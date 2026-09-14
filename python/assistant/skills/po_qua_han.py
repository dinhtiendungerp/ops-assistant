"""UC3: bao don mua da qua ngay nhan du kien ma chua ghi nhan nhan hang trong BC.

Vi sao co file nay. Khao sat Marou ngay 13/09/2026: hang mua ve cua hang don chung tu toi cuoi thang
moi post receive, Marou thue mot nhan su ben ngoai post don. Dung chot lam truoc phan khong can quyen
post: tro ly tim dong don mua con so luong chua nhan (`Outstanding Quantity` > 0) ma `Expected Receipt
Date` da qua ngay neo, bao dung nguoi, va hoi cua hang hang da ve that chua.

Ranh gioi: tro ly KHONG post Receive. Nguoi nhan hang bam Post tren Purchase Order trong BC. Hai nut tren
the chi ghi lai cau tra loi cua cua hang va bao Supply Chain:
  - "Hang da ve, chua nhap": viec cua nguoi post chung tu, BC dang lech voi thuc te.
  - "Hang chua ve": viec cua nguoi mua, can hoi nha cung cap.
Khong goi model: moi con so doc thang tu dong don mua, so ngay tre la phep tru ngay.
"""
from __future__ import annotations

import json
from datetime import date
from typing import Any

from ..cards import Action, Card, fmt_qty
from . import Delivery

SKILL = "po_qua_han"
ENTITY = "nwvPurchaseOrderLines"
# Tre qua moc nay thi nhieu kha nang la don treo (dat roi bo, hoac nhan tay ngoai BC), khong phai hang
# dang tren duong. Van bao, nhung tach rieng de nguoi mua dong don thay vi hoi cua hang.
NGAY_DON_TREO = 60
# Vai tro nhan hang tai mot dia diem chi thay don ve dia diem cua minh.
VAI_TRO_TAI_DIEM = ("store_manager", "warehouse")
VAI_TRO_XEM_HET = ("supply_chain", "dispatcher", "admin", "retail_ops")


def _ngay(v: Any) -> date | None:
    s = str(v or "")[:10]
    if not s or s <= "0001-01-01":                    # 0D cua BC ve thanh 0001-01-01
        return None
    try:
        return date.fromisoformat(s)
    except ValueError:
        return None


def dong_qua_han(asst: Any, dia_diem: str | None = None) -> list[dict[str, Any]]:
    """Dong don mua qua han, moi dong kem `so_ngay_tre`. Sap theo tre nhieu nhat truoc."""
    hom_nay = asst.gw.today()
    ra = []
    for r in asst.gw.doc(ENTITY, [], top=5000):
        con = float(r.get("outstandingQuantity") or 0)
        du_kien = _ngay(r.get("expectedReceiptDate"))
        if con <= 0 or not du_kien or du_kien >= hom_nay:
            continue
        if dia_diem and r.get("locationCode") != dia_diem:
            continue
        ra.append({**r, "so_ngay_tre": (hom_nay - du_kien).days})
    return sorted(ra, key=lambda r: (-r["so_ngay_tre"], r.get("documentNo", ""), r.get("lineNo", 0)))


def gom_theo_don(dong: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Mot don mua co the nhieu dong va nhieu ngay du kien. Gom theo (so don, dia diem nhan)."""
    don: dict[tuple[str, str], dict[str, Any]] = {}
    for r in dong:
        k = (r.get("documentNo", ""), r.get("locationCode", ""))
        d = don.setdefault(k, {"so_don": k[0], "dia_diem": k[1], "nha_cung_cap": r.get("buyFromVendorNo", ""),
                               "dong": [], "tre_nhat": 0, "nhan_mot_phan": False})
        d["dong"].append(r)
        d["tre_nhat"] = max(d["tre_nhat"], r["so_ngay_tre"])
        if float(r.get("quantityReceived") or 0) > 0:
            d["nhan_mot_phan"] = True
    return sorted(don.values(), key=lambda d: (-d["tre_nhat"], d["so_don"]))


def _pham_vi(user: dict[str, Any]) -> str | None:
    """Dia diem ma nguoi nay duoc xem. None la xem het."""
    if user.get("role") in VAI_TRO_TAI_DIEM:
        return user.get("store_code") or "__khong_co__"
    return None


def _ref(d: dict[str, Any]) -> str:
    return f"{d['so_don']}|{d['dia_diem']}"


def _ten_diem(ma: str) -> str:
    from ..core import STORE_LABEL
    return STORE_LABEL.get(ma, ma)


def _ten_hang(asst: Any) -> dict[str, str]:
    return {i["itemNo"]: i["description"] for i in asst.gw.items()}


def _xac_nhan(asst: Any, ref: str) -> dict[str, Any] | None:
    r = asst.mem.conn.execute("SELECT v FROM kv WHERE k=?", (f"po_xac_nhan:{ref}",)).fetchone()
    return json.loads(r["v"]) if r else None


def _dong_chu(r: dict[str, Any], ten: dict[str, str]) -> str:
    ma = r.get("itemNo", "")
    mo_ta = r.get("description") or ten.get(ma) or ma
    da = float(r.get("quantityReceived") or 0)
    nhan = f", đã nhận {fmt_qty(da)}" if da else ""
    return (f"{mo_ta} ({ma}): còn {fmt_qty(float(r['outstandingQuantity']))} / {fmt_qty(float(r.get('quantity') or 0))}"
            f"{nhan}, dự kiến {_ngay(r['expectedReceiptDate']).strftime('%d/%m')}")


def _the(asst: Any, d: dict[str, Any], ten: dict[str, str], hoi_cua_hang: bool) -> Card:
    treo = d["tre_nhat"] > NGAY_DON_TREO
    body = "\n".join("· " + _dong_chu(r, ten) for r in d["dong"][:8])
    if len(d["dong"]) > 8:
        body += f"\n· và {len(d['dong']) - 8} dòng nữa"
    xn = _xac_nhan(asst, _ref(d))
    if xn:
        body += f"\n\n{xn['nguoi']} báo {xn['cau']} lúc {xn['luc']}."
    elif treo:
        body += (f"\n\nTrễ hơn {NGAY_DON_TREO} ngày: nhiều khả năng là đơn treo chứ không phải hàng đang trên đường. "
                 "Người mua nên kiểm rồi đóng dòng, không cần hỏi cửa hàng.")
    facts = [("Nhà cung cấp", d["nha_cung_cap"] or "(trống)"), ("Nhận tại", _ten_diem(d["dia_diem"])),
             ("Trễ nhất", f"{d['tre_nhat']} ngày"),
             ("Tình trạng", "đã nhận một phần" if d["nhan_mot_phan"] else "chưa nhận dòng nào")]
    actions = []
    if hoi_cua_hang and not xn and not treo:
        actions = [Action("po_da_ve", "Hàng đã về, chưa nhập", "positive"),
                   Action("po_chua_ve", "Hàng chưa về", "default")]
    from ..bc_link import link
    links = [("Mở đơn mua trong BC", link("purchase_order", {"Document Type": "Order", "No.": d["so_don"]}))]
    return Card(title=f"Đơn mua {d['so_don']} quá hạn nhận", body=body, facts=facts, actions=actions, links=links,
                ref=_ref(d), kind="question" if actions else "info")


def handle(asst: Any, user: dict[str, Any]) -> list[Delivery]:
    """Tra loi "PO nao qua han chua nhan". Nguoi nhan hang thay don ve dia diem minh va duoc hoi hang da ve chua."""
    uid = user["user_id"]
    pham_vi = _pham_vi(user)
    dong = dong_qua_han(asst, pham_vi)
    hom_nay = asst.gw.today().strftime("%d/%m/%Y")
    noi = f" về {_ten_diem(pham_vi)}" if pham_vi else ""
    if not dong:
        return [Delivery(uid, f"Tính đến {hom_nay}, không có dòng đơn mua nào{noi} quá ngày nhận dự kiến mà chưa nhận.",
                         skill=SKILL)]
    don = gom_theo_don(dong)
    treo = [d for d in don if d["tre_nhat"] > NGAY_DON_TREO]
    ten = _ten_hang(asst)
    hoi = user.get("role") in VAI_TRO_TAI_DIEM
    mo_dau = (f"Tính đến {hom_nay} có {len(don)} đơn mua{noi} quá ngày nhận dự kiến mà Business Central chưa ghi nhận "
              f"nhận hàng, {len(dong)} dòng.")
    if treo:
        mo_dau += f" Trong đó {len(treo)} đơn trễ hơn {NGAY_DON_TREO} ngày, nhiều khả năng là đơn treo."
    hoi_them: list[Delivery] = []
    if hoi:
        mo_dau += " Bạn xác nhận giúp từng đơn hàng đã về chưa. Tôi không post nhận hàng; việc đó vẫn làm trên Purchase Order."
    else:
        hoi_them = _hoi_noi_nhan(asst, don, ten)
        so_noi = len({d.user_id for d in hoi_them})
        if hoi_them:
            mo_dau += f" Tôi vừa hỏi {so_noi} nơi nhận hàng xem hàng đã về chưa; câu trả lời sẽ báo lại bạn."
        mo_dau += " Tôi không post nhận hàng."
    out = [Delivery(uid, mo_dau, skill=SKILL)]
    for d in don[:10]:
        out.append(Delivery(uid, f"{d['so_don']} · {_ten_diem(d['dia_diem'])}", card=_the(asst, d, ten, hoi),
                            skill=SKILL, ref=_ref(d)))
    out += hoi_them
    if len(don) > 10:
        out.append(Delivery(uid, f"Còn {len(don) - 10} đơn nữa, trễ ít hơn.", skill=SKILL))
    return out


def _hoi_noi_nhan(asst: Any, don: list[dict[str, Any]], ten: dict[str, str]) -> list[Delivery]:
    """Gui the hoi "hang da ve chua" cho nguoi nhan hang tai dia diem cua don. Moi don chi hoi mot lan,
    bo qua don treo va don da co cau tra loi, de Supply Chain hoi lai nhieu lan khong thanh spam."""
    nguoi_tai: dict[str, list[dict[str, Any]]] = {}
    for vai in VAI_TRO_TAI_DIEM:
        for u in asst.mem.users_by_role(vai):
            if u.get("store_code"):
                nguoi_tai.setdefault(u["store_code"], []).append(u)
    ra: list[Delivery] = []
    for d in don:
        ref = _ref(d)
        if d["tre_nhat"] > NGAY_DON_TREO or _xac_nhan(asst, ref):
            continue
        khoa = f"po_da_hoi:{ref}"
        if asst.mem.conn.execute("SELECT 1 FROM kv WHERE k=?", (khoa,)).fetchone():
            continue
        nguoi = nguoi_tai.get(d["dia_diem"], [])
        for u in nguoi:
            ra.append(Delivery(u["user_id"], f"Đơn mua {d['so_don']} trễ {d['tre_nhat']} ngày, hàng đã về chưa?",
                               card=_the(asst, d, ten, True), skill=SKILL, ref=ref))
        if nguoi:
            asst.mem.conn.execute("INSERT OR REPLACE INTO kv(k,v) VALUES(?,?)", (khoa, "1"))
    asst.mem.conn.commit()
    return ra


def tom_tat_cho_brief(asst: Any, user: dict[str, Any]) -> list[Delivery]:
    """Mot dong trong brief sang, chi khi co don qua han. Khong the, nguoi can chi tiet thi hoi tiep."""
    dong = dong_qua_han(asst, _pham_vi(user))
    if not dong:
        return []
    don = gom_theo_don(dong)
    return [Delivery(user["user_id"], f"Đơn mua quá ngày nhận dự kiến mà chưa nhận: {len(don)} đơn, trễ nhất "
                                      f"{don[0]['tre_nhat']} ngày ({don[0]['so_don']}). Gõ \"PO nào quá hạn\" để xem từng đơn.",
                     skill=SKILL)]


def on_xac_nhan(asst: Any, user: dict[str, Any], ref: str, da_ve: bool) -> list[Delivery]:
    """Cua hang tra loi hang da ve hay chua. Ghi lai va bao Supply Chain, khong dung toi chung tu."""
    uid = user["user_id"]
    so_don, _, dia_diem = ref.partition("|")
    if user.get("role") not in VAI_TRO_TAI_DIEM or user.get("store_code") != dia_diem:
        return [Delivery(uid, "Chỉ người nhận hàng tại địa điểm của đơn này xác nhận được.", skill=SKILL)]
    if _xac_nhan(asst, ref):
        return [Delivery(uid, "Đơn này đã có người xác nhận rồi.", skill=SKILL, ref=ref)]
    cau = "hàng đã về nhưng chưa nhập vào BC" if da_ve else "hàng chưa về"
    ten_nguoi = (user.get("display_name") or uid).split(" (")[0]
    try:
        from zoneinfo import ZoneInfo
        luc = asst.mem.now().astimezone(ZoneInfo("Asia/Ho_Chi_Minh")).strftime("%H:%M %d/%m")
    except Exception:                                  # may Windows thieu goi tzdata
        luc = asst.mem.now().astimezone().strftime("%H:%M %d/%m")
    asst.mem.conn.execute("INSERT OR REPLACE INTO kv(k,v) VALUES(?,?)",
                          (f"po_xac_nhan:{ref}", json.dumps({"nguoi": ten_nguoi, "cau": cau, "luc": luc, "da_ve": da_ve},
                                                            ensure_ascii=False)))
    asst.mem.conn.commit()

    dong = [r for r in dong_qua_han(asst, dia_diem) if r.get("documentNo") == so_don]
    tong = sum(float(r["outstandingQuantity"]) for r in dong)
    viec = ("Cần người post Receive trên Purchase Order để tồn trong BC khớp thực tế." if da_ve
            else "Người mua cần hỏi nhà cung cấp ngày giao mới, hoặc dời Expected Receipt Date.")
    bao = f"{ten_nguoi} ({_ten_diem(dia_diem)}) báo đơn {so_don}: {cau}. Còn {fmt_qty(tong)} đơn vị chưa nhận trên {len(dong)} dòng. {viec}"
    out = [Delivery(uid, f"Đã ghi nhận: {cau}. Tôi đã báo Supply Chain.", skill=SKILL, ref=ref)]
    for sc in asst.mem.users_by_role("supply_chain"):
        out.append(Delivery(sc["user_id"], bao, skill=SKILL, ref=ref))
    return out
