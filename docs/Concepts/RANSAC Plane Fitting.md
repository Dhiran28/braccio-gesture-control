---
tags: [concept, depth, algorithm]
---
# RANSAC Plane Fitting

Used by [[objects_depth.py]] to find the **table** in a cloud of 3D points.

## The problem
Most points belong to the table, but some are objects, walls or noise. Ordinary "best fit" would be dragged off by those outliers.

## RANSAC = RANdom SAmple Consensus
Repeat 200 times:
1. Pick **3 random points** (3 points define a plane).
2. Make the plane: normal `n = (p2−p1) × (p3−p1)`, normalised; offset `d = −n·p1`.
3. Count **inliers**: points within **8 mm** of that plane (`|n·p + d| < 0.008`).
Keep the plane with the most inliers. Since the table is the biggest flat thing, it wins.

## Refinement
Take all the inliers and fit them exactly with **SVD** (least squares): the direction of least spread is the normal. Then flip the normal so it points **towards the camera**, which makes "height above the table" positive.

## Using the plane
For any point p: `height = n·p + d` = signed distance above the table. Points 1.5–25 cm up are objects.

## Why lock it?
The table doesn't move. Averaging 3 s of fits and then locking saves CPU, and stops a hand or object from tilting the "table".
