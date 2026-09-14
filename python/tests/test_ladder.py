"""UC1 + UC2 + UC5: nhu cau that, bac thang chan doan, va bang chung do nguoi dua vao."""
from __future__ import annotations

from datetime import date

import pytest

from assistant.core import Assistant
from assistant.memory import Memory
from assistant.skills import demand, evidence, ladder
from bc_agent.mock_client import MockBCClient

PAIR = ("33200", "S0001")
ASK = "sao Cửa hàng Quận 1 cứ hết Chocolate ice cream"
FAIR = "Cửa hàng Quận 1 tháng 8 có hội chợ ngay trước cửa hàng, bán gấp đôi, giờ hết rồi"


@pytest.fixture()
def a():
    x = Assistant(MockBCClient(), Memory(":memory:"))
    x.policy.shadow = False
    return x


# ---------- UC1: so lieu dau vao bi bop meo
def test_ngay_dut_hang_khong_phai_ngay_nhu_cau_bang_khong(a):
    v = demand.view(a, *PAIR)
    assert v.stockout_days, "phai nhan ra duoc ngay dut hang"
    assert v.corrected_daily > v.naive_daily
    assert v.uplift_pct > 20


def test_gop_ngay_lien_tiep_thanh_dot(a):
    d = [date(2026, 8, 25), date(2026, 8, 26), date(2026, 8, 27), date(2026, 9, 4)]
    assert demand.episodes(d) == [(date(2026, 8, 25), date(2026, 8, 27)), (date(2026, 9, 4), date(2026, 9, 4))]


def test_noi_rong_cua_so_khi_khong_du_ngay_sach(a):
    demand.add_exception(a, *PAIR, date(2026, 8, 1), date(2026, 8, 31), "hội chợ", "test")
    v = demand.view(a, *PAIR)
    assert v.widened and v.window > demand.WINDOW
    assert v.usable_days >= 10


# ---------- UC5: bac thang
def test_lap_lai_thi_doi_loai_cach_sua(a):
    d = ladder.diagnose(a, *PAIR)
    assert d["level"] == 2 and d["action"] == "AdjustParameter"
    assert len(d["transfers"]) == 2          # lich su nam trong BC, khong nam trong bo nho tro ly


def test_cap_chua_tung_hong_thi_van_o_bac_mot(a):
    assert ladder.diagnose(a, "33200", "S0002")["level"] == 1


def test_nguong_de_xuat_khong_chay_theo_so_dot(a):
    """Loi da nghi den khi thiet ke: neu nguong scale theo so dot dut hang thi mot thang xau
    se day nguong len vinh vien. Cong thuc phai giai thich duoc bang mot cau."""
    assert ladder.diagnose(a, *PAIR)["suggested_rop"] == ladder.TRANSFER_LEAD_DAYS * 2 + 3


def test_doi_nguong_luon_phai_qua_nguoi(a):
    out = a.handle_message("trang.sc", ASK)
    prop = a.mem.proposals()[0]
    assert prop["policy_mode"] == "approve" and prop["policy_rule"] == "P-09"
    assert prop["status"] == "Proposed"       # khong duoc tu lam du dang bat che do tu chu


# ---------- Bang chung do nguoi dua vao
def test_mot_cau_cua_nguoi_lam_tro_ly_rut_de_xuat_cua_chinh_no(a):
    ref = a.handle_message("trang.sc", ASK)[0].ref
    before = demand.view(a, *PAIR).corrected_daily
    out = a.handle_action("trang.sc", "lad_evidence", ref, {"text": FAIR})
    assert a.mem.proposal(ref)["status"] == "Rejected"
    assert demand.view(a, *PAIR).corrected_daily < before
    assert "rút lại đề xuất" in out[0].card.body


def test_tro_ly_nho_va_khong_de_xuat_lai_thu_vua_bi_bac(a):
    ref = a.handle_message("trang.sc", ASK)[0].ref
    a.handle_action("trang.sc", "lad_evidence", ref, {"text": FAIR})
    notes = a.mem.recall("ladder:S0001|33200")
    assert notes["evidence_rounds"] == 1 and notes["one_off"]


def test_dot_nam_trong_cua_so_su_kien_khong_con_tinh_vao_bac(a):
    before = len(ladder.diagnose(a, *PAIR)["episodes"])
    demand.add_exception(a, *PAIR, date(2026, 8, 1), date(2026, 9, 3), "hội chợ", "test")
    assert len(ladder.diagnose(a, *PAIR)["episodes"]) < before


def test_khong_doc_duoc_khoang_ngay_thi_hoi_lai_chu_khong_doan(a):
    ref = a.handle_message("trang.sc", ASK)[0].ref
    out = a.handle_action("trang.sc", "lad_evidence", ref, {"text": "tại dạo này khách đông hơn ấy mà"})
    assert "khoảng ngày" in out[0].text
    assert a.mem.proposal(ref)["status"] == "Proposed"     # chua rut de xuat khi chua hieu


def test_muc_nen_doi_han_thi_giu_nguyen_de_xuat(a):
    ref = a.handle_message("trang.sc", ASK)[0].ref
    out = a.handle_action("trang.sc", "lad_evidence", ref, {"text": "bên cạnh mở thêm văn phòng, từ nay đông hơn lâu dài"})
    assert "giữ nguyên đề xuất" in out[0].text
    assert a.mem.proposal(ref)["status"] == "Proposed"


def test_van_de_nguon_cung_thi_nang_nguong_khong_giai_quyet_gi(a):
    ref = a.handle_message("trang.sc", ASK)[0].ref
    out = a.handle_action("trang.sc", "lad_evidence", ref, {"text": "nhà máy không kịp sản xuất, kho cũng hết"})
    assert "nguồn cung" in out[0].text


def test_duyet_nang_nguong_thi_lan_sau_len_bac_ba(a):
    ref = a.handle_message("trang.sc", ASK)[0].ref
    a.handle_action("trang.sc", "lad_approve", ref, {})
    assert a.mem.recall("ladder:S0001|33200")["rop_raised"] == 9
    assert ladder.diagnose(a, *PAIR)["level"] == 3


def test_quan_ly_cua_hang_khong_doi_duoc_nguong(a):
    ref = a.handle_message("trang.sc", ASK)[0].ref
    out = a.handle_action("lan.s0001", "lad_approve", ref, {})
    assert "không" in out[0].text.lower() or "Chỉ" in out[0].text


def test_rule_evidence_doc_duoc_khoang_ngay_viet_ro():
    r = evidence.RuleEvidence()
    c = r.classify("hội chợ từ 8/8 đến 24/8", date(2026, 9, 18))
    assert c["kind"] == "one_off" and c["from"] == date(2026, 8, 8) and c["to"] == date(2026, 8, 24)
    c2 = r.classify("giữa tháng 8 có sự kiện", date(2026, 9, 18))
    assert c2["from"] == date(2026, 8, 11) and c2["to"] == date(2026, 8, 20)
