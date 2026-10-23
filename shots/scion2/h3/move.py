"""The 4 s move (round 2): palms up (poet.04/04-6) -> fists up (poet.12/02) -> back.

Every frame is rendered once, straight from the front master's textures (no frame is made
from another frame), with the same head/hand drawings the stills use for the two keys:
  palms-up key: head 'chinup' (07/chin-up-open-arms), open raised hands (11/welcome-new-day)
  fists key:    head 'welcome' (11/welcome-new-day), fists (poet.14.muse-dance/cards-2)
Timing (frames at 24 fps):
  0-9 hold, breathing | 10-13 anticipation: knees give, arms sink | 14-33 rise to the fists
  pose, with the feet stepping out one after the other (each boot lifts and lands; the other
  stays planted) | 34-36 overshoot and settle | 36 one-frame anticipation (forearms cock
  down, hands still open) | 37 swap: fists and laughing head land on a held frame |
  37-57 hold, breathing | 58 anticipation (fists pull in) | 59 swap back to open hands and
  the upturned head | 59-83 return, feet stepping back in | 84-87 settle | 88-95 hold.
"""
import math, os, sys, subprocess
import numpy as np, cv2

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import rig, pose

HERE = rig.HERE
A_ID = 'poet.04.main-poses/04-6-rise-flex-reflect'
B_ID = 'poet.12.main-poses/02'
W, H, FPS, N = 1600, 900, 24, 96
SV = 1.85
FLOOR = 862.0


def smooth(x):
    x = min(1, max(0, x)); return x * x * (3 - 2 * x)


def back_out(x, k=1.25):
    x = min(1, max(0, x)); x -= 1
    return 1 + x * x * ((k + 1) * x + k)


def arm_phase(f):
    """0 = palms-up key, 1 = fists key, with overshoot settles"""
    if f < 10: return 0.0
    if f < 14: return -0.05 * smooth((f - 10) / 4)                   # anticipation sink
    if f < 37: return -0.05 + 1.05 * back_out((f - 14) / 22, 1.0)      # rise, overshoot, settle
    if f < 58: return 1.0
    if f == 58: return 1.03                                           # pull-in before the return
    if f < 88: return 1.0 - back_out((f - 59) / 28, 0.8)
    return 0.0


def leg_plan(f):
    """per foot: 0 = A stance, 1 = B stance; R steps first going out and coming back"""
    def step(f, a, b):
        return smooth((f - a) / (b - a))
    if f < 59:
        return {'R': step(f, 15, 22), 'L': step(f, 23, 30)}, {'R': (15, 22), 'L': (23, 30)}
    return {'R': 1 - step(f, 62, 69), 'L': 1 - step(f, 70, 77)}, {'R': (62, 69), 'L': (70, 77)}


def ik(hip, ank, L1, L2, sign):
    d = ank - hip; dist = min(np.linalg.norm(d), (L1 + L2) * 0.999)
    a = math.atan2(d[1], d[0])
    A = math.acos(max(-1, min(1, (L1 * L1 + dist * dist - L2 * L2) / (2 * L1 * dist))))
    th = a - sign * A
    kn = hip + L1 * np.array([math.cos(th), math.sin(th)])
    return th, math.atan2(ank[1] - kn[1], ank[0] - kn[0])


def main(ss=2):
    fr_dir = os.path.join(HERE, 'frames'); os.makedirs(fr_dir, exist_ok=True)
    out_dir = os.path.join(HERE, 'out'); os.makedirs(out_dir, exist_ok=True)
    R = pose.get_rig('front'); L = pose.get_lib(); J = R.J
    keys = []
    for tid in (A_ID, B_ID):
        P, G, view, opts, info = pose.solve(tid)
        jp = R.joint_pos(R.transforms(P))
        sole = max(jp['anR'][1] + 46, jp['anL'][1] + 46, jp['toR'][1] + 8, jp['toL'][1] + 8)
        hipw = np.array([W / 2, FLOOR - SV * (sole - J['midhip'][1])])
        keys.append(dict(P=P, opts=opts, jp=jp, hipw=hipw,
                         ankw={S: hipw + SV * (jp['an' + S] - J['midhip']) for S in 'RL'}))
    PA, PB = keys[0]['P'], keys[1]['P']
    r_th = {S: math.atan2(*(J['kn' + S] - J['hip' + S])[::-1]) for S in 'RL'}
    r_sh = {S: math.atan2(*(J['an' + S] - J['kn' + S])[::-1]) for S in 'RL'}
    frames = []
    SEL = [int(x) for x in os.environ.get('MOVE_FRAMES', '').split(',') if x]
    for f in range(N):
        if SEL and f not in SEL:
            continue
        u = arm_phase(f)
        P = {}
        for k in PA:
            if k in ('hipw', 'shw', 'torso_len') or k.startswith('l'):
                P[k] = PA[k] + (PB[k] - PA[k]) * min(1, max(0, u))
            else:
                P[k] = PA[k] + pose.wrap(PB[k] - PA[k]) * u
        # one-frame anticipations before each swap: forearms cock down / fists pull in
        if f == 36:
            P['farmR'] += math.radians(-14); P['farmL'] += math.radians(14)
            P['handR'] = P['farmR']; P['handL'] = P['farmL']
        # breathing on the holds: chest swells 0.8%, shoulders rise
        br = math.sin(2 * math.pi * f / 40.0)
        P['torso_len'] *= 1 + 0.008 * br
        # weight: pelvis sinks in the anticipation and through the steps
        dip = 9 * smooth((f - 9) / 5) * (1 - smooth((f - 30) / 8)) if f < 40 else 7 * math.sin(math.pi * min(1, max(0, (f - 59) / 22)))
        steps, spans = leg_plan(f)
        hipw = keys[0]['hipw'] * (1 - min(1, max(0, u))) + keys[1]['hipw'] * min(1, max(0, u)) + np.array([0, dip])
        # hips shift over the planted foot during each step
        for S, (a, b) in spans.items():
            if a <= f <= b:
                other = 'L' if S == 'R' else 'R'
                stance = keys[1] if (f < 59) == (steps[other] > 0.5) else keys[0]
                pull = math.sin(math.pi * (f - a) / (b - a))
                hipw = hipw + np.array([(stance['ankw'][other][0] - hipw[0]) * 0.12 * pull, 0])
        G = np.array([[SV, 0, 0], [0, SV, 0]], float); G[:, 2] = hipw - SV * J['midhip']
        A = R.transforms(P)
        for S in 'RL':
            t = steps[S]
            aw = keys[0]['ankw'][S] * (1 - t) + keys[1]['ankw'][S] * t
            a, b = spans[S]
            if a < f < b:
                aw = aw + np.array([0, -20 * math.sin(math.pi * (f - a) / (b - a))])   # the boot lifts
            am = (aw - G[:, 2]) / SV
            hip = A['pelvis'][:, :2] @ J['hip' + S] + A['pelvis'][:, 2]
            L1 = np.linalg.norm(J['kn' + S] - J['hip' + S]) * P['lthigh' + S]
            L2 = np.linalg.norm(J['an' + S] - J['kn' + S]) * P['lshin' + S]
            bend = pose.wrap((P['shin' + S] + r_sh[S]) - (P['thigh' + S] + r_th[S]))
            th, sh = ik(hip, am, L1, L2, 1 if bend >= 0 else -1)
            P['thigh' + S] = pose.wrap(th - r_th[S]); P['shin' + S] = pose.wrap(sh - r_sh[S])
            # planted boot keeps its key angle; a stepping boot turns between them
            P['foot' + S] = PA['foot' + S] * (1 - t) + PB['foot' + S] * t
        fists = 37 <= f < 59
        opts = dict(keys[1]['opts'] if fists else keys[0]['opts'])
        img, _ = R.render(P, G, (W, H), ss=ss, opts=opts, lib=L)
        bg = np.full((H, W, 3), 236, np.float32)
        cv2.line(bg, (0, int(FLOOR)), (W, int(FLOOR)), (205, 205, 205), 2)
        al = img[..., 3:] / 255.
        frame = (img[..., :3] * al + bg * (1 - al)).astype(np.uint8)
        cv2.imwrite(os.path.join(fr_dir, f'{f:03d}.png'), frame)
        frames.append(frame)
        print(f, round(u, 3), flush=True)
    if SEL:
        return
    mp4 = os.path.join(out_dir, 'move.mp4')
    subprocess.run(['ffmpeg', '-y', '-loglevel', 'error', '-framerate', str(FPS), '-i', os.path.join(fr_dir, '%03d.png'),
                    '-c:v', 'libx264', '-pix_fmt', 'yuv420p', '-crf', '17', '-preset', 'slow', '-tune', 'animation', mp4], check=True)
    th = [cv2.resize(fr, (400, 225), interpolation=cv2.INTER_AREA) for fr in frames[::6]]
    for i, t in enumerate(th):
        cv2.putText(t, f'f{i * 6}', (6, 18), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 0), 1, cv2.LINE_AA)
    cv2.imwrite(os.path.join(out_dir, 'move_strip.jpg'), np.vstack([np.hstack(th[i:i + 4]) for i in range(0, len(th), 4)]),
                [cv2.IMWRITE_JPEG_QUALITY, 85])


if __name__ == '__main__':
    main(int(sys.argv[1]) if len(sys.argv) > 1 else 2)
