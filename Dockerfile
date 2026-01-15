FROM ghcr.io/painteau/python-ffmpeg-flask-gunicorn:latest

ENV PYTHONUNBUFFERED=1

WORKDIR /app

RUN apt-get update \
    && apt-get install -y --no-install-recommends pkg-config libavformat-dev libavcodec-dev libavdevice-dev libavutil-dev libswscale-dev libavfilter-dev \
    && rm -rf /var/lib/apt/lists/*

RUN pip install faster-whisper

RUN python -c "from faster_whisper import WhisperModel; WhisperModel('medium', device='cpu')"

COPY app.py .

CMD ["gunicorn", "-b", "0.0.0.0:5632", "app:app"]
