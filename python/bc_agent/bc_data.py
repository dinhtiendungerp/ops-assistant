"""BCData: mot cua vao duy nhat cho du lieu BC, che giau viec nguon nao den tu dau.

Hai duong lay du lieu, chon bang BC_SOURCE:

  api    (mac dinh) - custom API page cua extension "NWV Marou Data API".
         Entity set nwvItems, nwvItemLedgerEntries, nwvLotNoInformation, nwvStockkeepingUnits,
         nwvLocations, nwvItemCategories, nwvPurchaseOrderLines, nwvSalesOrderLines,
         nwvValueEntries. Ten truong co dinh do AL quy dinh nen khong phai do.

  odata  - web service OData V4 khai tay tren trang Web Services, cho page 38 va 6505.
         Duong du phong, dung khi extension chua publish. Ten truong doc tu $metadata vi
         BC dat ten truong web service theo caption, khac nhau giua cac ban dich.

Ly do phai co lop nay: API chuan v2.0 cua itemLedgerEntry khong co Location Code, Lot No.,
Expiration Date, Remaining Quantity; va khong co entity nao cho Lot No. Information,
Stockkeeping Unit, dong don mua, Value Entry.

Hai su that da kiem tren tai lieu AL, khong suy doan:
  - Bang "Lot No. Information" (6505) KHONG co Expiration Date, cung khong co Expiration
    Action Date. Han dung chi nam tren Item Ledger Entry.
  - Bang "Item Ledger Entry" (32) CO Item Category Code, khong can join sang Item de nhom
    theo nganh hang.
"""
from __future__ import annotations

import logging
import re
from typing import Any

import requests

from .auth import TokenProvider
from .config import Settings
from .odata import Condition, to_odata_filter
from .odata_client import API_ROOT, ODataError, ODataWSClient

log = logging.getLogger(__name__)

# ---------------------------------------------------------------- duong custom API page
PUBLISHER, GROUP, VERSION = "naviworld", "marouagent", "v1.0"

ES_ITEM = "nwvItems"
ES_ILE = "nwvItemLedgerEntries"
ES_LOT = "nwvLotNoInformation"
ES_SKU = "nwvStockkeepingUnits"
ES_LOCATION = "nwvLocations"
ES_CATEGORY = "nwvItemCategories"
ES_PO_LINE = "nwvPurchaseOrderLines"
ES_SO_LINE = "nwvSalesOrderLines"
ES_VALUE_ENTRY = "nwvValueEntries"

# Khoa chuan -> ten truong tren API page. Doi ten o AL thi doi o day, khong doi cho khac.
ILE_API = {
    "entry_no": "entryNo", "posting_date": "postingDate", "entry_type": "entryType",
    "document_type": "documentType", "document_no": "documentNo", "source_type": "sourceType",
    "source_no": "sourceNo", "item_no": "itemNo", "item_category": "itemCategoryCode",
    "description": "description", "variant_code": "variantCode", "location_code": "locationCode",
    "uom": "unitOfMeasureCode", "quantity": "quantity", "invoiced_qty": "invoicedQuantity",
    "remaining_qty": "remainingQuantity", "reserved_qty": "reservedQuantity", "open": "open",
    "positive": "positive", "lot_no": "lotNo", "serial_no": "serialNo", "package_no": "packageNo",
    "expiration_date": "expirationDate", "warranty_date": "warrantyDate",
    "cost_amount": "costAmountActual", "sales_amount": "salesAmountActual",
    "dim1": "globalDimension1Code", "dim2": "globalDimension2Code",
    "order_type": "orderType", "order_no": "orderNo", "correction": "correction",
    "last_modified": "lastModifiedDateTime",
}

LOT_API = {
    "item_no": "itemNo", "variant_code": "variantCode", "lot_no": "lotNo",
    "description": "description", "certificate_number": "certificateNumber",
    "blocked": "blocked", "inventory": "inventory", "expired_inventory": "expiredInventory",
    "last_modified": "lastModifiedDateTime",
}

ITEM_API = {
    "item_no": "itemNo", "description": "description", "item_category": "itemCategoryCode",
    "base_uom": "baseUnitOfMeasure", "item_tracking_code": "itemTrackingCode",
    "unit_cost": "unitCost", "unit_price": "unitPrice", "last_direct_cost": "lastDirectCost",
    "costing_method": "costingMethod", "blocked": "blocked",
    "replenishment_system": "replenishmentSystem", "reordering_policy": "reorderingPolicy",
    "reorder_point": "reorderPoint", "reorder_qty": "reorderQuantity",
    "safety_stock": "safetyStockQuantity", "max_inventory": "maximumInventory",
    "min_order_qty": "minimumOrderQuantity", "max_order_qty": "maximumOrderQuantity",
    "order_multiple": "orderMultiple", "vendor_no": "vendorNo", "inventory": "inventory",
    "qty_on_purch_order": "qtyOnPurchOrder", "qty_on_sales_order": "qtyOnSalesOrder",
}

SKU_API = {
    "location_code": "locationCode", "item_no": "itemNo", "variant_code": "variantCode",
    "description": "description", "replenishment_system": "replenishmentSystem",
    "reordering_policy": "reorderingPolicy", "reorder_point": "reorderPoint",
    "reorder_qty": "reorderQuantity", "safety_stock": "safetyStockQuantity",
    "max_inventory": "maximumInventory", "min_order_qty": "minimumOrderQuantity",
    "max_order_qty": "maximumOrderQuantity", "order_multiple": "orderMultiple",
    "transfer_from": "transferFromCode", "vendor_no": "vendorNo", "unit_cost": "unitCost",
    "inventory": "inventory", "qty_on_purch_order": "qtyOnPurchOrder",
    "qty_on_sales_order": "qtyOnSalesOrder",
}

LOCATION_API = {
    "code": "code", "name": "name", "city": "city", "country": "countryRegionCode",
    "in_transit": "useAsInTransit", "bin_mandatory": "binMandatory",
    "require_pick": "requirePick", "require_receive": "requireReceive",
    "require_shipment": "requireShipment", "require_putaway": "requirePutAway",
}

CATEGORY_API = {
    "code": "code", "description": "description",
    "parent": "parentCategory", "indentation": "indentation",
}

PO_LINE_API = {
    "document_no": "documentNo", "line_no": "lineNo", "vendor_no": "buyFromVendorNo",
    "item_no": "itemNo", "variant_code": "variantCode", "description": "description",
    "location_code": "locationCode", "quantity": "quantity",
    "outstanding_qty": "outstandingQuantity", "received_qty": "quantityReceived",
    "uom": "unitOfMeasureCode", "direct_unit_cost": "directUnitCost",
    "order_date": "orderDate", "expected_receipt_date": "expectedReceiptDate",
    "planned_receipt_date": "plannedReceiptDate",
}

SO_LINE_API = {
    "document_no": "documentNo", "line_no": "lineNo", "customer_no": "sellToCustomerNo",
    "item_no": "itemNo", "variant_code": "variantCode", "description": "description",
    "location_code": "locationCode", "quantity": "quantity",
    "outstanding_qty": "outstandingQuantity", "shipped_qty": "quantityShipped",
    "uom": "unitOfMeasureCode", "unit_price": "unitPrice", "shipment_date": "shipmentDate",
}

VALUE_ENTRY_API = {
    "entry_no": "entryNo", "ile_entry_no": "itemLedgerEntryNo", "posting_date": "postingDate",
    "ile_entry_type": "itemLedgerEntryType", "entry_type": "entryType",
    "document_no": "documentNo", "source_type": "sourceType", "source_no": "sourceNo",
    "item_no": "itemNo", "variant_code": "variantCode", "location_code": "locationCode",
    "item_charge_no": "itemChargeNo", "valued_qty": "valuedQuantity",
    "invoiced_qty": "invoicedQuantity", "cost_amount": "costAmountActual",
    "cost_amount_expected": "costAmountExpected", "sales_amount": "salesAmountActual",
    "discount_amount": "discountAmount",
    "dim1": "globalDimension1Code", "dim2": "globalDimension2Code",
}

# ---------------------------------------------------------------- duong web service OData
SVC_ILE = "NWVILE"
SVC_LOTS = "NWVLots"

ILE_KEYS = {
    "entry_no": ["entryno"],
    "item_no": ["itemno"],
    "posting_date": ["postingdate"],
    "entry_type": ["entrytype"],
    "document_no": ["documentno"],
    "location_code": ["locationcode"],
    "quantity": ["quantity"],
    "remaining_qty": ["remainingquantity", "remainingqty"],
    "lot_no": ["lotno"],
    "expiration_date": ["expirationdate"],
}

LOT_KEYS = {
    "item_no": ["itemno"],
    "lot_no": ["lotno"],
    "variant_code": ["variantcode"],
    "description": ["description"],
    "blocked": ["blocked"],
    "inventory": ["inventory"],
}

# API chuan v2.0, dung khi chay o che do odata va can item / location.
ITEM_MAP_V2 = {
    "item_no": "number", "description": "displayName",
    "item_category": "itemCategoryCode", "base_uom": "baseUnitOfMeasureCode",
    "unit_cost": "unitCost", "blocked": "blocked",
}
LOCATION_MAP_V2 = {"code": "code", "name": "displayName"}


def _norm(s: str) -> str:
    return re.sub(r"[^a-z0-9]", "", s.lower())


def _resolve(fields: list[str], keys: dict[str, list[str]]) -> dict[str, str | None]:
    index = {_norm(f): f for f in fields}
    return {k: next((index[a] for a in al if a in index), None) for k, al in keys.items()}


# Truong kieu Option tren API tra ve ten enum da ma hoa: khoang trang thanh `_x0020_`,
# dau cham thanh `_x002E_`. Vi du `Negative Adjmt.` ve thanh `Negative_x0020_Adjmt_x002E_`,
# va option rong ve thanh `_x0020_`. Khong giai ma thi moi phep so sanh ben Python deu truot:
# lop tinh toan bo het dong Negative Adjmt. khoi luong xuat, nhu cau tai kho tut xuong, va
# phan tang lech so voi lop AL. Da bat duoc loi nay ngay 12/09/2026 luc doi chieu tren BC that.
OPTION_FIELDS = frozenset({"entry_type", "document_type", "source_type", "order_type",
                           "ile_entry_type"})

# BC khong tra ngay rong, no tra `0001-01-01` (gia tri 0D). De nguyen thi moi phep tru ngay
# deu ra so am bay tram nghin: `observed_shelf_life` cho ra -739.787 ngay cho moi mat hang
# khong co han dung, va muc ton muc tieu bi chan xuong 1 ngay. Bat duoc ngay 12/09/2026.
ZERO_DATE = "0001-01-01"


def norm_date(v: Any) -> Any:
    """Ngay 0D cua BC khong phai mot ngay. Tra ve None de moi noi khac khong phai biet dieu do."""
    if isinstance(v, str) and v.startswith(ZERO_DATE):
        return None
    return v

_OPT_ESC = re.compile(r"_x([0-9A-Fa-f]{4})_")


def unescape_option(v: Any) -> Any:
    """Giai ma ten Option cua OData ve dang BC hien tren giao dien."""
    if not isinstance(v, str) or "_x" not in v:
        return v
    return _OPT_ESC.sub(lambda m: chr(int(m.group(1), 16)), v).strip()


def _project(rows: list[dict[str, Any]], mapping: dict[str, str | None]) -> list[dict[str, Any]]:
    out = []
    for r in rows:
        d = {k: (r.get(src) if src else None) for k, src in mapping.items()}
        for k in mapping:
            if k in OPTION_FIELDS:
                d[k] = unescape_option(d[k])
            elif k.endswith("_date") or k.endswith("_at"):
                d[k] = norm_date(d[k])
        out.append(d)
    return out


class _RestClient:
    """Phan HTTP dung chung cho custom API page va API chuan v2.0."""

    def __init__(self, s: Settings, path: str, timeout: int = 120):
        s.validate_live_bc()
        self.s = s
        self.timeout = timeout
        self.auth = TokenProvider(s)
        self.v2_root = f"{API_ROOT}/{s.bc_environment}/api/v2.0"
        self.company_id = s.bc_company_id or self._resolve_company_id(s.bc_company_name)
        self.base = f"{API_ROOT}/{s.bc_environment}/api/{path}/companies({self.company_id})"

    def _resolve_company_id(self, name: str) -> str:
        r = requests.get(f"{self.v2_root}/companies", headers=self.auth.headers(),
                         params={"$filter": f"name eq '{name}'"}, timeout=self.timeout)
        if r.status_code >= 400:
            raise ODataError(f"HTTP {r.status_code} khi tim company: {r.text[:300]}")
        items = r.json().get("value", [])
        if not items:
            raise ODataError(f"Khong tim thay company '{name}' trong {self.s.bc_environment}")
        return items[0]["id"]

    def list(self, entity_set: str, filter: str | None = None, orderby: str | None = None,
             top: int | None = None) -> list[dict[str, Any]]:
        params: dict[str, Any] = {}
        if filter:
            params["$filter"] = filter
        if orderby:
            params["$orderby"] = orderby
        if top:
            params["$top"] = top
        url = f"{self.base}/{entity_set}"
        out: list[dict[str, Any]] = []
        while url:
            r = requests.get(url, headers=self.auth.headers(), params=params, timeout=self.timeout)
            if r.status_code >= 400:
                raise ODataError(f"HTTP {r.status_code} GET {r.url}: {r.text[:400]}")
            body = r.json()
            out.extend(body.get("value", []))
            url = body.get("@odata.nextLink")
            params = {}
            if top and len(out) >= top:
                break
        return out[:top] if top else out


class ApiClient(_RestClient):
    """Custom API page cua extension NWV Marou Data API."""

    def __init__(self, s: Settings, timeout: int = 120):
        super().__init__(s, f"{PUBLISHER}/{GROUP}/{VERSION}", timeout)


class V2ApiClient(_RestClient):
    """API chuan v2.0. Khong can extension, nhung thieu truong, chi dung o che do odata."""

    def __init__(self, s: Settings, timeout: int = 120):
        super().__init__(s, "v2.0", timeout)


class BCData:
    """source = 'api' dung custom API page, 'odata' dung web service khai tay."""

    def __init__(self, s: Settings, source: str | None = None,
                 api: ApiClient | None = None, ws: ODataWSClient | None = None,
                 v2: V2ApiClient | None = None):
        self.s = s
        if source is None and api is None and ws is not None:
            source = "odata"          # test va cac cho tiem san ws thi khoi phai noi lai
        if source is None and api is not None:
            source = "api"
        self.source = (source or getattr(s, "bc_source", None) or "api").lower()
        if self.source not in ("api", "odata"):
            raise ODataError(f"BC_SOURCE khong hop le: {self.source}. Dung api | odata")
        self.api = api if api is not None else (ApiClient(s) if self.source == "api" else None)
        self.ws = ws if ws is not None else (ODataWSClient(s) if self.source == "odata" else None)
        self.v2 = v2 if v2 is not None else (V2ApiClient(s) if self.source == "odata" else None)
        self._ile_map: dict[str, str | None] | None = None
        self._lot_map: dict[str, str | None] | None = None

    # ---------- do ten truong: chi can o che do odata ----------
    def _map_for(self, service: str, keys: dict[str, list[str]]) -> dict[str, str | None]:
        by_type = self.ws.entity_fields()
        fields = by_type.get(service) or next(
            (v for k, v in by_type.items() if _norm(k) == _norm(service)), []
        )
        if not fields:
            raise ODataError(
                f"Khong thay entity type '{service}' trong $metadata. "
                f"Kiem lai web service da Published chua."
            )
        return _resolve(fields, keys)

    def ile_field_map(self) -> dict[str, str | None]:
        if self.source == "api":
            return dict(ILE_API)
        if self._ile_map is None:
            self._ile_map = self._map_for(SVC_ILE, ILE_KEYS)
        return self._ile_map

    def lot_field_map(self) -> dict[str, str | None]:
        if self.source == "api":
            return dict(LOT_API)
        if self._lot_map is None:
            self._lot_map = self._map_for(SVC_LOTS, LOT_KEYS)
        return self._lot_map

    def missing_ile_fields(self) -> list[str]:
        return [k for k, v in self.ile_field_map().items() if v is None]

    # ---------- du lieu ----------
    def item_ledger_entries(self, conds: list[Condition] | None = None, top: int | None = None,
                            newest_first: bool = True) -> list[dict[str, Any]]:
        m = self.ile_field_map()
        orderby = f"{m['posting_date']} desc" if (newest_first and m.get("posting_date")) else None
        flt = to_odata_filter(conds or [])
        if self.source == "api":
            rows = self.api.list(ES_ILE, filter=flt, orderby=orderby, top=top)
        else:
            rows = self.ws.list(SVC_ILE, filter=flt, orderby=orderby, top=top)
        return _project(rows, m)

    def lots(self, conds: list[Condition] | None = None, top: int | None = None) -> list[dict[str, Any]]:
        m = self.lot_field_map()
        flt = to_odata_filter(conds or [])
        if self.source == "api":
            rows = self.api.list(ES_LOT, filter=flt, top=top)
        else:
            rows = self.ws.list(SVC_LOTS, filter=flt, top=top)
        return _project(rows, m)

    def items(self, conds: list[Condition] | None = None, top: int | None = None) -> list[dict[str, Any]]:
        if self.source == "api":
            return _project(self.api.list(ES_ITEM, filter=to_odata_filter(conds or []), top=top), ITEM_API)
        return _project(self.v2.list("items", top=top), ITEM_MAP_V2)

    def locations(self, top: int | None = None) -> list[dict[str, Any]]:
        if self.source == "api":
            return _project(self.api.list(ES_LOCATION, top=top), LOCATION_API)
        return _project(self.v2.list("locations", top=top), LOCATION_MAP_V2)

    # Bon nguon duoi day chi co o che do api, vi API chuan khong co entity tuong ung.
    def _api_only(self, what: str):
        if self.source != "api":
            raise ODataError(
                f"{what} chi lay duoc qua custom API page. Publish extension NWV Marou Data API "
                f"roi dat BC_SOURCE=api."
            )

    def stockkeeping_units(self, conds: list[Condition] | None = None, top: int | None = None) -> list[dict[str, Any]]:
        self._api_only("Stockkeeping Unit")
        return _project(self.api.list(ES_SKU, filter=to_odata_filter(conds or []), top=top), SKU_API)

    def item_categories(self, top: int | None = None) -> list[dict[str, Any]]:
        self._api_only("Item Category")
        return _project(self.api.list(ES_CATEGORY, top=top), CATEGORY_API)

    def purchase_order_lines(self, conds: list[Condition] | None = None, top: int | None = None) -> list[dict[str, Any]]:
        self._api_only("Dong don mua")
        return _project(self.api.list(ES_PO_LINE, filter=to_odata_filter(conds or []), top=top), PO_LINE_API)

    def sales_order_lines(self, conds: list[Condition] | None = None, top: int | None = None) -> list[dict[str, Any]]:
        self._api_only("Dong don ban")
        return _project(self.api.list(ES_SO_LINE, filter=to_odata_filter(conds or []), top=top), SO_LINE_API)

    def value_entries(self, conds: list[Condition] | None = None, top: int | None = None,
                      newest_first: bool = True) -> list[dict[str, Any]]:
        self._api_only("Value Entry")
        orderby = "postingDate desc" if newest_first else None
        rows = self.api.list(ES_VALUE_ENTRY, filter=to_odata_filter(conds or []), orderby=orderby, top=top)
        return _project(rows, VALUE_ENTRY_API)
