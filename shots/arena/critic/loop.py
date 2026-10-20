"""One turn of the critic loop for an arena take.

    python3 shots/arena/critic/loop.py ACT-010            # man skin, authored acting beats
    python3 shots/arena/critic/loop.py ACT-003 --frames 40,72,150

For each acting beat it renders the take two ways, the compiler's rig as it ships
("rig") and the brad-on-brad assembly ("brad"), measures both on their pixels, and
writes a packet a critic can look at (see CRITICS.md):

  out/<ACT>/board_f<N>.png      rig | brad, plain and silhouette, same beat
  out/<ACT>/f<N>_<v>_*.png      plain, overlay, loupes, silhouette per variant
  out/<ACT>/keys_<v>.png        authored-beat frames only, no captions: the cold read
  out/<ACT>/report.json         every measurement
  out/<ACT>/report.md           the scoreboard, and what changed since the last turn

The numbers do not decide anything. They point the critic at the crop to look at.
"""
import argparse, json, os, sys
import numpy as np
from PIL import Image, ImageDraw

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import frame as F
from assemble import assemble
import assemble_kit
from bank import Bank

TEXTURE = ('passing', 'heel strike', 'weight onto', 'trailing foot', 'toe off', 'contact')
TOL_CM = 2.0
VARIANTS = ('rig', 'brad', 'kit')


def asked(bk, f, n, cards):
    """What Bolas asked for on this frame against what the parts can show."""
    out = []
    for a in range(n):
        fc = bk.face(f, a) or {}
        head = next(c for c in cards if c['actor'] == a and c['role'] == 'head')
        expressive = fc.get('mouth') not in (None, 'line') or abs(fc.get('brow', 0)) > .2 or fc.get('lid', 0) > .2 or fc.get('eyes') not in (None, 'o')
        fixed = '.ie.' not in head['id']
        out.append({'actor': a, 'effort': bk.effort(f, a), 'face_asked': fc,
                    'face_shown': head['id'] + (' (one fixed expression, sunglasses)' if fixed else ''),
                    'face_gap': bool(expressive and fixed),
                    'hands': {c['role']: {'asked': c.get('asked'), 'shown': c['id']} for c in cards if c['actor'] == a and c['role'].startswith('hand')}})
    return out


def acting_beats(clip):
    out = []
    for b in clip.get('beats', []):
        t = b.get('beat', '').lower()
        if any(w in t for w in TEXTURE):
            continue
        if 0 <= b['f'] < len(clip['frames']) and b['f'] not in out:
            out.append(b['f'])
    return out


def grounded(clip, f):
    return bool(clip['frames'][f].get('dbg', {}).get('sup'))


def ground(clip, f, cards, props=None):
    """Drop each figure so its lowest boot pixel sits on the floor (grounded frames only)."""
    img, masks, floor = F.render(clip, f, cards, props)
    if floor is None or not grounded(clip, f):
        return cards, (img, masks, floor)
    moved = False
    for a in sorted({c['actor'] for c in cards}):
        bs = [masks.get((a, r)) for r in ('boot.near', 'boot.far')]
        bs = [b for b in bs if b is not None and b.any()]
        if not bs:
            continue
        dy = floor - max(int(np.nonzero(b)[0].max()) for b in bs)
        if abs(dy) >= 1:
            moved = True
            for c in cards:
                if c['actor'] == a:
                    c['m'] = list(c['m'])
                    c['m'][5] += dy
    return cards, (F.render(clip, f, cards, props) if moved else (img, masks, floor))


def summarise(rep):
    j = rep['joints']
    read_bad = {k: v['brad_gap_cm'] for k, v in j.items() if v['brad_gap_cm'] > TOL_CM and not v['guessed']}
    guess_bad = {k: v['brad_gap_cm'] for k, v in j.items() if v['brad_gap_cm'] > TOL_CM and v['guessed']}
    fig = rep['figure']
    return {
        'joints_open_read': read_bad, 'joints_open_guessed': guess_bad,
        'worst_gap_cm': max([v['brad_gap_cm'] for v in j.values()] or [0]),
        'boots_below_floor_px': max(fig['boot_lowest_minus_floor_px'] or [0]),
        'head_to_figure': fig['head_to_figure_height'],
        'detached': fig['pieces_detached'],
        'view_mismatch': fig['view_mismatch'],
        'max_anisotropy': max(c['anisotropy'] for c in rep['cards'].values()),
        'stretched_cards': sorted(r for r, c in rep['cards'].items() if c['anisotropy'] > 1.15),
    }


def board(out, f, beat, crops, names):
    pad, lab = 16, 34
    ims = [Image.open(p) for p in crops]
    h = max(i.size[1] for i in ims)
    Wd = sum(i.size[0] for i in ims) + pad * (len(ims) + 1)
    lab = 64
    B = Image.new('RGB', (Wd, h + lab + pad), (30, 32, 38))
    d = ImageDraw.Draw(B)
    x = pad
    for i, im in enumerate(ims):
        B.paste(im, (x, lab))
        d.text((x, 10), names[i] if i < len(names) else '', fill=(230, 230, 230), font=F._font(18))
        x += im.size[0] + pad
    d.text((pad, 36), f'f{f}  {beat or ""}', fill=(255, 220, 120), font=F._font(20))
    B.save(os.path.join(out, f'board_f{f}.png'))


def keys_sheet(out, variant, frames, beats):
    ims = [Image.open(os.path.join(out, f'f{f}_{variant}_plain.png')) for f in frames]
    h = 520
    ims = [i.resize((max(1, int(i.size[0] * h / i.size[1])), h)) for i in ims]
    S = Image.new('RGB', (sum(i.size[0] for i in ims) + 12 * (len(ims) + 1), h + 24), (23, 25, 31))
    x = 12
    for i in ims:
        S.paste(i, (x, 12))
        x += i.size[0] + 12
    S.save(os.path.join(out, f'keys_{variant}.png'))


def run(act, skin, frames):
    clip = F.load_clip(act, skin)
    out = os.path.join(HERE, 'out', act)
    os.makedirs(out, exist_ok=True)
    prev = None
    rp = os.path.join(out, 'report.json')
    if os.path.exists(rp):
        prev = json.load(open(rp))
    frames = frames or acting_beats(clip)
    beat_of = {b['f']: b['beat'] for b in clip.get('beats', [])}
    report = {'act': act, 'skin': skin, 'px_per_cm': round(F.px_per_cm(clip), 2), 'frames': {}}
    for f in frames:
        n = F.actors(clip, f)
        if not n:
            report['frames'][str(f)] = {'skipped': 'no cut-out rig on this frame: a whole-pose picture replaces it'}
            continue
        per = [F.pieces(clip, f, a) for a in range(n)]
        row = {'beat': beat_of.get(f), 'grounded': grounded(clip, f), 'actors': n}
        crops = {}
        try:
            bk = Bank(act)
        except FileNotFoundError:
            bk = None
        for variant in VARIANTS:
            props = None
            if variant == 'kit':
                if bk is None:
                    continue
                cs, notes = [], []
                for a in range(n):
                    c2, nt = assemble_kit.assemble(clip, f, [dict(c) for c in per[a]], bk, a)
                    cs += c2
                    notes += nt
                props = bk.props(f)
                cs, (img, masks, floor) = ground(clip, f, cs, props)
                row['kit_asked'] = asked(bk, f, n, cs)
                row['kit_missing'] = sorted(set(notes))
            elif variant == 'brad':
                cs = [c for a in range(n) for c in assemble(clip, f, [dict(c) for c in per[a]])]
                cs, (img, masks, floor) = ground(clip, f, cs)
            else:
                cs = [dict(c) for a in range(n) for c in per[a]]
                img, masks, floor = F.render(clip, f, cs)
            reps = [F.probe(clip, f, [c for c in cs if c['actor'] == a], masks, floor) for a in range(n)]
            rep = reps[0][0]
            merged = dict(rep, joints={(f'{k}' if a == 0 else f'{clip["cast"][a]["name"]}:{k}'): v
                                       for a, (r, _) in enumerate(reps) for k, v in r['joints'].items()})
            J = {}
            if variant == 'rig':
                for a in range(n):
                    J.update({f'{a}{k}': v for k, v in F.skeleton(per[a]).items()})
            F.packet(img, masks, merged, reps[0][1], out, f'f{f}_{variant}', J, TOL_CM)
            row[variant] = {'summary': summarise(merged), 'probe': [r for r, _ in reps]}
            crops[variant] = (os.path.join(out, f'f{f}_{variant}_plain.png'), os.path.join(out, f'f{f}_{variant}_silhouette.png'))
        board(out, f, row['beat'], [crops[v][0] for v in VARIANTS if v in crops] + [crops[v][1] for v in VARIANTS if v in crops],
              [v for v in VARIANTS if v in crops] + [v + ' silhouette' for v in VARIANTS if v in crops])
        report['frames'][str(f)] = row
    done = [f for f in frames if 'rig' in report['frames'].get(str(f), {})]
    for v in VARIANTS:
        if done and all(os.path.exists(os.path.join(out, f'f{f}_{v}_plain.png')) for f in done):
            keys_sheet(out, v, done, beat_of)
    json.dump(report, open(rp, 'w'), indent=1, default=float)
    write_md(out, report, prev)
    return report


def write_md(out, report, prev):
    L = [f"# Critic packet: {report['act']} ({report['skin']})", '',
         f"px per cm from the skeleton: {report['px_per_cm']}. Gaps over {TOL_CM}cm are open joints.",
         'A "guessed" joint is one whose socket the card does not draw; brads.py placed it by rule.', '',
         '| f | beat | variant | open (read) | open (guessed) | worst cm | boots below floor px | head/figure | stretched cards | view mismatch |',
         '| --: | :-- | :-- | :-- | :-- | --: | --: | --: | :-- | :-- |']
    for f, row in report['frames'].items():
        if 'skipped' in row:
            L.append(f"| {f} | | | {row['skipped']} | | | | | | |")
            continue
        for v in VARIANTS:
            if v not in row:
                continue
            s = row[v]['summary']
            fmt = lambda d: ', '.join(f'{k} {x}' for k, x in d.items()) or '-'
            L.append(f"| {f} | {row['beat'] or ''} | {v} | {fmt(s['joints_open_read'])} | {fmt(s['joints_open_guessed'])} | "
                     f"{s['worst_gap_cm']} | {s['boots_below_floor_px']} | {s['head_to_figure']} | {', '.join(s['stretched_cards']) or '-'} | {s['view_mismatch']} |")
    if prev:
        L += ['', '## Since the last turn', '']
        for f, row in report['frames'].items():
            p = prev['frames'].get(f)
            if not p or 'rig' not in row or 'rig' not in p:
                continue
            for v in VARIANTS:
                if v not in p or v not in row:
                    continue
                a, b = p[v]['summary'], row[v]['summary']
                ch = [f"{k} {a[k]} -> {b[k]}" for k in ('worst_gap_cm', 'boots_below_floor_px', 'head_to_figure', 'detached', 'max_anisotropy') if a[k] != b[k]]
                if ch:
                    L.append(f"- f{f} {v}: " + '; '.join(ch))
    gaps = [(f, r) for f, r in report['frames'].items() if r.get('kit_asked')]
    if gaps:
        L += ['', '## What Bolas asked for that no part can show (kit)', '',
              '| f | beat | face asked | effort | hands asked -> shown | library missing |', '| --: | :-- | :-- | --: | :-- | :-- |']
        for f, r in gaps:
            for a in r['kit_asked']:
                fc = a['face_asked'] or {}
                face = f"mouth {fc.get('mouth')} open {fc.get('open')} brow {fc.get('brow')} lid {fc.get('lid')} eyes {fc.get('eyes')}"
                hs = '; '.join(f"{v['asked']['side']} {v['asked']['shape']} {v['asked']['shows']} -> {v['shown'].replace('kit.hand.', '')}" for v in a['hands'].values() if v['asked'])
                L.append(f"| {f} | {r['beat'] or ''} | {face} -> {a['face_shown'].replace('man.head.', '')}{' **(head cannot show this)**' if a['face_gap'] else ''} | {a['effort']} | {hs} | {'; '.join(r.get('kit_missing', [])) or '-'} |")
    L += ['', '## For the critic', '',
          'Look at `board_f*.png` first, then the loupes for any joint named above. Answer with CRITICS.md.',
          'The cold read uses `keys_<variant>.png` only.']
    open(os.path.join(out, 'report.md'), 'w').write('\n'.join(L) + '\n')


if __name__ == '__main__':
    ap = argparse.ArgumentParser()
    ap.add_argument('act')
    ap.add_argument('--skin', default='man')
    ap.add_argument('--frames', default='')
    a = ap.parse_args()
    fr = [int(x) for x in a.frames.split(',') if x]
    r = run(a.act, a.skin, fr)
    print(open(os.path.join(HERE, 'out', a.act, 'report.md')).read())
