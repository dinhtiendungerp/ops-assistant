"""Cat anh chup UC2 cho slide: bo cot trai va cot phai cua giao dien, giu vung noi dung chinh.

    python tools/cat_anh_slide_uc2.py      # ghi vao docs/uc2/slide/
Anh nguon: docs/anh-uc2 (node tools/chup_uc2.mjs), docs/anh-demo (node tools/chup_man_hinh.mjs).
"""
from pathlib import Path

from PIL import Image

GOC = Path(__file__).resolve().parent.parent / "docs"
RA = GOC / "uc2" / "slide"

# ten ra: (anh nguon, hop cat (trai, tren, phai, duoi) hoac None la giu nguyen)
CAT = {
    "tong-quan": ("anh-uc2/uc2-01-tong-quan.png", (500, 340, 2200, 1960)),
    "tang-qua-han": ("anh-uc2/uc2-02-tang-qua-han.png", (500, 340, 2200, 1960)),
    "chi-tiet-lo": ("anh-uc2/uc2-03-chi-tiet-lo.png", (500, 240, 2200, 2320)),
    "do-phu": ("anh-uc2/uc2-04-do-phu-du-lieu.png", (500, 1350, 2200, 2900)),
    "brief": ("anh-uc2/uc2-05-brief-supply-chain-dau.png", None),
    "het-han-dieu-phoi": ("anh-uc2/uc2-06-het-han-dieu-phoi-dau.png", (0, 0, 1612, 1290)),
    "sap-het-han-cua-hang": ("anh-uc2/uc2-07-sap-het-han-cua-hang-dau.png", (0, 0, 1612, 1290)),
    "truy-xuat": ("anh-uc2/uc2-08-truy-xuat-lo.png", None),
    "ton-cua-hang": ("anh-uc2/uc2-09-ton-cua-hang.png", None),
    "de-xuat": ("anh-uc2/uc2-10-de-xuat-huy-va-chuyen.png", None),
    "the-duyet": ("anh-uc2/uc2-11-the-duyet-nguoi-duyet.png", (0, 0, 1612, 1330)),
    "cau-hoi-mo": ("anh-demo/13-cau-hoi-mo-model.png", None),
}


def main() -> None:
    RA.mkdir(parents=True, exist_ok=True)
    for ten, (nguon, hop) in CAT.items():
        im = Image.open(GOC / nguon).convert("RGB")
        if hop:
            im = im.crop(hop)
        im.save(RA / f"{ten}.png", optimize=True)
        print(ten, im.size)


if __name__ == "__main__":
    main()
