"""Thang chẩn đoán: khi cùng một chỗ hỏng lại, đổi LOẠI cách sửa chứ không lặp lại cách cũ.

Đây là chỗ khác nhau giữa một job chạy đêm và một trợ lý. Job đêm thấy days of cover thấp thì
đề xuất chuyển hàng, lần nào cũng vậy, mười lần như một. Chuyển hàng ba lần mà vẫn đứt hàng thì
vấn đề không nằm ở chuyến hàng, nó nằm ở ngưỡng đặt lại hàng, hoặc ở chính con số dự báo,
hoặc ở chỗ không ai trong dữ liệu biết. Bốn nguyên nhân đó cần bốn cách sửa khác nhau.

Bậc thang:
  1. Thiếu lần này            -> chuyển hàng (skill replenishment lo)
  2. Lặp lại, ngưỡng quá thấp -> đề xuất nâng Reorder Point Days cho đúng cặp này
  3. Đã nâng ngưỡng vẫn lặp   -> con số dự báo sai vì lịch sử bị cắt cụt, đề xuất sửa cách tính
  4. Sửa cách tính vẫn lặp    -> không còn là bài toán kế hoạch, đưa người quyết kèm bằng chứng

Bậc thang này viết bằng AL cũng được, và nên viết bằng AL. Cái AL không làm được là bước sau:
người đọc kết luận, gõ một câu tiếng Việt giải thích chuyện đã xảy ra, và trợ lý phải đổi
chẩn đoán của chính nó theo câu đó. Xem evidence.py.
"""
from __future__ import annotations

import uuid
from typing import Any

from ..cards import Action, Card
from . import Delivery, demand

SKILL = "ladder"
SCENARIO = "DemandPlanning"
TRANSFER_LEAD_DAYS = 3     # POC: gia dinh. That ra phai lay tu Transfer Route trong BC.


def interventions(asst: Any, item_no: str, location: str) -> list[dict[str, Any]]:
    """Lich su tro ly da can thiep cho dung cap nay. Doc tu BC chu khong doc tu bo nho tro ly:
    lich su hanh dong thuoc ve BC."""
    rows = asst.gw.client.query("agentProposals", [("itemNo", "eq", item_no)], top=500)
    return [r for r in rows if r.get("toLocationCode") == location and r.get("status") == "Executed"]


def _explained(asst: Any, item_no: str, location: str, ep: tuple) -> bool:
    """Mot dot dut hang coi la da co nguyen nhan neu no nam trong cua so su kien da xac nhan,
    hoac no bat dau ngay sau cua so do (chay het hang vi ban vong trong su kien).
    Day la ly do bac thang tu ha xuong sau khi nguoi dua bang chung, chu khong phai do ai tat no."""
    from datetime import timedelta
    a, b = ep
    for e in demand.exceptions(asst, item_no, location):
        from datetime import date as _d
        f, t = _d.fromisoformat(e["from"]), _d.fromisoformat(e["to"])
        if a <= t and b >= f:
            return True
        if t < a <= t + timedelta(days=TRANSFER_LEAD_DAYS + 7):
            return True
    return False


def diagnose(asst: Any, item_no: str, location: str) -> dict[str, Any]:
    v = demand.view(asst, item_no, location)
    so12 = demand.stockout_days(demand._daily(asst.gw.sales_history(item_no, location, days=98)), asst.gw.today())
    eps = demand.episodes(so12)
    eps = [e for e in eps if not _explained(asst, item_no, location, e)]
    hist = interventions(asst, item_no, location)
    transfers = [h for h in hist if h["actionType"] == "Transfer"]
    params = [h for h in hist if h["actionType"] == "AdjustParameter"]
    notes = asst.mem.recall(f"ladder:{location}|{item_no}") or {}

    setup_rop = 5          # POC: NWV Agent Setup."Reorder Point Days"
    # Giai thich duoc bang mot cau: hai lan thoi gian chuyen hang, cong ba ngay dem.
    # Khong cho no chay theo so dot dut hang, vi nhu vay mot thang xau se day nguong len vinh vien.
    suggested_rop = TRANSFER_LEAD_DAYS * 2 + 3

    if len(eps) >= 2 and len(transfers) >= 2 and (params or notes.get("rop_raised")):
        if notes.get("forecast_fixed"):
            level, action = 4, "Escalate"
        else:
            level, action = 3, "AdjustParameter"
    elif len(eps) >= 2 and len(transfers) >= 1:
        level, action = 2, "AdjustParameter"
    else:
        level, action = 1, "Transfer"

    return {"level": level, "action": action, "view": v, "episodes": eps, "so12": so12, "transfers": transfers,
            "params": params, "setup_rop": setup_rop, "suggested_rop": suggested_rop, "notes": notes}


def _rationale(d: dict[str, Any]) -> str:
    v, eps, tr = d["view"], d["episodes"], d["transfers"]
    head = (f"{v.item_desc} tại {v.location} đứt hàng {len(d['so12'])} ngày trong {len(eps)} đợt "
            f"suốt 12 tuần qua. Trợ lý đã chuyển hàng {len(tr)} lần"
            + (f" ({', '.join(t['resultDocumentNo'] for t in tr if t.get('resultDocumentNo'))})" if tr else "")
            + ", vẫn lặp lại.")
    if d["level"] == 2:
        return (f"{head} Chuyến hàng không phải chỗ hỏng. Ngưỡng đặt lại hàng đang là {d['setup_rop']} ngày, "
                f"trong khi riêng thời gian chuyển hàng đã mất {TRANSFER_LEAD_DAYS} ngày. "
                f"Đề xuất nâng ngưỡng cho riêng cặp này lên {d['suggested_rop']} ngày, tức hai lần thời gian "
                f"chuyển hàng cộng ba ngày đệm.")
    if d["level"] == 3:
        return (f"{head} Ngưỡng đã nâng mà vẫn lặp. Vấn đề nằm ở con số dự báo: nhu cầu đọc thô là "
                f"{v.naive_daily} một ngày, nhưng {len(v.stockout_days)} ngày trong cửa sổ là ngày không còn hàng "
                f"để bán. Bỏ những ngày đó ra thì nhu cầu là {v.corrected_daily}, cao hơn {v.uplift_pct:.0f}%. "
                f"Đề xuất đổi cách tính nhu cầu cho cặp này sang số đã sửa.")
    if d["level"] == 4:
        return (f"{head} Đã nâng ngưỡng và đã sửa cách tính dự báo mà vẫn đứt. Chỗ này vượt phạm vi kế hoạch: "
                f"có thể là nguồn cung, là danh mục hàng của cửa hàng, hoặc là chuyện không nằm trong dữ liệu. "
                f"Trợ lý dừng ở đây và đưa bạn quyết.")
    return head


def run(asst: Any, user: dict[str, Any], item_no: str, location: str) -> list[Delivery]:
    d = diagnose(asst, item_no, location)
    if d["level"] == 1:
        from . import replenishment
        return replenishment.handle_stockout(asst, user, type("I", (), {"item_text": item_no, "quantity": 0})())

    v = d["view"]
    ref = f"LAD-{uuid.uuid4().hex[:6].upper()}"
    unit = asst.gw.unit_cost(item_no)
    created = asst.gw.create_proposal(
        scenario=SCENARIO, action_type=d["action"], item_no=item_no, from_loc="", to_loc=location,
        quantity=d["suggested_rop"] if d["action"] == "AdjustParameter" else 0,
        reference_key=f"{location}|{item_no}|L{d['level']}", rationale=_rationale(d), priority=80,
        evidence={"level": d["level"], "episodes": [[a.isoformat(), b.isoformat()] for a, b in d["episodes"]],
                  "transfers": [t.get("resultDocumentNo") for t in d["transfers"]],
                  "naive_daily": v.naive_daily, "corrected_daily": v.corrected_daily,
                  "stockout_days": len(v.stockout_days), "setup_rop": d["setup_rop"]},
        run_id=asst.run_id, model_name=asst.model_name)
    prop = {"proposal_id": created.get("proposalId") or str(uuid.uuid4()), "bc_id": created["id"],
            "scenario": SCENARIO, "action_type": d["action"], "status": "Proposed", "item_no": item_no,
            "from_loc": "", "to_loc": location, "quantity": d["suggested_rop"], "max_quantity": d["suggested_rop"],
            "rationale": _rationale(d), "evidence": {"level": d["level"]}, "requested_by": user["user_id"],
            "created_at": asst.mem.now().isoformat(), "item_desc": v.item_desc, "value_vnd": 0.0,
            "item_category": "", "ladder_ref": ref}
    asst.mem.save_proposal(prop)
    asst.mem.remember(f"ladderprop:{prop['proposal_id']}", {"item_no": item_no, "location": location, "level": d["level"]})

    decision = asst.policy.decide(prop)
    prop["policy_rule"], prop["policy_mode"] = decision.rule_code, decision.mode.value
    asst.mem.save_proposal(prop)

    facts = [
        ("Bậc chẩn đoán", f"{d['level']}/4"),
        ("Đứt hàng 12 tuần", f"{len(d['so12'])} ngày, {len(d['episodes'])} đợt"),
        ("Đã chuyển hàng", f"{len(d['transfers'])} lần" + (f": {', '.join(t.get('resultDocumentNo','') for t in d['transfers'])}" if d["transfers"] else "")),
        ("Nhu cầu đọc thô", f"{v.naive_daily}/ngày"),
        ("Nhu cầu sau khi bỏ ngày đứt hàng", f"{v.corrected_daily}/ngày ({v.uplift_pct:+.0f}%)"),
        ("Việc đề xuất", "Nâng Reorder Point Days lên " + str(d["suggested_rop"]) if d["action"] == "AdjustParameter" and d["level"] == 2
         else ("Đổi cách tính nhu cầu sang số đã sửa" if d["level"] == 3 else "Đưa người quyết định")),
        ("Policy", f"{decision.rule_code}: {decision.reason}"),
    ]
    card = Card(title=f"Bậc {d['level']}: đổi cách sửa, không lặp lại cách cũ",
                body=_rationale(d) + "\n\nNếu bạn biết chuyện gì đã xảy ra mà dữ liệu không thấy, "
                     "bấm nút cuối và gõ một câu. Tôi sẽ tính lại từ đầu.",
                facts=facts, ref=prop["proposal_id"], kind="proposal",
                actions=[Action("lad_approve", "Duyệt đổi ngưỡng", "positive"),
                         Action("lad_reject", "Từ chối", "destructive", needs_input="reason"),
                         Action("lad_evidence", "Không đúng, để tôi giải thích", needs_input="text")])
    out = [Delivery(user["user_id"], f"Chẩn đoán bậc {d['level']} cho {v.item_desc} tại {location}.", card, SKILL, prop["proposal_id"])]
    for u in asst.mem.users_by_role("supply_chain"):
        if u["user_id"] != user["user_id"]:
            out.append(Delivery(u["user_id"], f"Chẩn đoán bậc {d['level']} cho {v.item_desc} tại {location}.", card, SKILL, prop["proposal_id"]))
    return out


def on_approve(asst: Any, user: dict[str, Any], prop: dict[str, Any]) -> list[Delivery]:
    meta = asst.mem.recall(f"ladderprop:{prop['proposal_id']}") or {}
    key = f"{meta.get('location')}|{meta.get('item_no')}"
    notes = asst.mem.recall(f"ladder:{key}") or {}
    if meta.get("level") == 2:
        notes["rop_raised"] = prop["quantity"]
        msg = f"Đã nâng Reorder Point Days cho {key} lên {prop['quantity']:.0f} ngày, ghi dưới tên {user['display_name']}."
    elif meta.get("level") == 3:
        notes["forecast_fixed"] = True
        msg = f"Đã đổi cách tính nhu cầu cho {key} sang số đã sửa, ghi dưới tên {user['display_name']}."
    else:
        msg = "Đã ghi nhận, việc này chuyển cho người phụ trách."
    asst.mem.remember(f"ladder:{key}", notes)
    asst.gw.approve(prop["bc_id"], user.get("bc_user") or user["user_id"], "Duyet tu bac thang chan doan")
    prop.update({"status": "Executed", "approver": user["user_id"], "approved_at": asst.mem.now().isoformat(), "result_doc": ""})
    asst.mem.save_proposal(prop)
    return [Delivery(user["user_id"], msg + " Trên hệ thống thật, ngưỡng này được lưu riêng cho từng cặp cửa hàng và mặt hàng, không đổi ngưỡng chung của cả hệ thống.", skill=SKILL, ref=prop["proposal_id"])]
