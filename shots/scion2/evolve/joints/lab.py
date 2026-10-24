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
PAIRS = 36
JOINTS = ['neck', 'shoulder', 'elbow', 'wrist', 'hip', 'knee', 'ankle']
CHAR, COSTUME = 'poet', 'red_black_sunglasses'
METHODS0 = {
    'naive': {'pivot': 'kp', 'overlap': 0., 'on_top': 'child', 'trim': 'none', 'width': 'none', 'seam': 'none', 'facing': False},
    'rigkit': {'pivot': 'kp', 'overlap': 1.5, 'on_top': 'parent', 'trim': 'none', 'width': 'none', 'seam': 'brad', 'facing': True},
    'tuck_trim': {'pivot': 'kp', 'overlap': 2.5, 'on_top': 'parent', 'trim': 'contour', 'width': 'uniform', 'seam': 'brad', 'facing': True},
    'brad_pivot': {'pivot': 'brad', 'overlap': 1.5, 'on_top': 'child', 'trim': 'none', 'width': 'uniform', 'seam': 'brad', 'facing': True},
}


def font(sz, bold=False):
    p = '/usr/share/fonts/truetype/dejavu/DejaVuSans%s.ttf' % ('-Bold' if bold else '')
    return ImageFont.truetype(p, sz) if os.path.exists(p) else ImageFont.load_default()


F, FB, FS = font(12), font(15, True), font(10)


def view_ok(a, b):
    return a is None or b is None or a == b


def pairs(joint, seed=0):
    pp, cp = CN.J[joint][0], CN.J[joint][1]
    P = [p for p in PT.parts(CHAR, None) if p['part'] == pp and (p['costume'] == COSTUME or p['part'] == 'head')]
    C = [p for p in PT.parts(CHAR, None) if p['part'] == cp and (p['costume'] == COSTUME or p['part'] == 'head')]
    out = []
    for a in P:
        for b in C:
            if not view_ok(a['view'], b['view']):
                continue
            if joint in ('shoulder', 'hip') and b.get('side') not in ('L', 'R', None):
                continue
            if CN.anchor(a, joint, b.get('side')) is None:
                continue
            out.append((a, b))
    rng = random.Random(seed)
    rng.shuffle(out)
    out = out[:PAIRS]
    split = lambda a, b: 'held' if int(hashlib.md5((a['key'] + b['key']).encode()).hexdigest(), 16) % 3 == 0 else 'train'
    return [(a, b, split(a, b)) for a, b in out]


def load_methods(joint):
    M = dict(METHODS0)
    f = os.path.join(HERE, 'methods', joint + '.json')
    if os.path.exists(f):
        M.update(json.load(open(f)))
    return M


def evaluate(joint, rnd):
    t0 = time.time()
    M = load_methods(joint)
    PR = pairs(joint)
    res = {m: [] for m in M}
    for a, b, sp in PR:
        for ang in ANGLES:
            for m, g in M.items():
                try:
                    r = CN.connect(a, b, joint, ang, g)
                    if r is None:
                        continue
                    q = QA.run(r, a, b, joint, g)
                except Exception as e:
                    traceback.print_exc()
                    continue
                res[m].append({'parent': a['key'], 'child': b['key'], 'split': sp, 'angle': ang, **q})
    summ = {}
    for m, rs in res.items():
        tr = [r for r in rs if r['split'] == 'train']
        he = [r for r in rs if r['split'] == 'held']
        fk = {}
        for r in tr:
            for f in r['fails']:
                fk[f] = fk.get(f, 0) + 1
        summ[m] = {'train_clean': round(np.mean([r['grade'] == 'green' for r in tr]), 3) if tr else None,
                   'held_clean': round(np.mean([r['grade'] == 'green' for r in he]), 3) if he else None,
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
    q = QA.run(r, a, b, joint, g)
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
        jx, jy, br = J[0] - x0, J[1] - y0, q['band_r']
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


def sheet(joint, mname, g, PR, od, rnd, sm, rows=10):
    cs = 158
    W = 260 + len(ANGLES) * cs
    out = Image.new('RGB', (W, 70 + rows * (cs + 22)), (255, 255, 255))
    d = ImageDraw.Draw(out)
    d.text((10, 8), 'JOINT %s  ·  method "%s"  ·  round %02d' % (joint.upper(), mname, rnd), fill=(28, 32, 38), font=FB)
    d.text((10, 30), 'clean on TRAIN %.0f%% · HELD-OUT %s · genes %s' % (100 * (sm['train_clean'] or 0),
           '%.0f%%' % (100 * sm['held_clean']) if sm['held_clean'] is not None else '-', json.dumps(g)[:150]), fill=(95, 101, 112), font=F)
    d.text((10, 48), 'green = clean, amber = one seam test fails, red = two or more; red circle = the failing seam', fill=(95, 101, 112), font=F)
    y = 70
    for a, b, sp in PR[:rows]:
        d.text((6, y + 30), '%s\n+ %s\n(%s, %s / %s)' % (a['src_card'].split('/')[-1][:30], b['src_card'].split('/')[-1][:30], sp,
                                                         a['view'] or '?', b['view'] or '?'), fill=(60, 60, 60), font=FS)
        for i, ang in enumerate(ANGLES):
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
        picks.append((j, best, a, b, rng.choice(ANGLES)))
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
    md = ['# Joint lab round %02d' % rnd, '', '| joint | best method | clean TRAIN | clean HELD-OUT | pair-angles | top failing tests (best method) |',
          '|---|---|---|---|---|---|']
    for j in joints:
        best, summ = results[j]
        s = summ[best]
        fk = ', '.join('%s %d' % kv for kv in sorted(s['fail_kinds_train'].items(), key=lambda kv: -kv[1])[:4])
        md.append('| %s | %s | %.0f%% | %s | %d | %s |' % (j, best, 100 * (s['train_clean'] or 0), '%.0f%%' % (100 * s['held_clean']) if s['held_clean'] is not None else '-',
                                                       s['n_train'] + s['n_held'], fk))
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
