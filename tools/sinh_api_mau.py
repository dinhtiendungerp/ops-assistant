"""Sinh lai docs/ui-handoff/api-mau.json: phan hoi JSON that cua cac duong API giao dien dung.

Chay tren du lieu mo phong (BC_MODE=mock, LLM_MODE=scripted), so chi phi, file cai dat va kich ban doi sang
thu muc tam, nen khong dung vao trang thai that cua tro ly. Moi mang cat con 2 phan tu.

    python tools/sinh_api_mau.py
"""
from __future__ import annotations

import json
import os
import pathlib
import sys
import tempfile

ROOT = pathlib.Path(__file__).resolve().parents[1]
RA = ROOT / "docs" / "ui-handoff" / "api-mau.json"

os.environ["BC_MODE"] = "mock"
os.environ["LLM_MODE"] = "scripted"
sys.path.insert(0, str(ROOT / "python"))
os.chdir(ROOT / "python")

TAM = pathlib.Path(tempfile.mkdtemp(prefix="api-mau-"))
from assistant import budget as budget_mod  # noqa: E402
from assistant import caidat as caidat_mod  # noqa: E402
from assistant import kich_ban as kich_ban_mod  # noqa: E402

budget_mod.DUONG_SO = TAM / "chi-phi.sqlite"
caidat_mod.DUONG = TAM / "cai-dat.json"
kich_ban_mod.DUONG = TAM / "kich-ban.sqlite"

from fastapi.testclient import TestClient  # noqa: E402

from assistant.channels.web import app  # noqa: E402


def cat(v, n: int = 2):
    if isinstance(v, list):
        return [cat(x, n) for x in v[:n]]
    if isinstance(v, dict):
        return {k: cat(x, n) for k, x in v.items()}
    return v


def main() -> None:
    mau: dict[str, dict] = {}
    with TestClient(app) as c:
        def goi(ten: str, method: str, path: str, body: dict | None = None, ghi_chu: str = ""):
            r = c.request(method, path, json=body)
            try:
                tra_ve = r.json()
            except ValueError:
                tra_ve = r.text[:500]
            mau[ten] = {"method": method, "path": path, "body_gui": body, "status": r.status_code,
                        **({"ghi_chu": ghi_chu} if ghi_chu else {}), "tra_ve": cat(tra_ve)}
            return tra_ve

        goi("danh sach nguoi dung", "GET", "/api/users")
        goi("trang thai chung", "GET", "/api/state")
        goi("nguon du lieu", "GET", "/api/mode")
        goi("chinh sach (moi vai tro doc duoc)", "GET", "/api/policy")
        goi("doan chat cua mot nguoi", "GET", "/api/doan-chat?user=lan.s0001")
        goi("mo doan chat moi", "POST", "/api/doan-chat", {"user": "lan.s0001"},
            "Khong co conv_id la mo doan moi; co conv_id la chuyen sang doan do.")
        goi("gui mot tin", "POST", "/api/message", {"user": "lan.s0001", "text": "Choco nuts con bao nhieu?"})
        hop = goi("hop thu", "GET", "/api/inbox?user=lan.s0001&after=0")
        tin_id = next((m.get("id") for m in (hop if isinstance(hop, list) else hop.get("messages", []))
                       if isinstance(m, dict) and m.get("id")), None)
        if tin_id:
            goi("tra loi mot tin cu the", "POST", "/api/message",
                {"user": "lan.s0001", "text": "con o S0002 thi sao", "reply_to": tin_id},
                "reply_to la id tin nguoi dung bam Tra loi; hop thu tra kem truong trich.")
        goi("brief", "POST", "/api/brief", {"user": "hung.dieuphoi", "text": ""})
        hop_hung = goi("hop thu co the de xuat", "GET", "/api/inbox?user=hung.dieuphoi&after=0")
        goi("suc khoe ton kho, tong quan", "GET", "/api/uc2/summary")
        dong = goi("suc khoe ton kho, danh sach", "GET", "/api/uc2/lines?tier=StockOutRisk")
        rows = dong if isinstance(dong, list) else dong.get("lines", dong.get("rows", []))
        if rows and isinstance(rows[0], dict):
            lid = rows[0].get("line_id") or rows[0].get("id") or rows[0].get("lineId")
            if lid is not None:
                goi("chi tiet mot lo", "GET", f"/api/uc2/trace?line_id={lid}")
        goi("do phu du lieu", "GET", "/api/uc2/readiness")
        goi("cai dat AI va chi phi (chi admin)", "GET", "/api/usage?user=dung.admin")
        goi("cai dat AI, vai tro khong phai admin", "GET", "/api/usage?user=trang.sc",
            "Mau loi 403. Giao dien phai in nguyen van detail.")
        goi("chinh sach va cau chu (chi admin)", "GET", "/api/policy-setup?user=dung.admin")
        goi("nhat ky agent (chi admin)", "GET", "/api/nhat-ky?user=dung.admin")
        goi("nhat ky agent, vai tro khong phai admin", "GET", "/api/nhat-ky?user=trang.sc")
        goi("xem truoc kich ban, cau hoi khong ton tai", "POST", "/api/kich-ban/xem-truoc",
            {"user": "dung.admin", "cau_hoi_id": 999999},
            "Mau loi 400. Khi co cau hoi that thi tra mau, cac o so va canh bao; xem assistant/kich_ban.py.")

        # Nut tren the: lay the dau tien co action trong hop thu cua Hung
        msgs = hop_hung if isinstance(hop_hung, list) else hop_hung.get("messages", [])
        for m in msgs if isinstance(msgs, list) else []:
            card = (m or {}).get("card") or {}
            acts = card.get("actions") or []
            if acts:
                a = acts[0]
                goi("bam nut tren the", "POST", "/api/action",
                    {"user": "hung.dieuphoi", "verb": a.get("id"), "ref": a.get("ref") or card.get("ref", ""),
                     "payload": a.get("payload") or {}},
                    "Tra {delivered, con_mo}; con_mo true la bi tu choi, phai bat lai nut.")
                break

    RA.write_text(json.dumps(mau, ensure_ascii=False, indent=2), encoding="utf-8")
    for ten, v in mau.items():
        print(f"  {v['status']}  {v['method']:4s} {v['path']:45s} {ten}")
    print(f"\n{RA.relative_to(ROOT)}  {len(mau)} duong")


if __name__ == "__main__":
    main()
