"""Go "phuong an xu ly cho X" phai chay D4, khong roi vao planner (Dung go tay toi 16/09/2026, planner tra loi lac de)."""
from __future__ import annotations

from assistant.core import Assistant
from assistant.nlu import RuleNLU
from assistant.skills import uc2_hanh_dong
from bc_agent.mock_client import MockBCClient


def test_rule_nhan_ra_d4_kem_mat_hang_va_cua_hang():
    it = RuleNLU().parse("phương án xử lý cho Choco pillar ở S0010")
    assert it.intent == "D4" and it.store_hint == "S0010" and "Choco pillar" in it.item_text


def test_cau_phuong_an_ra_the_phuong_an_cua_lo_can_date():
    client = MockBCClient()
    a = Assistant(client)
    r = next(x for x in client.data["inventoryHealthLines"] if x["tier"] == "NearExpiry" and (x.get("daysToExpiry") or 0) > 0)
    out = a.handle_message("trang.sc", f"phương án xử lý cho {r['itemDescription']} ở {r['locationCode']}")
    the = [d for d in out if d.card]
    assert the and the[0].text.startswith("Phương án cho " + r["itemDescription"])
    assert not any(d.meta.get("unresolved") for d in out)


def test_khong_co_mat_hang_thi_tra_unresolved():
    a = Assistant(MockBCClient())
    it = RuleNLU().parse("phương án xử lý")
    out = uc2_hanh_dong.tu_cau(a, a.mem.user("trang.sc"), it, "phương án xử lý")
    assert out[0].meta.get("unresolved")
