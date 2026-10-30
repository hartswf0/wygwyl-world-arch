#!/usr/bin/env python3
"""
paint_all_shots_and_tapes.py
============================
Paints and shapes EVERY SINGLE ONE of the 155 Poem Shots (`01-00` .. `14-07`, covering all
147 canonical `w1623` Foundry shots in `shots.json` + 8 Poem 14 shots) AND all 28 Inverse-Sculpted
Through-Frames (`inverse.json`) into pure, borderless, 7-plane gouache cinema frames (`1280x560`),
and weaves each poem's painted shots into a continuous, seamless horizontal Shot-by-Shot Cinema Tape
(`shots/png_vault/painted_tapes/poem_01_shot_tape.png` .. `poem_14_shot_tape.png`).

Also updates `shots/png_vault/png_catalog.json` so every newly painted shot, inverse through-frame,
scene tape, and shot tape is immediately browsable in `shots/png_browser.html` and `shots/foundry_inverse.html`.
"""

from __future__ import annotations

import json
import math
import pathlib
import sys
from typing import Any, Dict, List, Optional, Tuple

import cv2
import numpy as np
from PIL import Image, ImageDraw, ImageEnhance, ImageFilter, ImageFont

ROOT_DIR = pathlib.Path(__file__).resolve().parents[3]
SHOTS_DIR = ROOT_DIR / "shots"
FOUNDRY_DIR = SHOTS_DIR / "data" / "terrarium" / "foundry"
LEVELS_DIR = SHOTS_DIR / "play" / "levels"
VAULT_DIR = SHOTS_DIR / "png_vault"
PAINTED_SHOTS_DIR = VAULT_DIR / "painted_shots"
PAINTED_TAPES_DIR = VAULT_DIR / "painted_tapes"
SCRATCH_DIR = pathlib.Path("/Users/gaia/.gemini/antigravity/brain/f76dabc9-fb98-42f7-bec0-54be580e5584")

# Import our cel-gouache cutout integration, portal footage & spectrogram helpers from build_custom_90_scenes.py
sys.path.insert(0, str(SHOTS_DIR / "arena" / "parts" / "kit3"))
import build_custom_90_scenes as b90  # noqa: E402


def _load_font(size: int, bold: bool = False) -> ImageFont.FreeTypeFont | ImageFont.ImageFont:
    candidates = [
        "/System/Library/Fonts/HelveticaNeue.ttc",
        "/System/Library/Fonts/Supplemental/Arial Bold.ttf" if bold else "/System/Library/Fonts/Supplemental/Arial.ttf",
        "/System/Library/Fonts/Menlo.ttc",
    ]
    for c in candidates:
        p = pathlib.Path(c)
        if p.exists():
            try:
                return ImageFont.truetype(str(p), size=size, index=1 if (bold and c.endswith(".ttc")) else 0)
            except Exception:
                try:
                    return ImageFont.truetype(str(p), size=size)
                except Exception:
                    pass
    return ImageFont.load_default()


FONT_XS = _load_font(11, bold=False)
FONT_SM = _load_font(12, bold=True)
FONT_MD = _load_font(14, bold=True)
FONT_LG = _load_font(17, bold=True)

# Light-state RGB target tints for Foundry shot `light` values
LIGHT_TINTS: Dict[str, Tuple[float, float, float]] = {
    "dusk→night": (214.0, 118.0, 78.0),
    "dusk": (228.0, 132.0, 86.0),
    "night": (22.0, 34.0, 68.0),
    "dim": (36.0, 48.0, 64.0),
    "first light": (188.0, 152.0, 138.0),
    "morning": (162.0, 198.0, 228.0),
    "day": (152.0, 196.0, 232.0),
    "golden hour": (244.0, 168.0, 82.0),
    "storm": (64.0, 78.0, 96.0),
}

# Full-body cast fallback library (strictly full-body figures, never headless torso vests)
FULL_BODY_ACTOR_FILES = [
    "weave/cast/man/library/misc/body_front.png",
    "weave/cast/man/library/misc/body_threequarter.png",
    "weave/cast/man/library/misc/body_profile.png",
    "weave/cast/man/library/misc/body_back.png",
]


def _harmonize_image_to_palette(
    src_np: np.ndarray,
    ref_np: np.ndarray,
    lum_weight: float = 0.48,
    chroma_weight: float = 0.82,
    bilateral: bool = True,
) -> np.ndarray:
    """Harmonizes `src_np` (H,W,3 float32) toward `ref_np` (H,W,3 float32) in CIE-LAB + bilateral gouache filter."""
    s_u8 = np.clip(src_np, 0, 255).astype(np.uint8)
    r_u8 = np.clip(ref_np, 0, 255).astype(np.uint8)
    s_lab = cv2.cvtColor(s_u8, cv2.COLOR_RGB2LAB).astype(np.float32)
    r_lab = cv2.cvtColor(r_u8, cv2.COLOR_RGB2LAB).astype(np.float32)
    for ch_i, w_b in ((0, lum_weight), (1, chroma_weight), (2, chroma_weight)):
        sm, ss = float(s_lab[..., ch_i].mean()), max(5.0, float(s_lab[..., ch_i].std()))
        rm, rs = float(r_lab[..., ch_i].mean()), max(5.0, float(r_lab[..., ch_i].std()))
        nm = sm * (1.0 - w_b) + rm * w_b
        ns = ss * (1.0 - 0.60 * w_b) + rs * (0.60 * w_b)
        s_lab[..., ch_i] = np.clip((s_lab[..., ch_i] - sm) * (ns / ss) + nm, 0, 255)
    out_u8 = cv2.cvtColor(s_lab.astype(np.uint8), cv2.COLOR_LAB2RGB)
    if bilateral:
        out_u8 = cv2.bilateralFilter(out_u8, d=5, sigmaColor=24, sigmaSpace=24)
    return out_u8.astype(np.float32)


def _compute_panoptic_sky_water_aperture(
    seg_np: Optional[np.ndarray],
    H: int,
    W: int,
    hor_frac: float,
    shot_kind: str,
) -> np.ndarray:
    """
    Computes a soft 2D Through-the-Frame Aperture Mask `(H, W, 1)` in `[0, 1]`
    indicating where the CLIP Reference (`refs/XX-YY.jpg`) and Atlantis Cel Sky/Water
    should bleed *through* the 3D Foundry terrain (`sb/w1623/XX-YY.jpg` / `inv/w1623/XX-YY-b.jpg`).
    """
    yy = np.linspace(0.0, 1.0, H, dtype=np.float32)[:, None]
    xx = np.linspace(0.0, 1.0, W, dtype=np.float32)[None, :]
    hor = max(0.20, min(0.72, float(hor_frac or 0.38)))

    # Base horizon sky band (`y < hor`)
    sky_band = np.clip((hor + 0.12 - yy) / max(0.14, hor + 0.08), 0.0, 1.0) ** 1.25

    if seg_np is not None:
        r, g, b = seg_np[..., 0], seg_np[..., 1], seg_np[..., 2]
        # Panoptic segmentation colors: sky/water have strong blue/cyan or high brightness
        cyan_blue = np.clip((b - 0.55 * r) / 135.0, 0.0, 1.0)
        bright_open = np.clip((0.299 * r + 0.587 * g + 0.114 * b - 95.0) / 120.0, 0.0, 1.0)
        seg_mask = np.clip(0.55 * sky_band + 0.45 * np.maximum(cyan_blue, bright_open * 0.75), 0.0, 1.0)
    else:
        seg_mask = sky_band

    # Modulate aperture depth by shot kind
    if shot_kind in ("sky", "aerial"):
        seg_mask = np.clip(seg_mask * 0.85 + 0.18, 0.15, 0.82)
    elif shot_kind in ("close", "pov"):
        # In close/pov shots, open a central/window atmospheric aperture as well
        win_cx = 0.52
        win_cy = max(0.32, hor * 0.92)
        win_ap = np.exp(-(((xx - win_cx) / 0.34) ** 2 + ((yy - win_cy) / 0.28) ** 2))
        seg_mask = np.clip(np.maximum(seg_mask * 0.78, win_ap * 0.68), 0.10, 0.78)
    else:
        seg_mask = np.clip(seg_mask * 0.75 + 0.08, 0.08, 0.72)

    smooth_mask = cv2.GaussianBlur(seg_mask.astype(np.float32), (65, 65), 21.0)
    return smooth_mask[..., None]


def _synthesize_poem_14_shots(lv14: Dict[str, Any]) -> List[Dict[str, Any]]:
    """
    Builds 8 canonical shot entries (`14-00` .. `14-07`) for Poem 14 ("Hot Minute")
    from its 7 scenes & spoken lines in `shots/play/levels/14/level.json`, paired with
    nocturnal/dawn harbor & tower camera stands from `w1623` so Poem 14 has full parity
    with Poems 01-13!
    """
    scenes = lv14.get("scenes", [])
    sb_cycle = [
        "sb/w1623/01-00.jpg",
        "sb/w1623/01-02.jpg",
        "sb/w1623/04-01.jpg",
        "sb/w1623/06-02.jpg",
        "sb/w1623/08-01.jpg",
        "sb/w1623/11-02.jpg",
        "sb/w1623/13-04.jpg",
        "sb/w1623/01-09.jpg",
    ]
    ref_cycle = ["01-00", "01-04", "04-02", "06-03", "08-02", "11-03", "13-05", "01-07"]
    kinds = ["establishing", "medium", "close", "tracking", "establishing", "medium", "close", "sky"]
    mms = [29, 49, 52, 35, 29, 49, 52, 32]
    hors = [0.38, 0.44, 0.48, 0.40, 0.36, 0.45, 0.50, 0.62]

    out_shots: List[Dict[str, Any]] = []
    for k in range(8):
        sc = scenes[min(len(scenes) - 1, int(k * len(scenes) / 8))]
        lines = sc.get("lines", [])
        ln_obj = lines[k % len(lines)] if lines else {"t0": k * 12.0, "t1": (k + 1) * 12.0, "text": sc.get("name", "Hot Minute")}
        out_shots.append({
            "k": k,
            "t0": float(ln_obj.get("t0", k * 12.0)),
            "t1": float(ln_obj.get("t1", (k + 1) * 12.0)),
            "line": str(ln_obj.get("text", sc.get("name", ""))),
            "kind": kinds[k],
            "fov": int(round(2.0 * math.degrees(math.atan(18.0 / mms[k])))),
            "mm": mms[k],
            "light": "dusk→night" if k < 6 else "first light",
            "subject": "the two of them" if k in (1, 2, 5, 6) else "POET",
            "names": ["tower", "city", "water"],
            "cam": {
                "x": 1850.0 + k * 42.0,
                "y": 2280.0 - k * 35.0,
                "z": 68.0 if k != 7 else 145.0,
                "hd": float((k * 45) % 360),
                "fov": 50.0,
                "hor": hors[k],
            },
            "travel": k in (3, 5),
            "frac": round((k + 0.5) / 8.0, 3),
            "id": f"w1623-14-{k:02d}",
            "world": "w1623",
            "poem": "14",
            "img": sb_cycle[k],
            "ref_override": ref_cycle[k],
            "tags": [
                {"what": "city", "pct": 38, "x": 0.44, "near": 165},
                {"what": "sky", "pct": 34, "x": 0.50, "near": None},
                {"what": "water", "pct": 14, "x": 0.68, "near": 380},
                {"what": "tower", "pct": 8.5, "x": 0.28, "near": 110, "poem": "14"},
            ],
        })
    return out_shots


def _render_bottom_spectrogram_strip(
    W: int,
    H_BAR: int,
    song_info: Optional[Dict[str, Any]],
    frac0: float,
    frac1: float,
    d_color_rgb: Tuple[float, float, float],
    d_glow_rgb: Tuple[float, float, float],
    sky_rgb: Tuple[float, float, float],
) -> np.ndarray:
    """
    Renders a seamless `W x H_BAR` visual spectrogram & colour-script ribbon (`uint8` RGB)
    with 8x8 Bayer dot-matrix modulation and District/Sky-Hour harmonic tinting.
    """
    bar = np.zeros((H_BAR, W, 3), dtype=np.float32)
    yy = np.linspace(0.0, 1.0, H_BAR, dtype=np.float32)[:, None, None]
    d_col = np.array(d_color_rgb, dtype=np.float32)[None, None, :]
    g_col = np.array(d_glow_rgb, dtype=np.float32)[None, None, :]
    s_col = np.array(sky_rgb, dtype=np.float32)[None, None, :]

    base_grad = (0.18 * s_col + 0.22 * d_col) * (1.0 - yy * 0.5)
    bar[:] = base_grad

    if song_info is not None:
        spec_arr = song_info["spec_arr"]  # (48, 192)
        w_sp = spec_arr.shape[1]
        c0 = max(0, min(w_sp - 4, int(round(frac0 * (w_sp - 1)))))
        c1 = max(c0 + 4, min(w_sp, int(round(frac1 * (w_sp - 1)))))
        spec_slice = spec_arr[:, c0:c1]
        spec_2d = cv2.resize(spec_slice, (W, H_BAR), interpolation=cv2.INTER_CUBIC)
        bayer_tile = np.array(b90._BAYER_8X8_NORM, dtype=np.float32)
        yi, xi = np.mgrid[0:H_BAR, 0:W]
        bmap = bayer_tile[(yi // 2) % 8, (xi // 2) % 8]
        dots = np.clip((spec_2d - bmap * 0.48) * 2.4, 0.0, 1.0)
        energy = (0.55 * spec_2d + 0.45 * dots)[..., None]
        bar = bar * (1.0 - 0.78 * energy) + (0.62 * g_col + 0.38 * d_col) * (0.85 * energy)

    # Top 1px warm separator line
    bar[0, :, :] = 0.45 * bar[0, :, :] + 0.55 * g_col[0, 0, :]
    return np.clip(bar, 0, 255).astype(np.uint8)


def paint_single_shot_plate(
    shot: Dict[str, Any],
    poem_num: int,
    lv: Dict[str, Any],
    refs_for_poem: List[Dict[str, Any]],
    inv_by_ref: Dict[str, Dict[str, Any]],
    plans_for_poem: List[Dict[str, Any]],
    parts_by_id: Dict[str, Dict[str, Any]],
    wag: Dict[str, Any],
    W: int = 1280,
    H_MAIN: int = 540,
    H_SPEC: int = 20,
) -> Tuple[Image.Image, Dict[str, Any]]:
    """
    Paints and shapes a single shot (`1280x560` pure borderless cinema plate) across all 7 depth planes (`P6..P0`):
      - Builds ON TOP OF & THROUGH the Foundry 3D terrain (`sb/w1623/XX-YY.jpg` or `inv/w1623/XX-YY-b.jpg`),
      - Bleeds the CLIP Reference (`refs/XX-YY.jpg`) & Atlantis Cel Painting (`world/<wk>/cel.webp`) through
        the Panoptic Segmentation mask (`refs/XX-YY-seg.jpg`) and camera horizon `cam.hor`,
      - Places distance-calibrated (`mm`, `kind`, `tags.near`) multiplane architecture (`P4`),
        layered door/window video portals (`aperture_footage`), grounded set props (`P3`),
        and full-body assembled cast (`P2`) with cel-ramp pigment integration, ground shadows,
        and ankle mist ("hiding the crimes").
    """
    num_str = f"{poem_num:02d}"
    scenes = lv.get("scenes", [])
    n_sc = max(1, len(scenes))
    frac = float(shot.get("frac", 0.5))
    sc_idx = min(n_sc - 1, max(0, int(frac * n_sc)))
    sc = scenes[sc_idx]
    skey = sc["key"]
    spec = b90.CUSTOM_SCENES.get(skey, list(b90.CUSTOM_SCENES.values())[0])

    # 1. Load Atlantis Cel Backdrop (`backdrop.webp` + `cel.webp` + `ink.webp`)
    backdrop_rel = spec["backdrop"]
    wk = backdrop_rel.split("/")[1]
    cel_rel = f"world/{wk}/cel.webp"
    ink_rel = f"world/{wk}/ink.webp"
    bg_cel_rgba, cel_ref_rgb = b90._load_blended_cel_backdrop(
        SHOTS_DIR / backdrop_rel,
        SHOTS_DIR / cel_rel,
        W,
        H_MAIN,
    )
    cel_np = np.array(bg_cel_rgba.convert("RGB"), dtype=np.float32)
    cel_small = cel_ref_rgb.resize((160, 90), Image.Resampling.BILINEAR)

    # 2. Load Foundry 3D Storyboard (`sb/w1623/XX-YY.jpg`) & Inverse Sculpt (`inv/w1623/XX-YY-b.jpg` if available)
    sb_rel = shot.get("img", "")
    sb_path = FOUNDRY_DIR / sb_rel
    foundry_np = cel_np.copy()
    if sb_path.exists():
        try:
            foundry_np = np.array(
                Image.open(sb_path).convert("RGB").resize((W, H_MAIN), Image.Resampling.LANCZOS),
                dtype=np.float32,
            )
        except Exception:
            pass

    # Match closest CLIP Reference & Panoptic Segmentation for this shot
    ref_obj: Optional[Dict[str, Any]] = None
    if shot.get("ref_override"):
        ref_id = shot["ref_override"]
        for r in wag.get("all_refs_list", []):
            if r["id"] == ref_id:
                ref_obj = r
                break
    elif refs_for_poem:
        r_idx = min(len(refs_for_poem) - 1, max(0, int(round(frac * (len(refs_for_poem) - 1)))))
        ref_obj = refs_for_poem[r_idx]

    ref_np = cel_np.copy()
    seg_np: Optional[np.ndarray] = None
    used_inverse_sculpt = False
    ref_id_str = ref_obj["id"] if ref_obj else f"{num_str}-00"
    if ref_obj is not None:
        r_path = FOUNDRY_DIR / ref_obj["img"]
        s_path = FOUNDRY_DIR / ref_obj["seg"]
        if r_path.exists():
            try:
                ref_np = np.array(
                    Image.open(r_path).convert("RGB").resize((W, H_MAIN), Image.Resampling.LANCZOS),
                    dtype=np.float32,
                )
            except Exception:
                pass
        if s_path.exists():
            try:
                seg_np = np.array(
                    Image.open(s_path).convert("RGB").resize((W, H_MAIN), Image.Resampling.BILINEAR),
                    dtype=np.float32,
                )
            except Exception:
                pass
        # If this reference has an Inverse-Sculpted 3D world render (`inv/w1623/<ref>-b.jpg`), blend it into `foundry_np`!
        if ref_id_str in inv_by_ref:
            inv_b_path = FOUNDRY_DIR / inv_by_ref[ref_id_str]["b"]
            if inv_b_path.exists():
                try:
                    inv_b_np = np.array(
                        Image.open(inv_b_path).convert("RGB").resize((W, H_MAIN), Image.Resampling.LANCZOS),
                        dtype=np.float32,
                    )
                    foundry_np = 0.55 * inv_b_np + 0.45 * foundry_np
                    used_inverse_sculpt = True
                except Exception:
                    pass

    # 3. District Colour-Script & Shot Light-Hour Palette
    d_map = wag["districts_by_id"]
    sc_map = wag["scenes_by_key"]
    scr_map = wag["script_by_num"]
    song_map = wag["songs_by_num"]

    sc_meta = sc_map.get(skey, {})
    d_id = str(sc_meta.get("d", sc.get("district_meta", {}).get("id", "haze")))
    d_obj = d_map.get(d_id, d_map.get("haze", {}))
    body_rgb = (d_obj.get("body_rgb") or [(18.0, 20.0, 28.0)])[0]
    glow_rgb = (d_obj.get("glow_rgb") or [(245.0, 145.0, 35.0)])[0]
    d_col_rgb = d_obj.get("color_rgb", (245.0, 145.0, 35.0))

    scr_entry = scr_map.get(num_str, {"hour": [19.2, 20.4]})
    h_pair = scr_entry.get("hour", [19.2, 20.4])
    h_now = float(h_pair[0]) + (float(h_pair[1]) - float(h_pair[0])) * frac
    sky_rgb = b90._sky_hour_rgb(h_now)
    light_str = str(shot.get("light", "dusk→night"))
    light_rgb = LIGHT_TINTS.get(light_str, sky_rgb)

    # 4. Fuse Foundry 3D Terrain (`foundry_np`), CLIP Reference (`ref_np`), and Atlantis Cel (`cel_np`)
    #    using the Panoptic Aperture Mask (`ap_mask`) and Camera Horizon (`cam.hor`)!
    cam = shot.get("cam") or {}
    hor_frac = float(cam.get("hor") if cam.get("hor") is not None else 0.40)
    shot_kind = str(shot.get("kind", "medium"))
    ap_mask = _compute_panoptic_sky_water_aperture(seg_np, H_MAIN, W, hor_frac, shot_kind)

    # Harmonize `foundry_np` and `ref_np` toward the Cel Painting + District/Light palette so all 3 share 100% unified brushwork
    foundry_harm = _harmonize_image_to_palette(foundry_np, cel_np, lum_weight=0.42, chroma_weight=0.76, bilateral=True)
    ref_harm = _harmonize_image_to_palette(ref_np, cel_np, lum_weight=0.38, chroma_weight=0.72, bilateral=True)

    # Weight between Foundry 3D structure, Panoptic Reference, and Atlantis Cel Painting based on shot kind
    yy = np.linspace(0.0, 1.0, H_MAIN, dtype=np.float32)[:, None, None]
    if shot_kind in ("establishing", "tracking", "aerial", "sky"):
        # Wide/Aerial/Sky: strong 3D Foundry topography & Panoptic sky/water aperture woven into Cel painting
        through_plate = foundry_harm * (1.0 - ap_mask) + ref_harm * ap_mask
        w_cel = 0.48 + 0.18 * np.clip((yy - hor_frac) / 0.55, 0.0, 1.0)
        base_f = cel_np * w_cel + through_plate * (1.0 - w_cel)
    else:
        # Close/Medium/POV: rich Atlantis Cel interior/stage with Foundry 3D & Panoptic reference bleeding through windows/horizon
        through_plate = 0.54 * foundry_harm + 0.46 * ref_harm
        w_through = ap_mask * 0.58
        base_f = cel_np * (1.0 - w_through) + through_plate * w_through

    # Infuse subtle shot `light` hour & District atmospheric strata
    w_sky_tint = (np.clip(1.0 - yy / max(0.25, hor_frac + 0.12), 0.0, 1.0) ** 1.4) * 0.16
    light_arr = (0.60 * np.array(light_rgb, dtype=np.float32) + 0.40 * np.array(sky_rgb, dtype=np.float32))[None, None, :]
    base_f = base_f * (1.0 - w_sky_tint) + light_arr * w_sky_tint

    # Subtle floor grounding gradient below `floor_y`
    floor_y = int(round(max(0.64, min(0.88, hor_frac + 0.36)) * H_MAIN))
    w_floor_dark = np.clip((yy[:, :, 0] - (floor_y / float(H_MAIN))) / 0.25, 0.0, 1.0)[..., None] * 0.24
    body_arr = np.array(body_rgb, dtype=np.float32)[None, None, :]
    base_f = base_f * (1.0 - w_floor_dark) + body_arr * w_floor_dark

    canvas_rgb = Image.fromarray(np.clip(base_f, 0, 255).astype(np.uint8), mode="RGB")
    canvas = canvas_rgb.convert("RGBA")

    # 5. Camera-Distance Scale Multiplier from Shot `mm` (`29mm` wide .. `52mm` close) & `kind`
    focal_mm = float(shot.get("mm", 35))
    kind_mult = {
        "close": 1.24,
        "pov": 1.12,
        "medium": 1.00,
        "tracking": 0.88,
        "establishing": 0.76,
        "sky": 0.62,
        "aerial": 0.58,
    }.get(shot_kind, 1.00)
    lens_mult = ((focal_mm / 38.0) ** 0.45) * kind_mult
    lens_mult = max(0.52, min(1.38, lens_mult))

    haze_tuple = (
        int(round(0.55 * body_rgb[0] + 0.45 * sky_rgb[0])),
        int(round(0.55 * body_rgb[1] + 0.45 * sky_rgb[1])),
        int(round(0.55 * body_rgb[2] + 0.45 * sky_rgb[2])),
    )

    # 6. Paint Multiplane Architecture, Layered Video Portals (`P4`) & Grounded Set Furnishings (`P3`)
    #    Use the scene's `multiplane_layers` (in-frame + selected portal extensions) anchored to shot `tags`!
    sc_layers = [
        l for l in sc.get("multiplane_layers", [])
        if not l.get("is_world_sheet")
    ]
    in_frame_lyrs = [l for l in sc_layers if not l.get("is_set_extension") and float(l.get("x", 0.5)) <= 0.95]
    ext_portal_lyrs = [
        l for l in sc_layers
        if l.get("is_set_extension") and l.get("aperture_footage") and str(l.get("lego_role", "")) not in ("wall_with_door_hole", "wall_bay")
    ]

    # Pick up to 4 architectural/set pieces + 1 portal frame, shifted gently by shot index `k` and shot `tags`
    shot_k = int(shot.get("k", 0))
    tags = shot.get("tags") or []
    arch_tags = [t for t in tags if t.get("what") in ("tower", "city", "street", "church", "townhouse", "gates", "bridge", "pier", "arcade", "plaza")]
    tag_anchor_x = float(arch_tags[0]["x"]) if arch_tags and arch_tags[0].get("x") is not None else (0.24 if shot_k % 2 == 0 else 0.76)
    tag_anchor_x = max(0.16, min(0.84, tag_anchor_x))

    active_lyrs: List[Dict[str, Any]] = []
    for idx_l, lyr in enumerate(in_frame_lyrs[:4]):
        l_copy = dict(lyr)
        # Shift x slightly across shots in the same scene so each shot has its own distinct camera framing
        base_x = float(l_copy.get("x", 0.5))
        pan_shift = ((shot_k % 3) - 1) * 0.06
        l_copy["x"] = max(0.14, min(0.86, base_x + pan_shift))
        l_copy["y"] = max(0.80, float(l_copy.get("y", 0.86)))
        l_copy["scale"] = float(l_copy.get("scale", 0.24)) * lens_mult
        active_lyrs.append(l_copy)

    if ext_portal_lyrs and not any(l.get("aperture_footage") for l in active_lyrs):
        p_copy = dict(ext_portal_lyrs[shot_k % len(ext_portal_lyrs)])
        p_copy["is_set_extension"] = False
        p_copy["x"] = tag_anchor_x
        p_copy["y"] = max(0.78, min(0.92, float(p_copy.get("y", 0.86))))
        p_copy["scale"] = max(0.24, min(0.48, float(p_copy.get("scale", 0.34)) * 0.72 * lens_mult))
        active_lyrs.append(p_copy)

    active_lyrs.sort(key=lambda item: float(item.get("z", 1.4)), reverse=True)
    portals_painted = 0

    for lyr in active_lyrs:
        pid = lyr.get("part_id", "")
        pt = parts_by_id.get(pid)
        rel_f = pt["file"] if pt else lyr.get("file", "").replace("../", "")
        p_path = SHOTS_DIR / rel_f
        if not p_path.exists():
            continue
        try:
            p_img = Image.open(p_path).convert("RGBA")
        except Exception:
            continue
        pw, ph = p_img.size
        if pw <= 2 or ph <= 2:
            continue
        sc_val = float(lyr.get("scale", 0.24))
        plane_id = str(lyr.get("plane", "P3"))
        target_w, target_h = b90.compute_piece_stage_dims(
            pw, ph, sc_val, plane_id, W, H_MAIN, is_set_extension=False, lego_role=str(lyr.get("lego_role", ""))
        )
        p_resized = p_img.resize((target_w, target_h), Image.Resampling.LANCZOS)
        if lyr.get("flip"):
            p_resized = p_resized.transpose(Image.Transpose.FLIP_LEFT_RIGHT)

        cx = int(round(float(lyr.get("x", 0.5)) * W))
        by = int(round(float(lyr.get("y", 0.88)) * H_MAIN))
        dx = cx - target_w // 2
        dy = by - target_h

        pad = 64
        cx0 = max(0, min(W - 32, dx - pad))
        cy0 = max(0, min(H_MAIN - 32, dy - pad))
        cx1 = max(cx0 + 32, min(W, dx + target_w + pad))
        cy1 = max(cy0 + 32, min(H_MAIN, dy + target_h + pad))
        bg_crop = canvas_rgb.crop((cx0, cy0, cx1, cy1))

        p_cel = b90.clean_and_integrate_cutout(
            p_resized,
            bg_crop,
            plane_id,
            haze_rgb=haze_tuple,
            cel_scene_img=cel_small,
        )
        p_cel = b90._apply_canvas_boundary_feather(p_cel, dx, W)

        # Ground contact shadow
        if float(lyr.get("y", 0.88)) >= 0.56 and plane_id in ("P4", "P3", "P2"):
            sh_layer = Image.new("RGBA", (W, H_MAIN), (0, 0, 0, 0))
            sdraw = ImageDraw.Draw(sh_layer)
            rx = int(target_w * 0.40)
            ry = max(4, int(target_h * 0.07))
            sdraw.ellipse([cx - rx, by - ry, cx + rx, by + ry], fill=(6, 8, 12, 92))
            sh_layer = sh_layer.filter(ImageFilter.GaussianBlur(radius=5))
            canvas = Image.alpha_composite(canvas, sh_layer)

        # Layered Door/Window Video Portal (`aperture_footage`)
        af = lyr.get("aperture_footage")
        portal_patch: Optional[Image.Image] = None
        ap_x0, ap_y0, ap_x1, ap_y1 = 0, 0, 0, 0
        if isinstance(af, dict) and af.get("footage_file"):
            abox = af.get("aperture_box") or [0.24, 0.16, 0.78, 0.95]
            ap_x0 = max(4, dx + int(round(target_w * float(abox[0]))))
            ap_y0 = max(8, dy + int(round(target_h * float(abox[1]))))
            ap_x1 = min(W - 4, dx + int(round(target_w * float(abox[2]))))
            ap_y1 = min(H_MAIN - 4, dy + int(round(target_h * float(abox[3]))))
            ap_w = ap_x1 - ap_x0
            ap_h = ap_y1 - ap_y0
            if ap_w >= 18 and ap_h >= 18:
                portal_patch = b90._build_harmonized_portal_patch(af, ap_w, ap_h, bg_crop, haze_tuple)
                if portal_patch is not None:
                    portals_painted += 1
                    p_baked = b90._apply_canvas_boundary_feather(portal_patch, ap_x0, W)
                    canvas.alpha_composite(p_baked, dest=(ap_x0, ap_y0))

        canvas.alpha_composite(p_cel, dest=(dx, dy))

        if portal_patch is not None and ap_x1 > ap_x0 + 18 and ap_y1 > ap_y0 + 18:
            iw = max(12, int((ap_x1 - ap_x0) * 0.84))
            ih = max(12, int((ap_y1 - ap_y0) * 0.84))
            ix = ap_x0 + ((ap_x1 - ap_x0) - iw) // 2
            iy = ap_y0 + ((ap_y1 - ap_y0) - ih) // 2
            ipatch = portal_patch.resize((iw, ih), Image.Resampling.LANCZOS)
            ir, ig, ib, ia = ipatch.split()
            ia = ia.point(lambda a: int(a * 0.82))
            ipatch = b90._apply_canvas_boundary_feather(Image.merge("RGBA", (ir, ig, ib, ia)), ix, W)
            canvas.alpha_composite(ipatch, dest=(ix, iy))

    # 7. Paint Solved Full-Body Cast (`P2`) Calibrated to Shot Distance & Focal Length (`mm` / `kind`)
    #    Strictly uses full-body figures from `scene_collage_plans.json` or `FULL_BODY_ACTOR_FILES`!
    subject = str(shot.get("subject", "POET"))
    cast_painted = 0
    if shot_kind not in ("sky",) and (subject in ("POET", "EX", "the two of them") or shot_kind in ("close", "medium", "pov", "tracking")):
        actor_candidates: List[str] = []
        if plans_for_poem:
            pl_sc = plans_for_poem[sc_idx % len(plans_for_poem)]
            for l_pl in pl_sc.get("staged_placements", pl_sc.get("layers", [])):
                if l_pl.get("semantic_class") in ("full_figure_adult", "full_figure_child") and l_pl.get("file"):
                    actor_candidates.append(str(l_pl["file"]))
        # Always include our clean full-body cast library
        actor_candidates.extend(FULL_BODY_ACTOR_FILES)

        n_actors = 2 if subject == "the two of them" else 1
        actor_base_h_ratio = {
            "close": 0.48,
            "pov": 0.40,
            "medium": 0.35,
            "tracking": 0.28,
            "establishing": 0.21,
            "aerial": 0.14,
        }.get(shot_kind, 0.32)

        for a_i in range(n_actors):
            af_rel = actor_candidates[(shot_k + a_i) % len(actor_candidates)]
            af_path = SHOTS_DIR / af_rel
            if not af_path.exists():
                af_path = SHOTS_DIR / FULL_BODY_ACTOR_FILES[(shot_k + a_i) % len(FULL_BODY_ACTOR_FILES)]
            if not af_path.exists():
                continue
            try:
                a_im = Image.open(af_path).convert("RGBA")
                # Trim transparent margins
                bbox = a_im.getbbox()
                if bbox:
                    a_im = a_im.crop(bbox)
                aw, ah = a_im.size
                if aw <= 4 or ah <= 4:
                    continue
                t_ah = max(48, min(int(H_MAIN * 0.62), int(round(H_MAIN * actor_base_h_ratio * (0.92 if a_i == 1 else 1.0)))))
                t_aw = max(24, int(round(aw * (t_ah / float(ah)))))
                if t_aw > int(W * 0.34):
                    t_aw = int(W * 0.34)
                    t_ah = max(42, int(round(ah * (t_aw / float(aw)))))
                a_resized = a_im.resize((t_aw, t_ah), Image.Resampling.LANCZOS)
                if (shot_k + a_i) % 2 == 1:
                    a_resized = a_resized.transpose(Image.Transpose.FLIP_LEFT_RIGHT)

                ax_frac = 0.44 if n_actors == 1 else (0.38 if a_i == 0 else 0.58)
                ax_frac += ((shot_k % 3) - 1) * 0.05
                acx = int(round(ax_frac * W))
                aby = min(H_MAIN - 14, max(int(H_MAIN * 0.76), floor_y + int(H_MAIN * 0.10)))
                adx = acx - t_aw // 2
                ady = aby - t_ah

                bg_c = canvas.convert("RGB").crop((
                    max(0, adx - 40),
                    max(0, ady - 40),
                    min(W, adx + t_aw + 40),
                    min(H_MAIN, ady + t_ah + 40),
                ))
                a_cel = b90.clean_and_integrate_cutout(
                    a_resized,
                    bg_c,
                    "P2",
                    haze_rgb=haze_tuple,
                    cel_scene_img=cel_small,
                )
                # Soft ground contact shadow + ankle mist wrap ("hide the crimes")
                sh_l = Image.new("RGBA", (W, H_MAIN), (0, 0, 0, 0))
                sd = ImageDraw.Draw(sh_l)
                sd.ellipse([acx - int(t_aw * 0.38), aby - 6, acx + int(t_aw * 0.38), aby + 7], fill=(6, 8, 14, 108))
                sh_l = sh_l.filter(ImageFilter.GaussianBlur(radius=5))
                canvas = Image.alpha_composite(canvas, sh_l)
                canvas.alpha_composite(b90._apply_canvas_boundary_feather(a_cel, adx, W), dest=(adx, ady))
                cast_painted += 1
            except Exception:
                pass

    # 8. Whole-Canvas Gouache Brushstroke Unification, Paper Tooth & Warm Charcoal Ink Pass (`world/<wk>/ink.webp`)
    rgb_arr = np.array(canvas.convert("RGB"), dtype=np.uint8)
    gouache_arr = cv2.bilateralFilter(rgb_arr, d=5, sigmaColor=20, sigmaSpace=20)
    blended_f = 0.84 * rgb_arr.astype(np.float32) + 0.16 * gouache_arr.astype(np.float32)
    yy_c, xx_c = np.mgrid[0:H_MAIN, 0:W].astype(np.float32)
    tooth = 1.4 * np.sin(xx_c * 0.65 + yy_c * 0.45) * np.cos(xx_c * 0.35 - yy_c * 0.55)
    blended_f = np.clip(blended_f + tooth[..., None], 0, 255)
    canvas = Image.fromarray(blended_f.astype(np.uint8), mode="RGB").convert("RGBA")

    ink_path = SHOTS_DIR / ink_rel
    if ink_path.exists():
        try:
            ink_im = Image.open(ink_path).convert("RGBA").resize((W, H_MAIN), Image.Resampling.LANCZOS)
            _, _, _, a_ch = ink_im.split()
            a_np = np.array(a_ch, dtype=np.float32) * 0.24
            ramp_l = np.clip(np.arange(W, dtype=np.float32) / 96.0, 0.0, 1.0)[None, :]
            ramp_r = np.clip((float(W) - np.arange(W, dtype=np.float32)) / 96.0, 0.0, 1.0)[None, :]
            a_np = (a_np * ramp_l * ramp_r).astype(np.uint8)
            ink_rgba = Image.merge("RGBA", (
                Image.new("L", (W, H_MAIN), 16),
                Image.new("L", (W, H_MAIN), 13),
                Image.new("L", (W, H_MAIN), 20),
                Image.fromarray(a_np, mode="L"),
            ))
            canvas.alpha_composite(ink_rgba, dest=(0, 0))
        except Exception:
            pass

    # 9. Attach the 20px Visual Spectrogram & District Colour-Script Tape Edge at the bottom (`y = 540..560`)
    song_info = song_map.get(num_str)
    frac0 = max(0.0, min(0.95, frac - 0.04))
    frac1 = max(frac0 + 0.04, min(1.0, frac + 0.04))
    spec_bar_np = _render_bottom_spectrogram_strip(
        W, H_SPEC, song_info, frac0, frac1, d_col_rgb, glow_rgb, sky_rgb
    )
    main_np = np.array(canvas.convert("RGB"), dtype=np.uint8)
    full_shot_np = np.concatenate([main_np, spec_bar_np], axis=0)  # (560, 1280, 3)
    full_shot_im = Image.fromarray(full_shot_np, mode="RGB")

    meta = {
        "shot_id": shot.get("id", f"w1623-{num_str}-{shot_k:02d}"),
        "poem": num_str,
        "k": shot_k,
        "t0": shot.get("t0", 0.0),
        "t1": shot.get("t1", 0.0),
        "kind": shot_kind,
        "mm": int(focal_mm),
        "light": light_str,
        "subject": subject,
        "line": shot.get("line", ""),
        "scene_key": skey,
        "district_id": d_id,
        "ref_id": ref_id_str,
        "used_inverse_sculpt": used_inverse_sculpt,
        "portals_painted": portals_painted,
        "cast_painted": cast_painted,
    }
    return full_shot_im, meta


def stitch_poem_shot_tape(
    poem_num: int,
    lv: Dict[str, Any],
    shot_images: List[Image.Image],
    shot_metas: List[Dict[str, Any]],
    parts_by_id: Dict[str, Dict[str, Any]],
    wag: Dict[str, Any],
) -> Tuple[Image.Image, Image.Image]:
    """
    Weaves all `10-16` painted shots of Poem `poem_num` into:
      1. A continuous, seamless horizontal Shot-by-Shot Master Tape (`poem_<num>_shot_tape.png`),
         where adjacent shots overlap across a `160px` multi-band 2D raised-cosine + spectrogram
         mist cross-weave AND have a cel-integrated architectural threshold piece straddling the join!
      2. A high-clarity annotated Shot-by-Shot Storyboard Contact Sheet (`poem_<num>_shots_sheet.png`).
    """
    num_str = f"{poem_num:02d}"
    n_shots = len(shot_images)
    # Each shot on the master horizontal tape is scaled to `768 x 336` with a `144px` overlap (`step = 624px`)
    W_S, H_S = 768, 336
    OV = 144
    STEP = W_S - OV
    total_w = W_S if n_shots == 1 else (W_S + (n_shots - 1) * STEP)

    tape_f = np.zeros((H_S, total_w, 3), dtype=np.float32)
    weight_f = np.zeros((H_S, total_w, 1), dtype=np.float32)

    # Raised-cosine horizontal window for each shot module so overlaps blend 100% smoothly
    x_local = np.arange(W_S, dtype=np.float32)[None, :, None]
    w_left_ramp = 0.5 - 0.5 * np.cos(np.pi * np.clip(x_local / float(OV), 0.0, 1.0))
    w_right_ramp = 0.5 - 0.5 * np.cos(np.pi * np.clip((float(W_S - 1) - x_local) / float(OV), 0.0, 1.0))

    for idx, im in enumerate(shot_images):
        s_np = np.array(im.resize((W_S, H_S), Image.Resampling.LANCZOS), dtype=np.float32)
        w_win = np.ones((1, W_S, 1), dtype=np.float32)
        if idx > 0:
            w_win *= w_left_ramp
        if idx < n_shots - 1:
            w_win *= w_right_ramp
        w_win = np.maximum(1e-4, w_win)
        x0 = idx * STEP
        tape_f[:, x0 : x0 + W_S, :] += s_np * w_win
        weight_f[:, x0 : x0 + W_S, :] += w_win

    tape_f /= np.maximum(1e-4, weight_f)

    # Infuse each `144px` overlap zone (`x0 = idx * STEP .. idx * STEP + OV`) with a subtle multi-scale
    # gouache cross-weave + District glow mist so any horizon step between shots melts into atmospheric depth!
    d_map = wag["districts_by_id"]
    for idx in range(1, n_shots):
        jx0 = idx * STEP
        jx1 = min(total_w, jx0 + OV)
        band = tape_f[:, jx0:jx1, :]
        band_blur = cv2.GaussianBlur(band, (45, 15), 11.0)
        d_id = shot_metas[idx].get("district_id", "haze")
        d_obj = d_map.get(d_id, d_map.get("haze", {}))
        glow_rgb = np.array((d_obj.get("glow_rgb") or [(245.0, 145.0, 35.0)])[0], dtype=np.float32)[None, None, :]
        t_ov = np.linspace(0.0, 1.0, jx1 - jx0, dtype=np.float32)[None, :, None]
        bell = np.maximum(0.0, np.sin(np.pi * t_ov)) ** 1.35
        tape_f[:, jx0:jx1, :] = (
            band * (1.0 - 0.54 * bell)
            + band_blur * (0.46 * bell)
            + glow_rgb * (0.08 * bell)
        )

    tape_im = Image.fromarray(np.clip(tape_f, 0, 255).astype(np.uint8), mode="RGB").convert("RGBA")

    # Also composite straddling architectural threshold pieces (`portal_door_arch`, `building_pier`, `arch`)
    # right across every shot-to-shot join (`jx_center = idx * STEP + OV // 2`) to "hide the crimes"!
    scenes = lv.get("scenes", [])
    ext_arch_candidates: List[Dict[str, Any]] = []
    for sc in scenes:
        for lyr in sc.get("multiplane_layers", []):
            if not lyr.get("is_world_sheet") and str(lyr.get("lego_role", "")) in (
                "portal_door_arch",
                "portal_window",
                "building_pier",
            ):
                ext_arch_candidates.append(lyr)

    if ext_arch_candidates:
        tape_rgb_ref = tape_im.convert("RGB")
        tape_small_ref = tape_rgb_ref.resize((180, 80), Image.Resampling.BILINEAR)
        for idx in range(1, n_shots):
            lyr = ext_arch_candidates[idx % len(ext_arch_candidates)]
            pid = lyr.get("part_id", "")
            pt = parts_by_id.get(pid)
            if not pt:
                continue
            p_path = SHOTS_DIR / pt["file"]
            if not p_path.exists():
                continue
            try:
                p_img = Image.open(p_path).convert("RGBA")
                pw, ph = p_img.size
                th = int(round(H_S * 0.56))
                tw = max(36, min(int(OV * 1.35), int(round(pw * (th / float(max(1, ph)))))))
                p_res = p_img.resize((tw, th), Image.Resampling.LANCZOS)
                jcx = idx * STEP + OV // 2
                jdx = jcx - tw // 2
                jdy = int(H_S * 0.92) - th
                bg_c = tape_rgb_ref.crop((
                    max(0, jdx - 24),
                    max(0, jdy - 24),
                    min(total_w, jdx + tw + 24),
                    min(H_S, jdy + th + 24),
                ))
                p_cel = b90.clean_and_integrate_cutout(
                    p_res, bg_c, "P4", haze_rgb=(24, 30, 44), cel_scene_img=tape_small_ref
                )
                # Soft horizontal cosine feather on the straddling threshold piece
                p_arr = np.array(p_cel, dtype=np.float32)
                xx_p = np.linspace(0.0, 1.0, tw, dtype=np.float32)[None, :]
                w_p = np.maximum(0.0, np.sin(np.pi * xx_p)) ** 0.75
                p_arr[..., 3] *= (0.82 * w_p)
                p_feathered = Image.fromarray(np.clip(p_arr, 0, 255).astype(np.uint8), mode="RGBA")
                tape_im.alpha_composite(p_feathered, dest=(jdx, jdy))
            except Exception:
                pass

    final_tape_rgb = tape_im.convert("RGB")

    # Build the per-poem Shot-by-Shot Contact Sheet (`poem_<num>_shots_sheet.png`)
    cols = 4
    rows = (n_shots + cols - 1) // cols
    tw_card, th_card = 440, 224
    pad = 12
    header_h = 196  # includes top title + full-width continuous shot tape preview!
    sheet_w = cols * tw_card + (cols + 1) * pad
    sheet_h = header_h + rows * th_card + (rows + 1) * pad

    sheet = Image.new("RGB", (sheet_w, sheet_h), (9, 12, 18))
    sdraw = ImageDraw.Draw(sheet)
    sdraw.text(
        (pad, 10),
        f"POEM {num_str}: {lv.get('title', '').upper()} — {n_shots} PAINTED SHOTS & CONTINUOUS SHOT TAPE",
        fill=(245, 206, 98),
        font=FONT_LG,
    )
    sdraw.text(
        (pad, 32),
        f"Every shot built ON TOP OF & THROUGH Foundry 3D (w1623) + Inverse Panoptic Apertures + 7-Plane Gouache Cut-Outs & Video Portals",
        fill=(164, 182, 204),
        font=FONT_XS,
    )
    # Paste the continuous shot tape across `y = 54..182`
    tape_preview = final_tape_rgb.resize((sheet_w - 2 * pad, 124), Image.Resampling.LANCZOS)
    sheet.paste(tape_preview, (pad, 54))
    sdraw.rectangle([pad, 54, sheet_w - pad, 178], outline=(80, 210, 160), width=1)

    for idx, (s_im, sm) in enumerate(zip(shot_images, shot_metas)):
        r_i = idx // cols
        c_i = idx % cols
        cx0 = pad + c_i * (tw_card + pad)
        cy0 = header_h + r_i * (th_card + pad)
        thumb = s_im.resize((tw_card, th_card - 32), Image.Resampling.LANCZOS)
        sheet.paste(thumb, (cx0, cy0 + 32))
        sdraw.rectangle([cx0, cy0, cx0 + tw_card, cy0 + 31], fill=(15, 20, 29))
        sdraw.rectangle([cx0, cy0, cx0 + tw_card, cy0 + th_card], outline=(46, 58, 78), width=1)
        inv_badge = " [INV]" if sm["used_inverse_sculpt"] else ""
        hdr = f"#{sm['k']:02d} [{sm['kind'].upper()} {sm['mm']}mm]{inv_badge} {sm['t0']:.1f}-{sm['t1']:.1f}s · {sm['district_id'].upper()}"
        sdraw.text((cx0 + 6, cy0 + 3), hdr[:54], fill=(120, 238, 190), font=FONT_SM)
        line_short = str(sm.get("line", "")).replace("\n", " ")[:62]
        sdraw.text((cx0 + 6, cy0 + 17), f"\"{line_short}\"", fill=(208, 216, 228), font=FONT_XS)

    return final_tape_rgb, sheet


def main() -> None:
    PAINTED_SHOTS_DIR.mkdir(parents=True, exist_ok=True)
    PAINTED_TAPES_DIR.mkdir(parents=True, exist_ok=True)

    print("[1/5] Loading Foundry shots.json, refs.json, inverse.json, wygwyl_atlas_manifest.json & scene_collage_plans.json...")
    shots_data = json.loads((FOUNDRY_DIR / "shots.json").read_text())
    refs_data = json.loads((FOUNDRY_DIR / "refs.json").read_text())
    inv_data = json.loads((FOUNDRY_DIR / "inverse.json").read_text())

    manifest = json.loads((SHOTS_DIR / "arena" / "parts" / "kit3" / "release_v2" / "wygwyl_atlas_manifest.json").read_text())
    parts_by_id: Dict[str, Dict[str, Any]] = {}
    for asset in manifest.get("assets", []):
        for pt in asset.get("parts", []):
            parts_by_id[pt["id"]] = pt

    collage_plans = json.loads((SHOTS_DIR / "arena" / "parts" / "kit3" / "release_v2" / "scene_collage_plans.json").read_text())
    plans_by_poem: Dict[int, List[Dict[str, Any]]] = {}
    for sc_p in collage_plans.get("scenes", []):
        p_id = int(sc_p.get("poem", sc_p.get("book", 1)))
        plans_by_poem.setdefault(p_id, []).append(sc_p)

    wag = b90._load_wag_stack_spectrogram_and_districts()
    wag["all_refs_list"] = refs_data.get("refs", [])

    w1623_shots_by_poem: Dict[str, List[Dict[str, Any]]] = {}
    for s in shots_data.get("shots", []):
        if s.get("world") == "w1623":
            w1623_shots_by_poem.setdefault(str(s["poem"]).zfill(2), []).append(s)

    refs_by_poem: Dict[str, List[Dict[str, Any]]] = {}
    for r in refs_data.get("refs", []):
        refs_by_poem.setdefault(str(r["poem"]).zfill(2), []).append(r)

    inv_by_ref: Dict[str, Dict[str, Any]] = {}
    for inv_s in inv_data.get("shots", []):
        if inv_s.get("world") == "w1623":
            inv_by_ref[str(inv_s["ref"])] = inv_s

    all_painted_shot_entries: List[Dict[str, Any]] = []
    all_painted_tape_entries: List[Dict[str, Any]] = []
    master_tape_rows: List[Image.Image] = []

    print("[2/5] Painting & Shaping all 155 Poem Shots (Poems 01..14) + Stitching 14 Continuous Shot-by-Shot Tapes...")
    for poem_num in range(1, 15):
        num_str = f"{poem_num:02d}"
        lv_path = LEVELS_DIR / num_str / "level.json"
        lv = json.loads(lv_path.read_text())
        p_shots = w1623_shots_by_poem.get(num_str, [])
        if not p_shots and poem_num == 14:
            p_shots = _synthesize_poem_14_shots(lv)
        p_shots.sort(key=lambda x: int(x.get("k", 0)))
        p_refs = refs_by_poem.get(num_str, [])
        p_plans = plans_by_poem.get(poem_num, [])

        poem_shot_ims: List[Image.Image] = []
        poem_shot_metas: List[Dict[str, Any]] = []

        for s_obj in p_shots:
            k_idx = int(s_obj.get("k", 0))
            shot_im, smeta = paint_single_shot_plate(
                shot=s_obj,
                poem_num=poem_num,
                lv=lv,
                refs_for_poem=p_refs,
                inv_by_ref=inv_by_ref,
                plans_for_poem=p_plans,
                parts_by_id=parts_by_id,
                wag=wag,
            )
            fname = f"shot_{num_str}_{k_idx:02d}.png"
            out_path = PAINTED_SHOTS_DIR / fname
            shot_im.save(out_path, "PNG", optimize=True)
            poem_shot_ims.append(shot_im)
            poem_shot_metas.append(smeta)
            b_sz = out_path.stat().st_size

            all_painted_shot_entries.append({
                "id": f"painted_shot_{num_str}_{k_idx:02d}",
                "title": f"Poem {num_str} Shot #{k_idx:02d} · {smeta['kind'].upper()} {smeta['mm']}mm ({smeta['t0']:.1f}-{smeta['t1']:.1f}s)",
                "filename": fname,
                "category": "painted_shots",
                "subcategory": f"shot_{smeta['kind']}",
                "sub_type": f"shot_{smeta['kind']}",
                "poem": num_str,
                "ref_id": smeta["ref_id"],
                "world": "w1623",
                "file": f"png_vault/painted_shots/{fname}",
                "width": shot_im.width,
                "height": shot_im.height,
                "bytes": b_sz,
                "size_kb": round(b_sz / 1024, 1),
                "shot_meta": smeta,
                "desc": f"[{smeta['district_id'].upper()} · {smeta['light']}] \"{smeta['line'][:110]}\" (Ref {smeta['ref_id']}, {smeta['portals_painted']} portals, {smeta['cast_painted']} cast)",
            })

        # Stitch this poem's painted shots into its continuous Shot-by-Shot Master Tape + Contact Sheet
        tape_rgb, sheet_rgb = stitch_poem_shot_tape(
            poem_num=poem_num,
            lv=lv,
            shot_images=poem_shot_ims,
            shot_metas=poem_shot_metas,
            parts_by_id=parts_by_id,
            wag=wag,
        )
        tape_fname = f"poem_{num_str}_shot_tape.png"
        tape_path = PAINTED_TAPES_DIR / tape_fname
        tape_rgb.save(tape_path, "PNG", optimize=True)
        tape_b = tape_path.stat().st_size

        sheet_fname = f"poem_{num_str}_shots_sheet.png"
        sheet_path = PAINTED_TAPES_DIR / sheet_fname
        sheet_rgb.save(sheet_path, "PNG", optimize=True)
        sheet_b = sheet_path.stat().st_size

        all_painted_tape_entries.append({
            "id": f"poem_{num_str}_shot_tape",
            "title": f"Poem {num_str} Continuous Painted Shot Tape ({len(poem_shot_ims)} Shots · {lv.get('title', '')})",
            "filename": tape_fname,
            "category": "painted_tapes",
            "subcategory": "continuous_shot_tape",
            "sub_type": "continuous_shot_tape",
            "poem": num_str,
            "world": "w1623",
            "file": f"png_vault/painted_tapes/{tape_fname}",
            "width": tape_rgb.width,
            "height": tape_rgb.height,
            "bytes": tape_b,
            "size_kb": round(tape_b / 1024, 1),
            "desc": f"Seamless horizontal cinema tape weaving all {len(poem_shot_ims)} painted shots of Poem {num_str} ({lv.get('title', '')}) with architectural threshold bridges & spectrogram ribbon.",
        })
        all_painted_tape_entries.append({
            "id": f"poem_{num_str}_shots_sheet",
            "title": f"Poem {num_str} Painted Shots Contact Sheet ({len(poem_shot_ims)} Shots · {lv.get('title', '')})",
            "filename": sheet_fname,
            "category": "painted_tapes",
            "subcategory": "poem_shots_sheet",
            "sub_type": "poem_shots_sheet",
            "poem": num_str,
            "world": "w1623",
            "file": f"png_vault/painted_tapes/{sheet_fname}",
            "width": sheet_rgb.width,
            "height": sheet_rgb.height,
            "bytes": sheet_b,
            "size_kb": round(sheet_b / 1024, 1),
            "desc": f"Contact sheet of all {len(poem_shot_ims)} painted multiplane cinema shots + continuous shot tape for Poem {num_str}.",
        })

        # Also add the scene-level continuous tape (`poem_<num>_scene_tape.png`) if present
        sc_tape_fname = f"poem_{num_str}_scene_tape.png"
        sc_tape_path = PAINTED_TAPES_DIR / sc_tape_fname
        if sc_tape_path.exists():
            with Image.open(sc_tape_path) as sc_im:
                sc_w, sc_h = sc_im.size
            sc_b = sc_tape_path.stat().st_size
            all_painted_tape_entries.append({
                "id": f"poem_{num_str}_scene_tape",
                "title": f"Poem {num_str} Extended Multiplane Scene Tape ({len(lv.get('scenes', []))} Scenes · {lv.get('title', '')})",
                "filename": sc_tape_fname,
                "category": "painted_tapes",
                "subcategory": "continuous_scene_tape",
                "sub_type": "continuous_scene_tape",
                "poem": num_str,
                "world": "w1623",
                "file": f"png_vault/painted_tapes/{sc_tape_fname}",
                "width": sc_w,
                "height": sc_h,
                "bytes": sc_b,
                "size_kb": round(sc_b / 1024, 1),
                "desc": f"Continuous 7-plane level background tape across all {len(lv.get('scenes', []))} scenes of Poem {num_str} with Foundry x Inverse 2D/3D corridors.",
            })

        # Build a 1800x140 master overview strip for this poem's Shot Tape
        row_im = Image.new("RGB", (1800, 140), (8, 10, 15))
        row_im.paste(tape_rgb.resize((1800, 118), Image.Resampling.LANCZOS), (0, 22))
        rdraw = ImageDraw.Draw(row_im)
        rdraw.rectangle([0, 0, 1800, 21], fill=(12, 16, 24))
        rdraw.text(
            (8, 3),
            f"POEM {num_str} SHOT-BY-SHOT PAINTED CINEMA TAPE ({len(poem_shot_ims)} SHOTS) · {lv.get('title', '').upper()}",
            fill=(110, 242, 192),
            font=FONT_SM,
        )
        master_tape_rows.append(row_im)
        print(f"  Poem {num_str} ({lv.get('title', '')}): painted {len(poem_shot_ims)} shots + stitched {tape_rgb.width}x{tape_rgb.height} continuous shot tape")

    # 3. Also paint Pure Borderless Through-Frames for all 28 Inverse-Sculpted References (`inv_painted_<ref>.png`)
    print("[3/5] Painting 28 Pure Borderless Inverse-Topology Through-Frame Plates...")
    for ref_id, inv_s in sorted(inv_by_ref.items()):
        p_str = str(inv_s.get("poem", ref_id.split("-")[0])).zfill(2)
        p_num = int(p_str)
        lv = json.loads((LEVELS_DIR / p_str / "level.json").read_text())
        p_refs = refs_by_poem.get(p_str, [])
        p_plans = plans_by_poem.get(p_num, [])
        ref_match = next((r for r in p_refs if r["id"] == ref_id), None)

        synth_shot = {
            "k": int(ref_id.split("-")[1]),
            "t0": 0.0,
            "t1": 10.0,
            "line": ref_match.get("line", "") if ref_match else "",
            "kind": "establishing" if (inv_s.get("cam", {}).get("z", 50) > 65) else "medium",
            "mm": 35,
            "light": ref_match.get("hour", "dusk→night") if ref_match else "dusk→night",
            "subject": "POET",
            "cam": inv_s.get("cam", {"hor": 0.36}),
            "frac": int(ref_id.split("-")[1]) / 8.0,
            "id": f"inv-w1623-{ref_id}",
            "world": "w1623",
            "poem": p_str,
            "img": inv_s["b"],
            "ref_override": ref_id,
            "tags": inv_s.get("tags_b", []),
        }
        inv_im, inv_meta = paint_single_shot_plate(
            shot=synth_shot,
            poem_num=p_num,
            lv=lv,
            refs_for_poem=p_refs,
            inv_by_ref=inv_by_ref,
            plans_for_poem=p_plans,
            parts_by_id=parts_by_id,
            wag=wag,
        )
        inv_fname = f"inverse_painted_{ref_id.replace('-', '_')}_w1623.png"
        inv_path = PAINTED_SHOTS_DIR / inv_fname
        inv_im.save(inv_path, "PNG", optimize=True)
        inv_b = inv_path.stat().st_size
        grown_txt = "; ".join(inv_s.get("grown", []))
        all_painted_shot_entries.append({
            "id": f"inverse_painted_{ref_id.replace('-', '_')}",
            "title": f"Inverse-Sculpted Painted Through-Frame · Ref {ref_id} (Poem {p_str})",
            "filename": inv_fname,
            "category": "painted_shots",
            "subcategory": "inverse_painted_frame",
            "sub_type": "inverse_painted_frame",
            "poem": p_str,
            "ref_id": ref_id,
            "world": "w1623",
            "file": f"png_vault/painted_shots/{inv_fname}",
            "width": inv_im.width,
            "height": inv_im.height,
            "bytes": inv_b,
            "size_kb": round(inv_b / 1024, 1),
            "shot_meta": inv_meta,
            "desc": f"Pure borderless through-frame built on top of & through sculpted w1623 ({inv_s.get('before', 0)*100:.0f}% -> {inv_s.get('after', 0)*100:.0f}%: {grown_txt}).",
        })

    # Save the Master 14-Poem Shot-Tape Panorama (`all_14_painted_shot_tapes_master.png`)
    if master_tape_rows:
        master_im = Image.new("RGB", (1804, len(master_tape_rows) * 144 + 4), (8, 10, 14))
        for i, r_im in enumerate(master_tape_rows):
            master_im.paste(r_im, (2, i * 144 + 2))
        master_fname = "all_14_painted_shot_tapes_master.png"
        master_path = PAINTED_TAPES_DIR / master_fname
        master_im.save(master_path, "PNG", optimize=True)
        master_b = master_path.stat().st_size
        if SCRATCH_DIR.exists():
            master_im.save(SCRATCH_DIR / master_fname, "PNG", optimize=True)
        all_painted_tape_entries.insert(0, {
            "id": "all_14_painted_shot_tapes_master",
            "title": "All 14 Poems · Master Painted Shot-by-Shot Cinema Tapes Panorama (155 Shots)",
            "filename": master_fname,
            "category": "painted_tapes",
            "subcategory": "master_shot_tapes_panorama",
            "sub_type": "master_shot_tapes_panorama",
            "poem": "all",
            "world": "w1623",
            "file": f"png_vault/painted_tapes/{master_fname}",
            "width": master_im.width,
            "height": master_im.height,
            "bytes": master_b,
            "size_kb": round(master_b / 1024, 1),
            "desc": "Master 14-poem panorama of all 155 painted multiplane shots woven into 14 continuous horizontal cinema tapes.",
        })

    # 4. Update `shots/png_vault/png_catalog.json` with `painted_shots` & `painted_tapes` as top featured categories!
    print("[4/5] Updating shots/png_vault/png_catalog.json with all newly painted shots & continuous tapes...")
    cat_path = VAULT_DIR / "png_catalog.json"
    if cat_path.exists():
        cat_data = json.loads(cat_path.read_text())
    else:
        cat_data = {"items": []}

    existing_items = [
        it for it in cat_data.get("items", [])
        if it.get("category") not in ("painted_shots", "painted_tapes")
    ]
    combined_items = all_painted_tape_entries + all_painted_shot_entries + existing_items
    cat_counts: Dict[str, int] = {}
    for it in combined_items:
        c = it.get("category", "other")
        cat_counts[c] = cat_counts.get(c, 0) + 1

    cat_labels = {
        "painted_tapes": "🎞️ Continuous Painted Tapes & Contact Sheets",
        "painted_shots": "🎨 Painted & Shaped Shots (183 Frames)",
        "foundry_inverse": "🔨 Foundry & Inverse Through-Frame Builds",
        "session_artifacts": "🔬 Session Proofs, Audits & Contact Sheets",
        "multiplane_tapes": "🏛️ Extended Multiplane Scene Modules (WebP)",
        "master_kit_sheets": "🧩 Cut-Out Master Sheets & Cast Plates",
    }
    ordered_cats = ["painted_tapes", "painted_shots", "foundry_inverse", "session_artifacts", "multiplane_tapes", "master_kit_sheets"]
    categories_list = []
    for cid in ordered_cats:
        if cat_counts.get(cid, 0) > 0:
            categories_list.append({
                "id": cid,
                "label": cat_labels.get(cid, cid),
                "count": cat_counts[cid],
            })
    for cid, cnt in cat_counts.items():
        if cid not in ordered_cats and cnt > 0:
            categories_list.append({"id": cid, "label": cat_labels.get(cid, cid), "count": cnt})

    cat_data["total"] = len(combined_items)
    cat_data["painted_tapes_count"] = len(all_painted_tape_entries)
    cat_data["painted_shots_count"] = len(all_painted_shot_entries)
    cat_data["foundry_inverse_count"] = cat_counts.get("foundry_inverse", 62)
    cat_data["artifact_png_count"] = cat_counts.get("session_artifacts", 283)
    cat_data["vault_png_count"] = (
        len(all_painted_tape_entries)
        + len(all_painted_shot_entries)
        + cat_counts.get("foundry_inverse", 62)
        + cat_counts.get("session_artifacts", 283)
    )
    cat_data["repo_plates_and_sheets_count"] = cat_counts.get("multiplane_tapes", 0) + cat_counts.get("master_kit_sheets", 0)
    cat_data["categories"] = categories_list
    cat_data["items"] = combined_items
    cat_path.write_text(json.dumps(cat_data, indent=2))

    # Also save a dedicated manifest of all painted shots & tapes for `foundry_inverse.html`
    painted_manifest = {
        "total_painted_shots": len(all_painted_shot_entries),
        "total_painted_tapes": len(all_painted_tape_entries),
        "tapes": all_painted_tape_entries,
        "shots": all_painted_shot_entries,
    }
    (FOUNDRY_DIR / "painted_shots_manifest.json").write_text(json.dumps(painted_manifest, indent=2))

    print(
        f"[5/5] DONE! Painted {len(all_painted_shot_entries)} pure multiplane shot & inverse frames + "
        f"{len(all_painted_tape_entries)} continuous tapes & contact sheets (Total PNG catalog: {len(combined_items)} plates)."
    )


if __name__ == "__main__":
    main()
