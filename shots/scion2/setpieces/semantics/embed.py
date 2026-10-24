"""Step 1: CLIP ViT-B/32 image embeddings for every set-piece card (kind 'card') on .props./.set./.hero./.fx. sheets.
Cached to emb_img.npz (ids, emb). Re-running only embeds ids not yet cached.
Image prep copies shots/scion2/evolve/puzzle/hygiene.py: alpha composited onto paper colour, letterboxed to 224."""
import json, os, sys
import numpy as np, cv2
cv2.setNumThreads(1)
HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, '../../../..'))
CUT = os.path.join(ROOT, 'shots/kits/cut')
sys.path.insert(0, os.path.join(ROOT, 'shots/scion2/evolve/puzzle'))
import hygiene as H  # _img, _txt, _sess (intra_op_num_threads=1)

TAGS = ('.props.', '.set.', '.hero.', '.fx.')


def setpieces():
    cat = json.load(open(os.path.join(CUT, 'catalog.json')))['sheets']
    out = []
    for sid, s in cat.items():
        if any(t in sid for t in TAGS):
            for p in s['parts']:
                out.append((sid, p))
    return cat, out


if __name__ == '__main__':
    cache = os.path.join(HERE, 'emb_img.npz')
    have = {}
    if os.path.exists(cache):
        z = np.load(cache, allow_pickle=True)
        have = dict(zip(z['ids'].tolist(), z['emb']))
    cat, parts = setpieces()
    todo = [p for _, p in parts if p['kind'] == 'card' and p['id'] not in have]
    print(len(parts), 'parts;', len(todo), 'to embed', flush=True)
    for i, p in enumerate(todo):
        px = cv2.imread(os.path.join(CUT, p['file']), cv2.IMREAD_UNCHANGED)
        if px is None:
            print('unreadable', p['id']); continue
        if px.ndim == 2: px = cv2.cvtColor(px, cv2.COLOR_GRAY2BGRA)
        if px.shape[2] == 3: px = np.dstack([px, np.full(px.shape[:2], 255, np.uint8)])
        have[p['id']] = H._img(px).astype(np.float32)
        if i % 200 == 199:
            np.savez(cache, ids=np.array(list(have)), emb=np.stack(list(have.values())))
            print(i + 1, flush=True)
    np.savez(cache, ids=np.array(list(have)), emb=np.stack(list(have.values())))
    print('done', len(have))
