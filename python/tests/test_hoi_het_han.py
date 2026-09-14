"""Hoi lo het han theo vai tro.

Ngay 14/09/2026 Hung (dieu phoi kho) hoi "co mat hang nao da het han chua" va tro ly hoi lai "ban thuoc cua hang nao":
chu "het" dua cau vao nhanh bao sap het hang. Dung bac: dang dung vai kho ma con hoi o dau.
"""
from __future__ import annotations

from assistant.core import Assistant
from assistant.nlu import RuleNLU
from bc_agent.mock_client import MockBCClient


def test_het_han_khong_phai_het_hang():
    assert RuleNLU().parse("có mặt hàng nào đã hết hạn chưa").intent == "EXPIRY"
    assert RuleNLU().parse("lô nào sắp hết hạn ở S0001").store_hint == "S0001"
    assert RuleNLU().parse("sắp hết Choco nuts").intent == "STOCKOUT"


def test_dieu_phoi_thay_moi_dia_diem_khong_bi_hoi_lai():
    a = Assistant(MockBCClient())
    out = a.handle_message("hung.dieuphoi", "có mặt hàng nào đã hết hạn chưa")
    assert out[0].skill == "inventory_health"
    assert "đã hết hạn ở mọi địa điểm" in out[0].text and "cửa hàng nào" not in out[0].text
    assert any(d.card for d in out)


def test_kho_chi_thay_kho_minh():
    a = Assistant(MockBCClient())
    out = a.handle_message("kho.w0003", "lô nào sắp hết hạn")
    assert "sắp hết hạn tại W0003" in out[0].text or "Không có lô nào sắp hết hạn tại W0003" in out[0].text
    for d in out[1:]:
        assert "W0003" in dict(d.card.facts)["Kho / lot"]


def test_dieu_phoi_hoi_sap_het_mot_mat_hang_thi_tra_ton_moi_noi():
    a = Assistant(MockBCClient())
    out = a.handle_message("hung.dieuphoi", "sắp hết Choco nuts")
    assert "cửa hàng nào" not in out[-1].text and "Choco nuts" in out[-1].text
