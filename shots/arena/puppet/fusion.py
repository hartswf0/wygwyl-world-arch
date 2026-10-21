"""Fusion heads: a generated (painted) head plate with coded features plugged onto its anchors.

The first one is the poet. Her only head card (weave/assets/parts/head.png) is a profile with the
eyes painted shut, so in every take she looked asleep (critics, every round). Here:

  plate   the painted head with the closed eye painted out (biharmonic inpaint from the skin
          around it): the blank plate Kit 3 asks every head to have
  closed  the original painted closed eye, kept as the 'closed' state: generated art where
          generated art exists
  open    a coded profile eye drawn in her style (almond opening, dark iris at the front, a
          heavy inked upper lid with the lash flick of her painted eye), with the bank's gaze
          (gx) moving the iris and its lid lowering the upper lid

    img = poet_head(face)      # RGBA card, same size and sockets as head.png

So a head is plug and play in both directions: a better painted eye drops in as 'open' later,
and the coded one keeps working on any plate that has the eye anchor.
"""
import os
import numpy as np
from PIL import Image, ImageDraw, ImageFilter

HERE = os.path.dirname(os.path.abspath(__file__))
SHOTS = os.path.normpath(os.path.join(HERE, '..', '..'))
HEAD = os.path.join(SHOTS, 'weave', 'assets', 'parts', 'head.png')
EYE = (246, 189)                 # the painted eye's centre on head.png (card px), read by eye
EYE_BOX = (224, 177, 266, 200)   # the closed eye and its lash flick
SS = 4

_cache = {}


def plate():
    """head.png with the closed eye painted out."""
    if 'plate' not in _cache:
        from skimage.restoration import inpaint_biharmonic
        im = np.asarray(Image.open(HEAD).convert('RGBA')).astype(float) / 255
        H, W = im.shape[:2]
        yy, xx = np.mgrid[0:H, 0:W]
        cx, cy = (EYE_BOX[0] + EYE_BOX[2]) / 2, (EYE_BOX[1] + EYE_BOX[3]) / 2
        rx, ry = (EYE_BOX[2] - EYE_BOX[0]) / 2 + 2, (EYE_BOX[3] - EYE_BOX[1]) / 2 + 2
        mask = ((xx - cx) / rx) ** 2 + ((yy - cy) / ry) ** 2 <= 1
        rgb = inpaint_biharmonic(im[..., :3], mask, channel_axis=-1)
        out = im.copy()
        out[..., :3] = rgb
        # a little of the board's grain back over the smooth patch
        noise = np.random.default_rng(3).normal(0, 0.012, mask.shape)
        out[mask, :3] = np.clip(out[mask, :3] + noise[mask, None], 0, 1)
        _cache['plate'] = Image.fromarray((out * 255).astype(np.uint8))
        _cache['closed_patch'] = Image.open(HEAD).convert('RGBA').crop(EYE_BOX)
    return _cache['plate']


def open_eye(lid=0.0, gx=0.0, gy=0.0):
    """A profile eye facing screen right, drawn at 4x on a transparent layer the plate's size."""
    W, H = Image.open(HEAD).size
    L = Image.new('RGBA', (W * SS, H * SS), (0, 0, 0, 0))
    d = ImageDraw.Draw(L)
    S = lambda x, y: (x * SS, y * SS)
    ink = (34, 24, 20, 255)
    back, front = (231, 190), (259, 188)       # back corner, front of the opening (toward the nose)
    top_peak = (247, 178.0 + 6 * min(lid, 0.85))              # the upper lid comes down with lid
    low = (246, 195.5)
    up = [back] + [((1 - t) ** 2 * back[0] + 2 * (1 - t) * t * top_peak[0] + t * t * front[0],
                    (1 - t) ** 2 * back[1] + 2 * (1 - t) * t * top_peak[1] + t * t * front[1]) for t in np.linspace(0, 1, 14)]
    lo = [((1 - t) ** 2 * front[0] + 2 * (1 - t) * t * low[0] + t * t * back[0],
           (1 - t) ** 2 * front[1] + 2 * (1 - t) * t * low[1] + t * t * back[1]) for t in np.linspace(0, 1, 14)]
    shape = [S(*p) for p in up + lo]
    d.polygon(shape, fill=(226, 211, 194, 255))
    # the lid crease above the opening, in the skin's shadow tone
    d.line([S(234, 184.5 + 4 * lid), S(246, 176.5 + 9 * lid), S(256, 181 + 5 * lid)], fill=(120, 80, 58, 150), width=int(1.0 * SS), joint='curve')
    # the iris sits at the front of the opening (profile), gaze nudges it
    ix, iy = 251.5 + 2.4 * gx, 187.8 - 1.6 * gy
    iris = Image.new('RGBA', L.size, (0, 0, 0, 0))
    di = ImageDraw.Draw(iris)
    di.ellipse([S(ix - 5.6, iy - 6.0), S(ix + 4.4, iy + 6.0)], fill=(58, 33, 24, 255))
    di.ellipse([S(ix - 2.6, iy - 2.8), S(ix + 1.6, iy + 2.8)], fill=(20, 12, 10, 255))
    di.ellipse([S(ix - 1.0, iy - 3.6), S(ix + 1.0, iy - 1.6)], fill=(250, 244, 236, 255))
    m = Image.new('L', L.size, 0)
    ImageDraw.Draw(m).polygon(shape, fill=255)
    L.paste(iris, (0, 0), Image.composite(iris, Image.new('RGBA', L.size, (0, 0, 0, 0)), m).getchannel('A'))
    # lids in ink: heavy upper with the lash flick at the back, light lower
    d.line([S(*p) for p in up], fill=ink, width=int(2.6 * SS), joint='curve')
    d.line([S(back[0] + 1, back[1] - .5), S(226.5, back[1] - 3.5)], fill=ink, width=int(1.8 * SS))
    d.line([S(*p) for p in lo[2:-2]], fill=(90, 60, 45, 200), width=int(0.9 * SS))
    return L.resize((W, H), Image.LANCZOS)


def poet_head(face):
    """The poet's head card for one frame of the bank's face."""
    face = face or {}
    eyes = face.get('eyes', 'o')
    lid = float(np.clip(face.get('lid') or 0, 0, 1))
    if eyes == 'closed' or lid > 0.85:
        key = ('closed',)
    else:
        key = ('open', round(lid, 1), round(float(face.get('gx') or 0), 1), round(float(face.get('gy') or 0), 1))
    if key not in _cache:
        base = plate().copy()
        if key[0] == 'closed':
            base.alpha_composite(_cache['closed_patch'], EYE_BOX[:2])
        else:
            base.alpha_composite(open_eye(*key[1:]))
        _cache[key] = base
    return _cache[key], 'poet.head.' + '_'.join(map(str, key))


if __name__ == '__main__':
    out = os.path.join(HERE, 'fusion_poet.png')
    states = [{'eyes': 'o'}, {'eyes': 'o', 'gx': 1}, {'eyes': 'o', 'lid': .5}, {'eyes': 'o', 'gy': 1}, {'eyes': 'closed'}]
    ims = [plate()] + [poet_head(s)[0] for s in states]
    sheet = Image.new('RGBA', (sum(i.width for i in ims), ims[0].height), (120, 160, 120, 255))
    x = 0
    for i in ims:
        sheet.alpha_composite(i, (x, 0))
        x += i.width
    sheet.convert('RGB').save(out)
    print(out)
