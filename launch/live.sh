#!/usr/bin/env bash
source "$(dirname "$0")/common.sh"
echo "=== BRACCIO GESTURE CONTROL - LIVE ==="
echo "Safety: keep a hand near the arm's 5V plug. Keys in the camera window: SPACE = pause, Q = quit."
camera_ok || { finish; exit 1; }
if ! arm_ok; then
  echo
  read -rp "Run SIMULATION instead (arm will not move)? [y/N] " a
  [[ "$a" =~ ^[Yy] ]] && python hand_to_braccio.py --show
  finish; exit 1
fi
python hand_to_braccio.py --show --arm-ip "$ARM_IP"
finish
