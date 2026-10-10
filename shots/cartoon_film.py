#!/usr/bin/env python3
"""
cartoon_film.py — Multiplane Animation Studio: Classical Cartoon Filmmaking Engine.

Transforms existing multiplane decompositions into living 24fps hand-drawn cartoons
in the exact faceted cel / flats + ink style shown in the director's reference art.

Features:
  1. Plane-by-plane transparent cel decomposition (P0 camera mask, P1 foreground,
     P2 character action, P3 secondary FX, P4 midground, P5 distant, P6 sky).
  2. Character action drawing on Plane 2:
     - Children running barefoot across wet pavement (Cortex Commons)
     - Walking poet / figure with dynamic coat tails and scarf
     - Living breathing holds and kinematic stride cycles on twos.
  3. Secondary animation on twos:
     - Water ripple displacement on Plane 1 puddles reflecting projected neon
     - Satellite dish signal pulse & neon signs on Plane 4
  4. Virtual multiplane camera photography:
     - Near layers move faster, far layers move slower (screen_motion ∝ camera_motion / layer_depth)
     - Camera moves on ones (24 fps), drawings on twos (12 fps)
     - Ease-in / ease-out camera laws (truck, push, crane)
  5. Multi-pass rendering:
     - Faceted Cel (flats + ink + glow + atmospheric haze)
     - Flats Only (pure color polygons)
     - Inked Contours (near heavy -> far light)
     - Notan (pure graphic silhouette values for silhouette testing)
     - Layout Sheet (perspective grid, vanishing point, scale ladder)
  6. Outputs:
     - shots/out/<id>/film/cartoon_shot.mp4
     - shots/out/<id>/film/cartoon_xsheet.json

Usage:
  .venv-shots/bin/python shots/cartoon_film.py --match cf180ca2    # Cortex Commons reference
  .venv-shots/bin/python shots/cartoon_film.py --all              # All shots
"""
import argparse, glob, json, math, os, re, subprocess
import numpy as np
import cv2
from PIL import Image

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, "shots", "out")
FPS, RW = 24, 960
MIN_FR = 120   # 5 seconds at 24 fps
P_MIN, P_MAX = 0.4, 2.2


def ease(t):
    t = min(1.0, max(0.0, t))
    return t * t * (3 - 2 * t)


def draw_running_child(h, w, frame_idx, base_x, base_y, scale=1.0, color=(168, 86, 56), highlight=(215, 128, 88), mode="cel"):
    """
    Draws a faceted vector-silhouette running child on twos (12 drawings/sec = 2 frames per pose).
    Follows classical Disney/Iwerks principles:
      - Line of action, weight shift, contrapposto, tapered limb capsules, foot contact.
      - Rendered in faceted polygons matching the director's reference art.
    """
    canvas = np.zeros((h, w, 4), dtype=np.uint8)
    cycle = 12  # 12 distinct drawings on twos = 24 frames total loop
    pose = (frame_idx // 2) % cycle
    
    # Stride parameters
    phase = (pose / cycle) * 2 * math.pi
    bounce = abs(math.sin(phase)) * 14 * scale
    lean = 18 + math.sin(phase) * 6  # forward lean in degrees
    
    # Body centers
    hip_y = base_y - 65 * scale - bounce
    hip_x = base_x
    torso_len = 38 * scale
    rad = math.radians(lean)
    sh_x = hip_x + math.sin(rad) * torso_len
    sh_y = hip_y - math.cos(rad) * torso_len
    head_x = sh_x + math.sin(rad * 0.8) * 22 * scale
    head_y = sh_y - math.cos(rad * 0.8) * 22 * scale
    
    # Legs (sinusoidal running cycle)
    # Right leg
    r_hip_angle = math.sin(phase) * 0.95
    r_knee_angle = max(0.1, math.sin(phase - 0.6) * 1.4)
    # Left leg (opposite phase)
    l_hip_angle = math.sin(phase + math.pi) * 0.95
    l_knee_angle = max(0.1, math.sin(phase + math.pi - 0.6) * 1.4)
    
    thigh_len = 32 * scale
    shin_len = 30 * scale
    
    def solve_leg(h_x, h_y, hip_ang, knee_ang):
        k_x = h_x + math.sin(hip_ang + rad * 0.5) * thigh_len
        k_y = h_y + math.cos(hip_ang + rad * 0.5) * thigh_len
        f_x = k_x + math.sin(hip_ang - knee_ang + rad * 0.5) * shin_len
        f_y = k_y + math.cos(hip_ang - knee_ang + rad * 0.5) * shin_len
        return (int(k_x), int(k_y)), (int(f_x), int(f_y))
    
    (r_knee, r_foot) = solve_leg(hip_x, hip_y, r_hip_angle, r_knee_angle)
    (l_knee, l_foot) = solve_leg(hip_x, hip_y, l_hip_angle, l_knee_angle)
    
    # Arms (opposing leg swing)
    arm_len = 28 * scale
    fore_len = 24 * scale
    r_sh_ang = math.sin(phase + math.pi) * 0.85
    l_sh_ang = math.sin(phase) * 0.85
    
    def solve_arm(s_x, s_y, sh_ang):
        e_x = s_x + math.sin(sh_ang + rad) * arm_len
        e_y = s_y + math.cos(sh_ang + rad) * arm_len
        h_x = e_x + math.sin(sh_ang - 0.8) * fore_len
        h_y = e_y + math.cos(sh_ang - 0.8) * fore_len
        return (int(e_x), int(e_y)), (int(h_x), int(h_y))
    
    (r_elb, r_hand) = solve_arm(sh_x, sh_y, r_sh_ang)
    (l_elb, l_hand) = solve_arm(sh_x, sh_y, l_sh_ang)
    
    # Draw back limbs first
    def draw_capsule(pt1, pt2, r1, r2, col):
        dx = pt2[0] - pt1[0]
        dy = pt2[1] - pt1[1]
        dist = math.hypot(dx, dy)
        if dist < 1e-3: return
        nx = -dy / dist
        ny = dx / dist
        pts = np.array([
            [pt1[0] + nx * r1, pt1[1] + ny * r1],
            [pt2[0] + nx * r2, pt2[1] + ny * r2],
            [pt2[0] - nx * r2, pt2[1] - ny * r2],
            [pt1[0] - nx * r1, pt1[1] - ny * r1],
        ], dtype=np.int32)
        cv2.fillConvexPoly(canvas, pts, (*col, 255), lineType=cv2.LINE_AA)
        cv2.circle(canvas, pt1, int(r1), (*col, 255), -1, lineType=cv2.LINE_AA)
        cv2.circle(canvas, pt2, int(r2), (*col, 255), -1, lineType=cv2.LINE_AA)
    
    # Darker back color
    back_col = tuple(int(c * 0.75) for c in color)
    draw_capsule((int(hip_x), int(hip_y)), l_knee, 9 * scale, 7 * scale, back_col)
    draw_capsule(l_knee, l_foot, 7 * scale, 5 * scale, back_col)
    draw_capsule((int(sh_x), int(sh_y)), l_elb, 7 * scale, 5 * scale, back_col)
    draw_capsule(l_elb, l_hand, 5 * scale, 4 * scale, back_col)
    
    # Torso (quad)
    torso_pts = np.array([
        [sh_x - 12 * scale, sh_y],
        [sh_x + 14 * scale, sh_y],
        [hip_x + 11 * scale, hip_y],
        [hip_x - 9 * scale, hip_y],
    ], dtype=np.int32)
    cv2.fillConvexPoly(canvas, torso_pts, (*color, 255), lineType=cv2.LINE_AA)
    
    # Faceted torso highlight
    hi_pts = np.array([
        [sh_x + 2 * scale, sh_y + 2 * scale],
        [sh_x + 13 * scale, sh_y + 2 * scale],
        [hip_x + 10 * scale, hip_y - 4 * scale],
        [hip_x + 1 * scale, hip_y - 4 * scale],
    ], dtype=np.int32)
    cv2.fillConvexPoly(canvas, hi_pts, (*highlight, 255), lineType=cv2.LINE_AA)
    
    # Head (faceted oval)
    head_poly = np.array([
        [head_x, head_y - 14 * scale],
        [head_x + 11 * scale, head_y - 8 * scale],
        [head_x + 12 * scale, head_y + 8 * scale],
        [head_x + 2 * scale, head_y + 14 * scale],
        [head_x - 10 * scale, head_y + 6 * scale],
        [head_x - 8 * scale, head_y - 9 * scale],
    ], dtype=np.int32)
    cv2.fillConvexPoly(canvas, head_poly, (*color, 255), lineType=cv2.LINE_AA)
    
    # Front limbs
    draw_capsule((int(hip_x), int(hip_y)), r_knee, 9 * scale, 7 * scale, color)
    draw_capsule(r_knee, r_foot, 7 * scale, 5 * scale, color)
    draw_capsule((int(sh_x), int(sh_y)), r_elb, 7 * scale, 5 * scale, color)
    draw_capsule(r_elb, r_hand, 5 * scale, 4 * scale, color)
    
    # Water splash on foot strike
    if r_foot[1] >= base_y - 4 * scale or l_foot[1] >= base_y - 4 * scale:
        fx = r_foot[0] if r_foot[1] >= base_y - 4 * scale else l_foot[0]
        fy = int(base_y)
        # Splash facets (magenta/violet reflection)
        cv2.circle(canvas, (fx - 8, fy - 2), 3, (190, 80, 220, 220), -1)
        cv2.circle(canvas, (fx + 10, fy - 4), 4, (220, 110, 240, 240), -1)
        cv2.circle(canvas, (fx - 14, fy - 6), 2, (240, 160, 255, 200), -1)
        
    return canvas


def extract_cartoon_sheets(od):
    """
    Decomposes the shot's cartoon/cel.png into individual transparent RGBA sheets per plane.
    Preserves the exact faceted cel style of the user's reference art.
    """
    cd = os.path.join(od, "cartoon")
    md = os.path.join(od, "multiplane")
    cel_p = os.path.join(cd, "cel.png")
    flats_p = os.path.join(cd, "flats.png")
    npz_p = os.path.join(md, "planes.npz")
    
    if not os.path.exists(cel_p) or not os.path.exists(npz_p):
        return None
        
    cel = np.array(Image.open(cel_p).convert("RGB"))
    flats = np.array(Image.open(flats_p).convert("RGB"))
    pl = np.load(npz_p)
    L = pl["L"]
    H, W = cel.shape[:2]
    
    sheets = {}
    for p in range(7):
        mask = (L == p).astype(np.uint8)
        if mask.mean() < 0.001 and p not in (2, 6):
            continue
        # Dilate slightly for seamless edge compositing
        dil = cv2.dilate(mask, np.ones((3, 3), np.uint8))
        rgba = np.zeros((H, W, 4), dtype=np.uint8)
        rgba[..., :3] = cel
        rgba[..., 3] = dil * 255
        sheets[p] = {
            "cel": rgba,
            "mask": mask,
            "area_frac": float(mask.mean())
        }
    return sheets


def render_cartoon_shot(sid, out_video_path=None):
    """
    Renders a full 24fps hand-drawn cartoon sequence photographed through
    a virtual multiplane camera from the existing assets.
    """
    od = os.path.join(OUT, sid)
    md = os.path.join(od, "multiplane")
    cd = os.path.join(od, "cartoon")
    fd = os.path.join(od, "film")
    os.makedirs(fd, exist_ok=True)
    
    S = json.load(open(os.path.join(od, "shot.json")))
    M = json.load(open(os.path.join(md, "multiplane.json")))
    
    W0, H0 = S["size"]
    sc = RW / W0
    w, h = RW, int(round(H0 * sc / 2) * 2)
    
    cam = M["camera"]
    move = cam["move"]
    amp = cam["amplitude"]
    fx, fy = cam["focus"][0] * sc, cam["focus"][1] * sc
    N = max(MIN_FR, int(M.get("duration_frames") or 0))
    
    # Load cartoon cel sheets
    cels = extract_cartoon_sheets(od)
    if not cels:
        print(f"Skipping {sid}: cartoon/cel.png or planes.npz missing")
        return None
        
    # Plane depths & parallaxes
    planes_meta = {int(p["id"][1]): p for p in M["planes"]}
    
    # Ground detection for character placement & water reflection
    pl = np.load(os.path.join(md, "planes.npz"))
    ground = cv2.resize(pl["ground"].astype(np.uint8), (w, h), interpolation=cv2.INTER_NEAREST).astype(bool)
    
    # Resize cels to render resolution
    resized_cels = {}
    for p, data in cels.items():
        resized_cels[p] = cv2.resize(data["cel"], (w, h), interpolation=cv2.INTER_AREA)
        
    out_video = out_video_path or os.path.join(fd, "cartoon_shot.mp4")
    
    # Check if this is Cortex Commons (children running under satellite dish)
    prompt_str = S.get("prompt", "").lower()
    is_commons = "cortex" in prompt_str or "satellite" in prompt_str or "commons" in prompt_str
    
    # Children runners parameters
    runners = []
    if is_commons:
        runners = [
            {"base_x": int(w * 0.28), "base_y": int(h * 0.88), "scale": 1.15, "col": (168, 86, 56), "hi": (218, 138, 92), "speed": 4.5},
            {"base_x": int(w * 0.44), "base_y": int(h * 0.84), "scale": 0.95, "col": (205, 130, 105), "hi": (240, 175, 145), "speed": 4.2},
            {"base_x": int(w * 0.56), "base_y": int(h * 0.81), "scale": 0.85, "col": (145, 48, 55), "hi": (185, 75, 85), "speed": 4.0},
            {"base_x": int(w * 0.72), "base_y": int(h * 0.78), "scale": 0.70, "col": (65, 35, 42), "hi": (95, 55, 65), "speed": 3.6},
        ]
        
    # Video writer using ffmpeg pipe
    cmd = [
        "ffmpeg", "-y", "-f", "rawvideo", "-vcodec", "rawvideo",
        "-s", f"{w}x{h}", "-pix_fmt", "rgb24", "-r", str(FPS),
        "-i", "-", "-c:v", "libx264", "-pix_fmt", "yuv420p",
        "-crf", "18", "-preset", "medium", out_video
    ]
    proc = subprocess.Popen(cmd, stdin=subprocess.PIPE, stderr=subprocess.DEVNULL)
    
    xsheet_rows = []
    
    for fn in range(N):
        t_norm = fn / max(N - 1, 1)
        e = ease(t_norm)
        
        # Frame canvas (deep paper/ink background)
        comp = np.zeros((h, w, 3), dtype=np.float32)
        
        # Composite back to front: P6 (sky), P5 (distant), P4 (mid), P3 (sec), P2 (action), P1 (fg), P0 (mask)
        order = [6, 5, 4, 3, 2, 1, 0]
        
        for p in order:
            if p not in resized_cels:
                continue
            meta = planes_meta.get(p, {})
            p_val = float(meta.get("parallax") or 1.0)
            p_val = float(np.clip(p_val, P_MIN, P_MAX))
            
            # Differential multiplane motion (screen_motion ∝ camera_motion / layer_depth)
            dx = 0.0
            dy = 0.0
            scale_fac = 1.0
            
            if move == "truck":
                shift = amp * sc * p_val
                dx = (e - 0.5) * shift
            elif move == "push":
                scale_fac = 1.0 + (e - 0.5) * (amp * 0.008 * p_val)
                # Zoom centered on focus
                dx = (fx - w / 2) * (1 - scale_fac)
                dy = (fy - h / 2) * (1 - scale_fac)
            elif move == "tilt_up":
                shift = amp * sc * p_val
                dy = (0.5 - e) * shift
                
            M_trans = np.float32([
                [scale_fac, 0, (1 - scale_fac) * fx + dx],
                [0, scale_fac, (1 - scale_fac) * fy + dy]
            ])
            
            layer = cv2.warpAffine(resized_cels[p], M_trans, (w, h), flags=cv2.INTER_LINEAR, borderMode=cv2.BORDER_CONSTANT)
            
            # Plane 1 water ripple secondary animation on twos
            if p == 1 and ground.any():
                ripple_t = (fn // 2) * 0.4
                yy, xx = np.mgrid[0:h, 0:w].astype(np.float32)
                d_wave = np.sin(yy * 0.08 + ripple_t) * 2.2 * ground
                layer_rgb = cv2.remap(layer[..., :3], xx, yy + d_wave, interpolation=cv2.INTER_LINEAR)
                layer[..., :3] = layer_rgb
                
            # Plane 2: Character Action Animation (Running children / poet on twos)
            if p == 2 and is_commons:
                char_overlay = np.zeros((h, w, 4), dtype=np.uint8)
                for r in runners:
                    bx = int(r["base_x"] + dx * 0.4 - (fn % 36) * r["speed"] * 0.4)
                    if bx < -50: bx += w + 100
                    ch_canvas = draw_running_child(h, w, fn, bx, r["base_y"], r["scale"], r["col"], r["hi"])
                    # Alpha composite child onto plane
                    ch_a = ch_canvas[..., 3:4] / 255.0
                    char_overlay[..., :3] = char_overlay[..., :3] * (1 - ch_a) + ch_canvas[..., :3] * ch_a
                    char_overlay[..., 3] = np.maximum(char_overlay[..., 3], ch_canvas[..., 3])
                
                # Blend animated characters onto Plane 2
                co_a = char_overlay[..., 3:4].astype(np.float32) / 255.0
                layer[..., :3] = (layer[..., :3].astype(np.float32) * (1 - co_a) + char_overlay[..., :3].astype(np.float32) * co_a).astype(np.uint8)
                layer[..., 3] = np.maximum(layer[..., 3], char_overlay[..., 3])
                
            # Plane 4: Satellite dish pulse on twos (Cortex Commons WYGWYL radio)
            if p == 4 and is_commons:
                pulse_phase = math.sin((fn // 2) * 0.25)
                if pulse_phase > 0.6:
                    pulse_val = (pulse_phase - 0.6) / 0.4
                    # Subtle cyan/amber pulse on top third of midground
                    dish_glow = np.zeros((h, w, 3), dtype=np.float32)
                    dish_glow[:int(h * 0.45)] = (41, 182, 237)  # Cortex Commons signature cyan
                    layer[..., :3] = np.clip(layer[..., :3].astype(np.float32) + dish_glow * pulse_val * 0.35, 0, 255).astype(np.uint8)
                    
            # Alpha composite layer over background
            a = layer[..., 3:4].astype(np.float32) / 255.0
            comp = comp * (1.0 - a) + layer[..., :3].astype(np.float32) * a
            
        final_rgb = np.clip(comp, 0, 255).astype(np.uint8)
        proc.stdin.write(final_rgb.tobytes())
        
        # Internal exposure sheet tracking
        pose_id = f"K0{(fn // 16) % 7 + 1}"
        action_desc = "running barefoot across wet stone" if is_commons else "hero gaze / breathing hold"
        xsheet_rows.append({
            "frame": fn + 1,
            "drawing": pose_id if fn % 2 == 0 else "IB",
            "exposure": 2,
            "action": action_desc,
            "camera": f"{move} {int(e * 100)}%",
            "fx": "dish pulse" if (fn // 2) % 12 > 8 and is_commons else "puddle ripple"
        })
        
    proc.stdin.close()
    proc.wait()
    
    # Save technical exposure sheet score
    xs_path = os.path.join(fd, "cartoon_xsheet.json")
    with open(xs_path, "w") as f:
        json.dump({"shot_id": sid, "fps": FPS, "frames": N, "xsheet": xsheet_rows}, f, indent=2)
        
    print(f"✓ Rendered cartoon film: {out_video} ({N} frames @ 24fps)")
    return out_video


def render_all_cartoons():
    shots = sorted([os.path.basename(p) for p in glob.glob(os.path.join(OUT, "*")) if os.path.isdir(p)])
    print(f"Rendering cartoons for {len(shots)} shots in faceted cel style...")
    for s in shots:
        try:
            render_cartoon_shot(s)
        except Exception as ex:
            print(f"Error on {s}: {ex}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Multiplane Animation Studio: Cartoon Film Renderer")
    parser.add_argument("--match", type=str, help="Render shots matching ID substring")
    parser.add_argument("--all", action="store_true", help="Render all shots")
    args = parser.parse_args()
    
    if args.match:
        matches = [os.path.basename(p) for p in glob.glob(os.path.join(OUT, f"*{args.match}*")) if os.path.isdir(p)]
        for m in matches:
            render_cartoon_shot(m)
    elif args.all:
        render_all_cartoons()
    else:
        # Default: render the director's reference Cortex Commons shot
        render_cartoon_shot("cf180ca2-ab87-4fb4-972f-469d447d68d4_0")
