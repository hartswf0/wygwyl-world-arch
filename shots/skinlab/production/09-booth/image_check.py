"""Image check of a rendered passage: does the figure change by pops? (round 3 self-check, by image, not by tracked path)

    python3 image_check.py FRAMES_DIR VERSION [x0 y0 x1 y1]

FRAMES_DIR holds f0000.png ... (render.mjs with KEEP_FRAMES=dir). Over a box around the figure in the close shot
(default: the booth's door opening), per frame:
  - diff: mean absolute pixel change from the previous frame (0-255), and the share of pixels that changed by > 40;
  - on twos a drawn pose holds two frames, so every other frame should be 0 (a hold) and the others a step.
It compares the steps of the lift (contact window) with the steps of the reach (which the critic accepted), lists
any step in f84-205 larger than the largest reach step, and writes image_check_vN.json plus a strip of the diffs
(image_check_vN.jpg: frame, then its difference image, f80-f136).
"""
import json, os, sys
import numpy as np
from PIL import Image, ImageDraw

d, V = sys.argv[1], sys.argv[2]
box = tuple(int(v) for v in sys.argv[3:7]) if len(sys.argv) >= 7 else (640, 0, 1120, 900)
files = sorted(f for f in os.listdir(d) if f.startswith('f') and f.endswith('.png'))
F = [np.asarray(Image.open(os.path.join(d, f)).convert('RGB').crop(box), dtype=np.int16) for f in files]
rows = []
for i in range(1, len(F)):
    a = np.abs(F[i] - F[i - 1]).max(axis=2)
    rows.append({'f': i, 'mean': round(float(a.mean()), 2), 'changed': round(float((a > 40).mean()), 4)})
R = {r['f']: r for r in rows}
rng = lambda a, b: [R[f] for f in range(a, b + 1) if f in R]
RA, LA = (int(os.environ.get('REACH', '79-82').split('-')[0]), int(os.environ.get('REACH', '79-82').split('-')[1])), (int(os.environ.get('LIFT', '83-95').split('-')[0]), int(os.environ.get('LIFT', '83-95').split('-')[1]))
reach = rng(*RA)                         # the reach the critic accepted (f78 is the cut); REACH=a-b to change
lift = rng(*LA)                          # the lift, grasp to contact; LIFT=a-b
rest = rng(96, 205)
mx = max(r['changed'] for r in reach)
out = {
    'version': V, 'box': box,
    'reach_steps_changed_share': [r['changed'] for r in reach],
    'lift_steps_changed_share': [r['changed'] for r in lift],
    'largest_reach_step': mx,
    'steps_after_reach_larger_than_largest_reach_step': [(r['f'], r['changed']) for r in lift + rest if r['changed'] > mx],
    'hold_frames_f96_205_with_any_change': [(r['f'], r['changed']) for r in rest if r['changed'] > 0.0005],
    'per_frame': rows,
}
json.dump(out, open(f'image_check_v{V}.json', 'w'), indent=1)
# strip: f80-f136, each frame over its difference image
sel = list(range(80, 137, 2))
tw, th = 160, 300
W = Image.new('RGB', (tw * len(sel), th * 2), (0, 0, 0)); dr = ImageDraw.Draw(W)
for k, f in enumerate(sel):
    im = Image.fromarray(F[f].astype(np.uint8)).resize((tw, th))
    W.paste(im, (k * tw, 0))
    if f >= 1:
        a = np.abs(F[f] - F[f - 1]).max(axis=2).astype(np.uint8)
        W.paste(Image.fromarray(a).convert('RGB').resize((tw, th)), (k * tw, th))
    dr.text((k * tw + 4, 4), str(f), fill=(255, 255, 0))
W.save(f'image_check_v{V}.jpg', quality=80)
print(json.dumps({k: v for k, v in out.items() if k != 'per_frame'}, indent=1))
