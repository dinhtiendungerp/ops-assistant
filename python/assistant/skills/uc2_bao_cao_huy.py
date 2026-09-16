"""UC2 S3, nhom Tom tat: bao cao tuan hang huy cho quan ly va tai chinh.

Vi sao (16/09/2026). Tai lieu 09: "tong hop gia tri huy, nhom hang va cua hang nhieu nhat, nguyen nhan chinh, so voi tuan truoc".
Code tinh moi con so tu Item Ledger Entry (huy = Negative Adjmt. co lo tai cua hang), bang Inventory Health (lo het han con ton)
va bang de xuat (de xuat huy dang cho, chung tu nhap chua post). Nguyen nhan lay tu D2 (`uc2_nguyen_nhan`) tren cua so 28 ngay.
Model viet ba doan (mo_dau, nhan_xet, viec_tuan_toi), kiem so; bang do code ghep. Gui the trong chat va email (MAIL_TO),
mot ban moi tuan; vong quet sang A2 tu gui vao thu Hai.
"""
from __future__ import annotations

import html as _html
import json
import logging
from collections import defaultdict
from datetime import timedelta
from typing import Any

from ..bc_link import link
from ..cards import Card, fmt_qty, fmt_vnd
from . import Delivery
from . import uc2_nguyen_nhan as d2
from . import uc2_tom_tat as tt

log = logging.getLogger(__name__)
SKILL = "inventory_health"
VAI_NHAN = ("supply_chain", "admin")
SCHEMA = {"type": "object", "additionalProperties": False, "required": ["mo_dau", "nhan_xet", "viec_tuan_toi"],
          "properties": {"mo_dau": {"type": "string"}, "nhan_xet": {"type": "string"}, "viec_tuan_toi": {"type": "string"}}}
_SYSTEM = (
    "Bạn là trợ lý vận hành của Marou Chocolate, viết phần lời của báo cáo tuần hàng hủy gửi ban quản lý và tài chính. Dữ liệu là "
    "số liệu code đã tính từ Business Central. mo_dau: 2-3 câu tình hình tuần này so với tuần trước (số lượng, giá trị, tăng hay giảm "
    "theo phần trăm đã có). nhan_xet: 2-3 câu về nhóm hàng, cửa hàng hủy nhiều nhất và nguyên nhân chính theo bảng nguyen_nhan. "
    "viec_tuan_toi: 1-2 câu việc nên làm, nhắc số đề xuất hủy đang chờ duyệt và chứng từ chưa post nếu có. Tiếng Việt, giọng báo cáo, "
    "xưng 'tôi', chỉ dùng con số có trong dữ liệu, không tính lại, không gạch đầu dòng, không chào hỏi. Số lượng đếm bằng 'cái' (sản "
    "phẩm hủy theo lô, không phải đơn hàng); giá trị là giá vốn theo đơn vị tiền của company, ghi đúng con số, không thêm 'đồng', "
    "'triệu' hay đơn vị nào khác.")


def _pct(moi: float, cu: float) -> float | None:
    return round(100 * (moi - cu) / cu, 1) if cu else None


def so_lieu(asst: Any, days: int = 7) -> dict[str, Any]:
    gw = asst.gw
    today = gw.today()
    ten = {i["itemNo"]: i["description"] for i in gw.items()}
    tu = (today - timedelta(days=days)).isoformat()
    tu_truoc = (today - timedelta(days=2 * days)).isoformat()
    ile = [r for r in gw.ile_cua_so(2 * days + 1) if not gw.la_kho(r["locationCode"]) and r["entryType"] == "Negative Adjmt." and r["lotNo"]]
    gia = {}

    def don_gia(ma: str) -> float:
        if ma not in gia:
            gia[ma] = gw.unit_cost(ma)
        return gia[ma]

    tuan: dict[str, float] = defaultdict(float)
    for r in ile:
        q = -float(r["quantity"])
        ky = "nay" if r["postingDate"] > tu else ("truoc" if r["postingDate"] > tu_truoc else "")
        if not ky:
            continue
        tuan[f"{ky}_sl"] += q
        tuan[f"{ky}_gt"] += q * don_gia(r["itemNo"])
    theo_ma: dict[str, float] = defaultdict(float)
    theo_cua_hang: dict[str, float] = defaultdict(float)
    for r in ile:
        if r["postingDate"] > tu:
            q = -float(r["quantity"])
            theo_ma[r["itemNo"]] += q * don_gia(r["itemNo"])
            theo_cua_hang[r["locationCode"]] += q * don_gia(r["itemNo"])
    rows = gw.doc("inventoryHealthLines", [], top=5000)
    het_han = [r for r in rows if r.get("tier") == "Expired"]
    de_xuat = [p for p in asst.de_xuat_gop() if p.get("scenario") == "InventoryHealth" and p.get("action_type") == "WriteOff"]
    cho_duyet = [p for p in de_xuat if p.get("status") == "Proposed"]
    chua_post = [f for f in asst.mem.followups() if f["kind"] == "write_off_post" and f["status"] == "open"]
    nn = d2.phan_tich(asst, days=28, top=3)
    return {"ngay": today.strftime("%d/%m/%Y"), "tu_ngay": tt._ngay((today - timedelta(days=days - 1)).isoformat()), "den_ngay": today.strftime("%d/%m/%Y"),
            "so_ngay": days,
            "tuan_nay": {"so_luong": fmt_qty(tuan["nay_sl"]), "gia_tri": fmt_vnd(tuan["nay_gt"])},
            "tuan_truoc": {"so_luong": fmt_qty(tuan["truoc_sl"]), "gia_tri": fmt_vnd(tuan["truoc_gt"])},
            "thay_doi_pct": {"so_luong": _pct(tuan["nay_sl"], tuan["truoc_sl"]), "gia_tri": _pct(tuan["nay_gt"], tuan["truoc_gt"])},
            "theo_mat_hang": [{"mat_hang": ten.get(k, k), "ma": k, "gia_tri": fmt_vnd(v)} for k, v in sorted(theo_ma.items(), key=lambda kv: -kv[1])[:5]],
            "theo_cua_hang": [{"dia_diem": k, "gia_tri": fmt_vnd(v)} for k, v in sorted(theo_cua_hang.items(), key=lambda kv: -kv[1])[:5]],
            "lo_het_han_con_ton": {"so_lo": len(het_han), "gia_tri": fmt_vnd(sum(float(r.get("inventoryValue") or 0) for r in het_han))},
            "de_xuat_huy_cho_duyet": len(cho_duyet), "chung_tu_huy_chua_post": len(chua_post),
            "nguyen_nhan": {"cua_so_ngay": 28, "pho_bien": nn["nguyen_nhan_pho_bien"], "nhom_dau": nn["nhom"]},
            "_tuan": dict(tuan)}


def _mau(d: dict[str, Any]) -> tuple[str, str, str]:
    td_ = d["thay_doi_pct"]["gia_tri"]
    xu = "" if td_ is None else (f", tăng {td_}% so với tuần trước" if td_ > 0 else f", giảm {abs(td_)}% so với tuần trước")
    mo = (f"Tuần {d['tu_ngay']} đến {d['den_ngay']} hủy {d['tuan_nay']['so_luong']} cái, giá trị {d['tuan_nay']['gia_tri']}{xu} "
          f"(tuần trước {d['tuan_truoc']['so_luong']} cái, {d['tuan_truoc']['gia_tri']}).")
    nx = ""
    if d["theo_mat_hang"]:
        nx += f"Hủy nhiều nhất là {d['theo_mat_hang'][0]['mat_hang']} ({d['theo_mat_hang'][0]['gia_tri']})"
        if d["theo_cua_hang"]:
            nx += f", cửa hàng {d['theo_cua_hang'][0]['dia_diem']} ({d['theo_cua_hang'][0]['gia_tri']})"
        nx += ". "
    pb = d["nguyen_nhan"]["pho_bien"]
    if pb:
        k = max(pb.items(), key=lambda kv: kv[1])[0]
        nx += f"Trong 28 ngày, nguyên nhân gặp nhiều nhất là {k} ({pb[k]} cặp mặt hàng và cửa hàng)."
    vt = (f"Còn {d['lo_het_han_con_ton']['so_lo']} lô đã hết hạn đang tồn ({d['lo_het_han_con_ton']['gia_tri']}), "
          f"{d['de_xuat_huy_cho_duyet']} đề xuất hủy chờ duyệt và {d['chung_tu_huy_chua_post']} chứng từ hủy chưa post; tuần tới nên xử lý hết để sổ sách khớp thực tế.")
    return mo, nx or "Tuần này không có dòng hủy nào theo lô.", vt


def soan(asst: Any) -> dict[str, Any]:
    from .. import cong_ty as ctm
    d = so_lieu(asst)
    du_lieu = {k: v for k, v in d.items() if not k.startswith("_")}
    m, nguoi_soan = tt._goi_model(asst, "bao_cao_huy", _SYSTEM, du_lieu, SCHEMA, max_tokens=700)
    mo = nx = vt = ""
    if m is not None:
        mo, nx, vt = (str(m.get(k) or "").strip() for k in ("mo_dau", "nhan_xet", "viec_tuan_toi"))
        la = tt.so_la(du_lieu, mo, nx, vt)
        if not (mo and nx and vt):
            nguoi_soan, mo = "mẫu có sẵn (model trả về rỗng)", ""
        elif la:
            nguoi_soan, mo = "mẫu có sẵn (đoạn model viết có số không có trong dữ liệu: " + ", ".join(sorted(la)) + ")", ""
    if not mo:
        mo, nx, vt = _mau(d)
    ct = asst.cong_ty or ctm.hien_tai.get() or ""
    tieu_de = f"Báo cáo tuần hàng hủy {d['tu_ngay']} đến {d['den_ngay']}" + (f", {ctm.nhan(ct, 'day_du')}" if ct else "")
    bang = [("Tuần này", f"{d['tuan_nay']['so_luong']} cái, {d['tuan_nay']['gia_tri']}"),
            ("Tuần trước", f"{d['tuan_truoc']['so_luong']} cái, {d['tuan_truoc']['gia_tri']}"),
            ("Thay đổi giá trị", f"{d['thay_doi_pct']['gia_tri']}%" if d["thay_doi_pct"]["gia_tri"] is not None else "không so được"),
            ("Theo mặt hàng", "; ".join(f"{x['mat_hang']} {x['gia_tri']}" for x in d["theo_mat_hang"]) or "không có"),
            ("Theo cửa hàng", "; ".join(f"{x['dia_diem']} {x['gia_tri']}" for x in d["theo_cua_hang"]) or "không có"),
            ("Lô hết hạn còn tồn", f"{d['lo_het_han_con_ton']['so_lo']} lô, {d['lo_het_han_con_ton']['gia_tri']}"),
            ("Đề xuất hủy chờ duyệt", str(d["de_xuat_huy_cho_duyet"])), ("Chứng từ hủy chưa post", str(d["chung_tu_huy_chua_post"]))]
    duoi = "Số liệu từ Item Ledger Entry và bảng NWV Inventory Health trong Business Central; phần lời do trợ lý soạn, mọi con số đã đối chiếu với bảng."
    text = "\n".join([tieu_de, ""] + [f"{k}: {v}" for k, v in bang] + ["", mo, "", nx, "", vt, "", duoi])
    html = ("<div style='font-family:Segoe UI,Arial,sans-serif;font-size:14px;color:#222'>"
            f"<h3>{_html.escape(tieu_de)}</h3><table style='border-collapse:collapse;font-size:13px'>"
            + "".join(f"<tr><td style='border:1px solid #ccc;padding:4px 8px;background:#f3f3f3'>{_html.escape(k)}</td>"
                      f"<td style='border:1px solid #ccc;padding:4px 8px'>{_html.escape(str(v))}</td></tr>" for k, v in bang)
            + f"</table><p>{_html.escape(mo)}</p><p>{_html.escape(nx)}</p><p>{_html.escape(vt)}</p>"
            + f"<p><a href='{_html.escape(link('inventory_health'))}'>Mở bảng Inventory Health</a></p><p style='color:#777;font-size:12px'>{_html.escape(duoi)}</p></div>")
    return {"tieu_de": tieu_de, "text": text, "html": html, "nguoi_soan": nguoi_soan, "so_lieu": d, "bang": bang, "mo_dau": mo, "nhan_xet": nx, "viec_tuan_toi": vt}


def gui(asst: Any, nguoi: dict[str, Any] | None = None, bat_buoc: bool = False) -> list[Delivery]:
    """Soan, gui the cho Supply Chain va quan tri (va nguoi goi), gui email mot lan moi tuan (khoa theo tuan ISO)."""
    from .. import thu_dien_tu as td
    bc = soan(asst)
    d = bc["so_lieu"]
    ngay = asst.mem.now().astimezone().strftime("%Y-%m-%d")
    tuan = asst.gw.today().isocalendar()
    khoa = f"bao_cao_huy|{asst.cong_ty}|{tuan[0]}-W{tuan[1]}"
    if td.da_gui_hom_nay(khoa, ngay) and not bat_buoc:
        trang_thai = "đã gửi hôm nay, không gửi lại"
    else:
        kq = td.gui(tieu_de=f"[{asst.cong_ty or 'Marou'}] {bc['tieu_de']}", text=bc["text"], html=bc["html"], loai="bao_cao_huy", khoa=khoa,
                    cong_ty=asst.cong_ty, nguoi_soan=bc["nguoi_soan"], ngay=ngay)
        trang_thai = f"{', '.join(kq['den']) or '(chưa có)'}: {td.TEN_TRANG_THAI.get(kq['trang_thai'], kq['trang_thai'])}"
    card = Card(title=bc["tieu_de"], body="\n\n".join([bc["mo_dau"], bc["nhan_xet"], bc["viec_tuan_toi"]]),
                facts=bc["bang"] + [("Email", trang_thai), ("Người soạn", bc["nguoi_soan"])], kind="brief", ref="s3",
                links=[("Bảng Inventory Health trong BC", link("inventory_health")), ("Trang NWV Agent Proposals", link("agent_proposals"))])
    nhan = {u["user_id"] for vai in VAI_NHAN for u in asst.mem.users_by_role(vai)} | ({nguoi["user_id"]} if nguoi else set())
    return [Delivery(uid, f"{bc['tieu_de']}: hủy {d['tuan_nay']['so_luong']} cái, {d['tuan_nay']['gia_tri']}.", card, SKILL, "s3") for uid in sorted(nhan)]


def handle(asst: Any, user: dict[str, Any], text: str = "") -> list[Delivery]:
    if user.get("role") not in ("supply_chain", "admin", "retail_ops", "dispatcher"):
        return [Delivery(user["user_id"], "Báo cáo tuần hàng hủy là của Supply Chain và quản lý. Bạn hỏi \"vì sao cửa hàng tôi hủy nhiều\" thì tôi phân tích riêng cửa hàng bạn.", skill=SKILL)]
    return gui(asst, user, bat_buoc="gửi lại" in (text or "").lower() or "gui lai" in (text or "").lower())
