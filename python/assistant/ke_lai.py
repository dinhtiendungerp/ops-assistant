"""Lop AI ke lai: model doc ket qua ma code da tra cuu roi viet lai phan loi, bang van nam duoi lam bang chung.

Vi sao (Dung, toi 16/09/2026): "AI lam rat tot viec tong hop du lieu, phan tich insight, truyen tai thanh ngon ngu tu nhien,
ma sao trong cac phan phan hoi dang nay lai khong dung AI". Cac skill rule (du bao, LS giai thich, CTKM, don qua han, nha
cung cap, het han, truy xuat lo) tra mot cau mo dau ngan cong mot the day so. Gio khi AI bat, model doc chinh the do va
viet 3 den 6 cau: dieu quan trong nhat, insight (so sanh, cho dang lo), va mot viec nen lam. The giu nguyen.

Ranh gioi giu nhu moi tinh nang AI khac: code doc so, model chi dien dat; moi chu so model viet phai co trong the (kiem
bang `uc2_tom_tat.so_la`), sai thi giu nguyen cau cua rule va khong gan nhan AI. Tat AI hoac het tran thi khong goi.
"""
from __future__ import annotations

import logging
from typing import Any

from .skills import Delivery
from .skills import uc2_tom_tat as tt

log = logging.getLogger(__name__)

# Skill nao thi ke lai. Cac skill AI san (brief, D3, D4, planner...) da co "Nguoi soan" trong the nen bo qua theo fact.
SKILL_KE_LAI = {"du_bao", "ls_giai_thich", "khuyen_mai", "po_qua_han", "nha_cung_cap", "truy_xuat", "tracking",
                "inventory_health", "replenishment", "ic_nhan_hang"}

_SYSTEM = (
    "Bạn là trợ lý vận hành chuỗi cửa hàng chocolate Marou. Code đã tra cứu Business Central và LS Central xong; dữ liệu "
    "nằm trong `the` (tiêu đề, nội dung, các con số) kèm câu hỏi và vai người hỏi. Viết lại phần lời trả lời: 3 đến 6 câu, "
    "nói điều quan trọng nhất trước, nêu một hai insight (so sánh, chỗ đáng lo, xu hướng) và một việc nên làm. Bảng dữ liệu "
    "vẫn hiện bên dưới, nên KHÔNG liệt kê lại toàn bộ; chỉ nhắc con số then chốt. Chỉ dùng con số có trong dữ liệu, không "
    "tính, không cộng, không suy ra số mới, không thêm đơn vị tiền. Xưng 'tôi', gọi người đọc là 'bạn', tiếng Việt, không "
    "chào hỏi, không gạch đầu dòng, không in tên trường kỹ thuật.")
_SCHEMA = {"type": "object", "properties": {"tra_loi": {"type": "string"}}, "required": ["tra_loi"], "additionalProperties": False}


def _co_nguoi_soan(card: Any) -> bool:
    return any((f[0] if isinstance(f, (list, tuple)) else getattr(f, "label", "")) == "Người soạn" for f in (card.facts or []))


def ke_lai(asst: Any, user: dict[str, Any], cau_hoi: str, out: list[Delivery]) -> list[Delivery]:
    """Ke lai cac the du lieu gui cho CHINH nguoi hoi. Tra ve cung danh sach, da sua tai cho."""
    if not getattr(asst, "ai_live", False) or not getattr(asst, "_writer", None):
        return out
    for d in out:
        if d.user_id != user.get("user_id") or not d.card or d.skill not in SKILL_KE_LAI:
            continue
        if getattr(d.card, "kind", "") not in ("", "info", "brief"):
            continue
        if _co_nguoi_soan(d.card):
            # The do AI viet san (D3, S1...): doan dau cua the la loi AI, nhung bong bong tren the lai la cau dem cua rule
            # ("Bat thuong 28 ngay qua: 16 tin hieu"). Dung 16/09: "phan can AI viet thi khong de AI viet". Dua doan AI len
            # lam cau tra loi; giao dien an bong bong trung va thu gon phan bang.
            doan = (d.card.body or "").split("\n\n")[0].strip()
            if doan and len(doan) > 40 and not doan.startswith(("·", "-", "1.")):
                d.meta["cau_rule"] = d.text
                d.text = doan
            continue
        the = d.card.to_dict()
        the.pop("actions", None)
        the.pop("links", None)
        du_lieu = {"cau_hoi": cau_hoi, "vai": user.get("role", ""), "cua_hang": user.get("store_code") or "",
                   "cau_rule_da_viet": d.text, "the": the}
        m, nguoi_soan = tt._goi_model(asst, "ke_lai", _SYSTEM, du_lieu, _SCHEMA, max_tokens=450)
        loi = (m or {}).get("tra_loi", "").strip() if m else ""
        if not loi:
            continue
        sai = tt.so_la(du_lieu, loi)
        if sai:
            log.info("Ke lai bi chan: so %s khong co trong the (%s)", sorted(sai), d.skill)
            continue
        d.meta["cau_rule"] = d.text
        d.text = loi
        d.card.facts = list(d.card.facts or []) + [("Người soạn", nguoi_soan)]
    return out
