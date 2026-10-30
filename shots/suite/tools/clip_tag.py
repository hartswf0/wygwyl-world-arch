"""Zero-shot CLIP tags for cut cards (OpenCLIP ViT-B-32 laion2b, local weights, offline).

    python3 shots/suite/tools/clip_tag.py <workdir>    # reads <workdir>/cuts.json, writes <workdir>/clip.json

Used only where a sheet's layout cannot name a card (counts do not match the layout and the
prompt has no numbered list), and to drop cards that are printed text, rulers or proof figures.
"""
import json, os, sys
os.environ.setdefault('HF_HUB_OFFLINE', '1')
import numpy as np
import torch
import open_clip
from PIL import Image

LABELS = {
    'hand': 'a cardboard cut-out of a single human hand',
    'head': 'a cardboard cut-out of a human head',
    'foot': 'a cardboard cut-out of a single shoe or boot or bare foot',
    'eye': 'a cardboard cut-out of a pair of eyes',
    'mouth': 'a cardboard cut-out of a mouth with lips',
    'brow': 'a cardboard cut-out of a pair of eyebrows',
    'nose': 'a cardboard cut-out of a nose',
    'glasses': 'a cardboard cut-out of sunglasses',
    'torso': 'a cardboard cut-out of a sleeveless shirt or jacket torso',
    'pelvis': 'a cardboard cut-out of shorts or a hip piece',
    'limb': 'a long capsule-shaped cardboard arm or leg segment with brass brads at both ends',
    'replacement': 'a cardboard cut-out puppet of a whole human figure in a pose',
    'wing': 'a cardboard cut-out of a feathered wing',
    'prop': 'a cardboard cut-out of an object',
    'text': 'black printed text on white paper',
}


WORDP = ['large printed letters forming a word', 'a small line of printed text or a caption',
         'a painted cardboard puppet part', 'a painted object or picture']


def tag_files(files, cache_path):
    """Tags for any list of card files (cached in cache_path)."""
    out = json.load(open(cache_path)) if os.path.exists(cache_path) else {}
    todo = [f for f in files if f not in out]
    if todo:
        dev = 'mps' if torch.backends.mps.is_available() else 'cpu'
        model, _, pre = open_clip.create_model_and_transforms('ViT-B-32', pretrained='laion2b_s34b_b79k', device=dev)
        tok = open_clip.get_tokenizer('ViT-B-32')
        keys = list(LABELS)
        with torch.no_grad():
            T = model.encode_text(tok([LABELS[k] for k in keys]).to(dev))
            T = T / T.norm(dim=-1, keepdim=True)
            for i in range(0, len(todo), 64):
                ims = []
                for f in todo[i:i + 64]:
                    im = Image.open(f).convert('RGBA')
                    bg = Image.new('RGBA', im.size, (255, 255, 255, 255))
                    ims.append(pre(Image.alpha_composite(bg, im).convert('RGB')))
                X = model.encode_image(torch.stack(ims).to(dev))
                X = X / X.norm(dim=-1, keepdim=True)
                P = (100 * X @ T.T).softmax(-1).cpu().numpy()
                for f, p in zip(todo[i:i + 64], P):
                    out[f] = {k: round(float(v), 3) for k, v in zip(keys, p)}
        json.dump(out, open(cache_path, 'w'))
    return out


def main(work):
    C = json.load(open(os.path.join(work, 'cuts.json')))
    out_p = os.path.join(work, 'clip.json')
    out = json.load(open(out_p)) if os.path.exists(out_p) else {}
    files = [p['abs'] for r in C.values() for p in r.get('parts', []) if p['abs'] not in out or 'wordness' not in out[p['abs']]]
    dev = 'mps' if torch.backends.mps.is_available() else 'cpu'
    model, _, pre = open_clip.create_model_and_transforms('ViT-B-32', pretrained='laion2b_s34b_b79k', device=dev)
    tok = open_clip.get_tokenizer('ViT-B-32')
    keys = list(LABELS)
    with torch.no_grad():
        T = model.encode_text(tok([LABELS[k] for k in keys]).to(dev))
        T = T / T.norm(dim=-1, keepdim=True)
        T2 = model.encode_text(tok(WORDP).to(dev))
        T2 = T2 / T2.norm(dim=-1, keepdim=True)
        for i in range(0, len(files), 64):
            ims = []
            for f in files[i:i + 64]:
                im = Image.open(f).convert('RGBA')
                bg = Image.new('RGBA', im.size, (255, 255, 255, 255))
                ims.append(pre(Image.alpha_composite(bg, im).convert('RGB')))
            X = model.encode_image(torch.stack(ims).to(dev))
            X = X / X.norm(dim=-1, keepdim=True)
            P = (100 * X @ T.T).softmax(-1).cpu().numpy()
            P2 = (100 * X @ T2.T).softmax(-1).cpu().numpy()
            for f, p, q in zip(files[i:i + 64], P, P2):
                out[f] = {k: round(float(v), 3) for k, v in zip(keys, p)}
                out[f]['wordness'] = round(float(q[:2].sum()), 3)
            print(i, len(files), flush=True)
    json.dump(out, open(out_p, 'w'))


if __name__ == '__main__':
    main(sys.argv[1])
