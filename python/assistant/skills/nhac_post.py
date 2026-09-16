"""Nhac post nhan hang: tro ly tu phat hien, tu nhac qua chat, tu soan email va gui, tu dong viec khi BC da post.

Vi sao co file nay (15/09/2026). Khao sat Marou: hang ve cua hang, chung tu don toi cuoi thang moi post Receive, Marou thue
nguoi ben ngoai post. Dung chot: tro ly KHONG post, nhung phai thay tro ly chu dong nhac nguoi post, ca qua chat va qua email.

Vong mot don mua:
  1. `po_qua_han`: dong don mua qua ngay nhan du kien ma con Outstanding Quantity. Tro ly hoi nguoi nhan hang tai dia diem.
  2. Nguoi nhan bam "Hang da ve, chua nhap" -> `on_xac_nhan` goi `nhac(chi_ref=...)`: email ngay cho nguoi post (MAIL_TO),
     bao Supply Chain qua chat.
  3. Moi sang (lich trong web.py) hoac khi Supply Chain go "nhac post": don nao da xac nhan ve ma BC van chua nhan thi nhac lai
     lan 2, 3... qua chat va email; don qua han chua ai xac nhan thi nhac trong cung thu.
  4. Lan chay sau thay don khong con Outstanding (nguoi post da post Receive): bao "da post", dong viec, khong nhac nua.

Ai soan gi. Danh sach don, so luong, ngay, link BC do code dien tu dong don mua, nen khong con so nao do model tu nghi ra.
Model (khi bat AI) chi viet doan mo dau va cau ket, theo muc tre va so lan da nhac. Doan model viet ma co chu so khong co
trong du lieu thi bo, dung doan mau. Tat AI hoac het tran chi phi: dung doan mau.
"""
from __future__ import annotations

import html as _html
import json
import logging
import re
from typing import Any

from ..cards import Card, fmt_qty
from . import Delivery
from . import po_qua_han as pq

log = logging.getLogger(__name__)
SKILL = "nhac_post"
VAI_TRO_CHU_VIEC = ("supply_chain",)          # nguoi nhan bao qua chat moi lan nhac, ngoai nguoi tai dia diem
VAI_TRO_DUOC_GOI = ("supply_chain", "dispatcher", "admin")

SCHEMA = {"type": "object", "additionalProperties": False, "required": ["mo_dau", "ket"],
          "properties": {"mo_dau": {"type": "string"}, "ket": {"type": "string"}}}


# ---------------------------------------------------------------- du lieu
def _kv(asst: Any, k: str) -> str | None:
    r = asst.mem.conn.execute("SELECT v FROM kv WHERE k=?", (k,)).fetchone()
    return r["v"] if r else None


def _dat_kv(asst: Any, k: str, v: str) -> None:
    asst.mem.conn.execute("INSERT OR REPLACE INTO kv(k,v) VALUES(?,?)", (k, v))
    asst.mem.conn.commit()


def _ngay_he_thong(asst: Any) -> str:
    """Ngay cua dong ho tro ly (co dong ho ao de demo "sang hom sau"), dung de chong nhac trung trong ngay."""
    return asst.mem.now().astimezone().strftime("%Y-%m-%d")


def thu_thap(asst: Any) -> dict[str, Any]:
    """Chia don qua han thanh ba nhom, cong danh sach don da xac nhan ve nay da duoc post (khong con qua han)."""
    don = pq.gom_theo_don(pq.dong_qua_han(asst))
    da_ve, chua_xn, treo = [], [], []
    con_mo = set()
    for d in don:
        ref = pq._ref(d)
        con_mo.add(ref)
        xn = pq._xac_nhan(asst, ref)
        d["xac_nhan"] = xn
        if xn and xn.get("da_ve"):
            da_ve.append(d)
        elif d["tre_nhat"] > pq.NGAY_DON_TREO:
            treo.append(d)
        elif not xn:
            chua_xn.append(d)
    da_post = []
    for r in asst.mem.conn.execute("SELECT k, v FROM kv WHERE k LIKE 'po_xac_nhan:%'").fetchall():
        ref = r["k"].split(":", 1)[1]
        xn = json.loads(r["v"])
        if xn.get("da_ve") and ref not in con_mo and not _kv(asst, f"nhac_post_dong:{ref}"):
            da_post.append({"ref": ref, "xac_nhan": xn})
    return {"da_ve": da_ve, "chua_xn": chua_xn, "treo": treo, "da_post": da_post}


def _dong_du_lieu(asst: Any, d: dict[str, Any], ten: dict[str, str]) -> dict[str, Any]:
    from ..bc_link import link
    return {"so_don": d["so_don"], "dia_diem": d["dia_diem"], "ten_dia_diem": pq._ten_diem(d["dia_diem"]),
            "nha_cung_cap": d["nha_cung_cap"], "tre_nhat": d["tre_nhat"],
            # So lan nhac da dem (nhac() tang truoc khi soan thu). Don da xac nhan ve it nhat la lan 1.
            "xac_nhan": d.get("xac_nhan"),
            "lan_nhac": max(int(_kv(asst, f"nhac_post_lan:{pq._ref(d)}") or 0), 1 if (d.get("xac_nhan") or {}).get("da_ve") else 0),
            "dong": [{"mat_hang": r.get("description") or ten.get(r.get("itemNo", ""), r.get("itemNo", "")),
                      "ma": r.get("itemNo", ""), "con": fmt_qty(float(r.get("outstandingQuantity") or 0)),
                      "dat": fmt_qty(float(r.get("quantity") or 0)),
                      "du_kien": pq._ngay(r.get("expectedReceiptDate")).strftime("%d/%m/%Y")} for r in d["dong"]],
            "link": link("purchase_order", {"Document Type": "Order", "No.": d["so_don"]})}


# ---------------------------------------------------------------- soan thu
def _mo_dau_mau(ct: str, ngay_bc: str, n_ve: int, n_chua: int, lan_max: int) -> tuple[str, str]:
    phan = []
    if n_ve:
        phan.append(f"{n_ve} đơn mua cửa hàng đã báo hàng về nhưng Business Central chưa post nhận hàng")
    if n_chua:
        phan.append(f"{n_chua} đơn mua đã quá ngày nhận dự kiến mà chưa ai xác nhận")
    mo = f"Tính đến {ngay_bc}, company {ct} còn " + " và ".join(phan) + "."
    if n_ve:
        mo += " Chừng nào chưa post, tồn trên hệ thống thấp hơn hàng thực có, và các cảnh báo hết hàng, đề xuất bổ sung cho cửa hàng đó sẽ sai theo."
    if lan_max >= 2:
        mo += f" Đây là lần nhắc thứ {lan_max} cho đơn trễ lâu nhất."
    ket = ("Nhờ anh chị post Receive trên từng Purchase Order ở danh sách dưới. Sau khi post, trợ lý tự thấy và đóng việc, "
           "không nhắc nữa. Nếu hàng thực tế chưa về, nhờ báo lại để người mua liên hệ nhà cung cấp.")
    return mo, ket


def _chu_so(s: str) -> set[str]:
    return set(re.findall(r"\d+", s))


def _model_viet(asst: Any, du_lieu: dict[str, Any], mo_mau: str, ket_mau: str) -> tuple[str, str, str]:
    """Tra ve (mo_dau, ket, nguoi_soan). Model chi duoc dung chu so co trong du lieu; sai thi dung doan mau."""
    w = getattr(asst, "_writer", None)
    if not w or not asst.budget.allow():
        return mo_mau, ket_mau, "mẫu có sẵn (AI đang tắt)"
    try:
        from bc_agent.llm import text_of
        resp = w.text(
            system=("Ban la tro ly van hanh cua Marou Chocolate, viet email tieng Viet nhac bo phan post chung tu. "
                    "Chi viet hai doan: mo_dau (2-3 cau: tinh hinh, vi sao can post som, muc do gap theo so ngay tre va so lan da "
                    "nhac) va ket (1-2 cau: viec can lam, noi ro tro ly khong tu post). Xung 'anh chi'. Khong chao hoi dai dong, "
                    "khong liet ke tung don vi code se chen danh sach. Chi dung con so co trong du lieu. Khong hua, khong doa."),
            user=json.dumps(du_lieu, ensure_ascii=False), max_tokens=500, schema=SCHEMA)
        asst.budget.track("thu", w.model, resp.usage)
        d = json.loads(text_of(resp))
        mo, ket = (d.get("mo_dau") or "").strip(), (d.get("ket") or "").strip()
        duoc = _chu_so(json.dumps(du_lieu, ensure_ascii=False))
        la = (_chu_so(mo) | _chu_so(ket)) - duoc
        if la:
            log.warning("Doan model viet bi bo vi co so la: %s", la)
            return mo_mau, ket_mau, f"mẫu có sẵn (đoạn model viết có số không có trong dữ liệu: {', '.join(sorted(la))})"
        if not mo or not ket:
            return mo_mau, ket_mau, "mẫu có sẵn (model trả về rỗng)"
        from bc_agent.config import settings
        return mo, ket, f"AI ({settings.live_model_name or 'model'})"
    except Exception as exc:
        log.warning("Model soan thu hong: %s", exc)
        return mo_mau, ket_mau, "mẫu có sẵn (gọi model không được)"


def soan_thu(asst: Any, da_ve: list[dict[str, Any]], chua_xn: list[dict[str, Any]], so_treo: int = 0) -> dict[str, Any]:
    from .. import cong_ty as ctm
    ten = pq._ten_hang(asst)
    ct = asst.cong_ty or ctm.hien_tai.get() or ""
    ngay_bc = asst.gw.today().strftime("%d/%m/%Y")
    ve = [_dong_du_lieu(asst, d, ten) for d in da_ve]
    chua = [_dong_du_lieu(asst, d, ten) for d in chua_xn]
    lan_max = max([x["lan_nhac"] for x in ve] or [0])
    mo_mau, ket_mau = _mo_dau_mau(ct, ngay_bc, len(ve), len(chua), lan_max)
    du_lieu = {"company": ct, "ngay": ngay_bc, "so_don_da_ve_chua_post": len(ve), "so_don_chua_xac_nhan": len(chua),
               "lan_nhac_cao_nhat": lan_max, "tre_lau_nhat_ngay": max([x["tre_nhat"] for x in ve + chua] or [0]),
               "don_da_ve": [{**{k: x[k] for k in ("so_don", "ten_dia_diem", "tre_nhat", "lan_nhac")},
                              "ngay_bao_ve": (x.get("xac_nhan") or {}).get("luc", ""),
                              "du_kien": sorted({r["du_kien"] for r in x["dong"]})} for x in ve],
               "don_chua_xac_nhan": [{**{k: x[k] for k in ("so_don", "ten_dia_diem", "tre_nhat")},
                                      "du_kien": sorted({r["du_kien"] for r in x["dong"]})} for x in chua]}
    mo, ket, nguoi_soan = _model_viet(asst, du_lieu, mo_mau, ket_mau)
    nhan = ctm.nhan(ct) if ct else "Marou"
    tieu_de = (f"[{nhan}] Nhắc post nhận hàng: {len(ve)} đơn đã về chưa nhập BC" if ve
               else f"[{nhan}] {len(chua)} đơn mua quá hạn nhận chưa được xác nhận") + f" ({ngay_bc})"

    def khoi(ds: list[dict[str, Any]], tieu: str) -> tuple[list[str], list[str]]:
        t, h = [], []
        if not ds:
            return t, h
        t.append(tieu)
        h.append(f"<h3 style='margin:18px 0 6px'>{_html.escape(tieu)}</h3>")
        for i, x in enumerate(ds, 1):
            xn = x.get("xac_nhan") or {}
            dong_xn = f" {xn['nguoi']} báo hàng đã về lúc {xn['luc']}." if xn.get("da_ve") else ""
            lan = f" Lần nhắc thứ {x['lan_nhac']}." if x in ve and x["lan_nhac"] else ""
            dau = (f"{i}. Đơn {x['so_don']}, nhận tại {x['ten_dia_diem']} ({x['dia_diem']}), nhà cung cấp {x['nha_cung_cap']}, "
                   f"trễ {x['tre_nhat']} ngày.{dong_xn}{lan}")
            t.append(dau)
            t += [f"   - {r['mat_hang']} ({r['ma']}): còn {r['con']} / {r['dat']}, dự kiến {r['du_kien']}" for r in x["dong"]]
            if x["link"]:
                t.append(f"   Mở đơn trong Business Central: {x['link']}")
            h.append(f"<p style='margin:10px 0 4px'><b>{_html.escape(dau)}</b></p>")
            h.append("<table style='border-collapse:collapse;font-size:13px'><tr>"
                     + "".join(f"<th style='border:1px solid #ccc;padding:4px 8px;background:#f3f3f3;text-align:left'>{c}</th>"
                               for c in ("Mặt hàng", "Mã", "Còn chưa nhận", "Đặt", "Dự kiến")) + "</tr>"
                     + "".join("<tr>" + "".join(f"<td style='border:1px solid #ccc;padding:4px 8px'>{_html.escape(str(r[k]))}</td>"
                                                 for k in ("mat_hang", "ma", "con", "dat", "du_kien")) + "</tr>" for r in x["dong"])
                     + "</table>")
            if x["link"]:
                h.append(f"<p style='margin:4px 0'><a href='{_html.escape(x['link'])}'>Mở đơn {_html.escape(x['so_don'])} trong Business Central</a></p>")
        return t, h

    t1, h1 = khoi(ve, "Hàng đã về, chưa post nhận hàng")
    t2, h2 = khoi(chua, "Quá hạn nhận, chưa có xác nhận từ nơi nhận (trợ lý đã hỏi qua chat)")
    duoi = "Email do trợ lý vận hành Marou tự soạn và gửi. Trợ lý không post chứng từ; số liệu đọc từ Purchase Line trong Business Central."
    if so_treo:
        duoi = f"Có {so_treo} đơn trễ hơn {pq.NGAY_DON_TREO} ngày không đưa vào email này vì nhiều khả năng là đơn treo. " + duoi
    text = "\n".join(["Chào anh chị,", "", mo, ""] + t1 + ([""] if t1 else []) + t2 + ["", ket, "", duoi])
    html = ("<div style='font-family:Segoe UI,Arial,sans-serif;font-size:14px;color:#222'>"
            f"<p>Chào anh chị,</p><p>{_html.escape(mo)}</p>" + "".join(h1) + "".join(h2)
            + f"<p style='margin-top:16px'>{_html.escape(ket)}</p><p style='color:#777;font-size:12px'>{_html.escape(duoi)}</p></div>")
    return {"tieu_de": tieu_de, "text": text, "html": html, "nguoi_soan": nguoi_soan, "ve": ve, "chua": chua}


# ---------------------------------------------------------------- nhac
def _the_thu(ket_qua: dict[str, Any], thu: dict[str, Any]) -> Card:
    from .. import thu_dien_tu as td
    body = thu["text"]
    if len(body) > 1800:
        body = body[:1800] + "\n…"
    facts = [("Gửi tới", ", ".join(ket_qua["den"]) or "(chưa có)"), ("Tiêu đề", ket_qua["tieu_de"]),
             ("Người soạn", thu["nguoi_soan"]), ("Kênh", td.TEN_KENH.get(ket_qua["kenh"], ket_qua["kenh"])),
             ("Trạng thái", td.TEN_TRANG_THAI.get(ket_qua["trang_thai"], ket_qua["trang_thai"]))]
    if ket_qua.get("loi"):
        facts.append(("Lỗi", ket_qua["loi"]))
    links = [(f"Mở đơn {x['so_don']} trong BC", x["link"]) for x in (thu["ve"] + thu["chua"])[:3] if x["link"]]
    tieu = "Tôi đã soạn và gửi email nhắc post" if ket_qua["trang_thai"] == "da_gui" else \
        ("Tôi đã soạn email nhắc post (chưa gửi ra ngoài)" if ket_qua["trang_thai"] == "chi_luu_file" else "Email nhắc post gửi không được")
    return Card(title=tieu, body=body, facts=facts, links=links, kind="info", ref=f"thu|{ket_qua['id']}")


def nhac(asst: Any, nguoi: dict[str, Any] | None = None, chi_ref: str | None = None, bat_buoc: bool = False) -> list[Delivery]:
    """Mot vong nhac. `nguoi` la ai kich hoat (None la lich chay nen). `chi_ref`: chi don vua duoc xac nhan ve.
    `bat_buoc`: nguoi dung go lenh thi gui lai email ke ca da gui trong ngay."""
    from .. import thu_dien_tu as td

    ngay = _ngay_he_thong(asst)
    nhom = thu_thap(asst)
    out: list[Delivery] = []
    chu_viec = [u for vai in VAI_TRO_CHU_VIEC for u in asst.mem.users_by_role(vai)]

    # Don da post: bao va dong viec.
    for x in nhom["da_post"]:
        so_don, _, dia_diem = x["ref"].partition("|")
        cau = (f"Đơn mua {so_don} ({pq._ten_diem(dia_diem)}) đã được post nhận hàng trong Business Central. "
               f"{x['xac_nhan']['nguoi']} báo hàng về lúc {x['xac_nhan']['luc']}. Tôi đóng việc nhắc cho đơn này.")
        for u in chu_viec:
            out.append(Delivery(u["user_id"], cau, skill=SKILL, ref=x["ref"]))
        _dat_kv(asst, f"nhac_post_dong:{x['ref']}", ngay)

    da_ve = [d for d in nhom["da_ve"] if not chi_ref or pq._ref(d) == chi_ref]
    chua_xn = [] if chi_ref else nhom["chua_xn"]
    if not da_ve and not chua_xn:
        if nguoi and not out:
            out.append(Delivery(nguoi["user_id"], "Không còn đơn mua nào đã về mà chưa post, cũng không có đơn quá hạn chưa xác nhận. "
                                                  "Không có gì để nhắc.", skill=SKILL))
        return out

    # Chat: nhac nguoi tai dia diem va chu viec, moi don mot lan mot ngay.
    for d in da_ve:
        ref = pq._ref(d)
        if _kv(asst, f"nhac_post_ngay:{ref}") == ngay and not bat_buoc:
            continue
        lan = int(_kv(asst, f"nhac_post_lan:{ref}") or 0) + 1
        _dat_kv(asst, f"nhac_post_lan:{ref}", str(lan))
        _dat_kv(asst, f"nhac_post_ngay:{ref}", ngay)
        if chi_ref:
            continue      # vua xac nhan xong: Supply Chain da nhan tin bao, khong nhac them mot tin chat nua
        con = sum(float(r.get("outstandingQuantity") or 0) for r in d["dong"])
        cau = (f"Nhắc lần {lan}: đơn mua {d['so_don']} ({pq._ten_diem(d['dia_diem'])}) đã báo hàng về nhưng Business Central "
               f"vẫn chưa post nhận, còn {fmt_qty(con)} đơn vị trên {len(d['dong'])} dòng, trễ {d['tre_nhat']} ngày. "
               f"Tôi đã gửi email cho bộ phận post chứng từ.")
        noi = [u for vai in pq.VAI_TRO_TAI_DIEM for u in asst.mem.users_by_role(vai) if u.get("store_code") == d["dia_diem"]]
        for u in noi + chu_viec:
            out.append(Delivery(u["user_id"], cau, skill=SKILL, ref=ref))

    # Email: mot thu gom cac don, chong gui trung trong ngay.
    khoa = f"nhac_post|{asst.cong_ty}|" + ",".join(sorted(pq._ref(d) for d in da_ve + chua_xn))
    if chi_ref:
        khoa = f"da_ve|{asst.cong_ty}|{chi_ref}"
    if td.da_gui_hom_nay(khoa, ngay) and not bat_buoc:
        if nguoi:
            cau = "Hôm nay tôi đã gửi email nhắc bộ phận post chứng từ cho đúng việc này rồi, không gửi lại."
            if nguoi.get("role") in VAI_TRO_DUOC_GOI:
                cau += " Gõ \"gửi lại mail nhắc post\" nếu cần gửi lại."
            out.append(Delivery(nguoi["user_id"], cau, skill=SKILL))
        return out
    thu = soan_thu(asst, da_ve, chua_xn, so_treo=0 if chi_ref else len(nhom["treo"]))
    kq = td.gui(tieu_de=thu["tieu_de"], text=thu["text"], html=thu["html"], loai="nhac_post", khoa=khoa,
                cong_ty=asst.cong_ty, nguoi_soan=thu["nguoi_soan"], ngay=ngay)
    the = _the_thu(kq, thu)
    nhan_the = {u["user_id"] for u in chu_viec} | ({nguoi["user_id"]} if nguoi else set())
    for uid in nhan_the:
        out.append(Delivery(uid, the.title + f": {kq['tieu_de']}", card=the, skill=SKILL, ref=the.ref))
    return out


def handle(asst: Any, user: dict[str, Any], text: str = "") -> list[Delivery]:
    """Supply Chain, dieu phoi, quan tri go "nhac post" hoac "gui mail nhac post"."""
    if user.get("role") not in VAI_TRO_DUOC_GOI:
        return [Delivery(user["user_id"], "Nhắc post chứng từ là việc của Supply Chain hoặc điều phối. Nếu hàng đã về, bạn bấm "
                                          "\"Hàng đã về, chưa nhập\" trên thẻ đơn mua, tôi sẽ tự nhắc người post.", skill=SKILL)]
    lai = bool(re.search(r"(gửi lại|gui lai|nhắc lại|nhac lai)", text or "", re.I))
    return nhac(asst, user, bat_buoc=lai)
