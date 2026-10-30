#!/usr/bin/env python3
"""archive_grab — pull found film into a set: a text query -> archive clips, or -> segmented archive objects as RGBA cut-outs.

    from archive_grab import Grab
    g = Grab()
    g.clips('a lit window at night, 1950s apartment', k=8)          # [{clip, title, year, score, thumb, thumb_url, video_url, t0, t1}]
    g.clips('choir', years=(1930, 1960))
    g.objects('a man walking in a coat', k=6, kinds=('figure',))    # segmented objects ('citizen' cut-outs), ranked
    g.cutout(obj, 'out.png')                                        # tight RGBA crop + provenance in PNG text chunks
    g.labelled(obj, 'out_tagged.png')                               # same, with the visible ARCHIVE tag strip under it

Search is CLIP (LAION ViT-B/32, the same model as the lab's thumbnail embeddings `cache/emb.npy`):
  · clips: text embedding vs the 15,149 clip-thumbnail embeddings (cosine).
  · objects: text embedding vs image embeddings of every segmented archive object (cutouts_clean.json: 205 objects;
    segments_odyssey.json + segments.json: ~1,700 tracked objects), computed once and cached in
    ~/.cache/wygwyl_archive_grab/, blended 0.8/0.2 with a CLIP text match on the object's own label/description.
Every result carries provenance (clip id, film title, year, source times, video URL) and the ledger word OBSERVED
(it is found film), so a set can tag it for as long as it is on screen (the WEAVE 'citizen' rule).

CLI:  python3 archive_grab.py clips "query" [k]   |   python3 archive_grab.py objects "query" [k] [outdir]
Needs: numpy, torch, open_clip, Pillow (anaconda python3). Reads the lab at $WYGWYL_LAB (default below); nothing private."""
import os, sys, json, re
import numpy as np

LAB = os.environ.get('WYGWYL_LAB', '/Users/gaia/resurrecting atlantis/CINEOSIS_44/lab')
CACHE = os.path.expanduser(os.environ.get('ARCHIVE_GRAB_CACHE', '~/.cache/wygwyl_archive_grab'))
PRIVATE = re.compile(r'(/CAT/|/EYE/|cdmx|thompson|wygwyl-private)', re.I)


class Grab:
    def __init__(self, lab=LAB, device=None):
        import torch, open_clip
        self.lab = lab; self.torch = torch
        self.dev = device or ('mps' if torch.backends.mps.is_available() else 'cpu')
        self.M, _, self.PRE = open_clip.create_model_and_transforms('ViT-B-32', pretrained='laion2b_s34b_b79k')
        self.M = self.M.to(self.dev).eval(); self.TOK = open_clip.get_tokenizer('ViT-B-32')
        self._corpus = self._E = self._ids = None; self._objs = self._OE = self._OT = None

    # ── encoders ──
    def text(self, ts):
        ts = [ts] if isinstance(ts, str) else ts
        with self.torch.no_grad():
            e = self.M.encode_text(self.TOK(ts).to(self.dev))
            return (e / e.norm(dim=-1, keepdim=True)).float().cpu().numpy()

    def images(self, ims):
        with self.torch.no_grad():
            x = self.torch.stack([self.PRE(im) for im in ims]).to(self.dev); e = self.M.encode_image(x)
            return (e / e.norm(dim=-1, keepdim=True)).float().cpu().numpy()

    # ── clips ──
    def _load_clips(self):
        if self._E is None:
            self._E = np.load(os.path.join(self.lab, 'cache/emb.npy')).astype(np.float32)
            self._E /= np.linalg.norm(self._E, axis=1, keepdims=True) + 1e-8
            self._ids = json.load(open(os.path.join(self.lab, 'cache/emb_ids.json')))
            self._corpus = json.load(open(os.path.join(self.lab, 'cache/corpus.json')))
            self._extra = {}                                   # odyssey clips that are not in the 15,149 corpus
            lp = os.path.join(self.lab, 'odyssey/library.json')
            if os.path.exists(lp):
                for s in json.load(open(lp)).get('shots', []):
                    if s.get('kind') == 'archive': self._extra[s['id']] = dict(sourceTitle=s.get('title'), sourceYear=s.get('year'), videoUrl=s.get('video'),
                                                                           thumbnailUrl=s.get('thumb'), startSeconds=s.get('st'), endSeconds=(s.get('st') or 0) + (s.get('dur') or 0))
            fp = os.path.join(self.lab, 'odyssey/cache/found.before-render.json')
            if os.path.exists(fp):
                for cid, s in json.load(open(fp)).get('clips', {}).items():
                    self._extra.setdefault(cid, dict(sourceTitle=s.get('title'), sourceYear=s.get('year'), videoUrl=s.get('video'),
                                                     thumbnailUrl=s.get('thumb') if str(s.get('thumb', '')).startswith('http') else None))

    def clip_record(self, cid, score=None):
        self._load_clips(); c = self._corpus.get(cid) or self._extra.get(cid, {})
        th = next((p for p in (os.path.join(self.lab, 'thumbs', cid + '.jpg'), os.path.join(self.lab, 'odyssey/thumbs', cid + '.jpg')) if os.path.exists(p)), None)
        return dict(clip=cid, title=c.get('sourceTitle'), year=c.get('sourceYear'), score=None if score is None else round(float(score), 4),
                    thumb=th, thumb_url=c.get('thumbnailUrl'), video_url=c.get('videoUrl'),
                    t0=c.get('startSeconds'), t1=c.get('endSeconds'), color=c.get('colorMode'), ledger='OBSERVED',
                    tag=f"ARCHIVE · {c.get('sourceTitle') or 'untitled clip ' + cid[:8]}" + (f" ({c.get('sourceYear')})" if c.get('sourceYear') else ''))

    def clips(self, query, k=8, years=None, exclude=(), negative=None):
        """query: str or list of str (averaged). negative: optional str whose similarity is subtracted (x0.5)."""
        self._load_clips()
        q = self.text(query if isinstance(query, list) else [query]).mean(0); q /= np.linalg.norm(q)
        s = self._E @ q
        if negative: s = s - 0.5 * (self._E @ self.text([negative])[0])
        out = []
        for i in np.argsort(-s):
            cid = self._ids[i]
            if cid in exclude: continue
            c = self._corpus.get(cid, {})
            if years and not (c.get('sourceYear') and years[0] <= c['sourceYear'] <= years[1]): continue
            out.append(self.clip_record(cid, s[i]))
            if len(out) >= k: break
        return out

    # ── segmented objects ──
    def _load_objects(self):
        if self._objs is not None: return
        objs = []
        cc = json.load(open(os.path.join(self.lab, 'cache/cutouts_clean.json')))
        for cid, lst in cc.items():
            for j, o in enumerate(lst):
                objs.append(dict(id=f'{cid}#c{j}', clip=cid, src='cutouts_clean', kind='person' if o['label'] in ('person', 'child', 'face') else 'object',
                                 label=o['label'], desc=o['label'], p=o.get('p'), png=o['png'], bbox=o.get('bbox'), area=o.get('area'),
                                 sprite=None, t=None))
        for fn in ('segments.json', 'segments_odyssey.json'):
            p = os.path.join(self.lab, 'cache', fn)
            if not os.path.exists(p): continue
            for cid, v in json.load(open(p)).items():
                for o in v.get('objects', []):
                    t = (v.get('t0') or 0) + (v.get('read_idx') or 0) / max(1, v.get('fps') or 6)
                    objs.append(dict(id=f"{cid}#s{o['k']}", clip=cid, src=fn.replace('.json', ''), kind=o.get('role'), label=o.get('label'),
                                     desc=o.get('desc') or o.get('label'), p=o.get('p'), png=o.get('png'), bbox=o.get('bbox'), area=o.get('area'),
                                     sprite=o.get('sprite'), sprite_wh=[o.get('sw'), o.get('sh')], present=o.get('present'), t=round(t, 2),
                                     fps=v.get('fps'), t_track=[v.get('t0'), (v.get('t0') or 0) + (v.get('frames') or 0) / max(1, v.get('fps') or 6)]))
        objs = [o for o in objs if o['png'] and not PRIVATE.search(o['png']) and os.path.exists(os.path.join(self.lab, o['png']))]
        os.makedirs(CACHE, exist_ok=True)
        ef, idf = os.path.join(CACHE, 'obj_emb.npy'), os.path.join(CACHE, 'obj_ids.json')
        have = {}
        if os.path.exists(ef) and os.path.exists(idf):
            E0 = np.load(ef); have = {i: E0[n] for n, i in enumerate(json.load(open(idf)))}
        todo = [o for o in objs if o['id'] not in have]
        if todo:
            from PIL import Image
            for i in range(0, len(todo), 48):
                ims = [self._on_grey(Image.open(os.path.join(self.lab, o['png']))) for o in todo[i:i + 48]]
                for o, e in zip(todo[i:i + 48], self.images(ims)): have[o['id']] = e
            np.save(ef, np.stack([have[o['id']] for o in objs])); json.dump([o['id'] for o in objs], open(idf, 'w'))
        self._objs = objs; self._OE = np.stack([have[o['id']] for o in objs])
        self._OT = self.text([f"a photo of {o['desc'] or o['label']}" for o in objs])

    @staticmethod
    def _on_grey(im):
        from PIL import Image
        im = im.convert('RGBA'); a = np.array(im)[..., 3]
        ys, xs = np.where(a > 16)
        if len(xs): im = im.crop((xs.min(), ys.min(), xs.max() + 1, ys.max() + 1))
        bg = Image.new('RGBA', im.size, (128, 128, 128, 255)); bg.alpha_composite(im); return bg.convert('RGB')

    PEOPLE = re.compile(r'\b(person|people|man|men|woman|women|child|children|boy|girl|figure|dancer|worker|soldier|player|crowd|couple|family|singer|musician|student|farmer|sailor|nurse|mother|father)\b', re.I)

    def objects(self, query, k=8, kinds=None, min_area=0.004, max_area=0.6, people=False):
        """kinds: e.g. ('figure','person') for 'citizen' cut-outs, ('object',) for things.
        people=True keeps only objects whose label or description names a person (the 'citizen' join)."""
        self._load_objects(); self._load_clips()
        q = self.text([query])[0]
        s = 0.8 * (self._OE @ q) + 0.2 * (self._OT @ q)
        out = []
        for i in np.argsort(-s):
            o = self._objs[i]
            if kinds and o['kind'] not in kinds and o['label'] not in kinds: continue
            if people and not self.PEOPLE.search(f"{o['label']} {o['desc']}"): continue
            if o.get('area') is not None and not (min_area <= o['area'] <= max_area): continue
            r = dict(o); r['score'] = round(float(s[i]), 4); r['png_path'] = os.path.join(self.lab, o['png'])
            r['provenance'] = self.clip_record(o['clip']); out.append(r)
            if len(out) >= k: break
        return out

    def cutout(self, obj, out_path, pad=4):
        """Tight RGBA crop of the object with its provenance written into the PNG's text chunks."""
        from PIL import Image, PngImagePlugin
        im = Image.open(obj['png_path'] if 'png_path' in obj else os.path.join(self.lab, obj['png'])).convert('RGBA')
        a = np.array(im)[..., 3]; ys, xs = np.where(a > 16)
        if len(xs): im = im.crop((max(0, xs.min() - pad), max(0, ys.min() - pad), min(im.width, xs.max() + 1 + pad), min(im.height, ys.max() + 1 + pad)))
        pv = obj.get('provenance') or self.clip_record(obj['clip'])
        info = PngImagePlugin.PngInfo()
        for kk, vv in dict(ledger='OBSERVED (found film)', tag=pv['tag'], clip=obj['clip'], title=str(pv['title']), year=str(pv['year']),
                           label=str(obj.get('label')), desc=str(obj.get('desc')), source_t=str(obj.get('t')), video_url=str(pv['video_url']),
                           object_id=obj['id']).items():
            info.add_text(kk, vv)
        os.makedirs(os.path.dirname(os.path.abspath(out_path)), exist_ok=True)
        im.save(out_path, pnginfo=info); return dict(path=out_path, size=list(im.size), tag=pv['tag'])

    def labelled(self, obj, out_path):
        """The cut-out with a visible ARCHIVE tag strip below it (what a set shows while the object is on screen)."""
        from PIL import Image, ImageDraw
        r = self.cutout(obj, out_path); im = Image.open(out_path).convert('RGBA')
        tag = r['tag']; h = 16; W = max(im.width, 7 * len(tag) + 10)
        out = Image.new('RGBA', (W, im.height + h), (0, 0, 0, 0)); out.alpha_composite(im, ((W - im.width) // 2, 0))
        d = ImageDraw.Draw(out); d.rectangle((0, im.height, W, im.height + h), fill=(20, 20, 20, 235))
        d.text((5, im.height + 2), tag, fill=(244, 239, 226, 255)); out.save(out_path); return r


if __name__ == '__main__':
    if len(sys.argv) < 3: print(__doc__); sys.exit(0)
    g = Grab(); mode, q = sys.argv[1], sys.argv[2]; k = int(sys.argv[3]) if len(sys.argv) > 3 else 6
    if mode == 'clips':
        for r in g.clips(q, k): print(f"{r['score']:.3f}  {r['year']}  {r['title'][:60]!s:60s}  {r['clip']}  {r['t0']}-{r['t1']}")
    else:
        od = sys.argv[4] if len(sys.argv) > 4 else None
        for r in g.objects(q, k):
            print(f"{r['score']:.3f}  {r['kind']:7s} {str(r['desc'])[:40]:40s}  {r['provenance']['tag'][:60]}")
            if od: g.cutout(r, os.path.join(od, r['id'].replace('#', '_') + '.png'))
