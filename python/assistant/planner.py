"""Planner: lop tra loi cac yeu cau khong co san rule.

Ba nguon:
  live   - model that (Azure OpenAI mac dinh, Claude de doi chieu), vong tool_use tu do. Tu chon goi tool nao, bao nhieu lan, khi nao du.
  replay - ban ghi cua mot lan chay model that (phien thiet ke 07/09/2026), luu trong assistant/replays/.
           Chuoi tool duoc CHAY LAI THAT tren du lieu hien tai, nen con so trong cau tra loi la so song,
           khong phai so chep tay. Nhung chuoi buoc thi co dinh: replay khong nghi ra duoc chuoi moi.
  off    - khong co ban ghi khop va khong co API key. Tra loi thang la khong lam duoc.

Muc dich cua replay khong phai gia lam model. No de nguoi xem thay ranh gioi:
cai gi rule/job queue lam duoc, cai gi bat buoc phai co model.
"""
from __future__ import annotations

import json
import logging
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from bc_agent.config import settings

from . import toolbox

log = logging.getLogger(__name__)
REPLAY_DIR = Path(__file__).resolve().parent / "replays"

SYSTEM = """Ban la tro ly van hanh chuoi cua hang chocolate Marou, chay tren du lieu Business Central.
Nguoi nhan: quan ly cua hang, dieu phoi kho, Supply Chain. Ho go tieng Viet tu nhien, khong theo mau.

Cach lam viec:
- Doc du lieu that bang tool truoc khi noi bat cu con so nao. Khong uoc luong, khong nho tu lan truoc.
- Goi it tool nhat du de tra loi. Moi ket qua tool duoc gui lai o moi luot sau, doc thua la ton tien
  va de vuot han muc token. Hoi ve mot mat hang thi bat dau bang stock_by_item.
- Con so trong cau tra loi phai chep tu ket qua tool. Tranh tu cong, chia, suy ra so moi; neu can
  mot phep tinh thi noi ro la uoc tinh va neu phep tinh.
- Rang buoc nguoi ta noi trong cau (ngan sach, so khach, ngay, dieu kien kieu 'tranh do de chay')
  la rang buoc that, phai kiem tra tung cai bang du lieu.
- Truoc khi de xuat rut hang khoi kho trung tam, phai kiem tra viec do co lam vo ke hoach bo sung
  cua cua hang khac khong (tool stores_at_risk).
- Thieu mot thong tin ma khong tool nao tra loi duoc thi goi ask_human hoi dung mot cau, khong doan.
- Neu du lieu khong du de ket luan, noi thang la khong du. Khong bia quy luat.
- Ket thuc bang cau tra loi tieng Viet ngan gon cho nguoi doc tren dien thoai: phuong an, con so,
  danh doi giua cac phuong an, va viec can nguoi quyet. Giu nguyen ma hang va ma kho.
- Muon ghi de xuat vao BC thi goi draft_proposal. De xuat van phai qua policy va nguoi duyet."""


@dataclass
class Step:
    tool: str
    args: dict[str, Any]
    why: str = ""
    result: Any = None


@dataclass
class Plan:
    source: str                       # live | replay
    scenario_id: str = ""
    steps: list[Step] = field(default_factory=list)
    answer: str = ""
    question: str = ""
    drafts: list[dict[str, Any]] = field(default_factory=list)
    tokens_note: str = ""


# ---------------------------------------------------------------- resolve slot
def _resolve(data: Any, path: str) -> Any:
    """Mini path: 'a.b', '0', '#itemNo=33310.qty' (phan tu dau khop), '?itemNo=33310' (loc,
    van la danh sach), '@sum:qty', '@len', '@join:store'."""
    cur = data
    for seg in [s for s in path.split(".") if s]:
        if seg.startswith("#"):
            key, _, val = seg[1:].partition("=")
            cur = next((x for x in cur if str(x.get(key)) == val), None)
        elif seg.startswith("?"):
            key, _, val = seg[1:].partition("=")
            cur = [x for x in cur if str(x.get(key)) == val]
        elif seg.startswith("@sum:"):
            cur = sum(float(x.get(seg[5:]) or 0) for x in cur)
        elif seg.startswith("@join:"):
            cur = ", ".join(str(x.get(seg[6:])) for x in cur)
        elif seg == "@len":
            cur = len(cur)
        elif seg.isdigit():
            cur = cur[int(seg)] if cur and int(seg) < len(cur) else None
        else:
            cur = (cur or {}).get(seg)
        if cur is None:
            return None
    return cur


def _fmt(v: Any) -> str:
    """Dinh dang so kieu Viet: dau cham ngan cach nghin, dau phay thap phan."""
    if isinstance(v, float) and v == int(v):
        v = int(v)
    if isinstance(v, int):
        return f"{v:,}".replace(",", ".")
    if isinstance(v, float):
        return f"{v:,.1f}".replace(",", "\x00").replace(".", ",").replace("\x00", ".")
    return str(v)


class ReplayPlanner:
    source = "replay"

    def __init__(self) -> None:
        self.scenarios = [json.loads(p.read_text(encoding="utf-8")) for p in sorted(REPLAY_DIR.glob("*.json"))]

    @staticmethod
    def _norm(t: str) -> str:
        import unicodedata
        t = unicodedata.normalize("NFD", t.lower()).replace("đ", "d")
        t = "".join(c for c in t if unicodedata.category(c) != "Mn")
        return re.sub(r"\s+", " ", t)

    @staticmethod
    def _has(hay: str, needle: str) -> bool:
        """Khop theo ranh gioi tu. Truoc day dung `in` nen 'quan ly' khop nham tu khoa 'qua'."""
        return re.search(rf"(?<![a-z0-9]){re.escape(needle)}(?![a-z0-9])", hay) is not None

    def match(self, text: str, prev_id: str = "") -> dict[str, Any] | None:
        t = self._norm(text)
        best, best_hit = None, 0
        for sc in self.scenarios:
            if sc.get("requires_prev") and sc["requires_prev"] != prev_id:
                continue
            groups = sc["match"]
            hit = sum(1 for g in groups if any(self._has(t, self._norm(w)) for w in g))
            if hit == len(groups) and hit > best_hit:
                best, best_hit = sc, hit
        return best

    def run(self, asst: Any, user: dict[str, Any], text: str, prev_id: str = "") -> Plan | None:
        sc = self.match(text, prev_id)
        if not sc:
            return None
        steps: list[Step] = []
        for s in sc["steps"]:
            st = Step(s["tool"], s.get("args", {}), s.get("why", ""))
            st.result = toolbox.run_tool(asst, user, st.tool, st.args)
            steps.append(st)
        nums: dict[str, Any] = {}
        vals: dict[str, str] = {}
        for name, spec in sc.get("slots", {}).items():
            if "expr" in spec:                        # cong thuc tren cac slot da co, chi so hoc
                try:
                    raw = eval(spec["expr"], {"__builtins__": {}}, dict(nums))   # noqa: S307 - bieu thuc nam trong file ban ghi
                except Exception:
                    raw = None
            else:
                raw = _resolve(steps[spec["step"]].result, spec.get("path", ""))
            if raw is not None and spec.get("mul"):
                raw = float(raw) * spec["mul"]
            if raw is not None and spec.get("round") is not None:
                raw = round(float(raw), spec["round"]) if spec["round"] else round(float(raw))
            nums[name] = raw
            vals[name] = _fmt(raw) if raw is not None else "?"
        answer = sc["answer"].format(**vals)

        def _draft_value(v):
            # "{wh_qty}" mot minh trong truong so thi lay con so, khong lay chuoi da dinh dang
            if isinstance(v, str):
                m = re.fullmatch(r"\{(\w+)\}", v)
                if m and m.group(1) in nums and nums[m.group(1)] is not None:
                    return nums[m.group(1)]
                return v.format(**vals)
            return v

        drafts = [{k: _draft_value(v) for k, v in d.items()} for d in sc.get("drafts", [])]
        return Plan(self.source, sc["id"], steps, answer, sc.get("question", "").format(**vals), drafts,
                    tokens_note=sc.get("recorded", ""))


class LivePlanner:
    source = "live"

    def __init__(self, budget=None) -> None:
        from bc_agent.llm import build_llm
        self.llm = build_llm()
        self.model = self.llm.model
        self.budget = budget

    def run(self, asst: Any, user: dict[str, Any], text: str, prev_id: str = "") -> Plan | None:
        if self.budget is not None and not self.budget.allow():
            return None
        who = f"Nguoi hoi: {user['display_name']}, vai tro {user['role']}, cua hang {user.get('store_code') or 'khong gan cua hang'}. Kho trung tam {asst.gw.central_wh}. Hom nay {asst.gw.today().isoformat()}."
        msgs: list[dict[str, Any]] = [{"role": "user", "content": f"{who}\n\n{text}"}]
        steps: list[Step] = []
        drafts: list[dict[str, Any]] = []
        question = ""
        for _ in range(toolbox.MAX_STEPS):
            resp = self.llm.complete(SYSTEM, msgs, toolbox.TOOLS)
            if self.budget is not None:
                self.budget.track("planner", self.model, resp.usage)
            if resp.stop_reason == "refusal":
                return None
            msgs.append({"role": "assistant", "content": resp.content})
            calls = [b for b in resp.content if b.type == "tool_use"]
            if not calls:
                answer = "".join(b.text for b in resp.content if b.type == "text").strip()
                return Plan(self.source, "live", steps, answer, question, drafts)
            results = []
            for c in calls:
                try:
                    out = toolbox.run_tool(asst, user, c.name, c.input)
                except Exception as e:                    # loi tool khong lam gay vong, model doc duoc loi
                    out = {"error": str(e)}
                steps.append(Step(c.name, c.input, "", out))
                if c.name == "draft_proposal":
                    drafts.append(dict(c.input))
                if c.name == "ask_human":
                    question = c.input["question"]
                results.append({"type": "tool_result", "tool_use_id": c.id,
                                "content": json.dumps(out, ensure_ascii=False, default=str)[:20000]})
            msgs.append({"role": "user", "content": results})
        return Plan(self.source, "live", steps, "Tôi chay qua nhieu buoc ma chua ket luan duoc, dung lai de anh/chi xem.", question, drafts)


def build_planner(budget=None, live: bool | None = None):
    if live is None:
        live = settings.llm_mode == "live"
    if live:
        try:
            return LivePlanner(budget)
        except Exception as e:
            log.warning("live planner khong dung duoc, quay ve replay: %s", e)
    return ReplayPlanner()
