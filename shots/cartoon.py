#!/usr/bin/env python3
"""
Cartoon signal stack: turns a multiplane decomposition into strong, drawable signals.

Photographic evidence is weak for a cartoon: texture, noise, soft edges. A layout artist wants
SHAPES, CONTOURS, VALUES and PERSPECTIVE. Each signal below is built from >1 source so it holds up:

  1. regions      cel regions = plane × (ADE class | SAM instance), superpixel-snapped, tiny bits merged
  2. flats        one colour per region, snapped to a small per-plane palette, pushed toward the shot's
                  own haze colour by depth (atmospheric perspective); hero kept saturated; sky = gradient
  3. ink          contours from region boundaries, NOT texture:
                    plane edges (occlusion) heavy · interior edges light · near planes thicker than far
                  + selective interior detail only near the focal point, never in sky/far planes
  4. notan        every plane as one value; values spread so depth-adjacent planes separate; hero flips
                  to the extreme opposite of its surround. Reports which planes merge in the source.
  5. perspective  horizon, vanishing point, ground grid from the fitted 3D plane (strong on consensus
                  ground, faint elsewhere) + a character scale ladder (1.7 m figures stood on the ground)
  6. composites   cel.png (flats+ink+glow) · layout_sheet.png (paper, coloured plane contours, grid, ladder,
                  plane tags) · planes_gs.png (plane map × ground grid × sky gradient) ·
                  plane_silhouettes.png (each plane alone, black on white) · consensus.png (vote maps)

Usage: .venv-shots/bin/python shots/cartoon.py [--match id-substr ...]
"""
import argparse, glob, json, math, os
import numpy as np
import cv2
from PIL import Image, ImageDraw, ImageFont
from scipy import ndimage as ndi
from skimage.measure import label as sk_label

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, "shots", "out")
NAMES = {0: "camera mask", 1: "foreground", 2: "character", 3: "secondary/FX", 4: "midground", 5: "distant", 6: "sky"}
PCOL = {0: (60, 60, 70), 1: (150, 100, 60), 2: (205, 40, 45), 3: (235, 140, 30),
        4: (45, 105, 210), 5: (110, 160, 225), 6: (120, 195, 220)}
INK_W = {0: 4.2, 1: 3.0, 2: 3.8, 3: 2.4, 4: 1.8, 5: 1.2, 6: 0.0}     # near heavy → far light
PAL_K = {0: 3, 1: 3, 2: 4, 3: 3, 4: 3, 5: 2, 6: 2}
PAPER = np.array([246, 241, 230], np.float32)


def font(sz):
    try: return ImageFont.truetype("/System/Library/Fonts/Supplemental/Arial.ttf", sz)
    except Exception: return ImageFont.load_default()


def lum(rgb): return (0.2126 * rgb[..., 0] + 0.7152 * rgb[..., 1] + 0.0722 * rgb[..., 2]) / 255.0


def stroke_alpha(mask, width):
    """Anti-aliased line of given width centred on a 1-px boundary mask."""
    if width <= 0 or not mask.any(): return np.zeros(mask.shape, np.float32)
    dt = ndi.distance_transform_edt(~mask)
    return np.clip(width / 2 + 0.5 - dt, 0, 1).astype(np.float32)


def render(sid):
    od = os.path.join(OUT, sid); md = os.path.join(od, "multiplane"); cd = os.path.join(od, "cartoon")
    os.makedirs(cd, exist_ok=True)
    S = json.load(open(os.path.join(od, "shot.json")))
    MP = json.load(open(os.path.join(md, "multiplane.json")))
    A = np.load(os.path.join(od, "arrays.npz")); PL = np.load(os.path.join(md, "planes.npz"))
    rgb = np.array(Image.open(os.path.join(ROOT, S["file"])).convert("RGB"))
    H, W = rgb.shape[:2]
    L, sky, ground, P2 = PL["L"], PL["sky"], PL["ground"], PL["P2"]
    seg, masks = A["seg"].astype(np.int32), A["masks"]
    Z = A["depth"].astype(np.float32); f = float(PL["focal_px"])

    # ------------------------------------------------------------ depth rank per plane (for haze/ink)
    zp = {int(p["id"][1]): p["z_median_m"] for p in MP["planes"] if p["area_frac"] > 0}
    fin = [v for v in zp.values() if v]
    lo, hi = (math.log(min(fin)), math.log(max(fin))) if fin else (0, 1)
    rank = {p: (1.0 if p == 6 else ((math.log(v) - lo) / max(hi - lo, 1e-6) if v else 0.5)) for p, v in zp.items()}

    # ------------------------------------------------------------ 1. cel regions
    part = seg.copy()
    for i, m in enumerate(masks):                      # characters/FX keep their instance identity
        sel = m & np.isin(L, [2, 3]); part[sel] = 200 + i
    key = L.astype(np.int32) * 1000 + part
    R = sk_label(key, background=-1, connectivity=1)
    sizes = np.bincount(R.ravel())
    small = sizes[R] < 0.0008 * H * W
    if small.any() and (~small).any():
        _, (iy, ix) = ndi.distance_transform_edt(small, return_indices=True)
        R = R[iy, ix]
    nR = R.max() + 1
    cnt = np.bincount(R.ravel(), minlength=nR).astype(np.float32)
    mean = np.stack([np.bincount(R.ravel(), rgb[..., c].ravel().astype(np.float32), nR) for c in range(3)], 1) / np.maximum(cnt, 1)[:, None]
    rplane = np.zeros(nR, np.int32)
    rplane[R.ravel()] = L.ravel()                      # regions are single-plane by construction (small merges may blur this)

    # ------------------------------------------------------------ 2. flats
    dark = cv2.erode(rgb.min(2), np.ones((15, 15), np.uint8)).astype(np.float32)
    top = np.argsort(dark.ravel())[-max(10, dark.size // 1000):]
    haze = rgb.reshape(-1, 3)[top].mean(0)              # the shot's own atmosphere colour
    rcol = mean.copy()
    for p in range(7):
        ids = np.where((rplane == p) & (cnt > 0))[0]
        if len(ids) == 0: continue
        k = min(PAL_K[p], len(ids))
        lab = cv2.cvtColor((mean[ids][None] / 255).astype(np.float32), cv2.COLOR_RGB2LAB)[0]
        w = np.repeat(np.arange(len(ids)), np.clip((cnt[ids] / cnt[ids].sum() * 4000).astype(int), 1, None))
        data = lab[w].astype(np.float32)
        if k > 1 and len(np.unique(data, axis=0)) >= k:
            _, lbl, cen = cv2.kmeans(data, k, None, (cv2.TERM_CRITERIA_EPS + cv2.TERM_CRITERIA_MAX_ITER, 30, 0.5), 3, cv2.KMEANS_PP_CENTERS)
            near = np.argmin(((lab[:, None] - cen[None]) ** 2).sum(-1), 1)
            snapped = cv2.cvtColor(cen[near][None].astype(np.float32), cv2.COLOR_LAB2RGB)[0] * 255
            rcol[ids] = 0.35 * mean[ids] + 0.65 * snapped   # keep a little local variation
        if p == 2:                                       # hero: saturate, no haze
            g = rcol[ids].mean(1, keepdims=True); rcol[ids] = np.clip(g + (rcol[ids] - g) * 1.25, 0, 255)
        elif p != 6:
            a = 0.08 + 0.45 * rank.get(p, 0.5)
            rcol[ids] = rcol[ids] * (1 - a) + haze * a
    F = rcol[R].astype(np.float32)
    if sky.any():                                        # painted sky: vertical gradient + stars as dots
        rows = np.where(sky.any(1))[0]
        rc = np.array([rgb[r][sky[r]].mean(0) for r in rows])
        allr = np.arange(H)
        prof = np.stack([np.interp(allr, rows, ndi.gaussian_filter1d(rc[:, c], 12)) for c in range(3)], 1)
        F[sky] = (prof[:, None, :].repeat(W, 1))[sky] * 0.85 + haze * 0.15
        g = cv2.cvtColor(rgb, cv2.COLOR_RGB2GRAY).astype(np.float32)
        top_hat = g - cv2.GaussianBlur(g, (0, 0), 4)
        cand = ((top_hat > 55) & (g > np.quantile(g[sky], 0.97)) & sky).astype(np.uint8)
        nc, cl, st, _ = cv2.connectedComponentsWithStats(cand, 8)
        keep = np.zeros(nc, bool); keep[1:] = st[1:, 4] <= 9          # point lights only, not cloud texture
        stars = keep[cl]
        if stars.mean() > 0.004 * sky.mean(): stars[:] = False         # too many → it's texture, not stars
        F[cv2.dilate(stars.astype(np.uint8), np.ones((2, 2), np.uint8)).astype(bool)] = (250, 246, 225)

    # ------------------------------------------------------------ 3. ink
    pl = L.astype(np.int16)
    edges_plane = np.zeros((H, W), bool); edges_int = np.zeros((H, W), bool)
    owner = np.full((H, W), 6, np.int16)
    for dy, dx in ((0, 1), (1, 0)):
        a_r = R[:H - dy, :W - dx]; b_r = R[dy:, dx:]
        a_p = pl[:H - dy, :W - dx]; b_p = pl[dy:, dx:]
        diff = a_r != b_r
        za = Z[:H - dy, :W - dx]; zb = Z[dy:, dx:]
        own = np.where(za <= zb, a_p, b_p)               # the nearer side owns the line
        own = np.where(a_p == 6, b_p, np.where(b_p == 6, a_p, own))
        pe = diff & (a_p != b_p); ie = diff & (a_p == b_p)
        sl = (slice(0, H - dy), slice(0, W - dx))
        edges_plane[sl] |= pe; edges_int[sl] |= ie
        owner[sl] = np.where(diff, own, owner[sl])
    ink = np.zeros((H, W), np.float32); ink_col = np.zeros((H, W, 3), np.float32)
    for p in range(6):
        for em, mult in ((edges_plane, 1.0), (edges_int, 0.42)):
            m = em & (owner == p)
            if p == 2 and em is edges_plane: m |= (edges_plane | edges_int) & cv2.dilate(P2.astype(np.uint8), np.ones((3, 3))).astype(bool) & (owner == 2)
            a = stroke_alpha(m, INK_W[p] * mult)
            upd = a > ink
            ink = np.maximum(ink, a); ink_col[upd] = PCOL[p]
    # selective interior detail: only near the focal point, only P0–P4, never sky
    gray = cv2.cvtColor(rgb, cv2.COLOR_RGB2GRAY).astype(np.float32) / 255
    dog = cv2.GaussianBlur(gray, (0, 0), 1.2) - cv2.GaussianBlur(gray, (0, 0), 2.2)
    det = np.clip((-dog - 0.014) / 0.02, 0, 1)
    fx, fy = MP["camera"]["focus"]
    yy, xx = np.mgrid[0:H, 0:W]
    falloff = np.exp(-(((xx - fx) / (0.45 * W)) ** 2 + ((yy - fy) / (0.55 * H)) ** 2))
    lut = np.zeros(256, np.float32); lut[:7] = (.5, .8, 1, .8, .45, .15, 0)
    pw = lut[L.astype(np.uint8)]
    detail = det * falloff * pw * 0.7

    # ------------------------------------------------------------ 4. notan
    present = [p for p in range(7) if (L == p).mean() > 0.002]
    orig_v = {p: float(lum(rgb)[L == p].mean()) for p in present}
    order = sorted(present, key=lambda p: orig_v[p])
    env_order = [p for p in order if p != 2]
    ladder = np.linspace(0.1, 0.9, max(len(env_order), 2))
    notan_v = {p: float(ladder[i]) for i, p in enumerate(env_order)}
    if 2 in present:
        ring = cv2.dilate(P2.astype(np.uint8), np.ones((31, 31), np.uint8)).astype(bool) & ~P2
        surround = float(np.mean([notan_v.get(int(p), .5) for p in L[ring][:: max(1, ring.sum() // 5000)]])) if ring.any() else .5
        notan_v[2] = 0.02 if surround > 0.45 else 0.98
    N = np.zeros((H, W), np.float32)
    for p, v in notan_v.items(): N[L == p] = v
    depth_sorted = sorted([p for p in present if p != 2], key=lambda p: rank.get(p, .5))
    merges = []
    for a_, b_ in zip(depth_sorted, depth_sorted[1:]):
        sep = abs(orig_v[a_] - orig_v[b_])
        if sep < 0.06: merges.append(dict(planes=[f"P{a_}", f"P{b_}"], separation=round(sep, 3)))

    # ------------------------------------------------------------ 5. perspective
    persp = np.zeros((H, W, 4), np.float32); ladder_pts = []; vp = None; horizon = None
    if bool(PL["has_plane"]):
        n = PL["plane_n"].astype(np.float64); d = float(PL["plane_d"])
        up = n
        fwd = np.array([0, 0, 1.0]) - up * up[2]
        if np.linalg.norm(fwd) < 0.2: fwd = np.array([0, -1.0, 0]) - up * (-up[1])
        fwd /= np.linalg.norm(fwd); right = np.cross(fwd, up); right /= np.linalg.norm(right)
        foot = -d * up
        def proj(P):
            P = np.atleast_2d(P); ok = P[:, 2] > 0.05
            uv = np.stack([f * P[:, 0] / np.maximum(P[:, 2], 1e-3) + W / 2, f * P[:, 1] / np.maximum(P[:, 2], 1e-3) + H / 2], 1)
            return uv, ok
        zg = Z[ground] if ground.any() else Z.ravel()
        zfar = float(np.quantile(zg, 0.97)) * 1.4
        s = float(np.clip(10 ** round(math.log10(max(d, 0.3) * 0.8)), 0.5, 20))
        if zfar / s > 60: s *= 2
        cv_img = np.zeros((H, W), np.uint8)
        K = int(min(60, zfar / s))
        for i in range(-K, K + 1):                      # receding lines
            P = foot + i * s * right + np.linspace(0.2, zfar, 200)[:, None] * fwd
            uv, ok = proj(P)
            if ok.sum() > 2: cv2.polylines(cv_img, [uv[ok].astype(np.int32)], False, 255, 1, cv2.LINE_AA)
        for j in range(1, K + 1):                       # cross lines
            P = foot + j * s * fwd + np.linspace(-zfar, zfar, 200)[:, None] * right
            uv, ok = proj(P)
            if ok.sum() > 2: cv2.polylines(cv_img, [uv[ok].astype(np.int32)], False, 255, 1, cv2.LINE_AA)
        g_on = cv_img.astype(np.float32) / 255
        zq = float(np.quantile(zg, 0.9))
        fade = np.clip(1.25 - Z / max(zq, 1e-3), 0.12, 1.0)          # grid recedes instead of piling into moiré
        strength = np.where(ground, 0.85, 0.16) * fade
        persp[..., 3] = g_on * strength; persp[..., :3] = (60, 110, 200)
        if fwd[2] > 0.05:
            vp = [float(f * fwd[0] / fwd[2] + W / 2), float(f * fwd[1] / fwd[2] + H / 2)]
        if abs(n[1]) > 1e-6:
            hv = lambda u: H / 2 - f * (n[0] * (u - W / 2) / f + n[2]) / n[1]
            a_, b_ = float(hv(0)), float(hv(W))
            if -H < a_ < 2 * H: horizon = [[0, a_], [W, b_]]
        # scale ladder: one 1.7 m figure per depth, staggered across frame, only standing on consensus ground
        zs = np.geomspace(max(np.quantile(zg, 0.08), 0.5), max(np.quantile(zg, 0.9), 1.0), 7)
        cols = (0.5, 0.3, 0.7, 0.15, 0.85, 0.42, 0.58)
        for k, zk in enumerate(zs):
            for j in range(len(cols)):
                ux = cols[(k * 2 + j) % len(cols)]
                base = foot + (zk * fwd) + ((ux * W - W / 2) * zk / f) * right
                top = base + 1.7 * up
                (b_uv, okb), (t_uv, okt) = proj(base), proj(top)
                if not (okb[0] and okt[0]): continue
                bu, bv = b_uv[0]; tu, tv = t_uv[0]; hgt = abs(bv - tv)
                if 0 <= bu < W and 0 <= bv < H and ground[int(bv), int(bu)] and 8 < hgt < 0.42 * H:
                    ladder_pts.append(dict(base=[float(bu), float(bv)], top=[float(tu), float(tv)], z_m=round(float(zk), 1)))
                    break

    # ------------------------------------------------------------ 6. composites
    glow_p = os.path.join(md, "glow_pass.png")
    glow = np.array(Image.open(glow_p)).astype(np.float32) if os.path.exists(glow_p) else 0
    # 6a cel preview
    cel = F.copy() + 0.45 * glow
    cel = cel * (1 - detail[..., None] * 0.55) + 25 * detail[..., None] * 0.55
    cel = cel * (1 - ink[..., None]) + np.array([22, 18, 24], np.float32) * ink[..., None]
    Image.fromarray(np.clip(cel, 0, 255).astype(np.uint8)).save(os.path.join(cd, "cel.png"))
    Image.fromarray(np.clip(F, 0, 255).astype(np.uint8)).save(os.path.join(cd, "flats.png"))
    Image.fromarray(np.dstack([np.zeros((H, W, 3), np.uint8), (np.clip(ink + detail * 0.6, 0, 1) * 255).astype(np.uint8)])).save(os.path.join(cd, "ink.png"))
    # 6b layout sheet
    sheet = PAPER * 0.78 + F * 0.22
    a = persp[..., 3:4]; sheet = sheet * (1 - a) + persp[..., :3] * a
    sheet = sheet * (1 - detail[..., None] * 0.5) + np.array([90, 90, 100]) * detail[..., None] * 0.5
    sheet = sheet * (1 - ink[..., None]) + ink_col * ink[..., None]
    im = Image.fromarray(np.clip(sheet, 0, 255).astype(np.uint8)); dr = ImageDraw.Draw(im)
    if horizon: dr.line([tuple(horizon[0]), tuple(horizon[1])], fill=(45, 105, 210), width=2); dr.text((10, horizon[0][1] - 18), "HORIZON", fill=(45, 105, 210), font=font(13))
    if vp and -W < vp[0] < 2 * W and -H < vp[1] < 2 * H:
        dr.ellipse([vp[0] - 6, vp[1] - 6, vp[0] + 6, vp[1] + 6], outline=(45, 105, 210), width=2); dr.text((vp[0] + 9, vp[1] - 8), "VP", fill=(45, 105, 210), font=font(13))
    for lp in ladder_pts:
        (bu, bv), (tu, tv) = lp["base"], lp["top"]; hgt = abs(bv - tv)
        r = max(2, hgt * 0.07); lw = max(1, int(hgt / 90) + 1)
        dr.line([(bu, bv), (tu, tv + 2 * r)], fill=(205, 40, 45), width=lw)
        dr.line([(tu - r * 1.6, tv + hgt * 0.3), (tu + r * 1.6, tv + hgt * 0.3)], fill=(205, 40, 45), width=lw)
        dr.ellipse([tu - r, tv, tu + r, tv + 2 * r], outline=(205, 40, 45), width=lw)
        dr.line([(bu - r * 2, bv), (bu + r * 2, bv)], fill=(205, 40, 45), width=lw)
        dr.text((bu + 4, bv - 12), f"{lp['z_m']}m", fill=(205, 40, 45), font=font(10))
    for p in present:                                   # plane tags at the centre of each plane's largest piece
        n_, cc, st, cen = cv2.connectedComponentsWithStats((L == p).astype(np.uint8), 8)
        if n_ < 2: continue
        j = 1 + int(np.argmax(st[1:, 4])); cx, cy = cen[j]
        dr.rounded_rectangle([cx - 15, cy - 11, cx + 15, cy + 11], 5, fill=PCOL[p]); dr.text((cx - 9, cy - 8), f"P{p}", fill=(255, 255, 255), font=font(14))
    im.save(os.path.join(cd, "layout_sheet.png"))
    # 6c notan
    nimg = np.dstack([N * 255] * 3).astype(np.uint8)
    nimg = (nimg * (1 - ink[..., None] * 0.5)).astype(np.uint8)
    Image.fromarray(nimg).save(os.path.join(cd, "notan.png"))
    # 6d plane map × ground grid × sky gradient
    gs = np.zeros((H, W, 3), np.float32)
    for p in range(7): gs[L == p] = PCOL[p]
    gs = gs * 0.55 + F * 0.45
    if sky.any(): gs[sky] = F[sky]
    gg = persp[..., 3:4] * 1.4; gs = gs * (1 - np.clip(gg, 0, 1)) + 255 * np.clip(gg, 0, 1)
    gs = gs * (1 - ink[..., None] * 0.8) + 15 * ink[..., None] * 0.8
    Image.fromarray(np.clip(gs, 0, 255).astype(np.uint8)).save(os.path.join(cd, "planes_gs.png"))
    # 6e each plane alone
    tw, th = W // 4, H // 4
    strip = Image.new("RGB", (tw * 4 + 50, th * 2 + 70), (12, 14, 20)); ds = ImageDraw.Draw(strip)
    for k, p in enumerate(range(7)):
        m = L == p; tile = np.full((H, W), 245, np.uint8); tile[m] = 20
        if p == 2: tile[m] = 0
        t = Image.fromarray(cv2.resize(tile, (tw, th), interpolation=cv2.INTER_AREA)).convert("RGB")
        x, y = 10 + (k % 4) * (tw + 10), 10 + (k // 4) * (th + 30)
        strip.paste(t, (x, y + 18)); ds.text((x, y), f"P{p} {NAMES[p]} · {int(m.mean() * 100)}%", fill=PCOL[p] if p != 0 else (180, 180, 190), font=font(12))
    strip.save(os.path.join(cd, "plane_silhouettes.png"))
    # 6f consensus vote maps
    con = rgb.astype(np.float32) * 0.3
    sv, gv = PL["sky_votes"].astype(np.float32), PL["ground_votes"].astype(np.float32)
    con += np.dstack([np.zeros_like(sv), np.zeros_like(sv), sv]) * 55
    con += np.dstack([np.zeros_like(gv), gv, gv * 0.5]) * 50
    con[sky & ~A["sky"]] = (255, 255, 0); con[A["sky"] & ~sky] = (255, 0, 255)
    edge_s = cv2.morphologyEx(sky.astype(np.uint8), cv2.MORPH_GRADIENT, np.ones((3, 3))).astype(bool)
    edge_g = cv2.morphologyEx(ground.astype(np.uint8), cv2.MORPH_GRADIENT, np.ones((3, 3))).astype(bool)
    con[edge_s] = (120, 190, 255); con[edge_g] = (60, 255, 140)
    Image.fromarray(np.clip(con, 0, 255).astype(np.uint8)).save(os.path.join(cd, "consensus.png"))

    # ------------------------------------------------------------ 7. readability + suggestions
    hero_c = None
    if P2.any():
        ring = cv2.dilate(P2.astype(np.uint8), np.ones((31, 31), np.uint8)).astype(bool) & ~P2
        hero_c = round(abs(float(lum(F)[P2].mean() - lum(F)[ring].mean())), 3)
    sem_g = A["ground"]; iou_g = float((sem_g & ground).sum() / max(1, (sem_g | ground).sum()))
    dens = {f"P{p}": round(float(detail[L == p].mean()), 4) for p in present}
    sugg = []
    for mg in merges:
        sugg.append(f"{mg['planes'][0]} and {mg['planes'][1]} merge in value (Δ{mg['separation']}): push the farther one toward the haze colour, or rim-light the nearer edge.")
    if hero_c is not None and hero_c < 0.15:
        sugg.append(f"Hero barely separates from its surround (Δ{hero_c}): darken the hero mass or lighten the plane behind it; consider a rim light.")
    if MP.get("silhouette", {}).get("hero_kind") == "to_draw":
        sugg.append("P2 is empty: place the character using the red 1.7 m scale ladder on the layout sheet.")
    if (L == 0).mean() > 0.4:
        sugg.append(f"Camera mask covers {int((L == 0).mean() * 100)}% of frame: keep it very dark and simple, so it frames the action and doesn't compete with it.")
    if not ladder_pts and bool(PL["has_plane"]):
        sugg.append("No ground visible where a figure could stand: scale must come from architecture (doors, steps).")
    if not bool(PL["has_plane"]):
        sugg.append("No ground plane recovered: draw perspective by hand from vanishing points in the architecture.")
    if (sky & ~A["sky"]).sum() > 0.01 * H * W or (A["sky"] & ~sky).sum() > 0.01 * H * W:
        sugg.append("Sky consensus changed the semantic sky noticeably; check consensus.png.")
    rec = dict(id=sid, plane_values={f"P{p}": dict(source=round(orig_v[p], 3), notan=round(notan_v[p], 3)) for p in present},
               value_merges=merges, hero_contrast_flats=hero_c, ground_consensus_iou=round(iou_g, 3),
               sky_semantic_frac=round(float(A["sky"].mean()), 3), sky_final_frac=round(float(sky.mean()), 3),
               detail_density=dens, scale_ladder=len(ladder_pts), vp=vp, horizon=horizon,
               haze_rgb=[int(v) for v in haze], ink_coverage=round(float((ink > 0.5).mean()), 4),
               regions=int(nR), suggestions=sugg)
    json.dump(rec, open(os.path.join(cd, "signals.json"), "w"), indent=2)
    return rec


def main():
    ap = argparse.ArgumentParser(); ap.add_argument("--match", nargs="*"); a = ap.parse_args()
    ids = sorted(os.path.basename(os.path.dirname(os.path.dirname(p))) for p in glob.glob(os.path.join(OUT, "*", "multiplane", "planes.npz")))
    if a.match: ids = [i for i in ids if any(m in i for m in a.match)]
    for sid in ids:
        r = render(sid)
        print(f"{sid[:8]} regions={r['regions']} merges={[m['planes'] for m in r['value_merges']]} hero_c={r['hero_contrast_flats']} "
              f"groundIoU={r['ground_consensus_iou']} sky {r['sky_semantic_frac']}→{r['sky_final_frac']} ladder={r['scale_ladder']}")
    allr = {}
    for p in glob.glob(os.path.join(OUT, "*", "cartoon", "signals.json")):
        j = json.load(open(p)); allr[j["id"]] = j
    with open(os.path.join(ROOT, "shots", "cartoon_data.js"), "w") as fh:
        fh.write("window.CT = " + json.dumps(allr) + ";\n")
    print(f"wrote {len(allr)} cartoon signal records")


if __name__ == "__main__":
    main()
