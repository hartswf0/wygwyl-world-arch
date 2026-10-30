#!/usr/bin/env python3
"""Measure lane B's replacement hand cards (arena/parts/kit3/v2/parts/<kit>/hand.R.<shape>.<palm|back>.png) so the suite can swap them.

Every card is a right hand on a template: a wrist tab with its brad at the left, fingers to the right. For each card this
writes the wrist brad (the centre of the ink in the tab column, 18 px in from the left edge of the ink) and the fingertip
(the inked point farthest from the wrist) to data/hand_cards.json, keyed by lane B character id. lib/hands_extra.js reads it.
"""
import json, os, re
import numpy as np, cv2
SUITE = os.path.dirname(os.path.dirname(os.path.abspath(__file__))); SHOTS = os.path.dirname(SUITE)
C = json.load(open(os.path.join(SUITE, 'data/characters.json')))
chars = C['characters'] if isinstance(C, dict) else C
out = {}
for ch in chars:
    rec = {}
    for f in ch.get('replacement', {}).get('hands', []):
        m = re.search(r'hand\.([RL])\.([a-z_]+)\.(palm|back)\.png$', f)
        if not m: continue
        a = cv2.imread(os.path.join(SHOTS, f), cv2.IMREAD_UNCHANGED)
        if a is None or a.shape[2] != 4: continue
        ys, xs = np.nonzero(a[:, :, 3] > 40)
        if not len(xs): continue
        x0 = xs.min(); col = (xs >= x0 + 10) & (xs <= x0 + 26)
        wrist = [int(x0 + 18), round(float((ys[col].min() + ys[col].max()) / 2), 1)]
        d = np.hypot(xs - wrist[0], ys - wrist[1]); i = int(d.argmax())
        rec.setdefault(m.group(2), {})[m.group(3)] = {'file': f, 'w': int(a.shape[1]), 'h': int(a.shape[0]), 'wrist': wrist, 'tip': [int(xs[i]), int(ys[i])], 'side': m.group(1)}
    if rec: out[ch['id']] = rec
json.dump({'about': 'lane B replacement hand cards, measured by tools/stage_hands.py', 'hands': out}, open(os.path.join(SUITE, 'data/hand_cards.json'), 'w'))
print(len(out), 'characters', sum(len(v) for v in out.values()), 'shapes')
