"""Prompt mau theo vai tro: the goi y tren man hinh chao va kich ban demo noi bo.

Vi sao co file nay (14/09/2026). Man hinh chao truoc day cho moi vai cung bon the chung chung ("Tra cuu ton kho: Toi muon
kiem tra ton kho cua ..."), nguoi dung phai tu go not mat hang va khong biet vai minh hoi duoc gi. Dung yeu cau "de xuat
cac prompt mau coi nhu la cac kich ban, tuong ung voi cac vai tro".

Nguyen tac chon cau:
  - Cau nao cung chay ra dung viec voi rule, KHONG can bat AI, tru cau danh dau `can_ai`. `tests/test_goi_y.py` gui tung
    cau cua tung nguoi dung demo vao tro ly mo phong va kiem intent, skill, khong roi vao cau tro giup.
  - Mat hang cua quan ly cua hang lay dung mon co so tren BC NWV01 ngay 14/09/2026 (MAROU-TO): S0001 Choco nuts 82,
    S0002 Ice cream 11 (min-max), S0005 Ice cream 14, S0010 Choco bowl 5 (Retail Forecast, co CTKM 23-25/09).
    S0013 (web store) khong co dong LS nao nen hoi ton va du bao Milk 1 liter.
  - `ghi_bc`: cau lam tro ly GHI vao BC (de xuat Proposed). Demo tren BC that thi biet truoc.
  - `intent` la intent RULE tra ve. Ba cau yeu cau mo (tiec 150 khach, kho mua dot, cau cho model) rule khong phan loai
    duoc, di thang sang planner: tat AI thi planner ban ghi di lai chuoi da dung san, bat AI thi model tu dung.
Bon cau dau cua moi vai la bon the lon; phan con lai hien thanh nut nho "Goi y khac".
"""
from __future__ import annotations

from typing import Any

# Mon demo theo cua hang. `ls`: mon LS dang de xuat chuyen; `mon`: mon hoi ton va du bao.
MON_CUA_HANG = {
    "S0001": {"ls": "Choco nuts", "mon": "Choco nuts"},
    "S0002": {"ls": "Ice cream", "mon": "Ice cream"},
    "S0005": {"ls": "Ice cream", "mon": "Tiramisu"},
    "S0010": {"ls": "Choco bowl", "mon": "Choco bowl"},
    "S0013": {"ls": "", "mon": "Milk 1 liter"},
}


def _g(ten: str, mo: str, cau: str, uc: str, icon: str = "hoi", can_ai: bool = False, ghi_bc: bool = False,
       intent: str = "") -> dict[str, Any]:
    return {"ten": ten, "mo": mo, "cau": cau, "uc": uc, "icon": icon, "can_ai": can_ai, "ghi_bc": ghi_bc, "intent": intent}


def cho_vai(role: str, store: str = "") -> list[dict[str, Any]]:
    m = MON_CUA_HANG.get(store, {"ls": "", "mon": ""})
    if role == "store_manager":
        ds = [
            _g("Brief sáng nay", "Mặt hàng dưới ngưỡng, đề xuất chờ duyệt, CTKM sắp tới.",
               "Tóm tắt những việc cần ưu tiên hôm nay.", "UC10", "brief", intent="BRIEF"),
            _g(f"Tồn {m['mon']} ở cửa hàng", "Tồn tại cửa hàng mình và kho trung tâm.",
               f"{m['mon']} ở cửa hàng tôi còn bao nhiêu", "UC2", "ton", intent="STOCK_QUERY"),
            _g("CTKM sắp tới", "Chương trình của LS áp cho cửa hàng mình.",
               "CTKM nào sắp tới ở cửa hàng tôi", "UC10", "km", intent="PROMO"),
            _g("Lô sắp hết hạn", "Lô quá hạn và cận hạn tại cửa hàng.",
               "cửa hàng tôi có lô nào sắp hết hạn không", "UC2", "han", intent="EXPIRY"),
        ]
        if m["ls"]:
            ds.append(_g(f"Vì sao LS đề xuất {m['ls']}", "Đọc nhật ký tính của LS Replenishment.",
                         f"vì sao LS đề xuất {m['ls']} cho {store}", "UC5", "ls", intent="REPLEN_WHY"))
        ds += [
            _g(f"Dự báo {m['mon']}", "Sai số, Holt-Winters, dự báo 7 ngày tới.",
               f"dự báo {m['mon']} ở {store} sai bao nhiêu", "UC1", "du_bao", intent="FORECAST"),
            _g("Đề xuất của tôi", "Tiến độ đề xuất và chứng từ.", "đề xuất của tôi đến đâu rồi", "UC10", "theo_doi",
               intent="TRACKING"),
            _g("Đơn mua chưa nhận", "PO về cửa hàng quá ngày nhận.", "đơn mua nào về cửa hàng tôi quá hạn chưa nhận",
               "UC3", "po", intent="PO_OVERDUE"),
        ]
        if store == "S0005":
            ds.append(_g("Tiệc 150 khách", "Yêu cầu mở nhiều ràng buộc (bản ghi đã duyệt).",
                         "thứ Bảy này nhà hàng nhận tiệc 150 khách, mỗi khách một phần tráng miệng, ngân sách 600, trời nóng "
                         "nên tránh kem, kho còn gì ghép được không", "UC10", "mo", intent="HELP"))
        return ds
    if role == "dispatcher":
        return [
            _g("Brief điều phối", "Ghi đề xuất chuyển hàng theo số LS, thẻ để duyệt.", "Tóm tắt những việc cần ưu tiên hôm nay.",
               "UC5", "brief", ghi_bc=True, intent="BRIEF"),
            _g("Hàng đã hết hạn", "Lô quá hạn theo địa điểm, đề xuất hủy có số lô.", "có mặt hàng nào đã hết hạn chưa",
               "UC2", "han", intent="EXPIRY"),
            _g("Truy xuất lô", "Lô đi đâu, còn ở đâu, thu hồi chỗ nào.", "truy xuất lô L260908-33170B", "UC2", "lo",
               intent="TRACE"),
            _g("CTKM sắp tới", "Và cửa hàng LS chưa cộng nhu cầu khuyến mãi.", "CTKM nào sắp tới", "UC10", "km",
               intent="PROMO"),
            _g("Vì sao LS đề xuất Ice cream", "Hàng min-max, kho không đủ nên LS chia lại.",
               "vì sao LS đề xuất Ice cream cho S0002", "UC5", "ls", intent="REPLEN_WHY"),
            _g("Tồn Choco nuts các nơi", "Tồn theo địa điểm và theo lô.", "Choco nuts còn bao nhiêu", "UC2", "ton",
               intent="STOCK_QUERY"),
            _g("Tiến độ đề xuất", "Đề xuất đang chờ, đã duyệt, chứng từ.", "tiến độ các đề xuất", "UC10", "theo_doi",
               intent="TRACKING"),
        ]
    if role == "warehouse":
        return [
            _g("Brief kho", "Đơn chờ ship hôm nay.", "Tóm tắt những việc cần ưu tiên hôm nay.", "UC10", "brief",
               intent="BRIEF"),
            _g("Lô trong kho sắp hết hạn", "Lô quá hạn và cận hạn tại W0003.", "kho có lô nào sắp hết hạn không", "UC2", "han",
               intent="EXPIRY"),
            _g("Hàng mua chưa về", "PO về kho quá ngày nhận.", "đơn mua nào về kho quá hạn chưa nhận", "UC3", "po",
               intent="PO_OVERDUE"),
            _g("Tồn Flavored syrup", "Tồn theo địa điểm.", "Flavored syrup còn bao nhiêu", "UC2", "ton", intent="STOCK_QUERY"),
            _g("Truy xuất lô", "Lô đi đâu, còn ở đâu.", "truy xuất lô L260908-33170B", "UC2", "lo", intent="TRACE"),
            _g("Kho bị mưa dột", "Sự cố không có mẫu (bản ghi đã duyệt).",
               "góc kho bị mưa dột, mấy thùng Flavored syrup ướt nhãn chưa đếm được, giờ xử lý sao", "UC10", "mo",
               intent="INVESTIGATE"),
        ]
    if role == "supply_chain":
        return [
            _g("Dự báo đang sai ở đâu", "WAPE ba phương pháp, cặp vượt ngưỡng.", "độ chính xác dự báo thế nào", "UC1", "du_bao",
               intent="FORECAST"),
            _g("Vì sao LS đề xuất 82 Choco nuts", "Average Usage đọc từ nhật ký tính LS.",
               "vì sao LS đề xuất Choco nuts cho S0001", "UC5", "ls", intent="REPLEN_WHY"),
            _g("Nhà cung cấp hay giao trễ", "Scorecard đúng hạn, lead time.", "nhà cung cấp nào hay giao trễ", "UC3", "ncc",
               intent="SUPPLIER"),
            _g("CTKM đang chạy và sắp tới", "Kèm cặp chưa có nhu cầu trong LS.", "CTKM nào đang chạy và sắp tới", "UC10", "km",
               intent="PROMO"),
            _g("Dự báo Choco bowl tại S0010", "Holt-Winters, dự báo ghi vào LS, sự kiện.",
               "dự báo Choco bowl ở S0010 sai bao nhiêu", "UC1", "du_bao", intent="FORECAST"),
            _g("Vì sao LS đề xuất Choco bowl", "Retail Forecast cộng khuyến mãi 23-25/09.",
               "vì sao LS đề xuất Choco bowl cho S0010", "UC5", "ls", intent="REPLEN_WHY"),
            _g("PO quá hạn", "Đơn mua chưa nhận, hỏi người nhận hàng.", "PO nào quá hạn chưa nhận", "UC3", "po",
               intent="PO_OVERDUE"),
            _g("Brief Supply Chain", "Lô xấu cần xử lý, đơn quá hạn.", "Tóm tắt những việc cần ưu tiên hôm nay.", "UC2",
               "brief", intent="BRIEF"),
            _g("Cửa hàng Quận 1 lại hết hàng", "Bậc thang chẩn đoán khi đứt hàng lặp lại.",
               "sao Cửa hàng Quận 1 cứ hết Chocolate ice cream", "UC5", "mo", intent="INVESTIGATE"),
            _g("Câu hỏi mở cho model", "Planner tự chọn tra gì, cần bật AI.",
               "so sánh tốc độ bán Flavored syrup giữa các cửa hàng 30 ngày qua, chỗ nào nên giữ ít hàng lại", "UC10", "mo",
               can_ai=True, intent="HELP"),
        ]
    if role == "retail_ops":
        return [
            _g("Brief Retail Ops", "Ngoại lệ chiết khấu POS cần giải trình.", "Tóm tắt những việc cần ưu tiên hôm nay.", "UC7",
               "brief", intent="BRIEF"),
            _g("CTKM đang chạy và sắp tới", "Chương trình LS theo cửa hàng.", "CTKM nào đang chạy và sắp tới", "UC10", "km",
               intent="PROMO"),
            _g("Croissant có giảm giá không", "CTKM theo mặt hàng, giờ áp dụng.", "croissant có giảm giá không", "UC10", "km",
               intent="PROMO"),
            _g("CTKM đã kết thúc", "Chương trình vừa qua.", "CTKM đã kết thúc", "UC10", "km", intent="PROMO"),
            _g("Dự báo ở Nhà hàng Thảo Điền", "Sai số dự báo theo cửa hàng.", "độ chính xác dự báo ở S0005", "UC1", "du_bao",
               intent="FORECAST"),
        ]
    if role == "admin":
        return [
            _g("Tiến độ đề xuất", "Mọi đề xuất trong BC.", "tiến độ các đề xuất", "UC10", "theo_doi", intent="TRACKING"),
            _g("Trợ lý tự chấm điểm", "Xem lại việc đã làm có đúng không.", "tự chấm điểm lại việc đã làm", "UC10", "brief",
               intent="SELF_REVIEW"),
            _g("CTKM đang chạy và sắp tới", "Và cặp chưa có nhu cầu trong LS.", "CTKM nào đang chạy và sắp tới", "UC10", "km",
               intent="PROMO"),
            _g("Câu hỏi mở cho model", "Planner tự dựng chuỗi tra cứu, cần bật AI.",
               "so sánh tốc độ bán Flavored syrup giữa các cửa hàng 30 ngày qua, chỗ nào nên giữ ít hàng lại", "UC10", "mo",
               can_ai=True, intent="HELP"),
            _g("Câu ngoài bản ghi", "Thấy ranh giới rule và model.",
               "tháng sau mình mở thêm cửa hàng ở Nha Trang thì nên đẩy bao nhiêu hàng ban đầu", "UC10", "mo", can_ai=True,
               intent="STOCK_QUERY"),
        ]
    return []


def cho_nguoi_dung(user: dict[str, Any] | None) -> list[dict[str, Any]]:
    if not user:
        return []
    return cho_vai(user.get("role", ""), user.get("store_code") or "")
