# Proofs

Decision evidence for choices recorded in `../PROJECT-MEMORY.md`. These are
**not** regenerable — no tool in this repo writes to these paths. They were
composed by hand on 2026-09-06 to answer a specific question, and they are kept
because the lesson they produced is only half a lesson without them.

## `registration/` — how much variance a pull should have

Seven frames working toward the registration spread, ending at the sheet that
shipped.

| Frame | Shows |
|---|---|
| `1-drift-ladder.png` | the drift ladder across candidate values |
| `2-four-pulls-current-clamp.png` | four pulls under the clamp as it then stood |
| `3-before-tightening.png` | the same composition before tightening |
| `4-at-your-tolerance.png` | the spread at the tolerance originally asked for |
| `5-variance.png` | **the decisive one** — "Can you tell two pulls apart?", the same composition pulled twice at sigma 0.25 / 0.75 / 1.50 / 3.00 px, nominal misregistration held at 3px so only variance moves |
| `6-final.png` | the settled value |
| `7-repull.png` | a re-pull confirming it holds |

`5-variance.png` is the picture behind the lesson *"the registration spread is
an aesthetic setting, not an error budget."* Its own labels carry both framings —
0.25 px reads as "a quality press", 3.00 px as "drift as style" — and choosing
the second is what the lesson records. Tuned as a press tolerance, the feature
becomes invisible.

## `colophon/` — which colophon layout to use

Four candidates rendered against each other, plus the composites used to decide.

| Frame | Shows |
|---|---|
| `1-D-typographic.png` | D — no device, three ink rules, written colophon |
| `2-A-wordmark.png` | A — wordmark-led, misregistration in the letterforms |
| `3-B-stacked.png` | B — device above, wordmark below |
| `4-C-horizontal.png` | C — device beside, horizontal block |
| `ALL-FOUR.png` | all four side by side |
| `WITH-DEVICE.png` | the device variants together |

The `overprint-colophon` tool in `optional/bin/` is what renders a colophon; it
does not produce these comparison sheets.
