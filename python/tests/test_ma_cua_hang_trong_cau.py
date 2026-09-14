"""Ma cua hang trong cau hoi ton kho.

Ngay 14/09/2026 Dung go "Toi muon kiem tra ton kho cua choco cake cua S001" va tro ly tu choi: ma cua hang (go thieu mot
so 0) nam trong chu dung de tra ten mat hang, lam diem khop rot duoi nguong. Gio ma dia diem duoc tach ra, chuan hoa
bon chu so va dung de loc ket qua.
"""
from __future__ import annotations

from assistant.core import Assistant
from assistant.nlu import RuleNLU, ma_dia_diem
from bc_agent.mock_client import MockBCClient


def test_chuan_hoa_ma_dia_diem():
    assert ma_dia_diem("choco cake của S001") == "S0001"
    assert ma_dia_diem("kho w3") == "W0003"
    assert ma_dia_diem("không có mã") == ""


def test_ma_cua_hang_khong_lot_vao_ten_mat_hang():
    it = RuleNLU().parse("Tôi muốn kiểm tra tồn kho của choco cake của S001")
    assert it.intent == "STOCK_QUERY" and it.store_hint == "S0001"
    assert "S001" not in it.item_text and "choco cake" in it.item_text.lower()


def test_hoi_ton_mot_cua_hang_chi_tra_cua_hang_do():
    a = Assistant(MockBCClient())
    out = a.handle_message("thao.s0013", "Tôi muốn kiểm tra tồn kho của choco cake của S001")
    assert out[-1].skill == "replenishment"
    assert "S0001" in out[-1].text and "S0002" not in out[-1].text


def test_quan_ly_cua_hang_khong_yeu_cau_bo_sung_cho_cua_hang_khac():
    a = Assistant(MockBCClient())
    out = a.handle_message("thao.s0013", "sắp hết Choco nuts S0001")
    assert "S0013" in out[-1].text and "chỉ gửi được" in out[-1].text
