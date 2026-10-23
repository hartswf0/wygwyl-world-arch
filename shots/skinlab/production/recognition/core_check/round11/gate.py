# gate.py OUT RENDERS_DIR ids: painting | last recognised render (test 6 = git 8505793 poet/blind; test 5 = 788a3d4 for falter-at-shoulder-contact-2) | round 11 (POSES=poses_v2 node recognize.mjs poet -> poet/renders)
import sys, json, os, numpy as np
from PIL import Image, ImageDraw
out, newdir, ids = sys.argv[1], sys.argv[2], sys.argv[3].split(',')
S='/tmp/claude-0/-home-user/f7ade34c-fa5f-538f-b092-e7629f2f6294/scratchpad'; shots='/home/user/wygwyl-world-arch/shots'
T3=('poet.09.main-poses/falter-at-shoulder-contact-2',)
H=330; tiles=[]
def fig(im):
    a=np.asarray(im.convert('RGBA')); m=a[...,3]>40
    if m.all() or not m.any(): bg=a[0,0,:3].astype(int); m=np.abs(a[...,:3].astype(int)-bg).sum(2)>30
    ys,xs=np.nonzero(m); im=im.crop((xs.min(),ys.min(),xs.max()+1,ys.max()+1)).convert('RGBA'); s=H/im.height
    im=im.resize((max(1,int(im.width*s)),H)); b=Image.new('RGBA',im.size,(232,224,210,255)); b.alpha_composite(im); return b.convert('RGB')
for i in ids:
    safe=i.replace('/','__'); old=(f'{S}/t5/{safe}.jpg','test 5') if i in T3 else (f'{S}/t6/{safe}.jpg','test 6')
    ims=[fig(Image.open(f'{shots}/kits/cut/{i}.webp')), fig(Image.open(old[0])), fig(Image.open(f'{newdir}/{safe}.png'))]
    W=sum(x.width for x in ims)+40; C=Image.new('RGB',(W,H+24),(28,28,34)); d=ImageDraw.Draw(C); x=10
    for im,lab in zip(ims,['painting',old[1],'round 11 (recognize.mjs)']): C.paste(im,(x,0)); d.text((x+3,3),lab,fill=(20,20,20)); x+=im.width+10
    d.text((10,H+7),i,fill='white')
    if C.width>2400: C=C.resize((2400,int(C.height*2400/C.width)))
    tiles.append(C)
rows=[];row=[];w=0
for t in tiles:
    if w+t.width>2400: rows.append(row); row=[]; w=0
    row.append(t); w+=t.width
rows.append(row); G=Image.new('RGB',(2400,sum(max(t.height for t in rw) for rw in rows)),(20,20,24)); y=0
for rw in rows:
    x=0
    for t in rw: G.paste(t,(x,y)); x+=t.width
    y+=max(t.height for t in rw)
G.save(out,quality=85)
