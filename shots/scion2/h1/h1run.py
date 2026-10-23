"""H1 runner: reproduce test poses (leave-one-family-out) and build painting|yours sheets.

python3 h1run.py kill   -> kill/<id>.png, kill/sheet.jpg (3 poses)
python3 h1run.py all    -> out/<id>.png, out/sheet.jpg, gaps.json (12 poses)
"""
import os, sys, json
import numpy as np, cv2
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import h1core as H, h1render as R

HERE = os.path.dirname(os.path.abspath(__file__))
REFUSE_OVER = 15.0  # degrees beyond the cap on any major part -> the target is not reached


def reproduce(tid, targets, cap=H.CAP):
    ranked = H.rank_sources(tid, targets)
    c, pid, v, info = ranked[0]
    T = H.markers(targets[tid])
    canvas, inf = R.render(pid, v, T, targets, H.family(tid), cap=cap)
    out = R.crop_to_height(canvas, R.figure_height(tid))
    F = inf['F']
    over = {b: round(F['want'][b], 1) for b in H.BONES
            if abs(F['want'][b]) > H.CAP and not b.startswith('foot')}
    reached = all(abs(F['want'][b]) <= H.CAP + REFUSE_OVER for b in H.BONES if not b.startswith('foot'))
    rec = dict(target=tid, source=pid, mirrored=v['mirror'], swapped_arms=v['swap_arm'],
               swapped_legs=v['swap_leg'], cost=round(c, 3), marker_err_torso_lengths=round(info['err'], 3),
               torso_fill_donor=inf['donor'], torso_fill_px=inf['filled'],
               rotation_applied={b: round(F['rot'][b], 1) for b in H.BONES},
               rotation_wanted_beyond_cap=over, reached=reached,
               runners_up=[(r[1], round(r[0], 3)) for r in ranked[1:4]])
    return out, rec


def trim(rgba):
    ys, xs = np.nonzero(rgba[..., 3] > 20)
    return rgba[ys.min():ys.max() + 1, xs.min():xs.max() + 1]


def label(img, text, sub=None):
    bar = np.full((44 if sub else 24, img.shape[1], 3), 255, np.uint8)
    cv2.putText(bar, text[:max(8, img.shape[1] // 7)], (4, 17), cv2.FONT_HERSHEY_SIMPLEX, .45, (0, 0, 0), 1, cv2.LINE_AA)
    if sub:
        cv2.putText(bar, sub[:max(8, img.shape[1] // 7)], (4, 37), cv2.FONT_HERSHEY_SIMPLEX, .4, (90, 90, 90), 1, cv2.LINE_AA)
    return np.vstack([bar, img])


def pair_tile(tid, out, rec, H_=420):
    tgt = trim(H.load_rgba(tid))
    k = H_ / tgt.shape[0]
    a = cv2.resize(R.flatten(tgt), (max(1, int(tgt.shape[1] * k)), H_), interpolation=cv2.INTER_AREA)
    b = cv2.resize(R.flatten(out), (max(1, int(out.shape[1] * k)), H_), interpolation=cv2.INTER_AREA)
    a = label(a, 'painting', tid.split('/')[0][5:7] + ' ' + tid.split('/')[1][:22])
    sub = ('from ' + rec['source'].split('/')[0][5:7] + ' ' + rec['source'].split('/')[1][:16]
           + (' (mirror)' if rec['mirrored'] else ''))
    b = label(b, 'H1' + ('' if rec['reached'] else ' NOT REACHED (cap)'), sub)
    gap = np.full((a.shape[0], 12, 3), 255, np.uint8)
    return np.hstack([a, gap, b])


def sheet(tiles, path, width=2600):
    rows, row, w = [], [], 0
    for t in tiles:
        if row and w + t.shape[1] + 30 > width:
            rows.append(row); row, w = [], 0
        row.append(t); w += t.shape[1] + 30
    rows.append(row)
    out = []
    for r in rows:
        hgt = max(t.shape[0] for t in r)
        line = np.full((hgt + 20, width, 3), 235, np.uint8)
        x = 10
        for t in r:
            line[10:10 + t.shape[0], x:x + t.shape[1]] = t; x += t.shape[1] + 30
        out.append(line)
    img = np.vstack(out)
    cv2.imwrite(path, img, [cv2.IMWRITE_JPEG_QUALITY, 88])


def run(ids, outdir, extra_uncapped=False):
    os.makedirs(outdir, exist_ok=True)
    targets = H.load_targets()
    tiles, recs = [], []
    for tid in ids:
        out, rec = reproduce(tid, targets)
        name = tid.replace('/', '__')
        cv2.imwrite(os.path.join(outdir, name + '.png'), out)
        tiles.append(pair_tile(tid, out, rec))
        if extra_uncapped:
            o2, r2 = reproduce(tid, targets, cap=180)
            cv2.imwrite(os.path.join(outdir, name + '__uncapped.png'), o2)
            r2['reached'] = True
            t2 = pair_tile(tid, o2, r2)
            t2 = label(t2[24 + 20:], 'diagnostic: same source, rotation cap lifted (not the method)')
            tiles.append(t2)
        recs.append(rec)
        print(tid, '<-', rec['source'], 'reached' if rec['reached'] else 'NOT reached', rec['rotation_wanted_beyond_cap'])
    sheet(tiles, os.path.join(outdir, 'sheet.jpg'))
    json.dump(recs, open(os.path.join(outdir, 'runs.json'), 'w'), indent=1)
    return recs


if __name__ == '__main__':
    ts = json.load(open(H.TESTSET))
    if sys.argv[1] == 'kill':
        ids = ['poet.13.main-poses/06-refocus', 'poet.04.main-poses/04-4-empty-cuffs', 'poet.13.main-poses/part-2']
        run(ids, os.path.join(HERE, 'kill'), extra_uncapped=True)
    else:
        run([p['id'] for p in ts['poses']], os.path.join(HERE, 'out'))
