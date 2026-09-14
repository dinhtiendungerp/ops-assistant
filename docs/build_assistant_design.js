const { p, h1, h2, h3, bullet, num, table, pageBreak, build, img } = require("./lib");

// Anh doc: 1484x984 -> width 600pt ~ 6.25in; giu ti le
const children = [
  h1("1. Tóm tắt"),
  p("Đề xuất một trợ lý vận hành chuỗi cửa hàng, gọi tạm là Marou Ops Assistant, chạy ngoài Business Central, nói chuyện với người của Marou qua Teams hoặc Zalo, email và một web console nhỏ. Nó đọc dữ liệu từ Business Central và LS Central, tự phát hiện việc cần làm, đề xuất, xin duyệt ngay trong chat, ghi kết quả về Business Central dưới tên người duyệt, rồi theo dõi đến khi việc xong."),
  p("Khác với bản thiết kế 0.1 (ba agent chạy đêm, ghi vào một bảng để người mở BC duyệt), bản này đặt agent vào đúng chỗ người đang phải đứng: giữa cửa hàng, kho, điều phối và kế toán, nơi hiện tại việc chạy bằng chat và Excel. Lớp logic AL của bản 0.1 giữ nguyên, nó trở thành nguồn số cho trợ lý. Cái đổi là kênh, vòng theo dõi, và việc trợ lý tự thu thập thông tin từ người (giải trình discount, xác nhận hàng hỏng) thay vì chỉ đọc bảng."),
  p("Giả định để viết tài liệu này, chưa xác nhận với Marou: Marou có Microsoft 365 và dùng Teams cho vận hành; nếu thực tế là Zalo thì kênh đổi, phần còn lại không đổi, riêng danh tính người duyệt phải xử lý khác (mục 4.4)."),

  h1("2. Ai dùng, dùng ở đâu"),
  table(["Vai trò", "Việc hằng ngày với trợ lý", "Kênh"], [
    ["Quản lý cửa hàng (4 đến 10 người)", "Báo sắp hết hàng, hàng hỏng, khách trả; nhận xác nhận đơn chuyển và ngày về; trả lời câu hỏi giải trình discount của nhân viên mình", "Teams hoặc Zalo trên điện thoại"],
    ["Điều phối kho và cung ứng (1 đến 2 người)", "Nhận đề xuất chuyển hàng, duyệt hoặc sửa số trong chat; nhận nhắc khi kho chưa ship; brief buổi sáng", "Teams, email"],
    ["Supply Chain / Planning", "Brief cận date, chậm luân chuyển, dư tồn; duyệt markdown, block purchase; xem forecast theo store", "Teams, web console"],
    ["Retail Ops / kiểm soát", "Nhận exception discount đã có giải trình; kết luận; xem xu hướng theo store và nhân viên", "Teams, web console"],
    ["Ban lãnh đạo", "Brief tuần theo store: doanh số, margin, việc đã xử lý, việc còn treo. Hỏi câu tự do trên số đã tính", "Email, Teams"],
    ["NaviWorld (vận hành POC)", "Đổi ngưỡng, xem log, đo chi phí, tắt bật skill", "Web console"],
  ], [1.6, 3.2, 1.2]),

  h1("3. Chức năng"),
  h2("3.1 Tương tác"),
  table(["Chức năng", "Mô tả", "Giai đoạn"], [
    ["Brief buổi sáng theo vai trò", "07:30 mỗi ngày, mỗi vai trò nhận một tin: điều phối thấy store nào dưới ngưỡng và đề xuất chuyển; Supply Chain thấy lot cận date và hàng chậm; Retail Ops thấy exception discount. Mỗi dòng có nút xử lý. Không ai phải mở BC để biết hôm nay có gì.", "1"],
    ["Yêu cầu bằng ngôn ngữ tự nhiên từ cửa hàng", "Quản lý cửa hàng nhắn \"sắp hết Mini bar\", \"khách trả 3 hộp bonbon hỏng\", gửi ảnh phiếu. Trợ lý hiểu item, số lượng, cửa hàng từ ngữ cảnh (người nhắn thuộc store nào), đối chiếu với BC rồi phản hồi trong một phút.", "1"],
    ["Duyệt trong chat", "Thẻ đề xuất có ba nút: Duyệt, Sửa số, Từ chối kèm lý do. Duyệt chạy dưới danh tính người bấm. Sửa số bị chặn theo tồn khả dụng.", "1"],
    ["Theo dõi và nhắc", "Sau khi duyệt, trợ lý tự kiểm tra tiến độ (Transfer đã ship, đã nhận chưa; exception đã đóng chưa; đề xuất treo quá 24 giờ) và nhắc đúng người, leo thang sau lần nhắc thứ hai.", "1"],
    ["Hỏi đáp có kiểm soát", "Câu hỏi trên số đã tính: \"Đà Nẵng còn bao nhiêu Ba Ria 76\", \"tuần này store nào bán chậm bonbon\", \"lot L260817 đang ở đâu\". Danh sách câu hỏi được duyệt trước cho giai đoạn 1; câu tự do qua BC MCP Server ở giai đoạn 2.", "1 và 2"],
    ["Thu thập giải trình", "Với exception discount, trợ lý hỏi quản lý cửa hàng lý do, ghi câu trả lời vào exception, rồi mới đưa cho Retail Ops kết luận. Đây là việc hiện nay tốn nhiều thời gian nhất của người kiểm soát.", "1"],
    ["Brief tuần cho lãnh đạo", "Mỗi thứ Hai: doanh số, margin theo store so với tuần trước và cùng kỳ, việc trợ lý đã xử lý (số đề xuất, tỷ lệ duyệt, thời gian xử lý), việc còn treo. Viết bằng tiếng Việt và tiếng Anh.", "2"],
  ], [1.5, 3.9, 0.6]),

  h2("3.2 Năng lực nghiệp vụ (skill)"),
  p("Mỗi skill là một cặp: lớp logic trong Business Central tính số, và một bộ tool cho trợ lý đọc số, đề xuất, hành động trong giới hạn. Số không bao giờ do mô hình ngôn ngữ tính."),
  table(["Skill", "Use case RFP", "Lớp logic trong BC (AL)", "Trợ lý làm gì thêm", "Hành động về BC"], [
    ["Replenishment", "UC5", "Days of cover theo store, target, constrained qty theo kho trung tâm và MOQ (codeunit NWV Replenishment Calc, hoặc LS Replenishment Journal nếu Marou đang dùng)", "Gộp nhiều store cùng chuyến, đề xuất chuyển ngang store sang store khi kho hết, giải thích số, xin duyệt, theo dõi ship", "Tạo Transfer Order (Open) khi duyệt; phase 2: tự duyệt trong policy"],
    ["Inventory Health", "UC2", "Tier và risk score theo item, location, lot (NWV Inv. Health Calc)", "Ghép lot cận date với store bán nhanh để đề xuất chuyển thay vì giảm giá; hỏi cửa hàng xác nhận hàng hỏng; theo dõi đến khi lot được xử lý", "Đề xuất Markdown, Transfer, Write-off; phase 2: Item Journal Line chưa post cho write-off"],
    ["Discount Governance", "UC7", "Ba rule DG-01 đến DG-03 trên NWV POS Discount Log nạp từ Trans. Sales Entry (NWV Discount Gov. Calc)", "Đọc bối cảnh, hỏi giải trình từ quản lý cửa hàng, ghi lại, xếp ưu tiên cho Retail Ops kết luận", "Đổi trạng thái exception, ghi giải trình; không kết luận"],
    ["Store Brief", "UC6", "Số bán, margin, tồn theo store từ Item Ledger Entry và Value Entry; so với tuần trước và forecast", "Viết tường thuật ngắn, chỉ ra bất thường, nối với việc đã xử lý", "Không ghi BC"],
    ["Demand Signal", "UC1", "Sales and Inventory Forecast của BC (Azure AI) ở cấp công ty; module tách xuống store theo tỷ trọng bán 8 tuần", "Dùng forecast để ước ngày hết hàng và số cần chuyển; báo độ chính xác hằng tháng", "Không ghi BC; số vào Replenishment"],
    ["Supplier Watch (phase 3)", "UC3", "Purchase Line có Expected Receipt Date đã qua mà chưa nhận; lead time thực tế so với Item Vendor", "Nhắc mua hàng, đề xuất mail hỏi nhà cung cấp", "Đề xuất; không sửa PO"],
  ], [1.1, 0.6, 1.9, 1.8, 1.4]),

  h2("3.3 Hành động về Business Central: bốn mức"),
  table(["Mức", "Trợ lý được làm gì", "Cơ chế", "POC"], [
    ["0. Đọc", "Đọc số đã tính, dữ liệu thô, chứng từ", "Custom API, API v2.0, OData, MCP", "Có"],
    ["1. Ghi đề xuất", "Ghi vào NWV Agent Proposal, ghi giải trình vào exception", "Custom API, tài khoản ứng dụng", "Có"],
    ["2. Tạo chứng từ mở", "Transfer Order trạng thái Open; phase 2 Item Journal Line chưa post", "Bound action approve trên API page, chạy dưới token của người duyệt", "Có, khi người duyệt"],
    ["3. Chạy nghiệp vụ có kiểm soát", "Release Transfer, gán lot, đổi trạng thái", "Bound action hoặc MCP tool có Allow Bound Actions", "Phase 2, sau khi có policy"],
    ["4. Post", "Ship, receive, post journal", "Không giao cho trợ lý", "Không"],
  ], [1.1, 2.2, 2, 0.7]),

  h2("3.4 Quản trị và vận hành"),
  bullet("Ngưỡng và rule nằm trong Business Central (NWV Agent Setup và codeunit), không nằm trong prompt. Kiểm toán viên đọc được."),
  bullet("Policy guard trong trợ lý: danh sách tool được phép theo skill; số lượng chuyển không vượt constrained qty; tối đa N đề xuất mỗi lần chạy; ẩn Staff ID và số thẻ member trước khi gửi mô hình nếu Marou yêu cầu."),
  bullet("Mỗi đề xuất và mỗi tin trợ lý gửi có run id, model, evidence, kênh, người nhận. Mỗi tool call có log. Đủ để trả lời câu \"vì sao hôm đó nó nói thế\"."),
  bullet("Feedback loop: lý do từ chối và số bị sửa được ghi lại; mỗi hai tuần NaviWorld đọc và chỉnh ngưỡng hoặc prompt. Không tự học."),
  bullet("Đồng hồ chi phí: token mỗi skill mỗi ngày, hiển thị trên web console. Có ngân sách ngày; vượt thì trợ lý dừng phần hỏi đáp tự do, giữ brief và duyệt."),
  bullet("Công tắc: tắt từng skill, tắt từng kênh, chuyển sang chế độ chỉ đọc bằng một cờ."),

  h1("4. Kiến trúc"),
  ...img(__dirname + "/arch.png", 600, 398, "Hình 1. Ba lớp: kênh, trợ lý, Business Central. Mũi tên nét đứt là đường hỏi đáp tự do qua BC MCP Server."),
  h2("4.1 Thành phần"),
  table(["Thành phần", "Công nghệ", "Vai trò", "Trạng thái"], [
    ["NWV Foundation + LS Adapter (AL)", "Per-tenant extension trên BC SaaS", "Lớp logic, ngưỡng, bảng đề xuất, custom API, bound action duyệt. Thêm ở bản này: bảng Agent Conversation Log tối giản để link đề xuất với tin nhắn, và API cho giải trình exception", "Đã viết bản 0.1, cần thêm hai object"],
    ["Custom API v1.0 + S2S OAuth", "BC chuẩn, GA từ 18.3", "Đường chính cho trợ lý đọc và ghi", "GA"],
    ["Webhook subscriptions", "BC API subscriptions (GA)", "BC đẩy sự kiện: exception mới, Transfer đã ship, đề xuất được duyệt trên UI", "GA, cần endpoint public"],
    ["BC MCP Server", "GA 04/2026, OAuth 2.1 theo user", "Hỏi đáp tự do ở phase 2, qua proxy gắn header", "GA phía BC; header cần proxy"],
    ["Sales and Inventory Forecast", "Extension chuẩn của BC, Azure AI", "Forecast cấp công ty cho UC1", "GA, giới hạn không tách location"],
    ["Ops Assistant service", "Python 3.11, anthropic SDK, FastAPI; chạy trên Azure Container Apps (hoặc VM NaviWorld cho POC)", "Orchestrator, skills, policy guard, scheduler, event listener, cost meter", "Có khung từ bản 0.1 (runner, tools, mock)"],
    ["Memory và audit", "PostgreSQL (Azure Database for PostgreSQL Flexible Server)", "Hội thoại, đề xuất mirror, kết quả, feedback, token usage", "Mới"],
    ["Channel adapters", "Azure Bot Service + Bot Framework SDK (Teams, Adaptive Cards, SSO); Zalo OA API (webhook, quick reply); Microsoft Graph (mail)", "Nhận tin, gửi thẻ, nhận nút bấm, lấy danh tính", "Mới"],
    ["Web console", "FastAPI + HTMX hoặc React nhỏ, đăng nhập Entra", "Danh sách đề xuất, KPI, log, ngưỡng, công tắc, chi phí", "Mới"],
    ["Mô hình ngôn ngữ", "Claude (claude-opus-4-8 cho quyết định, claude-haiku-4-5 cho phân loại tin nhắn) qua Anthropic API; hoặc Claude trên Microsoft Foundry nếu Marou cần dữ liệu ở Azure", "Hiểu tin nhắn, chọn tool, viết lý do và brief", "Chưa chạy live"],
    ["Quan sát", "Application Insights, OpenTelemetry từ service; telemetry BC", "Lỗi, độ trễ, chi phí", "Mới"],
  ], [1.6, 1.7, 2.1, 1.1]),

  h2("4.2 Nguyên tắc"),
  num("Business Central là hệ thống ghi sổ duy nhất. Trợ lý không giữ bản sao tồn kho; mỗi lần trả lời đọc mới. Postgres chỉ giữ hội thoại, đề xuất và kết quả.", "numbers"),
  num("Số do AL hoặc forecast tính. Mô hình ngôn ngữ chọn, giải thích, hỏi, viết. Tool không cho mô hình nhập số lượng tự do.", "numbers"),
  num("Mọi hành động mức 2 trở lên đi qua người, và chạy dưới danh tính người đó.", "numbers"),
  num("Trợ lý là một tiến trình, nhiều skill. Không dựng nhiều agent nói chuyện với nhau; phức tạp và khó audit.", "numbers"),
  num("Thay kênh không đổi lõi. Thay mô hình không đổi lõi. Cả hai là adapter.", "numbers"),

  h2("4.3 Luồng dữ liệu vào trợ lý"),
  table(["Nguồn", "Cách lấy", "Tần suất", "Dùng cho"], [
    ["Số đã tính (health line, suggestion, exception)", "Custom API, S2S, $filter theo store và ngưỡng", "Theo lịch (sau Job Queue đêm) và theo yêu cầu", "Brief, đề xuất, trả lời"],
    ["Dữ liệu thô (item, tồn theo lot, transfer, purchase line)", "API v2.0 và OData page tự expose, S2S", "Theo yêu cầu", "Trả lời câu hỏi cụ thể, kiểm tra trước khi đề xuất"],
    ["Sự kiện", "Webhook subscription trên API page, BC gọi endpoint của service", "Ngay khi có", "Nhắc, cập nhật thẻ trong chat, đóng vòng theo dõi"],
    ["POS", "Đã nằm trong database BC qua Web Replication của LS; đọc qua NWV POS Discount Log và Trans. Sales Entry", "Trễ vài phút đến vài chục phút", "Discount governance, store brief"],
    ["Forecast", "Sales and Inventory Forecast Entry của BC, tách xuống store bằng module Python", "Ngày", "Ước ngày hết hàng, số cần chuyển"],
    ["Đầu vào từ người", "Tin nhắn, ảnh, nút bấm qua channel adapter", "Ngay khi có", "Yêu cầu, giải trình, duyệt"],
    ["Câu hỏi tự do (phase 2)", "BC MCP Server qua proxy, token của người hỏi", "Theo yêu cầu", "Câu hỏi ngoài danh sách"],
  ], [1.9, 2.2, 1.1, 1.3]),

  h2("4.4 Danh tính và quyền"),
  p("Trợ lý có một tài khoản ứng dụng Microsoft Entra, đăng ký trong BC với permission set NWV AGENT RUN: đọc số đã tính, ghi đề xuất, ghi giải trình. Không có quyền trên chứng từ."),
  p("Người duyệt bấm nút trong Teams: Bot Framework SSO cho token Entra của người đó; service dùng on-behalf-of flow đổi lấy token Business Central và gọi bound action approve. BC ghi Transfer Order dưới tên người duyệt, audit đúng người. Đây là lý do Teams là kênh nên chọn nếu Marou có Microsoft 365."),
  p("Nếu kênh là Zalo: không có Entra. Phương án là bảng ánh xạ Zalo user sang BC user, xác nhận bằng mã PIN một lần, và lệnh duyệt chạy bằng tài khoản ứng dụng với trường Reviewed By ghi tên người duyệt. Audit chuẩn của BC sẽ thấy app user. Marou phải chấp nhận điểm này bằng văn bản nếu chọn Zalo."),
  p("Nhân viên cửa hàng không cần license Business Central để nhắn tin với trợ lý. Điểm phải kiểm tra trước khi cam kết: điều khoản multiplexing trong licensing guide của Microsoft đối với người dùng nội bộ truy cập dữ liệu BC qua ứng dụng trung gian có hành động ghi. NaviWorld tra và ghi kết luận vào tài liệu này trước khi gửi Marou."),

  h2("4.5 Dữ liệu gửi ra ngoài và bảo mật"),
  bullet("Dữ liệu gửi cho mô hình: mã hàng, tên hàng, kho, số lượng, ngày, giá trị tồn. Không có dữ liệu khách hàng. Staff ID và số thẻ member được thay bằng mã giả trước khi gửi, ánh xạ giữ trong Postgres."),
  bullet("Nếu Marou yêu cầu dữ liệu không rời Azure: dùng Claude trên Microsoft Foundry thay Anthropic API; code chỉ đổi endpoint và xác thực."),
  bullet("Secret trong Azure Key Vault. Endpoint webhook có xác thực bằng client state của BC subscription. Service không mở cổng nào khác ngoài webhook và bot endpoint."),
  bullet("Chính sách lưu: hội thoại 90 ngày, đề xuất và kết quả giữ theo kỳ kiểm toán của Marou."),

  h1("5. Ba luồng chính"),
  h2("5.1 Cửa hàng báo sắp hết hàng"),
  ...img(__dirname + "/flow.png", 600, 328, "Hình 2. Từ tin nhắn của cửa hàng đến Transfer Order và vòng nhắc kho."),
  p("Điểm đo được của luồng này: thời gian từ tin nhắn đến khi có đơn chuyển (hiện tại tính bằng giờ, mục tiêu dưới 15 phút), tỷ lệ đề xuất duyệt không sửa số, thời gian từ duyệt đến ship."),
  h2("5.2 Brief buổi sáng"),
  p("01:00 Job Queue chạy ba codeunit. 07:00 scheduler gọi ba skill đọc số, xếp ưu tiên, viết brief theo vai trò. 07:30 gửi Teams và email. Mỗi dòng brief là một đề xuất đã ghi trong BC, nút trên brief gọi đúng bound action. Người duyệt xử lý trên điện thoại trước khi đến văn phòng. 10:00 trợ lý tổng kết dòng nào chưa ai bấm, nhắc một lần."),
  h2("5.3 Exception discount có giải trình"),
  p("Sáng, rule DG-01 phát hiện nhân viên NV22 giảm 25% không có override. Trợ lý đọc bối cảnh (có member card không, có infocode không), nhắn quản lý cửa hàng Hà Nội: \"Hôm qua NV22 có 4 lần giảm giá tay trên 15%, tổng 1,8 triệu. Anh cho em lý do?\" Quản lý trả lời \"hàng trưng bày xả cuối ngày, có duyệt miệng\". Trợ lý ghi giải trình vào exception, chuyển trạng thái Explained, đưa lên brief của Retail Ops với tóm tắt hai dòng. Retail Ops kết luận Confirmed hay Dismissed. Điểm đo: thời gian từ phát hiện đến kết luận, số giờ Retail Ops rà mỗi tháng."),

  h1("6. Thay đổi so với bản 0.1"),
  table(["Phần", "Bản 0.1", "Bản này"], [
    ["Lớp AL", "Ba codeunit, bảng đề xuất, năm API page", "Giữ nguyên. Thêm API ghi giải trình exception, webhook subscription, và trường Channel Ref trên đề xuất"],
    ["Agent", "Ba job chạy đêm, ghi bảng, không nói chuyện", "Một trợ lý nhiều skill, hai chiều, có theo dõi và nhắc"],
    ["Người duyệt", "Mở page trong BC", "Bấm nút trong chat; page BC vẫn còn cho ai muốn"],
    ["Danh tính", "Tài khoản ứng dụng", "Token của người duyệt cho lệnh duyệt"],
    ["Dữ liệu vào", "Chỉ số đã tính", "Thêm dữ liệu thô, sự kiện, forecast của BC, tin nhắn và ảnh"],
    ["Bộ nhớ", "File log JSONL", "Postgres: hội thoại, đề xuất, kết quả, feedback, chi phí"],
    ["Cái Vincent thấy", "Một page danh sách", "Cửa hàng nhắn, 10 phút sau có đơn chuyển, hôm sau có hàng, không ai mở BC"],
  ], [1.2, 2, 2.8]),

  h1("7. Lộ trình"),
  table(["Giai đoạn", "Tuần", "Giao gì", "Đo gì"], [
    ["0. Nền", "1 và 2", "Deploy AL lên sandbox copy production, đặt ngưỡng, ghi baseline, bật Sales and Inventory Forecast, đăng ký Entra app và bot", "Baseline có chữ ký"],
    ["1. Trợ lý", "3 đến 6", "Teams bot với Replenishment, Inventory Health, Discount Governance; brief sáng; duyệt trong chat; theo dõi và nhắc; web console tối giản", "Thời gian từ yêu cầu đến đơn chuyển, tỷ lệ duyệt, giờ tiết kiệm, token mỗi ngày"],
    ["2. Mở rộng", "7 và 8", "Store Brief tuần, hỏi đáp qua MCP, demo Zalo adapter nếu cần; readout", "KPI so baseline theo mục 3 của bản 0.1"],
    ["3. Sau POC", "Rollout", "Tự duyệt trong policy (ví dụ chuyển dưới 50 cái và dưới 5 triệu), Item Journal cho write-off, Supplier Watch, cân nhắc chuyển sang Copilot Studio nếu Marou muốn billing và kênh trong tenant Microsoft", "Theo hợp đồng rollout"],
  ], [1, 0.8, 3, 1.4]),

  h1("8. Điểm cần chốt với Marou trước khi làm"),
  num("Kênh vận hành cửa hàng: Teams hay Zalo. Quyết định danh tính và license."),
  num("Marou có Microsoft 365 không, tenant admin có bật được Bot Service và, nếu sau này cần, external model trong Copilot Studio không."),
  num("Điều khoản multiplexing với người dùng cửa hàng (NaviWorld tra, Marou xác nhận)."),
  num("Dữ liệu có được rời Azure không. Quyết định Anthropic API hay Claude trên Microsoft Foundry."),
  num("Marou có dùng LS Central Replenishment không. Quyết định lớp logic UC5."),
  num("Lot và hạn dùng đã nhập đủ chưa; Transfer Route đã setup chưa; Staff Permission Group đã giới hạn discount chưa."),
  num("Ai là chủ sáng kiến, và năm use case tài chính của CFO còn trong phạm vi không."),

  pageBreak(),
  h1("Phụ lục A. Tool của từng skill"),
  table(["Skill", "Tool đọc", "Tool ghi", "Ràng buộc trong policy guard"], [
    ["Replenishment", "list_replenishment_suggestions, get_item_stock_by_location, get_inbound_transfers, get_store_forecast", "create_proposal(Transfer, Escalate), request_approval(card), notify(kho)", "quantity ≤ constrainedQty; from = kho trung tâm hoặc store có days of cover > 30; không trùng referenceKey"],
    ["Inventory Health", "list_inventory_health, get_lot_locations, get_store_velocity", "create_proposal(Markdown, Transfer, WriteOff, ReviewOnly), ask_store(confirm_damage)", "tối đa 10 đề xuất/run; Write-off chỉ khi Expired"],
    ["Discount Governance", "list_discount_exceptions, get_discount_log_context, get_staff_day_summary", "ask_store(explanation), set_exception_explanation, mark_under_review, create_proposal(Escalate, AuditNote)", "không set Confirmed/Dismissed; ẩn Staff ID khi gửi mô hình; câu hỏi giải trình dùng mẫu, không tự do"],
    ["Store Brief", "get_store_sales_margin, get_store_exceptions_week, list_proposals_week", "send_brief(channel)", "chỉ đọc"],
    ["Demand Signal", "get_company_forecast (BC), get_store_share", "write_store_forecast (Postgres)", "không ghi BC"],
  ], [1.1, 2.1, 1.9, 1.9]),

  h1("Phụ lục B. Dữ liệu trong Postgres"),
  table(["Bảng", "Nội dung", "Giữ bao lâu"], [
    ["conversation", "Kênh, người, thời điểm, nội dung tin, tin trợ lý, skill xử lý, token", "90 ngày"],
    ["proposal_mirror", "Bản sao đề xuất đã ghi BC (proposalId, trạng thái, kênh đã gửi, ai bấm, khi nào)", "Theo kỳ kiểm toán"],
    ["follow_up", "Việc cần kiểm tra lại: loại, tham chiếu BC, hạn, số lần nhắc, trạng thái", "Đến khi đóng + 90 ngày"],
    ["feedback", "Lý do từ chối, số bị sửa, đánh giá của người dùng", "Theo kỳ kiểm toán"],
    ["identity_map", "Zalo user hoặc Teams user sang BC user, store; PIN đã xác nhận", "Đến khi thu hồi"],
    ["usage", "Token và chi phí theo skill, theo ngày", "24 tháng"],
  ], [1.2, 3.6, 1.2]),

  h1("Phụ lục C. Object mới cần thêm vào AL"),
  bullet("API page exceptionExplanations: POST giải trình gắn với NWV Discount Exception, kèm kênh và người trả lời."),
  bullet("Field Channel Reference (Text[250]) trên NWV Agent Proposal: id tin nhắn hoặc card để cập nhật trạng thái ngược lại chat."),
  bullet("Webhook: đăng ký subscription trên agentProposals và discountExceptions qua API v2.0 subscriptions, không cần code AL; endpoint nhận ở service."),
  bullet("Nếu Marou dùng LS Replenishment: API page đọc Replen. Journal Line thay cho NWV Repl. Suggestion, cùng contract."),
];

build(
  "Marou Ops Assistant: chức năng và kiến trúc",
  "Bản 0.2, thay hướng ba agent chạy đêm bằng một trợ lý đa kênh có theo dõi. Tài liệu nội bộ NaviWorld.",
  { header: "NaviWorld Vietnam | Marou Ops Assistant | Nội bộ", footer: "Bản 0.2, 07/09/2026", cover: ["Soạn: Đinh Tiến Dũng, Principal Consultant", "Ngày: 07/09/2026", "Thay thế mục 4 và 5 của bản 0.1; các mục còn lại của bản 0.1 vẫn dùng", "Giả định: Marou dùng Microsoft 365 và Teams (chưa xác nhận)"] },
  children,
  __dirname + "/03 Marou Ops Assistant - Chuc nang va kien truc (v0.2).docx",
);
