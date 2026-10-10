#!/usr/bin/env python3
"""
film_render.py — from layout to footage.

The multiplane pass already cut every shot into depth sheets (S??_P?.png, back-painted),
chose a camera law (push / truck / tilt_up / crane_push) and wrote an x-sheet.
This script photographs those sheets through time:

  shot   out/<id>/film/shot.mp4      24 fps, camera on ones, secondary drawings on twos
         out/<id>/film/xsheet.json   what happens on which frame (hold → move → settle, FX list)
  reel   shots/film/poem_NN.mp4      the poem's shots cut together (12-frame dissolves)
         shots/film/riverbed_NN.json Golden Riverbed record (riverbed / flow / patches / bridges)
         shots/film/reels.js         index for reel.html

Secondary action comes only from evidence in the shot:
  water/pool/canal labels      → ripple displacement on that sheet (ones)
  fabric/plant/lantern labels  → sway anchored at the sheet's base (twos)
  hero sheet (P2)              → moving hold: breathing, anchored at the feet (twos)
  prompt mentions rain/drizzle → rain streaks, speed and length scaled by depth
  glow_pass.png                → neon flicker riding the midground camera
  plane haze                   → drifting haze between midground and foreground

What it CANNOT do: draw new character key poses. The x-sheet keys (K01…) remain
instructions for a draftsman or an image-to-video model (see riverbed segment prompts).

Usage:
  .venv-shots/bin/python shots/film_render.py --match d3d25411     # one shot
  .venv-shots/bin/python shots/film_render.py --all                # all shots + reels
  .venv-shots/bin/python shots/film_render.py --reels-only
"""
import argparse, glob, json, math, os, re, subprocess
import numpy as np
import cv2
from PIL import Image

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, "shots", "out")
FILM = os.path.join(ROOT, "shots", "film")
FPS, RW = 24, 960                       # render width; height follows aspect (even)
HOLD_IN, HOLD_OUT, MIN_FR = 12, 12, 120  # 0.5 s hold either side, ≥ 5 s per shot
XF = 12                                  # dissolve length in frames between shots
P_MIN, P_MAX = 0.4, 2.2                  # parallax spread a rigid card can survive before back-paint tears

R_WATER = re.compile(r"water|pool|canal|lagoon|sea|river|reflect|puddle|lake", re.I)
R_SWAY = re.compile(r"\b(fabric|laundry|cloth|flag|curtain|awning|plant|trees?|palms?|garden|flowers?|lanterns?|string lights|banner)\b", re.I)
R_FIG = re.compile(r"\b(person|people|figure|silhouette|walker|man|woman|child|kids?|crowd)\b", re.I)
R_RAIN = re.compile(r"\brain|drizzle|downpour|rain-slick|wet asphalt|soaked", re.I)


def ease(t):
    t = min(1.0, max(0.0, t)); return t * t * (3 - 2 * t)


def value_noise(h, w, cell, seed):
    rng = np.random.default_rng(seed)
    g = rng.random((h // cell + 3, w // cell + 3)).astype(np.float32)
    return cv2.resize(g, (w + 3 * cell, h + 3 * cell), interpolation=cv2.INTER_CUBIC)


def shot_dirs():
    return sorted(os.path.basename(os.path.dirname(os.path.dirname(p)))
                  for p in glob.glob(os.path.join(OUT, "*", "multiplane", "multiplane.json")))


# --------------------------------------------------------------------------- one shot
def render_shot(sid):
    od = os.path.join(OUT, sid); md = os.path.join(od, "multiplane"); fd = os.path.join(od, "film")
    os.makedirs(fd, exist_ok=True)
    S = json.load(open(os.path.join(od, "shot.json")))
    M = json.load(open(os.path.join(md, "multiplane.json")))
    W0, H0 = S["size"]
    sc = RW / W0; w, h = RW, int(round(H0 * sc / 2) * 2)
    cam = M["camera"]; move = cam["move"]; amp = cam["amplitude"]
    fx, fy = cam["focus"][0] * sc, cam["focus"][1] * sc
    N = max(MIN_FR, int(M.get("duration_frames") or 0))
    labels_all = " ".join([S.get("prompt", "")] + [d["label"] for d in S.get("detections", [])])
    rain = bool(R_RAIN.search(S.get("prompt", "")))
    haze_vals = [p["haze"] for p in M["planes"] if p.get("haze") is not None and p["id"] in ("P4", "P5")]
    haze = float(np.clip(np.mean(haze_vals) if haze_vals else 0.0, 0, 1))

    # water region = water-labelled detection boxes, feathered (ripple lives only here)
    water_mask = None
    wb = [d["box"] for d in S.get("detections", []) if R_WATER.search(d["label"])]
    if wb:
        water_mask = np.zeros((h, w), np.float32)
        for x0, y0, x1, y1 in wb:
            cv2.rectangle(water_mask, (int(x0 * sc), int(y0 * sc)), (int(x1 * sc), int(y1 * sc)), 1.0, -1)
        water_mask = cv2.GaussianBlur(water_mask, (0, 0), 6)

    # sheets back → front (file order S00.. is depth order by parallax, far first)
    sheets = []
    Lmap, sheet_idx = None, {}
    npz = os.path.join(md, "planes.npz")
    if os.path.exists(npz):
        z = np.load(npz)
        if "L" in z.files and "sheet_files" in z.files:
            Lmap = cv2.resize(z["L"], (w, h), interpolation=cv2.INTER_NEAREST)
            sheet_idx = {str(f): i for i, f in enumerate(z["sheet_files"])}
    for s in M["sheets"]:
        im = np.array(Image.open(os.path.join(md, s["file"])).convert("RGBA"))
        im = cv2.resize(im, (w, h), interpolation=cv2.INTER_AREA).astype(np.float32)
        if Lmap is not None and s["file"] in sheet_idx:          # tame placeholder back-paint
            own = (Lmap == sheet_idx[s["file"]]).astype(np.float32)
            painted = (im[..., 3] > 8) & (own < 0.5)
            if painted.any() and own.any():
                num = cv2.GaussianBlur(im[..., :3] * own[..., None], (0, 0), 18)
                den0 = cv2.GaussianBlur(own, (0, 0), 18)[..., None]
                loc = num / (den0 + 1e-3)
                calm = 0.5 * np.minimum(im[..., :3], loc * 1.05) + 0.5 * loc
                wgt = np.clip(den0 / 0.08, 0, 1)                       # no nearby support → keep fill
                calm = wgt * calm + (1 - wgt) * im[..., :3]
                im[..., :3][painted] = calm[painted]
                ab = cv2.GaussianBlur(im[..., 3], (0, 0), 3)
                im[..., 3][painted] = np.minimum(im[..., 3], ab)[painted]
        p = float(np.clip(s["parallax"], P_MIN, P_MAX))
        geo = {}
        if move in ("truck", "tilt_up"):
            geo["shift"] = min(amp * p, 0.3 * (W0 if move == "truck" else H0)) * sc
        else:
            geo["scale_end"] = min(1 + amp * p, 1.8)
        a = im[..., 3] > 8
        ys, xs = np.where(a)
        bbox = (ys.min(), ys.max(), xs.min(), xs.max()) if len(ys) else (0, h - 1, 0, w - 1)
        kind = []
        if R_WATER.search(s["label"]) or (s["plane"] in ("P1", "P4") and water_mask is not None
                                          and ((water_mask > 0) & a).mean() > 0.02): kind.append("ripple")
        if R_SWAY.search(s["label"]): kind.append("sway")
        if s["plane"] == "P2" and R_FIG.search(s["label"]): kind.append("breathe")
        sheets.append(dict(meta=s, im=im, geo=geo, bbox=bbox, kind=kind, plane=int(s["plane"][1]), p=p))
    for i, g in enumerate(sheets):                    # floors are ramps, not cards
        rows = (g["im"][..., 3] > 8).mean(axis=1)
        dense = np.where(rows > 0.25)[0]
        y0, y1 = (float(dense.min()), g["bbox"][1]) if len(dense) else (h, 0)
        if i and g["plane"] in (0, 1) and y1 >= h - 3 and y0 > 0.15 * h and g["p"] > sheets[i - 1]["p"]:
            g["ground"] = dict(y0=y0, p_far=sheets[i - 1]["p"], p_near=g["p"])
    pad = int(max([g["geo"].get("shift", 0) for g in sheets] + [0])) + 4

    glow = cv2.resize(np.array(Image.open(os.path.join(md, "glow_pass.png")).convert("RGB")), (w, h)).astype(np.float32) \
        if os.path.exists(os.path.join(md, "glow_pass.png")) else np.zeros((h, w, 3), np.float32)
    far = [g for g in sheets if g["plane"] in (5, 6)] or sheets[:1]
    back = far[0]["im"]
    haze_col = np.median(back[..., :3][back[..., 3] > 8], axis=0) if (back[..., 3] > 8).any() else np.array([128.0, 128.0, 128.0])
    hz_tex = value_noise(h, w, 96, 7)
    flick = value_noise(4, N + 8, 6, 11)[0]          # 1-D slow noise for the neon flicker
    rng = np.random.default_rng(3)
    drops = dict(x=rng.random(260) * w, y=rng.random(260) * h, z=rng.uniform(0.25, 1.0, 260))
    yy, xx = np.mgrid[0:h, 0:w].astype(np.float32)
    src = S.get("file") or S.get("path")
    src = src if src and os.path.isabs(src) else os.path.join(ROOT, src) if src else None
    base = (cv2.resize(np.array(Image.open(src).convert("RGB")), (w, h), interpolation=cv2.INTER_AREA).astype(np.float32)
            if src and os.path.exists(src) else np.zeros((h, w, 3), np.float32))
    base_g = dict(geo={"shift": min(amp, 0.3 * (W0 if move == "truck" else H0)) * sc} if move in ("truck", "tilt_up")
                  else {"scale_end": 1 + amp})

    def cam_e(f):  # camera progress with hold-in / settle
        return ease((f - HOLD_IN) / max(1, N - HOLD_IN - HOLD_OUT))

    def affine(g, e):
        if "shift" in g["geo"]:
            d = (e - 0.5) * g["geo"]["shift"]
            return np.float32([[1, 0, -d], [0, 1, 0]]) if move == "truck" else np.float32([[1, 0, 0], [0, 1, d]])
        k = 1 + (g["geo"]["scale_end"] - 1) * e
        return np.float32([[k, 0, fx - k * fx], [0, k, fy - k * fy]])

    def ground_warp(g, im, e):
        G = g["ground"]
        t = np.clip((yy - G["y0"]) / max(1.0, h - G["y0"]), 0, 1)
        p = G["p_far"] + (G["p_near"] - G["p_far"]) * t       # parallax ramps toward the lens
        if move in ("truck", "tilt_up"):
            d = (e - 0.5) * np.minimum(amp * p, 0.3 * (W0 if move == "truck" else H0)) * sc
            mx, my = (xx + d, yy) if move == "truck" else (xx, yy - d)
        else:
            k = 1 + (np.minimum(1 + amp * p, 1.8) - 1) * e
            mx, my = fx + (xx - fx) / k, fy + (yy - fy) / k
        return cv2.remap(im, mx.astype(np.float32), my.astype(np.float32), cv2.INTER_LINEAR,
                         borderMode=cv2.BORDER_REPLICATE)

    def secondary(g, f):
        im = g["im"]
        if not g["kind"]: return im
        f2 = f - (f % 2)                                  # drawings on twos
        y0, y1, x0, x1 = g["bbox"]
        mx, my = xx.copy(), yy.copy()
        if "ripple" in g["kind"]:                         # on ones: water reads alive
            wm = water_mask if water_mask is not None else (yy > y0).astype(np.float32)
            mx += 1.6 * np.sin(2 * np.pi * (yy / 23.0 + f / 30.0)) * wm
            my += 0.8 * np.sin(2 * np.pi * (xx / 41.0 + f / 37.0)) * wm
        if "sway" in g["kind"]:
            rel = np.clip((float(y1) - yy) / max(1.0, float(y1 - y0)), 0, 1)
            mx += 2.2 * rel * np.sin(2 * np.pi * f2 / 48.0)
        if "breathe" in g["kind"]:
            k = 1 + 0.006 * np.sin(2 * np.pi * f2 / 40.0)
            my = float(y1) - (float(y1) - my) / k
        return cv2.remap(im, mx.astype(np.float32), my.astype(np.float32), cv2.INTER_LINEAR, borderMode=cv2.BORDER_REPLICATE)

    mid_idx = min(range(len(sheets)), key=lambda i: abs(sheets[i]["plane"] - 4))
    tmp = os.path.join(fd, "shot.tmp.mp4")
    ff = subprocess.Popen(["ffmpeg", "-loglevel", "error", "-y", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{w}x{h}",
                           "-r", str(FPS), "-i", "-", "-c:v", "libx264", "-pix_fmt", "yuv420p", "-crf", "20",
                           "-preset", "veryfast", "-movflags", "+faststart", tmp], stdin=subprocess.PIPE)
    for f in range(N):
        e = cam_e(f)
        # safety plate: the source frame on the hero's law, so any tear reveals real image, not fill
        out = cv2.warpAffine(base, affine(base_g, e), (w, h), borderMode=cv2.BORDER_REPLICATE)
        haze_done = False
        for i, g in enumerate(sheets):
            if not haze_done and g["meta"]["parallax"] > 1.0 and haze > 0.02:   # haze sits between MG and nearer planes
                ox = int((f * 0.6) % (2 * 96)); hz = hz_tex[:h, ox:ox + w][..., None]
                a = np.clip(0.10 * haze * (0.6 + 0.8 * hz), 0, 0.12)
                out = out * (1 - a) + haze_col * a; haze_done = True
            im = secondary(g, f)
            Mx = affine(g, e)
            if "ground" in g:
                wim = ground_warp(g, im, e)
            else:
                if "shift" in g["geo"]:
                    im = cv2.copyMakeBorder(im, pad, pad, pad, pad, cv2.BORDER_REPLICATE)
                    Mx = Mx.copy(); Mx[0, 2] -= pad; Mx[1, 2] -= pad
                wim = cv2.warpAffine(im, Mx, (w, h), flags=cv2.INTER_LINEAR, borderMode=cv2.BORDER_CONSTANT)
            a = wim[..., 3:4] / 255.0
            out = out * (1 - a) + wim[..., :3] * a
            if i == mid_idx and glow.any():
                gw = cv2.warpAffine(glow, affine(g, e), (w, h))
                fl = 0.28 + 0.14 * flick[(f - f % 2) // 2 % len(flick)]
                out = out + fl * gw
        if rain:
            dr = np.zeros((h, w), np.float32)
            for x, y, z in zip(drops["x"], drops["y"], drops["z"]):
                yy0 = (y + f * 26 * z) % (h + 40) - 20
                cv2.line(dr, (int(x - 3 * z), int(yy0)), (int(x), int(yy0 + 16 * z)), float(0.35 * z), 1, cv2.LINE_AA)
            out = out * (1 - dr[..., None]) + 225 * dr[..., None]
        ff.stdin.write(np.clip(out, 0, 255).astype(np.uint8).tobytes())
    ff.stdin.close(); ff.wait()
    os.replace(tmp, os.path.join(fd, "shot.mp4"))
    Image.fromarray(np.clip(out, 0, 255).astype(np.uint8)).save(os.path.join(fd, "last.jpg"), quality=88)

    fx_list = (["rain (prompt)"] if rain else []) + (["haze drift %.2f" % haze] if haze > 0.02 else []) + \
              (["neon flicker (glow pass)"] if glow.any() else []) + \
              sorted({f"{k}: {g['meta']['label']}" for g in sheets for k in g["kind"]})
    xs = dict(id=sid, fps=FPS, frames=N, size=[w, h], camera=dict(move=move, why=cam.get("why"), amplitude=amp),
              timeline=[dict(frame=1, exposure=HOLD_IN, action="hold — establish (moving hold on secondary)"),
                        dict(frame=HOLD_IN + 1, exposure=N - HOLD_IN - HOLD_OUT, action=f"{move.replace('_', ' ')} · slow-in/slow-out · near planes travel more"),
                        dict(frame=N - HOLD_OUT + 1, exposure=HOLD_OUT, action="settle — hold for the cut")],
              fx=fx_list, keys_to_draw=M.get("xsheet") or [],
              note="camera + secondary action are rendered; character keys in keys_to_draw are NOT drawn yet")
    json.dump(xs, open(os.path.join(fd, "xsheet.json"), "w"), indent=1)
    return xs


# --------------------------------------------------------------------------- reels + riverbed
def job_of(fname):
    m = re.search(r"([0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12})_(\d)\.png$", fname)
    return (m.group(1), m.group(2)) if m else (None, None)


def resolve_shot(fname, have):
    j, k = job_of(fname)
    if not j: return None, False
    if f"{j}_{k}" in have: return f"{j}_{k}", True
    alt = [s for s in have if s.startswith(j)]
    return (alt[0], False) if alt else (None, False)       # same Midjourney job, sibling variant


def tc(fr):
    s, f = divmod(fr, FPS); m, s = divmod(s, 60); hh, m = divmod(m, 60)
    return f"{hh:02d}:{m:02d}:{s:02d}:{f:02d}"


def build_reels():
    os.makedirs(FILM, exist_ok=True)
    D = json.load(open(os.path.join(ROOT, "_city", "districts.json")))
    DM = {d["id"]: d for d in D["districts"]}
    have = set(shot_dirs())
    index = []

    poems_meta = {}
    pj_path = os.path.join(FILM, "poems.json")
    if os.path.exists(pj_path):
        for pm in json.load(open(pj_path)):
            poems_meta[pm["num"]] = pm

    for P in D["poems"]:
        d = DM[P["district"]]
        pm = poems_meta.get(P["num"], {})
        clips = []
        for n in P["images"]:
            fname = D["files"][str(n)]
            sid, exact = resolve_shot(fname, have)
            mp4 = os.path.join(OUT, sid, "film", "shot.mp4") if sid else None
            if not sid or not os.path.exists(mp4): continue
            xs = json.load(open(os.path.join(OUT, sid, "film", "xsheet.json")))
            M = json.load(open(os.path.join(OUT, sid, "multiplane", "multiplane.json")))
            S = json.load(open(os.path.join(OUT, sid, "shot.json")))
            clips.append(dict(n=n, sid=sid, exact=exact, mp4=mp4, frames=xs["frames"], xs=xs, M=M, S=S))
        if not clips: continue
        # cut with dissolves
        out = os.path.join(FILM, f"poem_{P['num']}.mp4")
        if not os.path.exists(out):
            args = ["ffmpeg", "-loglevel", "error", "-y"]
            for c in clips: args += ["-i", c["mp4"]]
            if len(clips) == 1:
                args += ["-c", "copy", out]
            else:
                fc, last, off = [], "[0:v]", 0.0
                for i in range(1, len(clips)):
                    off += clips[i - 1]["frames"] / FPS - XF / FPS
                    lab = f"[v{i}]"
                    fc.append(f"{last}[{i}:v]xfade=transition=fade:duration={XF / FPS:.3f}:offset={off:.3f}{lab}")
                    last = lab
                args += ["-filter_complex", ";".join(fc), "-map", last, "-c:v", "libx264", "-pix_fmt", "yuv420p",
                         "-crf", "20", "-preset", "veryfast", "-movflags", "+faststart", out]
            subprocess.run(args, check=True)
        # timecodes
        t = 0
        for i, c in enumerate(clips):
            c["start"] = t; c["end"] = t + c["frames"]; t = c["end"] - XF
        rb = riverbed(P, d, clips, pm)
        json.dump(rb, open(os.path.join(FILM, f"riverbed_{P['num']}.json"), "w"), indent=1, ensure_ascii=False)

        movs = pm.get("movements", [])
        shot_list = []
        for i, c in enumerate(clips):
            mov = movs[min(i, len(movs) - 1)] if movs else {}
            mov_lbl = mov.get("label", "")
            mov_ln = mov.get("line", "")
            act = c["M"].get("action") or (f"[{mov_lbl}] {mov_ln[:80]}…" if mov_lbl else "environmental hold")
            shot_list.append(dict(n=c["n"], id=c["sid"], exact=c["exact"], start=tc(c["start"]), end=tc(c["end"]),
                                  move=c["xs"]["camera"]["move"], fx=c["xs"]["fx"], action=act,
                                  movement_label=mov_lbl, movement_line=mov_ln,
                                  keys=7, shot_mp4=f"out/{c['sid']}/film/shot.mp4"))

        index.append(dict(num=P["num"], title=P["title"], district=d["id"], district_name=d["name"], color=d["color"],
                          tagline=pm.get("tagline", ""), window=pm.get("window", [0, 120]),
                          drone=pm.get("drone", {"base": 16.35, "steps": [0]}),
                          score=pm.get("score", {"engine": "malhun", "mode": "phrygian"}),
                          movements=movs,
                          mp4=f"film/poem_{P['num']}.mp4", riverbed=f"film/riverbed_{P['num']}.json",
                          seconds=round((clips[-1]["end"]) / FPS, 2),
                          shots=shot_list))
        print(f"poem {P['num']} {P['title']}: {len(clips)} shots → {out}")
    with open(os.path.join(FILM, "reels.js"), "w") as fh:
        fh.write("window.REELS = " + json.dumps(index, indent=2, ensure_ascii=False) + ";\n")
    print(f"wrote {len(index)} reels")


def riverbed(P, d, clips, pm=None):
    """Golden Riverbed record. Riverbed = what the district and the measured shots fix; flow = what may vary."""
    pal = f"body {', '.join(d['body'])}; glow {', '.join(d['glow'])}"
    pm = pm or {}
    movs = pm.get("movements", [])
    verse_text = " ".join(m.get("line", "") for m in movs) if movs else P.get("title", "")
    patches, segs, bridges = [], [], []
    for i, c in enumerate(clips):
        M, S, xs = c["M"], c["S"], c["xs"]
        camh = S["camera"].get("height_m")
        mov = movs[min(i, len(movs) - 1)] if movs else {}
        hold = [f"camera law: {xs['camera']['move']} — {xs['camera']['why']}",
                f"camera height {camh} m, pitch {S['camera'].get('pitch_deg')}°, hfov {S['camera'].get('fov_h_deg')}°" if camh else
                f"no recovered ground; hfov {S['camera'].get('fov_h_deg')}°",
                f"plane order: " + " > ".join(f"{p['id']} {p['name']}" for p in M["planes"] if p["area_frac"] > 0.02)]
        vary = xs["fx"] + (M.get("secondary") or [])
        seed = (M.get("action") or mov.get("line") or "") + " | source frame prompt: " + S.get("prompt", "")[:260]
        patches.append(dict(patch_id=f"{P['num']}.{i + 1}", start_time=tc(c["start"]), end_time=tc(c["end"]),
                            movement_label=mov.get("label", ""), movement_line=mov.get("line", ""),
                            local_event=M.get("action") or mov.get("line") or S.get("prompt", "")[:120],
                            camera_environment=f"{d['name']} · {S['camera'].get('shot_class')}",
                            what_must_hold=hold, what_may_vary=vary, local_seed=seed))
        segs.append(dict(segment_id=f"{P['num']}.{i + 1}", purpose="image-to-video from this shot's first frame",
                         movement_line=mov.get("line", ""),
                         prompt=(f"Start frame is fixed (use shot {c['sid']} image or cel). {xs['camera']['move'].replace('_', ' ')} "
                                 f"camera, slow-in/slow-out, near planes travel more than far; {d['name']}: {d['signature']}. "
                                 f"Action: {M.get('action') or mov.get('line') or 'environmental hold, 2D poet character on twos'}. "
                                 + (f"Beats: {' → '.join(M['beats'])}. " if M.get('beats') else "") + f"Keep palette {pal}.")))
        if i:
            a = clips[i - 1]
            bridges.append(dict(bridge_id=f"{P['num']}.b{i}", **{"from": a["sid"], "to": c["sid"]},
                                function="dissolve 12 frames; carry haze colour and screen direction across the cut",
                                prompt=(f"Last frame of {a['sid'][:8]} ({a['xs']['camera']['move']}) dissolves into first frame of "
                                        f"{c['sid'][:8]} ({c['xs']['camera']['move']}); keep {d['name']} light: {d['signature']}; "
                                        f"no new subjects appear during the dissolve.")))
    return {
        "engine": {"name": "PRIME ENGINE", "version": "8.0", "mode": "GOLDEN_RIVERBED"},
        "source_profile": {"source_type": "hybrid", "source_title": f"WYGWYL {P['num']} · {P['title']}",
                           "core_idea": next((x for x in d["poems"] if x.startswith(P["num"])), P["title"]),
                           "generative_goal": "animate the poem's placed Midjourney views as one continuous multiplane sequence",
                           "recommended_form": "patch_chain"},
        "riverbed": {"core_identity": f"{d['name']} — {d['mood']}",
                     "hinge_conditions": [d["signature"], f"architecture: {d['arch']}", f"materials: {d['materials']}"],
                     "identity_constraints": [f"measured palette — {pal}", "each patch starts on its source frame's composition"],
                     "governing_rules": ["camera moves only along each shot's recorded law", "near planes move more than far planes",
                                         "drawings on twos, camera on ones"],
                     "continuity_anchors": [f"district {d['name']} ({d['realm']})", "haze colour carried across dissolves"],
                     "invariants": ["horizon and vanishing point of each source frame", "plane depth order"],
                     "mistake_conditions": ["whole-frame zoom with no parallax", "new characters invented outside the x-sheet",
                                            "palette drifting outside body/glow swatches"]},
        "flow": {"mutable_variables": ["rain density", "haze drift", "neon flicker", "water ripple", "fabric sway"],
                 "atmospheric_range": [d["mood"]], "surface_detail_range": [d["materials"]],
                 "transformation_range": ["light flicker", "breathing holds"],
                 "camera_variation_range": ["amplitude ±30% of recorded", "hold length 0.5–1.5 s"],
                 "permitted_drift": ["secondary action timing", "particle placement"],
                 "forbidden_drift": ["camera direction reversal", "re-staging the hero", "time-of-day change"]},
        "diegesis": {"premise": next((x for x in d["poems"] if x.startswith(P["num"])), P["title"]),
                     "world_rules": [d["eras"]], "core_entities": ["poet"], "core_locations": d["key"],
                     "dominant_relations": d["moments"]},
        "sequence_architecture": {"macro_units": [{"unit_id": P["num"], "function": P["title"],
                                                   "riverbed_role": d["name"], "flow_behavior": "patch chain with dissolves",
                                                   "beats": [{"beat_id": p["patch_id"], "shift": "cut (dissolve)",
                                                              "transition_channel": "dissolve", "prompt_burden": "camera + secondary",
                                                              "patches": [p]} for p in patches]}]},
        "prompt_architecture": {
            "master_prompt_strategy": "lock district light and palette once; every segment inherits it and adds only its shot's action",
            "continuity_law": "each patch begins on its source frame; camera follows the recorded law; dissolves carry haze colour",
            "style_law": "classical multiplane: painted plates, held drawings on twos, restrained ink on near planes only",
            "transition_law": "12-frame dissolves; no whip pans unless the shot law says truck",
            "negative_constraints": ["no whole-frame zoom", "no extra characters", "no text overlays", "no lens flares not in glow pass"],
            "master_prompt": (f"{d['name']}, {d['realm']}. {d['mood']}. {d['signature']}. Architecture: {d['arch']}. "
                              f"Materials: {d['materials']}. Palette {pal}. Multiplane camera, near planes move more than far, "
                              f"drawings held on twos, camera eased in and out."),
            "segment_prompts": segs, "bridge_prompts": bridges,
            "constraint_prompts": [{"constraint_id": "poem_text", "purpose": "the poem's own lines are verified and timed to this reel",
                                    "prompt": verse_text}]},
        "generation_notes": {"model_behavior_priority": ["hold composition", "respect camera law", "palette"],
                             "stability_targets": ["architecture", "horizon"], "controlled_variability_targets": ["weather", "light flicker"],
                             "failure_risks": ["image-to-video models re-stage figures", "disocclusion holes where back-paint is thin"]},
        "conform": {"edl_requested": False, "otio_requested": False, "edl": None, "otio": None}}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--match", nargs="*"); ap.add_argument("--all", action="store_true"); ap.add_argument("--reels-only", action="store_true")
    a = ap.parse_args()
    if not a.reels_only:
        ids = shot_dirs()
        if a.match: ids = [i for i in ids if any(m in i for m in a.match)]
        elif not a.all: ids = ids[:1]
        for k, sid in enumerate(ids):
            xs = render_shot(sid)
            print(f"[{k + 1}/{len(ids)}] {sid[:8]} {xs['camera']['move']:<10} {xs['frames']}f  fx={xs['fx']}", flush=True)
    if a.all or a.reels_only: build_reels()


if __name__ == "__main__":
    main()
