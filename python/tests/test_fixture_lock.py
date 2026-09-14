"""Fixtures bi khoa thi khong duoc lam chet app.

Ly do co file nay: tren may cua Dung, thu muc du an nam trong OneDrive. Khi
device_commit_files ghi lai fixtures dung luc uvicorn --reload khoi tao lai tro ly,
Windows tra PermissionError va ca tien trinh chet, phai sua file bat ky de reload lai.
Hai test duoi chot lai hai lop phong ve: doc co retry, va baseline hong thi bo qua.
"""
from __future__ import annotations

import json
from pathlib import Path

import pytest

from assistant.core import Assistant
from assistant.gateway import BCGateway, FixtureLocked
from assistant.skills import kpi
from bc_agent.mock_client import MockBCClient


def test_doc_fixtures_json_co_retry(monkeypatch):
    """Hai lan dau bi khoa, lan thu ba doc duoc: van phai ra du lieu."""
    that = {"n": 0}
    real = Path.read_text

    def flaky(self, *a, **kw):
        if self.name.endswith(".json"):
            that["n"] += 1
            if that["n"] <= 2:
                raise PermissionError(13, "Permission denied", str(self))
        return real(self, *a, **kw)

    monkeypatch.setattr(Path, "read_text", flaky)
    monkeypatch.setattr("time.sleep", lambda *_: None)
    client = MockBCClient()
    assert client.data["inventoryHealthLines"], "phai doc duoc sau khi thu lai"
    assert that["n"] > 2


def test_doc_fixtures_khoa_han_thi_bao_loi_ro_rang(monkeypatch):
    monkeypatch.setattr(Path, "read_text",
                        lambda self, *a, **kw: (_ for _ in ()).throw(PermissionError(13, "denied", str(self))))
    monkeypatch.setattr("time.sleep", lambda *_: None)
    with pytest.raises(OSError, match="Khong doc duoc fixtures"):
        MockBCClient()


def test_sales_history_doc_mot_lan_roi_nho_lai():
    """48 cap x doc lai ca file la phi, va moi lan doc la mot lan co the trung khoa file."""
    gw = BCGateway(MockBCClient())
    calls = {"n": 0}
    real = gw._sales_rows

    def counted():
        calls["n"] += 1
        return real()

    gw._sales_rows = counted
    a = gw.sales_history("33200", "S0001", days=120)
    b = gw.sales_history("33200", "S0001", days=120)
    assert a == b
    assert calls["n"] == 2  # goi 2 lan nhung ben trong chi mo file 1 lan
    assert gw._sales_cache is not None


def test_khoi_tao_tro_ly_song_sot_khi_sales_history_bi_khoa(monkeypatch, caplog):
    """Baseline khong chot duoc thi ghi canh bao, khong duoc keo ca app chet theo."""
    def locked(self):
        raise FixtureLocked("gia lap OneDrive dang giu file")

    monkeypatch.setattr(BCGateway, "_sales_rows", locked)
    kpi._STOCKOUT_CACHE.clear()  # cache o cap module, khong don thi test truoc da ham nong
    with caplog.at_level("WARNING"):
        asst = Assistant(MockBCClient())
    assert asst.mem.recall("baseline") is None
    assert "Chua chot duoc baseline" in caplog.text
    # va tro ly van tra loi duoc
    out = asst.handle_message("hung.dieuphoi", "còn bao nhiêu Ba Ria 76")
    assert out
