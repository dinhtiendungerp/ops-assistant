"""Skill 'yeu cau mo': cau nguoi ta go khong roi vao rule nao co san.

Khac biet so voi cac skill khac trong thu muc nay: cac skill kia biet truoc phai doc bang nao,
theo thu tu nao. Skill nay khong biet. No dua cau hoi cho planner kem mot bo cong cu,
va planner tu quyet dinh goi gi, bao nhieu lan, khi nao du de tra loi.
"""
from __future__ import annotations

import logging
import uuid
from typing import Any

from .. import kich_ban
from ..cards import Action, Card
from ..planner import Plan
from . import Delivery, replenishment

log = logging.getLogger(__name__)
SKILL = "plan"

# Nguoi doc la dieu phoi kho va quan ly cua hang. Khong ke ten bien moi truong, khong ke ten
# thanh phan ky thuat; chi noi duoc gi va chua duoc gi.
CANT = ("Câu này tôi chưa trả lời được. Buổi demo đang chạy ở chế độ bản ghi: tôi chỉ đi lại được "
        "những chuỗi tra cứu đã dựng sẵn cho vài tình huống mẫu, chứ chưa tự nghĩ ra cách tra cho "
        "một câu mới. Khi mở chế độ đầy đủ thì tôi tự dựng chuỗi cho câu bất kỳ. Chỗ đổi chế độ "
        "nằm trong bảng điều khiển demo ở cột bên phải.")


def handle(asst: Any, user: dict[str, Any], text: str) -> list[Delivery]:
    """Dua cau cho planner. Kich ban da duyet duoc thu TRUOC do, o `thu_kich_ban`, goi tu core."""
    prev = (asst.mem.recall("last_plan") or {}).get("id", "")
    truoc = asst.budget.tong()
    try:
        plan: Plan | None = asst.planner.run(asst, user, text, prev)
    except Exception as exc:
        # Truoc day loi cua model (vi du Azure 429 vuot han muc token moi phut) lam sap ca request,
        # nguoi dung thay dai do "loi 500" ma khong biet vi sao. Noi ro ra chat.
        log.warning("Planner hong: %s", exc)
        sau = asst.budget.tong()
        kich_ban.ghi_cau_hoi(user, text, "khong_tra_loi", asst.gw, token=sau["token_tong"] - truoc["token_tong"],
                             usd=sau["usd"] - truoc["usd"])
        ly_do = ("model đang vượt hạn mức token mỗi phút của Azure, bạn đợi khoảng một phút rồi hỏi lại"
                 if "429" in str(exc) else "lần gọi model bị lỗi, bạn hỏi lại giúp tôi")
        return [Delivery(user["user_id"], f"Tôi chưa trả lời được câu này: {ly_do}. Câu hỏi đã được ghi lại.", skill=SKILL)]
    sau = asst.budget.tong()
    token, usd = sau["token_tong"] - truoc["token_tong"], sau["usd"] - truoc["usd"]
    if plan is None:
        # Khong duong nao tra loi duoc. Van ghi lai: day la khoang trong phai lap, co khi bang
        # them mot tool doc du lieu chu khong phai bang kich ban.
        kich_ban.ghi_cau_hoi(user, text, "khong_tra_loi", asst.gw, token=token, usd=usd)
        return [Delivery(user["user_id"], CANT, skill=SKILL)]
    return _tra_ket_qua(asst, user, text, plan, token, usd)


def _tra_ket_qua(asst: Any, user: dict[str, Any], text: str, plan: Plan, token: int = 0, usd: float = 0.0,
                 kb: dict[str, Any] | None = None) -> list[Delivery]:
    ref = f"PLAN-{uuid.uuid4().hex[:6].upper()}"
    asst.mem.remember("last_plan", {"id": plan.scenario_id, "ref": ref})
    buoc = [{"tool": s.tool, "args": s.args, "why": s.why, "result": s.result} for s in plan.steps]
    asst.mem.remember(f"plan:{ref}", {
        "source": plan.source, "scenario_id": plan.scenario_id, "question": plan.question,
        "recorded": plan.tokens_note, "drafts": plan.drafts, "cau": text, "steps": buoc,
    })
    nguon = {"live": "model", "replay": "ban_ghi", "kich_ban": "kich_ban"}.get(plan.source, plan.source)
    kich_ban.ghi_cau_hoi(user, text, nguon, asst.gw, buoc, plan.answer, ref, token, usd,
                         kich_ban_id=plan.scenario_id if nguon == "kich_ban" else "")

    actions = [Action("plan_steps", f"Xem {len(plan.steps)} bước tôi đã tra")]
    if plan.drafts:
        actions.append(Action("plan_apply", f"Ghi {len(plan.drafts)} đề xuất vào BC", "positive"))
    if plan.source == "kich_ban":
        actions.append(Action("plan_model", "Hỏi lại bằng model"))
    actions += [Action("plan_ok", "Trả lời đúng"), Action("plan_bad", "Chưa đúng")]
    if plan.source == "kich_ban":
        nguon_chu = f"kịch bản {plan.scenario_id} do {kb.get('duyet_boi', '')} duyệt, không gọi model" if kb else plan.scenario_id
    elif plan.source == "live":
        nguon_chu = "model tự dựng chuỗi tra cứu"
    else:
        nguon_chu = f"bản ghi {plan.scenario_id}"
    # "Nguoi soan" dat dau tien, cung nhan voi cac the AI khac (S1, D3, D4...), de nhin vao la biet AI viet hay cau mau.
    soan = f"AI ({asst.model_name.split(':')[-1]})" if plan.source == "live" else "không gọi model"
    facts = [("Người soạn", soan), ("Nguồn", nguon_chu), ("Số bước tra cứu", str(len(plan.steps)))]
    if plan.source == "live" and token:
        facts.append(("Token", f"{token:,}".replace(",", ".")))
    body = plan.question or ""
    # Model tu viet cau tra loi nen co the gan so cua dia diem nay sang dia diem khac. Code kiem, khong hoi lai model.
    sai = kich_ban.so_sai_dia_diem(plan.answer or "", buoc) if plan.source == "live" else []
    if sai:
        facts.append(("Kiểm tra số", f"{len(sai)} số không khớp dữ liệu đã tra"))
        body = (body + "\n" if body else "") + "Đừng dùng các số sau, code không tìm thấy chúng trong kết quả tra cứu:\n" + \
            "\n".join(f"· {x}" for x in sai)
    card = Card(title="Kế hoạch tôi dựng từ dữ liệu", body=body, facts=facts,
                ref=ref, kind="info", actions=actions)
    return [Delivery(user["user_id"], plan.answer, card, SKILL, ref)]


def thu_kich_ban(asst: Any, user: dict[str, Any], text: str) -> list[Delivery] | None:
    """Cau khong khop rule nao: thu kich ban da duyet truoc khi tra tien cho model.

    Tra None la khong co kich ban hop, hoac kich ban khop nhung khong doc duoc du so tren du lieu
    hien tai; cau hoi di tiep duong cu."""
    hit = kich_ban.khop(text, asst.gw)
    if not hit:
        return None
    kb, bien, giong = hit
    plan, ly_do = kich_ban.chay(kb, asst, user, bien)
    if plan is None:
        log.info("Bo kich ban %s cho cau %r: %s", kb["id"], text, ly_do)
        return None
    log.info("Tra loi bang kich ban %s (giong %.2f), khong goi model", kb["id"], giong)
    return _tra_ket_qua(asst, user, text, plan, kb=kb)


def danh_gia(asst: Any, user: dict[str, Any], ref: str, dung: bool) -> list[Delivery]:
    r = kich_ban.danh_gia(ref, dung)
    if not r:
        return [Delivery(user["user_id"], "Không còn câu trả lời này.", skill=SKILL)]
    if dung:
        cau = "Cảm ơn. Tôi ghi nhận câu trả lời này đúng."
        if r["nguon"] == "model":
            cau += " Người quản trị sẽ thấy nó trong danh sách câu có thể lưu thành kịch bản."
    else:
        cau = "Tôi ghi nhận câu trả lời này chưa đúng. Nó sẽ không được lưu thành kịch bản."
        if r["nguon"] == "kich_ban":
            cau = (f"Tôi ghi nhận kịch bản {r['kich_ban_id']} trả lời chưa đúng cho câu này. Người quản trị sẽ thấy "
                   "số lần bị báo sai. Bạn bấm Hỏi lại bằng model để có câu trả lời tự dựng.")
    return [Delivery(user["user_id"], cau, skill=SKILL, ref=ref)]


def hoi_lai_bang_model(asst: Any, user: dict[str, Any], ref: str) -> list[Delivery]:
    p = asst.mem.recall(f"plan:{ref}")
    if not p or not p.get("cau"):
        return [Delivery(user["user_id"], "Không còn câu hỏi gốc này.", skill=SKILL)]
    if not asst.ai_live:
        return [Delivery(user["user_id"], "AI đang tắt nên tôi chưa hỏi lại bằng model được.", skill=SKILL)]
    return handle(asst, user, p["cau"])


# Moi buoc tra cuu ke bang mot cau tieng Viet. Nguoi doc la dieu phoi kho va quan ly cua hang,
# ho khong can biet ten ham; ten ham chi con o log chay trong runs/.
def _ten_mat_hang(asst: Any, item_no: str) -> str:
    if not item_no:
        return ""
    ten = next((i["description"] for i in asst.gw.items() if i["itemNo"] == item_no), "")
    return f"{ten} ({item_no})" if ten else str(item_no)


def _ten_dia_diem(asst: Any, code: str) -> str:
    if not code:
        return ""
    from ..core import STORE_LABEL
    ten = STORE_LABEL.get(code)
    return f"{ten} ({code})" if ten else str(code)


def _buoc_tieng_viet(tool: str, args: dict[str, Any], asst: Any) -> str:
    ten = _ten_mat_hang(asst, args.get("item_no", ""))
    noi = _ten_dia_diem(asst, args.get("location", ""))
    if tool == "list_stock":
        nhom = f", nhóm hàng {args['category']}" if args.get("category") else ""
        return f"Đọc tồn kho tại {noi}{nhom}"
    if tool == "stock_by_item":
        return f"Xem {ten} đang nằm ở những kho và cửa hàng nào"
    if tool == "find_item":
        return f"Tra mã mặt hàng từ chữ \u201c{args.get('text', '')}\u201d"
    if tool == "stores_at_risk":
        return "Xem cửa hàng nào đang dưới ngưỡng tồn" + (f", riêng {ten}" if ten else "")
    if tool == "sales_rate":
        o = f" tại {noi}" if noi else " trên toàn hệ thống"
        return f"Đọc tốc độ bán của {ten}{o}, {args.get('days') or 90} ngày gần nhất"
    if tool == "lot_info":
        return f"Tra lô {args.get('lot_no', '')}: nằm ở đâu, còn bao nhiêu, hạn khi nào"
    if tool == "open_discount_exceptions":
        return "Đọc các trường hợp chiết khấu đang chờ giải trình"
    if tool == "draft_proposal":
        tu, den = _ten_dia_diem(asst, args.get("from_location", "")), _ten_dia_diem(asst, args.get("to_location", ""))
        duong = f" từ {tu}" if tu else ""
        duong += f" sang {den}" if den and den != tu else ""
        return f"Soạn đề xuất {args.get('action_type', '')} {args.get('quantity', '')} {ten}{duong}"
    if tool == "ask_human":
        return "Hỏi lại người dùng, vì không bảng nào trong Business Central trả lời được"
    return tool


def show_steps(asst: Any, user: dict[str, Any], ref: str) -> list[Delivery]:
    p = asst.mem.recall(f"plan:{ref}")
    if not p:
        return [Delivery(user["user_id"], "Không còn bản kế hoạch này.", skill=SKILL)]
    lines = []
    for i, s in enumerate(p["steps"], 1):
        n = len(s["result"]) if isinstance(s["result"], list) else 1
        buoc = _buoc_tieng_viet(s["tool"], s["args"], asst)
        cau = f"{i}. {buoc}." if s["tool"] in ("ask_human", "draft_proposal") else f"{i}. {buoc}, đọc được {n} dòng."
        if s.get("why"):
            cau += f"\n    Lý do: {s['why']}"
        lines.append(cau)
    note = p.get("recorded") or ""
    if p["source"] == "replay":
        tail = ("\n\nThứ tự các bước là bản ghi, nhưng dữ liệu thì đọc lại thật ở thời điểm chạy, nên "
                "con số trong câu trả lời là số hiện tại chứ không phải số chép sẵn.")
    elif p["source"] == "kich_ban":
        tail = (f"\n\nChuỗi này là kịch bản {p['scenario_id']}: lần đầu do model dựng, người quản trị đã duyệt "
                "và lưu lại. Dữ liệu đọc lại thật lúc chạy, mọi con số trong câu trả lời lấy từ kết quả các "
                "bước trên, không gọi model.")
    else:
        tail = "\n\nChuỗi này do model tự dựng tại chỗ. Hỏi lại câu khác sẽ ra chuỗi khác."
    return [Delivery(user["user_id"], "Tôi đã tra theo thứ tự này:\n\n" + "\n".join(lines) + tail
                     + (f"\n\n{note}" if note else ""), skill=SKILL, ref=ref)]


_SCENARIO = {"Transfer": "StoreReplenishment", "Escalate": "StoreReplenishment"}


def apply_drafts(asst: Any, user: dict[str, Any], ref: str) -> list[Delivery]:
    """Ghi tung de xuat vao BC roi tha qua PolicyEngine y het cac skill khac.
    Ke hoach do model dung ra khong duoc mot dac quyen nao: van policy do, van nguoi duyet do."""
    p = asst.mem.recall(f"plan:{ref}")
    if not p:
        return [Delivery(user["user_id"], "Không còn bản kế hoạch này.", skill=SKILL)]
    if p.get("applied"):
        return [Delivery(user["user_id"], "Kế hoạch này đã ghi vào BC rồi.", skill=SKILL)]
    items = {i["itemNo"]: i for i in asst.gw.items()}
    out: list[Delivery] = []
    created_ids: list[str] = []
    for d in p["drafts"]:
        item_no = d["item_no"]
        item = {"itemNo": item_no, "description": items.get(item_no, {}).get("description", item_no), "category": ""}
        unit = asst.gw.unit_cost(item_no)
        qty = float(d.get("quantity") or 0)
        created = asst.gw.create_proposal(
            scenario=_SCENARIO.get(d["action_type"], "InventoryHealth"), action_type=d["action_type"], item_no=item_no,
            from_loc=d.get("from_location", ""), to_loc=d.get("to_location", ""), quantity=qty,
            reference_key=f"{ref}|{item_no}|{d.get('from_location','')}", rationale=d["rationale"], priority=60,
            evidence={"from_plan": ref, "scenario": p["scenario_id"], "source": p["source"]},
            run_id=asst.run_id, model_name=asst.model_name)
        prop = {"proposal_id": created.get("proposalId") or str(uuid.uuid4()), "bc_id": created["id"],
                "scenario": _SCENARIO.get(d["action_type"], "InventoryHealth"), "action_type": d["action_type"],
                "status": "Proposed", "item_no": item_no, "from_loc": d.get("from_location", ""),
                "to_loc": d.get("to_location", ""), "quantity": qty, "max_quantity": qty, "rationale": d["rationale"],
                "evidence": {"from_plan": ref}, "requested_by": user["user_id"], "created_at": asst.mem.now().isoformat(),
                "item_desc": item["description"], "value_vnd": qty * unit, "item_category": ""}
        asst.mem.save_proposal(prop)
        out += replenishment._to_dispatchers(asst, prop, item, None)
        created_ids.append(prop["proposal_id"])
    p["applied"] = True
    asst.mem.remember(f"plan:{ref}", p)
    done = {d["proposal_id"]: d["status"] for d in asst.mem.proposals()}
    auto = sum(1 for pid in created_ids if done.get(pid) == "Executed")
    out.insert(0, Delivery(user["user_id"],
                           f"Tôi ghi {len(p['drafts'])} đề xuất vào BC. Policy tự lọc: {auto} việc tôi tự làm, "
                           f"{len(p['drafts']) - auto} việc chờ người duyệt. Không đề xuất nào được đi tắt.",
                           skill=SKILL, ref=ref))
    return out
