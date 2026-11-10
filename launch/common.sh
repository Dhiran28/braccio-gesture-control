#!/usr/bin/env bash
# Shared setup for all Braccio launchers
ARM_IP="192.168.1.100"                       # arm's fixed address on BraccioNet (change here if it ever moves)
export QT_QPA_FONTDIR=/usr/share/fonts/truetype/dejavu   # hides harmless font warnings
cd "$HOME/braccio-vision" || { echo "braccio-vision folder not found"; read -rp "Press Enter to close"; exit 1; }
source "$HOME/braccio-venv/bin/activate"

camera_ok() {
  if ! python -c "import pyrealsense2 as rs; import sys; sys.exit(0 if len(rs.context().query_devices()) else 1)" 2>/dev/null; then
    echo
    echo "  !! Camera not found. Plug the D435 into a BLUE USB port (USB 3 cable) and try again."
    return 1
  fi
}

arm_ok() {
  if ! ping -c 2 -W 1 "$ARM_IP" >/dev/null 2>&1; then
    echo
    echo "  !! Arm not reachable at $ARM_IP"
    echo "     - Is the arm powered (5V plugged in)? Wait ~10 s after power-on."
    echo "     - Is the Pi connected to the BraccioNet WiFi? (WiFi icon, top right)"
    echo "     - Is the Quest app closed? (only one controller at a time)"
    return 1
  fi
}

finish() {
  echo
  read -rp "Finished. Press Enter to close this window."
}
