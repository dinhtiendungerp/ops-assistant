"""Tra loi mot tin cu the: cau tra loi phai gan dung viec, du co tin khac chen vao.

Dung gap ngay 13/09/2026: tro ly hoi giai trinh chiet khau, chua kip tra loi thi da co tin
chuyen hang chen vao, va cau tra loi bi gan nham.
"""
from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from assistant.core import Assistant
from assistant.memory import Memory
from bc_agent.mock_client import MockBCClient

NV = "minh.s0002"


@pytest.fixture()
def asst():
    return Assistant(MockBCClient(), Memory(":memory:"))


def _hoi_giai_trinh(asst) -> tuple[int, str]:
    """Tro ly hoi mot cau giai trinh, tra ve (id tin hoi, exception id)."""
    exc = asst.gw.open_exceptions(5)[0]
    from assistant.skills import discount

    thu = asst.mem.user("thu.retailops")
    out = discount.on_ask_explanation(asst, thu, exc["id"])
    asst._deliver(out)
    nhan = [d for d in out if d.user_id != thu["user_id"]]
    assert nhan, "khong ai bi hoi"
    uid = nhan[0].user_id
    tin = [m for m in asst.mem.inbox(uid, 0) if m["direction"] == "out"][-1]
    return int(tin["id"]), exc["id"]


def test_tra_loi_dung_tin_thi_ghi_dung_exception(asst):
    tin_id, exc_id = _hoi_giai_trinh(asst)
    uid = asst.mem.message(tin_id)["user_id"]

    # Mot tin khac chen vao truoc khi nguoi ta kip tra loi.
    asst.handle_message(uid, "sắp hết Croissant plain")

    asst.handle_message(uid, "khách mua nguyên thùng nên tôi giảm thêm, có báo quản lý ca",
                        reply_to=tin_id)
    assert asst.gw.exception(exc_id).get("explanation"), "giai trinh khong duoc ghi vao dung exception"


def test_khong_bam_tra_loi_thi_van_chay_nhu_cu(asst):
    tin_id, exc_id = _hoi_giai_trinh(asst)
    uid = asst.mem.message(tin_id)["user_id"]
    asst.handle_message(uid, "khách mua nguyên thùng nên tôi giảm thêm, có báo quản lý ca")
    assert asst.gw.exception(exc_id).get("explanation")


def test_hop_thu_tra_kem_trich_dan(asst):
    tin_id, _ = _hoi_giai_trinh(asst)
    uid = asst.mem.message(tin_id)["user_id"]
    asst.handle_message(uid, "khách mua nguyên thùng nên tôi giảm thêm", reply_to=tin_id)
    tin = [m for m in asst.mem.inbox(uid, 0) if m["direction"] == "in"][-1]
    assert tin["reply_to"] == tin_id
    assert tin["trich"], "khong co trich dan de giao dien ve lai"


def test_api_nhan_reply_to(asst):
    from assistant.channels import web

    web.state["asst"] = asst
    c = TestClient(web.app)
    tin_id, exc_id = _hoi_giai_trinh(asst)
    uid = asst.mem.message(tin_id)["user_id"]
    r = c.post("/api/message", json={"user": uid, "text": "khách mua nguyên thùng nên giảm thêm",
                                     "reply_to": tin_id})
    assert r.status_code == 200
    assert asst.gw.exception(exc_id).get("explanation")


def test_tra_loi_tin_khong_co_that_thi_khong_lam_chet(asst):
    out = asst.handle_message(NV, "sắp hết Croissant plain", reply_to=999999)
    assert out
