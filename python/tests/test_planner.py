"""Kiem tra lop planner: chuoi tool that, so lieu song, ranh gioi khi khong co ban ghi."""
from __future__ import annotations

import pytest

from assistant.core import Assistant
from assistant.memory import Memory
from assistant.planner import ReplayPlanner, _resolve
from bc_agent.mock_client import MockBCClient


@pytest.fixture()
def asst():
    a = Assistant(MockBCClient(), Memory(":memory:"))
    a.policy.shadow = False
    return a


EVENT = "thứ Bảy này nhà hàng nhận tiệc 150 khách, mỗi khách một phần tráng miệng, ngân sách 600, trời nóng nên tránh kem, kho còn gì ghép được không"
REPLAN = "sếp chốt dùng kem được, nhưng thành 220 khách, mỗi khách hai viên, ngân sách giữ nguyên nhé"
WET = "góc kho bị mưa dột, mấy thùng Flavored syrup ướt nhãn chưa đếm được, giờ xử lý sao"


def test_resolve_path():
    rows = [{"itemNo": "A", "qty": 3}, {"itemNo": "B", "qty": 5}]
    assert _resolve(rows, "#itemNo=B.qty") == 5
    assert _resolve(rows, "@sum:qty") == 8
    assert _resolve(rows, "@len") == 2
    assert _resolve(rows, "#itemNo=Z.qty") is None


def test_ke_hoach_dung_so_that_khong_phai_so_chep(asst):
    """Con so trong cau tra loi phai doc lai tu du lieu: sua ton kho thi cau tra loi phai doi."""
    qty = sum(float(r["quantityOnHand"]) for r in asst.gw.client.data["inventoryHealthLines"]
              if r["itemNo"] == "33310" and r["locationCode"] == "W0003")
    out = asst.handle_message("tuan.s0005", EVENT)
    assert f"{int(qty):,}".replace(",", ".") in out[0].text
    # Choco pillar o kho nam trong ba lo, cong 12 vao mot lo la du
    first = next(r for r in asst.gw.client.data["inventoryHealthLines"]
                 if r["itemNo"] == "33310" and r["locationCode"] == "W0003")
    first["quantityOnHand"] = float(first["quantityOnHand"]) + 12
    out2 = asst.handle_message("tuan.s0005", EVENT)
    assert f"{int(qty) + 12:,}".replace(",", ".") in out2[0].text


def test_khong_co_ban_ghi_thi_noi_thang(asst):
    out = asst.handle_message("trang.sc", "tháng sau mình mở cửa hàng ở Nha Trang thì đẩy bao nhiêu hàng ban đầu")
    assert "chưa trả lời được" in out[0].text
    assert out[0].card is None


def test_doi_rang_buoc_thi_doi_ke_hoach(asst):
    """220 khach thay vi 150: ke hoach phai chuyen tu mot nguon sang hai nguon."""
    asst.handle_message("tuan.s0005", EVENT)
    out = asst.handle_message("tuan.s0005", REPLAN)
    txt = out[0].text
    assert "S0010" in txt and "120" in txt and "100" in txt
    plan = asst.mem.recall(f"plan:{out[0].ref}")
    assert len(plan["drafts"]) == 3


def test_replan_can_co_ke_hoach_truoc(asst):
    """KB-3 la buoc tiep theo cua KB-1. Hoi thang '220 khach' ma chua co ke hoach thi khong khop."""
    out = asst.handle_message("tuan.s0005", REPLAN)
    assert "chưa trả lời được" in out[0].text


def test_de_xuat_tu_ke_hoach_van_qua_policy(asst):
    """Ke hoach do model dung khong duoc di tat: van policy do, van nguoi duyet do."""
    asst.handle_message("tuan.s0005", EVENT)
    ref = asst.handle_message("tuan.s0005", REPLAN)[0].ref
    asst.handle_action("tuan.s0005", "plan_apply", ref, {})
    props = {p["item_no"] + "|" + p["from_loc"]: p for p in asst.mem.proposals()}
    auto = props["33310|W0003"]
    assert auto["status"] == "Executed" and auto["policy_rule"] == "P-01"       # 120 x 1,1 = 132 tu kho trung tam, duoi 200
    inter = props["33310|S0010"]
    assert inter["status"] == "Proposed" and inter["policy_rule"] == "P-02"     # chuyen giua hai cua hang
    nuts = props["33323|W0003"]
    assert nuts["status"] == "Proposed"                                         # 220 x 1,1 = 242 vuot han muc 200


def test_khong_ghi_de_xuat_hai_lan(asst):
    asst.handle_message("tuan.s0005", EVENT)
    ref = asst.handle_message("tuan.s0005", REPLAN)[0].ref
    asst.handle_action("tuan.s0005", "plan_apply", ref, {})
    n = len(asst.mem.proposals())
    out = asst.handle_action("tuan.s0005", "plan_apply", ref, {})
    assert len(asst.mem.proposals()) == n and "đã ghi" in out[0].text


def test_ke_hoach_thieu_thong_tin_thi_hoi_chu_khong_ghi(asst):
    """KB-1 thieu mot dieu kien (tiec co giu lanh duoc khong): tro ly hoi lai va KHONG soan de xuat nao."""
    out = asst.handle_message("tuan.s0005", EVENT)
    assert "giữ lạnh" in out[0].card.body
    assert all(a.id != "plan_apply" for a in out[0].card.actions)
    assert asst.mem.proposals() == []


def test_rule_bat_nham_thi_tra_lai_cho_planner(asst):
    """'xu ly sao' bi rule bat thanh INVESTIGATE. Khong giai duoc thi phai roi ve planner,
    khong duoc tra ve cau hoi lai vo nghia."""
    out = asst.handle_message("kho.w0003", WET)
    assert "30091" in out[0].text and "Excess" in out[0].text


def test_thiet_hai_that_khac_so_sach(asst):
    """Diem cua kich ban hang uot: gia tri so sach la mot chuyen, con bao nhieu thang ban het moi
    quyet dinh xu ly. Ca hai deu la so that doc tu tool, khong phai so chep."""
    out = asst.handle_message("kho.w0003", WET)
    assert "1.668,8" in out[0].text             # gia tri so sach cua 596 chai syrup o W0003
    import re
    months = float(re.search(r"chừng ([\d,]+) tháng", out[0].text).group(1).replace(",", "."))
    assert 3 < months < 12                       # tinh ca luong chuyen ra cua hang thi con vai thang, khong phai hai nam


def test_xem_lai_tung_buoc(asst):
    out = asst.handle_message("kho.w0003", WET)
    steps = asst.handle_action("kho.w0003", "plan_steps", out[0].ref, {})
    txt = steps[0].text
    # Ke bang tieng Viet, khong in ten ham ra cho nguoi dung doc
    assert "đang nằm ở những kho và cửa hàng nào" in txt and "Đọc tốc độ bán" in txt
    assert "stock_by_item" not in txt and "sales_rate" not in txt


def test_ban_ghi_khong_khop_thi_khong_doan_bua():
    """Matcher phai doi du moi nhom tu khoa, khong duoc khop mo."""
    rp = ReplayPlanner()
    assert rp.match("cho tôi xin quà") is None
    assert rp.match("thứ bảy có tiệc 150 khách, mỗi khách một phần tráng miệng")["id"] == "KB-1"


def test_matcher_theo_ranh_gioi_tu(asst):
    """Loi da bat duoc khi QA: 'quan ly ca' khop nham tu khoa 'qua' cua KB-1."""
    out = asst.handle_message("minh.s0002", "khách mua nguyên thùng nên em giảm thêm, có báo quản lý ca")
    assert "Choco pillar" not in out[0].text


def test_kho_ghi_duoc_de_xuat_tu_ke_hoach(asst):
    """Kho la nguoi phat hien lo am, phai ghi duoc de xuat chan xuat lo."""
    ref = asst.handle_message("kho.w0003", WET)[0].ref
    out = asst.handle_action("kho.w0003", "plan_apply", ref, {})
    assert "chưa được ghi đề xuất" not in out[0].text
    assert len(asst.mem.proposals()) == 2


def test_brief_cho_kho(asst):
    asst.handle_message("lan.s0001", "sắp hết Croissant plain")
    out = asst.morning_brief("kho.w0003")
    assert "chờ ship" in out[0].text and "Croissant" in out[0].text


def test_blockpurchase_khong_sinh_transfer_order(asst):
    """Loi da bat duoc khi QA: de xuat BlockPurchase tung tao mot Transfer Order 0 cai
    di tu kho trung tam ve chinh kho trung tam, roi bao kho di ship."""
    ref = asst.handle_message("kho.w0003", WET)[0].ref
    out = asst.handle_action("kho.w0003", "plan_apply", ref, {})
    assert asst.gw._transfers == {}
    assert not [d for d in out if "cần ship" in d.text]
    bp = [p for p in asst.mem.proposals() if p["action_type"] == "BlockPurchase"][0]
    assert bp["status"] == "Executed" and not bp["result_doc"]


def test_baseline_chot_truoc_khi_tro_ly_lam_gi(asst):
    """Baseline phai la anh chup luc khoi tao. Neu tinh sau thi chinh viec tro ly da lam
    se lam dep bao cao cua chinh no."""
    from assistant.skills import kpi
    before = kpi.baseline(asst)["repl"]["at_risk"]
    asst.handle_message("lan.s0001", "sắp hết Croissant plain")
    assert kpi.baseline(asst)["repl"]["at_risk"] == before
    assert asst.gw.risky_suggestions(200).__len__() < before      # hien trang da doi that


def test_ket_qua_do_bang_dung_don_vi_cua_baseline(asst):
    from assistant.skills import kpi
    ref = asst.handle_message("kho.w0003", WET)[0].ref
    asst.handle_action("kho.w0003", "plan_apply", ref, {})
    r = kpi.result(asst)
    assert r["covered_vnd"] > 0
    labels = dict(kpi.card(asst).facts)
    assert "chưa đo được" not in labels["Giá trị tồn xấu đã có hướng xử lý"]
