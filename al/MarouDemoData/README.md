# NWV Marou Demo Data (sandbox only)

Extension độc lập, một nút bấm, tạo dữ liệu giả lập cho POC UC2 trên sandbox bằng cách post thật qua Item Journal. Không phụ thuộc Foundation hay Data Readiness, nên cài được trước cả hai.

## Chạy

1. Publish lên sandbox (VS Code, symbol từ sandbox). Cần company đã có posting group, ví dụ tạo từ dữ liệu mẫu. Nếu company trống hoàn toàn, codeunit báo lỗi rõ ràng chứ không cố post.
2. Tell me, gõ `NWV Demo Data`, bấm **Tạo dữ liệu demo**. Chạy vài phút, có thanh tiến độ theo ngày.
3. Sau đó chạy `NWV Data Readiness` rồi `NWV Inv. Health Calc` (qua NWV Agent Setup hoặc Job Queue).

Chạy lần hai bị chặn vì đã có Item Ledger Entry của item `MAR-*`.

## Tạo gì

- Item Tracking Code `LOTEXP`: theo lô, có hạn dùng, bắt buộc nhập hạn khi nhập kho.
- 5 nhóm hàng BAR, CONF, DRINK, GIFT, INGR. 12 item cùng mã với `python/bc_agent/make_fixtures.py`.
- Location `WH-HCM`, `S-CALMETTE`, `S-THAODIEN`, `S-HANOI`, `S-DANANG`, và `IN-TRANSIT`; Transfer Route từ kho tới từng cửa hàng.
- Reason Code `NWV-EXP` cho write-off.
- Mỗi cặp item và location một lô nhập tại đầu kỳ, số lượng bằng tổng sẽ bán trong 120 ngày cộng tồn mục tiêu cuối kỳ, nên sau khi post hết lịch sử thì tồn đúng như kịch bản.
- 120 ngày lịch sử bán, Entry Type Sale, mỗi ngày một lần post batch.

## Kịch bản có chủ ý

| Tình huống | Item, location | Tầng mong đợi |
|---|---|---|
| Lô hết hạn 3 ngày, 27 hộp | MAR-BONBON-9, S-DANANG, lô `L...1` | Expired |
| Còn 12 ngày đến hạn, 40 hộp, bán không kịp | MAR-BONBON-16, S-HANOI, lô `L...1` | Near Expiry |
| Còn 3 thanh, vừa qua hội chợ rồi đứt hàng 9 ngày | MAR-BR76-80, S-DANANG | Stock-out Risk |
| Còn 12, cửa hàng bán mạnh nhất | MAR-MINI-24, S-CALMETTE | Stock-out Risk |
| Hộp quà Tết không bán từ tháng 3 | MAR-GIFT-TET, mọi nơi | Slow-moving |
| Lô `L2605190` 900 gói, không ai lấy | MAR-COCOANIB-100, WH-HCM | Slow-moving hoặc Excess |
| 488 tại kho, 313 tại Thảo Điền | MAR-MINI-24 | Healthy, dùng cho kịch bản 220 khách |

Số bán mỗi ngày sinh bằng LCG có seed theo cặp và ngày, nên hai lần chạy trên hai sandbox ra cùng bộ số.

## Không làm

Không tạo Sales Order, không tạo Transfer Order, không đụng tới LS Central. Không dùng trên production.
