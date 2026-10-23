"""Painting briefs for every test pose that no other-family painting reaches, and for the move's
in-betweens where the cut between neighbouring paintings is a jump. Writes ../gaps.json and
stick-figure references in ../gaps/ (marker skeleton over a faded target, or a pose interpolated
between two paintings' markers when there is no target painting)."""
import sys, os, json, cv2, numpy as np
sys.path.insert(0, os.path.dirname(__file__)); import h2
H2 = os.path.join(h2.ROOT, 'shots/scion2/h2'); GD = os.path.join(H2, 'gaps'); os.makedirs(GD, exist_ok=True)
SEG = [('neck','head'),('neck','groin'),('shoulderL','shoulderR'),('hipL','hipR'),('shoulderL','elbowL'),('elbowL','wristL'),
       ('shoulderR','elbowR'),('elbowR','wristR'),('hipL','kneeL'),('kneeL','ankleL'),('hipR','kneeR'),('kneeR','ankleR'),
       ('ankleL','toeL'),('ankleR','toeR'),('chin','head')]

def ang(P, a, b):
    """screen angle of bone a->b in degrees: 0 = straight down, +90 = toward screen right, -90 = toward screen left, 180 = straight up"""
    v = P[b][:2] - P[a][:2]
    return int(round(np.degrees(np.arctan2(v[0], v[1]))))

def side(P, k):
    """which screen side a limb is on (by its shoulder/hip), for the brief's wording"""
    other = k.replace('L', '#').replace('R', 'L').replace('#', 'R')
    return 'screen-left' if P[k][0] < P[other][0] else 'screen-right'

def limb_angles(P):
    out = {}
    for lim, (a, b, c) in dict(armL=('shoulderL','elbowL','wristL'), armR=('shoulderR','elbowR','wristR'),
                               legL=('hipL','kneeL','ankleL'), legR=('hipR','kneeR','ankleR')).items():
        out[f"{lim} ({'his left' if lim.endswith('L') else 'his right'}, {side(P, a)})"] = dict(
            upper=ang(P, a, b), lower=ang(P, b, c), conf=round(float(min(P[a][2], P[b][2], P[c][2])), 2))
    out['torso (groin->neck)'] = dict(angle=ang(P, 'groin', 'neck'))
    out['head (neck->head)'] = dict(angle=ang(P, 'neck', 'head'))
    return out

def stick(P, canvas, col=(40, 40, 200), s=1.0, o=(0, 0)):
    for a, b in SEG:
        pa = (int(P[a][0]*s+o[0]), int(P[a][1]*s+o[1])); pb = (int(P[b][0]*s+o[0]), int(P[b][1]*s+o[1]))
        cv2.line(canvas, pa, pb, col, 3, cv2.LINE_AA)
    for k in h2.J:
        cv2.circle(canvas, (int(P[k][0]*s+o[0]), int(P[k][1]*s+o[1])), 4, (20, 20, 20), -1, cv2.LINE_AA)
    return canvas

def ref_from_target(tid, path):
    im = h2.img(tid); P = h2.pose(tid)
    base = h2.rgba_on(im).astype(np.float32); base = (base*0.35 + 255*0.65).astype(np.uint8)
    pad = 40; c = np.full((im.shape[0]+2*pad, im.shape[1]+2*pad, 3), 255, np.uint8); c[pad:-pad, pad:-pad] = base
    stick(P, c, o=(pad, pad)); cv2.imwrite(path, c)

def norm_pose(pid, ank_to=(0, 0), height=380.0):
    P = h2.pose(pid); ank = (P['ankleL'][:2]+P['ankleR'][:2])/2; s = height/(ank[1]-P['head'][1])
    return {k: np.array([(v[0]-ank[0])*s+ank_to[0], (v[1]-ank[1])*s+ank_to[1], v[2]]) for k, v in P.items()}

def ref_between(a, b, path, t=0.5):
    Pa, Pb = norm_pose(a, (250, 480)), norm_pose(b, (250, 480))
    P = {k: Pa[k]*(1-t)+Pb[k]*t for k in Pa}
    c = np.full((540, 500, 3), 255, np.uint8)
    stick(Pa, c, (200, 200, 200)); stick(Pb, c, (200, 200, 200)); stick(P, c, (40, 40, 200))
    h2.put_text(c, f"grey: {a.split('/')[1][:24]} / {b.split('/')[1][:24]}", (6, 16), 0.38)
    h2.put_text(c, "red: the missing drawing (markers interpolated)", (6, 32), 0.38)
    cv2.imwrite(path, c); return P

# what I saw comparing each pick with its painting at the same height (hand-written, see out/sheet.jpg)
SEEN = {
 "poet.13.main-poses/06-refocus": "Pick holds a book to his chest, glasses on. Target: hand at temple, sunglasses off and held at the waist. Same stance and boots.",
 "poet.12.main-poses/02": "Pick: arms up in an open V with open hands and a calm face. Target: fists, elbows bent, laughing.",
 "poet.07.main-poses/push-two-sides-apart": "Pick has arms open low with palms up. Target pushes both palms out at shoulder height, in a wider stance.",
 "poet.04.main-poses/04-6-rise-flex-reflect": "Close. The pick's arms are lower and the gaze is forward, not up. No chest disc.",
 "poet.09.main-poses/phone-palm": "Pick is frontal with a hand at the temple. Target is 3/4 turned to screen-left with a phone at the ear (and is itself a cut painting).",
 "poet.04.main-poses/04-4-empty-cuffs": "Pick is a 3/4 crouch reaching down with a letter. Target is a frontal squat with both forearms raised, empty cuffs, and the chest disc.",
 "poet.04.main-poses/04-2-heart-seated": "Pick kneels forward reaching with flowers. Target kneels upright on one knee, hands at his sides, gazing up to the right.",
 "poet.13.main-poses/part-2": "Pick sits on a stone block reading a book, in 3/4 view. Target is a profile drinking from a cup with no seat painted.",
 "poet.05.main-poses/q3-restless-lying-2": "There is no lying painting outside poet.05, so the pick is a crouch. It fails completely.",
 "poet.08.main-poses/03-gentle-slow-bent-knee-dance-alone": "Pick stands straight with palms up. Target has bent knees, fists at shoulder height and head down-right: a dance.",
 "poet.09.main-poses/falter-at-shoulder-contact": "Pick is a low, wide lunge with both arms spread. Target is a walking stride with one arm reaching forward and the other back.",
 "poet.08.main-poses/05-chest-lean-opened-back-head-inhale-back-and-p": "Close: same arms and stance. The chin is up, but the head is not thrown back as far.",
}

def main():
    picks = json.load(open(os.path.join(H2, 'out/picks.json')))
    briefs = []
    for p in h2.TEST['poses']:
        tid = p['id']; r = picks[tid]; tg = h2.tag(tid); P = h2.pose(tid)
        if r['status'] == 'covered': continue
        ref = os.path.join(GD, tid.replace('/', '__') + '_ref.png'); ref_from_target(tid, ref)
        briefs.append(dict(
            id='test:' + tid, need=p['kind'], status=r['status'], nearest=r['pick'], nearest_D=r['D'],
            what_the_nearest_gets_wrong=SEEN[tid],
            brief=dict(view=tg['view'], posture=tg['cls'], hands=tg['hands'], gaze=tg['gaze'], props=tg['props'],
                       costume='red/black tracksuit with sunglasses' + (' and the poet.04 chest disc' if tg['costume'] == 'track-disc' else ''),
                       limb_angles_deg=limb_angles(P),
                       angle_convention='screen angle of each bone: 0 = straight down, +90 = toward screen right, -90 = toward screen left, 180 = straight up',
                       note=tg['note']),
            reference=dict(painting='shots/kits/cut/' + tid + '.webp', stick_figure=os.path.relpath(ref, h2.ROOT))))
    # the move's in-betweens: the two cuts that jump (pose distance ~0.5 between neighbours)
    mv = [('poet.05.main-poses/ask-the-universe-2', 'poet.11.main-poses/welcome-new-day',
           'move in-between (out): arms rising through shoulder height', 'front', 'palms up, opening', 'up',
           'Between the dip (arms low, palms up) and the open V. The cut skips the arms passing through horizontal. Stance about 1.1 torso lengths.'),
          ('poet.11.main-poses/welcome-new-day', 'poet.11.main-poses/02-front-guide-stone',
           'move in-between (back): arms falling through shoulder height', 'front', 'hands open, palms turning down', 'fwd',
           'The release after the fists. The arms come down from the V to the low palms-forward pose and the stance narrows.'),
          ('poet.11.main-poses/welcome-new-day', 'poet.12.main-poses/02',
           'move in-between: hands closing to fists at the top', 'front', 'half-closed fists', 'up',
           'Not a pose jump but a style jump: 12/02 has a thicker tan outline and a bigger painted head than poet.11. A fists-up drawn in the poet.11 hand, or an open-V drawn in the poet.12 hand, would remove the pop at the hit.')]
    for a, b, need, view, hands, gaze, why in mv:
        ref = os.path.join(GD, 'move__' + a.split('/')[1][:14] + '__' + b.split('/')[1][:14] + '_ref.png')
        P = ref_between(a, b, ref)
        D = h2.score(a, b, False)['terms']['pose']
        briefs.append(dict(id='move:' + a + ' > ' + b, need=need, status='gap', nearest=None, nearest_D=round(D, 3),
                           what_the_nearest_gets_wrong=why,
                           brief=dict(view=view, posture='stand', hands=hands, gaze=gaze, props=[],
                                      costume='red/black tracksuit with sunglasses', limb_angles_deg=limb_angles(P),
                                      angle_convention='screen angle of each bone: 0 = straight down, +90 = toward screen right, -90 = toward screen left, 180 = straight up'),
                           reference=dict(between=[a, b], stick_figure=os.path.relpath(ref, h2.ROOT))))
    # coverage holes not in the test (from coverage.md): no suited back view anywhere in main-poses
    briefs.append(dict(id='coverage:back-view', need='poet seen from behind, walking away (suit)', status='gap', nearest=None, nearest_D=None,
                       what_the_nearest_gets_wrong='None of the 130 main-poses paintings shows the suited poet from behind. Every back view is the ex in an olive bomber, plus one t-shirt back in poet.03. poet.14.exit has suited rear figures (1-stand, 3-walk-reach-to), but they are outside the 130 and unscored here.',
                       brief=dict(view='back', posture='walk', hands='sides', gaze='fwd (head seen from behind)', props=[], costume='red/black tracksuit'),
                       reference=dict(painting='shots/kits/cut/poet.03.main-poses/two-backs-out-of-step-1.webp (t-shirt back, for pose only)')))
    order = {'gap': 0, 'approximate': 1}
    briefs.sort(key=lambda b: (order.get(b['status'], 2), -(b['nearest_D'] if b['nearest_D'] is not None else 9)))
    top = ['test:poet.13.main-poses/part-2', 'test:poet.04.main-poses/04-4-empty-cuffs', 'test:poet.04.main-poses/04-2-heart-seated',
           'move:poet.05.main-poses/ask-the-universe-2 > poet.11.main-poses/welcome-new-day', 'coverage:back-view']
    for b in briefs: b['priority'] = top.index(b['id']) + 1 if b['id'] in top else None
    json.dump(dict(about='H2 painting briefs: the poses replacement cannot reach from other families. Each one is a painting for the person to make. '
                         'priority 1-5 is my ordering: what the poems most likely need, times how far the nearest painting is.',
                   briefs=briefs), open(os.path.join(H2, 'gaps.json'), 'w'), indent=1)
    for b in briefs: print(b['priority'], b['status'], b['id'], b['nearest_D'])

if __name__ == '__main__':
    main()
