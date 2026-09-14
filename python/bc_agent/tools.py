"""Tool cho model (khai theo dang Anthropic, bc_agent.llm doi sang OpenAI khi can) va dispatcher goi BC.

Nguyen tac thiet ke tool (ghi trong design doc, muc "Agent duoc lam gi"):
  1. Agent chi DOC so da tinh (health line, suggestion, exception). Khong co tool doc Item Ledger Entry tho.
  2. Agent chi GHI vao agentProposals va doi status exception sang Under Review. Khong co tool tao chung tu.
  3. So luong trong de xuat Transfer bi chan bang constrainedQty cua suggestion: agent khong duoc bia so.
  4. Moi tool call duoc log de audit (runner.py).
"""
from __future__ import annotations

import json
from typing import Any, Callable

from .config import settings
from .odata import Condition

SCENARIOS = ("InventoryHealth", "StoreReplenishment", "DiscountGovernance")
ACTIONS = ("ReviewOnly", "Transfer", "Markdown", "BlockPurchase", "WriteOff", "AuditNote", "Escalate")
TIERS = ("Healthy", "StockOutRisk", "Excess", "SlowMoving", "NearExpiry", "Expired")

# ------------------------------------------------------------------ tool schemas

TOOL_LIST_INV_HEALTH = {
    "name": "list_inventory_health",
    "description": (
        "Doc bang inventory health da tinh san trong Business Central (moi dong = item x location x lot). "
        "Tier: Healthy, Stock-out Risk, Excess, Slow-moving, Near Expiry, Expired. riskScore 0..100. "
        "Ket qua da duoc sap theo riskScore giam dan."
    ),
    "input_schema": {
        "type": "object",
        "properties": {
            "tier": {"type": "string", "enum": list(TIERS), "description": "Loc theo tier, bo trong de lay tat ca"},
            "location_code": {"type": "string", "description": "Loc theo location, bo trong de lay tat ca"},
            "min_risk_score": {"type": "integer", "minimum": 0, "maximum": 100, "default": 50},
            "top": {"type": "integer", "minimum": 1, "maximum": 200, "default": 50},
        },
    },
}

TOOL_LIST_REPL = {
    "name": "list_replenishment_suggestions",
    "description": (
        "Doc de xuat bo sung store da tinh san (days of cover, targetQty, suggestedQty, constrainedQty theo ton kho trung tam). "
        "Mac dinh chi lay dong co stockOutRisk = true."
    ),
    "input_schema": {
        "type": "object",
        "properties": {
            "store_location_code": {"type": "string"},
            "stock_out_risk_only": {"type": "boolean", "default": True},
            "top": {"type": "integer", "minimum": 1, "maximum": 200, "default": 50},
        },
    },
}

TOOL_LIST_DISC_EXC = {
    "name": "list_discount_exceptions",
    "description": (
        "Doc ngoai le discount do rule DG-01/DG-02/DG-03 phat hien. Severity Low/Medium/High. "
        "Status Open la chua ai xem."
    ),
    "input_schema": {
        "type": "object",
        "properties": {
            "status": {"type": "string", "enum": ["Open", "UnderReview", "Explained", "Confirmed", "Dismissed"], "default": "Open"},
            "severity": {"type": "string", "enum": ["Low", "Medium", "High"]},
            "store_no": {"type": "string"},
            "top": {"type": "integer", "minimum": 1, "maximum": 200, "default": 50},
        },
    },
}

TOOL_GET_DISC_CONTEXT = {
    "name": "get_discount_log_context",
    "description": (
        "Lay cac dong discount cua mot staff tai mot store trong mot ngay, de hieu boi canh truoc khi viet ghi chu audit "
        "(loai discount, co manager override, ly do infocode, member card)."
    ),
    "input_schema": {
        "type": "object",
        "properties": {
            "store_no": {"type": "string"},
            "staff_id": {"type": "string"},
            "trans_date": {"type": "string", "description": "YYYY-MM-DD"},
        },
        "required": ["store_no", "staff_id", "trans_date"],
    },
}

TOOL_MARK_UNDER_REVIEW = {
    "name": "mark_exception_under_review",
    "description": "Doi status mot discount exception tu Open sang Under Review sau khi agent da doc va viet ghi chu.",
    "input_schema": {
        "type": "object",
        "properties": {"exception_id": {"type": "string"}},
        "required": ["exception_id"],
    },
}

TOOL_LIST_PROPOSALS = {
    "name": "list_existing_proposals",
    "description": "Doc de xuat da co (mac dinh status Proposed) de khong tao trung. So khop bang referenceKey.",
    "input_schema": {
        "type": "object",
        "properties": {
            "scenario": {"type": "string", "enum": list(SCENARIOS)},
            "status": {"type": "string", "enum": ["Proposed", "Approved", "Rejected", "Executed", "Failed"], "default": "Proposed"},
        },
        "required": ["scenario"],
    },
}

TOOL_CREATE_PROPOSAL = {
    "name": "create_proposal",
    "description": (
        "Ghi mot de xuat vao Business Central de NGUOI duyet. Khong tao chung tu. "
        "Voi Transfer: quantity phai <= constrainedQty cua suggestion tuong ung, from = kho trung tam, to = store. "
        "rationale viet bang tieng Viet, ngan, neu con so cu the lay tu du lieu da doc. "
        "evidence la object JSON chua dung cac so da doc (de audit)."
    ),
    "input_schema": {
        "type": "object",
        "properties": {
            "scenario": {"type": "string", "enum": list(SCENARIOS)},
            "action_type": {"type": "string", "enum": list(ACTIONS)},
            "item_no": {"type": "string"},
            "lot_no": {"type": "string"},
            "from_location_code": {"type": "string"},
            "to_location_code": {"type": "string"},
            "quantity": {"type": "number", "minimum": 0},
            "reference_key": {"type": "string", "description": "Item|Location|Lot, Store|Item, hoac referenceKey cua exception"},
            "rationale": {"type": "string", "maxLength": 2000},
            "priority_score": {"type": "integer", "minimum": 0, "maximum": 100},
            "evidence": {"type": "object"},
        },
        "required": ["scenario", "action_type", "reference_key", "rationale", "priority_score", "evidence"],
    },
}

TOOLSETS: dict[str, list[dict[str, Any]]] = {
    "inventory_health": [TOOL_LIST_INV_HEALTH, TOOL_LIST_PROPOSALS, TOOL_CREATE_PROPOSAL],
    "replenishment": [TOOL_LIST_REPL, TOOL_LIST_PROPOSALS, TOOL_CREATE_PROPOSAL],
    "discount_governance": [TOOL_LIST_DISC_EXC, TOOL_GET_DISC_CONTEXT, TOOL_MARK_UNDER_REVIEW, TOOL_LIST_PROPOSALS, TOOL_CREATE_PROPOSAL],
}


# ------------------------------------------------------------------ dispatcher

class ToolDispatcher:
    """Thuc thi tool tren client (BCClient hoac MockBCClient). Giu bo nho cac suggestion da doc de chan so luong."""

    def __init__(self, client: Any, run_id: str, model_name: str):
        self.client = client
        self.run_id = run_id
        self.model_name = model_name
        self.proposals_created = 0
        self._seen_suggestions: dict[str, dict[str, Any]] = {}   # "store|item" -> suggestion
        self._handlers: dict[str, Callable[..., Any]] = {
            "list_inventory_health": self.list_inventory_health,
            "list_replenishment_suggestions": self.list_replenishment_suggestions,
            "list_discount_exceptions": self.list_discount_exceptions,
            "get_discount_log_context": self.get_discount_log_context,
            "mark_exception_under_review": self.mark_exception_under_review,
            "list_existing_proposals": self.list_existing_proposals,
            "create_proposal": self.create_proposal,
        }

    def dispatch(self, name: str, args: dict[str, Any]) -> str:
        if name not in self._handlers:
            return json.dumps({"error": f"unknown tool {name}"})
        try:
            result = self._handlers[name](**args)
            return json.dumps(result, ensure_ascii=False, default=str)
        except Exception as e:  # tra loi cho model thay vi crash, de model doi huong
            return json.dumps({"error": f"{type(e).__name__}: {e}"}, ensure_ascii=False)

    # ---- read tools
    def list_inventory_health(self, tier: str | None = None, location_code: str | None = None,
                              min_risk_score: int = 50, top: int = 50) -> list[dict[str, Any]]:
        conds: list[Condition] = [("riskScore", "ge", min_risk_score)]
        if tier:
            conds.append(("tier", "eq", tier))
        if location_code:
            conds.append(("locationCode", "eq", location_code))
        return self.client.query("inventoryHealthLines", conds, orderby="riskScore desc", top=top)

    def list_replenishment_suggestions(self, store_location_code: str | None = None,
                                       stock_out_risk_only: bool = True, top: int = 50) -> list[dict[str, Any]]:
        conds: list[Condition] = []
        if stock_out_risk_only:
            conds.append(("stockOutRisk", "eq", True))
        if store_location_code:
            conds.append(("storeLocationCode", "eq", store_location_code))
        if self.client.__class__.__name__ == "MockBCClient":
            rows = self.client.query("replenishmentSuggestions", conds, orderby="daysOfCover asc", top=top)
        else:
            # BC that: de xuat lay tu LS Replenishment (journal MAROU-TO), cung hinh dang voi bang cu da xoa.
            from assistant.gateway import BCGateway
            from .odata import apply_in_python
            rows = apply_in_python(BCGateway(self.client).goi_y_ls(), conds, "daysOfCover asc", top)
        for r in rows:
            self._seen_suggestions[f"{r['storeLocationCode']}|{r['itemNo']}"] = r
        return rows

    def list_discount_exceptions(self, status: str = "Open", severity: str | None = None,
                                 store_no: str | None = None, top: int = 50) -> list[dict[str, Any]]:
        conds: list[Condition] = [("status", "eq", status)]
        if severity:
            conds.append(("severity", "eq", severity))
        if store_no:
            conds.append(("storeNo", "eq", store_no))
        rows = self.client.query("discountExceptions", conds, top=top)
        # Sap theo muc do trong Python: OData sap enum theo ordinal, nhung mock sap theo chuoi; lam o day cho nhat quan
        rank = {"High": 2, "Medium": 1, "Low": 0}
        return sorted(rows, key=lambda r: (rank.get(r.get("severity"), -1), r.get("transDate", "")), reverse=True)

    def get_discount_log_context(self, store_no: str, staff_id: str, trans_date: str) -> list[dict[str, Any]]:
        conds: list[Condition] = [("storeNo", "eq", store_no), ("staffId", "eq", staff_id), ("transDate", "eq", trans_date)]
        return self.client.query("posDiscountLogs", conds, orderby="transTime asc", top=200)

    def list_existing_proposals(self, scenario: str, status: str = "Proposed") -> list[dict[str, Any]]:
        rows = self.client.query("agentProposals", [("scenario", "eq", scenario), ("status", "eq", status)], top=500)
        # Chi tra ve phan can de so khop, khong tra evidence dai
        return [{k: r.get(k) for k in ("id", "referenceKey", "actionType", "quantity", "createdAt")} for r in rows]

    # ---- write tools (bi gioi han)
    def mark_exception_under_review(self, exception_id: str) -> dict[str, Any]:
        return self.client.patch("discountExceptions", exception_id, {"status": "UnderReview"})

    def create_proposal(self, scenario: str, action_type: str, reference_key: str, rationale: str,
                        priority_score: int, evidence: dict[str, Any], item_no: str = "", lot_no: str = "",
                        from_location_code: str = "", to_location_code: str = "", quantity: float = 0) -> dict[str, Any]:
        if scenario not in SCENARIOS or action_type not in ACTIONS:
            raise ValueError("scenario/action_type khong hop le")
        if self.proposals_created >= settings.max_proposals_per_run:
            raise RuntimeError(f"Da dat gioi han {settings.max_proposals_per_run} de xuat/run. Dung lai va tong ket.")

        if action_type == "Transfer":
            if not (item_no and from_location_code and to_location_code and quantity > 0):
                raise ValueError("Transfer can item_no, from_location_code, to_location_code, quantity > 0")
            key = f"{to_location_code}|{item_no}"
            sug = self._seen_suggestions.get(key)
            if sug is None:
                raise ValueError("Chua doc suggestion cho store|item nay; goi list_replenishment_suggestions truoc")
            if quantity > float(sug["constrainedQty"]):
                raise ValueError(f"quantity {quantity} > constrainedQty {sug['constrainedQty']} cua suggestion; khong duoc vuot")

        # chong trung theo referenceKey
        dup = self.client.query("agentProposals", [("scenario", "eq", scenario), ("status", "eq", "Proposed"),
                                                   ("referenceKey", "eq", reference_key)], top=1)
        if dup:
            raise RuntimeError(f"Da co de xuat Proposed cho referenceKey {reference_key} (id {dup[0]['id']}); bo qua")

        body = {
            "scenario": scenario,
            "actionType": action_type,
            "itemNo": item_no,
            "lotNo": lot_no,
            "fromLocationCode": from_location_code,
            "toLocationCode": to_location_code,
            "quantity": quantity,
            "referenceKey": reference_key,
            "rationale": rationale[:2000],
            "priorityScore": int(priority_score),
            "evidenceJson": json.dumps(evidence, ensure_ascii=False, default=str),
            "modelName": self.model_name[:50],
            "runId": self.run_id[:50],
        }
        created = self.client.create("agentProposals", body)
        self.proposals_created += 1
        return {"id": created.get("id"), "proposalId": created.get("proposalId"), "status": created.get("status")}
