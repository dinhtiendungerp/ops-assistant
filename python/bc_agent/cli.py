"""CLI.

  python -m bc_agent.cli run inventory_health
  python -m bc_agent.cli run replenishment
  python -m bc_agent.cli run discount_governance
  python -m bc_agent.cli check-bc            # thu ket noi BC live, in so dong moi entity
  python -m bc_agent.cli uc2-reconcile       # so Inventory Health tren BC voi uc2-expected.json
  python -m bc_agent.cli uc1-reconcile       # so NWV Forecast Accuracy tren BC voi forecast.backtest_bc
  python -m bc_agent.cli uc3-reconcile       # so NWV Supplier Scorecard tren BC voi supplier.scorecard
  python -m bc_agent.cli forecast fixtures/sales_history.csv
  python -m bc_agent.cli make-fixtures       # sinh lai du lieu mau

Che do lay tu .env: BC_MODE=mock|live, LLM_MODE=scripted|live, LLM_PROVIDER=azure|anthropic
"""
from __future__ import annotations

import argparse
import json
import logging
import sys
from pathlib import Path

from .config import FIXTURES_DIR, settings
from .scenarios import SCENARIOS_BY_KEY

logging.basicConfig(level=logging.INFO, format="%(levelname)s %(name)s: %(message)s")
log = logging.getLogger("cli")

# Console Windows mac dinh cp1252, in tieng Viet co dau se vo giua chung. Ep utf-8.
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")


def build_client():
    if settings.bc_live:
        from .bc_client import BCClient
        return BCClient(settings)
    from .mock_client import MockBCClient
    return MockBCClient()


def build_llm(scenario_key: str):
    if settings.llm_mode == "live":
        from .llm import build_llm as _build
        llm = _build()
        return llm, f"{settings.llm_provider}:{llm.model}"
    from .runner import ScriptedLLM
    return ScriptedLLM(scenario_key, max_items=min(5, settings.max_proposals_per_run)), "scripted-policy"


def cmd_run(args: argparse.Namespace) -> int:
    from .runner import AgentRunner

    scenario = SCENARIOS_BY_KEY[args.scenario]
    client = build_client()
    llm, model_name = build_llm(scenario.key)
    log.info("Scenario: %s | BC=%s | LLM=%s", scenario.title, settings.bc_mode, model_name)
    result = AgentRunner(client, llm, model_name).run(scenario.key, scenario.system, scenario.task, scenario.tools)
    print("\n=== KET QUA ===")
    print(result.final_text)
    print(f"\nrun_id={result.run_id} tool_calls={result.tool_calls} proposals_created={result.proposals_created}")
    print(f"log: {result.log_path}")
    if hasattr(client, "save"):
        p = client.save(settings.log_dir / result.run_id)
        print(f"mock state: {p}")
    return 0


def cmd_check_bc(args: argparse.Namespace) -> int:
    """Kiem ket noi S2S va do phu du lieu. Cung mot duong voi `python -m bc_agent.probe`."""
    from .probe import probe

    report = probe(sample=args.sample)
    return 0 if report.get("ok") else 1


def _load_uc2(args: argparse.Namespace):
    from datetime import date

    from .bc_data import BCData
    from .uc2 import fetch, run

    data = BCData(settings)
    ile, items = fetch(data)
    if not ile:
        raise SystemExit("Item Ledger Entry rong. Chua import du lieu demo thi khong co gi de chay.")

    if args.today:
        today = date.fromisoformat(args.today)
    else:
        today = max(date.fromisoformat(str(r["posting_date"])[:10])
                    for r in ile if r.get("posting_date"))
    lines, sugg = run(ile, items, today, source_location=args.source_location)
    return ile, items, lines, sugg, today


def cmd_uc2(args: argparse.Namespace) -> int:
    from .uc2 import format_report, snapshot

    ile, _items, lines, sugg, today = _load_uc2(args)
    print(format_report(lines, sugg, ile, today, top=args.top))
    if args.json:
        out = Path(args.json)
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(json.dumps(snapshot(lines, sugg, today), ensure_ascii=False, indent=2),
                       encoding="utf-8")
        print(f"\nsnapshot: {out}")
    return 0


def _snapshot_from_al():
    """Doc bang ket qua do AL tinh (NWV Inv. Health Line, NWV Repl. Suggestion) qua API
    inventoryHealthLines va replenishmentSuggestions cua app NWV Marou Agent."""
    from .bc_client import BCClient
    from .uc2 import snapshot_from_al

    client = BCClient(settings)
    health = client.list("inventoryHealthLines")
    # NWV Repl. Suggestion da xoa khoi app 1.2.0.0; de xuat bo sung do LS Replenishment tinh, khong so o day.
    sugg: list = []
    if not health:
        raise SystemExit("inventoryHealthLines rong. Chay Run Inventory Health tren page NWV Agent Setup truoc.")
    return snapshot_from_al(health, sugg)


def cmd_uc2_reconcile(args: argparse.Namespace) -> int:
    """So ket qua voi ket qua tinh offline tren chinh bo du lieu demo.

    --from python : doc Item Ledger Entry roi tu tinh bang inventory.py (mac dinh)
    --from al     : doc bang ket qua do AL trong BC da tinh, day la duong chay chinh
    """
    from .uc2 import TIER_VI, TIERS, compare, snapshot

    expected = json.loads(Path(args.expected).read_text(encoding="utf-8"))
    if args.source == "al":
        actual = _snapshot_from_al()
        label = "AL"
    else:
        _ile, _items, lines, sugg, today = _load_uc2(args)
        actual = snapshot(lines, sugg, today)
        label = "Python"
    if actual.get("tier_la"):
        print(f"tier khong nhan ra tren API: {actual['tier_la']}")
    if actual.get("nhieu_ngay_neo"):
        print(f"bang ket qua co nhieu ngay neo: {actual['nhieu_ngay_neo']}")

    print(f"{'Phan tang':<18}{label:>8}{'Offline':>10}")
    for tier in TIERS:
        print(f"{TIER_VI[tier]:<18}{actual['tier_counts'][tier]:>8}"
              f"{expected.get('tier_counts', {}).get(tier, '-'):>10}")
    print(f"{'de xuat dieu chuyen':<18}{actual['so_de_xuat_dieu_chuyen']:>8}"
          f"{expected.get('so_de_xuat_dieu_chuyen', '-'):>10}")

    diffs = compare(actual, expected)
    if not diffs:
        print("\nTrung khop hoan toan.")
        return 0
    print(f"\n{len(diffs)} cho lech:")
    for d in diffs:
        print(f"  {d}")
    return 1


def _in_lech(ten: str, so_al: int, so_py: int, lech: list[str]) -> int:
    print(f"{ten}: AL {so_al} dong, Python {so_py} dong")
    if not lech:
        print("Trung khop hoan toan.")
        return 0
    print(f"{len(lech)} cho lech:")
    for d in lech[:40]:
        print(f"  {d}")
    return 1


def _so_sanh(al: dict, py: dict, truong: tuple[str, ...], dung_sai: float) -> list[str]:
    lech = [f"chi co ben AL: {k}" for k in al if k not in py] + [f"chi co ben Python: {k}" for k in py if k not in al]
    for k in al.keys() & py.keys():
        for f in truong:
            a, b = al[k].get(f), py[k].get(f)
            if isinstance(a, (int, float)) and isinstance(b, (int, float)) and not isinstance(a, bool):
                if abs(float(a) - float(b)) > dung_sai:
                    lech.append(f"{k} {f}: AL {a} / Python {b}")
            elif (a or "") != (b or ""):
                lech.append(f"{k} {f}: AL {a!r} / Python {b!r}")
    return sorted(lech)


def cmd_uc1_reconcile(args: argparse.Namespace) -> int:
    """Doc bang NWV Forecast Accuracy do codeunit 70120 tinh, roi tinh lai bang forecast.backtest_bc tren Item Ledger Entry
    that. Nguong mac dinh trung gia tri mac dinh cua NWV Agent Setup; Marou sua nguong thi phai truyen lai o day."""
    from datetime import date, timedelta

    from .bc_client import BCClient
    from .forecast import ForecastThresholds, backtest_bc
    from .uc2 import fetch
    from .bc_data import BCData

    client = BCClient(settings)
    al = client.list("forecastAccuracies")
    if not al:
        raise SystemExit("forecastAccuracies rong. Bam Run Forecast Accuracy tren NWV Agent Setup truoc.")
    as_of = date.fromisoformat(max(str(r["holdoutTo"])[:10] for r in al))
    ile, items = fetch(BCData(settings))
    exc = client.list("demandExceptions")
    planned = client.list("plannedSalesDemands")
    th = ForecastThresholds(holdout_days=args.holdout, central_warehouse=args.central_warehouse, horizon_days=args.horizon)
    toi: list[dict] = []
    py, _daily = backtest_bc(ile, as_of, th, exc, items, planned, forward=toi)
    khoa = lambda r: (r["itemNo"], r["locationCode"], r["method"])  # noqa: E731
    lech = _so_sanh({khoa(r): r for r in al}, {khoa(r): r for r in py},
                    ("actualQty", "forecastQty", "wapePct", "biasPct", "daysEvaluated", "daysCensored", "daysExcluded",
                     "isException", "modelParameters"), args.tol)
    print(f"Ky kiem tra ket thuc {as_of}, dung sai so {args.tol}, {len(planned)} dong Planned Sales Demand")
    kq = _in_lech("NWV Forecast Accuracy", len(al), len(py), lech)
    # Du bao cac ngay toi trong LSC Forecast Entry: chi so cac cap ban do (bang LS co the co dong Cronus khac).
    cap = {(r["itemNo"], r["locationCode"]) for r in py}
    tu = (as_of + timedelta(days=1)).isoformat()
    ls = [r for r in client.list("lsForecastEntries") if (r["itemNo"], r["locationCode"]) in cap and str(r["date"])[:10] >= tu]
    khoa_ngay = lambda r: (r["itemNo"], r["locationCode"], str(r["date"])[:10])  # noqa: E731
    lech2 = _so_sanh({khoa_ngay(r): r for r in ls}, {khoa_ngay(r): r for r in toi},
                     ("forecastQuantity", "forecastQuantityLower", "forecastQuantityUpper", "forecastQualityPct"), max(args.tol, 0.02))
    return max(kq, _in_lech("LSC Forecast Entry (du bao ngay toi)", len(ls), len(toi), lech2))


def cmd_uc3_reconcile(args: argparse.Namespace) -> int:
    """Doc bang NWV Supplier Scorecard do codeunit 70121 tinh, roi tinh lai bang supplier.scorecard tren Purchase Line va
    Purch. Rcpt. Line that. Ngay neo lay tu truong asOfDate cua bang ket qua."""
    from datetime import date

    from .bc_client import BCClient
    from .supplier import SupplierThresholds, scorecard

    client = BCClient(settings)
    al = client.list("supplierScorecards")
    if not al:
        raise SystemExit("supplierScorecards rong. Bam Run Supplier Scorecard tren NWV Agent Setup truoc.")
    ngay = [str(r.get("asOfDate") or "")[:10] for r in al if r.get("asOfDate")]
    as_of = date.fromisoformat(args.as_of or (max(ngay) if ngay else "2026-09-18"))
    po = client.list("nwvPurchaseOrderLines")
    rc = client.list("nwvPurchaseReceiptLines")
    # Nhom hang phai doc tu Item: ma nao thieu nhom se roi vao dong nhom rong, trung khoa voi dong tong cua nha cung cap.
    cat = {r["itemNo"]: r.get("itemCategoryCode") or "" for r in client.list("nwvItems")}
    vendors = {r["vendorNo"]: r.get("vendorName") or "" for r in al}
    th = SupplierThresholds(tolerance_days=args.tolerance_days, on_time_warn=args.on_time_warn, history_days=args.history_days)
    py = scorecard(po, rc, as_of, th, vendors, cat)
    khoa = lambda r: (r["vendorNo"], r.get("itemCategoryCode") or "")  # noqa: E731
    truong = tuple(k for k in py[0] if k not in ("id", "vendorName")) if py else ()
    lech = _so_sanh({khoa(r): r for r in al}, {khoa(r): r for r in py}, truong, args.tol)
    print(f"Ngay neo {as_of}, lich su {th.history_days} ngay, dung sai so {args.tol}")
    return _in_lech("NWV Supplier Scorecard", len(al), len(py), lech)


def cmd_forecast(args: argparse.Namespace) -> int:
    from .forecast import backtest, load_sales, summarize, write_report

    series = load_sales(Path(args.csv))
    results = backtest(series, holdout_days=args.holdout)
    out = Path(args.out)
    write_report(results, out)
    summary = summarize(results)
    print(f"Series: {len(series)} | ket qua: {len(results)} dong -> {out}")
    for m, w in summary.items():
        print(f"  {m:5s} WAPE gop tren holdout {args.holdout} ngay = {w:.1%}")
    print("Baseline = mo hinh co WAPE thap hon. Mo hinh AI sau nay phai thang so nay tren cung holdout.")
    return 0


def cmd_make_fixtures(args: argparse.Namespace) -> int:
    from .make_fixtures import make_all
    make_all(FIXTURES_DIR)
    print(f"Da sinh fixtures vao {FIXTURES_DIR}")
    return 0


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(prog="bc_agent")
    sub = p.add_subparsers(dest="cmd", required=True)

    r = sub.add_parser("run", help="chay mot kich ban agent")
    r.add_argument("scenario", choices=list(SCENARIOS_BY_KEY))
    r.set_defaults(fn=cmd_run)

    c = sub.add_parser("check-bc", help="kiem tra ket noi S2S va do phu du lieu")
    c.add_argument("--sample", type=int, default=2000)
    c.set_defaults(fn=cmd_check_bc)

    def add_uc2_args(p_):
        p_.add_argument("--today", help="ngay neo, mac dinh la Posting Date moi nhat trong du lieu")
        p_.add_argument("--source-location", default="W0003", help="kho nguon cho de xuat dieu chuyen")

    u = sub.add_parser("uc2", help="chay UC2 tren du lieu that doc qua custom API page")
    add_uc2_args(u)
    u.add_argument("--top", type=int, default=10)
    u.add_argument("--json", help="ghi snapshot ra file de doi chieu ve sau")
    u.set_defaults(fn=cmd_uc2)

    rc = sub.add_parser("uc2-reconcile", help="so ket qua tren BC voi ket qua tinh offline")
    add_uc2_args(rc)
    rc.add_argument("--expected", default="../demo-data-nwv/uc2-expected.json")
    rc.add_argument("--from", dest="source", choices=["python", "al"], default="al",
                    help="al: doc bang ket qua AL da tinh (mac dinh); python: tu tinh tu Item Ledger Entry")
    rc.set_defaults(fn=cmd_uc2_reconcile)

    u1 = sub.add_parser("uc1-reconcile", help="so bang do chinh xac du bao tren BC voi ban Python")
    u1.add_argument("--holdout", type=int, default=28)
    u1.add_argument("--central-warehouse", default="W0003")
    u1.add_argument("--horizon", type=int, default=28)
    u1.add_argument("--tol", type=float, default=0.15, help="dung sai so, mac dinh 0,15 cho lam tron 0,1")
    u1.set_defaults(fn=cmd_uc1_reconcile)

    u3 = sub.add_parser("uc3-reconcile", help="so scorecard nha cung cap tren BC voi ban Python")
    u3.add_argument("--as-of", help="ngay neo, mac dinh lay asOfDate cua bang ket qua")
    u3.add_argument("--tolerance-days", type=int, default=0)
    u3.add_argument("--on-time-warn", type=float, default=80.0)
    u3.add_argument("--history-days", type=int, default=180)
    u3.add_argument("--tol", type=float, default=0.15)
    u3.set_defaults(fn=cmd_uc3_reconcile)

    f = sub.add_parser("forecast", help="chay baseline forecast + backtest")
    f.add_argument("csv")
    f.add_argument("--holdout", type=int, default=28)
    f.add_argument("--out", default="runs/forecast_backtest.csv")
    f.set_defaults(fn=cmd_forecast)

    m = sub.add_parser("make-fixtures", help="sinh lai du lieu mau")
    m.set_defaults(fn=cmd_make_fixtures)

    args = p.parse_args(argv)
    return args.fn(args)


if __name__ == "__main__":
    sys.exit(main())
