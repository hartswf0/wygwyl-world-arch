#!/usr/bin/env python3
"""per poem: a labelled sheet of the generated clips and district views closest to the whole poem (its treatment and sets), for review. → tools/.cache/sheet_NN.jpg; adds 'poem_gen' and 'poem_views' to data/NN.json"""
import os, json, glob, numpy as np, cv2, torch, open_clip
H = os.path.dirname(os.path.abspath(__file__)); DES = os.path.dirname(H); C = os.path.join(H, '.cache')
GEN = json.load(open(os.path.join(C, 'gen.json'))); GE = np.load(os.path.join(C, 'gen.npy')); VE = np.load(os.path.join(C, 'views.npy'))
VIEWS = sorted(glob.glob(os.path.join(DES, 'assets', 'view_*.jpg')))
M, _, _ = open_clip.create_model_and_transforms('ViT-B-32', pretrained='laion2b_s34b_b79k'); M.eval(); TOK = open_clip.get_tokenizer('ViT-B-32')
def enc(ts):
    with torch.no_grad(): e = M.encode_text(TOK(ts)); return (e / e.norm(dim=-1, keepdim=True)).numpy()
for f in sorted(glob.glob(os.path.join(DES, 'data', '[0-9][0-9].json'))):
    d = json.load(open(f)); texts = [s['what'] for s in d['sets']] + [(s.get('treatment') or '')[:300] for s in d['scenes']] + [l['text'] for l in d['lines']]
    Q = enc([t for t in texts if t]); sg = (GE @ Q.T).max(1); sv = (VE @ Q.T).max(1)
    gi = np.argsort(-sg)[:20]; vi = np.argsort(-sv)[:8]
    d['poem_gen'] = [{'id': GEN[j]['id'], 'name': GEN[j]['name'], 'lib': GEN[j]['lib'], 'dur': GEN[j]['dur'], 'thumb': GEN[j]['thumb'], 'score': round(float(sg[j]), 3)} for j in gi]
    d['poem_views'] = [{'thumb': 'assets/' + os.path.basename(VIEWS[j]), 'score': round(float(sv[j]), 3)} for j in vi]
    json.dump(d, open(f, 'w'), indent=1, ensure_ascii=False)
    tiles = []
    for k, x in enumerate(d['poem_gen'] + d['poem_views']):
        im = cv2.imread(os.path.join(DES, x['thumb'])); im = cv2.resize(im, (320, 180)); lab = f"G{k}" if k < 20 else f"V{k - 20}"
        cv2.rectangle(im, (0, 0), (320, 24), (0, 0, 0), -1); cv2.putText(im, f"{lab} {x.get('name', x['thumb'][7:])[:30]}", (4, 17), 0, .45, (0, 255, 255), 1); tiles.append(im)
    while len(tiles) % 7: tiles.append(np.zeros_like(tiles[0]))
    cv2.imwrite(os.path.join(C, f"sheet_{d['num']}.jpg"), np.vstack([np.hstack(tiles[k:k + 7]) for k in range(0, len(tiles), 7)]), [cv2.IMWRITE_JPEG_QUALITY, 82])
    print(d['num'], 'sheet')
