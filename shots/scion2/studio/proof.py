"""The first proof: one scene, three actors, the same actions; six acceptance checks.

    python3 -m studio.proof            (run from shots/scion2; writes studio/proof01/)

Each actor plays each clip alone (the action matrix), then the scene plays twice with two
castings. The checks are measured on the solved skeleton, the painted silhouette and the
rendered pixels of every frame, never assumed from the clip.
"""
import json, math, os, shutil, subprocess, sys
import numpy as np, cv2

from studio import core, actions as act
from studio.core import Actor, Performer, PX_PER_CM, ang

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, 'proof01')
ROOT = os.path.abspath(os.path.join(HERE, '..', '..', '..'))
STAGE = {'W': 1280, 'H': 720, 'floor': 650}
DEPTH_PX = 60
PAPER = np.array([226, 232, 238], np.uint8)    # BGR warm paper
FLOOR = np.array([196, 206, 216], np.uint8)
PROP_IMG = os.path.join(ROOT, 'shots/kits/cut/02.props.tambourine/front.webp')
PROP_CM = 26.0
PLINTH = {'x0': 820, 'x1': 1060, 'top_cm': 92}

CAST = [('poet__red_black_sunglasses', 183, 'poet'),
        ('vintage_man__suit', 177, 'vintage man'),
        ('vintage_woman__gown', 166, 'vintage woman')]


# ------------------------------------------------------------------ drawing
def backdrop(plinth=False):
    W, H, fl = STAGE['W'], STAGE['H'], STAGE['floor']
    img = np.zeros((H, W, 3), np.uint8); img[:] = PAPER
    # the stage floor is a plane seen from the front: feet stand at different depths on it
    img[fl - DEPTH_PX:] = FLOOR
    cv2.line(img, (0, fl - DEPTH_PX), (W, fl - DEPTH_PX), (180, 190, 200), 1)
    cv2.line(img, (0, fl), (W, fl), (150, 165, 180), 2)
    if plinth:
        top = int(fl - PLINTH['top_cm'] * PX_PER_CM)
        cv2.rectangle(img, (PLINTH['x0'], top), (PLINTH['x1'], fl), (88, 112, 140), -1)
        cv2.rectangle(img, (PLINTH['x0'], top), (PLINTH['x1'], fl), (60, 84, 120), 3)
        cv2.rectangle(img, (PLINTH['x0'] - 8, top - 10), (PLINTH['x1'] + 8, top), (70, 96, 128), -1)
    return img


def over(dst, rgba):
    a = rgba[..., 3:4].astype(np.float32) / 255.
    dst[:] = (rgba[..., :3] * a + dst * (1 - a)).astype(np.uint8)


_PROP = {}


def prop_sprite():
    if 'p' not in _PROP:
        im = cv2.imread(PROP_IMG, cv2.IMREAD_UNCHANGED)
        ys, xs = np.nonzero(im[..., 3] > 8)
        im = im[ys.min():ys.max() + 1, xs.min():xs.max() + 1]
        s = PROP_CM * PX_PER_CM / max(im.shape[:2])
        _PROP['p'] = cv2.resize(im, None, fx=s, fy=s, interpolation=cv2.INTER_AREA)
    return _PROP['p']


def draw_prop(img, c):
    sp = prop_sprite()
    h, w = sp.shape[:2]
    x0, y0 = int(round(c[0] - w / 2)), int(round(c[1] - h / 2))
    lay = np.zeros((img.shape[0], img.shape[1], 4), np.uint8)
    xa, ya, xb, yb = max(0, x0), max(0, y0), min(img.shape[1], x0 + w), min(img.shape[0], y0 + h)
    if xb > xa and yb > ya:
        lay[ya:yb, xa:xb] = sp[ya - y0:yb - y0, xa - x0:xb - x0]
        over(img, lay)


def overlay(img, st, info):
    """skeleton, anchors and the frame's measurements on top of the render"""
    jp = st['jp']
    col = (40, 40, 200)
    for a, b in [('neck', 'midhip'), ('neck', 'headpiv'), ('headpiv', 'headtop'), ('shR', 'shL'), ('hipR', 'hipL'),
                 ('shR', 'elR'), ('elR', 'wrR'), ('wrR', 'tipR'), ('shL', 'elL'), ('elL', 'wrL'), ('wrL', 'tipL'),
                 ('hipR', 'knR'), ('knR', 'anR'), ('hipL', 'knL'), ('knL', 'anL')]:
        cv2.line(img, tuple(int(v) for v in jp[a]), tuple(int(v) for v in jp[b]), col, 2, cv2.LINE_AA)
    for k in jp:
        cv2.circle(img, tuple(int(v) for v in jp[k]), 3, (20, 20, 20), -1)
    fr = st['fr']
    for S in 'RL':
        if fr.get('contact', {}).get('foot' + S):
            ok = info.get('skate_cm', 0) < 0.5
            cv2.circle(img, tuple(int(v) for v in jp['an' + S]), 9, (40, 170, 40) if ok else (30, 30, 220), 2)
    x0, y0 = st['pts'].min(0); x1, y1 = st['pts'].max(0)
    cv2.rectangle(img, (int(x0), int(y0)), (int(x1), int(y1)), (160, 160, 160), 1)
    return img


def label(img, lines, color=(30, 30, 30)):
    for i, t in enumerate(lines):
        cv2.putText(img, t, (14, 28 + 24 * i), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 4, cv2.LINE_AA)
        cv2.putText(img, t, (14, 28 + 24 * i), cv2.FONT_HERSHEY_SIMPLEX, 0.6, color, 1, cv2.LINE_AA)


def encode(frames_dir, mp4):
    subprocess.run(['ffmpeg', '-y', '-loglevel', 'error', '-framerate', str(act.FPS), '-i', os.path.join(frames_dir, '%04d.jpg'),
                    '-c:v', 'libx264', '-pix_fmt', 'yuv420p', '-crf', '22', '-movflags', '+faststart', mp4], check=True)


# ------------------------------------------------------------------ measurement
def neck_attached(rgba, jp):
    """fraction of the collar -> head pivot segment covered by painted pixels (1.0 = attached)"""
    a, b = jp['collar'], jp['headpiv']
    n = 40
    al = rgba[..., 3]
    hit = 0
    for t in np.linspace(0, 1, n):
        x, y = (a + (b - a) * t).astype(int)
        if 0 <= y < al.shape[0] and 0 <= x < al.shape[1] and al[y, x] > 128:
            hit += 1
    return hit / n


def angle_err(st):
    """|measured world bone angle - clip angle| per bone (deg); arms solved by IK are skipped"""
    fr, jp = st['fr'], st['jp']
    if st['facing'] == 'L':
        W = STAGE['W']; jp = {k: np.array([W - p[0], p[1]]) for k, p in jp.items()}
    errs = {}
    ik = fr.get('ik', {})
    for b, (p, q) in core.BONES.items():
        if b[-1] in ik and b[:-1] in ('uarm', 'farm'):
            continue
        if 'gait' in fr and b[:-1] in ('thigh', 'shin'):       # legs placed by IK, checked by gait_err
            continue
        meas = ang(jp[q] - jp[p])
        want = math.radians(fr['bones'][b] + fr.get('body', 0.))
        errs[b] = abs(math.degrees(core.wrap(meas - want)))
    return errs


class Track:
    """per-frame records for one performer in one clip"""

    def __init__(self):
        self.rows = []
        self.lock_at = {}

    def add(self, i, st, rgba):
        fr, jp = st['fr'], st['jp']
        row = {'i': i, 'view': st['view'], 'event': fr.get('event'), 'anchor': fr.get('anchor'),
               'contact': {k: v for k, v in fr.get('contact', {}).items() if v},
               'neck': neck_attached(rgba, jp), 'low_px': float(st['pts'][:, 1].max() - STAGE['floor']),
               'root': [float(v) for v in (jp['midhip'])], 'ankles': {S: [float(v) for v in jp['an' + S]] for S in 'RL'},
               'tips': {S: [float(v) for v in jp['tip' + S]] for S in 'RL'},
               'headtop': float(jp['headtop'][1]), 'angle_err': angle_err(st), 'gait_err': st.get('gait_err')}
        # foot skate: drift of a planted ankle since it planted
        skate = 0.
        for S in 'RL':
            k = 'foot' + S
            if fr.get('contact', {}).get(k):
                if k not in self.lock_at:
                    self.lock_at[k] = np.array(jp['an' + S])
                skate = max(skate, float(np.linalg.norm(jp['an' + S] - self.lock_at[k])) / PX_PER_CM)
            else:
                self.lock_at.pop(k, None)
        row['skate_cm'] = skate
        self.rows.append(row)
        return row


# ------------------------------------------------------------------ playing
def play(perfs, clips, name, plinth=False, prop=None, director=None, ss=1):
    """render clips on performers side by side in one stage. clips: list of frame lists (same length
    or the director switches them). Writes <name>.mp4 and <name>_overlay.mp4; returns tracks."""
    d_plain = os.path.join(OUT, '_f', name); d_ov = d_plain + '_ov'
    for d in (d_plain, d_ov):
        shutil.rmtree(d, ignore_errors=True); os.makedirs(d)
    tracks = [Track() for _ in perfs]
    idx = [0] * len(perfs)
    clips = [list(c) for c in clips]
    n_total = max(len(c) for c in clips)
    i = 0
    poster = None
    while i < n_total:
        sts = []
        for k, p in enumerate(perfs):
            c = clips[k]
            fr = c[min(idx[k], len(c) - 1)]
            sts.append(p.solve(fr))
        if director:
            ch = director(i, sts, clips, idx)
            if ch:
                n_total = max(n_total, max(idx[k] + len(clips[k]) - idx[k] for k in range(len(perfs))))
                n_total = max(len(c) for c in clips)
                sts = [p.solve(clips[k][min(idx[k], len(clips[k]) - 1)]) for k, p in enumerate(perfs)]
        img = backdrop(plinth)
        rows = []
        layers = [p.render(st, ss) for p, st in zip(perfs, sts)]
        if prop is not None:
            pc = prop(i, sts)
        for k, (st, rgba) in enumerate(zip(sts, layers)):
            over(img, rgba)
            rows.append(tracks[k].add(i, st, rgba))
        if prop is not None:
            draw_prop(img, pc)
            rows[0]['prop'] = [float(v) for v in pc]
        cv2.imwrite(os.path.join(d_plain, '%04d.jpg' % i), img, [cv2.IMWRITE_JPEG_QUALITY, 92])
        ov = img.copy()
        for st, row in zip(sts, rows):
            overlay(ov, st, row)
        label(ov, ['%s  frame %d' % (name, i)] + ['%s: %s  skate %.2f cm  neck %.0f%%  view %s' %
                  (p.a.name, row['event'] or '', row['skate_cm'], 100 * row['neck'], row['view']) for p, row in zip(perfs, rows)])
        cv2.imwrite(os.path.join(d_ov, '%04d.jpg' % i), ov, [cv2.IMWRITE_JPEG_QUALITY, 88])
        if i == n_total // 2:
            poster = img
        for k in range(len(perfs)):
            idx[k] += 1
        i += 1
    encode(d_plain, os.path.join(OUT, name + '.mp4'))
    encode(d_ov, os.path.join(OUT, name + '_overlay.mp4'))
    cv2.imwrite(os.path.join(OUT, name + '.jpg'), poster if poster is not None else img, [cv2.IMWRITE_JPEG_QUALITY, 88])
    return tracks


def place_for_reach(actor, grasp_pt, S='L'):
    """stage x for the actor so the prop is at 85% of the arm's reach (blocking, not choreography)"""
    p = Performer(actor, STAGE, 300)
    st = p.solve(act.stand('q3r', 1)[0])
    sh = st['jp']['sh' + S]
    J, s = actor.rigs['q3r'].J, actor.scale['q3r']
    reach = (np.linalg.norm(J['el' + S] - J['sh' + S]) + np.linalg.norm(J['tip' + S] - J['el' + S])) * s * 0.85
    dy = grasp_pt[1] - sh[1]
    dx = math.sqrt(max(reach ** 2 - dy ** 2, (0.3 * reach) ** 2))
    return 300 + (grasp_pt[0] - dx - sh[0])


def grasp_points():
    fl = STAGE['floor']
    top = fl - PLINTH['top_cm'] * PX_PER_CM
    r = prop_sprite().shape[0] / 2
    d = 0.78 * r                                   # the hand holds the rim, the prop hangs below it
    grasp = (PLINTH['x0'] + 110, top - 2 * r + (r - d))
    place = (PLINTH['x0'] + 45, top - 2 * r + (r - d))      # set down nearer the actor, still on the plinth
    lift = (PLINTH['x0'] + 60, top - 2 * r - 70)
    return grasp, lift, place, d


def _py(o):
    return o.item() if hasattr(o, 'item') else str(o)


# ------------------------------------------------------------------ the checks
def run():
    os.makedirs(OUT, exist_ok=True)
    cast = [Actor(c, h, n) for c, h, n in CAST]
    res = {'stage': STAGE, 'px_per_cm': PX_PER_CM, 'actors': {}, 'cells': {}, 'scenes': {}, 'checks': {}}
    for a in cast:
        res['actors'][a.name] = {'char': a.char, 'proportions': a.proportions()}
    grasp, lift, place, d = grasp_points()
    clips = {'walk': act.walk(2), 'turn': act.turn(), 'grasp': act.grasp_release(grasp, lift, place),
             'fall': act.fall_recover()}
    for a in cast:
        for cname, clip in clips.items():
            x = {'walk': 160, 'turn': 520, 'fall': 640}.get(cname)
            if cname == 'grasp':
                x = place_for_reach(a, grasp)
            p = Performer(a, STAGE, x)
            prop = None
            if cname == 'grasp':
                state = {'c': np.array(grasp) + (0, d)}

                def prop(i, sts, state=state):
                    fr = sts[0]['fr']
                    if fr.get('contact', {}).get('handL') == 'prop':
                        state['c'] = np.array(sts[0]['jp']['tipL']) + (0, d)
                    return state['c']
            name = '%s__%s' % (a.name.replace(' ', '_'), cname)
            print('render', name, len(clip), flush=True)
            tr = play([p], [clip], name, plinth=(cname == 'grasp'), prop=prop)[0]
            res['cells'][name] = {'actor': a.name, 'action': cname, 'frames': len(clip), 'rows': tr.rows}
            json.dump(res['cells'][name], open(os.path.join(OUT, 'rows_%s.json' % name), 'w'), default=_py)
    # the scene, twice: casting A then casting B (roles swapped); blocking adapts, beats do not
    for tag, roles in (('A', (0, 1, 2)), ('B', (2, 0, 1))):
        res['scenes'][tag] = scene(cast, roles, tag)
    res['checks'] = checks(res, cast)
    json.dump(res, open(os.path.join(OUT, 'results.json'), 'w'), indent=0, default=_py)
    shutil.rmtree(os.path.join(OUT, '_f'), ignore_errors=True)
    for k, v in res['checks'].items():
        print(k, 'PASS' if v['pass'] else 'FAIL', v['summary'])
    return res


MEET = 34   # the collision lands on this frame in every casting


def stride_px(actor):
    """how far one walk cycle carries this actor (measured by a dry run, no rendering)"""
    p = Performer(actor, STAGE, 200)
    xs = [p.solve(f)['jp']['midhip'][0] for f in act.walk(1)]
    return xs[-1] - xs[0], xs


def scene(cast, roles, tag):
    """two actors walk at each other and collide on frame MEET; both fall and recover; the third
    turns to look. Start marks are solved per actor from its own stride so the beat stays on MEET."""
    A, B, C = (cast[k] for k in roles)
    walkA, walkB = act.walk(3), act.walk(3)
    # dry runs: where the front of each body is after MEET frames
    def front_after(actor, x0, facing):
        p = Performer(actor, STAGE, x0, facing)
        st = None
        for f in walkA[:MEET]:
            st = p.solve(f)
        return st['pts'][:, 0].max() if facing == 'R' else st['pts'][:, 0].min()
    centre = STAGE['W'] / 2 + 60
    xa = 200 + (centre - front_after(A, 200, 'R'))
    xb = 1080 + (centre - front_after(B, 1080, 'L'))      # x is the stage position for either facing
    pa, pb = Performer(A, STAGE, xa, 'R'), Performer(B, STAGE, xb, 'L')
    pc = Performer(C, STAGE, 150, 'R')
    fall = act.fall_recover()
    clipC = act.stand('front', MEET - 6) + act.turn(6, len(fall) + 10)
    hit = {'frame': None}

    def director(i, sts, clips, idx):
        a_front, b_front = sts[0]['pts'][:, 0].max(), sts[1]['pts'][:, 0].min()
        if hit['frame'] is None and a_front >= b_front - 1:
            hit['frame'] = i
            for k in (0, 1):
                # fall about whichever foot is planted at the hit, easing in from the walk pose
                cur = clips[k][min(idx[k], len(clips[k]) - 1)]
                f = fall if cur.get('contact', {}).get('footR') else act.mirror_sides(fall)
                clips[k] = clips[k][:idx[k]] + act.blend_in(f)
            return True
        return False
    name = 'scene_%s' % tag
    print('render', name, flush=True)
    trs = play([pa, pb, pc], [walkA, walkB, clipC], name, director=director)
    fall_start = [next((r['i'] for r in t.rows if r['event'] == 'fall'), None) for t in trs[:2]]
    return {'roles': {'walker_R': A.name, 'walker_L': B.name, 'watcher': C.name}, 'marks': [xa, xb, 150],
            'hit_frame': hit['frame'], 'fall_start': fall_start,
            'tracks': {p.a.name: t.rows for p, t in zip((pa, pb, pc), trs)}}


def checks(res, cast):
    C = {}
    # 1 distinct proportions: every pair differs by >= 3% in at least one ratio (to height), and each actor's
    #   bones keep their length through every frame (length channels are never touched)
    pr = {n: v['proportions'] for n, v in res['actors'].items()}
    keys = ['torso', 'thigh', 'shin', 'upper_arm', 'forearm', 'shoulders', 'head']
    names = list(pr)
    pairs = []
    for i in range(len(names)):
        for j in range(i + 1, len(names)):
            a, b = pr[names[i]], pr[names[j]]
            dif = max(abs(a[k] / a['height'] - b[k] / b['height']) / (b[k] / b['height']) for k in keys)
            pairs.append([names[i], names[j], round(100 * dif, 1)])
    C['1_distinct_proportions'] = {'pass': all(p[2] >= 3 for p in pairs), 'pairs_max_ratio_diff_pct': pairs,
                                   'summary': '; '.join('%s/%s %.1f%%' % tuple(p) for p in pairs)}
    # 2 walk without sliding: planted ankle drift < 0.5 cm, no pixel below the floor, and it travelled
    out = {}
    for n in names:
        rows = res['cells']['%s__walk' % n.replace(' ', '_')]['rows']
        sk = max(r['skate_cm'] for r in rows)
        pen = max(r['low_px'] for r in rows) / PX_PER_CM
        travel = (rows[-1]['root'][0] - rows[0]['root'][0]) / PX_PER_CM
        out[n] = {'max_skate_cm': round(sk, 3), 'max_below_floor_cm': round(pen, 2), 'travel_cm': round(travel, 1),
                  'pass': sk < 0.5 and pen < 0.5 and travel > 50}
    C['2_walk_no_slide'] = {'pass': all(v['pass'] for v in out.values()), 'actors': out,
                            'summary': '; '.join('%s skate %.2f cm, below floor %.1f cm, travel %.0f cm' %
                                                 (n, v['max_skate_cm'], v['max_below_floor_cm'], v['travel_cm']) for n, v in out.items())}
    # 3 front -> profile turn: head attached on every frame (painted pixels along collar->head pivot),
    #   feet do not jump at the drawing swap, height holds
    out = {}
    for n in names:
        rows = res['cells']['%s__turn' % n.replace(' ', '_')]['rows']
        sw = next(i for i, r in enumerate(rows) if r['event'] == 'swap')
        feet = lambda r: np.mean([r['ankles']['R'][0], r['ankles']['L'][0]])
        jump = abs(feet(rows[sw]) - feet(rows[sw - 1])) / PX_PER_CM
        hgt = lambda r: STAGE['floor'] - r['headtop']
        dh = abs(hgt(rows[sw]) - hgt(rows[sw - 1])) / hgt(rows[sw - 1])
        neck = min(r['neck'] for r in rows)
        out[n] = {'min_neck_cover': round(neck, 3), 'feet_jump_cm': round(jump, 2), 'height_change_pct': round(100 * dh, 1),
                  'pass': neck >= 0.95 and jump < 6 and dh < 0.06}
    C['3_turn_head_attached'] = {'pass': all(v['pass'] for v in out.values()), 'actors': out,
                                 'summary': '; '.join('%s neck %.0f%%, feet jump %.1f cm, height %.1f%%' %
                                                      (n, 100 * v['min_neck_cover'], v['feet_jump_cm'], v['height_change_pct']) for n, v in out.items())}
    # 4 grasp and release the same prop: the hand reaches the prop (< 1.5 cm) on the take frame, the prop
    #   lands at its place mark (< 1.5 cm) and stays after release
    grasp, lift, place, d = grasp_points()
    out = {}
    for n in names:
        rows = res['cells']['%s__grasp' % n.replace(' ', '_')]['rows']
        take = next(r for r in rows if r['contact'].get('handL') == 'prop')
        reach_err = np.linalg.norm(np.array(take['tips']['L']) - grasp) / PX_PER_CM
        last = rows[-1]['prop']
        place_err = np.linalg.norm(np.array(last) - (np.array(place) + (0, d))) / PX_PER_CM
        after = [r['prop'] for r in rows if r['event'] in ('return',)] + [rows[-1]['prop']]
        drift = max(np.linalg.norm(np.array(p) - last) for p in after) / PX_PER_CM
        neck = min(r['neck'] for r in rows)
        out[n] = {'reach_err_cm': round(float(reach_err), 2), 'place_err_cm': round(float(place_err), 2),
                  'prop_drift_after_release_cm': round(float(drift), 2), 'min_neck_cover': round(neck, 3),
                  'pass': reach_err < 1.5 and place_err < 1.5 and drift < 0.5}
    C['4_grasp_release'] = {'pass': all(v['pass'] for v in out.values()), 'actors': out,
                            'summary': '; '.join('%s reach %.1f cm, place %.1f cm' % (n, v['reach_err_cm'], v['place_err_cm'])
                                                 for n, v in out.items())}
    # 5 collide, fall, recover: the fall starts on the collision frame, nobody goes through the floor,
    #   everyone ends standing on the floor; plus each actor's solo fall/recover cell
    out = {}
    for tag, sc in res['scenes'].items():
        ok_start = sc['hit_frame'] is not None and all(f is not None and abs(f - sc['hit_frame']) <= 1 for f in sc['fall_start'])
        for n, rows in sc['tracks'].items():
            pen = max(r['low_px'] for r in rows) / PX_PER_CM
            end = rows[-1]
            standing = end['view'] in ('q3r', 'front') and abs(end['low_px']) < 1.5 and \
                (STAGE['floor'] - end['headtop']) > 0.85 * (STAGE['floor'] - rows[0]['headtop'])
            out['%s/%s' % (tag, n)] = {'max_below_floor_cm': round(pen, 2), 'ends_standing': bool(standing),
                                       'fall_on_hit': bool(ok_start), 'pass': pen < 0.5 and standing and ok_start}
    for n in names:
        rows = res['cells']['%s__fall' % n.replace(' ', '_')]['rows']
        pen = max(r['low_px'] for r in rows) / PX_PER_CM
        standing = abs(rows[-1]['low_px']) < 1.5 and (STAGE['floor'] - rows[-1]['headtop']) > 0.85 * (STAGE['floor'] - rows[0]['headtop'])
        out['solo/%s' % n] = {'max_below_floor_cm': round(pen, 2), 'ends_standing': bool(standing), 'pass': pen < 0.5 and standing}
    C['5_collide_fall_recover'] = {'pass': all(v['pass'] for v in out.values()), 'runs': out,
                                   'summary': '; '.join('%s %s' % (k, 'ok' if v['pass'] else 'FAIL') for k, v in out.items())}
    # 6 recasting keeps the choreography: in every cell the measured bone angles equal the clip's (< 1 deg),
    #   events land on the same frames for every actor, and both castings collide on the same frame
    worst, ev_ok, cons = 0., True, {}
    for cname in ('walk', 'turn', 'grasp', 'fall'):
        evs = []
        for n in names:
            rows = res['cells']['%s__%s' % (n.replace(' ', '_'), cname)]['rows']
            worst = max(worst, max(max(r['angle_err'].values()) for r in rows))
            evs.append([(r['event'], r['view']) for r in rows])
            cons.setdefault(cname, []).append([tuple(sorted(r['contact'])) for r in rows])
        ev_ok &= all(e == evs[0] for e in evs)
    # contacts may differ where an actor's own body changes which foot carries the weight (a hand-off)
    con_diff = {c: sum(1 for i in range(len(v[0])) if any(x[i] != v[0][i] for x in v)) for c, v in cons.items()}
    hits = [sc['hit_frame'] for sc in res['scenes'].values()]
    C['6_recast_invariance'] = {'pass': worst < 1.0 and ev_ok and len(set(hits)) == 1,
                                'max_angle_err_deg': round(worst, 3), 'events_identical': bool(ev_ok), 'scene_hit_frames': hits,
                                'frames_where_contacts_differ': con_diff,
                                'summary': 'max angle error %.3f deg; events identical %s; collision frames %s' % (worst, ev_ok, hits)}
    return C


if __name__ == '__main__':
    run()
