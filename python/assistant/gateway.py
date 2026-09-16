"""BCGateway: cac ham nghiep vu tro ly can, tren client BC (MockBCClient hoac BCClient).

Nguyen tac: so do BC (hoac fixtures mirror AL) tinh; gateway chi doc va ghi de xuat.
Khi mock, Transfer Order duoc gia lap trong bo nho de demo vong theo doi (ship / chua ship).
Khi live, transfer_status can mot API page doc Transfer Header (chua co trong Foundation 0.1, ghi o design 0.2 phu luc C).
"""
from __future__ import annotations

import logging

import json
import uuid
from datetime import datetime, timezone
from typing import Any

from rapidfuzz import fuzz, process, utils

from bc_agent.odata import Condition

log = logging.getLogger(__name__)


class FixtureLocked(OSError):
    """File fixtures bi khoa (OneDrive dang dong bo, hoac trinh soan thao dang giu file).
    Tach rieng de cho goi co the bo qua thay vi lam chet ca tien trinh."""


class BCGateway:
    # Bang ket qua cua AL chi doi khi Job Queue chay hoac co nguoi bam nut, nen mot phut la thua
    # an toan. Vong poll cua man hinh doc hai bang do moi 2 giay nen chung luon am, khong ai bam
    # phai mot lan doc nguoi.
    CACHE_TTL = 60.0
    # Item Ledger Entry chi doi khi co nguoi post, va cua so 120 ngay mat 8 giay de doc. De 60
    # giay thi cu ngoi khong mot phut la lan bam tiep theo lai cho 8 giay, va khong co vong poll
    # nao giu no am. Muoi lam phut, con nut "Doc lai tu BC" de bo ngay khi vua post xong.
    TTL_THEO_BANG = {"nwvItemLedgerEntries": 900.0}
    # Cua so lich su ban duoc lam tron len mot trong ba moc nay, de moi lan hoi BC deu dung chung
    # ban nho. Cac cho goi dang xin 7, 14, 90, 120 va 400 ngay.
    CUA_SO_BAN = (120, 400)

    def __init__(self, client: Any, central_wh: str = "W0003"):
        self.client = client
        # Kho trung tam mac dinh, dung cho mock va khi BC chua khai. Tren BC that doc tu API nwvLocations
        # (isCentralWarehouse = LSC Replen. Setup."Default Central Warehouse", tu 15/09/2026), xem `central_wh`.
        self._central_wh_mac_dinh = central_wh
        self._central_wh: str | None = None
        self.is_mock = client.__class__.__name__ == "MockBCClient"
        self._transfers: dict[str, dict[str, Any]] = {}
        self._journal: dict[str, dict[str, Any]] = {}     # mock: dong Item Journal nhap do duyet de xuat Write-off sinh ra (UC2 G2/A3)
        self._ic: dict[str, dict[str, Any]] = {}          # mock: don mua intercompany va phieu giao hang ben doi tac (16/09/2026)
        self._to_seq = 1022
        self._sales_cache: list[dict[str, Any]] | None = None
        self._as_of = None
        self._nho: dict[Any, tuple[float, Any]] = {}

    @property
    def central_wh(self) -> str:
        """Kho trung tam cua company: LSC Replen. Setup tren BC that, hang so tren mock. Doc mot lan."""
        if self._central_wh is None:
            self._central_wh = self._central_wh_mac_dinh
            if not self.is_mock:
                try:
                    locs = self.doc("nwvLocations", [], ttl=3600, select="code,isWarehouse,isCentralWarehouse")
                    chinh = [l["code"] for l in locs if l.get("isCentralWarehouse")]
                    kho = [l["code"] for l in locs if l.get("isWarehouse")]
                    self._central_wh = (chinh or kho or [self._central_wh_mac_dinh])[0]
                except Exception as exc:               # API cu chua co field, hoac BC loi: giu mac dinh
                    log.warning("Khong doc duoc kho trung tam tu BC, dung %s: %s", self._central_wh_mac_dinh, exc)
        return self._central_wh

    @central_wh.setter
    def central_wh(self, value: str) -> None:
        self._central_wh = value

    # ---------- nho lai cac lenh doc, de mot man hinh khong hoi BC ba bon lan cung mot thu
    def doc(self, entity_set: str, conds: list[Condition] | None = None, ttl: float | None = None,
            **kw: Any) -> list[dict[str, Any]]:
        """Doc mot bang cua BC, nho lai `ttl` giay.

        Vi sao can. Mo man hinh Suc khoe ton kho la ba lenh doc 5000 dong; moi vong poll them
        hai lenh nua; `items()` va `unit_cost()` moi lan goi lai doc lai ca bang. Tren BC that
        moi lenh mat khoang 1,7 giay nen man hinh cham thay ro. Nhung bang nay chi doi khi Job
        Queue chay hoac khi co nguoi bam Run Inventory Health, tuc rat thua so voi mot phut.

        Mock doc tu bo nho san nen khong nho lai: giu nguyen ngu nghia cu cho test, va
        `MockBCClient.query` tra ban deepcopy nen cache se lam mat tinh chat do.
        """
        if self.is_mock:
            return self.client.query(entity_set, conds, **kw)
        if entity_set == "replenishmentSuggestions":
            # UC1 dung LS Replenishment (Dung chot 13/09/2026). Tren BC that khong doc bang NWV Repl. Suggestion
            # nua ma doc journal chuyen hang cua LS roi dua ve cung hinh dang, de moi skill dang dung giu nguyen.
            from bc_agent.odata import apply_in_python
            return apply_in_python(self.goi_y_ls(), list(conds or []), kw.get("orderby"), kw.get("top"))
        import time

        khoa = (entity_set, tuple(conds or ()), tuple(sorted(kw.items())))
        t = time.monotonic()
        cu = self._nho.get(khoa)
        han = ttl if ttl is not None else self.TTL_THEO_BANG.get(entity_set, self.CACHE_TTL)
        if cu and t - cu[0] < han:
            return list(cu[1])
        gt = self.client.query(entity_set, conds, **kw)
        self._nho[khoa] = (t, gt)
        return list(gt)

    # ---------- de xuat bo sung lay tu LS Replenishment
    # Hai journal: MAROU-TO chuyen hang tu kho tong (Marou), MAROU-PO mua hang. Tu 15/09/2026 o Dakao MAROU-PO la
    # "Purchase Orders for Receiving Locations": moi cua hang mot don mua tu vendor MAROU, giao thang, khong qua kho.
    LS_TEMPLATE_CHUYEN = "MAROU-TO"
    LS_TEMPLATES = {"MAROU-TO": "Transfer", "MAROU-PO": "Purchase"}

    def _kho(self) -> set[str]:
        """Ma cac kho theo LS (nwvLocations.isWarehouse). Rong neu API chua co truong nay."""
        try:
            return {l["code"] for l in self.doc("nwvLocations", [], ttl=3600, select="code,isWarehouse") if l.get("isWarehouse")}
        except Exception:
            return set()

    def goi_y_ls(self) -> list[dict[str, Any]]:
        """Dong de xuat bo sung cua cua hang, doc tu LS Replenishment, dua ve hinh dang cua bang NWV Repl. Suggestion.

        Nguon: `replenJournalDetails` cua hai template (chuyen hang MAROU-TO, mua hang MAROU-PO; dong mua ve kho thi bo,
        chi giu dong mua giao thang cua hang) va `replenItemQuantities` (ton, hang dang ve). Trong dong ra, chi `daysOfCover`
        la phep chia do tro ly lam: ton hieu dung chia ban binh quan ngay, ca hai so lay nguyen tu LS. `stockOutRisk` la
        LS co de xuat so luong lon hon 0, khong phai nguong cua tro ly. `replenType` cho biet Transfer hay Purchase.
        """
        from bc_agent.bc_data import unescape_option

        riq = {(r["itemNo"], r["locationCode"]): r
               for r in self.doc("replenItemQuantities", [], top=5000) if not r.get("variantCode")}
        kho = self._kho()
        ra = []
        for template, loai in self.LS_TEMPLATES.items():
            chi_tiet = self.doc("replenJournalDetails", [("replenishmentTemplateCode", "eq", template)], top=5000)
            if not chi_tiet:
                continue
            lo = self.doc("replenJournalBatches", [("replenishmentTemplateCode", "eq", template)], top=1)
            luc_tinh = str(lo[0].get("lastRunDate") or "") if lo else ""
            for d in chi_tiet:
                if loai == "Purchase" and (d["locationCode"] in kho or d["locationCode"] == self.central_wh):
                    continue                       # mua ve kho tong: viec cua nguoi mua, khong phai de xuat cho cua hang
                q = riq.get((d["itemNo"], d["locationCode"]), {})
                ban = float(d.get("averageDailySales") or 0)
                ton_hd = float(d.get("effectiveInventory") or 0)
                de_xuat = float(d.get("systemSuggestedQuantity") or 0)
                # Số cuối cùng của LS là Quantity, sau các bước điều chỉnh (Stock Levels trừ tồn khả dụng, chia lại khi kho
                # thiếu). System Suggested Quantity với Stock Levels là mức Maximum Inventory, không phải số cần chuyển:
                # ngày 14/09/2026 brief ghi đề xuất Ice cream x S0002 = 20 trong khi LS ra 11.
                chuyen = float(d["quantity"]) if d.get("quantity") is not None else de_xuat
                phu = float(d.get("requiredCoverageDays") or 0)
                quyet = unescape_option(d.get("decision")) or ""
                vendor = d.get("vendorNo") or ""
                nguon = vendor if loai == "Purchase" else (d.get("replenishmentLocationCode") or self.central_wh)
                dong_tac = "mua" if loai == "Purchase" else "chuyển"
                ly_do = (f"LS Replenishment: tồn khả dụng {ton_hd:g}, bán bình quân {ban:g}/ngày, cần phủ {phu:g} ngày, "
                         f"đề xuất {dong_tac} {chuyen:g} từ {nguon}" + (f" ({quyet})." if quyet else "."))
                ra.append({
                    "id": d.get("id"), "storeLocationCode": d["locationCode"], "itemNo": d["itemNo"],
                    "itemDescription": d.get("description") or d["itemNo"],
                    "storeQtyOnHand": float(q.get("inventory") or 0),
                    "storeQtyInTransit": float(q.get("quantityInTransferIn") or 0),
                    "avgDailySalesQty": ban,
                    "daysOfCover": round(ton_hd / ban, 1) if ban else 9999.0,
                    "targetQty": de_xuat, "suggestedQty": chuyen, "constrainedQty": chuyen,
                    # Mua tu vendor thi khong bi ton kho tong chan
                    "warehouseQtyAvailable": chuyen if loai == "Purchase" else float(d.get("warehouseEffectiveInventory") or 0),
                    "sourceLocationCode": nguon,
                    "targetDays": phu, "shelfLifeDays": 0, "cappedByShelfLife": False,
                    "demandBasis": "LS", "daysCensored": int(q.get("noOfDaysOutOfStock") or 0),
                    "stockOutRisk": chuyen > 0, "reason": ly_do, "calculatedAt": luc_tinh,
                    "lsDecision": quyet, "replenType": loai, "lsTemplate": template, "vendorNo": vendor,
                })
        return ra

    def quen_nho(self, entity_set: str | None = None) -> None:
        """Bo ban nho. Khong truyen gi la bo het (nut Doc lai tu BC).

        Ghi mot de xuat thi chi bang de xuat doi, con ton kho va lich su ban thi khong. Ban dau
        cho `create_proposal` bo het, va brief cua dieu phoi tao 10 de xuat lien tiep nen no doc
        lai moi thu 10 lan: 74 giay cho mot cai brief. Do ngay 13/09/2026."""
        if entity_set is None:
            self._nho.clear()
            self._sales_cache = None
            return
        for k in [k for k in self._nho if k[0] == entity_set]:
            del self._nho[k]

    # ---------- danh muc
    def items(self) -> list[dict[str, str]]:
        rows = self.doc("inventoryHealthLines", [], top=5000)
        seen: dict[str, str] = {}
        for r in rows:
            seen.setdefault(r["itemNo"], r.get("itemDescription", r["itemNo"]))
        return [{"itemNo": k, "description": v} for k, v in seen.items()]

    def find_item(self, text: str, min_score: int = 60) -> dict[str, Any] | None:
        """Tim item tu chu nguoi go. Fuzzy tren description va itemNo. Tra ve item + score.

        Do hai vong, lay diem cao hon:
          1. token_set_ratio tren chuoi da chuan hoa. Khop tot khi nguoi ta go thieu hoac thua
             tu, vi du "ba ria 76" hay "sap het mini bar".
          2. WRatio tren chuoi da bo dau cach. Khop khi nguoi ta viet lien, vi du "minibar".

        Bat buoc chuan hoa hoa thuong bang default_process. Ban truoc de rapidfuzz so nguyen van
        nen "Mini bar" duoc 100 diem con "mini bar" chi duoc 54, duoi nguong 60, tuc la tro ly
        chi nhan ra mat hang khi nguoi dung go dung chu hoa nhu trong fixtures.
        """
        items = self.items()
        if not items:
            return None
        # Chu go chua NGUYEN CUM ten mot mat hang thi lay ten dai nhat khop, truoc khi so mo. Khong co buoc nay thi
        # "Ice cream" (33150) thua "Ice cream blueberry" (18200) vi token_set_ratio cho ca hai 100 diem.
        gon = lambda s: " ".join(utils.default_process(s or "").split())  # noqa: E731
        chu = f" {gon(text)} "
        nguyen_cum = [i for i in items if (d := gon(i.get("description"))) and f" {d} " in chu]
        if nguyen_cum:
            return {**max(nguyen_cum, key=lambda i: len(i["description"])), "score": 100.0}
        choices = {f"{i['description']} {i['itemNo']}": i for i in items}
        keys = list(choices)
        best_key, best_score = None, 0.0
        for scorer, tf in ((fuzz.token_set_ratio, lambda s: s),
                           (fuzz.WRatio, lambda s: s.replace(" ", ""))):
            hit = process.extractOne(tf(text), [tf(k) for k in keys],
                                     scorer=scorer, processor=utils.default_process)
            if hit and hit[1] > best_score:
                best_key, best_score = keys[hit[2]], hit[1]
        if best_key is None or best_score < min_score:
            return None
        return {**choices[best_key], "score": round(best_score, 1)}

    def stores(self) -> list[str]:
        """Danh sach cua hang lay tu du lieu BC, khong lay tu danh ba nguoi dung."""
        rows = self.doc("replenishmentSuggestions", [], top=5000)
        return sorted({r["storeLocationCode"] for r in rows})

    def unit_cost(self, item_no: str) -> float:
        """Gia von don vi, de policy xet nguong gia tri. Lay tu inventoryHealthLines (inventoryValue/qty)."""
        rows = self.doc("inventoryHealthLines", [("itemNo", "eq", item_no)], top=5)
        for r in rows:
            if float(r.get("quantityOnHand") or 0) > 0:
                return float(r["inventoryValue"]) / float(r["quantityOnHand"])
        return 0.0

    # ---------- ton kho va toc do
    def stock_by_location(self, item_no: str) -> list[dict[str, Any]]:
        rows = self.doc("inventoryHealthLines", [("itemNo", "eq", item_no)], top=500)
        agg: dict[str, dict[str, Any]] = {}
        for r in rows:
            a = agg.setdefault(r["locationCode"], {"locationCode": r["locationCode"], "qty": 0.0, "avgDaily": r.get("avgDailySalesQty", 0), "lots": []})
            a["qty"] += float(r["quantityOnHand"])
            a["lots"].append({"lot": r.get("lotNo"), "qty": r["quantityOnHand"], "expiry": r.get("expirationDate"), "daysToExpiry": r.get("daysToExpiry")})
        for a in agg.values():
            a["daysOfCover"] = round(a["qty"] / a["avgDaily"], 1) if a["avgDaily"] else 9999
        return sorted(agg.values(), key=lambda x: x["locationCode"])

    def suggestion(self, store: str, item_no: str) -> dict[str, Any] | None:
        rows = self.doc("replenishmentSuggestions", [("storeLocationCode", "eq", store), ("itemNo", "eq", item_no)], top=1)
        return rows[0] if rows else None

    def risky_suggestions(self, top: int = 20) -> list[dict[str, Any]]:
        rows = self.doc("replenishmentSuggestions", [("stockOutRisk", "eq", True)], top=200)
        return sorted(rows, key=lambda r: r["daysOfCover"])[:top]

    _ILE_DEMO: list[dict[str, Any]] | None = None

    def ile_theo_lo(self, lot_no: str) -> list[dict[str, Any]]:
        """Moi dong Item Ledger Entry cua mot lo (truy xuat, UC2).

        Live doc API nwvItemLedgerEntries loc Lot No. Mock doc thang bo du lieu demo (cung du lieu da post len BC), doi sang
        ten truong cua API. Bo demo doc mot lan cho ca tien trinh vi mo file Excel mat vai giay."""
        if not self.is_mock:
            return self.doc("nwvItemLedgerEntries", [("lotNo", "eq", lot_no)], top=2000)
        if BCGateway._ILE_DEMO is None:
            from bc_agent.demo_data import read_ile
            BCGateway._ILE_DEMO = [
                {"entryNo": i, "postingDate": str(r["posting_date"]), "entryType": r["entry_type"], "itemNo": r["item_no"],
                 "locationCode": r["location_code"], "lotNo": r.get("lot_no") or "", "quantity": r["quantity"],
                 "expirationDate": str(r["expiration_date"]) if r.get("expiration_date") else None}
                for i, r in enumerate(read_ile(), 1)]
        return [r for r in BCGateway._ILE_DEMO if (r["lotNo"] or "").upper() == lot_no.upper()]

    def la_kho(self, loc: str) -> bool:
        """Kho (khong phai cua hang): theo LS (nwvLocations.isWarehouse) hoac ma bat dau bang W (bo demo, mock)."""
        return loc in self._kho() or str(loc).upper().startswith("W")

    def ile_cua_so(self, days: int = 90) -> list[dict[str, Any]]:
        """Moi dong Item Ledger Entry trong `days` ngay, moi loai (Sale, Positive/Negative Adjmt., Purchase, Transfer), ten
        truong theo API page, entryType da giai ma Option, expirationDate None neu rong. Dung cho D3 bat thuong, D2 nguyen
        nhan huy, S3 bao cao tuan (16/09/2026). Live doc theo cua so chung nhu `sales_history` roi loc trong Python."""
        from datetime import timedelta

        from bc_agent.bc_data import norm_date, unescape_option
        since = (self.today() - timedelta(days=days)).isoformat()
        if self.is_mock:
            self.ile_theo_lo("__nap__")               # nap _ILE_DEMO mot lan
            return [dict(r) for r in BCGateway._ILE_DEMO if r["postingDate"] >= since]
        cua_so = next((b for b in self.CUA_SO_BAN if b >= days), self.CUA_SO_BAN[-1])
        tu = (self.today() - timedelta(days=cua_so)).isoformat()
        rows = self.doc("nwvItemLedgerEntries", [("postingDate", "ge", tu)], top=100000,
                        select="entryNo,postingDate,entryType,itemNo,locationCode,quantity,lotNo,expirationDate,documentNo")
        out = []
        for r in rows:
            ngay = str(r["postingDate"])[:10]
            if ngay < since:
                continue
            hd = norm_date(r.get("expirationDate"))
            out.append({"entryNo": r.get("entryNo"), "postingDate": ngay, "entryType": unescape_option(r.get("entryType")),
                        "itemNo": r["itemNo"], "locationCode": r["locationCode"], "quantity": float(r.get("quantity") or 0),
                        "lotNo": r.get("lotNo") or "", "expirationDate": str(hd) if hd else None, "documentNo": r.get("documentNo", "")})
        return out

    def health_lines(self, min_score: int = 60, top: int = 20) -> list[dict[str, Any]]:
        return self.doc("inventoryHealthLines", [("riskScore", "ge", min_score)], orderby="riskScore desc", top=top)

    def open_exceptions(self, top: int = 20) -> list[dict[str, Any]]:
        rows = self.doc("discountExceptions", [("status", "eq", "Open")], top=200)
        rank = {"High": 2, "Medium": 1, "Low": 0}
        return sorted(rows, key=lambda r: rank.get(r["severity"], -1), reverse=True)[:top]

    def exception(self, exc_id: str) -> dict[str, Any]:
        return self.client.get("discountExceptions", exc_id)

    def discount_context(self, store: str, staff: str, day: str) -> list[dict[str, Any]]:
        return self.doc("posDiscountLogs", [("storeNo", "eq", store), ("staffId", "eq", staff), ("transDate", "eq", day)], top=200)

    # ---------- ghi
    def create_proposal(self, *, scenario: str, action_type: str, item_no: str, from_loc: str, to_loc: str,
                        quantity: float, reference_key: str, rationale: str, priority: int, evidence: dict[str, Any],
                        run_id: str, model_name: str, lot_no: str = "", vendor_no: str = "", source_doc: str = "") -> dict[str, Any]:
        # lot_no: de xuat theo lo (huy, giam gia lo can date) phai mang so lo. Truoc 14/09/2026 cho nay ghi cung "",
        # nen de xuat huy 33100 tai W0003 len BC khong co lo, nguoi duyet khong biet huy lo nao. Dung bat duoc.
        # vendor_no: de xuat Purchase (Dakao mua thang tu Marou, 15/09/2026); duyet thi BC tao Purchase Order.
        body = {
            "scenario": scenario, "actionType": action_type, "itemNo": item_no, "lotNo": (lot_no or "")[:50],
            "fromLocationCode": from_loc, "toLocationCode": to_loc, "quantity": quantity, "vendorNo": (vendor_no or "")[:20],
            "sourceDocumentNo": (source_doc or "")[:20],
            "referenceKey": reference_key, "rationale": rationale[:2000], "priorityScore": int(priority),
            "evidenceJson": json.dumps(evidence, ensure_ascii=False, default=str), "modelName": model_name[:50], "runId": run_id[:50],
        }
        self.quen_nho("agentProposals")     # chi bang de xuat doi, ton kho va lich su ban thi khong
        return self.client.create("agentProposals", body)

    def de_xuat_dang_co(self) -> set[str]:
        """`Reference Key` cua nhung de xuat con hieu luc trong BC.

        Bo nho cua tro ly bi dung moi lan khoi dong lai, con BC thi giu. Neu chi so voi bo nho
        thi cu bam Brief mot lan la de xuat cu lai duoc ghi them mot ban. Bat duoc ngay
        13/09/2026."""
        try:
            rows = self.doc("agentProposals", [], top=2000)
        except Exception as exc:                 # chua publish app hoac chua co quyen doc
            log.warning("Khong doc duoc de xuat dang co: %s", exc)
            return set()
        return {r.get("referenceKey") for r in rows
                if r.get("status") in ("Proposed", "Executed") and r.get("referenceKey")}

    # Ten truong cua bang de xuat trong BC, doi sang ten ma bo nho tro ly dang dung.
    _TEN_DE_XUAT = {"proposalId": "proposal_id", "id": "bc_id", "actionType": "action_type",
                    "itemNo": "item_no", "fromLocationCode": "from_loc", "toLocationCode": "to_loc",
                    "resultDocumentNo": "result_doc", "resultDocumentType": "result_doc_type",
                    "reviewedBy": "approver", "reviewedAt": "approved_at", "createdAt": "created_at",
                    "referenceKey": "reference_key", "lotNo": "lot_no", "vendorNo": "vendor_no",
                    "sourceDocumentNo": "source_doc"}

    def de_xuat(self, top: int = 500) -> list[dict[str, Any]]:
        """De xuat doc tu BC, da doi ten truong cho khop bo nho tro ly.

        Vi sao can: bo nho tro ly chi giu nhung de xuat do CHINH phien nay tao ra, con BC thi giu
        het. Dung mo tro ly ra thay bang de xuat trong khi BC dang co 61 dong. Bat duoc ngay
        13/09/2026. Mock khong co bang nay, bo nho tro ly la nguon duy nhat."""
        if self.is_mock:
            return []
        try:
            rows = self.doc("agentProposals", [], top=top)
        except Exception as exc:
            log.warning("Khong doc duoc de xuat tu BC: %s", exc)
            return []
        ten_hang = {i["itemNo"]: i["description"] for i in self.items()}
        ra = []
        for r in rows:
            d = {self._TEN_DE_XUAT.get(k, k): v for k, v in r.items() if not k.startswith("@")}
            d.setdefault("item_desc", ten_hang.get(d.get("item_no", ""), d.get("item_no", "")))
            d["max_quantity"] = d.get("quantity")
            ra.append(d)
        return ra

    def approve(self, bc_id: str, approver_bc_user: str, comment: str = "") -> dict[str, Any]:
        """Live: POST .../agentProposals(id)/Microsoft.NAV.approve voi token uy quyen cua nguoi duyet (OBO).
        POC hien tai dung token app; TODO OBO khi co Teams SSO. Mock: gia lap codeunit NWV Agent Proposal Mgt."""
        self._kiem_con_de_xuat(bc_id)
        self.client.bound_action("agentProposals", bc_id, "approve", {"comment": comment[:250]})
        self.quen_nho("agentProposals")     # khong bo thi brief ke tiep van thay de xuat nay cho duyet
        if not self.is_mock:
            return self.client.get("agentProposals", bc_id)
        prop = self.client.get("agentProposals", bc_id)

        # Chi Transfer moi sinh Transfer Order. Loi da bat duoc khi QA: BlockPurchase tung tao
        # mot TO 0 cai di tu kho trung tam ve chinh kho trung tam roi bao kho di ship.
        # Live: BlockPurchase set Item."Blocked"/"Purchasing Blocked"; Markdown tao Sales Price;
        # WriteOff tao Item Journal Line; ReviewOnly chi danh dau. Xem design 0.2 phu luc C.
        if prop["actionType"] == "Purchase":
            # Mock: gia lap Purchase Order nhu BC that (codeunit NWV Agent Proposal Mgt. tao PO Open cho vendor cua de xuat)
            self._to_seq += 1
            po_no = f"PO-{self._to_seq}"
            # Don mua intercompany: ghi vao bo don gia lap de vong "doi tac da xuat kho chua" chay duoc tren mock.
            self.gia_lap_don_ic(po_no, prop["itemNo"], prop.get("itemDescription") or prop["itemNo"],
                                float(prop["quantity"]), prop["toLocationCode"], prop.get("vendorNo") or "MAROU")
            for r in self.client.data["agentProposals"]:
                if r["id"] == bc_id:
                    r.update({"status": "Executed", "reviewedBy": approver_bc_user, "reviewComment": comment,
                              "resultDocumentType": "Purchase Order", "resultDocumentNo": po_no})
            return {"resultDocumentNo": po_no, "resultDocumentType": "Purchase Order", "status": "Executed"}
        if prop["actionType"] == "PostReceipt":
            # Mock: gia lap codeunit NWV IC Receipt post Receive cho don mua, kem so lo doi tac da xuat.
            self._to_seq += 1
            rcpt = f"RCPT-{self._to_seq}"
            d = self._ic.get(prop.get("sourceDocumentNo") or "")
            if d:
                for l in d["lines"]:
                    l["received"] = l["quantity"]
                    l["outstanding"] = 0
                d["received"], d["outstanding"] = d["quantity"], 0
                d["purchaseReceipt"] = rcpt
            for r in self.client.data["agentProposals"]:
                if r["id"] == bc_id:
                    r.update({"status": "Executed", "reviewedBy": approver_bc_user, "reviewComment": comment,
                              "resultDocumentType": "Purchase Receipt", "resultDocumentNo": rcpt})
            return {"resultDocumentNo": rcpt, "resultDocumentType": "Purchase Receipt", "status": "Executed"}
        if prop["actionType"] == "WriteOff":
            # Mock: gia lap codeunit NWV Agent Proposal Mgt. 1.6.0.0 tao dong Item Journal (Negative Adjmt.) CHUA POST,
            # Document No. AGENT-<id>, lo va reason code. Ke toan post; tro ly theo doi bang ILE cung Document No.
            self._to_seq += 1
            doc_no = f"AGENT-{self._to_seq}"      # BC that: 'AGENT-' + Entry No. cua de xuat (codeunit 70102, 1.6.0.0)
            self._journal[doc_no] = {"id": doc_no, "documentNo": doc_no, "journalTemplateName": "ITEM", "journalBatchName": "AGENT",
                                     "lineNo": 10000 * (len(self._journal) + 1), "entryType": "Negative Adjmt.",
                                     "postingDate": self.today().isoformat(), "itemNo": prop["itemNo"],
                                     "locationCode": prop["fromLocationCode"], "quantity": prop["quantity"],
                                     "lotNo": prop.get("lotNo", ""), "reasonCode": "AGENT-EXP", "posted": False}
            for r in self.client.data["agentProposals"]:
                if r["id"] == bc_id:
                    r.update({"status": "Executed", "reviewedBy": approver_bc_user, "reviewComment": comment,
                              "resultDocumentType": "Item Journal Line", "resultDocumentNo": doc_no})
            return {"resultDocumentNo": doc_no, "resultDocumentType": "Item Journal Line", "status": "Executed"}
        if prop["actionType"] != "Transfer":
            label = {"BlockPurchase": "Chan mua them", "Markdown": "De nghi giam gia",
                     "WriteOff": "De nghi dieu chinh", "ReviewOnly": "Danh dau cho ra soat",
                     "Escalate": "Chuyen len nguoi phu trach"}.get(prop["actionType"], prop["actionType"])
            for r in self.client.data["agentProposals"]:
                if r["id"] == bc_id:
                    r.update({"status": "Executed", "reviewedBy": approver_bc_user, "reviewComment": comment,
                              "resultDocumentType": label, "resultDocumentNo": ""})
            return {"resultDocumentNo": "", "resultDocumentType": label, "status": "Executed"}

        # mock: tao Transfer Order gia lap
        self._to_seq += 1
        to_no = f"TO-{self._to_seq}"
        self._transfers[to_no] = {
            "no": to_no, "status": "Open", "shipped": False, "received": False,
            "fromLocationCode": prop["fromLocationCode"], "toLocationCode": prop["toLocationCode"],
            "itemNo": prop["itemNo"], "quantity": prop["quantity"], "createdBy": approver_bc_user,
            "createdAt": datetime.now(timezone.utc).isoformat(), "externalDocNo": f"AGENT {prop.get('proposalId', '')}",
        }
        for r in self.client.data["agentProposals"]:
            if r["id"] == bc_id:
                r.update({"status": "Executed", "reviewedBy": approver_bc_user, "reviewComment": comment,
                          "resultDocumentType": "Transfer Order", "resultDocumentNo": to_no})
        self._recalc_suggestion(prop["toLocationCode"], prop["itemNo"], in_transit_delta=float(prop["quantity"]))
        return {"resultDocumentNo": to_no, "status": "Executed"}

    def _recalc_suggestion(self, store: str, item_no: str, in_transit_delta: float = 0.0) -> None:
        """Mo phong job dem cua BC tinh lai NWV Repl. Suggestion sau khi co hang dang ve.
        Live: khong can, codeunit NWV Replenishment Calc lam viec nay."""
        if not self.is_mock:
            return
        for r in self.client.data["replenishmentSuggestions"]:
            if r["storeLocationCode"] == store and r["itemNo"] == item_no:
                r["storeQtyInTransit"] = float(r.get("storeQtyInTransit") or 0) + in_transit_delta
                avg = float(r["avgDailySalesQty"])
                total = float(r["storeQtyOnHand"]) + float(r["storeQtyInTransit"])
                r["daysOfCover"] = round(total / avg, 1) if avg > 0 else 9999
                r["stockOutRisk"] = avg > 0 and r["daysOfCover"] < 5
                r["reason"] = "Đủ hàng." if not r["stockOutRisk"] else r["reason"]
                return

    def execute_auto(self, bc_id: str, agent_bc_user: str, rule_code: str) -> dict[str, Any]:
        """Tro ly TU thuc thi trong pham vi policy. Chung tu tao duoi tai khoan cua tro ly,
        va comment ghi ro dong policy nao cho phep, de kiem toan truy nguoc.
        Day khong phai lach quyen: nguoi da uy quyen truoc bang policy, giong nhu mot job dinh ky."""
        return self.approve(bc_id, agent_bc_user, f"Tu dong theo policy {rule_code}")

    def undo_transfer(self, to_no: str, by_user: str) -> bool:
        """Hoan tac Transfer Order tro ly vua tao, khi chua ship.
        Live: goi bound action delete tren API page transferOrders; BC chan neu da ship."""
        t = self._transfers.get(to_no) if self.is_mock else None
        if not self.is_mock:
            raise NotImplementedError("Live: bound action cancel tren transferOrders")
        if not t or t["shipped"]:
            return False
        t["status"] = "Cancelled"
        t["cancelledBy"] = by_user
        self._recalc_suggestion(t["toLocationCode"], t["itemNo"], in_transit_delta=-float(t["quantity"]))
        return True

    def _kiem_con_de_xuat(self, bc_id: str) -> None:
        """De xuat co con ben BC khong. Bo nho tro ly song lau hon du lieu: o che do mo phong thi fixtures nap lai moi lan, con tren
        BC that thi nguoi khac co the da xoa dong do. Thieu cho nay, bam Duyet tra 500 thay vi mot cau doc duoc (16/09/2026)."""
        from bc_agent.bc_client import BCError
        try:
            self.client.get("agentProposals", bc_id)
        except KeyError:
            raise BCError("Đề xuất này không còn trong Business Central. Có thể nó thuộc phiên dữ liệu trước, hoặc đã bị xóa. "
                          "Bạn bấm Brief để lấy danh sách đề xuất hiện tại.") from None

    def reject(self, bc_id: str, approver_bc_user: str, comment: str) -> None:
        self._kiem_con_de_xuat(bc_id)
        self.client.bound_action("agentProposals", bc_id, "reject", {"comment": comment[:250]})
        self.quen_nho("agentProposals")
        if self.is_mock:
            for r in self.client.data["agentProposals"]:
                if r["id"] == bc_id:
                    r.update({"status": "Rejected", "reviewedBy": approver_bc_user, "reviewComment": comment})

    # ---------- dong Item Journal nhap cua de xuat Write-off (UC2 G2/A3, 16/09/2026)
    def dong_journal(self, doc_no: str) -> list[dict[str, Any]]:
        """Dong Item Journal con trong journal (chua post) mang Document No. nay. Live: API page nwvItemJournalLines (app 1.6.0.0)."""
        if self.is_mock:
            j = self._journal.get(doc_no)
            return [dict(j)] if j and not j["posted"] else []
        return self.doc("nwvItemJournalLines", [("documentNo", "eq", doc_no)], ttl=30, top=20)

    def da_post_journal(self, doc_no: str) -> bool:
        """Ke toan da post chua: co Item Ledger Entry mang Document No. AGENT-<id>."""
        if self.is_mock:
            j = self._journal.get(doc_no)
            return bool(j and j["posted"])
        return bool(self.doc("nwvItemLedgerEntries", [("documentNo", "eq", doc_no)], ttl=30, top=5))

    def gia_lap_post_journal(self, doc_no: str = "") -> list[str]:
        """Chi mock: gia lap ke toan post. Rong = post het. Tra danh sach Document No. da post."""
        if not self.is_mock:
            raise NotImplementedError("Chỉ mô phỏng. Trên Business Central kế toán post trong Item Journal.")
        ra = []
        for k, j in self._journal.items():
            if (not doc_no or k == doc_no) and not j["posted"]:
                j["posted"] = True
                ra.append(k)
        return ra

    # ---------- Intercompany: gui don mua sang company doi tac (16/09/2026)
    def gui_don_ic(self, doc_no: str) -> dict[str, Any]:
        """Goi `NWVDemoIntercompany.SendPurchaseOrder`: BC release don roi day sang inbox cua company doi tac, ben do
        Auto. Accept tao Sales Order. Release la viec cua nguoi mua, nen ham nay chi chay khi co nguoi bam nut."""
        if self.is_mock:
            self._to_seq += 1
            so = f"SO-{self._to_seq}"
            self._transfers[so] = {"no": so, "status": "Released", "shipped": False, "received": False,
                                   "itemNo": "", "quantity": 0, "toLocationCode": "", "fromLocationCode": ""}
            if doc_no in self._ic:
                self._ic[doc_no]["salesOrder"] = so
            return {"purchaseOrder": doc_no, "status": "Released", "icPartner": "MAROU", "salesOrder": so}
        return self.client.web_service("NWVDemoIntercompany", "SendPurchaseOrder", {"docNo": doc_no})

    # ---------- Intercompany phia nguoi mua: doi tac da xuat kho chua (16/09/2026)
    def ic_giao_hang(self, vendor_no: str = "") -> list[dict[str, Any]]:
        """Don mua intercompany cua company nay, kem phieu giao hang ben company doi tac (neu doi tac da post).

        Live: web service `NWVAgentICService.ShipmentStatus`, doc sang company kia bang ChangeCompany. Ham chi doc.
        Mock: dung bo don gia lap trong `self._ic`, do nut demo dung len."""
        if self.is_mock:
            return [dict(d) for d in self._ic.values() if not vendor_no or d.get("vendorNo") == vendor_no]
        kq = self.client.web_service("NWVAgentICService", "ShipmentStatus",
                                     {"configJson": json.dumps({"vendorNo": vendor_no}, ensure_ascii=False)})
        return (kq or {}).get("docs", []) if isinstance(kq, dict) else []

    def gia_lap_don_ic(self, doc_no: str, item_no: str, description: str, quantity: float, location: str,
                       vendor_no: str = "MAROU", sales_order: str = "") -> dict[str, Any]:
        """Chi mock: dung mot don mua intercompany de demo vong bao xuat kho va post nhan hang."""
        if not self.is_mock:
            raise NotImplementedError("Chỉ mô phỏng. Trên Business Central đơn mua do duyệt đề xuất Purchase sinh ra.")
        d = {"purchaseOrder": doc_no, "vendorNo": vendor_no, "vendorName": "Marou Chocolate (san xuat)", "icPartner": vendor_no,
             "partnerCompany": "NWV-MAROU", "status": "Released", "orderDate": self.today().strftime("%Y-%m-%d"),
             "expectedReceiptDate": "", "locationCode": location, "quantity": quantity, "outstanding": quantity, "received": 0.0,
             "salesOrder": sales_order,
             "lines": [{"lineNo": 10000, "itemNo": item_no, "description": description, "locationCode": location,
                        "quantity": quantity, "outstanding": quantity, "received": 0.0, "unitOfMeasureCode": "PCS"}],
             "shipment": {"posted": False}}
        self._ic[doc_no] = d
        return d

    def post_giao_hang_doi_tac(self, doc_no: str, company: str = "") -> dict[str, Any]:
        """Nut demo "Marou da xuat kho": post Ship cho don ban ben company doi tac. Tren he that day la viec cua nguoi kho
        Marou bam trong BC, tro ly khong bao gio goi. O day chi de demo chay duoc mot minh."""
        if self.is_mock:
            d = self._ic[doc_no]
            d["shipment"] = {"posted": True, "no": f"SHP-{len(self._ic)}{doc_no[-3:]}",
                             "postingDate": self.today().strftime("%Y-%m-%d"), "salesOrder": d.get("salesOrder", ""),
                             "sellToCustomerNo": "DAKAO", "locationCode": "W0003", "shipmentCount": 1,
                             "lines": [{"itemNo": l["itemNo"], "description": l["description"], "quantity": l["quantity"],
                                        "lots": [{"lotNo": f"L-{l['itemNo']}", "quantity": l["quantity"], "expirationDate": ""}]}
                                       for l in d["lines"]]}
            return {"company": company or "NWV-MAROU", "salesOrder": d.get("salesOrder", ""), "shipment": d["shipment"]["no"],
                    "postingDate": d["shipment"]["postingDate"]}
        return self.client.web_service("NWVDemoIntercompany", "PostSalesShipment", {"docNo": doc_no}, company=company)

    def transfer(self, to_no: str) -> dict[str, Any] | None:
        if self.is_mock:
            return self._transfers.get(to_no)
        raise NotImplementedError("Live: can API page transferOrders (design 0.2, phu luc C)")

    def mark_transfer(self, to_no: str, *, shipped: bool | None = None, received: bool | None = None) -> None:
        """Demo mock: kho bam 'da ship'. Live: BC tu cap nhat khi post shipment; tro ly chi doc."""
        t = self._transfers[to_no]
        if shipped is not None:
            t["shipped"] = shipped
            t["status"] = "Shipped" if shipped else t["status"]
        if received is not None:
            t["received"] = received
            t["status"] = "Received" if received else t["status"]

    def mark_under_review(self, exc_id: str) -> None:
        self.client.patch("discountExceptions", exc_id, {"status": "UnderReview"})

    def set_explanation(self, exc_id: str, text: str, by_user: str) -> None:
        """Live: POST exceptionExplanations (API moi, design 0.2 phu luc C) roi BC set Explained.
        Mock: ghi thang vao ban ghi."""
        if self.is_mock:
            for r in self.client.data["discountExceptions"]:
                if r["id"] == exc_id:
                    r.update({"status": "Explained", "explanation": text, "explainedBy": by_user})
            return
        self.client.create("exceptionExplanations", {"exceptionId": exc_id, "explanation": text, "answeredBy": by_user})

    # ---------- lich su ban theo ngay (cho dieu tra va tu danh gia)
    def sales_history(self, item_no: str | None = None, location: str | None = None,
                      days: int = 180) -> list[dict[str, Any]]:
        """Mock: doc sales_history.csv. Live: doc Item Ledger Entry loai Sale qua API page
        nwvItemLedgerEntries (page 70201 trong app NWV Marou Agent). Ten truong camelCase
        trung voi page itemLedgerEntries cu, chi doi ten entity set."""
        from datetime import timedelta
        since = (self.today() - timedelta(days=days)).isoformat()
        if not self.is_mock:
            # Doc theo CUA SO CHUNG roi loc trong Python, thay vi hoi BC rieng cho tung cap
            # mat hang x dia diem. Ly do: mo mot trang Chi tiet lo la mot cau hoi rieng mat
            # 1,7 giay, va moi lo lai la mot cau hoi moi. Doc chung thi ban nho cua
            # `doc()` dung duoc cho moi lo, moi cua hang va ca cho brief.
            cua_so = next((b for b in self.CUA_SO_BAN if b >= days), self.CUA_SO_BAN[-1])
            tu = (self.today() - timedelta(days=cua_so)).isoformat()
            rows = self.doc("nwvItemLedgerEntries",
                            [("entryType", "eq", "Sale"), ("postingDate", "ge", tu)], top=50000,
                            select="postingDate,itemNo,locationCode,quantity")
            out = []
            for r in rows:
                ngay = str(r["postingDate"])[:10]
                if ngay < since:
                    continue
                if item_no and r["itemNo"] != item_no:
                    continue
                if location and r["locationCode"] != location:
                    continue
                out.append({"date": ngay, "item_no": r["itemNo"],
                            "location_code": r["locationCode"], "qty": -float(r["quantity"])})
            return out
        rows = self._sales_rows()
        out = []
        for r in rows:
            if r["date"] < since:
                continue
            if item_no and r["item_no"] != item_no:
                continue
            if location and r["location_code"] != location:
                continue
            out.append(r)
        return out

    def ngay_ban_dau_tien(self) -> str | None:
        """Ngay ban som nhat, dang YYYY-MM-DD. Chi de tra do dai lich su tren man hinh do phu.

        Doc DUNG MOT dong bang `$orderby` thay vi keo ca 400 ngay ve roi lay min: ban cu mat
        12 giay cho mot con so."""
        if not self.is_mock:
            rows = self.doc("nwvItemLedgerEntries", [("entryType", "eq", "Sale")],
                            orderby="postingDate asc", top=1, select="postingDate")
            return str(rows[0]["postingDate"])[:10] if rows else None
        rows = self._sales_rows()
        return min(r["date"] for r in rows) if rows else None

    def _sales_rows(self) -> list[dict[str, Any]]:
        """Doc sales_history.csv mot lan roi giu lai. Lich su ban khong doi trong mot phien,
        va moi lan khoi tao tro ly can quet vai chuc cap nen doc lai la phi.

        Doc lai co retry vi tren may Windows co OneDrive dang dong bo, file co the bi khoa
        vai tram mili giay dung luc uvicorn --reload khoi tao lai tro ly. Truoc day loi
        PermissionError o day lam chet ca app luc khoi dong."""
        if self._sales_cache is not None:
            return self._sales_cache
        import csv
        import time
        from bc_agent.config import FIXTURES_DIR
        path = FIXTURES_DIR / "sales_history.csv"
        last: Exception | None = None
        for attempt in range(4):
            try:
                with path.open(encoding="utf-8") as f:
                    rows = [{"date": r["date"], "item_no": r["item_no"],
                             "location_code": r["location_code"], "qty": float(r["qty"])}
                            for r in csv.DictReader(f)]
                self._sales_cache = rows
                return rows
            except (PermissionError, OSError) as exc:
                last = exc
                time.sleep(0.25 * (attempt + 1))
        raise FixtureLocked(f"Khong doc duoc {path.name} sau 4 lan thu: {last}") from last

    def today(self):
        """Ngay neo cua tro ly. Phai trung voi ngay ma lop AL da tinh, khong phai ngay may chay.

        Mock: 18/09/2026, ngay cuoi cua bo du lieu demo. Live: doc `As Of Date` tren bang ket qua
        cua AL, tuc WorkDate luc Job Queue chay. Lech hai con so nay thi cua so lich su ban va
        so ngay ke tu lan ban cuoi deu sai, ma khong co gi bao loi.
        """
        from datetime import date
        if self.is_mock:
            return date(2026, 9, 18)
        if self._as_of is None:
            self._as_of = self._read_as_of() or date.today()
        return self._as_of

    def _read_as_of(self):
        from datetime import date
        try:
            rows = self.client.list("inventoryHealthLines", top=1, select="asOfDate")
        except Exception as exc:                       # chua publish, chua co quyen, chua tinh
            log.warning("Khong doc duoc As Of Date tu bang ket qua: %s", exc)
            return None
        raw = str((rows[0] if rows else {}).get("asOfDate") or "")[:10]
        if not raw or raw.startswith("0001-01-01"):
            log.warning("Bang NWV Inv. Health Line chua co As Of Date, tam dung ngay he thong")
            return None
        return date.fromisoformat(raw)
