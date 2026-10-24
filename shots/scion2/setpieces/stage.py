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

sys.path.insert(0, os.path.join(HERE, 'repair'))
import query                                    # noqa: E402
import border, actors as actmeas                # noqa: E402  (repair: card border, per-drawing measures)
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


# ------------------------------------------------------------------ camera (repair v2: one pinhole camera)
# v1 drew everything at one scale (a flat toy theatre), so a nearer actor could be smaller than a farther
# one and the floor was a strip in front elevation. v2 keeps the back line at PX_PER_CM and gives every
# depth line its perspective scale from one camera: eye height EYE_CM (inferred, a standing eye), so the
# horizon is EYE_CM * PX_PER_CM above the back line; focal F_PX from a 60 degree horizontal field (inferred).
EYE_CM = 150.0
HORIZON = GROUND_TOP - EYE_CM * PX_PER_CM          # 230
F_PX = (W / 2) / math.tan(math.radians(30))         # 1108.5
Z0_CM = F_PX / PX_PER_CM                            # camera distance of the back line, 462 cm
WALL_T_CM = 25.0                                    # wall thickness for opening reveals (inferred)


def persp(y):
    """scale factor of a thing standing on stage row y, relative to the back line"""
    return (y - HORIZON) / (GROUND_TOP - HORIZON)


def z_of(y):
    return Z0_CM / persp(y)


def y_of(z_cm, h_cm=0.0):
    """stage row of a point h_cm above the floor at camera distance z_cm"""
    return HORIZON + (EYE_CM - h_cm) * PX_PER_CM * Z0_CM / z_cm


def is_flat(rec):
    return rec['category'] in ('architecture', 'aperture') and rec['plane'] == 'mid_set'


# ------------------------------------------------------------------ real-world expectations (inferred)
# (keywords, dimension, lo, typical, hi) in cm. First match wins, so specific words come first.
EXPECT = [
    (('armchair', 'wing chair'), 'h', 85, 95, 110),
    (('sofa', 'couch'), 'h', 70, 85, 100),
    (('chair',), 'h', 80, 88, 100),
    (('pew',), 'h', 80, 95, 110),
    (('bench',), 'h', 40, 50, 95),
    (('bar front', 'homebar', 'counter'), 'h', 95, 105, 120),
    (('side table',), 'h', 50, 62, 70),          # repair v2: occasional tables are lower than dining tables (inferred)
    (('table',), 'h', 55, 72, 80),
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
FLAT_FIX = {}          # part id -> what clean_flat did (measured)


def floor_cut(a):
    """row (in a's coords) above which holes are counted: the median painted bottom of the columns minus 2%
    of the height (measured). Below it, the uneven bottom edge of a flat is not an opening."""
    cols = [np.nonzero(a[:, x])[0].max() for x in range(a.shape[1]) if a[:, x].any()]
    return int(np.median(cols) - 0.02 * a.shape[0])


def raw_holes(a):
    """transparent holes: a transparent pixel with paint to its left, its right and above it, above the floor cut"""
    left = np.maximum.accumulate(a, axis=1)
    right = np.maximum.accumulate(a[:, ::-1], axis=1)[:, ::-1]
    above = np.maximum.accumulate(a, axis=0)
    h = (~a) & left & right & above
    h[floor_cut(a):] = False
    return h


def clean_flat(im):
    """repair v2, for flats only (walls, apertures): (1) trim the painted card border the cutter left on the
    outside (rope / tan trim: critic saw it at the frame edges and along the wall/floor seam), width measured
    per part by border.border_width; (2) straighten each opening: its rectangle is the rows/columns that are
    >= 50% hole inside the hole's bbox; ragged paint inside it is cleared and ragged transparent bits
    outside it are filled by inpainting from the wall (critic saw a torn/deckle edge inside the glass)."""
    t, ev = border.border_width(im)
    im = border.trim(im, t)
    a = im[..., 3] > 40
    ys, xs = np.nonzero(a)
    bx, by, bw, bh = xs.min(), ys.min(), xs.max() - xs.min() + 1, ys.max() - ys.min() + 1
    sub = a[by:by + bh, bx:bx + bw]
    hole = raw_holes(sub)
    cut = floor_cut(sub)
    n, lab, st, _ = cv2.connectedComponentsWithStats(hole.astype(np.uint8), 8)
    fixes = []
    fill = np.zeros(im.shape[:2], np.uint8)
    clear = np.zeros(im.shape[:2], bool)
    for i in range(1, n):
        x, y, w, h, ar = st[i]
        if ar < 0.01 * bw * bh or w < 0.05 * bw or h < 0.15 * bh:
            continue
        comp = lab[y:y + h, x:x + w] == i
        rows = np.nonzero(comp.mean(1) >= 0.5)[0]
        cols = np.nonzero(comp.mean(0) >= 0.5)[0]
        if not len(rows) or not len(cols):
            continue
        r0, r1, c0, c1 = rows.min(), rows.max() + 1, cols.min(), cols.max() + 1
        if y + h >= cut - 2:
            r1 = bh - y                              # a door: open to the bottom
        X0, Y0 = bx + x, by + y
        rect = np.zeros(comp.shape, bool)
        rect[r0:r1, c0:c1] = True
        outside = comp & ~rect                       # ragged transparent bits outside the clean rectangle
        fill[Y0:Y0 + h, X0:X0 + w][outside] = 255
        clear[Y0 + r0:Y0 + r1, X0 + c0:X0 + c1] = True
        # raggedness of the original edge (measured): mean |edge position - rectangle side| along each side
        fixes.append({'hole_bbox': [int(X0), int(Y0), int(w), int(h)], 'rect': [int(X0 + c0), int(Y0 + r0), int(c1 - c0), int(r1 - r0)],
                      'filled_px': int(outside.sum()), 'cleared_paint_px': int((a[Y0 + r0:Y0 + r1, X0 + c0:X0 + c1]).sum())})
    if fill.any():
        im[..., :3] = cv2.inpaint(im[..., :3], fill, 4, cv2.INPAINT_TELEA)
        im[..., 3] = np.where(fill > 0, 255, im[..., 3])
    im[..., 3] = np.where(clear, 0, im[..., 3])
    return im, {'border_trim_px': t, 'border_evidence': ev, 'openings_straightened': fixes}


def image(rec):
    """BGRA cut-out (cached) and its alpha bbox (x, y, w, h), measured at alpha > 40. Flats are cleaned
    (clean_flat) first, so every later measure (contact line, openings, scale) sees the cleaned part."""
    if rec['id'] not in _IMG:
        im = cv2.imread(query.path(rec), cv2.IMREAD_UNCHANGED)
        if im.shape[2] == 3:
            im = np.dstack([im, np.full(im.shape[:2], 255, np.uint8)])
        if is_flat(rec):
            im, FLAT_FIX[rec['id']] = clean_flat(im)
        elif rec['category'] not in ('ground',) and rec.get('kind', 'card') == 'card':
            # rectangular cards (alpha fills >= 90% of its bbox: a counter front, a backdrop) carry the same
            # painted card border; trim it (measured width). Shaped cut-outs are left alone.
            a0 = im[..., 3] > 40
            ys_, xs_ = np.nonzero(a0)
            fillr = a0.sum() / float((xs_.max() - xs_.min() + 1) * (ys_.max() - ys_.min() + 1))
            if fillr >= 0.9:
                t, ev = border.border_width(im)
                im = border.trim(im, t)
                FLAT_FIX[rec['id']] = {'border_trim_px': t, 'bbox_fill': round(float(fillr), 3), 'openings_straightened': []}
        a = im[..., 3] > 40
        ys, xs = np.nonzero(a)
        _IMG[rec['id']] = (im, (int(xs.min()), int(ys.min()), int(xs.max() - xs.min() + 1), int(ys.max() - ys.min() + 1)))
    return _IMG[rec['id']]


def openings(rec):
    """transparent holes in a flat, measured from alpha: a transparent pixel with paint to its left, its
    right and above it (inside the alpha bbox). -> [{rect [x,y,w,h], open_bottom, area}] largest first"""
    im, (bx, by, bw, bh) = image(rec)
    a = im[by:by + bh, bx:bx + bw, 3] > 40
    hole = raw_holes(a)
    cut = floor_cut(a)
    n, lab, st, _ = cv2.connectedComponentsWithStats(hole.astype(np.uint8), 8)
    out = []
    for i in range(1, n):
        x, y, w, h, ar = st[i]
        if ar < 0.01 * bw * bh or w < 0.05 * bw or h < 0.15 * bh:
            continue
        ob = bool(y + h >= cut - 2)
        if ob:
            h = bh - y
        out.append({'rect': [int(x + bx), int(y + by), int(w), int(h)], 'open_bottom': ob,
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


# ------------------------------------------------------------------ repair v2: choosing floor and backdrop
import palette                                   # noqa: E402

FLOOR_NOT = ('water', 'road', 'pool', 'quay', 'ripple', 'kerb', 'curb', 'tide', 'shoulder', 'rim', 'ash', 'mud', 'soil',
             'sand', 'trail', 'grit', 'mound', 'snap', 'tick', 'splinter', 'reflection', 'lip', 'inlay', 'driveway')
FLOOR_MIN_PX = 300          # interior card width: the card is stretched across ~1.3-1.8k px (measured on the render)
FLOOR_MAX_PERIOD = 0.6      # autocorrelation peak of the high-passed card: above it the texture is machine-repeated
RUN_FILLS = []              # backdrops chosen earlier in this run: (scene, id, signature)


def choose_floor(st, wall_rec, poem):
    """the floor is chosen with the walls (critic: neon lobby floor under a parlour). Candidates: every usable
    ground-plane card a person can stand on (stand_on >= 0.5, any poem), not an outdoor/edge strip by name,
    interior >= FLOOR_MIN_PX wide, not periodic (autocorrelation peak <= FLOOR_MAX_PERIOD). Score = palette
    distance between the card and the bottom 30% of the wall (palette.dist), minus 12 for the wall's own sheet
    and 6 for the scene's poem. Lowest score wins. All candidates and their numbers go to the scene json."""
    wsig = palette.sig(image(wall_rec)[0], (0.7, 1.0))
    rows = []
    for r in query.find(category='ground', plane='ground_plane', affordance='stand_on', min_aff_conf=0.5):
        w = words_of(r)
        why = []
        bad = [k for k in FLOOR_NOT if k in w]
        if bad:
            why.append('outdoor/edge word ' + ','.join(bad))
        c = Stage.card_interior(r)
        if c.shape[1] < FLOOR_MIN_PX:
            why.append(f'interior {c.shape[1]} px wide < {FLOOR_MIN_PX}')
        per = palette.periodicity(c, 1)
        if per[0] > FLOOR_MAX_PERIOD:
            why.append(f'periodic x {per[0]} at {per[1]} px')
        fs = palette.sig(c)
        dist = palette.dist(fs, wsig)
        bonus = (12 if r['sheet'] == wall_rec['sheet'] else 0) + (6 if poem in r['poems'] else 0)
        rows.append({'id': r['id'], 'score': round(dist - bonus, 1), 'palette_dist': dist, 'bonus': bonus, 'periodicity_x': per,
                     'interior_px': [int(c.shape[1]), int(c.shape[0])], 'sig': fs, 'rejected': '; '.join(why) or None})
    ok = sorted([r for r in rows if not r['rejected']], key=lambda r: r['score'])
    st.repair['floor_choice'] = {'wall': wall_rec['id'], 'wall_bottom_sig': wsig, 'chosen': ok[0]['id'] if ok else None,
                                 'ranked': ok[:10], 'rejected': [r for r in rows if r['rejected']][:40],
                                 'n_candidates': len(rows)}
    st.book.log.append({'role': 'ground (chosen with the wall)', 'query': {'category': 'ground', 'plane': 'ground_plane',
                        'affordance': 'stand_on', 'min_aff_conf': 0.5}, 'returned_count': len(rows),
                        'chosen': [{'id': ok[0]['id'], 'why': f"lowest palette score {ok[0]['score']} vs wall bottom"}],
                        'skipped': [{'id': r['id'], 'why': r['rejected']} for r in rows if r['rejected']][:15]})
    return query.get(ok[0]['id'])


def choose_backdrop(st, poem, min_dist=12.0):
    """far plane per set (critic: one blue cloud swatch behind the door and windows of two scenes): the poem's
    full-frame backdrops, not a thin band (alpha bbox w/h <= 4, a band would be blown up by the cover fit), and
    at least min_dist (palette.dist) from every backdrop chosen earlier in this run. 'night' ones first."""
    def pick(r):
        im, bb = image(r)
        asp = bb[2] / bb[3]
        if asp > 4:
            return False, f'band w/h {asp:.1f} > 4'
        sg = palette.sig(im)
        for scn, rid, s2 in RUN_FILLS:
            dd = palette.dist(sg, s2)
            if dd < min_dist:
                return False, f'palette {dd} from {rid} used in {scn} (< {min_dist})'
        return True, f'w/h {asp:.2f}; distinct from {len(RUN_FILLS)} earlier fills'
    try:
        r = st.book.find('far backdrop', pick=pick, poem=poem, category='backdrop', plane='far_backdrop', contact='full-frame', text='night')
    except RuntimeError:
        r = st.book.find('far backdrop', pick=pick, poem=poem, category='backdrop', plane='far_backdrop', contact='full-frame')
    RUN_FILLS.append((st.name, r['id'], palette.sig(image(r)[0])))
    st.repair['backdrop'] = {'id': r['id'], 'sig': RUN_FILLS[-1][2], 'earlier': [(a, b) for a, b, _ in RUN_FILLS[:-1]]}
    return r


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
        self.vpx = W / 2.0           # vanishing point x on the horizon (measured from a wall corner if any)
        self.vp_src = 'frame centre (no wall corner measured)'
        self.floor_rec = None
        self.repair = {}             # repair v2 evidence per mechanism

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
    @staticmethod
    def card_interior(rec):
        """the fully painted inner rectangle of a ground card (measured), minus its painted card border"""
        im, (bx, by, bw, bh) = image(rec)
        crop = im[by:by + bh, bx:bx + bw]
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
            t, _ = border.border_width(crop)
            mx, my = max(int(0.03 * inner[2]), t), max(int(0.04 * inner[3]), t)
            crop = crop[r0 + my:r1 - my, c0 + mx:c1 - mx]
        return crop

    def ground(self, rec, y_top=None):
        """repair v2: the floor is one plane in the camera's perspective. One card (no tiling: v1 mirror-tiled
        a strip, which the critic saw as repeated seams and rivet pairs) is mapped by a homography onto the
        floor rectangle that runs from y_top (the back line, or further back when a hall continues behind a
        door) to below the frame, wide enough to cover the frame at its far edge. Its boards/seams converge
        on the vanishing point (self.vpx, HORIZON), the same one the walls' corners and reveals use."""
        crop = self.card_interior(rec)
        # the far edge of a floor card is painted ragged (viewed: broken-board notches at the p01 wall/floor seam);
        # its first 10% of rows are dropped (inferred share)
        crop = crop[int(0.10 * crop.shape[0]):]
        ch, cw = crop.shape[:2]
        yt = GROUND_TOP - 6 if y_top is None else y_top
        yf = H + 30
        mt, mf = persp(yt), persp(yf)
        half_cm = (max(self.vpx, W - self.vpx) + 40) / (PX_PER_CM * mt)
        src = np.float32([[0, 0], [cw, 0], [cw, ch], [0, ch]])
        dst = np.float32([[self.vpx - half_cm * PX_PER_CM * mt, yt], [self.vpx + half_cm * PX_PER_CM * mt, yt],
                          [self.vpx + half_cm * PX_PER_CM * mf, yf], [self.vpx - half_cm * PX_PER_CM * mf, yf]])
        Hm = cv2.getPerspectiveTransform(src, dst)
        c = crop.copy()
        c[..., 3] = 255
        lay = cv2.warpPerspective(c, Hm, (W, H), flags=cv2.INTER_LINEAR, borderMode=cv2.BORDER_CONSTANT, borderValue=(0, 0, 0, 0))
        depth_cm = z_of(yt) - z_of(yf)
        self.floor_rec = rec
        self.els.append(El(rec['id'], 'ground', -5, lay, plane='ground_plane', y_top=round(yt, 1),
                           card_px=[cw, ch], floor_world_cm=[round(2 * half_cm), round(depth_cm)],
                           stretch_x_over_y=round((2 * half_cm / cw) / (depth_cm / ch), 2), tiles=1,
                           vanishing_point=[round(self.vpx, 1), HORIZON],
                           scale_src='one card on the floor plane by homography (camera EYE_CM=%d, F_PX=%.0f); not real size: a ground card is a texture' % (EYE_CM, F_PX)))

    # ---- real-size pieces
    def piece(self, rec, x, d, role, mirror=False, k=None, scale=None, z=None, line=None, anchor='center', m=None):
        """stand the piece on depth line d (its contact y on line_y(d)), x = its centre (or left/right edge).
        repair v2: its real-size scale is multiplied by the perspective scale of its contact line (or m)."""
        im, (bx, by, bw, bh) = image(rec)
        sc = scale or resolve_scale(rec)
        mp = m if m is not None else persp(line_y(d) if line is None else line)
        k = k or sc['k'] * mp
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
               d=d, line_y=round(yl, 1), k=round(k, 4), persp=round(mp, 4), scale=sc, contact_y_px={'registry': cy_reg, 'measured_alpha_bottom': cy_meas, 'used': cy, 'src': cy_src},
               contact_type=c.get('type'), mirror=mirror, placed=P,
               stage_bbox=[round(tx + k * (bx if not mirror else im.shape[1] - 1 - bx - bw)), round(ty + k * by), round(k * bw), round(k * bh)])
        self.els.append(e)
        return e

    # ---- repair v2: one vanishing point, measured from a wall's painted corner
    def measure_vp(self, wall_el):
        """a flat with a side wall painted in perspective (p09: its left corner) has a floor line that slopes at
        its end. The columns whose painted bottom is > 4 px off the wall's median bottom, in a run of >= 20 px
        from either end, are fitted with a line; its crossing of the horizon is the vanishing point. With no
        such run the wall is flat elevation and the VP stays at the frame centre (both measured)."""
        al = wall_el.layer[..., 3] > 40
        xs = [x for x in range(W) if al[:, x].any()]
        bots = np.array([np.nonzero(al[:, x])[0].max() for x in xs], np.float32)
        xs = np.array(xs, np.float32)
        med = float(np.median(bots))
        out = []
        for side in ('left', 'right'):
            idx = range(len(xs)) if side == 'left' else range(len(xs) - 1, -1, -1)
            run = []
            for i in idx:
                if abs(bots[i] - med) > 4:
                    run.append(i)
                else:
                    break
            if len(run) < 20:
                continue
            k, c = np.polyfit(xs[run], bots[run], 1)
            if abs(k) < 0.05 or float(np.abs(np.polyval([k, c], xs[run]) - bots[run]).mean()) > 3.0:
                out.append({'side': side, 'run_px': len(run), 'rejected': 'not a straight corner line (slope < 0.05 or fit residual > 3 px)',
                            'fit_resid_px': round(float(np.abs(np.polyval([k, c], xs[run]) - bots[run]).mean()), 2)})
                continue
            vx = (HORIZON - c) / k
            resid = float(np.abs(np.polyval([k, c], xs[run]) - bots[run]).mean())
            out.append({'side': side, 'run_px': len(run), 'slope': round(float(k), 3), 'fit_resid_px': round(resid, 2),
                        'vp_x': round(float(vx), 1)})
        good = [o for o in out if 'vp_x' in o and -0.25 * W <= o['vp_x'] <= 1.25 * W]
        if good:
            self.vpx = float(np.mean([o['vp_x'] for o in good]))
            self.vp_src = 'measured from the painted corner of ' + wall_el.id
        self.repair['vanishing_point'] = {'vpx': round(self.vpx, 1), 'horizon_y': HORIZON, 'src': self.vp_src,
                                          'wall_bottom_median_y': med, 'corner_runs': out}
        return out

    # ---- repair v2: openings get a reveal (the wall's thickness), drawn behind the flat
    def reveals(self, wall_el, z=None):
        """for every opening of a placed flat: the faces of a WALL_T_CM thick wall that the camera sees (lintel
        underside when the opening top is above the horizon, sill top when its bottom is below it, the jamb on
        the side away from the vanishing point), each face the quad between the opening edge and that edge
        moved WALL_T_CM back toward the vanishing point. Colour: the wall paint in a ring 4..18 px around the
        opening (measured), shaded (lintel 0.45, jambs 0.62, sill 0.85; inferred light from above)."""
        P = wall_el.info['placed']
        rec = P.rec
        mw = wall_el.info['persp']
        Zw = Z0_CM / mw
        tau = WALL_T_CM / (Zw + WALL_T_CM)
        VP = np.array([self.vpx, HORIZON], np.float32)
        lay = np.zeros((H, W, 4), np.uint8)
        wal = wall_el.layer
        info = []
        for o in openings(rec):
            x, y, w, h = P.rect(o['rect'])
            x0, y0, x1, y1 = x, y, x + w, y + h
            ring = np.zeros((H, W), np.uint8)
            cv2.rectangle(ring, (int(x0 - 18), int(y0 - 18)), (int(x1 + 18), int(y1 + 18)), 255, -1)
            cv2.rectangle(ring, (int(x0 - 4), int(y0 - 4)), (int(x1 + 4), int(y1 + 4)), 0, -1)
            sel_ = (ring > 0) & (wal[..., 3] > 200)
            col = wal[..., :3][sel_].mean(0) if sel_.any() else np.array([90, 90, 90], np.float32)
            P0 = {'TL': np.array([x0, y0]), 'TR': np.array([x1, y0]), 'BR': np.array([x1, y1]), 'BL': np.array([x0, y1])}
            Q = {k: v + (VP - v) * tau for k, v in P0.items()}
            faces = []
            if VP[1] > y0:
                faces.append(('lintel', ['TL', 'TR'], 0.45))
            if VP[1] < y1 and not o['open_bottom']:
                faces.append(('sill', ['BL', 'BR'], 0.85))
            if VP[0] > x0:
                faces.append(('left jamb', ['TL', 'BL'], 0.62))
            if VP[0] < x1:
                faces.append(('right jamb', ['TR', 'BR'], 0.62))
            fi = []
            for name, (a, b), shade in faces:
                quad = np.array([P0[a], P0[b], Q[b], Q[a]], np.float32)
                c = tuple(int(v) for v in np.clip(col * shade, 0, 255)) + (255,)
                cv2.fillConvexPoly(lay, np.round(quad).astype(np.int32), c, cv2.LINE_AA)
                cv2.line(lay, tuple(np.round(Q[a]).astype(int)), tuple(np.round(Q[b]).astype(int)),
                         tuple(int(v) for v in np.clip(col * shade * 0.6, 0, 255)) + (255,), 1, cv2.LINE_AA)
                depth = float(max(np.linalg.norm(Q[a] - P0[a]), np.linalg.norm(Q[b] - P0[b])))
                perp = abs(float((Q[a] - P0[a])[1])) if name in ('lintel', 'sill') else abs(float((Q[a] - P0[a])[0]))
                fi.append({'face': name, 'depth_px': round(depth, 1), 'depth_perp_px': round(perp, 1)})
            info.append({'opening_stage_rect': [round(v, 1) for v in (x0, y0, w, h)], 'door': o['open_bottom'], 'faces': fi,
                         'max_face_px': max([f['depth_perp_px'] for f in fi], default=0.0),
                         'sill_cm_above_floor': None if o['open_bottom'] else round((wall_el.info['line_y'] - y1) / (PX_PER_CM * mw), 1)})
        e = El(wall_el.id + '#reveal', 'reveal', (wall_el.z - 0.05) if z is None else z, lay, plane='mid_set', role='reveal',
               of=wall_el.id, wall_thickness_cm=WALL_T_CM, tau=round(tau, 4), openings=info,
               scale_src='generated from the measured openings (inferred: wall thickness, light)')
        self.els.append(e)
        self.repair.setdefault('reveals', []).append({'wall': wall_el.id, 'openings': info})
        return e

    # ---- repair v2: contact shadows tie standing things to the floor plane
    def shadow_for(self, lay, line, m, z, eid, strength=0.42):
        al = lay[..., 3] > 40
        ys = np.nonzero(al.any(1))[0]
        if not len(ys):
            return None
        low = ys.max()
        band = al[max(0, low - max(6, int(0.04 * (low - ys.min())))):low + 1]
        xs = np.nonzero(band.any(0))[0]
        if not len(xs):
            return None
        cx, hw = (xs.min() + xs.max()) / 2, (xs.max() - xs.min()) / 2 * 1.08 + 6
        hh = max(4.0, 7 * m)
        sh = np.zeros((H, W), np.float32)
        cv2.ellipse(sh, (int(cx), int(line)), (int(hw), int(hh)), 0, 0, 360, 1.0, -1, cv2.LINE_AA)
        sh = cv2.GaussianBlur(sh, (0, 0), 4)
        out = np.zeros((H, W, 4), np.uint8)
        out[..., 3] = (sh * 255 * strength).astype(np.uint8)
        return out

    def add_shadow(self, el, strength=0.42):
        lay = self.shadow_for(el.layer, el.info['line_y'], el.info.get('persp', 1.0), None, el.id, strength)
        if lay is not None:
            z = -4 if el.kind == 'piece' else el.z - 0.0002
            self.els.append(El(el.id + '#shadow', 'shadow', z, lay, plane='ground_plane', role='contact shadow', of=el.id,
                               scale_src='generated (inferred: soft contact shadow)'))

    # ---- repair v2: a counter top seen from above
    def counter_top(self, front_el, top_rec, depth_cm=50.0):
        """a front-elevation counter only shows its front. Its top is a horizontal plane the camera (eye above it)
        sees from above: the top card (same sheet) is mapped by homography onto the trapezoid between the
        front's top edge (its surface affordance, measured) and the edge depth_cm behind it (inferred depth),
        both converging on the vanishing point. Returns the plane's geometry for props to rest on."""
        P = front_el.info['placed']
        g = next(a for a in P.rec['affordances'] if a['kind'] == 'surface')['geometry']
        xa, ya = P.pt(g['x_range'][0], g['surface_y'])
        xb, _ = P.pt(g['x_range'][1], g['surface_y'])
        x0, x1 = min(xa, xb), max(xa, xb)
        # the plane meets the front at the front's painted top edge (median top row over the surface's x range,
        # measured on the placed layer), not at the affordance's surface_y (viewed: a gap showed between them)
        al = front_el.layer[..., 3] > 40
        tops = [np.nonzero(al[:, x])[0].min() for x in range(max(0, int(x0)), min(W, int(x1))) if al[:, x].any()]
        if tops:
            ya = float(np.median(tops))
        x0, x1 = max(x0, float(front_el.info['stage_bbox'][0])), min(x1, float(front_el.info['stage_bbox'][0] + front_el.info['stage_bbox'][2]))
        yl = front_el.info['line_y']
        m = front_el.info['persp']
        h_cm = (yl - ya) / (PX_PER_CM * m)
        Zf = z_of(yl)
        Zb = Zf + depth_cm
        yb = y_of(Zb, h_cm)
        bx = lambda x: self.vpx + (x - self.vpx) * Zf / Zb
        crop = self.card_interior(top_rec)
        ch, cw = crop.shape[:2]
        src = np.float32([[0, 0], [cw, 0], [cw, ch], [0, ch]])
        dst = np.float32([[bx(x0), yb], [bx(x1), yb], [x1, ya + 1], [x0, ya + 1]])
        c = crop.copy()
        c[..., 3] = 255
        lay = cv2.warpPerspective(c, cv2.getPerspectiveTransform(src, dst), (W, H), flags=cv2.INTER_LINEAR,
                                  borderMode=cv2.BORDER_CONSTANT, borderValue=(0, 0, 0, 0))
        e = El(top_rec['id'], 'plane', front_el.z + 0.0002, lay, plane=top_rec['plane'], role='counter top', of=front_el.id,
               front_y=round(ya, 1), back_y=round(yb, 1), band_px=round(ya - yb, 1), depth_cm=depth_cm, height_cm=round(h_cm, 1),
               Z_front_cm=round(Zf, 1), x_front=[round(x0), round(x1)], scale_src='homography onto the counter top plane (inferred depth %d cm)' % depth_cm)
        self.els.append(e)
        e.geo = {'Zf': Zf, 'h': h_cm, 'x0': x0, 'x1': x1}
        return e

    def on_plane(self, prop, top_el, u, setback_cm, role):
        """rest a prop on a counter-top plane, setback_cm behind its front edge, at fraction u along it"""
        g = top_el.geo
        Z = g['Zf'] + setback_cm
        yr = y_of(Z, g['h'])
        x = self.vpx + (g['x0'] + u * (g['x1'] - g['x0']) - self.vpx) * g['Zf'] / Z
        e = self.piece(prop, x, 0.0, role, line=yr, z=top_el.z + 0.0005 + 0.0001 * u, m=Z0_CM / Z)
        e.kind = 'prop'
        e.info.update(rests_on=top_el.id, surface={'setback_cm': setback_cm, 'stage_y': round(yr, 1),
                                                   'plane_front_y': top_el.info['front_y'], 'plane_back_y': top_el.info['back_y'],
                                                   'x_range_stage': [round(self.vpx + (g['x0'] - self.vpx) * g['Zf'] / Z), round(self.vpx + (g['x1'] - self.vpx) * g['Zf'] / Z)]})
        self.constraints.append((e.id, top_el.id, 'prop drawn over the counter top it rests on'))
        return e

    def on_surface(self, prop, support, u, role, d_off=0.0005):
        """rest a prop on the support's surface affordance at fraction u of the surface x_range"""
        sa = next(a for a in support.info['placed'].rec['affordances'] if a['kind'] == 'surface')
        g = sa['geometry']
        P = support.info['placed']
        ry = g.get('rest_y', g['surface_y'])
        x0, x1 = g['x_range']
        sx, sy = P.pt(x0 + u * (x1 - x0), ry)
        e = self.piece(prop, sx, support.info['d'], role, line=sy, z=support.z + d_off, m=support.info['persp'])
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
                if rec.get('anchor') in ('floor', 'door'):
                    sh = self.shadow_for(lay, rec['planned_line'], rec.get('persp', 1.0), None, A.name, 0.38)
                    if sh is not None:
                        items.append((-4, A.name + '#shadow', sh, El(A.name + '#shadow', 'shadow', -4, sh)))
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

    GLASSES_CUT = 0.02       # CLIP glasses score: on above, off below (measured gap: 07-hello -0.007, every other poet drawing >= 0.042)
    TWEEN = 4                # dissolve in-between frames into a seat (no lowering drawing exists: measured hip ratios)
    HANDS_LIKE = {'wave': ('wave', 'palms-up')}   # a greeting that stays inside a door (viewed: open-up V crossed the jamb)

    def __init__(self, stage, cast, sheet, x_cm, d, name):
        self.st, self.c, self.sheet, self.name = stage, cast, sheet, name
        self.cx = x_cm * PX_PER_CM
        self.d0 = d
        self.frames = [(b, i) for b in sheet for i in range(b['hold'])]
        self.cache = {}
        self._last_floor = None
        self.continuity = self._resolve()

    def _resolve(self):
        """repair v2, continuity across swaps (measured per drawing, repair/actors.py):
        accessories: every beat's drawing must match the first beat's on the CLIP glasses score (within
        GLASSES_TOL); a mismatch is swapped for a same-posture drawing that matches, preferring the same
        hands (or a greeting family for a wave), then the nearest pose (select.pose_dist).
        outline: if the drawings in the sheet disagree on a sticker halo (one 0 px, another >= 2 px), the halo
        is stripped from all of them (only near-white edge pixels), so a swap never changes the outline."""
        subs = []
        ref = None
        for b in self.sheet:
            d, mir = self.c.get(b['d'])
            if d is None:
                continue
            g = actmeas.measure(d).get('glasses', {}).get('score')
            if ref is None:
                ref = (d, g)
                continue
            on = lambda v: v > self.GLASSES_CUT
            if g is None or ref[1] is None or on(g) == on(ref[1]):
                continue
            gs = lambda x: actmeas.measure(x).get('glasses', {}).get('score')
            cand = [x for x in self.c.lib if x.cls == d.cls and x.id != d.id and gs(x) is not None and on(gs(x)) == on(ref[1])]
            hands = d.cat.get('hands')
            fam = self.HANDS_LIKE.get(hands, (hands,))
            cand.sort(key=lambda x: (fam.index(x.cat.get('hands')) if x.cat.get('hands') in fam else 9, sel.pose_dist(d.ang, x.ang)[0]))
            if cand:
                new = cand[0].id.split('/')[-1] + ('~' if mir else '')
                subs.append({'beat': b.get('name'), 'was': b['d'], 'now': new, 'why': f'glasses score {g:.3f} vs first beat {ref[1]:.3f} (other side of {self.GLASSES_CUT})',
                             'now_glasses': round(gs(cand[0]), 3), 'now_hands': cand[0].cat.get('hands')})
                b['d_was'] = b['d']
                b['d'] = new
        actmeas.save()
        used = {}
        for b in self.sheet:
            d, mir = self.c.get(b['d'])
            if d is not None and d.id not in used:
                used[d.id] = actmeas.halo(d)['halo_px']
        hv = list(used.values())
        self.strip = max(hv) if hv and max(hv) >= 2 and min(hv) == 0 else 0
        return {'substitutions': subs, 'halo_px_by_drawing': used, 'halo_stripped_px': self.strip,
                'halo_rule': 'strip from all' if self.strip else 'consistent (no strip)'}

    def img_of(self, d, mir):
        key = (d.id, mir, self.strip)
        if key not in self.cache:
            img = d.image()
            if self.strip:
                img = actmeas.strip_halo(img, self.strip)
            self.cache[key] = img[:, ::-1] if mir else img
        return self.cache[key]

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
        img = self.img_of(d, mir)
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
        guard_s = s
        if 'seat' in b:
            seat_el = b['seat']
            s = guard_s * seat_el.info['persp']
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
            s = guard_s * persp(yl)
            tx = self.cx - s * gx
            ty = yl - s * low + dip - bob
            z = b.get('z', dd)
            rec.update(anchor='door' if 'door' in b else 'floor', planned_line=yl, depth=dd)
        key = (d.id, mir, round(tx, 2), round(ty, 2), round(s, 5))
        lay = warp(img, s, tx, ty)
        ys, xs = np.nonzero(lay[..., 3] > 40)
        if guard:
            rec['height_guard'] = guard
        mp = s / guard_s
        tp = {}
        for k in ('neck', 'groin'):
            if k in d.m:
                px_ = d.m[k][0] if not mir else d.w - d.m[k][0]
                tp[k] = [round(float(tx + s * px_), 1), round(float(ty + s * d.m[k][1]), 1)]
        rec.update(z=z, scale=round(float(s), 4), persp=round(float(mp), 4), torso_pts=tp,
                   height_cm_back_line=round(float((ys.max() - ys.min()) / PX_PER_CM / mp), 1) if len(ys) else None, centre_px=round(float(self.cx), 1), dip=dip, bob=round(bob, 2),
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
            if i < self.TWEEN and self._last_floor is not None:
                # dissolve in-between (repair v2): the last standing layer slides toward the seat and fades out
                # while the seated drawing fades in, over TWEEN frames (critic: the sit was a pop cut)
                f_ = (i + 1) / (self.TWEEN + 1)
                prev, pcx = self._last_floor
                M = np.float32([[1, 0, (self.cx - pcx) * f_], [0, 1, 0]])
                pv = cv2.warpAffine(prev, M, (W, H), borderMode=cv2.BORDER_CONSTANT, borderValue=(0, 0, 0, 0)).astype(np.float32)
                sv = lay.astype(np.float32)
                pa, sa = pv[..., 3:] / 255. * (1 - f_), sv[..., 3:] / 255. * f_
                oa = pa + sa * (1 - pa)
                rgb = (pv[..., :3] * pa + sv[..., :3] * sa * (1 - pa)) / np.maximum(oa, 1e-6)
                lay = np.dstack([rgb, oa * 255]).clip(0, 255).astype(np.uint8)
                rec.update(anchor='tween', tween={'frac_seated': round(f_, 2), 'of': self.TWEEN})
        else:
            self._last_floor = (lay, self.cx)
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
            if r['anchor'] == 'tween':
                continue
            if r['anchor'] == 'seat':
                if r.get('seat_err_px') is not None:
                    seat_errs.append(r['seat_err_px'])
            else:
                errs.append(r['low_px'] - (r['planned_line'] + r['dip'] - r['bob']))
        out['contact'].append({'id': 'actor:' + A.name, 'role': 'actor', 'feet_line_err_px_max': round(float(np.max(np.abs(errs))), 2) if errs else None,
                               'seat_err_px_median': round(float(np.median(seat_errs)), 1) if seat_errs else None,
                               'off_ground': any(samples['recs'][f][A.name].get('anchor') not in ('seat', 'tween') and
                                                 not (GROUND_TOP - 12 <= samples['recs'][f][A.name].get('planned_line', GROUND_TOP) <= H) for f in range(len(A)))})
    # 2. scale: actor standing height vs each real-size furniture/flat, against the expectation
    for A in stg.actors:
        # repair v2: heights are taken back to the back line (divided by the frame's perspective scale)
        hs = [samples['recs'][f][A.name]['height_cm_back_line'] for f in range(len(A))
              if samples['recs'][f][A.name].get('cls') == 'stand' and samples['recs'][f][A.name].get('height_cm_back_line')]
        if not hs:
            hs = [samples['recs'][f][A.name]['height_cm_back_line'] for f in range(len(A)) if samples['recs'][f][A.name].get('height_cm_back_line')
                  and samples['recs'][f][A.name].get('anchor') not in ('seat', 'tween')]
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
                meas_cm = o[3] * e.info['k'] / PX_PER_CM / e.info.get('persp', 1.0)
                exp_cm, what = DOOR_CM, 'door opening h'
            else:
                bb = e.info['stage_bbox']
                meas_cm = (bb[3] if ex_['dim'] == 'h' else bb[2]) / PX_PER_CM / e.info.get('persp', 1.0)
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
                floor_things.append((eid, r['planned_line'] if r['anchor'] not in ('seat', 'tween') else None, lay))
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
        elif obj.kind not in ('piece', 'prop'):
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
        want = (f % 2 == 0) or f == still_f
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
def solid_spans(wall_el, y0, y1, margin=100):
    """column runs of the placed wall that are solid paint (alpha > 200 in >= 97% of rows y0..y1), within the
    frame minus a margin (measured on the stage layer)"""
    a = wall_el.layer[int(y0):int(y1), :, 3] > 200
    solid = a.mean(0) >= 0.97
    spans, x = [], margin
    while x < W - margin:
        if solid[x]:
            x0 = x
            while x < W - margin and solid[x]:
                x += 1
            spans.append((x0, x))
        x += 1
    return spans


def entrance_walk(cast):
    """the walk drawing that reaches least ahead of its torso (actors.measure lead, measured): an arm thrown
    forward is what shows first from behind a jamb and reads as a floating limb (critic, p01)"""
    walks = [d for d in cast.lib if d.cls == 'walk']
    best = min(walks, key=lambda d: actmeas.measure(d)['lead'])
    return best.id.split('/')[-1], {d.id.split('/')[-1]: actmeas.measure(d)['lead'] for d in walks}


def scene_bar(poem, C):
    """the house bar: a man behind a bar (front + top plane), standing in front of solid wall with room
    between him and the counter, bottles on the counter top, a woman dancing downstage"""
    st = Stage(f'p{poem}_bar', poem)
    B = st.book
    wall = B.find('back wall (with an opening)', pick=all_of(need_size, need_window), poem=poem,
                  category=['architecture', 'aperture'], plane='mid_set', text='wall')
    w = st.piece(wall, 640, 0.0, 'back wall')
    st.measure_vp(w)
    st.reveals(w)
    st.backdrop(choose_backdrop(st, poem))
    st.ground(choose_floor(st, wall, poem))
    man, woman = C['vintage man'], C['vintage woman']
    # where he stands: the widest solid run of wall at the height his upper body shows (measured)
    spans = solid_spans(w, 150, 380)
    sp = max(spans, key=lambda t: t[1] - t[0])
    man_x = (sp[0] + sp[1]) / 2
    d_man = 0.25
    z_man = z_of(line_y(d_man))
    gap_cm, depth_cm = 20.0, 45.0           # room for his body in front of his feet line; counter depth (inferred)
    z_front = z_man - gap_cm - depth_cm
    d_bar = (y_of(z_front) - GROUND_TOP) / (FRONT - GROUND_TOP)
    st.repair['behind_counter_plan'] = {'solid_spans_px': spans, 'man_x': man_x, 'd_man': d_man, 'Z_man_cm': round(z_man, 1),
                                        'Z_wall_cm': round(Z0_CM, 1), 'Z_counter_back_cm': round(z_man - gap_cm, 1),
                                        'Z_counter_front_cm': round(z_front, 1), 'd_counter': round(d_bar, 3),
                                        'man_to_wall_cm': round(Z0_CM - z_man, 1)}
    bar = B.find('counter with a surface', pick=all_of(need_size, no_flags('label_doubt')), poem=poem,
                 category='furniture-surface', affordance='surface', min_aff_conf=0.6, text='bar')
    # the counter is centred on him unless that would push it off the frame (its width measured before placing)
    bw_ = image(bar)[1][2] * resolve_scale(bar)['k'] * persp(line_y(d_bar))
    cx_bar = min(max(man_x, bw_ / 2 + 20), W - bw_ / 2 - 20) if bw_ < W - 40 else W / 2
    b = st.piece(bar, cx_bar, d_bar, 'counter')
    st.add_shadow(b)

    def flat_top(r):
        bb = image(r)[1]
        ok = bb[2] >= 4 * bb[3] and any(a['kind'] == 'surface' and a['confidence'] >= 0.9 for a in r['affordances'])
        return ok, f'w/h {bb[2] / bb[3]:.1f}, surface affordance >= 0.9: {ok}'
    top = B.find('counter top plane (same sheet)', pick=flat_top, sheet=bar['sheet'], affordance='surface', min_aff_conf=0.9)
    t = st.counter_top(b, top, depth_cm)
    bottles = B.find('props for the counter top', pick=need_size, n=3, poem=poem, category='handheld-prop',
                     affordance='grip', contact='rests', text='bottle')
    g = t.geo
    us = [u for u in (0.08, 0.16, 0.24, 0.84, 0.92) if 60 < g['x0'] + u * (g['x1'] - g['x0']) < W - 60
          and abs(g['x0'] + u * (g['x1'] - g['x0']) - man_x) > 90]
    for u, r in zip(us[:2] + us[-1:], bottles):
        st.on_plane(r, t, u, 20.0, 'prop on counter')
    stand = 'view:front/stand'
    st.actor(man, [{'d': stand, 'hold': 44, 'name': 'tends bar'},
                   {'d': 'view:q3/dance', 'hold': 30, 'bob': 4, 'bob_period': 10, 'settle': True, 'name': 'sways to the music'},
                   {'d': stand, 'hold': 46, 'name': 'back to the bar'}], man_x / PX_PER_CM, d_man, man.name)
    ring = woman.ring('q3', 1.0, cls='dance')
    sheet = [{'d': ring[0], 'hold': 18, 'name': 'hold'}] + [{'d': k, 'hold': 3, 'name': 'spin 1'} for k in ring[1:]] + \
            [{'d': ring[0], 'hold': 16, 'name': 'land'}] + [{'d': k, 'hold': 2, 'name': 'spin 2', 'settle': False} for k in ring[1:]] + \
            [{'d': ring[0], 'hold': 120 - 18 - 21 - 16 - 14, 'name': 'end'}]
    st.actor(woman, sheet, 190 / PX_PER_CM, 0.95, woman.name)
    st.constraints.append((b.id, man.name, 'actor stands behind the counter: its front hides his legs'))
    st.constraints.append((t.id, man.name, 'the counter top plane is in front of the man behind it'))
    st.interactions.append({'type': 'behind counter', 'actor': man.name, 'piece': b.id, 'top': t.id,
                            'counter_top_y': t.info['back_y'], 'counter_front_top_y': t.info['front_y']})
    st.interactions.append({'type': 'props on surface', 'pieces': [r['id'] for r in bottles], 'surface': t.id})
    return st, 120


def scene_parlour(poem, C):
    """a living room: the poet walks in and sits in an armchair (seat line), its front arm in front of him;
    a phone rests on a side table set clear of his feet; the wall's window shows the set's own sky"""
    st = Stage(f'p{poem}_parlour', poem)
    B = st.book
    wall = B.find('back wall with a window', pick=all_of(need_size, need_window), poem=poem,
                  category=['architecture', 'aperture'], plane='mid_set', text='wall window')
    w = st.piece(wall, 640, 0.0, 'back wall')
    st.measure_vp(w)
    st.reveals(w)
    st.backdrop(choose_backdrop(st, poem))
    st.ground(choose_floor(st, wall, poem))
    poet = C['poet']
    sk = seated_key(poet)
    chair = B.find('seat for a sitter', pick=all_of(need_size, no_flags('size_doubt', 'label_doubt')), poem=poem,
                   category='furniture-seat', affordance='seat', min_aff_conf=0.8)
    ch = st.piece(chair, 760, 0.45, 'seat')
    st.add_shadow(ch)
    ov = None
    try:
        ovr = B.find('front overlay of the seat', sheet=chair['sheet'], text='overlay')
        ov = st.piece(ovr, ch.info['placed'].pt(image(chair)[1][0] + image(chair)[1][2], 0)[0], 0.45, 'overlay',
                      k=ch.info['k'], scale={'src': 'same sheet pixel scale as the seat', 'k': ch.info['k'],
                                             'basis': 'catalog bbox px == webp px for both parts (measured); position: bottom on the seat contact line, right edge on the seat right edge (inferred, template match failed: rms 57)'},
                      z=ch.z + 0.002, anchor='right')
    except RuntimeError:
        pass
    walk, leads = entrance_walk(poet)
    seat_x = ch.info['stage_bbox'][0] + 0.42 * ch.info['stage_bbox'][2]
    walk_cm = (seat_x - 15 * PX_PER_CM) / PX_PER_CM - 60
    sheet = [{'d': walk, 'hold': 44, 'move_cm': walk_cm, 'bob': 5, 'bob_period': 11, 'settle': False, 'name': 'walks in'},
             {'d': 'arrive-01-in-file', 'hold': 12, 'name': 'stops by the chair'}]
    seat_beat = {'d': sk, 'hold': 64, 'seat': ch, 'seat_u': 0.42, 'name': 'sits'} if sk else None
    if seat_beat:
        sheet.append(seat_beat)
    else:
        sheet.append({'d': 'view:front/stand', 'hold': 64, 'name': 'no seated painting: stands'})
    # the side table goes clear of the seated figure (measured: a probe render of the seated beat alone)
    feet_r = ch.info['stage_bbox'][0] + ch.info['stage_bbox'][2]
    if seat_beat:
        probe = StageActor(st, poet, [dict(seat_beat, hold=1)], 0, 0.5, 'probe')
        _, pr = probe.layer(0)
        feet_r = max(feet_r, pr['bbox'][0] + pr['bbox'][2])
    table = B.find('side table with a surface', pick=need_size, poem=poem, category='furniture-surface',
                   affordance='surface', text='table')
    t = st.piece(table, feet_r + 18, 0.36, 'side table', anchor='left')
    st.add_shadow(t)
    st.repair['table_clearance'] = {'seated_right_px': round(feet_r, 1), 'table_left_px': t.info['stage_bbox'][0]}
    srf = next(a for a in table['affordances'] if a['kind'] == 'surface')['geometry']
    sw = abs(srf['x_range'][1] - srf['x_range'][0]) * t.info['k']

    def fits(r):
        s_ = resolve_scale(r)
        if not s_:
            return False, 'no size'
        bw, bh = image(r)[1][2:]
        pw = bw * s_['k'] * t.info['persp']
        ok = pw <= 0.9 * sw and bw >= 0.5 * bh
        return ok, f'width {pw:.0f}px vs surface {sw:.0f}px, w/h {bw / bh:.2f} ({s_["src"]})'
    phone = B.find('prop resting on the side table', pick=fits, poem=poem, category='handheld-prop', text='phone',
                   contact=['rests', 'stands'])
    st.on_surface(phone, t, 0.5, 'prop on side table')
    A = st.actor(poet, sheet, 60, 0.5, poet.name)
    A.leads = leads
    seated = lambda recs: recs[poet.name].get('anchor') == 'seat'
    st.constraints.append((poet.name, ch.id, 'a sitter is in front of the seat body and back (while seated)', seated))
    if ov:
        st.constraints.append((ov.id, poet.name, "the seat's front arm overlay is in front of the sitter (while seated)", seated))
    st.interactions.append({'type': 'sit', 'actor': poet.name, 'seat': ch.id, 'seated_painting': sk,
                            'seat_affordance': seat_affordance(chair)})
    st.interactions.append({'type': 'props on surface', 'pieces': [phone['id']], 'surface': t.id})
    return st, 120


def scene_hall(poem, C):
    """a bedroom wall with a hall door: the hall behind is closed by its own far door (same sheet) and floored
    by the room's floor plane carried back under the door; the poet walks along behind the wall, stops in
    the doorway and greets; a woman stands downstage with her back to us"""
    st = Stage(f'p{poem}_doorway', poem)
    B = st.book
    wall = B.find('wall with a door opening', pick=need_door, poem=poem, category='aperture', affordance='aperture',
                  text='wall')
    w = st.piece(wall, 600, 0.0, 'wall with door')
    st.measure_vp(w)
    st.reveals(w, z=-0.1)
    door = w.info['scale']['opening']
    dr = w.info['placed'].rect(door['rect'])
    dcx = dr[0] + dr[2] / 2
    hall = B.find('hall seen through the door', pick=need_size, poem=poem, category='aperture', text='corridor')
    he = st.piece(hall, dcx, -0.14, 'behind-flat')
    # an opening in a flat must resolve to something opaque from the same set (critic: sky under his feet)
    y_back = he.info['line_y']
    hops = openings(hall)
    closure = None
    if hops:
        hr = he.info['placed'].rect(hops[0]['rect'])

        def closes(r):
            bb = image(r)[1]
            ok = r['id'] != hall['id'] and not openings(r) and bb[3] > 1.2 * bb[2]
            return ok, f"own openings {len(openings(r))}, h/w {bb[3] / bb[2]:.2f}"
        crec = B.find('closure for the hall opening (same sheet)', pick=closes, sheet=hall['sheet'],
                      category=['aperture', 'architecture'], text='door')
        cb = image(crec)[1]
        k = max(hr[3] / cb[3], hr[2] / cb[2]) * 1.02
        closure = st.piece(crec, hr[0] + hr[2] / 2, -0.2, 'behind-flat', k=k, line=hr[1] + hr[3], z=-0.2,
                           scale={'src': 'fit to the hall opening', 'k': k, 'basis': 'covers the measured opening of the hall flat (its distance is implied by the fit)'})
        y_back = min(y_back, hr[1] + hr[3])
        st.repair['hall_closure'] = {'hall': hall['id'], 'hall_opening_stage': [round(v, 1) for v in hr], 'closure': crec['id'],
                                     'k': round(k, 4), 'implied_persp': round(k / (resolve_scale(crec, prefer_door=False) or {'k': k})['k'], 3)}
    st.backdrop(choose_backdrop(st, poem))
    st.ground(choose_floor(st, wall, poem), y_top=y_back - 4)
    poet, woman = C['poet'], C['vintage woman']
    walk, leads = entrance_walk(poet)
    sheet = [{'d': walk, 'hold': 42, 'move_cm': 175, 'bob': 5, 'bob_period': 10, 'settle': False, 'name': 'walks along the hall'},
             {'d': 'arrive-01-in-file', 'hold': 26, 'name': 'stops in the doorway'},
             {'d': '07-hello', 'hold': 52, 'name': 'waves'}]
    A = st.actor(poet, sheet, dcx / PX_PER_CM - 175, -0.04, poet.name)
    A.leads = leads
    st.actor(woman, [{'d': 'view:back/stand', 'hold': 64, 'name': 'waits, back to us'},
                     {'d': 'view:back3q/dance', 'hold': 56, 'name': 'turns toward him'}], 300 / PX_PER_CM, 0.7, woman.name)
    st.constraints.append((w.id, poet.name, 'actor in the doorway: the wall around the opening is in front of him'))
    st.constraints.append((poet.name, hall['id'], 'actor in the doorway is in front of the hall behind'))
    if closure:
        st.constraints.append((hall['id'], closure.id, 'the hall flat is in front of the door that closes it'))
    st.interactions.append({'type': 'stand in doorway', 'actor': poet.name, 'wall': w.id, 'opening_stage_rect': [round(v, 1) for v in dr],
                            'opening_floor_y': round(dr[1] + dr[3], 1)})
    st.interactions.append({'type': 'entrance', 'actor': poet.name, 'walk': walk, 'walk_leads': leads})
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
                pm = el.info.get('persp', 1.0)
                r['feet_below_seat_contact_cm'] = round((x['low_px'] - el.info['line_y']) / PX_PER_CM / pm, 1)
                r['note_feet'] = 'positive = the feet reach lower than the chair legs: on the toy-theatre floor that reads as feet set forward of the chair'
                r['seat_height_cm_chair'] = round((el.info['line_y'] - x['seat_line_y']) / PX_PER_CM / pm, 1)
                r['seat_to_feet_cm_painting'] = round((x['low_px'] - x['seat_line_y']) / PX_PER_CM / pm, 1)
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
                if not len(ys):
                    r['contact'].append({'id': pid, 'off_frame': True})
                    continue
                xr = e.info['surface']['x_range_stage']
                r['contact'].append({'id': pid, 'bottom_y': int(ys.max()), 'rest_y': e.info['surface']['stage_y'],
                                     'err_px': round(float(ys.max() - e.info['surface']['stage_y']), 1),
                                     'within_surface_x': bool(min(xr) <= xs.mean() <= max(xr))})
        out.append(r)
    return out


# ------------------------------------------------------------------ repair v2: the critic's repair conditions, measured
BANDS = {'seat': (0.50, 0.65, 'seat-height piece, top of back / standing actor'),
         'counter': (0.55, 0.65, 'counter top / standing actor'),
         'side table': (0.30, 0.40, 'side table / standing actor')}


def repair_checks(st, samples):
    out = {}
    recs = samples['recs']
    # 1. furniture against the actor, both taken back to the back line (divide by each one's perspective scale)
    rows = []
    for A in st.actors:
        hs = [r[A.name]['height_cm_back_line'] for r in recs if r[A.name].get('cls') == 'stand' and r[A.name].get('anchor') in ('floor', 'door')
              and r[A.name].get('height_cm_back_line')]
        if not hs:
            continue
        act = float(np.median(hs))
        for e in st.els:
            role = e.info.get('role')
            if e.kind != 'piece' or role not in BANDS:
                continue
            if role == 'counter':
                top = next((x for x in st.els if x.info.get('of') == e.id and x.kind == 'plane'), None)
                h_px = e.info['line_y'] - (top.info['front_y'] if top else e.info['stage_bbox'][1])
            else:
                h_px = e.info['line_y'] - e.info['stage_bbox'][1]
            h_cm = h_px / PX_PER_CM / e.info['persp']
            lo, hi, what = BANDS[role]
            rows.append({'actor': A.name, 'actor_cm_back_line': round(act, 1), 'piece': e.id, 'role': role, 'piece_cm_back_line': round(h_cm, 1),
                         'ratio': round(h_cm / act, 3), 'band': [lo, hi], 'what': what, 'holds': lo <= h_cm / act <= hi})
    out['furniture_vs_actor'] = rows
    # 2. seated: hips on the seat line, head above the back, boots near the chair's front base line
    for it in st.interactions:
        if it['type'] != 'sit':
            continue
        A = next(a for a in st.actors if a.name == it['actor'])
        el = next(e for e in st.els if e.id == it['seat'])
        seated = [r[A.name] for r in recs if r[A.name].get('anchor') == 'seat']
        stand = [r[A.name] for r in recs if r[A.name].get('cls') == 'stand' and r[A.name].get('anchor') == 'floor']
        tw = [r[A.name] for r in recs if r[A.name].get('anchor') == 'tween']
        if seated:
            x = seated[-1]
            act_px_here = float(np.median([s_['height_cm_back_line'] for s_ in stand])) * PX_PER_CM * el.info['persp'] if stand else None
            head_above = el.info['stage_bbox'][1] - x['bbox'][1]
            out['seated'] = {'seat_err_px': x.get('seat_err_px'), 'seat_err_ok(<=15)': x.get('seat_err_px') is not None and abs(x['seat_err_px']) <= 15,
                             'head_above_back_px': head_above, 'actor_standing_px_at_chair_depth': round(act_px_here, 1) if act_px_here else None,
                             'head_above_back_frac': round(head_above / act_px_here, 3) if act_px_here else None,
                             'boots_vs_chair_base_px': round(x['low_px'] - el.info['line_y'], 1),
                             'boots_ok(<=40)': abs(x['low_px'] - el.info['line_y']) <= 40,
                             'tween_frames': len(tw), 'tween_ok(>=3)': len(tw) >= 3}
            out['seated']['head_ok(<=0.35)'] = out['seated']['head_above_back_frac'] is not None and out['seated']['head_above_back_frac'] <= 0.35
    # 3. floor: periodicity of the floor layer (high-passed autocorrelation peak along x, shifts 20 px..W/2)
    fl = next(e for e in st.els if e.kind == 'ground')
    band = fl.layer[GROUND_TOP + 2:H]
    out['floor'] = {'id': fl.id, 'periodicity_x_floor_layer': palette.periodicity(band, 1, 20 / W, 0.5),
                    'tiles': fl.info.get('tiles'), 'choice': st.repair.get('floor_choice', {}).get('ranked', [{}])[:3],
                    'palette_dist_to_wall': (st.repair.get('floor_choice', {}).get('ranked') or [{}])[0].get('palette_dist')}
    # 4. vanishing point
    out['vanishing_point'] = st.repair.get('vanishing_point')
    # 5. openings: reveal depth, fills
    out['reveals'] = [{'wall': r['wall'], 'openings': [{'rect': o['opening_stage_rect'], 'door': o['door'], 'max_face_px': o['max_face_px'],
                                                         'faces': o['faces'], 'sill_cm': o['sill_cm_above_floor'], 'ok(>=8px)': o['max_face_px'] >= 8}
                                                        for o in r['openings']]} for r in st.repair.get('reveals', [])]
    out['fill'] = st.repair.get('backdrop')
    out['flat_fix'] = {e.id: {k: v for k, v in FLAT_FIX.get(e.id, {}).items() if k != 'border_evidence'} for e in st.els if e.id in FLAT_FIX}
    # 6. depth ladder: lower feet (nearer) never shorter than higher feet (farther) by more than 5%
    lad = []
    names = [a.name for a in st.actors]
    for f, r in enumerate(recs):
        for a in names:
            for b in names:
                ra, rb = r[a], r[b]
                if a == b or ra.get('gap') or rb.get('gap') or ra.get('anchor') not in ('floor', 'door') or rb.get('anchor') not in ('floor', 'door'):
                    continue
                if ra['planned_line'] > rb['planned_line'] + 4:
                    nom_a = st.actors[names.index(a)].c.height_cm * ra['persp']
                    nom_b = st.actors[names.index(b)].c.height_cm * rb['persp']
                    lad.append({'frame': f, 'near': a, 'far': b, 'painted_ratio': round(ra['bbox'][3] / rb['bbox'][3], 3),
                                'nominal_ratio': round(nom_a / nom_b, 3)})
    if lad:
        out['depth_ladder'] = {'pairs': len(lad), 'min_nominal_ratio': min(x['nominal_ratio'] for x in lad),
                               'min_painted_ratio': min(x['painted_ratio'] for x in lad),
                               'worst_painted': min(lad, key=lambda x: x['painted_ratio']),
                               'ok_nominal(>=0.95)': min(x['nominal_ratio'] for x in lad) >= 0.95}
    # 7. entrances / partial visibility: any partly hidden actor frame must show a grounded part or the torso
    ent = []
    for f, (items, ids) in sorted(samples['ids'].items()):
        idx = {it[1]: n for n, it in enumerate(items)}
        for A in st.actors:
            if A.name not in idx:
                continue
            r = recs[f][A.name]
            al = items[idx[A.name]][2][..., 3] > 127
            vis = al & (ids == idx[A.name])
            nv, na = int(vis.sum()), int(al.sum())
            if nv < 40 or nv > 0.98 * na:
                continue
            ys, xs = np.nonzero(vis)
            grounded = bool(ys.max() >= r['low_px'] - 8)
            torso = any(0 <= p[0] < W and 0 <= p[1] < H and vis[int(p[1]), int(p[0])] for p in r.get('torso_pts', {}).values())
            # rule: if the torso shows (a visible component within 12 px of the neck or pelvis marker), other
            # visible parts are cut by an occluder in front of a visible body: fine. If the torso is hidden, every
            # visible part must reach the floor (a leg stepping in); a part that does not is a floating limb.
            n, lab, stt, _ = cv2.connectedComponentsWithStats(vis.astype(np.uint8), 8)
            float_px = 0
            tor_comp = False
            for i in range(1, n):
                if stt[i, 4] <= 40:
                    continue
                yy, xx = np.nonzero(lab == i)
                for p in r.get('torso_pts', {}).values():
                    if np.min((xx - p[0]) ** 2 + (yy - p[1]) ** 2) <= 144:
                        tor_comp = True
            torso = torso or tor_comp
            # (viewed, v2 run 1) a leg stepping in is often split by a nearer actor's dress into pieces that do not
            # reach the floor, and a hand swinging beside the stepping leg is normal. So a frame is a floating-limb
            # frame only when the torso is hidden AND no visible part reaches the floor (v1 p01 f18-20: the arm alone).
            big = [i for i in range(1, n) if stt[i, 4] > 40]
            any_grounded = any(stt[i, 1] + stt[i, 3] - 1 >= r['low_px'] - 8 for i in big)
            if not torso and not any_grounded:
                float_px = int(sum(stt[i, 4] for i in big))
            ent.append({'frame': f, 'actor': A.name, 'visible_frac': round(nv / na, 3), 'grounded': grounded, 'torso_visible': torso,
                        'floating_px': float_px})
    out['partial_visibility'] = {'frames': len(ent), 'floating_frames': [e for e in ent if e['floating_px'] > 0],
                                 'ok': not any(e['floating_px'] > 0 for e in ent), 'all': ent}
    # 8. continuity
    out['continuity'] = {A.name: A.continuity for A in st.actors}
    # 9. behind counter
    if 'behind_counter_plan' in st.repair:
        pl = st.repair['behind_counter_plan']
        top = next(e for e in st.els if e.kind == 'plane')
        wall = next(e for e in st.els if e.info.get('role') == 'back wall')
        hole = np.zeros((H, W), bool)
        for o in openings(wall.info['placed'].rec):
            x, y, w_, h_ = wall.info['placed'].rect(o['rect'])
            hole[int(y):int(y + h_), int(x):int(x + w_)] = True
        fr = []
        for f, (items, ids) in samples['ids'].items():
            idx = {it[1]: n for n, it in enumerate(items)}
            nm = 'vintage man'
            if nm in idx:
                vis = (items[idx[nm]][2][..., 3] > 127) & (ids == idx[nm])
                if vis.sum():
                    fr.append(float((vis & hole).sum()) / vis.sum())
        out['behind_counter'] = dict(pl, counter_top_band_px=top.info['band_px'],
                                     man_visible_over_openings_frac_max=round(max(fr), 3) if fr else None,
                                     floor_visible_behind_counter_px=0,
                                     note='eye 150 cm above a 105 cm counter: the floor behind it is hidden by geometry; no back-bar piece exists in the registry (query shelf/cabinet/sideboard/dresser/rack: none usable)')
    return out


def run(only=None):
    os.makedirs(OUT, exist_ok=True)
    rank = richness()
    top = [r['poem'] for r in rank[:3]]
    C = casts()
    summary = {'richness': rank, 'chosen_poems': top, 'scenes': {}}
    del RUN_FILLS[:]
    for poem, fn in zip(top, SCENES):
        if only and only not in fn.__name__:
            continue
        st, n = fn(poem, C)
        samples = shoot(st, n)
        checks = check_scene(st, samples)
        checks['interactions'] = measure_interactions(st, samples)
        checks['occlusion']['negative_control'] = negative_control(st)
        checks['repair'] = repair_checks(st, samples)
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
             'interactions': checks['interactions'], 'repair': {k: v for k, v in checks['repair'].items() if k not in ('flat_fix',)}}
        s['repair']['partial_visibility'] = {k: v for k, v in s['repair']['partial_visibility'].items() if k != 'all'}
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
