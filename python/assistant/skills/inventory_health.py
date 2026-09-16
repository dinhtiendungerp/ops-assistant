"""Skill Inventory Health (UC2): brief cho Supply Chain, de xuat theo tier, hoi cua hang xac nhan hang hong."""
from __future__ import annotations

import uuid
from typing import Any

from ..bc_link import link
from ..cards import Action, Card, fmt_qty, fmt_vnd
from . import Delivery

SKILL = "inventory_health"
ACTION_BY_TIER = {"Expired": "WriteOff", "NearExpiry": "Markdown", "SlowMoving": "Markdown", "Excess": "BlockPurchase", "StockOutRisk": "ReviewOnly"}


def line_card(r: dict[str, Any]) -> Card:
    act = ACTION_BY_TIER.get(r["tier"], "ReviewOnly")
    label = {"WriteOff": "Đề xuất hủy", "Markdown": "Đề xuất giảm giá", "BlockPurchase": "Chặn mua thêm", "ReviewOnly": "Ghi nhận"}[act]
    facts = [("Tier", f"{r['tier']} (điểm {r['riskScore']})"), ("Kho / lot", f"{r['locationCode']} / {r.get('lotNo', '')}"),
             ("Tồn", f"{fmt_qty(r['quantityOnHand'])} ({fmt_vnd(r['inventoryValue'])})"),
             ("Days of cover", str(r["daysOfCover"])), ("Hạn dùng", f"{r.get('expirationDate', '')} ({r.get('daysToExpiry')} ngày)")]
    actions = [Action("ih_propose", label, "positive", payload={"action_type": act})]
    if r["tier"] == "NearExpiry":
        actions.append(Action("ih_transfer_fast", "Phương án xử lý"))
    return Card(title=f"{r['itemDescription']}: {r['riskReason']}", facts=facts, ref=r["id"], kind="info", actions=actions,
                links=links_lo(r))


def links_lo(r: dict) -> list[tuple[str, str]]:
    """Mo dung dong Item Ledger Entry cua lo va dong Inventory Health trong BC."""
    loc = {"Item No.": r["itemNo"], "Location Code": r["locationCode"], "Lot No.": r.get("lotNo") or ""}
    return [("Item Ledger Entries của lô", link("item_ledger_entries", loc)),
            ("Dòng Inventory Health", link("inventory_health", loc))]


def brief_for_supply_chain(asst, user) -> list[Delivery]:
    """S1 (15/09/2026): the tom tat do AI viet len dau (3 viec quan trong nhat, ly do, nho ly do tu choi gan day), roi the tung
    dong nhu truoc. Tat AI thi the tom tat do code ghep, van cung hinh."""
    from . import uc2_tom_tat
    out = uc2_tom_tat.brief_ai(asst, user)
    if not out:
        return [Delivery(user["user_id"], "Không có dòng tồn kho nào vượt ngưỡng.", skill=SKILL)]
    return out


_CAN_DATE = ("sắp hết hạn", "sap het han", "cận date", "can date", "gần hết hạn", "gan het han", "cận hạn", "can han",
             "sắp hết date", "sap het date")


def het_han(asst, user, intent, text: str) -> list[Delivery]:
    """Hoi lo nao da het han hoac sap het han. Doc bang Inventory Health da tinh, khong goi model.

    Ngay 14/09/2026 Hung (dieu phoi kho) hoi "co mat hang nao da het han chua": "het" roi vao STOCKOUT, ma dieu phoi khong
    gan cua hang nao nen tro ly hoi lai "ban thuoc cua hang nao". Vai tro co dia diem (cua hang, kho) chi thay dia diem
    minh; vai tro dieu phoi, Supply Chain, Retail Ops, admin thay het, tru khi cau co ma dia diem."""
    uid = user["user_id"]
    thap = text.lower()
    tang = ("NearExpiry",) if any(k in thap for k in _CAN_DATE) else ("Expired",)
    ten_tang = "sắp hết hạn" if tang == ("NearExpiry",) else "đã hết hạn"
    noi = getattr(intent, "store_hint", "") or user.get("store_code") or ""
    rows = [r for r in asst.gw.doc("inventoryHealthLines", [], top=5000) if r.get("tier") in tang]
    if noi:
        rows = [r for r in rows if r.get("locationCode") == noi]
    # Chi loc theo mat hang khi chu con lai thuc su la ten mat hang (diem cao), khong de "mat hang nao" khop bua.
    item = asst.gw.find_item(intent.item_text, min_score=80) if (getattr(intent, "item_text", "") or "").strip() else None
    if item:
        rows = [r for r in rows if r.get("itemNo") == item["itemNo"]]
    pham_vi = (f" tại {noi}" if noi else " ở mọi địa điểm") + (f" cho {item['description']}" if item else "")
    if not rows:
        return [Delivery(uid, f"Không có lô nào {ten_tang}{pham_vi} theo bảng Inventory Health.", skill=SKILL)]
    rows.sort(key=lambda r: -float(r.get("inventoryValue") or 0))
    tong_sl = sum(float(r.get("quantityOnHand") or 0) for r in rows)
    tong_gt = sum(float(r.get("inventoryValue") or 0) for r in rows)
    theo_noi: dict[str, int] = {}
    for r in rows:
        theo_noi[r["locationCode"]] = theo_noi.get(r["locationCode"], 0) + 1
    chia = "" if noi else " Theo địa điểm: " + ", ".join(f"{k} {v} lô" for k, v in sorted(theo_noi.items())) + "."
    duoi = ("Từng lô ở bên dưới" if len(rows) <= 5 else "5 lô giá trị lớn nhất ở bên dưới") + ", bấm để ghi đề xuất cho người duyệt."
    out = [Delivery(uid, f"{len(rows)} lô {ten_tang}{pham_vi}, tổng tồn {fmt_qty(tong_sl)}, giá trị {fmt_vnd(tong_gt)}.{chia} {duoi}",
                    skill=SKILL)]
    for r in rows[:5]:
        out.append(Delivery(uid, r["itemDescription"], line_card(r), SKILL, r["id"]))
    return out


def on_propose(asst, user, line_id: str, action_type: str, to_loc: str = "", quantity: float | None = None,
               ref: str | None = None, rationale: str | None = None) -> list[Delivery]:
    """Ghi mot de xuat tu dong Inventory Health. `quantity`, `ref`, `rationale` do D4 (uc2_hanh_dong) truyen khi de xuat
    MOT PHAN lo: chuyen vua du ban truoc han, phan con lai giam gia; moi phan mot khoa rieng de khong bi coi la trung."""
    r = asst.gw.client.get("inventoryHealthLines", line_id)
    ref = ref or f"{r['itemNo']}|{r['locationCode']}|{r.get('lotNo', '')}"
    # So voi ca BC lan bo nho tro ly, xem `gw.de_xuat_dang_co`.
    # Khoa trung la item x kho x LO. Truoc day bo nho chi so item x kho, nen de xuat huy lo thu hai cua cung mat hang
    # tai cung kho bi chan nham.
    if ref in asst.gw.de_xuat_dang_co() or any(
            p["status"] == "Proposed" and p.get("channel_ref") == ref for p in asst.mem.proposals("Proposed")):
        return [Delivery(user["user_id"], "Đã có đề xuất đang chờ cho dòng này, tôi không ghi thêm bản nữa.", skill=SKILL)]
    ton = float(r["quantityOnHand"] or 0)
    qty = float(quantity) if quantity is not None else (ton if action_type in ("Transfer", "WriteOff") else 0.0)
    don_gia = float(r["inventoryValue"]) / ton if ton else 0.0
    rationale = rationale or asst.write_rationale(f"{r['tier']}: {r['riskReason']} Tồn {fmt_qty(ton)}, giá trị {fmt_vnd(r['inventoryValue'])}.")
    created = asst.gw.create_proposal(scenario="InventoryHealth", action_type=action_type, item_no=r["itemNo"], from_loc=r["locationCode"],
                                      to_loc=to_loc, quantity=qty,
                                      reference_key=ref, rationale=rationale, priority=int(r["riskScore"]),
                                      evidence={k: r[k] for k in ("quantityOnHand", "daysOfCover", "daysToExpiry", "daysSinceLastSale", "inventoryValue", "riskScore")},
                                      run_id=asst.run_id, model_name=asst.model_name, lot_no=r.get("lotNo", ""))
    prop = {"proposal_id": created.get("proposalId") or str(uuid.uuid4()), "bc_id": created["id"], "scenario": "InventoryHealth",
            "action_type": action_type, "status": "Proposed", "item_no": r["itemNo"], "from_loc": r["locationCode"], "to_loc": to_loc,
            "quantity": created.get("quantity", qty), "max_quantity": r["quantityOnHand"], "rationale": rationale, "evidence": {},
            "item_desc": r["itemDescription"], "requested_by": user["user_id"], "created_at": asst.mem.now().isoformat(),
            "channel_ref": ref, "value_vnd": round(qty * don_gia, 2), "item_category": r.get("itemCategoryCode", "")}
    decision = asst.policy.decide(prop)
    prop["policy_rule"] = decision.rule_code
    prop["policy_mode"] = decision.mode.value
    asst.mem.save_proposal(prop)
    out = [Delivery(user["user_id"], f"Đã ghi đề xuất {action_type} cho {r['itemDescription']} tại {r['locationCode']} vào BC (Proposed). "
                                     f"Tôi đã báo người duyệt ngay trong chat của họ.", skill=SKILL, ref=ref)]
    # Chat cho nguoi dang mo tro ly, email cho nguoi khong mo (Dung hoi toi 16/09/2026). Phan loi cua thu do AI soan.
    from . import thu_de_xuat
    return out + _bao_nguoi_duyet(asst, user, prop, r, decision) + thu_de_xuat.gui(asst, user, prop, r, decision)


def _bao_nguoi_duyet(asst, user, prop, r, decision) -> list[Delivery]:
    """Day the sang hop thu cua nguoi co quyen duyet.

    Truoc day de xuat chi duoc ghi vao BC roi bao lai chinh nguoi vua bam. Doi vai tro sang
    nguoi duyet thi hoi thoai trong tron, phai bam Brief moi thay. Dung chi ra ngay 13/09/2026.
    Nguoi duyet phai duoc goi, khong phai tu di tim."""
    nhan = [u for role in ("supply_chain", "dispatcher") for u in asst.mem.users_by_role(role)
            if u["user_id"] != user["user_id"]]
    if not nhan:
        return []
    nhan_hanh_dong = {"WriteOff": "Duyệt hủy", "Markdown": "Duyệt giảm giá",
                      "BlockPurchase": "Duyệt chặn mua", "Transfer": "Duyệt chuyển hàng",
                      "ReviewOnly": "Đã xem"}.get(prop["action_type"], "Duyệt")
    card = Card(
        title=f"{r['itemDescription']}: {r['riskReason']}",
        body=f"{prop['rationale']}\n\n{user['display_name']} đề nghị {prop['action_type']}. {decision.reason}",
        facts=[("Mặt hàng", f"{r['itemDescription']} ({r['itemNo']})"),
               ("Kho / lô", f"{r['locationCode']} / {r.get('lotNo', '')}"),
               ("Tồn", f"{fmt_qty(r['quantityOnHand'])} ({fmt_vnd(r['inventoryValue'])})"),
               ("Tier", f"{r['tier']} (điểm {r['riskScore']})"),
               ("Người đề nghị", user["display_name"])],
        ref=prop["proposal_id"], kind="proposal", links=links_lo(r) + [("Trang NWV Agent Proposals", link("agent_proposals"))],
        actions=[Action("approve", nhan_hanh_dong, "positive"),
                 Action("reject", "Từ chối", "destructive", needs_input="reason")])
    return [Delivery(u["user_id"], f"Đề xuất mới từ {user['display_name']} — {r['locationCode']}",
                     card, SKILL, prop["proposal_id"]) for u in nhan]


def on_transfer_fast(asst, user, line_id: str) -> list[Delivery]:
    """Nut "Phuong an xu ly" tren the lo can date. Truoc 16/09/2026 nut nay de xuat chuyen CA TON LO sang cua hang ban nhanh
    nhat, khong xet noi nhan co ban het truoc han khong. Gio la D4: code tinh tung phuong an, model so sanh, nguoi chon."""
    from . import uc2_hanh_dong
    return uc2_hanh_dong.on_goi_y(asst, user, line_id)
