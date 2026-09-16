// Chup man hinh cac tinh nang AI cua UC2 (S1, S2, S3, G2, D2, D3, D4, A2, A3) cho bo slide.
// Anh ra docs/anh-uc2/ voi tien to uc2ai-. Can server tro ly chay o :8188.
//   node tools/chup_uc2_ai.mjs              # chup het
//   node tools/chup_uc2_ai.mjs uc2ai-03     # chi chup anh co tien to do
// TOAN BO chay tren DU LIEU MO PHONG (doi /api/mode sang mock) vi cac buoc nay ghi de xuat va gui mail;
// chup xong tra nguon ve theo .env. AI de nguyen trang thai dang co tren trang Cai dat AI.
import { spawn } from "node:child_process";
import fs from "node:fs";
import os from "node:os";
import path from "node:path";
import { fileURLToPath } from "node:url";

const ROOT = path.resolve(path.dirname(fileURLToPath(import.meta.url)), "..");
const OUT = path.join(ROOT, "docs", "anh-uc2");
const APP = "http://127.0.0.1:8188";
const CHROME = "C:/Program Files/Google/Chrome/Application/chrome.exe";
const PORT = 9336;
const CHI = process.argv.slice(2);
fs.mkdirSync(OUT, { recursive: true });

const ngu = (ms) => new Promise((r) => setTimeout(r, ms));
const profile = fs.mkdtempSync(path.join(os.tmpdir(), "marou-uc2ai-"));
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
async function choDen(expr, ms = 180000) {
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
  await khung(cao || (selector ? 3600 : 900));
  try {
    const params = { format: "png", captureBeyondViewport: false };
    if (selector) {
      const ok = await js(`(() => { const e = ${selector}; if (!e) return false; e.scrollIntoView({block:'start'}); return true; })()`);
      if (!ok) throw new Error("khong thay phan tu cho " + ten);
      await ngu(400);
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
  await api("/api/doan-chat", { user });
  await js(`switchUser(${JSON.stringify(user)})`);
  await choDen("daTaiHopThu === true");
  await ngu(800);
}
async function hoi(user, cau) {
  await vaiMoi(user);
  await js(`(async () => { $('#text').value = ${JSON.stringify(cau)}; await send(); })()`);
  await choDen("!document.querySelector('#dangxuly') && !document.querySelector('.msg.tam')");
  await ngu(1800);
}
const TIN_CUOI = "[...document.querySelectorAll('#chat .msg.out')].pop()";
// Tin mang the co chu nay: brief va bien ban nam giua nhieu tin khac nen khong lay duoc bang TIN_CUOI.
const THE_CO = (chu) => `[...document.querySelectorAll('#chat .msg.out')].filter(m => m.querySelector('.card') && m.innerText.includes(${JSON.stringify(chu)})).pop()`;
const HOI_THOAI = "document.querySelector('#chat')";

async function main() {
  await ketNoi();
  await goi("Page.enable"); await goi("Runtime.enable");
  await khung(900);
  await goi("Page.navigate", { url: APP });
  await choDen("typeof switchUser === 'function' && typeof users !== 'undefined' && users.length > 0", 90000);

  const doi = await api("/api/mode", { bc: "mock" });
  console.log("nguon mo phong:", doi.loi || "ok");
  try {
    await goi("Page.reload");
    await choDen("typeof switchUser === 'function' && typeof users !== 'undefined' && users.length > 0", 90000);
    await choDen("typeof bcInfo !== 'undefined' && bcInfo && !bcInfo.live", 60000);
    const ai = await lay("/api/usage?user=dung.admin");
    console.log("AI dang bat:", ai?.ai?.dang_bat);

    // S1: brief Supply Chain do AI viet
    if (lam("uc2ai-01")) {
      await vaiMoi("trang.sc");
      await api("/api/brief", { user: "trang.sc", text: "" });
      await js("poll()"); await ngu(2500);
      await chup("uc2ai-01-brief-ai", THE_CO("việc quan trọng nhất"));
    }

    // S2 va D4: trang Chi tiet lo cua mot lo can date
    if (lam("uc2ai-02") || lam("uc2ai-03")) {
      const canDate = await lay("/api/uc2/lines?tier=NearExpiry");
      const lo = canDate.filter((r) => r.daysToExpiry >= 3).sort((a, b) => b.inventoryValue - a.inventoryValue)[0];
      await js("showTab('uc2')"); await ngu(1500);
      await js(`openTrace(${JSON.stringify(lo.id)})`);
      await choDen("document.querySelector('#giaithich') && !document.querySelector('#giaithich').innerText.includes('Đang soạn')", 180000);
      await ngu(1200);
      await chup("uc2ai-02-giai-thich-lo", "document.querySelector('#giaithich')");
      await choDen("document.querySelector('#phuongan') && !document.querySelector('#phuongan').innerText.includes('Đang tính')", 180000);
      await ngu(1000);
      await chup("uc2ai-03-phuong-an-lo", "document.querySelector('#phuongan')");
    }

    // D4 tren the trong chat, co nut ghi de xuat
    if (lam("uc2ai-04")) {
      const canDate = await lay("/api/uc2/lines?tier=NearExpiry");
      const lo = canDate.filter((r) => r.daysToExpiry >= 3).sort((a, b) => b.inventoryValue - a.inventoryValue)[0];
      await js("showTab('chat')");
      await vaiMoi("trang.sc");
      await api("/api/action", { user: "trang.sc", verb: "ih_transfer_fast", ref: lo.id, payload: {} });
      await js("poll()"); await ngu(2500);
      await chup("uc2ai-04-the-phuong-an", TIN_CUOI);
    }

    // G2 + A3: duyet huy, bien ban va chung tu nhap.
    // Supply Chain vua tao vua duyet duoc (policy cho ca hai vai), lam vay de xuat va nguoi duyet chac chan cung mot bo nho.
    if (lam("uc2ai-05")) {
      await vaiMoi("trang.sc");
      const hetHan = await lay("/api/uc2/lines?tier=Expired");
      let bb = null;
      for (const r of hetHan.slice(0, 15)) {
        const kq = await api("/api/action", { user: "trang.sc", verb: "ih_propose", ref: r.id, payload: { action_type: "WriteOff" } });
        await ngu(700);
        const st = await lay("/api/state");
        const moiNhat = (st.proposals || []).filter((x) => x.status === "Proposed" && x.action_type === "WriteOff")
          .sort((a, b) => String(b.created_at).localeCompare(String(a.created_at)))[0];
        if (!moiNhat) continue;
        const duyet = await api("/api/action", { user: "trang.sc", verb: "approve", ref: moiNhat.proposal_id, payload: {} });
        await js("poll()"); await ngu(3500);
        bb = await js("(() => { const c = [...document.querySelectorAll('#chat .card')].find(x => x.innerText.includes('BIÊN BẢN')); return c ? 1 : 0; })()");
        console.log("thu duyet", r.itemNo, JSON.stringify(duyet).slice(0, 80), "co bien ban:", bb);
        if (bb) break;
      }
      if (bb) {
        await chup("uc2ai-05-bien-ban-huy", "(() => { const c = [...document.querySelectorAll('#chat .card')].find(x => x.innerText.includes('BIÊN BẢN')); return c.closest('.msg') || c; })()");
      } else { console.log("KHONG tao duoc bien ban"); }
    }

    // D3 bat thuong
    if (lam("uc2ai-07")) { await hoi("trang.sc", "có gì bất thường trong sổ kho không"); await chup("uc2ai-07-bat-thuong", TIN_CUOI); }
    // D2 nguyen nhan huy
    if (lam("uc2ai-08")) { await hoi("trang.sc", "vì sao Chocolate cake hủy nhiều"); await chup("uc2ai-08-nguyen-nhan-huy", TIN_CUOI); }
    // S3 bao cao tuan
    if (lam("uc2ai-09")) { await hoi("trang.sc", "báo cáo tuần hàng hủy"); await chup("uc2ai-09-bao-cao-tuan", TIN_CUOI); }

    // A2 quet sang
    if (lam("uc2ai-10")) {
      await vaiMoi("dung.admin");
      await api("/api/quet-uc2", { user: "dung.admin", chay_lai: true });
      await js("poll()"); await ngu(3000);
      await chup("uc2ai-10-quet-sang", HOI_THOAI);
    }

    // Chi phi theo tung viec
    if (lam("uc2ai-11")) {
      await vaiMoi("dung.admin");
      await js("showTab('caidat')"); await ngu(2500);
      await chup("uc2ai-11-chi-phi-theo-viec", null, 1500);
    }
  } finally {
    const ve = await api("/api/mode", { bc: "env" });
    console.log("tra nguon ve .env:", ve.loi || "ok");
  }
}

main().catch((e) => { console.error(e); process.exitCode = 1; }).finally(() => { try { ws?.close(); } catch {} chrome.kill(); });
