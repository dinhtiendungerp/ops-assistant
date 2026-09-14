"""Skill Investigate: tra loi cau hoi mo bang cach tu di nhieu buoc.

Khac cac skill kia: khong co rule "neu A thi B". Tro ly nhan mot cau hoi khong doan truoc duoc
("sao Da Nang cu het Ba Ria 76"), tu chon buoc tiep theo, dung khi du bang chung, roi de xuat sua.

Phan phan tich la Python thuan nen chay duoc khong can model. Model (khi bat live) lam hai viec:
hieu cau hoi mo, va viet ket luan. So lieu khong bao gio do model tinh.
"""
from __future__ import annotations

import statistics
from collections import defaultdict
from datetime import date, timedelta
from typing import Any

from ..cards import Action, Card, fmt_qty
from . import Delivery

SKILL = "investigate"
WEEKDAYS = ["Thứ Hai", "Thứ Ba", "Thứ Tư", "Thứ Năm", "Thứ Sáu", "Thứ Bảy", "Chủ nhật"]


def _weekday_profile(rows: list[dict[str, Any]], today: date, weeks: int = 12) -> dict[int, float]:
    """Ban binh quan theo thu trong tuan. Ngay khong co dong ban tinh la 0, khong bo qua."""
    since = today - timedelta(weeks=weeks)
    by_day: dict[date, float] = defaultdict(float)
    for r in rows:
        d = date.fromisoformat(r["date"])
        if d >= since:
            by_day[d] += r["qty"]
    by_wd: dict[int, list[float]] = defaultdict(list)
    for i in range((today - since).days + 1):
        d = since + timedelta(days=i)
        by_wd[d.weekday()].append(by_day.get(d, 0.0))
    return {wd: statistics.fmean(v) for wd, v in by_wd.items() if v}


def _stockout_days(rows: list[dict[str, Any]], today: date, weeks: int = 12) -> list[date]:
    """Ngay khong ban duoc gi trong khi cac ngay cung thu khac deu ban: dau hieu het hang."""
    since = today - timedelta(weeks=weeks)
    by_day: dict[date, float] = defaultdict(float)
    for r in rows:
        d = date.fromisoformat(r["date"])
        if d >= since:
            by_day[d] += r["qty"]
    prof = _weekday_profile(rows, today, weeks)
    out = []
    for i in range((today - since).days + 1):
        d = since + timedelta(days=i)
        expected = prof.get(d.weekday(), 0)
        if expected >= 1 and by_day.get(d, 0.0) == 0:
            out.append(d)
    return out


def run(asst, user, item_no: str, store: str) -> list[Delivery]:
    """Vong dieu tra: moi buoc dua tren ket qua buoc truoc, dung khi du ket luan."""
    gw = asst.gw
    today = gw.today()
    steps: list[str] = []
    item = next((i for i in gw.items() if i["itemNo"] == item_no), {"itemNo": item_no, "description": item_no})

    # Buoc 1: co that la hay het hang khong
    rows = gw.sales_history(item_no, store)
    steps.append(f"Đọc {len(rows)} dòng bán 6 tháng của {item['description']} tại {store}")
    gaps = _stockout_days(rows, today)
    if not gaps:
        return [Delivery(user["user_id"], f"Tôi không thấy ngày nào {store} đứt hàng {item['description']} trong 12 tuần. Có thể vấn đề nằm ở chỗ khác, bạn mô tả rõ hơn giúp tôi.", skill=SKILL)]

    # Buoc 2: dut hang roi vao thu nao
    by_wd: dict[int, int] = defaultdict(int)
    for d in gaps:
        by_wd[d.weekday()] += 1
    worst = sorted(by_wd.items(), key=lambda kv: -kv[1])[:3]
    steps.append(f"{len(gaps)} ngày đứt hàng, tập trung vào {', '.join(WEEKDAYS[w] for w, _ in worst)}")

    # Buoc 3: nhu cau theo thu co lech khong
    prof = _weekday_profile(rows, today)
    wk = statistics.fmean([prof.get(i, 0) for i in range(5)]) or 0.001
    we = statistics.fmean([prof.get(i, 0) for i in (5, 6)])
    ratio = we / wk
    steps.append(f"Bán ngày thường {wk:.1f}/ngày, cuối tuần {we:.1f}/ngày, gấp {ratio:.2f} lần")

    # Buoc 4: hang ve vao thu nao
    ship_days = [date.fromisoformat(t["createdAt"][:10]).weekday() for t in (gw._transfers.values() if gw.is_mock else [])
                 if t.get("toLocationCode") == store and t.get("itemNo") == item_no]
    sug = gw.suggestion(store, item_no)
    doc = sug["daysOfCover"] if sug else None

    # Buoc 5: ket luan + de xuat
    findings, fix = [], ""
    # Chi noi "co quy luat" khi so lieu du manh. Khong thi noi thang la khong thay quy luat,
    # con hon dua ket luan nghe hop ly tu 3 quan sat.
    weekend_pattern = ratio > 1.2
    top_share = worst[0][1] / len(gaps) if gaps else 0
    concentrated = len(gaps) >= 6 and top_share >= 0.35

    if weekend_pattern:
        findings.append(f"cuối tuần bán gấp {ratio:.2f} lần ngày thường")
    if doc is not None and doc < 7:
        findings.append(f"tồn hiện tại chỉ đủ {doc} ngày")

    if weekend_pattern and concentrated and worst[0][0] in (5, 6, 0):
        findings.append(f"{worst[0][1]}/{len(gaps)} ngày đứt rơi vào {WEEKDAYS[worst[0][0]]}, tức là hết trước hoặc trong cuối tuần")
        fix = ("Chuyển hàng về trước cuối tuần thay vì đầu tuần, và nâng mục tiêu tồn cho hai ngày cuối tuần "
               f"lên khoảng {we * 2:.0f} sản phẩm.")
    elif weekend_pattern:
        findings.append(f"ngày đứt rải đều các thứ, chưa đủ tập trung để kết luận quy luật ({worst[0][1]}/{len(gaps)} ngày nhiều nhất)")
        fix = f"Nâng mục tiêu tồn cuối tuần lên khoảng {we * 2:.0f} sản phẩm, vì cuối tuần bán nhiều hơn hẳn."
    else:
        findings.append("không thấy chênh lệch rõ giữa ngày thường và cuối tuần")
        fix = "Nâng ngưỡng đặt lại hàng cho cặp cửa hàng và mặt hàng này. Cần thêm dữ liệu để nói được nguyên nhân."

    conclusion = asst.write_rationale(
        f"{store} đứt hàng {item['description']} {len(gaps)} ngày trong 12 tuần, "
        + ", ".join(findings) + ". " + fix)

    card = Card(title=f"Điều tra: {item['description']} tại {store}", body=conclusion,
                facts=[("Ngày đứt hàng / 12 tuần", str(len(gaps))),
                       ("Dồn vào", ", ".join(f"{WEEKDAYS[w]} ({n})" for w, n in worst)),
                       ("Ngày thường / cuối tuần", f"{wk:.1f} / {we:.1f} mỗi ngày"),
                       ("Tồn hiện tại", f"{doc} ngày" if doc is not None else "không có dữ liệu"),
                       ("Bước tôi đã đi", f"{len(steps)} bước")],
                ref=f"inv|{store}|{item_no}", kind="info",
                actions=[Action("inv_apply", "Áp dụng đề xuất", "positive"), Action("inv_steps", "Xem tôi đã tra gì")])
    asst.mem.remember(f"inv|{store}|{item_no}", {"steps": steps, "gaps": len(gaps), "ratio": ratio,
                                                 "weekend_target": round(we * 2), "item_no": item_no, "store": store})
    return [Delivery(user["user_id"], conclusion, card, SKILL, f"inv|{store}|{item_no}")]


def show_steps(asst, user, ref: str) -> list[Delivery]:
    data = asst.mem.recall(ref)
    if not data:
        return [Delivery(user["user_id"], "Tôi không còn giữ chi tiết lần tra này.", skill=SKILL)]
    lines = "\n".join(f"{i}. {s}" for i, s in enumerate(data["steps"], 1))
    return [Delivery(user["user_id"], f"Các bước tôi đã đi:\n{lines}", skill=SKILL, ref=ref)]


def apply_fix(asst, user, ref: str) -> list[Delivery]:
    data = asst.mem.recall(ref)
    if not data:
        return [Delivery(user["user_id"], "Tôi không còn giữ đề xuất này.", skill=SKILL)]
    key = f"{data['store']}|{data['item_no']}"
    asst.mem.set_override(key, {"weekend_target": data["weekend_target"], "ship_before_weekend": True,
                                "set_by": user["user_id"], "source": ref})
    return [Delivery(user["user_id"],
                     f"Đã đặt riêng cho {data['store']} và {data['item_no']}: mục tiêu tồn cuối tuần {data['weekend_target']}, "
                     "và ưu tiên chuyển hàng trước cuối tuần. Tôi áp dụng từ lần tính tiếp theo và sẽ báo lại sau 4 tuần xem có đỡ không.",
                     skill=SKILL, ref=ref)]
