# Lộ trình demo, bản 3

Ghi chú nội bộ cho người trình bày, không phải tài liệu gửi Marou. Viết lại ngày 14/09/2026.

Bản 2 dựng quanh UC2 và "yêu cầu mở" (tiệc 150 khách), vì lúc đó tài liệu 03, 04, 07 gọi nhầm UC10 là yêu cầu mở. RFP
gốc gọi UC10 là Supply Chain & Retail AI Assistant: câu hỏi đã duyệt, giải thích ngoại lệ, liên kết sang dashboard, và
hành động được đề xuất. Dũng đã chốt POC A (UC1, UC2, UC5) cộng POC D (UC10 và dashboard). Bản này đi theo đúng thứ tự
đó. Nhóm nút "Kịch bản demo" trên giao diện cũng xếp theo thứ tự này.

Nguyên tắc giữ từ bản 2: mở bằng con số, nói trước phần nào không cần model, rồi mới tới phần agent.

## Chuẩn bị

1. Business Central NWV01, company NWV, Work Date 18/09/2026.
2. Trên page NWV Agent Setup bấm Run Inventory Health, Run Forecast Accuracy, Run Supplier Scorecard. Tính LS
   Replenishment: `cd python; python ../tools/ls_replen_setup.py calc`.
3. Đối chiếu trước giờ, cả ba lệnh phải báo trùng khớp:
   `python -m bc_agent.cli uc2-reconcile`, `uc1-reconcile`, `uc3-reconcile`.
   Lần chạy 14/09/2026: UC2 167 dòng 45/32/47/4/1/38, UC1 148 dòng, UC3 6 dòng, không lệch.
4. Trợ lý để ở Business Central. Đổi nguồn mất khoảng 20 giây; đừng bấm kịch bản khi dải trên cùng chưa báo xong.
5. Vai Dũng, tab Cài đặt AI: quyết định bật hay tắt AI. Các màn 1 đến 5 không cần model. Màn 6 cần model nếu muốn cho
   xem câu ngoài kịch bản.
6. Nâng hạn mức token mỗi phút của deployment `gpt-4.1-mini` lên ít nhất 30.000 trên Foundry (đang 10.000).
7. Mở sẵn Business Central ở màn hình thứ hai. Mọi thẻ đều có liên kết mở thẳng đúng page, đúng bộ lọc; đã thử trên
   Chrome thật với Item Ledger Entries lọc theo lô và NWV Supplier Scorecard lọc theo nhà cung cấp.

## Màn 1. Dự báo đang sai ở đâu (UC1, 3 phút)

Vai Trang, nút "Dự báo đang sai ở đâu", rồi tab Dự báo.

Số trên BC: 74 cặp mặt hàng và điểm bán, kỳ kiểm tra 22/08 đến 18/09. Trung bình 28 ngày sai 38,7%, trung bình cùng thứ
8 tuần sai 41,2%. 20 cặp vượt ngưỡng, nặng nhất Tiramisu, Pecan pie, Ice cream ở Nhà hàng Thảo Điền. Bấm một cặp để xem
biểu đồ thực tế và dự báo theo ngày.

> Nói trước: đây là baseline, chưa phải mô hình AI. Nó là cái thước. Mô hình nào Marou mua sau này phải thắng con số
> 38,7% trên cùng kỳ kiểm tra. Ngày hết hàng bị loại khỏi phép đo, vì hết hàng thì bán 0 không phải do dự báo sai.

## Màn 2. Vì sao LS đề xuất con số đó (UC5, 4 phút)

Vai Trang, nút "Vì sao LS đề xuất 82 Choco nuts". Thẻ đọc nhật ký tính của LS Central, không tính lại:
bán bình quân 11,675 một ngày nhân 7 ngày phủ, trừ tồn khả dụng 0, ra 82. Bấm liên kết "Nhật ký tính của LS" để mở đúng
dòng trong BC.

Tiếp nút "Hàng min-max: Ice cream". Mặt hàng này đặt kiểu Stock Levels: tồn khả dụng 8 chạm Reorder Point 8 nên LS đưa lên
Maximum Inventory 20, cần 12; nhưng kho chỉ còn 25 cho tổng 26 của các cửa hàng nên LS chia lại, cửa hàng này còn 11.

> Chốt: Marou không phải tin một con số từ hộp đen. Mỗi đề xuất của LS có câu giải thích bằng tiếng Việt và nguyên văn
> nhật ký. Muốn đổi kết quả thì thẻ chỉ đúng field phải sửa.

Nếu khách hỏi có phải viết tay cho hai mặt hàng này: không. Bộ diễn giải đọc 194 mẫu câu LS ghi log, lấy từ source LS
28.0.10.3586, và nhận dạng 100% của 2.861 dòng log trên BC ngày 14/09.

## Màn 3. Sức khỏe tồn kho và truy xuất lô (UC2, 4 phút)

Tab Sức khỏe tồn kho: giá trị tồn ở bốn tầng xấu. Bấm một dòng để xem nguồn số, quy tắc phân tầng, lịch sử bán.

Vai Hùng, nút "Kho hỏi hàng hết hạn": 45 lô đã hết hạn, chia theo địa điểm, thẻ đề xuất hủy có số lô.

Nút "Truy xuất lô bánh quá hạn": lô L260908-33170B Chocolate cake, hạn 13/09, nhập 08/09 ở W0003, đã bán 8, còn 12 ở
Cửa hàng Quận 1 và 2 ở Cửa hàng Hà Nội. Thẻ nói nếu thu hồi thì lấy lại ở đâu. Bấm "Item Ledger Entries của lô".

> Chốt: hệ thống không bịa số. Mỗi con số mở ra được chứng từ gốc.

## Màn 4. Nhà cung cấp (UC3, 2 phút, ngoài POC A nhưng RFP có)

Vai Trang, nút "Nhà cung cấp hay giao trễ". AL-s Foods giao đúng hạn 48,7%, hứa 7 ngày mà thực tế 9; Dan-s Dairy 86,2%,
hứa 3 ngày thực tế 3,2. Bấm "Xem đơn quá hạn" trên thẻ.

> Nói thẳng: đơn mua và phiếu nhận là dữ liệu demo NaviWorld tạo trên BC, không phải lịch sử của Marou. Phiếu nhận post vào
> địa điểm riêng NCC-NHAN rồi xuất bù, để không làm lệch tồn của UC2 và LS.

## Màn 5. Từ đề xuất ra chứng từ (UC10 hành động đề xuất, 3 phút)

Vai Hùng bấm Brief: thẻ đề xuất chuyển hàng theo số của LS, đề xuất đang chờ từ trước hiện lại, không tạo trùng. Sửa số lớn
hơn tồn nguồn rồi duyệt: trợ lý chặn. Duyệt số hợp lệ, mở Transfer Order vừa sinh trong BC.

> Chốt: trợ lý chỉ ghi đề xuất ở trạng thái Proposed. Người duyệt bấm, BC tạo chứng từ. Ranh giới nằm trong permission set.

Sau buổi demo nhớ xoá TO thử bằng `NWVDemoRepost.CleanupAgentTests`, vì TO Open cộng vào Quantity in Transfer In/Out của LS.

## Màn 6. Câu hỏi đã duyệt (UC10, 4 phút)

Đây là màn trả lời câu "80% câu hỏi nằm ngoài kịch bản".

1. Bật AI. Vai Trang gõ một câu chưa có sẵn, ví dụ `so sánh tốc độ bán Flavored syrup giữa các cửa hàng 30 ngày qua,
   chỗ nào nên giữ ít hàng lại`. Model tự dựng chuỗi tra cứu. Lần đo 14/09: 24 giây, năm lượt gọi model, khoảng 0,005 USD.
2. Vai Dũng, tab Nhật ký agent, "Lưu thành kịch bản". Màn xem trước cho thấy code gắn từng con số vào một ô kết quả tra cứu
   và chỉ ra câu kết luận viết cố định. Sửa thành câu trung tính, lưu.
3. Hỏi lại cùng câu với mặt hàng khác: trả lời ngay, thẻ ghi kịch bản đã duyệt, không gọi model.

Cũng nên cho thấy câu viết khác kiểu rule quen vẫn vào đúng việc. Lần thử 14/09 với AI bật: "bên nào ship hàng cho mình
tệ nhất mấy tháng qua" vào scorecard nhà cung cấp, "phương pháp đoán nhu cầu hiện giờ lệch nhiều nhất ở món nào" vào độ
chính xác dự báo, mỗi câu khoảng 4 giây.

## Màn 7. Đóng sổ (2 phút)

Tab Cài đặt AI: token đã dùng, chi phí ước tính, trần chi phí, tỉ lệ câu trả lời bằng dữ liệu. Tắt AI: số trên Sức khỏe tồn
kho, Dự báo, Nhà cung cấp không đổi một chữ số nào, vì số do Business Central tính.

## Nếu khách hỏi khó

**"Dự báo này là AI à?"**
Không. Đây là baseline để đo. Phần AI ở UC1 là bước sau, và nó phải thắng baseline trên cùng kỳ kiểm tra thì mới đáng mua.

**"Sao không dùng Demand Forecast có sẵn của Microsoft?"**
Trước khi trả lời phải tra lại Microsoft Learn theo release wave hiện hành. Không hứa tính năng preview.

**"80% câu hỏi sẽ nằm ngoài kịch bản."**
Câu ngoài kịch bản không có nghĩa là không trả lời được: model tự dựng chuỗi tra cứu. Giới hạn thật là dữ liệu mà công cụ
đọc được; câu cần sản xuất hay công nợ thì phải thêm API page. Tỉ lệ thật đo trong tuần chạy thử, không ai biết trước 80%.

**"Sao biết nó không bịa số?"**
Số đến từ bảng AL tính trong BC và nhật ký của LS. Ba lệnh đối chiếu chạy bản Python độc lập trên cùng dữ liệu và ra
cùng con số. Khi lưu kịch bản, số nào không truy được về dữ liệu bị chỉ ra trên màn hình.

**"Chi phí bao nhiêu?"**
Câu rule đọc được và câu chạy kịch bản không tốn token. Câu hỏi mở đo thật khoảng 0,002 đến 0,005 USD trên `gpt-4.1-mini`
theo đơn giá công bố. Có trần cứng theo ngày và cộng dồn. Hóa đơn Azure mới là con số cuối cùng.

**"Dữ liệu có ra khỏi Việt Nam không?"**
Extension của bên thứ ba tự chọn region. Bản POC chạy ở eastus; nếu Marou yêu cầu thì dùng Data Zone Standard, phạm vi Asia
Pacific.
