🧠 Whisper Flask Transcriber
============================

A small Flask API exposing a Whisper (`faster-whisper`) model to transcribe audio files, packaged in a ready-to-use Docker container.

✨ Features
----------

- 🤖 Audio transcription via `/transcribe`
- 🔒 Optional API key authentication (`API_KEY`)
- 🚦 Built-in rate limiting (60 requests per minute per client)
- 🩺 Health endpoint `/health`
- 🐳 Docker image with a pre-downloaded Whisper model (`medium`)
- 🎚️ Whisper model selection via environment variable (`WHISPER_MODEL_NAME`)

📦 Requirements
---------------

- Docker installed
- Linux host capable of running `linux/amd64` or `linux/arm64` containers

⚙️ Environment variables
------------------------

- `API_KEY` (optional)
  - If set (non-empty) in the container, all routes require the HTTP header `X-API-Key` with this value.
  - Secure comparison on the server side (sanitized, reasonable length, constant-time comparison).
  - If not set, authentication is disabled.
- `WHISPER_MODEL_NAME` (optional)
  - Selects the Whisper model used by the API.
  - Accepted values: `tiny`, `base`, `small`, `medium`, `large-v2`, `large-v3`.
  - Default: `medium`.
  - Any other value is ignored and `medium` is used.
- `MAX_UPLOAD_MB` (optional)
  - Maximum allowed request size (in megabytes) for uploads.
  - Applies to `/transcribe-file` and other requests with bodies.
  - Default: `50`. Values ≤ 0 or > 1024 are ignored and the default is used.

🛠️ Build the image
-------------------

From the project folder:

```bash
docker build -t ghcr.io/painteau/whisper-flask:latest .
```

🚀 Run the container
--------------------

Without authentication:

```bash
docker run --rm -p 5632:5632 ghcr.io/painteau/whisper-flask:latest
```

With API key authentication:

```bash
docker run --rm \
  -e API_KEY=my-secret-key \
  -p 5632:5632 \
  ghcr.io/painteau/whisper-flask:latest
```

Example with model selection (`large-v3`):

```bash
docker run --rm \
  -e API_KEY=my-secret-key \
  -e WHISPER_MODEL_NAME=large-v3 \
  -p 5632:5632 \
  ghcr.io/painteau/whisper-flask:latest
```

🔍 Endpoints
-----------

### `/health` (GET)

Checks that the API is alive.

Example without auth:

```bash
curl http://localhost:5632/health
```

Example with auth:

```bash
curl -H "X-API-Key: my-secret-key" http://localhost:5632/health
```

Expected response:

```json
{
  "status": "ok"
}
```

### `/transcribe` (POST)

Transcribes an audio file accessible from inside the container (JSON payload with a file path).

JSON body:

```json
{
  "path": "/path/to/audio/file.mp3"
}
```

Example without auth:

```bash
curl -X POST http://localhost:5632/transcribe \
  -H "Content-Type: application/json" \
  -d '{"path": "/data/audio.mp3"}'
```

Example with auth:

```bash
curl -X POST http://localhost:5632/transcribe \
  -H "Content-Type: application/json" \
  -H "X-API-Key: my-secret-key" \
  -d '{"path": "/data/audio.mp3"}'
```

### `/transcribe-file` (POST)

Transcribes an audio file sent directly in the request (multipart upload).

The request must be `multipart/form-data` with a `file` field.
Only common audio/video formats are accepted: `wav`, `mp3`, `m4a`, `flac`, `ogg`, `webm`, `mp4`.

Example without auth:

```bash
curl -X POST http://localhost:5632/transcribe-file \
  -F "file=@C:/audios/reel.mp3" \
  http://localhost:5632/transcribe-file
```

Example with auth:

```bash
curl -X POST http://localhost:5632/transcribe-file \
  -H "X-API-Key: my-secret-key" \
  -F "file=@C:/audios/reel.mp3" \
  http://localhost:5632/transcribe-file
```

📂 Mounting an audio file into the container
-------------------------------------------

For example, if your file is on the host at `C:\audios\reel.mp3`, you can mount it into `/data` inside the container:

```bash
docker run --rm \
  -v C:/audios:/data \
  -p 5632:5632 \
  ghcr.io/painteau/whisper-flask:latest
```

Then call:

```bash
curl -X POST http://localhost:5632/transcribe \
  -H "Content-Type: application/json" \
  -d '{"path": "/data/reel.mp3"}'
```

🚦 Rate limiting
----------------

- Default limit: 60 requests per minute
- Limiting key:
  - If `API_KEY` is set: combination of `X-API-Key` + IP address
  - Otherwise: IP address only
- If the limit is exceeded, the API returns:

```json
{
  "error": "Too Many Requests"
}
```

🔐 Error codes
--------------

- `400 Bad Request`:
  - Invalid JSON
  - Missing or invalid `path` field
  - Nonexistent file path
  - Missing `file` field or unsupported/empty upload for `/transcribe-file`
- `401 Unauthorized`:
  - Missing or incorrect API key when `API_KEY` is set
- `404 Not Found`:
  - Unknown route
- `405 Method Not Allowed`:
  - Wrong HTTP method for a route
- `429 Too Many Requests`:
  - Rate limit exceeded
- `413 Payload Too Large`:
  - Request body exceeds `MAX_UPLOAD_MB`
- `500 Internal Server Error`:
  - Internal error during transcription

🧪 Example transcription response
---------------------------------

```json
{
  "transcript": "This is the transcribed audio text."
}
```

