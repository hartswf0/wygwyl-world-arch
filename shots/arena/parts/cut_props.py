"""Cut the prop cards from the man's prop sheets by hand-placed boxes.

    python3 shots/arena/parts/cut_props.py

The sheets (weave/cast/man/sheets/props.jpg, set_props.jpg) are drawn in the
cast's own cardboard style, so props stop being flat-shaded cuboids. Each box is
read off the sheet by eye; inside it, near-white pixels joined to the box edge are
background. 'holes' keeps see-through gaps (the railing, the door frame, the
open book's gutter stays solid). Writes parts/cut/props/<name>.png.
"""
import os
import numpy as np
from PIL import Image
from scipy import ndimage as nd

HERE = os.path.dirname(os.path.abspath(__file__))
SHEETS = os.path.join(HERE, '..', '..', 'weave', 'cast', 'man', 'sheets')
OUT = os.path.join(HERE, 'cut', 'props')
BOXES = {
    'set_props.jpg': {
        'railing': ((82, 62, 432, 238), True), 'stairs': ((498, 58, 812, 384), True),
        'door': ((862, 58, 1048, 381), False), 'doorframe': ((1072, 52, 1295, 382), True),
        'box': ((372, 547, 530, 715), False), 'cup': ((577, 432, 655, 540), False),
        'papercup': ((677, 437, 753, 538), False), 'table': ((555, 567, 781, 715), True),
        'basketball': ((832, 577, 952, 703), False), 'soccer': ((926, 598, 1040, 718), False),
        'baseball': ((882, 505, 946, 571), False), 'racket': ((952, 462, 1103, 718), True),
        'sign': ((1095, 405, 1298, 722), False)},
    'props.jpg': {
        'notebook': ((137, 207, 285, 403), False), 'book': ((372, 215, 655, 398), False),
        'lantern': ((1112, 352, 1295, 608), False), 'letter': ((845, 629, 981, 731), False),
        'bench': ((1037, 632, 1290, 723), True), 'record': ((95, 443, 372, 715), False)},
}


def cut_box(im, box, holes):
    a = np.asarray(im.crop(box).convert('RGB')).astype(int)
    light = (a.min(axis=2) > 205) & (np.ptp(a, axis=2) < 26)
    lab, _ = nd.label(light)
    edge = set(np.unique(np.concatenate([lab[0], lab[-1], lab[:, 0], lab[:, -1]]))) - {0}
    bg = np.isin(lab, list(edge))
    if holes:      # see-through gaps: big enclosed light regions are background too
        sizes = nd.sum(light, lab, range(1, lab.max() + 1))
        big = [i + 1 for i, s in enumerate(sizes) if s > 150]
        bg |= np.isin(lab, big)
    card = nd.binary_opening(~bg, iterations=1)
    if not holes:
        card = nd.binary_fill_holes(card)
    lab, n = nd.label(card)
    if n > 1:
        sizes = nd.sum(card, lab, range(1, n + 1))
        card = lab == int(np.argmax(sizes)) + 1       # one card: neighbours' corners dropped (the balls overlap)
    alpha = nd.gaussian_filter(card.astype(float), 0.6)
    rgba = np.dstack([a.astype(np.uint8), (alpha * 255).astype(np.uint8)])
    ys, xs = np.nonzero(card)
    return Image.fromarray(rgba).crop((xs.min(), ys.min(), xs.max() + 1, ys.max() + 1))


if __name__ == '__main__':
    os.makedirs(OUT, exist_ok=True)
    for sheet, boxes in BOXES.items():
        im = Image.open(os.path.join(SHEETS, sheet))
        for name, (box, holes) in boxes.items():
            c = cut_box(im, box, holes)
            c.save(os.path.join(OUT, name + '.png'))
            print(name, c.size)
