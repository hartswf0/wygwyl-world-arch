"""Kit 3 layout registry for every v2 build (poetm, ex, boy, ghost, woman, manx, robed, bola, shim, dotd).

kit.py draws each template and records, per cell, the brad crosses (A, B), the sockets and the
px-per-cm of the sheet. That record is the layout's knowledge of which cell is which part.
This module re-runs those functions (drawing to throwaway images) and returns the registry, plus
each build's skeleton lengths in cm, so a painted sheet can be named and scaled from its layout.

    python3 shots/suite/tools/kit_registry.py      # writes shots/suite/data/kit_layouts.json
"""
import json, math, os, sys
HERE = os.path.dirname(os.path.abspath(__file__))
SHOTS = os.path.normpath(os.path.join(HERE, '..', '..'))
KIT3 = os.path.join(SHOTS, 'arena', 'parts', 'kit3')
sys.path.insert(0, KIT3)
from PIL import ImageFont
import kit as K

_font = K.font
def _safe_font(path, n):
    try:
        return _font(path, n)
    except OSError:
        return ImageFont.load_default()
K.font = _safe_font
import v2 as V2  # registers the v2 builds into K.CHARS
V2.font = _safe_font
import packs as PKS
PKS.font = _safe_font if hasattr(PKS, 'font') else None

BUILDS = list(V2.BUILDS)


def skeleton_cm(build):
    """Lengths in cm from the build's rest skeleton (the same numbers the templates use)."""
    C = K.CHARS[build]
    J = C['J']
    d = lambda a, b: round(math.dist(J[a][:2], J[b][:2]), 2)
    out = {'height_cm': C['height']}
    for name, a, b in K.LIMBS:
        out[name] = d(a + 'L', b + 'L') if a + 'L' in J else None
    out['torso'] = round(abs(J['neck'][1] - J['hipL'][1]), 2)
    out['head_r'] = None
    return out


def registry():
    reg = {}
    for b in BUILDS:
        for view in ('front', 'threequarter', 'back', 'profile', 'threequarter_back'):
            geo = 'profile' if view == 'profile' else 'front'
            K.body_template(b, geo, reg, view)
        K.heads_template(b, reg)
        for v in ('front', 'profile'):
            K.face_template(b, v, reg)
        K.hands_template(b, reg)
        K.feet_template(b, reg)
    return reg


def main():
    reg = registry()
    out = {'about': 'Kit 3 layout registry per v2 build: template px (2048x1152 sheet), brad crosses A/B, sockets, px_per_cm; '
                     'skeleton lengths in cm. Written by shots/suite/tools/kit_registry.py from kit.py + v2.py.',
           'sheet_px': [K.SHEET_W, K.SHEET_H], 'builds': {}}
    for b in BUILDS:
        out['builds'][b] = {'label': K.CHARS[b].get('label'), 'height_cm': K.CHARS[b]['height'],
                            'skeleton_cm': skeleton_cm(b), 'layouts': reg.get(b, {})}
    p = os.path.join(SHOTS, 'suite', 'data', 'kit_layouts.json')
    json.dump(out, open(p, 'w'), indent=1)
    print('wrote', p, {b: len(v['layouts']) for b, v in out['builds'].items()})


if __name__ == '__main__':
    main()
