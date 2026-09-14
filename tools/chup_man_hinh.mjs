// Chup man hinh tro ly theo kich ban demo POC A+D, dung Chrome headless qua DevTools Protocol.
// Anh ra docs/anh-demo/. Can server tro ly dang chay o :8188 (nguon du lieu theo .env).
//   node tools/chup_man_hinh.mjs            # chup het
//   node tools/chup_man_hinh.mjs 04 05      # chi chup cac anh co tien to do
// Buoc 13 bat AI tren server (vai quan tri) de chup cau tra loi cua planner, chup xong tat lai.
import { spawn } from "node:child_process";
import fs from "node:fs";
import os from "node:os";
import path from "node:path";
import { fileURLToPath } from "node:url";

const ROOT = path.resolve(path.dirname(fileURLToPath(import.meta.url)), "..");
const OUT = path.join(ROOT, "docs", "anh-demo");
const APP = "http://127.0.0.1:8188";
const CHROME = "C:/Program Files/Google/Chrome/Application/chrome.exe";
const PORT = 9333;
const CHI = process.argv.slice(2);
fs.mkdirSync(OUT, { recursive: true });

const ngu = (ms) => new Promise((r) => setTimeout(r, ms));
const profile = fs.mkdtempSync(path.join(os.tmpdir(), "marou-shot-"));
const chrome = spawn(CHROME, ["--headless=new", `--remote-debugging-port=${PORT}`, `--user-data-dir=${profile}`,
  "--hide-scrollbars", "--window-size=1440,900", "about:blank"], { stdio: "ignore" });

let ws, id = 0;
const cho = new Map();
async function ketNoi() {
  for (let i = 0; i < 50; i++) {
    try {
      const tabs = await (await fetch(`http://127.0.0.1:${PORT}/json`)).json();
      const t = tabs.find((x) => x.type === "page");
      if (t) {
        ws = new WebSocket(t.webSocketDebuggerUrl);
        await new Promise((r, j) => { ws.onopen = r; ws.onerror = j; });
        ws.onmessage = (e) => { const m = JSON.parse(e.data); if (m.id && cho.has(m.id)) { cho.get(m.id)(m); cho.delete(m.id); } };
        return;
      }
    } catch { /* chrome chua len */ }
    await ngu(200);
  }
  throw new Error("khong ket noi duoc Chrome");
}
function goi(method, params = {}) {
  return new Promise((r, j) => {
    const n = ++id;
    cho.set(n, (m) => (m.error ? j(new Error(`${method}: ${m.error.message}`)) : r(m.result)));
    ws.send(JSON.stringify({ id: n, method, params }));
  });
}
async function js(expr) {
  const r = await goi("Runtime.evaluate", { expression: expr, awaitPromise: true, returnByValue: true });
  if (r.exceptionDetails) throw new Error(`JS loi: ${r.exceptionDetails.exception?.description || r.exceptionDetails.text}\n${expr}`);
  return r.result.value;
}
async function choDen(expr, ms = 90000) {
  const het = Date.now() + ms;
  while (Date.now() < het) { if (await js(expr)) return; await ngu(400); }
  throw new Error("het gio cho: " + expr);
}
async function khung(cao) {
  await goi("Emulation.setDeviceMetricsOverride", { width: 1440, height: cao, deviceScaleFactor: 2, mobile: false });
  await ngu(700);
}
// Hoi thoai la vung cuon rieng nen the dai hon man hinh bi o nhap che. Chup phan tu thi keo cao khung nhin
// cho vua phan tu roi moi cat; chup ca man hinh thi dung `cao` (mac dinh 900).
async function chup(ten, selector = null, cao = null, pad = 8) {
  if (CHI.length && !CHI.some((c) => ten.startsWith(c))) return;
  await khung(cao || (selector ? 3400 : 900));
  try { await chupThat(ten, selector, pad); } finally { await khung(900); }
}
async function chupThat(ten, selector, pad) {
  let params = { format: "png", captureBeyondViewport: false };
  if (selector) {
    const box = await js(`(() => { const e = ${selector}; if (!e) return null; e.scrollIntoView({block:'start'});
      const r = e.getBoundingClientRect(); return {x: r.x + scrollX, y: r.y + scrollY, w: r.width, h: r.height}; })()`);
    if (!box) throw new Error("khong thay phan tu cho " + ten);
    await ngu(300);
    const b2 = await js(`(() => { const r = (${selector}).getBoundingClientRect(); return {x: r.x, y: r.y, w: r.width, h: r.height}; })()`);
    params.clip = { x: Math.max(0, b2.x - pad), y: Math.max(0, b2.y - pad), width: b2.w + 2 * pad, height: b2.h + 2 * pad, scale: 1 };
  }
  const r = await goi("Page.captureScreenshot", params);
  fs.writeFileSync(path.join(OUT, ten + ".png"), Buffer.from(r.data, "base64"));
  console.log("chup", ten);
}
const api = (duong, body) => js(`fetch('${duong}', {method:'POST', headers:{'content-type':'application/json'}, body: ${JSON.stringify(JSON.stringify(body))}}).then(r => r.json())`);

async function vaiMoi(user) {
  // Doan chat moi cho moi canh, de anh khong lan tin cua lan thu truoc.
  await api("/api/doan-chat", { user });
  await js(`switchUser(${JSON.stringify(user)})`);
  await choDen("daTaiHopThu === true");
  await ngu(800);
}
async function hoi(user, cau) {
  await vaiMoi(user);
  await js(`(async () => { $('#text').value = ${JSON.stringify(cau)}; await send(); })()`);
  await choDen("!document.querySelector('#dangxuly') && !document.querySelector('.msg.tam')");
  await ngu(1200);
}
const TIN_CUOI = "[...document.querySelectorAll('#chat .msg.out')].pop()";
const HOI_THOAI = "document.querySelector('#chat')";

async function main() {
  await ketNoi();
  await goi("Page.enable"); await goi("Runtime.enable");
  await goi("Emulation.setDeviceMetricsOverride", { width: 1440, height: 900, deviceScaleFactor: 2, mobile: false });
  await goi("Page.navigate", { url: APP });
  await choDen("typeof switchUser === 'function' && typeof users !== 'undefined' && users.length > 0", 60000);
  await choDen("typeof bcInfo !== 'undefined' && bcInfo && bcInfo.live", 120000);

  // Man hinh chao theo vai tro: prompt mau lay tu /api/goi-y
  const choGoiY = "document.querySelectorAll('#hero .goi').length === 4 && !!goiY[me]";
  await vaiMoi("trang.sc");
  await choDen(choGoiY);
  await ngu(800);
  await chup("01-man-hinh-chao");
  await vaiMoi("ha.s0010");
  await choDen(choGoiY);
  await ngu(800);
  await chup("01b-chao-quan-ly-cua-hang", "document.querySelector('#hero')");
  await vaiMoi("hung.dieuphoi");
  await choDen(choGoiY);
  await ngu(800);
  await chup("01c-chao-dieu-phoi", "document.querySelector('#hero')");

  // Man 1. Du bao (UC1)
  await hoi("trang.sc", "độ chính xác dự báo thế nào");
  await chup("02-du-bao-tra-loi", TIN_CUOI);
  await js("showTab('uc1')");
  await choDen("document.querySelectorAll('#uc1 tr.row').length > 0");
  await js("chonDuBao('33341','S0010','HW')");
  await ngu(3000);
  await chup("03-tab-du-bao", null, 1500);
  await hoi("trang.sc", "dự báo Choco bowl ở S0010 sai bao nhiêu");
  await chup("03b-du-bao-choco-bowl", TIN_CUOI);

  // Man 2. Vi sao LS de xuat (UC5)
  await hoi("trang.sc", "vì sao LS đề xuất Choco nuts cho S0001");
  await chup("04-ls-choco-nuts", TIN_CUOI);
  await hoi("trang.sc", "vì sao LS đề xuất Ice cream cho S0002");
  await chup("05-ls-ice-cream-min-max", TIN_CUOI);
  await hoi("trang.sc", "vì sao LS đề xuất Choco bowl cho S0010");
  await chup("05b-ls-choco-bowl-retail-forecast", TIN_CUOI);

  // CTKM cua LS va goc nhin quan ly cua hang
  await hoi("trang.sc", "CTKM nào đang chạy và sắp tới");
  await chup("16-ctkm", TIN_CUOI);
  await hoi("ha.s0010", "CTKM nào sắp tới ở cửa hàng tôi");
  await chup("16b-ctkm-cua-hang", TIN_CUOI);
  await hoi("lan.s0001", "Choco nuts ở cửa hàng tôi còn bao nhiêu");
  await chup("17-ton-cua-hang", HOI_THOAI);
  await vaiMoi("ha.s0010");
  await js("brief()");
  await ngu(1500);
  await choDen("!document.querySelector('#dangxuly')", 180000);
  await ngu(2000);
  await chup("18-brief-cua-hang", HOI_THOAI);

  // Man 3. Suc khoe ton kho va truy xuat lo (UC2)
  await js("showTab('uc2')");
  await choDen("document.querySelectorAll('#uc2 tr.row').length > 0");
  await ngu(1500);
  await chup("06-tab-suc-khoe-ton-kho", null, 1300);
  await js("(async () => { const rows = await (await fetch('/api/uc2/lines?tier=NearExpiry')).json(); if (rows.length) await openTrace(rows[0].id); })()");
  await ngu(3000);
  await chup("07-chi-tiet-lo", null, 1600);
  await hoi("hung.dieuphoi", "có mặt hàng nào đã hết hạn chưa");
  await chup("08-hang-het-han", HOI_THOAI);
  await hoi("hung.dieuphoi", "truy xuất lô L260908-33170B");
  await chup("09-truy-xuat-lo", TIN_CUOI);

  // Man 4. Nha cung cap (UC3)
  await js("showTab('uc3')");
  await ngu(4000);
  await chup("10-tab-nha-cung-cap", null, 1300);
  await hoi("trang.sc", "nhà cung cấp nào hay giao trễ");
  await chup("11-nha-cung-cap-tra-loi", HOI_THOAI);

  // Man 5. De xuat va nguoi duyet
  await vaiMoi("hung.dieuphoi");
  await js("brief()");
  await ngu(1500);
  await choDen("!document.querySelector('#dangxuly')", 180000);
  await ngu(2000);
  await chup("12-brief-dieu-phoi", "document.querySelector('#chat .msg.out')");
  await chup("12b-the-de-xuat", "[...document.querySelectorAll('#chat .card.prop')].find(c => c.textContent.includes('Ice cream')) || document.querySelector('#chat .card.prop')");

  // Man 6. Cau ngoai kich ban, bat AI tam thoi
  if (!CHI.length || CHI.some((c) => "13".startsWith(c) || c.startsWith("13"))) {
    const bat = await api("/api/ai", { user: "dung.admin", on: true });
    console.log("bat AI", bat.loi || "ok");
    try {
      await hoi("trang.sc", "so sánh tốc độ bán Flavored syrup giữa các cửa hàng 30 ngày qua, chỗ nào nên giữ ít hàng lại");
      await chup("13-cau-hoi-mo-model", TIN_CUOI);
    } finally {
      await api("/api/ai", { user: "dung.admin", on: false });
      console.log("tat AI");
    }
  }

  // Man 7. Quan tri
  await vaiMoi("dung.admin");
  await js("showTab('nhatky')");
  await ngu(3500);
  await chup("14-nhat-ky-agent", null, 1500);
  await js("showTab('caidat')");
  await ngu(3500);
  await chup("15-cai-dat-ai", null, 1500);
}

main().catch((e) => { console.error(e); process.exitCode = 1; }).finally(() => { try { ws?.close(); } catch {} chrome.kill(); });
