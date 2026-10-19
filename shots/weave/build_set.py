"""The set for the weave passage: the AI plate (WYGWYL poem_07, keyframe 60) split into registered layers.

Writes shots/weave/set/:
  plate.jpg          the AI plate at 1920 wide, with the cut-out crowd figures painted out underneath (INVENTED, retouched)
  canopy_mask.png    the LED canopy (ADE20K 'ceiling' from the plate's own segmentation): the surface the archive plays on
  led.png            the canopy's LED dot texture (high-pass luminance), laid over the archive so it reads as shown on the canopy
  crowd_NN.png       the largest person cut-outs, each with a base pivot
  set.json           sizes, canopy quad (homography target for the archive), vanishing point, crowd pivots, provenance
Also extracts the archive clip to 24 fps frames + wav, and its loudness per frame (measured, drives the meter).
"""
import json, os, subprocess
import cv2
import numpy as np

ROOT = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(os.path.dirname(ROOT))
D = os.path.join(REPO, 'shots', 'video', 'poem_07', 'out', 'vid-poem-07-kf00060_0')
OUT = os.path.join(ROOT, 'set')
os.makedirs(OUT, exist_ok=True)
W, H = 1920, 1080
ARCH_ID = 'da69b1ba-1eb8-5072-8cf7-19fc272eba0f'


def main():
    img = cv2.imread(os.path.join(D, 'image.jpg'))
    a = np.load(os.path.join(D, 'arrays.npz'))
    lab = list(a['id2label'])
    seg = a['seg']
    s = W / img.shape[1]
    ph = int(round(img.shape[0] * s))
    up = lambda m, interp=cv2.INTER_LINEAR: cv2.resize(m, (W, ph), interpolation=interp)
    big = up(img, cv2.INTER_LANCZOS4)
    canvas = np.zeros((H, W, 3), np.uint8)
    oy = (H - ph) // 2

    ceil = (seg == lab.index('ceiling')).astype(np.uint8) * 255
    ceil = cv2.morphologyEx(ceil, cv2.MORPH_OPEN, np.ones((5, 5), np.uint8))
    # keep the canopy proper: the largest component (the side-building fragments are dropped)
    n, cl, st, _ = cv2.connectedComponentsWithStats(ceil)
    k = 1 + int(np.argmax(st[1:, 4]))
    ceil = ((cl == k) * 255).astype(np.uint8)
    ceil = cv2.GaussianBlur(up(ceil), (5, 5), 1.2)

    # LED texture: high-pass luminance of the canopy
    g = cv2.cvtColor(big, cv2.COLOR_BGR2GRAY).astype(np.float32)
    hp = g - cv2.GaussianBlur(g, (0, 0), 3.0)
    led = np.clip(128 + hp * 2.2, 0, 255).astype(np.uint8)

    # crowd cut-outs: largest person components in the bottom band
    per = (seg == lab.index('person')).astype(np.uint8)
    n, pl, pst, pc = cv2.connectedComponentsWithStats(per)
    order = sorted(range(1, n), key=lambda i: -pst[i, 4])
    crowd = []
    paint = np.zeros(seg.shape, np.uint8)
    for i in order:
        x, y, w, h, area = pst[i]
        if area < 900 or y + h < seg.shape[0] * 0.8 or w > 260:
            continue
        m = (pl == i).astype(np.uint8)
        paint |= m
        M = cv2.GaussianBlur(up(m * 255), (3, 3), 0.7)
        X0, Y0, X1, Y1 = int(x * s) - 2, int(y * s) - 2, int((x + w) * s) + 3, int((y + h) * s) + 3
        X0, Y0 = max(X0, 0), max(Y0, 0)
        X1, Y1 = min(X1, W), min(Y1, ph)
        rgba = np.dstack([big[Y0:Y1, X0:X1], M[Y0:Y1, X0:X1]])
        cid = 'crowd_%02d' % len(crowd)
        cv2.imwrite(os.path.join(OUT, cid + '.png'), rgba)
        crowd.append({'id': cid, 'file': 'set/%s.png' % cid, 'pos': [X0, Y0 + oy], 'size': [X1 - X0, Y1 - Y0],
                      'pivot': [(X1 - X0) / 2, Y1 - Y0], 'cx': (X0 + X1) / 2,
                      'ledger': 'INVENTED', 'provenance': 'person cut from the AI plate (ADE20K person component %d)' % i})
        if len(crowd) >= 9:
            break
    # paint out under the cut-outs so a tilt never shows a double
    hole = cv2.dilate(up(paint * 255, cv2.INTER_NEAREST), np.ones((9, 9), np.uint8))
    plate = cv2.inpaint(big, hole, 7, cv2.INPAINT_TELEA)

    canvas[oy:oy + ph] = plate
    cv2.imwrite(os.path.join(OUT, 'plate.jpg'), canvas, [cv2.IMWRITE_JPEG_QUALITY, 92])
    cm = np.zeros((H, W), np.uint8); cm[oy:oy + ph] = ceil
    cv2.imwrite(os.path.join(OUT, 'canopy_mask.png'), cm)
    lm = np.full((H, W), 128, np.uint8); lm[oy:oy + ph] = led
    cv2.imwrite(os.path.join(OUT, 'led.png'), lm)
    pm = np.zeros((H, W), np.uint8); pm[oy:oy + ph] = cv2.GaussianBlur(up(per * 255), (7, 7), 2)
    cv2.imwrite(os.path.join(OUT, 'crowd_mask.png'), pm)

    # the canopy's vanishing point: the lowest canopy pixel row's centre
    ys, xs = np.where(cm > 128)
    vy = ys.max(); vx = int(xs[ys >= vy - 3].mean())
    quad = [[-260, oy - 40], [W + 260, oy - 40], [vx + 70, vy + 8], [vx - 70, vy + 8]]  # archive TL,TR,BR,BL -> ceiling

    # archive: 24 fps frames + wav + loudness per frame
    src = os.path.join(ROOT, 'archive', ARCH_ID + '.mp4')
    fd = os.path.join(ROOT, 'archive', 'da69_frames')
    os.makedirs(fd, exist_ok=True)
    subprocess.run(['ffmpeg', '-v', 'error', '-y', '-i', src, '-vf', 'fps=24', '-q:v', '3', os.path.join(fd, '%04d.jpg')], check=True)
    wav = os.path.join(ROOT, 'archive', 'da69.wav')
    subprocess.run(['ffmpeg', '-v', 'error', '-y', '-i', src, '-ac', '1', '-ar', '48000', wav], check=True)
    import wave
    with wave.open(wav) as wf:
        x = np.frombuffer(wf.readframes(wf.getnframes()), np.int16).astype(np.float32) / 32768
    hop = 48000 // 24
    rms = np.array([np.sqrt(np.mean(x[i * hop:(i + 1) * hop] ** 2) + 1e-12) for i in range(len(x) // hop)])
    db = 20 * np.log10(rms + 1e-6)
    nframes = len(os.listdir(fd))

    meta = {'size': [W, H], 'plate_rect': [0, oy, W, ph], 'scale_from_plate': s,
            'plate': {'file': 'set/plate.jpg', 'ledger': 'INVENTED', 'provenance': 'WYGWYL poem_07 generated video, keyframe 60 (held)',
                      'retouch': 'crowd cut-outs painted out underneath (cv2.inpaint)'},
            'canopy': {'mask': 'set/canopy_mask.png', 'led': 'set/led.png', 'quad': quad, 'vanish': [vx, int(vy)],
                       'note': 'mask is the plate\'s own ADE20K ceiling class; palms and pillars stay in front because they are not ceiling'},
            'crowd': crowd,
            'archive': {'id': ARCH_ID, 'title': 'Sound And The Story', 'year': 1956, 'frames': 'archive/da69_frames/%04d.jpg',
                        'n': nframes, 'fps': 24, 'wav': 'archive/da69.wav', 'db': [round(float(v), 2) for v in db],
                        'page': 'https://www.movingimagearchive.com/sources/sound-and-the-story-331f8150?clip=' + ARCH_ID}}
    json.dump(meta, open(os.path.join(OUT, 'set.json'), 'w'), indent=1, default=lambda o: o.item() if hasattr(o, 'item') else str(o))
    print('crowd', len(crowd), 'vanish', vx, vy, 'archive frames', nframes, 'db range', round(db.min(), 1), round(db.max(), 1))


if __name__ == '__main__':
    main()
