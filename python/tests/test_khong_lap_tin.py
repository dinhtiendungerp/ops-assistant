"""Mot tin chi duoc ghi vao hop thu mot lan.

Go "brief" trong chat di qua hai tang cung goi `_deliver`: `handle_message` goi cho ket qua
cuoi cung, va `morning_brief` da tu goi vi no cung la cua vao rieng cua `POST /api/brief`.
Man hinh hien hai lan cung mot cau. Test nay giu cho no khong quay lai.
"""
from __future__ import annotations

import pytest

from assistant.core import Assistant
from assistant.memory import Memory
from bc_agent.mock_client import MockBCClient


@pytest.fixture()
def asst():
    return Assistant(MockBCClient(), Memory(":memory:"))


@pytest.mark.parametrize("nguoi", ["ha.s0010", "hung.dieuphoi", "trang.sc", "thu.retailops"])
def test_go_brief_trong_chat_chi_ra_mot_lan(asst, nguoi):
    """So dong trong hop thu phai bang so Delivery tra ve. Brief cua Supply Chain that su gui
    nhieu the (moi lo mot the), nen khong the dem bang cach loc trung noi dung."""
    out = asst.handle_message(nguoi, "brief")
    ra = [m for m in asst.mem.inbox(nguoi, 0) if m["direction"] == "out"]
    assert len(ra) == len(out), f"{len(out)} tin ma hop thu co {len(ra)} dong"


def test_goi_thang_morning_brief_van_ghi_mot_lan(asst):
    """`POST /api/brief` goi thang ham nay, khong qua handle_message."""
    out = asst.morning_brief("ha.s0010")          # tu 14/09/2026 co them dong CTKM sap toi tai cua hang, nen dem theo so tin tra ve
    assert len([m for m in asst.mem.inbox("ha.s0010", 0) if m["direction"] == "out"]) == len(out) >= 1


def test_deliver_hai_lan_cung_mot_danh_sach_chi_ghi_mot_lan(asst):
    from assistant.skills import Delivery

    d = [Delivery("ha.s0010", "thử")]
    asst._deliver(d)
    asst._deliver(d)
    assert len([m for m in asst.mem.inbox("ha.s0010", 0) if m["direction"] == "out"]) == 1


def test_bat_ai_thi_cau_ngan_van_di_qua_planner(asst):
    """Nguong sau tu tung chan ca "liet ke 5 mat hang" va tra ve cau tro giup, nhin nhu AI
    khong chay. Bat AI thi hai tu tro len la du."""
    asst.ai_live = False
    assert asst._dua_cho_planner("liệt kê 5 mặt hàng") is False
    asst.ai_live = True
    assert asst._dua_cho_planner("liệt kê 5 mặt hàng") is True
    assert asst._dua_cho_planner("brief") is False        # mot tu thi van la tro giup
