---
tags: [script, gui, tkinter]
aliases: [Control Panel]
---
# control_panel.py

**Job:** one desktop window that checks everything is ready and **starts the other scripts** with a button press.
**Run:** double-click **Braccio Control Panel**, or `~/braccio-venv/bin/python ~/braccio-vision/control_panel.py`.
**Made with:** **Tkinter**, Python's built-in GUI toolkit. No extra installs except `python3-tk`.

> [!tip] Want to understand *how* it was built?
> Read [[How the Control Panel Was Built]]: a step-by-step tutorial that rebuilds this file from an empty window.

## What's on the window (top to bottom)
| Part | Widget | Code |
|---|---|---|
| Title + emergency note | `tk.Label` | `Panel.__init__` |
| "Before you start" checklist | `tk.LabelFrame` + labels | `__init__` |
| Status lights: WiFi / Camera / Arm | `tk.Canvas` with a circle | `_light`, `set_light` |
| Connect BraccioNet button | `tk.Button` | `connect` |
| Arm IP box | `tk.Entry` + `StringVar` | saved to `arm_ip.txt` |
| Re-check button | `tk.Button` | `refresh` |
| 5 mode buttons | `tk.Button` (coloured) | `start_live`, `start_sim`, `start_check`, `start_camera`, `start_calibrate` |
| STOP | `tk.Button` (red, disabled until something runs) | `stop` |
| Status text | `tk.Label` + `StringVar` | `self.status.set(...)` |
| Log | `tk.Text` (black) | `write`, `pump` |

## The helper functions (top of the file)
| Function | How it checks |
|---|---|
| `load_ip()` | reads `arm_ip.txt`, or uses `192.168.1.100` |
| `camera_present()` | runs a **separate** tiny Python process that asks pyrealsense2 how many cameras there are. A separate process means a camera crash can't freeze the panel |
| `current_wifi()` | runs `iwgetid -r`, falling back to `nmcli` |
| `connect_wifi(name)` | `nmcli connection up id BraccioNet`, then `nmcli dev wifi connect BraccioNet` |
| `arm_reachable(ip)` | `ping -c 1 -W 1 ip`: one ping, 1 s timeout. Exit code 0 = reachable |

## How a button runs a script
`run(label, args)`:
```python
self.proc = subprocess.Popen([PY, "-u"] + args, cwd=HERE, env=ENV,
                             stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                             text=True, bufsize=1, start_new_session=True)
```
| Argument | Why |
|---|---|
| `PY` = `sys.executable` | the **same venv Python** that runs the panel |
| `-u` + `PYTHONUNBUFFERED=1` | print lines **immediately** (otherwise Python batches output and the log lags) |
| `stdout=PIPE, stderr=STDOUT` | capture all output, errors included, so the panel can show it |
| `start_new_session=True` | the script gets its own **process group**, so STOP can signal it and anything it started |

A **reader thread** reads the output line by line and puts each line in a `queue.Queue`. The GUI's `pump()` empties the queue every 100 ms and writes to the log. When the script ends, the thread puts `None` in the queue: the "finished" signal.

> [!important] Why the thread + queue?
> Tkinter is **single-threaded**: only the main thread may touch widgets. Reading output **blocks** (waits), so doing it on the main thread would freeze the window. The background thread does the waiting and the main thread only reads the queue. Full explanation: [[How the Control Panel Was Built#Step 5 - run a script without freezing the window]].

## STOP
```python
os.killpg(self.proc.pid, signal.SIGINT)     # = pressing Ctrl+C
# 4 s later, if still running:
os.killpg(p.pid, signal.SIGTERM)            # = "please terminate now"
```
SIGINT makes Python raise `KeyboardInterrupt`, so `hand_to_braccio.py` runs its `finally:` block and **sends the arm HOME** before exiting.

## Safety in the panel
- LIVE asks for **confirmation** ("Area clear and hand near the 5V plug?").
- LIVE refuses if the camera is missing, and offers **Simulation** if the arm doesn't answer a ping.
- All mode buttons are **disabled** while something runs, so two programs can never fight over the camera or arm.
- `refresh()` doesn't touch the camera while a mode is using it.
- Closing the window while running → asks, then STOP, then closes.

## Calibrate arm is different
It needs **typing**, so instead of capturing output it opens a real terminal:
```python
subprocess.Popen(["lxterminal", "--title=Braccio calibration", "-e", PY, ".../calibrate.py", "--arm-ip", ip])
```

## Small details
- `ENV` sets `QT_QPA_FONTDIR` to hide harmless OpenCV font warnings, and the reader also filters those lines.
- The log keeps at most about 400 lines (`write` deletes the oldest 100).
- `root.after(ms, fn)` schedules work on the GUI thread. It's used for `pump` (every 100 ms) and the first `refresh`.
