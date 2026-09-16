"""Skill Replenishment (UC5): cua hang bao sap het -> de xuat Transfer -> dieu phoi duyet trong chat -> TO -> theo doi ship.

So luong do BC (suggestion) hoac cong thuc mirror tinh; mo hinh ngon ngu khong nhap so.
"""
from __future__ import annotations

import json
import math
import uuid
from datetime import timedelta
from typing import Any

from ..cards import Action, Card, fmt_qty, fmt_vnd
from . import Delivery

SKILL = "replenishment"
TARGET_DOC = 14
REORDER_DOC = 5


def _plan(gw, store: str, item_no: str, requested_qty: float) -> dict[str, Any]:
    """Tinh de xuat. Uu tien suggestion cua BC; neu khong co thi mirror cong thuc AL."""
    locs = {r["locationCode"]: r for r in gw.stock_by_location(item_no)}
    st = locs.get(store, {"qty": 0.0, "avgDaily": 0.0, "daysOfCover": 9999})
    wh = locs.get(gw.central_wh, {"qty": 0.0})
    sug = gw.suggestion(store, item_no)
    transit = float(sug["storeQtyInTransit"]) if sug else 0.0
    avg = float(sug["avgDailySalesQty"]) if sug else float(st.get("avgDaily") or 0)
    onhand = float(sug["storeQtyOnHand"]) if sug else float(st["qty"])
    wh_avail = float(sug["warehouseQtyAvailable"]) if sug else float(wh["qty"])
    doc = round((onhand + transit) / avg, 1) if avg > 0 else 9999
    if sug and sug.get("demandBasis") == "LS":
        # BC that: so luong va so ngay phu lay nguyen tu LS Replenishment, tro ly khong tu tinh lai (Dung chot
        # dung module Replenishment cua LS, 13/09/2026). Truoc do o day nhan TARGET_DOC 14 ngay nen ra 164
        # trong khi LS de xuat 82 cho cung dong.
        target_days = float(sug.get("targetDays") or 0)
        need = float(sug.get("suggestedQty") or 0)
        target = onhand + transit + need
    else:
        target_days = TARGET_DOC
        target = math.ceil(avg * TARGET_DOC) if avg > 0 else 0
        need = max(0.0, target - onhand - transit)
    if need == 0 and requested_qty > 0:
        need = requested_qty            # store noi so, chua co lich su ban
    constrained = min(need, wh_avail)
    # nguon thay the: store khac co days of cover > 30 va ton > need
    alt = [r for code, r in locs.items() if code not in (store, gw.central_wh) and r["daysOfCover"] > 30 and r["qty"] >= need and need > 0]
    alt.sort(key=lambda r: -r["daysOfCover"])
    # gop chuyen: store khac cung risk voi item nay
    others = [r for r in gw.risky_suggestions(50) if r["itemNo"] == item_no and r["storeLocationCode"] != store]
    return {"onhand": onhand, "transit": transit, "avg": avg, "doc": doc, "target": target, "need": need,
            "target_days": target_days, "nguon": "LS Replenishment" if sug and sug.get("demandBasis") == "LS" else "",
            "wh_avail": wh_avail, "constrained": constrained, "alt": alt[:1], "others": others}


def handle_stockout(asst, user: dict[str, Any], intent) -> list[Delivery]:
    gw = asst.gw
    hint = getattr(intent, "store_hint", "") or ""
    store = user.get("store_code") or hint
    if hint and user.get("store_code") and hint != user["store_code"]:
        # Quan ly cua hang chi yeu cau bo sung cho cua hang minh. Truoc day ma cua hang khac trong cau bi bo qua va
        # tro ly tra loi cho cua hang cua nguoi hoi, nhin vao tuong la so cua cua hang duoc nhac.
        return [Delivery(user["user_id"], f"Bạn đang phụ trách {user['store_code']}, nên yêu cầu bổ sung chỉ gửi được cho "
                                          f"{user['store_code']}. Muốn xem tồn ở {hint} thì hỏi \"tồn kho <mặt hàng> ở {hint}\".",
                         skill=SKILL)]
    if not store:
        # Vai tro khong gan cua hang (dieu phoi, Supply Chain) hoi "sap het X": tra ton moi dia diem thay vi hoi lai
        # "ban thuoc cua hang nao". Dung bac ngay 14/09/2026: dang dung vai kho ma con hoi o dau.
        if intent.item_text and gw.find_item(intent.item_text):
            return stock_query(asst, user, intent)
        return [Delivery(user["user_id"], "Bạn hỏi mặt hàng nào, và ở cửa hàng nào nếu cần? Ví dụ: \"sắp hết Choco nuts ở S0001\".",
                         skill=SKILL, meta={"unresolved": True})]
    item = gw.find_item(intent.item_text) if intent.item_text else None
    if not item:
        names = ", ".join(i["description"] for i in gw.items()[:6])
        return [Delivery(user["user_id"], f"Tôi chưa nhận ra mặt hàng. Bạn nói rõ tên giúp tôi, ví dụ: {names}.", skill=SKILL)]

    plan = _plan(gw, store, item["itemNo"], intent.quantity)
    ref = f"{store}|{item['itemNo']}"
    out: list[Delivery] = []

    if plan["need"] <= 0:
        out.append(Delivery(user["user_id"],
            f"{item['description']} tại {store} còn {fmt_qty(plan['onhand'])}, bán bình quân {plan['avg']:.1f}/ngày, "
            f"đủ {plan['doc']} ngày. " + (f"{plan['nguon']} chưa đề xuất chuyển cho dòng này." if plan["nguon"] else f"Theo ngưỡng {REORDER_DOC} ngày thì chưa cần chuyển.") + f" Nếu có sự kiện sắp tới bạn nói số lượng, tôi chuyển yêu cầu cho điều phối.", skill=SKILL, ref=ref))
        return out

    if plan["constrained"] <= 0 and not plan["alt"]:
        # kho het, khong co store du: leo thang
        prop = _create(asst, user, item, store, gw.central_wh, 0, "Escalate", plan, ref,
                       f"Kho {gw.central_wh} hết {item['description']}, {store} chỉ còn {plan['doc']} ngày. Cần mua hoặc sản xuất.")
        out.append(Delivery(user["user_id"], f"Kho trung tâm cũng hết {item['description']}. Tôi đã báo điều phối và Supply Chain để tìm nguồn.", skill=SKILL, ref=ref))
        out += _to_dispatchers(asst, prop, item, plan, escalate=True)
        return out

    from_loc, qty = gw.central_wh, plan["constrained"]
    if plan["constrained"] < plan["need"] and plan["alt"]:
        from_loc, qty = plan["alt"][0]["locationCode"], min(plan["need"], plan["alt"][0]["qty"])

    rationale = asst.write_rationale(
        f"{store} còn {fmt_qty(plan['onhand'])} {item['description']}, bán {plan['avg']:.1f}/ngày, hết trong {plan['doc']} ngày. "
        f"Chuyển {fmt_qty(qty)} từ {from_loc} để đủ {fmt_qty(plan['target_days'])} ngày"
        + (f" theo {plan['nguon']}." if plan["nguon"] else ".")
        + (f" Kho chỉ còn {fmt_qty(plan['wh_avail'])} nên chưa đủ {fmt_qty(plan['need'])}." if plan["constrained"] < plan["need"] and from_loc == gw.central_wh else "")
        + (f" {', '.join(o['storeLocationCode'] for o in plan['others'])} cũng sắp hết, có thể gộp chuyến." if plan["others"] else ""))
    prop = _create(asst, user, item, store, from_loc, qty, "Transfer", plan, ref, rationale)
    # Quyet dinh policy TRUOC khi tra loi cua hang, de khong noi sai ("dang xin duyet" trong khi da tu lam)
    downstream = _to_dispatchers(asst, prop, item, plan)
    head = (f"Đã ghi nhận. {item['description']} tại {store} còn {fmt_qty(plan['onhand'])}, đủ {plan['doc']} ngày. ")
    if prop.get("status") == "Executed":
        out.append(Delivery(user["user_id"], head + f"Tôi đã lên đơn {prop['result_doc']} chuyển {fmt_qty(qty)} từ {from_loc}, kho sẽ ship hôm nay.", skill=SKILL, ref=ref))
        downstream = [d for d in downstream if d.user_id != user["user_id"]]
    else:
        out.append(Delivery(user["user_id"], head + f"Tôi đề xuất chuyển {fmt_qty(qty)} từ {from_loc} và đang xin điều phối duyệt, thường trong 15 phút.", skill=SKILL, ref=ref))
    out += downstream
    return out


def _create(asst, user, item, store, from_loc, qty, action_type, plan, ref, rationale, vendor_no: str = "") -> dict[str, Any]:
    evidence = {k: plan[k] for k in ("onhand", "transit", "avg", "doc", "target", "need", "wh_avail", "constrained")}
    unit_cost = asst.gw.unit_cost(item["itemNo"])
    created = asst.gw.create_proposal(
        scenario="StoreReplenishment", action_type=action_type, item_no=item["itemNo"], from_loc=from_loc, to_loc=store,
        quantity=qty, reference_key=ref, rationale=rationale, priority=max(0, min(100, int(100 - plan["doc"] * 10))) if plan["doc"] < 9999 else 50,
        evidence=evidence, run_id=asst.run_id, model_name=asst.model_name, vendor_no=vendor_no)
    prop = {"proposal_id": created.get("proposalId") or str(uuid.uuid4()), "bc_id": created["id"], "scenario": "StoreReplenishment",
            "action_type": action_type, "status": "Proposed", "item_no": item["itemNo"], "from_loc": from_loc, "to_loc": store,
            "vendor_no": vendor_no,
            "quantity": qty, "max_quantity": plan["wh_avail"] if from_loc == asst.gw.central_wh else qty, "rationale": rationale,
            "evidence": evidence, "requested_by": user["user_id"], "created_at": asst.mem.now().isoformat(), "item_desc": item["description"],
            "value_vnd": qty * unit_cost, "item_category": item.get("category", "")}
    asst.mem.save_proposal(prop)
    return prop


def proposal_card(prop: dict[str, Any], item_desc: str, plan: dict[str, Any] | None = None, escalate: bool = False) -> Card:
    mua = prop.get("action_type") == "Purchase"
    if mua:
        # Dakao mua thang tu Marou (15/09/2026): duyet thi BC tao Purchase Order Open cho vendor, giao toi cua hang.
        facts = [("Mặt hàng", f"{item_desc} ({prop['item_no']})"), ("Mua từ", prop.get("vendor_no") or prop["from_loc"]),
                 ("Giao đến", prop["to_loc"]), ("Số lượng", fmt_qty(prop["quantity"]))]
    else:
        facts = [("Mặt hàng", f"{item_desc} ({prop['item_no']})"), ("Từ", prop["from_loc"]), ("Đến", prop["to_loc"]), ("Số lượng", fmt_qty(prop["quantity"]))]
    if plan:
        facts += [("Tồn store / ngày", f"{fmt_qty(plan['onhand'])} / {plan['doc']} ngày"), ("Bán bình quân", f"{plan['avg']:.1f}/ngày")]
        if not mua:
            facts.append(("Kho còn", fmt_qty(plan["wh_avail"])))
    if escalate:
        return Card(title="Cần nguồn hàng", body=prop["rationale"], facts=facts, ref=prop["proposal_id"], kind="info",
                    actions=[Action("ack", "Đã nhận", "positive")])
    from ..bc_link import link
    loc = {"Item No.": prop["item_no"], "Location Code": prop["to_loc"]}
    links = [("Dòng journal LS", link("ls_transfer_journal_details", {"Replenishment Template Code": "MAROU-PO" if mua else "MAROU-TO", **loc})),
             ("Replen. Item Quantities", link("ls_item_quantities", loc)),
             ("Trang NWV Agent Proposals", link("agent_proposals"))]
    return Card(title="Đề xuất đặt mua" if mua else "Đề xuất chuyển hàng", body=prop["rationale"], facts=facts, ref=prop["proposal_id"], links=links,
                actions=[Action("approve", "Duyệt đặt mua" if mua else "Duyệt chuyển hàng", "positive"),
                         Action("edit", "Sửa số lượng", needs_input="quantity"),
                         Action("reject", "Từ chối", "destructive", needs_input="reason")]
                + ([Action("ls_vi_sao", "Vì sao LS ra số này", payload={"item_no": prop["item_no"], "store": prop["to_loc"]})]
                   if plan and plan.get("nguon") else []))


def _to_dispatchers(asst, prop, item, plan, escalate=False) -> list[Delivery]:
    """Day la cho workflow thanh agent: policy quyet dinh tu lam hay hoi."""
    decision = asst.policy.decide(prop)
    prop["policy_rule"] = decision.rule_code
    prop["policy_mode"] = decision.mode.value
    asst.mem.save_proposal(prop)
    roles = ["dispatcher", "supply_chain"] if escalate else ["dispatcher"]
    recipients = [u for role in roles for u in asst.mem.users_by_role(role)]

    if decision.is_auto:
        return _auto_execute(asst, prop, item, decision, recipients)

    card = proposal_card(prop, item["description"], plan, escalate)
    if decision.shadow:
        card.body = f"[Shadow mode] Nếu được phép tôi đã tự làm việc này ({decision.rule_code}). Giờ vẫn chờ bạn duyệt.\n" + card.body
    head = "Cần nguồn hàng" if escalate else "Đề xuất mới"
    return [Delivery(u["user_id"], f"{head} từ {prop['to_loc']} — {decision.reason}", card, SKILL, prop["proposal_id"]) for u in recipients]


def _auto_execute_nondoc(asst, prop, item, decision, recipients, label) -> list[Delivery]:
    """Viec tro ly tu lam nhung khong sinh chung tu chuyen hang: chan mua, danh dau ra soat.
    Khong bao kho, khong dat follow-up ship."""
    prop.update({"status": "Executed", "approver": f"agent:{decision.rule_code}",
                 "approved_at": asst.mem.now().isoformat(), "result_doc": ""})
    asst.mem.save_proposal(prop)
    asst.policy.note_auto()
    card = Card(title=f"Đã tự xử lý: {label}",
                body=f"{prop['rationale']}\n\nTôi tự làm theo policy {decision.rule_code} ({decision.reason}). Gỡ lại được bất kỳ lúc nào.",
                facts=[("Mặt hàng", f"{item['description']} ({prop['item_no']})"), ("Việc đã làm", label),
                       ("Kho", prop["from_loc"] or "-"), ("Policy", decision.rule_code)],
                ref=prop["proposal_id"], kind="info", actions=[Action("ack", "OK")])
    return [Delivery(u["user_id"], f"Đã tự xử lý: {label} — {item['description']}", card, SKILL, prop["proposal_id"]) for u in recipients]


def _auto_execute(asst, prop, item, decision, recipients) -> list[Delivery]:
    """Tro ly tu tao Transfer Order, roi BAO SAU kem nut hoan tac."""
    agent_user = asst.agent_bc_user
    res = asst.gw.execute_auto(prop["bc_id"], agent_user, decision.rule_code)
    to_no = res.get("resultDocumentNo", "")
    if not to_no:
        return _auto_execute_nondoc(asst, prop, item, decision, recipients, res.get("resultDocumentType", ""))
    prop.update({"status": "Executed", "approver": f"agent:{decision.rule_code}",
                 "approved_at": asst.mem.now().isoformat(), "result_doc": to_no})
    asst.mem.save_proposal(prop)
    asst.policy.note_auto()

    card = Card(title=f"Đã tự xử lý: {to_no}",
                body=f"{prop['rationale']}\n\nTôi tự làm theo policy {decision.rule_code} ({decision.reason}). Bạn hoàn tác được khi kho chưa ship.",
                facts=[("Mặt hàng", f"{item['description']} ({prop['item_no']})"), ("Từ", prop["from_loc"]), ("Đến", prop["to_loc"]),
                       ("Số lượng", fmt_qty(prop["quantity"])), ("Giá trị", fmt_vnd(prop.get("value_vnd", 0))),
                       ("Policy", decision.rule_code)],
                ref=prop["proposal_id"], kind="info",
                actions=[Action("undo", "Hoàn tác", "destructive"), Action("ack", "OK")])
    out = [Delivery(u["user_id"], f"Đã tự xử lý bổ sung cho {prop['to_loc']}", card, SKILL, prop["proposal_id"]) for u in recipients]

    item_desc = item["description"]
    for u in asst.mem.users():
        if u["role"] == "store_manager" and u.get("store_code") == prop["to_loc"]:
            out.append(Delivery(u["user_id"], f"Tôi đã lên đơn {to_no}: {fmt_qty(prop['quantity'])} {item_desc} từ {prop['from_loc']}. Dự kiến về ngày mai.", skill=SKILL, ref=to_no))
    ship_card = Card(title=f"Cần ship {to_no}", facts=[("Mặt hàng", item_desc), ("Số lượng", fmt_qty(prop["quantity"])), ("Đến", prop["to_loc"])],
                     body="Transfer Order tạo tự động theo policy. Release, pick và ship theo quy trình.",
                     ref=to_no, kind="info", actions=[Action("ship", "Đã ship", "positive")])
    for w in asst.mem.users_by_role("warehouse"):
        out.append(Delivery(w["user_id"], f"{to_no} cần ship hôm nay", ship_card, SKILL, to_no))
    now = asst.mem.now()
    asst.mem.add_followup("transfer_ship", to_no, now + timedelta(hours=18), notify_user="role:warehouse",
                          escalate_user=recipients[0]["user_id"] if recipients else "", note=prop["proposal_id"])
    asst.mem.add_followup("outcome_check", prop["proposal_id"], now + timedelta(days=14), notify_user=recipients[0]["user_id"] if recipients else "", note=to_no)
    return out


def on_undo(asst, user, prop, payload) -> list[Delivery]:
    to_no = prop.get("result_doc") or ""
    if not asst.gw.undo_transfer(to_no, user.get("bc_user") or user["user_id"]):
        return [Delivery(user["user_id"], f"Không hoàn tác được {to_no}: kho đã ship rồi. Bạn xử lý bằng đơn trả.", skill=SKILL, ref=to_no)]
    prop.update({"status": "Rejected", "approver": user["user_id"], "approved_at": asst.mem.now().isoformat()})
    asst.mem.save_proposal(prop)
    asst.mem.log_feedback(prop["proposal_id"], "undo", payload.get("reason", ""), user["user_id"])
    out = [Delivery(user["user_id"], f"Đã hủy {to_no}. Tôi ghi lại để chỉnh policy {prop.get('policy_rule', '')}.", skill=SKILL, ref=to_no)]
    for w in asst.mem.users_by_role("warehouse"):
        out.append(Delivery(w["user_id"], f"{to_no} đã hủy, không ship nữa.", skill=SKILL, ref=to_no))
    return out


# ---------- hanh dong tren the

def on_approve(asst, user, prop, payload) -> list[Delivery]:
    res = asst.gw.approve(prop["bc_id"], user.get("bc_user") or user["user_id"], payload.get("comment", ""))
    to_no = res.get("resultDocumentNo", "")
    prop.update({"status": "Executed", "approver": user["user_id"], "approved_at": asst.mem.now().isoformat(), "result_doc": to_no})
    asst.mem.save_proposal(prop)
    item_desc = asst.gw.find_item(prop["item_no"])["description"]
    if prop.get("action_type") == "WriteOff" and res.get("resultDocumentType") == "Item Journal Line" and to_no:
        # UC2 G2/A3 (16/09/2026): BC tao dong Item Journal nhap; tro ly soan bien ban, email bo phan post, theo doi den khi post.
        from . import uc2_huy
        prop["item_desc"] = prop.get("item_desc") or item_desc
        return uc2_huy.on_duyet_huy(asst, user, prop, res)
    if not to_no:
        # De xuat khong sinh chung tu chuyen hang (chan mua, giam gia, ra soat): khong bao kho.
        label = res.get("resultDocumentType", prop["action_type"])
        return [Delivery(user["user_id"], f"Đã duyệt: {label} cho {item_desc}. Ghi dưới tên {user['display_name']}. Việc này không sinh Transfer Order nên tôi không báo kho.", skill=SKILL, ref=prop["proposal_id"])]
    if prop.get("action_type") == "Purchase" or res.get("resultDocumentType") == "Purchase Order":
        # Don mua tu vendor giao thang cua hang: khong co kho nao phai ship, nguoi mua xem lai roi gui don cho Marou.
        from ..bc_link import link
        prop["vendor_no"] = prop.get("vendor_no") or res.get("vendorNo") or ""
        card = Card(title=f"Đã tạo Purchase Order {to_no}", kind="info", ref=to_no,
                    facts=[("Mặt hàng", item_desc), ("Số lượng", fmt_qty(prop["quantity"])), ("Mua từ", prop.get("vendor_no") or ""),
                           ("Giao đến", prop["to_loc"]), ("Trạng thái", "Open, chưa release")],
                    body="Purchase Order tạo dưới tên người duyệt, trạng thái Open. Người mua xem lại rồi release và gửi cho nhà cung cấp; "
                         "trợ lý không post gì.",
                    links=[("Mở Purchase Order trong BC", link("purchase_order", {"Document Type": "Order", "No.": to_no}))])
        out = [Delivery(user["user_id"], f"Đã duyệt. Purchase Order {to_no} tạo dưới tên {user['display_name']}, trạng thái Open, "
                                         f"mua {fmt_qty(prop['quantity'])} {item_desc} từ {prop.get('vendor_no') or ''} giao đến {prop['to_loc']}.",
                        card=card, skill=SKILL, ref=prop["proposal_id"])]
        for rid in sorted({u["user_id"] for u in asst.mem.users() if u["role"] == "store_manager" and u.get("store_code") == prop["to_loc"]} - {user["user_id"]}):
            out.append(Delivery(rid, f"Điều phối đã duyệt đặt mua {fmt_qty(prop['quantity'])} {item_desc} từ {prop.get('vendor_no') or 'nhà cung cấp'}, "
                                     f"đơn {to_no}, giao thẳng tới {prop['to_loc']}.", skill=SKILL, ref=to_no))
        return out
    out = [Delivery(user["user_id"], f"Đã duyệt. Transfer Order {to_no} tạo dưới tên {user['display_name']}, trạng thái Open. Tôi báo kho và cửa hàng.", skill=SKILL, ref=prop["proposal_id"])]
    # bao cua hang: nguoi yeu cau (neu la user that) va quan ly cua store nhan
    recipients = {u["user_id"] for u in asst.mem.users() if u["role"] == "store_manager" and u.get("store_code") == prop["to_loc"]}
    if asst.mem.user(prop["requested_by"]):
        recipients.add(prop["requested_by"])
    recipients.discard(user["user_id"])
    for rid in sorted(recipients):
        out.append(Delivery(rid, f"Điều phối đã duyệt: chuyển {fmt_qty(prop['quantity'])} {item_desc} từ {prop['from_loc']}, đơn {to_no}. Dự kiến hàng về ngày mai. Tôi sẽ báo khi kho ship.", skill=SKILL, ref=to_no))
    store_user = next(iter(recipients), prop["requested_by"])
    ship_card = Card(title=f"Cần ship {to_no}", facts=[("Mặt hàng", item_desc), ("Số lượng", fmt_qty(prop["quantity"])), ("Đến", prop["to_loc"])],
                     body="Transfer Order đã tạo ở trạng thái Open. Release, pick và ship theo quy trình; bấm Đã ship khi xong.",
                     ref=to_no, kind="info", actions=[Action("ship", "Đã ship", "positive")])
    for w in asst.mem.users_by_role("warehouse"):
        out.append(Delivery(w["user_id"], f"{to_no} cần ship hôm nay", ship_card, SKILL, to_no))
    now = asst.mem.now()
    asst.mem.add_followup("transfer_ship", to_no, now + timedelta(hours=18), notify_user="role:warehouse", escalate_user=user["user_id"], note=prop["proposal_id"])
    asst.mem.add_followup("transfer_receive", to_no, now + timedelta(hours=48), notify_user=store_user, note=prop["proposal_id"])
    return out


def on_edit(asst, user, prop, payload) -> list[Delivery]:
    try:
        qty = float(payload.get("quantity", 0))
    except (TypeError, ValueError):
        return [Delivery(user["user_id"], "Số lượng không hợp lệ.", skill=SKILL)]
    if qty <= 0 or qty > float(prop["max_quantity"]):
        return [Delivery(user["user_id"], f"Số lượng phải trong khoảng 1 đến {fmt_qty(prop['max_quantity'])} (tồn khả dụng tại {prop['from_loc']}).", skill=SKILL)]
    asst.gw.client.patch("agentProposals", prop["bc_id"], {"quantity": qty})
    prop["quantity"] = qty
    asst.mem.save_proposal(prop)
    return on_approve(asst, user, prop, {"comment": f"Sửa số thành {fmt_qty(qty)}"})


def on_reject(asst, user, prop, payload) -> list[Delivery]:
    reason = payload.get("reason", "") or "không nêu lý do"
    asst.gw.reject(prop["bc_id"], user.get("bc_user") or user["user_id"], reason)
    # Ly do tu choi luu vao outcome_note de brief hom sau nho (S1: "da tu choi hom X vi Y, khong de xuat lai").
    prop.update({"status": "Rejected", "approver": user["user_id"], "approved_at": asst.mem.now().isoformat(), "outcome_note": reason})
    asst.mem.save_proposal(prop)
    return [Delivery(user["user_id"], f"Đã từ chối, lý do: {reason}. Tôi ghi lại để chỉnh ngưỡng.", skill=SKILL, ref=prop["proposal_id"]),
            Delivery(prop["requested_by"], f"Điều phối chưa duyệt chuyển {prop['item_no']}: {reason}.", skill=SKILL, ref=prop["proposal_id"])]


def on_ship(asst, user, ref, payload) -> list[Delivery]:
    asst.gw.mark_transfer(ref, shipped=True)
    t = asst.gw.transfer(ref)
    for f in asst.mem.followups():
        if f["kind"] == "transfer_ship" and f["ref"] == ref and f["status"] == "open":
            asst.mem.update_followup(f["id"], status="done")
    out = [Delivery(user["user_id"], f"Đã ghi nhận {ref} ship.", skill=SKILL, ref=ref)]
    for u in asst.mem.users():
        if u.get("store_code") == t["toLocationCode"] and u["role"] == "store_manager":
            out.append(Delivery(u["user_id"], f"Kho đã ship {ref} ({fmt_qty(t['quantity'])} {t['itemNo']}). Nhận hàng xong bạn nhắn tôi một câu.", skill=SKILL, ref=ref))
    return out


def stock_query(asst, user, intent) -> list[Delivery]:
    item = asst.gw.find_item(intent.item_text) if intent.item_text else None
    if not item:
        return [Delivery(user["user_id"], "Bạn hỏi mặt hàng nào?", skill=SKILL, meta={"unresolved": True})]
    rows = asst.gw.stock_by_location(item["itemNo"])
    # Hoi mot cua hang cu the thi chi tra cua hang do; ma khong co trong du lieu thi van tra het kem mot cau noi ro.
    hint, ghi_chu = getattr(intent, "store_hint", "") or "", ""
    if hint:
        chon = [r for r in rows if r["locationCode"] == hint]
        if chon:
            rows = chon
        else:
            ghi_chu = f" Không có dòng tồn nào tại {hint}, tôi liệt kê các địa điểm đang có."
    lines = [f"{r['locationCode']}: {fmt_qty(r['qty'])}" + (f" ({r['daysOfCover']} ngày)" if r["daysOfCover"] < 9999 else "") for r in rows]
    # Quan ly cua hang hoi "o cua hang toi" ma khong go ma: noi cua hang minh truoc. Cua hang het sach thi khong co dong ton
    # nao, truoc 14/09/2026 cau tra loi liet ke cac noi khac ma khong nhac cua hang minh (Lan hoi Choco nuts tai S0001 = 0).
    minh = user.get("store_code") if user.get("role") == "store_manager" and not hint else ""
    if minh:
        cua_minh = next((r for r in rows if r["locationCode"] == minh), None)
        dau = (f"{item['description']} tại {minh} còn {fmt_qty(cua_minh['qty'])}"
               + (f", đủ {cua_minh['daysOfCover']} ngày" if cua_minh["daysOfCover"] < 9999 else "") + "."
               if cua_minh else f"{item['description']} tại {minh} đã hết, không còn dòng tồn nào.")
        khac = [l for r, l in zip(rows, lines) if r["locationCode"] != minh]
        return [Delivery(user["user_id"], dau + (" Nơi khác: " + "; ".join(khac) + "." if khac else ""), skill=SKILL)]
    return [Delivery(user["user_id"], f"{item['description']}: " + "; ".join(lines) + "." + ghi_chu, skill=SKILL)]


def _nap_de_xuat_cu(asst, p: dict[str, Any], plan: dict[str, Any], user: dict[str, Any]) -> dict[str, Any]:
    """Dua mot de xuat doc tu BC vao bo nho tro ly, de nut Duyet tren the tim thay no.

    `handle_action` tra de xuat trong bo nho theo `proposal_id`; de xuat tao o phien truoc chi
    con trong BC nen bam Duyet se ra "Khong tim thay de xuat"."""
    prop = dict(p)
    ev = prop.get("evidence") or prop.get("evidenceJson") or {}
    if isinstance(ev, str):
        try:
            ev = json.loads(ev or "{}")
        except ValueError:
            ev = {}
    prop["evidence"] = ev
    prop["scenario"] = prop.get("scenario") or "StoreReplenishment"
    prop["requested_by"] = prop.get("requested_by") or user["user_id"]
    prop["max_quantity"] = plan["wh_avail"] if prop.get("from_loc") == asst.gw.central_wh else prop.get("quantity")
    asst.mem.save_proposal(prop)
    return prop


def brief_for_dispatcher(asst, user) -> list[Delivery]:
    rows = asst.gw.risky_suggestions(10)
    if not rows:
        return [Delivery(user["user_id"], "Sáng nay không có store nào dưới ngưỡng.", skill=SKILL)]
    # De xuat con hieu luc, doc ca BC lan bo nho: bo nho bi dung moi lan khoi dong lai, con BC
    # thi giu. de_xuat_gop da xep moi nhat len truoc nen setdefault giu ban moi nhat.
    dang_co: dict[str, dict[str, Any]] = {}
    for p in asst.de_xuat_gop():
        if p.get("status") in ("Proposed", "Executed"):
            dang_co.setdefault(f"{p.get('to_loc')}|{p.get('item_no')}", p)

    the: list[Delivery] = []
    moi = cho = dang_di = het_kho = mua = 0
    for r in rows:
        store, ma, ten = r["storeLocationCode"], r["itemNo"], r["itemDescription"]
        cu = dang_co.get(f"{store}|{ma}")
        # De xuat chuyen hang cu (tao khi cua hang con lay tu kho tong) khong che dong mua thang tu vendor: o Dakao bang
        # de xuat sao chep tu NWV con 22 dong Proposed, neu de `cu` thang thi brief chi thay "cho duyet" cua the gioi cu.
        if cu and cu["status"] == "Executed" and r.get("replenType") != "Purchase":
            dang_di += 1                         # hang dang tren duong, khong de xuat chong len
            continue
        plan = _plan(asst.gw, store, ma, 0)
        if cu and r.get("replenType") != "Purchase":
            # Truoc day nhanh nay `continue` im lang: ca 10 dong da co de xuat tu lan brief truoc
            # nen dieu phoi chi thay cau mo dau "ban duyet tung dong:" roi khong co the nao.
            # Dung bat duoc ngay 13/09/2026. Viec chua duyet thi phai hien lai, khong tao them.
            prop = _nap_de_xuat_cu(asst, cu, plan, user)
            ngay = str(cu.get("created_at") or "")[:10]
            nhan = f"{store} / {ten} · chờ duyệt" + (f" từ {ngay[8:10]}/{ngay[5:7]}" if len(ngay) == 10 else "")
            the.append(Delivery(user["user_id"], nhan, proposal_card(prop, ten, plan), SKILL, prop["proposal_id"]))
            cho += 1
            continue
        if r.get("replenType") == "Purchase":
            # Dakao (15/09/2026): LS de xuat mua thang tu vendor MAROU, giao toi cua hang. De xuat loai Purchase; duyet thi
            # BC tao Purchase Order Open cho vendor (codeunit NWV Agent Proposal Mgt., app 1.5.3.0).
            if cu and cu.get("action_type") == "Purchase":
                prop = _nap_de_xuat_cu(asst, cu, plan, user)
                ngay = str(cu.get("created_at") or "")[:10]
                nhan = f"{store} / {ten} · chờ duyệt" + (f" từ {ngay[8:10]}/{ngay[5:7]}" if len(ngay) == 10 else "")
                the.append(Delivery(user["user_id"], nhan, proposal_card(prop, ten, plan), SKILL, prop["proposal_id"]))
                cho += 1
                continue
            mua += 1
            item = {"itemNo": ma, "description": ten}
            fake_user = {"user_id": f"brief:{store}", "store_code": store}
            prop = _create(asst, fake_user, item, store, "", float(r["suggestedQty"]), "Purchase", plan, f"{store}|{ma}",
                           r["reason"], vendor_no=r.get("vendorNo") or "")
            prop["requested_by"] = user["user_id"]
            asst.mem.save_proposal(prop)
            the.append(Delivery(user["user_id"], f"{store} / {ten} · mua từ {r.get('vendorNo') or ''}", proposal_card(prop, ten, plan),
                                SKILL, prop["proposal_id"]))
            continue
        if plan["constrained"] <= 0:
            het_kho += 1
            continue
        item = {"itemNo": ma, "description": ten}
        fake_user = {"user_id": f"brief:{store}", "store_code": store}
        prop = _create(asst, fake_user, item, store, asst.gw.central_wh, plan["constrained"], "Transfer", plan,
                       f"{store}|{ma}", r["reason"])
        prop["requested_by"] = user["user_id"]
        asst.mem.save_proposal(prop)
        the.append(Delivery(user["user_id"], f"{store} / {ten}", proposal_card(prop, ten, plan), SKILL, prop["proposal_id"]))
        moi += 1

    # Cau mo dau ke dung cai dang hien ben duoi, khong hua "duyet tung dong" khi khong co dong nao.
    phan = []
    if moi:
        phan.append(f"{moi} đề xuất mới")
    if cho:
        phan.append(f"{cho} đề xuất tạo trước đó vẫn chờ bạn duyệt")
    if dang_di:
        phan.append(f"{dang_di} dòng đã có chuyến hàng đang đi")
    if het_kho:
        phan.append(f"{het_kho} dòng kho trung tâm hết hàng, cần mua thêm")
    if mua:
        phan.append(f"{mua} đề xuất đặt mua thẳng từ nhà cung cấp, giao tới cửa hàng")
    tu_ls = bool(rows) and rows[0].get("demandBasis") == "LS"
    dau = ((f"Sáng nay LS Replenishment đề xuất bổ sung cho {len(rows)} dòng: " if tu_ls
            else f"Sáng nay {len(rows)} dòng dưới ngưỡng {REORDER_DOC} ngày: ") + "; ".join(phan) + ".")
    if moi or cho or mua:
        dau += " Bạn duyệt từng thẻ bên dưới."
    else:
        dau += " Không còn việc nào cần bạn duyệt."
    return [Delivery(user["user_id"], dau, skill=SKILL)] + the
