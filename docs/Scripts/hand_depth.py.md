---
tags: [script, hand, mediapipe]
---
# hand_depth.py

**Job:** (1) a standalone test of hand tracking with real 3D positions, and (2) a **library** of hand helpers used by [[hand_to_braccio.py]].
**Run:** `python hand_depth.py --show` (options `--zmin 0.3 --zmax 1.5`)

## Pieces other scripts import
| Name | What |
|---|---|
| `WRIST, THUMB_TIP, INDEX_MCP, …` | MediaPipe landmark numbers (0 = wrist, 4 = thumb tip, 8 = index tip…). See [[MediaPipe Hand Landmarks]] |
| `KEY_POINTS` | the 13 points we look up depth for (not all 21, to stay fast) |
| `HAND_CONNECTIONS` | pairs of points to draw the green skeleton |
| `classify_gesture(p)` | → `"pinch" / "fist" / "open" / "point" / "unknown"`. See [[Gesture Classification]] |
| `depth_at_color_pixel(...)` | finds the depth for one **colour** pixel without aligning whole images |

## depth_at_color_pixel - the clever bit
The colour and depth sensors are a few cm apart and have different lenses, so pixel (u, v) in the colour image is **not** the same pixel in the depth image. The usual fix is "align the whole depth frame to colour", but that's slow on a Pi.

Instead, for each of 13 points:
1. `rs.rs2_project_color_pixel_to_depth_pixel(...)` searches along the line of sight (0.1–3 m) for the matching depth pixel.
2. It takes a **7×7 patch** around it (`win=3`), drops zeros, and returns the **median** in metres.

Then `rs.rs2_deproject_pixel_to_point(c_intr, [u, v], z)` turns (pixel, depth) into **X, Y, Z in metres**. See [[Depth Camera and 3D Points]].

## Main loop (test mode)
```
camera frame → MediaPipe (21 points, image coords)
            → depth for 13 key points → 3D points
            → if wrist within zmin..zmax: gesture + smoothed wrist XYZ
            → print about 4 times/s, draw skeleton
```
The **interaction zone** (0.3–1.5 m here) ignores people walking behind you.

> [!note] Change made later
> In `hand_to_braccio.py` the gesture is now decided from MediaPipe's **world landmarks** (its own 3D hand model), not camera depth. Depth on thin fingers was too noisy. This test script still uses camera depth, which is useful for comparison.
