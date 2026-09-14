"""Probe: kiem duong S2S va do san sang du lieu UC2 tren BC that.

Chay:
    python -m bc_agent.probe
    python -m bc_agent.probe --json --sample 2000
    BC_SOURCE=odata python -m bc_agent.probe      # duong du phong khi chua publish extension

Kiem theo dung thu tu de biet hong o dau:
  1. Token S2S lay duoc chua.
  2. Company tim thay chua.
  3. Tung entity set doc duoc chua. O che do api, entity set nao loi tuc la extension
     NWV Marou Data API chua publish hoac permission set chua gan cho Entra app.
  4. Do phu du lieu tren mau Item Ledger Entry that: bao nhieu phan tram co Lot No.,
     co Expiration Date, co Location Code, va lich su dai toi dau.
  5. Do day cua master data phuc vu bo sung hang: Item Tracking Code, Reorder Point,
     Safety Stock Quantity, va co dung Stockkeeping Unit khong.

Bao cao con so that ke ca khi xau. Do phu du lieu la KET QUA cua POC, khong phai dieu kien
de POC duoc coi la thanh cong.
"""
from __future__ import annotations

import argparse
import json
import sys
from datetime import date
from typing import Any

from .bc_data import (ES_CATEGORY, ES_ILE, ES_ITEM, ES_LOCATION, ES_LOT, ES_PO_LINE,
                      ES_SKU, ES_SO_LINE, ES_VALUE_ENTRY, BCData)
from .config import settings

_EMPTY = {"", "0001-01-01", "0001-01-01T00:00:00Z", "None", "0"}


def pct(part: int, total: int) -> str:
    return "n/a" if total == 0 else f"{100.0 * part / total:.1f}%"


def filled(v: Any) -> bool:
    return str(v if v is not None else "").strip() not in _EMPTY


def _count(rows: list[dict], key: str) -> int:
    return sum(1 for r in rows if filled(r.get(key)))


def probe(sample: int) -> dict[str, Any]:
    report: dict[str, Any] = {"ok": False, "source": None, "steps": []}

    def step(name: str, status: str, detail: Any = None) -> None:
        report["steps"].append({"step": name, "status": status, "detail": detail})
        mark = {"ok": "  OK ", "warn": " WARN", "fail": " FAIL"}.get(status, "     ")
        print(f"[{mark}] {name}" + (f": {detail}" if detail is not None else ""))

    try:
        data = BCData(settings)
    except Exception as exc:  # noqa: BLE001
        step("Khoi tao client", "fail", str(exc))
        return report

    report["source"] = data.source
    client = data.api if data.source == "api" else data.ws

    try:
        client.auth.token()
        company = getattr(client, "company_id", None) or getattr(client, "company", "")
        step("Token S2S", "ok", f"source={data.source} environment={settings.bc_environment} company={company}")
    except Exception as exc:  # noqa: BLE001
        step("Token S2S", "fail", str(exc))
        return report

    # --- tung entity set doc duoc chua ---
    checks = [
        ("Item", lambda: data.items(top=sample)),
        ("Location", lambda: data.locations(top=200)),
        ("Item Category", lambda: data.item_categories(top=200)),
        ("Lot No. Information", lambda: data.lots(top=sample)),
        ("Stockkeeping Unit", lambda: data.stockkeeping_units(top=sample)),
        ("Purchase Order Line", lambda: data.purchase_order_lines(top=sample)),
        ("Sales Order Line", lambda: data.sales_order_lines(top=sample)),
        ("Value Entry", lambda: data.value_entries(top=200)),
    ]
    got: dict[str, list[dict]] = {}
    for name, fn in checks:
        try:
            rows = fn()
            got[name] = rows
            step(f"Doc {name}", "ok" if rows else "warn", f"{len(rows)} dong")
        except Exception as exc:  # noqa: BLE001
            got[name] = []
            step(f"Doc {name}", "fail", str(exc)[:300])
    report["row_counts"] = {k: len(v) for k, v in got.items()}

    # --- Item Ledger Entry, nguon chinh cua UC2 ---
    try:
        rows = data.item_ledger_entries(top=sample)
        step("Doc Item Ledger Entry", "ok", f"{len(rows)} dong mau")
    except Exception as exc:  # noqa: BLE001
        step("Doc Item Ledger Entry", "fail", str(exc)[:300])
        return report

    total = len(rows)
    dates = sorted(str(r["posting_date"])[:10] for r in rows if filled(r.get("posting_date")))
    coverage = {
        "so_dong_mau": total,
        "co_lot_no": f"{_count(rows, 'lot_no')}/{total} ({pct(_count(rows, 'lot_no'), total)})",
        "co_expiration_date": f"{_count(rows, 'expiration_date')}/{total} "
                              f"({pct(_count(rows, 'expiration_date'), total)})",
        "co_location_code": f"{_count(rows, 'location_code')}/{total} "
                            f"({pct(_count(rows, 'location_code'), total)})",
        "posting_date_cu_nhat": dates[0] if dates else None,
        "posting_date_moi_nhat": dates[-1] if dates else None,
        "so_location_xuat_hien": len({r.get("location_code") for r in rows if filled(r.get("location_code"))}),
        "so_item_xuat_hien": len({r.get("item_no") for r in rows if filled(r.get("item_no"))}),
    }
    step("Do phu du lieu UC2", "ok", json.dumps(coverage, ensure_ascii=False))
    report["coverage"] = coverage
    report["sample_ile_row"] = rows[0] if rows else None

    # --- do day master data cho bo sung hang ---
    items = got.get("Item", [])
    skus = got.get("Stockkeeping Unit", [])
    if items:
        master = {
            "so_item": len(items),
            "co_item_category": pct(_count(items, "item_category"), len(items)),
            "co_item_tracking_code": pct(_count(items, "item_tracking_code"), len(items)),
            "co_reorder_point": pct(_count(items, "reorder_point"), len(items)),
            "co_safety_stock": pct(_count(items, "safety_stock"), len(items)),
            "so_stockkeeping_unit": len(skus),
        }
        weak = [k for k in ("co_item_tracking_code", "co_reorder_point") if master[k] in ("0.0%", "n/a")]
        step("Do day master data", "ok" if not weak else "warn",
             json.dumps(master, ensure_ascii=False) + (f" | YEU: {weak}" if weak else ""))
        report["master_data"] = master

    report["ok"] = True
    return report


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description="Kiem S2S va do san sang du lieu UC2")
    p.add_argument("--sample", type=int, default=1000, help="So dong lay mau moi entity set")
    p.add_argument("--json", dest="as_json", action="store_true", help="In bao cao dang JSON")
    args = p.parse_args(argv)

    print(f"Probe Business Central, {date.today().isoformat()}")
    rep = probe(args.sample)
    if args.as_json:
        print(json.dumps(rep, ensure_ascii=False, indent=2, default=str))
    return 0 if rep.get("ok") else 1


if __name__ == "__main__":
    sys.exit(main())
