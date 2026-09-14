"""Hoi "viec cua toi den dau roi" phai tra loi duoc, khong duoc tu choi.

Cot phai man hinh da hien san de xuat va chung tu, nhung hoi cung noi dung do bang cau chu thi
tro ly tung bao "chua tra loi duoc". Dung chi ra ngay 13/09/2026. Duong nay khong goi model:
cau tra loi ghep tu bang de xuat, nen no chay ca khi AI dang tat.
"""
from __future__ import annotations

import pytest

from assistant.core import Assistant
from assistant.nlu import RuleNLU
from bc_agent.mock_client import MockBCClient


@pytest.fixture()
def asst():
    return Assistant(MockBCClient())


@pytest.mark.parametrize("cau", [
    "Cho tôi xem tiến độ các đề xuất và chứng từ tôi đang theo dõi.",
    "việc của tôi đến đâu rồi",
    "đề xuất của tôi tình trạng thế nào",
    "còn chứng từ nào chưa ship không",
])
def test_rule_nhan_ra_cau_hoi_ve_tien_do(cau):
    assert RuleNLU().parse(cau).intent == "TRACKING"


def test_tra_loi_bang_du_lieu_that_khong_phai_cau_tu_choi(asst):
    asst.morning_brief("hung.dieuphoi")          # tao vai de xuat
    out = asst.handle_message("hung.dieuphoi", "việc của tôi đến đâu rồi")
    assert len(out) == 1
    t = out[0].text
    assert "chưa trả lời được" not in t
    assert "Đang chờ người duyệt" in t
    assert "Kho trung tâm" in t                  # ten dia diem, khong phai ma tho


def test_chua_co_gi_thi_noi_ro_chua_co_chu_khong_tu_choi(asst):
    out = asst.handle_message("lan.s0001", "các đề xuất của tôi đến đâu rồi")
    assert "chưa có đề xuất" in out[0].text.lower()
    assert "chưa trả lời được" not in out[0].text


def test_quan_ly_cua_hang_chi_thay_viec_cua_cua_hang_minh(asst):
    asst.morning_brief("hung.dieuphoi")
    out = asst.handle_message("minh.s0002", "việc của tôi đến đâu rồi")
    t = out[0].text
    for ten_khac in ("Cửa hàng Quận 1", "Quán cà phê Đà Nẵng", "Nhà hàng Thảo Điền"):
        assert ten_khac not in t, f"lo viec cua {ten_khac} sang cho quan ly S0002"


def test_khong_goi_model(asst, monkeypatch):
    """Duong nay phai chay duoc khi AI tat, va khong duoc ton mot dong nao."""
    asst.set_ai(False)
    truoc = asst.budget.tong()["luot"]
    asst.morning_brief("hung.dieuphoi")
    out = asst.handle_message("hung.dieuphoi", "tiến độ các đề xuất")
    assert "Đang chờ người duyệt" in out[0].text
    assert asst.budget.tong()["luot"] == truoc
