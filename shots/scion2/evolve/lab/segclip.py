"""seg_clip family helpers: SAM part regions of the reference, CLIP region-to-card matching, joint snapping.

segment(t) -> label map (H x W int8, -1 = not figure) over PARTS, the reference split into part regions:
  SAM ViT-B (quantised ONNX, /tmp/claude-0/sam), prompted per part from the Pose Lab markers: 3 positive points along
  the part's bone, negative points at the middle of the neighbouring bones. Each part keeps its SAM mask inside the
  figure; a pixel claimed by several parts goes to the part whose bone is nearest; figure pixels nobody claimed go to
  the nearest bone. Guidance only: no reference pixel is ever placed.
embed(px) -> CLIP ViT-B/32 image embedding of a card / region crop on the neutral background (cached per card id).
"""
import json, math, os
import numpy as np, cv2

SAM = '/tmp/claude-0/sam'
CACHE = '/tmp/claude-0/evolve-scratch/piece_emb'
PARTS = ['head', 'torso', 'uarmL', 'uarmR', 'farmL', 'farmR', 'handL', 'handR', 'thighL', 'thighR', 'shinL', 'shinR', 'footL', 'footR']
NEIGH = {'head': ['torso'], 'torso': ['head', 'uarmL', 'uarmR', 'thighL', 'thighR'], 'uarmL': ['torso', 'farmL'], 'uarmR': ['torso', 'farmR'],
         'farmL': ['uarmL', 'handL'], 'farmR': ['uarmR', 'handR'], 'handL': ['farmL'], 'handR': ['farmR'],
         'thighL': ['torso', 'shinL', 'thighR'], 'thighR': ['torso', 'shinR', 'thighL'], 'shinL': ['thighL', 'footL'], 'shinR': ['thighR', 'footR'],
         'footL': ['shinL'], 'footR': ['shinR']}
_S = {}


def bones(m):
    mid = (m['hipL'] + m['hipR']) / 2
    B = {'head': (m['neck'], m['neck'] + 1.6 * (m['head'] - m['neck'])), 'torso': (m['neck'], mid)}
    for S in 'LR':
        e, w = m['elbow' + S], m['wrist' + S]
        B.update({'uarm' + S: (m['shoulder' + S], e), 'farm' + S: (e, w), 'hand' + S: (w, w + .6 * (w - e)),
                  'thigh' + S: (m['hip' + S], m['knee' + S]), 'shin' + S: (m['knee' + S], m['ankle' + S]),
                  'foot' + S: (m['ankle' + S], m['toe' + S])})
    return {k: (np.asarray(a, float), np.asarray(b, float)) for k, (a, b) in B.items()}


def _sess(name):
    if name not in _S:
        import onnxruntime as ort
        so = ort.SessionOptions(); so.intra_op_num_threads = 1
        _S[name] = ort.InferenceSession(os.path.join(SAM, name), so, providers=['CPUExecutionProvider'])
    return _S[name]


def seg_dist(P, a, b):
    ab = b - a
    tt = np.clip(((P - a) @ ab) / (ab @ ab + 1e-9), 0, 1)
    return np.linalg.norm(P - (a + tt[:, None] * ab), axis=1)


def segment(t):
    ref = t['ref']
    H, W = ref.shape[:2]
    a = ref[..., 3:] / 255.
    rgb = (ref[..., [2, 1, 0]] * a + 235 * (1 - a)).astype(np.float32)
    k = 1024 / max(H, W)
    im = cv2.resize(rgb, (int(round(W * k)), int(round(H * k))), interpolation=cv2.INTER_LINEAR)
    x = np.zeros((1024, 1024, 3), np.float32)
    x[:im.shape[0], :im.shape[1]] = (im - [123.675, 116.28, 103.53]) / [58.395, 57.12, 57.375]
    emb = _sess('vit_b-encoder-quant.onnx').run(None, {'x': x.transpose(2, 0, 1)[None]})[0]
    dec = _sess('vit_b-decoder-quant.onnx')
    B = bones({kk: np.asarray(v, float) for kk, v in t['markers'].items()})
    fig = t['fig_t']
    masks = {}
    for p in PARTS:
        a_, b_ = B[p]
        pos = [a_ + f * (b_ - a_) for f in (.25, .5, .75)] if p != 'head' else [a_ + f * (b_ - a_) for f in (.45, .7)]
        neg = [(B[n][0] + B[n][1]) / 2 for n in NEIGH[p]]
        pts = np.array(pos + neg + [[0, 0]], np.float32) * k
        lab = np.array([1] * len(pos) + [0] * len(neg) + [-1], np.float32)
        out = dec.run(None, {'image_embeddings': emb, 'point_coords': pts[None], 'point_labels': lab[None],
                             'mask_input': np.zeros((1, 1, 256, 256), np.float32), 'has_mask_input': np.zeros(1, np.float32),
                             'orig_im_size': np.array([H, W], np.float32)})
        masks[p] = (out[0][0, 0] > 0) & fig
    # a part's SAM mask is kept only near its own bone (20 cm; head 22 cm): SAM often returns the whole figure
    yy, xx = np.mgrid[0:H, 0:W]
    Pall = np.stack([xx.ravel(), yy.ravel()], 1).astype(np.float64)
    for p in PARTS:
        d = seg_dist(Pall, *B[p]).reshape(H, W)
        masks[p] &= d < (22 if p == 'head' else 20) * t['s']
    # resolve: overlaps by nearest bone; leftovers to the nearest bone
    ys, xs = np.nonzero(fig)
    P = np.stack([xs, ys], 1).astype(np.float64)
    D = np.stack([seg_dist(P, *B[p]) for p in PARTS], 1)
    claim = np.stack([masks[p][ys, xs] for p in PARTS], 1)
    Dc = np.where(claim, D, np.inf)
    lab = np.where(claim.any(1), np.argmin(Dc, 1), np.argmin(D, 1))
    L = np.full((H, W), -1, np.int8)
    L[ys, xs] = lab
    return L, B


# ------------------------------------------------------------------ CLIP
MEAN, STD = np.array([0.48145466, 0.4578275, 0.40821073]), np.array([0.26862954, 0.26130258, 0.27577711])


def embed(px):
    from evolve.puzzle import hygiene as HY
    return HY._img(px)


_EC = {}


def card_emb(pieces):
    """{piece id: embedding}, cached on disk per process-safe file"""
    os.makedirs(CACHE, exist_ok=True)
    out = {}
    for p in pieces:
        if p['id'] in _EC:
            out[p['id']] = _EC[p['id']]; continue
        f = os.path.join(CACHE, p['id'].replace('/', '__') + '.npy')
        if os.path.exists(f):
            e = np.load(f)
        else:
            e = embed(p['px']).astype(np.float32)
            np.save(f + '.%d.npy' % os.getpid(), e); os.replace(f + '.%d.npy' % os.getpid(), f)
        _EC[p['id']] = out[p['id']] = e
    return out


def region_crop(ref, L, i):
    ys, xs = np.nonzero(L == i)
    if len(xs) < 30:
        return None
    x0, y0, x1, y1 = xs.min(), ys.min(), xs.max() + 1, ys.max() + 1
    c = ref[y0:y1, x0:x1].astype(np.float32).copy()
    c[..., 3] *= (L[y0:y1, x0:x1] == i)
    return c
