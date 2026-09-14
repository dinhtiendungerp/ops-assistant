"""UC3 Procurement & Supplier Performance: scorecard nha cung cap. Khong goi model.

Vi sao co file nay (14/09/2026). RFP UC3 doi supplier scorecard, purchase commitment, late delivery va lead-time
exception. So do codeunit 70121 NWV Supplier Scorecard Calc tinh (API supplierScorecards), ban Python doi chieu trong
bc_agent/supplier.py ra cung so. Don qua han chua nhan do skill po_qua_han lo va hoi dung nguoi nhan hang.
"""
from __future__ import annotations

from typing import Any

from ..bc_link import link
from ..cards import Action, Card, fmt_qty, fmt_vnd
from . import Delivery

SKILL = "nha_cung_cap"


def _pct(v: Any) -> str:
    return f"{float(v or 0):.1f}%".replace(".", ",")


def _dmy(v: Any) -> str:
    s = str(v or "")[:10]
    return f"{s[8:10]}/{s[5:7]}/{s[:4]}" if len(s) == 10 else s


def _so(v: Any) -> str:
    return f"{float(v or 0):.1f}".replace(".", ",").replace(",0", "")


def handle(asst: Any, user: dict[str, Any], text: str = "") -> list[Delivery]:
    uid = user["user_id"]
    rows = asst.gw.doc("supplierScorecards", [], top=500)
    if not rows:
        return [Delivery(uid, "Chưa có scorecard nhà cung cấp. Trên BC cần chạy Run Supplier Scorecard (trang NWV Agent Setup) "
                              "hoặc Job Queue với tham số SUPPLIER.", skill=SKILL)]
    tong = sorted([r for r in rows if not r.get("itemCategoryCode")],
                  key=lambda r: (not r.get("needsAttention"), float(r.get("onTimePct") or 0)))
    thap = text.lower()
    import re
    chon = [r for r in tong if r["vendorNo"] in thap
            or re.search(rf"\b{re.escape((r.get('vendorName') or '-').lower().split('-')[0])}\b", thap)]
    if chon:
        tong = chon
    xem = [r for r in tong if r.get("needsAttention")]
    ky = rows[0]
    cau = (f"Kỳ {_dmy(ky.get('periodFrom'))} đến {_dmy(ky.get('periodTo'))}, {len(tong)} nhà cung cấp có đơn đến hạn. "
           + (f"{len(xem)} nhà cung cấp cần xem: " + "; ".join(f"{r['vendorName'] or r['vendorNo']} giao đúng hạn {_pct(r['onTimePct'])}"
                                                                  for r in xem) + "." if xem else "Không nhà cung cấp nào dưới ngưỡng."))
    out = [Delivery(uid, cau, skill=SKILL)]
    for r in tong:
        nhom = [x for x in rows if x["vendorNo"] == r["vendorNo"] and x.get("itemCategoryCode")]
        body = []
        if r.get("attentionReason"):
            body.append(r["attentionReason"])
        body.append(f"Hứa giao sau {_so(r['avgPromisedLeadTime'])} ngày, thực tế {_so(r['avgActualLeadTime'])} ngày. "
                    f"Dòng trễ trễ trung bình {_so(r['avgDelayDays'])} ngày.")
        if nhom:
            body.append("Theo nhóm hàng: " + "; ".join(f"{x['itemCategoryCode']} đúng hạn {_pct(x['onTimePct'])}" for x in nhom) + ".")
        facts = [("Đúng hạn", f"{_pct(r['onTimePct'])} ({r['linesOnTime']}/{r['linesDue']} dòng)"),
                 ("Giao đủ lần đầu", _pct(r["firstDeliveryCompletePct"])),
                 ("Lead time hứa / thực", f"{_so(r['avgPromisedLeadTime'])} / {_so(r['avgActualLeadTime'])} ngày"),
                 ("Quá hạn chưa nhận", f"{r['overdueLines']} dòng, {fmt_qty(r['overdueQty'])} đơn vị, {fmt_vnd(r['overdueAmount'])}")]
        actions = [Action("po_qua_han", "Xem đơn quá hạn")] if r.get("overdueLines") else []
        card = Card(title=f"Nhà cung cấp {r['vendorName'] or r['vendorNo']} ({r['vendorNo']})", body="\n".join(body), facts=facts,
                    actions=actions, ref=f"ncc|{r['vendorNo']}", kind="info",
                    links=[("Scorecard trong BC", link("supplier_scorecard", {"Vendor No.": r["vendorNo"]})),
                           ("Dòng đơn mua", link("purchase_lines", {"Document Type": "Order", "Buy-from Vendor No.": r["vendorNo"]}))])
        out.append(Delivery(uid, r["vendorName"] or r["vendorNo"], card=card, skill=SKILL, ref=f"ncc|{r['vendorNo']}"))
    return out
