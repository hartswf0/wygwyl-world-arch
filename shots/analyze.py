#!/usr/bin/env python3
"""
Shot analysis — Phase 1 prototype.

For each Midjourney image:
  1. prompt  -> structured hints (objects, prompted camera, height hint, district)
  2. Grounding DINO (prompt + district + generic vocab) -> boxes -> SAM 2 -> instance masks
  3. OneFormer ADE20K -> stuff map (sky / ground / building / water ...)
  4. Depth Pro -> metric-ish depth + estimated focal length / FOV
  5. ground mask -> 3D -> RANSAC plane -> camera height, pitch, roll, horizon line
  6. known-size objects (people, doors, containers...) -> metric rescale of height
  7. outputs: shot.json, overlay.jpg, depth.jpg, layers/{fg,mg,bg}.png, points.ply

Usage:
  .venv-shots/bin/python shots/analyze.py                 # default 6-image test set
  .venv-shots/bin/python shots/analyze.py --all           # all 100 images
  .venv-shots/bin/python shots/analyze.py --match catwalk # filename substring(s)
"""
import argparse, glob, json, math, os, re, sys, time

os.environ.setdefault("PYTORCH_ENABLE_MPS_FALLBACK", "1")
import numpy as np
import torch
import cv2
from PIL import Image

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, "shots", "out")
DEV = "mps" if torch.backends.mps.is_available() else ("cuda" if torch.cuda.is_available() else "cpu")

DEFAULT_SET = [
    "underpass_shadow-pool_ritual_in_Naraka_Market_water_d3d25411",   # naraka · ground level, water
    "The_Orange_Catwalk_elevated_concrete_path_glowing_w_3a0da51b",  # haze · elevated walkway, figure
    "indigo_hive_spires_with_cold_grandeur_and_signal_li_3603f621-18f4-4711-ab93-946cab123329_0",  # hive · skyline
    "rooftop_laundry_beneath_Ankhu_Spires_metallic_hummi_e9c68c53-270a-40d3-be47-b19b47b4068c_0",  # ankhu · rooftop
    "wet_stone_steps_beneath_mountain_in_Cenotaph_Rail_d",           # cenotaph · steps
    "Atlantis_City_central_plaza_sweeping_aerial_view_of",           # plaza · drone aerial
]

# ----------------------------------------------------------------------------- vocab
# Distilled from _city/districts.json "arch" fields: concrete, detectable nouns.
DISTRICT_VOCAB = {
    "naraka":   ["shipping container", "awning", "string lights", "cable", "air conditioner", "stairs", "shop stall", "lantern"],
    "haze":     ["concrete catwalk", "pillar", "stairs", "smokestack", "bridge", "chair", "railing"],
    "hive":     ["skyscraper", "spire", "lattice tower", "beacon light", "atrium"],
    "overseer": ["pipe", "tower", "moon", "palace ruin", "skywalk"],
    "bay":      ["lagoon", "boardwalk", "bridge", "colonnade", "canal", "dam wall", "graffiti"],
    "commons":  ["satellite dish", "crowd", "canopy", "glowing cube", "cathedral", "glass tower"],
    "plaza":    ["light fence", "gate", "terrace", "crystal tree", "reflecting pool"],
    "ankhu":    ["spire", "arch", "market stall", "platform", "hanging garden", "sky bridge", "palm tree", "laundry line", "elevator shaft"],
    "cenotaph": ["rusted platform", "viaduct arch", "stone steps", "lake", "mountain", "bell tower", "rail track"],
    "arcade":   ["escalator", "led screen", "neon sign", "chrome door", "storefront"],
    "temple":   ["portico", "reflecting pool", "column", "tree"],
    "ascent":   ["arch", "parade", "moon", "spire", "flower"],
}
GENERIC = ["person", "building", "window", "door", "sign", "street lamp", "railing", "stairs",
           "vehicle", "tree", "water", "street", "floor", "sky", "cloud", "wall"]
# Known real-world heights (m) for metric rescaling.
KNOWN_H = {"person": 1.70, "door": 2.10, "shipping container": 2.59, "vehicle": 1.50, "chair": 0.85,
           "child": 1.25, "silhouette": 1.70}
_HP = os.path.join(ROOT, "shots", "prompt_hints.json")
CURATED = {k: v for k, v in json.load(open(_HP)).items() if not k.startswith("_")} if os.path.exists(_HP) else {}
# Phrases that are ground-like for the plane fit.
GROUND_RE = re.compile(r"\b(ground|floor|street|road|water|pool|catwalk|walkway|path|steps|stairs|plaza|"
                       r"sidewalk|platform|deck|rooftop|boardwalk|pavement|asphalt|lake|lagoon|canal)\b")
ADE_GROUND = {"floor", "flooring", "road", "route", "grass", "sidewalk", "pavement", "earth", "ground", "water", "sea",
              "sand", "path", "stairs", "steps", "runway", "river", "bridge", "stairway", "staircase", "step", "stair",
              "dirt track", "field", "land", "soil", "pier", "wharf", "swimming pool", "lake", "rug", "carpet"}
STOP = re.compile(r"(iso|mm\b|f/|canon|nikon|leica|sony|panasonic|red komodo|iphone|lens|shutter|exposure|"
                  r"emotional|mood|undercurrent|perspective|style|inspired|sound|ambient|tone|feel|sense|--|"
                  r"camera|shot|frame|pan\b|focus|cinematist|surveyor|cartographer|\d+s\b)", re.I)

HEIGHT_HINTS = [("aerial", r"aerial|drone|bird'?s.eye|from above|satellite"),
                ("elevated", r"high-altitude|observation deck|platform level|elevated|overlook|rooftop|skyway|catwalk"),
                ("ground", r"street level|ground level|beneath|underpass|alley|steps|stairwell|looking up|worm")]


def load_district_index():
    fs = sorted([os.path.basename(f) for f in glob.glob(os.path.join(ROOT, "*.png"))], key=str.lower)
    pal = json.load(open(os.path.join(ROOT, "_city", "palettes.json")))
    idx = {}
    for d, v in pal.items():
        for i in v["images"]:
            if 1 <= i <= len(fs):
                idx[fs[i - 1]] = (d, i)
    return idx


def parse_prompt(prompt):
    body = prompt.split("--")[0]
    p = {}
    m = re.search(r"(\d{2,3})\s?mm", body); p["focal_mm"] = int(m.group(1)) if m else None
    m = re.search(r"ISO\s?([\d,]+)", body, re.I); p["iso"] = int(m.group(1).replace(",", "")) if m else None
    m = re.search(r"\b(Canon[^,.;]*?|Nikon \w+|Leica \w+[-\w]*|Sony [\w-]+|Panasonic \w+|RED Komodo[^,;]*?|iPhone \w+)(?=[,;.]| \d)", body)
    p["body"] = m.group(1).strip() if m else None
    p["height_hint"] = next((k for k, rx in HEIGHT_HINTS if re.search(rx, body, re.I)), None)
    m = re.search(r"--ar (\d+):(\d+)", prompt); p["ar"] = f"{m.group(1)}:{m.group(2)}" if m else None
    # object phrases: short comma/semicolon chunks without camera/emotion words
    objs = []
    for ch in re.split(r"[,;:.]| and | with ", body):
        ch = re.sub(r"[^\w\s'-]", " ", ch).strip().lower()
        ch = re.sub(r"^(a|an|the|of|in|on|under|beneath|above)\s+", "", ch)
        if 2 < len(ch) and len(ch.split()) <= 4 and not STOP.search(ch) and not re.match(r"^\d", ch):
            objs.append(ch)
    p["phrases"] = list(dict.fromkeys(objs))[:20]
    return p


# ----------------------------------------------------------------------------- models
class Models:
    def __init__(self):
        from transformers import (AutoProcessor, AutoModelForZeroShotObjectDetection,
                                  OneFormerProcessor, OneFormerForUniversalSegmentation,
                                  DepthProImageProcessor, DepthProForDepthEstimation)
        t = time.time()
        self.gd_proc = AutoProcessor.from_pretrained("IDEA-Research/grounding-dino-base")
        self.gd = AutoModelForZeroShotObjectDetection.from_pretrained("IDEA-Research/grounding-dino-base").to(DEV).eval()
        try:
            from transformers import Sam2Model, Sam2Processor
            self.sam_proc = Sam2Processor.from_pretrained("facebook/sam2.1-hiera-large")
            self.sam = Sam2Model.from_pretrained("facebook/sam2.1-hiera-large").to(DEV).eval()
            self.sam_name = "sam2.1-hiera-large"
        except Exception as e:  # fallback to SAM v1
            print("SAM2 unavailable, falling back to SAM:", e)
            from transformers import SamModel, SamProcessor
            self.sam_proc = SamProcessor.from_pretrained("facebook/sam-vit-huge")
            self.sam = SamModel.from_pretrained("facebook/sam-vit-huge").to(DEV).eval()
            self.sam_name = "sam-vit-huge"
        self.of_proc = OneFormerProcessor.from_pretrained("shi-labs/oneformer_ade20k_swin_large")
        self.of = OneFormerForUniversalSegmentation.from_pretrained("shi-labs/oneformer_ade20k_swin_large").to("cpu").eval()
        self.dp_proc = DepthProImageProcessor.from_pretrained("apple/DepthPro-hf")
        self.dp = DepthProForDepthEstimation.from_pretrained("apple/DepthPro-hf").to(DEV).eval()
        print(f"models loaded on {DEV} in {time.time()-t:.0f}s")

    @torch.no_grad()
    def detect(self, img, labels, box_thr=0.25, text_thr=0.22):
        W, H = img.size
        boxes, scores, names = [], [], []
        for i in range(0, len(labels), 12):          # keep under the 256-token text limit
            chunk = labels[i:i + 12]
            text = ". ".join(chunk) + "."
            inp = self.gd_proc(images=img, text=text, return_tensors="pt").to(DEV)
            out = self.gd(**inp)
            r = self.gd_proc.post_process_grounded_object_detection(
                out, inp.input_ids, threshold=box_thr, text_threshold=text_thr, target_sizes=[(H, W)])[0]
            labs = r.get("text_labels", r.get("labels"))
            for b, s, l in zip(r["boxes"].cpu().tolist(), r["scores"].cpu().tolist(), labs):
                l = (l or "").strip()
                if not l: continue
                # snap partial token matches back to a vocab label
                cand = [c for c in chunk if l in c or c in l]
                l = max(cand, key=len) if cand else l
                boxes.append(b); scores.append(s); names.append(l)
        if not boxes: return []
        import torchvision
        B, S = torch.tensor(boxes), torch.tensor(scores)
        keep = []
        for l in set(names):                         # per-label NMS
            ix = torch.tensor([i for i, n in enumerate(names) if n == l])
            k = torchvision.ops.nms(B[ix], S[ix], 0.5)
            keep += ix[k].tolist()
        dets = [dict(label=names[i], score=round(scores[i], 3), box=[round(v, 1) for v in boxes[i]]) for i in keep]
        # drop near-full-frame boxes for "thing" labels and cap count
        dets = [d for d in dets if not ((d["box"][2]-d["box"][0])*(d["box"][3]-d["box"][1]) > 0.92*W*H
                                       and d["label"] not in ("sky", "water", "street", "floor", "wall"))]
        return sorted(dets, key=lambda d: -d["score"])[:60]

    @torch.no_grad()
    def detect_tiles(self, img, labels, grid=(4, 3), overlap=0.2, box_thr=0.25):
        """SAHI-style: detect small things (crowd figures) on overlapping tiles, merge with NMS."""
        import torchvision
        W, H = img.size; gx, gy = grid
        tw, th = W / gx * (1 + overlap), H / gy * (1 + overlap)
        out = []
        for j in range(gy):
            for i in range(gx):
                x0 = max(0, min(W - tw, i * W / gx - tw * overlap / 2)); y0 = max(0, min(H - th, j * H / gy - th * overlap / 2))
                crop = img.crop((int(x0), int(y0), int(x0 + tw), int(y0 + th)))
                for d in self.detect(crop, labels, box_thr=box_thr):
                    b = d["box"]
                    if (b[2] - b[0]) > 0.6 * tw: continue  # tile-sized false positives
                    d["box"] = [round(b[0] + x0, 1), round(b[1] + y0, 1), round(b[2] + x0, 1), round(b[3] + y0, 1)]
                    out.append(d)
        if not out: return []
        k = torchvision.ops.nms(torch.tensor([d["box"] for d in out]), torch.tensor([d["score"] for d in out]), 0.4)
        return [out[i] for i in k.tolist()]

    @torch.no_grad()
    def segment(self, img, dets):
        if not dets: return np.zeros((0, img.size[1], img.size[0]), bool)
        boxes = [[d["box"] for d in dets]]
        inp = self.sam_proc(images=img, input_boxes=boxes, return_tensors="pt").to(DEV)
        out = self.sam(**inp, multimask_output=False)
        masks = self.sam_proc.post_process_masks(out.pred_masks.cpu(), inp["original_sizes"].cpu())[0]
        return masks[:, 0].numpy().astype(bool)

    @torch.no_grad()
    def stuff(self, img):
        inp = self.of_proc(images=img, task_inputs=["semantic"], return_tensors="pt")
        out = self.of(**inp)
        seg = self.of_proc.post_process_semantic_segmentation(out, target_sizes=[img.size[::-1]])[0]
        return seg.cpu().numpy(), self.of.config.id2label

    @torch.no_grad()
    def depth(self, img):
        inp = self.dp_proc(images=img, return_tensors="pt").to(DEV)
        out = self.dp(**inp)
        r = self.dp_proc.post_process_depth_estimation(out, target_sizes=[img.size[::-1]])[0]
        return r["predicted_depth"].float().cpu().numpy(), float(r["focal_length"]), float(r["field_of_view"])


# ----------------------------------------------------------------------------- geometry
def unproject(depth, f, mask=None, step=1):
    H, W = depth.shape
    v, u = np.mgrid[0:H:step, 0:W:step]
    z = depth[::step, ::step]
    if mask is not None:
        m = mask[::step, ::step]; u, v, z = u[m], v[m], z[m]
    x = (u - W / 2) * z / f; y = (v - H / 2) * z / f
    return np.stack([x, y, z], -1).reshape(-1, 3), (u, v)


def fit_ground(depth, f, mask, iters=400):
    pts, _ = unproject(depth, f, mask)
    pts = pts[np.isfinite(pts).all(1) & (pts[:, 2] > 0.05)]
    if len(pts) < 500: return None
    rng = np.random.default_rng(0)
    if len(pts) > 30000: pts = pts[rng.choice(len(pts), 30000, replace=False)]
    thr = 0.02 * np.median(pts[:, 2])
    best, best_n = None, 0
    for _ in range(iters):
        a, b, c = pts[rng.choice(len(pts), 3, replace=False)]
        n = np.cross(b - a, c - a); nn = np.linalg.norm(n)
        if nn < 1e-9: continue
        n /= nn
        if abs(n[1]) < 0.3 and abs(n[2]) < 0.75: continue  # horizontal-ish, or facing camera (overhead shot)
        d = -n @ a
        inl = np.abs(pts @ n + d) < thr
        if inl.sum() > best_n: best, best_n = inl, inl.sum()
    if best is None: return None
    P = pts[best]; c = P.mean(0)
    n = np.linalg.svd(P - c)[2][-1]; d = -n @ c
    if d < 0: n, d = -n, -d                           # orient normal toward camera ("up")
    return dict(n=n, d=float(d), inlier_frac=float(best_n / len(pts)), n_pts=int(len(pts)))


def horizon_line(n, f, W, H):
    # pixels whose viewing ray is parallel to the plane: n·[(u-W/2)/f, (v-H/2)/f, 1] = 0
    if abs(n[1]) < 1e-6: return None
    vs = lambda u: H / 2 - f * (n[0] * (u - W / 2) / f + n[2]) / n[1]
    a, b = float(vs(0)), float(vs(W))
    if not (-H < a < 2 * H and -H < b < 2 * H): return None   # horizon far outside frame (steep pitch)
    return [[0, a], [W, b]]


def object_metric_height(mask, depth, f):
    ys = np.where(mask.any(1))[0]
    if len(ys) < 8: return None
    z = np.median(depth[mask])
    return (ys[-1] - ys[0]) * z / f


def shot_class(h, pitch):
    if pitch is not None and pitch < -55: return "overhead"
    if h is None: return None
    for lim, name in [(0.6, "ground / worm's-eye"), (2.2, "eye-level"), (8, "elevated"), (40, "rooftop"), (1e9, "aerial")]:
        if h < lim: return name


# ----------------------------------------------------------------------------- outputs
PALETTE = [(255, 99, 72), (0, 210, 211), (254, 202, 87), (95, 39, 205), (29, 209, 161), (255, 159, 243),
           (84, 160, 255), (238, 82, 83), (16, 172, 132), (243, 104, 224), (72, 219, 251), (255, 107, 107)]


def draw_overlay(rgb, dets, masks, horizon, info):
    out = rgb.copy().astype(np.float32)
    order = np.argsort([-m.sum() for m in masks]) if len(masks) else []
    for i in order:                                   # big masks first so small ones stay visible
        c = np.array(PALETTE[i % len(PALETTE)], np.float32)
        out[masks[i]] = out[masks[i]] * 0.45 + c * 0.55
    out = out.astype(np.uint8)
    for i in order:
        c = PALETTE[i % len(PALETTE)]
        cs, _ = cv2.findContours(masks[i].astype(np.uint8), cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        cv2.drawContours(out, cs, -1, c, 2)
    for i, d in enumerate(dets):
        x0, y0 = int(d["box"][0]), int(d["box"][1])
        t = f'{d["label"]} {d["score"]:.2f}'
        (tw, th), _ = cv2.getTextSize(t, cv2.FONT_HERSHEY_SIMPLEX, 0.5, 1)
        cv2.rectangle(out, (x0, y0), (x0 + tw + 6, y0 + th + 8), PALETTE[i % len(PALETTE)], -1)
        cv2.putText(out, t, (x0 + 3, y0 + th + 3), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (15, 15, 20), 1, cv2.LINE_AA)
    if horizon:
        (a, b), (c, d) = horizon
        cv2.line(out, (int(a), int(b)), (int(c), int(d)), (255, 255, 255), 2, cv2.LINE_AA)
        cv2.putText(out, "horizon", (12, int(b) - 8), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2, cv2.LINE_AA)
    return out


def save_ply(path, pts, cols):
    with open(path, "wb") as fh:
        fh.write((f"ply\nformat binary_little_endian 1.0\nelement vertex {len(pts)}\n"
                  "property float x\nproperty float y\nproperty float z\n"
                  "property uchar red\nproperty uchar green\nproperty uchar blue\nend_header\n").encode())
        rec = np.empty(len(pts), dtype=[("p", "<f4", 3), ("c", "u1", 3)])
        rec["p"] = pts; rec["c"] = cols
        fh.write(rec.tobytes())


# ----------------------------------------------------------------------------- main
def analyze(M, path, prompt_rec, dist_idx):
    name = os.path.basename(path)
    gidx = int(re.search(r"_(\d)\.png$", name).group(1))
    sid = f'{prompt_rec["job_id"]}_{gidx}'
    od = os.path.join(OUT, sid); os.makedirs(os.path.join(od, "layers"), exist_ok=True)
    img = Image.open(path).convert("RGB"); W, H = img.size; rgb = np.array(img)
    prompt = prompt_rec["prompt"]; hints = parse_prompt(prompt)
    cur = CURATED.get(prompt_rec["job_id"])
    if cur:
        hints["regex_phrases"] = hints["phrases"]; hints["phrases"] = cur["objects"]; hints["curated"] = True
        if "height_hint" in cur: hints["height_hint"] = cur["height_hint"]
    district, bible_no = dist_idx.get(name, (None, None))

    t0 = time.time()
    vocab = list(dict.fromkeys(hints["phrases"] + DISTRICT_VOCAB.get(district, []) + GENERIC))
    dets = M.detect(img, vocab)
    masks = M.segment(img, dets)
    for d, m in zip(dets, masks): d["area_frac"] = round(float(m.mean()), 4)
    seg, id2label = M.stuff(img)
    depth, focal_px, fov = M.depth(img)
    t_models = time.time() - t0

    # stuff stats
    labels_present = {id2label[int(k)]: round(float((seg == k).mean()), 4) for k in np.unique(seg)}
    stuff = dict(sorted(labels_present.items(), key=lambda kv: -kv[1])[:12])
    sky = np.isin(seg, [k for k, v in id2label.items() if "sky" in v.split(", ")])

    # ground mask: ADE ground classes ∪ ground-like detections, minus sky (ADE names are compound: "sidewalk, pavement")
    ground = np.isin(seg, [k for k, v in id2label.items() if ADE_GROUND & set(v.split(", "))])
    for d, m in zip(dets, masks):
        if GROUND_RE.search(d["label"]): ground |= m
    ground &= ~sky
    plane = fit_ground(depth, focal_px, ground) if ground.mean() > 0.01 else None

    # known-size scale
    scales = []
    for d, m in zip(dets, masks):
        if d["label"] in KNOWN_H and d["score"] > 0.35:
            h = object_metric_height(m, depth, focal_px)
            if h and h > 0: scales.append(KNOWN_H[d["label"]] / h)
    scale = float(np.clip(np.median(scales), 0.25, 4.0)) if scales else 1.0

    cam = dict(focal_px=round(focal_px, 1), fov_h_deg=round(fov, 1),
               focal_35mm_equiv=round(36 * focal_px / W, 1),
               focal_prompted_mm=hints["focal_mm"], height_hint_prompt=hints["height_hint"])
    if hints["focal_mm"]:
        cam["focal_agrees"] = abs(cam["focal_35mm_equiv"] - hints["focal_mm"]) / hints["focal_mm"] < 0.35
    horizon = None; tile_people = []
    if plane:
        n = plane["n"]
        pitch = math.degrees(math.asin(np.clip(n[2], -1, 1)))
        roll = math.degrees(math.atan2(n[0], -n[1]))
        horizon = horizon_line(n, focal_px, W, H)
        if pitch < -45:                               # top-down: standing heights are foreshortened
            scales, scale = [], 1.0
            tile_people = M.detect_tiles(img, ["person"], grid=(8, 5), box_thr=0.20)
            for d in tile_people:
                x0, y0, x1, y1 = d["box"]
                z = float(np.median(depth[int(y0):int(y1) + 1, int(x0):int(x1) + 1]))
                w_m = min(x1 - x0, y1 - y0) * z / focal_px   # shorter side ≈ shoulder width seen from above
                if w_m > 0: scales.append(0.45 / w_m)
            if len(scales) >= 5: scale = float(np.clip(np.median(scales), 0.25, 200.0))
            else: scales = []
        h_raw = plane["d"]; h = h_raw * scale
        cam.update(height_m_raw=round(h_raw, 2), height_m=round(h, 2), scale_factor=round(scale, 3),
                   scale_refs=len(scales), pitch_deg=round(pitch, 1), roll_deg=round(roll, 1),
                   horizon=horizon, ground_inlier_frac=round(plane["inlier_frac"], 3))
        conf = plane["inlier_frac"] * (1.0 if scales else 0.6) * (1.0 if abs(roll) < 10 else 0.7)
        cam["shot_class"] = shot_class(h, pitch)
    else:
        cam.update(height_m=None, pitch_deg=None, shot_class={"aerial": "aerial (no ground)", "elevated": "elevated (no ground)"}
                   .get(hints["height_hint"], "undetermined (no ground)"))
        conf = 0.15
    cam["physics_confidence"] = round(float(conf), 2)
    if tile_people: cam["crowd_count_tiled"] = len(tile_people)
    cam["ground_frac"] = round(float(ground.mean()), 3); cam["sky_frac"] = round(float(sky.mean()), 3)

    # prompt fidelity
    found = {d["label"] for d in dets}
    asked = hints["phrases"]
    hit = [a for a in asked if any(a in f or f in a for f in found)]
    fidelity = dict(asked=asked, found_from_prompt=hit, missing=[a for a in asked if a not in hit],
                    unprompted=sorted(found - set(asked)),
                    score=round(len(hit) / len(asked), 2) if asked else None)

    # depth layers (fg / mg / bg by non-sky depth tertiles; sky goes to bg)
    dz = depth * scale
    valid = ~sky & np.isfinite(dz)
    q1, q2 = np.quantile(dz[valid], [0.33, 0.66]) if valid.any() else (1, 2)
    bands = {"fg": valid & (dz <= q1), "mg": valid & (dz > q1) & (dz <= q2), "bg": (valid & (dz > q2)) | sky}
    for k, m in bands.items():
        Image.fromarray(np.dstack([rgb, (m * 255).astype(np.uint8)])).save(os.path.join(od, "layers", f"{k}.png"))
    layers = {k: dict(frac=round(float(m.mean()), 3)) for k, m in bands.items()}
    layers["fg"]["max_depth_m"] = round(float(q1), 2); layers["mg"]["max_depth_m"] = round(float(q2), 2)

    # point cloud (no sky, clipped far tail)
    pm = valid & (dz < np.quantile(dz[valid], 0.98)) if valid.any() else valid
    pts, (u, v) = unproject(dz, focal_px, pm, step=3)
    pts[:, 1] *= -1; pts[:, 2] *= -1                  # to OpenGL/Blender-ish: y up, -z forward
    save_ply(os.path.join(od, "points.ply"), pts.astype(np.float32), rgb[v, u])

    # images
    Image.fromarray(rgb).save(os.path.join(od, "image.jpg"), quality=88)
    ov = draw_overlay(rgb, dets, masks, horizon, cam)
    for d in tile_people:
        x0, y0, x1, y1 = map(int, d["box"]); cv2.rectangle(ov, (x0, y0), (x1, y1), (254, 202, 87), 1)
    Image.fromarray(ov).save(os.path.join(od, "overlay.jpg"), quality=88)
    dn = np.clip(np.log1p(dz) / np.log1p(np.quantile(dz[valid], 0.98) if valid.any() else 1), 0, 1)
    dc = cv2.applyColorMap((255 - dn * 255).astype(np.uint8), cv2.COLORMAP_INFERNO)[..., ::-1].copy()
    dc[sky] = (dc[sky] * 0.25).astype(np.uint8)
    Image.fromarray(dc).save(os.path.join(od, "depth.jpg"), quality=88)
    gv = rgb.copy(); gv[ground] = (gv[ground] * 0.4 + np.array([29, 209, 161]) * 0.6).astype(np.uint8)
    gv[sky] = (gv[sky] * 0.4 + np.array([84, 160, 255]) * 0.6).astype(np.uint8)
    Image.fromarray(gv).save(os.path.join(od, "ground.jpg"), quality=85)

    # raw arrays for downstream (multiplane.py): instance masks in detection order, ADE ids, metric depth
    np.savez_compressed(os.path.join(od, "arrays.npz"), masks=np.asarray(masks, bool), seg=seg.astype(np.uint8),
                        depth=dz.astype(np.float16), sky=sky, ground=ground, focal_px=np.float32(focal_px),
                        id2label=np.array([id2label[i] for i in range(len(id2label))]))

    rec = dict(id=sid, job_id=prompt_rec["job_id"], grid_index=gidx, file=name, size=[W, H],
               district=district, bible_no=bible_no, prompt=prompt, hints=hints,
               detections=dets, stuff=stuff, camera=cam, fidelity=fidelity, layers=layers,
               models=dict(detector="grounding-dino-base", segmenter=M.sam_name,
                           stuff="oneformer_ade20k_swin_large", depth="DepthPro-hf"),
               timing_s=round(t_models, 1))
    json.dump(rec, open(os.path.join(od, "shot.json"), "w"), indent=2, default=float)
    return rec


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--all", action="store_true"); ap.add_argument("--match", nargs="*")
    a = ap.parse_args()
    prompts = json.load(open(os.path.join(ROOT, "midjourney_prompts.json")))
    by_file = {f: r for r in prompts for f in r["files"]}
    files = sorted(by_file, key=str.lower)
    pats = None if a.all else (a.match or DEFAULT_SET)
    if pats: files = [f for f in files if any(p in f for p in pats)]
    dist_idx = load_district_index()
    print(f"{len(files)} images on {DEV}")
    M = Models()
    os.makedirs(OUT, exist_ok=True)
    summary = []
    for i, f in enumerate(files, 1):
        gi = re.search(r"_(\d)\.png$", f).group(1)
        sid = f'{by_file[f]["job_id"]}_{gi}'
        try:
            r = analyze(M, os.path.join(ROOT, f), by_file[f], dist_idx)
            c = r["camera"]
            print(f"[{i}/{len(files)}] {r['district'] or '-':9s} {c.get('shot_class')!s:24s} h={c.get('height_m')} "
                  f"pitch={c.get('pitch_deg')} fov={c['fov_h_deg']} dets={len(r['detections'])} "
                  f"fid={r['fidelity']['score']} {r['timing_s']}s  {f[10:60]}")
            summary.append(sid)
        except Exception as e:
            import traceback; traceback.print_exc(); print("FAILED", f)
    # merge index (keep previously analyzed shots)
    ids = sorted({os.path.basename(os.path.dirname(p)) for p in glob.glob(os.path.join(OUT, "*", "shot.json"))})
    shots = [json.load(open(os.path.join(OUT, s, "shot.json"))) for s in ids]
    for s in shots: s.pop("prompt_full", None)
    with open(os.path.join(ROOT, "shots", "shots_data.js"), "w") as fh:
        fh.write("window.SHOTS = " + json.dumps(shots, default=float) + ";\n")
    print(f"wrote {len(shots)} shots -> shots/shots_data.js")


if __name__ == "__main__":
    main()
