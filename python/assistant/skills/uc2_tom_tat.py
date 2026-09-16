"""UC2, nhom Tom tat: S1 brief buoi sang do AI viet, S2 giai thich lo bang loi thuong.

Vi sao co file nay (15/09/2026). Dung nhan xet UC2 "toan thay application, khong thay AI". Kim chi nam da chot: BC tinh so,
AI khong tinh lai; moi dau ra AI co nguon; AI bat tat duoc. Hai tinh nang dau tien theo thu tu trong tai lieu 09 la S1 va S2,
vi du lieu da co san va Tom tat hien ngay tren man hinh dau tien.

Ai lam gi. Code doc bang Inventory Health da tinh, chon dong ung vien, cong so, tinh "du kien du" (ton tru ban duoc truoc han),
tim cua hang ban nhanh hon, gom de xuat dang cho va ly do tu choi gan day. Model chi viet loi: chon toi da 3 viec TRONG danh
sach code dua, viet ly do, cau mo dau va cau ket (S1); hoac viet mot doan noi ve lo (S2). Ba phep kiem sau khi model viet:
  1. moi chu so trong doan model viet phai co trong du lieu dua model (so la = model tu tinh, bo);
  2. moi dong model chon phai la dong code dua (id la, bo);
  3. rong thi bo.
Bo la dung mau do code ghep. Tat AI hoac het tran chi phi: dung mau ngay, khong goi model. Nguoi doc luon thay "Nguoi soan".
"""
from __future__ import annotations

import json
import logging
import re
from datetime import date, timedelta
from typing import Any

from ..bc_link import link
from ..cards import Card, fmt_qty, fmt_vnd
from . import Delivery
from .inventory_health import line_card
from .nhac_post import _dat_kv, _kv

log = logging.getLogger(__name__)
SKILL = "inventory_health"
SO_VIEC = 3
NGAY_NHO_TU_CHOI = 14
SO_UNG_VIEN = 8

TEN_TANG = {"Expired": "đã hết hạn", "NearExpiry": "cận date", "StockOutRisk": "sắp hết hàng", "SlowMoving": "chậm luân chuyển",
            "Excess": "dư tồn", "Healthy": "trong ngưỡng"}
VIEC_THEO_TANG = {"Expired": "đề xuất hủy", "NearExpiry": "chuyển sang cửa hàng bán nhanh hoặc giảm giá", "StockOutRisk": "bổ sung hàng",
                  "SlowMoving": "giảm giá hoặc ngừng nhập", "Excess": "chặn mua thêm"}

SCHEMA_BRIEF = {"type": "object", "additionalProperties": False, "required": ["mo_dau", "viec", "ket"],
                "properties": {"mo_dau": {"type": "string"},
                               "viec": {"type": "array", "items": {"type": "object", "additionalProperties": False,
                                                                   "required": ["id", "viec", "ly_do"],
                                                                   "properties": {"id": {"type": "string"}, "viec": {"type": "string"},
                                                                                  "ly_do": {"type": "string"}}}},
                               "ket": {"type": "string"}}}
SCHEMA_LO = {"type": "object", "additionalProperties": False, "required": ["doan"], "properties": {"doan": {"type": "string"}}}


# ---------------------------------------------------------------- goi model, kiem so
def _chu_so(s: str) -> set[str]:
    return set(re.findall(r"\d+", s))


def so_la(du_lieu: Any, *doan: str) -> set[str]:
    """Chu so xuat hien trong doan model viet ma khong co trong du lieu dua model."""
    duoc = _chu_so(json.dumps(du_lieu, ensure_ascii=False))
    return set().union(*[_chu_so(d or "") for d in doan]) - duoc


def _goi_model(asst: Any, muc_dich: str, system: str, du_lieu: dict[str, Any], schema: dict[str, Any],
               max_tokens: int = 700) -> tuple[dict[str, Any] | None, str]:
    """Tra (json model tra ve, nguoi_soan). None nghia la dung mau; nguoi_soan noi ro vi sao."""
    w = getattr(asst, "_writer", None)
    if not w or not asst.budget.allow():
        return None, "mẫu có sẵn (AI đang tắt)"
    try:
        from bc_agent.llm import text_of
        resp = w.text(system=system, user=json.dumps(du_lieu, ensure_ascii=False), max_tokens=max_tokens, schema=schema)
        asst.budget.track(muc_dich, w.model, resp.usage)
        d = json.loads(text_of(resp) or "{}")
        if not isinstance(d, dict):
            return None, "mẫu có sẵn (model trả về không đúng dạng)"
        from bc_agent.config import settings
        return d, f"AI ({settings.live_model_name or 'model'})"
    except Exception as exc:
        log.warning("Model %s hong: %s", muc_dich, exc)
        return None, "mẫu có sẵn (gọi model không được)"


def _ngay(s: str | None) -> str:
    try:
        return date.fromisoformat(str(s)[:10]).strftime("%d/%m/%Y")
    except Exception:
        return str(s or "")


# ---------------------------------------------------------------- du lieu chung
def _ref(r: dict[str, Any]) -> str:
    return f"{r['itemNo']}|{r['locationCode']}|{r.get('lotNo', '')}"


def _du_kien(r: dict[str, Any]) -> dict[str, Any]:
    """Voi lo con han: ban duoc bao nhieu truoc han theo binh quan hien tai, va du bao nhieu. Code tinh, model chi noi lai."""
    qty = float(r.get("quantityOnHand") or 0)
    avg = float(r.get("avgDailySalesQty") or 0)
    dte = r.get("daysToExpiry")
    if dte is None or dte < 0:
        return {}
    ban = round(min(qty, avg * dte), 1)
    return {"ban_duoc_truoc_han": fmt_qty(ban), "du_kien_du": fmt_qty(max(0.0, round(qty - ban, 1)))}


def tu_choi_gan_day(asst: Any) -> dict[str, dict[str, Any]]:
    """De xuat bi tu choi trong NGAY_NHO_TU_CHOI ngay, khoa theo item|dia diem|lo. Brief nho de khong doi lai viec vua bi bac."""
    moc = asst.mem.now() - timedelta(days=NGAY_NHO_TU_CHOI)
    ten_hang = {i["itemNo"]: i["description"] for i in asst.gw.items()}     # bo nho tro ly khong luu ten mat hang
    ra: dict[str, dict[str, Any]] = {}
    for p in asst.de_xuat_gop():
        if p.get("status") != "Rejected" or p.get("scenario") != "InventoryHealth":
            continue
        luc = str(p.get("approved_at") or p.get("created_at") or "")
        try:
            from datetime import datetime
            if datetime.fromisoformat(luc.replace("Z", "+00:00")) < moc:
                continue
        except ValueError:
            pass
        khoa = p.get("channel_ref") or p.get("reference_key") or f"{p.get('item_no')}|{p.get('from_loc')}|{p.get('lot_no', '')}"
        ra[khoa] = {"mat_hang": p.get("item_desc") or ten_hang.get(p.get("item_no", ""), p.get("item_no")), "dia_diem": p.get("from_loc"), "lo": p.get("lot_no", ""),
                    "hanh_dong": p.get("action_type"), "ly_do": p.get("outcome_note") or p.get("reviewComment") or "không nêu lý do",
                    "ngay": _ngay(luc)}
    return ra


def _dong_ung_vien(r: dict[str, Any], tu_choi: dict[str, dict[str, Any]]) -> dict[str, Any]:
    d = {"id": r["id"], "mat_hang": r["itemDescription"], "ma": r["itemNo"], "dia_diem": r["locationCode"], "lo": r.get("lotNo") or "",
         "tang": TEN_TANG.get(r["tier"], r["tier"]), "diem_rui_ro": r["riskScore"], "ton": fmt_qty(float(r["quantityOnHand"])),
         "gia_tri": fmt_vnd(float(r["inventoryValue"])), "han_dung": _ngay(r.get("expirationDate")), "con_ngay_den_han": r.get("daysToExpiry"),
         "ngay_du_ban": r.get("daysOfCover"), "ban_binh_quan_ngay": round(float(r.get("avgDailySalesQty") or 0), 1), "ly_do_xep_tang": r.get("riskReason", ""),
         "viec_thuong_lam": VIEC_THEO_TANG.get(r["tier"], "xem lại")}
    d.update(_du_kien(r))
    tc = tu_choi.get(_ref(r))
    if tc:
        d["da_tu_choi"] = f"{tc['hanh_dong']} bị từ chối ngày {tc['ngay']}: {tc['ly_do']}"
    return d


# ---------------------------------------------------------------- S1: brief do AI viet
def du_lieu_brief(asst: Any, user: dict[str, Any]) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    """Du lieu dua model (moi con so o day la con so duy nhat model duoc dung) va danh sach dong ung vien theo thu tu rui ro."""
    noi = user.get("store_code") or ""
    tat_ca = [r for r in asst.gw.doc("inventoryHealthLines", [], top=5000) if not noi or r.get("locationCode") == noi]
    theo_tang: dict[str, dict[str, Any]] = {}
    for r in tat_ca:
        t = theo_tang.setdefault(r["tier"], {"so_lo": 0, "gia_tri": 0.0})
        t["so_lo"] += 1
        t["gia_tri"] += float(r.get("inventoryValue") or 0)
    tu_choi = tu_choi_gan_day(asst)
    ung_vien = sorted([r for r in tat_ca if int(r.get("riskScore") or 0) >= 60], key=lambda r: -int(r["riskScore"]))[:SO_UNG_VIEN]
    cho = [p for p in asst.de_xuat_gop() if p.get("status") == "Proposed" and p.get("scenario") == "InventoryHealth"
           and (not noi or p.get("from_loc") == noi)]
    du_lieu = {
        "ngay": asst.gw.today().strftime("%d/%m/%Y"), "pham_vi": f"cửa hàng {noi}" if noi else "mọi địa điểm",
        "vai": user.get("role", ""), "so_viec_can_chon": SO_VIEC,
        "theo_tang": {TEN_TANG.get(k, k): {"so_lo": v["so_lo"], "gia_tri": fmt_vnd(v["gia_tri"])} for k, v in theo_tang.items()
                      if k != "Healthy"},
        "dong_ung_vien": [_dong_ung_vien(r, tu_choi) for r in ung_vien],
        "de_xuat_dang_cho_duyet": [{"mat_hang": p.get("item_desc") or p.get("item_no"), "dia_diem": p.get("from_loc"),
                                    "hanh_dong": p.get("action_type"), "so_luong": fmt_qty(float(p.get("quantity") or 0))} for p in cho[:5]],
        "so_de_xuat_dang_cho": len(cho),
        "tu_choi_gan_day": [v for k, v in tu_choi.items() if not noi or v.get("dia_diem") == noi][:5],
    }
    return du_lieu, ung_vien


_SYSTEM_BRIEF = (
    "Bạn là trợ lý vận hành của Marou Chocolate, viết bản tóm tắt buổi sáng về sức khỏe tồn kho cho người đọc theo vai trong dữ liệu. "
    "Xưng 'tôi', gọi người đọc là 'bạn'. Dữ liệu là bảng Business Central đã tính, bạn không được tính lại hay suy ra con số mới: "
    "chỉ dùng đúng những con số có trong dữ liệu. Chọn tối đa so_viec_can_chon việc quan trọng nhất trong dong_ung_vien (ghi đúng id), "
    "ưu tiên giá trị lớn, hạn sát và việc chưa có đề xuất chờ duyệt; dòng có 'da_tu_choi' thì không chọn lại trừ khi tình hình đã khác, "
    "và nếu nhắc thì nói rõ đã bị từ chối vì sao. mo_dau: 1-2 câu tình hình chung theo theo_tang. Mỗi việc: 'viec' là một câu hành động "
    "cụ thể có tên mặt hàng, địa điểm, số lượng; 'ly_do' một câu vì sao xếp trước việc khác. ket: 1 câu, nhắc số đề xuất đang chờ duyệt "
    "nếu có, và nói rõ tôi chỉ đề xuất, người duyệt quyết. Tiếng Việt, ngắn, không chào hỏi, không dùng gạch đầu dòng.")


def _brief_mau(du_lieu: dict[str, Any], ung_vien: list[dict[str, Any]]) -> dict[str, Any]:
    """Mau do code ghep khi khong co model: 3 dong rui ro cao nhat chua bi tu choi gan day."""
    tu_choi = {d["id"] for d in du_lieu["dong_ung_vien"] if d.get("da_tu_choi")}
    chon = [r for r in ung_vien if r["id"] not in tu_choi][:SO_VIEC] or ung_vien[:SO_VIEC]
    tang = du_lieu["theo_tang"]
    phan = [f"{v['so_lo']} lô {k} ({v['gia_tri']})" for k, v in tang.items() if v["so_lo"]]
    mo = f"Tính đến {du_lieu['ngay']}, {du_lieu['pham_vi']} có " + (", ".join(phan) if phan else "không dòng nào vượt ngưỡng") + "."
    viec = []
    for r in chon:
        dk = _du_kien(r)
        them = (f" Bán bình quân {round(float(r.get('avgDailySalesQty') or 0), 1)}/ngày, đến hạn bán được khoảng {dk['ban_duoc_truoc_han']}, dư {dk['du_kien_du']}."
                if dk and r["tier"] == "NearExpiry" else "")
        viec.append({"id": r["id"], "viec": f"{r['itemDescription']} tại {r['locationCode']}" + (f", lô {r['lotNo']}" if r.get("lotNo") else "")
                                             + f": {VIEC_THEO_TANG.get(r['tier'], 'xem lại')}, tồn {fmt_qty(float(r['quantityOnHand']))} "
                                             f"({fmt_vnd(float(r['inventoryValue']))}).",
                     "ly_do": f"{r.get('riskReason', '')} Điểm rủi ro {r['riskScore']}.{them}"})
    so_cho = du_lieu["so_de_xuat_dang_cho"]
    ket = (f"Đang có {so_cho} đề xuất chờ duyệt. " if so_cho else "") + "Tôi chỉ đề xuất, người duyệt quyết."
    tc = du_lieu["tu_choi_gan_day"]
    if tc:
        ket += f" Tôi không đề xuất lại {tc[0]['mat_hang']} tại {tc[0]['dia_diem']} vì đã bị từ chối ngày {tc[0]['ngay']} ({tc[0]['ly_do']})."
    return {"mo_dau": mo, "viec": viec, "ket": ket}


def _kiem_brief(d: dict[str, Any] | None, du_lieu: dict[str, Any]) -> str:
    """'' neu dung, khong thi ly do bo."""
    if not d:
        return "model trả về rỗng"
    viec = d.get("viec") or []
    ids = {x["id"] for x in du_lieu["dong_ung_vien"]}
    if not viec or not isinstance(viec, list):
        return "model không chọn việc nào"
    la_id = [v.get("id") for v in viec if not isinstance(v, dict) or v.get("id") not in ids]
    if la_id:
        return "model chọn dòng không có trong dữ liệu"
    if len({v["id"] for v in viec}) != len(viec):
        return "model chọn trùng dòng"
    la = so_la(du_lieu, d.get("mo_dau", ""), d.get("ket", ""), *[v.get("viec", "") + " " + v.get("ly_do", "") for v in viec])
    if la:
        return "đoạn model viết có số không có trong dữ liệu: " + ", ".join(sorted(la))
    if not (d.get("mo_dau") or "").strip():
        return "model không viết câu mở đầu"
    return ""


def soan_brief(asst: Any, user: dict[str, Any]) -> dict[str, Any]:
    """Tra {"mo_dau","viec","ket","nguoi_soan","du_lieu","ung_vien"}; viec da cat con SO_VIEC."""
    du_lieu, ung_vien = du_lieu_brief(asst, user)
    if not ung_vien:
        return {"mo_dau": "", "viec": [], "ket": "", "nguoi_soan": "", "du_lieu": du_lieu, "ung_vien": []}
    d, nguoi_soan = _goi_model(asst, "brief", _SYSTEM_BRIEF, du_lieu, SCHEMA_BRIEF)
    if d is not None:
        loi = _kiem_brief(d, du_lieu)
        if loi:
            log.warning("Brief AI bi bo: %s", loi)
            d, nguoi_soan = None, f"mẫu có sẵn ({loi})"
    if d is None:
        d = _brief_mau(du_lieu, ung_vien)
    d["viec"] = d["viec"][:SO_VIEC]
    return {**d, "nguoi_soan": nguoi_soan, "du_lieu": du_lieu, "ung_vien": ung_vien}


def the_brief(b: dict[str, Any]) -> Card:
    ten = {x["id"]: x for x in b["du_lieu"]["dong_ung_vien"]}
    dong = [f"{i}. {v['viec']} {v['ly_do']}".strip() for i, v in enumerate(b["viec"], 1)]
    body = "\n".join([b["mo_dau"], ""] + dong + ["", b["ket"]]).strip()
    facts = [("Người soạn", b["nguoi_soan"]), ("Nguồn số", f"Bảng NWV Inventory Health, chốt ngày {b['du_lieu']['ngay']}"),
             ("Cách kiểm", "Mọi con số trong đoạn được đối chiếu với bảng; có số lạ thì thay bằng câu mẫu")]
    links = [("Bảng Inventory Health trong BC", link("inventory_health"))]
    for v in b["viec"][:SO_VIEC]:
        x = ten.get(v["id"])
        if x:
            links.append((f"Sổ kho {x['mat_hang']} tại {x['dia_diem']}",
                          link("item_ledger_entries", {"Item No.": x["ma"], "Location Code": x["dia_diem"], "Lot No.": x["lo"]})))
    return Card(title=f"{len(b['viec'])} việc quan trọng nhất sáng nay", body=body, facts=facts, kind="brief", ref="brief-uc2", links=links)


def brief_ai(asst: Any, user: dict[str, Any], kem_the_dong: bool = True) -> list[Delivery]:
    """S1. The tom tat len dau, roi the tung dong: dong duoc chon truoc, dong ung vien con lai sau."""
    b = soan_brief(asst, user)
    if not b["ung_vien"]:
        return []
    out = [Delivery(user["user_id"], "Brief sức khỏe tồn kho sáng nay", the_brief(b), SKILL, "brief-uc2")]
    if kem_the_dong:
        chon = [v["id"] for v in b["viec"]]
        thu_tu = sorted(b["ung_vien"], key=lambda r: (r["id"] not in chon, chon.index(r["id"]) if r["id"] in chon else 0))
        for r in thu_tu:
            out.append(Delivery(user["user_id"], r["itemDescription"], line_card(r), SKILL, r["id"]))
    return out


# ---------------------------------------------------------------- S2: giai thich lo bang loi
_SYSTEM_LO = (
    "Bạn là trợ lý vận hành của Marou Chocolate. Viết MỘT đoạn 3-5 câu tiếng Việt, xưng 'tôi', giải thích cho quản lý về một lô hàng "
    "theo dữ liệu Business Central đã tính: vì sao lô vào tầng này (quy tắc nào khớp), bán được bao nhiêu và bao nhiêu một ngày, "
    "còn bao lâu đến hạn, dự kiến bán được bao nhiêu trước hạn và dư bao nhiêu, và việc thường làm là gì. Không tính lại, không suy ra "
    "con số mới, chỉ dùng đúng con số trong dữ liệu; có 'cua_hang_ban_nhanh_hon' thì nhắc tên và tốc độ bán của nó. Có 'de_xuat_dang_cho' "
    "thì nói đang chờ duyệt. Không chào hỏi, không gạch đầu dòng, không kết luận vượt ngoài dữ liệu.")


def du_lieu_lo(asst: Any, line_id: str) -> dict[str, Any]:
    from .. import uc2
    t = uc2.trace(asst, line_id)
    r = t["line"]
    khop = next((s for s in t["cascade"] if s.get("hit")), None)
    d = {"mat_hang": r["itemDescription"], "ma": r["itemNo"], "dia_diem": r["locationCode"], "lo": r.get("lotNo") or "",
         "tang": TEN_TANG.get(r["tier"], r["tier"]), "quy_tac_khop": f"{khop['test']} ({khop['actual']})" if khop else "",
         "ly_do_xep_tang": r.get("riskReason", ""), "diem_rui_ro": r.get("riskScore"),
         "ngay_chot": asst.gw.today().strftime("%d/%m/%Y"), "han_dung": _ngay(r.get("expirationDate")),
         "con_ngay_den_han": r.get("daysToExpiry"), "chi_tieu": {c["label"]: c["value"] for c in t["calc"]},
         "ban_binh_quan_ngay": round(float(r.get("avgDailySalesQty") or 0), 1),
         "ban_gan_day": {"so_ngay": t["doiChieu"]["soNgay"], "tong": t["doiChieu"]["tong"], "nhan": t["doiChieu"]["nhan"]},
         "viec_thuong_lam": VIEC_THEO_TANG.get(r["tier"], "xem lại")}
    d.update(_du_kien(r))
    if r["tier"] in ("NearExpiry", "SlowMoving", "Excess"):
        khac = [x for x in asst.gw.stock_by_location(r["itemNo"]) if x["locationCode"] not in (r["locationCode"], asst.gw.central_wh)
                and float(x.get("avgDaily") or 0) > float(r.get("avgDailySalesQty") or 0)]
        khac.sort(key=lambda x: -float(x["avgDaily"]))
        d["cua_hang_ban_nhanh_hon"] = [{"dia_diem": x["locationCode"], "ban_binh_quan_ngay": round(float(x["avgDaily"]), 1),
                                        "ton": fmt_qty(float(x["qty"]))} for x in khac[:2]]
    ref = _ref(r)
    cho = [p for p in asst.de_xuat_gop() if p.get("status") == "Proposed" and (p.get("channel_ref") or p.get("reference_key")) == ref]
    if cho:
        d["de_xuat_dang_cho"] = [{"hanh_dong": p.get("action_type"), "so_luong": fmt_qty(float(p.get("quantity") or 0))} for p in cho]
    tc = tu_choi_gan_day(asst).get(ref)
    if tc:
        d["da_tu_choi"] = f"{tc['hanh_dong']} bị từ chối ngày {tc['ngay']}: {tc['ly_do']}"
    return d


def _doan_mau(d: dict[str, Any]) -> str:
    cau = [f"Lô {d['lo'] or 'không mã'} của {d['mat_hang']} tại {d['dia_diem']} xếp vào tầng {d['tang']} vì {d['quy_tac_khop'] or d['ly_do_xep_tang']}."]
    ct = d["chi_tieu"]
    ban = next((v for k, v in ct.items() if k.startswith("Đã bán") or k.startswith("Lượng xuất")), None)
    if ban:
        cau.append(f"{d['ban_gan_day']['nhan']} trong cửa sổ tính là {ban}, bình quân {d['ban_binh_quan_ngay']} một ngày.")
    if d.get("con_ngay_den_han") is not None:
        if d["con_ngay_den_han"] < 0:
            cau.append(f"Hạn dùng {d['han_dung']} đã qua {-d['con_ngay_den_han']} ngày, tồn {ct.get('Tồn của lô này', '')} không bán được nữa.")
        else:
            cau.append(f"Còn {d['con_ngay_den_han']} ngày đến hạn {d['han_dung']}; theo tốc độ hiện tại bán được khoảng "
                       f"{d.get('ban_duoc_truoc_han', '?')}, dư {d.get('du_kien_du', '?')}.")
    if d.get("cua_hang_ban_nhanh_hon"):
        x = d["cua_hang_ban_nhanh_hon"][0]
        cau.append(f"{x['dia_diem']} đang bán nhanh hơn ({x['ban_binh_quan_ngay']}/ngày), là nơi có thể nhận bớt.")
    if d.get("de_xuat_dang_cho"):
        cau.append(f"Đã có đề xuất {d['de_xuat_dang_cho'][0]['hanh_dong']} đang chờ duyệt.")
    elif d.get("da_tu_choi"):
        cau.append(f"Đề xuất trước đó {d['da_tu_choi']}.")
    else:
        cau.append(f"Việc thường làm với tầng này: {d['viec_thuong_lam']}.")
    return " ".join(cau)


def giai_thich_lo(asst: Any, line_id: str) -> dict[str, Any]:
    """S2. Tra {"doan","nguoi_soan","line_id"}. Doan AI duoc nho theo dong va thoi diem tinh de khong tra tien hai lan."""
    d = du_lieu_lo(asst, line_id)
    r = next((x for x in asst.gw.doc("inventoryHealthLines", [], top=5000) if x.get("id") == line_id), {})
    khoa = f"giai_thich_lo:{line_id}|{r.get('calculatedAt', '')}"
    cu = _kv(asst, khoa)
    if cu and getattr(asst, "_writer", None):
        try:
            return {**json.loads(cu), "line_id": line_id, "nho_lai": True}
        except ValueError:
            pass
    m, nguoi_soan = _goi_model(asst, "giai_thich_lo", _SYSTEM_LO, d, SCHEMA_LO, max_tokens=400)
    doan = (m or {}).get("doan", "").strip() if m else ""
    if m is not None:
        la = so_la(d, doan)
        if not doan:
            nguoi_soan = "mẫu có sẵn (model trả về rỗng)"
        elif la:
            nguoi_soan = "mẫu có sẵn (đoạn model viết có số không có trong dữ liệu: " + ", ".join(sorted(la)) + ")"
            doan = ""
    if not doan:
        doan = _doan_mau(d)
    kq = {"doan": doan, "nguoi_soan": nguoi_soan}
    if nguoi_soan.startswith("AI"):
        _dat_kv(asst, khoa, json.dumps(kq, ensure_ascii=False))
    return {**kq, "line_id": line_id, "nho_lai": False}
