"""Round 06 blind critic pack (critic r05 fixes 1-3 in connect.py: no brad sprite, top piece's own grommet, side /
rim trim, under piece >= 40% visible). 12 renders: hip 1, neck 2, shoulder 2, elbow 2, wrist 1, ankle 2, knee 2
(round 05's mix without the waist, plus a second elbow and knee; one wrist fewer to keep 12). Pairs and angles are
random; a draw is redrawn when the method rejects it (no grommet on either piece) or a piece is under 40% visible.

    python3 -m evolve.joints.pack06 [round]          (from shots/scion2)
"""
import json, os, random, sys
import numpy as np
from PIL import Image
from evolve.joints import connect as CN, lab as L, qa as QA

HERE = os.path.dirname(os.path.abspath(__file__))
MIX = [('hip', 'register_align'), ('neck', 'register'), ('neck', 'register'), ('shoulder', 'register_align'), ('shoulder', 'register_align'),
       ('elbow', 'register'), ('elbow', 'register'), ('wrist', 'register_under_align'), ('ankle', 'boot_over_align'),
       ('ankle', 'boot_over_align'), ('knee', 'register'), ('knee', 'register')]


def main():
    rnd = int(sys.argv[1]) if len(sys.argv) > 1 else 6
    od = os.path.join(HERE, 'round%02d' % rnd)
    os.makedirs(os.path.join(od, 'critic'), exist_ok=True)
    rng = random.Random(rnd)
    renders, used = [], set()
    for j, m in MIX:
        g = L.load_methods(j)[m]
        PR = L.pairs(j)
        for _ in range(200):
            a, b, sp = rng.choice(PR)
            ang = rng.choice(L.rom_angles(j))
            if j == 'neck' and abs(ang) > 15 and not (b.get('view') or '').startswith('back'):
                continue                       # front / unknown-view heads tilt at most 15 degrees
            if (a['key'], b['key']) in used:
                continue
            r = CN.connect(a, b, j, ang, g)
            if r is None or r['vis_under'] < QA.VIS_MIN:
                continue
            used.add((a['key'], b['key']))
            q = QA.run(r, a, b, j, g, ang)
            renders.append((j, m, a, b, ang, r, q))
            break
    rng.shuffle(renders)
    key = {}
    for i, (j, m, a, b, ang, r, q) in enumerate(renders, 1):
        img = r['img']
        al = img[..., 3:] / 255.
        o = (img[..., [2, 1, 0]] * al + 245 * (1 - al)).astype(np.uint8)
        J = r['pivot']
        R = int(30 * CN.RS)
        crop = o[int(max(0, J[1] - R)):int(J[1] + R), int(max(0, J[0] - R)):int(J[0] + R)]
        im = Image.fromarray(crop)
        im = im.resize((480, int(480 * im.height / im.width)), Image.LANCZOS)
        im.save(os.path.join(od, 'critic', 's%02d.jpg' % i), quality=88)
        key['s%02d' % i] = {'joint': j, 'method': m, 'parent': a['key'], 'child': b['key'], 'angle': ang, 'on_top': r['on_top'],
                            'vis_under': round(r['vis_under'], 3), 'seam': None if q is None else {'grade': q['grade'], 'fails': q['fails']}}
    json.dump(key, open(os.path.join(od, 'critic_key.json'), 'w'), indent=1)
    print(json.dumps({k: (v['joint'], v['method'], v['on_top'], v['vis_under'], v['seam'] and v['seam']['grade']) for k, v in key.items()}, indent=0))


if __name__ == '__main__':
    main()
