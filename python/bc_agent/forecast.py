"""Mo hinh du bao BASELINE, tach hoan toan khoi agent.

Vi sao co file nay: use case 1 cua RFP (Demand Planning & Forecast) can mot baseline do duoc TRUOC khi noi den AI.
Hai mo hinh don gian, giai thich duoc cho nguoi nghiep vu:
  - ma28   : trung binh dong 28 ngay gan nhat
  - swa     : seasonal weekday average - trung binh cung thu trong 8 tuan gan nhat (bat nhip cuoi tuan cua retail)
Do chinh xac tren holdout 28 ngay cuoi: WAPE (tong |sai so| / tong thuc te) va bias.
Neu sau nay dung mo hinh phuc tap hon (Prophet, LightGBM, Azure ML), no phai thang baseline nay tren cung holdout.

Input CSV: date,item_no,location_code,qty  (mot dong/ngay/item/location; ngay khong ban co the bo trong)
"""
from __future__ import annotations

import csv
from collections import defaultdict
from dataclasses import dataclass
from datetime import date, timedelta
from pathlib import Path
from statistics import mean

Series = dict[date, float]


def load_sales(path: Path) -> dict[tuple[str, str], Series]:
    out: dict[tuple[str, str], Series] = defaultdict(dict)
    with path.open(encoding="utf-8") as f:
        for row in csv.DictReader(f):
            d = date.fromisoformat(row["date"])
            out[(row["item_no"], row["location_code"])][d] = out[(row["item_no"], row["location_code"])].get(d, 0.0) + float(row["qty"])
    return out


def _dense(series: Series, start: date, end: date) -> list[tuple[date, float]]:
    return [(start + timedelta(days=i), series.get(start + timedelta(days=i), 0.0)) for i in range((end - start).days + 1)]


def forecast_ma28(history: list[tuple[date, float]], horizon: int) -> list[float]:
    last = [q for _, q in history[-28:]]
    level = mean(last) if last else 0.0
    return [level] * horizon


def forecast_swa(history: list[tuple[date, float]], horizon: int, weeks: int = 8) -> list[float]:
    by_wd: dict[int, list[float]] = defaultdict(list)
    for d, q in history[-7 * weeks:]:
        by_wd[d.weekday()].append(q)
    last_day = history[-1][0]
    out = []
    for h in range(1, horizon + 1):
        wd = (last_day + timedelta(days=h)).weekday()
        vals = by_wd.get(wd) or [q for _, q in history[-28:]]
        out.append(mean(vals) if vals else 0.0)
    return out


@dataclass
class Accuracy:
    item_no: str
    location_code: str
    method: str
    actual_total: float
    forecast_total: float
    wape: float | None
    bias_pct: float | None


def backtest(series_map: dict[tuple[str, str], Series], holdout_days: int = 28) -> list[Accuracy]:
    results: list[Accuracy] = []
    for (item, loc), series in series_map.items():
        if not series:
            continue
        end = max(series)
        start = min(series)
        dense = _dense(series, start, end)
        if len(dense) < holdout_days + 28:
            continue
        train, test = dense[:-holdout_days], dense[-holdout_days:]
        actual = [q for _, q in test]
        for method, fn in (("ma28", forecast_ma28), ("swa", forecast_swa)):
            fc = fn(train, holdout_days)
            abs_err = sum(abs(a - f) for a, f in zip(actual, fc))
            tot = sum(actual)
            wape = abs_err / tot if tot > 0 else None
            bias = (sum(fc) - tot) / tot * 100 if tot > 0 else None
            results.append(Accuracy(item, loc, method, tot, sum(fc), wape, bias))
    return results


# ---------------------------------------------------------------- ban doi chieu cua NWV Forecast Accuracy Calc (AL)
# Chep dung cong thuc codeunit 70120, tung buoc. Hai ben chay tren cung Item Ledger Entry phai ra cung WAPE.
# Khac ham backtest o tren: nhu cau theo co so cua NWV Demand Calc (cua hang co ban dem Sale, kho trung tam dem tong luong
# xuat), bo ngay cau bi cat cut (het hang ma khong ban) va ngay co su kien (Planned Sales Demand cua LS, Demand Exception)
# khoi ca du lieu hoc lan sai so; them Holt-Winters (HW) va du bao cho cac ngay toi.
TRAIN_LOOKBACK = 84
HW_LOOKBACK = 365
HW_ALPHAS = (0.05, 0.1, 0.2, 0.3, 0.5)
HW_GAMMAS = (0.05, 0.1, 0.2, 0.3)
HW_TRENDS = ((0.0, 0.0), (0.1, 0.9))       # (beta, phi): khong xu huong, xu huong tat dan


@dataclass
class ForecastThresholds:
    holdout_days: int = 28
    wape_warn: float = 50.0
    bias_warn: float = 30.0
    min_actual: float = 20.0
    central_warehouse: str = "W0003"
    horizon_days: int = 28


def _round(x: float, step: float) -> float:
    from decimal import ROUND_HALF_UP, Decimal
    return float((Decimal(str(x)) / Decimal(str(step))).quantize(Decimal("1"), rounding=ROUND_HALF_UP) * Decimal(str(step)))


def _thu(d: date) -> int:
    """Thu trong tuan 1..7 (thu Hai = 1), giong Date2DWY(D, 1) cua AL."""
    return d.isoweekday()


def _ngay_su_kien(exceptions: list[dict], planned: list[dict]) -> set[tuple[str, str, date]]:
    """Ngay loai khoi du lieu hoc va phep do: dong LSC Replen. Planned Sales Demand dang Enabled (lich khuyen mai chuan cua
    LS) va NWV Demand Exception. Khoa rong o mat hang hoac dia diem nghia la moi mat hang, moi dia diem."""
    from .bc_data import unescape_option
    from .inventory import _d

    ra: set[tuple[str, str, date]] = set()
    for p in planned:
        trang_thai = unescape_option(p.get("status")) or ""
        loai = (unescape_option(p.get("plannedDemandType")) or "").strip()
        if trang_thai != "Enabled" or not loai or (p.get("variantCode") or ""):
            continue
        d = _d(p.get("date"))
        if d:
            ra.add((p.get("itemNo") or "", p.get("locationCode") or "", d))
    for e in exceptions:
        tu, den = _d(e.get("fromDate")), _d(e.get("toDate"))
        if not tu or not den:
            continue
        d = tu
        while d <= den:
            ra.add((e.get("itemNo") or "", e.get("locationCode") or "", d))
            d += timedelta(days=1)
    return ra


def _la_su_kien(ngay: set, item: str, loc: str, d: date) -> bool:
    return (item, loc, d) in ngay or ("", loc, d) in ngay or (item, "", d) in ngay or ("", "", d) in ngay


def _dien_ngay_khong_hop_le(demand: list[float], valid: list[bool], end: int) -> list[float]:
    """Chep FillInvalidDays cua AL. Chi so 1..end (phan tu 0 bo trong cho khop chi so AL)."""
    overall, s, dem = 0.0, 0.0, 0
    i = end
    while i >= 1 and dem < 56:
        if valid[i]:
            s += demand[i]
            dem += 1
        i -= 1
    if dem:
        overall = s / dem
    y = [0.0] * (end + 1)
    for i in range(1, end + 1):
        if valid[i]:
            y[i] = demand[i]
            continue
        s, dem = 0.0, 0
        k = i - 7
        while k >= 1 and k >= i - 56:
            if valid[k]:
                s += demand[k]
                dem += 1
            k -= 7
        y[i] = s / dem if dem else overall
    return y


def _chay_hw(y: list[float], start: int, end: int, first: date, alpha: float, gamma: float, beta: float, phi: float):
    """Chep RunHoltWinters cua AL: Holt-Winters cong tinh, mua vu tuan danh so theo thu 1..7."""
    k = min(4, (end - start + 1) // 7)
    base = sum(y[start:start + 7 * k]) / (7 * k)
    season = [0.0] * 8
    for p in range(7):
        season[_thu(first + timedelta(days=start + p - 1))] = sum(y[start + p + 7 * j] for j in range(k)) / k - base
    level, trend, sse, cnt = base, 0.0, 0.0, 0
    for t in range(start, end + 1):
        w = _thu(first + timedelta(days=t - 1))
        fc = level + phi * trend + season[w]
        if t >= start + 7:
            sse += (y[t] - fc) ** 2
            cnt += 1
        new_level = alpha * (y[t] - season[w]) + (1 - alpha) * (level + phi * trend)
        trend = beta * (new_level - level) + (1 - beta) * phi * trend
        season[w] = gamma * (y[t] - new_level) + (1 - gamma) * season[w]
        level = new_level
    return level, trend, season, sse, cnt


def holt_winters(demand: list[float], valid: list[bool], end: int, first: date) -> dict | None:
    """Chep FitHoltWinters cua AL. demand, valid danh chi so tu 1. None khi chua du 28 ngay tu lan ban dau."""
    start = next((i for i in range(1, end + 1) if demand[i] > 0), 0)
    if not start or end - start + 1 < 28:
        return None
    y = _dien_ngay_khong_hop_le(demand, valid, end)
    tot = None
    for beta, phi in HW_TRENDS:
        for alpha in HW_ALPHAS:
            for gamma in HW_GAMMAS:
                level, trend, season, sse, cnt = _chay_hw(y, start, end, first, alpha, gamma, beta, phi)
                if tot is None or sse < tot["sse"]:
                    tot = {"level": level, "trend": trend, "season": season, "sse": sse, "cnt": cnt,
                           "alpha": alpha, "gamma": gamma, "beta": beta, "phi": phi}
    tot["sigma"] = (tot["sse"] / tot["cnt"]) ** 0.5 if tot["cnt"] else 0.0
    return tot


def hw_du_bao(m: dict, h: int, weekday: int) -> float:
    damp, pw = 0.0, 1.0
    for _ in range(h):
        pw *= m["phi"]
        damp += pw
    return max(0.0, m["level"] + damp * m["trend"] + m["season"][weekday])


def _tham_so(m: dict | None) -> str:
    if m is None:
        return "thieu lich su, dung MA28"
    xu = "khong xu huong" if m["beta"] == 0 else "xu huong tat dan (beta 0.1, phi 0.9)"
    return f"alpha {m['alpha']:g}, gamma {m['gamma']:g}, {xu}"


def backtest_bc(ile: list[dict], as_of: date, th: ForecastThresholds = ForecastThresholds(),
                exceptions: list[dict] | None = None, items: dict[str, dict] | None = None,
                planned: list[dict] | None = None, forward: list[dict] | None = None) -> tuple[list[dict], list[dict]]:
    """Ban doi chieu cua codeunit 70120. Tra ve (dong accuracy, dong daily) cung ten truong voi API forecastAccuracies /
    forecastDailies. Truyen `forward` (list rong) de nhan them du bao Holt-Winters cho cac ngay toi, cung hinh dang API
    lsForecastEntries."""
    from .inventory import OUTBOUND_TYPES, _d, _q

    items = items or {}
    su_kien = _ngay_su_kien(exceptions or [], planned or [])
    moves: dict[tuple[str, str], dict[date, float]] = defaultdict(lambda: defaultdict(float))
    sale: dict[tuple[str, str], dict[date, float]] = defaultdict(lambda: defaultdict(float))
    out: dict[tuple[str, str], dict[date, float]] = defaultdict(lambda: defaultdict(float))
    has_sale: set[tuple[str, str]] = set()
    for r in ile:
        d = _d(r.get("posting_date"))
        if not d:
            continue
        key = (r.get("item_no"), r.get("location_code"))
        q = _q(r.get("quantity"))
        et = str(r.get("entry_type") or "")
        moves[key][d] += q
        if et == "Sale":
            has_sale.add(key)
            if q < 0:
                sale[key][d] += -q
        if q < 0 and et in OUTBOUND_TYPES:
            out[key][d] += -q

    holdout = th.holdout_days
    holdout_from = as_of - timedelta(days=holdout - 1)
    first = holdout_from - timedelta(days=HW_LOOKBACK)
    n = (as_of - first).days + 1
    train_end = (holdout_from - first).days
    short_start = train_end - TRAIN_LOOKBACK + 1
    acc_rows: list[dict] = []
    daily_rows: list[dict] = []
    for key in sorted(moves):
        item_no, loc = key
        if key not in has_sale or loc == th.central_warehouse:     # chi diem ban, xem ghi chu trong codeunit 70120
            continue
        src = sale[key]
        balance = sum(q for d, q in moves[key].items() if d < first)
        demand, valid, cens, excl = [0.0], [False], [False], [False]
        has_history, total = False, 0.0
        for i in range(1, n + 1):
            d = first + timedelta(days=i - 1)
            if i == short_start:
                has_history = balance != 0
            dq = src.get(d, 0.0)
            mq = moves[key].get(d, 0.0)
            if mq != 0 and short_start <= i <= train_end - 27:
                has_history = True
            c = balance <= 0.0001 and dq <= 0.0001
            x = _la_su_kien(su_kien, item_no, loc, d)
            demand.append(dq)
            cens.append(c)
            excl.append(x)
            valid.append(not c and not x)
            if i >= short_start:
                total += dq
            balance += mq
        if not has_history or total <= 0:
            continue

        # MA28: 28 ngay hop le gan nhat, nhin lui toi da 84 ngay
        vals, i = [], train_end
        while i >= 1 and i > train_end - TRAIN_LOOKBACK and len(vals) < 28:
            if valid[i]:
                vals.append(demand[i])
            i -= 1
        ma28 = sum(vals) / len(vals) if vals else 0.0
        tot, cnt = [0.0] * 8, [0] * 8
        for i in range(train_end - 55, train_end + 1):
            if i >= 1 and valid[i]:
                w = _thu(first + timedelta(days=i - 1))
                tot[w] += demand[i]
                cnt[w] += 1
        swa = [tot[w] / cnt[w] if cnt[w] else ma28 for w in range(8)]
        hw = holt_winters(demand, valid, train_end, first)
        ngay_ktra = [holdout_from + timedelta(days=h) for h in range(holdout)]
        du_bao = {
            "MA28": ([ma28] * holdout, ""),
            "SWA8": ([swa[_thu(d)] for d in ngay_ktra], ""),
            "HW": ([hw_du_bao(hw, h + 1, _thu(d)) for h, d in enumerate(ngay_ktra)] if hw else [ma28] * holdout, _tham_so(hw)),
        }

        meta = items.get(item_no, {})
        wape_hw = 0.0
        for method, (fc_list, tham_so) in du_bao.items():
            row = {"itemNo": item_no, "locationCode": loc, "method": method, "itemDescription": meta.get("description") or "",
                   "itemCategoryCode": meta.get("item_category") or "", "demandBasis": "Sale",
                   "holdoutFrom": holdout_from.isoformat(), "holdoutTo": as_of.isoformat(), "daysEvaluated": 0,
                   "daysCensored": 0, "daysExcluded": 0, "dailyLevel": _round(sum(fc_list) / holdout, 0.001),
                   "modelParameters": tham_so}
            act = fc_sum = err = 0.0
            for h in range(holdout):
                i = train_end + 1 + h
                fc = fc_list[h]
                daily_rows.append({"itemNo": item_no, "locationCode": loc, "method": method, "date": ngay_ktra[h].isoformat(),
                                   "actualQty": demand[i], "forecastQty": _round(fc, 0.001),
                                   "censored": cens[i], "excluded": excl[i]})
                if cens[i]:
                    row["daysCensored"] += 1
                elif excl[i]:
                    row["daysExcluded"] += 1
                else:
                    row["daysEvaluated"] += 1
                    act += demand[i]
                    fc_sum += fc
                    err += abs(demand[i] - fc)
            row["actualQty"] = _round(act, 0.001)
            row["forecastQty"] = _round(fc_sum, 0.001)
            row["absErrorQty"] = _round(err, 0.001)
            row["wapePct"] = _round(row["absErrorQty"] / row["actualQty"] * 100, 0.1) if row["actualQty"] > 0 else 0.0
            row["biasPct"] = (_round((row["forecastQty"] - row["actualQty"]) / row["actualQty"] * 100, 0.1)
                              if row["actualQty"] > 0 else 0.0)
            ly_do = []
            if row["actualQty"] > 0 and row["actualQty"] >= th.min_actual:
                if row["wapePct"] > th.wape_warn:
                    ly_do.append(f"WAPE {row['wapePct']:g}% vượt ngưỡng {th.wape_warn:g}%.")
                if abs(row["biasPct"]) > th.bias_warn:
                    ly_do.append(f"Dự báo {'cao' if row['biasPct'] > 0 else 'thấp'} hơn bán thực tế {abs(row['biasPct']):g}%.")
            row["isException"] = bool(ly_do)
            row["exceptionReason"] = " ".join(ly_do)
            acc_rows.append(row)
            if method == "HW":
                wape_hw = row["wapePct"]

        if forward is not None:
            m = holt_winters(demand, valid, n, first)
            if m:
                for h in range(1, th.horizon_days + 1):
                    d = as_of + timedelta(days=h)
                    q = hw_du_bao(m, h, _thu(d))
                    forward.append({"itemNo": item_no, "variantCode": "", "locationCode": loc, "date": d.isoformat(),
                                    "forecastQuantity": _round(q, 0.01),
                                    "forecastQuantityLower": _round(max(0.0, q - 1.2816 * m["sigma"]), 0.01),
                                    "forecastQuantityUpper": _round(q + 1.2816 * m["sigma"], 0.01),
                                    "forecastQualityPct": _round(max(0.0, 100 - wape_hw), 0.1)})
    return acc_rows, daily_rows


def wape_gop(rows: list[dict], method: str, **loc: str) -> float | None:
    """WAPE gop cua nhieu dong: tong sai so / tong thuc te, khong phai trung binh cac WAPE. Loc them theo truong bang tu khoa."""
    rs = [r for r in rows if r.get("method") == method and all((r.get(k) or "") == v for k, v in loc.items())]
    act = sum(float(r.get("actualQty") or 0) for r in rs)
    err = sum(float(r.get("absErrorQty") or 0) for r in rs)
    return round(err / act * 100, 1) if act > 0 else None


def write_report(results: list[Accuracy], out_path: Path) -> None:
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with out_path.open("w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["item_no", "location_code", "method", "actual_28d", "forecast_28d", "wape", "bias_pct"])
        for r in results:
            w.writerow([r.item_no, r.location_code, r.method, f"{r.actual_total:.1f}", f"{r.forecast_total:.1f}",
                        "" if r.wape is None else f"{r.wape:.3f}", "" if r.bias_pct is None else f"{r.bias_pct:.1f}"])


def summarize(results: list[Accuracy]) -> dict[str, float]:
    out = {}
    for method in ("ma28", "swa"):
        rs = [r for r in results if r.method == method and r.wape is not None]
        if rs:
            # WAPE gop: tong sai so / tong thuc te, khong phai trung binh cac WAPE
            abs_err = sum(r.wape * r.actual_total for r in rs)
            tot = sum(r.actual_total for r in rs)
            out[method] = abs_err / tot if tot else float("nan")
    return out
