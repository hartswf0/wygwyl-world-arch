#!/usr/bin/env python3
"""Writes shots/suite/AUDIT_sets.md: what set material already existed for every scene, how good it is, and what lane C built.
Run after sets_build.py.   python3 sets_audit.py"""
import os, json, glob, collections
SUITE = os.path.dirname(os.path.dirname(os.path.abspath(__file__))); SH = os.path.dirname(SUITE)
MAN = json.load(open(os.path.join(SH, 'arena/parts/kit3/release_v2/wygwyl_atlas_manifest.json')))
MS = {s['scene_num']: s for s in MAN['scenes']}; MID = {s['id']: s['scene_num'] for s in MAN['scenes']}
PLAY = collections.defaultdict(list)
for f in sorted(glob.glob(os.path.join(SH, 'play/levels/*/level.json'))):
    L = json.load(open(f))
    for s in L['scenes']:
        PLAY[MID.get(s.get('plan_id'), '?')].append(s)
OUT = {os.path.basename(p)[:8] + os.path.basename(p)[-2:]: json.load(open(os.path.join(p, 'shot.json')))['camera'] for p in glob.glob(os.path.join(SH, 'out', '*')) if os.path.exists(os.path.join(p, 'shot.json'))}
SETS = {os.path.basename(f)[:-5]: json.load(open(f)) for f in sorted(glob.glob(os.path.join(SUITE, 'data/sets/[0-9]*.json')))}
DD = {}
for n in range(1, 15):
    for s in json.load(open(os.path.join(SH, f'design/data/{n:02d}.design.json')))['sets']: DD[(f'{n:02d}', s['id'])] = s

OVR = json.load(open(os.path.join(SUITE, 'tools/sets_overrides.json')))
rows = []
for sid, S in SETS.items():
    m = MS.get(sid, {}); wb = m.get('world_backdrop') or {}; k = wb.get('world_shot_k'); cam = OUT.get(k, {})
    h = cam.get('height_m'); conf = cam.get('physics_confidence')
    wq = 'none'
    if k:
        good_h = h is not None and 0.4 <= h <= 8
        wq = f"{k} ({wb.get('district_name', '')}), {len(wb.get('multiplane_sheets') or [])} sheets, cam h {h if h is not None else '?'} m, phys {conf}" + ('' if good_h else ' — height implausible for staging')
    pl = PLAY.get(sid, [])
    pq = '; '.join(f"{p['key']} {p['img']} floor {p.get('floor')} ppc {p.get('ppc')} ({p.get('shot') or 'tier?'})" for p in pl) or 'no play scene'
    d = DD.get((S['poem'], S['set']), {})
    dq = f"{d.get('status', '—')}; plate {os.path.basename(d.get('plate') or '') or '—'}; layers {'yes' if d.get('layers') else 'no'}; surfaces {len(d.get('surfaces') or [])}" if d else 'set not in dossier'
    src = S['plate_sources'][0]
    built = f"{src.get('cand', 'code')}" + (f" (CLIP {src.get('clip_vs_set')}, people {src.get('people_area', 0):.0%})" if src.get('cand') else '')
    rows.append((sid, S['set'], wq, pq, dq, built, S['status'], f"{S['scale']['confidence']} ({S['scale']['method']}) {S['scale']['px_per_cm_at_ground_line']:.2f} px/cm"))

st = collections.Counter(S['status'] for S in SETS.values()); cf = collections.Counter(S['scale']['confidence'] for S in SETS.values())
src_n = collections.Counter((S['plate_sources'][0].get('cand') or 'code').split('_')[0] for S in SETS.values())
slots = sum(len(S['archive_slots']) for S in SETS.values()); plates = len({S.get('plate') for S in SETS.values() if S.get('plate')})

TXT = f"""# AUDIT — sets (lane C)

What set material already existed for each of the {len(SETS)} scenes in `shots/poems/breakdown/NN.json`, how good it is for staging
cut-out puppets, and what lane C built from it (`shots/suite/data/sets/<scene_id>.json`, page `shots/suite/sets.html`).

## The existing material, system by system

| System | What it has | Per scene? | Scale | Verdict for staging puppets |
| :-- | :-- | :-- | :-- | :-- |
| `shots/out/<id>/` (analyze.py, multiplane.py) | 81 Atlantis (Midjourney) views, 1456x816: Depth Pro metric depth + focal, OneFormer ADE20K, G-DINO+SAM 2.1 objects, ground-plane RANSAC, horizon, camera height/pitch/roll; multiplane P0–P6 label map + sheets | no (per image) | measured camera height; 30/81 rescaled by known-size objects; median physics confidence 0.52; 3 heights < 0.3 m, 1 > 20 m | **the best measured material we have.** Reused as is (depth, ADE, ground) for every Atlantis plate lane C picked. |
| `shots/world.html` + `shots/world/<k>/` | the same 81 views as dioramas: 2–36 depth sheets each (mean 7.2), 768-px LOD webp, compressed depth z' | no | z in metres from the analysis | good for flying through; sheets are 768 px and their planes are role-first (P2 = 'hero', often a building) — not a puppet stage. |
| `shots/stage.html` + `release_v2/wygwyl_atlas_manifest.json` | all 80 scenes, each given one world backdrop (a view above) + camera_grammar (fov, pitch, camera height) + kit ensembles (P0–P5 cut parts with x, y, scale) | **yes** (80/80) | one global calibration (`character_rigs_library.json` stage_calibration: floor 0.86 H, standing adult 0.54 H) for every plate | the backdrop pick is often off-set (the basement gets a temple view; the house party a district street) and the scale ignores the plate's own perspective. Its ensembles of cut props are good and are lanes D/E's to place. |
| `shots/play/levels/NN/level.json` | per scene: plate s*.webp 1280x720 (+env, +ext tape), floor y, ppc, stations, world_planes | yes (by plan_id) | floor ≈ 612–620 everywhere; ppc is one of 7 tier defaults (0.48–7.58) chosen by shot size, not measured on the plate | plates are frames of the poem films and carry generated figures; scale is a default. |
| `shots/play/level_assets_catalog.json` | 1,766 cut parts with plane (P0–P6), z, default_scale, canon_h_m, anim_role | by poem | canon_h_m per part (real height) | good: the props' real heights are what a measured set needs (px_per_cm x canon_h_m x 100). |
| `shots/terrarium.html` + `data/terrarium/` | 10 real-place landpacks (public landmarks), 6 foundry worlds, 14 poems x scenes pointing at the play plates (90 'multiplane scenes') | yes (play plates) | terrain metres | world-building, not shot plates; scenes reuse the play plates. |
| `shots/design/data/NN.design.json` (dossiers) | 62 sets: design, layers far/mid/near/occluders (words), surfaces (words), plate choice, status ({dict(collections.Counter(d.get('status') for d in DD.values()))}) | per set | none | the right intent; plates chosen by eye; thumbnails 420 px only. Lane C uses its plate as a candidate (bonus in the ranking) and copies its layer/surface notes into each set. |
| `shots/weave/set/` | p07: one registered plate (ADE ceiling = canopy screen, crowd cut-outs painted out); p04 night garden | 2 passages | scale_from_plate 1.875 by hand | **the model**: a set is plate + masks + occluders + surfaces with joins. Lane C generalises it to every scene. |

## What lane C built

- {len(SETS)} set files; {plates} distinct plates (scenes on the same set share a plate folder `shots/suite/sets/plates/<plate>/`).
- Plate sources: {dict(src_n)} (gen = our generated footage, MARKOV_POET / BOY WN_LEAVE; world/view = Atlantis Midjourney views; code = black card).
- Status: {dict(st)}.
- Scale confidence: {dict(cf)}.
- Archive slots: {slots} (surfaces with ranked clips, plus one 'citizen' slot of segmented archive figures per plated scene).

How the plate is chosen (`tools/sets_candidates.py`, `tools/sets_analyze.py`): candidates are the dossier's plate and refs, the
dossier's CLIP finds (top 3 gen clips, top 3 views), and the stage manifest's backdrop; every gen clip gives 5 frames. Each frame
is screened with Grounding DINO for people; score = CLIP(set text) − 0.9·people area − 0.02·(any people) − 0.25·(tallest − 0.15) +
0.012 if it is the dossier's plate + 0.006 if already measured. Then an eye check of the contact sheet: overrides in `tools/sets_overrides.json`
({sum(1 for k, v in OVR.items() if not k.startswith('_') and v.get('cand'))} plate swaps, {sum(1 for k, v in OVR.items() if not k.startswith('_') and v.get('status'))} status notes), each with its reason.

How scale is solved (`tools/sets_build.py`): ground plane by RANSAC on Depth Pro points of the ADE ground → horizon, camera
height, pitch, roll. Metric scale comes from people/doors/cars/chairs/benches the plate already has (their SAM masks; street lamps
only when there are 3 or more). With no such object the horizon and falloff are still measured, but the camera height is not
trusted on our generated frames: on the one gen plate that has cars and people (gen_5ab27d990d) Depth Pro makes the cars
0.10–0.16 m and the people 0.12–0.30 m tall, 3–14x too small, and every other gen plate comes out with a 0.19–0.56 m camera.
So for gen plates without a reference (and Atlantis plates whose height falls outside 0.4–8 m) an eye-level camera of 1.50 m is
assumed and the set is graded 'low'. A 170 cm figure is its foot point on the plane plus 1.70 m along the normal, projected; the
ground line is the floor row (water excluded when there is other floor) where that figure comes out nearest the stage's hero
height (0.54 H). Every set has a `scale_check.jpg` with three such figures (only on rows that have floor) and the reference objects
drawn measured (green) vs predicted (white). Flags drop the grade when the horizon sits well above where the sky meets the land,
the plane rolls > 8°, little floor is visible, or the only floor is water; two picture-disagreement flags with no reference
reject the plane and the stage calibration is used instead ('assumed').

## Per scene

| scene | set | stage-manifest backdrop (world) | play level plate & scale | dossier set | lane C plate | status | scale |
| :-- | :-- | :-- | :-- | :-- | :-- | :-- | :-- |
""" + '\n'.join('| ' + ' | '.join(str(c).replace('|', '/') for c in r) + ' |' for r in rows) + """

## Known gaps

- Plates still needed (status 'needs a plate') are listed on the page with the reason; the dossier prompts for them are in
  `shots/design/data/NN.design.json` (`sets[].prompt`).
- Painted-out figures are cv2 inpaints: fine behind a puppet, visible as smudges when the area is large (`plate_sources[0].painted_out`).
- Depth Pro on rain-on-glass, macro and aerial plates gives planes that do not match the picture; those sets are flagged 'low'.
- Layers are 1280x720; they are cut by depth and ADE class, not by hand, so thin things (railings, branches) can split between planes.
- No private photography was read: every candidate path is checked against the brief's exclusion list before use.
"""
open(os.path.join(SUITE, 'AUDIT_sets.md'), 'w').write(TXT)
print('wrote AUDIT_sets.md', dict(st), dict(cf))
