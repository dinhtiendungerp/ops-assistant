// Chup anh cho slide kich ban 17/09 tu HOP THU DANG CO tren may chu tro ly (BC that), khong gui cau moi, khong ghi BC.
// Chay sau tools/qa_kich_ban_17_09.py (cac cau tra loi nam san trong hop thu). Anh ra docs/anh-uc2/ tien to kb17-.
//   node tools/chup_kich_ban_17_09.mjs
import { spawn } from "node:child_process";
import fs from "node:fs";
import os from "node:os";
import path from "node:path";
import { fileURLToPath } from "node:url";

const ROOT = path.resolve(path.dirname(fileURLToPath(import.meta.url)), "..");
const OUT = path.join(ROOT, "docs", "anh-uc2");
const APP = "http://127.0.0.1:8188";
const CHROME = "C:/Program Files/Google/Chrome/Application/chrome.exe";
const PORT = 9337;
fs.mkdirSync(OUT, { recursive: true });

const ngu = (ms) => new Promise((r) => setTimeout(r, ms));
const profile = fs.mkdtempSync(path.join(os.tmpdir(), "marou-kb17-"));
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
async function choDen(expr, ms = 120000) {
  const het = Date.now() + ms;
  while (Date.now() < het) { if (await js(expr)) return; await ngu(400); }
  throw new Error("het gio cho: " + expr);
}
async function khung(cao) {
  await goi("Emulation.setDeviceMetricsOverride", { width: 1440, height: cao, deviceScaleFactor: 2, mobile: false });
  await ngu(700);
}
async function chup(ten, selector, pad = 8, moChiTiet = false) {
  await khung(3600);
  try {
    const ok = await js(`(() => { const e = ${selector}; if (!e) return false;
      ${moChiTiet ? "e.querySelectorAll('details').forEach(d => d.open = true);" : ""}
      e.scrollIntoView({block:'start'}); return true; })()`);
    if (!ok) { console.log("KHONG THAY", ten); return; }
    await ngu(500);
    const b = await js(`(() => { const r = (${selector}).getBoundingClientRect(); return {x: r.x, y: r.y, w: r.width, h: r.height}; })()`);
    const r = await goi("Page.captureScreenshot", { format: "png", clip: { x: Math.max(0, b.x - pad), y: Math.max(0, b.y - pad),
      width: b.w + 2 * pad, height: Math.min(b.h + 2 * pad, 3400), scale: 1 } });
    fs.writeFileSync(path.join(OUT, ten + ".png"), Buffer.from(r.data, "base64"));
    console.log("chup", ten);
  } finally { await khung(900); }
}
async function vai(user, ct) {
  await js(`nhoCongTy(${JSON.stringify(user)}, ${JSON.stringify(ct)})`);
  // Cung nguoi dung ma doi company thi switchUser khong lam gi; phai goi doiCongTy.
  if (await js(`me === ${JSON.stringify(user)}`)) await js(`doiCongTy(${JSON.stringify(ct)})`);
  else await js(`switchUser(${JSON.stringify(user)})`);
  await ngu(600);
  await choDen("daTaiHopThu === true");
  await choDen(`congTy === ${JSON.stringify(ct)} && me === ${JSON.stringify(user)}`, 60000);
  await ngu(2500);
  await choDen("daTaiHopThu === true");
  console.log("vai", user, ct, await js("document.querySelectorAll('#chat .msg').length"));
}
// Tin cuoi cung (tin cua tro ly) co chua chu nay.
const TIN = (chu) => `[...document.querySelectorAll('#chat .msg.out')].filter(m => m.innerText.includes(${JSON.stringify(chu)})).pop()`;

async function main() {
  await ketNoi();
  await goi("Page.enable"); await goi("Runtime.enable");
  await khung(900);
  await goi("Page.navigate", { url: APP });
  await choDen("typeof switchUser === 'function' && typeof users !== 'undefined' && users.length > 0", 90000);

  const CHI = process.argv.slice(2);
  if (!CHI.includes("dakao")) {
  await vai("trang.sc", "NWV-MAROU");
  await chup("kb17-02-brief-ai", TIN("việc quan trọng nhất"));
  await chup("kb17-04-phuong-an-chat", TIN("Phương án cho lô cận date"));
  await chup("kb17-04b-email-nguoi-duyet", TIN("Email cho người duyệt"));
  await chup("kb17-08-truy-xuat", TIN("Hành trình lô L260906-33323C"));

  await vai("hung.dieuphoi", "NWV-MAROU");
  await chup("kb17-05-duyet-chuyen", TIN("Transfer Order HO1039"));
  }

  await vai("trang.sc", "NWV-DAKAO");
  await chup("kb17-06-cham-luan-chuyen", TIN("chậm luân chuyển tại các cửa hàng"));
  await chup("kb17-07-ctkm-hang-cham", TIN("không áp dụng cho mặt hàng này"));
  await chup("kb17-09-bat-thuong", TIN("tín hiệu bất thường trong 28 ngày"));
  await chup("kb17-11-vi-sao-ls", TIN("Vì sao LS đề xuất 12 Ice cream"));
  await chup("kb17-13-de-xuat-bat-thuong", TIN("đề xuất bổ sung bất thường"));
  await chup("kb17-14-du-bao", TIN("Dự báo Choco bowl tại S0010"));
  await chup("kb17-15-ctkm", TIN("Chương trình khuyến mãi"));

  await vai("minh.s0002", "NWV-DAKAO");
  await chup("kb17-10-minh-ice-cream", TIN("đề xuất đặt mua 12 từ MAROU"));
  await chup("kb17-19-minh-nhan-tin", TIN("HO106205"));

  await vai("hung.dieuphoi", "NWV-DAKAO");
  await chup("kb17-12-duyet-dat-mua", TIN("Purchase Order HO106205"));
  await chup("kb17-16-kiem-hang", TIN("đã xuất kho đơn HO106202"));
}

main().then(() => { chrome.kill(); process.exit(0); }).catch((e) => { console.error(e); chrome.kill(); process.exit(1); });
