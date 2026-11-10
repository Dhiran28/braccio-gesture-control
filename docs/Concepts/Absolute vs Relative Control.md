---
tags: [concept, control, teleoperation]
---
# Absolute vs Relative Control

Two ways to turn "where my hand is" into "where the gripper goes". Switch with `CONTROL_MODE` in [[hand_to_braccio.py]].

## Absolute (default): like a touchscreen
A **box** in front of the camera is stretched onto the arm's workspace. Each hand position has **one** matching gripper position.
| Hand (≈60 cm from camera) | Gripper |
|---|---|
| centre | forward, 12 cm high |
| 15 cm up | 20 cm high |
| 15 cm down | 5 cm high |
| 15 cm sideways | base turns about 37° |
| closer (45 cm) | reaches further (30 cm) |
| further (75 cm) | pulls back (20 cm) |

✅ Hand and arm can **never drift apart**, even after tracking drops out.
❌ You must stay inside the box (camera at chest height, about 60 cm away).

## Relative: like a mouse ("clutch" control)
When following starts, it remembers your hand position (the **anchor**) and the gripper position. After that, the gripper moves by **how much your hand moved**, 1:1 in cm.
```
target = gripper_at_anchor + (hand_now − hand_at_anchor)
```
✅ Works from anywhere; very natural fine control. Surgical robots work like this.
❌ Every time tracking drops and re-anchors, the mapping shifts. In your video the arm ended up folded low while your hand was at chest height.

## Why absolute became the default
In real use, the hand left the camera view often (too close, too far, blocked). Relative mode accumulated those jumps; absolute mode simply returns to the right place.

## The hand box settings
```python
HAND_X = (-0.20, 0.20)   # m left/right of the camera centre line
HAND_Y = (-0.18, 0.18)   # m above/below it
HAND_Z = (0.40, 0.80)    # m from the camera
BASE_RANGE = (40, 140)   # deg
REACH  = (0.20, 0.32)    # m
HEIGHT = (0.03, 0.22)    # m above the board
```
A smaller box gives more sensitivity (small hand moves → big arm moves). A bigger box gives finer control.
