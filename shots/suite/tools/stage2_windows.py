#!/usr/bin/env python3
"""Stage 2 (poems 08-14): where each breakdown scene sits in the reading.

Each scene's lines (shots/poems/breakdown/NN.json) are matched to the poem's word stream on the suite clock
(kernel-data.json, faster-whisper word times) by shared word trigrams; every word of the reading is given to the
scene whose text it belongs to, gaps take the scene before, and the windows tile the poem's reading with no gap and no
overlap (so a poem's reel is its whole reading, in reading order). Scenes whose words are read in two places keep their
longest run; the other run joins its neighbour.

  python3 shots/suite/tools/stage2_windows.py [NN ...]   -> shots/suite/data/scenes/stage2_windows.json
"""
import os, re, sys, json
H = os.path.dirname(os.path.abspath(__file__)); SUITE = os.path.dirname(H); SHOTS = os.path.dirname(SUITE)
KERNEL = '/Users/gaia/cineosis-lab-cels/lab/bets/kernel-data.json'
norm = lambda w: re.sub(r"[^a-z0-9']", '', w.lower().replace('&', 'and'))

def words_of(poem, K):
    out = []
    for l in K['lines']:
        if l['id'].split('_')[0] != poem: continue
        for w in l.get('words', []): out.append((norm(w['w']), w['t0'], w['t1'], l['id'], w['w']))
    return sorted(out, key=lambda x: x[1])

# where the trigram match is fooled (the poem repeats a refrain across scenes, or the breakdown abridges a scene with
# '...'), the scene starts are set by hand, in reading order: (scene, kernel line id, first word of the scene)
STARTS = {
    '09': [('09.1', '09_L01', 'Accepting'), ('09.2', '09_L12', 'You'), ('09.3', '09_L22', 'She'), ('09.4', '09_L30', 'We')],
    '12': [('12.1', '12_L01', 'Decades'), ('12.3', '12_L02', 'My'), ('12.4', '12_L03', 'We'), ('12.2', '12_L05', 'This'), ('12.5', '12_L08', 'and')],
    '14': [('14.2', '14_L01', "Don't"), ('14.3', '14_L08', 'Whatever'), ('14.4', '14_L10', 'absent'), ('14.5', '14_L16', 'I'), ('14.6', '14_L20', 'and')],
}
# scenes with no words of their own: a wordless window between the previous poem's last scene and this poem's first word
PROLOGUE = {'14': ('14.1', '13')}
TAIL = {'14': 8.0}          # the last scene of the suite holds 8 s past its last word (the audio runs to 1440 s)

def windows_by_starts(poem, K, W):
    out = []
    for sid, lid, first in STARTS[poem]:
        i0 = next(i for i, w in enumerate(W) if w[3] == lid and w[0] == norm(first))
        out.append({'id': sid, 'i0': i0})
    for k, o in enumerate(out): o['i1'] = out[k + 1]['i0'] - 1 if k + 1 < len(out) else len(W) - 1
    return out

def windows(poem, K):
    bd = json.load(open(os.path.join(SHOTS, f'poems/breakdown/{poem}.json')))
    W = words_of(poem, K)
    if poem in STARTS: return finish(poem, bd, W, windows_by_starts(poem, K, W), K)
    toks = [w[0] for w in W]
    lab = [None] * len(W)
    for si, s in enumerate(bd['scenes']):
        st = [norm(x) for x in re.sub(r'\(.*?\)', ' ', s['lines']).replace('/', ' ').replace('—', ' ').split()]
        st = [x for x in st if x]
        grams = {tuple(st[i:i + 3]) for i in range(len(st) - 2)}
        for i in range(len(toks) - 2):
            if tuple(toks[i:i + 3]) in grams:
                for k in range(3):
                    if lab[i + k] is None: lab[i + k] = si
    # runs
    first = next((i for i, x in enumerate(lab) if x is not None), 0)
    for i in range(len(lab)):
        if lab[i] is None: lab[i] = lab[i - 1] if i > 0 and lab[i - 1] is not None else lab[first]
    runs = []
    for i, x in enumerate(lab):
        if runs and runs[-1][0] == x: runs[-1][2] = i
        else: runs.append([x, i, i])
    # each scene keeps its longest run (by time); shorter runs join the run before them
    best = {}
    for r in runs:
        d = W[r[2]][2] - W[r[1]][1]
        if r[0] not in best or d > best[r[0]][1]: best[r[0]] = (r, d)
    keep = [r for r in runs if best[r[0]][0] is r]
    out = []
    return finish(poem, bd, W, [{'id': bd['scenes'][r[0]]['id'], 'i0': r[1], 'i1': (keep[k + 1][1] - 1) if k + 1 < len(keep) else len(W) - 1} for k, r in enumerate(keep)], K)

def finish(poem, bd, W, out, K):
    # times: start just before the first word; end where the next one starts; the last scene breathes 1.2 s
    for k, o in enumerate(out):
        t_in = W[o['i0']][1] - 0.30 if k == 0 else out[k - 1]['out']
        if k + 1 < len(out): t_out = W[out[k + 1]['i0']][1] - 0.30
        else: t_out = min(K['duration'], W[o['i1']][2] + TAIL.get(poem, 1.2))
        o['in'], o['out'] = round(t_in, 3), round(t_out, 3)
        o['text'] = ' '.join(w[4] for w in W[o['i0']:o['i1'] + 1])
    if poem in PROLOGUE:
        sid, prev = PROLOGUE[poem]
        prev_out, _ = windows(prev, K)
        out.insert(0, {'id': sid, 'i0': None, 'i1': None, 'in': prev_out[-1]['out'], 'out': out[0]['in'], 'text': '(no words: the reading pauses between poems)'})
    missing = [s['id'] for s in bd['scenes'] if s['id'] not in {o['id'] for o in out}]
    return out, missing

if __name__ == '__main__':
    K = json.load(open(KERNEL))
    poems = sys.argv[1:] or [f'{n:02d}' for n in range(8, 15)]
    res = {}
    for p in poems:
        out, missing = windows(p, K)
        res[p] = {'scenes': out, 'unread': missing}
        for o in out: print(o['id'], o['in'], o['out'], round(o['out'] - o['in'], 2), o['text'][:110])
        if missing: print('  not matched in the reading:', missing)
    json.dump(res, open(os.path.join(SUITE, 'data/scenes/stage2_windows.json'), 'w'), indent=1)
