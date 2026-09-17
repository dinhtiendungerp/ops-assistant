"""Bo slide rut gon cho buoi demo 17/09/2026, ban v4: theo mach 20 buoc cua console (UC2 len dau).

Dem 16/09/2026 Dung yeu cau "cap nhat lai slide, dua cac hinh moi, kich ban moi". Cach lam:
- Mo bo day du `Demo-Marou/Marou POC - slide demo.pptx` (ra tu build_slide_uc2_v2.py).
- Them cac slide moi o cuoi bang CHINH helper cua build_slide_uc2_v2.py (exec phan helper, khong chay phan dung deck).
- Xep lai thu tu, bo slide khong dung, bo section, ghi ra `Demo-Marou/Marou POC - slide demo (ban ngan, 17-09 v4).pptx`.
Them roi moi xoa (khong xoa truoc roi them) de khong trung ten part.
Anh moi chup bang tools/chup_kich_ban_17_09.mjs tu cau tra loi that tren BC (QA dem 16/09).

Chay: cd docs; python build_slide_17_09.py [ten file ra]
"""
from __future__ import annotations

import sys
from pathlib import Path

from pptx import Presentation

DOCS = Path(__file__).resolve().parent
NGOAI = Path(r"C:/Users/dungdt.NWV/Demo-Marou")
NGUON = NGOAI / "Marou POC - slide demo.pptx"
RA = NGOAI / (sys.argv[1] if len(sys.argv) > 1 else "Marou POC - slide demo (ban ngan, 17-09 v7).pptx")

# Nap helper (mau, font, slide, txt, hop, anh, anh_cat, ba_cot_io, the_ngang, bang_nguon, note) tu builder goc.
_src = (DOCS / "build_slide_uc2_v2.py").read_text(encoding="utf-8")
_helper = _src.split("# ---------------------------------------------------------------- dung deck")[0]
g: dict = {"__file__": str(DOCS / "build_slide_uc2_v2.py"), "__name__": "helper"}
exec(compile(_helper, "build_slide_uc2_v2_helper", "exec"), g)
slide, txt, anh, anh_cat, ba_cot_io, the_ngang, bang_nguon, note, hop = (
    g["slide"], g["txt"], g["anh"], g["anh_cat"], g["ba_cot_io"], g["the_ngang"], g["bang_nguon"], g["note"], g["hop"])
NAVY, RED, BODY, AMBER, GREEN = g["NAVY"], g["RED"], g["BODY"], g["AMBER"], g["GREEN"]
A = DOCS / "anh-uc2"

pr = Presentation(str(NGUON))
so_cu = len(pr.slides._sldIdLst)
moi: dict[str, int] = {}


def them(khoa, s):
    moi[khoa] = len(pr.slides._sldIdLst)        # so thu tu 1-based cua slide vua them
    return s


# ---------------------------------------------------------------- N0 mach demo
s = them("mach", slide(pr, "KỊCH BẢN DEMO 17/09", "Hai mươi bước, bảy phần, UC2 ở trung tâm",
                        "Mỗi bước là một nút trên console; tên nút chính là câu sẽ gửi. Đã chạy thử trọn vòng trên Business Central đêm 16/09."))
the_ngang(s, [
    ("UC2 · bước 1 đến 9", ["1 · Sức khỏe tồn kho, brief AI", "2 · Lô cận date: AI chọn phương án, email người duyệt, Transfer Order",
                            "3 · Hỏi tự do: chậm luân chuyển, đề xuất CTKM, truy xuất lô, bất thường"], NAVY),
    ("UC5 và UC1 · bước 10 đến 15", ["4 · Cửa hàng hết hàng: LS tính, AI đề xuất đặt mua từ Marou, đề xuất bất thường",
                                    "5 · Dự báo ghi vào LS, CTKM thiếu nhu cầu"], RED),
    ("Liên công ty và vận hành · 16 đến 20", ["6 · Marou xuất kho, trợ lý tự báo cửa hàng, xin phép post phiếu nhận",
                                             "7 · Chi phí AI đo được"], AMBER),
], t=2.9, h=4.6)
bang_nguon(s, "Bản 20 phút: giữ bước 2, 3, 4, 5, 6, 7, 8, 10, 12, 16, 18.")
note(s, """
Slide điều hướng cho buổi demo. Nói trước đường đi: ba phần đầu là UC2 trọn vẹn, từ nhìn con số tới hỏi tự do; sau đó mới nối sang
cửa hàng bán lẻ (UC5), dự báo (UC1), và khép lại bằng vòng liên công ty khi hàng về cửa hàng.
Nhấn một câu: cả 20 bước đã chạy thử trên Business Central thật đêm 16/09, các ảnh trong bộ slide chụp từ chính lần chạy đó.
Nếu bị cắt giờ, đi bản 20 phút ở dải dưới.
""")

# ---------------------------------------------------------------- N1 email nguoi duyet
s = them("email", slide(pr, "KỊCH BẢN · BƯỚC 4", "Email cho người duyệt, AI soạn phần lời",
                         "Supply Chain ghi đề xuất chuyển lô cận date · người duyệt được gọi cả qua chat lẫn email"))
ba_cot_io(s, "Đề xuất chuyển 187 Choco pillar từ S0010 sang S0001, dòng Inventory Health của lô, policy đã khớp.",
          "Bấm Ghi đề xuất trên thẻ phương án. Trợ lý ghi đề xuất vào BC, đẩy thẻ cho người duyệt và gửi email.",
          "Email: đoạn mở đầu và đoạn kết do AI viết, bảng số và link Business Central do code điền. Thẻ báo kênh gửi, người soạn.")
anh(s, A / "kb17-04b-email-nguoi-duyet.png", 7.50, 2.95, 8.65, 5.2)
bang_nguon(s, "Chạy thật 17/09/2026 00:28 trên NWV-MAROU: SMTP đã gửi, người soạn AI (gpt-4.1-mini).")
note(s, """
Kịch bản mới tối 16/09. Ai đang mở trợ lý thì thấy thẻ trong chat; ai không mở thì nhận email. Trước đây chỉ có đường chat.
Chia việc rõ: code điền bảng mặt hàng, lô, tồn, giá trị, tầng, policy, link mở trang đề xuất trong BC. Model chỉ viết hai đoạn lời:
tình hình và vì sao cần duyệt sớm, rồi việc cần làm. Mọi chữ số model viết phải có trong dữ liệu đưa nó; sai là thư dùng mẫu, thẻ ghi lý do.
Email không gửi khi người đề nghị là lịch quét sáng, vì một lượt quét ghi tới 10 đề xuất; lúc đó đã có brief và email tổng hợp.
Nếu khách hỏi gửi cho ai: POC gửi một hộp thư cấu hình sẵn. Khi triển khai, gắn với người duyệt theo vai trong Entra và permission set.
""")

# ---------------------------------------------------------------- N2 hoi tu do
s = them("tudo", slide(pr, "KỊCH BẢN · BƯỚC 6 VÀ 7", "Hỏi tự do: hàng chậm luân chuyển, rồi nên chạy CTKM gì",
                        "Không có kịch bản viết sẵn · model tự chọn tool, code kiểm từng con số"))
anh(s, A / "kb17-06-cham-luan-chuyen.png", 1.20, 3.05, 7.30, 5.1)
anh_cat(s, A / "kb17-07-ctkm-hang-cham.png", 8.85, 3.05, 7.30, 5.1, 0.52)
txt(s, 1.20, 2.62, 7.3, 0.35, "Mặt hàng nào đang chậm luân chuyển ở các cửa hàng?", 16, True, NAVY)
txt(s, 8.85, 2.62, 7.3, 0.35, "Đề xuất CTKM để bán các mặt hàng này?", 16, True, NAVY)
bang_nguon(s, "Câu thứ hai nối tiếp câu đầu: trợ lý đưa vài tin gần nhất của đoạn chat cho model. Mức giảm phần trăm không bịa, người phụ trách chốt.")
note(s, """
Đây là câu trả lời cho “80% câu hỏi nằm ngoài kịch bản thì sao”. Hai câu này không có mẫu nào viết sẵn.
Câu một: model gọi bảng sức khỏe tồn kho, xếp theo số ngày tồn đủ bán và số ngày không bán, không chỉ nhìn tầng Chậm luân chuyển.
Trước khi sửa tối 16/09, model chỉ lọc tầng đó, thấy rỗng và trả lời “yên tâm”; đó là lý do chúng tôi đưa câu này vào demo.
Câu hai: “các mặt hàng này” chỉ hiểu được nhờ ngữ cảnh đoạn chat. Model đọc lại tồn kho và CTKM của LS, thấy ba CTKM đang chạy không có
Ice cream strawberry, đề xuất giảm giá, combo hoặc đưa ra khu trưng bày. Nó không đưa mức giảm phần trăm vì Marou chưa có quy tắc.
Bấm nút “Xem các bước tôi đã tra” trên thẻ để khách thấy model gọi tool gì. Câu hai mất khoảng 30 giây, nói câu dẫn trong lúc chờ.
""")

# ---------------------------------------------------------------- N3 truy xuat
s = them("truyxuat", slide(pr, "KỊCH BẢN · BƯỚC 8", "Truy xuất lô: còn ở đâu, thu hồi lấy lại ở đâu",
                            "Supply Chain · Traceability của UC2"))
ba_cot_io(s, "Số lô L260906-33323C. Item Ledger Entry của lô ở mọi địa điểm.",
          "Gõ “truy xuất lô L260906-33323C”.",
          "AI kể lại hành trình: nhập 110 về W0003, xuất 81 theo đơn liên công ty, còn 29, hạn 22/04/2027. Bảng sổ kho thu gọn bên dưới.")
anh(s, A / "kb17-08-truy-xuat.png", 7.50, 2.95, 8.65, 5.2)
bang_nguon(s, "81 cái xuất theo đơn HO106202 sang Cửa hàng Quận 1; phần liên công ty sẽ thấy cửa hàng được báo.")
note(s, """
Truy xuất là nửa sau của UC2. Trợ lý gom Item Ledger Entry của lô theo địa điểm, nói còn tồn ở đâu và thu hồi lấy lại ở đâu.
Phần lời do AI viết lại, bảng sổ kho thu gọn bên dưới và có link mở đúng Item Ledger Entry của lô trong BC.
Lô này nối với phần 6: Marou chọn lô còn hạn để xuất sang Dakao. Bên bán lẻ không quản lý lô nên cửa hàng chỉ thấy mặt hàng và số lượng.
Đừng dùng lô L260908-33110B: lô đó đã quá hạn, bị chọn trước khi sửa quy tắc FEFO.
""")

# ---------------------------------------------------------------- N4 cua hang het hang
s = them("uc5", slide(pr, "KỊCH BẢN · BƯỚC 10 VÀ 11", "Cửa hàng bán lẻ báo sắp hết, LS tính, AI giải thích",
                       "Minh, Cửa hàng Hà Nội (S0002, Dakao) · Supply Chain hỏi vì sao"))
ba_cot_io(s, "Một câu tự nhiên của cửa hàng. Kết quả LS Replenishment đã tính: Stock Levels 8/20.",
          "Minh gõ “sắp hết Ice cream ở cửa hàng tôi”. Supply Chain gõ “vì sao LS đề xuất Ice cream cho S0002”.",
          "Đề xuất đặt mua 12 từ MAROU giao thẳng S0002, gửi điều phối duyệt. AI kể lại nhật ký tính của LS.")
anh(s, A / "kb17-10-minh-ice-cream.png", 7.50, 2.62, 8.65, 0.9)
anh_cat(s, A / "kb17-11-vi-sao-ls.png", 7.50, 3.6, 8.65, 4.55, 0.62)
bang_nguon(s, "12 là số của LS Replenishment, trợ lý không tính lại. Dakao không có kho trung tâm nên đề xuất là đặt mua từ Marou.")
note(s, """
Chuyển từ UC2 sang UC5. Cửa hàng chỉ nói một câu; trợ lý nhận ra mặt hàng, cửa hàng của người hỏi, đọc con số LS đã tính, ghi đề xuất
loại Purchase vào BC và gửi Hùng duyệt. Bước này ghi thật; bấm lần hai trợ lý nói đã có đề xuất.
Câu “vì sao”: trợ lý đọc nhật ký tính của LS (Calc. Log Lines), không tính lại. Kiểu Stock Levels: tồn 8 chạm điểm đặt lại, LS đưa lên
mức tối đa 20 nên mua 12. Tham số nằm trên Item Card của LS, Marou tự sửa.
""")

# ---------------------------------------------------------------- N5 duyet dat mua
s = them("datmua", slide(pr, "KỊCH BẢN · BƯỚC 12", "Duyệt đặt mua, gửi đơn sang Marou",
                          "Hùng, điều phối · Intercompany chuẩn của Business Central"))
ba_cot_io(s, "Đề xuất đặt mua 12 Ice cream từ MAROU giao S0002.",
          "Bấm Duyệt đặt mua, rồi Gửi đơn sang Marou trên thẻ Purchase Order.",
          "Purchase Order Open bên Dakao; sau khi gửi, đơn Released và Marou tự sinh Sales Order.")
anh(s, A / "kb17-12-duyet-dat-mua.png", 7.50, 2.95, 8.65, 5.2)
bang_nguon(s, "Chạy thật đêm 16/09: PO HO106205 bên Dakao thành Sales Order S90018 bên Marou.")
note(s, """
Hai cú bấm, hai quyết định của người mua. Duyệt là BC tạo Purchase Order ở trạng thái Open. Gửi đơn sang Marou dùng Intercompany chuẩn:
đơn mua bên Dakao thành đơn bán bên Marou, không nhập lại. Trợ lý không tự bấm Gửi vì gửi kéo theo Release, là quyết định của người mua.
Thẻ ghi “tạo dưới tên Hùng”: chứng từ mang tham chiếu đề xuất, truy ngược được.
""")

# ---------------------------------------------------------------- N6 de xuat bat thuong
s = them("batthuongls", slide(pr, "KỊCH BẢN · BƯỚC 13", "AI tổng hợp đề xuất bổ sung bất thường",
                               "Nhóm Khám phá và phân tích insight · model đọc toàn bộ đề xuất của LS"))
ba_cot_io(s, "Mọi dòng LS Replenishment đề xuất, kèm cờ do code tính: hết hàng quá nửa cửa sổ tính, không có bán bình quân, tồn bằng 0.",
          "Gõ “tổng hợp những đề xuất bổ sung bất thường”.",
          "Danh sách dòng đáng xem, mỗi cửa hàng một dòng, nói vì sao; dòng kiểu min-max tách riêng vì không có bán bình quân là bình thường.")
anh_cat(s, A / "kb17-13-de-xuat-bat-thuong.png", 7.50, 2.95, 8.65, 5.2, 0.55)
bang_nguon(s, "Croissant chocolate lộ ra: bánh tươi huỷ cuối ngày nên tồn về 0 mỗi tối, LS đếm là hết hàng.")
note(s, """
Không ai viết sẵn câu trả lời. Model gọi tool đọc đề xuất của LS; code gắn cờ bất thường bằng tiếng Việt; model chọn dòng và giải thích.
Chỗ đáng nói: Croissant chocolate bị LS coi là hết hàng quá nửa số ngày vì bánh tươi huỷ cuối ngày. Đó là cách ghi Out of Stock
cần Marou xem lại, không phải lỗi của LS. Câu trả lời đổi theo dữ liệu; nếu model chọn dòng khác thì đọc lý do nó nêu.
""")

# ---------------------------------------------------------------- N7 du bao va CTKM
s = them("dubao", slide(pr, "KỊCH BẢN · BƯỚC 14 VÀ 15", "Dự báo ghi vào LS, CTKM thiếu nhu cầu",
                         "UC1 nối UC5 · Supply Chain"))
anh(s, A / "kb17-14-du-bao.png", 1.20, 3.05, 7.30, 5.1)
anh(s, A / "kb17-15-ctkm.png", 8.85, 3.05, 7.30, 5.1)
txt(s, 1.20, 2.62, 7.3, 0.35, "Dự báo Choco bowl ở S0010 sai bao nhiêu?", 16, True, NAVY)
txt(s, 8.85, 2.62, 7.3, 0.35, "CTKM nào đang chạy và sắp tới?", 16, True, NAVY)
bang_nguon(s, "Dự báo Holt-Winters ghi vào Retail Forecast Entry của LS. Choco bowl giảm 15% ngày 23 đến 25/09 chưa có nhu cầu cho S0002, S0005.")
note(s, """
Một nhịp UC1. Dự báo không nằm ở bảng riêng của NaviWorld: nó ghi vào bảng chuẩn của LS, nên LS Replenishment dùng ngay. Holt-Winters
là thống kê chuỗi thời gian, chưa phải AI; AI ở đây là phần kể lại kết quả. Khách hỏi WAPE, Bias: mở tab Dự báo, phần Cách đọc.
CTKM: trợ lý đọc Periodic Discount của LS và soi xem LS đã cộng nhu cầu khuyến mãi cho cửa hàng nào. Thiếu thì cửa hàng đó sẽ thiếu hàng
đúng ngày khuyến mãi. Lỗ hổng này cố ý để trong dữ liệu để thấy trợ lý bắt được.
""")

# ---------------------------------------------------------------- N8 tu biet Marou xuat kho
s = them("tubao", slide(pr, "KỊCH BẢN · BƯỚC 19", "Marou post xuất kho, trợ lý tự biết và báo cửa hàng",
                         "Không ai bấm gì trên trợ lý · người kho Marou làm việc như mọi ngày trong Business Central"))
anh(s, A / "kb17-19-minh-nhan-tin.png", 8.85, 2.62, 7.30, 5.5)
buoc3 = [("Marou", "Người kho bấm Post, chọn Ship trên Sales Order. Phiếu giao hàng mang số đơn mua của Dakao.", NAVY),
         ("Mỗi phút", "Trợ lý đọc phiếu giao hàng bên Marou qua web service chỉ đọc, nối với đơn mua bên Dakao.", RED),
         ("Báo ngay", "Cửa hàng nhận hàng, điều phối, Supply Chain nhận thẻ trong chat và email tổng hợp.", AMBER)]
for i, (ten, dong, mau) in enumerate(buoc3):
    y = 2.75 + i * 1.28
    hop(s, 1.20, y, 7.3, 1.12, g["BOXBG"], top_bar=mau)
    txt(s, 1.40, y + 0.18, 1.6, 0.4, ten, 19, True, mau)
    txt(s, 3.05, y + 0.18, 5.3, 0.9, dong, 16, False, BODY, space=2, line=1.0)
txt(s, 1.20, 6.65, 7.3, 1.5,
    ["Chỉ đọc, không ghi gì vào sổ. Đơn đã báo thì không báo lại.",
     "Đã thử thật: post xuất kho HO106204 ngoài trợ lý, trong vòng một phút cửa hàng S0005 có thẻ và email."], 16, False, BODY, space=4)
bang_nguon(s, "Cơ sở để biết: Sales Shipment Header bên Marou có External Document No. bằng số đơn mua bên Dakao, do Intercompany điền sẵn.")
note(s, """
Câu khách chắc chắn hỏi: “bên Marou bấm post thì làm sao trợ lý biết?”. Trả lời bằng slide này.
Trợ lý không cần ai báo. Mỗi phút nó gọi web service chỉ đọc của app NaviWorld, đọc Sales Shipment Header ở company bên bán; phiếu nào
mang số đơn mua của Dakao mà chưa từng báo thì báo cửa hàng nhận hàng, điều phối, Supply Chain, và gửi email. Không ghi gì.
Trên sân khấu có hai cách: nút demo thay người kho (an toàn), hoặc mở BC company NWV-MAROU, Sales Order S90016 (đơn HO106203, 5 Choco
bowl, lô đã gán sẵn), bấm Post, chọn Ship, rồi đợi tối đa một phút. Cách thứ hai thuyết phục hơn nếu mạng ổn.
Giới hạn nói thẳng: đơn đã xuất trước lúc máy chủ trợ lý khởi động thì lịch nền không tự báo lại, nút Kiểm hàng vẫn báo được.
""")

# ---------------------------------------------------------------- xep thu tu
# So thu tu (1-based) trong bo day du, xen slide moi theo mach 20 buoc.
THU_TU = [1, 2, 3, 4, 6, 7, 8, moi["mach"], 10, 14, 17, moi["email"], 18, moi["tudo"], moi["truyxuat"], 22,
          moi["uc5"], moi["datmua"], moi["batthuongls"], moi["dubao"], 26, moi["tubao"], 27, 29, 30]

ids = pr.slides._sldIdLst
tat_ca = list(ids)
giu = [tat_ca[i - 1] for i in THU_TU]
for sid in tat_ca:
    ids.remove(sid)
for sid in giu:
    ids.append(sid)
for sid in tat_ca:
    if sid not in giu:
        pr.part.drop_rel(sid.rId)

el = pr.part._element
for ext_lst in [e for e in el if e.tag.endswith("}extLst")]:
    for ext in list(ext_lst):
        if any(ch.tag.endswith("}sectionLst") for ch in ext):
            ext_lst.remove(ext)
    if len(ext_lst) == 0:
        el.remove(ext_lst)

# ---------------------------------------------------------------- v5: sua chu, ma G3, speaker note van noi
import copy as _copy
sys.path.insert(0, str(DOCS))
import note_slide_17_09 as ns

slides = list(pr.slides)
thieu = []
for so, cu, moi_chu in ns.SUA_CHU:
    thay = False
    for sh in slides[so - 1].shapes:
        if not sh.has_text_frame:
            continue
        for para in list(sh.text_frame.paragraphs):
            for r in para.runs:
                if cu in r.text:
                    r.text = r.text.replace(cu, moi_chu)
                    thay = True
            if thay and not moi_chu and not "".join(r.text for r in para.runs).strip() and len(sh.text_frame.paragraphs) > 1:
                para._p.getparent().remove(para._p)
    if not thay:
        thieu.append((so, cu[:50]))
if thieu:
    raise SystemExit(f"Khong tim thay chu can sua: {thieu}")

# Ma G3 cho "Email nhac post nhan hang" tren slide bon nhom AI (ban day du de trong ma).
s6 = slides[5]
g2 = next(sh for sh in s6.shapes if sh.has_text_frame and sh.text_frame.text == "G2")
email = next(sh for sh in s6.shapes if sh.has_text_frame and sh.text_frame.text == "Email nhắc post nhận hàng")
if not any(sh.has_text_frame and sh.text_frame.text == "G3" for sh in s6.shapes):
    el = _copy.deepcopy(g2._element)
    s6.shapes._spTree.append(el)
    g3 = s6.shapes[-1]
    g3.top = email.top
    g3.text_frame.paragraphs[0].runs[0].text = "G3"

for so, noi_dung in ns.NOTE.items():
    slides[so - 1].notes_slide.notes_text_frame.text = noi_dung.strip()

# Dung sang 17/09: bo slide 5 (hai don vi va painpoint). Note slide 21 da ke lai painpoint.
BO_SLIDE = [5]
_ids = pr.slides._sldIdLst
for so in sorted(BO_SLIDE, reverse=True):
    _sid = list(_ids)[so - 1]
    pr.part.drop_rel(_sid.rId)
    _ids.remove(_sid)

pr.save(str(RA))
print("bo day du:", so_cu, "slide; da ghi:", RA, "so slide:", len(Presentation(str(RA)).slides._sldIdLst))
