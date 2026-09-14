"""UC3: bao don mua qua ngay nhan du kien ma chua nhan. Khong goi model, khong post nhan hang.

Tu 14/09/2026 fixtures `purchase_order_lines.json` sinh tu cung ke hoach don mua da tao tren BC (tools/supplier_demo.py),
nen mock va BC that ra cung don. Ngay neo 18/09/2026:
  NCC-MO-01 W0003  30091 x36, 18200 x48, hen 08/09   -> tre 10 ngay
  NCC-MO-02 W0003  33200 x60, 33250 x48, hen 15/09   -> tre 3 ngay
  NCC-MO-04 S0001  10070 x36, hen 13/09              -> tre 5 ngay
  NCC-MO-03 S0005  hen 18/09, NCC-MO-05 S0010 hen 18/09 -> CHUA qua han (bang ngay neo)
  HO106122  S0001  Cronus 2024                        -> don treo, khong hoi cua hang
  NCC-0001.. lich su da nhan du                       -> khong bao
"""
from __future__ import annotations

import pytest

from assistant.core import Assistant
from assistant.nlu import RuleNLU
from assistant.skills import po_qua_han as pq
from bc_agent.mock_client import MockBCClient


@pytest.fixture()
def asst():
    return Assistant(MockBCClient())


@pytest.mark.parametrize("cau", [
    "PO nào quá hạn chưa nhận?", "đơn mua nào chưa nhận hàng", "hàng mua chưa về",
    "có PO nào trễ không", "tổng hợp PO quá hạn",
])
def test_rule_nhan_ra_cau_hoi(cau):
    assert RuleNLU().parse(cau).intent == "PO_OVERDUE"


@pytest.mark.parametrize("cau,intent", [("tiến độ đề xuất của tôi", "TRACKING"), ("brief", "BRIEF"),
                                        ("sắp hết Croissant plain", "STOCKOUT")])
def test_khong_cuop_intent_cu(cau, intent):
    assert RuleNLU().parse(cau).intent == intent


def test_chi_lay_dong_con_so_luong_va_da_qua_ngay(asst):
    dong = pq.dong_qua_han(asst)
    so_don = {r["documentNo"] for r in dong}
    assert so_don == {"NCC-MO-01", "NCC-MO-02", "NCC-MO-04", "HO106122"}
    assert not so_don & {"NCC-MO-03", "NCC-MO-05"}                  # hen dung ngay neo chua qua han
    assert not [r for r in dong if r["documentNo"].startswith("NCC-0")]   # lich su da nhan du
    tre = {r["documentNo"]: r["so_ngay_tre"] for r in dong}
    assert tre["NCC-MO-01"] == 10 and tre["NCC-MO-02"] == 3 and tre["NCC-MO-04"] == 5


def test_gom_theo_don_va_nhan_mot_phan(asst):
    don = {d["so_don"]: d for d in pq.gom_theo_don(pq.dong_qua_han(asst))}
    assert len(don["NCC-MO-01"]["dong"]) == 2 and not don["NCC-MO-01"]["nhan_mot_phan"]
    # Nhan mot phan: du lieu gia, vi don mo tren BC khong nhan phan nao (nhan hang lam doi ton UC2)
    dong = [{"documentNo": "X1", "locationCode": "S0002", "lineNo": 10000, "itemNo": "10000", "description": "",
             "quantity": 80, "outstandingQuantity": 30, "quantityReceived": 50, "expectedReceiptDate": "2026-09-15",
             "buyFromVendorNo": "44030", "so_ngay_tre": 3}]
    assert pq.gom_theo_don(dong)[0]["nhan_mot_phan"]


def test_supply_chain_thay_het_va_tro_ly_hoi_noi_nhan_mot_lan(asst):
    out = asst.handle_message("trang.sc", "PO nào quá hạn chưa nhận?")
    assert "4 đơn mua" in out[0].text and "không post" in out[0].text
    hoi = [d for d in out if d.user_id != "trang.sc"]
    assert {d.user_id for d in hoi} == {"lan.s0001", "kho.w0003"}
    assert all(d.card and [a.id for a in d.card.actions] == ["po_da_ve", "po_chua_ve"] for d in hoi)
    assert not [d for d in hoi if d.ref.startswith("HO106122")]      # don treo khong hoi cua hang
    lai = asst.handle_message("trang.sc", "PO nào quá hạn chưa nhận?")
    assert not [d for d in lai if d.user_id != "trang.sc"], "hoi lai lan hai khong duoc gui them the"


def test_cua_hang_chi_thay_don_cua_minh(asst):
    out = asst.handle_message("lan.s0001", "đơn mua nào chưa nhận hàng")
    the = [d.card for d in out if d.card]
    assert {c.ref for c in the} == {"NCC-MO-04|S0001", "HO106122|S0001"}
    assert not asst.handle_message("minh.s0002", "đơn mua nào chưa nhận hàng")[0].card


def test_xac_nhan_hang_da_ve_bao_supply_chain_va_khong_tao_chung_tu(asst):
    out = asst.handle_action("lan.s0001", "po_da_ve", "NCC-MO-04|S0001", {})
    sc = [d for d in out if d.user_id == "trang.sc"]
    assert sc and "post Receive" in sc[0].text and "36 đơn vị" in sc[0].text
    assert asst.gw.client.writes == []                               # khong ghi gi vao BC
    lan2 = asst.handle_action("lan.s0001", "po_chua_ve", "NCC-MO-04|S0001", {})
    assert "đã có người xác nhận" in lan2[0].text
    the = [d.card for d in asst.handle_message("trang.sc", "PO nào quá hạn") if d.card and d.card.ref == "NCC-MO-04|S0001"][0]
    assert "Lan báo hàng đã về" in the.body and not the.actions


def test_nguoi_khac_dia_diem_khong_xac_nhan_duoc(asst):
    out = asst.handle_action("minh.s0002", "po_da_ve", "NCC-MO-04|S0001", {})
    assert "Chỉ người nhận hàng" in out[0].text


def test_brief_co_mot_dong_don_mua_qua_han(asst):
    out = asst.morning_brief("kho.w0003")
    assert any("NCC-MO-01" in d.text for d in out)
    assert "chờ ship" in out[0].text                                  # brief cu van o dau


def test_mcp_tool(asst):
    from assistant import mcp_server

    user = asst.mem.user("trang.sc")
    kq = mcp_server.goi_tool(asst, user, "overdue_purchase_orders", {"location": "S0001"})
    assert not kq.get("isError")
    assert "NCC-MO-04" in kq["content"][0]["text"] and "NCC-MO-01" not in kq["content"][0]["text"]
