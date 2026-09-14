"""MCP server cua tro ly (`POST /mcp`).

Dung hoi ngay 13/09/2026 vi sao bo cong cu chua la MCP. Test giu ba dieu:
  1. client MCP bat ky noi duoc: initialize, tools/list, tools/call theo JSON-RPC;
  2. ranh gioi khong doi: khong co tool tao chung tu; ghi de xuat bi chan theo ton nguon, di qua
     policy va day the cho nguoi duyet y het luong trong chat;
  3. goi tu may khac phai co khoa, va khoa gan voi mot nguoi dung.
"""
from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from assistant import mcp_server
from assistant.channels import web
from assistant.core import Assistant
from assistant.memory import Memory
from bc_agent.mock_client import MockBCClient


@pytest.fixture()
def asst(monkeypatch):
    a = Assistant(MockBCClient(), Memory(":memory:"))
    monkeypatch.setitem(web.state, "asst", a)
    return a


@pytest.fixture()
def c(asst, monkeypatch):
    monkeypatch.setenv("MCP_KEYS", "khoa-hung:hung.dieuphoi,khoa-lan:lan.s0001")
    return TestClient(web.app)


def rpc(c, method, params=None, id_=1, key="khoa-hung"):
    r = c.post("/mcp", json={"jsonrpc": "2.0", "id": id_, "method": method, "params": params or {}},
               headers={"x-api-key": key} if key else {})
    return r


def goi(c, ten, args, key="khoa-hung"):
    return rpc(c, "tools/call", {"name": ten, "arguments": args}, key=key).json()["result"]


def test_bat_tay_va_liet_ke_tool(c):
    r = rpc(c, "initialize", {"protocolVersion": "2025-06-18", "capabilities": {}, "clientInfo": {"name": "test"}})
    assert r.status_code == 200 and r.headers.get("mcp-session-id")
    assert r.json()["result"]["serverInfo"]["name"] == "marou-ops"
    assert c.post("/mcp", json={"jsonrpc": "2.0", "method": "notifications/initialized"},
                  headers={"x-api-key": "khoa-hung"}).status_code == 202
    ten = {t["name"] for t in rpc(c, "tools/list").json()["result"]["tools"]}
    assert {"stock_by_item", "sales_rate", "inventory_health_summary", "proposal_status", "create_proposal"} <= ten
    assert not ten & {"ask_human", "draft_proposal", "approve", "post"}, "khong duoc co tool duyet hay tao chung tu"


def test_schema_khong_dung_anyof(c):
    """Foundry bao 'Invalid tool schema' neu inputSchema co anyOf, allOf hoac mot tham so nhieu kieu."""
    for t in rpc(c, "tools/list").json()["result"]["tools"]:
        chu = str(t["inputSchema"])
        assert "anyOf" not in chu and "allOf" not in chu, t["name"]
        for p in t["inputSchema"].get("properties", {}).values():
            assert isinstance(p.get("type"), str), (t["name"], p)


def test_doc_so_qua_mcp(c, asst):
    ma = asst.gw.find_item("Choco nuts")["itemNo"]
    kq = goi(c, "stock_by_item", {"item_no": ma})
    assert not kq["isError"] and asst.gw.central_wh in kq["content"][0]["text"]
    tong = goi(c, "inventory_health_summary", {})
    assert not tong["isError"] and tong["structuredContent"]


def test_ghi_de_xuat_vuot_ton_bi_chan(c, asst):
    ma = asst.gw.find_item("Choco nuts")["itemNo"]
    kq = goi(c, "create_proposal", {"action_type": "Transfer", "item_no": ma, "to_location": "S0001",
                                    "quantity": 10_000_000, "rationale": "thu vuot ton"})
    assert kq["isError"] and "chỉ còn" in kq["content"][0]["text"]
    assert not asst.mem.proposals()


def test_ghi_de_xuat_hop_le_qua_policy_va_bao_nguoi_duyet(c, asst):
    ma = asst.gw.find_item("Choco nuts")["itemNo"]
    kq = goi(c, "create_proposal", {"action_type": "Transfer", "item_no": ma, "to_location": "S0001",
                                    "quantity": 5, "rationale": "S0001 sap het, kho con du"}, key="khoa-lan")
    assert not kq["isError"], kq
    d = kq["structuredContent"]
    assert d["status"] in ("Proposed", "Executed") and d["policy"]
    assert "hung.dieuphoi" in d["nguoi_duoc_bao"]
    the = [m for m in asst.mem.inbox("hung.dieuphoi", 0) if m["direction"] == "out" and m.get("card")]
    assert the, "nguoi duyet phai thay the trong hoi thoai"
    lap = goi(c, "create_proposal", {"action_type": "Transfer", "item_no": ma, "to_location": "S0001",
                                     "quantity": 5, "rationale": "lan hai"}, key="khoa-lan")
    assert lap["isError"] and "không ghi thêm" in lap["content"][0]["text"]


def test_vai_khong_duoc_ghi(c, asst, monkeypatch):
    monkeypatch.setenv("MCP_KEYS", "khoa-admin:dung.admin")
    ma = asst.gw.find_item("Choco nuts")["itemNo"]
    kq = goi(c, "create_proposal", {"action_type": "ReviewOnly", "item_no": ma, "quantity": 0,
                                    "rationale": "thu"}, key="khoa-admin")
    assert kq["isError"]


def test_goi_tu_may_khac_phai_co_khoa(c):
    assert rpc(c, "tools/list", key=None).status_code == 401
    assert rpc(c, "tools/list", key="sai").status_code == 401


def test_goi_tu_chinh_may_khong_can_khoa():
    assert mcp_server.nguoi_goi({}, "127.0.0.1") == "trang.sc"
    assert mcp_server.nguoi_goi({"X-Marou-User": "hung.dieuphoi"}, "127.0.0.1") == "hung.dieuphoi"
    assert mcp_server.nguoi_goi({}, "10.0.0.5") is None
