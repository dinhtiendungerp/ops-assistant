// Chup man hinh rieng cho tai lieu UC2 (Inventory Health & Traceability), Chrome headless qua DevTools Protocol.
// Anh ra docs/anh-uc2/. Can server tro ly dang chay o :8188, nguon .env tro vao BC that.
//   node tools/chup_uc2.mjs            # chup het
//   node tools/chup_uc2.mjs uc2-10     # chi chup anh co tien to do
// Anh 01-09 doc BC that, KHONG ghi gi. Anh 10-12 bam nut de xuat, nen tam doi nguon sang du lieu mo phong de khong ghi
// de xuat that vao BC; chup xong tra nguon ve theo .env.
import { spawn } from "node:child_process";
import fs from "node:fs";
import os from "node:os";
import path from "node:path";
import { fileURLToPath } from "node:url";

const ROOT = path.resolve(path.dirname(fileURLToPath(import.meta.url)), "..");
const OUT = path.join(ROOT, "docs", "anh-uc2");
const APP = "http://127.0.0.1:8188";
const CHROME = "C:/Program Files/Google/Chrome/Application/chrome.exe";
const PORT = 9334;
const CHI = process.argv.slice(2);
fs.mkdirSync(OUT, { recursive: true });

const ngu = (ms) => new Promise((r) => setTimeout(r, ms));
const profile = fs.mkdtempSync(path.join(os.tmpdir(), "marou-uc2-"));
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
const lam = (ten) => !CHI.length || CHI.some((c) => ten.startsWith(c));
async function chup(ten, selector = null, cao = null, pad = 8) {
  if (!lam(ten)) return;
  await khung(cao || (selector ? 3400 : 900));
  try {
    const params = { format: "png", captureBeyondViewport: false };
    if (selector) {
      const ok = await js(`(() => { const e = ${selector}; if (!e) return false; e.scrollIntoView({block:'start'}); return true; })()`);
      if (!ok) throw new Error("khong thay phan tu cho " + ten);
      await ngu(300);
      const b = await js(`(() => { const r = (${selector}).getBoundingClientRect(); return {x: r.x, y: r.y, w: r.width, h: r.height}; })()`);
      params.clip = { x: Math.max(0, b.x - pad), y: Math.max(0, b.y - pad), width: b.w + 2 * pad, height: b.h + 2 * pad, scale: 1 };
    }
    const r = await goi("Page.captureScreenshot", params);
    fs.writeFileSync(path.join(OUT, ten + ".png"), Buffer.from(r.data, "base64"));
    console.log("chup", ten);
  } finally { await khung(900); }
}
const api = (duong, body) => js(`fetch('${duong}', {method:'POST', headers:{'content-type':'application/json'}, body: ${JSON.stringify(JSON.stringify(body))}}).then(r => r.json())`);
const lay = (duong) => js(`fetch('${duong}').then(r => r.json())`);

async function vaiMoi(user) {
  await api("/api/doan-chat", { user });           // doan chat moi, anh khong lan tin cu
  await js(`switchUser(${JSON.stringify(user)})`);
  await choDen("daTaiHopThu === true");
  await ngu(800);
}
async function hoi(user, cau) {
  await vaiMoi(user);
  await js(`(async () => { $('#text').value = ${JSON.stringify(cau)}; await send(); })()`);
  await choDen("!document.querySelector('#dangxuly') && !document.querySelector('.msg.tam')");
  await ngu(1500);
}
async function choTab(ma) {
  await js(`showTab('${ma}')`);
  await choDen(`document.querySelectorAll('#${ma} tr.row').length > 0`);
  await ngu(1200);
}
const TIN_CUOI = "[...document.querySelectorAll('#chat .msg.out')].pop()";
const HOI_THOAI = "document.querySelector('#chat')";

async function main() {
  await ketNoi();
  await goi("Page.enable"); await goi("Runtime.enable");
  await khung(900);
  await goi("Page.navigate", { url: APP });
  await choDen("typeof switchUser === 'function' && typeof users !== 'undefined' && users.length > 0", 60000);
  await choDen("typeof bcInfo !== 'undefined' && bcInfo && bcInfo.live", 120000);

  // ---- Man hinh Suc khoe ton kho, doc BC that
  await vaiMoi("trang.sc");
  await choTab("uc2");
  await chup("uc2-01-tong-quan", null, 1300);
  await js("selTier('Expired')");
  await ngu(2500);
  await chup("uc2-02-tang-qua-han", null, 1300);
  if (lam("uc2-03")) {
    await js("(async () => { const rows = await (await fetch('/api/uc2/lines?tier=Expired')).json(); if (rows.length) await openTrace(rows[0].id); })()");
    await ngu(3500);
    await chup("uc2-03-chi-tiet-lo", null, 1700);
  }
  if (lam("uc2-04")) {
    await js("selTier('')");
    await ngu(1500);
    await js("loadReadiness()");
    await choDen("uc2Mode === 'readiness'", 120000);
    await ngu(1500);
    await chup("uc2-04-do-phu-du-lieu", null, 1500);
  }

  // ---- Tro chuyen, doc BC that
  if (lam("uc2-05")) {
    await vaiMoi("trang.sc");
    await js("brief()");                               // brief Supply Chain chi doc, khong ghi de xuat
    await ngu(1500);
    await choDen("!document.querySelector('#dangxuly')", 180000);
    await ngu(2000);
    await chup("uc2-05-brief-supply-chain", HOI_THOAI);
  }
  if (lam("uc2-06")) { await hoi("hung.dieuphoi", "có mặt hàng nào đã hết hạn chưa"); await chup("uc2-06-het-han-dieu-phoi", HOI_THOAI); }
  if (lam("uc2-07")) { await hoi("ha.s0010", "cửa hàng tôi có lô nào sắp hết hạn không"); await chup("uc2-07-sap-het-han-cua-hang", HOI_THOAI); }
  if (lam("uc2-08")) { await hoi("hung.dieuphoi", "truy xuất lô L260908-33170B"); await chup("uc2-08-truy-xuat-lo", TIN_CUOI); }
  if (lam("uc2-09")) { await hoi("lan.s0001", "Choco nuts ở cửa hàng tôi còn bao nhiêu"); await chup("uc2-09-ton-cua-hang", HOI_THOAI, null); }

  // ---- Luong de xuat va nguoi duyet: du lieu mo phong de khong ghi vao BC
  if (lam("uc2-10") || lam("uc2-11") || lam("uc2-12")) {
    const doi = await api("/api/mode", { bc: "mock" });
    console.log("nguon mo phong", doi.loi || "ok");
    try {
      await goi("Page.reload");
      await choDen("typeof switchUser === 'function' && typeof users !== 'undefined' && users.length > 0", 60000);
      await choDen("typeof bcInfo !== 'undefined' && bcInfo && !bcInfo.live", 60000);
      await js("switchUser('hung.dieuphoi')");        // dat doan chat cua nguoi duyet truoc khi the den
      await choDen("daTaiHopThu === true");
      await api("/api/doan-chat", { user: "hung.dieuphoi" });
      await vaiMoi("trang.sc");
      const hetHan = await lay("/api/uc2/lines?tier=Expired");
      await api("/api/action", { user: "trang.sc", verb: "ih_propose", ref: hetHan[0].id, payload: { action_type: "WriteOff" } });
      const canDate = await lay("/api/uc2/lines?tier=NearExpiry");
      const loChuyen = canDate.find((r) => r.daysToExpiry >= 3 && r.locationCode !== "W0003") || canDate[0];
      await api("/api/action", { user: "trang.sc", verb: "ih_transfer_fast", ref: loChuyen.id, payload: {} });
      await js("poll()");
      await ngu(2500);
      await chup("uc2-10-de-xuat-huy-va-chuyen", HOI_THOAI);
      await js("switchUser('hung.dieuphoi')");
      await choDen("daTaiHopThu === true");
      await ngu(2500);
      await chup("uc2-11-the-duyet-nguoi-duyet", HOI_THOAI);
      await js("showTab('uc2')");
      await ngu(3000);
      await chup("uc2-12-tong-quan-mo-phong", null, 900);
    } finally {
      const ve = await api("/api/mode", { bc: "env" });
      console.log("tra nguon ve .env", ve.loi || "ok");
    }
  }
}

main().catch((e) => { console.error(e); process.exitCode = 1; }).finally(() => { try { ws?.close(); } catch {} chrome.kill(); });
