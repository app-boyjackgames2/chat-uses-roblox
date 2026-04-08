#!/bin/bash

RTMP_TARGET="${RTMP_URL}/${YOUTUBE_STREAM_KEY}"
W="${SCREEN_WIDTH:-1920}"
H="${SCREEN_HEIGHT:-1080}"
FPS="${STREAM_FPS:-30}"
BITRATE="${STREAM_BITRATE:-4500k}"

echo "[STREAM] Waiting for display and PulseAudio to be ready..."
sleep 8

echo "[STREAM] Starting FFmpeg RTMP stream to YouTube..."
echo "[STREAM] Resolution: ${W}x${H} @ ${FPS}fps | Bitrate: ${BITRATE}"
echo "[STREAM] RTMP target: ${RTMP_URL}/****"

exec ffmpeg \
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
