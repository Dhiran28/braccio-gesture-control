#!/usr/bin/env bash
source "$(dirname "$0")/common.sh"
echo "=== ARM DIRECTION CHECK (3 test poses, 12 s) ==="
echo "Compare the real arm with the simulation window: CANDLE -> REACH LOW -> REACH HIGH."
echo "Keep a hand near the arm's 5V plug."
arm_ok || { finish; exit 1; }
read -rp "Arm area clear? Press Enter to start..."
python hand_to_braccio.py --check --show --arm-ip "$ARM_IP"
finish
