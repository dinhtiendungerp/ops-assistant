"""Dong ho chi phi va tran cung.

Vi sao co file nay: uoc tinh chi phi bang tay luon sai. Moi lan goi model deu ghi lai token that
tu response.usage, cong don theo ngay, va khi vuot tran thi tu chuyen ve che do rule/template
thay vi bao loi. Nguoi dung khong bao gio bi hoa don bat ngo, va demo khong bao gio chet giua chung.

Hai tran, vuot cai nao cung chan:
  AGENT_DAILY_BUDGET_USD  tran theo ngay, mac dinh 2 do
  AGENT_TOTAL_BUDGET_USD  tran cong don tu truoc den nay, mac dinh 10 do

Gia Claude (USD/trieu token) cap nhat 07/09/2026 tu claude.com/pricing.
Gia Azure OpenAI lay ngay 12/09/2026 tu Azure Retail Prices API, region eastus, USD:
  https://prices.azure.com/api/retail/prices?$filter=armRegionName eq 'eastus'
Doi gia thi sua o day, dung uoc luong bang tay.
"""
from __future__ import annotations

import logging
import os
import sqlite3
from dataclasses import dataclass
from datetime import date
from pathlib import Path
from typing import Any

from .ket_noi_sqlite import boc

log = logging.getLogger(__name__)

PRICES: dict[str, tuple[float, float]] = {
    "claude-opus-5": (5.0, 25.0),
    "claude-opus-4-8": (5.0, 25.0),
    "claude-sonnet-4-6": (3.0, 15.0),
    "claude-haiku-4-5": (1.0, 5.0),
    # Azure OpenAI, deployment Global Standard o eastus. Deployment Regional va Data Zone dat hon
    # 10 phan tram: vao 0.44, ra 1.76.
    "gpt-4.1-mini": (0.40, 1.60),
    "gpt-4.1": (2.00, 8.00),
}
DEFAULT_PRICE = (5.0, 25.0)
CACHE_READ_MULT = 0.1
CACHE_WRITE_MULT = 1.25
# Ty le gia cache read so voi input, tinh rieng vi moi nha cung cap mot khac.
# Claude 0.1x. gpt-4.1-mini: 0.10 tren 0.40 nen la 0.25x.
CACHE_READ_MULT_BY_MODEL: dict[str, float] = {"gpt-4.1-mini": 0.25, "gpt-4.1": 0.25}

# So chi phi nam RIENG mot file tren dia, khong nam trong bo nho cua tro ly.
# Bo nho tro ly la `:memory:` va bi dung moi khi doi nguon du lieu hoac khoi dong lai, nen neu
# de chung thi so tien vua tieu bien mat va trang Cai dat luon hien 0. Bat duoc ngay 13/09/2026
# khi Dung hoi "ro rang da chay roi sao chi phi hom nay chua co".
DUONG_SO = Path(os.getenv("AGENT_SPEND_DB", "")) if os.getenv("AGENT_SPEND_DB") else     Path(os.getenv("AGENT_LOG_DIR", "./runs")) / "chi-phi.sqlite"


def so_chi_phi(path: Path | str | None = None) -> sqlite3.Connection:
    """Mo so chi phi tren dia. Dung chung cho moi Assistant trong cung mot may."""
    duong = Path(path) if path else DUONG_SO
    duong.parent.mkdir(parents=True, exist_ok=True)
    return sqlite3.connect(str(duong), check_same_thread=False)


SCHEMA = """
CREATE TABLE IF NOT EXISTS llm_calls (
  id INTEGER PRIMARY KEY AUTOINCREMENT, day TEXT, ts TEXT, purpose TEXT, model TEXT,
  input_tokens INTEGER, output_tokens INTEGER, cache_read INTEGER, cache_write INTEGER, usd REAL
);
CREATE INDEX IF NOT EXISTS ix_llm_day ON llm_calls(day);
"""


def price_of(model: str, tin: int, tout: int, cache_read: int = 0, cache_write: int = 0) -> float:
    pi, po = PRICES.get(model, DEFAULT_PRICE)
    cr_mult = CACHE_READ_MULT_BY_MODEL.get(model, CACHE_READ_MULT)
    return (tin / 1e6) * pi + (tout / 1e6) * po + (cache_read / 1e6) * pi * cr_mult + (cache_write / 1e6) * pi * CACHE_WRITE_MULT


def tokens_for_budget(model: str, usd: float, share_input: float = 0.626) -> dict[str, float]:
    """Voi ngan sach usd, chay duoc bao nhieu token.

    share_input la ty le token vao tren tong. Mac dinh 0.626 do tu lan goi that dau tien
    tren gpt-4.1-mini: 112 token vao, 67 token ra. Ty le nay doi theo loai viec, doi cho khac
    thi truyen so khac vao.
    """
    pi, po = PRICES.get(model, DEFAULT_PRICE)
    blended = share_input * pi + (1 - share_input) * po      # USD tren mot trieu token tong
    return {
        "chi_input": usd / pi * 1e6,
        "chi_output": usd / po * 1e6,
        "hon_hop": usd / blended * 1e6,
        "gia_hon_hop_moi_trieu": blended,
    }


@dataclass
class Spend:
    usd: float
    calls: int
    by_purpose: dict[str, float]


class Budget:
    """Tran theo ngay. Vuot tran thi allow() tra False, caller tu quay ve rule/template."""

    def __init__(self, conn: sqlite3.Connection | None = None, daily_cap_usd: float | None = None,
                 total_cap_usd: float | None = None):
        self.conn = boc(conn if conn is not None else so_chi_phi())
        self.conn.executescript(SCHEMA)
        self.cap = float(os.getenv("AGENT_DAILY_BUDGET_USD", "2") if daily_cap_usd is None else daily_cap_usd)
        self.total_cap = float(os.getenv("AGENT_TOTAL_BUDGET_USD", "10") if total_cap_usd is None else total_cap_usd)
        self._warned = False
        self._warned_total = False
        # Cong tac AI tren trang Cai dat. Tat thi allow() tra False, tuc di dung con duong ma
        # het tran ngan sach van di: moi cho goi model tu quay ve rule/template. Khong them
        # nhanh moi nao trong luong xu ly, nen khong them cho nao de sai.
        self.ai_off = False

    def today(self) -> str:
        return date.today().isoformat()

    def spent_today(self) -> float:
        r = self.conn.execute("SELECT COALESCE(SUM(usd),0) s FROM llm_calls WHERE day=?", (self.today(),)).fetchone()
        return float(r[0])

    def spent_total(self) -> float:
        """Cong don tu dong dau tien trong so, khong reset theo ngay."""
        r = self.conn.execute("SELECT COALESCE(SUM(usd),0) s FROM llm_calls").fetchone()
        return float(r[0])

    def allow(self) -> bool:
        """Vuot tran ngay hoac tran cong don deu chan. Chan nghia la caller quay ve rule
        hoac template, khong phai bao loi, de demo khong chet giua chung."""
        if self.ai_off:
            return False
        if self.total_cap > 0 and self.spent_total() >= self.total_cap:
            if not self._warned_total:
                log.warning("Da dat tran cong don %.2f USD. Chuyen ve che do rule/template.", self.total_cap)
                self._warned_total = True
            return False
        if self.cap <= 0:
            return True
        over = self.spent_today() >= self.cap
        if over and not self._warned:
            log.warning("Da dat tran %.2f USD hom nay. Chuyen ve che do rule/template.", self.cap)
            self._warned = True
        return not over

    def track(self, purpose: str, model: str, usage: Any) -> float:
        """usage la response.usage cua SDK. Doc token that, khong uoc luong."""
        tin = int(getattr(usage, "input_tokens", 0) or 0)
        tout = int(getattr(usage, "output_tokens", 0) or 0)
        cr = int(getattr(usage, "cache_read_input_tokens", 0) or 0)
        cw = int(getattr(usage, "cache_creation_input_tokens", 0) or 0)
        usd = price_of(model, tin, tout, cr, cw)
        from datetime import datetime, timezone
        self.conn.execute(
            "INSERT INTO llm_calls(day,ts,purpose,model,input_tokens,output_tokens,cache_read,cache_write,usd) VALUES(?,?,?,?,?,?,?,?,?)",
            (self.today(), datetime.now(timezone.utc).isoformat(), purpose, model, tin, tout, cr, cw, usd))
        self.conn.commit()
        return usd

    # ---------- so lieu cho trang Cai dat: token va tien, khong chi rieng tien
    _CONG = ("COALESCE(SUM(input_tokens),0), COALESCE(SUM(output_tokens),0), "
             "COALESCE(SUM(cache_read),0), COALESCE(SUM(cache_write),0), "
             "COALESCE(SUM(usd),0), COUNT(*)")

    @staticmethod
    def _hang(r: Any) -> dict[str, Any]:
        vao, ra, cr, cw, usd, n = r
        return {"token_vao": int(vao), "token_ra": int(ra), "cache_doc": int(cr), "cache_ghi": int(cw),
                "token_tong": int(vao) + int(ra) + int(cr) + int(cw), "usd": round(float(usd), 6),
                "luot": int(n)}

    def tong(self, day: str | None = None) -> dict[str, Any]:
        """Token va tien. day=None nghia la cong don tu dong dau tien trong so."""
        if day is None:
            r = self.conn.execute(f"SELECT {self._CONG} FROM llm_calls").fetchone()
        else:
            r = self.conn.execute(f"SELECT {self._CONG} FROM llm_calls WHERE day=?", (day,)).fetchone()
        return self._hang(r)

    def theo_ngay(self, limit: int = 14) -> list[dict[str, Any]]:
        rows = self.conn.execute(
            f"SELECT day, {self._CONG} FROM llm_calls GROUP BY day ORDER BY day DESC LIMIT ?", (limit,)).fetchall()
        return [dict(ngay=r[0], **self._hang(r[1:])) for r in rows]

    def theo_viec(self, day: str | None = None) -> list[dict[str, Any]]:
        """Chia theo `purpose`, tuc theo viec ma model duoc goi de lam."""
        if day is None:
            rows = self.conn.execute(
                f"SELECT purpose, {self._CONG} FROM llm_calls GROUP BY purpose ORDER BY SUM(usd) DESC").fetchall()
        else:
            rows = self.conn.execute(
                f"SELECT purpose, {self._CONG} FROM llm_calls WHERE day=? GROUP BY purpose ORDER BY SUM(usd) DESC",
                (day,)).fetchall()
        return [dict(viec=r[0], **self._hang(r[1:])) for r in rows]

    def theo_model(self) -> list[dict[str, Any]]:
        rows = self.conn.execute(
            f"SELECT model, {self._CONG} FROM llm_calls GROUP BY model ORDER BY SUM(usd) DESC").fetchall()
        return [dict(model=r[0], **self._hang(r[1:])) for r in rows]

    def report(self, day: str | None = None) -> Spend:
        day = day or self.today()
        rows = self.conn.execute("SELECT purpose, SUM(usd) s, COUNT(*) c FROM llm_calls WHERE day=? GROUP BY purpose", (day,)).fetchall()
        by = {r[0]: float(r[1]) for r in rows}
        return Spend(sum(by.values()), sum(int(r[2]) for r in rows), by)
