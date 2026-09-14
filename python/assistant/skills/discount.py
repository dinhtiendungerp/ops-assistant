"""Skill Discount Governance (UC7): exception -> hoi giai trinh quan ly cua hang -> ghi lai -> Retail Ops ket luan.
Tro ly khong ket luan; no thu thap va sap thu tu."""
from __future__ import annotations

from typing import Any

from ..cards import Action, Card, fmt_vnd
from . import Delivery

SKILL = "discount"


def exception_card(exc: dict[str, Any], with_ask: bool = True) -> Card:
    facts = [("Rule", f"{exc['ruleCode']} ({exc['severity']})"), ("Store / nhân viên", f"{exc['storeNo']} / {exc['staffId']}"),
             ("Ngày", exc["transDate"]), ("Giá trị", f"{exc['metricValue']} (ngưỡng {exc['thresholdValue']})"), ("Giảm giá", fmt_vnd(exc["discountAmount"]))]
    if exc.get("explanation"):
        facts.append(("Giải trình", exc["explanation"]))
    actions = [Action("ask_explanation", "Hỏi giải trình")] if with_ask and not exc.get("explanation") else []
    if exc.get("explanation"):
        actions += [Action("confirm_exception", "Xác nhận vi phạm", "destructive"), Action("dismiss_exception", "Bỏ qua", "positive")]
    return Card(title=exc["description"], facts=facts, ref=exc["id"], kind="info", actions=actions)


def brief_for_retail_ops(asst, user) -> list[Delivery]:
    rows = asst.gw.open_exceptions(8)
    if not rows:
        return [Delivery(user["user_id"], "Không có exception discount nào đang mở.", skill=SKILL)]
    high = sum(1 for r in rows if r["severity"] == "High")
    out = [Delivery(user["user_id"], f"{len(rows)} exception đang mở, {high} mức High. Tôi có thể hỏi giải trình quản lý cửa hàng trước khi bạn xem:", skill=SKILL)]
    for r in rows:
        out.append(Delivery(user["user_id"], r["description"], exception_card(r), SKILL, r["id"]))
    return out


def on_ask_explanation(asst, user, exc_id: str) -> list[Delivery]:
    exc = asst.gw.exception(exc_id)
    managers = [u for u in asst.mem.users() if u["role"] == "store_manager" and u.get("store_code") == exc["storeNo"]]
    if not managers:
        return [Delivery(user["user_id"], f"Chưa có quản lý cửa hàng {exc['storeNo']} trong danh bạ, tôi chưa hỏi được.", skill=SKILL)]
    ctx = asst.gw.discount_context(exc["storeNo"], exc["staffId"], exc["transDate"])
    manual = [c for c in ctx if c["discountType"] in ("ManualLine", "ManualTotal", "PriceOverride")]
    total = sum(c["discountAmount"] for c in manual)
    asst.gw.mark_under_review(exc_id)
    out = [Delivery(user["user_id"], f"Đã hỏi {managers[0]['display_name']}. Có trả lời tôi báo lại.", skill=SKILL, ref=exc_id)]
    q = (f"Ngày {exc['transDate']}, nhân viên {exc['staffId']} có {len(manual)} lần giảm giá tay, tổng {fmt_vnd(total)}"
         + (f", trong đó một lần {exc['metricValue']:.0f}% trên {exc['itemNo']}" if exc["ruleCode"] == "DG-01" else "")
         + ". Bạn cho tôi biết lý do để tôi ghi vào hồ sơ, không cần dài.")
    for m in managers:
        asst.mem.ask(m["user_id"], "explanation", exc_id)
        out.append(Delivery(m["user_id"], q, skill=SKILL, ref=exc_id))
    return out


# Cau tra loi cho co le. Nguoi ta hay go "ok" hoac "vang" theo phan xa, roi cau giai thich that
# moi den o tin nhan sau. Nhan bua cau dau thi ho so con lai mot chu "ok", va cau that bi roi ra
# ngoai vi cau hoi da dong.
_QUA_NGAN = 12
_DAP_LAI = {"ok", "oke", "okie", "okay", "vang", "da", "u", "um", "uh", "hieu", "biet", "roi",
            "yes", "y", "duoc", "dc", "co", "khong", "ko", "k"}
# Nguoi dung noi ho vua tra loi nham. Bat de mo lai cau hoi thay vi de cau sua troi vao HELP.
_NOI_NHAM = ("nham", "sai roi", "khong phai", "ko phai", "sua lai", "noi lai", "y toi la",
             "cho toi sua", "nhap nham", "go nham")


def _khong_phai_giai_trinh(text: str) -> bool:
    from ..core import Assistant
    t = Assistant._norm(text)
    return len(text.strip()) < _QUA_NGAN and (t in _DAP_LAI or len(t) <= 3)


def la_noi_nham(text: str) -> bool:
    from ..core import Assistant
    t = Assistant._norm(text)
    return any(Assistant._norm(k) in t for k in _NOI_NHAM)


def on_answer(asst, user, question: dict[str, Any], text: str) -> list[Delivery]:
    exc_id = question["ref"]
    if _khong_phai_giai_trinh(text):
        # Giu nguyen cau hoi dang cho, hoi lai mot lan cho ro.
        return [Delivery(user["user_id"],
                         "Tôi cần một câu lý do để ghi vào hồ sơ, ví dụ \"khách mua nguyên thùng nên giảm thêm, "
                         "có báo quản lý ca\". Bạn gõ giúp tôi lý do thật, một câu ngắn là đủ.",
                         skill=SKILL, ref=exc_id)]
    asst.gw.set_explanation(exc_id, text, user["user_id"])
    asst.mem.close_question(question["id"])
    # Nho lai de neu nguoi dung noi vua go nham thi mo lai dung exception do.
    asst.mem.remember(f"giaitrinh_vua_ghi:{user['user_id']}", {"exc_id": exc_id})
    exc = asst.gw.exception(exc_id)
    from .. import caidat
    out = [Delivery(user["user_id"], caidat.cau("da_ghi_giai_trinh"), skill=SKILL, ref=exc_id)]
    summary = asst.write_rationale(f"Giải trình của {user['display_name']} cho {exc['ruleCode']} ngày {exc['transDate']}: \"{text}\".")
    for r in asst.mem.users_by_role("retail_ops"):
        out.append(Delivery(r["user_id"], summary, exception_card(exc), SKILL, exc_id))
    return out


def mo_lai_giai_trinh(asst, user) -> list[Delivery] | None:
    """Nguoi dung vua ghi giai trinh xong roi noi la nham. Mo lai cau hoi cho dung exception do.

    Tra ve None neu khong co gi de mo lai, de nguoi goi di tiep duong khac."""
    meta = asst.mem.recall(f"giaitrinh_vua_ghi:{user['user_id']}") or {}
    exc_id = meta.get("exc_id")
    if not exc_id:
        return None
    try:
        exc = asst.gw.exception(exc_id)
    except Exception:
        return None
    if exc.get("status") in ("Confirmed", "Dismissed"):
        return [Delivery(user["user_id"], "Retail Ops đã kết luận việc này rồi nên tôi không sửa giải trình được nữa. "
                                          "Bạn nhắn trực tiếp Retail Ops giúp tôi.", skill=SKILL, ref=exc_id)]
    asst.mem.ask(user["user_id"], "explanation", exc_id)
    cu = exc.get("explanation") or ""
    return [Delivery(user["user_id"], f"Được, tôi bỏ câu cũ{f' (“{cu}”)' if cu else ''}. Bạn gõ lại lý do giúp tôi.",
                     skill=SKILL, ref=exc_id)]


def on_conclude(asst, user, exc_id: str, verdict: str) -> list[Delivery]:
    # Ket luan la cua nguoi; tro ly chi ghi nhan. Tren BC that: nguoi doi status tren page NWV Discount Exceptions.
    if asst.gw.is_mock:
        for r in asst.gw.client.data["discountExceptions"]:
            if r["id"] == exc_id:
                r["status"] = "Confirmed" if verdict == "confirm" else "Dismissed"
                r["concludedBy"] = user["user_id"]
    return [Delivery(user["user_id"], f"Đã ghi kết luận {'Xác nhận vi phạm' if verdict == 'confirm' else 'Bỏ qua'} dưới tên {user['display_name']}.", skill=SKILL, ref=exc_id)]
