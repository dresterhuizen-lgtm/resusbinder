#!/usr/bin/env python3
"""Render one professional, citation-bearing, source-controlled PNG study page.

Independent from the legacy multi-document publisher: never rewrites other
uploads.json entries or unrelated PNG assets.
"""
from pathlib import Path
import json,re
from PIL import Image,ImageDraw,ImageFont

ROOT=Path(__file__).resolve().parents[1]
SRC=ROOT/'publications/daily/2026-11-14-steroids-septic-shock.md'
OUT=ROOT/'assets/daily-2026-11-14-septic-shock-steroids-v4.png'
CATALOG=ROOT/'uploads.json'
IDENT='daily-2026-11-14-septic-shock-steroids'
W,H=1800,2600
NAVY='#102b41'; DEEP='#173b50'; TEAL='#138f9d'; INK='#263e50'; MUTED='#506b80'
PAPER='#f8fafb'; DIV='#d6e2e9'
FONTS='/usr/share/fonts/truetype/dejavu/'
def font(size,bold=False):
    return ImageFont.truetype(FONTS+('DejaVuSans-Bold.ttf' if bold else 'DejaVuSans.ttf'),size)
TITLE=font(60,True); SMALL=font(23); BODY=font(24); HEAD=font(30,True); REF=font(19)
def parse(path):
    data=path.read_text(encoding='utf-8')
    _,front,body=data.split('---\n',2)
    meta=dict((x.split(':',1)[0].strip(),x.split(':',1)[1].strip()) for x in front.splitlines() if ':' in x)
    sections={}; heading=None
    for line in body.splitlines():
        line=line.strip()
        if line.startswith('## '):
            heading=line[3:].upper();sections[heading]=[]
        elif line and heading:
            sections[heading].append(line)
    return meta,sections
def wrap(draw,text,f,maxwidth):
    words=text.split(); out=[];line=''
    for word in words:
        probe=(line+' '+word).strip()
        if draw.textbbox((0,0),probe,font=f)[2] <= maxwidth: line=probe
        else:
            if line:out.append(line)
            line=word
    if line:out.append(line)
    return out
def main():
    meta,sections=parse(SRC)
    im=Image.new('RGB',(W,H),PAPER);d=ImageDraw.Draw(im)
    d.rectangle((0,0,W,190),fill=NAVY)
    d.rectangle((0,190,W,199),fill=TEAL)
    d.text((72,22),'RESUS BINDER  /  DAILY RESUSCITATION LEARNING',font=font(24,True),fill='#8adfe8')
    d.text((72,68),meta['title'],font=TITLE,fill='#ffffff')
    d.text((72,148),meta['subtitle'],font=SMALL,fill='#c1d5e2')
    d.text((74,214),'EVIDENCE-INFORMED  •  ADULT SEPTIC SHOCK  •  14 NOVEMBER 2026',font=font(22,True),fill=TEAL)
    # Stable editorial two-column reading order, preserving whole sections.
    columns=[
      ['CURRENT PRACTICE: CANADA FIRST','WHY STEROIDS HELP','FIRST-HOUR ED / RESUSCITATION PLAN'],
      ['RECOGNITION / POCUS / TRAPS','WHAT THE 2026 STUDY ADDS','THE TAKE-HOME MESSAGE','REFERENCES / GUIDELINES']
    ]
    column_x=[72,936]; WIDTH=790
    for col,headings in enumerate(columns):
        x=column_x[col];y=274
        for heading in headings:
            rows=sections.get(heading,[])
            # Count all paragraph lines ahead of painting to catch overflows.
            projected=60
            for text in rows:
                txt=re.sub(r'^\d+\. ','',text) if heading=='FIRST-HOUR APPROACH' else text
                projected+=len(wrap(d,txt,BODY,WIDTH-43))*35+13
            if y+projected>H-148:
                raise RuntimeError(f'Section overflows the single page: {heading} ends at {y+projected}')
            d.rounded_rectangle((x,y,x+WIDTH,y+49),radius=7,fill=DEEP)
            d.text((x+17,y+9),heading,font=HEAD if d.textbbox((0,0),heading,font=HEAD)[2]<WIDTH-35 else font(25,True),fill='#ffffff')
            y+=62
            for item in rows:
                item = re.sub(r'^-\s*', '', item)
                numbered = re.match(r'^(\d+)\. (.+)$', item)
                refs = heading == 'REFERENCES / GUIDELINES'
                size = REF if refs else BODY
                leading = 28 if refs else 35
                if numbered:
                    d.text((x+7,y+2), numbered.group(1)+'.', font=font(23,True), fill=TEAL)
                    lines = wrap(d, numbered.group(2), size, WIDTH-60)
                    indent = 40
                else:
                    d.ellipse((x+8,y+12,x+16,y+20), fill=TEAL)
                    lines = wrap(d, item, size, WIDTH-41)
                    indent = 28
                for line in lines:
                    d.text((x+indent,y),line,font=size,fill=INK)
                    y += leading
                y += 12 if not refs else 9
            y += 17
    d.line((72,H-105,W-72,H-105),fill=DIV,width=3)
    d.text((72,H-88),'REVIEW LEVEL: ORIGINAL ABSTRACT REVIEWED; NETWORK COMPARISONS REQUIRE CAUTION',font=REF,fill=MUTED)
    d.text((W-265,H-88),'RESUS BINDER',font=font(20,True),fill=TEAL)
    OUT.parent.mkdir(exist_ok=True)
    im.save(OUT,optimize=True)
    with Image.open(OUT) as check:
        assert check.size==(W,H) and check.format=='PNG'
        check.verify()
    items=json.loads(CATALOG.read_text())
    entry={
      'id':IDENT,'title':'Daily Resuscitation Learning — 14 Nov 2026 · Steroids in septic shock',
      'file':OUT.name,'thumb':'','categories':['Shock & Hemodynamics'],
      'tags':['Studies','Septic Shock','Steroids','Hydrocortisone','Fludrocortisone'],
      'studies':True,'binder':False,'ccr':False,'width':W,'height':H,
      'high_yield':True,'recent_rank':0,
      'collection':'Daily Resuscitation Learning · 14 Nov 2026','collection_order':1
    }
    items=[i for i in items if i.get('id')!=IDENT]
    CATALOG.write_text(json.dumps([entry]+items,ensure_ascii=False,indent=2)+'\n')
    print(f'Validated {OUT.name}: {W}x{H}; catalog entry: {IDENT}')
if __name__=='__main__':
    main()
