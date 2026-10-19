#!/usr/bin/env python3
"""
SCION · Multiplane Animation Engine — State Graph compiler
==========================================================

Compiles each cel sequence in shots/video/poem_XX/ into one canonical
Spatio-Temporal State Graph (shots/scion/state/poem_XX.json):

  1. DRAMATIC BEAT & CAUSALITY GRAPH  beats segmented from measured subject
     motion; causal roles STIMULUS → PERCEPTION → THOUGHT → ANTICIPATION →
     ACTION_EXTREME → CONTACT/OVERSHOOT → SETTLE; each beat tagged with a
     Cineosis sign family (perception / affect / action / reflection /
     mental / break / time) and the poem movement line it falls under.
  2. MULTIPLANE SPATIAL STACK         planes P0..P6 from multiplane.json with
     the SCION parallax coefficients (Z = 0.2, 0.5, 1.0, 1.2, 2.5, 6.0, inf).
  3. EXECUTABLE X-SHEET               24 fps rows; 12 fps cel drawings grouped
     into exposures (on 2s / 4s / HOLD) by measured frame identity; camera
     vector integrated from phase correlation; pin + FX state per row.
  4. KINEMATIC HULL (measurable part) P2 character masks at pipeline keys:
     area, centroid, solidity, foot point, depth-scaled volume.

Five invariant gates are MEASURED, not asserted:
  G1 silhouette separability   solidity / components / negative space of P2
  G2 volume conservation       area * z^2 across adjacent keys within a shot
  G3 contact pinning           foot-point slide on ground, camera-compensated
  G4 arc & phase-lag           path reversals + breakdown timing asymmetry
  G5 monotonic vitality        cel (composite) vs source (rough) kinetic +
                               silhouette punch; ABORT if the cel is deader

Honesty note: the footage is generated video run through a cel filter. The
compiler audits and re-times it; it cannot invent drawings. Heuristic labels
(roles, signs) are marked "heuristic": true.

Usage:  python3 shots/scion_compile.py            # all poems
        python3 shots/scion_compile.py poem_02    # one poem
"""
import glob
import json
import math
import os
import subprocess
import sys

import cv2
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
VID = os.path.join(HERE, "video")
OUT = os.path.join(HERE, "scion")
STATE = os.path.join(OUT, "state")
ASSETS = os.path.join(OUT, "assets")

AW, AH = 256, 144          # analysis + atlas cell size
FULL_W = 1024              # source width (for px conversion)
SRC_FPS = 12
XS_FPS = 24

PLANE_Z = {"P0": 0.2, "P1": 0.5, "P2": 1.0, "P3": 1.2, "P4": 2.5, "P5": 6.0, "P6": None}
PLANE_ROLE = {
    "P0": "Lens mask / extreme foreground occluders",
    "P1": "Fast foreground elements",
    "P2": "Primary character performance (focal plane)",
    "P3": "Secondary characters, props, cast shadows, contact FX",
    "P4": "Midground set & ground-plane anchor",
    "P5": "Distant background architecture",
    "P6": "Sky dome, atmosphere, volumetric light",
}

# Cineosis sign families (colours match hartswf0.github.io/cineosis-lab)
SIGNS = {
    "perception": {"color": "#e9d9a8", "image": "Perception-image", "test": "the frame is organised around seeing: camera or light moves, the subject waits"},
    "affect":     {"color": "#f0b9a4", "image": "Affection-image",  "test": "a face or body holds a quality/power without yet acting"},
    "action":     {"color": "#e7a37c", "image": "Action-image (SAS)", "test": "a situation provokes an action that changes the situation"},
    "reflection": {"color": "#b9cfa0", "image": "Reflection-image (ASA)", "test": "an action discloses the situation it happened in"},
    "mental":     {"color": "#a9c9c9", "image": "Mental / relation-image", "test": "the image holds a relation between the beats rather than a deed"},
    "break":      {"color": "#d9d3c7", "image": "Opsign / break", "test": "the sensory-motor link snaps: a cut, a blank, a pure optical situation"},
    "time":       {"color": "#b8b3d8", "image": "Time-image", "test": "duration itself is shown: a hold that outlasts its action"},
}

ROLE_VERB = {
    "STIMULUS": "something in the world changes",
    "PERCEPTION": "the change is registered",
    "THOUGHT": "an internal decision forms",
    "ANTICIPATION": "the body/camera loads against the coming move",
    "ACTION_EXTREME": "the move reaches its extreme",
    "CONTACT_OVERSHOOT": "the move lands and overshoots",
    "SETTLE": "the world settles into the aftermath",
}

DIRECTOR_RULES = {
    "scared":  {"label": "More scared / nervous", "ops": [["hold_scale", "ANTICIPATION", 1.6], ["hold_scale", "PERCEPTION", 1.3], ["jitter_holds", 2], ["slow_in", 1.4]]},
    "heavy":   {"label": "More weight / heavier", "ops": [["extend_contact", 4], ["shake_on_contact", 6], ["hold_scale", "CONTACT_OVERSHOOT", 1.5], ["slow_out", 1.3]]},
    "huge":    {"label": "Make the world feel huge", "ops": [["scale_focal", 0.55], ["occluder", 0.22], ["parallax_far", 0.25]]},
    "funny":   {"label": "Make it funnier", "ops": [["hold_scale", "PERCEPTION", 2.0], ["snap", "ANTICIPATION", 2], ["hold_scale", "ACTION_EXTREME", 0.6], ["hold_scale", "SETTLE", 1.5]]},
    "faster":  {"label": "Faster / snappier", "ops": [["global_rate", 0.75], ["snap", "ANTICIPATION", 3]]},
    "dreamy":  {"label": "Slower / dreamier", "ops": [["global_rate", 1.35], ["on_ones", True]]},
}


# ───────────────────────────────────────────────────────── helpers
def load_frames(d, n):
    files = sorted(glob.glob(os.path.join(d, "*.png")))[:n]
    col, gray = [], []
    for f in files:
        im = cv2.imread(f, cv2.IMREAD_COLOR)
        sm = cv2.resize(im, (AW, AH), interpolation=cv2.INTER_AREA)
        col.append(sm)
        gray.append(cv2.cvtColor(sm, cv2.COLOR_BGR2GRAY).astype(np.float32))
    return col, gray


def hist(im):
    hsv = cv2.cvtColor(im, cv2.COLOR_BGR2HSV)
    h = cv2.calcHist([hsv], [0, 1], None, [24, 16], [0, 180, 0, 256])
    return cv2.normalize(h, h).flatten()


def smooth(x, k=5):
    if len(x) < k:
        return np.asarray(x, float)
    w = np.ones(k) / k
    return np.convolve(np.pad(x, (k // 2, k // 2), mode="edge"), w, mode="valid")


def r(x, n=3):
    return None if x is None or (isinstance(x, float) and not math.isfinite(x)) else round(float(x), n)


def clean(o):
    """Strict JSON: NaN/Inf from upstream files become null."""
    if isinstance(o, float):
        return o if math.isfinite(o) else None
    if isinstance(o, dict):
        return {k: clean(v) for k, v in o.items()}
    if isinstance(o, (list, tuple)):
        return [clean(v) for v in o]
    return o


def write_atlas(frames, path, cols=12, cell=None):
    cw, ch = cell or (AW, AH)
    n = len(frames)
    rows = int(math.ceil(n / cols))
    sheet = np.zeros((rows * ch, cols * cw, 3), np.uint8)
    for i, f in enumerate(frames):
        y, x = divmod(i, cols)
        if f.shape[1] != cw or f.shape[0] != ch:
            f = cv2.resize(f, (cw, ch), interpolation=cv2.INTER_AREA)
        sheet[y * ch:(y + 1) * ch, x * cw:(x + 1) * cw] = f
    tmp = path + ".png"
    cv2.imwrite(tmp, sheet)
    subprocess.run(["cwebp", "-quiet", "-q", "72", tmp, "-o", path], check=True)
    os.remove(tmp)
    return {"cols": cols, "rows": rows, "cell": [cw, ch], "count": n}


# ───────────────────────────────────────────────────────── motion analysis
def analyse_motion(cel_g, src_g, src_c):
    n = len(cel_g)
    win = cv2.createHanningWindow((AW, AH), cv2.CV_32F)
    cam = [(0.0, 0.0)]
    subj, cel_diff, src_energy, cuts, centroids = [0.0], [0.0], [0.0], [], [None]
    hists = [hist(c) for c in src_c]
    for t in range(1, n):
        a, b = src_g[t - 1], src_g[t]
        corr = cv2.compareHist(hists[t - 1], hists[t], cv2.HISTCMP_CORREL)
        is_cut = corr < 0.55
        if is_cut:
            cuts.append(t)
            cam.append((0.0, 0.0)); subj.append(0.0); src_energy.append(0.0)
            centroids.append(None)
        else:
            (dx, dy), _ = cv2.phaseCorrelate(a, b, win)
            if abs(dx) > AW * 0.25 or abs(dy) > AH * 0.25:
                dx = dy = 0.0
            cam.append((dx, dy))
            M = np.float32([[1, 0, dx], [0, 1, dy]])
            warped = cv2.warpAffine(a, M, (AW, AH), borderMode=cv2.BORDER_REPLICATE)
            res = np.abs(b - warped)
            res[:4, :] = res[-4:, :] = 0; res[:, :4] = res[:, -4:] = 0
            src_energy.append(float(np.abs(b - a).mean()))
            subj.append(float(res.mean()))
            m = res > max(18.0, np.percentile(res, 97))
            if m.sum() > 25:
                ys, xs = np.nonzero(m)
                centroids.append((float(xs.mean()) / AW, float(ys.mean()) / AH))
            else:
                centroids.append(None)
        cel_diff.append(float(np.abs(cel_g[t] - cel_g[t - 1]).mean()))
    return {
        "cam": cam, "subj": np.array(subj), "cel_diff": np.array(cel_diff),
        "src_energy": np.array(src_energy), "cuts": cuts, "centroids": centroids,
    }


# ───────────────────────────────────────────────────────── exposures
def exposures(cel_diff, cuts):
    """Group 12fps cel frames into drawings. A frame repeats its drawing when
    it is (near-)identical to the previous one."""
    thr = max(0.6, float(np.percentile(cel_diff[1:], 8)) * 1.05) if len(cel_diff) > 2 else 0.6
    drawings, cur = [], [0]
    for t in range(1, len(cel_diff)):
        if cel_diff[t] < thr and t not in cuts:
            cur.append(t)
        else:
            drawings.append(cur); cur = [t]
    drawings.append(cur)
    return drawings, thr


# ───────────────────────────────────────────────────────── beats
def segment_beats(subj, cam_speed, cuts, n, min_len=8, max_beats=9):
    e = smooth(subj, 5)
    q35, q75 = np.percentile(e, 35), np.percentile(e, 75)
    state = np.where(e > q75, 2, np.where(e < q35, 0, 1))
    runs, s = [], 0
    for t in range(1, n + 1):
        if t == n or state[t] != state[s] or t in cuts:
            runs.append([s, t]); s = t
    # merge short runs into the neighbour with the closer mean energy
    changed = True
    while changed and len(runs) > 1:
        changed = False
        for i, (a, b) in enumerate(runs):
            if b - a < min_len:
                if i == 0: j = 1
                elif i == len(runs) - 1: j = i - 1
                else:
                    m = e[a:b].mean()
                    j = i - 1 if abs(e[runs[i - 1][0]:runs[i - 1][1]].mean() - m) <= abs(e[runs[i + 1][0]:runs[i + 1][1]].mean() - m) else i + 1
                lo, hi = sorted([i, j])
                runs[lo] = [runs[lo][0], runs[hi][1]]; del runs[hi]
                changed = True
                break
    while len(runs) > max_beats:
        k = min(range(len(runs) - 1), key=lambda i: (runs[i][1] - runs[i][0]) + (runs[i + 1][1] - runs[i + 1][0]))
        runs[k] = [runs[k][0], runs[k + 1][1]]; del runs[k + 1]
    return runs, e


def assign_roles(runs, e):
    """Multi-arc causal roles: every local energy peak is an ACTION_EXTREME;
    the beat before it loads (ANTICIPATION), the beat after lands
    (CONTACT_OVERSHOOT); quiet beats between arcs alternate SETTLE (closer to
    the previous peak) and PERCEPTION/THOUGHT (closer to the next)."""
    means = [float(e[a:b].mean()) for a, b in runs]
    n = len(runs)
    spread = (max(means) - min(means)) or 1e-6
    peaks = [i for i in range(n)
             if means[i] >= (means[i - 1] if i > 0 else -1) and means[i] >= (means[i + 1] if i < n - 1 else -1)
             and (means[i] - min(means)) / spread > 0.45]
    if not peaks:
        peaks = [int(np.argmax(means))]
    roles = [None] * n
    for p in peaks:
        roles[p] = "ACTION_EXTREME"
    for i in range(n):
        if roles[i]:
            continue
        nxt = next((p for p in peaks if p > i), None)
        prv = next((p for p in reversed(peaks) if p < i), None)
        if nxt == i + 1:
            roles[i] = "ANTICIPATION"
        elif prv == i - 1:
            roles[i] = "CONTACT_OVERSHOOT"
        elif prv is None:
            roles[i] = "STIMULUS" if i == 0 else ("PERCEPTION" if i == 1 else "THOUGHT")
        elif nxt is None:
            k = i - prv - 2  # beats after the landing: settle, then a new arc opens and stays unresolved
            roles[i] = "SETTLE" if k == 0 else ("PERCEPTION" if k == 1 else "THOUGHT")
        else:
            roles[i] = "SETTLE" if (i - prv) <= (nxt - i) else "PERCEPTION"
    if roles[0] not in ("ACTION_EXTREME", "ANTICIPATION"):
        roles[0] = "STIMULUS"
    if n > 1 and roles[-1] not in ("ACTION_EXTREME", "CONTACT_OVERSHOOT"):
        roles[-1] = "SETTLE"
    return roles, means


def sign_for(role, mean_e, cam_mean, dur, p2_area, opens_on_cut, e_med):
    if opens_on_cut and role in ("STIMULUS", "SETTLE"):
        return "break"
    if role == "ACTION_EXTREME":
        return "action"
    if role == "CONTACT_OVERSHOOT":
        return "reflection"
    if cam_mean > 1.2 and mean_e <= e_med:
        return "perception"
    if p2_area and p2_area > 0.08 and role in ("ANTICIPATION", "THOUGHT", "PERCEPTION"):
        return "affect"
    if dur >= 24 and mean_e < e_med:
        return "time"
    if role == "SETTLE":
        return "mental"
    return "perception"


# ───────────────────────────────────────────────────────── keys (masks)
def load_keys(poem_dir, seq_keys):
    keys = []
    for kf in seq_keys:
        idx = int(kf[2:7])
        stem = os.path.splitext(kf)[0]
        sd = glob.glob(os.path.join(poem_dir, "out", f"*-{stem}"))
        if not sd:
            continue
        sd = sd[0]
        k = {"frame": idx, "id": os.path.basename(sd)}
        try:
            pl = np.load(os.path.join(sd, "multiplane", "planes.npz"))
            k["P2"] = pl["P2"]; k["ground"] = pl["ground"]
        except Exception:
            k["P2"] = None; k["ground"] = None
        try:
            k["depth"] = np.load(os.path.join(sd, "arrays.npz"))["depth"].astype(np.float32)
        except Exception:
            k["depth"] = None
        try:
            k["mp"] = json.load(open(os.path.join(sd, "multiplane", "multiplane.json")))
        except Exception:
            k["mp"] = None
        keys.append(k)
    return keys


def hull_metrics(k):
    m = k.get("P2")
    if m is None or m.mean() < 0.004:
        return None
    m8 = m.astype(np.uint8)
    ncomp, lab, stats, _ = cv2.connectedComponentsWithStats(m8, 8)
    big = [i for i in range(1, ncomp) if stats[i, cv2.CC_STAT_AREA] > 0.002 * m.size]
    cnts, hier = cv2.findContours(m8, cv2.RETR_CCOMP, cv2.CHAIN_APPROX_SIMPLE)
    area = float(m.sum())
    hull_area = sum(cv2.contourArea(cv2.convexHull(c)) for c in cnts if cv2.contourArea(c) > 0.002 * m.size) or 1.0
    holes = 0 if hier is None else int(sum(1 for h in hier[0] if h[3] >= 0))
    ys, xs = np.nonzero(m)
    cx, cy = float(xs.mean()), float(ys.mean())
    foot_y = int(ys.max())
    foot_x = float(xs[ys >= foot_y - 3].mean())
    on_ground = False
    if k.get("ground") is not None:
        g = k["ground"]
        y0, y1 = min(foot_y + 1, g.shape[0] - 1), min(foot_y + 8, g.shape[0])
        x0, x1 = max(int(foot_x) - 10, 0), min(int(foot_x) + 10, g.shape[1])
        on_ground = bool(g[y0:y1, x0:x1].mean() > 0.3) if y1 > y0 else False
    zmed = float(np.median(k["depth"][m])) if k.get("depth") is not None else None
    H, W = m.shape
    return {
        "area": area / m.size, "solidity": min(1.0, area / hull_area), "components": len(big),
        "holes": holes, "centroid": [cx / W, cy / H], "foot": [foot_x / W, foot_y / H],
        "on_ground": on_ground, "z_med_m": zmed,
        "volume": (area / m.size) * (zmed ** 2) if zmed else None,
    }


def mask_thumb(k):
    m = k.get("P2")
    if m is None:
        return np.zeros((AH, AW), np.uint8)
    return cv2.resize(m.astype(np.uint8) * 255, (AW, AH), interpolation=cv2.INTER_NEAREST)


def shot_id_of(frame, cuts):
    return sum(1 for c in cuts if c <= frame)


# ───────────────────────────────────────────────────────── gates
def gate1(hulls):
    rows = []
    for fr, h in hulls:
        if h is None:
            continue
        ok_area = 0.01 <= h["area"] <= 0.45
        ok_sol = 0.40 <= h["solidity"] <= 0.92
        ok_comp = h["components"] <= 2
        score = (0.4 * ok_sol + 0.3 * ok_area + 0.3 * ok_comp)
        why = []
        if not ok_sol:
            why.append("blob: no negative space to read a gesture" if h["solidity"] > 0.92 else "fragmented contour")
        if not ok_area:
            why.append("figure too small to read" if h["area"] < 0.01 else "figure crowds the frame")
        if not ok_comp:
            why.append(f"{h['components']} disconnected pieces")
        rows.append({"frame": fr, "score": r(score), "pass": score >= 0.7, "solidity": r(h["solidity"]), "area": r(h["area"]), "components": h["components"], "why": why})
    if not rows:
        return {"status": "N/A", "reason": "no character on Plane 2 in any key (pure environment sequence)", "keys": []}
    p = sum(x["pass"] for x in rows) / len(rows)
    return {"status": "PASS" if p >= 0.75 else "FAIL", "pass_rate": r(p), "keys": rows}


def gate2(hulls, cuts):
    rows = []
    for (fa, a), (fb, b) in zip(hulls, hulls[1:]):
        if a is None or b is None or a["volume"] is None or b["volume"] is None:
            continue
        if shot_id_of(fa, cuts) != shot_id_of(fb, cuts):
            continue
        dev = abs(b["volume"] - a["volume"]) / max(a["volume"], 1e-6)
        rows.append({"from": fa, "to": fb, "dev": r(dev), "pass": dev <= 0.05, "boil": dev > 0.25})
    if not rows:
        return {"status": "N/A", "reason": "fewer than two depth-scaled character keys inside one shot", "pairs": []}
    p = sum(x["pass"] for x in rows) / len(rows)
    return {"status": "PASS" if p >= 0.75 else "FAIL", "pass_rate": r(p), "median_dev": r(float(np.median([x["dev"] for x in rows]))), "pairs": rows}


def gate3(hulls, cuts, cam_cum):
    rows = []
    for (fa, a), (fb, b) in zip(hulls, hulls[1:]):
        if a is None or b is None or not (a["on_ground"] and b["on_ground"]):
            continue
        if shot_id_of(fa, cuts) != shot_id_of(fb, cuts):
            continue
        cdx = (cam_cum[fb][0] - cam_cum[fa][0]) / AW
        slide = abs((b["foot"][0] - a["foot"][0]) - cdx)
        rows.append({"from": fa, "to": fb, "slide": r(slide), "pass": slide <= 0.015})
    if not rows:
        return {"status": "N/A", "reason": "no consecutive keys with a foot pinned to recovered ground", "pairs": []}
    p = sum(x["pass"] for x in rows) / len(rows)
    return {"status": "PASS" if p >= 0.75 else "FAIL", "pass_rate": r(p), "pairs": rows}


def gate4(centroids, cuts, runs, keyframes_f, cum_motion):
    # path reversals of the moving-mass centroid, per shot (3-frame smoothed)
    sm = list(centroids)
    for t in range(1, len(centroids) - 1):
        trio = [centroids[t - 1], centroids[t], centroids[t + 1]]
        if all(c is not None for c in trio) and not any(x in cuts for x in (t, t + 1)):
            sm[t] = (sum(c[0] for c in trio) / 3, sum(c[1] for c in trio) / 3)
    centroids = sm
    rev, steps, speeds = 0, 0, []
    prev_v = None
    for t in range(2, len(centroids)):
        a, b = centroids[t - 1], centroids[t]
        if a is None or b is None or t in cuts or (t - 1) in cuts:
            prev_v = None
            continue
        v = np.array(b) - np.array(a)
        sp = float(np.linalg.norm(v))
        if sp < 0.008:
            continue
        speeds.append(sp)
        if prev_v is not None:
            cosang = float(np.dot(v, prev_v) / (np.linalg.norm(v) * np.linalg.norm(prev_v) + 1e-9))
            steps += 1
            if cosang < -0.3:
                rev += 1
        prev_v = v
    zig = rev / steps if steps else None
    cv_speed = float(np.std(speeds) / (np.mean(speeds) + 1e-9)) if len(speeds) > 4 else None
    # breakdown asymmetry between consecutive SCION keys
    bds = []
    for ka, kb in zip(keyframes_f, keyframes_f[1:]):
        if kb - ka < 3 or any(ka < c <= kb for c in cuts):
            continue
        seg = cum_motion[ka:kb + 1] - cum_motion[ka]
        total = seg[-1]
        if total <= 1e-6:
            continue
        half = int(np.searchsorted(seg, total / 2))
        asym = half / (kb - ka)
        bds.append({"between": [ka, kb], "breakdown": ka + half, "asymmetry": r(asym), "linear_blend": abs(asym - 0.5) < 0.08})
    lin = sum(b["linear_blend"] for b in bds) / len(bds) if bds else None
    status = "N/A"
    if zig is not None or lin is not None:
        bad = (zig is not None and zig > 0.35) or (lin is not None and lin > 0.5) or (cv_speed is not None and cv_speed < 0.15)
        status = "FAIL" if bad else "PASS"
    return {"status": status, "zigzag_rate": r(zig), "speed_cv": r(cv_speed), "linear_breakdown_rate": r(lin), "breakdowns": bds,
            "note": "zigzag = share of centroid steps that reverse direction; speed_cv near 0 = mechanical constant velocity"}


def gate5(src_c, cel_c, src_g, cel_g, keys, n):
    # kinetic readability: does the cel keep the source's motion structure?
    src_d = np.array([0.0] + [np.abs(src_g[t] - src_g[t - 1]).mean() for t in range(1, n)])
    cel_d = np.array([0.0] + [np.abs(cel_g[t] - cel_g[t - 1]).mean() for t in range(1, n)])
    src_k, cel_k = float(src_d[1:].mean()), float(cel_d[1:].mean())
    a_, b_ = smooth(src_d[1:], 5), smooth(cel_d[1:], 5)
    corr = float(np.corrcoef(a_, b_)[0, 1]) if a_.std() > 1e-6 and b_.std() > 1e-6 else 0.0
    # boil: change in the cel on pixels that are static in the source
    s_st, c_st = [], []
    for t in range(1, n):
        d = np.abs(src_g[t] - src_g[t - 1])
        m = d < 1.5
        if m.mean() > 0.2:
            s_st.append(float(d[m].mean())); c_st.append(float(np.abs(cel_g[t] - cel_g[t - 1])[m].mean()))
    boil_static = (np.mean(c_st) / max(np.mean(s_st), 1e-3)) if s_st else None
    boil_abs = float(np.mean(c_st)) if c_st else None
    # silhouette punch at keys: |mean L inside P2 - mean L in a ring around it|
    def punch(gray, m):
        if m is None or m.mean() < 0.004:
            return None
        ms = cv2.resize(m.astype(np.uint8), (AW, AH), interpolation=cv2.INTER_NEAREST).astype(bool)
        if ms.sum() < 10:
            return None
        ring = cv2.dilate(ms.astype(np.uint8), np.ones((9, 9), np.uint8)).astype(bool) & ~ms
        if ring.sum() < 10:
            return None
        return abs(float(gray[ms].mean()) - float(gray[ring].mean()))
    pr, pc = [], []
    for k in keys:
        f = min(k["frame"], n - 1)
        a, b = punch(src_g[f], k.get("P2")), punch(cel_g[f], k.get("P2"))
        if a is not None and b is not None:
            pr.append(a); pc.append(b)
    # edge energy (gesture line density)
    def edges(c):
        return float(np.mean([cv2.Canny(x, 60, 160).mean() for x in c[::6]]))
    e_src, e_cel = edges(src_c), edges(cel_c)
    boil = cel_k / (src_k + 1e-9)
    pun = min(2.0, float(np.mean(pc)) / max(float(np.mean(pr)), 4.0)) if pr else None
    edge = min(2.0, e_cel / (e_src + 1e-9))
    parts = [max(corr, 0.0), min(edge, 1.0)] + ([min(pun, 1.0)] if pun is not None else [])
    vit = float(np.mean(parts))
    reasons = []
    if corr < 0.6: reasons.append(f"motion structure lost (corr {corr:.2f})")
    if pun is not None and pun < 0.85: reasons.append(f"silhouette punch flattened ({pun:.2f}x)")
    if edge < 0.5: reasons.append(f"gesture line thinned ({edge:.2f}x edges)")
    if boil_static is not None and boil_static > 1.6 and boil_abs > 0.5:
        reasons.append(f"cel boils: {boil_static:.2f}x change on pixels that are still in the source")
    verdict = "KEEP_CEL" if not reasons else "ABORT_RESTORE_ROUGH"
    return {"status": "PASS" if verdict == "KEEP_CEL" else "FAIL", "verdict": verdict, "reasons": reasons,
            "checkpoints": {"STAGE_KEY_ROUGH": "source frames (video/poem_XX/frames)", "STAGE_TIEDOWN_MOTION": "not separately stored by the cel pipeline", "STAGE_COMPOSITE": "cel frames (video/poem_XX/cel_frames)"},
            "motion_corr": r(corr), "boil_ratio": r(boil), "boil_static": r(boil_static), "boil_static_gray": r(boil_abs),
            "punch_ratio": r(pun), "edge_ratio": r(edge), "vitality": r(vit)}


# ───────────────────────────────────────────────────────── compile one poem
def compile_poem(seq, poem_meta):
    pid = seq["id"]
    pdir = os.path.join(VID, pid)
    n = seq.get("total_frames") or len(glob.glob(os.path.join(pdir, "cel_frames", "*.png")))
    print(f"[{pid}] loading {n} frames …", flush=True)
    cel_c, cel_g = load_frames(os.path.join(pdir, "cel_frames"), n)
    src_c, src_g = load_frames(os.path.join(pdir, "frames"), n)
    n = min(len(cel_c), len(src_c))
    cel_c, cel_g, src_c, src_g = cel_c[:n], cel_g[:n], src_c[:n], src_g[:n]

    mo = analyse_motion(cel_g, src_g, src_c)
    cam = mo["cam"]
    cam_cum = np.cumsum(np.array(cam), axis=0).tolist()
    cam_speed = np.array([math.hypot(*c) for c in cam])
    cum_motion = np.cumsum(np.maximum(mo["subj"] - np.percentile(mo["subj"][1:], 25), 0.0))

    drawings, ex_thr = exposures(mo["cel_diff"], mo["cuts"])
    runs, e = segment_beats(mo["subj"], cam_speed, mo["cuts"], n)
    roles, means = assign_roles(runs, e)
    e_med = float(np.median(e))

    keys = load_keys(pdir, seq["keyframes"])
    hulls = [(k["frame"], hull_metrics(k)) for k in keys]
    hull_by_frame = {f: h for f, h in hulls}

    def nearest_key(fr):
        if not keys:
            return None
        return min(keys, key=lambda k: (shot_id_of(k["frame"], mo["cuts"]) != shot_id_of(fr, mo["cuts"]), abs(k["frame"] - fr)))

    movements = (poem_meta or {}).get("movements") or []
    beats, scion_keys = [], []
    for i, ((a, b), role) in enumerate(zip(runs, roles)):
        seg = e[a:b]
        kf = a + int(np.argmax(seg) if role in ("ACTION_EXTREME", "CONTACT_OVERSHOOT", "ANTICIPATION") else np.argmin(seg))
        nk = nearest_key(kf)
        h = hull_by_frame.get(nk["frame"]) if nk else None
        contents = []
        if nk and nk.get("mp"):
            for pl in nk["mp"].get("planes", []):
                for c in pl.get("contents") or []:
                    if c not in contents:
                        contents.append(c)
        cam_mean = float(cam_speed[a:b].mean())
        sign = sign_for(role, float(seg.mean()), cam_mean, b - a, h["area"] if h else None, a in mo["cuts"], e_med)
        mv = movements[min(int((a + b) / 2 / n * len(movements)), len(movements) - 1)] if movements else None
        subject = "the figure" if h else (contents[0] if contents else "the frame")
        beats.append({
            "id": f"B{i + 1:02d}", "role": role, "heuristic": True,
            "f_in": a, "f_out": b, "dur_src": b - a, "dur_24": (b - a) * 2,
            "energy": r(float(seg.mean())), "camera_speed": r(cam_mean),
            "sign": sign, "sign_image": SIGNS[sign]["image"],
            "verb": f"{ROLE_VERB[role]} — {subject}" + (f" against {', '.join(c for c in contents[:3] if c != subject)}" if contents else ""),
            "movement": mv["label"] if mv else None, "line": mv["line"] if mv else None,
            "key_frame": kf, "mask_key": nk["frame"] if nk else None, "opens_on_cut": a in mo["cuts"],
        })
        scion_keys.append({"id": f"K{i + 1:02d}", "frame": kf, "beat": f"B{i + 1:02d}", "role": role,
                           "silhouette_key": nk["frame"] if nk else None})

    # Key-only flip test proxy: do the keys alone span distinct situations?
    flip = None
    if len(scion_keys) >= 2:
        hs = [hist(src_c[k["frame"]]) for k in scion_keys]
        dif = [1 - cv2.compareHist(hs[i], hs[i + 1], cv2.HISTCMP_CORREL) for i in range(len(hs) - 1)]
        flip = {"mean_key_change": r(float(np.mean(dif))), "reads": float(np.mean(dif)) > 0.05 or len(mo["cuts"]) > 0,
                "note": "keys must differ enough to tell the story with no in-betweens"}

    # 3 staging topologies: candidate keys ranked by silhouette contrast
    topo = []
    for k in keys:
        h = hull_by_frame.get(k["frame"])
        g = src_g[min(k["frame"], n - 1)]
        horizon = None
        if k.get("ground") is not None and k["ground"].any():
            rows_g = np.nonzero(k["ground"].any(axis=1))[0]
            horizon = float(rows_g.min()) / k["ground"].shape[0]
        contrast = None
        if h is not None:
            ms = cv2.resize(k["P2"].astype(np.uint8), (AW, AH), interpolation=cv2.INTER_NEAREST).astype(bool)
            if ms.sum() > 10 and (~ms).sum() > 10:
                contrast = abs(float(g[ms].mean()) - float(g[~ms].mean())) / 255
        neg = 1 - (h["area"] if h else 0)
        topo.append({"frame": k["frame"], "horizon": r(horizon), "figure_scale": r(h["area"]) if h else 0,
                     "negative_space": r(neg), "silhouette_contrast": r(contrast),
                     "occluder_P0": r(next((p["area_frac"] for p in (k["mp"] or {}).get("planes", []) if p["id"] == "P0"), 0))})
    topo.sort(key=lambda t: (1.0 if t["figure_scale"] else 0.0) + (t["silhouette_contrast"] or 0) + 0.2 * (t["occluder_P0"] or 0), reverse=True)
    picks, seen = [], set()
    for t in topo:
        sig = (round((t["horizon"] or 0) * 4), round((t["figure_scale"] or 0) * 10))
        if sig not in seen:
            picks.append(t); seen.add(sig)
        if len(picks) == 3:
            break
    if picks:
        picks[0]["selected"] = True

    # multiplane stack per pipeline key
    stack = []
    for k in keys:
        mp = k.get("mp") or {}
        planes = []
        for pl in mp.get("planes", []):
            planes.append({"id": pl["id"], "z_scion": PLANE_Z.get(pl["id"]), "role": PLANE_ROLE.get(pl["id"]),
                           "name": pl.get("name"), "area": r(pl.get("area_frac")), "z_m": r(pl.get("z_median_m"), 2),
                           "parallax": r(pl.get("parallax")), "haze": r(pl.get("haze")), "contents": pl.get("contents") or []})
        stack.append({"frame": k["frame"], "camera": mp.get("camera"), "planes": planes})

    # X-sheet at 24 fps
    beat_of = np.zeros(n, int)
    for i, (a, b) in enumerate(runs):
        beat_of[a:b] = i
    draw_of, draw_len = np.zeros(n, int), np.zeros(n, int)
    for di, d in enumerate(drawings):
        for t in d:
            draw_of[t] = di; draw_len[t] = len(d)
    key_frames = {k["frame"] for k in scion_keys}
    pinned_beats = {b["id"] for b in beats if b["role"] in ("CONTACT_OVERSHOOT", "SETTLE")}
    xs = []
    for t in range(n):
        for sub in range(2):
            L = draw_len[t] * 2
            expo = "2s" if L == 2 else ("4s" if L == 4 else "HOLD")
            bt = beats[beat_of[t]]
            xs.append([t * 2 + sub, t, int(draw_of[t]), expo,
                       1 if (bt["id"] in pinned_beats and any(h and h["on_ground"] for f, h in hulls if abs(f - t) <= 6)) else 0,
                       [r(cam_cum[t][0] * FULL_W / AW, 1), r(cam_cum[t][1] * FULL_W / AW, 1)],
                       bt["id"], 1 if t in key_frames and sub == 0 else 0, 1 if t in mo["cuts"] and sub == 0 else 0])

    # gates
    G = {
        "G1_silhouette": gate1(hulls),
        "G2_volume": gate2(hulls, mo["cuts"]),
        "G3_contact": gate3(hulls, mo["cuts"], cam_cum),
        "G4_arcs": gate4(mo["centroids"], mo["cuts"], runs, sorted(key_frames), cum_motion),
        "G5_vitality": gate5(src_c, cel_c, src_g, cel_g, keys, n),
    }
    worst = None
    order = ["G5_vitality", "G1_silhouette", "G3_contact", "G2_volume", "G4_arcs"]
    for g in order:
        if G[g]["status"] == "FAIL":
            worst = g
            break
    fixes = {
        "G1_silhouette": "re-stage the key: open negative space between limbs and torso, or move the camera so the gesture reads in silhouette",
        "G2_volume": "the generator boils the figure's mass between keys; lock key volumes and redraw breakdowns from the hull, not the pixels",
        "G3_contact": "feet slide on the ground: pin the foot point in world space for the contact window and re-solve the in-betweens",
        "G4_arcs": "motion zig-zags or runs at constant speed: redraw breakdowns off-centre (favour the lead mass) and chart arcs on nose/hands/hips",
        "G5_vitality": "the cel filter flattened the motion: restore the rough source frames for this shot and re-ink with weight-sensitive line",
    }

    # atlases
    os.makedirs(ASSETS, exist_ok=True)
    big = [cv2.resize(cv2.imread(f), (384, 216), interpolation=cv2.INTER_AREA)
           for f in sorted(glob.glob(os.path.join(pdir, "cel_frames", "*.png")))[:n]]
    at_cel = write_atlas(big, os.path.join(ASSETS, f"{pid}_cel.webp"), cell=(384, 216))
    del big
    at_src = write_atlas(src_c, os.path.join(ASSETS, f"{pid}_rough.webp"))
    mthumbs = [cv2.cvtColor(mask_thumb(k), cv2.COLOR_GRAY2BGR) for k in keys]
    at_msk = write_atlas(mthumbs, os.path.join(ASSETS, f"{pid}_masks.webp"), cols=max(1, len(mthumbs))) if mthumbs else None

    return {
        "schema": "scion.state/2.0",
        "id": pid, "num": seq["num"], "title": seq["title"],
        "tagline": (poem_meta or {}).get("tagline"), "district": (poem_meta or {}).get("district_name"),
        "color": (poem_meta or {}).get("color"),
        "src_fps": SRC_FPS, "xsheet_fps": XS_FPS, "frames": n, "seconds": r(n / SRC_FPS, 2),
        "assets": {"cel": f"assets/{pid}_cel.webp", "rough": f"assets/{pid}_rough.webp",
                   "masks": f"assets/{pid}_masks.webp" if at_msk else None,
                   "atlas": at_cel, "rough_atlas": at_src, "mask_atlas": at_msk, "video": f"../video/{pid}/cartoon.mp4"},
        "cuts": mo["cuts"],
        "dramatic": {
            "two_seconds_before": (f"{(poem_meta or {}).get('tagline') or ''}. " if poem_meta else "") + (f"Before frame 1 we are already inside '{movements[0]['label']}': " if movements else "") + "the city was moving before the camera arrived, so the opening beat is a stimulus already in progress, not a cold start.",
            "causal_chain": [b["role"] for b in beats],
            "beats": beats, "keys": scion_keys, "flip_test": flip,
            "staging_topologies": picks,
        },
        "multiplane": {"z": PLANE_Z, "roles": PLANE_ROLE, "by_key": stack},
        "xsheet": {
            "columns": ["f24", "src_frame", "drawing", "exposure", "pin", "camera_xy_px", "beat", "is_key", "is_cut"],
            "rows": xs,
            "drawings": len(drawings), "identity_threshold": r(ex_thr),
            "exposure_mix": {k: int(sum(1 for d in drawings if (len(d) * 2 == 2 and k == "2s") or (len(d) * 2 == 4 and k == "4s") or (len(d) * 2 > 4 and k == "HOLD"))) for k in ("2s", "4s", "HOLD")},
        },
        "hull": [{"frame": f, **({k: (r(v) if isinstance(v, float) else v) for k, v in h.items() if k not in ("centroid", "foot")} if h else {"empty": True}),
                  **({"centroid": [r(x) for x in h["centroid"]], "foot": [r(x) for x in h["foot"]]} if h else {})} for f, h in hulls],
        "motion": {"subject": [r(x) for x in e], "camera": [r(x) for x in cam_speed],
                   "centroid": [[r(c[0]), r(c[1])] if c else None for c in mo["centroids"]]},
        "gates": G,
        "audit": {"highest_leverage_flaw": worst, "fix": fixes.get(worst) if worst else "no gate failed; push performance, not repair"},
        "director_rules": DIRECTOR_RULES,
    }


# ───────────────────────────────────────────────────────── main
def main():
    os.makedirs(STATE, exist_ok=True)
    seqs = json.load(open(os.path.join(HERE, "cartoon_sequences.json")))
    poems = {p["num"]: p for p in json.load(open(os.path.join(HERE, "film", "poems.json")))}
    only = sys.argv[1:]
    index = []
    for seq in seqs:
        if only and seq["id"] not in only:
            continue
        st = compile_poem(seq, poems.get(seq["num"]))
        with open(os.path.join(STATE, f"{seq['id']}.json"), "w") as f:
            json.dump(clean(st), f, separators=(",", ":"), allow_nan=False)
        g = st["gates"]
        index.append({"id": st["id"], "num": st["num"], "title": st["title"], "tagline": st["tagline"],
                      "district": st["district"], "color": st["color"], "frames": st["frames"],
                      "beats": len(st["dramatic"]["beats"]), "cuts": len(st["cuts"]),
                      "signs": [b["sign"] for b in st["dramatic"]["beats"]],
                      "gates": {k: v["status"] for k, v in g.items()},
                      "vitality": g["G5_vitality"]["vitality"], "flaw": st["audit"]["highest_leverage_flaw"],
                      "thumb": st["assets"]["cel"]})
        print(f"[{seq['id']}] beats={len(st['dramatic']['beats'])} cuts={len(st['cuts'])} " +
              " ".join(f"{k.split('_')[0]}:{v['status']}" for k, v in g.items()), flush=True)
    if not only:
        with open(os.path.join(OUT, "index.json"), "w") as f:
            json.dump({"schema": "scion.index/2.0", "signs": SIGNS, "poems": index,
                       "drawn": sorted(os.path.basename(os.path.dirname(m)) for m in glob.glob(os.path.join(OUT, "drawn", "*", "manifest.json")))}, f, indent=1)
        export = {
            "schema": "cineosis.scion-export/1.0",
            "source": "WYGWYL · Atlantis Urbanism — SCION multiplane animation engine",
            "studio_url": "https://hartswf0.github.io/wygwyl-world-arch/shots/scion.html",
            "sign_families": SIGNS,
            "shots": [],
        }
        for p in index:
            st = json.load(open(os.path.join(STATE, f"{p['id']}.json")))
            for b in st["dramatic"]["beats"]:
                export["shots"].append({
                    "id": f"wygwyl-{p['id']}-{b['id']}", "collection": "wygwyl-cel", "poem": p["title"],
                    "t_in": r(b["f_in"] / SRC_FPS, 2), "t_out": r(b["f_out"] / SRC_FPS, 2),
                    "sign": b["sign"], "sign_image": b["sign_image"], "role": b["role"],
                    "line": b["line"], "verb": b["verb"],
                    "video": f"https://hartswf0.github.io/wygwyl-world-arch/shots/scion.html?poem={p['id']}&beat={b['id']}",
                    "heuristic": True,
                })
        with open(os.path.join(OUT, "cineosis_export.json"), "w") as f:
            json.dump(export, f, indent=1)
        print(f"wrote {len(index)} state graphs + index.json + cineosis_export.json")


if __name__ == "__main__":
    main()
