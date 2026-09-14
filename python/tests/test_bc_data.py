"""Test cho duong web service OData khai tay (BC_SOURCE=odata).

Khong goi mang. ODataWSClient va V2ApiClient deu bi thay bang ban gia.

Duong nay ton tai vi mot ly do: khi extension NWV Marou Data API chua publish thi van phai
doc duoc Item Ledger Entry va Lot No. Information. Diem khac biet lon nhat so voi duong custom
API page la ten truong: BC dat ten truong web service theo caption cua field, nen phai do tu
$metadata roi khop bang alias, khong duoc doan.
"""
from __future__ import annotations

import pytest

from bc_agent import bc_data as bd
from bc_agent.config import Settings

SETTINGS = Settings(bc_mode="odata", bc_source="odata")

# Ten truong theo kieu caption ma BC sinh ra cho web service, khong phai camelCase cua API page.
ILE_FIELDS = [
    "Entry_No", "Item_No", "Posting_Date", "Entry_Type", "Document_No",
    "Location_Code", "Quantity", "Remaining_Quantity", "Lot_No", "Expiration_Date",
]
LOT_FIELDS = ["Item_No", "Lot_No", "Variant_Code", "Description", "Blocked", "Inventory"]


class _FakeWS:
    """Gia ODataWSClient: tra ve $metadata co san va mot dong cho moi service."""

    ROWS = {
        bd.SVC_ILE: [{
            "Entry_No": 2170, "Item_No": "33170", "Posting_Date": "2026-09-10",
            "Entry_Type": "Sale", "Document_No": "102313", "Location_Code": "S0001",
            "Quantity": -24, "Remaining_Quantity": 0, "Lot_No": "L2609-33170",
            "Expiration_Date": "2026-12-20", "Khong_Dung_Den": "bo qua",
        }],
        bd.SVC_LOTS: [{
            "Item_No": "33170", "Lot_No": "L2609-33170", "Variant_Code": "",
            "Description": "", "Blocked": False, "Inventory": 40,
        }],
    }

    def __init__(self, fields: dict[str, list[str]] | None = None):
        self.fields = fields if fields is not None else {
            bd.SVC_ILE: list(ILE_FIELDS), bd.SVC_LOTS: list(LOT_FIELDS)
        }
        self.calls: list[dict] = []

    def entity_fields(self):
        return self.fields

    def list(self, service, filter=None, orderby=None, top=None):
        self.calls.append({"service": service, "filter": filter, "orderby": orderby, "top": top})
        return self.ROWS.get(service, [])


class _FakeV2:
    """Gia V2ApiClient: API chuan v2.0, chi co items va locations."""

    ROWS = {
        "items": [{"number": "33170", "displayName": "Chocolate cake",
                   "itemCategoryCode": "DESSERTS", "baseUnitOfMeasureCode": "PCS",
                   "unitCost": 5.5, "blocked": False}],
        "locations": [{"code": "S0001", "displayName": "Cronus Super Market South"}],
    }

    def __init__(self):
        self.calls: list[dict] = []

    def list(self, entity_set, filter=None, orderby=None, top=None):
        self.calls.append({"entity_set": entity_set, "top": top})
        return self.ROWS.get(entity_set, [])


@pytest.fixture()
def data():
    return bd.BCData(SETTINGS, ws=_FakeWS(), v2=_FakeV2())


def test_tiem_ws_thi_tu_hieu_la_duong_odata(data):
    assert data.source == "odata"
    assert data.api is None


def test_ten_truong_do_tu_metadata_chu_khong_doan(data):
    m = data.ile_field_map()
    assert m["entry_no"] == "Entry_No"
    assert m["remaining_qty"] == "Remaining_Quantity"
    assert m["expiration_date"] == "Expiration_Date"
    assert data.missing_ile_fields() == []


def test_doc_metadata_mot_lan_roi_giu_lai(data):
    data.ile_field_map()
    data.ile_field_map()
    assert data._ile_map is not None


def test_truong_thieu_thi_bao_ten_chu_khong_im_lang():
    """Web service khai thieu cot thi phai noi ro thieu cot nao. Tra ve None im lang
    se thanh so 0 o lop tinh toan va khong ai phat hien ra."""
    ws = _FakeWS({bd.SVC_ILE: ["Entry_No", "Item_No", "Posting_Date"],
                  bd.SVC_LOTS: list(LOT_FIELDS)})
    d = bd.BCData(SETTINGS, ws=ws, v2=_FakeV2())
    thieu = d.missing_ile_fields()
    assert "lot_no" in thieu and "expiration_date" in thieu and "remaining_qty" in thieu
    assert "entry_no" not in thieu


def test_khong_thay_entity_type_thi_bao_loi_ro_rang():
    d = bd.BCData(SETTINGS, ws=_FakeWS({}), v2=_FakeV2())
    with pytest.raises(bd.ODataError, match="Published"):
        d.ile_field_map()


def test_ile_tra_ve_khoa_chuan_va_bo_cot_thua(data):
    rows = data.item_ledger_entries(top=5)
    call = data.ws.calls[-1]
    assert call["service"] == bd.SVC_ILE
    assert call["orderby"] == "Posting_Date desc"
    assert call["top"] == 5
    assert rows[0]["item_no"] == "33170"
    assert rows[0]["lot_no"] == "L2609-33170"
    assert "Khong_Dung_Den" not in rows[0]


def test_lot_khong_co_han_dung_o_duong_odata(data):
    """Bang Lot No. Information (6505) khong co Expiration Date. Da kiem tren source base app."""
    m = data.lot_field_map()
    assert "expiration_date" not in m
    rows = data.lots(top=1)
    assert rows[0]["inventory"] == 40


def test_item_va_location_lay_qua_api_chuan_v2(data):
    items = data.items()
    locs = data.locations()
    assert items[0]["item_no"] == "33170"
    assert items[0]["description"] == "Chocolate cake"
    assert locs[0]["code"] == "S0001"
    assert [c["entity_set"] for c in data.v2.calls] == ["items", "locations"]


def test_nguon_khong_hop_le_thi_bao_ngay():
    with pytest.raises(bd.ODataError, match="BC_SOURCE"):
        bd.BCData(SETTINGS, source="graphql", ws=_FakeWS(), v2=_FakeV2())
