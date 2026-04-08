#!/bin/bash
set -e

mkdir -p /var/log/supervisor

SNAPSHOT_DIR="${SNAPSHOT_DIR:-/tmp/stream_snapshots}"
SNAPSHOT_INTERVAL="${SNAPSHOT_INTERVAL:-30}"

echo "=== Chat Plays Roblox - Starting Services ==="
echo "Screen:           ${SCREEN_WIDTH}x${SCREEN_HEIGHT}x${SCREEN_DEPTH}"
echo "VNC Port:         ${VNC_PORT}"
echo "noVNC Port:       ${NOVNC_PORT}"
echo "Stream FPS:       ${STREAM_FPS}"
echo "Stream Bitrate:   ${STREAM_BITRATE}"
echo "RTMP URL:         ${RTMP_URL}"
echo "Stream Key:       ${YOUTUBE_STREAM_KEY:+SET (hidden)}"
echo "YouTube API:      ${YOUTUBE_API_KEY:+SET (hidden)}"
echo "Video ID:         ${YOUTUBE_VIDEO_ID}"
echo "Game ID:          ${ROBLOX_GAME_ID}"
echo "Snapshot Dir:     ${SNAPSHOT_DIR}"
echo "Snapshot Interval:${SNAPSHOT_INTERVAL}s"
echo "=============================================="

if [ -z "${YOUTUBE_STREAM_KEY}" ] || [ "${YOUTUBE_STREAM_KEY}" = "YOUR_STREAM_KEY_HERE" ]; then
  echo "WARNING: YOUTUBE_STREAM_KEY is not set — RTMP streaming will not work."
fi

if [ -z "${YOUTUBE_API_KEY}" ] || [ "${YOUTUBE_API_KEY}" = "YOUR_GOOGLE_CLOUD_API_KEY_HERE" ]; then
  echo "WARNING: YOUTUBE_API_KEY is not set — chat bot will not work."
fi


echo "Initializing Wine prefix..."
WINEARCH=win64 WINEPREFIX=/root/.wine wine wineboot --init 2>/dev/null || true

echo "Setting PulseAudio as default sink for Wine..."
export PULSE_SERVER=unix:/run/user/0/pulse/native

wget -O /tmp/RobloxPlayerInstaller.exe \
"https://www.roblox.com/download/client?os=win"

sleep 3

echo "Starting supervisor..."
exec /usr/bin/supervisord -c /etc/supervisor/conf.d/supervisord.conf
