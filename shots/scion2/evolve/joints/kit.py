"""Compatibility graph and kit search: one compatible part per slot, joined CLEAN by the evolved methods.

    python3 -m evolve.joints.kit front [round]          (from shots/scion2)

Graph: nodes are library2 parts of the poet (red_black costume, gated, misfiles excluded); an edge joins a parent and
child of a joint type when that joint's chosen method (METHOD below: the best of the lab's latest round, except the
ankle, where the blind critic outranks the proxy and boot_over_align is used) joins them CLEAN at 0 degrees; its
weight is the clean span: the largest run of CLEAN angles round 0 inside the joint's range of motion (library2
seam.ROM, 15 degree steps). Native pairs (sheet mates) are marked; they are tried first.
Kit: slots torso, head, pelvis, upper_arm, forearm, hand, thigh, shin, foot (one card per slot, the same card both
sides, mirrored for his left). Every joint must be CLEAN at neutral; score = sum over joints of clean span / ROM
span (bendability) + 0.15 per native edge - 1 per segment whose length, normalised by the kit's median ratio to
canon (library2 canon.json), is off by more than 12%. Search: per torso candidate, the best head, arm chain, pelvis
and leg chain (beam 3 each), combined and checked for proportion. Slots with no compatible part are reported as gaps.
Writes joints/kits/<view>/: graph.json, kit.json, parts.jpg (the kit's parts on the grid with clean ranges),
neutral.jpg, bends.jpg (arm raise, elbow, knee, head +-15, each seam outlined green / amber / red), bendability.jpg.
"""
import itertools, json, math, os, sys, time
import numpy as np, cv2
from PIL import Image, ImageDraw, ImageFont

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.abspath(os.path.join(HERE, '..', '..')))
from evolve.joints import parts as PT, connect as CN, qa as QA, lab as L  # noqa: E402

JOINTS = ['neck', 'shoulder', 'elbow', 'wrist', 'waist', 'hip', 'knee', 'ankle']
CHAIN = {'neck': ('torso', 'head'), 'shoulder': ('torso', 'upper_arm'), 'elbow': ('upper_arm', 'forearm'), 'wrist': ('forearm', 'hand'),
         'waist': ('pelvis', 'torso'), 'hip': ('pelvis', 'thigh'), 'knee': ('thigh', 'shin'), 'ankle': ('shin', 'foot')}
K = 6                       # candidates per slot
PROP_TOL = .12
F, FB, FS = L.font(12), L.font(15, True), L.font(10)


def method_for(joint, rnd):
    if joint == 'ankle':
        return 'boot_over_align'
    for r in range(rnd, 0, -1):
        f = os.path.join(HERE, 'round%02d' % r, 'summary.json')
        if os.path.exists(f):
            S = json.load(open(f))
            if joint in S:
                return S[joint]['best']
    return 'register'


def view_ok(p, view):
    return p['view'] in (view, None)


def candidates(view):
    """K parts per slot: gated, the red_black costume (heads: painted or front-composed), the view or unknown; natives of
    the best torsos first, then by smallest canon deviation"""
    allp = [p for p in PT.parts(L.CHAR, None) if view_ok(p, view) and L.usable(p, 'kit')]
    by = {}
    for p in allp:
        if p['part'] != 'head' and p['costume'] != L.COSTUME:
            continue
        if p['part'] == 'head' and not (p.get('state') == 'painted_face' or (p.get('state') == 'composed_face' and view == 'front')):
            continue
        by.setdefault(p['part'], []).append(p)

    def dev(p):
        d = ((p.get('rec') or {}).get('canon_deviation') or {}).get('length_ratio')
        return abs(math.log(d)) if d else 1.
    torsos = sorted([t for t in by.get('torso', []) if 'shoulder_l' in t['kp'] and 'shoulder_r' in t['kp']], key=dev)[:K]
    mates = set()
    for t in torsos:
        for keys in (((t.get('rec') or {}).get('source_set') or {}).get('sheet_mates') or {}).values():
            mates |= set(keys)
    out = {'torso': torsos}
    for part in ('head', 'pelvis', 'upper_arm', 'forearm', 'hand', 'thigh', 'shin', 'foot'):
        ps = by.get(part, [])
        ps.sort(key=lambda p: (p['key'] not in mates, dev(p)))
        out[part] = ps[:K]
    return out


_EV = {}


def edge(joint, a, b, M, side=None):
    """clean angles of a pair under the joint's method (cached)"""
    key = (joint, a['key'], b['key'], side)
    if key in _EV:
        return _EV[key]
    g = M[joint][1]
    res = {}
    for ang in L.rom_angles(joint):
        if joint == 'neck' and abs(ang) > 15 and (b.get('view') or 'front') in ('front', 'three-quarter'):
            continue
        r = CN.connect(a, b, joint, ang, g, side=side)
        if r is None:
            continue
        q = QA.run(r, a, b, joint, g, ang)
        if q is not None:
            res[ang] = q['grade']
    _EV[key] = res
    return res


def span(res, joint):
    """the largest run of CLEAN angles containing 0 (degrees), and the ROM span"""
    angs = sorted(res)
    if not angs:
        return 0., 1.
    rom = max(angs) - min(angs) or 1.
    z = min(angs, key=abs)
    if res.get(z) != 'green':
        return 0., rom
    i = angs.index(z)
    lo = hi = i
    while lo > 0 and res[angs[lo - 1]] == 'green':
        lo -= 1
    while hi < len(angs) - 1 and res[angs[hi + 1]] == 'green':
        hi += 1
    return float(angs[hi] - angs[lo]), float(rom)


def native(a, b):
    m = (((a.get('rec') or {}).get('source_set') or {}).get('sheet_mates') or {}).get(b['part'], [])
    return b['key'] in m


def canon_lengths():
    p = os.path.join(PT.LIB2, 'canon.json')
    C = json.load(open(p))['characters'].get('poet/red_black_sunglasses', {}) if os.path.exists(p) else {}
    return {k: (v or {}).get('canon') for k, v in (C.get('segments_cm') or {}).items()}


def proportion(kit):
    canon = canon_lengths()
    rat = {}
    for slot, p in kit.items():
        d = (p.get('rec') or {}).get('canon_deviation') or {}
        if d.get('length_cm') and canon.get(slot):
            rat[slot] = d['length_cm'] / canon[slot]
    if not rat:
        return {}, 0
    med = float(np.median(list(rat.values())))
    norm = {k: round(v / med, 3) for k, v in rat.items()}
    bad = [k for k, v in norm.items() if abs(v - 1) > PROP_TOL]
    return {'ratio_to_canon': {k: round(v, 3) for k, v in rat.items()}, 'kit_median': round(med, 3), 'normalised': norm, 'off': bad}, len(bad)


def search(view, rnd):
    t0 = time.time()
    M = {j: (method_for(j, rnd), L.load_methods(j)[method_for(j, rnd)]) for j in JOINTS}
    C = candidates(view)
    gaps = [s for s in ('torso', 'head', 'pelvis', 'upper_arm', 'forearm', 'hand', 'thigh', 'shin', 'foot') if not C.get(s)]
    graph = []

    def sc(joint, a, b, side=None):
        res = edge(joint, a, b, M, side)
        sp, rom = span(res, joint)
        ok = res.get(min(res, key=abs) if res else 0) == 'green'
        nat = native(a, b)
        graph.append({'joint': joint, 'parent': a['key'], 'child': b['key'], 'clean_at_0': bool(ok), 'clean_span_deg': sp, 'rom_deg': rom,
                      'native': nat, 'grades': {str(k): v for k, v in res.items()}})
        return (sp / rom + (.15 if nat else 0.)) if ok else None
    kits = []
    for T in C['torso']:
        heads = sorted([(s, H) for H in C['head'] for s in [sc('neck', T, H)] if s is not None], key=lambda x: -x[0])[:3]
        arms = []
        for U in C['upper_arm']:
            s1 = sc('shoulder', T, U, 'R')
            if s1 is None:
                continue
            for Fa in C['forearm']:
                s2 = sc('elbow', U, Fa)
                if s2 is None:
                    continue
                for A in C['hand']:
                    s3 = sc('wrist', Fa, A)
                    if s3 is not None:
                        arms.append((s1 + s2 + s3, U, Fa, A))
        arms = sorted(arms, key=lambda x: -x[0])[:3]
        pels = sorted([(s, P) for P in C['pelvis'] for s in [sc('waist', P, T)] if s is not None], key=lambda x: -x[0])[:3]
        legs = []
        for P in [p for _, p in pels]:
            for Th in C['thigh']:
                s1 = sc('hip', P, Th, 'R')
                if s1 is None:
                    continue
                for S in C['shin']:
                    s2 = sc('knee', Th, S)
                    if s2 is None:
                        continue
                    for Fo in C['foot']:
                        s3 = sc('ankle', S, Fo)
                        if s3 is not None:
                            legs.append((s1 + s2 + s3, P, Th, S, Fo))
        legs = sorted(legs, key=lambda x: -x[0])[:3]
        for (sh, H), (sa, U, Fa, A), (sl, P, Th, S, Fo) in itertools.product(heads or [(None, None)], arms or [(None,) * 4], legs or [(None,) * 5]):
            kit = {'torso': T, 'head': H, 'upper_arm': U, 'forearm': Fa, 'hand': A, 'pelvis': P, 'thigh': Th, 'shin': S, 'foot': Fo}
            missing = [k for k, v in kit.items() if v is None]
            kit = {k: v for k, v in kit.items() if v is not None}
            pr, nbad = proportion(kit)
            score = (sh or 0) + (sa or 0) + (sl or 0) + (next((s for s, p in pels if p is P), 0) if P is not None else 0) - nbad - 3 * len(missing)
            kits.append((score, kit, missing, pr))
    kits.sort(key=lambda x: -x[0])
    return kits, graph, M, C, gaps, time.time() - t0


# ------------------------------------------------------------------ rendering a kit
RS = CN.RS
ORDER_FRONT = ['thighR', 'thighL', 'shinR', 'shinL', 'footR', 'footL', 'pelvis', 'torso', 'head', 'upper_armR', 'upper_armL',
               'forearmR', 'forearmL', 'handR', 'handL']


def world(kit, M, pose, size=(900, 1300)):
    """forward kinematics with the evolved methods' placement (register / align genes); returns {node: (affine 2x3
    canonical -> canvas, part, mirrored)} and joint positions"""
    k = RS / 10.
    out, joints = {}, {}
    W, H = size
    P = kit['pelvis']
    Mp = np.array([[k, 0, W / 2 - P['pivot'][0] * k], [0, k, H * .42 - P['pivot'][1] * k]])
    out['pelvis'] = (Mp, P, False)

    def place(node, parent_node, joint, child, side):
        Mpar, par, mirp = out[parent_node]
        g = M[joint][1]
        pa = CN.anchor(par, joint, side)
        if pa is None:
            return
        J = Mpar[:, :2] @ pa + Mpar[:, 2]
        # base direction in the world: the parent's (actual or grid) axis through its own world rotation
        pax = {'torso': (0, -1), 'pelvis': (0, 1)}.get(par['part'], (0, 1))
        base = np.array([0, -1.]) if CN.J[joint][3] == 'up' else np.array([0, 1.]) if par['part'] in ('torso', 'pelvis') else np.array(pax, float)
        if g.get('align') and par['part'] not in ('torso', 'pelvis'):
            v = pa - par['pivot']
            if np.linalg.norm(v) > 20:
                base = v / np.linalg.norm(v)
        Rp = Mpar[:, :2] / k
        bw = Rp @ base
        caxis = np.array({'head': (0, -1), 'torso': (0, -1)}.get(child['part'], (0, 1)), float)
        if g.get('align'):
            ck = child['kp']
            dist = {'hand': ('knuckle_l', 'knuckle_r'), 'head': ('crown',), 'forearm': ('wrist', 'tip'), 'shin': ('ankle', 'tip'),
                    'upper_arm': ('elbow', 'tip'), 'thigh': ('knee', 'tip'), 'torso': ('neck',)}.get(child['part'], ())
            q = [np.asarray(ck[x], float) for x in dist if x in ck]
            if q:
                v = (sum(q) / len(q)) - child['pivot']
                if np.linalg.norm(v) > 20:
                    caxis = v / np.linalg.norm(v)
        mir = side == 'L'
        ang = pose.get(node, 0.)
        if mir:
            ang = -ang
        if child['part'] == 'foot':
            rot = math.radians(ang) * .5 + math.atan2(bw[1], bw[0]) - math.pi / 2
            if mir:
                pass
        else:
            ca = caxis * ([-1, 1] if mir else [1, 1])
            rot = math.atan2(bw[1], bw[0]) - math.atan2(ca[1], ca[0]) + math.radians(ang)
        R = np.array([[math.cos(rot), -math.sin(rot)], [math.sin(rot), math.cos(rot)]]) * k
        if mir:
            R = R @ np.array([[-1, 0], [0, 1.]])
        piv = np.asarray(child['pivot'], float)
        target = J
        if g.get('pivot') == 'register':
            gp = [b for b in par['brads'] if np.linalg.norm(b - pa) < 30]
            cb = [b for b in child['brads'] if np.linalg.norm(b - child['pivot']) < 30]
            if gp and cb:
                gp = min(gp, key=lambda b: np.linalg.norm(b - pa))
                cb = min(cb, key=lambda b: np.linalg.norm(b - child['pivot']))
                target, piv = Mpar[:, :2] @ gp + Mpar[:, 2], cb
        out[node] = (np.hstack([R, (target - R @ piv)[:, None]]), child, mir)
        joints[(joint, side or '')] = target
    place('torso', 'pelvis', 'waist', kit['torso'], None)
    place('head', 'torso', 'neck', kit['head'], None)
    for S in 'RL':
        place('upper_arm' + S, 'torso', 'shoulder', kit['upper_arm'], S)
        place('forearm' + S, 'upper_arm' + S, 'elbow', kit['forearm'], S)
        place('hand' + S, 'forearm' + S, 'wrist', kit['hand'], S)
        place('thigh' + S, 'pelvis', 'hip', kit['thigh'], S)
        place('shin' + S, 'thigh' + S, 'knee', kit['shin'], S)
        place('foot' + S, 'shin' + S, 'ankle', kit['foot'], S)
    return out, joints


def render(kit, M, pose, grades=None, size=(900, 1300)):
    W, H = size
    out, joints = world(kit, M, pose, size)
    acc = np.zeros((H, W, 4), np.float32)
    on_top = {j: M[j][1].get('on_top', 'child') for j in JOINTS}
    order = list(ORDER_FRONT)
    # children drawn under their parent where the joint's method puts the parent on top
    for j, (pp, cp) in CHAIN.items():
        if on_top[j] == 'parent':
            for S in ('', 'R', 'L'):
                c = cp + S if cp not in ('torso', 'head') else cp
                p = pp + S if pp not in ('torso', 'pelvis') else pp
                if c in order and p in order and order.index(c) > order.index(p):
                    order.remove(c); order.insert(order.index(p), c)
    for n in order:
        if n not in out:
            continue
        Mw, part, mir = out[n]
        lay = cv2.warpAffine(part['img'].astype(np.float32), Mw, (W, H), flags=cv2.INTER_LINEAR, borderValue=0)
        acc = CN.over(acc, lay)
    a = acc[..., 3:] / 255.
    o = (acc[..., [2, 1, 0]] * a + 245 * (1 - a)).astype(np.uint8)
    im = Image.fromarray(o)
    d = ImageDraw.Draw(im)
    for (j, S), p in joints.items():
        g = (grades or {}).get((j, S))
        if g:
            col = {'green': (40, 170, 60), 'amber': (235, 160, 20), 'red': (215, 40, 40)}[g]
            d.ellipse([p[0] - 14, p[1] - 14, p[0] + 14, p[1] + 14], outline=col, width=3)
    ys, xs = np.nonzero(acc[..., 3] > 10)
    if len(xs):
        im = im.crop((max(0, xs.min() - 30), max(0, ys.min() - 30), min(W, xs.max() + 30), min(H, ys.max() + 30)))
    return im


def pose_grades(kit, M, pose):
    """each seam's grade at this pose: the joint's pair verdict at the nearest swept angle"""
    out = {}
    for j, (pp, cp) in CHAIN.items():
        for S in (['R', 'L'] if j in ('shoulder', 'elbow', 'wrist', 'hip', 'knee', 'ankle') else ['']):
            node = cp + S if cp not in ('torso', 'head') else cp
            res = edge(j, kit[pp], kit[cp], M, S if j in ('shoulder', 'hip') else None)
            if not res:
                continue
            ang = pose.get(node, 0.)
            a0 = min(res, key=lambda a: abs(a - abs(ang) if j in ('elbow', 'knee') else abs(a - ang)))
            out[(j, S)] = res[a0]
    return out


def bend_chart(kit, M, path):
    rows = []
    for j, (pp, cp) in CHAIN.items():
        res = edge(j, kit[pp], kit[cp], M, 'R' if j in ('shoulder', 'hip') else None)
        rows.append((j, res))
    W, rh = 900, 34
    im = Image.new('RGB', (W, 40 + rh * len(rows)), (255, 255, 255))
    d = ImageDraw.Draw(im)
    d.text((10, 10), 'BENDABILITY: each joint\'s range of motion (grey) and its clean angles (green) / warn (amber) / mutilated (red)', fill=(28, 32, 38), font=F)
    lo_all, hi_all = -60, 180
    x = lambda a: 140 + (a - lo_all) / (hi_all - lo_all) * (W - 170)
    for i, (j, res) in enumerate(rows):
        y = 40 + i * rh
        d.text((10, y + 8), j, fill=(28, 32, 38), font=FB)
        if res:
            angs = sorted(res)
            d.rectangle([x(angs[0]), y + 8, x(angs[-1]), y + 22], fill=(225, 225, 225))
            for a in angs:
                col = {'green': (40, 170, 60), 'amber': (235, 160, 20), 'red': (215, 40, 40)}[res[a]]
                d.rectangle([x(a) - 6, y + 6, x(a) + 6, y + 24], fill=col)
            sp, rom = span(res, j)
            d.text((x(angs[-1]) + 12, y + 8), 'clean span %d of %d deg' % (sp, rom), fill=(95, 101, 112), font=FS)
    for a in range(-60, 181, 30):
        d.text((x(a) - 8, 40 + rh * len(rows) - 14), '%d' % a, fill=(150, 150, 150), font=FS)
    im.save(path, quality=88)


def parts_sheet(kit, M, path):
    cells = []
    for slot in ('head', 'torso', 'pelvis', 'upper_arm', 'forearm', 'hand', 'thigh', 'shin', 'foot'):
        p = kit.get(slot)
        if p is None:
            continue
        a = p['img'].astype(np.float32)
        al = a[..., 3:] / 255.
        o = (a[..., [2, 1, 0]] * al + 245 * (1 - al)).astype(np.uint8).copy()
        for gx in range(int(p['pivot'][0]) % 50, o.shape[1], 50):
            o[:, gx] = np.minimum(o[:, gx], 215)
        for gy in range(int(p['pivot'][1]) % 50, o.shape[0], 50):
            o[gy, :] = np.minimum(o[gy, :], 215)
        cv2.drawMarker(o, tuple(int(v) for v in p['pivot']), (220, 30, 30), cv2.MARKER_CROSS, 24, 3)
        im = Image.fromarray(o)
        im.thumbnail((240, 300))
        c = Image.new('RGB', (250, 360), (255, 255, 255))
        c.paste(im, (5, 5))
        d = ImageDraw.Draw(c)
        d.text((5, 310), slot.upper(), fill=(28, 32, 38), font=FB)
        d.text((5, 328), p['src_card'].split('/')[-1][:40], fill=(95, 101, 112), font=FS)
        js = [j for j, (pp, cp) in CHAIN.items() if slot in (pp, cp)]
        txt = []
        for j in js:
            pp, cp = CHAIN[j]
            res = edge(j, kit[pp], kit[cp], M, 'R' if j in ('shoulder', 'hip') else None)
            sp, rom = span(res, j)
            txt.append('%s %d/%d' % (j, sp, rom))
        d.text((5, 342), ' · '.join(txt)[:60], fill=(30, 110, 200), font=FS)
        cells.append(c)
    out = Image.new('RGB', (250 * 5, 360 * ((len(cells) + 4) // 5)), (255, 255, 255))
    for i, c in enumerate(cells):
        out.paste(c, ((i % 5) * 250, (i // 5) * 360))
    out.save(path, quality=86)


POSES = {'neutral': {}, 'arm raise (R shoulder 90)': {'upper_armR': 90.}, 'elbow bend (R 90)': {'forearmR': 90.},
         'knee bend (L hip 45, knee 75)': {'thighL': -45., 'shinL': 75.}, 'head +15': {'head': 15.}, 'head -15': {'head': -15.}}


def main():
    view = sys.argv[1] if len(sys.argv) > 1 else 'front'
    rnd = int(sys.argv[2]) if len(sys.argv) > 2 else 5
    od = os.path.join(HERE, 'kits', view)
    os.makedirs(od, exist_ok=True)
    kits, graph, M, C, gaps, secs = search(view, rnd)
    json.dump({'view': view, 'methods': {j: M[j][0] for j in M}, 'candidates': {k: [p['key'] for p in v] for k, v in C.items()},
               'edges': graph, 'seconds': round(secs, 1)}, open(os.path.join(od, 'graph.json'), 'w'), indent=1)
    if not kits:
        json.dump({'view': view, 'kit': None, 'gaps': gaps, 'why': 'no combination'}, open(os.path.join(od, 'kit.json'), 'w'), indent=1)
        print('no kit', gaps)
        return
    score, kit, missing, pr = kits[0]
    rep = {'view': view, 'score': round(score, 3), 'parts': {k: v['key'] for k, v in kit.items()}, 'missing_slots': missing,
           'gaps': gaps, 'proportion': pr, 'methods': {j: M[j][0] for j in M}, 'joints': {}}
    for j, (pp, cp) in CHAIN.items():
        if pp in kit and cp in kit:
            res = edge(j, kit[pp], kit[cp], M, 'R' if j in ('shoulder', 'hip') else None)
            sp, rom = span(res, j)
            rep['joints'][j] = {'clean_span_deg': sp, 'rom_deg': rom, 'native': native(kit[pp], kit[cp]), 'grades': {str(a): g for a, g in res.items()}}
    rep['runners_up'] = [{'score': round(s, 3), 'parts': {k: v['key'] for k, v in kt.items()}, 'missing': ms} for s, kt, ms, _ in kits[1:4]]
    json.dump(rep, open(os.path.join(od, 'kit.json'), 'w'), indent=1)
    if not missing:
        parts_sheet(kit, M, os.path.join(od, 'parts.jpg'))
        render(kit, M, {}, pose_grades(kit, M, {})).save(os.path.join(od, 'neutral.jpg'), quality=88)
        ims = []
        for name, pose in POSES.items():
            im = render(kit, M, pose, pose_grades(kit, M, pose))
            im.thumbnail((380, 560))
            c = Image.new('RGB', (390, 600), (255, 255, 255))
            c.paste(im, ((390 - im.width) // 2, 30))
            ImageDraw.Draw(c).text((8, 6), name, fill=(28, 32, 38), font=FB)
            ims.append(c)
        out = Image.new('RGB', (390 * len(ims), 600), (255, 255, 255))
        for i, c in enumerate(ims):
            out.paste(c, (i * 390, 0))
        out.save(os.path.join(od, 'bends.jpg'), quality=86)
        bend_chart(kit, M, os.path.join(od, 'bendability.jpg'))
    print(json.dumps({k: v for k, v in rep.items() if k != 'runners_up'}, indent=1)[:3000])


if __name__ == '__main__':
    main()
