"""Cau nao tra loi bang du lieu, cau nao phai goi model.

Dung hoi ngay 13/09/2026: bat AI len thi co co che nao phan loai de tiet kiem token khong.
Truoc do MOI tin nhan deu di qua model de phan loai, ke ca nhung cau rule doc duoc chac chan.
"""
from __future__ import annotations

import pytest

from assistant.dinh_tuyen import SoDinhTuyen, rule_du_chac
from assistant.nlu import Intent, RuleNLU
from bc_agent.mock_client import MockBCClient


@pytest.fixture()
def gw():
    from assistant.gateway import BCGateway

    return BCGateway(MockBCClient())


@pytest.mark.parametrize("cau", [
    "brief",
    "việc của tôi đến đâu rồi",
    "sắp hết Croissant plain",
    "còn bao nhiêu Chocolate ice cream",
    "tự chấm điểm lại đi",
])
def test_cau_rule_doc_duoc_thi_khong_goi_model(gw, cau):
    chac, ly_do = rule_du_chac(RuleNLU().parse(cau), gw)
    assert chac is True, f"{cau!r} bi day sang model, ly do: {ly_do}"
    assert ly_do


@pytest.mark.parametrize("cau", [
    "góc kho bị mưa dột, mấy thùng syrup ướt nhãn chưa đếm được, giờ xử lý sao",
    "tháng sau mở cửa hàng ở Nha Trang thì nên đẩy bao nhiêu hàng ban đầu",
    "kho có đủ hàng cho cả 5 cửa hàng trong 10 ngày tới không",
])
def test_cau_ngoai_rule_thi_day_sang_model(gw, cau):
    chac, ly_do = rule_du_chac(RuleNLU().parse(cau), gw)
    assert chac is False, f"{cau!r} bi tra loi bang rule, ly do: {ly_do}"


def test_biet_viec_ma_khong_tra_duoc_mat_hang_thi_van_goi_model(gw):
    """Day la cho de sai nhat: rule bat trung tu khoa nhung khong biet noi ve mon nao."""
    chac, ly_do = rule_du_chac(RuleNLU().parse("sắp hết cái món hôm qua ấy"), gw)
    assert chac is False
    assert "mặt hàng" in ly_do


def test_khong_co_gateway_thi_bo_qua_buoc_tra_ma():
    chac, _ = rule_du_chac(Intent("STOCKOUT", "Croissant plain"), None)
    assert chac is True


def test_so_dem_ra_ty_le_tiet_kiem():
    so = SoDinhTuyen()
    so.ghi(False, "đọc thẳng từ bảng kết quả")
    so.ghi(False, "đọc thẳng từ bảng kết quả")
    so.ghi(True, "rule không phân loại được")
    t = so.tom_tat()
    assert (t["tong"], t["bang_du_lieu"], t["goi_model"]) == (3, 2, 1)
    assert t["ty_le_tiet_kiem"] == pytest.approx(66.7, abs=0.1)
    assert t["ly_do"]["đọc thẳng từ bảng kết quả"] == 2


def test_live_nlu_khong_goi_model_khi_rule_chac(monkeypatch, gw):
    """Kiem tren chinh LiveNLU: cau rule doc duoc thi khong duoc cham vao model."""
    from assistant import nlu as m

    class LlmGia:
        model = "gia"

        def text(self, *a, **k):
            raise AssertionError("da goi model cho cau rule doc duoc")

    monkeypatch.setattr("bc_agent.llm.build_llm", lambda **k: LlmGia())
    n = m.LiveNLU(budget=None, gw=gw)
    assert n.parse("brief").intent == "BRIEF"
    assert n.parse("sắp hết Croissant plain").intent == "STOCKOUT"
    assert n.so.tom_tat()["goi_model"] == 0
