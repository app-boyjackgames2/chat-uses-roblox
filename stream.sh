#!/bin/bash

RTMP_TARGET="${RTMP_URL}/${YOUTUBE_STREAM_KEY}"
W="${SCREEN_WIDTH:-1920}"
H="${SCREEN_HEIGHT:-1080}"
FPS="${STREAM_FPS:-30}"
BITRATE="${STREAM_BITRATE:-4500k}"
SNAPSHOT_DIR="${SNAPSHOT_DIR:-/tmp/stream_snapshots}"
SNAPSHOT_INTERVAL="${SNAPSHOT_INTERVAL:-30}"   # seconds between snapshots

echo "[STREAM] Waiting for display and PulseAudio to be ready..."
sleep 8

mkdir -p "${SNAPSHOT_DIR}"

echo "[STREAM] Starting FFmpeg RTMP stream to YouTube..."
echo "[STREAM] Resolution: ${W}x${H} @ ${FPS}fps | Bitrate: ${BITRATE}"
echo "[STREAM] RTMP target: ${RTMP_URL}/****"
echo "[STREAM] Snapshots: ${SNAPSHOT_DIR}  (every ${SNAPSHOT_INTERVAL}s)"

# ─── Background snapshot loop ───────────────────────────────────────────────
# Captures a PNG from DISPLAY:1 every SNAPSHOT_INTERVAL seconds.
# Each snapshot is saved as stream_YYYYMMDD_HHMMSS.png.
snapshot_loop() {
    while true; do
        TIMESTAMP="$(date +%Y%m%d_%H%M%S)"
        SNAP_PATH="${SNAPSHOT_DIR}/stream_${TIMESTAMP}.png"

        # Use FFmpeg to grab a single frame directly from the virtual display
        ffmpeg -loglevel error \
            -f x11grab \
            -video_size "${W}x${H}" \
            -i ":1.0+0,0" \
            -frames:v 1 \
            "${SNAP_PATH}" \
            -y 2>/dev/null

        if [ -f "${SNAP_PATH}" ]; then
            echo "[SNAPSHOT] Captured → ${SNAP_PATH}"
            # Copy as latest.png for easy external access
            cp "${SNAP_PATH}" "${SNAPSHOT_DIR}/latest.png"
        else
            echo "[SNAPSHOT] Failed to capture frame"
        fi

        sleep "${SNAPSHOT_INTERVAL}"
    done
}

snapshot_loop &
SNAPSHOT_PID=$!
echo "[STREAM] Snapshot loop started (PID: ${SNAPSHOT_PID})"

# ─── Cleanup on exit ─────────────────────────────────────────────────────────
cleanup() {
    echo "[STREAM] Stopping snapshot loop (PID: ${SNAPSHOT_PID})..."
    kill "${SNAPSHOT_PID}" 2>/dev/null
    exit 0
}
trap cleanup SIGTERM SIGINT

# ─── Main RTMP stream ────────────────────────────────────────────────────────
ffmpeg \
  -loglevel warning \
  -f x11grab \
    -framerate "${FPS}" \
    -video_size "${W}x${H}" \
    -i ":1.0+0,0" \
  -f pulse \
    -i virtual_sink.monitor \
  -vf "scale=${W}:${H}" \
  -c:v libx264 \
    -preset veryfast \
    -tune zerolatency \
    -b:v "${BITRATE}" \
    -maxrate "${BITRATE}" \
    -bufsize "$(echo "${BITRATE}" | sed 's/k//')0k" \
    -pix_fmt yuv420p \
    -g "$(( FPS * 2 ))" \
    -keyint_min "${FPS}" \
  -c:a aac \
    -ar 44100 \
    -b:a 128k \
  -f flv \
  "${RTMP_TARGET}"

# If FFmpeg exits, also stop the snapshot loop
kill "${SNAPSHOT_PID}" 2>/dev/null
