---
tags: [concept, camera, depth]
---
# Depth Camera and 3D Points

## How the D435 measures depth
It has **two infrared cameras** about 5 cm apart (like your eyes), plus an **IR projector** that sprays invisible dots so plain surfaces have texture. A point appears at slightly different positions in the left and right images. That shift (**disparity**) is bigger for near things. The camera's chip turns the disparity into a **distance for every pixel**: the depth image.

| Fact | Value |
|---|---|
| Depth resolution used | 848×480 @ 30 fps |
| Minimum distance | about 0.28 m (closer = no depth, shows black) |
| Accuracy | about 2 % of distance (≈ ±1 cm at 60 cm) |
| Raw unit | 1 mm (`depth_scale` = 0.001) |
| Trouble with | shiny/black surfaces, sunlight, thin things (fingers!) far away |

A separate **RGB camera** gives the colour image. It's in a slightly different place, which is why colour and depth pixels don't line up 1:1.

## From pixel to metres (pinhole camera model)
A camera turns a 3D point (X, Y, Z) into a pixel (u, v):
```
u = fx · X/Z + cx          v = fy · Y/Z + cy
```
- `fx, fy`: focal lengths in pixels (how "zoomed" the lens is)
- `cx, cy`: the image centre (principal point)
These four numbers are the **intrinsics**; the camera stores them and RealSense gives them to you.

**Deprojection** runs that backwards: if you know the pixel and the depth Z,
```
X = (u - cx) / fx · Z          Y = (v - cy) / fy · Z
```
That's exactly `depth_to_points()` in [[objects_depth.py]], and what `rs2_deproject_pixel_to_point` does in [[hand_depth.py]].

> [!example] Worked example
> fx = 615, cx = 320. Your wrist is at pixel u = 443 with depth Z = 0.60 m.
> X = (443 − 320) / 615 × 0.60 = **0.12 m**, so your wrist is 12 cm to the right of the camera's centre line.

## Camera axes
x → right, y ↓ **down**, z → **out of the lens**. Raising your hand makes **y negative**. See [[01 System Overview#Three coordinate systems (the source of most confusion)]].

## Intrinsics vs extrinsics
- **Intrinsics**: one sensor's lens maths (fx, fy, cx, cy, distortion).
- **Extrinsics**: how two sensors sit relative to each other (rotation + translation). They're needed to go from a colour pixel to the right depth pixel (`d2c`, `c2d` in the code).

## Why use a median of a patch?
A single depth pixel at the edge of a finger may hit the wall behind. The median of a 7×7 patch ignores those outliers.
