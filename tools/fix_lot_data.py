"""Hai file sua du lieu lo sau khi da post: han dung tren ILE, va bang Lot No. Information.

Vi sao can. File journal `demo-data-nwv/import-full-journal.txt` chi ghi Expiration Date tren
DONG NHAP. Khi post, BC chep han dung sang Item Ledger Entry cua dong nhap, con dong xuat
(Negative Adjmt., Sale, Transfer) thi de trong, vi han dung cua dong xuat duoc suy tu dong nhap
ma no ap vao chu khong nhap tay. Nhin vao ILE thi 3.259 dong co so lo ma khong co han dung.

Chuyen do KHONG lam sai mot con so nao cua UC2. `bc_agent/inventory.py` lay han dung cua mot lo
tu BAT KY dong nao cua lo do co han dung (`if e and lot`), va dong nhap thi luon co. Day la viec
lam cho du lieu nhin dung, khong phai sua loi tinh toan.

Con `Lot No. Information` thi BC chi tu sinh khi Item Tracking Code bat co tao thong tin lo luc
post. Trong NWV hien chi co 40 dong, deu cua 33310, trong khi bo du lieu co 876 lo. Bang do la
cho nguoi van hanh tra "lo nay la lo gi", va la cho bam nut Block lo demo, nen phai co du.
Luu y: bang 6505 KHONG co truong Expiration Date (da doc trong source base app), nen han dung
duoc ghi vao Description de nguoi doc van thay.

Chay:
    python tools/fix_lot_data.py "C:/.../Table data for UPDATE.txt"

Sinh ra hai file canh file vao (hoac trong --out-dir):
    import-ile-expiry.txt       dien Expiration Date cho dung nhung dong Dung da xuat ra
    import-lot-info.txt         Lot No. Information con thieu

File vao la ban xuat "Table data" cua BC. No co the chua mot bang hoac ca hai bang; script tu
nhan ra bang nao qua dong `TABLEID:`.
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
JOURNAL = ROOT / "demo-data-nwv" / "import-full-journal.txt"

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

BANG_ILE = "Item Ledger Entry"
BANG_LOT = "Lot No. Information"

# Dung dung thu tu cot ma BC xuat ra. Doi thu tu la BC nhan sai cot ma khong bao gi.
COT_ILE = ["Entry No.", "Item No.", "Posting Date", "Entry Type", "Document No.",
           "Location Code", "Quantity", "Lot No.", "Expiration Date"]
COT_LOT = ["Item No.", "Variant Code", "Lot No.", "Description", "Test Quality",
           "Certificate Number", "Blocked", "Country/Region Code"]


def doc_bang(duong: Path) -> dict[str, tuple[list[str], list[list[str]]]]:
    """Tach mot ban xuat Table data thanh {ten bang: (tieu de, cac dong)}."""
    out: dict[str, tuple[list[str], list[list[str]]]] = {}
    ten, hdr, rows = None, None, []
    for dong in duong.read_text(encoding="utf-8-sig").splitlines():
        if dong.startswith("TABLEID:"):
            if ten:
                out[ten] = (hdr or [], rows)
            ten, hdr, rows = dong.split(":", 1)[1].strip(), None, []
        elif hdr is None and ten and dong.strip():
            hdr = [h.lstrip("*") for h in dong.split("\t")]
        elif dong.strip():
            rows.append(dong.split("\t"))
    if ten:
        out[ten] = (hdr or [], rows)
    return out


def ban_do_han_dung() -> dict[tuple[str, str], str]:
    """(Item No., Lot No.) -> han dung MM/DD/YY, doc tu chinh file journal da import.

    Lay tu file journal chu khong tinh lai, vi day dung la thu da post vao BC."""
    dong = JOURNAL.read_text(encoding="utf-8").splitlines()
    hdr = [h.lstrip("*") for h in dong[1].split("\t")]
    i = {h: n for n, h in enumerate(hdr)}
    han: dict[tuple[str, str], str] = {}
    xung_dot: list[tuple[str, str]] = []
    for l in dong[2:]:
        if not l.strip():
            continue
        r = l.split("\t")
        lot, exp = r[i["Lot No."]].strip(), r[i["Expiration Date"]].strip()
        if not lot or not exp:
            continue
        khoa = (r[i["Item No."]].strip(), lot)
        if han.get(khoa, exp) != exp:
            xung_dot.append(khoa)
        han[khoa] = exp
    if xung_dot:
        sys.exit(f"Mot lo co hai han dung khac nhau, khong doan: {xung_dot[:5]}")
    return han


def viet(duong: Path, bang: str, cot: list[str], rows: list[list[str]]) -> None:
    noi_dung = [f"TABLEID:{bang}", "\t".join("*" + c for c in cot)]
    noi_dung += ["\t".join(r) for r in rows]
    duong.write_text("\r\n".join(noi_dung) + "\r\n", encoding="utf-8")


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("file_vao", help="ban xuat Table data cua BC")
    ap.add_argument("--out-dir", default=None, help="thu muc ghi ket qua, mac dinh canh file vao")
    a = ap.parse_args()

    vao = Path(a.file_vao)
    ra_dir = Path(a.out_dir) if a.out_dir else vao.parent
    bang = doc_bang(vao)
    print(f"File vao co {len(bang)} bang: {', '.join(bang)}")
    han = ban_do_han_dung()
    print(f"Ban do han dung doc tu {JOURNAL.name}: {len(han)} lo")

    # -------------------------------------------------- 1. dien han dung cho ILE
    if BANG_ILE in bang:
        hdr, rows = bang[BANG_ILE]
        if hdr != COT_ILE:
            sys.exit(f"Cot cua {BANG_ILE} khong dung thu tu mong doi.\nCan: {COT_ILE}\nCo:  {hdr}")
        i = {h: n for n, h in enumerate(hdr)}
        ra, thieu, da_co, khong_lo = [], [], 0, 0
        for r in rows:
            r = (r + [""] * len(hdr))[:len(hdr)]
            lot = r[i["Lot No."]].strip()
            if not lot:
                khong_lo += 1
                continue
            if r[i["Expiration Date"]].strip():
                da_co += 1
                continue
            exp = han.get((r[i["Item No."]].strip(), lot))
            if not exp:
                thieu.append((r[i["Item No."]], lot))
                continue
            r[i["Expiration Date"]] = exp
            ra.append(r)
        if thieu:
            sys.exit(f"{len(thieu)} dong co lo ma khong tra duoc han dung, vi du {thieu[:5]}")
        f = ra_dir / "import-ile-expiry.txt"
        viet(f, BANG_ILE, COT_ILE, ra)
        print(f"\n{f}")
        print(f"  {len(ra)} dong duoc dien han dung"
              + (f", {da_co} dong da co san nen bo qua" if da_co else "")
              + (f", {khong_lo} dong khong co lo nen bo qua" if khong_lo else ""))
        print(f"  {len({(r[i['Item No.']], r[i['Lot No.']]) for r in ra})} lo, "
              f"{len({r[i['Item No.']] for r in ra})} mat hang")

    # -------------------------------------------------- 2. Lot No. Information con thieu
    da_co_lot = set()
    if BANG_LOT in bang:
        hdr, rows = bang[BANG_LOT]
        j = {h: n for n, h in enumerate(hdr)}
        da_co_lot = {(r[j["Item No."]].strip(), r[j["Lot No."]].strip()) for r in rows}
    rows_lot = []
    for (item, lot), exp in sorted(han.items()):
        if (item, lot) in da_co_lot:
            continue
        # Bang 6505 khong co truong Expiration Date, nen ghi han dung vao Description.
        # `Test Quality` de mot dau cach, dung y het cach BC xuat gia tri option rong.
        rows_lot.append([item, "", lot, f"HSD {_dmy(exp)}", " ", "", "No", ""])
    f = ra_dir / "import-lot-info.txt"
    viet(f, BANG_LOT, COT_LOT, rows_lot)
    print(f"\n{f}")
    print(f"  {len(rows_lot)} dong Lot No. Information con thieu"
          + (f", da bo qua {len(da_co_lot)} dong BC dang co" if da_co_lot else ""))
    print(f"  tong cong se thanh {len(rows_lot) + len(da_co_lot)} lo")


def _dmy(mmddyy: str) -> str:
    """MM/DD/YY cua ban xuat BC -> dd/mm/20yy cho nguoi doc."""
    try:
        m, d, y = mmddyy.split("/")
        return f"{int(d):02d}/{int(m):02d}/20{y}"
    except ValueError:
        return mmddyy


if __name__ == "__main__":
    main()
