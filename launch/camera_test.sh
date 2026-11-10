#!/usr/bin/env bash
source "$(dirname "$0")/common.sh"
echo "=== CAMERA TEST ==="
camera_ok || { finish; exit 1; }
python check_camera.py
echo
echo "Opening live colour + depth view (press Q in the window to close)..."
python check_camera.py --show
finish
