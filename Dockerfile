FROM ubuntu:22.04

ENV DEBIAN_FRONTEND=noninteractive \
    VIDEO_URL="https://vk.com/video-216155816_456240081" \
    OUTPUT_FILE="stream.mp4" \
    STREAM_KEY="tjp4-hbx3-uawe-dgqe-64dp" \
    RTMP_URL="rtmp://a.rtmp.youtube.com/live2"

RUN apt-get update && \
    apt-get install -y --no-install-recommends \
        ffmpeg \
        curl \
        ca-certificates \
        python3 \
        procps \
        util-linux \
    && curl -L https://github.com/yt-dlp/yt-dlp/releases/latest/download/yt-dlp \
         -o /usr/local/bin/yt-dlp \
    && chmod a+rx /usr/local/bin/yt-dlp \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY entrypoint.sh /app/entrypoint.sh
RUN chmod +x /app/entrypoint.sh

CMD ["/app/entrypoint.sh"]
