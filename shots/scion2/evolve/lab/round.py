"""One round of the algorithm lab.

    python3 -m evolve.lab.round <NN> <algo,algo,...> [--held] [--no-commit]      (from shots/scion2)

1. every listed algorithm on every TRAIN target (3 processes; a result is reused when the algorithm's file is
   unchanged since it was scored: lab/scores/<algo>/<target>.json + row/pair images);
2. round<NN>/summary.json + summary.md: means per algorithm, per-target table;
3. round<NN>/failures.jpg: the 6 worst TRAIN targets of the best algorithm (by mean Q);
4. round<NN>/critic/s01..s12.jpg: REFERENCE | RENDER only, no names, from the top 3 algorithms on random TRAIN targets;
   the key is round<NN>/critic_key.json (outside the folder);
5. evolve/live/latest.jpg: the best algorithm on 6 TRAIN targets;
6. --held: the best algorithm on HELD-OUT too (train vs held-out in summary);
7. commit + push evolve/lab and evolve/live.
"""
import colorsys, hashlib, json, math, os, random, subprocess, sys, time, traceback
from multiprocessing import Pool
import numpy as np, cv2
from PIL import Image, ImageDraw, ImageFont

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.abspath(os.path.join(HERE, '..', '..')))
from evolve.lab import harness as H  # noqa: E402

BENCH = json.load(open(os.path.join(HERE, 'benchmark.json')))
SCORES = os.path.join(HERE, 'scores')
LATEST = os.path.abspath(os.path.join(HERE, '..', 'live', 'latest.jpg'))
REPO = os.path.abspath(os.path.join(HERE, '..', '..', '..', '..'))
BRANCH = 'claude/cool-hypatia-2dxa8w'
SHOW = [0, 4, 5, 6, 14, 17]                   # TRAIN indices shown in latest.jpg (walk, arms up, hand at head, reach, tshirt, ex)
PH = 300


def font(sz, bold=False):
    p = '/usr/share/fonts/truetype/dejavu/DejaVuSans%s.ttf' % ('-Bold' if bold else '')
    return ImageFont.truetype(p, sz) if os.path.exists(p) else ImageFont.load_default()


F, FB, FS = font(13), font(15, True), font(10)


def safe(tid):
    return tid.replace('/', '__')


def algo_hash(name):
    src = open(os.path.join(HERE, 'algos', name + '.py'), 'rb').read()
    deps = b''
    for d in ('../puzzle/fill.py', '../puzzle/grow.py', '../puzzle/pieces.py', '../puzzle/hygiene.py', 'harness.py'):
        deps += open(os.path.join(HERE, d), 'rb').read()
    return hashlib.sha1(src + deps).hexdigest()[:12]


# ------------------------------------------------------------------ images
def to_rgb(bgra, box=None, bg=(235, 232, 226)):
    a = bgra[..., 3:] / 255.
    o = bgra[..., [2, 1, 0]] * a + np.array(bg, np.float32) * (1 - a)
    im = Image.fromarray(np.clip(o, 0, 255).astype(np.uint8))
    return im.crop(box) if box else im


def piece_map(ctx, asm, ms):
    t = ctx['t']
    H_, W = t['fig_t'].shape
    pm = np.full((H_, W, 3), 255, np.uint8)
    pm[t['fig_t']] = (228, 228, 228)
    n = len(ms)
    ncomp, roots = H.components(n, asm.get('edges', []))
    main = max(set(roots), key=roots.count) if n else None
    for i, m in enumerate(ms):
        col = tuple(int(255 * c) for c in colorsys.hsv_to_rgb((i * .61803) % 1, .7, .8))
        cnts, _ = cv2.findContours(m.astype(np.uint8), cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_NONE)
        cv2.drawContours(pm, cnts, -1, (220, 0, 0) if roots[i] != main else col, 3 if roots[i] != main else 1)
    bw = []
    for p in asm['pieces']:
        b = ctx['pieces'][p['pi']]['brads']
        M = np.asarray(p['M'], float)
        bw.append(b @ M[:, :2].T + M[:, 2] if len(b) else np.zeros((0, 2)))
    used = set()
    for i, bi, j, bj in asm.get('edges', []):
        if bi < 0 or bj < 0:                  # a skeleton-joint edge (seg_clip): no brads to draw between
            continue
        a_, b_ = bw[i][bi], bw[j][bj]
        cv2.line(pm, tuple(int(v) for v in a_), tuple(int(v) for v in b_), (0, 160, 0), 2)
        cv2.circle(pm, tuple(int(v) for v in a_), 3, (0, 170, 0), -1)
        used |= {(i, bi), (j, bj)}
    for i, b in enumerate(bw):
        for k, q in enumerate(b):
            if (i, k) not in used and 0 <= q[0] < W and 0 <= q[1] < H_:
                cv2.circle(pm, tuple(int(v) for v in q), 2, (220, 0, 0), -1)
    return Image.fromarray(pm)


def coverage_map(ctx, ms):
    t = ctx['t']
    fig, fd, ign = t['fig_t'], t['fig_dil'], t['ignore']
    U = np.zeros(fig.shape, bool)
    for m in ms:
        U |= m
    c = np.full(fig.shape + (3,), 255, np.uint8)
    c[fig & U] = (170, 170, 170)
    c[fig & ~U] = (30, 110, 220)
    c[U & ~fd & ~ign] = (220, 30, 30)
    c[ign & (t['ref'][..., 3] > 128)] = (255, 225, 120)
    return Image.fromarray(c)


def fit(im, h):
    k = h / im.height
    return im.resize((max(1, int(im.width * k)), h), Image.LANCZOS)


def row_image(ctx, asm, s, ms, ren, title):
    t = ctx['t']
    box = H.crop_box(t)
    ref = to_rgb(t['ref'].astype(np.float32), box)
    rr = to_rgb(ren, box)
    pm = piece_map(ctx, asm, ms).crop(box)
    cm = coverage_map(ctx, ms).crop(box)
    panels = [ref, rr, pm, cm]
    labels = ['REFERENCE', 'RENDER', 'PIECE MAP (green = snapped brads, red dot = free brad, thick red = disconnected)', 'COVERAGE (grey filled, blue empty, red overflow)']
    if asm.get('_seg') is not None:          # seg_clip family: the reference's SAM part regions beside the render
        Lm = asm['_seg']
        cols = np.array([[int(255 * c) for c in colorsys.hsv_to_rgb((i * .61803) % 1, .6, .9)] for i in range(16)], np.uint8)
        sg = np.full(Lm.shape + (3,), 255, np.uint8)
        sg[Lm >= 0] = cols[Lm[Lm >= 0]]
        panels.insert(2, Image.fromarray(sg).crop(box))
        labels.insert(2, 'SEGMENTATION (SAM part regions of the reference: guidance only)')
    ims = [fit(i, PH) for i in panels]
    pw = max(i.width for i in ims)
    W = 1600
    k = min(1., (W - 50) / (len(ims) * pw))
    ims = [i.resize((max(1, int(i.width * k)), max(1, int(i.height * k)))) for i in ims]
    ph = ims[0].height
    out = Image.new('RGB', (W, ph + 58), (255, 255, 255))
    d = ImageDraw.Draw(out)
    d.text((8, 4), title, fill=(28, 32, 38), font=FB)
    d.text((8, 24), 'coverage %.1f%%  overflow %.2f%%  components %d  pieces %d  snaps %d  CLIP %.3f  Q %.3f' %
           (100 * s['coverage'], 100 * s['overflow'], s['components'], s['pieces'], s['snaps'], s['clip'], s['Q']),
           fill=(180, 30, 30) if s['components'] != 1 or s['overflow'] > .005 else (28, 32, 38), font=F)
    x = 8
    for i, lab in zip(ims, labels):
        out.paste(i, (x, 44))
        x += (W - 16) // len(ims)
    return out


def pair_image(ctx, ren):
    t = ctx['t']
    box = H.crop_box(t)
    ref = fit(to_rgb(t['ref'].astype(np.float32), box), 420)
    rr = fit(to_rgb(ren, box), 420)
    out = Image.new('RGB', (ref.width + rr.width + 60, 470), (255, 255, 255))
    d = ImageDraw.Draw(out)
    out.paste(ref, (20, 40)); out.paste(rr, (40 + ref.width, 40))
    d.text((20, 12), 'REFERENCE', fill=(30, 110, 200), font=FB)
    d.text((40 + ref.width, 12), 'RENDER', fill=(215, 60, 40), font=FB)
    return out


# ------------------------------------------------------------------ jobs
def job(a):
    entry, algos, rnd = a
    out = []
    try:
        ctx = H.context(entry['char'], entry['costume'], entry['id'])
    except Exception as e:
        traceback.print_exc()
        return [{'algo': al, 'target': entry['id'], 'error': 'context: %r' % e} for al in algos]
    for al in algos:
        d = os.path.join(SCORES, al)
        os.makedirs(d, exist_ok=True)
        f = os.path.join(d, safe(entry['id']) + '.json')
        hsh = algo_hash(al)
        if os.path.exists(f):
            r = json.load(open(f))
            if r.get('hash') == hsh:
                out.append(r); continue
        try:
            asm = H.run(al, ctx, seed=0)
            s, ms, ren = H.score(ctx, asm)
            title = '%s  |  %s  |  round %s' % (entry['id'], al, rnd)
            row_image(ctx, asm, s, ms, ren, title).save(os.path.join(d, safe(entry['id']) + '_row.jpg'), quality=80)
            pair_image(ctx, ren).save(os.path.join(d, safe(entry['id']) + '_pair.jpg'), quality=85)
            r = {'algo': al, 'target': entry['id'], 'char': entry['char'], 'hash': hsh, 'scores': s, 'seconds': asm.get('seconds'),
                 'assembly': {'pieces': [{'id': ctx['pieces'][p['pi']]['id'], 'M': p['M']} for p in asm['pieces']], 'edges': asm['edges']},
                 'info': asm.get('info', {})}
        except Exception as e:
            traceback.print_exc()
            r = {'algo': al, 'target': entry['id'], 'error': repr(e), 'hash': hsh}
        json.dump(r, open(f, 'w'))
        out.append(r)
        print('%s %s %s' % (al, entry['id'], {k: round(v, 3) for k, v in r.get('scores', {}).items() if isinstance(v, (int, float))} if 'scores' in r else r.get('error')), flush=True)
    return out


def run_set(entries, algos, rnd, procs=3):
    tasks = [(e, algos, rnd) for e in entries]
    with Pool(procs) as P:
        res = P.map(job, tasks, chunksize=1)
    return [r for rs in res for r in rs]


def means(R, algo):
    rs = [r['scores'] for r in R if r['algo'] == algo and 'scores' in r]
    if not rs:
        return {}
    out = {k: float(np.nanmean([s[k] for s in rs])) for k in rs[0] if isinstance(rs[0][k], (int, float))}
    out['n'] = len(rs)
    out['one_component'] = sum(1 for s in rs if s['components'] == 1)
    return out


def git_commit(msg):
    try:
        subprocess.run(['git', 'add', 'shots/scion2/evolve/lab', 'shots/scion2/evolve/live'], cwd=REPO, check=True)
        if subprocess.run(['git', 'diff', '--cached', '--quiet'], cwd=REPO).returncode == 0:
            return
        subprocess.run(['git', 'commit', '-q', '-m', msg + '\n\nCo-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>\n'
                        'Claude-Session: https://claude.ai/code/session_012SuwqScw5qvLbAv3TLPPMi'], cwd=REPO, check=True)
        for _ in range(4):
            if subprocess.run(['git', 'push', '-u', 'origin', BRANCH], cwd=REPO).returncode == 0:
                return
            subprocess.run(['git', 'pull', '--no-rebase', '--no-edit', 'origin', BRANCH], cwd=REPO)
            time.sleep(5)
    except Exception:
        traceback.print_exc()


def main():
    rnd = int(sys.argv[1])
    algos = sys.argv[2].split(',')
    held = '--held' in sys.argv
    rd = os.path.join(HERE, 'round%02d' % rnd)
    os.makedirs(os.path.join(rd, 'critic'), exist_ok=True)
    t0 = time.time()
    R = run_set(BENCH['train'], algos, rnd)
    M = {a: means(R, a) for a in algos}
    ranked = sorted([a for a in algos if M[a]], key=lambda a: -M[a]['Q'])
    best = ranked[0]
    summ = {'round': rnd, 'algos': algos, 'ranked_by_Q': ranked, 'means': M, 'minutes': round((time.time() - t0) / 60, 1),
            'per_target': {e['id']: {a: next((r.get('scores') for r in R if r['algo'] == a and r['target'] == e['id']), None) for a in algos}
                           for e in BENCH['train']}}
    if held:
        RH = run_set(BENCH['held_out'], [best], rnd)
        summ['held_out'] = {'algo': best, 'train': M[best], 'held': means(RH, best),
                            'per_target': {r['target']: r.get('scores') for r in RH}}
    json.dump(summ, open(os.path.join(rd, 'summary.json'), 'w'), indent=1)
    md = ['# Round %02d' % rnd, '', '| algo | Q | coverage | overflow | components (mean) | one component | pieces | snaps | CLIP |',
          '|---|---|---|---|---|---|---|---|---|']
    for a in ranked:
        m = M[a]
        md.append('| %s | %.3f | %.1f%% | %.2f%% | %.1f | %d/%d | %.1f | %.1f | %.3f |' % (a, m['Q'], 100 * m['coverage'], 100 * m['overflow'],
                  m['components'], m['one_component'], m['n'], m['pieces'], m['snaps'], m['clip']))
    md += ['', '## per target (Q / coverage / components / CLIP)', '', '| target | ' + ' | '.join(ranked) + ' |', '|---|' + '---|' * len(ranked)]
    for e in BENCH['train']:
        cells = []
        for a in ranked:
            s = summ['per_target'][e['id']][a]
            cells.append('%.2f / %.0f%% / %d / %.2f' % (s['Q'], 100 * s['coverage'], s['components'], s['clip']) if s else 'error')
        md.append('| %s | %s |' % (e['id'], ' | '.join(cells)))
    if held:
        h = summ['held_out']
        md += ['', '## generalisation (%s)' % best, '', '| set | Q | coverage | overflow | one component | CLIP |', '|---|---|---|---|---|---|']
        for nm, m in (('TRAIN', h['train']), ('HELD-OUT', h['held'])):
            if m:
                md.append('| %s | %.3f | %.1f%% | %.2f%% | %d/%d | %.3f |' % (nm, m['Q'], 100 * m['coverage'], 100 * m['overflow'], m['one_component'], m['n'], m['clip']))
    open(os.path.join(rd, 'summary.md'), 'w').write('\n'.join(md) + '\n')
    # failure gallery
    worst = sorted([r for r in R if r['algo'] == best and 'scores' in r], key=lambda r: r['scores']['Q'])[:6]
    rows = [Image.open(os.path.join(SCORES, best, safe(r['target']) + '_row.jpg')) for r in worst]
    if rows:
        g = Image.new('RGB', (1600, sum(r.height for r in rows)), (255, 255, 255))
        y = 0
        for r in rows:
            g.paste(r, (0, y)); y += r.height
        g.save(os.path.join(rd, 'failures.jpg'), quality=80)
    # critic pack
    rng = random.Random(rnd)
    segs = [a for a in ranked if a.startswith('seg_')][:1]
    top = [a for a in ranked if not a.startswith('seg_')][:3 if not segs else 2] + segs
    picks = []
    pool = [(a, e['id']) for a in top for e in BENCH['train']
            if os.path.exists(os.path.join(SCORES, a, safe(e['id']) + '_pair.jpg'))]
    if segs:                                  # about a third of the sheets from the seg family, still blind
        sp = [x for x in pool if x[0] == segs[0]]; op = [x for x in pool if x[0] != segs[0]]
        rng.shuffle(sp); rng.shuffle(op)
        pool = sp[:4] + op
    else:
        rng.shuffle(pool)
    seen_t = {}
    for a, tid in pool:
        if seen_t.get(tid, 0) >= 1 and len({p[1] for p in pool}) > 12:
            continue
        picks.append((a, tid)); seen_t[tid] = seen_t.get(tid, 0) + 1
        if len(picks) == 12:
            break
    key = {}
    rng.shuffle(picks)                        # the seg sheets are not s01..s04
    for i, (a, tid) in enumerate(picks, 1):
        Image.open(os.path.join(SCORES, a, safe(tid) + '_pair.jpg')).save(os.path.join(rd, 'critic', 's%02d.jpg' % i), quality=88)
        key['s%02d' % i] = {'algo': a, 'target': tid}
    json.dump(key, open(os.path.join(rd, 'critic_key.json'), 'w'), indent=1)
    # latest
    rows = []
    for i in SHOW:
        e = BENCH['train'][i]
        p = os.path.join(SCORES, best, safe(e['id']) + '_row.jpg')
        if os.path.exists(p):
            rows.append(Image.open(p))
    if rows:
        hdr = 34
        g = Image.new('RGB', (1600, hdr + sum(r.height for r in rows)), (255, 255, 255))
        ImageDraw.Draw(g).text((8, 8), 'ALGORITHM LAB  round %02d  best by Q: %s  (TRAIN mean Q %.3f, coverage %.1f%%, one component %d/%d, CLIP %.3f)'
                               % (rnd, best, M[best]['Q'], 100 * M[best]['coverage'], M[best]['one_component'], M[best]['n'], M[best]['clip']),
                               fill=(28, 32, 38), font=FB)
        y = hdr
        for r in rows:
            g.paste(r, (0, y)); y += r.height
        os.makedirs(os.path.dirname(LATEST), exist_ok=True)
        g.save(LATEST + '.tmp.jpg', quality=78); os.replace(LATEST + '.tmp.jpg', LATEST)
    print(open(os.path.join(rd, 'summary.md')).read())
    if '--no-commit' not in sys.argv:
        git_commit('lab: round %02d (%s; best %s)' % (rnd, ', '.join(algos), best))


if __name__ == '__main__':
    main()
