"""MCP server cua tro ly: phoi bo cong cu cua planner ra cho client MCP ben ngoai.

Vi sao co file nay. Dung hoi ngay 13/09/2026: Foundry, Copilot Studio, VS Code, Claude Desktop deu
noi duoc MCP, sao bo cong cu cua tro ly chua la MCP. Truoc day `assistant/toolbox.py` chi dung duoc
tu trong planner cua chinh tro ly. Gio client nao noi MCP cung goi duoc, qua `POST /mcp` tren cung
server web, ma KHONG di vong qua ranh gioi:

  - Doc: so da tinh boi AL trong BC, qua dung gateway va ban nho cua tro ly.
  - Ghi: chi ghi DE XUAT, trang thai Proposed, qua PolicyEngine va day the cho nguoi duyet y het
    luong trong chat. So luong bi chan theo ton tai dia diem nguon ngay o day, khong o model.
  - Khong co tool nao tao chung tu, duyet, hay post. Cai do van la viec cua nguoi duyet.

Giao thuc: MCP Streamable HTTP, JSON-RPC 2.0. Server tra JSON thang (spec cho phep), khong mo
luong SSE, vi khong co tool nao chay lau hay can day thong bao. Tu viet thay vi dung goi `mcp` vi
may chua cai va phan can dung chi la initialize, tools/list, tools/call, ping.

Danh tinh: moi khoa trong `MCP_KEYS` gan voi mot nguoi dung demo, dang `khoa:user_id,khoa2:user_id2`.
Goi tu chinh may (127.0.0.1) thi khong can khoa, nguoi dung lay tu header `X-Marou-User`, mac dinh
`trang.sc`, giong nhu giao dien web demo hien cung khong co dang nhap.
"""
from __future__ import annotations

import json
import logging
import os
import uuid
from typing import Any

from . import toolbox

log = logging.getLogger(__name__)

PHIEN_BAN_GIAO_THUC = "2025-06-18"
TEN_SERVER = "marou-ops"
NGUOI_MAC_DINH = "trang.sc"
VAI_GHI_DUOC = ("dispatcher", "supply_chain", "store_manager", "retail_ops", "warehouse")

HUONG_DAN = (
    "Cong cu doc so lieu ton kho cua Marou tu Business Central va ghi de xuat cho nguoi duyet. "
    "Moi con so da do lop AL trong BC tinh; chep so tu ket qua tool, khong tu tinh them. "
    "Ghi de xuat khong tao chung tu: de xuat o trang thai Proposed, policy quyet dinh tu lam hay hoi nguoi, "
    "nguoi duyet bam Duyet thi BC moi tao Transfer Order. Hoi ve mot mat hang thi bat dau bang find_item "
    "roi stock_by_item."
)

# Bo cong cu cua planner, bo ask_human (client MCP tu hoi nguoi dung cua no) va doi draft_proposal
# tu "ghi nhap" thanh ghi that, vi o day khong con buoc nguoi xem ke hoach roi bam Ghi.
_BO = ("ask_human", "draft_proposal")


def _tools() -> list[dict[str, Any]]:
    ra = []
    for t in toolbox.TOOLS:
        if t["name"] in _BO:
            continue
        ra.append({"name": t["name"], "description": t["description"], "inputSchema": t["input_schema"]})
    ra.append({
        "name": "inventory_health_summary",
        "description": "Tong hop Inventory Health: so dong, so luong va gia tri ton theo tung tang (Expired, NearExpiry, "
                       "StockOutRisk, SlowMoving, Excess, Healthy), ngay chot so. Dung cho cau hoi 'ton xau bao nhieu tien'.",
        "inputSchema": {"type": "object", "properties": {}, "required": []},
    })
    ra.append({
        "name": "proposal_status",
        "description": "De xuat dang co trong BC va trang thai (Proposed, Executed, Rejected), chung tu da sinh. "
                       "Loc theo ma hang, dia diem nhan, trang thai. Dung de tra loi 'viec nay den dau roi'.",
        "inputSchema": {"type": "object", "properties": {
            "item_no": {"type": "string"}, "location": {"type": "string"},
            "status": {"type": "string", "enum": ["", "Proposed", "Executed", "Rejected"]}}, "required": []},
    })
    ra.append({
        "name": "explain_replenishment",
        "description": "Vi sao LS Replenishment de xuat so luong do cho mot mat hang tai mot cua hang: cong thuc LS, ban binh "
                       "quan va cua so ban, ton hieu dung, tham so tren Item, quyet dinh va nhat ky tinh LS nguyen van. Chi doc.",
        "inputSchema": {"type": "object", "properties": {
            "item_no": {"type": "string"}, "location": {"type": "string", "description": "Ma cua hang, vd S0001."}},
            "required": ["item_no", "location"]},
    })
    ra.append({
        "name": "overdue_purchase_orders",
        "description": "UC3: dong don mua (Purchase Order) con so luong chua nhan ma Expected Receipt Date da qua ngay chot so. "
                       "Gom theo so don va dia diem nhan, kem so ngay tre, da nhan mot phan chua, va cau tra loi cua cua hang "
                       "(hang da ve hay chua) neu co. Chi doc, khong post nhan hang.",
        "inputSchema": {"type": "object", "properties": {
            "location": {"type": "string", "description": "Ma dia diem nhan, rong la tat ca."}}, "required": []},
    })
    ra.append({
        "name": "forecast_accuracy",
        "description": "UC1: do chinh xac du bao baseline (MA28 trung binh 28 ngay, SWA8 trung binh cung thu) do tren ky kiem tra "
                       "28 ngay cuoi lich su, do BC tinh. WAPE gop tong va theo diem ban, nhom hang, danh sach cap vuot nguong. "
                       "Truyen item_no de lay chi tiet mot mat hang. Chi doc.",
        "inputSchema": {"type": "object", "properties": {
            "item_no": {"type": "string", "description": "Rong la tong hop."},
            "location": {"type": "string", "description": "Ma diem ban, rong la tat ca."}}, "required": []},
    })
    ra.append({
        "name": "supplier_scorecard",
        "description": "UC3: scorecard nha cung cap do BC tinh: ty le giao dung han, giao du lan dau, lead time hua va thuc te, "
                       "so ngay tre trung binh, dong qua han chua nhan. Moi nha cung cap co dong tong va dong theo nhom hang. Chi doc.",
        "inputSchema": {"type": "object", "properties": {
            "vendor_no": {"type": "string", "description": "Rong la tat ca."}}, "required": []},
    })
    ra.append({
        "name": "trace_lot",
        "description": "UC2: truy xuat mot lo tu Item Ledger Entry: nhap, nhan, xuat, ban tai tung dia diem, con ton o dau, "
                       "han dung. Dung khi can thu hoi. Chi doc.",
        "inputSchema": {"type": "object", "properties": {
            "lot_no": {"type": "string", "description": "Vd L260908-33170B."}}, "required": ["lot_no"]},
    })
    ra.append({
        "name": "create_proposal",
        "description": "Ghi MOT de xuat vao BC (bang NWV Agent Proposal), trang thai Proposed. KHONG tao chung tu. "
                       "Policy cua Marou quyet dinh tu lam hay dua nguoi duyet; nguoi duyet nhan the ngay trong hoi thoai. "
                       "Transfer va WriteOff bi chan neu so luong vuot ton tai dia diem nguon. Chi goi khi da doc du so lieu "
                       "va nguoi dung da dong y ghi.",
        "inputSchema": {"type": "object", "properties": {
            "action_type": {"type": "string", "enum": ["Transfer", "Markdown", "BlockPurchase", "WriteOff", "ReviewOnly"]},
            "item_no": {"type": "string"},
            "from_location": {"type": "string", "description": "Dia diem nguon. Transfer mac dinh la kho trung tam."},
            "to_location": {"type": "string", "description": "Dia diem nhan, bat buoc voi Transfer."},
            "quantity": {"type": "number"},
            "rationale": {"type": "string", "description": "Ly do bang tieng Viet, neu ro con so doc duoc tu tool."}},
            "required": ["action_type", "item_no", "quantity", "rationale"]},
    })
    return ra


# ---------------------------------------------------------------- danh tinh
def khoa_hop_le() -> dict[str, str]:
    ra = {}
    for cap in (os.getenv("MCP_KEYS") or "").split(","):
        khoa, _, nguoi = cap.strip().partition(":")
        if khoa and nguoi:
            ra[khoa] = nguoi
    return ra


def nguoi_goi(headers: dict[str, str], dia_chi: str) -> str | None:
    """user_id cua ben goi, hoac None neu khong duoc phep."""
    h = {k.lower(): v for k, v in headers.items()}
    khoa = h.get("x-api-key") or (h.get("authorization") or "").removeprefix("Bearer ").strip()
    ds = khoa_hop_le()
    if khoa and khoa in ds:
        return ds[khoa]
    if dia_chi in ("127.0.0.1", "::1", "localhost"):
        return h.get("x-marou-user") or NGUOI_MAC_DINH
    return None


# ---------------------------------------------------------------- goi tool
def _loi(cau: str) -> dict[str, Any]:
    return {"content": [{"type": "text", "text": cau}], "isError": True}


def _ket_qua(du_lieu: Any) -> dict[str, Any]:
    chu = json.dumps(du_lieu, ensure_ascii=False, default=str)
    ra: dict[str, Any] = {"content": [{"type": "text", "text": chu[:60000]}], "isError": False}
    if isinstance(du_lieu, dict):
        ra["structuredContent"] = du_lieu
    return ra


def goi_tool(asst: Any, user: dict[str, Any], ten: str, args: dict[str, Any]) -> dict[str, Any]:
    args = args or {}
    try:
        if ten in _BO:
            return _loi(f"Tool {ten} không có trên MCP server này.")
        if ten == "inventory_health_summary":
            from . import uc2
            return _ket_qua(uc2.summary(asst))
        if ten == "proposal_status":
            ds = asst.de_xuat_gop()
            if args.get("item_no"):
                ds = [p for p in ds if p.get("item_no") == args["item_no"]]
            if args.get("location"):
                ds = [p for p in ds if args["location"] in (p.get("to_loc"), p.get("from_loc"))]
            if args.get("status"):
                ds = [p for p in ds if p.get("status") == args["status"]]
            giu = ("proposal_id", "status", "action_type", "item_no", "item_desc", "from_loc", "to_loc", "quantity",
                   "policy_rule", "result_doc", "created_at", "approver")
            return _ket_qua({"so_de_xuat": len(ds), "de_xuat": [{k: p.get(k) for k in giu} for p in ds[:50]]})
        if ten == "explain_replenishment":
            from .skills import ls_giai_thich
            kq = ls_giai_thich.giai_thich(asst.gw, args["item_no"], args["location"])
            return _ket_qua(kq or {"loi": "Khong co dong LS cho mat hang va cua hang nay, hoac dang chay mo phong."})
        if ten == "overdue_purchase_orders":
            from .skills import po_qua_han as pq
            don = pq.gom_theo_don(pq.dong_qua_han(asst, args.get("location") or None))
            return _ket_qua({"ngay_chot": asst.gw.today().isoformat(), "so_don": len(don), "don": [
                {"so_don": d["so_don"], "dia_diem": d["dia_diem"], "nha_cung_cap": d["nha_cung_cap"],
                 "tre_nhat_ngay": d["tre_nhat"], "nhan_mot_phan": d["nhan_mot_phan"],
                 "xac_nhan_cua_hang": pq._xac_nhan(asst, pq._ref(d)),
                 "dong": [{k: r.get(k) for k in ("lineNo", "itemNo", "description", "quantity", "outstandingQuantity",
                                                 "quantityReceived", "expectedReceiptDate", "so_ngay_tre")} for r in d["dong"]]}
                for d in don[:50]]})
        if ten == "forecast_accuracy":
            from .skills import du_bao
            rows = asst.gw.doc("forecastAccuracies", [], top=5000)
            if args.get("location"):
                rows = [r for r in rows if r["locationCode"] == args["location"]]
            if args.get("item_no"):
                return _ket_qua({"dong": [r for r in rows if r["itemNo"] == args["item_no"]]})
            th = du_bao.tong_hop(rows) if rows else {}
            if th:
                th["ngoai_le"] = [{k: r.get(k) for k in ("itemNo", "itemDescription", "locationCode", "actualQty", "forecastQty",
                                                         "wapePct", "biasPct", "exceptionReason")} for r in th["ngoai_le"][:30]]
            return _ket_qua(th or {"loi": "Chua co ket qua do du bao tren BC."})
        if ten == "supplier_scorecard":
            rows = asst.gw.doc("supplierScorecards", [], top=500)
            if args.get("vendor_no"):
                rows = [r for r in rows if r["vendorNo"] == args["vendor_no"]]
            return _ket_qua({"scorecard": [{k: v for k, v in r.items() if not k.startswith("@")} for r in rows]})
        if ten == "trace_lot":
            from .skills import truy_xuat
            rows = asst.gw.ile_theo_lo(args["lot_no"])
            return _ket_qua(truy_xuat.hanh_trinh(rows) if rows else {"loi": f"Khong co dong nao cua lo {args['lot_no']}."})
        if ten == "create_proposal":
            return _tao_de_xuat(asst, user, args)
        if ten not in {t["name"] for t in toolbox.TOOLS}:
            return _loi(f"Không có tool {ten}.")
        return _ket_qua(toolbox.run_tool(asst, user, ten, args))
    except KeyError as exc:
        return _loi(f"Thiếu tham số {exc}.")
    except Exception as exc:                          # loi BC hay loi du lieu: tra ve cho model doc, khong sap server
        log.warning("MCP tool %s hong: %s", ten, exc)
        return _loi(f"Không chạy được {ten}: {str(exc)[:400]}")


def _tao_de_xuat(asst: Any, user: dict[str, Any], a: dict[str, Any]) -> dict[str, Any]:
    from .skills import replenishment

    if user.get("role") not in VAI_GHI_DUOC:
        return _loi("Vai trò này không được ghi đề xuất.")
    loai, ma = a.get("action_type", ""), (a.get("item_no") or "").strip()
    try:
        so = float(a.get("quantity") or 0)
    except (TypeError, ValueError):
        return _loi("Số lượng không hợp lệ.")
    ly_do = (a.get("rationale") or "").strip()
    if not ly_do:
        return _loi("Đề xuất phải có lý do.")
    mat_hang = next((i for i in asst.gw.items() if i["itemNo"] == ma), None)
    if not mat_hang:
        return _loi(f"Không có mặt hàng {ma}. Dùng find_item để tra mã trước.")
    tu = a.get("from_location") or (asst.gw.central_wh if loai == "Transfer" else user.get("store_code") or "")
    den = a.get("to_location") or ""
    if loai == "Transfer" and (not den or den == tu):
        return _loi("Transfer cần địa điểm nhận khác địa điểm nguồn.")
    if loai in ("Transfer", "WriteOff"):
        if so <= 0:
            return _loi("Số lượng phải lớn hơn 0.")
        # Chan o lop tool, khong o model. Model de xuat 300 cai khi nguon con 120 thi dung o day.
        ton = next((r["qty"] for r in asst.gw.stock_by_location(ma) if r["locationCode"] == tu), 0.0)
        if so > ton:
            return _loi(f"{mat_hang['description']} tại {tu} chỉ còn {ton:g}, không ghi đề xuất {so:g}.")

    tham_chieu = f"MCP|{ma}|{tu}|{den}"
    if tham_chieu in asst.gw.de_xuat_dang_co():
        return _loi("Đã có đề xuất đang hiệu lực cho đúng mặt hàng và tuyến này, không ghi thêm bản nữa.")
    kich_ban = "StoreReplenishment" if loai == "Transfer" else "InventoryHealth"
    tao = asst.gw.create_proposal(
        scenario=kich_ban, action_type=loai, item_no=ma, from_loc=tu, to_loc=den, quantity=so,
        reference_key=tham_chieu, rationale=ly_do, priority=60,
        evidence={"nguon": "mcp", "nguoi_goi": user["user_id"]}, run_id=asst.run_id, model_name="mcp-client")
    prop = {"proposal_id": tao.get("proposalId") or str(uuid.uuid4()), "bc_id": tao["id"], "scenario": kich_ban,
            "action_type": loai, "status": "Proposed", "item_no": ma, "from_loc": tu, "to_loc": den, "quantity": so,
            "max_quantity": so, "rationale": ly_do, "evidence": {"nguon": "mcp"}, "requested_by": user["user_id"],
            "created_at": asst.mem.now().isoformat(), "item_desc": mat_hang["description"],
            "value_vnd": so * asst.gw.unit_cost(ma), "item_category": ""}
    asst.mem.save_proposal(prop)
    gui = replenishment._to_dispatchers(asst, prop, {"itemNo": ma, "description": mat_hang["description"]}, None)
    asst._deliver(gui)
    ban = asst.mem.proposal(prop["proposal_id"]) or prop
    return _ket_qua({
        "proposal_id": prop["proposal_id"], "status": ban.get("status"), "policy": ban.get("policy_rule"),
        "chung_tu": ban.get("result_doc") or "", "nguoi_duoc_bao": sorted({d.user_id for d in gui}),
        "ghi_chu": ("Trợ lý đã tự làm theo policy." if ban.get("status") == "Executed"
                    else "Đề xuất đang chờ người duyệt. Chưa có chứng từ nào được tạo."),
    })


# ---------------------------------------------------------------- JSON-RPC
def xu_ly(asst: Any, user_id: str, tin: dict[str, Any]) -> dict[str, Any] | None:
    """Mot thong diep JSON-RPC. Tra None voi notification (khong co id)."""
    phuong_thuc, ma_tin = tin.get("method"), tin.get("id")
    tham_so = tin.get("params") or {}

    def tra(ket_qua: Any) -> dict[str, Any]:
        return {"jsonrpc": "2.0", "id": ma_tin, "result": ket_qua}

    def loi(ma: int, cau: str) -> dict[str, Any]:
        return {"jsonrpc": "2.0", "id": ma_tin, "error": {"code": ma, "message": cau}}

    if ma_tin is None:                                   # notifications/initialized va cac notification khac
        return None
    if phuong_thuc == "initialize":
        return tra({"protocolVersion": tham_so.get("protocolVersion") or PHIEN_BAN_GIAO_THUC,
                    "capabilities": {"tools": {"listChanged": False}},
                    "serverInfo": {"name": TEN_SERVER, "version": "0.1.0"}, "instructions": HUONG_DAN})
    if phuong_thuc == "ping":
        return tra({})
    if phuong_thuc == "tools/list":
        return tra({"tools": _tools()})
    if phuong_thuc == "tools/call":
        user = asst.mem.user(user_id)
        if not user:
            return loi(-32001, f"Không nhận ra người dùng {user_id}.")
        ten = tham_so.get("name", "")
        log.info("MCP %s goi %s %s", user_id, ten, json.dumps(tham_so.get("arguments") or {}, ensure_ascii=False)[:300])
        return tra(goi_tool(asst, user, ten, tham_so.get("arguments") or {}))
    return loi(-32601, f"Không hỗ trợ {phuong_thuc}.")
