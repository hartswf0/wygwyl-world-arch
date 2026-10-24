"""Fit Q's weights to the blind critic's closeness scores.

    python3 -m evolve.lab.calibrate            (from shots/scion2)

Data: every round<NN>/critic_verdicts.json ({'scores': {sheet: 0-10}}) joined through round<NN>/critic_key.json to the
metrics of that algorithm on that target in round<NN>/summary.json (per_target: the metrics of the render the critic
saw). Fits a ridge regression critic ~ coverage, overflow, (components > 1), pieces, snaps, clip, segments_missing;
reports the Pearson correlation with the critic of the current Q and of the fit (leave-one-out), and writes
calibration.json. With few judged sheets the fit is weak; it is reported, not used blindly.
"""
import glob, json, os
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
FEAT = ['coverage', 'overflow', 'disconnected', 'pieces', 'snaps', 'clip', 'segments_missing']


def rows():
    out = []
    for vf in sorted(glob.glob(os.path.join(HERE, 'round*/critic_verdicts.json'))):
        rd = os.path.dirname(vf)
        V = json.load(open(vf))['scores']
        K = json.load(open(os.path.join(rd, 'critic_key.json')))
        S = json.load(open(os.path.join(rd, 'summary.json')))['per_target']
        for sh, sc in V.items():
            k = K[sh]
            m = (S.get(k['target']) or {}).get(k['algo'])
            if not m:
                continue
            f = dict(m, disconnected=float(m['components'] > 1), segments_missing=m.get('segments_missing', np.nan))
            out.append((os.path.basename(rd), sh, k['algo'], k['target'], sc, f))
    return out


def main():
    R = rows()
    y = np.array([r[4] for r in R], float)
    X = np.array([[r[5].get(f, np.nan) for f in FEAT] for r in R], float)
    col = ~np.isnan(X).any(0)
    X = X[:, col]
    feats = [f for f, c in zip(FEAT, col) if c]
    q = np.array([r[5]['Q'] for r in R])
    Xs = (X - X.mean(0)) / (X.std(0) + 1e-9)
    lam = 1.0

    def fit(Xa, ya):
        A = np.hstack([Xa, np.ones((len(Xa), 1))])
        return np.linalg.solve(A.T @ A + lam * np.diag([1] * Xa.shape[1] + [0]), A.T @ ya)
    loo = []
    for i in range(len(y)):
        m = np.arange(len(y)) != i
        w = fit(Xs[m], y[m])
        loo.append(np.r_[Xs[i], 1] @ w)
    w = fit(Xs, y)
    res = {'n_sheets': len(y), 'features': feats, 'mean': X.mean(0).tolist(), 'std': (X.std(0) + 1e-9).tolist(), 'weights_standardised': dict(zip(feats + ['intercept'], np.round(w, 3).tolist())),
           'r_Q_vs_critic': float(np.corrcoef(q, y)[0, 1]) if len(y) > 2 else None,
           'r_fit_loo_vs_critic': float(np.corrcoef(loo, y)[0, 1]) if len(y) > 2 else None,
           'r_clip_vs_critic': float(np.corrcoef(X[:, feats.index('clip')], y)[0, 1]) if 'clip' in feats and len(y) > 2 else None,
           'sheets': [{'round': r[0], 'sheet': r[1], 'algo': r[2], 'target': r[3], 'critic': r[4], 'Q': round(r[5]['Q'], 3)} for r in R]}
    json.dump(res, open(os.path.join(HERE, 'calibration.json'), 'w'), indent=1)
    print(json.dumps({k: v for k, v in res.items() if k not in ('sheets', 'mean', 'std')}, indent=1))


def predict(m, cal):
    """the critic-calibrated proxy Qc for one target's metrics"""
    f = dict(m, disconnected=float(m['components'] > 1))
    x = (np.array([f[k] for k in cal['features']]) - cal['mean']) / np.array(cal['std'])
    w = cal['weights_standardised']
    return float(x @ np.array([w[k] for k in cal['features']]) + w['intercept'])


if __name__ == '__main__':
    main()
