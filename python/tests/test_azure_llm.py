"""Lop phien dich giua giao thuc tool use cua Anthropic va cua Azure OpenAI.

Day la phan khong phai "chi cam model nao". Bon cho trong assistant/ chi gui prompt roi doc chu
ve nen doi client la xong. Vong lap agent thi khac: hai ben dung hai giao thuc tool use khac nhau,
va neu dich sai thi agent chay nhung goi nham tool, hoac mat ket qua tool, rat kho phat hien.
"""
from __future__ import annotations

import json

import pytest

from bc_agent.azure_llm import (AzureLLMError, messages_to_openai, response_to_anthropic,
                                tools_to_openai)

TOOLS = [{"name": "read_health", "description": "Doc phan tang ton kho",
          "input_schema": {"type": "object", "properties": {"tier": {"type": "string"}},
                           "required": ["tier"]}}]


def test_cong_cu_doi_sang_dang_function_cua_openai():
    out = tools_to_openai(TOOLS)
    assert out == [{"type": "function", "function": {
        "name": "read_health", "description": "Doc phan tang ton kho",
        "parameters": TOOLS[0]["input_schema"]}}]


def test_cong_cu_khong_co_schema_van_ra_object_rong():
    """Thieu input_schema ma de None thi Azure tra 400. Phai co object rong."""
    out = tools_to_openai([{"name": "ping"}])
    assert out[0]["function"]["parameters"] == {"type": "object", "properties": {}}


def test_luot_assistant_co_tool_use_gom_thanh_tool_calls():
    msgs = [
        {"role": "user", "content": "phan tang giup"},
        {"role": "assistant", "content": [
            {"type": "text", "text": "de em xem"},
            {"type": "tool_use", "id": "tu_1", "name": "read_health", "input": {"tier": "Expired"}},
        ]},
        {"role": "user", "content": [
            {"type": "tool_result", "tool_use_id": "tu_1", "content": "31 lo qua han"}]},
    ]
    out = messages_to_openai("ban la tro ly", msgs)
    assert out[0] == {"role": "system", "content": "ban la tro ly"}
    assert out[1] == {"role": "user", "content": "phan tang giup"}
    assert out[2]["role"] == "assistant" and out[2]["content"] == "de em xem"
    call = out[2]["tool_calls"][0]
    assert call["id"] == "tu_1" and call["function"]["name"] == "read_health"
    assert json.loads(call["function"]["arguments"]) == {"tier": "Expired"}
    # Ket qua tool phai thanh message rieng role="tool", khong gop nhu Anthropic
    assert out[3] == {"role": "tool", "tool_call_id": "tu_1", "content": "31 lo qua han"}


def test_nhieu_ket_qua_tool_tach_thanh_nhieu_message():
    """Anthropic cho gop nhieu tool_result vao mot user message, OpenAI thi khong."""
    msgs = [{"role": "user", "content": [
        {"type": "tool_result", "tool_use_id": "a", "content": "1"},
        {"type": "tool_result", "tool_use_id": "b", "content": "2"},
    ]}]
    out = messages_to_openai("", msgs)
    assert [m["tool_call_id"] for m in out] == ["a", "b"]
    assert all(m["role"] == "tool" for m in out)


def test_thinking_block_bi_bo_qua_chu_khong_lam_vo():
    msgs = [{"role": "assistant", "content": [
        {"type": "thinking", "thinking": "..."},
        {"type": "text", "text": "xong"}]}]
    out = messages_to_openai("", msgs)
    assert out == [{"role": "assistant", "content": "xong"}]


def _azure_body(finish, content=None, calls=None, usage=None):
    msg = {"content": content}
    if calls:
        msg["tool_calls"] = calls
    return {"choices": [{"finish_reason": finish, "message": msg}],
            "usage": usage or {"prompt_tokens": 10, "completion_tokens": 5},
            "model": "gpt-4.1-mini-2025-04-14"}


def test_ket_qua_co_tool_call_doi_thanh_stop_reason_tool_use():
    body = _azure_body("tool_calls", content="dang tra", calls=[
        {"id": "call_1", "type": "function",
         "function": {"name": "read_health", "arguments": '{"tier":"NearExpiry"}'}}])
    r = response_to_anthropic(body)
    assert r.stop_reason == "tool_use"
    assert [b.type for b in r.content] == ["text", "tool_use"]
    tu = r.content[1]
    assert (tu.id, tu.name, tu.input) == ("call_1", "read_health", {"tier": "NearExpiry"})
    assert (r.usage.input_tokens, r.usage.output_tokens) == (10, 5)


@pytest.mark.parametrize("finish,mong_doi", [
    ("stop", "end_turn"), ("length", "max_tokens"), ("content_filter", "refusal"),
])
def test_doi_ten_ly_do_dung(finish, mong_doi):
    assert response_to_anthropic(_azure_body(finish, content="x")).stop_reason == mong_doi


def test_tham_so_tool_khong_phai_json_thi_bao_loi_chu_khong_nuot():
    """Nuot loi nay thi tool chay voi tham so rong va khong ai biet."""
    body = _azure_body("tool_calls", calls=[
        {"id": "c", "type": "function", "function": {"name": "f", "arguments": "{hong"}}])
    with pytest.raises(AzureLLMError, match="JSON"):
        response_to_anthropic(body)


def test_dem_token_cache_doc_tu_prompt_tokens_details():
    body = _azure_body("stop", content="x", usage={
        "prompt_tokens": 100, "completion_tokens": 20, "prompt_tokens_details": {"cached_tokens": 40}})
    u = response_to_anthropic(body).usage
    # prompt_tokens cua OpenAI da gom phan cache, nen input_tokens (khong cache) la 100 - 40.
    # Doi thanh dang Anthropic de budget khong dem phan cache hai lan.
    assert (u.input_tokens, u.output_tokens, u.cache_read_input_tokens) == (60, 20, 40)
