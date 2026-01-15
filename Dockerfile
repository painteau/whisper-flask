FROM python:3.11-slim

ENV PYTHONUNBUFFERED=1

WORKDIR /app

RUN apt-get update \
    && apt-get install -y --no-install-recommends ffmpeg \
    && rm -rf /var/lib/apt/lists/*

RUN pip install --no-cache-dir faster-whisper flask gunicorn

RUN python -c "from faster_whisper import WhisperModel; WhisperModel('medium', device='cpu')"

COPY app.py .

CMD ["gunicorn", "-b", "0.0.0.0:5632", "app:app"]
