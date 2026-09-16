"""UC2 D3, nhom Kham pha va phan tich: phat hien bat thuong trong so kho.

Vi sao (16/09/2026). Tai lieu 09: "lo ban sau han, hang nhan ve han qua ngan, lech kiem ke lon, cua hang huy tang dot bien".
Code quet Item Ledger Entry va bang Inventory Health theo nam tin hieu co dinh, moi tin hieu la mot dong co con so va nguon;
model chi xep thu tu va viet nhan xet tren danh sach do (kiem so, kiem chi so). Tat AI thi nhan xet do code ghep.

Nam tin hieu:
  1. ban_sau_han      dong Sale co lo ma ngay ban sau han dung cua lo.
  2. nhan_han_ngan    hang ve cua hang (dong nhap co lo) ma han con lai luc nhan < mot nua han thong thuong cua mat hang do
                      (trung vi han-luc-nhan trong 90 ngay, tinh tren moi cua hang).
  3. huy_tang         cua hang huy (Negative Adjmt. co lo) 14 ngay gan nhat gap doi 14 ngay truoc, tu 5 cai tro len.
  4. ton_khong_ban    cua hang con ton ma 7 ngay khong ban trong khi cua hang khac van ban mat hang do (bang Inventory Health).
  5. het_hang_lap     tang StockOutRisk va bi loai tu 5 ngay het hang tro len trong cua so tinh (bang Inventory Health).
"Lech kiem ke lon" trong tai lieu 09 chua lam duoc: bo demo khong co phieu kiem ke hay reason code de tach dieu chinh kiem ke
khoi nhan hang; can Marou xac nhan quy trinh kiem ke.
"""
from __future__ import annotations

import json
import logging
import statistics
from collections import defaultdict
from datetime import date, timedelta
from typing import Any

from ..bc_link import link
from ..cards import Card, fmt_qty
from . import Delivery
from . import uc2_tom_tat as tt

log = logging.getLogger(__name__)
SKILL = "inventory_health"
CUA_SO_NGAY = 28
NGAY_KHONG_BAN = 7
TEN_LOAI = {"ban_sau_han": "Bán sau hạn dùng", "nhan_han_ngan": "Nhận hàng hạn quá ngắn", "huy_tang": "Hủy tăng đột biến",
            "ton_khong_ban": "Còn tồn mà không bán", "het_hang_lap": "Hết hàng lặp lại"}
SCHEMA = {"type": "object", "additionalProperties": False, "required": ["uu_tien", "nhan_xet"],
          "properties": {"uu_tien": {"type": "array", "items": {"type": "string"}}, "nhan_xet": {"type": "string"}}}
_SYSTEM = (
    "Bạn là trợ lý vận hành của Marou Chocolate. Dữ liệu là danh sách tín hiệu bất thường mà trợ lý đã quét từ sổ kho Business "
    "Central, mỗi tín hiệu có id, loại, mặt hàng, địa điểm và con số. Chọn tối đa 3 id đáng xử lý trước (uu_tien) và viết nhan_xet "
    "3-5 câu tiếng Việt, xưng 'tôi': vì sao ba tín hiệu đó quan trọng hơn, có dấu hiệu nào lặp ở cùng cửa hàng hay cùng mặt hàng "
    "không, việc nên làm. Chỉ dùng con số có trong dữ liệu, không tính lại, không suy ra số mới, không gạch đầu dòng, không chào hỏi.")


def _d(s: str | None) -> date | None:
    try:
        return date.fromisoformat(str(s)[:10]) if s else None
    except ValueError:
        return None


def quet(asst: Any, cua_so: int = CUA_SO_NGAY, noi: str = "") -> dict[str, Any]:
    """Code quet. Tra {"ngay","cua_so_ngay","tin_hieu":[...],"theo_loai":{...},"khong_lam_duoc":[...]}."""
    gw = asst.gw
    today = gw.today()
    moc = (today - timedelta(days=cua_so)).isoformat()
    moc14 = (today - timedelta(days=14)).isoformat()
    moc28 = (today - timedelta(days=28)).isoformat()
    ten = {i["itemNo"]: i["description"] for i in gw.items()}
    ile = [r for r in gw.ile_cua_so(90) if not gw.la_kho(r["locationCode"]) and (not noi or r["locationCode"] == noi)]
    tin: list[dict[str, Any]] = []

    def them(loai: str, r: dict[str, Any], so: dict[str, Any], cau: str, muc: str = "vừa", lo: str = "") -> None:
        tin.append({"id": f"T{len(tin) + 1}", "loai": loai, "ten_loai": TEN_LOAI[loai], "muc_do": muc, "ma": r["itemNo"],
                    "mat_hang": ten.get(r["itemNo"], r["itemNo"]), "dia_diem": r["locationCode"], "lo": lo, "so": so, "cau": cau})

    # 1. Ban sau han
    gom: dict[tuple, dict[str, Any]] = {}
    for r in ile:
        if r["entryType"] == "Sale" and r["lotNo"] and r["expirationDate"] and r["postingDate"] > r["expirationDate"] and r["postingDate"] >= moc:
            g = gom.setdefault((r["itemNo"], r["locationCode"], r["lotNo"]), {"so_luong": 0.0, "so_lan": 0, "han": r["expirationDate"], "cuoi": r["postingDate"]})
            g["so_luong"] += -float(r["quantity"])
            g["so_lan"] += 1
            g["cuoi"] = max(g["cuoi"], r["postingDate"])
    for (ma, loc, lo), g in sorted(gom.items(), key=lambda kv: -kv[1]["so_luong"]):
        them("ban_sau_han", {"itemNo": ma, "locationCode": loc}, {"so_luong": fmt_qty(g["so_luong"]), "so_lan": g["so_lan"], "han_dung": tt._ngay(g["han"]), "ban_cuoi": tt._ngay(g["cuoi"])},
             f"{ten.get(ma, ma)} lô {lo} tại {loc} bán {fmt_qty(g['so_luong'])} cái sau hạn {tt._ngay(g['han'])}, lần cuối {tt._ngay(g['cuoi'])}.", "cao", lo)

    # 2. Nhan hang han qua ngan
    nhap = [r for r in ile if float(r["quantity"]) > 0 and r["lotNo"] and r["expirationDate"]]
    han_theo_ma: dict[str, list[int]] = defaultdict(list)
    for r in nhap:
        d1, d2 = _d(r["postingDate"]), _d(r["expirationDate"])
        if d1 and d2:
            han_theo_ma[r["itemNo"]].append((d2 - d1).days)
    trung_vi = {ma: statistics.median(v) for ma, v in han_theo_ma.items() if len(v) >= 5}
    gom2: dict[tuple, dict[str, Any]] = {}
    for r in nhap:
        tv = trung_vi.get(r["itemNo"])
        if not tv or tv < 2 or r["postingDate"] < moc:
            continue
        con = (_d(r["expirationDate"]) - _d(r["postingDate"])).days
        if con < 0.5 * tv:
            g = gom2.setdefault((r["itemNo"], r["locationCode"]), {"so_lan": 0, "so_luong": 0.0, "con_it_nhat": con, "trung_vi": tv})
            g["so_lan"] += 1
            g["so_luong"] += float(r["quantity"])
            g["con_it_nhat"] = min(g["con_it_nhat"], con)
    for (ma, loc), g in sorted(gom2.items(), key=lambda kv: -kv[1]["so_luong"]):
        them("nhan_han_ngan", {"itemNo": ma, "locationCode": loc},
             {"so_lan": g["so_lan"], "so_luong": fmt_qty(g["so_luong"]), "han_con_it_nhat_ngay": g["con_it_nhat"], "han_thong_thuong_ngay": fmt_qty(g["trung_vi"])},
             f"{ten.get(ma, ma)} về {loc} {g['so_lan']} lần với hạn còn dưới nửa mức thường ({fmt_qty(g['trung_vi'])} ngày), thấp nhất {g['con_it_nhat']} ngày, tổng {fmt_qty(g['so_luong'])} cái.",
             "cao" if g["so_lan"] >= 3 else "vừa")

    # 3. Huy tang dot bien theo cua hang
    huy_moi: dict[str, float] = defaultdict(float)
    huy_truoc: dict[str, float] = defaultdict(float)
    huy_ma: dict[str, dict[str, float]] = defaultdict(lambda: defaultdict(float))
    for r in ile:
        if r["entryType"] == "Negative Adjmt." and r["lotNo"] and r["postingDate"] >= moc28:
            q = -float(r["quantity"])
            if r["postingDate"] >= moc14:
                huy_moi[r["locationCode"]] += q
                huy_ma[r["locationCode"]][r["itemNo"]] += q
            else:
                huy_truoc[r["locationCode"]] += q
    for loc in sorted(huy_moi):
        m, t = huy_moi[loc], huy_truoc.get(loc, 0.0)
        if m >= 5 and m >= 2 * max(t, 1):
            top = max(huy_ma[loc].items(), key=lambda kv: kv[1])
            them("huy_tang", {"itemNo": top[0], "locationCode": loc},
                 {"huy_14_ngay": fmt_qty(m), "huy_14_ngay_truoc": fmt_qty(t), "mat_hang_huy_nhieu_nhat": fmt_qty(top[1])},
                 f"{loc} hủy {fmt_qty(m)} cái trong 14 ngày, so với {fmt_qty(t)} của 14 ngày trước; nhiều nhất là {ten.get(top[0], top[0])} ({fmt_qty(top[1])}).", "cao")

    # 4 va 5 tu bang Inventory Health
    rows = [r for r in gw.doc("inventoryHealthLines", [], top=5000) if not gw.la_kho(r["locationCode"]) and (not noi or r["locationCode"] == noi)]
    tat_ca = gw.doc("inventoryHealthLines", [], top=5000)
    ban_o_dau: dict[str, set[str]] = defaultdict(set)
    for r in tat_ca:
        if float(r.get("avgDailySalesQty") or 0) > 0 and not gw.la_kho(r["locationCode"]):
            ban_o_dau[r["itemNo"]].add(r["locationCode"])
    for r in sorted(rows, key=lambda x: -float(x.get("inventoryValue") or 0)):
        dsls = int(r.get("daysSinceLastSale") or 0)
        noi_khac = ban_o_dau.get(r["itemNo"], set()) - {r["locationCode"]}
        if float(r.get("quantityOnHand") or 0) > 0 and dsls >= NGAY_KHONG_BAN and noi_khac and r.get("tier") != "Expired":
            them("ton_khong_ban", r, {"ton": fmt_qty(float(r["quantityOnHand"])), "ngay_khong_ban": dsls, "cua_hang_khac_dang_ban": sorted(noi_khac)},
                 f"{r['itemDescription']} tại {r['locationCode']} còn {fmt_qty(float(r['quantityOnHand']))} mà {dsls} ngày không bán, trong khi {', '.join(sorted(noi_khac))} vẫn bán.",
                 "vừa", r.get("lotNo") or "")
    for r in sorted(rows, key=lambda x: -int(x.get("daysCensored") or 0)):
        cen = int(r.get("daysCensored") or 0)
        if r.get("tier") == "StockOutRisk" and cen >= 5:
            them("het_hang_lap", r, {"ngay_het_hang_trong_cua_so": cen, "ngay_du_ban": r.get("daysOfCover"), "ban_binh_quan_ngay": round(float(r.get("avgDailySalesQty") or 0), 1)},
                 f"{r['itemDescription']} tại {r['locationCode']} đã hết hàng {cen} ngày trong cửa sổ tính và lại sắp hết (đủ bán {r.get('daysOfCover')} ngày).", "cao" if cen >= 10 else "vừa")

    theo_loai = {TEN_LOAI[k]: sum(1 for t in tin if t["loai"] == k) for k in TEN_LOAI}
    return {"ngay": today.strftime("%d/%m/%Y"), "cua_so_ngay": cua_so, "pham_vi": noi or "mọi cửa hàng", "tin_hieu": tin, "theo_loai": theo_loai,
            "khong_lam_duoc": ["lệch kiểm kê lớn: bộ dữ liệu chưa có phiếu kiểm kê hay reason code để tách khỏi nhận hàng"]}


def _nhan_xet_mau(kq: dict[str, Any]) -> tuple[list[str], str]:
    cao = [t for t in kq["tin_hieu"] if t["muc_do"] == "cao"] or kq["tin_hieu"]
    top = cao[:3]
    if not kq["tin_hieu"]:
        return [], f"Trong {kq['cua_so_ngay']} ngày qua tôi không thấy tín hiệu bất thường nào ở {kq['pham_vi']}."
    theo = ", ".join(f"{v} {k.lower()}" for k, v in kq["theo_loai"].items() if v)
    return [t["id"] for t in top], (f"Trong {kq['cua_so_ngay']} ngày qua có {len(kq['tin_hieu'])} tín hiệu: {theo}. "
                                     f"Nên xem trước: " + " ".join(t["cau"] for t in top))


def goi_y(asst: Any, cua_so: int = CUA_SO_NGAY, noi: str = "") -> dict[str, Any]:
    kq = quet(asst, cua_so, noi)
    du_lieu = {k: v for k, v in kq.items()}
    du_lieu["tin_hieu"] = [{k: v for k, v in t.items() if k != "cau"} for t in kq["tin_hieu"][:40]]
    khoa = f"d3:{noi}|{kq['ngay']}|{len(kq['tin_hieu'])}|{sum(t['so'].get('so_lan', 0) or 0 for t in kq['tin_hieu'])}"
    cu = tt._kv(asst, khoa)
    if cu and getattr(asst, "_writer", None):
        try:
            return {**json.loads(cu), **kq, "nho_lai": True}
        except ValueError:
            pass
    m, nguoi_soan = (None, "mẫu có sẵn (AI đang tắt)") if not kq["tin_hieu"] else tt._goi_model(asst, "d3", _SYSTEM, du_lieu, SCHEMA, max_tokens=500)
    uu_tien, nhan_xet = [], ""
    if m is not None:
        ids = {t["id"] for t in kq["tin_hieu"]}
        uu_tien = [str(x) for x in (m.get("uu_tien") or []) if str(x) in ids][:3]
        nhan_xet = str(m.get("nhan_xet") or "").strip()
        la = tt.so_la(du_lieu, nhan_xet)
        if not nhan_xet or not uu_tien:
            nguoi_soan, nhan_xet = "mẫu có sẵn (model trả về rỗng hoặc chọn id lạ)", ""
        elif la:
            nguoi_soan, nhan_xet = "mẫu có sẵn (đoạn model viết có số không có trong dữ liệu: " + ", ".join(sorted(la)) + ")", ""
    if not nhan_xet:
        uu_tien, nhan_xet = _nhan_xet_mau(kq)
    ra = {"uu_tien": uu_tien, "nhan_xet": nhan_xet, "nguoi_soan": nguoi_soan}
    if nguoi_soan.startswith("AI"):
        tt._dat_kv(asst, khoa, json.dumps(ra, ensure_ascii=False))
    return {**ra, **kq, "nho_lai": False}


def the_bat_thuong(kq: dict[str, Any]) -> Card:
    theo = {t["id"]: t for t in kq["tin_hieu"]}
    dong = [f"{i}. {theo[x]['cau']}" for i, x in enumerate(kq["uu_tien"], 1) if x in theo]
    con = [t for t in kq["tin_hieu"] if t["id"] not in kq["uu_tien"]]
    body = kq["nhan_xet"]
    if dong:
        body += "\n\n" + "\n".join(dong)
    if con:
        body += "\n\nCác tín hiệu khác:\n" + "\n".join(f"- {t['cau']}" for t in con[:12]) + (f"\n- và {len(con) - 12} tín hiệu nữa" if len(con) > 12 else "")
    facts = [(k, str(v)) for k, v in kq["theo_loai"].items()] + [("Cửa sổ", f"{kq['cua_so_ngay']} ngày, {kq['pham_vi']}"), ("Người soạn", kq["nguoi_soan"])]
    links = [("Bảng Inventory Health trong BC", link("inventory_health"))]
    for x in kq["uu_tien"][:3]:
        t = theo.get(x)
        if t:
            links.append((f"Sổ kho {t['mat_hang']} tại {t['dia_diem']}", link("item_ledger_entries", {"Item No.": t["ma"], "Location Code": t["dia_diem"], "Lot No.": t["lo"]})))
    return Card(title=f"{len(kq['tin_hieu'])} tín hiệu bất thường trong {kq['cua_so_ngay']} ngày", body=body, facts=facts, kind="info", ref="d3", links=links)


def handle(asst: Any, user: dict[str, Any], intent: Any = None, text: str = "") -> list[Delivery]:
    noi = getattr(intent, "store_hint", "") or user.get("store_code") or ""
    kq = goi_y(asst, noi=noi)
    return [Delivery(user["user_id"], f"Bất thường {kq['cua_so_ngay']} ngày qua tại {kq['pham_vi']}: {len(kq['tin_hieu'])} tín hiệu.",
                     the_bat_thuong(kq), SKILL, "d3")]
