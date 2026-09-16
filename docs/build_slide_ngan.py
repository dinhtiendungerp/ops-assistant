"""Ban rut gon cua bo slide 12: giu lai nhung slide trong yeu nhat cho buoi demo 25 den 30 phut.

Khong dung lai noi dung. No mo bo day du roi xoa bot slide, nen sua bo day du thi chay lai file nay la xong.

Doc bo day du tu `Demo-Marou` chu khong tu `docs`, vi file trong docs nam trong OneDrive va hay bi PowerPoint
mo san; doc file dang bi khoa se hong. Ghi ra cung thu muc `Demo-Marou`, ngoai OneDrive.

Chay: cd docs; python build_slide_ngan.py
"""
from pathlib import Path

from pptx import Presentation

NGOAI = Path(r"C:/Users/dungdt.NWV/Demo-Marou")
NGUON = NGOAI / "Marou POC - slide demo.pptx"
RA = NGOAI / "Marou POC - slide demo (ban ngan).pptx"
# Ten file ra doi duoc qua tham so dong lenh. Can khi ban cu dang mo trong PowerPoint: ghi de len file dang mo thi
# PermissionError, va neu nguoi dung da sua gi tren ban do thi ghi de la mat cong cua ho.
import sys as _sys
if len(_sys.argv) > 1:
    RA = NGOAI / _sys.argv[1]

# So thu tu slide trong bo day du (bat dau tu 1) va ly do giu lai.
GIU = {
    1:  "bia",
    2:  "bia phan UC2",
    3:  "kien truc: tro ly lam viec the nao",
    4:  "ban do tinh nang",
    6:  "hai don vi Marou va Dakao, boi canh cho kich ban 16",
    7:  "13 tinh nang AI trong bon nhom, kem phep kiem so",
    8:  "bon chot chan tu de xuat den chung tu",
    10: "kich ban 01 dashboard suc khoe ton kho",
    14: "kich ban 05 brief buoi sang do AI viet",
    17: "kich ban 08 phuong an cho lo can date",
    18: "kich ban 09 de xuat va nguoi duyet",
    21: "kich ban 11 truy xuat lo, phan traceability cua UC2",
    26: "kich ban 16 nhan hang lien cong ty",
    27: "kich ban 16 bang chung, hai anh that",
    29: "chi phi AI do duoc",
    30: "tong ket va viec con lai",
}

# Nhung slide bo di, de biet neu khach hoi thi mo bo day du o slide nao.
BO = {
    5:  "kien truc chi tiet tung lop, de danh cho buoi sau",
    9:  "danh muc kich ban, khong can khi chi dien sau man",
    11: "kich ban 02 loc tang tim lo",
    12: "kich ban 03 vi sao mot lo vao tang do",
    13: "kich ban 04 do phu du lieu",
    15: "kich ban 06 hoi hang het han",
    16: "kich ban 07 tra ton tai cua hang cua minh",
    19: "kich ban 10 luong huy khep kin",
    20: "kich ban 10b bien ban huy do AI soan",
    22: "kich ban 12 phat hien bat thuong",
    23: "kich ban 13 nguyen nhan hang huy",
    24: "kich ban 14 quet sang",
    25: "kich ban 15 bao cao tuan hang huy",
    28: "kich ban bo sung UC3 nhac post nhan hang",
}


def xoa_slide(pr, giu_1based):
    """Giu lai dung nhung slide co so thu tu trong `giu_1based`, xoa het phan con lai."""
    ids = pr.slides._sldIdLst
    for i in range(len(ids) - 1, -1, -1):
        if (i + 1) in giu_1based:
            continue
        rid = ids[i].rId
        pr.part.drop_rel(rid)
        ids.remove(ids[i])


def bo_section(pr):
    """Xoa danh sach section trong presentation.xml.

    Template cua NaviWorld khai ba section tro toi 32 slide. Xoa bot slide thi nhung tro do thanh mo coi, va
    PowerPoint bao khong mo duoc file (bat duoc 16/09/2026 voi ban rut gon 16 slide). Section chi la cach nhom
    slide o khung ben trai, bo di khong mat noi dung gi.
    """
    el = pr.part._element
    for ext_lst in [e for e in el if e.tag.endswith("}extLst")]:
        for ext in list(ext_lst):
            if any(ch.tag.endswith("}sectionLst") for ch in ext):
                ext_lst.remove(ext)
        if len(ext_lst) == 0:
            el.remove(ext_lst)


def main() -> None:
    if not NGUON.exists():
        raise SystemExit(f"Khong thay bo day du o {NGUON}. Chay build_slide_uc2_v2.py roi chep ra {NGOAI}.")
    pr = Presentation(str(NGUON))
    tong = len(pr.slides._sldIdLst)
    # `^` uu tien cao hon `|`, viet gop mot dong la ra ket qua vo nghia. Tach ra cho ro.
    thieu = sorted(set(range(1, tong + 1)) - (set(GIU) | set(BO)))
    if thieu:
        print("CANH BAO: bo day du co", tong, "slide, chua xep slide:", thieu)
    xoa_slide(pr, set(GIU))
    bo_section(pr)
    pr.save(str(RA))
    print("da ghi:", RA)
    print("so slide:", len(Presentation(str(RA)).slides._sldIdLst))
    for i, (so, ly_do) in enumerate(sorted(GIU.items()), 1):
        print(f"  {i:2}. (goc {so:2}) {ly_do}")


if __name__ == "__main__":
    main()
