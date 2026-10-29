#!/usr/bin/env python3
"""
build_terrarium_worlds.py
Compiles:
1. Foundry Evolved Worlds (w1623, w1578, w0746, w1165, w0889, w0980 + w1623-sculpted)
   into full 3D Terrarium Landpacks (`unsettled.landpack/v1`) with:
   - True 12-bit heightfield `hf` derived from the world's topography genome, bathymetry,
     and inverse-topology sculpted camera stands (`shots.json` & `inverse.json`),
   - Ground texture `tex` (dataURL) + switchable `tex_palimpsest` and `tex_sculpted`,
   - Extruded 3D buildings `bld` across Baltimere, The Center, and Atlantis,
   - Full `wygwyl` poem camera stands, set pieces, multiplane scenes, and film clips.
2. Enriches all 10 Scouted Real-City Landpacks (`mount-vernon`, `fells-point`, etc.)
   with their `wt/01..14.json` WorldText stops, our 90 custom sidescrolling scenes
   (`play/levels/XX/s0_ext.webp..s5_ext.webp`), `poem_tape.webp` ground strips,
   cut-out props (`play/levels/XX/props/*.png`), and playable film clips (`PXX-00Y.mp4`).
3. Outputs `shots/data/terrarium/terrarium_master_index.json` for `shots/terrarium.html`
   and the Interactive AI Dog Helper.
"""

import base64
import glob
import io
import json
import math
import os
import numpy as np
from PIL import Image

ROOT = "/Users/gaia/WORLDBUILDING-TERMS/wygwyl-world-arch"
SHOTS_DIR = os.path.join(ROOT, "shots")
TERRA_DIR = os.path.join(SHOTS_DIR, "data", "terrarium")
FOUNDRY_DIR = os.path.join(TERRA_DIR, "foundry")
LANDPACK_OUT_DIR = os.path.join(FOUNDRY_DIR, "landpacks")
os.makedirs(LANDPACK_OUT_DIR, exist_ok=True)


def pack_heights_12bit(H_flat, relief):
    """Packs float height array [0..relief] into 12-bit base64 string identical to Terrarium unpackHeights."""
    clamped = np.clip(np.round(H_flat / max(relief, 1e-6) * 4095.0), 0, 4095).astype(np.int32)
    out = bytearray()
    n = len(clamped)
    for i in range(0, n, 2):
        a = int(clamped[i])
        b = int(clamped[i + 1]) if (i + 1) < n else 0
        out.append((a >> 4) & 0xFF)
        out.append(((a & 15) << 4) | ((b >> 8) & 15))
        out.append(b & 0xFF)
    return base64.b64encode(bytes(out)).decode("ascii")


def img_to_data_url(img_path, max_size=(512, 384), quality=78):
    with Image.open(img_path) as im:
        im = im.convert("RGB")
        im.thumbnail(max_size, Image.Resampling.LANCZOS)
        buf = io.BytesIO()
        im.save(buf, format="JPEG", quality=quality)
        b64 = base64.b64encode(buf.getvalue()).decode("ascii")
        return f"data:image/jpeg;base64,{b64}"


def load_json(path, default=None):
    if not os.path.exists(path):
        return default
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def collect_poem_assets():
    """Collects all 90 scenes, poem_tape.webp, props, reading audio, and video clips for Poems 01..14."""
    suite_patches = load_json(os.path.join(SHOTS_DIR, "data", "suite_patches.json"), [])
    cels_patches = load_json(os.path.join(SHOTS_DIR, "data", "cels_patches.json"), [])
    world_data = load_json(os.path.join(TERRA_DIR, "world.json"), {})
    stages_data = load_json(os.path.join(TERRA_DIR, "stages", "stages.json"), {})
    foundry_shots = load_json(os.path.join(FOUNDRY_DIR, "shots.json"), {})
    foundry_refs = load_json(os.path.join(FOUNDRY_DIR, "refs.json"), {})
    foundry_inv = load_json(os.path.join(FOUNDRY_DIR, "inverse.json"), {})

    poems_meta = {}
    for p_num_int in range(1, 15):
        p_num = f"{p_num_int:02d}"
        lvl_dir = os.path.join(SHOTS_DIR, "play", "levels", p_num)
        lvl_json = load_json(os.path.join(lvl_dir, "level.json"), {})

        # 6 Multiplane Scene Plates
        scenes = []
        lvl_scenes = lvl_json.get("scenes", [])
        for s_idx in range(6):
            ext_rel = f"play/levels/{p_num}/s{s_idx}_ext.webp"
            base_rel = f"play/levels/{p_num}/s{s_idx}.webp"
            plate = ext_rel if os.path.exists(os.path.join(SHOTS_DIR, ext_rel)) else base_rel
            s_meta = lvl_scenes[s_idx] if s_idx < len(lvl_scenes) else {}
            scenes.append({
                "idx": s_idx,
                "key": chr(65 + s_idx),
                "name": s_meta.get("name") or s_meta.get("title") or f"Scene {s_idx + 1}",
                "caption": s_meta.get("line") or s_meta.get("caption") or "",
                "plate": plate,
                "base_plate": base_rel,
                "t0": s_meta.get("t0", s_idx * 15),
                "t1": s_meta.get("t1", (s_idx + 1) * 15),
            })

        # Props in play/levels/<p_num>/props/
        prop_files = sorted(glob.glob(os.path.join(lvl_dir, "props", "*.png")))
        props = [f"play/levels/{p_num}/props/{os.path.basename(pf)}" for pf in prop_files]

        # Video clips from suite_patches & cels_patches
        p_tag = f"P{p_num}"
        clips = []
        seen_srcs = set()
        for patch in (suite_patches + cels_patches):
            pid = str(patch.get("id") or patch.get("patch_id") or "")
            p_poem = str(patch.get("poem") or "")
            if pid.startswith(p_tag) or p_poem == p_num or p_poem == str(p_num_int):
                src = patch.get("video") or patch.get("src") or patch.get("file") or ""
                if not src and pid.startswith("P"):
                    cand = f"cel_assets/patches/{pid}.mp4"
                    if os.path.exists(os.path.join(SHOTS_DIR, cand)):
                        src = cand
                if src and src not in seen_srcs:
                    seen_srcs.add(src)
                    clips.append({
                        "id": pid or f"P{p_num}-{len(clips)+1:03d}",
                        "src": src,
                        "thumb": patch.get("thumb") or patch.get("img") or f"cel_assets/thumbs/{pid}.jpg",
                        "line": patch.get("line") or patch.get("text") or patch.get("label") or "",
                        "sign": patch.get("sign") or patch.get("fn") or "PERCEPT",
                        "t0": patch.get("start") or patch.get("t0") or 0,
                        "dur": patch.get("dur") or 5.0
                    })
        # Fallback scan of cel_assets/patches/P<num>-*.mp4
        for mp4_path in sorted(glob.glob(os.path.join(SHOTS_DIR, "cel_assets", "patches", f"P{p_num}-*.mp4"))):
            rel_mp4 = f"cel_assets/patches/{os.path.basename(mp4_path)}"
            pid = os.path.splitext(os.path.basename(mp4_path))[0]
            if rel_mp4 not in seen_srcs:
                seen_srcs.add(rel_mp4)
                clips.append({
                    "id": pid,
                    "src": rel_mp4,
                    "thumb": f"cel_assets/thumbs/{pid}.jpg",
                    "line": f"Poem {p_num} Visual Cut {pid}",
                    "sign": ["PERCEPT", "ACTION", "AFFECT", "OPSIGN", "SONSIGN", "CRYSTAL", "RECOLL"][len(clips) % 7],
                    "t0": len(clips) * 6.0,
                    "dur": 6.0
                })

        # WorldText stops from wt/<p_num>.json
        wt_doc = load_json(os.path.join(TERRA_DIR, "stages", "wt", f"{p_num}.json"), {"stops": []})
        wt_stops = wt_doc.get("stops", [])

        # Foundry references for this poem
        p_refs = [
            {
                "id": r["id"],
                "source": r.get("source", "generated"),
                "desc": r.get("desc", ""),
                "line": r.get("line", ""),
                "clip": r.get("clip", 0.3),
                "img": f"data/terrarium/foundry/{r['img']}",
                "seg": f"data/terrarium/foundry/{r['seg']}" if r.get("seg") else None,
                "hour": r.get("hour", "night"),
            }
            for r in foundry_refs.get("refs", [])
            if r.get("poem") == p_num
        ]

        # Foundry inverse shots for w1623
        p_inv = [
            {
                "world": s["world"],
                "ref": s["ref"],
                "cam": s["cam"],
                "before": s["before"],
                "after": s["after"],
                "grown": s.get("grown", []),
                "a": f"data/terrarium/foundry/{s['a']}",
                "b": f"data/terrarium/foundry/{s['b']}",
            }
            for s in foundry_inv.get("shots", [])
            if s.get("poem") == p_num and s.get("world") == "w1623"
        ]

        # Foundry storyboard shots for w1623
        p_fshots = [
            {
                "id": s.get("id", f"w1623-{p_num}-{s['k']:02d}"),
                "k": s["k"],
                "t0": s["t0"],
                "t1": s["t1"],
                "line": s["line"],
                "kind": s["kind"],
                "mm": s.get("mm", 35),
                "light": s.get("light", "night"),
                "subject": s.get("subject", "the place"),
                "cam": s["cam"],
                "img": f"data/terrarium/foundry/{s['img']}",
                "tags": s.get("tags", []),
            }
            for s in foundry_shots.get("shots", [])
            if s.get("poem") == p_num and s.get("world") == "w1623"
        ]

        poems_meta[p_num] = {
            "num": p_num,
            "title": lvl_json.get("title") or foundry_shots.get("poems", {}).get(p_num, {}).get("title") or f"Poem {p_num}",
            "place": foundry_shots.get("poems", {}).get(p_num, {}).get("place") or lvl_json.get("location") or "",
            "tape": f"play/levels/{p_num}/poem_tape.webp",
            "reading_audio": f"play/levels/{p_num}/reading.mp3",
            "film_mp4": f"film/poem_{p_num}.mp4" if os.path.exists(os.path.join(SHOTS_DIR, f"film/poem_{p_num}.mp4")) else (clips[0]["src"] if clips else ""),
            "scenes": scenes,
            "props": props[:24],
            "clips": clips[:18],
            "wt_stops": wt_stops,
            "foundry_refs": p_refs,
            "foundry_inverse": p_inv,
            "foundry_shots": p_fshots,
        }

    return poems_meta, stages_data, world_data, foundry_shots, foundry_refs, foundry_inv


def build_foundry_landpacks(poems_meta, foundry_shots, foundry_inv):
    """Generates unsettled.landpack/v1 3D landpacks for the 6 elite Foundry worlds + sculpted w1623."""
    archive = load_json(os.path.join(FOUNDRY_DIR, "archive.json"), {})
    worlds_by_id = {w["id"]: w for w in archive.get("worlds", []) if isinstance(w, dict) and "id" in w}

    target_worlds = ["w1623", "w1578", "w0746", "w1165", "w0889", "w0980"]
    generated_packs = []

    for wid in target_worlds:
        map_path = os.path.join(FOUNDRY_DIR, "w", f"{wid}.jpg")
        if not os.path.exists(map_path):
            continue

        w_meta = worlds_by_id.get(wid, {})
        w_shot_meta = foundry_shots.get("worlds", {}).get(wid, {})
        layout_name = w_shot_meta.get("layout") or w_meta.get("g", {}).get("layout", "harbor")

        # Load 800x600 map image to synthesize heightfield + water mask + urban building footprints
        with Image.open(map_path) as im:
            im_rgb = im.convert("RGB")
            nx, nz = 128, 96
            im_small = np.array(im_rgb.resize((nx, nz), Image.Resampling.BILINEAR), dtype=np.float32)

        R = im_small[:, :, 0]
        G = im_small[:, :, 1]
        B = im_small[:, :, 2]

        # Water detection: blue-dominant or dark harbor/sea pixels
        water_score = (B - 0.55 * R - 0.45 * G)
        is_water = (water_score > 14.0) | ((B > R + 8) & (B > G + 4) & (R < 95))

        # Land elevation from luminance + warm ridge/hill tones + smooth radial relief
        lum = (0.299 * R + 0.587 * G + 0.114 * B) / 255.0
        # Green/ochre hills & urban terraces
        hill_boost = np.clip((R - B) / 180.0, 0.0, 1.0) * 0.45 + np.clip((G - B) / 180.0, 0.0, 1.0) * 0.35
        H = np.where(is_water, 0.0, (0.18 + lum * 0.55 + hill_boost * 0.45) * 18.0)

        # Incorporate actual camera stand elevations from shots.json for this world
        w_shots = [s for s in foundry_shots.get("shots", []) if s.get("world") == wid]
        yy, xx = np.mgrid[0:nz, 0:nx]
        for s in w_shots:
            if s.get("k", 0) == 0:
                cx = (s["cam"]["x"] / 8000.0) * (nx - 1)
                cz = (s["cam"]["y"] / 6000.0) * (nz - 1)
                target_h = max(1.5, min(22.0, s["cam"]["z"] / 7.5))
                dist2 = (xx - cx) ** 2 + (yy - cz) ** 2
                H += np.exp(-dist2 / (2.0 * 4.5 ** 2)) * (target_h * 0.25)

        # Smooth heightfield slightly (3x3 box filter) while keeping water flat at 0
        H_pad = np.pad(H, 1, mode="edge")
        H_smooth = (
            H_pad[:-2, :-2] + H_pad[:-2, 1:-1] + H_pad[:-2, 2:] +
            H_pad[1:-1, :-2] + H_pad[1:-1, 1:-1] + H_pad[1:-1, 2:] +
            H_pad[2:, :-2] + H_pad[2:, 1:-1] + H_pad[2:, 2:]
        ) / 9.0
        H_final = np.where(is_water, 0.0, np.clip(H_smooth, 0.4, 24.0))
        relief = float(max(12.0, np.max(H_final)))

        # Generate 3D building footprints (`bld`) across Baltimere, The Center, and Atlantis
        # Terrarium tile dimensions: w=160, h=120 -> x in [-80, 80], z in [-60, 60]
        W_UNITS, H_UNITS = 160.0, 120.0
        blds = []
        rng = np.random.default_rng(abs(hash(wid)) % (2**31))

        # Place district buildings where map shows warm urban stone/terracotta/street clusters
        urban_score = (R - B) + 0.5 * abs(R - G)
        for gy in range(4, nz - 4, 3):
            for gx in range(4, nx - 4, 3):
                if is_water[gy, gx]:
                    continue
                if urban_score[gy, gx] > 28 and lum[gy, gx] > 0.28:
                    wx = (gx / (nx - 1) - 0.5) * W_UNITS + rng.uniform(-1.1, 1.1)
                    wz = (gy / (nz - 1) - 0.5) * H_UNITS + rng.uniform(-1.1, 1.1)
                    if abs(wx) > 76 or abs(wz) > 56:
                        continue
                    bw = rng.uniform(1.1, 2.4)
                    bd = rng.uniform(1.1, 2.4)
                    bh = rng.uniform(2.2, 8.5) if urban_score[gy, gx] > 48 else rng.uniform(1.4, 4.5)
                    p = [
                        [round(wx - bw / 2, 2), round(wz - bd / 2, 2)],
                        [round(wx + bw / 2, 2), round(wz - bd / 2, 2)],
                        [round(wx + bw / 2, 2), round(wz + bd / 2, 2)],
                        [round(wx - bw / 2, 2), round(wz + bd / 2, 2)],
                        [round(wx - bw / 2, 2), round(wz - bd / 2, 2)],
                    ]
                    blds.append({"p": p, "h": round(float(bh), 2)})
                    if len(blds) >= 280:
                        break
            if len(blds) >= 280:
                break

        # Build the 14 Poem Camera Stands & Set-Piece Stops on this Foundry Island
        foundry_poems = []
        for p_num_int in range(1, 15):
            p_num = f"{p_num_int:02d}"
            pm = poems_meta[p_num]
            p_shots = [s for s in w_shots if s.get("poem") == p_num]
            set_pieces = []
            for s_idx in range(6):
                sc = pm["scenes"][s_idx]
                if s_idx < len(p_shots):
                    c = p_shots[s_idx]["cam"]
                    sx = round((c["x"] / 8000.0 - 0.5) * W_UNITS, 2)
                    sz = round((c["y"] / 6000.0 - 0.5) * H_UNITS, 2)
                    hd = round(float(c.get("hd", 0.0)), 1)
                    shot_img = f"data/terrarium/foundry/{p_shots[s_idx]['img']}" if wid == "w1623" else f"data/terrarium/foundry/w/{wid}-v{min(13, p_num_int):02d}.jpg"
                    line_txt = p_shots[s_idx].get("line", sc["caption"])
                else:
                    # Fallback arc for Poem 14 (which re-enters Poem 01 Mount Vernon)
                    angle = (p_num_int * 0.45) + s_idx * 0.18
                    sx = round(math.cos(angle) * (25 + s_idx * 4), 2)
                    sz = round(math.sin(angle) * (20 + s_idx * 3), 2)
                    hd = round((angle * 180 / math.pi) % 360, 1)
                    shot_img = f"data/terrarium/foundry/w/{wid}-v{min(13, p_num_int):02d}.jpg"
                    line_txt = sc["caption"]

                set_pieces.append({
                    "k": chr(65 + s_idx),
                    "name": sc["name"],
                    "line": line_txt,
                    "x": sx,
                    "z": sz,
                    "hd": hd,
                    "plate": sc["plate"],
                    "foundry_img": shot_img,
                    "clip": pm["clips"][s_idx % len(pm["clips"])]["src"] if pm["clips"] else pm["film_mp4"],
                })

            p0 = set_pieces[0]
            foundry_poems.append({
                "num": p_num,
                "title": pm["title"],
                "note": pm["place"],
                "x": p0["x"],
                "z": p0["z"],
                "tape": pm["tape"],
                "reading_audio": pm["reading_audio"],
                "film_mp4": pm["film_mp4"],
                "view_img": f"data/terrarium/foundry/w/{wid}-v{min(13, p_num_int):02d}.jpg",
                "set_pieces": set_pieces,
            })

        # Inverse-topology sculpted wedges for this world
        inv_wedges = [
            {
                "ref": s["ref"],
                "poem": s["poem"],
                "x": round((s["cam"]["x"] / 8000.0 - 0.5) * W_UNITS, 2),
                "z": round((s["cam"]["y"] / 6000.0 - 0.5) * H_UNITS, 2),
                "y": round(s["cam"]["z"] / 8.0, 2),
                "hd": s["cam"]["hd"],
                "fov": s["cam"].get("fov", 50.0),
                "before": s["before"],
                "after": s["after"],
                "grown": s.get("grown", []),
                "a": f"data/terrarium/foundry/{s['a']}",
                "b": f"data/terrarium/foundry/{s['b']}",
            }
            for s in foundry_inv.get("shots", [])
            if s.get("world") == wid
        ]

        tex_data_url = img_to_data_url(map_path)
        pack = {
            "format": "unsettled.landpack/v1",
            "name": f"FOUNDRY {wid.upper()} · {layout_name.upper()}",
            "foundry_id": wid,
            "layout": layout_name,
            "quality": w_shot_meta.get("q", 0.92),
            "recipe": w_shot_meta.get("recipe", []),
            "scale": 50.0,
            "w": W_UNITS,
            "h": H_UNITS,
            "nx": nx,
            "nz": nz,
            "relief": round(relief, 2),
            "zminM": 0.0,
            "reliefM": round(relief * 8.0, 1),
            "spawn": {"x": foundry_poems[0]["x"], "z": foundry_poems[0]["z"], "ry": 0.0},
            "hf": pack_heights_12bit(H_final.flatten(), relief),
            "tex": tex_data_url,
            "tex_map": f"data/terrarium/foundry/w/{wid}.jpg",
            "tex_palimpsest": f"data/terrarium/foundry/w/{wid}-p.jpg",
            "tex_sculpted_before": f"data/terrarium/foundry/inv/{wid}/map-a.jpg",
            "tex_sculpted_after": f"data/terrarium/foundry/inv/{wid}/map-b.jpg",
            "bld": blds,
            "wygwyl": {
                "stage": f"foundry-{wid}",
                "is_foundry": True,
                "foundry_id": wid,
                "layout": layout_name,
                "recipe": w_shot_meta.get("recipe", []),
                "poems": foundry_poems,
                "inverse_wedges": inv_wedges,
            }
        }

        out_file = os.path.join(LANDPACK_OUT_DIR, f"{wid}.landpack.json")
        with open(out_file, "w", encoding="utf-8") as f:
            json.dump(pack, f, separators=(",", ":"))
        generated_packs.append({
            "id": wid,
            "name": pack["name"],
            "layout": layout_name,
            "q": w_shot_meta.get("q", 0.92),
            "poems_score": w_shot_meta.get("poems", 0.92),
            "builder_score": w_shot_meta.get("builder", 0.91),
            "recipe": w_shot_meta.get("recipe", []),
            "landpack_url": f"data/terrarium/foundry/landpacks/{wid}.landpack.json",
            "map_img": f"data/terrarium/foundry/w/{wid}.jpg",
            "palimpsest_img": f"data/terrarium/foundry/w/{wid}-p.jpg",
            "inv_before_img": f"data/terrarium/foundry/inv/{wid}/map-a.jpg",
            "inv_after_img": f"data/terrarium/foundry/inv/{wid}/map-b.jpg",
            "inverse_count": len(inv_wedges),
        })
        print(f"Compiled Foundry 3D Landpack {wid} ({layout_name}): {os.path.getsize(out_file):,} bytes, {len(blds)} 3D buildings, {len(inv_wedges)} inverse wedges")

    return generated_packs


def enrich_real_city_landpacks(poems_meta, stages_data):
    """Enriches the 10 scouted real-city .landpack.json files with full WYGWYL scene plates, clips, props, and WorldText stops."""
    stage_summaries = []
    for s in stages_data.get("stages", []):
        key = s["key"]
        lp_path = os.path.join(TERRA_DIR, "stages", f"{key}.landpack.json")
        if not os.path.exists(lp_path):
            continue
        pack = load_json(lp_path)
        wyg = pack.get("wygwyl", {"stage": key, "poems": s.get("poems", [])})
        mLat = 111320.0
        mLon = 111320.0 * math.cos(float(pack.get("lat", s["lat"])) * math.pi / 180.0)
        S_scale = float(pack.get("scale", 1.84))

        enriched_poems = []
        for p_entry in wyg.get("poems", []):
            p_num = str(p_entry.get("num", "01")).zfill(2)
            pm = poems_meta.get(p_num, {})
            sps = p_entry.get("set_pieces", [])
            enriched_sps = []
            for idx, sp in enumerate(sps):
                sc = pm.get("scenes", [])[idx % len(pm["scenes"])] if pm.get("scenes") else {}
                clip_obj = pm.get("clips", [])[idx % len(pm["clips"])] if pm.get("clips") else {}
                wt_stop = pm.get("wt_stops", [])[idx % len(pm["wt_stops"])] if pm.get("wt_stops") else {}
                enriched_sps.append({
                    "k": sp.get("k", chr(65 + idx)),
                    "name": sp.get("name", sc.get("name", f"Stop {idx+1}")),
                    "x": sp.get("x", 0.0),
                    "z": sp.get("z", 0.0),
                    "lat": sp.get("lat", s["lat"]),
                    "lon": sp.get("lon", s["lon"]),
                    "plate": sc.get("plate", f"play/levels/{p_num}/s{idx % 6}_ext.webp"),
                    "line": wt_stop.get("text") or sc.get("caption") or clip_obj.get("line") or sp.get("name", ""),
                    "clip": clip_obj.get("src") or pm.get("film_mp4", ""),
                    "clip_id": clip_obj.get("id", f"P{p_num}-{idx+1:03d}"),
                    "sign": clip_obj.get("sign", ["PERCEPT", "ACTION", "AFFECT", "OPSIGN", "SONSIGN", "CRYSTAL"][idx % 6]),
                })

            # Also project all wt/<p_num>.json stops into tile (x, z)
            wt_projected = []
            for wst in pm.get("wt_stops", []):
                wx = (float(wst["lon"]) - float(pack.get("lon", s["lon"]))) * mLon / S_scale
                wz = -(float(wst["lat"]) - float(pack.get("lat", s["lat"]))) * mLat / S_scale
                wt_projected.append({
                    "lat": wst["lat"],
                    "lon": wst["lon"],
                    "x": round(wx, 2),
                    "z": round(wz, 2),
                    "text": wst["text"],
                })

            enriched_poems.append({
                "num": p_num,
                "title": p_entry.get("title", pm.get("title", "")),
                "note": p_entry.get("note", pm.get("place", "")),
                "lat": p_entry.get("lat", s["lat"]),
                "lon": p_entry.get("lon", s["lon"]),
                "tape": pm.get("tape", f"play/levels/{p_num}/poem_tape.webp"),
                "reading_audio": pm.get("reading_audio", f"play/levels/{p_num}/reading.mp3"),
                "film_mp4": pm.get("film_mp4", f"film/poem_{p_num}.mp4"),
                "props": pm.get("props", []),
                "clips": pm.get("clips", []),
                "set_pieces": enriched_sps,
                "wt_stops": wt_projected,
                "foundry_refs": pm.get("foundry_refs", []),
                "foundry_inverse": pm.get("foundry_inverse", []),
            })

        wyg["poems"] = enriched_poems
        pack["wygwyl"] = wyg
        with open(lp_path, "w", encoding="utf-8") as f:
            json.dump(pack, f, separators=(",", ":"))

        stage_summaries.append({
            "key": key,
            "name": s["name"],
            "lat": s["lat"],
            "lon": s["lon"],
            "poems": [p["num"] for p in enriched_poems],
            "landpack_url": f"data/terrarium/stages/{key}.landpack.json",
            "wt_urls": [f"data/terrarium/stages/wt/{p['num']}.json" for p in enriched_poems],
            "set_piece_count": sum(len(p["set_pieces"]) for p in enriched_poems),
        })
        print(f"Enriched Real-City Landpack {key}: poems={[p['num'] for p in enriched_poems]}, {os.path.getsize(lp_path):,} bytes")

    return stage_summaries


def main():
    poems_meta, stages_data, world_data, foundry_shots, foundry_refs, foundry_inv = collect_poem_assets()
    foundry_packs = build_foundry_landpacks(poems_meta, foundry_shots, foundry_inv)
    real_stages = enrich_real_city_landpacks(poems_meta, stages_data)

    # Load character rigs summary for the Dog AI Helper
    rigs_lib = load_json(os.path.join(SHOTS_DIR, "arena", "parts", "kit3", "release_v2", "character_rigs_library.json"), {})
    rigs_list = []
    rigs_raw = rigs_lib.get("rigs", {}) if isinstance(rigs_lib, dict) else {}
    rigs_iter = rigs_raw.values() if isinstance(rigs_raw, dict) else rigs_raw
    for r in rigs_iter:
        if not isinstance(r, dict):
            continue
        rp = r.get("resolved_parts", {})
        first_part = ""
        if isinstance(rp, dict) and rp:
            first_val = next(iter(rp.values()))
            first_part = first_val.get("file", "") if isinstance(first_val, dict) else str(first_val)
        rigs_list.append({
            "id": r.get("id"),
            "name": r.get("name"),
            "poems": r.get("poems", []),
            "height_ratio": r.get("canonical_height_stage_ratio", 0.54),
            "preview_part": first_part,
        })

    master_index = {
        "version": "wygwyl-terrarium-v2",
        "real_stages": real_stages,
        "foundry_worlds": foundry_packs,
        "poems": poems_meta,
        "character_rigs": rigs_list,
    }
    master_out = os.path.join(TERRA_DIR, "terrarium_master_index.json")
    with open(master_out, "w", encoding="utf-8") as f:
        json.dump(master_index, f, indent=2)
    print(f"Saved master index: {master_out} ({os.path.getsize(master_out):,} bytes)")


if __name__ == "__main__":
    main()
