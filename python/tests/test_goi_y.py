"""Prompt mau theo vai tro (assistant/goi_y.py) phai chay duoc: dung intent, co skill tra loi, khong roi vao cau tro giup.

Cau danh dau can_ai chi kiem la co trong danh sach; tat AI thi planner ban ghi tu choi cau moi, dung nhu thiet ke.
"""
from __future__ import annotations

import pytest

from assistant import goi_y
from assistant.core import Assistant, DEMO_USERS
from assistant.memory import Memory
from assistant.nlu import RuleNLU
from bc_agent.mock_client import MockBCClient

CAC_CAU = [(u["user_id"], g) for u in DEMO_USERS for g in goi_y.cho_nguoi_dung(u)]


@pytest.fixture(scope="module")
def asst():
    return Assistant(MockBCClient(), Memory(":memory:"))


def test_moi_vai_co_it_nhat_bon_goi_y():
    for u in DEMO_USERS:
        assert len(goi_y.cho_nguoi_dung(u)) >= 4, u["user_id"]


@pytest.mark.parametrize("uid,g", CAC_CAU, ids=[f"{u}:{g['ten']}" for u, g in CAC_CAU])
def test_rule_ra_dung_intent(uid, g):
    assert RuleNLU().parse(g["cau"]).intent == g["intent"]


@pytest.mark.parametrize("uid,g", [(u, g) for u, g in CAC_CAU if not g["can_ai"]],
                         ids=[f"{u}:{g['ten']}" for u, g in CAC_CAU if not g["can_ai"]])
def test_cau_mau_co_cau_tra_loi_that(asst, uid, g):
    out = asst.handle_message(uid, g["cau"])
    assert out, g["cau"]
    d = out[0]
    assert not d.meta.get("unresolved"), d.text
    assert "chưa trả lời được" not in d.text, d.text


def test_quan_ly_cua_hang_hoi_ton_thi_noi_cua_hang_minh_truoc(asst):
    out = asst.handle_message("lan.s0001", "Choco nuts ở cửa hàng tôi còn bao nhiêu")
    assert out[0].text.startswith("Choco nuts tại S0001")
