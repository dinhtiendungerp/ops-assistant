"""UC2 G2 + A3 (bien ban huy, luong huy khep kin) va A2 (quet sang tu dong), 16/09/2026."""
from __future__ import annotations

from collections import Counter

import pytest
from fastapi.testclient import TestClient

from assistant import thu_dien_tu as td
from assistant.core import Assistant
from assistant.skills import inventory_health as ih
from assistant.skills import uc2_huy, uc2_quet
from bc_agent.mock_client import MockBCClient
from tests.test_uc2_tom_tat import _ModelGia


@pytest.fixture()
def a():
    x = Assistant(MockBCClient())
    x.set_ai(False)
    return x


def _lo_het_han(a):
    return next(x for x in a.gw.doc("inventoryHealthLines", [], top=5000) if x["tier"] == "Expired")


def _duyet_huy(a):
    r = _lo_het_han(a)
    ih.on_propose(a, a.mem.user("trang.sc"), r["id"], "WriteOff")
    p = a.mem.proposals()[0]
    return r, p, a.handle_action("hung.dieuphoi", "approve", p["proposal_id"], {})


# ---------------------------------------------------------------- G2 + A3
def test_duyet_huy_tao_chung_tu_nhap_bien_ban_email_va_viec_theo_doi(a):
    r, p, ra = _duyet_huy(a)
    c = ra[0].card
    assert c.title.startswith("Đã duyệt hủy. Biên bản và chứng từ nháp AGENT-")
    assert "BIÊN BẢN ĐỀ NGHỊ HỦY HÀNG" in c.body and r["lotNo"] in c.body and "chưa post" in c.body
    assert ("Người soạn biên bản", "mẫu có sẵn (AI đang tắt)") in c.facts
    # Nguoi de nghi (Trang) duoc bao; de xuat Executed voi chung tu la dong journal
    assert any(d.user_id == "trang.sc" and "chờ kế toán post" in d.text for d in ra)
    p2 = a.mem.proposal(p["proposal_id"])
    assert p2["status"] == "Executed" and p2["result_doc"].startswith("AGENT-")
    assert a.gw.dong_journal(p2["result_doc"])[0]["lotNo"] == r["lotNo"]
    # Email cho bo phan post, viec theo doi
    assert td.gan_day(1)[0]["loai"] == "bien_ban_huy"
    assert [(f["kind"], f["ref"]) for f in a.mem.followups()] == [("write_off_post", p2["result_doc"])]


def test_theo_doi_nhac_roi_dong_khi_da_post(a):
    r, p, ra = _duyet_huy(a)
    doc = a.mem.proposal(p["proposal_id"])["result_doc"]
    assert a.run_followups() == []                     # chua den han kiem
    a.mem.advance_clock(25)
    out = a.run_followups()
    assert any("Nhắc lần 1" in d.text and doc in d.text for d in out) and td.gan_day(1)[0]["loai"] == "nhac_huy"
    a.mem.advance_clock(25)
    assert any("Nhắc lần 2" in d.text for d in a.run_followups())
    a.gw.gia_lap_post_journal(doc)
    a.mem.advance_clock(25)
    out = a.run_followups()
    assert any(d.card and d.card.title == f"Kế toán đã post chứng từ hủy {doc}" for d in out)
    assert a.mem.followups()[0]["status"] == "done" and a.run_followups() == []


def test_bien_ban_model_viet_dung_so_thi_dung(a, monkeypatch):
    r = _lo_het_han(a)
    ih.on_propose(a, a.mem.user("trang.sc"), r["id"], "WriteOff")
    p = a.mem.proposals()[0]
    m = _ModelGia({"dien_bien": f"Lô {r['lotNo']} tại {r['locationCode']} đã hết hạn, tồn {int(r['quantityOnHand'])} cái.",
                   "de_nghi": "Đề nghị kế toán post chứng từ nháp; trợ lý không post."})
    a._writer = m
    monkeypatch.setattr(a.budget, "allow", lambda: True)
    monkeypatch.setattr(a.budget, "track", lambda *x, **k: 0)
    ra = a.handle_action("hung.dieuphoi", "approve", p["proposal_id"], {})
    c = ra[0].card
    assert c.facts[-1][1].startswith("AI (") and f"Lô {r['lotNo']} tại {r['locationCode']} đã hết hạn" in c.body


def test_bien_ban_model_bia_so_thi_dung_mau(a, monkeypatch):
    r = _lo_het_han(a)
    ih.on_propose(a, a.mem.user("trang.sc"), r["id"], "WriteOff")
    p = a.mem.proposals()[0]
    a._writer = _ModelGia({"dien_bien": "Lô này 4444 cái.", "de_nghi": "Post."})
    monkeypatch.setattr(a.budget, "allow", lambda: True)
    monkeypatch.setattr(a.budget, "track", lambda *x, **k: 0)
    c = a.handle_action("hung.dieuphoi", "approve", p["proposal_id"], {})[0].card
    assert "4444" in c.facts[-1][1] and "4444" not in c.body


# ---------------------------------------------------------------- A2
def test_quet_sang_tu_de_xuat_huy_phuong_an_brief_va_email(a):
    out = uc2_quet.quet(a, a.mem.user("dung.admin"))
    props = a.mem.proposals()
    assert props and all(p["action_type"] == "WriteOff" and p["requested_by"] == "tro_ly" for p in props)
    assert len(props) <= uc2_quet.TOI_DA_DE_XUAT_HUY
    # Nguoi duyet nhan the de xuat, Supply Chain nhan phuong an D4, brief den Supply Chain va tung cua hang
    assert any(d.user_id == "hung.dieuphoi" and d.card and d.card.kind == "proposal" for d in out)
    assert sum(1 for d in out if d.user_id == "trang.sc" and d.card and d.card.title.startswith("Phương án cho lô cận date")) == uc2_quet.TOI_DA_PHUONG_AN
    assert any(d.user_id == "lan.s0001" and d.card and d.card.kind == "brief" for d in out)
    assert not any(d.user_id == "tro_ly" for d in out)
    assert td.gan_day(1)[0]["loai"] == "quet_uc2"
    tom_tat = next(d.text for d in out if d.ref == "quet-uc2")
    assert tom_tat.startswith("Quét sáng xong") and f"{len(props)} đề xuất hủy mới" in tom_tat


def test_quet_khong_lap_trong_ngay_va_chay_lai_khong_de_xuat_trung(a):
    uc2_quet.quet(a)
    n = len(a.mem.proposals())
    out = uc2_quet.quet(a, a.mem.user("dung.admin"))
    assert len(out) == 1 and "đã quét rồi" in out[0].text
    out = uc2_quet.quet(a, a.mem.user("dung.admin"), bat_buoc=True)
    # Lo da bao khong de xuat lai; vong sau lay tiep 10 lo het han ke tiep (bo demo co 45 lo het han)
    refs = [p["channel_ref"] for p in a.mem.proposals()]
    assert len(refs) == len(set(refs)) and n < len(refs) <= 2 * uc2_quet.TOI_DA_DE_XUAT_HUY
    assert "Quét sáng xong" in next(d.text for d in out if d.ref == "quet-uc2")


def test_quet_nhac_de_xuat_cho_qua_mot_ngay_va_chay_theo_doi(a):
    r, p, ra = _duyet_huy(a)
    ih.on_propose(a, a.mem.user("trang.sc"), next(x for x in a.gw.doc("inventoryHealthLines", [], top=5000)
                                                     if x["tier"] == "Expired" and x["id"] != r["id"])["id"], "WriteOff")
    a.mem.advance_clock(30)
    out = uc2_quet.quet(a, a.mem.user("dung.admin"))
    assert any(d.ref == "nhac-duyet" and "chờ duyệt quá 1 ngày" in d.text for d in out)
    assert any("Nhắc lần 1" in d.text for d in out)   # A3 chay trong vong quet


def test_api_quet_va_demo_post_huy(a):
    from assistant.channels import web
    web.state["asst"] = a
    c = TestClient(web.app)
    kq = c.post("/api/quet-uc2", json={"user": "dung.admin"}).json()
    assert "dung.admin" in kq["delivered"] and "hung.dieuphoi" in kq["delivered"]
    p = a.mem.proposals()[0]
    a.handle_action("hung.dieuphoi", "approve", p["proposal_id"], {})
    a.mem.advance_clock(25)
    kq = c.post("/api/demo/post-huy", json={"user": "dung.admin"}).json()
    assert kq["da_post"] == [a.mem.proposal(p["proposal_id"])["result_doc"]] and "hung.dieuphoi" in kq["delivered"]


def test_duyet_de_xuat_khong_con_ben_bc_thi_bao_ro(a):
    """Bo nho tro ly song lau hon du lieu: o che do mo phong fixtures nap lai, tren BC that nguoi khac co the xoa dong do.
    Bat duoc 16/09/2026: bam Duyet tra HTTP 500 KeyError thay vi mot cau doc duoc."""
    from bc_agent.bc_client import BCError

    r = _lo_het_han(a)
    ih.on_propose(a, a.mem.user("trang.sc"), r["id"], "WriteOff")
    p = a.mem.proposals()[0]
    a.gw.client.data["agentProposals"] = [x for x in a.gw.client.data["agentProposals"] if x["id"] != p["bc_id"]]
    with pytest.raises(BCError) as e:
        a.handle_action("hung.dieuphoi", "approve", p["proposal_id"], {})
    assert "không còn trong Business Central" in str(e.value)
