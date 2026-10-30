#!/usr/bin/env python3
"""SETS, STEP 3: one stageable set per scene -> shots/suite/data/sets/<scene_id>.json, layers, scale check, archive slots.

Inputs (from steps 1-2, in <work_dir>): candidates.json, choice.json (+ overrides in shots/suite/tools/sets_overrides.json),
measure/<plate>/{m.json, a.npz} (Depth Pro depth, OneFormer ADE20K, SAM masks of people/doors/windows/..., ground plane).

Per plate (shared by the scenes that use it) -> shots/suite/sets/plates/<plate>/:
  plate.jpg            the plate at 1280x720, people the plate already had painted out (cv2 inpaint; logged)
  P6_sky.png P5_far.png P4_mid.png P3_ground.png P1_near.png P0_occluders.png
                       full-frame RGBA layers, 1280x720, each filled a band underneath the nearer layers (paint-behind) so
                       parallax does not open holes. Split: sky = ADE sky; the rest by measured depth against the ground-line
                       distance Zg: ground (ADE floor/road/grass/water... nearer than the mid split) -> P3; non-ground nearer
                       than Zg -> P1 (in front of the puppet), the P1 pieces touching the frame edge -> P0; Zg..Zf -> P4; >Zf -> P5.
  exploded.jpg         the planes pulled apart, for the page
Per scene -> shots/suite/sets/<scene_id>/scale_check.jpg: three 170 cm grey figures standing on the ground plane.

Scale: stage frame is 1920x1080 (character_rigs_library stage_calibration reference). The ground plane n.X + d = 0 is
RANSAC-fitted to the ADE ground pixels in Depth Pro's 3-D points; metric scale s is the median of known-size references in the
plate (person 1.70 m, door 2.05 m, car 1.45 m, chair 0.85 m, bench 0.45 m) measured on their SAM masks, else 1 (Depth Pro is
metric-ish). A 1.70 m figure at ground pixel (u, y) is its foot point on the plane plus 1.70/s along the normal, projected.
px_per_cm falls off linearly with the row's distance below the horizon (exact for a level pinhole camera):
px_per_cm(y) ~= k * (y - horizon_y); the table and k are written to the set.
   anaconda python3 sets_build.py <work_dir>"""
import os, sys, json, math, re, glob, collections, shutil
import numpy as np, cv2

SUITE = os.path.dirname(os.path.dirname(os.path.abspath(__file__))); SH = os.path.dirname(SUITE)
sys.path.insert(0, os.path.join(SUITE, 'lib'))
WORK = sys.argv[1]
ONLY = sys.argv[2].split(',') if len(sys.argv) > 2 else None
C = {s['scene_id']: s for s in json.load(open(os.path.join(WORK, 'candidates.json')))['scenes']}
CH = json.load(open(os.path.join(WORK, 'choice.json')))
OVR_P = os.path.join(SUITE, 'tools', 'sets_overrides.json')
OVR = json.load(open(OVR_P)) if os.path.exists(OVR_P) else {}
DATA = os.path.join(SUITE, 'data', 'sets'); SETS = os.path.join(SUITE, 'sets'); PL = os.path.join(SETS, 'plates')
for d in (DATA, SETS, PL): os.makedirs(d, exist_ok=True)
SW, SHH = 1920, 1080          # stage frame (JSON coordinates)
LW, LH = 1280, 720            # layer / plate image size
FIG_M = 1.70
CODE_SETS = {'black_void', 'black'}
PLANES = [('P6', 'sky'), ('P5', 'far'), ('P4', 'mid'), ('P3', 'ground'), ('P1', 'near'), ('P0', 'occluders')]
PARALLAX = {'P6': 0.08, 'P5': 0.22, 'P4': 0.48, 'P3': 0.78, 'P2': 1.0, 'P1': 1.38, 'P0': 1.85}   # play/level_assets_catalog seven_planes
STAGE_CAL = json.load(open(os.path.join(SH, 'arena/parts/kit3/release_v2/character_rigs_library.json')))['stage_calibration']

SURF = [('pane', r'^(window|windowpane|mirror|glass|showcase)'), ('door', r'^(door|double door|screen door|gate)'),
        ('screen', r'^(screen|crt screen|television|monitor|projection screen|signboard|bulletin board|poster|billboard|painting|picture)'),
        ('water', r'^(water|sea|river|lake|pool|swimming pool|fountain|waterfall)'), ('wall', r'^(wall|building|edifice|house|skyscraper|column|pillar|tower|fence)'),
        ('floor', r'^(floor|road|sidewalk|pavement|ground|earth|grass|field|sand|path|runway|stairway|stairs|steps|rug|carpet|dirt track|land)'),
        ('haze', r'^(sky|fog|cloud|smoke)')]
DET_SURF = {'door': 'door', 'window': 'pane', 'mirror': 'pane', 'television screen': 'screen', 'screen': 'screen'}

def surf_kind(label):
    l = label.split(', ')[0].strip()
    for k, rx in SURF:
        if re.match(rx, l): return k
    return None

# ── geometry ──
def ray(u, v, f, W, H): return np.array([(u - W / 2) / f, (v - H / 2) / f, 1.0])
def foot_on_plane(u, v, P, f, W, H):
    n = np.array(P['n']); r = ray(u, v, f, W, H); den = n @ r
    if den >= -1e-6: return None             # ray does not hit the ground in front (above horizon)
    return r * (-P['d'] / den)
def project(X, f, W, H): return np.array([f * X[0] / X[2] + W / 2, f * X[1] / X[2] + H / 2])
def fig_px(u, v, P, f, W, H, s):
    X = foot_on_plane(u, v, P, f, W, H)
    if X is None or X[2] <= 0: return None, None
    n = np.array(P['n']); up = n if n[1] < 0 else -n      # image y grows downward: 'up' has negative y
    Hd = X + up * (FIG_M / s)
    if Hd[2] <= 0.05: return None, None
    p0, p1 = project(X, f, W, H), project(Hd, f, W, H)
    return float(np.hypot(*(p0 - p1))), float(np.linalg.norm(X) * s)
def horizon_y(P, f, W, H, u=None):
    n = np.array(P['n']); u = W / 2 if u is None else u
    if abs(n[1]) < 1e-6: return None
    return float(H / 2 - f * (n[0] * (u - W / 2) / f + n[2]) / n[1])

# ── silhouette ──
def draw_figure(img, x, yfoot, hpx, label, col=(150, 150, 150)):
    h = hpx; w = h * 0.26
    pts = []
    head_r = h * 0.065; cy = yfoot - h + head_r
    body = np.array([[-0.5, 0.135], [0.5, 0.135], [0.46, 0.53], [0.24, 0.53], [0.22, 1.0], [0.04, 1.0], [0.0, 0.58], [-0.04, 1.0], [-0.22, 1.0], [-0.24, 0.53], [-0.46, 0.53]])
    poly = np.stack([x + body[:, 0] * w, yfoot - h + body[:, 1] * h], 1).astype(np.int32)
    ov = img.copy()
    cv2.fillPoly(ov, [poly], col); cv2.circle(ov, (int(x), int(cy)), max(2, int(head_r)), col, -1)
    cv2.addWeighted(ov, 0.82, img, 0.18, 0, img)
    cv2.polylines(img, [poly], True, (30, 30, 30), 1, cv2.LINE_AA); cv2.circle(img, (int(x), int(cy)), max(2, int(head_r)), (30, 30, 30), 1, cv2.LINE_AA)
    cv2.ellipse(img, (int(x), int(yfoot)), (int(w * 0.6), max(2, int(w * 0.09))), 0, 0, 360, (20, 20, 20), 1, cv2.LINE_AA)
    put(img, label, (int(x - w * 0.6), int(yfoot + 14)), 0.4)

def put(img, t, org, sc=0.45, col=(244, 239, 226)):
    cv2.putText(img, t, org, cv2.FONT_HERSHEY_SIMPLEX, sc, (15, 15, 15), 3, cv2.LINE_AA)
    cv2.putText(img, t, org, cv2.FONT_HERSHEY_SIMPLEX, sc, col, 1, cv2.LINE_AA)

def save_rgba(path, rgb, alpha):
    a = np.clip(alpha * 255, 0, 255).astype(np.uint8)
    rgb = rgb.copy(); rgb[a == 0] = 0                       # nothing under zero alpha: keeps the PNGs small
    cv2.imwrite(path, np.dstack([rgb[..., ::-1], a]), [cv2.IMWRITE_PNG_COMPRESSION, 9])

def inpaint_lowres(img, mask, scale=0.25, radius=5):
    """inpaint at low res for big holes, then take full-res where known."""
    if not mask.any(): return img.copy()
    h, w = mask.shape; sw, sh = max(8, int(w * scale)), max(8, int(h * scale))
    small = cv2.resize(img, (sw, sh), interpolation=cv2.INTER_AREA); m = cv2.resize(mask.astype(np.uint8), (sw, sh), interpolation=cv2.INTER_NEAREST)
    m = cv2.dilate(m, np.ones((3, 3), np.uint8))
    fill = cv2.inpaint(small, m * 255, radius, cv2.INPAINT_TELEA)
    up = cv2.resize(fill, (w, h), interpolation=cv2.INTER_CUBIC); up = cv2.GaussianBlur(up, (0, 0), 2.0)
    out = img.copy(); out[mask] = up[mask]; return out

# ══════════════════════════════════════════════════════════════════════════ per plate
PLATE_CACHE = {}
def build_plate(key, frame, m, A, kind):
    if key in PLATE_CACHE: return PLATE_CACHE[key]
    od = os.path.join(PL, key); os.makedirs(od, exist_ok=True)
    W, H = m['size']; f = m['focal_px']
    rgb0 = cv2.cvtColor(cv2.imread(frame), cv2.COLOR_BGR2RGB)
    if rgb0.shape[:2] != (H, W): rgb0 = cv2.resize(rgb0, (W, H))
    depth = A['depth'].astype(np.float32); seg = A['seg']; sky = A['sky'].astype(bool); ground = A['ground'].astype(bool)
    id2 = [str(x) for x in A['id2label']]; masks = A['masks'].astype(bool) if A['masks'].size else np.zeros((0, H, W), bool)
    P = m['plane']
    # ---- scale from known-size references
    s_list = []
    for r in m['refs']:
        if r['touches_edge'] or r['score'] < 0.38: continue
        s_list.append((r['label'], r['known_m'] / r['h_m_raw'], r))
    s_vals = np.array([x[1] for x in s_list]) if s_list else np.array([])
    if len(s_vals):
        med = float(np.median(s_vals)); keep = [x for x in s_list if 0.6 < x[1] / med < 1.66]
        s = float(np.median([x[1] for x in keep])) if keep else med
        spread = float(np.std(np.log([x[1] for x in keep]))) if len(keep) > 1 else None
    else:
        s, keep, spread = 1.0, [], None
    if keep and all(x[0] == 'street lamp' for x in keep) and len(keep) < 3:   # lamp heights vary: alone they need numbers
        s, keep, spread = 1.0, [], None
    s = float(np.clip(s, 0.2, 20.0))
    prior = None
    if not keep and P is not None:
        h_raw = P['d'] * s
        if kind == 'gen' or not (0.4 <= h_raw <= 8.0):
            prior = (f"Depth Pro puts the camera {h_raw:.2f} m above the ground, but its metric scale is not trustworthy on "
                     + ("our generated frames (where a plate has cars and people they measure 3-14x too small)" if kind == 'gen' else "this plate (outside 0.4-8 m)")
                     + " and no known-size object is in the plate, so an eye-level camera of 1.50 m is assumed; the horizon and the falloff are measured")
            s = 1.5 / P['d']
    # people in the plate: SAM masks of person detections
    ppl = np.zeros((H, W), bool); n_people = 0
    for d, mk in zip(m['dets'], masks):
        if d['label'] == 'person' and d['score'] >= 0.30 and mk.mean() < 0.5: ppl |= mk; n_people += 1
    ade_person = np.isin(seg, [i for i, l in enumerate(id2) if l.startswith('person')])
    ppl |= ade_person & (cv2.dilate(ppl.astype(np.uint8), np.ones((25, 25), np.uint8)) > 0)
    people_frac = float(ppl.mean())
    # ---- work at layer size
    rgb = cv2.resize(rgb0, (LW, LH), interpolation=cv2.INTER_AREA)
    rs = lambda a: cv2.resize(a.astype(np.uint8), (LW, LH), interpolation=cv2.INTER_NEAREST).astype(bool)
    Z = cv2.resize(depth * s, (LW, LH), interpolation=cv2.INTER_NEAREST); skyL, gL, pL = rs(sky), rs(ground), rs(ppl)
    pLd = cv2.dilate(pL.astype(np.uint8), np.ones((9, 9), np.uint8)).astype(bool)
    clean = cv2.inpaint(rgb, pLd.astype(np.uint8) * 255, 7, cv2.INPAINT_TELEA) if pLd.any() else rgb.copy()
    if pLd.mean() > 0.002:  # large painted areas: smoother low-res fill
        clean = inpaint_lowres(clean, pLd, 0.25, 6) if pLd.mean() > 0.03 else clean
    cv2.imwrite(os.path.join(od, 'plate.jpg'), clean[..., ::-1], [cv2.IMWRITE_JPEG_QUALITY, 90])
    # depth of painted-out people: take the surrounding depth so they don't become their own plane
    if pLd.any():
        ring = cv2.dilate(pLd.astype(np.uint8), np.ones((15, 15), np.uint8)).astype(bool) & ~pLd
        if ring.any(): Z = Z.copy(); Z[pLd] = float(np.median(Z[ring]))
    # ---- ground line & scale geometry (in native analysis pixels, then mapped to stage)
    sx, sy = SW / W, SHH / H
    scale = dict(method=None)
    ground_info = {}; rejected = None
    if P is not None:
        yh = horizon_y(P, f, W, H)
        n = np.array(P['n']); pitch = math.degrees(math.asin(np.clip(n[2], -1, 1))); roll = math.degrees(math.atan2(n[0], -n[1]))
        # ground line = the staging line: among rows with ground under the central band (below the horizon), the row where a
        # 170 cm figure comes out nearest the stage's calibrated hero height (standing adult 0.54 H); ties -> nearer the 0.86 H baseline
        water_ids = [i for i, l in enumerate(id2) if re.match(r'^(water|sea|river|lake|pool|swimming pool|fountain)', l)]
        walk = ground & ~np.isin(seg, water_ids)
        on_water = walk.mean() < 0.02
        stand = ground if on_water else walk
        cols = slice(int(W * 0.2), int(W * 0.8)); gcov = stand[:, cols].mean(1)
        rows = [y for y in range(int(H * 0.3), H - 2, max(1, H // 360)) if gcov[y] > 0.25 and (yh is None or y > yh + 0.03 * H)]
        if not rows: rows = [y for y in range(0, H - 2, max(1, H // 360)) if gcov[y] > 0.08 and (yh is None or y > yh + 0.02 * H)]
        hero = STAGE_CAL['posture_height_ratios']['standing_adult'] * H; base = STAGE_CAL['floor_baseline_y_ratio'] * H
        best_row = None
        for y in rows:
            gx = np.where(stand[y])[0]; u = float(gx[np.argmin(np.abs(gx - W / 2))]) if len(gx) else W / 2
            hp, dd = fig_px(u, y, P, f, W, H, s)
            if not hp: continue
            cost = abs(math.log(hp / hero)) + 0.15 * abs(y - base) / H
            if best_row is None or cost < best_row[0]: best_row = (cost, y, u, hp, dd)
        if best_row:
            _, yg, ug, fh, dist = best_row
        else:
            fh = dist = None
        if fh is not None and fh > 2:
            table = []
            for y in np.linspace((yh if yh is not None else 0) + 0.03 * H, H - 1, 9):
                if y <= 0: continue
                hp, dd = fig_px(W / 2, y, P, f, W, H, s)
                if hp: table.append([round(y * sy, 1), round(hp * sy / 170.0, 4), round(dd, 2)])
            # linear falloff fit through horizon
            k = None
            if yh is not None and len(table) >= 3:
                yy = np.array([t[0] for t in table]) - yh * sy; pp = np.array([t[1] for t in table]); k = float((yy @ pp) / (yy @ yy))
            ref_check = []
            for lab, sv, r in keep:
                hp, dd = fig_px(r['foot'][0], r['foot'][1], P, f, W, H, s)
                if hp: ref_check.append(dict(label=lab, known_cm=int(r['known_m'] * 100), measured_px=round((r['foot'][1] - r['top']) * sy, 1),
                                             predicted_px=round(hp * sy * r['known_m'] / FIG_M, 1), foot=[round(r['foot'][0] * sx), round(r['foot'][1] * sy)]))
            nref = len(keep); inl = P['inlier_frac']; hcam = P['d'] * s
            plaus = 0.15 <= hcam <= 60
            if nref >= 2 and (spread is None or spread < 0.25) and inl >= 0.45 and abs(roll) < 10 and plaus: conf, cnum = 'high', 0.85
            elif nref >= 1 and inl >= 0.35 and plaus: conf, cnum = 'medium', 0.65
            elif inl >= 0.45 and plaus: conf, cnum = 'medium', 0.55
            elif plaus: conf, cnum = 'low', 0.35
            else: conf, cnum = 'low', 0.2
            # plausibility against the picture itself
            flags = []
            skyc = sky[:, int(W * 0.1):int(W * 0.9)]
            if skyc.mean() > 0.03 and yh is not None:
                lows = [np.where(c)[0].max() for c in skyc.T if c.any()]
                sky_bottom = float(np.percentile(lows, 50)) if lows else None
                if sky_bottom is not None and yh < sky_bottom - 0.12 * H:
                    flags.append(f'horizon y={yh * sy:.0f} sits {(sky_bottom - yh) * sy:.0f} px above where the sky meets the land (y={sky_bottom * sy:.0f})')
            if abs(roll) > 8: flags.append(f'ground plane rolls {roll:.0f} deg')
            if prior: flags.append('camera height assumed (1.50 m, eye level): no known-size object; Depth Pro scale distrusted')
            elif not keep and not (0.4 <= hcam <= 8.0): flags.append(f'camera height {hcam:.2f} m is outside eye-level staging (0.4-8 m) and no known-size object confirms it')
            if fh > 0.82 * H: flags.append('even the farthest ground row makes a standing figure nearly fill the frame (macro / very low camera)')
            if fh < 0.06 * H: flags.append('even the nearest ground row makes a standing figure tiny (aerial / very far camera)')
            if stand.mean() < 0.04: flags.append(f'little floor to fit on ({stand.mean():.1%} of frame): the horizon may be off')
            if on_water: flags.append('the only ground in the plate is water: figures stand on it (wade / float) or on a cut-out quay')
            if flags:
                conf, cnum = ('low', min(cnum, 0.3)) if len(flags) > 1 or conf != 'high' else ('medium', 0.5)
            how = (f"ground plane RANSAC on Depth Pro points of the ADE ground ({inl:.0%} inliers) -> horizon y={yh * sy:.0f}, camera height {hcam:.2f} m, "
                   f"pitch {pitch:.1f} deg, roll {roll:.1f} deg; metric scale x{s:.2f} from " +
                   (', '.join(f"{lab} ({int(r['known_m'] * 100)} cm)" for lab, _, r in keep) if keep else (prior if prior else 'no known-size object (Depth Pro metric depth taken as is)')) +
                   f"; a 170 cm figure at the ground line y={yg * sy:.0f} is {fh * sy:.0f} px")
            unreliable = (not keep) and sum(1 for x in flags if x.startswith(('horizon y=', 'ground plane rolls', 'even the'))) >= 2
            scale = {} if unreliable else dict(px_per_cm_at_ground_line=round(fh * sy / 170.0, 4), figure_height_px=round(fh * sy, 1), camera_distance_m=round(dist, 2),
                         camera_height_m=round(hcam, 2), pitch_deg=round(pitch, 1), roll_deg=round(roll, 1), focal_px_stage=round(f * sx, 1),
                         metric_scale=round(s, 3), refs=ref_check, ref_spread_log=None if spread is None else round(spread, 3),
                         flags=flags, falloff=dict(model='px_per_cm = k * (y - horizon_y)  [stage px, level-camera pinhole]', k=None if k is None else round(k, 6),
                                      table_y_pxpercm_distm=table),
                         how_measured=how, confidence=conf, confidence_num=cnum, method='ground_plane' + ('+refs' if keep else ''))
            ground_info = dict(y_px=round(yg * sy, 1), horizon_y_px=None if yh is None else round(yh * sy, 1), x_px=round(ug * sx, 1), stands_on_water=bool(on_water))
            if unreliable: ground_info, rejected = {}, dict(flags=flags, how=how)

    if not scale.get('px_per_cm_at_ground_line'):
        rej = rejected
        yg_s = STAGE_CAL['floor_baseline_y_ratio'] * SHH; fh_s = STAGE_CAL['posture_height_ratios']['standing_adult'] * SHH
        conf = 'assumed'
        scale = dict(px_per_cm_at_ground_line=round(fh_s / 170, 4), figure_height_px=round(fh_s, 1), camera_distance_m=None, camera_height_m=None,
                     metric_scale=round(s, 3), refs=[], falloff=dict(model='none (no ground plane found)', k=None, table_y_pxpercm_distm=[]),
                     how_measured=(('the fitted ground plane disagrees with the picture (' + '; '.join(rej['flags']) + '), so it is not used'
                                    if rej else 'no ground plane could be fitted (' + ('ground is %.0f%% of frame' % (100 * m['ground_frac'])) + ')') +
                                   '; stage calibration used: floor baseline 0.86 H, standing adult 0.54 H (character_rigs_library stage_calibration)'),
                     flags=rej['flags'] if rej else [], rejected_plane=rej['how'] if rej else None,
                     confidence=conf, confidence_num=0.1, method='stage_calibration')
        ground_info = dict(y_px=round(yg_s, 1), horizon_y_px=None, x_px=SW / 2)
    # ---- planes at layer size
    Zg = scale.get('camera_distance_m') or float(np.percentile(Z[~skyL], 30) if (~skyL).any() else 5.0)
    nons = ~skyL
    far_z = Z[nons & (Z > Zg)]
    Zf = float(max(2.5 * Zg, np.percentile(far_z, 50))) if far_z.size > 200 else 3 * Zg
    near = nons & ~gL & (Z < Zg * 0.92)
    lab = np.full((LH, LW), 4, np.uint8)                     # P4 mid by default
    lab[skyL] = 6
    lab[nons & (Z >= Zf)] = 5
    lab[gL & (Z < Zf)] = 3
    lab[near] = 1
    # occluders: near components touching left/right/top edges
    ncomp, cc, st, _ = cv2.connectedComponentsWithStats(near.astype(np.uint8), 8)
    for i in range(1, ncomp):
        x, y, w, h, a = st[i]
        if a < 0.002 * LW * LH: lab[cc == i] = 3 if gL[cc == i].mean() > 0.3 else 4; continue      # specks: back
        if x <= 1 or x + w >= LW - 1 or y <= 1: lab[cc == i] = 0
    # clean tiny islands in every plane (median filter on labels)
    lab = cv2.medianBlur(lab, 5)
    order = [6, 5, 4, 3, 1, 0]
    layers = []
    for pi, (pid, name) in zip(order, PLANES):
        mk = lab == pi
        frac = float(mk.mean())
        if frac < 0.0015 and pid not in ('P6',): continue
        nearer = np.isin(lab, [o for o in order if o < pi])
        if pid == 'P6':
            if frac < 0.0015: continue
            fill = inpaint_lowres(clean, ~mk, 0.125, 9); alpha = np.ones((LH, LW), np.float32)
            # sky is a full backing card when it exists
        else:
            band = cv2.dilate(mk.astype(np.uint8), np.ones((41, 41), np.uint8)).astype(bool) & nearer
            fill = inpaint_lowres(clean, band, 0.25, 6) if band.any() else clean
            dist_in = cv2.distanceTransform((~mk).astype(np.uint8), cv2.DIST_L2, 3)
            alpha = mk.astype(np.float32)
            alpha = np.maximum(alpha, (band & (dist_in < 20)).astype(np.float32) * np.clip(1 - dist_in / 20, 0, 1))
            alpha = cv2.GaussianBlur(alpha, (0, 0), 0.8); alpha[mk] = 1.0
        fn = f'{pid}_{name}.png'; save_rgba(os.path.join(od, fn), fill, alpha)
        zmed = float(np.median(Z[mk])) if mk.any() and pid != 'P6' else None
        layers.append(dict(id=f'{key}.{pid}', plane=pid, name=name, kind='image', file=f'sets/plates/{key}/{fn}', area_frac=round(frac, 4),
                           depth_m=None if pid == 'P6' else (round(zmed, 2) if zmed else None), parallax=PARALLAX[pid],
                           z=dict(P6=6.0, P5=3.8, P4=2.4, P3=1.4, P1=0.55, P0=0.25)[pid]))
    # exploded preview: every plane on its own, over a checkerboard, far to near
    tw, th = 400, 225; cols_ = 3; rows_ = (len(layers) + cols_ - 1) // cols_
    ex = np.full((rows_ * (th + 26), cols_ * (tw + 8), 3), 22, np.uint8)
    yy, xx = np.mgrid[0:th, 0:tw]; chk = (((yy // 12) + (xx // 12)) % 2)[..., None] * 28 + 40
    for i, L in enumerate(layers):
        im = cv2.imread(os.path.join(SUITE, L['file']), cv2.IMREAD_UNCHANGED); im = cv2.resize(im, (tw, th), interpolation=cv2.INTER_AREA)
        a_ = im[..., 3:4] / 255.0; tile = (chk * (1 - a_) + im[..., :3] * a_).astype(np.uint8)
        r_, c_ = divmod(i, cols_); ox, oy = c_ * (tw + 8), r_ * (th + 26)
        ex[oy + 22:oy + 22 + th, ox:ox + tw] = tile
        put(ex, f"{L['plane']} {L['name']}  {L['area_frac'] * 100:.0f}%" + (f"  ~{L['depth_m']} m" if L.get('depth_m') else ''), (ox + 4, oy + 16), 0.45)
    cv2.imwrite(os.path.join(od, 'exploded.jpg'), ex, [cv2.IMWRITE_JPEG_QUALITY, 82])
    # ---- surfaces (stage coords)
    surfaces = []; occl = []
    def poly_of(mask_native, min_frac=0.004, maxn=2, kind=None, label=None, src='ade'):
        out = []
        mk = cv2.resize(mask_native.astype(np.uint8), (LW, LH), interpolation=cv2.INTER_NEAREST)
        nc, cc2, st2, _ = cv2.connectedComponentsWithStats(mk, 8)
        idx = sorted(range(1, nc), key=lambda i: -st2[i][4])[:maxn]
        for i in idx:
            if st2[i][4] < min_frac * LW * LH: continue
            cs, _ = cv2.findContours((cc2 == i).astype(np.uint8), cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
            c = max(cs, key=cv2.contourArea); c = cv2.approxPolyDP(c, 0.006 * cv2.arcLength(c, True), True)
            pts = [[round(float(p[0][0]) * SW / LW, 1), round(float(p[0][1]) * SHH / LH, 1)] for p in c]
            if len(pts) < 3: continue
            comp = cc2 == i; zz = float(np.median(Z[comp])) if not skyL[comp].all() else None
            x, y, w, h, a = st2[i]
            out.append(dict(kind=kind, label=label, src=src, polygon=pts, area_frac=round(a / (LW * LH), 4), depth_m=None if zz is None else round(zz, 2),
                            bbox=[round(x * SW / LW), round(y * SHH / LH), round(w * SW / LW), round(h * SHH / LH)],
                            plane=('P%d' % int(np.bincount(lab[comp].ravel(), minlength=7).argmax()))))
        return out
    used = collections.Counter()
    for d, mk in zip(m['dets'], masks):
        k = DET_SURF.get(d['label'])
        if k and d['score'] >= 0.35 and used[k] < 3:
            for p in poly_of(mk, 0.003, 1, k, d['label'], 'grounding-dino+sam2'): surfaces.append(p); used[k] += 1
    for i in np.unique(seg):
        l = id2[int(i)]; k = surf_kind(l)
        if not k or used[k] >= 3: continue
        for p in poly_of(seg == i, 0.006 if k not in ('pane', 'door', 'screen') else 0.003, 2, k, l.split(',')[0], 'oneformer-ade20k'):
            surfaces.append(p); used[k] += 1
    surfaces.sort(key=lambda x: (['pane', 'door', 'screen', 'water', 'wall', 'haze', 'floor'].index(x['kind']), -x['area_frac']))
    for i, sfc in enumerate(surfaces): sfc['id'] = f"{sfc['kind']}_{i}"
    ncomp, cc, st, _ = cv2.connectedComponentsWithStats((lab <= 1).astype(np.uint8), 8)
    for i in sorted(range(1, ncomp), key=lambda i: -st[i][4])[:4]:
        if st[i][4] < 0.004 * LW * LH: continue
        x, y, w, h, a = st[i]
        cs, _ = cv2.findContours((cc == i).astype(np.uint8), cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        c = cv2.approxPolyDP(max(cs, key=cv2.contourArea), 3, True)
        occl.append(dict(id=f'occ_{len(occl)}', plane='P%d' % int(np.bincount(lab[cc == i].ravel(), minlength=7).argmax()),
                         polygon=[[round(float(p[0][0]) * SW / LW, 1), round(float(p[0][1]) * SHH / LH, 1)] for p in c],
                         bbox=[round(x * SW / LW), round(y * SHH / LH), round(w * SW / LW), round(h * SHH / LH)], area_frac=round(a / (LW * LH), 4),
                         depth_m=round(float(np.median(Z[cc == i])), 2)))
    R = dict(key=key, layers=layers, scale=scale, ground=ground_info, surfaces=surfaces, occluders=occl, people=dict(n=n_people, frac=round(people_frac, 4)),
             P=P, f=f, W=W, H=H, s=s, ground_mask=stand if P is not None else ground, Zg=Zg, Zf=Zf)
    PLATE_CACHE[key] = R
    return R

def scale_check(scene_dir, R, title):
    img = cv2.imread(os.path.join(PL, R['key'], 'plate.jpg')); img = cv2.resize(img, (LW, LH))
    k = LW / SW; sc = R['scale']; g = R['ground']
    if g.get('horizon_y_px') is not None:
        yh = int(g['horizon_y_px'] * k); cv2.line(img, (0, yh), (LW, yh), (60, 200, 255), 1, cv2.LINE_AA); put(img, 'horizon', (8, yh - 6), 0.42, (120, 220, 255))
    yg = int(g['y_px'] * k); cv2.line(img, (0, yg), (LW, yg), (90, 90, 230), 1, cv2.LINE_AA); put(img, 'ground line', (8, yg - 6), 0.42, (160, 160, 255))
    placed = []
    if R['P'] is not None and sc.get('method', '').startswith('ground_plane'):
        P, f, W, H, s = R['P'], R['f'], R['W'], R['H'], R['s']
        yg_n = g['y_px'] * H / SHH; fh0, _ = fig_px(g['x_px'] * W / SW, yg_n, P, f, W, H, s)
        yh_n = horizon_y(P, f, W, H)
        for frac, xt in ((1.0, 0.3), (0.6, 0.56), (0.35, 0.8)):
            y = yh_n + (yg_n - yh_n) * frac if yh_n is not None else yg_n * frac
            gr = R['ground_mask']; yi = int(np.clip(y, 0, H - 1)); gx = np.where(gr[yi])[0]
            while len(gx) < 3 and yi < yg_n:                  # no floor on that row (a wall, a window): come nearer until there is
                yi += max(1, H // 200); gx = np.where(gr[min(yi, H - 1)])[0]
            if len(gx) < 3: continue
            if placed and yi >= placed[-1]['_yi'] - 2: continue  # it collapsed onto a nearer figure's row
            y = float(yi); u = float(gx[np.argmin(np.abs(gx - xt * W))])
            hp, dd = fig_px(u, y, P, f, W, H, s)
            if not hp: continue
            draw_figure(img, u * LW / W, y * LH / H, hp * LH / H, f'170cm @ {dd:.1f} m = {hp * SHH / H:.0f}px')
            placed.append(dict(x_px=round(u * SW / W, 1), y_px=round(y * SHH / H, 1), figure_px=round(hp * SHH / H, 1), distance_m=round(dd, 2), _yi=yi))
        for p_ in placed: p_.pop('_yi', None)
        for r in sc.get('refs', []):
            x, y = int(r['foot'][0] * k), int(r['foot'][1] * k)
            cv2.line(img, (x, y), (x, int(y - r['measured_px'] * k)), (40, 220, 120), 2)
            cv2.line(img, (x + 4, y), (x + 4, int(y - r['predicted_px'] * k)), (255, 255, 255), 1)
            put(img, f"{r['label']} {r['known_cm']}cm", (x + 8, int(y - r['measured_px'] * k) + 4), 0.38, (150, 255, 180))
    else:
        for xt in (0.3, 0.56, 0.8):
            draw_figure(img, xt * LW, yg, sc['figure_height_px'] * k, f"170cm (stage calibration) {sc['figure_height_px']:.0f}px")
            placed.append(dict(x_px=round(xt * SW), y_px=g['y_px'], figure_px=sc['figure_height_px'], distance_m=None))
    bar = np.full((26, LW, 3), 24, np.uint8)
    put(bar, f"{title}  |  {sc['px_per_cm_at_ground_line']:.2f} px/cm @ ground line (stage 1920x1080)  |  confidence: {sc['confidence']}", (8, 18), 0.45)
    out = np.vstack([img, bar]); os.makedirs(scene_dir, exist_ok=True)
    cv2.imwrite(os.path.join(scene_dir, 'scale_check.jpg'), out, [cv2.IMWRITE_JPEG_QUALITY, 84])
    return placed

# ══════════════════════════════════════════════════════════════════════════ archive slots
G = None
def grab():
    global G
    if G is None:
        from archive_grab import Grab
        G = Grab()
    return G

KIND_Q = {'pane': 'seen through a window: {}', 'door': 'through a doorway: {}', 'screen': 'film on a screen: {}', 'water': 'water, reflections, waves: {}',
          'wall': 'projected on a wall: {}', 'haze': 'sky, clouds, smoke: {}', 'floor': 'shadows on the ground: {}'}

def slots_for(scene, surfaces, design):
    g = grab(); qs = [q for q in scene['archive_queries'] if q]
    lines = re.sub(r'\s*/\s*', ' ', scene.get('lines') or '')[:160]
    if qs:   # the dossier's archive queries are per poem: rank them by how close each is to this scene's lines and set
        st = g.text([f"{lines} {scene['set_what'][:120]}"])[0]; qe = g.text(qs)
        qs = [qs[i] for i in np.argsort(-(qe @ st))]
    dsurf = (design or {}).get('surfaces') or []
    slots = []; seen = set(); qi = 0
    pick = [s for s in surfaces if s['kind'] in ('pane', 'door', 'screen')][:3] + [s for s in surfaces if s['kind'] in ('water', 'wall', 'haze')][:2] + \
           [s for s in surfaces if s['kind'] == 'floor'][:1]
    for sfc in pick[:5]:
        if sfc['kind'] in ('pane', 'door', 'screen', 'wall') and qs:
            q = qs[qi % len(qs)]; qi += 1; query = [q, lines] if lines else [q]
            qtxt = q
        else:
            subject = {'water': 'water and light', 'haze': 'clouds and sky', 'floor': 'shadows and light on a floor', 'wall': 'a wall', 'pane': 'a window', 'door': 'a doorway', 'screen': 'a screen'}[sfc['kind']]
            qtxt = f"{subject}, {scene['set_what'][:80]}"; query = [qtxt]
        cands = g.clips(query, k=5, exclude=seen)
        for c in cands: seen.add(c['clip'])
        slots.append(dict(surface=sfc['id'], kind=sfc['kind'], join='screen' if sfc['kind'] in ('pane', 'door', 'screen', 'wall', 'water') else 'wipe',
                          query=qtxt, candidates=[slim(c) for c in cands]))
    # a citizen slot: archive figures to cut in (WEAVE join 3)
    who = f"a person standing or walking in {scene['set_what'][:70]}"
    objs = g.objects(who, k=4, kinds=('figure', 'person', 'reading'), people=True)
    od = os.path.join(SETS, 'archive_objects'); out = []
    for o in objs:
        fn = re.sub(r'[^\w.-]', '_', o['id']) + '.png'; fp = os.path.join(od, fn)
        if not os.path.exists(fp): g.cutout(o, fp)
        out.append(dict(id=o['id'], clip=o['clip'], label=o['label'], desc=o['desc'], score=o['score'], lab_png=o['png'], local=f'sets/archive_objects/{fn}',
                        t=o.get('t'), tag=o['provenance']['tag'], title=o['provenance']['title'], year=o['provenance']['year'], video_url=o['provenance']['video_url']))
    slots.append(dict(surface=None, kind='citizen', join='citizen', query=who, objects=out,
                      candidates=[slim(g.clip_record(o['clip'], o['score'])) for o in objs]))
    return slots, dsurf

def slim(c): return {k: c[k] for k in ('clip', 'title', 'year', 'score', 't0', 't1', 'thumb_url', 'video_url', 'tag')}

# ══════════════════════════════════════════════════════════════════════════ main
def status_of(scene, best, R, code):
    if code: return 'good', 'code set (black card): no plate needed'
    why = []
    clip = best['clip']; ppl = best['people']['area']; conf = R['scale']['confidence']
    dstat = (scene['design'] or {}).get('status')
    if clip < 0.215 or (dstat == 'need' and clip < 0.25): return 'needs a plate', f'best plate is a weak match to the set (CLIP {clip:.3f}); dossier status: {dstat}'
    if ppl > 0.12: return 'needs a plate', f'the best plate has large figures ({ppl:.0%} of frame) that fight the puppet'
    if clip >= 0.255 and ppl < 0.015: return 'good', f'the plate matches the set (CLIP {clip:.3f}) and has no figures ({ppl:.1%}); scale {conf}'
    return 'usable', f'CLIP {clip:.3f}, figures {ppl:.1%} (painted out), scale {conf}'

def main():
    index = []
    for sid, sc in C.items():
        if ONLY and sid not in ONLY: continue
        o = OVR.get(sid, {})
        ch = CH[sid]; best = ch['best']
        if o.get('cand'):
            alt = next(a for a in ch['alternatives'] if a['cand'] == o['cand'])
            cand = next(c for c in sc['candidates'] if c['id'] == alt['cand'])
            best = dict(best, cand=cand['id'], kind=cand['kind'], frame=alt['frame'], clip=alt['clip'], people=dict(n=alt['people'], area=alt['people_area']),
                        origin=cand['origin'], out_id=cand.get('out_id'), provenance=cand['provenance'])
        code = (sc['set'] in CODE_SETS) or o.get('code')
        key = best['cand'] if best['kind'] == 'world' else os.path.splitext(os.path.basename(best['frame']))[0]
        mdir = os.path.join(WORK, 'measure', key)
        if best['kind'] == 'view': key = 'view_' + key
        scene_dir = os.path.join(SETS, sid)
        rec = dict(scene_id=sid, poem=sc['poem'], title=sc['title'], movement=sc['movement'], seconds=sc['seconds'], lines=sc['lines'],
                   set=sc['set'], set_what=sc['set_what'], sets_used=sc['sets_used'], camera=sc['camera'], framing=sc['framing'],
                   stage=dict(w=SW, h=SHH, layer_px=[LW, LH], note='all x/y in stage px (1920x1080); layer PNGs are full-frame at 1280x720'))
        if code:
            yg = STAGE_CAL['floor_baseline_y_ratio'] * SHH; fh = STAGE_CAL['posture_height_ratios']['standing_adult'] * SHH
            rec.update(plate_sources=[dict(kind='code', what='black card, no plate')],
                       layers=[dict(id=f'{sid}.P6', plane='P6', kind='code', draw=dict(fill='#050505'), depth_m=None, parallax=PARALLAX['P6'], z=6.0),
                               dict(id=f'{sid}.P5', plane='P5', kind='code', draw=dict(stars='pin-pricked black card, sparse', seed=int(sid.replace('.', ''))), depth_m=None, parallax=PARALLAX['P5'], z=3.8)],
                       ground=dict(y_px=round(yg, 1), horizon_y_px=None, floor='none (figures float in black)'),
                       scale=dict(px_per_cm_at_ground_line=round(fh / 170, 4), figure_height_px=round(fh, 1), camera_distance_m=None,
                                  how_measured='code set: no plate; stage calibration (standing adult 0.54 H at floor baseline 0.86 H)', confidence='assumed', confidence_num=0.5,
                                  method='stage_calibration'),
                       surfaces=[dict(id='haze_0', kind='haze', polygon=[[0, 0], [SW, 0], [SW, SHH], [0, SHH]], label='the black itself', src='code')],
                       occluders=[], status='good', status_why='code set (black card): no plate needed')
            g = grab(); qs = sc['archive_queries'] or ['light flashing in darkness']
            cands = g.clips([qs[0], re.sub(r'\s*/\s*', ' ', sc['lines'] or '')[:160]], k=5)
            rec['archive_slots'] = [dict(surface='haze_0', kind='haze', join='wipe', query=qs[0], candidates=[slim(c) for c in cands])]
            os.makedirs(scene_dir, exist_ok=True)
            img = np.full((LH + 26, LW, 3), 6, np.uint8)
            for xt in (0.3, 0.56, 0.8): draw_figure(img, xt * LW, yg * LH / SHH, fh * LH / SHH, '170cm (stage calibration)')
            put(img, f"{sid}  black card  |  {fh / 170:.2f} px/cm (assumed)", (8, LH + 18), 0.45)
            cv2.imwrite(os.path.join(scene_dir, 'scale_check.jpg'), img, [cv2.IMWRITE_JPEG_QUALITY, 84])
            rec['scale_check'] = f'sets/{sid}/scale_check.jpg'
            # alternatives: still list plates in case a lit void is wanted
            rec['plate_alternatives'] = [dict(cand=a['cand'], clip=a['clip'], people=a['people'], origin=a['origin']) for a in ch['alternatives'][:4]]
        else:
            m = json.load(open(os.path.join(mdir, 'm.json'))); A = np.load(os.path.join(mdir, 'a.npz'))
            R = build_plate(key, best['frame'], m, A, best['kind'])
            placed = scale_check(scene_dir, R, f"{sid} {sc['set']}")
            st, why = status_of(sc, best, R, False)
            if o.get('status'): st, why = o['status'], o.get('why', why)
            slots, dsurf = slots_for(sc, R['surfaces'], sc['design'])
            prov = dict(best['provenance']); prov.update(cand=best['cand'], frame=os.path.basename(best['frame']), chosen_by=best['origin'],
                                                         clip_vs_set=round(best['clip'], 4), people_in_plate=best['people']['n'],
                                                         people_area=best['people']['area'], painted_out=R['people'])
            if o.get('why_cand'): prov['override'] = o['why_cand']
            rec.update(plate_sources=[prov], plate=f'sets/plates/{key}/plate.jpg', exploded=f'sets/plates/{key}/exploded.jpg',
                       layers=R['layers'] + [dict(id=f'{sid}.P2', plane='P2', kind='code', draw=dict(slot='puppets'), depth_m=R['scale'].get('camera_distance_m'),
                                                  parallax=PARALLAX['P2'], z=1.0)],
                       ground=R['ground'], scale=R['scale'], scale_check=f'sets/{sid}/scale_check.jpg', scale_check_figures=placed,
                       surfaces=R['surfaces'], design_surfaces=dsurf, design_layers=(sc['design'] or {}).get('layers'),
                       occluders=R['occluders'], archive_slots=slots, status=st, status_why=why,
                       plate_alternatives=[dict(cand=a['cand'], clip=a['clip'], people=a['people'], people_area=a['people_area'], origin=a['origin'])
                                           for a in ch['alternatives'][:5]],
                       split=dict(ground_line_distance_m=round(R['Zg'], 2), far_split_m=round(R['Zf'], 2)))
        # the passage answer, if this scene holds the poem's fulcrum line
        pa = sc.get('passage') or {}
        if pa.get('line') and pa['line'].split()[0].lower() in (sc['lines'] or '').lower() and \
                re.sub(r'\W', '', pa['line'].lower())[:18] in re.sub(r'\W', '', (sc['lines'] or '').lower()):
            ans = pa.get('answer') or {}
            rec['passage_answer'] = dict(line_id=pa.get('line_id'), line=pa.get('line'), clip=ans.get('clip'), title=ans.get('title'), year=ans.get('year'),
                                         said=ans.get('said'), t_in=ans.get('in'), t_out=ans.get('out'), join='answer')
        json.dump(rec, open(os.path.join(DATA, f'{sid}.json'), 'w'), indent=1, default=float)
        index.append(dict(scene_id=sid, poem=sc['poem'], title=sc['title'], movement=sc['movement'], set=sc['set'], status=rec['status'],
                          status_why=rec['status_why'], plate=rec.get('plate'), exploded=rec.get('exploded'), scale_check=rec['scale_check'],
                          px_per_cm=rec['scale']['px_per_cm_at_ground_line'], figure_px=rec['scale']['figure_height_px'],
                          confidence=rec['scale']['confidence'], method=rec['scale']['method'], camera=sc['camera'], framing=sc['framing'],
                          n_layers=len(rec['layers']), surfaces=collections.Counter(s['kind'] for s in rec['surfaces']),
                          slots=len(rec['archive_slots']), source=rec['plate_sources'][0].get('cand', 'code')))
        print(sid, rec['status'], rec['scale']['confidence'], rec['scale']['px_per_cm_at_ground_line'], rec['plate_sources'][0].get('cand', 'code'), flush=True)
    if not ONLY:
        json.dump(dict(stage=[SW, SHH], scenes=index), open(os.path.join(DATA, 'index.json'), 'w'), indent=1)

if __name__ == '__main__':
    main()
