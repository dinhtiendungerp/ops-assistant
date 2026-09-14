"""Do do phu cua knowledge LS Replenishment tren nhat ky tinh THAT trong BC.

Chay sau moi lan tinh journal hoac khi Marou doi cau hinh, doi version LS:
    cd python; python ../tools/ls_knowledge_coverage.py

In ra: so dong log, ty le nhan dang, dong chua nhan dang (gom theo dang), Label co trong log nhung chua co dien giai
tieng Viet, va Label co dien giai trong catalog. Dong chua nhan dang la viec phai bo sung vao knowledge, khong phai loi
cua tro ly.
"""
from __future__ import annotations

import re
import sys
from collections import Counter
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "python"))

from assistant import ls_knowledge as kt  # noqa: E402
from bc_agent.bc_client import BCClient  # noqa: E402
from bc_agent.config import Settings  # noqa: E402


def main() -> None:
    rows = BCClient(Settings()).query("replenCalcLogLines", [], top=20000)
    kq = kt.doc_nhat_ky([r.get("messageText", "") for r in rows])
    dang = lambda s: re.sub(r"-?\d[\d.,/]*", "#", s)[:110]  # noqa: E731
    print(f"LS Central trong knowledge: {kt.tai()['ls_central']}")
    print(f"Dong log: {len(rows)}; nhan dang {kq['ty_le_nhan_dang']:.1%}")
    print("Chua nhan dang:")
    for t, n in Counter(dang(x) for x in kq["chua_nhan_dang"]).most_common(20):
        print(f"  {n:5}  {t}")
    print("Nhan dang nhung chua co dien giai:")
    for t, n in Counter(dang(x) for x in kq["chua_dien_giai"]).most_common(20):
        print(f"  {n:5}  {t}")
    tong = len(kt.tai()["mau"])
    co = sum(1 for m in kt.tai()["mau"] if m.id in kt.tai()["dien_giai"])
    print(f"Label trong catalog: {tong}; co dien giai: {co}")


if __name__ == "__main__":
    main()
