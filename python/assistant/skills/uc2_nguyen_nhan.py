"""UC2 D2, nhom Kham pha va phan tich: tim nguyen nhan goc cua hang huy.

Vi sao (16/09/2026). Tai lieu 09: "vi sao mot mat hang hoac cua hang huy nhieu: nhan du, ban cham, han ngan khi nhan, chuyen tre".
Code doc Item Ledger Entry 90 ngay tai cua hang: hang huy = Negative Adjmt. co lo (bo demo va Marou deu huy theo lo khi het han).
Voi moi cap mat hang x cua hang co huy, code tinh bon thuoc do va gan nhan nguyen nhan theo quy tac; model chi viet ket luan tren
bang do (kiem so). "Chuyen tre" chua do duoc vi bo demo khong co Transfer Order; thay bang "nhan don cuc": mot lan nhan vuot
suc ban trong mot han dung.

Thuoc do moi cap:
  ty_le_huy         huy / nhan trong cua so.
  nhan_so_voi_ban   nhan / ban; > 1,25 la nhan du.
  ban_so_voi_noi_khac  ban binh quan ngay tai cua hang / binh quan cac cua hang khac cung mat hang; < 0,7 la ban cham.
  han_luc_nhan      trung binh so ngay han con lai luc nhan / trung vi cua mat hang o moi cua hang; < 0,7 la han ngan khi nhan.
  nhan_don_cuc      lan nhan lon nhat > ban binh quan ngay x han thong thuong.
"""
from __future__ import annotations

import json
import logging
import statistics
from collections import defaultdict
from datetime import date, timedelta
from typing import Any

from ..bc_link import link
from ..cards import Card, fmt_qty, fmt_vnd
from . import Delivery
from . import uc2_tom_tat as tt

log = logging.getLogger(__name__)
SKILL = "inventory_health"
CUA_SO_NGAY = 90
TEN_NN = {"nhan_du": "nhận dư so với bán", "ban_cham": "bán chậm hơn cửa hàng khác", "han_ngan": "hạn ngắn khi nhận",
          "don_cuc": "nhận dồn cục vượt sức bán trong hạn", "binh_thuong": "hủy trong mức thường của hàng tươi"}
SCHEMA = {"type": "object", "additionalProperties": False, "required": ["ket_luan"], "properties": {"ket_luan": {"type": "string"}}}
_SYSTEM = (
    "Bạn là trợ lý vận hành của Marou Chocolate. Dữ liệu là bảng phân tích hàng hủy do trợ lý tính từ sổ kho Business Central: mỗi "
    "nhóm mặt hàng x cửa hàng có số hủy, giá trị, và các thước đo (nhận so với bán, bán so với nơi khác, hạn lúc nhận, nhận dồn cục) "
    "kèm nhãn nguyên nhân code đã gán. Viết ket_luan 3-5 câu tiếng Việt, xưng 'tôi': nguyên nhân chính là gì và dựa vào số nào, "
    "nguyên nhân có lặp giữa các cửa hàng hay mặt hàng không, việc nên sửa từ gốc. Chỉ dùng con số có trong dữ liệu, không tính lại, "
    "không suy ra số mới, không gạch đầu dòng, không chào hỏi.")


def _d(s: str | None) -> date | None:
    try:
        return date.fromisoformat(str(s)[:10]) if s else None
    except ValueError:
        return None


def phan_tich(asst: Any, item_no: str = "", noi: str = "", days: int = CUA_SO_NGAY, top: int = 8) -> dict[str, Any]:
    gw = asst.gw
    today = gw.today()
    ten = {i["itemNo"]: i["description"] for i in gw.items()}
    ile = [r for r in gw.ile_cua_so(days) if not gw.la_kho(r["locationCode"])]
    # Han luc nhan theo mat hang (moi cua hang) de lam moc so sanh
    han_ma: dict[str, list[int]] = defaultdict(list)
    for r in ile:
        if float(r["quantity"]) > 0 and r["lotNo"] and r["expirationDate"]:
            d1, d2 = _d(r["postingDate"]), _d(r["expirationDate"])
            if d1 and d2:
                han_ma[r["itemNo"]].append((d2 - d1).days)
    trung_vi = {ma: statistics.median(v) for ma, v in han_ma.items() if v}
    # Ban binh quan ngay theo mat hang x cua hang
    ban: dict[tuple, float] = defaultdict(float)
    for r in ile:
        if r["entryType"] == "Sale":
            ban[(r["itemNo"], r["locationCode"])] += -float(r["quantity"])
    nhom: dict[tuple, dict[str, Any]] = {}
    for r in ile:
        if r["entryType"] != "Negative Adjmt." or not r["lotNo"]:
            continue
        if (item_no and r["itemNo"] != item_no) or (noi and r["locationCode"] != noi):
            continue
        g = nhom.setdefault((r["itemNo"], r["locationCode"]), {"huy": 0.0, "so_lan": 0, "lo": set()})
        g["huy"] += -float(r["quantity"])
        g["so_lan"] += 1
        g["lo"].add(r["lotNo"])
    ra = []
    for (ma, loc), g in nhom.items():
        nhap = [x for x in ile if x["itemNo"] == ma and x["locationCode"] == loc and float(x["quantity"]) > 0]
        nhan = sum(float(x["quantity"]) for x in nhap)
        b = ban.get((ma, loc), 0.0)
        bq = b / days
        khac = [ban[(m2, l2)] / days for (m2, l2) in ban if m2 == ma and l2 != loc]
        bq_khac = statistics.mean(khac) if khac else 0.0
        han_nhan = [(_d(x["expirationDate"]) - _d(x["postingDate"])).days for x in nhap if x["lotNo"] and x["expirationDate"] and _d(x["expirationDate"]) and _d(x["postingDate"])]
        han_tb = statistics.mean(han_nhan) if han_nhan else 0.0
        tv = trung_vi.get(ma, 0.0)
        lon_nhat = max((float(x["quantity"]) for x in nhap), default=0.0)
        don_gia = gw.unit_cost(ma)
        nguyen_nhan = []
        if b > 0 and nhan / b > 1.25:
            nguyen_nhan.append("nhan_du")
        if bq_khac > 0 and bq < 0.7 * bq_khac:
            nguyen_nhan.append("ban_cham")
        if tv and han_tb and han_tb < 0.7 * tv:
            nguyen_nhan.append("han_ngan")
        # Mot lan nhan vuot 1,5 lan luong ban duoc trong mot han dung. Nguong 1,0 bat 22/25 cap trong bo demo (banh tuoi han 2 ngay,
        # ban 3 cai/ngay, nhan 10 la dinh), khong con phan biet duoc gi.
        if bq > 0 and tv and lon_nhat > 1.5 * bq * tv:
            nguyen_nhan.append("don_cuc")
        if not nguyen_nhan:
            nguyen_nhan.append("binh_thuong")
        ra.append({"ma": ma, "mat_hang": ten.get(ma, ma), "dia_diem": loc, "huy": fmt_qty(g["huy"]), "so_lan_huy": g["so_lan"], "so_lo_huy": len(g["lo"]),
                   "gia_tri_huy": fmt_vnd(g["huy"] * don_gia), "_gia_tri": g["huy"] * don_gia,
                   "nhan": fmt_qty(nhan), "ban": fmt_qty(b), "ty_le_huy_tren_nhan_pct": round(100 * g["huy"] / nhan, 1) if nhan else None,
                   "nhan_so_voi_ban": round(nhan / b, 2) if b else None, "ban_binh_quan_ngay": round(bq, 1),
                   "ban_binh_quan_noi_khac": round(bq_khac, 1), "han_luc_nhan_tb_ngay": round(han_tb, 1),
                   "han_thong_thuong_ngay": fmt_qty(tv) if tv else None, "lan_nhan_lon_nhat": fmt_qty(lon_nhat),
                   "nguyen_nhan": [TEN_NN[k] for k in nguyen_nhan], "_nn": nguyen_nhan})
    ra.sort(key=lambda x: -x["_gia_tri"])
    tong_huy = sum(float(x["huy"]) for x in ra)
    tong_gt = sum(x["_gia_tri"] for x in ra)
    dem_nn: dict[str, int] = defaultdict(int)
    for x in ra:
        for k in x["_nn"]:
            dem_nn[TEN_NN[k]] += 1
    pham_vi = ", ".join(p for p in [ten.get(item_no, item_no) if item_no else "", noi] if p) or "mọi mặt hàng, mọi cửa hàng"
    return {"ngay": today.strftime("%d/%m/%Y"), "cua_so_ngay": days, "pham_vi": pham_vi, "so_nhom": len(ra),
            "tong_huy": fmt_qty(tong_huy), "tong_gia_tri_huy": fmt_vnd(tong_gt), "nguyen_nhan_pho_bien": dict(dem_nn),
            "nhom": [{k: v for k, v in x.items() if not k.startswith("_")} for x in ra[:top]], "_nhom": ra}


def _ket_luan_mau(pt: dict[str, Any]) -> str:
    if not pt["nhom"]:
        return f"Trong {pt['cua_so_ngay']} ngày qua không có dòng hủy nào theo lô ở {pt['pham_vi']}."
    n = pt["nhom"][0]
    pho_bien = max(pt["nguyen_nhan_pho_bien"].items(), key=lambda kv: kv[1])[0] if pt["nguyen_nhan_pho_bien"] else ""
    cau = [f"Trong {pt['cua_so_ngay']} ngày, {pt['pham_vi']} hủy {pt['tong_huy']} cái, giá trị {pt['tong_gia_tri_huy']}, ở {pt['so_nhom']} cặp mặt hàng và cửa hàng.",
           f"Nặng nhất là {n['mat_hang']} tại {n['dia_diem']}: hủy {n['huy']} ({n['gia_tri_huy']}), nhận {n['nhan']} mà bán {n['ban']}, "
           f"bán {n['ban_binh_quan_ngay']}/ngày so với {n['ban_binh_quan_noi_khac']}/ngày ở nơi khác; nguyên nhân: {', '.join(n['nguyen_nhan'])}."]
    if pho_bien:
        cau.append(f"Nguyên nhân gặp nhiều nhất trong các cặp là {pho_bien} ({pt['nguyen_nhan_pho_bien'][pho_bien]} cặp).")
    return " ".join(cau)


def goi_y(asst: Any, item_no: str = "", noi: str = "", days: int = CUA_SO_NGAY) -> dict[str, Any]:
    pt = phan_tich(asst, item_no, noi, days)
    du_lieu = {k: v for k, v in pt.items() if not k.startswith("_")}
    khoa = f"d2:{item_no}|{noi}|{pt['ngay']}|{pt['tong_huy']}|{pt['so_nhom']}"
    cu = tt._kv(asst, khoa)
    if cu and getattr(asst, "_writer", None):
        try:
            return {**json.loads(cu), **du_lieu, "nho_lai": True}
        except ValueError:
            pass
    m, nguoi_soan = (None, "mẫu có sẵn (AI đang tắt)") if not pt["nhom"] else tt._goi_model(asst, "d2", _SYSTEM, du_lieu, SCHEMA, max_tokens=500)
    ket_luan = ""
    if m is not None:
        ket_luan = str(m.get("ket_luan") or "").strip()
        la = tt.so_la(du_lieu, ket_luan)
        if not ket_luan:
            nguoi_soan = "mẫu có sẵn (model trả về rỗng)"
        elif la:
            nguoi_soan, ket_luan = "mẫu có sẵn (đoạn model viết có số không có trong dữ liệu: " + ", ".join(sorted(la)) + ")", ""
    if not ket_luan:
        ket_luan = _ket_luan_mau(pt)
    ra = {"ket_luan": ket_luan, "nguoi_soan": nguoi_soan}
    if nguoi_soan.startswith("AI"):
        tt._dat_kv(asst, khoa, json.dumps(ra, ensure_ascii=False))
    return {**ra, **du_lieu, "nho_lai": False}


def the_nguyen_nhan(kq: dict[str, Any]) -> Card:
    facts = [("Phạm vi", f"{kq['pham_vi']}, {kq['cua_so_ngay']} ngày"), ("Tổng hủy", f"{kq['tong_huy']} cái, {kq['tong_gia_tri_huy']}")]
    for n in kq["nhom"][:5]:
        facts.append((f"{n['mat_hang']} · {n['dia_diem']}", f"hủy {n['huy']} ({n['gia_tri_huy']}), nhận {n['nhan']}, bán {n['ban']}: {', '.join(n['nguyen_nhan'])}"))
    facts.append(("Người soạn", kq["nguoi_soan"]))
    links = [("Bảng Inventory Health trong BC", link("inventory_health"))]
    for n in kq["nhom"][:2]:
        links.append((f"Sổ kho {n['mat_hang']} tại {n['dia_diem']}", link("item_ledger_entries", {"Item No.": n["ma"], "Location Code": n["dia_diem"]})))
    return Card(title=f"Nguyên nhân hàng hủy: {kq['pham_vi']}", body=kq["ket_luan"], facts=facts, kind="info", ref="d2", links=links)


def handle(asst: Any, user: dict[str, Any], intent: Any, text: str = "") -> list[Delivery]:
    # Cua hang: ma trong cau, ten cua hang trong cau ("Quan 1", "Ha Noi"), roi cua hang cua nguoi hoi.
    noi = getattr(intent, "store_hint", "") or (asst._tim_cua_hang(text) if text and hasattr(asst, "_tim_cua_hang") else "") \
        or user.get("store_code") or ""
    item = None
    if (getattr(intent, "item_text", "") or "").strip() and not (noi and noi.lower() in intent.item_text.lower()):
        item = asst.gw.find_item(intent.item_text, min_score=80)
    kq = goi_y(asst, item["itemNo"] if item else "", noi)
    return [Delivery(user["user_id"], f"Phân tích hàng hủy {kq['cua_so_ngay']} ngày, {kq['pham_vi']}.", the_nguyen_nhan(kq), SKILL, "d2")]
