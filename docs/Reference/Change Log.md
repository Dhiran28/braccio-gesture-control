---
tags: [reference, history, lessons]
---
# Change Log: How Problems Were Solved

A record of real problems from testing. Each one is a lesson in **robotics debugging**.

| # | Problem observed | Root cause | Fix | Lesson |
|---|---|---|---|---|
| 1 | Camera on USB 2.1 | USB 2 cable | Another cable → 3.2 | Check the lowest layer first |
| 2 | Hand depth wrong | Wrong argument order in `rs2_project_color_pixel_to_depth_pixel` | Swapped `d2c`/`c2d` | Read the API signature carefully |
| 3 | IK answers the arm couldn't do | Wrist beyond its servo range | `within_limits` + both elbow solutions | Maths ≠ machine; always check limits |
| 4 | Gripper flicked fist ↔ pinch | Single-frame misclassification | 5–6 frame debounce | Never act on one sample |
| 5 | Wrist rotated when moving up/down | Palm-roll estimate changes with pose | Twist off by default | Disable features that cause harm |
| 6 | Gripper 15 cm too high | Shoulder about 12–15° short, wrist about 10–15° short | `joint_test.py` → `calibrate.py` (s−12, w−10) | Measure each joint separately |
| 7 | Jerky following | EMA smoothing tradeoff | One Euro filter | Use known algorithms (research!) |
| 8 | Open hand labelled "fist" at 1.5 m | Noisy depth on fingers | Gesture from MediaPipe world landmarks | Use the most reliable signal for each job |
| 9 | Hand and arm drifted apart | Relative mode + frequent tracking drop-outs | Absolute mode default | Choose control modes for real conditions |
| 10 | Arm folded over itself, wrist jammed | IK found a back-leaning solution near the base | `UPPER_ARM_MAX_DEG = 92`, reach ≥ 20 cm, nudge-out fallback | Valid maths can be a bad pose: add "naturalness" constraints |
| 11 | False detection moved the arm | One-frame hand | 0.3 s hold-still start | Require persistence before motion |
| 12 | Hard to grab | Objects on the desk (lower than the board), too wide; camera low and tilted up | Objects on the board 22–30 cm out, smaller objects, camera at chest height | The setup matters as much as the code |

The method that worked: **video/photos of the real arm → compare with the simulation numbers → isolate one joint → fix → re-test.**
