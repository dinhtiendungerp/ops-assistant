"""Hai company (NWV-MAROU, NWV-DAKAO) va nhac post nhan hang qua chat va email, 15/09/2026.

Du lieu mock: NCC-MO-04 nhan tai S0001 (Lan), tre 5 ngay tinh tu ngay neo 18/09/2026. Email trong test luon di kenh
file (conftest), khong gui ra ngoai.
"""
from __future__ import annotations

import json
from types import SimpleNamespace

import pytest
from fastapi.testclient import TestClient

from assistant import cong_ty as ctm
from assistant import thu_dien_tu as td
from assistant.core import Assistant
from assistant.memory import Memory
from assistant.nlu import RuleNLU
from assistant.skills import nhac_post
from assistant.skills import po_qua_han as pq
from bc_agent.mock_client import MockBCClient

REF = "NCC-MO-04|S0001"


# ---------------------------------------------------------------- company
def test_vai_nao_lam_o_company_nao():
    co = [ctm.MAROU, ctm.DAKAO]
    assert ctm.cua_vai({"role": "store_manager"}, co) == [ctm.DAKAO]
    assert ctm.cua_vai({"role": "warehouse"}, co) == [ctm.MAROU]
    assert ctm.cua_vai({"role": "supply_chain"}, co) == [ctm.MAROU, ctm.DAKAO]
    # Chi chay mot company (khong dat BC_COMPANIES) thi ai cung lam o company do
    assert ctm.cua_vai({"role": "store_manager"}, ["NWV"]) == ["NWV"]


@pytest.fixture()
def web_hai_cong_ty(monkeypatch):
    from assistant.channels import web
    tl = {ctm.MAROU: Assistant(MockBCClient(), Memory(":memory:"), cong_ty=ctm.MAROU),
          ctm.DAKAO: Assistant(MockBCClient(), Memory(":memory:"), cong_ty=ctm.DAKAO)}
    monkeypatch.setitem(web.state, "tro_ly", tl)
    monkeypatch.delitem(web.state, "asst", raising=False)
    monkeypatch.setattr(web, "cac_cong_ty", lambda: [ctm.MAROU, ctm.DAKAO])
    monkeypatch.setattr(ctm, "danh_sach", lambda s=None: [ctm.MAROU, ctm.DAKAO])
    return web, tl


def _so_tin(a, uid):
    return len(a.mem.inbox(uid, 0))


def test_quan_ly_cua_hang_luon_o_dakao_du_giao_dien_gui_marou(web_hai_cong_ty):
    web, tl = web_hai_cong_ty
    c = TestClient(web.app)
    d = c.get("/api/cong-ty", params={"user": "lan.s0001"}).json()
    assert [x["ten"] for x in d["duoc"]] == [ctm.DAKAO]
    c.post("/api/message", json={"user": "lan.s0001", "text": "brief"}, headers={"X-Cong-Ty": ctm.MAROU})
    assert _so_tin(tl[ctm.DAKAO], "lan.s0001") > 0 and _so_tin(tl[ctm.MAROU], "lan.s0001") == 0


def test_supply_chain_doi_duoc_company(web_hai_cong_ty):
    web, tl = web_hai_cong_ty
    c = TestClient(web.app)
    assert [x["ten"] for x in c.get("/api/cong-ty", params={"user": "trang.sc"}).json()["duoc"]] == [ctm.MAROU, ctm.DAKAO]
    c.post("/api/message", json={"user": "trang.sc", "text": "brief"}, headers={"X-Cong-Ty": ctm.DAKAO})
    assert _so_tin(tl[ctm.DAKAO], "trang.sc") > 0 and _so_tin(tl[ctm.MAROU], "trang.sc") == 0
    st = c.get("/api/state", headers={"X-Cong-Ty": ctm.DAKAO}).json()
    assert st["bc"]["cong_ty"] == ctm.DAKAO


def test_link_bc_mo_dung_company_cua_request(monkeypatch):
    from bc_agent.config import Settings
    from assistant import bc_link
    monkeypatch.setattr(bc_link, "Settings", lambda: Settings(bc_tenant_id="t", bc_environment="NWV01", bc_company_name="NWV"))
    tok = ctm.hien_tai.set(ctm.DAKAO)
    try:
        assert "company=NWV-DAKAO" in bc_link.link("purchase_order")
    finally:
        ctm.hien_tai.reset(tok)
    assert "company=NWV&" in bc_link.link("purchase_order")


# ---------------------------------------------------------------- nhac post
@pytest.mark.parametrize("cau", ["nhắc post nhận hàng", "gửi mail nhắc post chứng từ", "gửi lại mail nhắc post đơn mua"])
def test_rule_nhan_ra_yeu_cau_nhac(cau):
    assert RuleNLU().parse(cau).intent == "NHAC_POST"


def test_cau_hoi_po_van_la_po_overdue():
    assert RuleNLU().parse("PO nào quá hạn chưa nhận?").intent == "PO_OVERDUE"


@pytest.fixture()
def asst():
    return Assistant(MockBCClient(), cong_ty=ctm.DAKAO)


def _lan(a):
    return a.mem.user("lan.s0001")


def test_xac_nhan_hang_ve_thi_gui_email_ngay(asst):
    out = pq.on_xac_nhan(asst, _lan(asst), REF, True)
    the = [d for d in out if d.card and d.card.ref.startswith("thu|")]
    assert the, "phai co the email trong chat"
    thu = td.gan_day()
    assert len(thu) == 1 and thu[0]["trang_thai"] == "chi_luu_file" and "NCC-MO-04" in thu[0]["noi_dung"]
    assert "Dakao" in thu[0]["tieu_de"] and "1 đơn đã về chưa nhập BC" in thu[0]["tieu_de"]
    # Bat duoc tren BC ngay 15/09/2026: thu dau tien ghi "lan nhac thu 2" vi dem hai lan
    assert "Lần nhắc thứ 1" in thu[0]["noi_dung"] and "thứ 2" not in thu[0]["noi_dung"]
    # So trong email la so cua dong don mua, khong phai so model nghi ra
    dong = [r for r in pq.dong_qua_han(asst, "S0001") if r["documentNo"] == "NCC-MO-04"]
    assert f"còn {int(float(dong[0]['outstandingQuantity']))} /" in thu[0]["noi_dung"]


def test_khong_nhac_trung_trong_ngay_nhung_sang_hom_sau_nhac_lan_hai(asst):
    pq.on_xac_nhan(asst, _lan(asst), REF, True)
    nhac_post.nhac(asst)
    n = len(td.gan_day())
    nhac_post.nhac(asst)
    assert len(td.gan_day()) == n                     # cung ngay, cung danh sach: khong gui lai
    asst.mem.advance_clock(24)
    out = nhac_post.nhac(asst)
    assert len(td.gan_day()) == n + 1
    cau = [d.text for d in out if d.user_id == "lan.s0001"]
    assert any("Nhắc lần 2" in c for c in cau)


def test_da_post_thi_bao_va_dong_viec(asst, monkeypatch):
    pq.on_xac_nhan(asst, _lan(asst), REF, True)
    goc = asst.gw.doc

    def da_post(entity, conds, **kw):
        rows = goc(entity, conds, **kw)
        if entity == pq.ENTITY:
            rows = [dict(r, outstandingQuantity=0) if r.get("documentNo") == "NCC-MO-04" else r for r in rows]
        return rows
    monkeypatch.setattr(asst.gw, "doc", da_post)
    out = nhac_post.nhac(asst)
    assert any("đã được post nhận hàng" in d.text for d in out)
    assert not any("đã được post" in d.text for d in nhac_post.nhac(asst))   # bao mot lan


class _ModelGia:
    model = "gpt-4.1-mini"

    def __init__(self, mo, ket):
        self.tra = json.dumps({"mo_dau": mo, "ket": ket}, ensure_ascii=False)

    def text(self, **kw):
        return SimpleNamespace(content=[SimpleNamespace(type="text", text=self.tra)], usage=SimpleNamespace(),
                               stop_reason="end_turn")


def test_doan_model_viet_co_so_la_thi_dung_mau(asst, monkeypatch):
    asst._writer = _ModelGia("Có 999 đơn đang treo.", "Nhờ post.")
    monkeypatch.setattr(asst.budget, "allow", lambda: True)
    monkeypatch.setattr(asst.budget, "track", lambda *a, **k: 0)
    don = pq.gom_theo_don(pq.dong_qua_han(asst, "S0001"))
    thu = nhac_post.soan_thu(asst, don[:1], [])
    assert thu["nguoi_soan"].startswith("mẫu có sẵn") and "999" not in thu["text"]


def test_doan_model_viet_dung_so_thi_dung_doan_model(asst, monkeypatch):
    asst._writer = _ModelGia("Đơn đã trễ 5 ngày, cửa hàng đã có hàng mà hệ thống chưa ghi nhận.", "Nhờ anh chị post Receive sớm.")
    monkeypatch.setattr(asst.budget, "allow", lambda: True)
    monkeypatch.setattr(asst.budget, "track", lambda *a, **k: 0)
    don = [d for d in pq.gom_theo_don(pq.dong_qua_han(asst)) if d["so_don"] == "NCC-MO-04"]
    thu = nhac_post.soan_thu(asst, don, [])
    assert thu["nguoi_soan"].startswith("AI") and "trễ 5 ngày" in thu["text"]


def test_cua_hang_khong_goi_duoc_lenh_nhac(asst):
    out = nhac_post.handle(asst, _lan(asst), "nhắc post")
    assert len(out) == 1 and "Supply Chain" in out[0].text and not td.gan_day()
