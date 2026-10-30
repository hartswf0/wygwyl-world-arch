"""Drop at scale: every character placed in one sample set at two depths, and the whole cast in one line-up.

    python3 shots/suite/lib/castdrop.py --bank <dir with Bolas T###.json>

Sample set: the poem 07 plaza plate already in the repo (shots/weave/set/plate.jpg, 1920x1080). Its calibration,
in the lane-C set contract shape (shots/suite/data/sets/<scene>.json), is written to
shots/suite/data/sample_set_p07_plaza.json:
  horizon     y = 867 px: the canopy's vanishing point (shots/weave/set/set.json, canopy.vanish)
  ground      the plate's own person cut crowd_01 (ADE20K, shots/weave/set/set.json): 112 px tall, feet at y 1034;
              taken as 170 cm -> 0.659 px/cm at y 1034 -> 0.722 px/cm at the ground line y 1050;
              camera height = (1050 - 867) / 0.722 = 253 cm (an elevated wide shot)
  distance    assumed 60 deg horizontal field of view -> f = 1663 px -> the ground line is 23 m away
Each figure is rendered by the same cut-out solve as the arena takes (castrun.Puppet), at the px/cm the scale rule
(scale.py) gives for its foot line, then its height is MEASURED on the composited render and checked against the rule.
"""
import argparse, json, math, os, sys
import numpy as np
import cv2

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import castrun as R  # noqa: E402
import castkit as CK  # noqa: E402
import scale as SC  # noqa: E402

SUITE = R.SUITE
SHOTS = R.SHOTS
PLATE = os.path.join(SHOTS, 'weave', 'set', 'plate.jpg')
FOV = 60.0


def sample_set():
    horizon, ground = 867.0, 1050.0
    ppc_1034 = 112 / 170.0
    ppc_g = ppc_1034 * (ground - horizon) / (1034 - horizon)
    f_px = 960 / math.tan(math.radians(FOV / 2))
    return {
        'scene_id': 'sample.p07_plaza', 'poem': '07', 'plate_sources': ['shots/weave/set/plate.jpg'],
        'ground': {'y_px': ground, 'horizon_y_px': horizon},
        'scale': {'px_per_cm_at_ground_line': round(ppc_g, 5), 'figure_height_px': round(175 * ppc_g, 1),
                  'camera_distance_m': round(f_px / (ppc_g * 100), 2),
                  'how_measured': 'horizon = canopy vanishing point (weave/set/set.json); scale = plate person crowd_01, 112 px '
                                  'at foot y 1034, taken as 170 cm; distance from an assumed 60 deg HFOV'},
        'note': 'sample calibration for the cast page; lane C owns the real per-scene sets',
    }


def standing(cid, bankdir, yaw=None):
    """A neutral standing pose: Bolas T014 frame 0 retargeted to the character (EX: from behind)."""
    c = CK.BY_ID[cid]
    V = R.bank(bankdir, 'T014')
    rt = R.retarget(V, 0, c)
    if c.get('back_only'):
        yaw = 180 - 22
    return V, rt, yaw


def render_figure(cid, bankdir, ppc, f=0, view_override=None):
    """Render one character standing at ppc px/cm on a transparent canvas; returns (rgba float, foot point)."""
    V, rt, yaw = standing(cid, bankdir)
    cam = R.Cam(V['view'], yaw=yaw)
    cam.S = ppc
    pup = R.Puppet(cid, ppc)
    J3 = rt['J'][f]
    Hc = int(math.ceil(260 * ppc)) + 40
    Wc = int(math.ceil(160 * ppc)) + 40
    pel = J3[R.I['pelvis']]
    cam.c = [pel[0], 0.0, pel[2]]
    P2 = {}
    for n in R.N:
        p = cam.proj(J3[R.I[n]])
        P2[n] = np.array([p[0] - R.W / 2 + Wc / 2, p[1] - R.H * 0.5 + (Hc - 20), p[2]])
    ang, fx = cam.facing(rt['fwd'][f])
    view = view_override or R.pick_view(ang, pup.views, None, pup.c.get('back_only'))
    pup.pitch = {}
    for sd in 'LR':
        v3 = J3[R.I['toe' + sd]] - J3[R.I['ankle' + sd]]
        pup.pitch[sd] = math.atan2(-v3[1], math.hypot(v3[0], v3[2]))
    src = rt['src'][f]
    plant = {sd: ('ball' if src['ball' + sd][1] <= 1.0 else 'heel') for sd in 'LR' if rt['contact'][f][sd]}
    ops, pts = pup.solve(P2, view, fx < 0, plant, None)
    buf = np.zeros((Hc, Wc, 3), np.float32)
    ab = np.zeros((Hc, Wc), np.float32)
    cv = R.Canvas()
    c = pup.c
    for key, M, far, role in ops:
        cv.draw(buf, ab, key, M, far, c.get('tint'), c.get('alpha', 1.0))
    foot = np.array([P2['pelvis'][0], Hc - 20.0])
    crown = pts['head_top'][1] if c.get('code_head') else None
    stance_cm = float(J3[R.I['headTop']][1])      # how tall the motion itself stands in this frame
    return buf, ab, foot, view, crown, stance_cm


def composite(dst, buf, ab, at, foot):
    x0, y0 = int(round(at[0] - foot[0])), int(round(at[1] - foot[1]))
    h, w = ab.shape
    X0, Y0, X1, Y1 = max(0, x0), max(0, y0), min(dst.shape[1], x0 + w), min(dst.shape[0], y0 + h)
    if X1 <= X0 or Y1 <= Y0:
        return None
    a = ab[Y0 - y0:Y1 - y0, X0 - x0:X1 - x0, None]
    dst[Y0:Y1, X0:X1] = buf[Y0 - y0:Y1 - y0, X0 - x0:X1 - x0] + dst[Y0:Y1, X0:X1] * (1 - a)
    rows = np.where(a[:, :, 0].max(1) > 0.5)[0]
    return (Y0 + rows.min(), Y0 + rows.max()) if len(rows) else None


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--bank', required=True)
    a = ap.parse_args()
    st = sample_set()
    json.dump(st, open(os.path.join(SUITE, 'data', 'sample_set_p07_plaza.json'), 'w'), indent=1)
    plate = cv2.cvtColor(cv2.imread(PLATE), cv2.COLOR_BGR2RGB).astype(np.float32) / 255
    results = {}
    near_y, far_y = 1040.0, 935.0
    for c in CK.CAST:
        cid = c['id']
        img = plate.copy()
        rec = {}
        for tag, y, x in (('near', near_y, 760.0), ('far', far_y, 1060.0)):
            pl = SC.place({'height_cm': c['height_cm']}, st, x, y)
            buf, ab, foot, view, crown, stance = render_figure(cid, a.bank, pl['px_per_cm'])
            rows = composite(img, buf, ab, (x, y), foot)
            top = int(rows[0]) if rows else None
            if crown is not None and top is not None:
                top = max(top, int(round(crown + (y - foot[1]))))
            meas_h = (y - top) if top is not None else None
            chk = SC.check_placed({'height_cm': c['height_cm']}, st, y, meas_h) if meas_h else None
            rec[tag] = {'foot_y': y, 'x': x, 'px_per_cm': round(pl['px_per_cm'], 4), 'depth_m': round(pl['depth_m'], 1),
                        'want_height_px': round(chk['want_px'], 1) if chk else None, 'measured_height_px': int(meas_h) if meas_h else None,
                        'err_pct': round(float(chk['err_pct']), 2) if chk else None, 'ok': bool(chk['ok']) if chk else None, 'view': view,
                        'stance_cm': round(stance, 1),
                        'err_vs_stance_pct': round(100 * (meas_h / (stance * pl['px_per_cm']) - 1), 2) if meas_h else None,
                        'px_per_px': round(1 / pl['px_per_cm'], 2)}
            # rule marks: where the head must be
            u = (np.clip(img, 0, 1) * 255).astype(np.uint8)
            hx = int(x + 0.45 * c['height_cm'] * pl['px_per_cm'])
            cv2.line(u, (hx, int(y)), (hx, int(y - pl['height_px'])), (255, 220, 120), 2, cv2.LINE_AA)
            cv2.line(u, (hx - 5, int(y - pl['height_px'])), (hx + 5, int(y - pl['height_px'])), (255, 220, 120), 2)
            cv2.line(u, (hx - 5, int(y)), (hx + 5, int(y)), (255, 220, 120), 2)
            img = u.astype(np.float32) / 255
        u = (np.clip(img, 0, 1) * 255).astype(np.uint8)
        cv2.line(u, (0, int(st['ground']['horizon_y_px'])), (1920, int(st['ground']['horizon_y_px'])), (120, 200, 255), 1, cv2.LINE_AA)
        crop = u[540:1080, 480:1440]
        out = os.path.join(SUITE, 'cast', cid)
        os.makedirs(out, exist_ok=True)
        cv2.imwrite(os.path.join(out, 'drop.jpg'), cv2.cvtColor(crop, cv2.COLOR_RGB2BGR), [cv2.IMWRITE_JPEG_QUALITY, 80])
        results[cid] = rec
        print(cid, {k: (v['err_pct'], v['ok']) for k, v in rec.items()})
    # the line-up: everyone at one foot line and one px/cm, with a 0-200 cm ruler
    ppc = 1.6
    pad = 30
    figs = []
    for c in CK.CAST:
        buf, ab, foot, view, crown, stance = render_figure(c['id'], a.bank, ppc)
        figs.append((c, buf, ab, foot))
    Wl = sum(int(0.62 * c['height_cm'] * ppc) for c, *_ in figs) + 120
    Hl = int(215 * ppc) + 60
    line = np.zeros((Hl, Wl, 3), np.float32)
    line[:] = np.array([20, 24, 30]) / 255
    fy = Hl - 30
    x = 80
    u = (line * 255).astype(np.uint8)
    for cm in range(0, 201, 10):
        yy = int(fy - cm * ppc)
        cv2.line(u, (40, yy), (Wl, yy), (40, 46, 56) if cm % 50 else (70, 76, 90), 1)
        if cm % 50 == 0:
            cv2.putText(u, f'{cm}', (6, yy + 4), cv2.FONT_HERSHEY_PLAIN, 0.9, (220, 200, 160), 1, cv2.LINE_AA)
    line = u.astype(np.float32) / 255
    order = []
    for c, buf, ab, foot in figs:
        w = int(0.62 * c['height_cm'] * ppc)
        composite(line, buf, ab, (x + w / 2, fy), foot)
        order.append({'id': c['id'], 'x': round(float(x + w / 2), 1), 'height_cm': c['height_cm']})
        x += w
    u = (np.clip(line, 0, 1) * 255).astype(np.uint8)
    cv2.line(u, (0, fy), (Wl, fy), (150, 120, 80), 1)
    cv2.imwrite(os.path.join(SUITE, 'cast', 'lineup.jpg'), cv2.cvtColor(u, cv2.COLOR_RGB2BGR), [cv2.IMWRITE_JPEG_QUALITY, 82])
    json.dump({'set': st, 'near_y': near_y, 'far_y': far_y, 'characters': results, 'lineup': {'px_per_cm': ppc, 'foot_y': fy,
               'width': Wl, 'height': Hl, 'order': order}},
              open(os.path.join(SUITE, 'cast', 'drop.json'), 'w'), indent=1)


if __name__ == '__main__':
    main()
