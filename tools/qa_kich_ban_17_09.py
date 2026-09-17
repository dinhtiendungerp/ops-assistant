"""QA kich ban demo 17/09 tren may chu tro ly dang chay (BC that), bam dung cac lenh console gui.

    cd python; python ../tools/qa_kich_ban_17_09.py [--tu 1] [--den 20] [--ghi]

Mac dinh KHONG bam cac nut ghi vao BC (duyet de xuat, gui don IC, xuat kho); `--ghi` moi bam. In moi buoc: thoi gian, tin
moi cua nguoi lien quan (cau, tieu de the, nguoi soan, kiem tra so), va canh bao khi: khong co tin, tin loi, cau mau khi can
AI, "Kiem tra so" co so khong khop, hoac cau tra loi co chu ky thuat (flags, tier, SlowMoving...). Ket qua ghi JSON vao
runs/qa-kich-ban.json de doi chieu.
"""
from __future__ import annotations

import argparse
import json
import re
import sys
import time
from pathlib import Path

import requests

URL = "http://127.0.0.1:8188"
RA = Path(__file__).resolve().parents[1] / "python" / "runs" / "qa-kich-ban.json"
CHU_KY_THUAT = re.compile(r"\b(flags?|tier|SlowMoving|NearExpiry|StockOutRisk|Expired|Excess|onHand|suggestedQty|daysOfCover|"
                          r"min_max|oos_|cham luan chuyen|riskScore)\b")


def goi(method, duong, ct, **kw):
    h = {"X-Cong-Ty": ct}
    r = requests.request(method, URL + duong, headers=h, timeout=240, **kw)
    try:
        return r.status_code, r.json()
    except ValueError:
        return r.status_code, r.text


def hop_thu(user, ct):
    _, rows = goi("GET", f"/api/inbox?user={user}", ct)
    return rows if isinstance(rows, list) else rows.get("rows", [])


def fact(card, ten):
    for f in (card or {}).get("facts") or []:
        k, v = (f[0], f[1]) if isinstance(f, list) else (f.get("label"), f.get("value"))
        if k == ten:
            return str(v)
    return ""


def tom_tat(m):
    c = m.get("card") or {}
    return {"id": m["id"], "dir": m.get("direction"), "skill": m.get("skill"), "text": (m.get("text") or "")[:600],
            "card": c.get("title", ""), "kind": c.get("kind", ""), "nguoi_soan": fact(c, "Người soạn"),
            "kiem_tra_so": fact(c, "Kiểm tra số"), "actions": [a.get("id") for a in c.get("actions") or []],
            "body": (c.get("body") or "")[:400]}


def canh_bao(b, tin, giay):
    cb = []
    ra = [t for t in tin if t["dir"] == "out"]
    if b["loai"] in ("chat", "brief") and not ra:
        cb.append("không có tin trả lời")
    for t in ra:
        chu = t["text"] + " " + t["body"]
        if re.search(r"chưa trả lời được|không chạy được|lỗi|Traceback|chưa nhận ra", chu, re.I):
            cb.append(f"câu báo lỗi/không hiểu: {t['text'][:90]}")
        if t["kiem_tra_so"]:
            cb.append(f"Kiểm tra số: {t['kiem_tra_so']}")
        if CHU_KY_THUAT.search(t["text"]):
            cb.append(f"chữ kỹ thuật trong câu: {CHU_KY_THUAT.search(t['text']).group(0)}")
        if b.get("can_ai") and t["nguoi_soan"].startswith("mẫu"):
            cb.append(f"cần AI mà ra câu mẫu: {t['nguoi_soan']}")
    if giay > 25:
        cb.append(f"chậm {giay:.0f} giây")
    return cb


def chay(buoc, ghi):
    b = buoc
    ct, user = b["ct"], b["ai"]
    truoc = {u: max([m["id"] for m in hop_thu(u, ct)] or [0]) for u in b.get("xem", [user])}
    t0 = time.time()
    kq = None
    if b["loai"] == "chat":
        kq = goi("POST", "/api/message", ct, json={"user": user, "text": b["text"]})
    elif b["loai"] == "brief":
        kq = goi("POST", "/api/brief", ct, json={"user": user, "text": ""})
    elif b["loai"] == "api":
        if b.get("ghi") and not ghi:
            return {"bo_qua": "ghi vào BC, chạy với --ghi"}
        kq = goi("POST", b["url"], ct, json={"user": user, **b.get("body", {})})
    elif b["loai"] == "tab":
        kq = goi("GET", b["url"], ct)
    elif b["loai"] == "nut":
        if not ghi:
            return {"bo_qua": "bấm nút ghi BC, chạy với --ghi"}
        rows = hop_thu(user, ct)
        the = [m for m in rows if any(a.get("id") == b["verb"] for a in ((m.get("card") or {}).get("actions") or []))
               and (not b.get("co") or b["co"] in json.dumps(m, ensure_ascii=False))]
        if not the:
            return {"loi": f"không thấy thẻ có nút {b['verb']}"}
        m = the[-1]
        a = next(a for a in m["card"]["actions"] if a.get("id") == b["verb"])
        kq = goi("POST", "/api/action", ct, json={"user": user, "verb": b["verb"], "ref": m["card"].get("ref") or m.get("ref"),
                                                   "payload": {**(a.get("payload") or {}), **b.get("payload", {})}})
    giay = time.time() - t0
    tin = []
    for u in b.get("xem", [user]):
        tin += [dict(tom_tat(m), cho=u) for m in hop_thu(u, ct) if m["id"] > truoc[u]]
    ra = {"http": kq[0] if kq else None, "tra_ve": (kq[1] if kq and not isinstance(kq[1], dict) else
                                                   {k: v for k, v in (kq[1] or {}).items() if k != "rows"}) if kq else None,
          "giay": round(giay, 1), "tin": tin}
    ra["canh_bao"] = canh_bao(b, tin, giay) + ([f"HTTP {kq[0]}: {str(kq[1])[:200]}"] if kq and kq[0] >= 400 else [])
    return ra


KICH_BAN = [
    {"so": 1, "ten": "Sức khỏe tồn kho", "loai": "tab", "url": "/api/uc2/summary?user=trang.sc", "ai": "trang.sc", "ct": "NWV-MAROU"},
    {"so": 2, "ten": "Brief AI", "loai": "brief", "ai": "trang.sc", "ct": "NWV-MAROU", "can_ai": True},
    {"so": 3, "ten": "Lô nào sắp hết hạn", "loai": "chat", "text": "lô nào sắp hết hạn", "ai": "trang.sc", "ct": "NWV-DAKAO"},
    {"so": 4, "ten": "Phương án Choco pillar S0010", "loai": "chat", "text": "phương án xử lý cho Choco pillar ở S0010", "ai": "trang.sc",
     "ct": "NWV-DAKAO", "can_ai": True},
    {"so": "4b", "ten": "Ghi đề xuất theo phương án", "loai": "nut", "verb": "ih_d4_apply", "ai": "trang.sc", "ct": "NWV-DAKAO",
     "xem": ["trang.sc", "hung.dieuphoi"]},
    {"so": 5, "ten": "Hùng duyệt chuyển hàng", "loai": "nut", "verb": "approve", "co": "Choco pillar", "ai": "hung.dieuphoi", "ct": "NWV-DAKAO"},
    {"so": 6, "ten": "Chậm luân chuyển", "loai": "chat", "text": "mặt hàng nào đang chậm luân chuyển ở các cửa hàng", "ai": "trang.sc",
     "ct": "NWV-DAKAO", "can_ai": True},
    {"so": 7, "ten": "CTKM cho hàng chậm", "loai": "chat", "text": "bạn có đề xuất gì về CTKM để bán các mặt hàng chậm luân chuyển này không",
     "ai": "trang.sc", "ct": "NWV-DAKAO", "can_ai": True},
    {"so": 8, "ten": "Truy xuất lô", "loai": "chat", "text": "truy xuất lô L260906-33323C", "ai": "trang.sc", "ct": "NWV-MAROU"},
    {"so": 9, "ten": "Bất thường 28 ngày", "loai": "chat", "text": "có gì bất thường trong 28 ngày qua không", "ai": "trang.sc",
     "ct": "NWV-DAKAO", "can_ai": True},
    {"so": 10, "ten": "Minh sắp hết Ice cream", "loai": "chat", "text": "sắp hết Ice cream ở cửa hàng tôi", "ai": "minh.s0002",
     "ct": "NWV-DAKAO", "xem": ["minh.s0002", "hung.dieuphoi"]},
    {"so": 11, "ten": "Vì sao LS Ice cream S0002", "loai": "chat", "text": "vì sao LS đề xuất Ice cream cho S0002", "ai": "trang.sc",
     "ct": "NWV-DAKAO"},
    {"so": "12a", "ten": "Hùng duyệt đặt mua", "loai": "nut", "verb": "approve", "co": "Ice cream", "ai": "hung.dieuphoi", "ct": "NWV-DAKAO"},
    {"so": "12b", "ten": "Gửi đơn sang Marou", "loai": "nut", "verb": "ic_gui_don", "ai": "hung.dieuphoi", "ct": "NWV-DAKAO"},
    {"so": 13, "ten": "Đề xuất bất thường", "loai": "chat", "text": "tổng hợp những đề xuất bổ sung bất thường", "ai": "trang.sc",
     "ct": "NWV-DAKAO", "can_ai": True},
    {"so": 14, "ten": "Dự báo Choco bowl", "loai": "chat", "text": "dự báo Choco bowl ở S0010 sai bao nhiêu", "ai": "trang.sc", "ct": "NWV-DAKAO"},
    {"so": 15, "ten": "CTKM", "loai": "chat", "text": "CTKM nào đang chạy và sắp tới", "ai": "trang.sc", "ct": "NWV-DAKAO"},
    {"so": 16, "ten": "Kiểm hàng Marou xuất kho", "loai": "api", "url": "/api/ic-nhan-hang", "body": {"chay_lai": True},
     "ai": "hung.dieuphoi", "ct": "NWV-DAKAO", "xem": ["hung.dieuphoi", "lan.s0001", "trang.sc", "tuan.s0005"]},
    {"so": 19, "ten": "Marou xuất kho Ice cream", "loai": "api", "url": "/api/demo/marou-xuat-kho", "ghi": True,
     "ai": "hung.dieuphoi", "ct": "NWV-DAKAO", "xem": ["hung.dieuphoi", "minh.s0002"]},
    {"so": 20, "ten": "Chi phí AI", "loai": "tab", "url": "/api/usage?user=dung.admin", "ai": "dung.admin", "ct": "NWV-MAROU"},
]


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--chi", default="", help="danh sach so buoc, vd 3,4,4b")
    ap.add_argument("--ghi", action="store_true")
    x = ap.parse_args()
    chon = set(x.chi.split(",")) if x.chi else None
    tat_ca = json.loads(RA.read_text(encoding="utf-8")) if RA.exists() else {}
    for b in KICH_BAN:
        if chon and str(b["so"]) not in chon:
            continue
        kq = chay(b, x.ghi)
        tat_ca[str(b["so"])] = {"ten": b["ten"], **kq}
        print(f"\n### {b['so']} {b['ten']}  ({kq.get('giay', '-')} s)")
        for t in kq.get("tin", []):
            print(f"  [{t['cho']}] {t['text'][:300]}")
            if t["card"]:
                print(f"      thẻ: {t['card']} | soạn: {t['nguoi_soan']} | nút: {t['actions']}")
        for k in ("bo_qua", "loi"):
            if kq.get(k):
                print("  !!", kq[k])
        if isinstance(kq.get("tra_ve"), (dict, str)) and b["loai"] in ("api", "tab"):
            print("  trả về:", str(kq["tra_ve"])[:300])
        for c in kq.get("canh_bao", []):
            print("  CẢNH BÁO:", c)
        sys.stdout.flush()
    RA.write_text(json.dumps(tat_ca, ensure_ascii=False, indent=1), encoding="utf-8")
