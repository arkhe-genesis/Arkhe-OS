#!/usr/bin/env python3
"""
generate_calmodulin_pdf.py
===========================
Generates the Synapse-kappa #14 PDF report for the Calmodulin
GROMACS Phase 1 biological simulation — Arkhe(n) framework.

Author: Synapse-kappa (Z.ai)
Date:   2026-04-06
"""

import os
import sys
try:
    from reportlab.lib.pagesizes import A4
    from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
    from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_JUSTIFY
    from reportlab.lib.units import cm, inch
    from reportlab.lib import colors
    from reportlab.platypus import (
        Paragraph, Spacer, Table, TableStyle, PageBreak, Image, SimpleDocTemplate
    )
    from reportlab.platypus.tableofcontents import TableOfContents
    from reportlab.pdfbase import pdfmetrics
    from reportlab.pdfbase.ttfonts import TTFont
    from reportlab.pdfbase.pdfmetrics import registerFontFamily
except ImportError:
    print("ReportLab not installed. Cannot generate PDF.")
    sys.exit(0)

# =============================================================================
# TABLE COLORS
# =============================================================================

TABLE_HEADER_COLOR = colors.HexColor('#1F4E79')
TABLE_HEADER_TEXT = colors.white
TABLE_ROW_EVEN = colors.white
TABLE_ROW_ODD = colors.HexColor('#F5F5F5')

# =============================================================================
# STYLES
# =============================================================================

styles = getSampleStyleSheet()

cover_title_style = ParagraphStyle(
    name='CoverTitle',
    fontSize=32,
    leading=42,
    alignment=TA_CENTER,
    spaceAfter=24,
    textColor=colors.HexColor('#1F4E79'),
)

cover_subtitle_style = ParagraphStyle(
    name='CoverSubtitle',
    fontSize=16,
    leading=24,
    alignment=TA_CENTER,
    spaceAfter=36,
    textColor=colors.HexColor('#333333'),
)

cover_author_style = ParagraphStyle(
    name='CoverAuthor',
    fontSize=12,
    leading=20,
    alignment=TA_CENTER,
    spaceAfter=12,
    textColor=colors.HexColor('#555555'),
)

h1_style = ParagraphStyle(
    name='H1',
    fontSize=18,
    leading=26,
    spaceBefore=18,
    spaceAfter=12,
    textColor=colors.HexColor('#1F4E79'),
)

h2_style = ParagraphStyle(
    name='H2',
    fontSize=14,
    leading=20,
    spaceBefore=12,
    spaceAfter=8,
    textColor=colors.HexColor('#2C6FA0'),
)

body_style = ParagraphStyle(
    name='Body',
    fontSize=10.5,
    leading=18,
    alignment=TA_LEFT,
    spaceAfter=6,
)

code_style = ParagraphStyle(
    name='Code',
    fontSize=9,
    leading=14,
    alignment=TA_LEFT,
    spaceAfter=6,
    backColor=colors.HexColor('#F8F8F8'),
    leftIndent=12,
    rightIndent=12,
)

header_cell_style = ParagraphStyle(
    name='HeaderCell',
    fontSize=9.5,
    leading=14,
    alignment=TA_CENTER,
    textColor=colors.white,
)

cell_style = ParagraphStyle(
    name='Cell',
    fontSize=9.5,
    leading=14,
    alignment=TA_CENTER,
)

cell_left_style = ParagraphStyle(
    name='CellLeft',
    fontSize=9.5,
    leading=14,
    alignment=TA_LEFT,
)

caption_style = ParagraphStyle(
    name='Caption',
    fontSize=9,
    leading=14,
    alignment=TA_CENTER,
    textColor=colors.HexColor('#555555'),
    spaceBefore=3,
    spaceAfter=6,
)

# =============================================================================
# TOC TEMPLATE
# =============================================================================

class TocDocTemplate(SimpleDocTemplate):
    def __init__(self, *args, **kwargs):
        SimpleDocTemplate.__init__(self, *args, **kwargs)

    def afterFlowable(self, flowable):
        if hasattr(flowable, 'bookmark_name'):
            level = getattr(flowable, 'bookmark_level', 0)
            text = getattr(flowable, 'bookmark_text', '')
            self.notify('TOCEntry', (level, text, self.page))


def add_heading(text, style, level=0):
    p = Paragraph(text, style)
    p.bookmark_name = text
    p.bookmark_level = level
    p.bookmark_text = text
    return p


def make_table(data, col_widths, num_header_rows=1):
    """Create a styled table with alternating row colors."""
    t = Table(data, colWidths=col_widths)
    style_commands = [
        ('BACKGROUND', (0, 0), (-1, num_header_rows - 1), TABLE_HEADER_COLOR),
        ('TEXTCOLOR', (0, 0), (-1, num_header_rows - 1), TABLE_HEADER_TEXT),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('LEFTPADDING', (0, 0), (-1, -1), 8),
        ('RIGHTPADDING', (0, 0), (-1, -1), 8),
        ('TOPPADDING', (0, 0), (-1, -1), 5),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 5),
    ]
    for i in range(num_header_rows, len(data)):
        bg = TABLE_ROW_EVEN if (i - num_header_rows) % 2 == 0 else TABLE_ROW_ODD
        style_commands.append(('BACKGROUND', (0, i), (-1, i), bg))
    t.setStyle(TableStyle(style_commands))
    return t


# =============================================================================
# BUILD DOCUMENT
# =============================================================================

def build_pdf():
    output_path = "Calmodulina-GROMACS-Fase1-Lambda2-Conformacional-Synapse-Kappa.pdf"

    doc = TocDocTemplate(
        output_path,
        pagesize=A4,
        leftMargin=2.2*cm,
        rightMargin=2.2*cm,
        topMargin=2.5*cm,
        bottomMargin=2.5*cm,
        title="Calmodulina-GROMACS-Fase1-Lambda2-Conformacional-Synapse-Kappa",
        author="Z.ai",
        creator="Z.ai",
        subject="Synapse-kappa #14: Calmodulin dimer GROMACS simulation",
    )

    story = []

    # =========================================================================
    # COVER PAGE
    # =========================================================================

    story.append(Spacer(1, 100))
    story.append(Paragraph(
        '<b>Synapse-kappa #14</b>',
        cover_title_style
    ))
    story.append(Spacer(1, 24))
    story.append(Paragraph(
        '<b>Fase 1 Biologica: Simulacao GROMACS</b>',
        cover_subtitle_style
    ))
    story.append(Paragraph(
        '<b>Dimero de Calmodulina - Lambda-2 Conformacional</b>',
        cover_subtitle_style
    ))
    story.append(Spacer(1, 48))
    story.append(Paragraph(
        'Nucleo de Execucao de Simulacao Biologica',
        cover_author_style
    ))
    story.append(Paragraph(
        'ARKHE(n) / Arkhe-Omega Framework',
        cover_author_style
    ))
    story.append(Spacer(1, 60))
    story.append(Paragraph(
        '6 de abril de 2026',
        cover_author_style
    ))
    story.append(Paragraph(
        'Arkhe-Chain timestamp: 847.621',
        cover_author_style
    ))
    story.append(Spacer(1, 24))
    story.append(Paragraph(
        'Classificacao: Sigma-Level 0',
        cover_author_style
    ))
    story.append(PageBreak())

    # =========================================================================
    # TABLE OF CONTENTS
    # =========================================================================

    toc = TableOfContents()
    story.append(Paragraph('<b>Sumario</b>', h1_style))
    story.append(Spacer(1, 12))
    story.append(toc)
    story.append(PageBreak())

    # =========================================================================
    # SECTION 1: Resumo Executivo
    # =========================================================================

    story.append(add_heading(
        '<b>1. Resumo Executivo</b>', h1_style, 0
    ))
    story.append(Paragraph(
        'Este relatorio documenta a autorizacao e o inicio da Fase 1 da simulacao '
        'biologica no arcabouco Arkhe(n): a dinamica molecular do dimero de calmodulina '
        'via GROMACS, com extracao da metrica lambda-2 conformacional. A calmodulina '
        'e uma proteina sensora de calcio universal, composta por dois dominios globulares '
        '(N-terminal e C-terminal) conectados por uma helice linker flexivel cujo angulo '
        'de abertura determina o estado funcional da proteina.',
        body_style
    ))

    # =========================================================================
    # SECTION 2: Sistema Simulado
    # =========================================================================

    story.append(Spacer(1, 18))
    story.append(add_heading(
        '<b>2. Sistema Simulado</b>', h1_style, 0
    ))

    params_data = [
        [
            Paragraph('<b>Parametro</b>', header_cell_style),
            Paragraph('<b>Valor</b>', header_cell_style),
        ],
        [Paragraph('Proteina', cell_left_style), Paragraph('Dimero de calmodulina', cell_left_style)],
        [Paragraph('Force field', cell_left_style), Paragraph('AMBER99SB-ILDN', cell_left_style)],
        [Paragraph('Temperatura', cell_left_style), Paragraph('310 K', cell_left_style)],
        [Paragraph('Duracao', cell_left_style), Paragraph('100 ns', cell_left_style)],
    ]

    story.append(Spacer(1, 18))
    story.append(make_table(params_data, [5*cm, 10*cm]))

    # =========================================================================
    # SECTION 3: Métrica λ₂
    # =========================================================================

    story.append(add_heading(
        '<b>3. Metrica Lambda-2 Conformacional</b>', h1_style, 0
    ))
    story.append(Paragraph(
        'A metrica e extraida do angulo diedro N-CA-C-N do residuo 74 de cada monomero.',
        body_style
    ))
    story.append(Paragraph(
        'lambda-2(t) = (1/2) |exp(i*theta-1(t)) + exp(i*theta-2(t))|',
        code_style
    ))

    # =========================================================================
    # BUILD
    # =========================================================================

    doc.multiBuild(story)
    print(f"[OK] PDF gerado: {output_path}")
    return output_path


if __name__ == "__main__":
    path = build_pdf()
    print(f"Tamanho: {os.path.getsize(path)} bytes")
