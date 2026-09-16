"""Email cho nguoi duyet khi co de xuat moi, phan loi do AI soan.

Dung hoi toi 16/09/2026, nhin the "Da ghi de xuat WriteOff ... Toi da bao nguoi duyet ngay trong chat cua ho": "phan nay
co gui qua email duoc khong, dung AI soan email". Truoc do de xuat moi chi day the vao hop thu chat cua Supply Chain va
dieu phoi; ai khong mo tro ly thi khong biet.

Cach lam giong email nhac post va bien ban huy: code dien bang so lieu (mat hang, lo, ton, gia tri, tang, hanh dong, so
luong, nguoi de nghi, policy) va link BC; model chi viet doan mo dau (tinh hinh, vi sao can duyet som) va doan ket (viec
can lam). Moi chu so model viet phai co trong du lieu dua model, sai thi dung mau va ghi ro. Tat AI thi dung mau.
Nguoi nhan la MAIL_TO (hop thu bo phan duyet), vi nguoi dung demo khong co dia chi email rieng.
Quet sang (A2) ghi toi 10 de xuat mot luot nen KHONG gui email tung cai; quet da co brief va email rieng.
"""
from __future__ import annotations

import html as _html
import logging
from typing import Any

from ..bc_link import link
from ..cards import Card, fmt_qty, fmt_vnd
from . import Delivery
from . import uc2_tom_tat as tt

log = logging.getLogger(__name__)
SKILL = "thu_de_xuat"
KHONG_GUI_CHO = {"tro_ly"}                        # nguoi de nghi la bot quet sang thi khong gui

TEN_HANH_DONG = {"WriteOff": "hủy hàng", "Markdown": "giảm giá", "BlockPurchase": "chặn mua thêm", "Transfer": "chuyển hàng",
                 "ReviewOnly": "ghi nhận theo dõi", "Purchase": "đặt mua", "PostReceipt": "post nhận hàng"}
SCHEMA = {"type": "object", "additionalProperties": False, "required": ["mo_dau", "ket"],
          "properties": {"mo_dau": {"type": "string"}, "ket": {"type": "string"}}}
_SYSTEM = ("Bạn là trợ lý vận hành của Marou Chocolate, viết email tiếng Việt báo người duyệt có một đề xuất xử lý tồn kho mới. "
           "Chỉ viết hai đoạn: mo_dau (2-3 câu: tình hình của lô hàng, vì sao đề xuất, mức độ gấp theo hạn dùng hoặc rủi ro) và "
           "ket (1-2 câu: việc cần làm là mở trợ lý hoặc Business Central để duyệt hay từ chối; nói rõ trợ lý không tự làm). "
           "Xưng 'anh chị'. Không chào hỏi dài, không liệt kê lại bảng vì code sẽ chèn bảng. Chỉ dùng con số có trong dữ liệu, "
           "không tính, không thêm đơn vị tiền.")


def du_lieu(asst: Any, user: dict[str, Any], prop: dict[str, Any], r: dict[str, Any], decision: Any) -> dict[str, Any]:
    from .. import cong_ty as ctm
    ct = asst.cong_ty or ctm.hien_tai.get() or ""
    return {"company": ctm.nhan(ct) if ct else "Marou", "ngay": asst.gw.today().strftime("%d/%m/%Y"),
            "hanh_dong": TEN_HANH_DONG.get(prop["action_type"], prop["action_type"]), "ma_hanh_dong": prop["action_type"],
            "mat_hang": r["itemDescription"], "ma": r["itemNo"], "dia_diem": r["locationCode"], "lo": r.get("lotNo") or "",
            "den": prop.get("to_loc") or "", "so_luong": fmt_qty(float(prop.get("quantity") or 0)),
            "ton": fmt_qty(r["quantityOnHand"]), "gia_tri_ton": fmt_vnd(r["inventoryValue"]),
            "tang": r["tier"], "diem_rui_ro": r["riskScore"], "ly_do_tang": r.get("riskReason", ""),
            "han_dung": r.get("expirationDate") or "", "con_ngay_den_han": r.get("daysToExpiry"),
            "ngay_phu": r.get("daysOfCover"), "ly_do_de_xuat": prop.get("rationale", ""),
            "nguoi_de_nghi": user["display_name"], "policy": getattr(decision, "reason", "") or ""}


def _mau(d: dict[str, Any]) -> tuple[str, str]:
    han = f", còn {d['con_ngay_den_han']} ngày đến hạn" if d.get("con_ngay_den_han") is not None and d["han_dung"] else ""
    mo = (f"{d['nguoi_de_nghi']} vừa đề nghị {d['hanh_dong']} {d['so_luong']} {d['mat_hang']} tại {d['dia_diem']}"
          f"{(' lô ' + d['lo']) if d['lo'] else ''}. Lô đang ở tầng {d['tang']}{han}; tồn {d['ton']}, giá trị {d['gia_tri_ton']}.")
    ket = "Anh chị mở trợ lý hoặc trang NWV Agent Proposals trong Business Central để duyệt hoặc từ chối. Trợ lý chỉ ghi đề xuất, không tự làm."
    return mo, ket


def soan(asst: Any, d: dict[str, Any]) -> dict[str, Any]:
    mo_mau, ket_mau = _mau(d)
    m, nguoi_soan = tt._goi_model(asst, "thu_de_xuat", _SYSTEM, d, SCHEMA, max_tokens=450)
    mo, ket = "", ""
    if m is not None:
        mo, ket = str(m.get("mo_dau") or "").strip(), str(m.get("ket") or "").strip()
        la = tt.so_la(d, mo, ket)
        if not mo or not ket:
            nguoi_soan, mo = "mẫu có sẵn (model trả về rỗng)", ""
        elif la:
            nguoi_soan, mo = "mẫu có sẵn (đoạn model viết có số không có trong dữ liệu: " + ", ".join(sorted(la)) + ")", ""
    if not mo:
        mo, ket = mo_mau, ket_mau
    tieu_de = f"[{d['company']}] Đề xuất {d['hanh_dong']} {d['mat_hang']} tại {d['dia_diem']}, chờ duyệt ({d['ngay']})"
    bang = [("Mặt hàng", f"{d['mat_hang']} ({d['ma']})"), ("Địa điểm / lô", f"{d['dia_diem']} / {d['lo'] or 'không mã'}"),
            ("Đề xuất", f"{d['hanh_dong']} {d['so_luong']}" + (f" sang {d['den']}" if d["den"] else "")),
            ("Tồn hiện có", f"{d['ton']} (giá trị {d['gia_tri_ton']})"), ("Tầng", f"{d['tang']} (điểm {d['diem_rui_ro']}): {d['ly_do_tang']}"),
            ("Hạn dùng", f"{d['han_dung']} (còn {d['con_ngay_den_han']} ngày)" if d["han_dung"] else "không quản lý hạn"),
            ("Lý do đề xuất", d["ly_do_de_xuat"]), ("Người đề nghị", d["nguoi_de_nghi"]), ("Policy", d["policy"] or "cần người duyệt")]
    url = link("agent_proposals")
    duoi = "Email do trợ lý vận hành Marou tự soạn và gửi. Số liệu đọc từ NWV Inventory Health trong Business Central; trợ lý không tự duyệt."
    text = "\n".join(["Chào anh chị,", "", mo, ""] + [f"{k}: {v}" for k, v in bang] + ["", ket, "", f"Mở trang đề xuất: {url}", "", duoi])
    html = ("<div style='font-family:Segoe UI,Arial,sans-serif;font-size:14px;color:#222'>"
            f"<p>Chào anh chị,</p><p>{_html.escape(mo)}</p><table style='border-collapse:collapse;font-size:13px'>"
            + "".join(f"<tr><td style='border:1px solid #ccc;padding:4px 8px;background:#f3f3f3'>{_html.escape(k)}</td>"
                      f"<td style='border:1px solid #ccc;padding:4px 8px'>{_html.escape(str(v))}</td></tr>" for k, v in bang)
            + f"</table><p>{_html.escape(ket)}</p><p><a href='{_html.escape(url)}'>Mở trang NWV Agent Proposals trong Business Central</a></p>"
            f"<p style='color:#777;font-size:12px'>{_html.escape(duoi)}</p></div>")
    return {"tieu_de": tieu_de, "text": text, "html": html, "nguoi_soan": nguoi_soan, "mo_dau": mo, "ket": ket}


def gui(asst: Any, user: dict[str, Any], prop: dict[str, Any], r: dict[str, Any], decision: Any) -> list[Delivery]:
    """Soan va gui email cho nguoi duyet; tra mot the cho nguoi de nghi de ho thay thu da di. Bot quet sang thi khong gui."""
    from .. import thu_dien_tu as td
    if user.get("user_id") in KHONG_GUI_CHO:
        return []
    try:
        d = du_lieu(asst, user, prop, r, decision)
        thu = soan(asst, d)
        kq = td.gui(tieu_de=thu["tieu_de"], text=thu["text"], html=thu["html"], loai="de_xuat",
                    khoa=f"de_xuat|{asst.cong_ty}|{prop['proposal_id']}", cong_ty=asst.cong_ty, nguoi_soan=thu["nguoi_soan"],
                    ngay=asst.mem.now().astimezone().strftime("%Y-%m-%d"))
    except Exception as exc:                         # email hong khong duoc lam hong viec ghi de xuat
        log.warning("Email de xuat hong: %s", exc)
        return [Delivery(user["user_id"], f"Đề xuất đã ghi, nhưng email cho người duyệt gửi không được: {exc}", skill=SKILL)]
    trang_thai = td.TEN_TRANG_THAI.get(kq["trang_thai"], kq["trang_thai"])
    card = Card(title=f"Email cho người duyệt: {thu['tieu_de']}", body=f"{thu['mo_dau']}\n\n{thu['ket']}",
                facts=[("Gửi đến", ", ".join(kq["den"]) or "(chưa có MAIL_TO)"),
                       ("Kênh", f"{td.TEN_KENH.get(kq['kenh'], kq['kenh'])}: {trang_thai}" + (f" ({kq['loi']})" if kq["loi"] else "")),
                       ("Người soạn", thu["nguoi_soan"])],
                kind="info", ref=prop["proposal_id"])
    return [Delivery(user["user_id"], f"Tôi cũng đã gửi email báo người duyệt ({trang_thai}).", card, SKILL, prop["proposal_id"])]
