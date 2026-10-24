"""Slim the proof's results.json into the Crash Lab page's data (proof01/lab.json).

    python3 -m studio.lab
"""
import json, os

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, 'proof01')


def r2(x, n=2):
    return None if x is None else round(float(x), n)


def main():
    R = json.load(open(os.path.join(OUT, 'results.json')))
    lab = {'px_per_cm': R['px_per_cm'], 'checks': R['checks'], 'actors': R['actors'], 'cells': {}, 'scenes': {}}
    for name, c in R['cells'].items():
        rows = c['rows']
        lab['cells'][name] = {
            'actor': c['actor'], 'action': c['action'], 'frames': c['frames'],
            'video': name + '.mp4', 'overlay': name + '_overlay.mp4', 'poster': name + '.jpg',
            'series': {'skate': [r2(r['skate_cm']) for r in rows], 'neck': [r2(r['neck']) for r in rows],
                       'below': [r2(max(0., r['low_px']) / R['px_per_cm']) for r in rows],
                       'event': [r['event'] for r in rows], 'view': [r['view'] for r in rows],
                       'planted': [sorted(k for k in r['contact'] if k.startswith('foot')) for r in rows]}}
    for tag, s in R['scenes'].items():
        lab['scenes'][tag] = {'roles': s['roles'], 'hit_frame': s['hit_frame'], 'fall_start': s['fall_start'],
                              'video': 'scene_%s.mp4' % tag, 'overlay': 'scene_%s_overlay.mp4' % tag, 'poster': 'scene_%s.jpg' % tag}
    json.dump(lab, open(os.path.join(OUT, 'lab.json'), 'w'), separators=(',', ':'))
    print('lab.json', os.path.getsize(os.path.join(OUT, 'lab.json')))


if __name__ == '__main__':
    main()
