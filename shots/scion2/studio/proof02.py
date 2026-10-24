"""Proof 02: the same performance two ways, rig deformation (proof 01's method) against pose
selection from the actor's own paintings (the swarm method), plus the decoder path.

    python3 -m studio.proof02           (run from shots/scion2; writes studio/proof02/)

The performance: the poet walks in (2 cycles, 3/4), stops, reaches forward, holds, lowers the arm,
turns to the front and settles. The proof scene of the Dynamic Pose Selection swarm, in our clips.
"""
import json, os, shutil, subprocess, math
import numpy as np, cv2

from studio import actions as act, select as sel
from studio.core import Actor, Performer, PX_PER_CM
from studio import proof as P1

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, 'proof02')
STAGE = P1.STAGE
CHAR, HEIGHT = 'poet__red_black_sunglasses', 183
F = cv2.FONT_HERSHEY_SIMPLEX


def performance(actor):
    walk = act.walk(2)
    stop = act.blend_in(act.stand('q3r', 10), 5)
    # dry run to find the shoulder after the walk, so the reach target is relative to this actor
    p = Performer(actor, STAGE, 140)
    for f in walk + stop:
        st = p.solve(f)
    sh = st['jp']['shL']
    J, s = actor.rigs['q3r'].J, actor.scale['q3r']
    arm = (np.linalg.norm(J['elL'] - J['shL']) + np.linalg.norm(J['tipL'] - J['elL'])) * s
    tgt = (float(sh[0] + 0.86 * arm), float(sh[1] + 0.05 * arm))
    reach = []
    for name, n, a, b in (('reach', 12, 'rest', tgt), ('hold', 10, tgt, tgt), ('lower', 12, tgt, 'rest')):
        for i in range(n):
            f = act.frame('q3r', act.STAND['q3r'], 'footR', contact={'footR': True, 'footL': True}, event=name)
            f['ik'] = {'L': {'from': a, 'to': b, 'u': act.ease((i + 1) / n)}}
            reach.append(f)
    turn = act.turn()
    # turn() goes front -> 3/4; we want 3/4 -> front: play its frames backwards
    back = [dict(f, event='turn' if f.get('event') else None) for f in reversed(turn)]
    settle = act.stand('front', 12)
    clip = walk + stop + reach + back + settle
    phases = (['walk'] * len(walk) + ['stop'] * len(stop) + ['reach'] * len(reach) + ['turn'] * len(back) + ['settle'] * len(settle))
    return clip, phases


WEIGHTS = {'walk': {'thigh': 1.6, 'shin': 1.2, 'uarm': 0.5, 'farm': 0.3, 'chest': 0.6},
           'stop': {'thigh': 1.0, 'shin': 1.0, 'uarm': 0.6, 'farm': 0.4, 'chest': 1.0},
           'reach': {'thigh': 0.4, 'shin': 0.4, 'uarm': 1.8, 'farm': 1.4, 'chest': 0.8},
           'turn': {'thigh': 0.8, 'shin': 0.8, 'uarm': 0.6, 'farm': 0.4, 'chest': 1.0},
           'settle': {'thigh': 0.8, 'shin': 0.8, 'uarm': 0.6, 'farm': 0.4, 'chest': 1.0}}


def backdrop():
    return P1.backdrop(False)


def encode(d, mp4):
    subprocess.run(['ffmpeg', '-y', '-loglevel', 'error', '-framerate', '24', '-i', os.path.join(d, '%04d.jpg'),
                    '-c:v', 'libx264', '-pix_fmt', 'yuv420p', '-crf', '21', '-movflags', '+faststart', mp4], check=True)


def run():
    shutil.rmtree(OUT, ignore_errors=True)
    os.makedirs(OUT)
    actor = Actor(CHAR, HEIGHT, 'poet')
    pr = actor.proportions()
    actor_cm = (pr['thigh'] + pr['shin'], pr['torso'])
    clip, phases = performance(actor)
    lib = sel.library(CHAR, costume='track')     # clean figures only: no props or scenery in the cutout
    print('library', len(lib), 'drawings')
    p = Performer(actor, STAGE, 140)
    sts = [p.solve(f) for f in clip]
    targets = [sel.target_from(st) for st in sts]
    weights = [WEIGHTS[ph] for ph in phases]
    per, path = sel.decode(lib, targets, weights)
    # render
    dirs = {k: os.path.join(OUT, '_f', k) for k in ('rig', 'sel', 'pair')}
    for d in dirs.values():
        os.makedirs(d)
    p = Performer(actor, STAGE, 140)
    for i, f in enumerate(clip):
        st = p.solve(f)
        a = backdrop(); P1.over(a, p.render(st))
        b = backdrop()
        k, err, sw = per[i]
        if err <= sel.GAP_DEG:
            img, s, tx, ty = sel.place(lib[k], sw, st, actor_cm, PX_PER_CM, STAGE['floor'])
            sel.paste(b, img, s, tx, ty)
        else:
            # a gap: the library has no drawing for this pose. Show the wanted pose as a ghost and say
            # so, instead of substituting the nearest wrong drawing
            ghost = p.render(st)
            g = ghost.copy(); g[..., :3] = 200; g[..., 3] = (g[..., 3] * 0.55).astype(np.uint8)
            P1.over(b, g)
            ys, xs = np.nonzero(ghost[..., 3] > 0)
            if len(xs):
                cv2.putText(b, 'NO DRAWING', (int(xs.min()), int(ys.min()) - 28), F, 0.7, (40, 40, 160), 2, cv2.LINE_AA)
                cv2.putText(b, 'commission: %s, %s' % (phases[i], 'front' if st['view'] == 'front' else '3/4 right'),
                            (int(xs.min()), int(ys.min()) - 8), F, 0.5, (40, 40, 160), 1, cv2.LINE_AA)
        cv2.imwrite(os.path.join(dirs['rig'], '%04d.jpg' % i), a, [cv2.IMWRITE_JPEG_QUALITY, 92])
        cv2.imwrite(os.path.join(dirs['sel'], '%04d.jpg' % i), b, [cv2.IMWRITE_JPEG_QUALITY, 92])
        pa, pb = a.copy(), b.copy()
        for im, t in ((pa, 'A  rig deformation (one painting bent to every pose)'),
                      (pb, 'B  pose selection (the poet\'s own paintings, chosen per beat)')):
            cv2.putText(im, t, (16, 34), F, 0.8, (255, 255, 255), 5, cv2.LINE_AA)
            cv2.putText(im, t, (16, 34), F, 0.8, (30, 30, 30), 2, cv2.LINE_AA)
        cv2.putText(pb, '%s  |  %s  |  pose error %.0f deg' % (phases[i], lib[k].id.split('/')[-1][:40] if err <= sel.GAP_DEG else 'gap', err), (16, 66), F, 0.6, (60, 60, 60), 1, cv2.LINE_AA)
        cv2.imwrite(os.path.join(dirs['pair'], '%04d.jpg' % i), np.vstack([pa, pb])[::2, ::2], [cv2.IMWRITE_JPEG_QUALITY, 90])
    for k, d in dirs.items():
        encode(d, os.path.join(OUT, '%s.mp4' % k))
    # decoder path strip: one tile per held drawing
    segs = []
    for i, (k, err, sw) in enumerate(per):
        if err > sel.GAP_DEG:
            k = -1
        if not segs or segs[-1]['k'] != k:
            segs.append({'k': k, 'f0': i, 'f1': i, 'err': [err], 'phase': phases[i]})
        else:
            segs[-1]['f1'] = i; segs[-1]['err'].append(err)
    TH = 220
    tiles = []
    for sg in segs:
        if sg['k'] < 0:
            t = np.full((TH, 150, 3), 235, np.uint8)
            cv2.rectangle(t, (4, 4), (145, TH - 64), (60, 60, 190), 2)
            cv2.putText(t, 'NO DRAWING', (14, 80), F, 0.55, (60, 60, 190), 2, cv2.LINE_AA)
            cv2.putText(t, 'f%d-%d %s' % (sg['f0'], sg['f1'], sg['phase']), (3, TH - 40), F, 0.4, (20, 20, 20), 1, cv2.LINE_AA)
            cv2.putText(t, 'best %.0f deg' % np.mean(sg['err']), (3, TH - 24), F, 0.4, (20, 20, 20), 1, cv2.LINE_AA)
            tiles.append(t)
            continue
        d = lib[sg['k']]
        im = d.image()
        a = im[..., 3:4] / 255.
        rgb = (im[..., :3] * a + 236 * (1 - a)).astype(np.uint8)
        sc = (TH - 60) / rgb.shape[0]
        rgb = cv2.resize(rgb, (max(1, int(rgb.shape[1] * sc)), TH - 60))
        t = np.full((TH, max(rgb.shape[1], 150), 3), 250, np.uint8)
        t[:TH - 60, :rgb.shape[1]] = rgb
        cv2.putText(t, 'f%d-%d %s' % (sg['f0'], sg['f1'], sg['phase']), (3, TH - 40), F, 0.4, (20, 20, 20), 1, cv2.LINE_AA)
        cv2.putText(t, 'err %.0f deg' % np.mean(sg['err']), (3, TH - 24), F, 0.4, (20, 20, 20), 1, cv2.LINE_AA)
        cv2.putText(t, d.id.split('/')[-1][:22], (3, TH - 8), F, 0.35, (90, 90, 90), 1, cv2.LINE_AA)
        tiles.append(t)
    rows, row, w = [], [], 0
    for t in tiles:
        if w + t.shape[1] > 1600 and row:
            rows.append(row); row, w = [], 0
        row.append(t); w += t.shape[1] + 6
    rows.append(row)
    strip = np.vstack([np.hstack(sum([[t, np.full((TH, 6, 3), 210, np.uint8)] for t in r], []) + [np.full((TH, 1600 - sum(t.shape[1] + 6 for t in r), 3), 210, np.uint8)]) for r in rows])
    cv2.imwrite(os.path.join(OUT, 'decoder_path.jpg'), strip, [cv2.IMWRITE_JPEG_QUALITY, 90])
    # coverage: per phase, how well the library covers the wanted pose
    cov = {}
    for ph in WEIGHTS:
        e = [per[i][1] for i in range(len(per)) if phases[i] == ph]
        cov[ph] = {'frames': len(e), 'mean_err_deg': round(float(np.mean(e)), 1), 'max_err_deg': round(float(np.max(e)), 1),
                   'gap_frames': int(sum(x > sel.GAP_DEG for x in e)),
                   'drawings': sorted({lib[per[i][0]].id for i in range(len(per)) if phases[i] == ph})}
    rep = {'library_size': len(lib), 'library': [d.id for d in lib], 'segments': [
        {'drawing': lib[s['k']].id if s['k'] >= 0 else None, 'frames': [s['f0'], s['f1']], 'phase': s['phase'], 'mean_err_deg': round(float(np.mean(s['err'])), 1)} for s in segs],
        'coverage': cov, 'distinct_drawings': len({s['k'] for s in segs if s['k'] >= 0}), 'switches': len(segs) - 1,
        'gap_frames': int(sum(e > sel.GAP_DEG for _, e, _ in per)), 'frames': len(per)}
    json.dump(rep, open(os.path.join(OUT, 'report.json'), 'w'), indent=1)
    shutil.rmtree(os.path.join(OUT, '_f'))
    print(json.dumps({k: v for k, v in rep.items() if k not in ('library',)}, indent=1)[:3000])


if __name__ == '__main__':
    run()
