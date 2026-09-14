"""Trang Cai dat: dem token, uoc tinh tien, va cong tac bat tat AI.

Ly do co file nay: Dung phai tu kiem soat duoc chi phi va tu tat AI khi can, khong phai nho
NaviWorld sua `.env` roi khoi dong lai. Ba thu de vo tham lang neu khong co test:
so token bi dem lech, tat AI ma model van bi goi, va bat AI khi chua co credential thi
`validate_live_llm` nem SystemExit lam chet ca server.
"""
from __future__ import annotations

import sqlite3
from types import SimpleNamespace

import pytest
from fastapi.testclient import TestClient

from assistant.budget import Budget


class _Usage(SimpleNamespace):
    pass


def _budget() -> Budget:
    return Budget(sqlite3.connect(":memory:"), daily_cap_usd=2, total_cap_usd=10)


def _ghi(b: Budget, purpose: str, tin: int, tout: int) -> None:
    b.track(purpose, "gpt-4.1-mini", _Usage(input_tokens=tin, output_tokens=tout))


# ---------------------------------------------------------------- dem token


def test_tong_cong_ca_bon_loai_token():
    b = _budget()
    b.track("nlu", "gpt-4.1-mini",
            _Usage(input_tokens=100, output_tokens=20, cache_read_input_tokens=300,
                   cache_creation_input_tokens=40))
    t = b.tong()
    assert (t["token_vao"], t["token_ra"], t["cache_doc"], t["cache_ghi"]) == (100, 20, 300, 40)
    assert t["token_tong"] == 460          # tong phai gom ca cache, khong chi vao cong ra
    assert t["luot"] == 1


def test_theo_viec_xep_theo_tien_giam_dan():
    b = _budget()
    _ghi(b, "nlu", 100, 10)
    _ghi(b, "planner", 5000, 3000)
    _ghi(b, "nlu", 100, 10)
    rows = b.theo_viec()
    assert [r["viec"] for r in rows] == ["planner", "nlu"]
    assert rows[1]["luot"] == 2 and rows[1]["token_vao"] == 200


def test_theo_ngay_gom_dung_mot_dong_cho_hom_nay():
    b = _budget()
    _ghi(b, "nlu", 100, 10)
    _ghi(b, "rationale", 200, 30)
    rows = b.theo_ngay()
    assert len(rows) == 1
    assert rows[0]["ngay"] == b.today() and rows[0]["luot"] == 2 and rows[0]["token_vao"] == 300


def test_so_lieu_rong_van_tra_ve_so_khong_chu_khong_phai_None():
    """Trang Cai dat mo luc chua goi model lan nao van phai ve duoc."""
    t = _budget().tong()
    assert t == {"token_vao": 0, "token_ra": 0, "cache_doc": 0, "cache_ghi": 0,
                 "token_tong": 0, "usd": 0.0, "luot": 0}


# ---------------------------------------------------------------- cong tac AI


def test_tat_ai_thi_allow_tra_false_du_chua_cham_tran():
    b = _budget()
    assert b.allow()
    b.ai_off = True
    assert not b.allow()          # moi cho goi model deu di qua allow(), nen tat la tat that
    b.ai_off = False
    assert b.allow()


def test_set_ai_tat_roi_bat_lai_khong_lam_mat_bo_nho():
    from assistant.core import Assistant
    from bc_agent.mock_client import MockBCClient

    a = Assistant(MockBCClient())
    a.handle_message("lan.s0001", "brief")
    truoc = len(a.mem.inbox("lan.s0001", 0))
    assert truoc > 0

    a.set_ai(False)
    assert a.budget.ai_off and not a.ai_live
    assert a.model_name == "scripted"
    a.handle_message("lan.s0001", "brief")
    assert len(a.mem.inbox("lan.s0001", 0)) > truoc      # van tra loi duoc khi tat AI


# ---------------------------------------------------------------- API


ADMIN = "dung.admin"       # vai tro admin, xem `core.ADMIN_ROLES`
QUANLY = "lan.s0001"     # quan ly cua hang, khong duoc vao trang Cai dat


@pytest.fixture()
def client():
    from assistant.channels import web
    from assistant.memory import Memory
    from bc_agent.mock_client import MockBCClient

    from assistant.core import Assistant

    # Tro ly moi cho tung test, de cai dat mot test ghi ra khong dinh sang test sau.
    web.state["asst"] = Assistant(MockBCClient(), Memory(":memory:"))
    return TestClient(web.app)


def test_api_usage_tra_du_bon_khoi_man_hinh_can(client):
    u = client.get(f"/api/usage?user={ADMIN}").json()
    for khoi in ("ai", "hom_nay", "cong_don", "tran", "don_gia", "theo_viec", "theo_ngay"):
        assert khoi in u, khoi
    assert u["tran"]["ngay_usd"] > 0
    assert u["don_gia"]["vao_moi_trieu"] > 0


def test_api_ai_tat_duoc_va_trang_thai_phan_anh_ngay(client):
    assert client.post("/api/ai", json={"on": False, "user": ADMIN}).json()["dang_bat"] is False
    assert client.get(f"/api/usage?user={ADMIN}").json()["ai"]["dang_bat"] is False


def test_api_bat_ai_thieu_credential_thi_bao_loi_chu_khong_lam_chet_server(client, monkeypatch):
    """`validate_live_llm` nem SystemExit. Khong bat lai thi bam nut Bat AI la sap server.

    Settings la frozen dataclass nen khong gan de len field duoc; thay ham kiem tra tren class."""
    from bc_agent.config import Settings

    def thieu(self):
        raise SystemExit("LLM_PROVIDER=azure nhung thieu bien: AZURE_OPENAI_API_KEY")

    monkeypatch.setattr(Settings, "validate_live_llm", thieu)
    r = client.post("/api/ai", json={"on": True, "user": ADMIN}).json()
    assert r["dang_bat"] is False
    assert r["bat_duoc"] is False and r["loi"]


def test_api_tran_doi_duoc_va_co_hieu_luc_ngay(client):
    u = client.post("/api/tran", json={"user": ADMIN, "ngay_usd": 0.5, "cong_don_usd": 3}).json()
    assert u["tran"]["ngay_usd"] == 0.5 and u["tran"]["cong_don_usd"] == 3
    assert client.post("/api/tran", json={"user": ADMIN, "ngay_usd": -1}).status_code == 400


# ---------------------------------------------------------------- chi quan tri moi vao duoc


@pytest.mark.parametrize("goi", [
    lambda c, u: c.get(f"/api/usage?user={u}"),
    lambda c, u: c.post("/api/ai", json={"on": False, "user": u}),
    lambda c, u: c.post("/api/tran", json={"user": u, "ngay_usd": 5}),
    lambda c, u: c.get(f"/api/policy-setup?user={u}"),
    lambda c, u: c.post("/api/policy-setup", json={"user": u, "shadow": False}),
])
def test_quan_ly_cua_hang_khong_vao_duoc_trang_cai_dat(client, goi):
    """An cai tab di la chua du: ai go dung duong dan cung goi duoc, nen chan o may chu."""
    assert goi(client, QUANLY).status_code == 403
    assert goi(client, "").status_code == 403
    assert goi(client, ADMIN).status_code == 200


# ---------------------------------------------------------------- policy va cau chu


def test_doi_mode_cua_mot_dong_policy_co_hieu_luc_ngay(client):
    from assistant.channels import web

    truoc = next(r for r in web.state["asst"].policy.rules if r.code == "P-01")
    assert truoc.mode.value == "auto"
    client.post("/api/policy-setup", json={"user": ADMIN, "code": "P-01", "mode": "approve"})
    assert web.state["asst"].policy.rules[0].mode.value == "approve"
    ra = client.get(f"/api/policy-setup?user={ADMIN}").json()
    assert next(r for r in ra["rules"] if r["code"] == "P-01")["da_sua"] is True


def test_doi_tran_gia_tri_va_bo_tran_gia_tri(client):
    client.post("/api/policy-setup", json={"user": ADMIN, "code": "P-01", "max_value_vnd": 500})
    ra = client.get(f"/api/policy-setup?user={ADMIN}").json()
    assert next(r for r in ra["rules"] if r["code"] == "P-01")["max_value_vnd"] == 500
    client.post("/api/policy-setup", json={"user": ADMIN, "code": "P-01", "bo_tran_gia_tri": True})
    ra = client.get(f"/api/policy-setup?user={ADMIN}").json()
    assert next(r for r in ra["rules"] if r["code"] == "P-01")["max_value_vnd"] is None


def test_policy_tu_choi_gia_tri_bay(client):
    assert client.post("/api/policy-setup", json={"user": ADMIN, "code": "P-01", "mode": "xyz"}).status_code == 400
    assert client.post("/api/policy-setup", json={"user": ADMIN, "code": "P-99", "mode": "auto"}).status_code == 404
    assert client.post("/api/policy-setup", json={"user": ADMIN, "tran_tu_lam": -1}).status_code == 400


def test_sua_cau_mau_thi_tro_ly_noi_theo_cau_moi(client):
    from assistant import caidat

    client.post("/api/policy-setup", json={"user": ADMIN, "cau_mau_key": "tro_giup",
                                     "cau_mau_text": "Chào bạn, tôi nghe đây."})
    assert caidat.cau("tro_giup") == "Chào bạn, tôi nghe đây."
    # De trong la quay ve ban goc, khong phai la mot cau rong.
    client.post("/api/policy-setup", json={"user": ADMIN, "cau_mau_key": "tro_giup", "cau_mau_text": ""})
    assert caidat.cau("tro_giup") == caidat.CAU_MAU_GOC["tro_giup"]["text"]


def test_cai_dat_song_qua_lan_khoi_dong_lai(client):
    """Day la ly do file cai dat nam tren dia chu khong trong bo nho tro ly."""
    from assistant.channels import web
    from assistant.core import Assistant
    from assistant.memory import Memory
    from bc_agent.mock_client import MockBCClient

    client.post("/api/tran", json={"user": ADMIN, "ngay_usd": 0.25})
    client.post("/api/policy-setup", json={"user": ADMIN, "shadow": False})
    moi = Assistant(MockBCClient(), Memory(":memory:"))       # nhu vua khoi dong lai
    assert moi.budget.cap == 0.25
    assert moi.policy.shadow is False
    web.state["asst"] = moi


# ---------------------------------------------------------------- loi cua BC phai hien ra


def test_loi_cua_bc_ra_thanh_502_kem_cau_chu_khong_phai_500_tron(client, monkeypatch):
    """403 cua BC tung lam ca duong tra ve 500, giao dien nuot im va man hinh trong tron:
    bam Brief khong thay gi. Gio no ra thanh 502 kem nguyen van cau cua BC."""
    from bc_agent.bc_client import BCError
    from assistant.channels import web

    def tu_choi(*a, **k):
        raise BCError("HTTP 403 POST .../agentProposals: Sorry, the current permissions "
                      "prevented the action. (TableData 10000700 LSC Retail Setup ...)")

    monkeypatch.setattr(web.state["asst"].gw, "create_proposal", tu_choi)
    monkeypatch.setattr(web.state["asst"], "morning_brief", tu_choi)
    r = client.post("/api/brief", json={"user": "hung.dieuphoi", "text": ""})
    assert r.status_code == 502
    assert "10000700" in r.json()["loi"]        # ten bang thieu quyen phai den duoc man hinh


def test_lam_moi_bo_ban_nho(client):
    r = client.post("/api/lam-moi")
    assert r.status_code == 200 and "live" in r.json()
