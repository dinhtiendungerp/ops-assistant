"""Luong 5.1 va rang buoc cua tro ly tren mock BC."""
import pytest

from assistant.core import Assistant
from assistant.memory import Memory
from bc_agent.mock_client import MockBCClient


@pytest.fixture
def a():
    return Assistant(MockBCClient(), Memory(":memory:"))


def _texts(ds, user):
    return " | ".join(d.text for d in ds if d.user_id == user)


def test_stockout_creates_proposal_and_notifies_dispatcher(a):
    out = a.handle_message("lan.s0001", "sắp hết Croissant plain")
    assert any(d.user_id == "hung.dieuphoi" and d.card and d.card.actions[0].id == "approve" for d in out)
    prop = a.mem.proposals("Proposed")[0]
    assert prop["item_no"] == "33100" and prop["to_loc"] == "S0001" and prop["quantity"] > 0
    assert prop["quantity"] <= prop["max_quantity"]


def test_store_manager_cannot_approve(a):
    a.handle_message("lan.s0001", "sắp hết Croissant plain")
    prop = a.mem.proposals("Proposed")[0]
    out = a.handle_action("lan.s0001", "approve", prop["proposal_id"])
    assert "không có quyền" in out[0].text
    assert a.mem.proposal(prop["proposal_id"])["status"] == "Proposed"


def test_edit_cannot_exceed_available(a):
    a.handle_message("lan.s0001", "sắp hết Croissant plain")
    prop = a.mem.proposals("Proposed")[0]
    out = a.handle_action("hung.dieuphoi", "edit", prop["proposal_id"], {"quantity": prop["max_quantity"] + 1})
    assert "Số lượng phải" in out[0].text


def test_approve_creates_transfer_under_approver_and_schedules_followups(a):
    a.handle_message("lan.s0001", "sắp hết Croissant plain")
    prop = a.mem.proposals("Proposed")[0]
    out = a.handle_action("hung.dieuphoi", "approve", prop["proposal_id"])
    p = a.mem.proposal(prop["proposal_id"])
    assert p["status"] == "Executed" and p["result_doc"].startswith("TO-")
    t = a.gw.transfer(p["result_doc"])
    assert t["createdBy"] == "HUNG" and t["status"] == "Open"
    assert {d.user_id for d in out} >= {"hung.dieuphoi", "lan.s0001", "kho.w0003"}
    kinds = {f["kind"] for f in a.mem.followups()}
    assert kinds == {"transfer_ship", "transfer_receive"}


def test_followup_nudges_then_escalates(a):
    a.handle_message("lan.s0001", "sắp hết Croissant plain")
    prop = a.mem.proposals("Proposed")[0]
    a.handle_action("hung.dieuphoi", "approve", prop["proposal_id"])
    a.mem.advance_clock(20)
    out1 = a.run_followups()
    assert [d.user_id for d in out1] == ["kho.w0003"]
    a.mem.advance_clock(6)
    out2 = a.run_followups()
    assert {d.user_id for d in out2} == {"kho.w0003", "hung.dieuphoi"}
    to = a.mem.proposal(prop["proposal_id"])["result_doc"]
    a.handle_action("kho.w0003", "ship", to)
    a.mem.advance_clock(6)
    assert all(d.user_id != "kho.w0003" for d in a.run_followups())


def test_discount_explanation_roundtrip(a):
    brief = a.morning_brief("thu.retailops")
    exc_id = next(d.ref for d in brief if d.card)
    out = a.handle_action("thu.retailops", "ask_explanation", exc_id)
    manager = next(d.user_id for d in out if d.user_id != "thu.retailops")
    assert a.mem.pending_question(manager)
    out2 = a.handle_message(manager, "hàng trưng bày xả cuối ngày, có duyệt miệng")
    assert a.gw.exception(exc_id)["status"] == "Explained"
    assert any(d.user_id == "thu.retailops" and d.card and {x.id for x in d.card.actions} == {"confirm_exception", "dismiss_exception"} for d in out2)
    # quan ly cua hang khong ket luan duoc
    assert "Chỉ Retail Ops" in a.handle_action(manager, "confirm_exception", exc_id)[0].text


def test_brief_skips_items_already_in_flight(a):
    a.handle_message("lan.s0001", "sắp hết Croissant plain")
    prop = a.mem.proposals("Proposed")[0]
    a.handle_action("hung.dieuphoi", "approve", prop["proposal_id"])
    brief = a.morning_brief("hung.dieuphoi")
    # Cap S0001 x 33100 da co hang dang ve thi brief khong de xuat lai; cac cua hang khac van duoc de xuat
    assert all(d.text != "S0001 / Croissant - plain" for d in brief)
    assert any(d.text.endswith("/ Croissant - plain") for d in brief)


def test_stock_query(a):
    out = a.handle_message("lan.s0001", "còn bao nhiêu Chocolate ice cream")
    assert "Chocolate ice cream" in out[0].text and "S0001" in out[0].text


# ---------------------------------------------------------------- giai trinh chiet khau
def _hoi_giai_trinh(a):
    """Retail Ops hoi giai trinh, tra ve (user_id quan ly cua hang, exc_id)."""
    brief = a.morning_brief("thu.retailops")
    exc_id = next(d.ref for d in brief if d.card)
    out = a.handle_action("thu.retailops", "ask_explanation", exc_id)
    manager = next(d.user_id for d in out if d.user_id != "thu.retailops")
    return manager, exc_id


def test_go_ok_khong_duoc_tinh_la_giai_trinh(a):
    """Nguoi ta hay go 'ok' theo phan xa roi moi noi ly do that. Nhan bua cau dau thi ho so
    con lai mot chu 'ok', va cau that bi roi ra ngoai vi cau hoi da dong."""
    manager, exc_id = _hoi_giai_trinh(a)
    out = a.handle_message(manager, "ok")
    assert "lý do" in out[0].text
    assert a.mem.pending_question(manager), "cau hoi phai con treo de nguoi dung go lai"
    assert not a.gw.exception(exc_id).get("explanation")

    out2 = a.handle_message(manager, "khách mua nguyên thùng nên giảm thêm, có báo quản lý ca")
    assert "ghi lại" in out2[0].text
    assert a.gw.exception(exc_id)["status"] == "Explained"


def test_noi_nham_thi_mo_lai_cau_hoi_de_go_lai(a):
    manager, exc_id = _hoi_giai_trinh(a)
    a.handle_message(manager, "hàng trưng bày xả cuối ngày, có duyệt miệng")
    assert a.gw.exception(exc_id)["explanation"].startswith("hàng trưng bày")

    out = a.handle_message(manager, "tôi nhầm")
    assert "gõ lại" in out[0].text
    assert a.mem.pending_question(manager)
    a.handle_message(manager, "thật ra là khách đoàn đặt trước, có phiếu duyệt của quản lý")
    assert a.gw.exception(exc_id)["explanation"].startswith("thật ra là khách đoàn")


def test_ket_luan_roi_thi_khong_sua_giai_trinh_nua(a):
    manager, exc_id = _hoi_giai_trinh(a)
    a.handle_message(manager, "hàng trưng bày xả cuối ngày, có duyệt miệng")
    a.handle_action("thu.retailops", "confirm_exception", exc_id)
    out = a.handle_message(manager, "tôi nhầm")
    assert "đã kết luận" in out[0].text
    assert not a.mem.pending_question(manager)
