#!/usr/bin/env bash
# Braccio vision setup for Raspberry Pi 5 + RealSense D435
# Requires: Raspberry Pi OS **Bookworm 64-bit** (NOT Trixie - MediaPipe needs Python <= 3.12)
# Run:  bash setup_pi.sh        (takes ~45-90 min, mostly the librealsense build)
set -e

LRS_VERSION="master"           # 'master' = latest stable release; or pin a tag e.g. v2.56.x
VENV="$HOME/braccio-venv"
HERE="$(cd "$(dirname "$0")" && pwd)"

echo "== 0. Sanity checks =="
PYV=$(python3 -c 'import sys; print(f"{sys.version_info.major}.{sys.version_info.minor}")')
echo "System Python: $PYV"
if [ "$(echo "$PYV" | cut -d. -f2)" -ge 13 ]; then
  echo "!! Python $PYV detected (Trixie?). MediaPipe will NOT install. Re-flash with Raspberry Pi OS Bookworm 64-bit (Legacy)."
  exit 1
fi
uname -m | grep -q aarch64 || { echo "!! Not 64-bit OS. Use Raspberry Pi OS 64-bit."; exit 1; }

echo "== 1. Let the USB ports give the D435 enough power =="
CFG=/boot/firmware/config.txt
if ! grep -q "^usb_max_current_enable=1" "$CFG"; then
  echo "usb_max_current_enable=1" | sudo tee -a "$CFG"
  echo "   (added usb_max_current_enable=1 - takes effect after reboot)"
fi

echo "== 2. System packages =="
sudo apt update
sudo apt install -y git cmake build-essential pkg-config libssl-dev libusb-1.0-0-dev \
  libgtk-3-dev libglfw3-dev libgl1-mesa-dev libglu1-mesa-dev \
  python3-dev python3-venv curl

echo "== 3. Python venv =="
python3 -m venv "$VENV"
source "$VENV/bin/activate"
pip install --upgrade pip wheel setuptools
pip install numpy opencv-python mediapipe

echo "== 4. Build librealsense ($LRS_VERSION) with RSUSB backend + Python bindings =="
cd "$HOME"
[ -d librealsense ] || git clone --depth 1 -b "$LRS_VERSION" https://github.com/IntelRealSense/librealsense.git
cd librealsense
sudo cp config/99-realsense-libusb.rules /etc/udev/rules.d/
sudo udevadm control --reload-rules && sudo udevadm trigger
mkdir -p build && cd build
cmake .. \
  -DFORCE_RSUSB_BACKEND=ON \
  -DBUILD_PYTHON_BINDINGS=ON \
  -DPYTHON_EXECUTABLE="$VENV/bin/python" \
  -DCMAKE_BUILD_TYPE=Release \
  -DBUILD_EXAMPLES=ON \
  -DBUILD_GRAPHICAL_EXAMPLES=ON \
  -DBUILD_WITH_OPENMP=OFF
make -j3          # -j3 keeps RAM use safe on 8 GB
sudo make install
sudo ldconfig

echo "== 5. Put pyrealsense2 into the venv =="
SITE=$("$VENV/bin/python" -c 'import site; print(site.getsitepackages()[0])')
find . -name "pyrealsense2*.so*" -exec cp -v {} "$SITE/" \;
find . -name "pyrsutils*.so*"   -exec cp -v {} "$SITE/" \; || true
"$VENV/bin/python" -c "import pyrealsense2 as rs; print('pyrealsense2 OK, version', rs.__version__ if hasattr(rs,'__version__') else '?')"

echo "== 6. MediaPipe hand model =="
mkdir -p "$HERE/models"
curl -L -o "$HERE/models/hand_landmarker.task" \
  https://storage.googleapis.com/mediapipe-models/hand_landmarker/hand_landmarker/float16/latest/hand_landmarker.task

echo
echo "DONE. Now:  sudo reboot"
echo "After reboot:  source $VENV/bin/activate && cd $HERE && python check_camera.py"
