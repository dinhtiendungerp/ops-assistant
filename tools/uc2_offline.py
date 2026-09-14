"""Chay UC2 offline tren chinh bo du lieu sap import, sinh file ket qua de doi chieu.

Bo du lieu la bay file Item Journal. Sau khi post, moi dong journal thanh mot dong Item Ledger
Entry, nen chay lop tinh toan tren journal cho ra dung con so ma BC se cho ra. Ket qua ghi vao
demo-data-nwv/uc2-expected.json roi dung lam moc cho:

    cd python
    python -m bc_agent.cli uc2-reconcile

Ngay neo lay tu chinh du lieu: Posting Date moi nhat. Giong het cach lenh uc2 lam, de hai ben
khong lech nhau chi vi ngay.

Chay:
    python tools/uc2_offline.py
    python tools/uc2_offline.py --out demo-data-nwv/uc2-expected.json
"""
from __future__ import annotations

import argparse
import json
import sys
from datetime import date, datetime
from pathlib import Path

# Console Windows mac dinh cp1252, ly do phan tang gio co dau. Ep utf-8.
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "python"))

from bc_agent.demo_data import DEMO_DIR as DEMO, read_ile, read_items  # noqa: E402  cung bo doc voi make_fixtures
from bc_agent.inventory import Thresholds  # noqa: E402
from bc_agent.uc2 import format_report, run, snapshot  # noqa: E402


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default=str(DEMO / "uc2-expected.json"))
    ap.add_argument("--today", help="ngay neo, mac dinh la Posting Date moi nhat")
    ap.add_argument("--source-location", default="W0003")
    ap.add_argument("--top", type=int, default=10)
    args = ap.parse_args()

    items = read_items()
    ile = read_ile()
    today = date.fromisoformat(args.today) if args.today else max(r["posting_date"] for r in ile)

    lines, sugg = run(ile, items, today, source_location=args.source_location, th=Thresholds())
    print(format_report(lines, sugg, ile, today, top=args.top))

    out = Path(args.out)
    out.write_text(json.dumps(snapshot(lines, sugg, today), ensure_ascii=False, indent=2),
                   encoding="utf-8")
    print(f"\nda ghi: {out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
