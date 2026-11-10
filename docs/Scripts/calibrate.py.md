---
tags: [script, calibration]
---
# calibrate.py

**Job:** make the **real** arm match the **maths**, and save the corrections.
**Run:** Control Panel → **Calibrate arm** (opens a terminal), or `python calibrate.py --arm-ip 192.168.1.100`.

## Why it's needed
The code assumes "servo 90 = joint perfectly straight". In reality, horns are fitted a tooth off, and the shoulder **sags** under the weight of the stretched arm. In your tests the shoulder fell about 12–15° short and the wrist about 10–15° short, so the gripper stopped about 15 cm above the board instead of 5 cm.

## How it works
1. Imports the maths from `hand_to_braccio.py` as `H` (`H.ik`, `H.to_servos`, `H.SHOULDER_OFFSET`…), so calibration and live control use **exactly the same model**.
2. A background **thread** (`sender_loop`) sends the current pose 10 times a second, so the arm holds it while you type.
3. The main thread waits for your commands (`input("> ")`).
4. Each command changes an offset or sign **in memory** (`H.SHOULDER_OFFSET += d`), then `compute()` re-solves the pose and `show()` prints it.
5. `save` writes `calibration.json`:
```json
{"shoulder_offset": -12, "elbow_offset": 0, "wrist_offset": -10,
 "shoulder_sign": 1, "elbow_sign": 1, "wrist_sign": 1, "base_mm": 71.5}
```
6. When `hand_to_braccio.py` starts, it reads this file and overrides its defaults.

## Poses
| Key | Pose | Check against |
|---|---|---|
| 1 | Candle | all links vertical (use a phone level from the side) |
| 2 | Reach low | tip 22 cm out, 5 cm above the board |
| 3 | Reach high | tip 28 cm out, 18 cm above the board |
| 4 | Reach far | tip 30 cm out, 8 cm above the board |

## Commands
See [[Terminal Commands Cheat Sheet#Calibration commands inside calibrate.py]].

## Python ideas worth noticing
- `state = {...}` dict shared between the thread and the input loop (simple shared state).
- `setattr(H, "SHOULDER_SIGN", -getattr(H, "SHOULDER_SIGN"))`: change a module variable by name.
- `finally:` always sends the candle pose when you quit, even after Ctrl+C.

Concept: [[Servo Angles, Offsets and Calibration]]
