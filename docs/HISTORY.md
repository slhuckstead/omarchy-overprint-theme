# Commit history before the 2026-09-05 squash

The repo ships ~63MB of wallpapers. Every rewrite of one stores another
full copy in git, and `omarchy theme install` does a FULL clone -- so a
single 16:10 -> 16:9 pass had taken the clone to ~172MB against 2-18MB for
stock Omarchy themes. History was squashed to one commit to cut that.

Nothing is lost: the original history is on the `archive/pre-squash`
branch, and every message is reproduced below.

---

## Theme the shell and the window border; make the export reproducible

_413df53 — 2026-09-05 21:15:54 -0400_

The published theme stopped at colors.toml, so Omarchy filled in the rest
generically: a flat single-colour window border, and a shell whose every
surface derived from the foreground at four opacities.

Window border. colors.toml now carries hyprland_active_border as three
stops -- an ink, what those two inks actually make where they overlap on
this ground, and the other ink. It is the only place in the theme where an
overprint is visible as itself. Raw inks cannot be used: measured against
the night ground, #0F4C81 is 2.16 contrast (invisible as a border) and
#FFE800 is 15.32 (glare), so every stop is retargeted to the accent's own
weight. The angle is 45deg rather than the 15deg primary screen angle,
because at border_size 2 a 15deg gradient collapses to flat colour on the
side edges -- at 6px it looks fine, which is the trap.

shell.toml. Shipping one suppresses Omarchy's generated file entirely, so
this carries every key the shell reads. Two departures from the stock file:
the gradient means exactly one thing, "this window is active", instead of
being inherited by every card down to tooltips; and interaction states climb
through ink rather than four opacities of one grey -- hover and cursor in
the primary ink, focus the same ink with a much harder edge, selection as
ink laid down and edged in the overprint colour.

selected-border-width is set explicitly for [launcher] and [menu]. Omarchy's
stock template omits it and the default is 0, so a selected-row border
colour renders nothing at all. Border.surfaceWidths() does read it per
surface. Only findable by sampling pixels across a row edge.

Resolution independence. engine.render() takes a scale factor, defaulting to
w / 2560, and applies it to the halftone pitch, the misregistration offset
and the canopy band together -- the three constants that were in pixels. A
larger render is now the same press on a bigger sheet rather than a
different-looking print. Verified radially in 2D (the plates are rotated
15/75/45, so a per-row spectrum measures projections and lies): the screen
is 8.00px at 2560 and 12.00px at 3840, ratio 1.500. generate.py --dist
--hires opts in; the shipped set stays 2560x1600.

generate.py --dist rebuilds this repo. The twelve wallpapers are recorded as
SHIP so the export reproduces the published set instead of inventing one.
Rebuilds are now no-ops in git: render() is deterministic but magick
-colors 256 is not -- it picks the same 256 colours and emits them in a
different PLTE order each run, changing bytes while every pixel stays
identical (AE 0, same byte count) -- so the export stages, compares pixels,
and adopts only files that actually changed. Previews are skip-if-present.
The PNG tIME chunk is stripped. --dist refuses to write into a git working
tree without --force, having once deleted this repo's wallpapers.

overprint-make-launcher-shadow now validates before it writes: it checks the
runner exists, counts the terminal branches it rewrote, and runs bash -n on
the result, failing without touching the shadow if any of that does not
hold. Previously it wrote the file first and only then warned, which left a
launcher that silently ran the stock screensaver.

A post-update hook re-derives that shadow after every omarchy update and
raises a critical notification if it cannot, because a stale shadow fails
silently. install.sh installs it; uninstall.sh removes it.

Co-Authored-By: Claude Opus 5 (1M context) <noreply@anthropic.com>

---

## Split generated wallpapers across the theme and user directories

_8aa1454 — 2026-09-05 21:28:56 -0400_

generate.py wrote all 132 into the theme directory, and the README said so.
Both were wrong for anyone who installs this from git: `omarchy theme
install` does `rm -rf` on the theme directory before cloning, and the repo's
derived theme name is `overprint`, so a reinstall or an update destroyed
every wallpaper the generator had made.

The twelve that ship stay in the theme directory; the other 120 now go to
~/.config/omarchy/backgrounds/overprint/, which survives a reinstall.
omarchy-theme-set enumerates both directories when cycling backgrounds, so
all 132 stay in the rotation -- verified, its own find returns 132.

--palette counts across both directories, and the preview/unlock hero is
looked up in both: it is harbour-night-4-modulor, which is not one of the
twelve (those carry harbour-slate-4-modulor), so after the split it lives in
the user directory.

Co-Authored-By: Claude Opus 5 (1M context) <noreply@anthropic.com>

---

## Fail a build when two palette slots collide, not just when contrast misses

_785c007 — 2026-09-05 21:35:03 -0400_

The generator has always failed a run when a colour could not reach its
contrast target. Nothing checked the other way a palette breaks: two slots
solving to the same colour. That is the worse failure. A contrast fallback
announces itself as pure black or white; a collision quietly makes two
meanings look identical, which is the one thing this palette claims not to
do.

generate.py --check [day|slate|night] compares every pair of the fourteen
meaning-carrying slots under normal vision and under simulated protanopia,
deuteranopia and tritanopia (Vienot, Brettel & Mollon 1999 -- project LMS
onto the plane a dichromat can still distinguish). Backgrounds are excluded
because they are deliberately close, and accent is excluded because it is
blue by construction. A collision now fails the build exactly as a contrast
fallback does.

The floors are REGRESSION floors, not perceptual thresholds. Each sits just
under what the shipped night palette measures -- normal 0.0624, deutan
0.0185, protan 0.0392 -- so the gate catches a change that makes separation
worse rather than asserting a bar nothing meets. Re-measure them if
CANON_LEVEL moves; they are properties of that ground, exactly like
SLOT_CONTRAST.

Tritanopia is reported and never gated. The shipped palette's own tritan
floor is 0.0029 (orange/bright_red), so a gate there would fail the thing it
exists to protect. It is also ~0.01% of people against deuteranopia's ~6% of
males, which is why the palette was tuned for the latter. Reporting it keeps
the limitation visible rather than absent.

Of the three grounds only night passes. slate has bright_yellow/bright_green
at 0.0154 under normal vision -- four times below the shipped palette's own
floor -- plus three protanopia collisions including bright_blue/
bright_magenta at 0.0023, which is one colour to a protanope. day has two
contrast fallbacks to pure black and two protanopia collisions. Three of
those six were invisible to a normal-vision check, which is the argument for
simulating CVD rather than eyeballing swatches.

--check with no level exits on the canon ground alone, so reporting the two
unshipped grounds does not read as the theme being broken.

Co-Authored-By: Claude Opus 5 (1M context) <noreply@anthropic.com>

---

## Add a light variant, with its own contrast targets

_d9b80a2 — 2026-09-05 22:08:46 -0400_

generate.py --light builds ~/.config/omarchy/themes/overprint-light: the same
three inks on paper rather than on a dark ground. A separate theme
directory, because that is how Omarchy does light and dark (Catppuccin /
Catppuccin Latte) rather than as a mode switch inside one theme.

The dark targets could not be reused, and not for reasons of taste. Contrast
is solved against `selection`, and the ceiling there is a property of the
ground: 15.59:1 on the night ground, 11.51:1 on paper. Paper reflects, so a
light theme has LESS headroom, not more. green at 10.0 plus BRIGHT_DELTA
asked for 12.1:1, above what any colour of any hue can reach there, so
retarget() gave up and shipped pure black with its ink cast gone.
LEVEL_FG["day"] was worse: 13.0 put bright_foreground at 14.6:1 against a
ground ceiling of 14.49, demanding a colour darker than black. It is 11.0
now, still past WCAG AAA. Darkening the paper does not help -- `selection`
darkens with it, so the ceiling falls (0.080 -> 11.51, 0.140 -> 9.28).

SLOT_CONTRAST_LIGHT is searched, not derived. Compressing the dark targets
proportionally cleared the ceiling but left three protanopia collisions:
under colour-vision deficiency hue separation is gone and lightness is the
only channel left, which means the contrast targets ARE the separation. A
search against the collision gate found a set with no fallbacks and no
collisions. It is tight and the comment says so -- green at 9.3 puts
bright_green at 11.4 against a ceiling of 11.51 -- and BRIGHT_DELTA cannot
absorb the difference, because every reduction buys ceiling headroom and
costs collisions (1.8 -> 1, 1.6 -> 2, 1.2 -> 5).

BORDER_MIX_TEMPER is per mode now. At the accent's own contrast the dark
screen-blend is #FF5388 at 100% of max chroma, a hot pink that dominates and
has to be pulled back; the light multiply is #2C445C at 48%, because inks
absorb on paper instead of glowing. Tempering that again only walks it
toward grey, so light keeps its mix as the press made it.

--light renders its own ground only. Night and slate wallpapers under a
light UI are incoherent, and they are byte-for-byte the images the dark
theme already made; rendering all three levels cost six minutes and 215MB of
duplicates before this was fixed.

Co-Authored-By: Claude Opus 5 (1M context) <noreply@anthropic.com>

---

## Key contrast targets to the ground, which fixes slate

_3aa82ae — 2026-09-05 22:23:49 -0400_

Slate failed with one contrast fallback and four collisions, including
bright_blue/bright_magenta at 0.0023 under protanopia -- one colour to a
protanope. It was the only ground of the three that did not pass.

The fix was a reframe rather than a tuning pass. A hue's contrast target is
not a matter of taste per mode; it is bounded by what the ground can
physically support, and that bound belongs to the ground. Measured against
`selection`:

  night  #0D0F15  ceiling 15.59:1  max base target 13.5
  slate  #212329  ceiling 11.47:1  max base target  9.4
  day    #DAD6CE  ceiling 11.51:1  max base target  9.4

Slate is a LIFTED DARK ground, so the gap to white is squeezed exactly as
paper squeezes the gap to black, and its ceiling lands within 0.04 of day's.
Feeding slate the light targets took it from four collisions to zero in one
step. Only green needed moving, 9.3 to 9.0, because bright_green at 11.4 sat
above slate's 11.47 for a hue that cannot reach it with any chroma left.

So SLOT_CONTRAST_BY_LEVEL is keyed by level rather than by mode, and build()
takes level=. Night is the odd one out, and it is the odd one out because it
is the only ground with real headroom -- not because it is dark.

All three grounds now pass --check with no fallbacks and no collisions,
which had never been true. The two shipped palettes are byte-identical after
the refactor: night and day resolve to exactly the sets they used before.

Two consequences worth having. Moving CANON_LEVEL no longer needs a
re-search, because the targets travel with the ground. And a new ground
should have its ceiling measured first -- that number gives the shape of the
answer before anything is tuned.

Co-Authored-By: Claude Opus 5 (1M context) <noreply@anthropic.com>

---

## Add the slate variant, and give both variants one code path

_7b5305f — 2026-09-05 22:29:41 -0400_

generate.py --slate builds ~/.config/omarchy/themes/overprint-slate on the
lifted dark ground (#212329). themes.py describes that ground as the one
that survives daylight, where the night ground washes out under glare and
paper glares back, so it fills a real gap between the other two rather than
sitting between them for the sake of it.

--light and --slate are now one code path. ship_for(level) derives each
variant's twelve from SHIP -- the same compositions on the same presses,
moved to that ground -- and variant(level) builds it, so the two flags
cannot drift apart and a third ground would be a line in VARIANT_SUFFIX.
Each still renders only its own ground: the others are byte-for-byte the
images another variant already made.

Slate's inks come out visibly paler than night's. That is the ground, not a
fault: on a lifted ground higher contrast means lighter, and its ceiling is
11.47 against night's 15.59.

The light palette is byte-identical after the refactor.

Co-Authored-By: Claude Opus 5 (1M context) <noreply@anthropic.com>

---

## Ship wallpapers at 16:9, and add --for-display for everyone else

_705c0c8 — 2026-09-05 22:51:59 -0400_

Omarchy hangs wallpaper with Image.PreserveAspectCrop
(shell/plugins/background/Background.qml), so a mismatch between image and
panel is taken off the edges. These were 2560x1600 -- this laptop's panel --
which meant every 16:9 user lost 10% of the height and an ultrawide 33%.

That matters more here than it would for a photographic theme. These
compositions are nested golden-ratio fields with one dominant, derived by
rule rather than placed by eye; a crop re-proportions the exact thing the
composition is.

There is no aspect that serves everyone, so this is a majority call:

  shipping 16:10   1920x1080 / 2560x1440 / 3840x2160  lose 10% of height
                   2560x1600                          exact
                   3440x1440                          loses 33%
  shipping 16:9    1920x1080 / 2560x1440 / 3840x2160  EXACT
                   2560x1600                          loses 10% of width
                   3440x1440                          loses 26%

16:9 is exact on the three commonest panels and better on ultrawide, at the
cost of 10% of width for the author -- the right way round for a theme other
people install.

generate.py --for-display reads the focused monitor from hyprctl and
re-renders this theme's wallpapers at its exact resolution, for anyone the
majority call does not fit. It is a re-render rather than a resize:
engine.render() scales the halftone pitch, misregistration and canopy band
with the frame, so it is the same press on a differently-shaped sheet.

The cost is size: 58MB against 32MB, where stock themes ship 2-18MB. A
halftone does not compress like a photograph, being high-frequency
everywhere. Judged worth it, because a soft or re-cropped print is the one
thing this theme cannot afford.

Co-Authored-By: Claude Opus 5 (1M context) <noreply@anthropic.com>

---

## Fix ten review findings, four of them major

_ecfc19f — 2026-09-05 23:26:20 -0400_

Found by code-review over the day's work; each verified before fixing.

1. The collision gate was unreachable. main() called _finish() and dropped
   its return, so every build path returned None and printed "done" whatever
   the verdict, and the --palette path returned on FALLBACKS alone while
   ignoring the collisions _finish had just computed. --check was the only
   working gate in the whole generator -- which made commit 785c007 largely
   ceremonial. Both call sites now return the verdict. Verified by sabotaging
   a target to force a collision: --dist now exits 1 where it exited 0.

2. dist() -- the path that produces what people actually install -- never
   called check_collisions at all. A palette that --check failed would export
   clean.

3. REPO_README and MIT were defined and never written; datetime was imported
   only for the copyright year and unused. A fresh export was an unlicensed,
   undocumented repo whose own unwritten README said "MIT. See LICENSE".
   Both are written now, and only when absent, so a curated README is never
   clobbered.

4. generator/ was copied only when the directory already existed, so a fresh
   export shipped no generator -- contradicting the comment above it and the
   README instructions that depend on it.

5. The aspect trap. DEST/SLUG is ~/.config/omarchy/themes/overprint, exactly
   where `omarchy theme install` clones this repo, and the local build still
   rendered 2560x1600 while the shipped set moved to 3840x2160. A user
   following README's own `python3 generator/generate.py` had twelve tracked
   16:9 wallpapers deleted and rewritten at 16:10 inside their checkout --
   the reverse of the decision one commit earlier. The local build now
   matches what ships; --for-display remains the escape hatch.

6. The hero fallback did sorted(os.listdir(bg))[0] and raised IndexError on
   an empty backgrounds/, reachable by running --palette before a full build.

7. for_display() read width/height without consulting transform, so a
   90/270-rotated monitor got a landscape render and a hard crop -- the exact
   failure the command exists to prevent.

8. -resize fits inside the box, so "2880x1800" produced 2880x1620 while the
   comment claimed it matched the first-party previews. It now fills.

9. A full run did os.remove over EVERY entry of the user backgrounds
   directory -- a user-owned path the README tells people to put their own
   wallpapers in -- and raised IsADirectoryError on any subdirectory. It now
   removes only filenames this generator makes and reports anything else.

10. overprint-make-launcher-shadow lost its mkdir -p, so mktemp died outside
    die() when ~/.local/bin did not exist.

Also corrected a README claim that only `night` passed, which contradicted
the same file and the actual --check output.

Co-Authored-By: Claude Opus 5 (1M context) <noreply@anthropic.com>

---

## --for-display only fixed a twelfth of a rotation

_d2edea3 — 2026-09-05 23:31:47 -0400_

It walked the theme directory alone -- the twelve that ship -- and left the
other 120 in ~/.config/omarchy/backgrounds/<theme>/ at whatever aspect the
last build gave them. Since Omarchy cycles both directories, running the
command advertised as "re-render to YOUR monitor exactly" fixed 12 of 132
wallpapers and silently left the bulk of the rotation wrong.

It now walks both, and skips anything it did not make rather than assuming
every PNG in a user-owned directory is its own: a filename that does not
parse as <press>-<level>-<composition>, or that names a press or ground this
generator has no recipe for, is reported and left alone. Verified with a
decoy file, which came through byte-identical.

Tested on the slate variant: 44 wallpapers re-rendered across both
directories, 1 left alone.

Co-Authored-By: Claude Opus 5 (1M context) <noreply@anthropic.com>

---

## Ship the picker card as a command, and let --dist export a variant

_a51928a — 2026-09-05 23:45:11 -0400_

Two of the three remaining gaps, closed as far as they can be closed from
here.

THE PICKER CARD. Every first-party Omarchy theme ships a screenshot of a
working desktop as its preview.png -- bar, tiled terminals, file manager,
borders, wallpaper behind. This ships a downscaled wallpaper, which in the
picker answers a different question: theirs show what your desktop will look
like, ours shows an abstract image. That is a gap in kind, not polish, and it
is the largest one left in this theme's presentation.

It cannot be closed by tooling. Taking the screenshot needs a clean
workspace, and switching workspaces has no effect from an agent context --
verified against both the legacy and the Omarchy 4 Lua dispatch forms -- so
any capture taken that way contains whatever the operator had open. An
assembled composite was tried and came out worse than the comp. So the
capture ships as overprint-make-preview, which applies the theme, waits while
a human arranges the workspace, and writes preview.png and preview-unlock.png
at 2880x1800 -- the size solitude and last-horizon use, and only reachable
with `-resize ...^ -extent`, since plain -resize fits inside the box and
silently yields 2880x1620.

PUBLISHING VARIANTS. dist() hardcoded the canon ground, so overprint-light
and overprint-slate could be built locally but never exported as installable
repos -- which was the actual reason they are unpublished, rather than any
decision. --dist now takes --light or --slate and emits a self-contained repo
for either: palette, shell surfaces, wallpapers on that ground, previews, the
generator, README and LICENSE. Verified by exporting the light variant to an
empty directory and checking it comes out mode = "light" with day wallpapers.
Each still needs its own repo, because omarchy theme install derives one
theme per repo name.

Also preserves docs/HISTORY.md, written ahead of a clone-size squash that has
not happened.

Co-Authored-By: Claude Opus 5 (1M context) <noreply@anthropic.com>

