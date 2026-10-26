"""Export every playable character to a mobile web game bundle.

    python3 -m studio.game.build_game <out_dir>          (run from shots/scion2)

For each character in cast_plan.json, collects its clean whole-figure drawings (the rig library where a
rig module exists, plus the cast plan's masters), reads each drawing's geometry from its markers (body
length for one size per character, the pelvis as the anchor, facing, leg spread, arm reach), crops it to
its alpha, shrinks it for phones and writes webp + data.json. A character with no drawing is listed as
locked with the reason. Also exports a few set backdrops from the set-piece registry.

The game (play/index.html) animates only by swapping these whole drawings: nothing is bent.
"""
import json, math, os, re, sys
import numpy as np, cv2

from rigkit import core
from studio import select as sel

ROOT = core.ROOT
CUT = os.path.join(ROOT, 'shots/kits/cut')
SC2 = os.path.join(ROOT, 'shots/scion2')
MAXH = 460                      # exported drawing height (px): crisp on a phone, small to download
HEIGHT_CM = {'young_poet': 130, 'ghost_child': 125, 'child_traveler': 120, 'elder_man': 165, 'elder_woman': 158, 'elder_1': 160,
             'elders': 160, 'ancestor_elder': 165, 'woman': 165, 'vintage_woman': 166, 'mother': 163, 'angel': 175,
             'poet': 183, 'vintage_man': 177}
BEST_VIEW = {'front': 'front', '3/4': 'q3', 'profile': 'prof', 'back': 'back', 'seated': 'q3', 'kneeling': 'q3'}


def height_of(ch):
    return HEIGHT_CM.get(ch, 175)


def ang(a, b):
    return math.degrees(math.atan2(b[1] - a[1], b[0] - a[0]))


def adiff(a, b):
    return abs((a - b + 180) % 360 - 180)


def read_markers(mod, ids):
    """{painting id: markers} for a character, from its rig module if it has one, else its marker file"""
    out = {}
    if os.path.exists(os.path.join(SC2, 'rigkit/chars', mod + '.py')):
        try:
            out.update({k: v['markers'] for k, v in core.load_markers(mod).items()})
        except Exception:
            pass
    for d in ('shots/rig/poses_v2', 'shots/rig/poses'):
        f = os.path.join(ROOT, d, mod + '.json')
        if os.path.exists(f):
            for t in json.load(open(f)).get('targets', []):
                out.setdefault(t['id'], t['markers'])
    return out


def pt(m, k):
    v = m.get(k)
    return np.array(v[:2], float) if v and (len(v) < 5 or not isinstance(v[4], (int, float)) or v[4] >= 0.2) else None


def geometry(m, w, h):
    """body length px (legs + torso), pelvis x, leg spread, arm reach, facing right?  Any may be None"""
    g = {}
    legs = []
    for s in 'RL':
        a, b, c = pt(m, 'hip' + s), pt(m, 'knee' + s), pt(m, 'ankle' + s)
        if a is not None and b is not None and c is not None:
            legs.append(np.linalg.norm(a - b) + np.linalg.norm(b - c))
    neck, groin = pt(m, 'neck'), pt(m, 'groin')
    hR, hL = pt(m, 'hipR'), pt(m, 'hipL')
    if groin is None and hR is not None and hL is not None:
        groin = (hR + hL) / 2
    torso = np.linalg.norm(neck - groin) if neck is not None and groin is not None else None
    g['body_px'] = (np.mean(legs) * 2 + torso) if legs and torso else None
    g['groin_x'] = float(groin[0]) if groin is not None else None
    tA, tB = pt(m, 'hipR'), pt(m, 'kneeR')
    uA, uB = pt(m, 'hipL'), pt(m, 'kneeL')
    g['spread'] = adiff(ang(tA, tB), ang(uA, uB)) if all(x is not None for x in (tA, tB, uA, uB)) else 0
    arm = 0
    for s in 'RL':
        a, b = pt(m, 'shoulder' + s), pt(m, 'elbow' + s)
        if a is not None and b is not None:
            arm = max(arm, adiff(ang(a, b), 90))
    g['arm_out'] = arm
    chin = pt(m, 'chin')
    g['face_right'] = bool(chin[0] >= neck[0]) if chin is not None and neck is not None else True
    return g


def cls_of(key_view, desc, cat_cls):
    d = (desc or '').lower()
    if cat_cls and cat_cls not in ('', 'stand'):
        return cat_cls
    if key_view == 'seated' or 'seated' in d or 'sit' in d:
        return 'sit'
    if key_view == 'kneeling' or 'kneel' in d:
        return 'kneel'
    for w, c in (('dance', 'dance'), ('walk', 'walk'), ('run', 'run'), ('lean', 'lean'), ('lunge', 'lunge'), ('fall', 'fall'),
                 ('lying', 'lie'), ('crouch', 'crouch'), ('reach', 'reach'), ('point', 'point')):
        if w in d:
            return c
    return cat_cls or 'stand'


def view_of(key_view, cat_view):
    if cat_view:
        if cat_view.startswith('back3q'):
            return 'back3q'
        if cat_view.startswith('back'):
            return 'back'
        if cat_view.startswith(('3q', 'thr')):
            return 'q3'
        if cat_view.startswith('prof'):
            return 'prof'
        if cat_view == 'front':
            return 'front'
    return BEST_VIEW.get(key_view, 'front')


def collect(key, plan_char):
    """[(painting id, desc, view, cls)] for one character"""
    ch, _, co = key.partition('/')
    mod = f'{ch}__{co}'
    items, seen = [], set()
    cat = {}
    if os.path.exists(os.path.join(SC2, 'rigkit/chars', mod + '.py')):
        try:
            spec = core.char_module(mod)
            cat = spec.catalog() if hasattr(spec, 'catalog') else {}
            MK = core.load_markers(mod)
            from collections import Counter
            cos = Counter((cat.get(t, {}) or {}).get('costume') for t in MK).most_common(1)
            lib = sel.library(mod, costume=cos[0][0] if cos and cos[0][0] else None)
            for d in lib:
                if d.id not in seen:
                    seen.add(d.id)
                    items.append((d.id, '', view_of('', d.cat.get('view')), cls_of('', '', d.cls)))
        except Exception as e:
            print('  library failed for', mod, str(e)[:80])
    for kv, ids in plan_char['masters'].items():
        for s in ids:
            m = re.match(r'^(.*?)\s*\((.*)\)\s*$', s)
            pid, desc = (m.group(1), m.group(2)) if m else (s, '')
            if pid in seen or 'reference only' in desc.lower() or 'reference only' in pid:
                continue
            seen.add(pid)
            c = cat.get(pid, {}) or {}
            items.append((pid, desc, view_of(kv, c.get('view')), cls_of(kv, desc, c.get('cls'))))
    return mod, items


def export_drawing(pid, out_dir, name):
    for e in ('.webp', '.png'):
        p = os.path.join(CUT, pid + e)
        if os.path.exists(p):
            im = cv2.imread(p, cv2.IMREAD_UNCHANGED)
            break
    else:
        return None
    if im is None or im.ndim < 3:
        return None
    if im.shape[2] == 3:
        im = np.dstack([im, np.full(im.shape[:2], 255, np.uint8)])
    ys, xs = np.nonzero(im[..., 3] > 24)
    if len(xs) < 50:
        return None
    x0, x1, y0, y1 = xs.min(), xs.max() + 1, ys.min(), ys.max() + 1
    crop = im[y0:y1, x0:x1]
    s = min(1.0, MAXH / crop.shape[0])
    if s < 1:
        crop = cv2.resize(crop, (max(1, round(crop.shape[1] * s)), round(crop.shape[0] * s)), interpolation=cv2.INTER_AREA)
    os.makedirs(out_dir, exist_ok=True)
    fn = name + '.webp'
    cv2.imwrite(os.path.join(out_dir, fn), crop, [cv2.IMWRITE_WEBP_QUALITY, 82])
    return {'file': fn, 'w': crop.shape[1], 'h': crop.shape[0], 'x0': int(x0), 'y0': int(y0), 'scale': s, 'src_wh': (im.shape[1], im.shape[0])}


def run(out):
    plan = json.load(open(os.path.join(SC2, 'cast_plan.json')))
    chars, locked = [], []
    for key, pc in plan['characters'].items():
        ch, _, co = key.partition('/')
        mod, items = collect(key, pc)
        mk = read_markers(mod, [i[0] for i in items])
        cdir = os.path.join(out, 'assets', key.replace('/', '__'))
        draws = []
        for n, (pid, desc, view, cls) in enumerate(items):
            ex = export_drawing(pid, cdir, '%02d' % n)
            if not ex:
                continue
            m = mk.get(pid, {})
            g = geometry(m, *ex['src_wh']) if m else {'body_px': None, 'groin_x': None, 'spread': 0, 'arm_out': 0, 'face_right': True}
            alpha_h = ex['h'] / ex['scale']                       # drawing height in source px
            body = g['body_px'] or 0.72 * alpha_h                # fallback: legs+torso is ~72% of a figure's height
            ax = ((g['groin_x'] - ex['x0']) * ex['scale']) if g['groin_x'] is not None else ex['w'] / 2
            draws.append({'f': ex['file'], 'w': ex['w'], 'h': ex['h'], 'ax': round(float(np.clip(ax, 0, ex['w'])), 1),
                          'body_px': round(float(body * ex['scale']), 1), 'view': view, 'cls': cls,
                          'right': g['face_right'], 'spread': round(float(g['spread']), 1), 'arm': round(float(g['arm_out']), 1),
                          'id': pid, 'measured': bool(g['body_px'])})
        entry = {'key': key, 'name': pc.get('name') or ch.replace('_', ' '), 'who': pc.get('who', ''), 'poems': pc.get('poems', []),
                 'height_cm': height_of(ch), 'draws': draws, 'dir': key.replace('/', '__')}
        if draws:
            chars.append(entry)
        else:
            locked.append({'key': key, 'name': entry['name'], 'who': entry['who'], 'poems': entry['poems'],
                           'reason': 'no clean whole-figure painting exists yet: it needs new paintings before it can be played'})
        print('%-34s %3d drawings' % (key, len(draws)))
    json.dump({'characters': chars, 'locked': locked}, open(os.path.join(out, 'data.json'), 'w'), separators=(',', ':'))
    return chars, locked


if __name__ == '__main__':
    run(sys.argv[1])
