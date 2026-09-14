"""MockBCClient: cung interface voi BCClient, du lieu doc/ghi tren fixtures JSON.

Dung de:
  - demo kich ban khi chua co credential sandbox
  - test tool layer khong can mang
Ghi (create/patch/bound_action) chi thay doi ban sao trong bo nho; goi save() de ghi ra file runs/.
"""
from __future__ import annotations

import copy
import json
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from .config import FIXTURES_DIR
from .odata import Condition, apply_in_python

_ENTITY_FILES = {
    "inventoryHealthLines": "inventory_health_lines.json",
    "replenishmentSuggestions": "replenishment_suggestions.json",
    "discountExceptions": "discount_exceptions.json",
    "agentProposals": "agent_proposals.json",
    "posDiscountLogs": "pos_discount_logs.json",
    "nwvPurchaseOrderLines": "purchase_order_lines.json",
    "nwvPurchaseReceiptLines": "purchase_receipt_lines.json",
    "forecastAccuracies": "forecast_accuracies.json",
    "forecastDailies": "forecast_dailies.json",
    "lsForecastEntries": "ls_forecast_entries.json",
    "plannedSalesDemands": "planned_sales_demands.json",
    "plannedEvents": "planned_events.json",
    "lsPeriodicDiscounts": "ls_periodic_discounts.json",
    "lsPeriodicDiscountLines": "ls_periodic_discount_lines.json",
    "lsValidationPeriods": "ls_validation_periods.json",
    "lsStorePriceGroups": "ls_store_price_groups.json",
    "nwvItems": "nwv_items.json",
    "supplierScorecards": "supplier_scorecards.json",
}


def _read_json(path: Path) -> list[dict[str, Any]]:
    """Doc mot file fixtures, co retry.

    Tren may Windows co OneDrive dang dong bo, file vua ghi xong co the bi khoa vai tram
    mili giay (PermissionError), hoac doc trung luc dong bo ghi do dang (JSONDecodeError).
    Truoc day ca hai deu lam chet tien trinh uvicorn luc --reload khoi tao lai."""
    import time
    last: Exception | None = None
    for attempt in range(4):
        try:
            return json.loads(path.read_text(encoding="utf-8"))
        except (PermissionError, OSError, json.JSONDecodeError) as exc:
            last = exc
            time.sleep(0.25 * (attempt + 1))
    raise OSError(f"Khong doc duoc fixtures {path.name} sau 4 lan thu: {last}") from last


class MockBCClient:
    def __init__(self, fixtures_dir: Path = FIXTURES_DIR):
        self.fixtures_dir = fixtures_dir
        self.data: dict[str, list[dict[str, Any]]] = {}
        for entity, fname in _ENTITY_FILES.items():
            p = fixtures_dir / fname
            self.data[entity] = _read_json(p) if p.exists() else []
        self.base = f"mock://{fixtures_dir}"
        self.writes: list[dict[str, Any]] = []

    # `select` co de trung chu ky voi BCClient. Mock doc san ca dong nen bo qua, khong loc cot.
    def query(self, entity_set: str, conds: list[Condition] | None = None,
              orderby: str | None = None, top: int | None = None,
              select: str | None = None) -> list[dict[str, Any]]:
        return copy.deepcopy(apply_in_python(self.data[entity_set], conds or [], orderby, top))

    def get(self, entity_set: str, record_id: str) -> dict[str, Any]:
        for r in self.data[entity_set]:
            if r.get("id") == record_id:
                return copy.deepcopy(r)
        raise KeyError(f"{entity_set}({record_id}) not found")

    def create(self, entity_set: str, body: dict[str, Any]) -> dict[str, Any]:
        rec = dict(body)
        rec["id"] = str(uuid.uuid4())
        if entity_set == "agentProposals":
            # Mo phong OnInsertRecord cua page 70113: status luon Proposed
            rec["proposalId"] = str(uuid.uuid4())
            rec["status"] = "Proposed"
            rec["createdAt"] = datetime.now(timezone.utc).isoformat()
            rec["createdByAgent"] = "MOCK-AGENT"
        self.data[entity_set].append(rec)
        self.writes.append({"op": "create", "entity": entity_set, "body": rec})
        return copy.deepcopy(rec)

    def patch(self, entity_set: str, record_id: str, body: dict[str, Any], etag: str = "*") -> dict[str, Any]:
        for r in self.data[entity_set]:
            if r.get("id") == record_id:
                if entity_set == "discountExceptions" and body.get("status") not in (None, "Open", "UnderReview"):
                    raise RuntimeError("Agent may only set status to Under Review (mirror of page 70112 OnModifyRecord)")
                r.update(body)
                self.writes.append({"op": "patch", "entity": entity_set, "id": record_id, "body": body})
                return copy.deepcopy(r)
        raise KeyError(f"{entity_set}({record_id}) not found")

    def bound_action(self, entity_set: str, record_id: str, action: str, body: dict[str, Any] | None = None) -> None:
        # approve/reject la cua nguoi duyet; mock chi ghi nhan de test
        for r in self.data[entity_set]:
            if r.get("id") == record_id:
                r["status"] = {"approve": "Executed", "reject": "Rejected"}.get(action, r.get("status"))
                self.writes.append({"op": "action", "entity": entity_set, "id": record_id, "action": action, "body": body})
                return
        raise KeyError(f"{entity_set}({record_id}) not found")

    def save(self, out_dir: Path) -> Path:
        out_dir.mkdir(parents=True, exist_ok=True)
        p = out_dir / "mock_state_after_run.json"
        p.write_text(json.dumps({"writes": self.writes, "agentProposals": self.data["agentProposals"]},
                                ensure_ascii=False, indent=2), encoding="utf-8")
        return p
