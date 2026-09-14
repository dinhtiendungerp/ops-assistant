"""UC3: scorecard nha cung cap, ban doi chieu doc lap cua codeunit 70121 NWV Supplier Scorecard Calc.

Dau vao: dong don mua (API nwvPurchaseOrderLines) va dong phieu nhan (API nwvPurchaseReceiptLines). Dau ra: cung ten
truong voi API supplierScorecards. Hai ben chay tren cung du lieu phai ra cung con so; lech la mot trong hai sai.
Dinh nghia tung chi so ghi o dau codeunit 70121, chep lai o day tung buoc.
"""
from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass
from datetime import date, timedelta
from typing import Any


@dataclass
class SupplierThresholds:
    tolerance_days: int = 0
    on_time_warn: float = 80.0
    history_days: int = 180


def _d(v: Any) -> date | None:
    s = str(v or "")[:10]
    try:
        d = date.fromisoformat(s)
    except ValueError:
        return None
    return None if d.year <= 1 else d


def _r(x: float, step: float) -> float:
    from decimal import ROUND_HALF_UP, Decimal
    return float((Decimal(str(x)) / Decimal(str(step))).quantize(Decimal("1"), rounding=ROUND_HALF_UP) * Decimal(str(step)))


def scorecard(po_lines: list[dict], rcpt_lines: list[dict], as_of: date, th: SupplierThresholds = SupplierThresholds(),
              vendors: dict[str, str] | None = None, categories: dict[str, str] | None = None) -> list[dict]:
    """categories: itemNo -> Item Category Code (Purchase Line cua BC tu co truong nay; API chua phoi ra nen tra tu Item)."""
    vendors = vendors or {}
    categories = categories or {}
    from_date = as_of - timedelta(days=th.history_days)
    rc: dict[tuple[str, int], list[dict]] = defaultdict(list)
    for r in rcpt_lines:
        if float(r.get("quantity") or 0) != 0:
            rc[(r.get("orderNo"), int(r.get("orderLineNo") or 0))].append(r)

    acc: dict[tuple[str, str], dict[str, Any]] = {}

    def row(vendor: str, cat: str) -> dict[str, Any]:
        if (vendor, cat) not in acc:
            acc[(vendor, cat)] = {"vendorNo": vendor, "itemCategoryCode": cat, "vendorName": vendors.get(vendor, ""),
                                  "linesDue": 0, "linesCompleted": 0, "linesOnTime": 0, "_first": 0, "_received": 0,
                                  "_delay": 0, "_late": 0, "_promised": 0, "_actual": 0, "openLines": 0, "overdueLines": 0,
                                  "overdueQty": 0.0, "overdueAmount": 0.0, "lastReceiptDate": None}
        return acc[(vendor, cat)]

    for pl in po_lines:
        vendor = pl.get("buyFromVendorNo") or ""
        qty = float(pl.get("quantity") or 0)
        if not vendor or qty <= 0:
            continue
        exp = _d(pl.get("expectedReceiptDate"))
        order_date = _d(pl.get("orderDate"))
        receipts = rc.get((pl.get("documentNo"), int(pl.get("lineNo") or 0)), [])
        has = bool(receipts)
        completed_on = max((_d(r["postingDate"]) for r in receipts), default=None)
        first = min((_d(r["postingDate"]) for r in receipts), default=None)
        first_qty = sum(float(r["quantity"]) for r in receipts if _d(r["postingDate"]) == first)
        completed = float(pl.get("quantityReceived") or 0) >= qty and has
        for cat in (categories.get(pl.get("itemNo"), ""), ""):
            a = row(vendor, cat)
            if float(pl.get("outstandingQuantity") or 0) > 0:
                a["openLines"] += 1
                if exp and exp >= from_date and as_of > exp + timedelta(days=th.tolerance_days):
                    a["overdueLines"] += 1
                    a["overdueQty"] += float(pl["outstandingQuantity"])
                    a["overdueAmount"] += float(pl["outstandingQuantity"]) * float(pl.get("directUnitCost") or 0)
            if has and (a["lastReceiptDate"] is None or completed_on > a["lastReceiptDate"]):
                a["lastReceiptDate"] = completed_on
            if exp and from_date <= exp <= as_of:
                a["linesDue"] += 1
                if order_date:
                    a["_promised"] += (exp - order_date).days
                if completed:
                    a["linesCompleted"] += 1
                    if completed_on <= exp + timedelta(days=th.tolerance_days):
                        a["linesOnTime"] += 1
                    if order_date:
                        a["_actual"] += (completed_on - order_date).days
                    delay = (completed_on - exp).days
                else:
                    delay = (as_of - exp).days
                if delay > th.tolerance_days:
                    a["_delay"] += delay
                    a["_late"] += 1
                if has:
                    a["_received"] += 1
                    if first_qty >= qty:
                        a["_first"] += 1

    out = []
    for (vendor, cat), a in sorted(acc.items()):
        if a["linesDue"] == 0 and a["overdueLines"] == 0:      # khong co gi de cham, giong codeunit 70121
            continue
        r = {k: v for k, v in a.items() if not k.startswith("_")}
        r["periodFrom"], r["periodTo"], r["asOfDate"] = from_date.isoformat(), as_of.isoformat(), as_of.isoformat()
        r["avgDelayDays"] = _r(a["_delay"] / a["_late"], 0.1) if a["_late"] else 0.0
        r["onTimePct"] = _r(a["linesOnTime"] / a["linesDue"] * 100, 0.1) if a["linesDue"] else 0.0
        r["avgPromisedLeadTime"] = _r(a["_promised"] / a["linesDue"], 0.1) if a["linesDue"] else 0.0
        r["avgActualLeadTime"] = _r(a["_actual"] / a["linesCompleted"], 0.1) if a["linesCompleted"] else 0.0
        r["firstDeliveryCompletePct"] = _r(a["_first"] / a["_received"] * 100, 0.1) if a["_received"] else 0.0
        r["overdueAmount"] = _r(a["overdueAmount"], 0.01)
        r["lastReceiptDate"] = a["lastReceiptDate"].isoformat() if a["lastReceiptDate"] else None
        ly_do = []
        if r["linesDue"] >= 3 and r["onTimePct"] < th.on_time_warn:
            ly_do.append(f"Giao đúng hạn {r['onTimePct']:g}%, dưới ngưỡng {th.on_time_warn:g}%.")
        if r["overdueLines"] > 0:
            ly_do.append(f"{r['overdueLines']} dòng quá hạn chưa nhận đủ.")
        r["needsAttention"] = bool(ly_do)
        r["attentionReason"] = " ".join(ly_do)
        out.append(r)
    return out


def plan_to_lines(plan: dict, doc_prefix: str = "PO") -> tuple[list[dict], list[dict]]:
    """Dung dong don mua va phieu nhan tu ke hoach demo (tools/supplier_demo.py), dung cho fixtures cua mock."""
    po, rc = [], []
    for i, o in enumerate(plan["orders"], 1):
        doc = o["key"]          # so don de doc: NCC-0001, NCC-MO-01
        received: dict[int, float] = defaultdict(float)
        for j, rcp in enumerate(o["receipts"], 1):
            for x in rcp["lines"]:
                ln = (x["line"] + 1) * 10000
                received[ln] += x["quantity"]
                rc.append({"id": f"rc-{doc}-{j}-{ln}", "documentNo": f"R{doc}-{j}", "lineNo": ln, "orderNo": doc, "orderLineNo": ln,
                           "buyFromVendorNo": o["vendorNo"], "itemNo": o["lines"][x["line"]]["itemNo"],
                           "locationCode": o["locationCode"], "quantity": x["quantity"], "postingDate": rcp["date"],
                           "expectedReceiptDate": o["lines"][x["line"]]["expectedReceiptDate"]})
        for k, l in enumerate(o["lines"]):
            ln = (k + 1) * 10000
            q = float(l["quantity"])
            po.append({"id": f"po-{doc}-{ln}", "documentNo": doc, "lineNo": ln, "buyFromVendorNo": o["vendorNo"],
                       "itemNo": l["itemNo"], "variantCode": "", "description": "", "locationCode": o["locationCode"],
                       "quantity": q, "outstandingQuantity": q - received[ln], "quantityReceived": received[ln],
                       "unitOfMeasureCode": "", "directUnitCost": l["unitCost"], "orderDate": o["orderDate"],
                       "expectedReceiptDate": l["expectedReceiptDate"], "plannedReceiptDate": l["expectedReceiptDate"],
                       "vendorOrderNo": o["key"]})
    return po, rc
