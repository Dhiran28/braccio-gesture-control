---
tags: [concept, ai, mediapipe]
---
# MediaPipe Hand Landmarks

**MediaPipe** (by Google) is a set of ready-trained AI models. The **Hand Landmarker** finds hands in an image and returns **21 points** per hand.

```
        8   12  16  20        tips
        |   |   |   |
        7   11  15  19
        |   |   |   |
        6   10  14  18        PIP (middle knuckles)
   4    |   |   |   |
   3    5---9---13--17        MCP (base knuckles)
    2    \          /
     1    \        /
       ----- 0 ----           0 = wrist
```
| Number | Name in code |
|---|---|
| 0 | `WRIST` |
| 4 | `THUMB_TIP` |
| 5, 9, 13, 17 | `INDEX_MCP`, `MIDDLE_MCP`, …, `PINKY_MCP` (base knuckles) |
| 6, 10, 14, 18 | `INDEX_PIP`, … (middle knuckles) |
| 8, 12, 16, 20 | fingertips |

## Two kinds of output
| Output | Units | Used for |
|---|---|---|
| `hand_landmarks` | x, y as **fractions of the image** (0–1); z is relative depth only | where the hand is **in the picture** → look up camera depth |
| `hand_world_landmarks` | **metres**, centred on the hand; MediaPipe's own 3D estimate | **hand shape** (gesture). Not affected by camera depth noise |

The project uses **both**: picture position + camera depth for *where* the hand is, and world landmarks for *what shape* it is.

## How it runs
- The model file: `models/hand_landmarker.task` (downloaded by [[setup_pi.sh]]).
- `RunningMode.VIDEO`: it tracks from frame to frame, which is faster and steadier. It needs increasing timestamps.
- `min_hand_detection_confidence=0.6`: how sure it must be to report a hand.
- On the Pi 5 CPU: about 26 fps. The AI HAT+ isn't used, and isn't needed for this.

Next: [[Gesture Classification]]
