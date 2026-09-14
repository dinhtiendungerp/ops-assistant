"""Tra loi "viec cua toi den dau roi" tu du lieu da co, khong goi model.

Vi sao co file nay: cot phai man hinh da hien san de xuat, chung tu chuyen hang va viec dang
theo doi, nhung hoi cung noi dung do bang cau chu thi tro ly lai bao khong tra loi duoc. Dung
chi ra cho nay ngay 13/09/2026: "cai nay cung co thong tin het roi ma".

Khong dung model o day. Toan bo cau tra loi ghep tu bang de xuat trong bo nho tro ly va tu
Transfer Order, tuc dung nhung con so ma cot phai dang hien. Model khong them duoc gi ma con
co the dem sai, xem muc Azure OpenAI trong CLAUDE.md.
"""
from __future__ import annotations

from typing import Any

from . import Delivery

SKILL = "tracking"

TRANG_THAI = {"Proposed": "đang chờ người duyệt", "Executed": "đã thực thi",
              "Rejected": "đã từ chối", "Cancelled": "đã huỷ"}


def _ten_hang(asst: Any) -> dict[str, str]:
    return {i["itemNo"]: i["description"] for i in asst.gw.items()}


def _mot_dong(asst: Any, p: dict[str, Any], ten_hang: dict[str, str]) -> str:
    from ..core import STORE_LABEL

    ma = p.get("item_no") or ""
    # `item_desc` chi co tren de xuat do skill bo sung hang tao ra. De xuat den tu duong khac
    # thi tra ten trong danh muc, dung de nguoi doc nhin thay moi cai ma so.
    ten = p.get("item_desc") or ten_hang.get(ma) or ma
    tu = STORE_LABEL.get(p.get("from_loc") or "", p.get("from_loc") or "")
    den = STORE_LABEL.get(p.get("to_loc") or "", p.get("to_loc") or "")
    duong = f" {tu} sang {den}" if tu and den else (f" tại {den or tu}" if (den or tu) else "")
    sl = f", {p['quantity']:.0f}" if p.get("quantity") else ""
    tt = TRANG_THAI.get(p.get("status") or "", p.get("status") or "")
    ct = f", chứng từ {p['result_doc']}" if p.get("result_doc") else ""
    return f"{ten}{duong}{sl}: {tt}{ct}."


def handle(asst: Any, user: dict[str, Any]) -> list[Delivery]:
    """Danh sach viec cua nguoi dang hoi, xep theo trang thai."""
    uid = user["user_id"]
    props = asst.de_xuat_gop()
    # Nguoi duyet thi thay het; quan ly cua hang chi thay viec cua cua hang minh.
    if user.get("role") == "store_manager" and user.get("store_code"):
        props = [p for p in props if p.get("to_loc") == user["store_code"]]

    ten_hang = _ten_hang(asst)
    cho = [p for p in props if p.get("status") == "Proposed"]
    xong = [p for p in props if p.get("status") == "Executed"]
    thoi = [p for p in props if p.get("status") in ("Rejected", "Cancelled")]
    viec = [f for f in asst.mem.followups() if f.get("status") == "open"]
    to = [t for t in asst.gw._transfers.values() if t.get("status") != "Cancelled"] if asst.gw.is_mock else []

    if not (cho or xong or thoi or viec or to):
        return [Delivery(uid, "Hiện chưa có đề xuất, chứng từ hay việc nào đang theo dõi. "
                              "Khi Business Central tạo đề xuất, tôi sẽ báo bạn ở đây.", skill=SKILL)]

    phan: list[str] = []
    if cho:
        phan.append(f"Đang chờ người duyệt, {len(cho)} việc:\n" + "\n".join("  · " + _mot_dong(asst, p, ten_hang) for p in cho[:8]))
    if xong:
        phan.append(f"Đã thực thi, {len(xong)} việc:\n" + "\n".join("  · " + _mot_dong(asst, p, ten_hang) for p in xong[:8]))
    if thoi:
        phan.append(f"Đã dừng, {len(thoi)} việc:\n" + "\n".join("  · " + _mot_dong(asst, p, ten_hang) for p in thoi[:5]))
    if to:
        chua_ship = [t for t in to if not t.get("shipped")]
        phan.append(f"Chứng từ chuyển hàng: {len(to)} đơn, {len(chua_ship)} đơn chưa ship."
                    + ("\n" + "\n".join(f"  · {t['no']}: {t['quantity']:.0f} đi {t['toLocationCode']}"
                                        for t in chua_ship[:5]) if chua_ship else ""))
    if viec:
        phan.append(f"Việc tôi đang chờ trả lời: {len(viec)}.")

    return [Delivery(uid, "\n\n".join(phan) + "\n\nSố này lấy từ bảng đề xuất trong Business Central, "
                          "đúng những gì cột bên phải đang hiển thị.", skill=SKILL)]
