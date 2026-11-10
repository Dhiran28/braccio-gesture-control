---
tags: [concept, filter, smoothing]
---
# One Euro Filter

**Problem:** hand tracking jitters by a few mm every frame. Plain smoothing (averaging) removes jitter but adds **lag**: the arm trails behind fast moves. You can't have both with a fixed amount of smoothing.

**Idea** (Casiez, Roussel & Vogel, CHI 2012): change the smoothing **with speed**.
- Hand still or slow → **heavy** smoothing (jitter gone; lag doesn't matter because you're not moving).
- Hand fast → **light** smoothing (follows quickly; jitter isn't noticeable while moving).

## The maths (what `class OneEuro` does each frame)
1. Estimate the speed `dx` (also lightly smoothed, with cutoff `d_cutoff = 1 Hz`).
2. `cutoff = min_cutoff + beta × |speed|`
3. Turn the cutoff into a blend factor: `α = 1 / (1 + τ/dt)` with `τ = 1/(2π·cutoff)`
4. `x_smooth = α·x_new + (1−α)·x_smooth`
A higher cutoff gives α near 1 (trust the new value: responsive). A lower cutoff gives α near 0 (keep the old value: smooth).

## Settings
| Setting | Value | Turn it… |
|---|---|---|
| `FILTER_MIN_CUTOFF` | 0.8 Hz | **down** (0.5) if it twitches when your hand is still |
| `FILTER_BETA` | 6.0 | **up** (10) if it lags behind fast moves |

The official tuning order: set beta = 0, lower `min_cutoff` until still-hand jitter is gone, then raise beta until fast moves don't lag.

## Measured on test data
4 mm of random noise on a still hand → 1.4 mm after filtering. A fast 26 cm/s move lagged about 1 cm.

## Reset
`filt.reset()` is called when the hand is lost or changes shape, so the filter doesn't drag an old position into a new one.

Reference: https://gery.casiez.net/1euro/
