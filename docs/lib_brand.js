// Helper dung tai lieu Word theo brand kit "Aqua Blue & Warm Sand" (Dung gui ngay 14/09/2026).
// Cung API voi lib.js (p, h1, h2, h3, bullet, num, table, pageBreak, build, img) cong ghiChu() va luuY().
//
// Quy chuan:
//   Mau   : Aqua #4BACC6 (header bang, duong nhan), Ice Blue #DAEEF3 (nen ghi chu), Warm Sand #C89B72 (luu y, nhan phu),
//           Graphite #27343A (tieu de, noi dung), trang #FFFFFF.
//   Font  : Heading 1 Aptos Display Bold 20pt; Heading 2 Aptos Semibold 14pt; Heading 3 Aptos Semibold 12pt;
//           Normal Aptos 11pt; Caption Aptos Italic 9pt. Heading co vach Aqua ben trai.
//   Trang : A4 doc, le 20 mm, gian dong 1,15, sau doan 6 pt, Heading 1 truoc 18 pt sau 8 pt, canh trai, heading giu cung doan sau.
//   Bang  : header nen Aqua, vien 0,5 pt, dem o 2 mm, lap header khi bang sang trang.
//   Ghi chu: nen Ice Blue, vach Aqua. Luu y: vach Warm Sand, chu Graphite.
const fs = require("fs");
const {
  Document, Packer, Paragraph, TextRun, Table, TableRow, TableCell, Header, Footer, AlignmentType, LevelFormat,
  HeadingLevel, BorderStyle, WidthType, ShadingType, PageNumber, PageBreak, ImageRun, TabStopType,
} = require("docx");

const MAU = { aqua: "4BACC6", ice: "DAEEF3", sand: "C89B72", sandNen: "F4EEE8", graphite: "27343A", xam: "5F6B70", vien: "A9D5E2" };
const FONT = "Aptos", FONT_TIEU_DE = "Aptos Display";
const MM = 56.7;                                   // 1 mm = 56,7 dxa
const LE = Math.round(20 * MM);                    // le 20 mm
const CONTENT_W = 11906 - 2 * LE;                  // A4 rong 210 mm

const vach = (color, size = 24) => ({ left: { style: BorderStyle.SINGLE, size, color, space: 10 } });
const run = (t, o = {}) => new TextRun(typeof t === "string" ? { text: t, font: FONT, color: MAU.graphite, ...o } : { font: FONT, color: MAU.graphite, ...t, ...o });

function p(text, opts = {}) {
  const runs = Array.isArray(text) ? text : [text];
  return new Paragraph({ spacing: { after: 120, line: 276 }, ...opts, children: runs.map((t) => run(t)) });
}
const tieuDe = (level, t, size, font, before, after) => new Paragraph({
  heading: level, keepNext: true, keepLines: true, spacing: { before, after },
  border: vach(MAU.aqua, level === HeadingLevel.HEADING_1 ? 36 : 24), indent: { left: 170 },
  children: [new TextRun({ text: t, font, size, bold: true, color: MAU.graphite })],
});
const h1 = (t) => tieuDe(HeadingLevel.HEADING_1, t, 40, FONT_TIEU_DE, 360, 160);
const h2 = (t) => tieuDe(HeadingLevel.HEADING_2, t, 28, FONT, 280, 120);
const h3 = (t) => tieuDe(HeadingLevel.HEADING_3, t, 24, FONT, 200, 100);
const bullet = (t) => new Paragraph({ numbering: { reference: "bullets", level: 0 }, spacing: { after: 80, line: 276 }, children: [run(t)] });
const num = (t, ref = "numbers") => new Paragraph({ numbering: { reference: ref, level: 0 }, spacing: { after: 80, line: 276 }, children: [run(t)] });
const pageBreak = () => new Paragraph({ children: [new PageBreak()] });

// Khoi ghi chu: nen Ice Blue, vach Aqua. Khoi luu y: nen cat nhat, vach Warm Sand, co tieu de dam.
function khoi(nen, mauVach, tieu, noiDung) {
  const out = [];
  const chung = { shading: { type: ShadingType.CLEAR, fill: nen }, border: vach(mauVach, 36), indent: { left: 200, right: 120 } };
  if (tieu) out.push(new Paragraph({ ...chung, keepNext: true, spacing: { before: 120, after: 0, line: 276 }, children: [run(tieu, { bold: true })] }));
  out.push(new Paragraph({ ...chung, spacing: { before: tieu ? 0 : 120, after: 200, line: 276 }, children: [run(noiDung)] }));
  return out;
}
const ghiChu = (noiDung, tieu = "") => khoi(MAU.ice, MAU.aqua, tieu, noiDung);
const luuY = (noiDung, tieu = "") => khoi(MAU.sandNen, MAU.sand, tieu, noiDung);

const vienO = { style: BorderStyle.SINGLE, size: 4, color: MAU.vien };
function cell(text, w, head) {
  const runs = Array.isArray(text) ? text : [text];
  return new TableCell({
    borders: { top: vienO, bottom: vienO, left: vienO, right: vienO },
    width: { size: w, type: WidthType.DXA },
    margins: { top: 113, bottom: 113, left: 113, right: 113 },
    shading: head ? { fill: MAU.aqua, type: ShadingType.CLEAR } : undefined,
    children: runs.map((r) => new Paragraph({ spacing: { after: 0, line: 252 },
      children: [run(typeof r === "string" ? { text: r } : r, { size: 20, bold: !!head })] })),
  });
}
// table(headers, rows, ratios): do rong tinh theo ti le, quy ve CONTENT_W.
function table(headers, rows, ratios) {
  const total = ratios.reduce((a, b) => a + b, 0);
  const widths = ratios.map((r) => Math.round((r / total) * CONTENT_W));
  widths[widths.length - 1] += CONTENT_W - widths.reduce((a, b) => a + b, 0);
  const mk = (cells, head) => new TableRow({ tableHeader: head, cantSplit: !head, children: cells.map((c, i) => cell(c, widths[i], head)) });
  return [new Table({ width: { size: CONTENT_W, type: WidthType.DXA }, columnWidths: widths,
    rows: [mk(headers, true), ...rows.map((r) => mk(r, false))] }), new Paragraph({ spacing: { after: 120 }, children: [] })];
}

function img(file, widthPx, heightPx, caption) {
  const out = [new Paragraph({ alignment: AlignmentType.CENTER, keepNext: !!caption, spacing: { before: 120, after: 60 }, children: [new ImageRun({
    type: "png", data: fs.readFileSync(file), transformation: { width: widthPx, height: heightPx },
    altText: { title: caption, description: caption, name: caption } })] })];
  if (caption) out.push(new Paragraph({ alignment: AlignmentType.CENTER, spacing: { after: 200 },
    children: [run(caption, { size: 18, italics: true, color: MAU.xam })] }));
  return out;
}

// meta: { headerLeft, headerRight, footer, cover: [dong...] }
function build(title, subtitle, meta, children, outFile) {
  const tabPhai = [{ type: TabStopType.RIGHT, position: CONTENT_W }];
  const header = new Header({ children: [new Paragraph({
    tabStops: tabPhai, spacing: { after: 120 }, border: { bottom: { style: BorderStyle.SINGLE, size: 8, color: MAU.aqua, space: 6 } },
    children: [run(meta.headerLeft || "NaviWorld", { size: 18, bold: true, color: MAU.xam }),
      run(`\t${(meta.headerRight || "").toUpperCase()}`, { size: 16, color: MAU.xam, characterSpacing: 20 })],
  })] });
  const footer = new Footer({ children: [new Paragraph({
    tabStops: tabPhai, border: { top: { style: BorderStyle.SINGLE, size: 8, color: MAU.aqua, space: 6 } },
    children: [run(meta.footer || title, { size: 18, color: MAU.xam }),
      new TextRun({ children: ["\t", PageNumber.CURRENT], font: FONT, size: 18, color: MAU.graphite })],
  })] });
  const bia = [
    // Khoang trong dat o doan rieng: vach trai cua doan tieu de keo dai theo ca spacing before.
    new Paragraph({ spacing: { before: 2600, after: 0 }, children: [] }),
    new Paragraph({ spacing: { before: 0, after: 160 }, border: vach(MAU.aqua, 48), indent: { left: 200 },
      children: [new TextRun({ text: title, font: FONT_TIEU_DE, size: 52, bold: true, color: MAU.graphite })] }),
    new Paragraph({ spacing: { after: 360 }, indent: { left: 200 }, children: [run(subtitle, { size: 28, color: MAU.aqua })] }),
    ...(meta.cover || []).map((line) => new Paragraph({ spacing: { after: 80 }, indent: { left: 200 }, children: [run(line, { size: 20, color: MAU.xam })] })),
    new Paragraph({ spacing: { before: 200 }, border: { bottom: { style: BorderStyle.SINGLE, size: 8, color: MAU.sand, space: 1 } }, children: [] }),
    pageBreak(),
  ];
  const listIndent = { indent: { left: 540, hanging: 300 } };
  const doc = new Document({
    creator: "NaviWorld Vietnam", title,
    styles: {
      default: { document: { run: { font: FONT, size: 22, color: MAU.graphite }, paragraph: { spacing: { line: 276, after: 120 } } } },
      paragraphStyles: [
        { id: "Heading1", name: "Heading 1", basedOn: "Normal", next: "Normal", quickFormat: true,
          run: { font: FONT_TIEU_DE, size: 40, bold: true, color: MAU.graphite }, paragraph: { spacing: { before: 360, after: 160 }, outlineLevel: 0, keepNext: true } },
        { id: "Heading2", name: "Heading 2", basedOn: "Normal", next: "Normal", quickFormat: true,
          run: { font: FONT, size: 28, bold: true, color: MAU.graphite }, paragraph: { spacing: { before: 280, after: 120 }, outlineLevel: 1, keepNext: true } },
        { id: "Heading3", name: "Heading 3", basedOn: "Normal", next: "Normal", quickFormat: true,
          run: { font: FONT, size: 24, bold: true, color: MAU.graphite }, paragraph: { spacing: { before: 200, after: 100 }, outlineLevel: 2, keepNext: true } },
        { id: "Caption", name: "Caption", basedOn: "Normal", next: "Normal", quickFormat: true, run: { font: FONT, size: 18, italics: true } },
      ],
    },
    numbering: { config: [
      { reference: "bullets", levels: [{ level: 0, format: LevelFormat.BULLET, text: "•", alignment: AlignmentType.LEFT, style: { paragraph: listIndent, run: { color: MAU.aqua } } }] },
      ...["numbers", "numbers2", "numbers3"].map((reference) => ({ reference, levels: [{ level: 0, format: LevelFormat.DECIMAL, text: "%1.", alignment: AlignmentType.LEFT, style: { paragraph: listIndent } }] })),
    ] },
    sections: [{
      properties: { page: { size: { width: 11906, height: 16838 }, margin: { top: LE, right: LE, bottom: LE, left: LE, header: 567, footer: 567 } } },
      headers: { default: header }, footers: { default: footer },
      children: [...bia, ...children],
    }],
  });
  return Packer.toBuffer(doc).then((buf) => { fs.writeFileSync(outFile, buf); console.log("wrote", outFile); });
}

module.exports = { p, h1, h2, h3, bullet, num, table, pageBreak, build, img, ghiChu, luuY, MAU, CONTENT_W };
