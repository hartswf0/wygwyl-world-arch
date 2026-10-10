#!/usr/bin/env python3
"""
Scene program + render-and-compare solver.

One source of truth per shot: a SCENE PROGRAM = camera move + 7 multiplane planes, each a list of vector
shapes (polygon paths with holes) filled with the shot's REAL colours (flat or a 2-stop linear gradient fit
to the original pixels). Every other view is derived from it.

Loop (the image is the judge; a human/LLM judge looks at compare.jpg + cartoon.html between runs):
    seed   plane map (L) × colour clusters on a mean-shifted image → shapes
    render polygons back-to-front (P6 … P0), the same way the SVG will
    score  ΔE (colour) · SSIM of blurred luminance (value structure) · edge F (structural edges) · complexity
    refine split the worst shapes (where ΔE·√area is highest); merge similar neighbours; tune simplification
           keep a change only if  loss = fidelity + λ·complexity  goes down  (a cartoon = simplest drawing that reads)
    export scene.json · cartoon.html (SVG multiplane, camera move on twos, paint-behind, onion-skin vs original)
           · compare.jpg (original | cartoon | end of camera move | ΔE heat)

Usage: .venv-shots/bin/python shots/scene_program.py [--match id-substr ...] [--rounds 14] [--lam 0.15] [--seed semantic|colour]
"""
import argparse, glob, json, math, os, re, time
import numpy as np
import cv2
from PIL import Image, ImageDraw, ImageFont
from scipy import ndimage as ndi
from skimage.metrics import structural_similarity as ssim
from skimage.measure import label as sk_label

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, "shots", "out")
SC = 0.5                                     # scoring resolution
K_SEED = {0: 2, 1: 3, 2: 2, 3: 2, 4: 3, 5: 2, 6: 2}
INK_W = {0: 3.2, 1: 2.4, 2: 2.8, 3: 1.8, 4: 1.3, 5: 0.9, 6: 0}
CX_W = {0: 1.6, 1: 1.3, 2: 0.4, 3: 0.5, 4: 1.2, 5: 1.4, 6: 1.6}   # detail is cheap on characters, dear on environment
SEED_MODE = "semantic"


def to_lab(rgb):                             # rgb float 0..255 → Lab (L 0..100)
    return cv2.cvtColor((np.asarray(rgb, np.float32) / 255.0).reshape(-1, 1, 3) if rgb.ndim == 2 else np.asarray(rgb, np.float32) / 255.0,
                        cv2.COLOR_RGB2LAB).reshape(rgb.shape)


def font(sz):
    try: return ImageFont.truetype("/System/Library/Fonts/Supplemental/Arial.ttf", sz)
    except Exception: return ImageFont.load_default()


class Scene:
    def __init__(s, sid, eps=1.6, lam=0.15):
        s.sid = sid; s.od = os.path.join(OUT, sid); s.md = os.path.join(s.od, "multiplane")
        S = json.load(open(os.path.join(s.od, "shot.json")))
        s.MP = json.load(open(os.path.join(s.md, "multiplane.json")))
        PL = np.load(os.path.join(s.md, "planes.npz"))
        s.rgb = np.array(Image.open(os.path.join(ROOT, S["file"])).convert("RGB"))
        s.prompt = S.get("prompt", "")
        s.H, s.W = s.rgb.shape[:2]; s.L = PL["L"].astype(np.int32)
        s.eps, s.lam = eps, lam
        h, w = int(s.H * SC), int(s.W * SC); s.h, s.w = h, w
        small = cv2.resize(s.rgb, (w, h), interpolation=cv2.INTER_AREA)
        s.ref = cv2.GaussianBlur(small, (0, 0), 1.0).astype(np.float32)
        s.ref_lab = to_lab(s.ref); s.ref_lum = s.ref_lab[..., 0] / 100
        ms = cv2.pyrMeanShiftFiltering(small, 6, 18)
        g = cv2.cvtColor(ms, cv2.COLOR_RGB2GRAY); med = float(np.median(g))
        s.ref_edges = cv2.Canny(g, int(max(10, .5 * med)), int(min(255, 1.2 * med))) > 0
        s.ref_edt = ndi.distance_transform_edt(~s.ref_edges)
        s.yy, s.xx = np.mgrid[0:h, 0:w].astype(np.float32)
        s.cache = {}; s.history = []
        cam = s.MP["camera"]; s.move, s.amp, s.focus = cam["move"], float(cam.get("amplitude", .06)), cam["focus"]
        if s.amp > 1: s.amp /= (s.W if s.move == "truck" else s.H)          # truck/tilt amplitude is stored in px
        s.par = {int(p["id"][1]): min(2.5, float(p["parallax"] if p["parallax"] is not None else 0)) for p in s.MP["planes"]}
        s.par[6] = 0.0
        A = np.load(os.path.join(s.od, "arrays.npz"))
        s.seg, s.inst = A["seg"].astype(np.int32), A["masks"]
        s.seed_mode = SEED_MODE
        s.seed()
        jn = os.path.join(ROOT, "shots", "judge_notes.json")
        s.judge = (json.load(open(jn)).get(sid, {}) if os.path.exists(jn) else {})
        s.lines_all = s.find_lines(); s.line_on = set()

    # ---------------------------------------------------------------- seed
    def seed(s):
        ms = cv2.pyrMeanShiftFiltering(s.rgb, 8, 16)
        lab = to_lab(ms.astype(np.float32))
        S = np.zeros((s.H, s.W), np.int32); nxt = 1; s.plane = {}
        inst = np.zeros((s.H, s.W), np.int32)
        for i, m_ in enumerate(s.inst): inst[m_] = i + 1
        for p in range(7):
            m = s.L == p
            if m.sum() < 30: continue
            if s.seed_mode == "semantic":
                # designed masses: environment by ADE class, characters/FX by SAM instance
                tmp = np.where(m, (inst + 1) if p in (2, 3) else (s.seg + 1), 0).astype(np.int32)
            else:
                px = lab[m]; k = min(K_SEED[p], max(1, len(px) // 2000))
                if k > 1:
                    sub = px[np.random.default_rng(0).choice(len(px), min(len(px), 20000), replace=False)]
                    _, _, cen = cv2.kmeans(sub, k, None, (cv2.TERM_CRITERIA_EPS + cv2.TERM_CRITERIA_MAX_ITER, 30, .5), 3, cv2.KMEANS_PP_CENTERS)
                    cl = np.argmin(((px[:, None] - cen[None]) ** 2).sum(-1), 1)
                else: cl = np.zeros(len(px), int)
                tmp = np.zeros((s.H, s.W), np.int32); tmp[m] = cl + 1
            comp = sk_label(tmp, background=0, connectivity=1)
            minA = 40 if p in (2, 3) else 0.0012 * s.H * s.W
            sizes = np.bincount(comp.ravel())
            small = m & (sizes[comp] < minA)
            if small.any() and (m & ~small).any():
                _, (iy, ix) = ndi.distance_transform_edt(small | ~m, return_indices=True)
                comp = np.where(small, comp[iy, ix], comp)
            for c in np.unique(comp[m]):
                S[m & (comp == c)] = nxt; s.plane[nxt] = p; nxt += 1
        s.S = S; s.nxt = nxt
        s.objs = ndi.find_objects(s.S)

    # ---------------------------------------------------------------- shape geometry + colour
    def mask_of(s, lbl, S=None):
        S = s.S if S is None else S
        if S is s.S and lbl - 1 >= len(s.objs): s.objs = list(ndi.find_objects(s.S)) + [None] * max(0, s.nxt - 1 - int(s.S.max()))
        sl = ndi.find_objects((S == lbl).astype(np.int32))[0] if S is not s.S else (s.objs[lbl - 1] if lbl - 1 < len(s.objs) else None)
        if sl is None: return None, None
        y0, y1 = max(0, sl[0].start - 4), min(S.shape[0], sl[0].stop + 4)
        x0, x1 = max(0, sl[1].start - 4), min(S.shape[1], sl[1].stop + 4)
        return S[y0:y1, x0:x1] == lbl, (y0, x0)

    def geom(s, lbl):
        """contours (full-res px, holes included, simplified) + colour model; cached until the shape changes."""
        if lbl in s.cache: return s.cache[lbl]
        m, (y0, x0) = s.mask_of(lbl)
        mm = cv2.dilate(m.astype(np.uint8), np.ones((5, 5), np.uint8))       # 2 px overlap hides seams
        sm = float(s.judge.get("smooth", 3.0)) * (0.35 if s.plane[lbl] in (2, 3) else 1.0)
        if sm > 0.5:                                                          # drawn edge, not torn paper
            pad = int(3 * sm) + 2; big = np.pad(mm, pad).astype(np.float32)
            big = cv2.GaussianBlur(big, (0, 0), sm) > 0.5
            mm = big[pad:-pad, pad:-pad].astype(np.uint8) | (cv2.erode(mm, np.ones((3, 3), np.uint8)))
        cs, _ = cv2.findContours(mm, cv2.RETR_CCOMP, cv2.CHAIN_APPROX_NONE)
        polys = []
        for c in cs:
            if cv2.contourArea(c) < 6: continue
            a = cv2.approxPolyDP(c, s.eps, True)
            if len(a) >= 3: polys.append(a[:, 0, :].astype(np.float32) + [x0, y0])
        ys, xs = np.nonzero(m); ys = ys + y0; xs = xs + x0
        if len(ys) > 6000:
            i = np.random.default_rng(lbl).choice(len(ys), 6000, replace=False); ys, xs = ys[i], xs[i]
        col = s.rgb[ys, xs].astype(np.float32)
        cx, cy = float(xs.mean()), float(ys.mean())
        X = np.stack([np.ones(len(xs)), xs - cx, ys - cy], 1).astype(np.float32)
        coef, *_ = np.linalg.lstsq(X, col, rcond=None)                        # rgb = a + B·[dx,dy]
        a, B = coef[0], coef[1:].T                                            # B: 3×2
        U, Sg, Vt = np.linalg.svd(B); d = Vt[0]; k = B @ d                    # rank-1 gradient direction
        t = (xs - cx) * d[0] + (ys - cy) * d[1]; t0, t1 = np.percentile(t, [2, 98]) if len(t) > 20 else (0, 0)
        grad = float(np.linalg.norm(k) * (t1 - t0)) > 7 and len(xs) > 400
        if not grad: a = col.mean(0); k = np.zeros(3, np.float32)
        g = dict(polys=polys, a=a, k=k, d=d, c=(cx, cy), t=(float(t0), float(t1)), grad=bool(grad), area=int(m.sum()))
        s.cache[lbl] = g; return g

    def order(s):
        labels = [l for l in s.plane if l - 1 < len(s.objs) and s.objs[l - 1] is not None]
        return sorted(labels, key=lambda l: (-s.plane[l], -s.geom(l)["area"]))

    def fill_shape(s, img, g, polys, scale):
        pts = [np.round(p * scale * 16).astype(np.int32) for p in polys]
        if not pts: return
        hh, ww = img.shape[:2]
        if not g["grad"]:
            cv2.fillPoly(img, pts, tuple(float(v) for v in np.clip(g["a"], 0, 255)), cv2.LINE_AA, 4); return
        m = np.zeros((hh, ww), np.uint8); cv2.fillPoly(m, pts, 1, cv2.LINE_8, 4); sel = m > 0
        cx, cy = g["c"]; t = ((s_xx(ww, hh)[0][sel] / scale - cx) * g["d"][0] + (s_xx(ww, hh)[1][sel] / scale - cy) * g["d"][1])
        t = np.clip(t, *g["t"]); img[sel] = np.clip(g["a"][None] + t[:, None] * g["k"][None], 0, 255)

    def find_lines(s):
        """long straight structure lines (steps, corridor edges, cornices) inside environment planes, coloured
        from the darker side of the edge in the real image."""
        g = cv2.cvtColor(cv2.pyrMeanShiftFiltering(s.rgb, 6, 14), cv2.COLOR_RGB2GRAY)
        segs = cv2.createLineSegmentDetector().detect(g)[0]
        out = []
        if segs is None: return out
        lab = to_lab(s.rgb.astype(np.float32))
        for x1, y1, x2, y2 in np.asarray(segs).reshape(-1, 4):
            ln = math.hypot(x2 - x1, y2 - y1)
            if ln < 0.035 * s.W: continue
            mx, my = (x1 + x2) / 2, (y1 + y2) / 2; p = int(s.L[int(my), int(mx)])
            if p not in (0, 1, 4, 5): continue
            nx, ny = -(y2 - y1) / ln, (x2 - x1) / ln
            ts = np.linspace(0.1, 0.9, 9)
            xs, ys = x1 + (x2 - x1) * ts, y1 + (y2 - y1) * ts
            def samp(o):
                xx = np.clip((xs + nx * o).astype(int), 0, s.W - 1); yy = np.clip((ys + ny * o).astype(int), 0, s.H - 1)
                return xx, yy
            (ax, ay), (bx, by) = samp(3.5), samp(-3.5)
            if not ((s.L[ay, ax] == p).all() and (s.L[by, bx] == p).all()): continue   # plane edges are the shapes' job
            la, lb = lab[ay, ax, 0].mean(), lab[by, bx, 0].mean()
            if abs(la - lb) < 7: continue
            dark = s.rgb[ay, ax].mean(0) if la < lb else s.rgb[by, bx].mean(0)
            fx, fy = s.focus
            fw = math.exp(-(((mx - fx) / (0.3 * s.W)) ** 2 + ((my - fy) / (0.35 * s.H)) ** 2))
            if fw < float(s.judge.get("line_focal_min", 0.25)): continue      # layout lines belong where the eye goes
            out.append(dict(p=p, pts=np.array([[x1, y1], [x2, y2]], np.float32), col=(dark * 0.6).astype(float).tolist(),
                            w=max(1.6, INK_W[p] * 1.1), score=ln * abs(la - lb) * max(fw, 0.2)))
        out.sort(key=lambda d: -d["score"])
        return out[:90]

    def render(s, scale=SC, xform=None, polys_of=None):
        hh, ww = int(s.H * scale), int(s.W * scale)
        img = np.zeros((hh, ww, 3), np.float32)
        lines = [s.lines_all[i] for i in sorted(s.line_on)]
        def draw_lines(p):
            for d in lines:
                if d["p"] != p: continue
                pts = xform(p, d["pts"]) if xform else d["pts"]
                a, b = (np.round(pts * scale * 16).astype(int)).tolist()
                cv2.line(img, tuple(a), tuple(b), d["col"], max(1, int(round(d["w"] * scale))), cv2.LINE_AA, 4)
        cur_p = None
        for l in s.order():
            if cur_p is not None and s.plane[l] != cur_p: draw_lines(cur_p)
            cur_p = s.plane[l]
            g = s.geom(l); polys = polys_of(l) if polys_of else g["polys"]
            if xform: polys = [xform(s.plane[l], p) for p in polys]
            s.fill_shape(img, g, polys, scale)
        if cur_p is not None: draw_lines(cur_p)
        return img

    # ---------------------------------------------------------------- score
    def score(s, img=None):
        img = s.render() if img is None else img
        lab = to_lab(img)
        dE = np.linalg.norm(lab - s.ref_lab, axis=2)
        val = ssim(cv2.GaussianBlur(lab[..., 0] / 100, (0, 0), 3), cv2.GaussianBlur(s.ref_lum, (0, 0), 3), data_range=1.0)
        g = cv2.cvtColor(np.clip(img, 0, 255).astype(np.uint8), cv2.COLOR_RGB2GRAY)
        re = cv2.Canny(g, 12, 30) > 0
        prec = float((s.ref_edt[re] <= 2).mean()) if re.any() else 0
        rdt = ndi.distance_transform_edt(~re) if re.any() else np.full(re.shape, 99.0)
        rec = float((rdt[s.ref_edges] <= 2).mean()) if s.ref_edges.any() else 0
        ef = 2 * prec * rec / max(prec + rec, 1e-6)
        labels = s.order(); geoms = [s.geom(l) for l in labels]
        verts = sum(len(p) for g_ in geoms for p in g_["polys"]); nsh = len(geoms)
        cx = sum(CX_W[s.plane[l]] * (sum(len(p) for p in g_["polys"]) + 30) for l, g_ in zip(labels, geoms)) / 1000
        nl = len(s.line_on); cx += nl * 14 / 1000
        loss = float(float(dE.mean()) / 10 + (1 - val) * 2 + (1 - ef) + s.lam * cx)
        return dict(loss=round(loss, 4), dE=round(float(dE.mean()), 2), value_ssim=round(float(val), 3), edge_f=round(ef, 3),
                    shapes=nsh, verts=int(verts), lines=nl), dE

    # ---------------------------------------------------------------- refine
    def _commit(s, S_new, changed):
        old = (s.S, s.objs, dict(s.plane), {l: s.cache[l] for l in changed if l in s.cache})
        s.S = S_new; s.objs = ndi.find_objects(s.S)
        if len(s.objs) < s.nxt - 1: s.objs = list(s.objs) + [None] * (s.nxt - 1 - len(s.objs))
        for l in changed: s.cache.pop(l, None)
        for l in list(s.plane):
            if l - 1 >= len(s.objs) or s.objs[l - 1] is None: s.plane.pop(l)
        return old

    def _revert(s, old):
        s.S, s.objs, s.plane, cached = old
        for l, g in cached.items(): s.cache[l] = g

    def try_split(s, lbl):
        m, off = s.mask_of(lbl)
        if m is None: return None
        y0, x0 = off; ys, xs = np.nonzero(m)
        if len(ys) < 300: return None
        lab = to_lab(s.rgb[ys + y0, xs + x0].astype(np.float32))
        span = max(m.shape) or 1
        f = np.concatenate([lab, np.stack([xs, ys], 1) * (18.0 / span)], 1).astype(np.float32)
        sub = f[np.random.default_rng(lbl).choice(len(f), min(len(f), 8000), replace=False)]
        _, _, cen = cv2.kmeans(sub, 2, None, (cv2.TERM_CRITERIA_EPS + cv2.TERM_CRITERIA_MAX_ITER, 25, .5), 2, cv2.KMEANS_PP_CENTERS)
        cl = np.argmin(((f[:, None] - cen[None]) ** 2).sum(-1), 1)
        tmp = np.zeros(m.shape, np.int32); tmp[ys, xs] = cl + 1
        comp = sk_label(tmp, background=0, connectivity=1)
        sizes = np.bincount(comp.ravel()); minA = 40 if s.plane[lbl] in (2, 3) else 0.0006 * s.H * s.W
        small = m & (sizes[comp] < minA)
        if small.all() or (~small & m).sum() == 0: return None
        if small.any():
            _, (iy, ix) = ndi.distance_transform_edt(small | ~m, return_indices=True); comp = np.where(small, comp[iy, ix], comp)
        ids = [c for c in np.unique(comp[m]) if c]
        if len(ids) < 2: return None
        S_new = s.S.copy(); sub_S = S_new[y0:y0 + m.shape[0], x0:x0 + m.shape[1]]
        new = []
        for c in ids[1:]:
            sub_S[m & (comp == c)] = s.nxt; s.plane[s.nxt] = s.plane[lbl]; new.append(s.nxt); s.nxt += 1
        return S_new, [lbl] + new

    def neighbours(s):
        a = np.concatenate([s.S[:, :-1].ravel(), s.S[:-1, :].ravel()]); b = np.concatenate([s.S[:, 1:].ravel(), s.S[1:, :].ravel()])
        d = a != b; pairs = np.unique(np.stack([np.minimum(a[d], b[d]), np.maximum(a[d], b[d])], 1), axis=0)
        return [(int(x), int(y)) for x, y in pairs if x in s.plane and y in s.plane and s.plane[x] == s.plane[y]]

    def refine(s, rounds=14, log=print):
        cur, dE = s.score(); s.history.append(dict(round=0, op="seed", **cur)); log(f"  seed  {cur}")
        best_eps = s.eps
        for e in (1.0, 2.4, 3.5):                                         # global simplification tolerance
            s.eps = e; s.cache.clear(); sc, _ = s.score()
            if sc["loss"] < cur["loss"]: cur, best_eps = sc, e
        s.eps = best_eps; s.cache.clear(); cur, dE = s.score()
        s.history.append(dict(round=0, op=f"eps={best_eps}", **cur))
        fx, fy = s.focus                                                  # detail goes where the director looks
        focal = 0.35 + np.exp(-(((s.xx / SC - fx) / (0.35 * s.W)) ** 2 + ((s.yy / SC - fy) / (0.45 * s.H)) ** 2))
        tried = set(); line_next = 0
        for r in range(1, rounds + 1):
            improved = 0
            # structure lines, a batch at a time (strongest first). Metric-only: keep if loss drops.
            # Judge-requested (judge_notes.json lines=true): keep while total cost stays within the style budget.
            want = bool(s.judge.get("lines")); budget = float(s.judge.get("style_budget", 0.03))
            if r == 1: s.base_loss = cur["loss"]
            cap = int(s.judge.get("line_max", 60))
            while line_next < len(s.lines_all) and len(s.line_on) < cap and line_next < 120:
                batch = set(range(line_next, min(line_next + 6, len(s.lines_all)))); line_next += 6
                s.line_on |= batch; sc, dE2 = s.score()
                ok = sc["loss"] < cur["loss"] - 1e-4 or (want and sc["loss"] <= s.base_loss * (1 + budget))
                if ok: cur, dE = sc, dE2; improved += 1; s.history.append(dict(round=r, op=f"+lines {min(batch)}-{max(batch)}{' (judge)' if want else ''}", **cur))
                else: s.line_on -= batch
                break                                                     # one batch per round, interleaved with shape edits
            # split where it's wrong (focal-weighted), skipping shapes that already failed
            lblmap = cv2.resize(s.S, (s.w, s.h), interpolation=cv2.INTER_NEAREST)
            labs = list(s.plane)
            err = ndi.mean(dE * focal, lblmap, index=labs); area = ndi.sum(np.ones_like(dE), lblmap, index=labs)
            pri = [l for l, _ in sorted(zip(labs, np.nan_to_num(err) * np.sqrt(area)), key=lambda t: -t[1]) if l not in tried][:8]
            for lbl in pri:
                if lbl not in s.plane: continue
                res = s.try_split(lbl)
                if not res: tried.add(lbl); continue
                old = s._commit(*res); sc, dE2 = s.score()
                if sc["loss"] < cur["loss"] - 1e-4: cur, dE = sc, dE2; improved += 1; s.history.append(dict(round=r, op=f"split {lbl}", **cur))
                else:
                    for l in res[1][1:]: s.plane.pop(l, None)
                    s._revert(old); tried.add(lbl)
            # merge where it's redundant
            cand = []
            for a_, b_ in s.neighbours():
                ga, gb = s.geom(a_), s.geom(b_)
                lab2 = to_lab(np.array([[ga["a"], gb["a"]]], np.float32))[0]
                cand.append((float(np.linalg.norm(lab2[0] - lab2[1])), a_, b_))
            for dc, a_, b_ in sorted(cand)[:6]:
                if dc > 10 or a_ not in s.plane or b_ not in s.plane or (a_, b_) in tried: continue
                S_new = np.where(s.S == b_, a_, s.S); keep_b = s.plane[b_]
                old = s._commit(S_new, [a_, b_]); sc, dE2 = s.score()
                if sc["loss"] < cur["loss"] - 1e-4: cur, dE = sc, dE2; improved += 1; s.history.append(dict(round=r, op=f"merge {b_}→{a_}", **cur))
                else: s._revert(old); s.plane[b_] = keep_b; tried.add((a_, b_))
            log(f"  r{r:02d}  {cur}  (+{improved})")
            if not improved and (line_next >= min(120, len(s.lines_all)) or len(s.line_on) >= int(s.judge.get("line_max", 60))): break
        s.final, s.dE = cur, dE
        return cur

    # ---------------------------------------------------------------- export
    def xform_fn(s, e):
        fx, fy = s.focus
        def f(p, pts):
            k = s.par.get(p, 0) * e; pts = pts.copy()
            if s.move in ("push", "crane_push"):
                sc = 1 + s.amp * k; pts = (pts - [fx, fy]) * sc + [fx, fy]
            if s.move == "crane_push": pts[:, 1] += s.amp * s.H * .5 * k
            if s.move == "truck": pts[:, 0] -= s.amp * s.W * k
            if s.move == "tilt_up": pts[:, 1] += s.amp * s.H * k
            return pts
        return f

    def paint_behind(s):
        """extend every plane under the nearer planes (+frame overscan) so the camera move never reveals holes."""
        band = int(math.ceil(s.amp * max(s.W, s.H) * 2.6)) + 10; pad = band
        planeimg = np.zeros_like(s.S); 
        for l, p in s.plane.items(): planeimg[s.S == l] = p
        Sp = np.pad(s.S, pad, mode="edge"); Pp = np.pad(planeimg, pad, mode="edge")
        present = sorted(set(s.plane.values())); far = max(p for p in present if p != 2) if present else 6
        ext = {}
        for p in present:
            own = np.where(Pp == p, Sp, 0)
            if not own.any(): continue
            dist, (iy, ix) = ndi.distance_transform_edt(own == 0, return_indices=True)
            grow = (Pp < p) | (Pp == p) if p != far else np.ones_like(own, bool)
            grow &= (dist <= band) if p not in (far, 6) else True
            if p in (2, 3): grow = own > 0                                    # characters don't get painted behind
            ext[p] = np.where(grow, own[iy, ix], 0)
        def polys_of(lbl):
            p = s.plane[lbl]; E = ext.get(p)
            if E is None: return s.geom(lbl)["polys"]
            m = (E == lbl).astype(np.uint8)
            if not m.any(): return s.geom(lbl)["polys"]
            m = cv2.dilate(m, np.ones((5, 5), np.uint8))
            cs, _ = cv2.findContours(m, cv2.RETR_CCOMP, cv2.CHAIN_APPROX_NONE)
            out = []
            for c in cs:
                if cv2.contourArea(c) < 6: continue
                a = cv2.approxPolyDP(c, max(s.eps, 1.5), True)
                if len(a) >= 3: out.append(a[:, 0, :].astype(np.float32) - pad)
            return out
        return polys_of

    def export(s):
        pd = os.path.join(s.od, "program"); os.makedirs(pd, exist_ok=True)
        polys_of = s.paint_behind()
        hx = lambda c: "#%02x%02x%02x" % tuple(int(v) for v in np.clip(c, 0, 255))
        defs, groups, planes_json = [], {p: [] for p in range(7)}, {p: [] for p in range(7)}
        for l in s.order():
            g = s.geom(l); p = s.plane[l]; polys = polys_of(l)
            if not polys: continue
            d = " ".join("M" + " L".join(f"{x:.1f} {y:.1f}" for x, y in poly) + "Z" for poly in polys)
            if g["grad"]:
                (cx, cy), (t0, t1), dv = g["c"], g["t"], g["d"]
                gid = f"g{l}"; c0, c1 = g["a"] + g["k"] * t0, g["a"] + g["k"] * t1
                defs.append(f'<linearGradient id="{gid}" gradientUnits="userSpaceOnUse" x1="{cx + dv[0] * t0:.1f}" y1="{cy + dv[1] * t0:.1f}" '
                            f'x2="{cx + dv[0] * t1:.1f}" y2="{cy + dv[1] * t1:.1f}"><stop offset="0" stop-color="{hx(c0)}"/><stop offset="1" stop-color="{hx(c1)}"/></linearGradient>')
                fill = f"url(#{gid})"; ink = hx((c0 + c1) / 2 * .32)
            else: fill = hx(g["a"]); ink = hx(g["a"] * .32)
            groups[p].append(f'<path d="{d}" fill="{fill}" stroke="{ink}" stroke-width="{INK_W[p]}" vector-effect="non-scaling-stroke"/>')
            planes_json[p].append(dict(id=int(l), d=d, fill=fill if not g["grad"] else dict(c0=hx(g["a"] + g["k"] * g["t"][0]), c1=hx(g["a"] + g["k"] * g["t"][1])), area=g["area"]))
        mp = {int(p["id"][1]): p for p in s.MP["planes"]}
        if s.line_on:
            for d_ in [s.lines_all[i] for i in sorted(s.line_on)]:
                (x1, y1), (x2, y2) = d_["pts"].tolist()
                groups[d_["p"]].append(f'<line class="sl" x1="{x1:.1f}" y1="{y1:.1f}" x2="{x2:.1f}" y2="{y2:.1f}" stroke="{hx(d_["col"])}" stroke-width="{d_["w"]:.1f}" stroke-linecap="round"/>')
        svg_groups = "\n".join(f'<g id="P{p}" class="plane" data-par="{s.par.get(p, 0):.3f}" data-name="{mp[p]["name"] if p in mp else ""}">{"".join(groups[p])}</g>'
                               for p in range(6, -1, -1) if groups[p])
        frames = int(s.MP.get("duration_frames") or 96)
        # perceptual stats per plane → sound score (planes = drones, characters = plucks, lines = rhythm)
        planeimg = np.zeros_like(s.S)
        for l, p in s.plane.items(): planeimg[s.S == l] = p
        pstats = []
        for p in range(7):
            m = planeimg == p
            if m.mean() < 0.003: continue
            ys, xs = np.nonzero(m); col = s.rgb[m].mean(0)
            pstats.append(dict(p=p, area=round(float(m.mean()), 3), cx=round(float(xs.mean() / s.W), 3), cy=round(float(ys.mean() / s.H), 3),
                               rgb=[int(v) for v in col], par=round(s.par.get(p, 0), 3),
                               z=next((q["z_median_m"] for q in s.MP["planes"] if q["id"] == f"P{p}"), None)))
        chars = []
        for l in s.order():
            if s.plane[l] != 2: continue
            g = s.geom(l); chars.append(dict(x=round(g["c"][0] / s.W, 3), y=round(g["c"][1] / s.H, 3), a=g["area"]))
        chars = sorted(chars, key=lambda c: -c["a"])[:8]
        water = bool(re.search(r"water|rain|drip|pool|sea|river|wet|tide|bay", s.prompt, re.I))
        html = HTML.replace("__W__", str(s.W)).replace("__H__", str(s.H)).replace("__DEFS__", "".join(defs)).replace("__GROUPS__", svg_groups) \
            .replace("__CFG__", json.dumps(dict(move=s.move, amp=s.amp, focus=s.focus, frames=frames, title=s.MP.get("title") or s.sid[:8],
                                                action=s.MP.get("action") or "", score=s.final, planes=pstats, chars=chars,
                                                lines=len(s.line_on), water=water, beats=s.MP.get("beats") or [])))
        open(os.path.join(pd, "cartoon.html"), "w").write(html)
        json.dump(dict(id=s.sid, W=s.W, H=s.H, camera=dict(move=s.move, amplitude=s.amp, focus=s.focus, frames=frames),
                       parallax={f"P{p}": v for p, v in s.par.items()}, eps=s.eps, lam=s.lam, score=s.final, history=s.history,
                       planes={f"P{p}": v for p, v in planes_json.items() if v}), open(os.path.join(pd, "scene.json"), "w"))
        # compare sheet for the judge
        f0 = s.render(); f1 = s.render(xform=s.xform_fn(1.0), polys_of=polys_of)
        Image.fromarray(np.clip(s.render(scale=1.0), 0, 255).astype(np.uint8)).save(os.path.join(pd, "frame0.png"))
        heat = cv2.applyColorMap(np.clip(s.dE / 30 * 255, 0, 255).astype(np.uint8), cv2.COLORMAP_INFERNO)[..., ::-1]
        tiles = [s.ref, f0, f1, heat.astype(np.float32)]; names = ["original", "cartoon (program)", f"end of {s.move}", "ΔE error"]
        sheet = Image.new("RGB", (s.w * 2 + 6, s.h * 2 + 6 + 44), (10, 12, 16)); dr = ImageDraw.Draw(sheet)
        for i, (t, n) in enumerate(zip(tiles, names)):
            x, y = (i % 2) * (s.w + 6), (i // 2) * (s.h + 6) + 44
            sheet.paste(Image.fromarray(np.clip(t, 0, 255).astype(np.uint8)), (x, y)); dr.text((x + 8, y + 6), n, fill=(255, 255, 255), font=font(14))
        sc = s.final
        dr.text((8, 12), f"{s.MP.get('title') or s.sid[:8]}   ΔE {sc['dE']} · value SSIM {sc['value_ssim']} · edge F {sc['edge_f']} · {sc['shapes']} shapes · {sc['verts']} verts · loss {sc['loss']}",
                fill=(242, 165, 65), font=font(15))
        sheet.save(os.path.join(pd, "compare.jpg"), quality=88)
        return pd


_GRID = {}
def s_xx(w, h):
    if (w, h) not in _GRID: _GRID[(w, h)] = np.mgrid[0:h, 0:w][::-1].astype(np.float32)
    return _GRID[(w, h)]


HTML = r"""<!doctype html><html lang="en"><head><meta charset="utf-8"><title>Cartoon · scene program</title>
<meta name="viewport" content="width=device-width,initial-scale=1">
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;600&family=JetBrains+Mono&display=swap" rel="stylesheet">
<style>
html,body{margin:0;height:100%;background:#07090d;color:#e8ecf3;font:13px Inter,sans-serif;overflow:hidden}
.wrap{position:absolute;inset:0 0 46px 0;display:grid;place-items:center}
.frame{position:relative;max-width:100%;max-height:100%;aspect-ratio:__W__/__H__;height:100%;overflow:hidden;box-shadow:0 20px 80px rgba(0,0,0,.6)}
svg,.ref{position:absolute;inset:0;width:100%;height:100%}
.ref{object-fit:fill;opacity:0;pointer-events:none}
svg.noink path{stroke:none}
.bar{position:absolute;left:0;right:0;bottom:0;height:46px;display:flex;gap:14px;align-items:center;padding:0 14px;background:rgba(14,18,26,.92);border-top:1px solid #1b2230}
.bar b{color:#f2a541}.bar label{display:flex;gap:6px;align-items:center;color:#8a95a8}
.bar button{background:#1a2130;color:#e8ecf3;border:1px solid #2a3446;border-radius:7px;padding:5px 11px;cursor:pointer;font:inherit}
.mono{font-family:'JetBrains Mono',monospace;color:#8a95a8}
</style></head><body>
<div class="wrap"><div class="frame">
<svg id="svg" class="noink" viewBox="0 0 __W__ __H__" preserveAspectRatio="none" shape-rendering="geometricPrecision"><defs>__DEFS__</defs>__GROUPS__</svg>
<img class="ref" id="ref" src="../image.jpg" alt="original"></div></div>
<div class="bar"><button id="play">❚❚</button><span class="mono" id="fr">f000</span>
<label>onion-skin original <input type="range" id="onion" min="0" max="100" value="0"></label>
<label><input type="checkbox" id="ink"> ink</label><label><input type="checkbox" id="explode"> explode planes</label>
<button id="hear" title="generate a sound score from the scene program">🔊 hear it</button>
<span class="mono" id="sc"></span><span style="margin-left:auto"><b id="tt"></b></span></div>
<script>
const C=__CFG__,W=__W__,H=__H__,G=[...document.querySelectorAll('.plane')];let f=0,play=true,dir=1;
document.getElementById('tt').textContent=C.title+' · '+C.move.replace('_',' ');
document.getElementById('sc').textContent=`ΔE ${C.score.dE} · value ${C.score.value_ssim} · edges ${C.score.edge_f} · ${C.score.shapes} shapes`;
const ease=u=>u<.5?2*u*u:1-Math.pow(-2*u+2,2)/2;
function pose(){const N=C.frames,u=f/N,e=ease(u),[fx,fy]=C.focus,ex=document.getElementById('explode').checked;
 G.forEach((g,i)=>{const k=+g.dataset.par*e;let t='';
  if(C.move==='push'||C.move==='crane_push'){const s=1+C.amp*k;t=`translate(${fx} ${fy}) scale(${s}) translate(${-fx} ${-fy})`}
  if(C.move==='crane_push')t=`translate(0 ${C.amp*H*.5*k}) `+t;
  if(C.move==='truck')t=`translate(${-C.amp*W*k} 0)`;
  if(C.move==='tilt_up')t=`translate(0 ${C.amp*H*k})`;
  if(ex)t=`translate(${(i-G.length/2)*W*.012} ${(i-G.length/2)*-H*.03}) `+t;
  g.setAttribute('transform',t)});
 document.getElementById('fr').textContent='f'+String(f).padStart(3,'0')}
setInterval(()=>{if(!play)return;f+=2*dir;if(f>=C.frames){f=C.frames;dir=-1}if(f<=0){f=0;dir=1}pose()},1000/12); // on twos @24fps
document.getElementById('play').onclick=e=>{play=!play;e.target.textContent=play?'❚❚':'▶'};
document.getElementById('onion').oninput=e=>document.getElementById('ref').style.opacity=e.target.value/100;
document.getElementById('ink').onchange=e=>document.getElementById('svg').classList.toggle('noink',!e.target.checked);
document.getElementById('explode').onchange=pose;pose();
// ---------------------------------------------------------------- hear the scene (sonification of the scene program)
let AC=null,SND=null;
const PENTA=[0,2,4,7,9,12,14,16,19,21,24];
const hz=(base,step)=>base*Math.pow(2,PENTA[Math.max(0,Math.min(PENTA.length-1,step))]/12);
function lumOf(c){return (0.2126*c[0]+0.7152*c[1]+0.0722*c[2])/255}
function warmth(c){return (c[0]-c[2])/255}
function startSound(){
  AC=new (window.AudioContext||window.webkitAudioContext)();const t0=AC.currentTime;
  const master=AC.createGain();master.gain.value=0;master.gain.linearRampToValueAtTime(.9,t0+1.5);
  const tone=AC.createBiquadFilter();tone.type='lowpass';tone.frequency.value=2200;
  // room: enclosure (camera mask + foreground coverage) = longer, darker reverb
  const encl=C.planes.filter(p=>p.p<=1).reduce((a,p)=>a+p.area,0),sky=(C.planes.find(p=>p.p===6)||{area:0}).area;
  const len=1.2+3.5*Math.min(1,encl*1.4)-1.0*sky,rv=AC.createConvolver(),ir=AC.createBuffer(2,AC.sampleRate*len,AC.sampleRate);
  for(let ch=0;ch<2;ch++){const d=ir.getChannelData(ch);for(let i=0;i<d.length;i++)d[i]=(Math.random()*2-1)*Math.pow(1-i/d.length,2.2+2*sky)}
  rv.buffer=ir;const wet=AC.createGain();wet.gain.value=.35+.4*encl;
  tone.connect(master);tone.connect(rv);rv.connect(wet);wet.connect(master);master.connect(AC.destination);
  const voices=[];
  // planes → drones: far = low, near = high; warm colour → major third, cool → minor; brightness → filter
  const order=[6,5,4,3,1,0];
  C.planes.filter(p=>p.p!==2).forEach(p=>{
    const pan=AC.createStereoPanner();pan.pan.value=Math.max(-1,Math.min(1,p.cx*2-1));
    const g=AC.createGain();g.gain.value=Math.min(.22,.05+p.area*.35)*(p.p===0?.6:1);
    const f=AC.createBiquadFilter();f.type='lowpass';f.frequency.value=180+3200*Math.pow(lumOf(p.rgb),1.3);f.Q.value=.7;
    if(p.p===6){ // sky = air: filtered noise, brighter sky = higher air
      const nb=AC.createBuffer(1,AC.sampleRate*2,AC.sampleRate),d=nb.getChannelData(0);for(let i=0;i<d.length;i++)d[i]=Math.random()*2-1;
      const n=AC.createBufferSource();n.buffer=nb;n.loop=true;const bp=AC.createBiquadFilter();bp.type='bandpass';bp.frequency.value=400+3000*lumOf(p.rgb);bp.Q.value=.8;
      n.connect(bp);bp.connect(g);g.gain.value*=.8;n.start();
    }else{
      const base=55,step=order.indexOf(p.p)*2,fr=hz(base,step);
      [[fr,'sawtooth',1],[fr*(warmth(p.rgb)>0?1.26:1.19),'triangle',.6],[fr*1.003,'sine',.8]].forEach(([q,type,a])=>{
        const o=AC.createOscillator();o.type=type;o.frequency.value=q;const og=AC.createGain();og.gain.value=a*.33;
        const lfo=AC.createOscillator(),lg=AC.createGain();lfo.frequency.value=.05+.15*Math.random();lg.gain.value=q*.004;lfo.connect(lg);lg.connect(o.frequency);lfo.start();
        o.connect(og);og.connect(f);o.start();voices.push(o)});
    }
    f.connect(g);g.connect(pan);pan.connect(tone);voices.push({pan,base:pan.pan.value,par:p.par});
  });
  SND={master,tone,voices,lastBeat:-1,lastTick:-1,encl};
  // water → drips at random
  if(C.water){(function drip(){if(!AC)return;const t=AC.currentTime,o=AC.createOscillator(),g=AC.createGain(),pn=AC.createStereoPanner();
    o.type='sine';const f0=900+Math.random()*1400;o.frequency.setValueAtTime(f0,t);o.frequency.exponentialRampToValueAtTime(f0*.45,t+.09);
    g.gain.setValueAtTime(.0001,t);g.gain.exponentialRampToValueAtTime(.12,t+.005);g.gain.exponentialRampToValueAtTime(.0001,t+.18);
    pn.pan.value=Math.random()*2-1;o.connect(g);g.connect(pn);pn.connect(tone);o.start(t);o.stop(t+.2);setTimeout(drip,250+Math.random()*1300)})()}
}
function pluck(freq,pan,dur=.5,vol=.18){const t=AC.currentTime,o=AC.createOscillator(),g=AC.createGain(),p=AC.createStereoPanner();
  o.type='triangle';o.frequency.value=freq;p.pan.value=pan;g.gain.setValueAtTime(.0001,t);g.gain.exponentialRampToValueAtTime(vol,t+.008);g.gain.exponentialRampToValueAtTime(.0001,t+dur);
  o.connect(g);g.connect(p);p.connect(SND.tone);o.start(t);o.stop(t+dur+.05)}
function tick(){const t=AC.currentTime,b=AC.createBuffer(1,AC.sampleRate*.03,AC.sampleRate),d=b.getChannelData(0);for(let i=0;i<d.length;i++)d[i]=(Math.random()*2-1)*(1-i/d.length);
  const s=AC.createBufferSource(),h=AC.createBiquadFilter(),g=AC.createGain();s.buffer=b;h.type='highpass';h.frequency.value=6000;g.gain.value=.05;s.connect(h);h.connect(g);g.connect(SND.tone);s.start(t)}
function soundFrame(){if(!SND)return;const e=ease(f/C.frames),t=AC.currentTime;
  // camera: push opens the filter (closer = brighter); truck sweeps the stereo field by parallax; tilt lifts brightness
  if(C.move==='push'||C.move==='crane_push')SND.tone.frequency.setTargetAtTime(1400+3200*e,t,.2);
  if(C.move==='tilt_up')SND.tone.frequency.setTargetAtTime(1800+2000*e,t,.2);
  if(C.move==='truck')SND.voices.forEach(v=>{if(v.pan)v.pan.pan.setTargetAtTime(Math.max(-1,Math.min(1,v.base-1.2*C.amp*10*v.par*e)),t,.2)});
  // characters pluck every 12 frames (half-second on twos), cycling through figures; height → pitch, x → pan
  const beat=Math.floor(f/12);if(beat!==SND.lastBeat&&C.chars.length){SND.lastBeat=beat;const c=C.chars[beat%C.chars.length];
    pluck(hz(220,Math.round((1-c.y)*8)),c.x*2-1);if(navigator.vibrate)navigator.vibrate(12)}
  // structure lines → rhythmic texture: more lines = denser ticks
  const every=C.lines>24?4:C.lines>8?6:C.lines>0?12:0,tk=every?Math.floor(f/every):-1;if(every&&tk!==SND.lastTick){SND.lastTick=tk;tick()}
}
setInterval(()=>{if(play)soundFrame()},1000/12);
document.getElementById('hear').onclick=e=>{if(!AC){startSound();e.target.textContent='🔇 mute'}else{AC.close();AC=null;SND=null;e.target.textContent='🔊 hear it'}};
</script></body></html>"""


def main():
    ap = argparse.ArgumentParser(); ap.add_argument("--match", nargs="*"); ap.add_argument("--rounds", type=int, default=14)
    ap.add_argument("--lam", type=float, default=0.15); ap.add_argument("--seed", default="semantic", choices=["semantic", "colour"]); a = ap.parse_args()
    global SEED_MODE; SEED_MODE = a.seed
    ids = sorted(os.path.basename(os.path.dirname(os.path.dirname(p))) for p in glob.glob(os.path.join(OUT, "*", "multiplane", "planes.npz")))
    if a.match: ids = [i for i in ids if any(m in i for m in a.match)]
    allr = {}
    for sid in ids:
        t = time.time(); print(sid[:8])
        sc = Scene(sid, lam=a.lam); r = sc.refine(a.rounds); sc.export()
        print(f"  → {r}  {time.time() - t:.0f}s")
    for p in glob.glob(os.path.join(OUT, "*", "program", "scene.json")):
        j = json.load(open(p)); allr[j["id"]] = dict(score=j["score"], history=j["history"], camera=j["camera"])
    with open(os.path.join(ROOT, "shots", "program_data.js"), "w") as fh:
        fh.write("window.PG = " + json.dumps(allr) + ";\n")


if __name__ == "__main__":
    main()
