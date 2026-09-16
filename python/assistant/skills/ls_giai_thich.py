"""Giai thich vi sao LS Replenishment ra con so cho mot mat hang tai mot dia diem. Khong goi model.

Vi sao co file nay. Dung hoi ngay 14/09/2026: "LS tinh nhung ban co hieu tai sao tinh ra nhu vay khong, de giai thich
tren chat". Cung ngay Dung yeu cau knowledge phai dung chung cho moi tinh huong, khong chi du lieu mau. Nen skill nay
KHONG viet tay cong thuc cua nhanh nao: no doc nhat ky tinh ma chinh LS ghi (`replenCalcLogLines`), dich tung dong bang
knowledge sinh tu source LS (`assistant/ls_knowledge.py`), roi bo sung hai phan LS khong ghi vao log:
  - ban binh quan: tinh o buoc Calc. Item Quantities, doc tu Replen. Item Quantity va Sales Profile;
  - thanh phan ton hieu dung: doc tu Replen. Item Quantity.
Moi con so doc tu BC. Tro ly khong tinh lai. Dong log nao knowledge chua doc duoc thi hien nguyen van va noi ro.
"""
from __future__ import annotations

import re
from typing import Any

from .. import ls_knowledge as kt
from ..bc_link import link
from ..cards import Card, fmt_qty
from . import Delivery

SKILL = "ls_giai_thich"
TEMPLATE = "MAROU-TO"

# Tham so luon neu, vi chung vao thang cong thuc hoac quyet dinh. Tham so khac chi neu khi co gia tri.
_LUON_NEU = ("Replen. Source", "Replenishment Calculation Type", "Store Stock Cover Reqd (Days)", "Replenishment Sales Profile",
             "Reorder Point", "Maximum Inventory", "Transfer Multiple")
_BO_QUA_NEU_RONG = ("", "0", "No", "None")
# Buoc nao can trich nguyen van log LS cho nguoi doc doi chieu.
_TRICH = ("cong_thuc", "dieu_chinh", "lam_tron", "gioi_han_kho", "psd", "cross_dock", "bo_qua")


def _so(v: Any) -> str:
    """In dung so LS luu, toi da 5 chu so le, khong lam tron 11.675 thanh 11.7."""
    try:
        f = float(v)
    except (TypeError, ValueError):
        return str(v)
    return fmt_qty(f) if f.is_integer() else f"{f:.5f}".rstrip("0").rstrip(".")


def _ngay(v: Any) -> str:
    s = str(v or "")[:10]
    return f"{s[8:10]}/{s[5:7]}" if len(s) == 10 and s > "0001-01-01" else ""


def du_lieu(gw: Any, item_no: str, store: str, template: str = TEMPLATE) -> dict[str, Any] | None:
    """Doc het nhung gi can de giai thich. None neu dang chay mo phong hoac LS chua co dong nay."""
    if gw.is_mock:
        return None
    # Journal nao co dong chi tiet cho cap nay thi giai thich theo journal do (Dakao mua thang tu Marou thi la MAROU-PO,
    # 15/09/2026); MAROU-TO van ghi log "khong xet" cho mat hang To Store nen khong duoc chon journal chi vi co log.
    cac_tpl = list(dict.fromkeys([template, *gw.LS_TEMPLATES]))
    ct, log, tpl = [], [], template
    for chi_can_ct in (True, False):
        for tpl in cac_tpl:
            ct = gw.doc("replenJournalDetails", [("replenishmentTemplateCode", "eq", tpl), ("itemNo", "eq", item_no),
                                                  ("locationCode", "eq", store)], top=1)
            log = sorted(gw.doc("replenCalcLogLines", [("replenishmentTemplateCode", "eq", tpl), ("itemNo", "eq", item_no),
                                                        ("locationCode", "eq", store)], top=500),
                         key=lambda r: r.get("entryNo", 0))
            if ct or (log and not chi_can_ct):
                break
        else:
            continue
        break
    if not ct and not log:
        return None
    riq = gw.doc("replenItemQuantities", [("itemNo", "eq", item_no), ("locationCode", "eq", store)], top=5)
    riq = next((r for r in riq if not r.get("variantCode")), riq[0] if riq else {})
    ts = gw.doc("replenItemParameters", [("itemNo", "eq", item_no)], top=1)
    return {"ct": ct[0] if ct else {}, "riq": riq, "ts": ts[0] if ts else {}, "log": [l.get("messageText", "") for l in log],
            "gw": gw, "template": tpl}


def _profile(gw: Any, ma: str) -> list[dict[str, Any]]:
    if not ma:
        return []
    return sorted(gw.doc("replenSalesProfileLines", [("salesProfileCode", "eq", ma)], top=20), key=lambda r: r.get("lineNo", 0))


def _cau_ban_binh_quan(gw: Any, riq: dict[str, Any], ma_profile: str) -> list[str]:
    """Phan ban binh quan, LS tinh o Calc. Item Quantities va khong ghi vao Calc. Log Lines."""
    if not riq:
        return []
    ra = []
    cuaso = "; ".join(f"{p.get('startDateFormula')} đến {p.get('endDateFormula')} trọng số {_so(p.get('weight'))}"
                      for p in _profile(gw, ma_profile))
    ra.append(f"Bán bình quân {_so(riq.get('dailySales'))}/ngày lấy từ Replen. Item Quantity, tính trên {_ngay(riq.get('salesDateFrom'))} "
              f"đến {_ngay(riq.get('salesDateTo'))}" + (f" theo sales profile {ma_profile} ({cuaso})" if ma_profile else "")
              + ". " + (kt.tham_so("Daily Sales").get("y_nghia") or ""))
    so_ngay, het = int(riq.get("noOfSalesDates") or 0), int(riq.get("noOfDaysOutOfStock") or 0)
    if het:
        # No. of Sales Dates va No. of Days Out of Stock la TONG qua moi cua so cua profile (Calc-DailySale cong don).
        ra.append(f"LS đếm {het} ngày hết hàng trên tổng {so_ngay} ngày của các cửa sổ; bán vào những ngày đó bị bỏ ra và "
                  "bán bình quân của từng cửa sổ chỉ chia cho số ngày còn hàng.")
        if so_ngay and het * 2 > so_ngay:
            ra.append("Lưu ý: quá nửa số ngày bị tính là hết hàng. Hàng tươi huỷ cuối ngày thì tồn về 0 mỗi tối và bị đếm là hết "
                      "hàng; nếu không đúng thực tế thì xem lại cách LS ghi Out of Stock (Replen. Setup).")
    return ra


def _cau_du_bao(gw: Any, item_no: str, store: str) -> list[str]:
    """Du bao tung ngay ma LS cong lai (LSC Forecast Entry do NWV Forecast Accuracy Calc ghi bang Holt-Winters) va lich su
    kien trong cung khoang ngay. LS khong ghi tung ngay vao Calc. Log Lines, chi ghi tong."""
    from datetime import timedelta

    tu = gw.today() + timedelta(days=1)
    den = tu + timedelta(days=13)
    dong = sorted((r for r in gw.doc("lsForecastEntries", [("itemNo", "eq", item_no), ("locationCode", "eq", store)], top=200)
                   if tu.isoformat() <= str(r.get("date"))[:10] <= den.isoformat()), key=lambda r: str(r.get("date")))
    ra = []
    if dong:
        ra.append("Dự báo từng ngày LS đọc từ Retail Forecast Entry (Holt-Winters do NWV Forecast Accuracy Calc ghi, chất lượng "
                  f"{_so(dong[0].get('forecastQualityPct'))}% = 100 − WAPE kỳ kiểm tra): "
                  + ", ".join(f"{_ngay(r.get('date'))} {_so(r.get('forecastQuantity'))}" for r in dong[:7]) + ".")
    else:
        ra.append("Không có dòng Retail Forecast Entry cho mặt hàng này; LS dùng bán bình quân hoặc 0 theo Forecast Exception "
                  "Handling trên LS Forecast Setup.")
    su_kien = [r for r in gw.doc("plannedSalesDemands", [("itemNo", "eq", item_no), ("locationCode", "eq", store)], top=200)
               if tu.isoformat() <= str(r.get("date"))[:10] <= den.isoformat()]
    if su_kien:
        from bc_agent.bc_data import unescape_option
        theo_ma: dict[str, list[dict[str, Any]]] = {}
        for r in su_kien:
            theo_ma.setdefault(r.get("plannedDemandEvent") or "(không mã)", []).append(r)
        for ma, rs in theo_ma.items():
            rs.sort(key=lambda r: str(r.get("date")))
            loai = unescape_option(rs[0].get("plannedDemandType")) or ""
            ra.append(f"Sự kiện {ma} ({loai} {_so(rs[0].get('plannedDemand'))}) từ {_ngay(rs[0].get('date'))} đến "
                      f"{_ngay(rs[-1].get('date'))}: LS chỉnh dự báo của những ngày này trước khi cộng.")
    return ra


def _cau_ton(riq: dict[str, Any]) -> str:
    if not riq:
        return ""
    phan = [f"tồn {_so(riq.get('inventory'))}"]
    for truong, caption, dau in (("quantityOnPurchaseOrder", "Quantity on Purchase Order", "+"),
                                 ("quantityOnSalesOrder", "Quantity on Sales Order", "−"),
                                 ("quantityInTransferIn", "Quantity in Transfer In", "+"),
                                 ("quantityInTransferOut", "Quantity in Transfer Out", "−")):
        if float(riq.get(truong) or 0):
            phan.append(f"{dau} {kt.ten_tham_so(caption)} {_so(riq.get(truong))}")
    cau = "Thành phần tồn trên Replen. Item Quantity: " + " ".join(phan) + "."
    if float(riq.get("quantityInTransferIn") or 0) or float(riq.get("quantityInTransferOut") or 0):
        cau += " Hàng chuyển đến và đi gồm cả Transfer Order còn Open chưa release, vì LS không lọc theo Status."
    return cau


def giai_thich(gw: Any, item_no: str, store: str, template: str = TEMPLATE) -> dict[str, Any] | None:
    """Cac y giai thich, dung chung cho chat va MCP."""
    from bc_agent.bc_data import unescape_option

    d = du_lieu(gw, item_no, store, template)
    if not d:
        return None
    ct, riq, ts = d["ct"], d["riq"], d["ts"]
    doc = kt.doc_nhat_ky(d["log"])
    buoc: list[kt.Buoc] = doc["buoc"]

    so_cuoi = float(ct.get("quantity") or 0)
    ssq = float(ct.get("systemSuggestedQuantity") or 0)
    kieu = unescape_option(ct.get("calculationType")) or ""
    quyet = (unescape_option(ct.get("decision")) or "").strip()
    y: list[str] = []

    tom = f"LS đề xuất {_so(so_cuoi)}" + (f" (số hệ thống đề xuất {_so(ssq)})" if ssq != so_cuoi else "")
    if kieu:
        tom += f", kiểu tính {kieu}"
    if quyet:
        tom += f", quyết định {quyet}"
    y.append(tom + ".")

    # Tham so: gom moi cap tu dong Replen. Data. Nguon tham so noi ro truoc, vi no quyet dinh sua o dau.
    cap: dict[str, str] = {}
    for b in buoc:
        if b.loai == "tham_so" and b.buoc == "tham_so":
            for a, v in b.cap:
                cap.setdefault(a, v)
    nguon = cap.get("Replen. Source", "")
    if nguon:
        y.append(f"Tham số lấy từ {kt.tai()['nguon_tham_so'].get(nguon, nguon)} (Replen. Source = {nguon}).")
    # Journal mua: ProcessRecord ghi dong "Select Lowest Price Vendor = ..." chi khi Replenishment Type = Purchase.
    la_mua = any(b.goc.startswith("Select Lowest Price Vendor =") for b in buoc)
    an = {"Replen. Source", "Item No.", "Variant Code", "Replenishment Grade Code", "Range in Location",
          "Replenish as Item No - Method"} | (set() if la_mua else {"Purch. Order Delivery", "Wareh Stock Cover Reqd (Days)", "Vendor No."})
    neu = [a for a in cap if a not in an and (a in _LUON_NEU or cap[a] not in _BO_QUA_NEU_RONG)]
    if neu:
        y.append("Tham số LS dùng: " + "; ".join(f"{a} = {cap[a] or '(trống)'}" for a in neu) + ".")

    # Cac buoc tinh theo dung thu tu LS ghi. Bo dong xet pham vi va dong ghi so khong doi ("from 5 to 5").
    for b in buoc:
        if b.loai != "mau" or b.buoc in ("pham_vi", "he_thong", "tham_so") or not b.noi:
            continue
        if b.id in ("CALC:Text009", "CALC:Text011") and b.gia_tri.get("1") == b.gia_tri.get("2"):
            continue
        y.append(b.noi + "".join(" " + x.noi for x in b.phan_them if x.noi))
        if b.buoc == "ton":
            ct_ton = _cau_ton(riq)
            if ct_ton:
                y.append(ct_ton)

    if kieu in ("LS Forecast", "Retail Forecast"):
        # Kieu Retail Forecast khong dung ban binh quan: LS cong du bao tung ngay trong LSC Forecast Entry roi chinh theo
        # Planned Sales Demand. Ban binh quan chi dung cho ngay thieu dong du bao (Forecast Exception Handling).
        y.extend(_cau_du_bao(gw, item_no, store))
    elif kieu in ("Average Usage",) or float(riq.get("dailySales") or 0):
        y.extend(_cau_ban_binh_quan(gw, riq, cap.get("Replenishment Sales Profile") or ts.get("salesProfile") or ""))

    doi = [b for b in buoc if b.doi_so and b.buoc not in ("cong_thuc",)]
    # Stock Levels: System Suggested Quantity la muc Maximum Inventory (hoac Reorder Point), so cong thuc la
    # muc do tru ton kha dung, LS ghi o dong DecisionSSQStoreEffInvQtyTxt.
    goc, ten_goc = ssq, "số công thức"
    sl = next((b for b in buoc if b.id == "CALC:DecisionSSQStoreEffInvQtyTxt"), None)
    if sl is not None:
        try:
            goc, ten_goc = max(0.0, float(sl.gia_tri.get("4", ""))), "số cần theo mức tồn"
        except ValueError:
            pass
    if doi and so_cuoi != goc:
        ten_buoc = kt.tai()["ten_buoc"]
        cac = list(dict.fromkeys(ten_buoc.get(b.buoc, b.buoc).lower() for b in doi))
        y.append(f"Số cuối {_so(so_cuoi)} khác {ten_goc} {_so(goc)} do bước: " + ", ".join(cac) + ".")

    # Noi sua: chi tham so vao cong thuc hoac buoc da doi so, va chi phan ung voi nguon tham so dang dung.
    lien_quan = [a for a in neu if a in _LUON_NEU] + [t for b in buoc for t in b.tham_so if t in cap and t not in neu]
    tu_khoa = {"Item": "trên Item", "ItemStore": "Item Store Rec", "DataProfile": "Data Profile"}.get(nguon, "")
    sua = []
    for a in dict.fromkeys(lien_quan):
        cho = kt.tham_so(a).get("sua_o", "")
        if not cho:
            continue
        doan = next((p.strip() for p in re.split(r",\s*hoặc\s*|;\s*", cho) if tu_khoa and tu_khoa in p), "") or cho
        sua.append(f"{a}: {doan}")
    if sua and nguon:
        y.append("Muốn đổi kết quả thì sửa " + "; ".join(sua) + ". Sửa xong phải tính lại Replen. Item Quantity rồi journal.")

    if doc["chua_nhan_dang"]:
        y.append(f"{len(doc['chua_nhan_dang'])} dòng nhật ký LS knowledge chưa đọc được, xem nguyên văn bên dưới.")

    trich = [b.goc for b in buoc if b.buoc in _TRICH
             and not (b.id in ("CALC:Text009", "CALC:Text011") and b.gia_tri.get("1") == b.gia_tri.get("2"))]
    trich += doc["chua_nhan_dang"]
    return {"item_no": item_no, "store": store, "mo_ta": ct.get("description") or item_no, "de_xuat": so_cuoi,
            "tu_kho": ct.get("replenishmentLocationCode") or ct.get("vendorNo") or "", "y": y, "nhat_ky_ls": trich,
            "template": d.get("template", template),
            "ty_le_nhan_dang": doc["ty_le_nhan_dang"], "ls_central": kt.tai()["ls_central"]}


def handle(asst: Any, user: dict[str, Any], item_no: str, store: str) -> list[Delivery]:
    uid = user["user_id"]
    kq = giai_thich(asst.gw, item_no, store)
    if not kq:
        if asst.gw.is_mock:
            return [Delivery(uid, "Giải thích theo LS Replenishment chỉ có khi nối Business Central. Bản mô phỏng không có "
                                  "journal của LS.", skill=SKILL)]
        return [Delivery(uid, f"Journal {TEMPLATE} của LS chưa có dòng {item_no} tại {store}. Có thể mặt hàng chưa được phân "
                              "phối cho cửa hàng này (Item Distribution) hoặc journal chưa tính lại.", skill=SKILL)]
    body = "\n".join("· " + c for c in kq["y"])
    if kq["nhat_ky_ls"]:
        body += "\n\nNhật ký tính của LS, nguyên văn:\n" + "\n".join(kq["nhat_ky_ls"])
    tpl = kq.get("template", TEMPLATE)
    mua = tpl != TEMPLATE
    card = Card(title=f"Vì sao LS đề xuất {_so(kq['de_xuat'])} {kq['mo_ta']} cho {store}", body=body,
                facts=[("Mặt hàng", f"{kq['mo_ta']} ({item_no})"), ("Cửa hàng", store),
                       ("Mua từ" if mua else "Từ kho", kq["tu_kho"]),
                       ("Nguồn", f"LS Replenishment, journal {tpl}")],
                ref=f"{store}|{item_no}", kind="info",
                links=[("Nhật ký tính của LS", link("ls_calc_log", {"Replenishment Template Code": tpl, "Item No.": item_no,
                                                                     "Location Code": store})),
                       ("Dòng journal LS", link("ls_transfer_journal_details", {"Replenishment Template Code": tpl,
                                                                               "Item No.": item_no, "Location Code": store})),
                       ("Replen. Item Quantities", link("ls_item_quantities", {"Item No.": item_no, "Location Code": store}))])
    return [Delivery(uid, f"LS đề xuất {_so(kq['de_xuat'])} {kq['mo_ta']} cho {store}. Các bước dưới đây đọc từ nhật ký tính "
                          "của LS, tôi không tính lại.", card=card, skill=SKILL, ref=f"{store}|{item_no}")]
