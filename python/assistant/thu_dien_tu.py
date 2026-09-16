"""Gui email nhac viec, va so ghi moi thu da gui.

Vi sao co file nay (15/09/2026). Dung chot ranh gioi: tro ly chi phat hien va nhac, nguoi post chung tu. Nhung phai thay tro
ly tu chu dong: vua nhac qua chat, vua tu soan email roi gui. File nay lo phan gui va phan ghi so; noi dung thu do skill
soan (vi du `skills/nhac_post.py`).

Ba kenh gui, chon bang MAIL_MODE trong .env (auto la mac dinh):
  graph  Microsoft Graph `POST /users/{MAIL_SENDER}/sendMail`, dung chinh Entra app S2S cua tro ly. Can quyen ung dung
         Mail.Send (Microsoft Graph, Application) da duoc admin consent, va MAIL_SENDER la hop thu co that trong tenant.
         Tra Microsoft Learn ngay 15/09/2026: Mail.Send application "Allows the app to send mail as any user without a
         signed-in user", AdminConsentRequired = Yes; gioi han hop thu duoc gui bang RBAC for Applications cua Exchange Online.
  smtp   SMTP_HOST, SMTP_PORT, SMTP_USER, SMTP_PASSWORD (STARTTLS). Mat khau do nguoi quan tri tu dien vao .env.
  file   Khong gui ra ngoai: ghi file .eml vao runs/thu-di/. Dung khi chua cau hinh kenh nao, de tinh nang van chay va
         noi ro la chua gui that.
auto: co MAIL_SENDER thi graph, co SMTP_HOST thi smtp, khong co gi thi file.

Moi thu, gui duoc hay khong, deu ghi vao runs/thu-di.sqlite: gui cho ai, tieu de, noi dung, kenh, trang thai, loi. Khoa
chong trung (`khoa`) de mot viec khong bi nhac hai lan trong cung ngay.
"""
from __future__ import annotations

import logging
import smtplib
import sqlite3
from datetime import datetime, timezone
from email.message import EmailMessage
from pathlib import Path
from typing import Any

from bc_agent.config import Settings

log = logging.getLogger(__name__)

DUONG = Path(Settings().log_dir) / "thu-di.sqlite"
THU_MUC_EML = Path(Settings().log_dir) / "thu-di"

_SQL = """
CREATE TABLE IF NOT EXISTS thu (
  id INTEGER PRIMARY KEY AUTOINCREMENT, ts TEXT, ngay TEXT, cong_ty TEXT, loai TEXT, khoa TEXT,
  den TEXT, tieu_de TEXT, noi_dung TEXT, nguoi_soan TEXT, kenh TEXT, trang_thai TEXT, loi TEXT
);
CREATE INDEX IF NOT EXISTS ix_thu_khoa ON thu(khoa, ngay);
"""


def _ket_noi() -> sqlite3.Connection:
    DUONG.parent.mkdir(parents=True, exist_ok=True)
    c = sqlite3.connect(DUONG)
    c.row_factory = sqlite3.Row
    c.executescript(_SQL)
    return c


def kenh(s: Settings | None = None) -> str:
    s = s or Settings()
    m = (s.mail_mode or "auto").strip().lower()
    if m in ("graph", "smtp", "file"):
        return m
    if s.mail_sender:
        return "graph"
    if s.smtp_host:
        return "smtp"
    return "file"


def nguoi_nhan_mac_dinh(s: Settings | None = None) -> list[str]:
    s = s or Settings()
    return [x.strip() for x in (s.mail_to or "").replace(";", ",").split(",") if x.strip()]


def da_gui_hom_nay(khoa: str, ngay: str) -> bool:
    """Viec nay da co thu (gui that hoac ghi file) trong ngay chua. Thu loi khong tinh, de lan sau thu lai."""
    with _ket_noi() as c:
        return bool(c.execute("SELECT 1 FROM thu WHERE khoa=? AND ngay=? AND trang_thai!='loi'", (khoa, ngay)).fetchone())


def gan_day(n: int = 30) -> list[dict[str, Any]]:
    with _ket_noi() as c:
        return [dict(r) for r in c.execute("SELECT * FROM thu ORDER BY id DESC LIMIT ?", (n,)).fetchall()]


def _gui_graph(s: Settings, den: list[str], tieu_de: str, html: str) -> None:
    import msal
    import requests

    app = msal.ConfidentialClientApplication(s.bc_client_id, client_credential=s.bc_client_secret,
                                             authority=f"https://login.microsoftonline.com/{s.bc_tenant_id}")
    tk = app.acquire_token_for_client(scopes=["https://graph.microsoft.com/.default"])
    if "access_token" not in tk:
        raise RuntimeError(f"Không lấy được token Microsoft Graph: {tk.get('error_description') or tk.get('error')}")
    than = {"message": {"subject": tieu_de, "body": {"contentType": "HTML", "content": html},
                        "toRecipients": [{"emailAddress": {"address": a}} for a in den]},
            "saveToSentItems": True}
    r = requests.post(f"https://graph.microsoft.com/v1.0/users/{s.mail_sender}/sendMail",
                      headers={"Authorization": f"Bearer {tk['access_token']}", "Content-Type": "application/json"},
                      json=than, timeout=60)
    if r.status_code >= 400:
        try:
            loi = r.json().get("error", {})
            cau = f"{loi.get('code')}: {loi.get('message')}"
        except ValueError:
            cau = r.text[:300]
        if r.status_code == 403:
            cau += (" (Entra app chưa có quyền Mail.Send loại Application trên Microsoft Graph, hoặc chưa được admin consent,"
                    " hoặc hộp thư gửi bị giới hạn bởi RBAC for Applications.)")
        raise RuntimeError(f"Microsoft Graph trả HTTP {r.status_code}. {cau}")


def _thu_eml(s: Settings, den: list[str], tieu_de: str, text: str, html: str) -> EmailMessage:
    m = EmailMessage()
    m["Subject"] = tieu_de
    m["From"] = s.mail_sender or s.smtp_user or "tro-ly@marou.local"
    m["To"] = ", ".join(den)
    m.set_content(text)
    m.add_alternative(html, subtype="html")
    return m


def _gui_smtp(s: Settings, den: list[str], tieu_de: str, text: str, html: str) -> None:
    with smtplib.SMTP(s.smtp_host, s.smtp_port, timeout=60) as sv:
        sv.starttls()
        if s.smtp_user:
            sv.login(s.smtp_user, s.smtp_password)
        sv.send_message(_thu_eml(s, den, tieu_de, text, html))


def gui(*, tieu_de: str, text: str, html: str, den: list[str] | None = None, loai: str = "", khoa: str = "",
        cong_ty: str = "", nguoi_soan: str = "", ngay: str = "", s: Settings | None = None) -> dict[str, Any]:
    """Gui mot thu va ghi so. Khong nem loi ra ngoai: gui hong thi ghi trang_thai='loi' kem cau loi de hien len chat."""
    s = s or Settings()
    den = den or nguoi_nhan_mac_dinh(s)
    k = kenh(s)
    ngay = ngay or datetime.now().strftime("%Y-%m-%d")
    trang_thai, loi = "da_gui", ""
    if not den:
        trang_thai, loi = "loi", "Chưa có địa chỉ nhận: đặt MAIL_TO trong python/.env."
    else:
        try:
            if k == "graph":
                _gui_graph(s, den, tieu_de, html)
            elif k == "smtp":
                _gui_smtp(s, den, tieu_de, text, html)
            else:
                THU_MUC_EML.mkdir(parents=True, exist_ok=True)
                ten = f"{datetime.now().strftime('%Y%m%d-%H%M%S')}-{(khoa or loai or 'thu').replace('|', '_')[:60]}.eml"
                (THU_MUC_EML / ten).write_bytes(bytes(_thu_eml(s, den, tieu_de, text, html)))
                trang_thai = "chi_luu_file"
        except Exception as exc:                       # gui hong khong duoc lam gay luong nhac qua chat
            log.warning("Gui thu hong: %s", exc)
            trang_thai, loi = "loi", str(exc)[:500]
    with _ket_noi() as c:
        cur = c.execute("INSERT INTO thu(ts,ngay,cong_ty,loai,khoa,den,tieu_de,noi_dung,nguoi_soan,kenh,trang_thai,loi) "
                        "VALUES(?,?,?,?,?,?,?,?,?,?,?,?)",
                        (datetime.now(timezone.utc).isoformat(), ngay, cong_ty, loai, khoa, ", ".join(den), tieu_de, text,
                         nguoi_soan, k, trang_thai, loi))
        ma = cur.lastrowid
    return {"id": ma, "den": den, "tieu_de": tieu_de, "kenh": k, "trang_thai": trang_thai, "loi": loi}


TEN_TRANG_THAI = {"da_gui": "đã gửi", "chi_luu_file": "chưa gửi ra ngoài, đã lưu file .eml (chưa cấu hình kênh gửi)",
                  "loi": "gửi không được"}
TEN_KENH = {"graph": "Microsoft Graph", "smtp": "SMTP", "file": "file .eml trong runs/thu-di"}
