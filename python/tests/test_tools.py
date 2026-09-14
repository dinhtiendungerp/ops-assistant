"""Test rang buoc cua tool layer tren MockBCClient. Chay: pytest -q"""
import json
import pytest

from bc_agent.mock_client import MockBCClient
from bc_agent.tools import ToolDispatcher


@pytest.fixture
def disp():
    return ToolDispatcher(MockBCClient(), run_id="test", model_name="test")


def test_transfer_requires_reading_suggestion_first(disp):
    out = json.loads(disp.dispatch("create_proposal", {
        "scenario": "StoreReplenishment", "action_type": "Transfer", "item_no": "33100",
        "from_location_code": "W0003", "to_location_code": "S0001", "quantity": 10,
        "reference_key": "S0001|33100", "rationale": "x", "priority_score": 50, "evidence": {}}))
    assert "error" in out and "list_replenishment_suggestions" in out["error"]


def test_transfer_cannot_exceed_constrained_qty(disp):
    rows = json.loads(disp.dispatch("list_replenishment_suggestions", {"stock_out_risk_only": True}))
    # Lay dong dau tien con chuyen duoc. Khong ghim ma cu the: mat hang han dung ngan bi chan
    # xuong 0 va danh sach do doi theo bo du lieu demo.
    sug = next(r for r in rows if float(r["constrainedQty"]) > 0)
    ref = f"{sug['storeLocationCode']}|{sug['itemNo']}"
    body = {"scenario": "StoreReplenishment", "action_type": "Transfer", "item_no": sug["itemNo"],
            "from_location_code": "W0003", "to_location_code": sug["storeLocationCode"],
            "reference_key": ref, "rationale": "x", "priority_score": 50, "evidence": {}}
    out = json.loads(disp.dispatch("create_proposal", {**body, "quantity": sug["constrainedQty"] + 1}))
    assert "error" in out and "constrainedQty" in out["error"]
    ok = json.loads(disp.dispatch("create_proposal", {**body, "quantity": sug["constrainedQty"]}))
    assert ok["status"] == "Proposed"


def test_duplicate_reference_key_rejected(disp):
    body = {"scenario": "InventoryHealth", "action_type": "ReviewOnly", "reference_key": "A|B|C",
            "rationale": "x", "priority_score": 10, "evidence": {"a": 1}}
    assert "proposalId" in json.loads(disp.dispatch("create_proposal", body))
    assert "error" in json.loads(disp.dispatch("create_proposal", body))


def test_agent_cannot_confirm_exception(disp):
    exc = json.loads(disp.dispatch("list_discount_exceptions", {"status": "Open", "top": 1}))[0]
    ok = json.loads(disp.dispatch("mark_exception_under_review", {"exception_id": exc["id"]}))
    assert ok["status"] == "UnderReview"
    with pytest.raises(RuntimeError):
        disp.client.patch("discountExceptions", exc["id"], {"status": "Confirmed"})


def test_max_proposals_per_run(disp, monkeypatch):
    from bc_agent import tools
    import dataclasses
    monkeypatch.setattr(tools, "settings", dataclasses.replace(tools.settings, max_proposals_per_run=2))
    for i in range(2):
        assert "proposalId" in json.loads(disp.dispatch("create_proposal", {
            "scenario": "InventoryHealth", "action_type": "ReviewOnly", "reference_key": f"K{i}",
            "rationale": "x", "priority_score": 1, "evidence": {}}))
    out = json.loads(disp.dispatch("create_proposal", {
        "scenario": "InventoryHealth", "action_type": "ReviewOnly", "reference_key": "K9",
        "rationale": "x", "priority_score": 1, "evidence": {}}))
    assert "gioi han" in out["error"]
