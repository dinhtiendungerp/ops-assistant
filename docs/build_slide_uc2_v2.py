"""Dung lai bo slide POC tu template NaviWorld: kien truc moi (3 hinh theo comment cua Hung dev), cac kich ban UC2 va UC3
theo dang dau vao / thao tac / dau ra, va SPEAKER NOTE chi tiet cho tung slide.

Chay:  cd docs; python build_slide_uc2_v2.py
Nguon: file goc trong Downloads (giu slide bia va bia phan de khong mat do hoa cua template), anh trong docs/anh-uc2,
docs/uc2 va docs/kien-truc.
"""
from __future__ import annotations

import copy
from pathlib import Path

from PIL import Image
from pptx import Presentation
from pptx.dml.color import RGBColor
from pptx.enum.shapes import MSO_SHAPE
from pptx.enum.text import MSO_ANCHOR, PP_ALIGN
from pptx.util import Emu, Inches, Pt

ROOT = Path(__file__).resolve().parent.parent
GOC = Path.home() / "Downloads" / "Marou_POC_Business_Central_AI_Agent_v0.1(1).pptx"
RA = ROOT / "docs" / "12 Marou POC - Kien truc va kich ban UC2 (slide).pptx"
ANH = ROOT / "docs" / "anh-uc2"
ANH_DEMO = ROOT / "docs" / "anh-demo"
KT = ROOT / "docs" / "kien-truc"
UC2 = ROOT / "docs" / "uc2"

NAVY = RGBColor(0x00, 0x1F, 0x60)
RED = RGBColor(0xD7, 0x19, 0x20)
BODY = RGBColor(0x33, 0x33, 0x33)
MUTED = RGBColor(0x66, 0x70, 0x85)
WHITE = RGBColor(0xFF, 0xFF, 0xFF)
BOXBG = RGBColor(0xF5, 0xF7, 0xFA)
BAND = RGBColor(0xEA, 0xF4, 0xF7)
GREEN = RGBColor(0x2F, 0x6B, 0x35)
AMBER = RGBColor(0xB0, 0x78, 0x0A)
FONT = "Aptos"
W, H = 17.4167, 9.7917
FOOTER = "Marou POC · Business Central & AI Agent · NaviWorld"


# ---------------------------------------------------------------- khung
def txt(s, l, t, w, h, noi_dung, size=21, bold=False, color=BODY, align=PP_ALIGN.LEFT, space=6, line=None):
    tb = s.shapes.add_textbox(Inches(l), Inches(t), Inches(w), Inches(h))
    tf = tb.text_frame
    tf.word_wrap = True
    tf.margin_left = tf.margin_right = tf.margin_top = tf.margin_bottom = 0
    dong = noi_dung if isinstance(noi_dung, (list, tuple)) else [noi_dung]
    for i, d in enumerate(dong):
        p = tf.paragraphs[0] if i == 0 else tf.add_paragraph()
        p.alignment = align
        p.space_after = Pt(space)
        if line:
            p.line_spacing = line
        r = p.add_run()
        r.text = str(d)
        r.font.size = Pt(size)
        r.font.bold = bold
        r.font.name = FONT
        r.font.color.rgb = color
    return tb


def hop(s, l, t, w, h, fill=BOXBG, vien=None, top_bar=None):
    sh = s.shapes.add_shape(MSO_SHAPE.RECTANGLE, Inches(l), Inches(t), Inches(w), Inches(h))
    sh.fill.solid()
    sh.fill.fore_color.rgb = fill
    if vien:
        sh.line.color.rgb = vien
        sh.line.width = Pt(1)
    else:
        sh.line.fill.background()
    sh.shadow.inherit = False
    if top_bar:
        b = s.shapes.add_shape(MSO_SHAPE.RECTANGLE, Inches(l), Inches(t), Inches(w), Inches(0.08))
        b.fill.solid()
        b.fill.fore_color.rgb = top_bar
        b.line.fill.background()
        b.shadow.inherit = False
    return sh


def anh(s, duong, l, t, w, h):
    """Dat anh vua khung, giu ty le, can giua khung."""
    duong = Path(duong)
    iw, ih = Image.open(duong).size
    ty = min(w / (iw / 96), h / (ih / 96)) if iw and ih else 1
    aw, ah = (iw / 96) * ty, (ih / 96) * ty
    return s.shapes.add_picture(str(duong), Inches(l + (w - aw) / 2), Inches(t + (h - ah) / 2), Inches(aw), Inches(ah))


def anh_cat(s, duong, l, t, w, h, phan_tren=1.0):
    """Anh cao qua khung: cat lay phan tren `phan_tren` (ty le chieu cao) roi moi dat."""
    duong = Path(duong)
    im = Image.open(duong)
    if phan_tren < 1.0:
        im = im.crop((0, 0, im.width, int(im.height * phan_tren)))
        tam = ROOT / "docs" / "anh-uc2" / f"_cat-{duong.stem}.png"
        im.save(tam)
        duong = tam
    return anh(s, duong, l, t, w, h)


def slide(pr, eyebrow="", tieu_de="", phu="", ghi_chu=""):
    s = pr.slides.add_slide(pr.slide_layouts[10])       # Blank
    if eyebrow:
        txt(s, 1.20, 0.44, 14.06, 0.38, eyebrow, 18, True, RED)
    if tieu_de:
        txt(s, 1.20, 0.95, 15.02, 0.9, tieu_de, 41, True, NAVY)
    if phu:
        txt(s, 1.20, 1.92, 15.00, 0.62, phu, 20, False, BODY)
    txt(s, 3.70, 9.03, 10.94, 0.26, FOOTER, 13.5, False, MUTED, PP_ALIGN.CENTER)
    if ghi_chu:
        note(s, ghi_chu)
    return s


def bang_nguon(s, noi_dung):
    hop(s, 1.20, 8.29, 14.95, 0.56, BAND)
    txt(s, 1.40, 8.41, 14.58, 0.42, noi_dung, 17, False, NAVY)


def note(s, noi_dung):
    s.notes_slide.notes_text_frame.text = noi_dung.strip()


def ba_cot_io(s, dau_vao, thao_tac, dau_ra, l=1.20, w=5.83, t=2.92):
    """Cot trai kieu template: DAU VAO / THAO TAC / DAU RA."""
    for i, (nhan, ndung) in enumerate((("ĐẦU VÀO", dau_vao), ("THAO TÁC", thao_tac), ("ĐẦU RA", dau_ra))):
        y = t + i * 1.76
        txt(s, l, y, w, 0.4, nhan, 20, True, NAVY)
        txt(s, l, y + 0.47, w, 1.27, ndung, 19, False, BODY, space=3, line=1.05)


def the_ngang(s, muc, t=2.95, h=2.7, l=1.20, w=14.95, khoang=0.28):
    """Day hop ngang: muc = [(tieu de, [dong...], mau vach)]"""
    n = len(muc)
    bw = (w - khoang * (n - 1)) / n
    for i, (ten, dong, mau) in enumerate(muc):
        x = l + i * (bw + khoang)
        hop(s, x, t, bw, h, BOXBG, top_bar=mau)
        txt(s, x + 0.25, t + 0.3, bw - 0.5, 0.6, ten, 22, True, mau)
        txt(s, x + 0.25, t + 1.0, bw - 0.5, h - 1.2, dong, 18, False, BODY, space=5, line=1.05)


def mui_ten(s, l, t, w):
    c = s.shapes.add_shape(MSO_SHAPE.RIGHT_ARROW, Inches(l), Inches(t), Inches(w), Inches(0.3))
    c.fill.solid()
    c.fill.fore_color.rgb = RGBColor(0xB9, 0xC4, 0xD4)
    c.line.fill.background()
    c.shadow.inherit = False


def xoa_slide(pr, giu_index):
    """Giu lai cac slide theo chi so 0-based, xoa het phan con lai."""
    xml = pr.slides._sldIdLst
    ids = list(xml)
    for i, sid in enumerate(ids):
        if i in giu_index:
            continue
        pr.part.drop_rel(sid.rId)
        xml.remove(sid)


def doi_chu(s, cu, moi):
    for sh in s.shapes:
        if not sh.has_text_frame:
            continue
        for p in sh.text_frame.paragraphs:
            for r in p.runs:
                if cu in r.text:
                    r.text = r.text.replace(cu, moi)


# ---------------------------------------------------------------- dung deck
# Xoa slide cu roi LUU TAM va MO LAI: neu thao tac tiep tren cung doi tuong, part cua slide da xoa van con trong goi va
# slide moi lay trung ten part (canh bao "Duplicate name: ppt/slides/slide3.xml"), file mo ra co the hong.
TAM = ROOT / "docs" / "_tam-slide-goc.pptx"
_pr = Presentation(str(GOC))
xoa_slide(_pr, {0, 2})                                  # giu bia va bia phan UC2
_pr.save(str(TAM))
pr = Presentation(str(TAM))
bia, bia_phan = pr.slides[0], pr.slides[1]
doi_chu(bia, "Finance & SCM", "UC2 Inventory Health & Traceability")
note(bia, """
Mở đầu. Đây là phiên POC thứ hai, tập trung UC2 Inventory Health & Traceability, cộng phần trợ lý AI (UC10) chạy xuyên suốt.
Nói ngay ba điều để người nghe có khung: (1) mọi con số do Business Central và LS Central tính, trợ lý đọc lại chứ không tự tính;
(2) trợ lý chỉ ghi đề xuất, chứng từ chỉ sinh ra khi người của Marou bấm Duyệt, và sinh ở trạng thái nháp; (3) phần AI bật tắt được
và có trần chi phí. Dữ liệu trình diễn là bộ mô phỏng do NaviWorld dựng trên danh mục thật của Marou, không phải số liệu vận hành thật.
""")
note(bia_phan, """
Chuyển phần. Nhắc lại phạm vi: UC2 gồm sức khỏe tồn kho theo lô, hạn dùng, truy xuất lô; UC3 có thêm phần nhắc post nhận hàng vì
khảo sát cho thấy đây là điểm đau thật của Marou. Bộ slide đi theo ba bước: trợ lý làm việc thế nào, bản đồ tính năng, rồi từng kịch bản.
Nếu buổi họp bị rút ngắn thì bỏ phần kịch bản chi tiết, giữ ba slide kiến trúc đầu.
""")

# ---- 1. Kien truc, ba hinh
s = slide(pr, "KIẾN TRÚC · BƯỚC 1", "Trợ lý vận hành làm việc thế nào",
          "Một vòng: đọc số đã tính, suy luận trên đó, rồi đề xuất và nhắc. Người duyệt quyết định.")
anh(s, KT / "kien-truc-tong-quan.png", 1.20, 2.55, 14.95, 5.6)
note(s, """
Slide mở đầu phần kiến trúc, dùng để người mới nắm được toàn bộ hệ thống trong một phút.
Đi theo mũi tên: người của Marou hỏi hoặc bấm nút trên thẻ, trợ lý ĐỌC số Business Central và LS đã tính (sức khỏe tồn kho theo lô,
đề xuất bổ sung của LS, dự báo, sổ kho, đơn mua, khuyến mãi). Bước SUY LUẬN là nơi có AI: trợ lý ghép số với bộ nhớ (việc đang chờ,
đề xuất đã bị từ chối) và kiến thức (cách LS tính, ngưỡng Marou đặt, policy duyệt), model chọn việc và viết lời, nhưng mọi con số phải
có sẵn trong dữ liệu. Bước ĐỀ XUẤT VÀ NHẮC: ghi đề xuất vào BC ở trạng thái Proposed, gửi thẻ cho đúng người duyệt, nhắc qua chat và
email, tự quét mỗi sáng, theo dõi đến khi chứng từ được post.
Băng dưới cùng là ranh giới quan trọng nhất: người bấm Duyệt thì BC mới tạo Transfer Order, Purchase Order hoặc dòng Item Journal hủy,
và đều ở trạng thái nháp. Trợ lý không release, không post.
Câu khách hay hỏi: "AI có tự sửa dữ liệu không?" Trả lời: không, nó chỉ ghi vào bảng đề xuất; chứng từ do BC tạo dưới tên người duyệt.
""")

s = slide(pr, "KIẾN TRÚC · BƯỚC 2", "Bản đồ tính năng",
          "Tên tính năng theo lớp. Chi tiết từng tính năng nằm ở các slide kịch bản phía sau.")
anh(s, KT / "ban-do-tinh-nang.png", 1.20, 2.5, 14.95, 5.75)
note(s, """
Slide này trả lời câu "hệ thống có những gì", chỉ tên tính năng, chưa đi vào chi tiết, để buổi họp ngắn vẫn đủ thông tin.
Hai cột dọc là thứ xuyên suốt mọi lớp. Bảo mật và quyền: kết nối bằng S2S OAuth qua Entra app, permission set tách riêng cho agent và
người duyệt, phân quyền theo vai và theo company, agent không có quyền post chứng từ, có nhật ký agent, secret không nằm trong mã nguồn,
và chỉ gửi cho model phần kết quả đã lọc chứ không gửi cả bảng dữ liệu. Vận hành: lịch chạy nền mỗi sáng, bộ nhớ trợ lý lưu trên đĩa,
bộ nhớ đệm cho lệnh đọc BC, định tuyến rule trước model sau để tiết kiệm token, bản đối chiếu độc lập bằng Python, bộ test tự động.
Bảy lớp ngang đọc từ trên xuống: Giao diện, Kiểm soát, Trợ lý, Năng lực AI, Dữ liệu của trợ lý, Model, Business Central.
Lớp "Năng lực AI" với bốn nhóm Tóm tắt, Tạo sinh nội dung, Khám phá và phân tích, Tự động hóa là kim chỉ nam đã chốt với Marou:
mọi tính năng AI phải thuộc một trong bốn nhóm, nếu không thì đó là tính năng ứng dụng thông thường.
Nếu khách hỏi về hạ tầng như container, GPU, vector store: nói thẳng là POC này không dùng, vì số liệu do BC tính và model chỉ nhận
kết quả đã lọc; không cần vector store hay GPU riêng.
""")

s = slide(pr, "KIẾN TRÚC · BƯỚC 3", "Chi tiết từng lớp",
          "Dùng khi cần đi sâu; có thể bỏ qua nếu buổi họp bị giới hạn thời gian.")
anh(s, KT / "kien-truc-chi-tiet.png", 0.75, 2.4, 15.9, 5.9)
note(s, """
Slide tham chiếu, không cần đọc hết. Chỉ vào ba chỗ nếu có người hỏi:
1. Dải màu hồng nhạt ở trên là trợ lý NaviWorld tự host, bên trong chia bốn cột: hiểu câu hỏi (rule trước, model sau), skill theo use case,
   kiểm soát (policy, chặn ở lớp tool, ngân sách), lưu vết và kết nối.
2. Dải vàng ở giữa là "AI ở đâu trong UC2": 12 tính năng đã chạy thật, xếp theo bốn nhóm năng lực, kèm phép kiểm chung.
3. Khối xanh dưới cùng là Business Central: lớp 1 dữ liệu chuẩn, lớp 2 tính toán bằng AL và LS, lớp 3 đề xuất và người duyệt.
Điểm cần nhấn: tắt trợ lý đi thì ba lớp trong BC vẫn chạy, số liệu và dashboard không đổi. Đó là lý do POC này không tạo ra phụ thuộc
vào NaviWorld ở mức dữ liệu.
Con số cập nhật tới 16/09/2026: 34 API page chỉ đọc, hai company NWV-MAROU và NWV-DAKAO, app NWV Marou Agent 1.6.1.0.
""")

# ---- Hai company
s = slide(pr, "KIẾN TRÚC · HAI ĐƠN VỊ", "Marou sản xuất và Dakao bán lẻ trên cùng một môi trường",
          "Mỗi company một trợ lý riêng, dữ liệu và bộ nhớ tách biệt; hàng đi từ Marou thẳng tới từng cửa hàng.")
the_ngang(s, [
    ("NWV-MAROU · sản xuất", ["Quản lý theo lô và hạn dùng",
                              "Kho trung tâm W0003",
                              "Đề xuất chuyển hàng nội bộ",
                              "Vai: kho, Supply Chain, điều phối"], NAVY),
    ("Luồng hàng", ["LS Central tính nhu cầu từng cửa hàng",
                    "Trợ lý ghi đề xuất loại Purchase",
                    "Người duyệt bấm Duyệt: BC tạo Purchase Order",
                    "Người mua bấm Gửi đơn: sang Marou thành Sales Order"], RED),
    ("NWV-DAKAO · bán lẻ", ["Mua thẳng từ Marou, giao tới từng cửa hàng",
                            "Không qua kho trung tâm của Dakao",
                            "Hạn dùng suy từ đợt giao",
                            "Vai: quản lý cửa hàng, Retail Ops"], NAVY),
], t=2.95, h=3.1)
txt(s, 1.20, 6.35, 14.95, 0.5, "Đã chạy thật hai đầu: đơn mua HO106200 ở NWV-DAKAO, gửi sang NWV-MAROU thành Sales Order S90013 cho khách DAKAO.",
    20, True, NAVY)
txt(s, 1.20, 6.95, 14.95, 1.1,
    ["Intercompany chuẩn của Business Central: IC Partner hai chiều, tự gửi và tự nhận. Hai đơn đều chưa post, người của Marou xử lý tiếp như đơn thường.",
     "Người dùng chọn đơn vị ngay trên giao diện; thẻ và link mở đúng company trong Business Central."],
    19, False, BODY, space=4)
bang_nguon(s, "Trạng thái 16/09/2026. Dữ liệu hai company hiện là bản sao của bộ mô phỏng; dữ liệu bán lẻ riêng cho Dakao sẽ dựng ở bước sau.")
note(s, """
Giải thích vì sao có hai company: Marou là đơn vị sản xuất, có quản lý lô và hạn dùng. Dakao là đơn vị bán lẻ, không quản lý lô.
Hàng đi từ Marou sang Dakao bằng nghiệp vụ mua bán giữa hai công ty, và anh Dũng đã chốt là giao thẳng tới từng cửa hàng chứ không
qua kho trung tâm của Dakao.
Điều này đổi cách trợ lý đề xuất: bên Marou là đề xuất chuyển hàng nội bộ (Transfer Order), bên Dakao là đề xuất đặt mua (Purchase Order)
với nhà cung cấp là chính Marou. Số lượng vẫn do LS Central tính, trợ lý không tự tính lại.
Bằng chứng đã chạy thật: đơn HO106199 trong company NWV-DAKAO.
Tự động hóa hai chiều đã chạy: đây chính là vấn đề số 3 trong khảo sát của Marou. Dùng Intercompany chuẩn của Business Central,
bật được vì hai company chung một môi trường. Người mua bấm "Gửi đơn sang Marou" trên thẻ; BC release đơn mua, đẩy sang hộp thư của
company kia, và bên đó tự tạo Sales Order. Bằng chứng: đơn HO106200 bên Dakao thành S90013 bên Marou, khách hàng DAKAO, cùng mặt hàng
và số lượng.
Ranh giới vẫn giữ: trợ lý không tự bấm gửi, vì gửi kéo theo release đơn, đó là quyết định của người mua.
Hai điểm cần Marou xác nhận khi triển khai thật: kho xuất hàng bên Marou (đơn bán hiện chưa gán địa điểm xuất), và có cho tự động post
hai đầu hay dừng ở mức tạo chứng từ như bây giờ.
""")

# ---- AI o dau
s = slide(pr, "AI · BỐN NHÓM NĂNG LỰC", "12 tính năng AI đã chạy thật trong UC2",
          "Mỗi tính năng phải thuộc một trong bốn nhóm; không thuộc nhóm nào thì đó là tính năng ứng dụng.")
nhom = [("Tóm tắt", [("S1", "Brief buổi sáng do AI viết"), ("S2", "Giải thích lô bằng lời"), ("S3", "Báo cáo tuần hàng hủy")], AMBER),
        ("Tạo sinh nội dung", [("G1", "Lý do đề xuất viết lại"), ("G2", "Biên bản hủy"), ("", "Email nhắc post nhận hàng")], RGBColor(0xA4, 0x55, 0x2A)),
        ("Khám phá và phân tích", [("D1", "Hỏi đáp tự do"), ("D4", "Phương án cho lô cận date"), ("D3", "Phát hiện bất thường"), ("D2", "Nguyên nhân hàng hủy")], RGBColor(0x2F, 0x6B, 0x8A)),
        ("Tự động hóa", [("A1", "Đề xuất có người duyệt"), ("A2", "Quét sáng mỗi ngày"), ("A3", "Luồng hủy khép kín")], GREEN)]
bw = (14.95 - 0.3 * 3) / 4
for i, (ten, ds, mau) in enumerate(nhom):
    x = 1.20 + i * (bw + 0.3)
    hop(s, x, 2.95, bw, 3.5, BOXBG, top_bar=mau)
    txt(s, x + 0.22, 3.2, bw - 0.44, 0.75, ten, 21, True, mau, line=0.95)
    for j, (ma, mo) in enumerate(ds):
        y = 4.05 + j * 0.6
        if ma:
            txt(s, x + 0.22, y, 0.62, 0.35, ma, 18, True, mau)
        txt(s, x + 0.86, y, bw - 1.1, 0.55, mo, 18, False, BODY, space=0, line=0.95)
txt(s, 1.20, 6.75, 14.95, 0.45, "Phép kiểm chung cho mọi tính năng AI", 21, True, NAVY)
txt(s, 1.20, 7.3, 14.95, 0.95,
    ["Mọi chữ số model viết phải có trong dữ liệu code đưa; mọi dòng hoặc phương án model chọn phải nằm trong danh sách code đưa.",
     "Sai một điều là thay bằng câu mẫu, thẻ ghi rõ “Người soạn: mẫu có sẵn” kèm lý do. Tắt AI thì tính năng vẫn chạy bằng mẫu."],
    18, False, BODY, space=3)
bang_nguon(s, "Còn chờ khảo sát Marou: G3 chương trình giảm giá cận date, G4 và A4 thu hồi lô, S4 tóm tắt tin báo sự cố, D5 học ngưỡng.")
note(s, """
Đây là slide trả lời thẳng câu hỏi khách chắc chắn hỏi: "AI nằm ở đâu, hay chỉ là phần mềm thường?"
Bốn nhóm này là kim chỉ nam đã chốt. Đọc lướt tên 12 tính năng, đừng giải thích từng cái ở đây vì các slide sau sẽ diễn.
Phần quan trọng nhất là khối "Phép kiểm chung" ở dưới. Giải thích bằng một ví dụ thật: hôm 15/09 model viết đoạn giải thích cho một lô
Choco nuts và tự suy ra "ngày 20/07" từ mã lô L260720, con số đó không có trong dữ liệu đưa cho model, nên hệ thống loại đoạn đó và
thay bằng câu mẫu, thẻ ghi rõ lý do. Đó là cách chúng tôi chặn việc model bịa số.
Nếu khách hỏi "vậy AI có thể sai không": trả lời là model vẫn có thể viết câu chưa hay, nhưng không thể đưa ra con số không có trong
dữ liệu, vì mọi con số đều bị đối chiếu trước khi hiện ra màn hình.
Bốn tính năng chưa làm nằm ở băng dưới; nói rõ lý do là cần Marou xác nhận quy trình hoặc dữ liệu, không phải vì kỹ thuật.
""")

# ---- Kiem soat
s = slide(pr, "AI · KIỂM SOÁT", "Từ đề xuất đến chứng từ: bốn chốt chặn",
          "Không có đường tắt nào cho agent ghi thẳng vào chứng từ.")
the_ngang(s, [
    ("1 · Lớp tool", ["Số lượng không vượt tồn nguồn", "Chống trùng theo Reference Key còn hiệu lực trong BC", "Đề xuất từng phần có khóa riêng"], NAVY),
    ("2 · Policy", ["Mỗi loại việc: tự làm, đưa người duyệt, hoặc không bao giờ làm", "Trần giá trị, trần số việc mỗi ngày", "Shadow mode khi mới triển khai"], RED),
    ("3 · Người duyệt", ["Thẻ đến đúng vai, kèm số liệu và lý do", "Duyệt hoặc từ chối kèm ghi chú", "Lý do từ chối được nhớ lại"], NAVY),
    ("4 · Business Central", ["Chứng từ tạo ở trạng thái nháp", "Mang số đề xuất để truy ngược", "Người của Marou release và post"], RGBColor(0x23, 0x50, 0x7D)),
], t=2.95, h=3.25)
txt(s, 1.20, 6.6, 14.95, 0.45, "Ngoài ra, phần AI có công tắc và trần chi phí riêng", 22, True, NAVY)
txt(s, 1.20, 7.15, 14.95, 1.05,
    ["Trần 2 USD mỗi ngày và 10 USD cộng dồn; vượt trần thì trợ lý tự quay về câu mẫu chứ không báo lỗi.",
     "Quản trị bật tắt AI ngay trên giao diện; số liệu, dashboard và luồng duyệt không đổi khi tắt. Toàn bộ ngày QA 16/09 tốn 0,085 USD cho 146 lượt gọi."],
    19, False, BODY, space=4)
note(s, """
Slide này dành cho người lo rủi ro: kế toán, kiểm soát nội bộ, IT.
Bốn chốt chặn đọc từ trái sang. Chốt 1 nằm trong code: trợ lý không thể đề xuất chuyển 500 cái khi kho chỉ có 200, và không ghi trùng
một việc đã có đề xuất đang chờ trong BC. Chốt 2 là policy, Marou tự sửa được: mỗi loại việc đặt là tự làm, đưa người duyệt, hay cấm.
Chốt 3 là người duyệt, thẻ đến đúng vai kèm đủ số liệu. Chốt 4 là BC: chứng từ sinh ra ở trạng thái nháp và mang số đề xuất, nên kiểm
toán truy ngược được từ chứng từ về đề xuất và về dòng dữ liệu gốc.
Về chi phí: nói con số thật đo được, 0,085 USD cho cả ngày chạy kiểm thử với 146 lượt gọi model. Nhấn rằng đây là ước tính theo đơn giá
công bố của Azure, còn hóa đơn thật mới là số cuối cùng.
Nếu khách hỏi dữ liệu có ra khỏi Việt Nam không: hiện môi trường demo dùng Azure OpenAI ở Mỹ; khi triển khai, extension của NaviWorld
tự chọn được vùng xử lý, có thể giữ trong Asia Pacific. Đây là điểm cần ghi vào phần governance.
""")

# ---- Danh muc kich ban
s = slide(pr, "KỊCH BẢN", "Danh mục kịch bản trình diễn",
          "Mười bốn kịch bản, mỗi kịch bản một slide: đầu vào, thao tác, đầu ra.")
ds = [("01", "Dashboard sức khỏe tồn kho", "Supply Chain", "UC2"),
      ("02", "Lọc đúng tầng, tìm đúng lô", "Supply Chain", "UC2"),
      ("03", "Vì sao một lô vào tầng đó", "Người kiểm số", "UC2 · S2"),
      ("04", "Độ phủ dữ liệu trước khi tin kết quả", "Supply Chain", "UC2"),
      ("05", "Brief buổi sáng do AI viết", "Supply Chain", "UC2 · S1"),
      ("06", "Hỏi hàng đã hết hạn toàn hệ thống", "Điều phối kho", "UC2"),
      ("07", "Tra tồn tại cửa hàng của mình", "Quản lý cửa hàng", "UC2"),
      ("08", "Phương án cho lô cận date", "Supply Chain", "UC2 · D4"),
      ("09", "Đề xuất và người duyệt", "Supply Chain, điều phối", "UC2 · A1"),
      ("10", "Luồng hủy khép kín", "Người duyệt, kế toán", "UC2 · G2, A3"),
      ("11", "Truy xuất lô và khoanh vùng thu hồi", "QA", "UC2"),
      ("12", "Phát hiện bất thường trong sổ kho", "Supply Chain", "UC2 · D3"),
      ("13", "Nguyên nhân hàng hủy", "Supply Chain, cửa hàng", "UC2 · D2"),
      ("14", "Quét sáng và báo cáo tuần", "Cả nhóm", "UC2 · A2, S3")]
cot_w = [0.9, 7.2, 4.0, 2.85]
x0 = 1.20
y0 = 2.85
hop(s, x0, y0, sum(cot_w), 0.5, NAVY)
for i, ten in enumerate(("MÃ", "KỊCH BẢN", "VAI CHÍNH", "THUỘC UC")):
    txt(s, x0 + sum(cot_w[:i]) + 0.15, y0 + 0.11, cot_w[i] - 0.2, 0.3, ten, 16, True, WHITE)
for r, row in enumerate(ds):
    y = y0 + 0.5 + r * 0.4
    if r % 2 == 0:
        hop(s, x0, y, sum(cot_w), 0.4, RGBColor(0xF7, 0xF9, 0xFC))
    for i, v in enumerate(row):
        txt(s, x0 + sum(cot_w[:i]) + 0.15, y + 0.07, cot_w[i] - 0.2, 0.3, v, 16,
            i == 0, NAVY if i == 0 else BODY)
txt(s, 13.6, 2.85, 2.55, 3.4, ["Nếu thiếu thời gian", "", "Diễn 01, 05, 08, 09, 10.",
                               "Năm kịch bản này đi hết một vòng: nhìn số, được nhắc, chọn cách xử lý, duyệt, ra chứng từ."],
    18, False, BODY, space=5)
note(s, """
Slide điều hướng. Nói trước để người nghe biết đường đi: bốn kịch bản đầu là nhìn và kiểm số liệu, năm kịch bản giữa là trợ lý chủ động
đề xuất và người duyệt quyết, năm kịch bản cuối là phần phân tích và tự động hóa.
Cột "thuộc UC" ghi mã tính năng AI để nối với slide bốn nhóm năng lực phía trước.
Nếu buổi họp bị rút còn 15 phút, diễn năm kịch bản 01, 05, 08, 09, 10; đó là một vòng đủ từ nhìn số tới ra chứng từ.
""")


def kb(ma, tieu_de, vai, dau_vao, thao_tac, dau_ra, hinh=None, nguon="", ghi_chu="", hinh_l=7.50, hinh_t=3.10, hinh_w=8.65, hinh_h=4.85, cat=1.0):
    s = slide(pr, f"KỊCH BẢN {ma}", tieu_de, vai)
    ba_cot_io(s, dau_vao, thao_tac, dau_ra)
    if hinh:
        if cat < 1.0:
            anh_cat(s, hinh, hinh_l, hinh_t, hinh_w, hinh_h, cat)
        else:
            anh(s, hinh, hinh_l, hinh_t, hinh_w, hinh_h)
    if nguon:
        bang_nguon(s, nguon)
    if ghi_chu:
        note(s, ghi_chu)
    return s


kb("01", "Dashboard sức khỏe tồn kho", "Supply Chain · có trong POC",
   "Kết quả tính tồn theo lô, giá trị, hạn dùng và phân tầng do Business Central chạy.",
   "Mở tab Sức khỏe tồn kho. Đọc tổng giá trị và sáu tầng.",
   "5.088,4 nằm ở bốn tầng có vấn đề, chiếm 38,1% của 13.370,2; 82 trên 167 dòng.",
   ANH / "uc2-01-tong-quan.png",
   "Ảnh chụp trên môi trường demo, số liệu của bộ dữ liệu mô phỏng.",
   """
Mở màn bằng con số tiền, không mở bằng tính năng. Câu nói: "Đây là toàn bộ giá trị tồn đang có vấn đề, tính theo từng lô."
Chỉ vào bốn ô lớn: quá hạn, cận date, sắp hết hàng, chậm luân chuyển. Nhấn rằng đây là kết quả do codeunit AL trong Business Central
tính, chạy bằng Job Queue hằng đêm hoặc bấm tay, không phải do trợ lý tính.
Ngày chốt hiển thị ngay trên màn hình; nếu ngày chốt khác ngày hôm nay thì mọi con số phía sau đều theo ngày chốt đó.
Nếu khách hỏi vì sao tổng lại là giá vốn chứ không phải giá bán: vì đây là giá trị tồn kho trên sổ, khớp với Item Ledger Entry.
""")

kb("02", "Lọc đúng tầng, tìm đúng lô", "Supply Chain · có trong POC",
   "Danh sách sức khỏe tồn kho và từ khóa: tên mặt hàng, mã hoặc số lô.",
   "Bấm vào một tầng để lọc. Gõ từ khóa để tìm.",
   "Danh sách rút gọn theo tầng, xếp theo điểm rủi ro; mỗi dòng là một lô tại một địa điểm.",
   ANH / "uc2-02-tang-qua-han.png",
   "Điểm rủi ro do Business Central tính, dùng để xếp thứ tự xử lý.",
   """
Thao tác đơn giản nhưng cần nói rõ đơn vị của một dòng: một dòng là một mặt hàng, tại một địa điểm, của một lô. Đây là điểm khác biệt
so với báo cáo tồn kho thường, vốn chỉ tới mức mặt hàng và kho.
Điểm rủi ro là cách xếp thứ tự: giá trị lớn và hạn sát thì lên trước. Marou sửa được ngưỡng, không phải sửa code.
""")

kb("03", "Vì sao một lô vào tầng đó", "Người kiểm tra số liệu · có trong POC",
   "Một dòng tồn theo mặt hàng, địa điểm và lô.",
   "Bấm vào dòng để mở trang Chi tiết lô.",
   "Nguồn số liệu từng chỉ tiêu, quy tắc phân tầng dừng ở điều kiện đầu tiên khớp, lịch sử bán theo ngày để cộng tay đối chiếu, và một đoạn giải thích bằng lời.",
   ANH / "uc2ai-02-giai-thich-lo.png",
   "Tính năng S2. Mọi con số trong đoạn được đối chiếu với bảng bên dưới trước khi hiển thị. Ảnh chụp trên dữ liệu mô phỏng.",
   """
Đây là slide làm người kiểm số tin hệ thống. Trang Chi tiết lô cho thấy từng chỉ tiêu lấy từ đâu và tính thế nào, kèm lịch sử bán theo
ngày để người ta tự cộng lại.
Phần mới so với phiên trước là mục "Nói bằng lời" ở đầu trang: trợ lý tóm tắt cả trang thành ba đến năm câu. Ảnh trên slide là đoạn thật
do model viết. Chỉ vào dòng "Người soạn: AI (gpt-4.1-mini)" ở cuối đoạn và giải thích: nếu model viết ra con số không có trong bảng,
hệ thống bỏ đoạn đó và thay bằng câu mẫu, dòng này sẽ ghi "mẫu có sẵn" kèm lý do.
Câu hỏi hay gặp: "Sao không để AI tính luôn cho nhanh?" Trả lời: vì khi đó không ai đối chiếu được, và model đã từng tính đúng nhưng
kết luận ngược trong lần thử đầu tiên. Số phải do BC tính.
""")

kb("04", "Độ phủ dữ liệu trước khi tin kết quả", "Supply Chain · có trong POC",
   "Lô, hạn dùng, lịch sử bán và phân nhóm hàng trên toàn bộ danh mục.",
   "Mở màn hình Độ phủ dữ liệu.",
   "Tỷ lệ dòng có lô, có hạn dùng, có lịch sử bán; chỗ nào thiếu thì kết quả phân tầng ở đó yếu.",
   ANH / "uc2-04-do-phu-du-lieu.png",
   "Cùng logic với codeunit đo độ phủ trong Business Central.",
   """
Slide trung thực, nên giữ. Thông điệp: kết quả chỉ tốt bằng dữ liệu đầu vào. Nếu một nhóm hàng chưa bật quản lý lô hoặc chưa có hạn dùng
thì phân tầng cho nhóm đó không có giá trị.
Dùng slide này để mở câu chuyện chuẩn bị dữ liệu khi triển khai thật: cần chốt danh sách mặt hàng quản lý lô, và cần hạn dùng trên
chứng từ nhập.
""")

kb("05", "Brief buổi sáng do AI viết", "Supply Chain · có trong POC",
   "Bảng sức khỏe tồn kho đã tính, đề xuất đang chờ, và lý do từ chối 14 ngày gần đây.",
   "Bấm Brief, hoặc để lịch 07:30 tự gửi.",
   "Ba việc quan trọng nhất kèm lý do, câu mở đầu theo tình hình chung, câu kết nhắc số đề xuất đang chờ duyệt.",
   ANH / "uc2ai-01-brief-ai.png",
   "Tính năng S1. Code chọn dòng ứng viên và cộng số; model chọn ba việc trong danh sách đó và viết lời. Ảnh chụp trên dữ liệu mô phỏng.",
   """
Đây là ví dụ rõ nhất của nhóm Tóm tắt. Trước đây brief là một danh sách thẻ dài, người đọc phải tự xếp thứ tự. Bây giờ trợ lý nói thẳng
ba việc nên làm trước và vì sao.
Giải thích ranh giới: code đọc bảng, chọn ra tối đa tám dòng ứng viên theo điểm rủi ro, tính sẵn "bán được bao nhiêu trước hạn, dư bao nhiêu",
rồi đưa cho model. Model chỉ được chọn trong tám dòng đó và chỉ được dùng những con số đã đưa.
Chi tiết đáng nói: brief nhớ đề xuất đã bị từ chối trong 14 ngày và không đòi lại việc đó; nếu có nhắc thì nói rõ đã bị từ chối vì sao.
Đây là thứ một báo cáo tĩnh không làm được.
Trên môi trường thật, brief này cũng được gửi qua email mỗi sáng.
""")

kb("06", "Hỏi hàng đã hết hạn toàn hệ thống", "Điều phối kho · có trong POC",
   "Câu hỏi bằng tiếng Việt, không cần mẫu câu.",
   "Gõ: “có mặt hàng nào đã hết hạn chưa”.",
   "Số lô, tổng tồn, giá trị, chia theo địa điểm; năm lô giá trị lớn nhất kèm nút ghi đề xuất.",
   ANH / "uc2-06-het-han-dieu-phoi.png",
   "Câu này đi đường rule, không gọi model, nên không tốn token.",
   """
Nhấn hai điểm. Một: câu hỏi tự nhiên, người dùng không phải học cú pháp. Hai: câu này không tốn tiền, vì rule nhận ra ý định và trả lời
thẳng từ bảng đã tính. Chỉ những câu rule không chắc mới đưa qua model.
Phân quyền thể hiện ngay ở đây: điều phối kho thấy toàn hệ thống và có chia theo địa điểm; nếu người hỏi là quản lý cửa hàng thì chỉ
thấy cửa hàng mình. Đây là ranh giới theo vai, khi triển khai thật sẽ gắn vào danh tính Entra và permission set của BC.
""")

kb("07", "Tra tồn tại cửa hàng của mình", "Quản lý cửa hàng · có trong POC",
   "Vai đang chọn là quản lý cửa hàng, câu hỏi về một mặt hàng.",
   "Gõ: “Choco nuts ở cửa hàng tôi còn bao nhiêu”.",
   "Tồn tại cửa hàng của mình trước, kèm nơi có thể bổ sung và số đề xuất của LS nếu đang thiếu.",
   ANH / "uc2-09-ton-cua-hang.png",
   "Nếu cửa hàng đã hết hàng, trợ lý vẫn nói rõ cửa hàng mình trước rồi mới nói nơi khác.",
   """
Kịch bản cho người dùng ở cửa hàng. Điểm từng sửa theo phản hồi: khi cửa hàng đã hết sạch, câu trả lời cũ nhảy sang nói về kho, làm
người hỏi tưởng hệ thống trả lời nhầm. Bây giờ luôn trả lời cửa hàng mình trước, kể cả khi số là 0.
Nếu mặt hàng đang thiếu, trợ lý nói luôn số mà LS Central đề xuất bổ sung, không phải con số tự nghĩ ra.
""")

kb("08", "Phương án cho lô cận date", "Supply Chain · có trong POC",
   "Một lô cận date: tồn, hạn còn lại, tốc độ bán tại chỗ và tại các cửa hàng khác.",
   "Bấm Phương án xử lý trên thẻ lô, hoặc mở trang Chi tiết lô.",
   "Bảng so sánh: giữ tại chỗ, chuyển vừa đủ, chuyển rồi giảm giá phần dư, giảm giá, chấp nhận hủy; kèm giá trị cứu được và một phương án được chọn.",
   ANH / "uc2ai-03-phuong-an-lo.png",
   "Tính năng D4. Code tính từng phương án; model chọn một phương án trong bảng và viết lý do. Ảnh chụp trên dữ liệu mô phỏng.",
   """
Đây là tính năng khách dễ thấy giá trị tiền nhất, và là chỗ sửa một lỗi nghiệp vụ của bản trước: trước đây nút chuyển hàng đề xuất chuyển
CẢ tồn lô sang cửa hàng bán nhanh nhất, không xét nơi nhận có bán hết trước hạn không. Chuyển cả lô sang một cửa hàng khác chỉ là dời chỗ
hàng sắp hỏng.
Cách tính bây giờ: bán được tại chỗ bằng tốc độ bán nhân số ngày còn lại; phần dư mới cần xử lý. Khả năng nhận của cửa hàng khác bằng tốc
độ bán của họ nhân số ngày còn lại sau một ngày vận chuyển, trừ đi tồn họ đang có. Chỉ chuyển đúng phần họ bán hết.
Ví dụ thật trên slide: Choco pillar tại một cửa hàng, 470 cái, còn 25 ngày, bán 10,8 một ngày. Giữ tại chỗ thì dư 199. Cửa hàng bán nhanh
hơn nhận được nhiều hơn số đó, nên chuyển 199 là hết dư, cứu được toàn bộ giá trị.
Model được phép chọn khác gợi ý của code nếu nêu được lý do trên số đã có; nếu nó viết ra số lạ thì hệ thống bỏ và dùng gợi ý của code.
Mức giảm giá chưa có, vì Marou chưa cho quy tắc; đó là câu hỏi khảo sát G3.
""")

kb("09", "Đề xuất và người duyệt", "Supply Chain và điều phối · có trong POC",
   "Thẻ lô có số lô, tồn, tầng và hành động phù hợp với tầng đó.",
   "Bấm Ghi đề xuất. Người duyệt mở thẻ trong chat của mình.",
   "Đề xuất ghi vào bảng NWV Agent Proposal ở trạng thái Proposed; người duyệt thấy đủ căn cứ, sửa số lượng được, duyệt hoặc từ chối kèm lý do.",
   ANH / "uc2-11-the-duyet-nguoi-duyet.png",
   "Duyệt trên thẻ của trợ lý gọi đúng hàm approve của Business Central, không phải đường tắt riêng.",
   """
Đây là chỗ chứng minh ranh giới giữa trợ lý và hệ thống. Ba ý cần nói:
1. Trợ lý chỉ ghi vào bảng đề xuất, trạng thái luôn là Proposed. Nó không có quyền trên Transfer Header hay Item Journal.
2. Thẻ đi tới đúng người theo vai. Người duyệt thấy mặt hàng, lô, tồn, giá trị, lý do, và dòng policy nào đã khớp.
3. Bấm Duyệt trên thẻ chính là gọi hàm approve trong BC. Nếu Marou thích, người duyệt có thể làm hẳn trong BC trên page NWV Agent Proposals,
   kết quả như nhau.
Từ chối cũng có giá trị: lý do được ghi lại, và brief sáng hôm sau sẽ không đề xuất lại việc vừa bị bác.
""")

s = slide(pr, "KỊCH BẢN 10", "Luồng hủy khép kín: từ đề xuất đến sổ sách",
          "Người duyệt bấm một nút, phần còn lại trợ lý theo đến khi kế toán post xong.")
buoc = [("1 · Duyệt hủy", ["Người duyệt bấm Duyệt hủy trên thẻ lô hết hạn"], NAVY),
        ("2 · BC tạo chứng từ nháp", ["Dòng Item Journal, loại Negative Adjmt.", "Có số lô và reason code", "Chưa post"], RGBColor(0x23, 0x50, 0x7D)),
        ("3 · Biên bản do AI soạn", ["Bảng số liệu do code điền", "Model viết diễn biến và đề nghị", "Gửi email cho bộ phận post"], AMBER),
        ("4 · Theo dõi đến khi xong", ["Mỗi ngày kiểm sổ kho", "Chưa post thì nhắc lại", "Post rồi thì đóng việc"], GREEN)]
the_ngang(s, buoc, t=2.85, h=2.5)
for i in range(3):
    mui_ten(s, 1.20 + (i + 1) * ((14.95 - 0.28 * 3) / 4) + i * 0.28 + 0.02, 3.95, 0.24)
txt(s, 1.20, 5.75, 14.95, 0.5, "Vì sao cần bước này", 22, True, NAVY)
txt(s, 1.20, 6.3, 14.95, 1.5,
    ["Khảo sát cho thấy hàng hết hạn bị hủy thực tế nhưng chứng từ điều chỉnh kho thường trễ, nên sổ sách không khớp thực tế.",
     "Trợ lý không post thay kế toán. Nó chuẩn bị sẵn chứng từ đúng lô, đúng lý do, rồi nhắc cho đến khi có người post.",
     "Chứng từ mang số đề xuất, nên từ bút toán trong sổ kho truy ngược được về đề xuất và về dòng dữ liệu đã dẫn tới quyết định đó."],
    20, False, BODY, space=6)
bang_nguon(s, "Tính năng G2 và A3. Đã chạy thật trên NWV-MAROU: chứng từ AGENT-95, 4 Tiramisu lô L260910-33130 tại S0010.")
note(s, """
Kịch bản này khép vòng từ phát hiện tới sổ sách, và là câu trả lời cho vấn đề Marou nêu trong khảo sát: chứng từ điều chỉnh kho thường
làm trễ nên tồn trên hệ thống không khớp thực tế.
Đi theo bốn bước trên slide. Bước 2 là điểm kỹ thuật đáng nói: khi duyệt, Business Central tạo một dòng Item Journal loại Negative Adjmt.
trong batch riêng tên AGENT, có số lô và reason code, và để nguyên ở trạng thái chưa post. Agent không có quyền post, quyền đó nằm ngoài
permission set của nó.
Bước 3, biên bản: bảng số liệu do code điền từ bảng kết quả, model chỉ viết hai đoạn diễn biến và đề nghị. Biên bản được gửi email cho
bộ phận post kèm link mở thẳng đúng batch trong BC.
Bước 4: mỗi ngày trợ lý kiểm xem sổ kho đã có bút toán mang số chứng từ đó chưa. Có thì báo và đóng việc. Chưa thì nhắc lại qua chat và
email, tới lần thứ ba thì báo người duyệt can thiệp. Nếu dòng biến mất mà không có bút toán, trợ lý báo có thể ai đó đã xóa.
Nếu khách hỏi "sao không cho AI post luôn": đó là ranh giới đã chốt với anh Dũng, và cũng là ranh giới an toàn cho kiểm toán.
""")

kb("10b", "Biên bản hủy do trợ lý soạn", "Người duyệt và kế toán · có trong POC",
   "Đề xuất hủy vừa được duyệt và dòng Item Journal nháp mà Business Central vừa tạo.",
   "Không có thao tác: biên bản hiện ngay trên thẻ và được gửi email cho bộ phận post.",
   "Bảng số liệu đầy đủ (mặt hàng, lô, số lượng, giá vốn, hạn dùng, người đề nghị, người duyệt, số chứng từ) kèm hai đoạn lời do model viết.",
   ANH / "uc2ai-05-bien-ban-huy.png",
   "Tính năng G2. Dòng cuối thẻ ghi rõ ai soạn: AI hay câu mẫu, kèm lý do nếu dùng câu mẫu. Ảnh chụp trên dữ liệu mô phỏng.",
   """
Slide này để khách nhìn tận mắt đầu ra của nhóm Tạo sinh nội dung.
Chỉ vào bảng số liệu: toàn bộ do code điền từ bảng kết quả và từ dòng Item Journal vừa tạo, không phải model nghĩ ra. Model chỉ viết hai
đoạn: diễn biến và đề nghị. Đây là ranh giới cần nói rõ, vì biên bản là giấy tờ có giá trị nội bộ.
Chỉ vào dòng cuối thẻ: ghi người soạn là AI kèm tên model. Nếu model viết ra số không có trong dữ liệu, dòng này sẽ ghi "mẫu có sẵn"
kèm lý do, và nội dung là câu mẫu do code ghép. Nghĩa là biên bản không bao giờ mang số bịa.
Biên bản cũng được gửi email cho bộ phận post kèm link mở thẳng đúng batch Item Journal trong Business Central, để người post không phải
đi tìm.
Nếu Marou có mẫu biên bản riêng, nói rằng phần bảng và bố cục sửa được, còn nguyên tắc số liệu do BC cung cấp thì giữ nguyên.
""", cat=0.58)

kb("11", "Truy xuất lô và khoanh vùng thu hồi", "QA và an toàn thực phẩm · có trong POC",
   "Một số lô, ví dụ L260908-33170B.",
   "Gõ: “truy xuất lô L260908-33170B”.",
   "Hành trình lô theo từng địa điểm: nhập bao nhiêu, bán bao nhiêu, còn tồn ở đâu; nếu phải thu hồi thì lấy lại ở những nơi nào.",
   ANH / "uc2-08-truy-xuat-lo.png",
   "Đọc thẳng Item Ledger Entry của lô; mỗi dòng mở được sổ kho trong Business Central.",
   """
Kịch bản dành cho QA. Tình huống thật: phát hiện một lô có vấn đề, cần biết lô đó đã đi đâu và còn ở đâu, trong vài giây thay vì lọc
báo cáo bằng tay.
Nhấn rằng đây là truy xuất theo lô thật trong sổ kho, không phải suy đoán. Mỗi dòng có link mở Item Ledger Entry đã lọc sẵn theo mặt hàng
và số lô, để QA đối chiếu ngay trong BC.
Phần chưa làm, nên nói thẳng: liên kết ngược lên lô nguyên liệu và theo dõi xác nhận thu hồi của từng cửa hàng là hai tính năng G4 và A4,
cần Marou mô tả quy trình thu hồi hiện tại trước khi làm.
""")

kb("12", "Phát hiện bất thường trong sổ kho", "Supply Chain · có trong POC",
   "Sổ kho 28 ngày gần nhất tại các cửa hàng, cộng bảng sức khỏe tồn kho.",
   "Gõ: “có gì bất thường trong sổ kho không”.",
   "Danh sách tín hiệu kèm số: bán sau hạn, nhận hàng hạn quá ngắn, hủy tăng đột biến, còn tồn mà không bán, hết hàng lặp lại; ba tín hiệu được xếp ưu tiên.",
   ANH / "uc2ai-07-bat-thuong.png",
   "Tính năng D3. Code quét theo năm quy tắc; model xếp thứ tự và viết nhận xét. Ảnh chụp trên dữ liệu mô phỏng.",
   """
Đây là nhóm Khám phá: trợ lý chủ động chỉ ra thứ người ta không hỏi tới.
Năm tín hiệu đều là quy tắc do code quét, có thể kiểm lại từng cái: bán sau hạn dùng; nhận hàng mà hạn còn lại dưới một nửa mức thường
của chính mặt hàng đó; hủy 14 ngày gần đây gấp đôi 14 ngày trước; còn tồn mà bảy ngày không bán trong khi cửa hàng khác vẫn bán;
hết hàng lặp lại nhiều ngày trong cửa sổ tính.
Trên bộ dữ liệu demo, tín hiệu nổi nhất là nhận hàng hạn quá ngắn ở một cửa hàng: bánh tươi về tới nơi thì gần như hết hạn. Đó là thứ
nhìn báo cáo tồn kho thường không thấy.
Model chỉ chọn ba tín hiệu đáng xử lý trước và viết nhận xét; nó không tự tạo ra tín hiệu mới.
Một điều chưa làm được, nói thẳng nếu khách hỏi: lệch kiểm kê lớn chưa quét được vì bộ dữ liệu chưa có phiếu kiểm kê và reason code để
tách khỏi nghiệp vụ nhận hàng.
""")

kb("13", "Nguyên nhân hàng hủy", "Supply Chain và quản lý cửa hàng · có trong POC",
   "Sổ kho 90 ngày: nhận, bán, hủy theo lô của từng cặp mặt hàng và cửa hàng.",
   "Gõ: “vì sao Chocolate cake hủy nhiều” hoặc “vì sao cửa hàng tôi hủy nhiều”.",
   "Bảng theo cặp mặt hàng và cửa hàng: hủy bao nhiêu, giá trị, nhận so với bán, bán so với cửa hàng khác, hạn lúc nhận; kèm nhãn nguyên nhân và kết luận.",
   ANH / "uc2ai-08-nguyen-nhan-huy.png",
   "Tính năng D2. Bốn thước đo do code tính, model viết kết luận. Ảnh chụp trên dữ liệu mô phỏng.",
   """
Câu hỏi "vì sao hủy nhiều" trước đây phải làm bằng Excel. Bây giờ trợ lý trả lời bằng bốn thước đo, mỗi thước đo là một nguyên nhân
có thể sửa được:
1. Nhận dư so với bán: nhận nhiều hơn 1,25 lần lượng bán trong cùng kỳ.
2. Bán chậm hơn cửa hàng khác: dưới 70% tốc độ trung bình của các cửa hàng khác cho cùng mặt hàng.
3. Hạn ngắn khi nhận: hạn còn lại lúc nhận dưới 70% mức thường của mặt hàng đó.
4. Nhận dồn cục: một lần nhận vượt quá lượng bán được trong cả một vòng hạn dùng.
Trên dữ liệu demo, nguyên nhân phổ biến nhất là nhận dư và nhận dồn cục, tức vấn đề nằm ở khâu đặt hàng chứ không phải khâu bán.
Đó chính là loại kết luận giúp sửa từ gốc.
Phần chưa đo được: chuyển hàng trễ, vì bộ dữ liệu demo chưa có Transfer Order để đo thời gian đi đường.
""")

s = slide(pr, "KỊCH BẢN 14", "Quét sáng: trợ lý làm trước khi có ai hỏi",
          "07:30 mỗi ngày, cho từng company, không cần ai bấm nút.")
the_ngang(s, [
    ("Lô hết hạn mới", ["Tự ghi đề xuất hủy vào Business Central", "Đưa thẻ tới người duyệt", "Policy vẫn bắt buộc người duyệt"], GREEN),
    ("Lô cận date mới", ["Gửi bảng phương án xử lý cho Supply Chain", "Tối đa ba lô mỗi sáng"], AMBER),
    ("Brief theo vai", ["Supply Chain và từng quản lý cửa hàng", "Bản của Supply Chain gửi kèm email"], NAVY),
    ("Nhắc và theo dõi", ["Đề xuất chờ duyệt quá một ngày", "Chứng từ hủy chưa post", "Chuyển hàng chưa ship"], RGBColor(0x23, 0x50, 0x7D)),
], t=2.9, h=2.65)
anh(s, ANH / "uc2ai-10-quet-sang.png", 1.20, 5.95, 14.95, 1.1)
txt(s, 1.20, 7.25, 14.95, 0.95,
    ["Một lô đã báo thì sáng hôm sau không báo lại, nên hộp thư buổi sáng chỉ có việc mới.",
     "Mỗi company chạy một lần mỗi ngày; quản trị bấm chạy lại được ngay trên giao diện."], 19, False, BODY, space=4)
bang_nguon(s, "Tính năng A2. Ảnh là câu tóm tắt trợ lý gửi cho quản trị sau khi quét xong, chụp trên dữ liệu mô phỏng.")
note(s, """
Đây là nhóm Tự động hóa, và là câu trả lời cho "agent khác gì báo cáo tự động".
Mỗi sáng 07:30 trợ lý tự quét, không cần ai bấm. Với lô hết hạn mới, nó tự ghi đề xuất hủy và đưa tới người duyệt; policy vẫn bắt buộc
người duyệt, nên tự động mà vẫn có phanh. Với lô cận date mới, nó gửi bảng phương án. Sau đó gửi brief cho từng vai, nhắc các đề xuất
chờ duyệt quá một ngày, và chạy các việc đang theo dõi như chứng từ hủy chưa post.
Điều quan trọng cho người vận hành: một lô đã báo rồi thì sáng hôm sau không báo lại, nên hộp thư buổi sáng chỉ có cái mới. Đây là khác
biệt với báo cáo tự động, vốn gửi lại toàn bộ danh sách mỗi ngày và người ta sẽ ngừng đọc sau một tuần.
Câu tóm tắt trong ảnh là thứ quản trị nhận được: quét xong làm được những gì, gửi cho ai.
""")

kb("15", "Báo cáo tuần hàng hủy", "Supply Chain và quản lý · có trong POC",
   "Sổ kho hai tuần gần nhất, bảng sức khỏe tồn kho, đề xuất và chứng từ hủy đang chờ.",
   "Tự gửi sáng thứ Hai, hoặc gõ: “báo cáo tuần hàng hủy”.",
   "Tuần này so với tuần trước, mặt hàng và cửa hàng hủy nhiều nhất, nguyên nhân chính, số việc còn tồn đọng; gửi kèm email.",
   ANH / "uc2ai-09-bao-cao-tuan.png",
   "Tính năng S3. Số liệu do code tính; model viết ba đoạn mở đầu, nhận xét và việc tuần tới. Ảnh chụp trên dữ liệu mô phỏng.",
   """
Báo cáo tuần là thứ gửi lên quản lý và tài chính, nên giọng khác brief hằng ngày: có so sánh với tuần trước và có phần việc tuần tới.
Chỉ vào bảng số: tuần này so tuần trước cả số lượng và giá trị, mặt hàng hủy nhiều nhất, cửa hàng hủy nhiều nhất, số lô hết hạn còn tồn,
số đề xuất hủy chờ duyệt và số chứng từ chưa post. Phần nguyên nhân lấy từ D2, tính trên 28 ngày.
Lưu ý khi diễn: trên bộ dữ liệu demo, tuần gần nhất có thể hiện 0 vì các lô hết hạn chưa được post hủy. Đó chính là vấn đề mà vòng đề xuất
và theo dõi đang đẩy, không phải lỗi số liệu. Nếu khách thắc mắc, dùng luôn cơ hội đó để nói về slide luồng hủy khép kín.
Email gửi mỗi tuần một lần, tính theo tuần ISO, nên bấm lại trong tuần không gửi trùng.
""")

# ---- UC3 nhac post
s = slide(pr, "KỊCH BẢN BỔ SUNG · UC3", "Nhắc post nhận hàng: việc Marou đang phải thuê người làm",
          "Khảo sát: hàng mua về cửa hàng, chứng từ dồn tới cuối tháng mới post nhận.")
the_ngang(s, [
    ("Trợ lý phát hiện", ["Đơn mua quá ngày nhận dự kiến mà còn số lượng chưa nhận",
                          "Gom theo số đơn và địa điểm nhận"], NAVY),
    ("Hỏi người tại chỗ", ["Gửi thẻ hỏi cửa hàng: hàng đã về chưa",
                           "Mỗi đơn chỉ hỏi một lần"], RED),
    ("Nhắc người post", ["Email tự soạn kèm danh sách đơn, số lượng, link mở đơn trong BC",
                         "Nhắc lại mỗi sáng nếu chưa post"], AMBER),
    ("Đóng việc", ["BC không còn số lượng chưa nhận thì báo đã post",
                   "Không nhắc nữa"], GREEN),
], t=2.95, h=2.9)
txt(s, 1.20, 6.25, 14.95, 0.45, "Ranh giới", 22, True, NAVY)
txt(s, 1.20, 6.8, 14.95, 1.3,
    ["Trợ lý không post chứng từ. Nó phát hiện, hỏi đúng người, soạn và gửi email, rồi theo đến khi Business Central ghi nhận đã nhận hàng.",
     "Email đã gửi thật trong POC qua SMTP; nội dung danh sách đơn do code điền, model chỉ viết đoạn mở đầu và câu kết."],
    19, False, BODY, space=4)
bang_nguon(s, "Khảo sát Marou: Marou đang thuê một nhân sự bên ngoài để post đơn. Đây là việc trợ lý gánh được phần theo dõi và nhắc.")
note(s, """
Slide này gắn POC với một điểm đau có thật mà anh Dũng thu được khi khảo sát: hàng mua về cửa hàng nhưng chứng từ dồn tới cuối tháng
mới post nhận, và Marou đang thuê người bên ngoài làm việc đó. Hậu quả là tồn trên hệ thống thấp hơn thực tế, kéo theo cảnh báo hết hàng
và đề xuất bổ sung sai.
Bốn bước trên slide là vòng khép kín. Nhấn mạnh trợ lý không post thay ai: nó chỉ phát hiện, hỏi người nhận hàng tại chỗ, soạn email
và nhắc lại đến khi BC ghi nhận.
Email đã gửi thật trong quá trình làm POC, không phải mô phỏng. Danh sách đơn, số lượng, ngày dự kiến và link mở đơn đều do code điền
từ Purchase Line; model chỉ viết đoạn mở đầu và câu kết, và vẫn bị kiểm số như mọi chỗ khác.
Nếu khách hỏi "vậy có thể cho AI post luôn không": về kỹ thuật làm được, nhưng đó là đổi ranh giới đã chốt, cần Marou quyết và cần bàn
về kiểm soát nội bộ. Đừng hứa trong buổi này.
""")

# ---- Chi phi va van hanh
s = slide(pr, "VẬN HÀNH", "Chi phí AI đo được và cách kiểm soát",
          "Token là số đếm thật từ nhà cung cấp; tiền là ước tính theo đơn giá công bố.")
anh(s, ANH / "uc2ai-11-chi-phi-theo-viec.png", 1.20, 2.8, 8.6, 5.3)
txt(s, 10.15, 2.9, 6.0, 0.5, "Số đo được ngày 16/09/2026", 22, True, NAVY)
txt(s, 10.15, 3.5, 6.0, 1.6,
    ["Cả ngày kiểm thử: 146 lượt gọi model, 0,085 USD.",
     "Một câu hỏi mở tốn khoảng 6 nghìn token, tức 0,001 đến 0,002 USD.",
     "Brief, giải thích lô, phương án, biên bản: mỗi lần dưới 1.000 token."], 19, False, BODY, space=5)
txt(s, 10.15, 5.35, 6.0, 0.5, "Ba lớp chặn", 22, True, NAVY)
txt(s, 10.15, 5.95, 6.0, 2.2,
    ["Rule trả lời trước, model chỉ được gọi khi rule không chắc.",
     "Trần theo ngày và trần cộng dồn; vượt thì tự về câu mẫu.",
     "Giới hạn token mỗi phút trên tài khoản Azure.",
     "Quản trị xem được chi phí theo từng việc và tắt AI bất cứ lúc nào."], 19, False, BODY, space=5)
bang_nguon(s, "Trang Cài đặt AI chỉ vai quản trị mở được; các đường API tương ứng cũng chặn theo vai.")
note(s, """
Slide cho người trả tiền. Ba ý:
1. Con số là thật, đếm từ phản hồi của Azure sau mỗi lượt gọi, lưu từng dòng. Tiền là ước tính theo bảng giá công bố, hóa đơn thật mới
   là số cuối cùng; nói thẳng điều này.
2. Chi phí nhỏ vì kiến trúc: rule trả lời phần lớn câu hỏi, model chỉ nhận bảng số đã lọc chứ không nhận cả dữ liệu.
3. Có phanh thật: hai mức trần, vượt thì trợ lý tự quay về câu mẫu thay vì báo lỗi giữa buổi demo.
Nếu khách hỏi chi phí khi chạy thật cho cả Marou: nói rằng con số phụ thuộc số người dùng và số câu hỏi mở, và đề nghị đo trong giai đoạn
thí điểm với trần chi phí đặt sẵn, thay vì hứa một con số bây giờ.
""")

# ---- Muc dap ung
s = slide(pr, "TỔNG KẾT", "Mức đáp ứng và việc còn lại",
          "Trạng thái 16/09/2026 trên môi trường demo NWV01, hai company.")
the_ngang(s, [
    ("Đã chạy thật", ["Sức khỏe tồn kho theo lô, sáu tầng", "Truy xuất lô", "Đề xuất và người duyệt, ba loại chứng từ nháp",
                      "12 tính năng AI trong bốn nhóm", "Hai company, mua thẳng từ Marou",
                      "Intercompany: đơn mua thành đơn bán bên kia", "Email và lịch chạy nền"], GREEN),
    ("Cần dữ liệu hoặc quy trình của Marou", ["Mức giảm giá cho lô cận date", "Quy trình thu hồi lô", "Kênh Teams thay cho chat web",
                                              "Phiếu kiểm kê và reason code", "Ngưỡng cận date theo nhóm hàng"], AMBER),
    ("Cần Marou quyết", ["Có cho tự động post hai đầu không", "Kho xuất hàng bên Marou cho đơn bán",
                         "Có cho trợ lý post chứng từ không", "Vùng xử lý dữ liệu của model", "Ngưỡng và policy chính thức"], RED),
], t=2.9, h=3.6)
txt(s, 1.20, 6.85, 14.95, 1.25,
    ["Bước tiếp theo đề xuất: chốt ngưỡng và policy với Supply Chain, dựng dữ liệu bán lẻ riêng cho Dakao, rồi chạy thử một tuần thật với trần chi phí đặt sẵn.",
     "Mọi con số trong bộ slide này đo trên bộ dữ liệu mô phỏng của NaviWorld, không phải số liệu vận hành của Marou."],
    19, False, BODY, space=4)
note(s, """
Slide đóng. Chia ba cột cho rõ trách nhiệm: cái gì đã chạy được, cái gì đang chờ dữ liệu hoặc quy trình từ Marou, cái gì cần Marou quyết.
Đừng gộp ba nhóm này làm một, vì khách cần biết phần nào phụ thuộc họ.
Kết bằng đề nghị cụ thể: chốt ngưỡng và policy với Supply Chain, dựng dữ liệu bán lẻ riêng cho Dakao, chạy thử một tuần thật với trần
chi phí đặt sẵn. Đó là bước nhỏ, đo được, không đòi cam kết lớn.
Câu cuối bắt buộc phải nói: toàn bộ số liệu trong buổi này là dữ liệu mô phỏng do NaviWorld dựng trên danh mục của Marou, không phải
số liệu vận hành thật.
""")

RA.parent.mkdir(parents=True, exist_ok=True)
try:
    pr.save(str(RA))
    ra_that = RA
except PermissionError:
    # File dang mo trong PowerPoint: ghi ra ban moi thay vi hong ca lan build. Dong file roi chay lai de ghi de.
    ra_that = RA.with_name(RA.stem + " (ban moi)" + RA.suffix)
    pr.save(str(ra_that))
    print("CANH BAO: file goc dang mo trong PowerPoint, da ghi ra ban moi. Dong file roi chay lai de ghi de.")
TAM.unlink(missing_ok=True)
print("da ghi:", ra_that)
print("so slide:", len(pr.slides.__iter__.__self__._sldIdLst))
