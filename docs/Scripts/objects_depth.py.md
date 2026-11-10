---
tags: [script, depth, objects, future]
---
# objects_depth.py

**Job:** find objects on a table using **depth only** (no AI). This is the basis of the future **point-to-pick / mining** mode, where the camera views the table and the arm picks what you select.
**Run:** `python objects_depth.py --show` → keep the table clear for 3 s → "Table locked" → place objects.
Keys: **r** = re-detect the table, **q** = quit. Writes `table_plane.json`.

> [!note] Camera placement for this mode
> Different from gesture mode: here the camera looks **down at the table** (50–70 cm above, tilted 30–45°), not at you.

## The four steps
1. **Depth → 3D points** (`depth_to_points`): every pixel becomes (x, y, z) using the lens maths. See [[Depth Camera and 3D Points]].
2. **Find the table** (`fit_plane_ransac`): the biggest flat surface. See [[RANSAC Plane Fitting]]. It's averaged over 3 s, then **locked**, because the table doesn't move.
3. **What sticks up?** For every point, `height = point · normal + d` = distance above the table. Points 1.5–25 cm above the table are object candidates.
4. **Group into objects** (`find_objects`): clean the mask (`MORPH_OPEN` removes specks), split into blobs (`connectedComponentsWithStats`), and drop blobs under 60 pixels.

## What it reports per object
| Field | Meaning |
|---|---|
| `centre_m` | 3D middle of the object (camera frame) |
| `base_on_table_m` | the centre **dropped onto the table**: where the gripper should aim |
| `top_m` | middle of the top surface |
| `height_m` | 95th percentile height (robust to noise) |
| `footprint_m` | widest size seen from above: will it fit in the gripper? |
| `bbox` | rectangle in the image, for drawing |

## Depth clean-up filters (RealSense built-ins)
`decimation(2)` halves the resolution for 4× less work → `disparity` → `spatial` (smooth across pixels) → `temporal` (smooth over time) → back to depth → `hole_filling`.

## Tested
On a synthetic scene (camera 60 cm up, tilted 35°, blocks of 3/5/8 cm) it found all 3 objects, with heights within 2 mm.

## What's still missing for point-to-pick
A **camera → robot calibration**: a transform that converts `base_on_table_m` (camera frame) into the arm's base angle and reach. See [[Learning Path and Exercises]].
