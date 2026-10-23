"""H1 move: palms up (04-6) -> fists up (12/02) -> palms up, 4 s at 24 fps, 1600x900.

The keys are the two paintings. Every frame between is a target pose interpolated in
bone-angle space; the frame is the nearest painting (pose graph over all clean paintings,
with hysteresis) deformed toward it with the same capped skinned mesh warp as the stills.
When the nearest painting changes, the frame cuts to the other warped drawing (a
dissolve was tried and showed two men at once).
"""
import os, sys, json, math, subprocess
from multiprocessing import Pool
import numpy as np, cv2
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import h1core as H, h1render as R

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, 'out')
FPS, SECS, W, HH = 24, 4, 1600, 900
FIG_H = 640          # on-screen height of the palms-up painting
FLOOR = 840
BG = (232, 236, 238)  # BGR, pale paper grey
A_ID = 'poet.04.main-poses/04-6-rise-flex-reflect'
B_ID = 'poet.12.main-poses/02'
SWITCH_MARGIN = .06
DISSOLVE = 0   # a 3-frame dissolve showed two men at once; a cut inside the fast part of the move reads better


def fig_bbox(pid):
    a = H.load_rgba(pid)[..., 3] > 20
    ys, xs = np.nonzero(a)
    return xs.min(), ys.min(), xs.max(), ys.max()


def screen_markers(pid, k, anchor):
    """markers of a painting placed on screen: scale k, its groin at anchor x, boots on FLOOR"""
    M = H.markers(H.load_targets()[pid])
    x0, y0, x1, y1 = fig_bbox(pid)
    out = {}
    for n, p in M.items():
        out[n] = np.array([anchor + (p[0] - M['groin'][0]) * k, FLOOR - (y1 - p[1]) * k])
    return out


def interp_pose(A, B, t):
    """bone-angle interpolation (lengths too), rebuilt from the groin"""
    P = {'groin': (1 - t) * A['groin'] + t * B['groin']}
    def lerp_vec(a0, a1, b0, b1):
        va, vb = A[a1] - A[a0], B[b1] - B[b0]
        la, lb = np.linalg.norm(va), np.linalg.norm(vb)
        aa, ab = math.atan2(va[1], va[0]), math.atan2(vb[1], vb[0])
        d = (ab - aa + math.pi) % (2 * math.pi) - math.pi
        an = aa + t * d; ln = (1 - t) * la + t * lb
        return np.array([math.cos(an), math.sin(an)]) * ln
    for k in ['neck', 'hipL', 'hipR']:
        P[k] = P['groin'] + lerp_vec('groin', k, 'groin', k)
    for k in ['shoulderL', 'shoulderR', 'chin', 'head']:
        P[k] = P['neck'] + lerp_vec('neck', k, 'neck', k)
    for sd in 'LR':
        for a, b in [('shoulder', 'elbow'), ('elbow', 'wrist'), ('hip', 'knee'), ('knee', 'ankle'), ('ankle', 'toe')]:
            P[b + sd] = P[a + sd] + lerp_vec(a + sd, b + sd, a + sd, b + sd)
    return P


def ease(x):
    return x * x * (3 - 2 * x)


def timeline():
    """per frame: blend weight toward B. holds on the painted keys, eased moves between"""
    n = FPS * SECS
    w = []
    for f in range(n + 1):
        u = f / n
        if u < .08: x = 0
        elif u < .44: x = ease((u - .08) / .36)
        elif u < .56: x = 1
        elif u < .92: x = 1 - ease((u - .56) / .36)
        else: x = 0
        w.append(x)
    return w


def place(canvas_pm, off, frame):
    """composite a premultiplied canvas (target coords + off) onto the frame"""
    h, w = canvas_pm.shape[:2]
    x0, y0 = int(round(-off[0])), int(round(-off[1]))
    fx0, fy0 = max(0, x0), max(0, y0)
    fx1, fy1 = min(W, x0 + w), min(HH, y0 + h)
    if fx1 <= fx0 or fy1 <= fy0:
        return frame
    c = canvas_pm[fy0 - y0:fy1 - y0, fx0 - x0:fx1 - x0]
    a = c[..., 3:4] / 255.
    reg = frame[fy0:fy1, fx0:fx1].astype(np.float32)
    frame[fy0:fy1, fx0:fx1] = np.clip(c[..., :3] + reg * (1 - a), 0, 255).astype(np.uint8)
    return frame


_T = None


def _render_frame(job):
    f, T, pid, v = job
    targets = H.load_targets()
    frame = np.full((HH, W, 3), BG, np.uint8)
    can, inf = R.render(pid, v, T, targets, None)
    frame = place(can, inf['off'], frame)
    cv2.imwrite(os.path.join(HERE, '_frames', '%03d.png' % f), frame)
    return dict(want=inf['F']['want'])


def main():
    targets = H.load_targets()
    xa0, ya0, xa1, ya1 = fig_bbox(A_ID)
    ka = FIG_H / (ya1 - ya0)
    A = screen_markers(A_ID, ka, W / 2)
    # B at the same body size: match neck-to-ankle span
    Mb = H.markers(targets[B_ID]); Ma = H.markers(targets[A_ID])
    span = lambda M: np.linalg.norm(M['neck'] - (M['ankleL'] + M['ankleR']) / 2)
    kb = ka * span(Ma) / span(Mb)
    B = screen_markers(B_ID, kb, W / 2)
    Ca, Cb = H.conf(targets[A_ID]), H.conf(targets[B_ID])
    Ct = {k: min(Ca[k], Cb[k]) for k in Ca}
    pool = H.CLEAN  # the pose graph: every clean painting, keys included

    ws = timeline()
    frames_dir = os.path.join(HERE, '_frames'); os.makedirs(frames_dir, exist_ok=True)
    log = []
    cur = None
    # pass 1: walk the pose graph (sequential, with hysteresis)
    plan = []
    for f, x in enumerate(ws):
        T = interp_pose(A, B, x)
        ranked = H.rank_sources(A_ID, targets, exclude_family=False, allow=pool, T=T, Ct=Ct, costume=False)
        best = ranked[0]
        if cur is not None:
            cur_c = next((r for r in ranked if r[1] == cur[1] and r[2] == cur[2]), None)
            # change painting when another is clearly nearer, or when this one would need
            # more than the cap and another needs less
            if cur_c is None or best[0] < cur_c[0] - SWITCH_MARGIN or \
                    (cur_c[3]['maxover'] > 0 and best[3]['maxover'] < cur_c[3]['maxover']):
                cur = best
            else:
                cur = cur_c
        else:
            cur = best
        plan.append((f, x, T, cur))
    # pass 2: render
    jobs = [(f, T, c[1], c[2]) for f, x, T, c in plan]
    with Pool(2, maxtasksperchild=12) as pool_:
        infos = pool_.map(_render_frame, jobs)
    for (f, x, T, c), F in zip(plan, infos):
        log.append(dict(frame=f, toward_fists=round(x, 3), source=c[1], mirrored=c[2]['mirror'],
                        cost=round(c[0], 3),
                        beyond_cap={b: round(F['want'][b], 1) for b in H.BONES
                                    if abs(F['want'][b]) > H.CAP and not b.startswith('foot')}))
        print(f, round(x, 2), c[1].split('/')[1][:24], 'mirror' if c[2]['mirror'] else '', log[-1]['beyond_cap'])
    json.dump(log, open(os.path.join(OUT, 'move_log.json'), 'w'), indent=1)
    subprocess.run(['ffmpeg', '-y', '-loglevel', 'error', '-framerate', str(FPS), '-i', os.path.join(frames_dir, '%03d.png'),
                    '-frames:v', str(FPS * SECS), '-c:v', 'libx264', '-pix_fmt', 'yuv420p', '-crf', '26', '-preset', 'slow',
                    os.path.join(OUT, 'move.mp4')], check=True)
    # contact strip: every 6th frame
    tiles = []
    for f in range(0, FPS * SECS + 1, 6):
        im = cv2.imread(os.path.join(frames_dir, '%03d.png' % f))
        im = im[40:880, 400:1200]
        im = cv2.resize(im, (240, 252), interpolation=cv2.INTER_AREA)
        cv2.putText(im, str(f), (6, 18), cv2.FONT_HERSHEY_SIMPLEX, .5, (0, 0, 0), 1, cv2.LINE_AA)
        tiles.append(im)
    rows = [np.hstack(tiles[i:i + 9]) for i in range(0, len(tiles), 9)]
    if rows[-1].shape[1] < rows[0].shape[1]:
        rows[-1] = np.hstack([rows[-1], np.full((252, rows[0].shape[1] - rows[-1].shape[1], 3), 255, np.uint8)])
    cv2.imwrite(os.path.join(OUT, 'move_strip.jpg'), np.vstack(rows), [cv2.IMWRITE_JPEG_QUALITY, 88])


if __name__ == '__main__':
    main()
