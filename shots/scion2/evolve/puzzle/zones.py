"""Zone learning: where each piece landed in blind fills, read against the Pose Lab skeleton after the fill.

zones.json  {'fills': [target|mode, ...], 'pieces': {piece id: {zone: count}}, 'labels': {piece id: library slot}}
relabel.md  pieces whose learned zone (most frequent, >= 2 landings) disagrees with their library label, with
            contact sheets relabel/<learned zone>.jpg (numbered as in the table).
Only BLIND fills are recorded (prior fills would teach the prior its own guesses).
"""
import json, os
import numpy as np
from PIL import Image, ImageDraw, ImageFont

HERE = os.path.dirname(os.path.abspath(__file__))
PATH = os.path.join(HERE, 'zones.json')
SLOT_ZONE = {'pelvis': 'hips', 'upper_arm': 'upper_arm', 'forearm': 'forearm', 'hand': 'hand', 'thigh': 'thigh',
             'shin': 'shin', 'foot': 'foot', 'head': 'head', 'torso': 'torso'}


def load():
    if os.path.exists(PATH):
        return json.load(open(PATH)).get('pieces', {})
    return {}


def _all():
    return json.load(open(PATH)) if os.path.exists(PATH) else {'fills': [], 'pieces': {}, 'labels': {}}


def n_fills():
    return len(_all()['fills'])


def record(r):
    if r.get('mode') != 'blind':
        return
    Z = _all()
    key = '%s|%s' % (r['target'], r['mode'])
    if key in Z['fills']:
        return
    Z['fills'].append(key)
    for p in r['placed']:
        if not p['zone']:
            continue
        d = Z['pieces'].setdefault(p['id'], {})
        d[p['zone']] = d.get(p['zone'], 0) + 1
        Z['labels'][p['id']] = p['label']
    json.dump(Z, open(PATH + '.tmp', 'w'), indent=1)
    os.replace(PATH + '.tmp', PATH)


def write_relabel():
    from evolve import library
    Z = _all()
    imgs = {c['id']: c['img'] for ch, co in (('poet', 'red_black_sunglasses'), ('ex', 'ex_jacket')) for c in library.cards(ch, co)}
    rows = []
    for pid, d in Z['pieces'].items():
        zone, n = max(d.items(), key=lambda kv: kv[1])
        lab = SLOT_ZONE.get(Z['labels'].get(pid), Z['labels'].get(pid))
        if n >= 2 and zone != lab:
            rows.append((zone, pid, lab, n, sum(d.values()), d))
    rows.sort(key=lambda r: (r[0], -r[3]))
    os.makedirs(os.path.join(HERE, 'relabel'), exist_ok=True)
    md = ['# Pieces whose learned zone disagrees with their library label', '',
          'Learned from %d blind fills: a piece\'s zone is the skeleton zone holding most of its pixels where the blind '
          'puzzle put it (read after the fill). Listed when the most frequent zone (>= 2 landings) is not the label.'
          % len(Z['fills']), '']
    F = ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf', 11)
    by_zone = {}
    for r in rows:
        by_zone.setdefault(r[0], []).append(r)
    for zone, rs in by_zone.items():
        md += ['## learned: %s (%d pieces) — contact sheet relabel/%s.jpg' % (zone, len(rs), zone), '',
               '| # | piece | library label | landings in %s / all | all zones |' % zone, '|---|---|---|---|---|']
        cw, ch = 130, 150
        cols = 8
        sheet = Image.new('RGB', (cols * cw, ((len(rs) + cols - 1) // cols) * ch), (230, 230, 230))
        dr = ImageDraw.Draw(sheet)
        for i, (z, pid, lab, n, tot, d) in enumerate(rs):
            md.append('| %d | `%s` | %s | %d / %d | %s |' % (i + 1, pid, lab, n, tot, ', '.join('%s %d' % kv for kv in sorted(d.items(), key=lambda kv: -kv[1]))))
            try:
                im = Image.open(imgs[pid]).convert('RGBA')
                im.thumbnail((cw - 8, ch - 30))
                x, y = (i % cols) * cw + 4, (i // cols) * ch + 4
                sheet.paste(im, (x, y), im)
                dr.text((x, y + ch - 26), '%d  label: %s' % (i + 1, lab), fill=(0, 0, 0), font=F)
            except Exception:
                pass
        sheet.save(os.path.join(HERE, 'relabel', '%s.jpg' % zone), quality=80)
        md.append('')
    open(os.path.join(HERE, 'relabel.md'), 'w').write('\n'.join(md) + '\n')


def summary_line(R):
    bl = [r for r in R.values() if r.get('mode') == 'blind' and 'error' not in r]
    pr = {r['target']: r for r in R.values() if r.get('mode') == 'prior' and 'error' not in r}
    s = 'blind fills %d: median coverage %.1f%%, median pieces %d' % (len(bl), 100 * np.median([r['coverage'] for r in bl]),
                                                                     np.median([r['n_pieces'] for r in bl]))
    pairs = [(R['%s|blind' % t], pr[t]) for t in pr if '%s|blind' % t in R]
    if pairs:
        s += '; prior vs blind on %d targets: coverage %+.1f pts, pieces %+.1f' % (
            len(pairs), 100 * np.mean([p['coverage'] - b['coverage'] for b, p in pairs]), np.mean([p['n_pieces'] - b['n_pieces'] for b, p in pairs]))
    return s
