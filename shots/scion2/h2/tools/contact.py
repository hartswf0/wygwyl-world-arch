import cv2, glob, numpy as np, sys, os
fs=sorted(glob.glob('shots/kits/cut/poet.*.main-poses/*.webp'))
H=260; W=200; cols=8
def tile(f,i):
    im=cv2.imread(f,cv2.IMREAD_UNCHANGED)
    a=im[:,:,3:4]/255.; rgb=im[:,:,:3]*a+235*(1-a)
    s=min((H-30)/im.shape[0],(W-6)/im.shape[1])
    r=cv2.resize(rgb.astype(np.uint8),(max(1,int(im.shape[1]*s)),max(1,int(im.shape[0]*s))),interpolation=cv2.INTER_AREA)
    t=np.full((H,W,3),235,np.uint8); y0=H-30-r.shape[0]; x0=(W-r.shape[1])//2
    t[y0:y0+r.shape[0],x0:x0+r.shape[1]]=r
    n=f.split('cut/poet.')[1].replace('.main-poses/','/').replace('.webp','')
    cv2.putText(t,f'{i}:{n[:26]}',(2,H-16),cv2.FONT_HERSHEY_SIMPLEX,0.33,(0,0,0),1)
    cv2.putText(t,f'{im.shape[1]}x{im.shape[0]}',(2,H-4),cv2.FONT_HERSHEY_SIMPLEX,0.33,(80,80,80),1)
    return t
ts=[tile(f,i) for i,f in enumerate(fs)]
out=sys.argv[1]
per=40
for p in range(0,len(ts),per):
    chunk=ts[p:p+per]
    while len(chunk)%cols: chunk.append(np.full((H,W,3),255,np.uint8))
    rows=[np.hstack(chunk[i:i+cols]) for i in range(0,len(chunk),cols)]
    cv2.imwrite(f'{out}_{p//per}.jpg',np.vstack(rows),[cv2.IMWRITE_JPEG_QUALITY,85])
