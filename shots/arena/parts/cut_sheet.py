"""Cut a generated sheet of cards on a light background into separate RGBA parts.

    python3 shots/arena/parts/cut_sheet.py <sheet.jpg> <out_dir> name1,name2,...

Background = pixels connected to the border that are near-white; everything else
is card. Components are ordered row by row (top to bottom, left to right) and
named in that order. A socket is NOT inferred here: register it by eye in
registered.json (the brad reader was off by up to 30px on the cut heads).
"""
import os, sys
import numpy as np
from PIL import Image
from scipy import ndimage as nd


def cut(sheet, out_dir, names, min_area=4000, pad=4):
    im = Image.open(sheet).convert('RGB')
    a = np.asarray(im).astype(int)
    light = (a.min(axis=2) > 222) & (np.ptp(a, axis=2) < 22)
    lab, _ = nd.label(light)
    border = set(np.unique(np.concatenate([lab[0], lab[-1], lab[:, 0], lab[:, -1]]))) - {0}
    bg = np.isin(lab, list(border))
    card = nd.binary_opening(~bg, iterations=2)
    card = nd.binary_fill_holes(card)
    lab, n = nd.label(card)
    boxes = [(sl, int((lab[sl] == i + 1).sum())) for i, sl in enumerate(nd.find_objects(lab))]
    comps = [(i + 1, sl) for i, (sl, area) in enumerate(boxes) if area >= min_area]
    # rows: cluster by vertical centre
    comps.sort(key=lambda c: (c[1][0].start + c[1][0].stop) / 2)
    rows, cur = [], []
    for c in comps:
        cy = (c[1][0].start + c[1][0].stop) / 2
        if cur and cy - (cur[-1][1][0].start + cur[-1][1][0].stop) / 2 > (c[1][0].stop - c[1][0].start) * 0.5:
            rows.append(cur)
            cur = []
        cur.append(c)
    rows.append(cur)
    ordered = [c for r in rows for c in sorted(r, key=lambda c: c[1][1].start)]
    os.makedirs(out_dir, exist_ok=True)
    rgba = np.dstack([np.asarray(im), np.zeros(a.shape[:2], np.uint8)])
    out = []
    for (i, sl), name in zip(ordered, names):
        y0, y1 = max(0, sl[0].start - pad), min(a.shape[0], sl[0].stop + pad)
        x0, x1 = max(0, sl[1].start - pad), min(a.shape[1], sl[1].stop + pad)
        m = (lab[y0:y1, x0:x1] == i)
        m = nd.binary_erosion(m, iterations=1)
        piece = rgba[y0:y1, x0:x1].copy()
        # defringe: the sheet's white survives a pixel or two inside the cut; drop
        # near-white pixels that touch the edge (critic, p3d turn 1: a white halo)
        edge = m & ~nd.binary_erosion(m, iterations=3)
        rgb = piece[..., :3].astype(int)
        whiteish = (rgb.min(axis=2) > 170) & (np.ptp(rgb, axis=2) < 40)
        m = m & ~(edge & whiteish)
        m = nd.binary_opening(m, iterations=1)
        piece[..., 3] = (m * 255).astype(np.uint8)
        path = os.path.join(out_dir, f'{name}.png')
        Image.fromarray(piece).save(path)
        out.append((name, path, [x0, y0, x1, y1], piece.shape[1::-1]))
    if len(ordered) != len(names):
        print(f'warning: {len(ordered)} cards found, {len(names)} names given', file=sys.stderr)
    return out


if __name__ == '__main__':
    for name, path, box, size in cut(sys.argv[1], sys.argv[2], sys.argv[3].split(',')):
        print(name, size, box)
