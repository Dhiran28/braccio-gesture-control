#!/usr/bin/env bash
source "$(dirname "$0")/common.sh"
echo "=== BRACCIO GESTURE CONTROL - SIMULATION (arm does not move) ==="
echo "Keys in the camera window: SPACE = pause, Q = quit."
camera_ok || { finish; exit 1; }
python hand_to_braccio.py --show
finish
