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
        "description": "Cac cua hang dang duoi nguong ton, tu bang NWV Repl. Suggestion. Dung de kiem tra rut hang khoi kho trung tam co lam vo ke hoach cua cua hang khac khong.",
        "input_schema": {"type": "object", "properties": {
            "item_no": {"type": "string", "description": "Rong la lay tat ca mat hang"}}, "required": []},
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
        return [{"store": r["storeLocationCode"], "itemNo": r["itemNo"], "description": r.get("itemDescription"),
                 "onHand": r["storeQtyOnHand"], "inTransit": r.get("storeQtyInTransit", 0),
                 "avgDailySalesQty": r["avgDailySalesQty"], "daysOfCover": r["daysOfCover"],
                 "suggestedQty": r.get("suggestedQty"), "reason": r.get("reason")} for r in rows]
    if name == "sales_rate":
        days = int(args.get("days") or 90)
        hist = gw.sales_history(args["item_no"], args.get("location"), days=days)
        cutoff = gw.today().isoformat()
        qty = sum(h["qty"] for h in hist)
        n = len({h["date"] for h in hist}) or 1
        return {"itemNo": args["item_no"], "location": args.get("location") or "ALL", "asOf": cutoff,
                "totalQty": qty, "daysWithSales": n, "avgPerSellingDay": round(qty / n, 2),
                "avgPerCalendarDay": round(qty / days, 2)}
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
