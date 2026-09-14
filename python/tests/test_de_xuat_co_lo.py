"""De xuat huy va giam gia theo lo phai mang so lo len BC.

Ngay 14/09/2026 Dung thay de xuat Write-off 33100 tai W0003 trong BC khong co Lot No.: gateway ghi cung `lotNo = ""`.
Nguoi duyet khong biet huy lo nao, trong khi 33100 tai W0003 co nam lo, ba lo da het han.
"""
from __future__ import annotations

from collections import Counter

from assistant.core import Assistant
from assistant.skills import inventory_health
from bc_agent.mock_client import MockBCClient


def _hai_lo_cung_cho(client: MockBCClient):
    rows = [r for r in client.data["inventoryHealthLines"] if r.get("lotNo")]
    dem = Counter((r["itemNo"], r["locationCode"]) for r in rows)
    cap = next(k for k, n in dem.items() if n >= 2)
    return [r for r in rows if (r["itemNo"], r["locationCode"]) == cap][:2]


def test_de_xuat_huy_ghi_so_lo_va_khong_chan_lo_thu_hai():
    client = MockBCClient()
    a = Assistant(client)
    user = a.mem.user("trang.sc")
    lo1, lo2 = _hai_lo_cung_cho(client)

    inventory_health.on_propose(a, user, lo1["id"], "WriteOff")
    inventory_health.on_propose(a, user, lo2["id"], "WriteOff")

    ghi = [w["body"] for w in client.writes if w["op"] == "create" and w["entity"] == "agentProposals"]
    assert [b["lotNo"] for b in ghi] == [lo1["lotNo"], lo2["lotNo"]]


def test_bam_lai_cung_lo_thi_khong_ghi_them():
    client = MockBCClient()
    a = Assistant(client)
    user = a.mem.user("trang.sc")
    lo1, _ = _hai_lo_cung_cho(client)

    inventory_health.on_propose(a, user, lo1["id"], "WriteOff")
    out = inventory_health.on_propose(a, user, lo1["id"], "WriteOff")

    ghi = [w for w in client.writes if w["op"] == "create" and w["entity"] == "agentProposals"]
    assert len(ghi) == 1 and "Đã có đề xuất đang chờ" in out[0].text
