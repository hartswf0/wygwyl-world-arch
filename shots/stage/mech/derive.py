"""Derived cards for mechanisms, cut from kit parts (the kit itself stays read-only).

    python3 shots/stage/mech/derive.py      -> shots/stage/mech/parts/*.webp

Each derived card is a knife cut through an existing card, so it keeps the painted surface:
- car_body_nodoor / car_door: the 02 car side card with the front door cut free on its hinge line.
- car_cabin: the dark cabin seen through the car's window holes (hand-cut from the same card's colours).
"""
import os
import numpy as np
from PIL import Image, ImageDraw, ImageFilter

HERE = os.path.dirname(os.path.abspath(__file__))
CUT = os.path.normpath(os.path.join(HERE, '..', '..', 'kits', 'cut'))
OUT = os.path.join(HERE, 'parts')

DOOR = [(213, 97), (318, 21), (393, 19), (394, 219), (213, 219), (209, 160)]


def mask(size, poly):
    m = Image.new('L', size, 0)
    ImageDraw.Draw(m).polygon(poly, fill=255)
    return m


def car():
    body = Image.open(os.path.join(CUT, '02.props.car/car.webp')).convert('RGBA')
    m = mask(body.size, DOOR)
    a = np.array(body)
    mm = np.array(m) > 0
    door = a.copy(); door[~mm, 3] = 0
    rest = a.copy(); rest[mm, 3] = 0
    # a thin dark edge round the door card (the knife line reads as a seam)
    dd = Image.fromarray(door)
    edge = m.filter(ImageFilter.FIND_EDGES).filter(ImageFilter.MaxFilter(3))
    e = np.array(edge) > 0
    da = np.array(dd)
    da[e & (da[:, :, 3] > 0), :3] = (da[e & (da[:, :, 3] > 0), :3] * 0.45).astype(np.uint8)
    x0, y0, x1, y1 = Image.fromarray(da).getbbox()
    Image.fromarray(da).crop((x0, y0, x1, y1)).save(os.path.join(OUT, 'car_door.webp'), lossless=True)
    Image.fromarray(rest).save(os.path.join(OUT, 'car_body_nodoor.webp'), lossless=True)
    print('car door bbox', (x0, y0, x1, y1))


if __name__ == '__main__':
    os.makedirs(OUT, exist_ok=True)
    car()
