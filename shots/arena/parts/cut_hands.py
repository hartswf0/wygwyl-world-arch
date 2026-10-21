"""Cut the man's hand cards (weave/cast/man/sheets/hands.jpg, hands_2.jpg) and register them.

    python3 shots/arena/parts/cut_hands.py

Each hand is drawn on a cardboard tab with a brass eyelet: the eyelet is socket A
(it sits on the wrist, under the forearm cuff), B is the fingertip end along the
hand. Sockets are read off the sheet by eye in sheet px and moved into card px by
the crop. Writes parts/cut/man_hands/<shape>.png and man_hands/hands.json.
"""
import json, os
import numpy as np
from PIL import Image
from cut_props import cut_box

HERE = os.path.dirname(os.path.abspath(__file__))
SHEETS = os.path.join(HERE, '..', '..', 'weave', 'cast', 'man', 'sheets')
OUT = os.path.join(HERE, 'cut', 'man_hands')
# name: (sheet, box, eyelet A, fingertip B), all sheet px
HANDS = {
    'open_back': ('hands.jpg', (62, 62, 302, 198), (90, 133), (295, 136)),
    'open_palm': ('hands.jpg', (597, 55, 838, 193), (625, 130), (830, 136)),
    'fist': ('hands.jpg', (872, 75, 1062, 198), (898, 130), (1052, 140)),
    'grip': ('hands.jpg', (1102, 72, 1288, 198), (1132, 137), (1280, 137)),
    'pinch': ('hands.jpg', (67, 302, 285, 438), (95, 398), (272, 352)),
    'point': ('hands.jpg', (327, 327, 563, 443), (355, 383), (556, 354)),
    'thumb': ('hands.jpg', (597, 282, 783, 448), (628, 400), (772, 392)),
    'relaxed': ('hands.jpg', (1079, 565, 1313, 688), (1105, 612), (1302, 628)),
    'wave': ('hands.jpg', (867, 509, 1038, 731), (942, 702), (950, 522)),
    'peace': ('hands_2.jpg', (917, 277, 1023, 493), (965, 465), (950, 288)),
    'hang': ('hands_2.jpg', (127, 35, 263, 271), (180, 63), (186, 262)),
}


def cut(sheet, box):
    im = Image.open(os.path.join(SHEETS, sheet))
    card = cut_box(im, box, False)
    # where the tight crop starts inside the box: match the card's alpha back onto the box
    a = np.asarray(im.crop(box).convert('RGB')).astype(int)
    light = (a.min(axis=2) > 205) & (np.ptp(a, axis=2) < 26)
    ys, xs = np.nonzero(~light)
    return card, (box[0] + int(xs.min()), box[1] + int(ys.min()))


if __name__ == '__main__':
    os.makedirs(OUT, exist_ok=True)
    reg = {}
    for name, (sheet, box, A, B) in HANDS.items():
        card, (ox, oy) = cut(sheet, box)
        card.save(os.path.join(OUT, name + '.png'))
        reg[name] = {'file': f'arena/parts/cut/man_hands/{name}.png', 'A': [A[0] - ox, A[1] - oy], 'B': [B[0] - ox, B[1] - oy]}
        print(name, card.size, reg[name]['A'], reg[name]['B'])
    json.dump(reg, open(os.path.join(OUT, 'hands.json'), 'w'), indent=1)
