"""CTKM cua LS: tra cuu dang chay, sap toi, da ket thuc, va cap mat hang x cua hang LS Replenishment chua cong nhu cau.

Fixtures sinh tu tools/ls_replen_setup.chuong_trinh_km (cung cau hinh da ap len NWV01), ngay neo mock 18/09/2026.
"""
from __future__ import annotations

from datetime import date

import pytest

from assistant.core import Assistant
from assistant.mcp_server import goi_tool
from assistant.nlu import RuleNLU
from assistant.skills import khuyen_mai as km
from bc_agent.mock_client import MockBCClient

NEO = date(2026, 9, 18)


@pytest.fixture()
def asst():
    return Assistant(MockBCClient())


@pytest.mark.parametrize("cau", ["CTKM nào sắp tới", "hiện có khuyến mãi gì không", "Choco bowl có khuyến mãi không",
                                 "tổng hợp CTKM tháng này", "giảm giá croissant sau 19h", "có ưu đãi nào đang chạy ở Hà Nội"])
def test_rule_nhan_ra_hoi_khuyen_mai(cau):
    assert RuleNLU().parse(cau).intent == "PROMO"


@pytest.mark.parametrize("cau,intent", [("vì sao LS đề xuất Choco bowl cho S0010", "REPLEN_WHY"),
                                        ("dự báo có tính khuyến mãi không", "FORECAST")])
def test_cau_vi_sao_va_du_bao_khong_bi_bat_nham(cau, intent):
    assert RuleNLU().parse(cau).intent == intent


def test_ten_mat_hang_con_lai_sau_khi_bo_tu_khuyen_mai():
    assert RuleNLU().parse("Choco bowl có khuyến mãi không").item_text == "Choco bowl"


def test_dang_chay_va_sap_toi_kem_cap_chua_co_nhu_cau(asst):
    out = asst.handle_message("hung.dieuphoi", "CTKM nào đang chạy và sắp tới")
    d = out[0]
    assert d.skill == "khuyen_mai"
    body = d.card.body
    assert "MR2609-CR" in body and "19:00-22:00" in body
    assert "MR2609-CB" in body and "MR2609-CP" in body
    assert "MR2607-CP" not in body                                  # da ket thuc, khong hoi thi khong liet ke
    dong_cb = next(l for l in body.splitlines() if "chưa cộng nhu cầu khuyến mãi cho Choco bowl" in l)
    assert dong_cb.split("cho Choco bowl tại ")[1].split(", dù")[0] == "S0002, S0005"   # S0001, S0010 da co Planned Event
    assert "KM-CHOCOPILLAR-09" in body                              # Choco pillar du ca S0001 va S0002


def test_loc_theo_mat_hang_lay_moi_mon_trung_ten(asst):
    out = asst.handle_message("hung.dieuphoi", "croissant có giảm giá không")
    body = out[0].card.body
    assert "MR2609-CR" in body and "MR2609-CB" not in body
    assert "Croissant - plain" in body and "Croissant - chocolate" in body


def test_quan_ly_cua_hang_thay_ctkm_cua_nhom_gia_cua_minh(asst):
    out = asst.handle_message("minh.s0002", "CTKM nào sắp tới")
    body = out[0].card.body
    assert "MR2609-CP" in body and "MR2609-CB" in body              # S0002 co ca ALL va FOOD
    out = asst.handle_message("ha.s0010", "CTKM nào sắp tới")
    body = out[0].card.body
    assert "MR2609-CB" in body and "MR2609-CP" not in body          # S0010 khong thuoc nhom gia FOOD


def test_hoi_ctkm_da_ket_thuc(asst):
    out = asst.handle_message("hung.dieuphoi", "CTKM đã kết thúc")
    assert "MR2607-CP" in out[0].card.body and "MR2609-CB" not in out[0].card.body


def test_trang_thai_chuong_trinh():
    o = {"status": "Enabled", "startingDate": "2026-09-23", "endingDate": "2026-09-25"}
    assert km.trang_thai(o, NEO) == "sap_toi"
    assert km.trang_thai({**o, "status": "Disabled"}, NEO) == "chua_bat"          # quen bat: POS se khong ap
    assert km.trang_thai({**o, "status": "Disabled", "startingDate": "2022-01-01", "endingDate": "2028-12-31"}, NEO) == "da_tat"
    assert km.trang_thai({**o, "startingDate": "2026-09-01", "endingDate": "2026-09-30"}, NEO) == "dang_chay"
    assert km.trang_thai({**o, "startingDate": "2026-07-06", "endingDate": "2026-07-19"}, NEO) == "da_ket_thuc"
    assert km.trang_thai({**o, "startingDate": "0001-01-01", "endingDate": "0001-01-01"}, NEO) == "dang_chay"


def _du_lieu(**kw):
    base = {
        "hom_nay": NEO, "cua_hang": ["S0001", "S0002"], "ky": {}, "su_kien": {}, "nhu_cau": [],
        "nhom_gia": [{"store": "S0001", "priceGroupCode": "ALL"}, {"store": "S0002", "priceGroupCode": "ALL"},
                     {"store": "S0001", "priceGroupCode": "FOOD"}],
        "hang": {"A": {"itemNo": "A", "description": "Món A", "itemCategoryCode": "KEM"},
                 "B": {"itemNo": "B", "description": "Món B", "itemCategoryCode": "KEM"},
                 "C": {"itemNo": "C", "description": "Món C", "itemCategoryCode": "BANH"}},
        "ban": {("A", "S0001"), ("B", "S0001"), ("B", "S0002"), ("C", "S0002")},
        "ctkm": [{"no": "X", "description": "KM kem", "status": "Enabled", "type": "Disc. Offer", "priceGroup": "",
                  "startingDate": "2026-09-20", "endingDate": "2026-09-21"}],
        "dong": [{"offerNo": "X", "type": "Item_x0020_Category", "no": "KEM", "dealPriceDiscPct": 10, "exclude": False},
                 {"offerNo": "X", "type": "Item", "no": "A", "exclude": True}],
    }
    base.update(kw)
    return base


def test_nhom_hang_tru_dong_exclude_va_nhom_gia_rong_la_moi_cua_hang():
    c = km.tong_hop(_du_lieu())[0]
    assert [h["no"] for h in c["hang"]] == ["B"]                    # KEM gom A, B; A bi Exclude
    assert c["cua_hang"] == ["S0001", "S0002"]
    assert c["dang_ban"] == [("B", "S0001"), ("B", "S0002")] and c["thieu"] == [("B", "S0001"), ("B", "S0002")]


def test_nhom_gia_va_dong_nhu_cau_trong_thoi_gian_ctkm():
    du = _du_lieu(nhu_cau=[{"itemNo": "B", "locationCode": "S0001", "date": "2026-09-20", "status": "Enabled",
                            "variantCode": "", "plannedDemandEvent": "EV1"},
                           {"itemNo": "B", "locationCode": "S0002", "date": "2026-09-25", "status": "Enabled",
                            "variantCode": "", "plannedDemandEvent": "EV2"}])       # ngoai thoi gian CTKM, khong tinh
    c = km.tong_hop(du)[0]
    assert c["co_nhu_cau"] == {("B", "S0001"): {"EV1"}} and c["thieu"] == [("B", "S0002")]
    du["ctkm"][0]["priceGroup"] = "FOOD"
    c = km.tong_hop(du)[0]
    assert c["cua_hang"] == ["S0001"] and c["thieu"] == []


def test_ctkm_chay_tu_lau_khong_bao_thieu_nhu_cau():
    du = _du_lieu()
    du["ctkm"][0].update(startingDate="2022-01-01", endingDate="2028-12-31")
    c = km.tong_hop(du)[0]
    assert c["trang_thai"] == "dang_chay" and not c["moi"] and c["thieu"] == []


def test_mcp_tool_promotions(asst):
    kq = goi_tool(asst, {"user_id": "hung.dieuphoi", "role": "dispatcher"}, "promotions", {"status": "sap_toi"})
    ds = {c["no"]: c for c in kq["structuredContent"]["ctkm"]}
    assert set(ds) == {"MR2609-CB", "MR2609-CP"}
    assert {x["location"] for x in ds["MR2609-CB"]["chua_co_nhu_cau_ls"]} == {"S0002", "S0005"}
    assert ds["MR2609-CP"]["chua_co_nhu_cau_ls"] == []


def test_brief_dieu_phoi_nhac_ctkm_sap_toi(asst):
    out = km.tom_tat_cho_brief(asst, {"user_id": "hung.dieuphoi", "role": "dispatcher"})
    assert out and "Choco bowl -15% 23-25/09" in out[0].text and "MR2609-CB" in out[0].text
