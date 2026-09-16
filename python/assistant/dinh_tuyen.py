"""Quyet dinh cau nao tra loi bang du lieu, cau nao phai goi model.

Vi sao co file nay: bat AI len thi truoc day MOI tin nhan deu di qua model de phan loai, ke ca
"brief" hay "sap het Croissant plain" la nhung cau rule doc duoc chac chan. Do la tien tra cho
mot viec khong can den model. Dung hoi ngay 13/09/2026.

Nguyen tac: rule chay TRUOC, luon luon, va khong ton gi. Model chi duoc goi khi rule khong chac.
Rule "chac" nghia la:
  1. No phan loai ra mot intent that, khong phai HELP.
  2. Intent nao can biet mat hang thi phai tra duoc ma mat hang tu chu nguoi go.

Cai gia cua viec doan sai: neu rule nhan nham, cau tra loi se lech. Nen cho nao con nghi ngo thi
day sang model, dat hon nhung dung hon. Danh sach `CAN_MAT_HANG` chinh la cho de sai nhat: rule
bat trung mot tu khoa nhung khong biet nguoi ta noi ve mon nao.
"""
from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import Any

log = logging.getLogger(__name__)

# Intent chi tra loi dung khi biet mat hang nao. Khong tra duoc ma thi phai hoi model.
CAN_MAT_HANG = ("STOCKOUT", "STOCK_QUERY", "INVESTIGATE", "DAMAGE", "REPLEN_WHY")
# Intent doc thang tu bang, khong bao gio can model.
# NHAC_POST va IC_SHIP: skill tu doc don mua va phieu giao hang roi tu soan, model khong tham gia viec chon.
# Thieu hai cai nay trong danh sach thi rule bi coi la khong chac, cau di sang model va model phan loai nham:
# "hang Marou da xuat kho chua" tung ra TRACKING (bat duoc khi chay thu ca 16 man ngay 16/09/2026).
TU_DU_LIEU = ("BRIEF", "TRACKING", "PO_OVERDUE", "EXPIRY", "FORECAST", "SUPPLIER", "TRACE", "PROMO", "SELF_REVIEW",
              "ANOMALY", "WASTE_REPORT", "WASTE_WHY", "NHAC_POST", "IC_SHIP")


@dataclass
class SoDinhTuyen:
    """Dem xem bao nhieu cau tra loi duoc bang du lieu, bao nhieu cau phai goi model."""
    bang_du_lieu: int = 0
    goi_model: int = 0
    ly_do: dict[str, int] = field(default_factory=dict)

    def ghi(self, dung_model: bool, ly_do: str) -> None:
        if dung_model:
            self.goi_model += 1
        else:
            self.bang_du_lieu += 1
        self.ly_do[ly_do] = self.ly_do.get(ly_do, 0) + 1

    def tom_tat(self) -> dict[str, Any]:
        tong = self.bang_du_lieu + self.goi_model
        return {"tong": tong, "bang_du_lieu": self.bang_du_lieu, "goi_model": self.goi_model,
                "ty_le_tiet_kiem": round(self.bang_du_lieu / tong * 100, 1) if tong else 0.0,
                "ly_do": dict(sorted(self.ly_do.items(), key=lambda kv: -kv[1]))}


def rule_du_chac(intent: Any, gw: Any = None) -> tuple[bool, str]:
    """Rule co du chac de tra loi ma khong can model khong.

    Tra ve (du chac, ly do doc duoc). Ly do di thang len man hinh Cai dat nen viet cho nguoi doc.
    """
    ten = getattr(intent, "intent", "HELP")
    if ten == "HELP":
        return False, "rule không phân loại được"
    if ten == "ANSWER":
        # Nguoi dung dang tra loi mot cau hoi cua tro ly. Noi dung la van xuoi, khong can hieu
        # them gi: skill giai trinh nhan nguyen van.
        return True, "trả lời câu hỏi đang chờ"
    if ten in TU_DU_LIEU:
        return True, "đọc thẳng từ bảng kết quả"
    if ten in CAN_MAT_HANG:
        chu = (getattr(intent, "item_text", "") or "").strip()
        if not chu:
            return False, "biết loại việc nhưng chưa biết mặt hàng"
        if gw is not None:
            try:
                if not gw.find_item(chu):
                    return False, "không tra được mã mặt hàng từ chữ người gõ"
            except Exception as exc:                 # khong de loi tra cuu chan ca duong
                log.warning("find_item hong khi dinh tuyen: %s", exc)
                return False, "không tra được mã mặt hàng từ chữ người gõ"
        return True, "rule nhận ra việc và mặt hàng"
    return False, "rule không phân loại được"
