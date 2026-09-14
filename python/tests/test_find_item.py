"""Do ten mat hang phai khong phan biet hoa thuong va chiu duoc viet lien.

Ly do co file nay: ban dau find_item de rapidfuzz so nguyen van, nen "Mini bar" duoc 100 diem
con "mini bar" chi duoc 54, duoi nguong 60. Tro ly chi nhan ra mat hang khi nguoi dung go dung
chu hoa. Loi nay chi lo ra khi co nguoi go tay trong buoi demo, khong test nao bat duoc.
"""
from __future__ import annotations

import pytest

from assistant.gateway import BCGateway
from bc_agent.mock_client import MockBCClient


@pytest.fixture()
def gw():
    return BCGateway(MockBCClient())


@pytest.mark.parametrize("text", [
    "Choco nuts", "choco nuts", "CHOCO NUTS", "choconuts",
    "sắp hết choco nuts", "sap het choconuts", "33323",
])
def test_moi_cach_go_deu_ra_choco_nuts(gw, text):
    hit = gw.find_item(text)
    assert hit is not None, f"khong nhan ra {text!r}"
    assert hit["itemNo"] == "33323"


@pytest.mark.parametrize("text,item_no", [
    ("chocolate ice cream", "33200"),
    ("VANILLA ICE CREAM", "33250"),
    ("tiramisu", "33130"),
    ("pecan pie", "33120"),
    ("carrot cake", "33160"),
    ("flavored syrup", "30091"),
    ("frozen waffles", "18120"),
    ("milk 1 liter", "10000"),
])
def test_cac_mat_hang_khac(gw, text, item_no):
    hit = gw.find_item(text)
    assert hit is not None and hit["itemNo"] == item_no


@pytest.mark.parametrize("text", [
    "xe máy", "cà phê sữa", "abcxyz", "hôm nay trời đẹp", "sếp đổi ý",
])
def test_cau_khong_phai_ten_hang_thi_tra_ve_none(gw, text):
    """Noi long nguong de bat duoc chu viet lien khong duoc keo theo viec doan bua."""
    assert gw.find_item(text) is None
