"""Du lieu demo UC3: lich su don mua va phieu nhan cua hai nha cung cap, cong vai don mua con mo qua han.

Chay (tu thu muc python):
    python ../tools/supplier_demo.py plan      # in tom tat ke hoach, ghi demo-data-nwv/supplier-plan.json
    python ../tools/supplier_demo.py apply     # tao don va post phieu nhan qua web service NWVDemoSupplier
    python ../tools/supplier_demo.py calc      # tinh scorecard tren BC (Work Date 18/09/2026) va in ket qua

Kich ban (seed co dinh, chay lai ra dung ke hoach cu; don da co key thi AL bo qua):
- 44030 Dan-s Dairy: dat thu Hai va thu Nam, hua giao 3 ngay. Dang tin cay: phan lon dung hen, it khi giao thieu.
- 44020 AL-s Foods: dat thu Ba, hua giao 7 ngay. Tu 27/07/2026 tre ngay cang nhieu va hay giao lam hai lan.
Lich su nhan hang vao dia diem NCC-NHAN (xem ghi chu dau codeunit 70257: khong lam doi ton cua W0003 va cua hang).
Don con mo dat o W0003 va cua hang de tro ly bao qua han va hoi dung nguoi nhan.
"""
from __future__ import annotations

import json
import random
import sys
from datetime import date, timedelta
from pathlib import Path

GOC = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(GOC / "python"))

RA = GOC / "demo-data-nwv" / "supplier-plan.json"
NHAN = "NCC-NHAN"
NEO = date(2026, 9, 18)
TU = date(2026, 4, 6)
DOI_TE = date(2026, 7, 27)          # AL-s Foods bat dau giao tre nhieu hon
SEED = 20260914

GIA = {"10000": 0.9, "10045": 0.45, "10070": 0.5, "10100": 1.7, "18120": 1.0, "18200": 0.95, "18230": 0.95,
       "30091": 2.8, "33120": 6.5, "33150": 1.8, "33200": 4.2, "33250": 3.1}
SUA = ["10000", "10045", "10070", "10100"]
DO_LANH = ["18200", "18230", "30091", "33120", "33150", "33200", "33250"]
RA_MAT_18120 = date(2026, 7, 20)

# Don con mo, khong nhan: key, NCC, ngay dat, ngay hen, dia diem, dong
DON_MO = [
    ("NCC-MO-01", "44020", date(2026, 9, 1), date(2026, 9, 8), "W0003", [("30091", 36), ("18200", 48)]),
    ("NCC-MO-02", "44020", date(2026, 9, 8), date(2026, 9, 15), "W0003", [("33200", 60), ("33250", 48)]),
    ("NCC-MO-03", "44020", date(2026, 9, 11), date(2026, 9, 18), "S0005", [("33120", 12)]),
    ("NCC-MO-04", "44030", date(2026, 9, 10), date(2026, 9, 13), "S0001", [("10070", 36)]),
    ("NCC-MO-05", "44030", date(2026, 9, 15), date(2026, 9, 18), "S0010", [("10000", 48), ("10045", 24)]),
]


def _ngay_dat(thu: set[int], den: date):
    d = TU
    while d <= den:
        if d.weekday() in thu:
            yield d
        d += timedelta(days=1)


def ke_hoach() -> dict:
    rnd = random.Random(SEED)
    don: list[dict] = []
    ngay_mo = {(k[1], k[2]) for k in DON_MO}
    stt = 0

    def them(ncc: str, ngay: date, hua: int, mat_hang: list[str], so_dong: tuple[int, int], sl: tuple[int, int],
             dung_hen: float, tre: tuple[int, int], tach: float, tre_lan_hai: tuple[int, int]) -> None:
        nonlocal stt
        han = ngay + timedelta(days=hua)
        if han >= NEO or (ncc, ngay) in ngay_mo:
            return
        stt += 1
        chon = rnd.sample(mat_hang, rnd.randint(*so_dong))
        dong = [{"itemNo": m, "quantity": rnd.randint(sl[0] // 12, sl[1] // 12) * 12, "unitCost": GIA[m],
                 "expectedReceiptDate": han.isoformat()} for m in chon]
        r = rnd.random()
        ngay_nhan = han if r < dung_hen else han + timedelta(days=rnd.randint(*tre))
        ngay_nhan = min(ngay_nhan, NEO - timedelta(days=1))
        phieu = []
        if rnd.random() < tach:
            lan1, lan2 = [], []
            for i, l in enumerate(dong):
                dau = max(12, int(l["quantity"] * rnd.uniform(0.5, 0.8)) // 12 * 12)
                dau = min(dau, l["quantity"])
                lan1.append({"line": i, "quantity": dau})
                if l["quantity"] - dau > 0:
                    lan2.append({"line": i, "quantity": l["quantity"] - dau})
            phieu.append({"date": ngay_nhan.isoformat(), "lines": lan1})
            if lan2:
                ngay2 = min(ngay_nhan + timedelta(days=rnd.randint(*tre_lan_hai)), NEO - timedelta(days=1))
                phieu.append({"date": ngay2.isoformat(), "lines": lan2})
        else:
            phieu.append({"date": ngay_nhan.isoformat(), "lines": [{"line": i, "quantity": l["quantity"]} for i, l in enumerate(dong)]})
        don.append({"key": f"NCC-{stt:04d}", "vendorNo": ncc, "orderDate": ngay.isoformat(), "locationCode": NHAN,
                    "lines": dong, "receipts": phieu})

    for ngay in _ngay_dat({0, 3}, NEO):
        them("44030", ngay, 3, SUA, (2, 3), (24, 96), 0.9, (1, 2), 0.05, (1, 2))
    for ngay in _ngay_dat({1}, NEO):
        hang = DO_LANH + (["18120"] if ngay >= RA_MAT_18120 else [])
        if ngay < DOI_TE:
            them("44020", ngay, 7, hang, (3, 4), (12, 72), 0.72, (1, 4), 0.2, (2, 4))
        else:
            them("44020", ngay, 7, hang, (3, 4), (12, 72), 0.3, (3, 8), 0.35, (2, 5))

    for key, ncc, dat, han, noi, dong in DON_MO:
        don.append({"key": key, "vendorNo": ncc, "orderDate": dat.isoformat(), "locationCode": noi,
                    "lines": [{"itemNo": m, "quantity": q, "unitCost": GIA[m], "expectedReceiptDate": han.isoformat()}
                              for m, q in dong], "receipts": []})
    return {"receivingLocation": NHAN, "orders": don}


def tom_tat(plan: dict) -> None:
    from collections import Counter
    c = Counter(o["vendorNo"] for o in plan["orders"])
    phieu = sum(len(o["receipts"]) for o in plan["orders"])
    mo = [o["key"] for o in plan["orders"] if not o["receipts"]]
    print(f"{len(plan['orders'])} don ({dict(c)}), {phieu} phieu nhan, don mo: {mo}")


def main(argv: list[str]) -> None:
    cmd = argv[0] if argv else "plan"
    plan = ke_hoach()
    RA.parent.mkdir(parents=True, exist_ok=True)
    RA.write_text(json.dumps(plan, ensure_ascii=False, indent=1), encoding="utf-8")
    tom_tat(plan)
    if cmd == "apply":
        import tools_bc as t
        tong = {"ordersCreated": 0, "ordersSkipped": 0, "receiptsPosted": 0, "errors": []}
        for i in range(0, len(plan["orders"]), 8):
            phan = {"receivingLocation": plan["receivingLocation"], "orders": plan["orders"][i:i + 8]}
            kq = t.ws("CreateSupplierHistory", {"planJson": json.dumps(phan)}, service="NWVDemoSupplier")
            for k in ("ordersCreated", "ordersSkipped", "receiptsPosted"):
                tong[k] += kq[k]
            tong["errors"] += kq["errors"]
            print(i, kq)
            if kq["errors"]:
                break
        print(tong)
    elif cmd == "calc":
        import tools_bc as t
        print(t.ws("RunCalculations", {"param": "SUPPLIER", "workDateText": NEO.isoformat()}, service="NWVAgentCalcService"))
        from bc_agent.bc_client import BCClient
        from bc_agent.config import Settings
        for r in BCClient(Settings()).query("supplierScorecards", [], top=200):
            print(r["vendorNo"], r["itemCategoryCode"] or "(tong)", "due", r["linesDue"], "on-time", r["onTimePct"],
                  "giao du lan dau", r["firstDeliveryCompletePct"], "tre TB", r["avgDelayDays"], "lead hua/thuc",
                  r["avgPromisedLeadTime"], r["avgActualLeadTime"], "qua han", r["overdueLines"], "|", r["attentionReason"])


if __name__ == "__main__":
    main(sys.argv[1:])
