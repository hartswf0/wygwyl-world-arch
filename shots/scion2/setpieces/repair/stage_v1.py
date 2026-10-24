#!/usr/bin/env python3
"""Stage: compose WYGWYL scenes ONLY by querying the set-piece registry (no hand-picked file paths).

    cd shots/scion2/setpieces && python3 stage.py            # all three proof scenes -> proof/
    python3 stage.py rank                                     # poem richness table only

A scene is a toy theatre seen from the front (Toon Boom scene package / multiplane, flattened):
  far plane     a backdrop from the registry, cover-fitted behind everything (the one exemption from
                real size: it is "infinitely" far)
  mid plane     architecture / aperture flats standing on the back line (GROUND_TOP)
  ground plane  a ground card textured across the floor band GROUND_TOP..H
  near plane    furniture standing on depth lines between the back line and the front edge
  props         resting on a surface affordance of a placed piece (surface rest_y)
  actors        exposure-sheet players (studio/exposure.py method: whole paintings swapped on beats)
                standing on a depth line, seated on a seat line, or standing in a door opening
  occluders     overlays in front of actors (an armchair's front arm, a bar front)
One scale for everything that is real-size: PX_PER_CM = 2.4 px/cm (studio/core.py), the actors' scale.

Every piece comes from query.find(...); the call, its arguments, the ids it returned and why a
candidate was skipped are written to proof/<scene>.json. Sizes: the registry's size_cm is used when
it agrees with a real-world expectation for the thing (EXPECT); otherwise the expectation's typical
size is used and the override is recorded (registry sizes are sheet medians for many parts: viewed,
e.g. bentwood chairs at 44 cm, a bar front at 97 cm wide x 32 cm tall). Walls with a door opening are
scaled so the opening (measured from alpha) is a 205 cm door.

Measured per scene (proof/<scene>.json "checks"): contact lines off the ground plane, actor/furniture
scale ratio against the real-world expectation, occlusion-order violations (id buffer), and the
interaction errors (seat line, door threshold, counter occlusion, prop-on-surface).
"""
import json, math, os, sys, shutil, subprocess
import numpy as np, cv2

HERE = os.path.dirname(os.path.abspath(__file__))
SCION = os.path.dirname(HERE)
sys.path.insert(0, HERE)
sys.path.insert(0, SCION)
cv2.setNumThreads(1)

import query                                    # noqa: E402
from studio import exposure as ex, select as sel    # noqa: E402
from studio.core import PX_PER_CM              # noqa: E402

OUT = os.path.join(HERE, 'proof')
W, H, FPS = 1280, 720, 24
GROUND_TOP, FRONT = 590, 715          # back line (walls stand here) and front line of the floor band
FONT = cv2.FONT_HERSHEY_SIMPLEX
PLANE_RANK = {'far_backdrop': 0, 'ground_plane': 1, 'mid_set': 2, 'near_set': 3, 'foreground_occluder': 4,
              'overlay_fx': 5}


def line_y(d):
    """stage y of the depth line d (0 = back line where the walls stand, 1 = front edge)"""
    return GROUND_TOP + d * (FRONT - GROUND_TOP)


# ------------------------------------------------------------------ real-world expectations (inferred)
# (keywords, dimension, lo, typical, hi) in cm. First match wins, so specific words come first.
EXPECT = [
    (('armchair', 'wing chair'), 'h', 85, 95, 110),
    (('sofa', 'couch'), 'h', 70, 85, 100),
    (('chair',), 'h', 80, 88, 100),
    (('pew',), 'h', 80, 95, 110),
    (('bench',), 'h', 40, 50, 95),
    (('bar front', 'homebar', 'counter'), 'h', 95, 105, 120),
    (('side table', 'table'), 'h', 55, 72, 80),
    (('bottle',), 'h', 20, 30, 35),
    (('receiver', 'handset'), 'h', 17, 21, 24),
    (('phone base', 'telephone', 'rotary'), 'w', 18, 23, 28),
    (('cup', 'mug'), 'h', 7, 9, 12),
    (('saucer',), 'w', 12, 14, 17),
    (('wall', 'facade'), 'h', 240, 280, 320),
    (('door',), 'h', 195, 205, 215),
    (('window',), 'h', 80, 120, 160),
    (('lamp',), 'h', 120, 150, 175),
    (('television', ' tv '), 'w', 50, 70, 110),
]
DOOR_CM = 205.0
ACTOR_CM = {'poet': 183, 'vintage man': 177, 'vintage woman': 166}


def words_of(rec):
    return ' ' + ' '.join([rec['id'].split('/')[-1], rec.get('label') or '', rec.get('name') or '']).lower() \
        .replace('-', ' ').replace('_', ' ') + ' '


def expect_of(rec):
    w = words_of(rec)
    for kws, dim, lo, typ, hi in EXPECT:
        for k in kws:
            if k in w:
                return {'keyword': k.strip(), 'dim': dim, 'lo': lo, 'typ': typ, 'hi': hi}
    return None


_IMG = {}


def image(rec):
    """BGRA cut-out (cached) and its alpha bbox (x, y, w, h), measured at alpha > 40"""
    if rec['id'] not in _IMG:
        im = cv2.imread(query.path(rec), cv2.IMREAD_UNCHANGED)
        if im.shape[2] == 3:
            im = np.dstack([im, np.full(im.shape[:2], 255, np.uint8)])
        a = im[..., 3] > 40
        ys, xs = np.nonzero(a)
        _IMG[rec['id']] = (im, (int(xs.min()), int(ys.min()), int(xs.max() - xs.min() + 1), int(ys.max() - ys.min() + 1)))
    return _IMG[rec['id']]


def openings(rec):
    """transparent holes in a flat, measured from alpha: a transparent pixel with paint to its left, its
    right and above it (inside the alpha bbox). -> [{rect [x,y,w,h], open_bottom, area}] largest first"""
    im, (bx, by, bw, bh) = image(rec)
    a = im[by:by + bh, bx:bx + bw, 3] > 40
    left = np.maximum.accumulate(a, axis=1)
    right = np.maximum.accumulate(a[:, ::-1], axis=1)[:, ::-1]
    above = np.maximum.accumulate(a, axis=0)
    hole = (~a) & left & right & above
    n, lab, st, _ = cv2.connectedComponentsWithStats(hole.astype(np.uint8), 8)
    out = []
    for i in range(1, n):
        x, y, w, h, ar = st[i]
        if ar < 0.01 * bw * bh or w < 0.05 * bw or h < 0.15 * bh:
            continue
        out.append({'rect': [int(x + bx), int(y + by), int(w), int(h)], 'open_bottom': bool(y + h >= bh - 2),
                    'area': int(ar), 'fill': round(float(ar) / (w * h), 2)})
    return sorted(out, key=lambda o: -o['area'])


def door_opening(rec):
    """the largest measured opening that reaches the bottom and is door-shaped (taller than wide)"""
    for o in openings(rec):
        x, y, w, h = o['rect']
        if o['open_bottom'] and h > 1.3 * w:
            return o
    return None


def resolve_scale(rec, prefer_door=True):
    """stage px per part px, with where it came from. Returns dict or None (not placeable at real size)."""
    im, (bx, by, bw, bh) = image(rec)
    reg = rec.get('size_cm') or {}
    ev = {'registry_size_cm': reg or None, 'registry_scale_src': rec.get('scale_src'), 'flags': rec['flags'],
          'alpha_bbox_px': [bw, bh]}
    if prefer_door:
        door = door_opening(rec)
        if door:
            k = DOOR_CM * PX_PER_CM / door['rect'][3]
            return dict(ev, k=k, src='door_opening_measured', cm={'h': round(bh * k / PX_PER_CM, 1), 'w': round(bw * k / PX_PER_CM, 1)},
                        opening=door, basis='measured opening, 205 cm door (inferred)')
    e = expect_of(rec)
    if e:
        rv = reg.get(e['dim'])
        ok = rv is not None and e['lo'] <= rv <= e['hi'] and 'size_doubt' not in rec['flags']
        val = rv if ok else e['typ']
        px = bh if e['dim'] == 'h' else bw
        k = val * PX_PER_CM / px
        return dict(ev, k=k, src='registry' if ok else 'expectation_override', expect=e,
                    cm={'h': round(bh * k / PX_PER_CM, 1), 'w': round(bw * k / PX_PER_CM, 1)},
                    basis='registry size within expected range' if ok else
                    f"registry {e['dim']}={rv} outside {e['lo']}-{e['hi']} cm or size_doubt; typical {e['typ']} cm used (inferred)")
    if reg and 'size_doubt' not in rec['flags']:
        m = max(reg.get('h') or 0, reg.get('w') or 0)
        k = m * PX_PER_CM / max(bw, bh)
        return dict(ev, k=k, src='registry_unchecked', cm={'h': round(bh * k / PX_PER_CM, 1), 'w': round(bw * k / PX_PER_CM, 1)},
                    basis='registry size, no expectation known for this thing')
    return None


# ------------------------------------------------------------------ poem richness (measured on the registry)
def roles():
    def aff(r, k, c=0.0):
        return any(a['kind'] == k and a['confidence'] >= c for a in r['affordances'])

    def sized(r):
        return resolve_scale(r, prefer_door=False) is not None or (r['category'] == 'aperture' and door_opening(r))
    return {
        'far_backdrop': lambda r: r['plane'] == 'far_backdrop' and r['category'] == 'backdrop',
        'ground': lambda r: r['category'] == 'ground' and r['plane'] == 'ground_plane',
        'wall/flat': lambda r: r['category'] in ('architecture', 'aperture') and r['plane'] == 'mid_set' and sized(r),
        'seat': lambda r: r['category'] == 'furniture-seat' and aff(r, 'seat', 0.6) and sized(r),
        'surface': lambda r: aff(r, 'surface', 0.6) and r['category'] in ('furniture-surface', 'architecture', 'other') and sized(r),
        'door/aperture': lambda r: r['category'] == 'aperture' and aff(r, 'aperture', 0.6),
        'grip prop': lambda r: r['category'] == 'handheld-prop' and aff(r, 'grip', 0.6) and sized(r),
        'occluder': lambda r: r['plane'] == 'foreground_occluder' or aff(r, 'occluder', 0.8),
    }


def richness():
    """per poem: usable best-copy pieces per staging role (each role capped at 5, so a poem must cover
    many roles to rank high); the tie-break is the total. Pieces are counted under every poem of their sheet."""
    R = roles()
    by = {}
    for r in query.find(min_grade='B'):
        for p in r['poems']:
            c = by.setdefault(p, {k: 0 for k in R})
            for k, f in R.items():
                if f(r):
                    c[k] += 1
    rows = [{'poem': p, 'score': sum(min(v, 5) for v in c.values()), 'total': sum(c.values()), 'roles': c} for p, c in by.items()]
    return sorted(rows, key=lambda r: (-r['score'], -r['total']))


# ------------------------------------------------------------------ querying with a record
class Book:
    """every query a scene makes, what it returned and what was taken"""

    def __init__(self):
        self.log = []

    def find(self, role, pick=None, n=1, **kw):
        res = query.find(**kw)
        entry = {'role': role, 'query': {k: v for k, v in kw.items()}, 'returned': [r['id'] for r in res[:15]],
                 'returned_count': len(res), 'chosen': [], 'skipped': []}
        out = []
        for r in res:
            ok, why = pick(r) if pick else (True, '')
            if ok:
                out.append(r)
                entry['chosen'].append({'id': r['id'], 'why': why})
                if len(out) >= n:
                    break
            elif len(entry['skipped']) < 15:
                entry['skipped'].append({'id': r['id'], 'why': why})
        self.log.append(entry)
        if not out:
            raise RuntimeError(f'query for {role} found nothing usable: {kw}')
        return out if n > 1 else out[0]


def need_size(r):
    s = resolve_scale(r, prefer_door=False)
    return (s is not None, 'real size: ' + (s['src'] if s else 'none'))


def need_door(r):
    o = door_opening(r)
    return (o is not None, f"door opening measured {o['rect']}" if o else 'no door-shaped opening at the bottom (measured)')


def need_window(r):
    o = [x for x in openings(r) if not x['open_bottom']]
    return (bool(o), f"window opening measured {o[0]['rect']}" if o else 'no enclosed opening (measured)')


def all_of(*fs):
    def f(r):
        whys = []
        for g in fs:
            ok, why = g(r)
            whys.append(why)
            if not ok:
                return False, '; '.join(whys)
        return True, '; '.join(whys)
    return f


def no_flags(*fl):
    return lambda r: (not (set(fl) & set(r['flags'])), 'flags ' + ','.join(r['flags']) if r['flags'] else 'no flags')


# ------------------------------------------------------------------ elements
class El:
    """one placed layer. layer: full-frame BGRA uint8 (static) or None for actors"""

    def __init__(self, eid, kind, z, layer=None, **info):
        self.id, self.kind, self.z, self.layer = eid, kind, z, layer
        self.info = info


def warp(img, k, tx, ty, mirror=False, ky=None):
    if mirror:
        img = img[:, ::-1]
    ky = k if ky is None else ky
    M = np.array([[k, 0, tx], [0, ky, ty]], np.float32)
    return cv2.warpAffine(img, M, (W, H), flags=cv2.INTER_AREA if k < 1 else cv2.INTER_CUBIC,
                          borderMode=cv2.BORDER_CONSTANT, borderValue=(0, 0, 0, 0))


class Placed:
    """a registry piece placed at real size: maps part px -> stage px"""

    def __init__(self, rec, k, tx, ty, mirror=False):
        self.rec, self.k, self.tx, self.ty, self.mirror = rec, k, tx, ty, mirror
        self.pw = image(rec)[0].shape[1]

    def pt(self, x, y):
        if self.mirror:
            x = self.pw - 1 - x
        return (self.tx + self.k * x, self.ty + self.k * y)

    def rect(self, r):
        x0, y0 = self.pt(r[0], r[1])
        x1, y1 = self.pt(r[0] + r[2], r[1] + r[3])
        return [min(x0, x1), y0, abs(x1 - x0), y1 - y0]


class Stage:
    def __init__(self, name, poem):
        self.name, self.poem = name, poem
        self.book = Book()
        self.els = []
        self.actors = []
        self.constraints = []        # (front id, back id, why)
        self.interactions = []

    # ---- far plane
    def backdrop(self, rec):
        im, (bx, by, bw, bh) = image(rec)
        crop = im[by:by + bh, bx:bx + bw]
        k = max(W / bw, (GROUND_TOP + 60) / bh)
        tx = (W - bw * k) / 2
        ty = GROUND_TOP + 60 - bh * k
        self.els.append(El(rec['id'], 'backdrop', -10, warp(crop, k, tx, ty), plane='far_backdrop', k=round(k, 3),
                           scale_src='cover-fit (far plane exempt from real size)'))

    # ---- ground plane
    def ground(self, rec):
        im, (bx, by, bw, bh) = image(rec)
        crop = im[by:by + bh, bx:bx + bw]
        # keep the fully painted inner rectangle (measured): perspective strips have transparent corners
        a = crop[..., 3] > 200
        r0, r1, c0, c1 = 0, a.shape[0], 0, a.shape[1]
        for _ in range(3):
            cols = np.nonzero(a[r0:r1].mean(0) >= 0.98)[0]
            if len(cols):
                c0, c1 = cols.min(), cols.max() + 1
            rows = np.nonzero(a[:, c0:c1].mean(1) >= 0.98)[0]
            if len(rows):
                r0, r1 = rows.min(), rows.max() + 1
        inner = [int(c0), int(r0), int(c1 - c0), int(r1 - r0)]
        if inner[2] > 0.3 * bw and inner[3] > 0.3 * bh:
            # also trim the painted card border (viewed: it showed as vertical seams when mirror-tiled)
            mx, my = int(0.03 * inner[2]), int(0.04 * inner[3])
            crop = crop[r0 + my:r1 - my, c0 + mx:c1 - mx]
            bw, bh = crop.shape[1], crop.shape[0]
            inner = [int(c0 + mx), int(r0 + my), int(bw), int(bh)]
        band = H - GROUND_TOP + 6
        k = band / bh
        tile = cv2.resize(crop, (max(1, int(round(bw * k))), band), interpolation=cv2.INTER_AREA)
        tile[..., 3] = 255
        row = []
        i = 0
        while sum(t.shape[1] for t in row) < W:
            row.append(tile if i % 2 == 0 else tile[:, ::-1])      # mirror-repeat hides the seam
            i += 1
        strip = np.hstack(row)[:, :W]
        lay = np.zeros((H, W, 4), np.uint8)
        lay[GROUND_TOP - 6:] = strip
        self.els.append(El(rec['id'], 'ground', -5, lay, plane='ground_plane', k=round(k, 3), tiles=i, inner_rect_px=inner,
                           scale_src='fit to floor band, mirror-tiled (inferred: ground cards are foreshortened textures)'))

    # ---- real-size pieces
    def piece(self, rec, x, d, role, mirror=False, k=None, scale=None, z=None, line=None, anchor='center'):
        """stand the piece on depth line d (its contact y on line_y(d)), x = its centre (or left/right edge)"""
        im, (bx, by, bw, bh) = image(rec)
        sc = scale or resolve_scale(rec)
        k = k or sc['k']
        c = rec.get('contact') or {}
        cy_reg = c.get('y_px')
        cy_meas = by + bh - 1
        # contact row: the registry's, unless the measured alpha bottom disagrees by more than 3% of height
        cy = cy_reg if cy_reg is not None and abs(cy_reg - cy_meas) <= 0.03 * bh else cy_meas
        cy_src = 'registry' if cy == cy_reg else 'alpha_bottom'
        if rec['category'] in ('architecture', 'aperture') and rec['plane'] == 'mid_set' and d >= 0:
            # flats: the floor line is the median of the per-column painted bottoms (measured). A painted
            # perspective floor corner reaching lower at one end would otherwise lift the whole wall.
            al = im[by:by + bh, bx:bx + bw, 3] > 40
            colb = [by + np.nonzero(al[:, x])[0].max() for x in range(bw) if al[:, x].any()]
            cmed = float(np.median(colb))
            if abs(cmed - cy) > 0.03 * bh:
                cy, cy_src = cmed, 'column_median'
        yl = line_y(d) if line is None else line
        ty = yl - k * cy
        cx = bx + bw / 2
        if mirror:
            cx = im.shape[1] - 1 - cx
        if anchor == 'left':
            tx = x - k * (im.shape[1] - 1 - (bx + bw) if mirror else bx)
        elif anchor == 'right':
            tx = x - k * ((im.shape[1] - 1 - bx) if mirror else (bx + bw))
        else:
            tx = x - k * cx
        P = Placed(rec, k, tx, ty, mirror)
        lay = warp(im, k, tx, ty, mirror)
        if d < 0 and line is None:
            # upstage of the back line: nothing of it can show on the floor in front of the walls
            lay[int(GROUND_TOP):, :, 3] = 0
        e = El(rec['id'], 'piece', d if z is None else z, lay, role=role, plane=rec['plane'], category=rec['category'],
               d=d, line_y=round(yl, 1), k=round(k, 4), scale=sc, contact_y_px={'registry': cy_reg, 'measured_alpha_bottom': cy_meas, 'used': cy, 'src': cy_src},
               contact_type=c.get('type'), mirror=mirror, placed=P,
               stage_bbox=[round(tx + k * (bx if not mirror else im.shape[1] - 1 - bx - bw)), round(ty + k * by), round(k * bw), round(k * bh)])
        self.els.append(e)
        return e

    def on_surface(self, prop, support, u, role, d_off=0.0005):
        """rest a prop on the support's surface affordance at fraction u of the surface x_range"""
        sa = next(a for a in support.info['placed'].rec['affordances'] if a['kind'] == 'surface')
        g = sa['geometry']
        P = support.info['placed']
        ry = g.get('rest_y', g['surface_y'])
        x0, x1 = g['x_range']
        sx, sy = P.pt(x0 + u * (x1 - x0), ry)
        e = self.piece(prop, sx, support.info['d'], role, line=sy, z=support.z + d_off)
        e.info.update(rests_on=support.id, surface={'affordance_conf': sa['confidence'], 'rest_y_px': ry, 'stage_y': round(sy, 1),
                                                     'x_range_stage': [round(P.pt(x0, ry)[0]), round(P.pt(x1, ry)[0])]})
        e.kind = 'prop'
        self.constraints.append((e.id, support.id, 'prop drawn over the surface it rests on'))
        return e

    def actor(self, cast, sheet, x_cm, d, name, facing_note=''):
        A = StageActor(self, cast, sheet, x_cm, d, name)
        self.actors.append(A)
        return A

    # ---- rendering
    def static_sorted(self):
        return sorted(self.els, key=lambda e: e.z)

    def frame(self, f, want_ids=False):
        items = [(e.z, e.id, e.layer, e) for e in self.els]
        recs = {}
        for A in self.actors:
            lay, rec = A.layer(f)
            recs[A.name] = rec
            if lay is not None:
                items.append((rec['z'], A.name, lay, A))
        items.sort(key=lambda t: t[0])
        out = np.zeros((H, W, 3), np.float32)
        out[:] = (200, 205, 210)
        ids = np.full((H, W), -1, np.int16) if want_ids else None
        for i, (z, eid, lay, obj) in enumerate(items):
            a = lay[..., 3:4].astype(np.float32) / 255.
            out = lay[..., :3].astype(np.float32) * a + out * (1 - a)
            if want_ids:
                ids[lay[..., 3] > 127] = i
        return out.astype(np.uint8), recs, (items, ids)


class StageActor:
    """an exposure-sheet player on the stage. Beats: {'d': drawing key ('id' or 'view:<v>/<cls>', '~' mirrors),
    'hold', 'move_cm', 'bob', 'bob_period', 'settle', 'name', and where it stands:
    'depth' (depth line), 'seat' (an element with a seat affordance), 'door' (a wall element with an opening)}"""

    def __init__(self, stage, cast, sheet, x_cm, d, name):
        self.st, self.c, self.sheet, self.name = stage, cast, sheet, name
        self.cx = x_cm * PX_PER_CM
        self.d0 = d
        self.frames = [(b, i) for b in sheet for i in range(b['hold'])]
        self.cache = {}

    def __len__(self):
        return len(self.frames)

    @staticmethod
    def seat_point(d, img, mir):
        """the drawing's sitting point: x at the pelvis marker, y the underside of the buttocks, measured as
        the median lowest painted row in the columns between the back hip and the pelvis"""
        a = img[..., 3] > 40
        m = d.m
        g = m['groin'].copy()
        hx = [m[k][0] for k in ('hipR', 'hipL') if k in m] + [g[0]]
        if mir:
            g[0] = d.w - g[0]
            hx = [d.w - x for x in hx]
        x0, x1 = (int(min(hx)), int(g[0])) if not mir else (int(g[0]), int(max(hx)))
        bots = []
        for x in range(max(0, x0), min(a.shape[1], x1 + 1)):
            col = a[int(g[1]):, x]
            run = np.argmin(col) if not col.all() else len(col)
            bots.append(g[1] + run)
        return float(g[0]), float(np.median(bots)), (x0, x1)

    def layer(self, f):
        f = min(f, len(self.frames) - 1)
        b, i = self.frames[f]
        d, mir = self.c.get(b['d'])
        rec = {'actor': self.name, 'beat': b.get('name') or b['d'], 'drawing': d.id if d else None, 'mirror': mir,
               'swap': i == 0, 'cls': d.cls if d else None}
        if d is None:
            rec['gap'] = True
            rec['z'] = 0
            return None, rec
        if 'move_cm' in b and i > 0:
            self.cx += b['move_cm'] * PX_PER_CM / b['hold']
        if 'x_cm' in b and i == 0:
            self.cx = b['x_cm'] * PX_PER_CM
        img = d.image()
        if mir:
            img = img[:, ::-1]
        s = ex.scale_of(self.c, d)
        a = img[..., 3] > 40
        rows = np.nonzero(a.any(1))[0]
        low = rows.max()
        # height guard (measured): a standing painting whose marker-based scale puts the actor more than
        # 6% off his nominal height has bad leg/torso markers (the stand drawings used here with a raised
        # hand measure within 1%, so the raised hand does not trip it); it is rescaled to the nominal height
        guard = None
        if d.cls == 'stand':
            h_cm = (rows.max() - rows.min()) * s / PX_PER_CM
            if abs(h_cm / self.c.height_cm - 1) > 0.06:
                guard = {'marker_scale_height_cm': round(float(h_cm), 1), 'rescaled_to_cm': self.c.height_cm}
                s *= self.c.height_cm / h_cm
        gx = d.m['groin'][0] if not mir else d.w - d.m['groin'][0]
        dip = [3, 1.5][i] if b.get('settle', True) and i < 2 else 0.
        bob = b.get('bob', 0.) * abs(math.sin(math.pi * i / max(1, b.get('bob_period', 6))))
        if 'seat' in b:
            seat_el = b['seat']
            g = next(x for x in seat_el.info['placed'].rec['affordances'] if x['kind'] == 'seat')['geometry']
            P = seat_el.info['placed']
            sx0, sy = P.pt(g['x_range'][0], g['seat_y'])
            sx1, _ = P.pt(g['x_range'][1], g['seat_y'])
            u = b.get('seat_u', 0.45)
            target_x = min(sx0, sx1) + u * abs(sx1 - sx0)
            px, py, cols = self.seat_point(d, img, mir)
            self.cx = target_x
            tx = target_x - s * px
            ty = sy - s * py + dip
            z = seat_el.z + 0.001
            rec.update(anchor='seat', seat_line_y=round(sy, 1), seat_point_px=[round(px, 1), round(py, 1)], seat_el=seat_el.id,
                       planned_line=sy)
        else:
            dd = b.get('depth', self.d0)
            yl = line_y(dd)
            tx = self.cx - s * gx
            ty = yl - s * low + dip - bob
            z = b.get('z', dd)
            rec.update(anchor='door' if 'door' in b else 'floor', planned_line=yl, depth=dd)
        key = (d.id, mir, round(tx, 2), round(ty, 2), round(s, 5))
        lay = warp(img, s, tx, ty)
        ys, xs = np.nonzero(lay[..., 3] > 40)
        if guard:
            rec['height_guard'] = guard
        rec.update(z=z, scale=round(float(s), 4), centre_px=round(float(self.cx), 1), dip=dip, bob=round(bob, 2),
                   bbox=[int(xs.min()), int(ys.min()), int(xs.max() - xs.min() + 1), int(ys.max() - ys.min() + 1)] if len(xs) else None,
                   low_px=float(ys.max()) if len(ys) else None,
                   height_cm=round(float((ys.max() - ys.min()) / PX_PER_CM), 1) if len(ys) else None,
                   seat_cols=None)
        if 'seat' in b:
            # measured on the rendered layer: lowest painted row in the buttock columns
            c0 = int(tx + s * rec['seat_point_px'][0]) - 6
            colb = []
            al = lay[..., 3] > 40
            for x in range(c0 - 10, c0 + 4):
                if 0 <= x < W and al[:, x].any():
                    yy = np.nonzero(al[:int(rec['seat_line_y']) + 40, x])[0]
                    if len(yy):
                        colb.append(yy.max())
            rec['seat_err_px'] = round(float(np.median(colb) - rec['seat_line_y']), 1) if colb else None
            rec['feet_low_px'] = rec['low_px']
        return lay, rec


# ------------------------------------------------------------------ checks
def check_scene(stg, samples):
    out = {'contact': [], 'scale': [], 'occlusion': {}, 'interactions': []}
    # 1. contact lines: every standing piece on the ground band, measured alpha bottom on its planned line
    for e in stg.els:
        if e.kind not in ('piece', 'prop'):
            continue
        lay = e.layer
        ys = np.nonzero((lay[..., 3] > 40).any(1))[0]
        bottom = int(ys.max()) if len(ys) else None
        planned = e.info['line_y']
        cropped = bottom is not None and bottom >= H - 1 and planned >= H - 1
        if e.kind == 'prop':
            on = 'surface ' + e.info['rests_on']
            off = False
        else:
            on = 'ground band' if GROUND_TOP - 12 <= planned <= H else 'OFF the ground plane'
            off = on.startswith('OFF')
            if off and e.info.get('role') == 'behind-flat':
                on = 'behind the back line by design (seen only through an opening; its own painted floor shows)'
        if e.info.get('contact_y_px', {}).get('src') == 'column_median' and bottom is not None:
            al = lay[..., 3] > 40
            cols = [np.nonzero(al[:, x])[0].max() for x in range(W) if al[:, x].any()]
            bottom = int(np.median(cols))
        err = None if bottom is None or cropped else bottom - planned
        out['contact'].append({'id': e.id, 'role': e.info['role'], 'planned_line_y': planned, 'measured_bottom_y': bottom,
                               'err_px': None if err is None else round(err, 1), 'on': on, 'off_ground': off,
                               'contact_type': e.info.get('contact_type'),
                               'floating_or_sunk': bool(err is not None and abs(err) > 3)})
    # actors: every frame, feet on their planned line (floor/door) or the seat
    for A in stg.actors:
        errs, seat_errs = [], []
        for f in range(len(A)):
            r = samples['recs'][f][A.name]
            if r.get('gap'):
                continue
            if r['anchor'] == 'seat':
                if r.get('seat_err_px') is not None:
                    seat_errs.append(r['seat_err_px'])
            else:
                errs.append(r['low_px'] - (r['planned_line'] + r['dip'] - r['bob']))
        out['contact'].append({'id': 'actor:' + A.name, 'role': 'actor', 'feet_line_err_px_max': round(float(np.max(np.abs(errs))), 2) if errs else None,
                               'seat_err_px_median': round(float(np.median(seat_errs)), 1) if seat_errs else None,
                               'off_ground': any(samples['recs'][f][A.name].get('anchor') != 'seat' and
                                                 not (GROUND_TOP - 12 <= samples['recs'][f][A.name].get('planned_line', GROUND_TOP) <= H) for f in range(len(A)))})
    # 2. scale: actor standing height vs each real-size furniture/flat, against the expectation
    for A in stg.actors:
        hs = [samples['recs'][f][A.name]['height_cm'] for f in range(len(A))
              if samples['recs'][f][A.name].get('cls') == 'stand' and samples['recs'][f][A.name].get('height_cm')]
        if not hs:
            hs = [samples['recs'][f][A.name]['height_cm'] for f in range(len(A)) if samples['recs'][f][A.name].get('height_cm')
                  and samples['recs'][f][A.name].get('anchor') != 'seat']
        act_cm = float(np.median(hs)) if hs else None
        for e in stg.els:
            if e.kind not in ('piece', 'prop'):
                continue
            ex_ = expect_of(e.info['placed'].rec)
            sc = e.info['scale']
            if not ex_ and sc.get('src') != 'door_opening_measured':
                continue
            if ex_ and ex_['typ'] < 50:          # actor vs a bottle says little; furniture and flats only
                continue
            if sc.get('src') == 'door_opening_measured':
                o = sc['opening']['rect']
                meas_cm = o[3] * e.info['k'] / PX_PER_CM
                exp_cm, what = DOOR_CM, 'door opening h'
            else:
                bb = e.info['stage_bbox']
                meas_cm = (bb[3] if ex_['dim'] == 'h' else bb[2]) / PX_PER_CM
                exp_cm, what = ex_['typ'], f"{ex_['keyword']} {ex_['dim']}"
            reg = sc.get('registry_size_cm') or {}
            dim = 'h' if what.endswith(' h') else 'w'
            reg_v = reg.get(dim)
            row = {'actor': A.name, 'actor_height_cm_measured': act_cm, 'actor_height_cm_nominal': ACTOR_CM.get(A.name),
                   'piece': e.id, 'what': what, 'piece_cm_rendered': round(meas_cm, 1), 'expected_cm': exp_cm,
                   'ratio_rendered': round(act_cm / meas_cm, 3) if act_cm else None,
                   'ratio_expected': round(ACTOR_CM.get(A.name, act_cm or 1) / exp_cm, 3),
                   'scale_src': sc.get('src')}
            if row['ratio_rendered']:
                row['rendered_over_expected'] = round(row['ratio_rendered'] / row['ratio_expected'], 3)
            if reg_v and sc.get('src') == 'expectation_override':
                row['if_registry_size_trusted'] = {'piece_cm': reg_v, 'rendered_over_expected': round((act_cm / reg_v) / row['ratio_expected'], 3) if act_cm else None}
            out['scale'].append(row)
    # 3. occlusion order: on sampled frames, constraints that say which layer must cover which
    viol = {}
    checked = {}
    for f, (items, ids) in samples['ids'].items():
        idx = {it[1]: n for n, it in enumerate(items)}
        cons = list(stg.constraints)
        # toy-theatre depth rule: of two floor-standing things that overlap, the one standing lower
        # (downstage) must be drawn in front. Props, overlays, backdrop and ground are left out.
        floor_things = []
        for n, (z, eid, lay, obj) in enumerate(items):
            if isinstance(obj, El) and obj.kind == 'piece' and obj.info.get('role') not in ('overlay',):
                floor_things.append((eid, obj.info['line_y'], lay))
            elif isinstance(obj, StageActor):
                r = samples['recs'][f][eid]
                floor_things.append((eid, r['planned_line'] if r['anchor'] != 'seat' else None, lay))
        for a in floor_things:
            for b in floor_things:
                if a[0] == b[0] or a[1] is None or b[1] is None or a[1] - b[1] < 4:
                    continue
                cons.append((a[0], b[0], 'downstage (lower contact line %.0f > %.0f) in front' % (a[1], b[1])))
        # plane rule from the registry (near_set over mid_set etc.) for pieces
        for n1, it1 in enumerate(items):
            for n2, it2 in enumerate(items):
                o1, o2 = it1[3], it2[3]
                if isinstance(o1, El) and isinstance(o2, El) and o1.kind == 'piece' and o2.kind == 'piece':
                    p1, p2 = PLANE_RANK.get(o1.info['plane'], 2), PLANE_RANK.get(o2.info['plane'], 2)
                    if p1 > p2 and o1.info.get('role') != 'behind-flat':
                        cons.append((o1.id, o2.id, f"registry plane {o1.info['plane']} over {o2.info['plane']}"))
        for con in cons:
            fr, bk, why = con[:3]
            if len(con) > 3 and not con[3](samples['recs'][f]):
                continue
            if fr not in idx or bk not in idx:
                continue
            la, lb = items[idx[fr]][2], items[idx[bk]][2]
            both = (la[..., 3] > 127) & (lb[..., 3] > 127)
            nb = int(both.sum())
            key = f'{fr} > {bk}'
            c = checked.setdefault(key, {'front': fr, 'back': bk, 'why': why, 'overlap_px': 0, 'violating_px': 0, 'frames': 0})
            c['frames'] += 1
            c['overlap_px'] = max(c['overlap_px'], nb)
            if nb:
                bad = int((both & (ids == idx[bk])).sum())
                c['violating_px'] = max(c['violating_px'], bad)
    out['occlusion'] = {'constraints_checked': len(checked),
                        'constraints_with_overlap': sum(1 for c in checked.values() if c['overlap_px']),
                        'violations': [c for c in checked.values() if c['violating_px'] > 20],
                        'all': list(checked.values())}
    return out


# ------------------------------------------------------------------ output
def encode(d, mp4):
    subprocess.run(['ffmpeg', '-y', '-loglevel', 'error', '-framerate', str(FPS), '-i', os.path.join(d, '%04d.jpg'),
                    '-c:v', 'libx264', '-pix_fmt', 'yuv420p', '-crf', '20', '-movflags', '+faststart', mp4], check=True)


def layer_diagram(stg, f, recs, items, path):
    """left: side view (depth vs height in cm); right: exploded layers in draw order"""
    L = np.full((900, 700, 3), 250, np.uint8)
    cv2.putText(L, f'{stg.name}: side view (depth line -> height, cm)', (16, 28), FONT, 0.55, (0, 0, 0), 1, cv2.LINE_AA)
    base = 820
    dx = lambda d: int(80 + (d + 0.35) / 1.45 * 560)
    hy = lambda cm: int(base - cm * 1.9)
    cv2.line(L, (40, base), (680, base), (90, 90, 90), 2)
    for dd, lab in ((0, 'back line (walls)'), (1, 'front edge')):
        cv2.line(L, (dx(dd), base - 6), (dx(dd), base + 6), (0, 0, 0), 2)
        cv2.putText(L, lab, (dx(dd) - 30, base + 24), FONT, 0.4, (0, 0, 0), 1, cv2.LINE_AA)
    cv2.putText(L, 'upstage <-   depth   -> downstage (camera)', (170, base + 50), FONT, 0.45, (60, 60, 60), 1, cv2.LINE_AA)
    rows = []
    for n, (z, eid, lay, obj) in enumerate(items):
        if isinstance(obj, StageActor):
            r = recs[eid]
            d = r.get('depth', None)
            if d is None:
                d = (r['z'] - 0.001)
            col, h_cm, bot = (0, 0, 220), (r['bbox'][3] / PX_PER_CM if r.get('bbox') else 0), (H - r['low_px']) / PX_PER_CM * 0
            lab = f'ACTOR {eid} [{r["anchor"]}] {r["drawing"].split("/")[-1][:18]}'
        elif obj.kind in ('backdrop', 'ground'):
            continue
        else:
            d = obj.info['d'] if obj.kind == 'piece' else obj.info['d']
            col = (150, 90, 0) if obj.kind == 'piece' else (0, 140, 0)
            h_cm = obj.info['stage_bbox'][3] / PX_PER_CM
            lab = f"{obj.info['plane']} {eid.split('/')[-1][:24]}"
            bot = (line_y(d) - obj.info['line_y']) / PX_PER_CM if obj.kind == 'prop' else 0
        x = dx(d) + (n % 3) * 5
        cv2.rectangle(L, (x - 3, hy(bot + h_cm)), (x + 3, hy(bot)), col, -1)
        rows.append((x, hy(bot + h_cm), lab, col))
    for i, (x, y, lab, col) in enumerate(sorted(rows, key=lambda t: t[0])):
        ty = 60 + i * 17
        cv2.putText(L, lab, (12, ty), FONT, 0.38, col, 1, cv2.LINE_AA)
        cv2.line(L, (min(690, 12 + 7 * len(lab)), ty - 4), (x, y), col, 1, cv2.LINE_AA)
    cv2.putText(L, 'vertical: 1.9 px per cm; bars start at their contact (props at their surface)', (16, 890), FONT, 0.4, (60, 60, 60), 1, cv2.LINE_AA)
    # exploded layers, draw order (back first)
    th = []
    for n, (z, eid, lay, obj) in enumerate(items):
        a = lay[..., 3:4].astype(np.float32) / 255.
        chk = np.full((H, W, 3), 235, np.float32)
        chk[(np.add.outer(np.arange(H) // 40, np.arange(W) // 40) % 2) == 0] = 215
        im = (lay[..., :3] * a + chk * (1 - a)).astype(np.uint8)
        t = cv2.resize(im, (256, 144), interpolation=cv2.INTER_AREA)
        t = cv2.copyMakeBorder(t, 0, 30, 2, 2, cv2.BORDER_CONSTANT, value=(255, 255, 255))
        kind = 'actor' if isinstance(obj, StageActor) else obj.kind
        cv2.putText(t, f'{n}: z={z:.3f} {kind}', (3, 156), FONT, 0.37, (0, 0, 160), 1, cv2.LINE_AA)
        cv2.putText(t, eid.split('/')[-1][:34], (3, 170), FONT, 0.33, (0, 0, 0), 1, cv2.LINE_AA)
        th.append(t)
    cols = 4
    while len(th) % cols:
        th.append(np.full_like(th[0], 255))
    grid = np.vstack([np.hstack(th[i:i + cols]) for i in range(0, len(th), cols)])
    gh = max(900, grid.shape[0])
    R = np.full((gh, grid.shape[1], 3), 255, np.uint8)
    R[:grid.shape[0]] = grid
    Lp = np.full((gh, 700, 3), 250, np.uint8)
    Lp[:900] = L
    cv2.imwrite(path, np.hstack([Lp, R]), [cv2.IMWRITE_JPEG_QUALITY, 88])


def shoot(stg, n_frames):
    fdir = os.path.join(OUT, '_f', stg.name)
    shutil.rmtree(fdir, ignore_errors=True)
    os.makedirs(fdir)
    recs, ids = [], {}
    still_f = int(n_frames * 0.8)
    for f in range(n_frames):
        want = (f % 6 == 0) or f == still_f
        img, r, (items, idb) = stg.frame(f, want_ids=want)
        recs.append(r)
        if want:
            ids[f] = (items, idb)
        if f == still_f:
            cv2.imwrite(os.path.join(OUT, stg.name + '.jpg'), img, [cv2.IMWRITE_JPEG_QUALITY, 92])
            layer_diagram(stg, f, r, items, os.path.join(OUT, stg.name + '_layers.jpg'))
        cv2.imwrite(os.path.join(fdir, '%04d.jpg' % f), img, [cv2.IMWRITE_JPEG_QUALITY, 92])
    encode(fdir, os.path.join(OUT, stg.name + '.mp4'))
    # strip on fours for viewing
    ims = [cv2.imread(os.path.join(fdir, '%04d.jpg' % f)) for f in range(0, n_frames, 8)]
    th = [cv2.resize(i, (320, 180)) for i in ims]
    while len(th) % 5:
        th.append(np.full((180, 320, 3), 255, np.uint8))
    cv2.imwrite(os.path.join(OUT, stg.name + '_strip.jpg'), np.vstack([np.hstack(th[i:i + 5]) for i in range(0, len(th), 5)]),
                [cv2.IMWRITE_JPEG_QUALITY, 85])
    shutil.rmtree(fdir)
    return {'recs': recs, 'ids': ids}


def jsonable(o):
    if isinstance(o, (np.floating, np.integer)):
        return o.item()
    if isinstance(o, np.ndarray):
        return o.tolist()
    if isinstance(o, (El, Placed, StageActor)):
        return getattr(o, 'id', None) or getattr(o, 'name', None) or str(o)
    return str(o)


def manifest(stg, samples, checks, extra):
    els = []
    for e in sorted(stg.els, key=lambda e: e.z):
        i = {k: v for k, v in e.info.items() if k != 'placed'}
        els.append(dict(id=e.id, kind=e.kind, z=round(e.z, 4), **i))
    acts = []
    for A in stg.actors:
        beats = []
        for b in A.sheet:
            bb = {k: (v.id if isinstance(v, El) else v) for k, v in b.items()}
            beats.append(bb)
        used = sorted({(r[A.name]['drawing'], r[A.name]['mirror']) for r in samples['recs'] if r[A.name].get('drawing')})
        acts.append({'name': A.name, 'char': A.c.char, 'height_cm': A.c.height_cm, 'frames': len(A), 'sheet': beats,
                     'drawings_used': used})
    m = {'scene': stg.name, 'poem': stg.poem, 'size': [W, H], 'fps': FPS, 'frames': len(samples['recs']),
         'px_per_cm': PX_PER_CM, 'ground_top_y': GROUND_TOP, 'front_y': FRONT,
         'depth_line': 'y = %d + d * %d' % (GROUND_TOP, FRONT - GROUND_TOP),
         'queries': stg.book.log, 'elements': els, 'actors': acts, 'interactions': stg.interactions,
         'declared_occlusion': [{'front': c[0], 'back': c[1], 'why': c[2]} for c in stg.constraints],
         'checks': checks}
    m.update(extra)
    json.dump(m, open(os.path.join(OUT, stg.name + '.json'), 'w'), indent=1, default=jsonable)
    return m


# ------------------------------------------------------------------ casts
def casts():
    poet = ex.Cast('poet__red_black_sunglasses', 'track', 183, 'poet')
    # the seated painting carries a cup in the hand (props ['cup']); it is let in only for seats
    for d in sel.library('poet__red_black_sunglasses', costume='track', props_ok=('cup',)):
        if d.cls == 'sit' and d.id.split('/')[-1] not in poet.by_id:
            d.ring = d.view
            poet.lib.append(d)
            poet.by_id[d.id.split('/')[-1]] = d
    man = ex.Cast('vintage_man__suit', 'suit', 177, 'vintage man')
    woman = ex.Cast('vintage_woman__gown', 'gown', 166, 'vintage woman')
    return {'poet': poet, 'vintage man': man, 'vintage woman': woman}


def seated_key(cast):
    """first clean seated painting of the cast (by tag), or None"""
    for d in cast.lib:
        if d.cls == 'sit':
            return d.id.split('/')[-1]
    return None


# ------------------------------------------------------------------ interaction measurements
def hidden_fraction(samples, actor, front_id, below_y=None, frames=None):
    """fraction of the actor's painted pixels (below below_y) that front_id covers, on the id-buffer frames"""
    fr = []
    for f, (items, ids) in samples['ids'].items():
        if frames and f not in frames:
            continue
        idx = {it[1]: n for n, it in enumerate(items)}
        if actor not in idx or front_id not in idx:
            continue
        al = items[idx[actor]][2][..., 3] > 127
        if below_y is not None:
            al[:int(below_y)] = False
        n = int(al.sum())
        if n:
            fr.append(float((al & (ids == idx[front_id])).sum()) / n)
    return round(float(np.mean(fr)), 3) if fr else None


def seat_affordance(rec):
    return next((a for a in rec['affordances'] if a['kind'] == 'seat'), None)


# ------------------------------------------------------------------ scenes (queries only)
def scene_bar(poem, C):
    """the house bar: a man behind a bar front (legs hidden by its front edge), bottles resting on its top,
    a woman dancing a spin downstage, a corrugated wall with an opening onto the night sky"""
    st = Stage(f'p{poem}_bar', poem)
    B = st.book
    sky = B.find('far backdrop', poem=poem, category='backdrop', plane='far_backdrop', contact='full-frame', text='night')
    st.backdrop(sky)
    gr = B.find('ground', poem=poem, category='ground', plane='ground_plane', text='floor')
    st.ground(gr)
    wall = B.find('back wall (with an opening)', pick=all_of(need_size, need_window), poem=poem,
                  category=['architecture', 'aperture'], plane='mid_set', text='wall')
    w = st.piece(wall, 640, 0.0, 'back wall')
    bar = B.find('counter with a surface', pick=all_of(need_size, no_flags('label_doubt')), poem=poem,
                 category='furniture-surface', affordance='surface', min_aff_conf=0.6, text='bar')
    b = st.piece(bar, 700, 0.55, 'counter')
    bottles = B.find('props for the counter top', pick=need_size, n=3, poem=poem, category='handheld-prop',
                     affordance='grip', contact='rests', text='bottle')
    for u, r in zip((0.12, 0.22, 0.86), bottles):
        st.on_surface(r, b, u, 'prop on counter')
    man, woman = C['vintage man'], C['vintage woman']
    stand = 'view:front/stand'
    m = st.actor(man, [{'d': stand, 'hold': 44, 'name': 'tends bar'},
                       {'d': 'view:q3/dance', 'hold': 30, 'bob': 4, 'bob_period': 10, 'settle': True, 'name': 'sways to the music'},
                       {'d': stand, 'hold': 46, 'name': 'back to the bar'}], 680 / PX_PER_CM, 0.22, man.name)
    ring = woman.ring('q3', 1.0, cls='dance')
    sheet = [{'d': ring[0], 'hold': 18, 'name': 'hold'}] + [{'d': k, 'hold': 3, 'name': 'spin 1'} for k in ring[1:]] + \
            [{'d': ring[0], 'hold': 16, 'name': 'land'}] + [{'d': k, 'hold': 2, 'name': 'spin 2', 'settle': False} for k in ring[1:]] + \
            [{'d': ring[0], 'hold': 120 - 18 - 21 - 16 - 14, 'name': 'end'}]
    wo = st.actor(woman, sheet, 250 / PX_PER_CM, 0.9, woman.name)
    st.constraints.append((b.id, man.name, 'actor stands behind the counter: its front edge hides his legs'))
    top_y = b.info['placed'].pt(0, next(a for a in bar['affordances'] if a['kind'] == 'surface')['geometry']['surface_y'])[1]
    st.interactions.append({'type': 'behind counter', 'actor': man.name, 'piece': b.id, 'counter_top_y': round(top_y, 1)})
    st.interactions.append({'type': 'props on surface', 'pieces': [r['id'] for r in bottles], 'surface': b.id})
    return st, 120


def scene_parlour(poem, C):
    """a living room: the poet walks in and sits in an armchair (seat line), its front arm in front of him;
    a phone rests on a side table; the wall's window shows the night"""
    st = Stage(f'p{poem}_parlour', poem)
    B = st.book
    sky = B.find('far backdrop', poem=poem, category='backdrop', plane='far_backdrop', contact='full-frame', text='night')
    st.backdrop(sky)
    gr = B.find('ground', poem=poem, category='ground', plane='ground_plane', text='floor')
    st.ground(gr)
    wall = B.find('back wall with a window', pick=all_of(need_size, need_window), poem=poem,
                  category=['architecture', 'aperture'], plane='mid_set', text='wall window')
    st.piece(wall, 640, 0.0, 'back wall')
    poet = C['poet']
    sk = seated_key(poet)
    chair = B.find('seat for a sitter', pick=all_of(need_size, no_flags('size_doubt', 'label_doubt')), poem=poem,
                   category='furniture-seat', affordance='seat', min_aff_conf=0.8)
    ch = st.piece(chair, 800, 0.45, 'seat')
    # a front overlay cut for this seat on the same sheet (same sheet pixel scale, measured from catalog bboxes)
    ov = None
    try:
        ovr = B.find('front overlay of the seat', sheet=chair['sheet'], text='overlay')
        ov = st.piece(ovr, ch.info['placed'].pt(image(chair)[1][0] + image(chair)[1][2], 0)[0], 0.45, 'overlay',
                      k=ch.info['k'], scale={'src': 'same sheet pixel scale as the seat', 'k': ch.info['k'],
                                             'basis': 'catalog bbox px == webp px for both parts (measured); position: bottom on the seat contact line, right edge on the seat right edge (inferred, template match failed: rms 57)'},
                      z=ch.z + 0.002, anchor='right')
    except RuntimeError:
        pass
    table = B.find('side table with a surface', pick=need_size, poem=poem, category='furniture-surface',
                   affordance='surface', text='table')
    t = st.piece(table, 1040, 0.36, 'side table')
    srf = next(a for a in table['affordances'] if a['kind'] == 'surface')['geometry']
    sw = abs(srf['x_range'][1] - srf['x_range'][0]) * t.info['k']

    def fits(r):
        s = resolve_scale(r)
        if not s:
            return False, 'no size'
        bw, bh = image(r)[1][2:]
        pw = bw * s['k']
        ok = pw <= 0.9 * sw and bw >= 0.5 * bh
        return ok, f'width {pw:.0f}px vs surface {sw:.0f}px, w/h {bw / bh:.2f} ({s["src"]})'
    phone = B.find('prop resting on the side table', pick=fits, poem=poem, category='handheld-prop', text='phone',
                   contact=['rests', 'stands'])
    st.on_surface(phone, t, 0.5, 'prop on side table')
    # he walks to just short of the seat, so the sit swap moves his pelvis only a little (measured: sit_jump_cm)
    seat_x = ch.info['stage_bbox'][0] + 0.42 * ch.info['stage_bbox'][2]
    walk_cm = (seat_x - 15 * PX_PER_CM) / PX_PER_CM - 60
    sheet = [{'d': 'walk-the-room', 'hold': 44, 'move_cm': walk_cm, 'bob': 5, 'bob_period': 11, 'settle': False, 'name': 'walks in'},
             {'d': 'arrive-01-in-file', 'hold': 12, 'name': 'stops by the chair'}]
    if sk:
        sheet.append({'d': sk, 'hold': 64, 'seat': ch, 'seat_u': 0.42, 'name': 'sits'})
    else:
        sheet.append({'d': 'view:front/stand', 'hold': 64, 'name': 'no seated painting: stands'})
    st.actor(poet, sheet, 60, 0.7, poet.name)
    seated = lambda recs: recs[poet.name].get('anchor') == 'seat'
    st.constraints.append((poet.name, ch.id, 'a sitter is in front of the seat body and back (while seated)', seated))
    if ov:
        st.constraints.append((ov.id, poet.name, "the seat's front arm overlay is in front of the sitter (while seated)", seated))
    st.interactions.append({'type': 'sit', 'actor': poet.name, 'seat': ch.id, 'seated_painting': sk,
                            'seat_affordance': seat_affordance(chair)})
    st.interactions.append({'type': 'props on surface', 'pieces': [phone['id']], 'surface': t.id})
    return st, 120


def scene_hall(poem, C):
    """a bedroom wall with a hall door: the poet walks along the hall behind the wall, stops in the
    doorway and waves; a woman stands downstage with her back to us"""
    st = Stage(f'p{poem}_doorway', poem)
    B = st.book
    sky = B.find('far backdrop', poem=poem, category='backdrop', plane='far_backdrop', contact='full-frame', text='night')
    st.backdrop(sky)
    gr = B.find('ground', poem=poem, category='ground', plane='ground_plane', text='floor')
    st.ground(gr)
    wall = B.find('wall with a door opening', pick=need_door, poem=poem, category='aperture', affordance='aperture',
                  text='wall')
    w = st.piece(wall, 600, 0.0, 'wall with door')
    door = w.info['scale']['opening']
    dr = w.info['placed'].rect(door['rect'])
    dcx = dr[0] + dr[2] / 2
    hall = B.find('hall seen through the door', pick=need_size, poem=poem, category='aperture', text='corridor')
    st.piece(hall, dcx, -0.14, 'behind-flat')
    poet, woman = C['poet'], C['vintage woman']
    # he comes along the hall from the left, behind solid wall, so he is first seen in the door opening
    sheet = [{'d': 'walk-the-room', 'hold': 42, 'move_cm': 175, 'bob': 5, 'bob_period': 10, 'settle': False, 'name': 'walks along the hall'},
             {'d': 'arrive-01-in-file', 'hold': 26, 'name': 'stops in the doorway'},
             {'d': '07-hello', 'hold': 52, 'name': 'waves'}]
    st.actor(poet, sheet, dcx / PX_PER_CM - 175, -0.04, poet.name)
    st.actor(woman, [{'d': 'view:back/stand', 'hold': 64, 'name': 'waits, back to us'},
                     {'d': 'view:back3q/dance', 'hold': 56, 'name': 'turns toward him'}], 300 / PX_PER_CM, 0.9, woman.name)
    st.constraints.append((w.id, poet.name, 'actor in the doorway: the wall around the opening is in front of him'))
    st.constraints.append((poet.name, hall['id'], 'actor in the doorway is in front of the hall behind'))
    st.interactions.append({'type': 'stand in doorway', 'actor': poet.name, 'wall': w.id, 'opening_stage_rect': [round(v, 1) for v in dr],
                            'opening_floor_y': round(dr[1] + dr[3], 1)})
    return st, 120


SCENES = [scene_bar, scene_parlour, scene_hall]


def negative_control(st):
    """does the occlusion check catch a wrong order? Each declared constraint's front layer is pushed
    behind its back layer, two id-buffer frames are rendered and checked; restored afterwards."""
    out = []
    for con in list(st.constraints):
        fr, bk, why = con[:3]
        el = next((e for e in st.els if e.id == fr), None)
        A = next((a for a in st.actors if a.name == fr), None)
        f = int(0.8 * max(len(a) for a in st.actors))
        if el is not None:
            z0 = el.z
            bz = next((e.z for e in st.els if e.id == bk), None)
            if bz is None:
                _, r = next(a for a in st.actors if a.name == bk).layer(f)
                bz = r['z']
            el.z = bz - 0.01
            img, recs, (items, ids) = st.frame(f, want_ids=True)
            el.z = z0
        else:
            continue          # an actor's z comes from its beat; the El-side cases are enough for a control
        sm = {'recs': [recs] * (f + 1), 'ids': {f: (items, ids)}}
        idx = {it[1]: n for n, it in enumerate(items)}
        la, lb = items[idx[fr]][2], items[idx[bk]][2]
        both = (la[..., 3] > 127) & (lb[..., 3] > 127)
        bad = int((both & (ids == idx[bk])).sum())
        out.append({'pushed_behind': fr, 'of': bk, 'overlap_px': int(both.sum()), 'violating_px_detected': bad,
                    'detected': bad > 20 or int(both.sum()) == 0})
    return out


def measure_interactions(st, samples):
    out = []
    for it in st.interactions:
        r = dict(it)
        if it['type'] == 'behind counter':
            r['legs_hidden_frac'] = hidden_fraction(samples, it['actor'], it['piece'], below_y=it['counter_top_y'] + 3)
            r['visible_above_counter_frac'] = None
            fr = []
            for f, (items, ids) in samples['ids'].items():
                idx = {x[1]: n for n, x in enumerate(items)}
                al = items[idx[it['actor']]][2][..., 3] > 127
                up = al.copy(); up[int(it['counter_top_y']):] = False
                if up.sum():
                    fr.append(float((up & (ids == idx[it['actor']])).sum()) / up.sum())
            r['visible_above_counter_frac'] = round(float(np.mean(fr)), 3) if fr else None
        elif it['type'] == 'sit':
            rs = [samples['recs'][f][it['actor']] for f in range(len(samples['recs']))]
            seated = [x for x in rs if x.get('anchor') == 'seat']
            if seated:
                x = seated[-1]
                el = next(e for e in st.els if e.id == it['seat'])
                r['seat_line_y'] = x['seat_line_y']
                r['seat_err_px_measured'] = x.get('seat_err_px')
                r['feet_below_seat_contact_cm'] = round((x['low_px'] - el.info['line_y']) / PX_PER_CM, 1)
                r['note_feet'] = 'positive = the feet reach lower than the chair legs: on the toy-theatre floor that reads as feet set forward of the chair'
                r['seat_height_cm_chair'] = round((el.info['line_y'] - x['seat_line_y']) / PX_PER_CM, 1)
                r['seat_to_feet_cm_painting'] = round((x['low_px'] - x['seat_line_y']) / PX_PER_CM, 1)
                r['seated_frames'] = len(seated)
        elif it['type'] == 'stand in doorway':
            dx0, dy0, dw, dh = it['opening_stage_rect']
            rows = []
            for f, (items, ids) in samples['ids'].items():
                rec = samples['recs'][f][it['actor']]
                if rec.get('cls') != 'stand' or 'walk' in (rec.get('drawing') or ''):
                    continue
                idx = {x[1]: n for n, x in enumerate(items)}
                al = items[idx[it['actor']]][2][..., 3] > 127
                vis = al & (ids == idx[it['actor']])
                ys, xs = np.nonzero(vis)
                inside = ((xs >= dx0) & (xs <= dx0 + dw) & (ys >= dy0) & (ys <= dy0 + dh)).mean() if len(xs) else None
                rows.append({'frame': f, 'feet_y': rec['low_px'], 'visible_px': int(len(xs)), 'visible_inside_opening_frac': round(float(inside), 3) if inside is not None else None,
                             'head_clearance_cm': round((rec['bbox'][1] - dy0) / PX_PER_CM, 1), 'painted_px': int(al.sum())})
            r['frames'] = rows
            if rows:
                r['feet_vs_threshold_px'] = round(float(np.median([x['feet_y'] for x in rows])) - it['opening_floor_y'], 1)
                r['visible_inside_opening_frac_min'] = min(x['visible_inside_opening_frac'] for x in rows if x['visible_inside_opening_frac'] is not None)
                r['head_clearance_cm_min'] = min(x['head_clearance_cm'] for x in rows)
        elif it['type'] == 'props on surface':
            r['contact'] = []
            for pid in it['pieces']:
                e = next(e for e in st.els if e.id == pid)
                lay = e.layer
                ys, xs = np.nonzero(lay[..., 3] > 40)
                xr = e.info['surface']['x_range_stage']
                r['contact'].append({'id': pid, 'bottom_y': int(ys.max()), 'rest_y': e.info['surface']['stage_y'],
                                     'err_px': round(float(ys.max() - e.info['surface']['stage_y']), 1),
                                     'within_surface_x': bool(min(xr) <= xs.mean() <= max(xr))})
        out.append(r)
    return out


def run(only=None):
    os.makedirs(OUT, exist_ok=True)
    rank = richness()
    top = [r['poem'] for r in rank[:3]]
    C = casts()
    summary = {'richness': rank, 'chosen_poems': top, 'scenes': {}}
    for poem, fn in zip(top, SCENES):
        if only and only not in fn.__name__:
            continue
        st, n = fn(poem, C)
        samples = shoot(st, n)
        checks = check_scene(st, samples)
        checks['interactions'] = measure_interactions(st, samples)
        checks['occlusion']['negative_control'] = negative_control(st)
        jumps = []
        for A in st.actors:
            rs = [r[A.name] for r in samples['recs']]
            for a, b in zip(rs, rs[1:]):
                if b.get('swap') and a.get('centre_px') is not None and b.get('centre_px') is not None:
                    jumps.append({'actor': A.name, 'into': b['beat'], 'centre_jump_cm': round(abs(b['centre_px'] - a['centre_px']) / PX_PER_CM, 1)})
        checks['swap_jumps'] = jumps
        checks['height_guard'] = sorted({(A.name, r[A.name]['drawing'].split('/')[-1], r[A.name]['height_guard']['marker_scale_height_cm'])
                                         for A in st.actors for r in samples['recs'] if r[A.name].get('height_guard')})
        m = manifest(st, samples, checks, {'richness_rank': next(i for i, r in enumerate(rank) if r['poem'] == poem) + 1,
                                            'richness': next(r for r in rank if r['poem'] == poem)})
        s = {'off_ground': [c['id'] for c in checks['contact'] if c.get('off_ground')],
             'floating_or_sunk': [c['id'] for c in checks['contact'] if c.get('floating_or_sunk')],
             'occlusion_violations': len(checks['occlusion']['violations']),
             'constraints_checked': checks['occlusion']['constraints_checked'],
             'scale': [(x['actor'], x['piece'].split('/')[-1][:30], x.get('rendered_over_expected'), x['scale_src']) for x in checks['scale']],
             'interactions': checks['interactions']}
        summary['scenes'][st.name] = s
        print(json.dumps({st.name: s}, indent=1, default=jsonable)[:4000])
    json.dump(summary, open(os.path.join(OUT, 'summary.json'), 'w'), indent=1, default=jsonable)
    shutil.rmtree(os.path.join(OUT, '_f'), ignore_errors=True)


if __name__ == '__main__':
    if len(sys.argv) > 1 and sys.argv[1] == 'rank':
        for r in richness():
            print(r['poem'], r['score'], r['total'], r['roles'])
    else:
        run(sys.argv[1] if len(sys.argv) > 1 else None)
