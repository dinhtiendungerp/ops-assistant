"""Nhat ky quyet dinh cua tro ly, ghep tu viec that trong ngay.

Thay cho "ca dem" (bo ngay 13/09/2026). Ca dem chay lai Brief cua dieu phoi theo lo, khong goi
model lan nao, nen dem no ra tra loi cau "agent o dau" la tu dua bang chung agent chi la kich ban.
Tai lieu 04 muc 2 da xep loai viec do vao cot Job Queue lam duoc. Dung chi ra.

Nhat ky nay khong tu chay gi. No doc lai nhung gi da xay ra: de xuat nao duoc soan, policy nao
cho tu lam hay bat hoi nguoi, ai duyet, ai tu choi, va cau hoi nao di qua model hay qua kich ban
da duyet. Moi dong truy nguoc duoc ve dong policy hoac ve chuoi tool.
"""
from __future__ import annotations

from typing import Any

from . import kich_ban

_VIEC_NGUON = {"model": "Tự dựng chuỗi tra cứu", "kich_ban": "Chạy kịch bản đã duyệt",
               "ban_ghi": "Chạy bản ghi dựng sẵn", "khong_tra_loi": "Không trả lời được"}


def _ten(asst: Any, uid: str) -> str:
    if not uid:
        return ""
    if uid.startswith("agent:"):
        return "Trợ lý"
    u = asst.mem.user(uid)
    return (u or {}).get("display_name", uid).split(" (")[0]


def quyet_dinh(asst: Any, gioi_han: int = 80) -> list[dict[str, Any]]:
    ra: list[dict[str, Any]] = []
    for p in asst.de_xuat_gop():
        trang_thai, duyet = p.get("status") or "", str(p.get("approver") or "")
        if duyet.startswith("agent:"):
            viec, loai = "Tự làm theo policy", "ok"
        elif trang_thai == "Proposed":
            viec, loai = "Đưa người duyệt", "cho"
        elif trang_thai == "Executed":
            viec, loai = "Người duyệt đồng ý", "ok"
        elif trang_thai == "Rejected":
            viec, loai = "Bị từ chối", "loi"
        else:
            viec, loai = trang_thai or "Đề xuất", ""
        ghi_chu = str(p.get("rationale") or "")
        if len(ghi_chu) > 180:
            ghi_chu = ghi_chu[:177].rstrip() + "…"
        ra.append({
            "ts": str(p.get("approved_at") or p.get("created_at") or ""), "loai": loai, "viec": viec,
            "doi_tuong": p.get("item_desc") or p.get("item_no") or "", "ma": p.get("item_no") or "",
            "noi": p.get("to_loc") or p.get("from_loc") or "", "so_luong": p.get("quantity") or 0,
            "hanh_dong": p.get("action_type") or "", "policy": p.get("policy_rule") or "",
            "ai_quyet": _ten(asst, duyet) if trang_thai != "Proposed" else "",
            "chung_tu": p.get("result_doc") or "", "ghi_chu": ghi_chu,
        })
    for g in _cau_hoi_gan_day(40):
        ra.append({
            "ts": g["ts"], "loai": "ok" if g["nguon"] in ("kich_ban", "model") else ("loi" if g["nguon"] == "khong_tra_loi" else ""),
            "viec": _VIEC_NGUON.get(g["nguon"], g["nguon"]) + (f" {g['kich_ban_id']}" if g["nguon"] == "kich_ban" else ""),
            "doi_tuong": g["cau"], "ma": "", "noi": "", "so_luong": 0, "hanh_dong": "hỏi đáp", "policy": "",
            "ai_quyet": _ten(asst, g["user_id"]), "chung_tu": "",
            "ghi_chu": (f"{g['token']:,} token".replace(",", ".") if g["token"] else "0 token")
                       + ({"dung": ", người hỏi báo đúng", "sai": ", người hỏi báo chưa đúng"}.get(g["danh_gia"], "")),
        })
    ra.sort(key=lambda r: r["ts"], reverse=True)
    return ra[:gioi_han]


def _cau_hoi_gan_day(n: int) -> list[dict[str, Any]]:
    with kich_ban._ket_noi() as c:
        return [dict(r) for r in c.execute(
            "SELECT ts,user_id,cau,nguon,kich_ban_id,token,danh_gia FROM cau_hoi ORDER BY id DESC LIMIT ?", (n,))]


def tong_hop(asst: Any) -> dict[str, Any]:
    nhom = kich_ban.nhom_cau_hoi()
    ds = kich_ban.danh_sach()
    return {
        "quyet_dinh": quyet_dinh(asst),
        "cau_hoi": nhom,
        "kich_ban": [{k: v for k, v in kb.items() if k not in ("buoc",)} for kb in ds],
        "tong": {
            "cau_ngoai_rule": sum(g["so_lan"] for g in nhom),
            "goi_model": sum(g["goi_model"] for g in nhom),
            "chay_kich_ban": sum(g["chay_kich_ban"] for g in nhom),
            "khong_tra_loi": sum(g["khong_tra_loi"] for g in nhom),
            "kich_ban_bat": sum(1 for kb in ds if kb["bat"]),
            "token_tiet_kiem": sum(kb["token_tiet_kiem"] for kb in ds),
            "usd_tiet_kiem": round(sum(kb["usd_tiet_kiem"] for kb in ds), 6),
        },
    }
