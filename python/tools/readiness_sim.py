"""Chay lai dung logic cua codeunit "NWV Data Readiness Calc" bang Python.

Muc dich: thay truoc bang ket qua trong thế nào truoc khi deploy len sandbox that,
va kiem tra nguong Dat / Can xem lai / Chan co hop ly khong.

Chay hai kich ban: du lieu day du (nhu fixtures POC), va du lieu thieu (nhu nhieu khach hang that).
"""
from __future__ import annotations

import csv
import json
import random
from datetime import date
from pathlib import Path

FIX = Path(__file__).resolve().parent.parent / "bc_agent" / "fixtures"
TODAY = date(2026, 9, 7)


def load():
    lines = json.loads((FIX / "inventory_health_lines.json").read_text(encoding="utf-8"))
    sales = []
    with (FIX / "sales_history.csv").open(encoding="utf-8") as f:
        for r in csv.DictReader(f):
            sales.append({"date": date.fromisoformat(r["date"]), "item_no": r["item_no"],
                          "location_code": r["location_code"], "qty": float(r["qty"])})
    return lines, sales


def degrade(lines, sales, seed=7):
    """Mo phong du lieu thieu: 55% dong khong co lot, 30% lot khong co han dung,
    20% mat hang khong co category, lich su ban chi con 4 thang."""
    rng = random.Random(seed)
    out = []
    for r in lines:
        r = dict(r)
        if rng.random() < 0.55:
            r["lotNo"] = ""
            r["expirationDate"] = None
        elif rng.random() < 0.30:
            r["expirationDate"] = None
        if rng.random() < 0.20:
            r["itemCategoryCode"] = ""
        if rng.random() < 0.10:
            r["unitCostZero"] = True
        out.append(r)
    cut = date(2026, 5, 10)
    return out, [s for s in sales if s["date"] >= cut]


def compute(lines, sales, tracking_pct=1.0, sku_count=0, route_count=1, policy_pct=0.0):
    rows = []

    def add_info(code, group, desc, value, impact):
        rows.append((code, group, desc, str(value), "", "Thông tin", impact))

    def add_pct(code, group, desc, num, den, ok, warn, impact):
        pct = round(num / den * 100, 1) if den else 0.0
        v = "Chặn" if den == 0 or pct < warn else ("Đạt" if pct >= ok else "Cần xem lại")
        rows.append((code, group, desc, f"{num} / {den}", f"{pct}%", v, impact))

    def add_num(code, group, desc, value, unit, ok, warn, impact):
        v = "Đạt" if value >= ok else ("Cần xem lại" if value >= warn else "Chặn")
        rows.append((code, group, desc, f"{value} {unit}", "", v, impact))

    total_open = len(lines)
    with_lot = sum(1 for r in lines if r.get("lotNo"))
    with_exp = sum(1 for r in lines if r.get("expirationDate"))
    lots = {(r["itemNo"], r["lotNo"]) for r in lines if r.get("lotNo")}
    items = {r["itemNo"] for r in lines}
    with_cat = {r["itemNo"] for r in lines if r.get("itemCategoryCode")}
    cats = {r["itemCategoryCode"] for r in lines if r.get("itemCategoryCode")}
    with_cost = {r["itemNo"] for r in lines if not r.get("unitCostZero")}
    locs = {r["locationCode"] for r in lines}

    add_info("DR-01", "Lô và hạn dùng", "Số dòng Item Ledger Entry còn tồn", total_open,
             "Mẫu số của mọi tỷ lệ bên dưới")
    add_pct("DR-02", "Lô và hạn dùng", "Tỷ lệ dòng tồn có Lot No.", with_lot, total_open, 80, 40,
            "Không có lô thì mất hẳn phần theo dõi cận date theo lô")
    add_pct("DR-03", "Lô và hạn dùng", "Tỷ lệ dòng tồn có Expiration Date", with_exp, total_open, 80, 40,
            "Thiếu thì bậc Expired và Near Expiry rỗng")
    add_info("DR-04", "Lô và hạn dùng", "Số lô riêng biệt đang còn tồn", len(lots),
             "Số dòng mà cây phân tầng sẽ chạy trên đó")
    add_pct("DR-05", "Lô và hạn dùng", "Tỷ lệ mặt hàng có Item Tracking Code",
            round(len(items) * tracking_pct), len(items), 80, 40,
            "Không bật thì hàng nhập sau vẫn không có lô")

    first = min(s["date"] for s in sales)
    months = round((TODAY - first).days / 30, 1)
    since = date(TODAY.year, TODAY.month, TODAY.day).toordinal() - 90
    recent = [s for s in sales if s["date"].toordinal() >= since]
    pairs = {(s["item_no"], s["location_code"]) for s in recent}
    add_info("DR-10", "Lịch sử bán", "Ngày bán sớm nhất", first, "Mốc bắt đầu của mọi phép tính lịch sử")
    add_num("DR-11", "Lịch sử bán", "Độ dài lịch sử bán", months, "tháng", 12, 6,
            "Dưới 6 tháng thì tốc độ bán không đáng tin; dưới 12 tháng không bắt được mùa Tết")
    add_info("DR-12", "Lịch sử bán", "Số dòng bán trong 90 ngày gần nhất", len(recent),
             "Cửa sổ mặc định để tính tốc độ bán")
    add_num("DR-13", "Lịch sử bán", "Số cặp mặt hàng và cửa hàng có bán trong 90 ngày",
            len(pairs), "cặp", 20, 5, "Mỗi cặp là một dòng trong bảng bổ sung hàng")

    add_info("DR-19", "Master data", "Số mặt hàng tồn kho chưa bị chặn", len(items), "Mẫu số của hai tỷ lệ dưới")
    add_pct("DR-20", "Master data", "Tỷ lệ mặt hàng có Item Category Code", len(with_cat), len(items), 90, 60,
            "Không phân nhóm thì phải dùng một ngưỡng cận date chung cho cả bar lẫn bonbon")
    add_info("DR-21", "Master data", "Số Item Category đang được dùng", len(cats),
             "Số ngưỡng cận date riêng có thể đặt được")
    add_pct("DR-22", "Master data", "Tỷ lệ mặt hàng có Unit Cost lớn hơn 0", len(with_cost), len(items), 95, 80,
            "Thiếu giá vốn thì không quy tồn ra tiền được")
    add_num("DR-23", "Master data", "Số kho và cửa hàng", len(locs), "địa điểm", 2, 1,
            "Một địa điểm thì không có gì để điều chuyển")

    add_info("DR-30", "Sẵn sàng cho UC5", "Số mặt hàng đã đặt Reordering Policy",
             f"{round(len(items) * policy_pct)} / {len(items)}",
             "Không bắt buộc cho POC, chỉ cho biết Marou dùng phần lập kế hoạch chuẩn tới đâu")
    add_info("DR-31", "Sẵn sàng cho UC5", "Số Stockkeeping Unit đã tạo", sku_count,
             "Bằng 0 thì ngưỡng chuẩn chỉ đặt được ở cấp mặt hàng, không chặn POC")
    add_num("DR-32", "Sẵn sàng cho UC5", "Số Transfer Route đã cấu hình", route_count, "tuyến", 1, 1,
            "Bằng 0 thì không tạo được Transfer Order giữa các địa điểm")
    return rows


def show(title, rows):
    print("=" * 118)
    print(title)
    print("=" * 118)
    print(f"{'Mã':7s} {'Nhóm':17s} {'Nội dung':52s} {'Kết quả':16s} {'%':8s} Kết luận")
    print("-" * 118)
    for code, group, desc, val, pct, verdict, _impact in rows:
        print(f"{code:7s} {group:17s} {desc[:52]:52s} {val:16s} {pct:8s} {verdict}")
    blockers = [r for r in rows if r[5] == "Chặn"]
    warns = [r for r in rows if r[5] == "Cần xem lại"]
    print("-" * 118)
    print(f"Tổng: {len(rows)} dòng. Chặn: {len(blockers)}. Cần xem lại: {len(warns)}.")
    if blockers:
        print("Phải sửa trước khi chốt phạm vi:")
        for b in blockers:
            print(f"  {b[0]} {b[2]} — {b[6]}")
    print()


if __name__ == "__main__":
    lines, sales = load()
    show("KỊCH BẢN 1. Dữ liệu đầy đủ, như bộ fixtures POC",
         compute(lines, sales, tracking_pct=1.0, sku_count=0, route_count=4, policy_pct=0.0))
    dl, ds = degrade(lines, sales)
    show("KỊCH BẢN 2. Dữ liệu thiếu, như nhiều khách hàng thật khi chưa dọn master data",
         compute(dl, ds, tracking_pct=0.45, sku_count=0, route_count=0, policy_pct=0.1))
