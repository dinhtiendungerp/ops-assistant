"""Baseline va ket qua.

Ly do co file nay: RFP cua Marou bat buoc "success criteria kem baseline KPI", va Vincent
yeu cau ket qua nhin thay duoc truoc khi du an ket thuc. Khong co baseline thi cuoi du an
khong chung minh duoc gi, dashboard dep may cung vo nghia.

Nguyen tac:
  - Baseline tinh tu du lieu lich su cua chinh Marou, khong lay so nganh, khong uoc luong.
  - Ket qua tinh tu viec tro ly da lam trong ky, doi chieu voi dung baseline do.
  - Cho nao chua do duoc thi ghi "chua do duoc", khong dien so nghe hop ly vao.
"""
from __future__ import annotations

from collections import defaultdict
from datetime import datetime
from typing import Any

from ..cards import Card, fmt_vnd
from . import Delivery
from .investigate import _stockout_days

SKILL = "kpi"
BAD_TIERS = ("SlowMoving", "Excess", "NearExpiry", "Expired")


_STOCKOUT_CACHE: dict[tuple, tuple[int, float]] = {}


def _stockout_baseline(gw: Any, today: Any, pairs: tuple) -> tuple[int, float]:
    """Quet lich su ban de dem ngay dut hang.

    Doc MOT lan cho ca 74 cap roi nhom trong Python, khong hoi BC tung cap mot. Ban cu goi
    `sales_history(item, store)` trong vong lap: tren BC that moi luot mat 1,7 giay nen chi
    rieng ham nay ngon 129 giay, va do la ca thoi gian nguoi dung ngoi cho khi bam nut
    Business Central. Do duoc ngay 13/09/2026.

    Lich su ban khong doi trong mot phien nen van nho lai ket qua."""
    key = (id(type(gw.client)), today.isoformat(), pairs)
    if key in _STOCKOUT_CACHE:
        return _STOCKOUT_CACHE[key]
    theo_cap: dict[tuple[str, str], list[dict[str, Any]]] = defaultdict(list)
    can = set(pairs)
    for r in gw.sales_history(days=120):
        k = (r["location_code"], r["item_no"])
        if k in can:
            theo_cap[k].append(r)
    days, qty = 0, 0.0
    for rows in theo_cap.values():
        gaps = _stockout_days(rows, today, weeks=12)
        if not gaps:
            continue
        avg = sum(r["qty"] for r in rows) / max(len({r["date"] for r in rows}), 1)
        days += len(gaps)
        qty += len(gaps) * avg
    _STOCKOUT_CACHE[key] = (days, round(qty))
    return _STOCKOUT_CACHE[key]


def baseline(asst: Any) -> dict[str, Any]:
    """Anh chup hien trang truoc khi tro ly lam gi. Tinh mot lan roi giu lai."""
    cached = asst.mem.recall("baseline")
    if cached:
        return cached
    gw, today = asst.gw, asst.gw.today()

    # 1. Bo sung cua hang: so cap dang duoi nguong, va so ngay dut hang 12 tuan qua
    risky = gw.risky_suggestions(200)
    pairs = {(r["storeLocationCode"], r["itemNo"]) for r in gw.doc("replenishmentSuggestions", [], top=5000)}
    lost_days, lost_qty = _stockout_baseline(gw, today, tuple(sorted(pairs)))

    # 2. Suc khoe ton: gia tri dang nam o cac tang xau
    health = gw.doc("inventoryHealthLines", [], top=5000)
    bad_value = sum(float(h["inventoryValue"]) for h in health if h.get("tier") in BAD_TIERS)
    by_tier: dict[str, float] = defaultdict(float)
    for h in health:
        if h.get("tier") in BAD_TIERS:
            by_tier[h["tier"]] += float(h["inventoryValue"])

    # 3. Ky luat gia tren POS
    exc = gw.doc("discountExceptions", [], top=1000)
    leak = sum(float(e.get("discountAmount") or 0) for e in exc)

    data = {
        "as_of": today.isoformat(),
        "repl": {"pairs": len(pairs), "at_risk": len(risky), "stockout_days_12w": lost_days,
                 "lost_qty": lost_qty},
        "health": {"bad_value": bad_value, "by_tier": dict(by_tier),
                   "lines": len([h for h in health if h.get("tier") in BAD_TIERS])},
        "discount": {"exceptions": len(exc), "leak_vnd": leak,
                     "explained": len([e for e in exc if e.get("status") in ("Explained", "Confirmed", "Dismissed")])},
    }
    asst.mem.remember("baseline", data)
    return data


def result(asst: Any) -> dict[str, Any]:
    """Tro ly da lam duoc gi tinh den luc nay, do bang chinh don vi cua baseline."""
    props = asst.mem.proposals()
    done = [p for p in props if p["status"] == "Executed"]
    auto = [p for p in done if str(p.get("approver", "")).startswith("agent:")]
    moved = sum(float(p.get("value_vnd") or 0) for p in done if p["action_type"] == "Transfer")
    covered = sum(float(p.get("value_vnd") or 0) for p in props if p["action_type"] in ("BlockPurchase", "Markdown", "WriteOff", "ReviewOnly"))
    lead: list[float] = []
    for p in done:
        if p.get("approved_at") and p.get("created_at"):
            try:
                dt = (datetime.fromisoformat(p["approved_at"]) - datetime.fromisoformat(p["created_at"])).total_seconds() / 60
                lead.append(max(dt, 0))
            except ValueError:
                pass
    exc = asst.gw.client.query("discountExceptions", [], top=1000)
    answered = [e for e in exc if e.get("status") in ("Explained", "Confirmed", "Dismissed")]
    return {
        "proposals": len(props), "executed": len(done), "auto": len(auto),
        "rejected": len([p for p in props if p["status"] in ("Rejected", "Cancelled")]),
        "moved_vnd": moved, "covered_vnd": covered,
        "lead_minutes": round(sum(lead) / len(lead), 1) if lead else None,
        "lead_n": len(lead),
        "explained": len(answered),
    }


def _pct(a: float, b: float) -> str:
    return f"{a / b * 100:.0f}%" if b else "-"


def card(asst: Any) -> Card:
    b, r = baseline(asst), result(asst)
    facts = [
        ("Baseline chốt ngày", b["as_of"]),
        ("Đứt hàng 12 tuần qua", f"{b['repl']['stockout_days_12w']} ngày cửa hàng, ước {b['repl']['lost_qty']:.0f} sản phẩm không bán được"),
        ("Đang dưới ngưỡng", f"{b['repl']['at_risk']}/{b['repl']['pairs']} cặp cửa hàng và mặt hàng"),
        ("Tồn xấu", f"{fmt_vnd(b['health']['bad_value'])} trên {b['health']['lines']} dòng"),
        ("Chiết khấu tay vượt ngưỡng", f"{fmt_vnd(b['discount']['leak_vnd'])} trên {b['discount']['exceptions']} lượt"),
        ("Có giải trình lúc bắt đầu", f"{b['discount']['explained']}/{b['discount']['exceptions']}"),
        ("——— Sau khi trợ lý chạy ———", ""),
        ("Đề xuất đã tạo", f"{r['proposals']}, trong đó {r['executed']} đã thực thi ({r['auto']} trợ lý tự làm)"),
        ("Giá trị hàng đã điều chuyển", fmt_vnd(r["moved_vnd"])),
        ("Giá trị tồn xấu đã có hướng xử lý", f"{fmt_vnd(r['covered_vnd'])} ({_pct(r['covered_vnd'], b['health']['bad_value'])} tồn xấu)"),
        ("Từ lúc phát hiện đến khi có chứng từ",
         ("dưới 1 phút" if r["lead_minutes"] < 1 else f"{r['lead_minutes']} phút") + f" (trung bình {r['lead_n']} việc)"
         if r["lead_minutes"] is not None else "chưa đo được"),
        ("Đã có giải trình", f"{r['explained']}/{b['discount']['exceptions']}"),
        ("Bị hoàn tác hoặc từ chối", str(r["rejected"])),
    ]
    body = ("Baseline lấy từ chính dữ liệu lịch sử trong BC, không lấy số ngành. Ba dòng cuối là chỉ số năng suất, "
            "phần còn lại là chỉ số kết quả kinh doanh. Cột thiếu dữ liệu thì ghi chưa đo được chứ không điền số ước lượng.\n\n"
            "Ở buổi demo này baseline chạy trên dữ liệu mô phỏng. Trên hệ thống thật, cùng cách tính này "
            "đọc lịch sử tồn kho và bán hàng của Marou rồi cho ra bộ số để hai bên chốt trước khi bắt đầu.")
    return Card(title="Baseline và kết quả", body=body, facts=facts, kind="brief", ref="kpi")


def run(asst: Any, user: dict[str, Any]) -> list[Delivery]:
    return [Delivery(user["user_id"], "Bảng baseline và kết quả tính tới lúc này.", card(asst), SKILL, "kpi")]
