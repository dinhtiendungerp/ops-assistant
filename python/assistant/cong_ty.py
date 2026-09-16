"""Hai company cua Marou tren cung mot environment BC, va ai lam viec o company nao.

Vi sao co file nay (15/09/2026). Marou co hai phap nhan: Marou san xuat (co quan ly lo) va Dakao ban le (khong quan
ly lo). Dung tao hai company NWV-MAROU va NWV-DAKAO tren NWV01. Moi company mot tro ly rieng (bo nho, de xuat, policy
rieng), vi du lieu, de xuat va chung tu cua hai phap nhan khong duoc lan vao nhau.

Tien dung cho nguoi dung:
  - Nguoi chi lam o mot company (quan ly cua hang, kho nha may) khong bao gio phai chon.
  - Nguoi lam ca hai (Supply Chain, dieu phoi, quan tri) co nut doi company tren thanh tieu de; lua chon nho theo nguoi.

`hien_tai` la ContextVar: tang web dat company cua request, cac cho sinh link BC (bc_link) doc ra ma khong phai
truyen tham so qua moi skill.
"""
from __future__ import annotations

from contextvars import ContextVar
from typing import Any

from bc_agent.config import Settings

MAROU = "NWV-MAROU"
DAKAO = "NWV-DAKAO"

# Nhan hien tren giao dien va trong cau tra loi. Company khong co trong bang thi hien nguyen ten.
NHAN = {
    MAROU: {"ngan": "Marou", "day_du": "Marou (sản xuất)", "mo_ta": "Nhà máy, kho trung tâm, có quản lý lô"},
    DAKAO: {"ngan": "Dakao", "day_du": "Dakao (bán lẻ)", "mo_ta": "Chuỗi cửa hàng, không quản lý lô"},
}

# Vai nao lam o company nao. Phan tu dau la mac dinh.
VAI = {
    "store_manager": [DAKAO],
    "retail_ops": [DAKAO],
    "warehouse": [MAROU],
    "dispatcher": [DAKAO, MAROU],
    "supply_chain": [MAROU, DAKAO],
    "admin": [MAROU, DAKAO],
}

hien_tai: ContextVar[str] = ContextVar("cong_ty_hien_tai", default="")


def danh_sach(s: Settings | None = None) -> list[str]:
    """Cac company tro ly dang chay. BC_COMPANIES rong thi chi mot company theo BC_COMPANY_NAME."""
    s = s or Settings()
    ds = [c.strip() for c in (s.bc_companies or "").split(",") if c.strip()]
    return ds or [s.bc_company_name or "NWV"]


def nhan(ten: str, kieu: str = "ngan") -> str:
    return NHAN.get(ten, {}).get(kieu, ten)


def cua_vai(user: dict[str, Any] | None, co: list[str]) -> list[str]:
    """Company nguoi nay duoc lam, chi trong so company dang chay. Vai la hoac khong khop thi cho moi company."""
    if not user:
        return list(co)
    ds = [c for c in VAI.get(user.get("role", ""), []) if c in co]
    return ds or list(co)


def mo_ta(co: list[str]) -> list[dict[str, str]]:
    return [{"ten": c, "ngan": nhan(c), "day_du": nhan(c, "day_du"), "mo_ta": nhan(c, "mo_ta")} for c in co]
