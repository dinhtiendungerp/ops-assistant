"""Cai dat nguoi quan tri sua duoc, luu tren dia.

Vi sao co file nay: truoc day muon doi tran chi phi, tat AI, sua nguong policy hay sua cau chu
cua tro ly thi phai sua `.env` hoac sua code roi khoi dong lai, tuc phai nho NaviWorld. Dung
yeu cau tu lam duoc. Va phai nho qua lan khoi dong lai, neu khong thi moi lan mo lai la mat het.

Ba nhom:
  - Tran chi phi va cong tac AI. Xem `assistant/budget.py`.
  - Nguong policy: moi dong `NWV Agent Policy` cho phep tu lam den muc nao. Xem `assistant/policy.py`.
  - Cau chu: chi tho cho model viet lai cau, va vai cau tro ly noi thang. Nhung cau nam trong
    tung skill thi van o code, vi chung dinh voi con so va ma hang.

Tren he thong that cua Marou, ba nhom nay nam trong bang cua BC va sua tren page, khong phai
mot file JSON. O ban POC de day cho gon.
"""
from __future__ import annotations

import json
import logging
import os
from pathlib import Path
from typing import Any

log = logging.getLogger(__name__)

DUONG = Path(os.getenv("AGENT_SETTINGS_FILE", "")) if os.getenv("AGENT_SETTINGS_FILE") else \
    Path(os.getenv("AGENT_LOG_DIR", "./runs")) / "cai-dat.json"

# Cau chu sua duoc. Key la ten trong code, `nhan` la ten nguoi quan tri doc.
CAU_MAU_GOC: dict[str, dict[str, str]] = {
    "viet_lai": {
        "nhan": "Chỉ thị cho model khi viết lại câu",
        "giai_thich": "Model chỉ được diễn đạt lại kết luận đã có. Câu này là chỗ cấm nó tự suy ra "
                      "con số mới, nên sửa thì giữ nguyên ý đó.",
        "text": "Viet lai doan sau thanh 2-3 cau tieng Viet cho nguoi dieu phoi kho doc tren dien thoai. "
                "Giu nguyen moi con so, ma hang, ma kho. Khong them thong tin.",
    },
    "tro_giup": {
        "nhan": "Câu trợ lý nói khi không hiểu yêu cầu",
        "giai_thich": "Hiện ra khi câu nhắn quá ngắn và không khớp rule nào.",
        "text": "Tôi là trợ lý vận hành. Bạn có thể nhắn: \"sắp hết Croissant plain\", "
                "\"còn bao nhiêu Chocolate ice cream\", \"brief\" để xem việc sáng nay. "
                "Điều phối duyệt đề xuất bằng nút trên thẻ.",
    },
    "da_ghi_giai_trinh": {
        "nhan": "Câu xác nhận sau khi ghi giải trình chiết khấu",
        "giai_thich": "Gửi cho nhân viên vừa gõ lý do.",
        "text": "Tôi đã ghi lại, cảm ơn bạn. Nếu gõ nhầm thì nhắn tôi một câu, "
                "tôi sửa được chừng nào Retail Ops chưa kết luận.",
    },
}

MAC_DINH: dict[str, Any] = {
    "tran_ngay_usd": None,      # None = giu mac dinh cua Budget (tuc theo bien moi truong)
    "tran_cong_don_usd": None,
    "ai_bat": None,             # None = theo LLM_MODE trong .env
    "shadow": None,             # None = theo AGENT_SHADOW_MODE
    "tran_tu_lam": None,        # None = theo AGENT_DAILY_AUTO_CAP
    "rules": {},                # {"P-01": {"mode": "auto", "max_value_vnd": 200}}
    "cau_mau": {},              # {"viet_lai": "..."}
}


def doc() -> dict[str, Any]:
    """Doc file cai dat. File hong hay khong co thi tra ve mac dinh, khong nem loi: mat cai dat
    con hon la tro ly khong khoi dong duoc."""
    out = dict(MAC_DINH)
    try:
        if DUONG.exists():
            out.update(json.loads(DUONG.read_text(encoding="utf-8")))
    except Exception as exc:
        log.warning("Khong doc duoc %s, dung mac dinh: %s", DUONG, exc)
    return out


def ghi(moi: dict[str, Any]) -> dict[str, Any]:
    """Tron `moi` vao cai dat dang co roi luu. Tra ve ban day du sau khi tron."""
    cu = doc()
    for k, v in moi.items():
        if k in ("rules", "cau_mau") and isinstance(v, dict):
            gop = dict(cu.get(k) or {})
            gop.update(v)
            cu[k] = gop
        else:
            cu[k] = v
    DUONG.parent.mkdir(parents=True, exist_ok=True)
    DUONG.write_text(json.dumps(cu, ensure_ascii=False, indent=2), encoding="utf-8")
    return cu


def cau(key: str) -> str:
    """Cau chu dang co hieu luc: ban quan tri sua neu co, khong thi ban goc."""
    da_sua = (doc().get("cau_mau") or {}).get(key)
    if isinstance(da_sua, str) and da_sua.strip():
        return da_sua
    return CAU_MAU_GOC[key]["text"]


def ap_vao(budget: Any, policy: Any) -> None:
    """Ap cai dat da luu len mot tro ly vua dung xong.

    Goi trong `Assistant.__init__`, sau khi Budget va PolicyEngine da co. Cai gi de None thi
    khong dung toi, de gia tri mac dinh cua hai lop do nguyen ven."""
    c = doc()
    if c.get("tran_ngay_usd") is not None:
        budget.cap = float(c["tran_ngay_usd"])
    if c.get("tran_cong_don_usd") is not None:
        budget.total_cap = float(c["tran_cong_don_usd"])
    if c.get("shadow") is not None:
        policy.shadow = bool(c["shadow"])
    if c.get("tran_tu_lam") is not None:
        policy.daily_auto_cap = int(c["tran_tu_lam"])
    for r in policy.rules:
        sua = (c.get("rules") or {}).get(r.code)
        if not sua:
            continue
        if sua.get("mode"):
            from .policy import Mode
            try:
                r.mode = Mode(sua["mode"])
            except ValueError:
                log.warning("Mode %r khong hop le cho %s, giu nguyen", sua["mode"], r.code)
        if "max_value_vnd" in sua:
            gt = sua["max_value_vnd"]
            r.max_value_vnd = None if gt in (None, "") else float(gt)
