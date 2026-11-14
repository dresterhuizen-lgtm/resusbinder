#!/usr/bin/env python3
"""Publish reviewed Markdown teaching notes as PDFs and update Resus Binder's upload catalog."""
import json, re, hashlib, sys
from pathlib import Path
from xml.sax.saxutils import escape
from reportlab.lib import colors
from reportlab.lib.enums import TA_LEFT
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.pagesizes import A4
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, KeepTogether
from reportlab.lib.units import mm

ROOT=Path(__file__).resolve().parents[1]
INBOX=ROOT/'publications'/'pending'
ASSETS=ROOT/'assets'
CATALOG=ROOT/'uploads.json'
CATEGORIES={'Studies','Resus Binder','CCR'}

def slugify(s):
    return re.sub(r'[^a-z0-9]+','-',s.lower()).strip('-')[:72] or 'document'

def parse(path):
    raw=path.read_text(encoding='utf-8')
    if not raw.startswith('---\n'):
        raise ValueError(f'{path}: YAML-style header required')
    _, header, body=raw.split('---\n',2)
    meta={}
    for line in header.splitlines():
        if ':' in line:
            key,value=line.split(':',1)
            meta[key.strip().lower()]=value.strip().strip('"').strip("'")
    title=meta.get('title','')
    section=meta.get('section','Studies')
    if not title or len(title)>180 or section not in CATEGORIES:
        raise ValueError(f'{path}: invalid title or section')
    if len(body.strip())<50:
        raise ValueError(f'{path}: document body too short')
    return title,section,body

def paragraph(text,style):
    text=escape(text)
    text=re.sub(r'\*\*(.+?)\*\*',r'<b>\1</b>',text)
    text=re.sub(r'\*(.+?)\*',r'<i>\1</i>',text)
    return Paragraph(text,style)

def generate(title,body,target):
    styles={
        'title':ParagraphStyle('Title',fontName='Helvetica-Bold',fontSize=19,leading=24,textColor=colors.HexColor('#17324a'),spaceAfter=12),
        'h2':ParagraphStyle('Heading',fontName='Helvetica-Bold',fontSize=12,leading=16,textColor=colors.HexColor('#16667c'),spaceBefore=13,spaceAfter=6),
        'body':ParagraphStyle('Body',fontName='Helvetica',fontSize=9.5,leading=14,spaceAfter=7),
        'bullet':ParagraphStyle('Bullet',fontName='Helvetica',fontSize=9.5,leading=14,leftIndent=13,firstLineIndent=-9,spaceAfter=5),
        'small':ParagraphStyle('Small',fontName='Helvetica',fontSize=8,leading=11,textColor=colors.HexColor('#586a7a'),spaceAfter=8)
    }
    doc=SimpleDocTemplate(str(target),pagesize=A4,rightMargin=19*mm,leftMargin=19*mm,topMargin=18*mm,bottomMargin=18*mm,title=title)
    story=[paragraph(title,styles['title'])]
    for line in body.splitlines():
        t=line.strip()
        if not t:
            story.append(Spacer(1,4*mm))
        elif t.startswith('## '):
            story.append(paragraph(t[3:],styles['h2']))
        elif t.startswith('# '):
            story.append(paragraph(t[2:],styles['h2']))
        elif t.startswith(('- ','* ')):
            story.append(paragraph('• '+t[2:],styles['bullet']))
        else:
            story.append(paragraph(t,styles['body']))
    doc.build(story)
    if target.stat().st_size<1000 or target.read_bytes()[:5]!=b'%PDF-':
        raise ValueError(f'Invalid generated PDF: {target}')

def main():
    ASSETS.mkdir(exist_ok=True)
    manifest=json.loads(CATALOG.read_text(encoding='utf-8')) if CATALOG.exists() else []
    if not isinstance(manifest,list):raise ValueError('Invalid catalog')
    seen={p.get('id') for p in manifest}
    count=0
    for source in sorted(INBOX.glob('*.md')):
        title,section,body=parse(source)
        digest=hashlib.sha256(source.read_bytes()).hexdigest()[:12]
        identifier='auto-'+digest
        if identifier in seen:continue
        filename=f'{slugify(title)}-{digest}.pdf'
        target=ASSETS/filename
        generate(title,body,target)
        item={'id':identifier,'title':title,'pdf':filename,'thumb':'','categories':['Other'] if section=='Studies' else [section],
              'tags':[section],'studies':section=='Studies','binder':section=='Resus Binder','ccr':section=='CCR',
              'high_yield':False,'width':600,'height':800,'recent_rank':0}
        manifest.insert(0,item)
        seen.add(identifier)
        count+=1
    if count:
        CATALOG.write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print(f'Published {count} new document(s)')

if __name__=='__main__':
    main()
