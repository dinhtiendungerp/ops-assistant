"""Speaker note van noi cho bo slide rut gon 17/09 (v5), va cac cho sua chu tren slide.

Dung yeu cau sang 17/09/2026: note phai la van noi de doc thanh loi, co the kem ghi chu; slide khong dua thong tin kieu nhat ky
chay thu (so don, so phieu, "da chay that ... "); "diem dau" doi thanh "painpoint", va painpoint lay tu boi canh hien tai chu
khong phai tu khao sat. Moi note chia hai phan: NOI (doc len) va GHI CHU (cho nguoi trinh bay, khong doc).
Khoa cua NOTE la so thu tu slide trong ban rut gon (1-based), theo THU_TU cua build_slide_17_09.py.
"""

# (so slide, chu cu tren slide, chu moi). Chu moi rong la xoa doan van do.
SUA_CHU = [
    (5, "Hai đơn vị của Marou và ba điểm đau khảo sát nêu", "Hai đơn vị của Marou và ba painpoint ở kho bán lẻ"),
    (5, "Khảo sát 13/09/2026 nêu ba điểm đau ở kho bán lẻ. ", "Ba painpoint lấy từ bối cảnh vận hành hiện tại. "),
    (5, "Khảo sát nêu, POC trả lời", "Painpoint và cách POC trả lời"),
    (5, "Đã chạy thật: đơn mua HO106201 (Dakao) thành đơn bán S90014 (Marou), xuất kho 102043, nhận hàng 107110.",
        "Marou bán cho Dakao bằng Intercompany chuẩn của Business Central."),
    (5, "Nguồn: khảo sát Marou 13/09/2026 và RFP 20/08/2026.", "Nguồn: bối cảnh vận hành hiện tại của Marou và RFP 20/08/2026."),
    (7, " Toàn bộ ngày QA 16/09 tốn 0,085 USD cho 146 lượt gọi.", ""),
    (8, " Đã chạy thử trọn vòng trên Business Central đêm 16/09.", ""),
    (12, "Chạy thật 17/09/2026 00:28 trên NWV-MAROU: SMTP đã gửi, người soạn AI (gpt-4.1-mini).",
         "Người duyệt không mở trợ lý vẫn nhận được việc cần duyệt; thẻ ghi rõ kênh gửi và người soạn."),
    (15, "81 cái xuất theo đơn HO106202 sang Cửa hàng Quận 1; phần liên công ty sẽ thấy cửa hàng được báo.",
         "Lô này vừa xuất sang Cửa hàng Quận 1 theo đơn liên công ty; phần sau sẽ thấy cửa hàng được báo."),
    (18, "Chạy thật đêm 16/09: PO HO106205 bên Dakao thành Sales Order S90018 bên Marou.",
         "Trợ lý không tự bấm Gửi đơn: gửi kéo theo Release, đó là quyết định của người mua."),
    (21, "Đã chạy thật 16/09/2026 trên NWV01: đơn HO106201, phiếu giao hàng 102043 bên Marou, phiếu nhận 107110 tại cửa hàng S0010.",
         "Policy P-12: loại đề xuất làm Business Central post chứng từ luôn cần người duyệt."),
    (22, "Đã thử thật: post xuất kho HO106204 ngoài trợ lý, trong vòng một phút cửa hàng S0005 có thẻ và email.", ""),
    (23, "Đã chạy thật trên Business Central", "Email và phiếu nhận trên Business Central"),
    (23, "Một đơn đi hết vòng", "Hai đầu của cùng một vòng"),
    (23, "Đơn mua HO106201 ở Dakao sang Marou thành đơn bán S90014, Marou xuất kho phiếu 102043 lô L260908-33110B.",
         "Email: trợ lý tự soạn khi Marou vừa xuất kho, gửi cửa hàng nhận hàng và Supply Chain, không có số lô."),
    (23, "Người duyệt bấm Duyệt thì Business Central post phiếu nhận 107110 tại cửa hàng Quán cà phê Đà Nẵng.",
         "Phiếu nhận: Business Central post sau khi người duyệt bấm Duyệt, đúng số lượng còn phải nhận."),
    (23, "Hai ảnh chụp trên môi trường demo NWV01 ngày 16/09/2026. Email gửi thật qua SMTP.",
         "Ảnh chụp trên môi trường demo. Email gửi qua SMTP."),
    (24, "Số đo được ngày 16/09/2026", "Số đo trên môi trường demo"),
    (24, "Cả ngày kiểm thử: 146 lượt gọi model, 0,085 USD.", "Cả vòng 20 bước demo: khoảng 0,08 USD."),
]

NOTE = {
1: """NÓI:
Em chào anh. Hôm nay NaviWorld trình bày phần POC về sức khỏe tồn kho và truy xuất lô, tức UC2, cùng với trợ lý AI chạy xuyên suốt.
Trước khi vào, em xin nói ba điều để anh có khung. Thứ nhất, mọi con số anh thấy hôm nay đều do Business Central và LS Central tính, trợ lý chỉ đọc lại chứ không tự tính. Thứ hai, trợ lý chỉ ghi đề xuất; chứng từ chỉ sinh ra khi người của Marou bấm Duyệt, và sinh ở trạng thái nháp. Thứ ba, phần AI bật tắt được và có trần chi phí.
Dữ liệu trong buổi này là bộ mô phỏng NaviWorld dựng trên danh mục thật của Marou, không phải số vận hành thật.

GHI CHÚ:
- Câu dữ liệu mô phỏng nói ngay từ đầu, để không ai hỏi lại giữa chừng.""",

2: """NÓI:
Phạm vi phần này là UC2: sức khỏe tồn kho theo lô, hạn dùng và truy xuất lô. Bên em đi ba bước: trước là trợ lý làm việc thế nào, sau là bản đồ tính năng, rồi mới tới từng kịch bản chạy trên hệ thống.

GHI CHÚ:
- Nếu bị rút giờ: giữ ba slide kiến trúc và các bước demo UC2, bỏ bớt phần UC5 và UC1.""",

3: """NÓI:
Slide này để anh nắm toàn bộ hệ thống trong một phút. Anh đi theo mũi tên giúp em.
Người của Marou hỏi một câu hoặc bấm nút trên thẻ. Trợ lý đọc những con số Business Central và LS đã tính: sức khỏe tồn kho, đề xuất bổ sung, dự báo, sổ kho, đơn mua, khuyến mãi.
Bước suy luận là chỗ có AI. Trợ lý ghép số liệu với bộ nhớ, ví dụ việc đang chờ hay đề xuất từng bị từ chối, và với kiến thức về cách LS tính, ngưỡng Marou đặt. Model chọn việc và viết lời, nhưng con số nào nó viết cũng phải có sẵn trong dữ liệu.
Bước cuối là đề xuất và nhắc: ghi đề xuất vào Business Central, gửi thẻ cho đúng người duyệt, nhắc qua chat và email, theo dõi đến khi chứng từ được post.
Băng dưới cùng là ranh giới quan trọng nhất: người bấm Duyệt thì Business Central mới tạo chứng từ, và chứng từ ở trạng thái nháp.

GHI CHÚ:
- Khách hỏi "AI có tự sửa dữ liệu không": không, nó chỉ ghi vào bảng đề xuất; chứng từ do Business Central tạo dưới tên người duyệt.""",

4: """NÓI:
Đây là câu trả lời cho câu hỏi "hệ thống có những gì". Slide chỉ ghi tên tính năng, chi tiết để phần sau.
Hai cột dọc là thứ đi xuyên mọi lớp. Cột bảo mật: kết nối bằng tài khoản ứng dụng của Entra, quyền tách riêng cho agent và người duyệt, agent không có quyền post, và model chỉ nhận phần kết quả đã lọc. Cột vận hành: lịch chạy nền mỗi sáng, bộ nhớ trợ lý, bộ đối chiếu độc lập, bộ test tự động.
Bảy lớp ngang anh đọc từ trên xuống. Lớp em muốn anh để ý là Năng lực AI với bốn nhóm: tóm tắt, tạo sinh nội dung, khám phá và phân tích, tự động hóa. Tính năng nào không thuộc bốn nhóm này thì bên em gọi đúng tên là tính năng ứng dụng.

GHI CHÚ:
- Khách hỏi về GPU, vector store: POC không cần, vì số liệu do Business Central tính và model chỉ nhận kết quả đã lọc.""",

5: """NÓI:
Slide này nối kiến trúc với bài toán của Marou. Marou có hai đơn vị. Marou là sản xuất, quản lý theo lô và hạn dùng. Dakao là bán lẻ, không quản lý lô. Hàng đi từ Marou sang Dakao bằng mua bán giữa hai công ty, giao thẳng tới từng cửa hàng.
Vì vậy trợ lý đề xuất khác nhau ở hai bên. Bên Marou là chuyển hàng nội bộ. Bên Dakao là đặt mua, với nhà cung cấp chính là Marou. Số lượng vẫn do LS Central tính.
Ở giữa là ba painpoint của kho bán lẻ theo bối cảnh hiện tại. Một, hàng về cửa hàng mà chứng từ nhận hàng dồn tới cuối tháng mới post, phải thuê người ngoài làm. Hai, muốn tự động hóa đơn qua lại giữa hai công ty. Ba, kết ca thiếu nguyên liệu.
Painpoint một và hai POC trả lời được, anh sẽ thấy ở phần liên công ty cuối buổi. Painpoint ba nằm ngoài phạm vi POC này, em nói thẳng từ đầu.

GHI CHÚ:
- Không nói "khảo sát"; đây là bối cảnh hiện tại, chưa khảo sát chính thức.
- Khách hỏi vì sao không tự gửi đơn: gửi đơn kéo theo Release, là quyết định của người mua.""",

6: """NÓI:
Đây là slide trả lời câu anh chắc chắn sẽ hỏi: AI nằm ở đâu, hay đây chỉ là phần mềm thường?
Mười ba tính năng, xếp vào bốn nhóm. Em không giải thích từng cái ở đây, vì các slide sau sẽ chạy thật cho anh xem.
Phần quan trọng nhất là khối phép kiểm bên dưới. Con số nào model viết ra cũng phải có trong dữ liệu code đưa cho nó; phương án nào nó chọn cũng phải nằm trong danh sách code đưa. Sai một điều là hệ thống bỏ đoạn đó, thay bằng câu mẫu, và thẻ ghi rõ lý do.
Ví dụ có thật: có lần model đọc mã lô rồi tự suy ra một ngày tháng không có trong dữ liệu. Hệ thống bỏ đoạn đó ngay. Đó là cách bên em chặn model bịa số.

GHI CHÚ:
- Khách hỏi "AI có sai không": câu văn có thể chưa hay, nhưng không thể đưa ra con số không có trong dữ liệu.
- G3 là email nhắc việc: nhắc post nhận hàng và báo người duyệt.""",

7: """NÓI:
Slide này dành cho anh kế toán, kiểm soát nội bộ và IT. Có bốn chốt chặn từ lúc có đề xuất tới lúc có chứng từ.
Chốt một nằm trong code: trợ lý không thể đề xuất chuyển năm trăm cái khi kho chỉ có hai trăm, và không ghi trùng việc đã có đề xuất đang chờ.
Chốt hai là policy, Marou tự sửa được: mỗi loại việc đặt là tự làm, đưa người duyệt, hay không bao giờ làm.
Chốt ba là người duyệt, thẻ đến đúng vai kèm đủ số liệu.
Chốt bốn là Business Central: chứng từ ở trạng thái nháp và mang số đề xuất, nên kiểm toán truy ngược được.
Riêng phần AI còn có công tắc và trần chi phí. Vượt trần thì trợ lý tự quay về câu mẫu, không báo lỗi giữa chừng.

GHI CHÚ:
- Khách hỏi dữ liệu có ra khỏi Việt Nam không: demo dùng Azure OpenAI ở Mỹ; khi triển khai chọn được vùng Asia Pacific. Ghi vào phần governance.""",

8: """NÓI:
Giờ em chuyển sang phần chạy thật. Buổi demo có hai mươi bước, bảy phần, và UC2 nằm ở trung tâm.
Ba phần đầu là UC2 trọn vẹn: nhìn con số tồn kho, xử lý một lô cận date, rồi hỏi tự do trên tồn kho. Sau đó em nối sang cửa hàng bán lẻ hết hàng, một nhịp dự báo, và khép lại bằng vòng liên công ty khi hàng về tới cửa hàng.
Mỗi bước là một nút trên màn hình; tên nút chính là câu em sẽ gửi cho trợ lý.

GHI CHÚ:
- Bị cắt giờ: đi bản 20 phút ở dải dưới slide.
- Hai câu hỏi tự do (bước 6, 7) và bước 13 không bấm sát nhau, tránh chạm hạn mức token mỗi phút.""",

9: """NÓI:
Em mở bằng tiền, không mở bằng tính năng. Đây là toàn bộ giá trị tồn đang có vấn đề, tính theo từng lô.
Anh nhìn bốn ô lớn: quá hạn, cận date, sắp hết hàng, chậm luân chuyển. Các con số này do Business Central tính, chạy tự động mỗi đêm hoặc bấm tay. Trợ lý không tính.
Ngày làm việc hiện ngay trên màn hình; mọi con số phía sau tính theo ngày đó.

GHI CHÚ:
- Khách hỏi vì sao là giá vốn: đây là giá trị tồn trên sổ, khớp Item Ledger Entry.""",

10: """NÓI:
Đây là ví dụ rõ nhất của nhóm tóm tắt. Trước đây brief là một danh sách thẻ dài, người đọc tự xếp thứ tự. Bây giờ trợ lý nói thẳng ba việc nên làm trước và vì sao.
Code đọc bảng, lọc ra vài dòng ứng viên, tính sẵn bán được bao nhiêu trước hạn, dư bao nhiêu. Model chỉ được chọn trong mấy dòng đó và chỉ dùng số đã đưa.
Điều một báo cáo tĩnh không làm được: brief nhớ đề xuất nào đã bị từ chối trong hai tuần và không đòi lại việc đó.

GHI CHÚ:
- Mất khoảng 30 giây, phần lớn là đọc Business Central. Nói trước để khách không tưởng máy treo.""",

11: """NÓI:
Đây là tính năng anh dễ thấy giá trị tiền nhất.
Một lô cận date: còn bao nhiêu, còn mấy ngày, cửa hàng này bán bao nhiêu, cửa hàng khác bán bao nhiêu. Code tính năm phương án: giữ tại chỗ, chuyển vừa đủ, chuyển rồi giảm giá phần dư, giảm giá, chấp nhận hủy, kèm giá trị cứu được của từng cái.
Chữ quan trọng là chuyển vừa đủ. Cửa hàng nhận chỉ nhận phần họ bán hết trước hạn, sau khi trừ tồn họ đang có. Chuyển cả lô sang chỗ khác chỉ là dời chỗ hàng sắp hỏng.
Model chọn một phương án và nói vì sao. Nó được chọn khác gợi ý của code, miễn lý do dựa trên số đã có.

GHI CHÚ:
- Mức giảm giá chưa có vì Marou chưa có quy tắc; cần chốt với Supply Chain.""",

12: """NÓI:
Ngay sau khi Supply Chain ghi đề xuất, người duyệt được gọi hai đường. Ai đang mở trợ lý thì thấy thẻ trong chat. Ai không mở thì nhận email.
Email này chia việc rõ: bảng mặt hàng, lô, tồn, giá trị, link mở trang đề xuất là code điền. Model chỉ viết hai đoạn lời: tình hình và vì sao cần duyệt sớm, rồi việc cần làm. Số nào trong đoạn lời cũng phải có trong dữ liệu.
Người đề nghị thấy ngay trong chat là thư đã gửi, gửi qua kênh nào, ai soạn.

GHI CHÚ:
- Lịch quét sáng không gửi email từng đề xuất, vì một lượt quét ghi tới 10 đề xuất; đã có brief tổng hợp.
- Khách hỏi gửi cho ai: POC gửi một hộp thư cấu hình sẵn; khi triển khai gắn theo vai người duyệt.""",

13: """NÓI:
Đây là chỗ em chứng minh ranh giới giữa trợ lý và hệ thống.
Trợ lý chỉ ghi vào bảng đề xuất, trạng thái luôn là chờ duyệt. Nó không có quyền tạo Transfer Order hay Item Journal.
Thẻ đi tới đúng người theo vai, có đủ mặt hàng, lô, tồn, giá trị, lý do, và dòng policy đã khớp.
Bấm Duyệt trên thẻ chính là gọi hàm duyệt trong Business Central. Người duyệt muốn làm hẳn trong Business Central cũng được, kết quả như nhau.
Từ chối cũng có giá trị: lý do được ghi lại, và brief hôm sau không đề xuất lại việc vừa bị bác.

GHI CHÚ:
- Bước 5 trên màn hình: Hùng bấm Duyệt, Transfer Order tạo ở trạng thái Open.""",

14: """NÓI:
Chắc anh sẽ hỏi: nếu tám mươi phần trăm câu hỏi nằm ngoài kịch bản thì sao? Hai câu này không có mẫu nào viết sẵn.
Câu thứ nhất: mặt hàng nào đang chậm luân chuyển. Model tự chọn cách đọc bảng tồn kho, xếp theo số ngày tồn đủ bán và số ngày không bán, rồi liệt kê từng cửa hàng.
Câu thứ hai em hỏi nối tiếp: có đề xuất CTKM gì để bán các mặt hàng này không. Chữ "các mặt hàng này" trợ lý hiểu được nhờ đọc lại mấy tin trước trong đoạn chat. Model đọc CTKM đang chạy của LS, thấy chưa có chương trình nào cho mặt hàng đó, rồi đề xuất giảm giá, combo hoặc đưa ra khu trưng bày.
Nó không đưa ra mức giảm bao nhiêu phần trăm, vì Marou chưa có quy tắc, và việc đó để người phụ trách chốt.

GHI CHÚ:
- Bấm "Xem các bước tôi đã tra" trên thẻ để khách thấy model gọi tool gì.
- Câu hai mất khoảng 30 giây, nói câu dẫn trong lúc chờ. Hai câu phải ở cùng một đoạn chat.""",

15: """NÓI:
Truy xuất là nửa sau của UC2. Em gõ số lô, trợ lý gom toàn bộ sổ kho của lô đó theo địa điểm: nhập bao nhiêu, xuất đi đâu, còn bao nhiêu ở đâu, hạn tới ngày nào.
Nếu phải thu hồi, anh biết ngay lấy lại ở đâu và bao nhiêu. Phần lời do AI viết, bảng sổ kho thu gọn bên dưới, có link mở đúng sổ kho của lô trong Business Central.

GHI CHÚ:
- Dùng lô L260906-33323C. Không dùng lô L260908-33110B vì lô đó đã quá hạn.""",

16: """NÓI:
Đây là nhóm khám phá: trợ lý chỉ ra thứ không ai hỏi tới.
Code quét năm tín hiệu, cái nào cũng kiểm lại được: bán sau hạn, nhận hàng mà hạn còn quá ngắn, hủy tăng gấp đôi, còn tồn mà không bán trong khi cửa hàng khác vẫn bán, và hết hàng lặp lại.
Model chỉ chọn ba tín hiệu đáng xử lý trước và viết nhận xét; nó không tự tạo tín hiệu mới.
Trên bộ dữ liệu này, tín hiệu nổi nhất là một cửa hàng nhận bánh tươi mà về tới nơi thì gần hết hạn. Báo cáo tồn kho thường không cho anh thấy điều đó.

GHI CHÚ:
- Lệch kiểm kê chưa quét được vì dữ liệu chưa có phiếu kiểm kê. Nói thẳng nếu khách hỏi.""",

17: """NÓI:
Giờ em chuyển sang bán lẻ. Anh Minh ở cửa hàng Hà Nội chỉ gõ một câu: sắp hết Ice cream ở cửa hàng tôi.
Trợ lý nhận ra mặt hàng, nhận ra cửa hàng của người hỏi, đọc con số LS Replenishment đã tính, ghi đề xuất đặt mua mười hai cái từ Marou giao thẳng cửa hàng, và gửi điều phối duyệt.
Rồi em hỏi tiếp vì sao LS ra số mười hai. Trợ lý đọc nhật ký tính của LS và kể lại: tồn tám chạm điểm đặt lại, LS đưa lên mức tối đa hai mươi, nên mua mười hai. Trợ lý không tính lại gì cả.

GHI CHÚ:
- Bước này ghi thật vào Business Central. Bấm lần hai trợ lý báo đã có đề xuất.
- Tham số nằm trên Item Card của LS, Marou tự sửa.""",

18: """NÓI:
Hai cú bấm, hai quyết định của người mua. Bấm Duyệt thì Business Central tạo đơn mua ở trạng thái Open. Bấm Gửi đơn sang Marou thì đơn mua bên Dakao thành đơn bán bên Marou, không ai phải nhập lại.
Trợ lý không tự bấm Gửi, vì gửi kéo theo Release, và đó là quyết định của người mua.

GHI CHÚ:
- Đây là Intercompany chuẩn của Business Central, bật được vì hai company chung một môi trường.""",

19: """NÓI:
Câu này không ai viết sẵn trả lời: tổng hợp những đề xuất bổ sung bất thường.
Model tự đọc toàn bộ đề xuất của LS. Code gắn cờ cho từng dòng: hết hàng quá nửa thời gian tính, không có bán bình quân mà vẫn đề xuất, tồn bằng không. Model chọn dòng đáng xem và nói vì sao.
Chỗ đáng nói là Croissant chocolate. LS coi nó hết hàng quá nửa số ngày, vì bánh tươi hủy cuối ngày nên tồn về không mỗi tối. Đây không phải lỗi của LS, mà là cách ghi hết hàng Marou cần xem lại.

GHI CHÚ:
- Câu trả lời đổi theo dữ liệu. Nếu model chọn dòng khác thì đọc lý do nó nêu.""",

20: """NÓI:
Một nhịp về dự báo. Dự báo không nằm ở bảng riêng của NaviWorld: nó ghi vào bảng dự báo chuẩn của LS, nên LS Replenishment dùng được ngay. Phương pháp là Holt-Winters, thống kê chuỗi thời gian; em nói rõ đây chưa phải AI, AI ở đây là phần kể lại kết quả.
Bên phải là CTKM. Trợ lý đọc chương trình khuyến mãi của LS và soi xem LS đã cộng nhu cầu khuyến mãi cho cửa hàng nào. Choco bowl giảm mười lăm phần trăm từ 23 tới 25 tháng 9, nhưng hai cửa hàng chưa có nhu cầu trong LS. Nghĩa là đúng ngày khuyến mãi, hai cửa hàng đó sẽ thiếu hàng.

GHI CHÚ:
- Khách hỏi WAPE, Bias là gì: mở tab Dự báo, phần Cách đọc.
- Lỗ hổng CTKM cố ý để trong dữ liệu để thấy trợ lý bắt được.""",

21: """NÓI:
Phần này trả lời hai painpoint anh đã thấy ở đầu buổi: nhận hàng post trễ, và đơn qua lại giữa hai công ty.
Em xin nói rõ là hai đầu không giống nhau. Bên Marou, bên bán, không có gì tự động; người kho vẫn post xuất kho như mọi ngày.
Bên Dakao, bên mua, trợ lý làm ba việc. Marou vừa xuất kho thì trợ lý báo ngay cho cửa hàng nhận hàng và Supply Chain để chuẩn bị, chỉ báo, không ghi gì. Qua ngày hôm sau mà vẫn chưa post nhận thì trợ lý nhắc lại và xin phép post thay. Người duyệt bấm Duyệt thì Business Central mới post phiếu nhận. Không ai duyệt thì không có gì được post.
Đây là loại đề xuất duy nhất mà duyệt làm Business Central post thật một chứng từ.

GHI CHÚ:
- Khách hỏi "vậy trợ lý được post rồi à": đúng, nhưng chỉ loại này, chỉ sau khi có người duyệt, và quyền post nằm trong permission set riêng phải gán tay.
- Khách hỏi sao không tự động luôn: tồn kho là số kế toán, post nhầm phải đảo bằng chứng từ khác.
- Số lô: bán lẻ không quản lý lô, trợ lý không đẩy số lô ra cho cửa hàng.""",

22: """NÓI:
Chắc anh sẽ hỏi: bên Marou bấm post thì làm sao trợ lý biết?
Trợ lý không cần ai báo. Mỗi phút nó đọc phiếu giao hàng bên Marou. Phiếu giao hàng mang số đơn mua của Dakao, do Intercompany điền sẵn, nên trợ lý nối được hai chứng từ. Phiếu nào chưa từng báo thì trợ lý báo cửa hàng nhận hàng, điều phối và Supply Chain, và gửi email.
Việc này chỉ đọc, không ghi gì vào sổ.

GHI CHÚ:
- Diễn trên màn hình: bấm nút demo 19, hoặc mở Business Central company NWV-MAROU, Sales Order S90016 (đơn HO106203, lô đã gán sẵn), bấm Post, chọn Ship, rồi đợi tối đa một phút.
- Giới hạn: đơn xuất trước lúc máy chủ trợ lý khởi động thì không tự báo; nút Kiểm hàng vẫn báo được.""",

23: """NÓI:
Đây là hai đầu của cùng một vòng, chụp trên môi trường demo.
Bên trái là email trợ lý tự soạn khi Marou vừa xuất kho. Danh sách đơn, mặt hàng, số lượng và link mở đơn đều do code điền. Anh để ý email này không có số lô, vì Dakao là bán lẻ, số lô không phải việc của cửa hàng.
Bên phải là phiếu nhận Business Central post sau khi người duyệt bấm Duyệt. Trợ lý không dừng ở chỗ gửi thông báo.

GHI CHÚ:
- Khách để ý địa chỉ Gmail: tenant demo không có license Exchange Online nên POC gửi qua SMTP; triển khai thật dùng hộp thư của Marou.
- Phiếu nhận trong ảnh có lô vì dữ liệu demo bên Dakao còn bật quản lý lô. Đừng hứa bán lẻ truy được lô.""",

24: """NÓI:
Slide này cho người trả tiền. Em nói ba ý.
Một, token là số đếm thật từ Azure sau mỗi lượt gọi; tiền là ước tính theo đơn giá công bố, hóa đơn thật mới là số cuối.
Hai, chi phí nhỏ là do kiến trúc: câu nào rule trả lời được thì không gọi model, và model chỉ nhận bảng số đã lọc.
Ba, có phanh thật: trần theo ngày và trần cộng dồn, vượt thì trợ lý tự quay về câu mẫu. Quản trị xem được chi phí theo từng việc và tắt AI bất cứ lúc nào.

GHI CHÚ:
- Khách hỏi chi phí khi chạy thật cho cả Marou: phụ thuộc số người dùng và số câu hỏi mở; đề nghị đo trong thí điểm với trần đặt sẵn, đừng hứa con số.""",

25: """NÓI:
Để kết, em chia ba cột cho rõ trách nhiệm. Cột xanh là những gì đã chạy. Cột vàng là những gì đang mở rộng. Cột đỏ là những điều cần Marou quyết: ai được quyền post phiếu nhận, có mở thêm loại chứng từ nào không, vùng xử lý dữ liệu, ngưỡng và policy chính thức.
Bước tiếp theo bên em đề nghị là một bước nhỏ: chốt ngưỡng và policy với Supply Chain, dựng dữ liệu bán lẻ riêng cho Dakao, rồi chạy thử một tuần thật với trần chi phí đặt sẵn.
Và em nhắc lại: toàn bộ số liệu hôm nay là dữ liệu mô phỏng NaviWorld dựng trên danh mục của Marou. Em cảm ơn anh.

GHI CHÚ:
- Đừng gộp ba cột làm một; khách cần biết phần nào phụ thuộc họ.""",
}
