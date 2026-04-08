#!/usr/bin/env bash
set -euo pipefail

VIDEO_URL="${VIDEO_URL:-https://vk.com/video-216155816_456240081}"
OUTPUT_FILE="${OUTPUT_FILE:-stream.mp4}"
STREAM_KEY="${STREAM_KEY:-tjp4-hbx3-uawe-dgqe-64dp}"
RTMP_URL="${RTMP_URL:-rtmp://a.rtmp.youtube.com/live2}"

# ─── Swap (requires --privileged or --cap-add SYS_ADMIN) ─────────────────────
setup_swap() {
    if swapon --show | grep -q /swapfile; then
        echo "[SWAP] /swapfile already active — skipping."
        return
    fi
    echo "[SWAP] Creating 2 GB swapfile..."
    fallocate -l 2G /swapfile   || { echo "[SWAP] fallocate failed — skipping swap."; return; }
    chmod 600 /swapfile
    mkswap  /swapfile
    swapon  /swapfile
    echo "[SWAP] Swap enabled."
}
setup_swap

# ─── Download video ───────────────────────────────────────────────────────────
if [ -f "$OUTPUT_FILE" ]; then
    echo "[DOWNLOAD] $OUTPUT_FILE already exists — skipping download."
else
    echo "[DOWNLOAD] Downloading: $VIDEO_URL"
    yt-dlp \
        -f "bestvideo+bestaudio/best" \
        --merge-output-format mp4 \
        -o "$OUTPUT_FILE" \
        --no-part \
        --force-overwrites \
        "$VIDEO_URL"

    if [ $? -eq 0 ]; then
        echo "[DOWNLOAD] Видео успешно сохранено как $OUTPUT_FILE"
    else
        echo "[DOWNLOAD] Ошибка загрузки!"
        exit 1
    fi
fi

# ─── Stream loop ──────────────────────────────────────────────────────────────
FULL_RTMP="${RTMP_URL}/${STREAM_KEY}"
echo "[STREAM] Starting stream → $FULL_RTMP"

while true; do
    if [ ! -f "$OUTPUT_FILE" ]; then
        echo "[STREAM] Файл $OUTPUT_FILE не найден! Ожидание..."
        sleep 10
        continue
    fi

    echo "[STREAM] Запуск трансляции..."

    ffmpeg -re -stream_loop -1 -i "$OUTPUT_FILE" \
        -c:v libx264 -preset veryfast -pix_fmt yuv420p \
        -tune zerolatency \
        -b:v 3000k -maxrate 3000k -bufsize 6000k \
        -g 48 -r 24 \
        -c:a aac -b:a 160k -ar 44100 \
        -f flv "$FULL_RTMP"

    echo "[STREAM] FFmpeg был остановлен. Перезапуск через 5 секунд..."
    sleep 5
done
