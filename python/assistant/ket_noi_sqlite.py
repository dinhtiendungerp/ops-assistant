"""Ket noi SQLite dung chung giua nhieu luong cua uvicorn.

Vi sao co file nay. Ngay 14/09/2026 `/api/inbox` tra 500 `sqlite3.InterfaceError: bad parameter or other API misuse`
ngay sau khi doi nguon du lieu: FastAPI chay moi request dong bo tren threadpool, ma `Memory` va `Budget` giu MOT
ket noi `check_same_thread=False`. Hai luong goi `execute` va doc cursor chong len nhau thi sqlite3 cua Python bao loi
tren. `check_same_thread=False` chi tat buoc kiem tra, khong lam ket noi an toan.

Cach sua: moi `execute` chay trong mot khoa va doc het ket qua truoc khi nha khoa, tra ve mot cursor da doc san
(`fetchone`, `fetchall`, lap, `lastrowid`, `rowcount`). Luong goi khong phai doi gi.
"""
from __future__ import annotations

import sqlite3
import threading
from typing import Any, Iterator


class _KetQua:
    """Cursor da doc het, dung ngoai khoa ma khong cham vao ket noi."""

    def __init__(self, rows: list[Any], lastrowid: int | None, rowcount: int):
        self._rows = rows
        self._i = 0
        self.lastrowid = lastrowid
        self.rowcount = rowcount

    def fetchone(self) -> Any:
        if self._i >= len(self._rows):
            return None
        r = self._rows[self._i]
        self._i += 1
        return r

    def fetchall(self) -> list[Any]:
        r = self._rows[self._i:]
        self._i = len(self._rows)
        return r

    def __iter__(self) -> Iterator[Any]:
        return iter(self.fetchall())


class KetNoiKhoa:
    """Boc sqlite3.Connection, tuan tu hoa moi lenh bang RLock."""

    def __init__(self, conn: sqlite3.Connection):
        self._conn = conn
        self._khoa = threading.RLock()

    def execute(self, sql: str, params: Any = ()) -> _KetQua:
        with self._khoa:
            cur = self._conn.execute(sql, params)
            rows = cur.fetchall() if cur.description else []
            return _KetQua(rows, cur.lastrowid, cur.rowcount)

    def executescript(self, sql: str) -> None:
        with self._khoa:
            self._conn.executescript(sql)

    def commit(self) -> None:
        with self._khoa:
            self._conn.commit()

    def close(self) -> None:
        with self._khoa:
            self._conn.close()

    @property
    def row_factory(self) -> Any:
        return self._conn.row_factory

    @row_factory.setter
    def row_factory(self, v: Any) -> None:
        self._conn.row_factory = v


def boc(conn: sqlite3.Connection | KetNoiKhoa) -> KetNoiKhoa:
    return conn if isinstance(conn, KetNoiKhoa) else KetNoiKhoa(conn)
