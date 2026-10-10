#!/usr/bin/env python3
"""
Perception passes on a scene program: does the cartoon still READ, at a glance, by meaning, and by feel?

  1. squint ladder  ("denoising" in reverse): blur original and cartoon together at σ = 1..32 px and compare.
                    A good cartoon matches the original MORE as you blur: it keeps big values and silhouettes,
                    and only drops detail. reads_at = smallest blur where value-SSIM ≥ 0.9.
  2. CLIP           per plane (P0–P6) and per depth layer (FG = P0+P1, MG = P2–P4, BG = P5+P6). Measures:
                      image↔image similarity of masked crops (original vs cartoon)
                      zero-shot label (scene's own ADE labels + prompt nouns): does the plane read as the same thing?
                    whole frame: CLIP(prompt) retention = sim(cartoon, prompt) / sim(original, prompt)
  3. senses         cross-modal descriptors from the program: enclosure, openness, warmth, weight, contrast,
                    tempo, density, plus a one-line "felt" description. Comparable across shots and other works.

Writes out/<id>/program/perceive.json + perceive.jpg, and shots/perceive_data.js (window.PC).
Usage: .venv-shots/bin/python shots/perceive.py [--match id-substr ...]
"""
import argparse, glob, json, os, re
import numpy as np
import cv2, torch
from PIL import Image, ImageDraw, ImageFont
from skimage.metrics import structural_similarity as ssim

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, "shots", "out")
DEV = "mps" if torch.backends.mps.is_available() else "cpu"
LAYERS = {"FG": (0, 1), "MG": (2, 3, 4), "BG": (5, 6)}
SIGMAS = (1, 2, 4, 8, 16, 32)
SYN = [{"person", "child", "people", "man", "woman"}, {"wall", "building", "house"}, {"water", "sea", "river", "lake"},
       {"floor", "road", "sidewalk", "earth", "ground"}, {"stairs", "stairway", "step"}]
CAM_RE = re.compile(r"(--\w+\s*\S*)|\b(canon|nikon|sony|leica|fujifilm|hasselblad|eos|iso\s*\d+|\d+\s*mm|f/?\d+(\.\d+)?|1/\d+s?|lens|camera|photograph\w*|photo\w*|r\d|mark\s*\w+|shutter|aperture)\b", re.I)


def same_thing(a, b):
    return a == b or any(a in g and b in g for g in SYN)


def content(prompt):
    return re.sub(r"\s+", " ", CAM_RE.sub(" ", prompt)).strip(" ,.;")[:300]


def font(sz):
    try: return ImageFont.truetype("/System/Library/Fonts/Supplemental/Arial.ttf", sz)
    except Exception: return ImageFont.load_default()


class Clip:
    def __init__(s, name="openai/clip-vit-base-patch16"):
        from transformers import CLIPModel, CLIPProcessor
        s.m = CLIPModel.from_pretrained(name).to(DEV).eval(); s.p = CLIPProcessor.from_pretrained(name)

    @torch.no_grad()
    def img(s, ims):
        x = s.p(images=ims, return_tensors="pt").to(DEV)
        f = s.m.get_image_features(**x)
        f = f if torch.is_tensor(f) else f.pooler_output
        return torch.nn.functional.normalize(f.float(), dim=-1)

    @torch.no_grad()
    def txt(s, texts):
        x = s.p(text=texts, return_tensors="pt", padding=True, truncation=True, max_length=77).to(DEV)
        f = s.m.get_text_features(**x)
        f = f if torch.is_tensor(f) else f.pooler_output
        return torch.nn.functional.normalize(f.float(), dim=-1)


def masked_crop(rgb, m, pad=12):
    ys, xs = np.nonzero(m)
    if len(ys) < 50: return None
    y0, y1 = max(0, ys.min() - pad), min(rgb.shape[0], ys.max() + pad); x0, x1 = max(0, xs.min() - pad), min(rgb.shape[1], xs.max() + pad)
    c = rgb[y0:y1, x0:x1].copy(); mm = cv2.dilate(m[y0:y1, x0:x1].astype(np.uint8), np.ones((7, 7), np.uint8)).astype(bool)
    c[~mm] = 128
    return Image.fromarray(c)


def senses(planes, rgb, L, mp, nshapes, nlines):
    area = {p: float((L == p).mean()) for p in range(7)}
    lum = cv2.cvtColor(rgb, cv2.COLOR_RGB2GRAY).astype(np.float32) / 255
    H = lum.shape[0]
    enclosure = min(1.0, area[0] + 0.6 * area[1])
    openness = area[6] + 0.5 * area[5]
    warm = float(((rgb[..., 0].astype(float) - rgb[..., 2]) / 255).mean())
    weight = float(lum[H // 2:].mean() - lum[:H // 2].mean())              # >0 = dark top (heavy, looming)
    contrast = float(np.percentile(lum, 95) - np.percentile(lum, 5))
    cam = mp["camera"]; amp = float(cam.get("amplitude", .06)); amp = amp / max(rgb.shape[:2]) if amp > 1 else amp
    pars = [p["parallax"] for p in mp["planes"] if p.get("parallax") is not None]
    tempo = float(amp * (max(pars) - min(pars) if pars else 0) * 10)
    density = (nshapes + nlines) / 100
    words = []
    words.append("enclosed, close walls" if enclosure > .45 else "half-held" if enclosure > .2 else "open, exposed")
    words.append("vast sky overhead" if openness > .35 else "a sliver of distance" if openness > .1 else "no horizon to escape to")
    words.append("warm air" if warm > .08 else "cold air" if warm < -.03 else "neutral air")
    words.append("heavy ceiling pressing down" if weight > .06 else "light above, weight underfoot" if weight < -.06 else "even weight")
    words.append("hard light" if contrast > .7 else "soft, hazy light" if contrast < .45 else "")
    words.append({"push": "slowly drawn inward", "truck": "drifting sideways", "tilt_up": "lifting the gaze", "crane_push": "descending and approaching"}.get(cam["move"], ""))
    return dict(enclosure=round(enclosure, 3), openness=round(openness, 3), warmth=round(warm, 3), weight=round(weight, 3),
                contrast=round(contrast, 3), tempo=round(tempo, 3), density=round(density, 2),
                felt=", ".join(w for w in words if w))


def run(sid, clip):
    od = os.path.join(OUT, sid); pd = os.path.join(od, "program")
    S = json.load(open(os.path.join(od, "shot.json"))); MP = json.load(open(os.path.join(od, "multiplane", "multiplane.json")))
    SC = json.load(open(os.path.join(pd, "scene.json")))
    A = np.load(os.path.join(od, "arrays.npz")); L = np.load(os.path.join(od, "multiplane", "planes.npz"))["L"]
    orig = np.array(Image.open(os.path.join(ROOT, S["file"])).convert("RGB")); cart = np.array(Image.open(os.path.join(pd, "frame0.png")).convert("RGB"))
    # 1. squint ladder at half res
    h, w = orig.shape[0] // 2, orig.shape[1] // 2
    o2 = cv2.resize(orig, (w, h), interpolation=cv2.INTER_AREA).astype(np.float32); c2 = cv2.resize(cart, (w, h), interpolation=cv2.INTER_AREA).astype(np.float32)
    ladder = []
    for sg in SIGMAS:
        ob, cb = cv2.GaussianBlur(o2, (0, 0), sg), cv2.GaussianBlur(c2, (0, 0), sg)
        ol, cl = [cv2.cvtColor((x / 255).astype(np.float32), cv2.COLOR_RGB2LAB) for x in (ob, cb)]
        ladder.append(dict(sigma=sg, dE=round(float(np.linalg.norm(ol - cl, axis=2).mean()), 2),
                           value_ssim=round(float(ssim(ol[..., 0] / 100, cl[..., 0] / 100, data_range=1.0)), 3)))
    reads_at = next((r["sigma"] for r in ladder if r["value_ssim"] >= 0.9), None)
    # 2. CLIP
    id2 = [str(x) for x in A["id2label"]]
    ade = [id2[i].split(",")[0].strip() for i, c in sorted(enumerate(np.bincount(A["seg"].ravel(), minlength=len(id2))), key=lambda t: -t[1]) if c > 0.004 * A["seg"].size]
    nouns = [p.strip() for p in (S.get("hints", {}).get("objects") or [])][:12]
    labels = list(dict.fromkeys(ade[:14] + nouns + ["person", "child", "sky", "water"]))
    T = clip.txt([f"a picture of {l}" for l in labels])
    groups = {f"P{p}": (p,) for p in range(7)}; groups.update(LAYERS)
    per = {}
    for name, ps in groups.items():
        m = np.isin(L, ps)
        if m.mean() < 0.004: continue
        a, b = masked_crop(orig, m), masked_crop(cart, m)
        if a is None: continue
        F = clip.img([a, b]); sim = float((F[0] @ F[1]).item())
        lo, lc = ((F @ T.T) * 100).softmax(-1).cpu().numpy()
        to, tc = labels[int(lo.argmax())], labels[int(lc.argmax())]
        po = float(lc[int(lo.argmax())])
        per[name] = dict(area=round(float(m.mean()), 3), clip_sim=round(sim, 3), reads_as_orig=to, reads_as_cartoon=tc,
                         same=same_thing(to, tc) or po >= 0.15, p_orig_label_in_cartoon=round(po, 3))
    # style-invariant prompt test: rank of the shot's own prompt among ALL prompts (camera/photo words stripped)
    Fw = clip.img([Image.fromarray(orig), Image.fromarray(cart)])
    sims = (Fw @ clip.allp.T).cpu().numpy()
    own = clip.prompt_ix.get(S.get("job_id"))
    rank = lambda row: int((row > row[own]).sum()) + 1 if own is not None else None
    whole = dict(img_img=round(float((Fw[0] @ Fw[1]).item()), 3), prompt_rank_orig=rank(sims[0]), prompt_rank_cartoon=rank(sims[1]),
                 n_prompts=int(sims.shape[1]))
    sn = senses(SC.get("planes"), orig, L, MP, SC["score"]["shapes"], SC["score"].get("lines", 0))
    weakest = sorted([(k, v) for k, v in per.items() if k.startswith("P")], key=lambda kv: kv[1]["clip_sim"])[:2]
    rec = dict(id=sid, squint=ladder, reads_at_sigma=reads_at, clip_layers={k: v for k, v in per.items() if not k.startswith("P")},
               clip_planes={k: v for k, v in per.items() if k.startswith("P")}, whole=whole, senses=sn,
               weakest_planes=[k for k, _ in weakest])
    json.dump(rec, open(os.path.join(pd, "perceive.json"), "w"), indent=1)
    # squint strip: original over cartoon at increasing blur
    tw, th = w // 3, h // 3; sh = Image.new("RGB", (tw * len(SIGMAS) + 6 * (len(SIGMAS) - 1), th * 2 + 30), (10, 12, 16)); dr = ImageDraw.Draw(sh)
    for i, sg in enumerate(SIGMAS):
        for j, src in enumerate((o2, c2)):
            t = cv2.resize(cv2.GaussianBlur(src, (0, 0), sg), (tw, th), interpolation=cv2.INTER_AREA)
            sh.paste(Image.fromarray(np.clip(t, 0, 255).astype(np.uint8)), (i * (tw + 6), 26 + j * th))
        dr.text((i * (tw + 6) + 4, 6), f"σ{sg}  SSIM {ladder[i]['value_ssim']}", fill=(242, 165, 65) if sg == reads_at else (200, 200, 210), font=font(12))
    sh.save(os.path.join(pd, "perceive.jpg"), quality=86)
    return rec


def main():
    ap = argparse.ArgumentParser(); ap.add_argument("--match", nargs="*"); a = ap.parse_args()
    ids = sorted(os.path.basename(os.path.dirname(os.path.dirname(p))) for p in glob.glob(os.path.join(OUT, "*", "program", "frame0.png")))
    if a.match: ids = [i for i in ids if any(m in i for m in a.match)]
    clip = Clip()
    P = json.load(open(os.path.join(ROOT, "midjourney_prompts.json")))
    clip.prompt_ix = {r["job_id"]: i for i, r in enumerate(P)}
    clip.allp = torch.cat([clip.txt([content(r["prompt"]) for r in P[i:i + 32]]) for i in range(0, len(P), 32)])
    for sid in ids:
        r = run(sid, clip)
        lay = " ".join(f"{k}:{v['clip_sim']}{'' if v['same'] else '!'}" for k, v in r["clip_layers"].items())
        w = r["whole"]
        print(f"{sid[:8]} reads@σ{r['reads_at_sigma']} prompt-rank {w['prompt_rank_orig']}→{w['prompt_rank_cartoon']}/{w['n_prompts']} {lay} weakest={r['weakest_planes']} | {r['senses']['felt']}")
    allr = {}
    for p in glob.glob(os.path.join(OUT, "*", "program", "perceive.json")):
        j = json.load(open(p)); allr[j["id"]] = j
    open(os.path.join(ROOT, "shots", "perceive_data.js"), "w").write("window.PC = " + json.dumps(allr) + ";\n")


if __name__ == "__main__":
    main()
