#!/usr/bin/env python3
"""Scene windows on the suite clock, so a poem's scenes tile its reading end to end.

Each scene in shots/poems/breakdown/NN.json carries its lines; the reading (kernel-data.json, faster-whisper words on the
suite clock) is aligned to the breakdown text with difflib, word by word. A scene starts 0.35 s before its first word
(the first scene of a poem 1.0 s before), and ends where the next one starts (the last ends 1.6 s after the last word).

  python3 shots/suite/tools/stage_windows.py 01 02 ...   -> prints the windows; import windows(poem) from elsewhere
"""
import json, re, sys, difflib, os
KERNEL = '/Users/gaia/cineosis-lab-cels/lab/bets/kernel-data.json'
SHOTS = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
norm = lambda w: re.sub(r'[^a-z0-9]', '', w.lower().replace('&', 'and'))


def windows(poem, pre=0.35, first_pre=1.0, tail=1.6):
    K = json.load(open(KERNEL))
    W = [(w['w'], w['t0'], w['t1'], l['id']) for l in K['lines'] if l['film'] == poem for w in l['words']]
    b = json.load(open(os.path.join(SHOTS, 'poems/breakdown', poem + '.json')))
    toks, owner = [], []
    for k, s in enumerate(b['scenes']):
        for x in re.split(r'[\s/—\-–]+', s['lines']):
            if norm(x): toks.append(norm(x)); owner.append(k)
    kt = [norm(w[0]) for w in W]
    sm = difflib.SequenceMatcher(None, toks, kt, autojunk=False)
    m, blk = {}, {}
    for a, bb, n in sm.get_matching_blocks():
        for q in range(n): m[a + q] = bb + q; blk[a + q] = n
    starts, frac = [], []
    for k, s in enumerate(b['scenes']):
        idx = [i for i in range(len(toks)) if owner[i] == k]
        offs = [m[i] - (i - idx[0]) for i in idx if i in m and blk[i] >= 3]
        frac.append(sum(1 for i in idx if i in m) / max(1, len(idx)))
        # first kernel word of the scene: the earliest word that sits in a run of >= 3 matched words
        starts.append(offs[0] if offs and frac[-1] >= 0.3 else None)
    starts[0] = 0
    unread = [k for k in range(len(starts)) if starts[k] is None]
    for k in range(1, len(starts)):               # monotone
        if starts[k] is not None and starts[k] <= starts[k - 1 if starts[k - 1] is not None else 0]: starts[k] = None
    out = []
    read = [k for k in range(len(starts)) if starts[k] is not None]
    for k, s in enumerate(b['scenes']):
        o = {'id': s['id'], 'movement': s['movement'], 'match': round(frac[k], 2)}
        if starts[k] is None:
            o['unread'] = True                    # the reading does not speak this scene: it plays after the last word
        else:
            i0 = starts[k]; nxt = [starts[q] for q in read if q > k]; i1 = nxt[0] if nxt else len(W)
            o.update(w0=i0, w1=i1, first=W[i0][0], last=W[i1 - 1][0], **{'in': round(W[i0][1] - (first_pre if k == 0 else pre), 3)})
        out.append(o)
    K2 = [l for l in K['lines'] if l['film'] > poem]
    next_first = min((l['t0'] for l in K2), default=W[-1][2] + 12)
    for k, o in enumerate(out):
        if o.get('unread'):
            o['in'] = out[k - 1]['out'] if k else W[0][1] - first_pre
            o['out'] = round(min(max(o['in'] + 6, next_first - 1.0), o['in'] + 12), 3)
        else:
            nxt = next((q for q in out[k + 1:] if not q.get('unread')), None)
            o['out'] = nxt['in'] if nxt else round(W[-1][2] + (0.5 if k + 1 < len(out) else tail), 3)
        o['dur'] = round(o['out'] - o['in'], 3)
    return out, W


if __name__ == '__main__':
    for p in sys.argv[1:]:
        ws, W = windows(p)
        for o in ws: print(p, o['id'], f"{o['in']:8.2f}-{o['out']:8.2f} ({o['dur']:5.1f}s) match {o['match']}", 'UNREAD' if o.get('unread') else f"words {o['w0']}-{o['w1']}  {o['first']} … {o['last']}")
