"""animate(char, keys, out_mp4, ...) -- pose-to-pose animation through the rigs.

keys: list of dicts, in time order
  {'t': seconds the pose LANDS (e.g. the stressed word), 'target': painting id (a marker pose),
   'x': optional stage x (0..1 of the frame width, default 0.5), 'keys': optional pose overrides,
   'label': free text}
Between two keys:
  * the move is rendered in the rig of the NEXT key: on the last held frame of the previous key
    the figure is re-solved in that rig to the previous pose (same markers), so any rig/view
    change happens on a held frame, never mid-motion;
  * bone angles ease with a small anticipation before the move (3 frames) and an overshoot
    and settle after it (back-out easing);
  * standing to standing in the same rig: the feet are planted with two-bone IK; a foot that
    has to travel steps (lifts on an arc and lands) while the other stays planted;
  * hands change drawing on the landing frame; a head change lands 3 frames later (never the
    same frame as the hands);
  * holds breathe (chest swells 0.8 %, 3.3 s cycle) and the pelvis settles 1-2 px.
Every frame is rendered once from the master textures (no frame is made from another frame).
"""
import math, os, json, subprocess, sys
import numpy as np, cv2

from . import core, posing

FPS = 24
STAND_RIGS = ('front', 'q3r')


def smooth(x):
    x = min(1, max(0, x)); return x * x * (3 - 2 * x)


def back_out(x, k=1.0):
    x = min(1, max(0, x)) - 1
    return 1 + x * x * ((k + 1) * x + k)


def wrap(a):
    return (a + math.pi) % (2 * math.pi) - math.pi


def lerpP(PA, PB, u):
    P = {}
    for k in PA:
        if k in ('hipw', 'shw', 'torso_len') or k.startswith('l'):
            P[k] = PA[k] + (PB[k] - PA[k]) * min(1, max(0, u))
        else:
            P[k] = PA[k] + wrap(PB[k] - PA[k]) * u
    return P


def world_T():
    return 190.0          # torso length (neck -> mid-hip) on screen, px at 900 high


def lowest(R, P, G):
    A = R.transforms(P)
    ys = []
    for n in R.order:
        V = R.deform(n, A) @ G[:, :2].T + G[:, 2]
        m = R.mesh[n]
        if len(m['T']):
            ys.append(V[m['T'][m['opaque']].ravel(), 1].max() if m['opaque'].any() else V[:, 1].max())
    return max(ys)


def ik(hip, ank, L1, L2, sign):
    d = ank - hip; dist = min(max(np.linalg.norm(d), 1e-3), (L1 + L2) * 0.999)
    a = math.atan2(d[1], d[0])
    A = math.acos(max(-1, min(1, (L1 * L1 + dist * dist - L2 * L2) / (2 * L1 * dist))))
    th = a - sign * A
    kn = hip + L1 * np.array([math.cos(th), math.sin(th)])
    return th, math.atan2(ank[1] - kn[1], ank[0] - kn[0])


class Stage:
    def __init__(self, char, size=(1600, 900), floor=0.955):
        self.char, self.W, self.H = char, size[0], size[1]
        self.floor = floor * size[1]

    def key_pose(self, k, view=None, mirror=None):
        """solve key k (optionally forced into another rig) and place it on the stage"""
        kk = dict(k.get('keys', {}))
        if view is not None:
            kk['view'] = view + ('_m' if mirror else '')
        pose = posing.pose_from_markers(self.char, k['target'], kk)
        R = posing.rig(self.char, pose['view'])
        Gk = np.array(pose['G'])
        T_rig = np.linalg.norm(np.array(R.J.get('mkneck', R.J['neck'])) - R.J['midhip'])
        s = world_T() / T_rig
        rot = math.atan2(Gk[1, 0], Gk[0, 0])
        c, si = math.cos(rot), math.sin(rot)
        G = np.array([[s * c, -s * si, 0], [s * si, s * c, 0]])
        X = k.get('x', 0.5) * self.W
        if pose['mirror']:
            X = self.W - X
        G[:, 2] = [X, 0]
        G[:, 2] -= G[:, :2] @ R.J['midhip'] - np.array([0, 0])
        low = lowest(R, pose['P'], G)
        G[1, 2] += self.floor - low
        return pose, G

    def render(self, pose, P, G, ss):
        R = posing.rig(self.char, pose['view'])
        img, _ = R.render(P, G, (self.W, self.H), ss=ss, opts=pose['opts'], lib=posing.parts(self.char))
        if pose['mirror']:
            img = img[:, ::-1].copy()
        return img


def plan(char, keys, duration, size=(1600, 900)):
    """frame list: each frame = (rig key index, P, G, pose-with-opts) as plain data"""
    st = Stage(char, size)
    n = int(round(duration * FPS))
    frames = [None] * n
    solved = [st.key_pose(k) for k in keys]
    land = [int(round(k['t'] * FPS)) for k in keys]
    events = []
    for i in range(len(keys)):
        pose_i, G_i = solved[i]
        R = posing.rig(char, pose_i['view'])
        if i == 0:
            prevP, prevG, prev_opts = pose_i['P'], G_i, pose_i['opts']
            start = 0
        else:
            # previous key re-solved in this key's rig (rig change lands on a held frame)
            pp, pg = st.key_pose(keys[i - 1], pose_i['view'], pose_i['mirror'])
            prevP, prevG = pp['P'], pg
            prev_opts = solved[i - 1][0]['opts']
            if solved[i - 1][0]['view'] != pose_i['view'] or solved[i - 1][0]['mirror'] != pose_i['mirror']:
                events.append({'frame': None, 'what': 'rig %s%s -> %s%s on a held frame' % (
                    solved[i - 1][0]['view'], '(m)' if solved[i - 1][0]['mirror'] else '', pose_i['view'], '(m)' if pose_i['mirror'] else '')})
        # move duration from the largest angle change
        dmax = max(abs(wrap(pose_i['P'][k] - prevP[k])) for k in prevP if not (k in ('hipw', 'shw', 'torso_len') or k.startswith('l')))
        dmove = int(round(FPS * min(1.0, max(0.4, 0.35 + 0.45 * dmax / math.pi))))
        L = land[i]
        hold_from = land[i - 1] + 4 if i else 0
        s0 = max(hold_from + 3, L - dmove)
        if i == 0:
            s0 = L = 0
        if events and events[-1]['frame'] is None:
            events[-1]['frame'] = max(s0 - 3, 0)
        nxt = land[i + 1] if i + 1 < len(keys) else n
        # feet: planted IK between two standing keys of the same rig
        same_stand = i > 0 and pose_i['view'] in STAND_RIGS and solved[i - 1][0]['view'] == pose_i['view'] and \
            solved[i - 1][0]['mirror'] == pose_i['mirror']
        J = R.J
        ankA = ankB = None
        if same_stand:
            ankA = {S: prevG[:, :2] @ R.joint_pos(R.transforms(prevP))['an' + S] + prevG[:, 2] for S in 'RL'}
            ankB = {S: G_i[:, :2] @ R.joint_pos(R.transforms(pose_i['P']))['an' + S] + G_i[:, 2] for S in 'RL'}
        f_end = nxt if i + 1 < len(keys) else n
        f_begin = (s0 - 3) if i else 0
        for f in range(max(f_begin, 0), min(f_end, n)):
            if frames[f] is not None and f < s0 - 3:
                continue
            if f < s0:                                 # anticipation: drift 6 % away from the target
                u = -0.06 * smooth((f - (s0 - 3)) / 3)
            elif f < L:
                u = -0.06 + 1.06 * back_out((f - s0) / max(1, L - s0), 1.1)
            else:
                u = 1.0
            P = lerpP(prevP, pose_i['P'], u)
            uc = min(1, max(0, u))
            G = prevG * (1 - uc) + G_i * uc
            # breathing + settle on the hold
            if f >= L:
                P['torso_len'] *= 1 + 0.008 * math.sin(2 * math.pi * (f - L) / 80.0)
            if same_stand and i > 0:
                movers = [S for S in 'RL' if np.linalg.norm(ankB[S] - ankA[S]) > 6]
                win = {}
                if movers:
                    span = max(1, L - s0)
                    for j, S in enumerate(sorted(movers, key=lambda S: -np.linalg.norm(ankB[S] - ankA[S]))):
                        a = s0 + j * span // (len(movers) + 1)
                        win[S] = (a, a + max(4, span * 2 // (len(movers) + 1)))
                A = R.transforms(P)
                for S in 'RL':
                    if S in win:
                        a, b = win[S]; t = smooth((f - a) / max(1, b - a))
                        aw = ankA[S] * (1 - t) + ankB[S] * t
                        if a < f < b:
                            aw = aw + np.array([0, -0.12 * world_T() * math.sin(math.pi * (f - a) / (b - a))])
                    else:
                        aw = ankB[S] if f >= L else ankA[S] * (1 - uc) + ankB[S] * uc
                        aw = ankA[S] if f < L else ankB[S]
                    am = np.linalg.solve(G[:, :2], aw - G[:, 2])
                    hip = A['pelvis'][:, :2] @ J['hip' + S] + A['pelvis'][:, 2]
                    L1 = np.linalg.norm(J['kn' + S] - J['hip' + S]) * P['lthigh' + S]
                    L2 = np.linalg.norm(J['an' + S] - J['kn' + S]) * P['lshin' + S]
                    r_th = math.atan2(*(J['kn' + S] - J['hip' + S])[::-1]); r_sh = math.atan2(*(J['an' + S] - J['kn' + S])[::-1])
                    bend = wrap((P['shin' + S] + r_sh) - (P['thigh' + S] + r_th))
                    th, sh = ik(hip, am, L1, L2, 1 if bend >= 0 else -1)
                    P['thigh' + S] = wrap(th - r_th); P['shin' + S] = wrap(sh - r_sh)
            # parts: old drawings until landing; hands land at L, head at L+3
            opts = dict(pose_i['opts'])
            if i > 0:
                if f < L:
                    opts['hands'] = prev_opts['hands']; opts['head'] = prev_opts['head']; opts['props'] = prev_opts['props']
                elif f < L + 3 and prev_opts['head'] != pose_i['opts']['head'] and prev_opts['hands'] != pose_i['opts']['hands']:
                    opts['head'] = prev_opts['head']
            frames[f] = {'view': pose_i['view'], 'mirror': pose_i['mirror'], 'P': P, 'G': G.tolist(), 'opts': opts, 'key': i}
    for f in range(n):
        if frames[f] is None:
            frames[f] = frames[f - 1]
    return frames, events, solved


_ST = None


def _render_frame(args):
    global _ST
    char, fr, size, ss, bg = args
    if _ST is None:
        _ST = Stage(char, size)
    pose = {'view': fr['view'], 'mirror': fr['mirror'], 'opts': fr['opts']}
    img = _ST.render(pose, fr['P'], np.array(fr['G']), ss)
    a = img[..., 3:] / 255.
    return (img[..., :3] * a + bg * (1 - a)).astype(np.uint8)


def backdrop(size, floor):
    W, H = size
    g = np.linspace(0, 1, H)[:, None, None]
    bg = (np.array([214, 222, 228]) * (1 - g) + np.array([186, 196, 204]) * g) * np.ones((H, W, 3))
    bg[int(floor) + 6:] = np.array([150, 160, 168])
    return bg.astype(np.float32)


def animate(char, keys, out_mp4, duration=None, size=(1600, 900), ss=2, audio=None, strip=None, workers=4, frames_only=None):
    duration = duration or keys[-1]['t'] + 2.0
    frames, events, solved = plan(char, keys, duration, size)
    st = Stage(char, size)
    bg = backdrop(size, st.floor)
    sel = range(len(frames)) if frames_only is None else frames_only
    jobs = [(char, frames[f], size, ss, bg) for f in sel]
    os.makedirs(os.path.dirname(out_mp4), exist_ok=True)
    out = []
    if frames_only is not None:
        import multiprocessing as mp
        with mp.Pool(workers) as pool:
            return list(pool.map(_render_frame, jobs))
    tmp = out_mp4 + '.noaudio.mp4'
    ff = subprocess.Popen(['ffmpeg', '-y', '-loglevel', 'error', '-f', 'rawvideo', '-pix_fmt', 'bgr24', '-s', '%dx%d' % size,
                           '-r', str(FPS), '-i', '-', '-c:v', 'libx264', '-pix_fmt', 'yuv420p', '-crf', '20', '-preset', 'medium',
                           '-tune', 'animation', tmp], stdin=subprocess.PIPE)
    import multiprocessing as mp
    thumbs = []
    with mp.Pool(workers) as pool:
        for f, img in enumerate(pool.imap(_render_frame, jobs, chunksize=4)):
            ff.stdin.write(img.tobytes())
            if f % 24 == 0:
                thumbs.append((f, cv2.resize(img, (320, 180), interpolation=cv2.INTER_AREA)))
            if f % 240 == 0:
                print('frame', f, '/', len(jobs), flush=True)
    ff.stdin.close(); ff.wait()
    if audio:
        subprocess.run(['ffmpeg', '-y', '-loglevel', 'error', '-i', tmp, '-i', audio, '-c:v', 'copy', '-c:a', 'aac', '-b:a', '128k',
                        '-shortest', out_mp4], check=True)
        os.remove(tmp)
    else:
        os.replace(tmp, out_mp4)
    if strip:
        for f, t in thumbs:
            cv2.putText(t, '%.1fs' % (f / FPS), (4, 14), cv2.FONT_HERSHEY_SIMPLEX, 0.4, (0, 0, 0), 1, cv2.LINE_AA)
        per = 10
        rows = [np.hstack([t for _, t in thumbs[i:i + per]] + [np.full((180, 320, 3), 255, np.uint8)] * (per - len(thumbs[i:i + per])))
                for i in range(0, len(thumbs), per)]
        cv2.imwrite(strip, np.vstack(rows), [cv2.IMWRITE_JPEG_QUALITY, 80])
    return frames, events, solved
