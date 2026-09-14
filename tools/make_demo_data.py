"""Sinh bo du lieu demo Marou cho Business Central: master data va Item Journal.

Mo phong theo ngay, co theo doi so du tung lo tai tung dia diem, xuat hang theo FEFO.
Khong dong nao lam am lo, va so ton cuoi ky la ket qua that cua mo phong chu khong phai
so ghim tay. Cac tinh huong demo duoc tao bang cach can thiep vao luong chuyen hang
(chuyen du, chuyen thieu), dung cach ma thuc te van xay ra.

Dong chay hang: nhap san xuat vao kho W0003 theo lo, chuyen tu kho ra cua hang bang
cap Negative Adjmt. o kho va Positive Adjmt. o cua hang giu nguyen so lo, roi ban tai
cua hang. Nho giu nguyen so lo ma demo truy xuat nguon goc chay duoc: tu mot so lo tim
ra no da di den nhung cua hang nao va ban trong khoang thoi gian nao.

Chay:
    python tools/make_demo_data.py --out /mnt/user-data/outputs/marou-demo
"""
from __future__ import annotations

import argparse
import random
import sys
from collections import defaultdict
from datetime import date, timedelta
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import openpyxl
from openpyxl.styles import Alignment, Font, PatternFill
from openpyxl.utils import get_column_letter

from demo_scenario import (ASSORTMENT, BATCH, BLOCKED_LOT_ITEM, BY_NO, COUNT_ADJ_LOCATIONS,
                           HISTORY_DAYS, ITEMS, LOT_NOS_SERIES, NO_REPLEN, OVERSHIP,
                           SHORT_DATED, START, STORES, TODAY, TRACKED, TRACKING_CODE, UNDERSHIP,
                           WASTE_ITEMS, WH, Item, demand_lambda, is_active, is_fresh,
                           stores_for, unit_price, wholesale_lambda)

SEED = 20260911
COLUMNS = [
    "Batch Name", "Posting Date", "Entry Type", "Document No.", "Item No.", "Description",
    "Variant Code", "Location Code", "Bin Code", "Quantity", "Unit of Measure Code",
    "Unit Amount", "Amount", "Discount Amount", "Unit Cost", "Gen. Bus. Posting Group",
    "Applies-to Entry", "Serial No.", "Lot No.", "Expiration Date", "Warranty Date",
    "Department Code", "Project Code", "Customergroup Code", "Area Code",
    "Businessgroup Code", "Salescampaign Code", "ItemDescription",
]
HEAD_FILL = PatternFill("solid", fgColor="1F3864")


# ---------------------------------------------------------------- so du tung lo
class Stock:
    """Ton theo (location, item, lot). Xuat theo FEFO: het han som nhat di truoc."""

    def __init__(self) -> None:
        self.qty: dict[tuple[str, str, str], float] = defaultdict(float)
        self.exp: dict[tuple[str, str], date] = {}          # (item, lot) -> han dung

    def receive(self, loc: str, item: str, lot: str, qty: float, exp: date) -> None:
        self.qty[(loc, item, lot)] += qty
        self.exp[(item, lot)] = exp

    def lots(self, loc: str, item: str, on: date, allow_expired: bool = False) -> list[tuple[str, float, date]]:
        out = []
        for (l, i, lot), q in self.qty.items():
            if l == loc and i == item and q > 0.0001:
                e = self.exp[(i, lot)]
                if allow_expired or e >= on:
                    out.append((lot, q, e))
        out.sort(key=lambda t: (t[2], t[0]))
        return out

    def on_hand(self, loc: str, item: str) -> float:
        return sum(q for (l, i, _), q in self.qty.items() if l == loc and i == item)

    def take(self, loc: str, item: str, qty: float, on: date,
             allow_expired: bool = False) -> list[tuple[str, float, date]]:
        """Tra ve danh sach (lot, qty, exp) da tru ra. Khong du thi tra ve it hon."""
        taken = []
        need = qty
        for lot, have, exp in self.lots(loc, item, on, allow_expired):
            if need <= 0.0001:
                break
            use = min(have, need)
            self.qty[(loc, item, lot)] -= use
            need -= use
            taken.append((lot, use, exp))
        return taken


def lot_code(it: Item, d: date, suffix: str = "") -> str:
    """Mot lo san xuat cho moi mat hang moi chu ky, dung chung cho moi dia diem.
    Nho vay demo truy xuat nguon goc chay duoc: mot so lo di den nhieu cua hang.
    Hau to A, B, C danh dau me san xuat trong cung mot ngay, moi me mot han dung rieng."""
    return f"L{d:%y%m%d}-{it.no}{suffix}"


def make_row(d: date, entry_type: str, it: Item, loc: str, qty: float,
             unit_amount: float, lot: str, exp: date, doc_prefix: str,
             discount: float = 0.0) -> dict:
    return {
        "Batch Name": BATCH,
        "Posting Date": d,
        "Entry Type": entry_type,
        "Document No.": f"{doc_prefix}{d:%y%m%d}",
        "Item No.": it.no,
        "Description": it.desc,
        "Variant Code": "",
        "Location Code": loc,
        "Bin Code": "",
        "Quantity": round(qty, 2),
        "Unit of Measure Code": it.uom,
        "Unit Amount": round(unit_amount, 2),
        "Amount": round(unit_amount * qty, 2),
        "Discount Amount": round(discount, 2),
        "Unit Cost": it.cost,
        "Gen. Bus. Posting Group": "",
        "Applies-to Entry": "",
        "Serial No.": "",
        # Mat hang khong co Item Tracking Code thi hai cot nay PHAI de trong.
        # Dien vao se bi BC chan luc post.
        "Lot No.": lot if it.no in TRACKED else "",
        "Expiration Date": exp if it.no in TRACKED else "",
        "Warranty Date": "",
        "Department Code": "",
        "Project Code": "",
        "Customergroup Code": "",
        "Area Code": "",
        "Businessgroup Code": "",
        "Salescampaign Code": "",
        "ItemDescription": it.desc,
    }


# ---------------------------------------------------------------- mo phong
def simulate() -> tuple[list[dict], dict]:
    rng = random.Random(SEED)
    st = Stock()
    rows: list[dict] = []
    stats = defaultdict(int)
    sales_hist: dict[tuple[str, str], list[float]] = defaultdict(list)

    # Can thiep "chuyen du" khong gan vao mot ngay chinh xac, vi ngay do chua chac la ngay
    # chuyen hang. Gan vao lan chuyen dau tien ke tu ngay do, roi xoa khoi hang cho.
    pending = {(i, l): [TODAY - timedelta(days=n), m] for i, l, n, m in OVERSHIP}
    undership = {(i, l): TODAY - timedelta(days=n) for i, l, n in UNDERSHIP}

    for day_idx in range(HISTORY_DAYS + 1):
        d = START + timedelta(days=day_idx)

        for it in ITEMS:
            if not is_active(it, d):
                continue
            shops = stores_for(it)

            # --- nhap san xuat vao kho theo chu ky lo
            # Chu ky san xuat ngan hon nhieu so voi han dung, nen mot mat hang co hang chuc
            # lo khac nhau trong ky chu khong phai vai lo. Han dung con lech nhau tung lo,
            # vi thuc te khong me nao giong me nao.
            lot_period = max(2, min(it.shelf // 6, 14))
            if day_idx % lot_period == 0:
                # Nhap bu den muc du ban het mot chu ky lo cong mot chu ky chuyen hang.
                # Phai tru ton kho dang co, khong tru thi moi ky lai chong len mot lop nua.
                horizon = lot_period + it.move_days
                need = sum(demand_lambda(it, s, d + timedelta(days=k))
                           for s in shops for k in range(horizon))
                # Kho con phai co hang de ban si, khong tinh vao thi cua hang bi doi theo.
                need += sum(wholesale_lambda(it, d + timedelta(days=k)) for k in range(horizon))
                qty = round(need * 1.12 - st.on_hand(WH, it.no))
                inj = pending.get((it.no, WH))
                if inj and d >= inj[0]:
                    qty = max(qty, round(need * inj[1]))
                    pending.pop((it.no, WH))
                if qty > 0:
                    # Chia thanh nhieu me khi luong lon, moi me mot han dung rieng
                    n_sub = 3 if qty >= 120 else (2 if qty >= 40 else 1)
                    base = qty // n_sub
                    jit = max(1, it.shelf // 8)
                    for k in range(n_sub):
                        sub_qty = qty - base * (n_sub - 1) if k == n_sub - 1 else base
                        if sub_qty <= 0:
                            continue
                        suffix = "" if n_sub == 1 else "ABC"[k]
                        lot = lot_code(it, d, suffix)
                        shelf = max(1, it.shelf + rng.randint(-jit, jit))
                        exp = d + timedelta(days=shelf)
                        st.receive(WH, it.no, lot, sub_qty, exp)
                        rows.append(make_row(d, "Purchase", it, WH, sub_qty, it.cost, lot, exp, "PR"))
                        stats["nhap_kho"] += 1

            # --- nhap lo can date roi chuyen thang ve mot cua hang
            for s_item, s_store, s_back, s_left, s_mult in SHORT_DATED:
                if it.no != s_item or d != TODAY - timedelta(days=s_back):
                    continue
                lot = lot_code(it, d) + "-SD"
                exp = d + timedelta(days=s_left)
                sellable = sum(demand_lambda(it, s_store, d + timedelta(days=k))
                               for k in range(s_left))
                qty = round(sellable * s_mult)
                if qty <= 0:
                    continue
                st.receive(WH, it.no, lot, qty, exp)
                rows.append(make_row(d, "Purchase", it, WH, qty, it.cost, lot, exp, "PR"))
                st.qty[(WH, it.no, lot)] -= qty
                st.receive(s_store, it.no, lot, qty, exp)
                rows.append(make_row(d, "Negative Adjmt.", it, WH, qty, it.cost, lot, exp, "TR"))
                rows.append(make_row(d, "Positive Adjmt.", it, s_store, qty, it.cost, lot, exp, "TR"))
                stats["nhap_can_date"] += 1

            # --- ban si tu kho trung tam
            wl = wholesale_lambda(it, d)
            if wl > 0:
                q = sum(1 for _ in range(int(wl * 3) + 1) if rng.random() < 1 / 3)
                if q > 0:
                    for lot, used, exp in st.take(WH, it.no, q, d):
                        rows.append(make_row(d, "Sale", it, WH, used, round(it.price * 0.72, 2),
                                             lot, exp, "WS"))
                        sales_hist[(it.no, WH)].append(used)
                        stats["ban_si"] += 1

            # --- chuyen tu kho ra cua hang
            if day_idx % it.move_days == 0:
                for s in shops:
                    if (it.no, s) in undership and d >= undership[(it.no, s)]:
                        continue
                    if any(it.no == i and s == st_ and f <= d <= to
                           for i, st_, f, to in NO_REPLEN):
                        continue          # cua so ngung chuyen hang, de ton tu rut ve 0
                    # Hang tuoi khong tru hang qua han dung duoc, nen muc ton muc tieu
                    # bi chan boi chinh han dung chu khong phai boi chu ky chuyen.
                    cover = min(max(it.move_days + 2, 14), max(it.move_days, it.shelf - 1))
                    need = sum(demand_lambda(it, s, d + timedelta(days=k)) for k in range(cover))
                    have = st.on_hand(s, it.no)
                    # Hang tuoi khong dat du phong, dat du phong la sinh ra huy hang.
                    buffer = 1.0 if it.shelf <= 7 else (1.25 if it.shelf > 60 else 1.12)
                    want = max(0.0, need * buffer - have)
                    inj = pending.get((it.no, s))
                    if inj and d >= inj[0]:
                        want = max(want, need * inj[1])
                        pending.pop((it.no, s))
                    want = round(want)
                    if want <= 0:
                        continue
                    for lot, q, exp in st.take(WH, it.no, want, d):
                        st.receive(s, it.no, lot, q, exp)
                        rows.append(make_row(d, "Negative Adjmt.", it, WH, q, it.cost, lot, exp, "TR"))
                        rows.append(make_row(d, "Positive Adjmt.", it, s, q, it.cost, lot, exp, "TR"))
                        stats["chuyen_kho"] += 2

            # --- ban tai cua hang
            for s in shops:
                lam = demand_lambda(it, s, d)
                if lam <= 0:
                    continue
                q = sum(1 for _ in range(int(lam * 3) + 1) if rng.random() < 1 / 3)
                if q <= 0:
                    continue
                price = unit_price(it, s, d)
                sold = 0.0
                for lot, used, exp in st.take(s, it.no, q, d):
                    disc = (it.price - price) * used
                    rows.append(make_row(d, "Sale", it, s, used, price, lot, exp, "SL", disc))
                    sold += used
                    stats["ban"] += 1
                if sold < q:
                    stats["thieu_hang_ngay"] += 1
                sales_hist[(it.no, s)].append(sold)

            # --- huy hang qua han, chi hang tuoi, chay moi thu hai
            if it.no in WASTE_ITEMS and d <= TODAY - timedelta(days=7):
                for loc in [WH] + shops:
                    for lot, q, exp in st.lots(loc, it.no, d, allow_expired=True):
                        if exp < d:
                            st.qty[(loc, it.no, lot)] -= q
                            rows.append(make_row(d, "Negative Adjmt.", it, loc, q, it.cost, lot, exp, "WS"))
                            stats["huy_qua_han"] += 1

        # --- kiem ke hang thang, chenh lech nho
        if d.day == 1 and day_idx > 0:
            for loc in COUNT_ADJ_LOCATIONS:
                for it in rng.sample(ITEMS, 3):
                    if loc not in stores_for(it):
                        continue
                    lots = st.lots(loc, it.no, d)
                    if not lots:
                        continue
                    lot, have, exp = lots[0]
                    delta = rng.choice([-2, -1, 1, 2])
                    if delta < 0 and have < abs(delta):
                        continue
                    et = "Positive Adjmt." if delta > 0 else "Negative Adjmt."
                    st.qty[(loc, it.no, lot)] += delta
                    rows.append(make_row(d, et, it, loc, abs(delta), it.cost, lot, exp, "CT"))
                    stats["kiem_ke"] += 1

    rows.sort(key=lambda r: (r["Posting Date"],
                             {"Purchase": 0, "Positive Adjmt.": 1, "Negative Adjmt.": 2, "Sale": 3}[r["Entry Type"]],
                             r["Item No."], r["Location Code"]))
    return rows, {"stats": dict(stats), "stock": st, "sales": sales_hist}


# ---------------------------------------------------------------- xuat excel
def style_header(ws, columns: list[str]) -> None:
    ws.append(columns)
    for c in range(1, len(columns) + 1):
        cell = ws.cell(row=1, column=c)
        cell.font = Font(bold=True, color="FFFFFF")
        cell.fill = HEAD_FILL
        cell.alignment = Alignment(horizontal="center", vertical="center", wrap_text=True)
        ws.column_dimensions[get_column_letter(c)].width = 26 if len(columns[c - 1]) > 16 else 16
    ws.freeze_panes = "A2"


def write_journal(path: Path, rows: list[dict]) -> None:
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "Item Journals"
    ws.sheet_properties.tabColor = "1F3864"
    style_header(ws, COLUMNS)
    for r in rows:
        ws.append([r[c] for c in COLUMNS])
    for col in ("B", "T"):
        for cell in ws[col][1:]:
            cell.number_format = "DD/MM/YYYY"
    ws.auto_filter.ref = f"A1:{get_column_letter(len(COLUMNS))}{ws.max_row}"
    wb.save(path)


def write_master(path: Path, sim: dict):
    """Chi ghi nhung gi phai sua tren master data co san, khong tao ban ghi moi."""
    st: Stock = sim["stock"]
    sales = sim["sales"]
    wb = openpyxl.Workbook()
    wb.remove(wb.active)

    def sheet(title, cols, data, tab="7F7F7F"):
        ws = wb.create_sheet(title)
        ws.sheet_properties.tabColor = tab
        style_header(ws, cols)
        for r in data:
            ws.append(r)

    # Item: cap nhat gia von cho mat hang dang de 0, va gan tracking code cho ba mat hang
    # da duoc cau hinh tren Item Card. Khong dong vao mat hang khac.
    item_rows = []
    for i in ITEMS:
        item_rows.append([
            i.no, i.desc, i.cost, i.cost, i.price,
            TRACKING_CODE if i.no in TRACKED else "",
            LOT_NOS_SERIES if i.no in TRACKED else "",
            "Purchase", "Fixed Reorder Qty.",
            "co" if i.cost_was_zero else "",
            "co" if i.no in TRACKED else "",
        ])
    sheet("Item",
          ["No.", "Description", "Unit Cost", "Last Direct Cost", "Unit Price",
           "Item Tracking Code", "Lot Nos.", "Replenishment System", "Reordering Policy",
           "Gia von moi dat", "Co lot tracking"],
          item_rows, tab="C00000")

    # Stockkeeping Unit: nguong tinh tu chinh luong ban 90 ngay cuoi cua mo phong
    sku = []
    for loc in [WH] + STORES:
        for it in ITEMS:
            if loc != WH and loc not in stores_for(it):
                continue
            if loc == WH:
                avg = sum(sum(sales.get((it.no, s), [])[-90:]) for s in stores_for(it)) / 90
            else:
                avg = sum(sales.get((it.no, loc), [])[-90:]) / 90
            lead, safety, target = it.move_days + 2, 3, 14
            sku.append([loc, it.no, "", "Purchase" if loc == WH else "Transfer",
                        "Fixed Reorder Qty.", round(avg * (lead + safety)),
                        max(1, round(avg * target)), round(avg * safety),
                        round(avg * 45), "" if loc == WH else WH])
    sheet("Stockkeeping Unit",
          ["Location Code", "Item No.", "Variant Code", "Replenishment System",
           "Reordering Policy", "Reorder Point", "Reorder Quantity",
           "Safety Stock Quantity", "Maximum Inventory", "Transfer-from Code"],
          sku, tab="C00000")

    # Lot No. Information: chi cho mat hang co tracking code, va chi cho lo con ton
    seen, lots, blocked = set(), [], None
    for (loc, item, lot), q in sorted(st.qty.items()):
        if q <= 0.0001 or item not in TRACKED or (item, lot) in seen:
            continue
        seen.add((item, lot))
        if item == BLOCKED_LOT_ITEM and blocked is None:
            blocked = lot
        lots.append([item, "", lot, f"{BY_NO[item].desc} lot {lot}",
                     "true" if (item == BLOCKED_LOT_ITEM and lot == blocked) else "false"])
    sheet("Lot No. Information",
          ["Item No.", "Variant Code", "Lot No.", "Description", "Blocked"], lots)

    wb.save(path)
    return len(lots), blocked


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", required=True)
    args = ap.parse_args()
    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)

    rows, sim = simulate()
    n_lots, blocked = write_master(out / "00-MasterData.xlsx", sim)

    by_month: dict[tuple[int, int], list[dict]] = defaultdict(list)
    for r in rows:
        by_month[(r["Posting Date"].year, r["Posting Date"].month)].append(r)
    for idx, mk in enumerate(sorted(by_month), start=1):
        write_journal(out / f"{idx:02d}-ItemJournals-{mk[0]}-{mk[1]:02d}.xlsx", by_month[mk])

    st: Stock = sim["stock"]
    rem = {k: v for k, v in st.qty.items() if v > 0.0001}
    neg = {k: v for k, v in st.qty.items() if v < -0.0001}
    print(f"{len(rows)} dong, {len(by_month)} file thang")
    print("thong ke:", sim["stats"])
    print(f"lo con ton: {len(rem)}  tong ton: {sum(rem.values()):,.0f}  lo am: {len(neg)}")
    print(f"Lot No. Information: {n_lots} dong, lo bi khoa: {blocked}")
    for mk in sorted(by_month):
        print(f"  {mk[0]}-{mk[1]:02d}: {len(by_month[mk]):6d} dong")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())


# ---------------------------------------------------------------- doi sang dang Item Ledger Entry
SIGN = {"Purchase": 1, "Positive Adjmt.": 1, "Sale": -1, "Negative Adjmt.": -1}


def journal_rows_to_ile(rows: list[dict]) -> list[dict]:
    """Doi dong Item Journal thanh dong Item Ledger Entry nhu BC se sinh ra sau khi post.

    Dung de chay thu lop tinh toan UC2 tren dung bo du lieu sap import, truoc khi co BC that.
    Quantity tren ILE la so co dau: nhap duong, xuat am.
    """
    out = []
    for i, r in enumerate(rows, start=1):
        et = r["Entry Type"]
        out.append({
            "entry_no": i,
            "posting_date": r["Posting Date"],
            "entry_type": et,
            "document_no": r["Document No."],
            "item_no": r["Item No."],
            "description": r["Description"],
            "location_code": r["Location Code"],
            "quantity": SIGN[et] * r["Quantity"],
            "lot_no": r["Lot No."] or None,
            "expiration_date": r["Expiration Date"] or None,
            "variant_code": "",
            "unit_cost": r["Unit Cost"],
        })
    return out
