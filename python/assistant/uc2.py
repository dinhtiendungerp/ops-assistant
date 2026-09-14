"""Man hinh UC2 Inventory Health cho web demo.

Day la lop view, khong tra ve Delivery nhu cac skill khac. No phuc vu bon man hinh:
  summary   : dai tong tien va sau o tang, tuc cau mo dau cua buoi demo
  lines     : danh sach dong ton theo tang, xep theo Risk Score
  trace     : mo mot dong ra cho thay con so den tu dau, va bac nao cua cay phan tang khop
  readiness : do phu du lieu, chay lai dung logic codeunit NWV Data Readiness Calc

Muc dich cua trace: trong buoi demo, buoc lam nguoi ta tin khong phai bang mau dep,
ma la mo mot dong ra doi chieu voi chung tu goc truoc mat ho.
"""
from __future__ import annotations

from .cards import fmt_vnd

from collections import defaultdict
from datetime import date, timedelta
from typing import Any

TIER_ORDER = ["Expired", "NearExpiry", "StockOutRisk", "SlowMoving", "Excess", "Healthy"]
TIER_LABEL = {
    "Expired": "Đã quá hạn",
    "NearExpiry": "Cận date",
    "StockOutRisk": "Sắp hết hàng",
    "SlowMoving": "Chậm luân chuyển",
    "Excess": "Dư tồn",
    "Healthy": "Trong ngưỡng",
}
BAD_TIERS = ["Expired", "NearExpiry", "SlowMoving", "Excess"]

# Nguong mac dinh, khop voi NWV Agent Setup
SETUP = {"near_expiry_days": 45, "stockout_days": 7, "slow_days": 60, "excess_days": 90, "history_days": 90}


def _all(asst: Any) -> list[dict[str, Any]]:
    # Qua `gw.doc` de ba man hinh (tong quan, danh sach, do phu) dung chung mot lan doc.
    return asst.gw.doc("inventoryHealthLines", [], top=5000)


def summary(asst: Any) -> dict[str, Any]:
    rows = _all(asst)
    by_tier: dict[str, dict[str, Any]] = {t: {"tier": t, "label": TIER_LABEL[t], "lines": 0, "value": 0.0, "qty": 0.0}
                                          for t in TIER_ORDER}
    for r in rows:
        t = r.get("tier")
        if t not in by_tier:
            continue
        by_tier[t]["lines"] += 1
        by_tier[t]["value"] += float(r["inventoryValue"])
        by_tier[t]["qty"] += float(r["quantityOnHand"])
    total = sum(v["value"] for v in by_tier.values())
    bad = sum(by_tier[t]["value"] for t in BAD_TIERS)
    return {
        "asOf": asst.gw.today().isoformat(),
        "totalValue": total,
        "totalLines": len(rows),
        "badValue": bad,
        "badPct": round(bad / total * 100, 1) if total else 0.0,
        "badLines": sum(by_tier[t]["lines"] for t in BAD_TIERS),
        "tiers": [by_tier[t] for t in TIER_ORDER],
    }


def lines(asst: Any, tier: str = "", limit: int = 200) -> list[dict[str, Any]]:
    rows = _all(asst)
    if tier:
        rows = [r for r in rows if r.get("tier") == tier]
    rank = {t: i for i, t in enumerate(TIER_ORDER)}
    rows.sort(key=lambda r: (-int(r.get("riskScore") or 0), rank.get(r.get("tier"), 9)))
    return rows[:limit]


def _cascade(r: dict[str, Any]) -> list[dict[str, Any]]:
    """Sau bac cua cay phan tang, danh dau bac nao khop va vi sao. Dung thu tu voi codeunit AL."""
    dte = r.get("daysToExpiry")
    doc = float(r.get("daysOfCover") or 0)
    dsls = int(r.get("daysSinceLastSale") or 0)
    avg = float(r.get("avgDailySalesQty") or 0)
    steps = [
        {"step": 1, "tier": "Expired", "test": "Days To Expiry nhỏ hơn 0",
         "actual": f"Days To Expiry = {dte}", "hit": dte is not None and dte < 0},
        {"step": 2, "tier": "NearExpiry", "test": f"Days To Expiry nhỏ hơn hoặc bằng {SETUP['near_expiry_days']}",
         "actual": f"Days To Expiry = {dte}", "hit": dte is not None and 0 <= dte <= SETUP["near_expiry_days"]},
        {"step": 3, "tier": "StockOutRisk", "test": f"Days of Cover nhỏ hơn {SETUP['stockout_days']} và có bán",
         "actual": f"Days of Cover = {doc}, bán bình quân {avg}/ngày", "hit": doc < SETUP["stockout_days"] and avg > 0},
        {"step": 4, "tier": "SlowMoving", "test": f"Days Since Last Sale từ {SETUP['slow_days']} trở lên",
         "actual": f"Days Since Last Sale = {dsls}", "hit": dsls >= SETUP["slow_days"]},
        {"step": 5, "tier": "Excess", "test": f"Days of Cover lớn hơn {SETUP['excess_days']}",
         "actual": f"Days of Cover = {doc}", "hit": doc > SETUP["excess_days"]},
        {"step": 6, "tier": "Healthy", "test": "Không khớp bậc nào ở trên", "actual": "", "hit": True},
    ]
    stopped = False
    for s in steps:
        if stopped:
            s["hit"] = False
            s["state"] = "khong xet"
        elif s["hit"]:
            s["state"] = "khớp, dừng ở đây"
            stopped = True
        else:
            s["state"] = "không khớp, xét tiếp"
    return steps


def trace(asst: Any, line_id: str) -> dict[str, Any]:
    """Mo mot dong ra: con so den tu dau, tinh the nao, va bac nao cua cay khop."""
    # Lay tu ban danh sach da nho thay vi mot lenh GET rieng: tren BC that lenh do mat 1,5 giay,
    # va nguoi dung vua bam tu chinh danh sach do ra nen no chac chan dang nam trong ban nho.
    r = next((x for x in _all(asst) if x.get("id") == line_id), None)
    if r is None:
        r = asst.gw.client.get("inventoryHealthLines", line_id)
    today = asst.gw.today()
    since = today - timedelta(days=SETUP["history_days"])

    hist = [h for h in asst.gw.sales_history(r["itemNo"], r["locationCode"], days=SETUP["history_days"] + 30)
            if date.fromisoformat(h["date"]) >= since]
    hist.sort(key=lambda h: h["date"], reverse=True)
    sold = sum(h["qty"] for h in hist)
    qty = float(r["quantityOnHand"])
    unit = round(float(r["inventoryValue"]) / qty, 2) if qty else 0
    # Con so tren dong la con so cua bang ket qua (AL hoac ban doi chieu), khong tinh lai o day.
    avg = float(r.get("avgDailySalesQty") or 0)
    censored = int(r.get("daysCensored") or 0)
    counted = SETUP["history_days"] - censored
    basis = str(r.get("demandBasis") or "sale")
    days_txt = (f"{SETUP['history_days']} ngày trừ {censored} ngày hết hàng bị loại, còn {counted}"
                if censored else f"{SETUP['history_days']} ngày")
    if basis == "outflow":
        demand_row = {"label": f"Lượng xuất {SETUP['history_days']} ngày qua",
                      "formula": f"Tổng Quantity các dòng xuất (Sale, Negative Adjmt., Transfer) tại {r['locationCode']}, "
                                 f"từ {since.isoformat()} tới {today.isoformat()}. Kho trung tâm tính theo lượng xuất, "
                                 f"trong đó bán sỉ tại chỗ là {sold:.0f} trên {len(hist)} dòng",
                      "value": f"{avg * counted:.0f}"}
        avg_formula = f"{avg * counted:.0f} chia {days_txt}"
    else:
        demand_row = {"label": f"Đã bán {SETUP['history_days']} ngày qua",
                      "formula": f"Tổng Quantity của Item Ledger Entry loại Sale, từ {since.isoformat()} tới {today.isoformat()}, tại {r['locationCode']}",
                      "value": f"{sold:.0f} trên {len(hist)} dòng bán"}
        avg_formula = f"{sold:.0f} chia {days_txt}"

    steps_calc = [
        {"label": "Tồn của lô này",
         "formula": "Tổng Remaining Quantity của Item Ledger Entry còn mở, lọc theo Item, Location, Lot",
         "value": f"{qty:.0f} {r.get('baseUnitOfMeasure', '')}"},
        {"label": "Giá trị tồn", "formula": f"Tồn nhân giá vốn đơn vị {fmt_vnd(unit)}",
         "value": fmt_vnd(float(r["inventoryValue"]))},
        demand_row,
        {"label": "Bán bình quân ngày", "formula": avg_formula, "value": f"{avg}"},
        {"label": "Days of Cover", "formula": f"{qty:.0f} chia {avg}" if avg else "Không bán được gì nên không tính được",
         "value": str(r.get("daysOfCover"))},
        {"label": "Days To Expiry", "formula": f"{r.get('expirationDate')} trừ {today.isoformat()}",
         "value": str(r.get("daysToExpiry"))},
        {"label": "Days Since Last Sale", "formula": f"{today.isoformat()} trừ ngày bán gần nhất {r.get('lastSaleDate') or 'không có'}",
         "value": str(r.get("daysSinceLastSale"))},
    ]
    # Lich su ban dua ra de doi chieu: nguoi xem cong nham vai ngay la ra duoc con so binh quan
    # o tren. Kho trung tam tinh theo luong xuat nen phai noi ro, khong thi nguoi ta doi chieu
    # voi dong Sale roi thay lech.
    ban = hist[:14]
    doi_chieu = {
        "nhan": "Lượng xuất" if basis == "outflow" else "Đã bán",
        "diaDiem": r["locationCode"],
        "soNgay": len(ban),
        "tong": round(sum(h["qty"] for h in ban), 3),
        "giaiThich": (
            f"{len(ban)} ngày gần nhất tại {r['locationCode']}. "
            + ("Đây là kho trung tâm nên số đếm là lượng xuất, gồm bán sỉ tại chỗ và hàng chuyển "
               "ra cửa hàng, không phải chỉ dòng Sale."
               if basis == "outflow" else
               "Cộng cả cửa sổ 90 ngày rồi chia số ngày được tính, ra bán bình quân ở bảng trên.")
            + (f" Đã loại {censored} ngày hết hàng khỏi mẫu số." if censored else "")
        ),
        "dong": ban,
    }
    return {"line": r, "calc": steps_calc, "cascade": _cascade(r),
            "recentSales": ban, "doiChieu": doi_chieu, "setup": SETUP}


# ---------------------------------------------------------------- do phu du lieu
def readiness(asst: Any) -> list[dict[str, Any]]:
    """Chay lai dung logic codeunit NWV Data Readiness Calc, nhung tren du lieu mock.
    Tren sandbox that thi con so nay do chinh codeunit AL sinh ra, khong phai doan nay."""
    rows = _all(asst)
    out: list[dict[str, Any]] = []

    def info(code, group, desc, value, impact):
        out.append({"code": code, "group": group, "desc": desc, "value": str(value),
                    "pct": None, "verdict": "Thông tin", "impact": impact})

    def pct(code, group, desc, num, den, ok, warn, impact):
        p = round(num / den * 100, 1) if den else 0.0
        v = "Chặn" if den == 0 or p < warn else ("Đạt" if p >= ok else "Cần xem lại")
        out.append({"code": code, "group": group, "desc": desc, "value": f"{num} / {den}",
                    "pct": p, "verdict": v, "impact": impact})

    def num(code, group, desc, value, unit, ok, warn, impact):
        v = "Đạt" if value >= ok else ("Cần xem lại" if value >= warn else "Chặn")
        out.append({"code": code, "group": group, "desc": desc, "value": f"{value} {unit}",
                    "pct": None, "verdict": v, "impact": impact})

    total = len(rows)
    with_lot = sum(1 for r in rows if r.get("lotNo"))
    with_exp = sum(1 for r in rows if r.get("expirationDate"))
    lots = {(r["itemNo"], r["lotNo"]) for r in rows if r.get("lotNo")}
    items = {r["itemNo"] for r in rows}
    with_cat = {r["itemNo"] for r in rows if r.get("itemCategoryCode")}
    cats = {r["itemCategoryCode"] for r in rows if r.get("itemCategoryCode")}
    locs = {r["locationCode"] for r in rows}

    info("DR-01", "Lô và hạn dùng", "Số dòng Item Ledger Entry còn tồn", total, "Mẫu số của mọi tỷ lệ bên dưới")
    pct("DR-02", "Lô và hạn dùng", "Tỷ lệ dòng tồn có Lot No.", with_lot, total, 80, 40,
        "Không có lô thì phân tầng chỉ chạy ở mức Item và Location, mất hẳn phần theo dõi cận date theo lô")
    pct("DR-03", "Lô và hạn dùng", "Tỷ lệ dòng tồn có Expiration Date", with_exp, total, 80, 40,
        "Thiếu thì bậc Expired và Near Expiry của cây phân tầng rỗng, tức mất phần giá trị nhất của UC2")
    info("DR-04", "Lô và hạn dùng", "Số lô riêng biệt đang còn tồn", len(lots), "Số dòng mà cây phân tầng chạy trên đó")

    # Truoc day doc ca 400 ngay lich su ban chi de lay ngay som nhat, mat 12 giay tren BC that.
    # Gio ngay som nhat lay bang mot dong, con phan con lai chi can cua so 90 ngay, va cua so do
    # cac man hinh khac cung doc nen dung chung ban nho.
    ngay_dau = asst.gw.ngay_ban_dau_tien()
    recent = asst.gw.sales_history(days=90)
    if ngay_dau:
        first = date.fromisoformat(ngay_dau)
        months = round((asst.gw.today() - first).days / 30, 1)
        pairs = {(h["item_no"], h["location_code"]) for h in recent}
        info("DR-10", "Lịch sử bán", "Ngày bán sớm nhất", first.isoformat(), "Mốc bắt đầu của mọi phép tính lịch sử")
        num("DR-11", "Lịch sử bán", "Độ dài lịch sử bán", months, "tháng", 12, 6,
            "Dưới 6 tháng thì tốc độ bán không đáng tin; dưới 12 tháng không bắt được mùa Tết")
        info("DR-12", "Lịch sử bán", "Số dòng bán trong 90 ngày gần nhất", len(recent), "Cửa sổ tính tốc độ bán")
        num("DR-13", "Lịch sử bán", "Số cặp mặt hàng và cửa hàng có bán trong 90 ngày", len(pairs), "cặp", 20, 5,
            "Mỗi cặp là một dòng trong bảng bổ sung hàng")

    info("DR-19", "Master data", "Số mặt hàng tồn kho", len(items), "Mẫu số của tỷ lệ dưới")
    pct("DR-20", "Master data", "Tỷ lệ mặt hàng có Item Category Code", len(with_cat), len(items), 90, 60,
        "Không phân nhóm thì phải dùng một ngưỡng cận date chung cho cả thanh bar lẫn bonbon")
    info("DR-21", "Master data", "Số Item Category đang dùng", len(cats), "Số ngưỡng cận date riêng có thể đặt")
    num("DR-23", "Master data", "Số kho và cửa hàng", len(locs), "địa điểm", 2, 1,
        "Một địa điểm thì không có gì để điều chuyển")
    return out
