#!/usr/bin/env python3
"""
Keep going: make N more cartoons, end to end, and hand the judge a short list.

  pick     next N shots not yet in shots/out (one image per Midjourney job, so coverage is broad)
  analyze  analyze.py   (DINO + SAM + OneFormer + Depth Pro, ~18 s/img + 2 min model load)
  planes   multiplane.py (auto director notes when none are written)
  program  scene_program.py (render → score → refine; judge_notes.json applied if present)
  perceive perceive.py (squint ladder, CLIP per plane / FG-MG-BG, senses)
  prejudge automatic flags from the metrics, so the human/LLM judge looks at the risky ones first
  sheets   shots/contact/page_##.jpg (original | cartoon, 8 per page, flags printed) for fast batch judging

Usage:
  .venv-shots/bin/python shots/batch.py --n 50            # pick + run everything
  .venv-shots/bin/python shots/batch.py --ids-file shots/batch50.json --skip-analyze
  .venv-shots/bin/python shots/batch.py --sheets-only
"""
import argparse, glob, json, os, re, subprocess, sys
from PIL import Image, ImageDraw, ImageFont

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, "shots", "out"); PY = sys.executable


def font(sz):
    try: return ImageFont.truetype("/System/Library/Fonts/Supplemental/Arial.ttf", sz)
    except Exception: return ImageFont.load_default()


def pick(n):
    files = sorted(glob.glob(os.path.join(ROOT, "*.png")), key=str.lower)
    done = {d.rsplit("_", 1)[0] for d in os.listdir(OUT)} if os.path.isdir(OUT) else set()
    seen, out = set(), []
    for f in files:
        m = re.search(r"([0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12})_(\d)\.png$", f)
        if not m or m.group(1) in done or m.group(1) in seen: continue
        seen.add(m.group(1)); out.append(f"{m.group(1)}_{m.group(2)}")
    return out[:n]


def sh(args):
    print("$", " ".join(args[:4]), "…" if len(args) > 4 else ""); sys.stdout.flush()
    r = subprocess.run(args, cwd=ROOT)
    if r.returncode: print(f"  ! exit {r.returncode}")


def prejudge(sid):
    """metric-only flags; the judge decides. Returns (flags, risk 0..1)."""
    pd = os.path.join(OUT, sid, "program"); flags = []
    try:
        sc = json.load(open(os.path.join(pd, "scene.json")))["score"]
        pc = json.load(open(os.path.join(pd, "perceive.json")))
        cam = json.load(open(os.path.join(OUT, sid, "shot.json")))["camera"]
    except Exception as e:
        return [f"missing: {e.__class__.__name__}"], 1.0
    if (pc.get("reads_at_sigma") or 99) > 8: flags.append(f"reads only at σ{pc.get('reads_at_sigma')}")
    w = pc["whole"]; ro, rc = w.get("prompt_rank_orig") or 1, w.get("prompt_rank_cartoon") or 1
    if rc > max(5, 2 * ro): flags.append(f"lost its prompt: rank {ro}→{rc}")
    for k, v in pc.get("clip_layers", {}).items():
        if not v["same"]: flags.append(f"{k} reads as '{v['reads_as_cartoon']}' not '{v['reads_as_orig']}'")
    if sc["dE"] > 12: flags.append(f"ΔE {sc['dE']}")
    if "overhead" in (cam.get("shot_class") or ""): flags.append("overhead (crowd/ring risk)")
    risk = min(1.0, 0.25 * len(flags) + min(0.5, max(0, rc - ro) / 20))
    return flags, round(risk, 2)


def sheets(ids, per=8):
    os.makedirs(os.path.join(ROOT, "shots", "contact"), exist_ok=True)
    rows = []
    for sid in ids:
        pd = os.path.join(OUT, sid, "program")
        if not os.path.exists(os.path.join(pd, "frame0.png")): continue
        flags, risk = prejudge(sid); rows.append((risk, sid, flags))
    rows.sort(key=lambda r: -r[0])                                         # riskiest first
    W, TH = 360, 202
    index = []
    for pg in range(0, len(rows), per):
        chunk = rows[pg:pg + per]
        im = Image.new("RGB", (W * 2 + 18, (TH + 40) * len(chunk) + 10), (10, 12, 16)); dr = ImageDraw.Draw(im)
        for i, (risk, sid, flags) in enumerate(chunk):
            S = json.load(open(os.path.join(OUT, sid, "shot.json")))
            o = Image.open(os.path.join(ROOT, S["file"])).convert("RGB").resize((W, TH))
            c = Image.open(os.path.join(OUT, sid, "program", "frame0.png")).convert("RGB").resize((W, TH))
            y = 10 + i * (TH + 40); im.paste(o, (6, y + 34)); im.paste(c, (W + 12, y + 34))
            col = (255, 110, 120) if risk >= .5 else (242, 165, 65) if risk > 0 else (42, 212, 192)
            dr.text((6, y + 2), f"{sid[:8]}  {(S.get('district') or '-')}  risk {risk}", fill=col, font=font(13))
            dr.text((6, y + 18), ("; ".join(flags) or "no flags")[:110], fill=(170, 176, 190), font=font(11))
            index.append(dict(id=sid, risk=risk, flags=flags, page=pg // per + 1))
        im.save(os.path.join(ROOT, "shots", "contact", f"page_{pg // per + 1:02d}.jpg"), quality=84)
    json.dump(index, open(os.path.join(ROOT, "shots", "contact", "index.json"), "w"), indent=1)
    print(f"wrote {len(index)} entries on {(len(rows) + per - 1) // per} contact pages (riskiest first)")
    return index


def main():
    ap = argparse.ArgumentParser(); ap.add_argument("--n", type=int, default=0); ap.add_argument("--ids-file")
    ap.add_argument("--skip-analyze", action="store_true"); ap.add_argument("--sheets-only", action="store_true"); a = ap.parse_args()
    ids = json.load(open(a.ids_file)) if a.ids_file else pick(a.n) if a.n else []
    if not a.sheets_only:
        if not ids: sys.exit("nothing to do: pass --n or --ids-file")
        json.dump(ids, open(os.path.join(ROOT, "shots", "batch_last.json"), "w"))
        if not a.skip_analyze: sh([PY, "shots/analyze.py", "--match", *ids])
        sh([PY, "shots/multiplane.py"])
        sh([PY, "shots/scene_program.py", "--match", *ids])
        sh([PY, "shots/perceive.py", "--match", *ids])
    allids = sorted(os.path.basename(os.path.dirname(os.path.dirname(p))) for p in glob.glob(os.path.join(OUT, "*", "program", "frame0.png")))
    sheets(ids or allids)


if __name__ == "__main__":
    main()
