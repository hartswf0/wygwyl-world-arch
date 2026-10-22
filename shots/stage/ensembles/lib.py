"""Shared helpers for the ensemble library (build_ensembles.py) and the staging (plan_poems.py).

Part references are written short:  'sheet:slug'  ->  the cut part whose id is 'sheet/<id-slug>' and whose slug
contains `slug` (exact slug first). Every reference is checked against the cut catalog when the library is built.
"""
import json, os, re

HERE = os.path.dirname(os.path.abspath(__file__))
STAGE = os.path.dirname(HERE)
SHOTS = os.path.dirname(STAGE)
CUT = os.path.join(SHOTS, 'kits', 'cut')
CAT = json.load(open(os.path.join(CUT, 'catalog.json')))['sheets']
PARTS = {p['id']: dict(p, sheet=sid) for sid, s in CAT.items() for p in s['parts']}


def part(ref):
    """'09.props.phonebooth:grey-black' -> the full part id (raises if missing or ambiguous)."""
    if ref in PARTS:
        return ref
    sheet, _, slug = ref.partition(':')
    if sheet not in CAT:
        raise KeyError(f'no sheet {sheet!r} ({ref})')
    ids = [p['id'] for p in CAT[sheet]['parts']]
    exact = [i for i in ids if i.split('/', 1)[1] == slug]
    if exact:
        return exact[0]
    hit = [i for i in ids if slug in i.split('/', 1)[1]]
    if len(hit) != 1:
        raise KeyError(f'{ref}: {len(hit)} matches {hit[:6]}')
    return hit[0]


def size(pid):
    """(w, h) of a part card in sheet pixels (the stage draws it at this aspect)."""
    return PARTS[pid]['bbox'][2], PARTS[pid]['bbox'][3]


def aspect(pid):
    w, h = size(pid)
    return h / w


_holes = {}


def hole(pid):
    """The largest transparent opening enclosed by a card (a window, a door, a rose, a TV glass), as fractions of
    the card [x0, y0, x1, y1]; None when the card has no enclosed opening."""
    if pid in _holes:
        return _holes[pid]
    import numpy as np
    from PIL import Image
    from scipy import ndimage
    im = Image.open(os.path.join(CUT, PARTS[pid]['file'])).convert('RGBA')
    W0, H0 = im.size
    k = 220 / max(W0, H0)
    a = np.array(im.getchannel('A').resize((max(8, round(W0 * k)), max(8, round(H0 * k)))))
    clear = a < 40
    lab, n = ndimage.label(clear)
    edge = set(np.unique(np.concatenate([lab[0], lab[:, 0], lab[:, -1]])))   # a doorway may open onto the bottom edge
    best, area = None, 0
    for i in range(1, n + 1):
        if i in edge:
            continue
        ys, xs = np.nonzero(lab == i)
        if len(xs) > area:
            area = len(xs)
            best = [xs.min() / a.shape[1], ys.min() / a.shape[0], (xs.max() + 1) / a.shape[1], (ys.max() + 1) / a.shape[0]]
    if best and area < .015 * a.size:
        best = None
    _holes[pid] = [round(v, 3) for v in best] if best else None
    return _holes[pid]


def load_ensembles():
    out = {}
    for f in sorted(os.listdir(HERE)):
        if f.startswith('ens.') and f.endswith('.json'):
            E = json.load(open(os.path.join(HERE, f)))
            out[E['id']] = E
    return out
