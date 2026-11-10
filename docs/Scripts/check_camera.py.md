---
tags: [script, camera, test]
---
# check_camera.py

**Job:** prove the camera works before blaming anything else.
**Run:**
```bash
python check_camera.py           # 10 s, text only
python check_camera.py --show    # live window: colour | depth side by side (q = quit)
python check_camera.py --seconds 30
```
**Control Panel button:** *Camera test*.

## What it measures
| Value | How | Good |
|---|---|---|
| **FPS** | frames counted ÷ seconds | about 30 (below 20 → USB 2 or power problem) |
| **Centre distance** | median of a 10×10 depth patch in the middle | matches a tape measure |
| **Valid depth %** | share of pixels with depth > 0 | above 60 % |

At the end it prints **CAMERA OK** or **CAMERA NEEDS ATTENTION**, with the reason.

## Code walk-through
```python
frames = pipe.wait_for_frames()             # blocks until a new depth+colour pair arrives
depth_m = np.asanyarray(d.get_data()) * scale   # raw 16-bit numbers -> metres
patch = depth_m[h//2-5:h//2+5, w//2-5:w//2+5]   # 10x10 pixels in the middle
patch = patch[patch > 0]                    # 0 means "no depth here"
centre = np.median(patch)                   # median ignores odd outliers
valid = (depth_m > 0).mean()                # True/False mean = fraction of True
```
`np.hstack([color, dep])` puts two images side by side for the window.

## Why a median, not an average?
Depth has occasional wild pixels (edges, reflections). One 5 m value would wreck an average; a median just ignores it. The same trick is used for the hand in [[hand_depth.py]].

Related: [[rs_common.py]], [[Depth Camera and 3D Points]]
