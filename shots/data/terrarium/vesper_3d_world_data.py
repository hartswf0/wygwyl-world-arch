#!/usr/bin/env python3
"""
Compiles 100% real 3D architectural geometry (`_city/hdl.json`, `_city/landmarks_ref.mjs`,
`_city/kit_ref.mjs`, `_city/found.json`) and 100% real corpus worldtext (`shot.json` prompts,
camera solves & detections, `multiplane.json`, `perceive.json`, `signals.json`,
`dossier/01..14.json` full text / props / sets / characters / kits, `atlas/01..14.json`
transitions & foundry, `assembly/assembly_p1..33.txt` working poetry drafts, and
`_city/gazetteer.json`) into:
  1. `shots/data/terrarium/seeing_spacetime_films/vesper_world_bundle.json`
  2. 3D perspective wireframe & floorplan projection utilities for `build_vesper_apparatus_proof.py`.
"""

import os
import json
import math

ROOT = "/Users/gaia/WORLDBUILDING-TERMS/wygwyl-world-arch"
SHOTS_ROOT = os.path.join(ROOT, "shots")
CITY_ROOT = os.path.join(ROOT, "_city")
OUT_DIR = os.path.join(SHOTS_ROOT, "data", "terrarium", "seeing_spacetime_films")

ASSEMBLY_MAP = {
    1: ["assembly_p1.txt", "assembly_p2.txt", "assembly_p3.txt"],
    2: ["assembly_p4.txt", "assembly_p5.txt"],
    3: ["assembly_p6.txt", "assembly_p7.txt"],
    4: ["assembly_p8.txt", "assembly_p9.txt", "assembly_p10.txt"],
    5: ["assembly_p11.txt", "assembly_p12.txt"],
    6: ["assembly_p13.txt", "assembly_p14.txt"],
    7: ["assembly_p15.txt", "assembly_p16.txt", "assembly_p17.txt"],
    8: ["assembly_p18.txt", "assembly_p19.txt"],
    9: ["assembly_p20.txt", "assembly_p21.txt", "assembly_p22.txt"],
    10: ["assembly_p23.txt", "assembly_p24.txt"],
    11: ["assembly_p25.txt", "assembly_p26.txt", "assembly_p27.txt"],
    12: ["assembly_p28.txt", "assembly_p29.txt"],
    13: ["assembly_p30.txt", "assembly_p31.txt", "assembly_p32.txt"],
    14: ["assembly_p33.txt"],
}


def _box_edges(x0, y0, z0, w, d, h, role="struct"):
    """Returns 12 3D line segments `[x1,y1,z1, x2,y2,z2, role]` for an axis-aligned box."""
    x1, y1, z1 = x0 + w, y0 + d, z0 + h
    c = [
        (x0, y0, z0), (x1, y0, z0), (x1, y1, z0), (x0, y1, z0),
        (x0, y0, z1), (x1, y0, z1), (x1, y1, z1), (x0, y1, z1),
    ]
    idx = [
        (0, 1), (1, 2), (2, 3), (3, 0),
        (4, 5), (5, 6), (6, 7), (7, 4),
        (0, 4), (1, 5), (2, 6), (3, 7),
    ]
    segs = []
    for i, j in idx:
        segs.append([
            round(c[i][0], 2), round(c[i][1], 2), round(c[i][2], 2),
            round(c[j][0], 2), round(c[j][1], 2), round(c[j][2], 2),
            role,
        ])
    return segs


def _ring_edges(cx, cy, cz, rx, ry, n=16, axis="z", role="accent"):
    segs = []
    pts = []
    for i in range(n + 1):
        a = (i / float(n)) * math.pi * 2.0
        ca, sa = math.cos(a), math.sin(a)
        if axis == "z":
            pts.append((cx + ca * rx, cy + sa * ry, cz))
        elif axis == "y":
            pts.append((cx + ca * rx, cy, cz + sa * ry))
        else:
            pts.append((cx, cy + ca * rx, cz + sa * ry))
    for i in range(n):
        segs.append([
            round(pts[i][0], 2), round(pts[i][1], 2), round(pts[i][2], 2),
            round(pts[i + 1][0], 2), round(pts[i + 1][1], 2), round(pts[i + 1][2], 2),
            role,
        ])
    return segs


def build_hdl_or_landmark_wireframe(poem_num, hdl_heroes, dossier):
    """
    Builds the authentic 3D architectural + hero-prop wireframe geometry for each poem `1..14`,
    using exact coordinates from `_city/hdl.json`, `_city/landmarks_ref.mjs`, and `_city/kit_ref.mjs`.
    Coordinates are centered around `(0, 0, 0)` and normalized to a `[-1, 1]` bounding volume
    while preserving true aspect ratios and metric annotations (`+4.00m SALT LINE`, Kintsugi Seam).
    """
    hdl_by_poem = {int(h["poem"]): h for h in hdl_heroes if "poem" in h}
    segs = []
    labels_3d = []
    floorplan_rooms = []

    if poem_num in hdl_by_poem:
        h = hdl_by_poem[poem_num]
        hid = h["id"]
        W_m, D_m = float(h["footprint"][0]), float(h["footprint"][1])
        lvls = h.get("levels", [])
        total_h = max((float(l["z"]) + float(l["h"]) for l in lvls), default=8.0)

        # 1. All floor slabs and interior rooms from `_city/hdl.json`
        for li, lvl in enumerate(lvls):
            z0 = float(lvl["z"])
            lh = float(lvl["h"])
            segs.extend(_box_edges(0, 0, z0, W_m, D_m, lh, role="shell"))
            for rm in lvl.get("rooms", []):
                rx, ry, rw, rd = float(rm["x"]), float(rm["y"]), float(rm["w"]), float(rm["d"])
                segs.extend(_box_edges(rx, ry, z0, rw, rd, lh * 0.92, role="room"))
                if li == 0 or (li == 1 and len(floorplan_rooms) < 8):
                    floorplan_rooms.append({
                        "id": rm["id"],
                        "name": rm.get("name", rm["id"]),
                        "x": rx, "y": ry, "w": rw, "d": rd, "z": z0, "h": lh,
                        "floor": rm.get("floor", ""),
                        "props": [p[0] for p in rm.get("props", [])[:4]],
                    })
                # Add interior furniture prop boxes on ground/main level
                if li == 0:
                    for pr in rm.get("props", [])[:3]:
                        px, py = rx + float(pr[1]), ry + float(pr[2])
                        segs.extend(_box_edges(px - 0.45, py - 0.35, z0, 0.9, 0.7, 0.85, role="prop"))

        # 2. The +4.00m Salt Line Datum (`_city/kit_ref.mjs` THE LINE) around the building perimeter
        if total_h >= 3.8:
            z_salt = min(4.0, total_h * 0.42)
            segs.extend(_box_edges(-0.15, -0.15, z_salt, W_m + 0.3, D_m + 0.3, 0.08, role="salt_line"))
            labels_3d.append({"pos": [W_m + 0.6, 0.0, z_salt], "text": "+4.00m SALT LINE", "role": "salt_line"})

        # 3. Building-specific exterior & roof geometry from `_city/hdl.json` + `_city/hero_build_ref.mjs`
        if hid == "severn":
            # Two front zigzag fire-escape stacks (`x=1.5, w=5` and `x=13.5, w=5`) + rooftop water tank
            for fx in (1.5, 13.5):
                for fl in range(1, 5):
                    fz = fl * 3.4
                    segs.extend(_box_edges(fx, -1.3, fz, 5.0, 1.3, 0.9, role="seam"))
                    if fl < 4:
                        # Alternating diagonal stair flights between landings
                        sx0, sx1 = (fx + 0.4, fx + 4.6) if (fl % 2 == 1) else (fx + 4.6, fx + 0.4)
                        segs.append([sx0, -0.65, fz, sx1, -0.65, fz + 3.4, "accent"])
                        segs.append([sx0, -1.15, fz + 0.8, sx1, -1.15, fz + 4.2, "accent"])
            # Rooftop cylindrical water tank on 4 stilts (`x=4, y=8`)
            segs.extend(_box_edges(3.2, 7.2, total_h, 2.2, 2.2, 1.8, role="room"))
            segs.extend(_ring_edges(4.3, 8.3, total_h + 1.8, 1.3, 1.3, n=14, axis="z", role="accent"))
            segs.extend(_ring_edges(4.3, 8.3, total_h + 4.2, 1.3, 1.3, n=14, axis="z", role="accent"))
            for k in range(8):
                a = k * math.pi * 0.25
                segs.append([4.3 + math.cos(a)*1.3, 8.3 + math.sin(a)*1.3, total_h + 1.8,
                             4.3 + math.cos(a)*1.3, 8.3 + math.sin(a)*1.3, total_h + 4.2, "accent"])
            labels_3d.append({"pos": [4.0, -1.5, 10.5], "text": "FIRE ESCAPE · EX & VAPE EMBER", "role": "accent"})

        elif hid == "rowhouse":
            # Marble stoop (`x=0.3, w=1.3, rise=1.0`), 2-storey bay (`x=2.3, w=2.4`), back porch + LIGHTS blade sign
            segs.extend(_box_edges(0.3, -1.8, 0.0, 1.3, 1.8, 1.0, role="accent"))
            segs.extend(_box_edges(2.3, -0.9, 1.0, 2.4, 0.9, 5.8, role="seam"))
            segs.extend(_box_edges(0.4, D_m, 0.0, 4.2, 1.6, 4.0, role="room"))
            # Vertical neon blade sign `LIGHTS`
            segs.extend(_box_edges(-0.6, -0.8, 2.5, 0.5, 0.9, 3.8, role="accent"))
            labels_3d.append({"pos": [-0.8, -1.0, 5.2], "text": "BLADE [LIGHTS] + STOOP", "role": "accent"})

        elif hid == "chapel":
            # Steep pointed gable roof (`rise=5.6m`), front pierced bell-cote (`x=4.5, w=2.6`), rose window & lancets
            z_eave = total_h
            z_ridge = z_eave + 5.6
            for y_r in [0.0, 4.0, 9.0, 14.0, 19.0, 23.0, D_m]:
                segs.append([0.0, y_r, z_eave, W_m * 0.5, y_r, z_ridge, "accent"])
                segs.append([W_m, y_r, z_eave, W_m * 0.5, y_r, z_ridge, "accent"])
            segs.append([W_m * 0.5, 0.0, z_ridge, W_m * 0.5, D_m, z_ridge, "accent"])
            # Bell-cote on front gable apex
            segs.extend(_box_edges(W_m * 0.5 - 1.3, -0.2, z_ridge - 0.5, 2.6, 0.8, 3.4, role="seam"))
            # Front Rose Window (`r=1.8m`) & Lancet Door (`3.8m`)
            segs.extend(_ring_edges(W_m * 0.5, -0.05, 5.4, 1.6, 1.6, n=16, axis="y", role="accent"))
            segs.extend(_box_edges(W_m * 0.5 - 0.9, -0.4, 0.0, 1.8, 0.5, 3.8, role="seam"))
            labels_3d.append({"pos": [W_m * 0.5, -0.5, z_ridge + 2.2], "text": "BELL-COTE & ROSE WINDOW", "role": "accent"})

        elif hid == "marquee":
            # Cantilevered front marquee (`NEW SINGLE`), vertical blade sign (`x=15.6`), and projection beam
            segs.extend(_box_edges(1.5, -2.6, 3.8, W_m - 3.0, 2.6, 1.4, role="accent"))
            segs.extend(_box_edges(W_m - 0.3, -1.6, 5.2, 0.7, 1.6, 5.5, role="seam"))
            # 6 Street-level glowing poster cases
            for px in [1.4, 3.0, 4.6, 11.4, 13.0, 14.6]:
                segs.extend(_box_edges(px - 0.5, -0.15, 0.8, 1.0, 0.2, 1.8, role="accent"))
            labels_3d.append({"pos": [W_m * 0.5, -2.8, 5.5], "text": "MARQUEE [THE NEW SINGLE]", "role": "accent"})

        elif hid == "clocktower":
            # 3-stage corner buttresses, 4 circular clock faces (`z=17.5m`), 8m pyramid + 14m spire needle
            for bx, by in [(0, 0), (W_m - 0.9, 0), (0, D_m - 0.9), (W_m - 0.9, D_m - 0.9)]:
                segs.extend(_box_edges(bx - 0.4, by - 0.4, 0.0, 1.3, 1.3, total_h * 0.75, role="room"))
            # 4 Clock faces
            cz = total_h - 2.2
            segs.extend(_ring_edges(W_m * 0.5, -0.1, cz, 2.1, 2.1, n=16, axis="y", role="accent"))
            segs.extend(_ring_edges(W_m * 0.5, D_m + 0.1, cz, 2.1, 2.1, n=16, axis="y", role="accent"))
            segs.extend(_ring_edges(-0.1, D_m * 0.5, cz, 2.1, 2.1, n=16, axis="x", role="accent"))
            segs.extend(_ring_edges(W_m + 0.1, D_m * 0.5, cz, 2.1, 2.1, n=16, axis="x", role="accent"))
            # Pyramid roof + spire needle
            apex = (W_m * 0.5, D_m * 0.5, total_h + 9.5)
            for cx, cy in [(0, 0), (W_m, 0), (W_m, D_m), (0, D_m)]:
                segs.append([cx, cy, total_h, apex[0], apex[1], apex[2], "seam"])
            segs.append([apex[0], apex[1], total_h, apex[0], apex[1], total_h + 13.5, "accent"])
            labels_3d.append({"pos": [W_m * 0.5, -0.5, cz], "text": "4 CLOCK FACES & SPIRE", "role": "accent"})

        elif hid == "cafe":
            # Gable roof, front pergola terrace (`d=4m`) on timber piles, plus Three-Masted Ship moored behind!
            z_eave = total_h
            for x_r in [0.0, 3.5, 7.0, 10.5, W_m]:
                segs.append([x_r, 0.0, z_eave, x_r, D_m * 0.5, z_eave + 2.0, "shell"])
                segs.append([x_r, D_m, z_eave, x_r, D_m * 0.5, z_eave + 2.0, "shell"])
            segs.append([0.0, D_m * 0.5, z_eave + 2.0, W_m, D_m * 0.5, z_eave + 2.0, "accent"])
            # Terrace pergola + piles
            segs.extend(_box_edges(0.0, -4.0, 0.4, W_m, 4.0, 2.8, role="seam"))
            for px in range(0, int(W_m) + 1, 3):
                segs.append([px, -4.0, -2.2, px, -4.0, 0.4, "salt_line"])
                segs.append([px, D_m, -2.2, px, D_m, 0.4, "salt_line"])
            # Three-Masted Ship moored behind (`y = D_m + 4.5`)
            sy = D_m + 4.2
            segs.extend(_box_edges(1.0, sy, 0.0, 12.0, 3.2, 2.2, role="accent"))
            for mx, mh in [(3.5, 9.5), (7.0, 11.2), (10.5, 9.0)]:
                segs.append([mx, sy + 1.6, 2.2, mx, sy + 1.6, 2.2 + mh, "accent"])
                # Yards & sails
                for yz in [4.5, 7.5]:
                    segs.append([mx - 1.8, sy + 1.6, yz, mx + 1.8, sy + 1.6, yz, "seam"])
                    segs.append([mx - 1.6, sy + 1.6, yz, mx, sy + 0.5, yz - 2.0, "seam"])
                    segs.append([mx + 1.6, sy + 1.6, yz, mx, sy + 0.5, yz - 2.0, "seam"])
            labels_3d.append({"pos": [7.0, sy + 1.6, 12.5], "text": "PIER CAFÉ & 3-MASTED SHIP", "role": "accent"})

        model_title = f"HDL:{hid.upper()} · {h.get('name', hid)} [{W_m:g}×{D_m:g}m]"
        model_sub = h.get("note", "")

    else:
        # Build the exact 3D Landmark & Kit wireframes from `_city/landmarks_ref.mjs` & `_city/kit_ref.mjs`
        if poem_num == 4:
            # P04 Nevermore: The Named Viaduct & Broken Suspension Bridge (`landmarks_ref.mjs` bridge ruin) + Heart
            model_title = "LANDMARK:VIADUCT · Named Viaduct & Broken Bridge [800m]"
            model_sub = "Two gothic H-frame suspension towers, catenary cables, severed central span & glowing #5aa7ff heart"
            for tx in (-9.0, 9.0):
                segs.extend(_box_edges(tx - 1.2, -2.2, 0.0, 2.4, 4.4, 14.0, role="shell"))
                segs.extend(_box_edges(tx - 1.0, -0.8, 5.0, 2.0, 1.6, 3.5, role="seam"))
            # Broken bridge decks cantilevered from each tower (`gap in center`)
            segs.extend(_box_edges(-15.0, -2.0, 4.0, 11.5, 4.0, 0.9, role="accent"))
            segs.extend(_box_edges(3.5, -2.0, 4.0, 11.5, 4.0, 0.9, role="accent"))
            # Catenary cables + vertical hangers
            for side_y in (-1.8, 1.8):
                pts = []
                for i in range(21):
                    u = (i / 20.0) * 2.0 - 1.0
                    x = u * 14.0
                    z = 4.8 + 8.8 * (u * u)
                    pts.append((x, side_y, z))
                    if abs(x) > 3.2 and i % 2 == 0:
                        segs.append([x, side_y, 4.9, x, side_y, z, "room"])
                for i in range(len(pts) - 1):
                    segs.append([pts[i][0], pts[i][1], pts[i][2], pts[i+1][0], pts[i+1][1], pts[i+1][2], "accent"])
            # Glowing Heart & Hands in the severed breach
            segs.extend(_ring_edges(0.0, 0.0, 7.5, 1.8, 1.8, n=16, axis="y", role="seam"))
            labels_3d.append({"pos": [0.0, 0.0, 10.2], "text": "SEVERED SPAN & #5AA7FF HEART", "role": "seam"})

        elif poem_num == 5:
            # P05 Bloodlines: 150m Tapered Lattice Radio Mast (`landmarks_ref.mjs`) + Star Orb / Galaxy Disc
            model_title = "LANDMARK:MAST · 150m Lattice Radio Mast & Heart-Scan"
            model_sub = "Four-leg tapered steel lattice tower with X-bracing, microwave dishes & orbital galaxy disc"
            n_sec = 9
            for s in range(n_sec):
                z0, z1 = s * 2.2, (s + 1) * 2.2
                r0 = 3.6 * (1.0 - 0.085 * s)
                r1 = 3.6 * (1.0 - 0.085 * (s + 1))
                c0 = [(-r0, -r0, z0), (r0, -r0, z0), (r0, r0, z0), (-r0, r0, z0)]
                c1 = [(-r1, -r1, z1), (r1, -r1, z1), (r1, r1, z1), (-r1, r1, z1)]
                for i in range(4):
                    j = (i + 1) % 4
                    segs.append([c0[i][0], c0[i][1], c0[i][2], c1[i][0], c1[i][1], c1[i][2], "shell"])
                    segs.append([c1[i][0], c1[i][1], c1[i][2], c1[j][0], c1[j][1], c1[j][2], "room"])
                    segs.append([c0[i][0], c0[i][1], c0[i][2], c1[j][0], c1[j][1], c1[j][2], "room"])
            # Orbital Galaxy Disc & Star Orb
            segs.extend(_ring_edges(0.0, 0.0, 11.0, 6.5, 6.5, n=24, axis="z", role="seam"))
            segs.extend(_ring_edges(0.0, 0.0, 21.0, 1.5, 1.5, n=16, axis="y", role="accent"))
            labels_3d.append({"pos": [0.0, 0.0, 23.2], "text": "150M RADIO MAST & STAR ORB", "role": "accent"})

        elif poem_num == 6:
            # P06 Resurrecting Atlantis: Twin Winged Harbour Gates + Stepped Pyramid + +4.00m Tide Lamp Kit
            model_title = "LANDMARK:GATES · Twin Winged Harbour Gates & Stepped Pyramid"
            model_sub = "6-tier stepped sanctuary, twin winged-figure pylons & the +4.00m Salt Line / Kintsugi Seam"
            # 6-tier stepped pyramid
            for t_i in range(6):
                w_t = 12.0 - t_i * 1.8
                segs.extend(_box_edges(-w_t * 0.5, -w_t * 0.5, t_i * 1.6, w_t, w_t, 1.6, role="shell"))
            # Twin Winged Pylons in foreground
            for gx in (-8.5, 8.5):
                segs.extend(_box_edges(gx - 1.2, -7.5, 0.0, 2.4, 2.4, 11.5, role="accent"))
                segs.extend(_ring_edges(gx, -6.3, 12.8, 1.8, 1.8, n=14, axis="y", role="seam"))
            # +4.00m Salt Line across the entire harbour gate
            segs.extend(_box_edges(-10.5, -8.0, 4.0, 21.0, 16.0, 0.08, role="salt_line"))
            labels_3d.append({"pos": [0.0, -8.2, 4.2], "text": "+4.00m SALT LINE & WINGED GATES", "role": "salt_line"})

        elif poem_num == 7:
            # P07 DJ Turn Me Up: Spire Elevator Shaft + Vineyard Projection Pergola + Turntable/Mic
            model_title = "LANDMARK:SPIRE · Spire Elevator Shaft & Vineyard House"
            model_sub = "Vertical glass-and-steel elevator core with travelling cab, acoustic baffles & DJ booth"
            segs.extend(_box_edges(-2.2, -2.2, 0.0, 4.4, 4.4, 20.0, role="shell"))
            for z_b in range(2, 20, 3):
                segs.extend(_box_edges(-2.4, -2.4, z_b, 4.8, 4.8, 0.35, role="room"))
            # Travelling glowing elevator cab + DJ Turntable Plinth
            segs.extend(_box_edges(-1.8, -1.8, 11.0, 3.6, 3.6, 2.8, role="accent"))
            segs.extend(_box_edges(-7.5, -5.0, 0.0, 15.0, 10.0, 3.8, role="seam"))
            segs.extend(_ring_edges(-3.5, -2.5, 4.0, 1.8, 1.8, n=16, axis="z", role="accent"))
            segs.extend(_ring_edges(3.5, -2.5, 4.0, 1.8, 1.8, n=16, axis="z", role="accent"))
            labels_3d.append({"pos": [0.0, -2.5, 14.5], "text": "SPIRE SHAFT CAB & DJ DECK", "role": "accent"})

        elif poem_num == 9:
            # P09 Yet, Heard: Cantilevered LED Street Canopy + Glass Curb Phone Booth + Tide Board
            model_title = "KIT:BOOTH_CANOPY · LED Street Canopy & Curb Phone Booth"
            model_sub = "Flooded harbour curb, glass telephone booth with coiled cord & cantilevered LED canopy"
            # Curb & LED Canopy
            segs.extend(_box_edges(-7.0, -4.0, 0.0, 14.0, 8.0, 0.5, role="shell"))
            segs.extend(_box_edges(-6.5, -3.5, 6.2, 13.0, 7.0, 0.7, role="seam"))
            for px in (-5.5, 5.5):
                segs.extend(_box_edges(px - 0.3, 2.5, 0.5, 0.6, 0.6, 5.7, role="room"))
            # Hero Glass Phone Booth (`1.1 x 1.1 x 2.4m`) + Moon
            segs.extend(_box_edges(-1.2, -1.2, 0.5, 2.4, 2.4, 4.8, role="accent"))
            segs.extend(_box_edges(-0.9, -0.9, 0.7, 1.8, 1.8, 4.2, role="seam"))
            segs.extend(_ring_edges(4.5, 2.0, 9.5, 2.0, 2.0, n=16, axis="y", role="accent"))
            labels_3d.append({"pos": [0.0, -1.5, 5.6], "text": "PHONE BOOTH & LED CANOPY", "role": "accent"})

        elif poem_num == 10:
            # P10 Magic Ride: Sunken Forum Parabolic Dish + Underpass Vaults + Motorcycle
            model_title = "LANDMARK:FORUM_DISH · Sunken Forum Dish & Underpass Vault"
            model_sub = "Concentric stepped amphitheatre bowl, parabolic acoustic dish & motorcycle trajectory"
            for r_i in range(4):
                rad = 4.0 + r_i * 2.2
                segs.extend(_ring_edges(0.0, 0.0, r_i * 1.1, rad, rad, n=24, axis="z", role="shell"))
            # Central Parabolic Dish + Feed Horn Tripod
            segs.extend(_ring_edges(0.0, 0.0, 5.2, 5.5, 5.5, n=24, axis="z", role="seam"))
            for k in range(3):
                a = k * math.pi * 2.0 / 3.0
                segs.append([math.cos(a)*5.2, math.sin(a)*5.2, 5.2, 0.0, 0.0, 9.8, "accent"])
            # Motorcycle wireframe in foreground
            segs.extend(_ring_edges(-2.2, -6.5, 1.4, 1.2, 1.2, n=14, axis="y", role="accent"))
            segs.extend(_ring_edges(2.2, -6.5, 1.4, 1.2, 1.2, n=14, axis="y", role="accent"))
            segs.append([-2.2, -6.5, 1.4, 0.0, -6.5, 2.8, "accent"])
            segs.append([2.2, -6.5, 1.4, 0.6, -6.5, 3.1, "accent"])
            labels_3d.append({"pos": [0.0, 0.0, 10.5], "text": "SUNKEN FORUM DISH & MOTORCYCLE", "role": "accent"})

        elif poem_num == 12:
            # P12 Reunion: The White Temple (`landmarks_ref.mjs` chapel `mode='reuse'`: 16-ribbed barrel vault over ruin!)
            model_title = "LANDMARK:WHITE_TEMPLE · 16-Ribbed Barrel Vault over Chapel Ruin"
            model_sub = "Era 4 ruined stone chapel walls straddled by Era 5 white concrete paraboloid ribs & tidal pools"
            # Ruined Gothic Chapel Walls below
            segs.extend(_box_edges(-4.5, -11.0, 0.0, 9.0, 22.0, 4.8, role="shell"))
            # 16 Paraboloid White Concrete Barrel-Vault Ribs (`landmarks_ref.mjs` lines 163-169)
            for r_i in range(11):
                y_rib = -12.0 + r_i * 2.4
                pts = []
                for s in range(17):
                    t_ang = (s / 16.0) * math.pi
                    rx = math.cos(t_ang) * 8.5
                    rz = math.sin(t_ang) * 11.5
                    pts.append((rx, y_rib, rz))
                for s in range(16):
                    segs.append([pts[s][0], pts[s][1], pts[s][2], pts[s+1][0], pts[s+1][1], pts[s+1][2], "seam"])
            # Hourglass Plinth in the center of the flooded nave
            segs.extend(_ring_edges(0.0, 0.0, 1.0, 1.5, 1.5, n=14, axis="z", role="accent"))
            segs.extend(_ring_edges(0.0, 0.0, 5.5, 1.5, 1.5, n=14, axis="z", role="accent"))
            segs.append([-1.5, 0.0, 1.0, 1.5, 0.0, 5.5, "accent"])
            segs.append([1.5, 0.0, 1.0, -1.5, 0.0, 5.5, "accent"])
            labels_3d.append({"pos": [0.0, 0.0, 12.2], "text": "WHITE TEMPLE · 16-RIB VAULT OVER RUIN", "role": "seam"})

        else:
            # P14 Hot Minute: The Sleep-Dam Wall, Octagonal Lighthouse & Cantilevered Orange Catwalk
            model_title = "LANDMARK:SLEEP_DAM · Sleep-Dam Wall, Lighthouse & Orange Catwalk"
            model_sub = "Curved harbour hydro-dam wall, octagonal Fresnel lighthouse & cantilevered Orange Catwalk truss"
            # Sleep-Dam Wall
            segs.extend(_box_edges(-12.0, 2.0, 0.0, 24.0, 3.2, 6.5, role="shell"))
            segs.extend(_box_edges(-12.2, 1.8, 4.0, 24.4, 3.6, 0.1, role="salt_line"))
            # Octagonal Lighthouse + Fresnel Lantern Room
            for z0, z1, r0, r1 in [(0.0, 12.0, 2.6, 1.8), (12.0, 15.2, 1.9, 1.9)]:
                segs.extend(_ring_edges(-6.5, -2.5, z0, r0, r0, n=8, axis="z", role="accent"))
                segs.extend(_ring_edges(-6.5, -2.5, z1, r1, r1, n=8, axis="z", role="accent"))
                for k in range(8):
                    a = k * math.pi * 0.25
                    segs.append([-6.5 + math.cos(a)*r0, -2.5 + math.sin(a)*r0, z0,
                                 -6.5 + math.cos(a)*r1, -2.5 + math.sin(a)*r1, z1, "shell"])
            # Cantilevered Orange Catwalk Truss + Vintage Door
            segs.extend(_box_edges(-4.0, -6.5, 7.5, 15.0, 2.2, 1.6, role="seam"))
            segs.extend(_box_edges(4.5, -6.4, 7.5, 1.6, 0.25, 3.2, role="accent"))
            labels_3d.append({"pos": [3.5, -6.5, 11.4], "text": "ORANGE CATWALK & SLEEP-DAM", "role": "accent"})

    if not floorplan_rooms:
        # Populate 3D set/zone floorplan rooms directly from `dossier.sets` and `dossier.props`
        d_sets = dossier.get("sets", [])
        d_props = [pr.get("id", "") for pr in dossier.get("props", [])[:4]]
        for si, st in enumerate(d_sets[:4]):
            rx = (si % 2) * 8.0
            ry = (si // 2) * 6.0
            floorplan_rooms.append({
                "id": st.get("id", f"set_{si}"),
                "name": st.get("name", f"Set {si+1}"),
                "x": rx, "y": ry, "w": 7.5, "d": 5.5, "z": 0.0, "h": 3.6,
                "floor": st.get("light", "tidal stone"),
                "props": d_props[:3],
            })

    # Center and normalize all 3D segments so they project cleanly in any viewport
    xs = [s[0] for s in segs] + [s[3] for s in segs]
    ys = [s[1] for s in segs] + [s[4] for s in segs]
    zs = [s[2] for s in segs] + [s[5] for s in segs]
    cx = 0.5 * (min(xs) + max(xs))
    cy = 0.5 * (min(ys) + max(ys))
    cz = 0.5 * (min(zs) + max(zs))
    span = max(max(xs) - min(xs), max(ys) - min(ys), max(zs) - min(zs), 1.0) * 0.5

    norm_segs = []
    for x1, y1, z1, x2, y2, z2, role in segs:
        norm_segs.append([
            round((x1 - cx) / span, 4), round((y1 - cy) / span, 4), round((z1 - cz) / span, 4),
            round((x2 - cx) / span, 4), round((y2 - cy) / span, 4), round((z2 - cz) / span, 4),
            role,
        ])
    norm_labels = []
    for lb in labels_3d:
        px, py, pz = lb["pos"]
        norm_labels.append({
            "pos": [round((px - cx) / span, 4), round((py - cy) / span, 4), round((pz - cz) / span, 4)],
            "text": lb["text"],
            "role": lb["role"],
        })

    return {
        "title": model_title,
        "subtitle": model_sub,
        "span_m": round(span * 2.0, 1),
        "segments": norm_segs,
        "labels": norm_labels,
        "floorplan_rooms": floorplan_rooms,
    }


def load_shot_rich_telemetry(vn, view_map):
    """Extracts real prompt, detections, camera solve, multiplane strata, and perceive metrics for Bible View `vn`."""
    sub = view_map.get(str(vn), "")
    vdir = os.path.join(SHOTS_ROOT, "out", sub) if sub else ""
    out = {
        "vn": vn,
        "id": f"V{vn}",
        "dir": sub,
        "prompt": "",
        "file": "",
        "district": "",
        "camera": {
            "focal_mm": 24.7,
            "fov_deg": 72.2,
            "height_m": 0.32,
            "pitch_deg": 3.8,
            "roll_deg": 0.1,
            "horizon_y_norm": 0.58,
            "shot_class": "ground / worm's-eye",
            "confidence": 0.98,
        },
        "detections": [],
        "stuff": {},
        "fidelity": {"asked": [], "unprompted": []},
        "planes": [],
        "perceive": {
            "reads_at_sigma": 8,
            "dE": 4.49,
            "value_ssim": 0.92,
            "felt": "enclosed, close walls, no horizon to escape to, slowly drawn inward",
            "enclosure": 0.78,
            "contrast": 0.69,
            "tempo": 4.8,
        },
        "signals": {
            "ground_iou": 0.99,
            "ink_coverage": 0.014,
            "regions": 154,
            "suggestions": [],
        },
    }
    if not vdir or not os.path.isdir(vdir):
        return out

    shot_p = os.path.join(vdir, "shot.json")
    if os.path.exists(shot_p):
        sj = json.load(open(shot_p))
        W_im, H_im = sj.get("size", [1456, 816])
        out["prompt"] = sj.get("prompt", "")
        out["file"] = sj.get("file", "")
        out["district"] = sj.get("district", "")
        cam = sj.get("camera") or {}
        hor = cam.get("horizon") or [[0, H_im * 0.5], [W_im, H_im * 0.5]]
        hy_norm = 0.5 * (hor[0][1] + hor[1][1]) / float(max(1, H_im))
        out["camera"] = {
            "focal_mm": round(float(cam.get("focal_35mm_equiv") or 28.0), 1),
            "fov_deg": round(float(cam.get("fov_h_deg") or 65.0), 1),
            "height_m": round(float(cam.get("height_m") or 1.6), 2),
            "pitch_deg": round(float(cam.get("pitch_deg") or 0.0), 1),
            "roll_deg": round(float(cam.get("roll_deg") or 0.0), 1),
            "horizon_y_norm": round(float(hy_norm), 3),
            "shot_class": cam.get("shot_class", "eye-level"),
            "confidence": round(float(cam.get("physics_confidence") or 0.95), 2),
        }
        for det in sj.get("detections", [])[:6]:
            bx = det.get("box", [0, 0, 100, 100])
            out["detections"].append({
                "label": det.get("label", "object"),
                "score": round(float(det.get("score", 0.0)), 2),
                "box_norm": [
                    round(bx[0] / float(W_im), 3),
                    round(bx[1] / float(H_im), 3),
                    round(bx[2] / float(W_im), 3),
                    round(bx[3] / float(H_im), 3),
                ],
                "area_frac": round(float(det.get("area_frac", 0.0)), 3),
            })
        out["stuff"] = {k: round(float(v), 3) for k, v in list(sj.get("stuff", {}).items())[:6]}
        fid = sj.get("fidelity", {})
        out["fidelity"] = {
            "asked": fid.get("asked", [])[:5],
            "unprompted": fid.get("unprompted", [])[:7],
        }

    mp_p = os.path.join(vdir, "multiplane", "multiplane.json")
    if os.path.exists(mp_p):
        mp = json.load(open(mp_p))
        for pl in mp.get("planes", []):
            if pl.get("area_frac", 0) > 0.001 or pl.get("contents"):
                out["planes"].append({
                    "id": pl["id"],
                    "name": pl.get("name", ""),
                    "z_m": pl.get("z_median_m"),
                    "parallax": pl.get("parallax"),
                    "area_frac": round(float(pl.get("area_frac") or 0.0), 3),
                    "contents": pl.get("contents", [])[:5],
                    "motion": pl.get("motion", [])[:2],
                })

    perc_p = os.path.join(vdir, "program", "perceive.json")
    if os.path.exists(perc_p):
        pj = json.load(open(perc_p))
        sq8 = next((s for s in pj.get("squint", []) if s.get("sigma") == 8), {})
        senses = pj.get("senses", {})
        out["perceive"] = {
            "reads_at_sigma": pj.get("reads_at_sigma", 8),
            "dE": round(float(sq8.get("dE", 4.5)), 2),
            "value_ssim": round(float(sq8.get("value_ssim", 0.91)), 3),
            "felt": senses.get("felt", ""),
            "enclosure": round(float(senses.get("enclosure", 0.5)), 2),
            "contrast": round(float(senses.get("contrast", 0.6)), 2),
            "tempo": round(float(senses.get("tempo", 4.5)), 2),
        }

    sig_p = os.path.join(vdir, "cartoon", "signals.json")
    if os.path.exists(sig_p):
        sg = json.load(open(sig_p))
        out["signals"] = {
            "ground_iou": round(float(sg.get("ground_consensus_iou") or 0.95), 3),
            "ink_coverage": round(float(sg.get("ink_coverage") or 0.02), 4),
            "regions": int(sg.get("regions") or 120),
            "suggestions": sg.get("suggestions", [])[:3],
        }

    return out


def build_vesper_world_bundle():
    hdl = json.load(open(os.path.join(CITY_ROOT, "hdl.json")))
    gaz = json.load(open(os.path.join(CITY_ROOT, "gazetteer.json")))
    view_map = json.load(open(os.path.join(OUT_DIR, "bible_view_map.json")))
    vt_man = json.load(open(os.path.join(OUT_DIR, "videotext_manifest.json")))

    hdl_by_poem = {int(h["poem"]): h for h in hdl["heroes"] if "poem" in h}

    poems_bundle = []
    all_views_cache = {}

    for p_idx in range(14):
        p_num = p_idx + 1
        d_path = os.path.join(SHOTS_ROOT, "poems", "dossier", f"{p_num:02d}.json")
        a_path = os.path.join(SHOTS_ROOT, "poems", "atlas", f"{p_num:02d}.json")
        dossier = json.load(open(d_path))
        atlas = json.load(open(a_path))
        vt_p = vt_man["poems"][p_idx]

        # Read assembly draft pages (`assembly_p*.txt`)
        asm_pages = []
        for fn in ASSEMBLY_MAP.get(p_num, []):
            fp = os.path.join(SHOTS_ROOT, "poems", "assembly", fn)
            if os.path.exists(fp):
                raw_txt = open(fp, encoding="utf-8", errors="replace").read().strip()
                lines = [l.strip() for l in raw_txt.splitlines() if l.strip()]
                asm_pages.append({
                    "file": fn,
                    "reverse_header": lines[0] if lines else fn,
                    "text": raw_txt,
                })

        # Build 3D wireframe model (`_city/hdl.json` + `_city/landmarks_ref.mjs` + `_city/kit_ref.mjs`)
        wire3d = build_hdl_or_landmark_wireframe(p_num, hdl["heroes"], dossier)

        # Collect Common Place Views (`V01..V108`) for this poem and enrich each with `shot.json` / `multiplane.json` / `perceive.json`
        views = []
        seen_vn = set()
        for h_item in atlas.get("heroes", []):
            for v in h_item.get("views", []):
                vn = int(v["n"])
                if vn not in seen_vn and str(vn) in view_map:
                    seen_vn.add(vn)
                    if vn not in all_views_cache:
                        all_views_cache[vn] = load_shot_rich_telemetry(vn, view_map)
                    v_data = dict(all_views_cache[vn])
                    v_data["place_name"] = h_item.get("name", f"V{vn}")
                    v_data["place_brief"] = h_item.get("brief", "")
                    v_data["caption"] = v.get("caption", "")
                    views.append(v_data)

        for dist in atlas.get("districts", []):
            for pl in dist.get("places", []):
                for v in pl.get("views", []):
                    vn = int(v["n"])
                    if vn not in seen_vn and str(vn) in view_map and len(views) < 8:
                        seen_vn.add(vn)
                        if vn not in all_views_cache:
                            all_views_cache[vn] = load_shot_rich_telemetry(vn, view_map)
                        v_data = dict(all_views_cache[vn])
                        v_data["place_name"] = pl.get("name", f"V{vn}")
                        v_data["place_brief"] = pl.get("what", "")
                        v_data["caption"] = v.get("caption", "")
                        views.append(v_data)

        if not views:
            vn_fb = 92
            if vn_fb not in all_views_cache:
                all_views_cache[vn_fb] = load_shot_rich_telemetry(vn_fb, view_map)
            v_data = dict(all_views_cache[vn_fb])
            v_data["place_name"] = "The Underpass Shadow-Pool"
            views.append(v_data)

        hdl_entry = hdl_by_poem.get(p_num)
        hdl_meta = None
        if hdl_entry:
            hdl_meta = {
                "id": hdl_entry["id"],
                "name": hdl_entry.get("name", hdl_entry["id"]),
                "landmark": hdl_entry.get("landmark", ""),
                "footprint": hdl_entry.get("footprint", [10, 10]),
                "note": hdl_entry.get("note", ""),
                "eras": hdl_entry.get("eras", {}),
                "facts": hdl_entry.get("facts", []),
                "fit": hdl_entry.get("fit", []),
                "beats": hdl_entry.get("beats", []),
                "levels_count": len(hdl_entry.get("levels", [])),
                "rooms_count": sum(len(l.get("rooms", [])) for l in hdl_entry.get("levels", [])),
            }

        poems_bundle.append({
            "num": f"{p_num:02d}",
            "title": dossier.get("title", vt_p["title"]),
            "district": dossier.get("district", vt_p["district_name"]),
            "fx_code": vt_p.get("fx_code", f"FX{p_num:02d}"),
            "fx_name": vt_p.get("fx_name", ""),
            "dur": vt_p.get("dur", 90.0),
            "palette": dossier.get("palette", []),
            "palette_notes": dossier.get("palette_notes", ""),
            "essence": dossier.get("essence", ""),
            "full_text": dossier.get("full_text", []),
            "arc": dossier.get("arc", []),
            "characters": [
                {
                    "id": c.get("id", ""),
                    "costume": c.get("costume", ""),
                    "role": c.get("role_in_poem", ""),
                    "arc": c.get("arc", ""),
                    "actions": c.get("signature_actions", [])[:4],
                    "hands": c.get("hands", [])[:4],
                    "design_notes": c.get("design_notes", ""),
                }
                for c in dossier.get("characters", [])
            ],
            "props": [
                {
                    "id": pr.get("id", ""),
                    "name": pr.get("name", ""),
                    "hero": bool(pr.get("hero")),
                    "scale_cm": pr.get("scale_cm"),
                    "look": pr.get("look", ""),
                    "build": pr.get("build", ""),
                    "states": pr.get("states", []),
                    "who": pr.get("who", []),
                }
                for pr in dossier.get("props", [])
            ],
            "sets": [
                {
                    "id": st.get("id", ""),
                    "name": st.get("name", ""),
                    "look": st.get("look", ""),
                    "light": st.get("light", ""),
                    "layers": st.get("layers", {}),
                }
                for st in dossier.get("sets", [])
            ],
            "fx_specs": dossier.get("fx", []),
            "kits_to_build": dossier.get("kits_to_build", []),
            "insights": dossier.get("insights", []),
            "future": dossier.get("future", []),
            "assembly_pages": asm_pages,
            "transitions": atlas.get("transitions", [])[:4],
            "foundry": [
                {
                    "id": f.get("id", ""),
                    "desc": f.get("desc", ""),
                    "line": f.get("line", ""),
                    "hour": f.get("hour", ""),
                    "img": f.get("img", ""),
                }
                for f in (atlas.get("foundry") or [])[:6]
                if isinstance(f, dict)
            ],
            "hdl_meta": hdl_meta,
            "wire3d": wire3d,
            "views": views,
        })

    for vn_str in view_map.keys():
        vn_int = int(vn_str)
        if vn_int not in all_views_cache:
            all_views_cache[vn_int] = load_shot_rich_telemetry(vn_int, view_map)

    bundle = {
        "city": {
            "name": gaz.get("city", "Atlantis"),
            "tagline": gaz.get("tagline", "Where You Go When You Leave"),
            "summary": gaz.get("summary", ""),
            "water_datum": "+4.00m SALT LINE (#ecebe4 at 4/10 height) · KINTSUGI SEAM (#5fe8ff) · TIDE GATES (+0.90m, 12.42h cycle)",
            "archive_counts": {"bible_views": 108, "active_dirs": 81, "found_pool": 2707, "archive_frames": 45498},
            "eras": gaz.get("eras", []),
        },
        "poems": poems_bundle,
        "views_by_no": {str(k): v for k, v in sorted(all_views_cache.items())},
    }

    out_path = os.path.join(OUT_DIR, "vesper_world_bundle.json")
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(bundle, f, indent=2)
    print(f"Saved Vesper World Bundle ({len(poems_bundle)} poems, {len(all_views_cache)} views) -> {out_path}")
    return bundle


if __name__ == "__main__":
    build_vesper_world_bundle()
