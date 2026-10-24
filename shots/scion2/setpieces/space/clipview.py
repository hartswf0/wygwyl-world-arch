"""SPACE step 2: CLIP ViT-B/32 zero-shot scores for VIEW and DEPTH cues.

Image embeddings are NOT recomputed: they are a snapshot of the semantics swarm's cache
(shots/scion2/setpieces/semantics/emb_img.npz, alpha composited on paper colour, letterboxed 224), copied to
cache/emb_img.npz so this run is reproducible even if that file changes. Text embeddings use
shots/scion2/evolve/puzzle/hygiene.py (_txt, onnxruntime intra_op_num_threads=1).
Output cache/clip.json: id -> {'view': {class: softmax p}, 'depth': {class: softmax p}}  (softmax at temperature 100).
"""
import json, os, shutil, sys
import numpy as np
HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, '../../../..'))
sys.path.insert(0, os.path.join(ROOT, 'shots/scion2/evolve/puzzle'))
import hygiene as Hy

PFX = 'a painted paper cut-out: '
VIEW = {
    'front': ['a flat front elevation of an object seen straight on', 'a building facade seen straight from the front, flat',
              'a door seen flat from the front'],
    '3/4': ['an object seen at a three-quarter angle, showing its front and one side',
            'a piece of furniture drawn in three-quarter view', 'a house seen from a corner angle'],
    'side': ['a side profile view of an object', 'a vehicle seen exactly from the side', 'an object in side elevation'],
    'top': ['a top-down plan view seen from directly above', 'a floor or map seen from overhead',
            'an object photographed from directly above'],
    'scene': ['a painted landscape scene with perspective depth and a horizon',
              'a wide painted backdrop showing a whole street receding into the distance',
              'an interior room drawn in perspective'],
}
DEPTH = {
    'sky': ['a sky with clouds', 'a night sky', 'a distant skyline silhouette'],
    'ground': ['a strip of ground or floor', 'a road surface', 'water surface seen at a low angle'],
    'building': ['a building', 'a wall', 'a doorway'],
    'object': ['a single small object', 'a piece of furniture', 'a household prop'],
    'foliage': ['a leafy branch hanging into the frame', 'a plant', 'a tree'],
    'glow': ['soft glowing light and haze', 'a beam of light', 'smoke or mist'],
}


def emb(d):
    return {k: Hy._txt([PFX + t for t in v]).mean(0) for k, v in d.items()}


if __name__ == '__main__':
    src = os.path.join(ROOT, 'shots/scion2/setpieces/semantics/emb_img.npz')
    dst = os.path.join(HERE, 'cache', 'emb_img.npz')
    if not os.path.exists(dst):
        shutil.copy(src, dst)
    z = np.load(dst, allow_pickle=True)
    ids, E = z['ids'].tolist(), z['emb']
    out = {}
    for name, d in (('view', VIEW), ('depth', DEPTH)):
        T = emb(d)
        ks = list(T)
        M = np.stack([T[k] / np.linalg.norm(T[k]) for k in ks])
        S = 100 * E @ M.T
        P = np.exp(S - S.max(1, keepdims=True)); P /= P.sum(1, keepdims=True)
        for i, pid in enumerate(ids):
            out.setdefault(pid, {})[name] = {k: round(float(P[i, j]), 3) for j, k in enumerate(ks)}
    json.dump({'prompts': {'prefix': PFX, 'view': VIEW, 'depth': DEPTH}, 'parts': out},
              open(os.path.join(HERE, 'cache', 'clip.json'), 'w'))
    print('scored', len(out))
