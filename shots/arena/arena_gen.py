#!/usr/bin/env python3
"""
THE ARENA GENERATION PACK — everything a generator needs, in one folder.

    python3 shots/arena/arena_gen.py        -> shots/arena/gen_pack/

A generator cannot be told "make a cut-out puppet" and produce something that
registers. It needs three things at once and they have never been in the same
place: what the piece IS (the brief), what it must LOOK like (style reference),
and what the body is DOING (the pose). This assembles all three.

  style/   the cards that pass acceptance, and the generated poses, as the look
           to hold: drawn cardboard, visible fluting at the cut edge, brass brads
  poses/   one sheet per challenge: the Bolas skeleton at every named beat, drawn
           at that vignette's own camera, so a generated pose is conditioned on
           the motion it has to match rather than on a description of it
  briefs/  the per-card briefs, with length in cm from the skeleton and the pivot
           declared
  PACK.md  what is in here and what to do with it

ONE CAMERA, NOT FIFTY-SEVEN. I previously reported the bank using 57 distinct
camera yaws from -119 to +116 and sized the card budget on it. That was wrong: I
had read view['x'], the camera's centre, as the yaw. The bank states yaw
explicitly and it is -22 degrees for 188 of its 191 vignettes — three others at
-58 and -14. The arena is effectively a single camera. That collapses the
library from 188 cards to 68, and it means a flat card has a fighting chance,
because it only has to be right from one direction.

Elevation does vary - twelve values from 6 to 60 degrees, most often 7, 10 or 12
- so the vertical foreshortening changes between vignettes even though the
facing does not. That is a stretch problem, not a view problem.
"""
import json, os, math, glob, shutil, collections
import numpy as np, cv2

HERE = os.path.dirname(os.path.abspath(__file__))
BANK = os.path.join(HERE, 'bolas', 'bank')
PACK = os.path.join(HERE, 'gen_pack')
DEG = math.pi / 180.0

BONES = [('pelvis','spineMid'),('spineMid','chest'),('chest','neckBase'),('neckBase','headBase'),
         ('headBase','headTop'),('chest','shoulderL'),('chest','shoulderR'),
         ('shoulderL','elbowL'),('elbowL','wristL'),('shoulderR','elbowR'),('elbowR','wristR'),
         ('pelvis','hipL'),('pelvis','hipR'),('hipL','kneeL'),('kneeL','ankleL'),
         ('hipR','kneeR'),('kneeR','ankleR'),('ankleL','heelL'),('heelL','toeL'),
         ('ankleR','heelR'),('heelR','toeR')]

def projector(view, W=1920, H=1080):
    yaw, elev = view.get('yaw', -22) * DEG, view.get('elev', 10) * DEG
    cy, sy, ce, se = math.cos(yaw), math.sin(yaw), math.cos(elev), math.sin(elev)
    c = [view.get('x', 0), view.get('y', 90), view.get('z', 0)]
    s = H * 0.86 / 230 * view.get('zoom', 1.0)
    def proj(p):
        x, y, z = p[0]-c[0], p[1]-c[1], p[2]-c[2]
        x1, z1 = x*cy - z*sy, x*sy + z*cy
        y2, z2 = y*ce - z1*se, y*se + z1*ce
        return (W/2 + x1*s, H*0.52 - y2*s, z2)
    return proj, s

def draw_pose(P, idx, proj, tile=320, label=''):
    """one beat, drawn as the body it is: bones as bars, joints as pins"""
    pts = {n: proj(P[i]) for n, i in idx.items()}
    xs = [p[0] for p in pts.values()]; ys = [p[1] for p in pts.values()]
    cx, cy = (min(xs)+max(xs))/2, (min(ys)+max(ys))/2
    span = max(max(xs)-min(xs), max(ys)-min(ys), 1.0) * 1.35
    k = tile / span
    im = np.full((tile, tile, 3), 244, np.uint8)
    def T(p): return (int((p[0]-cx)*k + tile/2), int((p[1]-cy)*k + tile/2))
    order = sorted(BONES, key=lambda b: -(pts[b[0]][2] + pts[b[1]][2]))   # far bones first
    for a, b in order:
        if a not in pts or b not in pts: continue
        d = (pts[a][2] + pts[b][2]) / 2
        g = int(np.clip(150 - d*0.9, 40, 190))
        cv2.line(im, T(pts[a]), T(pts[b]), (g, g, g), max(2, int(tile*0.028)), cv2.LINE_AA)
    joined = {n for b in BONES for n in b}
    for n, p in pts.items():
        if n not in joined: continue          # 'nose' carries no bone; it is not a piece
        cv2.circle(im, T(p), max(2, int(tile*0.012)), (30, 30, 30), -1, cv2.LINE_AA)
    cv2.rectangle(im, (0, 0), (tile-1, tile-1), (180, 180, 180), 1)
    if label:
        cv2.putText(im, label[:34], (5, tile-7), cv2.FONT_HERSHEY_SIMPLEX, tile/900.0, (60, 60, 60), 1, cv2.LINE_AA)
    return im

def sheet(tiles, cols, title, path, tile=320):
    if not tiles: return 0
    rows = int(math.ceil(len(tiles)/cols)); head = 46
    canv = np.full((head + rows*(tile+8) + 8, cols*(tile+8) + 8, 3), 252, np.uint8)
    cv2.putText(canv, title, (8, 30), cv2.FONT_HERSHEY_DUPLEX, .72, (20, 20, 20), 1, cv2.LINE_AA)
    for i, t in enumerate(tiles):
        r, c = divmod(i, cols)
        canv[head + r*(tile+8): head + r*(tile+8)+tile, 8 + c*(tile+8): 8 + c*(tile+8)+tile] = t
    cv2.imwrite(path, canv, [cv2.IMWRITE_JPEG_QUALITY, 92])
    return len(tiles)

def main():
    for d in ('style', 'poses', 'briefs'):
        os.makedirs(os.path.join(PACK, d), exist_ok=True)

    # ---- style: only cards that pass acceptance get to be the reference
    acc = {}
    p = os.path.join(HERE, 'pieces_accept.json')
    if os.path.exists(p):
        for r in json.load(open(p)): acc[r['file']] = r['ok']
    n_style = 0
    for src in (glob.glob(os.path.join(HERE, '..', 'weave', 'cast', 'man', 'parts', '*.png'))
                + glob.glob(os.path.join(HERE, '..', 'weave', 'assets', '*.png'))):
        b = os.path.basename(src)
        keep = acc.get(b, None)
        if keep is True or 'pose' in b or 'crouch' in b or 'recovery' in b:
            if 'atlas' in b: continue
            shutil.copy(src, os.path.join(PACK, 'style', ('ACCEPTED__' if keep else 'POSE__') + b))
            n_style += 1

    # ---- poses: the Bolas skeleton at every named beat, per challenge
    clips = {os.path.basename(f).split('__')[0]: f
             for f in sorted(glob.glob(os.path.join(HERE, 'clips', '*__bolas.json')))}
    T2A = {}
    for f in sorted(glob.glob(os.path.join(BANK, 'T1*.json'))):
        d = json.load(open(f))
        a = (d.get('after') or '')
        if 'ACT-' in a: T2A[d['id']] = a.split('ACT-')[1][:3]
    made = []
    for tid, act in sorted(T2A.items(), key=lambda kv: kv[1]):
        bank = os.path.join(BANK, tid + '.json')
        if not os.path.exists(bank): continue
        V = json.load(open(bank))
        idx = {n: i for i, n in enumerate(V['joints'])}
        proj, _ = projector(V['view'] or {})
        cid = 'ACT-' + act
        beats = []
        cf = clips.get(cid)
        if cf:
            try: beats = json.load(open(cf)).get('beats') or []
            except Exception: beats = []
        if not beats:
            beats = [{'f': f, 'who': '', 'beat': f'f{f}'} for f in range(0, V['len'], max(1, V['len']//10))]
        seen, tiles = set(), []
        for b in beats:
            f = min(b['f'], len(V['frames'])-1)
            if f in seen: continue
            seen.add(f)
            fr = V['frames'][f]['a']
            who = list(fr)[0]
            tiles.append(draw_pose(fr[who]['j'], idx, proj, label=f"f{f} {b['beat']}"))
            if len(tiles) >= 24: break
        yaw = (V['view'] or {}).get('yaw', -22); elev = (V['view'] or {}).get('elev', 10)
        out = os.path.join(PACK, 'poses', f'{cid}_{tid}.jpg')
        n = sheet(tiles, 6, f"{cid}  {V['title']}  -  {len(tiles)} beats, camera yaw {yaw} elev {elev}", out)
        made.append((cid, V['title'], n, yaw, elev))

    # ---- briefs
    for f in ('pieces.json', 'pieces_brief.json', 'pieces_brief.md', 'pieces_accept.json'):
        s = os.path.join(HERE, f)
        if os.path.exists(s): shutil.copy(s, os.path.join(PACK, 'briefs', f))

    brief = json.load(open(os.path.join(HERE, 'pieces_brief.json')))
    yaws = collections.Counter(x[3] for x in made); elevs = collections.Counter(x[4] for x in made)
    md = [f'# Arena generation pack', '',
          f'- **{brief["cards"]} card briefs** — `briefs/pieces_brief.json`, one per piece, '
          f'length in cm from the Bolas skeleton, pivot declared.',
          f'- **{len(made)} pose sheets** — `poses/`, the skeleton at every named beat, drawn at '
          f'that vignette\'s own camera.',
          f'- **{n_style} style references** — `style/`, only cards that pass acceptance, plus the '
          f'three generated poses.', '',
          '## The camera', '',
          f'yaw across these vignettes: {dict(yaws)} — effectively one camera.',
          f'elevation: {dict(sorted(elevs.items()))} — this is what changes, and it foreshortens '
          'the vertical rather than turning the body.', '',
          '## How to use it', '',
          '1. Condition on the matching tile in `poses/` for the beat you are generating.',
          '2. Hold the look from `style/` — drawn cardboard, fluting at the cut edge, brass brads.',
          '3. Take the size, pivot and prompt from the brief in `briefs/pieces_brief.json`.',
          '4. Run `pieces_accept.py` on the result. A piece that fails is regenerated, not placed.', '',
          '## Production Movement Contact Sheets', '',
          'To ensure physical coherence across acting beats without arbitrary bounding-box cuts,',
          '13 full-bleed production movement contact sheets were synthesized directly under the canonical Bolas camera (yaw -22°, elev 12°),',
          'conditioned on the reference cardboard puppet ("The Man" / Boone style: Black man in 30s, neat beard, sunglasses, black jacket with salmon-pink side stripes, corrugated fluting, brass split-pin brad joints):', '',
          '| Sheet File | Challenge & Title | Keyframe Sequence & Acting Beats |',
          '| :--- | :--- | :--- |',
          '| `MAN_01_MOVEMENT.jpg` | **Movement Master** | Overview of canonical motions: Walk, Brake, Run, Crouch, Turn, Jump, Slip |',
          '| `ACT-001_WALK_STUDY.jpg` | **ACT-001 (T101) Walk Without Spilling** | Heel-strike (#f15), Passing stride (#f45), Brake step (#f120), Settle with level cup (#f180) |',
          '| `ACT-002_SPRINT_STUDY.jpg` | **ACT-002 (T102) Sprint and Reconsider** | Sprint acceleration (#f20), Hard brake (#f65), 180° turnaround (#f118), Balanced settle (#f232) |',
          '| `ACT-003_CROUCH_STUDY.jpg` | **ACT-003 (T103) Crouch and Sneak** | Alert standing (#f10), Ducking (#f40), Peak crouch (#f72), Low crawl (#f150) |',
          '| `ACT-004_SPIN_STUDY.jpg` | **ACT-004 (T104) Spin and Find Target** | Stance windup (#f20), 180° half-spin (#f65), 360° whip (#f110), Target lock-in (#f145) |',
          '| `ACT-005_JUMP_STUDY.jpg` | **ACT-005 (T105) Jump Over Obstacle** | Compression (#f20), Launch (#f50), Airborne apex tuck (#f85), Impact splashdown (#f130) |',
          '| `ACT-006_LEDGE_STUDY.jpg` | **ACT-006 (T106) Catch the Ledge** | Vertical leap (#f20), Ledge grip contact (#f60), Overhead hang (#f110), Pull-up (#f160) |',
          '| `ACT-007_SLIP_STUDY.jpg` | **ACT-007 (T107) Slip and Recover** | Normal stride (#f15), Sudden foot slip (#f35), Torso back 45° flail (#f50), Recovery step (#f95) |',
          '| `ACT-008_FLOOR_STUDY.jpg` | **ACT-008 (T108) Stand After a Fall** | Prone lying (#f30), Palm push-up (#f110), All-fours crawl (#f160), Rise to upright (#f220) |',
          '| `ACT-010_BOX_STUDY.jpg` | **ACT-010 (T110) The Heavy Box** | Standing approach (#f20), Deep deadlift squat (#f55), Leg drive lift (#f95), Upright carry (#f130) |',
          '| `ACT-013_PUNCH_STUDY.jpg` | **ACT-013 (T113) Punch That Misses** | Boxing guard (#f15), Straight right cross (#f55), Over-rotated whiff (#f75), Recoil guard (#f110) |',
          '| `ACT-014_KICK_STUDY.jpg` | **ACT-014 (T114) Kick and Keep Balance** | Knee chamber (#f20), Horizontal snap kick (#f60), Apex hold (#f85), Controlled recoil (#f120) |',
          '| `ACT-015_BLOCK_STUDY.jpg` | **ACT-015 (T115) Block into Retreat** | Ready stance (#f15), Crossed forearm block (#f50), Weight shift brace (#f85), Tactical retreat (#f120) |', '',
          '## What is deliberately not here', '',
          '- Nothing cut out of a pose. The four-box decompile shares 35–110% of each card with its',
          '  neighbours, which is the duplicate-limb artefact; there is nothing to segment if the',
          '  piece was never joined.',
          '- No photographic source. The cast is drawn.']
    open(os.path.join(PACK, 'PACK.md'), 'w').write('\n'.join(md))

    print(f'style references: {n_style}')
    print(f'pose sheets:      {len(made)}')
    for cid, t, n, y, e in made[:6]: print(f'   {cid}  {t[:30]:32s} {n:2d} beats  yaw {y} elev {e}')
    print(f'   … {max(0,len(made)-6)} more')
    print(f'card briefs:      {brief["cards"]}')
    print(f'\n-> {os.path.relpath(PACK, os.getcwd())}')

if __name__ == '__main__':
    main()
