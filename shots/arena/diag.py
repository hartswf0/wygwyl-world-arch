"""print a take's flags with the beats around them: python3 diag.py ACT-006 [frame ...]"""
import sys, json, numpy as np
sys.path.insert(0, '.')
import importlib, arena_lib as AL
cid = sys.argv[1]
m = importlib.import_module('challenges.' + cid.replace('-', '_').lower())
sc = m.build(); sc.solve(); tech, failing, acc = AL.check(sc)
print(json.dumps(tech['flagged_frame_ranges'], indent=0))
print(sorted([(b['f'], b['beat']) for b in sc.beats if b['beat'] not in ('passing', 'heel strike')]))
for a in sys.argv[2:]:
    fr = int(a)
    for n, J in ((n, sc.poses[n][fr]) for n in sc.actors):
        print(fr, n, {k: np.round(J[k]).tolist() for k in ('P', 'N', 'shR', 'elbR', 'palmR', 'hipR', 'kneeR', 'ankR', 'kneeL', 'ankL', 'toeL', 'toeR')},
              'reach', round(J['reachR'], 3), round(J['reachL'], 3), 'leg', {k: round(v, 1) for k, v in sc.leg_err[fr][n].items()},
              'herr', {k[1]: round(v[0], 1) for k, v in sc.hand_err[fr].items()})
