"""The move: palms up (04/04-6) -> fists up (12/02) -> back, 4 s @ 24 fps, 1600x900, by replacement.
Every frame is one whole painting (or, on a 2-frame dissolve, two), placed with uniform scale and
translation only. Scale: each drawing is scaled so the man's head-to-ankle height is the same.
Placement: the midpoint between the ankles sits on the same screen x, the lowest boot pixel on one floor line."""
import sys, os, json, subprocess, cv2, numpy as np
sys.path.insert(0, os.path.dirname(__file__)); import h2
OUT = os.path.join(h2.ROOT, 'shots/scion2/h2/out')
W, H, FPS = 1600, 900, 24
HEIGHT = 540          # head-marker to ankle-marker height on screen, px
FLOOR, CX = 840, 800
BG = np.array([225, 230, 234], np.float32)   # BGR, light warm grey

A = 'poet.04.main-poses/04-6-rise-flex-reflect'
B = 'poet.12.main-poses/02'
ASK = 'poet.05.main-poses/ask-the-universe-2'
WEL = 'poet.11.main-poses/welcome-new-day'
GUI = 'poet.11.main-poses/02-front-guide-stone'

# (drawing, frames) or ('dissolve', from, to, frames)
# (drawing, frames) or ('dissolve', from, to, frames).
# v1 used two 2-frame dissolves (ask>welcome, guide>palms); at full size they read as a translucent
# double man with four arms and two offset heads, so v2 is all cuts. The dissolve code stays for the record.
TIMING = [
    (A, 14),                 # key: palms up, held
    (ASK, 6),                # dip: arms sink and open before the throw (anticipation)
    (WEL, 6),                # arms fly up, hands still open
    (B, 30),                 # key: fists up -- cut on the hit at f26 (1.08 s), held through f55
    (WEL, 6),                # fists open, release
    (GUI, 10),               # arms drop low, palms forward, stance narrows
    (A, 24),                 # key: palms up again, held to the end
]

def layer(pid):
    im = h2.img(pid); P = h2.pose(pid)
    ank = (P['ankleL'][:2] + P['ankleR'][:2]) / 2
    s = HEIGHT / (ank[1] - P['head'][1])
    ys = np.where((im[:, :, 3] > 128).any(1))[0]
    floor_src = ys.max()
    tx = CX - s * ank[0]; ty = FLOOR - s * floor_src
    M = np.array([[s, 0, tx], [0, s, ty]], np.float32)
    rgba = cv2.warpAffine(im, M, (W, H), flags=cv2.INTER_AREA if s < 1 else cv2.INTER_CUBIC,
                          borderMode=cv2.BORDER_CONSTANT, borderValue=(0, 0, 0, 0)).astype(np.float32)
    return rgba, dict(src=pid, scale=round(float(s), 4), tx=round(float(tx), 1), ty=round(float(ty), 1))

def ground():
    g = np.tile(BG, (H, W, 1))
    g[FLOOR + 6:] = BG * 0.93
    # soft contact shadow, the same for every drawing (it does not move)
    sh = np.zeros((H, W), np.float32)
    cv2.ellipse(sh, (CX, FLOOR + 4), (170, 16), 0, 0, 360, 1.0, -1)
    sh = cv2.GaussianBlur(sh, (0, 0), 9) * 0.28
    return g * (1 - sh[:, :, None])

def over(bg, rgba, alpha=1.0):
    a = rgba[:, :, 3:4] / 255.0 * alpha
    return rgba[:, :, :3] * a + bg * (1 - a)

def main():
    cache = {}
    def L(p):
        if p not in cache: cache[p] = layer(p)
        return cache[p][0]
    g = ground(); frames = []; log = []
    for step in TIMING:
        if step[0] == 'dissolve':
            _, a, b, n = step
            for i in range(n):
                t = (i + 1) / (n + 1)
                # dissolve: the outgoing drawing fades over the incoming one (both whole paintings)
                f = over(over(g, L(b), t), L(a), 1 - t)
                frames.append(f); log.append(dict(frame=len(frames) - 1, dissolve=[a, b], t=round(t, 3)))
        else:
            p, n = step
            f = over(g, L(p))
            for i in range(n):
                frames.append(f); log.append(dict(frame=len(frames) - 1, src=p))
    assert len(frames) == 96, len(frames)
    tmp = os.path.join(OUT, '_frames'); os.makedirs(tmp, exist_ok=True)
    for i, f in enumerate(frames):
        cv2.imwrite(os.path.join(tmp, f'{i:03d}.png'), np.clip(f, 0, 255).astype(np.uint8))
    subprocess.run(['ffmpeg', '-y', '-loglevel', 'error', '-framerate', str(FPS), '-i', os.path.join(tmp, '%03d.png'),
                    '-c:v', 'libx264', '-pix_fmt', 'yuv420p', '-crf', '24', '-preset', 'slow', '-movflags', '+faststart',
                    os.path.join(OUT, 'move.mp4')], check=True)
    # contact strip: every 6th frame
    tiles = []
    for i in range(0, 96, 6):
        t = cv2.resize(np.clip(frames[i], 0, 255).astype(np.uint8), (400, 225), interpolation=cv2.INTER_AREA)
        e = log[i]; name = e.get('src') or ('dissolve ' + ' > '.join(x.split('/')[0][5:7] + '/' + x.split('/')[1][:10] for x in e['dissolve']))
        if 'src' in e: name = name.split('/')[0][5:7] + '/' + name.split('/')[1][:22]
        h2.put_text(t, f'f{i:02d}  {name}', (5, 16), 0.42)
        tiles.append(t)
    strip = np.vstack([np.hstack(tiles[r * 4:(r + 1) * 4]) for r in range(4)])
    cv2.imwrite(os.path.join(OUT, 'move_strip.jpg'), strip, [cv2.IMWRITE_JPEG_QUALITY, 85])
    json.dump(dict(fps=FPS, size=[W, H], timing=[list(s) for s in TIMING],
                   placement={k: v[1] for k, v in cache.items()}, frames=log), open(os.path.join(OUT, 'move.json'), 'w'), indent=1)
    for f in os.listdir(tmp): os.remove(os.path.join(tmp, f))
    os.rmdir(tmp)

if __name__ == '__main__':
    main()
