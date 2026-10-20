# The Weave: archive, cel and AI in one registered shot

Open [`shots/weave.html`](../weave.html) and pick a passage tab (`?p=p04_hands` or `?p=p07_turn_me_up`), or watch the films:

- [`p04_hands/passage.mp4`](p04_hands/passage.mp4): poem 04, "I put them back on". 28.6 s, sound, 1920×1080, 24 fps, −16.5 LUFS. Joins: **wipe**, **citizen**, **touch**.
- [`passage.mp4`](passage.mp4): poem 07, "So DJ please turn me up". 13.8 s, −15.6 LUFS. Joins: **touch**, **screen**, **answer**.

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

1. **Screen.** The archive plays on a surface of the AI plate, behind the plate's own occluders. *(p07: the canopy.)*
2. **Wipe.** The archive is registered to the plate and wiped in, labelled as a reconstruction for as long as it shows. *(p04: the 1969 sky, assembled from the clip's own frames, wipes down into the plate's sky mask on "clouds meet stars" and goes back up on "mine".)*
3. **Citizen.** An archive figure enters as a cut-out, tagged for every frame it is visible. *(p04: the man at the ship's rail rises on a stick behind the plate's ledge; his film runs inside one fixed scissor cut from "find".)*
4. **Touch.** A puppet's socket is on something, and every hand-off is a logged contact. *(p07: the knob angle drives the canopy, meter and archive sound. p04: her wrist stubs find her own loose hands; one hand carries the other to the far wrist.)*
5. **Answer.** After her line, the matched clip answers as a captioned inset. *(p07.)*

## Passage 04: "I put them back on"

Poem 04, 364.0–392.6 s on her clock, 686 frames. The states, contacts and measurements are in [`clips/p04_hands.json`](clips/p04_hands.json); the build is in [`p04_hands/`](p04_hands/).

1. She stands in the night garden. Her arms end at the wrist tabs; her two hands lie on the ground ahead.
2. "Clouds meet stars": the 1969 sky wipes down into the plate's sky, tagged; the garden darkens.
3. She kneels: near toe pinned, far foot steps once, both knees land; dust.
4. **The failure.** "Search the ground": she pats the bare ground twice with her wrist stub, a stub-width short of the hands. Nothing there. The dust stays on the stub.
5. "Two hands": a warm light finds them.
6. The man at the rail rises on a stick behind the ledge, tagged; from "find" his film runs and he turns and laughs.
7. "They too used to be mine": she lifts both stubs and looks at them; the 1969 sky goes back up.
8. "I put": the near wrist presses onto hand A and the brad goes in.
9. "On": hand A pinches hand B.
10. The carry, with a held stop on "care".
11. "Stake": B goes onto the far wrist; A lets go.
12. "Nevermore": both hands go down to rest on her thighs. Both stay dusty.

Measured (from the frames the page draws; `node shots/weave/selftest.mjs`): grip 2.2 px (0.26% of her height), press 0 px, pat 2.1 px, fit gap 2.2 px, near toe 0 px, far toe planted outside its one step, far knee gap 7.9 px (0.95%), IK reach ≤ 0.998, both archive tags wholly on screen in all 933 tag-frames. See [`p04_hands/limitations.md`](p04_hands/limitations.md) for what this does not show.

## Passage 07: "So DJ please turn me up"

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

## Layout

One renderer, any number of passages. Each passage is a config (its own `build_*.py`) plus one clip.

| File | What |
| :-- | :-- |
| `../weave.html` | the generic renderer: reads `passages.json`, draws a clip's display list under each frame's camera; `?p=<id>`, `&debug=1` (contact marks), `&f=N`, `&capture=1`, `&selftest=1` |
| `passages.json` | the index: id, tab, clip, mp4, joins, dir for each passage |
| `weave_lib.py` | shared: easing and keys, word times, the `Rig` (sockets, bone angles), two-bone IK, op builders (`op_img`, `op_label`, `label_fit`), the camera mirror `cam_t`, overlap rasters, paper cut, atlas packing, sound helpers |
| `clips/<id>.json` | per frame: `draw` (a list of ops: `img` `warp` `tint` `rect` `glow` `dots` `line` `label` `proc` `inset`, each on a parallax plane `k`), `cam`, `g` (graph values), `dbg` (contact marks); per clip: images, masks, sequences, audio, states, contacts, ledger, joins, `measured` |
| `render.mjs <id>` | captures every frame from the live page into `<dir>/frames` and muxes with `<dir>/passage.wav` at −16 LUFS |
| `sheet.mjs <id> out.jpg f...` | a contact sheet of chosen frames, drawn by the same page (`DEBUG=1` for contact marks) |
| `selftest.mjs [id...]` | runs `?selftest=1` headless for each passage: frame count, every image loaded, determinism, the clip's measured pass flags |

The display-list rules: `rect` always fills the screen; an `img` with a `mask` draws the mask with the image's own transform; `wipe {y, seed, jag, clip}` keeps the image above a torn edge, inside a full-plane clip mask; `dust` speckles inside the part's alpha.

## Files (passage 07, in this folder)

| File | What |
| :-- | :-- |
| `build_assets.py` | cuts and registers the puppet parts and the archive console and knob; packs `assets/atlas.png`, checking every rect against its source |
| `build_set.py` | splits the AI plate into plate, canopy mask, LED texture and crowd cut-outs; extracts the archive at 24 fps; measures its loudness per frame |
| `build_clip.py` | evaluates every frame once: FK and two-bone IK, the level model, meter, canopy lag, crowd and camera; logs contact error and overlaps; compiles the display list |
| `build_sound.py` | builds sound from the same event times: her voice, the archive gated by the canopy, detent clicks, taps and room tone |
| `critic.py` | a scripted critic that checks the acceptance list and appends to `validation_log.md` |
| `epistemic_ledger.md` · `source_manifest.json` · `limitations.md` | what is observed, invented, retouched; what was used and not used; what falls short |

Passage 04 has the same set in [`p04_hands/`](p04_hands/) (`build_assets.py`, `build_clip.py`, `build_sound.py`, `critic.py`, ledger, manifest, limitations, validation log).

Rebuild:

```bash
# poem 07
python3 shots/weave/build_assets.py && python3 shots/weave/build_set.py && python3 shots/weave/build_clip.py
python3 shots/weave/build_sound.py && node shots/weave/render.mjs p07_turn_me_up && python3 shots/weave/critic.py
# poem 04
python3 shots/weave/p04_hands/build_assets.py && python3 shots/weave/p04_hands/build_clip.py && python3 shots/weave/p04_hands/build_sound.py
node shots/weave/render.mjs p04_hands && python3 shots/weave/p04_hands/critic.py
# both
node shots/weave/selftest.mjs
```

The server is `python3 -m http.server 8800` at the repo root. `build_set.py` needs `shots/video/poem_07` and `p04_hands/build_assets.py` needs `shots/video/poem_04` locally (gitignored); neither re-fetches anything. Only the archive frames a passage uses are committed.

## Widening to the other 13 poems

Each poem already has archive patches matched to its lines (`cineosis-lab/lab/cels/cels.json`). For each poem:

1. Pick the one line that changes what the next scene means.
2. Pick its matched clip.
3. Choose the **one join** the clip affords: an object to touch, a surface to play on, a figure to cut, or a past to wipe in.
4. Then build the same five files.

Prove each passage alone before cutting them together.
