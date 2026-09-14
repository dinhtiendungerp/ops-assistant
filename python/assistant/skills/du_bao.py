"""UC1 Demand Planning & Forecast: tra loi ve do chinh xac du bao. Khong goi model.

Vi sao co file nay (14/09/2026). RFP UC1 doi forecast vs actual, exception list, accuracy tracking. So do bang AL tinh
(codeunit 70120 NWV Forecast Accuracy Calc, API forecastAccuracies), ban Python doi chieu trong bc_agent/forecast.py ra
cung WAPE. Tro ly chi doc va noi lai. Day la BASELINE thong ke (trung binh 28 ngay, trung binh cung thu), khong phai mo
hinh AI: moi mo hinh sau nay phai thang so nay tren cung ky kiem tra thi moi dang dung.
Tu 14/09/2026 them Holt-Winters (HW, mo hinh thong ke chuoi thoi gian, mua vu tuan). HW hoc tren toan bo lich su va ghi du
bao 28 ngay toi vao LSC Forecast Entry; mat hang kieu tinh Retail Forecast cua LS bo sung hang theo du bao do, cong lich
khuyen mai trong LSC Replen. Planned Sales Demand.
"""
from __future__ import annotations

from collections import defaultdict
from typing import Any

from bc_agent.forecast import wape_gop

from ..bc_link import link
from ..cards import Card, fmt_qty
from . import Delivery

SKILL = "du_bao"
TEN_PP = {"MA28": "trung bình 28 ngày", "SWA8": "trung bình cùng thứ 8 tuần", "HW": "Holt-Winters"}
VAI_TRO_TAI_DIEM = ("store_manager",)


def _pct(v: float | None) -> str:
    return "không đo được" if v is None else f"{v:.1f}%".replace(".", ",")


def tong_hop(rows: list[dict[str, Any]]) -> dict[str, Any]:
    """Tong hop dung chung cho chat, man hinh Du bao va MCP. WAPE gop = tong sai so / tong thuc te."""
    methods = sorted({r["method"] for r in rows})
    tong = {m: wape_gop(rows, m) for m in methods}
    tot = min((m for m in methods if tong[m] is not None), key=lambda m: tong[m], default=None)
    theo_noi = {loc: {m: wape_gop(rows, m, locationCode=loc) for m in methods} for loc in sorted({r["locationCode"] for r in rows})}
    theo_nhom = {cat: {m: wape_gop(rows, m, itemCategoryCode=cat) for m in methods}
                 for cat in sorted({r.get("itemCategoryCode") or "" for r in rows})}
    ngoai_le = sorted([r for r in rows if r.get("isException") and r["method"] == tot],
                      key=lambda r: -float(r.get("absErrorQty") or 0))
    ky = (rows[0].get("holdoutFrom"), rows[0].get("holdoutTo")) if rows else (None, None)
    return {"methods": methods, "tong": tong, "tot_nhat": tot, "theo_noi": theo_noi, "theo_nhom": theo_nhom,
            "ngoai_le": ngoai_le, "so_cap": len({(r["itemNo"], r["locationCode"]) for r in rows}), "ky": ky}


def _ngay(s: Any) -> str:
    s = str(s or "")[:10]
    return f"{s[8:10]}/{s[5:7]}" if len(s) == 10 else ""


def handle(asst: Any, user: dict[str, Any], intent: Any, text: str) -> list[Delivery]:
    uid = user["user_id"]
    rows = asst.gw.doc("forecastAccuracies", [], top=5000)
    if not rows:
        return [Delivery(uid, "Chưa có kết quả đo độ chính xác dự báo. Trên BC cần chạy Run Forecast Accuracy (trang NWV Agent "
                              "Setup) hoặc Job Queue với tham số FORECAST.", skill=SKILL)]
    noi = getattr(intent, "store_hint", "") or (user.get("store_code") if user.get("role") in VAI_TRO_TAI_DIEM else "") or ""
    item = asst.gw.find_item(intent.item_text, min_score=75) if (getattr(intent, "item_text", "") or "").strip() else None
    if item:
        return chi_tiet(asst, user, item["itemNo"], noi, rows)
    if noi:
        rows = [r for r in rows if r["locationCode"] == noi]
        if not rows:
            return [Delivery(uid, f"Không có cặp mặt hàng nào tại {noi} đủ lịch sử để đo dự báo.", skill=SKILL)]
    th = tong_hop(rows)
    tot = th["tot_nhat"]
    pham_vi = f"mặt hàng tại {noi}" if noi else "mặt hàng và điểm bán"
    cau = (f"Đo trên {th['so_cap']} cặp {pham_vi}, kỳ kiểm tra {_ngay(th['ky'][0])} đến {_ngay(th['ky'][1])}: "
           + "; ".join(f"{TEN_PP.get(m, m)} sai {_pct(th['tong'][m])}" for m in th["methods"])
           + f". Phương pháp tốt hơn là {TEN_PP.get(tot, tot)}. {len(th['ngoai_le'])} cặp vượt ngưỡng cần xem.")
    body = []
    if not noi:
        body.append("Theo điểm bán (" + TEN_PP.get(tot, tot) + "): "
                    + ", ".join(f"{loc} {_pct(v[tot])}" for loc, v in th["theo_noi"].items()) + ".")
    body.append("Theo nhóm hàng: " + ", ".join(f"{cat or '(trống)'} {_pct(v[tot])}" for cat, v in th["theo_nhom"].items()) + ".")
    if th["ngoai_le"]:
        body.append("Lệch nhiều nhất:")
        for r in th["ngoai_le"][:6]:
            body.append(f"· {r['itemDescription']} tại {r['locationCode']}: bán {fmt_qty(r['actualQty'])}, dự báo "
                        f"{fmt_qty(round(float(r['forecastQty'])))}. {r['exceptionReason']}")
    body.append("Trung bình 28 ngày và trung bình cùng thứ là mốc so sánh. Holt-Winters là mô hình thống kê chuỗi thời gian "
                "(mức nền, xu hướng, mùa vụ theo thứ), chưa phải AI; nó dự báo 28 ngày tới và ghi vào Retail Forecast Entry của "
                "LS. Ngày hết hàng và ngày có Planned Sales Demand của LS bị bỏ khỏi dữ liệu học và phép đo. WAPE là tổng sai số "
                "tuyệt đối chia tổng bán thực tế.")
    card = Card(title="Độ chính xác dự báo", body="\n".join(body),
                facts=[(TEN_PP.get(m, m), _pct(th["tong"][m])) for m in th["methods"]]
                + [("Cặp đo", str(th["so_cap"])), ("Cần xem", str(len(th["ngoai_le"])))],
                ref=f"dubao|{noi}", kind="info",
                links=[("Trang NWV Forecast Accuracy", link("forecast_accuracy", {"Location Code": noi} if noi else None))])
    return [Delivery(uid, cau, card=card, skill=SKILL, ref=f"dubao|{noi}")]


def chi_tiet(asst: Any, user: dict[str, Any], item_no: str, noi: str, rows: list[dict[str, Any]]) -> list[Delivery]:
    uid = user["user_id"]
    rs = [r for r in rows if r["itemNo"] == item_no and (not noi or r["locationCode"] == noi)]
    if not rs:
        return [Delivery(uid, f"Không có kết quả đo dự báo cho {item_no}" + (f" tại {noi}" if noi else "") + ".", skill=SKILL)]
    ten = rs[0].get("itemDescription") or item_no
    theo_noi: dict[str, dict[str, dict]] = defaultdict(dict)
    for r in rs:
        theo_noi[r["locationCode"]][r["method"]] = r
    out = []
    for loc, m in sorted(theo_noi.items()):
        tot = min(m, key=lambda k: float(m[k].get("wapePct") or 1e9))
        r = m[tot]
        body = [f"Kỳ kiểm tra {_ngay(r['holdoutFrom'])} đến {_ngay(r['holdoutTo'])}, tính {r['daysEvaluated']} ngày"
                + (f", bỏ {r['daysCensored']} ngày hết hàng" if r.get("daysCensored") else "")
                + (f", bỏ {r['daysExcluded']} ngày có sự kiện đã khai" if r.get("daysExcluded") else "") + "."]
        for k, x in sorted(m.items()):
            body.append(f"· {TEN_PP.get(k, k)}: mức {x['dailyLevel']}/ngày, dự báo {fmt_qty(round(float(x['forecastQty'])))} "
                        f"so với bán {fmt_qty(x['actualQty'])}, sai {_pct(x['wapePct'])}, lệch {_pct(x['biasPct'])}.")
        if r.get("isException"):
            body.append(f"Cần xem: {r['exceptionReason']}")
        tuan = _theo_tuan(asst, item_no, loc, tot)
        if tuan:
            body.append("Theo tuần (bán / dự báo): " + "; ".join(f"{t} {a} / {f}" for t, a, f in tuan) + ".")
        hw = m.get("HW")
        if hw and hw.get("modelParameters"):
            body.append(f"Tham số Holt-Winters đã chọn: {hw['modelParameters']}.")
        toi, su_kien = ngay_toi(asst, item_no, loc)
        if toi:
            body.append("Dự báo 7 ngày tới đã ghi vào Retail Forecast Entry của LS: "
                        + ", ".join(f"{_ngay(r['date'])} {fmt_qty(round(float(r['forecastQuantity']), 1))}" for r in toi[:7])
                        + f" (tổng {fmt_qty(round(sum(float(r['forecastQuantity']) for r in toi[:7]), 1))}).")
        for sk in su_kien:
            body.append(f"Sự kiện sắp tới {sk['ma']}: {sk['loai']} {sk['muc']} từ {_ngay(sk['tu'])} đến {_ngay(sk['den'])}. "
                        "LS cộng vào dự báo khi tính bổ sung hàng.")
        card = Card(title=f"Dự báo {ten} tại {loc}", body="\n".join(body),
                    facts=[("Phương pháp tốt hơn", TEN_PP.get(tot, tot)), ("WAPE", _pct(r["wapePct"])), ("Bias", _pct(r["biasPct"]))],
                    ref=f"dubao|{loc}|{item_no}", kind="info",
                    links=[("Dự báo và thực tế từng ngày", link("forecast_daily", {"Item No.": item_no, "Location Code": loc,
                                                                                    "Method": tot}))])
        out.append(Delivery(uid, f"{ten} tại {loc}: sai {_pct(r['wapePct'])} với {TEN_PP.get(tot, tot)}.", card=card, skill=SKILL,
                            ref=f"dubao|{loc}|{item_no}"))
    return out[:5]


def ngay_toi(asst: Any, item_no: str, loc: str, so_ngay: int = 28) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    """Du bao cac ngay toi (LSC Forecast Entry) va su kien sap toi (LSC Replen. Planned Sales Demand) cua mot cap."""
    from datetime import timedelta

    from bc_agent.bc_data import unescape_option

    tu = asst.gw.today() + timedelta(days=1)
    den = (tu + timedelta(days=so_ngay - 1)).isoformat()
    toi = sorted((r for r in asst.gw.doc("lsForecastEntries", [("itemNo", "eq", item_no), ("locationCode", "eq", loc)], top=400)
                  if tu.isoformat() <= str(r.get("date"))[:10] <= den), key=lambda r: str(r["date"]))
    theo_ma: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for r in asst.gw.doc("plannedSalesDemands", [("itemNo", "eq", item_no), ("locationCode", "eq", loc)], top=400):
        if tu.isoformat() <= str(r.get("date"))[:10] <= den and (unescape_option(r.get("status")) or "") == "Enabled":
            theo_ma[r.get("plannedDemandEvent") or ""].append(r)
    su_kien = []
    for ma, rs in sorted(theo_ma.items()):
        rs.sort(key=lambda r: str(r["date"]))
        loai = unescape_option(rs[0].get("plannedDemandType")) or ""
        muc = f"{fmt_qty(float(rs[0].get('plannedDemand') or 0))}" + ("%" if "%" in loai else "")
        su_kien.append({"ma": ma or "(không mã)", "loai": loai, "muc": muc, "tu": str(rs[0]["date"])[:10],
                        "den": str(rs[-1]["date"])[:10], "ngay": [str(r["date"])[:10] for r in rs]})
    return toi, su_kien


def _theo_tuan(asst: Any, item_no: str, loc: str, method: str) -> list[tuple[str, str, str]]:
    ngay = asst.gw.doc("forecastDailies", [("itemNo", "eq", item_no), ("locationCode", "eq", loc), ("method", "eq", method)], top=200)
    ngay = sorted(ngay, key=lambda r: r["date"])
    ra = []
    for i in range(0, len(ngay), 7):
        tuan = [r for r in ngay[i:i + 7] if not r.get("censored") and not r.get("excluded")]
        if not tuan:
            continue
        ra.append((_ngay(ngay[i]["date"]), fmt_qty(round(sum(float(r["actualQty"]) for r in tuan))),
                   fmt_qty(round(sum(float(r["forecastQty"]) for r in tuan)))))
    return ra
