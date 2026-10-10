#!/usr/bin/env python3
"""
build_world.py — compile the 81 multiplane shots into a walkable 3D world.

Each shot becomes a DIORAMA: its depth sheets (S??_P?.png) are stood up in 3D at
compressed measured depth z' = 1 + 3·ln(1 + z_m/2), each sized 2·z'·tan(hfov/2) wide.
From the shot's camera point the original composition recomposes exactly; step off
that point and the sheets separate into real parallax (a physical multiplane stand).

Dioramas ring the 12 districts of _city at their map coordinates and altitude.
Poem reels (film/reels.js) become flight paths: a cut is a camera move through the world.

Writes:
  shots/world/<id8>/S??.webp   768-px sheets (LOD; full-res PNG is loaded on entry)
  shots/world/<id8>/cel.webp   flat cel paint, ink.webp line pass (RGBA), thumb.jpg
  shots/world_data.js          window.WORLD = {districts, shots, reels}
"""
import glob, json, math, os, re
import numpy as np
from PIL import Image

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SH = os.path.join(ROOT, "shots"); OUT = os.path.join(SH, "out"); WD = os.path.join(SH, "world")
LO = 768


def zc(zm):  # compressed stage depth (world units) — monotone, keeps sky finite
    return round(1.0 + 3.0 * math.log(1.0 + max(0.05, float(zm)) / 2.0), 3)


def load_js(path, var):
    t = open(path).read(); return json.loads(t.split("=", 1)[1].strip().rstrip(";"))


def save_webp(im, path, w=LO):
    if os.path.exists(path): return
    h = int(round(im.height * w / im.width))
    im.resize((w, h), Image.LANCZOS).save(path, "WEBP", quality=82, method=4)


def main():
    os.makedirs(WD, exist_ok=True)
    C = load_js(os.path.join(SH, "city_data.js"), "CITY")
    reels = load_js(os.path.join(SH, "film", "reels.js"), "REELS") if os.path.exists(os.path.join(SH, "film", "reels.js")) else []
    dist_of = {s: d["id"] for d in C["districts"] for s in d["shots"]}
    shots = []
    for mp in sorted(glob.glob(os.path.join(OUT, "*", "multiplane", "multiplane.json"))):
        od = os.path.dirname(os.path.dirname(mp)); sid = os.path.basename(od); k8 = sid[:8] + sid[-2:]
        M = json.load(open(mp)); S = json.load(open(os.path.join(od, "shot.json")))
        W0, H0 = S["size"]; cam = S.get("camera", {}); mc = M["camera"]
        dd = os.path.join(WD, k8); os.makedirs(dd, exist_ok=True)
        sheets = []
        for s in M["sheets"]:
            src = os.path.join(od, "multiplane", s["file"])
            if not os.path.exists(src): continue
            if s.get("z_m") is None:
                zr = mc.get("z_ref_m") or 10.0
                s["z_m"] = zr / s["parallax"] if s.get("parallax") else 2000.0
            if s["plane"] == "P6": s["z_m"] = max(s["z_m"], 400.0)
            lo = os.path.join(dd, s["file"].replace(".png", ".webp"))
            save_webp(Image.open(src).convert("RGBA"), lo)
            sheets.append(dict(lo=os.path.relpath(lo, SH), hi=os.path.relpath(src, SH), z=zc(s["z_m"]), zm=s["z_m"],
                               plane=s["plane"], label=s["label"],
                               water=bool(re.search(r"water|pool|canal|lagoon|sea|river|reflect|lake", s["label"], re.I)),
                               sway=bool(re.search(r"\b(fabric|laundry|cloth|flag|curtain|plant|trees?|palms?|garden|lanterns?)\b", s["label"], re.I))))
        if not sheets: continue
        for nm in ("cel", "ink"):
            p = os.path.join(od, "cartoon", f"{nm}.png")
            if os.path.exists(p): save_webp(Image.open(p).convert("RGBA" if nm == "ink" else "RGB"), os.path.join(dd, f"{nm}.webp"))
        th = os.path.join(dd, "thumb.jpg")
        if not os.path.exists(th):
            im = Image.open(os.path.join(od, "image.jpg")).convert("RGB"); im.thumbnail((384, 384)); im.save(th, quality=84)
        bd = os.path.join(dd, "backdrop.webp")
        save_webp(Image.open(os.path.join(od, "image.jpg")).convert("RGB"), bd, w=1024)
        zref = mc.get("z_ref_m") or float(np.median([s["zm"] for s in sheets]))
        hero = min(sheets, key=lambda s: abs(s["zm"] - zref))
        shots.append(dict(
            id=sid, k=k8, district=dist_of.get(sid), title=M.get("title") or S.get("prompt", "")[:60],
            prompt=S.get("prompt", "")[:320], action=M.get("action"), beats=M.get("beats") or [],
            fov=cam.get("fov_h_deg") or 50.0, aspect=round(W0 / H0, 4), pitch=cam.get("pitch_deg") or 0.0,
            roll=cam.get("roll_deg") or 0.0, height=cam.get("height_m"), shot_class=cam.get("shot_class"),
            move=mc["move"], amp=mc["amplitude"], focus=[mc["focus"][0] / W0, mc["focus"][1] / H0], why=mc.get("why"),
            z_hero=hero["z"], W0=W0, sheets=sheets,
            cel=os.path.relpath(os.path.join(dd, "cel.webp"), SH) if os.path.exists(os.path.join(dd, "cel.webp")) else None,
            ink=os.path.relpath(os.path.join(dd, "ink.webp"), SH) if os.path.exists(os.path.join(dd, "ink.webp")) else None,
            thumb=os.path.relpath(th, SH), backdrop=os.path.relpath(bd, SH),
            film=f"out/{sid}/film/shot.mp4" if os.path.exists(os.path.join(od, "film", "shot.mp4")) else None))
        print(f"{sid[:8]} {len(sheets)} sheets  z'={[s['z'] for s in sheets]}")
    districts = [dict(id=d["id"], name=d["name"], realm=d.get("realm"), mood=d.get("mood"), signature=d.get("signature"),
                      color=d["color"], glow=d.get("glow", []), body=d.get("body", []), coords=d["coords"],
                      zone=d["coords"].get("zone")) for d in C["districts"]]
    R = [dict(num=r["num"], title=r["title"], district=r["district"], color=r["color"],
              shots=[s["id"] for s in r["shots"]]) for r in reels]
    with open(os.path.join(SH, "world_data.js"), "w") as fh:
        fh.write("window.WORLD = " + json.dumps(dict(districts=districts, shots=shots, reels=R), ensure_ascii=False) + ";\n")
    print(f"world: {len(districts)} districts, {len(shots)} dioramas, {len(R)} poem flights")


if __name__ == "__main__":
    main()
