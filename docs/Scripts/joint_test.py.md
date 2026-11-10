---
tags: [script, diagnosis]
---
# joint_test.py

**Job:** diagnosis. Moves **one joint at a time** so you can see whether the real arm matches the numbers.
**Run:** `python joint_test.py` (optional: the arm IP as an argument). Stand at the **side** of the arm and photograph each step.

| Step | Servos | Should look like |
|---|---|---|
| 1 | `90,90,90,90,90,20` | candle, straight up |
| 2 | shoulder 45 | whole straight arm leans **forward** about 45° |
| 3 | + elbow 45 | forearm bends another 45° |
| 4 | + wrist 45 | gripper bends another 45° |
| 5 | `90,47,67,6,90,20` | gripper about 5 cm above the board |

Each pose is held 8 s (`hold()` re-sends every 0.1 s), then it returns to candle.

## What it found in your arm
All joints bent the **right direction** (no `flip` needed), but the shoulder fell about 12–15° short and the wrist about 10–15° short. That led to the calibration `s-12`, `w-10`.

## How to read results
| Step 2 shows | Means | Fix |
|---|---|---|
| leans about 45° forward | shoulder OK | none |
| leans **backward** | direction reversed | `flip s` in [[calibrate.py]] |
| leans only 10–20° | sagging / weak power | check 5 V 5 A supply, then offset |
| crooked at step 1 | horn offset | `s±N` until candle is straight |

It's a tiny script (36 lines): a good first one to read and modify.
