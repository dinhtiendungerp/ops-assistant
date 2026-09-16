"""Bo cong cu cho planner. Day la khac biet kien truc so voi job queue:
job queue chay mot chuoi buoc co dinh do dev viet san; planner nhan mot bo cong cu
va tu chon goi cai nao, bao nhieu lan, theo thu tu nao, tuy cau nguoi hoi.

Moi tool tra ve JSON thuan. Ham chan (guardrail) nam o day chu khong nam o model:
model chi duoc doc, va chi duoc de xuat; moi de xuat van di qua PolicyEngine va BC.
"""
from __future__ import annotations

from typing import Any

MAX_STEPS = 12

TOOLS: list[dict[str, Any]] = [
    {
        "name": "list_stock",
        "description": "Ton kho CUA MOT DIA DIEM, moi mat hang o do: so luong, gia von, nhom hang, phan tang, so lo va lo gan han nhat. "
                       "Chi dung khi can biet ca dia diem con gi. Cau hoi ve MOT mat hang o nhieu noi thi dung stock_by_item, "
                       "khong goi tool nay lan luot cho tung dia diem.",
        "input_schema": {"type": "object", "properties": {
            "location": {"type": "string", "description": "Ma dia diem, vi du W0003 (kho trung tam), S0001, S0002, S0005, S0010, S0013"},
            "category": {"type": "string", "description": "Loc theo nhom hang: DESSERTS, ICECREAM, FROZEN, BEVERAGES, DAIRY. Rong la lay het."}},
            "required": ["location"]},
    },
    {
        "name": "stock_by_item",
        "description": "Ton kho MOT mat hang tai TAT CA dia diem trong mot lan goi, kem ban binh quan ngay, so ngay ban con lai "
                       "(days of cover) va lo. Day la tool dau tien cho moi cau hoi ve mot mat hang.",
        "input_schema": {"type": "object", "properties": {"item_no": {"type": "string"}}, "required": ["item_no"]},
    },
    {
        "name": "find_item",
        "description": "Tim ma mat hang tu chu nguoi go, vi du 'choco nuts' -> 33323.",
        "input_schema": {"type": "object", "properties": {"text": {"type": "string"}}, "required": ["text"]},
    },
    {
        "name": "stores_at_risk",
        "description": "Cac cap cua hang x mat hang ma LS Replenishment dang de xuat bo sung, tuc sap het hang (stock-out risk): ton, "
                       "hang dang ve, ban binh quan, so ngay con ban duoc, so luong de xuat, so ngay het hang trong cua so tinh. "
                       "Dung cho cau 'mat hang nao sap het', 'cua hang nao co nguy co het hang', va de kiem tra rut hang khoi kho "
                       "trung tam co lam vo ke hoach cua cua hang khac khong.",
        "input_schema": {"type": "object", "properties": {
            "item_no": {"type": "string", "description": "Rong la lay tat ca mat hang"},
            "location": {"type": "string", "description": "Ma cua hang, vi du S0002. Rong la moi cua hang."}}, "required": []},
    },
    {
        "name": "inventory_health",
        "description": "Bang Suc khoe ton kho (NWV Inventory Health) Business Central da tinh: moi dong la mat hang x dia diem x lo, "
                       "xep tang Expired (het han), NearExpiry (can date), StockOutRisk (sap het hang), SlowMoving (cham luan chuyen), "
                       "Excess (ton thua), Healthy. Tra toi da 40 dong rui ro cao nhat kem ly do xep tang. Dung cho cau 'o cua hang toi "
                       "co gi can lo', 'lo nao sap het han', 'mat hang nao sap het hang', 'hang nao ton lau khong ban'.",
        "input_schema": {"type": "object", "properties": {
            "location": {"type": "string", "description": "Ma dia diem. Rong la moi dia diem."},
            "tier": {"type": "string", "enum": ["Expired", "NearExpiry", "StockOutRisk", "SlowMoving", "Excess", "Healthy", ""],
                     "description": "Loc mot tang. Rong la lay moi tang tru Healthy."},
            "item_no": {"type": "string"},
            "sort": {"type": "string", "enum": ["rui_ro", "ban_cham"],
                     "description": "rui_ro (mac dinh): diem rui ro cao nhat, bo Healthy. ban_cham: MOI tang con ton, xep ton "
                                    "phu nhieu ngay nhat / ban it nhat truoc; dung cho cau 'hang nao ban cham', 'dua gi ra khu "
                                    "trung bay', 'hang nao can day ban' (tang SlowMoving rong khong co nghia la khong co hang ban cham)."}},
            "required": []},
    },
    {
        "name": "replenishment_suggestions",
        "description": "Danh sach de xuat bo sung hang cua LS Replenishment (LS Central da tinh, tro ly khong tinh lai): moi dong "
                       "la mat hang x cua hang, gom so luong LS de xuat, muc LS tinh truoc khi chan, ban binh quan ngay, so ngay phu "
                       "yeu cau, ton, hang dang ve, ton kha dung o kho cap, so ngay het hang trong cua so tinh, quyet dinh cua LS, "
                       "kieu (chuyen tu kho hay mua tu vendor), nguon. Kem `flags` do code tinh, viet bang tieng Viet doc duoc, de nhin ra "
                       "dong bat thuong (het hang qua nua cua so tinh, khong co ban binh quan ma van de xuat, de xuat vuot ban binh "
                       "quan nhan ngay phu, kho cap khong du, ton bang 0, bi chia lai vi kho thieu; kieu min-max chi la ghi chu). "
                       "Dung cho cau 'tong hop de xuat bo sung', 'de xuat nao bat thuong', 'LS dang de xuat gi cho cua hang toi'. "
                       "Muon biet vi sao MOT dong ra so do thi goi explain_replenishment.",
        "input_schema": {"type": "object", "properties": {
            "location": {"type": "string", "description": "Ma cua hang. Rong la moi cua hang."},
            "item_no": {"type": "string"},
            "only_suggested": {"type": "boolean", "description": "true (mac dinh): chi dong LS de xuat so luong > 0"}},
            "required": []},
    },
    {
        "name": "explain_replenishment",
        "description": "Vi sao LS Replenishment ra so luong do cho MOT mat hang tai MOT cua hang: cac buoc doc tu nhat ky tinh cua LS "
                       "(kieu tinh, tham so, ton kha dung, cong thuc, quyet dinh) va nhat ky nguyen van. Chi co khi noi Business Central.",
        "input_schema": {"type": "object", "properties": {"item_no": {"type": "string"}, "location": {"type": "string"}},
                         "required": ["item_no", "location"]},
    },
    {
        "name": "sales_rate",
        "description": "Toc do ban binh quan ngay cua mot mat hang tai mot dia diem, tinh tren lich su ban.",
        "input_schema": {"type": "object", "properties": {
            "item_no": {"type": "string"}, "location": {"type": "string"}, "days": {"type": "integer"}},
            "required": ["item_no"]},
    },
    {
        "name": "lot_info",
        "description": "Thong tin mot lo: nam o dau, con bao nhieu, han dung, gia tri ton, phan tang.",
        "input_schema": {"type": "object", "properties": {"lot_no": {"type": "string"}}, "required": ["lot_no"]},
    },
    {
        "name": "promotions",
        "description": "Chuong trinh khuyen mai cua LS (Periodic Discount): dang chay, sap toi, chua bat, da ket thuc; mat hang, "
                       "muc giam, ngay gio, cua hang ap dung; va cap mat hang x cua hang chua co Planned Sales Demand trong thoi "
                       "gian chuong trinh (LS Replenishment chua cong nhu cau). Dung cho cau ve CTKM, va khi de xuat CTKM cho hang "
                       "ban cham de biet mat hang da co chuong trinh chua.",
        "input_schema": {"type": "object", "properties": {
            "status": {"type": "string", "enum": ["dang_chay", "sap_toi", "chua_bat", "da_ket_thuc"],
                       "description": "Bo trong la dang chay va sap toi."},
            "item_no": {"type": "string"}, "location": {"type": "string"}}, "required": []},
    },
    {
        "name": "open_discount_exceptions",
        "description": "Cac exception chiet khau POS dang mo. Dung khi cau hoi lien quan gia, khuyen mai, hoac khi can biet mat hang nao dang duoc giam gia tai cua hang.",
        "input_schema": {"type": "object", "properties": {"item_no": {"type": "string"}}, "required": []},
    },
    {
        "name": "draft_proposal",
        "description": "Ghi mot de xuat vao BC (bang NWV Agent Proposal). Chua thuc thi. Sau buoc nay PolicyEngine quyet dinh tu lam hay cho nguoi duyet. Chi goi khi da du du lieu.",
        "input_schema": {"type": "object", "properties": {
            "action_type": {"type": "string", "enum": ["Transfer", "Markdown", "BlockPurchase", "WriteOff", "Escalate", "ReviewOnly"]},
            "item_no": {"type": "string"}, "from_location": {"type": "string"}, "to_location": {"type": "string"},
            "quantity": {"type": "number"}, "rationale": {"type": "string", "description": "Ly do bang tieng Viet, neu ro con so"}},
            "required": ["action_type", "item_no", "quantity", "rationale"]},
    },
    {
        "name": "ask_human",
        "description": "Hoi lai nguoi dung mot cau duy nhat khi thieu thong tin ma khong tool nao tra loi duoc (vi du ngan sach, so luong khach, ai chiu chi phi). Dung tool nay thay vi doan.",
        "input_schema": {"type": "object", "properties": {"question": {"type": "string"}}, "required": ["question"]},
    },
]


def run_tool(asst: Any, user: dict[str, Any], name: str, args: dict[str, Any]) -> Any:
    gw = asst.gw
    if name == "list_stock":
        loc = args["location"]
        cat = (args.get("category") or "").upper()
        rows = gw.client.query("inventoryHealthLines", [("locationCode", "eq", loc)], top=2000)
        agg: dict[str, dict[str, Any]] = {}
        for r in rows:
            if cat and r.get("itemCategoryCode", "").upper() != cat:
                continue
            a = agg.setdefault(r["itemNo"], {"itemNo": r["itemNo"], "description": r.get("itemDescription"),
                                             "category": r.get("itemCategoryCode"), "qty": 0.0, "value": 0.0,
                                             "avgDailySalesQty": r.get("avgDailySalesQty", 0), "tiers": [], "lots": []})
            a["qty"] += float(r["quantityOnHand"])
            a["value"] += float(r["inventoryValue"])
            a["tiers"].append(r.get("tier"))
            a["lots"].append({"lot": r.get("lotNo"), "qty": r["quantityOnHand"], "expiry": r.get("expirationDate"),
                              "daysToExpiry": r.get("daysToExpiry")})
        for a in agg.values():
            a["unitCost"] = round(a["value"] / a["qty"], 2) if a["qty"] else 0
            a["tier"] = sorted(set(a["tiers"]))
            a.pop("tiers")
            # Gon danh sach lo lai: so lo va lo gan han nhat. Ban day du 6 den 7 nghin ky tu moi dia
            # diem, model goi cho ca sau dia diem trong mot luot la vuot han muc 10.000 token moi
            # phut cua deployment (bat duoc 13/09/2026). Can chi tiet mot lo thi da co lot_info.
            lo = [x for x in a.pop("lots") if x.get("lot")]
            gan = min(lo, key=lambda x: x.get("daysToExpiry") if x.get("daysToExpiry") is not None else 10**6, default=None)
            a["lotCount"] = len(lo)
            if gan:
                a["nearestLot"] = {"lot": gan["lot"], "qty": gan["qty"], "daysToExpiry": gan.get("daysToExpiry")}
        return sorted(agg.values(), key=lambda x: x["itemNo"])
    if name == "stock_by_item":
        return gw.stock_by_location(args["item_no"])
    if name == "find_item":
        return gw.find_item(args["text"], min_score=50) or {"found": False}
    if name == "stores_at_risk":
        rows = gw.risky_suggestions(100)
        if args.get("item_no"):
            rows = [r for r in rows if r["itemNo"] == args["item_no"]]
        if args.get("location"):
            rows = [r for r in rows if r["storeLocationCode"] == args["location"]]
        return [{"store": r["storeLocationCode"], "itemNo": r["itemNo"], "description": r.get("itemDescription"),
                 "onHand": r["storeQtyOnHand"], "inTransit": r.get("storeQtyInTransit", 0),
                 "avgDailySalesQty": r["avgDailySalesQty"], "daysOfCover": r["daysOfCover"],
                 "suggestedQty": r.get("suggestedQty"), "source": r.get("sourceLocationCode") or r.get("vendorNo"),
                 "replenType": r.get("replenType", "Transfer"), "daysOutOfStockInWindow": r.get("daysCensored"),
                 "reason": r.get("reason")} for r in rows]
    if name == "inventory_health":
        # Bang da tinh trong BC; tool chi loc va rut gon, khong tinh lai. 40 dong rui ro cao nhat de khong vuot han muc token.
        conds = []
        if args.get("location"):
            conds.append(("locationCode", "eq", args["location"]))
        if args.get("item_no"):
            conds.append(("itemNo", "eq", args["item_no"]))
        rows = gw.doc("inventoryHealthLines", conds, top=5000)
        tier = args.get("tier") or ""
        if args.get("sort") == "ban_cham":
            # Dung 16/09/2026: "mat hang nao ban cham de dua ra khu trung bay" o S0005, model chi loc SlowMoving (0 dong) roi
            # bao "yen tam". Ban cham la so tuong doi: xep moi dong con ton theo ngay phu giam dan, ban binh quan tang dan.
            rows = [r for r in rows if float(r.get("quantityOnHand") or 0) > 0 and r.get("tier") != "Expired"
                    and (not tier or r.get("tier") == tier)]
            rows.sort(key=lambda r: (-float(r.get("daysOfCover") or 9999), float(r.get("avgDailySalesQty") or 0)))
            # Toi da 2 dong moi mat hang, de danh sach co nhieu mat hang thay vi mot mon o moi cua hang.
            dem: dict[str, int] = {}
            gon = []
            for r in rows:
                dem[r["itemNo"]] = dem.get(r["itemNo"], 0) + 1
                if dem[r["itemNo"]] <= 2:
                    gon.append(r)
            rows = gon
        else:
            rows = [r for r in rows if (r.get("tier") == tier if tier else r.get("tier") != "Healthy")]
            rows.sort(key=lambda r: -int(r.get("riskScore") or 0))
        return {"asOf": gw.today().isoformat(), "matched": len(rows),
                "rows": [{"itemNo": r["itemNo"], "description": r.get("itemDescription"), "location": r["locationCode"],
                          "lot": r.get("lotNo") or "", "tier": r.get("tier"), "qty": r.get("quantityOnHand"),
                          "value": r.get("inventoryValue"), "avgDailySalesQty": r.get("avgDailySalesQty"),
                          "daysSinceLastSale": r.get("daysSinceLastSale"),
                          "daysOfCover": r.get("daysOfCover"), "daysToExpiry": r.get("daysToExpiry"),
                          "expiry": r.get("expirationDate"), "riskScore": r.get("riskScore"), "reason": r.get("riskReason")}
                         for r in rows[:20 if args.get("sort") == "ban_cham" else 40]]}
    if name == "replenishment_suggestions":
        rows = gw.doc("replenishmentSuggestions", [], top=5000)
        # Model hay dien kho trung tam vao location (16/09/2026: "W0003 khong co de xuat nao"); de xuat la cua CUA HANG nen
        # kho trung tam nghia la khong loc.
        if args.get("location") and (args["location"] == gw.central_wh or gw.la_kho(args["location"])):
            args = dict(args, location="")
        if args.get("location"):
            rows = [r for r in rows if r.get("storeLocationCode") == args["location"]]
        if args.get("item_no"):
            rows = [r for r in rows if r.get("itemNo") == args["item_no"]]
        if args.get("only_suggested", True):
            rows = [r for r in rows if float(r.get("suggestedQty") or 0) > 0]
        ra = []
        for r in rows:
            avg = float(r.get("avgDailySalesQty") or 0)
            phu = float(r.get("targetDays") or 0)
            sug = float(r.get("suggestedQty") or 0)
            muc = float(r.get("targetQty") or 0)
            oos = int(r.get("daysCensored") or 0)
            kho = float(r.get("warehouseQtyAvailable") or 0)
            ton = float(r.get("storeQtyOnHand") or 0)
            quyet = str(r.get("lsDecision") or "")
            # Stock Levels (min-max): LS khong ghi ban binh quan va System Suggested Quantity la Maximum Inventory, nen "khong co
            # ban binh quan" va "de xuat bi chan" la binh thuong voi kieu tinh nay, khong phai bat thuong. Danh dau rieng.
            min_max = "Maximum Inventory" in quyet
            flags = []
            if min_max:
                flags.append("kiểu min-max (không có bán bình quân là bình thường)")
            if oos >= 28:
                flags.append("hết hàng quá nửa cửa sổ tính")        # cua so Sales Profile DEFAULT 56 ngay; qua nua la het hang
            if sug > 0 and avg <= 0 and not min_max:
                flags.append("không có bán bình quân mà vẫn đề xuất")
            if avg > 0 and phu > 0 and sug > avg * phu * 1.5:
                flags.append("đề xuất vượt bán bình quân nhân ngày phủ")
            if r.get("replenType", "Transfer") == "Transfer" and muc > 0 and kho < muc:
                flags.append("kho cấp không đủ")
            if ton <= 0:
                flags.append("tồn bằng 0")
            if muc > 0 and sug < muc and not min_max and r.get("replenType", "Transfer") == "Transfer":
                flags.append("bị chia lại vì kho thiếu")
            ra.append({"store": r.get("storeLocationCode"), "itemNo": r.get("itemNo"), "description": r.get("itemDescription"),
                       "suggestedQty": sug, "lsTargetQty": muc, "avgDailySalesQty": avg, "coverDays": phu,
                       "onHand": ton, "inTransit": r.get("storeQtyInTransit", 0), "daysOfCover": r.get("daysOfCover"),
                       "sourceAvailable": kho, "daysOutOfStockInWindow": oos, "decision": r.get("lsDecision") or "",
                       "replenType": r.get("replenType", "Transfer"), "source": r.get("sourceLocationCode") or r.get("vendorNo"),
                       "flags": flags})
        ra.sort(key=lambda x: (-len(x["flags"]), -x["suggestedQty"]))
        return {"asOf": gw.today().isoformat(), "count": len(ra), "windowDays": 56, "rows": ra[:60]}
    if name == "explain_replenishment":
        from .skills import ls_giai_thich
        if gw.is_mock:
            return {"available": False, "reason": "Giai thich theo nhat ky LS chi co khi noi Business Central."}
        kq = ls_giai_thich.giai_thich(gw, args["item_no"], args["location"])
        if not kq:
            return {"available": False, "reason": f"LS chua co dong {args['item_no']} tai {args['location']}."}
        return {"available": True, "itemNo": args["item_no"], "location": args["location"], "suggestedQty": kq.get("de_xuat"),
                "steps": kq.get("y", []), "lsLog": kq.get("nhat_ky_ls", [])[:12]}
    if name == "sales_rate":
        days = int(args.get("days") or 90)
        hist = gw.sales_history(args["item_no"], args.get("location"), days=days)
        cutoff = gw.today().isoformat()
        qty = sum(h["qty"] for h in hist)
        n = len({h["date"] for h in hist}) or 1
        return {"itemNo": args["item_no"], "location": args.get("location") or "ALL", "asOf": cutoff,
                "totalQty": qty, "daysWithSales": n, "avgPerSellingDay": round(qty / n, 2),
                "avgPerCalendarDay": round(qty / days, 2)}
    if name == "promotions":
        from .skills import khuyen_mai
        tt = {args["status"]} if args.get("status") else {"dang_chay", "sap_toi"}
        ds = [c for c in khuyen_mai.tong_hop(khuyen_mai.doc(gw)) if c["trang_thai"] in tt and (c["dang_ban"] or c["trang_thai"] == "da_ket_thuc")
              and (not args.get("item_no") or any(h["no"] == args["item_no"] for h in c["hang"]) or c["tat_ca"])
              and (not args.get("location") or args["location"] in c["cua_hang"])]
        return {"ngay_chot": gw.today().isoformat(), "so_ctkm": len(ds), "ctkm": [
            {**{k: c[k] for k in ("no", "ten", "loai", "trang_thai", "tu", "den", "gio", "muc", "nhom_gia", "cua_hang", "hang",
                                  "nhom", "tat_ca", "su_kien")},
             "chua_co_nhu_cau_ls": [{"item_no": i, "location": l} for i, l in c["thieu"]]} for c in ds[:50]]}
    if name == "lot_info":
        rows = gw.client.query("inventoryHealthLines", [("lotNo", "eq", args["lot_no"])], top=200)
        return [{"itemNo": r["itemNo"], "description": r.get("itemDescription"), "location": r["locationCode"],
                 "qty": r["quantityOnHand"], "value": r["inventoryValue"], "expiry": r.get("expirationDate"),
                 "daysToExpiry": r.get("daysToExpiry"), "tier": r.get("tier"), "riskScore": r.get("riskScore"),
                 "lastSaleDate": r.get("lastSaleDate")} for r in rows]
    if name == "open_discount_exceptions":
        rows = gw.open_exceptions(50)
        if args.get("item_no"):
            rows = [r for r in rows if r.get("itemNo") == args["item_no"]]
        return [{"id": r["id"], "rule": r["ruleCode"], "severity": r["severity"], "store": r["storeNo"],
                 "itemNo": r.get("itemNo"), "date": r["transDate"], "description": r["description"]} for r in rows]
    if name == "draft_proposal":
        return {"staged": True, **args}          # thuc su ghi BC o buoc apply, sau khi nguoi doc xong ke hoach
    if name == "ask_human":
        return {"asked": args["question"]}
    raise ValueError(f"tool khong ton tai: {name}")
