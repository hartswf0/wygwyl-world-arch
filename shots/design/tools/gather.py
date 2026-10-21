#!/usr/bin/env python3
"""PRODUCTION DESIGN, STEP 1: what we already have for every set, prop, character and effect a poem needs.

For each poem (shots/poems/breakdown/NN.json) every need is matched, by CLIP (LAION ViT-B/32, text → image), against
  · our generated footage: MARKOV_POET_00, MARKOV_POET, BOY/WN_LEAVE (three frames a clip, averaged);
  · the Atlantis district views (wygwyl/world/districts/v, Midjourney);
  · the found-film archive (15,149 clip thumbnails, the lab's own image embeddings);
and the kit packs already painted for the poem (Character Kits v2). Thumbnails go to design/assets, the findings to
design/data/NN.json. Nothing here comes from the private photography.   anaconda python3 gather.py"""
import os, re, json, glob, hashlib, numpy as np, cv2, torch, open_clip

H = os.path.dirname(os.path.abspath(__file__)); DES = os.path.dirname(H); SHOTS = os.path.dirname(DES)
A = os.path.join(DES, 'assets'); DATA = os.path.join(DES, 'data'); CACHE = os.path.join(H, '.cache')
for d in (A, DATA, CACHE): os.makedirs(d, exist_ok=True)
BH = '/Users/gaia/Downloads/butterfly-halfworld'
LAB = '/Users/gaia/resurrecting atlantis/CINEOSIS_44/lab'
DIST = os.path.join(BH, '.claude/worktrees/hungry-cori-d982c1/wygwyl/world/districts')
KERNEL = '/Users/gaia/cineosis-lab-cels/lab/bets/kernel-data.json'
FILM = os.path.join(DIST, 'tools/.work/story/film.json')
GEN_DIRS = [(os.path.join(BH, 'MARKOV_POET_ARCHIVE-FLY/MARKOV_POET_00/videos'), 'MARKOV_POET_00'),
            (os.path.join(BH, 'MARKOV_POET_ARCHIVE-FLY/MARKOV_POET/videos'), 'MARKOV_POET'),
            ('/Users/gaia/resurrecting atlantis/BOY/WN_LEAVE', 'WN_LEAVE')]
PRIVATE = re.compile(r'(/CAT/|/EYE/|cdmx|thompson)', re.I)                         # never: the private shoot, real-person GPS

dev = 'mps' if torch.backends.mps.is_available() else 'cpu'
M, _, PRE = open_clip.create_model_and_transforms('ViT-B-32', pretrained='laion2b_s34b_b79k'); M = M.to(dev).eval(); TOK = open_clip.get_tokenizer('ViT-B-32')
def enc_text(ts):
    with torch.no_grad(): e = M.encode_text(TOK(ts).to(dev)); return (e / e.norm(dim=-1, keepdim=True)).float().cpu().numpy()
def enc_imgs(ims):
    from PIL import Image
    with torch.no_grad():
        x = torch.stack([PRE(Image.fromarray(cv2.cvtColor(i, cv2.COLOR_BGR2RGB))) for i in ims]).to(dev); e = M.encode_image(x)
        return (e / e.norm(dim=-1, keepdim=True)).float().cpu().numpy()
def thumb(img, name, w=420):
    out = os.path.join(A, name)
    if not os.path.exists(out):
        h = int(img.shape[0] * w / img.shape[1]); cv2.imwrite(out, cv2.resize(img, (w, h), interpolation=cv2.INTER_AREA), [cv2.IMWRITE_JPEG_QUALITY, 80])
    return 'assets/' + name

# ── our generated footage ──
gen_cache = os.path.join(CACHE, 'gen.json'); gen_emb = os.path.join(CACHE, 'gen.npy')
if os.path.exists(gen_cache):
    GEN = json.load(open(gen_cache)); GE = np.load(gen_emb)
else:
    GEN, embs = [], []
    for d, lib in GEN_DIRS:
        for f in sorted(glob.glob(os.path.join(d, '*.mp4'))):
            if PRIVATE.search(f): continue
            cap = cv2.VideoCapture(f); n = int(cap.get(cv2.CAP_PROP_FRAME_COUNT)); fps = cap.get(cv2.CAP_PROP_FPS) or 24; fr = []
            for k in (.25, .5, .75):
                cap.set(cv2.CAP_PROP_POS_FRAMES, int(n * k)); ok, im = cap.read()
                if ok: fr.append(im)
            if not fr: continue
            e = enc_imgs(fr).mean(0); e /= np.linalg.norm(e); key = hashlib.md5(f.encode()).hexdigest()[:10]
            name = re.sub(r'_[0-9a-f]{8}-[0-9a-f-]{27,}.*$', '', os.path.basename(f)).replace('.mp4', '')
            GEN.append({'id': key, 'lib': lib, 'file': os.path.basename(f), 'name': re.sub(r'[_]+', ' ', name)[:90], 'dur': round(n / fps, 1),
                        'thumb': thumb(fr[len(fr) // 2], f'gen_{key}.jpg'), 'path': f}); embs.append(e)
            print(lib, len(GEN), name[:60], flush=True)
    GE = np.stack(embs); json.dump(GEN, open(gen_cache, 'w')); np.save(gen_emb, GE)

# ── the Atlantis district views ──
P = json.load(open(os.path.join(DIST, 'places.json'))); VIEW_D = {}
for d in P['districts']:
    for v in d['views']: VIEW_D.setdefault(v, d['name'])
view_cache = os.path.join(CACHE, 'views.npy')
VIEWS = [{'id': f'v{v:03d}', 'n': v, 'district': VIEW_D.get(v, ''), 'src': f'wygwyl/world/districts/v/{v:03d}.webp'} for v in range(1, 101) if os.path.exists(os.path.join(DIST, 'v', f'{v:03d}.webp'))]
ims = [cv2.imread(os.path.join(DIST, 'v', f"{x['n']:03d}.webp")) for x in VIEWS]
for x, im in zip(VIEWS, ims): x['thumb'] = thumb(im, f"view_{x['n']:03d}.jpg")
VE = np.load(view_cache) if os.path.exists(view_cache) else enc_imgs(ims); np.save(view_cache, VE)

# ── the archive ──
AE = np.load(os.path.join(LAB, 'cache/emb.npy')); AIDS = json.load(open(os.path.join(LAB, 'cache/emb_ids.json'))); CORP = json.load(open(os.path.join(LAB, 'cache/corpus.json')))
def arch_thumb(cid):
    for d in ('thumbs', 'odyssey/thumbs'):
        p = os.path.join(LAB, d, cid + '.jpg')
        if os.path.exists(p): return thumb(cv2.imread(p), f'arch_{cid[:13]}.jpg', 360)

# ── the kit packs already painted (Character Kits v2) ──
KITS = json.load(open(os.path.join(SHOTS, 'arena/parts/kit3/v2/kits.json')))
LINES = json.load(open(KERNEL))['lines']; FILMJ = json.load(open(FILM))

def top(E, q, k):
    s = E @ q; i = np.argsort(-s)[:k]; return [(int(j), float(s[j])) for j in i]
def find(text, k_gen=4, k_view=3, k_arch=5, poem=None):
    q = enc_text([text])[0]; out = {'gen': [], 'views': [], 'archive': []}
    for j, s in top(GE, q, k_gen): g = GEN[j]; out['gen'].append({'id': g['id'], 'name': g['name'], 'lib': g['lib'], 'thumb': g['thumb'], 'score': round(s, 3)})
    for j, s in top(VE, q, k_view): v = VIEWS[j]; out['views'].append({'id': v['id'], 'district': v['district'], 'thumb': v['thumb'], 'score': round(s, 3)})
    seen = set()
    for j, s in top(AE, q, k_arch * 3):
        cid = AIDS[j]; c = CORP.get(cid) or {}; t = c.get('sourceTitle')
        if t in seen: continue
        th = arch_thumb(cid)
        if not th: continue
        seen.add(t); out['archive'].append({'clip': cid, 'title': t, 'year': c.get('sourceYear'), 'thumb': th, 'score': round(s, 3)})
        if len(out['archive']) >= k_arch: break
    return out

for f in sorted(glob.glob(os.path.join(SHOTS, 'poems/breakdown/[0-9][0-9].json'))):
    B = json.load(open(f)); p = B['num']; nd = B.get('needs', {})
    poem_lines = [{'id': l['id'], 't0': l['t0'], 't1': l['t1'], 'text': l['text']} for l in LINES if str(l['film']).zfill(2) == p and l.get('text')]
    sets = [{'id': s['id'], 'what': s['what'], 'found': find(f"{s['what']}", 5, 4, 6)} for s in B.get('sets', [])]
    props = [{**pr, 'found': find(f"{pr['what']}", 3, 0, 5)} for pr in nd.get('props', [])]
    fx = [{'id': x, 'found': find(x.replace('_', ' '), 2, 0, 3)} for x in nd.get('fx', [])[:12]]
    kp = next((x for x in KITS['poems'] if x['num'] == p), {})
    chars = []
    for ch in kp.get('characters', []):
        cast = next((c for c in KITS['cast'] if c['id'] == ch['id']), {})
        chars.append({'id': ch['id'], 'name': ch.get('name'), 'costumes': ch.get('costumes'), 'who': cast.get('who'),
                      'action_sheet': ('../arena/parts/kit3/' + ch['action']['image']) if ch.get('action') else None,
                      'packs': [('../arena/parts/kit3/' + pk['image']) for c in cast.get('costumes', []) if c['costume'] in (ch.get('costumes') or []) for pk in c.get('packs', [])]})
    in_film = [{'id': s.get('id'), 'scene': s.get('scene'), 'name': s.get('name'), 'source': s.get('source'), 'what': s.get('what'), 'district': s.get('d')}
               for s in FILMJ.get(p, {}).get('shots', [])]
    data = {'num': p, 'title': B['title'], 'style': B.get('style'), 'pages': B.get('pages'), 'lines': poem_lines,
            'scenes': [{'id': s['id'], 'movement': s.get('movement'), 'seconds': s.get('seconds'), 'lines': s.get('lines'), 'treatment': s.get('treatment'),
                        'shots': [{'id': sh['id'], 'framing': sh.get('framing'), 'set': sh.get('set'), 'action': sh.get('action'),
                                   'bodies': [{k: b.get(k) for k in ('role', 'costume', 'view', 'pose', 'action', 'expression', 'hands')} for b in sh.get('bodies', [])],
                                   'props': sh.get('props'), 'fx': sh.get('fx')} for sh in s.get('shots', [])]} for s in B.get('scenes', [])],
            'needs': nd, 'sets': sets, 'props': props, 'fx': fx, 'characters': chars, 'scene_book': in_film}
    json.dump(data, open(os.path.join(DATA, f'{p}.json'), 'w'), indent=1, ensure_ascii=False)
    print(p, B['title'], len(sets), 'sets', len(props), 'props', len(chars), 'characters', flush=True)
