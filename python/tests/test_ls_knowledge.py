"""Knowledge doc nhat ky LS Replenishment phai dung cho moi nhanh tinh, khong chi du lieu mau.

Dung yeu cau ngay 14/09/2026. Test khong chep lai cau log bang tay cho tung nhanh: no lay CHINH van ban Label trong
mau_log.json (sinh tu source LS), dien gia tri gia vao nhu StrSubstNo cua LS, roi kiem bo doc tra lai dung gia tri.
Nhu vay nhanh nao LS co ghi log (Stock Levels, lead time, cross dock, kho khong du hang...) cung duoc kiem, ke ca nhanh
du lieu demo chua bao gio chay toi.
"""
from __future__ import annotations

import re

import pytest

from assistant import ls_knowledge as kt


def _strsubstno(van_ban: str, gia_tri: dict[str, str]) -> str:
    return re.sub(r"%(\d)", lambda m: gia_tri.get(m.group(1), ""), van_ban)


def _mau(id_: str) -> kt.Mau:
    return next(m for m in kt.tai()["mau"] if m.id == id_)


def _gia(i: int, van_ban: str) -> str:
    # Xen ke so, so am, caption co ngoac, de lo loi tach nhom.
    mau = ["12.5", "-4", "Store Stock Cover Reqd (Days)", "37", "Brought up to Reorder Point", "09/19/26", "1,000", "S0001", "0"]
    return mau[(i + len(van_ban)) % len(mau)]


def test_moi_label_doc_lai_dung_cau_goc():
    """Moi Label: dien gia tri, doc lai, dien nguoc gia tri doc duoc vao Label da khop phai ra dung chuoi cu."""
    sai = []
    for m in kt.tai()["mau"]:
        if m.do_dac_trung < 4:
            continue
        gia_tri = {n: _gia(int(n), m.van_ban) for n in set(re.findall(r"%(\d)", m.van_ban))}
        dong = _strsubstno(m.van_ban, gia_tri).strip()
        b = kt.doc_dong(dong)
        if b.loai != "mau":
            sai.append((m.id, dong, "khong nhan dang"))
            continue
        khop = _mau(b.id)
        dung_lai = _strsubstno(khop.van_ban, b.gia_tri).strip()
        if b.phan_them:
            dung_lai = None          # cau ghep: chi can nhan dang duoc
        if dung_lai is not None and re.sub(r"\s+", " ", dung_lai) != re.sub(r"\s+", " ", dong):
            sai.append((m.id, dong, dung_lai))
    assert not sai, sai[:5]


def test_dien_giai_tro_dung_label_va_dung_tham_so():
    ids = {m.id: m for m in kt.tai()["mau"]}
    for id_, d in kt.tai()["dien_giai"].items():
        assert id_ in ids, f"{id_} khong co trong mau_log.json, sinh lai hoac sua id"
        co = set(re.findall(r"%(\d)", ids[id_].van_ban))
        dung = set(re.findall(r"\{(\d)", d.get("noi", "")))
        assert dung <= co, f"{id_} dung {dung - co} ma Label khong co"
        assert d.get("buoc") in kt.tai()["ten_buoc"], id_
        for t in d.get("tham_so") or []:
            assert t in kt.tai()["tham_so"], f"{id_}: tham so {t} chua co trong tham_so.yaml"


@pytest.mark.parametrize("id_, gia_tri, can_co", [
    # Stock Levels: dua ve Maximum Inventory
    ("CALC:DecisionQtyMaxInvTxt", {"1": "Brought to Maximum Inventory", "2": "30", "3": "50", "4": "Effective Inventory", "5": "20"},
     ["30", "Maximum Inventory 50", "tồn khả dụng 20"]),
    # Nang len Reorder Point
    ("CALC:DecisionQtyReorderPointTxt", {"1": "Brought up to Reorder Point", "2": "8", "3": "10", "4": "Projected Eff. Inventory", "5": "2"},
     ["Nâng số lượng lên 8", "Reorder Point 10", "tồn dự kiến khi hàng về 2"]),
    # Lam tron roi cong them mot boi so
    ("CALC:Text224", {"1": "12", "2": "3", "3": "20", "4": "12", "5": "24"}, ["cộng thêm một bội số 12", "24"]),
    # Kho chuyen hang khong du
    ("CALC:Text203", {"1": "40", "2": "65"}, ["chỉ còn 40", "65", "AD203"]),
    # Kho het hang
    ("CALC:Text201", {"1": "0"}, ["A201"]),
    # Nhu cau da len ke hoach trong cua so phu
    ("CALC:PlannedSalesDemandCoverFoundTxt", {"1": "Replen. Planned Sales Dem.", "2": "09/19/26", "3": "09/25/26"}, ["nhu cầu từng ngày theo kế hoạch"]),
    # He so du bao bi chan tran
    ("CALC:ForwardFactorReplacedText", {"1": "1.8", "2": "1.5"}, ["1.8", "1.5"]),
    # Loai khoi bo sung
    ("CALC:Text104", {"1": "S0020", "2": "S0001|S0002"}, ["S0020", "bỏ qua"]),
])
def test_nhanh_du_lieu_demo_chua_chay_toi(id_, gia_tri, can_co):
    dong = _strsubstno(_mau(id_).van_ban, gia_tri)
    b = kt.doc_dong(dong)
    assert b.id == id_, (dong, b.id)
    for c in can_co:
        assert c in b.noi, (c, b.noi)


def test_cau_ghep_hai_label_va_the_dau_dong():
    dong = ("Adjust Item quantity from 62 to 37. Warehouse Effective Inventory(25) is less than Quantity(62) "
            "then Quantity(62) - Warehouse Effective Inventory(25) = Quantity(37) [AD202]")
    b = kt.doc_dong(dong)
    assert b.id == "CALC:Text009" and b.phan_them[0].id == "CALC:Text202"
    assert "chỉ mua phần thiếu 37" in b.phan_them[0].noi

    b = kt.doc_dong("[Cross Dock] Quantity to Cross Dock less than zero :Old value=-3 New Value=0")
    assert b.the == ["Cross Dock"] and b.id == "CALC:Text016"

    b = kt.doc_dong("Store Effective Inventory = 11 - Warehouse Effective Inventory = 137. "
                    "(Quantity on Purchase Order is not considered due to Replen. Setup)")
    assert b.id == "CALC:StoreWhseEffInvTxt" and "hàng mua đang về" in b.phan_them[0].noi


def test_dong_tham_so_tach_dung_ca_gia_tri_rong():
    b = kt.doc_dong("Replen. Data  - Store Forward Sales Profile =  - Wareh. Forward Sales Profile =  - Replenish as Location Code =  "
                    "- Replenish as Item No. =  - Replenish as Item No - Method = Total")
    assert b.loai == "tham_so"
    assert dict(b.cap) == {"Store Forward Sales Profile": "", "Wareh. Forward Sales Profile": "", "Replenish as Location Code": "",
                           "Replenish as Item No.": "", "Replenish as Item No - Method": "Total"}


def test_caption_co_ngoac_khong_bi_cat():
    b = kt.doc_dong("System Suggested Quantity(-50) = Daily Sales(14.86428) * Store Stock Cover Reqd (Days)(7) * "
                    "Forward Sales Forecast Factor(1) - Effective Inventory(154)")
    assert b.id == "CALC:Text015"
    assert b.gia_tri["3"] == "Store Stock Cover Reqd (Days)" and b.gia_tri["4"] == "7" and b.gia_tri["7"] == "154"


def test_dong_la_hien_nguyen_van():
    kq = kt.doc_nhat_ky(["Mot dong LS ban moi chua co trong source da doc"])
    assert kq["chua_nhan_dang"] == ["Mot dong LS ban moi chua co trong source da doc"] and kq["ty_le_nhan_dang"] == 0.0


def test_nhanh_stock_levels_tren_bc_that():
    # Nguyen van log LS ngay 14/09/2026 sau khi dat 33150 va 30091 sang Stock Levels (tools/ls_replen_setup.py STOCK_LEVELS).
    b = kt.doc_dong("Decision = Brought to Maximum Inventory. System Suggested Quantity(20) - Store Effective Inventory(8) = Quantity(12).")
    assert b.id == "CALC:DecisionSSQStoreEffInvQtyTxt"
    assert b.noi.startswith("Quyết định: Brought to Maximum Inventory.") and "12 = số hệ thống đề xuất 20" in b.noi

    b = kt.doc_dong("Decision =  . System Suggested Quantity(0) - Store Effective Inventory(4) = Quantity(-4).")
    assert not b.noi.startswith("Quyết định"), b.noi          # Decision rong thi khong in "Quyết định: ."

    kq = kt.doc_nhat_ky(["If Effective Inventory(4) > Reorder Point(3) THEN System Suggested Quantity(0)",
                         "Adjust Record quantity from 12 to 11"])
    assert kq["ty_le_nhan_dang"] == 1.0
