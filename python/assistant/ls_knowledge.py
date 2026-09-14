"""Doc nhat ky tinh cua LS Replenishment bang knowledge sinh tu source, cho moi tinh huong chu khong rieng du lieu mau.

Vi sao co file nay. Dung yeu cau ngay 14/09/2026: "toi can mot knowledge chung de nhieu tinh huong khac ban cung giai thich
duoc". Ban dau `skills/ls_giai_thich.py` viet tay cho mot nhanh (Average Usage, chuyen hang, khong lead time) va se giai
thich sai khi kho khong du hang, khi kieu tinh la Stock Levels, khi tham so den tu Data Profile...

Ba lop, deu nam trong `assistant/knowledge/ls_replen/`:
  mau_log.json   Label trong source LS da ghi vao Calc. Log Lines. Sinh bang `tools/ls_knowledge_build.py`, khong go tay.
  dien_giai.yaml Cau tieng Viet cho tung Label, buoc tinh, co lam doi so luong hay khong, doc o thu tuc nao.
  tham_so.yaml   Y nghia va noi sua cua tung tham so, khoa theo caption LS in trong log.

Cach doc mot dong log:
  1. Boc cac the dau dong "[Cross Dock] ", "[Replen. Planned Sales Dem.] ".
  2. Khop tron dong voi Label cu the nhat (nhieu chu co dinh nhat) truoc.
  3. Khong khop tron thi khop Label o DAU dong roi doc tiep phan con lai (LS hay ghep hai Label, vi du ton hieu dung
     cong cau "(Quantity on Purchase Order is not considered due to Replen. Setup)").
  4. Dong dang "A = x - B = y" (cac dong Replen. Data, Replen. Setup) tach thanh tung cap tham so.
  5. Khong khop gi thi tra ve nguyen van va danh dau `chua_nhan_dang`. Dem so dong nay la thuoc do do phu.
So trong cau lay nguyen tu log, khong tinh lai.
"""
from __future__ import annotations

import json
import re
from dataclasses import dataclass, field
from functools import lru_cache
from pathlib import Path
from typing import Any

import yaml

THU_MUC = Path(__file__).parent / "knowledge" / "ls_replen"
_NHOM_CO_DINH = 4        # Label co it hon so chu co dinh nay (vd "%1 = %2") khong dung de khop tron dong
_THE = re.compile(r"^\[([^\]]{2,60})\]\s*")
_NGAN = re.compile(r"^(?:\.\s*|,\s*|\s+-\s+|\s+)")


@dataclass
class Mau:
    id: str
    van_ban: str
    do_dac_trung: int
    tron: re.Pattern
    dau: re.Pattern
    thu_tu: list[str]          # "1","2"... theo thu tu nhom trong regex


@dataclass
class Buoc:
    """Mot dong log da doc."""
    goc: str
    id: str = ""                                   # id Label; "" neu la dong tham so hoac chua nhan dang
    loai: str = "mau"                              # mau | tham_so | chua_nhan_dang
    gia_tri: dict[str, str] = field(default_factory=dict)
    the: list[str] = field(default_factory=list)
    buoc: str = ""
    noi: str = ""
    doi_so: bool = False
    tham_so: list[str] = field(default_factory=list)
    phan_them: list["Buoc"] = field(default_factory=list)   # Label ghep o sau
    cap: list[tuple[str, str]] = field(default_factory=list)  # cap tham so "A = x"


def _regex(van_ban: str) -> tuple[str, list[str]]:
    """Doi Label thanh regex. %n lap lai dung backreference; khoang trang cuoi Label khong bat buoc."""
    # Bo khoang trang dau va cuoi: Label ghep nhu " (%1 is not considered due to %2)" di sau Label khac, phan dau da
    # duoc cat khi doc phan con lai.
    phan = [p for p in re.split(r"(%\d)", van_ban.strip()) if p != ""]
    # BC cat khoang trang cuoi Message Text, nen "Filter %2" voi %2 rong ve thanh "Filter". Khoang trang ngay truoc
    # tham so cuoi cung la khong bat buoc.
    khoang_cuoi_tuy_chon = len(phan) >= 2 and re.fullmatch(r"%\d", phan[-1]) is not None and phan[-2].endswith(" ")
    ra, thu_tu, da_co = "", [], set()
    for i, p in enumerate(phan):
        if re.fullmatch(r"%\d", p):
            n = p[1]
            if n in da_co:
                ra += f"(?P=p{n})"
            else:
                # Ngoac phai can bang mot cap: caption "Store Stock Cover Reqd (Days)" dung truoc "(7)" thi nhom lazy
                # thuong cat o ngoac dau tien va ra %3 = "Store Stock Cover Reqd ", %4 = "Days)(7".
                ra += f"(?P<p{n}>(?:[^()]|\\([^()]*\\))*?)"
                da_co.add(n)
                thu_tu.append(n)
        elif khoang_cuoi_tuy_chon and i == len(phan) - 2:
            ra += re.escape(p.rstrip()) + r"\s*"
        else:
            ra += re.escape(p)
    return ra, thu_tu


@lru_cache(maxsize=1)
def tai() -> dict[str, Any]:
    goc = json.loads((THU_MUC / "mau_log.json").read_text(encoding="utf-8"))
    dg = yaml.safe_load((THU_MUC / "dien_giai.yaml").read_text(encoding="utf-8"))
    ts = yaml.safe_load((THU_MUC / "tham_so.yaml").read_text(encoding="utf-8"))
    mau: list[Mau] = []
    for m in goc["mau"]:
        r, thu_tu = _regex(m["van_ban"])
        mau.append(Mau(m["id"], m["van_ban"], m["do_dac_trung"], re.compile(r"^" + r + r"\s*$", re.S),
                       re.compile(r"^" + r, re.S), thu_tu))
    return {"ls_central": goc.get("ls_central"), "mau": mau, "dien_giai": dg.get("mau", {}), "ten_buoc": dg.get("buoc", {}),
            "tham_so": ts.get("tham_so", {}), "nguon_tham_so": ts.get("nguon_tham_so", {})}


def ten_tham_so(caption: str) -> str:
    t = tai()["tham_so"].get((caption or "").strip())
    return t["ten"] if t and t.get("ten") else caption


def _dien(mau_cau: str, gia_tri: dict[str, str]) -> str:
    def thay(m: re.Match) -> str:
        v = gia_tri.get(m.group(1), "").strip()
        return ten_tham_so(v) if m.group(2) == "ten" else v
    kq = re.sub(r"\{(\d)(?:\|(ten))?\}", thay, mau_cau)
    # LS de Decision rong khi khong bo sung (enum gia tri " "), cau thanh "Quyết định: . ...": bo han cum do.
    return re.sub(r"^Quyết định:\s*\.\s*", "", kq)


def _gan_dien_giai(b: Buoc) -> Buoc:
    d = tai()["dien_giai"].get(b.id)
    if d:
        b.buoc = d.get("buoc", "")
        b.noi = _dien(d.get("noi", ""), b.gia_tri)
        b.doi_so = bool(d.get("doi_so"))
        b.tham_so = list(d.get("tham_so") or [])
    return b


_TACH_CAP = re.compile(r"(?:^|\s)-\s+(?=[A-Z][^=]{0,70}=)")


def _doc_cap(chu: str) -> list[tuple[str, str]]:
    """'Replen. Data - A = x - B = y' thanh [(A, x), (B, y)]. Caption bat dau bang chu hoa, gia tri co the rong."""
    than = re.sub(r"^(Replen\. Data|Replen\. Setup|Data Profile)\s*:?\s*", "", chu.strip())
    # Caption co san " - " ("Replenish as Item No - Method") thi khong duoc tach o do.
    giu = {k: k.replace(" - ", "␟") for k in tai()["tham_so"] if " - " in k}
    for k, v in giu.items():
        than = than.replace(k, v)
    ra = []
    for phan in (x.replace("␟", " - ") for x in _TACH_CAP.split(than)):
        if "=" not in phan:
            continue
        cap, _, gia_tri = phan.partition("=")
        cap = cap.strip()
        if not cap or not cap[0].isupper():
            continue
        ra.append((cap, gia_tri.strip().strip("'").rstrip(".").strip()))
    return ra


def _khop(chu: str, cho_phep_dau: bool = True) -> Buoc | None:
    k = tai()
    # Nhieu Label cung khop tron khi nhom lazy nuot ca phan con lai: "SSQ(%1) = ... Factor(%5)" khop ca dong co them
    # "- Effective Inventory(154)". Chon Label co tong phan bat duoc ngan nhat, tuc Label giai thich duoc nhieu chu nhat.
    tot, tot_do_dai = None, None
    for m in k["mau"]:
        if m.do_dac_trung < _NHOM_CO_DINH:
            continue
        x = m.tron.match(chu)
        if x:
            do_dai = sum(len(x.group(f"p{n}") or "") for n in m.thu_tu)
            if tot is None or do_dai < tot_do_dai:
                tot, tot_do_dai = (m, x), do_dai
    tron = None
    if tot:
        m, x = tot
        tron = _gan_dien_giai(Buoc(goc=chu, id=m.id, gia_tri={n: x.group(f"p{n}") for n in m.thu_tu}))
    if not cho_phep_dau:
        return tron
    ghep = _khop_ghep(chu, k)
    # Dong ghep hai Label ("%1 found within ... (%2 to %3). " + "%1 adjusted from %2 to %3.") cung khop tron voi Label sau vi
    # %1 nuot ca cau dau. Chon cach doc de lai it chu chua giai thich hon. Gap that 14/09/2026 voi Retail Forecast.
    if tron is not None and (ghep is None or _do_dai_bat(tron) <= _do_dai_bat(ghep)):
        return tron
    return ghep


def _do_dai_bat(b: Buoc) -> int:
    return sum(len(v or "") for v in b.gia_tri.values()) + sum(_do_dai_bat(x) for x in b.phan_them)


def _khop_ghep(chu: str, k: dict) -> Buoc | None:
    for m in k["mau"]:
        if m.do_dac_trung < 8 or not m.thu_tu and m.do_dac_trung < 12:
            continue
        x = m.dau.match(chu)
        if not x or x.end() == 0:
            continue
        con_lai = _NGAN.sub("", chu[x.end():])
        if not con_lai:
            continue
        # Label cuoi co %n thi phan lazy an rong; chi nhan khi phan con lai doc duoc.
        sau = _khop(con_lai, cho_phep_dau=True) or _khop(" " + con_lai, cho_phep_dau=False)
        if sau is None:
            continue
        b = _gan_dien_giai(Buoc(goc=chu, id=m.id, gia_tri={n: x.group(f"p{n}") for n in m.thu_tu}))
        b.phan_them.append(sau)
        return b
    return None


def doc_dong(chu: str) -> Buoc:
    goc = chu or ""
    con, the = goc.strip(), []
    while True:
        m = _THE.match(con)
        if not m:
            break
        the.append(m.group(1))
        con = con[m.end():]
    b = _khop(con)
    if b is None:
        # "Filters:Item No.: A|B, Store Group Filter: S1" va "Template Filters:Replen. Template.Location Code=W0003":
        # Label ngan o dau dong (Filters:, Template Filters:) cong danh sach bo loc ghep tay.
        for m in tai()["mau"]:
            if not m.thu_tu and m.van_ban.strip().endswith(":") and con.startswith(m.van_ban.strip()):
                than = con[len(m.van_ban.strip()):]
                cap = [(a.strip(), v.strip()) for a, v in
                       (re.split(r"\s*(?:=|:)\s*", x, maxsplit=1) for x in re.split(r",\s+|\s+-\s+", than)
                        if re.search(r"[=:]", x))]
                b = _gan_dien_giai(Buoc(goc=goc, id=m.id, cap=cap))
                break
    if b is None and " = " in con:
        cap = _doc_cap(con)
        if cap:
            b = Buoc(goc=goc, loai="tham_so", buoc="tham_so" if con.startswith("Replen. Data") or con.startswith("Data Profile")
                     else "he_thong", cap=cap)
    if b is None:
        b = Buoc(goc=goc, loai="chua_nhan_dang")
    b.goc, b.the = goc, the
    return b


def doc_nhat_ky(dong: list[str]) -> dict[str, Any]:
    """Doc ca nhat ky cua mot mat hang tai mot dia diem. Tra ve cac buoc va thong ke do phu."""
    buoc = [doc_dong(d) for d in dong]
    chua = [b.goc for b in buoc if b.loai == "chua_nhan_dang"]
    co_mau_chua_dien = [b.goc for b in buoc if b.loai == "mau" and not b.noi]
    return {"buoc": buoc, "chua_nhan_dang": chua, "chua_dien_giai": co_mau_chua_dien,
            "ty_le_nhan_dang": round(1 - len(chua) / len(buoc), 3) if buoc else 1.0}


def cau_tham_so(caption: str, gia_tri: str) -> str:
    """Mot cau cho mot cap tham so: ten, gia tri, y nghia ngan, noi sua."""
    t = tai()["tham_so"].get(caption.strip(), {})
    ten = t.get("ten") or caption
    cau = f"{caption} = {gia_tri or '(trống)'}"
    if ten != caption:
        cau += f" ({ten})"
    if t.get("sua_o"):
        cau += f"; sửa ở {t['sua_o']}"
    return cau


def tham_so(caption: str) -> dict[str, Any]:
    return tai()["tham_so"].get(caption.strip(), {})
