---
tags: [concept, safety]
---
# Safety Design

Layers, from the outermost (human) to the innermost (code):

| # | Layer | Where |
|---|---|---|
| 1 | **Pull the 5V plug**: always works | physical |
| 2 | Confirmation dialogs before LIVE / check / calibrate | [[control_panel.py]] |
| 3 | Only one mode at a time (buttons disabled while running) | panel |
| 4 | STOP = Ctrl+C → the script's `finally` sends **HOME** | panel + script |
| 5 | Simulation is the default (`--arm-ip` must be given) | [[hand_to_braccio.py]] |
| 6 | Arm check before LIVE (3 slow known poses) | `--check` |
| 7 | Interaction zone 0.3–1.2 m (people behind you are ignored) | `ZONE` |
| 8 | Hold-still start, debounced gestures | [[Debouncing and State Machines]] |
| 9 | IK rejects poses outside servo limits or leaning back | [[Inverse Kinematics]] |
| 10 | Never below 3 cm above the board | `HEIGHT` |
| 11 | **Speed limit**: max 6°/packet per joint (150°/s), gripper 15°/packet | main loop |
| 12 | No hand for 2 s → HOME | `NO_HAND_HOME_S` |
| 13 | Clamping to servo limits in `to_servos` and on the Arduino | both ends |
| 14 | Gripper "closed" = 70, not 73, so it doesn't stall the servo hard on an object | `GRIP_CLOSED` |

## Design rule
**Every exit path ends in HOME.** Normal quit (Q), Ctrl+C, STOP, a crash inside the loop (`finally`), and `--check` interrupted (`try/finally` in `run_check`).

## Not covered (be aware)
- Collisions with objects or people. There's no force sensing. Keep hands out of the arm's reach while LIVE.
- SIGTERM/SIGKILL skip `finally`. The panel only uses SIGTERM as a last resort after 4 s.
- Pi overheating with no cooler: check `vcgencmd measure_temp` (keep it under about 80 °C).
