---
tags: [script, camera, python]
---
# rs_common.py

**Job:** shared helper. Starts the D435 the same way for every script, and turns depth into a colourful picture.
**Not run directly:** other scripts `import` it.

## Functions

### `start_pipeline(color=True, depth=True)` → `(rs, pipe, profile, depth_scale)`
1. Imports `pyrealsense2` (Intel's Python library) as `rs`.
2. Lists connected cameras. If there are none, it exits with a helpful message.
3. Prints name, serial number, firmware and **USB type**. It **warns if USB 2**: depth is unreliable on USB 2.
4. Configures the streams:
   - depth **848×480**, format `z16` (16-bit distance numbers), 30 fps
   - colour **640×480**, `bgr8` (OpenCV's colour order), 30 fps
5. Turns on the **IR emitter** (the dot projector), which gives better depth on plain surfaces.
6. Throws away 30 frames so auto-exposure can settle.
7. Returns `depth_scale`: how many metres one depth unit is (D435: **0.001**, so a raw value of 600 = 0.6 m).

### `colorize_depth(depth_m, max_m=1.5)` → image
Maps distance to colour (near = red/warm, far = blue/cool, no data = black) with OpenCV's `COLORMAP_JET`. Used only for display.

## Concepts
- **Pipeline**: RealSense's object that delivers matched sets of frames (`wait_for_frames()`).
- **Profile**: the active settings. Used later to read **intrinsics** (lens maths) and **extrinsics** (how the colour and depth sensors sit relative to each other). See [[Depth Camera and 3D Points]].

## Why the import is inside the function
`import pyrealsense2` only happens when a camera is actually needed. Tests and the Control Panel can import other parts without the camera library being present.

Used by: [[check_camera.py]], [[hand_depth.py]], [[objects_depth.py]], [[hand_to_braccio.py]]
