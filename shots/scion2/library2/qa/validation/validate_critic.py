"""Validate qa/detect.py against the blind critic's named defects on the joint lab's judged renders.

    python3 shots/scion2/library2/qa/validation/validate_critic.py CACHE_DIR

CACHE_DIR holds r<round>_<sheet>.npz re-renders: the joint lab's connect() for each critic_key.json entry, with
rgba, pm, cm, P, C, pivot, axis_p, axis_c, top, rs, brad_mask. The light-rim and colour detectors read the critic's
own JPEG (what was judged; the library images were defringed after rounds 01-04). That is mapped through the
lab's crop: a 30 cm radius around the pivot, scaled to 480 px wide. The geometric detectors (tab, grommet) read the
re-render.

The fit uses rounds 01-03, and round 04 is the held-out test. Writes qa/validation/report.json.
"""
import json, os, sys
import numpy as np
import cv2
from PIL import Image
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(HERE))
import detect as D  # noqa: E402

REPO = os.path.abspath(os.path.join(HERE, '..', '..', '..', '..', '..'))
JOINTS = os.path.join(REPO, 'shots', 'scion2', 'evolve', 'joints')
LAB = json.load(open(os.path.join(HERE, 'critic_labels.json')))
VER = json.load(open(os.path.join(JOINTS, 'critic_verdicts.json')))


def critic_frame(d, rnd, sh):
    """the critic JPEG and the map render px -> critic px"""
    im = np.array(Image.open(os.path.join(JOINTS, 'round%02d' % rnd, 'critic', '%s.jpg' % sh)).convert('RGB'))
    J = d['pivot']
    R = int(30 * float(d['rs']))
    H, W = d['rgba'].shape[:2]
    x0, y0 = int(max(0, J[0] - R)), int(max(0, J[1] - R))
    x1, y1 = int(min(W, J[0] + R)), int(min(H, J[1] + R))
    k = im.shape[1] / float(x1 - x0)
    return im, x0, y0, x1, y1, k


def to_critic(m, x0, y0, x1, y1, k, shape):
    c = m[y0:y1, x0:x1].astype(np.uint8)
    return cv2.resize(c, (shape[1], shape[0]), interpolation=cv2.INTER_NEAREST).astype(bool)


def features(path, rnd, sh):
    d = np.load(path, allow_pickle=True)
    top = str(d['top'])
    over = 'parent' if top == 'parent' else 'child'
    ppc = float(d['rs'])
    J = d['pivot']
    axP, axC = -d['axis_p'], d['axis_c']
    comp = d['rgba']
    al = comp[..., 3:] / 255.0
    rgb = (comp[..., :3] * al + 245 * (1 - al)).astype(np.uint8)
    brad = d['brad_mask'].astype(bool) if 'brad_mask' in d.files else None
    mP, mC = d['pm'].astype(bool), d['cm'].astype(bool)
    if brad is not None:          # the brad belongs to the top part
        if over == 'parent':
            mP = mP | brad
        else:
            mC = mC | brad
    f = {}
    # geometry and brass from the high-resolution re-render (10 px/cm) when there is one
    hp = os.path.join(os.path.dirname(path), 'hi_' + os.path.basename(path))
    if os.path.exists(hp):
        h = np.load(hp, allow_pickle=True)
        hal = h['rgba'][..., 3:] / 255.0
        hrgb = (h['rgba'][..., :3] * hal + 245 * (1 - hal)).astype(np.uint8)
        hb = h['brad_mask'].astype(bool) if 'brad_mask' in h.files else None
        hP, hC = h['pm'].astype(bool), h['cm'].astype(bool)
        if hb is not None:
            if over == 'parent':
                hP = hP | hb
            else:
                hC = hC | hb
        f['tab_cm2'], _ = D.tab_visible(hrgb, hP, hC, h['pivot'], -h['axis_p'], h['axis_c'], over, float(h['rs']), hb)
        g = D.grommet(hrgb, h['P'] if 'P' in h.files else None, h['C'] if 'C' in h.files else None, h['pivot'], float(h['rs']), hb)
    else:
        f['tab_cm2'], _ = D.tab_visible(rgb, mP, mC, J, axP, axC, over, ppc, brad)
        g = D.grommet(rgb, d['P'] if 'P' in d.files else None, d['C'] if 'C' in d.files else None, J, ppc, brad)
    f['grommet_measurable'] = float(not (rnd == 1))    # round 01 renders carry no part layers: no rings to measure
    f.update(registration_cm=g['registration_cm'] or 0.0, bare_brad=float(g['bare_brad']), crescent_cm=g['crescent_cm'],
             peek=0.0 if g['peek_frac'] is None else 1.0)
    im, x0, y0, x1, y1, k = critic_frame(d, rnd, sh)
    cP, cC = to_critic(mP, x0, y0, x1, y1, k, im.shape), to_critic(mC, x0, y0, x1, y1, k, im.shape)
    Jc = [(J[0] - x0) * k, (J[1] - y0) * k]
    f['light_rim'], _ = D.light_rim(im, cP, cC, Jc, over, ppc * k)
    f['colour_dE'] = D.colour_mismatch(im, cP, cC, Jc, over, ppc * k) or 0.0
    return f


def pr(pred, truth):
    tp = sum(p and t for p, t in zip(pred, truth))
    fp = sum(p and not t for p, t in zip(pred, truth))
    fn = sum(t and not p for p, t in zip(pred, truth))
    prec = tp / (tp + fp) if tp + fp else None
    rec = tp / (tp + fn) if tp + fn else None
    return dict(tp=tp, fp=fp, fn=fn, precision=None if prec is None else round(prec, 2), recall=None if rec is None else round(rec, 2))


TERMS = {   # term -> (feature(s), critic label)
    'tab_visible': (lambda f: f['tab_cm2'], 'tab'),
    'light_rim': (lambda f: f['light_rim'], 'rim'),
    'grommet': (lambda f: max(f['registration_cm'], f['crescent_cm'] * 3, 9 * f['bare_brad'], 9 * f['peek']), 'grommet'),
    'colour_jump': (lambda f: f['colour_dE'], 'colour'),
}


def main(cache):
    rows = []
    for rnd in (1, 2, 3, 4):
        for sh, labels in sorted(LAB['round%02d' % rnd].items()):
            p = os.path.join(cache, 'r%d_%s.npz' % (rnd, sh))
            if not os.path.exists(p):
                continue
            f = features(p, rnd, sh)
            v = VER['round%02d' % rnd][sh]
            rows.append(dict(round=rnd, sheet=sh, labels=labels, critic_clean=v['verdict'] == 'CLEAN', score=v['score'], f=f))
    train = [r for r in rows if r['round'] <= 3]
    test = [r for r in rows if r['round'] == 4]
    rep = {'n': len(rows), 'train': len(train), 'test': len(test), 'terms': {}}
    th = {}
    for t, (fx, lab) in TERMS.items():
        tr_ = [r for r in train if t != 'grommet' or r['f'].get('grommet_measurable', 1)]
        te_ = [r for r in test if t != 'grommet' or r['f'].get('grommet_measurable', 1)]
        al_ = [r for r in rows if t != 'grommet' or r['f'].get('grommet_measurable', 1)]
        train_, test_, rows_ = train, test, rows
        train, test, rows = tr_, te_, al_
        xs = sorted(set(round(fx(r['f']), 4) for r in train))
        best = None
        for c in xs + [1e9]:      # fire when value > c; maximise F1 on train
            pred = [fx(r['f']) > c for r in train]
            q = pr(pred, [lab in r['labels'] for r in train])
            f1 = 0 if not q['precision'] or not q['recall'] else 2 * q['precision'] * q['recall'] / (q['precision'] + q['recall'])
            if best is None or f1 > best[0] + 1e-9 or (best[0] == 0 and f1 == 0):
                best = (f1, c)        # ties at F1 = 0 move to the loosest threshold (never fire)
        th[t] = best[1]
        rep['terms'][t] = {'threshold': best[1], 'train': pr([fx(r['f']) > best[1] for r in train], [lab in r['labels'] for r in train]),
                           'test_r04': pr([fx(r['f']) > best[1] for r in test], [lab in r['labels'] for r in test]),
                           'all': pr([fx(r['f']) > best[1] for r in rows], [lab in r['labels'] for r in rows]),
                           'n_train': len(train), 'n_test': len(test)}
        train, test, rows = train_, test_, rows_
    # overall: the critic's CLEAN still names defects (it is a severity call), so CLEAN = at most K terms fire,
    # K fitted on train (rounds 01-03)
    nf = lambda r: sum(fx(r['f']) > th[t] for t, (fx, _) in TERMS.items() if t != 'grommet' or r['f'].get('grommet_measurable', 1))
    bestK = max(range(0, 5), key=lambda K: (np.mean([(nf(r) <= K) == r['critic_clean'] for r in train]), -K))
    rep['clean_if_at_most_terms_fire'] = int(bestK)

    def clean(r):
        return nf(r) <= bestK
    for nm, S in (('train', train), ('test_r04', test), ('all', rows)):
        rep['agreement_' + nm] = round(float(np.mean([clean(r) == r['critic_clean'] for r in S])), 3) if S else None
        cl = [r for r in S if r['critic_clean']]
        mu = [r for r in S if not r['critic_clean']]
        rep['on_critic_clean_' + nm] = '%d/%d called clean' % (sum(clean(r) for r in cl), len(cl))
        rep['on_critic_mutilated_' + nm] = '%d/%d called not clean' % (sum(not clean(r) for r in mu), len(mu))
    rep['critic_clean_rate'] = round(float(np.mean([r['critic_clean'] for r in rows])), 3)
    rep['rows'] = [dict(round=r['round'], sheet=r['sheet'], labels=r['labels'], critic_clean=r['critic_clean'],
                        f={k: round(v, 3) for k, v in r['f'].items()}, fired=[t for t, (fx, _) in TERMS.items() if fx(r['f']) > th[t]]) for r in rows]
    json.dump(rep, open(os.path.join(HERE, 'report.json'), 'w'), indent=1)
    print(json.dumps({k: v for k, v in rep.items() if k != 'rows'}, indent=1))


if __name__ == '__main__':
    main(sys.argv[1])
