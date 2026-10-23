"""Pieces for the blind puzzle: every library card of the character (library.json + library_harvest.json) as a SHAPE.

Body labels (slot, side, view) are never used to choose a piece. They are kept on the record only so that the
zone learning can later compare where a piece landed with what the library calls it.

Rules about where pieces come from (the only ones):
  * a harvest card cut from the target painting is excluded;
  * a kit card whose box on its sheet touches the target painting's box is excluded (same pixels);
  * a whole figure filed as a card (an id that is itself a painting with markers, or a sheet 'ref'/'pose' figure that
    is not a head) is excluded: it is another painting's whole body, not a piece;
  * same character; same costume (the poet's black_tshirt cards would paint the wrong clothes), heads of another
    costume allowed as in the contract.
Everything else is in, including cards the harvest checks flagged bad: as shapes they may still fit.
"""
import functools, os, sys
import numpy as np, cv2

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.abspath(os.path.join(HERE, '..', '..')))
from evolve import library, cards as C, assemble as AS  # noqa: E402


def excluded(c, tid, all_targets):
    sheet = tid.rsplit('/', 1)[0]
    if c['kind'] == 'harvest' and c['source'] == tid:
        return 'cut from the target painting'
    if c['id'] == tid:
        return 'is the target painting'
    if c['kind'] == 'kit':
        if c['family'] == sheet:
            tb = library._sheet(sheet).get(tid, {}).get('bbox')
            if tb and c['sheet_bbox'] and library._boxes_touch(tb, c['sheet_bbox']):
                return 'overlaps the target painting on its sheet'
        if c['id'] in all_targets:
            return 'a whole painting filed as a card'
        if c['sheet_kind'] in ('ref', 'pose') and c['slot'] != 'head':
            return 'a whole figure (sheet ref/pose)'
    return None


@functools.lru_cache(maxsize=3000)
def card_pixels(cid, img, erase):
    im = C.read_bgra(img).astype(np.float32)
    for x0, y0, x1, y1 in erase:
        im[int(y0):int(y1), int(x0):int(x1), 3] = 0
    a = im[..., 3]
    ys, xs = np.nonzero(a > 128)
    if len(xs) < 50:
        return None
    x0, y0, x1, y1 = xs.min(), ys.min(), xs.max() + 1, ys.max() + 1
    im = im[y0:y1, x0:x1].copy()
    # holes keyed out of white paint are filled back (a piece is one solid shape)
    hard = (im[..., 3] > 128).astype(np.uint8)
    ff = np.pad(1 - hard, 1, constant_values=1)
    mask = np.zeros((ff.shape[0] + 2, ff.shape[1] + 2), np.uint8)
    cv2.floodFill(ff, mask, (0, 0), 2)
    holes = ff[1:-1, 1:-1] == 1
    im[..., 3][holes] = 255
    return im


def pieces_for(char, costume, tid):
    allt = set(AS.all_targets(char).keys())
    out, gone = [], []
    for c in library.cards(char, costume):
        why = excluded(c, tid, allt)
        if why:
            gone.append((c['id'], why)); continue
        px = card_pixels(c['id'], c['img'], tuple(tuple(e) for e in c.get('erase') or ()))
        if px is None:
            gone.append((c['id'], 'too few pixels')); continue
        out.append({'id': c['id'], 'px': px, 'ppc': c['ppc'], 'label': c['slot'], 'kind': c['kind'], 'family': c['family']})
    return out, gone
