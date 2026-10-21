"""Atlas references per poem, from butterfly-halfworld's world atlas (read-only clone).

    python3 shots/poems/atlas.py [path/to/butterfly-halfworld]   # -> shots/poems/atlas/NN.json + refs/atlas/

Per poem it gathers what the atlas (wygwyl/atlas.html) already knows and draws:
  scenes      the scene book's scenes (what, lines, camera, blocking, where), each with its world views
  districts   the district(s) the poem plays in: mood, hour, weather, light, architecture, places, vignettes
  heroes      hero buildings (scene book + HDL plans) with their reference photos and rooms
  transitions how the poem is entered and left
  foundry     the foundry's best images for the poem (MARKOV clips, generated stills, halfworld frames)
  sets        the foundry's per-source set images
  search      for every prop, set and character in the dossier, the archive's 8,000 images ranked by meaning
              (the archive stores each image's CLIP score for 151 terms; a name picks its terms)
Images are copied (≤480 px jpg) to refs/atlas/ so the pages and kits can use them.
"""
import json, os, re, sys
import numpy as np
from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
BH = sys.argv[1] if len(sys.argv) > 1 else os.path.normpath(os.path.join(HERE, '..', '..', '..', 'hartswf0', 'butterfly-halfworld'))
W = os.path.join(BH, 'wygwyl', 'world')
OUT = os.path.join(HERE, 'atlas')
IMG = os.path.join(HERE, 'refs', 'atlas')
STOP = {'the', 'and', 'with', 'over', 'into', 'from', 'his', 'her', 'its', 'one', 'two', 'for', 'that', 'this', 'card', 'cards', 'cut'}


def copy(src, name, size=480):
    """Thumbnail src into refs/atlas/name.jpg; returns the page-relative path or None."""
    dst = os.path.join(IMG, name + '.jpg')
    if not os.path.exists(dst):
        if not os.path.exists(src):
            return None
        im = Image.open(src).convert('RGB')
        im.thumbnail((size, size))
        os.makedirs(os.path.dirname(dst), exist_ok=True)
        im.save(dst, quality=78)
    return 'refs/atlas/' + name + '.jpg'


def view(n):
    return copy(os.path.join(W, 'districts', 'v', f'{int(n):03d}.webp'), f'views/{int(n):03d}')


class Archive:
    def __init__(self):
        D = json.load(open(os.path.join(W, 'archive', 'items.json')))
        self.F = {f: i for i, f in enumerate(D['fields'])}
        self.items, self.vocab, self.poems = D['items'], D['vocab'], D['poems']
        n = len(self.items)
        self.VS = np.fromfile(os.path.join(W, 'archive', 'vocab.u8'), dtype=np.uint8).reshape(n, len(self.vocab)).astype(np.float32)
        self.PS = np.fromfile(os.path.join(W, 'archive', 'poems.u8'), dtype=np.uint8).reshape(n, len(self.poems)).astype(np.float32)
        self.shown = np.array([it[self.F['source']] != 'shoot' for it in self.items])  # shoot photographs of real people are never shown

    def terms(self, words):
        toks = [t for t in re.findall(r'[a-z]+', words.lower()) if len(t) > 2 and t not in STOP]
        tw = {}
        for i, p in enumerate(self.vocab):
            pw = re.findall(r'\w+', p.lower())
            hits = sum(1 for t in toks if any(w.startswith(t) or (t.startswith(w) and len(w) > 3) for w in pw))
            if hits:
                tw[i] = hits / len(pw) ** .5
        return tw

    def search(self, words, poem, k=6, used=()):
        tw = self.terms(words)
        if not tw:
            return [], []
        s = sum(self.VS[:, i] * w for i, w in tw.items())
        if poem in self.poems:  # lean toward the poem's own images
            s = s + .35 * self.PS[:, self.poems.index(poem)]
        s[~self.shown] = -1e9
        out = []
        for i in np.argsort(-s):
            if len(out) >= k:
                break
            if int(i) in used:
                continue
            it = self.items[i]
            p = copy(os.path.join(W, 'archive', 't', f'{i}.webp'), f'archive/{i}')
            if p:
                out.append({'id': f'a{i}', 'img': p, 'source': it[self.F['source']], 'kind': it[self.F['kind']],
                            'tags': [self.vocab[t] for t in it[self.F['tags']][:4]], 'path': os.path.basename(str(it[self.F['path']]))})
        return out, sorted((self.vocab[i] for i in tw), key=lambda t: -tw[self.vocab.index(t)])


def main():
    S = json.load(open(os.path.join(W, 'districts', 'scenes.json')))
    refs = json.load(open(os.path.join(W, 'foundry', 'refs.json')))
    sets = json.load(open(os.path.join(W, 'foundry', 'sets.json')))['sets']
    hdl = json.load(open(os.path.join(W, 'heroes', 'hdl.json')))['heroes']
    href = json.load(open(os.path.join(W, 'heroes', 'refs.json')))
    gaz = json.load(open(os.path.join(W, 'gazetteer', 'world.json')))
    pal = json.load(open(os.path.join(W, 'language', 'palettes.json')))
    A = Archive()
    dist = {d['id']: d for d in S['districts']}
    os.makedirs(OUT, exist_ok=True)
    for n in [f'{i:02d}' for i in range(1, 15)]:
        dpath = os.path.join(HERE, 'dossier', f'{n}.json')
        P = json.load(open(dpath)) if os.path.exists(dpath) else {}
        scenes = [s for s in S['scenes'] if s['poem'] == n]
        dids = []
        for s in scenes:
            if s.get('d') and s['d'] not in dids:
                dids.append(s['d'])
        R = {'num': n, 'title': P.get('title') or (scenes[0]['title'] if scenes else n)}
        R['script'] = next(({k: x[k] for k in ('hour', 'weather', 'why', 'seq')} for x in S['script'] if x['num'] == n), None)
        R['scenes'] = [{'key': s['key'], 'name': s['name'], 'what': s['what'], 'lines': s.get('lines'), 'camera': s.get('camera'),
                        'position': s.get('position'), 'here': s.get('here'), 'block': s.get('block'), 'district': s.get('d'),
                        'views': [{'n': v, 'img': view(v)} for v in (s.get('clip_views') or [])[:4]]} for s in scenes]
        R['districts'] = []
        for did in dids:
            d = dist.get(did)
            if not d:
                continue
            R['districts'].append({k: d.get(k) for k in ('id', 'name', 'mood', 'tone', 'hour', 'weather', 'sound', 'camera', 'light_tech', 'arch', 'language', 'body', 'color')}
                                  | {'places': [{'name': p['name'], 'what': p['what'], 'views': [{'n': v, 'img': view(v)} for v in p['views'][:3]]} for p in d.get('places', [])],
                                     'vignettes': [{'name': v['name'], 'what': v['what'], 'views': [{'n': x, 'img': view(x)} for x in v['views'][:2]]} for v in d.get('vignettes', [])]})
        R['heroes'] = []
        for h in S['heroes']:
            if n in h.get('poems', []):
                R['heroes'].append({'id': h['id'], 'name': h['name'], 'brief': h['brief'], 'beats': h.get('beats'), 'facts': h.get('facts'),
                                    'views': [{'n': v, 'img': view(v)} for v in h.get('views', [])[:4]]})
        for h in hdl:
            if h.get('poem') == n:
                imgs = []
                for side in ('exterior', 'interior'):
                    for r in href.get(h['id'], {}).get(side, [])[:4]:
                        p = copy(os.path.join(W, 'heroes', 'ref', r['f']), f"heroes/{h['id']}/{r['f'][:-5]}")
                        if p:
                            imgs.append({'img': p, 'side': side, 'source': r['src']})
                rooms = [f"{lv['name']}: " + ', '.join(rm.get('name', rm.get('id', '')) for rm in lv.get('rooms', [])) for lv in h.get('levels', [])]
                R['heroes'].append({'id': h['id'], 'name': h['name'], 'brief': h.get('note'), 'landmark': h.get('landmark'),
                                    'skin': h.get('skin'), 'rooms': rooms, 'refs': imgs})
        R['transitions'] = [t for t in S['transitions'] if n in (t.get('from'), t.get('to'))]
        for t in R['transitions']:
            t['view_imgs'] = [view(v) for v in t.get('views', [])[:2]]
        R['foundry'] = [{'id': r['id'], 'img': copy(os.path.join(W, 'foundry', r['img']), f"foundry/{r['id']}"), 'source': r['source'],
                         'desc': r.get('desc'), 'line': r.get('line'), 'hour': r.get('hour')} for r in refs['refs'] if r['poem'] == n]
        R['sets'] = []
        for st in sets:
            if st['poem'] == n:
                for im in st['images'][:3]:
                    p = copy(os.path.join(W, 'foundry', im['img']), f"sets/{im['id']}")
                    if p:
                        R['sets'].append({'source': st['source'], 'img': p, 'video': im.get('video'), 'desc': im.get('desc')})
        # meaning search for every prop, set and character the dossier names
        used = set()
        R['search'] = []
        for kind, xs in (('prop', P.get('props') or []), ('set', P.get('sets') or []), ('character', P.get('characters') or [])):
            for x in xs:
                # the name first (fewest stray terms); the look or role only when the name touches none
                name = ' '.join(str(x.get(k, '')).replace('_', ' ') for k in ('name', 'id'))
                more = str(x.get('look', '')) if kind != 'character' else ' '.join([x.get('role_in_poem', '')] + (x.get('signature_actions') or [])[:3])
                hits, terms = A.search(name if A.terms(name) else more, n, 6 if kind != 'character' else 4, used)
                used |= {int(h['id'][1:]) for h in hits[:2]}
                R['search'].append({'kind': kind, 'id': x.get('id'), 'name': x.get('name') or x.get('id'), 'terms': terms[:6], 'hits': hits})
        R['palettes'] = [p for p in pal if any(w in p['name'] for w in ' '.join(d.get('name', '') for d in R['districts']).lower().split() if len(w) > 4)][:2]
        json.dump(R, open(os.path.join(OUT, f'{n}.json'), 'w'), indent=1)
        print(n, R['title'], len(R['scenes']), 'scenes', len(R['districts']), 'districts', len(R['heroes']), 'heroes',
              len(R['foundry']), 'foundry', len(R['sets']), 'sets', sum(len(s['hits']) for s in R['search']), 'archive hits')
    json.dump({k: gaz[k] for k in ('overview', 'calendar', 'institutions', 'trades', 'transit', 'customs', 'sayings')} | {'thesis': S['thesis'],
              'realms': S['realms']}, open(os.path.join(OUT, 'world.json'), 'w'), indent=1)


if __name__ == '__main__':
    main()
