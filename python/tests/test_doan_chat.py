"""Doan chat: mo doan moi, tin cu khong mat, mo lai doc duoc.

Dung yeu cau ngay 13/09/2026: "co co che nao luu lich su chat khong, roi mo doan chat moi
nhu cac agent thuc su khong".
"""
from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from assistant.core import Assistant
from assistant.memory import Memory
from bc_agent.mock_client import MockBCClient

AI = "lan.s0001"


@pytest.fixture()
def asst():
    return Assistant(MockBCClient(), Memory(":memory:"))


@pytest.fixture()
def client(asst):
    from assistant.channels import web

    web.state["asst"] = asst
    return TestClient(web.app)


def test_doan_moi_thi_hop_thu_rong_nhung_tin_cu_van_con(asst):
    asst.handle_message(AI, "sắp hết Croissant plain")
    cu = asst.mem.inbox(AI, 0)
    assert len(cu) >= 2

    asst.mem.doan_moi(AI)
    assert asst.mem.inbox(AI, 0) == []                     # doan moi thi trong

    tong = asst.mem.conn.execute(
        "SELECT COUNT(*) n FROM messages WHERE user_id=?", (AI,)).fetchone()["n"]
    assert tong == len(cu), "tin cu bi mat khi mo doan moi"


def test_mo_lai_doan_cu_thi_doc_duoc_tin_cu(asst):
    asst.handle_message(AI, "sắp hết Croissant plain")
    doan_cu = asst.mem.doan_dang_mo(AI)
    n_cu = len(asst.mem.inbox(AI, 0))

    asst.mem.doan_moi(AI)
    asst.handle_message(AI, "còn bao nhiêu Chocolate ice cream")
    assert len(asst.mem.inbox(AI, 0)) < n_cu + 2           # chi thay tin cua doan moi

    asst.mem.mo_doan(AI, doan_cu)
    assert len(asst.mem.inbox(AI, 0)) == n_cu


def test_ten_doan_lay_cau_dau_nguoi_dung_go(asst):
    asst.handle_message(AI, "sắp hết Croissant plain")
    d = asst.mem.cac_doan(AI)
    assert d[0]["dang_mo"] is True
    assert "Croissant" in d[0]["ten"]
    assert d[0]["so_tin"] >= 2


def test_bam_doan_moi_hai_lan_khong_sinh_hai_dong_rong(asst):
    asst.handle_message(AI, "sắp hết Croissant plain")
    asst.mem.doan_moi(AI)
    asst.mem.doan_moi(AI)
    rong = [d for d in asst.mem.cac_doan(AI) if d["so_tin"] == 0]
    assert len(rong) == 1


def test_moi_vai_tro_co_doan_rieng(asst):
    asst.handle_message(AI, "sắp hết Croissant plain")
    asst.handle_message("minh.s0002", "sắp hết Croissant plain")
    assert asst.mem.doan_dang_mo(AI) != asst.mem.doan_dang_mo("minh.s0002")
    assert all(m["user_id"] == AI for m in asst.mem.inbox(AI, 0))


def test_api_doi_doan(client, asst):
    asst.handle_message(AI, "sắp hết Croissant plain")
    cu = asst.mem.doan_dang_mo(AI)

    r = client.post("/api/doan-chat", json={"user": AI}).json()
    assert any(d["dang_mo"] and d["so_tin"] == 0 for d in r["doan"])

    r = client.post("/api/doan-chat", json={"user": AI, "conv_id": cu}).json()
    assert next(d for d in r["doan"] if d["dang_mo"])["conv_id"] == cu
    assert client.get(f"/api/doan-chat?user={AI}").status_code == 200
    assert client.post("/api/doan-chat", json={"user": "khong-co-ai"}).status_code == 404
