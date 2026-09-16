"""Policy: quyet dinh tro ly TU LAM hay HOI NGUOI.

Day la thu bien workflow thanh agent. Khong co lop nay thi moi viec deu phai co nguoi bam nut,
va tro ly chi la mot cai form dep hon.

Nguyen tac:
  1. Marou dat policy, khong phai NaviWorld. Moi dong policy la mot cau nghiep vu doc duoc:
     "chuyen tu kho trung tam, duoi 2 tuan ban, gia von duoi 200, thi tu lam".
  2. Ngoai policy thi hoi. Khong co vung xam.
  3. Shadow mode: giai doan dau tro ly KHONG tu lam, chi noi "neu duoc phep toi da lam X".
     Nguoi doi chieu vai ngay, thay dung thi bat autonomy len. Day la cach roll out an toan.
  4. Moi lan tu lam deu ghi lai dong policy nao cho phep. Kiem toan truy nguoc duoc.
  5. Tran so luot tu lam moi ngay, va cong tat khan cap.

Tren BC that, bang nay la table "NWV Agent Policy" (design 0.3), Marou sua tren page,
khong phai sua code. O day de trong Python cho prototype.
"""
from __future__ import annotations

import copy
import os
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Callable


class Mode(str, Enum):
    AUTO = "auto"        # tro ly tu lam, bao sau
    APPROVE = "approve"  # dua the cho nguoi duyet
    BLOCK = "block"      # khong bao gio lam, ke ca nguoi bam


@dataclass
class Rule:
    code: str
    scenario: str
    action_type: str
    mode: Mode
    description: str = ""
    max_quantity: float | None = None
    max_value_vnd: float | None = None
    from_locations: tuple[str, ...] | None = None
    item_categories: tuple[str, ...] | None = None
    extra: Callable[[dict[str, Any]], bool] | None = None

    def matches(self, p: dict[str, Any]) -> tuple[bool, str]:
        if p.get("scenario") != self.scenario:
            return False, "khác scenario"
        if self.action_type != "*" and p.get("action_type") != self.action_type:
            return False, "khác action"
        if self.max_quantity is not None and float(p.get("quantity") or 0) > self.max_quantity:
            return False, f"số lượng {p.get('quantity')} vượt {self.max_quantity}"
        if self.max_value_vnd is not None and float(p.get("value_vnd") or 0) > self.max_value_vnd:
            return False, f"giá trị {float(p.get('value_vnd') or 0):,.0f} vượt {self.max_value_vnd:,.0f}"
        if self.from_locations and p.get("from_loc") not in self.from_locations:
            return False, f"nguồn {p.get('from_loc')} không nằm trong danh sách cho phép"
        if self.item_categories and p.get("item_category") not in self.item_categories:
            return False, f"nhóm hàng {p.get('item_category')} không nằm trong danh sách"
        if self.extra and not self.extra(p):
            return False, "không thoả điều kiện riêng"
        return True, self.description or self.code


@dataclass
class Decision:
    mode: Mode
    reason: str
    rule_code: str = ""
    shadow: bool = False    # true = dang o shadow mode, dang le AUTO nhung van hoi

    @property
    def is_auto(self) -> bool:
        return self.mode == Mode.AUTO and not self.shadow


# Policy mac dinh cho POC. Marou chinh cac con so nay o tuan 2.
DEFAULT_RULES: list[Rule] = [
    # Nguong gia tri tinh theo gia von cua company NWV (don vi tien cua company, gia von mot
    # mon tu 0,45 den 7,5). Tren he thong that cua Marou thi Marou dat lai con so nay.
    Rule("P-01", "StoreReplenishment", "Transfer", Mode.AUTO,
         description="Chuyển hàng từ kho trung tâm W0003, dưới 2 tuần bán, giá vốn dưới 200",
         max_value_vnd=200, from_locations=("W0003",)),
    Rule("P-02", "StoreReplenishment", "Transfer", Mode.APPROVE,
         description="Chuyển giữa các cửa hàng, hoặc giá trị lớn: cần người duyệt"),
    Rule("P-11", "StoreReplenishment", "Purchase", Mode.APPROVE,
         description="Đặt mua từ nhà cung cấp giao thẳng cửa hàng (Dakao mua từ Marou): người mua duyệt, BC tạo Purchase Order Open"),
    Rule("P-12", "StoreReplenishment", "PostReceipt", Mode.APPROVE,
         description="Post phiếu nhận hàng intercompany thay người: luôn cần người duyệt, vì đây là việc duy nhất trợ lý ghi thẳng vào sổ kho"),
    Rule("P-03", "StoreReplenishment", "Escalate", Mode.APPROVE,
         description="Kho hết hàng: báo người, trợ lý không tự xử lý được"),
    Rule("P-04", "InventoryHealth", "Markdown", Mode.APPROVE,
         description="Giảm giá ảnh hưởng doanh thu: luôn cần người duyệt"),
    Rule("P-05", "InventoryHealth", "WriteOff", Mode.APPROVE,
         description="Huỷ hàng ảnh hưởng sổ sách: luôn cần người duyệt"),
    Rule("P-06", "InventoryHealth", "Transfer", Mode.AUTO,
         description="Chuyển lô cận date sang cửa hàng bán nhanh, giá vốn dưới 100",
         max_value_vnd=100),
    Rule("P-07", "InventoryHealth", "BlockPurchase", Mode.AUTO,
         description="Chặn mua thêm hàng đang dư tồn: gỡ lại được bất kỳ lúc nào"),
    Rule("P-09", "DemandPlanning", "AdjustParameter", Mode.APPROVE,
         description="Đổi ngưỡng hoặc cách tính dự báo: luôn cần người duyệt, vì nó đổi hành vi của mọi lần sau"),
    Rule("P-10", "DemandPlanning", "Escalate", Mode.APPROVE,
         description="Vượt phạm vi kế hoạch: đưa người quyết định kèm bằng chứng"),
    Rule("P-08", "DiscountGovernance", "*", Mode.APPROVE,
         description="Mọi việc liên quan kỷ luật nhân viên đều do người kết luận"),
]


class PolicyEngine:
    def __init__(self, rules: list[Rule] | None = None, shadow: bool | None = None, daily_auto_cap: int | None = None):
        # deepcopy: moi engine giu ban rule rieng. Neu chi list() thi cac doi tuong Rule dung chung,
        # sua nguong o mot noi se lam doi nguong o moi noi khac (loi da bat duoc khi chay ca bo test).
        self.rules = copy.deepcopy(rules if rules is not None else DEFAULT_RULES)
        env_shadow = os.getenv("AGENT_SHADOW_MODE", "true").lower() in ("1", "true", "yes")
        self.shadow = env_shadow if shadow is None else shadow
        self.daily_auto_cap = int(os.getenv("AGENT_DAILY_AUTO_CAP", "20")) if daily_auto_cap is None else daily_auto_cap
        self.kill_switch = False
        self.auto_today = 0

    def decide(self, p: dict[str, Any]) -> Decision:
        if self.kill_switch:
            return Decision(Mode.APPROVE, "Công tắc khẩn cấp đang bật: mọi việc đều hỏi người", "KILL")
        misses: list[str] = []
        for r in self.rules:
            ok, why = r.matches(p)
            if not ok:
                if r.scenario == p.get("scenario"):
                    misses.append(f"{r.code}: {why}")
                continue
            if r.mode == Mode.AUTO:
                if self.shadow:
                    return Decision(Mode.AUTO, f"{why} (shadow mode: chưa tự làm, chỉ báo trước)", r.code, shadow=True)
                if self.auto_today >= self.daily_auto_cap:
                    return Decision(Mode.APPROVE, f"Đã tự làm {self.auto_today} việc hôm nay, chạm trần {self.daily_auto_cap}", r.code)
                return Decision(Mode.AUTO, why, r.code)
            return Decision(r.mode, why, r.code)
        return Decision(Mode.APPROVE, "Không dòng policy nào khớp: " + ("; ".join(misses[:2]) if misses else "chưa có policy cho việc này"), "")

    def note_auto(self) -> None:
        self.auto_today += 1

    def summary(self) -> list[dict[str, Any]]:
        return [{"code": r.code, "scenario": r.scenario, "action": r.action_type, "mode": r.mode.value,
                 "description": r.description,
                 "limit": (f"≤ {r.max_value_vnd:,.0f}" if r.max_value_vnd else "") + (f" từ {'/'.join(r.from_locations)}" if r.from_locations else "")}
                for r in self.rules]
