"""A scripted critic for poem 04 (the hands). It reads only the clip, the asset list and the rendered frames,
checks the acceptance list written before the build, and appends PASS / NOT YET with evidence to validation_log.md.

This is NOT an independent reviewer: no separate model was available. Every line is a measurement or a count.
usage: python3 shots/weave/p04_hands/critic.py
"""
import datetime, glob, json, os, subprocess, sys
import cv2
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(HERE))
from weave_lib import WEAVE, raster_ops

clip = json.load(open(os.path.join(WEAVE, 'clips', 'p04_hands.json')))
A = json.load(open(os.path.join(HERE, 'assets', 'assets.json')))
SET = json.load(open(os.path.join(HERE, 'set', 'set.json')))
FILES = {a['id']: os.path.join(WEAVE, a['file']) for a in A['assets'] if a['kind'] == 'puppet_part'}
F, V, FPS, N = clip['frames'], clip['validation'], clip['clock']['fps'], clip['clock']['frames']
ST = {s['id']: s['t'] for s in clip['states']}
M = {m[0]: m for m in clip['measured']}
rows = []


def check(name, ok, evidence, blocking=True):
    rows.append((name, 'PASS' if ok else ('NOT YET' if blocking else 'POLISH'), evidence))


def ids(fr):
    return [o.get('id', '') for o in fr['draw'] if o.get('t') == 'img']


# 1 the failure is on screen: two pats on bare ground, before the light finds the hands, away from the hands
pats = [c for c in clip['contacts'] if 'wrong attempt' in c['what']]
a_rest = clip['scene']['hand_A_rest'][0]
pat_frames = [F[min(N - 1, int(c['t'] * FPS) + 1)] for c in pats]
pat_x = [next((d[0] for d in fr['dbg'] if d[2] == 'on' and d[1] > 900 and abs(d[0] - clip['scene']['toe_near'][0]) > 5), None) for fr in pat_frames]
ok1 = len(pats) == 2 and all(c['t'] < ST['S5_found'][0] for c in pats) and all(x is not None and x < a_rest for x in pat_x)
check('the failure is on screen (wrong attempts)', ok1,
      f'{len(pats)} pats at {[c["t"] for c in pats]} s, before the reveal at {ST["S5_found"][0]} s; stub x {pat_x} < hand A rest x {round(a_rest, 1)}')

# 2 dust persists: every particle still drawn in the last frame, landed on the ground line
last_dots = next(o for o in F[-1]['draw'] if o.get('t') == 'dots')['pts']
on_ground = sum(1 for p in last_dots if abs(p[1] - (clip['scene']['ground'] - 1)) < 0.5)
check('dust lands and stays', len(last_dots) == V['dust_particles'] and on_ground == len(last_dots),
      f'{len(last_dots)} of {V["dust_particles"]} particles drawn in the last frame, {on_ground} resting on the ground line')

# 3 the archive is labelled for as long as it shows, wholly on screen
bad = []
for fr in F:
    labels = [o['txt'] for o in fr['draw'] if o.get('t') == 'label']
    if 'sky1969' in ids(fr) and not any('SKY' in t for t in labels):
        bad.append((fr['t'], 'sky'))
    if any(i.startswith('seq:cit') for i in ids(fr)) and not any('SHIP' in t for t in labels):
        bad.append((fr['t'], 'citizen'))
lab = M.get('archive labels wholly on screen')
check('archive labelled whenever it shows', not bad and lab and lab[2],
      f'{len(bad)} unlabelled archive frames{(" first " + str(bad[:3])) if bad else ""}; {lab[1] if lab else "no on-screen measure"}')

# 4 no pop-ins: anything absent at frame 0 must enter by a wipe or rise from behind the ledge
first = {}
for fr in F:
    for i in ids(fr):
        key = 'seq:cit' if i.startswith('seq:cit') else i
        first.setdefault(key, fr['f'])
late = {k: f for k, f in first.items() if f > 0}
cit_ok = True
if 'seq:cit' in late:
    fr = F[late['seq:cit']]
    o = next(o for o in fr['draw'] if o.get('id', '').startswith('seq:cit'))
    top = o['m'][5]          # the image origin's y: the top of the cut at rise ~0
    cit_ok = top > SET['ledge']['top_y'] - 20
sky_ok = 'sky1969' not in late or next(o for o in F[late['sky1969']]['draw'] if o.get('id') == 'sky1969')['wipe']['y'] < 0
hand_ok = all(k in ('hand_open', 'hand_near') or k in ('seq:cit', 'sky1969') for k in late)
check('nothing pops in', cit_ok and sky_ok and hand_ok,
      f'late entries {late}; the citizen enters with its top at y {round(top, 1) if "seq:cit" in late else "-"} (ledge top {SET["ledge"]["top_y"]}); the sky enters with its wipe edge above the frame: {sky_ok}')

# 5 contacts
for name in ['near toe drift', 'grip error < 1% (A pinching B)', 'press error < 1% (wrist onto A)', 'pat error < 1% (stub on ground)',
             'fit gap before the brad < 1%', 'knees on ground after kneel', 'far knee joint gap < 1% (rigid far leg vs skirt)', 'IK reach ratio max']:
    m = next((x for k, x in M.items() if k.startswith(name.split(' (')[0])), None)
    if m:
        check(m[0], bool(m[2]), m[1])
ft = next((x for k, x in M.items() if k.startswith('far toe planted')), None)
if ft:
    check(ft[0], bool(ft[2]), ft[1])

# 6 the head stays readable: how much of the face is covered by parts drawn after it
worst = (1.0, None)
for f in range(0, N, 6):
    fr = F[f]
    order = [o['id'] for o in fr['draw'] if o.get('t') == 'img' and o.get('id') in FILES]
    if 'head' not in order:
        continue
    head = raster_ops(fr['draw'], FILES, ['head'])
    over = raster_ops(fr['draw'], FILES, order[order.index('head') + 1:])
    vis = 1 - (head & over).sum() / max(1, head.sum())
    if vis < worst[0]:
        worst = (vis, fr['t'])
check('her head stays readable (>= 85% of it uncovered)', worst[0] >= 0.85, f'worst {round(100 * worst[0], 1)}% visible at {worst[1]} s (sampled every 6th frame)')

# 7 the render: frames on disk, no unexplained jumps between frames, mp4 present with sound
frames = sorted(glob.glob(os.path.join(HERE, 'frames', '*.jpg')))
check('every frame rendered', len(frames) == N, f'{len(frames)} of {N} frames on disk')
if len(frames) == N:
    diffs, prev = [], None
    for p in frames:
        g = cv2.resize(cv2.imread(p, cv2.IMREAD_GRAYSCALE), (480, 270)).astype(np.float32)
        if prev is not None:
            diffs.append(float(np.abs(g - prev).mean()))
        prev = g
    d = np.array(diffs); med = float(np.median(d)); i = int(d.argmax())
    check('no jump cuts or pops between frames (max step < 6x median and < 12 grey levels)', d.max() < max(6 * med, 1.5) and d.max() < 12,
          f'median step {med:.2f}, max {d.max():.2f} between f{i} and f{i + 1} ({F[i]["t"]} s)', blocking=False)
mp4 = os.path.join(HERE, 'passage.mp4')
if os.path.exists(mp4):
    pr = subprocess.run(['ffprobe', '-v', 'error', '-show_entries', 'stream=codec_type,duration', '-of', 'json', mp4], capture_output=True, text=True)
    st = json.loads(pr.stdout)['streams']
    kinds = {s['codec_type']: round(float(s.get('duration', 0)), 2) for s in st}
    check('passage.mp4 has picture and sound of the clip length', 'video' in kinds and 'audio' in kinds and abs(kinds['video'] - N / FPS) < 0.1,
          f'{kinds}; clip {round(N / FPS, 2)} s')
else:
    check('passage.mp4 exists', False, 'not rendered yet')

# 8 not claimed
check('an independent critic watched it', False, 'no separate model was available; these are scripted measurements, and a person still has to watch it', blocking=False)

verdict = 'PASS' if all(r[1] != 'NOT YET' for r in rows) else 'NOT YET'
stamp = datetime.datetime.now().strftime('%Y-%m-%d %H:%M')
lines = [f'\n## critic run {stamp} - {verdict}\n', '| check | result | evidence |', '|---|---|---|']
lines += [f'| {a} | {b} | {c} |' for a, b, c in rows]
log = os.path.join(HERE, 'validation_log.md')
if not os.path.exists(log):
    open(log, 'w').write('# Validation log - poem 04, the hands\n\nEach run of critic.py appends a table. Earlier runs are kept.\n')
open(log, 'a').write('\n'.join(lines) + '\n')
for a, b, c in rows:
    print(f'{b:8s} {a}: {c}')
print('verdict', verdict)
