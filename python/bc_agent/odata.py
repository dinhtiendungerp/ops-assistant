"""Dieu kien loc dung chung cho live (OData $filter) va mock (loc trong Python).

Condition = (field, op, value) voi op in eq, ne, gt, ge, lt, le.
"""
from __future__ import annotations

import re
from datetime import date, datetime

from typing import Any, Iterable

Condition = tuple[str, str, Any]

_OPS = {
    "eq": lambda a, b: a == b,
    "ne": lambda a, b: a != b,
    "gt": lambda a, b: a > b,
    "ge": lambda a, b: a >= b,
    "lt": lambda a, b: a < b,
    "le": lambda a, b: a <= b,
}


# Ngay trong OData V4 la Edm.Date, viet tran khong dau nhay. Boc trong dau nhay thi BC tra
# HTTP 400 "A binary operator with incompatible types was detected. Found operand types
# 'Edm.Date' and 'Edm.String'". Bat duoc ngay 12/09/2026 khi tro ly loc theo Posting Date.
_ISO_DATE = re.compile(r"^\d{4}-\d{2}-\d{2}$")


def _literal(v: Any) -> str:
    if isinstance(v, bool):
        return "true" if v else "false"
    if isinstance(v, (int, float)):
        return str(v)
    if isinstance(v, datetime):
        return v.isoformat()
    if isinstance(v, date):
        return v.isoformat()
    s = str(v)
    if _ISO_DATE.match(s):
        return s
    return "'" + s.replace("'", "''") + "'"


def to_odata_filter(conds: Iterable[Condition]) -> str | None:
    parts = [f"{f} {op} {_literal(v)}" for f, op, v in conds]
    return " and ".join(parts) if parts else None


def apply_in_python(rows: list[dict[str, Any]], conds: Iterable[Condition],
                    orderby: str | None = None, top: int | None = None) -> list[dict[str, Any]]:
    out = rows
    for f, op, v in conds:
        fn = _OPS[op]
        out = [r for r in out if f in r and fn(r[f], v)]
    if orderby:
        field, _, direction = orderby.partition(" ")
        out = sorted(out, key=lambda r: r.get(field), reverse=(direction.strip().lower() == "desc"))
    if top:
        out = out[:top]
    return out
