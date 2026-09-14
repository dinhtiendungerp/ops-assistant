"""Marou Ops Assistant - prototype (ban 0.2).

Mot tro ly nhieu skill, hai chieu, chay tren mock BC (hoac BC that qua bc_agent.bc_client).
  gateway.py   BCGateway: ham nghiep vu tren client BC (mock/live), giu Transfer Order gia lap khi mock
  memory.py    SQLite: users, conversations, proposals mirror, follow-ups, dong ho ao cho demo
  nlu.py       hieu tin nhan: rule + fuzzy (scripted) hoac model qua bc_agent.llm (live)
  cards.py     the de xuat: Adaptive Card JSON (Teams) va HTML (web demo)
  core.py      Assistant: handle_message, handle_action, morning_brief, run_followups
  skills/      replenishment, inventory_health, discount
  channels/    web (FastAPI + chat UI mo phong Teams), teams (khung Bot Framework)
"""
