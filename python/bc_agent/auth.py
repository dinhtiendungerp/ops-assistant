"""TokenProvider: mot cho duy nhat lay access token S2S cho BC SaaS.

Tham chieu Microsoft Learn, Using service-to-service (S2S) authentication:
  authority = https://login.microsoftonline.com/<tenantId>
  scope     = https://api.businesscentral.dynamics.com/.default
  Entra app phai duoc cap quyen ung dung Dynamics 365 Business Central > API.ReadWrite.All
  va phai duoc dang ky trong BC tren trang Microsoft Entra Applications kem permission set.

Token duoc giu lai trong bo nho va chi lay moi khi con duoi 60 giay la het han. MSAL cung
co cache rieng cua no, o day giu them mot lop de khong phai goi acquire_token_for_client
cho tung request.
"""
from __future__ import annotations

import logging
import time

import msal

from .config import Settings

log = logging.getLogger(__name__)

SCOPE = ["https://api.businesscentral.dynamics.com/.default"]


class AuthError(RuntimeError):
    pass


class TokenProvider:
    def __init__(self, s: Settings):
        s.validate_live_bc()
        self.s = s
        self._app = msal.ConfidentialClientApplication(
            client_id=s.bc_client_id,
            client_credential=s.bc_client_secret,
            authority=f"https://login.microsoftonline.com/{s.bc_tenant_id}",
        )
        self._token: str | None = None
        self._expires_at: float = 0.0

    def token(self) -> str:
        if self._token and time.time() < self._expires_at - 60:
            return self._token
        result = self._app.acquire_token_for_client(scopes=SCOPE)
        if "access_token" not in result:
            raise AuthError(
                f"Khong lay duoc token S2S: {result.get('error')}: {result.get('error_description')}"
            )
        self._token = result["access_token"]
        self._expires_at = time.time() + int(result.get("expires_in", 3600))
        log.debug("Lay token S2S moi, het han sau %ss", result.get("expires_in"))
        return self._token

    def headers(self, extra: dict[str, str] | None = None) -> dict[str, str]:
        h = {
            "Authorization": f"Bearer {self.token()}",
            "Accept": "application/json",
            "Content-Type": "application/json",
        }
        if extra:
            h.update(extra)
        return h
