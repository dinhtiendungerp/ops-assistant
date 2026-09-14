"""Test khong duoc dung vao so chi phi va file cai dat that.

Hai file nay nam trong `runs/` va song qua lan khoi dong lai. Neu de test ghi vao do thi mot
lan chay `pytest` co the tat AI cua tro ly that hoac lam so tien bao cao sai. Doi ca hai sang
thu muc tam cua tung phien test.
"""
from __future__ import annotations

import pytest

from assistant import budget as budget_mod
from assistant import caidat as caidat_mod
from assistant import kich_ban as kich_ban_mod


@pytest.fixture(autouse=True)
def _tach_khoi_file_that(tmp_path, monkeypatch):
    monkeypatch.setattr(budget_mod, "DUONG_SO", tmp_path / "chi-phi.sqlite")
    monkeypatch.setattr(caidat_mod, "DUONG", tmp_path / "cai-dat.json")
    # Kich ban da duyet cung song qua lan khoi dong lai; test ghi vao file that thi mot kich ban
    # gia co the tra loi thay model tren man hinh demo.
    monkeypatch.setattr(kich_ban_mod, "DUONG", tmp_path / "kich-ban.sqlite")
    yield
