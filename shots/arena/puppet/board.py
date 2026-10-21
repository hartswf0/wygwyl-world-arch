"""Critic boards for the 3D-drawn puppet.

    python3 shots/arena/puppet/board.py ACT-010 [--turn 80]

  out/<ACT>/keys.png        authored acting beats, the vignette's own camera, no captions (cold read)
                            --yaw/--elev steer the camera: keys_yaw<Y>_elev<E>.png
  out/<ACT>/turn_f<N>.png   one frame from eight directions, 45 degrees apart: steerability
  out/<ACT>/vs_main.png     the main sheet (body_profile.jpg) beside the puppet standing in profile
  out/<ACT>/notes.json      per frame: head chosen, view angle, expression, hands asked
"""
import argparse, json, math, os, sys
import numpy as np
from PIL import Image, ImageDraw

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import p3d

TEXTURE = ('passing', 'heel strike', 'weight onto', 'trailing foot', 'toe off', 'contact')
BG = (23, 25, 31)


def crop(img, cam, pelvis, w_cm=150, h_top=125, h_bot=105):
    c = cam.P(pelvis)
    x0, x1 = c[0] - w_cm / 2 * cam.s, c[0] + w_cm / 2 * cam.s
    y0, y1 = c[1] - h_top * cam.s, c[1] + h_bot * cam.s
    return img.crop((int(x0), int(y0), int(x1), int(y1)))


def strip(ims, h=520, pad=12, labels=None):
    ims = [i.resize((max(1, int(i.size[0] * h / i.size[1])), h)) for i in ims]
    S = Image.new('RGB', (sum(i.size[0] for i in ims) + pad * (len(ims) + 1), h + pad * 2 + (26 if labels else 0)), BG)
    d = ImageDraw.Draw(S)
    x = pad
    for k, i in enumerate(ims):
        S.paste(i, (x, pad + (26 if labels else 0)))
        if labels:
            d.text((x + 4, 6), labels[k], fill=(220, 220, 220), font=p3d.vec and _font(18))
        x += i.size[0] + pad
    return S


def _font(n):
    from PIL import ImageFont
    for p in ('/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf',):
        if os.path.exists(p):
            return ImageFont.truetype(p, n)
    return ImageFont.load_default()


def beats(tid):
    B = json.load(open(os.path.join(p3d.ARENA, 'bolas', 'bank', 'beats.json'))).get(tid, [])
    out = []
    for b in B:
        if not any(w in b['beat'].lower() for w in TEXTURE) and b['f'] not in out:
            out.append(b['f'])
    return out


def run(act, turn=None, yaw=None, elev=None):
    P = p3d.Puppet(act)
    out = os.path.join(HERE, 'out', act)
    os.makedirs(out, exist_ok=True)
    fs = [f for f in beats(P.tid) if f < len(P.V['frames'])]
    notes = {}
    ims = []
    for f in fs:
        img, nt = P.render(f, yaw=yaw, elev=elev)
        a = P.V['frames'][f]['a']
        pel = np.mean([np.array(v['j'][0], float) for v in a.values()], axis=0)
        cam = p3d.Camera(P.V['view'], yaw=yaw, elev=elev)
        ims.append(crop(img, cam, pel, w_cm=150 * len(a)))
        notes[f] = nt
    tag = '' if yaw is None and elev is None else f'_yaw{yaw}_elev{elev}'
    hidden = [f for f, nt in notes.items() if any(n.get('face_hidden_by') for n in nt)]
    strip(ims).save(os.path.join(out, f'keys{tag}.png'))
    print('face hidden behind a held prop on frames:', hidden or 'none')
    # turnaround
    f = turn if turn is not None else (fs[len(fs) // 2] if fs else 0)
    a0 = list(P.V['frames'][f]['a'].values())[0]
    pel = np.array(a0['j'][0], float)
    centre = [pel[0], 95, pel[2]]
    base = P.V['view'].get('yaw', -22)
    ims, labels = [], []
    for k in range(8):
        yaw = base + 45 * k
        img, nt = P.render(f, yaw=yaw, centre=centre)
        cam = p3d.Camera(P.V['view'], yaw=yaw, centre=centre)
        ims.append(crop(img, cam, pel))
        labels.append(f'yaw {yaw:+.0f}  {nt[0]["head"].replace("man.head.", "")}  {nt[0]["view_angle"]:+d}')
    strip(ims, h=460, labels=labels).save(os.path.join(out, f'turn_f{f}.png'))
    # against the main sheet: frame 0, camera square to the body's side
    a0 = list(P.V['frames'][0]['a'].values())[0]
    j, Rc, R0 = P.frames_of(a0)
    side_yaw = math.degrees(math.atan2(R0['fwd'][2], R0['fwd'][0]))   # camera looks along -x of the body
    pel = j['pelvis']
    centre = [pel[0], 95, pel[2]]
    best = None
    for yaw in range(-180, 180, 5):
        cam = p3d.Camera(P.V['view'], yaw=yaw, elev=4, centre=centre)
        d = cam.dir(R0['fwd'])
        if best is None or abs(d[2]) < best[0] and d[0] > 0:
            best = (abs(d[2]), yaw)
    img, _ = P.render(0, yaw=best[1], elev=4, centre=centre)
    cam = p3d.Camera(P.V['view'], yaw=best[1], elev=4, centre=centre)
    me = crop(img, cam, pel)
    main = Image.open(os.path.join(p3d.SHOTS, 'weave/cast/man/sheets/body_profile.jpg')).convert('RGB')
    strip([main, me], h=620, labels=['main sheet: body_profile.jpg', f'puppet f0, yaw {best[1]}, elev 4']).save(os.path.join(out, 'vs_main.png'))
    json.dump({str(k): v for k, v in notes.items()}, open(os.path.join(out, 'notes.json'), 'w'), indent=1, default=str)
    return out


if __name__ == '__main__':
    ap = argparse.ArgumentParser()
    ap.add_argument('act')
    ap.add_argument('--turn', type=int)
    ap.add_argument('--yaw', type=float, help='steer the camera: degrees around the vertical (vignette camera if omitted)')
    ap.add_argument('--elev', type=float, help='camera elevation, degrees')
    a = ap.parse_args()
    print(run(a.act, a.turn, a.yaw, a.elev))


def closeups(act, f, yaws=(0, 90, 180, 270)):
    """Feet and hands up close from several directions: do the boots roll, do the hands face true."""
    P = p3d.Puppet(act)
    out = os.path.join(HERE, 'out', act)
    a0 = list(P.V['frames'][f]['a'].values())[0]
    j = {k: np.array(a0['j'][i], float) for k, i in p3d.J.items()}
    centre = [j['pelvis'][0], 95, j['pelvis'][2]]
    base = P.V['view'].get('yaw', -22)
    rows = []
    for what, pts in (('feet', ['ankleL', 'ankleR', 'toeL', 'toeR', 'heelL', 'heelR']), ('hands', ['wristL', 'wristR'])):
        ims, labels = [], []
        for y in yaws:
            img, nt = P.render(f, yaw=base + y, centre=centre)
            cam = p3d.Camera(P.V['view'], yaw=base + y, centre=centre)
            Q = np.array([cam.P(j[k])[:2] for k in pts])
            pad = 28 * cam.s
            box = (int(Q[:, 0].min() - pad), int(Q[:, 1].min() - pad), int(Q[:, 0].max() + pad), int(Q[:, 1].max() + pad))
            ims.append(img.crop(box))
            h = nt[0]['hands']
            labels.append(f'{what} yaw {base + y:+.0f} near {nt[0]["near"]}' + (f'  L {h["L"]["shape"] or "relaxed"}/{h["L"]["palm"]}  R {h["R"]["shape"] or "relaxed"}/{h["R"]["palm"]}' if what == 'hands' else ''))
        rows.append(strip(ims, h=360, labels=labels))
    W = max(r.size[0] for r in rows)
    S = Image.new('RGB', (W, sum(r.size[1] for r in rows)), BG)
    y = 0
    for r in rows:
        S.paste(r, (0, y))
        y += r.size[1]
    S.save(os.path.join(out, f'closeups_f{f}.png'))
    return os.path.join(out, f'closeups_f{f}.png')
