"""Kenh web demo: mo phong Teams. Mot trang, chon 'toi la ai', chat, bam nut tren the.
Chay:  uvicorn assistant.channels.web:app --reload --port 8088   (hoac python -m assistant.channels.web)
Che do BC/LLM lay tu .env nhu bc_agent.
"""
from __future__ import annotations

import logging
import uuid
from pathlib import Path
from typing import Any

from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import FileResponse, JSONResponse, Response
from pydantic import BaseModel

from bc_agent.bc_client import BCError
from bc_agent.config import settings

from .. import budget as budget_mod
from .. import caidat
from .. import cong_ty as cong_ty_mod

from ..core import Assistant, la_quan_tri
from ..memory import Memory

log = logging.getLogger("web")
STATIC = Path(__file__).resolve().parent.parent / "static"


def _client(live: bool | None = None, cong_ty: str = ""):
    """`live=None` nghia la theo BC_MODE trong .env. Nut tren giao dien truyen True hoac False.
    `cong_ty` la ten company; mock khong phan biet company, moi company doc cung bo fixtures."""
    if settings.bc_live if live is None else live:
        from dataclasses import replace

        from bc_agent.bc_client import BCClient
        s = settings if not cong_ty or cong_ty == settings.bc_company_name else replace(
            settings, bc_company_name=cong_ty, bc_company_id="")
        return BCClient(s)
    from bc_agent.mock_client import MockBCClient
    return MockBCClient()


app = FastAPI(title="Marou Ops Assistant (demo)")


class _CongTyMiddleware:
    """Doc company cua request tu header `X-Cong-Ty` (giao dien tu gan) hoac tham so `cong_ty`, dat vao
    ContextVar `cong_ty.hien_tai`. ASGI thuan, khong dung BaseHTTPMiddleware vi cai do lam mat ContextVar."""

    def __init__(self, app_):
        self.app = app_

    async def __call__(self, scope, receive, send):
        if scope.get("type") != "http":
            return await self.app(scope, receive, send)
        from urllib.parse import parse_qs, unquote
        ten = ""
        for k, v in scope.get("headers") or []:
            if k.decode("latin-1").lower() == "x-cong-ty":
                ten = unquote(v.decode("latin-1")).strip()
        if not ten:
            ten = (parse_qs(scope.get("query_string", b"").decode()).get("cong_ty") or [""])[0].strip()
        token = cong_ty_mod.hien_tai.set(ten if ten in cong_ty_mod.danh_sach(settings) else "")
        try:
            await self.app(scope, receive, send)
        finally:
            cong_ty_mod.hien_tai.reset(token)


app.add_middleware(_CongTyMiddleware)


@app.exception_handler(BCError)
def _loi_bc(request, exc: BCError):
    """BC tu choi thi tra ve cau cua BC, dung de thanh 500 tron.

    Truoc day mot loi 403 cua BC lam ca duong tra ve 500, giao dien nuot im va man hinh trong
    tron: bam Brief khong thay gi, bam Ghi de xuat vao BC khong thay gi. Ngay 13/09/2026 mat mot
    vong moi tim ra la LS Central doi quyen doc `LSC Retail Setup` khi ghi vao bang cua extension."""
    log.warning("BC tu choi: %s", exc)
    return JSONResponse(status_code=502, content={"loi": str(exc)[:600]})
# bc_live_override: None la theo .env, True/False la nguoi dung da bam nut tren giao dien.
# tro_ly: moi company mot tro ly, dung khi co request dau tien cua company do (dung mot tro ly tren BC that
# mat vai chuc giay vi phai chot baseline).
import threading
import time

state: dict[str, Any] = {"tro_ly": {}, "bc_live_override": None}
_khoa_tro_ly = threading.Lock()


def bc_is_live() -> bool:
    ov = state.get("bc_live_override")
    return settings.bc_live if ov is None else bool(ov)


def cac_cong_ty() -> list[str]:
    return cong_ty_mod.danh_sach(settings)


def _bo_nho(live: bool, ten: str) -> Memory:
    """Bo nho tro ly nam tren dia, moi company mot file: runs/bo-nho-<company>.sqlite.

    Truoc 16/09/2026 la Memory(":memory:"): moi lan `--reload` sau khi sua file Python hay khoi dong lai la mat hop thu, de xuat da
    nap, viec theo doi chung tu huy (A3) va cac doan AI da soan. Dung yeu cau chuyen xuong dia.

    CHE DO MO PHONG VAN GIU TRONG RAM. `MockBCClient` nap lai fixtures moi lan dung client moi, nen de xuat da ghi vao mock bien mat
    theo, trong khi bo nho tren dia thi con: bam Duyet tren the cu se tra 500 vi `bc_id` khong con trong mock (bat duoc 16/09/2026
    khi chup anh cho slide). Du lieu mo phong la de demo, khong can nho qua lan khoi dong lai.
    Duoi pytest cung dung ":memory:" de khong ghi vao runs/ that."""
    import re as _re
    import sys
    if not live or "pytest" in sys.modules:
        return Memory(":memory:")
    duong = Path(settings.log_dir) / f"bo-nho-{_re.sub(r'[^A-Za-z0-9_-]+', '_', ten) or 'mac-dinh'}.sqlite"
    duong.parent.mkdir(parents=True, exist_ok=True)
    return Memory(duong)


def _tro_ly_cua(ten: str) -> Assistant:
    # Test gan san mot tro ly vao state["asst"] thi moi company dung tro ly do.
    if state.get("asst") is not None:
        return state["asst"]
    with _khoa_tro_ly:
        a = state["tro_ly"].get(ten)
        if a is None:
            live = bc_is_live()
            a = Assistant(_client(live, ten), _bo_nho(live, ten), cong_ty=ten)
            state["tro_ly"][ten] = a
        return a


def _dung_lai_tro_ly(live: bool, xoa_bo_nho: bool = False) -> None:
    """Doi nguon du lieu hoac reset: bo moi tro ly, dung lai company mac dinh ngay de bao loi som neu hong.
    `xoa_bo_nho` (nut Reset): xoa file bo nho cua nguon do de bat dau sach; doi nguon thi giu, moi nguon co file rieng."""
    with _khoa_tro_ly:
        cu = state["tro_ly"]
        state["tro_ly"] = {}
        state.pop("asst", None)
    if xoa_bo_nho:
        for a in cu.values():
            try:
                a.mem.conn.close()
            except Exception:
                pass
        for f in Path(settings.log_dir).glob("bo-nho-*.sqlite"):
            try:
                f.unlink()
            except OSError as exc:
                log.warning("Khong xoa duoc %s: %s", f, exc)
    ten = cac_cong_ty()[0]
    a = Assistant(_client(live, ten), _bo_nho(live, ten), cong_ty=ten)
    with _khoa_tro_ly:
        state["tro_ly"][ten] = a
    with _khoa_tt:
        _tt_cham.clear()
    import sys
    if "pytest" not in sys.modules:
        threading.Thread(target=_lam_nong, name="lam-nong", daemon=True).start()


# Giao dien goi `/api/state` moi 2 giay, va cho nay dem hai bang ket qua moi lan. Tren BC that
# hai lenh do mat khoang 3,4 giay, tuc lau hon ca chu ky poll: cac vong poll chong len nhau va
# ca man hinh cham theo. Ca hai lenh gio di qua ban nho cua gateway (`BCGateway.doc`), dung chung
# voi man hinh Suc khoe ton kho va voi brief. Bat duoc ngay 13/09/2026.
def _dem_dong_ket_qua(live: bool) -> dict[str, Any]:
    a = asst()
    try:
        n_health = len(a.gw.doc("inventoryHealthLines", [], top=5000))
        n_sugg = len(a.gw.doc("replenishmentSuggestions", [], top=5000))
        return {"so_dong_ket_qua": n_health, "so_dong_de_xuat": n_sugg,
                "san_sang": n_health > 0, "as_of": a.gw.today().isoformat()}
    except Exception as exc:
        return {"so_dong_ket_qua": 0, "so_dong_de_xuat": 0, "san_sang": False, "loi": str(exc)[:300]}


def quen_dem() -> None:
    """Bo ban nho de lan doc sau lay so moi tu BC, o moi company dang chay."""
    for a in list(state["tro_ly"].values()):
        a.gw.quen_nho()
    with _khoa_tt:
        _tt_cham.clear()


# Phan CHAM cua /api/state (dem hai bang ket qua, doc de xuat tu BC) giu trong mot ban chup theo company va lam moi
# o luong nen. Vong poll 2 giay tra ban chup ngay, khong doi BC. Do toi 16/09/2026: sau mot phut ngoi khong, ban nho
# het han va MOT lan poll mat 16-17 giay (goi_y_ls doc LS 12 giay, de xuat 3 giay), nen doi vai la man hinh trong
# 30-45 giay truoc khi man hinh chao hien ra. Dung bat duoc: "doi role la phai doi 30-45s".
_tt_cham: dict[str, dict[str, Any]] = {}
_dang_lam_moi: set[str] = set()
_khoa_tt = threading.Lock()
TT_CHAM_TUOI_GIAY = 8


def _lam_moi_tt_cham(ten: str) -> None:
    try:
        cong_ty_mod.hien_tai.set(ten)
        a = _tro_ly_cua(ten)
        dem = _dem_dong_ket_qua(bc_is_live())
        de_xuat = a.de_xuat_gop()
        with _khoa_tt:
            _tt_cham[ten] = {"luc": time.time(), "dem": dem, "proposals": de_xuat}
    except Exception as exc:                        # luong nen khong duoc lam chet may chu
        log.warning("Lam moi trang thai cham cho %s hong: %s", ten, exc)
    finally:
        with _khoa_tt:
            _dang_lam_moi.discard(ten)


def _tt_cham_cua(ten: str, dong_bo: bool = False) -> dict[str, Any] | None:
    """Ban chup cua company `ten`; cu qua thi kich luong nen lam moi. `dong_bo` (mock, test) thi tinh ngay tai cho."""
    with _khoa_tt:
        c = _tt_cham.get(ten)
        cu = c is None or time.time() - c["luc"] > TT_CHAM_TUOI_GIAY
        kich = cu and ten not in _dang_lam_moi
        if kich:
            _dang_lam_moi.add(ten)
    if kich:
        if dong_bo or c is None and not bc_is_live():
            _lam_moi_tt_cham(ten)
            with _khoa_tt:
                return _tt_cham.get(ten)
        threading.Thread(target=_lam_moi_tt_cham, args=(ten,), name=f"tt-cham-{ten}", daemon=True).start()
    return c


_giu_am_dang_chay = False


def _doc_truoc(ten: str) -> None:
    """Doc truoc cac bang nang ma cau hoi demo can (CTKM, suc khoe ton kho, de xuat LS, lich su ban, du bao, ILE 28 ngay)."""
    from ..skills import khuyen_mai
    a = _tro_ly_cua(ten)
    if a.gw.is_mock:
        return
    cong_ty_mod.hien_tai.set(ten)
    for viec in (lambda: a.gw.doc("inventoryHealthLines", [], top=5000), lambda: a.gw.doc("replenishmentSuggestions", [], top=5000),
                 lambda: khuyen_mai.doc(a.gw), lambda: a.gw.doc("forecastAccuracies", [], top=5000),
                 lambda: a.gw.ile_cua_so(28), lambda: a.gw.de_xuat_dang_co()):
        try:
            viec()
        except Exception as exc:
            log.warning("Doc truoc %s hong: %s", ten, exc)


def _lam_nong() -> None:
    """Dung san tro ly va ban chup cho moi company ngay khi may chu len, de cu bam dau tien khong phai doi BC. Sau do giu am cac
    bang nang: doc lai moi 12 phut (ban nho cua chung song 15 phut), de cau hoi trong buoi demo khong gap lan doc nguoi."""
    import time
    for ten in cac_cong_ty():
        try:
            _lam_moi_tt_cham(ten)
        except Exception as exc:
            log.warning("Lam nong %s hong: %s", ten, exc)
    global _giu_am_dang_chay
    if _giu_am_dang_chay:               # Reset cung goi ham nay; chi mot vong giu am
        for ten in cac_cong_ty():
            try:
                _doc_truoc(ten)
            except Exception as exc:
                log.warning("Giu am %s hong: %s", ten, exc)
        return
    _giu_am_dang_chay = True
    while True:
        for ten in cac_cong_ty():
            try:
                _doc_truoc(ten)
            except Exception as exc:
                log.warning("Giu am %s hong: %s", ten, exc)
        time.sleep(720)


def bc_status() -> dict[str, Any]:
    """Che do dang chay va bang chung cho no. Khong noi "dang chay that" ma khong dem duoc dong nao.

    `nguon` la cai nguoi xem can biet: mock thi la fixtures, live thi la ten environment va company.
    `san_sang` false nghia la dang tro vao BC that nhung hai bang ket qua cua AL con rong, tuc
    chua ai bam Run Inventory Health.
    """
    live = bc_is_live()
    ten = cong_ty_dang_chon()
    out: dict[str, Any] = {
        "live": live,
        "theo_env": state.get("bc_live_override") is None,
        "bc_mode_env": settings.bc_mode,
        "cong_ty": ten, "cong_ty_nhan": cong_ty_mod.nhan(ten, "day_du"),
        "nguon": (f"{settings.bc_environment} / {ten}" if live
                  else f"fixtures trong python/bc_agent/fixtures ({cong_ty_mod.nhan(ten)})"),
    }
    out.update(_dem_dong_ket_qua(live))
    return out


def cong_ty_dang_chon(user: str | None = None) -> str:
    """Company cua request: header/tham so ma giao dien gui, neu hop le va nguoi dung duoc lam o do.
    Khong co thi company mac dinh cua vai nguoi dung, cuoi cung la company dau tien."""
    co = cac_cong_ty()
    ten = cong_ty_mod.hien_tai.get()
    if user:
        from ..core import DEMO_USERS
        u = next((x for x in DEMO_USERS if x["user_id"] == user), None)
        duoc = cong_ty_mod.cua_vai(u, co)
        if ten not in duoc:
            ten = duoc[0]
    return ten if ten in co else co[0]


def asst(user: str | None = None) -> Assistant:
    """Tro ly cua company dang chon. Dat luon ContextVar de link BC trong the tro dung company."""
    ten = cong_ty_dang_chon(user)
    cong_ty_mod.hien_tai.set(ten)
    return _tro_ly_cua(ten)


def _moi_tro_ly() -> list[Assistant]:
    """Cong tac AI, tran chi phi, policy la cai dat chung: ap cho moi company dang chay."""
    if state.get("asst") is not None:
        return [state["asst"]]
    if not state["tro_ly"]:
        _tro_ly_cua(cac_cong_ty()[0])
    return list(state["tro_ly"].values())


# ---------------------------------------------------------------- nhac post nhan hang (chat + email)
class NhacIn(BaseModel):
    user: str = ""
    gui_lai: bool = False


@app.post("/api/nhac-post")
def nhac_post_ngay(x: NhacIn):
    """Chay mot vong nhac post cho company dang chon, giong lich chay nen moi sang. Xem skills/nhac_post.py."""
    from ..skills import nhac_post
    a = asst(x.user or None)
    u = a.mem.user(x.user) if x.user else None
    out = a._deliver(nhac_post.nhac(a, u, bat_buoc=x.gui_lai))
    return {"delivered": [d.user_id for d in out]}


@app.get("/api/thu-di")
def thu_di(user: str = ""):
    """Email tro ly da soan: gui that, chi luu file, hay loi. Chi quan tri xem."""
    from .. import thu_dien_tu as td
    _chan_neu_khong_phai_quan_tri(user)
    return {"kenh": td.kenh(), "nguoi_nhan": td.nguoi_nhan_mac_dinh(), "thu": td.gan_day(50)}


class QuetIn(BaseModel):
    user: str = ""
    chay_lai: bool = False


@app.post("/api/quet-uc2")
def quet_uc2_ngay(x: QuetIn):
    """UC2 A2: chay mot vong quet sang cho company dang chon (de xuat huy lo het han, phuong an lo can date, brief, nhac, theo doi).
    Giong lich chay nen moi sang. Xem skills/uc2_quet.py."""
    from ..skills import uc2_quet
    a = asst(x.user or None)
    u = a.mem.user(x.user) if x.user else None
    out = a._deliver(uc2_quet.quet(a, u, bat_buoc=x.chay_lai))
    return {"delivered": [d.user_id for d in out]}


class ICIn(BaseModel):
    user: str = ""
    doc_no: str = ""
    chay_lai: bool = False


@app.post("/api/ic-nhan-hang")
def ic_nhan_hang_quet(x: ICIn):
    """Intercompany phia nguoi mua: bao don doi tac vua xuat kho, nhac don qua ngay chua post nhan, va ghi de xuat
    PostReceipt cho nhung don do. Xem skills/ic_nhan_hang.py."""
    from ..skills import ic_nhan_hang
    a = asst(x.user or None)
    u = a.mem.user(x.user) if x.user else None
    out = a._deliver(ic_nhan_hang.quet(a, u, bat_buoc=x.chay_lai))
    return {"delivered": [d.user_id for d in out]}


@app.post("/api/demo/marou-xuat-kho")
def demo_marou_xuat_kho(x: ICIn):
    """Chi demo: bam thay nguoi kho Marou, post xuat kho cho don ban ma Intercompany da tao tu don mua `doc_no`.
    Tren he that day la thao tac cua nguoi kho ben Marou trong BC; tro ly khong bao gio goi duong nay."""
    from ..skills import ic_nhan_hang
    a = asst(x.user or None)
    # Khong truyen so don thi lay don dau tien doi tac chua xuat kho, de nguoi demo khong phai nho so don.
    doc_no, doi_tac = x.doc_no, ""
    # Don MOI NHAT truoc: buoc 15 phai xuat dung don Ice cream vua gui o buoc 8, khong phai don du phong tao tu truoc.
    for d in sorted(a.gw.ic_giao_hang(ic_nhan_hang.NHA_CUNG_CAP_IC), key=lambda d: d.get("purchaseOrder") or "", reverse=True):
        if doc_no and d["purchaseOrder"] != doc_no:
            continue
        if not doc_no and ((d.get("shipment") or {}).get("posted") or float(d.get("outstanding") or 0) <= 0):
            continue
        doc_no, doi_tac = d["purchaseOrder"], d.get("partnerCompany") or ""
        break
    if not doc_no:
        raise HTTPException(status_code=400, detail="Không còn đơn mua liên công ty nào đang chờ bên bán xuất kho. "
                            "Kiểm lại bước 8: Hùng (Dakao) duyệt đặt mua rồi bấm Gửi đơn sang Marou trên thẻ Đã tạo Purchase Order.")
    x.doc_no = doc_no
    try:
        # Ngay post lay theo dong ho tro ly (co nut +24 gio), de buoc "bao trong ngay" chay duoc vao bat ky ngay demo nao.
        kq = a.gw.post_giao_hang_doi_tac(x.doc_no, doi_tac, a.mem.now().astimezone().strftime("%Y-%m-%d"))
    except NotImplementedError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e
    a.gw.quen_nho()
    u = a.mem.user(x.user) if x.user else None
    # Khong bat_buoc: chi bao don vua xuat. QA dem 16/09: bat_buoc gui lai ca HO106202 da bao o buoc truoc ("email cho 2 don").
    out = a._deliver(ic_nhan_hang.quet(a, u, bat_buoc=False))
    return {"ket_qua": kq, "delivered": [d.user_id for d in out]}


@app.post("/api/demo/post-huy")
def demo_post_huy(x: QuetIn):
    """Chi mo phong: gia lap ke toan da post cac dong Item Journal huy, de xem vong A3 khep lai. Tren BC that thi post trong Item Journal."""
    a = asst(x.user or None)
    try:
        da = a.gw.gia_lap_post_journal()
    except NotImplementedError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e
    out = a.run_followups()
    return {"da_post": da, "delivered": [d.user_id for d in out]}


def _cac_lich() -> list[tuple[str, str, Any]]:
    """(ten viec, gio HH:MM, ham(asst) -> list[Delivery]). Gio rong = tat viec do."""
    from ..skills import nhac_post, uc2_quet
    return [("nhac_post", (settings.nhac_post_gio or "").strip(), nhac_post.nhac),
            ("quet_uc2", (settings.quet_uc2_gio or "").strip(), uc2_quet.quet)]


def _chay_lich_nhac() -> None:
    """Moi phut xem da toi gio cua tung viec nen chua (NHAC_POST_GIO, QUET_UC2_GIO); toi gio thi moi company chay mot lan trong ngay.
    Ngay da chay ghi vao runs/lich-nhac.json theo khoa "<company>|<viec>" de khoi dong lai trong ngay khong chay lai."""
    import json as _json
    import time
    from datetime import datetime

    duong = Path(settings.log_dir) / "lich-nhac.json"
    while True:
        try:
            bay_gio = datetime.now()
            hom_nay = bay_gio.strftime("%Y-%m-%d")
            for viec, gio, ham in _cac_lich():
                if not gio or bay_gio.strftime("%H:%M") < gio:
                    continue
                da = _json.loads(duong.read_text(encoding="utf-8")) if duong.exists() else {}
                if da.get("tam_dung"):
                    # Khoa "tam_dung": true trong runs/lich-nhac.json thi khong chay lich nao. Dat toi 16/09/2026 cho buoi demo
                    # 17/09: quet sang tu ghi toi 10 de xuat huy moi company va gui email, ma khoi dong lai may chu sau 07:30
                    # la no chay ngay. Xoa khoa (hoac dat false) la lich chay lai binh thuong.
                    continue
                for ten in cac_cong_ty():
                    khoa = ten if viec == "nhac_post" else f"{ten}|{viec}"     # khoa cu cua nhac post giu nguyen
                    if da.get(khoa) == hom_nay:
                        continue
                    a = _tro_ly_cua(ten)
                    cong_ty_mod.hien_tai.set(ten)
                    try:
                        out = a._deliver(ham(a))
                        log.info("Lich %s %s: %d tin", viec, ten, len(out))
                    except Exception as exc:
                        log.warning("Lich %s %s hong: %s", viec, ten, exc)
                    da[khoa] = hom_nay
                    duong.parent.mkdir(parents=True, exist_ok=True)
                    duong.write_text(_json.dumps(da), encoding="utf-8")
        except Exception as exc:                    # lich chay nen khong duoc lam chet may chu
            log.warning("Lich chay nen hong: %s", exc)
        time.sleep(60)


IC_QUET_GIAY = 60


def _quet_xuat_kho_nen() -> None:
    """Moi phut doc phieu giao hang ben doi tac; don nao moi xuat thi bao ngay (chat + email). Khong bi khoa "tam_dung",
    vi viec nay chi bao, khong ghi gi vao BC. Don da bao roi (kv) thi khong bao lai."""
    import time
    from ..skills import ic_nhan_hang
    # Moc theo tien trinh: don da xuat truoc lan quet dau khong bao tu dong (nut Kiem hang van bao duoc). Khong co moc thi
    # sau Reset buoi sang (bo nho sach), lich nen bao lai don xuat tu toi hom truoc truoc khi nguoi demo bam Kiem hang.
    moc: dict[str, set[str]] = {}
    while True:
        for ten in cac_cong_ty():
            try:
                a = _tro_ly_cua(ten)
                if a.gw.is_mock:
                    continue
                cong_ty_mod.hien_tai.set(ten)
                if ten not in moc:
                    moc[ten] = ic_nhan_hang.don_trong_ngay(a)
                    continue
                out = a._deliver(ic_nhan_hang.bao_xuat_moi(a, bo_qua=moc[ten]))
                if out:
                    log.info("Quet xuat kho %s: %d tin", ten, len(out))
            except Exception as exc:
                log.warning("Quet xuat kho %s hong: %s", ten, exc)
        time.sleep(IC_QUET_GIAY)


@app.on_event("startup")
def _bat_lich_nhac() -> None:
    import sys
    if "pytest" in sys.modules:
        return
    threading.Thread(target=_lam_nong, name="lam-nong", daemon=True).start()
    threading.Thread(target=_quet_xuat_kho_nen, name="quet-xuat-kho", daemon=True).start()
    if not any(gio for _, gio, _ in _cac_lich()):
        return
    threading.Thread(target=_chay_lich_nhac, name="lich-chay-nen", daemon=True).start()


@app.get("/api/cong-ty")
def cong_ty_cua_nguoi(user: str = ""):
    """Company dang chay, company nguoi nay duoc lam, va company dang chon. Nguoi chi co mot company thi
    giao dien khong hien nut doi."""
    from ..core import DEMO_USERS
    co = cac_cong_ty()
    u = next((x for x in DEMO_USERS if x["user_id"] == user), None)
    duoc = cong_ty_mod.cua_vai(u, co)
    return {"tat_ca": cong_ty_mod.mo_ta(co), "duoc": cong_ty_mod.mo_ta(duoc),
            "dang_chon": cong_ty_dang_chon(user) if user else co[0]}


class MessageIn(BaseModel):
    user: str
    text: str
    reply_to: int | None = None       # id cua tin ma nguoi dung bam Tra loi


class ActionIn(BaseModel):
    user: str
    verb: str
    ref: str
    payload: dict[str, Any] = {}


class ClockIn(BaseModel):
    hours: float = 24


class AutonomyIn(BaseModel):
    shadow: bool | None = None
    kill: bool | None = None


@app.get("/")
def index():
    # no-store: sua index.html xong, F5 la thay ngay. Khong co dong nay thi Edge va Chrome
    # giu ban cu trong cache va nguoi xem tuong la chua sua gi.
    return FileResponse(STATIC / "index.html",
                        headers={"Cache-Control": "no-store, must-revalidate"})


# Linh vat: mot ban day du cho man hinh chao, ba cai dau cho tung trang thai cua tro ly.
ANH_LINH_VAT = {"mascot.png", "mascot-san-sang.png", "mascot-suy-nghi.png", "mascot-hoan-tat.png"}


@app.get("/{ten}.png")
def anh_linh_vat(ten: str):
    """Anh trang tri. Cache duoc vi chung khong bao gio doi."""
    if f"{ten}.png" not in ANH_LINH_VAT:
        raise HTTPException(status_code=404, detail="Khong co anh nay")
    return FileResponse(STATIC / f"{ten}.png", media_type="image/png",
                        headers={"Cache-Control": "public, max-age=86400"})


@app.get("/api/users")
def users():
    return asst().mem.users()


@app.get("/api/goi-y")
def goi_y_theo_vai(user: str):
    """Prompt mau cua nguoi dung theo vai tro (assistant/goi_y.py): the tren man hinh chao."""
    from assistant import goi_y
    return goi_y.cho_nguoi_dung(asst(user).mem.user(user))


@app.get("/api/inbox")
def inbox(user: str, after: int = 0):
    return asst(user).mem.inbox(user, after)


@app.post("/api/message")
def message(m: MessageIn):
    out = asst(m.user).handle_message(m.user, m.text, reply_to=m.reply_to)
    return {"delivered": [d.user_id for d in out]}


@app.post("/api/action")
def action(a: ActionIn):
    """`con_mo` = de xuat van con cho nguoi duyet, tuc hanh dong vua roi khong doi duoc gi.

    Giao dien tat nut ngay khi bam de khong ai bam hai lan. Neu tro ly tu choi (so luong vuot
    ton, khong du quyen, thieu ly do) thi cai the phai song lai, neu khong nguoi duyet ngoi
    nhin nut mo ma khong sua duoc gi. Dung mot co chung cho moi ly do tu choi, thay vi doan
    theo cau tra loi."""
    tl = asst(a.user)
    out = tl.handle_action(a.user, a.verb, a.ref, a.payload)
    prop = tl.mem.proposal(a.ref)
    return {"delivered": [d.user_id for d in out],
            "con_mo": bool(prop and prop["status"] == "Proposed")}


@app.post("/api/brief")
def brief(m: MessageIn):
    out = asst(m.user).morning_brief(m.user)
    return {"delivered": [d.user_id for d in out]}


@app.post("/api/brief_all")
def brief_all():
    n = 0
    for u in asst().mem.users():
        n += len(asst().morning_brief(u["user_id"]))
    return {"delivered": n}


@app.post("/api/clock")
def clock(c: ClockIn):
    now = asst().mem.advance_clock(c.hours)
    out = asst().run_followups()
    return {"now": now.isoformat(), "followups_sent": len(out)}


@app.post("/api/followups")
def followups():
    out = asst().run_followups()
    return {"followups_sent": len(out)}


@app.get("/api/policy")
def policy():
    a = asst()
    return {"shadow": a.policy.shadow, "kill_switch": a.policy.kill_switch,
            "auto_today": a.policy.auto_today, "daily_auto_cap": a.policy.daily_auto_cap,
            "rules": a.policy.summary()}


@app.post("/api/autonomy")
def autonomy(a_in: AutonomyIn):
    a = asst()
    if a_in.shadow is not None:
        a.policy.shadow = a_in.shadow
    if a_in.kill is not None:
        a.policy.kill_switch = a_in.kill
    return {"shadow": a.policy.shadow, "kill_switch": a.policy.kill_switch}


@app.post("/api/self_review")
def self_review(m: MessageIn):
    from ..skills import review
    a = asst(m.user)
    out = review.run_self_review(a, a.mem.user(m.user))
    a._deliver(out)
    return {"delivered": len(out)}


@app.get("/api/uc2/summary")
def uc2_summary():
    from .. import uc2
    return uc2.summary(asst())


@app.get("/api/uc2/lines")
def uc2_lines(tier: str = ""):
    from .. import uc2
    return uc2.lines(asst(), tier)


@app.get("/api/uc2/trace")
def uc2_trace(line_id: str):
    from .. import uc2
    try:
        return uc2.trace(asst(), line_id)
    except Exception as e:
        raise HTTPException(status_code=404, detail=str(e)) from e


@app.get("/api/uc2/giai-thich")
def uc2_giai_thich(line_id: str):
    """S2: mot doan loi thuong ve lo, model viet tu dung con so cua trang Chi tiet lo; tat AI thi code ghep mau."""
    from ..skills import uc2_tom_tat
    try:
        return uc2_tom_tat.giai_thich_lo(asst(), line_id)
    except Exception as e:
        raise HTTPException(status_code=404, detail=str(e)) from e


@app.get("/api/uc2/phuong-an")
def uc2_phuong_an(line_id: str):
    """D4: bang phuong an cho lo can date (code tinh) cong loi khuyen (model chon, hoac mau)."""
    from ..skills import uc2_hanh_dong
    try:
        kq = uc2_hanh_dong.goi_y(asst(), line_id)
    except Exception as e:
        raise HTTPException(status_code=404, detail=str(e)) from e
    kq["phan_tich"] = {k: v for k, v in kq["phan_tich"].items() if not k.startswith("_")}
    return kq


@app.get("/api/uc2/bat-thuong")
def uc2_bat_thuong(noi: str = ""):
    """D3: tin hieu bat thuong 28 ngay (code quet) cong nhan xet (model xep thu tu)."""
    from ..skills import uc2_bat_thuong as m
    return m.goi_y(asst(), noi=noi)


@app.get("/api/uc2/nguyen-nhan-huy")
def uc2_nguyen_nhan_huy(item: str = "", noi: str = ""):
    """D2: nguyen nhan goc hang huy 90 ngay theo mat hang x cua hang."""
    from ..skills import uc2_nguyen_nhan as m
    return m.goi_y(asst(), item, noi)


@app.post("/api/bao-cao-huy")
def bao_cao_huy(x: QuetIn):
    """S3: soan va gui bao cao tuan hang huy (the + email)."""
    from ..skills import uc2_bao_cao_huy as m
    a = asst(x.user or None)
    u = a.mem.user(x.user) if x.user else None
    out = a._deliver(m.gui(a, u, bat_buoc=x.chay_lai))
    return {"delivered": [d.user_id for d in out]}


@app.get("/api/uc2/lo")
def uc2_lo(lot: str):
    """Hanh trinh cua mot lo tu Item Ledger Entry (UC2 traceability), dung cho trang Chi tiet lo."""
    from ..bc_link import link
    from ..skills import truy_xuat
    rows = asst().gw.ile_theo_lo(lot)
    h = truy_xuat.hanh_trinh(rows)
    h["moc"] = [{"date": d, "location": l, "type": t, "label": truy_xuat.TEN_LOAI.get(t, t), "qty": q} for d, l, t, q in h["moc"]]
    h["links"] = [{"label": "Item Ledger Entries của lô", "url": link("item_ledger_entries", {"Item No.": h["item"], "Lot No.": lot})},
                  {"label": "Lot No. Information", "url": link("lot_info_list", {"Item No.": h["item"], "Lot No.": lot})}]
    return h


@app.get("/api/uc1/tong-hop")
def uc1_tong_hop():
    """Man hinh Du bao (UC1): tong hop do chinh xac do BC tinh, danh sach ngoai le va moi dong."""
    from ..bc_link import link
    from ..skills import du_bao
    rows = asst().gw.doc("forecastAccuracies", [], top=5000)
    th = du_bao.tong_hop(rows) if rows else {"methods": [], "tong": {}, "tot_nhat": None, "theo_noi": {}, "theo_nhom": {},
                                              "ngoai_le": [], "so_cap": 0, "ky": (None, None)}
    th["rows"] = rows
    th["tenPP"] = du_bao.TEN_PP
    th["link"] = link("forecast_accuracy")
    return th


@app.get("/api/uc1/ngay")
def uc1_ngay(item: str, loc: str, method: str):
    from ..bc_link import link
    from ..skills import du_bao
    a = asst()
    rows = a.gw.doc("forecastDailies", [("itemNo", "eq", item), ("locationCode", "eq", loc), ("method", "eq", method)], top=400)
    toi, su_kien = du_bao.ngay_toi(a, item, loc)
    return {"rows": sorted(rows, key=lambda r: r["date"]), "toi": toi, "su_kien": su_kien,
            "link": link("forecast_daily", {"Item No.": item, "Location Code": loc, "Method": method}),
            "link_ls": link("ls_forecast_entries", {"Item No.": item, "Location Code": loc})}


@app.get("/api/uc3/scorecard")
def uc3_scorecard():
    """Man hinh Nha cung cap (UC3): scorecard do BC tinh va don mua qua han chua nhan."""
    from ..bc_link import link
    from ..skills import po_qua_han as pq
    a = asst()
    rows = a.gw.doc("supplierScorecards", [], top=500)
    don = pq.gom_theo_don(pq.dong_qua_han(a))
    return {"rows": rows, "link": link("supplier_scorecard"),
            "don": [{"so_don": d["so_don"], "dia_diem": d["dia_diem"], "nha_cung_cap": d["nha_cung_cap"], "tre": d["tre_nhat"],
                     "treo": d["tre_nhat"] > pq.NGAY_DON_TREO, "so_dong": len(d["dong"]),
                     "con": sum(float(r.get("outstandingQuantity") or 0) for r in d["dong"]),
                     "link": link("purchase_order", {"Document Type": "Order", "No.": d["so_don"]})} for d in don]}


@app.get("/api/uc2/readiness")
def uc2_readiness():
    from .. import uc2
    return uc2.readiness(asst())


@app.post("/api/kpi")
def kpi(m: MessageIn):
    from ..skills import kpi as k
    a = asst(m.user)
    a._deliver(k.run(a, a.mem.user(m.user)))
    return {"ok": True}


@app.get("/api/state")
def bc_state():
    a = asst()
    transfers = list(a.gw._transfers.values()) if a.gw.is_mock else []
    sp = a.budget.report()
    ten = cong_ty_dang_chon()
    live = bc_is_live()
    # Phan nhanh tinh tai cho; phan cham (dem bang ket qua, de xuat trong BC) lay tu ban chup, lam moi o luong nen.
    bc = {"live": live, "theo_env": state.get("bc_live_override") is None, "bc_mode_env": settings.bc_mode,
          "cong_ty": ten, "cong_ty_nhan": cong_ty_mod.nhan(ten, "day_du"),
          "nguon": (f"{settings.bc_environment} / {ten}" if live
                    else f"fixtures trong python/bc_agent/fixtures ({cong_ty_mod.nhan(ten)})")}
    c = _tt_cham_cua(ten, dong_bo=state.get("asst") is not None)
    if c:
        bc.update(c["dem"])
        de_xuat = c["proposals"]
    else:
        bc.update({"so_dong_ket_qua": 0, "so_dong_de_xuat": 0, "san_sang": True, "dang_tai": True})
        de_xuat = a.mem.proposals()
    return {"now": a.mem.now().isoformat(),
            "mode": {"bc": ("live" if live else "mock"), "llm": settings.llm_mode, "model": a.model_name,
                     "planner": a.planner.source, "replays": [s["id"] for s in getattr(a.planner, "scenarios", [])]},
            "bc": bc,
            "budget": {"spent_usd": round(sp.usd, 4), "spent_vnd": round(sp.usd * 26000), "calls": sp.calls,
                       "cap_usd": a.budget.cap, "by_purpose": {k: round(v, 4) for k, v in sp.by_purpose.items()},
                       "blocked": not a.budget.allow()},
            "policy": {"shadow": a.policy.shadow, "kill": a.policy.kill_switch, "auto_today": a.policy.auto_today,
                       "cap": a.policy.daily_auto_cap},
            "proposals": de_xuat, "followups": a.mem.followups(), "transfers": transfers,
            "tin_ra": a.mem.dem_tin_ra()}


class ModeIn(BaseModel):
    bc: str          # "mock", "live", hoac "env" de quay ve theo .env


@app.get("/api/mode")
def get_mode():
    return bc_status()


@app.post("/api/mode")
def set_mode(m: ModeIn):
    """Doi nguon du lieu ngay tren giao dien, khong phai sua .env roi khoi dong lai.

    Doi nguon thi phai dung tro ly moi: bo nho, baseline va so chi phi deu gan voi mot nguon.
    Neu dung khong len duoc BC that thi quay ve mock va noi ro loi, khong de tro ly chet.
    """
    want = (m.bc or "").strip().lower()
    if want not in ("mock", "live", "env"):
        raise HTTPException(status_code=400, detail="bc phai la mock, live hoac env")
    override = None if want == "env" else (want == "live")
    live = settings.bc_live if override is None else override
    truoc = state.get("bc_live_override")
    try:
        _dung_lai_tro_ly(live)
        state["bc_live_override"] = override
        quen_dem()
    except Exception as exc:
        state["bc_live_override"] = truoc
        _dung_lai_tro_ly(bc_is_live())
        st = bc_status()
        st["loi"] = f"Khong doi sang {want} duoc: {exc}"[:300]
        return st
    return bc_status()


# ---------------------------------------------------------------- trang Cai dat
def _chan_neu_khong_phai_quan_tri(user: str) -> None:
    """Bat tat model va doi tran chi phi la viec cua quan tri, khong phai cua quan ly cua hang.

    Chan o day chu khong chi an cai tab di, vi an tren giao dien thi ai go dung duong dan
    cung goi duoc."""
    if not la_quan_tri(asst().mem.user(user)):
        raise HTTPException(status_code=403,
                            detail="Trang Cài đặt AI chỉ dành cho vai trò quản trị hệ thống.")


def _ai_san_sang() -> tuple[bool, str]:
    """Co du duong den model khong. Tra ve (duoc, ly do neu khong duoc).

    Kiem truoc khi bat, de nut khong nem ra mot loi cua thu vien vao mat nguoi dung."""
    try:
        settings.validate_live_llm()
    except BaseException as exc:            # validate_live_llm nem SystemExit
        return False, str(exc)[:200]
    return True, ""


def _thong_tin_ai() -> dict[str, Any]:
    a = asst()
    duoc, ly_do = _ai_san_sang()
    ten = settings.live_model_name or "chua dat"
    return {"dang_bat": bool(a.ai_live and not a.budget.ai_off),
            "bat_duoc": duoc, "ly_do": ly_do,
            "nha_cung_cap": "Azure OpenAI" if settings.llm_provider == "azure" else "Anthropic Claude",
            "model": ten,
            "mac_dinh_khi_khoi_dong": settings.llm_mode == "live"}


@app.get("/api/usage")
def usage(user: str = ""):
    """Token da dung, tien uoc tinh, va trang thai cong tac AI.

    Tien la UOC TINH: token thi dem that tu response.usage, con don gia la bang gia cong bo
    chep vao `assistant/budget.py`. Hoa don that cua Azure van la con so cuoi cung.
    """
    _chan_neu_khong_phai_quan_tri(user)
    a = asst()
    b = a.budget
    hom_nay, cong_don = b.tong(b.today()), b.tong()
    ten_model = settings.live_model_name or "gpt-4.1-mini"
    vao, ra = budget_mod.PRICES.get(ten_model, budget_mod.DEFAULT_PRICE)
    con_lai = max(0.0, min(b.cap - hom_nay["usd"], b.total_cap - cong_don["usd"]))
    uoc = budget_mod.tokens_for_budget(ten_model, con_lai)
    return {
        "ai": _thong_tin_ai(),
        "hom_nay": hom_nay, "cong_don": cong_don,
        "ngay": b.today(),
        "tran": {"ngay_usd": b.cap, "cong_don_usd": b.total_cap,
                 "con_lai_ngay_usd": round(max(0.0, b.cap - hom_nay["usd"]), 6),
                 "con_lai_cong_don_usd": round(max(0.0, b.total_cap - cong_don["usd"]), 6),
                 "dang_chan": not b.allow()},
        "don_gia": {"model": ten_model, "vao_moi_trieu": vao, "ra_moi_trieu": ra,
                    "nguon": "Azure Retail Prices API, region eastus, 12/09/2026"},
        "uoc_tinh_con_chay_duoc": {"token": round(uoc["hon_hop"]),
                                   "gia_hon_hop_moi_trieu": round(uoc["gia_hon_hop_moi_trieu"], 4)},
        "dinh_tuyen": getattr(getattr(a, "nlu", None), "so", None) and a.nlu.so.tom_tat(),
        "theo_ngay": b.theo_ngay(14),
        "theo_viec": b.theo_viec(),
        "theo_model": b.theo_model(),
    }


class AiIn(BaseModel):
    on: bool
    user: str = ""


@app.post("/api/ai")
def set_ai(x: AiIn):
    """Bat tat AI ngay tren giao dien. Tat thi tro ly chay bang rule va template, khong goi
    model lan nao, va con so tren man hinh khong doi vi so do Business Central tinh."""
    _chan_neu_khong_phai_quan_tri(x.user)
    a = asst()
    if x.on:
        duoc, ly_do = _ai_san_sang()
        if not duoc:
            out = _thong_tin_ai()
            out["loi"] = ly_do
            return out
        try:
            for t in _moi_tro_ly():
                t.set_ai(True)
            caidat.ghi({"ai_bat": True})
        except BaseException as exc:
            for t in _moi_tro_ly():
                t.set_ai(False)
            out = _thong_tin_ai()
            out["loi"] = str(exc)[:300]
            return out
    else:
        for t in _moi_tro_ly():
            t.set_ai(False)
        caidat.ghi({"ai_bat": False})
    return _thong_tin_ai()


class TranIn(BaseModel):
    ngay_usd: float | None = None
    cong_don_usd: float | None = None
    user: str = ""


@app.post("/api/tran")
def set_tran(t: TranIn):
    """Doi tran chi phi ngay tai cho. Tran la cho chan that: cham tran thi moi cho goi model
    tu quay ve rule, khong bao loi."""
    _chan_neu_khong_phai_quan_tri(t.user)
    b = asst().budget
    luu: dict[str, Any] = {}
    for ten, khoa, gt in (("cap", "tran_ngay_usd", t.ngay_usd),
                          ("total_cap", "tran_cong_don_usd", t.cong_don_usd)):
        if gt is None:
            continue
        if gt < 0:
            raise HTTPException(status_code=400, detail="Tran khong duoc am")
        setattr(b, ten, float(gt))
        luu[khoa] = float(gt)
    if luu:
        caidat.ghi(luu)          # phai nho qua lan khoi dong lai, neu khong dat cung bang khong
        for tl in _moi_tro_ly():
            caidat.ap_vao(tl.budget, tl.policy)
    b._warned = b._warned_total = False
    return usage(t.user)


# ---------------------------------------------------------------- policy va cau chu
@app.get("/api/policy-setup")
def get_policy(user: str = ""):
    """Cac dong policy dang co hieu luc, cong hai cong tac chung va ba cau chu sua duoc."""
    _chan_neu_khong_phai_quan_tri(user)
    from ..policy import DEFAULT_RULES

    a = asst()
    # "Da sua" so voi ban goc, khong so voi "co dong trong file cai dat khong". Bam "Ve cau goc"
    # ghi mot chuoi rong de len nen dong do van con trong file, nhung noi dung thi da ve nhu cu.
    goc = {r.code: r for r in DEFAULT_RULES}
    rules = []
    for r in a.policy.rules:
        g = goc.get(r.code)
        rules.append({"code": r.code, "scenario": r.scenario, "action": r.action_type,
                      "mode": r.mode.value, "description": r.description,
                      "max_value_vnd": r.max_value_vnd,
                      "from_locations": list(r.from_locations or []),
                      "da_sua": bool(g) and (r.mode != g.mode or r.max_value_vnd != g.max_value_vnd)})
    cau_mau = [{"key": k, **v, "text": caidat.cau(k), "da_sua": caidat.cau(k) != v["text"]}
               for k, v in caidat.CAU_MAU_GOC.items()]
    return {"rules": rules, "shadow": a.policy.shadow, "tran_tu_lam": a.policy.daily_auto_cap,
            "da_tu_lam": a.policy.auto_today, "cau_mau": cau_mau,
            "mode_labels": {"auto": "Trợ lý tự làm", "approve": "Đưa người duyệt",
                            "block": "Không bao giờ làm"}}


class PolicyIn(BaseModel):
    user: str = ""
    code: str | None = None
    mode: str | None = None
    max_value_vnd: float | None = None
    bo_tran_gia_tri: bool = False        # dat lai thanh khong gioi han
    shadow: bool | None = None
    tran_tu_lam: int | None = None
    cau_mau_key: str | None = None
    cau_mau_text: str | None = None


@app.post("/api/policy-setup")
def set_policy(x: PolicyIn):
    """Sua mot dong policy, hai cong tac chung, hoac mot cau chu. Luu xuong dia roi ap ngay
    vao tro ly dang chay, khong phai khoi dong lai."""
    _chan_neu_khong_phai_quan_tri(x.user)
    a = asst()
    moi: dict[str, Any] = {}
    if x.code:
        if not any(r.code == x.code for r in a.policy.rules):
            raise HTTPException(status_code=404, detail=f"Khong co dong policy {x.code}")
        sua: dict[str, Any] = {}
        if x.mode:
            if x.mode not in ("auto", "approve", "block"):
                raise HTTPException(status_code=400, detail="mode phai la auto, approve hoac block")
            sua["mode"] = x.mode
        if x.bo_tran_gia_tri:
            sua["max_value_vnd"] = None
        elif x.max_value_vnd is not None:
            if x.max_value_vnd < 0:
                raise HTTPException(status_code=400, detail="Tran gia tri khong duoc am")
            sua["max_value_vnd"] = x.max_value_vnd
        if sua:
            moi["rules"] = {x.code: sua}
    if x.shadow is not None:
        moi["shadow"] = x.shadow
    if x.tran_tu_lam is not None:
        if x.tran_tu_lam < 0:
            raise HTTPException(status_code=400, detail="Tran tu lam khong duoc am")
        moi["tran_tu_lam"] = x.tran_tu_lam
    if x.cau_mau_key:
        if x.cau_mau_key not in caidat.CAU_MAU_GOC:
            raise HTTPException(status_code=404, detail=f"Khong co cau mau {x.cau_mau_key}")
        moi["cau_mau"] = {x.cau_mau_key: (x.cau_mau_text or "")}
    if moi:
        caidat.ghi(moi)
        for t in _moi_tro_ly():              # ap ngay cho moi company, khong doi khoi dong lai
            caidat.ap_vao(t.budget, t.policy)
    return get_policy(x.user)


@app.post("/api/lam-moi")
def lam_moi():
    """Bo ban nho roi doc lai tu BC. Dung ngay sau khi bam Run Inventory Health trong BC,
    de khong phai doi het mot phut."""
    quen_dem()
    return bc_status()


# ---------------------------------------------------------------- doan chat
@app.get("/api/doan-chat")
def cac_doan(user: str):
    return asst(user).mem.cac_doan(user)


class DoanIn(BaseModel):
    user: str
    conv_id: str | None = None       # None la mo mot doan moi


@app.post("/api/doan-chat")
def doi_doan(x: DoanIn):
    """Mo doan chat khac, hoac bat dau mot doan moi.

    Tin cu khong mat: chung van nam trong bang `messages`, chi la hop thu loc theo doan dang mo."""
    m = asst(x.user).mem
    if not m.user(x.user):
        raise HTTPException(status_code=404, detail="Khong nhan ra nguoi dung")
    if x.conv_id:
        m.mo_doan(x.user, x.conv_id)
    else:
        m.doan_moi(x.user)
    return {"doan": m.cac_doan(x.user)}


# ---------------------------------------------------------------- MCP server
@app.post("/mcp")
async def mcp_post(request: Request):
    """MCP Streamable HTTP. Xem `assistant/mcp_server.py`. Cung tro ly, cung bo nho voi giao dien web,
    nen de xuat ghi tu client MCP hien ngay trong hoi thoai cua nguoi duyet."""
    from .. import mcp_server as ms

    nguoi = ms.nguoi_goi(dict(request.headers), request.client.host if request.client else "")
    if nguoi is None:
        return JSONResponse(status_code=401, content={"jsonrpc": "2.0", "id": None,
                                                      "error": {"code": -32001, "message": "Thiếu hoặc sai khoá MCP."}})
    try:
        than = await request.json()
    except ValueError:
        return JSONResponse(status_code=400, content={"jsonrpc": "2.0", "id": None,
                                                      "error": {"code": -32700, "message": "Không đọc được JSON."}})
    tin = than if isinstance(than, list) else [than]
    tl = asst(nguoi)
    ra = [r for r in (ms.xu_ly(tl, nguoi, t) for t in tin if isinstance(t, dict)) if r is not None]
    if not ra:
        return Response(status_code=202)
    headers = {}
    if any(t.get("method") == "initialize" for t in tin if isinstance(t, dict)):
        headers["Mcp-Session-Id"] = uuid.uuid4().hex
    return JSONResponse(content=ra if isinstance(than, list) else ra[0], headers=headers)


@app.get("/mcp")
def mcp_get():
    # Khong mo luong SSE: khong co tool nao can day thong bao ve client.
    return Response(status_code=405)


@app.delete("/mcp")
def mcp_delete():
    return Response(status_code=200)


# ---------------------------------------------------------------- nhat ky va kich ban da duyet
@app.get("/api/nhat-ky")
def nhat_ky(user: str = ""):
    """Quyet dinh trong ngay, cau hoi ngoai rule va kich ban da duyet. Xem `assistant/nhat_ky.py`.

    Chi quan tri: man hinh nay hien cau hoi cua moi vai tro. Dung yeu cau ngay 13/09/2026."""
    from .. import nhat_ky as nk

    _chan_neu_khong_phai_quan_tri(user)
    return nk.tong_hop(asst())


class KichBanIn(BaseModel):
    user: str
    cau_hoi_id: int
    tra_loi_mau: str | None = None


@app.post("/api/kich-ban/xem-truoc")
def kich_ban_xem_truoc(x: KichBanIn):
    """Lap mau tu mot cau model da tra loi, chua luu. Bao ra con so nao khong truy duoc."""
    from .. import kich_ban as kb

    _chan_neu_khong_phai_quan_tri(x.user)
    try:
        return kb.xem_truoc(x.cau_hoi_id, asst().gw)
    except (KeyError, ValueError) as exc:
        raise HTTPException(status_code=400, detail=str(exc.args[0] if exc.args else exc))


@app.post("/api/kich-ban")
def kich_ban_luu(x: KichBanIn):
    from .. import kich_ban as kb

    _chan_neu_khong_phai_quan_tri(x.user)
    u = asst().mem.user(x.user) or {}
    try:
        return kb.luu(x.cau_hoi_id, asst().gw, u.get("display_name", x.user).split(" (")[0], x.tra_loi_mau)
    except (KeyError, ValueError) as exc:
        raise HTTPException(status_code=400, detail=str(exc.args[0] if exc.args else exc))


class BatKichBanIn(BaseModel):
    user: str
    id: str
    bat: bool


@app.post("/api/kich-ban/bat")
def kich_ban_bat(x: BatKichBanIn):
    from .. import kich_ban as kb

    _chan_neu_khong_phai_quan_tri(x.user)
    if not kb.kich_ban(x.id):
        raise HTTPException(status_code=404, detail="Không có kịch bản này.")
    kb.bat_tat(x.id, x.bat)
    return {"ok": True}


@app.post("/api/reset")
def reset():
    _dung_lai_tro_ly(bc_is_live(), xoa_bo_nho=True)
    quen_dem()
    return {"ok": True}


if __name__ == "__main__":
    import uvicorn

    logging.basicConfig(level=logging.INFO)
    uvicorn.run(app, host="0.0.0.0", port=8088)
