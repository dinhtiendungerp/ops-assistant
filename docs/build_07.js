// Tai lieu 07: phan tich use case, dieu kien, han che va lua chon kenh AI. Noi bo NaviWorld.
const { p, h1, h2, h3, bullet, num, table, pageBreak, build } = require("./lib");

const S = [];
const add = (...x) => S.push(...x);

// ------------------------------------------------------------------ 1
add(
  h1("1. Tóm tắt cho người quyết định"),
  p("Tài liệu này trả lời ba câu hỏi nội bộ trước khi viết bản đề xuất gửi Marou. Thứ nhất, các use case trong RFP cần những năng lực gì từ lớp AI, điều kiện gì phía Marou và giới hạn gì. Thứ hai, vì sao hai tuần qua NaviWorld dựng trợ lý trên web console tự build thay vì Copilot Studio. Thứ ba, nên đề xuất phương án nào và mở rộng về sau ra sao."),
  p("Kết luận ngắn: không phải chọn giữa Copilot Studio và tự build. Hệ thống có hai phần. Phần lõi gồm lớp tính AL trong Business Central, bảng đề xuất và bước người duyệt, policy, chặn số và MCP server của NaviWorld. Phương án nào cũng dùng chung phần này. Phần vỏ hội thoại mới là thứ phải chọn: web console, Copilot Studio trên Teams, Foundry, hay nút ngay trong BC."),
  p("Đề nghị: vỏ chính là Copilot Studio trên Teams nếu Marou có Microsoft 365 và chấp nhận license. Phần kiểm soát nằm ở BC và MCP server, không nằm trong prompt. Web console giữ làm màn hình quản trị, màn hình demo và đường dự phòng khi Marou chưa có Copilot Studio. Web console hiện tại là công cụ chứng minh ý tưởng, không phải kênh sản phẩm."),
  h2("Bốn điểm cần chốt"),
  num("Marou có Microsoft 365, Teams và license Copilot Studio hay không. Đây là điều kiện quyết định vỏ hội thoại.", "numbers"),
  num("Thử lại Copilot Studio với MCP server của NaviWorld trên cả hai harness trước khi viết đề xuất. Kết luận thử ngày 11/09/2026 có một phần đã lệch với tài liệu Microsoft ngày 13/09/2026 (mục 6).", "numbers"),
  num("Ai vận hành MCP server và trợ lý sau POC: NaviWorld theo hợp đồng dịch vụ, hay Marou tự vận hành trên Azure của Marou.", "numbers"),
  num("Có đưa Microsoft Fabric vào lộ trình không, ai trả capacity.", "numbers"),
);

// ------------------------------------------------------------------ 2
add(
  pageBreak(),
  h1("2. Trợ lý đang nối Business Central bằng gì"),
  p("Câu này hay bị nhầm vì trong dự án có hai thứ cùng tên MCP. Trợ lý hiện tại không dùng Business Central MCP Server. Nó đọc và ghi qua custom API page của app NWV Marou Agent, xác thực service-to-service (S2S) bằng Entra app. MCP server làm ngày 13/09/2026 là MCP của NaviWorld, bọc bộ công cụ của trợ lý, và bên dưới vẫn đi S2S."),
  table(["Đường nối", "Xác thực", "Dùng cho", "Trạng thái trong dự án"], [
    ["Custom API page v1.0 (publisher naviworld, group marouagent)", "S2S OAuth, client credentials, Entra app có permission set riêng", "Trợ lý đọc bảng kết quả, ghi đề xuất, chạy không người trực", "Đang chạy trên NWV01, đường chính"],
    ["Business Central MCP Server của Microsoft", "Chỉ OAuth authorization code kèm PKCE, mọi thao tác dưới danh tính người đăng nhập, không có client credentials", "Hỏi đáp trong Copilot Studio, VS Code dưới danh tính người dùng", "Đã thử với Copilot Studio ngày 10 và 11/09/2026 trên môi trường cũ, không dùng trong trợ lý"],
    ["MCP server của NaviWorld (POST /mcp)", "Khoá gắn với người dùng; gọi từ chính máy thì không cần khoá", "Cho agent bên ngoài (Copilot Studio, Foundry, VS Code) dùng chung bộ công cụ và policy của trợ lý", "Đã gọi thật bằng JSON-RPC, chưa nối với client thật"],
  ], [2.1, 2.1, 2.2, 1.8]),
  p("Vì sao không dùng Business Central MCP Server làm đường chính. BC MCP Server không có đường client credentials, nên mọi việc chạy không người trực như brief sáng, nhắc kho, tự làm theo policy đều không đi qua nó được. Ngoài ra, nếu agent gọi thẳng API của BC qua MCP thì mất ba lớp kiểm soát đang có: policy tự làm hay hỏi người, chặn số lượng vượt tồn, và việc mọi con số phải đến từ bảng AL đã tính."),
);

// ------------------------------------------------------------------ 3
add(
  pageBreak(),
  h1("3. Toàn bộ use case và loại bài toán"),
  p("RFP gốc ngày 20/08/2026 không nằm trong thư mục dự án. Bảng dưới dựng lại từ tài liệu 01 đến 06. Số hiệu UC3 và UC10 lấy theo tài liệu 03 và 04, phải đối chiếu lại với RFP trước khi dùng trong đề xuất."),
  table(["Use case", "Nội dung", "Loại bài toán", "Cần model", "Trạng thái 13/09/2026"], [
    ["UC2 Inventory Health & Traceability", "Phân tầng tồn theo lô, cận date, chậm luân chuyển, dư tồn; đề xuất xử lý", "Tính toán AL, cộng agent đề xuất và theo dõi", "Không cho số; có cho hội thoại", "AL chạy trên NWV01; trợ lý đọc thật. Phần Traceability và OneTrace ngoài phạm vi"],
    ["UC5 Store Replenishment", "Days of cover theo cửa hàng, đề xuất chuyển hàng, duyệt, theo dõi ship", "Tính toán AL, cộng agent", "Không cho số; có cho câu tự do", "AL chạy; luồng cửa hàng báo, điều phối duyệt, Transfer Order chạy thật"],
    ["UC7 Promotion & Discount Governance", "Phát hiện chiết khấu tay bất thường, hỏi giải trình, Retail Ops kết luận", "Rule AL, cộng agent thu thập giải trình", "Có, để đọc câu giải thích", "Rule AL đã viết; LS Adapter chưa build; trợ lý chạy trên log mô phỏng"],
    ["UC1 Demand Planning & Forecast", "Dự báo nhu cầu, độ chính xác", "Mô hình dự báo, không phải agent", "Không", "Chỉ có baseline WAPE trên dữ liệu mẫu; chưa chạy dữ liệu thật"],
    ["UC6 Retail Sales, Margin & Store Performance", "Doanh số, biên lợi nhuận theo cửa hàng", "BI", "Không, trừ phần tường thuật", "Chưa làm. Brief tuần cho lãnh đạo nằm ở giai đoạn 2 của tài liệu 03"],
    ["UC9 Service Category (MMV First)", "Chưa rõ", "Chưa rõ", "Chưa rõ", "Chưa thiết kế vì chưa biết MMV First là gì"],
    ["UC3 Supplier Watch (theo tài liệu 03)", "PO quá hạn nhận, lead time thực tế", "Tính toán, cộng nhắc việc", "Không", "Giai đoạn 3, chưa làm"],
    ["UC10 Yêu cầu mở (theo tài liệu 04)", "Câu nhiều ràng buộc: tiệc 150 khách, kho bị dột", "Agent tự lập chuỗi tra cứu", "Có, bắt buộc", "Planner chạy với model thật; kịch bản đã duyệt biến câu lặp lại thành 0 token"],
    ["POC C Loyalty Journey", "Tích điểm, Wallet Pass", "Cấu hình LS Central, tích hợp", "Không", "Chỉ nêu điều kiện, chưa nhận"],
    ["POC D Executive & AI Cockpit", "Dashboard liên phòng ban, hỏi đáp tự nhiên", "BI cộng hỏi đáp", "Có cho hỏi đáp", "Chỉ nêu điều kiện, chưa nhận"],
  ], [1.6, 1.9, 1.5, 1.1, 2.1]),
  p("Điểm quan trọng nhất của bảng: phần giá trị đo được của UC2 và UC5 nằm ở lớp AL, không cần model. Model chỉ bắt buộc ở ba chỗ: đọc câu tiếng Việt tự do, tự lập chuỗi tra cứu cho câu chưa gặp, và đọc câu giải thích của người. Vì vậy lựa chọn kênh AI không được làm chậm hay làm hỏng lớp AL."),
);

// ------------------------------------------------------------------ 4
add(
  pageBreak(),
  h1("4. Từng use case: cần gì, điều kiện gì, giới hạn gì"),
  h2("4.1 UC2 Inventory Health"),
  table(["Mục", "Nội dung"], [
    ["Lớp AI cần làm", "Brief sáng theo vai trò; thẻ đề xuất (giảm giá, huỷ, chặn mua, chuyển sang cửa hàng bán nhanh); người duyệt nhận thẻ ngay; theo dõi tới khi lô được xử lý; trả lời \"lô này ở đâu\", \"tồn xấu bao nhiêu tiền\""],
    ["Điều kiện phía Marou", "Tỷ lệ Item Ledger Entry có Lot No. và Expiration Date đủ cao; Item Tracking Code gán đúng trước khi có phát sinh; Item Category phân nhóm đúng; ít nhất 90 ngày lịch sử bán; người duyệt chỉ định rõ"],
    ["Giới hạn đã biết", "Không gán được Item Tracking Code cho item đã có phát sinh (TestNoEntriesExist). Lô vá vào sau khi post làm phân bổ theo lô mâu thuẫn, phải post lại. Ghép lô cận date với cửa hàng bán nhanh hiện là rule, chưa phải agent. Đo lại sau 14 ngày mới đặt cho chuyến trợ lý tự làm"],
    ["Năng lực kênh bắt buộc", "Thẻ duyệt, đẩy việc chủ động, hỏi đáp số, vết kiểm toán"],
  ], [1.6, 6.4]),
  h2("4.2 UC5 Store Replenishment"),
  table(["Mục", "Nội dung"], [
    ["Lớp AI cần làm", "Cửa hàng nhắn bằng lời; trợ lý tra mặt hàng, tính số từ bảng AL; điều phối duyệt hoặc sửa số trong chat; policy cho tự làm trong hạn mức; nhắc kho khi chưa ship, leo thang sau lần hai; bậc thang chẩn đoán khi một cặp cửa hàng và mặt hàng hết lặp lại"],
    ["Điều kiện phía Marou", "Transfer Route và In-Transit đã setup; Statement của LS POS post hằng ngày (nếu post theo tuần thì tốc độ bán bảy ngày gần nhất bằng 0); xác nhận có dùng LS Central Replenishment không; chỉ định người điều phối"],
    ["Giới hạn đã biết", "Duyệt hiện chạy bằng token của ứng dụng, chưa dùng danh tính người bấm (on-behalf-of chưa làm). Nút Đã ship chỉ ghi trong trợ lý, chưa đọc trạng thái Transfer Order thật"],
    ["Năng lực kênh bắt buộc", "Thẻ duyệt có ô sửa số, đẩy việc chủ động, theo dõi và nhắc, trả lời đúng tin, policy và hoàn tác"],
  ], [1.6, 6.4]),
  h2("4.3 UC7 Discount Governance"),
  table(["Mục", "Nội dung"], [
    ["Lớp AI cần làm", "Hỏi quản lý cửa hàng lý do chiết khấu; nhận câu trả lời tự do, gắn đúng exception; chuyển cho Retail Ops kết luận; trợ lý không được kết luận"],
    ["Điều kiện phía Marou", "Log POS có Staff ID và loại chiết khấu; Staff Permission Group trên POS đã cấu hình (chưa có thì cấu hình trước, agent sau); đồng ý có gửi Staff ID ra ngoài BC hay phải ẩn"],
    ["Giới hạn đã biết", "LS Adapter chưa build, tên field LS Central chưa đối chiếu symbol đúng version. Trợ lý đang chạy trên log mô phỏng"],
    ["Năng lực kênh bắt buộc", "Hỏi và chờ câu trả lời, trả lời đúng tin khi có tin chen ngang, đọc câu tự do"],
  ], [1.6, 6.4]),
  pageBreak(),
  h2("4.4 UC1, UC6 và yêu cầu mở"),
  table(["Use case", "Lớp AI cần làm", "Điều kiện", "Giới hạn"], [
    ["UC1", "Dùng forecast để ước ngày hết hàng; báo độ chính xác hằng tháng", "Tối thiểu 12 tháng lịch sử để bắt mùa Tết", "Không hứa mô hình AI trong POC; kết quả thật cần vài tháng"],
    ["UC6", "Tường thuật ngắn theo cửa hàng, nối với việc đã xử lý", "Value Entry đủ để tính margin; ai xem dashboard", "Là BI; nếu Power BI thì mỗi người xem cần license Pro"],
    ["Yêu cầu mở", "Đọc ràng buộc trong câu, tự chọn đọc gì, đổi kế hoạch khi ràng buộc đổi, hỏi lại đúng một câu", "Model và ngân sách token; bộ công cụ đủ dữ liệu", "Model đã suy luận sai ba lần khi thử; phải có người duyệt và số phải lấy từ công cụ"],
  ], [1.0, 2.6, 2.2, 2.2]),
);

// ------------------------------------------------------------------ 5
add(
  pageBreak(),
  h1("5. Năng lực kênh AI mà các use case đòi hỏi"),
  p("Gom từ mục 4, bỏ những thứ lớp AL đã làm. Cột cuối cho biết thiếu năng lực đó thì use case nào hỏng."),
  table(["Mã", "Năng lực", "Thiếu thì sao"], [
    ["N1", "Hỏi đáp số bằng tiếng Việt, số lấy từ bảng AL", "Mất lý do dùng trợ lý thay vì mở BC"],
    ["N2", "Thẻ duyệt có nút và ô sửa số, lý do từ chối", "UC2, UC5 phải quay về duyệt trong BC"],
    ["N3", "Chủ động đẩy việc: brief sáng, thẻ tới người duyệt khi cửa hàng báo", "Người duyệt phải tự đi tìm; tài liệu 03 coi đây là giá trị chính"],
    ["N4", "Theo dõi và nhắc, leo thang", "UC5 mất vòng khép kín tới khi hàng về"],
    ["N5", "Hỏi và chờ câu trả lời, gắn đúng câu hỏi khi có tin chen ngang", "UC7 không thu được giải trình"],
    ["N6", "Yêu cầu mở nhiều bước, hỏi lại khi thiếu", "Mất phần duy nhất bắt buộc phải có model"],
    ["N7", "Policy tự làm hay hỏi người, shadow mode, trần lượt, hoàn tác", "Trợ lý chỉ là form đẹp hơn"],
    ["N8", "Chặn số vượt tồn và mọi con số phải truy về dữ liệu, cưỡng chế trong code", "Rủi ro sai số tiền và mất niềm tin khi nghiệm thu"],
    ["N9", "Vết kiểm toán: dòng policy nào cho phép, ai duyệt, chuỗi tra cứu nào", "Không trả lời được kiểm toán"],
    ["N10", "Đo token thật và trần chi phí cứng", "Không kiểm soát được tiền, Azure budget chỉ cảnh báo"],
    ["N11", "Chạy được khi tắt AI", "POC phụ thuộc hoàn toàn vào model"],
    ["N12", "Duyệt dưới danh tính người bấm", "Vết kiểm toán trong BC ghi sai người"],
    ["N13", "Kênh Zalo", "Chỉ quan trọng nếu cửa hàng Marou không dùng Teams"],
  ], [0.6, 3.8, 3.6]),
);

// ------------------------------------------------------------------ 6
add(
  pageBreak(),
  h1("6. Các phương án đáp ứng năng lực tới đâu"),
  p("B là Copilot Studio, C là trợ lý NaviWorld tự build (web console cộng MCP server), D là Copilot capability trong BC, F là Foundry Agent Service. Nguồn: tài liệu Microsoft tra ngày 13/09/2026 (Phụ lục A) và các lần thử thật trong dự án (Phụ lục B). Chữ \"dựng\" nghĩa là có cơ chế nhưng NaviWorld phải tự cấu hình hoặc viết."),
  table(["Mã", "B Copilot Studio", "C Tự build", "D Trong BC", "F Foundry"], [
    ["N1", "Có. Nối MCP server của NaviWorld qua Streamable, API key hoặc OAuth", "Có, đang chạy", "Chỉ trên dòng đang mở, không có chat", "Có. Nối MCP, key hoặc Entra hoặc OAuth passthrough"],
    ["N2", "Dựng bằng node Adaptive Card có ô nhập; Teams giới hạn schema 1.5", "Có, đang chạy", "PromptDialog trong BC", "Tài liệu chỉ thấy thẻ duyệt lời gọi tool MCP; thẻ tuỳ biến chưa kiểm"],
    ["N3", "Dựng bằng Power Automate; chỉ chat 1:1, người nhận phải cài agent, tin không vào transcript", "Có trên web console; lên Teams phải tự làm bot", "Không", "Chưa thấy tài liệu cho tin chủ động"],
    ["N4", "Dựng bằng Power Automate", "Có", "Không", "Phải tự làm"],
    ["N5", "Dựng bằng topic hoặc Adaptive Card chờ trả lời", "Có, kể cả trả lời đúng tin", "Không", "Chưa kiểm"],
    ["N6", "Có (generative orchestration)", "Có", "Hạn chế", "Có"],
    ["N7", "Không nên đặt trong Instructions; phải nằm trong MCP server hoặc BC", "Có, trong code", "Trong AL", "Phải nằm trong MCP server"],
    ["N8", "Như N7. Thử 11/09: viết luật vào Instructions không chặn được", "Có, trong code", "Trong AL", "Như N7"],
    ["N9", "Có transcript; policy log nằm ở MCP server", "Có", "Có trong BC", "Có tracing; policy log ở MCP server"],
    ["N10", "Trần theo agent trong Power Platform admin center, tính bằng Copilot Credits", "Có, trần cứng theo ngày", "Theo Azure OpenAI của khách", "Không có trần cứng; Azure budget chỉ cảnh báo"],
    ["N11", "Không, kênh là AI", "Có", "Có, lớp AL", "Không"],
    ["N12", "Có nếu tool đặt xác thực người dùng cuối", "Chưa làm (cần on-behalf-of)", "Có, người đang mở page", "Có với OAuth passthrough, cùng tenant"],
    ["N13", "Không có sẵn", "Làm được", "Không", "Không có sẵn"],
  ], [0.6, 2.2, 1.6, 1.4, 2.2]),
  h2("Kết quả thử thật ngày 10 và 11/09/2026, và chỗ đã lệch"),
  bullet("Copilot Studio harness Standard cộng BC MCP Server ở Static Tool Mode trả dữ liệu BC thật trong một lượt, khoảng 30 giây."),
  bullet("Dynamic Tool Mode gây ConnectorTimeoutError sau 120 giây và vòng lặp hỏi lại tham số. Ghi \"không hỏi lại tham số\" vào Instructions không chặn được vì đó là slot filling của nền tảng."),
  bullet("Harness GitHub Copilot khi thử không nạp được tool của connector hay MCP. Nhưng tài liệu Microsoft ngày 13/09/2026 ghi agent chạy harness này thêm được tool MCP và Fabric data agent. Kết luận cũ có thể đã lỗi thời, phải thử lại trước khi dùng làm lý do."),
  bullet("Agent flow của Copilot Studio có giới hạn 100 giây cho mỗi action; tool MCP trong Foundry cũng ngắt sau 100 giây. Brief của điều phối trên BC thật lần đầu mất khoảng 44 giây, vẫn trong giới hạn nhưng không dư nhiều."),
);

// ------------------------------------------------------------------ 7
add(
  pageBreak(),
  h1("7. Vì sao hai tuần qua làm trên web console"),
  h2("7.1 Diễn biến quyết định"),
  table(["Ngày", "Quyết định hoặc sự kiện", "Tài liệu"], [
    ["07/09", "Bản 0.1: ba agent chạy đêm ghi vào bảng đề xuất, người duyệt trong BC", "01, 02"],
    ["07/09", "Bản 0.2: một trợ lý đa kênh (Teams, Zalo, web console) có duyệt trong chat và theo dõi", "03"],
    ["08/09", "Bản 0.5: thêm policy tự làm, nhánh planner cho yêu cầu mở, baseline trong sản phẩm", "04"],
    ["10/09", "Kế hoạch UC2: đề nghị cửa B nếu Marou có Microsoft 365, D nếu không, C chỉ khi cần Zalo", "06"],
    ["10 và 11/09", "Thử Copilot Studio với BC MCP Server: Standard cộng Static chạy được; Dynamic timeout; Instructions không cưỡng chế được; harness GitHub Copilot không nạp tool", "Lịch sử chat"],
    ["11/09", "Dũng quyết không mất thêm thời gian chứng minh nền tảng Microsoft làm được hay không; chọn cửa tự build để chủ động", "Lịch sử chat"],
    ["12/09", "Chốt kiến trúc bốn lớp, lớp tính chạy bằng AL trong BC; cửa vào AI là cửa C; model Azure OpenAI gpt-4.1-mini", "CLAUDE.md"],
    ["13/09", "Chạy trên BC thật; thêm định tuyến tiết kiệm token, kịch bản đã duyệt, MCP server", "CLAUDE.md"],
  ], [1.0, 5.8, 1.2]),
  h2("7.2 Lý do, và lý do nào còn đứng"),
  table(["Lý do chọn web console", "Còn đúng không"], [
    ["Cần chứng minh nhanh toàn bộ luồng (N2 đến N11) trong một buổi demo mà không phụ thuộc license, tenant và cấu hình phía Marou", "Còn đúng cho POC và demo"],
    ["Copilot Studio không cưỡng chế được policy và số bằng Instructions", "Còn đúng. Nhưng cách sửa là đặt policy ở MCP server, không phải bỏ Copilot Studio"],
    ["Harness GitHub Copilot không nạp tool MCP", "Có thể đã lỗi thời, tài liệu 13/09 nói ngược lại. Phải thử lại"],
    ["BC MCP Server chỉ xác thực người dùng, không chạy không người trực", "Còn đúng. Nhưng MCP server của NaviWorld đi S2S nên không vướng"],
    ["Chưa xác nhận Marou có Microsoft 365 và Teams", "Còn đúng, là câu hỏi cho buổi clarification"],
    ["Kiểm soát được token, trần chi phí, tắt AI mà hệ thống vẫn chạy", "Còn đúng; Copilot Studio có trần theo agent nhưng tính bằng Copilot Credits"],
    ["Có thể cần Zalo", "Chưa xác nhận"],
  ], [4.6, 3.4]),
  p("Điều cần nói thẳng khi trình bày: web console không phải kênh sản phẩm. Nó chưa có đăng nhập (người dùng tự chọn vai trò), chưa có ứng dụng điện thoại, chưa duyệt dưới danh tính người bấm. Phần mang sang được sản phẩm là lõi: bộ công cụ, policy, định tuyến, kịch bản đã duyệt, trần chi phí, và MCP server bọc chúng."),
);

// ------------------------------------------------------------------ 8
add(
  pageBreak(),
  h1("8. Chi phí, vận hành và ai host"),
  table(["Khoản", "B Copilot Studio", "C Tự build", "F Foundry"], [
    ["Chi phí AI", "Copilot Credits: câu trả lời tạo sinh 2, agent action 5, agent flow 13 trên 100 action; gói 25.000 credit mỗi tháng hoặc trả theo mức dùng (tra ngày 10/09). Tài liệu 06 ước 13.000 đến 19.000 credit mỗi tháng cho 5 người, chưa kiểm giả định", "Token Azure OpenAI đo thật: một câu hỏi mở 6.100 đến 6.600 token gửi đi, 0,001 đến 0,002 USD. Câu rule đọc được và câu chạy kịch bản 0 token", "Chỉ trả token model; hosted agent tính thêm CPU và RAM theo phiên"],
    ["License phía Marou", "Microsoft 365, Teams, Copilot Studio hoặc trả theo mức dùng, Power Platform environment", "Không cần license Microsoft thêm; cần Entra app và Azure subscription", "Azure subscription; người dùng cần vai trò Foundry Agent Consumer nếu OAuth passthrough"],
    ["Hạ tầng", "Microsoft vận hành kênh; MCP server của NaviWorld vẫn phải host", "Container cho trợ lý và MCP server, Key Vault, lưu trữ. Chưa tính giá, cần Azure Pricing Calculator", "Microsoft vận hành agent; MCP server vẫn phải host"],
    ["Effort NaviWorld (tài liệu 06)", "5 đến 8 ngày", "9 đến 14 ngày cộng vận hành", "Chưa ước"],
    ["Ai vận hành lâu dài", "Marou tự vận hành được phần agent; MCP server cần người", "NaviWorld, tính phí vận hành tháng", "Như B"],
  ], [1.4, 2.4, 2.4, 1.8]),
  p("Khách có tự host được phần tự build không: về kỹ thuật được, đặt trên Azure và tenant của Marou. Rủi ro là Marou cần người vận hành một dịch vụ Python: xoay secret, theo dõi lỗi, cập nhật khi model bị ngừng. Nếu vỏ là Copilot Studio thì phần phải tự host chỉ còn MCP server, nhỏ và không có giao diện."),
  p("Số chi phí token lấy từ sổ chi phí của trợ lý sau khi sửa lỗi đếm đôi phần cache ngày 13/09/2026, và khớp bậc độ lớn với Foundry Monitor cùng ngày: 54 lượt gọi, 109,81 nghìn token, ước tính 0,03 bảng Anh cho toàn bộ từ trước tới giờ. Không lấy số tiền của tenant demo này để hứa với Marou."),
);

// ------------------------------------------------------------------ 9
add(
  h1("9. Rủi ro"),
  table(["Rủi ro", "Ảnh hưởng", "Cách xử lý"], [
    ["Dữ liệu lô và hạn dùng của Marou thật phủ thấp", "Tầng cận date và hết hạn rỗng, mất phần giá trị nhất của UC2", "Đo độ phủ tuần 1, cam kết theo kết quả"],
    ["Marou không có Microsoft 365 hoặc license Copilot Studio", "Không dùng được vỏ B", "Dùng C hoặc D; lõi không đổi"],
    ["Tool MCP phía Copilot Studio và Fabric data agent còn preview", "Marou IT từ chối", "Nói trước; không đặt tiêu chí nghiệm thu lên phần preview"],
    ["Dữ liệu ra ngoài Việt Nam", "Azure OpenAI đang ở eastus; Fabric data agent qua Copilot Studio có thể ra ngoài vùng Fabric", "Data Zone Standard; ghi rõ ở phần governance"],
    ["Model suy luận sai", "Kết luận ngược với số", "Người duyệt; số chỉ lấy từ công cụ; kịch bản đã duyệt báo số model tự tính"],
    ["Vượt hạn mức token mỗi phút", "Câu hỏi mở không trả lời được", "Nâng TPM deployment; trợ lý đã chờ và thử lại, báo rõ trong chat"],
    ["Duyệt chưa dưới danh tính người bấm", "Vết kiểm toán BC ghi tên ứng dụng", "On-behalf-of qua Teams SSO, hoặc duyệt trên page BC"],
    ["NaviWorld ôm vận hành dài hạn nếu chọn C", "Chi phí người không nằm trong giá", "Phí vận hành tháng trong commercial model, hoặc chuyển vỏ sang B"],
  ], [2.4, 2.8, 2.8]),
);

// ------------------------------------------------------------------ 10
add(
  pageBreak(),
  h1("10. Knowledge còn thiếu cho AI"),
  p("Hiện AI chỉ biết số trong BC và các dòng policy. Chia làm hai loại: thứ làm đổi con số phải nằm trong BC để kiểm toán được; thứ chỉ là bối cảnh thì để trong tài liệu."),
  table(["Thiếu", "Ví dụ", "Nên nằm ở đâu"], [
    ["Quy trình vận hành", "Xử lý hàng hết hạn, quy định chiết khấu, SOP kho", "SharePoint, dùng làm knowledge cho Copilot Studio hoặc Foundry IQ"],
    ["Thông số nghiệp vụ", "Hạn dùng theo nhóm hàng, sức chứa tủ đông, lead time và MOQ nhà cung cấp", "Bảng setup trong BC (NWV Agent Setup, Category Threshold, Item Vendor)"],
    ["Sự kiện làm lệch nhu cầu", "Khuyến mãi, tiệc, Tết, tủ đông hỏng", "NWV Demand Exception trong BC"],
    ["Cách từng người làm việc", "Cách gõ tắt tên món, cửa hàng hay báo tiệc trước mấy ngày", "Memory của agent (đang preview), không dùng cho con số"],
    ["Dữ liệu ngoài BC", "Doanh số lịch sử dài, dữ liệu marketing", "Fabric, qua Fabric data agent làm tool"],
  ], [1.8, 3.2, 3.0]),
);

// ------------------------------------------------------------------ 11
add(
  h1("11. Đề nghị và lộ trình mở rộng"),
  table(["Giai đoạn", "Làm gì", "Ghi chú"], [
    ["POC", "AL trong BC; đề xuất và người duyệt; web console để demo và quản trị; MCP server; Azure OpenAI", "Chạy được khi tắt AI; đo token thật"],
    ["Pilot", "Copilot Studio trên Teams gọi MCP server; thẻ duyệt bằng Adaptive Card; brief và nhắc bằng Power Automate; SharePoint làm knowledge; đo Copilot Credits hai tuần", "Lõi không đổi; thử lại harness trước"],
    ["Mở rộng dữ liệu", "Đưa BC vào OneLake; Fabric data agent làm tool cho UC6 và lịch sử cho UC1", "Preview, cần capacity F2 trở lên, dữ liệu có thể ra ngoài vùng Fabric"],
    ["Theo dõi", "Agent trong BC (Agent SDK, Agent Designer), Memory của Foundry", "Đều preview; không cam kết"],
  ], [1.3, 4.3, 2.4]),
  h2("Khi Marou hỏi \"sao không dùng Copilot Studio\""),
  p("Có dùng, cho phần hội thoại trên Teams. Phần tính số nằm trong Business Central bằng AL, phần kiểm soát nằm trong MCP server mà Copilot Studio gọi. Lý do không đặt luật nghiệp vụ trong Copilot Studio là NaviWorld đã thử: viết luật vào Instructions không chặn được hành vi của nền tảng. Luật phải nằm trong code để kiểm toán viên đọc được và để hệ thống vẫn chạy khi tắt AI."),
  h2("Việc tiếp theo để chốt"),
  num("Hỏi Marou: Microsoft 365, Teams, Copilot Studio, Zalo, ai vận hành sau POC.", "numbers2"),
  num("Đưa MCP server lên một địa chỉ công khai có khoá; thử với Copilot Studio trên cả hai harness, ghi lại kết quả thật.", "numbers2"),
  num("Dựng một thẻ duyệt Adaptive Card và một tin chủ động Power Automate trên tenant demo để kiểm N2, N3.", "numbers2"),
  num("Tính giá hạ tầng bằng Azure Pricing Calculator cho cả C và B.", "numbers2"),
  num("Đối chiếu bảng use case mục 3 với RFP gốc.", "numbers2"),
);

// ------------------------------------------------------------------ phu luc
add(
  h1("Phụ lục A. Tài liệu Microsoft đã tra ngày 13/09/2026"),
  table(["Nội dung", "Nguồn"], [
    ["Copilot Studio nối MCP server có sẵn: chỉ Streamable, API key hoặc OAuth 2.0, cần generative orchestration, chịu data policy của Power Platform", "learn.microsoft.com/microsoft-copilot-studio/mcp-add-existing-server-to-agent"],
    ["Harness GitHub Copilot thêm được tool MCP", "learn.microsoft.com/microsoft-copilot-studio/agents-experience/add-tools-custom-agent"],
    ["Adaptive Card: Teams giới hạn schema 1.5; node Adaptive Card có ô nhập", "learn.microsoft.com/microsoft-copilot-studio/adaptive-cards-overview; authoring-ask-with-adaptive-card"],
    ["Tin chủ động qua Power Automate: chỉ chat 1:1, phải cài agent, không vào transcript", "learn.microsoft.com/microsoft-copilot-studio/advanced-proactive-message"],
    ["Fabric data agent trong Copilot Studio: preview, F2 trở lên, cùng tenant, dữ liệu có thể ra ngoài vùng Fabric", "learn.microsoft.com/fabric/data-science/data-agent-microsoft-copilot-studio"],
    ["Foundry: xác thực MCP (key, Entra, OAuth passthrough cùng tenant); tool MCP ngắt sau 100 giây", "learn.microsoft.com/azure/foundry/agents/how-to/mcp-authentication; tools/model-context-protocol"],
    ["Foundry: publish lên Teams và Microsoft 365 Copilot", "learn.microsoft.com/azure/foundry/agents/how-to/publish-copilot"],
    ["Foundry Agent Service chỉ tính phí inference; hosted agent tính CPU và RAM", "learn.microsoft.com/azure/foundry/agents/faq; concepts/hosted-agents"],
    ["Memory preview, danh sách vùng không có Southeast Asia", "learn.microsoft.com/azure/foundry/agents/concepts/what-is-memory"],
    ["Prompt caching gpt-4.1-mini, cached_tokens trong prompt_tokens_details", "learn.microsoft.com/azure/ai-foundry/openai/how-to/prompt-caching"],
    ["Business Central MCP Server: mặc định chỉ đọc, cấu hình theo API page", "learn.microsoft.com/dynamics365/business-central/dev-itpro/ai/configure-mcp-server"],
  ], [4.6, 3.4]),
  h1("Phụ lục B. Bằng chứng thử thật trong dự án"),
  table(["Việc", "Kết quả", "Ngày"], [
    ["Copilot Studio Standard cộng BC MCP Static", "Trả dữ liệu thật trong một lượt, khoảng 30 giây", "11/09"],
    ["Copilot Studio Dynamic Tool Mode", "ConnectorTimeoutError sau 120 giây; vòng lặp hỏi lại tham số", "10/09"],
    ["Harness GitHub Copilot", "Không nạp tool connector hay MCP khi chạy", "11/09"],
    ["Trợ lý đọc BC thật qua S2S", "Bấm chuyển sang BC 24 giây; brief điều phối lần đầu 44 giây, lần sau 0,1 giây", "13/09"],
    ["Planner với Azure OpenAI", "Câu hỏi mở 3 bước tra cứu, khoảng 6 nghìn token gửi đi; câu tương tự chạy kịch bản 0 token", "13/09"],
    ["Model suy luận sai", "Kết luận ngược phép tính; đếm sai số đề xuất; nói \"bán chậm\" với cửa hàng bán nhiều hơn", "12 và 13/09"],
    ["MCP server của NaviWorld", "initialize, tools/list, tools/call chạy trên server demo; 8 test", "13/09"],
  ], [2.4, 4.4, 1.2]),
);

build(
  "Marou Ops Assistant: use case, điều kiện và lựa chọn kênh AI",
  "Vì sao dựng trên web console, Copilot Studio đáp ứng tới đâu, và hướng mở rộng.",
  {
    header: "NaviWorld Vietnam | Marou POC | Lựa chọn kênh AI",
    footer: "Bản 1.0, 13/09/2026",
    cover: [
      "Soạn: Đinh Tiến Dũng, Principal Consultant",
      "Ngày: 13/09/2026",
      "Người đọc: nội bộ NaviWorld, trước khi viết đề xuất gửi Marou",
      "Tính năng Microsoft tra ngày 13/09/2026, nguồn ở Phụ lục A. Tra lại trước khi ký",
      "Con số chi phí là số đo trên tenant demo hoặc ước tính nội bộ, chưa phải báo giá",
    ],
  },
  S,
  __dirname + "/07 Marou Ops Assistant - Use case va lua chon kenh AI (noi bo).docx",
);
