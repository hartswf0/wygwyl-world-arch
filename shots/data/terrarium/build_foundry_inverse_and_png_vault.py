#!/usr/bin/env python3
"""
Builds on top of and through:
  - https://hartswf0.github.io/butterfly-halfworld/wygwyl/world/foundry/index.html
  - https://hartswf0.github.io/butterfly-halfworld/wygwyl/world/foundry/inverse.html

1. Generates 62 high-resolution Foundry + Inverse Composite PNGs in `shots/png_vault/foundry_inverse/`:
   - 28 Inverse-Topology "Triple-Through" Landscape Synthesis PNGs (`inv_triple_<ref>_w1623.png`)
   - 14 Poem "Foundry Camera Stand x Multiplane Sidescroller" PNGs (`foundry_stand_poem_<NN>.png`)
   - 14 Poem "Interior Walk-In Set (Interiors Become Sets)" PNGs (`inverse_walkin_set_poem_<NN>.png`)
   - 6 Foundry World "4-State Cartographic & Route Atlas" PNGs (`foundry_world_atlas_<wid>.png`)
2. Saves & optimizes all 341 unique generated artifact PNGs from the session artifact directory
   into `shots/png_vault/artifacts/*.png`.
3. Catalogs all saved PNGs + 365 Master Kit Cut-Out PNG Sheets into `shots/png_vault/png_catalog.json`
   for the Website PNG Grid Browser (`shots/png_browser.html`) and Foundry/Inverse Studio (`shots/foundry_inverse.html`).
"""

import os
import sys
import glob
import json
import math
import time
import hashlib
from PIL import Image, ImageDraw, ImageFont, ImageEnhance, ImageFilter, ImageChops

REPO_ROOT = "/Users/gaia/WORLDBUILDING-TERMS/wygwyl-world-arch"
SHOTS_DIR = os.path.join(REPO_ROOT, "shots")
FOUNDRY_DIR = os.path.join(SHOTS_DIR, "data", "terrarium", "foundry")
BRAIN_DIR = "/Users/gaia/.gemini/antigravity/brain/f76dabc9-fb98-42f7-bec0-54be580e5584"

VAULT_DIR = os.path.join(SHOTS_DIR, "png_vault")
VAULT_FI_DIR = os.path.join(VAULT_DIR, "foundry_inverse")
VAULT_ART_DIR = os.path.join(VAULT_DIR, "artifacts")

os.makedirs(VAULT_FI_DIR, exist_ok=True)
os.makedirs(VAULT_ART_DIR, exist_ok=True)


def get_font(size=14, bold=False):
    candidates = [
        "/System/Library/Fonts/HelveticaNeue.ttc",
        "/System/Library/Fonts/Supplemental/Arial Bold.ttf" if bold else "/System/Library/Fonts/Supplemental/Arial.ttf",
        "/System/Library/Fonts/Helvetica.ttc",
    ]
    for c in candidates:
        if os.path.exists(c):
            try:
                return ImageFont.truetype(c, size)
            except Exception:
                pass
    return ImageFont.load_default()


FONT_XS = get_font(11, False)
FONT_SM = get_font(12, False)
FONT_SM_B = get_font(12, True)
FONT_MD = get_font(14, False)
FONT_MD_B = get_font(14, True)
FONT_LG = get_font(18, True)
FONT_XL = get_font(22, True)


def safe_open_rgb(path, size=None):
    if not path or not os.path.exists(path):
        im = Image.new("RGB", size or (400, 220), (16, 22, 30))
        return im
    try:
        im = Image.open(path).convert("RGB")
        if size:
            im = im.resize(size, Image.Resampling.LANCZOS)
        return im
    except Exception:
        return Image.new("RGB", size or (400, 220), (16, 22, 30))


def safe_open_rgba(path, max_h=None):
    if not path or not os.path.exists(path):
        return None
    try:
        im = Image.open(path).convert("RGBA")
        if max_h and im.height > max_h:
            w = max(1, int(im.width * (max_h / im.height)))
            im = im.resize((w, max_h), Image.Resampling.LANCZOS)
        return im
    except Exception:
        return None


def save_quantized_png(im, dst_path, colors=256):
    if im.mode not in ("RGB", "RGBA"):
        im = im.convert("RGBA")
    q = im.quantize(colors=colors, method=Image.Quantize.FASTOCTREE)
    q.save(dst_path, format="PNG", optimize=True)
    return os.path.getsize(dst_path)


SCENE_PLANS_CACHE = None


def collect_poem_cutouts(poem_str):
    """Returns curated full-body character figures and architectural/prop pieces for a given poem from scene_collage_plans.json."""
    global SCENE_PLANS_CACHE
    if SCENE_PLANS_CACHE is None:
        sp_path = os.path.join(SHOTS_DIR, "arena", "parts", "kit3", "release_v2", "scene_collage_plans.json")
        if os.path.exists(sp_path):
            SCENE_PLANS_CACHE = json.load(open(sp_path))
        else:
            SCENE_PLANS_CACHE = {"scenes": []}

    p_int = int(poem_str)
    out = []
    seen_files = set()

    for sc in SCENE_PLANS_CACHE.get("scenes", []):
        if int(sc.get("book", 0)) != p_int:
            continue
        for pl in sc.get("staged_placements", []):
            sem = pl.get("semantic_class", "")
            f_rel = pl.get("file", "")
            if not f_rel or f_rel in seen_files:
                continue
            full_p = os.path.join(SHOTS_DIR, f_rel)
            if not os.path.exists(full_p):
                continue
            if sem in ("full_figure_adult", "full_figure_child", "crouched_or_prone_figure"):
                seen_files.add(f_rel)
                out.append(("actor", pl.get("label", "Figure")[:26], full_p))
            elif sem in ("door_window_arch", "stair_bridge_viaduct", "large_furniture", "medium_prop"):
                seen_files.add(f_rel)
                out.append(("prop", pl.get("label", "Prop")[:26], full_p))

    # Ensure we always have at least 2 full-body character cutouts
    fallback_figs = [
        ("actor", "Poet Full Figure (Front)", os.path.join(SHOTS_DIR, "weave/cast/man/library/misc/body_front_08.png")),
        ("actor", "EX Leaning (Back View)", os.path.join(SHOTS_DIR, "arena/parts/kit3/release_v2/cuts/ex.ex_jacket.master/ex.ex_jacket.master__p30.png")),
        ("actor", "Poet Seated Figure", os.path.join(SHOTS_DIR, "weave/cast/man/library/misc/body_sitting_04.png")),
    ]
    for kind, label, fp in fallback_figs:
        if os.path.exists(fp) and len([x for x in out if x[0] == "actor"]) < 3:
            out.append((kind, label, fp))

    return out


def synthesize_through_frame(ref_obj, inv_shot, poem_str, width=1220, height=510):
    """
    Synthesizes the 'BUILT ON TOP & THROUGH' frame combining:
      1. Inverse-sculpted world (`inv_shot['b']`) as the metric 3D terrain base
      2. Through-Aperture bleed of `ref_obj['img']` + Multiplane stage `s2_ext.webp`
         modulated by `ref_obj['seg']` and horizon `cam['hor']`
      3. Poem cut-out props & character silhouettes placed at measured metric tags (`tags_b`)
      4. Foundry yellow/pink/cyan rangefinder telemetry overlays
    """
    ref_img_p = os.path.join(FOUNDRY_DIR, ref_obj["img"])
    ref_seg_p = os.path.join(FOUNDRY_DIR, ref_obj["seg"])
    inv_b_p = os.path.join(FOUNDRY_DIR, inv_shot["b"])
    stage_p = os.path.join(SHOTS_DIR, "play", "levels", poem_str, "s2_ext.webp")
    tape_p = os.path.join(SHOTS_DIR, "play", "levels", poem_str, "poem_tape.webp")

    base_b = safe_open_rgb(inv_b_p, (width, height))
    ref_im = safe_open_rgb(ref_img_p, (width, height))
    seg_im = safe_open_rgb(ref_seg_p, (width, height))
    stage_im = safe_open_rgb(stage_p, (width, height))

    hor = inv_shot.get("cam", {}).get("hor") or ref_obj.get("horizon") or 0.38
    hor_y = int(max(0.18, min(0.72, hor)) * height)

    # Create a smooth vertical & panoptic mask so:
    # - Above horizon (sky/clouds/upper towers): Reference image + Stage plate shine THROUGH (55% blend)
    # - Near horizon & water: 38% through-bleed
    # - Ground plane: Sculpted Foundry terrain stays crisp with 25% stage texture blend
    mask = Image.new("L", (width, height), 0)
    mdraw = ImageDraw.Draw(mask)
    for y in range(height):
        if y < hor_y:
            t = 1.0 - (y / max(1, hor_y))
            val = int(115 + 95 * t)  # 115..210
        else:
            t = (y - hor_y) / max(1, height - hor_y)
            val = int(95 * (1.0 - t * 0.65))  # 95..33
        mdraw.line([(0, y), (width, y)], fill=val)

    # Modulate mask with luminance of segmentation to create panoptic window/sky apertures
    seg_gray = seg_im.convert("L").filter(ImageFilter.GaussianBlur(radius=6))
    comb_mask = ImageChops.lighter(mask, ImageEnhance.Brightness(seg_gray).enhance(0.55))

    # Blend ref_im and stage_im for the through-projection layer
    through_layer = Image.blend(ref_im, stage_im, 0.42)
    through_layer = ImageEnhance.Contrast(through_layer).enhance(1.12)

    composite = Image.composite(through_layer, base_b, comb_mask).convert("RGBA")

    # Overlay subtle panoptic contour edges (12% opacity) so you see the inverse topology grid reading through
    seg_edges = seg_im.filter(ImageFilter.FIND_EDGES).convert("RGBA")
    r, g, b, _ = seg_edges.split()
    seg_edges = Image.merge("RGBA", (r, g, b, r.point(lambda p: min(55, int(p * 0.35)))))
    composite = Image.alpha_composite(composite, seg_edges)

    # Place poem cut-out props & actors on the ground plane according to `tags_b`
    cutouts = collect_poem_cutouts(poem_str)
    tags_b = [t for t in inv_shot.get("tags_b", []) if t.get("what") != "sky"]
    for idx, (kind, cname, cpath) in enumerate(cutouts[:5]):
        rgba = safe_open_rgba(cpath)
        if not rgba:
            continue
        # Pick horizontal position from tags_b or spread across stage
        if idx < len(tags_b):
            tx = float(tags_b[idx].get("x", 0.25 + idx * 0.14))
            near_m = float(tags_b[idx].get("near") or (45 + idx * 35))
        else:
            tx = 0.22 + idx * 0.15
            near_m = 35.0 + idx * 25.0

        # Compute metric scale from distance in meters (`near_m`)
        dist_factor = max(0.32, min(1.0, 48.0 / math.sqrt(max(12.0, near_m))))
        target_h = int((165 if kind == "prop" else 185) * dist_factor)
        if rgba.height > 0:
            scale = target_h / rgba.height
            tw = max(16, int(rgba.width * scale))
            th = max(16, target_h)
            rgba_s = rgba.resize((tw, th), Image.Resampling.LANCZOS)
        else:
            continue

        px = int(max(40, min(width - tw - 40, tx * width - tw // 2)))
        ground_y = int(hor_y + (height - hor_y) * (1.0 - dist_factor * 0.48))
        py = max(hor_y - th // 2, min(height - th - 26, ground_y - th))

        # Ground contact shadow
        sh = Image.new("RGBA", (tw + 20, 18), (0, 0, 0, 0))
        sdraw = ImageDraw.Draw(sh)
        sdraw.ellipse([4, 2, tw + 16, 16], fill=(5, 8, 12, 135))
        composite.alpha_composite(sh, (px - 10, py + th - 10))
        composite.alpha_composite(rgba_s, (px, py))

    # Overlay Poem Spectrogram Tape strip along the bottom 22px
    if os.path.exists(tape_p):
        tape_im = safe_open_rgb(tape_p, (width, 22)).convert("RGBA")
        composite.alpha_composite(tape_im, (0, height - 22))

    # Draw Horizon Line & Foundry/Inverse Rangefinder Tags
    draw = ImageDraw.Draw(composite)
    # Dashed/subtle horizon line
    for x in range(0, width, 16):
        draw.line([(x, hor_y), (x + 8, hor_y)], fill=(255, 61, 110, 150), width=1)
    draw.text((10, hor_y - 16), f"INVERSE HORIZON {int(hor*100)}% · CAM {int(inv_shot['cam']['z'])}m UP @ {int(inv_shot['cam']['hd'])%360}°", fill=(255, 61, 110, 235), font=FONT_XS)

    # Draw measured tags from tags_b
    for idx, t in enumerate(tags_b[:6]):
        tx = int(max(65, min(width - 95, float(t.get("x", 0.5)) * width)))
        ty = 26 + (idx % 2) * 24
        near = t.get("near")
        dist_str = f"{near/1000:.1f}km" if (near and near >= 1000) else (f"{near}m" if near else "")
        label = f"{t['what']} {t['pct']}%" + (f" · {dist_str}" if dist_str else "")
        is_poem_obj = bool(t.get("poem"))
        col = (255, 61, 110) if is_poem_obj else (255, 210, 63)
        tw_box = len(label) * 6 + 14
        draw.rounded_rectangle([tx - tw_box // 2, ty, tx + tw_box // 2, ty + 19], radius=8, fill=(10, 14, 20, 215), outline=col, width=1)
        draw.text((tx - tw_box // 2 + 7, ty + 2), label, fill=col, font=FONT_XS)
        draw.line([(tx, ty + 19), (tx, min(height - 30, hor_y + 18))], fill=(col[0], col[1], col[2], 125), width=1)

    return composite.convert("RGB")


def build_foundry_inverse_pngs():
    arch = json.load(open(os.path.join(FOUNDRY_DIR, "archive.json")))
    inv = json.load(open(os.path.join(FOUNDRY_DIR, "inverse.json")))
    refs_data = json.load(open(os.path.join(FOUNDRY_DIR, "refs.json")))
    refs_map = {r["id"]: r for r in refs_data["refs"]}
    poems_meta = refs_data["poems"]

    generated_records = []

    # -------------------------------------------------------------------------
    # SERIES A: 28 Inverse-Topology "Triple-Through" Landscape Synthesis PNGs
    # -------------------------------------------------------------------------
    print("Building Series A: 28 Inverse-Topology Triple-Through PNGs...")
    for rid in inv["refs"]:
        ref_obj = refs_map.get(rid)
        if not ref_obj:
            continue
        poem_str = ref_obj["poem"]
        # Find the w1623 shot (or first available world)
        m_shots = [s for s in inv["shots"] if s["ref"] == rid]
        inv_shot = next((s for s in m_shots if s["world"] == "w1623"), m_shots[0] if m_shots else None)
        if not inv_shot:
            continue

        W, H = 1600, 900
        canvas = Image.new("RGB", (W, H), (11, 17, 24))
        draw = ImageDraw.Draw(canvas)

        # Header Bar
        draw.rectangle([0, 0, W, 52], fill=(18, 24, 32))
        draw.line([(0, 52), (W, 52)], fill=(255, 210, 63), width=1)
        title_str = f"INVERSE TOPOLOGY × THROUGH-FRAME BUILD · REF {rid} · POEM {poem_str}: {poems_meta[poem_str]['title'].upper()}"
        draw.text((18, 9), title_str, fill=(255, 210, 63), font=FONT_MD_B)
        sub_str = f"Source: {ref_obj['source'].upper()} · CLIP Fit: {ref_obj['clip']} · Hour: {ref_obj['hour']} · World {inv_shot['world']}: Match {int(inv_shot['before']*100)}% -> {int(inv_shot['after']*100)}% · “{(ref_obj.get('line') or '')[:95]}”"
        draw.text((18, 30), sub_str, fill=(221, 211, 187), font=FONT_SM)

        # Top 4 Comparison Strip (y=62..272)
        pw, ph = 382, 180
        panels = [
            (f"1. REFERENCE ({ref_obj['source'].upper()}) · {rid}", os.path.join(FOUNDRY_DIR, ref_obj["img"]), (255, 210, 63)),
            ("2. PANOPTIC SEGMENTATION (5×12 GRID)", os.path.join(FOUNDRY_DIR, ref_obj["seg"]), (143, 214, 148)),
            (f"3. FOUNDRY CAMERA BEFORE ({int(inv_shot['before']*100)}%)", os.path.join(FOUNDRY_DIR, inv_shot["a"]), (169, 159, 134)),
            (f"4. SCULPTED LAND AFTER ({int(inv_shot['after']*100)}%)", os.path.join(FOUNDRY_DIR, inv_shot["b"]), (255, 61, 110)),
        ]
        for i, (plab, ppath, pcol) in enumerate(panels):
            px = 18 + i * 394
            py = 64
            pim = safe_open_rgb(ppath, (pw, ph))
            canvas.paste(pim, (px, py + 20))
            draw.rectangle([px, py + 20, px + pw, py + 20 + ph], outline=pcol, width=1)
            draw.text((px + 4, py + 2), plab, fill=pcol, font=FONT_SM_B)

        # Bottom Left: Hero "BUILT ON TOP & THROUGH" Synthesis (1180 x 510)
        hero_w, hero_h = 1170, 510
        hero_im = synthesize_through_frame(ref_obj, inv_shot, poem_str, hero_w, hero_h)
        canvas.paste(hero_im, (18, 298))
        draw.rectangle([18, 298, 18 + hero_w, 298 + hero_h], outline=(255, 210, 63), width=2)
        draw.text((22, 278), f"5. BUILT ON TOP & THROUGH: SCULPTED {inv_shot['world'].upper()} + PANOPTIC SKY/WATER APERTURE + POEM {poem_str} MULTIPLANE & CUT-OUT CAST", fill=(255, 210, 63), font=FONT_SM_B)

        # Bottom Right: Sculpted Island Map (`inv/w1623/map-b.jpg`) + Camera Pin + Grown List
        rx, ry, rw = 1204, 298, 378
        map_b_p = os.path.join(FOUNDRY_DIR, f"inv/{inv_shot['world']}/map-b.jpg")
        map_im = safe_open_rgb(map_b_p, (rw, 284))
        # Draw camera wedge pin on map_im (8000x6000m island)
        mdraw = ImageDraw.Draw(map_im)
        cx = int((inv_shot["cam"]["x"] / 8000.0) * rw)
        cy = int((inv_shot["cam"]["y"] / 6000.0) * 284)
        hd_rad = math.radians(inv_shot["cam"].get("hd", 0))
        mdraw.line([(cx, cy), (int(cx + 34 * math.sin(hd_rad - 0.4)), int(cy - 34 * math.cos(hd_rad - 0.4)))], fill=(255, 210, 63), width=2)
        mdraw.line([(cx, cy), (int(cx + 34 * math.sin(hd_rad + 0.4)), int(cy - 34 * math.cos(hd_rad + 0.4)))], fill=(255, 210, 63), width=2)
        mdraw.ellipse([cx - 6, cy - 6, cx + 6, cy + 6], fill=(255, 61, 110), outline=(255, 210, 63), width=2)

        canvas.paste(map_im, (rx, ry))
        draw.rectangle([rx, ry, rx + rw, ry + 284], outline=(255, 61, 110), width=1)
        draw.text((rx + 4, 278), f"6. ISLAND TOPOLOGY ({inv_shot['world']}) & CAMERA WEDGE", fill=(255, 61, 110), font=FONT_SM_B)

        # Info Box below map
        iy = ry + 294
        draw.rectangle([rx, iy, rx + rw, 298 + hero_h], fill=(18, 24, 32), outline=(65, 75, 90), width=1)
        draw.text((rx + 10, iy + 8), "WHAT THE INVERSE SEARCH SCULPTED:", fill=(255, 210, 63), font=FONT_SM_B)
        grown_list = inv_shot.get("grown", []) or ["the world already held this frame"]
        for gi, gtxt in enumerate(grown_list[:4]):
            draw.text((rx + 12, iy + 30 + gi * 20), f"• {gtxt[:52]}", fill=(143, 214, 148), font=FONT_XS)

        # Cross-world comparison row in info box
        draw.text((rx + 10, iy + 118), "ALL 6 WORLDS SCULPTED FOR THIS REF:", fill=(255, 210, 63), font=FONT_XS)
        for wi, ms in enumerate(m_shots[:6]):
            wtxt = f"{ms['world']}: {int(ms['before']*100)}% -> {int(ms['after']*100)}% ({len(ms.get('grown',[]))} grown)"
            draw.text((rx + 12 + (wi % 2) * 182, iy + 138 + (wi // 2) * 18), wtxt, fill=(221, 211, 187), font=FONT_XS)

        # Footer caption
        draw.text((18, 822), f"Reference Desc: {(ref_obj.get('desc') or '')[:145]}", fill=(169, 159, 134), font=FONT_SM)
        frac_str = " · ".join([f"{k}: {round(v)}%" for k, v in sorted(ref_obj.get("frac", {}).items(), key=lambda x: -x[1])[:6]])
        draw.text((18, 844), f"Panoptic Fractions: {frac_str}   |   Camera Pos: ({int(inv_shot['cam']['x'])}m, {int(inv_shot['cam']['y'])}m, {int(inv_shot['cam']['z'])}m) · Heading {int(inv_shot['cam']['hd'])%360}° · FOV {int(inv_shot['cam']['fov'])}°", fill=(143, 214, 148), font=FONT_SM)

        fname = f"inv_triple_{rid.replace('-', '_')}_w1623.png"
        dst = os.path.join(VAULT_FI_DIR, fname)
        sz = save_quantized_png(canvas, dst)
        generated_records.append({
            "id": f"fi_triple_{rid}",
            "title": f"Inverse Triple-Through · Ref {rid} (Poem {poem_str}: {poems_meta[poem_str]['title']})",
            "category": "foundry_inverse",
            "subcategory": "inverse_triple_through",
            "poem": poem_str,
            "ref_id": rid,
            "world": inv_shot["world"],
            "file": f"png_vault/foundry_inverse/{fname}",
            "width": W,
            "height": H,
            "size_kb": round(sz / 1024, 1),
            "desc": f"Through-frame synthesis combining Reference {rid} ({ref_obj['source']}), Panoptic Segmentation, Foundry w1623 Sculpt ({int(inv_shot['before']*100)}%->{int(inv_shot['after']*100)}%), and Poem {poem_str} multiplane cut-out cast."
        })

    # -------------------------------------------------------------------------
    # SERIES B: 14 Poem "Foundry Camera Stand x Multiplane Sidescroller" PNGs
    # -------------------------------------------------------------------------
    print("Building Series B: 14 Poem Foundry Camera Stand x Multiplane PNGs...")
    w1623_obj = arch["worlds"]["w1623"]
    for p_idx in range(1, 15):
        p_str = f"{p_idx:02d}"
        p_info = arch["poems"].get(p_str, poems_meta.get(p_str, {"title": f"Poem {p_str}", "zone": "B", "line": ""}))
        W, H = 1600, 900
        canvas = Image.new("RGB", (W, H), (11, 17, 24))
        draw = ImageDraw.Draw(canvas)

        draw.rectangle([0, 0, W, 52], fill=(18, 24, 32))
        draw.line([(0, 52), (W, 52)], fill=(255, 210, 63), width=1)
        hold_pct = int(round((w1623_obj["r"]["by_poem"].get(p_str, 0.75)) * 100))
        draw.text((18, 9), f"FOUNDRY CAMERA STAND × 6-STOP MULTIPLANE SIDESCROLLER · POEM {p_str}: {p_info.get('title','').upper()}", fill=(255, 210, 63), font=FONT_MD_B)
        draw.text((18, 30), f"World w1623 (Champion 58%) · Poem Hold: {hold_pct}% · Zone: {p_info.get('zone','all')} · “{p_info.get('line','')}”", fill=(221, 211, 187), font=FONT_SM)

        # Top Left: 3 Top Worlds Camera Stands for this poem (w1623, w1578, w0746)
        v_poem = "13" if p_str == "14" else p_str
        for wi, wid in enumerate(["w1623", "w1578", "w0746"]):
            vx = 18 + wi * 388
            vy = 62
            v_path = os.path.join(FOUNDRY_DIR, f"w/{wid}-v{v_poem}.jpg")
            vim = safe_open_rgb(v_path, (376, 168))
            canvas.paste(vim, (vx, vy + 18))
            draw.rectangle([vx, vy + 18, vx + 376, vy + 18 + 168], outline=(255, 210, 63) if wi == 0 else (90, 100, 115), width=1)
            wpct = int(round(arch["worlds"][wid]["r"]["by_poem"].get(p_str, 0.7) * 100))
            draw.text((vx + 4, vy), f"STAND {wid.upper()}-v{v_poem} · HOLDS {wpct}% · {arch['worlds'][wid]['g']['layout'].upper()}", fill=(255, 210, 63) if wi == 0 else (221, 211, 187), font=FONT_XS)

        # Top Right: Poem Reader Checks in w1623
        rx = 1188
        draw.rectangle([rx, 64, W - 18, 248], fill=(18, 24, 32), outline=(65, 75, 90), width=1)
        draw.text((rx + 10, 72), f"POEM {p_str} READER CHECKS (w1623):", fill=(255, 210, 63), font=FONT_SM_B)
        p_checks = w1623_obj["r"]["poems"].get(p_str, [])
        for ci, chk in enumerate(p_checks[:7]):
            ok = chk.get("ok")
            sym = "[+]" if ok else "[-]"
            col = (143, 214, 148) if ok else (255, 107, 94)
            draw.text((rx + 12, 96 + ci * 20), f"{sym} {chk.get('text','')[:42]} [{chk.get('kind','')}]", fill=col, font=FONT_XS)

        # Middle: 6 Multiplane Scene Stops (A -> F) Blended Over the Foundry Stand Horizon (y=260..540)
        draw.text((18, 258), f"6-STOP SIDESCROLLING CORRIDOR (STOPS A -> F) LAYERED ON TOP OF FOUNDRY STAND w1623-v{v_poem}:", fill=(255, 210, 63), font=FONT_SM_B)
        stand_wide = safe_open_rgb(os.path.join(FOUNDRY_DIR, f"w/w1623-v{v_poem}.jpg"), (1564, 310))
        for si in range(6):
            sx = si * 260
            s_path = os.path.join(SHOTS_DIR, "play", "levels", p_str, f"s{si}_ext.webp")
            sim = safe_open_rgb(s_path, (258, 310))
            crop_bg = stand_wide.crop((sx, 0, min(1564, sx + 258), 310)).resize((258, 310))
            blended = Image.blend(crop_bg, sim, 0.58)
            stand_wide.paste(blended, (sx, 0))
            sdraw = ImageDraw.Draw(stand_wide)
            stop_letter = chr(65 + si)
            sdraw.rectangle([sx + 6, 6, sx + 74, 26], fill=(10, 14, 20), outline=(255, 210, 63), width=1)
            sdraw.text((sx + 12, 9), f"STOP {stop_letter} · s{si}", fill=(255, 210, 63), font=FONT_XS)

        # Overlay cut-out props across the 6 stops
        stand_rgba = stand_wide.convert("RGBA")
        cutouts = collect_poem_cutouts(p_str)
        for ci, (kind, cname, cpath) in enumerate(cutouts[:6]):
            rgba = safe_open_rgba(cpath, max_h=145)
            if rgba:
                stand_rgba.alpha_composite(rgba, (80 + ci * 245, 310 - rgba.height - 12))
        canvas.paste(stand_rgba.convert("RGB"), (18, 280))
        draw.rectangle([18, 280, 18 + 1564, 280 + 310], outline=(255, 210, 63), width=1)

        # Bottom: Poem Spectrogram Tape (`poem_tape.webp`) + World Palimpsest Map (`w1623-p.jpg`)
        draw.text((18, 602), f"POEM {p_str} CONTINUOUS SPECTROGRAM GROUND TAPE (poem_tape.webp) + PALIMPSEST MAP (w1623-p.jpg):", fill=(143, 214, 148), font=FONT_SM_B)
        tape_p = os.path.join(SHOTS_DIR, "play", "levels", p_str, "poem_tape.webp")
        tape_im = safe_open_rgb(tape_p, (1180, 240))
        canvas.paste(tape_im, (18, 624))
        draw.rectangle([18, 624, 18 + 1180, 624 + 240], outline=(143, 214, 148), width=1)

        pal_im = safe_open_rgb(os.path.join(FOUNDRY_DIR, "w/w1623-p.jpg"), (374, 240))
        canvas.paste(pal_im, (1208, 624))
        draw.rectangle([1208, 624, 1208 + 374, 624 + 240], outline=(255, 61, 110), width=1)

        fname = f"foundry_stand_poem_{p_str}.png"
        dst = os.path.join(VAULT_FI_DIR, fname)
        sz = save_quantized_png(canvas, dst)
        generated_records.append({
            "id": f"fi_stand_{p_str}",
            "title": f"Foundry Stand × 6-Stop Sidescroller · Poem {p_str}: {p_info.get('title','')}",
            "category": "foundry_inverse",
            "subcategory": "foundry_camera_stand",
            "poem": p_str,
            "world": "w1623",
            "file": f"png_vault/foundry_inverse/{fname}",
            "width": W,
            "height": H,
            "size_kb": round(sz / 1024, 1),
            "desc": f"Foundry camera stand w1623-v{v_poem} ({hold_pct}% hold) layered with Poem {p_str}'s 6 multiplane stops (A->F), cut-out props, reader checks, and spectrogram ground tape."
        })

    # -------------------------------------------------------------------------
    # SERIES C: 14 Poem "Interior Walk-In Sets (Interiors Become Sets)" PNGs
    # -------------------------------------------------------------------------
    print("Building Series C: 14 Poem Interior Walk-In Set PNGs...")
    for p_idx in range(1, 15):
        p_str = f"{p_idx:02d}"
        p_info = poems_meta.get(p_str, arch["poems"].get(p_str, {"title": f"Poem {p_str}", "text": [""]}))
        p_refs = [r for r in refs_data["refs"] if r["poem"] == p_str]
        set_refs = [r for r in p_refs if r["id"] not in inv["refs"]] or p_refs or [refs_data["refs"][p_idx % len(refs_data["refs"])]]

        W, H = 1600, 900
        canvas = Image.new("RGB", (W, H), (10, 14, 20))
        draw = ImageDraw.Draw(canvas)

        draw.rectangle([0, 0, W, 52], fill=(18, 24, 32))
        draw.line([(0, 52), (W, 52)], fill=(255, 61, 110), width=1)
        draw.text((18, 9), f"INVERSE TOPOLOGY · “INTERIORS BECOME WALK-IN SETS” · POEM {p_str}: {p_info['title'].upper()}", fill=(255, 61, 110), font=FONT_MD_B)
        draw.text((18, 30), f"{len(set_refs)} Walk-In Set References (No Horizon -> Shapes Walls, Windows, Light & Lenses) + Window Portal to Foundry World w1623", fill=(221, 211, 187), font=FONT_SM)

        # Top Strip: Up to 4 Walk-In Set Reference Pairs (Image + Panoptic Seg)
        for ri, r in enumerate(set_refs[:4]):
            rx = 18 + ri * 394
            ry = 64
            rim = safe_open_rgb(os.path.join(FOUNDRY_DIR, r["img"]), (190, 155))
            sim = safe_open_rgb(os.path.join(FOUNDRY_DIR, r["seg"]), (190, 155))
            canvas.paste(rim, (rx, ry + 20))
            canvas.paste(sim, (rx + 192, ry + 20))
            draw.rectangle([rx, ry + 20, rx + 382, ry + 20 + 155], outline=(255, 61, 110), width=1)
            draw.text((rx + 4, ry + 2), f"SET REF {r['id']} ({r['source'].upper()}) · {r['hour'].upper()} · CLIP {r['clip']}", fill=(255, 210, 63), font=FONT_XS)

        # Hero Walk-In Set Composite (y=258..855):
        # Takes primary interior ref + Poem s0_ext.webp interior room + cuts a window aperture to Foundry w1623 outside + stages cutouts!
        r0 = set_refs[0]
        room_bg = safe_open_rgb(os.path.join(SHOTS_DIR, "play", "levels", p_str, "s0_ext.webp"), (1564, 580))
        ref_bg = safe_open_rgb(os.path.join(FOUNDRY_DIR, r0["img"]), (1564, 580))
        walkin = Image.blend(room_bg, ref_bg, 0.45).convert("RGBA")

        # Cut an architectural "Window / Door Portal to the Foundry World Outside"
        v_poem = "13" if p_str == "14" else p_str
        outside_im = safe_open_rgb(os.path.join(FOUNDRY_DIR, f"w/w1623-v{v_poem}.jpg"), (460, 250)).convert("RGBA")
        wdraw = ImageDraw.Draw(outside_im)
        # Window muntin bars
        wdraw.rectangle([0, 0, 459, 249], outline=(255, 210, 63, 220), width=4)
        wdraw.line([(230, 0), (230, 250)], fill=(255, 210, 63, 180), width=3)
        wdraw.line([(0, 125), (460, 125)], fill=(255, 210, 63, 180), width=3)
        wdraw.rectangle([8, 8, 310, 28], fill=(10, 14, 20, 210))
        wdraw.text((14, 11), f"THROUGH-WINDOW PORTAL -> FOUNDRY w1623-v{v_poem}", fill=(255, 210, 63, 255), font=FONT_XS)
        walkin.alpha_composite(outside_im, (552, 58))

        # Stage cut-out props & characters inside the walk-in set
        cutouts = collect_poem_cutouts(p_str)
        for ci, (kind, cname, cpath) in enumerate(cutouts[:6]):
            rgba = safe_open_rgba(cpath, max_h=275 if kind == "actor" else 220)
            if rgba:
                px = 90 + ci * 240
                py = 560 - rgba.height
                walkin.alpha_composite(rgba, (px, max(40, py)))

        canvas.paste(walkin.convert("RGB"), (18, 270))
        draw.rectangle([18, 270, 18 + 1564, 270 + 580], outline=(255, 61, 110), width=2)
        draw.text((22, 250), f"WALK-IN MULTIPLANE SET SYNTHESIS: INTERIOR REF {r0['id']} + STAGE {p_str}/s0_ext + THROUGH-WINDOW PORTAL TO w1623 + CUT-OUT CAST", fill=(255, 210, 63), font=FONT_SM_B)

        fname = f"inverse_walkin_set_poem_{p_str}.png"
        dst = os.path.join(VAULT_FI_DIR, fname)
        sz = save_quantized_png(canvas, dst)
        generated_records.append({
            "id": f"fi_walkin_{p_str}",
            "title": f"Inverse Walk-In Set · Poem {p_str}: {p_info['title']}",
            "category": "foundry_inverse",
            "subcategory": "walkin_interior_set",
            "poem": p_str,
            "ref_id": r0["id"],
            "world": "w1623",
            "file": f"png_vault/foundry_inverse/{fname}",
            "width": W,
            "height": H,
            "size_kb": round(sz / 1024, 1),
            "desc": f"Walk-in interior set synthesis for Poem {p_str} built from non-horizon references ({', '.join(r['id'] for r in set_refs[:4])}) with through-window Foundry view and cut-out cast."
        })

    # -------------------------------------------------------------------------
    # SERIES D: 6 Foundry World "4-State Cartographic & Route Atlas" PNGs
    # -------------------------------------------------------------------------
    print("Building Series D: 6 Foundry World 4-State Cartographic PNGs...")
    for wid in inv["worlds"]:
        w_obj = arch["worlds"][wid]
        W, H = 1600, 900
        canvas = Image.new("RGB", (W, H), (11, 17, 24))
        draw = ImageDraw.Draw(canvas)

        q_pct = int(round(w_obj.get("q", w_obj["r"]["score"]) * 100))
        r_pct = int(round(w_obj["r"]["score"] * 100))
        b_pct = int(round((w_obj.get("b", {}).get("score", 0)) * 100))
        w_shots = [s for s in inv["shots"] if s["world"] == wid]
        grown_cnt = sum(len(s.get("grown", [])) for s in w_shots)

        draw.rectangle([0, 0, W, 52], fill=(18, 24, 32))
        draw.line([(0, 52), (W, 52)], fill=(255, 210, 63), width=1)
        draw.text((18, 9), f"FOUNDRY × INVERSE CARTOGRAPHIC ATLAS · WORLD {wid.upper()} (GEN {w_obj['gen']} · NICHE {w_obj['cell']})", fill=(255, 210, 63), font=FONT_MD_B)
        draw.text((18, 30), f"Together: {q_pct}% · Poems: {r_pct}% · Builder: {b_pct}% · Layout: {w_obj['g']['layout']} · Street: {w_obj['d']['street_km']} km · Inverse Sculpted: {grown_cnt} features across {len(w_shots)} shots", fill=(221, 211, 187), font=FONT_SM)

        maps_4 = [
            (f"1. DISTRICT & NATURE MAP (w/{wid}.jpg)", os.path.join(FOUNDRY_DIR, f"w/{wid}.jpg"), (255, 210, 63)),
            (f"2. EPOCH PALIMPSEST PAINTING (w/{wid}-p.jpg)", os.path.join(FOUNDRY_DIR, f"w/{wid}-p.jpg"), (143, 214, 148)),
            (f"3. INVERSE TOPOLOGY BEFORE (inv/{wid}/map-a.jpg)", os.path.join(FOUNDRY_DIR, f"inv/{wid}/map-a.jpg"), (169, 159, 134)),
            (f"4. INVERSE SCULPTED AFTER + WEDGES (inv/{wid}/map-b.jpg)", os.path.join(FOUNDRY_DIR, f"inv/{wid}/map-b.jpg"), (255, 61, 110)),
        ]
        for mi, (mlab, mpath, mcol) in enumerate(maps_4):
            mx = 18 + (mi % 2) * 536
            my = 64 + (mi // 2) * 412
            mim = safe_open_rgb(mpath, (520, 375))
            canvas.paste(mim, (mx, my + 20))
            draw.rectangle([mx, my + 20, mx + 520, my + 20 + 375], outline=mcol, width=1)
            draw.text((mx + 4, my + 2), mlab, fill=mcol, font=FONT_SM_B)

        # Right Sidebar (x=1092..1582): Recipe, Poem Hold Bars, Builder Checks
        rx = 1092
        draw.rectangle([rx, 64, W - 18, H - 20], fill=(18, 24, 32), outline=(65, 75, 90), width=1)
        draw.text((rx + 12, 74), f"WORLD {wid.upper()} RECIPE & EPOCHS:", fill=(255, 210, 63), font=FONT_SM_B)
        for ri, rline in enumerate(w_obj.get("recipe", [])[:6]):
            draw.text((rx + 14, 98 + ri * 20), f"{ri+1}. {rline[:56]}", fill=(221, 211, 187), font=FONT_XS)

        draw.text((rx + 12, 232), "POEM-BY-POEM HOLD SCORES (01–14):", fill=(255, 210, 63), font=FONT_SM_B)
        for pi in range(1, 15):
            ps = f"{pi:02d}"
            sc = w_obj["r"]["by_poem"].get(ps, 0.0)
            by = 258 + (pi - 1) * 24
            draw.text((rx + 14, by), f"P{ps} {arch['poems'][ps]['title'][:18]:18s}", fill=(221, 211, 187), font=FONT_XS)
            draw.rectangle([rx + 185, by + 3, rx + 415, by + 13], fill=(29, 37, 46))
            draw.rectangle([rx + 185, by + 3, rx + 185 + int(230 * sc), by + 13], fill=(255, 210, 63))
            draw.text((rx + 422, by), f"{int(round(sc*100))}%", fill=(143, 214, 148), font=FONT_XS)

        draw.text((rx + 12, 608), "BUILDER VERIFICATION CHECKS:", fill=(255, 210, 63), font=FONT_SM_B)
        for bi, bchk in enumerate((w_obj.get("b", {}).get("checks", []))[:10]):
            ok = bchk.get("ok")
            warn = bchk.get("warn")
            sym = "[+]" if ok else ("~" if warn else "[-]")
            col = (143, 214, 148) if ok else ((240, 192, 96) if warn else (255, 107, 94))
            draw.text((rx + 14, 632 + bi * 22), f"{sym} {bchk.get('text','')[:46]} [{bchk.get('area','')}]", fill=col, font=FONT_XS)

        fname = f"foundry_world_atlas_{wid}.png"
        dst = os.path.join(VAULT_FI_DIR, fname)
        sz = save_quantized_png(canvas, dst)
        generated_records.append({
            "id": f"fi_world_{wid}",
            "title": f"Foundry 4-State Cartographic Atlas · World {wid} ({q_pct}%)",
            "category": "foundry_inverse",
            "subcategory": "foundry_world_atlas",
            "poem": "all",
            "world": wid,
            "file": f"png_vault/foundry_inverse/{fname}",
            "width": W,
            "height": H,
            "size_kb": round(sz / 1024, 1),
            "desc": f"4-state cartographic comparison of Foundry World {wid}: District Map, Palimpsest Painting, Inverse Pre-Sculpt Map, and Inverse Post-Sculpt Map with 28 camera wedges."
        })

    print(f"Built {len(generated_records)} Foundry+Inverse PNGs in {VAULT_FI_DIR}.")
    return generated_records


def classify_artifact_png(fname):
    low = fname.lower()
    if any(k in low for k in ("scene", "poem_tape", "multiplane", "backdrop", "lego_arch", "contact_poems", "plates_01")):
        return ("scenes_multiplane", "Multiplane Scenes, Poem Tapes & World Backdrops")
    if any(k in low for k in ("face", "head", "hand", "shoe", "feet", "eye", "mouth", "nose", "prof", "yp_")):
        return ("faces_hands_shoes", "Faces, Heads, Hands & Shoes Audits")
    if any(k in low for k in ("crash_lab", "assembly", "asm_", "body_lab", "stage_scene", "stage_rig", "suite_player", "cards_")):
        return ("studios_crash_assembly", "Crash Lab, Assembly, Body Lab & Stage Proofs")
    if any(k in low for k in ("escalator", "orange", "kids", "storm_chapel", "catwalk", "crimson", "naraka", "ankhu", "arcade", "cenotaph", "overseer", "commons", "temple", "plaza", "ascent", "hive", "bay", "sightline", "stairs", "deconed", "latent", "cel_vj")):
        return ("halfworld_3d_stages", "Halfworld 3D Stages, Escalator, Orange & Naraka")
    if any(k in low for k in ("set_sheets", "non_set_sheets", "sheet", "prop", "cuts_p", "woman_family_cuts", "cuts_index")):
        return ("cut_sheets_props", "Cut-Sheet & Prop Inspections")
    return ("character_rigs_bodies", "Character Rigs, 4-Angle Bodies & Scion Proofs")


def copy_and_optimize_artifact_pngs():
    print("Scanning & optimizing artifact PNGs from brain directory...")
    pngs = sorted(
        glob.glob(os.path.join(BRAIN_DIR, "*.png")) + glob.glob(os.path.join(BRAIN_DIR, "scratch", "*.png")),
        key=os.path.getmtime,
        reverse=True,
    )
    seen_hashes = set()
    used_names = set()
    records = []

    for p in pngs:
        raw_sz = os.path.getsize(p)
        if raw_sz < 2000:
            continue
        h = hashlib.md5(open(p, "rb").read()).hexdigest()
        if h in seen_hashes:
            continue
        seen_hashes.add(h)

        base_name = os.path.basename(p)
        if base_name in used_names:
            base_name = f"scratch_{base_name}"
        used_names.add(base_name)

        dst_path = os.path.join(VAULT_ART_DIR, base_name)
        try:
            im = Image.open(p)
            orig_w, orig_h = im.size
            # Smart resize so tall contact sheets stay crisp (width up to 1450, max side up to 2800)
            w, h_px = orig_w, orig_h
            if max(w, h_px) > 2600 or min(w, h_px) > 1500:
                scale = min(2600 / max(w, h_px), 1500 / min(w, h_px))
                w = max(1, int(w * scale))
                h_px = max(1, int(h_px * scale))
                im = im.resize((w, h_px), Image.Resampling.LANCZOS)
            opt_sz = save_quantized_png(im, dst_path, colors=256)
        except Exception as e:
            print(f"  Warning on {p}: {e}")
            continue

        cat_key, cat_label = classify_artifact_png(base_name)
        mtime_str = time.strftime("%Y-%m-%d %H:%M", time.localtime(os.path.getmtime(p)))
        clean_title = base_name.replace(".png", "").replace("scratch_", "").replace("verify_", "").replace("_", " ").title()

        records.append({
            "id": f"art_{base_name.replace('.png','')}",
            "title": clean_title,
            "filename": base_name,
            "category": cat_key,
            "category_label": cat_label,
            "created": mtime_str,
            "file": f"png_vault/artifacts/{base_name}",
            "orig_width": orig_w,
            "orig_height": orig_h,
            "width": w,
            "height": h_px,
            "size_kb": round(opt_sz / 1024, 1),
            "desc": f"Generated project proof/audit PNG ({orig_w}×{orig_h}px · {mtime_str}) — {cat_label}."
        })

    print(f"Optimized & saved {len(records)} unique artifact PNGs into {VAULT_ART_DIR}.")
    return records


def collect_repo_kit_and_scene_pngs():
    """Also indexes the 365 Master Kit Cut-Out PNG Sheets and 90 Multiplane Scene Plates so the PNG browser can show everything."""
    records = []
    # 1. 90 Multiplane Scene Plates & 14 Poem Tapes
    for p_idx in range(1, 15):
        p_str = f"{p_idx:02d}"
        tape_f = f"play/levels/{p_str}/poem_tape.webp"
        if os.path.exists(os.path.join(SHOTS_DIR, tape_f)):
            records.append({
                "id": f"repo_tape_{p_str}",
                "title": f"Poem {p_str} Continuous Spectrogram Tape",
                "filename": f"poem_{p_str}_tape.webp",
                "category": "repo_multiplane_plates",
                "category_label": "90 Multiplane Scene Plates & 14 Poem Tapes",
                "poem": p_str,
                "file": tape_f,
                "width": 2400,
                "height": 270,
                "size_kb": round(os.path.getsize(os.path.join(SHOTS_DIR, tape_f)) / 1024, 1),
                "desc": f"Continuous visual spectrogram & terrain ground ribbon for Poem {p_str}."
            })
        for si in range(6):
            sf = f"play/levels/{p_str}/s{si}_ext.webp"
            if os.path.exists(os.path.join(SHOTS_DIR, sf)):
                records.append({
                    "id": f"repo_scene_{p_str}_s{si}",
                    "title": f"Poem {p_str} · Stop {chr(65+si)} (s{si}_ext)",
                    "filename": f"poem_{p_str}_s{si}_ext.webp",
                    "category": "repo_multiplane_plates",
                    "category_label": "90 Multiplane Scene Plates & 14 Poem Tapes",
                    "poem": p_str,
                    "file": sf,
                    "width": 1600,
                    "height": 900,
                    "size_kb": round(os.path.getsize(os.path.join(SHOTS_DIR, sf)) / 1024, 1),
                    "desc": f"Seamless multiplane stage plate for Poem {p_str} Stop {chr(65+si)}."
                })

    # 2. Master Kit PNG Sheets from release_catalog.json if present
    cat_p = os.path.join(SHOTS_DIR, "arena", "parts", "kit3", "release_v2", "release_catalog.json")
    if os.path.exists(cat_p):
        try:
            rcat = json.load(open(cat_p))
            for sh in rcat.get("sheets", [])[:365]:
                f_rel = sh.get("sheet_rel") or sh.get("original_file") or ""
                if f_rel.startswith("shots/"):
                    f_rel = f_rel[len("shots/"):]
                p_full = os.path.join(SHOTS_DIR, f_rel)
                if not os.path.exists(p_full):
                    alt = os.path.join("arena/parts/kit3/release_v2", f_rel)
                    if os.path.exists(os.path.join(SHOTS_DIR, alt)):
                        f_rel = alt
                        p_full = os.path.join(SHOTS_DIR, f_rel)
                if f_rel and os.path.exists(p_full):
                    p_list = sh.get("poems") or []
                    p_str = str(p_list[0]).zfill(2) if p_list else "all"
                    sid = sh.get("id") or os.path.basename(f_rel)
                    records.append({
                        "id": f"kit_sheet_{sid}",
                        "title": f"Kit Sheet · {sid}",
                        "filename": os.path.basename(f_rel),
                        "category": "repo_kit_sheets",
                        "category_label": "365 Master Cut-Out Kit PNG Sheets",
                        "poem": p_str,
                        "file": f_rel,
                        "width": sh.get("width", 1024),
                        "height": sh.get("height", 1536),
                        "size_kb": round(os.path.getsize(p_full) / 1024, 1),
                        "desc": f"Master gouache cut-out sheet ({sh.get('part_count', 0)} cut pieces) · {sh.get('kind', 'kit')}."
                    })
        except Exception as e:
            print("Warning reading release_catalog:", e)

    return records


def main():
    t0 = time.time()
    fi_records = build_foundry_inverse_pngs()
    art_records = copy_and_optimize_artifact_pngs()
    repo_records = collect_repo_kit_and_scene_pngs()

    all_items = []
    for r in fi_records:
        r["category_label"] = "Foundry & Inverse Through-Frame Builds (NEW · 62 PNGs)"
        r["filename"] = os.path.basename(r["file"])
        r["created"] = time.strftime("%Y-%m-%d %H:%M")
        all_items.append(r)
    all_items.extend(art_records)
    all_items.extend(repo_records)

    # Compute category counts
    cats = {}
    for it in all_items:
        c = it["category"]
        if c not in cats:
            cats[c] = {"id": c, "label": it.get("category_label", c), "count": 0}
        cats[c]["count"] += 1

    catalog = {
        "generated_at": time.strftime("%Y-%m-%dT%H:%M:%SZ"),
        "total_count": len(all_items),
        "vault_png_count": len(fi_records) + len(art_records),
        "foundry_inverse_count": len(fi_records),
        "artifact_png_count": len(art_records),
        "repo_plates_and_sheets_count": len(repo_records),
        "categories": list(cats.values()),
        "items": all_items,
    }

    cat_dst = os.path.join(VAULT_DIR, "png_catalog.json")
    with open(cat_dst, "w") as f:
        json.dump(catalog, f, indent=2)

    tot_vault_mb = (
        sum(os.path.getsize(os.path.join(SHOTS_DIR, r["file"])) for r in (fi_records + art_records))
        / (1024 * 1024)
    )
    print(f"Done in {time.time()-t0:.1f}s! Catalog written to {cat_dst}")
    print(f"  Foundry+Inverse PNGs: {len(fi_records)}")
    print(f"  Saved Artifact PNGs:  {len(art_records)}")
    print(f"  Repo Plates & Sheets: {len(repo_records)}")
    print(f"  Total Indexed Plates: {len(all_items)} (Vault disk size: {tot_vault_mb:.1f} MB)")


if __name__ == "__main__":
    main()
