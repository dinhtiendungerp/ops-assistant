// Helper dung chung cho hai tai lieu. Noi dung nam o content_*.js.
const fs = require("fs");
const {
  Document, Packer, Paragraph, TextRun, Table, TableRow, TableCell, Header, Footer,
  AlignmentType, LevelFormat, HeadingLevel, BorderStyle, WidthType, ShadingType, PageNumber, PageBreak, ImageRun,
} = require("docx");

const CONTENT_W = 9026; // A4, le 1 inch
const border = { style: BorderStyle.SINGLE, size: 4, color: "BFBFBF" };
const borders = { top: border, bottom: border, left: border, right: border };

function p(text, opts = {}) {
  const runs = Array.isArray(text) ? text : [text];
  return new Paragraph({
    spacing: { after: 120, line: 276 },
    ...opts,
    children: runs.map((t) => (typeof t === "string" ? new TextRun(t) : new TextRun(t))),
  });
}
const h1 = (t) => new Paragraph({ heading: HeadingLevel.HEADING_1, children: [new TextRun(t)] });
const h2 = (t) => new Paragraph({ heading: HeadingLevel.HEADING_2, children: [new TextRun(t)] });
const h3 = (t) => new Paragraph({ heading: HeadingLevel.HEADING_3, children: [new TextRun(t)] });
const bullet = (t) => new Paragraph({ numbering: { reference: "bullets", level: 0 }, spacing: { after: 60 }, children: [new TextRun(t)] });
const num = (t, ref = "numbers") => new Paragraph({ numbering: { reference: ref, level: 0 }, spacing: { after: 60 }, children: [new TextRun(t)] });
const pageBreak = () => new Paragraph({ children: [new PageBreak()] });

function cell(text, w, opts = {}) {
  const runs = Array.isArray(text) ? text : [text];
  return new TableCell({
    borders,
    width: { size: w, type: WidthType.DXA },
    margins: { top: 60, bottom: 60, left: 100, right: 100 },
    shading: opts.head ? { fill: "E7EEF5", type: ShadingType.CLEAR } : undefined,
    children: runs.map((r) => new Paragraph({ spacing: { after: 0 }, children: [new TextRun(typeof r === "string" ? { text: r, bold: !!opts.head, size: 20 } : { size: 20, ...r })] })),
  });
}

// table(headers, rows, widths) ; widths tinh theo ti le, tu quy ve CONTENT_W
function table(headers, rows, ratios) {
  const total = ratios.reduce((a, b) => a + b, 0);
  const widths = ratios.map((r) => Math.round((r / total) * CONTENT_W));
  widths[widths.length - 1] += CONTENT_W - widths.reduce((a, b) => a + b, 0);
  const mk = (cells, head) => new TableRow({ tableHeader: head, children: cells.map((c, i) => cell(c, widths[i], { head })) });
  return new Table({
    width: { size: CONTENT_W, type: WidthType.DXA },
    columnWidths: widths,
    rows: [mk(headers, true), ...rows.map((r) => mk(r, false))],
  });
}

function build(title, subtitle, meta, children, outFile) {
  const doc = new Document({
    creator: "NaviWorld Vietnam",
    title,
    styles: {
      default: { document: { run: { font: "Arial", size: 22 } } },
      paragraphStyles: [
        { id: "Heading1", name: "Heading 1", basedOn: "Normal", next: "Normal", quickFormat: true,
          run: { size: 30, bold: true, font: "Arial", color: "1F3864" }, paragraph: { spacing: { before: 320, after: 160 }, outlineLevel: 0 } },
        { id: "Heading2", name: "Heading 2", basedOn: "Normal", next: "Normal", quickFormat: true,
          run: { size: 25, bold: true, font: "Arial", color: "1F3864" }, paragraph: { spacing: { before: 240, after: 120 }, outlineLevel: 1 } },
        { id: "Heading3", name: "Heading 3", basedOn: "Normal", next: "Normal", quickFormat: true,
          run: { size: 22, bold: true, font: "Arial" }, paragraph: { spacing: { before: 160, after: 80 }, outlineLevel: 2 } },
      ],
    },
    numbering: {
      config: [
        { reference: "bullets", levels: [{ level: 0, format: LevelFormat.BULLET, text: "•", alignment: AlignmentType.LEFT, style: { paragraph: { indent: { left: 540, hanging: 300 } } } }] },
        { reference: "numbers", levels: [{ level: 0, format: LevelFormat.DECIMAL, text: "%1.", alignment: AlignmentType.LEFT, style: { paragraph: { indent: { left: 540, hanging: 300 } } } }] },
        { reference: "numbers2", levels: [{ level: 0, format: LevelFormat.DECIMAL, text: "%1.", alignment: AlignmentType.LEFT, style: { paragraph: { indent: { left: 540, hanging: 300 } } } }] },
        { reference: "numbers3", levels: [{ level: 0, format: LevelFormat.DECIMAL, text: "%1.", alignment: AlignmentType.LEFT, style: { paragraph: { indent: { left: 540, hanging: 300 } } } }] },
      ],
    },
    sections: [{
      properties: { page: { size: { width: 11906, height: 16838 }, margin: { top: 1440, right: 1440, bottom: 1440, left: 1440 } } },
      headers: { default: new Header({ children: [new Paragraph({ alignment: AlignmentType.RIGHT, children: [new TextRun({ text: meta.header, size: 16, color: "7F7F7F" })] })] }) },
      footers: { default: new Footer({ children: [new Paragraph({ alignment: AlignmentType.CENTER, children: [new TextRun({ text: `${meta.footer}  |  Trang `, size: 16, color: "7F7F7F" }), new TextRun({ children: [PageNumber.CURRENT], size: 16, color: "7F7F7F" })] })] }) },
      children: [
        new Paragraph({ spacing: { before: 2400, after: 200 }, children: [new TextRun({ text: title, size: 40, bold: true, color: "1F3864" })] }),
        new Paragraph({ spacing: { after: 200 }, children: [new TextRun({ text: subtitle, size: 24, color: "404040" })] }),
        ...meta.cover.map((line) => new Paragraph({ spacing: { after: 60 }, children: [new TextRun({ text: line, size: 20, color: "404040" })] })),
        pageBreak(),
        ...children,
      ],
    }],
  });
  return Packer.toBuffer(doc).then((buf) => { fs.writeFileSync(outFile, buf); console.log("wrote", outFile); });
}

function img(file, widthPx, heightPx, caption) {
  const out = [new Paragraph({ alignment: AlignmentType.CENTER, spacing: { after: 60 }, children: [new ImageRun({
    type: "png", data: fs.readFileSync(file), transformation: { width: widthPx, height: heightPx },
    altText: { title: caption, description: caption, name: caption } })] })];
  if (caption) out.push(new Paragraph({ alignment: AlignmentType.CENTER, spacing: { after: 200 }, children: [new TextRun({ text: caption, size: 18, italics: true, color: "595959" })] }));
  return out;
}

module.exports = { p, h1, h2, h3, bullet, num, table, pageBreak, build, img, TextRun };
