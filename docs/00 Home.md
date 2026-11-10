---
tags: [braccio, home, moc]
aliases: [Start Here, Index]
---
# 🦾 Braccio Vision: Start Here

This vault documents the **gesture-controlled TinkerKit Braccio arm**. A Raspberry Pi 5 watches your hand with an Intel RealSense **D435** depth camera and drives the arm over WiFi.

> [!tip] How to read this vault
> It's written so you can **understand and rebuild** the system, not just run it.
> - New here? Read top to bottom: [[01 System Overview]] → [[02 Hardware and Network]] → [[03 Folder Map]].
> - Want to **use** it? Go to [[Operator Quick Start]] and [[Terminal Commands Cheat Sheet]].
> - Want to **learn how it works**? Start with [[How hand_to_braccio Was Built]] and the notes in *Concepts*.

## 🗺️ Map of the vault

### 1. The big picture
- [[01 System Overview]]: what talks to what, with diagrams
- [[02 Hardware and Network]]: Pi, camera, arm, router, IP addresses
- [[03 Folder Map]]: every file in `~/braccio-vision`, one line each

### 2. Using it
- [[Operator Quick Start]]: daily checklist and how to pick an object
- [[Terminal Basics]]: what the terminal is, and the 15 commands you actually need
- [[Terminal Commands Cheat Sheet]]: every project command, copy-paste ready
- [[Copying Files via USB]]: updating scripts without installing anything on the Pi

### 3. Every script, explained
| Script | One-line job | Note |
|---|---|---|
| `setup_pi.sh` | Installs everything (one time) | [[setup_pi.sh]] |
| `rs_common.py` | Starts the camera (shared helper) | [[rs_common.py]] |
| `check_camera.py` | Proves the camera works | [[check_camera.py]] |
| `hand_depth.py` | Hand points + gestures in 3D | [[hand_depth.py]] |
| `objects_depth.py` | Finds objects on the table from depth | [[objects_depth.py]] |
| `hand_to_braccio.py` | **The main program**: hand → arm | [[hand_to_braccio.py]] |
| `calibrate.py` | Makes the real arm match the maths | [[calibrate.py]] |
| `joint_test.py` | Moves one joint at a time (diagnosis) | [[joint_test.py]] |
| `control_panel.py` | The desktop window with buttons | [[control_panel.py]] |
| `install_shortcuts.sh` | Puts the icon on the desktop | [[install_shortcuts.sh]] |
| `launch/*.sh` | Old terminal launchers (superseded) | [[launch scripts]] |

### 4. How it was built (learning)
- [[How hand_to_braccio Was Built]]: building the main program in 8 stages
- [[How the Control Panel Was Built]]: a Tkinter GUI tutorial using the real panel

### 5. Concepts (the ideas behind the code)
- [[Depth Camera and 3D Points]]
- [[MediaPipe Hand Landmarks]]
- [[Gesture Classification]]
- [[Inverse Kinematics]]
- [[Servo Angles, Offsets and Calibration]]
- [[One Euro Filter]]
- [[Debouncing and State Machines]]
- [[Absolute vs Relative Control]]
- [[UDP Networking]]
- [[RANSAC Plane Fitting]]
- [[Safety Design]]

### 6. Reference
- [[Settings Reference]]: every tunable number in `hand_to_braccio.py`
- [[Troubleshooting]]
- [[Change Log]]: what went wrong while building this, and how it was fixed
- [[Learning Path and Exercises]]
- [[Glossary]]
