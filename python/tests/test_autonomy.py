"""Test phan tu chu: policy, shadow mode, hoan tac, dieu tra, tu cham diem."""
import pytest

from assistant.core import Assistant
from assistant.memory import Memory
from assistant.policy import PolicyEngine
from assistant.skills import investigate, review
from bc_agent.mock_client import MockBCClient


@pytest.fixture
def auto():
    a = Assistant(MockBCClient(), Memory(":memory:"))
    a.policy = PolicyEngine(shadow=False)
    return a


@pytest.fixture
def shadow():
    a = Assistant(MockBCClient(), Memory(":memory:"))
    a.policy = PolicyEngine(shadow=True)
    return a


def test_shadow_mode_does_not_act(shadow):
    out = shadow.handle_message("lan.s0001", "sắp hết Croissant plain")
    prop = shadow.mem.proposals()[0]
    assert prop["status"] == "Proposed" and prop["result_doc"] is None
    card = next(d.card for d in out if d.card)
    assert "Shadow mode" in card.body and {a.id for a in card.actions} == {"approve", "edit", "reject"}


def test_autonomy_executes_and_offers_undo(auto):
    out = auto.handle_message("lan.s0001", "sắp hết Croissant plain")
    prop = auto.mem.proposals()[0]
    assert prop["status"] == "Executed" and prop["policy_rule"] == "P-01"
    assert prop["approver"] == "agent:P-01"
    # chung tu tao duoi tai khoan tro ly, khong muon danh nguoi
    assert auto.gw.transfer(prop["result_doc"])["createdBy"] == auto.agent_bc_user
    card = next(d.card for d in out if d.user_id == "hung.dieuphoi" and d.card)
    assert "undo" in {a.id for a in card.actions}


def test_high_value_still_needs_human(auto):
    auto.policy.rules[0].max_value_vnd = 10
    auto.handle_message("lan.s0001", "sắp hết Croissant plain")
    prop = auto.mem.proposals()[0]
    assert prop["status"] == "Proposed" and prop["policy_mode"] == "approve"


def test_kill_switch_stops_all_autonomy(auto):
    auto.policy.kill_switch = True
    auto.handle_message("lan.s0001", "sắp hết Croissant plain")
    prop = auto.mem.proposals()[0]
    assert prop["status"] == "Proposed" and prop["policy_rule"] == "KILL"


def test_daily_auto_cap(auto):
    auto.policy.daily_auto_cap = 1
    auto.handle_message("lan.s0001", "sắp hết Croissant plain")
    auto.handle_message("tuan.s0005", "sắp hết Blueberry muffin")
    assert sorted(p["status"] for p in auto.mem.proposals()) == ["Executed", "Proposed"]


def test_undo_reverses_and_records_feedback(auto):
    auto.handle_message("lan.s0001", "sắp hết Croissant plain")
    prop = auto.mem.proposals()[0]
    auto.handle_action("hung.dieuphoi", "undo", prop["proposal_id"], {"reason": "chưa cần"})
    assert auto.gw.transfer(prop["result_doc"])["status"] == "Cancelled"
    assert auto.mem.feedback()[0]["kind"] == "undo"
    assert auto.gw.suggestion(prop["to_loc"], prop["item_no"])["storeQtyInTransit"] == 0


def test_undo_blocked_after_ship(auto):
    auto.handle_message("lan.s0001", "sắp hết Croissant plain")
    prop = auto.mem.proposals()[0]
    auto.handle_action("kho.w0003", "ship", prop["result_doc"])
    assert "đã ship" in auto.handle_action("hung.dieuphoi", "undo", prop["proposal_id"], {})[0].text


def test_store_manager_cannot_undo(auto):
    auto.handle_message("lan.s0001", "sắp hết Croissant plain")
    prop = auto.mem.proposals()[0]
    assert "Chỉ điều phối" in auto.handle_action("lan.s0001", "undo", prop["proposal_id"], {})[0].text


def test_investigation_is_honest_when_no_pattern(auto):
    # S0001 x Choco nuts chua co can thiep nao nen van o bac 1: cau hoi "vi sao" di vao skill investigate
    out = auto.handle_message("trang.sc", "sao Cửa hàng Quận 1 cứ hết Choco nuts")
    card = next(d.card for d in out if d.card)
    assert "chưa đủ tập trung" in card.body or "không thấy chênh lệch" in card.body
    assert "Đọc" in investigate.show_steps(auto, auto.mem.user("trang.sc"), card.ref)[0].text


def test_investigation_fix_is_stored_as_override(auto):
    auto.handle_message("trang.sc", "sao Cửa hàng Quận 1 cứ hết Choco nuts")
    auto.handle_action("trang.sc", "inv_apply", "inv|S0001|33323", {})
    assert "S0001|33323" in auto.mem.overrides()


def test_self_review_scores_own_work(auto):
    auto.handle_message("lan.s0001", "sắp hết Croissant plain")
    out = review.run_self_review(auto, auto.mem.user("trang.sc"))
    assert "chấm lại" in out[0].text
    prop = auto.mem.proposals()[0]
    assert auto.mem.proposal(prop["proposal_id"])["outcome"] in ("good", "bad", "unknown")


def test_self_review_flags_bad_policy(auto):
    for u, q in [("lan.s0001", "sắp hết Croissant plain"), ("tuan.s0005", "sắp hết Blueberry muffin"), ("ha.s0010", "sắp hết Carrot cake")]:
        auto.handle_message(u, q)
    for p in auto.mem.proposals():
        if p["status"] == "Executed":
            auto.handle_action("hung.dieuphoi", "undo", p["proposal_id"], {"reason": "sai"})
    review.run_self_review(auto, auto.mem.user("trang.sc"))
    assert any("P-01" in s for s in auto.mem.recall("self-review")["suggestions"])
