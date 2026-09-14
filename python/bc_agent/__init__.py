"""NaviWorld - Marou AI agent POC.

Cau truc:
  config.py        doc .env
  bc_client.py     BCClient: OAuth S2S + custom API naviworld/marouagent/v1.0
  mock_client.py   MockBCClient: cung interface, du lieu tu fixtures/
  tools.py         dinh nghia tool cho model + dispatcher goi client
  llm.py           mot cho chon backend: Azure OpenAI (mac dinh) hoac Claude
  runner.py        vong lap agent (build_llm() hoac ScriptedLLM), log moi tool call
  scenarios/       system prompt + task cho tung agent
  forecast.py      mo hinh du bao baseline, TACH KHOI agent
"""
__version__ = "0.1.0"
