"""Bo nho tro ly dung chung mot ket noi SQLite giua cac luong cua uvicorn.

Ngay 14/09/2026 `/api/inbox` tra 500 `sqlite3.InterfaceError` khi hai request chong len nhau. Test nay ban nhieu luong
cung doc va ghi mot `Memory` va phai khong co loi nao.
"""
from __future__ import annotations

import threading

from assistant.memory import Memory


def test_nhieu_luong_doc_ghi_cung_ket_noi():
    mem = Memory()
    mem.upsert_users([{"user_id": "u1", "display_name": "U", "role": "admin", "location_code": ""}])
    loi: list[BaseException] = []

    def chay(i: int) -> None:
        try:
            for j in range(150):
                mem.log_message("u1", "out", f"tin {i}-{j}")
                mem.inbox("u1", 0)
                mem.doan_dang_mo("u1")
        except BaseException as e:  # noqa: BLE001
            loi.append(e)

    luong = [threading.Thread(target=chay, args=(i,)) for i in range(8)]
    for t in luong:
        t.start()
    for t in luong:
        t.join()
    assert not loi, loi[:1]
    assert len(mem.inbox("u1", 0)) == 8 * 150
