---
tags: [concept, robotics, maths, ik]
aliases: [IK]
---
# Inverse Kinematics

- **Forward kinematics (FK):** "If the joints are at these angles, where is the gripper?" This is easy: add up the links.
- **Inverse kinematics (IK):** "I want the gripper **here**. What angles do I need?" This is harder: there can be 0, 1, 2 or infinitely many answers.

## Simplifying the Braccio
The base (M1) just turns the whole arm to face a direction. After that, shoulder, elbow and wrist all bend in **one vertical plane**. So the problem becomes **2D (side view)**: reach out and height up.

```
            elbow
           ●───────● wrist
      L1  /         \  L3 (to gripper tip)
         /           \
shoulder●             ● tip  (reach, height)
        | L0
  ======●====== board
       base
```
| Link | Length (m) | Code |
|---|---|---|
| base → shoulder axle | 0.0715 | `L0` |
| shoulder → elbow | 0.125 | `L1` |
| elbow → wrist | 0.125 | `L2` |
| wrist → gripper tip | 0.192 | `L3` |

Angles in the code are **absolute**: measured from horizontal (0° = pointing forward, 90° = straight up, −90° = straight down).
- `a1`: upper arm, `a2`: forearm, `a3` (= φ, "phi"): gripper.

## The trick: choose the gripper angle first
Three joints for a 2D target means there are infinitely many solutions. So we **pick** the gripper angle φ, which leaves a 2-link problem with a known formula.

1. **Pick φ**: near the board we want the gripper pointing down (−90°); higher up, tilted forward (−30°). In between it blends:
   ```python
   k = (height - 0.03) / (0.16 - 0.03)      # 0 at the lowest height, 1 at 16 cm and above
   want = -90 + k * (-30 - -90)
   ```
2. **Step back from the tip to the wrist**, along the gripper:
   ```python
   wr = reach  - L3 * cos(φ)
   wh = height - L0 - L3 * sin(φ)        # relative to the shoulder axle
   ```
3. **Solve the 2-link arm (L1, L2) to reach the wrist point**, using the **law of cosines**:
   ```python
   c  = (wr² + wh² - L1² - L2²) / (2·L1·L2)     # cos(elbow bend)
   q2 = ±acos(c)                                 # two answers: elbow one way or the other
   q1 = atan2(wh, wr) - atan2(L2·sin q2, L1 + L2·cos q2)
   a1 = q1,  a2 = q1 + q2,  a3 = φ
   ```
   If `|c| > 1`, the wrist point is too far or too close: that φ is impossible.
4. **Check limits** (`within_limits`): every servo inside its range (2° margin), and the **upper arm not leaning back** (`a1 ≤ 92°`).
5. If it fails, try the next φ (5° steps, nearest to `want` first), then the other elbow. If nothing fits → `None`, and `main()` nudges the target out or up by up to 11 cm until it fits.

## Worked example (no calibration offsets)
Target: reach **0.22 m**, height **0.05 m**.
- want φ ≈ −81°. Candidates are tried nearest first:
  - −80, −85, −90, −95: **impossible** (`|c| > 1`, the wrist point would be closer than the folded arm allows)
  - −75, −70: reachable, but the wrist servo would need 0–2°, below its limit + margin
  - **−65°: fits** ✓
- Wrist point: wr = 0.139, wh = 0.153 m (distance 0.206 m < L1+L2 = 0.25 ✓).
- Result: a1 = **82.1°**, a2 = **13.3°**, a3 = **−65°**.
- Servos ([[Servo Angles, Offsets and Calibration]]): shoulder 90+(82.1−90) = **82**, elbow 90+(13.3−82.1) = **21**, wrist 90+(−65−13.3) = **12** → packet `90,82,21,12,90,20`.
- FK check: the tip lands at (0.220, 0.050). ✓

## Why "upper arm never leans back"?
Near the base, the maths found a valid but silly pose: shoulder leaning **backwards**, forearm folding forward, wrist bent to its limit, gripper hanging next to the base. It was seen in your video. Forbidding `a1 > 92°` keeps poses human-like (reaching forward), and the minimum reach was raised to 20 cm.

## Reachable area (with your calibration)
Roughly: reach 20–32 cm, height 3–22 cm. Lower and closer is limited by the wrist's range; higher and closer needs a backward-leaning shoulder (not allowed). Objects are easiest to pick at **22–30 cm**.

Code: [[hand_to_braccio.py#ik - reach and height to joint angles]]
