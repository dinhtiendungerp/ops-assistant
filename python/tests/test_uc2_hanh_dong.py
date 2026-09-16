"""UC2 D4 (16/09/2026): goi y hanh dong toi uu cho lo can date. Code tinh phuong an, model chon va giai thich, nguoi ghi de xuat."""
from __future__ import annotations

import pytest

from assistant.core import Assistant
from assistant.skills import uc2_hanh_dong as d4
from bc_agent.mock_client import MockBCClient
from tests.test_uc2_tom_tat import _ModelGia


@pytest.fixture()
def a():
    x = Assistant(MockBCClient())
    x.set_ai(False)
    return x


def _lo(a, ten="Choco pillar", noi="S0010"):
    return next(x for x in a.gw.doc("inventoryHealthLines", [], top=5000)
                if x["itemDescription"] == ten and x["locationCode"] == noi and x["tier"] == "NearExpiry")


def _bat_model(a, monkeypatch, tra):
    m = _ModelGia(tra)
    a._writer = m
    monkeypatch.setattr(a.budget, "allow", lambda: True)
    monkeypatch.setattr(a.budget, "track", lambda *x, **k: 0)
    return m


def test_chuyen_vua_du_khong_phai_ca_lo(a):
    r = _lo(a)
    pt = d4.phan_tich(a, r)
    # 470 cai, 25 ngay, ban 10.8/ngay: ban duoc 271 tai cho, du 199; S0001 ban nhanh hon nen nhan phan du
    assert pt["phuong_an"]["giu"]["ban_duoc_truoc_han"] == "271" and pt["_du"] == 199
    assert pt["_chuyen"] == [{"den": "S0001", "so_luong": 199, "ban_binh_quan_ngay": 21.2}]
    assert pt["de_xuat_cua_code"] == "chuyen" and pt["_du_sau_chuyen"] == 0
    # Kha nang nhan = ban binh quan cua ho x (ngay con lai - 1 ngay van chuyen) - ton ho dang co, lam tron xuong
    s1 = next(x for x in pt["noi_nhan"] if x["dia_diem"] == "S0001")
    assert s1["nhan_duoc_toi_da"] < 21.2 * 24


def test_khong_noi_nhan_thi_giam_gia_hoac_giu(a):
    pt = d4.phan_tich(a, _lo(a, "Tiramisu", "S0002"))      # con 2 ngay, khong cua hang nao con cho
    assert pt["de_xuat_cua_code"] == "giam_gia" and "chuyen" not in pt["phuong_an"]
    pt = d4.phan_tich(a, _lo(a, "Carrot cake", "W0003"))   # ban het truoc han
    assert pt["de_xuat_cua_code"] == "giu" and pt["_du"] == 0


def test_the_va_ghi_de_xuat_theo_phuong_an(a):
    r = _lo(a)
    u = a.mem.user("trang.sc")
    out = d4.on_goi_y(a, u, r["id"])
    c = out[0].card
    assert c.title.startswith("Phương án cho lô cận date") and ("Người soạn", "mẫu có sẵn (AI đang tắt)") in c.facts
    assert any(l.startswith("→ Chuyển vừa đủ") for l, _ in c.facts)
    assert c.actions[0].payload == {"chon": "chuyen"} and c.actions[1].payload == {"chon": "giam_gia"}
    ra = d4.on_ap_dung(a, u, r["id"], "chuyen")
    assert any("Đã ghi đề xuất Transfer" in d.text for d in ra) and any(d.user_id == "hung.dieuphoi" for d in ra)
    p = a.mem.proposals()[0]
    assert p["action_type"] == "Transfer" and p["to_loc"] == "S0001" and p["quantity"] == 199 and p["quantity"] < r["quantityOnHand"]
    assert p["channel_ref"].endswith("|TO|S0001") and p["value_vnd"] > 0
    # Giam gia phan du la de xuat rieng, khoa rieng, van ghi duoc du da co de xuat chuyen cua cung lo
    ra2 = d4.on_ap_dung(a, u, r["id"], "giam_gia")
    assert any("Đã ghi đề xuất Markdown" in d.text for d in ra2)
    assert {p["action_type"] for p in a.mem.proposals()} == {"Transfer", "Markdown"}


def test_lo_het_han_khong_co_phuong_an(a):
    r = next(x for x in a.gw.doc("inventoryHealthLines", [], top=5000) if x["tier"] == "Expired")
    out = d4.on_goi_y(a, a.mem.user("trang.sc"), r["id"])
    assert "đã hết hạn" in out[0].text and out[0].card is None


def test_model_chon_khac_code_va_dung_so_thi_theo_model(a, monkeypatch):
    r = _lo(a)
    m = _bat_model(a, monkeypatch, {"chon": "giam_gia", "vi_sao": "Tôi chọn giảm giá 199 cái tại S0010 vì đơn giản hơn chuyển sang S0001."})
    kq = d4.goi_y(a, r["id"])
    assert kq["chon"] == "giam_gia" and kq["nguoi_soan"].startswith("AI") and not kq["nho_lai"]
    assert d4.goi_y(a, r["id"])["nho_lai"] and m.so_lan == 1
    c = d4.the_phuong_an(kq)
    assert c.actions[0].payload == {"chon": "giam_gia"} and any(l.startswith("→ Giảm giá") for l, _ in c.facts)


def test_model_bia_so_hoac_chon_la_thi_dung_mau(a, monkeypatch):
    r = _lo(a)
    _bat_model(a, monkeypatch, {"chon": "chuyen", "vi_sao": "Chuyển 500 cái."})
    kq = d4.goi_y(a, r["id"])
    assert kq["chon"] == "chuyen" and "500" in kq["nguoi_soan"] and "500" not in kq["vi_sao"]
    _bat_model(a, monkeypatch, {"chon": "dung_noi_bo", "vi_sao": "Dùng nội bộ."})
    kq = d4.goi_y(a, r["id"])
    assert "không có trong bảng" in kq["nguoi_soan"] and kq["chon"] == "chuyen"


def test_api_phuong_an(a):
    from fastapi.testclient import TestClient
    from assistant.channels import web
    web.state["asst"] = a
    kq = TestClient(web.app).get("/api/uc2/phuong-an", params={"line_id": _lo(a)["id"]}).json()
    assert kq["chon"] == "chuyen" and "chuyen" in kq["phan_tich"]["phuong_an"] and not any(k.startswith("_") for k in kq["phan_tich"])


def test_model_tra_ten_phuong_an_thay_vi_khoa_van_nhan(a, monkeypatch):
    r = _lo(a)
    _bat_model(a, monkeypatch, {"chon": "Chuyển vừa đủ sang cửa hàng bán nhanh hơn", "vi_sao": "S0001 nhận 199."})
    kq = d4.goi_y(a, r["id"])
    assert kq["chon"] == "chuyen" and kq["nguoi_soan"].startswith("AI")
