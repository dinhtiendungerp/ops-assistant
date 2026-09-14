"""Hieu tin nhan cua nguoi dung.

Hai backend:
  - RuleNLU   : rule tieng Viet + fuzzy item. Khong can API key. Du cho demo cac cau ngan trong van hanh cua hang.
  - LiveNLU   : model (Azure OpenAI hoac Claude) voi output JSON theo schema, fallback ve RuleNLU neu loi.

Intent:
  STOCKOUT      "sap het / het / thieu / con it ..."   -> skill replenishment
  STOCK_QUERY   "con bao nhieu / ton ... "              -> tra loi ton theo location
  DAMAGE        "hong / vo / khach tra ..."             -> ghi nhan, hoi xac nhan (POC: chi ghi)
  ANSWER        tra loi cau hoi tro ly dang cho (giai trinh)
  BRIEF         "brief / hom nay co gi"
  TRACKING      "viec cua toi den dau roi / tien do de xuat"  -> doc lai tu bang de xuat, khong goi model
  REPLEN_WHY    "vi sao LS de xuat 82 Choco nuts o S0001" -> doc journal va nhat ky tinh cua LS
  PO_OVERDUE    "PO nao qua han / don mua chua nhan / hang mua chua ve" -> UC3, doc dong don mua, khong goi model
  EXPIRY        "lo nao het han / sap het han / can date"  -> doc bang Inventory Health, khong goi model
  FORECAST      "do chinh xac du bao / du bao X sai bao nhieu"  -> UC1, doc forecastAccuracies
  SUPPLIER      "nha cung cap nao hay giao tre / scorecard"     -> UC3, doc supplierScorecards
  TRACE         "truy xuat lo L260908-33170B"                    -> UC2, doc Item Ledger Entry cua lo
  PROMO         "CTKM nao dang chay / sap toi"                   -> doc LSC Periodic Discount va Planned Event cua LS
  INVESTIGATE   "sao ... cu het hang", "vi sao", "tai sao"  -> agent tu di nhieu buoc tra loi
  SELF_REVIEW   "tu cham diem", "review lai", "lam co dung khong"
  HELP          con lai
"""
from __future__ import annotations

import json
import logging
import re
from dataclasses import dataclass, field
from typing import Any

from bc_agent.config import settings

log = logging.getLogger(__name__)

INTENT_SCHEMA = {
    "type": "object",
    "properties": {
        "intent": {"type": "string", "enum": ["STOCKOUT", "STOCK_QUERY", "DAMAGE", "ANSWER", "BRIEF", "TRACKING", "PO_OVERDUE", "EXPIRY", "FORECAST", "SUPPLIER", "TRACE", "PROMO", "REPLEN_WHY", "INVESTIGATE", "SELF_REVIEW", "PLAN", "HELP"]},
        "item_text": {"type": "string", "description": "cum chu chi mat hang, rong neu khong co"},
        "quantity": {"type": "number", "description": "so luong nguoi noi, 0 neu khong co"},
        "store_hint": {"type": "string", "description": "ten cua hang neu nguoi noi nhac den, rong neu khong"},
    },
    "required": ["intent", "item_text", "quantity", "store_hint"],
    "additionalProperties": False,
}


@dataclass
class Intent:
    intent: str
    item_text: str = ""
    quantity: float = 0
    store_hint: str = ""
    raw: dict[str, Any] = field(default_factory=dict)


_STOCKOUT = re.compile(r"(sắp hết|sap het|hết hàng|het hang|\bhết\b|\bhet\b|thiếu|thieu|còn ít|con it|cần thêm|can them|bổ sung|bo sung)", re.I)
_QUERY = re.compile(r"(còn bao nhiêu|con bao nhieu|tồn|ton kho|bao nhiêu|bao nhieu|ở đâu|o dau)", re.I)
_DAMAGE = re.compile(r"(hỏng|hong|vỡ|vo\b|trả lại|tra lai|khách trả|khach tra|lỗi|loi\b|cận date|can date)", re.I)
# Nguoi ta khong go moi chu "brief". The goi y tren man hinh chao dien san mot cau day du,
# va nguoi dung cung go kieu "viec can uu tien hom nay la gi".
_BRIEF = re.compile(r"(brief|hôm nay có gì|hom nay co gi|tổng hợp|tong hop|tóm tắt|tom tat|"
                    r"việc cần ưu tiên|viec can uu tien|cần ưu tiên|can uu tien|"
                    r"việc sáng nay|viec sang nay|việc hôm nay|viec hom nay)", re.I)
# Hoi ve viec dang chay cua chinh minh. Tra loi duoc bang bang de xuat da co, khong can model.
_TRACKING = re.compile(r"(tiến độ|tien do|đang theo dõi|dang theo doi|theo dõi xử lý|theo doi xu ly|"
                       r"đến đâu rồi|den dau roi|tới đâu rồi|toi dau roi|đề xuất của tôi|de xuat cua toi|"
                       r"đề xuất nào|de xuat nao|chứng từ|chung tu|tình trạng|tinh trang)", re.I)
# UC3: don mua qua ngay nhan du kien ma chua nhan. Dat truoc BRIEF va TRACKING vi "tong hop PO qua han"
# va "chung tu mua chua nhan" deu trung tu khoa cua hai nhom do.
_PO_QUA_HAN = re.compile(r"(\bpo\b|purchase order|đơn mua|don mua|đơn đặt hàng|don dat hang|hàng mua|hang mua)"
                         r".*(quá hạn|qua han|trễ|\btre\b|chưa nhận|chua nhan|chưa về|chua ve|chưa nhập|chua nhap|"
                         r"chưa post|chua post|chưa receive|chua receive)|"
                         r"(chưa nhận hàng|chua nhan hang|chưa post nhận|chua post nhan|quá hạn nhận|qua han nhan)", re.I)
# Hoi vi sao LS / de xuat bo sung ra con so. Dat truoc INVESTIGATE (cua hang cu het hang) vi cung tu "vi sao".
_REPLEN_WHY = re.compile(r"(vì sao|vi sao|tại sao|tai sao|giải thích|giai thich|\bsao\b).*(đề xuất|de xuat|\bls\b|replenishment|số lượng|so luong)", re.I)
# Tu cua cau hoi LS, bo khoi item_text truoc khi tra ten mat hang.
_LS_BO = re.compile(r"(đề xuất|de xuat|\bls\b|replenishment|số lượng|so luong|giải thích|giai thich|\bra\b|\bsố\b|\bnày\b|\bnay\b|\b\d+\b)", re.I)
# UC3 scorecard nha cung cap. Dat sau PO_OVERDUE: "PO nao tre" la don cu the, "nha cung cap nao hay giao tre" la scorecard.
_NCC = re.compile(r"(nhà cung cấp|nha cung cap|\bncc\b|vendor|supplier|scorecard|giao trễ|giao tre|lead ?time|giao đúng hạn|"
                  r"giao dung han)", re.I)
# UC2 truy xuat lo. Co ma lo trong cau la du.
_TRUY_XUAT = re.compile(r"(truy xuất|truy xuat|trace|hành trình lô|hanh trinh lo|thu hồi lô|thu hoi lo|lô này đi đâu|lo nay di dau)", re.I)
_MA_LO = re.compile(r"\bL\d{6}-[A-Z0-9-]+\b", re.I)
# UC1 do chinh xac du bao.
_DU_BAO = re.compile(r"(dự báo|du bao|forecast|wape|độ chính xác|do chinh xac)", re.I)
_DU_BAO_BO = re.compile(r"\b(sai|lệch|lech|bao nhiêu|nhiêu|thế nào|the nao|ra sao|nhóm|nhom|mặt hàng|cặp|cap|nào|nao|có|co|"
                        r"của|cua|đúng|dung|không|khong|tốt|tot|hàng|hang)\b", re.I)
# Chuong trinh khuyen mai cua LS (Periodic Discount). "chiet khau" khong nam day: do la exception chiet khau POS (UC7).
_KHUYEN_MAI = re.compile(r"(khuyến mãi|khuyen mai|khuyến mại|\bctkm\b|\bkm\b|chương trình giảm giá|chuong trinh giam gia|"
                         r"giảm giá|giam gia|ưu đãi|uu dai|promotion|\bpromo\b|periodic discount|mix ?& ?match|multibuy|"
                         r"đồng giá|dong gia|mua \d+ tặng|mua \d+ tang)", re.I)
_KHUYEN_MAI_BO = re.compile(r"(khuyến mãi|khuyen mai|khuyến mại|khuyến|khuyen|tổng hợp|tong hop|liệt kê|liet ke|tháng này|thang nay|tuần này|tuan nay|tháng|thang|\bctkm\b|\bkm\b|chương trình|chuong trinh|giảm giá|giam gia|ưu đãi|"
                            r"uu dai|promotion|\bpromo\b|sắp tới|sap toi|sắp diễn ra|sap dien ra|sắp chạy|sap chay|tuần tới|tuan toi|"
                            r"tuần sau|tuan sau|tháng tới|thang toi|đang chạy|dang chay|hiện có|hien co|hiện tại|hien tai|đã kết thúc|"
                            r"da ket thuc|vừa qua|vua qua|áp dụng|ap dung|diễn ra|dien ra|\bnào\b|\bnao\b|\bcó\b|\bco\b|\bgì\b|\bgi\b|"
                            r"\bnhững\b|\bnhung\b|\bcác\b|\bcac\b|\bko\b|\bkhông\b|\bchạy\b|\bchay\b|\bđang\b|\bnhé\b|\bnày\b|\bnay\b|"
                            r"\bmón\b|\bmon\b|mặt hàng|mat hang|\bhàng\b|\bhang\b|\bsắp\b|\bsap\b|\bra sao\b|\bthế nào\b)", re.I)
# Lo het han / sap het han. Dat truoc WHY va STOCKOUT: "het" trong "het han" khong phai het hang.
_HET_HAN = re.compile(r"(hết hạn|het han|quá hạn sử dụng|qua han su dung|quá date|qua date|hết date|het date|cận date|can date|"
                      r"cận hạn|can han|hạn dùng|han dung|hạn sử dụng|han su dung|expired|expiry)", re.I)
# Tu con sot lai sau khi _STOPWORDS da cat "het": khong phai ten mat hang.
_HET_HAN_BO = re.compile(r"\b(sắp|sap|đã|da|gần|gan|chưa|chua|nào|nao|có|co|lô|lo|hàng|hang|hạn|han|date|sử dụng|su dung|dùng|dung)\b", re.I)
_WHY = re.compile(r"(vì sao|vi sao|tại sao|tai sao|\bsao\b|lý do|ly do|nguyên nhân|nguyen nhan)", re.I)
_REVIEW = re.compile(r"(tự chấm|tu cham|chấm lại|cham lai|review|đánh giá lại|danh gia lai|làm có đúng|lam co dung)", re.I)
_QTY = re.compile(r"(\d+)\s*(cái|cai|hộp|hop|thanh|pcs|chiếc|chiec|thùng|thung)\b", re.I)
_STOPWORDS = re.compile(r"(sắp hết|sap het|hết hàng|het hang|hết|het|thiếu|thieu|còn ít|con it|cần thêm|can them|bổ sung|bo sung|còn bao nhiêu|con bao nhieu|bao nhiêu|bao nhieu|tồn|ton kho|ở đâu|o dau|hỏng|hong|khách trả|khach tra|trả lại|tra lai|\brồi\b|\broi\b|\bnha\b|\bnhé\b|\bnhe\b|\bạ\b|\bem\b|\banh\b|\bchị\b|\bchi\b|\bơi\b|\boi\b|\bcho\b|\bở\b|\btại\b|\btai\b|cửa hàng|cua hang|\bstore\b|vì sao|vi sao|tại sao|tai sao|\bsao\b|\bcứ\b|\bcu\b|\bhay\b|\bmãi\b|\bmai\b)", re.I)


# Ma dia diem go trong cau, ke ca go thieu so 0 ("S001" la S0001). Bo khoi item_text va dua vao store_hint.
# Ngay 14/09/2026 Dung go "kiem tra ton kho cua choco cake cua S001": ma cua hang nam trong item_text lam
# find_item rot duoi nguong, cau roi xuong planner va bi tu choi.
_MA_DIA_DIEM = re.compile(r"\b([SsWw])0*(\d{1,4})\b")
# Tu dem cua cau hoi, khong phai ten mat hang.
_TU_DEM = re.compile(r"\b(tôi|toi|mình|minh|muốn|muon|kiểm tra|kiem tra|xem|giúp|giup|của|cua|kho|số lượng|so luong|"
                     r"mặt hàng|mat hang|bạn|với|voi|được|duoc|không|khong|là|la|đang|dang|hiện|hien|nay|hôm nay|hom nay)\b", re.I)


def ma_dia_diem(text: str) -> str:
    """Ma dia diem dau tien trong cau, chuan hoa bon chu so. '' neu khong co."""
    m = _MA_DIA_DIEM.search(text or "")
    return f"{m.group(1).upper()}{int(m.group(2)):04d}" if m else ""


class RuleNLU:
    def parse(self, text: str, has_pending_question: bool = False) -> Intent:
        t = text.strip()
        if has_pending_question and not (_STOCKOUT.search(t) or _QUERY.search(t)):
            return Intent("ANSWER", raw={"text": t})
        qty = 0.0
        m = _QTY.search(t)
        if m:
            qty = float(m.group(1))
        store_hint = ma_dia_diem(t)
        item_text = _STOPWORDS.sub(" ", _QTY.sub(" ", _MA_DIA_DIEM.sub(" ", t)))
        item_text = _TU_DEM.sub(" ", item_text)
        item_text = re.sub(r"\s+", " ", item_text).strip(" ,.!?")
        if _REVIEW.search(t):
            return Intent("SELF_REVIEW")
        if _PO_QUA_HAN.search(t):
            return Intent("PO_OVERDUE")
        if _NCC.search(t):
            return Intent("SUPPLIER", item_text, qty, store_hint)
        # Truoc BRIEF: "tong hop CTKM" la hoi khuyen mai. Sau vi sao LS va du bao: hai loai cau do co the nhac khuyen mai.
        if _KHUYEN_MAI.search(t) and not _REPLEN_WHY.search(t) and not _DU_BAO.search(t):
            return Intent("PROMO", re.sub(r"\s+", " ", _KHUYEN_MAI_BO.sub(" ", item_text)).strip(" ,.!?"), qty, store_hint)
        if _BRIEF.search(t):
            return Intent("BRIEF")
        if _TRUY_XUAT.search(t) or _MA_LO.search(t):
            return Intent("TRACE", item_text, qty, store_hint)
        if _TRACKING.search(t):
            return Intent("TRACKING")
        if _REPLEN_WHY.search(t):
            return Intent("REPLEN_WHY", _LS_BO.sub(" ", item_text).strip(), qty)
        if _DU_BAO.search(t):
            return Intent("FORECAST", _DU_BAO_BO.sub(" ", _DU_BAO.sub(" ", item_text)).strip(), qty, store_hint)
        if _HET_HAN.search(t) and not _PO_QUA_HAN.search(t):
            return Intent("EXPIRY", _HET_HAN_BO.sub(" ", _HET_HAN.sub(" ", item_text)).strip(), qty, store_hint)
        if _WHY.search(t):
            return Intent("INVESTIGATE", item_text, qty, store_hint)
        if _STOCKOUT.search(t):
            return Intent("STOCKOUT", item_text, qty, store_hint)
        if _QUERY.search(t):
            return Intent("STOCK_QUERY", item_text, qty, store_hint)
        if _DAMAGE.search(t):
            return Intent("DAMAGE", item_text, qty)
        return Intent("HELP", item_text, qty)


class LiveNLU:
    """Phan loai bang model, NHUNG chi khi rule khong tu chac.

    Rule chay truoc va khong ton gi. Truoc day moi tin deu di qua model, ke ca "brief" hay
    "sap het Croissant plain" la nhung cau rule doc duoc chac chan. Xem `assistant/dinh_tuyen.py`
    de biet the nao la chac. `gw` de tra ma mat hang; khong co thi bo qua buoc kiem do."""

    def __init__(self, budget=None, gw=None):
        from bc_agent.llm import build_llm

        from .dinh_tuyen import SoDinhTuyen

        self.llm = build_llm(fast=True)   # phan loai tin ngan: model nhanh la du
        self.model = self.llm.model
        self.fallback = RuleNLU()
        self.budget = budget
        self.gw = gw
        self.so = SoDinhTuyen()

    def parse(self, text: str, has_pending_question: bool = False) -> Intent:
        # Het tran ngan sach thi ve rule, demo van chay
        if self.budget is not None and not self.budget.allow():
            self.so.ghi(False, "AI đang tắt hoặc chạm trần")
            return self.fallback.parse(text, has_pending_question)

        from .dinh_tuyen import rule_du_chac

        thu = self.fallback.parse(text, has_pending_question)
        chac, ly_do = rule_du_chac(thu, self.gw)
        if chac:
            self.so.ghi(False, ly_do)
            log.info("dinh tuyen: tra loi bang du lieu (%s)", ly_do)
            return thu
        self.so.ghi(True, ly_do)
        # Truoc 13/09/2026 prompt khong ta tung intent va enum khong co PLAN, nen cau mo co nhac
        # ten mat hang ("so sanh toc do ban Choco nuts giua cac cua hang, noi nao ban cham ma dang
        # giu nhieu") bi ep vao STOCK_QUERY: tro ly tra mot dong ton kho, planner khong bao gio chay.
        system = ("Ban phan loai tin nhan cua nhan vien cua hang chocolate gui cho tro ly van hanh. Tra ve JSON theo schema.\n"
                  "STOCKOUT: bao sap het, can them hang cho cua hang.\n"
                  "STOCK_QUERY: CHI hoi con bao nhieu mot mat hang, o dau. Khong so sanh, khong phan tich.\n"
                  "DAMAGE: bao hang hong, vo, khach tra.\n"
                  "BRIEF: xin tong hop viec hom nay. TRACKING: hoi tien do de xuat, chung tu cua minh.\n"
                  "PO_OVERDUE: hoi don mua (PO) qua ngay nhan, chua nhan, hang mua chua ve.\n"
                  "EXPIRY: hoi lo hang da het han, sap het han, can date.\n"
                  "FORECAST: hoi do chinh xac du bao, du bao lech bao nhieu, WAPE.\n"
                  "SUPPLIER: hoi nha cung cap giao dung han hay tre, lead time, scorecard nha cung cap.\n"
                  "PROMO: hoi chuong trinh khuyen mai, giam gia, uu dai cua LS dang chay, sap toi hoac da ket thuc.\n"
                  "TRACE: truy xuat mot lo hang (co so lo dang L260908-...), lo da di dau, thu hoi.\n"
                  "REPLEN_WHY: hoi vi sao LS Replenishment / de xuat bo sung ra so luong do cho mot mat hang.\n"
                  "INVESTIGATE: hoi vi sao mot cua hang cu het mot mat hang.\n"
                  "SELF_REVIEW: bao tro ly tu cham diem viec da lam.\n"
                  "PLAN: yeu cau mo can tu tra nhieu bang roi ket luan: so sanh, xep hang, phan tich, lap ke hoach, "
                  "cau co rang buoc (so khach, ngan sach, ngay, dieu kien), su co khong co mau.\n"
                  "ANSWER: chi khi tro ly dang cho cau tra loi va tin nay la cau tra loi.\n"
                  "HELP: chao hoi, cau khong lien quan van hanh.\n"
                  "Phan van giua STOCK_QUERY va PLAN thi chon PLAN.\n"
                  f"Tro ly dang cho cau tra loi: {'co' if has_pending_question else 'khong'}.")
        try:
            resp = self.llm.text(system, text, max_tokens=512, schema=INTENT_SCHEMA)
            if self.budget is not None:
                self.budget.track("nlu", self.model, resp.usage)
            if resp.stop_reason == "refusal":
                return self.fallback.parse(text, has_pending_question)
            from bc_agent.llm import text_of
            data = json.loads(text_of(resp))
            return Intent(data["intent"], data.get("item_text", ""), float(data.get("quantity") or 0), data.get("store_hint", ""), data)
        except Exception:
            return self.fallback.parse(text, has_pending_question)


def build_nlu(budget=None, live: bool | None = None, gw=None) -> RuleNLU | LiveNLU:
    if live is None:
        live = settings.llm_mode == "live"
    return LiveNLU(budget=budget, gw=gw) if live else RuleNLU()
