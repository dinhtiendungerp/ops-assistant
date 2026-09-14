"""Kiem mot resource Azure OpenAI da san sang chua: goi that mot lan roi in ra ket qua.

Chay:
    python tools/check_azure_openai.py

Doc ba bien, uu tien bien moi truong, khong co thi lay trong python/.env:
    AZURE_OPENAI_ENDPOINT     vi du https://marou.openai.azure.com
    AZURE_OPENAI_DEPLOYMENT   ten deployment tu dat luc deploy model, KHONG phai ten model
    AZURE_OPENAI_API_KEY      Keys and Endpoint tren resource

Dung API v1 cua Azure OpenAI: POST {endpoint}/openai/v1/chat/completions. Duong nay khong phai
khai api-version theo tung thang nhu duong cu. Tra tren Microsoft Learn ngay 12/09/2026.

Loi hay gap va y nghia, script dich san o duoi:
    401  sai key, hoac key cua resource khac
    404  sai ten deployment, day la loi pho bien nhat vi nguoi ta hay dien ten model
    429  het quota theo phut, vao Quotas tren Foundry ma nang TPM
"""
from __future__ import annotations

import json
import os
import sys
import time
from pathlib import Path

import requests
from dotenv import load_dotenv

# Console Windows mac dinh la cp1252, in tieng Viet co dau se vo. Ep utf-8.
sys.stdout.reconfigure(encoding="utf-8")

ROOT = Path(__file__).resolve().parents[1]
load_dotenv(ROOT / "python" / ".env")

ENDPOINT = (os.getenv("AZURE_OPENAI_ENDPOINT") or "").strip().rstrip("/")
DEPLOYMENT = (os.getenv("AZURE_OPENAI_DEPLOYMENT") or "").strip()
API_KEY = (os.getenv("AZURE_OPENAI_API_KEY") or "").strip()

CAU_HOI = (
    "Mot lo hang ton 470 don vi, con 25 ngay den han, ban binh quan 11 don vi mot ngay. "
    "Tra loi dung mot cau tieng Viet: co ban het truoc han khong, va vi sao."
)


def thieu_bien() -> list[str]:
    return [name for name, val in (
        ("AZURE_OPENAI_ENDPOINT", ENDPOINT),
        ("AZURE_OPENAI_DEPLOYMENT", DEPLOYMENT),
        ("AZURE_OPENAI_API_KEY", API_KEY),
    ) if not val]


def main() -> int:
    thieu = thieu_bien()
    if thieu:
        print("Thieu bien: " + ", ".join(thieu))
        print("Dat trong python/.env hoac trong bien moi truong roi chay lai.")
        return 2

    url = f"{ENDPOINT}/openai/v1/chat/completions"
    print(f"Goi   : {url}")
    print(f"Model : {DEPLOYMENT}  (ten deployment, khong phai ten model)")

    t0 = time.perf_counter()
    try:
        r = requests.post(
            url,
            headers={"api-key": API_KEY, "Content-Type": "application/json"},
            json={"model": DEPLOYMENT,
                  "messages": [{"role": "user", "content": CAU_HOI}],
                  "max_completion_tokens": 200},
            timeout=60,
        )
    except requests.RequestException as exc:
        print(f"Khong goi duoc: {exc}")
        print("Kiem lai endpoint. No phai la dang https://<ten resource>.openai.azure.com")
        return 1
    giay = time.perf_counter() - t0

    if r.status_code != 200:
        print(f"\nHTTP {r.status_code} sau {giay:.1f}s")
        print({401: "Sai API key, hoac key cua resource khac.",
               403: "Key dung nhung khong co quyen tren resource nay.",
               404: "Khong thay deployment. Kiem lai ten deployment, day la ten tu dat luc "
                    "deploy model chu khong phai ten model.",
               429: "Het quota theo phut. Vao Quotas tren Azure AI Foundry ma nang TPM.",
               }.get(r.status_code, "Xem chi tiet duoi day."))
        print(r.text[:600])
        return 1

    body = r.json()
    tra_loi = body["choices"][0]["message"]["content"].strip()
    dung = body.get("usage", {})
    print(f"\nHTTP 200 sau {giay:.1f}s")
    print(f"Model that su chay: {body.get('model', 'khong ro')}")
    print(f"Token: vao {dung.get('prompt_tokens', '?')}, ra {dung.get('completion_tokens', '?')}")
    print("\nCau hoi:\n  " + CAU_HOI)
    print("\nTra loi:\n  " + tra_loi.replace("\n", "\n  "))
    print("\nResource chay duoc. Ba bien tren dung de dien vao SetAuthorization ben AL khi dung cua D.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
