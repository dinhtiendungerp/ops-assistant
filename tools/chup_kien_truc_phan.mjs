// Render docs/kien-truc/kien-truc-chi-tiet.html bang Chrome headless, luu anh ca trang va hai anh cat theo phan de dat len slide:
//   kien-truc-phan-1-tro-ly.png : nguoi dung va kenh, tro ly, Azure OpenAI, ban doi chieu
//   kien-truc-phan-2-bc.png     : ba lop trong Business Central va ba nguyen tac
//   node tools/chup_kien_truc_phan.mjs
import { spawn } from "node:child_process";
import fs from "node:fs";
import os from "node:os";
import path from "node:path";
import { fileURLToPath, pathToFileURL } from "node:url";

const ROOT = path.resolve(path.dirname(fileURLToPath(import.meta.url)), "..");
const DIR = path.join(ROOT, "docs", "kien-truc");
const CHROME = "C:/Program Files/Google/Chrome/Application/chrome.exe";
const PORT = 9338;
const ngu = (ms) => new Promise((r) => setTimeout(r, ms));
const profile = fs.mkdtempSync(path.join(os.tmpdir(), "marou-kt-"));
const chrome = spawn(CHROME, ["--headless=new", `--remote-debugging-port=${PORT}`, `--user-data-dir=${profile}`,
  "--hide-scrollbars", "--window-size=1800,1000", "about:blank"], { stdio: "ignore" });

let ws, id = 0;
const cho = new Map();
async function ketNoi() {
  for (let i = 0; i < 50; i++) {
    try {
      const t = (await (await fetch(`http://127.0.0.1:${PORT}/json`)).json()).find((x) => x.type === "page");
      if (t) {
        ws = new WebSocket(t.webSocketDebuggerUrl);
        await new Promise((r, j) => { ws.onopen = r; ws.onerror = j; });
        ws.onmessage = (e) => { const m = JSON.parse(e.data); if (m.id && cho.has(m.id)) { cho.get(m.id)(m); cho.delete(m.id); } };
        return;
      }
    } catch { /* chua len */ }
    await ngu(200);
  }
  throw new Error("khong ket noi duoc Chrome");
}
const goi = (method, params = {}) => new Promise((r, j) => {
  const n = ++id;
  cho.set(n, (m) => (m.error ? j(new Error(m.error.message)) : r(m.result)));
  ws.send(JSON.stringify({ id: n, method, params }));
});
const js = async (expr) => (await goi("Runtime.evaluate", { expression: expr, returnByValue: true })).result.value;

async function main() {
  await ketNoi();
  await goi("Page.enable");
  await goi("Emulation.setDeviceMetricsOverride", { width: 1800, height: 2600, deviceScaleFactor: 2, mobile: false });
  await goi("Page.navigate", { url: pathToFileURL(path.join(DIR, "kien-truc-chi-tiet.html")).href });
  await ngu(2500);
  const b = await js(`(() => {
    const r = (e) => { const x = e.getBoundingClientRect(); return {top: x.top + scrollY, bottom: x.bottom + scrollY}; };
    const users = r(document.querySelector('.band.users'));
    const ai = r(document.querySelector('.band.ai'));
    const bc = r(document.querySelector('.band.bc'));
    const rules = r(document.querySelector('.rules'));
    const flows = [...document.querySelectorAll('.flow')].map(r);
    return {users, ai, bc, rules, flows, h: document.body.scrollHeight};
  })()`);
  const chup = async (ten, y0, y1) => {
    const r = await goi("Page.captureScreenshot", { format: "png", captureBeyondViewport: true,
      clip: { x: 20, y: y0, width: 1760, height: y1 - y0, scale: 1 } });
    fs.writeFileSync(path.join(DIR, ten), Buffer.from(r.data, "base64"));
    console.log("chup", ten, Math.round(y1 - y0));
  };
  // Phan 1: tu dai nguoi dung toi truoc dai "AI o dau" (dai do da co slide 13 tinh nang rieng).
  await chup("kien-truc-phan-1-tro-ly.png", b.users.top - 10, b.ai.top - 8);
  // Phan 2: tu mui ten doc/ghi/quyen tren lop BC toi het ba nguyen tac.
  await chup("kien-truc-phan-2-bc.png", b.flows[b.flows.length - 1].top - 6, b.rules.bottom + 10);
  const r = await goi("Page.captureScreenshot", { format: "png", captureBeyondViewport: true,
    clip: { x: 0, y: 0, width: 1800, height: b.h, scale: 1 } });
  fs.writeFileSync(path.join(DIR, "kien-truc-chi-tiet.png"), Buffer.from(r.data, "base64"));
}
main().then(() => { chrome.kill(); process.exit(0); }).catch((e) => { console.error(e); chrome.kill(); process.exit(1); });
