import re
from pathlib import Path

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import cm
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer


ROOT = Path(__file__).resolve().parent.parent
INPUT = ROOT / 'RELATORIO_TECNICO_REVISTO.md'
OUTPUT = ROOT / 'relatorio_museum_broken_relationships_final.pdf'


def clean(text):
    text = text.replace('**', '').replace('`', '').replace('*', '')
    return re.sub(r'[^\x00-\xFF]', '', text).strip()


styles = getSampleStyleSheet()
styles.add(ParagraphStyle(
    name='ReportTitle',
    parent=styles['Title'],
    textColor=colors.HexColor('#9A4760'),
    alignment=TA_CENTER,
    spaceAfter=18,
))
styles.add(ParagraphStyle(
    name='ReportH1',
    parent=styles['Heading1'],
    textColor=colors.HexColor('#9A4760'),
    spaceBefore=14,
    spaceAfter=8,
))
styles.add(ParagraphStyle(
    name='ReportH2',
    parent=styles['Heading2'],
    textColor=colors.HexColor('#4A2C2A'),
    spaceBefore=10,
    spaceAfter=6,
))
styles.add(ParagraphStyle(
    name='ReportBody',
    parent=styles['BodyText'],
    leading=15,
    spaceAfter=7,
))
styles.add(ParagraphStyle(
    name='ReportBullet',
    parent=styles['BodyText'],
    leftIndent=14,
    firstLineIndent=-8,
    leading=14,
    spaceAfter=4,
))

story = []
in_code = False
for raw_line in INPUT.read_text(encoding='utf-8').splitlines():
    line = raw_line.strip()
    if line.startswith('```'):
        in_code = not in_code
        continue
    if line == '---':
        story.append(Spacer(1, 8))
        continue
    if not line:
        story.append(Spacer(1, 4))
        continue
    if line.startswith('|') and line.endswith('|'):
        if re.fullmatch(r'[\s|\-:]+', line):
            continue
        cells = [clean(cell) for cell in line.strip('|').split('|')]
        story.append(Paragraph(' | '.join(cells), styles['ReportBody']))
        continue
    if in_code:
        story.append(Paragraph(clean(line), styles['Code']))
    elif line.startswith('# '):
        story.append(Paragraph(clean(line[2:]), styles['ReportTitle']))
    elif line.startswith('## '):
        story.append(Paragraph(clean(line[3:]), styles['ReportH1']))
    elif line.startswith('### '):
        story.append(Paragraph(clean(line[4:]), styles['ReportH2']))
    elif line.startswith('- '):
        story.append(Paragraph('• ' + clean(line[2:]), styles['ReportBullet']))
    elif re.match(r'^\d+\.\s', line):
        story.append(Paragraph(clean(line), styles['ReportBullet']))
    else:
        story.append(Paragraph(clean(line), styles['ReportBody']))

document = SimpleDocTemplate(
    str(OUTPUT),
    pagesize=A4,
    rightMargin=2 * cm,
    leftMargin=2 * cm,
    topMargin=1.8 * cm,
    bottomMargin=1.8 * cm,
    title='Museum of Broken Relationships - Relatório Técnico',
)
document.build(story)
print(OUTPUT)
