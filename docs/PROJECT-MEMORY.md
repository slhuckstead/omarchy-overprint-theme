# Overprint — project memory

Handoff state for the theme and its tooling. The generator's source of truth is
`~/.local/share/overprint` (this repo carries a copy under `generator/`); the two
sibling repos, `omarchy-overprint-slate-theme` and `omarchy-overprint-light-theme`,
are publish targets of the same work and deliberately carry no handoff file of their
own. The operator's manual is `~/.local/share/overprint/README.md`.

## Session Status

```
STATUS: Three-variant Omarchy theme, feature-complete against both agreed lists. Adapts grounds on solar, dims to the room, re-pulls its own wallpaper weekly. All three repos clean and pushed.
FOCUS: Confirm the boot screen at the next reboot -- the one remaining unverified item.
FOCUS_SINCE: 2026-09-07
FOCUS_CARRIED: 0
LAST_SESSION: 2026-09-07 -- read the overnight ground calibration and settled the ground
  source by measurement. GROUND=solar is the permanent answer on this machine. See
  "Calibration result" below for WHY, which is NOT the reason the tool printed. Closed
  backlog 3 (calibration) and 4 (DIM_STEP, settled from the same data). Cleanup done and
  verified: GROUND_CALIBRATE=off, the occupancy log --forgotten, the temporary 5-minute
  timer override removed and the tick back to OnCalendar=*:00/10:00.
  Also fixed the refusal message in overprint-calibrate-ground, which blamed the camera
  whenever GROUND_BAND was the binding term. It now names the term, the closest split and
  the band value that would let it through, and keeps the sensor wording only for the case
  where cluster noise really is the blocker. Verified against three fixtures (band-bound,
  band-bound-then-lowered, genuinely noisy); the lowered-band fixture reproduces the
  28.6 / 35.3 thresholds predicted by hand from last night's numbers.
PREVIOUS_SESSION: 2026-09-06 -- twelve commits across the three repos. Closed the five-item
  agreed scope (screensaver across variants, variant installers, app-theme audit,
  wallpaper cycling, sensor+solar ground adaptation) and a five-item follow-on list
  (per-pull registration, weekly re-pull, plate proof, colophon, LOCATE=weather).
  VERIFIED BY MEASUREMENT, not assumption: camera gating proven with a marker script
  (solar + BRIGHTNESS=off opens the lens zero times); control loop noise cut from 9
  panel moves / 22.6% travel to 1 move / 3.1%; boot passphrase geometry recomputed
  from installed assets (entry y=934 on a 1600px screen). UNVERIFIED: the boot screen
  itself -- the machine has not rebooted since the Plymouth change.
  Biggest find was unplanned: unlock.png is Plymouth's LOGO, not a lock screen, and
  shipping a full-screen wallpaper there had been pushing the LUKS passphrase box off
  the bottom of the display. Fixed to an 800x188 wordmark.
  Two corrections from Seth, both now written into the source rather than just fixed:
  the capture guard was defeated by inserting a cursor fix between the check and the
  shutter; and the registration drift was set by asking a press-quality question when
  the drift is the style.
BACKLOG:
  1. Confirm the boot screen at the next reboot -- passphrase box visible, wordmark
     centred. Still unverified; ~48h uptime with no reboot since the Plymouth change.
  2. Upstream issue omacom/omarchy#10533 (dimText below AA on 19 of 22 first-party
     themes) awaits triage. If they fix it, DELETE ~/.config/omarchy/themed/pi.json.tpl
     or it shadows their template indefinitely.
  3. If the sensor ground is ever revisited it needs BOTH, and neither alone is enough:
     a run that covers 10:00-14:00 (the peak this one missed), and a GROUND_BAND derived
     from measured noise rather than the shipped 6. Nothing is blocked on it -- solar
     covers slate and night; only the day/paper ground stays manual.
CURRENT_PHASE: Feature-complete against both agreed lists (5 of 5, and 5 of 5), with the
  ground source now settled by measurement rather than left open. One item unverified
  (the boot screen), which needs a reboot rather than work.
BRANCH: main
COMMIT: f0b3e28
WRITTEN: 2026-09-07
```

## Calibration result -- the sensor cannot drive the ground here (2026-09-07)

19.2 hours, 242 samples, unbroken 5-minute cadence, Sun 14:33 to Mon 09:50.
`overprint-calibrate-ground` rejected both a three-way and a two-way split and printed
"the camera is not seeing the change." **That sentence was wrong.** The decision it
reached was right; the reason it gave was not. The tool has since been fixed to report
which of the two requirements actually bound, so it no longer blames the camera for a
number in a config file -- but any refusal recorded before 2026-09-07 carries the old
wording and should be re-read with that in mind.

The camera sees the day clearly: flat 24.2 from midnight to 06:00, up to 44.0 by 09:15,
around 30 through the afternoon, an evening lamp bump to 35.5, back to 24.6 by 20:00.

Noise was not the blocker either. Pooled SD was 1.5, so the noise floor asks 4.5 points
of separation -- and the cluster gaps were 7.7 and 5.6, which both beat it. The blocker
was `2 x GROUND_BAND = 12.0`, and `GROUND_BAND=6` is a shipped default nobody measured:
four times the noise actually present, and the third of three anti-flap brakes (the
ground is fed the smoothed median at `overprint-adapt:561`, then AGREE=2, then DWELL=900).
At `GROUND_BAND=2.8` or below the three-way split passes.

Solar is still the right answer, for reasons the arithmetic does not reach:

- **The run missed the brightest hours.** The top eight readings are all Mon 09:00-09:35
  and the curve was still climbing when it stopped; 10:00-14:00 was never sampled. The
  bright cluster's centre of 38.1 is an underestimate off a truncated curve, so those
  gaps are the wrong gaps to tune against.
- **The night end is the camera's black floor, not the room.** 72 samples from 00:00 to
  06:00 span 24.0 to 24.2 -- two tenths of a point over six hours, a locked-exposure
  sensor bottoming out. Usable range is ~20 points of 255, and a three-way split would
  live entirely inside it: void if the machine moves, a monitor arrives, a blind closes,
  or December comes. It was also one day, in September.
- **Solar needs no camera, no per-machine number and no recalibration.** Its one cost is
  that `GROUND_SOLAR_DAY=slate` and `GROUND_SOLAR_NIGHT=night`, so the day/paper ground
  is only ever reached by hand.

Cluster figures worth keeping, since the raw timeline was deleted as an occupancy log:
range 23.2-44.0; k=3 centres 24.7 / 32.4 / 38.1 with gaps 7.7 and 5.6; k=2 centres
24.9 / 34.2 with gap 9.3; pooled SD 1.5 (k=3) and 2.1 (k=2).

### DIM_STEP settled from the same data

Backlog item 4 wanted a real transition to judge `DIM_STEP=80` against 100. The run had
one: a sharp 8.5-point fall at 20:33 (33.1 -> 24.6 -- a lamp going off, not the sunset).
Simulated against the real readings through the actual control loop:

    DIM_STEP=80     the fall: 1 move, 4.8% travel     whole run: 9 moves, 26.8%
    DIM_STEP=100    the fall: 1 move, 5.5% travel     whole run: 8 moves, 26.3%

The config comment claimed "80 settles in 3 ticks, 100 in 2." Not in this room: **both
settle in one move**, because after the 80% step the 1.2% residual is inside a 2.0%
deadband and a second step never fires. At this dynamic range the setting is inert --
0.7% of panel on the sharpest real transition in the data. Left at 80; there is no
measured cost to the gentler fall. Revisit only if the room's range widens.

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

- **`GROUND_BAND` gates calibration, not just runtime.** `overprint-calibrate-ground`
  demands `max(2 x GROUND_BAND, 3 x pooled SD)` of separation between clusters, so a
  shipped hysteresis default silently decides whether a whole day of sampling can ever
  succeed -- and when it fails it blames the camera. Check which of the two terms is
  binding before believing the verdict.
