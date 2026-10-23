"""Driver: fill target after target, learn zones, write live frames, commit now and then. Runs until stopped.

    cd shots/scion2 && nohup python3 -m evolve.puzzle.run > /tmp/claude-0/evolve-scratch/puzzle.log 2>&1 &

Order: the 4 kill poses (blind), then every other poet / ex pose with markers (blind), and every 3rd target
(and the 4 kill poses once 8 targets have zone data) also in 'prior' mode, so blind (the control) and prior can be
compared on the same target. Two worker processes.
"""
import glob, json, os, subprocess, sys, time, traceback
from multiprocessing import Pool

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.abspath(os.path.join(HERE, '..', '..')))
from evolve.puzzle import fill as FL, render as RD, zones as ZN  # noqa: E402
from evolve import assemble as AS  # noqa: E402

KILL = [('poet', 'red_black_sunglasses', 'poet.09.main-poses/falter-at-shoulder-contact'),
        ('poet', 'red_black_sunglasses', 'poet.04.main-poses/04-6-rise-flex-reflect'),
        ('poet', 'red_black_sunglasses', 'poet.13.main-poses/06-refocus'),
        ('ex', 'ex_jacket', 'ex.ex_jacket.master/back-view-neutral-stand-with-vape-pen-01')]
RESULTS = os.path.join(HERE, 'results.json')
COMMIT_EVERY = 25 * 60
REPO = os.path.abspath(os.path.join(HERE, '..', '..', '..', '..'))
BRANCH = 'claude/cool-hypatia-2dxa8w'
KEEP_FRAMES = 6


def all_targets():
    out = list(KILL)
    for ch, co in (('poet', 'red_black_sunglasses'), ('ex', 'ex_jacket')):
        T = AS.all_targets(ch)
        for tid, t in sorted(T.items()):
            if (ch, co, tid) in out or not t.get('markers') or 'neck' not in t['markers']:
                continue
            if not os.path.exists(os.path.join(AS.ROOT, 'shots/kits/cut', tid + '.webp')):
                continue
            if t.get('markers_use') is False:
                continue
            out.append((ch, co, tid))
    return out


def job(a):
    (ch, co, tid), mode, zones = a
    os.makedirs(RD.LIVE, exist_ok=True)
    tag_mode = mode

    def on_step(step, tag, P, pieces, t, masks):
        try:
            im, st = RD.frame(tid, step, tag, P, masks, pieces, t, tag_mode)
            RD.save(im, os.path.join(RD.LIVE, '%s_%s_%03d.jpg' % (RD.safe(tid), mode, step)))
            RD.save(im, os.path.join(RD.LIVE, '_row_%s_%s.jpg' % (RD.safe(tid), mode)))
            RD.montage([k[2] for k in KILL])
        except Exception:
            traceback.print_exc()
    try:
        r = FL.fill(ch, co, tid, mode=mode, zones=zones, on_step=on_step)
    except Exception as e:
        traceback.print_exc()
        return {'target': tid, 'mode': mode, 'error': repr(e)}
    # prune frames: first, last, and a few between
    fr = sorted(glob.glob(os.path.join(RD.LIVE, '%s_%s_*.jpg' % (RD.safe(tid), mode))))
    if len(fr) > KEEP_FRAMES:
        keep = {fr[int(round(i * (len(fr) - 1) / (KEEP_FRAMES - 1)))] for i in range(KEEP_FRAMES)}
        for f in fr:
            if f not in keep:
                os.remove(f)
    return {k: v for k, v in r.items() if not k.startswith('_')}


def git_commit(msg):
    paths = ['shots/scion2/evolve/puzzle', 'shots/scion2/evolve/live']
    try:
        subprocess.run(['git', 'add'] + paths, cwd=REPO, check=True)
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


def note(line):
    with open(os.path.join(RD.LIVE, 'notes.md'), 'a') as f:
        f.write('- %s %s\n' % (time.strftime('%Y-%m-%d %H:%M'), line))


def main():
    os.makedirs(RD.LIVE, exist_ok=True)
    R = json.load(open(RESULTS)) if os.path.exists(RESULTS) else {}
    targets = all_targets()
    queue = []
    for i, spec in enumerate(targets):
        queue.append((spec, 'blind'))
        if i >= 4 and i % 3 == 0:
            queue.append((spec, 'prior'))
    queue = [q for q in queue if '%s|%s' % (q[0][2], q[1]) not in R]
    last_commit = time.time()
    done = 0
    kill_prior_added = any(k.endswith('|prior') for k in R)
    with Pool(2) as pool:
        while queue:
            batch, queue = queue[:2], queue[2:]
            zones = ZN.load()
            res = pool.map(job, [(spec, mode, zones) for spec, mode in batch])
            for r in res:
                R['%s|%s' % (r['target'], r['mode'])] = r
                if 'error' not in r:
                    ZN.record(r)
                    done += 1
                    print('%s [%s] coverage %.1f%% overflow %.2f%% pieces %d (%.0fs)' % (r['target'], r['mode'], 100 * r['coverage'],
                                                                                        100 * r['overflow'], r['n_pieces'], r['seconds']), flush=True)
            json.dump(R, open(RESULTS + '.tmp', 'w'), indent=1)
            os.replace(RESULTS + '.tmp', RESULTS)
            ZN.write_relabel()
            if not kill_prior_added and ZN.n_fills() >= 8:
                queue = [(k, 'prior') for k in KILL] + queue
                kill_prior_added = True
            if done and done % 4 == 0:
                note(ZN.summary_line(R))
            if time.time() - last_commit > COMMIT_EVERY:
                git_commit('puzzle: blind silhouette fills, %d done (live frames, zones)' % len(R))
                last_commit = time.time()
    note('queue finished: %d fills' % len(R))
    git_commit('puzzle: queue finished, %d fills' % len(R))


if __name__ == '__main__':
    main()
