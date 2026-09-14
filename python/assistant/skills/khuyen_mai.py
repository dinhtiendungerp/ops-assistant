"""Chuong trinh khuyen mai (CTKM) dang chay va sap toi, doc tu bang chuan LS. Khong goi model, khong ghi gi vao BC.

Vi sao co file nay (14/09/2026). Dung hoi "tren agent truy cuu, hoi dap duoc cac CTKM sap toi, hien co khong". Truoc do tro
ly chi thay dong Planned Sales Demand (phia bo sung hang), khong thay chuong trinh gia ban o POS.

Nguon, doc trong source LS Central 28.0.10.3586:
  - LSC Periodic Discount: dau chuong trinh (Multibuy, Mix&Match, Disc. Offer, Total Discount, Tender Type, Item Point,
    Line Discount), Status, Price Group. Ngay bat dau va ket thuc la FlowField tu LSC Validation Period.
  - LSC Periodic Discount Line: Item, Item Category, Product Group, Special Group hoac All; dong Exclude bi tru ra.
  - LSC Store Price Group: chuong trinh ap cho cua hang co Price Group do; Price Group rong la moi cua hang.
  - LSC Replen. Planned Event (Source Type = Discount, Source Code = so chuong trinh) va Planned Sales Demand: cach chuan
    de LS Replenishment cong nhu cau cua chuong trinh (bao cao Update Planned Sales Demand from Discount).

Viec agent lam them ngoai tra cuu: voi moi CTKM dang chay hoac sap toi, so cua hang ap dung va dang ban mat hang voi dong
Planned Sales Demand trong thoi gian chuong trinh. Cap nao khong co dong thi LS Replenishment tinh nhu ngay thuong, day la
viec can bao Supply Chain. Tro ly chi bao, khong tu tao Planned Event.

"Dang ban" = co dong Sale trong 90 ngay tai cua hang do. Chuong trinh Enabled ma khong mat hang nao dang ban tai cac cua
hang cua tro ly thi chi dem, khong liet ke (company NWV con 30 chuong trinh mau cho hang thoi trang, golf).
"""
from __future__ import annotations

import re
from collections import defaultdict
from datetime import date, timedelta
from typing import Any

from bc_agent.bc_data import unescape_option

from ..bc_link import link
from ..cards import Card, fmt_qty
from . import Delivery

SKILL = "khuyen_mai"
NGAY_BAN = 90
VAI_TRO_TAI_DIEM = ("store_manager",)

_SAP_TOI = re.compile(r"(sắp tới|sap toi|sắp diễn ra|sap dien ra|sắp chạy|sap chay|tuần tới|tuan toi|tuần sau|tuan sau|"
                      r"tháng tới|thang toi|sắp có|sap co|upcoming|kế tiếp|ke tiep)", re.I)
_DANG = re.compile(r"(đang chạy|dang chay|đang có|dang co|hiện có|hien co|hiện tại|hien tai|hôm nay|hom nay|đang áp dụng|"
                   r"dang ap dung|hiện hành|hien hanh|còn hiệu lực|con hieu luc)", re.I)
_DA_QUA = re.compile(r"(đã kết thúc|da ket thuc|đã qua|da qua|vừa qua|vua qua|trước đây|truoc day|đã chạy|da chay|tháng trước|"
                     r"thang truoc)", re.I)


def _d(s: Any) -> date | None:
    s = str(s or "")[:10]
    try:
        v = date.fromisoformat(s)
    except ValueError:
        return None
    return None if v.year <= 1 else v


def _ngay(v: date | None, nam: int | None = None) -> str:
    if not v:
        return "không giới hạn"
    return v.strftime("%d/%m") if v.year == nam else v.strftime("%d/%m/%Y")


TEN_LOAI = {"Multibuy": "mua nhiều giảm giá (Multibuy)", "Mix&Match": "combo (Mix&Match)", "Item Point": "đổi điểm (Item Point)",
            "Total Discount": "giảm trên tổng hóa đơn (Total Discount)", "Tender Type": "giảm theo hình thức thanh toán (Tender Type)",
            "Line Discount": "giảm theo dòng (Line Discount)"}


def _gio(p: dict[str, Any] | None) -> str:
    if not p:
        return ""
    tu, den = str(p.get("startingTime") or "")[:5], str(p.get("endingTime") or "")[:5]
    if tu in ("", "00:00") and den in ("", "00:00"):
        return ""
    return f", {tu or '00:00'}-{den or '24:00'}"


MOI_BAT_DAU = 28     # CTKM bat dau trong so ngay nay (hoac sap toi) thi lich su ban chua phan anh no


def trang_thai(o: dict[str, Any], hom_nay: date) -> str:
    """dang_chay | sap_toi | chua_bat | da_tat | da_ket_thuc.

    Chua bat = Disabled, sap toi hoac vua toi ngay bat dau: POS se khong ap, co the la quen bat. Da tat = Disabled tu lau
    (du lieu mau Cronus co nhieu chuong trinh 2022-2028 dang tat): chi dem, khong liet ke."""
    tu, den = _d(o.get("startingDate")), _d(o.get("endingDate"))
    if den and den < hom_nay:
        return "da_ket_thuc"
    if unescape_option(o.get("status")) != "Enabled":
        return "chua_bat" if tu and tu >= hom_nay - timedelta(days=MOI_BAT_DAU) else "da_tat"
    if tu and tu > hom_nay:
        return "sap_toi"
    return "dang_chay"


def _muc_giam(o: dict[str, Any], dong: list[dict[str, Any]]) -> str:
    loai = unescape_option(o.get("type")) or ""
    kieu = unescape_option(o.get("discountType")) or ""
    if loai == "Disc. Offer":
        pct = sorted({float(l.get("dealPriceDiscPct") or 0) for l in dong if not l.get("exclude")})
        return "giảm " + "/".join(f"{fmt_qty(p)}%" for p in pct) if pct and pct != [0.0] else "giảm giá theo dòng"
    if kieu == "Discount %" and float(o.get("discountPctValue") or 0):
        return f"{TEN_LOAI.get(loai, loai)} giảm {fmt_qty(float(o['discountPctValue']))}%"
    if kieu == "Deal Price" and float(o.get("dealPriceValue") or 0):
        return f"{TEN_LOAI.get(loai, loai)} đồng giá {fmt_qty(float(o['dealPriceValue']))}"
    if kieu == "Discount Amount" and float(o.get("discountAmountValue") or 0):
        return f"{TEN_LOAI.get(loai, loai)} giảm {fmt_qty(float(o['discountAmountValue']))}"
    if kieu == "Least Expensive":
        return f"{TEN_LOAI.get(loai, loai)}, món rẻ nhất được giảm"
    return TEN_LOAI.get(loai, loai)


def doc(gw: Any) -> dict[str, Any]:
    """Doc mot lan cac bang LS can cho viec tra loi. Tach rieng de MCP va brief dung chung."""
    hom_nay = gw.today()
    return {
        "hom_nay": hom_nay,
        "ctkm": gw.doc("lsPeriodicDiscounts", [], top=5000),
        "dong": gw.doc("lsPeriodicDiscountLines", [], top=20000),
        "nhom_gia": gw.doc("lsStorePriceGroups", [], top=5000),
        "ky": {r["validationId"]: r for r in gw.doc("lsValidationPeriods", [], top=5000)},
        "su_kien": {r["eventCode"]: r for r in gw.doc("plannedEvents", [], top=2000)},
        "nhu_cau": gw.doc("plannedSalesDemands", [("date", "ge", (hom_nay - timedelta(days=62)).isoformat())], top=50000),
        "hang": {i["itemNo"]: i for i in gw.doc("nwvItems", [], top=5000)},
        "ban": {(r["item_no"], r["location_code"]) for r in gw.sales_history(days=NGAY_BAN) if float(r.get("qty") or 0) > 0},
        "cua_hang": [s for s in gw.stores() if s != getattr(gw, "central_wh", "")],
    }


def tong_hop(du_lieu: dict[str, Any]) -> list[dict[str, Any]]:
    """Moi CTKM thanh mot dong da giai: trang thai, cua hang ap dung, mat hang, cap chua co nhu cau trong LS."""
    hom_nay = du_lieu["hom_nay"]
    cua_hang = du_lieu["cua_hang"]
    theo_nhom_gia: dict[str, set[str]] = defaultdict(set)
    for r in du_lieu["nhom_gia"]:
        theo_nhom_gia[r["priceGroupCode"]].add(r["store"])
    dong_theo_ctkm: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for l in du_lieu["dong"]:
        dong_theo_ctkm[l["offerNo"]].append(l)
    theo_nhom_hang: dict[str, list[str]] = defaultdict(list)
    for no, it in du_lieu["hang"].items():
        theo_nhom_hang[it.get("itemCategoryCode") or ""].append(no)
    nhu_cau: dict[tuple[str, str], list[dict[str, Any]]] = defaultdict(list)
    for r in du_lieu["nhu_cau"]:
        if unescape_option(r.get("status")) == "Enabled" and not r.get("variantCode"):
            nhu_cau[(r["itemNo"], r["locationCode"])].append(r)
    gan_su_kien: dict[str, list[str]] = defaultdict(list)
    for ma, ev in du_lieu["su_kien"].items():
        if unescape_option(ev.get("sourceType")) == "Discount" and ev.get("sourceCode"):
            gan_su_kien[ev["sourceCode"]].append(ma)

    ra = []
    for o in du_lieu["ctkm"]:
        tt = trang_thai(o, hom_nay)
        dong = dong_theo_ctkm.get(o["no"], [])
        pg = o.get("priceGroup") or ""
        ap = [s for s in cua_hang if not pg or s in theo_nhom_gia.get(pg, set())]
        hang: dict[str, dict[str, Any]] = {}
        nhom: list[str] = []
        tat_ca = False
        tru: set[str] = set()
        for l in dong:
            loai = unescape_option(l.get("type")) or ""
            if l.get("exclude"):
                if loai == "Item":
                    tru.add(l["no"])
                continue
            if loai == "Item":
                hang[l["no"]] = l
            elif loai == "Item Category":
                for no in theo_nhom_hang.get(l["no"], []):
                    hang.setdefault(no, {**l, "no": no, "description": du_lieu["hang"][no].get("description", no)})
            elif loai == "All":
                tat_ca = True
            else:
                nhom.append(f"{loai} {l['no']}")
        for no in tru:
            hang.pop(no, None)
        ban = du_lieu["ban"]
        dang_ban = sorted({(no, s) for no in hang for s in ap if (no, s) in ban})
        if tat_ca:
            dang_ban = sorted({(no, s) for no, s in ban if s in ap})
        tu, den = _d(o.get("startingDate")), _d(o.get("endingDate"))
        co_nhu_cau: dict[tuple[str, str], set[str]] = {}
        thieu: list[tuple[str, str]] = []
        # Chuong trinh chay tu lau thi lich su ban da gom tac dong cua no, khong can Planned Sales Demand rieng.
        moi = tt == "sap_toi" or (tt == "dang_chay" and (tu or date.min) >= hom_nay - timedelta(days=MOI_BAT_DAU))
        if moi:
            bat_dau = max(tu or hom_nay, hom_nay + timedelta(days=1))
            ket_thuc = den or (hom_nay + timedelta(days=28))
            for cap in dang_ban:
                ma = {r.get("plannedDemandEvent") or "" for r in nhu_cau.get(cap, [])
                      if bat_dau <= (_d(r.get("date")) or date.min) <= ket_thuc}
                if ma:
                    co_nhu_cau[cap] = ma
                elif bat_dau <= ket_thuc:
                    thieu.append(cap)
        ra.append({"no": o["no"], "ten": o.get("description") or o["no"], "loai": unescape_option(o.get("type")) or "",
                   "trang_thai": tt, "moi": moi, "tu": tu, "den": den, "gio": _gio(du_lieu["ky"].get(o.get("validationPeriodId") or "")),
                   "muc": _muc_giam(o, dong), "nhom_gia": pg, "cua_hang": ap,
                   "hang": [{"no": no, "ten": l.get("description") or no, "pct": float(l.get("dealPriceDiscPct") or 0),
                             "gia": float(l.get("offerPrice") or 0), "gia_goc": float(l.get("standardPrice") or 0)}
                            for no, l in sorted(hang.items())],
                   "nhom": nhom, "tat_ca": tat_ca, "dang_ban": dang_ban, "co_nhu_cau": co_nhu_cau, "thieu": thieu,
                   "su_kien": sorted(gan_su_kien.get(o["no"], []))})
    return ra


def _cau_thieu(c: dict[str, Any], ten_hang: dict[str, str]) -> str:
    if not c["dang_ban"] or not c["moi"]:
        return ""
    if not c["thieu"]:
        ma = sorted({m for v in c["co_nhu_cau"].values() for m in v if m})
        return f"LS Replenishment đã có nhu cầu khuyến mãi cho cả {len(c['dang_ban'])} cặp mặt hàng x cửa hàng" + \
               (f" (Planned Event {', '.join(ma)})." if ma else ".")
    theo_hang: dict[str, list[str]] = defaultdict(list)
    for no, s in c["thieu"]:
        theo_hang[no].append(s)
    phan = "; ".join(f"{ten_hang.get(no, no)} tại {', '.join(ss)}" for no, ss in sorted(theo_hang.items()))
    if not c["co_nhu_cau"]:
        return (f"Chưa có Planned Sales Demand nào trong thời gian CTKM ({phan}): LS Replenishment tính như ngày thường. "
                "Nếu CTKM làm tăng bán thì cần tạo Planned Event gắn CTKM này.")
    return (f"LS Replenishment chưa cộng nhu cầu khuyến mãi cho {phan}, dù cửa hàng đó thuộc nhóm giá của CTKM và đang bán "
            "mặt hàng. Cần thêm dòng vào Planned Event hoặc chạy lại Update Planned Sales Demand from Discount.")


def _dong(c: dict[str, Any], ten_hang: dict[str, str], cua_hang: str = "") -> str:
    hang = ", ".join(h["ten"] for h in c["hang"][:4]) + (f" và {len(c['hang']) - 4} món khác" if len(c["hang"]) > 4 else "")
    if c["tat_ca"]:
        hang = "mọi mặt hàng"
    if c["nhom"]:
        hang = ", ".join(x for x in (hang, "nhóm " + ", ".join(c["nhom"])) if x)
    noi = "" if cua_hang else (f" tại {', '.join(c['cua_hang'])}" if c["nhom_gia"] else " tại mọi cửa hàng")
    nam = c["nam"]
    return f"{c['no']} {c['ten']}: {c['muc']} {hang}, {_ngay(c['tu'], nam)} đến {_ngay(c['den'], nam)}{c['gio']}{noi}."


def tim_hang(asst: Any, chu: str) -> list[str]:
    """Ma mat hang nguoi dung nhac. "croissant" khop ca Croissant plain va Croissant chocolate nen lay moi mon co ten chua
    cum chu do; khong co thi so mo nhu cac skill khac. Chu con sot (vi du ten cua hang "Quan 1") khong khop gi thi bo loc."""
    if not chu:
        return []
    gon = lambda s: " ".join(re.sub(r"[^\w\s]", " ", (s or "").lower()).split())  # noqa: E731
    c = gon(chu)
    chua = [i["itemNo"] for i in asst.gw.items() if c and f" {c} " in f" {gon(i.get('description'))} "]
    if chua:
        return sorted(chua)
    it = asst.gw.find_item(chu, min_score=80)
    return [it["itemNo"]] if it else []


def handle(asst: Any, user: dict[str, Any], intent: Any, text: str) -> list[Delivery]:
    uid = user["user_id"]
    try:
        du_lieu = doc(asst.gw)
    except Exception as e:                       # thieu API page (app cu) thi noi ro, khong de chet im
        return [Delivery(uid, f"Chưa đọc được bảng khuyến mãi của LS: {e}", skill=SKILL)]
    ds = tong_hop(du_lieu)
    for c in ds:
        c["nam"] = du_lieu["hom_nay"].year
    cua_hang = asst._tim_cua_hang(text) or getattr(intent, "store_hint", "") or \
        (user.get("store_code") if user.get("role") in VAI_TRO_TAI_DIEM else "") or ""
    chu = (getattr(intent, "item_text", "") or "").strip()
    ma_hang = tim_hang(asst, chu)
    item = {"itemNo": ma_hang[0], "description": chu} if ma_hang else None

    muon = set()
    if _SAP_TOI.search(text):
        muon.add("sap_toi")
    if _DANG.search(text):
        muon.add("dang_chay")
    if _DA_QUA.search(text):
        muon.add("da_ket_thuc")
    if not muon:
        muon = {"dang_chay", "sap_toi"}
    if "dang_chay" in muon or "sap_toi" in muon:
        muon.add("chua_bat")

    def hop(c: dict[str, Any]) -> bool:
        if c["trang_thai"] not in muon:
            return False
        if cua_hang and cua_hang not in c["cua_hang"]:
            return False
        if ma_hang and not (c["tat_ca"] or any(h["no"] in ma_hang for h in c["hang"])):
            return False
        # Chuong trinh da ket thuc thi chi can co mat hang; con lai phai co mat hang dang ban tai cua hang cua tro ly
        if c["trang_thai"] == "da_ket_thuc":
            return bool(c["hang"] or c["tat_ca"])
        cap = [p for p in c["dang_ban"] if (not cua_hang or p[1] == cua_hang) and (not ma_hang or p[0] in ma_hang)]
        return bool(cap)

    chon = sorted((c for c in ds if hop(c)), key=lambda c: ({"dang_chay": 0, "sap_toi": 1, "chua_bat": 2, "da_ket_thuc": 3}[c["trang_thai"]],
                                                            c["tu"] or date.min))
    an = [c for c in ds if c["trang_thai"] in ("dang_chay", "sap_toi") and not c["dang_ban"]]
    tat = [c for c in ds if c["trang_thai"] == "da_tat"]
    ten_hang = {h["no"]: h["ten"] for c in ds for h in c["hang"]}
    pham_vi = " ".join(x for x in (f"cho {item['description']}" if item else "", f"tại {cua_hang}" if cua_hang else "") if x)

    if not chon:
        cau = "Không có CTKM " + ("sắp tới" if muon == {"sap_toi", "chua_bat"} else "đang chạy hoặc sắp tới") + \
              (f" {pham_vi}" if pham_vi else "") + " trong LS."
        if an and not (item or cua_hang):
            cau += f" {len(an)} CTKM đang bật trong LS nhưng không mặt hàng nào của chúng bán trong {NGAY_BAN} ngày qua tại các cửa hàng."
        return [Delivery(uid, cau, skill=SKILL, ref="ctkm|")]

    nhom_tt = {"dang_chay": "Đang chạy", "sap_toi": "Sắp tới", "chua_bat": "Đã soạn nhưng chưa bật (POS chưa áp)",
               "da_ket_thuc": "Đã kết thúc"}
    body: list[str] = []
    so = defaultdict(int)
    canh_bao = 0
    for tt in ("dang_chay", "sap_toi", "chua_bat", "da_ket_thuc"):
        nhom = [c for c in chon if c["trang_thai"] == tt]
        if not nhom:
            continue
        body.append(nhom_tt[tt] + ":")
        for c in nhom[:8]:
            so[tt] += 1
            body.append("· " + _dong(c, ten_hang, cua_hang))
            if tt in ("dang_chay", "sap_toi"):
                ghi = _cau_thieu(c, ten_hang)
                if ghi:
                    body.append("  " + ghi)
                canh_bao += 1 if c["thieu"] else 0
            if tt == "chua_bat":
                body.append("  CTKM đang Disabled, POS sẽ không áp dù đã tới ngày.")
    if an and not (item or cua_hang):
        body.append(f"Còn {len(an)} CTKM đang bật trong LS nhưng không mặt hàng nào của chúng bán trong {NGAY_BAN} ngày qua tại "
                    f"{', '.join(du_lieu['cua_hang'])}, nên không liệt kê.")
    if tat and not (item or cua_hang):
        body.append(f"{len(tat)} CTKM khác đã tắt từ trước ngày {(du_lieu['hom_nay'] - timedelta(days=MOI_BAT_DAU)).strftime('%d/%m')} "
                    "và chưa hết hạn, không liệt kê.")
    body.append(f"Nguồn: LSC Periodic Discount, Validation Period, Store Price Group, Replen. Planned Event. Ngày tham chiếu "
                f"{du_lieu['hom_nay'].strftime('%d/%m/%Y')}.")

    dem = ", ".join(f"{so[k]} {nhom_tt[k].split(' (')[0].lower()}" for k in ("dang_chay", "sap_toi", "chua_bat", "da_ket_thuc") if so[k])
    cau = f"CTKM{(' ' + pham_vi) if pham_vi else ''}: {dem}."
    if canh_bao:
        cau += f" {canh_bao} CTKM chưa có đủ nhu cầu trong LS Replenishment, xem chi tiết."
    links = [(f"CTKM {c['no']} trong LS", link("ls_periodic_discounts", {"No.": c["no"]})) for c in chon[:3]]
    links.append(("Replen. Planned Events", link("ls_planned_events")))
    card = Card(title="Chương trình khuyến mãi" + (f" {pham_vi}" if pham_vi else ""), body="\n".join(body),
                facts=[(nhom_tt[k].split(" (")[0], str(so[k])) for k in ("dang_chay", "sap_toi", "chua_bat", "da_ket_thuc") if so[k]]
                + ([("Thiếu nhu cầu trong LS", str(canh_bao))] if canh_bao else []),
                ref=f"ctkm|{cua_hang}|{item['itemNo'] if item else ''}", kind="info", links=links)
    return [Delivery(uid, cau, card=card, skill=SKILL, ref=card.ref)]


def tom_tat_cho_brief(asst: Any, user: dict[str, Any], so_ngay: int = 14) -> list[Delivery]:
    """Mot dong trong brief sang: CTKM bat dau trong `so_ngay` ngay toi. Supply Chain va dieu phoi thay them cap chua co nhu
    cau trong LS Replenishment; quan ly cua hang chi thay CTKM ap cho cua hang minh. Khong co gi thi khong them dong."""
    du_lieu = doc(asst.gw)
    hom_nay = du_lieu["hom_nay"]
    noi = user.get("store_code") if user.get("role") in VAI_TRO_TAI_DIEM else ""
    toi = [c for c in tong_hop(du_lieu) if c["trang_thai"] == "sap_toi" and c["tu"] and c["tu"] <= hom_nay + timedelta(days=so_ngay)
           and any(not noi or s == noi for _, s in c["dang_ban"])]
    if not toi:
        return []
    ds = "; ".join(f"{c['ten']} từ {_ngay(c['tu'], hom_nay.year)}" for c in toi[:4])
    cau = f"CTKM sắp bắt đầu trong {so_ngay} ngày" + (f" tại {noi}" if noi else "") + f": {ds}."
    thieu = [c for c in toi if c["thieu"]]
    if thieu and not noi:
        cau += " " + "; ".join(f"{c['no']} chưa có nhu cầu trong LS Replenishment cho " +
                               ", ".join(f"{s}" for _, s in c["thieu"]) for c in thieu) + "."
    return [Delivery(user["user_id"], cau, skill=SKILL, ref="ctkm|brief")]
