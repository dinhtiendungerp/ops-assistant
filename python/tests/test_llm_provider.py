"""Mot cho quyet dinh model: bc_agent.llm.build_llm() va ham text() cua backend Azure.

Khong goi mang. requests.post duoc thay bang ham gia ghi lai payload.
"""
from __future__ import annotations

import json
from dataclasses import replace
from types import SimpleNamespace

import pytest

from bc_agent import azure_llm, config
from bc_agent.llm import build_llm, text_of


def _azure_settings(**over):
    base = dict(llm_mode="live", llm_provider="azure",
                azure_openai_endpoint="https://marou.openai.azure.com",
                azure_openai_deployment="gpt-4.1-mini", azure_openai_api_key="k")
    base.update(over)
    return replace(config.settings, **base)


@pytest.fixture
def azure(monkeypatch):
    s = _azure_settings()
    monkeypatch.setattr(config, "settings", s)
    monkeypatch.setattr("bc_agent.llm.settings", s)
    monkeypatch.setattr(azure_llm, "settings", s)
    sent: list[dict] = []

    def fake_post(url, headers, json, timeout):
        sent.append({"url": url, "headers": headers, "payload": json})
        return SimpleNamespace(status_code=200, text="", json=lambda: {
            "choices": [{"finish_reason": "stop",
                         "message": {"content": '{"intent":"STOCKOUT","item_text":"mini bar","quantity":0,"store_hint":""}'}}],
            "usage": {"prompt_tokens": 50, "completion_tokens": 20},
            "model": "gpt-4.1-mini-2025-04-14"})

    monkeypatch.setattr(azure_llm.requests, "post", fake_post)
    return sent


def test_mac_dinh_la_azure():
    """Tu 12/09/2026 khong dat LLM_PROVIDER thi chay Azure OpenAI."""
    assert config.Settings().llm_provider == "azure"


def test_build_llm_ra_backend_azure_va_model_la_ten_deployment(azure):
    llm = build_llm()
    assert type(llm).__name__ == "AzureOpenAILLM"
    assert llm.model == "gpt-4.1-mini"
    # fast=True tren Azure van la deployment do, vi chi co mot deployment
    assert build_llm(fast=True).model == "gpt-4.1-mini"


def test_text_gui_dung_duong_va_dung_key(azure):
    llm = build_llm()
    llm.text("he thong", "nguoi dung hoi", max_tokens=99)
    s = azure[0]
    assert s["url"] == "https://marou.openai.azure.com/openai/v1/chat/completions"
    assert s["headers"]["api-key"] == "k"
    p = s["payload"]
    assert p["model"] == "gpt-4.1-mini"
    assert p["max_completion_tokens"] == 99
    assert p["messages"] == [{"role": "system", "content": "he thong"},
                             {"role": "user", "content": "nguoi dung hoi"}]
    assert "response_format" not in p and "tools" not in p


def test_text_co_schema_thi_ep_json_strict(azure):
    schema = {"type": "object", "properties": {"intent": {"type": "string"}},
              "required": ["intent"], "additionalProperties": False}
    resp = build_llm().text("s", "u", schema=schema)
    rf = azure[0]["payload"]["response_format"]
    assert rf["type"] == "json_schema"
    assert rf["json_schema"]["schema"] is schema
    assert rf["json_schema"]["strict"] is True
    # Ket qua doc duoc bang cung mot ham voi Claude
    assert json.loads(text_of(resp))["intent"] == "STOCKOUT"
    assert resp.stop_reason == "end_turn"
    assert (resp.usage.input_tokens, resp.usage.output_tokens) == (50, 20)


def test_thieu_bien_azure_thi_bao_ten_bien(monkeypatch):
    s = _azure_settings(azure_openai_api_key="")
    monkeypatch.setattr("bc_agent.llm.settings", s)
    with pytest.raises(SystemExit, match="AZURE_OPENAI_API_KEY"):
        build_llm()


def test_provider_la_gi_khac_thi_tu_choi(monkeypatch):
    s = _azure_settings(llm_provider="openai")
    monkeypatch.setattr("bc_agent.llm.settings", s)
    with pytest.raises(SystemExit, match="LLM_PROVIDER"):
        build_llm()


def test_provider_anthropic_thi_fast_la_haiku(monkeypatch):
    """Duong Claude van con de doi chieu. Khong can SDK that: thay module anthropic bang stub."""
    import sys
    calls = []

    class _Client:
        def __init__(self, api_key):
            calls.append(api_key)
            self.messages = SimpleNamespace(create=lambda **kw: SimpleNamespace(content=[], usage=None, stop_reason="end_turn", kw=kw))

    monkeypatch.setitem(sys.modules, "anthropic", SimpleNamespace(Anthropic=_Client))
    s = replace(config.settings, llm_mode="live", llm_provider="anthropic", anthropic_api_key="sk",
                agent_model="claude-opus-5", agent_model_fast="claude-haiku-4-5")
    monkeypatch.setattr("bc_agent.llm.settings", s)
    assert build_llm().model == "claude-opus-5"
    fast = build_llm(fast=True)
    assert fast.model == "claude-haiku-4-5"
    r = fast.text("s", "u", schema={"type": "object"}, thinking=True)
    assert r.kw["output_config"]["format"]["schema"] == {"type": "object"}
    assert r.kw["thinking"] == {"type": "adaptive"}


def test_text_of_gop_block_text_bo_block_khac():
    r = SimpleNamespace(content=[SimpleNamespace(type="thinking", thinking="x"),
                                 SimpleNamespace(type="text", text=" a "),
                                 SimpleNamespace(type="text", text="b")])
    assert text_of(r) == "a b"
