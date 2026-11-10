# Braccio Gesture Control

Control a TinkerKit Braccio robot arm with your bare hand. An Intel RealSense D435 depth camera and a Raspberry Pi 5 track your hand in 3D, and the arm follows it over WiFi. Open hand = gripper open, fist = grab.

Built during my internship at ICP, with remote operation in mining in mind.

## How it works
```
D435 (colour + depth) -> Raspberry Pi 5
   MediaPipe hand landmarks -> 3D hand position from depth -> open/fist gesture
   -> One Euro smoothing -> inverse kinematics -> servo angles
   -> UDP "base,shoulder,elbow,wrist,twist,gripper" -> Arduino UNO R4 WiFi -> Braccio
```

## Hardware
- Raspberry Pi 5 (8 GB), Raspberry Pi OS Bookworm 64-bit (not Trixie)
- Intel RealSense D435 on a USB 3 port
- TinkerKit Braccio + Arduino UNO R4 WiFi running the UDP sketch (port 5005)
- A small WiFi router so the Pi and the arm share a network

## Quick start
```bash
bash setup_pi.sh            # one time: librealsense, Python venv, MediaPipe model (45-90 min)
sudo reboot
bash install_shortcuts.sh   # desktop icon "Braccio Control Panel"
```
Then open **Braccio Control Panel** and press: Arm check -> Calibrate arm (first time) -> LIVE.

Command line:
```bash
source ~/braccio-venv/bin/activate
python check_camera.py --show                            # camera test
python hand_to_braccio.py --show                         # simulation, arm does not move
python hand_to_braccio.py --show --arm-ip 192.168.1.100  # live
python calibrate.py --arm-ip 192.168.1.100               # match the real arm to the model
```

## Files
| File | Does |
|---|---|
| `hand_to_braccio.py` | main program: hand -> arm |
| `control_panel.py` | desktop window with status lights, mode buttons and screen recording |
| `calibrate.py` | per-joint offsets, saved to `calibration.json` |
| `joint_test.py` | moves one joint at a time for diagnosis |
| `hand_depth.py` | hand landmarks + gestures with real 3D positions |
| `objects_depth.py` | finds objects on a table from depth (RANSAC table plane) |
| `check_camera.py`, `rs_common.py` | camera test and shared camera helpers |
| `setup_pi.sh`, `install_shortcuts.sh` | installers |
| `docs/` | full documentation (Obsidian vault, open `docs/00 Home.md`) |

## Safety
The arm moves at most 6 degrees per joint per update, goes home when no hand is seen for 2 s, and every exit path sends it home. Keep a hand near the arm's 5 V plug while running LIVE.
