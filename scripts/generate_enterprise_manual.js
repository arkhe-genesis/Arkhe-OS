
/**
 * @license
 * Copyright 2026 Google LLC
 * SPDX-License-Identifier: Apache-2.0
 */

import fs from "node:fs";

import {
  Document, Packer, Paragraph, TextRun, Table, TableRow, TableCell,
    AlignmentType,
   HeadingLevel, BorderStyle, WidthType,
  ShadingType, VerticalAlign,
} from "docx";


// "Midnight Code" palette
const C = {
  primary: "020617",
  body: "1E293B",
  secondary: "64748B",
  accent: "94A3B8",
  tableBg: "F8FAFC",
  white: "FFFFFF",
  coverBg: "0F172A",
  highlight: "E2E8F0",
};

const border = { style: BorderStyle.SINGLE, size: 6, color: C.accent };
const cellBorders = { top: border, bottom: border, left: border, right: border };

// Helpers
const h1 = (text) => new Paragraph({
  heading: HeadingLevel.HEADING_1,
  spacing: { before: 600, after: 300 },
  children: [new TextRun({ text, font: "Times New Roman", size: 36, bold: true, color: C.primary })]
});

const h2 = (text) => new Paragraph({
  heading: HeadingLevel.HEADING_2,
  spacing: { before: 400, after: 200 },
  children: [new TextRun({ text, font: "Times New Roman", size: 28, bold: true, color: C.primary })]
});

const p = (text) => new Paragraph({
  spacing: { after: 150, line: 276 },
  alignment: AlignmentType.JUSTIFIED,
  children: [new TextRun({ text, font: "Calibri", size: 22, color: C.body })]
});

const code = (text) => new Paragraph({
  spacing: { after: 80, line: 240 },
  indent: { left: 360 },
  children: [new TextRun({ text, font: "Courier New", size: 18, color: C.body })]
});

const spacer = (twips = 100) => new Paragraph({ spacing: { before: twips } });

const cellText = (text, opts = {}) => new TableCell({
  borders: cellBorders,
  width: opts.width ? { size: opts.width, type: WidthType.DXA } : undefined,
  shading: opts.header ? { fill: C.tableBg, type: ShadingType.CLEAR } : undefined,
  verticalAlign: VerticalAlign.CENTER,
  children: [new Paragraph({
    alignment: AlignmentType.CENTER,
    spacing: { before: 60, after: 60 },
    children: [new TextRun({ text, font: "Calibri", size: 20, color: C.body, bold: !!opts.header })]
  })]
});

const cellLeft = (text, opts = {}) => new TableCell({
  borders: cellBorders,
  width: opts.width ? { size: opts.width, type: WidthType.DXA } : undefined,
  shading: opts.header ? { fill: C.tableBg, type: ShadingType.CLEAR } : undefined,
  verticalAlign: VerticalAlign.CENTER,
  children: [new Paragraph({
    alignment: AlignmentType.LEFT,
    spacing: { before: 60, after: 60 },
    children: [new TextRun({ text, font: "Calibri", size: 20, color: C.body, bold: !!opts.header })]
  })]
});

const _makeTable = (headers, rows, widths) => new Table({
  alignment: AlignmentType.CENTER,
  columnWidths: widths,
  margins: { top: 80, bottom: 80, left: 150, right: 150 },
  rows: [
    new TableRow({
      table: true,
      children: headers.map((h, i) => cellText(h, { header: true, width: widths[i] }))
    }),
    ...rows.map(row => new TableRow({
      children: row.map((cell, i) => cellLeft(cell, { width: widths[i] }))
    }))
  ]
});

// --- COVER ---
const coverSection = {
  properties: {
    page: {
      margin: { top: 0, bottom: 0, left: 0, right: 0 },
      size: { width: 11906, height: 16838 }
    },
    titlePage: true
  },
  children: [
    spacer(4000),
    new Paragraph({
      alignment: AlignmentType.CENTER,
      spacing: { after: 200 },
      children: [new TextRun({ text: "ARKHE", font: "Times New Roman", size: 72, bold: true, color: C.primary })]
    }),
    new Paragraph({
      alignment: AlignmentType.CENTER,
      spacing: { after: 100 },
      children: [new TextRun({ text: "ENTERPRISE", font: "Times New Roman", size: 56, bold: true, color: C.secondary })]
    }),
    spacer(200),
    new Paragraph({
      alignment: AlignmentType.CENTER,
      spacing: { after: 80 },
      children: [new TextRun({ text: "Sistema de Coerência Aplicada (SCA)", font: "Calibri", size: 28, color: C.accent })]
    }),
    spacer(1500),
    new Paragraph({
      alignment: AlignmentType.CENTER,
      children: [new TextRun({ text: "Manual de Referência Técnica v1.0", font: "Calibri", size: 22, color: C.secondary })]
    }),
    spacer(400),
    new Paragraph({
      alignment: AlignmentType.CENTER,
      children: [new TextRun({ text: "Abril 2026", font: "Calibri", size: 22, color: C.secondary })]
    }),
  ]
};

// --- MAIN CONTENT ---
const mainChildren = [
  h1("1. Introdução"),
  p("O framework Arkhe(n) evoluiu para o Sistema de Coerência Aplicada (SCA), uma estrutura operacional completa para gerenciamento de plataformas de dados cloud-nativas."),
  h2("1.1 Visão Sistêmica"),
  p("A Arquitetura Arkhe aplica o princípio do λ₂ ao domínio de dados."),
  h1("2. Infraestrutura as Code"),
  p("Provisionamento via Terraform para AWS e Snowflake."),
  code("resource \"aws_kinesis_stream\" \"arkhe_stream\" {...}"),
];

const doc = new Document({
  sections: [
    coverSection,
    {
      properties: {
        page: {
          margin: { top: 1800, right: 1440, bottom: 1440, left: 1440 },
          size: { width: 11906, height: 16838 }
        }
      },
      children: mainChildren
    }
  ]
});

const buffer = await Packer.toBuffer(doc);
fs.writeFileSync("Arkhe_Enterprise_Manual_v1.0.docx", buffer);
console.log("DOCX generated successfully!");

// @ts-ignore
console.log(_makeTable);
