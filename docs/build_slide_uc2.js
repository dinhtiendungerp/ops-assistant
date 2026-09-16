// Slide UC2 Inventory Health & Traceability: kien truc giai phap, luong du lieu, kich ban (dau vao, thao tac, dau ra) kem anh.
//   python tools/cat_anh_slide_uc2.py   (cat anh vao docs/uc2/slide)
//   cd docs; node build_slide_uc2.js
// Mau va font theo brand kit Aqua Blue & Warm Sand (xem lib_brand.js). So lieu lay tu BC NWV01 ngay 14/09/2026, Work Date
// 18/09/2026; anh de xuat va the duyet chup tren du lieu mo phong.
const fs = require("fs");
const path = require("path");
const pptxgen = require("pptxgenjs");

const MAU = { aqua: "4BACC6", ice: "DAEEF3", sand: "C89B72", sandNen: "F4EEE8", graphite: "27343A", xam: "5F6B70", vien: "A9D5E2", nen: "F7FAFB", trang: "FFFFFF" };
const F = "Aptos", FT = "Aptos Display";
const W = 13.333, H = 7.5, LE = 0.6, RONG = W - 2 * LE;
const ANH = path.join(__dirname, "uc2", "slide");
const RA = path.join(__dirname, "11 UC2 Inventory Health - Kien truc va kich ban (slide).pptx");

const pres = new pptxgen();
pres.layout = "LAYOUT_WIDE";
pres.author = "NaviWorld Vietnam";
pres.title = "UC2 Inventory Health & Traceability: kiến trúc giải pháp và kịch bản đáp ứng";

let soTrang = 0;
const TONG_KB = 10;

function kichThuoc(file) {
  const b = fs.readFileSync(file);
  return { w: b.readUInt32BE(16), h: b.readUInt32BE(20) };
}

// Anh vua khung (maxW x maxH), canh theo "trai" | "giua" | "phai"; khung trang vien Aqua nhat va bong nhe.
function anh(slide, ten, x, y, maxW, maxH, canh = "giua", chuThich = "") {
  const f = path.join(ANH, ten + ".png");
  const { w, h } = kichThuoc(f);
  const r = Math.min(maxW / w, maxH / h);
  const iw = w * r, ih = h * r;
  const ix = canh === "trai" ? x : canh === "phai" ? x + maxW - iw : x + (maxW - iw) / 2;
  slide.addShape(pres.shapes.RECTANGLE, { x: ix - 0.05, y: y - 0.05, w: iw + 0.1, h: ih + 0.1, fill: { color: MAU.trang },
    line: { color: MAU.vien, width: 0.75 }, shadow: { type: "outer", color: "000000", opacity: 0.12, blur: 6, offset: 2, angle: 90 } });
  slide.addImage({ path: f, x: ix, y, w: iw, h: ih, altText: chuThich || ten });
  if (chuThich) slide.addText(chuThich, { x: ix, y: y + ih + 0.1, w: iw, h: 0.3, fontFace: F, fontSize: 9, italic: true, color: MAU.xam, margin: 0, isTextBox: true });
  return { x: ix, y, w: iw, h: ih };
}

function trangNoiDung(kicker, tieuDe, ghiChu) {
  const s = pres.addSlide();
  soTrang++;
  s.background = { color: MAU.trang };
  s.addText(kicker.toUpperCase(), { x: LE, y: 0.35, w: 9, h: 0.3, fontFace: F, fontSize: 11, bold: true, color: MAU.aqua, charSpacing: 2, margin: 0, isTextBox: true });
  s.addText(tieuDe, { x: LE, y: 0.62, w: RONG, h: 0.7, fontFace: FT, fontSize: 28, bold: true, color: MAU.graphite, margin: 0, valign: "top", isTextBox: true });
  s.addText("UC2 Inventory Health & Traceability", { x: LE, y: H - 0.42, w: 6, h: 0.25, fontFace: F, fontSize: 9, color: MAU.xam, margin: 0, isTextBox: true });
  s.addText(String(soTrang), { x: W - LE - 1, y: H - 0.42, w: 1, h: 0.25, fontFace: F, fontSize: 9, color: MAU.xam, align: "right", margin: 0, isTextBox: true });
  if (ghiChu) s.addNotes(ghiChu);
  return s;
}

function vong(s, x, y, d, chu, nen = MAU.aqua, mau = MAU.trang, co = 12) {
  s.addShape(pres.shapes.OVAL, { x, y, w: d, h: d, fill: { color: nen }, line: { color: nen, width: 0 } });
  s.addText(chu, { x, y, w: d, h: d, fontFace: F, fontSize: co, bold: true, color: mau, align: "center", valign: "middle", margin: 0, isTextBox: true });
}

function the(s, x, y, w, h, nen = MAU.nen, vien = null) {
  s.addShape(pres.shapes.ROUNDED_RECTANGLE, { x, y, w, h, rectRadius: 0.08, fill: { color: nen }, line: vien ? { color: vien, width: 0.75 } : { color: nen, width: 0 } });
}

// Doan chu nhieu dong: mang chuoi thanh bullet
const dong = (arr, co = 12, mau = MAU.graphite, bullet = true) => arr.map((t, i) => ({
  text: t, options: { bullet: bullet ? { indent: 12 } : false, breakLine: i < arr.length - 1, paraSpaceAfter: 4, fontFace: F, fontSize: co, color: mau },
}));

function nhanVai(s, vai, y = 1.3) {
  s.addText([{ text: "Vai  ", options: { bold: true, color: MAU.graphite } }, { text: vai, options: { color: MAU.graphite } }],
    { shape: pres.shapes.ROUNDED_RECTANGLE, rectRadius: 0.15, x: LE, y, w: Math.min(0.9 + vai.length * 0.085, 6), h: 0.34, fill: { color: MAU.ice },
      line: { color: MAU.ice, width: 0 }, fontFace: F, fontSize: 11, margin: [0, 10, 0, 10], valign: "middle", isTextBox: true });
}

// Ba khoi Dau vao / Thao tac / Dau ra xep doc
function baKhoi(s, x, y, w, khoi, co = 12) {
  const nhan = ["Đầu vào", "Thao tác", "Đầu ra"];
  const cao = khoi.map((k) => k.cao || 1.6);
  let yy = y;
  khoi.forEach((k, i) => {
    the(s, x, yy, w, cao[i] - 0.12, i === 2 ? MAU.ice : MAU.nen);
    vong(s, x + 0.15, yy + 0.14, 0.36, String(i + 1), i === 2 ? MAU.graphite : MAU.aqua);
    s.addText(nhan[i], { x: x + 0.62, y: yy + 0.12, w: w - 0.8, h: 0.4, fontFace: F, fontSize: 13, bold: true, color: MAU.graphite, margin: 0, valign: "middle", isTextBox: true });
    s.addText(dong(k.dong, co), { x: x + 0.55, y: yy + 0.52, w: w - 0.7, h: cao[i] - 0.72, valign: "top", margin: [0, 4, 0, 0], isTextBox: true });
    yy += cao[i];
  });
}

// ============================================================ 1. Bia
{
  const s = pres.addSlide();
  soTrang++;
  s.background = { color: MAU.graphite };
  s.addText("MAROU CHOCOLATE · POC · UC2", { x: LE, y: 1.2, w: 6.5, h: 0.35, fontFace: F, fontSize: 12, bold: true, color: MAU.aqua, charSpacing: 3, margin: 0, isTextBox: true });
  s.addText("Inventory Health & Traceability", { x: LE, y: 1.75, w: 6.4, h: 1.9, fontFace: FT, fontSize: 40, bold: true, color: MAU.trang, margin: 0, valign: "top", isTextBox: true });
  s.addText("Kiến trúc giải pháp và các kịch bản đáp ứng: đầu vào, thao tác, đầu ra", { x: LE, y: 3.7, w: 6.2, h: 0.9, fontFace: F, fontSize: 18, color: MAU.ice, margin: 0, valign: "top", isTextBox: true });
  s.addText([
    { text: "NaviWorld Vietnam · 15/09/2026", options: { breakLine: true } },
    { text: "Hình chụp trên môi trường Business Central demo có LS Central, dữ liệu mô phỏng 5 cửa hàng, 1 kho trung tâm, 21 mặt hàng." },
  ], { x: LE, y: 5.6, w: 6.0, h: 0.9, fontFace: F, fontSize: 11, color: "B8C4C9", margin: 0, valign: "top", paraSpaceAfter: 4, isTextBox: true });
  const f = path.join(ANH, "tong-quan.png");
  s.addImage({ path: f, x: 7.35, y: 0.9, w: 5.4, h: 5.4 * 1620 / 1700, altText: "Màn hình Sức khỏe tồn kho" });
  s.addNotes("Mở đầu: tài liệu đi qua kiến trúc, cách Business Central tính sức khỏe tồn kho, rồi 10 kịch bản đang chạy được trên môi trường demo. Mỗi kịch bản nói rõ cần dữ liệu gì, người dùng làm gì, nhận được gì.");
}

// ============================================================ 2. UC2 dap ung gi
{
  const s = trangNoiDung("Phạm vi", "RFP kỳ vọng bốn đầu ra, POC đã có cả bốn",
    "RFP của Marou ghi bốn đầu ra kỳ vọng cho UC2. Mỗi thẻ là tên trong RFP và tính năng tương ứng trên POC. Hàng số dưới cùng là kết quả Business Central tính trên dữ liệu demo ngày chốt 18/09/2026.");
  const muc = [
    ["Inventory health dashboard", "Tab Sức khỏe tồn kho: giá trị và số dòng theo 6 tầng, danh sách lô xếp theo điểm rủi ro, chi tiết nguồn số của từng lô."],
    ["Aging and expiry alert", "Tầng Đã quá hạn và Cận date; hỏi hàng hết hạn bằng lời, mỗi vai thấy đúng phạm vi của mình; brief buổi sáng."],
    ["Stock-out risk", "Tầng Sắp hết hàng khi số ngày đủ bán dưới 7; hỏi tồn một món ở cửa hàng mình và nơi còn hàng."],
    ["Traceability view", "Truy xuất lô: nhập ở đâu, chuyển đi đâu, đã bán bao nhiêu, còn ở đâu, thu hồi lấy lại ở đâu."],
  ];
  const w = (RONG - 3 * 0.25) / 4;
  muc.forEach(([ten, mo], i) => {
    const x = LE + i * (w + 0.25);
    the(s, x, 1.55, w, 3.05, MAU.nen);
    vong(s, x + 0.25, 1.8, 0.5, String(i + 1));
    s.addText(ten, { x: x + 0.25, y: 2.45, w: w - 0.5, h: 0.75, fontFace: F, fontSize: 15, bold: true, color: MAU.graphite, margin: 0, valign: "top", isTextBox: true });
    s.addText(mo, { x: x + 0.25, y: 3.2, w: w - 0.5, h: 1.3, fontFace: F, fontSize: 13, color: MAU.graphite, margin: 0, valign: "top", isTextBox: true });
  });
  const so = [["167", "dòng kết quả theo mặt hàng, địa điểm, lô"], ["6", "tầng sức khỏe tồn kho"], ["5.088,4", "giá trị ở bốn tầng có vấn đề, 38,1% tồn kho"], ["6/6", "tầng khớp khi đối chiếu độc lập"]];
  so.forEach(([n, t], i) => {
    const x = LE + i * (w + 0.25);
    s.addText(n, { x, y: 4.95, w, h: 0.95, fontFace: FT, fontSize: 44, bold: true, color: i === 2 ? MAU.sand : MAU.aqua, margin: 0, valign: "bottom", isTextBox: true });
    s.addText(t, { x, y: 5.95, w: w - 0.1, h: 0.6, fontFace: F, fontSize: 12, color: MAU.xam, margin: 0, valign: "top", isTextBox: true });
  });
}

// ============================================================ 3. Kien truc
{
  const s = trangNoiDung("Kiến trúc giải pháp", "Ba tầng: người dùng, trợ lý NaviWorld, Business Central",
    "Đọc từ dưới lên. Business Central giữ dữ liệu, tính kết quả bằng AL và lưu đề xuất chờ duyệt. Trợ lý NaviWorld đọc kết quả qua API chỉ đọc, trả lời theo vai và chỉ ghi được đề xuất. Azure OpenAI chỉ được gọi khi câu hỏi chưa có mẫu, và không bao giờ ghi vào BC. Tắt trợ lý thì ba lớp trong BC vẫn chạy.");
  const bang = (y, h, nen, nhan) => {
    s.addShape(pres.shapes.ROUNDED_RECTANGLE, { x: LE, y, w: RONG, h, rectRadius: 0.1, fill: { color: nen }, line: { color: nen, width: 0 } });
    s.addText(nhan.toUpperCase(), { x: LE + 0.2, y: y + 0.08, w: 8, h: 0.28, fontFace: F, fontSize: 10, bold: true, color: MAU.xam, charSpacing: 2, margin: 0, isTextBox: true });
  };
  const hop = (x, y, w, h, ten, mo, vien = MAU.vien, dut = false) => {
    s.addShape(pres.shapes.ROUNDED_RECTANGLE, { x, y, w, h, rectRadius: 0.06, fill: { color: MAU.trang }, line: { color: vien, width: 1, dashType: dut ? "dash" : "solid" } });
    s.addText([{ text: ten, options: { bold: true, fontSize: 12, breakLine: true } }, { text: mo, options: { fontSize: 10, color: MAU.xam } }],
      { x: x + 0.1, y: y + 0.05, w: w - 0.2, h: h - 0.1, fontFace: F, color: MAU.graphite, valign: "top", margin: 2, paraSpaceAfter: 2, isTextBox: true });
  };
  const muiTen = (x, y1, y2, nhan, len = true) => {
    s.addShape(pres.shapes.LINE, { x, y: y1, w: 0, h: y2 - y1, line: { color: MAU.graphite, width: 1.25, beginArrowType: len ? "triangle" : undefined, endArrowType: "triangle" } });
    s.addText(nhan, { x: x + 0.1, y: y1 + (y2 - y1) / 2 - 0.14, w: 3.4, h: 0.28, fontFace: F, fontSize: 9.5, color: MAU.graphite, margin: 0, isTextBox: true });
  };

  // Tang 1: nguoi dung
  bang(1.45, 1.2, MAU.nen, "Người dùng và kênh vào");
  const w3 = (RONG - 0.4 - 2 * 0.2) / 3;
  hop(LE + 0.2, 1.8, w3, 0.75, "Web trợ lý theo vai", "Quản lý cửa hàng, điều phối, kho, Supply Chain: dashboard, hỏi đáp, duyệt trên thẻ");
  hop(LE + 0.2 + w3 + 0.2, 1.8, w3, 0.75, "Business Central", "Người duyệt mở đề xuất và Transfer Order; quản trị sửa ngưỡng");
  hop(LE + 0.2 + 2 * (w3 + 0.2), 1.8, w3, 0.75, "Cổng MCP", "Agent khác gọi cùng công cụ, cùng quy định phê duyệt");

  muiTen(3.0, 2.65, 3.0, "Hỏi đáp, bấm nút trên thẻ");
  muiTen(8.2, 2.65, 3.0, "Link mở đúng page và bộ lọc trong BC", false);

  // Tang 2: tro ly
  bang(3.0, 1.75, MAU.ice, "Trợ lý NaviWorld");
  const w5 = (RONG - 0.4 - 4 * 0.15) / 5;
  const tl = [
    ["Hiểu câu hỏi", "Quy tắc nhận dạng chạy trước; gọi model khi câu chưa có mẫu"],
    ["Skill UC2", "Sức khỏe tồn kho, hàng hết hạn, tồn cửa hàng, truy xuất lô, đề xuất"],
    ["Kiểm soát", "Quy định phê duyệt, chống đề xuất trùng, trần chi phí AI"],
    ["Kết nối BC", "OAuth S2S, đọc API chỉ đọc, ghi đề xuất, tạo link BC"],
  ];
  tl.forEach(([t, m], i) => hop(LE + 0.2 + i * (w5 + 0.15), 3.35, w5, 1.25, t, m));
  hop(LE + 0.2 + 4 * (w5 + 0.15), 3.35, w5, 1.25, "Azure OpenAI", "gpt-4.1-mini. Chỉ nhận kết quả đã lọc; không tính số, không ghi BC", MAU.sand, true);

  muiTen(3.0, 4.75, 5.1, "Đọc: API chỉ đọc (OData v4)", false);
  muiTen(8.2, 4.75, 5.1, "Ghi: chỉ đề xuất, trạng thái Proposed");

  // Tang 3: BC
  bang(5.1, 1.85, MAU.sandNen, "Business Central và LS Central");
  const lop = [
    ["Lớp 1 · Dữ liệu chuẩn", "Item Ledger Entry (lô, hạn dùng, bán, chuyển), Item, Location; ngưỡng trên NWV Agent Setup"],
    ["Lớp 2 · Tính toán bằng AL", "NWV Inv. Health Calc chạy bằng Job Queue hằng đêm, ghi bảng NWV Inv. Health Line"],
    ["Lớp 3 · Đề xuất và người duyệt", "NWV Agent Proposal chờ duyệt; duyệt chuyển hàng thì BC tạo Transfer Order"],
  ];
  const wl = (RONG - 0.4 - 2 * 0.45) / 3;
  lop.forEach(([t, m], i) => {
    const x = LE + 0.2 + i * (wl + 0.45);
    hop(x, 5.45, wl, 1.3, t, m, MAU.sand);
    if (i < 2) s.addShape(pres.shapes.LINE, { x: x + wl + 0.05, y: 6.1, w: 0.35, h: 0, line: { color: MAU.graphite, width: 1.25, endArrowType: "triangle" } });
  });
}

// ============================================================ 4. Ai lam gi
{
  const s = trangNoiDung("Phân vai", "Số do Business Central tính, AI chỉ tham gia ở hai chỗ",
    "Câu hỏi hay gặp: AI nằm ở đâu, sao hỏi mười lần ra cùng một câu. Câu hỏi quen thuộc được trợ lý nhận dạng bằng quy tắc và trả lời bằng số đọc từ BC, nên cùng dữ liệu thì cùng câu trả lời. Model chỉ được gọi cho câu hỏi chưa có mẫu và để viết lại lý do đề xuất. Mọi con số trong câu trả lời phải lấy từ kết quả đọc BC, code kiểm lại sau khi model trả lời.");
  const cot = [
    ["Business Central tính số", "Tồn theo lô, hạn dùng, bán bình quân ngày, phân tầng, điểm rủi ro. Chạy bằng AL, kết quả nằm trong bảng của BC, mở và đối chiếu được.", MAU.graphite],
    ["Trợ lý đọc và trả lời", "Nhận dạng câu hỏi quen thuộc bằng quy tắc, đọc bảng đã tính, trả lời trong phạm vi của vai. Cùng câu hỏi, cùng dữ liệu thì cùng câu trả lời.", MAU.aqua],
    ["AI ở hai chỗ", "Câu hỏi chưa có mẫu: model chọn dữ liệu cần đọc rồi trả lời, số phải lấy từ kết quả đọc. Viết lại lý do đề xuất, giữ nguyên số. Bật tắt được, có trần chi phí.", MAU.sand],
    ["Người Marou quyết định", "Trợ lý chỉ ghi đề xuất. Người duyệt bấm Duyệt hoặc Từ chối; chứng từ chỉ sinh ra khi được duyệt.", MAU.graphite],
  ];
  const w = (RONG - 3 * 0.25) / 4;
  cot.forEach(([t, m, c], i) => {
    const x = LE + i * (w + 0.25);
    the(s, x, 1.55, w, 4.1, i === 2 ? MAU.sandNen : MAU.nen);
    vong(s, x + 0.25, 1.85, 0.6, String(i + 1), c, MAU.trang, 16);
    s.addText(t, { x: x + 0.25, y: 2.65, w: w - 0.5, h: 0.8, fontFace: F, fontSize: 17, bold: true, color: MAU.graphite, margin: 0, valign: "top", isTextBox: true });
    s.addText(m, { x: x + 0.25, y: 3.45, w: w - 0.5, h: 2.1, fontFace: F, fontSize: 14, color: MAU.graphite, margin: 0, valign: "top", isTextBox: true });
  });
  s.addText("Tắt AI thì dashboard, số liệu, đề xuất và luồng duyệt vẫn chạy như cũ.",
    { shape: pres.shapes.ROUNDED_RECTANGLE, rectRadius: 0.08, x: LE, y: 5.95, w: RONG, h: 0.6, fill: { color: MAU.ice }, line: { color: MAU.ice, width: 0 },
      fontFace: F, fontSize: 14, bold: true, color: MAU.graphite, margin: [0, 16, 0, 16], valign: "middle", isTextBox: true });
}

// ============================================================ 5. Luong du lieu
{
  const s = trangNoiDung("Luồng dữ liệu UC2", "Từ sổ kho đến thẻ việc của từng vai",
    "Đầu vào là dữ liệu chuẩn của BC, không nhập tay thêm gì ngoài ngưỡng. Business Central tính hằng đêm bằng Job Queue, hoặc người dùng bấm Run Inventory Health trên page NWV Agent Setup. Kết quả là một bảng; mọi màn hình và câu trả lời phía sau chỉ đọc bảng đó.");
  const cot = [
    ["Đầu vào", ["Item Ledger Entry: tồn theo lô, hạn dùng, bán, xuất, chuyển", "Item, Location, Item Category", "Ngưỡng trên NWV Agent Setup: cận date 45 ngày, đủ bán dưới 7 ngày, trên 90 ngày, 60 ngày không bán"]],
    ["Xử lý trong BC", ["NWV Demand Calc: bán bình quân ngày theo mặt hàng và địa điểm, bỏ ngày hết hàng", "NWV Inv. Health Calc: gom tồn theo lô, xếp tầng, chấm điểm rủi ro", "Job Queue chạy hằng đêm"]],
    ["Đầu ra", ["Bảng NWV Inv. Health Line: mỗi dòng là mặt hàng, địa điểm, lô", "Tầng, điểm rủi ro 0 đến 100, số ngày đủ bán, hạn còn, giá trị, lý do"]],
    ["Người dùng nhận", ["Dashboard và chi tiết lô", "Brief buổi sáng, hỏi đáp theo vai", "Đề xuất xử lý, thẻ duyệt", "Truy xuất lô, link mở sổ kho trong BC"]],
  ];
  const w = (RONG - 3 * 0.45) / 4;
  cot.forEach(([t, ds], i) => {
    const x = LE + i * (w + 0.45);
    the(s, x, 1.55, w, 4.95, i === 2 ? MAU.ice : MAU.nen);
    vong(s, x + 0.2, 1.75, 0.45, String(i + 1), i === 2 ? MAU.graphite : MAU.aqua);
    s.addText(t, { x: x + 0.78, y: 1.75, w: w - 0.9, h: 0.45, fontFace: F, fontSize: 16, bold: true, color: MAU.graphite, margin: 0, valign: "middle", isTextBox: true });
    s.addText(dong(ds, 14), { x: x + 0.15, y: 2.4, w: w - 0.3, h: 4.0, valign: "top", margin: 2, isTextBox: true });
    if (i < 3) s.addShape(pres.shapes.CHEVRON, { x: x + w + 0.12, y: 3.8, w: 0.22, h: 0.4, fill: { color: MAU.aqua }, line: { color: MAU.aqua, width: 0 } });
  });
}

// ============================================================ 6. Phan tang
{
  const s = trangNoiDung("Quy tắc phân tầng", "Mỗi lô dừng ở tầng đầu tiên khớp điều kiện",
    "Cây phân tầng xét từ trên xuống, lô dừng ở bậc đầu tiên khớp. Ngưỡng Marou tự sửa trên NWV Agent Setup, có thể đặt riêng cận date theo nhóm hàng, không sửa code. Bốn tầng Đã quá hạn, Cận date, Chậm luân chuyển, Dư tồn cộng lại là 5.088,4. Số trên biểu đồ là dữ liệu demo ngày chốt 18/09/2026.");
  const tang = [
    ["Đã quá hạn", "Hạn còn dưới 0 ngày", "45", 1273.3, true],
    ["Cận date", "Hạn còn từ 0 đến 45 ngày", "32", 2099.7, true],
    ["Sắp hết hàng", "Có bán và đủ bán dưới 7 ngày", "47", 3818.2, false],
    ["Chậm luân chuyển", "Từ 60 ngày không bán, hoặc không có nhu cầu", "4", 46.6, true],
    ["Dư tồn", "Đủ bán trên 90 ngày", "1", 1668.8, true],
    ["Trong ngưỡng", "Còn lại", "38", 4463.6, false],
  ];
  const y0 = 1.55, hr = 0.8, wt = 6.3;
  tang.forEach(([ten, dk, n, , xau], i) => {
    const y = y0 + i * hr;
    the(s, LE, y, wt, hr - 0.1, xau ? MAU.sandNen : MAU.nen);
    vong(s, LE + 0.15, y + 0.15, 0.4, String(i + 1), xau ? MAU.sand : MAU.aqua);
    s.addText([{ text: ten, options: { bold: true, fontSize: 13, breakLine: true } }, { text: dk, options: { fontSize: 11, color: MAU.xam } }],
      { x: LE + 0.7, y: y + 0.04, w: 4.4, h: hr - 0.18, fontFace: F, color: MAU.graphite, valign: "middle", margin: 0, isTextBox: true });
    s.addText([{ text: n, options: { bold: true, fontSize: 18 } }, { text: " dòng", options: { fontSize: 11, color: MAU.xam, breakLine: true } },
      { text: tang[i][3].toLocaleString("vi-VN", { minimumFractionDigits: 1, maximumFractionDigits: 1 }), options: { fontSize: 11, color: MAU.xam } }],
      { x: LE + 4.7, y: y + 0.02, w: 1.45, h: hr - 0.14, fontFace: F, color: MAU.graphite, align: "right", valign: "middle", margin: 0, isTextBox: true });
  });
  const nhan = tang.map((t) => t[0]);
  s.addChart(pres.charts.BAR, [
    { name: "Tính vào 5.088,4", labels: nhan, values: tang.map((t) => (t[4] ? t[3] : 0)) },
    { name: "Tầng khác", labels: nhan, values: tang.map((t) => (t[4] ? 0 : t[3])) },
  ], {
    x: 7.2, y: 1.45, w: 5.55, h: 4.9, barDir: "bar", barGrouping: "stacked", catAxisOrientation: "maxMin",
    chartColors: [MAU.sand, MAU.aqua], showValue: false,
    showTitle: true, title: "Giá trị tồn theo tầng", titleFontFace: F, titleFontSize: 13, titleColor: MAU.graphite,
    showLegend: true, legendPos: "b", legendFontFace: F, legendFontSize: 10, legendColor: MAU.graphite,
    catAxisLabelColor: MAU.graphite, catAxisLabelFontFace: F, catAxisLabelFontSize: 11, valAxisHidden: true,
    valGridLine: { style: "none" }, catGridLine: { style: "none" },
  });
  s.addText("Điểm rủi ro 0 đến 100 để xếp thứ tự trong bảng: quá hạn 100; cận date từ 60, lô dự kiến bán hết trước hạn tối đa 65.",
    { x: 7.2, y: 6.4, w: 5.55, h: 0.5, fontFace: F, fontSize: 10, italic: true, color: MAU.xam, margin: 0, valign: "top", isTextBox: true });
}

// ============================================================ 7. Ban do kich ban
const KB = [
  ["Xem sức khỏe tồn kho", "Supply Chain", "Mở tab Sức khỏe tồn kho, bấm ô tầng, tìm theo mã hoặc lô", "Giá trị theo 6 tầng, lô xếp theo điểm rủi ro"],
  ["Vì sao lô vào tầng này", "Supply Chain, người kiểm tra số", "Bấm một dòng trên bảng", "Nguồn từng con số, quy tắc dừng ở bậc nào, bán theo ngày"],
  ["Dữ liệu có đủ để tin không", "Supply Chain, IT", "Bấm Độ phủ dữ liệu", "Tỷ lệ dòng có lô, hạn dùng, độ dài lịch sử; Đạt hoặc Cần xem lại"],
  ["Brief buổi sáng", "Supply Chain, điều phối", "Bấm Brief hoặc gõ brief", "Các lô rủi ro nhất, mỗi thẻ có nút xử lý"],
  ["Hỏi hàng hết hạn theo vai", "Điều phối, quản lý cửa hàng", "Gõ câu hỏi bằng lời", "Số lô, tồn, giá trị theo địa điểm; cửa hàng chỉ thấy của mình"],
  ["Hỏi tồn một món", "Quản lý cửa hàng", "Gõ tên món", "Cửa hàng mình trước, rồi nơi còn hàng và số ngày đủ bán"],
  ["Đề xuất xử lý lô", "Supply Chain", "Bấm Đề xuất hủy hoặc Chuyển sang cửa hàng bán nhanh", "Đề xuất có số lô ghi vào BC, trạng thái Proposed"],
  ["Duyệt đề xuất", "Người duyệt", "Bấm Duyệt hoặc Từ chối trên thẻ", "Quyết định ghi vào BC; duyệt chuyển hàng thì có Transfer Order"],
  ["Truy xuất lô", "QA, điều phối", "Gõ số lô", "Hành trình lô, nơi còn tồn, số thu hồi được"],
  ["Hỏi tự do khi bật AI", "Supply Chain, quản lý", "Gõ câu hỏi chưa có mẫu", "Câu trả lời kèm số và các bước đã tra"],
];
{
  const s = trangNoiDung("Kịch bản đáp ứng", "Mười kịch bản đang chạy trên môi trường demo",
    "Bản đồ mười kịch bản. Chín kịch bản đầu không cần bật AI. Kịch bản 7 và 8 chụp trên dữ liệu mô phỏng để không ghi đề xuất thật vào BC demo. Mỗi slide sau đi vào một kịch bản với đầu vào, thao tác và đầu ra.");
  const o = (t, opt = {}) => ({ text: t, options: { fontFace: F, fontSize: 10.5, color: MAU.graphite, valign: "middle", ...opt } });
  const hd = (t) => o(t, { bold: true, fill: { color: MAU.aqua }, fontSize: 11 });
  const rows = [[hd("#"), hd("Kịch bản"), hd("Vai"), hd("Người dùng làm gì"), hd("Nhận được")]];
  KB.forEach((k, i) => {
    const fill = { color: i % 2 ? MAU.nen : MAU.trang };
    rows.push([o(String(i + 1), { fill, bold: true, align: "center" }), o(k[0], { fill, bold: true }), o(k[1], { fill }), o(k[2], { fill }), o(k[3], { fill })]);
  });
  s.addTable(rows, { x: LE, y: 1.45, w: RONG, colW: [0.45, 2.55, 2.35, 3.35, 3.433], rowH: 0.46, border: { type: "solid", pt: 0.5, color: MAU.vien }, margin: [0.03, 0.08, 0.03, 0.08] });
}

// ============================================================ 8-17. Tung kich ban
function kichBan(i, tieuDe, vai, ghiChu) {
  const s = trangNoiDung(`Kịch bản ${i}/${TONG_KB} · ${KB[i - 1][0]}`, tieuDe, ghiChu);
  nhanVai(s, vai);
  return s;
}

// 1. Dashboard: khoi trai, anh phai
{
  const s = kichBan(1, "Tiền đang nằm ở hàng có vấn đề bao nhiêu", "Supply Chain",
    "Vai Trang (Supply Chain). Mở tab Sức khỏe tồn kho: con số lớn là giá trị ở bốn tầng có vấn đề. Bấm ô Đã quá hạn để lọc còn 45 dòng; gõ số lô vào ô tìm để lọc một lô. Dòng chốt ngày cho biết kết quả tính theo Work Date nào.");
  baKhoi(s, LE, 1.85, 5.3, [
    { dong: ["Bảng NWV Inv. Health Line do BC tính, 167 dòng, chốt ngày 18/09/2026", "Tồn theo lô, giá vốn, số ngày đủ bán"], cao: 1.55 },
    { dong: ["Mở tab Sức khỏe tồn kho", "Bấm một ô tầng để lọc; gõ mặt hàng, mã hoặc số lô để tìm"], cao: 1.55 },
    { dong: ["5.088,4 ở bốn tầng có vấn đề, 38,1% của 13.370,2", "Số dòng và giá trị của từng tầng", "Danh sách lô xếp theo điểm rủi ro, kèm lý do"], cao: 1.85 },
  ]);
  anh(s, "tong-quan", 6.25, 1.35, 6.48, 5.55, "phai");
}

// 2. Chi tiet lo: anh trai, khoi phai
{
  const s = kichBan(2, "Mở một lô để xem từng con số lấy từ đâu", "Supply Chain, người kiểm tra số liệu",
    "Bấm dòng Croissant - plain tại S0001, lô L260910-33100A. Bảng Nguồn số liệu ghi cách xác định từng chỉ tiêu. Quy tắc phân tầng tô đậm bậc 01 Expired là bậc khớp; các bậc sau ghi Không xét. Phần Đã bán theo ngày ở cuối trang để cộng tay đối chiếu.");
  anh(s, "chi-tiet-lo", LE, 1.85, 5.9, 5.05, "trai");
  baKhoi(s, 5.15, 1.85, 7.58, [
    { dong: ["Dòng kết quả của lô", "Item Ledger Entry của lô và lịch sử bán 90 ngày tại địa điểm"], cao: 1.5 },
    { dong: ["Bấm một dòng trên bảng Sức khỏe tồn kho", "Ví dụ: Croissant - plain, S0001, lô L260910-33100A"], cao: 1.5 },
    { dong: ["Nguồn từng con số: tồn 23, bán 90 ngày, số ngày hết hàng bị loại, số ngày đủ bán 2,9", "Quy tắc dừng ở bậc 01 Expired vì hạn còn -6 ngày", "Bán theo ngày để cộng tay"], cao: 2.05 },
  ]);
}

// 3. Do phu du lieu
{
  const s = kichBan(3, "Biết dữ liệu đủ tốt trước khi tin kết quả", "Supply Chain, IT",
    "Bấm Độ phủ dữ liệu trên thanh công cụ. Mỗi dòng là một phép đo trên BC và nói thiếu thì ảnh hưởng gì. Trên demo có hai dòng Cần xem lại: 68,9% dòng tồn có số lô vì chỉ 9 mã quản lý lô, và lịch sử bán 6 tháng nên chưa bắt được mùa Tết.");
  baKhoi(s, LE, 1.85, 5.3, [
    { dong: ["Item Ledger Entry, Lot No. Information, Item", "Bảng kết quả Inventory Health"], cao: 1.45 },
    { dong: ["Bấm Độ phủ dữ liệu trên màn hình Sức khỏe tồn kho"], cao: 1.2 },
    { dong: ["Từng phép đo: kết quả, tỷ lệ, kết luận Đạt hoặc Cần xem lại", "Thiếu thì ảnh hưởng gì, ví dụ lịch sử dưới 12 tháng chưa bắt được mùa Tết", "Demo: 100% dòng tồn có hạn dùng; 68,9% có số lô"], cao: 2.3 },
  ]);
  anh(s, "do-phu", 6.25, 1.35, 6.48, 5.55, "phai");
}

// 4. Brief
{
  const s = kichBan(4, "Mở đầu ngày bằng danh sách lô cần xử lý", "Supply Chain, điều phối",
    "Vai Trang bấm Brief. Trợ lý đọc bảng Inventory Health, lấy các dòng điểm rủi ro cao nhất và dựng thẻ. Mỗi thẻ có nút theo tầng: quá hạn thì Đề xuất hủy, cận date thì Đề xuất giảm giá và Chuyển sang cửa hàng bán nhanh. Link mở đúng Item Ledger Entry của lô trong BC. Brief hiện ghép bằng quy tắc, không gọi model.");
  anh(s, "brief", LE, 1.85, 5.0, 5.05, "trai");
  baKhoi(s, 5.3, 1.85, 7.43, [
    { dong: ["Bảng Inventory Health đã tính, điểm rủi ro của từng dòng", "Phạm vi của vai: Supply Chain thấy toàn hệ thống"], cao: 1.5 },
    { dong: ["Bấm Brief cạnh ô nhập, hoặc gõ brief"], cao: 1.2 },
    { dong: ["Số dòng cần xử lý, xếp theo mức rủi ro", "Mỗi thẻ: tầng, kho và lô, tồn, số ngày đủ bán, hạn dùng", "Nút xử lý theo tầng và link mở sổ kho của lô trong BC"], cao: 2.35 },
  ]);
}

// 5. Het han theo vai: hai anh
{
  const s = kichBan(5, "Cùng câu hỏi, mỗi vai thấy đúng phạm vi của mình", "Điều phối kho, quản lý cửa hàng S0010",
    "Hai câu hỏi trên hai vai. Hùng (điều phối) hỏi có mặt hàng nào đã hết hạn chưa: 45 lô ở mọi địa điểm, tổng tồn 704, giá trị 1.273,32, chia theo địa điểm. Hà (quản lý S0010) hỏi cửa hàng tôi có lô nào sắp hết hạn không: 6 lô, chỉ của S0010. Trợ lý không hỏi lại thuộc cửa hàng nào vì lấy từ vai.");
  baKhoi(s, LE, 1.85, 3.75, [
    { dong: ["Bảng Inventory Health", "Địa điểm gắn với vai người hỏi"], cao: 1.4 },
    { dong: ["Gõ: có mặt hàng nào đã hết hạn chưa", "Gõ: cửa hàng tôi có lô nào sắp hết hạn không"], cao: 1.65 },
    { dong: ["Điều phối: 45 lô, tồn 704, giá trị 1.273,32, chia theo địa điểm", "S0010: 6 lô, chỉ của S0010", "Thẻ các lô giá trị lớn nhất"], cao: 2.0 },
  ], 11);
  anh(s, "het-han-dieu-phoi", 4.6, 1.85, 3.95, 4.7, "giua", "Điều phối kho hỏi hàng đã hết hạn");
  anh(s, "sap-het-han-cua-hang", 8.78, 1.85, 3.95, 4.7, "giua", "Quản lý S0010 hỏi lô sắp hết hạn");
}

// 6. Ton mot mon: anh rong phia tren, ba khoi ngang
{
  const s = kichBan(6, "Hỏi tồn ở cửa hàng mình và nơi còn hàng", "Quản lý cửa hàng S0001",
    "Vai Lan (S0001) gõ Choco nuts ở cửa hàng tôi còn bao nhiêu. Trợ lý trả lời cửa hàng mình trước, kể cả khi đã hết, rồi liệt kê nơi còn hàng kèm số ngày đủ bán, để quản lý biết xin chuyển từ đâu.");
  anh(s, "ton-cua-hang", LE + 0.6, 1.95, RONG - 1.2, 2.6, "giua");
  const w = (RONG - 2 * 0.3) / 3;
  const k = [
    ["Đầu vào", ["Tồn theo mặt hàng và địa điểm", "Số ngày đủ bán từ bảng Inventory Health"]],
    ["Thao tác", ["Gõ: Choco nuts ở cửa hàng tôi còn bao nhiêu"]],
    ["Đầu ra", ["S0001 đã hết", "Nơi khác: S0002 415 (41,2 ngày), S0005 52, S0010 74, W0003 685"]],
  ];
  k.forEach(([t, ds], i) => {
    const x = LE + i * (w + 0.3);
    the(s, x, 4.9, w, 1.95, i === 2 ? MAU.ice : MAU.nen);
    vong(s, x + 0.15, 5.04, 0.36, String(i + 1), i === 2 ? MAU.graphite : MAU.aqua);
    s.addText(t, { x: x + 0.62, y: 5.02, w: w - 0.8, h: 0.4, fontFace: F, fontSize: 13, bold: true, color: MAU.graphite, margin: 0, valign: "middle", isTextBox: true });
    s.addText(dong(ds, 12), { x: x + 0.55, y: 5.45, w: w - 0.7, h: 1.3, valign: "top", margin: [0, 4, 0, 0], isTextBox: true });
  });
}

// 7. De xuat
{
  const s = kichBan(7, "Từ thẻ lô ra đề xuất có số lô trong Business Central", "Supply Chain",
    "Chụp trên dữ liệu mô phỏng. Bấm Đề xuất hủy trên thẻ Choco nuts S0002: trợ lý kiểm đề xuất trùng, áp quy định phê duyệt, ghi đề xuất WriteOff trạng thái Proposed vào BC và gửi thẻ cho người duyệt. Bấm Chuyển sang cửa hàng bán nhanh trên lô Carrot cake: trợ lý chọn S0001 vì bán 3 cái mỗi ngày. Hiện đề xuất chuyển ghi cả tồn lô; giới hạn theo lượng bán được trước hạn làm khi triển khai.");
  baKhoi(s, LE, 1.85, 5.3, [
    { dong: ["Thẻ lô từ brief hoặc câu trả lời", "Tốc độ bán theo cửa hàng, quy định phê duyệt, đề xuất đang chờ trong BC"], cao: 1.55 },
    { dong: ["Bấm Đề xuất hủy trên lô quá hạn", "Bấm Chuyển sang cửa hàng bán nhanh trên lô cận date"], cao: 1.5 },
    { dong: ["Đề xuất WriteOff hoặc Transfer có số lô, trạng thái Proposed", "Chọn cửa hàng bán nhanh nhất, ví dụ S0001 bán 3,0 mỗi ngày", "Bấm lần hai thì báo đã có đề xuất đang chờ"], cao: 2.0 },
  ]);
  anh(s, "de-xuat", 6.25, 1.85, 6.48, 4.6, "phai", "Dữ liệu mô phỏng");
}

// 8. Duyet
{
  const s = kichBan(8, "Người duyệt nhận thẻ và quyết định trong một lần bấm", "Người duyệt: Supply Chain, điều phối",
    "Chụp trên dữ liệu mô phỏng. Thẻ đến hộp thư người duyệt ngay khi đề xuất được ghi. Thẻ ghi người đề nghị và quy định áp dụng: hủy hàng ảnh hưởng sổ sách nên luôn cần người duyệt. Từ chối phải ghi lý do. Duyệt chuyển hàng thì BC tạo Transfer Order trạng thái Open. Duyệt hủy hiện ghi nhận quyết định; biên bản và chứng từ hủy nháp hoàn thiện khi triển khai.");
  anh(s, "the-duyet", LE, 1.85, 5.9, 4.85, "trai", "Dữ liệu mô phỏng");
  baKhoi(s, 7.0, 1.85, 5.73, [
    { dong: ["Đề xuất Proposed trong bảng NWV Agent Proposal", "Quy định phê duyệt khớp với loại đề xuất"], cao: 1.5 },
    { dong: ["Bấm Duyệt hủy hoặc Duyệt chuyển hàng", "Hoặc Từ chối, kèm lý do", "Có thể duyệt ngay trên page NWV Agent Proposals trong BC"], cao: 1.75 },
    { dong: ["Trạng thái đề xuất cập nhật trong BC", "Duyệt chuyển hàng: BC tạo Transfer Order trạng thái Open", "Link mở lô, dòng Inventory Health và page đề xuất"], cao: 1.8 },
  ]);
}

// 9. Truy xuat lo
{
  const s = kichBan(9, "Lô đi đâu, còn ở đâu, thu hồi lấy lại được bao nhiêu", "QA, điều phối kho",
    "Vai Hùng gõ truy xuất lô L260908-33170B. Trợ lý gom Item Ledger Entry của lô theo địa điểm: W0003 nhập mua 22 và xuất hết; S0001 nhận 14, bán 2, còn 12; S0002 nhận 8, bán 6, còn 2. Lô đã quá hạn từ 13/09 mà còn tồn nên trợ lý ghi rõ. Link mở đúng sổ kho và Lot No. Information của lô.");
  anh(s, "truy-xuat", LE, 1.85, 6.3, 4.9, "trai");
  baKhoi(s, 7.25, 1.85, 5.48, [
    { dong: ["Item Ledger Entry của lô: nhập, chuyển, bán", "Hạn dùng của lô"], cao: 1.4 },
    { dong: ["Gõ: truy xuất lô L260908-33170B"], cao: 1.15 },
    { dong: ["Hành trình theo địa điểm: W0003 nhập 22; S0001 nhận 14, còn 12; S0002 nhận 8, còn 2", "Thu hồi: lấy lại 12 tại S0001, 2 tại S0002; 8 cái đã bán", "Cảnh báo lô đã quá hạn từ 13/09 mà còn tồn"], cao: 2.5 },
  ]);
}

// 10. Hoi tu do (AI)
{
  const s = kichBan(10, "Câu hỏi chưa có mẫu: model chọn dữ liệu cần đọc", "Supply Chain",
    "Kịch bản duy nhất gọi model, khi bật AI trên trang Cài đặt AI. Câu hỏi so sánh tốc độ bán Flavored syrup giữa các cửa hàng 30 ngày qua không có mẫu sẵn. Model chọn đọc gì (8 bước tra cứu), trả lời kèm số lấy từ kết quả đọc. Nút Xem 8 bước tôi đã tra liệt kê từng bước bằng tiếng Việt. Code kiểm số trong câu trả lời theo đúng địa điểm; sai thì thẻ ghi Kiểm tra số. Người dùng đánh giá Trả lời đúng hoặc Chưa đúng.");
  baKhoi(s, LE, 1.85, 5.3, [
    { dong: ["API chỉ đọc: tồn, lô, lịch sử bán", "AI đang bật, còn trong trần chi phí"], cao: 1.45 },
    { dong: ["Gõ: so sánh tốc độ bán Flavored syrup giữa các cửa hàng 30 ngày qua, chỗ nào nên giữ ít hàng lại"], cao: 1.55 },
    { dong: ["Câu trả lời kèm số theo từng cửa hàng", "Kế hoạch đã tra: 8 bước, 6.700 token", "Nút xem các bước đã tra, đánh giá đúng hoặc chưa đúng"], cao: 2.0 },
  ]);
  anh(s, "cau-hoi-mo", 6.25, 1.85, 6.48, 5.0, "phai");
}

// ============================================================ 18. Kiem soat va kiem chung
{
  const s = trangNoiDung("Kiểm soát", "Mỗi con số mở lại được, mỗi quyết định có người duyệt",
    "Bốn cơ chế giúp Marou tin kết quả. Đối chiếu độc lập: một bản tính viết riêng bằng Python đọc cùng dữ liệu BC và ra đúng sáu tầng 45, 32, 47, 4, 1, 38. Link BC trên thẻ mở đúng page với bộ lọc mặt hàng, kho, lô. Trợ lý chỉ ghi đề xuất ở trạng thái Proposed. AI có công tắc và trần chi phí, mọi lượt gọi model ghi token.");
  const muc = [
    ["Đối chiếu độc lập", "Bản tính thứ hai đọc cùng dữ liệu BC, so từng tầng: 45 / 32 / 47 / 4 / 1 / 38, khớp cả sáu."],
    ["Mở lại trong Business Central", "Thẻ có link mở đúng Item Ledger Entries lọc sẵn mặt hàng, kho, lô; ngưỡng sửa trên NWV Agent Setup."],
    ["Chỉ ghi đề xuất", "Trạng thái luôn là Proposed; chống đề xuất trùng cho cùng lô; quy định phê duyệt theo loại và giá trị."],
    ["AI trong giới hạn", "Bật tắt trên trang Cài đặt AI, trần chi phí theo ngày và cộng dồn; mỗi lượt gọi model ghi số token."],
  ];
  const w = (RONG - 0.3) / 2, h = 2.35;
  muc.forEach(([t, m], i) => {
    const x = LE + (i % 2) * (w + 0.3), y = 1.55 + Math.floor(i / 2) * (h + 0.25);
    the(s, x, y, w, h, i === 0 ? MAU.ice : MAU.nen);
    vong(s, x + 0.3, y + 0.35, 0.6, String(i + 1), i === 0 ? MAU.graphite : MAU.aqua, MAU.trang, 16);
    s.addText(t, { x: x + 1.15, y: y + 0.32, w: w - 1.4, h: 0.65, fontFace: F, fontSize: 18, bold: true, color: MAU.graphite, margin: 0, valign: "middle", isTextBox: true });
    s.addText(m, { x: x + 1.15, y: y + 1.0, w: w - 1.4, h: 1.2, fontFace: F, fontSize: 15, color: MAU.graphite, margin: 0, valign: "top", isTextBox: true });
  });
}

// ============================================================ 19. Muc dap ung
{
  const s = trangNoiDung("Mức đáp ứng", "Đã chạy trong POC và phần hoàn thiện khi triển khai",
    "Cột trái là những gì đã chạy trên môi trường demo và vừa trình bày. Cột giữa là luồng đã có nhưng bước cuối cần theo quy trình thật của Marou. Cột phải là tính năng chưa có, sẽ chọn làm dựa trên khảo sát người dùng.");
  const cot = [
    ["Có trong POC", MAU.aqua, MAU.ice, ["Dashboard 6 tầng, lọc và tìm lô", "Chi tiết lô và nguồn số liệu", "Độ phủ dữ liệu", "Brief, hỏi hết hạn và tồn theo vai", "Đề xuất có số lô, chống trùng, thẻ duyệt", "Duyệt chuyển hàng tạo Transfer Order", "Truy xuất lô, link mở sổ kho trong BC", "Hỏi tự do khi bật AI"]],
    ["Hoàn thiện khi triển khai", MAU.sand, MAU.sandNen, ["Duyệt hủy sinh biên bản và chứng từ hủy nháp; hiện ghi nhận quyết định", "Số lượng chuyển vừa đủ bán trước hạn; hiện đề xuất cả tồn lô", "Chặn mua thêm hàng dư tồn; hiện ghi nhận quyết định", "Brief do AI viết, nêu ba việc quan trọng nhất và lý do"]],
    ["Chưa có, chọn qua khảo sát", MAU.graphite, MAU.nen, ["Nhắc chủ động mỗi sáng qua kênh người dùng quen dùng", "Đề xuất giảm giá có mức giảm", "Truy ngược lô nguyên liệu tới thành phẩm", "Gợi ý xuất lô theo hạn dùng"]],
  ];
  const w = (RONG - 2 * 0.3) / 3;
  cot.forEach(([t, c, nen, ds], i) => {
    const x = LE + i * (w + 0.3);
    the(s, x, 1.55, w, 5.3, nen);
    s.addText(t, { shape: pres.shapes.ROUNDED_RECTANGLE, rectRadius: 0.08, x: x + 0.2, y: 1.75, w: w - 0.4, h: 0.55, fill: { color: c }, line: { color: c, width: 0 },
      fontFace: F, fontSize: 14, bold: true, color: MAU.trang, align: "center", valign: "middle", margin: 0, isTextBox: true });
    s.addText(dong(ds, 14), { x: x + 0.2, y: 2.5, w: w - 0.4, h: 4.2, valign: "top", margin: [0, 4, 0, 0], paraSpaceAfter: 6, isTextBox: true });
  });
}

// ============================================================ 20. Buoc tiep theo
{
  const s = pres.addSlide();
  soTrang++;
  s.background = { color: MAU.graphite };
  s.addText("BƯỚC TIẾP THEO", { x: LE, y: 0.9, w: 8, h: 0.35, fontFace: F, fontSize: 12, bold: true, color: MAU.aqua, charSpacing: 3, margin: 0, isTextBox: true });
  s.addText("Đưa UC2 về sát việc thật của Marou", { x: LE, y: 1.3, w: RONG, h: 0.9, fontFace: FT, fontSize: 34, bold: true, color: MAU.trang, margin: 0, isTextBox: true });
  const buoc = [
    ["Khảo sát người dùng", "Tám câu hỏi về lần hủy hàng gần nhất, cách xử lý hàng cận date, thu hồi lô, để chọn tính năng AI làm trước."],
    ["Xác nhận dữ liệu", "Hàng tươi thừa cuối ngày có ghi hủy vào BC không; hạn dùng của từng đợt giao có được ghi ở phía cửa hàng không."],
    ["Chốt quy định phê duyệt", "Việc gì hệ thống được tự làm, việc gì luôn cần người duyệt, hạn mức giá trị bao nhiêu."],
  ];
  const w = (RONG - 2 * 0.35) / 3;
  buoc.forEach(([t, m], i) => {
    const x = LE + i * (w + 0.35);
    s.addShape(pres.shapes.ROUNDED_RECTANGLE, { x, y: 2.75, w, h: 3.4, rectRadius: 0.1, fill: { color: "34454C" }, line: { color: "34454C", width: 0 } });
    vong(s, x + 0.3, 3.05, 0.65, String(i + 1), MAU.aqua, MAU.graphite, 18);
    s.addText(t, { x: x + 0.3, y: 3.95, w: w - 0.6, h: 0.55, fontFace: F, fontSize: 18, bold: true, color: MAU.trang, margin: 0, valign: "top", isTextBox: true });
    s.addText(m, { x: x + 0.3, y: 4.55, w: w - 0.6, h: 1.5, fontFace: F, fontSize: 13, color: "D5DEE1", margin: 0, valign: "top", isTextBox: true });
  });
  s.addNotes("Ba việc cần Marou tham gia để chuyển UC2 từ demo sang dữ liệu thật: khảo sát người dùng, xác nhận hai điểm dữ liệu, và chốt quy định phê duyệt.");
}

pres.writeFile({ fileName: RA }).then((f) => console.log("wrote", f));
