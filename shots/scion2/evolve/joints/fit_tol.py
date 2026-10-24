# Fit seam.py fail thresholds to the 48 blind-critic joint verdicts (train R01-R03, test R04).
# Features: proxy_fit/feat<N>.json, the current seam.py terms recomputed on each judged render with that round's
# own joint-lab code (git show of its commit; fit_feats.py). Run: python3 fit_tol.py from /tmp/claude-0/evolve-scratch/fit.
import json, numpy as np, itertools
V = json.load(open('/home/user/wygwyl-world-arch/shots/scion2/evolve/joints/critic_verdicts.json'))
rows = []
for n in (1, 2, 3, 4):
    F = json.load(open('feat%d.json' % n))
    for sh, v in V['round0%d' % n].items():
        f = F.get(sh, {})
        if 'error' in f or not f:
            continue
        rows.append((n, sh, v['verdict'] == 'CLEAN', v['score'], f))
print('sheets', len(rows))
TERMS = ['gap_frac', 'exposed_A_frac', 'exposed_B_frac', 'covered', 'colour_dE', 'registration_cm', 'grommet_peek', 'tab_visible_frac', 'trim_cut', 'light_rim', 'width_step']
def val(f, t):
    if t == 'width_step':
        r = f.get('width_ratio')
        try:
            r = float(r)
        except Exception:
            return 0.
        return max(r, 1 / r) if r > 0 else 0.
    v = f.get(t)
    try:
        return float(v) if v is not None else 0.
    except Exception:
        return 0.
X = np.array([[val(r[4], t) for t in TERMS] for r in rows])
y = np.array([r[2] for r in rows])
sc = np.array([r[3] for r in rows], float)
tr = np.array([r[0] <= 3 for r in rows]); te = ~tr
before = np.array([r[4].get('verdict') == 'CLEAN' for r in rows])
bnum = np.array([{'CLEAN': 1, 'WARN': .5}.get(r[4].get('verdict'), 0.) for r in rows])
def acc(pred, m): return float((pred[m] == y[m]).mean())
print('BEFORE  agreement train %.2f test %.2f | r(score) train %.2f test %.2f' % (acc(before, tr), acc(before, te),
      np.corrcoef(bnum[tr], sc[tr])[0, 1], np.corrcoef(bnum[te], sc[te])[0, 1]))
# fit per-term fail thresholds (coordinate descent on train agreement, ties -> looser)
th = {t: np.inf for t in TERMS}
def predict(th, Xm):
    return ~np.any(np.stack([Xm[:, i] > th[t] for i, t in enumerate(TERMS)], 1), 1)
for it in range(4):
    for i, t in enumerate(TERMS):
        cands = sorted(set(X[tr, i].tolist())) + [np.inf]
        best = (acc(predict(th, X), tr), th[t])
        for c in cands:
            th2 = dict(th); th2[t] = c
            a = acc(predict(th2, X), tr)
            if a > best[0] + 1e-9:
                best = (a, c)
        th[t] = best[1]
after = predict(th, X)
def margin(th, Xm):
    out = np.zeros(len(Xm))
    for i, t in enumerate(TERMS):
        if np.isfinite(th[t]) and th[t] > 0:
            out -= np.clip(Xm[:, i] / th[t] - 1, 0, None)
        elif np.isfinite(th[t]):
            out -= (Xm[:, i] > th[t]).astype(float)
    return out
mg = margin(th, X)
print('AFTER   agreement train %.2f test %.2f | r(score) train %.2f test %.2f' % (acc(after, tr), acc(after, te),
      np.corrcoef(mg[tr], sc[tr])[0, 1] if mg[tr].std() > 0 else float('nan'), np.corrcoef(mg[te], sc[te])[0, 1] if mg[te].std() > 0 else float('nan')))
print('fitted fail thresholds:', {t: (round(v, 3) if np.isfinite(v) else None) for t, v in th.items()})
print('critic CLEAN train %d/%d test %d/%d; fitted CLEAN test %d' % (y[tr].sum(), tr.sum(), y[te].sum(), te.sum(), after[te].sum()))
for r, p, m_ in zip(rows, after, mg):
    if r[0] == 4:
        print(r[1], 'critic', 'CLEAN' if r[2] else 'MUT', r[3], '| seam', r[4].get('verdict'), '| fitted', 'CLEAN' if p else 'MUT')
json.dump({'terms': TERMS, 'fitted_fail': {t: (v if np.isfinite(v) else None) for t, v in th.items()}}, open('fitted_tol.json', 'w'), indent=1)
from scipy.stats import spearmanr
print('per-term Spearman vs critic score (all 48):')
for i, t in enumerate(TERMS):
    if X[:, i].std() > 0:
        rho, p = spearmanr(X[:, i], sc)
        print('  %-18s rho %+.2f (p %.2f)  median clean %.3f / mutilated %.3f' % (t, rho, p, np.median(X[y, i]), np.median(X[~y, i])))
# logistic on all terms, CV leave-one-round-out
from sklearn.linear_model import LogisticRegression
Xs = (X - X.mean(0)) / (X.std(0) + 1e-9)
clf = LogisticRegression(C=.5, class_weight='balanced', max_iter=2000).fit(Xs[tr], y[tr])
pp = clf.predict(Xs)
print('logistic (balanced) agreement train %.2f test %.2f; r(prob, score) test %.2f' % (acc(pp, tr), acc(pp, te), np.corrcoef(clf.predict_proba(Xs[te])[:, 1], sc[te])[0, 1]))
print('weights', dict(zip(TERMS, np.round(clf.coef_[0], 2))))
