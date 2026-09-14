# NWV Marou Data Readiness

Extension chạy một lần trong tuần đầu của POC, để trả lời câu hỏi phải trả lời trước khi chốt phạm vi: dữ liệu của Marou có đủ để UC2 chạy không.

Nó chỉ đọc. Không ghi gì vào dữ liệu chuẩn, không tạo chứng từ, không sửa master data. Không phụ thuộc extension nào khác, không phụ thuộc LS Central, không cần đăng ký Entra app.

## Deploy

1. Mở thư mục `al/MarouDataReadiness` trong VS Code có AL extension.
2. `AL: Download symbols` từ sandbox Marou. `app.json` khai `application` 27.0, sandbox 28.x vẫn build được.
3. `AL: Package` rồi `AL: Publish`.
4. Gán permission set `NWV DATA READINESS` cho tài khoản sẽ chạy, hoặc chạy bằng tài khoản SUPER.

## Chạy

Tìm `NWV Data Readiness` trong ô tìm kiếm, mở trang, bấm **Chạy kiểm tra**.

Kết quả ra 17 dòng chia bốn nhóm. Dòng màu đỏ là thứ phải sửa trước khi cam kết phạm vi. Dòng màu vàng là thứ nên biết nhưng không chặn. Cột cuối nói rõ nếu chỉ số đó thấp thì phần nào của POC bị ảnh hưởng.

Trang là List page chuẩn nên xuất Excel bằng **Open in Excel** để đưa vào biên bản.

## Bốn nhóm kiểm tra

| Nhóm | Trả lời câu hỏi gì |
|---|---|
| Lô và hạn dùng | UC2 có chạy được không. Đây là nhóm quan trọng nhất |
| Lịch sử bán | Tốc độ bán bình quân và Days of Cover có đáng tin không |
| Master data | Có quy tồn ra tiền được không, có đặt ngưỡng riêng theo nhóm hàng được không |
| Sẵn sàng cho UC5 | Có tạo được Transfer Order giữa các địa điểm không |

## Ngưỡng kết luận

| Mã | Đạt khi | Chặn khi | Vì sao |
|---|---|---|---|
| DR-02 Lot No. | từ 80% | dưới 40% | Không có lô thì phân tầng chỉ chạy ở mức Item và Location |
| DR-03 Expiration Date | từ 80% | dưới 40% | Thiếu thì bậc Expired và Near Expiry của cây phân tầng rỗng |
| DR-05 Item Tracking Code | từ 80% | dưới 40% | Không bật thì hàng nhập sau vẫn không có lô, DR-02 không tự cải thiện |
| DR-11 Độ dài lịch sử | từ 12 tháng | dưới 6 tháng | Dưới 6 tháng thì tốc độ bán không đáng tin; dưới 12 tháng không bắt được mùa Tết |
| DR-13 Số cặp có bán | từ 20 cặp | dưới 5 cặp | Mỗi cặp là một dòng trong bảng bổ sung hàng |
| DR-20 Item Category | từ 90% | dưới 60% | Không phân nhóm thì phải dùng một ngưỡng cận date chung cho cả bar lẫn bonbon |
| DR-22 Unit Cost | từ 95% | dưới 80% | Thiếu giá vốn thì con số giá trị tồn xấu thấp hơn thực tế |
| DR-23 Số địa điểm | từ 2 | dưới 1 | Một địa điểm thì không có gì để điều chuyển |
| DR-32 Transfer Route | từ 1 tuyến | 0 tuyến | Không có route thì phần hành động của UC2 và UC5 dừng ở mức đề xuất |

DR-01, DR-04, DR-10, DR-12, DR-19, DR-21, DR-30, DR-31 chỉ là thông tin, không có ngưỡng đạt hay không đạt.

## Nguồn dữ liệu từng chỉ số

Expiration Date được đọc từ `Item Ledger Entry`, không phải từ `Lot No. Information`. Đây là điểm hay nhầm.

Dòng tồn được định nghĩa là Item Ledger Entry có `Open` bằng true và `Remaining Quantity` lớn hơn 0. Mặt hàng được đếm là Item có `Type` bằng Inventory và `Blocked` bằng false. Địa điểm không tính kho trung chuyển, tức `Use As In-Transit` bằng false.

## Xem trước kết quả mà không cần sandbox

`python/tools/readiness_sim.py` chạy lại đúng logic này bằng Python trên bộ fixtures, với hai kịch bản: dữ liệu đầy đủ và dữ liệu thiếu. Dùng để thấy trước bảng kết quả trông thế nào, và để kiểm tra ngưỡng có hợp lý không.

```bash
cd python && python3 tools/readiness_sim.py
```

## Trạng thái

Đã qua linter `tools/al_lint.py`, chưa compile bằng AL compiler vì máy sinh mã không có symbol của sandbox. Lỗi cú pháp nếu còn sẽ hiện ngay ở bước Package.
