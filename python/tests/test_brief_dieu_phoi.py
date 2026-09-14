"""Brief cua dieu phoi phai hien lai viec chua duyet, khong duoc im lang.

Dung bat duoc ngay 13/09/2026: vai Hung bam Brief chi ra "Sang nay 10 dong duoi nguong 5 ngay.
Moi dong toi da tinh so chuyen, ban duyet tung dong:" roi khong co the nao. Ca 10 dong da co de
xuat tu lan brief truoc trong BC, va nhanh chong tao trung chi `continue` ma khong hien gi.
"""
from __future__ import annotations

import pytest

from assistant.core import Assistant
from assistant.memory import Memory
from bc_agent.mock_client import MockBCClient


@pytest.fixture()
def asst():
    return Assistant(MockBCClient(), Memory(":memory:"))


def _the(out):
    return [d for d in out if d.card is not None]


def test_bam_brief_lan_hai_van_thay_the_cho_duyet(asst):
    lan1 = asst.morning_brief("hung.dieuphoi")
    so_de_xuat = len(asst.mem.proposals())
    assert _the(lan1), "lan dau phai co the de xuat"

    lan2 = asst.morning_brief("hung.dieuphoi")
    assert len(_the(lan2)) == len(_the(lan1)), "viec chua duyet phai hien lai"
    assert len(asst.mem.proposals()) == so_de_xuat, "khong duoc tao de xuat trung"
    assert "chờ bạn duyệt" in lan2[0].text


def test_cau_mo_dau_khong_hua_the_khi_khong_con_viec(asst, monkeypatch):
    # Giu nguyen danh sach dong rui ro: mock cap nhat ton sau khi duyet nen danh sach tu doi,
    # con tren BC that thi bang ket qua chi doi khi Job Queue chay lai.
    dong = asst.gw.risky_suggestions(10)
    monkeypatch.setattr(asst.gw, "risky_suggestions", lambda n=10: [dict(r) for r in dong])
    for d in _the(asst.morning_brief("hung.dieuphoi")):
        asst.handle_action("hung.dieuphoi", "approve", d.card.ref, {})
    out = asst.morning_brief("hung.dieuphoi")
    assert not _the(out)
    assert "Không còn việc nào cần bạn duyệt" in out[0].text
    assert "đang đi" in out[0].text


def test_de_xuat_chi_con_trong_bc_van_duyet_duoc(asst, monkeypatch):
    """Khoi dong lai tro ly thi bo nho rong, de xuat chi con trong BC. The hien ra ma bam Duyet
    bao "Khong tim thay de xuat" thi con te hon khong hien."""
    lan1 = _the(asst.morning_brief("hung.dieuphoi"))
    goc = asst.mem.proposal(lan1[0].card.ref)
    ban_bc = {k: goc[k] for k in ("proposal_id", "bc_id", "action_type", "status", "item_no", "from_loc",
                                  "to_loc", "quantity", "rationale", "created_at")}
    ban_bc["evidenceJson"] = '{"onhand": 1}'

    moi = Assistant(asst.gw.client, Memory(":memory:"))
    monkeypatch.setattr(moi.gw, "de_xuat", lambda top=500: [dict(ban_bc)])
    out = moi.morning_brief("hung.dieuphoi")
    the = [d for d in _the(out) if d.card.ref == goc["proposal_id"]]
    assert the, "de xuat cua BC phai co the"

    kq = moi.handle_action("hung.dieuphoi", "approve", goc["proposal_id"], {})
    assert not any("Không tìm thấy" in d.text for d in kq)
