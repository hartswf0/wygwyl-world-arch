"""Animate a poem: python3 -m rigkit.poem <plan.json>   (run from shots/scion2)

plan.json: {"char", "poem": "09", "keys": [{"word": "real", "near": 3.9, "target": painting id, "x": 0.5, "why": ...}]}
Each key lands on the start of the named word (the stressed word of its line), found in
shots/stage/timeline/<poem>.json nearest to "near" seconds.  Writes <out>.mp4 (audio muxed),
<out>_strip.jpg and <out>.json (resolved key list with times, poses and part sources).
"""
import json, os, re, sys
from . import core, animate


def resolve(plan):
    tl = json.load(open(os.path.join(core.ROOT, 'shots/stage/timeline/%s.json' % plan['poem'])))
    words = tl['words']
    norm = lambda w: re.sub(r'[^a-z]', '', w.lower())
    keys = []
    for k in plan['keys']:
        if 't' in k:
            t = k['t']
        else:
            c = [w for w in words if norm(w['w']) == norm(k['word'])]
            if not c:
                raise ValueError('word not found: %s' % k['word'])
            w = min(c, key=lambda w: abs(w['s'] - k['near']))
            t = w['s']
        kk = dict(k.get('keys', {}))
        if not plan.get('costume_props', False):
            kk['no_costume_props'] = True      # one costume through the poem
        keys.append(dict(k, t=round(t, 3), keys=kk))
    keys.sort(key=lambda k: k['t'])
    return keys, tl


def main(path):
    plan = json.load(open(path))
    keys, tl = resolve(plan)
    od = os.path.dirname(os.path.abspath(path))
    name = 'poem%s' % plan['poem']
    audio = os.path.join(core.ROOT, 'shots/stage', tl['audio'])
    frames, events, solved = animate.animate(plan['char'], keys, os.path.join(od, name + '.mp4'), duration=tl['duration'],
                                             audio=audio, strip=os.path.join(od, name + '_strip.jpg'), ss=plan.get('ss', 2))
    out = []
    for k, (pose, G) in zip(keys, solved):
        out.append({'t': k['t'], 'word': k.get('word'), 'target': k['target'], 'why': k.get('why', ''), 'rig': pose['view'],
                    'mirrored': pose['mirror'], 'sources': pose['sources'], 'flags': pose['flags']})
    json.dump({'poem': plan['poem'], 'title': tl['title'], 'duration': tl['duration'], 'fps': animate.FPS, 'size': [1600, 900],
               'keys': out, 'rig_changes': events}, open(os.path.join(od, name + '.json'), 'w'), indent=1)


if __name__ == '__main__':
    main(sys.argv[1])
