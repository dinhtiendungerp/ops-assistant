"""Gia Azure OpenAI va hai tran chi phi.

Ly do co file nay: con so tien phai tinh tu don gia that, khong uoc luong. Don gia lay ngay
12/09/2026 tu Azure Retail Prices API, region eastus, deployment Global Standard.
"""
from __future__ import annotations

import sqlite3

import pytest

from assistant.budget import Budget, price_of, tokens_for_budget


def test_gia_gpt_41_mini_dung_theo_bang_gia_azure():
    """112 token vao, 67 token ra la lan goi that dau tien tren resource Marou."""
    usd = price_of("gpt-4.1-mini", 112, 67)
    assert usd == pytest.approx(112 / 1e6 * 0.40 + 67 / 1e6 * 1.60)
    assert usd == pytest.approx(0.0001520, abs=1e-9)


def test_cache_read_cua_azure_khong_dung_he_so_cua_claude():
    """Claude cache read la 0.1 lan input, gpt-4.1-mini la 0.25 lan. Dung nham he so thi
    con so bao cao cho khach se sai."""
    assert price_of("gpt-4.1-mini", 0, 0, cache_read=1_000_000) == pytest.approx(0.40 * 0.25)
    assert price_of("claude-opus-5", 0, 0, cache_read=1_000_000) == pytest.approx(5.0 * 0.1)


def test_muoi_do_doi_ra_bao_nhieu_token():
    t = tokens_for_budget("gpt-4.1-mini", 10.0)
    assert t["chi_input"] == pytest.approx(25_000_000)
    assert t["chi_output"] == pytest.approx(6_250_000)
    assert 11_000_000 < t["hon_hop"] < 12_500_000


def _budget(daily=100.0, total=10.0):
    return Budget(sqlite3.connect(":memory:"), daily_cap_usd=daily, total_cap_usd=total)


class _Usage:
    def __init__(self, tin, tout):
        self.input_tokens, self.output_tokens = tin, tout
        self.cache_read_input_tokens = self.cache_creation_input_tokens = 0


def test_tran_cong_don_chan_khi_vuot_muoi_do():
    b = _budget()
    assert b.allow()
    # 6,25 trieu token ra la dung 10 do
    b.track("test", "gpt-4.1-mini", _Usage(0, 6_250_000))
    assert b.spent_total() == pytest.approx(10.0)
    assert not b.allow(), "vuot tran cong don ma van cho chay"


def test_tran_cong_don_khong_reset_theo_ngay():
    """Tran ngay reset moi sang, tran cong don thi khong. Day la khac biet chinh."""
    b = _budget(daily=100.0, total=1.0)
    b.track("test", "gpt-4.1-mini", _Usage(0, 700_000))   # 1,12 do
    b.conn.execute("UPDATE llm_calls SET day='2020-01-01'")
    b.conn.commit()
    assert b.spent_today() == 0.0
    assert b.spent_total() == pytest.approx(1.12)
    assert not b.allow(), "hom sau van phai chan vi tran cong don da vuot"


def test_tran_bang_khong_nghia_la_khong_gioi_han():
    b = _budget(daily=0.0, total=0.0)
    b.track("test", "gpt-4.1-mini", _Usage(0, 100_000_000))
    assert b.allow()
