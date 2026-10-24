"""Parts on library2's canonical grid (10 px per cm, pivot at a fixed canvas point, primary axis fixed).

parts(char, costume=None, part=None) -> list of Part dicts:
  key, part, source ('library2' or 'onfly'), img (RGBA uint8 on the canonical canvas, BGRA order), pivot (canvas xy),
  kp {name: xy} (canonical keypoints: head neck/crown/chin/eye_line, torso neck/shoulder_l/r, limb tip, pelvis hips),
  brads (canonical xy array), view (front / three-quarter / side / back / None), facing, side (L / R / None),
  state, character, costume, src_card
library2 parts are read from shots/scion2/library2/index.json (status ok; never modified here). Part types library2 does
not have yet are regularised on the fly the same way from the old library: card anchors from evolve/cards.prep
(limb A = proximal joint, B = distal; hand A wrist; foot A ankle; pelvis waist + hips), uniform scale to 10 px/cm from
the card's px/cm, rotated so pivot -> tip follows the grid's axis; hygiene junk is skipped.
"""
import functools, json, math, os, sys
import numpy as np, cv2

HERE = os.path.dirname(os.path.abspath(__file__))
SC2 = os.path.abspath(os.path.join(HERE, '..', '..'))
LIB2 = os.path.join(SC2, 'library2')
sys.path.insert(0, SC2)
sys.path.insert(0, os.path.join(LIB2, 'tools'))
from common import GRID, CANON_PPC  # noqa: E402  (library2's grid, read-only)
from evolve import library as LB, cards as CD  # noqa: E402
from evolve.puzzle import hygiene as HY  # noqa: E402

VIEW = {'front': 'front', 'threequarter': 'three-quarter', 'side': 'side', 'profile': 'side', 'back': 'back',
        'threequarter_back': 'back', 'three-quarter': 'three-quarter', 'three-quarter-back': 'back'}


def _read(p):
    im = cv2.imread(p, cv2.IMREAD_UNCHANGED)
    if im is None:
        return None
    if im.shape[2] == 3:
        im = np.dstack([im, np.full(im.shape[:2], 255, np.uint8)])
    return im


@functools.lru_cache(None)
def lib2_index():
    p = os.path.join(LIB2, 'index.json')
    return json.load(open(p))['parts'] if os.path.exists(p) else {}


def from_lib2(rec):
    img = _read(os.path.join(LIB2, rec['image']))
    if img is None:
        return None
    kp = {k: np.asarray(v, float) for k, v in rec['keypoints']['canonical'].items()}
    c = rec.get('classes', {})
    M = np.asarray(rec['transform']['matrix_card_to_canonical'], float)
    lc = next((x for x in LB._raw()[0] if x['id'] == rec['source_card']), None)
    br = np.asarray((lc or {}).get('brads') or [], float).reshape(-1, 2)
    brads = br @ M[:, :2].T + M[:, 2] if len(br) else np.zeros((0, 2))
    return {'key': rec['key'], 'part': rec['part'], 'source': 'library2', 'img': img, 'pivot': kp['pivot'], 'kp': kp,
            'brads': brads, 'view': (c.get('view') or {}).get('value'), 'facing': (c.get('facing') or {}).get('value'),
            'side': (c.get('side') or {}).get('value'), 'state': (c.get('state') or {}).get('value'),
            'character': rec['character'], 'costume': rec['costume'], 'src_card': rec['source_card'], 'flags': rec.get('flags', [])}


def onfly(c, part, char, costume):
    """regularise one old-library card onto the canonical grid"""
    try:
        k = CD.prep(c)
    except Exception:
        return None
    if not k.ok or not k.ppc:
        return None
    G = GRID[part]
    W, H = G['canvas']
    s = CANON_PPC / k.ppc
    A, B = np.asarray(k.A, float), np.asarray(k.B, float)
    if part in ('foot', 'pelvis'):
        ang = 0.
    else:
        v = B - A
        ax = np.asarray(G['axis'], float)
        ang = math.atan2(ax[1], ax[0]) - math.atan2(v[1], v[0])
    if part == 'torso':                       # prep: A = waist (hem), B = neck
        pass
    R = np.array([[math.cos(ang), -math.sin(ang)], [math.sin(ang), math.cos(ang)]]) * s
    piv = np.asarray(G['pivot'], float)
    M = np.hstack([R, (piv - R @ A)[:, None]])
    img = cv2.warpAffine(k.bgra.astype(np.uint8), M, (W, H), flags=cv2.INTER_LINEAR, borderValue=0)
    if (img[..., 3] > 128).sum() < 200:
        return None
    tf = lambda p: R @ np.asarray(p, float) + M[:, 2]
    kp = {'pivot': piv, 'tip': tf(B)}
    if part == 'pelvis' and k.hip1 is not None:
        kp.update(hip_l=tf(k.hip1), hip_r=tf(k.hip2))
    if part == 'torso':
        kp.update(neck=tf(B), shoulder_l=tf(k.shL), shoulder_r=tf(k.shR))
    br = np.asarray(c.get('brads') or [], float).reshape(-1, 2)
    facing = None
    if part == 'foot':
        facing = 'screen-right' if (B - A)[0] > 0 else 'screen-left'
    return {'key': '%s/%s/%s' % (char, part, c['id'].replace('/', '__')), 'part': part, 'source': 'onfly', 'img': img,
            'pivot': piv, 'kp': kp, 'brads': br @ R.T + M[:, 2] if len(br) else np.zeros((0, 2)),
            'view': VIEW.get(c.get('view') or ''), 'facing': facing, 'side': c.get('side'), 'state': None,
            'character': char, 'costume': costume, 'src_card': c['id'], 'flags': [],
            'width_cm': {'pivot': k.w0, 'tip': k.w1}}


@functools.lru_cache(None)
def parts(char, costume=None, part=None):
    out = []
    have = set()
    for rec in lib2_index().values():
        if rec['status'] != 'ok' or rec['character'] != char or (part and rec['part'] != part):
            continue
        if costume and rec['costume'] != costume and rec['part'] != 'head':
            continue
        p = from_lib2(rec)
        if p:
            out.append(p); have.add(rec['part'])
    # part types library2 does not have yet: on the fly from the old library (cloth of this costume; heads never)
    hyg = HY.load()
    cost = costume or 'red_black_sunglasses'
    for c in LB.cards(char, cost):
        pt = c['slot']
        if pt in have or pt == 'head' or (part and pt != part) or c['kind'] != 'kit':
            continue
        if hyg.get(c['id']) and HY.junk(hyg[c['id']]):
            continue
        if c.get('other_costume'):
            continue
        p = onfly(c, pt, char, cost)
        if p:
            out.append(p)
    return out
