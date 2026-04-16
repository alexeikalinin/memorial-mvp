#!/usr/bin/env bash
# Builds demo.mp4 + demo-poster.png via Pillow + ffmpeg (no libfreetype/drawtext required).
set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"
python3 render_landing_demo.py
# Poster: strong frame from chat segment (~46s)
ffmpeg -y -ss 46 -i demo.mp4 -frames:v 1 -update 1 -q:v 2 "../images/demo-poster.png"
ls -lh demo.mp4 "../images/demo-poster.png"
