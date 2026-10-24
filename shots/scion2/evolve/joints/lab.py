"""The joint lab: evolve a CONNECTION METHOD per joint type, bottom up.

    python3 -m evolve.joints.lab <round> [joint,joint,...]      (from shots/scion2)

Per joint type: every compatible (parent, child) pair of the poet (same costume; views equal or one unknown; side
matched for shoulders and hips), sampled to PAIRS pairs (seeded), split 2/3 TRAIN / 1/3 HELD-OUT by a hash of the pair;
each pair is connected at ANGLES degrees by every method in the population (methods/<joint>.json + METHODS0); the
seam tests (qa.py) grade every pair-angle. Fitness = share of CLEAN pair-angles on TRAIN; HELD-OUT reported.
Writes joints/round<NN>/: summary.json / summary.md, <joint>_sheet.jpg (best method: one row per pair across the angle
sweep, each cell outlined green / amber / red, the failing seam circled and its tests named), <joint>_failures.jpg,
critic/s01..s12.jpg (pair renders only, no names) + critic_key.json outside the folder.
"""
import hashlib, json, os, random, sys, time, traceback
from multiprocessing import Pool
import numpy as np, cv2
from PIL import Image, ImageDraw, ImageFont

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.abspath(os.path.join(HERE, '..', '..')))
from evolve.joints import parts as PT, connect as CN, qa as QA  # noqa: E402

ANGLES = [-60, -30, 0, 30, 60, 90]
# round 02: sweep only inside each joint's anatomical range (library2 seam.ROM), in 15 degree steps
def rom_angles(joint):
    sys.path.insert(0, os.path.abspath(os.path.join(HERE, '..', '..', 'library2', 'qa')))
    import seam
    lo, hi = seam.ROM.get(joint, seam.ROM['generic'])
    a = list(range(int(lo), int(hi) + 1, 15))
    if a[-1] != hi:
        a.append(int(hi))
    return a


# misfiles reported to library2 (excluded until it re-gates them): a thigh filed as a torso, a foot and a forearm as shins
EXCLUDE = {'poet.red_black_sunglasses.replacements.deep_crouch__left-thigh-2-eyelets', 'poet.04.action.red_black_sunglasses.parts.01__foot-l-foot-r',
           'poet.01.action.black_tshirt.parts.02__farm-r-2',
           # (library2 b0707fa confirmed back_lying__left-thigh as a real jacket torso: off the list; lying torsos stay out of
           #  front / back packs instead)
           # round 06: the file name names another part than the slot it is filed in (suspected; reported to library2)
           'poet.red_black_sunglasses.body.back__poet-black-upper-arm-l', 'poet.04.action.red_black_sunglasses.parts.01__thigh-r-shin-l',
           'poet.14.action.red_black_sunglasses.parts.01__thigh-l', 'poet.14.action.red_black_sunglasses.parts.01__thigh-r',
           'poet.04.action.red_black_sunglasses.parts.02__uarm-l-2', 'poet.04.action.red_black_sunglasses.parts.02__farm-l-2',
           'poet.04.action.red_black_sunglasses.parts.02__farm-r-2', 'poet.red_black_sunglasses.replacements.back_lying__left-boot',
           'poet.red_black_sunglasses.replacements.deep_crouch__left-boot-boot-only'}
FACE_OK = {'painted_face', 'composed_face', 'composed'}


def usable(p, joint):
    """round 02 gates: library2's gates (identity: CLIP + canon length) already applied in parts.py; front-ish heads must
    carry a painted face (or a composed one), back heads must be backs of heads"""
    if p['key'].split('/')[-1] in EXCLUDE:
        return False
    if p['part'] == 'head':
        st = p.get('state')
        if p.get('view') in ('back',):
            return st == 'back_of_head'
        return st in FACE_OK
    return True
PAIRS = 36
JOINTS = ['neck', 'shoulder', 'elbow', 'wrist', 'hip', 'knee', 'ankle']
CHAR, COSTUME = 'poet', 'red_black_sunglasses'
METHODS0 = {
    'naive': {'pivot': 'kp', 'overlap': 0., 'on_top': 'child', 'trim': 'none', 'width': 'none', 'seam': 'none', 'facing': False},
    'rigkit': {'pivot': 'kp', 'overlap': 1.5, 'on_top': 'parent', 'trim': 'none', 'width': 'none', 'seam': 'brad', 'facing': True},
    'tuck_trim': {'pivot': 'kp', 'overlap': 2.5, 'on_top': 'parent', 'trim': 'contour', 'width': 'uniform', 'seam': 'brad', 'facing': True},
    'brad_pivot': {'pivot': 'brad', 'overlap': 1.5, 'on_top': 'child', 'trim': 'none', 'width': 'uniform', 'seam': 'brad', 'facing': True},
    # library2 QA's first finding: the parent's tab (the torso's neck tab and eyelet) over the child
    'tab_trim_under': {'pivot': 'kp', 'overlap': 1.5, 'on_top': 'child', 'trim': 'none', 'width': 'none', 'seam': 'brad', 'facing': True,
                       'parent_tab': .5},
    'register': {'pivot': 'register', 'overlap': 0., 'on_top': 'child', 'trim': 'none', 'width': 'uniform', 'seam': 'brad', 'facing': True,
                 'parent_tab': .5, 'tab_shape': 'round'},
    'register_under': {'pivot': 'register', 'overlap': 0., 'on_top': 'parent', 'trim': 'none', 'width': 'uniform', 'seam': 'brad', 'facing': True},
    'tab_trim_over': {'pivot': 'kp', 'overlap': 1.0, 'on_top': 'parent', 'trim': 'contour', 'width': 'none', 'seam': 'none', 'facing': True,
                      'parent_tab': 0.},
}


def font(sz, bold=False):
    p = '/usr/share/fonts/truetype/dejavu/DejaVuSans%s.ttf' % ('-Bold' if bold else '')
    return ImageFont.truetype(p, sz) if os.path.exists(p) else ImageFont.load_default()


F, FB, FS = font(12), font(15, True), font(10)


def view_ok(a, b):
    return a is None or b is None or a == b


_CL = {}


def cloth_lab(p):
    """median CIE-Lab of a part's non-skin paint (its cloth / leather), cached"""
    if p['key'] not in _CL:
        a = p['img']
        m = a[..., 3] > 200
        lab = cv2.cvtColor(a[..., :3], cv2.COLOR_BGR2LAB).astype(np.float32)[m] * [100 / 255., 1, 1] - [0, 128, 128]
        skin = (lab[:, 0] > 25) & (lab[:, 0] < 75) & (lab[:, 1] > 8) & (lab[:, 2] > 12)
        cl = lab[~skin]
        _CL[p['key']] = (np.median(cl, 0), float(len(cl) / max(len(lab), 1))) if len(cl) > 50 else (None, 0.)
    return _CL[p['key']]


def cloth_match(a, b, tol=25.):
    """round 05 (critic r04: a pale grey sleeve on a black-jacket hand): when both parts carry cloth (>10% non-skin),
    their cloth colours must be within dE tol"""
    ca, fa = cloth_lab(a)
    cb, fb = cloth_lab(b)
    if ca is None or cb is None or fa < .1 or fb < .1:
        return True
    return float(np.linalg.norm(ca - cb)) <= tol


def sheet_of(p):
    return p['src_card'].split('/')[0]


def width_at(p, where):
    """canonical width (px) across the part's axis at its pivot ('pivot') or at a joint keypoint"""
    ax = {'torso': (0, -1), 'pelvis': (0, 1), 'head': (0, -1)}.get(p['part'], (0, 1))
    q = p['pivot'] if where == 'pivot' else np.asarray(p['kp'][where], float)
    u = np.array(ax, float)
    return CN.width_across(p['img'][..., 3], q - (12 * u if where != 'pivot' else -12 * u), u)


def pairs(joint, seed=0):
    """round 03: NATIVE pairs first (parent and child from the same source sheet / set: painted to join each other), then
    cross-sheet pairs whose widths at the joint agree within the joint's tolerance after the allowed uniform scale
    (0.85-1.15); necks take painted heads only (composed faces show their patch outline)"""
    pp, cp = CN.J[joint][0], CN.J[joint][1]
    ok = lambda p, part: p['part'] == part and (p['costume'] == COSTUME or p['part'] == 'head') and usable(p, joint) and \
        (p['part'] != 'head' or p.get('state') == 'painted_face' or p.get('view') == 'back' or
         (p.get('state') == 'composed_face' and p.get('view') == 'front'))     # 87f70e4: front composed heads usable
    P = [p for p in PT.parts(CHAR, None) if ok(p, pp)]
    C = [p for p in PT.parts(CHAR, None) if ok(p, cp)]
    native, cross = [], []
    sys.path.insert(0, os.path.abspath(os.path.join(HERE, '..', '..', 'library2', 'qa')))
    import seam
    lo, hi = seam.TOL.get(joint, seam.TOL['generic'])['ratio']
    for a in P:
        for b in C:
            if not view_ok(a['view'], b['view']):
                continue
            pa = CN.anchor(a, joint, b.get('side'))
            if pa is None:
                continue
            mates = (((a.get('rec') or {}).get('source_set') or {}).get('sheet_mates') or {}).get(b['part'], [])
            if (b['key'] in mates) or (not mates and sheet_of(a) == sheet_of(b) and a['costume'] == b['costume']):
                if a.get('side') in ('L', 'R') and b.get('side') in ('L', 'R') and a['side'] != b['side']:
                    continue
                native.append((a, b))
                continue
            name = CN.J[joint][2]
            kpn = next((k for k in (name, name + '_r', name + '_l', 'tip') if k in a['kp']), None)
            wa = width_at(a, kpn) if kpn else 0
            wb = width_at(b, 'pivot')
            if wa > 5 and wb > 5:
                r_ = wb / wa
                if not (lo / 1.15 <= r_ <= hi / .85):
                    continue
            if not cloth_match(a, b):
                continue
            cross.append((a, b))
    rng = random.Random(seed)
    rng.shuffle(native); rng.shuffle(cross)
    native = native[:PAIRS // 2]
    out = [(a, b, 'native') for a, b in native] + [(a, b, None) for a, b in cross[:PAIRS - len(native)]]
    split = lambda a, b: 'held' if int(hashlib.md5((a['key'] + b['key']).encode()).hexdigest(), 16) % 3 == 0 else 'train'
    return [(a, b, split(a, b) + ('-native' if n else '')) for a, b, n in out]


def load_methods(joint):
    M = dict(METHODS0)
    f = os.path.join(HERE, 'methods', joint + '.json')
    if os.path.exists(f):
        M.update({k: {g: v for g, v in d.items() if not g.startswith('_')} for k, d in json.load(open(f)).items()})
    return M


def evaluate(joint, rnd):
    t0 = time.time()
    M = load_methods(joint)
    PR = pairs(joint)
    res = {m: [] for m in M}
    if os.environ.get('NATIVE_ONLY'):
        PR = [x for x in PR if x[2].endswith('native')]
    for a, b, sp in PR:
        for ang in rom_angles(joint):
            if joint == 'neck' and abs(ang) > 15 and (b.get('view') or 'front') in ('front', 'three-quarter'):
                continue                       # round 04: front heads tilt at most 15 degrees until the collar handles more
            for m, g in M.items():
                try:
                    r = CN.connect(a, b, joint, ang, g)
                    if r is None:
                        continue
                    q = QA.run(r, a, b, joint, g, ang)
                except Exception as e:
                    traceback.print_exc()
                    continue
                if q is None:                  # outside the joint's range: not applicable
                    continue
                res[m].append({'parent': a['key'], 'child': b['key'], 'split': sp, 'angle': ang, **q})
    summ = {}
    for m, rs in res.items():
        tr = [r for r in rs if r['split'].startswith('train')]
        he = [r for r in rs if r['split'].startswith('held')]
        nat = [r for r in rs if r['split'].endswith('native')]
        fk = {}
        for r in tr:
            for f in r['fails']:
                fk[f] = fk.get(f, 0) + 1
        summ[m] = {'train_clean': round(np.mean([r['grade'] == 'green' for r in tr]), 3) if tr else None,
                   'held_clean': round(np.mean([r['grade'] == 'green' for r in he]), 3) if he else None,
                   'native_clean': round(np.mean([r['grade'] == 'green' for r in nat]), 3) if nat else None, 'n_native': len(nat),
                   'n_train': len(tr), 'n_held': len(he), 'fail_kinds_train': fk, 'genes': M[m]}
    best = max(summ, key=lambda m: summ[m]['train_clean'] or 0)
    od = os.path.join(HERE, 'round%02d' % rnd)
    os.makedirs(od, exist_ok=True)
    json.dump({'joint': joint, 'pairs': len(PR), 'angles': ANGLES, 'best': best, 'methods': summ, 'seconds': round(time.time() - t0, 1),
               'results': res}, open(os.path.join(od, joint + '.json'), 'w'))
    sheet(joint, best, M[best], PR, od, rnd, summ[best])
    failures(joint, best, M[best], PR, res[best], od)
    return joint, best, summ


def cell(a, b, joint, ang, g, size=150):
    r = CN.connect(a, b, joint, ang, g)
    if r is None:
        return None, None
    q = QA.run(r, a, b, joint, g, ang)
    if q is None:
        return None, None
    img = r['img']
    al = img[..., 3:] / 255.
    o = (img[..., [2, 1, 0]] * al + 245 * (1 - al)).astype(np.uint8)
    # crop round the joint
    J = r['pivot']
    R = int(max(q['band_r'] * 2.4, 18 * CN.RS))
    x0, y0 = int(max(0, J[0] - R)), int(max(0, J[1] - R))
    x1, y1 = int(min(o.shape[1], J[0] + R)), int(min(o.shape[0], J[1] + R))
    im = Image.fromarray(o[y0:y1, x0:x1])
    d = ImageDraw.Draw(im)
    if q['fails']:
        sp = q.get('spot') or J
        jx, jy, br = sp[0] - x0, sp[1] - y0, max(q['band_r'] * .5, 3 * CN.RS)
        d.ellipse([jx - br, jy - br, jx + br, jy + br], outline=(220, 30, 30), width=2)
    k = size / max(im.width, im.height)
    im = im.resize((max(1, int(im.width * k)), max(1, int(im.height * k))), Image.LANCZOS)
    col = {'green': (40, 170, 60), 'amber': (235, 160, 20), 'red': (215, 40, 40)}[q['grade']]
    c = Image.new('RGB', (size + 8, size + 22), (255, 255, 255))
    c.paste(im, (4 + (size - im.width) // 2, 4 + (size - im.height) // 2))
    d = ImageDraw.Draw(c)
    d.rectangle([1, 1, size + 6, size + 6], outline=col, width=3)
    d.text((4, size + 8), ('%+d° ' % ang) + (','.join(q['fails']) if q['fails'] else 'clean'), fill=col, font=FS)
    return c, q


def sheet(joint, mname, g, PR, od, rnd, sm, rows=14):
    PR = [x for x in PR if x[2].endswith('native')][:6] + [x for x in PR if not x[2].endswith('native')][:rows - 6]
    cs = 158
    AN = rom_angles(joint)
    W = 260 + len(AN) * cs
    out = Image.new('RGB', (W, 70 + rows * (cs + 22)), (255, 255, 255))
    d = ImageDraw.Draw(out)
    d.text((10, 8), 'JOINT %s  ·  method "%s"  ·  round %02d' % (joint.upper(), mname, rnd), fill=(28, 32, 38), font=FB)
    d.text((10, 30), 'clean on TRAIN %.0f%% · HELD-OUT %s · genes %s' % (100 * (sm['train_clean'] or 0),
           '%.0f%%' % (100 * sm['held_clean']) if sm['held_clean'] is not None else '-', json.dumps(g)[:150]), fill=(95, 101, 112), font=F)
    d.text((10, 48), 'green = clean, amber = one seam test fails, red = two or more; red circle = the failing seam', fill=(95, 101, 112), font=F)
    y = 70
    for a, b, sp in PR[:rows]:
        d.text((6, y + 14), 'NATIVE (same sheet)' if sp.endswith('native') else 'cross-sheet', fill=(30, 110, 200) if sp.endswith('native') else (120, 120, 120), font=FS)
        d.text((6, y + 30), '%s\n+ %s\n(%s, %s / %s)' % (a['src_card'].split('/')[-1][:30], b['src_card'].split('/')[-1][:30], sp,
                                                         a['view'] or '?', b['view'] or '?'), fill=(60, 60, 60), font=FS)
        for i, ang in enumerate(AN):
            c, q = cell(a, b, joint, ang, g)
            if c:
                out.paste(c, (250 + i * cs, y))
        y += cs + 22
    out.save(os.path.join(od, '%s_sheet.jpg' % joint), quality=82)


def failures(joint, mname, g, PR, rs, od, n=12):
    bad = [r for r in rs if r['grade'] == 'red'][:n] or [r for r in rs if r['grade'] == 'amber'][:n]
    byk = {p['key']: p for a, b, _ in PR for p in (a, b)}
    cells = []
    for r in bad:
        c, q = cell(byk[r['parent']], byk[r['child']], joint, r['angle'], g, size=180)
        if c:
            cells.append(c)
    if not cells:
        return
    cols = 6
    out = Image.new('RGB', (cols * 190, 40 + ((len(cells) + cols - 1) // cols) * 206), (255, 255, 255))
    ImageDraw.Draw(out).text((8, 8), 'JOINT %s · worst seams of "%s"' % (joint.upper(), mname), fill=(28, 32, 38), font=FB)
    for i, c in enumerate(cells):
        out.paste(c, ((i % cols) * 190, 40 + (i // cols) * 206))
    out.save(os.path.join(od, '%s_failures.jpg' % joint), quality=82)


def critic_pack(rnd, results, seed=0):
    """12 pair renders (best method per joint, random pairs and angles), no names; key outside the folder"""
    od = os.path.join(HERE, 'round%02d' % rnd)
    os.makedirs(os.path.join(od, 'critic'), exist_ok=True)
    rng = random.Random(seed + rnd)
    key = {}
    picks = []
    js = [j for j in results]
    for i in range(12):
        j = js[i % len(js)]
        best = results[j][0]
        PR = pairs(j)
        a, b, sp = rng.choice(PR)
        picks.append((j, best, a, b, rng.choice(rom_angles(j))))
    rng.shuffle(picks)
    for i, (j, best, a, b, ang) in enumerate(picks, 1):
        g = load_methods(j)[best]
        r = CN.connect(a, b, j, ang, g)
        if r is None:
            continue
        img = r['img']
        al = img[..., 3:] / 255.
        o = (img[..., [2, 1, 0]] * al + 245 * (1 - al)).astype(np.uint8)
        J = r['pivot']
        R = int(30 * CN.RS)
        crop = o[int(max(0, J[1] - R)):int(J[1] + R), int(max(0, J[0] - R)):int(J[0] + R)]
        im = Image.fromarray(crop)
        im = im.resize((480, int(480 * im.height / im.width)), Image.LANCZOS)
        im.save(os.path.join(od, 'critic', 's%02d.jpg' % i), quality=88)
        key['s%02d' % i] = {'joint': j, 'method': best, 'parent': a['key'], 'child': b['key'], 'angle': ang}
    json.dump(key, open(os.path.join(od, 'critic_key.json'), 'w'), indent=1)


def main():
    rnd = int(sys.argv[1])
    joints = sys.argv[2].split(',') if len(sys.argv) > 2 else JOINTS
    with Pool(2) as P:
        out = P.starmap(evaluate, [(j, rnd) for j in joints])
    results = {j: (best, summ) for j, best, summ in out}
    md = ['# Joint lab round %02d' % rnd, '', '| joint | best method | clean TRAIN | clean HELD-OUT | clean NATIVE pairs | pair-angles | top failing tests (best method) |',
          '|---|---|---|---|---|---|---|']
    for j in joints:
        best, summ = results[j]
        s = summ[best]
        fk = ', '.join('%s %d' % kv for kv in sorted(s['fail_kinds_train'].items(), key=lambda kv: -kv[1])[:4])
        md.append('| %s | %s | %.0f%% | %s | %s (%d) | %d | %s |' % (j, best, 100 * (s['train_clean'] or 0), '%.0f%%' % (100 * s['held_clean']) if s['held_clean'] is not None else '-',
                  '%.0f%%' % (100 * s['native_clean']) if s.get('native_clean') is not None else '-', s.get('n_native', 0), s['n_train'] + s['n_held'], fk))
    md += ['', '## all methods (clean on TRAIN)', '', '| joint | ' + ' | '.join(sorted({m for j in joints for m in results[j][1]})) + ' |']
    ms = sorted({m for j in joints for m in results[j][1]})
    md.append('|---|' + '---|' * len(ms))
    for j in joints:
        md.append('| %s | %s |' % (j, ' | '.join('%.0f%%' % (100 * results[j][1][m]['train_clean']) if m in results[j][1] and results[j][1][m]['train_clean'] is not None else '-' for m in ms)))
    od = os.path.join(HERE, 'round%02d' % rnd)
    open(os.path.join(od, 'summary.md'), 'w').write('\n'.join(md) + '\n')
    json.dump({j: {'best': results[j][0], 'methods': results[j][1]} for j in joints}, open(os.path.join(od, 'summary.json'), 'w'), indent=1)
    critic_pack(rnd, results)
    print('\n'.join(md))


if __name__ == '__main__':
    main()
