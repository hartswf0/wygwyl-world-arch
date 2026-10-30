#!/usr/bin/env python3
"""SETS, STEP 1: every scene's candidate plates, ranked.

For each scene in shots/poems/breakdown/NN.json the primary set is the set most of its shots use. Its candidate plates:
  · the design dossier's `plate` for that set (shots/design/data/NN.design.json), when it is a gen clip or an Atlantis view;
  · the dossier's CLIP finds for that set (design/data/NN.json `found`: top gen clips and views);
  · the Atlantis view the stage manifest already gave the scene (release_v2/wygwyl_atlas_manifest.json world_backdrop),
    which has the full analyze.py pass (DepthPro depth, OneFormer ADE20K, ground plane, horizon) in shots/out/<id>/.
Full-resolution sources: gen clip -> 5 frames from the mp4 (the frame with fewest people is chosen in step 2);
view NNN -> wygwyl/world/districts/v/NNN.webp (matched to shots/out/<id> when it is the same Midjourney image).
Each candidate is scored by CLIP (LAION ViT-B/32) against the set text.  anaconda python3 sets_candidates.py <work_dir>
Nothing here reads the private photography (paths are checked)."""
import os, re, sys, json, glob, collections
import numpy as np, cv2, torch, open_clip
from PIL import Image

SUITE = os.path.dirname(os.path.dirname(os.path.abspath(__file__))); SH = os.path.dirname(SUITE)
WORK = sys.argv[1] if len(sys.argv) > 1 else os.path.join(SUITE, '.work')
os.makedirs(os.path.join(WORK, 'src'), exist_ok=True)
BH = '/Users/gaia/Downloads/butterfly-halfworld'
DIST = os.path.join(BH, '.claude/worktrees/hungry-cori-d982c1/wygwyl/world/districts')
GEN_JSON = '/Users/gaia/Downloads/WYGWYL-WORLD-ARCH-kits/shots/design/tools/.cache/gen.json'
PRIVATE = re.compile(r'(/CAT/|/EYE/|cdmx|thompson|wygwyl-private)', re.I)

dev = 'mps' if torch.backends.mps.is_available() else 'cpu'
M, _, PRE = open_clip.create_model_and_transforms('ViT-B-32', pretrained='laion2b_s34b_b79k'); M = M.to(dev).eval()
TOK = open_clip.get_tokenizer('ViT-B-32')
def enc_text(ts):
    with torch.no_grad(): e = M.encode_text(TOK(ts).to(dev)); return (e / e.norm(dim=-1, keepdim=True)).float().cpu().numpy()
def enc_img(paths):
    with torch.no_grad():
        x = torch.stack([PRE(Image.open(p).convert('RGB')) for p in paths]).to(dev); e = M.encode_image(x)
        return (e / e.norm(dim=-1, keepdim=True)).float().cpu().numpy()

GEN = {g['id']: g for g in json.load(open(GEN_JSON))}
MAN = json.load(open(os.path.join(SH, 'arena/parts/kit3/release_v2/wygwyl_atlas_manifest.json')))
MSCENE = {s['scene_num']: s for s in MAN['scenes']}
OUTS = {os.path.basename(p)[:8] + os.path.basename(p)[-2:]: os.path.basename(p) for p in glob.glob(os.path.join(SH, 'out', '*')) if os.path.isdir(p)}

# views <-> analysed shots (same Midjourney image at a different size?)
def tiny(p):
    im = cv2.imread(p, cv2.IMREAD_GRAYSCALE); im = cv2.resize(im, (64, 36), interpolation=cv2.INTER_AREA).astype(np.float32)
    return (im - im.mean()) / (im.std() + 1e-6)
out_tiny = {k: tiny(os.path.join(SH, 'out', v, 'image.jpg')) for k, v in OUTS.items() if os.path.exists(os.path.join(SH, 'out', v, 'image.jpg'))}
VIEW2OUT = {}
for p in sorted(glob.glob(os.path.join(DIST, 'v', '*.webp'))):
    n = int(os.path.basename(p)[:3]); t = tiny(p)
    best = max(out_tiny.items(), key=lambda kv: float((kv[1] * t).mean()))
    if float((best[1] * t).mean()) > 0.9: VIEW2OUT[n] = best[0]

def gen_frames(gid):
    g = GEN.get(gid)
    if not g or PRIVATE.search(g['path']) or not os.path.exists(g['path']): return []
    out = []
    cap = cv2.VideoCapture(g['path']); n = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    for k in (.1, .3, .5, .7, .9):
        f = os.path.join(WORK, 'src', f'gen_{gid}_{int(k*100):02d}.jpg')
        if not os.path.exists(f):
            cap.set(cv2.CAP_PROP_POS_FRAMES, int(n * k)); ok, im = cap.read()
            if not ok: continue
            cv2.imwrite(f, im, [cv2.IMWRITE_JPEG_QUALITY, 93])
        out.append(f)
    return out

def cand_from_thumb(thumb, origin, score=None):
    m = re.match(r'assets/(gen|view)_(\w+)\.jpg', thumb or '')
    if not m: return None
    kind, key = m.groups()
    if kind == 'gen':
        fr = gen_frames(key)
        if not fr: return None
        g = GEN[key]
        return dict(id=f'gen_{key}', kind='gen', frames=fr, origin=[origin], dossier_score=score,
                    provenance=dict(ledger='INVENTED', lib=g['lib'], file=g['file'], name=g['name']))
    n = int(key); src = os.path.join(DIST, 'v', f'{n:03d}.webp')
    if not os.path.exists(src): return None
    ok = VIEW2OUT.get(n)
    if ok: return dict(id=f'world_{ok}', kind='world', frames=[os.path.join(SH, 'out', OUTS[ok], 'image.jpg')], out_id=OUTS[ok],
                       origin=[origin], dossier_score=score, view=n,
                       provenance=dict(ledger='INVENTED', lib='Atlantis (Midjourney)', file=f'out/{OUTS[ok]}/image.jpg', view=n))
    return dict(id=f'view_{n:03d}', kind='view', frames=[src], origin=[origin], dossier_score=score, view=n,
                provenance=dict(ledger='INVENTED', lib='Atlantis (Midjourney)', file=f'wygwyl/world/districts/v/{n:03d}.webp'))

scenes = []
for n in range(1, 15):
    B = json.load(open(os.path.join(SH, f'poems/breakdown/{n:02d}.json')))
    DD = json.load(open(os.path.join(SH, f'design/data/{n:02d}.design.json')))
    DF = json.load(open(os.path.join(SH, f'design/data/{n:02d}.json')))
    bsets = {s['id']: s for s in B['sets']}; dsets = {s['id']: s for s in DD['sets']}; fsets = {s['id']: s for s in DF['sets']}
    arch_q = []
    for r in DD.get('references', []):
        if 'rchive' in r.get('what', ''): arch_q += re.findall(r"'([^']{3,80})'", r.get('look_for', ''))
    for sc in B['scenes']:
        sets = collections.Counter(sh.get('set') for sh in sc['shots'] if sh.get('set'))
        sid = sets.most_common(1)[0][0] if sets else None
        cams = collections.Counter(sh.get('camera') for sh in sc['shots']); frs = collections.Counter(sh.get('framing') for sh in sc['shots'])
        text = (bsets.get(sid, {}).get('what') or sid or '')
        ds = dsets.get(sid, {})
        cands = {}
        def add(c):
            if not c: return
            if c['id'] in cands: cands[c['id']]['origin'] += c['origin']
            else: cands[c['id']] = c
        if ds.get('plate'): add(cand_from_thumb(ds['plate'], 'dossier_plate'))
        for r in ds.get('refs', []) or []: add(cand_from_thumb(r, 'dossier_ref'))
        fs = fsets.get(sid, {}).get('found', {})
        for g in (fs.get('gen') or [])[:3]: add(cand_from_thumb(g.get('thumb'), 'dossier_found_gen', g.get('score')))
        for v in (fs.get('views') or [])[:3]: add(cand_from_thumb(v.get('thumb'), 'dossier_found_view', v.get('score')))
        wb = (MSCENE.get(sc['id']) or {}).get('world_backdrop') or {}
        k = wb.get('world_shot_k')
        if k and k in OUTS:
            add(dict(id=f'world_{k}', kind='world', frames=[os.path.join(SH, 'out', OUTS[k], 'image.jpg')], out_id=OUTS[k], origin=['stage_manifest'],
                     dossier_score=None, provenance=dict(ledger='INVENTED', lib='Atlantis (Midjourney)', file=f'out/{OUTS[k]}/image.jpg',
                                                         district=wb.get('district_name'))))
        scenes.append(dict(scene_id=sc['id'], poem=f'{n:02d}', title=B['title'], movement=sc.get('movement'), seconds=sc.get('seconds'),
                           lines=sc.get('lines'), set=sid, sets_used=dict(sets), set_what=text, camera=cams.most_common(1)[0][0],
                           framing=frs.most_common(1)[0][0], design=ds, archive_queries=arch_q,
                           passage=DF.get('passage'),
                           candidates=list(cands.values())))

# CLIP: every candidate frame vs its scene's set text
allf = sorted({f for s in scenes for c in s['candidates'] for f in c['frames']})
E = {}
for i in range(0, len(allf), 32):
    for f, e in zip(allf[i:i+32], enc_img(allf[i:i+32])): E[f] = e
for s in scenes:
    t = enc_text([f"a photograph of {s['set_what']}", f"{s['set'] or ''}".replace('_', ' ')])
    for c in s['candidates']:
        sims = [float(E[f] @ t[0]) for f in c['frames']]
        c['clip_frames'] = [round(x, 4) for x in sims]; c['clip'] = round(max(sims), 4)
    s['candidates'].sort(key=lambda c: -c['clip'])
json.dump(dict(view2out=VIEW2OUT, scenes=scenes), open(os.path.join(WORK, 'candidates.json'), 'w'), indent=1)
print(len(scenes), 'scenes;', len(allf), 'candidate frames;', len(VIEW2OUT), 'views matched to analysed shots')
for s in scenes: print(s['scene_id'], s['set'], [(c['id'], c['clip'], c['origin'][0]) for c in s['candidates'][:4]])
