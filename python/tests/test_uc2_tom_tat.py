"""UC2 nhom Tom tat (15/09/2026): S1 brief do AI viet, S2 giai thich lo bang loi.

Nguyen tac kiem: model chi duoc dung con so va dong co trong du lieu code dua; sai la dung mau. Tat AI thi dung mau ngay.
"""
from __future__ import annotations

import json
from types import SimpleNamespace

import pytest
from fastapi.testclient import TestClient

from assistant.core import Assistant
from assistant.skills import uc2_tom_tat as t
from bc_agent.mock_client import MockBCClient


class _ModelGia:
    model = "gpt-4.1-mini"

    def __init__(self, tra: dict):
        self.tra = json.dumps(tra, ensure_ascii=False)
        self.so_lan = 0

    def text(self, **kw):
        self.so_lan += 1
        return SimpleNamespace(content=[SimpleNamespace(type="text", text=self.tra)], usage=SimpleNamespace(), stop_reason="end_turn")


@pytest.fixture()
def a():
    x = Assistant(MockBCClient())
    x.set_ai(False)
    return x


def _bat_model(a, monkeypatch, tra: dict) -> _ModelGia:
    m = _ModelGia(tra)
    a._writer = m
    monkeypatch.setattr(a.budget, "allow", lambda: True)
    monkeypatch.setattr(a.budget, "track", lambda *x, **k: 0)
    return m


def _the_brief(out):
    return next(d.card for d in out if d.card and d.card.kind == "brief")


# ---------------------------------------------------------------- S1
def test_tat_ai_brief_supply_chain_dung_mau_va_van_co_the_dong(a):
    out = a.morning_brief("trang.sc")
    c = _the_brief(out)
    assert c.title.startswith("3 việc") and ("Người soạn", "mẫu có sẵn (AI đang tắt)") in c.facts
    assert "45 lô đã hết hạn" in c.body and "1. Choco nuts tại S0002" in c.body
    # The tung dong van con, dong duoc chon dung dau
    the_dong = [d for d in out if d.card and d.card.kind == "info"]
    assert len(the_dong) == t.SO_UNG_VIEN and the_dong[0].text == "Choco nuts"


def test_model_viet_dung_thi_dung_doan_model(a, monkeypatch):
    du_lieu, ung_vien = t.du_lieu_brief(a, a.mem.user("trang.sc"))
    chon = [x["id"] for x in ung_vien[:2]]
    _bat_model(a, monkeypatch, {"mo_dau": "Sáng nay 45 lô đã hết hạn cần hủy.",
                                "viec": [{"id": chon[1], "viec": "Hủy Chocolate cake tại S0010, 28 cái.", "ly_do": "Hết hạn 1 ngày."},
                                         {"id": chon[0], "viec": "Hủy Choco nuts tại S0002, 285 cái.", "ly_do": "Giá trị lớn nhất."}],
                                "ket": "Tôi chỉ đề xuất, bạn duyệt."})
    out = a.morning_brief("trang.sc")
    c = _the_brief(out)
    assert c.title.startswith("2 việc") and c.facts[0][1].startswith("AI (") and "1. Hủy Chocolate cake" in c.body
    # Thu tu the dong theo thu tu model chon
    the_dong = [d for d in out if d.card and d.card.kind == "info"]
    assert the_dong[0].ref == chon[1] and the_dong[1].ref == chon[0]


def test_model_bia_so_thi_dung_mau(a, monkeypatch):
    _, ung_vien = t.du_lieu_brief(a, a.mem.user("trang.sc"))
    _bat_model(a, monkeypatch, {"mo_dau": "Có 999 lô hết hạn.", "viec": [{"id": ung_vien[0]["id"], "viec": "Hủy.", "ly_do": "x"}], "ket": "ok"})
    c = _the_brief(a.morning_brief("trang.sc"))
    assert c.facts[0][1].startswith("mẫu có sẵn (đoạn model viết có số không có trong dữ liệu: 999") and "999" not in c.body


def test_model_chon_dong_la_thi_dung_mau(a, monkeypatch):
    _bat_model(a, monkeypatch, {"mo_dau": "Tình hình ổn.", "viec": [{"id": "khong-co", "viec": "Hủy.", "ly_do": "x"}], "ket": "ok"})
    c = _the_brief(a.morning_brief("trang.sc"))
    assert "không có trong dữ liệu" in c.facts[0][1]


def test_brief_nho_ly_do_tu_choi_gan_day(a):
    du_lieu, ung_vien = t.du_lieu_brief(a, a.mem.user("trang.sc"))
    r = ung_vien[0]
    a.mem.save_proposal({"proposal_id": "P-TC", "bc_id": "x", "scenario": "InventoryHealth", "action_type": "WriteOff", "status": "Rejected",
                         "item_no": r["itemNo"], "from_loc": r["locationCode"], "to_loc": "", "quantity": 1, "max_quantity": 1,
                         "rationale": "", "evidence": {}, "item_desc": r["itemDescription"], "requested_by": "trang.sc",
                         "approver": "hung.dieuphoi", "approved_at": a.mem.now().isoformat(), "created_at": a.mem.now().isoformat(),
                         "channel_ref": t._ref(r), "outcome_note": "QA đang giữ lô để kiểm"})
    du_lieu, _ = t.du_lieu_brief(a, a.mem.user("trang.sc"))
    assert du_lieu["dong_ung_vien"][0]["da_tu_choi"].endswith("QA đang giữ lô để kiểm")
    assert du_lieu["tu_choi_gan_day"][0]["ly_do"] == "QA đang giữ lô để kiểm"
    c = _the_brief(a.morning_brief("trang.sc"))
    assert "1. Choco nuts tại S0002" not in c.body and "không đề xuất lại Choco nuts tại S0002" in c.body


def test_brief_cua_hang_chi_thay_cua_hang_minh(a):
    out = a.morning_brief("lan.s0001")
    c = _the_brief(out)
    assert "cửa hàng S0001" in c.body
    for d in out:
        if d.card and d.card.kind == "info":
            assert any(v.startswith("S0001") for l, v in d.card.facts if l == "Kho / lot")


# ---------------------------------------------------------------- S2
def _lo_can_date(a):
    return next(x for x in a.gw.doc("inventoryHealthLines", [], top=5000) if x["tier"] == "NearExpiry" and x["daysToExpiry"] > 3)


def test_giai_thich_lo_mau_co_du_so_cua_dong(a):
    r = _lo_can_date(a)
    kq = t.giai_thich_lo(a, r["id"])
    assert kq["nguoi_soan"] == "mẫu có sẵn (AI đang tắt)"
    assert r["lotNo"] in kq["doan"] and f"Còn {r['daysToExpiry']} ngày" in kq["doan"] and "dư" in kq["doan"]
    assert "đang bán nhanh hơn" in kq["doan"]       # S0001 ban Choco pillar nhanh hon S0010 trong bo demo


def test_giai_thich_lo_model_viet_dung_thi_nho_lai(a, monkeypatch):
    r = _lo_can_date(a)
    m = _bat_model(a, monkeypatch, {"doan": f"Lô {r['lotNo']} còn {r['daysToExpiry']} ngày, tôi thấy nên chuyển bớt."})
    kq = t.giai_thich_lo(a, r["id"])
    assert kq["nguoi_soan"].startswith("AI") and not kq["nho_lai"]
    kq2 = t.giai_thich_lo(a, r["id"])
    assert kq2["nho_lai"] and kq2["doan"] == kq["doan"] and m.so_lan == 1


def test_giai_thich_lo_model_bia_so_thi_dung_mau(a, monkeypatch):
    r = _lo_can_date(a)
    _bat_model(a, monkeypatch, {"doan": "Lô này bán 777 cái một ngày."})
    kq = t.giai_thich_lo(a, r["id"])
    assert kq["nguoi_soan"].startswith("mẫu có sẵn (đoạn model viết có số không có trong dữ liệu: 777") and "777" not in kq["doan"]


def test_api_giai_thich(a):
    from assistant.channels import web
    web.state["asst"] = a
    c = TestClient(web.app)
    r = _lo_can_date(a)
    kq = c.get("/api/uc2/giai-thich", params={"line_id": r["id"]}).json()
    assert kq["line_id"] == r["id"] and r["lotNo"] in kq["doan"]
    assert c.get("/api/uc2/giai-thich", params={"line_id": "khong-co"}).status_code == 404
