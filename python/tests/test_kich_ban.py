"""Cau ngoai kich ban thanh kich ban da duyet.

Dung hoi ngay 13/09/2026: khach se noi 80% cau hoi la ngoai kich ban, muon chuyen hoa cau ngoai
kich ban thanh kich ban thi sao. Test giu bon dieu:
  1. con so trong mau phai truy duoc ve ket qua tool, so model tu tinh thi bao ra;
  2. cau tuong tu khac mat hang chay kich ban ma khong goi model, so dung cho mat hang moi;
  3. khong du bien, khac nghia, hoac khong doc ra so thi tra cau hoi ve model;
  4. chi quan tri luu duoc kich ban.
"""
from __future__ import annotations

import pytest

from assistant import kich_ban
from assistant.core import Assistant
from assistant.memory import Memory
from assistant.planner import Plan, Step, _fmt
from assistant.toolbox import run_tool
from bc_agent.mock_client import MockBCClient

CAU = "tình hình {} trên toàn hệ thống thế nào"


@pytest.fixture()
def asst():
    return Assistant(MockBCClient(), Memory(":memory:"))


def _hai_mat_hang(asst):
    """Hai mat hang co ban va co ton o kho trung tam, de cau tra loi co du so."""
    ra = []
    for it in asst.gw.items():
        rows = asst.gw.stock_by_location(it["itemNo"])
        ban = run_tool(asst, {}, "sales_rate", {"item_no": it["itemNo"], "days": 90})
        if any(r["locationCode"] == asst.gw.central_wh for r in rows) and ban["totalQty"] > 0:
            ra.append(it)
        if len(ra) == 2:
            return ra
    pytest.skip("mock khong du hai mat hang")


def _tra_loi_kieu_model(asst, it):
    """Dung dung cai model se lam: goi hai tool roi viet cau co so. Mot so tu tinh (so ngay)."""
    ton = run_tool(asst, {}, "stock_by_item", {"item_no": it["itemNo"]})
    ban = run_tool(asst, {}, "sales_rate", {"item_no": it["itemNo"], "days": 90})
    tong = sum(r["qty"] for r in ton)
    kho = next(r["qty"] for r in ton if r["locationCode"] == asst.gw.central_wh)
    tu_tinh = round(tong / ban["avgPerCalendarDay"]) + 1000          # so khong nam trong ket qua nao
    cau = (f"{it['description']} ({it['itemNo']}) đang có tổng {_fmt(round(tong))} ở {len(ton)} địa điểm, "
           f"kho W0003 giữ {_fmt(round(kho))}. 90 ngày qua bán {_fmt(round(ban['totalQty']))}, "
           f"bình quân {_fmt(round(ban['avgPerCalendarDay'], 1))} mỗi ngày, đủ khoảng {_fmt(tu_tinh)} ngày.")
    buoc = [{"tool": "stock_by_item", "args": {"item_no": it["itemNo"]}, "why": "", "result": ton},
            {"tool": "sales_rate", "args": {"item_no": it["itemNo"], "days": 90}, "why": "", "result": ban}]
    return cau, buoc, {"tong": tong, "kho": kho, "ban": ban}


def _ghi_cau_model(asst, it):
    cau_tl, buoc, so = _tra_loi_kieu_model(asst, it)
    user = asst.mem.user("trang.sc")
    id_ = kich_ban.ghi_cau_hoi(user, CAU.format(it["description"]), "model", asst.gw, buoc, cau_tl,
                               ref="PLAN-TEST01", token=1800, usd=0.0012)
    return id_, cau_tl, so


def test_lap_mau_truy_so_ve_ket_qua_va_bao_so_tu_tinh(asst):
    a, _ = _hai_mat_hang(asst)
    id_, _, _ = _ghi_cau_model(asst, a)
    mau = kich_ban.xem_truoc(id_, asst.gw)
    assert "{item_desc}" in mau["tra_loi_mau"] and "{item_no}" in mau["tra_loi_mau"]
    assert mau["bien_can"] == ["item_desc", "item_no"]
    assert len(mau["slots"]) == 5, mau["slots"]         # tong, so dia diem, kho, da ban, binh quan
    assert mau["slots"]["s2"]["path"] == "@len"
    assert "90 ngày" in mau["tra_loi_mau"], "tham so 90 ngay la hang so, khong phai o ket qua"
    assert len(mau["canh_bao"]) == 1 and "ngày" in mau["canh_bao"][0]
    assert all("{item_no}" in s["args"].get("item_no", "{item_no}") for s in mau["buoc"])


def test_hai_o_cung_gia_tri_thi_gan_theo_dia_diem_nhac_gan_nhat():
    """Chay that ngay 13/09/2026: S0005 va S0010 cung 9,1 ngay, so cua S0010 bi gan vao o S0005."""
    ket_qua = [{"locationCode": "S0005", "qty": 52.0, "daysOfCover": 9.1},
               {"locationCode": "S0010", "qty": 74.0, "daysOfCover": 9.1}]
    buoc = [{"tool": "stock_by_item", "args": {"item_no": "33323"}, "result": ket_qua}]
    cau = "- S0005 tồn 52, đủ 9.1 ngày\n- S0010 tồn 74, đủ 9.1 ngày"
    mau = kich_ban.lap_mau(cau, buoc, {"item_no": "33323", "item_desc": "Choco nuts"}, {"33323"})
    duong = [s["path"] for s in mau["slots"].values()]
    assert duong == ["#locationCode=S0005.qty", "#locationCode=S0005.daysOfCover",
                     "#locationCode=S0010.qty", "#locationCode=S0010.daysOfCover"]


def test_cau_ket_luan_co_dinh_phai_duoc_bao():
    """Kich ban dien lai so chu khong suy luan lai: "ban cham nhat la S0005" se lap nguyen chu."""
    buoc = [{"tool": "stock_by_item", "args": {"item_no": "33323"},
             "result": [{"locationCode": "S0005", "avgDaily": 5.7}]}]
    mau = kich_ban.lap_mau("S0005 bán 5.7 mỗi ngày. Địa điểm bán chậm nhất là S0005.", buoc,
                           {"item_no": "33323", "item_desc": "Choco nuts"}, {"33323"})
    assert any("chậm nhất" in c for c in mau["canh_bao"])


def test_cau_tuong_tu_khac_mat_hang_chay_kich_ban_khong_goi_model(asst, monkeypatch):
    a, b = _hai_mat_hang(asst)
    id_, _, _ = _ghi_cau_model(asst, a)
    kb = kich_ban.luu(id_, asst.gw, "Dũng")
    assert kb["id"] == "K-001"

    def cam_goi(*_a, **_k):
        raise AssertionError("da goi planner cho cau khop kich ban")
    monkeypatch.setattr(asst.planner, "run", cam_goi)

    out = asst.handle_message("lan.s0001", CAU.format(b["description"]) + " nhé")
    assert len(out) == 1 and out[0].card is not None
    _, _, so = _tra_loi_kieu_model(asst, b)
    tl = out[0].text
    assert b["description"] in tl and a["description"] not in tl
    assert _fmt(round(so["tong"])) in tl and _fmt(round(so["ban"]["totalQty"])) in tl
    assert any("K-001" in v for _, v in out[0].card.facts)

    ds = kich_ban.danh_sach()
    assert ds[0]["so_lan_chay"] == 1 and ds[0]["token_tiet_kiem"] == 1800


def test_khong_du_bien_hoac_khac_nghia_thi_ve_model(asst, monkeypatch):
    a, _ = _hai_mat_hang(asst)
    id_, _, _ = _ghi_cau_model(asst, a)
    kich_ban.luu(id_, asst.gw, "Dũng")
    assert kich_ban.khop("tình hình mặt hàng hôm qua trên toàn hệ thống thế nào", asst.gw) is None
    assert kich_ban.khop(f"tháng sau mở cửa hàng Nha Trang thì đẩy bao nhiêu {a['description']}", asst.gw) is None

    goi = []
    monkeypatch.setattr(asst.planner, "run", lambda *x, **k: goi.append(1) or None)
    asst.handle_message("trang.sc", "tình hình mặt hàng hôm qua trên toàn hệ thống thế nào")
    assert goi, "cau khong du bien phai di tiep sang planner"


def test_khong_doc_ra_so_tren_du_lieu_moi_thi_bo_kich_ban(asst):
    a, b = _hai_mat_hang(asst)
    id_, _, _ = _ghi_cau_model(asst, a)
    kb = kich_ban.luu(id_, asst.gw, "Dũng")
    # Lam hong mot o: tro vao dia diem khong ton tai.
    kb["slots"]["s1"]["path"] = "#locationCode=KHONGCO.qty"
    plan, ly_do = kich_ban.chay(kb, asst, asst.mem.user("trang.sc"), kich_ban.tim_bien(CAU.format(b["description"]), asst.gw))
    assert plan is None and "s1" in ly_do


def test_tat_kich_ban_thi_khong_khop(asst):
    a, b = _hai_mat_hang(asst)
    kb = kich_ban.luu(_ghi_cau_model(asst, a)[0], asst.gw, "Dũng")
    kich_ban.bat_tat(kb["id"], False)
    assert kich_ban.khop(CAU.format(b["description"]), asst.gw) is None


def test_mau_sua_tay_khong_duoc_them_cho_trong_la(asst):
    a, _ = _hai_mat_hang(asst)
    id_, _, _ = _ghi_cau_model(asst, a)
    with pytest.raises(ValueError):
        kich_ban.luu(id_, asst.gw, "Dũng", "Tồn {s1}, lãi {loi_nhuan}")


def test_cau_bi_bao_sai_khong_duoc_de_nghi_luu(asst):
    a, _ = _hai_mat_hang(asst)
    _ghi_cau_model(asst, a)
    kich_ban.danh_gia("PLAN-TEST01", False)
    nhom = kich_ban.nhom_cau_hoi()
    assert nhom[0]["sai"] == 1 and nhom[0]["luu_duoc_tu"] is None


def test_nut_danh_gia_tren_the(asst, monkeypatch):
    a, b = _hai_mat_hang(asst)
    kich_ban.luu(_ghi_cau_model(asst, a)[0], asst.gw, "Dũng")
    out = asst.handle_message("trang.sc", CAU.format(b["description"]))
    asst.handle_action("trang.sc", "plan_bad", out[0].card.ref, {})
    assert kich_ban.danh_sach()[0]["sai"] == 1


def test_model_phan_loai_plan_thi_di_planner_va_loi_model_khong_sap(asst, monkeypatch):
    """Hai loi bat duoc khi chay that 13/09/2026: cau mo co ten mat hang bi ep vao STOCK_QUERY nen
    planner khong chay; va Azure 429 lam sap ca request thanh loi 500."""
    from assistant.nlu import Intent

    monkeypatch.setattr(asst.nlu, "parse", lambda *a, **k: Intent("PLAN", "Choco nuts"))

    def qua_tai(*_a, **_k):
        raise RuntimeError("HTTP 429 tu Azure OpenAI: rate_limit_exceeded")
    monkeypatch.setattr(asst.planner, "run", qua_tai)
    out = asst.handle_message("trang.sc", "so sánh tốc độ bán Choco nuts giữa các cửa hàng")
    assert "hạn mức token" in out[0].text
    assert kich_ban.nhom_cau_hoi()[0]["khong_tra_loi"] == 1


def test_api_chi_quan_tri_luu_duoc_kich_ban(asst, monkeypatch):
    from fastapi.testclient import TestClient

    from assistant.channels import web

    monkeypatch.setitem(web.state, "asst", asst)
    a, _ = _hai_mat_hang(asst)
    id_, _, _ = _ghi_cau_model(asst, a)
    c = TestClient(web.app)
    assert c.post("/api/kich-ban", json={"user": "trang.sc", "cau_hoi_id": id_}).status_code == 403
    r = c.post("/api/kich-ban/xem-truoc", json={"user": "dung.admin", "cau_hoi_id": id_})
    assert r.status_code == 200 and r.json()["slots"]
    assert c.post("/api/kich-ban", json={"user": "dung.admin", "cau_hoi_id": id_}).json()["id"] == "K-001"
    assert c.get("/api/nhat-ky?user=trang.sc").status_code == 403
    d = c.get("/api/nhat-ky?user=dung.admin").json()
    assert d["tong"]["kich_ban_bat"] == 1 and d["cau_hoi"] and "quyet_dinh" in d


def test_so_gan_nham_dia_diem_bi_bao():
    """Cau tra loi that cua planner ngay 14/09/2026 (Azure gpt-4.1-mini, BC NWV01): "S0010 ... ton 2 chai" trong khi
    list_stock S0010 khong co Flavored syrup; so 2 la ton cua S0005. Cac so con lai deu dung dia diem."""
    import json
    from pathlib import Path

    from assistant import kich_ban as kb

    d = json.loads((Path(__file__).parent / "data_so_sai_dia_diem.json").read_text(encoding="utf-8"))
    sai = kb.so_sai_dia_diem(d["tra_loi"], d["buoc"])
    assert len(sai) == 1 and "S0010" in sai[0] and "“2”" in sai[0]
    dung = d["tra_loi"].replace("S0010: 0.6 chai/ngày, tồn 2 chai", "S0010: 0.6 chai/ngày, chưa thấy tồn")
    assert kb.so_sai_dia_diem(dung, d["buoc"]) == []
