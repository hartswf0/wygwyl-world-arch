#!/usr/bin/env python3
"""
Fast, high-precision fusion of:
  1. 3D Multiplane Common Places (`depth_sharp.npz`, `curr_rgb`, `mp_curr['disp']`)
  2. Round 1 + Round 2 Handmade SCION Studio films (`shots/paeleo/handmade/<01..14>-*/film.mp4`)
     with 100% de-bradded 4-angle painted characters, props, and SCION 01..50 apparatus
  3. Afterlight 3D Optical Shaders (`FX01..FX14`).
"""
import os
import glob
import cv2
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
SHOTS = os.path.dirname(HERE)
W = 1280
H = 720
FPS = 24

_POEM_HANDMADE_FRAMES = {}


def _strip_bottom_subtitle_band(rgb):
    """
    Removes the bottom subtitle pill (`y = 650..708, x = 140..1140`) from a 1280x720
    frame of `film.mp4` so downstream sheets and Videotext films never have double subtitles.
    """
    out = rgb.copy()
    # Smoothly blend/tile the stage floor just above y=648 into y=648..712 across x=120..1160
    src_band = out[616:648, 120:1160]  # 32px tall strip above subtitle box
    tiled = np.vstack([src_band, src_band[::-1]])[:64, :]  # 64px tall seamless mirror
    tiled = cv2.GaussianBlur(tiled, (5, 5), 1.2)
    alpha = np.linspace(0.0, 1.0, 64, dtype=np.float32)[:, None, None]
    # Fade in horizontally too
    wx = np.ones((1, 1040, 1), dtype=np.float32)
    wx[:, :40, 0] = np.linspace(0.0, 1.0, 40)
    wx[:, -40:, 0] = np.linspace(1.0, 0.0, 40)
    w = alpha * wx
    patch = out[648:712, 120:1160].astype(np.float32)
    out[648:712, 120:1160] = np.clip(patch * (1.0 - w) + tiled.astype(np.float32) * w, 0, 255).astype(np.uint8)
    return out


def get_handmade_poem_frame_rgb(poem_num, u_poem):
    """
    Loads and caches the Round 1 + Round 2 Handmade SCION Studio film frames
    from `shots/paeleo/handmade/<01..14>-*/film.mp4` as RGB uint8 (1280x720),
    excluding the opening title slate (`0..80`) and closing audit slate (`total-96..total`)
    and stripping the bottom subtitle pill.
    """
    pnum = int(poem_num)
    if pnum not in _POEM_HANDMADE_FRAMES:
        pattern = os.path.join(HERE, "handmade", f"{pnum:02d}-*", "film.mp4")
        matches = sorted(glob.glob(pattern))
        frames = []
        if matches:
            cap = cv2.VideoCapture(matches[0])
            total = int(cap.get(cv2.CAP_PROP_FRAME_COUNT)) or 768
            start_f = 82
            end_f = max(start_f + 48, total - 96)
            cap.set(cv2.CAP_PROP_POS_FRAMES, start_f)
            idx = start_f
            while idx < end_f:
                ok, bgr = cap.read()
                if not ok or bgr is None:
                    break
                if (idx - start_f) % 2 == 0:
                    if bgr.shape[1] != W or bgr.shape[0] != H:
                        bgr = cv2.resize(bgr, (W, H), interpolation=cv2.INTER_AREA)
                    rgb = cv2.cvtColor(bgr, cv2.COLOR_BGR2RGB)
                    rgb = _strip_bottom_subtitle_band(rgb)
                    frames.append(rgb)
                idx += 1
            cap.release()
        if len(_POEM_HANDMADE_FRAMES) >= 3:
            _POEM_HANDMADE_FRAMES.clear()
        _POEM_HANDMADE_FRAMES[pnum] = frames

    frames = _POEM_HANDMADE_FRAMES[pnum]
    if not frames:
        return np.zeros((H, W, 3), dtype=np.uint8)
    u_clamped = float(np.clip(u_poem, 0.0, 0.9999))
    f_i = int(u_clamped * len(frames))
    return frames[f_i]


def blend_multiplane_and_handmade_scion(poem_num, curr_rgb, past_rgb, st_curr, mp_curr, u_seg, t, total_dur):
    """
    Fuses:
      1. 3D Multiplane depth_sharp station (`curr_rgb`, `mp_curr['disp']`)
      2. Round 1 + Round 2 Handmade SCION Studio craft (`get_handmade_poem_frame_rgb`)
         with de-bradded 4-angle characters, props, and SCION 01..50 apparatus
    before `apply_poem_afterlight_fx` applies the 3D Afterlight optical physics (`FX01..FX14`).
    """
    u_poem = float(np.clip(t / max(1.0, total_dur), 0.0, 1.0))
    hm_u8 = get_handmade_poem_frame_rgb(poem_num, u_poem)
    hm_rgb = hm_u8.astype(np.float32) / 255.0

    # Compute local detail / foreground presence in the handmade SCION frame
    hm_gray = 0.299 * hm_rgb[:, :, 0] + 0.587 * hm_rgb[:, :, 1] + 0.114 * hm_rgb[:, :, 2]
    hm_blur = cv2.GaussianBlur(hm_gray, (0, 0), 9.0)
    hm_detail = np.clip(np.abs(hm_gray - hm_blur) * 3.8, 0.0, 1.0)
    hm_sat = np.max(hm_rgb, axis=2) - np.min(hm_rgb, axis=2)
    hm_salience = np.clip(hm_detail * 0.65 + hm_sat * 0.85, 0.0, 1.0)
    hm_salience = cv2.GaussianBlur(hm_salience, (0, 0), 3.0)[..., None]

    is_common_place = (st_curr.get("kind_badge") == "COMMON PLACE")
    disp = mp_curr["disp"][..., None]

    if is_common_place:
        # On 3D Common Place architectural stations: preserve the 3D parallax architecture in the background
        # while the Round 2 handmade SCION characters, props, and apparatus inhabit the foreground & mid-plane
        w_hm = np.clip(0.38 + 0.48 * hm_salience + 0.14 * disp, 0.32, 0.88)
    else:
        # On SCION / Painted Cel stations: lead with the Round 1 + Round 2 Handmade SCION Studio frame
        # infused with the 3D multiplane depth relief
        w_hm = np.clip(0.64 + 0.30 * hm_salience, 0.58, 0.92)

    fused_curr = np.clip(curr_rgb * (1.0 - w_hm) + hm_rgb * w_hm, 0.0, 1.0)
    fused_past = np.clip(past_rgb * (1.0 - w_hm * 0.7) + hm_rgb * (w_hm * 0.7), 0.0, 1.0)
    return fused_curr, fused_past
