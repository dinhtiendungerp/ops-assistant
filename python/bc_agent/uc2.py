"""Chay UC2 tren du lieu that va doi chieu voi ket qua tinh offline.

Vi sao can lop nay: `inventory.py` nhan Item Ledger Entry roi tra phan tang, nhung no khong biet
du lieu den tu dau. Cho nay noi no voi `bc_data.py` de chay duoc tren BC that, va cho ra dung mot
bo con so de so voi ket qua tinh offline tren chinh bo du lieu demo. Lech la co cho sai, thuong
o cach doc Quantity co dau hoac o cach xac dinh ngay het hang.

Doc toan bo Item Ledger Entry chu khong chi cua so lich su, vi ton kho theo lo la tong Quantity
co dau tu dong dau tien. Cat bot lich su thi ton kho sai.
"""
from __future__ import annotations

from collections import Counter
from datetime import date
from typing import Any

from .bc_data import BCData
from .inventory import (HealthLine, ReplenishmentSuggestion, Thresholds, inventory_health,
                        observed_shelf_life, replenishment)

TIERS = ["Expired", "NearExpiry", "StockOutRisk", "SlowMoving", "Excess", "Healthy"]

TIER_VI = {
    "Expired": "qua han",
    "NearExpiry": "can han",
    "StockOutRisk": "rui ro dut hang",
    "SlowMoving": "cham luan chuyen",
    "Excess": "ton thua",
    "Healthy": "binh thuong",
}


def fetch(data: BCData) -> tuple[list[dict[str, Any]], dict[str, dict]]:
    """Doc Item Ledger Entry va Item tu BC. Hai loi goc, khong loc gi."""
    ile = data.item_ledger_entries(newest_first=False)
    items = {r["item_no"]: r for r in data.items() if r.get("item_no")}
    return ile, items


def run(ile: list[dict[str, Any]], items: dict[str, dict], today: date,
        source_location: str = "W0003",
        th: Thresholds = Thresholds()) -> tuple[list[HealthLine], list[ReplenishmentSuggestion]]:
    lines = inventory_health(ile, today, items, th)
    sugg = replenishment(ile, today, source_location, items, th)
    return lines, sugg


def tier_counts(lines: list[HealthLine]) -> dict[str, int]:
    c = Counter(line.tier for line in lines)
    return {t: c.get(t, 0) for t in TIERS}


def tier_quantities(lines: list[HealthLine]) -> dict[str, float]:
    q: dict[str, float] = {t: 0.0 for t in TIERS}
    for line in lines:
        q[line.tier] = round(q.get(line.tier, 0.0) + line.quantity, 3)
    return q


def snapshot(lines: list[HealthLine], sugg: list[ReplenishmentSuggestion],
             today: date) -> dict[str, Any]:
    """Bo con so dung de doi chieu giua BC that va ket qua tinh offline."""
    return {
        "today": today.isoformat(),
        "so_dong": len(lines),
        "tier_counts": tier_counts(lines),
        "tier_quantities": tier_quantities(lines),
        "so_de_xuat_dieu_chuyen": len(sugg),
        "so_de_xuat_bi_chan_boi_han_dung": sum(1 for s in sugg if s.capped_by_shelf_life),
    }


def snapshot_from_al(health_rows: list[dict[str, Any]], sugg_rows: list[dict[str, Any]]) -> dict[str, Any]:
    """Cung bo con so nhu snapshot(), nhung lay tu bang ket qua do AL tinh, doc qua
    inventoryHealthLines va replenishmentSuggestions. Dung de so AL voi Python.

    tier tren API la ten enum: Expired, NearExpiry, StockOutRisk, SlowMoving, Excess, Healthy,
    trung voi TIERS. asOfDate la Work Date luc AL chay.
    """
    counts = {t: 0 for t in TIERS}
    qty = {t: 0.0 for t in TIERS}
    unknown: Counter = Counter()
    for r in health_rows:
        t = str(r.get("tier") or "")
        if t not in counts:
            unknown[t] += 1
            continue
        counts[t] += 1
        qty[t] = round(qty[t] + float(r.get("quantityOnHand") or 0), 3)
    risky = [s for s in sugg_rows if s.get("stockOutRisk")]
    as_of = sorted({str(r.get("asOfDate") or "")[:10] for r in health_rows} - {""})
    snap = {
        "today": as_of[-1] if as_of else None,
        "so_dong": len(health_rows),
        "tier_counts": counts,
        "tier_quantities": qty,
    }
    if sugg_rows:
        snap["so_de_xuat_dieu_chuyen"] = len(risky)
        snap["so_de_xuat_bi_chan_boi_han_dung"] = sum(1 for s in risky if s.get("cappedByShelfLife"))
    if unknown:
        snap["tier_la"] = dict(unknown)
    if len(as_of) > 1:
        snap["nhieu_ngay_neo"] = as_of
    return snap


def compare(actual: dict[str, Any], expected: dict[str, Any]) -> list[str]:
    """Tra ve danh sach cho lech. Rong tuc la trung."""
    diffs: list[str] = []

    for key in ("so_dong", "so_de_xuat_dieu_chuyen", "so_de_xuat_bi_chan_boi_han_dung"):
        a, e = actual.get(key), expected.get(key)
        # Tu 14/09/2026 BC khong con NWV Repl. Suggestion (UC1 dung LS Replenishment): AL khong co so de xuat de so.
        if key != "so_dong" and key not in actual:
            continue
        if e is not None and a != e:
            diffs.append(f"{key}: BC {a}, offline {e}")

    ac, ec = actual.get("tier_counts", {}), expected.get("tier_counts", {})
    for tier in TIERS:
        a, e = ac.get(tier, 0), ec.get(tier)
        if e is not None and a != e:
            diffs.append(f"{tier} ({TIER_VI[tier]}): BC {a}, offline {e}")

    aq, eq = actual.get("tier_quantities", {}), expected.get("tier_quantities", {})
    for tier in TIERS:
        a, e = aq.get(tier, 0.0), eq.get(tier)
        if e is not None and abs(float(a) - float(e)) > 0.001:
            diffs.append(f"{tier} so luong: BC {a}, offline {e}")

    if actual.get("today") != expected.get("today"):
        diffs.append(f"ngay neo: BC {actual.get('today')}, offline {expected.get('today')}")

    return diffs


def format_report(lines: list[HealthLine], sugg: list[ReplenishmentSuggestion],
                  ile: list[dict[str, Any]], today: date, top: int = 10) -> str:
    out: list[str] = []
    counts = tier_counts(lines)
    qty = tier_quantities(lines)

    out.append(f"UC2 Inventory Health, ngay neo {today.isoformat()}")
    out.append(f"{len(ile)} dong Item Ledger Entry, {len(lines)} to hop mat hang x dia diem x lo")
    out.append("")
    out.append(f"{'Phan tang':<18}{'So to hop':>10}{'So luong':>12}")
    for tier in TIERS:
        out.append(f"{TIER_VI[tier]:<18}{counts[tier]:>10}{qty[tier]:>12,.0f}")
    out.append("")

    out.append(f"De xuat dieu chuyen: {len(sugg)} dong, "
               f"{sum(1 for s in sugg if s.capped_by_shelf_life)} dong bi chan boi han dung")
    shelf = observed_shelf_life(ile)
    if shelf:
        out.append("Han dung do tu du lieu: " +
                   ", ".join(f"{k} {v} ngay" for k, v in sorted(shelf.items())))
    out.append("")

    out.append(f"{top} dong rui ro cao nhat:")
    out.append(f"{'Item':<8}{'Loc':<8}{'Lot':<20}{'Ton':>8}{'DoC':>7}{'Han':>6}  Phan tang / ly do")
    for line in lines[:top]:
        out.append(
            f"{line.item_no:<8}{line.location_code:<8}{(line.lot_no or '-'):<20}"
            f"{line.quantity:>8,.0f}"
            f"{(f'{line.days_of_cover:.1f}' if line.days_of_cover is not None else '-'):>7}"
            f"{(str(line.days_to_expiry) if line.days_to_expiry is not None else '-'):>6}"
            f"  {TIER_VI[line.tier]} / {line.risk_reason}"
        )
    return "\n".join(out)
