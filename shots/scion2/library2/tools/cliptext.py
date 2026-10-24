"""CLIP zero-shot against the cached card embeddings (emb.npy, library.json order). Weights live in CLIP_DIR."""
import os, sys
import numpy as np
import common as C

CLIP = os.environ.get('CLIP_DIR', '/tmp/claude-0/clip')
P = 'a paper cut-out puppet piece: '
_s = {}


def _init():
    if 'E' in _s:
        return
    sys.path.insert(0, CLIP)
    sys.path.insert(0, os.path.join(C.SHOTS, 'skinlab'))
    import onnxruntime as ort
    from clip_label import tokens
    _s['tok'] = tokens
    _s['txt'] = ort.InferenceSession(os.path.join(CLIP, 'textual.onnx'), providers=['CPUExecutionProvider'])
    E = np.load(os.path.join(CLIP, 'emb.npy')).astype(np.float32)
    _s['E'] = E / np.linalg.norm(E, axis=1, keepdims=True)
    _s['row'] = {c['id']: i for i, c in enumerate(C.cards())}


def text(prompts):
    _init()
    t = _s['txt'].run(None, {'input': _s['tok'](prompts)})[0]
    return t / np.linalg.norm(t, axis=1, keepdims=True)


def zero_shot(card_id, classes):
    """classes: {name: [prompts]} -> {name: prob}"""
    _init()
    if card_id not in _s['row']:
        return None
    e = _s['E'][_s['row'][card_id]]
    names = list(classes)
    ck = tuple((n, tuple(classes[n])) for n in names)
    if ck not in _s.setdefault('T', {}):
        T = np.stack([text([P + p for p in classes[n]]).mean(0) for n in names])
        _s['T'][ck] = T / np.linalg.norm(T, axis=1, keepdims=True)
    T = _s['T'][ck]
    z = 100 * T @ e
    p = np.exp(z - z.max()); p /= p.sum()
    return dict(zip(names, p.round(3).tolist()))
