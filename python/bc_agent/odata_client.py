"""ODataWSClient: duong du phong doc web service OData V4 khai tay tren trang Web Services.

Chi dung khi extension NWV Marou Data API chua publish. Khi extension da co thi dung
duong custom API page trong bc_data.py, ten truong co dinh do AL quy dinh nen khong phai do.

URL cho BC SaaS, theo Microsoft Learn (Publish a web service):
    https://api.businesscentral.dynamics.com/v2.0/<tenant>/<environment>/ODataV4/Company('<Ten>')/<service>
    https://api.businesscentral.dynamics.com/v2.0/<tenant>/<environment>/ODataV4/$metadata

Ten company phan biet hoa thuong. Tai lieu khuyen dung dang Company(Id=<guid>) vi guid khong
doi con ten thi admin sua duoc, nen o day co company id thi uu tien dung guid.

Vi sao phai doc $metadata: BC dat ten truong cua web service theo caption cua field, nen ten
thay doi theo ban dich va theo tung page. Khong duoc doan ten truong, phai do tu $metadata roi
khop lai bang bang alias trong bc_data.py.
"""
from __future__ import annotations

import logging
import re
import xml.etree.ElementTree as ET
from typing import Any
from urllib.parse import quote

import requests

from .auth import TokenProvider
from .config import Settings

log = logging.getLogger(__name__)

API_ROOT = "https://api.businesscentral.dynamics.com/v2.0"


class ODataError(RuntimeError):
    pass


class ODataWSClient:
    def __init__(self, s: Settings, timeout: int = 120):
        s.validate_live_bc()
        self.s = s
        self.timeout = timeout
        self.auth = TokenProvider(s)
        self.root = f"{API_ROOT}/{s.bc_tenant_id}/{s.bc_environment}/ODataV4"
        self.base = f"{self.root}/{self._company_segment()}"
        self._fields: dict[str, list[str]] | None = None

    def _company_segment(self) -> str:
        if self.s.bc_company_id:
            return f"Company(Id={self.s.bc_company_id})"
        return "Company(" + quote(f"'{self.s.bc_company_name}'", safe="") + ")"

    # ---------------------------------------------------------------- $metadata
    def entity_fields(self) -> dict[str, list[str]]:
        """Tra ve {ten EntityType: [ten truong]} doc tu $metadata. Doc mot lan roi giu lai."""
        if self._fields is not None:
            return self._fields
        r = requests.get(f"{self.root}/$metadata", headers=self.auth.headers(),
                         timeout=self.timeout)
        if r.status_code >= 400:
            raise ODataError(f"HTTP {r.status_code} khi doc $metadata: {r.text[:400]}")
        self._fields = parse_metadata(r.text)
        if not self._fields:
            raise ODataError(
                "$metadata khong co EntityType nao. Kiem lai da Published web service chua."
            )
        return self._fields

    # ---------------------------------------------------------------- doc du lieu
    def list(self, service: str, filter: str | None = None, orderby: str | None = None,
             top: int | None = None) -> list[dict[str, Any]]:
        params: dict[str, Any] = {}
        if filter:
            params["$filter"] = filter
        if orderby:
            params["$orderby"] = orderby
        if top:
            params["$top"] = top
        url = f"{self.base}/{service}"
        out: list[dict[str, Any]] = []
        while url:
            r = requests.get(url, headers=self.auth.headers(), params=params, timeout=self.timeout)
            if r.status_code >= 400:
                raise ODataError(f"HTTP {r.status_code} GET {r.url}: {r.text[:400]}")
            body = r.json()
            out.extend(body.get("value", []))
            url = body.get("@odata.nextLink")
            params = {}
            if top and len(out) >= top:
                break
        return out[:top] if top else out


def parse_metadata(xml_text: str) -> dict[str, list[str]]:
    """Doc EDMX, tra ve ten truong cua tung EntityType.

    Tach rieng khoi ODataWSClient de test duoc ma khong can mang.
    """
    try:
        root = ET.fromstring(xml_text)
    except ET.ParseError as exc:
        raise ODataError(f"$metadata khong phai XML hop le: {exc}") from exc

    def local(tag: str) -> str:
        return re.sub(r"^\{.*\}", "", tag)

    out: dict[str, list[str]] = {}
    for node in root.iter():
        if local(node.tag) != "EntityType":
            continue
        name = node.get("Name")
        if not name:
            continue
        out[name] = [
            p.get("Name")
            for p in node
            if local(p.tag) == "Property" and p.get("Name")
        ]
    return out
