#!/usr/bin/env python3
import os
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image

PDF_PATH = os.path.join(os.getcwd(), 'arkhe_sovereign_report.pdf')

def make_table(data, col_widths):
    table = Table(data, colWidths=col_widths)
    table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
        ('GRID', (0, 0), (-1, -1), 1, colors.black),
    ]))
    return table

def build_report():
    doc = SimpleDocTemplate(PDF_PATH, pagesize=A4)
    styles = getSampleStyleSheet()
    story = []

    title_style = ParagraphStyle(
        'TitleStyle', parent=styles['Title'], fontSize=24, spaceAfter=20, alignment=1
    )
    header_cell_style = ParagraphStyle('HeaderCellStyle', parent=styles['Normal'], fontSize=10, textColor=colors.whitesmoke, alignment=1)
    cell_style = ParagraphStyle('CellStyle', parent=styles['Normal'], fontSize=9, alignment=1)
    cell_left_style = ParagraphStyle('CellLeftStyle', parent=styles['Normal'], fontSize=9, alignment=0)
    caption_style = ParagraphStyle('CaptionStyle', parent=styles['Italic'], fontSize=8, alignment=1, spaceBefore=6)

    story.append(Paragraph('ARKHE-Chain Sovereign Stack Report', title_style))
    story.append(Spacer(1, 18))

    story.append(Paragraph('<b>Infrastructure Fundamental Constants</b>', styles['Heading2']))
    story.append(Spacer(1, 12))

    const_data = [
        [Paragraph('<b>Constant</b>', header_cell_style),
         Paragraph('<b>Value</b>', header_cell_style),
         Paragraph('<b>Description</b>', header_cell_style)],
        [Paragraph('lambda-2-crit', cell_left_style),
         Paragraph('0.847', cell_style),
         Paragraph('Critical coherence threshold', cell_left_style)],
        [Paragraph('phi', cell_left_style),
         Paragraph('1.618', cell_style),
         Paragraph('Golden ratio (hybrid consensus)', cell_left_style)],
        [Paragraph('K-c', cell_left_style),
         Paragraph('0.618', cell_style),
         Paragraph('Kuramoto critical coupling', cell_left_style)],
        [Paragraph('f-bio', cell_left_style),
         Paragraph('40 Hz', cell_style),
         Paragraph('Biological oscillation frequency', cell_left_style)],
        [Paragraph('N (oscillators)', cell_left_style),
         Paragraph('144,000', cell_style),
         Paragraph('Rio City-State resident nodes', cell_left_style)],
    ]
    const_table = make_table(const_data, [3.5*cm, 3.0*cm, 7.0*cm])
    story.append(const_table)
    story.append(Spacer(1, 6))
    story.append(Paragraph('<b>Table 9.</b> ARKHE-Chain Fundamental Constants', caption_style))

    doc.build(story)
    print(f"PDF generated: {PDF_PATH}")

if __name__ == '__main__':
    build_report()
