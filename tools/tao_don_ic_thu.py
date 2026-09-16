"""Tao don mua lien cong ty de thu vong "Marou post xuat kho -> tro ly tu bao cua hang Dakao".

Vi sao (16/09/2026 dem): Dung hoi "ben Marou bam post don IC thi agent tu thong bao va email, co so nao de biet" va muon
tu post de kiem. Script lam dung chuoi nghiep vu that, khong di duong tat:
  1. NWV-DAKAO: ghi de xuat Purchase (vendor MAROU) vao bang NWV Agent Proposal, duyet -> BC tao Purchase Order.
  2. NWV-DAKAO: NWVDemoIntercompany.SendPurchaseOrder -> release, IC Outbox; NWV-MAROU Auto Accept tao Sales Order.
  3. NWV-MAROU: NWVDemoIntercompany.PrepareSalesShipment -> dien kho xuat, gan lo FEFO. KHONG post.
Nguoi kho Marou mo Sales Order trong BC, bam Post > Ship. Trong vong mot phut lich nen cua may chu tro ly
(`web._quet_xuat_kho_nen`) doc phieu giao hang qua NWVAgentICService.ShipmentStatus va bao cua hang + Supply Chain.

    cd python; python ../tools/tao_don_ic_thu.py 33341:5:S0010 33310:10:S0005
"""
from __future__ import annotations

import json
import sys
import time
from dataclasses import replace
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "python"))

from bc_agent.bc_client import BCClient  # noqa: E402
from bc_agent.config import settings  # noqa: E402
from assistant.gateway import BCGateway  # noqa: E402

DAKAO, MAROU = "NWV-DAKAO", "NWV-MAROU"


def tao(item_no: str, qty: float, store: str) -> dict:
    cd = BCClient(replace(settings, bc_company_name=DAKAO, bc_company_id=""))
    gw = BCGateway(cd)
    ref = f"THU-IC|{item_no}|{store}|{int(time.time())}"
    p = gw.create_proposal(scenario="StoreReplenishment", action_type="Purchase", item_no=item_no, from_loc="", to_loc=store,
                           quantity=qty, reference_key=ref, rationale="Đơn thử vòng liên công ty (Dũng post xuất kho tay bên Marou).",
                           priority=10, evidence={}, run_id="thu-ic", model_name="", vendor_no="MAROU")
    kq = gw.approve(p["id"], "", "Đơn thử liên công ty")
    po = kq.get("resultDocumentNo") or ""
    if not po:
        raise SystemExit(f"Duyệt không ra Purchase Order: {kq}")
    gui = gw.gui_don_ic(po)
    time.sleep(3)
    cm = BCClient(replace(settings, bc_company_name=MAROU, bc_company_id=""))
    chuan_bi = cm.web_service("NWVDemoIntercompany", "PrepareSalesShipment", {"docNo": po})
    return {"item": item_no, "qty": qty, "store": store, "purchaseOrder": po, "gui": gui, "marou": chuan_bi}


if __name__ == "__main__":
    for arg in sys.argv[1:] or ["33341:5:S0010"]:
        it, q, st = arg.split(":")
        print(json.dumps(tao(it, float(q), st), ensure_ascii=False))
