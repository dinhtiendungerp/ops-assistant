const { p, h1, h2, h3, bullet, num, table, pageBreak } = require("./lib");

const part2 = [
  pageBreak(),
  h1("5. Kế hoạch theo giai đoạn"),
  p("Mỗi giai đoạn dưới đây có mục tiêu, việc cụ thể ở mức object, người làm, tiêu chí xong, và điều gì làm nó trượt. Việc được đánh số để dùng làm work item trong DevOps."),

  h2("5.1 Giai đoạn 0. Độ phủ dữ liệu (tuần 1)"),
  p("Mục tiêu: biết trước khi cam kết. Kết quả của giai đoạn này quyết định tầng nào của cây được cam kết số, tầng nào chỉ báo cáo độ phủ."),
  table(["Việc", "Ai", "Chi tiết"], [
    ["0.1 Marou tạo sandbox chép từ production", "Marou IT", "Admin center, copy environment. Cần quyền admin phía Marou. Nửa ngày kể cả chờ copy"],
    ["0.2 Build và publish NWV Marou Data Readiness", "AL dev", "Mở VS Code, tải symbol từ sandbox, build, publish PTE. Đây là lần compile thật đầu tiên, sửa lỗi cú pháp nếu có"],
    ["0.3 Chạy 17 kiểm tra, xuất Excel", "Consultant", "Page NWV Data Readiness, action Chạy kiểm tra, Open in Excel. Lưu file vào biên bản tuần 1"],
    ["0.4 Xác nhận năm điểm với Marou", "Consultant, Marou", "Chu kỳ post Statement từ LS POS về Item Ledger Entry. Số tháng lịch sử trong BC. Item Category đã phân nhóm chưa. Danh sách Location là cửa hàng. Ai duyệt đề xuất hằng ngày"],
    ["0.5 Họp chốt phạm vi tầng", "Dũng, Marou", "Quyết định số 1 ở mục 1. Ghi vào biên bản: tầng nào cam kết, tầng nào chỉ độ phủ, ngưỡng khởi điểm theo Item Category"],
  ], [2.0, 1.0, 3.0]),
  p("Tiêu chí xong: có file Excel 17 dòng trên dữ liệu thật, có biên bản chốt tầng cam kết và ngưỡng khởi điểm."),
  p("Điều làm nó trượt: Marou không cấp sandbox hoặc không cấp quyền publish PTE. Nếu vậy NaviWorld chỉ chạy được trên fixtures và toàn bộ lịch lùi theo."),
  p("Điểm kỹ thuật cần nói rõ: tốc độ bán trong NWV Inv. Health Calc đọc từ Item Ledger Entry loại Sale. Với LS Central, POS transaction chỉ về Item Ledger Entry khi Statement được post. Nếu Marou post Statement hằng ngày thì số bán trễ một ngày, chấp nhận được. Nếu post theo tuần thì tốc độ bán của bảy ngày gần nhất luôn bằng không, và phải đổi sang đọc Trans. Sales Entry qua adapter LS Central. Câu hỏi này rẻ ở tuần 1 và đắt ở tuần 4."),

  h2("5.2 Giai đoạn 1. Lõi tính toán và trang Business Central (tuần 2 tới 3)"),
  p("Mục tiêu: người của Marou mở BC ra thấy con số tiền và tự đối chiếu được từng dòng. Đây là quick win."),
  table(["Việc", "Ai", "Chi tiết"], [
    ["1.1 Build và publish NWV Marou Agent Foundation", "AL dev", "Lần compile thật đầu tiên của 36 object. Dự phòng một ngày sửa lỗi compile và lỗi tham chiếu LS Central"],
    ["1.2 Table NWV Inv. Health Snapshot (70108)", "AL dev", "Khoá: Run No., Tier. Trường: Run Date, Run Type (Baseline, Daily), Lines, Quantity, Inventory Value. Mỗi lần CalculateAll ghi sáu dòng, một dòng mỗi tầng"],
    ["1.3 Codeunit NWV Inv. Health Snapshot Mgt. (70106)", "AL dev", "TakeSnapshot sau CalculateAll. LockBaseline: đánh dấu run đầu tiên là Baseline, không cho ghi đè. Compare(RunNo) trả chênh lệch theo tầng"],
    ["1.4 Page NWV Inv. Health Lines (70108), list", "AL dev", "Nguồn NWV Inv. Health Line. Sắp theo Risk Score giảm dần. StyleExpr theo Tier. Filter nhanh theo tầng. Action mở Item Ledger Entry lọc theo Item, Location, Lot; action mở Lot No. Information; action Tạo đề xuất gọi NWV Agent Proposal Mgt. Open in Excel có sẵn của BC"],
    ["1.5 Page FactBox (70117), CardPart", "AL dev", "Hiện sáu chỉ số, ngưỡng đã áp cho Item Category của dòng, và bậc nào của cây đã khớp. Đây là bản AL của panel “con số này ở đâu ra” trong demo web"],
    ["1.6 Table cue (70109) và page Activities (70118)", "AL dev", "Sáu ô: giá trị theo tầng, kèm mũi tên so với baseline. Gắn vào Role Center của Supply Chain qua pageextension. Không cần Power BI"],
    ["1.7 Action Lập lịch Job Queue trên NWV Agent Setup", "AL dev", "Tạo Job Queue Entry cho codeunit 70105, tham số INVHEALTH, chạy 05:00 hằng ngày, Maximum No. of Attempts 3"],
    ["1.8 Kiểm tra tốc độ bán theo kết quả 0.4", "AL dev", "Nếu Statement không post hằng ngày: viết codeunit adapter đọc Trans. Sales Entry, cùng mẫu với NWV LS Discount Adapter (70200)"],
    ["1.9 Test trên sandbox với dữ liệu thật", "Consultant", "Chạy CalculateAll, đo thời gian chạy, kiểm 10 dòng bất kỳ so với Item Ledger Entry. Ghi lại thời gian chạy để quyết lịch Job Queue"],
    ["1.10 Buổi xem số đầu tiên với Marou", "Dũng, Marou", "Mở page 70108, đọc con số tiền theo tầng, mở hai dòng đối chiếu trước mặt họ. Ghi lại phản hồi về ngưỡng"],
  ], [2.0, 0.9, 3.1]),
  p("Tiêu chí xong: Job Queue chạy ba đêm liên tiếp không lỗi trên sandbox, page 70108 hiện đúng số, 10 dòng kiểm tay khớp, Marou đã xem và có ý kiến về ngưỡng."),
  p("Điều làm nó trượt: thời gian chạy CalculateAll trên khối lượng thật. Codeunit quét Item Ledger Entry còn mở theo Item, Location, Lot rồi gọi GetSalesVelocity cho từng cặp. Với vài chục cửa hàng và vài trăm SKU thì vài phút; với hàng nghìn cặp thì phải đổi sang tính tốc độ bán một lượt bằng query rồi tra lại. Đo ở 1.9 rồi mới quyết, không đoán."),

  h2("5.3 Giai đoạn 2. Hành động ghi ngược Business Central (tuần 3 tới 4)"),
  p("Mục tiêu: từ một dòng xấu ra một chứng từ chờ duyệt bằng một nút bấm, dưới quyền người bấm, và hoàn tác được."),
  table(["Việc", "Ai", "Chi tiết"], [
    ["2.1 Nhánh Transfer trong Execute", "AL dev", "Đã có. Kiểm lại với Transfer Route thật của Marou và Location In-Transit"],
    ["2.2 Nhánh Write-off trong Execute", "AL dev", "Tạo Item Journal Line trong template ITEM, batch NWV-WO: Entry Type Negative Adjmt., Item, Location, Lot qua Reservation Entry, Quantity, Reason Code NWV-EXP. Không post. Batch này đi qua Item Journal Batch Approval Workflow, tính năng chuẩn từ BC 2026 wave 1. Hai lớp duyệt là chủ ý: Supply Chain duyệt đề xuất, Kế toán duyệt batch rồi post. Việc gửi duyệt tự động từ code phụ thuộc event của Approvals Mgmt. có sẵn cho item journal ở v28 hay không, kiểm khi compile; nếu không có thì Kế toán bấm Send for approval trên journal"],
    ["2.3 Nhánh Block Purchase trong Execute", "AL dev", "Đặt Item.Purchasing Blocked = true, ghi Review Comment kèm ngày. Hoàn tác đặt lại false. Chỉ áp cho tầng Excess và Slow-moving"],
    ["2.4 Nhánh Markdown", "AL dev", "Chỉ ghi Status Executed với Result Document Type là Ghi nhận. Không tạo Periodic Discount trong LS Central ở POC này"],
    ["2.5 Action Hoàn tác trên page NWV Agent Proposals", "AL dev", "Transfer: xoá Transfer Order nếu chưa ship. Write-off: xoá dòng journal nếu chưa post. Block Purchase: bỏ cờ. Ghi ai hoàn tác, lúc nào"],
    ["2.6 FactBox bằng chứng trên đề xuất", "AL dev", "Đọc Evidence JSON, hiện dạng cặp tên và giá trị. Người duyệt không phải đọc JSON"],
    ["2.7 Workflow Item Journal Batch Approval", "Consultant", "Cấu hình trên sandbox: template ITEM, batch NWV-WO, approver là người Marou chỉ định ở 0.4. Đây là cấu hình chuẩn, không code"],
    ["2.8 Permission set NWV AGENT REVIEW", "AL dev", "Thêm quyền Item Journal Line RIMD, Item M cho trường Purchasing Blocked, Transfer Header và Line RIMD. Vẫn không có quyền post"],
    ["2.9 UAT bốn kịch bản với Marou", "Consultant, Marou", "Duyệt Transfer, duyệt Write-off rồi thấy approval request, Block Purchase rồi thử tạo Purchase Order bị chặn, hoàn tác cả ba"],
  ], [2.0, 0.9, 3.1]),
  p("Tiêu chí xong: bốn kịch bản UAT pass trên sandbox, có ảnh chụp chứng từ trong BC cho từng kịch bản, permission set được Marou IT xem qua."),
  p("Điều làm nó trượt: Item Tracking. Nếu item của Marou dùng Item Tracking Code có Lot, dòng Item Journal phải kèm Reservation Entry đúng lot mới post được. Phần này AL chuẩn nhưng dễ sai, cần test với item thật chứ không phải CRONUS."),

  h2("5.4 Giai đoạn 3. Đo lường (tuần 4 tới 5)"),
  p("Mục tiêu: cuối POC chứng minh được bằng số, không bằng cảm nhận."),
  table(["Việc", "Ai", "Chi tiết"], [
    ["3.1 Page NWV Inv. Health KPI (70109)", "AL dev", "Bảng hai cột: baseline và hiện tại. Dòng: giá trị tồn từng tầng xấu; giá trị đã có đề xuất được duyệt; số đề xuất duyệt không sửa trên tổng; số hoàn tác; thời gian trung bình từ Created At tới Reviewed At. Open in Excel"],
    ["3.2 API page inventoryHealthSnapshot (70119)", "AL dev", "Đọc snapshot theo run. Dùng cho Copilot Studio hoặc Power BI nếu chọn"],
    ["3.3 Quy trình khoá baseline", "Consultant", "Lần chạy thật đầu tiên trên production được đánh Baseline trước khi mở quyền duyệt cho Marou. Ghi biên bản kèm ảnh page KPI ngay lúc đó"],
    ["3.4 Bảng lấy mẫu nghiệm thu", "Consultant", "Excel 20 dòng chọn ngẫu nhiên trải sáu tầng, cột hệ thống nói gì, cột chứng từ gốc nói gì, cột khớp hay không. Chuẩn bị mẫu ở tuần 5, điền ở buổi nghiệm thu"],
    ["3.5 Nhật ký tuần", "Consultant", "Mỗi tuần một trang: Job Queue chạy mấy đêm, mấy lỗi, KPI tuần này, đề xuất nào bị từ chối và vì sao. Đây là nguồn cho phần rủi ro của báo cáo cuối"],
  ], [2.0, 0.9, 3.1]),
  p("Tiêu chí xong: page KPI hiện đúng số trên sandbox, mẫu Excel lấy mẫu đã có, quy trình khoá baseline viết thành một trang."),

  h2("5.5 Chạy thật và nghiệm thu (tuần 5 tới 10)"),
  table(["Tuần", "Việc"], [
    ["5", "Cài hai PTE lên production Marou. Chạy CalculateAll lần đầu, khoá baseline. Lập lịch Job Queue. Mở quyền duyệt cho người Marou chỉ định"],
    ["6 tới 9", "Marou duyệt đề xuất hằng ngày. NaviWorld theo dõi Job Queue Log Entry, họp 30 phút mỗi tuần đọc page KPI và nhật ký tuần. Chỉnh ngưỡng nếu tỷ lệ từ chối cao, ghi lại mỗi lần chỉnh"],
    ["10", "Buổi nghiệm thu: điền bảng lấy mẫu 20 dòng trước mặt Marou, đọc page KPI so với baseline, đọc nhật ký bốn tuần. Báo cáo kết quả kể cả khi kết quả xấu"],
  ], [0.6, 5.0]),
  p("Bốn tuần chạy thật là phần không nén được. Có thể dựng xương sống nhanh hơn năm tuần nếu compile suôn sẻ, nhưng không có cách nào có bốn tuần số liệu trong hai tuần."),
  p("Nếu Marou không cho cài lên production: mọi thứ vẫn chạy trên sandbox chép từ production, nhưng kết quả kinh doanh ở tuần 10 chỉ là “nếu đã duyệt thì đã xử lý được bao nhiêu”, không phải “đã xử lý được bao nhiêu”. Phải nói rõ điều này trong đề xuất chứ không để tới buổi nghiệm thu."),
];

module.exports = { part2 };
