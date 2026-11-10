---
tags: [terminal, howto]
---
# Copying Files via USB

The Pi doesn't need Claude or any login. New versions of scripts travel on a **USB drive**.

## Steps
1. **Mac**: download the file and save it onto the USB drive (replace the old copy if asked).
2. Plug the USB drive into the **Pi**. It appears as `/media/braccio/USB DEVICE` (a desktop icon too).
3. In the Control Panel press **STOP** if something is running.
4. Terminal:
   ```bash
   cp /media/braccio/*/hand_to_braccio.py ~/braccio-vision/
   ```
   No output means success. `cp` overwrites the old file.
5. Check it's the new version (optional). Search for a setting you know is new:
   ```bash
   grep -n "CONTROL_MODE" ~/braccio-vision/hand_to_braccio.py
   ```
6. Press **LIVE** again.

## Whole project as a zip
```bash
cd ~
cp /media/braccio/*/braccio-vision.zip ~/
unzip -o braccio-vision.zip          # -o = overwrite existing files without asking
```
> [!note] Your calibration is safe
> `calibration.json` and `arm_ip.txt` are not inside the zip, so unzipping never overwrites them.

## What the pieces mean
| Piece | Meaning |
|---|---|
| `cp` | copy |
| `/media/braccio/` | where Raspberry Pi OS puts USB drives for user `braccio` |
| `*` | "whatever the drive is called" (works with the space in `USB DEVICE`) |
| `~/braccio-vision/` | destination folder; the trailing `/` means "into this folder, keep the name" |

## Before ejecting
```bash
sync        # make sure everything is written
```
Then right-click the USB icon on the desktop → **Eject**.
