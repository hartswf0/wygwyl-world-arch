"""H2 replacement animation: library.
A painting is never deformed: it is placed with uniform scale + translation (+ optional mirror).
Selection = a view-aware pose distance between the target's markers and each candidate's markers,
plus silhouette overlap, the hand-read view/hands/gaze/props tags, and costume continuity.
"""
import json, os, sys, glob
import numpy as np, cv2
sys.path.insert(0, os.path.dirname(__file__))
from catalog_src import C

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '../../../..'))
CUT = os.path.join(ROOT, 'shots/kits/cut')
MARK = json.load(open(os.path.join(ROOT, 'shots/rig/poses_v2/poet__red_black_sunglasses.json')))
MK = {t['id']: t['markers'] for t in MARK['targets']}
TEST = json.load(open(os.path.join(ROOT, 'shots/scion2/test_set.json')))

J = ['head','chin','neck','shoulderL','shoulderR','elbowL','elbowR','wristL','wristR','groin',
     'hipL','hipR','kneeL','kneeR','ankleL','ankleR','toeL','toeR']
JW = dict(head=1.6, chin=0.8, neck=1.0, shoulderL=1.0, shoulderR=1.0, elbowL=1.6, elbowR=1.6,
          wristL=2.4, wristR=2.4, groin=1.0, hipL=0.8, hipR=0.8, kneeL=1.3, kneeR=1.3,
          ankleL=1.5, ankleR=1.5, toeL=0.8, toeR=0.8)
SWAP_ARMS = {'shoulderL':'shoulderR','shoulderR':'shoulderL','elbowL':'elbowR','elbowR':'elbowL','wristL':'wristR','wristR':'wristL'}
SWAP_LEGS = {'hipL':'hipR','hipR':'hipL','kneeL':'kneeR','kneeR':'kneeL','ankleL':'ankleR','ankleR':'ankleL','toeL':'toeR','toeR':'toeL'}
BONES = [('neck','groin',1.0),('hipL','kneeL',.9),('hipR','kneeR',.9),('kneeL','ankleL',.77),('kneeR','ankleR',.77),
         ('shoulderL','elbowL',.58),('shoulderR','elbowR',.58),('shoulderL','shoulderR',.82)]

_img = {}
def img(pid):
    if pid not in _img:
        _img[pid] = cv2.imread(os.path.join(CUT, pid + '.webp'), cv2.IMREAD_UNCHANGED)
    return _img[pid]

def family(pid): return pid.split('/')[0]

def tag(pid):
    c = C[pid]
    return dict(costume=c[0], use=c[1], view=c[2], cls=c[3], props=c[4], hands=c[5], gaze=c[6], note=c[7])

def pose(pid, mirror=False):
    """markers -> dict name -> (x, y, conf) in painting px; mirrored about the image width."""
    m = MK[pid]; w = img(pid).shape[1]
    out = {}
    for k in J:
        x, y, _d, _s, c = m[k]
        if mirror: x = w - 1 - x
        out[k] = np.array([x, y, max(c, 0.05)])
    if mirror:  # anatomical labels follow the flip
        out = {(SWAP_ARMS.get(k) or SWAP_LEGS.get(k) or k): v for k, v in out.items()}
    return out

def unit(P):
    """body unit (~ neck-to-groin length of an unforeshortened torso), robust to foreshortening."""
    r = [np.hypot(*(P[a][:2]-P[b][:2]))/L for a, b, L in BONES]
    # foreshortening only shortens a bone on screen, so the longer estimates are the trustworthy ones;
    # the 2nd-longest guards against one mislabelled marker
    return float(sorted(r)[-2])

VIEW_FACE = {'front':(0,1),'3qR':(1,1),'3qL':(-1,1),'profR':(2,1),'profL':(-2,1),'back':(0,-1),'back3qR':(1,-1),'back3qL':(-1,-1)}
def mirror_view(v):
    return v.replace('R','#').replace('L','R').replace('#','L') if v else v

def view_pen(vt, vs):
    if vt == vs: return 0.0
    a, b = VIEW_FACE[vt], VIEW_FACE[vs]
    p = 0.12*abs(a[0]-b[0])
    if a[0]*b[0] < 0: p += 0.25          # turned the other way
    if a[1] != b[1]: p += 0.6            # front vs back
    return p

def fit(Pt, Ps, ratio):
    """uniform scale k*ratio + translation, weighted LS, k clamped to [0.9, 1.1]."""
    A = np.array([Ps[k][:2] for k in J]); B = np.array([Pt[k][:2] for k in J])
    w = np.array([JW[k]*np.sqrt(Pt[k][2]*Ps[k][2]) for k in J])
    ma = (w[:,None]*A).sum(0)/w.sum(); mb = (w[:,None]*B).sum(0)/w.sum()
    a0, b0 = A-ma, B-mb
    s = (w*(a0*b0).sum(1)).sum()/max((w*(a0*a0).sum(1)).sum(), 1e-9)
    s = float(np.clip(s, 0.9*ratio, 1.1*ratio))
    t = mb - s*ma
    err = np.sqrt((w*((s*A+t-B)**2).sum(1)).sum()/w.sum())
    return s, t, err, w

DIRB = [('neck','head',1.0),('groin','neck',1.0),('shoulderL','elbowL',1.0),('shoulderR','elbowR',1.0),
        ('elbowL','wristL',1.2),('elbowR','wristR',1.2),('hipL','kneeL',1.0),('hipR','kneeR',1.0),('kneeL','ankleL',0.8),('kneeR','ankleR',0.8)]
def dir_dist(Pt, Ps):
    """mean screen-angle difference of the limb bones, in units of pi, confidence weighted"""
    num = den = 0.0
    for a, b, wb in DIRB:
        va = Pt[b][:2]-Pt[a][:2]; vb = Ps[b][:2]-Ps[a][:2]
        d = abs(np.angle(complex(*va)/complex(*vb))) / np.pi if np.hypot(*vb) > 1e-6 and np.hypot(*va) > 1e-6 else 0.5
        w = wb*min(Pt[a][2], Pt[b][2], Ps[a][2], Ps[b][2])**0.5
        num += w*d; den += w
    return num/max(den, 1e-9)

def pose_dist(Pt, Ps):
    ut, us = unit(Pt), unit(Ps)
    best = None
    for sa in (0, 1):
        for sl in (0, 1):
            Q = {}
            for k in J:
                kk = k
                if sa: kk = SWAP_ARMS.get(kk, kk)
                if sl: kk = SWAP_LEGS.get(kk, kk)
                Q[k] = Ps[kk]
            s, t, err, w = fit(Pt, Q, ut/us)
            e = err/ut + 0.5*dir_dist(Pt, Q) + 0.04*(sa+sl)
            if best is None or e < best[0]:
                best = (e, s, t, (sa, sl))
    return best

def place(pid, s, t, mirror, shape):
    """RGBA of painting pid under x' = s*x + t (after optional mirror), on canvas shape (h, w)."""
    im = img(pid)
    if mirror: im = im[:, ::-1]
    M = np.array([[s, 0, t[0]], [0, s, t[1]]], np.float32)
    return cv2.warpAffine(im, M, (shape[1], shape[0]), flags=cv2.INTER_AREA if s < 1 else cv2.INTER_CUBIC,
                          borderMode=cv2.BORDER_CONSTANT, borderValue=(0,0,0,0))

def sil_iou(tid, sid, s, t, mirror):
    ti = img(tid); h, w = ti.shape[:2]; pad = int(0.6*max(h, w))
    T = np.zeros((h+2*pad, w+2*pad), bool); T[pad:pad+h, pad:pad+w] = ti[:,:,3] > 128
    S = place(sid, s, t+pad, mirror, T.shape)[:,:,3] > 128
    return (T & S).sum()/max((T | S).sum(), 1)

HANDS_NEAR = {('palms-up','open-up'):.5, ('palms-up','palms-out'):.5, ('palms-out','reach'):.5, ('palms-up','reach'):.6,
              ('fists','open-up'):.6, ('pockets','sides'):.6, ('chest','holding'):.5, ('mixed','holding'):.6, ('mixed','chest'):.6,
              ('mixed','reach'):.7, ('sides','mixed'):.7}
def hands_pen(a, b):
    if a == b: return 0.0
    return 0.15*HANDS_NEAR.get((a,b), HANDS_NEAR.get((b,a), 1.0))

def gaze_pen(a, b):
    if a == b: return 0.0
    near = {frozenset(['up','back']):.5, frozenset(['fwd','side']):.4, frozenset(['down','side']):.7}
    return 0.12*near.get(frozenset([a,b]), 1.0)

GROUP = dict(stand='up', walk='up', lunge='up', dance='up', lean='up', crouch='low', kneel='low', sit='sit', lie='lie', fall='fall', ride='ride')
def cls_pen(a, b):
    if a == b: return 0.0
    return 0.1 if GROUP.get(a) == GROUP.get(b) else 0.8

def candidates(target_id):
    fam = family(target_id)
    for pid, c in C.items():
        if c[1] != 'ok' or c[0] not in ('track','track-disc') or pid not in MK: continue
        if family(pid) == fam: continue
        yield pid

def score(target_id, sid, mirror, Pt=None, tt=None):
    Pt = Pt if Pt is not None else pose(target_id)
    tt = tt or tag(target_id); ts = tag(sid)
    Ps = pose(sid, mirror)
    e, s, t, sw = pose_dist(Pt, Ps)
    vs = mirror_view(ts['view']) if mirror else ts['view']
    iou = sil_iou(target_id, sid, s, t, mirror) if target_id in C else None
    terms = dict(pose=e, view=view_pen(tt['view'], vs), hands=hands_pen(tt['hands'], ts['hands']),
                 gaze=gaze_pen(tt['gaze'], ts['gaze']),
                 props=0.15*len([p for p in ts['props'] if p not in tt['props']]),
                 cls=cls_pen(tt['cls'], ts['cls']),
                 mirror=0.04 if mirror else 0.0,
                 costume=0.0 if tt['costume'] == ts['costume'] else 0.03)
    if iou is not None: terms['sil'] = 0.6*(1-iou)
    D = sum(terms.values())
    return dict(src=sid, mirror=mirror, D=float(D), terms={k: round(float(v),3) for k, v in terms.items()},
                iou=None if iou is None else round(float(iou),3), s=float(s), t=[float(t[0]), float(t[1])], swap=sw, view=vs)

def rank(target_id, n=8):
    Pt = pose(target_id); tt = tag(target_id)
    res = [score(target_id, sid, m, Pt, tt) for sid in candidates(target_id) for m in (False, True)]
    res.sort(key=lambda r: r['D'])
    return res[:n]

def rgba_on(rgba, bg=235):
    a = rgba[:,:,3:4]/255.0
    return (rgba[:,:,:3]*a + bg*(1-a)).astype(np.uint8)

def crop_alpha(rgba, pad=4):
    ys, xs = np.where(rgba[:,:,3] > 8)
    y0, y1 = max(ys.min()-pad, 0), min(ys.max()+pad+1, rgba.shape[0])
    x0, x1 = max(xs.min()-pad, 0), min(xs.max()+pad+1, rgba.shape[1])
    return rgba[y0:y1, x0:x1], (x0, y0)

def render_pick(target_id, r):
    """the reproduction at the target painting's scale: canvas = target painting frame, grown to fit."""
    ti = img(target_id); h, w = ti.shape[:2]; pad = int(0.8*max(h, w))
    full = place(r['src'], r['s'], np.array(r['t'])+pad, r['mirror'], (h+2*pad, w+2*pad))
    fig, (x0, y0) = crop_alpha(full)
    return fig, (x0-pad, y0-pad)

def put_text(im, s, org, scale=0.5, col=(30,30,30), th=1):
    cv2.putText(im, s, org, cv2.FONT_HERSHEY_SIMPLEX, scale, (255,255,255), th+2, cv2.LINE_AA)
    cv2.putText(im, s, org, cv2.FONT_HERSHEY_SIMPLEX, scale, col, th, cv2.LINE_AA)

def pair_panel(target_id, fig, off, label, H=520, bg=235):
    """painting | reproduction, same pixel scale (so the same man is the same height), feet on one line."""
    T = img(target_id)
    # common frame in target coordinates
    x0 = min(0, off[0]); y0 = min(0, off[1])
    x1 = max(T.shape[1], off[0]+fig.shape[1]); y1 = max(T.shape[0], off[1]+fig.shape[0])
    def on(rgba, ox, oy):
        c = np.zeros((y1-y0, x1-x0, 4), np.uint8); c[oy-y0:oy-y0+rgba.shape[0], ox-x0:ox-x0+rgba.shape[1]] = rgba
        return c
    A = on(T, 0, 0); B = on(fig, off[0], off[1])
    sc = (H-40)/A.shape[0]
    A = cv2.resize(rgba_on(A, bg), None, fx=sc, fy=sc, interpolation=cv2.INTER_AREA)
    B = cv2.resize(rgba_on(B, bg), None, fx=sc, fy=sc, interpolation=cv2.INTER_AREA)
    sep = np.full((A.shape[0], 6, 3), 255, np.uint8)
    row = np.hstack([A, sep, B])
    out = np.full((H, row.shape[1], 3), 255, np.uint8); out[:row.shape[0]] = row
    for i, l in enumerate(label):
        put_text(out, l, (4, H-26+14*i), 0.4)
    return out
