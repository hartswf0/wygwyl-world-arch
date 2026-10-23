# gate.py OUT NEW_DIR ids: painting | the last recognised render (blind test 3, or test 4 for daisy and phone-palm) | the new render
import sys, json, os, numpy as np
from PIL import Image, ImageDraw
out, newdir, ids = sys.argv[1], sys.argv[2], sys.argv[3].split(',')
R='/home/user/wygwyl-world-arch/shots/skinlab/production/recognition'; shots='/home/user/wygwyl-world-arch/shots'
k3=json.load(open(R+'/poet/blind3_key.json'))['files']; k4=json.load(open(R+'/poet/key.json'))['blind']
f3={v['id']:k for k,v in k3.items()}; f4={v['id']:k for k,v in k4.items()}
T4=('poet.07.main-poses/pluck-the-daisy','poet.09.main-poses/phone-palm')
H=330; tiles=[]
def fig(im, mode):
    a=np.asarray(im.convert('RGBA'))
    if mode=='alpha': m=a[...,3]>40
    else: bg=a[0,0,:3].astype(int); m=np.abs(a[...,:3].astype(int)-bg).sum(2)>30
    ys,xs=np.nonzero(m); im=im.crop((xs.min(),ys.min(),xs.max()+1,ys.max()+1)).convert('RGBA'); s=H/im.height
    im=im.resize((max(1,int(im.width*s)),H)); b=Image.new('RGBA',im.size,(232,224,210,255)); b.alpha_composite(im); return b.convert('RGB')
for i in ids:
    old = (R+'/poet/blind/'+f4[i], 'test 4 (recognised)') if i in T4 else (R+'/poet/blind3/'+f3[i], 'test 3 (recognised)')
    ims=[fig(Image.open(f'{shots}/kits/cut/{i}.webp'),'alpha'), fig(Image.open(old[0]),'bg'), fig(Image.open(f"{newdir}/{i.replace('/','__')}.png"),'alpha')]
    W=sum(x.width for x in ims)+40; C=Image.new('RGB',(W,H+24),(28,28,34)); d=ImageDraw.Draw(C); x=10
    for im,lab in zip(ims,['painting',old[1],'round 9']): C.paste(im,(x,0)); d.text((x+3,3),lab,fill=(20,20,20)); x+=im.width+10
    d.text((10,H+7),i,fill='white')
    if C.width>2400: C=C.resize((2400,int(C.height*2400/C.width)))
    tiles.append(C)
rows=[];row=[];w=0
for t in tiles:
    if w+t.width>2400: rows.append(row); row=[]; w=0
    row.append(t); w+=t.width
rows.append(row); S=Image.new('RGB',(2400,sum(max(t.height for t in rw) for rw in rows)),(20,20,24)); y=0
for rw in rows:
    x=0
    for t in rw: S.paste(t,(x,y)); x+=t.width
    y+=max(t.height for t in rw)
S.save(out,quality=85)
