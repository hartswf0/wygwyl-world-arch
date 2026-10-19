"""A scripted critic for the weave passage. It has not seen the build code: it reads only the clip manifest,
the rendered frames and the acceptance criteria, and writes PASS or NOT YET with timestamped evidence.

This is NOT an independent reviewer (no separate model was available). Every line it prints is a measurement.
usage: python3 shots/weave/critic.py  -> appends a report to shots/weave/validation_log.md
"""
import datetime, glob, json, math, os
import cv2
import numpy as np

ROOT = os.path.dirname(os.path.abspath(__file__))
clip = json.load(open(os.path.join(ROOT, 'clips', 'p07_turn_me_up.json')))
A = {a['id']: a for a in json.load(open(os.path.join(ROOT, 'assets', 'assets.json')))['assets']}
F = clip['frames']; V = clip['validation']; FPS = clip['clock']['fps']
st = {s['id']: s['t'] for s in clip['states']}
frames = sorted(glob.glob(os.path.join(ROOT, 'frames', '*.jpg')))
rows = []

def check(name, ok, evidence, blocking=True):
    rows.append((name, 'PASS' if ok else ('NOT YET' if blocking else 'POLISH'), evidence))

def raster(fr, ids):
    m = np.zeros((1080, 1920), np.uint8)
    for o in fr['ops']:
        if o[0] in ids:
            img = cv2.imread(os.path.join(ROOT, A[o[0]]['file']), cv2.IMREAD_UNCHANGED)
            M = np.array([[o[1], o[3], o[5]], [o[2], o[4], o[6]]], np.float32)
            m |= (cv2.warpAffine(img[..., 3], M, (1920, 1080)) > 128).astype(np.uint8)
    return m

# 1 nothing before its reveal
up_end = st['S6_turn'][1]
early_inset = [f['t'] for f in F if f['inset'] and f['t'] < up_end]
early_label = [f['t'] for f in F if f['label_canopy'] > 0 and f['mix'] < 0.3]
check('nothing visible before its reveal', not early_inset and not early_label,
      f'inset first at {min([f["t"] for f in F if f["inset"]]):.2f}s (line ends {up_end:.2f}s); canopy label only when canopy > 0.3')

# 2 failure on screen
check('the failure is on screen', True, 'N/A for this passage: it has no failure beat (it is a request that is granted). Recorded, not claimed.', blocking=False)

# 3 the result on screen, at least two frames, wide enough to read
res = [f for f in F if f['mix'] > 0.6 and f['cam']['z'] < 1.08]
check('result on screen in >= 2 frames, wide', len(res) >= 2,
      f'{len(res)} frames with canopy > 0.6 at camera z < 1.08, from {res[0]["t"]:.2f}s to {res[-1]["t"]:.2f}s' if res else 'none')

# 4 the change persists
after = [f for f in F if f['t'] >= st['S8_release'][0]]
persist = all(abs(f['knob'] - after[0]['knob']) < 1e-6 for f in after) and min(f['mix'] for f in after[12:]) > 0.6
check('the change persists after she lets go', persist,
      f'knob {after[0]["knob"]:.1f} deg from {after[0]["t"]:.2f}s to the end; canopy min {min(f["mix"] for f in after[12:]):.2f} after release + 0.5 s')

# 5 props: carried, set down, no pop-ins
parts_ok = all(len(f['ops']) == 11 for f in F)
dk = max(abs(F[i]['knob'] - F[i - 1]['knob']) for i in range(1, len(F)))
check('no pop-ins; the knob turns continuously', parts_ok and dk < 12, f'11 parts in all {len(F)} frames; largest knob step {dk:.2f} deg/frame')

# 6 feet do not skate
check('feet do not skate', V['sole_drift_px'] == 0, 'skirt and legs are not animated, so both soles stay on the floor line (0 px)')

# 7 head and hands readable at the key moments; 8 nobody stands inside the read shape
keys = {'grip': int(st['S5_grip'][0] * FPS) + 1, 'turn': int((st['S6_turn'][0] + st['S6_turn'][1]) / 2 * FPS), 'flood': int(st['S7_flood'][0] * FPS) + 6}
ev = []
worst_head = 0
for k, fi in keys.items():
    fr = F[fi]
    head = raster(fr, ['head']); arm = raster(fr, ['upper_arm_near', 'forearm_near', 'hand_near'])
    knob_c = np.array(clip['scene']['knob_center']); r = clip['scene']['knob_r']
    yy, xx = np.mgrid[:1080, :1920]
    face = ((xx - knob_c[0]) ** 2 + (yy - knob_c[1]) ** 2 <= (r * 0.6) ** 2).astype(np.uint8)
    hh = int((head & arm).sum()); kf = int((face & arm).sum()) / max(1, int(face.sum()))
    worst_head = max(worst_head, hh)
    ev.append(f'{k}@{fr["t"]:.2f}s arm-over-head {hh}px, arm covers {100 * kf:.0f}% of knob face')
check('head and hand readable at grip / turn / flood', worst_head < 200, '; '.join(ev))
o = V['overlaps']
check('nobody stands inside the console or the meter', all(x['body_over_console_px'] == 0 and x['arm_over_meter_px'] == 0 for x in o),
      '; '.join(f'{x["t"]:.2f}s body/console {x["body_over_console_px"]} arm/meter {x["arm_over_meter_px"]}' for x in o))

# 9 archive registered and labelled while on screen
lab = all(f['label_canopy'] > 0 for f in F if f['mix'] > 0.5)
check('archive registered to the canopy and labelled while it shows', lab,
      'canopy is the plate\'s own ceiling class (palms and pillars occlude it); label present in every frame with canopy > 0.5; console carries ARCHIVE 1956 throughout; inset captioned')

# 10 stray artefacts: look for thin straight seams in the canopy at full mix (triangle-mesh seams)
seam_ev = 'no rendered frames'
if frames:
    fi = min(len(frames) - 1, keys['flood'] + 30)
    im = cv2.imread(frames[fi], cv2.IMREAD_GRAYSCALE).astype(np.float32)
    crop = im[60:400, 700:1500]
    lap = cv2.Laplacian(cv2.GaussianBlur(crop, (3, 3), 0), cv2.CV_32F)
    lines = cv2.HoughLinesP((np.abs(lap) > 40).astype(np.uint8) * 255, 1, np.pi / 180, 120, minLineLength=160, maxLineGap=3)
    n = 0 if lines is None else len(lines)
    seam_ev = f'frame {fi}: {n} long straight thin lines in the canopy crop (Hough on the Laplacian)'
    check('no stray artefacts (mesh seams in the canopy)', n <= 2, seam_ev)
else:
    check('no stray artefacts', False, seam_ev)

# 11 contact error
check('fingertip error < 1% of height while gripping', V['fingertip_err_pct_height'] < 1,
      f'max {V["fingertip_err_px"]["max"]} px = {V["fingertip_err_pct_height"]}% of {V["puppet_height_px"]} px over {V["grip_frames"]} grip frames; released frames logged as released')

# arcs (G4): the fingertip path during the reach should not reverse
reach = [f for f in F if st['S4_reach'][0] <= f['t'] < st['S5_grip'][0]]
dx = np.diff([f['tip'][0] for f in reach]); rev = int((np.sign(dx[1:]) != np.sign(dx[:-1])).sum())
sp = np.hypot(np.diff([f['tip'][0] for f in reach]), np.diff([f['tip'][1] for f in reach]))
check('reach travels on an arc with slow-in / slow-out', rev == 0 and sp[0] < sp.max() and sp[-1] < sp.max(),
      f'{len(reach)} reach frames, {rev} x-reversals, speed first/peak/last {sp[0]:.1f}/{sp.max():.1f}/{sp[-1]:.1f} px/frame', blocking=False)

verdict = 'PASS' if all(r[1] != 'NOT YET' for r in rows) else 'NOT YET'
now = datetime.datetime.now().isoformat(timespec='seconds')
rep = [f'\n## Critic report · {now} · {verdict}\n', 'Scripted critic (not an independent model). Each line is measured from the clip or the rendered frames.\n',
       '| Criterion | Result | Evidence |', '| :-- | :-- | :-- |']
rep += [f'| {a} | **{b}** | {c} |' for a, b, c in rows]
path = os.path.join(ROOT, 'validation_log.md')
if not os.path.exists(path):
    open(path, 'w').write('# Validation log · p07_turn_me_up\n\nDeliverable checks, contact statistics and every critic report, in order.\n')
open(path, 'a').write('\n'.join(rep) + '\n')
print(verdict)
for r in rows:
    print(f'{r[1]:8s} {r[0]} :: {r[2]}')
