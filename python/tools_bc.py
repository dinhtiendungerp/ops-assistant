"""Tro giup quan tri BC qua S2S cho phien lam viec: doc API, publish extension, goi action.

Khong in token hay secret. Chay: python tools_bc.py [--company NWV-DAKAO] <lenh> ...
  get <duong dan tuong doi sau /v2.0/<tenant>/<env>/>
  companies
  extensions
  upload <duong dan .app>
  deploy-status
  ws <Ham> '<json>' [service]
Khong co --company thi dung BC_COMPANY_NAME trong .env. App cai theo environment, nen upload o company nao cung duoc;
web service va du lieu thi theo company.
"""
from __future__ import annotations

import json
import sys
import time
from dataclasses import replace

import requests

from bc_agent.auth import TokenProvider
from bc_agent.config import Settings

S = Settings()
if "--company" in sys.argv:
    _i = sys.argv.index("--company")
    S = replace(S, bc_company_name=sys.argv[_i + 1], bc_company_id="")
    del sys.argv[_i:_i + 2]
TP = TokenProvider(S)
BASE = f"https://api.businesscentral.dynamics.com/v2.0/{S.bc_tenant_id}/{S.bc_environment}"


def req(method: str, path: str, **kw):
    url = path if path.startswith("http") else f"{BASE}/{path.lstrip('/')}"
    h = TP.headers(kw.pop("headers", None))
    r = requests.request(method, url, headers=h, timeout=kw.pop("timeout", 300), **kw)
    return r


def company_id(name: str | None = None) -> str:
    name = name or S.bc_company_name
    r = req("GET", "api/v2.0/companies")
    r.raise_for_status()
    for c in r.json()["value"]:
        if c["name"] == name:
            return c["id"]
    raise SystemExit(f"khong thay company {name}")


def ws(fn: str, body: dict, service: str = "NWVReplenService"):
    """Goi unbound action ODataV4 cua codeunit web service; tra ve JSON da giai (ham tra Text JSON)."""
    r = req("POST", f"ODataV4/{service}_{fn}?company={S.bc_company_name}", json=body, timeout=1800)
    if not r.ok:
        raise SystemExit(f"{fn} HTTP {r.status_code}: {r.text[:1500]}")
    val = r.json().get("value")
    try:
        return json.loads(val)
    except Exception:
        return val


def show(r):
    print(r.status_code)
    try:
        print(json.dumps(r.json(), ensure_ascii=False, indent=1)[:20000])
    except Exception:
        print(r.text[:5000])


def main(argv):
    cmd = argv[0]
    if cmd == "get":
        show(req("GET", argv[1]))
    elif cmd == "companies":
        show(req("GET", "api/v2.0/companies"))
    elif cmd == "extensions":
        cid = company_id()
        r = req("GET", f"api/microsoft/automation/v2.0/companies({cid})/extensions")
        for e in r.json().get("value", []):
            if "NWV" in e["displayName"] or "LS Central" == e["displayName"]:
                print(e["displayName"], e["versionMajor"], e["versionMinor"], e["versionBuild"],
                      e["versionRevision"], "installed" if e["isInstalled"] else "-", e["publishedAs"], e["packageId"])
    elif cmd == "ws":
        # ws <Ham> '<json tham so>'  goi NWVReplenService
        print(json.dumps(ws(argv[1], json.loads(argv[2]) if len(argv) > 2 else {},
                            *(argv[3:4] or [])), ensure_ascii=False, indent=1)[:30000])
    elif cmd == "deploy-status":
        cid = company_id()
        show(req("GET", f"api/microsoft/automation/v2.0/companies({cid})/extensionDeploymentStatus"))
    elif cmd == "upload":
        cid = company_id()
        base = f"api/microsoft/automation/v2.0/companies({cid})/extensionUpload"
        r = req("GET", base)
        vals = r.json().get("value", []) if r.ok else []
        if vals:
            up = vals[0]
        else:
            r = req("POST", base, json={"schedule": "Current version", "schemaSyncMode": "Add"})
            if not r.ok:
                show(r)
                return
            up = r.json()
        sid = up["systemId"]
        # upload <app> force : xoa table/field trong ban moi thi BC doi Force Sync, du lieu cua cac object do mat.
        mode = "Force Sync" if len(argv) > 2 and argv[2] == "force" else "Add"
        if up.get("schemaSyncMode") != mode:
            r = req("PATCH", f"{base}({sid})", json={"schemaSyncMode": mode}, headers={"If-Match": "*"})
            print("schemaSyncMode", mode, r.status_code, r.text[:300])
        with open(argv[1], "rb") as f:
            data = f.read()
        r = req("PATCH", f"{base}({sid})/extensionContent", data=data,
                headers={"Content-Type": "application/octet-stream", "If-Match": "*"})
        print("content", r.status_code, r.text[:500])
        r = req("POST", f"{base}({sid})/Microsoft.NAV.upload")
        print("upload", r.status_code, r.text[:500])
        for _ in range(40):
            time.sleep(6)
            r = req("GET", f"api/microsoft/automation/v2.0/companies({cid})/extensionDeploymentStatus")
            rows = r.json().get("value", [])
            if rows:
                top = rows[0]
                print(top.get("name"), top.get("appVersion"), top.get("status"), top.get("startedOn"))
                if top.get("status") not in ("InProgress", "Unknown"):
                    break
    else:
        raise SystemExit(__doc__)


if __name__ == "__main__":
    main(sys.argv[1:])
