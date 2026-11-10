---
tags: [script, desktop, bash]
---
# install_shortcuts.sh

**Job:** put one icon, **Braccio Control Panel**, on the desktop.
**Run once:** `bash ~/braccio-vision/install_shortcuts.sh`

## What it does
1. Installs `python3-tk` if Tkinter is missing.
2. Deletes old `braccio-*.desktop` icons (the earlier 4-icon version).
3. Writes `~/Desktop/braccio-control-panel.desktop`:
```ini
[Desktop Entry]
Type=Application
Name=Braccio Control Panel
Exec=/home/braccio/braccio-venv/bin/python /home/braccio/braccio-vision/control_panel.py
Icon=input-gaming
Terminal=false
```
   A `.desktop` file is the Linux standard for "an app icon": name, command and picture.
4. `chmod +x` and `gio set … metadata::trusted true` mark it as trusted.
5. Sets `quick_exec=1` in `~/.config/libfm/libfm.conf`, so double-clicking runs it without the "Execute / Open?" question (the Pi file manager is based on libfm).

## Heredoc
```bash
cat > file <<EOD
...text...
EOD
```
writes everything between the markers into `file`. `$HOME` inside it is replaced with your real home folder.
