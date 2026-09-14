"""Chay lop tinh toan UC2 tren dung bo du lieu demo sap import vao company NWV.

Bo du lieu do duoc sinh boi tools/make_demo_data.py, deterministic theo seed, nen day vua la
test cua lop tinh toan vua la ban doi chieu cho con so ghi trong README cua bo du lieu.
Neu ai sua nguong hoac sua kich ban ma khong cap nhat tai lieu, test nay do.
"""
from __future__ import annotations

import sys
from datetime import date
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tools"))

from bc_agent.inventory import (Thresholds, demand_profiles, inventory_health,  # noqa: E402
                                positions, replenishment)

TODAY = date(2026, 9, 18)
WH = "W0003"
# Doc thang tu kich ban, khong chep lai: doi TRACKED trong demo_scenario thi test phai
# di theo chu khong phai bao do.
from demo_scenario import TRACKED  # noqa: E402


@pytest.fixture(scope="module")
def ile():
    from make_demo_data import journal_rows_to_ile, simulate

    rows, _ = simulate()
    return journal_rows_to_ile(rows)


@pytest.fixture(scope="module")
def items():
    from demo_scenario import ITEMS

    return {i.no: {"description": i.desc, "item_category": i.cat, "unit_cost": i.cost} for i in ITEMS}


def test_bo_du_lieu_dung_quy_mo(ile):
    assert 24000 <= len(ile) <= 26000
    assert min(r["posting_date"] for r in ile) == date(2026, 3, 22)
    assert max(r["posting_date"] for r in ile) == TODAY


def test_chi_mat_hang_co_tracking_moi_co_lot_va_han_dung(ile):
    for r in ile:
        assert bool(r["lot_no"]) == (r["item_no"] in TRACKED), r["item_no"]
        assert bool(r["expiration_date"]) == (r["item_no"] in TRACKED), r["item_no"]


def test_khong_lo_nao_am(ile):
    for p in positions(ile):
        assert p.quantity > 0


def test_han_dung_da_dang_chu_khong_phai_mot_hai_gia_tri(ile):
    by_item: dict[str, set] = {}
    for r in ile:
        if r["expiration_date"]:
            by_item.setdefault(r["item_no"], set()).add(r["expiration_date"])
    assert set(by_item) == TRACKED
    for item_no, exps in by_item.items():
        assert len(exps) >= 30, f"{item_no} chi co {len(exps)} han dung"


def test_kho_khong_bi_coi_la_khong_co_nhu_cau(ile):
    """Kho xuat hang bang Negative Adjmt. chu khong phai dong Sale. Neu chi dem dong Sale
    thi moi lo o kho se roi vao nhom cham luan chuyen, day la loi de mac nhat."""
    dp = demand_profiles(ile, TODAY)
    wh = [p for (item, loc), p in dp.items() if loc == WH]
    assert len(wh) >= 20
    # Khong mat hang nao con kinh doanh ma bi coi la khong co nhu cau tai kho.
    # 18230 la ngoai le dung: da ngung kinh doanh tu 01/06 nen that su khong con nhu cau.
    im_lang = [p.item_no for p in wh if p.avg_daily == 0]
    assert im_lang == ["18230"], im_lang
    # mat hang nao khong ban si tai kho thi phai lay co so la tong luong xuat
    no_wholesale = [p for p in wh if p.basis == "outflow"]
    assert len(no_wholesale) >= 10


def test_cau_bi_cat_cut_duoc_loai_khoi_mau_so(ile):
    """33200 tai S0001 het hang tu 25/08 den 02/09. Nhung ngay do phai bi loai khoi mau so,
    neu khong thi nhu cau binh quan bi keo xuong va nguong bo sung tut theo."""
    dp = demand_profiles(ile, TODAY)
    p = dp[("33200", "S0001")]
    assert p.days_censored >= 5
    naive = p.total_qty / 90
    assert p.avg_daily > naive * 1.03


def test_phan_tang_rai_deu_qua_cac_nhom(ile, items):
    lines = inventory_health(ile, TODAY, items)
    counts: dict[str, int] = {}
    for l in lines:
        counts[l.tier] = counts.get(l.tier, 0) + 1
    for tier in ("Expired", "NearExpiry", "StockOutRisk", "SlowMoving", "Healthy"):
        assert counts.get(tier, 0) > 0, f"khong co dong nao o nhom {tier}: {counts}"
    assert counts["Expired"] >= 20


def test_lo_qua_han_luon_dung_dau_danh_sach(ile, items):
    lines = inventory_health(ile, TODAY, items)
    assert lines[0].tier == "Expired"
    assert lines[0].risk_score == 100
    assert "hết hạn" in lines[0].risk_reason


def test_mat_hang_khong_co_lot_van_duoc_phan_tang(ile, items):
    lines = inventory_health(ile, TODAY, items)
    untracked = [l for l in lines if l.lot_no is None]
    assert untracked, "mat hang khong co tracking bi bo qua"
    assert all(l.days_to_expiry is None for l in untracked)
    assert {l.tier for l in untracked} - {"Expired", "NearExpiry"}, "phai phan tang duoc bang tieu chi khac"
    assert not [l for l in untracked if l.tier in ("Expired", "NearExpiry")], \
        "khong co han dung thi khong duoc ket luan can han hay qua han"


def test_de_xuat_dieu_chuyen_bi_chan_boi_ton_kho_nguon(ile, items):
    sugg = replenishment(ile, TODAY, WH, items)
    assert sugg
    for s in sugg:
        assert s.constrained_qty <= s.suggested_qty
        assert s.constrained_qty <= s.source_available + 0.001
        assert s.source_location_code == WH


def test_kich_ban_cua_hang_thieu_trong_khi_kho_thua(ile, items):
    """33323 tai S0001 ton bang 0 trong khi kho con hang. Phai ra de xuat dieu chuyen,
    va so luong de xuat phai lon hon 0 chu khong bi chan ve 0."""
    sugg = [s for s in replenishment(ile, TODAY, WH, items)
            if s.item_no == "33323" and s.store_location_code == "S0001"]
    assert len(sugg) == 1
    s = sugg[0]
    assert s.quantity_on_hand == 0
    assert s.stock_out_risk is True
    assert s.constrained_qty > 0
    assert s.source_available > 100


def test_nguong_doi_thi_ket_qua_doi(ile, items):
    chat = Thresholds(stockout_days=3, excess_days=200)
    base = inventory_health(ile, TODAY, items)
    tight = inventory_health(ile, TODAY, items, chat)
    n = lambda ls, t: sum(1 for l in ls if l.tier == t)  # noqa: E731
    assert n(tight, "StockOutRisk") < n(base, "StockOutRisk")
    assert n(tight, "Excess") <= n(base, "Excess")


def test_muc_ton_muc_tieu_bi_chan_boi_han_dung(ile, items):
    """De xuat bo sung du ban 14 ngay cho mat hang han dung 3 ngay la cam ket truoc mot lan
    huy hang. 33110 Croissant - chocolate han 3 ngay, muc tieu phai tut ve 2 ngay."""
    from bc_agent.inventory import observed_shelf_life

    shelf = observed_shelf_life(ile)
    assert shelf["33110"] <= 4
    assert shelf["33323"] > 100

    sugg = {(s.item_no, s.store_location_code): s for s in replenishment(ile, TODAY, WH, items)}
    tuoi = [s for (i, _), s in sugg.items() if i == "33110"]
    assert tuoi
    for s in tuoi:
        assert s.capped_by_shelf_life is True
        assert s.target_days <= 2
        assert "hạn dùng" in s.rationale

    lau = [s for (i, _), s in sugg.items() if i == "33323"]
    for s in lau:
        assert s.capped_by_shelf_life is False
        assert s.target_days == 14
