"""Cut every painted sheet that holds puppet parts (poem kits, v2 renders, tracksuit source sheets)
into cards in a work directory, with the release cutter (via cutter.py) and the strict brad reader.

    python3 shots/suite/tools/cut_all.py <workdir>     # writes <workdir>/cuts/<sheet>/*.png + <workdir>/cuts.json
"""
import json, os, sys
from concurrent.futures import ProcessPoolExecutor, as_completed
import cv2
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import cutter
import sheets as SH

SHOTS = SH.SHOTS


def safe(sid):
    return sid.replace(':', '__')


def job(args):
    s, work = args
    sid = safe(s['id'])
    res = cutter.cut(os.path.join(SHOTS, s['file']), sid, os.path.join(work, 'cuts'), flatten=True)
    for p in res.get('parts', []):
        rgba = cv2.imread(p['abs'], cv2.IMREAD_UNCHANGED)
        p['brads'] = cutter.brads(rgba)
        a = rgba[:, :, 3] > 128
        p['alpha_px'] = int(a.sum())
    return s['id'], res


def main(work):
    S = SH.inventory()
    todo = [s for s in S if s.get('holds_parts') and s['state'] == 'painted' and s['group'] in ('poem_kit', 'kit3_v2_render', 'tracksuit_source')]
    out = {}
    cache = os.path.join(work, 'cuts.json')
    if os.path.exists(cache):
        out = json.load(open(cache))
    todo = [s for s in todo if s['id'] not in out]
    print('to cut', len(todo))
    with ProcessPoolExecutor(max_workers=8) as ex:
        futs = [ex.submit(job, (s, work)) for s in todo]
        for i, f in enumerate(as_completed(futs)):
            sid, res = f.result()
            out[sid] = res
            if i % 25 == 0:
                print(i, sid, len(res.get('parts', [])), flush=True)
    json.dump(out, open(cache, 'w'))
    print('sheets cut', len(out), 'cards', sum(len(r.get('parts', [])) for r in out.values()))


if __name__ == '__main__':
    main(sys.argv[1])
