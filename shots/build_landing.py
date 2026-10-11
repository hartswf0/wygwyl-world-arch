#!/usr/bin/env python3
"""
Landing assets: turn the angular scene programs into live multiplane layers for the root index.

For each selected shot this reads  shots/out/<sid>/program/cartoon.html  (the paired SVG of scene.json) and writes
    landing/<key>/P6.svg … P1.svg   one standalone transparent SVG per plane (far → near, document order),
                                    with only the gradients that plane uses; viewBox is padded by the paint-behind
                                    overscan so the layers can slide under a camera move without showing holes
    landing/<key>/poster.webp       frame0.png, for first paint and thumbnails
    landing/manifest.js             window.LANDING = { key: {w,h,pad,focus,accent,district,sid,planes:[{id,name,par,src}]} }

Nothing here invents art: every shape is the program's own.  Usage:  python3 shots/build_landing.py
"""
import json, os, re, colorsys
from PIL import Image

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, "shots", "out")
DEST = os.path.join(ROOT, "landing")
PAD_X, PAD_Y = 140, 80                        # source px of overscan kept either side (paint-behind lives out there)

SHOTS = {                                     # key → full shot id
    "cortex":   "bdc7d6ec-1d4e-4f99-ad7e-9917394c542a_2",   # hero: children under the dish
    "haze":     "3a0da51b-4c03-45a0-bf3f-d03e5092c4be_0",   # Film
    "moon":     "3da7e92e-f002-4973-9ea6-826a8b88f494_3",   # Reels
    "temple":   "08fe12af-1077-4515-a156-18353f12265f_0",   # World
    "overseer": "18a6390f-1d57-4872-96e2-7c601f756cbd_0",   # Map
    "hive":     "c1eadbdf-d2d9-48d2-9cfa-b8b1425c610f_2",   # World guide
    "arcade":   "bf0a66ea-3b8d-4c15-9513-a1b874283e73_0",   # Shot Lab
    "cenotaph": "abac8bce-fd10-4576-b8bb-49497eb29786_1",   # Storyboard
    "commons":  "245fd8b5-27bb-402d-8f8d-458257e5535b_3",   # Studio
}


def accent(im):
    """most saturated, reasonably bright colour of the drawing (for chapter accents)"""
    sm = im.convert("RGB").resize((48, 27)); best, bs = (242, 165, 65), -1
    for r, g, b in sm.getdata():
        h, s, v = colorsys.rgb_to_hsv(r / 255, g / 255, b / 255)
        sc = s * v * (1 if v > .35 else .4)
        if sc > bs: bs, best = sc, (r, g, b)
    return "#%02x%02x%02x" % best


def build(key, sid):
    pd = os.path.join(OUT, sid, "program")
    html = open(os.path.join(pd, "cartoon.html"), encoding="utf-8").read()
    scene = json.load(open(os.path.join(pd, "scene.json")))
    W, H = scene["W"], scene["H"]
    svg = html[html.find('<svg id="svg"'):html.find("</svg>") + 6]
    defs = re.search(r"<defs>(.*?)</defs>", svg, re.S).group(1)
    grads = {}
    for m in re.finditer(r'<(linearGradient|radialGradient) id="([^"]+)".*?</\1>', defs, re.S):
        grads[m.group(2)] = m.group(0)
    d = os.path.join(DEST, key); os.makedirs(d, exist_ok=True)
    planes = []
    for m in re.finditer(r'<g id="(P\d)" class="plane" data-par="([\d.]+)" data-name="([^"]*)">(.*?)</g>', svg, re.S):
        pid, par, name, body = m.groups()
        if "<path" not in body and "<line" not in body: continue
        used = sorted(set(re.findall(r"url\(#([^)]+)\)", body)))
        dd = "<defs>" + "".join(grads[u] for u in used if u in grads) + "</defs>" if used else ""
        vb = f"{-PAD_X} {-PAD_Y} {W + 2 * PAD_X} {H + 2 * PAD_Y}"
        open(os.path.join(d, f"{pid}.svg"), "w", encoding="utf-8").write(
            f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="{vb}" shape-rendering="geometricPrecision"><style>path{{stroke:none}}</style>{dd}{body}</svg>')
        planes.append(dict(id=pid, name=name, par=float(par), src=f"landing/{key}/{pid}.svg"))
    poster = Image.open(os.path.join(pd, "frame0.png")).convert("RGB")
    poster.resize((960, round(960 * H / W))).save(os.path.join(d, "poster.webp"), quality=78, method=6)
    try:
        mp = json.load(open(os.path.join(OUT, sid, "multiplane", "multiplane.json")))["camera"]["focus"]
        focus = [round(mp[0] / W, 4), round(mp[1] / H, 4)]
    except Exception:
        focus = [.5, .5]
    shot = json.load(open(os.path.join(OUT, sid, "shot.json")))
    return dict(sid=sid, w=W, h=H, padx=PAD_X, pady=PAD_Y, focus=focus, accent=accent(poster),
                district=shot.get("district"), planes=planes, poster=f"landing/{key}/poster.webp")


def main():
    os.makedirs(DEST, exist_ok=True); man = {}
    for k, sid in SHOTS.items():
        man[k] = build(k, sid)
        size = sum(os.path.getsize(os.path.join(DEST, k, f)) for f in os.listdir(os.path.join(DEST, k)))
        print(f"{k:9s} {man[k]['district']:9s} {len(man[k]['planes'])} planes  {size // 1024} KB  focus {man[k]['focus']}  {man[k]['accent']}")
    open(os.path.join(DEST, "manifest.js"), "w").write("window.LANDING = " + json.dumps(man, separators=(",", ":")) + ";\n")
    print("wrote landing/manifest.js")


if __name__ == "__main__":
    main()
