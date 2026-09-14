"""UC1 Demand Planning: nhu cầu thật của một cặp cửa hàng và mặt hàng.

Vấn đề nghiêm túc nhất của use case này không phải chọn mô hình, mà là số liệu đầu vào bị bóp méo
theo hai hướng ngược nhau, và cả hai đều làm dự báo sai một cách khó phát hiện:

  1. Ngày đứt hàng bị đọc thành ngày nhu cầu bằng không. Không bán được vì không còn hàng
     thì không phải là không có nhu cầu. Đọc nhầm chỗ này làm dự báo tụt xuống, tụt xuống thì
     lại đặt ít, đặt ít thì lại đứt hàng. Càng chạy càng sai.
  2. Ngày có sự kiện một lần bị đọc thành nhu cầu bình thường. Đọc nhầm chỗ này làm dự báo
     vống lên và tồn kho phình ra sau đó.

Cả hai đều cần một con người nói ra chuyện gì đã xảy ra. Dữ liệu trong BC không chứa
"hội chợ trước cửa hàng tháng 8". Đó là lý do module này nhận thêm một danh sách cửa sổ ngoại lệ
do người nhập, và tính lại ngay khi có cửa sổ mới.

Mô hình giữ ở mức giải thích được: nhu cầu ngày bằng trung bình các ngày dùng được, nhân hệ số
thứ trong tuần. Nếu sau này dùng mô hình phức tạp hơn thì nó phải thắng cái này trên cùng holdout.
"""
from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass, field
from datetime import date, timedelta
from statistics import fmean
from typing import Any

from ..cards import Action, Card
from . import Delivery

SKILL = "demand"
WINDOW = 28          # so ngay dung de tinh nhu cau hien tai
LOOKBACK_WEEKS = 12  # so tuan dung de do dut hang
KEY = "demand_exceptions"


@dataclass
class DemandView:
    item_no: str
    location: str
    item_desc: str
    window_from: date
    window_to: date
    sold: float
    stockout_days: list[date] = field(default_factory=list)
    excluded_days: list[date] = field(default_factory=list)
    exceptions: list[dict[str, Any]] = field(default_factory=list)
    naive_daily: float = 0.0
    corrected_daily: float = 0.0
    usable_days: int = 0
    window: int = WINDOW
    widened: bool = False

    @property
    def uplift_pct(self) -> float:
        return (self.corrected_daily / self.naive_daily - 1) * 100 if self.naive_daily else 0.0

    @property
    def forecast_14(self) -> float:
        return self.corrected_daily * 14


# ---------------------------------------------------------------- cua so ngoai le
def exceptions(asst: Any, item_no: str, location: str) -> list[dict[str, Any]]:
    all_ex = asst.mem.recall(KEY) or {}
    return all_ex.get(f"{location}|{item_no}", [])


def add_exception(asst: Any, item_no: str, location: str, d_from: date, d_to: date,
                  reason: str, by: str) -> None:
    all_ex = asst.mem.recall(KEY) or {}
    key = f"{location}|{item_no}"
    all_ex.setdefault(key, []).append({"from": d_from.isoformat(), "to": d_to.isoformat(),
                                       "reason": reason, "by": by, "at": asst.mem.now().isoformat()})
    asst.mem.remember(KEY, all_ex)


# ---------------------------------------------------------------- tinh
def _daily(rows: list[dict[str, Any]]) -> dict[date, float]:
    by_day: dict[date, float] = defaultdict(float)
    for r in rows:
        by_day[date.fromisoformat(r["date"])] += r["qty"]
    return by_day


def stockout_days(by_day: dict[date, float], today: date, weeks: int = LOOKBACK_WEEKS) -> list[date]:
    """Xap xi: ngay khong ban duoc gi trong khi cac ngay cung thu trong ky deu ban.
    Day la XAP XI, khong phai su that: BC khong luu ton kho theo tung ngay trong qua khu.
    Muon chinh xac thi can snapshot ton hang ngay, ghi o phu luc thiet ke."""
    since = today - timedelta(weeks=weeks)
    by_wd: dict[int, list[float]] = defaultdict(list)
    for i in range((today - since).days + 1):
        d = since + timedelta(days=i)
        by_wd[d.weekday()].append(by_day.get(d, 0.0))
    prof = {wd: fmean(v) for wd, v in by_wd.items() if v}
    out = []
    for i in range((today - since).days + 1):
        d = since + timedelta(days=i)
        if prof.get(d.weekday(), 0) >= 0.6 and by_day.get(d, 0.0) == 0:
            out.append(d)
    return out


def episodes(days: list[date]) -> list[tuple[date, date]]:
    """Gop cac ngay lien tiep thanh dot. Ba dot rieng le khac han mot dot dai chin ngay."""
    out: list[tuple[date, date]] = []
    for d in sorted(days):
        if out and (d - out[-1][1]).days == 1:
            out[-1] = (out[-1][0], d)
        else:
            out.append((d, d))
    return out


def view(asst: Any, item_no: str, location: str, window: int = WINDOW, min_usable: int = 14) -> DemandView:
    """Loai bo ngay dut hang va ngay su kien thi cua so 28 ngay co the khong con du ngay sach.
    Khi do noi rong cua so thay vi co tinh tren vai ngay con lai. Bao ro la da noi rong."""
    v = _view_once(asst, item_no, location, window)
    for wider in (56, 90):
        if v.usable_days >= min_usable or wider <= window:
            break
        v2 = _view_once(asst, item_no, location, wider)
        v2.widened = True
        v = v2
    return v


def _view_once(asst: Any, item_no: str, location: str, window: int) -> DemandView:
    today = asst.gw.today()
    rows = asst.gw.sales_history(item_no, location, days=LOOKBACK_WEEKS * 7 + 14)
    by_day = _daily(rows)
    w_from, w_to = today - timedelta(days=window - 1), today
    so = [d for d in stockout_days(by_day, today) if w_from <= d <= w_to]

    ex = exceptions(asst, item_no, location)
    excl: list[date] = []
    for e in ex:
        a, b = date.fromisoformat(e["from"]), date.fromisoformat(e["to"])
        for i in range((b - a).days + 1):
            d = a + timedelta(days=i)
            if w_from <= d <= w_to:
                excl.append(d)

    items = {i["itemNo"]: i["description"] for i in asst.gw.items()}
    v = DemandView(item_no, location, items.get(item_no, item_no), w_from, w_to,
                   sold=sum(by_day.get(w_from + timedelta(days=i), 0.0) for i in range(window)),
                   stockout_days=so, excluded_days=sorted(set(excl)), exceptions=ex)
    v.naive_daily = round(v.sold / window, 2)
    drop = set(so) | set(excl)
    usable = [by_day.get(w_from + timedelta(days=i), 0.0)
              for i in range(window) if (w_from + timedelta(days=i)) not in drop]
    v.usable_days = len(usable)
    v.corrected_daily = round(fmean(usable), 2) if usable else v.naive_daily
    v.window = window
    return v


def card(asst: Any, v: DemandView, ref: str = "") -> Card:
    ep = episodes(v.stockout_days)
    facts = [
        ("Mặt hàng và cửa hàng", f"{v.item_desc} ({v.item_no}) tại {v.location}"),
        ("Cửa sổ tính", f"{v.window_from.isoformat()} đến {v.window_to.isoformat()}, {v.window} ngày"
         + (" (đã nới rộng vì thiếu ngày sạch)" if v.widened else "")),
        ("Đã bán trong cửa sổ", f"{v.sold:.0f}"),
        ("Nhu cầu ngày nếu đọc thô", f"{v.naive_daily}"),
        ("Ngày đứt hàng bị loại", f"{len(v.stockout_days)} ngày, {len(ep)} đợt"),
        ("Ngày sự kiện bị loại", f"{len(v.excluded_days)} ngày" + (f" ({v.exceptions[-1]['reason']})" if v.exceptions else "")),
        ("Số ngày còn dùng được", f"{v.usable_days}/{v.window}"),
        ("Nhu cầu ngày sau khi sửa", f"{v.corrected_daily}  ({v.uplift_pct:+.0f}% so với đọc thô)"),
        ("Dự báo 14 ngày tới", f"{v.forecast_14:.0f}"),
    ]
    body = ("Số đọc thô coi mọi ngày bằng nhau. Con số sau khi sửa bỏ những ngày không bán được vì hết hàng "
            "và những ngày nằm trong sự kiện một lần đã được xác nhận. Hai loại ngày đó không nói gì về nhu cầu bình thường.")
    return Card(title="Nhu cầu thật, sau khi sửa số liệu đầu vào", body=body, facts=facts, kind="info",
                ref=ref or f"{v.location}|{v.item_no}", actions=[Action("ack", "OK")])


def run(asst: Any, user: dict[str, Any], item_no: str, location: str) -> list[Delivery]:
    v = view(asst, item_no, location)
    return [Delivery(user["user_id"], f"Nhu cầu {v.item_desc} tại {v.location}.", card(asst, v), SKILL)]
