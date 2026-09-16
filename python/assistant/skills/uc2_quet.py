"""UC2 A2: tro ly tu quet moi sang, tu soan de xuat, gui brief va nhac, khong ai phai bam.

Vi sao (16/09/2026). Truoc do moi thu deu cho nguoi bam Brief hoac hoi. Tai lieu 09 (US-10, A2): moi sang tu quet ket qua moi,
tu soan de xuat cho lo vuot nguong, gui qua kenh nguoi dung quen dung, nhac lai neu chua xu ly. Kenh o POC: chat trong tro ly
va email (MAIL_TO). Teams chua co.

Mot vong quet, moi company, moi ngay mot lan (lich trong web.py theo QUET_UC2_GIO, hoac nut / POST /api/quet-uc2):
  1. Lo DA HET HAN chua co de xuat va chua tung bao: tu ghi de xuat Write-off vao BC (nguoi de nghi la "tro ly"), the den nguoi duyet
     nhu moi de xuat khac. Policy P-05 bat buoc nguoi duyet, nen day la tu dong hoa co phanh.
  2. Lo CAN DATE moi con phan du: the "Phuong an xu ly" (D4) cho Supply Chain, toi da 3 lo gia tri lon nhat mot ngay.
  3. Brief S1 cho Supply Chain va tung quan ly cua hang; ban cua Supply Chain gui email.
  4. De xuat cho duyet qua 1 ngay: mot dong nhac nguoi duyet.
  5. Chay cac viec theo doi (A3: chung tu huy chua post; chuyen hang chua ship).
Da bao roi thi khong bao lai (kv `quet_da_bao:<lo>`), de moi sang chi co cai MOI.
"""
from __future__ import annotations

import html as _html
import logging
from datetime import timedelta
from typing import Any

from ..bc_link import link
from ..cards import fmt_vnd
from . import Delivery
from . import inventory_health as ih
from . import uc2_hanh_dong as d4
from . import uc2_tom_tat as tt
from .nhac_post import _dat_kv, _kv

log = logging.getLogger(__name__)
SKILL = "inventory_health"
NGUOI_QUET = {"user_id": "tro_ly", "display_name": "Trợ lý (quét sáng)", "role": "agent"}
TOI_DA_DE_XUAT_HUY = 10
TOI_DA_PHUONG_AN = 3
VAI_NHAN_BRIEF = ("supply_chain", "store_manager")
VAI_DUYET = ("supply_chain", "dispatcher")


def _ngay(asst: Any) -> str:
    return asst.mem.now().astimezone().strftime("%Y-%m-%d")


def quet(asst: Any, nguoi: dict[str, Any] | None = None, bat_buoc: bool = False) -> list[Delivery]:
    """Mot vong quet. `nguoi` la ai bam nut (None la lich chay nen). `bat_buoc`: chay lai du hom nay da chay."""
    from .. import thu_dien_tu as td
    ngay = _ngay(asst)
    if _kv(asst, "quet_uc2_ngay") == ngay and not bat_buoc:
        return [Delivery(nguoi["user_id"], "Sáng nay tôi đã quét rồi. Bấm lại với \"chạy lại\" nếu muốn quét thêm một lần.", skill=SKILL)] if nguoi else []
    rows = asst.gw.doc("inventoryHealthLines", [], top=5000)
    out: list[Delivery] = []
    tom_tat: dict[str, Any] = {"de_xuat_huy": 0, "phuong_an": 0, "brief": 0, "nhac_duyet": 0, "theo_doi": 0, "email": ""}

    # 1. Lo het han moi: tu ghi de xuat huy, nguoi duyet nhan the.
    dang_co = set(asst.gw.de_xuat_dang_co()) | {p.get("channel_ref") for p in asst.mem.proposals("Proposed")}
    het_han = sorted([r for r in rows if r.get("tier") == "Expired" and int(r.get("riskScore") or 0) >= 60],
                     key=lambda r: -float(r.get("inventoryValue") or 0))
    for r in het_han:
        ref = tt._ref(r)
        if ref in dang_co or _kv(asst, f"quet_da_bao:{ref}"):
            continue
        if tom_tat["de_xuat_huy"] >= TOI_DA_DE_XUAT_HUY:
            break
        try:
            ra = ih.on_propose(asst, NGUOI_QUET, r["id"], "WriteOff")
        except Exception as exc:                        # mot dong hong khong duoc lam hong ca vong quet
            log.warning("Quet: khong ghi duoc de xuat huy cho %s: %s", ref, exc)
            continue
        out += [d for d in ra if d.user_id != NGUOI_QUET["user_id"]]
        _dat_kv(asst, f"quet_da_bao:{ref}", ngay)
        tom_tat["de_xuat_huy"] += 1

    # 2. Lo can date moi con phan du: phuong an D4 cho Supply Chain.
    sc = asst.mem.users_by_role("supply_chain")
    can_date = sorted([r for r in rows if r.get("tier") == "NearExpiry" and (r.get("daysToExpiry") or -1) >= 0],
                      key=lambda r: -float(r.get("inventoryValue") or 0))
    for r in can_date:
        ref = tt._ref(r)
        if _kv(asst, f"quet_da_bao:{ref}") or ref in dang_co:
            continue
        if tom_tat["phuong_an"] >= TOI_DA_PHUONG_AN:
            break
        pt = d4.phan_tich(asst, r)
        _dat_kv(asst, f"quet_da_bao:{ref}", ngay)
        if pt["_du"] <= 0:
            continue
        kq = d4.goi_y(asst, r["id"])
        the = d4.the_phuong_an(kq)
        for u in sc:
            out.append(Delivery(u["user_id"], f"Lô cận date mới: {r['itemDescription']} tại {r['locationCode']}", the, SKILL, r["id"]))
        tom_tat["phuong_an"] += 1

    # 3. Brief S1 cho tung nguoi, ban Supply Chain gui email.
    thu_text = ""
    for vai in VAI_NHAN_BRIEF:
        for u in asst.mem.users_by_role(vai):
            b = tt.brief_ai(asst, u, kem_the_dong=False)
            if not b:
                continue
            out += b
            tom_tat["brief"] += 1
            if vai == "supply_chain" and not thu_text and b[0].card:
                thu_text = b[0].card.body
    if thu_text:
        khoa = f"quet_uc2|{asst.cong_ty}|{ngay}"
        if not td.da_gui_hom_nay(khoa, ngay) or bat_buoc:
            text = thu_text + "\n\nMở bảng Inventory Health: " + link("inventory_health") + "\n\nEmail do trợ lý vận hành Marou tự soạn mỗi sáng từ bảng NWV Inventory Health."
            kq = td.gui(tieu_de=f"[{asst.cong_ty or 'Marou'}] Brief sức khỏe tồn kho {asst.gw.today().strftime('%d/%m/%Y')}", text=text,
                        html="<div style='font-family:Segoe UI,Arial,sans-serif;font-size:14px'><p>" + _html.escape(thu_text).replace("\n", "<br>")
                             + f"</p><p><a href='{_html.escape(link('inventory_health'))}'>Mở bảng Inventory Health</a></p></div>",
                        loai="quet_uc2", khoa=khoa, cong_ty=asst.cong_ty, nguoi_soan="brief S1", ngay=ngay)
            tom_tat["email"] = td.TEN_TRANG_THAI.get(kq["trang_thai"], kq["trang_thai"])
        else:
            tom_tat["email"] = "đã gửi hôm nay"

    # 4. De xuat cho duyet qua mot ngay.
    moc = (asst.mem.now() - timedelta(hours=24)).isoformat()
    cu = [p for p in asst.de_xuat_gop() if p.get("status") == "Proposed" and p.get("scenario") == "InventoryHealth"
          and str(p.get("created_at") or "") < moc]
    if cu:
        gia_tri = sum(float(p.get("value_vnd") or 0) for p in cu)
        cau = (f"Còn {len(cu)} đề xuất tồn kho chờ duyệt quá 1 ngày, cũ nhất từ {tt._ngay(min(str(p.get('created_at') or '') for p in cu))}"
               + (f", tổng giá trị {fmt_vnd(gia_tri)}" if gia_tri else "") + ". Bấm Brief hoặc mở trang NWV Agent Proposals để duyệt.")
        for u in {x["user_id"]: x for vai in VAI_DUYET for x in asst.mem.users_by_role(vai)}.values():
            out.append(Delivery(u["user_id"], cau, skill=SKILL, ref="nhac-duyet"))
        tom_tat["nhac_duyet"] = len(cu)

    # 4b. Thu Hai: bao cao tuan hang huy (S3) cho Supply Chain va quan tri, kem email.
    if asst.gw.today().weekday() == 0:
        try:
            from . import uc2_bao_cao_huy
            out += uc2_bao_cao_huy.gui(asst)
            tom_tat["bao_cao_tuan"] = True
        except Exception as exc:
            log.warning("Quet: bao cao tuan hong: %s", exc)

    # 5. Viec theo doi (A3 va chuyen hang).
    try:
        td_out = asst.run_followups()          # da ghi hop thu roi (meta da_ghi), gop vao de nguoi bam nut thay
        out += td_out
        tom_tat["theo_doi"] = len(td_out)
    except Exception as exc:
        log.warning("Quet: theo doi hong: %s", exc)

    _dat_kv(asst, "quet_uc2_ngay", ngay)
    cau = (f"Quét sáng xong: {tom_tat['de_xuat_huy']} đề xuất hủy mới cho lô hết hạn, {tom_tat['phuong_an']} phương án cho lô cận date, "
           f"brief gửi {tom_tat['brief']} người" + (f", email {tom_tat['email']}" if tom_tat["email"] else "")
           + (f", nhắc {tom_tat['nhac_duyet']} đề xuất chờ duyệt" if tom_tat["nhac_duyet"] else "")
           + (f", {tom_tat['theo_doi']} tin theo dõi" if tom_tat["theo_doi"] else "") + ".")
    nhan = {u["user_id"] for u in asst.mem.users_by_role("admin")} | ({nguoi["user_id"]} if nguoi else set())
    for uid in sorted(nhan):
        out.append(Delivery(uid, cau, skill=SKILL, ref="quet-uc2"))
    return out
