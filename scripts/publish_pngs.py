from pathlib import Path
import json,re
from PIL import Image,ImageDraw,ImageFont
import fitz
R=Path(__file__).resolve().parents[1]; A=R/'assets'; C=R/'uploads.json'; W,H=1600,2250
fontroot='/usr/share/fonts/truetype/dejavu/'
def F(n,b=False):return ImageFont.truetype(fontroot+('DejaVuSans-Bold.ttf' if b else 'DejaVuSans.ttf'),n)
def readmd(p):
 s=p.read_text();header,body=s.split('---\n',2)[1:]; meta={}
 for line in header.splitlines():
  if ':' in line:
   a,b=line.split(':',1);meta[a.strip()]=b.strip()
 chunks=[];head='INTRODUCTION';lines=[]
 for line in body.splitlines():
  if line.startswith('## '):
   if lines:chunks.append((head,lines))
   head=line[3:];lines=[]
  elif line.strip():lines.append(line.strip().replace('**',''))
 if lines:chunks.append((head,lines))
 return meta,chunks
def wrap(d,t,f,width):
 out=[];s=''
 for w in t.split():
  test=(s+' '+w).strip()
  if d.textbbox((0,0),test,font=f)[2]<=width:s=test
  else:
   if s:out.append(s)
   s=w
 if s:out.append(s)
 return out or ['']
def render(title,sub,sections,base):
 A.mkdir(exist_ok=True)
 images=[];idx=0;col=0;x=72;y=255;im=None;d=None
 def start():
  nonlocal idx,col,x,y,im,d
  idx+=1;col=0;x=72;y=255
  im=Image.new('RGB',(W,H),'white');d=ImageDraw.Draw(im)
  d.rectangle((0,0,W,204),fill='#102c43');d.rectangle((0,197,W,205),fill='#18a0aa')
  d.text((72,25),'RESUS BINDER   /   RESIDENT TEACHING',font=F(23,True),fill='#97e8e8')
  for n,line in enumerate(wrap(d,title,F(47,True),1455)[:2]):
   d.text((72,71+53*n),line,font=F(47,True),fill='white')
  d.text((72,215),sub[:105],font=F(22),fill='#627788')
 def save():
  path=base+'-'+str(idx).zfill(2)+'.png'
  d.line((72,H-110,W-72,H-110),fill='#c4d3df',width=2)
  d.text((72,H-90),'CLINICAL EVIDENCE  |  INTERPRET IN PATIENT CONTEXT',font=F(19),fill='#60768a')
  d.text((W-200,H-90),'PAGE '+str(idx),font=F(19),fill='#60768a')
  im.save(A/path,optimize=True);images.append(path)
 def nextcol():
  nonlocal col,x,y
  if col==0:col=1;x=822;y=255
  else:save();start()
 start()
 for heading,paragraphs in sections:
  need=89+sum(len(wrap(d,p[2:] if p.startswith('- ') else p,F(23),650 if p.startswith('- ') else 685))*35+12 for p in paragraphs)
  if need < (H-415) and y+need>H-155:nextcol()
  d.rounded_rectangle((x,y,x+700,y+51),radius=8,fill='#123752')
  d.text((x+16,y+8),heading.upper()[:35],font=F(27,True),fill='white')
  y+=69
  for p in paragraphs:
   bullet=p.startswith('- ');p=p[2:] if bullet else p
   for j,line in enumerate(wrap(d,p,F(23),650 if bullet else 685)):
    if y+39>H-158:nextcol()
    if bullet and j==0:d.ellipse((x+8,y+13,x+17,y+22),fill='#0c97a2')
    d.text((x+(30 if bullet else 7),y),line,font=F(23),fill='#233746')
    y+=35
   y+=12
  y+=20
 save()
 return images
def entry(title,file,id,category='Other',extra=None):
 return dict(id=id,title=title,file=file,thumb='',categories=[category],tags=['Studies'],studies=True,binder=False,ccr=False,width=W,height=H,high_yield=True,recent_rank=0,**(extra or {}))
items=json.loads(C.read_text())
items=[i for i in items if i.get('id') not in ('auto-c59df9646821','upload-5b3c89a5') and not str(i.get('id','')).startswith('png-')]
new=[]
for md in sorted((R/'publications/png').glob('*.md')):
 meta,sections=readmd(md);imgs=render(meta['title'],meta.get('subtitle','Clinical review'),sections,md.stem)
 for j,file in enumerate(imgs,1):
  new.append(entry(meta['title']+(f' - page {j}' if len(imgs)>1 else ''),file,f'png-{md.stem}-{j}',meta.get('category','Other')))
for name,base,title,old_id in [
 ('daily-resuscitation-learning-2026-11-12.pdf','daily-review-12-nov','Daily Resuscitation Learning - 12 November 2026',93),
 ('daily-resuscitation-learning-2026-11-13.pdf','daily-review-13-nov','Daily Resuscitation Learning - 13 November 2026',94)]:
 doc=fitz.open(A/name)
 imgs=[]
 for idx,page in enumerate(doc,1):
  filename=f'{base}-{idx:02d}.png'
  pix=page.get_pixmap(matrix=fitz.Matrix(2.2,2.2),alpha=False)
  pix.save(str(A/filename))
  imgs.append(filename)
 for j,file in enumerate(imgs,1):
  new.append(entry(title+(f' - page {j}' if len(imgs)>1 else ''),file,f'png-{base}-{j}',extra={'replaces_id':old_id} if j==1 else {}))
C.write_text(json.dumps(new+items,ensure_ascii=False,indent=2)+'\n')
print('Generated',len(new),'PNG entries; files:',', '.join(x['file'] for x in new))
