"""Render every marker pose of a character through its rigs.

python3 -m rigkit.cast <char>      (run from shots/scion2)
  -> shots/scion2/cast/<char>/poses/<painting id with / -> __>.png   RGBA on the painting's canvas
     shots/scion2/cast/<char>/contact_<n>.jpg                        painting | rig, same height
     shots/scion2/cast/<char>/poses.json                             view, sources of every part, params
     shots/scion2/cast/<char>/flags.json                             what the rig could not reach
"""
import json, os, sys
import numpy as np, cv2

from . import core, posing

OUT = os.path.join(os.path.dirname(core.HERE), 'cast')


def on_bg(rgba, bg=236):
    a = rgba[..., 3:] / 255.
    return (rgba[..., :3] * a + bg * (1 - a)).astype(np.uint8)


def contact(rows, path_fmt, H=300, per_page=24, maxw=2400):
    pages = [rows[i:i + per_page] for i in range(0, len(rows), per_page)]
    out = []
    for pi, pg in enumerate(pages):
        tiles = []
        for title, a, b, flag in pg:
            pair = [cv2.resize(on_bg(im), (max(1, int(im.shape[1] * H / im.shape[0])), H), interpolation=cv2.INTER_AREA) for im in (a, b)]
            t = np.hstack([pair[0], np.full((H, 4, 3), 255, np.uint8), pair[1]])
            if t.shape[1] > 900:
                k = 900 / t.shape[1]
                t = cv2.resize(t, (900, int(H * k)), interpolation=cv2.INTER_AREA)
                t = cv2.copyMakeBorder(t, 0, H - t.shape[0], 0, 0, cv2.BORDER_CONSTANT, value=(255, 255, 255))
            t = cv2.copyMakeBorder(t, 18, 0, 0, 0, cv2.BORDER_CONSTANT, value=(255, 255, 255))
            cv2.putText(t, title[5:50], (2, 13), cv2.FONT_HERSHEY_SIMPLEX, 0.38, (0, 0, 160) if flag else (0, 0, 0), 1, cv2.LINE_AA)
            tiles.append(t)
        rws, row, w = [], [], 0
        for t in tiles:
            if row and w + t.shape[1] > maxw:
                rws.append(row); row, w = [], 0
            row.append(t); w += t.shape[1] + 10
        rws.append(row)
        ims = [np.hstack(sum([[t, np.full((t.shape[0], 10, 3), 255, np.uint8)] for t in r], [])) for r in rws]
        W = max(i.shape[1] for i in ims)
        img = np.vstack([cv2.copyMakeBorder(i, 0, 8, 0, W - i.shape[1], cv2.BORDER_CONSTANT, value=(255, 255, 255)) for i in ims])
        p = path_fmt % (pi + 1)
        cv2.imwrite(p, img, [cv2.IMWRITE_JPEG_QUALITY, 85])
        out.append(p)
    return out


def run(char, ids=None):
    od = os.path.join(OUT, char); pd = os.path.join(od, 'poses')
    os.makedirs(pd, exist_ok=True)
    MK = core.load_markers(char)
    ids = ids or list(MK)
    rows, info, flags = [], {}, {}
    for tid in ids:
        try:
            pose = posing.pose_from_markers(char, tid)
            img = posing.render(pose)
        except Exception as e:      # never silently drop a pose: flag it
            flags[tid] = ['render failed: %r' % e]
            print('FAIL', tid, e)
            continue
        cv2.imwrite(os.path.join(pd, tid.replace('/', '__') + '.png'), img)
        info[tid] = {k: pose[k] for k in ('view', 'mirror', 'sources', 'opts', 'P', 'info')}
        if pose['flags']:
            flags[tid] = pose['flags']
        rows.append((tid, core.read_rgba(os.path.join(core.CUT, tid + '.webp')), img, bool(pose['flags'])))
        print(tid, pose['view'], pose['mirror'], pose['flags'], flush=True)
    if ids is not None and len(ids) < len(MK):
        contact(rows, os.path.join(od, 'contact_partial_%d.jpg'))
        return
    for f in os.listdir(od):
        if f.startswith('contact'):
            os.remove(os.path.join(od, f))
    contact(rows, os.path.join(od, 'contact_%d.jpg'))
    json.dump(info, open(os.path.join(od, 'poses.json'), 'w'), indent=1)
    for tid, why in getattr(core.char_module(char), 'EXCLUDE_TARGETS', {}).items():
        flags[tid] = ['not rendered: ' + why]
    json.dump(flags, open(os.path.join(od, 'flags.json'), 'w'), indent=1)


if __name__ == '__main__':
    run(sys.argv[1], sys.argv[2:] or None)
