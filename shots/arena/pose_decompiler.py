"""Pose Decompiler: Turn Bolas-conditioned character keyframe generations into articulated cardboard puppet parts.

Workflow:
1. Extract 3D keyframe beats from Bolas Crash Lab (e.g. crouches, deep bends, rolls, jumps).
2. Generate the character in that exact perspective pose with authentic cardboard edge textures and brass brads.
3. Decompile: Remove studio background, isolate transparent puppet, and segment into modular parts.
4. Register into cast library for keyframe swapping on the Arena beat strip.
"""
import argparse, cv2, json, os, sys
import numpy as np
from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(HERE)


def isolate_figure(image_path, out_clean_path, pad=10):
    """Cleanly isolates the foreground cardboard figure from studio background."""
    bgr = cv2.imread(image_path)
    if bgr is None:
        raise FileNotFoundError(f"Cannot load image: {image_path}")
    rgb = cv2.cvtColor(bgr, cv2.COLOR_BGR2RGB)
    h, w, _ = bgr.shape

    # Color difference from background white/light-gray [248, 248, 248]
    bg_ref = np.array([248.0, 248.0, 248.0])
    diff = np.linalg.norm(bgr.astype(float) - bg_ref, axis=2)
    fg = (diff > 25.0).astype(np.uint8) * 255

    # Morphology to eliminate holes inside cardboard/brads
    kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (7, 7))
    fg = cv2.morphologyEx(fg, cv2.MORPH_CLOSE, kernel)

    # Keep largest connected component (the figure)
    num_labels, labels, stats, centroids = cv2.connectedComponentsWithStats(fg)
    if num_labels <= 1:
        raise ValueError(f"No figure detected in {image_path}")
    largest_label = 1 + np.argmax(stats[1:, cv2.CC_STAT_AREA])
    clean_fg = (labels == largest_label).astype(np.uint8) * 255
    clean_fg = cv2.GaussianBlur(clean_fg, (3, 3), 0)

    x, y, bw, bh, area = stats[largest_label]
    rgba = np.dstack([rgb, clean_fg])
    cropped = rgba[max(0, y - pad):min(h, y + bh + pad), max(0, x - pad):min(w, x + bw + pad)]

    os.makedirs(os.path.dirname(os.path.abspath(out_clean_path)), exist_ok=True)
    Image.fromarray(cropped).save(out_clean_path)
    print(f"[OK] Clean cutout saved: {out_clean_path} ({cropped.shape[1]}x{cropped.shape[0]} px)")
    return cropped


def decompile_parts(rgba_arr, cuts, out_dir, prefix):
    """Slices the isolated figure into modular articulated cardboard pieces."""
    h, w, _ = rgba_arr.shape
    os.makedirs(out_dir, exist_ok=True)
    decompiled = {}

    for part_name, (ymin, xmin, ymax, xmax) in cuts.items():
        y0, y1 = int(ymin * h), int(ymax * h)
        x0, x1 = int(xmin * w), int(xmax * w)
        sub = rgba_arr[y0:y1, x0:x1].copy()

        alpha = sub[:, :, 3]
        if np.any(alpha > 20):
            ys, xs = np.where(alpha > 20)
            tight = sub[ys.min():ys.max() + 1, xs.min():xs.max() + 1]
            out_file = os.path.join(out_dir, f"{prefix}.{part_name}.png")
            Image.fromarray(tight).save(out_file)
            decompiled[part_name] = {
                'path': out_file,
                'width': tight.shape[1],
                'height': tight.shape[0],
                'rel_box': [round(ymin, 3), round(xmin, 3), round(ymax, 3), round(xmax, 3)]
            }
            print(f"  - Decompiled part '{part_name}': {out_file} ({tight.shape[1]}x{tight.shape[0]})")
    return decompiled


def main():
    parser = argparse.ArgumentParser(description="Decompile pose-generated puppets into parts.")
    parser.add_argument("image", help="Path to input generated pose image")
    parser.add_argument("--out-clean", default="shots/arena/poses/clean_figure.png", help="Path for transparent cutout")
    parser.add_argument("--out-parts-dir", default="shots/weave/cast/man/parts", help="Directory for decompiled parts")
    parser.add_argument("--prefix", default="man.pose", help="Prefix for part filenames")
    parser.add_argument("--character", choices=['man', 'poet'], default='man', help="Character template for segmentation")
    args = parser.parse_args()

    rgba = isolate_figure(args.image, args.out_clean)

    if args.character == 'man':
        cuts = {
            'head': (0.0, 0.45, 0.35, 1.0),
            'arm': (0.2, 0.0, 0.65, 0.55),
            'torso': (0.2, 0.3, 0.6, 0.85),
            'legs': (0.45, 0.1, 1.0, 1.0)
        }
    else:
        cuts = {
            'head': (0.0, 0.45, 0.4, 1.0),
            'arm': (0.25, 0.0, 0.6, 0.6),
            'torso_dress': (0.25, 0.2, 0.8, 0.85),
            'legs': (0.55, 0.2, 1.0, 0.85)
        }

    parts = decompile_parts(rgba, cuts, args.out_parts_dir, args.prefix)
    manifest = {
        'source_image': args.image,
        'clean_figure': args.out_clean,
        'character': args.character,
        'parts': parts
    }
    manifest_path = os.path.join(args.out_parts_dir, f"{args.prefix}_manifest.json")
    with open(manifest_path, 'w') as f:
        json.dump(manifest, f, indent=2)
    print(f"[DONE] Registered manifest in {manifest_path}")


if __name__ == '__main__':
    main()
