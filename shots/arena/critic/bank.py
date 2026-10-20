"""What Bolas asked for on a frame, read from the motion bank, in the clip's camera.

The clip keeps only card matrices. Everything that makes the Crash Lab expressive
(hand shape, grip, palm facing, face, effort, props with size and holder) is in the
bank and dropped by the compiler. This reads it back so a part can be chosen from
it and the critic can compare what was asked for with what was drawn.

    B = Bank('ACT-010')            # T110
    B.hands(f, actor=0)            {'L': {'shape','grip','palm'}, 'R': {...}}
    B.face(f), B.effort(f)
    B.props(f)                     [{'type','held','polys':[[...]], 'fills':[...]}]  in screen px
"""
import json, math, os

HERE = os.path.dirname(os.path.abspath(__file__))
BANK = os.path.normpath(os.path.join(HERE, '..', 'bolas', 'bank'))
W, H = 1920, 1080


class Bank:
    def __init__(self, act):
        n = int(act.split('-')[1])
        self.tid = f'T{n + 100}'
        path = os.path.join(BANK, self.tid + '.json')
        if not os.path.exists(path):
            raise FileNotFoundError(f'{path}: re-bake with bolas/export_bank.mjs <bolas checkout>')
        self.V = json.load(open(path))
        v = self.V['view'] or {}
        self.yaw, self.elev = math.radians(v.get('yaw', -22)), math.radians(v.get('elev', 10))
        self.c = [v.get('x', 0), v.get('y', 90), v.get('z', 0)]
        self.s = H * 0.86 / 230 * v.get('zoom', 1.0)
        self.ids = [a['id'] for a in self.V['actors']]

    def proj(self, p):
        x, y, z = p[0] - self.c[0], p[1] - self.c[1], p[2] - self.c[2]
        cy, sy, ce, se = math.cos(self.yaw), math.sin(self.yaw), math.cos(self.elev), math.sin(self.elev)
        x1, z1 = x * cy - z * sy, x * sy + z * cy
        y2, z2 = y * ce - z1 * se, y * se + z1 * ce
        return [W / 2 + x1 * self.s, H * 0.52 - y2 * self.s, z2]

    def _a(self, f, actor):
        return self.V['frames'][f]['a'].get(self.ids[actor])

    def hands(self, f, actor=0):
        h = self._a(f, actor)['hand']
        return {'L': {'shape': h['L'] or 'relaxed', 'grip': h['gL'], 'palm': h['pL'] or 'in'},
                'R': {'shape': h['R'] or 'relaxed', 'grip': h['gR'], 'palm': h['pR'] or 'in'}}

    def face(self, f, actor=0):
        return self._a(f, actor)['face']

    def effort(self, f, actor=0):
        return self._a(f, actor)['effort']

    def props(self, f):
        out = []
        for pid, q in self.V['frames'][f].get('p', {}).items():
            if q.get('type') != 'box' or not q.get('pos') or not q.get('size'):
                continue
            sx, sy, sz = q['size']
            cx, cy, cz = q['pos']
            P = {}
            for i in (-1, 1):
                for j in (-1, 1):
                    for k in (-1, 1):
                        P[(i, j, k)] = self.proj([cx + i * sx / 2, cy + j * sy / 2, cz + k * sz / 2])
            faces = {'top': [(-1, 1, -1), (1, 1, -1), (1, 1, 1), (-1, 1, 1)],
                     'front': [(-1, -1, -1), (1, -1, -1), (1, 1, -1), (-1, 1, -1)],
                     'side': [(1, -1, -1), (1, -1, 1), (1, 1, 1), (1, 1, -1)],
                     'back': [(-1, -1, 1), (1, -1, 1), (1, 1, 1), (-1, 1, 1)],
                     'left': [(-1, -1, -1), (-1, -1, 1), (-1, 1, 1), (-1, 1, -1)]}
            shade = {'top': '#d9b483', 'front': '#c49a6c', 'side': '#a77f55', 'back': '#b88e60', 'left': '#a77f55'}
            polys = []
            for name, idx in faces.items():
                pts = [P[i] for i in idx]
                # back-face cull in screen space (counter-clockwise = facing us)
                a = sum(pts[i][0] * pts[(i + 1) % 4][1] - pts[(i + 1) % 4][0] * pts[i][1] for i in range(4))
                if a < 0:
                    polys.append({'pts': [p[:2] for p in pts], 'fill': shade[name], 'z': sum(p[2] for p in pts) / 4})
            polys.sort(key=lambda p: -p['z'])
            out.append({'id': pid, 'type': 'box', 'held': q.get('held'), 'size_cm': q['size'], 'polys': polys})
        return out

    def near_side(self, f, actor=0):
        """'L' or 'R': the shoulder nearer the camera (smaller depth) on frame f."""
        j = self._a(f, actor)['j']
        return 'L' if self.proj(j[16])[2] < self.proj(j[17])[2] else 'R'

    def foot(self, f, actor, side):
        """Screen (heel, toe) of one foot, from the bank's heel and toe joints."""
        j = self._a(f, actor)['j']
        h, t = (7, 11) if side == 'L' else (8, 12)
        return self.proj(j[h])[:2], self.proj(j[t])[:2]
