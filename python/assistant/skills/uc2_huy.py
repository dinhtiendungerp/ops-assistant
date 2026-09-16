"""UC2 G2 + A3: bien ban huy do AI soan, luong huy khep kin.

Vi sao (16/09/2026). Truoc do duyet de xuat Write-off chi doi trang thai, khong sinh gi trong BC, khong ai biet ke toan da post
chua. Tai lieu 09 (US-11, G2, A3): duyet hui thi co bien ban va chung tu nhap; ke toan post; tro ly theo doi den khi xong.

Luong:
  1. Nguoi duyet bam "Duyet huy". BC (codeunit NWV Agent Proposal Mgt. 1.6.0.0) tao dong Item Journal Negative Adjmt. CHUA POST,
     Document No. AGENT-<id>, co lo va reason code. Agent khong post.
  2. Tro ly soan bien ban: code dien bang so lieu (mat hang, lo, so luong, gia tri, han dung, nguoi de nghi, nguoi duyet, chung tu);
     model viet hai doan (dien bien, de nghi), moi chu so phai co trong du lieu, sai thi dung mau. Gui the cho nguoi duyet va nguoi
     de nghi, gui email cho bo phan post (MAIL_TO) kem link mo Item Journal.
  3. Viec theo doi `write_off_post`: moi ngay tro ly xem ILE co Document No. do chua. Co thi bao "da post", dong viec. Chua thi
     nhac lai qua chat va email, lan 3 thi bao nguoi duyet can thiep.
"""
from __future__ import annotations

import html as _html
import logging
from datetime import timedelta
from typing import Any

from ..bc_link import link
from ..cards import Card, fmt_qty, fmt_vnd
from . import Delivery
from . import uc2_tom_tat as tt

log = logging.getLogger(__name__)
SKILL = "inventory_health"
VAI_TRO_THEO_DOI = ("supply_chain",)
SO_LAN_NHAC_TOI_DA = 3
SCHEMA = {"type": "object", "additionalProperties": False, "required": ["dien_bien", "de_nghi"],
          "properties": {"dien_bien": {"type": "string"}, "de_nghi": {"type": "string"}}}

_SYSTEM = (
    "Bạn là trợ lý vận hành của Marou Chocolate, soạn phần lời của một biên bản đề nghị hủy hàng theo dữ liệu Business Central đã có. "
    "Viết tiếng Việt, giọng hành chính ngắn gọn. dien_bien: 2-3 câu nêu lô hàng nào, tại đâu, tình trạng (hết hạn bao nhiêu ngày hoặc "
    "lý do xếp tầng), số lượng và giá trị theo giá vốn, ai đề nghị và ai duyệt. de_nghi: 1-2 câu đề nghị kế toán kiểm tra và post "
    "chứng từ điều chỉnh kho đã lập sẵn, nói rõ trợ lý chỉ lập nháp, chưa post. Chỉ dùng con số có trong dữ liệu, không thêm số, "
    "không chào hỏi, không gạch đầu dòng.")


def _lo_cua(prop: dict[str, Any], jnl: dict[str, Any]) -> str:
    """So lo: bo nho tro ly khong luu lot_no, nen lay tu dong journal (BC ghi tu de xuat) hoac tu khoa item|kho|lo."""
    if prop.get("lot_no"):
        return str(prop["lot_no"])
    if jnl.get("lotNo"):
        return str(jnl["lotNo"])
    phan = str(prop.get("channel_ref") or prop.get("reference_key") or "").split("|")
    return phan[2] if len(phan) >= 3 else ""


def _dong_ket_qua(asst: Any, prop: dict[str, Any], lo: str) -> dict[str, Any]:
    """Dong Inventory Health cua lo bi huy, de lay han dung, tang, ly do. Khong co thi dung so tren de xuat."""
    for r in asst.gw.doc("inventoryHealthLines", [], top=5000):
        if r.get("itemNo") == prop.get("item_no") and r.get("locationCode") == prop.get("from_loc") and (r.get("lotNo") or "") == lo:
            return r
    return {}


def du_lieu_bien_ban(asst: Any, prop: dict[str, Any], doc_no: str, nguoi_duyet: dict[str, Any]) -> dict[str, Any]:
    from .. import cong_ty as ctm
    jnl = (asst.gw.dong_journal(doc_no) or [{}])[0]
    lo = _lo_cua(prop, jnl)
    r = _dong_ket_qua(asst, prop, lo)
    qty = float(prop.get("quantity") or 0)
    ton = float(r.get("quantityOnHand") or 0)
    don_gia = float(r.get("inventoryValue") or 0) / ton if ton else float(prop.get("value_vnd") or 0) / qty if qty else 0.0
    ct = asst.cong_ty or ctm.hien_tai.get() or ""
    return {"so_bien_ban": doc_no, "ngay": asst.gw.today().strftime("%d/%m/%Y"), "company": ctm.nhan(ct, "day_du") if ct else "(mô phỏng)",
            "mat_hang": prop.get("item_desc") or prop.get("item_no"), "ma": prop.get("item_no"), "lo": lo,
            "dia_diem": prop.get("from_loc"), "so_luong": fmt_qty(qty), "don_vi": r.get("baseUnitOfMeasure", ""),
            "gia_von_don_vi": fmt_vnd(don_gia), "gia_tri": fmt_vnd(qty * don_gia),
            "han_dung": tt._ngay(r.get("expirationDate")) if r else "", "qua_han_ngay": -int(r["daysToExpiry"]) if r.get("daysToExpiry") is not None and r["daysToExpiry"] < 0 else 0,
            "tang": tt.TEN_TANG.get(r.get("tier", ""), r.get("tier", "")), "ly_do_xep_tang": r.get("riskReason", ""),
            "ly_do_de_xuat": prop.get("rationale", ""), "nguoi_de_nghi": prop.get("requested_by", ""),
            "nguoi_duyet": nguoi_duyet.get("display_name") or nguoi_duyet.get("user_id", ""), "luc_duyet": tt._ngay(prop.get("approved_at")),
            "chung_tu": {"loai": "Item Journal, Negative Adjmt., chưa post", "template": jnl.get("journalTemplateName", "ITEM"),
                         "batch": jnl.get("journalBatchName", "AGENT"), "document_no": doc_no, "reason_code": jnl.get("reasonCode", "AGENT-EXP")}}


def _mau(d: dict[str, Any]) -> tuple[str, str]:
    tinh_trang = f"đã quá hạn {d['qua_han_ngay']} ngày (hạn dùng {d['han_dung']})" if d["qua_han_ngay"] else (d["ly_do_xep_tang"] or "không còn bán được")
    dien_bien = (f"Lô {d['lo'] or 'không mã'} của {d['mat_hang']} ({d['ma']}) tại {d['dia_diem']} {tinh_trang}. "
                 f"Số lượng đề nghị hủy {d['so_luong']} {d['don_vi']}".rstrip() + f", giá trị theo giá vốn {d['gia_tri']}. "
                 f"{d['nguoi_de_nghi']} đề nghị, {d['nguoi_duyet']} duyệt ngày {d['luc_duyet'] or d['ngay']}.")
    de_nghi = (f"Đề nghị kế toán kiểm tra và post dòng Item Journal {d['chung_tu']['template']}/{d['chung_tu']['batch']}, "
               f"Document No. {d['chung_tu']['document_no']}, reason code {d['chung_tu']['reason_code']}. Trợ lý chỉ lập nháp, chưa post.")
    return dien_bien, de_nghi


def soan_bien_ban(asst: Any, prop: dict[str, Any], doc_no: str, nguoi_duyet: dict[str, Any]) -> dict[str, Any]:
    d = du_lieu_bien_ban(asst, prop, doc_no, nguoi_duyet)
    m, nguoi_soan = tt._goi_model(asst, "bien_ban", _SYSTEM, d, SCHEMA, max_tokens=500)
    dien_bien, de_nghi = "", ""
    if m is not None:
        dien_bien, de_nghi = str(m.get("dien_bien") or "").strip(), str(m.get("de_nghi") or "").strip()
        la = tt.so_la(d, dien_bien, de_nghi)
        if not dien_bien or not de_nghi:
            nguoi_soan, dien_bien = "mẫu có sẵn (model trả về rỗng)", ""
        elif la:
            nguoi_soan, dien_bien = "mẫu có sẵn (đoạn model viết có số không có trong dữ liệu: " + ", ".join(sorted(la)) + ")", ""
    if not dien_bien:
        dien_bien, de_nghi = _mau(d)
    tieu_de = f"BIÊN BẢN ĐỀ NGHỊ HỦY HÀNG số {d['so_bien_ban']}"
    bang = [("Company", d["company"]), ("Mặt hàng", f"{d['mat_hang']} ({d['ma']})"), ("Lô", d["lo"] or "không mã"), ("Địa điểm", d["dia_diem"]),
            ("Số lượng", f"{d['so_luong']} {d['don_vi']}".strip()), ("Giá vốn đơn vị", d["gia_von_don_vi"]), ("Giá trị", d["gia_tri"]),
            ("Hạn dùng", d["han_dung"] or "không ghi"), ("Người đề nghị", d["nguoi_de_nghi"]), ("Người duyệt", f"{d['nguoi_duyet']} ({d['luc_duyet'] or d['ngay']})"),
            ("Chứng từ", f"{d['chung_tu']['loai']}: {d['chung_tu']['template']}/{d['chung_tu']['batch']}, Document No. {d['chung_tu']['document_no']}, reason {d['chung_tu']['reason_code']}")]
    duoi = "Biên bản do trợ lý vận hành Marou soạn từ số liệu Business Central; chứng từ điều chỉnh kho đang ở trạng thái nháp, chưa post."
    text = "\n".join([tieu_de, f"Ngày {d['ngay']}", ""] + [f"{k}: {v}" for k, v in bang] + ["", dien_bien, "", de_nghi, "", duoi])
    html = ("<div style='font-family:Segoe UI,Arial,sans-serif;font-size:14px;color:#222'>"
            f"<h3>{_html.escape(tieu_de)}</h3><p>Ngày {_html.escape(d['ngay'])}</p><table style='border-collapse:collapse;font-size:13px'>"
            + "".join(f"<tr><td style='border:1px solid #ccc;padding:4px 8px;background:#f3f3f3'>{_html.escape(k)}</td>"
                      f"<td style='border:1px solid #ccc;padding:4px 8px'>{_html.escape(str(v))}</td></tr>" for k, v in bang)
            + f"</table><p>{_html.escape(dien_bien)}</p><p>{_html.escape(de_nghi)}</p><p style='color:#777;font-size:12px'>{_html.escape(duoi)}</p></div>")
    return {"tieu_de": tieu_de, "text": text, "html": html, "nguoi_soan": nguoi_soan, "du_lieu": d}


def _links(d: dict[str, Any]) -> list[tuple[str, str]]:
    ct = d["chung_tu"]
    return [("Mở Item Journal, batch " + ct["batch"], link("item_journal", {"Journal Batch Name": ct["batch"]})),
            ("Sổ kho của lô", link("item_ledger_entries", {"Item No.": d["ma"], "Location Code": d["dia_diem"], "Lot No.": d["lo"]}))]


def on_duyet_huy(asst: Any, user: dict[str, Any], prop: dict[str, Any], res: dict[str, Any]) -> list[Delivery]:
    """Sau khi BC tao dong journal nhap: soan bien ban, gui the, gui email cho bo phan post, dat viec theo doi."""
    from .. import thu_dien_tu as td
    doc_no = res.get("resultDocumentNo") or ""
    bb = soan_bien_ban(asst, prop, doc_no, user)
    d = bb["du_lieu"]
    ngay = asst.mem.now().astimezone().strftime("%Y-%m-%d")
    kq = td.gui(tieu_de=f"[{d['company'] or 'Marou'}] Biên bản hủy {d['mat_hang']} lô {d['lo'] or 'không mã'}, chứng từ {doc_no} chờ post",
                text=bb["text"] + "\n\nMở Item Journal: " + (_links(d)[0][1] or ""), html=bb["html"] + f"<p><a href='{_html.escape(_links(d)[0][1])}'>Mở Item Journal trong Business Central</a></p>",
                loai="bien_ban_huy", khoa=f"huy|{asst.cong_ty}|{doc_no}", cong_ty=asst.cong_ty, nguoi_soan=bb["nguoi_soan"], ngay=ngay)
    trang_thai = td.TEN_TRANG_THAI.get(kq["trang_thai"], kq["trang_thai"])
    card = Card(title=f"Đã duyệt hủy. Biên bản và chứng từ nháp {doc_no}", body=bb["text"][:1800],
                facts=[("Chứng từ", f"Item Journal {d['chung_tu']['template']}/{d['chung_tu']['batch']}, Document No. {doc_no}, chưa post"),
                       ("Email cho bộ phận post", f"{', '.join(kq['den']) or '(chưa có)'}: {trang_thai}"),
                       ("Theo dõi", "Tôi kiểm mỗi sáng; kế toán post xong tôi báo lại và đóng việc"),
                       ("Người soạn biên bản", bb["nguoi_soan"])],
                links=_links(d), kind="info", ref=doc_no)
    out = [Delivery(user["user_id"], f"Đã duyệt hủy {fmt_qty(float(prop.get('quantity') or 0))} {d['mat_hang']} tại {d['dia_diem']}. "
                                     f"BC tạo dòng Item Journal {doc_no} ở trạng thái nháp, tôi đã soạn biên bản và gửi email cho bộ phận post.",
                    card=card, skill=SKILL, ref=prop["proposal_id"])]
    if asst.mem.user(prop.get("requested_by", "")) and prop["requested_by"] != user["user_id"]:
        out.append(Delivery(prop["requested_by"], f"{user['display_name']} đã duyệt hủy {d['mat_hang']} lô {d['lo'] or 'không mã'} tại {d['dia_diem']}. "
                                                  f"Chứng từ {doc_no} chờ kế toán post; tôi sẽ báo khi xong.", skill=SKILL, ref=doc_no))
    now = asst.mem.now()
    asst.mem.add_followup("write_off_post", doc_no, now + timedelta(hours=24), notify_user=user["user_id"],
                          escalate_user=user["user_id"], note=prop["proposal_id"])
    return out


def theo_doi(asst: Any, f: dict[str, Any]) -> list[Delivery]:
    """Mot lan kiem viec `write_off_post`. Goi tu Assistant.run_followups."""
    from .. import thu_dien_tu as td
    doc_no = f["ref"]
    nguoi = {u["user_id"] for vai in VAI_TRO_THEO_DOI for u in asst.mem.users_by_role(vai)} | {f["notify_user"]}
    nguoi.discard("")
    now = asst.mem.now()
    if asst.gw.da_post_journal(doc_no):
        asst.mem.update_followup(f["id"], status="done")
        loc = {"Document No.": doc_no}
        card = Card(title=f"Kế toán đã post chứng từ hủy {doc_no}", kind="info", ref=doc_no,
                    body="Item Ledger Entry đã ghi nhận điều chỉnh giảm. Vòng hủy cho lô này khép lại, tôi không nhắc nữa.",
                    links=[("Item Ledger Entry của chứng từ", link("item_ledger_entries", loc))])
        return [Delivery(u, f"Chứng từ hủy {doc_no} đã được post, đóng việc.", card, SKILL, doc_no) for u in sorted(nguoi)]
    lan = int(f.get("attempts") or 0) + 1
    con = asst.gw.dong_journal(doc_no)
    if not con:
        # Khong con trong journal ma cung chua co ILE: ai do xoa dong nhap. Bao nguoi duyet, dong viec.
        asst.mem.update_followup(f["id"], status="done", attempts=lan)
        return [Delivery(u, f"Dòng Item Journal {doc_no} không còn trong batch mà chưa thấy Item Ledger Entry nào post từ nó. "
                            f"Có thể đã bị xóa; bạn kiểm lại với kế toán. Tôi đóng việc theo dõi.", skill=SKILL, ref=doc_no) for u in sorted(nguoi)]
    j = con[0]
    ngay = now.astimezone().strftime("%Y-%m-%d")
    khoa = f"nhac_huy|{asst.cong_ty}|{doc_no}"
    thu = ""
    if not td.da_gui_hom_nay(khoa, ngay):
        text = (f"Chứng từ hủy {doc_no} ({fmt_qty(float(j.get('quantity') or 0))} {j.get('itemNo')}, lô {j.get('lotNo') or 'không mã'}, "
                f"tại {j.get('locationCode')}) vẫn nằm trong Item Journal {j.get('journalTemplateName')}/{j.get('journalBatchName')}, chưa post. "
                f"Nhắc lần {lan}. Nhờ anh chị kiểm tra và post. Trợ lý không tự post.\n\nMở Item Journal: "
                + link("item_journal", {"Journal Batch Name": j.get("journalBatchName", "")}))
        kq = td.gui(tieu_de=f"[{asst.cong_ty or 'Marou'}] Nhắc post chứng từ hủy {doc_no} (lần {lan})", text=text,
                    html="<p>" + _html.escape(text).replace("\n", "<br>") + "</p>", loai="nhac_huy", khoa=khoa, cong_ty=asst.cong_ty,
                    nguoi_soan="mẫu có sẵn", ngay=ngay)
        thu = f" Tôi đã gửi email nhắc bộ phận post ({td.TEN_TRANG_THAI.get(kq['trang_thai'], kq['trang_thai'])})."
    cau = f"Nhắc lần {lan}: chứng từ hủy {doc_no} vẫn chưa được post, còn nằm trong Item Journal {j.get('journalBatchName')}.{thu}"
    out = [Delivery(u, cau, skill=SKILL, ref=doc_no) for u in sorted(nguoi)]
    if lan >= SO_LAN_NHAC_TOI_DA and f.get("escalate_user"):
        out.append(Delivery(f["escalate_user"], f"Chứng từ hủy {doc_no} đã nhắc {lan} lần vẫn chưa post. Bạn can thiệp giúp; tôi vẫn kiểm mỗi ngày.",
                            skill=SKILL, ref=doc_no))
    asst.mem.update_followup(f["id"], attempts=lan, due_at=(now + timedelta(hours=24)).isoformat())
    return out
