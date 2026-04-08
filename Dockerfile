FROM --platform=linux/amd64 ubuntu:22.04

ENV DEBIAN_FRONTEND=noninteractive \
    DISPLAY=:1 \
    VNC_PORT=5900 \
    NOVNC_PORT=6080 \
    SCREEN_WIDTH=1920 \
    SCREEN_HEIGHT=1080 \
    SCREEN_DEPTH=24 \
    RTMP_URL=rtmp://a.rtmp.youtube.com/live2 \
    YOUTUBE_STREAM_KEY=YOUR_STREAM_KEY_HERE \
    STREAM_FPS=30 \
    STREAM_BITRATE=4500k

# Single layer: add i386, install everything, pip install, clean up
RUN dpkg --add-architecture i386 && \
    apt-get update && \
    apt-get install -y --no-install-recommends \
        xvfb \
        x11vnc \
        novnc \
        websockify \
        wine \
        openbox \
        wget \
        curl \
        ffmpeg \
        python3 \
        python3-pip \
        python3-tk \
        python3-xlib \
        xdotool \
        scrot \
        supervisor \
        pulseaudio \
        pulseaudio-utils \
        fonts-liberation \
        fonts-dejavu-core \
    && \
    # Python packages — core (must succeed)
    pip3 install --no-cache-dir \
        google-api-python-client \
        google-auth-httplib2 \
        google-auth-oauthlib \
        python-xlib \
        pyautogui \
        Pillow \
        requests \
        numpy \
        opencv-python-headless \
    && \
    # Optional packages (keyboard/mouse — Linux-only, allowed to fail)
    pip3 install --no-cache-dir keyboard mouse || true \
    && \
    # Pre-init Wine silently
    winecfg || true \
    && \
    # Aggressive cleanup — saves ~400 MB
    apt-get clean && \
    rm -rf \
        /var/lib/apt/lists/* \
        /var/cache/apt/* \
        /usr/share/doc \
        /usr/share/man \
        /usr/share/locale \
        /usr/share/wine/fonts \
        /root/.cache \
        /tmp/*

WORKDIR /app

COPY bot.py          /app/bot.py
COPY stream.sh       /app/stream.sh
COPY supervisord.conf /etc/supervisor/conf.d/supervisord.conf
COPY start.sh        /app/start.sh
COPY default.pa      /etc/pulse/default.pa

RUN chmod +x /app/start.sh /app/stream.sh

EXPOSE 5900 6080

CMD ["/app/start.sh"]
