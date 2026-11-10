---
tags: [braccio, howto]
aliases: [Daily Checklist, How to use]
---
# Operator Quick Start

## Every session
1. **Router** (BraccioNet) on, then wait about 1 minute.
2. **Arm 5V** plugged in. It moves to its start pose, so keep clear. Wait about 10 s.
3. **Pi**: double-click **Braccio Control Panel** on the desktop.
4. Check the three lights: **WiFi**, **Camera**, **Arm** should be green. If WiFi is red, press *Connect BraccioNet*.
5. Make sure the **Quest app is closed**. Only one controller at a time.
6. First run of the day: press **Arm check** and watch that the 3 poses look right.
7. Press **LIVE**, confirm the dialog, and keep a hand near the arm's 5V plug.

## Picking an object
Put a **small** object (eraser, bottle cap) **on the board**, 22–30 cm in front of the base.

| You do | Arm does |
|---|---|
| Show an **open hand**, hold still about 0.3 s | Starts following ("hand found – hold still…" then "open …") |
| Move your hand left/right | Base turns |
| Move your hand towards/away from the camera | Gripper reaches out / pulls back |
| **Lower your hand slowly** | Gripper goes down and turns to point at the board |
| Make a **fist** | Gripper closes (the arm holds still for a moment while your hand changes shape) |
| Lift your hand, keeping the fist | Carries the object |
| **Open** your hand | Drops it |
| Take your hand away for 2 s | Arm returns home (straight up) |

> [!tip] Two-step grab
> First line up **above** the object, then go **straight down**. Moving sideways and down at the same time is hard to control.

## Keys in the camera window
- **Space**: pause/resume (the arm holds its pose)
- **Q**: quit (the arm goes home)

## Stopping
- **STOP** button: the program sends the arm home, then exits.
- **Emergency**: pull the arm's **5V plug**.

## Where to stand
Camera at chest height pointing straight at you, about **60 cm** away. Keep your hand in the **middle** of the camera window. See [[02 Hardware and Network#Physical layout for gesture control]].
