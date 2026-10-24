"""Summary across joints: per part type, the gate counts (pass/warn/fail), the pair-angle counts (CLEAN / WARN /
MUTILATED / N/A), the main failure kinds, and the parts with the widest clean ranges.

    python3 shots/scion2/library2/qa/summary.py      # -> qa/summary.json + qa/sheets/summary.jpg
"""
import json, os, sys
from PIL import Image, ImageDraw
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(os.path.dirname(HERE), 'tools'))
import common as C  # noqa: E402


def main():
    out = {}
    for fn in sorted(os.listdir(os.path.join(HERE, 'results'))):
        if not fn.endswith('.json'):
            continue
        R = C.load_json(os.path.join(HERE, 'results', fn))
        best = []
        gates_fail = {}
        for key, e in R['parts'].items():
            g = e['gates']
            for t in ('cutoff', 'contamination', 'connection', 'view', 'identity'):
                if g.get(t, {}).get('result') == 'fail':
                    gates_fail[t] = gates_fail.get(t, 0) + 1
            for nb, p in e['pairs'].items():
                cr = p.get('clean_range')
                best.append(((cr[1] - cr[0]) if cr else -1, key, nb, cr))
        best.sort(key=lambda t: -t[0])
        out[fn[:-5]] = {'joint': R['joint'], 'angles': R['angles'], 'counts': R['counts'], 'gate_fails_by_test': gates_fail,
                        'widest_clean': [{'part': k, 'neighbour': n, 'clean_range': c} for _, k, n, c in best[:10]],
                        'pairs_with_any_clean_range': sum(1 for b in best if b[0] >= 0), 'pairs': len(best)}
    with open(os.path.join(HERE, 'summary.json'), 'w') as f:
        json.dump(out, f, indent=1)
    W, lh = 1500, 18
    lines = []
    for k, v in out.items():
        c = v['counts']
        lines.append(('%s  (%s joint)' % (k, v['joint']), (0, 0, 120)))
        lines.append(('  parts: %s   gate fails by test: %s' % (c['parts'], v['gate_fails_by_test']), (0, 0, 0)))
        lines.append(('  pair-angles: %s   pairs with a clean range around 0: %d of %d' % (c['pair_angles'], v['pairs_with_any_clean_range'], v['pairs']), (0, 0, 0)))
        lines.append(('  failure kinds: %s' % dict(sorted(c['kinds'].items(), key=lambda kv: -kv[1])), (120, 0, 0)))
        lines.append(('', (0, 0, 0)))
    S = Image.new('RGB', (W, 40 + lh * len(lines)), (255, 255, 255))
    d = ImageDraw.Draw(S)
    d.text((8, 8), 'library2 QA summary (qa/summary.json)', fill=(0, 0, 0), font=C.font(16))
    for i, (t, col) in enumerate(lines):
        d.text((8, 36 + i * lh), t[:200], fill=col, font=C.font(12))
    os.makedirs(os.path.join(HERE, 'sheets'), exist_ok=True)
    S.save(os.path.join(HERE, 'sheets', 'summary.jpg'), quality=90)
    print(json.dumps({k: v['counts'] for k, v in out.items()}, indent=0))


if __name__ == '__main__':
    main()
