📜 Changelog
===========

All notable changes to this project are documented in this file.

## 🟢 [0.2.0] - File upload & hardening

- Added `/transcribe-file` endpoint to transcribe audio files uploaded as `multipart/form-data`
- Restricted uploads to common audio types (`wav`, `mp3`, `m4a`, `flac`, `ogg`, `webm`)
- Introduced configurable maximum upload size via `MAX_UPLOAD_MB`
- Return `413 Payload Too Large` when request size exceeds the configured limit
- Improved temporary file handling and cleanup for uploaded audio
- Updated `README.md` with `/transcribe-file` examples and `MAX_UPLOAD_MB` documentation

## 🟢 [0.1.0] - Initial release

- Added Flask API `/transcribe` using `faster-whisper` (`medium` model)
- Added `/health` endpoint
- Docker integration with:
  - Base image `ghcr.io/painteau/python-ffmpeg-flask-gunicorn:latest`
  - Installation of `faster-whisper`
  - Pre-download of the Whisper `medium` model at build time
- Optional authentication via `API_KEY` environment variable:
  - If set: auth required via `X-API-Key` header
  - Secure key comparison (sanitized, reasonable length, constant-time comparison)
  - If not set: no auth
- Simple rate limiting:
  - 60 requests per minute per client
  - Key based on IP and API key (if present)
- Hardened JSON input and improved error handling:
  - 400, 401, 404, 405, 429, 500 with consistent JSON responses
- Whisper model selection via `WHISPER_MODEL_NAME`:
  - Supported values: `tiny`, `base`, `small`, `medium`, `large-v2`, `large-v3`
  - Automatic fallback to `medium` for any invalid value
- Documentation:
  - `README.md` with Docker and `curl` examples
  - `CHANGELOG.md`
  - `LICENSE`

