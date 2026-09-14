"""Lien ket mo trang Business Central da loc san, gan vao the tro ly.

Vi sao co file nay (14/09/2026). RFP UC10 doi "dashboard links": moi con so tro ly noi phai mo duoc cho goc trong BC.
Dang URL lay tu Microsoft Learn, bai "Web client URL" (tra ngay 14/09/2026):
    https://businesscentral.dynamics.com/<tenant>/<environment>/?company=<ten>&page=<id>&filter='<field>' IS '<value>' AND ...
Ten field trong filter la ten field cua BANG nguon cua page, gia tri boc trong dau nhay don.
"""
from __future__ import annotations

from urllib.parse import quote

from bc_agent.config import Settings

# Page ID dung trong the. Base App doc tu source 28.4, LS doc tu source LS Central 28.0.10.3586, NWV la app cua ta.
PAGE = {
    "item_ledger_entries": 38,
    "purchase_order": 50,
    "purchase_lines": 518,
    "lot_info_list": 6508,
    "agent_proposals": 70101,
    "inventory_health": 70102,
    "forecast_accuracy": 70120,
    "forecast_daily": 70121,
    "supplier_scorecard": 70124,
    "ls_transfer_journal": 10012215,
    "ls_transfer_journal_details": 10012216,
    "ls_calc_log": 10012270,
    "ls_item_quantities": 10012218,
    "ls_forecast_entries": 10012431,     # LSC Forecast Entries (Retail Forecast Entries), doc trong source LS 28.0
    "ls_periodic_discounts": 99001601,   # LSC Periodic Discount List
    "ls_planned_events": 10012326,       # LSC Replen. Planned Events
}


def link(page: str | int, filters: dict[str, str] | None = None, settings: Settings | None = None) -> str:
    """URL toi trang BC. Tra '' neu chua cau hinh tenant/environment (vi du chay test khong co .env)."""
    s = settings or Settings()
    if not (s.bc_tenant_id and s.bc_environment):
        return ""
    page_id = PAGE.get(page, page) if isinstance(page, str) else page
    url = (f"https://businesscentral.dynamics.com/{s.bc_tenant_id}/{quote(s.bc_environment)}/"
           f"?company={quote(s.bc_company_name or '')}&page={page_id}")
    parts = [f"'{k}' IS '{v}'" for k, v in (filters or {}).items() if v not in (None, "")]
    if parts:
        url += "&filter=" + quote(" AND ".join(parts), safe="'")
    return url
