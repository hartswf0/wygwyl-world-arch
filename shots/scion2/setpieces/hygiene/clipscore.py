"""Pass 2: CLIP zero-shot scores per set piece from the cached image embeddings. Writes cache/clip_scores.json.
Prompt groups (each a max over its prompts):
  text      printed captions / title lettering / label strips
  refsheet  a reference sheet / diagram / several drawings
  person    a person, face, hand, body part (a character baked into the piece)
  scrap     a blank scrap, a torn sliver, a thin line
  object    generic single painted objects / scenery (the baseline the others must beat)
  label     the part's own label ('a painted paper cut-out of <label>'), and its rank among all labels of the same sheet
"""
import json, os, re, sys
import numpy as np
from common import setpieces, CACHE, HERE
sys.path.insert(0, os.path.join(HERE, '..', '..', 'evolve', 'puzzle'))
import hygiene as H

P0 = 'a painted paper cut-out: '
G = {
    'text': ['printed text, a caption label with words', 'a strip of printed letters', 'a title in large black capital letters',
             'a printed reference number and label', 'handwritten notes and annotations'],
    'refsheet': ['a reference sheet with several small drawings and labels', 'a diagram with arrows and labels',
                 'a grid of many small separate objects', 'a model sheet showing the same object several times'],
    'person': ['a person', 'a man standing', 'a woman', 'a human face', 'a human hand', 'a human arm',
               'a person sitting in a chair', 'a silhouette of a person', 'a puppet body part, a limb with a joint'],
    'scrap': ['a blank scrap of white paper', 'a thin sliver of paper', 'a thin line', 'an empty white rectangle'],
    'object': ['a piece of furniture', 'a building facade', 'a door', 'a window', 'a wall', 'a tree', 'a plant with leaves',
               'a lamp', 'a household object', 'a tool', 'a vehicle', 'a cloud', 'the moon', 'smoke', 'a rock',
               'a stone arch', 'a wooden plank', 'a metal machine part', 'a flower', 'a sign board', 'a staircase',
               'a road', 'water waves', 'a light beam', 'a mug', 'a box', 'a book', 'a bottle', 'a clock', 'a boat'],
}


def clean_label(p):
    s = p.get('name') or p.get('label') or ''
    s = re.sub(r'\b[A-Z]?\d+[A-Z]?\b|\(.*?\)|[_.\-]', ' ', s)
    s = re.sub(r'\s+', ' ', s).strip().lower()
    if len(re.findall(r'[a-z]{3,}', s)) == 0:
        s = re.sub(r'[-_]', ' ', p['id'].split('/')[1]).lower()
        s = re.sub(r'\bpart\b|\d+', ' ', s).strip()
    return s


def main():
    P = {p['id']: p for p in setpieces()}
    ids = json.load(open(os.path.join(CACHE, 'clip_ids.json')))
    E = np.load(os.path.join(CACHE, 'clip_img.npy'))
    T = {k: H._txt([P0 + t for t in v]) for k, v in G.items()}
    labs = {i: clean_label(P[i]) for i in ids}
    uniq = sorted(set(labs.values()))
    LT = H._txt([P0 + (u or 'an object') for u in uniq])
    li = {u: j for j, u in enumerate(uniq)}
    out = {}
    for k, i in enumerate(ids):
        e = E[k]
        r = {}
        for g, t in T.items():
            s = t @ e
            r[g] = round(float(s.max()), 4)
            r[g + '_best'] = G[g][int(s.argmax())]
        ls = LT @ e
        own = float(ls[li[labs[i]]])
        r['label_text'] = labs[i]
        r['label_sim'] = round(own, 4)
        r['label_pct'] = round(float((ls < own).mean()), 3)   # share of all set-piece labels this image matches less well
        out[i] = r
    json.dump(out, open(os.path.join(CACHE, 'clip_scores.json'), 'w'))
    print(len(out))


if __name__ == '__main__':
    main()
