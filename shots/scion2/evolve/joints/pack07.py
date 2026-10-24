"""Round 07 / 08 blind critic pack: 12 joint renders + 4 controls, shuffled into 16 sheets.

Round 08 (critic r07): angles capped at 120 deg (elbow, knee) and +-20 deg (back necks); rom.sweep now needs the
union connected through the pivot disc; elbow / knee pairs must carry the piping across (piping.match, mirroring the
child when that fixes it); new controls (shoulder, wrist, hip, and an elbow again from another painting).

Joints (critic r06 fixes): hip 1, neck 2, shoulder 2, wrist 1, ankle 2, elbow 2, knee 2. Elbows and knees use the
round_end variant (register_round). Each pair's clean ROM is measured first (rom.sweep: no background in the crook,
no notch cut by the method, under piece >= 40% visible) and its angle is sampled inside that range. Torsos in front /
back packs must be front / back stance torsos (no lying / falling / profile / seat cards); connector pieces are never
parents. Wrist z-order per pair: the order that does not cover the hand's fingers (seam 'covered'), else fewer tab cm2.

Controls: 4 unaltered painted joints (back neck, elbow, knee, ankle) cut from the master pose paintings
(shots/kits/cut/<sheet>/<pose>.webp, joint markers from shots/rig/poses_v2), kept to the two segments meeting at the
joint (a capsule round each bone; the painting's own alpha outside the figure).

All 16 are rendered the same way: a 60 cm field centred on the joint, resampled to 2.5 px/cm (the paintings' scale)
and enlarged to 480 px, on the same 245 grey. The key (critic_key.json, outside the folder) names the controls.

    python3 -m evolve.joints.pack07 [round]          (from shots/scion2)
"""
import json, math, os, random, sys
import numpy as np, cv2
from PIL import Image
from evolve.joints import connect as CN, lab as L, qa as QA, rom as ROM, piping as PI

HERE = os.path.dirname(os.path.abspath(__file__))
SHOTS = os.path.abspath(os.path.join(HERE, '..', '..', '..'))
FIELD_CM, PX_CM, OUT = 60, 2.5, 480
MIX = [('hip', ['register_align']), ('neck', ['register']), ('neck', ['register']), ('shoulder', ['register_align']), ('shoulder', ['register_align']),
       ('wrist', ['register_align', 'register_under_align']), ('ankle', ['boot_over_align']), ('ankle', ['boot_over_align']),
       ('elbow', ['register_round']), ('elbow', ['register_round']), ('knee', ['register_round']), ('knee', ['register_round'])]
BAD_TORSO = ('lie', 'lying', 'fall', 'profile', 'connector', 'connecter', 'seat', 'reach')
CONTROLS7 = [('neck', 'poet.11.main-poses/01-wall-rear-three-quarter-touch', 'neck', ('head', 25), ('groin', 30)),
            ('elbow', 'poet.11.main-poses/05-read-water-reathe-1', 'elbowL', ('shoulderL', 6), ('wristL', 6)),
            ('knee', 'poet.04.main-poses/04-2-kneel-hollow', 'kneeR', ('hipR', 8), ('ankleR', 7)),
            ('ankle', 'poet.12.main-poses/02', 'ankleL', ('kneeL', 7), ('toeL', 9))]
CONTROLS8 = [('shoulder', 'poet.11.main-poses/02-front-guide-stone', 'shoulderL', ('elbowL', 6), ('hipL', 12)),
             ('wrist', 'poet.13.main-poses/06-refocus', 'wristR', ('elbowR', 5), ('@ext:elbowR:11', 6)),
             ('hip', 'poet.08.main-poses/03-gentle-slow-bent-knee-dance-alone', 'hipL', ('kneeL', 8), ('groin', 10)),
             ('elbow', 'poet.04.main-poses/04-4-empty-cuffs', 'elbowL', ('shoulderL', 6), ('wristL', 6))]
CAP = {'elbow': (0, 120), 'knee': (0, 120)}


def pack_ok(j, a, b):
    """front / back stance torsos only; no connector parents"""
    name = lambda p: p['key'].split('/')[-1].lower()
    for p in (a, b):
        if p['part'] == 'torso' and (p.get('view') not in ('front', 'back') or any(t in name(p) for t in BAD_TORSO)):
            return False
    if any(t in name(a) for t in ('connector', 'connecter')):
        return False
    # the jacket is black: pale (unpainted / white reserve) cloth cards are a different costume whatever their label
    for p in (a, b):
        if p['part'] in ('torso', 'upper_arm', 'forearm', 'thigh', 'shin', 'pelvis') and pale(p):
            return False
    return True


_PALE = {}


def pale(p):
    if p['key'] not in _PALE:
        im = p['img']
        m = im[..., 3] > 128
        _PALE[p['key']] = bool(m.any() and float(im[..., :3][m].mean()) > 110)
    return _PALE[p['key']]


def finish(rgb_on_grey, centre, px_cm):
    """the common rendering: a FIELD_CM field round centre, resampled to PX_CM, enlarged to OUT px"""
    R = FIELD_CM / 2 * px_cm
    H, W = rgb_on_grey.shape[:2]
    pad = int(R) + 2
    big = cv2.copyMakeBorder(rgb_on_grey, pad, pad, pad, pad, cv2.BORDER_CONSTANT, value=(245, 245, 245))
    cx, cy = centre[0] + pad, centre[1] + pad
    crop = big[int(cy - R):int(cy + R), int(cx - R):int(cx + R)]
    n = int(FIELD_CM * PX_CM)
    small = cv2.resize(crop, (n, n), interpolation=cv2.INTER_AREA)
    return Image.fromarray(small).resize((OUT, OUT), Image.LANCZOS)


def render_joint(r):
    img = r['img']
    al = img[..., 3:] / 255.
    o = (img[..., [2, 1, 0]] * al + 245 * (1 - al)).astype(np.uint8)
    return finish(o, r['target'], CN.RS)


def seg_dist(xx, yy, p, q):
    p, q = np.asarray(p, float), np.asarray(q, float)
    v = q - p
    t = np.clip(((xx - p[0]) * v[0] + (yy - p[1]) * v[1]) / max(1e-6, v @ v), 0, 1)
    return np.hypot(xx - (p[0] + t * v[0]), yy - (p[1] + t * v[1]))


def render_control(tid, joint_m, segs, T):
    t = T[tid]
    sc = (t['solves'][0].get('scale_px_per_cm') if t.get('solves') else None) or t['scale_prior']['px_per_cm']
    im = np.asarray(Image.open(os.path.join(SHOTS, t['img'])).convert('RGBA')).astype(np.float32)
    m = t['markers']
    J = m[joint_m][:2]
    H, W = im.shape[:2]
    yy, xx = np.mgrid[0:H, 0:W]
    keep = np.zeros((H, W), bool)
    for mk, r_cm in segs:
        if mk.startswith('@ext:'):              # past the joint, continuing the line from another marker (no hand marker)
            frm, cm_ = mk[5:].split(':')
            v = np.asarray(J, float) - np.asarray(m[frm][:2], float)
            end = np.asarray(J, float) + v / max(1e-6, np.linalg.norm(v)) * float(cm_) * sc
        else:
            end = m[mk][:2]
        keep |= seg_dist(xx, yy, J, end) <= r_cm * sc
    al = im[..., 3:] / 255. * keep[..., None]
    o = (im[..., :3] * al + 245 * (1 - al)).astype(np.uint8)
    return finish(o, J, sc), {'target': tid, 'marker': joint_m, 'px_per_cm': round(sc, 3)}


def main():
    rnd = int(sys.argv[1]) if len(sys.argv) > 1 else 7
    od = os.path.join(HERE, 'round%02d' % rnd)
    os.makedirs(os.path.join(od, 'critic'), exist_ok=True)
    rng = random.Random(rnd)
    sheets, used, romtab = [], set(), []
    for j, ms in MIX:
        M = L.load_methods(j)
        PR = [x for x in L.pairs(j) if pack_ok(j, x[0], x[1])]
        for _ in range(60):
            a, b, sp = rng.choice(PR)
            if (a['key'], b['key']) in used:
                continue
            best = None
            for m in ms:
                g = M[m]
                if rnd >= 8 and j in ('elbow', 'knee'):
                    ok, g, offs = PI.match(a, b, j, g)
                    if not ok:
                        continue
                res = ROM.sweep(a, b, j, g)
                rr = ROM.run_range(res, 'ok')
                if rr is None:
                    continue
                lo, hi = CAP.get(j, (-999, 999)) if rnd >= 8 else (-999, 999)
                if rnd >= 8 and j == 'neck':
                    lo, hi = (-20, 20) if (b.get('view') or '').startswith('back') else (-15, 15)   # faces tilt at most 15
                angs = [x for x in sorted(res) if rr[0] <= x <= rr[1] and lo <= x <= hi]
                if not angs:
                    continue
                bends = [x for x in angs if x != 0] or angs
                ang = rng.choice(bends)
                r = CN.connect(a, b, j, ang, g)
                if r is None:
                    continue
                q = QA.run(r, a, b, j, g, ang)
                fails = (q or {}).get('fails', [])
                cost = (10 if 'covered' in fails else 0) + float((q or {}).get('tests', {}).get('tab_cm2') or 0) / 10.
                if best is None or cost < best[0]:
                    best = (cost, m, ang, r, q, rr, bool(g.get('mirror')))
            if best is None:
                continue
            cost, m, ang, r, q, rr, mirrored = best
            used.add((a['key'], b['key']))
            romtab.append({'joint': j, 'method': m, 'parent': a['key'], 'child': b['key'], 'clean_rom': rr, 'angle': ang})
            sheets.append((render_joint(r), {'kind': 'joint', 'joint': j, 'method': m, 'parent': a['key'], 'child': b['key'], 'angle': ang,
                                             'clean_rom': rr, 'mirrored_for_piping': mirrored, 'on_top': r['on_top'], 'vis_under': round(r['vis_under'], 3),
                                             'seam': None if q is None else {'grade': q['grade'], 'fails': q['fails'],
                                                                             'tab_cm2': q['tests'].get('tab_cm2'), 'light_rim2': q['tests'].get('light_rim2')}}))
            break
    T = {t['id']: t for t in json.load(open(os.path.join(SHOTS, 'rig', 'poses_v2', 'poet__red_black_sunglasses.json')))['targets']}
    for j, tid, jm, s1, s2 in (CONTROLS8 if rnd >= 8 else CONTROLS7):
        im, info = render_control(tid, jm, [s1, s2], T)
        sheets.append((im, dict(kind='CONTROL (unaltered painting)', joint=j, **info)))
    rng.shuffle(sheets)
    key = {}
    for i, (im, info) in enumerate(sheets, 1):
        im.save(os.path.join(od, 'critic', 's%02d.jpg' % i), quality=88)
        key['s%02d' % i] = info
    json.dump(key, open(os.path.join(od, 'critic_key.json'), 'w'), indent=1)
    json.dump(romtab, open(os.path.join(od, 'pack_rom.json'), 'w'), indent=1)
    for k, v in key.items():
        print(k, v['kind'], v['joint'], v.get('method', ''), v.get('angle', ''), v.get('clean_rom', ''), (v.get('seam') or {}).get('fails', ''))


if __name__ == '__main__':
    main()
