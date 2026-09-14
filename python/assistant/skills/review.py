"""Skill Review: tro ly tu cham diem quyet dinh cua chinh no, roi de xuat sua policy.

Day la thu con nguoi khong bao gio lam vi khong co thoi gian: quay lai tung viec da lam
2 tuan truoc va hoi "no co dung khong". Khong co vong nay thi he thong dung yen mai mai.

Cach cham:
  Transfer bo sung  -> sau khi hang ve, cua hang co dut hang lai khong, ton co du lau khong
  Transfer can date -> lot da ban het truoc han chua
  Bi hoan tac / tu choi -> dem theo dong policy, nhieu qua thi policy dat sai

Tat ca deu doc tu du lieu, khong hoi ai.
"""
from __future__ import annotations

from collections import defaultdict
from datetime import date, timedelta
from typing import Any

from ..cards import Action, Card
from . import Delivery

SKILL = "review"


def score_one(asst, prop: dict[str, Any]) -> tuple[str, str]:
    """Tra ve (ket qua, ghi chu). ket qua: good | bad | unknown."""
    gw = asst.gw
    if prop["scenario"] == "StoreReplenishment" and prop["action_type"] == "Transfer":
        to_no = prop.get("result_doc")
        t = gw.transfer(to_no) if to_no and gw.is_mock else None
        if t and t["status"] == "Cancelled":
            return "bad", "Bị hoàn tác trước khi ship"
        sug = gw.suggestion(prop["to_loc"], prop["item_no"])
        if not sug:
            return "unknown", "Không còn dòng theo dõi cho cặp cửa hàng và mặt hàng này"
        doc = float(sug["daysOfCover"])
        if sug["stockOutRisk"]:
            return "bad", f"Sau khi chuyển, cửa hàng vẫn dưới ngưỡng ({doc} ngày). Số chuyển thiếu."
        if doc > 45:
            return "bad", f"Chuyển xong tồn lên {doc} ngày, dư nhiều. Số chuyển thừa."
        return "good", f"Cửa hàng giữ được {doc} ngày tồn, trong khoảng hợp lý."
    if prop["scenario"] == "InventoryHealth":
        lines = gw.client.query("inventoryHealthLines",
                                [("itemNo", "eq", prop["item_no"]), ("locationCode", "eq", prop["from_loc"])], top=20)
        left = sum(float(l["quantityOnHand"]) for l in lines if l.get("tier") in ("NearExpiry", "Expired"))
        if left == 0:
            return "good", "Lot cận date đã xử lý xong, không còn tồn rủi ro."
        return "bad", f"Vẫn còn {left:.0f} sản phẩm ở nhóm cận date hoặc hết hạn."
    return "unknown", "Chưa có cách đo cho loại việc này."


def run_self_review(asst, user, days_back: int = 14) -> list[Delivery]:
    cutoff = asst.mem.now() - timedelta(days=days_back)
    done = [p for p in asst.mem.proposals() if p["status"] in ("Executed", "Rejected")
            and (p.get("approved_at") or "") and p["approved_at"] <= cutoff.isoformat()]
    # Trong demo, chua co viec nao du 14 ngay thi cham tat ca viec da xu ly
    if not done:
        done = [p for p in asst.mem.proposals() if p["status"] in ("Executed", "Rejected")]
    if not done:
        return [Delivery(user["user_id"], "Chưa có việc nào tôi đã xử lý để chấm lại.", skill=SKILL)]

    tally = {"good": 0, "bad": 0, "unknown": 0}
    by_rule: dict[str, dict[str, int]] = defaultdict(lambda: {"good": 0, "bad": 0, "unknown": 0})
    details: list[str] = []
    for p in done:
        res, note = score_one(asst, p)
        asst.mem.set_outcome(p["proposal_id"], res, note)
        tally[res] += 1
        by_rule[p.get("policy_rule") or "(người duyệt)"][res] += 1
        if res == "bad":
            details.append(f"{p['item_no']} → {p['to_loc'] or p['from_loc']}: {note}")

    undone = [f for f in asst.mem.feedback() if f["kind"] in ("undo", "reject")]
    by_rule_undo: dict[str, int] = defaultdict(int)
    for f in undone:
        pr = asst.mem.proposal(f["proposal_id"])
        if pr:
            by_rule_undo[pr.get("policy_rule") or "(người duyệt)"] += 1

    # De xuat sua policy dua tren so lieu, khong dua cam tinh
    suggestions: list[str] = []
    for rule, t in by_rule.items():
        total = sum(t.values())
        if total >= 3 and t["bad"] / total >= 0.34:
            suggestions.append(f"{rule}: {t['bad']}/{total} việc chưa đạt, nên siết ngưỡng hoặc chuyển về chế độ hỏi người.")
    for rule, n in by_rule_undo.items():
        if n >= 2:
            suggestions.append(f"{rule}: bị hoàn tác {n} lần, policy này đang cho tôi tự làm quá rộng.")
    if not suggestions:
        suggestions.append("Chưa có dòng policy nào cần sửa. Tôi giữ nguyên và chấm lại sau hai tuần.")

    body = (f"Tôi chấm lại {len(done)} việc đã xử lý: {tally['good']} đạt, {tally['bad']} chưa đạt, {tally['unknown']} chưa đo được.\n"
            + ("\n".join("• " + d for d in details[:4]) if details else ""))
    card = Card(title="Tôi tự chấm lại việc mình đã làm", body=body,
                facts=[("Đạt", str(tally["good"])), ("Chưa đạt", str(tally["bad"])), ("Chưa đo được", str(tally["unknown"])),
                       ("Bị hoàn tác hoặc từ chối", str(len(undone)))]
                      + [("Theo policy " + r, f"{t['good']} đạt / {t['bad']} chưa") for r, t in list(by_rule.items())[:4]],
                ref="self-review", kind="info",
                actions=[Action("review_detail", "Xem đề xuất sửa policy")])
    asst.mem.remember("self-review", {"suggestions": suggestions, "tally": tally})
    return [Delivery(user["user_id"], body, card, SKILL, "self-review")]


def show_suggestions(asst, user, ref: str = "self-review") -> list[Delivery]:
    data = asst.mem.recall(ref) or {}
    lines = data.get("suggestions") or ["Chưa có."]
    return [Delivery(user["user_id"], "Đề xuất sửa policy, dựa trên kết quả thực tế:\n"
                     + "\n".join(f"{i}. {s}" for i, s in enumerate(lines, 1))
                     + "\n\nTôi không tự sửa policy. Bạn quyết rồi đổi trên trang NWV Agent Policy.", skill=SKILL, ref=ref)]
