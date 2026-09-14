"""UC2 Traceability: hanh trinh cua mot lo tu Item Ledger Entry. Khong goi model, khong ghi gi vao BC.

Vi sao co file nay (14/09/2026). RFP UC2 doi "traceability view". Lo co dau vet day du trong Item Ledger Entry (nhap,
chuyen, ban, huy) vi du lieu demo da post lai co lot tracking. Tro ly gom theo dia diem va loai but toan, noi ro con bao
nhieu o dau, da ban bao nhieu, va neu phai thu hoi thi can lay lai tu nhung dia diem nao. Moi con so la tong Quantity
cua dong Item Ledger Entry, khong tinh lai gi khac.
"""
from __future__ import annotations

import re
from collections import defaultdict
from typing import Any

from bc_agent.bc_data import unescape_option

from ..bc_link import link
from ..cards import Card, fmt_qty
from . import Delivery

SKILL = "truy_xuat"
_MA_LO = re.compile(r"\b(L\d{6}-[A-Z0-9-]+)\b", re.I)
# Bo du lieu demo ghi hang ve cua hang bang Positive Adjmt. va hang ra kho bang Negative Adjmt. (khong dung Transfer Order),
# nen hai loai nay goi trung tinh la nhan va xuat, khong goi la chuyen hay huy.
TEN_LOAI = {"Purchase": "nhập mua", "Positive Adjmt.": "nhận", "Output": "sản xuất", "Transfer": "chuyển",
            "Sale": "bán", "Negative Adjmt.": "xuất", "Consumption": "tiêu hao"}


def _vn(iso: str) -> str:
    """2026-09-13 thanh 13/09/2026. Chuoi khong dung dang thi tra nguyen."""
    m = re.fullmatch(r"(\d{4})-(\d{2})-(\d{2})", iso or "")
    return f"{m.group(3)}/{m.group(2)}/{m.group(1)}" if m else (iso or "")


def ma_lo(text: str) -> str:
    m = _MA_LO.search(text or "")
    return m.group(1).upper() if m else ""


def hanh_trinh(rows: list[dict[str, Any]]) -> dict[str, Any]:
    """Gom dong Item Ledger Entry cua mot lo. Tra ve so theo dia diem va moc thoi gian."""
    noi: dict[str, dict[str, float]] = defaultdict(lambda: defaultdict(float))
    moc = []
    han = ""
    item = ""
    for r in sorted(rows, key=lambda r: (str(r.get("postingDate")), int(r.get("entryNo") or 0))):
        loai = unescape_option(r.get("entryType")) or ""
        q = float(r.get("quantity") or 0)
        loc = r.get("locationCode") or ""
        noi[loc][loai] += q
        noi[loc]["_ton"] += q
        item = item or r.get("itemNo") or ""
        if r.get("expirationDate") and str(r["expirationDate"])[:4] > "0001":
            han = str(r["expirationDate"])[:10]
        moc.append((str(r.get("postingDate"))[:10], loc, loai, q))
    return {"item": item, "han": han, "noi": {k: dict(v) for k, v in noi.items()}, "moc": moc}


def handle(asst: Any, user: dict[str, Any], text: str) -> list[Delivery]:
    uid = user["user_id"]
    lo = ma_lo(text)
    if not lo:
        return [Delivery(uid, "Bạn cho tôi số lô, ví dụ: \"truy xuất lô L260908-33170B\".", skill=SKILL, meta={"unresolved": True})]
    rows = asst.gw.ile_theo_lo(lo)
    if not rows:
        return [Delivery(uid, f"Không có dòng Item Ledger Entry nào của lô {lo}.", skill=SKILL)]
    h = hanh_trinh(rows)
    ten = next((i["description"] for i in asst.gw.items() if i["itemNo"] == h["item"]), h["item"])
    body = []
    con_ton = []
    tong_ban = 0.0
    for loc, s in sorted(h["noi"].items(), key=lambda kv: -abs(kv[1].get("_ton", 0))):
        phan = [f"{TEN_LOAI.get(k, k)} {fmt_qty(abs(v))}" for k, v in s.items() if not k.startswith("_") and v]
        ton = s.get("_ton", 0)
        tong_ban += -s.get("Sale", 0)
        body.append(f"· {loc}: " + ", ".join(phan) + f"; còn {fmt_qty(ton)}.")
        if ton > 0.0001:
            con_ton.append((loc, ton))
    dau = h["moc"][0] if h["moc"] else None
    cuoi = h["moc"][-1] if h["moc"] else None
    han = _vn(h["han"]) or "không ghi"
    try:
        qua_han = bool(h["han"]) and h["han"] < asst.gw.today().isoformat()
    except Exception:                                  # khong co ngay neo thi khong ket luan qua han
        qua_han = False
    if qua_han and con_ton:
        han += " (đã quá hạn, lô còn tồn)"
    cau = (f"Lô {lo} ({ten}), hạn dùng {han}: nhập lần đầu {_vn(dau[0]) if dau else ''} tại {dau[1] if dau else ''}, "
           f"đã bán {fmt_qty(tong_ban)}, "
           + ("còn " + ", ".join(f"{fmt_qty(t)} tại {l}" for l, t in con_ton) if con_ton else "không còn tồn ở đâu") + ".")
    if con_ton:
        body.append("Nếu phải thu hồi: lấy lại " + ", ".join(f"{fmt_qty(t)} tại {l}" for l, t in con_ton)
                    + f". {fmt_qty(tong_ban)} đã bán cho khách không thu lại được từ tồn kho.")
    body.append(f"{len(h['moc'])} dòng Item Ledger Entry, dòng cuối ngày {_vn(cuoi[0]) if cuoi else ''}.")
    card = Card(title=f"Hành trình lô {lo}", body="\n".join(body),
                facts=[("Mặt hàng", f"{ten} ({h['item']})"), ("Hạn dùng", han),
                       ("Đã bán", fmt_qty(tong_ban)), ("Còn tồn", fmt_qty(sum(t for _, t in con_ton)))],
                ref=f"lo|{lo}", kind="info",
                links=[("Item Ledger Entries của lô", link("item_ledger_entries", {"Item No.": h["item"], "Lot No.": lo})),
                       ("Lot No. Information", link("lot_info_list", {"Item No.": h["item"], "Lot No.": lo}))])
    return [Delivery(uid, cau, card=card, skill=SKILL, ref=f"lo|{lo}")]
