"""Intercompany phia nguoi mua: bao doi tac da xuat kho, nhac khi qua ngay, de xuat cho tro ly post nhan hang (16/09/2026)."""
from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from assistant import thu_dien_tu as td
from assistant.core import Assistant
from assistant.skills import ic_nhan_hang as ic
from bc_agent.mock_client import MockBCClient


@pytest.fixture()
def a():
    x = Assistant(MockBCClient())
    x.set_ai(False)
    return x


def _don(a, po="HO106201", loc="S0010"):
    return a.gw.gia_lap_don_ic(po, "33110", "Croissant - chocolate", 2, loc)


def _xuat(a, po="HO106201"):
    return a.gw.post_giao_hang_doi_tac(po, "NWV-MAROU")


def test_chua_xuat_kho_thi_khong_bao_gi(a):
    _don(a)
    assert ic.quet(a) == []


def test_xuat_trong_ngay_bao_cua_hang_va_supply_chain_kem_email(a):
    _don(a)
    _xuat(a)
    out = ic.quet(a)
    nhan = {d.user_id for d in out}
    assert "tuan.s0005" not in nhan                      # cua hang khac khong bi lam phien
    assert "ha.s0010" in nhan and "trang.sc" in nhan
    the = next(d.card for d in out if d.card and d.card.kind == "info")
    assert "đã xuất kho đơn HO106201" in the.title and "Croissant - chocolate" in the.body
    assert td.gan_day(1)[0]["loai"] == "ic_xuat_kho"
    # Chua qua ngay thi chua de xuat gi
    assert a.mem.proposals() == []


def test_khong_bao_lai_don_da_bao(a):
    _don(a)
    _xuat(a)
    ic.quet(a)
    assert ic.quet(a) == []


def test_qua_ngay_chua_post_thi_nhac_va_de_xuat_cho_tro_ly_post(a):
    _don(a)
    _xuat(a)
    ic.quet(a)
    a.mem.advance_clock(30)
    a.gw._ic["HO106201"]["shipment"]["postingDate"] = "2026-09-15"   # doi tac xuat tu hom qua
    out = ic.quet(a)
    assert any("vẫn còn" in d.text and "chưa post nhận" in d.text for d in out)
    p = a.mem.proposals()[0]
    assert p["action_type"] == "PostReceipt" and p["source_doc"] == "HO106201" and p["requested_by"] == "tro_ly"
    assert p["policy_rule"] == "P-12" and p["policy_mode"] == "approve"
    the = next(d.card for d in out if d.card and d.card.kind == "proposal")
    assert the.title == "Cho trợ lý post nhận hàng đơn HO106201?"
    assert [x.id for x in the.actions] == ["approve", "reject"]
    # chay lai trong ngay khong ghi de xuat thu hai
    ic.quet(a, bat_buoc=True)
    assert len([x for x in a.mem.proposals() if x["action_type"] == "PostReceipt"]) == 1


def test_duyet_thi_bc_post_phieu_nhan_va_bao_ca_hai_ben(a):
    _don(a)
    _xuat(a)
    ic.quet(a)
    a.gw._ic["HO106201"]["shipment"]["postingDate"] = "2026-09-15"
    ic.quet(a, bat_buoc=True)
    p = next(x for x in a.mem.proposals() if x["action_type"] == "PostReceipt")
    out = a.handle_action("hung.dieuphoi", "approve", p["proposal_id"], {})
    the = out[0].card
    assert the.title.startswith("Đã post phiếu nhận RCPT-") and "số trên hệ thống khớp lại" in the.body
    assert {d.user_id for d in out} >= {"hung.dieuphoi", "ha.s0010", "trang.sc"}
    assert a.mem.proposal(p["proposal_id"])["status"] == "Executed"
    assert a.gw._ic["HO106201"]["outstanding"] == 0


def test_cua_hang_khong_thay_so_lo_nhung_nguoi_duyet_thi_thay(a):
    """Dakao la ban le, khong quan ly lo (Dung bac 16/09/2026). So lo chi hien o the nguoi duyet, vi do la thu BC se ghi
    vao phieu nhan; tin va email gui cua hang thi khong."""
    _don(a)
    _xuat(a)
    out = ic.quet(a)
    the_cua_hang = next(d.card for d in out if d.card and d.card.kind == "info")
    assert "lô" not in the_cua_hang.body and "L-33110" not in the_cua_hang.body
    assert "L-33110" not in td.gan_day(1)[0]["noi_dung"]
    a.gw._ic["HO106201"]["shipment"]["postingDate"] = "2026-09-15"
    out = ic.quet(a, bat_buoc=True)
    the_duyet = next(d.card for d in out if d.card and d.card.kind == "proposal")
    assert "lô L-33110" in the_duyet.body


def test_da_nhan_thi_dong_viec_mot_lan(a):
    _don(a)
    _xuat(a)
    ic.quet(a)
    a.gw._ic["HO106201"].update({"outstanding": 0, "received": 2})
    out = ic.quet(a)
    assert any("đã được post nhận hàng đủ" in d.text for d in out)
    assert ic.quet(a) == []


def test_cau_hoi_cua_quan_ly_cua_hang_chi_thay_don_cua_minh(a):
    _don(a, "HO106201", "S0010")
    _don(a, "HO106200", "S0005")
    _xuat(a, "HO106201")
    _xuat(a, "HO106200")
    out = ic.handle(a, a.mem.user("ha.s0010"))
    assert len(out) == 1 and "HO106201" in out[0].text


def test_api_demo_marou_xuat_kho(a):
    from assistant.channels import web
    web.state["asst"] = a
    _don(a)
    c = TestClient(web.app)
    kq = c.post("/api/demo/marou-xuat-kho", json={"user": "dung.admin", "doc_no": "HO106201"}).json()
    assert kq["ket_qua"]["shipment"].startswith("SHP-")
    assert "ha.s0010" in kq["delivered"]
