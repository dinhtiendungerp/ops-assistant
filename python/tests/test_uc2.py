"""Test cho lop noi UC2 voi du lieu that.

Khong goi mang. BCData bi thay bang ban gia.
"""
from __future__ import annotations

from datetime import date, timedelta

import pytest

from bc_agent import uc2


class _FakeData:
    def __init__(self, ile, items):
        self._ile, self._items = ile, items
        self.calls: list[str] = []

    def item_ledger_entries(self, conds=None, top=None, newest_first=True):
        self.calls.append("ile")
        return list(self._ile)

    def items(self, conds=None, top=None):
        self.calls.append("items")
        return list(self._items)


TODAY = date(2026, 9, 18)

# Bon to hop, moi cai roi vao mot phan tang khac nhau.
ILE = [
    # 33170 tai S0001: lo qua han, con ton
    {"posting_date": date(2026, 9, 1), "entry_type": "Purchase", "item_no": "33170",
     "location_code": "S0001", "lot_no": "L1", "expiration_date": date(2026, 9, 15), "quantity": 30},
    {"posting_date": date(2026, 9, 10), "entry_type": "Sale", "item_no": "33170",
     "location_code": "S0001", "lot_no": "L1", "expiration_date": date(2026, 9, 15), "quantity": -20},
    # 33110 tai S0002: ban deu, ton mong, rui ro dut hang
    {"posting_date": date(2026, 8, 1), "entry_type": "Purchase", "item_no": "33110",
     "location_code": "S0002", "lot_no": None, "expiration_date": None, "quantity": 500},
    *[{"posting_date": date(2026, 8, 1) + timedelta(days=i),
       "entry_type": "Sale", "item_no": "33110", "location_code": "S0002", "lot_no": None,
       "expiration_date": None, "quantity": -10} for i in range(48)],
    # 30091 tai W0003: khong co dong ban nao gan day, cham luan chuyen
    {"posting_date": date(2026, 3, 25), "entry_type": "Purchase", "item_no": "30091",
     "location_code": "W0003", "lot_no": None, "expiration_date": None, "quantity": 40},
]

ITEMS = [
    {"item_no": "33170", "description": "Chocolate cake", "unit_cost": 5.5},
    {"item_no": "33110", "description": "Croissant - chocolate", "unit_cost": 1.2},
    {"item_no": "30091", "description": "Flavored syrup", "unit_cost": 2.8},
]


@pytest.fixture()
def data():
    return _FakeData(ILE, ITEMS)


def test_fetch_doc_ca_hai_nguon_va_danh_chi_muc_theo_ma_hang(data):
    ile, items = uc2.fetch(data)
    assert data.calls == ["ile", "items"]
    assert len(ile) == len(ILE)
    assert set(items) == {"33170", "33110", "30091"}
    assert items["33170"]["unit_cost"] == 5.5


def test_phan_tang_du_sau_nhan_ke_ca_nhan_khong_co_dong_nao():
    lines, _ = uc2.run(ILE, {i["item_no"]: i for i in ITEMS}, TODAY)
    counts = uc2.tier_counts(lines)
    assert list(counts) == uc2.TIERS
    assert counts["Expired"] == 1
    assert counts["SlowMoving"] == 1
    assert sum(counts.values()) == len(lines)


def test_lo_qua_han_duoc_nhan_dung():
    lines, _ = uc2.run(ILE, {i["item_no"]: i for i in ITEMS}, TODAY)
    expired = [x for x in lines if x.tier == "Expired"]
    assert len(expired) == 1
    assert (expired[0].item_no, expired[0].lot_no, expired[0].quantity) == ("33170", "L1", 10)
    assert expired[0].days_to_expiry == -3


def test_snapshot_du_khoa_de_doi_chieu():
    lines, sugg = uc2.run(ILE, {i["item_no"]: i for i in ITEMS}, TODAY)
    snap = uc2.snapshot(lines, sugg, TODAY)
    assert snap["today"] == "2026-09-18"
    assert snap["so_dong"] == len(lines)
    assert set(snap["tier_counts"]) == set(uc2.TIERS)
    assert set(snap["tier_quantities"]) == set(uc2.TIERS)


def test_compare_trung_thi_khong_bao_gi():
    lines, sugg = uc2.run(ILE, {i["item_no"]: i for i in ITEMS}, TODAY)
    snap = uc2.snapshot(lines, sugg, TODAY)
    assert uc2.compare(snap, snap) == []


def test_compare_chi_ro_tung_cho_lech():
    lines, sugg = uc2.run(ILE, {i["item_no"]: i for i in ITEMS}, TODAY)
    actual = uc2.snapshot(lines, sugg, TODAY)
    expected = uc2.snapshot(lines, sugg, TODAY)
    expected["tier_counts"] = dict(expected["tier_counts"])
    expected["tier_counts"]["Expired"] += 1
    expected["so_de_xuat_dieu_chuyen"] += 2

    diffs = uc2.compare(actual, expected)
    assert any("Expired" in d for d in diffs)
    assert any("so_de_xuat_dieu_chuyen" in d for d in diffs)


def test_compare_bao_ca_khi_lech_ngay_neo():
    lines, sugg = uc2.run(ILE, {i["item_no"]: i for i in ITEMS}, TODAY)
    actual = uc2.snapshot(lines, sugg, TODAY)
    expected = dict(actual, today="2026-09-11")
    assert any("ngay neo" in d for d in uc2.compare(actual, expected))


def test_bao_cao_in_du_sau_phan_tang_va_khong_vo_khi_thieu_han_dung():
    lines, sugg = uc2.run(ILE, {i["item_no"]: i for i in ITEMS}, TODAY)
    text = uc2.format_report(lines, sugg, ILE, TODAY, top=3)
    for tier in uc2.TIERS:
        assert uc2.TIER_VI[tier] in text
    assert "2026-09-18" in text


def test_snapshot_tu_bang_ket_qua_al_cung_khoa_voi_snapshot_python():
    """Reconcile --from al doc inventoryHealthLines va replenishmentSuggestions. Bo con so
    phai cung khoa voi snapshot() de compare() dung duoc, va tier la ten enum cua AL."""
    health = [
        {"tier": "Expired", "quantityOnHand": 10, "asOfDate": "2026-09-18"},
        {"tier": "Expired", "quantityOnHand": 5.5, "asOfDate": "2026-09-18"},
        {"tier": "Healthy", "quantityOnHand": 100, "asOfDate": "2026-09-18"},
        {"tier": "LaLam", "quantityOnHand": 1, "asOfDate": "2026-09-18"},
    ]
    sugg = [
        {"stockOutRisk": True, "cappedByShelfLife": True},
        {"stockOutRisk": True, "cappedByShelfLife": False},
        {"stockOutRisk": False, "cappedByShelfLife": True},
    ]
    snap = uc2.snapshot_from_al(health, sugg)
    assert snap["today"] == "2026-09-18"
    assert snap["tier_counts"]["Expired"] == 2 and snap["tier_counts"]["Healthy"] == 1
    assert snap["tier_quantities"]["Expired"] == 15.5
    assert snap["so_de_xuat_dieu_chuyen"] == 2
    assert snap["so_de_xuat_bi_chan_boi_han_dung"] == 1
    assert snap["tier_la"] == {"LaLam": 1}
    lines, s2 = uc2.run(ILE, {i["item_no"]: i for i in ITEMS}, TODAY)
    assert set(uc2.snapshot(lines, s2, TODAY)) <= set(snap) | {"tier_la"}
