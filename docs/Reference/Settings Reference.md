---
tags: [reference, settings]
---
# Settings Reference

All settings are at the top of `hand_to_braccio.py` (lines 36–113). Edit with `nano`, then STOP → LIVE. Values in `calibration.json` override the offsets and signs.

## Arm geometry and limits
| Setting | Value | Meaning |
|---|---|---|
| `PORT` | 5005 | UDP port of the arm |
| `L0, L1, L2, L3` | 0.0715, 0.125, 0.125, 0.192 | link lengths (m) |
| `LO`, `HI` | see [[02 Hardware and Network#Servo limits from braccio_udp.ino]] | servo limits |
| `GRIP_OPEN, GRIP_CLOSED` | 20, 70 | gripper values. 10 = widest open |
| `UPPER_ARM_MAX_DEG` | 92 | upper arm can't lean back past this |

## Calibration (normally set by `calibrate.py`)
| Setting | Default | Yours |
|---|---|---|
| `SHOULDER_SIGN, ELBOW_SIGN, WRIST_SIGN` | +1 | +1 |
| `SHOULDER_OFFSET` | 0 | **−12** |
| `ELBOW_OFFSET` | 0 | 0 |
| `WRIST_OFFSET` | 0 | **−10** |
| `HOME` | `[90,90,90,90,90,20]` + offsets | candle |

## Wrist twist
| Setting | Value | Meaning |
|---|---|---|
| `TWIST_ENABLED` | False | turning your hand turns M5 |
| `TWIST_DEADBAND` | 15 | degrees ignored around centre |
| `TWIST_SIGN` | +1 | flip if it twists the wrong way |

## Hand box and mapping → [[Absolute vs Relative Control]]
| Setting | Value | Meaning |
|---|---|---|
| `HAND_X` | (−0.20, 0.20) m | left/right range used |
| `HAND_Y` | (−0.18, 0.18) m | up/down range used |
| `HAND_Z` | (0.40, 0.80) m | distance-to-camera range used |
| `ZONE` | (0.30, 1.20) m | hand ignored outside this distance |
| `MIRROR_X` | True | **set False if left/right is swapped** |
| `BASE_RANGE` | (40, 140)° | base turn used |
| `REACH` | (0.20, 0.32) m | gripper distance from the base |
| `HEIGHT` | (0.03, 0.22) m | gripper height above the board |
| `NEAR_MEANS_FAR` | True | hand closer to camera → arm reaches further |
| `CONTROL_MODE` | "absolute" | or "relative" (mouse-like) |

## Gripper angle → [[Inverse Kinematics]]
| Setting | Value | Meaning |
|---|---|---|
| `APPROACH_LOW` | −90° | gripper angle at the lowest height (straight down) |
| `APPROACH_HIGH` | −30° | angle when high (mostly forward) |
| `GRIP_TILT_FROM_H` | 0.16 m | height where it's fully tilted |

## Feel and safety
| Setting | Value | Meaning |
|---|---|---|
| `MOVE_SCALE` | 1.0 | relative mode: hand cm → gripper cm |
| `BASE_DEG_PER_M` | 200 | (old relative setting, now unused) |
| `READY` | (90°, 0.27 m, 0.12 m) | relative mode start pose |
| `FILTER_MIN_CUTOFF` | 0.8 | lower = steadier when still → [[One Euro Filter]] |
| `FILTER_BETA` | 6.0 | higher = less lag when fast |
| `SEND_HZ` | 25 | packets per second |
| `MAX_DEG_PER_SEND` | 6 | joint speed limit per packet |
| `GRIP_STEP` | 15 | gripper speed per packet |
| `NO_HAND_HOME_S` | 2.0 | seconds without a hand → HOME |
| `START_FRAMES` | 8 | steady frames before following |
| `GESTURE_FRAMES` | 6 | frames a gesture must last |

## Common tweaks
| Want | Change |
|---|---|
| Left/right swapped | `MIRROR_X = False` |
| Gripper opens wider | `GRIP_OPEN = 10` |
| Smoother, slower | `MAX_DEG_PER_SEND = 4`, `FILTER_MIN_CUTOFF = 0.5` |
| Snappier | `MAX_DEG_PER_SEND = 8`, `FILTER_BETA = 10` |
| Less hand movement needed | make `HAND_X/Y/Z` ranges smaller |
| Gripper flatter when high | `APPROACH_HIGH = -15` |
