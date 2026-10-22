# Rig Builder labels: what is collected, and what it could train

**Status: nothing is trained yet.** The Rig Builder (`shots/rig/index.html`) collects human answers. `shots/rig/build.py` folds them back into the part data as overrides: medians for points, majority votes for categories. No model is fitted, and no model predicts anything. This file describes the data so that a model can be fitted later. It also says how the same data can check the current heuristics now.

## The loop

1. Someone opens the Builder, assembles a character, and fixes what the critic flags. They also answer quick tasks in the **Captchas** tab.
2. Every answer is saved in this browser right away (`localStorage['rigb.session']`) and applied on the page.
3. **Export labels** downloads `<session>.json`. Commit it as `shots/rig/labels/<session>.json`. Use one file per session and never edit old files.
4. `python3 shots/rig/build.py` reads every label file and applies the answers to `shots/rig/data/*.json`. From then on, everyone sees the fix.

The stage rigs (`shots/stage/anim/rigs.py`) do not read these labels yet. The Builder's data is their test bench, and wiring the labels into them is a separate step.

## Label file format

```json
{"session": "rig-202610221907-ju37", "who": "optional name", "started": "...", "exported": "...",
 "tool": "shots/rig/index.html", "counts": {"pivot": 12, "side": 5},
 "answers": [
  {"t": "pivot", "part": "<part id>", "point": "socket", "xy": [61.5, 304.1], "snapped": [62, 303] | null,
   "asked": {"cls": "upper_arm", "side": "R", "view": "front", "q": "A", "src": "hint", "guess": [62, 321.8]},
   "ms": 2140, "ts": "...", "char": "poet/red_black_sunglasses", "view": "front"}
 ]}
```

Every answer carries:

- `asked`: what the data said when the question was asked.
- `ms`: time to answer, which is a rough confidence signal.
- `char`/`view`: the character and view it was asked in.

Points are in the card's own pixel frame (`shots/kits/cut/<file>`, or `shots/bodylab/img/...`). Torso and hip points use viewer names `shVL/shVR/hipVL/hipVR`.

| `t` | Where it comes from | Value | What build.py does |
|---|---|---|---|
| `pivot` | Captcha: "click the SHOULDER / ELBOW / WRIST / KNEE / ANKLE / NECK brad" | `point`, `xy` (or `v: "none"` / `"unsure"`) | Median of all clicks becomes the point, with `src: "label"` |
| `edit-point` | Builder **Points** mode: a dot dragged onto a brad (snaps to detected rings) | `point`, `xy` | Same as `pivot` |
| `side` | Captcha: left or right? | `L`, `R`, `pair` (two parts in one card), `unsure` | Majority vote sets `side`; `pair` grades the part C |
| `costume` | Captcha: does it belong to this costume? | `yes`, `no`, `unsure` | A `no` majority sets `not_costume`, and the critic and default picker avoid the part |
| `cut` | Captcha: is this cut clean? | `yes` / `no` + `why[]` + `marks` (problem points) | A `no` majority grades the part C with the reasons; a `yes` majority lifts B to A |
| `shape` | Captcha: which hand shape? | `relaxed, open, fist, grip, point, flat_push, pinch, cup, wave, thumb, peace, claw` | Majority vote sets `shape` |
| `slot` | Captcha: drag this part into its slot | `upper_arm_L` … `shoe_R`, `torso`, `head`, `hip`, `not_body` | Majority vote sets class and side |
| `scale` | Builder: a scale fix (critic button, handle, ±) | multiplier on the sheet's px/cm | Median becomes `user_scale`, the part's default multiplier |
| `choice` | Builder: a part picked from a slot strip | `slot`, `part` | The latest pick becomes that slot's default for the character and view |
| `fix` | Builder: a critic fix button | the finding's title | Logged only, as a record of which problems people accept a fix for |
| `skip` | Captcha skipped | `kind`, `point` | Logged only, which marks ambiguous items |

Captchas ask first where the data is least sure:

- **Pivots:** where the point was guessed (`src: hint`, meaning no brad was detected there), where the card has 0 or more than 4 detected brads, and on parts that are in the current rig.
- **Sides:** where `side` is missing.
- **Cuts:** parts graded B.
- **Hand shapes:** hands with no shape.
- **Slots:** parts whose cutter label disagrees with their Body Lab class.

## What this could train or check (honestly: none of it is built)

- **Pivot / socket regressor.** Inputs are a card's alpha and RGB crop, plus its class. Targets are the clicked `xy` points.
  - It is small and data-efficient: there is 1 to 4 points per card, and brads are visually distinctive brass circles.
  - A first baseline needs no learning at all. Score the existing heuristics (`rigs.resolve`, the brad detector in `catalog.json`) against the median human click: pixel error, and the % within 2 cm at the card's px/cm. `asked.guess` and `asked.src` are stored with every answer for exactly this.
- **Brad detector precision and recall.** `snapped` says whether the human click landed on a detected ring. Clicks with no ring nearby are missed brads, and rings never clicked are false positives (knuckles, laces, ears). That is the evaluation set for the cutter's brad finder.
- **L/R classifier.** Inputs are a hand, foot or limb card. Targets are `L`/`R`/`pair`. Mirrored copies give free negatives (a flipped L is an R). Hands are the hard case, because the thumb and the palm/back view interact.
- **Hand-shape classifier.** This is 12 classes on hand cards. `cards.py` already knows the shapes for the poet's hand sheet, and that set can seed or check the human labels.
- **Cut-quality model.**
  - Targets are clean/unclean with reason tags and problem locations (`marks`).
  - It could replace or calibrate the registry's rule-based A/B/C grades (`shots/kits/cut/registry.json`: holes, pale fringe, clipped at panel edge…).
  - The marks are weak localization labels for a segmentation-style "where is the defect" head.
- **Slot / class classifier.** Inputs are the card and the cutter label. The target is the slot. It checks Body Lab's classification (`shots/bodylab/body.json`), which mislabels some cards, for example a `thigh.L` card classed as an upper arm.
- **Costume membership.** These are pairwise yes/no answers (part vs the costume's torso). They are training pairs for an embedding that clusters cards by outfit.
- **Scale constraints.** `scale` answers and the critic's anthropometric norms (hand ≈ 10.8% of height, foot 15%, head 13%, forearm 14.5%, upper arm 18.6%, thigh 24.5%, shin 24.6%) are constraints for a per-sheet px/cm solver. Body Lab's per-sheet scale could be re-solved as least squares over all segments plus human multipliers. That would replace the "character median" fallback.
- **Rig choices.** Which part people pick per slot is preference data for ranking candidates (the current ranker is the hand-written `score()` in index.html).

## Caveats

- **Too few answers.** One person and one session is not a dataset. Repeat questions across people, so that majority votes mean something and agreement can be measured. Click spread in px gives an inter-annotator error bar for pivots.
- **Single answers are applied as-is.** A single answer currently wins outright (a majority of one). Bad answers can be undone by deleting or reverting the label file, because answers are only ever appended.
- **The task picker is biased.** It favours uncertain items, so the labels are not a random sample. Do not use them to estimate overall error rates without reweighting.
- **Points depend on the image.** They are tied to the exact card image. If the cutter re-cuts a sheet and the card's pixel frame changes, its point labels must be dropped or re-projected. `build.py` does not detect this yet; a hash of the card image in each answer would.
