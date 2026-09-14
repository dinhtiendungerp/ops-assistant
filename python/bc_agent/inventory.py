"""Lop tinh toan UC2: tu Item Ledger Entry tho ra phan tang ton kho va de xuat bo sung.

Vi sao lop nay nam o Python chu khong phai AL: logic goc viet trong NWV Inv. Health Calc,
nhung extension do chua build duoc. Lop nay lap lai dung cong thuc do tren du lieu doc qua
custom API page, de demo chay duoc ma chi can publish extension chi-doc NWV Marou Data API.
Khi extension logic len duoc production thi day thanh ban doi chieu, khong phai bo di.

Ba diem ma phien ban truoc lam sai va o day sua lai:

1. Cau bi cat cut. Ngay het hang khong phai ngay cau bang 0. Neu chia tong luong ban cho
   toan bo so ngay trong cua so thi cang dut hang cang thay nhu cau thap, roi nguong bo sung
   cang tut xuong, roi lai cang dut hang. Vong lap nay la loi pho bien nhat khi chuyen tu
   bang tinh sang he thong. O day ngay ton bang 0 bi loai khoi mau so.

2. Nhu cau tai kho. Kho xuat hang di cua hang bang Negative Adjmt. hoac Transfer chu khong
   phai bang dong Sale. Dem dong Sale se thay kho khong co nhu cau va xep moi lo o kho vao
   nhom cham luan chuyen. O day: dia diem nao khong he co dong Sale thi lay tong luong xuat.

3. Mat hang khong co Item Tracking Code. Khong co lot thi khong co han dung, va khong co han
   dung thi khong the ket luan can han hay qua han. Nhung dong do phai duoc phan tang bang
   cac tieu chi con lai, khong duoc mac dinh coi la Healthy, cung khong duoc bo qua.
"""
from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass, field
from datetime import date, timedelta
from typing import Any, Iterable

OUTBOUND_TYPES = {"Sale", "Negative Adjmt.", "Transfer", "Consumption", "Output"}


@dataclass(frozen=True)
class Thresholds:
    """Bang nguong. Moi con so o day phai chot voi nghiep vu truoc khi demo, khong phai
    hang so ky thuat. Gia tri mac dinh lay tu NWV Agent Setup."""
    sales_history_days: int = 90
    stockout_days: int = 7          # days of cover duoi muc nay la rui ro dut hang
    excess_days: int = 90           # days of cover tren muc nay la ton thua
    slow_days: int = 60             # so ngay khong co dong ban thi coi la cham luan chuyen
    near_expiry_days: int = 45      # con it hon so ngay nay den han thi vao dien theo doi
    target_days: int = 14           # muc ton muc tieu khi bo sung
    reorder_days: int = 5           # duoi muc nay thi de xuat bo sung ngay
    # Kho trung tam (NWV Agent Setup."Central Warehouse Code"). Tai kho, nhu cau la tong luong
    # xuat: ban si tai cho cong hang chuyen di cua hang. Kho vua ban si vua chuyen di ma chi dem
    # dong Sale thi syrup 30091 ra 0,81 chai mot ngay, days of cover 735 ngay, trong khi ca he
    # thong tieu thu 3 chai mot ngay. Chot ngay 12/09/2026.
    central_warehouse: str = "W0003"


@dataclass
class Position:
    item_no: str
    location_code: str
    lot_no: str | None
    quantity: float
    expiration_date: date | None
    unit_cost: float = 0.0
    item_description: str = ""
    item_category: str = ""

    @property
    def value(self) -> float:
        return round(self.quantity * self.unit_cost, 2)


@dataclass
class DemandProfile:
    item_no: str
    location_code: str
    total_qty: float
    days_counted: int
    days_censored: int
    last_sale: date | None
    basis: str                      # "sale" hoac "outflow"

    @property
    def avg_daily(self) -> float:
        return round(self.total_qty / self.days_counted, 4) if self.days_counted else 0.0


@dataclass
class HealthLine:
    item_no: str
    location_code: str
    lot_no: str | None
    item_description: str
    item_category: str
    quantity: float
    inventory_value: float
    avg_daily_qty: float
    days_of_cover: float | None
    last_sale_date: date | None
    days_since_last_sale: int | None
    expiration_date: date | None
    days_to_expiry: int | None
    tier: str
    risk_score: int
    risk_reason: str
    demand_basis: str
    days_censored: int


def _d(v: Any) -> date | None:
    """Doc mot ngay. Ngay 0D cua BC (`0001-01-01`) duoc coi la khong co ngay, xem
    `bc_data.norm_date`: de no lot qua thi moi phep tru ngay ra so am bay tram nghin."""
    if not v:
        return None
    if isinstance(v, date):
        return None if v.year <= 1 else v
    s = str(v)[:10]
    try:
        d = date.fromisoformat(s)
    except ValueError:
        return None
    return None if d.year <= 1 else d


def _q(v: Any) -> float:
    try:
        return float(v or 0)
    except (TypeError, ValueError):
        return 0.0


# ---------------------------------------------------------------- ton kho theo lo
def positions(ile: Iterable[dict[str, Any]], items: dict[str, dict] | None = None) -> list[Position]:
    """Ton hien tai theo item x location x lot, tinh bang tong Quantity co dau cua ILE.

    Khong dung Remaining Quantity vi truong do phu thuoc viec BC da ap dong nhap voi dong xuat
    hay chua. Tong Quantity thi luon dung, ke ca khi chua adjust cost.
    """
    qty: dict[tuple[str, str, str | None], float] = defaultdict(float)
    exp: dict[tuple[str, str | None], date] = {}
    for r in ile:
        lot = r.get("lot_no") or None
        key = (r.get("item_no"), r.get("location_code"), lot)
        qty[key] += _q(r.get("quantity"))
        e = _d(r.get("expiration_date"))
        if e and lot:
            exp[(r.get("item_no"), lot)] = e

    items = items or {}
    out = []
    for (item_no, loc, lot), q in qty.items():
        if q <= 0.0001:
            continue
        meta = items.get(item_no, {})
        out.append(Position(
            item_no=item_no, location_code=loc, lot_no=lot, quantity=round(q, 3),
            expiration_date=exp.get((item_no, lot)),
            unit_cost=_q(meta.get("unit_cost")),
            item_description=meta.get("description") or "",
            item_category=meta.get("item_category") or "",
        ))
    return out


# ---------------------------------------------------------------- nhu cau
def demand_profiles(ile: Iterable[dict[str, Any]], today: date,
                    th: Thresholds = Thresholds()) -> dict[tuple[str, str], DemandProfile]:
    """Nhu cau binh quan ngay theo item x location, da loai ngay het hang.

    Co so tinh theo vai tro dia diem:
      - kho trung tam (th.central_warehouse): tong luong xuat, vi viec cua kho la cap hang cho
        cua hang, ban si chi la mot phan cua luong ra;
      - cua hang: dong Sale neu co, khong co dong Sale nao thi tong luong xuat.
    """
    rows = list(ile)
    since = today - timedelta(days=th.sales_history_days - 1)

    moves: dict[tuple[str, str], dict[date, float]] = defaultdict(lambda: defaultdict(float))
    sale_qty: dict[tuple[str, str], dict[date, float]] = defaultdict(lambda: defaultdict(float))
    out_qty: dict[tuple[str, str], dict[date, float]] = defaultdict(lambda: defaultdict(float))
    has_sale: set[tuple[str, str]] = set()
    last_sale: dict[tuple[str, str], date] = {}

    for r in rows:
        d = _d(r.get("posting_date"))
        if not d:
            continue
        key = (r.get("item_no"), r.get("location_code"))
        q = _q(r.get("quantity"))
        moves[key][d] += q
        et = str(r.get("entry_type") or "")
        if et == "Sale":
            has_sale.add(key)
            if q < 0:
                sale_qty[key][d] += -q
                if d >= since:
                    last_sale[key] = max(last_sale.get(key, d), d)
        if q < 0 and et in OUTBOUND_TYPES:
            out_qty[key][d] += -q
        if q < 0 and et == "Sale" and key not in last_sale and d < since:
            last_sale.setdefault(key, d)

    # ngay ban cuoi cung, tinh tren toan bo lich su chu khong chi trong cua so
    for key, series in sale_qty.items():
        if series:
            last_sale[key] = max(series)

    out: dict[tuple[str, str], DemandProfile] = {}
    for key, day_moves in moves.items():
        if key[1] == th.central_warehouse or key not in has_sale:
            basis = "outflow"
        else:
            basis = "sale"
        src = sale_qty[key] if basis == "sale" else out_qty[key]

        # so du dau moi ngay, de biet ngay nao khong con hang de ban
        balance = 0.0
        for d in sorted(day_moves):
            if d >= since:
                break
            balance += day_moves[d]

        total = 0.0
        counted = censored = 0
        d = since
        while d <= today:
            if balance <= 0.0001 and src.get(d, 0.0) <= 0.0001:
                censored += 1        # khong con hang va cung khong ban duoc gi: cau bi cat cut
            else:
                counted += 1
                total += src.get(d, 0.0)
            balance += day_moves.get(d, 0.0)
            d += timedelta(days=1)

        out[key] = DemandProfile(item_no=key[0], location_code=key[1], total_qty=round(total, 3),
                                 days_counted=counted, days_censored=censored,
                                 last_sale=last_sale.get(key), basis=basis)
    return out


# ---------------------------------------------------------------- phan tang
def classify(pos: Position, dp: DemandProfile | None, today: date,
             th: Thresholds = Thresholds()) -> HealthLine:
    avg = dp.avg_daily if dp else 0.0
    doc = round(pos.quantity / avg, 1) if avg > 0 else None
    last = dp.last_sale if dp else None
    dsls = (today - last).days if last else None
    dte = (pos.expiration_date - today).days if pos.expiration_date else None

    if dte is not None and dte < 0:
        tier, score = "Expired", 100
        reason = f"Lô đã hết hạn {-dte} ngày."
    elif dte is not None and dte <= th.near_expiry_days:
        tier = "NearExpiry"
        score = 60 + round(40 * (1 - dte / th.near_expiry_days))
        if doc is None:
            reason = f"Còn {dte} ngày đến hạn, chưa có dòng bán nào để ước lượng."
        elif doc > dte:
            reason = f"Còn {dte} ngày đến hạn nhưng days of cover là {doc}, sẽ không bán hết."
        else:
            reason = f"Còn {dte} ngày đến hạn, dự kiến bán hết trước hạn."
            score = min(score, 65)
    elif doc is not None and doc < th.stockout_days:
        tier = "StockOutRisk"
        score = 50 + round(40 * (1 - doc / th.stockout_days))
        reason = (f"Days of cover {doc} dưới ngưỡng {th.stockout_days}. "
                  f"Bán bình quân {avg:.2f} một ngày ({dp.basis}).")
    elif dsls is not None and dsls >= th.slow_days:
        tier = "SlowMoving"
        score = min(70, 30 + round(30 * pos.value / 10_000))
        reason = f"{dsls} ngày không có dòng bán. Giá trị tồn {pos.value:,.0f}."
    elif doc is None:
        tier = "SlowMoving"
        score = min(70, 30 + round(30 * pos.value / 10_000))
        reason = "Không có dòng bán nào trong cửa sổ lịch sử."
    elif doc > th.excess_days:
        tier = "Excess"
        score = min(60, 20 + round(30 * pos.value / 10_000))
        reason = f"Days of cover {doc} vượt ngưỡng {th.excess_days}."
    else:
        tier, score, reason = "Healthy", 0, "Trong ngưỡng."

    return HealthLine(
        item_no=pos.item_no, location_code=pos.location_code, lot_no=pos.lot_no,
        item_description=pos.item_description, item_category=pos.item_category,
        quantity=pos.quantity, inventory_value=pos.value, avg_daily_qty=avg,
        days_of_cover=doc, last_sale_date=last, days_since_last_sale=dsls,
        expiration_date=pos.expiration_date, days_to_expiry=dte,
        tier=tier, risk_score=score, risk_reason=reason,
        demand_basis=dp.basis if dp else "khong co du lieu",
        days_censored=dp.days_censored if dp else 0,
    )


def inventory_health(ile: Iterable[dict[str, Any]], today: date,
                     items: dict[str, dict] | None = None,
                     th: Thresholds = Thresholds()) -> list[HealthLine]:
    rows = list(ile)
    pos = positions(rows, items)
    dp = demand_profiles(rows, today, th)
    lines = [classify(p, dp.get((p.item_no, p.location_code)), today, th) for p in pos]
    lines.sort(key=lambda x: (-x.risk_score, -x.inventory_value))
    return lines


# ---------------------------------------------------------------- han dung thuc te
def observed_shelf_life(ile: Iterable[dict[str, Any]]) -> dict[str, int]:
    """Han dung thuc te cua tung mat hang, do tu chinh du lieu: trung vi cua
    (Expiration Date - Posting Date) tren cac dong nhap.

    Khong lay tu truong Expiration Calculation tren Item vi truong do kieu DateFormula,
    custom API page hien chua phoi ra. Do tu du lieu con dung hon: no phan anh han dung
    that cua hang da nhap, chu khong phai con so cau hinh co the da cu.
    Mat hang khong co Item Tracking Code thi khong co trong ket qua.
    """
    spans: dict[str, list[int]] = defaultdict(list)
    for r in ile:
        if _q(r.get("quantity")) <= 0:
            continue
        d, e = _d(r.get("posting_date")), _d(r.get("expiration_date"))
        if d and e:
            spans[r.get("item_no")].append((e - d).days)
    out = {}
    for item_no, xs in spans.items():
        xs.sort()
        out[item_no] = xs[len(xs) // 2]
    return out


# ---------------------------------------------------------------- de xuat bo sung
@dataclass
class ReplenishmentSuggestion:
    item_no: str
    item_description: str
    store_location_code: str
    source_location_code: str
    quantity_on_hand: float
    avg_daily_qty: float
    days_of_cover: float | None
    target_qty: float
    suggested_qty: float
    constrained_qty: float
    source_available: float
    stock_out_risk: bool
    target_days: int
    capped_by_shelf_life: bool
    rationale: str


def replenishment(ile: Iterable[dict[str, Any]], today: date, source_location: str,
                  items: dict[str, dict] | None = None,
                  th: Thresholds = Thresholds()) -> list[ReplenishmentSuggestion]:
    """De xuat dieu chuyen tu kho ve cua hang.

    Hai rang buoc, thieu cai nao cung ra de xuat sai:
      - So luong bi chan boi ton kho that o kho nguon. Agent khong duoc de xuat con so
        ma kho khong co.
      - Muc ton muc tieu bi chan boi han dung. De xuat bo sung du ban 14 ngay cho mat hang
        han dung 3 ngay la cam ket truoc mot lan huy hang. Muc tieu lay min cua so ngay
        muc tieu va han dung tru mot ngay.
    """
    rows = list(ile)
    pos = positions(rows, items)
    dp = demand_profiles(rows, today, th)
    shelf = observed_shelf_life(rows)
    items = items or {}

    on_hand: dict[tuple[str, str], float] = defaultdict(float)
    for p in pos:
        on_hand[(p.item_no, p.location_code)] += p.quantity

    out = []
    stores = {loc for (_, loc) in dp if loc != source_location}
    for (item_no, loc), profile in sorted(dp.items()):
        if loc == source_location or loc not in stores:
            continue
        avg = profile.avg_daily
        if avg <= 0:
            continue
        have = on_hand.get((item_no, loc), 0.0)
        doc = round(have / avg, 1)
        if doc >= th.reorder_days:
            continue
        cover_days = th.target_days
        shelf_days = shelf.get(item_no)
        capped = False
        # `shelf_days > 0` phai co, va phai trung voi dieu kien trong NWV Replenishment Calc.
        # Thieu no thi mot han dung am (du lieu xau) se chan muc ton muc tieu xuong 1 ngay.
        if shelf_days is not None and shelf_days > 0 and shelf_days - 1 < cover_days:
            cover_days = max(1, shelf_days - 1)
            capped = True
        target = round(avg * cover_days)
        suggested = max(0.0, target - have)
        available = on_hand.get((item_no, source_location), 0.0)
        constrained = min(suggested, available)
        meta = items.get(item_no, {})
        out.append(ReplenishmentSuggestion(
            item_no=item_no, item_description=meta.get("description") or "",
            store_location_code=loc, source_location_code=source_location,
            quantity_on_hand=round(have, 2), avg_daily_qty=avg, days_of_cover=doc,
            target_qty=target, suggested_qty=round(suggested, 2),
            constrained_qty=round(constrained, 2), source_available=round(available, 2),
            stock_out_risk=doc < th.stockout_days,
            target_days=cover_days,
            capped_by_shelf_life=capped,
            rationale=(f"Days of cover {doc} dưới ngưỡng {th.reorder_days}. "
                       f"Bổ sung lên mức {cover_days} ngày"
                       + (f" (chặn theo hạn dùng {shelf_days} ngày)." if capped else ".")
                       + (f" Kho nguồn chỉ còn {available:,.0f}, đề xuất bị chặn lại."
                          if constrained < suggested else " Kho nguồn đủ hàng.")),
        ))
    out.sort(key=lambda s: (s.days_of_cover if s.days_of_cover is not None else 999,
                            -s.constrained_qty))
    return out
