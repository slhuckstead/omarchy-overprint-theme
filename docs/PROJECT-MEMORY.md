# Overprint — project memory

Handoff state for the theme and its tooling. The generator's source of truth is
`~/.local/share/overprint` (this repo carries a copy under `generator/`); the two
sibling repos, `omarchy-overprint-slate-theme` and `omarchy-overprint-light-theme`,
are publish targets of the same work and deliberately carry no handoff file of their
own. The operator's manual is `~/.local/share/overprint/README.md`.

## Session Status

```
STATUS: Three-variant Omarchy theme, feature-complete against both agreed lists. Adapts grounds on solar, dims to the room, re-pulls its own wallpaper weekly. All three repos clean and pushed.
FOCUS: Read the overnight calibration data and settle whether the room's light can drive the ground on this machine, or whether solar is the permanent answer.
FOCUS_SINCE: 2026-09-06
FOCUS_CARRIED: 0
LAST_SESSION: 2026-09-06 — twelve commits across the three repos. Closed the five-item
  agreed scope (screensaver across variants, variant installers, app-theme audit,
  wallpaper cycling, sensor+solar ground adaptation) and a five-item follow-on list
  (per-pull registration, weekly re-pull, plate proof, colophon, LOCATE=weather).
  VERIFIED BY MEASUREMENT, not assumption: camera gating proven with a marker script
  (solar + BRIGHTNESS=off opens the lens zero times); control loop noise cut from 9
  panel moves / 22.6% travel to 1 move / 3.1%; boot passphrase geometry recomputed
  from installed assets (entry y=934 on a 1600px screen). UNVERIFIED: the boot screen
  itself — the machine has not rebooted since the Plymouth change.
  Biggest find was unplanned: unlock.png is Plymouth's LOGO, not a lock screen, and
  shipping a full-screen wallpaper there had been pushing the LUKS passphrase box off
  the bottom of the display. Fixed to an 800x188 wordmark.
  Two corrections from Seth, both now written into the source rather than just fixed:
  the capture guard was defeated by inserting a cursor fix between the check and the
  shutter; and the registration drift was set by asking a press-quality question when
  the drift is the style.
BACKLOG:
  1. Confirm the boot screen at the next reboot — passphrase box visible, wordmark centred.
  2. Upstream issue omacom/omarchy#10533 (dimText below AA on 19 of 22 first-party
     themes) awaits triage. If they fix it, DELETE ~/.config/omarchy/themed/pi.json.tpl
     or it shadows their template indefinitely.
  3. Sensor thresholds stay blank until the calibration says otherwise; GROUND_CALIBRATE
     is still on and the recording is an occupancy log — --forget it once settled.
  4. DIM_STEP=80 was a judgement, not a measurement. A sunset in the sample data can
     settle whether a slow fall actually feels better than a fast one.
CURRENT_PHASE: Feature-complete against both agreed lists (5 of 5, and 5 of 5). No scope
  baseline exists beyond those, so no honest percentage for "the theme" as a whole.
BRANCH: main
COMMIT: 88a4fa9
WRITTEN: 2026-09-06
```

## Standing traps

Recorded because each cost real time and none is discoverable from the code alone.

- **`unlock.png` is Plymouth's logo**, not a lock screen. Plymouth centres it at native
  size and hangs `entry.y = logo.y + logo.height + 40` off it, with no clamping. Measure
  the arithmetic before changing its size.
- **`omarchy theme install` does `rm -rf` on the theme directory.** All three installed
  themes should be local builds; the repos are for publishing. A clone is also staged
  differently — `.lua` and terminal configs are denied from one.
- **The registration spread is an aesthetic setting, not an error budget.** Tuned as a
  press tolerance the whole feature becomes invisible.
- **Hyprland under Omarchy 4 dispatches via `hl.dsp.*`.** The bare shell forms parse as
  Lua and fail with a syntax error, which reads exactly like "no effect".
- **`pkill -f` self-matches your own command line from anywhere in it**, not just the
  pattern. Kill by PID when the command line mentions the target for any other reason.
