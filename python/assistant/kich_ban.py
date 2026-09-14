"""Bien cau hoi ngoai kich ban thanh kich ban da duyet.

Vi sao co file nay. Khach se noi: 80% cau nguoi dung hoi la ngoai kich ban, vay lam sao de he
thong gioi dan len. Dung hoi ngay 13/09/2026. Cau tra loi KHONG phai huan luyen lai model:

  1. Moi cau di qua planner deu duoc ghi lai: cau hoi, chuoi tool model da dung, cau tra loi,
     so token, va nguoi hoi danh gia dung hay sai.
  2. Nguoi quan tri chon mot cau da tra loi dung roi bam "Luu thanh kich ban". Code (khong phai
     model) lap mau: moi con so trong cau tra loi phai truy duoc ve mot o trong ket qua tool,
     mat hang va dia diem thanh bien. Con so nao khong truy duoc thi bao ra, vi do la so model
     tu tinh, dung la thu da bat duoc model dem sai hai lan.
  3. Lan sau co cau tuong tu, du khac mat hang hay cua hang, tro ly chay lai chuoi tool tren du
     lieu hien tai, dien so vao mau. Khong goi model, khong ton token.

Buoc kiem truoc khi chay kich ban, vi nhan nham thi tro ly tra loi sai ma giong van rat chac:
  - cau moi phai co du bien kich ban can (mat hang, dia diem), tra bang ten chinh xac, khong doan;
  - tu con lai cua cau phai giong cau mau tu `NGUONG` tro len;
  - moi o so trong mau phai doc ra duoc gia tri tren du lieu moi. Thieu mot o la bo kich ban,
    tra cau hoi ve cho model.
Nguoi hoi van thay ro cau tra loi den tu kich ban nao va co nut hoi lai bang model.

Luu tren dia (`runs/kich-ban.sqlite`), khong nam trong bo nho tro ly, vi bo nho do bi dung moi
lan doi nguon du lieu con kich ban la tai san cua Marou.
"""
from __future__ import annotations

import json
import logging
import os
import re
import sqlite3
import unicodedata
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

log = logging.getLogger(__name__)

DUONG = Path(os.getenv("AGENT_LOG_DIR", "./runs")) / "kich-ban.sqlite"
NGUONG = 0.6                      # do giong toi thieu giua phan chu con lai cua hai cau
BUOC_KHONG_MANG = ("draft_proposal",)   # so luong trong de xuat gan voi mat hang cu, khong dung lai

SCHEMA = """
CREATE TABLE IF NOT EXISTS cau_hoi (
  id INTEGER PRIMARY KEY AUTOINCREMENT, ts TEXT, user_id TEXT, vai_tro TEXT, cau TEXT, khoa TEXT,
  nguon TEXT, kich_ban_id TEXT, ref TEXT, buoc TEXT, tra_loi TEXT, bien TEXT,
  token INTEGER DEFAULT 0, usd REAL DEFAULT 0, danh_gia TEXT DEFAULT ''
);
CREATE TABLE IF NOT EXISTS kich_ban (
  id TEXT PRIMARY KEY, ts TEXT, tu_cau_hoi INTEGER, duyet_boi TEXT, cau_mau TEXT, khoa TEXT,
  bien_can TEXT, buoc TEXT, slots TEXT, tra_loi_mau TEXT, cau_hoi_lai TEXT, canh_bao TEXT,
  token_goc INTEGER DEFAULT 0, usd_goc REAL DEFAULT 0, bat INTEGER DEFAULT 1
);
"""

# Tu lich su trong cau hoi, bo di khi so khop, khong mang nghia cua cau hoi.
_TU_DEM = {"nhe", "nha", "a", "oi", "giup", "voi", "em", "anh", "chi", "ban", "minh", "toi", "vay",
           "ha", "ah", "the", "thi", "la", "co", "khong", "ko", "k", "cho", "di", "roi", "nay", "do"}


@contextmanager
def _ket_noi():
    """Mo, ghi, dong. Khong giu ket noi lau vi uvicorn --reload va OneDrive deu hay khoa file."""
    DUONG.parent.mkdir(parents=True, exist_ok=True)
    c = sqlite3.connect(str(DUONG), check_same_thread=False)
    c.row_factory = sqlite3.Row
    try:
        c.executescript(SCHEMA)
        yield c
        c.commit()
    finally:
        c.close()


def _bay_gio() -> str:
    return datetime.now(timezone.utc).isoformat()


def chuan(t: str) -> str:
    """Bo dau, chu thuong, chi giu chu va so cach nhau mot dau cach."""
    t = unicodedata.normalize("NFD", (t or "").lower()).replace("đ", "d")
    t = "".join(ch for ch in t if unicodedata.category(ch) != "Mn")
    return re.sub(r"[^a-z0-9]+", " ", t).strip()


# ---------------------------------------------------------------- bien trong cau
def tim_bien(text: str, gw: Any) -> dict[str, str]:
    """Mat hang va dia diem nhac trong cau. Chi nhan khi ten hoac ma xuat hien NGUYEN VAN.

    Khong dung so khop mo o day: find_item cho "Croissant plain" va "Croissant chocolate" diem
    gan nhau, ma kich ban chay nham mat hang thi con so tra ve van dep va sai hoan toan."""
    from .core import STORE_LABEL

    t = f" {chuan(text)} "
    bien: dict[str, str] = {}
    tot: tuple[int, dict[str, str]] | None = None
    for it in gw.items():
        for ten in (it["description"], it["itemNo"]):
            c = chuan(ten)
            if c and f" {c} " in t and (tot is None or len(c) > tot[0]):
                tot = (len(c), it)
    if tot:
        bien["item_no"], bien["item_desc"] = tot[1]["itemNo"], tot[1]["description"]
    for ma, nhan in STORE_LABEL.items():
        if f" {chuan(ma)} " in t or f" {chuan(nhan)} " in t:
            bien["location"], bien["location_name"] = ma, nhan
            break
    return bien


def khoa(text: str, bien: dict[str, str]) -> str:
    """Phan chu con lai sau khi bo mat hang, dia diem, so va tu dem. Dung de so hai cau."""
    bo = set()
    for k in ("item_desc", "item_no", "location", "location_name"):
        bo.update(chuan(bien.get(k, "")).split())
    tu = [w for w in chuan(text).split() if w not in bo and w not in _TU_DEM and not w.isdigit()]
    return " ".join(sorted(set(tu)))


def _giong(a: str, b: str) -> float:
    x, y = set(a.split()), set(b.split())
    return len(x & y) / len(x | y) if x and y else 0.0


# ---------------------------------------------------------------- ghi cau hoi
def ghi_cau_hoi(user: dict[str, Any], cau: str, nguon: str, gw: Any, buoc: list[dict[str, Any]] | None = None,
                tra_loi: str = "", ref: str = "", token: int = 0, usd: float = 0.0, kich_ban_id: str = "") -> int:
    """`nguon`: model (planner live), ban_ghi (replay dung san), kich_ban (kich ban da duyet),
    khong_tra_loi (khong duong nao tra loi duoc, day la khoang trong phai lap)."""
    bien = tim_bien(cau, gw)
    with _ket_noi() as c:
        cur = c.execute(
            "INSERT INTO cau_hoi(ts,user_id,vai_tro,cau,khoa,nguon,kich_ban_id,ref,buoc,tra_loi,bien,token,usd) "
            "VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?)",
            (_bay_gio(), user["user_id"], user.get("role", ""), cau, khoa(cau, bien), nguon, kich_ban_id, ref,
             json.dumps(buoc or [], ensure_ascii=False, default=str)[:400000], tra_loi,
             json.dumps(bien, ensure_ascii=False), int(token), float(usd)))
        return int(cur.lastrowid)


def danh_gia(ref: str, dung: bool) -> dict[str, Any] | None:
    with _ket_noi() as c:
        c.execute("UPDATE cau_hoi SET danh_gia=? WHERE ref=?", ("dung" if dung else "sai", ref))
        r = c.execute("SELECT * FROM cau_hoi WHERE ref=?", (ref,)).fetchone()
    return dict(r) if r else None


def cau_hoi(id_: int) -> dict[str, Any] | None:
    with _ket_noi() as c:
        r = c.execute("SELECT * FROM cau_hoi WHERE id=?", (id_,)).fetchone()
    if not r:
        return None
    d = dict(r)
    d["buoc"], d["bien"] = json.loads(d["buoc"] or "[]"), json.loads(d["bien"] or "{}")
    return d


def nhom_cau_hoi(gioi_han: int = 50) -> list[dict[str, Any]]:
    """Gom cau giong nhau (cung khoa), xep theo so lan hoi roi tien da ton.

    Nhom da co kich ban van hien, de nguoi quan tri thay kich ban dang do cho bao nhieu cau."""
    with _ket_noi() as c:
        rows = [dict(r) for r in c.execute("SELECT id,ts,user_id,vai_tro,cau,khoa,nguon,kich_ban_id,ref,tra_loi,"
                                           "token,usd,danh_gia FROM cau_hoi ORDER BY id DESC")]
    nhom: dict[str, dict[str, Any]] = {}
    for r in rows:
        g = nhom.setdefault(r["khoa"] or r["cau"], {
            "khoa": r["khoa"], "cau_moi_nhat": r["cau"], "ts": r["ts"], "so_lan": 0, "goi_model": 0,
            "chay_kich_ban": 0, "khong_tra_loi": 0, "token": 0, "usd": 0.0, "dung": 0, "sai": 0,
            "luu_duoc_tu": None, "kich_ban_id": ""})
        g["so_lan"] += 1
        g["token"] += r["token"] or 0
        g["usd"] += r["usd"] or 0
        g["goi_model"] += r["nguon"] == "model"
        g["chay_kich_ban"] += r["nguon"] == "kich_ban"
        g["khong_tra_loi"] += r["nguon"] == "khong_tra_loi"
        g["dung"] += r["danh_gia"] == "dung"
        g["sai"] += r["danh_gia"] == "sai"
        g["kich_ban_id"] = g["kich_ban_id"] or r["kich_ban_id"] or ""
        # Chi lap kich ban tu cau model da tra loi va khong ai bao la sai. Uu tien cau duoc bao dung.
        if r["nguon"] == "model" and r["tra_loi"] and r["danh_gia"] != "sai":
            if g["luu_duoc_tu"] is None or (r["danh_gia"] == "dung" and g.get("_dg") != "dung"):
                g["luu_duoc_tu"], g["_dg"] = r["id"], r["danh_gia"]
    for g in nhom.values():
        g.pop("_dg", None)
        g["usd"] = round(g["usd"], 6)
    return sorted(nhom.values(), key=lambda g: (-g["so_lan"], -g["usd"]))[:gioi_han]


# ---------------------------------------------------------------- lap mau tu mot cau tra loi
_ID = ("itemNo", "locationCode", "store", "location", "lot", "lotNo")
_KET_LUAN = re.compile(r"(nhất|nên |đề xuất|khuyến nghị|cao hơn|thấp hơn|nhanh hơn|chậm hơn|nhiều hơn|ít hơn|"
                       r"vì vậy|do đó|kết luận|rủi ro)", re.I)
_SO = re.compile(r"(?<![\w/:.,\-])(\d{1,3}(?:\.\d{3})+(?:,\d+)?|\d+(?:[.,]\d+)?)(?![\w/])(?![.,]\d)")


def _chi_muc(obj: Any, path: str = "") -> list[tuple[str, float]]:
    """Moi o so trong ket qua tool, kem duong dan `_resolve` doc lai duoc.

    Phan tu danh sach co ma (itemNo, locationCode...) thi dat duong dan theo ma chu khong theo
    vi tri, vi lan chay sau thu tu dong co the doi."""
    noi = (lambda seg: f"{path}.{seg}" if path else seg)
    if isinstance(obj, bool) or obj is None:
        return []
    if isinstance(obj, (int, float)):
        return [(path, float(obj))]
    ra: list[tuple[str, float]] = []
    if isinstance(obj, dict):
        for k, v in obj.items():
            ra += _chi_muc(v, noi(k))
    elif isinstance(obj, list):
        for i, x in enumerate(obj):
            seg = str(i)
            if isinstance(x, dict):
                k = next((k for k in _ID if isinstance(x.get(k), str) and x.get(k) and "." not in x[k]), None)
                if k:
                    seg = f"#{k}={x[k]}"
            ra += _chi_muc(x, noi(seg))
        dicts = [x for x in obj if isinstance(x, dict)]
        so_truong = {k for d in dicts for k, v in d.items() if isinstance(v, (int, float)) and not isinstance(v, bool)}
        for k in sorted(so_truong):
            ra.append((noi(f"@sum:{k}"), sum(float(d.get(k) or 0) for d in dicts)))
        ra.append((noi("@len"), float(len(obj))))
    return ra


def _doc_so(s: str) -> tuple[float, int]:
    """So kieu Viet (1.234,5) va kieu model hay viet (3.5). Tra ve gia tri va so chu so thap phan."""
    if re.fullmatch(r"\d{1,3}(\.\d{3})+(,\d+)?", s):
        phan = s.split(",")
        return float(s.replace(".", "").replace(",", ".")), len(phan[1]) if len(phan) > 1 else 0
    if "," in s or "." in s:
        nguyen, _, le = re.split(r"([.,])", s, maxsplit=1)
        return float(f"{nguyen}.{le}"), len(le)
    return float(s), 0


def _bang(v: float, x: float, le: int) -> bool:
    return abs(round(v, le) - x) < 1e-9


_MA_DD = re.compile(r"\b([SW]\d{4})\b")


def so_sai_dia_diem(tra_loi: str, buoc: list[dict[str, Any]]) -> list[str]:
    """Con so model viet ngay sau mot ma dia diem ma khong co o ket qua nao cua DUNG dia diem do.

    Kiem theo gia tri thoi thi khong du. Chay that ngay 14/09/2026: model viet "S0010: 0.6 chai/ngay, ton 2 chai" trong khi
    list_stock cua S0010 tra ve rong; so 2 co that nhung la ton cua S0005. Nen moi so phai co mot o bang no, va o do phai
    thuoc dia diem duoc nhac gan nhat phia truoc trong cung dong: duong dan co `=S0010`, hoac buoc tra cuu goi rieng cho
    S0010 (tham so hay truong chu cua ket qua dang dict) va duong dan khong gan dia diem nao khac."""
    hang_so = {float(v) for s in buoc for v in (s.get("args") or {}).values()
               if isinstance(v, (int, float)) and not isinstance(v, bool)}
    # Cau hoi ve mot mat hang thi o cua mat hang khac trong cung danh sach (lotCount cua mon khac bang 2) khong tinh.
    hang = {s["result"]["itemNo"] for s in buoc if s.get("tool") == "find_item" and isinstance(s.get("result"), dict)
            and s["result"].get("itemNo")}
    o: list[tuple[str, float, set[str]]] = []
    for s in buoc:
        res = s.get("result")
        ma_buoc = {m for v in (s.get("args") or {}).values() if isinstance(v, str) for m in _MA_DD.findall(v)}
        if isinstance(res, dict):
            ma_buoc |= {m for v in res.values() if isinstance(v, str) for m in _MA_DD.findall(v)}
        for p, v in _chi_muc(res):
            mon = re.findall(r"#itemNo=([^.#]+)", p)
            if hang and mon and mon[-1] not in hang:
                continue
            o.append((p, v, ma_buoc))
    canh_bao: list[str] = []
    for dong in tra_loi.splitlines():
        for m in _SO.finditer(dong):
            truoc = _MA_DD.findall(dong[:m.start()])
            if not truoc:
                continue
            ma = truoc[-1]
            gia_tri, le = _doc_so(m.group(1))
            if le == 0 and gia_tri in hang_so:
                continue
            bang = [(p, mb) for p, v, mb in o if _bang(v, gia_tri, le)]
            dung = [p for p, mb in bang if f"={ma}" in p or (not _MA_DD.search(p) and ma in mb)]
            if not dung:
                ly_do = "không có trong dữ liệu đã tra" if not bang else f"dữ liệu đã tra của {ma} không có số này"
                canh_bao.append(f"“{m.group(1)}” ở dòng “{dong.strip()[:90]}”: {ly_do}")
    return list(dict.fromkeys(canh_bao))


def lap_mau(tra_loi: str, buoc: list[dict[str, Any]], bien: dict[str, str], ma_hang: set[str]) -> dict[str, Any]:
    """Doi mot cau tra loi cua model thanh mau co bien.

    Tra ve buoc da tham so hoa, slots, tra_loi_mau, canh_bao (con so khong truy duoc) va bien_can."""
    # 1. Buoc: bo buoc ghi de xuat, doi gia tri cua bien thanh cho trong.
    buoc_moi, bo_buoc = [], []
    thay = {v: f"{{{k}}}" for k, v in bien.items() if k in ("item_no", "location") and v}
    for s in buoc:
        if s["tool"] in BUOC_KHONG_MANG:
            bo_buoc.append(s["tool"])
            continue
        args = {}
        for k, v in (s.get("args") or {}).items():
            if isinstance(v, str) and v in thay:
                v = thay[v]
            elif k == "text" and isinstance(v, str) and bien.get("item_desc") and chuan(bien["item_desc"]) in chuan(v):
                v = "{item_desc}"
            args[k] = v
        buoc_moi.append({"tool": s["tool"], "args": args, "why": s.get("why", ""), "result": s.get("result")})

    # 2. Chi muc so tren ket qua cua cac buoc giu lai. Duong dan co ma cua bien thi doi thanh bien.
    # So nguoi hoi hoac model tu dat lam tham so (90 ngay, nhom 5 cua hang) la hang so, khong
    # phai ket qua. Bat no vao mot o ket qua tinh co bang 90 thi lan sau cau tra loi doi so ngay.
    hang_so = {float(v) for s in buoc_moi for v in s["args"].values()
               if isinstance(v, (int, float)) and not isinstance(v, bool)}
    chi_muc: list[tuple[int, str, float]] = []
    for i, s in enumerate(buoc_moi):
        for p, v in _chi_muc(s["result"]):
            for gia_tri, cho in thay.items():
                p = p.replace(f"={gia_tri}", f"={cho}")
            chi_muc.append((i, p, v))

    # 3. Danh dau ten mat hang va dia diem truoc, de ma hang 33323 hay S0001 khong bi coi la so.
    MOC = "\x00{}\x00"
    van = tra_loi
    for k in ("item_desc", "location_name", "item_no", "location"):
        if bien.get(k):
            van = re.sub(rf"(?<![\w]){re.escape(bien[k])}(?![\w])", MOC.format(k), van)

    slots: dict[str, dict[str, Any]] = {}
    canh_bao: list[str] = []
    manh: list[str] = []
    cuoi = 0
    for m in _SO.finditer(van):
        chu = m.group(1)
        manh.append(van[cuoi:m.start()].replace("{", "{{").replace("}", "}}"))
        cuoi = m.end()
        gia_tri, le = _doc_so(chu)
        if chu in ma_hang or (le == 0 and gia_tri in hang_so):
            manh.append(chu)
            continue
        ung = [(i, p) for i, p, v in chi_muc if _bang(v, gia_tri, le)]
        if not ung:
            # Khong truy duoc: model tu tinh ra. Giu nguyen chu nhung bao ra cho nguoi duyet.
            dau, cuoi_cau = max(0, m.start() - 50), min(len(van), m.end() + 30)
            doan = re.sub(r"\x00(\w+)\x00", lambda x: bien.get(x.group(1), ""), van[dau:cuoi_cau])
            canh_bao.append(f"“{chu}” trong “…{doan}…”")
            manh.append(chu)
            continue
        # Nhieu o cung gia tri (hai cua hang cung 9,1 ngay) thi chon o co ma dia diem hoac mat hang
        # duoc nhac GAN NHAT phia truoc con so. Chay that ngay 13/09/2026: thieu buoc nay, so cua
        # S0010 bi gan vao o cua S0005 vi hai o bang nhau, doi mat hang la ra so sai.
        truoc_so = van[:m.start()]

        def gan_nhat(p: str) -> int:
            vi_tri = -1
            for ma in re.findall(r"#\w+=([^.#]+)", p):
                that = next((v for v, cho in thay.items() if cho == ma), ma)
                vi_tri = max(vi_tri, truoc_so.rfind(that))
                if ma in thay.values():
                    k = ma.strip("{}")
                    vi_tri = max(vi_tri, truoc_so.rfind(MOC.format(k)))
            return vi_tri

        # Uu tien: ma gan nhat phia truoc, roi duong dan theo bien, roi theo ma, roi ngan nhat.
        ung.sort(key=lambda ip: (-gan_nhat(ip[1]), "{" not in ip[1], "#" not in ip[1], len(ip[1])))
        ten = f"s{len(slots) + 1}"
        slots[ten] = {"step": ung[0][0], "path": ung[0][1], "round": min(le, 1)}
        manh.append(f"{{{ten}}}")
    manh.append(van[cuoi:].replace("{", "{{").replace("}", "}}"))
    mau = "".join(manh)
    for k in ("item_desc", "location_name", "item_no", "location"):
        mau = mau.replace(MOC.format(k).replace("{", "{{").replace("}", "}}"), f"{{{k}}}")

    can = sorted({k for k in bien if f"{{{k}}}" in mau or any(f"{{{k}}}" in json.dumps(s["args"], ensure_ascii=False)
                                                               or any(f"{{{k}}}" in sl["path"] for sl in slots.values())
                                                               for s in buoc_moi)})
    # Kich ban dien lai SO, khong suy luan lai. Cau so sanh hay khuyen nghi viet cho mat hang goc se
    # lap nguyen chu cho mat hang khac. Chay that ngay 13/09/2026: "Dia diem ban cham nhat la S0005"
    # duoc giu nguyen khi hoi sang Croissant. Bao ra de nguoi duyet sua hoac bo cau do.
    for cau in re.split(r"(?<=[.!?])\s+|\n+", mau):
        if _KET_LUAN.search(cau) and cau.strip():
            hien = re.sub(r"\{(s\d+)\}", "…", cau).replace("{item_desc}", bien.get("item_desc", "")).strip()
            canh_bao.append(f"Câu kết luận viết cố định, lặp lại nguyên văn cho mặt hàng khác: “{hien}”")
    if bo_buoc:
        canh_bao.append("Kịch bản không mang theo bước soạn đề xuất: số lượng trong đề xuất gắn với mặt hàng cũ. "
                        "Muốn ghi đề xuất thì hỏi lại bằng model.")
    return {"buoc": [{k: v for k, v in s.items() if k != "result"} for s in buoc_moi], "slots": slots,
            "tra_loi_mau": mau, "canh_bao": canh_bao, "bien_can": can}


def xem_truoc(id_cau_hoi: int, gw: Any) -> dict[str, Any]:
    ch = cau_hoi(id_cau_hoi)
    if not ch:
        raise KeyError("Không còn câu hỏi này.")
    if ch["nguon"] != "model" or not ch["tra_loi"]:
        raise ValueError("Chỉ lưu được câu do model tự dựng chuỗi tra cứu và đã có câu trả lời.")
    ma_hang = {i["itemNo"] for i in gw.items()}
    mau = lap_mau(ch["tra_loi"], ch["buoc"], ch["bien"], ma_hang)
    return {"cau_hoi": {k: ch[k] for k in ("id", "cau", "tra_loi", "token", "usd", "danh_gia")}, **mau}


def luu(id_cau_hoi: int, gw: Any, duyet_boi: str, tra_loi_mau: str | None = None) -> dict[str, Any]:
    """Lap mau lai tu dau roi luu. `tra_loi_mau` la ban nguoi quan tri da sua tay (neu co).

    Ban sua tay van phai giu dung cac cho trong {s1}, {item_desc}...: chen them cho trong nao
    khong co trong slots thi chay se hong, nen chan ngay o day."""
    ch = cau_hoi(id_cau_hoi)
    mau = xem_truoc(id_cau_hoi, gw)
    if tra_loi_mau is not None and tra_loi_mau.strip():
        hop_le = set(mau["slots"]) | set(ch["bien"])
        la = {m for m in re.findall(r"(?<!\{)\{(\w+)\}(?!\})", tra_loi_mau) if m not in hop_le}
        if la:
            raise ValueError("Mẫu có chỗ trống không đọc được từ dữ liệu: " + ", ".join(sorted(la)))
        mau["tra_loi_mau"] = tra_loi_mau
    hoi_lai = next((s["args"].get("question", "") for s in mau["buoc"] if s["tool"] == "ask_human"), "")
    with _ket_noi() as c:
        n = c.execute("SELECT COUNT(*) FROM kich_ban").fetchone()[0]
        kb_id = f"K-{n + 1:03d}"
        c.execute(
            "INSERT INTO kich_ban(id,ts,tu_cau_hoi,duyet_boi,cau_mau,khoa,bien_can,buoc,slots,tra_loi_mau,cau_hoi_lai,"
            "canh_bao,token_goc,usd_goc,bat) VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,1)",
            (kb_id, _bay_gio(), id_cau_hoi, duyet_boi, ch["cau"], khoa(ch["cau"], ch["bien"]),
             json.dumps(mau["bien_can"]), json.dumps(mau["buoc"], ensure_ascii=False),
             json.dumps(mau["slots"], ensure_ascii=False), mau["tra_loi_mau"], hoi_lai,
             json.dumps(mau["canh_bao"], ensure_ascii=False), ch["token"], ch["usd"]))
        c.execute("UPDATE cau_hoi SET kich_ban_id=? WHERE id=?", (kb_id, id_cau_hoi))
    return kich_ban(kb_id)


def kich_ban(kb_id: str) -> dict[str, Any] | None:
    with _ket_noi() as c:
        r = c.execute("SELECT * FROM kich_ban WHERE id=?", (kb_id,)).fetchone()
    return _mo_kb(dict(r)) if r else None


def _mo_kb(d: dict[str, Any]) -> dict[str, Any]:
    for k in ("bien_can", "buoc", "slots", "canh_bao"):
        d[k] = json.loads(d[k] or ("{}" if k == "slots" else "[]"))
    return d


def danh_sach(chi_bat: bool = False) -> list[dict[str, Any]]:
    with _ket_noi() as c:
        rows = [_mo_kb(dict(r)) for r in c.execute("SELECT * FROM kich_ban" + (" WHERE bat=1" if chi_bat else "")
                                                   + " ORDER BY id")]
        dem = {r["kich_ban_id"]: dict(r) for r in c.execute(
            "SELECT kich_ban_id, SUM(nguon='kich_ban') chay, SUM(danh_gia='dung' AND nguon='kich_ban') dung, "
            "SUM(danh_gia='sai' AND nguon='kich_ban') sai FROM cau_hoi WHERE kich_ban_id<>'' GROUP BY kich_ban_id")}
    for kb in rows:
        d = dem.get(kb["id"], {})
        kb["so_lan_chay"], kb["dung"], kb["sai"] = int(d.get("chay") or 0), int(d.get("dung") or 0), int(d.get("sai") or 0)
        kb["token_tiet_kiem"] = kb["so_lan_chay"] * (kb["token_goc"] or 0)
        kb["usd_tiet_kiem"] = round(kb["so_lan_chay"] * (kb["usd_goc"] or 0), 6)
    return rows


def bat_tat(kb_id: str, bat: bool) -> None:
    with _ket_noi() as c:
        c.execute("UPDATE kich_ban SET bat=? WHERE id=?", (1 if bat else 0, kb_id))


# ---------------------------------------------------------------- khop va chay
def khop(text: str, gw: Any) -> tuple[dict[str, Any], dict[str, str], float] | None:
    ds = danh_sach(chi_bat=True)
    if not ds:
        return None
    bien = tim_bien(text, gw)
    k = khoa(text, bien)
    tot = None
    for kb in ds:
        if not set(kb["bien_can"]) <= set(bien):
            continue
        s = _giong(k, kb["khoa"])
        if s >= NGUONG and (tot is None or s > tot[2]):
            tot = (kb, bien, s)
    return tot


def chay(kb: dict[str, Any], asst: Any, user: dict[str, Any], bien: dict[str, str]):
    """Chay lai chuoi tool tren du lieu hien tai va dien so vao mau. Tra ve (Plan, ly do).

    Plan None nghia la bo kich ban: mot o so khong doc ra duoc tren du lieu moi (vi du mat hang
    nay khong co o dia diem do). Luc do cau hoi ve lai model thay vi tra loi thieu."""
    from . import toolbox
    from .planner import Plan, Step, _fmt, _resolve

    try:
        steps = []
        for s in kb["buoc"]:
            args = {k: (v.format(**bien) if isinstance(v, str) else v) for k, v in s["args"].items()}
            steps.append(Step(s["tool"], args, s.get("why", ""), toolbox.run_tool(asst, user, s["tool"], args)))
        vals: dict[str, str] = {}
        for ten, spec in kb["slots"].items():
            raw = _resolve(steps[spec["step"]].result, spec["path"].format(**bien))
            if raw is None or isinstance(raw, (list, dict)):
                return None, f"không đọc được ô {ten} trên dữ liệu hiện tại"
            le = spec.get("round") or 0
            vals[ten] = _fmt(round(float(raw), le) if le else round(float(raw)))
        answer = kb["tra_loi_mau"].format(**bien, **vals)
        hoi = (kb.get("cau_hoi_lai") or "").format(**bien) if kb.get("cau_hoi_lai") else ""
    except (KeyError, IndexError, ValueError, TypeError) as exc:
        log.warning("Kich ban %s khong chay duoc: %s", kb["id"], exc)
        return None, f"lỗi khi chạy: {exc}"
    return Plan("kich_ban", kb["id"], steps, answer, hoi, []), ""
