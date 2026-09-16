"""BCClient: goi custom API cua NWV Marou Agent Foundation tren BC SaaS bang S2S OAuth.

Tham chieu Microsoft Learn:
  - Using service-to-service (S2S) authentication:
    scope  = https://api.businesscentral.dynamics.com/.default
    token  = https://login.microsoftonline.com/<tenantId>/oauth2/v2.0/token
    permission app: Dynamics 365 Business Central > Application > API.ReadWrite.All
  - Base URL API: https://api.businesscentral.dynamics.com/v2.0/<environment>/api/<publisher>/<group>/<version>/companies(<companyId>)/<entitySet>

Cac endpoint dung o day (tu AL pages 70110..70114):
  inventoryHealthLines, replenishmentSuggestions, discountExceptions, agentProposals, posDiscountLogs
"""
from __future__ import annotations

import logging
import time
from typing import Any

import msal
import json
import requests

from .config import Settings
from .odata import Condition, to_odata_filter

log = logging.getLogger(__name__)

API_ROOT = "https://api.businesscentral.dynamics.com/v2.0"
SCOPE = ["https://api.businesscentral.dynamics.com/.default"]
PUBLISHER, GROUP, VERSION = "naviworld", "marouagent", "v1.0"


class BCError(RuntimeError):
    pass


class BCClient:
    """Interface dung chung voi MockBCClient: list / get / create / patch / bound_action."""

    def __init__(self, s: Settings):
        s.validate_live_bc()
        self.s = s
        self._app = msal.ConfidentialClientApplication(
            client_id=s.bc_client_id,
            client_credential=s.bc_client_secret,
            authority=f"https://login.microsoftonline.com/{s.bc_tenant_id}",
        )
        self._token: str | None = None
        self._token_exp: float = 0
        self._company_id = s.bc_company_id or self._resolve_company_id(s.bc_company_name)
        self.base = f"{API_ROOT}/{s.bc_environment}/api/{PUBLISHER}/{GROUP}/{VERSION}/companies({self._company_id})"

    # ---------- auth ----------
    def _access_token(self) -> str:
        if self._token and time.time() < self._token_exp - 60:
            return self._token
        result = self._app.acquire_token_for_client(scopes=SCOPE)
        if "access_token" not in result:
            raise BCError(f"Khong lay duoc token: {result.get('error')}: {result.get('error_description')}")
        self._token = result["access_token"]
        self._token_exp = time.time() + int(result.get("expires_in", 3600))
        return self._token

    def _headers(self, extra: dict[str, str] | None = None) -> dict[str, str]:
        h = {
            "Authorization": f"Bearer {self._access_token()}",
            "Accept": "application/json",
            "Content-Type": "application/json",
        }
        if extra:
            h.update(extra)
        return h

    def _resolve_company_id(self, name: str) -> str:
        url = f"{API_ROOT}/{self.s.bc_environment}/api/v2.0/companies"
        r = requests.get(url, headers=self._headers(), params={"$filter": f"name eq '{name}'"}, timeout=60)
        self._raise(r)
        items = r.json().get("value", [])
        if not items:
            raise BCError(f"Khong tim thay company '{name}' trong environment {self.s.bc_environment}")
        return items[0]["id"]

    # ---------- http ----------
    @staticmethod
    def _raise(r: requests.Response) -> None:
        if r.status_code >= 400:
            try:
                msg = r.json().get("error", {}).get("message", r.text)
            except ValueError:
                msg = r.text
            raise BCError(f"HTTP {r.status_code} {r.request.method} {r.url}: {msg}")

    def list(self, entity_set: str, filter: str | None = None, orderby: str | None = None,
             top: int | None = None, select: str | None = None) -> list[dict[str, Any]]:
        params: dict[str, Any] = {}
        if filter:
            params["$filter"] = filter
        if orderby:
            params["$orderby"] = orderby
        if top:
            params["$top"] = top
        if select:
            params["$select"] = select
        url = f"{self.base}/{entity_set}"
        out: list[dict[str, Any]] = []
        while url:
            r = requests.get(url, headers=self._headers(), params=params, timeout=120)
            self._raise(r)
            body = r.json()
            out.extend(body.get("value", []))
            url = body.get("@odata.nextLink")
            params = {}
            if top and len(out) >= top:
                break
        return out[:top] if top else out

    def query(self, entity_set: str, conds: list[Condition] | None = None,
              orderby: str | None = None, top: int | None = None,
              select: str | None = None) -> list[dict[str, Any]]:
        return self.list(entity_set, filter=to_odata_filter(conds or []), orderby=orderby,
                         top=top, select=select)

    def get(self, entity_set: str, record_id: str) -> dict[str, Any]:
        r = requests.get(f"{self.base}/{entity_set}({record_id})", headers=self._headers(), timeout=60)
        self._raise(r)
        return r.json()

    def create(self, entity_set: str, body: dict[str, Any]) -> dict[str, Any]:
        r = requests.post(f"{self.base}/{entity_set}", headers=self._headers(), json=body, timeout=60)
        self._raise(r)
        return r.json()

    def patch(self, entity_set: str, record_id: str, body: dict[str, Any], etag: str = "*") -> dict[str, Any]:
        r = requests.patch(
            f"{self.base}/{entity_set}({record_id})",
            headers=self._headers({"If-Match": etag}),
            json=body,
            timeout=60,
        )
        self._raise(r)
        return r.json()

    def web_service(self, service: str, fn: str, body: dict[str, Any] | None = None, timeout: int = 300,
                    company: str = "") -> Any:
        """Goi unbound action ODataV4 cua mot codeunit web service: POST .../ODataV4/<service>_<fn>?company=<ten>.

        Dung cho viec chi lam duoc bang AL, vi du gui Purchase Order sang company doi tac (Intercompany, 16/09/2026).
        Ham AL tra Text JSON nen thu giai; khong phai JSON thi tra nguyen chuoi."""
        from urllib.parse import quote
        root = f"{API_ROOT}/{self.s.bc_environment}/ODataV4"
        # company: goi sang company khac, dung khi tro ly o Dakao can bam mot nut demo ben Marou (16/09/2026).
        r = requests.post(f"{root}/{service}_{fn}?company={quote(company or self.s.bc_company_name)}",
                          headers=self._headers(), json=body or {}, timeout=timeout)
        self._raise(r)
        val = r.json().get("value")
        try:
            return json.loads(val) if isinstance(val, str) else val
        except ValueError:
            return val

    def bound_action(self, entity_set: str, record_id: str, action: str, body: dict[str, Any] | None = None) -> None:
        """Goi [ServiceEnabled] procedure tren API page: POST .../entitySet(id)/Microsoft.NAV.<action>"""
        r = requests.post(
            f"{self.base}/{entity_set}({record_id})/Microsoft.NAV.{action}",
            headers=self._headers(),
            json=body or {},
            timeout=60,
        )
        self._raise(r)
