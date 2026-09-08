#!/bin/sh
set -eu
cd /workspace
export PATH="${HOME:-/root}/.local/bin:$PATH"
python3 -m pip install --user -q yt-dlp edge-tts fastapi uvicorn pillow >/tmp/yt-dlp-install.log 2>&1 || true
python3 -m pip install --user -q -r worker/requirements.txt >/tmp/worker-pip.log 2>&1 || true
if ! curl -sf -o /dev/null --max-time 2 http://127.0.0.1:8091/health; then
  LUMENCUT_WORKER_HOST=127.0.0.1 LUMENCUT_WORKER_PORT=8091 LUMENCUT_DATA_DIR=/workspace/data DATA_DIR=/workspace/data \
    python3 -m worker.main >>/tmp/lumencut-worker.log 2>&1 &
fi
node scripts/preview.mjs stop || true
if curl -sf -o /dev/null --max-time 2 http://127.0.0.1:8080/; then
  exit 0
fi
npm run dev >>/tmp/app-startup.log 2>&1 &
