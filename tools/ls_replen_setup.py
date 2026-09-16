"""Dien master data LS Replenishment cho bo demo Marou tren NWV01, roi chay tinh cua LS.

Cau hinh sinh tu tools/demo_scenario.py, khong chep tay: danh sach mat hang, cua hang ban mon nao
(ASSORTMENT), han dung, nhip chuyen hang (move_days), mon ngung kinh doanh.

    cd python
    python ../tools/ls_replen_setup.py config           # in cau hinh se ap
    python ../tools/ls_replen_setup.py apply            # ghi master data qua NWVDemoReplenSetup
    python ../tools/ls_replen_setup.py --company NWV-DAKAO partners   # vendor MAROU (Dakao) / customer DAKAO (Marou)
    python ../tools/ls_replen_setup.py --company NWV-DAKAO apply      # cau hinh rieng cho Dakao: mua thang tu Marou
    python ../tools/ls_replen_setup.py apply --reset-oos  # them buoc xoa het Out of Stock Log demo (sau khi post lai ILE)
    python ../tools/ls_replen_setup.py preflight        # kiem truoc khi import lai Item Journal
    python ../tools/ls_replen_setup.py calc             # Upd Out of Stock, Calc. Item Qty, tinh 2 journal
    python ../tools/ls_replen_setup.py summary          # doc lai ket qua tinh

Ngay neo demo 18/09/2026 truyen vao phien web service lam Work Date.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(HERE.parent / "python"))

import demo_scenario as ds  # noqa: E402

WORK_DATE = "2026-09-18"
SALES_PROFILE = "DEFAULT"   # co san: 3 tuan gan nhat trong so 75, 3-6 tuan 15, 6-8 tuan 10
TEMPLATE_TO = "MAROU-TO"
TEMPLATE_PO = "MAROU-PO"


def cover_days(it: ds.Item) -> tuple[int, int]:
    """So ngay phu ton o cua hang va o kho.

    Cua hang: bang nhip chuyen hang cua kich ban (move_days), khong vuot qua han dung tru 1 ngay,
    vi phu qua han dung la de xuat chuyen hang de roi huy.
    Kho: hang tuoi Dakao giao gan nhu hang ngay nen 2 ngay; han vua 7 ngay; han dai 21 ngay.
    """
    store = min(it.move_days, max(1, it.shelf - 1))
    if it.shelf <= 7:
        whse = 2
    elif it.shelf <= 60:
        whse = 7
    else:
        whse = 21
    return store, whse


# UC5 min-max: hang ban cham, han dai, dat theo muc ton tai quay thay vi so ngay phu. LS nhanh Calc-StockLevels:
# ton kha dung <= Reorder Point thi dua len Maximum Inventory, con khong thi khong de xuat. Hai muc dat sao cho
# ngay 18/09/2026 moi ma co cua hang duoi va tren diem dat lai (30091: S0001 3, S0002 4, S0005 2, S0010 0;
# 33150: S0001 16, S0002 8, S0005 6, S0010 13), de demo thay ca hai nhanh.
STOCK_LEVELS = {
    "30091": {"reorderPoint": 3, "maxInventory": 12},
    "33150": {"reorderPoint": 8, "maxInventory": 20},
}


# UC1 dua vao bo sung hang: hai mat hang kem bo sung theo du bao Holt-Winters ghi trong LSC Forecast Entry (kieu tinh
# Retail Forecast cua LS). Choco nuts 33323 cung nhom giu Average Usage de dat canh nhau khi demo.
LS_FORECAST = {"33310", "33341"}


def ngay_su_kien() -> list[dict]:
    """Lich khuyen mai va su kien bang bang chuan LS (Replen. Planned Event + Planned Sales Demand).

    Hai su kien da xay ra lay dung tu kich ban sinh du lieu (demo_scenario.PROMO, EVENT) de du bao bo cac ngay do khoi
    du lieu hoc. Mot su kien sap toi de LS cong them vao du bao khi tinh bo sung hang."""
    p_item, p_stores, p_from, p_to, p_mult, _ = ds.PROMO
    e_item, e_store, e_from, e_to, e_mult = ds.EVENT
    loai = "Additional % Factor (to Forecast)"
    return [
        {"code": "KM-CHOCOPILLAR-07", "description": f"Khuyen mai {p_item} thang 7 (ban x{p_mult:g})", "startDate": p_from.isoformat(),
         "endDate": p_to.isoformat(), "type": loai, "demand": round((p_mult - 1) * 100), "offerNo": "MR2607-CP",
         "lines": [{"item": p_item, "location": s} for s in p_stores]},
        {"code": "SK-ICECREAM-08", "description": f"Su kien {e_item} tai {e_store} thang 8 (ban x{e_mult:g})", "startDate": e_from.isoformat(),
         "endDate": e_to.isoformat(), "type": loai, "demand": round((e_mult - 1) * 100),
         "lines": [{"item": e_item, "location": e_store}]},
        {"code": "KM-CHOCOPILLAR-09", "description": "Khuyen mai Choco pillar 23-25/09 (demo, sap toi)", "startDate": "2026-09-23",
         "endDate": "2026-09-25", "type": loai, "demand": 100, "offerNo": "MR2609-CP",
         "lines": [{"item": "33310", "location": "S0001"}, {"item": "33310", "location": "S0002"}]},
        {"code": "KM-CHOCOBOWL-09", "description": "Khuyen mai Choco bowl 23-25/09 (demo, sap toi)", "startDate": "2026-09-23",
         "endDate": "2026-09-25", "type": loai, "demand": 150, "offerNo": "MR2609-CB",
         "lines": [{"item": "33341", "location": "S0001"}, {"item": "33341", "location": "S0010"}]},
    ]


def chuong_trinh_km() -> list[dict]:
    """Chuong trinh khuyen mai chuan LS (LSC Periodic Discount + Validation Period) cho tro ly tra loi CTKM.

    - MR2607-CP: khuyen mai thang 7 da xay ra, nhom gia FOOD (S0001, S0002) dung PROMO; da ket thuc nen Disabled
      (LS khong cho bat chuong trinh co ngay ket thuc da qua).
    - MR2609-CP: sap toi, nhom gia FOOD, Planned Event co du S0001 va S0002: khop.
    - MR2609-CB: sap toi, nhom gia ALL, Planned Event chi co S0001 va S0010 trong khi S0002, S0005 cung ban Choco bowl.
      Co y de lech: tro ly phai chi ra LS Replenishment chua cong nhu cau o hai cua hang do.
    - MR2609-CR: dang chay ca thang 9, 19h-22h, banh sung bo giam 30% de xa hang cuoi ngay, khong co Planned Event."""
    p_item, _, p_from, p_to, _, _ = ds.PROMO
    return [
        {"no": "MR2607-CP", "description": "Choco pillar -20% thang 7", "type": "Disc. Offer", "priceGroup": "FOOD",
         "discountPct": 20, "validationId": "260701", "startDate": p_from.isoformat(), "endDate": p_to.isoformat(),
         "enabled": False, "lines": [{"item": p_item, "discPct": 20}]},
        {"no": "MR2609-CP", "description": "Choco pillar -20% 23-25/09", "type": "Disc. Offer", "priceGroup": "FOOD",
         "discountPct": 20, "validationId": "260901", "startDate": "2026-09-23", "endDate": "2026-09-25",
         "enabled": True, "lines": [{"item": "33310", "discPct": 20}]},
        {"no": "MR2609-CB", "description": "Choco bowl -15% 23-25/09", "type": "Disc. Offer", "priceGroup": "ALL",
         "discountPct": 15, "validationId": "260902", "startDate": "2026-09-23", "endDate": "2026-09-25",
         "enabled": True, "lines": [{"item": "33341", "discPct": 15}]},
        {"no": "MR2609-CR", "description": "Banh sung bo -30% sau 19h", "type": "Disc. Offer", "priceGroup": "ALL",
         "discountPct": 30, "validationId": "260903", "startDate": "2026-09-01", "endDate": "2026-09-30",
         "startTime": "19:00:00", "endTime": "22:00:00", "enabled": True,
         "lines": [{"item": "33110", "discPct": 30}, {"item": "33100", "discPct": 30}]},
    ]


# Hai company tu 15/09/2026. Dakao (ban le) mua hang thang tu Marou, giao toi tung cua hang: vendor MAROU tren Item, khong
# co quy tac Replen. From Warehouse, journal mua kieu "Purchase Orders for Receiving Locations" (moi cua hang mot don, mau
# RT00003 cua Cronus). Marou (san xuat) giu kho tong W0003 va journal chuyen hang cho den khi dung lai du lieu.
DAKAO = "NWV-DAKAO"
MAROU = "NWV-MAROU"
VENDOR_MAROU = {"no": "MAROU", "name": "Marou Chocolate (san xuat)", "copyFrom": "44020"}
CUSTOMER_DAKAO = {"no": "DAKAO", "name": "Dakao (ban le)"}


def build_config(company: str = "") -> dict:
    dakao = company == DAKAO
    items = []
    dist = []
    for it in ds.ITEMS:
        store, whse = cover_days(it)
        row = {"no": it.no, "storeCoverDays": store, "whseCoverDays": whse, "salesProfile": SALES_PROFILE}
        if it.no in STOCK_LEVELS:
            row.update(calcType="Stock Levels", **STOCK_LEVELS[it.no])
        elif it.no in LS_FORECAST:
            row.update(calcType="LS Forecast")
        if dakao:
            row.update(vendor=VENDOR_MAROU["no"], fromWarehouse=False, purchOrderDelivery="To Store")
        items.append(row)
        status = "Not purchased again" if it.no in ds.DISCONTINUED else "Active"
        for s in ds.stores_for(it):
            dist.append({"store": s, "item": it.no, "status": status})
    item_filter = "|".join(it.no for it in ds.ITEMS)
    stores = "|".join(ds.STORES)
    return {
        # Dong Out of Stock Log con mo tu truoc ngay dau cua du lieu demo la rac Cronus, xem codeunit 70253.
        "deleteOpenOutOfStockBefore": ds.START.isoformat(),
        "centralWarehouse": ds.WH,
        "lsForecastSetup": True,
        "offers": chuong_trinh_km(),
        "plannedEvents": ngay_su_kien(),
        "stores": ds.STORES,
        "items": items,
        "distribution": dist,
        "templates": [
            {"code": TEMPLATE_TO, "type": "Transfer", "description": "Marou - chuyen hang tu kho tong W0003",
             "location": ds.WH, "storeGroupFilter": stores, "itemNoFilter": item_filter},
            ({"code": TEMPLATE_PO, "type": "Purchase", "description": "Dakao - mua tu Marou, giao thang cua hang",
              "location": "", "storeGroupFilter": stores, "itemNoFilter": item_filter, "purchaseOrderType": "Receiving Locations"}
             if dakao else
             {"code": TEMPLATE_PO, "type": "Purchase", "description": "Marou - mua hang ve kho tong W0003",
              "location": ds.WH, "storeGroupFilter": stores, "itemNoFilter": item_filter}),
        ],
    }


def main(argv: list[str]) -> None:
    # --company nam trong sys.argv thi tools_bc doc (no tu cat khoi sys.argv khi import); o day cat truoc de lay lenh.
    company = ""
    argv = list(argv)
    if "--company" in argv:
        i = argv.index("--company")
        company = argv[i + 1]
        del argv[i:i + 2]
    cmd = argv[0] if argv else "config"
    cfg = build_config(company)
    if "--reset-oos" in argv:
        cfg["resetOutOfStockLog"] = True
    if cmd == "config":
        print(json.dumps(cfg, ensure_ascii=False, indent=1))
        return

    import tools_bc as t  # can .env cua python/; --company NWV-DAKAO doi company

    if cmd == "partners":
        # Vendor MAROU trong Dakao, customer DAKAO trong Marou. Company nao thi doi tac nay.
        body = {"vendor": VENDOR_MAROU} if company == DAKAO else {"customer": CUSTOMER_DAKAO}
        print(t.ws("EnsurePartners", {"configJson": json.dumps(body, ensure_ascii=False)}, service="NWVDemoIntercompany"))
    elif cmd == "apply":
        res = t.ws("Apply", {"configJson": json.dumps(cfg, ensure_ascii=False)}, service="NWVDemoReplenSetup")
        print("so thay doi:", res["changes"])
        for e in res["log"]:
            print(f"  {e['table']:<24} {e['key']:<16} {e['field']:<34} {e['old']!s:>22} -> {e['new']}")
    elif cmd == "calc":
        print(t.ws("UpdateOutOfStock", {"workDateText": WORK_DATE}))
        items = "|".join(it.no for it in ds.ITEMS)
        print(t.ws("CalcItemQuantities", {"itemFilter": items, "workDateText": WORK_DATE}))
        for tpl in (TEMPLATE_TO, TEMPLATE_PO):
            print(t.ws("CalculateJournal", {"templateCode": tpl, "batchNo": "DEFAULT",
                                            "recalcItemQuantities": False, "workDateText": WORK_DATE}))
    elif cmd == "summary":
        summary(t)
    elif cmd == "preflight":
        preflight(t)
    else:
        raise SystemExit(__doc__)


def read(t, table: int, filters: dict, fields: str = "", maxrows: int = 5000) -> list[dict]:
    return t.ws("ReadTable", {"tableNo": table, "filtersJson": json.dumps(filters), "fieldFilter": fields,
                              "maxRows": maxrows})["rows"]


def preflight(t) -> None:
    """Kiem nhung bay da gap truoc khi import lai Item Journal. Xem CLAUDE.md, muc UC1 tren LS Replenishment."""
    items = "|".join(it.no for it in ds.ITEMS)
    loi = []
    rows = read(t, 27, {"No.": items}, "No.,Base Unit of Measure,Sales Unit of Measure,Purch. Unit of Measure,Item Tracking Code")
    for r in rows:
        for f in ("Sales Unit of Measure", "Purch. Unit of Measure"):
            if r[f] not in ("", r["Base Unit of Measure"]):
                loi.append(f"{r['No.']}: {f} = {r[f]}, khac Base {r['Base Unit of Measure']} (dong import se bi quy doi)")
        can = r["No."] in ds.TRACKED
        if can and not r["Item Tracking Code"]:
            loi.append(f"{r['No.']}: thieu Item Tracking Code (lot se bi bo qua khi post)")
        if not can and r["Item Tracking Code"]:
            loi.append(f"{r['No.']}: co Item Tracking Code {r['Item Tracking Code']} ma khong nam trong TRACKED")
    if len(rows) != len(ds.ITEMS):
        loi.append(f"chi tim thay {len(rows)}/{len(ds.ITEMS)} ma")
    var = read(t, 5401, {"Item No.": items}, "Item No.,Code")
    if var:
        ma = sorted({v["Item No."] for v in var})
        loi.append(f"{len(var)} Item Variant tren {', '.join(ma)}: LS Replenishment chi tinh theo variant, ton khong variant bi bo qua")
    cid = t.company_id()
    ile = t.req("GET", f"api/naviworld/marouagent/v1.0/companies({cid})/nwvItemLedgerEntries?$top=1&$select=entryNo").json()
    co_ile = bool(ile.get("value"))
    print("Item Ledger Entry:", "CON DU LIEU (phai xoa truoc khi import lai)" if co_ile else "rong")
    if loi:
        print(f"{len(loi)} van de:")
        for l in loi:
            print("  -", l)
    else:
        print("Master data 21 ma: khong co van de.")


def summary(t) -> None:
    items = "|".join(it.no for it in ds.ITEMS)
    riq = read(t, 10012205, {"Item No.": items, "Location Code": "|".join(ds.STORES + [ds.WH])},
               "Item No.,Location Code,Inventory,Daily Sales,Sales Date From,Sales Date To,No. of Sales Dates,"
               "No. of Days Out of Stock,Replenish From Warehouse,Replenishment Calculation Type,Is a Whse,"
               "Store Stock Cover Reqd (Days),Quantity in Transfer In,Quantity on Purchase Order")
    print(f"Replen. Item Quantity (21 ma x 5 cua hang + kho): {len(riq)} dong")
    for r in sorted(riq, key=lambda r: (r["Item No."], r["Location Code"])):
        print(f"  {r['Item No.']} {r['Location Code']:<6} ton {r['Inventory']:>7} ban/ngay {r['Daily Sales']:>8} "
              f"{r['Sales Date From']}..{r['Sales Date To']} het hang {r['No. of Days Out of Stock']:>3} ngay "
              f"tu kho {r['Replenish From Warehouse']} phu {r['Store Stock Cover Reqd (Days)']}")
    for tpl in (TEMPLATE_TO, TEMPLATE_PO):
        det = read(t, 10012204, {"Replenishment Template Code": tpl},
                   "Item No.,Location Code,Replenishment Location Code,Effective Inventory,Average Daily Sales,"
                   "Required Coverage Days,System Suggested Quantity,Quantity,Projected Eff. Inventory,Decision")
        print(f"\n{tpl}: {len(det)} dong chi tiet, {sum(1 for d in det if d['System Suggested Quantity'])} dong co de xuat")
        for d in det[:60]:
            print(f"  {d['Item No.']} {d['Location Code']:<6} ton hieu dung {d['Effective Inventory']:>7} "
                  f"ban/ngay {d['Average Daily Sales']:>7} phu {d['Required Coverage Days']:>3} "
                  f"de xuat {d['System Suggested Quantity']:>6} quyet dinh {d['Decision']}")
        log = read(t, 10012247, {"Replenishment Template Code": tpl}, "", 200)
        if log:
            print(f"  log tinh: {len(log)} dong, vi du:")
            for l in log[:12]:
                print("   ", {k: v for k, v in l.items() if v not in ("", 0, 0.0, False, "0001-01-01") and not k.startswith(("System", "$"))})


if __name__ == "__main__":
    main(sys.argv[1:])
