#!/usr/bin/env python3
"""
BUTCHER — SAM for the silhouette, the skeleton for the cuts.

    python3 shots/arena/butcher.py bodies/ACT-010_p2.png --act ACT-010

The four-box decompile shares 35-110% of each card with its neighbours, which is
the duplicate limb on screen. Better segmentation alone does not fix that:
SAM will happily hand you "a leg" as one mask and the thigh and the shin are
still fused inside it. What separates them is not vision, it is the skeleton —
the knee is a known point and the cut is the plane through it.

So both, each doing the half it can:

  SAM              where the figure ENDS: one clean person mask, no background,
                   no neighbour's limb
  the skeleton     where the figure DIVIDES: each piece is the mask inside a
                   capsule drawn between two joints, so a thigh stops at the
                   knee because the knee is a coordinate, not a guess

WHICH FRAME IS THIS A DRAWING OF. The study panels caption their frame but the
filename does not carry it, so it is recovered rather than read: every frame of
the vignette is rasterised as a thick stick figure, normalised to the same box
as the drawing, and scored by IoU. The frame whose skeleton best fills the
drawn silhouette is the frame it was drawn from. That is the registration, and
it is checkable — a bad match shows up as a low score instead of a bad cut.
"""
import os, sys, json, math, glob
import numpy as np, cv2

HERE = os.path.dirname(os.path.abspath(__file__))
BANK = os.path.join(HERE, 'bolas', 'bank')
DEG = math.pi / 180.0
BONES = [('pelvis','spineMid'),('spineMid','chest'),('chest','neckBase'),('neckBase','headBase'),
         ('headBase','headTop'),('chest','shoulderL'),('chest','shoulderR'),
         ('shoulderL','elbowL'),('elbowL','wristL'),('shoulderR','elbowR'),('elbowR','wristR'),
         ('pelvis','hipL'),('pelvis','hipR'),('hipL','kneeL'),('kneeL','ankleL'),
         ('hipR','kneeR'),('kneeR','ankleR'),('ankleL','ballL'),('ankleR','ballR')]
# the pieces we cut, as (name, jointA, jointB, radius in bone-lengths)
CUTS = [('head','headBase','headTop',0.85),('torso','pelvis','neckBase',0.62),
        ('uarmL','shoulderL','elbowL',0.40),('farmL','elbowL','wristL',0.36),
        ('uarmR','shoulderR','elbowR',0.40),('farmR','elbowR','wristR',0.36),
        ('thighL','hipL','kneeL',0.40),('shinL','kneeL','ankleL',0.34),
        ('thighR','hipR','kneeR',0.40),('shinR','kneeR','ankleR',0.34),
        ('bootL','ankleL','ballL',1.10),('bootR','ankleR','ballR',1.10)]

def projector(view, W=1920, H=1080):
    yaw, elev = view.get('yaw', -22)*DEG, view.get('elev', 10)*DEG
    cy, sy, ce, se = math.cos(yaw), math.sin(yaw), math.cos(elev), math.sin(elev)
    c = [view.get('x',0), view.get('y',90), view.get('z',0)]
    s = H*0.86/230*view.get('zoom',1.0)
    def P(p):
        x,y,z = p[0]-c[0], p[1]-c[1], p[2]-c[2]
        x1,z1 = x*cy - z*sy, x*sy + z*cy
        y2,_  = y*ce - z1*se, y*se + z1*ce
        return (W/2 + x1*s, H*0.52 - y2*s)
    return P

def stick(pts, size=160, thick=9):
    xs=[p[0] for p in pts.values()]; ys=[p[1] for p in pts.values()]
    w=max(xs)-min(xs) or 1; h=max(ys)-min(ys) or 1
    k=(size*0.88)/max(w,h); ox,oy=min(xs),min(ys)
    im=np.zeros((size,size),np.uint8)
    T=lambda p:(int((p[0]-ox)*k+size*0.06),int((p[1]-oy)*k+size*0.06))
    for a,b in BONES:
        if a in pts and b in pts: cv2.line(im,T(pts[a]),T(pts[b]),255,thick,cv2.LINE_AA)
    return im>80

def silhouette(mask, size=160):
    ys,xs=np.nonzero(mask)
    m=mask[ys.min():ys.max()+1, xs.min():xs.max()+1].astype(np.uint8)
    h,w=m.shape; k=(size*0.88)/max(h,w)
    m=cv2.resize(m,(max(1,int(w*k)),max(1,int(h*k))),interpolation=cv2.INTER_AREA)
    out=np.zeros((size,size),np.uint8)
    out[int(size*0.06):int(size*0.06)+m.shape[0], int(size*0.06):int(size*0.06)+m.shape[1]]=m
    return out>0

def find_frame(V, mask):
    """which frame of this vignette is the drawing a drawing of?"""
    idx={n:i for i,n in enumerate(V['joints'])}
    P=projector(V['view'] or {})
    target=silhouette(mask)
    best=(-1,-1,None)
    for f,fr in enumerate(V['frames']):
        for aid,a in fr['a'].items():
            pts={n:P(a['j'][i]) for n,i in idx.items()}
            s=stick(pts)
            iou=float((s&target).sum())/float((s|target).sum() or 1)
            if iou>best[0]: best=(iou,f,aid)
    return best

def fit(pts, mask):
    """put the skeleton onto the drawing: uniform scale + offset, bbox to bbox"""
    ys,xs=np.nonzero(mask)
    jx=[p[0] for p in pts.values()]; jy=[p[1] for p in pts.values()]
    sw=(max(jx)-min(jx)) or 1; sh=(max(jy)-min(jy)) or 1
    mw=int(np.ptp(xs))+1; mh=int(np.ptp(ys))+1   # numpy 2
    k=min(mw/sw, mh/sh)
    cx0,cy0=(min(jx)+max(jx))/2,(min(jy)+max(jy))/2
    cx1,cy1=(xs.min()+xs.max())/2,(ys.min()+ys.max())/2
    return {n:((p[0]-cx0)*k+cx1, (p[1]-cy0)*k+cy1) for n,p in pts.items()}, k

def nearest_bone(shape, mask, segs):
    """Every pixel of the figure belongs to exactly one piece: the bone it is
       closest to. Capsules drawn per bone overlapped 92% — a thigh capsule wide
       enough to hold a thigh also holds most of the torso. A partition cannot
       overlap, because a pixel has one nearest bone, and the seam between two
       pieces lands on the perpendicular through the joint, which is where a
       brad goes."""
    ys, xs = np.nonzero(mask)
    P = np.stack([xs, ys], 1).astype(np.float32)
    best = np.full(len(P), 1e18, np.float32)
    who = np.full(len(P), -1, np.int32)
    for i, (nm, a, b) in enumerate(segs):
        A = np.array(a, np.float32); B = np.array(b, np.float32)
        d = B - A; L2 = float(d @ d) or 1.0
        t = np.clip(((P - A) @ d) / L2, 0.0, 1.0)[:, None]
        dist = np.linalg.norm(P - (A + t * d), axis=1)
        better = dist < best
        best[better] = dist[better]; who[better] = i
    out = {}
    for i, (nm, a, b) in enumerate(segs):
        m = np.zeros(shape, bool)
        sel = who == i
        if sel.sum() < 150: continue
        m[ys[sel], xs[sel]] = True
        # drop stray islands: a piece is one piece
        n, lab, st, _ = cv2.connectedComponentsWithStats(m.astype(np.uint8))
        if n > 1:
            k = max(range(1, n), key=lambda j: st[j, 4])
            m = (lab == k)
        out[nm] = m
    return out


def capsule(shape, a, b, r):
    m=np.zeros(shape,np.uint8)
    a=np.array(a,float); b=np.array(b,float); d=b-a
    L=np.linalg.norm(d) or 1.0
    n=np.array([-d[1],d[0]])/L
    poly=np.array([a+n*r, b+n*r, b-n*r, a-n*r],np.int32)
    cv2.fillPoly(m,[poly],1)
    cv2.circle(m,tuple(map(int,a)),int(r),1,-1); cv2.circle(m,tuple(map(int,b)),int(r),1,-1)
    return m.astype(bool)

def sam_person(path):
    """SAM says where the figure ends; the alpha already does here, but SAM also
       removes the ground shadow and any caption the lift left behind"""
    im=cv2.imread(path, cv2.IMREAD_UNCHANGED)
    if im.ndim==3 and im.shape[2]==4:
        a=im[:,:,3]>24
    else:
        a=np.ones(im.shape[:2],bool)
    try:
        import torch
        from transformers import Sam3Model, Sam3Processor
        from PIL import Image
        m=Sam3Model.from_pretrained('facebook/sam3').eval()
        p=Sam3Processor.from_pretrained('facebook/sam3')
        dev='mps' if torch.backends.mps.is_available() else 'cpu'; m=m.to(dev)
        rgb=cv2.cvtColor(im[:,:,:3],cv2.COLOR_BGR2RGB)
        pil=Image.fromarray(rgb)
        inp=p(images=pil,text='a person',return_tensors='pt').to(dev)
        with torch.no_grad(): out=m(**inp)
        r=p.post_process_instance_segmentation(out,threshold=0.4,mask_threshold=0.5,
              target_sizes=[(pil.size[1],pil.size[0])])[0]
        ms=r['masks'].cpu().numpy() if hasattr(r['masks'],'cpu') else np.asarray(r['masks'])
        if len(ms):
            best=max(ms,key=lambda x:np.asarray(x).sum())
            return im, (np.asarray(best).astype(bool) & a), 'sam'
    except Exception as e:
        print(f'   (SAM unavailable: {type(e).__name__}) falling back to the alpha')
    return im, a, 'alpha'

def main():
    src=sys.argv[1]
    act=None
    for i,x in enumerate(sys.argv):
        if x=='--act' and i+1<len(sys.argv): act=sys.argv[i+1]
    if act is None:
        import re; m=re.match(r'(ACT-\d{3})', os.path.basename(src)); act=m.group(1) if m else None
    tid=None
    for f in sorted(glob.glob(os.path.join(BANK,'T1*.json'))):
        d=json.load(open(f))
        if act and act in (d.get('after') or ''): tid=d['id']; V=d; break
    if tid is None: raise SystemExit(f'no vignette for {act}')
    im, mask, how = sam_person(src)
    print(f'{os.path.basename(src)}  mask from {how}  {mask.sum():,} px')
    iou,f,aid = find_frame(V, mask)
    print(f'best match: {tid} frame {f} actor {aid}  (silhouette IoU {iou:.3f})')
    idx={n:i for i,n in enumerate(V['joints'])}
    P=projector(V['view'] or {})
    pts={n:P(V['frames'][f]['a'][aid]['j'][i]) for n,i in idx.items()}
    pts,k=fit(pts,mask)
    inside=sum(1 for p in pts.values() if 0<=int(p[1])<mask.shape[0] and 0<=int(p[0])<mask.shape[1]
               and mask[int(p[1]),int(p[0])])
    print(f'{inside} of {len(pts)} joints land inside the figure')
    out=os.path.join(HERE,'cut',os.path.splitext(os.path.basename(src))[0])
    os.makedirs(out,exist_ok=True)
    man={'source':os.path.basename(src),'vignette':tid,'frame':f,'actor':aid,
         'silhouette_iou':round(iou,3),'joints_inside':f'{inside}/{len(pts)}','pieces':[]}
    segs=[(nm,pts[ja],pts[jb]) for nm,ja,jb,_ in CUTS
          if ja in pts and jb in pts and math.dist(pts[ja],pts[jb])>=6]
    parts=nearest_bone(mask.shape, mask, segs)
    for nm,ja,jb,_ in CUTS:
        if nm not in parts: continue
        piece=parts[nm]; a,b=pts[ja],pts[jb]
        ys,xs=np.nonzero(piece)
        rgba=np.dstack([im[:,:,:3], (piece*255).astype(np.uint8)])[ys.min():ys.max()+1, xs.min():xs.max()+1]
        cv2.imwrite(os.path.join(out,nm+'.png'),rgba)
        man['pieces'].append(dict(id=nm,bone=[ja,jb],
            pivot=[round(a[0]-xs.min(),1),round(a[1]-ys.min(),1)],
            socket=[round(b[0]-xs.min(),1),round(b[1]-ys.min(),1)],
            px=[int(rgba.shape[1]),int(rgba.shape[0])],area=int(piece.sum())))
    # a partition cannot overlap; measure it anyway rather than assert it
    tot=sum(int(m.sum()) for m in parts.values()); sh=0
    for nm,mk in parts.items():
        other=np.zeros_like(mk)
        for o,mo in parts.items():
            if o!=nm: other|=mo
        sh+=int((mk&other).sum())
    man['overlap_pct']=round(100.0*sh/max(1,tot),1)
    man['covered_pct']=round(100.0*tot/max(1,int(mask.sum())),1)
    json.dump(man,open(os.path.join(out,'manifest.json'),'w'),indent=1)
    print(f'{len(man["pieces"])} pieces -> {os.path.relpath(out,os.getcwd())}')
    print(f'overlap between pieces: {man["overlap_pct"]}%   (the four-box decompile: 35-110%)')
    print(f'of the figure, {man["covered_pct"]}% ended up in a piece')

if __name__=='__main__':
    main()
