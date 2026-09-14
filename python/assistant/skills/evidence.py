"""Bằng chứng do người đưa vào: một câu tiếng Việt làm trợ lý đổi chẩn đoán của chính nó.

Đây là chỗ Job Queue không thay được. Chuyện "tháng 8 có hội chợ ngay trước cửa hàng" không nằm
trong bảng nào của Business Central, không ai nhập nó vào đâu cả, và nó là lý do thật sự khiến
mọi con số của tháng đó lệch. Người biết chuyện đó chỉ gõ một câu, và trợ lý phải:

  1. Hiểu đó là sự kiện một lần chứ không phải mức nền mới.
  2. Rút lại đề xuất của chính nó, chứ không phải làm tiếp rồi ghi chú bên lề.
  3. Đánh dấu cửa sổ ngày đó là ngoại lệ và tính lại nhu cầu ngay.
  4. Nhớ, để lần sau không đề xuất lại đúng thứ vừa bị bác.

Hai backend, giống mọi chỗ khác trong prototype:
  rule : chỉ đọc được mẫu "tháng N", "đầu/giữa/cuối tháng N", và khoảng ngày viết rõ. Ngoài mẫu
         thì nói thẳng là không đọc được và hỏi lại khoảng ngày. Không đoán.
  live : model đọc câu bất kỳ và trả về JSON theo schema.
"""
from __future__ import annotations

import json
import re
import unicodedata
from datetime import date
from typing import Any

from bc_agent.config import settings

from ..cards import Action, Card
from . import Delivery, demand

SKILL = "evidence"

SCHEMA = {
    "type": "object",
    "properties": {
        "kind": {"type": "string", "enum": ["one_off", "permanent", "supply", "unknown"],
                 "description": "one_off: su kien mot lan da qua. permanent: muc nen da doi han. supply: van de nguon cung. unknown: khong du thong tin"},
        "date_from": {"type": "string", "description": "yyyy-mm-dd, rong neu khong suy ra duoc"},
        "date_to": {"type": "string", "description": "yyyy-mm-dd, rong neu khong suy ra duoc"},
        "reason": {"type": "string", "description": "tom tat su viec bang tieng Viet, duoi 15 tu"},
    },
    "required": ["kind", "date_from", "date_to", "reason"],
    "additionalProperties": False,
}

_ONE_OFF = re.compile(r"(hội chợ|hoi cho|sự kiện|su kien|khai trương|khai truong|lễ hội|le hoi|đoàn khách|doan khach|"
                      r"một lần|mot lan|đợt đó|dot do|hôm đó|hom do|tạm thời|tam thoi|xong rồi|xong roi|hết rồi|het roi)", re.I)
_PERMANENT = re.compile(r"(mở thêm|mo them|chuyển sang|chuyen sang|từ nay|tu nay|lâu dài|lau dai|thường xuyên|thuong xuyen)", re.I)
_SUPPLY = re.compile(r"(nhà cung cấp|nha cung cap|nhà máy|nha may|không kịp sản xuất|khong kip san xuat|thiếu nguyên liệu|thieu nguyen lieu)", re.I)
_MONTH = re.compile(r"(đầu|giữa|cuối|dau|giua|cuoi)?\s*tháng\s*(\d{1,2})", re.I)
_RANGE = re.compile(r"(\d{1,2})\s*[/-]\s*(\d{1,2})\s*(?:đến|den|tới|toi|-)\s*(\d{1,2})\s*[/-]\s*(\d{1,2})")


def _norm(t: str) -> str:
    t = unicodedata.normalize("NFD", t.lower()).replace("đ", "d")
    return "".join(c for c in t if unicodedata.category(c) != "Mn")


def _month_range(word: str, month: int, year: int) -> tuple[date, date]:
    import calendar
    last = calendar.monthrange(year, month)[1]
    w = _norm(word or "")
    if w == "dau":
        return date(year, month, 1), date(year, month, 10)
    if w == "giua":
        return date(year, month, 11), date(year, month, 20)
    if w == "cuoi":
        return date(year, month, 21), date(year, month, last)
    return date(year, month, 1), date(year, month, last)


class RuleEvidence:
    source = "rule"

    def classify(self, text: str, today: date) -> dict[str, Any]:
        kind = "unknown"
        if _SUPPLY.search(text):
            kind = "supply"
        elif _PERMANENT.search(text):
            kind = "permanent"
        elif _ONE_OFF.search(text):
            kind = "one_off"
        d_from = d_to = None
        m = _RANGE.search(text)
        if m:
            d1, m1, d2, m2 = (int(x) for x in m.groups())
            d_from, d_to = date(today.year, m1, d1), date(today.year, m2, d2)
        else:
            m = _MONTH.search(text)
            if m:
                d_from, d_to = _month_range(m.group(1), int(m.group(2)), today.year)
        return {"kind": kind, "from": d_from, "to": d_to, "reason": text.strip()[:120], "source": self.source}


class LiveEvidence:
    source = "live"

    def __init__(self, budget=None):
        from bc_agent.llm import build_llm
        self.llm = build_llm(fast=True)
        self.model = self.llm.model
        self.budget = budget
        self.fallback = RuleEvidence()

    def classify(self, text: str, today: date) -> dict[str, Any]:
        if self.budget is not None and not self.budget.allow():
            return self.fallback.classify(text, today)
        try:
            resp = self.llm.text(
                system=("Ban doc mot cau giai thich cua nhan vien van hanh chuoi cua hang ve chuyen da xay ra "
                        f"tai mot cua hang. Hom nay la {today.isoformat()}. Tra ve JSON theo schema. "
                        "Chi dien date_from va date_to khi cau noi du de suy ra khoang ngay."),
                user=text, max_tokens=512, schema=SCHEMA)
            if self.budget is not None:
                self.budget.track("evidence", self.model, resp.usage)
            if resp.stop_reason == "refusal":
                return self.fallback.classify(text, today)
            from bc_agent.llm import text_of
            d = json.loads(text_of(resp))
            return {"kind": d["kind"], "reason": d.get("reason") or text[:120], "source": self.source,
                    "from": date.fromisoformat(d["date_from"]) if d.get("date_from") else None,
                    "to": date.fromisoformat(d["date_to"]) if d.get("date_to") else None}
        except Exception:
            return self.fallback.classify(text, today)


def build(budget=None, live: bool | None = None):
    if live is None:
        live = settings.llm_mode == "live"
    if live:
        try:
            return LiveEvidence(budget)
        except Exception:
            pass
    return RuleEvidence()


# ---------------------------------------------------------------- ap dung
def apply(asst: Any, user: dict[str, Any], prop: dict[str, Any], text: str) -> list[Delivery]:
    meta = asst.mem.recall(f"ladderprop:{prop['proposal_id']}") or {}
    item_no, location = meta.get("item_no"), meta.get("location")
    if not item_no:
        return [Delivery(user["user_id"], "Đề xuất này chưa gắn với cặp cửa hàng và mặt hàng nào.", skill=SKILL)]

    today = asst.gw.today()
    key = f"{location}|{item_no}"
    again = bool((asst.mem.recall(f"ladder:{key}") or {}).get("evidence_rounds"))
    c = asst.ev.classify(text, today)
    before = demand.view(asst, item_no, location)

    if c["kind"] == "unknown" or (c["kind"] == "one_off" and not c["from"]):
        note = ("Tôi chưa đọc được câu này. " if c["source"] == "rule" else "")
        return [Delivery(user["user_id"],
                         note + "Bạn cho tôi khoảng ngày, ví dụ tháng 8, hoặc 8/8 đến 24/8. Tôi cần biết chuyện đó "
                         "rơi vào những ngày nào thì mới bỏ đúng những ngày đó ra được, chứ đoán thì hỏng số.",
                         skill=SKILL, ref=prop["proposal_id"])]

    if c["kind"] == "permanent":
        return [Delivery(user["user_id"],
                         f"Vậy đây là mức nền mới chứ không phải sự kiện một lần. Tôi giữ nguyên đề xuất nâng ngưỡng, "
                         f"và ghi lý do bạn vừa nói vào đề xuất. Bạn bấm Duyệt là tôi ghi vào BC.",
                         skill=SKILL, ref=prop["proposal_id"])]

    if c["kind"] == "supply":
        return [Delivery(user["user_id"],
                         "Nếu gốc là nguồn cung thì nâng ngưỡng đặt lại hàng không giải quyết được, chỉ làm đơn chuyển "
                         "nhiều hơn mà kho vẫn không có hàng. Tôi rút đề xuất và chuyển việc này thành câu hỏi cho mua hàng.",
                         skill=SKILL, ref=prop["proposal_id"])]

    # one_off co khoang ngay: rut de xuat, danh dau ngoai le, tinh lai
    demand.add_exception(asst, item_no, location, c["from"], c["to"], c["reason"], user["display_name"])
    asst.gw.reject(prop["bc_id"], user.get("bc_user") or user["user_id"], f"Su kien mot lan: {c['reason'][:180]}")
    prop.update({"status": "Rejected", "approver": user["user_id"], "outcome_note": c["reason"]})
    asst.mem.save_proposal(prop)

    notes = asst.mem.recall(f"ladder:{key}") or {}
    notes.setdefault("one_off", []).append({"from": c["from"].isoformat(), "to": c["to"].isoformat(), "reason": c["reason"]})
    notes["evidence_rounds"] = notes.get("evidence_rounds", 0) + 1
    asst.mem.remember(f"ladder:{key}", notes)

    after = demand.view(asst, item_no, location)
    from . import ladder
    d2 = ladder.diagnose(asst, item_no, location)

    left = [e for e in d2["episodes"]]
    thin = after.usable_days < 14
    facts = [
        ("Tôi đã hiểu là", f"sự kiện một lần, {c['from'].isoformat()} đến {c['to'].isoformat()}"),
        ("Đọc câu bằng", "model" if c["source"] == "live" else "rule (chỉ nhận dạng được mẫu tháng N và khoảng ngày viết rõ)"),
        ("Nhu cầu ngày trước khi biết", f"{before.corrected_daily}"),
        ("Nhu cầu ngày sau khi biết", f"{after.corrected_daily}"),
        ("Số ngày bị loại thêm", f"{len(after.excluded_days)} ngày"),
        ("Cửa sổ tính lại", f"{after.window} ngày" + (", đã nới rộng vì thiếu ngày sạch" if after.widened else "")),
        ("Số ngày còn dùng được", f"{after.usable_days}/{after.window}" + (" (mỏng, con số này chưa chắc)" if thin else "")),
        ("Đợt đứt hàng chưa giải thích", f"{len(left)} đợt" + (": " + "; ".join(f"{a.isoformat()} đến {b.isoformat()}" for a, b in left[:4]) if left else "")),
        ("Đề xuất cũ", f"Nâng Reorder Point Days lên {prop['quantity']:.0f} ngày"),
        ("Việc thay thế", "Giữ nguyên ngưỡng, đánh dấu cửa sổ sự kiện" if not left else "Chưa đề xuất gì thêm, tôi hỏi tiếp trước"),
    ]
    head = ("Tôi ghi nhận thêm. " if again else
            "Tôi rút lại đề xuất. Lý do tôi đề xuất nâng ngưỡng là vì thấy đứt hàng lặp lại mà không biết vì sao. ")
    body = (head
            + f"Giờ biết {c['reason']}, thì mấy đợt đó có nguyên nhân riêng, không phải mức nền đổi. "
            f"Nâng ngưỡng vĩnh viễn vì một chuyện đã qua sẽ làm tồn kho phình ra cả năm sau.\n\n"
            f"Tôi đã đánh dấu {c['from'].isoformat()} đến {c['to'].isoformat()} là ngoại lệ và tính lại. "
            f"Nhu cầu ngày đi từ {before.corrected_daily} xuống {after.corrected_daily}.")
    if thin:
        body += (f"\n\nMột điều tôi phải nói trước. Bỏ ngày sự kiện và ngày đứt hàng ra thì không còn đủ ngày sạch, "
                 f"nên tôi đã nới cửa sổ lên {after.window} ngày và vẫn chỉ được {after.usable_days} ngày dùng được. "
                 f"Con số {after.corrected_daily} dựa trên chừng đó ngày thôi, đừng chốt kế hoạch dài hạn bằng nó. "
                 f"Qua vài tuần có đủ ngày sạch tôi tính lại.")
    if left:
        body += ("\n\nCòn một chuyện chưa xong. Câu vừa rồi giải thích được mấy đợt trong khoảng đó, nhưng vẫn còn "
                 + str(len(left)) + " đợt nằm ngoài cửa sổ đó: "
                 + "; ".join(f"{a.isoformat()} đến {b.isoformat()}" for a, b in left[:4])
                 + ". Mấy đợt này tôi chưa biết vì sao, nên tôi chưa dám nói là không cần đổi ngưỡng. "
                 "Bạn nhớ được gì về mấy ngày đó thì gõ tiếp cho tôi một câu nữa.")
    else:
        body += ("\n\nSau khi bỏ cửa sổ đó ra thì không còn đợt đứt hàng nào chưa giải thích. "
                 "Tôi không đề xuất đổi ngưỡng nữa, và lần sau gặp lại cặp này tôi cũng sẽ không đề xuất lại.")
    acts = [Action("demand_show", "Xem bảng nhu cầu", payload={"item_no": item_no, "location": location}), Action("ack", "OK")]
    if left:
        acts.insert(0, Action("lad_evidence", "Nói tiếp về mấy đợt kia", needs_input="text"))
    card = Card(title="Tôi tính lại và rút đề xuất", body=body, facts=facts, ref=prop["proposal_id"], kind="info", actions=acts)
    return [Delivery(user["user_id"], "Tôi nhận bằng chứng và tính lại.", card, SKILL, prop["proposal_id"])]
