"""The 4 s move: palms up (poet.04/04-6) -> fists up (poet.12/02) -> back, every frame from the rig.

Keys: the rig posed toward each painting's markers (pose.solve).  In between, bone angles
are eased (wrap-aware); the legs are solved by 2-bone IK so the boots stay on one floor,
the travelling foot lifts on a small arc, and the pelvis dips through the change (weight).
Hands change drawing (open palm -> borrowed fist) by a one-frame replacement swap while
the forearms are moving fastest.
"""
import math, os, sys, json, subprocess
import numpy as np, cv2

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import rig, pose

HERE = rig.HERE
A_ID = 'poet.04.main-poses/04-6-rise-flex-reflect'
B_ID = 'poet.12.main-poses/02'
W, H, FPS, SEC = 1600, 900, 24, 4
SV = 1.82                 # px per master px on the video canvas
FLOOR = 860.0
J = rig.J


def ease(x):
    x = min(1, max(0, x))
    return x * x * (3 - 2 * x)


def phase(f):
    """0..1..0 over 96 frames: hold, go, hold, return, hold."""
    t = f / FPS
    if t < 0.4: return 0.0
    if t < 1.55: return ease((t - 0.4) / 1.15)
    if t < 2.25: return 1.0
    if t < 3.45: return 1 - ease((t - 2.25) / 1.2)
    return 0.0


def lerp_ang(a, b, u):
    return a + pose.wrap(b - a) * u


def sole_y(jp):
    return max(jp['anR'][1] + 46, jp['anL'][1] + 46, jp['toR'][1] + 8, jp['toL'][1] + 8)


def ik(hip, ank, L1, L2, bend_sign):
    d = ank - hip; dist = np.linalg.norm(d)
    dist_c = min(dist, (L1 + L2) * 0.999)
    a = math.atan2(d[1], d[0])
    cosA = (L1 * L1 + dist_c * dist_c - L2 * L2) / (2 * L1 * dist_c)
    A = math.acos(max(-1, min(1, cosA)))
    th = a - bend_sign * A
    knee = hip + L1 * np.array([math.cos(th), math.sin(th)])
    sh = math.atan2(ank[1] - knee[1], ank[0] - knee[0])
    return th, sh


def main(out_dir=None, ss=2):
    out_dir = out_dir or os.path.join(HERE, 'out')
    fr_dir = os.path.join(HERE, 'frames'); os.makedirs(fr_dir, exist_ok=True)
    R = pose.get_rig()
    keys = []
    for tid in (A_ID, B_ID):
        P, G, size, info = pose.solve(tid)
        A = R.transforms(P)
        jp = R.joint_pos(A)
        keys.append(dict(P=P, jp=jp, info=info, sole=sole_y(jp)))
    PA, PB = keys[0]['P'], keys[1]['P']
    # world placement of each key: midhip x at centre, soles on the floor
    for k in keys:
        k['hipw'] = np.array([W / 2, FLOOR - SV * (k['sole'] - J['midhip'][1])])
        k['ankw'] = {S: k['hipw'] + SV * (k['jp']['an' + S] - J['midhip']) for S in 'RL'}
    # boot travel: which foot moves more
    mv = {S: np.linalg.norm(keys[1]['ankw'][S] - keys[0]['ankw'][S]) for S in 'RL'}
    frames = []
    n = SEC * FPS
    prev_u = 0
    SEL = [int(x) for x in os.environ.get('MOVE_FRAMES', '').split(',') if x]
    for f in range(n):
        if SEL and f not in SEL:
            continue
        u = phase(f)
        du = abs(u - prev_u); prev_u = u
        P = {}
        for k in PA:
            if k in ('hipw', 'shw', 'torso_len') or k.startswith('l'):
                P[k] = PA[k] + (PB[k] - PA[k]) * u
            else:
                P[k] = lerp_ang(PA[k], PB[k], u)
        dip = 14 * math.sin(math.pi * u)          # pelvis sinks through the change
        hipw = keys[0]['hipw'] * (1 - u) + keys[1]['hipw'] * u + np.array([0, dip])
        G = np.array([[SV, 0, 0], [0, SV, 0]], float); G[:, 2] = hipw - SV * J['midhip']
        Ginv = lambda p: (p - G[:, 2]) / SV
        A = R.transforms(P)
        for S in 'RL':
            aw = keys[0]['ankw'][S] * (1 - u) + keys[1]['ankw'][S] * u
            if mv[S] > 4:
                aw = aw + np.array([0, -16 * math.sin(math.pi * u) * (mv[S] / max(mv.values()))])
            am = Ginv(aw)
            hip = A['thigh' + S][:, :2] @ J['hip' + S] + A['thigh' + S][:, 2]
            hip = A['pelvis'][:, :2] @ J['hip' + S] + A['pelvis'][:, 2]
            L1 = np.linalg.norm(J['kn' + S] - J['hip' + S]) * P['lthigh' + S]
            L2 = np.linalg.norm(J['an' + S] - J['kn' + S]) * P['lshin' + S]
            r_th = math.atan2(*(J['kn' + S] - J['hip' + S])[::-1])
            r_sh = math.atan2(*(J['an' + S] - J['kn' + S])[::-1])
            # geometric knee bend of the eased pose decides which side the knee goes
            bend = pose.wrap((P['shin' + S] + r_sh) - (P['thigh' + S] + r_th))
            sign = 1 if bend >= 0 else -1
            th, sh = ik(hip, am, L1, L2, sign)
            r_th = math.atan2(*(J['kn' + S] - J['hip' + S])[::-1])
            r_sh = math.atan2(*(J['an' + S] - J['kn' + S])[::-1])
            P['thigh' + S] = pose.wrap(th - r_th)
            P['shin' + S] = pose.wrap(sh - r_sh)
        yaw = keys[0]['info']['head_yaw'] * (1 - u) + keys[1]['info']['head_yaw'] * u
        # hand drawings: open palm until the swap, fist after; 3-frame dissolve at u ~ 0.5
        mix = 1.0 if u >= 0.5 else 0.0     # replacement swap on one frame (no ghosting dissolve)
        if mix <= 0:
            img, _ = R.render(P, G, (W, H), ss=ss, head_yaw=yaw)
        elif mix >= 1:
            img, _ = R.render(P, G, (W, H), ss=ss, head_yaw=yaw, hands={'R': 'fist', 'L': 'fist'})
        else:
            a, _ = R.render(P, G, (W, H), ss=ss, head_yaw=yaw)
            b, _ = R.render(P, G, (W, H), ss=ss, head_yaw=yaw, hands={'R': 'fist', 'L': 'fist'})
            fa = a.astype(np.float32); fb = b.astype(np.float32)
            pa = fa[..., :3] * fa[..., 3:] / 255.; pb = fb[..., :3] * fb[..., 3:] / 255.
            al = fa[..., 3:] * (1 - mix) + fb[..., 3:] * mix
            pr = pa * (1 - mix) + pb * mix
            img = np.dstack([np.where(al > 0, pr / np.maximum(al, 1e-3) * 255, 0), al]).clip(0, 255).astype(np.uint8)
        bg = np.full((H, W, 3), 236, np.float32)
        cv2.line(bg, (0, int(FLOOR)), (W, int(FLOOR)), (200, 200, 200), 2)
        al = img[..., 3:] / 255.
        frame = (img[..., :3] * al + bg * (1 - al)).astype(np.uint8)
        cv2.imwrite(os.path.join(fr_dir, f'{f:03d}.png'), frame)
        frames.append(frame)
        print(f, round(u, 3), flush=True)
    if SEL:
        return
    os.makedirs(out_dir, exist_ok=True)
    mp4 = os.path.join(out_dir, 'move.mp4')
    subprocess.run(['ffmpeg', '-y', '-loglevel', 'error', '-framerate', str(FPS), '-i', os.path.join(fr_dir, '%03d.png'),
                    '-c:v', 'libx264', '-pix_fmt', 'yuv420p', '-crf', '26', '-preset', 'slow', mp4], check=True)
    # contact strip: every 6th frame
    th = [cv2.resize(fr, (400, 225), interpolation=cv2.INTER_AREA) for fr in frames[::6]]
    for i, t in enumerate(th):
        cv2.putText(t, f'f{i * 6}', (6, 18), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 0), 1, cv2.LINE_AA)
    rows = [np.hstack(th[i:i + 4]) for i in range(0, len(th), 4)]
    cv2.imwrite(os.path.join(out_dir, 'move_strip.jpg'), np.vstack(rows), [cv2.IMWRITE_JPEG_QUALITY, 85])


if __name__ == '__main__':
    main(ss=int(sys.argv[1]) if len(sys.argv) > 1 else 2)
