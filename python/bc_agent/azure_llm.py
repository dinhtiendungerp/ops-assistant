"""Chay lop agent va tro ly tren Azure OpenAI.

Chon bang bien `LLM_PROVIDER`: `azure` (mac dinh tu 12/09/2026) hoac `anthropic`.
Khong goi thang file nay tu ngoai, dung `bc_agent.llm.build_llm()`.

Vi sao khong phai chi doi ten model. Bon cho trong `assistant/` chi gui prompt roi doc chu ve,
doi cho do that su chi la doi client. Nhung vong lap agent trong `runner.py` noi bang giao thuc
tool use cua Anthropic: content block, `stop_reason == "tool_use"`, `tool_result` kem
`tool_use_id`. Azure OpenAI noi bang giao thuc khac: `choices[0].message.tool_calls`,
`finish_reason == "tool_calls"`, message rieng voi `role="tool"` va `tool_call_id`. File nay la
lop phien dich giua hai giao thuc do, de `runner.py` khong phai biet ben duoi la ai.

Ban tra ve duoc dung lai thanh SimpleNamespace giong het hinh dang cua SDK Anthropic, cung cach
`ScriptedLLM` da lam. Nho vay `AgentRunner` khong sua mot dong nao.

Duong goi: POST {endpoint}/openai/v1/chat/completions, khong phai khai api-version theo thang.
"""
from __future__ import annotations

import json
import logging
import time
import uuid
from types import SimpleNamespace
from typing import Any

import requests

from .config import Settings, settings

log = logging.getLogger(__name__)

TIMEOUT = 120


class AzureLLMError(RuntimeError):
    pass


# ---------------------------------------------------------------- doi hinh dang cong cu
def tools_to_openai(tools: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Anthropic dung `input_schema`, OpenAI boc them mot lop `function` va goi la `parameters`."""
    out = []
    for t in tools:
        out.append({
            "type": "function",
            "function": {
                "name": t["name"],
                "description": t.get("description", ""),
                "parameters": t.get("input_schema") or {"type": "object", "properties": {}},
            },
        })
    return out


# ---------------------------------------------------------------- doi hinh dang hoi thoai
def messages_to_openai(system: str, messages: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Doi lich su kieu Anthropic sang kieu OpenAI.

    Ba truong hop phai xu ly rieng:
      - noi dung la chuoi: giu nguyen.
      - assistant turn co tool_use: gom text vao `content`, gom tool_use vao `tool_calls`.
      - user turn chi gom tool_result: moi ket qua thanh mot message role="tool" rieng, vi
        OpenAI khong cho gop nhieu ket qua vao mot message nhu Anthropic.
    """
    out: list[dict[str, Any]] = [{"role": "system", "content": system}] if system else []
    for m in messages:
        role, content = m.get("role"), m.get("content")
        if isinstance(content, str):
            out.append({"role": role, "content": content})
            continue

        blocks = list(content or [])
        if role == "assistant":
            texts, calls = [], []
            for b in blocks:
                b = b if isinstance(b, dict) else _block_to_dict(b)
                if b.get("type") == "text":
                    texts.append(b.get("text", ""))
                elif b.get("type") == "tool_use":
                    calls.append({
                        "id": b.get("id") or f"call_{uuid.uuid4().hex[:8]}",
                        "type": "function",
                        "function": {"name": b.get("name"),
                                     "arguments": json.dumps(b.get("input") or {}, ensure_ascii=False)},
                    })
                # thinking block cua Anthropic khong co doi ung ben OpenAI, bo qua
            msg: dict[str, Any] = {"role": "assistant", "content": "\n".join(texts) or None}
            if calls:
                msg["tool_calls"] = calls
            out.append(msg)
            continue

        # user turn: co the la tool_result, co the la text
        results = [b if isinstance(b, dict) else _block_to_dict(b) for b in blocks]
        if results and all(r.get("type") == "tool_result" for r in results):
            for r in results:
                out.append({"role": "tool", "tool_call_id": r.get("tool_use_id"),
                            "content": _as_text(r.get("content"))})
        else:
            out.append({"role": role, "content": "\n".join(_as_text(r) for r in results)})
    return out


def _block_to_dict(b: Any) -> dict[str, Any]:
    if hasattr(b, "model_dump"):
        return b.model_dump()
    return {k: getattr(b, k) for k in ("type", "text", "id", "name", "input") if hasattr(b, k)}


def _as_text(v: Any) -> str:
    if isinstance(v, str):
        return v
    return json.dumps(v, ensure_ascii=False, default=str)


# ---------------------------------------------------------------- doi hinh dang ket qua
STOP_REASON = {
    "tool_calls": "tool_use",
    "stop": "end_turn",
    "length": "max_tokens",
    "content_filter": "refusal",
}


def response_to_anthropic(body: dict[str, Any]) -> Any:
    """Dung lai ket qua cua Azure thanh hinh dang ma AgentRunner dang doc."""
    choice = (body.get("choices") or [{}])[0]
    msg = choice.get("message") or {}
    blocks: list[Any] = []

    text = msg.get("content")
    if text:
        blocks.append(SimpleNamespace(type="text", text=text))

    for call in msg.get("tool_calls") or []:
        fn = call.get("function") or {}
        try:
            args = json.loads(fn.get("arguments") or "{}")
        except json.JSONDecodeError:
            # Model tra JSON hong. Bao ro chu khong nuot, vi nuot thi tool chay voi tham so rong.
            raise AzureLLMError(f"Tham so tool khong phai JSON hop le: {fn.get('arguments')!r}")
        blocks.append(SimpleNamespace(type="tool_use", id=call.get("id"),
                                      name=fn.get("name"), input=args))

    usage = body.get("usage") or {}
    return SimpleNamespace(
        content=blocks,
        stop_reason=STOP_REASON.get(choice.get("finish_reason"), choice.get("finish_reason")),
        # `prompt_tokens` cua OpenAI DA GOM `cached_tokens`; `input_tokens` cua Anthropic thi khong.
        # Truoc 13/09/2026 chep thang prompt_tokens sang input_tokens nen phan cache bi dem hai lan:
        # so token tren trang Cai dat va tren the tra loi thoi phong (46 nghin thay vi 28 nghin),
        # tien thoi phong hon gap doi. Bang chung: luot goi dau prompt 1.054 ma cached 1.024.
        usage=SimpleNamespace(
            input_tokens=max(0, int(usage.get("prompt_tokens") or 0)
                             - int(((usage.get("prompt_tokens_details") or {}).get("cached_tokens")) or 0)),
            output_tokens=int(usage.get("completion_tokens") or 0),
            cache_read_input_tokens=int(((usage.get("prompt_tokens_details") or {}).get("cached_tokens")) or 0),
            cache_creation_input_tokens=0,
        ),
        model=body.get("model", ""),
    )


# ---------------------------------------------------------------- backend
class AzureOpenAILLM:
    """Cung interface voi ClaudeLLM trong `bc_agent.llm`: `complete` cho vong lap tool use,
    `text` cho mot cau hoi mot cau tra loi. Ca hai tra ve hinh dang cua SDK Anthropic."""

    def __init__(self, s: Settings | None = None, max_tokens: int = 4096):
        s = s or settings
        self.endpoint = s.azure_openai_endpoint
        self.deployment = s.azure_openai_deployment
        self.api_key = s.azure_openai_api_key
        self.max_tokens = max_tokens
        thieu = [n for n, v in (("AZURE_OPENAI_ENDPOINT", self.endpoint),
                                ("AZURE_OPENAI_DEPLOYMENT", self.deployment),
                                ("AZURE_OPENAI_API_KEY", self.api_key)) if not v]
        if thieu:
            raise AzureLLMError("Thieu bien: " + ", ".join(thieu))

    @property
    def model(self) -> str:
        """Ten ghi vao so chi phi. Bang ten deployment, nen deployment phai dat trung ten model
        (`gpt-4.1-mini`) thi `budget.PRICES` moi tra dung gia."""
        return self.deployment

    @property
    def url(self) -> str:
        return f"{self.endpoint}/openai/v1/chat/completions"

    def _post(self, payload: dict[str, Any]) -> Any:
        payload = {"model": self.deployment, **payload}
        for lan in range(2):
            r = requests.post(self.url, headers={"api-key": self.api_key,
                                                 "Content-Type": "application/json"},
                              json=payload, timeout=TIMEOUT)
            # 429 la vuot han muc token moi phut cua deployment (dang dat 10.000). Vong lap planner
            # gui lai ca lich su kem ket qua tool nen de cham tran. Cho dung so giay Azure bao roi
            # thu lai mot lan; qua 20 giay thi thoi, de nguoi hoi khong ngoi cho mot phut.
            if r.status_code == 429 and lan == 0:
                try:
                    cho = float(r.headers.get("retry-after") or r.headers.get("x-ratelimit-reset-requests") or 5)
                except ValueError:
                    cho = 5.0
                if cho <= 20:
                    time.sleep(cho)
                    continue
            break
        if r.status_code >= 400:
            raise AzureLLMError(f"HTTP {r.status_code} tu Azure OpenAI: {r.text[:400]}")
        return response_to_anthropic(r.json())

    def complete(self, system: str, messages: list[dict[str, Any]], tools: list[dict[str, Any]]) -> Any:
        payload: dict[str, Any] = {
            "messages": messages_to_openai(system, messages),
            "max_completion_tokens": self.max_tokens,
        }
        if tools:
            payload["tools"] = tools_to_openai(tools)
        return self._post(payload)

    def text(self, system: str, user: str, max_tokens: int = 512,
             schema: dict[str, Any] | None = None, thinking: bool = False) -> Any:
        """Mot cau hoi, mot cau tra loi. `schema` bat structured output, model bi ep tra JSON
        dung schema (strict). `thinking` khong co doi ung tren gpt-4.1-mini, bo qua."""
        payload: dict[str, Any] = {
            "messages": messages_to_openai(system, [{"role": "user", "content": user}]),
            "max_completion_tokens": max_tokens,
        }
        if schema is not None:
            payload["response_format"] = {"type": "json_schema", "json_schema": {
                "name": "out", "schema": schema, "strict": True}}
        return self._post(payload)
