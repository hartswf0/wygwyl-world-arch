# The stage engine (engine.js), the sound library and the playground

`shots/stage/engine.js` is shared by the stage (`index.html`) and the playground (`play/index.html`). It holds the clip loader and drawer, anchors, events, ensembles, the sound player and the library reader. All data paths are relative to `shots/stage/`.

## Clips (FORMATS §1)

- **Image paths.** An image path that starts with `./` or `../` resolves against the clip file. Any other path resolves against the clip file plus `image_root`. Both conventions on disk work:
  - anim clips: `image_root: "shots/"` (a note) with `../../../../kits/...` paths;
  - mech clips: `image_root: "../../../"` with `kits/...` and `stage/mech/parts/...` paths.

  Older Arena actions pass `imgBase` (`../arena/`).
- **Draw ops.**
  - `img` takes `a`, `blend` and `shade` (far limbs are darkened).
  - `poly` and `line` take `a`.
  - `clip … unclip` masks are nestable. A mask that is never closed is closed at the end of the frame.
  - `plate` is an image or a video. A video plays with the clock, and `poster` is supported.
  - `glow` is a radial light drawn with `lighter` or its own `blend`.
  - `text` is painted lettering.
  - `shadow` is kept. `bg` and `floor` are ignored.
- **Box.** A clip's box is its `view` when it has one, else the bounds of its cards over the whole clip.
- **`E.frameBox(C, f)`** gives an actor's bounds in one frame. An actor walks across its clip box, so its feet are found frame by frame.
- **Anchors.** `anchor_tracks[name][f]` is used when present, else `anchors[name]`. `E.toStage` maps an anchor to stage pixels and handles flip and rotation.

## Stage (index.html)

- **Layer kinds.** New: `clip {src, x, y, w, loop?, f0?, f1?}`, `ensemble {ensemble, x, y, scale_px_per_cm, flip?}` (the anchor is the floor centre, and the ensemble's layers sit in back/mid/front bands) and `sfx {sfx, vol, loop?}`. Existing kinds are unchanged.
- **Frames.** A clip layer's frame comes from her audio clock. It runs from its play cue, or else from the scene start. A once-clip such as `car.door` plays once and holds.
- **Cues.**
  - show, hide, move and play work on the new kinds.
  - A new `sfx` cue (`{action: 'sfx', sfx: id}`, no layer needed) fires when its word is crossed.
  - The cue editor has an "sfx (sound)" type with a sound picker.
- **Sound on the clock.** Three sources, all from the same `t`:
  - sfx cues;
  - clip `events`, which fire when the clip's frame crosses the event's frame;
  - sfx layers, beds that sound while the layer shows and rejoin at the right offset after a seek.

  Nothing sounds on a scrub, and everything sounds through WebAudio from decoded buffers. Clip events show in the cue log as `sfx … ← mech.x`.
- **Attachments.**
  - Select a clip layer to see its anchors as yellow dots.
  - Drag a character onto a socket of another clip (it lights blue) and it attaches: `attach: {to: <layer ref>, anchor, dx, dy, mount?}`.
  - The rider takes the parent's px/cm, follows the anchor track every frame, and can be nudged with drag or the arrow keys.
  - On a seat/saddle anchor it hangs by its hips: 47% of its drawn height up from its feet, since anim clips have no hip socket.
  - The ⚓✕ button in the layer list detaches it.
- **Tray.** New tabs:
  - **Mechanisms** (`mech/index.json`, with thumbnails, anchors and sfx; ★ marks this poem's own);
  - **Characters** (`anim/index.json`, a line-up at true relative scale plus every act);
  - **Sequences** (`seq/`);
  - **Ensembles** (manifest);
  - **Sounds** (listen, add as a layer, cue).

  Clips drop in at the scene camera's px/cm with their feet on its `foot_y`.
- **Library.** `build_assets.py` now writes `assets.json.library`: which index files exist, the mech/seq clip files and an ensembles manifest (`ensembles/*.json` summarised). The stage reads only files listed there, so a missing folder costs no 404. Re-run it when those folders change.
- **Fixes made while checking the lead's reports.**
  - Scene edges are stored to 3 decimals, and `floor(t·24)` put `t0` on the previous frame. With `?s=3`, the stage therefore opened, and added layers to, the previous scene. The frame now takes a 0.01-frame tolerance, and `tlSceneAt` compares at half a frame.
  - **The giant boot over the moon (09.1, 17–21 s).** This was not a pose-swap. The plan's hidden solved action `ACT-001__man` has `y = foot - h/2`, `w = 0.6·h` for an INSERT shot (ppc 7.5). A walk's box spans the whole path, so the figure came out mis-sized and floating at the top. Plan action layers (in scenes not edited in the browser) now stand on the camera's `foot_y` at real height: the clip's cast cm_px times the scene ppc, with the frame-0 feet at the layer's x. In a shot too close to hold a whole figure, the figure is scaled until the head is in frame, and the layer is marked `cheat`.
  - **Pose-swap.** It only trades a whole-figure card for another of the same character: both cards come from `<character>.main-poses` sheets with the same character prefix. The feet stay on the same floor point and the scale is the sheet's. Body-part cards are never swapped, the editor refuses them, and the pose picker lists only main poses. All timeline pose-swap cues on disk pass this check.

## Sound library (sfx/)

`python3 shots/stage/sfx/build_sfx.py` writes `sfx/index.json` (a list per FORMATS §4) and 52 MP3s: 24 kHz mono, 48 kbps, about 1 MB in all.

**Recordings and her voice (37).**

| Source | Sounds |
| :-- | :-- |
| The wygwyl ATLANTIS pack (named in atlantis-standard.json, CLAP labels in labels.json) | rain (CLAP RAIN 0.98/0.99), wind, waves (nearest: CLAP ATMOS/OCEANIC), sea drone, vinyl crackle, chimes, portal open (riser) and hum, crowd and street (location audio from shoot clip AF5A3002; no crowd walla exists) |
| butterfly-halfworld `audio/foley` and `audio/sound` | footsteps (stone, soft, stairs), door (heavy) and glass door, wings, glass set and tap, water, drip, lights hum, projector, paper, breath, coat, shutter, night room |
| Her reading, from the chop kit | "a tambourine sounds", "DJ turn", "waves will calm", "winds will mute", "A familiar heart", "rotted by rain" |

**Unsourced: no recording on disk (15).** These are marked `kind: synth, unsourced: true`. They are made from deterministic recipes after `shots/weave/build_sound.py`:
- engine start / idle / rev
- phone ring / dial / pickup / hangup
- heartbeat
- clock tick
- tambourine jingle
- vinyl scratch
- glass shatter
- fire crackle
- card tap
- knob detent

**Resolving an id.** An id resolves by id, then by aliases, then by the longest id prefix, then by tags. So the mechanisms' ids find a sound: `sfx.car.engine_idle_loop` finds engine idle, and `sfx.heart.lub` finds heartbeat. An id with no word match (e.g. `sfx.glint.ping`) plays nothing.

## Playground (play/index.html), on hold

It was written before the hold and has not been verified yet. It has:
- a canvas world on the engine;
- places (ensembles, any poem's scene, world plates);
- every character and act, mechanisms, portals (a mask plus a plate);
- sound pads (Q…P);
- number keys to make each actor act;
- double-click to walk somewhere;
- drag onto an anchor or slot;
- Save and Load as JSON;
- "Append to that scene", which writes `wygwyl.stage.NN.KEY` and downloads the fragment.

## Verified (headless Chromium, `--autoplay-policy=no-user-gesture-required`, port 8784)

- All 14 poems load with no page errors, no console errors and no failed requests.
- Poem 10, 10.3: `motorcycle.ride` plays with poet_tracksuit (ACT-003) attached to `seat`. Its events fire on the audio clock (`ride_loop`, `glint.ping`).
- Poem 04, 04.2: `heart.beat`. `lub` and `dub` fire every beat.
- Poem 12, 12.3: `hourglass.yard`, 12 anchors, `fire.gutter` events.
- 09.1 at 18.8 s now shows the walking figure standing on the quay. Pose-swaps on 04, 09 and 13 are correct.
