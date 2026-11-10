---
tags: [reference, troubleshooting]
---
# Troubleshooting

## Camera
| Symptom | Cause → fix |
|---|---|
| "No RealSense camera found" | Cable or port. Use a **blue** port and a USB 3 cable; run `rs-enumerate-devices` |
| Warning "camera is on USB 2" | The cable is USB 2 (your first one was). Swap the cable |
| FPS below 20 | USB 2, weak power supply, or Pi overheating |
| Depth black near the camera | Closer than about 28 cm: move back |
| Camera light red in the panel while a mode runs | Normal: the panel doesn't check the camera while it's in use |

## Hand tracking
| Symptom | Fix |
|---|---|
| "hand outside zone Z 1.5 m" | Stand about 60 cm from the camera |
| "hand seen, no depth at wrist" | Too close (<30 cm) or the wrist is out of frame |
| Wrong gesture label | Palm facing the camera, good light, hand in the middle of the picture |
| "hand found – hold still…" stays | Keep your hand steady for a moment |

## Arm
| Symptom | Fix |
|---|---|
| Arm light red | 5V on? Wait 10 s; Pi on BraccioNet; `ping 192.168.1.100` |
| Arm doesn't move but the log shows packets | Quest app also running? Arm on a different network? Wrong IP in the panel? |
| Arm twitches between two poses | Two senders (Quest + Pi). Close one |
| Gripper stops above objects | Object on the **desk** instead of the **board**; or recalibrate (`s-2`) |
| Left/right swapped | `MIRROR_X = False` |
| Arm folds over itself | Fixed (upper arm can't lean back). Update `hand_to_braccio.py` |
| Wrist twists when you move up/down | `TWIST_ENABLED = False` (default) |
| Shoulder sags/shakes | Arm supply must be 5 V and at least 5 A |
| "out of reach – holding" | The target is too close to the base: move your hand so the gripper goes further out |

## Control Panel
| Symptom | Fix |
|---|---|
| Icon does nothing | Run `~/braccio-venv/bin/python ~/braccio-vision/control_panel.py` in a terminal to see the error |
| "tkinter missing" | `sudo apt install -y python3-tk` |
| WiFi light red, Connect fails | Pick BraccioNet from the WiFi icon once and enter the password |
| Font warnings in the log | Harmless (filtered) |

## Pi
| Symptom | Fix |
|---|---|
| Slow / throttling | `vcgencmd measure_temp`. Fit the Active Cooler |
| MediaPipe won't install | You're on Trixie (Python 3.13): use Bookworm |
| Traceback mentioning `__del__` on exit | Harmless; fixed with `landmarker.close()` |
