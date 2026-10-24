"""Per-pair bendability (round 07, critic r06: background wedges open in the crook of large bends).

For each pair and method, the angle is swept over the joint's range (15 degree steps) and each render is checked for
background near the pivot:
  hull_bg   the coordinator's measure: background inside the convex hull of the union, within 1.2 x the joint width of
            the pivot, as a share of that hull. Straight (rest) joints already have 2-6% (limb tapers, the parent's
            narrower end), so a bend is clean when it adds at most 1 point to the pair's own rest value
  core_bg   background inside the disc the pair fills round its pivot at rest (0.9 x the distance from the pivot to the
            nearest background in the rest render) -- where a joint cut round about its brad has paper at any angle
            -- in cm2 (clean if <= 0.4 cm2)
  cut_bg    background within 1.2 x the joint width of the pivot where either card had paper before the method's
            cuts (tab / trim cuts that open a notch no piece covers), in cm2 (clean if <= 0.4 cm2)
A pair-angle is clean ('ok') when core_bg and cut_bg are clean and the under piece keeps >= 40% visible (cut_bg is
not counted at neck, wrist and ankle, where the method removes tabs and ears on purpose).
A pair's clean ROM is the run of clean angles containing the rest angle (the swept angle nearest 0).

    python3 -m evolve.joints.rom elbow,knee register,register_round      (from shots/scion2)
"""
import json, os, sys
import numpy as np, cv2
from evolve.joints import connect as CN, lab as L

HERE = os.path.dirname(os.path.abspath(__file__))
HULL_MAX, CORE_MAX = .01, .4


def core_radius(r):
    a = (r['img'][..., 3] > 128).astype(np.uint8)
    d = cv2.distanceTransform(a, cv2.DIST_L2, 3)
    c = r['target']
    return .9 * float(d[int(round(c[1])), int(round(c[0]))])


def wedge(r, rc):
    a = r['img'][..., 3] > 128
    c = r['target']
    w = max(r['joint_w'], 2 * CN.RS)
    H, W = a.shape
    yy, xx = np.mgrid[0:H, 0:W]
    d2 = (xx - c[0]) ** 2 + (yy - c[1]) ** 2
    disk = d2 <= (1.2 * w) ** 2
    pts = np.column_stack(np.nonzero(a & disk))[:, ::-1].astype(np.int32)
    if len(pts) < 3:
        return 1., 99., 99.
    hull = np.zeros_like(a, np.uint8)
    cv2.fillConvexPoly(hull, cv2.convexHull(pts), 1)
    hb = float((hull.astype(bool) & ~a).sum()) / max(1, hull.sum())
    core = float(((d2 <= rc ** 2) & ~a).sum()) / CN.RS ** 2
    cut = float((disk & ~a & (r['origP'] | r['origC'])).sum()) / CN.RS ** 2
    return hb, core, cut


def run_range(res, key):
    angs = sorted(res)
    if not angs:
        return None
    z = min(angs, key=abs)
    if not res[z][key]:
        return None
    i = lo = hi = angs.index(z)
    while lo > 0 and res[angs[lo - 1]][key]:
        lo -= 1
    while hi < len(angs) - 1 and res[angs[hi + 1]][key]:
        hi += 1
    return [angs[lo], angs[hi]]


def sweep(a, b, j, g, side=None):
    res = {}
    r0 = CN.connect(a, b, j, 0, g)
    if r0 is None:
        return res
    rc = core_radius(r0)
    h0 = wedge(r0, rc)[0]
    for ang in L.rom_angles(j):
        r = CN.connect(a, b, j, ang, g, side=side) if side else CN.connect(a, b, j, ang, g)
        if r is None:
            continue
        hb, core, cut = wedge(r, rc)
        res[ang] = {'hull_bg': round(hb, 4), 'core_cm2': round(core, 2), 'cut_cm2': round(cut, 2), 'cut_ok': bool(cut <= CORE_MAX), 'hull_ok': bool(hb <= h0 + HULL_MAX), 'core_ok': bool(core <= CORE_MAX),
                    'vis_ok': bool(r['vis_under'] >= .4)}
        # at the extremity joints the method cuts tabs and ears on purpose, so cut_bg is not counted there
        res[ang]['ok'] = res[ang]['core_ok'] and (res[ang]['cut_ok'] or j in ('neck', 'wrist', 'ankle')) and res[ang]['vis_ok']
    return res


def main():
    joints = sys.argv[1].split(',')
    methods = sys.argv[2].split(',') if len(sys.argv) > 2 else None
    out = {}
    for j in joints:
        M = L.load_methods(j)
        ms = [m for m in (methods or M) if m in M]
        for m in ms:
            rows = []
            for a, b, sp in L.pairs(j):
                res = sweep(a, b, j, M[m])
                rows.append({'parent': a['key'], 'child': b['key'], 'split': sp, 'core_rom': run_range(res, 'ok'),
                             'hull_rom': run_range(res, 'hull_ok'), 'angles': {str(k): v for k, v in res.items()}})
            out.setdefault(j, {})[m] = rows
            span = lambda r: (r[1] - r[0]) if r else -1
            cs = [span(x['core_rom']) for x in rows]
            hs = [span(x['hull_rom']) for x in rows]
            print('%-6s %-16s pairs %2d  core-clean ROM median %4.0f deg (none at rest: %d)   hull ROM median %4.0f deg (none: %d)' % (
                j, m, len(rows), np.median([c for c in cs if c >= 0] or [0]), sum(c < 0 for c in cs), np.median([h for h in hs if h >= 0] or [0]), sum(h < 0 for h in hs)), flush=True)
    od = os.path.join(HERE, 'rom')
    os.makedirs(od, exist_ok=True)
    for j in out:
        json.dump(out[j], open(os.path.join(od, '%s.json' % j), 'w'), indent=0)


if __name__ == '__main__':
    main()
