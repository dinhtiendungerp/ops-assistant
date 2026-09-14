"""Dien Lot No. vao file Table data for Item Ledger Entry xuat tu BC.

Vi sao can file nay. Lan import dau tien vao company NWV (12/09/2026) mat toan bo Lot No.:
Config Package do Lot No. vao field 6501 cua Item Journal Line, nhung
`ItemJournalLine.CheckItemTracking()` goi `ClearTracking()` khi batch khong bat
"Item Tracking on Lines", nen truong do bi xoa truoc khi post. Expiration Date thi song
vi no di qua field 6506 "Item Expiration Date", field do khong co OnValidate goi
CheckItemTracking. Ket qua: ILE co han dung ma khong co so lo.

App `NWV Marou Demo Setup` 1.0.1.0 da bat co do khi tao batch, nen lan import sau khong
lap lai loi nay. File nay la duong sua nhanh cho bo du lieu da post roi.

Cach ghep: moi dong Item Journal sau khi post thanh dung mot dong Item Ledger Entry. Ghep theo
khoa (Item No., Location Code, Posting Date, Entry Type, Quantity co dau, Expiration Date), roi
trong moi nhom gan lo theo dung thu tu xuat hien trong bay file journal.

Chay:
    python tools/fill_ile_lots.py "C:/.../Table data for Item Ledger Entry (1).txt"
    python tools/fill_ile_lots.py <file vao> --out <file ra>
"""
from __future__ import annotations

import argparse
import sys
from collections import defaultdict
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "python"))
sys.path.insert(0, str(ROOT / "tools"))

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

from bc_agent.demo_data import read_ile  # noqa: E402
from demo_scenario import TRACKED  # noqa: E402

COL_ENTRY, COL_ITEM, COL_DATE, COL_TYPE, COL_DOC, COL_LOC, COL_QTY, COL_LOT, COL_EXP = range(9)


def parse_us_date(s: str) -> date | None:
    """BC xuat ngay kieu MM/DD/YY. Nam hai chu so: 26 la 2026."""
    s = (s or "").strip()
    if not s:
        return None
    m, d, y = s.split("/")
    year = int(y)
    if year < 100:
        year += 2000
    return date(year, int(m), int(d))


def fmt_us_date(d: date | None) -> str:
    return "" if not d else f"{d.month:02d}/{d.day:02d}/{d.year % 100:02d}"


def key_of(item_no: str, loc: str, posting: date | None, entry_type: str,
           qty: float, exp: date | None) -> tuple:
    return (item_no, loc, posting, entry_type, round(qty, 3), exp)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("infile")
    ap.add_argument("--out", help="mac dinh la <file vao>-lot.txt canh file goc")
    args = ap.parse_args()

    src = Path(args.infile)
    out = Path(args.out) if args.out else src.with_name(src.stem + "-lot" + src.suffix)

    # ---- ben journal: chi mat hang co Item Tracking Code moi co lo
    journal = defaultdict(list)
    so_dong_co_lo = 0
    for r in read_ile():
        if not r["lot_no"]:
            continue
        so_dong_co_lo += 1
        journal[key_of(r["item_no"], r["location_code"], r["posting_date"],
                       r["entry_type"], r["quantity"], r["expiration_date"])].append(r["lot_no"])
    print(f"Journal: {so_dong_co_lo} dong co Lot No., {len(journal)} to hop khoa")

    lines = src.read_text(encoding="utf-8-sig").splitlines()
    if not lines[0].startswith("TABLEID:"):
        sys.exit("Dong dau khong phai TABLEID, kiem lai file xuat tu BC")
    head, hdr = lines[0], lines[1]
    cols = hdr.split("\t")
    if len(cols) != 9 or "Lot No." not in cols[COL_LOT]:
        sys.exit(f"Cot khong dung thu tu mong doi: {cols}")

    used = defaultdict(int)
    filled = missing = skipped_untracked = 0
    khong_ghep = defaultdict(int)
    body = []
    for ln in lines[2:]:
        if not ln.strip():
            continue
        f = ln.split("\t")
        item_no = f[COL_ITEM].strip()
        if item_no not in TRACKED:
            skipped_untracked += 1
            body.append(ln)
            continue
        k = key_of(item_no, f[COL_LOC].strip(), parse_us_date(f[COL_DATE]),
                   f[COL_TYPE].strip(), float(f[COL_QTY]), parse_us_date(f[COL_EXP]))
        lots = journal.get(k, [])
        i = used[k]
        if i < len(lots):
            f[COL_LOT] = lots[i]
            used[k] = i + 1
            filled += 1
        else:
            missing += 1
            khong_ghep[k[:4]] += 1
        body.append("\t".join(f))

    print(f"ILE: dien {filled} dong, khong ghep duoc {missing}, bo qua {skipped_untracked} dong "
          f"cua mat hang khong co tracking code")
    if khong_ghep:
        print("Khoa khong ghep duoc (toi da 10):")
        for k, n in list(sorted(khong_ghep.items(), key=lambda kv: -kv[1]))[:10]:
            print(f"   {k}  x{n}")
    du = sum(len(v) - used[k] for k, v in journal.items())
    if du:
        print(f"Con {du} lo trong journal khong tim thay dong ILE tuong ung")

    out.write_text("\n".join([head, hdr, *body]) + "\n", encoding="utf-8")
    print(f"\nDa ghi: {out}")
    return 0 if missing == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
