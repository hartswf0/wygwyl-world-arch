#!/usr/bin/env python3
"""
Multiplane decomposition: turns each analysed shot (shots/out/<id>/) into a classical multiplane stack.

Measured layer (from analyze.py arrays)  +  Director layer (shots/director_notes.json)
  -> P0 camera mask · P1 foreground · P2 character action · P3 secondary/FX · P4 midground · P5 distant · P6 sky
  -> per-plane RGBA sheets with paint-behind strips, line drawings, glow pass, haze per plane
  -> parallax factors (screen_motion ∝ 1/depth), camera move, overscan, x-sheet
  -> previews: exploded stack, layout drawing (blue-pencil/red-key), silhouette test, parallax playback (on twos)

Assignment logic (role first, depth second):
  P6  = sky/stars/moon (ADE sky ∪ sky-ish detections behind the scene)
  P2  = the HERO: characters matching the director's/prompt's subject, grouped by depth;
        if no characters exist, the most animatable element (cloth > light/FX > water) becomes the performer
  P3  = other characters + FX/cloth elements, each kept as its own sheet at its own depth
  rest is environment, split into near / mid / far:
        - hero-relative when a hero exists (near < 0.85·Z_hero), else 1-D k-means on log depth
        - rigid units (ADE regions / detected objects with small depth spread) stay whole
        - receding surfaces (floors, walls, ceilings with large spread) are sliced into strips by band
  near band: framing pieces touching left/right/top edge and not ground  -> P0 camera mask
             the rest (near floor strips, near props)                    -> P1
  mid -> P4, far -> P5

Usage: .venv-shots/bin/python shots/multiplane.py [--match substr ...]
"""
import argparse, glob, json, math, os, re
import numpy as np
import cv2
from PIL import Image, ImageDraw, ImageFont

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, "shots", "out")
PLANES = {0: "camera mask", 1: "foreground", 2: "character action", 3: "secondary / FX",
          4: "midground", 5: "distant background", 6: "sky / atmosphere"}
PCOL = {0: (40, 40, 48), 1: (120, 86, 60), 2: (214, 48, 49), 3: (242, 165, 65),
        4: (47, 111, 219), 5: (120, 170, 235), 6: (150, 215, 235)}

CHAR_RE = re.compile(r"\b(person|people|child|children|kid|kids|crowd|figure|silhouette|man|woman|girl|boy|"
                     r"dancer|walker|runner|animal|dog|cat|bird|fish|mirrorfish|horse)\b")
CLOTH_RE = re.compile(r"(fabric|laundry|sarong|cloth|textile|flag|curtain|banner|awning|sheet)")
FX_RE = re.compile(r"(light|lamp|lantern|beacon|led|glow|fire|flame|neon|reflection|smoke|steam|vapor|haze|fog|"
                   r"mist|spark|glyph|sign|screen|lattice tower)")
SKY_RE = re.compile(r"\b(sky|cloud|moon|stars?|constellation|aurora|galaxy)\b")
WATER_RE = re.compile(r"(water|pool|lake|lagoon|canal|sea|river|reflection)")

# what each kind of thing does in a cycle (classical defaults; frames @24fps)
MOTION = [
    (r"child|kid", "moving hold + toe-drag action; breathing every 32f"),
    (r"crowd", "mill: 3 offset 16f loops, mass reads as texture"),
    (r"person|people|figure|silhouette|walker|man|woman", "walk cycle 12 drawings on twos (24f): contact-down-pass-up"),
    (r"fabric|laundry|sarong|cloth|textile|flag|curtain|awning", "flutter wave 8 drawings on twos; +2f overlap per sheet"),
    (r"water|pool|lake|lagoon|canal|sea|river", "ripple rings 16f cycle; reflection shimmer 8f"),
    (r"beacon|led|lamp|light|lantern|neon|sign|screen|lattice tower", "pulse: hold 12f → flash 2f → decay 6f"),
    (r"star|constellation", "twinkle: random holds 6–18f"),
    (r"haze|fog|mist|smoke|steam|vapor", "drift 0.2%W/f; two sheets opposite directions"),
    (r"fire|flame", "flame cycle 6 drawings on ones"),
    (r"tree|plant|palm|garden|flower", "sway 48f ease-in/ease-out"),
    (r"cable|wire|line", "slow sway 32f"),
    (r"cloud|sky", "slow drift, barely moves (far plane)"),
]


def motion_for(label):
    for rx, m in MOTION:
        if re.search(rx, label): return m
    return None


def kmeans1d(x, k=3, iters=40):
    c = np.quantile(x, np.linspace(0.15, 0.85, k))
    for _ in range(iters):
        lab = np.argmin(np.abs(x[:, None] - c[None]), 1)
        nc = np.array([x[lab == i].mean() if (lab == i).any() else c[i] for i in range(k)])
        if np.allclose(nc, c): break
        c = nc
    return np.sort(c)


def dilate(m, r):
    r = int(max(1, r)); k = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (2 * r + 1, 2 * r + 1))
    return cv2.dilate(m.astype(np.uint8), k).astype(bool)


def iou(a, b):
    u = (a | b).sum(); return (a & b).sum() / u if u else 0


def dog_lines(rgb, mask=None):
    g = cv2.cvtColor(rgb, cv2.COLOR_RGB2GRAY).astype(np.float32) / 255
    d = cv2.GaussianBlur(g, (0, 0), 1.1) - cv2.GaussianBlur(g, (0, 0), 2.0)
    a = np.clip((-d - 0.006) / 0.02, 0, 1)
    if mask is not None: a *= mask
    return a


def ease(t):  # slow-in / slow-out
    return t * t * (3 - 2 * t)


def unproject_all(Z, f):
    H, W = Z.shape
    v, u = np.mgrid[0:H, 0:W].astype(np.float32)
    return np.stack([(u - W / 2) * Z / f, (v - H / 2) * Z / f, Z], -1)


def fit_plane(Z, f, mask, iters=400):
    """RANSAC ground plane in camera coords (x right, y down, z forward); normal oriented toward camera."""
    if mask.mean() < 0.01: return None
    P = unproject_all(Z, f)[mask]
    rng = np.random.default_rng(0)
    if len(P) > 30000: P = P[rng.choice(len(P), 30000, replace=False)]
    thr = 0.02 * np.median(P[:, 2]); best, bn = None, 0
    for _ in range(iters):
        a, b, c = P[rng.choice(len(P), 3, replace=False)]
        n = np.cross(b - a, c - a); nn = np.linalg.norm(n)
        if nn < 1e-9: continue
        n /= nn
        if abs(n[1]) < 0.3 and abs(n[2]) < 0.75: continue
        inl = np.abs(P @ n - n @ a) < thr
        if inl.sum() > bn: best, bn = inl, inl.sum()
    if best is None: return None
    Q = P[best]; c = Q.mean(0); n = np.linalg.svd(Q - c)[2][-1]; d = -n @ c
    if d < 0: n, d = -n, -d
    return dict(n=n.astype(np.float64), d=float(d), inlier_frac=float(bn / len(P)))


def below_horizon(n, f, W, H):
    """Pixels whose viewing ray hits the ground plane in front of the camera."""
    v, u = np.mgrid[0:H, 0:W].astype(np.float32)
    ray_dot = n[0] * (u - W / 2) / f + n[1] * (v - H / 2) / f + n[2]
    return ray_dot < 0          # ray points toward the plane (normal faces the camera)


def build(sid, notes):
    od = os.path.join(OUT, sid); md = os.path.join(od, "multiplane"); os.makedirs(md, exist_ok=True)
    S = json.load(open(os.path.join(od, "shot.json")))
    A = np.load(os.path.join(od, "arrays.npz"))
    rgb = np.array(Image.open(os.path.join(ROOT, S["file"])).convert("RGB"))
    H, W = rgb.shape[:2]
    Z = A["depth"].astype(np.float32)
    Z = np.where(np.isfinite(Z) & (Z > 0), Z, np.nanmax(Z[np.isfinite(Z)]))
    masks, dets = A["masks"], S["detections"]
    seg, ground = A["seg"], A["ground"]
    N = notes.get(sid, {})
    cam = S["camera"]

    # ---------------------------------------------------------------- P6 sky (consensus)
    # ADE sky is the authority. Detector "sky" boxes may only EXTEND sky that ADE already found
    # (connected + farther than the scene) — otherwise a bright ceiling becomes sky (Naraka).
    sky_sem = A["sky"].copy()
    sky = sky_sem.copy()
    det_sky = np.zeros((H, W), bool)
    for d, m in zip(dets, masks):
        if SKY_RE.search(d["label"]) and d["score"] > 0.3: det_sky |= m
    if sky_sem.any() and det_sky.any():
        zq = np.quantile(Z[~sky_sem], 0.85) if (~sky_sem).any() else 0
        cand_s = det_sky & (Z > zq) & ~ground & ~sky_sem
        n, cc, _, _ = cv2.connectedComponentsWithStats((cand_s | sky_sem).astype(np.uint8), 8)
        keep = np.unique(cc[sky_sem]); sky |= cand_s & np.isin(cc, keep[keep > 0])
    sky_votes = sky_sem.astype(np.uint8) + det_sky.astype(np.uint8) + (Z > np.quantile(Z, 0.9)).astype(np.uint8)

    # ---------------------------------------------------------------- ground (consensus: semantic ∧ geometric)
    plane = fit_plane(Z, float(A["focal_px"]), ground & ~sky)
    things = np.zeros((H, W), bool)
    for d, m in zip(dets, masks):
        if not re.search(r"floor|street|road|water|pool|path|steps|stairs|plaza|ground|deck|platform|catwalk|sidewalk", d["label"]):
            things |= m
    if plane:
        P = unproject_all(Z, float(A["focal_px"]))
        res = np.abs(P @ plane["n"] + plane["d"]) / np.maximum(Z, 1e-3)
        below = below_horizon(plane["n"], float(A["focal_px"]), W, H)
        geo_t, geo_l = res < 0.04, res < 0.12
        ground_c = (ground & geo_l) | (geo_t & below & ~things & ~sky)
        ground_votes = ground.astype(np.uint8) + geo_t.astype(np.uint8) + (below & ~things).astype(np.uint8)
    else:
        ground_c, ground_votes = ground.copy(), ground.astype(np.uint8) * 2
    ground = ground_c

    # ---------------------------------------------------------------- characters / hero
    cand = sorted([i for i, d in enumerate(dets) if CHAR_RE.search(d["label"]) and d["area_frac"] < 0.25
                   and d["score"] >= 0.27], key=lambda i: -dets[i]["score"])
    kept = []
    for i in cand:                                   # one sheet per body (child/person overlap)
        if all(iou(masks[i], masks[j]) < 0.6 for j in kept): kept.append(i)
    subj = N.get("hero") or next((p for p in S["hints"]["phrases"] if CHAR_RE.search(p)), "person")
    hero_kind, P2, hero_ids = None, np.zeros((H, W), bool), []
    director_elem = bool(N.get("hero")) and not CHAR_RE.search(N["hero"])   # director names a non-character performer
    if N.get("hero") and CHAR_RE.search(N["hero"]):
        match = [i for i in kept if N["hero"] in dets[i]["label"] or dets[i]["label"] in N["hero"]
                 or (N["hero"] in ("child", "kid") and dets[i]["label"] in ("child", "kid"))]
        if not match and N["hero"] in ("child", "kid", "person"):
            match = [i for i in kept if dets[i]["label"] in ("person", "child", "silhouette")]
        if not match: kept_for_hero = []; hero_kind = "to_draw"
        else: kept_for_hero = match
    else:
        kept_for_hero = [] if director_elem else kept
    if kept_for_hero:
        def score(i):
            d = dets[i]; cx = (d["box"][0] + d["box"][2]) / 2 / W
            return d["score"] * (2.0 if subj in d["label"] or d["label"] in subj else 1.0) * (1 - 0.5 * abs(cx - 0.5)) * d["area_frac"] ** 0.25
        h = max(kept_for_hero, key=score); zh = np.median(Z[masks[h]])
        hero_ids = [i for i in kept_for_hero if (dets[i]["label"] == dets[h]["label"] or i == h)
                    and 0.7 < np.median(Z[masks[i]]) / zh < 1.45]
        hero_kind = "character"
    elif hero_kind != "to_draw":                      # no characters: the most animatable element performs
        pool = [i for i, d in enumerate(dets) if 0.004 < d["area_frac"] < 0.45 and d["score"] > 0.28 and not SKY_RE.search(d["label"])]
        pref = [lambda l: N.get("hero") and (N["hero"] in l or l in N["hero"]), CLOTH_RE.search, FX_RE.search, WATER_RE.search]
        for f in pref:
            hit = [i for i in pool if f(dets[i]["label"])]
            if hit:
                def escore(i):
                    b = dets[i]["box"]; cx = (b[0] + b[2]) / 2 / W
                    edge = b[0] <= 3 or b[2] >= W - 3
                    return dets[i]["score"] * dets[i]["area_frac"] ** 0.3 * (1 - abs(cx - 0.5)) * (0.25 if edge else 1)
                lab = max(hit, key=escore)
                zl = np.median(Z[masks[lab]])
                hero_ids = [i for i in hit if dets[i]["label"] == dets[lab]["label"]
                            and 0.7 < np.median(Z[masks[i]]) / zl < 1.45]
                hero_kind = "element"; break
    for i in hero_ids: P2 |= masks[i]
    P2 &= ~sky
    Zh = float(np.median(Z[P2])) if P2.any() else None

    # ---------------------------------------------------------------- P3 secondary sheets (own depth each)
    sec = []
    for i, d in enumerate(dets):
        if i in hero_ids or d["area_frac"] > 0.3 or d["score"] < 0.27: continue
        lab = d["label"]
        if (i in kept) or (CLOTH_RE.search(lab) or FX_RE.search(lab)) and not SKY_RE.search(lab):
            b = d["box"]
            if i not in kept and Zh and np.median(Z[masks[i]]) < 0.85 * Zh and \
                    (b[0] <= 0.06 * W or b[2] >= 0.94 * W or d["area_frac"] > 0.05):
                continue                              # near edge-touching piece = framing, let it fall to P0
            m = masks[i] & ~P2 & ~sky
            if m.sum() > 0.0005 * H * W and all(iou(m, s["mask"]) < 0.6 for s in sec):
                sec.append(dict(mask=m, label=lab))
    P3 = np.zeros((H, W), bool)
    for s in sec: s["mask"] &= ~P3; P3 |= s["mask"]
    # an element hero recruits its whole family from the ADE map (all laundry on the line, all lamps...)
    if hero_kind == "element":
        hl = dets[hero_ids[0]]["label"]
        fam = [k for k, v in enumerate(A["id2label"]) if (CLOTH_RE.search(hl) and CLOTH_RE.search(str(v)) or re.search(r"clothes", str(v)) and CLOTH_RE.search(hl))
               or (FX_RE.search(hl) and re.search(r"\b(light|lamp|chandelier|sconce)\b", str(v)))]
        fm = np.isin(seg, fam) & ~P2 & ~P3 & ~sky
        n, cc, st, _ = cv2.connectedComponentsWithStats(fm.astype(np.uint8), 8)
        for j in sorted(range(1, n), key=lambda j: -st[j, 4])[:12]:
            if st[j, 4] > 0.002 * H * W:
                m = cc == j; sec.append(dict(mask=m, label=hl + " (line)")); P3 |= m

    # ---------------------------------------------------------------- environment bands
    env = ~sky & ~P2 & ~P3
    lz = np.log(Z)
    if env.sum() < 100: env = ~sky & ~P2
    if env.sum() < 100: env = np.ones((H, W), bool)      # all sky/hero frame (video keyframes): bands from the whole frame
    c = kmeans1d(lz[env][:: max(1, env.sum() // 60000)], 3)
    b1, b2 = (c[0] + c[1]) / 2, (c[1] + c[2]) / 2
    if Zh:
        b1 = math.log(0.85 * Zh); b2 = max(b2, math.log(1.3 * Zh))
    band = np.where(lz < b1, 0, np.where(lz < b2, 1, 2)).astype(np.uint8)
    # rigid units: ADE components + non-character detections with small depth spread stay whole
    units = []
    for k in np.unique(seg[env]):
        n, cc, st, _ = cv2.connectedComponentsWithStats(((seg == k) & env).astype(np.uint8), 8)
        units += [cc == j for j in range(1, n) if st[j, 4] > 0.003 * H * W]
    units += [masks[i] & env for i, d in enumerate(dets) if i not in hero_ids and not CHAR_RE.search(d["label"])
              and (masks[i] & env).sum() > 0.003 * H * W]
    sliced = 0
    for u in units:
        zu = Z[u]; q10, q50, q90 = np.quantile(zu, [0.1, 0.5, 0.9])
        if q90 / max(q10, 1e-3) < 1.6:
            lb = 0 if math.log(q50) < b1 else (1 if math.log(q50) < b2 else 2); band[u] = lb
        else: sliced += 1                               # receding surface: keep per-pixel strips
    near = env & (band == 0)
    # near pieces: ground strips -> P1; framing pieces (touch L/R/top, off the ground) -> P0 camera mask.
    # Ground is split out FIRST, otherwise ceiling+wall+floor form one connected blob.
    # Top-down shots have no lens-side framing: everything near is foreground (rooftops).
    P0 = np.zeros((H, W), bool)
    overhead = (cam.get("pitch_deg") or 0) < -45
    if not overhead:
        n, cc, st, _ = cv2.connectedComponentsWithStats((near & ~ground).astype(np.uint8), 8)
        for j in range(1, n):
            x, y, w, h, a = st[j]
            if a < 0.008 * H * W: continue
            if x <= 2 or x + w >= W - 2 or y <= 2: P0 |= cc == j
    L = np.full((H, W), 255, np.uint8)
    L[sky] = 6; L[env & (band == 2)] = 5; L[env & (band == 1)] = 4
    L[near & ~P0] = 1; L[P0] = 0
    Lm = cv2.medianBlur(L, 7)                          # smooth ragged band edges (environment only)
    fix = env & np.isin(Lm, [0, 1, 4, 5]); L[fix] = Lm[fix]
    L[P3] = 3; L[P2] = 2; L[sky] = 6
    L[L == 255] = 4
    # snap environment plane edges to image superpixels: plane borders follow real edges, not depth noise
    from skimage.segmentation import slic
    sp = slic(rgb, n_segments=1800, compactness=14, start_label=0, channel_axis=-1)
    envL = np.isin(L, [0, 1, 4, 5])
    nsp = sp.max() + 1
    counts = np.zeros((nsp, 7), np.int32)
    np.add.at(counts, (sp[envL], L[envL]), 1)
    major = counts.argmax(1).astype(np.uint8); has = counts.sum(1) > 0
    snap = envL & has[sp]
    L[snap] = major[sp][snap]
    L[P3] = 3; L[P2] = 2; L[sky] = 6

    # ---------------------------------------------------------------- sheets (composited by depth)
    sheets = []
    for p in (0, 1, 4, 5, 6):
        m = L == p
        if m.sum() > 0.002 * H * W: sheets.append(dict(plane=p, mask=m, label=PLANES[p]))
    if P2.any(): sheets.append(dict(plane=2, mask=L == 2, label="hero: " + ", ".join(sorted({dets[i]["label"] for i in hero_ids}))))
    for s in sec:
        m = s["mask"] & (L == 3)
        if m.sum() > 0.0005 * H * W: sheets.append(dict(plane=3, mask=m, label=s["label"]))
    for s in sheets:
        s["z"] = float(np.median(Z[s["mask"]])) if s["plane"] != 6 else float("inf")
    sheets.sort(key=lambda s: -s["z"])                 # back to front
    zfin = [s["z"] for s in sheets if math.isfinite(s["z"])]
    Zref = Zh or float(np.median([s["z"] for s in sheets if s["plane"] == 4] or zfin))
    for s in sheets:
        s["parallax"] = 0.01 if not math.isfinite(s["z"]) else float(np.clip(Zref / s["z"], 0.02, 8.0))

    # ---------------------------------------------------------------- camera move
    move = (N.get("camera") or {}).get("move")
    if not move:
        far = L == 5; fx = np.argwhere(far)[:, 1].mean() / W if far.any() else 0.5
        if (cam.get("pitch_deg") or 0) < -45: move = "crane_push"
        elif abs(fx - 0.5) < 0.15 and far.mean() < 0.25: move = "push"
        elif cam.get("sky_frac", 0) > 0.25: move = "truck"
        else: move = "push"
    fpref = (N.get("camera") or {}).get("focus", "hero")
    def centroid(m):
        yx = np.argwhere(m); return (float(yx[:, 1].mean()), float(yx[:, 0].mean())) if len(yx) else (W / 2, H / 2)
    focus = {"far": centroid(L == 5), "hero": centroid(P2) if P2.any() else centroid(L == 4),
             "sky": centroid(sky), "center": (W / 2, H / 2)}.get(fpref, (W / 2, H / 2))
    AMP = {"truck": 0.035 * W, "tilt_up": 0.05 * H, "push": 0.06, "crane_push": 0.10}[move]
    for s in sheets:
        p = s["parallax"]
        if move in ("truck", "tilt_up"): s["shift_px"] = float(min(AMP * p, 0.3 * (W if move == "truck" else H)))
        else: s["scale_end"] = float(min(1 + AMP * p, 1.8))

    # ---------------------------------------------------------------- paint-behind strips + backing
    def disp(s):  # displacement magnitude in px at frame edge for this sheet
        return s.get("shift_px", (s.get("scale_end", 1) - 1) * 0.5 * W)
    small = (W // 2, H // 2)
    back = sheets[0]
    for k, s in enumerate(sheets):
        nearer = [t for t in sheets[k + 1:]]
        occ = np.zeros((H, W), bool)
        for t in nearer: occ |= t["mask"]
        r = max([abs(disp(t) - disp(s)) for t in nearer] or [0]) + 3
        strip = (occ & dilate(s["mask"], r)) if s is not back else ~s["mask"]
        s["strip"] = strip
        s["paint_behind_frac"] = round(float(strip.sum() / max(1, s["mask"].sum())), 3)
        alpha = s["mask"] | strip
        img = rgb.copy()
        if strip.any():                                # rough placeholder paint (the BG painter's job)
            ys, xs = np.where(alpha)
            y0, y1, x0, x1 = ys.min(), ys.max() + 1, xs.min(), xs.max() + 1
            roi = rgb[y0:y1, x0:x1]; known = s["mask"][y0:y1, x0:x1]
            sc = 0.5 if roi.size > 200000 else 1.0
            r_s = cv2.resize(roi, None, fx=sc, fy=sc, interpolation=cv2.INTER_AREA)
            k_s = cv2.resize(known.astype(np.uint8), (r_s.shape[1], r_s.shape[0]), interpolation=cv2.INTER_NEAREST)
            fill = cv2.inpaint(r_s, (1 - k_s).astype(np.uint8), 4, cv2.INPAINT_TELEA)
            fill = cv2.resize(fill, (roi.shape[1], roi.shape[0]), interpolation=cv2.INTER_CUBIC)
            st_roi = strip[y0:y1, x0:x1]
            img[y0:y1, x0:x1][st_roi] = fill[st_roi]
        s["rgba"] = np.dstack([img, (alpha * 255).astype(np.uint8)])
        s["file"] = f"S{k:02d}_P{s['plane']}.png"
        Image.fromarray(s["rgba"]).save(os.path.join(md, s["file"]))

    # ---------------------------------------------------------------- per-plane exports + glow + haze
    hsv = cv2.cvtColor(rgb, cv2.COLOR_RGB2HSV)
    glow_src = (hsv[..., 2] > 235) & ((hsv[..., 1] > 60) | (hsv[..., 2] > 250))
    glow_src = cv2.morphologyEx(glow_src.astype(np.uint8), cv2.MORPH_OPEN, np.ones((2, 2), np.uint8)).astype(bool)
    gl = cv2.GaussianBlur(rgb.astype(np.float32) * glow_src[..., None], (0, 0), 12) * 2.2
    Image.fromarray(np.clip(gl, 0, 255).astype(np.uint8)).save(os.path.join(md, "glow_pass.png"))
    dark = cv2.erode(rgb.min(2), np.ones((15, 15), np.uint8)).astype(np.float32)
    Aatm = float(np.max(rgb.reshape(-1, 3)[np.argsort(dark.ravel())[-max(10, dark.size // 1000):]].mean(0)))
    planes_out = []
    for p in range(7):
        m = L == p
        lab_here = sorted({d["label"] for d, mk in zip(dets, masks) if (mk & m).sum() > 0.4 * mk.sum() and mk.sum() > 0})
        ade = [str(A["id2label"][k]).split(",")[0] for k, c_ in zip(*np.unique(seg[m], return_counts=True))
               if c_ > 0.01 * max(1, m.sum())] if m.any() else []
        contents = list(dict.fromkeys(lab_here + ade))
        mot = list(dict.fromkeys([mm for mm in (motion_for(cn) for cn in contents) if mm]))
        sh = [s for s in sheets if s["plane"] == p]
        line = dog_lines(rgb, m.astype(np.float32))
        Image.fromarray(np.dstack([np.zeros((H, W, 3), np.uint8), (line * 255).astype(np.uint8)])).save(os.path.join(md, f"P{p}_line.png"))
        planes_out.append(dict(
            id=f"P{p}", name=PLANES[p], area_frac=round(float(m.mean()), 3),
            z_median_m=(round(float(np.median(Z[m])), 2) if m.any() and p != 6 else None),
            parallax=(round(float(np.mean([s["parallax"] for s in sh])), 3) if sh else None),
            sheets=[s["file"] for s in sh], contents=contents[:14], motion=mot,
            glow_px=int((glow_src & m).sum()), haze=round(float(dark[m].mean() / max(Aatm, 1)), 3) if m.any() else None,
            paint_behind_frac=(round(float(np.mean([s["paint_behind_frac"] for s in sh])), 3) if sh else None),
            overscan_px=(int(math.ceil(max(disp(s) for s in sh))) if sh else 0)))

    # ---------------------------------------------------------------- silhouette test (hero black on grey)
    sil = np.full((H, W, 3), 205, np.uint8)
    sil[L == 3] = 150; sil[np.isin(L, [0, 1])] = 175; sil[P2] = 0
    Image.fromarray(sil).save(os.path.join(md, "silhouette.png"))
    silm = {}
    if hero_kind == "to_draw":
        silm = dict(hero_kind="to_draw", hero_labels=[N["hero"]], hero_count=0,
                    note=f"P2 is empty: the director's '{N['hero']}' is not in the frame — draw it (see staging).")
    if P2.any():
        lum = cv2.cvtColor(rgb, cv2.COLOR_RGB2GRAY).astype(np.float32)
        ring = dilate(P2, 15) & ~P2
        edge = dilate(P2, 1) & ~P2
        silm = dict(hero_kind=hero_kind, hero_labels=sorted({dets[i]["label"] for i in hero_ids}), hero_count=len(hero_ids),
                    contrast=round(abs(float(lum[P2].mean() - lum[ring].mean())) / 255, 3),
                    tangency=round(float((edge & dilate(P3, 3)).sum() / max(1, edge.sum())), 3),
                    frame_share=round(float(P2.mean()), 4), z_m=round(Zh, 2))

    # ---------------------------------------------------------------- previews
    # layout drawing: paper, blue-pencil environment, red hero, orange FX
    paper = np.full((H, W, 3), (246, 241, 230), np.float32)
    for p in (6, 5, 4, 1, 0, 3, 2):
        ln = dog_lines(rgb, (L == p).astype(np.float32)) * (1.6 if p == 2 else 1.0)
        col = np.array(PCOL[p], np.float32)
        paper = paper * (1 - np.clip(ln, 0, 1)[..., None]) + col * np.clip(ln, 0, 1)[..., None]
    Image.fromarray(paper.astype(np.uint8)).save(os.path.join(md, "layout_drawing.png"))
    # plane map
    pm = np.zeros((H, W, 3), np.uint8)
    for p in range(7): pm[L == p] = PCOL[p]
    Image.fromarray((rgb * 0.35 + pm * 0.65).astype(np.uint8)).save(os.path.join(md, "plane_map.jpg"), quality=88)
    exploded(md, sheets, planes_out, W, H)
    parallax_preview(md, sheets, move, focus, gl, W, H)

    xs, f = [], 1
    for kid, desc, n in N.get("keys", []):
        xs.append(dict(frame=f, drawing=kid, exposure=n, action=desc)); f += n
    rec = dict(id=sid, title=N.get("title"), action=N.get("action"), emotion=N.get("emotion"), beats=N.get("beats"),
               staging=N.get("staging"), secondary=N.get("secondary"),
               camera=dict(move=move, why=(N.get("camera") or {}).get("why", "auto: chosen from shot grammar"),
                           focus=[round(focus[0]), round(focus[1])], amplitude=AMP, z_ref_m=round(Zref, 2)),
               planes=planes_out, silhouette=silm, receding_surfaces_sliced=sliced,
               sheets=[dict(file=s["file"], plane=f"P{s['plane']}", label=s["label"],
                            z_m=(round(s["z"], 2) if math.isfinite(s["z"]) else None), parallax=round(s["parallax"], 3),
                            paint_behind_frac=s["paint_behind_frac"]) for s in sheets],
               xsheet=xs, duration_frames=f - 1)
    json.dump(rec, open(os.path.join(md, "multiplane.json"), "w"), indent=2)
    np.savez_compressed(os.path.join(md, "planes.npz"), L=L, P2=P2, P3=P3, sky=sky, ground=ground,
                        sky_votes=sky_votes, ground_votes=ground_votes, superpixels=sp.astype(np.int32),
                        plane_n=(plane["n"] if plane else np.zeros(3)), plane_d=np.float64(plane["d"] if plane else 0),
                        has_plane=bool(plane), focal_px=A["focal_px"], hero_kind=str(hero_kind),
                        sheet_files=np.array([s["file"] for s in sheets]))
    return rec


def exploded(md, sheets, planes_out, W, H):
    sc = 0.42; w, h = int(W * sc), int(H * sc)
    npl = len({s["plane"] for s in sheets})
    CW, CH = 1300, 70 + (npl - 1) * 95 + int(h * 0.45) + 20
    canvas = Image.new("RGB", (CW, CH), (9, 11, 16)); dr = ImageDraw.Draw(canvas)
    try: font = ImageFont.truetype("/System/Library/Fonts/Supplemental/Arial.ttf", 17); fs = ImageFont.truetype("/System/Library/Fonts/Supplemental/Arial.ttf", 13)
    except Exception: font = fs = ImageFont.load_default()
    order = [6, 5, 4, 3, 2, 1, 0]
    shear = np.float32([[1, 0.55, 0], [0, 0.45, 0]])
    y = 40
    for p in order:
        sh = [s for s in sheets if s["plane"] == p]
        info = planes_out[p]
        if not sh: continue
        comp = np.zeros((H, W, 4), np.uint8)
        for s in sh:
            a = s["rgba"][..., 3:4].astype(np.float32) / 255
            comp[..., :3] = (comp[..., :3] * (1 - a) + s["rgba"][..., :3] * a).astype(np.uint8)
            comp[..., 3] = np.maximum(comp[..., 3], s["rgba"][..., 3])
        small = cv2.resize(comp, (w, h), interpolation=cv2.INTER_AREA)
        warped = cv2.warpAffine(small, shear, (int(w + h * 0.55) + 2, int(h * 0.45) + 2))
        frame = np.zeros_like(warped); cv2.polylines(frame, [np.int32([[0, 0], [w, 0], [w + h * 0.55, h * 0.45], [h * 0.55, h * 0.45]])], True, (*PCOL[p], 255), 1)
        warped = np.where(warped[..., 3:4] > 0, warped, frame)
        im = Image.fromarray(warped, "RGBA")
        canvas.paste(im, (380, y), im)
        z = f"Z {info['z_median_m']} m" if info["z_median_m"] is not None else "Z ∞"
        dr.rectangle([30, y + 8, 40, y + 18], fill=PCOL[p])
        dr.text((50, y + 4), f"P{p}  {PLANES[p]}", fill=(232, 236, 243), font=font)
        dr.text((50, y + 28), f"{z} · parallax ×{info['parallax']} · {int(info['area_frac'] * 100)}% frame", fill=(138, 149, 168), font=fs)
        dr.text((50, y + 46), ", ".join(info["contents"][:5])[:48], fill=(110, 120, 138), font=fs)
        y += 95
    canvas.save(os.path.join(md, "exploded.jpg"), quality=90)


def parallax_preview(md, sheets, move, focus, glow, W, H, n_draw=24, scale=0.5):
    w, h = int(W * scale), int(H * scale); fx, fy = focus[0] * scale, focus[1] * scale
    pad = int(max([s.get("shift_px", 0) for s in sheets] + [0]) * scale) + 4
    prepped = []
    for s in sheets:
        im = cv2.resize(s["rgba"], (w, h), interpolation=cv2.INTER_AREA)
        if move in ("truck", "tilt_up"): im = cv2.copyMakeBorder(im, pad, pad, pad, pad, cv2.BORDER_REPLICATE)
        prepped.append((s, im.astype(np.float32)))
    g = cv2.resize(glow, (w, h)).astype(np.float32)
    frames = []
    for t in range(n_draw):
        e = ease(t / (n_draw - 1))
        out = np.zeros((h, w, 3), np.float32)
        for s, im in prepped:
            if move in ("truck", "tilt_up"):
                d = (e - 0.5) * s["shift_px"] * scale
                dx, dy = (-d, 0) if move == "truck" else (0, d)
                M = np.float32([[1, 0, dx - pad], [0, 1, dy - pad]])
            else:
                k = 1 + (s["scale_end"] - 1) * e
                M = np.float32([[k, 0, fx - k * fx], [0, k, fy - k * fy]])
            wim = cv2.warpAffine(im, M, (w, h), flags=cv2.INTER_LINEAR, borderMode=cv2.BORDER_CONSTANT)
            a = wim[..., 3:4] / 255
            out = out * (1 - a) + wim[..., :3] * a
            if s is prepped[-1][0]: pass
        out = np.clip(out + 0.35 * g, 0, 255).astype(np.uint8)
        frames.append(Image.fromarray(out))
    frames = frames + frames[::-1]                     # ping-pong so it loops
    frames[0].save(os.path.join(md, "parallax.webp"), save_all=True, append_images=frames[1:],
                   duration=83, loop=0, quality=80)  # 83 ms = each drawing held 2 frames @24fps ("on twos")


def main():
    ap = argparse.ArgumentParser(); ap.add_argument("--match", nargs="*"); a = ap.parse_args()
    notes = {k: v for k, v in json.load(open(os.path.join(ROOT, "shots", "director_notes.json"))).items() if not k.startswith("_")}
    ids = sorted(os.path.basename(os.path.dirname(p)) for p in glob.glob(os.path.join(OUT, "*", "arrays.npz")))
    if a.match: ids = [i for i in ids if any(m in i for m in a.match)]
    allrec = {}
    for sid in ids:
        r = build(sid, notes)
        allrec[sid] = r
        pl = " ".join(f"P{p['id'][1]}:{int(p['area_frac']*100)}%" for p in r["planes"] if p["area_frac"] > 0)
        print(f"{sid[:8]} {r['camera']['move']:10s} hero={r['silhouette'].get('hero_labels')} {pl}")
    prev = {}
    for p in glob.glob(os.path.join(OUT, "*", "multiplane", "multiplane.json")):
        j = json.load(open(p)); prev[j["id"]] = j
    with open(os.path.join(ROOT, "shots", "multiplane_data.js"), "w") as fh:
        fh.write("window.MP = " + json.dumps(prev) + ";\n")
    print(f"wrote {len(prev)} multiplane records")


if __name__ == "__main__":
    main()
