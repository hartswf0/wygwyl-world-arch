"""A scene = a camera + 2-4 ensembles placed by depth + one focal action (+ extras as a group, props the scene
uses, at most one archive still placed in the world). See STAGING.md. Recipes live in recipes.py."""
import os, sys, re

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from lib import part, aspect, load_ensembles, PARTS
from resolve import Cam, resolve_ensemble, slot_pos, card_rect, overlap, rnd, clip_box

ENS = None
CHAR_CLIPS = {'poet_tracksuit': 'poet_tracksuit', 'poet_tshirt': 'poet_tshirt', 'ex': 'ex', 'woman': 'woman', 'young_poet': 'young_poet', 'party_guest': 'party_guest'}
ACT_FOR = [(r'\bwalk|stroll|climb|step|follow', 'ACT-001__man'), (r'kneel|crouch|search', 'ACT-003__man'),
           (r'\bfall|falls|fell|drop', 'ACT-008__man'), (r'danc|spin', 'ACT-017__man'), (r'wait|stand|sits?\b|seated|call', 'ACT-024__man')]


def figure(SC, n, C, cam, k, x, foot_y, pk):
    pid = part(C['pose'])
    bw, bh = PARTS[pid]['bbox'][2:]
    hcm = C.get('h_cm') or SC.character_cm(C.get('who', 'poet'), n)
    f = C.get('f') or SC.pose_factor(PARTS[pid].get('label') or pid, PARTS[pid]['bbox'])
    if f == 'lying':
        w = hcm * 1.05 * pk
        h = w * bh / bw
    else:
        h = hcm * f * pk
        w = h * bw / bh
    L = {'part': pid, 'x': rnd(x), 'y': rnd(foot_y - h / 2 + .01 * h), 'w': rnd(w), 'role': C.get('role', C.get('who', 'poet'))}
    if C.get('flip'):
        L['flip'] = True
    if C.get('op'):
        L['op'] = C['op']
    return L


def stage(n, sc, R, cam_d, SC, archive, actions):
    global ENS
    ENS = ENS or load_ensembles()
    cam = Cam(cam_d)
    items, seq, placed, named = [], [0], {}, {}
    for eid, place in R['ens']:
        E = ENS[eid]
        placed[eid] = (E, place)
        named[eid] = resolve_ensemble(E, place, cam, items, seq)
    focal = None
    poet_layer = None
    for C in R.get('cast', []):
        if C.get('slot'):
            eid, sname = C['slot'].split(':')
            E, place = placed[eid]
            S, k, x, fy, pk = slot_pos(E, place, sname, cam)
            k += C.get('dk', 0)
            x += C.get('dx', 0)
            if C.get('dk'):
                fy, pk = cam.at(k)
        elif C.get('portal'):   # a figure seen through a card's opening: (ensemble, card, [x, foot, height] in fractions of the opening)
            eid, hn, (fx, ffoot, fh) = C['portal']
            key, holder = named[eid][hn]
            x0, y0, x1, y1 = card_rect(holder)
            hx = holder.get('_hole') or [.3, .2, .7, .7]
            ox0, oy0, ox1, oy1 = x0 + hx[0] * (x1 - x0), y0 + hx[1] * (y1 - y0), x0 + hx[2] * (x1 - x0), y0 + hx[3] * (y1 - y0)
            x, fy, hpx = ox0 + fx * (ox1 - ox0), oy0 + ffoot * (oy1 - oy0), fh * (oy1 - oy0)
            k, pk = key + 1e-3, hpx / (C.get('h_cm') or SC.character_cm(C.get('who', 'poet'), n))
        else:
            k = C.get('k', 1.0)
            fy, pk = cam.at(k)
            x = C.get('x', 800)
            fy -= C.get('y_cm', 0) * pk
        L = figure(SC, n, C, cam, k, x, fy, pk)
        L['label'] = C.get('label', C.get('who', 'poet') + (' (focal)' if C.get('focal') else ''))
        seq[0] += 1
        items.append((k - 1e-5, seq[0], L))
        if C.get('reflect'):
            seq[0] += 1
            items.append((k - 1e-5 + 1e-6, seq[0], dict(L, y=rnd(fy + (fy - L['y'])), rot=180, flip=not L.get('flip', False),
                                                         op=C['reflect'] if isinstance(C['reflect'], float) else .35, role='reflection', label='reflection')))
        if C.get('focal'):
            focal = (L, k, fy, pk)
        if L['role'] == 'poet' and poet_layer is None:
            poet_layer = (L, k, fy, pk)
    for P in R.get('props', []):
        pid = part(P['ref'])
        k = P.get('k', 1.0)
        fy, pk = cam.at(k)
        h = P['h_cm'] * pk
        w = h / aspect(pid)
        L = {'part': pid, 'x': rnd(P.get('x', 800)), 'y': rnd(fy - P.get('y_cm', 0) * pk - h / 2), 'w': rnd(w), 'label': P.get('label', 'prop'), 'role': 'prop'}
        for kk in ('op', 'blend', 'rot', 'flip'):
            if kk in P:
                L[kk] = P[kk]
        seq[0] += 1
        items.append((k - 2e-5, seq[0], L))
    # the archive still: one, hidden until its cue, placed as an object in the world (a slot on a card)
    if archive and R.get('archive'):
        a = archive[R.get('archive_i', 0) % len(archive)]
        where = R['archive']
        if ':' in where:
            eid, sname = where.split(':')
            E, place = placed[eid]
            S = next(s for s in E['slots'] if s['name'] == sname)
            key, holder = named[eid][S['on']]
            if not holder.get('h'):
                holder['h'] = rnd(holder['w'] * aspect(holder['part']))
            x0, y0, x1, y1 = card_rect(holder)
            rx = S['rect'] if not holder.get('flip') else [1 - S['rect'][2], S['rect'][1], 1 - S['rect'][0], S['rect'][3]]
            a0, b0, c0, d0 = x0 + rx[0] * (x1 - x0), y0 + rx[1] * (y1 - y0), x0 + rx[2] * (x1 - x0), y0 + rx[3] * (y1 - y0)
            bw, bh = c0 - a0, d0 - b0
            w = min(bw, bh / a['ar'])
            L = {'kind': 'image', 'src': a['src'], 'x': rnd((a0 + c0) / 2), 'y': rnd((b0 + d0) / 2), 'w': rnd(w), 'ar': a['ar'],
                 'label': 'archive in the set (' + sname + '): ' + a['label'][:50], 'tag': a['tag'], 'op': .95, 'hide': True, 'role': 'archive', 'ens': eid}
            seq[0] += 1
            items.append((key - 3e-3, seq[0], L))
        else:   # 'sky@x,y,w': a memory hung in the sky (exteriors with no surface for it)
            m = re.match(r'sky@(\d+),(\d+),(\d+)', where)
            x, y, w = map(int, m.groups()) if m else (1250, 200, 300)
            L = {'kind': 'image', 'src': a['src'], 'x': x, 'y': y, 'w': w, 'ar': a['ar'], 'label': 'archive in the sky: ' + a['label'][:50],
                 'tag': a['tag'], 'blend': 'screen', 'op': .75, 'hide': True, 'role': 'archive'}
            seq[0] += 1
            items.append((5e7, seq[0], L))
    items.sort(key=lambda t: (-t[0], t[1]))
    layers = [L for _, _, L in items]
    # the hidden solved action takes the poet's place (the timeline plays it and hides the still pose)
    if poet_layer:
        L, k, fy, pk = poet_layer
        text = ' '.join([sc.get('what', ''), sc.get('name', ''), R.get('action_hint', '')])
        act = R.get('action') if R.get('action') is not None else next((a for rx, a in ACT_FOR if re.search(rx, text, re.I)), None)
        if act and R.get('shot') not in ('CU', 'INSERT', 'MS') and os.path.exists(os.path.join(os.path.dirname(HERE), f"anim/clips/{CHAR_CLIPS.get(R.get('costume', 'poet_tracksuit'))}/{act.split('__')[0]}.json")):
            ah = 180 * pk
            src = f"anim/clips/{CHAR_CLIPS.get(R.get('costume', 'poet_tracksuit'))}/{act.split('__')[0]}.json"
            B = clip_box(os.path.join(os.path.dirname(HERE), src))
            bx0, by0, bx1, by1 = B['box']
            sc_ = pk / B['cm_px']   # stage px per clip px at the pose's depth: the actor at its real height
            w, h = (bx1 - bx0) * sc_, (by1 - by0) * sc_
            A = {'kind': 'clip', 'src': src, 'x': rnd(L['x'] - (B['x_start'] - bx0) * sc_ + w / 2), 'y': rnd(fy + h / 2 - (B['floor'] - by0) * sc_),
                 'w': rnd(w), 'h': rnd(h), 'hide': True, 'role': 'action', 'fit': 'free', 'loop': False,
                 'label': 'solved action for this beat (the right character; plays on its verb, replacing the still pose; real size at this depth)'}
            layers.insert(layers.index(L) + 1, A)
        # the timeline takes the first poet main-pose layer as the pose: move the poet ahead of any other
        # character card from a poet sheet (the EX's cards live there) when nothing in between overlaps him
        i = layers.index(L)
        j = next((j for j, M in enumerate(layers[:i]) if M.get('part', '').startswith('poet.') and 'main-poses' in M.get('part', '')), None)
        if j is not None and not any(overlap(L, M) for M in layers[j:i] if M.get('h') or M.get('part')):
            moved = [layers.pop(i)]
            if i < len(layers) and layers[i].get('role') == 'action':
                moved.append(layers.pop(i))
            layers[j:j] = moved
    for fx in R.get('fx', []):   # screen washes in front (rain, haze)
        L = {'part': part(fx['ref']), 'x': fx.get('x', 800), 'y': fx.get('y', 450), 'w': fx.get('w', 1700), 'role': 'fx', 'label': fx.get('label', 'fx')}
        for kk in ('h', 'op', 'blend', 'rot', 'flip'):
            if kk in fx:
                L[kk] = fx[kk]
        layers.append(L)
    for L in layers:
        L.pop('_hole', None)
    return layers, focal
