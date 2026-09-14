"""Post lai du lieu kho demo tren NWV01 qua S2S, thay cho bay buoc bam tay.

    cd python
    python ../tools/repost_demo.py preview
    python ../tools/repost_demo.py reset        # XOA ledger kho (ILE, Value Entry, Item Application Entry ...)
    python ../tools/repost_demo.py master       # gan LOTALLEXP cho TRACKED, xoa variant Cronus 30091 33150
    python ../tools/repost_demo.py import       # chuan bi batch, chen 24.759 dong tu import-full-journal.txt
    python ../tools/repost_demo.py post         # post theo tung thang, khoa lo demo
    python ../tools/repost_demo.py calc         # lop AL (Work Date 18/09/2026), roi LS Replenishment

Moi buoc dung lai khi BC bao loi. Web service nam trong app NWV Marou Demo Setup (NWVDemoRepost) va
NWV Marou Agent (NWVAgentCalcService).
"""
from __future__ import annotations

import calendar
import csv
import json
import subprocess
import sys
import time
from datetime import date, datetime
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(ROOT / "python"))

import demo_scenario as ds  # noqa: E402
import tools_bc as t  # noqa: E402

FILE = ROOT / "demo-data-nwv" / "import-full-journal.txt"
WORK_DATE = "2026-09-18"
VARIANT_ITEMS = ["30091", "33150"]
CHUNK = 1000


def ws(fn: str, body: dict, service: str = "NWVDemoRepost"):
    t0 = time.time()
    kq = t.ws(fn, body, service=service)
    print(f"  {fn} {time.time() - t0:.0f}s: {json.dumps(kq, ensure_ascii=False)[:600]}")
    return kq


def _d(s: str) -> str:
    return datetime.strptime(s, "%m/%d/%y").date().isoformat() if s else ""


def doc_file() -> list[dict]:
    rows = list(csv.reader(FILE.open(encoding="utf-8-sig"), delimiter="\t"))[2:]
    out = []
    for r in rows:
        out.append({"line": int(r[2]), "item": r[3], "date": _d(r[4]), "type": r[5], "doc": r[6], "loc": r[7],
                    "qty": float(r[8]), "unitAmount": float(r[9] or 0), "unitCost": float(r[10] or 0),
                    "amount": float(r[11] or 0), "discount": float(r[12] or 0), "exp": _d(r[13]), "lot": r[14]})
    return out


def main(cmd: str) -> None:
    if cmd == "preview":
        ws("Preview", {})
    elif cmd == "reset":
        ws("ResetInventoryLedger", {"confirmText": "XOA-LEDGER-KHO-NWV"})
    elif cmd == "master":
        ws("AssignTracking", {"itemsCsv": ",".join(sorted(ds.TRACKED)), "trackingCode": "LOTALLEXP"})
        ws("DeleteVariants", {"itemsCsv": ",".join(VARIANT_ITEMS)})
        subprocess.run([sys.executable, str(HERE / "ls_replen_setup.py"), "preflight"], check=False)
    elif cmd == "import":
        ws("Prepare", {})
        lines = doc_file()
        print(f"  file: {len(lines)} dong")
        for i in range(0, len(lines), CHUNK):
            kq = ws("ImportLines", {"linesJson": json.dumps(lines[i:i + CHUNK])})
            if kq["imported"] != len(lines[i:i + CHUNK]):
                raise SystemExit("so dong chen khong khop")
    elif cmd == "post":
        lines = doc_file()
        dau = min(date.fromisoformat(l["date"]) for l in lines).replace(day=1)
        cuoi = max(date.fromisoformat(l["date"]) for l in lines)
        m = dau
        while m <= cuoi:
            het = m.replace(day=calendar.monthrange(m.year, m.month)[1])
            # nua thang mot dot cho giao dich khong qua lon trong mot lan goi web service
            for tu, den in ((m, m.replace(day=15)), (m.replace(day=16), het)):
                ws("PostRange", {"fromText": tu.isoformat(), "toText": den.isoformat()})
            m = date(m.year + (m.month == 12), m.month % 12 + 1, 1)
        ws("BlockDemoLot", {})
    elif cmd == "calc":
        # UC1 dung LS Replenishment (Dung chot 13/09/2026), nen khong chay NWV Replenishment Calc nua.
        for param in ("INVHEALTH", "DISCGOV"):
            ws("RunCalculations", {"param": param, "workDateText": WORK_DATE}, service="NWVAgentCalcService")
        for sub in (["apply", "--reset-oos"], ["calc"]):
            subprocess.run([sys.executable, str(HERE / "ls_replen_setup.py"), *sub], check=True)
    else:
        raise SystemExit(__doc__)


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else "")
