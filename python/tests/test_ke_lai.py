"""Lop AI ke lai (16/09/2026): model viet lai phan loi cua the du lieu, so phai co trong the, tat AI thi khong dung."""
from __future__ import annotations

from assistant import ke_lai
from assistant.cards import Card
from assistant.core import Assistant
from assistant.skills import Delivery
from bc_agent.mock_client import MockBCClient


def _the() -> Delivery:
    return Delivery("trang.sc", "Đo trên 74 cặp: Holt-Winters sai 37,0%.", Card(title="Độ chính xác dự báo", body="S0001 34,1%",
                    facts=[("Holt-Winters", "37,0%"), ("Cặp đo", "74")], kind="info"), skill="du_bao")


def test_tat_ai_thi_giu_nguyen():
    a = Assistant(MockBCClient())
    a.ai_live = False
    d = _the()
    out = ke_lai.ke_lai(a, a.mem.user("trang.sc"), "độ chính xác dự báo", [d])
    assert out[0].text.startswith("Đo trên 74 cặp") and not any(f[0] == "Người soạn" for f in out[0].card.facts)


def test_ai_viet_lai_va_gan_nhan(monkeypatch):
    a = Assistant(MockBCClient())
    a.ai_live, a._writer = True, object()
    monkeypatch.setattr(ke_lai.tt, "_goi_model", lambda *x, **k: ({"tra_loi": "Holt-Winters đang tốt nhất với sai số 37,0% trên 74 cặp."}, "AI (test)"))
    d = _the()
    out = ke_lai.ke_lai(a, a.mem.user("trang.sc"), "độ chính xác dự báo", [d])
    assert out[0].text.startswith("Holt-Winters đang tốt nhất") and ("Người soạn", "AI (test)") in out[0].card.facts
    assert out[0].meta["cau_rule"].startswith("Đo trên 74 cặp")


def test_so_la_thi_giu_cau_rule(monkeypatch):
    a = Assistant(MockBCClient())
    a.ai_live, a._writer = True, object()
    monkeypatch.setattr(ke_lai.tt, "_goi_model", lambda *x, **k: ({"tra_loi": "Sai số 42% trên 74 cặp."}, "AI (test)"))
    d = _the()
    out = ke_lai.ke_lai(a, a.mem.user("trang.sc"), "độ chính xác dự báo", [d])
    assert out[0].text.startswith("Đo trên 74 cặp") and not any(f[0] == "Người soạn" for f in out[0].card.facts)


def test_the_da_co_nguoi_soan_hay_the_de_xuat_thi_bo_qua(monkeypatch):
    a = Assistant(MockBCClient())
    a.ai_live, a._writer = True, object()
    monkeypatch.setattr(ke_lai.tt, "_goi_model", lambda *x, **k: ({"tra_loi": "khong duoc goi"}, "AI (test)"))
    d1 = _the(); d1.card.facts.append(("Người soạn", "AI (x)"))
    d2 = Delivery("trang.sc", "đề xuất", Card(title="Đề xuất", body="", kind="proposal"), skill="replenishment")
    out = ke_lai.ke_lai(a, a.mem.user("trang.sc"), "x", [d1, d2])
    assert out[0].text.startswith("Đo trên") and out[1].text == "đề xuất"
