// Tai lieu 08 ban 2.0: tai lieu demo noi bo. Kien truc, prompt mau theo vai tro, kich ban demo kem anh, muc dap ung UC,
// chi tiet cach xu ly tung phan (du bao, LS Replenishment, CTKM, ton kho, nha cung cap, tro ly). Noi bo NaviWorld.
//   cd docs; node build_08.js
// Prompt mau doc tu docs/demo/goi-y.json (sinh tu python/assistant/goi_y.py kem cau tra loi that tren BC).
const fs = require("fs");
const { p, h1, h2, h3, bullet, num, table, pageBreak, build, img } = require("./lib");

const ANH = __dirname + "/anh-demo/";
function kichThuoc(file) {
  const b = fs.readFileSync(file);
  return { w: b.readUInt32BE(16), h: b.readUInt32BE(20) };
}
function anh(ten, caption, maxW = 600, maxH = 820) {
  const file = ten.includes("/") ? ten : ANH + ten;
  if (!fs.existsSync(file)) return [p(`(Thiếu ảnh ${ten})`)];
  const { w, h } = kichThuoc(file);
  const r = Math.min(maxW / w, maxH / h);
  return img(file, Math.round(w * r), Math.round(h * r), caption);
}
let soHinh = 0;
const hinh = (ten, cap, maxW, maxH) => anh(ten, `Hình ${++soHinh}. ${cap}`, maxW, maxH);

const GOI_Y = JSON.parse(fs.readFileSync(__dirname + "/demo/goi-y.json", "utf8"));
const TEN_VAI = { store_manager: "Quản lý cửa hàng", dispatcher: "Điều phối kho", warehouse: "Kho trung tâm",
  supply_chain: "Supply Chain", retail_ops: "Retail Ops", admin: "Quản trị hệ thống" };
const cat = (s, n) => (s && s.length > n ? s.slice(0, n - 1).trimEnd() + "…" : s || "");

function bangGoiY(nguoi) {
  return table(["Thẻ gợi ý", "Câu gửi đi", "UC", "Trả lời đầu tiên trên BC ngày 14/09"], nguoi.goi_y.map((g) => [
    g.ten + (g.can_ai ? " (cần bật AI)" : "") + (g.ghi_bc ? " (ghi đề xuất vào BC)" : ""),
    g.cau, g.uc,
    g.tra_loi_bc ? cat(g.tra_loi_bc, 210) : (g.can_ai ? "Không chạy khi soạn tài liệu: cần bật AI." :
      g.ghi_bc ? "Không chạy khi soạn tài liệu vì ghi đề xuất vào BC; xem màn 6." : "Câu yêu cầu mở, đi qua planner (bản ghi đã duyệt khi tắt AI)."),
  ]), [1.3, 1.9, 0.45, 2.9]);
}
const nguoi = (id) => GOI_Y.find((x) => x.user_id === id);

const children = [
  // ------------------------------------------------------------------ 1
  h1("1. Tóm tắt và thông điệp của buổi demo"),
  p("Tài liệu nội bộ để team NaviWorld chuẩn bị và chạy buổi demo nội bộ bản POC Marou Ops Assistant. Phạm vi theo POC đã chốt: POC A (UC1 dự báo, UC2 sức khỏe tồn kho và truy xuất lô, UC5 bổ sung hàng cho cửa hàng) cộng POC D (UC10 trợ lý AI và dashboard). Mọi ảnh chụp và con số lấy từ trợ lý đang đọc Business Central NWV01, company NWV, LS Central 28.0, chụp ngày 14/09/2026 với Work Date 18/09/2026."),
  p("Bản 2.0 so với bản 1.0 thêm: bộ prompt mẫu theo từng vai trò (mục 3), dự báo Holt-Winters và việc đưa dự báo vào LS Replenishment, chương trình khuyến mãi (CTKM) của LS trên trợ lý, và mục 6 giải thích chi tiết cách từng phần xử lý số liệu."),
  h2("1.1 Ba câu cần người nghe nhớ"),
  num("Số liệu do Business Central tính. Code AL trong app NWV Marou Agent và module Replenishment của LS Central tính trong BC; trợ lý chỉ đọc lại. Tắt trợ lý thì dashboard trong BC vẫn chạy, số không đổi."),
  num("Trợ lý chỉ đề xuất, người của Marou quyết. Mọi đề xuất vào bảng NWV Agent Proposal ở trạng thái Proposed; chỉ khi người duyệt bấm Duyệt thì BC mới tạo Transfer Order."),
  num("Model là lớp cuối. Rule và kịch bản đã duyệt trả lời trước, không tốn token. Model Azure OpenAI chỉ được gọi cho câu mơ hồ hoặc yêu cầu mở, và code kiểm lại số trong câu trả lời của model."),
  h2("1.2 Chuẩn bị trước buổi demo"),
  table(["Việc", "Cách làm", "Kiểm thế nào"], [
    ["Work Date", "Đặt Work Date 18/09/2026 trên BC.", "Dải xanh trên trợ lý ghi ngày chốt 18/09/2026."],
    ["Chạy lớp tính AL", "Trang NWV Agent Setup: Run Inventory Health, Run Forecast Accuracy (bật Publish LS Forecast), Run Supplier Scorecard. Hoặc Job Queue.", "167 dòng Inventory Health, 222 dòng Forecast Accuracy, 2.072 dòng Retail Forecast Entry, 6 dòng scorecard."],
    ["Tính LS", "cd python; python ../tools/ls_replen_setup.py calc", "Journal MAROU-TO: Choco nuts S0001 = 82, Ice cream S0002 = 11, Choco bowl S0010 = 5."],
    ["Đối chiếu", "python -m bc_agent.cli uc1-reconcile, uc2-reconcile --from al, uc3-reconcile", "Ba lệnh báo khớp hoàn toàn."],
    ["Trợ lý", "cd python; python -m uvicorn assistant.channels.web:app --port 8188 --reload; bấm Business Central trên dải nguồn.", "Không sửa file Python trong lúc demo: --reload khởi động lại máy chủ, màn hình báo mất kết nối vài giây."],
    ["AI", "Vai Dũng, tab Cài đặt AI: để tắt, chỉ bật ở màn 7.", "Trần chi phí 2 USD mỗi ngày."],
    ["Sau buổi demo", "Xoá Transfer Order tạo thử khi duyệt (External Document No. AGENT *).", "TO Open cộng vào Quantity in Transfer In/Out của LS, làm lệch lần tính sau."],
  ], [1.1, 2.9, 2.4]),

  // ------------------------------------------------------------------ 2
  pageBreak(),
  h1("2. Kiến trúc hệ thống"),
  ...hinh(__dirname + "/kien-truc/kien-truc-chi-tiet.png", "Kiến trúc POC ngày 14/09/2026. Bản gốc độ phân giải cao: docs/kien-truc/kien-truc-chi-tiet.png", 600, 900),
  h2("2.1 Từng lớp làm gì"),
  table(["Lớp", "Nằm ở đâu", "Làm gì", "Không làm gì"], [
    ["1. Dữ liệu", "Bảng chuẩn của BC và LS Central", "Item Ledger Entry có lô và hạn dùng, Purchase Line, Purch. Rcpt. Line, bảng Replenishment, Retail Forecast Entry, Periodic Discount và Planned Event của LS. Mở ra ngoài qua 33 API page chỉ đọc.", "Không sao chép dữ liệu sang hệ thống khác."],
    ["2. Tính toán", "Codeunit AL trong app NWV Marou Agent 1.5.1.0; module Replenishment của LS", "Phân tầng tồn kho theo lô (UC2), backtest và dự báo Holt-Winters ghi vào LS (UC1), scorecard nhà cung cấp (UC3), ngoại lệ chiết khấu (UC7); LS tính đề xuất bổ sung kiểu Average Usage, Stock Levels, Retail Forecast (UC5). Ngưỡng nằm trên page NWV Agent Setup.", "Không gọi model."],
    ["3. Đề xuất và người duyệt", "Bảng NWV Agent Proposal, page NWV Agent Proposals", "Lưu đề xuất kèm lý do, số đã đọc, số lô. Duyệt đề xuất chuyển hàng thì BC tạo Transfer Order Open.", "Không có đường để trợ lý tạo chứng từ trực tiếp."],
    ["4. Trợ lý NaviWorld", "Python FastAPI do NaviWorld host: web console, MCP server 16 tool", "Hiểu câu hỏi qua bốn tầng, đọc bảng kết quả, giải thích, soạn đề xuất, áp policy và trần chi phí, lưu vết.", "Không tự tính lại con số của BC."],
    ["Model", "Azure OpenAI gpt-4.1-mini, eastus, Global Standard, 30.000 token mỗi phút", "Phân loại câu mơ hồ, dựng chuỗi tra cứu cho câu mở.", "Không đọc thẳng BC, không ghi gì."],
  ], [1.0, 1.6, 3.2, 1.5]),
  h2("2.2 Một câu hỏi đi qua hệ thống"),
  num("Rule NLU đọc câu: loại việc (17 intent), mặt hàng, mã hoặc tên cửa hàng, số lô. Nhận ra thì chạy skill tương ứng, không tốn token.", "numbers2"),
  num("Không nhận ra thì thử kịch bản đã duyệt: câu hỏi quản trị viên đã lưu, điền lại số trên dữ liệu mới. Khớp thì trả lời, không tốn token.", "numbers2"),
  num("Vẫn chưa được và AI đang bật: model phân loại câu. Nếu là yêu cầu mở, planner để model tự gọi các tool đọc rồi viết câu trả lời; code kiểm mỗi con số đứng sau mã cửa hàng có đúng dữ liệu của cửa hàng đó không.", "numbers2"),
  num("Nếu cần hành động, skill ghi đề xuất Proposed vào BC sau khi qua policy, chặn số vượt tồn nguồn và chống trùng. Thẻ đề xuất đến hộp thư của người duyệt.", "numbers2"),
  p("Tắt AI thì bước 3 bị bỏ; số trên dashboard không đổi vì do BC tính. Trong 73 prompt mẫu ở mục 3, chỉ 3 câu cần bật AI."),
  h2("2.3 Kết nối, quyền và chi phí"),
  bullet("Trợ lý gọi BC bằng S2S OAuth 2.0 (Entra app). Quyền: permission set của app (NWV AGENT RUN, NWV AGENT LS READ) cộng permission set tenant NWVMAROULSC cho hai bảng LS mà BC đòi khi đọc Item và khi ghi đề xuất."),
  bullet("Vai trò trên web console là ranh giới hiển thị, chưa phải xác thực: người dùng tự chọn vai. Bản chính thức gắn với đăng nhập Entra và gọi BC dưới danh tính người duyệt."),
  bullet("Token là số đếm thật từ response của Azure. Một câu mở khoảng 6 đến 14 nghìn token, 0,001 đến 0,002 USD. 10 USD tương đương khoảng 11,8 triệu token theo tỷ lệ vào ra đo được."),
  bullet("Dữ liệu xử lý ở region eastus. Nếu Marou cần giữ trong khu vực thì tạo resource Data Zone Standard; Copilot chuẩn của Microsoft và extension bên thứ ba chọn region riêng."),

  // ------------------------------------------------------------------ 3
  pageBreak(),
  h1("3. Prompt mẫu theo vai trò"),
  p("Màn hình chào của mỗi vai hiện bốn thẻ lớn và một hàng gợi ý khác, lấy từ python/assistant/goi_y.py. Bấm thẻ thì câu được điền vào ô nhập, sửa nếu cần rồi Enter. Test tests/test_goi_y.py gửi từng câu của từng người dùng demo vào trợ lý và kiểm câu nào cũng ra đúng loại việc, không rơi vào câu trợ giúp. Cột cuối là câu trả lời thật khi chạy trên BC NWV01 lúc soạn tài liệu; con số thay đổi khi dữ liệu BC đổi."),
  p("Mặt hàng trong câu của quản lý cửa hàng chọn đúng món có số trên BC: Quận 1 (S0001) Choco nuts vì LS đề xuất 82; Hà Nội (S0002) Ice cream, hàng min-max; Thảo Điền (S0005) Tiramisu; Đà Nẵng (S0010) Choco bowl, hàng bổ sung theo dự báo và có CTKM 23-25/09; cửa hàng trực tuyến (S0013) Milk 1 liter vì LS không có dòng nào cho cửa hàng này."),
  ...hinh("01b-chao-quan-ly-cua-hang.png", "Màn hình chào của Hà, quản lý Quán cà phê Đà Nẵng: bốn thẻ và gợi ý khác cho vai quản lý cửa hàng."),
  ...hinh("01c-chao-dieu-phoi.png", "Màn hình chào của Hùng, điều phối kho. Gợi ý ghi vào BC được đánh dấu."),
  ...[["ha.s0010", "3.1 Quản lý cửa hàng (ví dụ Hà, S0010)", "Hỏi về cửa hàng mình: tồn, lô sắp hết hạn, CTKM áp cho cửa hàng, vì sao LS đề xuất món của cửa hàng, tiến độ đề xuất gửi cho cửa hàng. Chỉ thấy dữ liệu cửa hàng mình. Bốn quản lý khác có cùng bộ câu, đổi món như trên; riêng Tuấn (S0005) thêm câu tiệc 150 khách."],
      ["hung.dieuphoi", "3.2 Điều phối kho (Hùng)", "Nhìn toàn hệ thống: brief ghi đề xuất chuyển hàng theo số của LS, lô hết hạn theo địa điểm, truy xuất lô, CTKM và chỗ LS chưa cộng nhu cầu."],
      ["kho.w0003", "3.3 Kho trung tâm (W0003)", "Lô trong kho, hàng mua chưa về kho, truy xuất lô, sự cố không có mẫu (kho mưa dột). Brief kho đọc đơn chờ ship; trên BC thật hiện chỉ báo không có đơn nào vì chưa đọc Transfer Order Released."],
      ["trang.sc", "3.4 Supply Chain (Trang)", "Vai chính của POC A: độ chính xác dự báo, vì sao LS ra số, nhà cung cấp, CTKM, PO quá hạn, bậc thang chẩn đoán, câu hỏi mở cho model."],
      ["thu.retailops", "3.5 Retail Ops (Thư)", "CTKM theo cửa hàng, mặt hàng, đã kết thúc; dự báo theo cửa hàng. Brief ngoại lệ chiết khấu POS mới có dữ liệu trên bản mô phỏng; NWV01 chưa có log POS."],
      ["dung.admin", "3.6 Quản trị (Dũng)", "Tiến độ mọi đề xuất, tự chấm điểm, câu hỏi cho model, câu ngoài bản ghi để thấy ranh giới rule và model. Chỉ vai này mở được tab Nhật ký agent và Cài đặt AI."],
    ].flatMap(([id, tieuDe, moTa]) => [h2(tieuDe), p(moTa), bangGoiY(nguoi(id))]),

  // ------------------------------------------------------------------ 4
  pageBreak(),
  h1("4. Kịch bản demo và hình ảnh"),
  p("Tổng khoảng 35 phút. Thứ tự đi theo POC A+D. Nhóm nút Kịch bản demo ở cột trái xếp đúng thứ tự này; bấm một nút là trợ lý đổi vai và gửi câu. Mỗi màn có câu cần nói, vì người nghe hay nhầm chỗ nào là AI."),
  ...hinh("01-man-hinh-chao.png", "Màn hình chào của vai Supply Chain. Dải xanh cho biết đang đọc Business Central NWV01; cột phải là đề xuất đang có trong BC."),

  h2("Màn 1. Dự báo đang sai ở đâu (UC1, 5 phút)"),
  p("Vai Trang hỏi \"độ chính xác dự báo thế nào\". Trợ lý đọc bảng NWV Forecast Accuracy: 74 cặp mặt hàng và điểm bán, kỳ kiểm tra 22/08 đến 18/09, Holt-Winters sai 37,1%, trung bình cùng thứ 8 tuần 37,2%, trung bình 28 ngày 38,2%, 20 cặp vượt ngưỡng. Mở tab Dự báo, chọn Choco bowl tại S0010: biểu đồ có 28 ngày kiểm tra và 28 ngày tới, ba ô vàng 23-25/09 là ngày có khuyến mãi."),
  p("Câu cần nói: Holt-Winters là mô hình thống kê chuỗi thời gian, chưa phải AI. Dữ liệu demo là mô phỏng nên mô hình chỉ hơn 0,1 điểm; giá trị nằm ở quy trình đo trên cùng kỳ và việc dự báo đi thẳng vào LS để bổ sung hàng. Chi tiết ở mục 6.2."),
  ...hinh("02-du-bao-tra-loi.png", "Trả lời về độ chính xác dự báo, có link sang page NWV Forecast Accuracy."),
  ...hinh("03-tab-du-bao.png", "Tab Dự báo: WAPE ba phương pháp theo điểm bán và nhóm hàng, biểu đồ Choco bowl tại S0010 có dự báo 28 ngày tới và ngày sự kiện."),
  ...hinh("03b-du-bao-choco-bowl.png", "Chi tiết một cặp: ba phương pháp, tham số Holt-Winters đã chọn, dự báo 7 ngày tới đã ghi vào LS, sự kiện sắp tới."),

  h2("Màn 2. Vì sao LS đề xuất con số đó (UC5, 6 phút)"),
  p("Ba câu, ba kiểu tính của LS. \"vì sao LS đề xuất Choco nuts cho S0001\": Average Usage, bán bình quân 11,675 mỗi ngày nhân 7 ngày phủ, trừ tồn khả dụng 0, ra 82. \"vì sao LS đề xuất Ice cream cho S0002\": Stock Levels, tồn 8 chạm Reorder Point 8 nên đưa lên Maximum Inventory 20, cần 12; kho còn 25 cho tổng nhu cầu 26 nên LS chia lại, cửa hàng này còn 11. \"vì sao LS đề xuất Choco bowl cho S0010\": Retail Forecast, LS cộng dự báo Holt-Winters 7 ngày được 24,2, khuyến mãi +150% ba ngày cuối nâng lên 38,66, trừ tồn 34 ra 5."),
  p("Câu cần nói: trợ lý không tính lại. Nó đọc từng dòng nhật ký tính của LS và nói bằng tiếng Việt; bộ diễn giải lấy 194 mẫu câu từ source LS 28.0 nên đọc được cả nhánh chưa có trong dữ liệu demo, trên BC nhận dạng 100% dòng log. Thẻ chỉ ra field nào phải sửa nếu muốn đổi kết quả."),
  ...hinh("04-ls-choco-nuts.png", "Giải thích đề xuất 82 Choco nuts cho S0001 (Average Usage)."),
  ...hinh("05-ls-ice-cream-min-max.png", "Giải thích đề xuất 11 Ice cream cho S0002 (Stock Levels, kho không đủ nên chia lại)."),
  ...hinh("05b-ls-choco-bowl-retail-forecast.png", "Giải thích đề xuất 5 Choco bowl cho S0010 (Retail Forecast cộng Planned Sales Demand)."),

  h2("Màn 3. Chương trình khuyến mãi (UC10, 4 phút)"),
  p("Vai Trang hỏi \"CTKM nào đang chạy và sắp tới\". Trợ lý đọc Periodic Discount của LS: 3 đang chạy, 2 sắp tới. Điểm đáng xem là dòng dưới MR2609-CB: CTKM Choco bowl áp cho mọi cửa hàng nhưng Planned Event chỉ có S0001 và S0010, nên LS Replenishment chưa cộng nhu cầu khuyến mãi ở S0002 và S0005. Đổi sang vai Hà hỏi \"CTKM nào sắp tới ở cửa hàng tôi\": chỉ thấy chương trình áp cho S0010."),
  p("Câu cần nói: chỗ lệch Choco bowl do NaviWorld cố ý tạo trong dữ liệu demo để thấy việc agent kiểm chéo giữa hai phân hệ LS (giá bán POS và bổ sung hàng). Trợ lý chỉ báo, không tự tạo Planned Event. Hai CTKM Tiramisu và Blueberry muffin là dữ liệu mẫu Cronus có sẵn trong company."),
  ...hinh("16-ctkm.png", "CTKM đang chạy và sắp tới, kèm cặp mặt hàng và cửa hàng LS chưa cộng nhu cầu."),
  ...hinh("16b-ctkm-cua-hang.png", "Quản lý cửa hàng S0010 hỏi CTKM của cửa hàng mình."),

  h2("Màn 4. Sức khỏe tồn kho và truy xuất lô (UC2, 5 phút)"),
  p("Tab Sức khỏe tồn kho: giá trị tồn ở các tầng xấu, lọc theo tầng. Bấm một lô cận hạn để mở Chi tiết lô: nguồn số, quy tắc phân tầng dừng ở bậc nào, lịch sử bán để cộng tay đối chiếu."),
  ...hinh("06-tab-suc-khoe-ton-kho.png", "Tab Sức khỏe tồn kho, 167 dòng do NWV Inv. Health Calc tính."),
  ...hinh("07-chi-tiet-lo.png", "Chi tiết lô: nguồn số liệu, quy tắc phân tầng, bán theo ngày."),
  p("Vai Hùng hỏi \"có mặt hàng nào đã hết hạn chưa\": 45 lô, chia theo địa điểm, thẻ đề xuất hủy có số lô. Tiếp \"truy xuất lô L260908-33170B\": lô Chocolate cake hạn 13/09 đã quá hạn, nhập 08/09 ở W0003, đã bán 8, còn 12 ở S0001 và 2 ở S0002; thẻ nói thu hồi lấy lại ở đâu và có link Item Ledger Entries lọc đúng lô. Vai Lan hỏi tồn Choco nuts ở cửa hàng mình: S0001 đã hết, kho còn 685."),
  ...hinh("08-hang-het-han.png", "Điều phối hỏi hàng hết hạn, không bị hỏi lại thuộc cửa hàng nào.", 600, 900),
  ...hinh("09-truy-xuat-lo.png", "Truy xuất một lô bánh đã quá hạn."),
  ...hinh("17-ton-cua-hang.png", "Quản lý cửa hàng hỏi tồn ở cửa hàng mình: trợ lý nói cửa hàng mình trước, rồi các nơi khác.", 600, 700),

  h2("Màn 5. Nhà cung cấp (UC3, 3 phút)"),
  p("Tab Nhà cung cấp và câu \"nhà cung cấp nào hay giao trễ\": AL-s Foods giao đúng hạn 48,7%, hứa 7 ngày thực tế 9; Dan-s Dairy 86,2%. Phải nói rõ đơn mua và phiếu nhận là dữ liệu demo NaviWorld tạo; phiếu nhận post vào địa điểm riêng NCC-NHAN rồi xuất bù nên không làm lệch tồn UC2 và LS."),
  ...hinh("10-tab-nha-cung-cap.png", "Tab Nhà cung cấp, 6 dòng do NWV Supplier Scorecard Calc tính."),
  ...hinh("11-nha-cung-cap-tra-loi.png", "Trợ lý trả lời về nhà cung cấp, thẻ có nút xem đơn quá hạn."),

  h2("Màn 6. Brief buổi sáng và từ đề xuất ra chứng từ (UC10, 5 phút)"),
  p("Vai Hà bấm Brief sáng nay: mặt hàng dưới ngưỡng, số đề xuất đang chờ, CTKM sắp bắt đầu tại cửa hàng. Đổi sang vai Hùng bấm Brief: trợ lý ghi đề xuất chuyển hàng theo số của LS vào BC (chỉ dòng chưa có đề xuất đang chờ) rồi hiện thẻ. Sửa số lớn hơn tồn nguồn rồi Duyệt: trợ lý chặn. Duyệt số hợp lệ thì BC tạo Transfer Order Open."),
  ...hinh("18-brief-cua-hang.png", "Brief của quản lý cửa hàng S0010.", 600, 700),
  ...hinh("12-brief-dieu-phoi.png", "Câu mở đầu brief của điều phối."),
  ...hinh("12b-the-de-xuat.png", "Thẻ đề xuất chuyển hàng có nút Duyệt, Từ chối, Vì sao LS ra số này."),

  h2("Màn 7. Câu ngoài kịch bản (UC10, 4 phút)"),
  p("Vai Dũng bật AI trong tab Cài đặt AI. Vai Trang gõ câu chưa có sẵn: \"so sánh tốc độ bán Flavored syrup giữa các cửa hàng 30 ngày qua, chỗ nào nên giữ ít hàng lại\". Planner tự gọi các tool đọc. Thẻ ghi rõ nguồn là model, số bước, số token và phần Kiểm tra số. Nói thẳng rằng phần kiểm số chỉ cảnh báo, người đọc vẫn quyết. Sau đó vai quản trị lưu câu này thành kịch bản đã duyệt; hỏi lại với mặt hàng khác thì trả lời không gọi model. Nhớ tắt AI sau màn này."),
  ...hinh("13-cau-hoi-mo-model.png", "Câu trả lời do model dựng chuỗi tra cứu, kèm kết quả kiểm số của code."),

  h2("Màn 8. Quản trị và chi phí (3 phút)"),
  p("Tab Nhật ký agent: đề xuất nào được soạn, policy nào áp, ai duyệt, câu nào đi qua model. Tab Cài đặt AI: token đã dùng, chi phí ước tính, trần theo ngày và cộng dồn, tỷ lệ câu không cần model. Tắt AI: số trên dashboard không đổi."),
  ...hinh("14-nhat-ky-agent.png", "Nhật ký agent (chỉ vai quản trị).", 600, 900),
  ...hinh("15-cai-dat-ai.png", "Cài đặt AI: bật tắt, trần chi phí, số token thật từng lượt.", 600, 900),

  // ------------------------------------------------------------------ 5
  pageBreak(),
  h1("5. Mức đáp ứng use case trong RFP"),
  p("Đánh giá theo đầu ra RFP (bản IT & Digital Transformation, 20/08/2026) ghi cho từng use case. Đáp ứng nghĩa là đã chạy trên BC NWV01 và có ảnh ở mục 4; một phần nghĩa là mới có một số đầu ra hoặc mới chạy trên dữ liệu mô phỏng."),
  table(["Use case", "Đầu ra RFP yêu cầu", "Đã có", "Chưa có hoặc giới hạn", "Mức"], [
    ["UC1 Demand Planning & Forecast", "Forecast dashboard; forecast vs actual; assumptions; exception list; accuracy tracking", "Tab Dự báo: WAPE, bias ba phương pháp theo cửa hàng và nhóm hàng; biểu đồ thực tế, dự báo kỳ kiểm tra và 28 ngày tới; 20 cặp vượt ngưỡng. Holt-Winters ghi 2.072 dòng Retail Forecast Entry, LS bổ sung hàng theo đó. Lịch sự kiện dùng Planned Event của LS.", "Chưa có mô hình học máy (dữ liệu demo không đủ để chứng minh). Chưa có màn hình ghi giả định kế hoạch. Chưa cấu hình Sales Hist. Adj. của LS.", "Đáp ứng phần đo và dự báo"],
    ["UC2 Inventory Health & Traceability", "Inventory health dashboard; aging/expiry alert; stock-out risk; traceability view", "6 tầng theo lô, đề xuất hủy lô hết hạn có số lô, Chi tiết lô, truy xuất hành trình lô và nơi cần thu hồi.", "Chưa nối OneTrace (chưa biết là gì).", "Đáp ứng"],
    ["UC3 Procurement & Supplier Performance", "Supplier scorecard; purchase commitment; late delivery và lead-time exceptions", "Scorecard theo nhà cung cấp và nhóm hàng, lead time hứa và thực tế, đơn quá hạn, trợ lý hỏi người nhận hàng.", "Đơn mua là dữ liệu demo NaviWorld tạo. Chưa có purchase planning.", "Đáp ứng phần scorecard"],
    ["UC4 Production & Distribution Planning", "Supply-demand view; production readiness; transfer plan", "Không", "Ngoài phạm vi A+D.", "Chưa làm"],
    ["UC5 Store Replenishment Optimization", "Replenishment suggestions; min-max; stock-out risk; transfer recommendations", "LS tính đề xuất kiểu Average Usage, Stock Levels và Retail Forecast; trợ lý giải thích từng bước; thẻ đề xuất chuyển hàng, duyệt ra Transfer Order; cảnh báo CTKM chưa có nhu cầu trong LS.", "Thẻ min-max chưa hiện bán bình quân.", "Đáp ứng"],
    ["UC6 Retail Sales, Margin & Store Performance", "Store dashboard; sales/margin trend", "Không", "Bài toán BI, ngoài phạm vi A+D.", "Chưa làm"],
    ["UC7 Promotion & Discount Governance", "Approval workflow; authorization matrix; discount log; exception/audit", "Tra cứu CTKM của LS trên trợ lý. Codeunit ba rule ngoại lệ chiết khấu và luồng hỏi giải trình (dữ liệu mô phỏng).", "NWV01 chưa có log POS; chưa có approval workflow và authorization matrix.", "Một phần"],
    ["UC8 Loyalty, Wallet Pass", "Digital member pass; loyalty rules", "Không", "Ngoài phạm vi.", "Chưa làm"],
    ["UC9 Multi-store Operations & Service Category", "Service catalog; workflows (MMV First)", "Không", "Chưa biết MMV First là gì.", "Chưa làm"],
    ["UC10 Supply Chain & Retail AI Assistant", "Natural-language answers; exception explanation; dashboard links; recommended actions", "Hỏi đáp tiếng Việt theo vai với prompt mẫu, câu hỏi đã duyệt thành kịch bản, giải thích ngoại lệ, link mở page BC, đề xuất có người duyệt, trần chi phí, nhật ký agent, MCP server 16 tool.", "Chưa nối client MCP thật; duyệt bằng Entra app, chưa theo danh tính người duyệt.", "Đáp ứng"],
  ], [1.2, 1.5, 2.6, 1.8, 0.8]),

  // ------------------------------------------------------------------ 6
  pageBreak(),
  h1("6. Chi tiết cách xử lý"),
  p("Mục này trả lời câu \"hệ thống tính ra con số đó thế nào\". Mỗi phần ghi: dữ liệu đầu vào, các bước, công thức, ví dụ bằng số thật trên BC, tham số chỉnh ở đâu và giới hạn."),
  h2("6.1 Nguyên tắc chung"),
  bullet("Một nguồn tính: code AL trong BC hoặc LS. Trợ lý chỉ đọc bảng kết quả qua API page chỉ đọc."),
  bullet("Ngày neo là Work Date (18/09/2026 cho demo), không phải ngày máy chạy. Trợ lý đọc As Of Date trên bảng kết quả để dùng cùng ngày."),
  bullet("Bản đối chiếu độc lập: python/bc_agent (inventory.py, forecast.py, supplier.py) chép lại công thức AL và chạy trên cùng dữ liệu BC. Lệnh uc1-, uc2-, uc3-reconcile phải khớp từng dòng; lệch là một trong hai bên sai. Ngày 14/09 khớp 167 dòng tồn kho, 222 dòng dự báo cộng 2.072 dòng Forecast Entry, 6 dòng scorecard."),

  h2("6.2 UC1 Dự báo nhu cầu"),
  h3("Mục tiêu"),
  p("Trả lời hai câu: dự báo đang sai bao nhiêu, ở đâu (đo), và nhu cầu những ngày tới là bao nhiêu để bổ sung hàng (dự báo). Codeunit 70120 NWV Forecast Accuracy Calc làm cả hai trong một lần chạy, khoảng 10 giây cho 74 cặp."),
  h3("Bước 1. Dựng chuỗi bán theo ngày"),
  bullet("Đơn vị đo là cặp mặt hàng x cửa hàng có dòng Sale. Kho trung tâm không đo: luồng xuất của kho là lịch chuyển hàng, không phải nhu cầu bán, WAPE thử ra 93 đến 129%."),
  bullet("Nhu cầu mỗi ngày = tổng số lượng dòng Item Ledger Entry loại Sale của cặp trong ngày đó (codeunit NWV Demand Calc)."),
  bullet("Tồn đầu ngày tính cộng dồn từ mọi dòng Item Ledger Entry của cặp."),
  h3("Bước 2. Làm sạch: bỏ ngày không phản ánh nhu cầu"),
  bullet("Ngày hết hàng: tồn đầu ngày bằng hoặc dưới 0 và bán 0. Bán 0 vì không có hàng chứ không phải vì không ai mua; giữ lại thì dự báo bị kéo xuống, bổ sung ít hơn, lại hết hàng."),
  bullet("Ngày có sự kiện: có dòng LSC Replen. Planned Sales Demand đang Enabled cho đúng mặt hàng, cửa hàng, ngày (lịch khuyến mãi chuẩn của LS), hoặc nằm trong khoảng khai ở bảng NWV Demand Exception. Ngày bán tăng vì khuyến mãi không phải mức nền."),
  bullet("Ngày bị bỏ không tính sai số. Với Holt-Winters, ngày bị bỏ được điền bằng trung bình cùng thứ của tối đa 8 tuần trước để chuỗi liền mạch; không đủ thì lấy trung bình 56 ngày hợp lệ gần nhất."),
  p("Ví dụ: trước khi bỏ ngày khuyến mãi tháng 7 của Choco pillar, SWA8 sai 41,2%; sau khi bỏ còn 37,2%. Tuần khuyến mãi bán gấp ba làm trung bình cùng thứ lệch nặng nhất."),
  h3("Bước 3. Backtest: đo trên kỳ đã biết kết quả"),
  p("Kỳ kiểm tra là 28 ngày cuối kết thúc ở Work Date: 22/08 đến 18/09/2026. Dự báo cho kỳ này chỉ được dùng dữ liệu trước 22/08, rồi so với bán thật. Cách này giống việc đứng ở ngày 21/08 dự báo cho bốn tuần sau."),
  table(["Phương pháp", "Cách lập dự báo", "Vai trò"], [
    ["MA28, trung bình 28 ngày", "Trung bình bán của 28 ngày hợp lệ gần nhất trước kỳ kiểm tra (nhìn lùi tối đa 84 ngày). Mọi ngày trong kỳ cùng một số.", "Mốc đơn giản nhất, gần với cách Average Usage của LS."],
    ["SWA8, trung bình cùng thứ", "Mỗi thứ trong tuần lấy trung bình các ngày cùng thứ hợp lệ trong 56 ngày (8 tuần) trước kỳ. Thứ Bảy dự báo bằng trung bình các thứ Bảy.", "Mốc có mùa vụ tuần."],
    ["HW, Holt-Winters", "Mô hình thống kê chuỗi thời gian: tách mức nền, xu hướng và mùa vụ theo thứ, cập nhật dần theo từng ngày. Học trên tối đa 365 ngày trước kỳ.", "Phương pháp dự báo chính, ghi vào LS."],
  ], [1.3, 3.6, 1.6]),
  h3("Holt-Winters làm gì, nói bằng lời"),
  p("Mỗi ngày mô hình giữ hai thứ: mức nền (bình quân một ngày bán bao nhiêu nếu bỏ ảnh hưởng của thứ) và bảy hệ số mùa vụ (thứ Bảy thường cao hơn nền bao nhiêu, thứ Hai thấp hơn bao nhiêu). Dự báo ngày mai = mức nền + hệ số của thứ ngày mai. Khi có số bán thật, mô hình sửa mức nền một phần theo sai lệch (phần đó là alpha) và sửa hệ số mùa vụ một phần (gamma). Alpha nhỏ nghĩa là mức nền đổi chậm, ít bị kéo bởi một ngày bán bất thường."),
  bullet("Khởi tạo: mức nền = trung bình của tối đa 4 tuần đầu; hệ số mùa vụ = trung bình từng thứ trừ mức nền. Cần ít nhất 28 ngày kể từ ngày bán đầu tiên."),
  bullet("Chọn tham số tự động cho từng cặp: thử 40 tổ hợp, alpha trong {0,05; 0,1; 0,2; 0,3; 0,5}, gamma trong {0,05; 0,1; 0,2; 0,3}, và có hoặc không có xu hướng tắt dần (beta 0,1, phi 0,9). Chọn tổ hợp có tổng bình phương sai số dự báo một ngày trước nhỏ nhất trên dữ liệu học, bỏ 7 ngày đầu. Tham số đã chọn ghi vào cột Model Parameters."),
  bullet("Không cần thư viện ngoài: toàn bộ viết bằng AL trong BC, bản Python chép lại để đối chiếu."),
  h3("Bước 4. Đo sai số"),
  bullet("WAPE % = tổng |bán thật - dự báo| của từng ngày / tổng bán thật x 100. Đọc là: trung bình dự báo lệch bao nhiêu phần trăm lượng bán. WAPE gộp nhiều cặp cộng tổng sai số và tổng bán của các cặp, nên cặp bán nhiều có trọng số lớn."),
  bullet("Bias % = (tổng dự báo - tổng bán thật) / tổng bán thật x 100. Dương là dự báo cao (dễ tồn thừa), âm là dự báo thấp (dễ hết hàng). WAPE thấp mà bias lớn vẫn là dấu hiệu xấu."),
  bullet("Cặp cần xem: bán thật trong kỳ từ 20 trở lên, và WAPE trên 50% hoặc |bias| trên 30%. Ngưỡng nằm trên NWV Agent Setup (field 51, 52, 53)."),
  p("Ví dụ Choco bowl tại S0010, kỳ 22/08 đến 18/09, 28 ngày, không ngày nào bị bỏ, bán thật 104:"),
  table(["Phương pháp", "Mức một ngày", "Tổng dự báo", "Tổng sai số tuyệt đối", "WAPE", "Bias", "Tham số"], [
    ["MA28", "3,75", "105", "39,5", "38%", "+1%", ""],
    ["SWA8", "3,59", "100,5", "30", "28,8%", "-3,4%", ""],
    ["Holt-Winters", "3,61", "100,9", "34,3", "33%", "-3%", "alpha 0,05, gamma 0,05, không xu hướng"],
  ], [1.1, 0.8, 0.8, 1.1, 0.7, 0.7, 1.8]),
  p("Tổng dự báo của ba phương pháp gần bằng bán thật (bias nhỏ), nhưng sai số từng ngày lớn vì bán lẻ theo ngày dao động mạnh: tuần đầu bán 7, 6, 4, 2, 6, 3, 2 trong khi Holt-Winters dự báo 4,6; 3,7; 3,0; 3,7; 3,4; 3,3; 3,5. Với cặp này trung bình cùng thứ tốt hơn; trên toàn bộ 74 cặp Holt-Winters tốt nhất."),
  table(["Tổng 74 cặp", "Holt-Winters", "SWA8", "MA28"], [
    ["WAPE gộp", "37,1%", "37,2%", "38,2%"],
    ["Cặp vượt ngưỡng (theo phương pháp tốt nhất)", "20", "", ""],
  ], [2.4, 1.2, 1.2, 1.2]),
  h3("Vì sao Holt-Winters chỉ hơn 0,1 điểm"),
  p("Dữ liệu demo do NaviWorld sinh: mỗi ngày bán là số ngẫu nhiên quanh một kỳ vọng biết trước. Phần ngẫu nhiên không mô hình nào đoán được. Thử ngoài hệ thống ngày 14/09 trên cùng 74 cặp (tools/forecast_lab.py): trần lý thuyết tính từ chính hàm sinh dữ liệu là 34,6%; Holt-Winters của thư viện statsmodels 37,7%; SARIMA 37,8%; LightGBM 42,9% (thua vì chỉ có 74 chuỗi, 6 tháng, không có biến giá hay khuyến mãi). Nghĩa là trên dữ liệu này chỉ còn khoảng 3 điểm để cải thiện. Không dùng các con số này để hứa với Marou; phải chạy lại trên lịch sử bán thật."),
  h3("Bước 5. Dự báo các ngày tới và ghi vào LS"),
  bullet("Holt-Winters học lại trên toàn bộ lịch sử đến Work Date (kể cả kỳ kiểm tra), dự báo 28 ngày tới (field 54 Forecast Horizon Days)."),
  bullet("Ghi vào bảng chuẩn của LS: LSC Forecast Entry (Retail Forecast Entry), mỗi dòng một mặt hàng x cửa hàng x ngày. Xoá dòng của cặp từ ngày mai trở đi rồi ghi lại, nên chạy lại không trùng. Chỉ ghi khi bật field 55 Publish LS Forecast."),
  bullet("Forecast Quantity (Lower) và (Upper) = dự báo ± 1,2816 x độ lệch chuẩn của sai số một bước, tức khoảng 80%. Forecast Quality % = 100 - WAPE Holt-Winters của cặp."),
  bullet("Dự báo ghi vào là mức nền, không cộng khuyến mãi. LS tự cộng Planned Sales Demand khi tính bổ sung; cộng sẵn thì bị tính hai lần."),
  table(["Ngày", "19/09", "20/09", "21/09", "22/09", "23/09", "24/09", "25/09"], [
    ["Forecast Quantity", "4,68", "3,78", "2,88", "3,22", "3,30", "3,16", "3,18"],
    ["Lower / Upper", "2,85 / 6,52", "1,94 / 5,62", "1,04 / 4,72", "1,39 / 5,06", "1,46 / 5,13", "1,32 / 5,00", "1,35 / 5,02"],
  ], [1.3, 0.8, 0.8, 0.8, 0.8, 0.8, 0.8, 0.8]),
  p("Choco bowl tại S0010, Forecast Quality 67% (= 100 - 33). Thứ Bảy 19/09 cao nhất vì hệ số mùa vụ thứ Bảy dương."),
  h3("Bước 6. LS Replenishment dùng dự báo thế nào"),
  p("Mặt hàng đặt LSC Replen. Calculation Type = Retail Forecast (33310 Choco pillar và 33341 Choco bowl trong demo) được LS tính bằng hàm Calc-LSForecast, đọc trong source LS 28.0:"),
  num("Cộng Forecast Quantity các ngày trong cửa sổ phủ (Store Stock Cover Reqd 7 ngày): 19/09 đến 25/09 = 24,2.", "numbers3"),
  num("Chỉnh từng ngày theo Planned Sales Demand. Sự kiện KM-CHOCOBOWL-09 kiểu Additional % Factor (to Forecast) 150 cho 23 đến 25/09: mỗi ngày nhân 2,5. 3,30 thành 8,25; 3,16 thành 7,90; 3,18 thành 7,95. Tổng thành 38,66.", "numbers3"),
  num("Trừ tồn khả dụng (tồn + hàng đang chuyển đến - đang chuyển đi - đơn bán ...) = 34. Còn 4,66, làm tròn lên 5. LS đề xuất chuyển 5 Choco bowl từ W0003.", "numbers3"),
  p("Ngày chưa có Forecast Entry thì LS dùng bán bình quân của Average Usage, vì LSC Forecast Setup đặt Forecast Exception Handling = Use Average Usage Result. Hai kiểu Planned Demand khác: Substitute Quantity (thay hẳn số dự báo) và Additional Quantity (cộng số lượng)."),
  h3("Tham số và giới hạn"),
  bullet("Chỉnh trên NWV Agent Setup: 50 Holdout Days (28), 51 WAPE Warn % (50), 52 Bias Warn % (30), 53 Min Actual Qty (20), 54 Forecast Horizon Days (28), 55 Publish LS Forecast. Lịch sự kiện khai trên Replen. Planned Events của LS."),
  bullet("Chưa làm: báo cáo Calc. Sales Hist. Adj. PDE của LS (bỏ phần bán tăng do sự kiện khỏi bán bình quân kiểu Average Usage) chưa cấu hình Sales Hist. Adj. Rule. LS còn module LS Forecast chạy qua LS Insight (ARIMA, Seasonal ARIMA) và BC có Sales and Inventory Forecast (Azure AI); chưa so trên dữ liệu thật."),

  h2("6.3 UC5 Bổ sung hàng cho cửa hàng bằng LS Replenishment"),
  p("Đề xuất bổ sung do module Replenishment của LS tính, không phải NaviWorld tính. Chạy: Scheduler Job hoặc tools/ls_replen_setup.py calc gọi web service NWVReplenService: Update Out of Stock, Calc. Item Quantities, rồi tính journal MAROU-TO (chuyển từ kho W0003) và MAROU-PO (mua). Tham số lấy từ Item (nhóm Replenishment), Item Distribution, Replen. From Warehouse, Replen. Setup."),
  table(["Kiểu tính", "Công thức (đọc trong source LS 28.0)", "Ví dụ trên BC"], [
    ["Average Usage", "Số cần = bán bình quân ngày x số ngày phủ x Forward Sales Forecast Factor - tồn khả dụng; làm tròn lên theo Transfer Multiple; âm thì 0. Bán bình quân theo Sales Profile DEFAULT: 3 tuần gần nhất trọng số 75, tuần 4-6 trọng số 15, tuần 7-8 trọng số 10, bỏ ngày hết hàng.", "Choco nuts S0001: 11,675 x 7 - 0 = 81,7, tròn 82."],
    ["Stock Levels (min-max)", "Tồn khả dụng ≤ Reorder Point thì đưa lên Maximum Inventory; không thì 0. Kho không đủ cho mọi cửa hàng thì LS chia lại theo tỷ lệ.", "Ice cream S0002: tồn 8 = Reorder Point 8, lên 20, cần 12; kho 25 cho tổng 26, chia lại còn 11."],
    ["Retail Forecast", "Tổng Forecast Entry trong cửa sổ phủ, chỉnh theo Planned Sales Demand, trừ tồn khả dụng (mục 6.2 bước 6).", "Choco bowl S0010: 24,2 thành 38,66, trừ 34, ra 5."],
  ], [1.2, 3.6, 1.8]),
  h3("Trợ lý giải thích thế nào"),
  bullet("LS ghi Calc. Log Lines cho từng bước khi tính. Trợ lý đọc log của đúng dòng journal qua API page, không tính lại."),
  bullet("Knowledge lấy từ source LS 28.0: 194 mẫu câu (Label) LS ghi vào log, 116 câu có diễn giải tiếng Việt, 65 tham số kèm chỗ sửa. Bộ đọc khớp từng dòng log với mẫu, bóc giá trị, ghép câu. Đo trên BC: 2.831 dòng log, nhận dạng 100%. Dòng nào không đọc được thì hiện nguyên văn."),
  bullet("Thẻ còn bổ sung phần LS không ghi log: bán bình quân từ Replen. Item Quantity, thành phần tồn, dự báo từng ngày và sự kiện với kiểu Retail Forecast, và field cần sửa để đổi kết quả."),
  bullet("Duyệt đề xuất: brief điều phối ghi đề xuất theo Quantity cuối của LS (không phải System Suggested Quantity), chống trùng theo Reference Key còn hiệu lực trong BC."),

  h2("6.4 Chương trình khuyến mãi của LS"),
  table(["Bảng LS", "Dùng để"], [
    ["LSC Periodic Discount (99001453)", "Đầu chương trình: loại (Multibuy, Mix&Match, Disc. Offer, Total Discount, Tender Type, Item Point, Line Discount), Status, Price Group."],
    ["LSC Validation Period (99001481)", "Ngày bắt đầu, kết thúc và giờ hiệu lực (ví dụ 19:00-22:00)."],
    ["LSC Periodic Discount Line (99001454)", "Mặt hàng, nhóm hàng hoặc tất cả; dòng Exclude bị trừ ra."],
    ["LSC Store Price Group (99001575)", "Cửa hàng thuộc nhóm giá nào. CTKM có Price Group áp cho cửa hàng có nhóm đó; Price Group trống áp mọi cửa hàng."],
    ["LSC Replen. Planned Event, Planned Sales Demand", "Cách chuẩn để Replenishment biết CTKM: Planned Event Source Type = Discount, Source Code = số CTKM; báo cáo Update Planned Sales Demand from Discount sinh dòng nhu cầu từng ngày."],
  ], [2.2, 4.4]),
  bullet("Trạng thái: đang chạy (Enabled, đã tới ngày), sắp tới (Enabled, chưa tới ngày), chưa bật (Disabled mà sắp tới hoặc mới bắt đầu trong 28 ngày: POS sẽ không áp, có thể quên bật), đã tắt (Disabled từ lâu, chỉ đếm), đã kết thúc."),
  bullet("Chỉ liệt kê CTKM có mặt hàng bán trong 90 ngày tại cửa hàng áp dụng. Company NWV còn 31 CTKM mẫu Cronus đang bật cho hàng thời trang, golf; trợ lý chỉ đếm."),
  bullet("Kiểm chéo: với CTKM sắp tới hoặc bắt đầu trong 28 ngày, lấy các cặp mặt hàng x cửa hàng thuộc nhóm giá và đang bán, tìm dòng Planned Sales Demand trong thời gian CTKM. Cặp không có dòng thì LS Replenishment đang tính như ngày thường. CTKM chạy từ lâu thì không cảnh báo vì lịch sử bán đã gồm tác động của nó."),
  p("Dữ liệu demo: MR2609-CP Choco pillar -20% 23-25/09 nhóm FOOD (S0001, S0002), Planned Event đủ hai cửa hàng. MR2609-CB Choco bowl -15% 23-25/09 mọi cửa hàng, Planned Event chỉ S0001 và S0010, cố ý lệch ở S0002 và S0005. MR2609-CR bánh sừng bò -30% sau 19h cả tháng 9, không Planned Event. MR2607-CP tháng 7 đã kết thúc."),

  h2("6.5 UC2 Sức khỏe tồn kho và truy xuất lô"),
  p("Codeunit 70101 NWV Inv. Health Calc, mỗi dòng kết quả là mặt hàng x địa điểm x lô. Tồn = tổng Remaining Quantity của Item Ledger Entry còn Open. Giá trị = số lượng x Unit Cost (POC)."),
  bullet("Nhu cầu bình quân ngày (NWV Demand Calc) trên cửa sổ 90 ngày (Sales History Days): cửa hàng có bán thì đếm Sale; kho trung tâm luôn đếm tổng lượng xuất (Sale, Negative Adjmt., Transfer). Ngày tồn bằng 0 mà không bán được bị loại khỏi mẫu số."),
  bullet("Days of cover = tồn / nhu cầu bình quân ngày. Hạn dùng của lô lấy từ Item Ledger Entry."),
  table(["Thứ tự", "Tầng", "Điều kiện (dừng ở điều kiện đầu tiên khớp)"], [
    ["1", "Expired, quá hạn", "Còn dưới 0 ngày đến hạn."],
    ["2", "Near Expiry, cận hạn", "Còn ≤ Near Expiry Days (mặc định 45, đặt riêng theo nhóm hàng ở NWV Category Threshold). Lý do ghi rõ có bán hết trước hạn không."],
    ["3", "Stock-out Risk, rủi ro đứt hàng", "Có nhu cầu và days of cover < Stock-out Risk Days (7)."],
    ["4", "Slow-moving, chậm luân chuyển", "Đã từng bán nhưng ≥ Slow-moving Days (60) không bán, hoặc không có nhu cầu trong cửa sổ."],
    ["5", "Excess, tồn thừa", "Days of cover > Excess Days (90)."],
    ["6", "Healthy", "Còn lại."],
  ], [0.6, 1.6, 4.4]),
  p("Risk Score 0 đến 100 để sắp thứ tự, không phải xác suất. Kết quả trên BC: 167 dòng, 45 quá hạn, 32 cận hạn, 47 rủi ro đứt hàng, 4 chậm luân chuyển, 1 tồn thừa, 38 bình thường."),
  p("Truy xuất lô: gom mọi dòng Item Ledger Entry của lô theo địa điểm và loại bút toán, cộng số lượng; nơi còn tồn là nơi phải thu hồi, phần đã bán cho khách không lấy lại được từ tồn kho."),

  h2("6.6 UC3 Scorecard nhà cung cấp"),
  p("Codeunit 70121 NWV Supplier Scorecard Calc trên Purchase Line (Order) và Purch. Rcpt. Line, cửa sổ 180 ngày đến Work Date."),
  bullet("Đến hạn: Expected Receipt Date ≤ Work Date. Đúng hạn: nhận đủ và ngày nhận đủ ≤ Expected Receipt Date + dung sai (On-time Tolerance Days)."),
  bullet("Giao đủ lần đầu: phiếu nhận ngày sớm nhất đã đủ số lượng dòng. Trễ: ngày nhận đủ - ngày hẹn; dòng quá hạn chưa nhận thì Work Date - ngày hẹn."),
  bullet("Lead time hứa = Expected Receipt Date - Order Date; lead time thực = ngày nhận đủ - Order Date."),
  bullet("Cần xem: đúng hạn dưới 80% khi có ít nhất 3 dòng đến hạn, hoặc có dòng quá hạn. Có dòng tổng theo nhà cung cấp và dòng theo nhóm hàng."),

  h2("6.7 UC10 Trợ lý: định tuyến, kiểm soát và lưu vết"),
  h3("Định tuyến bốn tầng"),
  table(["Tầng", "Khi nào dùng", "Chi phí"], [
    ["Rule NLU", "Câu nhận ra loại việc; nếu loại việc cần mặt hàng thì phải tra được mã từ chữ người gõ.", "0 token"],
    ["Kịch bản đã duyệt", "Câu giống câu quản trị viên đã lưu (từ khớp từ 0,6, đủ biến mặt hàng, địa điểm) và mọi ô số đọc được trên dữ liệu mới.", "0 token"],
    ["Model phân loại", "Rule không chắc; AI đang bật và còn trần chi phí.", "Vài trăm token"],
    ["Planner", "Yêu cầu mở. Model gọi tool đọc (tối đa vài vòng), code kiểm số theo địa điểm. Tắt AI thì chỉ đi lại được bản ghi đã duyệt (tiệc 150 khách, kho mưa dột).", "6 đến 14 nghìn token"],
  ], [1.3, 4.2, 1.1]),
  h3("Lưu câu hỏi thành kịch bản"),
  p("Câu đi qua model được lưu kèm chuỗi tool và câu trả lời. Quản trị bấm Lưu thành kịch bản: code (không phải model) truy mỗi con số trong câu trả lời về đúng ô trong kết quả tool, mặt hàng và địa điểm thành biến. Số nào không truy được thì báo, vì đó là số model tự tính. Câu kết luận so sánh bị báo để người duyệt viết lại trung tính, vì kịch bản chỉ điền lại số, không suy luận lại."),
  h3("Policy cho đề xuất"),
  table(["Mã", "Loại việc", "Chế độ", "Mô tả"], [
    ["P-01", "Chuyển hàng từ kho W0003", "Tự làm", "Dưới 2 tuần bán, giá vốn dưới 200 (mặc định chạy Shadow: chỉ báo trước)."],
    ["P-02", "Chuyển hàng khác", "Người duyệt", "Chuyển giữa cửa hàng hoặc giá trị lớn."],
    ["P-03", "Kho hết hàng", "Người duyệt", "Báo người, trợ lý không tự xử lý."],
    ["P-04, P-05", "Giảm giá, huỷ hàng", "Người duyệt", "Ảnh hưởng doanh thu và sổ sách."],
    ["P-06", "Chuyển lô cận date", "Tự làm", "Sang cửa hàng bán nhanh, giá vốn dưới 100."],
    ["P-07", "Chặn mua hàng dư", "Tự làm", "Gỡ lại được."],
    ["P-08", "Chiết khấu, nhân viên", "Người duyệt", "Kỷ luật nhân viên do người kết luận."],
    ["P-09, P-10", "Đổi tham số dự báo, vượt kế hoạch", "Người duyệt", "Đổi hành vi mọi lần sau."],
  ], [0.9, 1.6, 1.0, 3.1]),
  bullet("Chặn ở lớp tool: số lượng không vượt tồn nguồn; chống trùng theo Reference Key còn hiệu lực trong BC. Có Shadow mode, trần số việc tự làm mỗi ngày, nút dừng khẩn cấp."),
  bullet("Trần chi phí AI: 2 USD mỗi ngày, 10 USD cộng dồn; chạm trần thì tự về rule, không báo lỗi."),
  bullet("Lưu vết: tin nhắn và đoạn chat, chi-phi.sqlite (token thật từng lượt), kich-ban.sqlite (câu hỏi, chuỗi tool, đánh giá), Nhật ký agent (ai đề xuất, policy nào, ai duyệt)."),
  bullet("MCP server POST /mcp, 16 tool (15 đọc và create_proposal), dùng chung policy và luồng duyệt với chat."),

  h2("6.8 UC7 Ngoại lệ chiết khấu (mô phỏng)"),
  p("Codeunit 70104 kiểm soát sau bán trên log chiết khấu POS: DG-01 một dòng giảm tay vượt Max Manual Discount % (15); DG-02 một nhân viên trong ngày có tỷ trọng doanh số giảm tay trên 20%; DG-03 một nhân viên trong ngày giảm tay quá 5 lần. Trợ lý hỏi giải trình quản lý cửa hàng, Retail Ops kết luận. Kiểm soát trước khi giảm giá (quyền nhân viên, duyệt tại POS) là cấu hình LS Central."),

  // ------------------------------------------------------------------ 7
  pageBreak(),
  h1("7. Câu hỏi hay gặp khi demo"),
  table(["Câu hỏi", "Trả lời gợi ý"], [
    ["AI nằm ở đâu, toàn thấy BC tính?", "Đúng là số do BC tính, đó là chủ ý. Agent nằm ở bốn việc: hiểu câu tự do theo vai, tự chọn đọc gì cho câu chưa gặp, kiểm chéo giữa các phân hệ (CTKM và nhu cầu LS), soạn đề xuất có lý do và đưa đúng người duyệt. Màn 3 và màn 7 cho thấy rõ nhất."],
    ["Holt-Winters có phải AI không?", "Không, là mô hình thống kê. Trên dữ liệu demo nó chỉ hơn trung bình 0,1 điểm vì dữ liệu là mô phỏng. Quy trình đo đã sẵn: mô hình học máy nào sau này cũng phải thắng trên cùng kỳ kiểm tra thì mới dùng."],
    ["80% câu hỏi ngoài kịch bản thì sao?", "Câu mới đi qua model; câu trả lời tốt được quản trị lưu thành kịch bản, lần sau không tốn token. Không huấn luyện lại model."],
    ["Model tính sai thì sao?", "Model không được tính số của nghiệp vụ. Số lấy từ tool; code kiểm số theo địa điểm và cảnh báo. Hai lần thử thật model từng đếm sai và kết luận ngược phép tính của chính nó, nên nguyên tắc này bắt buộc."],
    ["Trợ lý có tự tạo chứng từ không?", "Không. Chỉ ghi đề xuất Proposed. Transfer Order sinh ra khi người duyệt bấm Duyệt. Policy cho phép tự làm chỉ trong phạm vi nhỏ và mặc định chạy Shadow."],
    ["Dữ liệu có ra khỏi Việt Nam không?", "Model chạy ở Azure eastus. Model chỉ nhận câu hỏi và kết quả tool đã lọc, không nhận nguyên bảng. Có thể chuyển sang Data Zone Standard."],
    ["Chi phí AI bao nhiêu?", "Một câu mở khoảng 0,001 đến 0,002 USD; phần lớn câu trả lời bằng rule, 0 token. Có trần ngày và cộng dồn."],
    ["Con số trong demo có phải của Marou?", "Không. Company NWV trên tenant demo, dữ liệu bán do NaviWorld sinh, đơn mua demo, CTKM demo. Phải chạy lại trên dữ liệu thật trước khi nói hiệu quả."],
  ], [2.0, 4.6]),

  h1("8. Giới hạn đã biết và việc còn lại"),
  table(["Điểm", "Hiện trạng", "Việc cần làm"], [
    ["Thẻ đề xuất mặt hàng min-max", "Dòng journal Stock Levels của LS không có bán bình quân nên thẻ ghi 0.", "Lấy bán bình quân từ Replen. Item Quantity khi dòng journal để trống."],
    ["Kiểm số câu trả lời của model", "Báo nhầm khi một dòng nhắc nhiều cửa hàng.", "Chỉ kiểm số đứng ngay sau mã cửa hàng trong cùng mệnh đề."],
    ["Duyệt trong POC", "Nút Duyệt gọi approve bằng Entra app.", "Đăng nhập Entra và gọi BC dưới danh tính người duyệt."],
    ["Brief kho trung tâm", "Trên BC luôn báo không có đơn chờ ship.", "Đọc Transfer Order Released chưa ship."],
    ["CTKM", "Chưa đổi dòng Product Group, Special Group ra mặt hàng; chưa đọc Deal (LSC Offer).", "Thêm API page cho hai liên kết đó."],
    ["UC1", "Chưa cấu hình Sales Hist. Adj. của LS; chưa so với LS Forecast và BC Sales and Inventory Forecast.", "Làm khi có dữ liệu thật."],
    ["UC7 trên BC", "NWV01 chưa có log chiết khấu POS.", "Nạp log POS hoặc sinh dữ liệu demo đúng bảng LS 28."],
    ["UC3 dữ liệu", "Đơn mua demo NaviWorld tạo.", "Thay bằng lịch sử mua thật."],
    ["MCP", "Chưa thử với Foundry hoặc Copilot Studio.", "Cần địa chỉ công khai."],
    ["Bảo vệ trước prompt injection", "Chưa có bộ kiểm thử cho nội dung nằm sẵn trong dữ liệu BC (mô tả hàng, ghi chú).", "Làm bộ câu hỏi chuẩn và bộ kiểm thử injection trước khi rollout."],
  ], [1.5, 2.6, 2.3]),
];

build(
  "Marou Ops Assistant: tài liệu demo nội bộ",
  "Kiến trúc, prompt mẫu theo vai trò, kịch bản demo, mức đáp ứng use case và chi tiết cách xử lý. POC A + D",
  { header: "NaviWorld Vietnam | Marou POC | Nội bộ", footer: "Bản 2.0, 14/09/2026",
    cover: ["Người đọc: team tư vấn và dev NaviWorld chuẩn bị demo nội bộ", "Môi trường: Business Central NWV01, company NWV, LS Central 28.0; app NWV Marou Agent 1.5.1.0", "Ngày: 14/09/2026, Work Date 18/09/2026", "Không gửi khách hàng. Bản gửi Marou là tài liệu 02."] },
  children,
  __dirname + "/08 Marou Ops Assistant - Kien truc, muc dap ung UC va kich ban demo (noi bo).docx",
);
