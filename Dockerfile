FROM --platform=linux/amd64 ubuntu:22.04

ENV DEBIAN_FRONTEND=noninteractive
ENV DISPLAY=:1
ENV VNC_PORT=5900
ENV NOVNC_PORT=6080
ENV SCREEN_WIDTH=1920
ENV SCREEN_HEIGHT=1080
ENV SCREEN_DEPTH=24
ENV RTMP_URL=rtmp://a.rtmp.youtube.com/live2
ENV YOUTUBE_STREAM_KEY=YOUR_STREAM_KEY_HERE
ENV STREAM_FPS=30
ENV STREAM_BITRATE=4500k

RUN dpkg --add-architecture i386 && \
    apt-get update && apt-get install -y \
    xvfb \
    x11vnc \
    novnc \
    websockify \
    wine \
    openbox \
    xterm \
    wget \
    curl \
    git \
    ffmpeg \
    python3 \
    python3-pip \
    python3-venv \
    python3-dev \
    cabextract \
    xdotool \
    scrot \
    supervisor \
    pulseaudio \
    pulseaudio-utils \
    libpulse-dev \
    fonts-liberation \
    fonts-dejavu \
    && rm -rf /var/lib/apt/lists/*

RUN pip3 install --no-cache-dir \
    google-api-python-client \
    google-auth-httplib2 \
    google-auth-oauthlib \
    pyautogui \
    Pillow \
    requests \
    keyboard \
    mouse \
    opencv-python-headless \
    numpy \
    pywin32; exit 0

RUN winecfg || true

WORKDIR /app

COPY bot.py /app/bot.py
COPY stream.sh /app/stream.sh
COPY supervisord.conf /etc/supervisor/conf.d/supervisord.conf
COPY start.sh /app/start.sh
COPY default.pa /etc/pulse/default.pa

RUN chmod +x /app/start.sh /app/stream.sh

EXPOSE 5900 6080

CMD ["/app/start.sh"]
