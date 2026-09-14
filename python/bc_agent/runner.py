"""Vong lap agent. Backend LLM:
  - bc_agent.llm.build_llm() : Azure OpenAI (mac dinh) hoac Claude, manual loop de chen approval gate/log.
  - ScriptedLLM              : khong goi API; di theo policy co dinh cho tung kich ban de test tool layer end-to-end.

Moi tool call va ket qua duoc ghi vao runs/<run_id>.jsonl. Day la log audit cua POC.
"""
from __future__ import annotations

import json
import logging
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from types import SimpleNamespace
from typing import Any, Protocol

from .config import settings
from .llm import ClaudeLLM  # noqa: F401  giu ten cu cho code ngoai import
from .tools import ToolDispatcher

log = logging.getLogger(__name__)


class LLM(Protocol):
    def complete(self, system: str, messages: list[dict[str, Any]], tools: list[dict[str, Any]]) -> Any: ...


# ------------------------------------------------------------------ Scripted backend (offline)

def _tool_use(name: str, inp: dict[str, Any]) -> SimpleNamespace:
    return SimpleNamespace(type="tool_use", id=f"toolu_{uuid.uuid4().hex[:12]}", name=name, input=inp)


def _text(t: str) -> SimpleNamespace:
    return SimpleNamespace(type="text", text=t)


def _resp(blocks: list[Any], stop: str) -> SimpleNamespace:
    return SimpleNamespace(content=blocks, stop_reason=stop)


class ScriptedLLM:
    """Policy co dinh, du de chung minh tool layer va rang buoc (khong bia so, khong trung, gioi han so de xuat).

    Khong phai agent thong minh. Dung khi LLM_MODE=scripted.
    """

    def __init__(self, scenario_key: str, max_items: int = 5):
        self.scenario_key = scenario_key
        self.max_items = max_items
        self.step = 0
        self.rows: list[dict[str, Any]] = []
        self.existing: set[str] = set()
        self.created: list[str] = []

    @staticmethod
    def _last_tool_results(messages: list[dict[str, Any]]) -> list[Any]:
        last = messages[-1]
        if last["role"] != "user" or not isinstance(last["content"], list):
            return []
        out = []
        for blk in last["content"]:
            if blk.get("type") == "tool_result":
                try:
                    out.append(json.loads(blk["content"]))
                except (TypeError, ValueError):
                    out.append(blk["content"])
        return out

    def complete(self, system: str, messages: list[dict[str, Any]], tools: list[dict[str, Any]]) -> Any:
        results = self._last_tool_results(messages)
        self.step += 1
        sk = self.scenario_key
        scen = {"inventory_health": "InventoryHealth", "replenishment": "StoreReplenishment",
                "discount_governance": "DiscountGovernance"}[sk]

        if self.step == 1:
            return _resp([_tool_use("list_existing_proposals", {"scenario": scen})], "tool_use")
        if self.step == 2:
            self.existing = {r["referenceKey"] for r in results[0] if isinstance(r, dict)}
            if sk == "inventory_health":
                return _resp([_tool_use("list_inventory_health", {"min_risk_score": 60, "top": 20})], "tool_use")
            if sk == "replenishment":
                return _resp([_tool_use("list_replenishment_suggestions", {"stock_out_risk_only": True, "top": 20})], "tool_use")
            return _resp([_tool_use("list_discount_exceptions", {"status": "Open", "top": 20})], "tool_use")
        if self.step == 3:
            self.rows = [r for r in results[0] if isinstance(r, dict)][: self.max_items]
            calls = []
            for r in self.rows:
                calls.append(self._proposal_for(sk, scen, r))
                if sk == "discount_governance":
                    calls.append(_tool_use("mark_exception_under_review", {"exception_id": r["id"]}))
            if not calls:
                return _resp([_text("Khong co dong nao vuot nguong. Khong tao de xuat.")], "end_turn")
            return _resp(calls, "tool_use")
        # step 4: tong ket
        ok = [r for r in results if isinstance(r, dict) and "proposalId" in r]
        err = [r for r in results if isinstance(r, dict) and "error" in r]
        return _resp([_text(f"Da tao {len(ok)} de xuat, {len(err)} bi tu choi boi rang buoc "
                            f"({'; '.join(e['error'][:80] for e in err) if err else 'khong co'}). "
                            "Cac de xuat dang cho nguoi duyet tren page NWV Agent Proposals.")], "end_turn")

    def _proposal_for(self, sk: str, scen: str, r: dict[str, Any]) -> SimpleNamespace:
        if sk == "inventory_health":
            ref = f"{r['itemNo']}|{r['locationCode']}|{r.get('lotNo', '')}"
            action = {"Expired": "WriteOff", "NearExpiry": "Markdown", "StockOutRisk": "ReviewOnly",
                      "SlowMoving": "Markdown", "Excess": "BlockPurchase"}.get(r["tier"], "ReviewOnly")
            return _tool_use("create_proposal", {
                "scenario": scen, "action_type": action, "item_no": r["itemNo"], "lot_no": r.get("lotNo", ""),
                "from_location_code": r["locationCode"], "reference_key": ref,
                "rationale": f"{r['tier']}: {r['riskReason']} Ton {r['quantityOnHand']} {r.get('baseUnitOfMeasure', '')}, gia tri {r['inventoryValue']:,.0f}.",
                "priority_score": int(r["riskScore"]),
                "evidence": {k: r[k] for k in ("quantityOnHand", "daysOfCover", "daysToExpiry", "daysSinceLastSale", "inventoryValue", "riskScore")},
            })
        if sk == "replenishment":
            ref = f"{r['storeLocationCode']}|{r['itemNo']}"
            return _tool_use("create_proposal", {
                "scenario": scen, "action_type": "Transfer", "item_no": r["itemNo"],
                "from_location_code": "W0003", "to_location_code": r["storeLocationCode"],
                "quantity": float(r["constrainedQty"]), "reference_key": ref,
                "rationale": f"Store {r['storeLocationCode']} con {r['daysOfCover']} ngay ton cho {r['itemNo']}. {r['reason']}",
                "priority_score": max(0, min(100, int(100 - float(r["daysOfCover"]) * 10))),
                "evidence": {k: r[k] for k in ("storeQtyOnHand", "storeQtyInTransit", "avgDailySalesQty", "daysOfCover", "targetQty", "suggestedQty", "warehouseQtyAvailable", "constrainedQty")},
            })
        # discount governance
        sev_score = {"High": 90, "Medium": 60, "Low": 30}.get(r["severity"], 50)
        return _tool_use("create_proposal", {
            "scenario": scen, "action_type": "Escalate" if r["severity"] == "High" else "AuditNote",
            "item_no": r.get("itemNo", ""), "reference_key": f"{r['ruleCode']}|{r['referenceKey']}",
            "rationale": f"{r['ruleCode']} {r['severity']}: {r['description']} Staff {r['staffId']} store {r['storeNo']} ngay {r['transDate']}.",
            "priority_score": sev_score,
            "evidence": {k: r.get(k) for k in ("ruleCode", "metricValue", "thresholdValue", "discountAmount", "occurrenceCount")},
        })


# ------------------------------------------------------------------ runner

@dataclass
class RunResult:
    run_id: str
    scenario_key: str
    final_text: str
    tool_calls: int
    proposals_created: int
    log_path: Path
    transcript: list[dict[str, Any]] = field(default_factory=list)


class AgentRunner:
    def __init__(self, client: Any, llm: LLM, model_name: str):
        self.client = client
        self.llm = llm
        self.model_name = model_name

    def run(self, scenario_key: str, system: str, task: str, tools: list[dict[str, Any]]) -> RunResult:
        run_id = f"{scenario_key}-{datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')}-{uuid.uuid4().hex[:6]}"
        settings.log_dir.mkdir(parents=True, exist_ok=True)
        log_path = settings.log_dir / f"{run_id}.jsonl"
        dispatcher = ToolDispatcher(self.client, run_id, self.model_name)
        messages: list[dict[str, Any]] = [{"role": "user", "content": task}]
        tool_calls = 0
        final_text = ""

        def logline(kind: str, payload: dict[str, Any]) -> None:
            with log_path.open("a", encoding="utf-8") as f:
                f.write(json.dumps({"ts": datetime.now(timezone.utc).isoformat(), "kind": kind, **payload},
                                   ensure_ascii=False, default=str) + "\n")

        logline("start", {"run_id": run_id, "scenario": scenario_key, "model": self.model_name, "bc": getattr(self.client, "base", "?")})

        for iteration in range(settings.max_tool_iterations):
            response = self.llm.complete(system, messages, tools)
            content = list(response.content)
            texts = [b.text for b in content if getattr(b, "type", "") == "text"]
            if texts:
                final_text = "\n".join(texts)

            if response.stop_reason == "refusal":
                logline("refusal", {"iteration": iteration})
                final_text = final_text or "Model tu choi yeu cau (stop_reason=refusal)."
                break
            if response.stop_reason != "tool_use":
                logline("end", {"iteration": iteration, "text": final_text})
                break

            # Luu assistant turn nguyen ven (ke ca thinking block) roi thuc thi tool
            messages.append({"role": "assistant", "content": _serialize_blocks(content)})
            results = []
            for blk in content:
                if getattr(blk, "type", "") != "tool_use":
                    continue
                tool_calls += 1
                args = dict(blk.input) if isinstance(blk.input, dict) else json.loads(json.dumps(blk.input))
                out = dispatcher.dispatch(blk.name, args)
                logline("tool", {"iteration": iteration, "name": blk.name, "args": args, "result_preview": out[:500]})
                results.append({"type": "tool_result", "tool_use_id": blk.id, "content": out})
            messages.append({"role": "user", "content": results})
        else:
            logline("max_iterations", {"limit": settings.max_tool_iterations})
            final_text = final_text or f"Dung vi vuot {settings.max_tool_iterations} vong tool."

        return RunResult(run_id, scenario_key, final_text, tool_calls, dispatcher.proposals_created, log_path, messages)


def _serialize_blocks(blocks: list[Any]) -> list[dict[str, Any]]:
    """Chuyen content block cua SDK (hoac SimpleNamespace) thanh dict de gui lai. Giu nguyen thinking block."""
    out = []
    for b in blocks:
        if hasattr(b, "model_dump"):
            out.append(b.model_dump(exclude_none=True))
        else:
            d = dict(vars(b))
            out.append(d)
    return out
