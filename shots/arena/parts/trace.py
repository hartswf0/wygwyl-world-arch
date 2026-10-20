"""Rotoscope a generated card into a code part: flat colour regions as polygons.

    python3 shots/arena/parts/trace.py man.torso.profile [--mode outline|colours]

outline (default): the card's silhouette, its light panels and its piping, filled
in the kit's colours: a code part with the card's shape. colours: every quantised
colour region, kept for comparison; it turns fluting into speckle.

The traced part keeps the card's look (its few main colours, its outline) but is
now shapes in centimetres, so it can be edited like any kit part: recoloured,
re-proportioned, a stripe moved, a hem shortened. Its sockets are carried over
from the image part's REGISTERED sockets (registered.json); tracing never invents
a joint. Output: lib/<id>.traced.{png,svg,json}, comparable with the original on
sheet.png.
"""
import argparse, json, os, sys
import numpy as np
from PIL import Image
from skimage import measure

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from kit import vec
import library as LIBR


def trace(pid, colours=8, cm_per_px=None, tol=1.2, mode='outline'):
    P = {p['id']: p for p in LIBR.load()}
    src = P[pid]
    im = Image.open(os.path.join(LIBR.SHOTS, src['file'])).convert('RGBA')
    A = np.asarray(im)[:, :, 3] > 128
    q = im.convert('RGB').quantize(colors=colours, method=Image.Quantize.MEDIANCUT)
    lab = np.asarray(q)
    pal = q.getpalette()[:colours * 3]
    # scale: put the card at body size using the same rule the assembler uses
    s = src['sockets']
    if cm_per_px is None:
        a, b, cm = {'torso': ('hip', 'neck', 50.0), 'head': ('neck', 'crown', 27.0)}[src['kind']]
        cm_per_px = cm / float(np.hypot(*(np.array(s[a]) - np.array(s[b]))))
    ox, oy = s['A']

    def to_cm(c):
        return [[(x - ox) * cm_per_px, (y - oy) * cm_per_px] for y, x in c]
    shapes = []
    # silhouette first (carries the cardboard rim), then colour regions, largest first
    for c in measure.find_contours(np.pad(A, 1).astype(float), 0.5):
        c = measure.approximate_polygon(c - 1, tolerance=tol)
        if len(c) > 3:
            shapes.append({'poly': to_cm(c), 'fill': '#000000'})
    if mode == 'outline':
        # The silhouette and the landmarks, filled in the kit's own style. Tracing every
        # colour turned the fluting into speckle and lost the piping (critic, trace
        # turn 2); a drawn part wants the shape from the card and the paint from code.
        from kit import body as KB
        shapes = [dict(sh, fill=KB.CLOTH, stroke=KB.LINE, sw=0.12) for sh in shapes]
        hsv = np.asarray(im.convert('RGB').convert('HSV')).astype(float)
        Hh, Ss, Vv = hsv[..., 0] * 360 / 255, hsv[..., 1] / 255, hsv[..., 2] / 255
        pipe = A & (Hh < 25) & (Ss > 0.3) & (Vv > 0.6)
        # inside the cut edge only: the cardboard rim is light too, and its outline is
        # the whole card (critic, trace turn 3)
        from scipy import ndimage as nd
        inner = nd.binary_erosion(A, iterations=10)
        pipe &= inner
        light = inner & (Vv > 0.55) & (Ss < 0.45) & ~pipe       # collar, armhole lining
        for m, col in ((light, '#c9a57a'), (pipe, KB.PIPING)):
            for c in measure.find_contours(np.pad(m, 1).astype(float), 0.5):
                c = measure.approximate_polygon(c - 1, tolerance=tol)
                if len(c) > 3:
                    area = 0.5 * abs(np.dot(c[:, 0], np.roll(c[:, 1], 1)) - np.dot(c[:, 1], np.roll(c[:, 0], 1)))
                    if area > 40:
                        shapes.append({'poly': to_cm(c), 'fill': col, 'rim': False})
        for k, v in s.items():
            if k in ('hip', 'hip_L', 'hip_R', 'shoulder_L', 'shoulder_R'):
                shapes += vec.brad([(v[0] - ox) * cm_per_px, (v[1] - oy) * cm_per_px])
    regions = []
    # Every region outline, painted largest first so a region nested inside another
    # lands on top (painting colour by colour let the card-edge colour, whose outer
    # outline encloses the whole card, bury everything: critic, trace turn 1).
    for i in (range(colours) if mode == "colours" else []):
        m = (lab == i) & A
        if m.sum() < 30:
            continue
        col = '#%02x%02x%02x' % tuple(pal[i * 3:i * 3 + 3])
        for c in measure.find_contours(np.pad(m, 1).astype(float), 0.5):
            c = measure.approximate_polygon(c - 1, tolerance=tol)
            if len(c) > 3:
                area = 0.5 * abs(np.dot(c[:, 0], np.roll(c[:, 1], 1)) - np.dot(c[:, 1], np.roll(c[:, 0], 1)))
                if area > 12:
                    regions.append((area, {'poly': to_cm(c), 'fill': col, 'rim': False}))
    shapes += [r for _, r in sorted(regions or [], key=lambda t: -t[0])]
    sockets = {k: [(v[0] - ox) * cm_per_px, (v[1] - oy) * cm_per_px] for k, v in s.items()}
    part = {'kind': src['kind'], 'view': src.get('view'), 'shapes': shapes, 'sockets': sockets,
            'socket_source': 'registered (carried from ' + pid + ')'}
    rec = LIBR._write_code(pid + '.traced', part, {'view': src.get('view'), 'traced_from': pid})
    rec['source'] = 'traced'
    rec['socket_source'] = 'registered'
    json.dump({'shapes': shapes, 'sockets': sockets, 'from': pid, 'record': rec},
              open(os.path.join(LIBR.LIB, pid + '.traced.json'), 'w'))
    return rec, len(shapes)


if __name__ == '__main__':
    ap = argparse.ArgumentParser()
    ap.add_argument('id')
    ap.add_argument('--colours', type=int, default=8)
    ap.add_argument('--mode', default='outline', choices=['outline', 'colours'])
    a = ap.parse_args()
    rec, n = trace(a.id, a.colours, mode=a.mode)
    print(rec['file'], n, 'shapes')
