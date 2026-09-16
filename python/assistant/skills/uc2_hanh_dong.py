"""UC2 D4, nhom Kham pha va phan tich: goi y hanh dong toi uu cho lo can date.

Vi sao (16/09/2026). Nut "Chuyen sang store ban nhanh" cu de xuat chuyen CA TON LO sang cua hang ban nhanh nhat, khong xet noi
nhan co ban het truoc han khong, va khong xet phan con lai lam gi. Tai lieu 09 (US-12, D4): chuyen vua du ban truoc han, phan
con lai giam gia hoac chap nhan huy; so sanh cac phuong an theo toc do ban con lai va gia von.

Ai lam gi. Code tinh moi con so: ban duoc tai cho truoc han, phan du, kha nang nhan cua tung cua hang (ban binh quan cua ho x
so ngay con lai sau van chuyen, tru ton ho dang co), so chuyen tung noi, gia tri cuu duoc hay mat. Code cung co mot de xuat
theo quy tac. Model (khi bat AI) doc bang phuong an do, chon mot phuong an va viet vi sao, co the khac de xuat cua code neu
noi duoc ly do tren so da co. Model khong tinh: moi chu so trong doan phai co trong du lieu, phuong an chon phai co trong bang.
Nguoi bam "Ghi de xuat theo phuong an" thi trong tro ly ghi de xuat vao BC (moi phan mot de xuat, qua policy, nguoi duyet quyet).
Muc giam gia chua co quy tac cua Marou (G3, cho khao sat) nen de xuat giam gia chi mang so luong.
"""
from __future__ import annotations

import json
import logging
import math
from typing import Any

from ..bc_link import link
from ..cards import Action, Card, fmt_qty, fmt_vnd
from . import Delivery
from . import inventory_health as ih
from . import uc2_tom_tat as tt

log = logging.getLogger(__name__)
SKILL = "inventory_health"
NGAY_VAN_CHUYEN = 1        # ngay hang di duong, tru khoi cua so ban cua noi nhan
SO_NOI_NHAN = 2

TEN_PA = {"giu": "Giữ tại chỗ, bán đến hạn", "chuyen": "Chuyển vừa đủ sang cửa hàng bán nhanh hơn",
          "chuyen_giam_gia": "Chuyển vừa đủ, phần còn lại giảm giá", "giam_gia": "Giảm giá phần dư ngay tại chỗ",
          "huy": "Chấp nhận hủy phần dư khi đến hạn"}
SCHEMA = {"type": "object", "additionalProperties": False, "required": ["chon", "vi_sao"],
          "properties": {"chon": {"type": "string"}, "vi_sao": {"type": "string"}}}


# ---------------------------------------------------------------- code tinh
def phan_tich(asst: Any, r: dict[str, Any]) -> dict[str, Any]:
    """Moi con so cua D4 nam o day. Ham thuan, cung dong ra cung ket qua, de nut 'Ghi de xuat' tinh lai y het."""
    qty = float(r.get("quantityOnHand") or 0)
    avg = float(r.get("avgDailySalesQty") or 0)
    dte = int(r.get("daysToExpiry") if r.get("daysToExpiry") is not None else -1)
    don_gia = float(r["inventoryValue"]) / qty if qty else 0.0
    # Hang dem cai: ban duoc tai cho lam tron xuong, phan du la so nguyen, de so chuyen va so giam gia khong le 0,9 cai.
    ban_tai_cho = float(math.floor(min(qty, avg * max(dte, 0))))
    du = round(qty - ban_tai_cho, 1)
    cua_so = max(0, dte - NGAY_VAN_CHUYEN)
    noi_nhan = []
    for x in asst.gw.stock_by_location(r["itemNo"]):
        if x["locationCode"] in (r["locationCode"], asst.gw.central_wh) or float(x.get("avgDaily") or 0) <= 0:
            continue
        # Ton cua ho ban truoc, phan con lai cua cua so moi la cho de nhan them. Lam tron xuong vi hang dem cai.
        kha_nang = math.floor(max(0.0, float(x["avgDaily"]) * cua_so - float(x.get("qty") or 0)))
        if kha_nang > 0:
            noi_nhan.append({"dia_diem": x["locationCode"], "ban_binh_quan_ngay": round(float(x["avgDaily"]), 1),
                             "ton_hien_co": fmt_qty(float(x.get("qty") or 0)), "nhan_duoc_toi_da": kha_nang})
    noi_nhan.sort(key=lambda x: -x["nhan_duoc_toi_da"])
    chuyen, con = [], math.floor(du)
    for x in noi_nhan[:SO_NOI_NHAN]:
        q = min(con, x["nhan_duoc_toi_da"])
        if q > 0:
            chuyen.append({"den": x["dia_diem"], "so_luong": q, "ban_binh_quan_ngay": x["ban_binh_quan_ngay"]})
            con -= q
    tong_chuyen = sum(c["so_luong"] for c in chuyen)
    du_sau_chuyen = round(du - tong_chuyen, 1)
    pa: dict[str, dict[str, Any]] = {}
    pa["giu"] = {"ban_duoc_truoc_han": fmt_qty(ban_tai_cho), "du_den_han": fmt_qty(du), "gia_tri_phan_du": fmt_vnd(du * don_gia)}
    if chuyen:
        pa["chuyen"] = {"chuyen": chuyen, "tong_chuyen": tong_chuyen, "giu_lai_ban_tai_cho": fmt_qty(ban_tai_cho),
                        "du_sau_chuyen": fmt_qty(du_sau_chuyen), "gia_tri_cuu_duoc": fmt_vnd(tong_chuyen * don_gia),
                        "gia_tri_phan_du": fmt_vnd(du_sau_chuyen * don_gia)}
        if du_sau_chuyen > 0:
            pa["chuyen_giam_gia"] = {**pa["chuyen"], "giam_gia_so_luong": fmt_qty(du_sau_chuyen)}
    if du > 0 and dte >= 0:
        pa["giam_gia"] = {"so_luong": fmt_qty(du), "gia_tri_rui_ro": fmt_vnd(du * don_gia), "muc_giam": "chưa có quy tắc của Marou, người duyệt đặt"}
    if du > 0:
        pa["huy"] = {"so_luong": fmt_qty(du), "gia_tri_mat": fmt_vnd(du * don_gia)}
    if du <= 0:
        de_xuat = "giu"
    elif chuyen and du_sau_chuyen <= 0:
        de_xuat = "chuyen"
    elif chuyen:
        de_xuat = "chuyen_giam_gia"
    elif dte >= 1 and avg > 0:
        de_xuat = "giam_gia"
    else:
        de_xuat = "huy"
    return {"line_id": r["id"], "mat_hang": r["itemDescription"], "ma": r["itemNo"], "dia_diem": r["locationCode"], "lo": r.get("lotNo") or "",
            "tang": tt.TEN_TANG.get(r["tier"], r["tier"]), "ton": fmt_qty(qty), "gia_von_don_vi": fmt_vnd(don_gia),
            "gia_tri_ton": fmt_vnd(float(r["inventoryValue"])), "han_dung": tt._ngay(r.get("expirationDate")), "con_ngay_den_han": dte,
            "ban_binh_quan_ngay_tai_cho": round(avg, 1), "ngay_van_chuyen": NGAY_VAN_CHUYEN, "noi_nhan": noi_nhan[:SO_NOI_NHAN],
            "phuong_an": {k: {"ten": TEN_PA[k], **v} for k, v in pa.items()}, "de_xuat_cua_code": de_xuat,
            "quy_tac": ["chuyển chỉ số mà nơi nhận bán hết trước hạn, sau khi bán hết tồn của họ",
                        "giảm giá và hủy luôn cần người duyệt", "mức giảm giá chưa có quy tắc của Marou"],
            "_du": du, "_du_sau_chuyen": du_sau_chuyen, "_chuyen": chuyen}


_SYSTEM = (
    "Bạn là trợ lý vận hành của Marou Chocolate, giúp Supply Chain chọn cách xử lý một lô cận date. Dữ liệu là bảng phương án đã "
    "được Business Central và trợ lý tính sẵn; bạn KHÔNG tính lại, không suy ra con số mới, chỉ dùng đúng số trong dữ liệu. "
    "Chọn một phương án (ghi đúng khóa trong phuong_an) và viết vi_sao 2-4 câu tiếng Việt, xưng 'tôi': so sánh với phương án gần "
    "nhất bằng số (giá trị cứu được, phần dư, nơi nhận và tốc độ bán của họ), nêu điều kiện phải đúng (ngày vận chuyển, nơi nhận "
    "bán hết tồn của họ trước). Có thể chọn khác de_xuat_cua_code nếu nói được lý do trên số đã có. Không chào hỏi, không gạch đầu dòng.")


def goi_y(asst: Any, line_id: str) -> dict[str, Any]:
    """Phan tich cong loi khuyen. Loi khuyen AI nho theo dong va thoi diem tinh."""
    r = next((x for x in asst.gw.doc("inventoryHealthLines", [], top=5000) if x.get("id") == line_id), None) \
        or asst.gw.client.get("inventoryHealthLines", line_id)
    pt = phan_tich(asst, r)
    du_lieu = {k: v for k, v in pt.items() if not k.startswith("_")}
    khoa = f"d4:{line_id}|{r.get('calculatedAt', '')}"
    cu = tt._kv(asst, khoa)
    if cu and getattr(asst, "_writer", None):
        try:
            return {**json.loads(cu), "phan_tich": pt, "nho_lai": True}
        except ValueError:
            pass
    m, nguoi_soan = tt._goi_model(asst, "d4", _SYSTEM, du_lieu, SCHEMA, max_tokens=450)
    chon, vi_sao = "", ""
    if m is not None:
        chon, vi_sao = _khoa_phuong_an(str(m.get("chon") or ""), pt["phuong_an"]), str(m.get("vi_sao") or "").strip()
        la = tt.so_la(du_lieu, vi_sao)
        if chon not in pt["phuong_an"]:
            log.warning("D4: model chon '%s' khong co trong bang %s", m.get("chon"), list(pt["phuong_an"]))
            nguoi_soan, chon = "mẫu có sẵn (model chọn phương án không có trong bảng)", ""
        elif la:
            nguoi_soan, chon = "mẫu có sẵn (đoạn model viết có số không có trong dữ liệu: " + ", ".join(sorted(la)) + ")", ""
        elif not vi_sao:
            nguoi_soan, chon = "mẫu có sẵn (model trả về rỗng)", ""
    if not chon:
        chon, vi_sao = pt["de_xuat_cua_code"], _vi_sao_mau(pt)
    kq = {"chon": chon, "vi_sao": vi_sao, "nguoi_soan": nguoi_soan}
    if nguoi_soan.startswith("AI"):
        tt._dat_kv(asst, khoa, json.dumps(kq, ensure_ascii=False))
    return {**kq, "phan_tich": pt, "nho_lai": False}


def _khoa_phuong_an(chon: str, pa: dict[str, Any]) -> str:
    """Model hay tra ten phuong an ("Chuyển vừa đủ...") thay vi khoa ("chuyen"). Nhan ca hai, khong nhan khop mo."""
    c = chon.strip().strip("\"'").lower()
    if c in pa:
        return c
    for k, v in pa.items():
        if c == v["ten"].lower() or c == f"{k}: {v['ten']}".lower():
            return k
    return c


def _vi_sao_mau(pt: dict[str, Any]) -> str:
    pa = pt["phuong_an"]
    de = pt["de_xuat_cua_code"]
    dau = (f"Lô còn {pt['con_ngay_den_han']} ngày, tại {pt['dia_diem']} bán {pt['ban_binh_quan_ngay_tai_cho']}/ngày nên đến hạn bán được "
           f"{pa['giu']['ban_duoc_truoc_han']}, dư {pa['giu']['du_den_han']} ({pa['giu']['gia_tri_phan_du']}).")
    if de in ("chuyen", "chuyen_giam_gia"):
        c = pa["chuyen"]
        noi = ", ".join(f"{x['so_luong']} sang {x['den']} (bán {x['ban_binh_quan_ngay']}/ngày)" for x in c["chuyen"])
        cau = f" Chuyển {noi} sau khi trừ {pt['ngay_van_chuyen']} ngày vận chuyển và tồn sẵn của họ, cứu được {c['gia_tri_cuu_duoc']}."
        if de == "chuyen_giam_gia":
            cau += f" Còn dư {c['du_sau_chuyen']} không nơi nào bán kịp, đề xuất giảm giá tại chỗ."
        return dau + cau
    if de == "giam_gia":
        return dau + " Không cửa hàng nào còn chỗ bán thêm trước hạn, nên giảm giá phần dư ngay tại chỗ."
    if de == "huy":
        return dau + " Không còn ngày để bán hay chuyển, phần dư sẽ phải hủy khi đến hạn."
    return dau + " Bán hết trước hạn theo tốc độ hiện tại, không cần làm gì thêm."


# ---------------------------------------------------------------- the va hanh dong
def the_phuong_an(kq: dict[str, Any]) -> Card:
    pt, pa = kq["phan_tich"], kq["phan_tich"]["phuong_an"]
    facts = [("Lô", f"{pt['lo'] or 'không mã'} tại {pt['dia_diem']}, tồn {pt['ton']} ({pt['gia_tri_ton']}), còn {pt['con_ngay_den_han']} ngày")]
    for k, v in pa.items():
        if k == "giu":
            so = f"bán được {v['ban_duoc_truoc_han']}, dư {v['du_den_han']} ({v['gia_tri_phan_du']})"
        elif k in ("chuyen", "chuyen_giam_gia"):
            so = "chuyển " + ", ".join(f"{x['so_luong']} sang {x['den']}" for x in v["chuyen"]) + f", cứu {v['gia_tri_cuu_duoc']}"
            so += f", dư {v['du_sau_chuyen']}" + (" giảm giá" if k == "chuyen_giam_gia" else "")
        elif k == "giam_gia":
            so = f"{v['so_luong']} cái, giá trị {v['gia_tri_rui_ro']}, mức giảm do người duyệt đặt"
        else:
            so = f"{v['so_luong']} cái, mất {v['gia_tri_mat']}"
        facts.append((("→ " if k == kq["chon"] else "") + v["ten"], so))
    facts.append(("Người soạn", kq["nguoi_soan"]))
    actions = [Action("ih_d4_apply", f"Ghi đề xuất: {TEN_PA[kq['chon']]}", "positive", payload={"chon": kq["chon"]})]
    khac = next((k for k in ("giam_gia", "huy", "chuyen") if k in pa and k != kq["chon"]), None)
    if khac:
        actions.append(Action("ih_d4_apply", f"Thay vào đó: {TEN_PA[khac]}", payload={"chon": khac}))
    loc = {"Item No.": pt["ma"], "Location Code": pt["dia_diem"], "Lot No.": pt["lo"]}
    return Card(title=f"Phương án cho lô cận date: {pt['mat_hang']} tại {pt['dia_diem']}", body=kq["vi_sao"], facts=facts, ref=pt["line_id"],
                kind="info", actions=actions,
                links=[("Item Ledger Entries của lô", link("item_ledger_entries", loc)), ("Dòng Inventory Health", link("inventory_health", loc))])


def on_goi_y(asst: Any, user: dict[str, Any], line_id: str) -> list[Delivery]:
    r = asst.gw.client.get("inventoryHealthLines", line_id)
    dte = r.get("daysToExpiry")
    if dte is None or dte < 0:
        return [Delivery(user["user_id"], "Lô này đã hết hạn, không còn phương án bán hay chuyển. Dùng Đề xuất hủy.", skill=SKILL)]
    kq = goi_y(asst, line_id)
    return [Delivery(user["user_id"], f"Phương án cho {r['itemDescription']} tại {r['locationCode']}", the_phuong_an(kq), SKILL, line_id)]


def on_ap_dung(asst: Any, user: dict[str, Any], line_id: str, chon: str) -> list[Delivery]:
    """Ghi de xuat theo phuong an da chon: moi phan mot de xuat, khoa rieng, qua policy va nguoi duyet nhu moi de xuat khac."""
    r = asst.gw.client.get("inventoryHealthLines", line_id)
    pt = phan_tich(asst, r)
    if chon not in pt["phuong_an"]:
        return [Delivery(user["user_id"], "Phương án này không còn đúng với số hiện tại, tôi tính lại rồi, bạn bấm Phương án xử lý lần nữa.", skill=SKILL)]
    goc = f"{r['itemNo']}|{r['locationCode']}|{r.get('lotNo', '')}"
    out: list[Delivery] = []
    ly = f"D4: {TEN_PA[chon]}. " + _vi_sao_mau(pt)
    if chon in ("chuyen", "chuyen_giam_gia"):
        for c in pt["_chuyen"]:
            out += ih.on_propose(asst, user, line_id, "Transfer", c["den"], quantity=c["so_luong"], ref=f"{goc}|TO|{c['den']}",
                                 rationale=f"Chuyển {c['so_luong']} sang {c['den']} (bán {c['ban_binh_quan_ngay']}/ngày), vừa đủ bán trước hạn "
                                           f"sau {NGAY_VAN_CHUYEN} ngày vận chuyển. {ly}")
    if chon == "chuyen_giam_gia":
        out += ih.on_propose(asst, user, line_id, "Markdown", quantity=pt["_du_sau_chuyen"], ref=f"{goc}|MD",
                             rationale=f"Giảm giá {fmt_qty(pt['_du_sau_chuyen'])} còn dư sau khi chuyển. {ly}")
    elif chon == "giam_gia":
        out += ih.on_propose(asst, user, line_id, "Markdown", quantity=pt["_du"], ref=f"{goc}|MD", rationale=f"Giảm giá phần dư {fmt_qty(pt['_du'])}. {ly}")
    elif chon == "huy":
        out += ih.on_propose(asst, user, line_id, "WriteOff", quantity=pt["_du"], ref=f"{goc}|WO", rationale=f"Hủy phần dư {fmt_qty(pt['_du'])} khi đến hạn. {ly}")
    elif chon == "giu":
        out += ih.on_propose(asst, user, line_id, "ReviewOnly", ref=f"{goc}|GIU", rationale=ly)
    return out
