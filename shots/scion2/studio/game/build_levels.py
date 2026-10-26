"""Build the 14 poems as game levels.

    python3 -m studio.game.build_levels <play_dir>        (run from shots/scion2)

A level is one poem. Its scenes come from shots/stage/plans/NN.json (the authored tableau of each scene) and
shots/stage/timeline/NN.json (the reading's word times and scene times). Each scene is composed to one
wide image from the plan's own kit pieces only (type `part`). Archive stills and footage planes in the plans
(kinds `image` and `plane`) are not used: a painted sky from the set-piece registry stands in, and the poet's
own still drawing is left out because the player is the poet.

For every line of the poem a marker is placed on the stage; the level asks the player to stand at it while
the line is read. Marker places are the authored characters and props of the scene, so the player walks through
the tableau.
"""
import json, os, shutil, sys
import numpy as np
from PIL import Image

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..', '..'))
SHOTS = os.path.join(ROOT, 'shots')
CUT = os.path.join(SHOTS, 'kits/cut')
FW, FH = 1600, 900            # the plans' frame
OW, OH = 1280, 720            # exported frame
K = OW / FW
SKIP_KINDS = {'plane', 'image', 'action', 'clip', 'sfx', 'ensemble'}


def find_part(part):
    for e in ('.webp', '.png'):
        p = os.path.join(CUT, part + e)
        if os.path.exists(p):
            return p
    return None


_cache = {}


def load_part(part):
    if part not in _cache:
        p = find_part(part)
        _cache[part] = Image.open(p).convert('RGBA') if p else None
    return _cache[part]


def blend(base, top, mode):
    """base, top: float arrays 0..1 (top premultiplied-free RGB); returns the blended rgb"""
    if mode == 'screen':
        return 1 - (1 - base) * (1 - top)
    if mode == 'multiply':
        return base * top
    if mode == 'add':
        return np.clip(base + top, 0, 1)
    return top


def compose(layers, bg_path):
    sky = Image.open(bg_path).convert('RGB')
    s = max(OW / sky.width, OH / sky.height)
    sky = sky.resize((max(OW, round(sky.width * s)), max(OH, round(sky.height * s))), Image.LANCZOS)
    sky = sky.crop(((sky.width - OW) // 2, 0, (sky.width - OW) // 2 + OW, OH))
    canvas = np.asarray(sky, np.float32) / 255.
    npcs, used, missing = [], 0, 0
    for l in layers:
        part = l.get('part')
        if not part or l.get('kind') in SKIP_KINDS or l.get('hide'):
            continue
        if part.startswith('poet.'):                  # the player is the poet
            continue
        im = load_part(part)
        if im is None:
            missing += 1
            continue
        w = max(1, round(l['w'] * K))
        h = max(1, round(l['h'] * K)) if l.get('h') else max(1, round(im.height * w / im.width))
        rs = im.resize((w, h), Image.LANCZOS)
        x0, y0 = round(l['x'] * K - w / 2), round(l['y'] * K - h / 2)
        xa, ya, xb, yb = max(0, x0), max(0, y0), min(OW, x0 + w), min(OH, y0 + h)
        if xb <= xa or yb <= ya:
            continue
        a = np.asarray(rs, np.float32) / 255.
        a = a[ya - y0:yb - y0, xa - x0:xb - x0]
        al = a[..., 3:4] * float(l.get('op', 1.0))
        rgb = a[..., :3]
        region = canvas[ya:yb, xa:xb]
        mixed = blend(region, rgb, l.get('blend'))
        canvas[ya:yb, xa:xb] = region * (1 - al) + mixed * al
        used += 1
        if '.main-poses' in part or 'heads-hands' in part or 'cast' in part:
            npcs.append({'part': part, 'x': round(l['x'] * K), 'h': h, 'w': w})
    return Image.fromarray((np.clip(canvas, 0, 1) * 255).astype(np.uint8)), npcs, used, missing


def markers_for(lines, npcs, width):
    """one marker x per line: characters and big props, spread so the player has to walk"""
    cand = sorted({n['x'] for n in npcs if 80 < n['x'] < width - 80})
    for f in (0.18, 0.5, 0.82):
        if all(abs(c - f * width) > 160 for c in cand):
            cand.append(round(f * width))
    cand.sort()
    out, prev = [], width * 0.5
    for i, _ in enumerate(lines):
        best = max(cand, key=lambda c: (abs(c - prev) if abs(c - prev) < width * 0.6 else width * 0.6 - abs(c - prev) * 0.1) + ((i * 37 + c) % 29) * 0.01)
        out.append(int(best))
        prev = best
    return out


def run(play):
    out = os.path.join(play, 'levels')
    shutil.rmtree(out, ignore_errors=True)
    os.makedirs(out)
    bgs = {m['poem']: m for m in json.load(open(os.path.join(play, 'assets/bg/bg.json')))}
    default_bg = next(iter(bgs.values()))
    plan_c = json.load(open(os.path.join(os.path.dirname(SHOTS), 'shots/scion2/cast_plan.json')))['poems']
    playable = {c['key']: c['dir'] for c in json.load(open(os.path.join(play, 'data.json')))['characters']}
    index = []
    for n in range(1, 15):
        num = '%02d' % n
        plan = json.load(open(os.path.join(SHOTS, 'stage/plans/%s.json' % num)))
        tl = json.load(open(os.path.join(SHOTS, 'stage/timeline/%s.json' % num)))
        pdir = os.path.join(out, num)
        os.makedirs(pdir)
        shutil.copy(os.path.join(SHOTS, 'stage/audio/%s.mp3' % num), os.path.join(pdir, 'reading.mp3'))
        bg = bgs.get(num, default_bg)
        by_key = {s['key']: s for s in plan['scenes']}
        scenes = []
        for k, ts in enumerate(tl['scenes']):
            ps = by_key.get(ts['key'])
            if not ps:
                continue
            img, npcs, used, missing = compose(ps.get('layers', []), os.path.join(play, 'assets/bg', bg['f']))
            fn = 's%d.webp' % k
            img.save(os.path.join(pdir, fn), quality=76, method=4)
            cam = ps.get('camera', {})
            lines = ts.get('lines', [])
            mx = markers_for(lines, npcs, OW)
            ppc = cam.get('ppc', 2.0) * K
            foot = min(OH - 6, cam.get('foot_y', 774) * K)
            scenes.append({'key': ts['key'], 'name': ts['name'], 't0': round(ts['t0'], 3), 't1': round(ts['t1'], 3), 'img': fn,
                           'floor': round(foot, 1), 'ppc': round(ppc, 3), 'shot': cam.get('shot', ''),
                           'npcs': [{'x': c['x']} for c in npcs],
                           'lines': [{'t': round(l['t'], 2), 'e': round(l['e'], 2), 'text': l['text'], 'w0': l['w'][0], 'w1': l['w'][1], 'mx': mx[i]}
                                     for i, l in enumerate(lines)],
                           'pieces': used, 'missing_pieces': missing})
        data = {'num': num, 'title': tl['title'], 'audio': 'reading.mp3', 'duration': round(tl['duration'], 2),
                'words': [[w['w'], round(w['s'], 2), round(w['e'], 2)] for w in tl['words']], 'scenes': scenes,
                'frame': [OW, OH], 'bg': bg['f'],
                'cast': [{'key': k, 'dir': playable[k]} for k in plan_c[num]['cast'] if k in playable]}
        json.dump(data, open(os.path.join(pdir, 'level.json'), 'w'), separators=(',', ':'))
        index.append({'num': num, 'title': tl['title'], 'duration': data['duration'], 'scenes': len(scenes),
                      'lines': sum(len(s['lines']) for s in scenes), 'thumb': '%s/%s' % (num, scenes[0]['img']), 'cast': len(data['cast'])})
        print(num, tl['title'][:30], 'scenes', len(scenes), 'pieces', sum(s['pieces'] for s in scenes),
              'missing', sum(s['missing_pieces'] for s in scenes), flush=True)
    json.dump(index, open(os.path.join(out, 'index.json'), 'w'))


if __name__ == '__main__':
    run(sys.argv[1])
