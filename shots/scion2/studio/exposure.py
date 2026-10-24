"""Exposure-sheet animation from whole paintings: the simple method the swarms converge on.

Reiniger, Gilliam, South Park, Cartoon Saloon, Harmony's drawing substitution, the Multiview Turn Lab
and Pose2Pose all animate painted characters the same way when a pose is not in the drawing: they
swap to a drawing that has it. Nothing here bends a painting.

  vocabulary  an actor's clean paintings (one costume, full figure, no scenery in the cutout), each
              tagged by view (front, q3, prof, back3q, back) and posture
  sheet       a list of beats: which painting (by tag or id, optionally mirrored), how long it holds,
              where the body travels while it holds, and how it lands (a settle)
  placement   every painting is scaled so the actor keeps one size (from its marked legs and torso),
              its lowest painted pixel sits on the floor, and its body centre stays where the
              previous beat left it unless the beat travels: a swap never jumps
  turn        a spin is a ring of views; the ring is resolved per actor from its own drawings, mirrored
              where the far side is the near side flipped. The same ring plays for any cast member.

Each frame records the actor's height, floor contact and centre, so the invariants can be checked.
"""
import math
import numpy as np, cv2

from studio import select as sel
from studio.core import PX_PER_CM

RING = ['q3', 'prof', 'back3q', 'back', 'back3q~', 'prof~', 'q3~', 'front']   # ~ = mirrored drawing


class Cast:
    """an actor's vocabulary: clean drawings by id and by view"""

    def __init__(self, char, costume, height_cm, name):
        self.char, self.name, self.height_cm = char, name, height_cm
        self.lib = sel.library(char, costume=costume)
        for d in self.lib:      # the selector folds back3q into back; keep it apart for turns
            v = d.cat.get('view') or ''
            d.ring = 'back3q' if v.startswith('back3q') else d.view
        self.by_id = {d.id.split('/')[-1]: d for d in self.lib}
        # one actor size: the median of (legs + torso) over the drawings, in that drawing's pixels, maps
        # to the actor's own legs + torso in cm (taken as 0.70 of height, the poet's measured ratio)
        self.body_cm = 0.70 * height_cm

    def get(self, key):
        """'id' or 'view:<v>' (first drawing in that view, prefer posture `cls` if given 'view:<v>/<cls>')"""
        mir = key.endswith('~')
        key = key.rstrip('~')
        if key.startswith('view:'):
            v, _, cls = key[5:].partition('/')
            c = [d for d in self.lib if d.ring == v]
            if cls:
                c = [d for d in c if d.cls == cls] or c
            if not c:
                return None, mir
            return c[0], mir
        return self.by_id.get(key), mir

    def ring(self, start='q3', turns=1.0, cls=None):
        """the spin for this actor as a fixed list of slots (one per view of RING). A slot whose view
        the actor has no drawing for (in posture `cls`, strictly) holds the previous drawing, so every
        actor's spin has the same beats."""
        i0 = RING.index(start)
        out, last = [], None
        for k in range(int(round(turns * len(RING)))):
            v = RING[(i0 + k) % len(RING)]
            vv = v.rstrip('~')
            c = [d for d in self.lib if d.ring == vv and (cls is None or d.cls == cls)]
            if c:
                last = c[0].id.split('/')[-1] + ('~' if v.endswith('~') else '')
            out.append(last)
        return out


def scale_of(cast, d):
    legs, torso = d.body_px
    return cast.body_cm * PX_PER_CM / (legs + torso)


class Player:
    """plays one actor's sheet onto the stage, frame by frame"""

    def __init__(self, cast, stage, x_cm, sheet):
        self.c, self.stage, self.sheet = cast, stage, sheet
        self.cx = x_cm * PX_PER_CM          # body centre x on stage (px)
        self.frames = []
        for b in sheet:
            for i in range(b['hold']):
                self.frames.append((b, i))

    def __len__(self):
        return len(self.frames)

    def draw(self, canvas, f):
        if f >= len(self.frames):
            f = len(self.frames) - 1
        b, i = self.frames[f]
        d, mir = self.c.get(b['d'])
        rec = {'beat': b.get('name') or b['d'], 'drawing': d.id if d else None, 'mirror': mir, 'swap': i == 0}
        if d is None:
            rec['gap'] = True
            return rec
        # travel: the centre moves during a beat that travels (linear, or eased if the beat says so)
        if 'move_cm' in b and i > 0:
            self.cx += b['move_cm'] * PX_PER_CM / b['hold']
        img = d.image()
        if mir:
            img = img[:, ::-1]
        s = scale_of(self.c, d) * b.get('scale', 1.0)
        a = img[..., 3] > 40
        ys, xs = np.nonzero(a)
        low = ys.max()
        # the body centre of a drawing: its pelvis marker (mirrored with the drawing)
        gx = d.m['groin'][0] if not mir else d.w - d.m['groin'][0]
        # landing settle: a 2-frame dip after a swap (paper drops onto the table)
        dip = [3, 1.5][i] if b.get('settle', True) and i < 2 else 0.
        bob = b.get('bob', 0.) * abs(math.sin(math.pi * i / max(1, b.get('bob_period', 6))))
        tx = self.cx - s * gx
        ty = self.stage['floor'] - s * low + dip - bob
        lay = sel.paste(canvas, img, s, tx, ty)
        al = lay[..., 3] > 40
        yy, xx = np.nonzero(al)
        rec.update({'height_px': float(yy.max() - yy.min()) if len(yy) else 0., 'low_px': float(yy.max()) if len(yy) else 0.,
                    'centre_px': float(self.cx), 'scale': float(s), 'dip': dip, 'bob': bob})
        return rec
