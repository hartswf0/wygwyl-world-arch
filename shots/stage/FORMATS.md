# Stage formats (shared by the mechanisms, sequences, ensembles and engine work)

Units: the stage is 1600×900 px. Real sizes are in cm. Everything is cut-out cardboard: rigid cards on
brass brads, replacement cards, layers. "Some assembly required" is the look, not a bug.

## 1. Clip (display list) — `*.json`, played by the stage's action layer
Same as the Acting Arena clips (`shots/arena/clips/ACT-*.json`) and `shots/stage/anim/clips/`, extended:
```json
{
 "id": "mech.motorcycle.ride", "title": "...", "kind": "mech|action|sequence",
 "clock": {"fps": 24, "frames": 96}, "loop": true,
 "image_root": "../../../../",            // images are relative to the clip file unless image_root says otherwise
 "images": {"wheel": "kits/cut/10.props.motorcycle/front-wheel.webp"},
 "size_cm": {"w": 210, "h": 120}, "cm_px": 2.0, "floor_y": 400,   // clip px per cm and where the floor is
 "anchors": {"seat": [310, 180], "handlebar_L": [420, 150]},      // sockets other clips attach to (clip px, frame 0)
 "anchor_tracks": {"seat": [[310,180], ...]},                     // optional per-frame socket positions
 "events": [{"f": 12, "sfx": "sfx.engine.start", "label": "engine catches"}],
 "frames": [{"f": 0, "draw": [ ...ops... ]}]
}
```
Draw ops (existing): `img {id, m:[a,b,c,d,e,f]}`, `poly {pts, fill, stroke, w}`, `line {pts|x1..y2, stroke, w}`,
`shadow {x, y, rx, a}`, `bg`, `floor` (ignored on the stage).
Draw ops (new, the engine supports them):
- `img` may carry `a` (alpha 0–1) and `blend` (canvas composite name: screen, multiply, lighter…).
- `clip {pts}` … `unclip` — everything between is masked to the polygon (windows, TV screens, doors, portals).
- `plate {src, m, w, h, video?}` — an image or video drawn under the current transform (what a portal shows;
  `src` relative to shots/stage/, e.g. `../world/<id>/backdrop.webp` or `../film/poem_06.mp4`).
- `glow {x, y, r, color, a}` — a radial light (headlights, the heart's blue point, lamps, the call-cord).
- `text {x, y, s, color, txt}` — painted lettering only where a card would carry it (NEVERMORE, signs).

## 2. Ensemble — `shots/stage/ensembles/<id>.json`
A reusable set piece: an assembled group of layers with a real size and named slots for actors.
```json
{
 "id": "ens.phone_booth.quay", "name": "the lit phone booth on the quay", "poems": ["09"],
 "size_cm": {"w": 260, "h": 260}, "depth": "mid", "anchor": "floor-centre",
 "layers": [ {stage layer, with x_cm, y_cm relative to the anchor (y up from the floor), w_cm, h_cm?, band: back|mid|front} ],
 "slots": [{"name": "caller", "x_cm": 0, "y_cm": 0, "facing": "left", "pose": "stand|sit|kneel", "inside": true}],
 "mechs": [{"clip": "mech/clips/phone.handset_lift.json", "slot": "caller", "trigger": "pick up"}],
 "sfx": ["sfx.phone.ring"], "notes": "..."
}
```

## 3. Stage layer kinds (plans/NN.json scenes[].layers)
`part`, `plane`, `image`, `video`, `action` (existing) plus:
- `clip` — any clip file: `{kind:'clip', src:'mech/clips/x.json', x, y, w, loop?, f0?, f1?}`
- `ensemble` — `{kind:'ensemble', ensemble:'ens.phone_booth.quay', x, y, scale_px_per_cm, flip?}` drawn as its layers
- `sfx` — `{kind:'sfx', sfx:'sfx.rain', vol, loop?}` (no picture; plays on the timeline)
Cues (timeline) may target any of these: show / hide / play / move / pose-swap / sfx.

## 4. Sound effects — `shots/stage/sfx/index.json`
`[{id: 'sfx.engine.start', file: 'sfx/engine_start.mp3', dur, tags: ['motorcycle', 'engine'], source}]`,
small mono files, drawn from the project's own sound libraries (butterfly-halfworld wygwyl: atlantis-standard.json,
pack/, chops, audio) — never invented URLs.

## 5. Ownership (who edits what)
- mechanisms: `shots/stage/mech/**`
- sequences & character interaction: `shots/stage/anim/**`, `shots/stage/seq/**`
- ensembles & staging: `shots/stage/ensembles/**`, `plan_poems.py`, `plans/`, `sets/`, `scale.py`
- engine, playground, sfx: `shots/stage/index.html`, `shots/stage/play/**`, `shots/stage/sfx/**`, `build_assets.py`, `build_timeline.py`
- cut parts are read-only for everyone except the cut agent (`shots/kits/cut/**`).
