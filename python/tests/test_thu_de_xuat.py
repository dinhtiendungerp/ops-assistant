"""De xuat moi phai den nguoi duyet ca qua email, phan loi do AI soan (Dung hoi toi 16/09/2026)."""
from __future__ import annotations

import sqlite3

from assistant import thu_dien_tu as thu_mod
from assistant.core import Assistant
from assistant.skills import inventory_health, thu_de_xuat, uc2_quet
from bc_agent.mock_client import MockBCClient


def _thu():
    if not thu_mod.DUONG.exists():
        return []
    with sqlite3.connect(thu_mod.DUONG) as c:
        c.row_factory = sqlite3.Row
        return [dict(r) for r in c.execute("SELECT * FROM thu ORDER BY id")]


def _lo_het_han(client):
    return next(r for r in client.data["inventoryHealthLines"] if r["tier"] == "Expired" and r.get("lotNo"))


def test_de_nghi_thi_gui_mot_email_cho_nguoi_duyet_va_bao_lai_nguoi_de_nghi():
    client = MockBCClient()
    a = Assistant(client)
    user = a.mem.user("lan.s0001")
    r = _lo_het_han(client)
    out = inventory_health.on_propose(a, user, r["id"], "WriteOff")
    thu = _thu()
    assert len(thu) == 1 and thu[0]["loai"] == "de_xuat" and thu[0]["den"] == "nguoi-post@example.com"
    assert r["itemDescription"] in thu[0]["tieu_de"] and "hủy hàng" in thu[0]["tieu_de"]
    assert r["lotNo"] in thu[0]["noi_dung"] and "Người đề nghị: Lan" in thu[0]["noi_dung"]
    assert thu[0]["nguoi_soan"].startswith("mẫu có sẵn")          # AI tat trong test
    the = [d for d in out if d.skill == thu_de_xuat.SKILL]
    assert len(the) == 1 and the[0].user_id == "lan.s0001" and the[0].card.title.startswith("Email cho người duyệt")
    assert ("Người soạn", thu[0]["nguoi_soan"]) in the[0].card.facts


def test_quet_sang_khong_gui_email_tung_de_xuat():
    client = MockBCClient()
    a = Assistant(client)
    r = _lo_het_han(client)
    inventory_health.on_propose(a, uc2_quet.NGUOI_QUET, r["id"], "WriteOff")
    assert _thu() == []


def test_email_hong_khong_lam_hong_de_xuat(monkeypatch):
    client = MockBCClient()
    a = Assistant(client)
    user = a.mem.user("trang.sc")
    r = _lo_het_han(client)

    def no(**kw):
        raise RuntimeError("SMTP chết")
    monkeypatch.setattr(thu_mod, "gui", no)
    out = inventory_health.on_propose(a, user, r["id"], "WriteOff")
    assert a.mem.proposals("Proposed")
    assert any("gửi không được" in d.text for d in out if d.skill == thu_de_xuat.SKILL)
