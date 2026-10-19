# The Weave: archive, cel and AI in one registered shot

Open [`shots/weave.html`](../weave.html), or watch [`passage.mp4`](passage.mp4). It has sound and runs 13.8 s at 1920×1080, 24 fps and −15.6 LUFS.

## The problem this answers

WYGWYL has three bodies of material on one clock. Until now they did not touch.

- **Her voice** (observed) ran under everything as a soundtrack.
- **The archive** (observed: 4,788 read shots, 97 already matched to her lines in the cineosis cels cut) was cut in *instead of* the picture, or cel-filtered on its own.
- **The AI world** (invented: the 14 poem videos) was cel-filtered and treated as the finished picture.

SCION measured what that last choice costs:

- The filtered cel boils at 4.8–9.4× on still pixels.
- Volume drifts 10–59%.
- Contacts can't be pinned at all.

These are failures of the medium, not of tuning. A filter that re-segments every frame cannot hold a shape.

## The move

None of the three is the finished picture. Each is **material in one registered scene**, and the scene is **code**: `frame = render(clip.json, t)`.

| Material | Demoted / promoted to | In this passage |
| :-- | :-- | :-- |
| AI video | the **set**: depth planes, ground and surfaces with their own segmentation | the LED canopy street; its `ceiling` class is the screen, its `person` class is the crowd |
| Archive | an **object in the world** that is labelled as long as it shows | the 1956 console she touches; the film playing on the canopy; the inset answer |
| Cel | a **cut-out puppet** of rigid parts, solved by IK to sockets | the POET, cardboard, fingertip pinned to the 1956 knob |

Because the figure is rigid parts, the SCION gates that failed now pass by construction:

- **G2:** volume is constant.
- **G3:** contact error is measured, at 0.26% of height.
- **G5:** nothing boils except the drawn needle. It boils on purpose, on twos, on its own layer.

## Five joins (how archive, cel and AI meet)

1. **Screen.** The archive plays on a surface of the AI plate, behind the plate's own occluders.
2. **Wipe.** The archive is registered to the plate and wiped in as the past. It is labelled as a reconstruction. *(Not used here: nothing in poem 07 claims a past.)*
3. **Citizen.** An archive figure enters as a cut-out, with a provenance tag on its first entrance.
4. **Touch.** A puppet's socket is on an archive object, and what the hand does drives the archive. **This passage is a touch join:** the knob angle sets the canopy, the meter and the archive's sound.
5. **Answer.** After her line, the matched clip answers as a captioned inset.

## The passage

The line is "So DJ please turn me up." (661.0–674.8 s on her clock). The states and their times are in [`clips/p07_turn_me_up.json`](clips/p07_turn_me_up.json):

1. reading
2. looks up
3. anticipation (the shoulder leads)
4. reach (an arc)
5. grip (on "please")
6. turn (75° on "turn me up")
7. flood (the canopy carries the 1956 film; the 1956 hand on the same knob answers)
8. release
9. after (the knob stays turned and the canopy stays lit)

It was chosen after testing three candidates. *Sound And The Story* opens on a hand turning this kind of knob, and it was already matched to this line. The poem 04 Apollo pair was second; Gouda and the mirror hall was weakest. See `source_manifest.json` for all three.

## Files

| File | What |
| :-- | :-- |
| `build_assets.py` | cuts and registers the puppet parts and the archive console and knob; packs `assets/atlas.png`, checking every rect against its source |
| `build_set.py` | splits the AI plate into plate, canopy mask, LED texture and crowd cut-outs; extracts the archive at 24 fps; measures its loudness per frame |
| `build_clip.py` | evaluates every frame once: FK and two-bone IK, the level model, meter, canopy lag, crowd and camera; logs contact error and overlaps |
| `build_sound.py` | builds sound from the same event times: her voice, the archive gated by the canopy, detent clicks, taps and room tone |
| `render.mjs` | captures frames from the live page in frame ranges and muxes at −16 LUFS |
| `critic.py` | a scripted critic that checks the acceptance list and appends to `validation_log.md` |
| `epistemic_ledger.md` · `source_manifest.json` · `limitations.md` | what is observed, invented, retouched; what was used and not used; what falls short |

Rebuild:

```bash
python3 shots/weave/build_assets.py && python3 shots/weave/build_set.py && python3 shots/weave/build_clip.py
python3 shots/weave/build_sound.py && node shots/weave/render.mjs && python3 shots/weave/critic.py
```

`build_set.py` needs `shots/video/poem_07` locally (gitignored) and re-fetches nothing. The archive clip is in `archive/`; the other candidates are re-fetchable from the URLs in the manifest. Only the archive frames the passage uses are committed; `build_set.py` re-extracts them all.

## Widening to the other 13 poems

Each poem already has archive patches matched to its lines (`cineosis-lab/lab/cels/cels.json`). For each poem:

1. Pick the one line that changes what the next scene means.
2. Pick its matched clip.
3. Choose the **one join** the clip affords: an object to touch, a surface to play on, a figure to cut, or a past to wipe in.
4. Then build the same five files.

Prove each passage alone before cutting them together.
