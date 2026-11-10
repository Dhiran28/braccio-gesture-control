---
tags: [script, setup, bash]
---
# setup_pi.sh

**Job:** one-time installer. It turns a fresh Raspberry Pi OS into a machine that can run the camera and the hand AI.
**Run:** `bash setup_pi.sh`, then `sudo reboot`. It takes 45–90 min, mostly compiling the camera driver.
**Language:** Bash (a list of terminal commands in a file).

## What it does, step by step

| Step | Lines do | Why |
|---|---|---|
| 0. Sanity checks | Reads the Python version. **Stops if 3.13+** (Trixie). Stops if not 64-bit (`aarch64`) | MediaPipe has no Python 3.13 / 32-bit builds |
| 1. USB power | Adds `usb_max_current_enable=1` to `/boot/firmware/config.txt` | Lets the Pi give the D435 enough current. Takes effect after reboot |
| 2. System packages | `sudo apt install git cmake build-essential libusb … python3-venv` | Compilers and libraries needed to build librealsense |
| 3. Python venv | `python3 -m venv ~/braccio-venv`, then `pip install numpy opencv-python mediapipe` | A private Python for this project. See [[Terminal Basics#Virtual environments]] |
| 4. Build librealsense | `git clone` Intel's driver, `cmake -DFORCE_RSUSB_BACKEND=ON -DBUILD_PYTHON_BINDINGS=ON …`, `make -j3`, `sudo make install` | There's no ready-made Pi package. **RSUSB** talks to the camera through plain libusb, avoiding kernel patches |
| 5. Python bindings | Copies `pyrealsense2*.so` into the venv's `site-packages` | So `import pyrealsense2` works inside the venv |
| 6. Hand model | `curl` downloads `hand_landmarker.task` into `models/` | The MediaPipe AI model file |

## Key Bash ideas used
```bash
set -e                       # stop at the first command that fails (don't continue half-broken)
VENV="$HOME/braccio-venv"    # a variable; use it as "$VENV"
HERE="$(cd "$(dirname "$0")" && pwd)"   # the folder this script lives in
[ -d librealsense ] || git clone ...   # "if the folder doesn't exist, clone it"
grep -q "^usb_max..." "$CFG"           # -q = quiet; just "found or not"
```

## `make -j3` vs `-j2`
`-jN` compiles N files at the same time. More is faster but uses more RAM and heat. With **no cooler**, `-j2` is safer. That's what you used.

## If it fails
| Message | Fix |
|---|---|
| `Python 3.13 detected` | Re-flash **Bookworm 64-bit (Legacy)** in Raspberry Pi Imager |
| Build killed / freezes | Use `make -j2`, check `vcgencmd measure_temp` and add a fan |
| `import pyrealsense2` fails | Run step 5 again: find the `.so` under `~/librealsense/build` and copy it into the venv |

Related: [[rs_common.py]], [[check_camera.py]]
