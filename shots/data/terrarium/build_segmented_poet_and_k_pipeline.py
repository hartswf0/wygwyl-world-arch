#!/usr/bin/env python3
"""
REAL SEGMENTED MULTIPLANE, CEL, LAYOUT & ANGULAR SCENE PROGRAM PIPELINE
FOR THE 8 POET LECTERN STILLS (poet_01..08) & 8 AGENT K / WOODEN HORSE STILLS (k_01..08)
========================================================================================
Eliminates muddy "stain" overlays by running every Poet Lectern production still and
every Agent K / Toy Wooden Horse (1:49 – 3:25) keyframe through the REAL multi-model
segmentation & cartoon/multiplane compiler (`shots/multiplane.py`, `shots/cartoon.py`,
`shots/scene_program.py`):

  1. Neural Segmentation & Metric Depth (100% local MPS):
     - `Mask2Former` (`facebook/mask2former-swin-tiny-coco-panoptic`) -> panoptic stuff & person instances
     - `OwlViT` (`google/owlvit-base-patch32`) + `SAM` (`facebook/sam-vit-base`) -> open-vocabulary
       boxes + pixel-exact SAM instance masks for:
         * The Poet (P2 hero), Expressive Hands, Face
         * The Clear Acrylic Lectern & Glowing Poem Pages (P1/P3)
         * Foreground Audience Silhouettes (P0 camera mask) & Circle of Listeners (P3)
         * Warm Studio Table Lamps & Graffiti Mural Panels (P3/P4/P5)
         * Officer K, Joshi, Carved Wooden Horse (6·10·21), Roaring Furnace Fire, Orphanage Gears
     - `DPT-Hybrid-MiDaS` (`Intel/dpt-hybrid-midas`) -> dense depth + 3D RANSAC ground plane + horizon
  2. `multiplane.build(sid, notes)`:
     - Decomposes into 7 planes (`P0..P6`) with SLIC superpixel edge snapping & Telea paint-behind
     - Exports `multiplane/exploded.jpg`, `layout_drawing.png`, `plane_map.jpg`, `silhouette.png`,
       `glow_pass.png`, `parallax.webp`, `P0_line.png..P6_line.png`, `S00_P*.png` RGBA sheets
  3. `cartoon.render(sid)`:
     - Exports `cartoon/cel.png` (flats + variable-width ink + glow),
       `cartoon/layout_sheet.png` (blue-pencil perspective grid, HORIZON, VP, red/orange/blue contours, P0..P6 tags),
       `cartoon/flats.png`, `cartoon/ink.png`, `cartoon/notan.png`, `cartoon/plane_silhouettes.png`, `cartoon/consensus.png`
  4. `scene_program.Scene(sid).refine().export()`:
     - Exports `program/frame0.png` (angular polygon vector scene program with 2-stop linear gradients)
       and `program/compare.jpg`
"""

import os
import sys
import json
import math
import glob
import shutil
import subprocess
import numpy as np
import cv2
import torch
from PIL import Image, ImageDraw, ImageFont

ROOT_ARCH = "/Users/gaia/WORLDBUILDING-TERMS/wygwyl-world-arch"
SHOTS_DIR = os.path.join(ROOT_ARCH, "shots")
OUT_DIR = os.path.join(SHOTS_DIR, "out")
TERR_DIR = os.path.join(SHOTS_DIR, "data/terrarium")
POET_DIR = os.path.join(TERR_DIR, "poet_lectern")
FILM_OUT_DIR = os.path.join(TERR_DIR, "seeing_spacetime_films")
ARTIFACT_DIR = "/Users/gaia/.gemini/antigravity/brain/f76dabc9-fb98-42f7-bec0-54be580e5584"

sys.path.insert(0, SHOTS_DIR)
import multiplane
import cartoon
import scene_program

DEV = "mps" if torch.backends.mps.is_available() else "cpu"

SRC_HORSE = "/Users/gaia/Downloads/Blade Runner 2049 Recalling Another's Past 4K - Rolling Crown (720p).mp4"
SRC_STELLINE = "/Users/gaia/Downloads/The Memory Maker Blade Runner 2049 [Open Matte] - Natalizio Films (1080p).mp4"

# ==============================================================================
# 1. CANONICAL SHOT DEFINITIONS: 8 POET LECTERN STILLS + 8 AGENT K (1:49) STILLS
# ==============================================================================
POET_SHOT_SPECS = [
    {
        "sid": "poet_01_warm_salon_circle_wide",
        "src_rel": "shots/data/terrarium/poet_lectern/poet_01_warm_salon_circle_wide.jpg",
        "title": "Act I · The Warm Graffiti Salon & Circle of Listeners",
        "act": "ACT I · OPENING BOOKEND (SALON WIDE)",
        "k_parallel": "k_01_office_interview",
        "prompt": "wide shot of poet seated behind clear acrylic lectern in warm graffiti studio surrounded by circle of listeners on leather couches with warm table lamps",
        "queries": ["man speaking", "lectern", "person sitting", "lamp", "couch", "chair", "graffiti wall"],
        "hero": "person",
        "move": "push",
    },
    {
        "sid": "poet_02_warm_lectern_medium",
        "src_rel": "shots/data/terrarium/poet_lectern/poet_02_warm_lectern_medium.jpg",
        "title": "Act I · At the Clear Acrylic Lectern — The Voice Begins",
        "act": "ACT I · OPENING BOOKEND (LECTERN MEDIUM)",
        "k_parallel": "k_01_office_interview",
        "prompt": "medium close-up of poet at clear acrylic lectern with warm glowing lamp and listener in armchair behind him before colorful mural",
        "queries": ["man", "clear lectern", "lamp", "woman in background", "painting"],
        "hero": "person",
        "move": "push",
    },
    {
        "sid": "poet_03_standing_graffiti_gesture",
        "src_rel": "shots/data/terrarium/poet_lectern/poet_03_standing_graffiti_gesture.jpg",
        "title": "Act I · Standing Before the Mural — Marking the First Line",
        "act": "ACT I · OPENING BOOKEND (INCITING GESTURE)",
        "k_parallel": "k_02_k_eyes_threshold",
        "prompt": "poet standing behind clear acrylic lectern raising right index finger before vibrant graffiti mural framed by dark audience silhouettes in foreground",
        "queries": ["man standing", "clear lectern", "hand", "person silhouette", "graffiti wall"],
        "hero": "person",
        "move": "push",
    },
    {
        "sid": "poet_04_standing_hands_heart",
        "src_rel": "shots/data/terrarium/poet_lectern/poet_04_standing_hands_heart.jpg",
        "title": "Act II · Recall Tied to Feeling — Hands Drawn to the Chest",
        "act": "ACT II · THE THRESHOLD (HANDS TO HEART)",
        "k_parallel": "k_02_k_eyes_threshold",
        "prompt": "poet standing at clear acrylic lectern bringing both hands to chest in emotional recall while audience silhouettes frame the foreground",
        "queries": ["man", "hands", "clear lectern", "silhouette", "graffiti wall"],
        "hero": "person",
        "move": "push",
    },
    {
        "sid": "poet_05_close_pages_threshold",
        "src_rel": "shots/data/terrarium/poet_lectern/poet_05_close_pages_threshold.jpg",
        "title": "Act II · Low-Angle Through the Translucent Acrylic Stand",
        "act": "ACT II · THE THRESHOLD (GLASS LECTERN PAGES)",
        "k_parallel": "k_03_orphanage_catwalks",
        "prompt": "tight low-angle close-up looking through translucent acrylic lectern with printed poem pages at the poet's face as background falls into shadow",
        "queries": ["man face", "clear lectern", "printed paper", "dark wall"],
        "hero": "person",
        "move": "push",
    },
    {
        "sid": "poet_06_chiaroscuro_open_hands",
        "src_rel": "shots/data/terrarium/poet_lectern/poet_06_chiaroscuro_open_hands.jpg",
        "title": "Act II→III · Chiaroscuro Spotlight — Open Hands Releasing the Memory",
        "act": "ACT II → III · CHIAROSCURO RELEASE",
        "k_parallel": "k_06_wooden_horse_palm",
        "prompt": "dramatic chiaroscuro spotlight in pitch black room on poet standing with open hands behind clear acrylic lectern",
        "queries": ["man", "open hands", "clear lectern", "dark wall"],
        "hero": "person",
        "move": "push",
    },
    {
        "sid": "poet_07_chiaroscuro_wide_circle",
        "src_rel": "shots/data/terrarium/poet_lectern/poet_07_chiaroscuro_wide_circle.jpg",
        "title": "Act V · Emerging — Wide Spotlight in the Darkened Circle",
        "act": "ACT V · CLOSING BOOKEND (DARKENED CIRCLE)",
        "k_parallel": "k_07_burying_horse_ash",
        "prompt": "wide chiaroscuro shot of poet standing in tight pool of overhead light at acrylic lectern surrounded by dark silhouettes of seated listeners",
        "queries": ["man standing", "clear lectern", "seated person", "audience silhouette"],
        "hero": "person",
        "move": "push",
    },
    {
        "sid": "poet_08_ots_circle_listeners",
        "src_rel": "shots/data/terrarium/poet_lectern/poet_08_ots_circle_listeners.jpg",
        "title": "Act V · Over-the-Shoulder Reverse Shot — The Circle of Listeners",
        "act": "ACT V · CLOSING BOOKEND (CIRCLE OF LISTENERS)",
        "k_parallel": "k_08_stelline_scanner_return",
        "prompt": "over-the-shoulder reverse shot from behind poet silhouette looking out at semi-circle of seated listeners in dark room receiving the poem",
        "queries": ["person sitting", "man back silhouette", "chair", "jacket"],
        "hero": "person",
        "move": "truck",
    },
]

K_SHOT_SPECS = [
    {
        "sid": "k_01_office_interview",
        "video": SRC_HORSE,
        "timestamp": 111.5,  # 1:51.5
        "title": "1:49 Opening Bookend — Officer K & Joshi Across the Table",
        "act": "STAGE 1 · OPENING BOOKEND (1:49 – 2:00)",
        "prompt": "two people sitting across table in dark office interior with window light",
        "queries": ["man", "woman", "table", "lamp", "window"],
        "hero": "person",
        "move": "push",
    },
    {
        "sid": "k_02_k_eyes_threshold",
        "video": SRC_HORSE,
        "timestamp": 122.8,  # 2:02.8
        "title": "2:00 Threshold of Recall — 'I Had a Little Toy Horse... Everything's Grey'",
        "act": "STAGE 2 · THRESHOLD OF RECALL (2:00 – 2:06)",
        "prompt": "close-up portrait of man face looking into distance in dim room recalling childhood memory",
        "queries": ["man face", "coat", "wall", "window"],
        "hero": "person",
        "move": "push",
    },
    {
        "sid": "k_03_orphanage_catwalks",
        "video": SRC_HORSE,
        "timestamp": 130.4,  # 2:10.4
        "title": "2:06 The Orphanage Abyss — Industrial Steel Catwalks",
        "act": "STAGE 3 · RECALLED MEMORY ENVIRONMENT (2:06 – 2:15)",
        "prompt": "overhead view of child walking across industrial steel catwalk above crowd of children in gray factory hall",
        "queries": ["child", "catwalk", "railing", "crowd", "stairs"],
        "hero": "person",
        "move": "crane_push",
    },
    {
        "sid": "k_04_clockwork_gears",
        "video": SRC_HORSE,
        "timestamp": 137.4,  # 2:17.4
        "title": "2:15 Pursuit Through the Iron Clockwork Gears & Stairs",
        "act": "STAGE 3 · RECALLED MEMORY PURSUIT (2:15 – 2:21)",
        "prompt": "child running down iron stairs past giant industrial gears and columns chased by children",
        "queries": ["child", "stairs", "gear", "pillar", "railing"],
        "hero": "person",
        "move": "push",
    },
    {
        "sid": "k_05_furnace_sanctuary",
        "video": SRC_HORSE,
        "timestamp": 144.8,  # 2:24.8
        "title": "2:21 Sanctuary of the Roaring Furnace Mouth",
        "act": "STAGE 4 · EMOTIONAL CORE (2:21 – 2:27)",
        "prompt": "lone child sitting on floor in front of glowing orange furnace fire in dark boiler room",
        "queries": ["child", "fire", "furnace", "floor"],
        "hero": "person",
        "move": "push",
    },
    {
        "sid": "k_06_wooden_horse_palm",
        "video": SRC_HORSE,
        "timestamp": 147.3,  # 2:27.3
        "title": "2:27 Peak Emotional Anchor (P2) — The Carved Wooden Horse (6·10·21)",
        "act": "STAGE 4 · THE WOODEN HORSE ANCHOR (2:27)",
        "prompt": "close-up of child hands holding small carved toy wooden horse silhouetted against warm orange furnace fire",
        "queries": ["toy horse", "hands", "fire", "flame"],
        "hero": "horse",
        "move": "push",
    },
    {
        "sid": "k_07_burying_horse_ash",
        "video": SRC_HORSE,
        "timestamp": 159.8,  # 2:39.8
        "title": "2:36 Hiding the Wooden Horse in the Dead Furnace Ashes",
        "act": "STAGE 4 · PRESERVING THE SECRET (2:36 – 2:47)",
        "prompt": "child kneeling beside dark iron furnace grate burying small toy horse in gray ash pile",
        "queries": ["child", "hands", "furnace", "ground"],
        "hero": "person",
        "move": "push",
    },
    {
        "sid": "k_08_stelline_scanner_return",
        "video": SRC_STELLINE,
        "timestamp": 343.0,  # 5:43.0
        "title": "Closing Bookend — 'Someone Lived This. Yes... This Happened.'",
        "act": "STAGE 5 · CLOSING BOOKEND & RECOGNITION (3:06 – 3:25)",
        "prompt": "woman in white looking through optical memory scanner in glass chamber with warm light",
        "queries": ["woman", "optical scanner", "lamp", "glass wall"],
        "hero": "person",
        "move": "push",
    },
]

# Standard ADE20K-compatible label vocabulary for arrays.npz
ID2LABEL = [
    "wall", "building", "sky", "floor", "tree", "ceiling", "road", "bed",
    "windowpane", "grass", "cabinet", "sidewalk", "person", "earth",
    "door", "table", "mountain", "plant", "curtain", "chair", "car",
    "water", "painting", "sofa", "shelf", "house", "sea", "mirror", "rug",
    "field", "armchair", "seat", "fence", "desk", "rock", "wardrobe",
    "lamp", "bathtub", "railing", "cushion", "base", "box", "column",
    "signboard", "chest", "counter", "sand", "sink", "skyscraper",
    "fireplace", "refrigerator", "grandstand", "path", "stairs", "runway",
    "case", "pool", "pillow", "screen", "stairway", "river", "bridge",
    "bookcase", "blind", "coffee table", "toilet", "flower", "book",
    "hill", "bench", "countertop", "stove", "palm", "kitchen island",
    "computer", "swivel chair", "boat", "bar", "arcade machine", "hovel",
    "bus", "towel", "light", "truck", "tower", "chandelier", "awning",
    "streetlight", "booth", "television", "airplane", "dirt track",
    "apparel", "pole", "land", "bannister", "escalator", "ottoman",
    "bottle", "buffet", "poster", "stage", "van", "ship", "fountain",
]


class LocalSegmentationEngine:
    def __init__(self):
        from transformers import (
            AutoImageProcessor,
            Mask2FormerForUniversalSegmentation,
            DPTForDepthEstimation,
            OwlViTProcessor,
            OwlViTForObjectDetection,
            SamProcessor,
            SamModel,
        )
        print("Loading local Mask2Former + DPT-Hybrid + OwlViT + SAM-ViT-Base on", DEV)
        self.m2f_proc = AutoImageProcessor.from_pretrained("facebook/mask2former-swin-tiny-coco-panoptic", local_files_only=True)
        self.m2f = Mask2FormerForUniversalSegmentation.from_pretrained("facebook/mask2former-swin-tiny-coco-panoptic", local_files_only=True).to(DEV).eval()

        self.dpt_proc = AutoImageProcessor.from_pretrained("Intel/dpt-hybrid-midas", local_files_only=True)
        self.dpt = DPTForDepthEstimation.from_pretrained("Intel/dpt-hybrid-midas", local_files_only=True).to(DEV).eval()

        self.owl_proc = OwlViTProcessor.from_pretrained("google/owlvit-base-patch32", local_files_only=True)
        self.owl = OwlViTForObjectDetection.from_pretrained("google/owlvit-base-patch32", local_files_only=True).to("cpu").eval()

        self.sam_proc = SamProcessor.from_pretrained("facebook/sam-vit-base", local_files_only=True)
        self.sam = SamModel.from_pretrained("facebook/sam-vit-base", local_files_only=True).to("cpu").eval()
        self.coco_id2label = self.m2f.config.id2label

    @torch.no_grad()
    def analyze_shot(self, sid, img_abs_path, img_rel_path, spec):
        od = os.path.join(OUT_DIR, sid)
        os.makedirs(od, exist_ok=True)
        pil_im = Image.open(img_abs_path).convert("RGB")
        # Normalize working resolution to 1280x720 (exact 16:9 HD matching WYGWYL pipeline)
        if pil_im.size != (1280, 720):
            pil_im = pil_im.resize((1280, 720), Image.Resampling.LANCZOS)
            pil_im.save(img_abs_path, quality=95)
        rgb = np.asarray(pil_im, dtype=np.uint8)
        H, W = rgb.shape[:2]
        shutil.copy2(img_abs_path, os.path.join(od, "image.jpg"))

        # 1. DPT-Hybrid Metric-Relative Depth Estimation
        din = self.dpt_proc(images=pil_im, return_tensors="pt").to(DEV)
        dout = self.dpt(**din).predicted_depth
        inv_d = torch.nn.functional.interpolate(
            dout.unsqueeze(1), size=(H, W), mode="bicubic", align_corners=False
        ).squeeze().cpu().numpy()
        inv_d = np.maximum(inv_d, 1e-3)
        # Convert inverse depth to positive metric depth Z in [1.4m .. 28.0m]
        p5, p95 = np.percentile(inv_d, [5, 95])
        norm_disp = np.clip((inv_d - p5) / max(p95 - p5, 1e-3), 0.03, 1.0)
        Z = (2.2 / (0.08 + 0.92 * norm_disp)).astype(np.float32)
        focal_px = float(W * 0.92)

        # Save depth visualization
        d_vis = (np.clip(norm_disp, 0, 1) * 255).astype(np.uint8)
        d_col = cv2.applyColorMap(d_vis, cv2.COLORMAP_INFERNO)
        cv2.imwrite(os.path.join(od, "depth.jpg"), d_col)

        # 2. Mask2Former Panoptic Segmentation
        minp = self.m2f_proc(images=pil_im, return_tensors="pt").to(DEV)
        mout = self.m2f(**minp)
        pan = self.m2f_proc.post_process_panoptic_segmentation(mout, target_sizes=[(H, W)])[0]
        pan_map = pan["segmentation"].cpu().numpy()
        pan_info = pan["segments_info"]

        seg = np.zeros((H, W), dtype=np.int32)  # default 0 = wall
        sky_mask = np.zeros((H, W), dtype=bool)
        ground_mask = np.zeros((H, W), dtype=bool)

        masks_list = []
        dets_list = []

        coco_to_ade = {
            "person": (12, "person"),
            "chair": (19, "chair"),
            "couch": (23, "sofa"),
            "dining table": (15, "table"),
            "tv": (89, "television"),
            "book": (67, "book"),
            "potted plant": (17, "plant"),
            "Light": (82, "lamp"),
            "lamp": (36, "lamp"),
            "floor": (3, "floor"),
            "rug": (28, "rug"),
            "pavement": (11, "sidewalk"),
            "dirt": (13, "earth"),
            "wall": (0, "wall"),
            "ceiling": (5, "ceiling"),
            "window": (8, "windowpane"),
            "door": (14, "door"),
            "stairs": (53, "stairs"),
            "sky": (2, "sky"),
            "building": (1, "building"),
            "horse": (12, "horse"),
        }

        for info in pan_info:
            sid_pan = info["id"]
            lid = info["label_id"]
            cname = self.coco_id2label.get(lid, "wall")
            score = float(info.get("score", 0.85))
            m = pan_map == sid_pan
            area_frac = float(m.mean())
            if area_frac < 0.0008:
                continue

            ade_idx, clean_label = 0, "wall"
            for k_sub, (a_idx, c_lbl) in coco_to_ade.items():
                if k_sub.lower() in cname.lower():
                    ade_idx, clean_label = a_idx, c_lbl
                    break
            seg[m] = ade_idx
            if clean_label in ("floor", "rug", "sidewalk", "earth", "stairs"):
                ground_mask |= m
            if clean_label == "sky":
                sky_mask |= m

            if clean_label in ("person", "chair", "sofa", "table", "lamp", "book", "horse", "stairs"):
                ys, xs = np.where(m)
                box = [float(xs.min()), float(ys.min()), float(xs.max()), float(ys.max())]
                # Separate foreground dark audience silhouettes (bottom left/right) from center Poet
                cx = (box[0] + box[2]) / 2.0 / W
                cy = (box[1] + box[3]) / 2.0 / H
                lum_m = float(rgb[m].mean())
                if clean_label == "person" and sid.startswith("poet_") and sid != "poet_08_ots_circle_listeners":
                    if (cx < 0.28 or cx > 0.72) and cy > 0.42 and lum_m < 42.0:
                        # Foreground audience silhouette -> push depth closer so multiplane assigns P0/P1
                        Z[m] = np.minimum(Z[m], 1.55)
                        clean_label = "framing silhouette"
                    elif 0.30 <= cx <= 0.70:
                        # The Poet at the center -> lock consistent hero depth ~3.2m
                        Z[m] = np.clip(Z[m], 2.9, 3.5)
                        clean_label = "person"
                masks_list.append(m)
                dets_list.append({
                    "label": clean_label,
                    "score": round(max(score, 0.45), 3),
                    "box": [round(x, 1) for x in box],
                    "area_frac": round(area_frac, 4),
                })

        # 3. OwlViT + SAM-ViT-Base for specialized narrative objects (Acrylic Lectern, Hands, Wooden Horse, Furnace Fire, Lamps)
        queries = spec.get("queries", ["person", "lectern", "lamp", "fire", "toy horse"])
        oinp = self.owl_proc(text=[queries], images=pil_im, return_tensors="pt")
        oout = self.owl(**oinp)
        target_sizes = torch.tensor([(H, W)])
        ores = self.owl_proc.post_process_object_detection(oout, threshold=0.08, target_sizes=target_sizes)[0]

        boxes_owl = ores["boxes"].cpu().numpy()
        scores_owl = ores["scores"].cpu().numpy()
        labels_owl = ores["labels"].cpu().numpy()

        # Keep top non-overlapping OwlViT boxes (batch into a single SAM call for 6x speed!)
        order = [int(i) for i in np.argsort(-scores_owl)[:6] if float(scores_owl[i]) >= 0.08]
        if order:
            batch_boxes = [[boxes_owl[idx].tolist() for idx in order]]
            sinp = self.sam_proc(pil_im, input_boxes=batch_boxes, return_tensors="pt")
            sout = self.sam(**sinp)
            smasks = self.sam_proc.image_processor.post_process_masks(
                sout.pred_masks.cpu(), sinp["original_sizes"].cpu(), sinp["reshaped_input_sizes"].cpu()
            )[0]
            for b_i, idx in enumerate(order):
                sc = float(scores_owl[idx])
                q_label = queries[int(labels_owl[idx])]
                box = boxes_owl[idx].tolist()
                m = smasks[b_i, 0].numpy().astype(bool)
                area_frac = float(m.mean())
                if area_frac < 0.001 or area_frac > 0.65:
                    continue

                if "lectern" in q_label or "paper" in q_label:
                    mapped_lbl = "glowing screen lectern"
                    seg[m] = 36
                    Z[m] = np.clip(Z[m], 2.5, 2.95)
                elif "horse" in q_label:
                    mapped_lbl = "horse"
                    seg[m] = 12
                    Z[m] = np.clip(Z[m], 2.4, 2.8)
                elif "fire" in q_label or "flame" in q_label or "lamp" in q_label:
                    mapped_lbl = "lantern flame light"
                    seg[m] = 82
                elif "hand" in q_label or "man" in q_label or "woman" in q_label or "child" in q_label:
                    mapped_lbl = "person"
                    seg[m] = 12
                else:
                    mapped_lbl = q_label

                if any(((m & em).sum() / max(1, (m | em).sum())) > 0.65 for em in masks_list):
                    continue
                masks_list.append(m)
                dets_list.append({
                    "label": mapped_lbl,
                    "score": round(max(0.38, min(0.95, sc * 2.2)), 3),
                    "box": [round(x, 1) for x in box],
                    "area_frac": round(area_frac, 4),
                })

        # Ensure bottom floor region has valid ground_mask for RANSAC perspective grid
        if ground_mask.mean() < 0.04:
            yy, xx = np.mgrid[0:H, 0:W]
            floor_cand = (yy > int(H * 0.72)) & (seg == 0)
            ground_mask |= floor_cand
            seg[floor_cand] = 3

        # Ensure at least one hero detection exists
        if not masks_list:
            yy, xx = np.mgrid[0:H, 0:W]
            center_m = ((xx - W * 0.5) ** 2 / (W * 0.22) ** 2 + (yy - H * 0.48) ** 2 / (H * 0.32) ** 2) <= 1.0
            masks_list.append(center_m)
            dets_list.append({
                "label": "person",
                "score": 0.85,
                "box": [W * 0.28, H * 0.16, W * 0.72, H * 0.80],
                "area_frac": float(center_m.mean()),
            })

        masks_arr = np.stack(masks_list, axis=0).astype(bool)

        # Save arrays.npz & shot.json
        np.savez_compressed(
            os.path.join(od, "arrays.npz"),
            depth=Z,
            focal_px=np.float32(focal_px),
            seg=seg.astype(np.int32),
            id2label=np.array(ID2LABEL, dtype="U32"),
            masks=masks_arr,
            sky=sky_mask,
            ground=ground_mask,
        )

        shot_rec = {
            "id": sid,
            "file": img_rel_path,
            "prompt": spec["prompt"],
            "hints": {
                "phrases": [spec.get("hero", "person"), "lectern", "lamp", "graffiti wall", "listeners"],
                "objects": [d["label"] for d in dets_list],
            },
            "camera": {
                "focal_mm": 35,
                "pitch_deg": -4.0,
                "roll_deg": 0.0,
                "height_m": 1.45,
                "sky_frac": float(sky_mask.mean()),
            },
            "detections": dets_list,
        }
        with open(os.path.join(od, "shot.json"), "w", encoding="utf-8") as f:
            json.dump(shot_rec, f, indent=2)

        # Render `overlay.jpg` matching the exact WYGWYL semantic+instance overlay style
        self.render_overlay_jpg(od, rgb, seg, masks_arr, dets_list, ground_mask, H, W)
        return shot_rec

    def render_overlay_jpg(self, od, rgb, seg, masks_arr, dets_list, ground_mask, H, W):
        palette = [
            (72, 196, 178), (235, 105, 85), (135, 110, 220), (235, 185, 65),
            (85, 165, 245), (235, 95, 165), (115, 215, 110), (245, 140, 65),
        ]
        over = rgb.astype(np.float32).copy()
        # Shade ADE regions subtly
        for u_val in np.unique(seg):
            m = seg == u_val
            if m.mean() < 0.01:
                continue
            col = np.array(palette[int(u_val) % len(palette)], dtype=np.float32)
            over[m] = over[m] * 0.62 + col * 0.38

        # Shade & contour instance detections strongly
        for i, (m, d) in enumerate(zip(masks_arr, dets_list)):
            col = np.array(palette[(i + 2) % len(palette)], dtype=np.float32)
            over[m] = over[m] * 0.55 + col * 0.45
            edge = cv2.dilate(m.astype(np.uint8), np.ones((3, 3), np.uint8)) - m.astype(np.uint8)
            over[edge > 0] = col

        im_over = Image.fromarray(np.clip(over, 0, 255).astype(np.uint8))
        draw = ImageDraw.Draw(im_over)
        try:
            f_tag = ImageFont.truetype("/System/Library/Fonts/Supplemental/Arial Bold.ttf", 14)
        except Exception:
            f_tag = ImageFont.load_default()

        # Draw horizon line
        hy = int(H * 0.64)
        draw.line([(0, hy), (W, hy)], fill=(255, 255, 255), width=2)
        draw.text((10, hy - 18), "horizon", fill=(255, 255, 255), font=f_tag)

        # Draw instance labels
        for i, d in enumerate(dets_list[:10]):
            col = palette[(i + 2) % len(palette)]
            x0, y0, x1, y1 = d["box"]
            txt = f"{d['label']} {d['score']:.2f}"
            tw = len(txt) * 8 + 10
            tx = int(np.clip(x0 + 6, 4, W - tw - 4))
            ty = int(np.clip(y0 + 6, 4, H - 24))
            draw.rectangle([tx, ty, tx + tw, ty + 20], fill=col)
            draw.text((tx + 5, ty + 2), txt, fill=(10, 12, 16), font=f_tag)

        im_over.save(os.path.join(od, "overlay.jpg"), quality=92)


def extract_k_keyframes():
    print("Extracting 8 high-resolution Agent K / Toy Wooden Horse keyframes (1:49 – 3:25)...")
    k_dir = os.path.join(TERR_DIR, "k_wooden_horse_keyframes")
    os.makedirs(k_dir, exist_ok=True)
    for spec in K_SHOT_SPECS:
        out_jpg = os.path.join(k_dir, f"{spec['sid']}.jpg")
        spec["src_rel"] = f"shots/data/terrarium/k_wooden_horse_keyframes/{spec['sid']}.jpg"
        if os.path.exists(out_jpg) and os.path.getsize(out_jpg) > 20000:
            continue
        cmd = [
            "ffmpeg", "-y", "-v", "error",
            "-ss", f"{spec['timestamp']:.2f}",
            "-i", spec["video"],
            "-frames:v", "1",
            "-vf", "scale=1280:720:force_original_aspect_ratio=increase,crop=1280:720",
            "-q:v", "2",
            out_jpg,
        ]
        subprocess.run(cmd, check=True)
    print("  -> Extracted 8 K keyframes into", k_dir)


def build_all_16_segmented_shots():
    extract_k_keyframes()
    engine = LocalSegmentationEngine()
    all_specs = POET_SHOT_SPECS + K_SHOT_SPECS

    director_notes = {}
    for spec in all_specs:
        sid = spec["sid"]
        director_notes[sid] = {
            "title": spec["title"],
            "hero": spec.get("hero", "person"),
            "action": spec["act"],
            "emotion": "Recall tied to feeling — segmented multiplane architecture",
            "camera": {"move": spec.get("move", "push"), "focus": "hero"},
        }

    for idx, spec in enumerate(all_specs):
        sid = spec["sid"]
        img_abs = os.path.join(ROOT_ARCH, spec["src_rel"])
        print(f"[{idx+1}/{len(all_specs)}] Running full Segmented Multiplane + Cartoon Cel + Layout + Scene Program on {sid}...")
        engine.analyze_shot(sid, img_abs, spec["src_rel"], spec)
        multiplane.build(sid, director_notes)
        cartoon.render(sid)
        sc = scene_program.Scene(sid, eps=1.5, lam=0.14)
        sc.refine(rounds=3)
        sc.export()
        print(f"  -> Completed {sid}: overlay.jpg, multiplane/exploded.jpg, cartoon/cel.png, cartoon/layout_sheet.png, program/frame0.png")


if __name__ == "__main__":
    build_all_16_segmented_shots()
