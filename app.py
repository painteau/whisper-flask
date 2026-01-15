from flask import Flask, request, jsonify
from faster_whisper import WhisperModel
import os
import time
from collections import defaultdict, deque
import hmac
import tempfile
from werkzeug.exceptions import RequestEntityTooLarge

app = Flask(__name__)

raw_api_key = os.environ.get("API_KEY")
API_KEY = raw_api_key.strip() if isinstance(raw_api_key, str) and raw_api_key.strip() else None

DEFAULT_MAX_UPLOAD_MB = 50
raw_max_upload = os.environ.get("MAX_UPLOAD_MB")
try:
    max_upload_mb = int(raw_max_upload) if raw_max_upload is not None else DEFAULT_MAX_UPLOAD_MB
except ValueError:
    max_upload_mb = DEFAULT_MAX_UPLOAD_MB
if max_upload_mb <= 0 or max_upload_mb > 1024:
    max_upload_mb = DEFAULT_MAX_UPLOAD_MB
app.config["MAX_CONTENT_LENGTH"] = max_upload_mb * 1024 * 1024

RATE_LIMIT = 60
RATE_WINDOW_SECONDS = 60
_request_log = defaultdict(deque)

ALLOWED_AUDIO_EXTENSIONS = {
    "wav",
    "mp3",
    "m4a",
    "flac",
    "ogg",
    "webm",
}

allowed_models = {
    "tiny",
    "base",
    "small",
    "medium",
    "large-v2",
    "large-v3",
}

env_model_name = os.environ.get("WHISPER_MODEL_NAME") or "medium"
WHISPER_MODEL_NAME = env_model_name if env_model_name in allowed_models else "medium"

model = WhisperModel(WHISPER_MODEL_NAME, device="cpu")


def authenticate():
    # If no API key is configured, authentication is disabled
    if not API_KEY:
        return None
    provided_key = request.headers.get("X-API-Key")
    if not isinstance(provided_key, str) or not provided_key or len(provided_key) > 256:
        return jsonify({"error": "Unauthorized"}), 401
    if not hmac.compare_digest(provided_key, API_KEY):
        return jsonify({"error": "Unauthorized"}), 401
    return None


def check_rate_limit():
    identifier_parts = []
    if API_KEY:
        identifier_parts.append(request.headers.get("X-API-Key") or "no-key")
    identifier_parts.append(request.remote_addr or "unknown")
    identifier = "|".join(identifier_parts)
    now = time.time()
    window_start = now - RATE_WINDOW_SECONDS
    entries = _request_log[identifier]
    while entries and entries[0] < window_start:
        entries.popleft()
    if len(entries) >= RATE_LIMIT:
        return jsonify({"error": "Too Many Requests"}), 429
    entries.append(now)
    return None


def guard_request():
    auth_error = authenticate()
    if auth_error:
        return auth_error
    rate_error = check_rate_limit()
    if rate_error:
        return rate_error
    return None


@app.errorhandler(400)
def handle_400(error):
    return jsonify({"error": "Bad Request"}), 400


@app.errorhandler(404)
def handle_404(error):
    return jsonify({"error": "Not Found"}), 404


@app.errorhandler(405)
def handle_405(error):
    return jsonify({"error": "Method Not Allowed"}), 405


@app.errorhandler(429)
def handle_429(error):
    return jsonify({"error": "Too Many Requests"}), 429


@app.errorhandler(500)
def handle_500(error):
    return jsonify({"error": "Internal Server Error"}), 500


@app.errorhandler(RequestEntityTooLarge)
def handle_413(error):
    return jsonify({"error": "File too large"}), 413


def is_allowed_file(file):
    if not file or not file.filename:
        return False
    name = file.filename
    if "." not in name:
        return False
    ext = name.rsplit(".", 1)[1].lower()
    if ext not in ALLOWED_AUDIO_EXTENSIONS:
        return False
    mimetype = file.mimetype or ""
    if not mimetype.startswith("audio/") and mimetype not in ("video/webm", "application/octet-stream"):
        return False
    return True


@app.route("/transcribe", methods=["POST"])
def transcribe():
    guard_error = guard_request()
    if guard_error:
        return guard_error
    # Safely parse the JSON body (returns None instead of raising on invalid JSON)
    data = request.get_json(silent=True)
    if not isinstance(data, dict):
        return jsonify({"error": "Invalid JSON body"}), 400
    # Validate the 'path' field
    path = data.get("path")
    if not isinstance(path, str) or not path:
        return jsonify({"error": "Field 'path' must be a non-empty string"}), 400
    if not os.path.exists(path):
        return jsonify({"error": "Invalid file path"}), 400
    try:
        segments, _ = model.transcribe(path)
        transcript = " ".join([seg.text for seg in segments])
    except Exception:
        return jsonify({"error": "Failed to transcribe audio"}), 500
    return jsonify({"transcript": transcript}), 200


@app.route("/transcribe-file", methods=["POST"])
def transcribe_file():
    guard_error = guard_request()
    if guard_error:
        return guard_error
    if "file" not in request.files:
        return jsonify({"error": "Missing file field"}), 400
    file = request.files["file"]
    if not file or not file.filename:
        return jsonify({"error": "Empty filename"}), 400
    if not is_allowed_file(file):
        return jsonify({"error": "Unsupported file type"}), 400
    ext = file.filename.rsplit(".", 1)[1].lower() if "." in file.filename else ""
    suffix = "." + ext if ext in ALLOWED_AUDIO_EXTENSIONS else ".tmp"
    tmp_path = None
    try:
        with tempfile.NamedTemporaryFile(suffix=suffix, delete=False) as tmp:
            tmp_path = tmp.name
            file.save(tmp_path)
        segments, _ = model.transcribe(tmp_path)
        transcript = " ".join([seg.text for seg in segments])
    except Exception:
        if tmp_path and os.path.exists(tmp_path):
            try:
                os.remove(tmp_path)
            except OSError:
                pass
        return jsonify({"error": "Failed to transcribe uploaded file"}), 500
    if tmp_path and os.path.exists(tmp_path):
        try:
            os.remove(tmp_path)
        except OSError:
            pass
    return jsonify({"transcript": transcript}), 200


@app.route("/health", methods=["GET"])
def health_check():
    guard_error = guard_request()
    if guard_error:
        return guard_error
    return jsonify({"status": "ok"}), 200


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5632)
