# -*- coding: utf-8 -*-
"""Cat linh vat ra bon tep dung trong giao dien.

Ban 2, ngay 13/09/2026: Dung dua bo linh vat moi gom hai anh da co nen trong suot.
  docs/linh-vat-toan-than.png  ca nguoi, tay dang gioi thieu  -> mascot.png cho man hinh chao
  docs/linh-vat-ban-than.png   dau va than tren               -> ba avatar 128px
Bo moi chi co mot net mat, nen ba trang thai (san sang, suy nghi, hoan tat) dung chung mot avatar.
Giu ba ten tep de giao dien khong phai sua; khi co anh rieng tung trang thai thi thay o day.

Ban 1 cat tu `docs/linh-vat-goc.png`, anh co chu chung khung nen phai xoa chu theo tung dai.
"""
from __future__ import annotations

import pathlib

import numpy as np
from PIL import Image

GOC = pathlib.Path(__file__).resolve().parents[1] / "docs"
TOAN_THAN = GOC / "linh-vat-toan-than.png"
BAN_THAN = GOC / "linh-vat-ban-than.png"
RA = pathlib.Path(__file__).resolve().parents[1] / "python" / "assistant" / "static"


def chi_giu_hinh_lon_nhat(im: Image.Image, nguong: int = 40) -> Image.Image:
    """Giu lai mang lien thong lon nhat, bo moi manh vun con lai.

    Anh xuat tu cong cu tao anh con vai vet ban mo o mep khung; bo het nhung gi khong dinh vao
    than linh vat."""
    from collections import deque

    al = np.asarray(im.convert("RGBA"))[:, :, 3]
    h, w = al.shape
    co = al > nguong
    tham = np.zeros((h, w), dtype=bool)
    lon_nhat: list[tuple[int, int]] = []
    for y0 in range(h):
        for x0 in range(w):
            if not co[y0, x0] or tham[y0, x0]:
                continue
            q = deque([(y0, x0)])
            tham[y0, x0] = True
            mang = []
            while q:
                y, x = q.popleft()
                mang.append((y, x))
                for dy, dx in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                    ny, nx = y + dy, x + dx
                    if 0 <= ny < h and 0 <= nx < w and co[ny, nx] and not tham[ny, nx]:
                        tham[ny, nx] = True
                        q.append((ny, nx))
            if len(mang) > len(lon_nhat):
                lon_nhat = mang
    giu = np.zeros((h, w), dtype=bool)
    for y, x in lon_nhat:
        giu[y, x] = True
    a = np.array(im.convert("RGBA"))
    a[:, :, 3] = np.where(giu, a[:, :, 3], 0)
    return Image.fromarray(a)


def sach(im: Image.Image) -> Image.Image:
    """Bo manh vun roi bo vien trong quanh hinh."""
    im = chi_giu_hinh_lon_nhat(im)
    return im.crop(im.getbbox())


def luu(im: Image.Image, ten: str, rong: int) -> None:
    im = im.resize((rong, max(1, round(im.height * rong / im.width))), Image.LANCZOS)
    p = RA / ten
    im.save(p, "PNG", optimize=True)
    print(f"  {ten:22s} {im.size}  {p.stat().st_size / 1024:.0f} KB")


def cat_dau(im: Image.Image) -> Image.Image:
    """Cat o vuong quanh khuon mat, chua phan mam vang phia tren.

    De ca than vao vong tron 34px thi khuon mat chi con vai pixel. Tim khuon mat bang mau kem."""
    a = np.asarray(im.convert("RGBA")).astype(int)
    rgb, al = a[:, :, :3], a[:, :, 3]
    mat = (al > 150) & (rgb.mean(2) > 175) & (rgb[:, :, 0] - rgb[:, :, 2] > 35) & (rgb[:, :, 0] - rgb[:, :, 1] < 70)
    ys, xs = np.where(mat)
    if not len(xs):
        return im
    cx, cy = (xs.min() + xs.max()) / 2, (ys.min() + ys.max()) / 2
    # He so 0,68: bo moi co khuon mat chiem gan het bong trang, o vong tron 34px van thay mat va
    # mot phan mu do. 0,85 cua ban 1 hop voi anh cu, voi anh ban than moi thi lay gan het nguoi.
    r = max(xs.max() - xs.min(), ys.max() - ys.min()) * 0.68
    hop = (round(cx - r), round(cy - r * 1.2), round(cx + r), round(cy + r * 0.8))
    return im.crop(hop)


def main() -> None:
    # Anh lon, lam sach tren ban thu nho truoc cho nhanh: 1.100 x 1.300 diem anh voi BFS thuan
    # Python mat vai phut, con thu nho mot nua van du net cho o 440px.
    toan = Image.open(TOAN_THAN).convert("RGBA")
    toan = toan.resize((toan.width // 2, toan.height // 2), Image.LANCZOS)
    luu(sach(toan), "mascot.png", 440)

    ban = Image.open(BAN_THAN).convert("RGBA")
    ban = sach(ban.resize((ban.width // 2, ban.height // 2), Image.LANCZOS))
    dau = cat_dau(ban)
    for ten in ("mascot-san-sang.png", "mascot-suy-nghi.png", "mascot-hoan-tat.png"):
        luu(dau, ten, 128)


if __name__ == "__main__":
    main()
