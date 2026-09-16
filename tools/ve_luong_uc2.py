"""Ve so do tuan tu cac luong UC2 thanh anh PNG cho tai lieu (docs/uc2/luong-*.png).

Moi luong la mot bang lan (thanh phan theo cot) va buoc (mui ten tu lan nay sang lan kia). Sinh HTML roi chup bang
Chrome headless, cat phan trang thua bang Pillow. Chay: python tools/ve_luong_uc2.py
"""
from __future__ import annotations

import html
import subprocess
from pathlib import Path

from PIL import Image

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "docs" / "uc2"
CHROME = r"C:\Program Files\Google\Chrome\Application\chrome.exe"

LUONG = {
    "luong-1-tinh-trong-bc": {
        "tieu_de": "Luồng 1. Business Central tính sức khỏe tồn kho (hằng đêm hoặc bấm Run)",
        "lan": ["Job Queue / người bấm Run", "NWV Inv. Health Calc (70101)", "NWV Demand Calc (70110)",
                "NWV Agent Setup, Category Threshold", "Item Ledger Entry", "NWV Inv. Health Line"],
        "buoc": [
            (0, 1, "NWV Agent Job Runner tham số INVHEALTH, hoặc nút Run Inventory Health. Ngày neo = Work Date"),
            (1, 3, "Đọc ngưỡng: Sales History Days 90, Stock-out Risk 7, Near Expiry 45, Slow-moving 60, Excess 90"),
            (1, 2, "Build(ngày neo, 90 ngày, kho trung tâm W0003)"),
            (2, 4, "Một lượt đọc sổ kho, gom theo ngày; bỏ ngày tồn 0 mà không bán; kho trung tâm tính tổng lượng xuất"),
            (2, 1, "Nhu cầu bình quân ngày theo mặt hàng x địa điểm, cơ sở Sale hoặc Outflow"),
            (1, 4, "Dòng còn Open, Remaining Quantity khác 0, gom theo mặt hàng x địa điểm x lô; hạn dùng của lô"),
            (1, 3, "Ngưỡng riêng theo nhóm hàng nếu có (NWV Category Threshold)"),
            (1, 1, "Cây 6 bậc, dừng ở bậc đầu tiên khớp: quá hạn, cận hạn, rủi ro đứt hàng, chậm, thừa, bình thường"),
            (1, 5, "Xoá kết quả cũ, ghi 167 dòng: tầng, điểm rủi ro, lý do, days of cover, hạn còn, giá trị"),
        ],
    },
    "luong-2-dashboard": {
        "tieu_de": "Luồng 2. Người dùng xem dashboard Sức khỏe tồn kho và Chi tiết lô",
        "lan": ["Người dùng", "Web console (index.html)", "FastAPI (web.py, uc2.py)", "BCGateway (bộ nhớ theo bảng)",
                "API page chỉ đọc (BC)", "Bảng trong BC"],
        "buoc": [
            (0, 1, "Mở tab Sức khỏe tồn kho, bấm ô tầng để lọc"),
            (1, 2, "GET /api/uc2/summary và /api/uc2/lines?tier="),
            (2, 3, "doc(\"inventoryHealthLines\")"),
            (3, 4, "Chỉ gọi BC khi bộ nhớ quá 60 giây: GET api/naviworld/marouagent/v1.0/.../inventoryHealthLines"),
            (4, 5, "Đọc NWV Inv. Health Line"),
            (3, 2, "Dòng kết quả; uc2.py cộng giá trị theo tầng, không tính lại tầng"),
            (0, 1, "Bấm một dòng"),
            (1, 2, "GET /api/uc2/trace?line_id="),
            (2, 3, "Dòng đó (từ bộ nhớ) và bán theo ngày 90 ngày (nwvItemLedgerEntries, Sale; bộ nhớ 15 phút)"),
            (2, 1, "Nguồn số, cây phân tầng dừng ở bậc nào, bảng bán theo ngày để cộng tay"),
            (1, 0, "Link mở Item Ledger Entries và dòng Inventory Health trong BC, lọc đúng mặt hàng, kho, lô"),
        ],
    },
    "luong-3-chat-de-xuat-duyet": {
        "tieu_de": "Luồng 3. Hỏi lô hết hạn trong chat, đề xuất hủy, người duyệt quyết định",
        "lan": ["Người hỏi (vd Supply Chain)", "Trợ lý: Rule NLU và skill", "Policy engine", "Business Central",
                "Người duyệt (Điều phối)"],
        "buoc": [
            (0, 1, "\"có mặt hàng nào đã hết hạn chưa\""),
            (1, 1, "Rule nhận ra intent EXPIRY. Không gọi model, 0 token"),
            (1, 3, "Đọc inventoryHealthLines tầng Expired; vai có địa điểm chỉ thấy địa điểm mình"),
            (1, 0, "Câu tóm tắt theo địa điểm và thẻ từng lô: Đề xuất hủy, Chuyển sang cửa hàng bán nhanh (lô cận hạn)"),
            (0, 1, "Bấm Đề xuất hủy trên thẻ một lô"),
            (1, 3, "Kiểm đề xuất trùng: Reference Key mặt hàng|kho|lô còn hiệu lực trong BC"),
            (1, 2, "Xét policy: P-05 hủy hàng luôn cần người duyệt"),
            (1, 3, "POST agentProposals: WriteOff, trạng thái Proposed, số lô, lý do, số liệu đã đọc"),
            (1, 4, "Thẻ Duyệt hủy / Từ chối đến hộp thư người duyệt, kèm link lô trong BC"),
            (4, 3, "Duyệt: NWV Agent Proposal Mgt. Transfer tạo Transfer Order Open; WriteOff, Markdown chỉ ghi nhận quyết định"),
        ],
    },
    "luong-4-truy-xuat-lo": {
        "tieu_de": "Luồng 4. Truy xuất một lô để thu hồi",
        "lan": ["Người hỏi", "Trợ lý: Rule NLU và skill truy_xuat", "API page nwvItemLedgerEntries", "Item Ledger Entry"],
        "buoc": [
            (0, 1, "\"truy xuất lô L260908-33170B\""),
            (1, 1, "Rule nhận ra intent TRACE và số lô"),
            (1, 2, "GET nwvItemLedgerEntries lọc Lot No."),
            (2, 3, "Mọi dòng của lô: nhập, nhận, xuất, bán, tại mọi địa điểm"),
            (2, 1, "Danh sách dòng kèm Posting Date, Entry Type, Location, Quantity, Expiration Date"),
            (1, 1, "Gom theo địa điểm và loại bút toán; còn tồn = tổng Quantity có dấu; so hạn dùng với ngày neo"),
            (1, 0, "Còn ở đâu bao nhiêu, đã bán bao nhiêu, thu hồi lấy lại ở đâu; link Item Ledger Entries lọc đúng lô"),
        ],
    },
}

CSS = """
body{margin:0;font-family:'Segoe UI',Arial,sans-serif;background:#fff;color:#2b2521}
.wrap{padding:18px 18px;width:1000px;box-sizing:border-box}
h2{margin:0 0 14px;font-size:21px;color:#7a1f1f}
.lanes{display:grid;gap:10px;margin-bottom:6px}
.lane{background:#23507d;color:#fff;border-radius:8px;padding:8px 10px;font-size:13.5px;font-weight:600;text-align:center;line-height:1.2;
      display:flex;align-items:center;justify-content:center;min-height:52px}
.step{position:relative;height:92px}
.vl{position:absolute;top:0;bottom:0;border-left:2px dashed #c9bfb5}
.arrow{position:absolute;top:68px;height:0;border-top:2.5px solid #8b1e1e}
.arrow.left::before,.arrow.right::after{content:"";position:absolute;top:-7px;border:6px solid transparent}
.arrow.right::after{right:-2px;border-left:10px solid #8b1e1e}
.arrow.left::before{left:-2px;border-right:10px solid #8b1e1e}
.self{position:absolute;top:52px;width:34px;height:26px;border:2.5px solid #8b1e1e;border-left:none;border-radius:0 12px 12px 0}
.lbl{position:absolute;top:2px;font-size:15px;line-height:1.28;color:#2b2521;background:#fff;padding:0 4px}
.no{display:inline-block;min-width:20px;height:20px;border-radius:10px;background:#8b1e1e;color:#fff;font-size:12px;
    text-align:center;line-height:20px;margin-right:5px;font-weight:700}
"""


def ve(ma: str, d: dict) -> Path:
    n = len(d["lan"])
    w = 1000 - 36
    cot = w / n
    tam = [cot * i + cot / 2 for i in range(n)]
    rows = []
    for k, (a, b, nhan) in enumerate(d["buoc"], 1):
        vls = "".join(f'<div class="vl" style="left:{x:.0f}px"></div>' for x in tam)
        chu = f'<span class="no">{k}</span>{html.escape(nhan)}'
        if a == b:
            x = tam[a]
            ve_ = f'<div class="self" style="left:{x:.0f}px"></div>'
            lbl = f'<div class="lbl" style="left:{x + 40:.0f}px;max-width:{min(w - x - 50, cot * 3.2):.0f}px">{chu}</div>'
        else:
            x1, x2 = sorted((tam[a], tam[b]))
            huong = "right" if b > a else "left"
            ve_ = f'<div class="arrow {huong}" style="left:{x1:.0f}px;width:{x2 - x1:.0f}px"></div>'
            rong = max(x2 - x1 - 10, cot * 2.4)
            trai = min(x1 + 6, w - rong)
            lbl = f'<div class="lbl" style="left:{trai:.0f}px;max-width:{rong:.0f}px">{chu}</div>'
        rows.append(f'<div class="step">{vls}{ve_}{lbl}</div>')
    lanes = "".join(f'<div class="lane">{html.escape(t)}</div>' for t in d["lan"])
    doc = (f'<!doctype html><meta charset="utf-8"><style>{CSS}</style><div class="wrap"><h2>{html.escape(d["tieu_de"])}</h2>'
           f'<div class="lanes" style="grid-template-columns:repeat({n},1fr)">{lanes}</div>{"".join(rows)}</div>')
    OUT.mkdir(parents=True, exist_ok=True)
    f_html = OUT / f"{ma}.html"
    f_html.write_text(doc, encoding="utf-8")
    f_png = OUT / f"{ma}.png"
    cao = 170 + 92 * len(d["buoc"])
    subprocess.run([CHROME, "--headless=new", "--disable-gpu", "--hide-scrollbars", "--force-device-scale-factor=2",
                    f"--window-size=1000,{cao}", f"--screenshot={f_png}", f_html.as_uri()], check=True,
                   stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    im = Image.open(f_png).convert("RGB")
    xam = im.convert("L").point(lambda v: 0 if v > 250 else 255)
    hop = xam.getbbox()
    if hop:
        im = im.crop((0, 0, im.width, min(im.height, hop[3] + 24)))
    im.save(f_png)
    f_html.unlink()
    return f_png


if __name__ == "__main__":
    for ma, d in LUONG.items():
        print(ve(ma, d))
