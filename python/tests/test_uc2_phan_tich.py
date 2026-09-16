"""UC2 D3 bat thuong, D2 nguyen nhan huy, S3 bao cao tuan hang huy (16/09/2026). Code tinh, model chi viet loi, kiem so."""
from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from assistant import thu_dien_tu as td
from assistant.core import Assistant
from assistant.nlu import RuleNLU
from assistant.skills import uc2_bao_cao_huy as s3
from assistant.skills import uc2_bat_thuong as d3
from assistant.skills import uc2_nguyen_nhan as d2
from bc_agent.mock_client import MockBCClient
from tests.test_uc2_tom_tat import _ModelGia


@pytest.fixture()
def a():
    x = Assistant(MockBCClient())
    x.set_ai(False)
    return x


def _bat_model(a, monkeypatch, tra):
    m = _ModelGia(tra)
    a._writer = m
    monkeypatch.setattr(a.budget, "allow", lambda: True)
    monkeypatch.setattr(a.budget, "track", lambda *x, **k: 0)
    return m


# ---------------------------------------------------------------- NLU
@pytest.mark.parametrize("cau,intent,item,noi", [
    ("có gì bất thường trong 28 ngày qua không", "ANOMALY", "", ""),
    ("vì sao Chocolate cake hủy nhiều", "WASTE_WHY", "Chocolate cake", ""),
    ("vì sao S0002 hủy nhiều thế", "WASTE_WHY", "", "S0002"),
    ("báo cáo tuần hàng hủy", "WASTE_REPORT", "", ""),
    ("vì sao LS đề xuất Choco nuts cho S0001", "REPLEN_WHY", "Choco nuts", ""),
    ("có mặt hàng nào đã hết hạn chưa", "EXPIRY", "", ""),
])
def test_nlu_ba_intent_moi(cau, intent, item, noi):
    i = RuleNLU().parse(cau)
    assert i.intent == intent and i.item_text == item and (i.store_hint or "") == noi


# ---------------------------------------------------------------- D3
def test_d3_quet_ra_tin_hieu_co_so_va_nguon(a):
    kq = d3.quet(a)
    assert kq["tin_hieu"] and all(t["id"] and t["cau"] and t["so"] for t in kq["tin_hieu"])
    assert kq["theo_loai"]["Nhận hàng hạn quá ngắn"] > 0          # bo demo: banh tuoi ve cua hang con 0-1 ngay han
    assert kq["theo_loai"]["Bán sau hạn dùng"] == 0                 # bo demo khong co
    assert all(not a.gw.la_kho(t["dia_diem"]) for t in kq["tin_hieu"])
    assert kq["khong_lam_duoc"]


def test_d3_theo_cua_hang_va_the(a):
    kq = d3.goi_y(a, noi="S0001")
    assert all(t["dia_diem"] == "S0001" for t in kq["tin_hieu"]) and kq["nguoi_soan"] == "mẫu có sẵn (AI đang tắt)"
    c = d3.the_bat_thuong(kq)
    assert c.title.endswith("ngày") and c.body and any(l.startswith("Sổ kho") for l, _ in c.links)
    out = a.handle_message("lan.s0001", "có gì bất thường không")
    assert out[0].card and "S0001" in out[0].text


def test_d3_model_chon_id_va_dung_so(a, monkeypatch):
    kq = d3.quet(a)
    ids = [t["id"] for t in kq["tin_hieu"][:2]]
    m = _bat_model(a, monkeypatch, {"uu_tien": ids + ["T999"], "nhan_xet": f"Tôi thấy {ids[0]} đáng xem trước."})
    kq2 = d3.goi_y(a)
    assert kq2["uu_tien"] == ids and kq2["nguoi_soan"].startswith("AI")
    assert d3.goi_y(a)["nho_lai"] and m.so_lan == 1
    b = Assistant(MockBCClient())                      # tro ly moi: ban nho theo ngay cua `a` da giu ket qua AI o tren
    _bat_model(b, monkeypatch, {"uu_tien": ids, "nhan_xet": "Có 777 tín hiệu."})
    kq3 = d3.goi_y(b)
    assert "777" in kq3["nguoi_soan"] and "777" not in kq3["nhan_xet"]


# ---------------------------------------------------------------- D2
def test_d2_phan_tich_gan_nguyen_nhan(a):
    pt = d2.phan_tich(a)
    assert pt["so_nhom"] > 5 and pt["nhom"][0]["huy"] and pt["nhom"][0]["nguyen_nhan"]
    n = pt["nhom"][0]
    assert n["nhan_so_voi_ban"] > 1.25 and "nhận dư so với bán" in n["nguyen_nhan"]
    # "don cuc" khong duoc bat gan het cac cap
    assert pt["nguyen_nhan_pho_bien"].get("nhận dồn cục vượt sức bán trong hạn", 0) < pt["so_nhom"]
    theo_cua_hang = d2.phan_tich(a, noi="S0002")
    assert theo_cua_hang["nhom"] and all(x["dia_diem"] == "S0002" for x in theo_cua_hang["nhom"])
    theo_ma = d2.phan_tich(a, item_no="33170")
    assert theo_ma["nhom"] and all(x["ma"] == "33170" for x in theo_ma["nhom"])


def test_d2_chat_theo_mat_hang_va_cua_hang_cua_minh(a):
    out = a.handle_message("trang.sc", "vì sao Chocolate cake hủy nhiều")
    c = out[0].card
    assert c.title == "Nguyên nhân hàng hủy: Chocolate cake" and ("Người soạn", "mẫu có sẵn (AI đang tắt)") in c.facts
    out = a.handle_message("lan.s0001", "vì sao cửa hàng tôi hủy nhiều")
    assert out[0].card.title == "Nguyên nhân hàng hủy: S0001"


def test_d2_model_bia_so_thi_dung_mau(a, monkeypatch):
    _bat_model(a, monkeypatch, {"ket_luan": "Hủy 9999 cái do nhận dư."})
    kq = d2.goi_y(a)
    assert "9999" in kq["nguoi_soan"] and "9999" not in kq["ket_luan"]


# ---------------------------------------------------------------- S3
def test_s3_so_lieu_va_bao_cao(a):
    d = s3.so_lieu(a)
    assert d["lo_het_han_con_ton"]["so_lo"] == 45 and d["tuan_truoc"]["so_luong"] != "0"
    bc = s3.soan(a)
    assert bc["tieu_de"].startswith("Báo cáo tuần hàng hủy") and "Lô hết hạn còn tồn: 45 lô" in bc["text"]
    out = s3.gui(a, a.mem.user("trang.sc"))
    assert {d_.user_id for d_ in out} >= {"trang.sc", "dung.admin"} and out[0].card.kind == "brief"
    assert td.gan_day(1)[0]["loai"] == "bao_cao_huy"
    # Lan hai trong tuan khong gui lai email
    out2 = s3.gui(a, a.mem.user("trang.sc"))
    assert any(v.startswith("đã gửi hôm nay") for l, v in out2[0].card.facts if l == "Email")


def test_s3_chat_va_quyen(a):
    assert a.handle_message("trang.sc", "báo cáo tuần hàng hủy")[0].card.title.startswith("Báo cáo tuần")
    out = a.handle_message("lan.s0001", "báo cáo tuần hàng hủy")
    assert out[0].card is None and "Supply Chain" in out[0].text


def test_api_ba_duong(a):
    from assistant.channels import web
    web.state["asst"] = a
    c = TestClient(web.app)
    assert c.get("/api/uc2/bat-thuong").json()["tin_hieu"]
    assert c.get("/api/uc2/nguyen-nhan-huy", params={"noi": "S0002"}).json()["nhom"]
    kq = c.post("/api/bao-cao-huy", json={"user": "dung.admin"}).json()
    assert "dung.admin" in kq["delivered"]
