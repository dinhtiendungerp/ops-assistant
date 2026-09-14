"""Test cho duong custom API page: dung entity set, dung URL, dung khoa chuan.

Khong goi mang. TokenProvider va requests deu bi thay bang ban gia.
"""
from __future__ import annotations

import pytest

from bc_agent import bc_data as bd
from bc_agent.config import Settings

SETTINGS = Settings(
    bc_mode="api", bc_source="api", bc_tenant_id="t", bc_client_id="c", bc_client_secret="s",
    bc_environment="NWV01", bc_company_name="CRONUS", bc_company_id="11111111-2222-3333-4444-555555555555",
)


class _FakeApi:
    """Ghi lai loi goi, tra ve mot dong cho moi entity set."""

    ROWS = {
        bd.ES_ILE: [{
            "id": "x", "entryNo": 2170, "postingDate": "2026-09-10", "entryType": "Sale",
            "documentNo": "102313", "itemNo": "33170", "itemCategoryCode": "DESSERTS",
            "locationCode": "S0001", "quantity": -24, "remainingQuantity": 0,
            "lotNo": "L2609-33170", "expirationDate": "2026-12-20", "open": False,
            "costAmountActual": -132.0, "salesAmountActual": 172.36, "khongDungDen": "bo qua",
        }],
        bd.ES_LOT: [{"itemNo": "33170", "lotNo": "L2609-33170", "description": "",
                     "blocked": False, "inventory": 40, "expiredInventory": 0}],
        bd.ES_ITEM: [{"itemNo": "33170", "description": "Chocolate cake", "itemCategoryCode": "DESSERTS",
                      "baseUnitOfMeasure": "PCS", "itemTrackingCode": "LOTALLEXP", "unitCost": 5.5,
                      "reorderPoint": 12, "safetyStockQuantity": 5}],
        bd.ES_LOCATION: [{"code": "S0001", "name": "Cronus Super Market South", "useAsInTransit": False}],
        bd.ES_CATEGORY: [{"code": "DESSERTS", "description": "Desserts", "indentation": 0}],
        bd.ES_SKU: [{"locationCode": "S0001", "itemNo": "33170", "reorderPoint": 12,
                     "safetyStockQuantity": 5, "transferFromCode": "W0003"}],
        bd.ES_PO_LINE: [{"documentNo": "PO-001", "lineNo": 10000, "itemNo": "33170",
                         "outstandingQuantity": 30, "expectedReceiptDate": "2026-09-15"}],
        bd.ES_SO_LINE: [{"documentNo": "SO-001", "lineNo": 10000, "itemNo": "33170",
                         "outstandingQuantity": 5, "shipmentDate": "2026-09-12"}],
        bd.ES_VALUE_ENTRY: [{"entryNo": 9, "itemLedgerEntryNo": 2170, "postingDate": "2026-09-10",
                             "itemNo": "33170", "costAmountActual": -132.0, "salesAmountActual": 172.36}],
    }

    def __init__(self):
        self.calls: list[dict] = []

    def list(self, entity_set, filter=None, orderby=None, top=None):
        self.calls.append({"entity_set": entity_set, "filter": filter, "orderby": orderby, "top": top})
        return self.ROWS.get(entity_set, [])


@pytest.fixture()
def data():
    return bd.BCData(SETTINGS, api=_FakeApi())


def test_mac_dinh_la_duong_api_khi_tiem_api_client(data):
    assert data.source == "api"
    assert data.ws is None and data.v2 is None


def test_ile_dung_entity_set_va_sap_xep_theo_camel_case(data):
    rows = data.item_ledger_entries(top=5)
    call = data.api.calls[-1]
    assert call["entity_set"] == bd.ES_ILE
    assert call["orderby"] == "postingDate desc"
    assert set(rows[0]) == set(bd.ILE_API)
    assert rows[0]["item_no"] == "33170"
    assert rows[0]["item_category"] == "DESSERTS"
    assert rows[0]["expiration_date"] == "2026-12-20"
    assert "khongDungDen" not in rows[0]


def test_khong_con_truong_nao_thieu_o_duong_api(data):
    assert data.missing_ile_fields() == []


def test_lot_khong_co_truong_han_dung(data):
    """Bang Lot No. Information (6505) khong co Expiration Date, cung khong co
    Expiration Action Date. Da kiem tren tai lieu AL. Neu co ngay ai do them lai vao day
    thi test nay phai do, vi so lieu se sai mot cach im lang."""
    m = data.lot_field_map()
    assert "expiration_date" not in m
    assert "expiration_action_date" not in m
    rows = data.lots(top=1)
    assert rows[0]["lot_no"] == "L2609-33170"
    assert rows[0]["inventory"] == 40


def test_item_va_location_lay_qua_custom_api_chu_khong_phai_v2(data):
    items = data.items()
    locs = data.locations()
    assert items[0]["item_tracking_code"] == "LOTALLEXP"
    assert items[0]["reorder_point"] == 12
    assert locs[0]["in_transit"] is False
    assert [c["entity_set"] for c in data.api.calls] == [bd.ES_ITEM, bd.ES_LOCATION]


def test_bon_nguon_chi_co_o_duong_api(data):
    assert data.stockkeeping_units()[0]["transfer_from"] == "W0003"
    assert data.item_categories()[0]["code"] == "DESSERTS"
    assert data.purchase_order_lines()[0]["outstanding_qty"] == 30
    assert data.sales_order_lines()[0]["shipment_date"] == "2026-09-12"
    assert data.value_entries()[0]["ile_entry_no"] == 2170


def test_che_do_odata_bao_ro_la_thieu_chu_khong_tra_ve_rong():
    """Web service khai tay chi co Item Ledger Entry va Lot No. Information.
    Hoi Stockkeeping Unit o che do do thi phai bao loi, khong duoc tra ve list rong."""
    from tests.test_bc_data import _FakeV2, _FakeWS

    d = bd.BCData(Settings(bc_mode="odata"), ws=_FakeWS(), v2=_FakeV2())
    assert d.source == "odata"
    for fn in (d.stockkeeping_units, d.item_categories, d.purchase_order_lines,
               d.sales_order_lines, d.value_entries):
        with pytest.raises(bd.ODataError, match="NWV Marou Data API"):
            fn()


def test_url_custom_api_dung_dinh_dang(monkeypatch):
    """Base URL phai la /api/<publisher>/<group>/<version>/companies(<guid>), khong phai /api/v2.0."""
    class _FakeToken:
        def __init__(self, *_a, **_k):
            pass

        def token(self):
            return "fake"

        def headers(self, extra=None):
            return {"Authorization": "Bearer fake"}

    monkeypatch.setattr(bd, "TokenProvider", _FakeToken)
    c = bd.ApiClient(SETTINGS)
    assert c.base == (
        "https://api.businesscentral.dynamics.com/v2.0/NWV01"
        "/api/naviworld/marouagent/v1.0"
        "/companies(11111111-2222-3333-4444-555555555555)"
    )
    assert bd.V2ApiClient(SETTINGS).base.endswith(
        "/NWV01/api/v2.0/companies(11111111-2222-3333-4444-555555555555)"
    )
