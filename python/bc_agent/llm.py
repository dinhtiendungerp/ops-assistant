"""Mot cho duy nhat quyet dinh model nao dang chay.

    from bc_agent.llm import build_llm
    llm = build_llm()            # model chinh: vong lap agent, planner, viet lai cau
    llm = build_llm(fast=True)   # model nhanh: phan loai tin, doc cau giai thich

Ca hai backend cung hai ham:
    llm.complete(system, messages, tools)   vong lap tool use, tra ve hinh dang SDK Anthropic
    llm.text(system, user, max_tokens, schema, thinking)   mot hoi mot dap, co the ep JSON theo schema
    llm.model                               ten ghi vao so chi phi (`assistant/budget.py`)

Chon backend bang `LLM_PROVIDER` trong `.env`: `azure` (mac dinh) hoac `anthropic`.
Chi goi khi `LLM_MODE=live`; che do scripted khong di qua day.
"""
from __future__ import annotations

from typing import Any, Protocol

from .config import settings


class LLM(Protocol):
    model: str

    def complete(self, system: str, messages: list[dict[str, Any]], tools: list[dict[str, Any]]) -> Any: ...

    def text(self, system: str, user: str, max_tokens: int = 512,
             schema: dict[str, Any] | None = None, thinking: bool = False) -> Any: ...


class ClaudeLLM:
    """Backend Claude qua SDK anthropic. Giu lai de doi chieu, khong con la mac dinh."""

    def __init__(self, model: str, max_tokens: int = 16000):
        settings.validate_live_llm()
        import anthropic  # import muon de mock mode khong can SDK

        self.client = anthropic.Anthropic(api_key=settings.anthropic_api_key)
        self.model = model
        self.max_tokens = max_tokens

    def complete(self, system: str, messages: list[dict[str, Any]], tools: list[dict[str, Any]]) -> Any:
        return self.client.messages.create(
            model=self.model,
            max_tokens=self.max_tokens,
            thinking={"type": "adaptive"},
            system=system,
            tools=tools,
            messages=messages,
        )

    def text(self, system: str, user: str, max_tokens: int = 512,
             schema: dict[str, Any] | None = None, thinking: bool = False) -> Any:
        kw: dict[str, Any] = {}
        if schema is not None:
            kw["output_config"] = {"format": {"type": "json_schema", "schema": schema}}
        if thinking:
            kw["thinking"] = {"type": "adaptive"}
        return self.client.messages.create(
            model=self.model, max_tokens=max_tokens, system=system,
            messages=[{"role": "user", "content": user}], **kw)


def build_llm(fast: bool = False) -> LLM:
    settings.validate_live_llm()
    if settings.llm_provider == "azure":
        from .azure_llm import AzureOpenAILLM
        return AzureOpenAILLM()
    return ClaudeLLM(settings.agent_model_fast if fast else settings.agent_model)


def text_of(resp: Any) -> str:
    """Gop cac block text trong ket qua, dung chung cho ca hai backend."""
    return "".join(getattr(b, "text", "") for b in resp.content if getattr(b, "type", "") == "text").strip()
