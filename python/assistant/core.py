"""Assistant: noi cac skill lai, giu bo nho, chay theo doi. Channel layer goi ba ham:
  handle_message(user_id, text)         -> list[Delivery]
  handle_action(user_id, verb, ref, payload) -> list[Delivery]
  run_followups()                        -> list[Delivery]   (scheduler goi dinh ky)
  morning_brief(user_id)                 -> list[Delivery]
"""
from __future__ import annotations

import logging
import os
import re
import uuid
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

from bc_agent.config import settings

from .budget import Budget
from .gateway import BCGateway
from . import caidat
from .memory import Memory
from .policy import PolicyEngine
from .nlu import Intent, RuleNLU, build_nlu
from .planner import build_planner
from .skills import (Delivery, demand, discount, evidence, inventory_health, investigate, ladder,
                     plan, po_qua_han, ls_giai_thich, replenishment, review, tracking)
from .skills import du_bao, khuyen_mai, nha_cung_cap, truy_xuat

log = logging.getLogger(__name__)

# Dia diem cua company NWV trong bo du lieu demo. Ten tieng Viet ngan de nguoi go tin nhan
# nhac den cua hang bang loi thay vi bang ma: "sao Cửa hàng Quận 1 cứ hết ..." khop S0001.
CENTRAL_WH = "W0003"
# Ten goi bang loi cua tung dia diem, de nguoi go tin nhan nhac den cua hang bang ten thay vi
# bang ma. Day la nhan hien thi cua tro ly; tren BC ten Location van la ten cua Cronus cho den
# khi doi master data.
STORE_LABEL = {
    "S0001": "Cửa hàng Quận 1",
    "S0002": "Cửa hàng Hà Nội",
    "S0005": "Nhà hàng Thảo Điền",
    "S0010": "Quán cà phê Đà Nẵng",
    "S0013": "Cửa hàng trực tuyến",
    "W0003": "Kho trung tâm",
}

DEMO_USERS = [
    {"user_id": "lan.s0001", "display_name": "Lan (QL Cửa hàng Quận 1, S0001)", "role": "store_manager", "store_code": "S0001", "bc_user": "LAN"},
    {"user_id": "minh.s0002", "display_name": "Minh (QL Cửa hàng Hà Nội, S0002)", "role": "store_manager", "store_code": "S0002", "bc_user": "MINH"},
    {"user_id": "tuan.s0005", "display_name": "Tuấn (QL Nhà hàng Thảo Điền, S0005)", "role": "store_manager", "store_code": "S0005", "bc_user": "TUAN"},
    {"user_id": "ha.s0010", "display_name": "Hà (QL Quán cà phê Đà Nẵng, S0010)", "role": "store_manager", "store_code": "S0010", "bc_user": "HA"},
    {"user_id": "thao.s0013", "display_name": "Thảo (QL Cửa hàng trực tuyến, S0013)", "role": "store_manager", "store_code": "S0013", "bc_user": "THAO"},
    {"user_id": "hung.dieuphoi", "display_name": "Hùng (Điều phối kho)", "role": "dispatcher", "bc_user": "HUNG"},
    {"user_id": "kho.w0003", "display_name": "Kho trung tâm W0003", "role": "warehouse", "store_code": "W0003", "bc_user": "KHOW0003"},
    {"user_id": "trang.sc", "display_name": "Trang (Supply Chain)", "role": "supply_chain", "bc_user": "TRANG"},
    {"user_id": "thu.retailops", "display_name": "Thư (Retail Ops)", "role": "retail_ops", "bc_user": "THU"},
    {"user_id": "dung.admin", "display_name": "Dũng (Quản trị hệ thống)", "role": "admin", "bc_user": "DUNG"},
]

# Chi vai tro nay mo duoc trang Cai dat AI: bat tat model, doi tran chi phi, sua policy.
# Tren ban demo nay nguoi dung tu chon minh la ai tu danh sach ben trai, nen day la ranh gioi
# vai tro chu chua phai xac thuc. Tren he thong that no gan vao danh tinh Entra va permission
# set cua BC, giong het cach nut Duyet dang lam.
ADMIN_ROLES = ("admin",)


def la_quan_tri(user: dict[str, Any] | None) -> bool:
    return bool(user) and user.get("role") in ADMIN_ROLES

# Nhan tieng Viet cho tung nut tren the. Log ky thuat ([verb] ref payload) van nam trong runs/<run_id>.jsonl,
# khong day ra man hinh nguoi dung.
ACTION_LABELS = {
    "approve": "Duyệt đề xuất", "edit": "Sửa số lượng", "reject": "Từ chối đề xuất",
    "undo": "Hoàn tác", "ship": "Đã ship", "ack": "Đã nhận",
    "ask_explanation": "Hỏi giải trình", "confirm_exception": "Kết luận là có vi phạm",
    "dismiss_exception": "Bỏ qua exception", "inv_steps": "Xem tôi đã tra gì",
    "inv_apply": "Áp dụng đề xuất từ điều tra", "review_detail": "Xem chi tiết chấm điểm",
    "ih_propose": "Đề xuất xử lý tồn", "ih_transfer_fast": "Phương án cho lô cận date", "ih_d4_apply": "Ghi đề xuất theo phương án",
    "plan_steps": "Xem tôi đã tra gì", "plan_apply": "Ghi đề xuất vào BC",
    "plan_ok": "Trả lời đúng", "plan_bad": "Chưa đúng", "plan_model": "Hỏi lại bằng model",
    "lad_approve": "Duyệt việc đổi ngưỡng", "lad_reject": "Từ chối", "lad_evidence": "Giải thích cho trợ lý",
    "demand_show": "Xem bảng nhu cầu",
    "ls_vi_sao": "Vì sao LS ra số này",
    "po_da_ve": "Hàng đã về, chưa nhập", "po_chua_ve": "Hàng chưa về",
    "po_qua_han": "Xem đơn quá hạn",
}


def action_text(verb: str, payload: dict[str, Any]) -> str:
    label = ACTION_LABELS.get(verb, verb)
    # "edit" la duyet kem so da sua, khong phai mot hanh dong rieng: tren giao dien nguoi duyet
    # chi thay mot nut Duyet, ho sua so trong o roi bam.
    if verb == "edit" and payload.get("quantity"):
        return f"Duyệt, sửa số lượng thành {payload['quantity']}"
    if verb == "reject" and payload.get("reason"):
        return f"{label}: {payload['reason']}"
    return label


# Cau nay gio sua duoc tren trang Cai dat, ban goc nam trong `caidat.CAU_MAU_GOC`.
HELP = caidat.CAU_MAU_GOC["tro_giup"]["text"]


class Assistant:
    def __init__(self, client: Any, memory: Memory | None = None, users: list[dict[str, Any]] | None = None,
                 cong_ty: str = ""):
        # Company ma tro ly nay phuc vu (assistant/cong_ty.py). Rong la che do mot company nhu truoc 15/09/2026.
        self.cong_ty = cong_ty or getattr(getattr(client, "s", None), "bc_company_name", "") or ""
        self.gw = BCGateway(client, central_wh=CENTRAL_WH)
        self.mem = memory or Memory(":memory:")
        self.mem.upsert_users(users or DEMO_USERS)
        # So chi phi nam rieng mot file tren dia, xem `budget.so_chi_phi`. Khong gan vao
        # `self.mem` vi bo nho tro ly la `:memory:` va bi dung moi lan doi nguon du lieu.
        self.budget = Budget()
        self.policy = PolicyEngine()
        # Nguoi quan tri sua tran chi phi, nguong policy va cau chu tren trang Cai dat. Ap o day,
        # sau khi Budget va PolicyEngine da dung xong, truoc khi tro ly kip lam gi.
        caidat.ap_vao(self.budget, self.policy)
        cong_tac = caidat.doc().get("ai_bat")
        self.agent_bc_user = os.getenv("AGENT_BC_USER", "NWV-AGENT")
        self.ai_live = settings.llm_mode == "live" if cong_tac is None else bool(cong_tac)
        self.budget.ai_off = not self.ai_live
        self._dung_ai()
        self.run_id = f"asst-{datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')}-{uuid.uuid4().hex[:6]}"
        # Chot baseline NGAY luc khoi tao, truoc khi tro ly kip lam gi. Neu tinh sau thi
        # chinh viec tro ly da lam da lam thay doi hien trang, va bao cao se tu khen minh.
        from .skills import kpi as _kpi
        try:
            _kpi.baseline(self)
        except OSError as exc:
            # Fixtures bi khoa (OneDrive dong bo, uvicorn --reload trung thoi diem ghi file).
            # Khong duoc lam chet ca app vi mot lan doc file hong: bo qua, lan goi baseline
            # sau se tinh lai. Chi mat tinh "chot truoc khi tro ly kip lam gi" neu nguoi dung
            # kip thao tac trong vai giay dau, chap nhan duoc.
            log.warning("Chua chot duoc baseline luc khoi tao: %s", exc)

    def _dung_ai(self) -> None:
        live = self.ai_live
        self.nlu = build_nlu(self.budget, live=live, gw=self.gw)
        self.planner = build_planner(self.budget, live=live)
        self.ev = evidence.build(self.budget, live=live)
        self._writer = None
        if live:
            from bc_agent.llm import build_llm
            self._writer = build_llm()
        self.model_name = f"{settings.llm_provider}:{settings.live_model_name}" if live else "scripted"

    def set_ai(self, on: bool) -> None:
        """Bat tat AI ngay luc dang chay. Tat thi tro ly tra loi bang rule va template,
        khong goi model lan nao; bat lai thi dung lai LiveNLU, LivePlanner va nguoi viet cau.

        Hai thu khac nhau, dung gop: `ai_live` la co con duong den model hay khong;
        `budget.ai_off` la cong tac chan moi lan goi. Bat AI thi mo ca hai."""
        self.budget.ai_off = not on
        if on == self.ai_live:
            return
        self.ai_live = on
        self._dung_ai()

    # ---------- viet cau (rationale, tom tat). Scripted: dung nguyen template; live: model viet lai ngan gon
    def write_rationale(self, template_text: str) -> str:
        # Khong co model, hoac het tran ngan sach: dung nguyen template. Van du nghia, chi kem muot hon.
        if not self._writer or not self.budget.allow():
            return template_text
        try:
            from bc_agent.llm import text_of
            resp = self._writer.text(
                system=caidat.cau("viet_lai"),
                user=template_text, max_tokens=400, thinking=True)
            self.budget.track("rationale", self._writer.model, resp.usage)
            if resp.stop_reason == "refusal":
                return template_text
            return text_of(resp) or template_text
        except Exception as e:  # khong de loi model lam gay luong
            log.warning("writer failed: %s", e)
            return template_text

    # ---------- inbound
    def handle_message(self, user_id: str, text: str, reply_to: int | None = None) -> list[Delivery]:
        """`reply_to` la id cua tin ma nguoi dung bam Tra loi.

        Vi sao can: tro ly hoi mot cau, chua kip tra loi thi da co tin khac chen vao, va cau tra
        loi bi gan nham vao cau hoi moi nhat. Bam Tra loi vao dung tin do thi tro ly biet no
        thuoc ve viec nao. Dung gap ngay 13/09/2026 voi cau hoi giai trinh chiet khau."""
        user = self.mem.user(user_id)
        if not user:
            return [Delivery(user_id, "Tôi chưa có bạn trong danh bạ. Nhờ NaviWorld thêm vào.")]
        self.mem.log_message(user_id, "in", text, reply_to=reply_to)
        goc = self.mem.message(reply_to) if reply_to else None
        pending = self.mem.pending_question(user_id, (goc or {}).get("ref"))
        # Cau rule khong doc duoc: thu kich ban da duyet TRUOC khi goi model phan loai. Dat sau
        # buoc nay thi cau nao khop kich ban van ton mot luot NLU cua model.
        if not pending and not goc and RuleNLU().parse(text).intent == "HELP":
            theo_kb = plan.thu_kich_ban(self, user, text)
            if theo_kb:
                so = getattr(self.nlu, "so", None)
                if so is not None:
                    so.ghi(False, "chạy kịch bản đã duyệt")
                return self._deliver(theo_kb)
        intent = self.nlu.parse(text, has_pending_question=bool(pending))
        log.info("%s -> %s %s", user_id, intent.intent, intent.item_text)

        if not pending and discount.la_noi_nham(text):
            # Vua ghi giai trinh xong ma noi la nham thi mo lai, dung de cau sua roi vao HELP.
            lam_lai = discount.mo_lai_giai_trinh(self, user)
            if lam_lai:
                return self._deliver(lam_lai)
        # Bam Tra loi vao dung tin dang hoi thi day la cau tra loi, khong can rule doan lai.
        if goc and pending and (goc.get("ref") or "") == (pending.get("ref") or ""):
            intent = Intent("ANSWER", intent.item_text, intent.quantity)
        if intent.intent == "ANSWER" and pending:
            out = discount.on_answer(self, user, pending, text)
        elif intent.intent == "STOCKOUT":
            out = replenishment.handle_stockout(self, user, intent)
        elif intent.intent == "STOCK_QUERY":
            out = replenishment.stock_query(self, user, intent)
        elif intent.intent == "BRIEF":
            out = self.morning_brief(user_id)
        elif intent.intent == "TRACKING":
            out = tracking.handle(self, user)
        elif intent.intent == "REPLEN_WHY":
            out = self._ls_vi_sao(user, intent, text)
        elif intent.intent == "PO_OVERDUE":
            out = po_qua_han.handle(self, user)
        elif intent.intent == "NHAC_POST":
            from .skills import nhac_post
            out = nhac_post.handle(self, user, text)
        elif intent.intent == "EXPIRY":
            out = inventory_health.het_han(self, user, intent, text)
        elif intent.intent == "ANOMALY":
            from .skills import uc2_bat_thuong
            out = uc2_bat_thuong.handle(self, user, intent, text)
        elif intent.intent == "WASTE_WHY":
            from .skills import uc2_nguyen_nhan
            out = uc2_nguyen_nhan.handle(self, user, intent, text)
        elif intent.intent == "WASTE_REPORT":
            from .skills import uc2_bao_cao_huy
            out = uc2_bao_cao_huy.handle(self, user, text)
        elif intent.intent == "FORECAST":
            out = du_bao.handle(self, user, intent, text)
        elif intent.intent == "SUPPLIER":
            out = nha_cung_cap.handle(self, user, text)
        elif intent.intent == "TRACE":
            out = truy_xuat.handle(self, user, text)
        elif intent.intent == "PROMO":
            out = khuyen_mai.handle(self, user, intent, text)
        elif intent.intent == "INVESTIGATE":
            out = self._investigate(user, intent, text)
        elif intent.intent == "SELF_REVIEW":
            out = review.run_self_review(self, user)
        elif intent.intent == "PLAN":
            # Model nhan ra day la yeu cau mo. Chi co model phan loai ra PLAN, rule thi khong.
            out = plan.handle(self, user, text)
        elif intent.intent == "DAMAGE":
            out = [Delivery(user_id, "Tôi ghi nhận hàng hỏng/trả. Ở bản POC này tôi chưa tạo chứng từ điều chỉnh; Supply Chain sẽ thấy trong brief. Bạn chụp ảnh gửi kèm nếu có.", skill="inventory_health")]
        else:
            # Rule khong phan loai duoc. Day KHONG phai loi: phan lon cau that trong van hanh
            # khong roi vao rule nao. Chuyen cho planner tu dung chuoi tra cuu.
            out = plan.handle(self, user, text) if self._dua_cho_planner(text) else [Delivery(user_id, caidat.cau("tro_giup"))]

        # Rule doan sai (bat trung mot tu khoa nhung khong giai duoc): tra lai cho planner,
        # thay vi tra ve mot cau hoi lai vo nghia.
        if len(out) == 1 and out[0].meta.get("unresolved") and self._dua_cho_planner(text):
            out = plan.handle(self, user, text)
        return self._deliver(out)

    def de_xuat_gop(self) -> list[dict[str, Any]]:
        """De xuat cua BC gop voi de xuat trong bo nho tro ly.

        BC la so goc nen trang thai lay theo BC; bo nho tro ly giu them dong policy da khop va
        ten mat hang nen giu lai nhung truong do. De xuat chi co trong bo nho (che do mo phong,
        hoac vua tao ma chua doc lai) van hien."""
        gop: dict[str, dict[str, Any]] = {}
        for p in self.gw.de_xuat():
            gop[p.get("proposal_id") or p.get("bc_id")] = dict(p)
        for p in self.mem.proposals():
            khoa = p.get("proposal_id")
            if khoa in gop:
                for k, v in p.items():                    # bo nho bo sung cho ban cua BC
                    if v not in (None, "") and not gop[khoa].get(k):
                        gop[khoa][k] = v
            else:
                gop[khoa] = dict(p)
        return sorted(gop.values(), key=lambda p: str(p.get("created_at") or ""), reverse=True)

    def _dua_cho_planner(self, text: str) -> bool:
        """Cau khong roi vao rule nao thi co dua cho planner tu dung chuoi tra cuu khong.

        Bat AI thi dua gan nhu moi cau: LivePlanner tu dung chuoi cho cau bat ky, va do chinh la
        cai dang mua. Nguong sau tu cu chan ca nhung cau ngan hoan toan hop le nhu
        "liet ke 5 mat hang", nguoi dung nhan lai cau tro giup va tuong AI khong chay.
        Tat AI thi giu nguong cu, vi ReplayPlanner chi khop duoc ban ghi co san; cau ngan
        khong khop se ra mot cau tu choi dai dong, tra loi tro giup con ro hon."""
        return len(text.split()) >= (2 if self.ai_live else 6)

    def handle_action(self, user_id: str, verb: str, ref: str, payload: dict[str, Any] | None = None) -> list[Delivery]:
        user = self.mem.user(user_id)
        payload = payload or {}
        if not user:
            return [Delivery(user_id, "Không nhận ra người dùng.")]
        self.mem.log_message(user_id, "in", action_text(verb, payload))

        if verb in ("approve", "edit", "reject"):
            prop = self.mem.proposal(ref)
            if not prop:
                return self._deliver([Delivery(user_id, "Không tìm thấy đề xuất.")])
            if user["role"] not in ("dispatcher", "supply_chain"):
                return self._deliver([Delivery(user_id, "Bạn không có quyền duyệt đề xuất này. Ranh giới này nằm trong permission set của BC, không phải do tôi quyết.")])
            if prop["status"] != "Proposed":
                return self._deliver([Delivery(user_id, f"Đề xuất này đã ở trạng thái {prop['status']}.")])
            fn = {"approve": replenishment.on_approve, "edit": replenishment.on_edit, "reject": replenishment.on_reject}[verb]
            return self._deliver(fn(self, user, prop, payload))
        if verb == "undo":
            prop = self.mem.proposal(ref)
            if not prop:
                return self._deliver([Delivery(user_id, "Không tìm thấy việc cần hoàn tác.")])
            if user["role"] not in ("dispatcher", "supply_chain"):
                return self._deliver([Delivery(user_id, "Chỉ điều phối hoặc Supply Chain hoàn tác được.")])
            return self._deliver(replenishment.on_undo(self, user, prop, payload))
        if verb == "ship":
            return self._deliver(replenishment.on_ship(self, user, ref, payload))
        if verb == "ack":
            return self._deliver([Delivery(user_id, "Đã ghi nhận.")])
        if verb == "ask_explanation":
            return self._deliver(discount.on_ask_explanation(self, user, ref))
        if verb in ("confirm_exception", "dismiss_exception"):
            if user["role"] != "retail_ops":
                return self._deliver([Delivery(user_id, "Chỉ Retail Ops kết luận exception.")])
            return self._deliver(discount.on_conclude(self, user, ref, "confirm" if verb == "confirm_exception" else "dismiss"))
        if verb == "inv_steps":
            return self._deliver(investigate.show_steps(self, user, ref))
        if verb == "inv_apply":
            return self._deliver(investigate.apply_fix(self, user, ref))
        if verb in ("lad_approve", "lad_reject", "lad_evidence"):
            prop = self.mem.proposal(ref)
            if not prop:
                return self._deliver([Delivery(user_id, "Không tìm thấy đề xuất.")])
            if verb == "lad_evidence":
                text = (payload.get("text") or "").strip()
                if not text:
                    return self._deliver([Delivery(user_id, "Bạn gõ giúp tôi một câu về chuyện đã xảy ra.")])
                self.mem.log_message(user_id, "in", text)
                return self._deliver(evidence.apply(self, user, prop, text))
            if user["role"] not in ("supply_chain", "dispatcher"):
                return self._deliver([Delivery(user_id, "Chỉ Supply Chain hoặc điều phối duyệt được việc đổi ngưỡng.")])
            if prop["status"] != "Proposed":
                return self._deliver([Delivery(user_id, f"Đề xuất này đã ở trạng thái {prop['status']}.")])
            if verb == "lad_approve":
                return self._deliver(ladder.on_approve(self, user, prop))
            self.gw.reject(prop["bc_id"], user.get("bc_user") or user_id, payload.get("reason", "")[:200])
            prop.update({"status": "Rejected", "approver": user_id, "outcome_note": payload.get("reason", "")})
            self.mem.save_proposal(prop)
            return self._deliver([Delivery(user_id, "Đã từ chối. Tôi ghi lại lý do cho vòng tự chấm điểm.", skill="ladder", ref=ref)])
        if verb == "ls_vi_sao":
            return self._deliver(ls_giai_thich.handle(self, user, payload.get("item_no", ""), payload.get("store", "")))
        if verb == "po_qua_han":
            return self._deliver(po_qua_han.handle(self, user))
        if verb in ("po_da_ve", "po_chua_ve"):
            return self._deliver(po_qua_han.on_xac_nhan(self, user, ref, verb == "po_da_ve"))
        if verb == "demand_show":
            return self._deliver(demand.run(self, user, payload.get("item_no", ""), payload.get("location", "")))
        if verb == "plan_steps":
            return self._deliver(plan.show_steps(self, user, ref))
        if verb in ("plan_ok", "plan_bad"):
            return self._deliver(plan.danh_gia(self, user, ref, verb == "plan_ok"))
        if verb == "plan_model":
            return self._deliver(plan.hoi_lai_bang_model(self, user, ref))
        if verb == "plan_apply":
            if user["role"] not in ("dispatcher", "supply_chain", "store_manager", "retail_ops", "warehouse"):
                return self._deliver([Delivery(user_id, "Vai trò này chưa được ghi đề xuất.")])
            return self._deliver(plan.apply_drafts(self, user, ref))
        if verb == "review_detail":
            return self._deliver(review.show_suggestions(self, user, ref))
        if verb == "ih_propose":
            return self._deliver(inventory_health.on_propose(self, user, ref, payload.get("action_type", "ReviewOnly")))
        if verb == "ih_transfer_fast":
            return self._deliver(inventory_health.on_transfer_fast(self, user, ref))
        if verb == "ih_d4_apply":
            from .skills import uc2_hanh_dong
            return self._deliver(uc2_hanh_dong.on_ap_dung(self, user, ref, payload.get("chon", "")))
        return self._deliver([Delivery(user_id, f"Chưa hỗ trợ hành động {verb}.")])

    @staticmethod
    def _norm(text: str) -> str:
        """Bo dau tieng Viet va khoang trang de so khop ten cua hang: 'Sieu thi Nam' khop S0001."""
        import unicodedata
        t = unicodedata.normalize("NFD", text.lower()).replace("\u0111", "d")
        return "".join(c for c in t if unicodedata.category(c) != "Mn" and c.isalnum())

    def _tim_cua_hang(self, text: str) -> str:
        """Ma cua hang nhac trong cau: ma (S0001), ten day du (Cua hang Quan 1) hoac phan rieng cua ten (Quan 1, Ha Noi,
        Thao Dien, Da Nang). Nguoi dung it khi go ca chu "Cua hang"; ngay 14/09/2026 cau "chuyen 82 hop Choco nuts xuong
        Quan 1" khong nhan ra cua hang nen roi sang planner. Phan rieng khong duoc dinh lien chu so phia sau (Quan 10)."""
        words = self._norm(text)
        for code in self.gw.stores():
            ten = STORE_LABEL.get(code, "")
            rieng = re.sub(r"^(cửa hàng|nhà hàng|quán cà phê)\s+", "", ten, flags=re.I)
            for k, alias in enumerate((code, ten, rieng)):
                a = self._norm(alias) if alias else ""
                i = words.find(a) if a else -1
                if i >= 0 and not (k and words[i + len(a):i + len(a) + 1].isdigit()):
                    return code
        return ""

    def _ls_vi_sao(self, user: dict[str, Any], intent, text: str) -> list[Delivery]:
        """Cau hoi vi sao LS Replenishment ra so luong do. Can mat hang va cua hang."""
        item = self.gw.find_item(intent.item_text, min_score=50) if intent.item_text else None
        if not item:
            return [Delivery(user["user_id"], "Bạn hỏi về mặt hàng nào? Ví dụ: \"vì sao LS đề xuất Choco nuts cho Cửa hàng Quận 1\".",
                             skill="ls_giai_thich", meta={"unresolved": True})]
        store = self._tim_cua_hang(text) or user.get("store_code") or ""
        if not store or store == self.gw.central_wh:
            return [Delivery(user["user_id"], "Bạn hỏi đề xuất cho cửa hàng nào?", skill="ls_giai_thich", meta={"unresolved": True})]
        return ls_giai_thich.handle(self, user, item["itemNo"], store)

    def _investigate(self, user: dict[str, Any], intent, text: str = "") -> list[Delivery]:
        """Cau hoi mo: phai doan item va store tu cau chu, roi giao cho skill dieu tra."""
        item = self.gw.find_item(intent.item_text, min_score=50) if intent.item_text else None
        if not item:
            return [Delivery(user["user_id"], "Bạn hỏi về mặt hàng nào? Ví dụ: \"sao Cửa hàng Quận 1 cứ hết Chocolate ice cream\".", skill="investigate", meta={"unresolved": True})]
        # Do ten cua hang tren CAU GOC, khong phai tren item_text. item_text da bi cat stopword,
        # ma trong stopword co "cua hang", nen ten kieu "Cua hang Quan 1" khong bao gio khop.
        store = self._tim_cua_hang(text or intent.item_text) or user.get("store_code") or ""
        # Dieu tra la chuyen cua hang dut hang. Nguoi kho hoi ma khong nhac cua hang nao thi cau
        # do khong phai cau dieu tra, tra lai cho planner (vi du "hang trong kho bi uot, xu ly sao").
        if not store or store == self.gw.central_wh:
            return [Delivery(user["user_id"], "Bạn hỏi về cửa hàng nào?", skill="investigate", meta={"unresolved": True})]
        # Neu cap nay da dut hang lap lai va tro ly da tung chuyen hang, thi cau hoi khong con la
        # "vi sao lan nay", ma la "vi sao chua bao gio het". Chuyen sang bac thang chan doan.
        d = ladder.diagnose(self, item["itemNo"], store)
        if d["level"] >= 2:
            return ladder.run(self, user, item["itemNo"], store)
        return investigate.run(self, user, item["itemNo"], store)

    # ---------- brief va theo doi
    def morning_brief(self, user_id: str) -> list[Delivery]:
        user = self.mem.user(user_id)
        if not user:
            return []
        role = user["role"]
        if role == "dispatcher":
            out = replenishment.brief_for_dispatcher(self, user)
        elif role == "supply_chain":
            out = inventory_health.brief_for_supply_chain(self, user)
        elif role == "retail_ops":
            out = discount.brief_for_retail_ops(self, user)
        elif role == "store_manager":
            rows = [r for r in self.gw.risky_suggestions(50) if r["storeLocationCode"] == user["store_code"]]
            # Doc de xuat gop BC va bo nho, giong cot phai va cau "de xuat cua toi den dau roi". Truoc 14/09/2026 chi doc bo
            # nho tro ly nen brief bao "0 de xuat dang cho" trong khi BC co 4 de xuat cho S0010.
            pend = [p for p in self.de_xuat_gop() if p.get("status") == "Proposed" and p.get("to_loc") == user["store_code"]]
            text = (f"Cửa hàng {user['store_code']}: {len(rows)} mặt hàng dưới ngưỡng ({', '.join(r['itemDescription'] for r in rows)}). "
                    f"{len(pend)} đề xuất đang chờ điều phối duyệt.") if rows or pend else f"Cửa hàng {user['store_code']} sáng nay đủ hàng."
            out = [Delivery(user_id, text)]
            # UC2 S1: lo het han, can date tai cua hang minh, do AI tom tat (15/09/2026). Loi doc bang khong duoc lam hong brief.
            try:
                from .skills import uc2_tom_tat
                out += uc2_tom_tat.brief_ai(self, user)
            except Exception as exc:
                log.warning("Brief bo qua tom tat UC2: %s", exc)
        elif role == "warehouse":
            open_tos = [t for t in self.gw._transfers.values() if not t["shipped"] and t["status"] != "Cancelled"] if self.gw.is_mock else []
            if open_tos:
                desc = {i["itemNo"]: i["description"] for i in self.gw.items()}
                lines = "; ".join(f"{t['no']}: {t['quantity']:.0f} {desc.get(t['itemNo'], t['itemNo'])} đi {t['toLocationCode']}" for t in open_tos)
                text = f"Sáng nay {len(open_tos)} đơn chờ ship. {lines}."
            else:
                text = "Sáng nay không có đơn nào chờ ship."
            out = [Delivery(user_id, text, skill="replenishment")]
        else:
            out = [Delivery(user_id, "Chưa có brief cho vai trò này.")]
        if role in ("supply_chain", "dispatcher", "store_manager"):
            # CTKM sap bat dau, chi khi co. Thieu API page khuyen mai (app cu) khong duoc lam hong ca brief.
            try:
                out += khuyen_mai.tom_tat_cho_brief(self, user)
            except Exception as exc:
                log.warning("Brief bo qua CTKM: %s", exc)
        if role in ("supply_chain", "store_manager", "warehouse"):
            # UC3: mot dong ve don mua qua han nhan, chi khi co. Loi doc don mua khong duoc lam hong ca brief.
            try:
                out += po_qua_han.tom_tat_cho_brief(self, user)
            except Exception as exc:
                log.warning("Brief bo qua don mua qua han: %s", exc)
        return self._deliver(out)

    def run_followups(self) -> list[Delivery]:
        out: list[Delivery] = []
        now = self.mem.now()
        for f in self.mem.due_followups():
            if f["kind"] == "transfer_ship":
                t = self.gw.transfer(f["ref"])
                if t and t["shipped"]:
                    self.mem.update_followup(f["id"], status="done")
                    continue
                attempts = f["attempts"] + 1
                msg = f"Nhắc lần {attempts}: {f['ref']} ({t['quantity']:.0f} {t['itemNo']} đi {t['toLocationCode']}) chưa ship. Cửa hàng đang chờ."
                for w in self.mem.users_by_role("warehouse"):
                    out.append(Delivery(w["user_id"], msg, skill="replenishment", ref=f["ref"]))
                if attempts >= 2 and f["escalate_user"]:
                    out.append(Delivery(f["escalate_user"], f"{f['ref']} đã nhắc kho {attempts} lần vẫn chưa ship. Bạn can thiệp giúp.", skill="replenishment", ref=f["ref"]))
                self.mem.update_followup(f["id"], attempts=attempts, due_at=(now + timedelta(hours=6)).isoformat())
            elif f["kind"] == "write_off_post":
                # UC2 A3: chung tu huy nhap da duoc ke toan post chua (16/09/2026).
                from .skills import uc2_huy
                out += uc2_huy.theo_doi(self, f)
            elif f["kind"] == "transfer_receive":
                t = self.gw.transfer(f["ref"])
                if t and t["received"]:
                    self.mem.update_followup(f["id"], status="done")
                    continue
                if t and t["shipped"]:
                    out.append(Delivery(f["notify_user"], f"{f['ref']} đã ship 2 ngày, cửa hàng nhận chưa? Nhận rồi bạn nhắn tôi để đóng đơn.", skill="replenishment", ref=f["ref"]))
                self.mem.update_followup(f["id"], attempts=f["attempts"] + 1, due_at=(now + timedelta(hours=24)).isoformat())
        return self._deliver(out)

    # ---------- ghi log outbound; channel doc tu inbox
    def _deliver(self, out: list[Delivery]) -> list[Delivery]:
        """Ghi tin ra hop thu. Moi Delivery chi ghi mot lan, du di qua day may lan.

        Vai duong co hai tang goi `_deliver`: `handle_message` goi cho ket qua cuoi cung, con
        `morning_brief` da tu goi vi no cung la mot cua vao rieng (`POST /api/brief`). Go "brief"
        trong chat thi di qua ca hai, va man hinh hien hai lan cung mot cau. Bat duoc ngay
        13/09/2026. Danh dau tung tin thay vi go bo mot trong hai tang, vi con vai duong khac
        cung co hinh nay va bo nham la mat tin."""
        for d in out:
            if d.meta.get("da_ghi"):
                continue
            d.meta["da_ghi"] = True
            self.mem.log_message(d.user_id, "out", d.text, d.card.to_dict() if d.card else None, d.skill, d.ref)
        return out
