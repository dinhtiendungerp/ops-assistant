"""Thu cac mo hinh du bao pho bien tren cung ky kiem tra voi UC1, so voi baseline MA28 va SWA8.

Hai buoc, vi thu vien mo hinh (statsmodels, lightgbm, pandas) khong cai vao Python chung cua may:

    cd python
    python ../tools/forecast_lab.py chuoi            # Python chung: doc ILE bo demo, ghi chuoi ban theo ngay ra JSON
    <venv>/python ../tools/forecast_lab.py chay      # venv co statsmodels + lightgbm: chay mo hinh, ghi ket qua

Quy tac giong het codeunit 70120 (NWV Forecast Accuracy Calc) de so cong bang:
- chi cap cua hang co dong Sale, nhu cau = so luong Sale moi ngay;
- ky kiem tra 28 ngay ket thuc 18/09/2026, du bao lap mot lan tai ngay 21/08 cho ca 28 ngay;
- ngay het hang (dau ngay ton <= 0 va ban 0) bi bo khoi phep do sai so;
- WAPE gop = tong |thuc te - du bao| / tong thuc te tren moi cap.
Them mot dong "Tran ly thuyet": ky vong that cua ham sinh du lieu demo (tools/demo_scenario.demand_lambda). Khong mo hinh
nao vuot duoc dong nay; khoang cach toi no la phan con cai thien duoc, phan con lai la nhieu ngau nhien.
"""
from __future__ import annotations

import json
import math
import sys
from collections import defaultdict
from datetime import date, timedelta
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
OUT = ROOT / "docs" / "du-bao"
CHUOI = OUT / "chuoi-ban-theo-ngay.json"
KET_QUA = OUT / "ket-qua-thu-mo-hinh.json"
AS_OF = date(2026, 9, 18)
HOLDOUT = 28
CENTRAL = "W0003"


# ------------------------------------------------------------------ buoc 1: chuoi ban
def chuoi() -> None:
    sys.path.insert(0, str(ROOT / "python"))
    import demo_scenario as ds
    from bc_agent.demo_data import read_ile

    ile = read_ile()
    items = {it.no: it for it in ds.ITEMS}
    moves = defaultdict(lambda: defaultdict(float))
    sale = defaultdict(lambda: defaultdict(float))
    co_sale = set()
    for r in ile:
        k = (r["item_no"], r["location_code"])
        moves[k][r["posting_date"]] += r["quantity"]
        if r["entry_type"] == "Sale":
            co_sale.add(k)
            if r["quantity"] < 0:
                sale[k][r["posting_date"]] += -r["quantity"]
    dau = min(d for m in moves.values() for d in m)
    ngay = [dau + timedelta(days=i) for i in range((AS_OF - dau).days + 1)]
    ra = []
    for k in sorted(co_sale):
        item, loc = k
        if loc == CENTRAL:
            continue
        ton, dem, het, ky_vong = 0.0, [], [], []
        for d in ngay:
            q = sale[k].get(d, 0.0)
            het.append(ton <= 0.0001 and q <= 0.0001)
            dem.append(q)
            lam = ds.demand_lambda(items[item], loc, d) if item in items else 0.0
            # make_demo_data: q = so lan thanh cong trong int(lam*3)+1 lan thu, xac suat 1/3
            ky_vong.append((int(lam * 3) + 1) / 3 if lam > 0 else 0.0)
            ton += moves[k].get(d, 0.0)
        it = items.get(item)
        ra.append({"item": item, "loc": loc, "ten": it.desc if it else item, "nhom": it.cat if it else "",
                   "ban": dem, "het_hang": het, "ky_vong": ky_vong})
    OUT.mkdir(parents=True, exist_ok=True)
    CHUOI.write_text(json.dumps({"ngay_dau": dau.isoformat(), "as_of": AS_OF.isoformat(), "chuoi": ra}, ensure_ascii=False),
                     encoding="utf-8")
    print(f"{len(ra)} chuoi, {len(ngay)} ngay tu {dau} -> {CHUOI}")


# ------------------------------------------------------------------ buoc 2: mo hinh
def _dien_ngay_het_hang(y, hop_le, t_end):
    """Ngay het hang ban 0 vi khong co hang, khong phai vi khong ai mua. Thay bang trung binh cung thu 8 tuan gan nhat
    (hoac trung binh chung) truoc khi dua cho mo hinh, neu khong mo hinh hoc nham la nhu cau giam."""
    import numpy as np
    y = np.array(y[:t_end], dtype=float)
    ok = np.array(hop_le[:t_end], dtype=bool)
    chung = y[ok][-56:].mean() if ok.any() else 0.0
    for t in np.where(~ok)[0]:
        cung_thu = [y[s] for s in range(t - 7, max(-1, t - 57), -7) if s >= 0 and ok[s]]
        y[t] = float(np.mean(cung_thu)) if cung_thu else chung
    return y


def chay() -> None:
    import warnings

    import numpy as np
    import pandas as pd
    import lightgbm as lgb
    from statsmodels.tsa.holtwinters import ExponentialSmoothing
    from statsmodels.tsa.statespace.sarimax import SARIMAX

    warnings.filterwarnings("ignore")
    data = json.loads(CHUOI.read_text(encoding="utf-8"))
    dau = date.fromisoformat(data["ngay_dau"])
    n = (AS_OF - dau).days + 1
    t0 = n - HOLDOUT                      # chi so ngay dau ky kiem tra; mo hinh chi thay [0, t0)
    ngay = [dau + timedelta(days=i) for i in range(n)]
    chuoi_list = data["chuoi"]

    # Dung dung tap cap ma BC da do (74 cap trong NWV Forecast Accuracy), de so cong bang voi 38,7%.
    uc1 = {(r["itemNo"], r["locationCode"]) for r in json.loads(
        (ROOT / "python" / "bc_agent" / "fixtures" / "forecast_accuracies.json").read_text(encoding="utf-8"))}
    du_bao: dict[str, dict[int, np.ndarray]] = defaultdict(dict)
    dung: list[int] = []
    for si, c in enumerate(chuoi_list):
        if (c["item"], c["loc"]) not in uc1:
            continue
        y = np.array(c["ban"], dtype=float)
        het = np.array(c["het_hang"], dtype=bool)
        hop_le = ~het
        ban_dau = int(np.argmax(y > 0)) if (y > 0).any() else n
        if y[:t0].sum() <= 0 or ban_dau > t0 - 28 or y.sum() <= 0:
            continue
        dung.append(si)
        # --- MA28 va SWA8: y het AL, hoc tren 84 ngay truoc ky kiem tra
        vals = [y[t] for t in range(t0 - 1, max(-1, t0 - 85), -1) if hop_le[t]][:28]
        ma28 = float(np.mean(vals)) if vals else 0.0
        swa = []
        for w in range(7):
            v = [y[t] for t in range(max(0, t0 - 56), t0) if hop_le[t] and ngay[t].weekday() == w]
            swa.append(float(np.mean(v)) if v else ma28)
        du_bao["MA28"][si] = np.full(HOLDOUT, ma28)
        du_bao["SWA8"][si] = np.array([swa[ngay[t].weekday()] for t in range(t0, n)])

        yf = _dien_ngay_het_hang(y, hop_le, t0)[ban_dau:]
        # --- Seasonal naive: lap lai tuan cuoi
        du_bao["Seasonal naive"][si] = np.array([yf[len(yf) - 7 + (h % 7)] for h in range(HOLDOUT)])
        # --- Holt-Winters (ETS): muc + mua vu tuan, co / khong xu huong tat dan, chon theo AIC
        tot = None
        for trend in (None, "add"):
            try:
                m = ExponentialSmoothing(yf, trend=trend, damped_trend=trend is not None, seasonal="add",
                                         seasonal_periods=7, initialization_method="estimated").fit()
                if tot is None or m.aic < tot.aic:
                    tot = m
            except Exception:
                pass
        du_bao["Holt-Winters (ETS)"][si] = np.clip(tot.forecast(HOLDOUT), 0, None) if tot is not None else np.full(HOLDOUT, ma28)
        # --- SARIMA(1,0,1)(0,1,1)7: ARIMA co mua vu tuan
        try:
            m = SARIMAX(yf, order=(1, 0, 1), seasonal_order=(0, 1, 1, 7), enforce_stationarity=False,
                        enforce_invertibility=False).fit(disp=False)
            du_bao["SARIMA"][si] = np.clip(m.forecast(HOLDOUT), 0, None)
        except Exception:
            du_bao["SARIMA"][si] = np.full(HOLDOUT, ma28)
        du_bao["Trần lý thuyết"][si] = np.array(c["ky_vong"][t0:n])
        print(f"  {si + 1}/{len(chuoi_list)} {c['item']} {c['loc']}", end="\r")

    # --- LightGBM: mot mo hinh chung cho moi cap (global model), du bao truc tiep 28 ngay tu mot moc
    def dac_trung(yf_full, moc, h, c, si):
        q = yf_full[: moc + 1]
        td = ngay[moc + h]
        cung_thu = [q[s] for s in range(moc + h - 7, max(-1, moc + h - 63), -7) if s <= moc]
        return {"h": h, "thu": td.weekday(), "ngay_trong_thang": td.day, "thang": td.month,
                "tb7": q[-7:].mean(), "tb14": q[-14:].mean(), "tb28": q[-28:].mean(), "tb56": q[-56:].mean(),
                "cung_thu_tb": float(np.mean(cung_thu)) if cung_thu else q[-28:].mean(),
                "do_lech28": q[-28:].std(), "ty_le_0_28": float((q[-28:] == 0).mean()),
                "item": c["item"], "loc": c["loc"], "nhom": c["nhom"]}

    hang_train, hang_du_doan = [], []
    for si in dung:
        c = chuoi_list[si]
        y = np.array(c["ban"], dtype=float)
        hop_le = ~np.array(c["het_hang"], dtype=bool)
        yf_full = _dien_ngay_het_hang(y, hop_le, t0)
        ban_dau = int(np.argmax(y > 0))
        for moc in range(ban_dau + 56, t0 - HOLDOUT, 3):
            for h in range(1, HOLDOUT + 1):
                if hop_le[moc + h]:
                    hang_train.append({**dac_trung(yf_full, moc, h, c, si), "y": y[moc + h]})
        for h in range(1, HOLDOUT + 1):
            hang_du_doan.append({**dac_trung(yf_full, t0 - 1, h, c, si), "si": si})
    tr = pd.DataFrame(hang_train)
    te = pd.DataFrame(hang_du_doan)
    cot = [k for k in tr.columns if k != "y"]
    for k in ("item", "loc", "nhom"):
        loai = pd.CategoricalDtype(sorted(set(tr[k]) | set(te[k])))
        tr[k] = tr[k].astype(loai)
        te[k] = te[k].astype(loai)
    mo_hinh = lgb.LGBMRegressor(objective="tweedie", tweedie_variance_power=1.2, n_estimators=600, learning_rate=0.03,
                                num_leaves=31, min_child_samples=40, subsample=0.8, subsample_freq=1,
                                colsample_bytree=0.8, verbose=-1, random_state=7)
    mo_hinh.fit(tr[cot], tr["y"])
    te["du_bao"] = mo_hinh.predict(te[cot])
    for si, g in te.groupby("si"):
        du_bao["LightGBM"][int(si)] = g.sort_values("h")["du_bao"].to_numpy()
    for si in dung:
        du_bao["Kết hợp ETS + LightGBM"][si] = (du_bao["Holt-Winters (ETS)"][si] + du_bao["LightGBM"][si]) / 2
    quan_trong = sorted(zip(cot, mo_hinh.booster_.feature_importance("gain")), key=lambda kv: -kv[1])[:8]

    # --- do sai so, dung quy tac cua AL
    def do(loc=lambda c: True):
        bang = {}
        for ten, fc in du_bao.items():
            act = err = tong_fc = 0.0
            for si in dung:
                c = chuoi_list[si]
                if not loc(c):
                    continue
                y = c["ban"][t0:n]
                het = c["het_hang"][t0:n]
                for h in range(HOLDOUT):
                    if het[h]:
                        continue
                    act += y[h]
                    tong_fc += float(fc[si][h])
                    err += abs(y[h] - float(fc[si][h]))
            bang[ten] = {"wape": round(err / act * 100, 1) if act else None,
                         "bias": round((tong_fc - act) / act * 100, 1) if act else None}
        return bang

    thang_ma28 = {}
    for ten, fc in du_bao.items():
        thang = 0
        for si in dung:
            c = chuoi_list[si]
            y = np.array(c["ban"][t0:n])
            ok = ~np.array(c["het_hang"][t0:n], dtype=bool)
            if np.abs(y[ok] - fc[si][ok]).sum() < np.abs(y[ok] - du_bao["MA28"][si][ok]).sum() - 1e-9:
                thang += 1
        thang_ma28[ten] = thang
    nhom = sorted({chuoi_list[si]["nhom"] for si in dung})
    ket_qua = {
        "so_cap": len(dung), "ky_kiem_tra": [ngay[t0].isoformat(), AS_OF.isoformat()],
        "tong": do(), "theo_nhom": {g: do(lambda c, g=g: c["nhom"] == g) for g in nhom},
        "so_cap_thang_ma28": thang_ma28, "lightgbm_dac_trung_quan_trong": [[k, round(float(v))] for k, v in quan_trong],
        "lightgbm_so_dong_hoc": len(tr),
    }
    KET_QUA.write_text(json.dumps(ket_qua, ensure_ascii=False, indent=1), encoding="utf-8")
    print()
    print(f"{len(dung)} cap, ky kiem tra {ngay[t0]} - {AS_OF}, LightGBM hoc tren {len(tr)} dong")
    print(f"{'Mo hinh':<26}{'WAPE':>7}{'Bias':>8}{'Thang MA28':>12}")
    for ten, v in sorted(ket_qua["tong"].items(), key=lambda kv: kv[1]["wape"]):
        print(f"{ten:<26}{v['wape']:>7}{v['bias']:>8}{thang_ma28[ten]:>12}")
    for g, b in ket_qua["theo_nhom"].items():
        print(g, {k: v["wape"] for k, v in b.items()})
    print("dac trung LightGBM:", quan_trong)


if __name__ == "__main__":
    {"chuoi": chuoi, "chay": chay}[sys.argv[1] if len(sys.argv) > 1 else "chuoi"]()
