#!/usr/bin/env python3
"""
Cartoon video: keyframe the real pipeline, propagate the cel with optical flow.

  1. extract    ffmpeg → frames at --fps (default 12, "on twos"), scaled to --width
  2. keyframes  every --every seconds, plus a forced keyframe at every scene cut (histogram jump)
  3. cartoon    each keyframe goes through the SAME stack as stills:
                  analyze.analyze (DINO+SAM+OneFormer+DepthPro) → multiplane.build → cartoon.render
                  then, by --style:
                    angular (default)  scene_program.Scene refine → program/frame0.png : the angular filled-region drawing
                                       (irregular polygons, light gradients, no outlines; see shots/ANGULAR_STUDIO_PROMPT.md)
                    cel                cartoon/cel.png : flats + ink + glow
  4. propagate  every in-between frame = the two neighbouring keyframe cels, warped by Farneback flow
                (in-between → keyframe) and blended by time distance × photometric agreement
                (where a warp disagrees with the real frame — occlusion, new content — that keyframe loses weight).
                Never blends across a scene cut.
  5. encode     cartoon.mp4 (+ compare.mp4 original|cartoon) with the source audio

Everything lands in shots/video/<clip>/ ; the still-image data (shots/out, *_data.js) is not touched.

Usage:
  .venv-shots/bin/python shots/cartoon_video.py clip.mp4
  .venv-shots/bin/python shots/cartoon_video.py clip.mp4 --every 0.75 --fps 12 --width 1024 --start 0 --dur 10
  .venv-shots/bin/python shots/cartoon_video.py clip.mp4 --prompt "rainy neon street, a courier on a bike"   # optional detector hints
  .venv-shots/bin/python shots/cartoon_video.py clip.mp4 --reuse        # reuse extracted frames + finished keyframe cels
"""
import argparse, glob, json, os, re, shutil, subprocess, sys
import numpy as np
import cv2
from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, HERE)


def sh(args):
    r = subprocess.run(args, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
    if r.returncode: sys.exit(f"{args[0]} failed:\n{r.stdout[-2000:]}")
    return r.stdout


def extract(video, fdir, fps, width, start, dur):
    os.makedirs(fdir, exist_ok=True)
    cmd = ["ffmpeg", "-y", "-loglevel", "error"]
    if start: cmd += ["-ss", str(start)]
    cmd += ["-i", video]
    if dur: cmd += ["-t", str(dur)]
    cmd += ["-vf", f"fps={fps},scale={width}:-2", os.path.join(fdir, "%05d.png")]
    sh(cmd)
    return sorted(glob.glob(os.path.join(fdir, "*.png")))


def hist(img):
    h = cv2.calcHist([cv2.cvtColor(img, cv2.COLOR_BGR2HSV)], [0, 1], None, [16, 8], [0, 180, 0, 256])
    return cv2.normalize(h, h).flatten()


def pick_keyframes(frames, fps, every, cut_thresh):
    """→ (keyframe indices, set of cut indices = first frame of a new scene)"""
    step = max(1, round(every * fps)); keys, cuts = [0], set()
    prev = hist(cv2.imread(frames[0])); last = 0
    for i in range(1, len(frames)):
        cur = hist(cv2.imread(frames[i]))
        if cv2.compareHist(prev, cur, cv2.HISTCMP_CORREL) < cut_thresh:
            cuts.add(i); keys.append(i); last = i
        elif i - last >= step:
            keys.append(i); last = i
        prev = cur
    return keys, cuts


def cartoonify_keyframes(idxs, frames, work, hints, reuse, style="angular", rounds=10, lam=0.15):
    """Run the real stack on each keyframe; return {frame index: cel BGR uint8}."""
    import analyze, multiplane, cartoon                     # heavy imports only when needed
    out = os.path.join(work, "out"); os.makedirs(out, exist_ok=True)
    analyze.OUT = multiplane.OUT = cartoon.OUT = out         # keep video shots out of the stills' shots/out
    if style == "angular":
        import scene_program; scene_program.OUT = out
    kdir = os.path.join(work, "keyframes"); os.makedirs(kdir, exist_ok=True)
    clip = os.path.basename(work)
    cels, M = {}, None
    notes = {}
    for n, i in enumerate(idxs):
        name = f"kf{i:05d}_0.png"; path = os.path.join(kdir, name)
        shutil.copy(frames[i], path)
        job = f"vid-{re.sub(r'[^a-z0-9]+', '-', clip.lower())}-kf{i:05d}"; sid = f"{job}_0"
        cel_p = os.path.join(out, sid, "program", "frame0.png") if style == "angular" else os.path.join(out, sid, "cartoon", "cel.png")
        if not (reuse and os.path.exists(cel_p)):
            if M is None: M = analyze.Models()
            rec = analyze.analyze(M, path, dict(job_id=job, prompt=hints, files=[name]), {})
            sj = os.path.join(out, sid, "shot.json")
            rec["file"] = os.path.relpath(path, ROOT)         # downstream stages read ROOT/<file>
            json.dump(rec, open(sj, "w"), indent=2, default=float)
            multiplane.build(sid, notes)
            cartoon.render(sid)
            if style == "angular":
                sc = scene_program.Scene(sid, lam=lam); sc.refine(rounds); sc.export()
        cel = cv2.imread(cel_p)
        h, w = cv2.imread(frames[i]).shape[:2]
        if cel.shape[:2] != (h, w): cel = cv2.resize(cel, (w, h), interpolation=cv2.INTER_AREA)
        cels[i] = cel
        print(f"  keyframe {n + 1}/{len(idxs)}  frame {i}  → {sid[-18:]}"); sys.stdout.flush()
    return cels


def flow_to(src_gray, dst_gray, scale=0.5):
    """dense flow such that for each pixel of dst, flow gives its location in src (cv2.remap-ready map)."""
    h, w = dst_gray.shape
    a = cv2.resize(dst_gray, None, fx=scale, fy=scale, interpolation=cv2.INTER_AREA)
    b = cv2.resize(src_gray, None, fx=scale, fy=scale, interpolation=cv2.INTER_AREA)
    f = cv2.calcOpticalFlowFarneback(a, b, None, 0.5, 4, 21, 3, 7, 1.5, 0)
    f = cv2.resize(f, (w, h), interpolation=cv2.INTER_LINEAR) / scale
    gx, gy = np.meshgrid(np.arange(w, dtype=np.float32), np.arange(h, dtype=np.float32))
    return gx + f[..., 0], gy + f[..., 1]


def warp(img, mapx, mapy):
    return cv2.remap(img, mapx, mapy, cv2.INTER_LINEAR, borderMode=cv2.BORDER_REPLICATE)


def propagate(i, frames_bgr, a, b, cels, tau=14.0):
    """Cel for frame i from keyframes a<=i<=b (b may be None = hold forward from a only)."""
    cur = frames_bgr(i); g = cv2.cvtColor(cur, cv2.COLOR_BGR2GRAY)
    out_cels, ws = [], []
    for k, base in ((a, None), (b, None)):
        if k is None: continue
        if k == i: return cels[k]
        gk = cv2.cvtColor(frames_bgr(k), cv2.COLOR_BGR2GRAY)
        mx, my = flow_to(gk, g)
        w_time = (b - i) / (b - a) if (k == a and b is not None) else (i - a) / (b - a) if k == b else 1.0
        # photometric agreement: does the warped real keyframe look like the real current frame?
        err = np.abs(warp(frames_bgr(k), mx, my).astype(np.float32) - cur.astype(np.float32)).mean(2)
        err = cv2.GaussianBlur(err, (0, 0), 6)
        out_cels.append(warp(cels[k], mx, my).astype(np.float32))
        ws.append(w_time * np.exp(-err / tau) + 1e-4)
    if len(out_cels) == 1: return out_cels[0].astype(np.uint8)
    wsum = ws[0] + ws[1]
    return ((out_cels[0] * (ws[0] / wsum)[..., None] + out_cels[1] * (ws[1] / wsum)[..., None])).astype(np.uint8)


def main():
    ap = argparse.ArgumentParser(description="cartoonify a video: keyframe the pipeline, propagate with optical flow")
    ap.add_argument("video"); ap.add_argument("--fps", type=float, default=12); ap.add_argument("--width", type=int, default=1024)
    ap.add_argument("--every", type=float, default=1.0, help="seconds between keyframes")
    ap.add_argument("--cut", type=float, default=0.55, help="histogram correlation below this = scene cut")
    ap.add_argument("--start", type=float, default=0); ap.add_argument("--dur", type=float, default=0)
    ap.add_argument("--prompt", default="", help="optional text hints for the detector (objects, setting)")
    ap.add_argument("--reuse", action="store_true"); ap.add_argument("--no-compare", action="store_true")
    ap.add_argument("--style", choices=["angular", "cel"], default="angular", help="angular = scene_program filled-region drawing; cel = cartoon.py flats+ink")
    ap.add_argument("--rounds", type=int, default=10, help="scene_program refine rounds per keyframe (angular)")
    ap.add_argument("--lam", type=float, default=0.15, help="scene_program complexity penalty: higher = fewer, bigger shapes")
    a = ap.parse_args()

    clip = re.sub(r"[^A-Za-z0-9_-]+", "_", os.path.splitext(os.path.basename(a.video))[0])
    work = os.path.join(HERE, "video", clip); fdir = os.path.join(work, "frames")
    if os.path.isdir(fdir) and not a.reuse: shutil.rmtree(fdir)
    frames = sorted(glob.glob(os.path.join(fdir, "*.png"))) if a.reuse else []
    if not frames:
        print(f"[1/4] extracting {a.fps:g} fps @ {a.width}px"); frames = extract(a.video, fdir, a.fps, a.width, a.start, a.dur)
    n = len(frames); print(f"      {n} frames ({n / a.fps:.1f}s)")

    print("[2/4] keyframes + scene cuts")
    keys, cuts = pick_keyframes(frames, a.fps, a.every, a.cut)
    print(f"      {len(keys)} keyframes, {len(cuts)} cuts at frames {sorted(cuts)}")

    print("[3/4] cartoonifying keyframes with the still pipeline")
    cels = cartoonify_keyframes(keys, frames, work, a.prompt, a.reuse, a.style, a.rounds, a.lam)

    print("[4/4] propagating")
    cache = {}
    def fb(i):
        if i not in cache:
            if len(cache) > 40: cache.pop(next(iter(cache)))
            cache[i] = cv2.imread(frames[i])
        return cache[i]
    odir = os.path.join(work, "cel_frames"); shutil.rmtree(odir, ignore_errors=True); os.makedirs(odir)
    cdir = os.path.join(work, "cmp_frames"); shutil.rmtree(cdir, ignore_errors=True); os.makedirs(cdir)
    for i in range(n):
        prev_k = max(k for k in keys if k <= i)
        nxt = [k for k in keys if k > i]
        nk = nxt[0] if nxt and nxt[0] not in cuts else None      # never blend across a scene cut
        cel = propagate(i, fb, prev_k, nk, cels)
        cv2.imwrite(os.path.join(odir, f"{i + 1:05d}.png"), cel)
        if not a.no_compare: cv2.imwrite(os.path.join(cdir, f"{i + 1:05d}.png"), np.hstack([fb(i), cel]))
        if i % 24 == 0: print(f"      frame {i}/{n}"); sys.stdout.flush()

    def encode(src, dst, extra=()):
        cmd = ["ffmpeg", "-y", "-loglevel", "error", "-framerate", f"{a.fps:g}", "-i", os.path.join(src, "%05d.png")]
        if a.video: cmd += ["-ss", str(a.start)] + (["-t", str(a.dur)] if a.dur else []) + ["-i", a.video, "-map", "0:v", "-map", "1:a?"]
        cmd += ["-c:v", "libx264", "-pix_fmt", "yuv420p", "-crf", "17", "-c:a", "aac", "-shortest", dst]
        sh(cmd)
    encode(odir, os.path.join(work, "cartoon.mp4"))
    if not a.no_compare: encode(cdir, os.path.join(work, "compare.mp4"))
    print(f"done → {os.path.relpath(os.path.join(work, 'cartoon.mp4'), ROOT)}"
          + ("" if a.no_compare else f"  (+ compare.mp4: original | cartoon)"))


if __name__ == "__main__":
    main()
