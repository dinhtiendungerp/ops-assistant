"""UC1 do chinh xac du bao, UC3 scorecard nha cung cap, UC2 truy xuat lo, va lien ket sang BC. Lam ngay 14/09/2026.

So tinh bang AL tren BC (codeunit 70120, 70121). Ban Python o bc_agent/forecast.py va bc_agent/supplier.py chep dung
cong thuc; da doi chieu tren BC that: 148 dong du bao va 6 dong scorecard, khong truong nao lech. Test o day kiem cong
thuc tren du lieu nho tu dung, va kiem tro ly doc dung bang ket qua.
"""
from __future__ import annotations

from datetime import date, timedelta

import pytest

from assistant.bc_link import link
from assistant.core import Assistant
from assistant.nlu import RuleNLU
from bc_agent.forecast import ForecastThresholds, backtest_bc, wape_gop
from bc_agent.mock_client import MockBCClient
from bc_agent.supplier import scorecard

NEO = date(2026, 9, 18)


# ---------------------------------------------------------------- UC1 cong thuc
def _ile_ban_deu(so_ngay: int, ban: float, het_tu: date | None = None) -> list[dict]:
    """Nhap 10.000 truoc cua so, ban deu moi ngay; tu het_tu tro di ton ve 0 va khong ban (cau bi cat cut)."""
    dau = NEO - timedelta(days=so_ngay)
    rows = [{"posting_date": dau - timedelta(days=1), "entry_type": "Positive Adjmt.", "item_no": "A", "location_code": "S1",
             "quantity": 10000}]
    ton = 10000.0
    for i in range(so_ngay + 1):
        d = dau + timedelta(days=i)
        if het_tu and d >= het_tu:
            continue
        rows.append({"posting_date": d, "entry_type": "Sale", "item_no": "A", "location_code": "S1", "quantity": -ban})
        ton -= ban
        if het_tu and d == het_tu - timedelta(days=1):       # cuoi ngay truoc do huy het phan con lai
            rows.append({"posting_date": d, "entry_type": "Negative Adjmt.", "item_no": "A", "location_code": "S1", "quantity": -ton})
            ton = 0
    return rows


def test_ban_deu_thi_du_bao_dung():
    acc, daily = backtest_bc(_ile_ban_deu(150, 5), NEO)
    ma = next(r for r in acc if r["method"] == "MA28")
    assert ma["dailyLevel"] == 5 and ma["wapePct"] == 0 and ma["daysEvaluated"] == 28 and not ma["isException"]
    assert len([d for d in daily if d["method"] == "MA28"]) == 28


def test_ngay_het_hang_bi_bo_khoi_sai_so():
    # Het hang 5 ngay cuoi: khong duoc tinh la du bao sai 5 x 5 = 25 don vi.
    acc, _ = backtest_bc(_ile_ban_deu(150, 5, het_tu=NEO - timedelta(days=4)), NEO)
    ma = next(r for r in acc if r["method"] == "MA28")
    assert ma["daysCensored"] == 5 and ma["daysEvaluated"] == 23 and ma["wapePct"] == 0


def test_kho_trung_tam_khong_do():
    rows = [dict(r, location_code="W0003") for r in _ile_ban_deu(150, 5)]
    assert backtest_bc(rows, NEO, ForecastThresholds(central_warehouse="W0003"))[0] == []


def test_ngoai_le_khi_ban_giam_manh():
    rows = _ile_ban_deu(150, 10)
    for r in rows:                                   # 28 ngay cuoi chi ban 3
        if r["entry_type"] == "Sale" and r["posting_date"] > NEO - timedelta(days=28):
            r["quantity"] = -3
    ma = next(r for r in backtest_bc(rows, NEO)[0] if r["method"] == "MA28")
    assert ma["isException"] and "cao hơn bán thực tế" in ma["exceptionReason"] and ma["biasPct"] > 200


def test_exception_theo_ngay_da_khai_bi_bo():
    rows = _ile_ban_deu(150, 5)
    exc = [{"itemNo": "", "locationCode": "S1", "fromDate": (NEO - timedelta(days=2)).isoformat(), "toDate": NEO.isoformat()}]
    ma = next(r for r in backtest_bc(rows, NEO, exceptions=exc)[0] if r["method"] == "MA28")
    assert ma["daysExcluded"] == 3


# ---------------------------------------------------------------- UC3 cong thuc
def _po(doc, qty, exp, order, rec=0.0, vendor="V1", item="I1"):
    return {"documentNo": doc, "lineNo": 10000, "buyFromVendorNo": vendor, "itemNo": item, "quantity": qty,
            "quantityReceived": rec, "outstandingQuantity": qty - rec, "expectedReceiptDate": exp, "orderDate": order,
            "directUnitCost": 2}


def _rc(doc, qty, ngay):
    return {"orderNo": doc, "orderLineNo": 10000, "quantity": qty, "postingDate": ngay}


def test_scorecard_dung_han_tre_giao_hai_lan_va_qua_han():
    po = [_po("D1", 10, "2026-09-01", "2026-08-29", 10),          # dung han
          _po("D2", 10, "2026-09-02", "2026-08-30", 10),          # giao hai lan, xong tre 3 ngay
          _po("D3", 10, "2026-09-10", "2026-09-07", 0),           # qua han 8 ngay chua nhan
          _po("D4", 10, "2024-01-01", "2023-12-20", 0, vendor="CRONUS")]   # don treo ngoai ky
    rc = [_rc("D1", 10, "2026-09-01"), _rc("D2", 6, "2026-09-02"), _rc("D2", 4, "2026-09-05")]
    r = next(x for x in scorecard(po, rc, NEO, categories={"I1": "CAT"}) if x["itemCategoryCode"] == "")
    assert (r["linesDue"], r["linesCompleted"], r["linesOnTime"]) == (3, 2, 1)
    assert r["onTimePct"] == 33.3 and r["firstDeliveryCompletePct"] == 50.0
    assert r["avgDelayDays"] == 5.5                               # (3 + 8) / 2
    assert r["overdueLines"] == 1 and r["overdueAmount"] == 20 and r["needsAttention"]
    assert not [x for x in scorecard(po, rc, NEO) if x["vendorNo"] == "CRONUS"]


# ---------------------------------------------------------------- tro ly
@pytest.fixture()
def asst():
    return Assistant(MockBCClient())


@pytest.mark.parametrize("cau,intent", [
    ("độ chính xác dự báo thế nào", "FORECAST"), ("dự báo choco pillar ở S0001 sai bao nhiêu", "FORECAST"),
    ("nhà cung cấp nào hay giao trễ", "SUPPLIER"), ("truy xuất lô L260908-33170B", "TRACE"),
    ("lô L260908-33170B đi đâu rồi", "TRACE"), ("PO nào quá hạn chưa nhận?", "PO_OVERDUE"),
])
def test_rule_nhan_ra(cau, intent):
    assert RuleNLU().parse(cau).intent == intent


def test_du_bao_doc_dung_bang_ket_qua(asst):
    rows = asst.gw.doc("forecastAccuracies", [], top=5000)
    out = asst.handle_message("trang.sc", "độ chính xác dự báo thế nào")
    assert out[0].skill == "du_bao"
    wape = f"{wape_gop(rows, 'MA28'):.1f}".replace(".", ",")
    assert wape in out[0].text and "chưa phải AI" in out[0].card.body


def test_du_bao_mot_mat_hang_co_theo_tuan(asst):
    out = asst.handle_message("trang.sc", "dự báo choco pillar ở S0001 sai bao nhiêu")
    assert out[0].card.title == "Dự báo Choco pillar tại S0001" and "Theo tuần" in out[0].card.body


def test_quan_ly_cua_hang_chi_thay_cua_hang_minh(asst):
    out = asst.handle_message("lan.s0001", "độ chính xác dự báo thế nào")
    assert "tại S0001" in out[0].text


def test_scorecard_nha_cung_cap(asst):
    out = asst.handle_message("trang.sc", "nhà cung cấp nào hay giao trễ")
    assert out[0].skill == "nha_cung_cap" and "AL-s Foods" in out[0].text
    the = [d.card for d in out if d.card]
    al = next(c for c in the if "44020" in c.title)
    assert dict(al.facts)["Đúng hạn"].startswith("48,7%") and [a.id for a in al.actions] == ["po_qua_han"]
    lai = asst.handle_action("trang.sc", "po_qua_han", al.ref, {})
    assert lai[0].skill == "po_qua_han"


def test_truy_xuat_lo_bi_khoa(asst):
    out = asst.handle_message("hung.dieuphoi", "truy xuất lô L260908-33170B")
    assert out[0].skill == "truy_xuat"
    body = out[0].card.body
    assert "S0001" in body and "Nếu phải thu hồi" in body


def test_mcp_tool_moi(asst):
    from assistant import mcp_server

    user = asst.mem.user("trang.sc")
    for ten, args in (("forecast_accuracy", {}), ("supplier_scorecard", {"vendor_no": "44020"}),
                      ("trace_lot", {"lot_no": "L260908-33170B"})):
        kq = mcp_server.goi_tool(asst, user, ten, args)
        assert not kq.get("isError"), (ten, kq)


def test_lien_ket_bc_dung_dang_url():
    from bc_agent.config import Settings

    from dataclasses import replace
    s = replace(Settings(), bc_tenant_id="t1", bc_environment="NWV01", bc_company_name="NWV")
    url = link("item_ledger_entries", {"Item No.": "33100", "Lot No.": "L1"}, settings=s)
    assert url.startswith("https://businesscentral.dynamics.com/t1/NWV01/?company=NWV&page=38&filter=")
    assert "'Item%20No.'%20IS%20'33100'%20AND%20'Lot%20No.'%20IS%20'L1'" in url
    assert link("item_ledger_entries", settings=replace(s, bc_tenant_id="")) == ""


def test_ten_mat_hang_khop_nguyen_cum_thang_ten_dai_hon(asst):
    # "Ice cream" la ten dung cua 33150; truoc day so mo chon "Ice cream blueberry" (18200) vi ca hai 100 diem.
    assert asst.gw.find_item("vì sao LS đề xuất Ice cream cho S0002")["itemNo"] == "33150"
    assert asst.gw.find_item("Ice cream blueberry")["itemNo"] == "18200"
    assert asst.gw.find_item("croissant chocolate")["itemNo"] == "33110"


@pytest.mark.parametrize("cau,ma", [("chuyển 82 hộp Choco nuts xuống Quận 1", "S0001"), ("hàng ở Hà Nội", "S0002"),
                                    ("S0005 thiếu", "S0005"), ("quán Đà Nẵng", "S0010"), ("Quận 10", ""),
                                    ("Cửa hàng trực tuyến", "S0013")])
def test_nhan_ten_cua_hang_ngan(asst, cau, ma):
    assert asst._tim_cua_hang(cau) == ma


def _ile_theo_thu(so_ngay: int) -> list[dict]:
    """Ban cuoi tuan gap doi ngay thuong: MA28 phang se sai, Holt-Winters mua vu tuan phai bat duoc."""
    dau = NEO - timedelta(days=so_ngay)
    rows = [{"posting_date": dau - timedelta(days=1), "entry_type": "Positive Adjmt.", "item_no": "A", "location_code": "S1",
             "quantity": 100000}]
    for i in range(so_ngay + 1):
        d = dau + timedelta(days=i)
        rows.append({"posting_date": d, "entry_type": "Sale", "item_no": "A", "location_code": "S1",
                     "quantity": -(10 if d.weekday() >= 5 else 5)})
    return rows


def test_holt_winters_bat_mua_vu_tuan_va_ghi_du_bao_ngay_toi():
    toi: list[dict] = []
    acc, _ = backtest_bc(_ile_theo_thu(200), NEO, ForecastThresholds(horizon_days=14), forward=toi)
    theo = {r["method"]: r for r in acc}
    assert theo["HW"]["wapePct"] < 5 < theo["MA28"]["wapePct"]
    assert theo["HW"]["modelParameters"].startswith("alpha ")
    assert len(toi) == 14 and toi[0]["date"] == (NEO + timedelta(days=1)).isoformat()
    cuoi_tuan = [r["forecastQuantity"] for r in toi if date.fromisoformat(r["date"]).weekday() >= 5]
    thuong = [r["forecastQuantity"] for r in toi if date.fromisoformat(r["date"]).weekday() < 5]
    assert min(cuoi_tuan) > max(thuong)
    assert all(r["forecastQuantityLower"] <= r["forecastQuantity"] <= r["forecastQuantityUpper"] for r in toi)


def test_ngay_co_planned_sales_demand_cua_ls_bi_bo():
    rows = _ile_ban_deu(150, 5)
    ngay = [(NEO - timedelta(days=k)).isoformat() for k in range(3)]
    planned = [{"itemNo": "A", "variantCode": "", "locationCode": "S1", "date": d, "status": "Enabled",
                "plannedDemandType": "Additional_x0020__x0025__x0020_Factor_x0020__x0028_to_x0020_Forecast_x0029_"} for d in ngay]
    planned.append({"itemNo": "A", "variantCode": "", "locationCode": "S1", "date": (NEO - timedelta(days=5)).isoformat(),
                    "status": "Disabled", "plannedDemandType": "Additional_x0020_Quantity_x0020__x0028_to_x0020_Forecast_x0029_"})
    ma = next(r for r in backtest_bc(rows, NEO, planned=planned)[0] if r["method"] == "MA28")
    assert ma["daysExcluded"] == 3                    # dong Disabled khong tinh
