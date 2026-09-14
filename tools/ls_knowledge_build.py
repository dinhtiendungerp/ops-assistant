"""Sinh danh muc cau log tinh Replenishment tu source LS Central. Khong go tay.

Vi sao co file nay. Dung yeu cau ngay 14/09/2026: knowledge giai thich so cua LS phai dung cho moi tinh huong, khong chi
cho du lieu mau. Moi dong trong `LSC Replen. Calc. Log Lines V2` do LS ghi bang `StrSubstNo(<Label>, ...)` hoac ghep
nhieu Label lai. Nen danh muc dung nhat la chinh cac Label do, doc thang tu source. Nang version LS thi chay lai script
va xem file sinh ra khac gi.

Chay:  python tools/ls_knowledge_build.py [thu muc src cua goi LS]
Ra:    python/assistant/knowledge/ls_replen/mau_log.json

Phan dien giai tieng Viet nam rieng o `dien_giai.yaml` (nguoi viet, doc source roi moi ghi), khoa theo `id` o day.
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

GOC = Path(__file__).resolve().parents[1]
SRC_MAC_DINH = GOC / "unpacked" / "LS Retail_LS Central_28.0.10.3586" / "src" / "src"
RA = GOC / "python" / "assistant" / "knowledge" / "ls_replen" / "mau_log.json"
PHIEN_BAN_LS = "28.0.10.3586"

# Nhung file co ghi Calc. Log Lines khi tinh journal (tim bang InsertTempReplenCalculationLogLine ngay 14/09/2026).
# Bo cac page va file tao chung tu: chung khong ghi log tinh.
# Khoa ngan dung lam tien to id, de id doc duoc va khong trung giua cac file.
FILE_GHI_LOG = {
    "CALC": "Replenishment/Automatic/Journals/Core/Replen. Calculation.codeunit.al",
    "ADDITEMS": "Replenishment/Automatic/Journals/Standard/Add Items to Replen. Jrnl.report.al",
    "MWH": "Replenishment/Automatic/Journals/MultiWarehouse/Replen. Multi-Whse. Utils.codeunit.al",
    "REDIST": "Replenishment/Automatic/Journals/StoreStockRedistribution/Replen. Redist. Calculation.codeunit.al",
    "ADDBOM": "Replenishment/Automatic/Journals/Hospitality/Add BOM to Replen. Jrnl.report.al",
    "ADDCOMP": "Replenishment/Automatic/Journals/Hospitality/Add Comp. to Replen. Jrnl.report.al",
}

_LABEL = re.compile(r"^\s*(\w+)\s*:\s*Label\s+'((?:[^']|'')*)'(.*)$")
# Label khong bao gio xuat hien trong log: thanh tien trinh, loi hop thoai, ma locked noi bo.
_BO = re.compile(r"^(#|@)|#\d#|@\d@|\?$|^(This Batch Job|Process has been terminated)")


def doc_label(duong: Path) -> list[tuple[str, str, int, bool]]:
    ra = []
    for i, dong in enumerate(duong.read_text(encoding="utf-8-sig").splitlines(), 1):
        m = _LABEL.match(dong)
        if m:
            ra.append((m.group(1), m.group(2).replace("''", "'"), i, "Locked = true" in m.group(3)))
    return ra


def main(argv: list[str]) -> None:
    src = Path(argv[0]) if argv else SRC_MAC_DINH
    muc: dict[str, dict] = {}
    for khoa_file, rel in FILE_GHI_LOG.items():
        f = src / rel
        for ten, van_ban, dong, _locked in doc_label(f):
            if _BO.search(van_ban) or not van_ban.strip():
                continue
            chu = re.sub(r"%\d", "", van_ban)
            # Cung mot cau o nhieu file (Checking Item o ba report) thi giu mot muc, ghi them noi xuat hien.
            khoa = van_ban.strip()
            if khoa in muc:
                muc[khoa]["cung_xuat_hien"].append(f"{Path(rel).name}:{ten}")
                continue
            muc[khoa] = {
                "id": f"{khoa_file}:{ten}",
                "label": ten,
                "file": Path(rel).name,
                "dong": dong,
                "van_ban": van_ban,
                "so_tham_so": len(set(re.findall(r"%(\d)", van_ban))),
                "do_dac_trung": len(re.sub(r"\W", "", chu)),
                "cung_xuat_hien": [],
            }
    ds = sorted(muc.values(), key=lambda m: (-m["do_dac_trung"], m["id"]))
    RA.parent.mkdir(parents=True, exist_ok=True)
    RA.write_text(json.dumps({"ls_central": PHIEN_BAN_LS, "nguon": list(FILE_GHI_LOG.values()), "mau": ds}, ensure_ascii=False, indent=1),
                  encoding="utf-8")
    print(f"{len(ds)} mau -> {RA}")


if __name__ == "__main__":
    main(sys.argv[1:])
