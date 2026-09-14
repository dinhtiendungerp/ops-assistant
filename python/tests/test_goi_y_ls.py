"""UC1 tren BC that doc de xuat bo sung tu LS Replenishment, khong doc bang NWV Repl. Suggestion.

Dung chot 13/09/2026: dung module Replenishment co san cua LS. Gateway dua dong `replenJournalDetails` cua template
MAROU-TO ve hinh dang cu, nen moi skill dung `risky_suggestions` / `suggestion` giu nguyen. So luong va so ngay phu
lay nguyen tu LS; buoc bao sap het khong duoc nhan 14 ngay cua tro ly nua.
"""
from __future__ import annotations

from types import SimpleNamespace

from assistant.gateway import BCGateway
from assistant.skills import replenishment
from bc_agent.odata import apply_in_python


class LSClient:
    """Gia BCClient: ten lop khac MockBCClient nen gateway di duong live."""

    DATA = {
        "replenJournalDetails": [
            {"id": "d1", "replenishmentTemplateCode": "MAROU-TO", "itemNo": "33323", "description": "Choco nuts",
             "locationCode": "S0001", "replenishmentLocationCode": "W0003", "systemSuggestedQuantity": 82,
             "quantity": 82, "effectiveInventory": 0, "averageDailySales": 11.675, "requiredCoverageDays": 7,
             "warehouseEffectiveInventory": 685, "decision": "Based_x0020_on_x0020_Calculated_x0020_Need"},
            {"id": "d2", "replenishmentTemplateCode": "MAROU-TO", "itemNo": "10045", "description": "Cream 250 ml",
             "locationCode": "S0001", "replenishmentLocationCode": "W0003", "systemSuggestedQuantity": 0,
             "quantity": 0, "effectiveInventory": 110, "averageDailySales": 8.82143, "requiredCoverageDays": 4,
             "warehouseEffectiveInventory": 66, "decision": "_x0020_"},
        ],
        "replenItemQuantities": [
            {"itemNo": "33323", "locationCode": "S0001", "variantCode": "", "inventory": 0, "quantityInTransferIn": 0,
             "noOfDaysOutOfStock": 9, "noOfSalesDates": 56, "dailySales": 11.675, "salesDateFrom": "2026-07-24",
             "salesDateTo": "2026-09-17"},
        ],
        "replenItemParameters": [{"itemNo": "33323", "salesProfile": "DEFAULT", "storeStockCoverDays": 7, "reorderPoint": 0,
                                  "maximumInventory": 0, "transferMultiple": 0, "replenCalculationType": "Average_x0020_Usage"}],
        "replenSalesProfileLines": [{"salesProfileCode": "DEFAULT", "lineNo": 0, "startDateFormula": "-3W",
                                     "endDateFormula": "-1D", "weight": 75}],
        "replenCalcLogLines": [
            # Nguyen van tu BC ngay 14/09/2026
            {"replenishmentTemplateCode": "MAROU-TO", "itemNo": "33323", "locationCode": "S0001", "entryNo": 0,
             "messageText": "Replen. Data  - Manual Estimated Daily Sale = 0 - Store Stock Cover Reqd (Days) = 7 - Wareh Stock Cover Reqd (Days) = 21 - Replenishment Sales Profile = DEFAULT"},
            {"replenishmentTemplateCode": "MAROU-TO", "itemNo": "33323", "locationCode": "S0001", "entryNo": 1,
             "messageText": "System Suggested Quantity(82) = Daily Sales(11.675) * Store Stock Cover Reqd (Days)(7) * Forward Sales Forecast Factor(1) - Effective Inventory(0)"},
            {"replenishmentTemplateCode": "MAROU-TO", "itemNo": "33323", "locationCode": "S0001", "entryNo": 2,
             "messageText": "Checking Item=33323 Variant= Store=S0001"}],
        "replenJournalBatches": [{"replenishmentTemplateCode": "MAROU-TO", "lastRunDate": "2026-09-13"}],
        "inventoryHealthLines": [
            {"itemNo": "33323", "itemDescription": "Choco nuts", "locationCode": "W0003", "quantityOnHand": 685,
             "avgDailySalesQty": 0, "inventoryValue": 753.5},
        ],
    }

    def query(self, entity_set, conds=None, orderby=None, top=None, select=None):
        return apply_in_python([dict(r) for r in self.DATA.get(entity_set, [])], conds or [], orderby, top)


def gw() -> BCGateway:
    return BCGateway(LSClient())


def test_dong_ls_dua_ve_hinh_dang_cu():
    rows = gw().doc("replenishmentSuggestions", [], top=5000)
    assert len(rows) == 2
    r = next(x for x in rows if x["itemNo"] == "33323")
    assert r["suggestedQty"] == 82 and r["targetDays"] == 7 and r["stockOutRisk"]
    assert r["sourceLocationCode"] == "W0003" and r["demandBasis"] == "LS"
    assert r["lsDecision"] == "Based on Calculated Need" and "LS Replenishment" in r["reason"]


def test_rui_ro_la_ls_co_de_xuat_khong_phai_nguong_tro_ly():
    risky = gw().risky_suggestions(20)
    assert [(r["storeLocationCode"], r["itemNo"]) for r in risky] == [("S0001", "33323")]


def test_bao_sap_het_lay_so_luong_cua_ls():
    plan = replenishment._plan(gw(), "S0001", "33323", 0)
    assert plan["need"] == 82 and plan["target_days"] == 7 and plan["nguon"] == "LS Replenishment"


def test_mock_van_giu_cong_thuc_cu():
    from bc_agent.mock_client import MockBCClient

    plan = replenishment._plan(BCGateway(MockBCClient()), "S0001", "33323", 0)
    assert plan["target_days"] == replenishment.TARGET_DOC and plan["nguon"] == ""


def test_giai_thich_doc_so_cua_ls_va_trich_nhat_ky():
    from assistant.skills import ls_giai_thich

    kq = ls_giai_thich.giai_thich(gw(), "33323", "S0001")
    noi = " ".join(kq["y"])
    # Tu 14/09/2026 cau giai thich dich tu nhat ky LS bang knowledge chung (assistant/ls_knowledge.py).
    assert "LS đề xuất 82" in noi and "11.675/ngày" in noi and "số ngày phủ ở cửa hàng 7" in noi
    assert "DEFAULT" in noi and "Store Stock Cover Reqd (Days)" in noi
    assert kq["nhat_ky_ls"] == [ls_giai_thich_log()]


def ls_giai_thich_log() -> str:
    return next(l["messageText"] for l in LSClient.DATA["replenCalcLogLines"] if l["messageText"].startswith("System Suggested"))


def test_mock_khong_bia_giai_thich():
    from assistant.core import Assistant
    from bc_agent.mock_client import MockBCClient

    a = Assistant(MockBCClient())
    out = a.handle_message("hung.dieuphoi", "vì sao LS đề xuất Choco nuts cho Cửa hàng Quận 1")
    assert "chỉ có khi nối Business Central" in out[0].text


def test_so_chuyen_la_quantity_cuoi_cua_ls_khong_phai_muc_toi_da():
    """Stock Levels: System Suggested Quantity = Maximum Inventory 20, Quantity sau khi tru ton va chia lai = 11.
    Ngay 14/09/2026 brief ghi de xuat Ice cream x S0002 = 20 vi doc nham truong."""
    g = gw()
    d = dict(LSClient.DATA["replenJournalDetails"][0], id="d3", itemNo="33150", description="Ice cream", locationCode="S0002",
             systemSuggestedQuantity=20, quantity=11, effectiveInventory=8, warehouseEffectiveInventory=25,
             decision="Brought_x0020_to_x0020_Maximum_x0020_Inventory")
    LSClient.DATA["replenJournalDetails"].append(d)
    try:
        r = next(x for x in g.goi_y_ls() if x["itemNo"] == "33150")
        assert r["suggestedQty"] == 11 and r["constrainedQty"] == 11 and r["targetQty"] == 20 and r["stockOutRisk"]
        assert "đề xuất chuyển 11" in r["reason"]
    finally:
        LSClient.DATA["replenJournalDetails"].remove(d)
