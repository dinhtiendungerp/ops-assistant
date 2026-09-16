"""Intercompany phia nguoi mua: Marou xuat kho, Dakao chuan bi nhan, va de xuat cho tro ly post nhan hang.

Vi sao (Dung chot 16/09/2026). Marou ban cho Dakao qua Intercompany. Hai dau KHONG tu dong post nhu nhau:

  - Phia Marou (nguoi ban) khong co gi tu dong. Nguoi kho Marou post xuat kho trong BC nhu moi ngay.
  - Phia Dakao (nguoi mua) thi tro ly lam ba viec, va chi viec thu ba moi dong vao so sach:
      1. Marou post xuat kho TRONG NGAY: tro ly bao ngay qua chat va email cho cua hang nhan hang va Supply Chain,
         de ho chuan bi nhan. Chi bao, khong ghi gi.
      2. Qua ngay hom sau ma ben Dakao van chua post nhan: tro ly nhac lai, VA ghi mot de xuat PostReceipt.
      3. Nguoi duyet bam Duyet thi BC moi post phieu nhan (codeunit NWV IC Receipt), kem dung so lo Marou da xuat.
         Khong ai duyet thi khong co gi duoc post; tro ly nhac tiep moi ngay.

Luu y cach doc yeu cau: Marou la ben XUAT, nen cau "thong bao chuan bi nhan hang" o day gui cho phia Dakao, tuc cua hang
dung ten tren don mua va Supply Chain. Marou khong nhan tin nao trong vong nay.

So lieu do BC dien: don mua, so luong con lai, phieu giao hang, so lo, han dung deu doc tu web service NWVAgentICService,
khong tinh lai. Model khong tham gia vong nay.
"""
from __future__ import annotations

import html as _html
import logging
import uuid
from datetime import date, datetime
from typing import Any

from ..bc_link import link
from ..cards import Action, Card, fmt_qty
from . import Delivery
from .nhac_post import _dat_kv, _kv

log = logging.getLogger(__name__)
SKILL = "ic_nhan_hang"
VAI_TRO_CHU_VIEC = ("supply_chain",)
VAI_TRO_TAI_DIEM = ("store_manager", "warehouse")
VAI_DUYET = ("supply_chain", "dispatcher")
VAI_TRO_DUOC_GOI = ("supply_chain", "dispatcher", "admin")
NHA_CUNG_CAP_IC = "MAROU"


def _ngay(s: Any) -> date | None:
    if isinstance(s, date):
        return s
    t = str(s or "")[:10]
    try:
        return datetime.strptime(t, "%Y-%m-%d").date()
    except ValueError:
        return None


def _ten_diem(ma: str) -> str:
    from ..core import STORE_LABEL
    return STORE_LABEL.get(ma, ma)


def thu_thap(asst: Any) -> dict[str, list[dict[str, Any]]]:
    """Chia don mua intercompany thanh ba nhom theo trang thai giao / nhan."""
    # Ngay "hom nay" o day lay theo dong ho tro ly, KHONG theo As Of Date cua bang Inventory Health.
    # Ly do: phieu giao hang duoc post voi ngay that, con As Of Date la ngay chot cua lan tinh gan nhat (bo demo neo 18/09).
    # Lay As Of Date thi mot phieu vua post sang nay da bi coi la "qua ngay" va tro ly bo qua buoc bao truoc.
    # Dong ho tro ly co nut +24 gio trong khay demo, nen van dien duoc canh "sang hom sau".
    hom_nay = asst.mem.now().astimezone().date()
    trong_ngay, qua_ngay, da_nhan = [], [], []
    for d in asst.gw.ic_giao_hang(NHA_CUNG_CAP_IC):
        shp = d.get("shipment") or {}
        if not shp.get("posted"):
            continue
        d["ngay_xuat"] = _ngay(shp.get("postingDate"))
        con = float(d.get("outstanding") or 0)
        if con <= 0:
            da_nhan.append(d)
        elif d["ngay_xuat"] and d["ngay_xuat"] < hom_nay:
            d["so_ngay"] = (hom_nay - d["ngay_xuat"]).days
            qua_ngay.append(d)
        else:
            trong_ngay.append(d)
    return {"trong_ngay": trong_ngay, "qua_ngay": qua_ngay, "da_nhan": da_nhan}


# ---------------------------------------------------------------- soan tin
def _dong_hang(d: dict[str, Any], kem_lo: bool = False) -> list[str]:
    """Dong mat hang cua phieu giao hang. `kem_lo` chi bat cho nguoi duyet.

    Vi sao mac dinh tat (Dung bac 16/09/2026): Dakao la ban le, KHONG quan ly lo, nen so lo doc len cho cua hang la thua.
    Rieng tren he demo thi NWV-DAKAO la ban sao cua NWV nen 68 ma van con Item Tracking Code, va company da co 25 nghin dong
    Item Ledger Entry nen `TestNoEntriesExist` khong cho go ma lo ra nua. Nghia la BC VAN doi so lo khi post phieu nhan o day.
    Tro ly lay dung lo Marou da xuat thay vi bia mot so, va chi ghi lo o cho nguoi duyet doc de kiem, khong day ra cua hang."""
    ra = []
    for l in (d.get("shipment") or {}).get("lines", []):
        lo = ", ".join(f"{x.get('lotNo')} ({fmt_qty(float(x.get('quantity') or 0))})" for x in l.get("lots", []))
        ra.append(f"{l.get('description') or l.get('itemNo')} ({l.get('itemNo')}): {fmt_qty(float(l.get('quantity') or 0))}"
                  + (f", lô {lo}" if kem_lo and lo else ""))
    return ra


def _facts(d: dict[str, Any]) -> list[tuple[str, str]]:
    shp = d.get("shipment") or {}
    return [("Đơn mua", d["purchaseOrder"]),
            ("Bên bán", f"{d.get('vendorName') or d.get('vendorNo')} ({d.get('partnerCompany') or ''})"),
            ("Phiếu giao hàng", f"{shp.get('no', '')} ngày {(_ngay(shp.get('postingDate')) or '')}"),
            ("Giao đến", f"{_ten_diem(d.get('locationCode', ''))} ({d.get('locationCode', '')})"),
            ("Còn phải nhận", fmt_qty(float(d.get("outstanding") or 0)))]


def _links(d: dict[str, Any]) -> list[tuple[str, str]]:
    return [("Mở đơn mua trong Business Central", link("purchase_order", {"Document Type": "Order", "No.": d["purchaseOrder"]}))]


def _nguoi_nhan(asst: Any, d: dict[str, Any]) -> list[str]:
    """Nguoi tai dia diem nhan hang, cong chu viec (Supply Chain)."""
    diem = d.get("locationCode", "")
    tai_diem = [u["user_id"] for vai in VAI_TRO_TAI_DIEM for u in asst.mem.users_by_role(vai) if u.get("store_code") == diem]
    chu = [u["user_id"] for vai in VAI_TRO_CHU_VIEC for u in asst.mem.users_by_role(vai)]
    return sorted(set(tai_diem) | set(chu))


def _the_bao_xuat(d: dict[str, Any]) -> Card:
    return Card(title=f"{d.get('vendorName') or 'Marou'} đã xuất kho đơn {d['purchaseOrder']}",
                body="\n".join(["Hàng đã rời kho bên bán, cửa hàng chuẩn bị nhận."] + _dong_hang(d)
                               + ["", "Khi hàng về, người nhận post Receive trên đơn mua. Trợ lý không tự post."]),
                facts=_facts(d), links=_links(d), kind="info", ref=f"ic-xuat|{d['purchaseOrder']}")


def _thu_bao_xuat(asst: Any, ds: list[dict[str, Any]], ngay: str) -> dict[str, Any]:
    from .. import cong_ty as ctm
    from .. import thu_dien_tu as td
    nhan = ctm.nhan(asst.cong_ty) if asst.cong_ty else "Marou"
    dong = []
    html = []
    for i, d in enumerate(ds, 1):
        shp = d.get("shipment") or {}
        dau = (f"{i}. Đơn {d['purchaseOrder']}, phiếu giao hàng {shp.get('no', '')} ngày "
               f"{_ngay(shp.get('postingDate')) or ''}, giao đến {_ten_diem(d.get('locationCode', ''))} "
               f"({d.get('locationCode', '')}), còn phải nhận {fmt_qty(float(d.get('outstanding') or 0))}.")
        dong.append(dau)
        dong += [f"   - {x}" for x in _dong_hang(d)]
        dong.append("   Mở đơn mua: " + _links(d)[0][1])
        html.append(f"<p style='margin:10px 0 4px'><b>{_html.escape(dau)}</b></p><ul>"
                    + "".join(f"<li>{_html.escape(x)}</li>" for x in _dong_hang(d)) + "</ul>"
                    + f"<p><a href='{_html.escape(_links(d)[0][1])}'>Mở đơn {_html.escape(d['purchaseOrder'])} trong Business Central</a></p>")
    mo = (f"Bên bán đã post xuất kho {len(ds)} đơn mua intercompany trong hôm nay. Nhờ cửa hàng chuẩn bị nhận hàng, "
          f"và post Receive trên đơn mua ngay khi hàng tới.")
    ket = ("Trợ lý không tự post nhận hàng. Nếu qua ngày mai đơn vẫn chưa được post, tôi sẽ nhắc lại và gửi một đề xuất "
           "để người duyệt quyết định có cho trợ lý post thay hay không.")
    text = "\n".join(["Chào anh chị,", "", mo, ""] + dong + ["", ket])
    body = ("<div style='font-family:Segoe UI,Arial,sans-serif;font-size:14px;color:#222'><p>Chào anh chị,</p>"
            f"<p>{_html.escape(mo)}</p>" + "".join(html) + f"<p>{_html.escape(ket)}</p></div>")
    return td.gui(tieu_de=f"[{nhan}] Marou đã xuất kho {len(ds)} đơn, chuẩn bị nhận hàng", text=text, html=body,
                  loai="ic_xuat_kho", khoa=f"ic_xuat|{asst.cong_ty}|" + ",".join(sorted(d["purchaseOrder"] for d in ds)),
                  cong_ty=asst.cong_ty, nguoi_soan="mẫu có sẵn", ngay=ngay)


# ---------------------------------------------------------------- de xuat post nhan hang
def _de_xuat_post(asst: Any, d: dict[str, Any]) -> list[Delivery]:
    """Ghi de xuat PostReceipt vao BC va day the sang nguoi duyet. Mot don mot de xuat."""
    ref = f"ICRECV|{d['purchaseOrder']}"
    if any(p.get("channel_ref") == ref and p["status"] == "Proposed" for p in asst.mem.proposals("Proposed")):
        return []
    dong = (d.get("lines") or [{}])[0]
    con = float(d.get("outstanding") or 0)
    shp = d.get("shipment") or {}
    ly_do = (f"{d.get('vendorName') or 'Bên bán'} đã post xuất kho đơn {d['purchaseOrder']} ngày "
             f"{d.get('ngay_xuat') or ''} (phiếu {shp.get('no', '')}), đến nay {d.get('so_ngay', 1)} ngày mà đơn mua vẫn "
             f"còn {fmt_qty(con)} chưa nhận. Tồn trên hệ thống thấp hơn hàng thực có tại {_ten_diem(d.get('locationCode', ''))} "
             f"chừng nào chưa post. Đề nghị cho trợ lý post Receive, lấy đúng số lô bên bán đã xuất.")
    # De xuat co the da nam trong BC tu vong quet hom truoc, con bo nho tro ly thi moi. Nap lai roi gui the nhac, khong ghi
    # ban thu hai: khong nap thi bam Duyet tren the se ra "Khong tim thay de xuat" (loi cu, xem replenishment._nap_de_xuat_cu).
    cu = next((x for x in asst.gw.de_xuat() if x.get("reference_key") == ref and x.get("status") == "Proposed"), None)
    if cu:
        prop = dict(cu)
        prop.update({"evidence": {}, "channel_ref": ref, "requested_by": cu.get("requested_by") or "tro_ly",
                     "item_desc": dong.get("description") or dong.get("itemNo", ""),
                     "max_quantity": cu.get("quantity") or con, "source_doc": cu.get("source_doc") or d["purchaseOrder"]})
        quyet_cu = asst.policy.decide(prop)
        prop["policy_rule"], prop["policy_mode"] = quyet_cu.rule_code, quyet_cu.mode.value
        asst.mem.save_proposal(prop)
        return _the_de_xuat(asst, d, prop, ly_do, quyet_cu.reason)
    created = asst.gw.create_proposal(
        scenario="StoreReplenishment", action_type="PostReceipt", item_no=dong.get("itemNo", ""),
        from_loc=shp.get("locationCode", ""), to_loc=d.get("locationCode", ""), quantity=con,
        reference_key=ref, rationale=ly_do, priority=60,
        evidence={"purchaseOrder": d["purchaseOrder"], "shipment": shp.get("no", ""), "postingDate": str(d.get("ngay_xuat") or ""),
                  "outstanding": con, "lines": d.get("lines", []), "shipmentLines": shp.get("lines", [])},
        run_id=asst.run_id, model_name=asst.model_name, vendor_no=d.get("vendorNo", ""), source_doc=d["purchaseOrder"])
    prop = {"proposal_id": created.get("proposalId") or str(uuid.uuid4()), "bc_id": created["id"],
            "scenario": "StoreReplenishment", "action_type": "PostReceipt", "status": "Proposed",
            "item_no": dong.get("itemNo", ""), "item_desc": dong.get("description") or dong.get("itemNo", ""),
            "from_loc": shp.get("locationCode", ""), "to_loc": d.get("locationCode", ""), "quantity": con,
            "max_quantity": con, "rationale": ly_do, "evidence": {}, "requested_by": "tro_ly",
            "created_at": asst.mem.now().isoformat(), "channel_ref": ref, "vendor_no": d.get("vendorNo", ""),
            "source_doc": d["purchaseOrder"]}
    quyet = asst.policy.decide(prop)
    prop["policy_rule"], prop["policy_mode"] = quyet.rule_code, quyet.mode.value
    asst.mem.save_proposal(prop)
    return _the_de_xuat(asst, d, prop, ly_do, quyet.reason)


def _the_de_xuat(asst: Any, d: dict[str, Any], prop: dict[str, Any], ly_do: str, ly_do_policy: str) -> list[Delivery]:
    """The cho nguoi duyet. Day la cho DUY NHAT ghi so lo ra man hinh: nguoi duyet can thay BC se ghi lo nao vao phieu nhan."""
    card = Card(title=f"Cho trợ lý post nhận hàng đơn {d['purchaseOrder']}?",
                body=ly_do + "\n\n" + "\n".join(_dong_hang(d, kem_lo=True)) + f"\n\n{ly_do_policy}",
                facts=_facts(d) + [("Đã xuất kho", f"{d.get('so_ngay', 1)} ngày trước"), ("Người đề nghị", "Trợ lý")],
                links=_links(d) + [("Trang NWV Agent Proposals", link("agent_proposals"))],
                kind="proposal", ref=prop["proposal_id"],
                actions=[Action("approve", "Duyệt cho post nhận hàng", "positive"),
                         Action("reject", "Để người post", "destructive", needs_input="reason")])
    nhan = {u["user_id"] for vai in VAI_DUYET for u in asst.mem.users_by_role(vai)}
    return [Delivery(u, f"Đơn {d['purchaseOrder']} đã xuất kho {d.get('so_ngay', 1)} ngày mà chưa nhận", card, SKILL,
                     prop["proposal_id"]) for u in sorted(nhan)]


# ---------------------------------------------------------------- vong quet
def quet(asst: Any, nguoi: dict[str, Any] | None = None, bat_buoc: bool = False) -> list[Delivery]:
    """Mot vong. `nguoi` la ai kich hoat (None la lich chay nen); `bat_buoc` bo qua chong lap trong ngay."""
    from .. import thu_dien_tu as td
    ngay = asst.mem.now().astimezone().strftime("%Y-%m-%d")
    nhom = thu_thap(asst)
    out: list[Delivery] = []

    # 1. Doi tac xuat kho trong ngay: bao ngay, mot lan mot don.
    moi = [d for d in nhom["trong_ngay"] if not _kv(asst, f"ic_bao_xuat:{d['purchaseOrder']}") or bat_buoc]
    for d in moi:
        the = _the_bao_xuat(d)
        cau = (f"{d.get('vendorName') or 'Marou'} vừa post xuất kho đơn {d['purchaseOrder']}, giao đến "
               f"{_ten_diem(d.get('locationCode', ''))}. Chuẩn bị nhận hàng; hàng tới thì post Receive trên đơn mua.")
        for u in _nguoi_nhan(asst, d):
            out.append(Delivery(u, cau, the, SKILL, the.ref))
        _dat_kv(asst, f"ic_bao_xuat:{d['purchaseOrder']}", ngay)
    if moi:
        kq = _thu_bao_xuat(asst, moi, ngay)
        for u in {x["user_id"] for vai in VAI_TRO_CHU_VIEC for x in asst.mem.users_by_role(vai)}:
            out.append(Delivery(u, f"Tôi đã gửi email báo xuất kho cho {len(moi)} đơn "
                                   f"({td.TEN_TRANG_THAI.get(kq['trang_thai'], kq['trang_thai'])}).", skill=SKILL, ref="ic-xuat-mail"))

    # 2. Qua ngay hom sau van chua post nhan: nhac lai va de xuat cho tro ly post.
    for d in nhom["qua_ngay"]:
        po = d["purchaseOrder"]
        if _kv(asst, f"ic_nhac_nhan:{po}") == ngay and not bat_buoc:
            continue
        _dat_kv(asst, f"ic_nhac_nhan:{po}", ngay)
        cau = (f"Đơn {po} đã được {d.get('vendorName') or 'Marou'} xuất kho từ {d['ngay_xuat']} ({d['so_ngay']} ngày), "
               f"nhưng đơn mua tại {_ten_diem(d.get('locationCode', ''))} vẫn còn {fmt_qty(float(d.get('outstanding') or 0))} "
               f"chưa post nhận. Tồn trên hệ thống đang thấp hơn hàng thực có.")
        for u in _nguoi_nhan(asst, d):
            out.append(Delivery(u, cau, skill=SKILL, ref=f"ic-nhac|{po}"))
        out += _de_xuat_post(asst, d)

    # 3. Da post nhan: bao mot lan roi thoi.
    for d in nhom["da_nhan"]:
        po = d["purchaseOrder"]
        if not _kv(asst, f"ic_bao_xuat:{po}") or _kv(asst, f"ic_dong:{po}"):
            continue
        _dat_kv(asst, f"ic_dong:{po}", ngay)
        cau = f"Đơn {po} đã được post nhận hàng đủ tại {_ten_diem(d.get('locationCode', ''))}. Tôi đóng việc theo dõi đơn này."
        for u in _nguoi_nhan(asst, d):
            out.append(Delivery(u, cau, skill=SKILL, ref=f"ic-xong|{po}"))

    if nguoi and not out:
        out.append(Delivery(nguoi["user_id"], "Không có đơn mua intercompany nào mới xuất kho, cũng không có đơn nào quá hạn "
                                              "chưa post nhận.", skill=SKILL))
    return out


def on_duyet_post(asst: Any, user: dict[str, Any], prop: dict[str, Any], res: dict[str, Any]) -> list[Delivery]:
    """Sau khi BC post phieu nhan. Goi tu replenishment.on_approve khi Result Document Type = 'Purchase Receipt'."""
    po = prop.get("source_doc") or ""
    rcpt = res.get("resultDocumentNo") or ""
    hang = []
    for x in asst.gw.ic_giao_hang(NHA_CUNG_CAP_IC):
        if x["purchaseOrder"] == po:
            hang = _dong_hang(x)
            break
    card = Card(title=f"Đã post phiếu nhận {rcpt} cho đơn {po}",
                body="\n".join([f"{user.get('display_name') or user['user_id']} duyệt cho trợ lý post nhận hàng. "
                                f"Hàng đã vào tồn của cửa hàng, số trên hệ thống khớp lại với hàng thực có."] + hang),
                facts=[("Đơn mua", po), ("Phiếu nhận", rcpt), ("Số lượng", fmt_qty(float(prop.get("quantity") or 0))),
                       ("Nhận tại", f"{_ten_diem(prop.get('to_loc', ''))} ({prop.get('to_loc', '')})"),
                       ("Người duyệt", user.get("display_name") or user["user_id"])],
                links=[("Mở phiếu nhận trong Business Central", link("purchase_receipt", {"No.": rcpt})),
                       ("Mở đơn mua", link("purchase_order", {"Document Type": "Order", "No.": po}))],
                kind="info", ref=rcpt)
    nhan = set(_nguoi_nhan(asst, {"locationCode": prop.get("to_loc", "")})) | {user["user_id"]}
    return [Delivery(u, f"Đã post phiếu nhận {rcpt} cho đơn mua {po}.", card, SKILL, rcpt) for u in sorted(nhan)]


def handle(asst: Any, user: dict[str, Any], text: str = "") -> list[Delivery]:
    """Supply Chain, dieu phoi, quan tri hoi "hang Marou da xuat chua"."""
    if user.get("role") not in VAI_TRO_DUOC_GOI:
        nhom = thu_thap(asst)
        cua_toi = [d for d in nhom["trong_ngay"] + nhom["qua_ngay"] if d.get("locationCode") == user.get("store_code")]
        if not cua_toi:
            return [Delivery(user["user_id"], "Hiện không có đơn hàng nào từ Marou đã xuất kho mà cửa hàng bạn chưa nhận.", skill=SKILL)]
        return [Delivery(user["user_id"], f"Marou đã xuất kho đơn {d['purchaseOrder']}, chuẩn bị nhận hàng.",
                         _the_bao_xuat(d), SKILL, f"ic-xuat|{d['purchaseOrder']}") for d in cua_toi]
    return quet(asst, user, bat_buoc=True)
