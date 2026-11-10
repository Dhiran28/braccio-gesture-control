---
tags: [learning, exercises]
---
# Learning Path and Exercises

## Order to read the code
1. `joint_test.py` (36 lines): UDP and a loop
2. `rs_common.py` + `check_camera.py`: camera basics, numpy
3. `hand_depth.py`: MediaPipe, 3D points, geometry
4. `hand_to_braccio.py`, in this order: `to_servos` → `fk` → `ik` → `hand_to_target` → `OneEuro` → `main()`
5. `calibrate.py`: threads, interactive input
6. `control_panel.py` with [[How the Control Panel Was Built]]
7. `objects_depth.py`: point clouds, RANSAC, OpenCV blobs

## Exercises (easy → hard)
1. **Change a packet.** Edit `joint_test.py` to add a step with the base at 45°.
2. **Print the 3D wrist.** In `hand_to_braccio.py`, add the wrist XYZ to the status line.
3. **Gripper strength.** Make `GRIP_CLOSED` depend on how tight the fist is (distance from fingertip to palm).
4. **New gesture.** Make *point* (index only) turn the base slowly while held.
5. **Record and replay.** Save every `sent` packet with a timestamp to a CSV, then write `replay.py` that sends it again.
6. **Panel button.** Add "Objects test" to the Control Panel.
7. **Camera → robot calibration (point-to-pick, step 1).** Put the gripper tip at 4+ known spots; record the camera XYZ of a marker held there; solve the rigid transform (Kabsch/SVD).
8. **Point-to-pick.** Combine `objects_depth.py` + that transform + `ik()`: click an object in the window → the arm picks it.
9. **Quest link.** Send the selected object from the Quest 3 app instead of a mouse click.

## Ideas to learn next
- Homogeneous transforms (4×4 matrices) for camera ↔ robot
- PID control and trajectory planning (smooth paths instead of speed limits)
- ROS 2: the standard robotics framework, the same ideas as here at scale
- YOLO on the AI HAT+: object **names**, not just shapes
