"""Bo nho cua tro ly: SQLite mot file. Trong POC that thay bang Postgres, schema giu nguyen."""
from __future__ import annotations

import json
import sqlite3

from .ket_noi_sqlite import boc
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Iterable

SCHEMA = """
CREATE TABLE IF NOT EXISTS users (
  user_id TEXT PRIMARY KEY, display_name TEXT, role TEXT, store_code TEXT, channel TEXT, bc_user TEXT
);
CREATE TABLE IF NOT EXISTS messages (
  id INTEGER PRIMARY KEY AUTOINCREMENT, ts TEXT, user_id TEXT, direction TEXT, text TEXT, card_json TEXT, skill TEXT, ref TEXT,
  conv_id TEXT, reply_to INTEGER
);
CREATE INDEX IF NOT EXISTS ix_msg_conv ON messages(user_id, conv_id, id);
CREATE TABLE IF NOT EXISTS proposals (
  proposal_id TEXT PRIMARY KEY, bc_id TEXT, scenario TEXT, action_type TEXT, status TEXT, item_no TEXT,
  from_loc TEXT, to_loc TEXT, quantity REAL, max_quantity REAL, rationale TEXT, evidence TEXT,
  requested_by TEXT, approver TEXT, approved_at TEXT, result_doc TEXT, created_at TEXT, channel_ref TEXT,
  policy_rule TEXT, policy_mode TEXT, value_vnd REAL, item_category TEXT, outcome TEXT, outcome_note TEXT
);
CREATE TABLE IF NOT EXISTS followups (
  id INTEGER PRIMARY KEY AUTOINCREMENT, kind TEXT, ref TEXT, due_at TEXT, notify_user TEXT, escalate_user TEXT,
  attempts INTEGER DEFAULT 0, status TEXT DEFAULT 'open', note TEXT
);
CREATE TABLE IF NOT EXISTS pending_questions (
  id INTEGER PRIMARY KEY AUTOINCREMENT, user_id TEXT, kind TEXT, ref TEXT, asked_at TEXT, status TEXT DEFAULT 'open'
);
CREATE TABLE IF NOT EXISTS feedback (
  id INTEGER PRIMARY KEY AUTOINCREMENT, ts TEXT, proposal_id TEXT, kind TEXT, note TEXT, by_user TEXT
);
CREATE TABLE IF NOT EXISTS notes (k TEXT PRIMARY KEY, v TEXT, ts TEXT);
CREATE TABLE IF NOT EXISTS overrides (k TEXT PRIMARY KEY, v TEXT, ts TEXT);
CREATE TABLE IF NOT EXISTS kv (k TEXT PRIMARY KEY, v TEXT);
"""


class Memory:
    def __init__(self, path: Path | str = ":memory:"):
        self.conn = boc(sqlite3.connect(str(path), check_same_thread=False))
        self.conn.row_factory = sqlite3.Row
        self.conn.executescript(SCHEMA)

    # ---------- dong ho ao (demo "sang hom sau")
    def now(self) -> datetime:
        row = self.conn.execute("SELECT v FROM kv WHERE k='clock_offset_s'").fetchone()
        off = int(row["v"]) if row else 0
        return datetime.now(timezone.utc) + timedelta(seconds=off)

    def advance_clock(self, hours: float) -> datetime:
        row = self.conn.execute("SELECT v FROM kv WHERE k='clock_offset_s'").fetchone()
        off = int(row["v"]) if row else 0
        off += int(hours * 3600)
        self.conn.execute("INSERT OR REPLACE INTO kv(k,v) VALUES('clock_offset_s',?)", (str(off),))
        self.conn.commit()
        return self.now()

    # ---------- users
    def upsert_users(self, users: Iterable[dict[str, Any]]) -> None:
        for u in users:
            self.conn.execute(
                "INSERT OR REPLACE INTO users(user_id,display_name,role,store_code,channel,bc_user) VALUES(?,?,?,?,?,?)",
                (u["user_id"], u["display_name"], u["role"], u.get("store_code"), u.get("channel", "web"), u.get("bc_user")))
        self.conn.commit()

    def user(self, user_id: str) -> dict[str, Any] | None:
        r = self.conn.execute("SELECT * FROM users WHERE user_id=?", (user_id,)).fetchone()
        return dict(r) if r else None

    def users_by_role(self, role: str) -> list[dict[str, Any]]:
        return [dict(r) for r in self.conn.execute("SELECT * FROM users WHERE role=?", (role,))]

    def users(self) -> list[dict[str, Any]]:
        return [dict(r) for r in self.conn.execute("SELECT * FROM users ORDER BY role, display_name")]

    # ---------- messages
    def log_message(self, user_id: str, direction: str, text: str, card: dict | None = None, skill: str = "",
                    ref: str = "", reply_to: int | None = None) -> int:
        cur = self.conn.execute(
            "INSERT INTO messages(ts,user_id,direction,text,card_json,skill,ref,conv_id,reply_to) "
            "VALUES(?,?,?,?,?,?,?,?,?)",
            (self.now().isoformat(), user_id, direction, text, json.dumps(card, ensure_ascii=False) if card else None,
             skill, ref, self.doan_dang_mo(user_id), reply_to))
        self.conn.commit()
        return int(cur.lastrowid)

    def message(self, msg_id: int) -> dict[str, Any] | None:
        r = self.conn.execute("SELECT * FROM messages WHERE id=?", (msg_id,)).fetchone()
        return dict(r) if r else None

    # ---------- doan chat
    def doan_dang_mo(self, user_id: str) -> str:
        """Doan chat dang mo cua mot nguoi. Chua co thi tao doan dau tien."""
        r = self.conn.execute("SELECT v FROM kv WHERE k=?", (f"doan:{user_id}",)).fetchone()
        if r:
            return r["v"]
        return self.doan_moi(user_id)

    def doan_moi(self, user_id: str) -> str:
        import uuid as _uuid

        ma = _uuid.uuid4().hex[:12]
        self.conn.execute("INSERT OR REPLACE INTO kv(k,v) VALUES(?,?)", (f"doan:{user_id}", ma))
        self.conn.commit()
        return ma

    def mo_doan(self, user_id: str, conv_id: str) -> None:
        self.conn.execute("INSERT OR REPLACE INTO kv(k,v) VALUES(?,?)", (f"doan:{user_id}", conv_id))
        self.conn.commit()

    def cac_doan(self, user_id: str, limit: int = 30) -> list[dict[str, Any]]:
        """Danh sach doan chat, moi doan lay cau dau nguoi do go lam ten.

        Doan chua co tin nao thi khong hien, de bam "Doan moi" hai lan khong sinh ra hai dong rong."""
        rows = self.conn.execute(
            "SELECT conv_id, COUNT(*) n, MIN(id) dau, MAX(ts) cuoi FROM messages "
            "WHERE user_id=? AND conv_id IS NOT NULL GROUP BY conv_id ORDER BY MAX(id) DESC LIMIT ?",
            (user_id, limit)).fetchall()
        dang_mo = self.doan_dang_mo(user_id)
        out = []
        for r in rows:
            t = self.conn.execute(
                "SELECT text FROM messages WHERE user_id=? AND conv_id=? AND direction='in' ORDER BY id LIMIT 1",
                (user_id, r["conv_id"])).fetchone()
            ten = (t["text"] if t else "") or "Trợ lý mở lời"
            out.append({"conv_id": r["conv_id"], "ten": ten[:60], "so_tin": int(r["n"]),
                        "cuoi": r["cuoi"], "dang_mo": r["conv_id"] == dang_mo})
        if not any(d["dang_mo"] for d in out):
            out.insert(0, {"conv_id": dang_mo, "ten": "Đoạn chat mới", "so_tin": 0,
                           "cuoi": self.now().isoformat(), "dang_mo": True})
        return out

    def inbox(self, user_id: str, after_id: int = 0) -> list[dict[str, Any]]:
        rows = self.conn.execute(
            "SELECT * FROM messages WHERE user_id=? AND id>? AND conv_id=? ORDER BY id",
            (user_id, after_id, self.doan_dang_mo(user_id)))
        out = []
        for r in rows:
            d = dict(r)
            d["card"] = json.loads(d.pop("card_json")) if d.get("card_json") else None
            if d.get("reply_to"):
                g = self.message(int(d["reply_to"]))
                d["trich"] = (g["text"] or "")[:160] if g else ""
            out.append(d)
        return out

    # ---------- proposals
    def save_proposal(self, p: dict[str, Any]) -> None:
        cols = ("proposal_id", "bc_id", "scenario", "action_type", "status", "item_no", "from_loc", "to_loc", "quantity",
                "max_quantity", "rationale", "evidence", "requested_by", "approver", "approved_at", "result_doc", "created_at", "channel_ref",
                "policy_rule", "policy_mode", "value_vnd", "item_category", "outcome", "outcome_note")
        vals = [p.get(c) if c != "evidence" else json.dumps(p.get("evidence", {}), ensure_ascii=False) for c in cols]
        self.conn.execute(f"INSERT OR REPLACE INTO proposals({','.join(cols)}) VALUES({','.join('?' * len(cols))})", vals)
        self.conn.commit()

    def proposal(self, proposal_id: str) -> dict[str, Any] | None:
        r = self.conn.execute("SELECT * FROM proposals WHERE proposal_id=?", (proposal_id,)).fetchone()
        if not r:
            return None
        d = dict(r)
        d["evidence"] = json.loads(d["evidence"] or "{}")
        return d

    def proposals(self, status: str | None = None) -> list[dict[str, Any]]:
        q = "SELECT * FROM proposals" + (" WHERE status=?" if status else "") + " ORDER BY created_at DESC"
        rows = self.conn.execute(q, (status,) if status else ()).fetchall()
        return [dict(r) for r in rows]

    def log_feedback(self, proposal_id: str, kind: str, note: str, by_user: str) -> None:
        """Ly do tu choi / hoan tac. Dung cho vong tu danh gia va chinh policy."""
        self.conn.execute("INSERT INTO feedback(ts,proposal_id,kind,note,by_user) VALUES(?,?,?,?,?)",
                          (self.now().isoformat(), proposal_id, kind, note, by_user))
        self.conn.commit()

    def feedback(self) -> list[dict[str, Any]]:
        return [dict(r) for r in self.conn.execute("SELECT * FROM feedback ORDER BY id DESC")]

    def set_outcome(self, proposal_id: str, outcome: str, note: str) -> None:
        self.conn.execute("UPDATE proposals SET outcome=?, outcome_note=? WHERE proposal_id=?", (outcome, note, proposal_id))
        self.conn.commit()

    # ---------- ghi nho ket qua dieu tra va tham so rieng
    def remember(self, key: str, value: dict[str, Any]) -> None:
        self.conn.execute("INSERT OR REPLACE INTO notes(k,v,ts) VALUES(?,?,?)",
                          (key, json.dumps(value, ensure_ascii=False, default=str), self.now().isoformat()))
        self.conn.commit()

    def recall(self, key: str) -> dict[str, Any] | None:
        r = self.conn.execute("SELECT v FROM notes WHERE k=?", (key,)).fetchone()
        return json.loads(r["v"]) if r else None

    def set_override(self, key: str, value: dict[str, Any]) -> None:
        """Tham so rieng cho mot cap store|item, do nguoi duyet tu ket qua dieu tra."""
        self.conn.execute("INSERT OR REPLACE INTO overrides(k,v,ts) VALUES(?,?,?)",
                          (key, json.dumps(value, ensure_ascii=False, default=str), self.now().isoformat()))
        self.conn.commit()

    def overrides(self) -> dict[str, dict[str, Any]]:
        return {r["k"]: json.loads(r["v"]) for r in self.conn.execute("SELECT k,v FROM overrides")}

    # ---------- follow-ups
    def add_followup(self, kind: str, ref: str, due_at: datetime, notify_user: str, escalate_user: str = "", note: str = "") -> int:
        cur = self.conn.execute(
            "INSERT INTO followups(kind,ref,due_at,notify_user,escalate_user,note) VALUES(?,?,?,?,?,?)",
            (kind, ref, due_at.isoformat(), notify_user, escalate_user, note))
        self.conn.commit()
        return int(cur.lastrowid)

    def due_followups(self) -> list[dict[str, Any]]:
        now = self.now().isoformat()
        return [dict(r) for r in self.conn.execute("SELECT * FROM followups WHERE status='open' AND due_at<=? ORDER BY due_at", (now,))]

    def update_followup(self, fid: int, **fields: Any) -> None:
        sets = ", ".join(f"{k}=?" for k in fields)
        self.conn.execute(f"UPDATE followups SET {sets} WHERE id=?", (*fields.values(), fid))
        self.conn.commit()

    def dem_tin_ra(self) -> dict[str, int]:
        """So tin tro ly da gui cho tung nguoi. Giao dien dung de cham dau nguoi co tin moi.

        Doi vai tro trong buoi demo la chuyen thuong xuyen, va truoc day nguoi xem khong biet
        vai tro nao vua nhan viec. Dem o day chu khong tinh o giao dien, vi giao dien chi giu
        duoc phan no da tai."""
        rows = self.conn.execute(
            "SELECT user_id, COUNT(*) n FROM messages WHERE direction='out' GROUP BY user_id").fetchall()
        return {r["user_id"]: int(r["n"]) for r in rows}

    def followups(self) -> list[dict[str, Any]]:
        return [dict(r) for r in self.conn.execute("SELECT * FROM followups ORDER BY due_at")]

    # ---------- pending questions (giai trinh)
    def ask(self, user_id: str, kind: str, ref: str) -> int:
        cur = self.conn.execute("INSERT INTO pending_questions(user_id,kind,ref,asked_at) VALUES(?,?,?,?)",
                                (user_id, kind, ref, self.now().isoformat()))
        self.conn.commit()
        return int(cur.lastrowid)

    def pending_question(self, user_id: str, ref: str | None = None) -> dict[str, Any] | None:
        """Cau hoi dang cho. `ref` cho phep chi dinh dung cau hoi nao, khi nguoi dung bam Tra loi
        vao mot tin cu the thay vi tra loi cau hoi moi nhat."""
        if ref:
            r = self.conn.execute(
                "SELECT * FROM pending_questions WHERE user_id=? AND ref=? AND status='open' ORDER BY id DESC LIMIT 1",
                (user_id, ref)).fetchone()
            if r:
                return dict(r)
        r = self.conn.execute("SELECT * FROM pending_questions WHERE user_id=? AND status='open' ORDER BY id DESC LIMIT 1", (user_id,)).fetchone()
        return dict(r) if r else None

    def close_question(self, qid: int) -> None:
        self.conn.execute("UPDATE pending_questions SET status='answered' WHERE id=?", (qid,))
        self.conn.commit()
