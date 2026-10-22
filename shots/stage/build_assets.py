"""Index everything the cut-out stage can layer, per poem: shots/stage/assets.json.

    python3 shots/stage/build_assets.py

Layer kinds (the weave's three materials, plus the kits):
  part     cut kit parts (shots/kits/cut/catalog.json; loaded by the stage directly, not repeated here)
  plane    AI as set: the 81 stills split into depth sheets (shots/world/<id>/: backdrop, far to near
           S00..S03 with their named contents from out/<id>/multiplane/multiplane.json), and the cel/ink passes
  plate    moving plates: each still's multiplane shot film (out/<id>/film/shot.mp4) and the poem films
  image    stills and atlas references (refs/stills, refs/atlas/*), tagged by source; archive-sourced
           images carry an on-screen tag while they show (the weave's rule)
  archive  archive film frames (weave/archive) and clips
  action   solved actions: arena/clips/ACT-NNN__<cast>.json, display lists per frame, played live
Paths are relative to shots/stage/.
"""
import glob, json, os, re

HERE = os.path.dirname(os.path.abspath(__file__))
SHOTS = os.path.dirname(HERE)
rel = lambda p: os.path.relpath(p, HERE).replace(os.sep, '/')
POEMS = [f'{i:02d}' for i in range(1, 15)]


def planes():
    out = {}
    for d in sorted(glob.glob(os.path.join(SHOTS, 'world', '*_*'))):
        if not os.path.isdir(d):
            continue
        short = os.path.basename(d)
        full = next(iter(glob.glob(os.path.join(SHOTS, 'out', short.split('_')[0] + '*_' + short.split('_')[1]))), None)
        meta = {}
        if full and os.path.exists(os.path.join(full, 'multiplane', 'multiplane.json')):
            mp = json.load(open(os.path.join(full, 'multiplane', 'multiplane.json')))
            for p in mp.get('planes', []):
                for s in p.get('sheets', []):
                    meta[s.split('.')[0]] = {'plane': p.get('name'), 'contents': p.get('contents', [])[:4], 'z': p.get('z_median_m'), 'parallax': p.get('parallax')}
        fid = os.path.basename(full) if full else short
        sheets = []
        for f in sorted(glob.glob(os.path.join(d, 'S*.webp')), reverse=True):   # S00 is farthest: list far to near
            k = os.path.basename(f)[:-5]
            sheets.append({'file': rel(f), 'sheet': k} | meta.get(k, {}))
        sheets.sort(key=lambda s: s['sheet'])
        film = os.path.join(full, 'film', 'shot.mp4') if full else None
        out[fid] = {'id': fid, 'short': short, 'thumb': rel(os.path.join(d, 'thumb.jpg')), 'backdrop': rel(os.path.join(d, 'backdrop.webp')),
                    'cel': rel(os.path.join(d, 'cel.webp')), 'ink': rel(os.path.join(d, 'ink.webp')), 'sheets': sheets,
                    'film': rel(film) if film and os.path.exists(film) else None}
    return out


def actions():
    out = []
    for f in sorted(glob.glob(os.path.join(SHOTS, 'arena', 'clips', 'ACT-*__*.json'))):
        cast = os.path.basename(f)[:-5].split('__')[1]
        if cast not in ('man', 'poet'):
            continue
        j = json.load(open(f))
        beats = [b.get('beat') for b in j.get('beats', []) if isinstance(b, dict)][:8]
        out.append({'id': os.path.basename(f)[:-5], 'file': rel(f), 'title': j.get('title'), 'cast': cast, 'frames': len(j.get('frames', [])),
                    'fps': j.get('clock', {}).get('fps', 24), 'floor': j.get('floor'), 'situation': j.get('situation'), 'beats': beats})
    return out


def library():
    """What the tray's library tabs may read: only files that exist, so the stage never asks for an absent one.
    mech/index.json, seq/index.json, anim/index.json, sfx/index.json when present; otherwise the clip files themselves;
    ensembles/*.json summarised here (the ensembles manifest)."""
    ex = lambda p: rel(p) if os.path.exists(p) else None
    lib = {'mech': ex(os.path.join(HERE, 'mech', 'index.json')), 'seq': ex(os.path.join(HERE, 'seq', 'index.json')),
           'anim': ex(os.path.join(HERE, 'anim', 'index.json')), 'sfx': ex(os.path.join(HERE, 'sfx', 'index.json'))}

    def clips(d, kind):
        out = []
        for f in sorted(glob.glob(os.path.join(HERE, d, '**', '*.json'), recursive=True)):
            if os.path.basename(f) == 'index.json':
                continue
            try:
                j = json.load(open(f))
            except Exception:
                continue
            if not isinstance(j, dict) or not isinstance(j.get('frames'), list):
                continue
            out.append({'id': j.get('id') or os.path.basename(f)[:-5], 'title': j.get('title') or j.get('id'), 'src': rel(f), 'kind': kind,
                        'frames': len(j['frames']), 'anchors': sorted((j.get('anchors') or {}).keys()), 'events': len(j.get('events') or []),
                        'size_cm': j.get('size_cm'), 'loop': j.get('loop'), 'poems': j.get('poems')})
        return out
    lib['mech_clips'] = clips('mech', 'mech')
    lib['seq_clips'] = clips('seq', 'sequence')
    ens = []
    for f in sorted(glob.glob(os.path.join(HERE, 'ensembles', '*.json'))):
        try:
            j = json.load(open(f))
        except Exception:
            continue
        if not isinstance(j, dict) or 'layers' not in j:
            continue
        ens.append({'id': j.get('id') or os.path.basename(f)[:-5], 'name': j.get('name'), 'file': rel(f), 'poems': j.get('poems') or [],
                    'size_cm': j.get('size_cm'), 'slots': [s.get('name') for s in j.get('slots') or []], 'mechs': len(j.get('mechs') or []),
                    'sfx': j.get('sfx') or [], 'layers': len(j.get('layers') or [])})
    lib['ensembles'] = ens
    return lib


def main():
    P = planes()
    films = {p['num']: p for p in json.load(open(os.path.join(SHOTS, 'film', 'poems.json')))}
    per = {}
    for n in POEMS:
        D = json.load(open(os.path.join(SHOTS, 'poems', 'dossier', f'{n}.json')))
        stills = [s['id'] for s in films.get(n, {}).get('shots', [])]
        stills += [b['still'] for b in D.get('best_footage') or [] if b['still'] not in stills]
        for s in D.get('sets') or []:
            stills += [r for r in s.get('refs') or [] if '/' not in r and r not in stills]
        images = []
        A = D.get('atlas') or {}
        seen = set()
        for b in A.get('best') or []:
            if b['img'] not in seen:
                seen.add(b['img'])
                images.append({'file': '../poems/' + b['img'], 'label': b.get('element'), 'source': b['img'].split('/')[2], 'use': b.get('use_for')})
        for kind in ('props', 'sets', 'characters'):
            for x in D.get(kind) or []:
                for r in x.get('atlas_refs') or []:
                    if r not in seen:
                        seen.add(r)
                        images.append({'file': '../poems/' + r, 'label': x.get('name') or x.get('id'), 'source': r.split('/')[2], 'use': kind[:-1]})
        for s in stills:
            p = os.path.join(SHOTS, 'poems', 'refs', 'stills', s + '.jpg')
            if os.path.exists(p):
                images.append({'file': rel(p), 'label': 'still ' + s[:8], 'source': 'still', 'use': 'plate'})
        per[n] = {'planes': [s for s in stills if s in P], 'images': images,
                  'film': rel(os.path.join(SHOTS, 'film', f'poem_{n}.mp4')) if os.path.exists(os.path.join(SHOTS, 'film', f'poem_{n}.mp4')) else None}
    arch = [{'file': rel(f), 'label': 'archive frame ' + os.path.basename(f)[:-4], 'source': 'archive'} for f in sorted(glob.glob(os.path.join(SHOTS, 'weave', 'archive', '*_frames', '*.jpg')))[::12]]
    out = {'about': __doc__.strip().split('\n')[0], 'planes': P, 'poems': per, 'actions': actions(), 'archive': arch, 'library': library()}
    json.dump(out, open(os.path.join(HERE, 'assets.json'), 'w'), indent=1)
    L = out['library']
    print(len(L['mech_clips']), 'mech clips,', len(L['seq_clips']), 'sequence clips,', len(L['ensembles']), 'ensembles;', 'indexes:', {k: L[k] for k in ('mech', 'seq', 'anim', 'sfx')})
    print(len(P), 'plane sets,', sum(len(v['images']) for v in per.values()), 'poem images,', len(out['actions']), 'actions,', len(arch), 'archive frames')


if __name__ == '__main__':
    main()
