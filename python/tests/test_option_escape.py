"""Ten Option tren API tra ve dang ma hoa, phai giai ma truoc khi so sanh.

Ly do co file nay: `Negative Adjmt.` tren API la `Negative_x0020_Adjmt_x002E_`. Lop tinh toan
so `entry_type` voi chuoi `"Negative Adjmt."`, khong khop thi bo het dong xuat kho khoi phep
tinh nhu cau. Ket qua ngay 12/09/2026 khi doi chieu tren BC that: rui ro dut hang 42 thay vi
58, cham luan chuyen 13 thay vi 4. Du lieu dung, phep so sanh sai.
"""
from __future__ import annotations

import pytest

from bc_agent.bc_data import ILE_API, OPTION_FIELDS, _project, norm_date, unescape_option
from bc_agent.inventory import OUTBOUND_TYPES, _d, observed_shelf_life


@pytest.mark.parametrize("raw,mong_doi", [
    ("Negative_x0020_Adjmt_x002E_", "Negative Adjmt."),
    ("Positive_x0020_Adjmt_x002E_", "Positive Adjmt."),
    ("Sale", "Sale"),
    ("Purchase", "Purchase"),
    ("Transfer", "Transfer"),
    ("_x0020_", ""),          # option rong
    ("", ""),
    (None, None),
])
def test_giai_ma_ten_option(raw, mong_doi):
    assert unescape_option(raw) == mong_doi


def test_ten_da_giai_ma_khop_voi_bang_loai_xuat():
    """Day moi la dieu quan trong: sau khi giai ma thi phep so sanh trong inventory.py dung."""
    for raw in ("Sale", "Negative_x0020_Adjmt_x002E_", "Transfer"):
        assert unescape_option(raw) in OUTBOUND_TYPES
    assert unescape_option("Positive_x0020_Adjmt_x002E_") not in OUTBOUND_TYPES


def test_project_giai_ma_truong_option_va_giu_nguyen_truong_khac():
    rows = [{
        "entryNo": 1, "postingDate": "2026-09-18", "entryType": "Negative_x0020_Adjmt_x002E_",
        "documentType": "_x0020_", "itemNo": "33170", "locationCode": "W0003",
        "quantity": -13, "lotNo": "L260910-33170B", "expirationDate": "2026-09-15",
    }]
    out = _project(rows, ILE_API)[0]
    assert out["entry_type"] == "Negative Adjmt."
    assert out["document_type"] == ""
    # ma lo va ma hang khong bi ham giai ma cham vao
    assert out["lot_no"] == "L260910-33170B"
    assert out["item_no"] == "33170"
    assert out["quantity"] == -13


def test_chi_giai_ma_truong_da_khai_la_option():
    """Ma lo hay ma hang chua chuoi trong giong ma hoa thi phai de nguyen."""
    assert "lot_no" not in OPTION_FIELDS
    rows = [{"entryType": "Sale", "lotNo": "L_x0020_123"}]
    out = _project(rows, {"entry_type": "entryType", "lot_no": "lotNo"})[0]
    assert out["lot_no"] == "L_x0020_123"


# ---------------------------------------------------------------- ngay 0D cua BC
@pytest.mark.parametrize("raw,mong_doi", [
    ("0001-01-01", None),
    ("0001-01-01T00:00:00Z", None),
    ("2026-09-18", "2026-09-18"),
    ("", ""),
    (None, None),
])
def test_ngay_0d_khong_phai_mot_ngay(raw, mong_doi):
    assert norm_date(raw) == mong_doi


def test_project_chuan_hoa_ngay_0d():
    rows = [{"entryType": "Sale", "postingDate": "2026-09-18", "expirationDate": "0001-01-01"}]
    out = _project(rows, ILE_API)[0]
    assert out["expiration_date"] is None
    assert out["posting_date"] == "2026-09-18"


def test_doc_ngay_0d_tra_ve_none():
    from datetime import date
    assert _d("0001-01-01") is None
    assert _d(date(1, 1, 1)) is None
    assert _d("2026-09-18") == date(2026, 9, 18)


def test_han_dung_khong_tinh_tren_ngay_0d():
    """Loi da bat duoc: de ngay 0D lot qua thi han dung ra -739.787 ngay, va muc ton muc tieu
    bi chan xuong 1 ngay cho moi mat hang khong co han dung."""
    rows = [
        {"item_no": "33170", "posting_date": "2026-09-14", "expiration_date": "2026-09-18", "quantity": 10},
        {"item_no": "33200", "posting_date": "2026-09-14", "expiration_date": "0001-01-01", "quantity": 10},
    ]
    sl = observed_shelf_life(rows)
    assert sl["33170"] == 4
    assert "33200" not in sl


def test_chan_theo_han_dung_bo_qua_ngay_0d():
    """Hai dieu kien cung mot luc: ngay 0D khong duoc tinh thanh han dung, va dieu kien chan
    phai trung voi NWV Replenishment Calc (`ShelfDays > 0`). Truoc khi sua, dong Purchase mang
    ngay 0D duoi day lam han dung ra -739.787 ngay va muc ton muc tieu bi chan xuong 1 ngay."""
    from datetime import date, timedelta

    from bc_agent.inventory import Thresholds, replenishment

    ile = [
        {"posting_date": date(2026, 6, 22), "entry_type": "Purchase", "item_no": "33200",
         "location_code": "W0003", "lot_no": None, "expiration_date": "0001-01-01", "quantity": 500},
        {"posting_date": date(2026, 6, 22), "entry_type": "Negative Adjmt.", "item_no": "33200",
         "location_code": "W0003", "lot_no": None, "expiration_date": "0001-01-01", "quantity": -100},
        {"posting_date": date(2026, 6, 22), "entry_type": "Positive Adjmt.", "item_no": "33200",
         "location_code": "S0001", "lot_no": None, "expiration_date": "0001-01-01", "quantity": 100},
    ] + [
        {"posting_date": date(2026, 9, 1) + timedelta(days=i), "entry_type": "Sale",
         "item_no": "33200", "location_code": "S0001", "lot_no": None,
         "expiration_date": "0001-01-01", "quantity": -5}
        for i in range(19)
    ]
    sugg = replenishment(ile, date(2026, 9, 18), "W0003",
                         {"33200": {"description": "Chocolate ice cream", "unit_cost": 4.2}},
                         Thresholds())
    assert sugg, "cap S0001 x 33200 chi con 5 cai, phai ra de xuat"
    s = sugg[0]
    assert not s.capped_by_shelf_life
    assert s.target_days == 14
    assert "hạn dùng" not in s.rationale


# ---------------------------------------------------------------- BC_MODE
@pytest.mark.parametrize("raw,live", [
    ("mock", False), ("", False), ("live", True), ("api", True), ("API", True), (" Live ", True),
])
def test_bc_mode_nhan_ca_live_va_api(raw, live):
    """`.env` va brief tung ghi BC_MODE=api, con code chi so voi "live", nen tro ly am tham
    chay tren fixtures trong khi man hinh bao dang chay that."""
    from dataclasses import replace

    from bc_agent import config
    assert replace(config.settings, bc_mode=raw).bc_live is live


def test_bc_mode_la_nao_khac_thi_bao_ngay():
    from dataclasses import replace

    from bc_agent import config
    with pytest.raises(SystemExit, match="BC_MODE"):
        _ = replace(config.settings, bc_mode="thuc").bc_live
