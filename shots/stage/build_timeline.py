"""Timelines for the stage: each poem's scenes on her reading, with cues that fire on her words.

    python3 shots/stage/build_timeline.py            # all poems
    python3 shots/stage/build_timeline.py 04 07      # these

Reads (never writes): the word timings of her readings (butterfly-halfworld/wygwyl/timings/NN.json,
or the copy in shots/stage/timeline/words/), the scene book (shots/poems/atlas/NN.json), the stage
plan (shots/stage/plans/NN.json) and the cut catalog (shots/kits/cut/catalog.json).
Writes shots/stage/timeline/NN.json:

  {num, title, audio, duration, fps: 24, words: [{w, s, e}],
   scenes: [{key, name, t0, t1, lines: [{t, e, text, w: [i0, i1]}], book: [...], match: {...},
             cues: [{t, w, word, layer, action: show|hide|move|play|pose-swap, ...}]}],
   quality: {...}}

Alignment: the scene book lines are a paraphrase of her reading. Their tokens, in scene order, are
aligned to her words by a monotone dynamic-programming alignment (fuzzy word match, cheap gaps in the
reading, dearer gaps in the book). Each scene starts at its first anchored word; the cut is moved back
to the longest pause between the previous scene's last anchor and this one, so the picture cuts on
her breath. Scenes with no anchors are given a share of the gap by their length in the book.

Cues are a first pass, every one anchored to a word (index w into words; t is that word's start):
  play       the scene's solved action starts on its verb (walk, fall, turn, dance, wait ...)
             and the still pose hides on the same word (the pose swaps for the moving one)
  pose-swap  another of the poem's drawn poses swaps in on a word that names it (kneel, reach ...)
  show/hide  the tagged archive wipes in on a word of the scene's name (or mid-scene) and out
             at the end of that line
  show       a prop named in her words is held back and appears on that word
  move       the figure travels on walk / follow / run words, over the rest of the line
Edits on the stage override these per scene (saved in the browser and in the poem JSON export).
"""
import json, re, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SH = ROOT / 'shots'
OUT = SH / 'stage' / 'timeline'
SRC = Path('/home/user/hartswf0/butterfly-halfworld/wygwyl/timings')
FPS = 24

STOP = set('a an the of to and or in on at for with from by is it its i my me you your we our he she his her they them this that these those be am are was were will would as so but if not no do did done have has had there here what when where who how than then just into out up down over all any some one'.split())

ACT_VERBS = {
    1: 'walk carry step follow trail stroll wander pace', 2: 'run sprint rush race chase hurr',
    3: 'crouch duck bend kneel stoop', 4: 'spin turn twirl round search', 5: 'jump dive leap plunge swim',
    6: 'climb reach catch ledge grab hang', 7: 'slip slide stumbl', 8: 'fall fell trip stand rise ground',
    9: 'door push pull open', 10: 'lift heavy weigh box', 11: 'sit chair seat', 12: 'hand give hold offer take',
    13: 'punch hit strike fight', 14: 'kick', 15: 'block retreat', 16: 'sorry apolog fight friend',
    17: 'danc beat rhythm groove music', 18: 'danc spin partner twirl', 19: 'celebrat cheer joy win victor',
    20: 'danc stage wall room', 21: 'hide cower fear help afraid', 22: 'pretend carry smile fake',
    23: 'enter walk proud confiden arriv', 24: 'wait stand still time stay', 25: 'ball catch', 26: 'ball fake',
    27: 'ball kick miss', 28: 'ball late return', 29: 'carry table door', 30: 'door hold open',
    31: 'catch fall friend hold', 32: 'bump spill cup'}
MOVE_VERBS = 'walk follow run ride wander trail drift step chase cross come leav went go'.split()
POSE_SKIP = set('poet main poses pose reference separately supplied threequarter three quarter front profile only assembled guide small large every working body part prop parts card cards separate'.split())


def norm(w):
    return re.sub(r"[^a-z0-9]", '', w.lower().replace("’", "'").replace("'", ''))


def toks(text):
    return [t for t in (norm(x) for x in re.split(r"[\s/—–\-]+", text)) if t]


def lev(a, b):
    if a == b: return 0
    prev = list(range(len(b) + 1))
    for i, ca in enumerate(a, 1):
        cur = [i]
        for j, cb in enumerate(b, 1):
            cur.append(min(prev[j] + 1, cur[j - 1] + 1, prev[j - 1] + (ca != cb)))
        prev = cur
    return prev[-1]


def sim(a, b):
    if a == b: return 0.6 if a in STOP else 2.0
    if a in STOP or b in STOP: return 0
    if len(a) >= 4 and len(b) >= 4 and (a.startswith(b) or b.startswith(a) or a[:5] == b[:5]): return 1.6
    if len(a) >= 4 and len(b) >= 4 and 1 - lev(a, b) / max(len(a), len(b)) >= 0.75: return 1.2
    return 0


def words_of(num):
    f = SRC / f'{num}.json'
    if not f.exists(): f = OUT / 'words' / f'{num}.json'
    j = json.loads(f.read_text())
    W = []
    for seg in j['segments']:
        for k, w in enumerate(seg['words']):
            W.append({'w': w['w'].strip(), 's': round(w['s'], 3), 'e': round(w['e'], 3), **({'seg_start': True} if k == 0 else {})})
    return W, j['duration']


def ref(L, layers):
    base = L.get('id') or L.get('part') or ('action:' + L['action'] if L.get('action') else L.get('src', ''))
    n = sum(1 for M in layers[:layers.index(L)] if (M.get('id') or M.get('part') or ('action:' + M['action'] if M.get('action') else M.get('src', ''))) == base)
    return base + (f'#{n}' if n else '')


def kind(L):
    return L.get('kind') or ('part' if L.get('part') else 'action' if L.get('action') else 'image')


def lines_for(W, i0, i1):
    """Caption lines for words i0..i1-1: break on her segments, on pauses > .7 s, and keep lines short."""
    out, cur = [], []
    for k in range(i0, i1):
        if cur and (W[k].get('seg_start') or W[k]['s'] - W[k - 1]['e'] > 0.7 or len(cur) >= 12
                    or (len(cur) >= 7 and re.search(r'[,.;:?!]$', W[k - 1]['w']))):
            out.append(cur); cur = []
        cur.append(k)
    if cur: out.append(cur)
    # don't leave a one-word orphan line if it can join its neighbour
    res = []
    for c in out:
        if res and len(c) == 1 and len(res[-1]) < 12 and W[c[0]]['s'] - W[res[-1][-1]]['e'] < 0.7: res[-1] += c
        else: res.append(c)
    return [{'t': W[c[0]]['s'], 'e': W[c[-1]]['e'], 'text': ' '.join(W[k]['w'] for k in c), 'w': [c[0], c[-1]]} for c in res]


def stemhit(word, keys, minlen=3):
    w = norm(word)
    if len(w) < 3 or w in STOP: return None
    for k in keys:
        if len(k) >= minlen and (w == k or (w.startswith(k) and len(w) - len(k) <= 4) or (len(k) >= 5 and k.startswith(w) and len(w) >= 4)):
            return k
    return None


def align_in(B, W, lo, hi):
    """Align one scene's tokens B inside the reading W[lo:hi]: every book token is matched or paid for,
    the reading is free before and after. Returns (score, {book i: word j})."""
    n, m, GW, GB = len(B), hi - lo, 0.06, 0.45
    if m <= 0 or n == 0: return -1e9, {}
    S = [[0.0] * (m + 1) for _ in range(n + 1)]
    P = [[0] * (m + 1) for _ in range(n + 1)]
    for i in range(1, n + 1): S[i][0], P[i][0] = S[i - 1][0] - GB, 3
    for i in range(1, n + 1):
        for j in range(1, m + 1):
            best, p = S[i][j - 1] - GW, 2
            u = S[i - 1][j] - GB
            if u > best: best, p = u, 3
            s = sim(B[i - 1], W[lo + j - 1])
            if s > 0 and S[i - 1][j - 1] + s > best: best, p = S[i - 1][j - 1] + s, 1
            S[i][j], P[i][j] = best, p
    jbest = max(range(m + 1), key=lambda j: S[n][j])
    i, j, M = n, jbest, {}
    while i > 0 and j > 0:
        p = P[i][j]
        if p == 1: M[i - 1] = lo + j - 1; i -= 1; j -= 1
        elif p == 2: j -= 1
        else: i -= 1
    return S[n][jbest], M


def build(num, CAT):
    atlas = json.loads((SH / 'poems' / 'atlas' / f'{num}.json').read_text())
    plan_f = SH / 'stage' / 'plans' / f'{num}.json'
    plan = json.loads(plan_f.read_text()) if plan_f.exists() else {'scenes': []}
    pscenes = {s['key']: s for s in plan.get('scenes', [])}
    W, dur = words_of(num)
    WT = [norm(w['w']) for w in W]
    scenes = atlas['scenes']
    N = len(scenes)
    BT = [[t for line in s.get('lines', []) for t in toks(line)] for s in scenes]

    # 1. place each scene's book lines in her reading, strongest scenes first, never overlapping
    def strength(si):
        sc, M = align_in(BT[si], WT, 0, len(WT))
        content = sum(1 for bi in M if BT[si][bi] not in STOP)
        return content / max(1, len(BT[si])) + sc * 1e-3
    taken, span, anch = [], {}, {}
    for si in sorted(range(N), key=strength, reverse=True):
        free, a = [], 0
        for x0, x1 in sorted(taken):
            if x0 > a: free.append((a, x0))
            a = max(a, x1 + 1)
        if a < len(WT): free.append((a, len(WT)))
        best = (-1e9, {})
        for lo, hi in free:
            r = align_in(BT[si], WT, lo, hi)
            if r[0] > best[0]: best = r
        M = best[1]
        # a function word only anchors next to a content word (else 'the' pulls a scene far off)
        cj = sorted(j for bi, j in M.items() if BT[si][bi] not in STOP)
        M = {bi: j for bi, j in M.items() if BT[si][bi] not in STOP or any(abs(j - c) <= 2 for c in cj)}
        content = len(cj)
        n = sum(1 for t in BT[si] if t not in STOP)
        if M and (content >= 2 and content / max(1, n) >= 0.25 or (content >= 1 and n <= 3)):
            span[si] = (min(M.values()), max(M.values())); anch[si] = M; taken.append(span[si])

    # 2. order: anchored scenes in reading order; an unanchored scene follows its book predecessor
    order = sorted(span, key=lambda si: span[si][0])
    for si in range(N):
        if si in span: continue
        prev = max([k for k in range(si) if k in order], default=None)
        order.insert(order.index(prev) + 1 if prev is not None else 0, si)
    # first word index of each scene; unanchored ones take a share of the gap by book length
    start = {}
    for pos, si in enumerate(order):
        if si in span: start[si] = span[si][0]
    for pos, si in enumerate(order):
        if si in start: continue
        lo_pos = max([p for p in range(pos) if order[p] in span], default=None)
        hi_pos = min([p for p in range(pos + 1, len(order)) if order[p] in span], default=None)
        a = span[order[lo_pos]][1] + 1 if lo_pos is not None else 0
        b = span[order[hi_pos]][0] if hi_pos is not None else len(W)
        group = order[(lo_pos + 1 if lo_pos is not None else 0):(hi_pos if hi_pos is not None else len(order))]
        tot = sum(max(3, len(BT[k])) for k in group)
        before = sum(max(3, len(BT[k])) for k in group[:group.index(si)])
        start[si] = min(len(W) - 1, a + round((b - a) * before / tot))

    # 3. cut on the longest pause between the previous scene's last anchor and this scene's first word
    cuts = [0.0]
    for pos in range(1, len(order)):
        si, pv = order[pos], order[pos - 1]
        b = max(start[si], start[pv] + 1)
        a = min(max((span[pv][1] + 1) if pv in span else start[pv] + 1, start[pv] + 1), b)
        # the last breath (a pause of .3 s or a new phrase) before the scene's first anchored word,
        # else the longest pause in between
        ks = [k for k in range(max(1, a), b + 1) if W[k]['s'] - W[k - 1]['e'] >= 0.3 or W[k].get('seg_start')]
        bk = max(ks) if ks else max(range(max(1, a), b + 1), key=lambda k: W[k]['s'] - W[k - 1]['e'], default=b)
        bk = min(bk, len(W) - 1)
        gap = W[bk]['s'] - W[bk - 1]['e'] if bk > 0 else 0.3
        t = W[bk]['s'] - min(0.3, max(0.0, gap) * 0.5)
        t = max(t, cuts[-1] + 1.0)                     # never shorter than a second
        cuts.append(round(round(t * FPS) / FPS, 4))     # on a frame
        start[si] = bk
    cuts.append(round(dur, 3))

    out_scenes, qual = [], []
    for pos, si in enumerate(order):
        s = scenes[si]
        t0, t1 = cuts[pos], cuts[pos + 1]
        wi = [k for k, w in enumerate(W) if t0 <= w['s'] < t1]
        i0, i1 = (wi[0], wi[-1] + 1) if wi else (0, 0)
        lines = lines_for(W, i0, i1) if wi else []
        M = anch.get(si, {})
        cov = round(len(M) / max(1, len(BT[si])), 2)
        qual.append(cov)
        sc = {'key': s['key'], 'name': s.get('name', ''), 'book_index': si, 't0': t0, 't1': t1, 'lines': lines, 'book': s.get('lines', []),
              'match': {'how': 'anchored' if si in span else 'interpolated', 'book_tokens': len(BT[si]), 'anchored': len(M), 'coverage': cov,
                        'span': [W[span[si][0]]['s'], W[span[si][1]]['e']] if si in span else None,
                        'first_word': W[span[si][0]]['w'] if si in span else None}}
        sc['cues'] = cues_for(num, s, pscenes.get(s['key']), W, i0, i1, lines, t0, t1, CAT)
        out_scenes.append(sc)
    words = [{'w': w['w'], 's': w['s'], 'e': w['e']} for w in W]
    q = {'mean_coverage': round(sum(qual) / len(qual), 2), 'anchored_scenes': len(span), 'scenes': N,
         'book_order_kept': order == sorted(order)}
    return {'num': num, 'title': atlas.get('title', ''), 'audio': f'audio/{num}.mp3', 'duration': dur, 'fps': FPS,
            'source': f'word timings: wygwyl/timings/{num}.json (Whisper small.en on her reading); scenes: poems/atlas/{num}.json',
            'quality': q, 'words': words, 'scenes': out_scenes}


def cues_for(num, sb, ps, W, i0, i1, lines, t0, t1, CAT):
    if not ps or i1 <= i0: return []
    layers, cues = ps['layers'], []
    def cue(k, L, action, **kw):
        c = {'t': W[k]['s'], 'w': k, 'word': W[k]['w'], 'layer': ref(L, layers), 'action': action, 'auto': True}
        c.update(kw); cues.append(c); return c
    early = [k for k in range(i0, i1) if W[k]['s'] >= t0 + min(1.2, 0.2 * (t1 - t0))] or list(range(i0, i1))
    pose = next((L for L in layers if kind(L) == 'part' and L['part'].startswith('poet.') and 'main-poses' in L['part'] and not L.get('hide')), None) \
        or next((L for L in layers if kind(L) == 'part' and L['part'].startswith('poet.') and not L.get('hide')), None)
    used = set()

    # 1. the solved action plays on its verb; the still pose swaps out on the same word
    for L in [L for L in layers if kind(L) == 'action' and L.get('hide')][:1]:
        n = int(re.search(r'ACT-0*(\d+)', L['action']).group(1)) if re.search(r'ACT-0*(\d+)', L['action']) else 0
        keys = ACT_VERBS.get(n, '').split()
        k = next((k for k in early if stemhit(W[k]['w'], keys)), None)
        why = 'verb'
        if k is None:
            mid = max(early[0], lines[min(1, len(lines) - 1)]['w'][0] if lines else early[0])
            k = next((k for k in range(mid, i1) if norm(W[k]['w']) not in STOP), mid); why = 'fallback: second line'
        cue(k, L, 'play', mode='once', why=why); used.add(k)
        if pose: cue(k, pose, 'hide', why='the moving figure replaces the still')
        break

    # 2. another drawn pose of this poem swaps in on a word that names it
    if pose and not any(c['action'] == 'play' for c in cues):
        cands = []
        for sid, sh in CAT['sheets'].items():
            if sid.startswith(f'poet.{num}.main-poses'):
                for p in sh['parts']:
                    if p['id'] == pose['part']: continue
                    keys = [t for t in toks(p.get('label') or p['id'].split('/')[1]) if len(t) >= 4 and t not in POSE_SKIP and t not in STOP and not t.isdigit()]
                    if keys: cands.append((p['id'], keys))
        for k in early:
            hit = next((pid for pid, keys in cands if stemhit(W[k]['w'], keys, 4)), None)
            if hit: cue(k, pose, 'pose-swap', part=hit, why='her word names the pose'); used.add(k); break

    # 3. the figure travels on walk / follow / run words, over the rest of the line
    if pose and not any(c['action'] == 'play' for c in cues):
        k = next((k for k in early if stemhit(W[k]['w'], MOVE_VERBS)), None)
        if k is not None:
            le = next((l for l in lines if l['w'][0] <= k <= l['w'][1]), None)
            d = round(max(1.5, min(5.0, (le['e'] if le else W[k]['e']) - W[k]['s'] + 0.6)), 2)
            cue(k, pose, 'move', dx=-200 if pose.get('flip') else 200, dy=0, dur=d, why='a travelling word')

    # 4. props named in her words are held back and appear on that word (two at most)
    nprop = 0
    for L in layers:
        if nprop >= 2: break
        if kind(L) != 'part' or '.props.' not in L['part'] or L.get('hide'): continue
        keys = [t for t in toks(L['part'].split('/')[1]) if len(t) >= 4 and t not in POSE_SKIP and not re.match(r'^[a-z]?\d', t)]
        k = next((k for k in early if k not in used and stemhit(W[k]['w'], keys, 4)), None)
        if k is None: continue
        c0 = cue(i0, L, 'hide', why='held back until named'); c0['t'] = t0; c0.pop('w'); c0.pop('word')
        cue(k, L, 'show', fx='pop', why='named in her line'); nprop += 1

    # 5. the tagged archive wipes in on a word of the scene's name (else mid-scene) and out at the end of that line
    arch = [L for L in layers if kind(L) == 'image' and L.get('tag') and L.get('hide')]
    if arch and lines:
        L = arch[0]
        keys = [t for t in toks(sb.get('name', '')) if len(t) >= 4 and t not in STOP]
        k = next((k for k in early if stemhit(W[k]['w'], keys, 4)), None)
        why = 'a word of the scene name'
        if k is None:
            mid = max(early[0], lines[len(lines) // 2]['w'][0]); k = next((k for k in range(mid, i1) if norm(W[k]['w']) not in STOP), mid); why = 'mid-scene'
        le = next((l for l in lines if l['w'][0] <= k <= l['w'][1]), lines[-1])
        kend = min(i1 - 1, le['w'][1])
        if W[kend]['e'] - W[k]['s'] < 1.5: kend = min(i1 - 1, kend + 4)
        cue(k, L, 'show', fx='wipe', why=why)
        c = cue(kend, L, 'hide', fx='wipe', why='end of the line'); c['t'] = round(min(t1 - 0.1, W[kend]['e'] + 0.3), 3)
        c['dt'] = round(c['t'] - W[kend]['s'], 3)       # word-anchored: t = words[w].s + dt
    cues.sort(key=lambda c: c['t'])
    return cues


def main():
    nums = [a for a in sys.argv[1:] if re.match(r'^\d\d$', a)] or [f'{i:02d}' for i in range(1, 15)]
    CAT = json.loads((SH / 'kits' / 'cut' / 'catalog.json').read_text())
    OUT.mkdir(exist_ok=True)
    print(f"{'poem':5}{'scenes':>7}{'anch':>6}{'cov':>6}  scene windows (key t0-t1 coverage/first word)")
    for num in nums:
        T = build(num, CAT)
        (OUT / f'{num}.json').write_text(json.dumps(T, ensure_ascii=False, separators=(',', ':')))
        q = T['quality']
        sw = '  '.join(f"{s['key'][-1]}:{s['t0']:.1f}-{s['t1']:.1f} {s['match']['coverage']:.2f}/{s['match']['first_word'] or '~'}/{len(s['cues'])}c" for s in T['scenes'])
        print(f"{num:5}{q['scenes']:>7}{q['anchored_scenes']:>6}{q['mean_coverage']:>6}{'' if q['book_order_kept'] else ' R'}  {sw}")


if __name__ == '__main__':
    main()
