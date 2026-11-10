---
tags: [script, bash, legacy]
---
# launch scripts (launch/*.sh)

**Status:** older, terminal-based launchers. They still work, but the [[control_panel.py]] does the same things in one window.

| File | Does |
|---|---|
| `common.sh` | shared setup: `ARM_IP=192.168.1.100`, `cd` to the project, activate the venv, and the functions `camera_ok`, `arm_ok`, `finish` |
| `live.sh` | camera check → arm ping (offers simulation if it fails) → LIVE |
| `sim.sh` | camera check → simulation |
| `check.sh` | arm ping → "Press Enter" → 3 test poses |
| `camera_test.sh` | 10 s camera test, then the live view |

Run one with `bash ~/braccio-vision/launch/live.sh`.

## Bash ideas they show
```bash
source "$(dirname "$0")/common.sh"     # load shared functions into this script
camera_ok || { finish; exit 1; }       # if camera_ok fails: run finish, then exit
read -rp "Run SIMULATION instead? [y/N] " a
[[ "$a" =~ ^[Yy] ]] && python hand_to_braccio.py --show   # regex: starts with y or Y
```
They're a good comparison with the panel: the **same logic** (check camera → check arm → run), as a script instead of a GUI.
