"""Replacement heads and hands, cut from whole paintings of the poet (H3 round 2).

Every item records its source painting (so leave-one-family-out can be enforced per target),
its view / expression, a seat (heads: the collar line; hands: the wrist base and the finger
direction) and the source figure's scale (torso length neck->mid-hip in source px, from the
Pose Lab markers, or set by hand where a source has no markers).

Heads are cut along the collar line and sit into the rig's collar (no edge on the seat).
Hands are cut by skin colour inside a box (plus their painted outline) and slide under the
rig's cuff (no edge at the wrist).
"""
import json, math, os
import numpy as np, cv2

import rig

HERE = rig.HERE
LIBDIR = os.path.join(HERE, 'lib')

# id: (source, kind, box x0,y0,x1,y1, seat-a, seat-b or tip, tags, scale override)
HEADS = {
    'chinup':  dict(src='poet.07.main-poses/chin-up-open-arms', box=(126, 0, 200, 64), collar=[(126, 60), (200, 60)],
                    view='3qR', gaze='up', expr='calm', glasses=True),
    'reathe':  dict(src='poet.11.main-poses/05-read-water-reathe-1', box=(55, 0, 120, 60), collar=[(55, 57), (120, 57)],
                    view='front', gaze='back', expr='calm', glasses=True),
    'welcome': dict(src='poet.11.main-poses/welcome-new-day', box=(158, 24, 214, 84), collar=[(158, 82), (214, 82)],
                    view='front', gaze='up', expr='smile', glasses=True),
    'q1':      dict(src='poet.10.main-poses/q1-approach-bike', box=(104, 0, 180, 70),
                    collar=[(104, 40), (112, 44), (125, 58), (140, 64), (160, 68), (180, 68)],
                    view='3qR', gaze='side', expr='calm', glasses=True),
    'setdown': dict(src='poet.06.main-poses/set-down-03-the-coin', box=(100, 0, 206, 114),
                    collar=[(100, 58), (116, 78), (128, 100), (150, 110), (180, 104), (206, 100)],
                    view='3qR', gaze='down', expr='calm', glasses=True, torso=180.0),
}
HANDS = {
    # open palm raised, fingers up (palms up / welcome)
    'raisedR':  dict(src='poet.11.main-poses/welcome-new-day', side='R', box=(0, 4, 52, 60), base=(42, 55), tip=(15, 12), shape='open-up'),
    'raisedL':  dict(src='poet.11.main-poses/welcome-new-day', side='L', box=(326, 0, 380, 56), base=(336, 49), tip=(366, 8), shape='open-up'),
    # palm up, horizontal (offering)
    'palmupR':  dict(src='poet.07.main-poses/chin-up-open-arms', side='R', box=(0, 100, 46, 152), base=(41, 140), tip=(4, 118), shape='palm-up'),
    'palmupL':  dict(src='poet.07.main-poses/chin-up-open-arms', side='L', box=(298, 96, 350, 152), base=(301, 137), tip=(346, 112), shape='palm-up'),
    # vertical stop palm (fingers up, palm to viewer)
    'stopR':    dict(src='poet.08.main-poses/07-push-flat-through-palm-pushes-aside-reach-oth', side='R', box=(10, 46, 62, 120),
                     base=(36, 114), tip=(34, 52), shape='stop', torso=140.0),
    # flat hand reaching (fingers forward)
    'reachL':   dict(src='poet.08.main-poses/07-push-flat-through-palm-pushes-aside-reach-oth', side='L', box=(236, 38, 291, 80),
                     base=(243, 62), tip=(289, 60), shape='reach', torso=112.0),
    # fists, knuckles to viewer
    'fist12R':  dict(src='poet.12.main-poses/02', side='R', box=(10, 0, 58, 46), base=(33, 44), tip=(30, 5), shape='fist'),
    'fist12L':  dict(src='poet.12.main-poses/02', side='L', box=(234, 0, 280, 46), base=(258, 44), tip=(258, 5), shape='fist'),
    'fist08L':  dict(src='poet.08.main-poses/03-gentle-slow-bent-knee-dance-alone', side='L', box=(176, 44, 216, 99),
                     base=(196, 96), tip=(192, 50), shape='fist'),
    'fist14R':  dict(src='poet.14.muse-dance/cards-2', side='R', box=(5, 0, 50, 44), base=(23, 42), tip=(25, 0), shape='fist',
                     torso=137.0),
    'fist14L':  dict(src='poet.14.muse-dance/cards-2', side='L', box=(143, 2, 188, 46), base=(171, 43), tip=(165, 4), shape='fist',
                     torso=137.0),
}


def fam(src):
    return src.split('/')[0]


def torso_len(mk, src):
    m = mk[src]['markers']
    neck = np.array(m['neck'][:2]); hip = (np.array(m['hipR'][:2]) + np.array(m['hipL'][:2])) / 2
    return float(np.linalg.norm(neck - hip))


def skin(rgb):
    b, g, r = rgb[..., 0].astype(int), rgb[..., 1].astype(int), rgb[..., 2].astype(int)
    gold = (g > 0.72 * r) & (r > 170)
    return (r > 70) & (r > g + 12) & (g > b + 20) & (r - b > 40) & ~gold


def build_lib():
    os.makedirs(LIBDIR, exist_ok=True)
    mk = rig.load_markers()
    meta = {'heads': {}, 'hands': {}}
    for hid, h in HEADS.items():
        im = rig.read_rgba(os.path.join(rig.CUT, h['src'] + '.webp')).astype(np.float32)
        x0, y0, x1, y1 = h['box']
        crop = im[y0:y1, x0:x1].copy()
        Hc, Wc = crop.shape[:2]
        yy, xx = np.mgrid[0:Hc, 0:Wc].astype(np.float32)
        cx = [p[0] - x0 for p in h['collar']]; cyv = [p[1] - y0 for p in h['collar']]
        cyl = np.interp(xx, cx, cyv)
        fig = crop[..., 3] > 127
        al = (crop[..., 3] / 255.) * np.clip((cyl - yy) / 2.5, 0, 1)
        figall = im[..., 3] > 127
        al = rig.strip_edge(al, figall[y0:y1, x0:x1], 3.0)
        edgeok = (yy < cyl - 5).astype(np.float32)   # 1: edged everywhere but the collar seat
        crop[..., 3] = al * 255
        cv2.imwrite(os.path.join(LIBDIR, f'head_{hid}.png'), np.clip(crop, 0, 255).astype(np.uint8))
        cv2.imwrite(os.path.join(LIBDIR, f'headedge_{hid}.png'), (edgeok * 255).astype(np.uint8))
        a, b = np.array(h['collar'][0], float), np.array(h['collar'][-1], float)
        seat = np.array([np.mean([p[0] for p in h['collar']]), np.interp(np.mean([p[0] for p in h['collar']]), [p[0] for p in h['collar']], [p[1] for p in h['collar']])])
        meta['heads'][hid] = dict(h, seat=(seat - (x0, y0)).tolist(), collar_ang=math.atan2(b[1] - a[1], b[0] - a[0]),
                                  torso=(h['torso'] if 'torso' in h else torso_len(mk, h['src'])), family=fam(h['src']))
    for hid, h in HANDS.items():
        im = rig.read_rgba(os.path.join(rig.CUT, h['src'] + '.webp')).astype(np.float32)
        x0, y0, x1, y1 = h['box']
        crop = im[y0:y1, x0:x1].copy()
        sk = skin(crop[..., :3]) & (crop[..., 3] > 127)
        sk = cv2.morphologyEx(sk.astype(np.uint8), cv2.MORPH_CLOSE, np.ones((3, 3), np.uint8))
        n, lab, st, _ = cv2.connectedComponentsWithStats(sk)
        if n > 1:
            k = 1 + np.argmax(st[1:, cv2.CC_STAT_AREA]); sk = (lab == k).astype(np.uint8)
        sk = cv2.morphologyEx(sk, cv2.MORPH_CLOSE, np.ones((5, 5), np.uint8))
        # fill holes (palm creases are dark)
        ff = sk.copy(); hmask = np.zeros((ff.shape[0] + 2, ff.shape[1] + 2), np.uint8)
        cv2.floodFill(ff, hmask, (0, 0), 1)
        sk = sk | (1 - ff)
        m = cv2.dilate(sk, cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (5, 5))) > 0
        m &= crop[..., 3] > 127
        al = m.astype(np.float32)
        figall = im[..., 3] > 127
        al = rig.strip_edge(al, figall[y0:y1, x0:x1], 3.0)
        Hc, Wc = al.shape
        yy, xx = np.mgrid[0:Hc, 0:Wc].astype(np.float32)
        bx, by = h['base'][0] - x0, h['base'][1] - y0
        edgeok = (np.hypot(xx - bx, yy - by) > 9).astype(np.float32)
        crop[..., 3] = al * 255
        cv2.imwrite(os.path.join(LIBDIR, f'hand_{hid}.png'), np.clip(crop, 0, 255).astype(np.uint8))
        cv2.imwrite(os.path.join(LIBDIR, f'handedge_{hid}.png'), (edgeok * 255).astype(np.uint8))
        meta['hands'][hid] = dict(h, base=[bx, by], tip=[h['tip'][0] - x0, h['tip'][1] - y0],
                                  torso=(h['torso'] if 'torso' in h else torso_len(mk, h['src'])), family=fam(h['src']))
    json.dump(meta, open(os.path.join(LIBDIR, 'lib.json'), 'w'), indent=1)
    return meta


class Lib:
    def __init__(self):
        self.meta = json.load(open(os.path.join(LIBDIR, 'lib.json')))
        self.tex = {}

    def _tex(self, kind, iid, mirror=False):
        key = (kind, iid, mirror)
        if key not in self.tex:
            im = cv2.imread(os.path.join(LIBDIR, f'{kind}_{iid}.png'), cv2.IMREAD_UNCHANGED)
            e = cv2.imread(os.path.join(LIBDIR, f'{kind}edge_{iid}.png'), 0).astype(np.float32) / 255.
            if mirror:
                im = im[:, ::-1].copy(); e = e[:, ::-1].copy()
            self.tex[key] = (rig.premul_up(im), cv2.resize(e, None, fx=rig.U, fy=rig.U, interpolation=cv2.INTER_LINEAR))
        return self.tex[key]

    @staticmethod
    def _warp(tex, E, M, W, H):
        """M maps sprite px (not upsampled) -> output px"""
        Mu = M.copy(); Mu[:, :2] = M[:, :2] / rig.U
        lay = cv2.warpAffine(tex, Mu.astype(np.float32), (W, H), flags=cv2.INTER_LINEAR, borderMode=cv2.BORDER_CONSTANT)
        e = cv2.warpAffine(E, Mu.astype(np.float32), (W, H), flags=cv2.INTER_LINEAR, borderMode=cv2.BORDER_CONSTANT)
        return lay, e

    def place_head(self, acc, spec, R, A, Gs, opts, piece, sc_o):
        hid, mirror = (spec if isinstance(spec, (list, tuple)) else (spec, False))
        h = self.meta['heads'][hid]
        tex, E = self._tex('head', hid, mirror)
        Wsp = tex.shape[1] / rig.U
        seat = np.array(h['seat'], float); ang0 = h['collar_ang']
        if mirror:
            seat[0] = Wsp - seat[0]; ang0 = -ang0
        rig_torso = np.linalg.norm(R.J['neck'] - R.J['midhip'])
        s = rig_torso / h['torso'] * opts.get('head_scale', 1.0)
        Mh = A['head']
        rot = math.atan2(Mh[1, 0], Mh[0, 0]) - ang0
        c, si = math.cos(rot), math.sin(rot)
        M = s * np.array([[c, -si], [si, c]])
        target = Mh[:, :2] @ R.J['collar'] + Mh[:, 2] + np.array(opts.get('head_off', (0, 0)))
        t = target - M @ seat
        Mo = np.hstack([Gs[:, :2] @ M, (Gs[:, :2] @ t + Gs[:, 2])[:, None]])
        lay, e = self._warp(tex, E, Mo, acc.shape[1], acc.shape[0])
        return piece(acc, lay, e, sc_o)

    def place_hand(self, acc, spec, side, R, A, Gs, opts, piece, sc_o):
        hid, mirror = (spec if isinstance(spec, (list, tuple)) else (spec, False))
        h = self.meta['hands'][hid]
        tex, E = self._tex('hand', hid, mirror)
        Wsp = tex.shape[1] / rig.U
        base = np.array(h['base'], float); tip = np.array(h['tip'], float)
        if mirror:
            base[0] = Wsp - base[0]; tip[0] = Wsp - tip[0]
        rig_torso = np.linalg.norm(R.J['neck'] - R.J['midhip'])
        s = rig_torso / h['torso'] * opts.get('hand_scale', 1.0)
        Mh = A['hand' + side]
        wr = Mh[:, :2] @ R.J['wr' + side] + Mh[:, 2]
        tp = Mh[:, :2] @ R.J['tip' + side] + Mh[:, 2]
        d = (tp - wr) / np.linalg.norm(tp - wr)
        u = (tip - base) / np.linalg.norm(tip - base)
        rot = math.atan2(d[1], d[0]) - math.atan2(u[1], u[0]) + math.radians(opts.get('hand_rot', {}).get(side, 0.0))
        c, si = math.cos(rot), math.sin(rot)
        M = s * np.array([[c, -si], [si, c]])
        t = (wr - d * 2.5) - M @ base
        Mo = np.hstack([Gs[:, :2] @ M, (Gs[:, :2] @ t + Gs[:, 2])[:, None]])
        lay, e = self._warp(tex, E, Mo, acc.shape[1], acc.shape[0])
        return piece(acc, lay, e, sc_o)

    def place_cuff(self, acc, side, R, A, Gs, sc_o):
        """an empty cuff: the sleeve's round opening, seen at the wrist"""
        Mh = A['farm' + side]
        el = Mh[:, :2] @ R.J['el' + side] + Mh[:, 2]
        wr = Mh[:, :2] @ R.J['wr' + side] + Mh[:, 2]
        d = (wr - el) / np.linalg.norm(wr - el)
        p = Gs[:, :2] @ (wr - d * 1.5) + Gs[:, 2]
        ang = math.degrees(math.atan2(d[1], d[0]))
        ax = (11 * sc_o, 5.5 * sc_o)
        lay8 = np.zeros(acc.shape, np.uint8)
        tan = tuple(int(v) for v in rig.EDGE_TAN) + (255,)
        cv2.ellipse(lay8, (int(p[0]), int(p[1])), (int(ax[1]), int(ax[0])), ang, 0, 360, tan, -1, cv2.LINE_AA)
        cv2.ellipse(lay8, (int(p[0]), int(p[1])), (int(ax[1] * 0.72), int(ax[0] * 0.8)), ang, 0, 360, (14, 14, 18, 255), -1, cv2.LINE_AA)
        lay = lay8.astype(np.float32)
        lay[..., :3] *= lay[..., 3:] / 255.
        return lay


if __name__ == '__main__':
    m = build_lib()
    print(len(m['heads']), 'heads', len(m['hands']), 'hands')
