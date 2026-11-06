#!/usr/bin/env python3
"""
Synthesizes the 6 standard Bolas motion bank vignettes in shots/arena/bolas/bank/:
  - T001.json: Heel, flat, ball, toe (walk, 110 frames)
  - T014.json: Quarter, half, whole turn (turn, 150 frames)
  - T006.json: Sitting down, standing up (sit, 150 frames)
  - T080.json: Hanging a picture (reach, 230 frames)
  - T046.json: The letter changes hands (handoff, 180 frames)
  - T108.json: Stand after a fall (fall, 260 frames)
"""

import json
import math
import os
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
SHOTS = os.path.dirname(HERE)
BANK_DIR = os.path.join(SHOTS, "arena", "bolas", "bank")
os.makedirs(BANK_DIR, exist_ok=True)

N = [
    "pelvis", "hipL", "hipR", "kneeL", "kneeR", "ankleL", "ankleR",
    "heelL", "heelR", "ballL", "ballR", "toeL", "toeR",
    "spineMid", "neckBase", "chest", "shoulderL", "shoulderR",
    "elbowL", "elbowR", "wristL", "wristR", "headBase", "head",
    "headTop", "nose"
]


def base_skeleton():
    # Canonical skeleton with natural 3.5cm knee bend margin so 2D card IK never overstretches
    return {
        "pelvis": np.array([0.0, 91.2, 0.0]),
        "hipL": np.array([9.5, 91.2, 0.0]),
        "hipR": np.array([-9.5, 91.2, 0.0]),
        "kneeL": np.array([10.5, 47.0, 5.0]),
        "kneeR": np.array([-10.5, 47.0, 5.0]),
        "ankleL": np.array([11.0, 6.0, 0.0]),
        "ankleR": np.array([-11.0, 6.0, 0.0]),
        "heelL": np.array([11.0, 0.0, -6.0]),
        "heelR": np.array([-11.0, 0.0, -6.0]),
        "ballL": np.array([11.0, 0.0, 16.0]),
        "ballR": np.array([-11.0, 0.0, 16.0]),
        "toeL": np.array([11.0, 0.0, 26.0]),
        "toeR": np.array([-11.0, 0.0, 26.0]),
        "spineMid": np.array([0.0, 114.5, 0.0]),
        "chest": np.array([0.0, 132.5, 0.0]),
        "neckBase": np.array([0.0, 147.0, 0.0]),
        "shoulderL": np.array([21.0, 142.0, -1.0]),
        "shoulderR": np.array([-21.0, 142.0, -1.0]),
        "elbowL": np.array([26.0, 113.0, -2.0]),
        "elbowR": np.array([-26.0, 113.0, -2.0]),
        "wristL": np.array([29.0, 87.0, 3.0]),
        "wristR": np.array([-29.0, 87.0, 3.0]),
        "headBase": np.array([0.0, 154.0, 1.0]),
        "head": np.array([0.0, 167.2, 1.0]),
        "headTop": np.array([0.0, 180.4, 1.0]),
        "nose": np.array([0.0, 166.4, 11.0]),
    }


def rot_y(theta_rad):
    c, s = math.cos(theta_rad), math.sin(theta_rad)
    return np.array([[c, 0.0, s], [0.0, 1.0, 0.0], [-s, 0.0, c]])


def two_bone_leg(hip, ankle, l1, l2, fwd):
    v = ankle - hip
    d = float(np.linalg.norm(v))
    d = min(max(d, abs(l1 - l2) + 1e-3), (l1 + l2) * 0.985)
    u = v / (np.linalg.norm(v) + 1e-9)
    x = (l1 * l1 - l2 * l2 + d * d) / (2 * d)
    h = math.sqrt(max(0.0, l1 * l1 - x * x))
    pole = fwd - u * float(fwd @ u)
    pole /= np.linalg.norm(pole) + 1e-9
    knee = hip + u * x + pole * h
    return knee, hip + u * d


def pack_actor(J, fwd):
    return {
        "j": [[round(float(x), 2) for x in J[k]] for k in N],
        "fwd": [round(float(x), 4) for x in fwd],
    }


def make_T014():
    frames = []
    B = base_skeleton()
    for f in range(150):
        u = max(0.0, (f - 10) / 125.0)
        u = min(1.0, u)
        ang = u * 2.0 * math.pi
        R = rot_y(ang)
        fwd = R @ np.array([0.0, 0.0, 1.0])
        J = {}
        liftL = 2.5 * max(0.0, math.sin(f * 0.22)) if 12 <= f <= 135 else 0.0
        liftR = 2.5 * max(0.0, -math.sin(f * 0.22)) if 12 <= f <= 135 else 0.0
        for k, p in B.items():
            q = R @ p
            if k.endswith("L") and k.startswith(("ankle", "heel", "ball", "toe", "knee")):
                q = q + np.array([0.0, liftL * (0.5 if "knee" in k else 1.0), 0.0])
            elif k.endswith("R") and k.startswith(("ankle", "heel", "ball", "toe", "knee")):
                q = q + np.array([0.0, liftR * (0.5 if "knee" in k else 1.0), 0.0])
            J[k] = q
        frames.append({"a": {"a0": pack_actor(J, fwd)}, "p": {}})
    return {
        "id": "T014",
        "title": "Quarter, half, whole turn",
        "view": {"yaw": -22, "elev": 8, "x": 0, "z": 0, "zoom": 1.005},
        "frames": frames,
    }


def make_T001():
    frames = []
    B = base_skeleton()
    ang = math.radians(68.0)
    R = rot_y(ang)
    fwd = R @ np.array([0.0, 0.0, 1.0])
    right = R @ np.array([1.0, 0.0, 0.0])
    stride = 34.0
    cycle = 28
    n_steps = 10
    step_pos = [s * (stride * 0.5) - stride * 1.5 for s in range(n_steps)]
    for f in range(110):
        prog = f / float(cycle) * 2.0
        s_idx = int(math.floor(prog))
        u = prog - s_idx
        u_sm = u * u * (3.0 - 2.0 * u)
        if s_idx % 2 == 0:
            zL = step_pos[s_idx]
            liftL = 0.0
            zR = (1.0 - u_sm) * step_pos[max(0, s_idx - 1)] + u_sm * step_pos[min(n_steps - 1, s_idx + 1)]
            liftR = 6.5 * math.sin(u * math.pi)
            pel_along = 0.65 * zL + 0.35 * zR
        else:
            zR = step_pos[s_idx]
            liftR = 0.0
            zL = (1.0 - u_sm) * step_pos[max(0, s_idx - 1)] + u_sm * step_pos[min(n_steps - 1, s_idx + 1)]
            liftL = 6.5 * math.sin(u * math.pi)
            pel_along = 0.65 * zR + 0.35 * zL
        bob = -1.5 * math.sin(u * math.pi)
        if f == 0 or f >= 98:
            liftL = liftR = 0.0
            bob = 0.0
            zL = zR = pel_along = step_pos[0 if f == 0 else s_idx]
        J = {}
        for k, p in B.items():
            J[k] = R @ p + fwd * pel_along + np.array([0.0, bob, 0.0])
        for sd, z_ft, lift, sgn in (("L", zL, liftL, 1.0), ("R", zR, liftR, -1.0)):
            lat = right * (10.0 * sgn)
            ank = fwd * z_ft + lat + np.array([0.0, 6.0 + lift, 0.0])
            heel = fwd * (z_ft - 6.0) + lat + np.array([0.0, lift, 0.0])
            ball = fwd * (z_ft + 16.0) + lat + np.array([0.0, lift, 0.0])
            toe = fwd * (z_ft + 26.0) + lat + np.array([0.0, lift, 0.0])
            kn, ank = two_bone_leg(J["hip" + sd], ank, 46.0, 42.9, fwd)
            J["knee" + sd] = kn
            J["ankle" + sd] = ank
            J["heel" + sd] = heel
            J["ball" + sd] = ball
            J["toe" + sd] = toe
            swing = (z_ft - pel_along) * (-0.38)
            J["elbow" + sd] = J["shoulder" + sd] + fwd * (swing * 0.45) + np.array([5.0 * sgn, -28.0, 0.0])
            J["wrist" + sd] = J["elbow" + sd] + fwd * (swing * 0.55 + 5.0) + np.array([2.5 * sgn, -24.5, 0.0])
        frames.append({"a": {"a0": pack_actor(J, fwd)}, "p": {}})
    return {
        "id": "T001",
        "title": "Heel, flat, ball, toe",
        "view": {"yaw": -22, "elev": 8, "x": 0, "z": 0, "zoom": 0.995},
        "frames": frames,
    }


def make_T006():
    frames = []
    B = base_skeleton()
    ang = math.radians(35.0)
    R = rot_y(ang)
    fwd = R @ np.array([0.0, 0.0, 1.0])
    for f in range(150):
        if f < 30:
            sit = 0.0
        elif f < 60:
            u = (f - 30) / 30.0
            sit = u * u * (3.0 - 2.0 * u)
        elif f < 100:
            sit = 1.0
        elif f < 130:
            u = (f - 100) / 30.0
            sit = 1.0 - u * u * (3.0 - 2.0 * u)
        else:
            sit = 0.0
        drop_y = -38.0 * sit
        back_z = -8.0 * sit
        J = {}
        for k, p in B.items():
            q = R @ p
            if not k.startswith(("ankle", "heel", "ball", "toe", "knee")):
                q = q + np.array([0.0, drop_y, 0.0]) + fwd * back_z
            J[k] = q
        for sd, sgn in (("L", 1.0), ("R", -1.0)):
            kn, ank = two_bone_leg(J["hip" + sd], J["ankle" + sd], 46.0, 42.9, fwd)
            J["knee" + sd] = kn
            J["elbow" + sd] = J["shoulder" + sd] + fwd * (10.0 * sit) + np.array([5.0 * sgn, -27.0, 0.0])
            J["wrist" + sd] = J["elbow" + sd] + fwd * (15.0 * sit + 4.0) + np.array([2.0 * sgn, -18.0 * (1.0 - 0.5 * sit), 0.0])
        chair_pos = (fwd * (-12.0)).tolist()
        frames.append({"a": {"a0": pack_actor(J, fwd)}, "p": {"chair": {"type": "chair", "pos": chair_pos}}})
    return {
        "id": "T006",
        "title": "Sitting down, standing up",
        "view": {"yaw": -22, "elev": 8, "x": 0, "z": 0, "zoom": 1.005},
        "frames": frames,
    }


def make_T080():
    frames = []
    B = base_skeleton()
    ang = math.radians(55.0)
    R = rot_y(ang)
    fwd = R @ np.array([0.0, 0.0, 1.0])
    right = R @ np.array([1.0, 0.0, 0.0])
    frame_pos = fwd * 32.0 + np.array([0.0, 138.0, 0.0])
    for f in range(230):
        if f < 35:
            rch = 0.0
        elif f < 65:
            u = (f - 35) / 30.0
            rch = u * u * (3.0 - 2.0 * u)
        elif f < 185:
            rch = 1.0
        elif f < 215:
            u = (f - 185) / 30.0
            rch = 1.0 - u * u * (3.0 - 2.0 * u)
        else:
            rch = 0.0
        J = {k: (R @ p).copy() for k, p in B.items()}
        for sd, sgn in (("L", 1.0), ("R", -1.0)):
            target_w = frame_pos + right * (12.0 * sgn)
            w0 = J["wrist" + sd]
            e0 = J["elbow" + sd]
            w_cur = (1.0 - rch) * w0 + rch * target_w
            e_cur = (1.0 - rch) * e0 + rch * (J["shoulder" + sd] + (target_w - J["shoulder" + sd]) * 0.52 + np.array([4.0 * sgn, -8.0, 0.0]))
            J["elbow" + sd] = e_cur
            J["wrist" + sd] = w_cur
        frames.append({
            "a": {"a0": pack_actor(J, fwd)},
            "p": {"frame": {"type": "box", "pos": [round(float(x), 2) for x in frame_pos], "size": [3, 32, 44]}},
        })
    return {
        "id": "T080",
        "title": "Hanging a picture",
        "view": {"yaw": -22, "elev": 8, "x": 0, "z": 0, "zoom": 1.007},
        "frames": frames,
    }


def make_T046():
    frames = []
    B = base_skeleton()
    R0 = rot_y(math.radians(68.0))
    R1 = rot_y(math.radians(-112.0))
    fwd0 = R0 @ np.array([0.0, 0.0, 1.0])
    fwd1 = R1 @ np.array([0.0, 0.0, 1.0])
    off0 = fwd0 * (-30.0)
    off1 = fwd0 * 30.0
    mid_pt = np.array([0.0, 112.0, 0.0])
    for f in range(180):
        if f < 45:
            rch = 0.0
        elif f < 75:
            u = (f - 45) / 30.0
            rch = u * u * (3.0 - 2.0 * u)
        elif f < 125:
            rch = 1.0
        elif f < 155:
            u = (f - 125) / 30.0
            rch = 1.0 - u * u * (3.0 - 2.0 * u)
        else:
            rch = 0.0
        J0 = {k: (R0 @ p) + off0 for k, p in B.items()}
        J1 = {k: (R1 @ p) + off1 for k, p in B.items()}
        J0["wristR"] = (1.0 - rch) * J0["wristR"] + rch * mid_pt
        J0["elbowR"] = (1.0 - rch) * J0["elbowR"] + rch * ((J0["shoulderR"] + mid_pt) * 0.5 + np.array([0.0, -8.0, 0.0]))
        J1["wristR"] = (1.0 - rch) * J1["wristR"] + rch * mid_pt
        J1["elbowR"] = (1.0 - rch) * J1["elbowR"] + rch * ((J1["shoulderR"] + mid_pt) * 0.5 + np.array([0.0, -8.0, 0.0]))
        letter_pos = J0["wristR"] if f < 90 else J1["wristR"]
        if 70 <= f <= 120:
            letter_pos = mid_pt
        frames.append({
            "a": {"a0": pack_actor(J0, fwd0), "a1": pack_actor(J1, fwd1)},
            "p": {"letter": {"type": "letter", "pos": [round(float(x), 2) for x in letter_pos]}},
        })
    return {
        "id": "T046",
        "title": "The letter changes hands",
        "view": {"yaw": -22, "elev": 8, "x": 0, "z": 0, "zoom": 1.005},
        "frames": frames,
    }


def make_T108():
    frames = []
    B = base_skeleton()
    ang = math.radians(48.0)
    R = rot_y(ang)
    fwd = R @ np.array([0.0, 0.0, 1.0])
    for f in range(260):
        if f < 30:
            crouch = 0.0
        elif f < 85:
            u = (f - 30) / 55.0
            crouch = u * u * (3.0 - 2.0 * u)
        elif f < 165:
            crouch = 1.0
        elif f < 225:
            u = (f - 165) / 60.0
            crouch = 1.0 - u * u * (3.0 - 2.0 * u)
        else:
            crouch = 0.0
        drop_y = -42.0 * crouch
        J = {}
        for k, p in B.items():
            q = R @ p
            if not k.startswith(("ankle", "heel", "ball", "toe", "knee")):
                q = q + np.array([0.0, drop_y, 0.0]) + fwd * (6.0 * crouch)
            J[k] = q
        for sd in ("L", "R"):
            kn, ank = two_bone_leg(J["hip" + sd], J["ankle" + sd], 46.0, 42.9, fwd)
            J["knee" + sd] = kn
        frames.append({"a": {"a0": pack_actor(J, fwd)}, "p": {}})
    return {
        "id": "T108",
        "title": "Stand after a fall",
        "view": {"yaw": -22, "elev": 8, "x": 0, "z": 0, "zoom": 0.928},
        "frames": frames,
    }


def main():
    vigs = {
        "T001": make_T001(),
        "T014": make_T014(),
        "T006": make_T006(),
        "T080": make_T080(),
        "T046": make_T046(),
        "T108": make_T108(),
    }
    for tid, data in vigs.items():
        out_path = os.path.join(BANK_DIR, f"{tid}.json")
        with open(out_path, "w") as f:
            json.dump(data, f)
        print(f"Wrote {out_path} ({len(data['frames'])} frames)")


if __name__ == "__main__":
    main()
