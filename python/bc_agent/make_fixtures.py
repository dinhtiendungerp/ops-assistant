"""Dung fixtures cho MockBCClient tu chinh bo du lieu demo sap import vao BC.

Truoc 12/09/2026 fixtures la mot the gioi bia (WH-HCM, S-CALMETTE, MAR-MINI-24) khong lien quan
gi den bo du lieu demo. Tro ly chay mock ra mot bo so, BC that ra bo so khac, khong doi chieu
duoc. Gio mock lay tu `demo-data-nwv/` qua `bc_agent.demo_data`, va lop tinh toan la
`bc_agent.inventory` (ban doi chieu cua lop AL). Ket qua: 166 dong Inventory Health,
31/38/58/4/1/34 theo tang, 22 de xuat dieu chuyen, trung `demo-data-nwv/uc2-expected.json`.

Phan khong co trong bo du lieu demo (POS discount log, lich su de xuat cua tro ly) van la
du lieu dung, nhung dat tren dung cua hang va mat hang cua bo demo.

Chay:  cd python && python -m bc_agent.cli make-fixtures
"""
from __future__ import annotations

import csv
import json
import math
import random
import sys
import uuid
from collections import defaultdict
from datetime import date, datetime, timedelta, timezone
from pathlib import Path

from .demo_data import DEMO_DIR, ROOT, read_ile, read_items
from .inventory import HealthLine, ReplenishmentSuggestion, Thresholds, inventory_health, replenishment

sys.path.insert(0, str(ROOT / "tools"))
from demo_scenario import BY_NO, STORES, TODAY, WH  # noqa: E402  kich ban du lieu demo, chi dung luc sinh fixtures

SEED = 20260918
CALC_AT = datetime(2026, 9, 18, 1, 0, tzinfo=timezone.utc)
TH = Thresholds()

# Nguong POS, trung NWV Agent Setup mac dinh
MAX_MANUAL_PCT = 15.0
SHARE_WARN_PCT = 20.0
REPEAT_COUNT = 5


def _iso(d: date | None) -> str | None:
    return d.isoformat() if d else None


def _doc(v: float | None) -> float:
    """Khong co nhu cau thi mock ghi 9999, cung quy uoc voi gateway."""
    return 9999 if v is None else v


# ---------------------------------------------------------------- UC2 tu bo demo
def health_rows(lines: list[HealthLine]) -> list[dict]:
    out = []
    for l in lines:
        meta = BY_NO.get(l.item_no)
        out.append({
            "id": str(uuid.uuid4()), "itemNo": l.item_no, "locationCode": l.location_code,
            "lotNo": l.lot_no or "", "itemDescription": l.item_description or (meta.desc if meta else l.item_no),
            "itemCategoryCode": meta.cat if meta else "", "baseUnitOfMeasure": meta.uom if meta else "PCS",
            "quantityOnHand": l.quantity, "inventoryValue": round(l.inventory_value, 2),
            "avgDailySalesQty": l.avg_daily_qty, "daysOfCover": _doc(l.days_of_cover),
            "lastSaleDate": _iso(l.last_sale_date),
            "daysSinceLastSale": l.days_since_last_sale if l.days_since_last_sale is not None else TH.sales_history_days + 1,
            "expirationDate": _iso(l.expiration_date), "daysToExpiry": l.days_to_expiry,
            "demandBasis": l.demand_basis, "daysCensored": l.days_censored,
            "tier": l.tier, "riskScore": l.risk_score, "riskReason": l.risk_reason,
            "calculatedAt": CALC_AT.isoformat(), "asOfDate": TODAY.isoformat(),
        })
    return out


def suggestion_rows(sugg: list[ReplenishmentSuggestion], lines: list[HealthLine], ile: list[dict]) -> list[dict]:
    """AL ghi mot dong cho moi cap cua hang x mat hang co lich su, co co Stock-out Risk.
    `inventory.replenishment` chi tra ve cap co rui ro, nen cac cap con lai dung tu Inventory
    Health Line: ton, nhu cau, days of cover, va reason 'Du hang.'"""
    out = []
    seen = set()
    wh_qty: dict[str, float] = defaultdict(float)
    for l in lines:
        if l.location_code == WH:
            wh_qty[l.item_no] += l.quantity
    for s in sugg:
        seen.add((s.store_location_code, s.item_no))
        out.append({
            "id": str(uuid.uuid4()), "storeLocationCode": s.store_location_code, "itemNo": s.item_no,
            "itemDescription": s.item_description, "storeQtyOnHand": s.quantity_on_hand, "storeQtyInTransit": 0.0,
            "avgDailySalesQty": s.avg_daily_qty, "daysOfCover": _doc(s.days_of_cover),
            "targetQty": s.target_qty, "suggestedQty": s.suggested_qty,
            "warehouseQtyAvailable": s.source_available, "constrainedQty": s.constrained_qty,
            "sourceLocationCode": s.source_location_code, "targetDays": s.target_days,
            "shelfLifeDays": 0, "cappedByShelfLife": s.capped_by_shelf_life,
            "demandBasis": "sale", "daysCensored": 0,
            "stockOutRisk": s.stock_out_risk, "reason": s.rationale, "calculatedAt": CALC_AT.isoformat(),
        })
    pairs = {(r["location_code"], r["item_no"]) for r in ile if r["location_code"] in STORES}
    agg: dict[tuple[str, str], dict] = {}
    for l in lines:
        if l.location_code in STORES:
            a = agg.setdefault((l.location_code, l.item_no), {"qty": 0.0, "avg": l.avg_daily_qty, "desc": l.item_description,
                                                              "basis": l.demand_basis, "cens": l.days_censored})
            a["qty"] += l.quantity
    for store, item_no in sorted(pairs - seen):
        a = agg.get((store, item_no), {"qty": 0.0, "avg": 0.0, "desc": BY_NO[item_no].desc, "basis": "sale", "cens": 0})
        avg = float(a["avg"] or 0)
        doc = round(a["qty"] / avg, 1) if avg > 0 else 9999
        out.append({
            "id": str(uuid.uuid4()), "storeLocationCode": store, "itemNo": item_no, "itemDescription": a["desc"],
            "storeQtyOnHand": a["qty"], "storeQtyInTransit": 0.0, "avgDailySalesQty": avg, "daysOfCover": doc,
            "targetQty": math.ceil(avg * TH.target_days) if avg > 0 else 0, "suggestedQty": 0.0,
            "warehouseQtyAvailable": wh_qty.get(item_no, 0.0), "constrainedQty": 0.0,
            "sourceLocationCode": WH, "targetDays": TH.target_days, "shelfLifeDays": 0, "cappedByShelfLife": False,
            "demandBasis": a["basis"], "daysCensored": a["cens"],
            "stockOutRisk": False, "reason": "Đủ hàng.", "calculatedAt": CALC_AT.isoformat(),
        })
    return out


def sales_rows(ile: list[dict]) -> list[dict]:
    """Lich su ban theo ngay, dung cho dieu tra va tu danh gia. Cung dinh nghia voi duong live:
    dong Item Ledger Entry loai Sale, qty duong."""
    rows = []
    for r in ile:
        if r["entry_type"] == "Sale":
            rows.append({"date": r["posting_date"].isoformat(), "item_no": r["item_no"],
                         "location_code": r["location_code"], "qty": -r["quantity"]})
    rows.sort(key=lambda r: (r["date"], r["item_no"], r["location_code"]))
    return rows


# ---------------------------------------------------------------- lich su de xuat
def historical_proposals() -> list[dict]:
    """Hai lan tro ly da chuyen hang cho cap S0001 x 33200 (Chocolate ice cream) sau hai dot
    dut hang thang 6 va thang 7 trong bo demo. Lich su hanh dong nam trong BC, khong nam trong
    bo nho tro ly, nen de o day."""
    base = {"scenario": "StoreReplenishment", "actionType": "Transfer", "itemNo": "33200",
            "lotNo": "", "fromLocationCode": WH, "toLocationCode": "S0001",
            "status": "Executed", "createdByAgent": "NWV-AGENT", "modelName": "scripted",
            "resultDocumentType": "Transfer Order", "reviewComment": ""}
    return [
        {**base, "id": "a1000000-0000-4000-8000-000000000001", "proposalId": "AP-000181",
         "quantity": 24.0, "referenceKey": "S0001|33200|2026-06-21",
         "rationale": "Days of cover 1.4 dưới 5. Bổ sung lên mức 14 ngày.",
         "priorityScore": 86, "createdAt": "2026-06-21T01:10:00Z", "reviewedBy": "HUNG",
         "reviewedAt": "2026-06-21T02:40:00Z", "resultDocumentNo": "TO-0944", "runId": "hist",
         "evidenceJson": "{\"doc\": 1.4, \"avg\": 6.9}"},
        {**base, "id": "a1000000-0000-4000-8000-000000000002", "proposalId": "AP-000206",
         "quantity": 30.0, "referenceKey": "S0001|33200|2026-07-19",
         "rationale": "Days of cover 0.9 dưới 5. Bổ sung lên mức 14 ngày.",
         "priorityScore": 91, "createdAt": "2026-07-19T01:10:00Z", "reviewedBy": "HUNG",
         "reviewedAt": "2026-07-19T03:05:00Z", "resultDocumentNo": "TO-0977", "runId": "hist",
         "evidenceJson": "{\"doc\": 0.9, \"avg\": 7.2}"},
    ]


# ---------------------------------------------------------------- POS discount (khong co trong bo demo)
POS_STAFF = {"S0001": ["NV01", "NV02", "NV03"], "S0002": ["NV11", "NV12", "NV22"],
             "S0005": ["NV51", "NV52"], "S0010": ["NV61", "NV62"]}
HEAVY_DAY = date(2026, 9, 14)      # NV22 tai S0002: nhieu manual discount trong mot ngay (DG-02/DG-03)
OVERRIDE_DAY = date(2026, 9, 16)   # NV03 tai S0001: price override 30% khong co manager override (DG-01)


def gen_pos_discounts(rng: random.Random, days: int = 30) -> list[dict]:
    rows = []
    trans_no = 1000
    items = list(BY_NO.values())
    for i in range(days):
        d = TODAY - timedelta(days=days - i)
        for store, staffs in POS_STAFF.items():
            for st in staffs:
                n = rng.randint(2, 6)
                if st == "NV22" and d == HEAVY_DAY:
                    n = 9
                for k in range(n):
                    trans_no += 1
                    it = rng.choice(items)
                    qty = rng.randint(1, 4)
                    gross = round(it.price * qty, 2)
                    r = rng.random()
                    if st == "NV22" and d == HEAVY_DAY:
                        dtype, pct, offer = "ManualLine", rng.choice([15, 20, 25]), ""
                    elif r < 0.55:
                        dtype, pct, offer = "Offer", rng.choice([10, 15, 20]), "PROMO-SEP"
                    elif r < 0.75:
                        dtype, pct, offer = "Member", 5, ""
                    elif r < 0.97:
                        dtype, pct, offer = "ManualLine", rng.choice([5, 10]), ""
                    else:
                        dtype, pct, offer = "ManualTotal", rng.choice([10, 20, 25]), ""
                    override = dtype.startswith("Manual") and pct > 15 and (rng.random() < 0.6 or st == "NV22")
                    if st == "NV03" and d == OVERRIDE_DAY and k == 0:
                        dtype, pct, offer, override = "PriceOverride", 30, "", False
                    term = f"P{store[1:]}01"
                    rows.append({
                        "id": str(uuid.uuid4()), "storeNo": store, "posTerminalNo": term, "transactionNo": trans_no,
                        "lineNo": 10000, "receiptNo": f"R{trans_no}", "transDate": d.isoformat(),
                        "transTime": f"{rng.randint(9, 20):02d}:{rng.randint(0, 59):02d}:00", "staffId": st, "itemNo": it.no,
                        "quantity": qty, "grossAmount": gross, "discountAmount": round(gross * pct / 100, 2), "discountPct": float(pct),
                        "discountType": dtype, "offerNo": offer, "managerOverride": override,
                        "infocodeReason": "DAMAGED" if (dtype == "ManualLine" and rng.random() < 0.3) else "",
                        "memberCardNo": f"M{rng.randint(10000, 99999)}" if dtype == "Member" else "",
                        "sourceSystem": "MOCK", "sourceEntryKey": f"{store}|{term}|{trans_no}|10000",
                    })
    return rows


def discount_exceptions_mirror(logs: list[dict]) -> list[dict]:
    manual = {"ManualLine", "ManualTotal", "PriceOverride"}
    out = []
    detected = (CALC_AT + timedelta(minutes=10)).isoformat()
    for r in logs:
        if r["discountType"] in manual and r["discountPct"] > MAX_MANUAL_PCT and not r["managerOverride"]:
            out.append({"id": str(uuid.uuid4()), "ruleCode": "DG-01", "severity": "High", "storeNo": r["storeNo"], "staffId": r["staffId"],
                        "transDate": r["transDate"], "transactionNo": r["transactionNo"], "posTerminalNo": r["posTerminalNo"], "itemNo": r["itemNo"],
                        "metricValue": r["discountPct"], "thresholdValue": MAX_MANUAL_PCT, "discountAmount": r["discountAmount"],
                        "occurrenceCount": 1,
                        "description": f"Manual discount {r['discountPct']:.0f}% trên item {r['itemNo']}, vượt mức {MAX_MANUAL_PCT:.0f}% mà không có manager override.",
                        "status": "Open", "detectedAt": detected, "referenceKey": r["sourceEntryKey"]})
    groups: dict[tuple[str, str, str], list[dict]] = {}
    for r in logs:
        groups.setdefault((r["storeNo"], r["staffId"], r["transDate"]), []).append(r)
    for (store, st, d), rows in groups.items():
        gross = sum(x["grossAmount"] for x in rows)
        mdisc = sum(x["discountAmount"] for x in rows if x["discountType"] in manual)
        mcount = sum(1 for x in rows if x["discountType"] in manual)
        share = round(mdisc / gross * 100, 2) if gross else 0
        base = {"storeNo": store, "staffId": st, "transDate": d, "transactionNo": 0, "posTerminalNo": "", "itemNo": "",
                "discountAmount": round(mdisc, 2), "occurrenceCount": mcount, "status": "Open", "detectedAt": detected,
                "referenceKey": f"{store}|{st}|{d}"}
        if share > SHARE_WARN_PCT:
            out.append({"id": str(uuid.uuid4()), "ruleCode": "DG-02", "severity": "Medium", "metricValue": share, "thresholdValue": SHARE_WARN_PCT,
                        "description": f"Tỷ trọng manual discount {share}% trên doanh số các dòng có discount, vượt {SHARE_WARN_PCT:.0f}%.", **base})
        if mcount > REPEAT_COUNT:
            out.append({"id": str(uuid.uuid4()), "ruleCode": "DG-03", "severity": "Medium", "metricValue": float(mcount), "thresholdValue": float(REPEAT_COUNT),
                        "description": f"{mcount} lần manual discount trong ngày, vượt mức {REPEAT_COUNT} lần.", **base})
    return out


# ---------------------------------------------------------------- ghi
def make_uc1_uc3(fixtures_dir: Path, demo_dir: Path = DEMO_DIR, ile: list[dict] | None = None,
                 items: dict[str, dict] | None = None) -> dict:
    """Fixtures UC1 (do chinh xac du bao) va UC3 (don mua, phieu nhan, scorecard), them ngay 14/09/2026.

    Tinh bang chinh ban doi chieu Python cua codeunit 70120 va 70121 tren cung du lieu voi BC: Item Ledger Entry cua bo
    demo, va ke hoach don mua sinh boi tools/supplier_demo.py (seed co dinh). Nen mock ra dung so BC ra. Don mua Cronus
    treo tu 2024 (HO106122) giu lai de kiem nhanh don treo."""
    from .forecast import ForecastThresholds, backtest_bc
    from .supplier import plan_to_lines, scorecard
    from supplier_demo import ke_hoach  # noqa: E402

    ile = ile if ile is not None else read_ile(demo_dir)
    items = dict(items if items is not None else read_items(demo_dir))
    health_path = fixtures_dir / "inventory_health_lines.json"
    cat = {}
    if health_path.exists():
        cat = {r["itemNo"]: r.get("itemCategoryCode") or "" for r in json.loads(health_path.read_text(encoding="utf-8"))}
    for no, it in items.items():
        it["item_category"] = cat.get(no, "")

    def dump(name: str, data) -> None:
        (fixtures_dir / name).write_text(json.dumps(data, ensure_ascii=False, indent=1, default=str), encoding="utf-8")

    # Lich su kien lay dung cau hinh da ap len BC (tools/ls_replen_setup.ngay_su_kien), trai ra tung ngay nhu LS luu.
    from ls_replen_setup import ngay_su_kien
    planned = []
    for ev in ngay_su_kien():
        d, den = date.fromisoformat(ev["startDate"]), date.fromisoformat(ev["endDate"])
        while d <= den:
            for ln in ev["lines"]:
                planned.append({"id": f"psd-{len(planned)}", "itemNo": ln["item"], "variantCode": "", "locationCode": ln["location"],
                                "date": d.isoformat(), "lineNo": 10000, "plannedDemand": ev["demand"],
                                "plannedDemandType": ev["type"], "plannedDemandEvent": ev["code"], "status": "Enabled"})
            d += timedelta(days=1)
    toi: list[dict] = []
    acc, daily = backtest_bc(ile, TODAY, ForecastThresholds(), [], items, planned, forward=toi)
    for i, r in enumerate(acc):
        r["id"] = f"fa-{i}"
    for i, r in enumerate(daily):
        r["id"] = f"fd-{i}"
    for i, r in enumerate(toi):
        r["id"] = f"lsfc-{i}"
    dump("forecast_accuracies.json", acc)
    dump("forecast_dailies.json", daily)
    dump("ls_forecast_entries.json", toi)
    dump("planned_sales_demands.json", planned)

    # CTKM chuan LS (Periodic Discount), dung cau hinh da ap len BC (tools/ls_replen_setup.chuong_trinh_km). Nhom gia cua
    # cua hang chep tu NWV01: moi cua hang co ALL, S0001 va S0002 co them FOOD.
    from ls_replen_setup import chuong_trinh_km
    names = {r["itemNo"]: r.get("itemDescription", "") for r in json.loads(health_path.read_text(encoding="utf-8"))} if health_path.exists() else {}
    ctkm, dong, ky = [], [], []
    for o in chuong_trinh_km():
        ctkm.append({"id": f"pd-{o['no']}", "no": o["no"], "description": o["description"], "status": "Enabled" if o["enabled"] else "Disabled",
                     "type": o["type"], "discountType": "Deal Price", "priceGroup": o["priceGroup"], "validationPeriodId": o["validationId"],
                     "startingDate": o["startDate"], "endingDate": o["endDate"], "discountPctValue": o["discountPct"],
                     "dealPriceValue": 0, "discountAmountValue": 0, "plannedDemandType": " ", "plannedDemand": 0})
        ky.append({"id": f"vp-{o['validationId']}", "validationId": o["validationId"], "description": o["description"],
                   "startingDate": o["startDate"], "endingDate": o["endDate"],
                   "startingTime": o.get("startTime", "00:00:00"), "endingTime": o.get("endTime", "00:00:00")})
        for i, ln in enumerate(o["lines"], 1):
            dong.append({"id": f"pdl-{o['no']}-{i}", "offerNo": o["no"], "lineNo": i * 10000, "type": "Item", "no": ln["item"],
                         "variantCode": "", "description": names.get(ln["item"], ln["item"]), "dealPriceDiscPct": ln["discPct"],
                         "offerPrice": 0, "standardPrice": 0, "exclude": False, "status": "Enabled" if o["enabled"] else "Disabled"})
    dump("ls_periodic_discounts.json", ctkm)
    dump("ls_periodic_discount_lines.json", dong)
    dump("ls_validation_periods.json", ky)
    stores = sorted({r["location_code"] for r in ile if str(r.get("location_code") or "").startswith("S")})
    dump("ls_store_price_groups.json", [{"id": f"spg-{s}-{g}", "store": s, "priceGroupCode": g, "priority": 0}
                                        for s in stores for g in (["ALL", "FOOD"] if s in ("S0001", "S0002") else ["ALL"])])
    dump("planned_events.json", [{"id": f"pe-{ev['code']}", "eventCode": ev["code"], "description": ev["description"],
                                  "startDate": ev["startDate"], "endDate": ev["endDate"], "status": "Enabled",
                                  "noOfLines": sum(1 for r in planned if r["plannedDemandEvent"] == ev["code"]),
                                  "sourceType": "Discount" if ev.get("offerNo") else "Manual", "sourceCode": ev.get("offerNo", "")}
                                 for ev in ngay_su_kien()])
    dump("nwv_items.json", [{"id": f"it-{no}", "itemNo": no, "description": names.get(no, ""), "itemCategoryCode": it.get("item_category", "")}
                            for no, it in sorted(items.items())])

    po, rc = plan_to_lines(ke_hoach())
    names = {r["itemNo"]: r.get("itemDescription", "") for r in json.loads(health_path.read_text(encoding="utf-8"))} if health_path.exists() else {}
    for r in po:
        r["description"] = names.get(r["itemNo"], "")
    po.append({"id": "po-106122-10000", "documentNo": "HO106122", "lineNo": 10000, "buyFromVendorNo": "44010", "itemNo": "40170",
               "variantCode": "", "description": "", "locationCode": "S0001", "quantity": 25, "outstandingQuantity": 25,
               "quantityReceived": 0, "unitOfMeasureCode": "PCS", "directUnitCost": 10, "orderDate": "2024-07-26",
               "expectedReceiptDate": "2024-08-01", "plannedReceiptDate": "2024-08-01"})
    dump("purchase_order_lines.json", po)
    dump("purchase_receipt_lines.json", rc)
    cards = scorecard(po, rc, TODAY, vendors={"44020": "AL-s Foods Ltd", "44030": "Dan-s Dairy Ltd"}, categories=cat)
    for i, r in enumerate(cards):
        r["id"] = f"sc-{i}"
    dump("supplier_scorecards.json", cards)
    return {"forecast_rows": len(acc), "po_lines": len(po), "receipts": len(rc), "scorecards": len(cards)}


def make_all(fixtures_dir: Path, demo_dir: Path = DEMO_DIR) -> dict:
    rng = random.Random(SEED)
    fixtures_dir.mkdir(parents=True, exist_ok=True)
    items = read_items(demo_dir)
    ile = read_ile(demo_dir)
    today = max(r["posting_date"] for r in ile)
    assert today == TODAY, f"ngay neo cua bo demo la {today}, ky vong {TODAY}"
    lines = inventory_health(ile, today, items, TH)
    sugg = replenishment(ile, today, WH, items, TH)
    logs = gen_pos_discounts(rng)

    with (fixtures_dir / "sales_history.csv").open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=["date", "item_no", "location_code", "qty"])
        w.writeheader()
        w.writerows(sales_rows(ile))

    def dump(name: str, data) -> None:
        (fixtures_dir / name).write_text(json.dumps(data, ensure_ascii=False, indent=1, default=str), encoding="utf-8")

    health = health_rows(lines)
    suggestions = suggestion_rows(sugg, lines, ile)
    dump("inventory_health_lines.json", health)
    dump("replenishment_suggestions.json", suggestions)
    dump("pos_discount_logs.json", logs)
    dump("discount_exceptions.json", discount_exceptions_mirror(logs))
    dump("agent_proposals.json", historical_proposals())
    them = make_uc1_uc3(fixtures_dir, demo_dir, ile, items)
    return {"today": today.isoformat(), "health": len(health), "suggestions": len(suggestions),
            "risky": sum(1 for s in suggestions if s["stockOutRisk"]), "pos": len(logs), **them}


if __name__ == "__main__":
    from .config import FIXTURES_DIR
    print(make_all(FIXTURES_DIR))
