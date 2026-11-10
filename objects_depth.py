"""Step 3: find objects on the table using depth only (no AI model).

1. Turn the depth image into 3D points.
2. Find the flat table surface (RANSAC plane fit). Locked after a few seconds,
   because the table doesn't move.
3. Anything sticking up 1.5 - 25 cm above the table = object.
4. Group those pixels into blobs and report each object's 3D centre, height and size.

    python objects_depth.py            # text output
    python objects_depth.py --show     # live depth view with boxes + labels
Keys in --show mode: r = re-detect table, q = quit
Saves the locked table plane to table_plane.json (used later for calibration).
"""
import argparse
import json
import time

import numpy as np


# ---------- pure-numpy core (testable without a camera) ----------

def depth_to_points(depth_m, fx, fy, cx, cy):
    """Depth image (m) -> HxWx3 array of camera-frame points (x right, y down, z forward)."""
    h, w = depth_m.shape
    us, vs = np.meshgrid(np.arange(w), np.arange(h))
    x = (us - cx) / fx * depth_m
    y = (vs - cy) / fy * depth_m
    return np.dstack([x, y, depth_m])


def fit_plane_ransac(pts, iters=200, thresh=0.008, rng=None):
    """pts: Nx3. Returns (normal, d) with normal.p + d = 0, normal pointing toward the camera."""
    rng = rng or np.random.default_rng(0)
    best_inliers, best = -1, None
    n = len(pts)
    if n < 100:
        return None
    for _ in range(iters):
        s = pts[rng.choice(n, 3, replace=False)]
        nrm = np.cross(s[1] - s[0], s[2] - s[0])
        norm = np.linalg.norm(nrm)
        if norm < 1e-9:
            continue
        nrm /= norm
        d = -nrm @ s[0]
        inl = np.count_nonzero(np.abs(pts @ nrm + d) < thresh)
        if inl > best_inliers:
            best_inliers, best = inl, (nrm, d)
    if best is None:
        return None
    # refine with least squares on inliers
    nrm, d = best
    inl = pts[np.abs(pts @ nrm + d) < thresh]
    c = inl.mean(axis=0)
    _, _, vt = np.linalg.svd(inl - c, full_matrices=False)
    nrm = vt[-1]
    d = -nrm @ c
    if d < 0:            # camera (origin) should be on the positive side
        nrm, d = -nrm, -d
    return nrm, float(d)


def find_objects(points, plane, min_h=0.015, max_h=0.25, min_pixels=60):
    """points: HxWx3, plane: (normal, d). Returns list of dicts and the object mask."""
    import cv2
    nrm, d = plane
    valid = points[..., 2] > 0
    height = points @ nrm + d                  # signed distance above table (toward camera)
    mask = valid & (height > min_h) & (height < max_h)
    mask = cv2.morphologyEx(mask.astype(np.uint8), cv2.MORPH_OPEN, np.ones((5, 5), np.uint8))
    n, labels, stats, _ = cv2.connectedComponentsWithStats(mask, connectivity=8)
    objects = []
    for i in range(1, n):
        if stats[i, cv2.CC_STAT_AREA] < min_pixels:
            continue
        sel = labels == i
        p = points[sel]
        hts = height[sel]
        top = p[hts > np.percentile(hts, 70)]           # top surface of the object
        centre = np.median(p, axis=0)
        # ground point: centre dropped onto the table plane (where the gripper should aim)
        base = centre - (centre @ nrm + d) * nrm
        # footprint: extent of the object's points flattened onto the table, along 2 in-plane axes
        a = np.cross(nrm, [1.0, 0, 0] if abs(nrm[0]) < 0.9 else [0, 1.0, 0])
        a /= np.linalg.norm(a)
        b = np.cross(nrm, a)
        footprint = max(np.ptp(p @ a), np.ptp(p @ b))
        objects.append({
            "id": len(objects) + 1,
            "centre_m": centre.round(4).tolist(),
            "base_on_table_m": base.round(4).tolist(),
            "top_m": np.median(top, axis=0).round(4).tolist() if len(top) else centre.round(4).tolist(),
            "height_m": round(float(np.percentile(hts, 95)), 4),
            "footprint_m": round(float(footprint), 4),
            "pixels": int(stats[i, cv2.CC_STAT_AREA]),
            "bbox": [int(stats[i, cv2.CC_STAT_LEFT]), int(stats[i, cv2.CC_STAT_TOP]),
                     int(stats[i, cv2.CC_STAT_WIDTH]), int(stats[i, cv2.CC_STAT_HEIGHT])],
        })
    return objects, mask


# ---------- camera loop ----------

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--show", action="store_true")
    ap.add_argument("--max-range", type=float, default=1.5, help="ignore depth beyond this (m)")
    ap.add_argument("--lock-after", type=float, default=3.0, help="seconds of averaging before locking the table")
    args = ap.parse_args()

    import cv2
    from rs_common import start_pipeline, colorize_depth

    rs, pipe, profile, scale = start_pipeline(color=False)
    decimate = rs.decimation_filter(2)                  # 848x480 -> 424x240: 4x less work
    to_disp, to_depth = rs.disparity_transform(True), rs.disparity_transform(False)
    spatial, temporal = rs.spatial_filter(), rs.temporal_filter()
    holes = rs.hole_filling_filter(1)

    plane, plane_samples, t_start = None, [], time.time()
    last_print = 0
    try:
        while True:
            f = pipe.wait_for_frames().get_depth_frame()
            if not f:
                continue
            f = decimate.process(f)
            f = to_disp.process(f); f = spatial.process(f); f = temporal.process(f); f = to_depth.process(f)
            f = holes.process(f).as_depth_frame()
            intr = f.profile.as_video_stream_profile().get_intrinsics()
            depth_m = np.asanyarray(f.get_data()).astype(np.float32) * scale
            depth_m[depth_m > args.max_range] = 0
            pts = depth_to_points(depth_m, intr.fx, intr.fy, intr.ppx, intr.ppy)

            if plane is None:
                flat = pts[depth_m > 0][::7]
                pl = fit_plane_ransac(flat)
                if pl is not None:
                    plane_samples.append(np.r_[pl[0], pl[1]])
                if time.time() - t_start > args.lock_after and plane_samples:
                    m = np.median(np.array(plane_samples), axis=0)
                    plane = (m[:3] / np.linalg.norm(m[:3]), float(m[3]))
                    tilt = 90 - np.degrees(np.arccos(abs(plane[0][2])))
                    print(f"\nTable locked: {plane[1]:.3f} m from camera, camera looking down at ~{tilt:.0f} deg")
                    with open("table_plane.json", "w") as fh:
                        json.dump({"normal": plane[0].tolist(), "d": plane[1]}, fh, indent=2)
                    print("Saved table_plane.json\n")
                else:
                    print("Finding table... keep the table clear of hands", end="\r")
                continue

            objects, mask = find_objects(pts, plane)
            now = time.time()
            if now - last_print > 0.5:
                if objects:
                    for o in objects:
                        x, y, z = o["base_on_table_m"]
                        print(f"Object {o['id']}: base X {x:+.3f} Y {y:+.3f} Z {z:.3f} m | "
                              f"height {o['height_m']*100:.1f} cm | width ~{o['footprint_m']*100:.1f} cm")
                else:
                    print("No objects on table")
                print("-" * 70)
                last_print = now

            if args.show:
                img = colorize_depth(depth_m, args.max_range)
                img[mask > 0] = (img[mask > 0] * 0.4 + np.array([255, 255, 255]) * 0.6).astype(np.uint8)
                for o in objects:
                    x, y, w, h = o["bbox"]
                    cv2.rectangle(img, (x, y), (x + w, y + h), (255, 255, 255), 1)
                    cv2.putText(img, f"{o['id']}: {o['height_m']*100:.0f}cm", (x, max(10, y - 4)),
                                cv2.FONT_HERSHEY_SIMPLEX, 0.4, (255, 255, 255), 1)
                img = cv2.resize(img, (img.shape[1] * 2, img.shape[0] * 2), interpolation=cv2.INTER_NEAREST)
                cv2.imshow("Objects on table  (r = re-detect table, q = quit)", img)
                k = cv2.waitKey(1) & 0xFF
                if k == ord("q"):
                    break
                if k == ord("r"):
                    plane, plane_samples, t_start = None, [], time.time()
    finally:
        pipe.stop()


if __name__ == "__main__":
    main()
