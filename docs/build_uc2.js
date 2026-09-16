// Hai tai lieu UC2 Inventory Health & Traceability dung chung noi dung, chia theo 4 nhom nang luc AI:
//   noi bo  : "09 UC2 Inventory Health - Tai lieu tinh nang (noi bo).docx"  tai lieu hoa tinh nang, co bang chung, luong,
//             khoang trong, kim chi nam AI. Khong co cau hoi khao sat.
//   gui khach: "10 UC2 Inventory Health - Gioi thieu tinh nang va khao sat (ban gui khach).docx"  tinh nang, muc dap ung,
//             nang luc AI, cau hoi khao sat pain point. Khong co bang chung ky thuat, luong, khoang trong.
//   cd docs; node build_uc2.js
// Anh: docs/anh-uc2 (node tools/chup_uc2.mjs), so do luong: docs/uc2 (python tools/ve_luong_uc2.py).
// Dinh dang theo brand kit Aqua Blue & Warm Sand (lib_brand.js).
const fs = require("fs");
const { p, h1, h2, h3, bullet, num, table, pageBreak, build, img, ghiChu, luuY } = require("./lib_brand");

function kichThuoc(file) {
  const b = fs.readFileSync(file);
  return { w: b.readUInt32BE(16), h: b.readUInt32BE(20) };
}

function taiLieu(ban) {
  const NOI_BO = ban === "noi_bo";
  let soHinh = 0;
  const anh = (file, cap, maxW = 600, maxH = 800) => {
    const f = file.includes("/") ? file : __dirname + "/anh-uc2/" + file;
    if (!fs.existsSync(f)) return [p(`(Thiếu ảnh ${file})`)];
    const { w, h } = kichThuoc(f);
    const r = Math.min(maxW / w, maxH / h);
    return img(f, Math.round(w * r), Math.round(h * r), `Hình ${++soHinh}. ${cap}`);
  };
  const luong = (ten, cap) => anh(__dirname + "/uc2/" + ten, cap, 600, 820);
  const c = [];
  const them = (...x) => c.push(...x.flat());

  // ================================================================== 1. Tom tat / Gioi thieu
  if (NOI_BO) {
    them(h1("1. Tóm tắt"),
      p("Tài liệu tính năng của UC2 Inventory Health & Traceability, use case trục đầu tiên của POC A. RFP của Marou (IT & Digital Transformation, 20/08/2026) ghi đầu ra kỳ vọng: inventory health dashboard, aging and expiry alert, stock-out risk, traceability view. Tài liệu gồm kim chỉ nam phát triển theo bốn nhóm năng lực AI, user story, tính năng và màn hình kèm bằng chứng, luồng giữa các thành phần, khoảng trống và đề xuất."),
      luuY("Số liệu và ảnh lấy từ Business Central NWV01, company NWV, ngày 14/09/2026, Work Date 18/09/2026, trừ ba ảnh luồng đề xuất ở mục 4.5 chụp trên dữ liệu mô phỏng để không ghi đề xuất thật vào BC. Dữ liệu bán và lô là bộ demo NaviWorld sinh; thực tế bán lẻ không quản lý lô.", "Bối cảnh dữ liệu"),
      table(["Chỉ số trên BC ngày 14/09/2026", "Giá trị"], [
        ["Dòng kết quả (mặt hàng x địa điểm x lô)", "167"],
        ["Quá hạn / cận hạn / rủi ro đứt hàng / chậm luân chuyển / tồn thừa / bình thường", "45 / 32 / 47 / 4 / 1 / 38"],
        ["Giá trị tồn kho", "13.370,2"],
        ["Giá trị ở bốn tầng có vấn đề (quá hạn, cận hạn, chậm, thừa)", "5.088,4, tức 38,1%, trên 82 dòng"],
        ["Đối chiếu bản Python độc lập (uc2-reconcile --from al)", "Khớp hoàn toàn sáu tầng"],
        ["Test tự động liên quan UC2", "33 test"],
      ], [4.2, 2.4]),
      p("Phần lớn tính năng UC2 hiện là ứng dụng: AL tính, quy tắc trả lời, luồng duyệt. Model mới được gọi ở hai chỗ. Mục 2 xếp các tính năng AI tiếp theo vào bốn nhóm năng lực, dùng số liệu BC đã tính."));
  } else {
    them(h1("1. Giới thiệu"),
      p("Tài liệu giới thiệu trước với Marou Chocolate các tính năng của use case UC2 Inventory Health & Traceability trong POC mà NaviWorld đề xuất: tính năng nào đã có, mức đáp ứng so với yêu cầu trong RFP, và các năng lực AI mà agent có thể đảm nhận. Phần cuối là tám câu hỏi để chọn tính năng AI làm trước, dựa trên việc đang tốn thời gian và tiền nhất của Marou."),
      ghiChu("RFP ghi đầu ra kỳ vọng của UC2: inventory health dashboard, aging and expiry alert, stock-out risk, traceability view."),
      luuY("Hình ảnh trong tài liệu chụp trên môi trường Business Central demo của NaviWorld có LS Central, với dữ liệu mô phỏng cho 5 cửa hàng, 1 kho trung tâm và 21 mặt hàng. Con số minh họa cách hệ thống hoạt động, không phải số liệu của Marou.", "Bối cảnh dữ liệu demo"),
      table(["Mức đáp ứng", "Ý nghĩa"], [
        ["Có trong POC", "Đã chạy trên môi trường demo, có hình minh họa trong tài liệu này."],
        ["Có trong POC, hoàn thiện khi triển khai", "Luồng đã có; phần tạo chứng từ hoặc mở rộng hoàn thiện theo quy trình của Marou."],
        ["Đề xuất, xác nhận qua khảo sát", "Tính năng AI đề xuất; làm hay không, làm theo cách nào tùy kết quả khảo sát ở mục 5."],
      ], [2.2, 4.4]));
  }

  // ================================================================== 2. Kim chi nam / Nang luc AI
  const NHOM = [
    ["Tóm tắt", "Rút gọn báo cáo, danh sách lô, tin nhắn, email thành vài câu người bận đọc được ngay."],
    ["Tạo sinh nội dung", "Soạn văn bản, chứng từ nháp, thông báo, báo cáo từ dữ liệu có sẵn."],
    ["Khám phá và phân tích insight", "Trả lời câu hỏi tự do, tìm nguyên nhân, phát hiện bất thường, gợi ý hành động dựa trên dữ liệu."],
    ["Tự động hóa", "Tự thực hiện chuỗi bước lặp lại: quét, đề xuất, xin duyệt, tạo chứng từ, nhắc, theo dõi đến khi xong."],
  ];
  // [nhom, ma, ten, lam gi, vi du, trang thai noi bo, muc dap ung gui khach, du lieu can, kiem soat, uu tien]
  const AI = [
    ["Tóm tắt", "S1", "Brief buổi sáng do AI viết", "Đọc bảng sức khỏe tồn kho đã tính, viết 3 việc quan trọng nhất hôm nay theo vai và lý do, thay cho danh sách thẻ dài.",
      "\"Sáng nay S0002 có 13 lô quá hạn, lớn nhất là Choco nuts 285 hộp; kho W0003 có 14 lô cận date nên ưu tiên chuyển bánh sang Quận 1.\"",
      "Có dạng quy tắc: brief liệt kê thẻ theo điểm rủi ro, chưa do model viết", "Có trong POC, hoàn thiện khi triển khai", "NWV Inv. Health Line", "Số trong câu phải truy về dòng kết quả", "Cao"],
    ["Tóm tắt", "S2", "Giải thích lô bằng lời thường", "Tóm Chi tiết lô thành một đoạn: vì sao vào tầng, bán bao nhiêu, còn bao lâu, dự kiến dư bao nhiêu.",
      "\"Lô Carrot cake này bán 1,6 cái mỗi ngày, còn 3 ngày hạn, sẽ dư khoảng 12 cái nếu không xử lý.\"",
      "Có dạng quy tắc: Chi tiết lô hiển thị bảng và cây phân tầng", "Có trong POC, hoàn thiện khi triển khai", "Dòng kết quả, lịch sử bán", "Không tự tính lại, chỉ diễn đạt", "Trung bình"],
    ["Tóm tắt", "S3", "Báo cáo tuần hàng hủy cho quản lý và tài chính", "Tổng hợp giá trị hủy, nhóm hàng và cửa hàng nhiều nhất, nguyên nhân chính, so với tuần trước.",
      "\"Tuần 37 hủy 1.273, tăng 18%; 60% là bánh tươi tại S0002 do nhận hàng dư thứ Sáu.\"",
      "Chưa có", "Đề xuất, xác nhận qua khảo sát", "Item Ledger Entry hủy có mã lý do", "Người nhận chọn phạm vi", "Sau khảo sát"],
    ["Tóm tắt", "S4", "Tóm tắt tin báo sự cố từ cửa hàng", "Gom tin báo hỏng, cận date, hết hàng trong nhóm chat hoặc email thành danh sách sự cố có mặt hàng, lô, cửa hàng.",
      "\"Hôm nay 7 tin báo: 3 kem chảy do tủ S0005, 2 lô bánh cận date S0001, 2 xin thêm Choco nuts.\"",
      "Chưa có", "Đề xuất, xác nhận qua khảo sát", "Kênh chat hoặc email được phép đọc", "Chỉ đọc kênh được cấp quyền", "Sau khảo sát"],
    ["Tạo sinh nội dung", "G1", "Lý do đề xuất viết bằng lời", "Viết lại câu lý do của đề xuất cho người duyệt đọc dễ, giữ nguyên mọi con số.",
      "Thẻ đề xuất hủy có đoạn lý do ngắn gọn.", "Có (model thật, khi bật AI)", "Có trong POC", "Dòng kết quả", "Code giữ nguyên số và mã", "Đã có"],
    ["Tạo sinh nội dung", "G2", "Biên bản và chứng từ hủy nháp", "Khi đề xuất hủy được duyệt: soạn biên bản hủy và chứng từ điều chỉnh kho nháp có lô, số lượng, lý do, người duyệt.",
      "Biên bản hủy 285 hộp Choco nuts lô L260720-33323-SD tại S0002, chứng từ nháp chờ kế toán post.",
      "Chưa có: duyệt hủy chỉ ghi nhận quyết định", "Có trong POC, hoàn thiện khi triển khai", "Đề xuất đã duyệt, mẫu biên bản của Marou", "Kế toán post, AI không post", "Cao"],
    ["Tạo sinh nội dung", "G3", "Chương trình giảm giá xả hàng cận date", "Soạn mô tả chương trình, mức giảm đề xuất, thời gian và hướng dẫn cho nhân viên bán; tạo chương trình ở trạng thái chưa bật.",
      "\"Giảm 30% Carrot cake lô L260915 tại S0002 từ 17h, còn 12 cái.\"",
      "Chưa có: đề xuất giảm giá chưa có mức giảm", "Đề xuất, xác nhận qua khảo sát", "Tốc độ bán, giá vốn, quy định giá của Marou", "Retail Ops bật chương trình", "Trung bình"],
    ["Tạo sinh nội dung", "G4", "Thông báo thu hồi và email khiếu nại", "Soạn thông báo gửi cửa hàng phải rút lô, email gửi nhà cung cấp hoặc nhà máy kèm số lô, số lượng, bằng chứng.",
      "Thông báo rút lô L260908-33170B tại S0001 (12) và S0002 (2).", "Chưa có", "Đề xuất, xác nhận qua khảo sát", "Truy xuất lô", "Người gửi xem trước khi gửi", "Sau khảo sát"],
    ["Khám phá và phân tích insight", "D1", "Hỏi đáp tự do về tồn và lô", "Câu hỏi không có mẫu: agent tự chọn tra tồn, lô, tốc độ bán rồi trả lời kèm số.",
      "\"So sánh tốc độ bán Flavored syrup giữa các cửa hàng, chỗ nào nên giữ ít hàng lại.\"", "Có (model thật, khi bật AI)", "Có trong POC", "API chỉ đọc", "Code kiểm số theo địa điểm, trần chi phí", "Đã có"],
    ["Khám phá và phân tích insight", "D2", "Tìm nguyên nhân gốc của hàng hủy", "Phân tích vì sao một mặt hàng hoặc cửa hàng hủy nhiều: nhận dư, bán chậm, hạn ngắn khi nhận, chuyển trễ.",
      "\"Quận 1 hủy bánh gấp đôi Hà Nội vì nhận hàng thứ Sáu gấp 3 lần mức bán cuối tuần.\"", "Chưa có", "Đề xuất, xác nhận qua khảo sát", "Sổ kho theo lô, lịch nhận hàng, hủy có lý do", "Ghi rõ giả thuyết và số dẫn chứng", "Cao"],
    ["Khám phá và phân tích insight", "D3", "Phát hiện bất thường", "Lô bán sau hạn, hàng nhận về hạn quá ngắn, lệch kiểm kê lớn, cửa hàng hủy tăng đột biến.",
      "\"Lô Tiramisu nhận ngày 10/09 chỉ còn 2 ngày hạn, thấp hơn thường lệ 5 ngày.\"", "Chưa có", "Đề xuất, xác nhận qua khảo sát", "Sổ kho, POS, kiểm kê", "Chỉ cảnh báo, người kết luận", "Trung bình"],
    ["Khám phá và phân tích insight", "D4", "Gợi ý hành động tối ưu cho lô cận date", "So sánh chuyển, giảm giá, dùng nội bộ, hủy theo tốc độ bán còn lại, giá vốn, quy tắc của Marou; chuyển vừa đủ bán trước hạn, phần còn lại giảm giá.",
      "\"Chuyển 9 sang S0001 (bán 3 mỗi ngày), giảm giá 12 còn lại tại S0002.\"", "Một phần: chọn cửa hàng bán nhanh nhất theo quy tắc, đề xuất cả tồn lô", "Có trong POC, hoàn thiện khi triển khai", "Tốc độ bán theo cửa hàng, hạn còn, giá vốn", "Người duyệt theo policy", "Cao"],
    ["Khám phá và phân tích insight", "D5", "Gợi ý ngưỡng cận date theo nhóm hàng", "Học từ lịch sử bán hết và hủy để đề xuất số ngày cận date cho từng nhóm.",
      "\"Kem nên cảnh báo trước 30 ngày thay vì 45; bánh tươi trước 2 ngày.\"", "Chưa có: ngưỡng nhập tay", "Đề xuất, xác nhận qua khảo sát", "Lịch sử 12 tháng", "Đổi ngưỡng luôn qua người duyệt", "Sau khảo sát"],
    ["Tự động hóa", "A1", "Đề xuất xử lý có người duyệt", "Từ thẻ lô: kiểm trùng, xét policy, ghi đề xuất có số lô, đưa thẻ đến đúng người duyệt; duyệt chuyển hàng thì tạo Transfer Order.",
      "Hình 9 và 10.", "Có (luồng ứng dụng, không dùng model)", "Có trong POC", "Bảng đề xuất", "Policy, chống trùng, người duyệt", "Đã có"],
    ["Tự động hóa", "A2", "Tự quét và nhắc mỗi ngày", "Mỗi sáng tự quét kết quả mới, tự soạn đề xuất cho lô vượt ngưỡng, gửi qua kênh người dùng quen dùng, nhắc lại nếu chưa xử lý.",
      "8h sáng quản lý S0002 nhận 3 thẻ trên Teams, 14h nhắc lô chưa xử lý.", "Chưa có: người dùng phải hỏi hoặc bấm Brief", "Đề xuất, xác nhận qua khảo sát", "Job Queue, kênh Teams", "Giới hạn số tin mỗi ngày", "Cao"],
    ["Tự động hóa", "A3", "Luồng hủy khép kín", "Đề xuất, duyệt, chứng từ nháp, kế toán post, xác nhận hoàn tất, cập nhật báo cáo hủy.",
      "", "Chưa có", "Có trong POC, hoàn thiện khi triển khai", "Quy trình hủy của Marou", "Mỗi bước ghi sổ có người", "Cao"],
    ["Tự động hóa", "A4", "Điều phối thu hồi nhiều bước", "Khoanh lô liên quan, báo từng cửa hàng, thu xác nhận đã rút và số lượng, tổng hợp cho QA đến khi đủ.",
      "", "Chưa có: có truy xuất một lô", "Đề xuất, xác nhận qua khảo sát", "Truy xuất lô, danh bạ cửa hàng", "QA mở và đóng vụ thu hồi", "Sau khảo sát"],
  ];

  if (NOI_BO) {
    them(pageBreak(), h1("2. Kim chỉ nam: bốn nhóm năng lực AI"),
      p("Mọi tính năng AI của agent cho UC2 được xếp vào một trong bốn nhóm dưới đây. Tính năng mới phải ghi rõ thuộc nhóm nào và làm thay người dùng việc gì. Tính năng không thuộc nhóm nào là tính năng ứng dụng: vẫn cần, nhưng không tính là AI."),
      table(["Nhóm", "Nghĩa trong UC2"], NHOM, [1.6, 5.0]),
      h2("2.1 Nguyên tắc"),
      num("Số liệu do Business Central tính. AI đọc số đã tính rồi tóm tắt, soạn, phân tích, điều phối; không tự tính lại tầng, tồn hay giá trị.", "numbers2"),
      num("Mỗi đầu ra của AI có nguồn: con số truy về dòng kết quả hoặc chứng từ, có link mở trong BC.", "numbers2"),
      num("Hành động ghi sổ (hủy, chuyển, giảm giá, đổi ngưỡng) luôn qua policy và người duyệt; AI soạn nháp, người quyết.", "numbers2"),
      num("AI bật tắt được, có trần chi phí; tắt AI thì ứng dụng và số liệu vẫn chạy.", "numbers2"),
      num("Model chỉ nhận kết quả tool đã lọc, không nhận nguyên bảng dữ liệu.", "numbers2"),
      h2("2.2 Hiện trạng: AI đang tham gia ở đâu"),
      p("Đọc code ngày 14/09/2026. Trong UC2, model chỉ được gọi ở hai chỗ: planner trả lời câu hỏi mở và viết lại câu lý do của đề xuất, cả hai chỉ khi bật AI. Phân tầng là AL; hỏi hết hạn, truy xuất, brief là quy tắc; đề xuất và duyệt là luồng ứng dụng. Vì vậy người xem thấy sản phẩm giống một ứng dụng."),
      table(["Nhóm", "Đang có bằng model", "Đang có bằng quy tắc hoặc ứng dụng", "Chưa có"], [
        ["Tóm tắt", "", "Brief liệt kê thẻ; câu tóm tắt hết hạn theo địa điểm; Chi tiết lô", "S1 brief do AI viết, S2 giải thích lô bằng lời, S3 báo cáo tuần, S4 tóm tắt tin báo"],
        ["Tạo sinh nội dung", "G1 lý do đề xuất", "Thẻ đề xuất ghép từ dòng kết quả", "G2 biên bản và chứng từ hủy nháp, G3 chương trình xả hàng, G4 thông báo thu hồi"],
        ["Khám phá và phân tích", "D1 hỏi đáp tự do (planner)", "Cây phân tầng, chọn cửa hàng bán nhanh nhất", "D2 nguyên nhân gốc, D3 bất thường, D4 hành động tối ưu, D5 ngưỡng"],
        ["Tự động hóa", "", "A1 đề xuất, policy, chống trùng, duyệt ra Transfer Order", "A2 tự quét và nhắc, A3 luồng hủy khép kín, A4 điều phối thu hồi"],
      ], [1.3, 1.5, 2.1, 1.7]),
      h2("2.3 Danh mục tính năng AI và ưu tiên"),
      luuY("Cột ví dụ ở bản gửi khách là câu minh họa cách agent trả lời, không phải số liệu đã chạy."),
      table(["Mã", "Tính năng", "Làm gì", "Trạng thái", "Dữ liệu cần", "Kiểm soát", "Ưu tiên"],
        AI.map((x) => [x[1], `${x[2]} (${x[0]})`, x[3], x[5], x[7], x[8], x[9]]), [0.4, 1.2, 2.2, 1.1, 1.0, 1.0, 0.6]),
      h2("2.4 Thứ tự đề xuất cho vòng tiếp theo"),
      p("Chọn những việc tận dụng nền đã có và cho người xem thấy AI rõ nhất, không cần dữ liệu mới:"),
      num("S1 brief do AI viết và S2 giải thích lô bằng lời: dữ liệu đã có, cho thấy Tóm tắt ngay trên màn hình đầu tiên.", "numbers3"),
      num("D4 gợi ý hành động tối ưu cho lô cận date: sửa luôn khoảng trống chuyển cả tồn lô, là Phân tích có giá trị tiền.", "numbers3"),
      num("G2 và A3 luồng hủy khép kín với chứng từ nháp: Tạo sinh cộng Tự động hóa, khép vòng từ phát hiện đến sổ sách.", "numbers3"),
      num("A2 tự quét và nhắc qua Teams: chuyển từ người dùng phải hỏi sang agent chủ động.", "numbers3"),
      p("D2, D3, D5, S3, S4, G3, G4, A4 chờ khảo sát vì cần dữ liệu hoặc quy trình mà Marou chưa xác nhận."));
  } else {
    them(pageBreak(), h1("2. Agent AI cho quản lý tồn kho: bốn nhóm năng lực"),
      p("Số tồn, hạn dùng và phân tầng do Business Central và LS Central tính. Agent đọc số đã tính rồi làm thay người dùng những việc tốn công, chia thành bốn nhóm năng lực:"),
      table(["Nhóm năng lực", "Agent làm gì cho người quản lý tồn kho"], NHOM, [1.8, 4.8]),
      ghiChu("Mọi con số có nguồn và mở được chứng từ gốc trong Business Central; mọi hành động ghi sổ đều do người của Marou duyệt; AI bật tắt được và có giới hạn chi phí.", "Nguyên tắc chung"),
      luuY("Cột ví dụ là câu minh họa cách agent trả lời, không phải số liệu thật của Marou."),
      ...["Tóm tắt", "Tạo sinh nội dung", "Khám phá và phân tích insight", "Tự động hóa"].flatMap((nhom, i) => [
        h2(`2.${i + 1} ${nhom}`),
        table(["Tính năng", "Agent làm gì", "Ví dụ", "Mức đáp ứng"],
          AI.filter((x) => x[0] === nhom).map((x) => [x[2], x[3], x[4], x[6]]), [1.3, 2.4, 2.0, 1.1]),
      ]));
  }

  // ================================================================== 3. Nguoi dung va user story
  const US = [
    ["US-01", "Là Supply Chain, tôi muốn thấy tổng giá trị tồn ở các tầng có vấn đề và chia theo sáu tầng, để biết tiền đang nằm ở đâu.", "Mở tab Sức khỏe tồn kho thấy giá trị và tỷ lệ tầng xấu, sáu ô tầng có số dòng và giá trị.", "Đã có", "Có trong POC", "Hình 1", "Ứng dụng"],
    ["US-02", "Là Supply Chain, tôi muốn lọc theo tầng và tìm theo mặt hàng, mã, lô.", "Bấm ô Đã quá hạn chỉ còn dòng quá hạn; gõ số lô chỉ còn dòng của lô đó.", "Đã có", "Có trong POC", "Hình 2", "Ứng dụng"],
    ["US-03", "Là người kiểm tra số liệu, tôi muốn biết vì sao một lô vào tầng đó và số lấy từ đâu.", "Bấm một dòng thấy nguồn số, quy tắc phân tầng dừng ở bậc nào, bán theo ngày cộng tay được.", "Đã có", "Có trong POC", "Hình 3", "Ứng dụng; S2 thêm lời giải thích"],
    ["US-04", "Là người dùng, tôi muốn mở đúng chứng từ gốc trong Business Central từ thẻ của agent.", "Link mở sổ kho của lô trong Business Central, lọc sẵn mặt hàng, kho, lô.", "Đã có", "Có trong POC", "Hình 10, 11", "Ứng dụng"],
    ["US-05", "Là quản trị, tôi muốn chỉnh ngưỡng chung và theo nhóm hàng mà không sửa code.", "Sửa trên trang thiết lập, tính lại thì tầng đổi.", "Đã có", "Có trong POC", "", "Ứng dụng; D5 gợi ý ngưỡng"],
    ["US-06", "Là Supply Chain, tôi muốn biết dữ liệu có đủ để tin kết quả không.", "Màn hình độ phủ ghi tỷ lệ dòng có lô, có hạn dùng, độ dài lịch sử, kết luận Đạt hoặc Cần xem lại.", "Đã có", "Có trong POC", "Hình 4", "Ứng dụng"],
    ["US-07", "Là điều phối, tôi muốn hỏi bằng lời xem hàng nào đã hết hạn, không bị hỏi lại thuộc cửa hàng nào.", "Trả lời số lô, tổng tồn, giá trị, chia theo địa điểm, thẻ lô giá trị lớn nhất.", "Đã có", "Có trong POC", "Hình 6", "Tóm tắt dạng quy tắc"],
    ["US-08", "Là quản lý cửa hàng, tôi muốn biết lô nào tại cửa hàng mình sắp hết hạn.", "Chỉ thấy lô của cửa hàng mình.", "Đã có", "Có trong POC", "Hình 7", "Tóm tắt dạng quy tắc"],
    ["US-09", "Là Supply Chain, tôi muốn bản tóm tắt buổi sáng nêu việc rủi ro nhất kèm nút xử lý.", "Bấm Brief ra các thẻ xếp theo điểm rủi ro; bản AI viết nêu 3 việc quan trọng nhất và lý do.", "Một phần: brief dạng quy tắc", "Có trong POC, hoàn thiện khi triển khai", "Hình 5", "S1 Tóm tắt"],
    ["US-10", "Là quản lý cửa hàng, tôi muốn được báo chủ động khi lô vào cận date qua kênh tôi hay dùng.", "Không cần mở web; thông báo có nút xử lý; nhắc lại nếu chưa xử lý.", "Chưa có", "Đề xuất, xác nhận qua khảo sát", "", "A2 Tự động hóa"],
    ["US-11", "Là Supply Chain, tôi muốn đề xuất hủy lô hết hạn có số lô và người duyệt nhận ngay; duyệt xong có biên bản và chứng từ hủy nháp.", "Đề xuất có số lô; thẻ Duyệt hủy đến người duyệt; duyệt thì có biên bản và chứng từ nháp.", "Một phần: duyệt chỉ ghi nhận", "Có trong POC, hoàn thiện khi triển khai", "Hình 9, 10", "A1, G2, A3"],
    ["US-12", "Là điều phối, tôi muốn chuyển lô cận date sang cửa hàng bán nhanh hơn, với số lượng vừa đủ bán trước hạn.", "Chọn cửa hàng bán nhanh nhất; số lượng không vượt lượng bán được trước hạn; duyệt ra Transfer Order.", "Một phần: đề xuất cả tồn lô", "Có trong POC, hoàn thiện khi triển khai", "Hình 9", "D4 Phân tích"],
    ["US-13", "Là Supply Chain, tôi muốn đề xuất giảm giá lô cận date kèm mức giảm và nội dung chương trình.", "Đề xuất có mức giảm; duyệt thì có chương trình giảm giá ở trạng thái chưa bật trong LS Central.", "Một phần: chưa có mức giảm", "Đề xuất, xác nhận qua khảo sát", "", "G3 Tạo sinh"],
    ["US-14", "Là Supply Chain, tôi muốn chặn mua thêm hàng đang dư tồn.", "Duyệt thì mặt hàng bị chặn mua.", "Một phần: chỉ ghi nhận", "Có trong POC, hoàn thiện khi triển khai", "", "A1 Tự động hóa"],
    ["US-15", "Là người duyệt, tôi không muốn nhận hai đề xuất cho cùng một lô.", "Bấm lần hai báo đã có đề xuất đang chờ.", "Đã có", "Có trong POC", "", "Ứng dụng"],
    ["US-16", "Là quản lý cửa hàng, tôi muốn hỏi tồn một món ở cửa hàng mình và nơi khác.", "Nói cửa hàng mình trước, kể cả khi đã hết.", "Đã có", "Có trong POC", "Hình 8", "Tóm tắt dạng quy tắc"],
    ["US-17", "Là QA, tôi muốn truy xuất một lô: nhập ở đâu, đi đâu, còn ở đâu, thu hồi chỗ nào.", "Gõ số lô ra hành trình và nơi còn tồn; link mở sổ kho của đúng lô.", "Đã có", "Có trong POC", "Hình 11", "Tóm tắt dạng quy tắc; G4, A4"],
    ["US-18", "Là QA, tôi muốn truy ngược từ lô nguyên liệu của nhà máy tới lô thành phẩm và cửa hàng.", "Nối dữ liệu sản xuất hoặc OneTrace.", "Chưa có", "Đề xuất, xác nhận qua khảo sát", "", "D Phân tích"],
    ["US-19", "Là thủ kho, tôi muốn biết xuất lô nào trước (hết hạn trước xuất trước).", "Khi soạn phiếu xuất, gợi ý lô theo hạn dùng.", "Chưa có", "Đề xuất, xác nhận qua khảo sát", "", "D Phân tích"],
    ["US-20", "Là quản lý, tôi muốn hỏi tự do về tồn và lô mà không cần mẫu câu, kể cả câu phân tích.", "Agent tự chọn tra gì và trả lời kèm số có nguồn.", "Đã có khi bật AI", "Có trong POC", "", "D1 Phân tích"],
    ["US-21", "Là quản lý, tôi muốn biết vì sao cửa hàng hoặc mặt hàng hủy nhiều và điều gì bất thường, để sửa từ gốc.", "Agent nêu nguyên nhân có số dẫn chứng; cảnh báo lô bán sau hạn, hàng nhận hạn ngắn.", "Chưa có", "Đề xuất, xác nhận qua khảo sát", "", "D2, D3 Phân tích"],
  ];
  them(pageBreak(), h1("3. Người dùng và user story"), h2("3.1 Vai trò"),
    table(["Vai", NOI_BO ? "Người demo" : "Ví dụ trong demo", "Quan tâm chính trong UC2"], [
      ["Supply Chain", "Trang", "Tiền đang nằm ở hàng xấu bao nhiêu, lô nào cần xử lý trước, ngưỡng có hợp lý không."],
      ["Điều phối kho", "Hùng", "Lô hết hạn ở đâu, chuyển hay hủy, duyệt đề xuất."],
      ["Quản lý cửa hàng", "Lan, Minh, Tuấn, Hà, Thảo", "Lô sắp hết hạn tại quầy, món sắp hết, tồn ở nơi khác để xin chuyển."],
      ["Kho trung tâm", "Kho W0003", "Lô trong kho sắp hết hạn, hàng mua chưa về, xuất lô nào trước."],
      ["QA, an toàn thực phẩm", "", "Truy xuất và thu hồi lô khi có sự cố."],
      ["Kế toán, tài chính", "", "Giá trị hàng hủy, chứng từ hủy, xu hướng theo tháng."],
      ["Quản trị hệ thống", "Dũng", "Ngưỡng, quy định phê duyệt, nhật ký agent, chi phí AI."],
    ], [1.4, 1.6, 3.6]),
    h2("3.2 User story"),
    NOI_BO
      ? p("Trạng thái: Đã có là chạy trên BC NWV01; Một phần là có luồng nhưng chưa ra kết quả nghiệp vụ cuối; Chưa có là việc tiếp theo. Cột nhóm AI trỏ về mã ở mục 2.3.")
      : p("Cột mức đáp ứng theo định nghĩa ở mục 1; cột năng lực AI trỏ về tính năng ở mục 2."),
    table(NOI_BO ? ["Mã", "User story", "Tiêu chí chấp nhận", "Trạng thái", "Bằng chứng", "Nhóm AI"] : ["Mã", "User story", "Tiêu chí chấp nhận", "Mức đáp ứng", "Minh họa", "Năng lực AI"],
      US.map((u) => NOI_BO ? [u[0], u[1], u[2], u[3], u[5], u[6]] : [u[0], u[1], u[2], u[4], u[5], u[6]]),
      [0.5, 1.9, 1.8, 1.0, 0.6, 0.9]));

  // ================================================================== 4. Tinh nang va man hinh
  them(pageBreak(), h1("4. Tính năng và màn hình"),
    h2("4.1 Dashboard Sức khỏe tồn kho"),
    p("Con số lớn là giá trị ở bốn tầng có vấn đề (quá hạn, cận date, chậm luân chuyển, dư tồn); sáu ô tầng bấm được để lọc; bảng xếp theo điểm rủi ro, mỗi dòng là một mặt hàng tại một địa điểm theo lô. " +
      (NOI_BO ? "Nút Đọc lại từ BC bỏ bản nhớ 60 giây để thấy ngay kết quả vừa chạy Run Inventory Health." : "Business Central tính lại hằng đêm hoặc khi người dùng bấm chạy.")),
    anh("uc2-01-tong-quan.png", "Tổng quan: 5.088,4 ở tầng có vấn đề (38,1% của 13.370,2), 82 trên 167 dòng."),
    NOI_BO ? p("Bằng chứng: API inventoryHealthLines trả 167 dòng, tổng hợp theo tầng 45/32/47/4/1/38, trùng số của uc2-reconcile ở mục 4.7.") : [],
    anh("uc2-02-tang-qua-han.png", "Lọc tầng Đã quá hạn: 45 dòng, giá trị 1.273,3."),
    h2("4.2 Chi tiết lô"),
    p("Bấm một dòng để mở ba phần: nguồn số liệu (tồn lấy từ dòng sổ kho nào, tốc độ bán tính trên cơ sở nào, bao nhiêu ngày hết hàng bị loại khỏi phép tính), bậc phân tầng mà lô dừng lại, và lịch sử bán theo ngày để tự cộng đối chiếu."),
    anh("uc2-03-chi-tiet-lo.png", "Chi tiết một lô đã quá hạn.", 600, 900),
    h2("4.3 Độ phủ dữ liệu"),
    p(NOI_BO
      ? "Trả lời câu có nên tin kết quả không. Trên BC ngày 14/09: 115 trên 167 dòng tồn có Lot No. (68,9%, Cần xem lại, vì chỉ 9 mã quản lý lô), 100% dòng tồn có hạn dùng, 70 lô đang còn tồn, lịch sử bán 6 tháng (Cần xem lại), 80 cặp mặt hàng x cửa hàng có bán trong 90 ngày, 100% mặt hàng có Item Category."
      : "Trước khi dùng kết quả, màn hình này cho biết dữ liệu có đủ không: bao nhiêu dòng tồn có số lô và hạn dùng, lịch sử bán dài bao lâu, mặt hàng đã được phân nhóm chưa. Dòng Cần xem lại chỉ ra việc cần bổ sung dữ liệu, ví dụ lịch sử dưới 12 tháng thì chưa bắt được mùa Tết."),
    anh("uc2-04-do-phu-du-lieu.png", "Màn hình Độ phủ dữ liệu.", 600, 900),
    h2("4.4 Hỏi đáp và bản tóm tắt theo vai"),
    p("Người dùng hỏi bằng tiếng Việt thông thường. Mỗi vai chỉ thấy phạm vi của mình: quản lý cửa hàng thấy cửa hàng mình, kho thấy kho, điều phối và Supply Chain thấy toàn hệ thống." +
      (NOI_BO ? " Các câu dưới đây rule nhận ra, không gọi model." : "")),
    anh("uc2-05-brief-supply-chain-dau.png", "Bản tóm tắt buổi sáng của Supply Chain (phần đầu): các dòng rủi ro nhất, mỗi thẻ có nút xử lý theo tầng.", 600, 720),
    anh("uc2-06-het-han-dieu-phoi-dau.png", "Điều phối hỏi hàng đã hết hạn (phần đầu): 45 lô, chia theo địa điểm, sau đó là thẻ các lô giá trị lớn nhất.", 600, 720),
    anh("uc2-07-sap-het-han-cua-hang-dau.png", "Quản lý cửa hàng S0010 hỏi lô sắp hết hạn (phần đầu): chỉ lô của S0010.", 600, 720),
    anh("uc2-09-ton-cua-hang.png", "Quản lý S0001 hỏi tồn Choco nuts: cửa hàng mình đã hết, kho còn 685.", 600, 600),
    h2("4.5 Đề xuất xử lý lô và người duyệt"),
    p("Nút trên thẻ theo tầng: quá hạn thì Đề xuất hủy; cận date thì Đề xuất giảm giá và Chuyển sang cửa hàng bán nhanh; chậm luân chuyển thì Đề xuất giảm giá; dư tồn thì Chặn mua thêm. Agent kiểm đề xuất trùng, áp quy định phê duyệt, ghi đề xuất có số lô vào Business Central và đưa thẻ đến người duyệt." +
      (NOI_BO ? " Ba hình dưới chụp trên dữ liệu mô phỏng." : "")),
    anh("uc2-10-de-xuat-huy-va-chuyen.png", "Đề xuất hủy lô Choco nuts tại S0002 và chuyển lô Carrot cake sang S0001, nơi bán 3 cái mỗi ngày.", 600, 700),
    anh("uc2-11-the-duyet-nguoi-duyet.png", "Thẻ Duyệt hủy đến người duyệt: số lô, tồn, tầng, người đề nghị, quy định áp dụng, link mở lô trong Business Central.", 600, 800),
    NOI_BO ? p("Giới hạn thấy trong hình 9: agent tính được S0001 bán khoảng 9 trong 3 ngày còn hạn nhưng đề xuất chuyển vẫn ghi cả tồn lô. Duyệt WriteOff, Markdown, BlockPurchase chỉ ghi nhận quyết định; chỉ Transfer sinh Transfer Order.") : [],
    h2("4.6 Truy xuất lô"),
    anh("uc2-08-truy-xuat-lo.png", "Truy xuất lô L260908-33170B (Chocolate cake): hạn 13/09 đã quá, nhập 08/09 tại W0003, đã bán 8, còn 12 tại S0001 và 2 tại S0002."));

  if (NOI_BO) {
    them(h2("4.7 Bằng chứng kiểm chứng"),
      table(["Loại", "Nội dung", "Kết quả"], [
        ["Đối chiếu độc lập", "python -m bc_agent.cli uc2-reconcile --from al: đọc bảng AL trên BC, so với bản Python tính offline trên cùng bộ dữ liệu", "Quá hạn 45/45, cận hạn 32/32, rủi ro đứt hàng 47/47, chậm 4/4, thừa 1/1, bình thường 38/38. Trùng khớp hoàn toàn."],
        ["Test phân tầng", "tests/test_uc2.py (9), tests/test_inventory.py (13)", "Lô quá hạn đứng đầu, ngày hết hàng loại khỏi mẫu số, kho không bị coi là không có nhu cầu, ngưỡng đổi thì kết quả đổi, mặt hàng không có lô vẫn được phân tầng."],
        ["Test hội thoại", "test_hoi_het_han (4), test_de_xuat_co_lo (2), test_ma_cua_hang_trong_cau (4), test truy xuất lô, test_goi_y", "Đúng intent, đúng phạm vi vai, đề xuất mang số lô, khóa trùng theo lô."],
        ["Số trên BC", "API inventoryHealthLines, NWV01, 14/09/2026", "167 dòng, giá trị 13.370,2, tầng xấu 5.088,4."],
        ["Link BC", "bc_link: page 38 Item Ledger Entries lọc Item No., Location Code, Lot No.; page 70102 NWV Inventory Health", "Đã mở thử trên BC, lọc đúng lô."],
      ], [1.2, 2.8, 2.6]));

    // ================================================================ 5. Luong
    them(pageBreak(), h1("5. Luồng hoạt động giữa các thành phần"), h2("5.1 Thành phần tham gia"),
      table(["Thành phần", "Nằm ở đâu", "Việc trong UC2"], [
        ["Item Ledger Entry, Lot No. Information", "Bảng chuẩn BC", "Nguồn tồn theo lô, hạn dùng, lịch sử bán và xuất."],
        ["NWV Agent Setup, NWV Category Threshold", "App NWV Marou Agent", "Ngưỡng chung và theo nhóm hàng."],
        ["NWV Demand Calc (70110)", "Codeunit AL", "Nhu cầu bình quân ngày theo mặt hàng x địa điểm, loại ngày hết hàng."],
        ["NWV Inv. Health Calc (70101)", "Codeunit AL", "Gom tồn theo lô, phân tầng, tính điểm rủi ro, ghi bảng kết quả."],
        ["NWV Inv. Health Line", "Bảng AL", "Kết quả: 167 dòng."],
        ["NWV Agent Job Runner", "Job Queue", "Chạy hằng đêm với tham số INVHEALTH."],
        ["API page chỉ đọc", "App NWV Marou Agent", "inventoryHealthLines, nwvItemLedgerEntries, nwvLotNoInformation."],
        ["NWV Agent Proposal, NWV Agent Proposal Mgt.", "Bảng và codeunit AL", "Lưu đề xuất, duyệt; Transfer sinh Transfer Order."],
        ["BCGateway", "python/assistant/gateway.py", "Gọi BC bằng S2S, nhớ kết quả theo bảng (60 giây, sổ kho 15 phút)."],
        ["uc2.py, web.py, index.html", "python/assistant", "Dashboard, Chi tiết lô, độ phủ dữ liệu."],
        ["Rule NLU, skill inventory_health, truy_xuat", "python/assistant", "Hiểu câu hỏi, trả lời, soạn đề xuất."],
        ["Planner, write_rationale", "python/assistant", "Hai chỗ dùng model trong UC2: câu hỏi mở (D1), lý do đề xuất (G1)."],
        ["Policy engine", "python/assistant/policy.py", "P-04 giảm giá, P-05 hủy cần người duyệt; P-06 chuyển lô cận hạn tự làm dưới ngưỡng giá trị (mặc định Shadow); P-07 chặn mua."],
        ["bc_agent/inventory.py", "Python", "Bản đối chiếu độc lập công thức AL."],
      ], [2.0, 1.7, 2.9]),
      h2("5.2 Luồng 1. Business Central tính kết quả"),
      luong("luong-1-tinh-trong-bc.png", "Tính sức khỏe tồn kho trong BC, không có trợ lý tham gia."),
      p("Cây phân tầng dừng ở bậc đầu tiên khớp. Điểm rủi ro 0 đến 100 để sắp thứ tự: quá hạn 100; cận hạn 60 cộng tối đa 40 theo độ gần hạn, giới hạn 65 nếu dự kiến bán hết trước hạn; rủi ro đứt hàng 50 cộng tối đa 40 theo days of cover; chậm luân chuyển theo giá trị tồn; tồn thừa 20 cộng theo giá trị, tối đa 60."),
      table(["Bậc", "Tầng", "Điều kiện"], [
        ["1", "Quá hạn", "Còn dưới 0 ngày đến hạn."],
        ["2", "Cận hạn", "Còn ≤ Near Expiry Days (45, hoặc theo nhóm hàng)."],
        ["3", "Rủi ro đứt hàng", "Có nhu cầu và days of cover < 7."],
        ["4", "Chậm luân chuyển", "Đã từng bán nhưng ≥ 60 ngày không bán, hoặc không có nhu cầu trong cửa sổ."],
        ["5", "Tồn thừa", "Days of cover > 90."],
        ["6", "Bình thường", "Còn lại."],
      ], [0.6, 1.5, 4.5]),
      h2("5.3 Luồng 2. Xem dashboard và Chi tiết lô"),
      luong("luong-2-dashboard.png", "Dashboard chỉ đọc kết quả của BC; bộ nhớ theo bảng giữ màn hình nhanh."),
      h2("5.4 Luồng 3. Hỏi trong chat, đề xuất và duyệt"),
      luong("luong-3-chat-de-xuat-duyet.png", "Từ câu hỏi đến quyết định của người duyệt."),
      h2("5.5 Luồng 4. Truy xuất lô"),
      luong("luong-4-truy-xuat-lo.png", "Truy xuất đọc thẳng Item Ledger Entry của lô."),
      h2("5.6 Chỗ AI sẽ chen vào các luồng"),
      table(["Luồng", "Hiện tại", "Khi thêm tính năng AI ở mục 2.4"], [
        ["1. BC tính", "AL, không có trợ lý", "Giữ nguyên. AI không tính tầng."],
        ["2. Dashboard", "Đọc bảng, hiển thị", "S2: đoạn giải thích lô do model viết từ dòng kết quả và lịch sử bán, số trong câu truy về dòng."],
        ["3. Chat, đề xuất, duyệt", "Rule, thẻ ghép sẵn, duyệt ghi nhận", "S1 brief do model viết; D4 model so sánh phương án chuyển, giảm giá, hủy trên số đã tính; G2 và A3 duyệt hủy sinh biên bản và Item Journal nháp."],
        ["4. Truy xuất", "Rule gom sổ kho", "G4 soạn thông báo thu hồi; A4 theo dõi xác nhận từng cửa hàng."],
        ["Mới: quét hằng ngày", "Không có", "A2: Job Queue xong thì agent tự chọn lô cần báo, gửi Teams, nhắc lại."],
      ], [1.3, 2.0, 3.3]));

    // ================================================================ 6. Khoang trong
    them(pageBreak(), h1("6. Khoảng trống và đề xuất"),
      table(["Khoảng trống", "Hiện trạng", "Đề xuất", "Mã AI", "Ưu tiên"], [
        ["Sản phẩm giống ứng dụng", "Model chỉ ở D1, G1", "Làm theo thứ tự mục 2.4", "S1, S2, D4, G2, A2, A3", "Cao"],
        ["Chứng từ hủy", "Duyệt WriteOff chỉ ghi nhận", "Duyệt thì tạo Item Journal (Negative Adjmt.) nháp có lô, lý do, người duyệt; kế toán post.", "G2, A3", "Cao"],
        ["Số lượng chuyển lô cận hạn", "Đề xuất cả tồn lô", "Giới hạn bằng lượng cửa hàng nhận bán được trước hạn, phần còn lại đề xuất giảm giá.", "D4", "Cao"],
        ["Giảm giá", "Không có mức giảm", "Gợi ý mức giảm theo ngày còn hạn và tốc độ bán; duyệt thì tạo Periodic Discount Disabled.", "G3", "Trung bình"],
        ["Cảnh báo chủ động", "Phải hỏi hoặc bấm Brief", "Gửi sáng mỗi ngày qua Teams, chỉ lô đổi tầng hoặc giá trị lớn.", "A2", "Cao"],
        ["Giá trị tồn", "Số lượng x Unit Cost", "Dùng Value Entry để khớp sổ kế toán.", "", "Trung bình"],
        ["Hạn dùng ở bán lẻ", "Demo quản lý lô tới cửa hàng; thực tế bán lẻ không quản lý lô, chỉ sản xuất có lô", "Xác định hạn dùng hàng ở cửa hàng từ đợt giao của nhà máy; phân tầng cửa hàng theo mặt hàng x địa điểm, không theo lô.", "", "Cao"],
        ["Truy xuất ngược, thu hồi", "Chỉ một lô, không theo dõi rút hàng", "Liên kết lô nguyên liệu, danh sách cửa hàng phải rút, hỏi xác nhận từng cửa hàng.", "G4, A4", "Cần khảo sát"],
        ["Xuất theo hạn dùng", "Không có", "Gợi ý lô khi soạn Transfer Order hoặc phiếu xuất.", "", "Cần khảo sát"],
        ["Ngưỡng theo nhóm", "Bảng có sẵn, chưa có số của Marou", "Học ngưỡng cận hạn từ lịch sử, đưa người duyệt (P-09).", "D5", "Sau khảo sát"],
      ], [1.3, 1.4, 2.4, 0.8, 0.7]));

    // ================================================================ 7. De xuat them
    them(h1("7. KPI, nghiệm thu, giả định"),
      h2("7.1 KPI và baseline"),
      table(["KPI", "Đo từ đâu", "Baseline trên dữ liệu demo"], [
        ["Giá trị tồn ở tầng có vấn đề", "NWV Inv. Health Line", "5.088,4 (38,1%)"],
        ["Giá trị lô đã quá hạn còn tồn", "NWV Inv. Health Line tầng Expired", "1.273,3 trên 45 lô"],
        ["Giá trị hàng hủy mỗi tháng", "Item Ledger Entry Negative Adjmt. có lý do hủy", "Chưa đo: cần mã lý do hủy"],
        ["Số ngày đứt hàng theo cửa hàng", "Nhu cầu và tồn theo ngày", "Có trong kpi.py của trợ lý"],
        ["Thời gian truy xuất một lô", "Đo tay trước và sau", "Cần khảo sát"],
        ["Tỷ lệ đề xuất được duyệt không sửa", "NWV Agent Proposal", "Bắt đầu đo khi dùng thật"],
        ["Tỷ lệ câu trả lời có dùng AI và chi phí", "Sổ chi phí của trợ lý", "Bắt đầu đo khi bật AI"],
      ], [2.0, 2.5, 2.1]),
      h2("7.2 Kịch bản nghiệm thu UC2"),
      num("Đặt Work Date 18/09/2026, chạy Run Inventory Health: bảng NWV Inv. Health Line có 167 dòng.", "numbers"),
      num("Chạy uc2-reconcile --from al: khớp sáu tầng.", "numbers"),
      num("Mở tab Sức khỏe tồn kho: tổng tầng xấu 5.088,4; bấm Đã quá hạn còn 45 dòng.", "numbers"),
      num("Mở Chi tiết một lô, cộng tay bán theo ngày, so với nhu cầu bình quân trên dòng.", "numbers"),
      num("Bấm link Item Ledger Entries trên thẻ: BC mở đúng mặt hàng, kho, lô.", "numbers"),
      num("Vai điều phối hỏi hàng đã hết hạn: 45 lô chia theo địa điểm. Vai quản lý S0010 hỏi lô sắp hết hạn: chỉ lô của S0010.", "numbers"),
      num("Truy xuất lô L260908-33170B: còn 12 tại S0001, 2 tại S0002.", "numbers"),
      num("Đề xuất hủy một lô: đề xuất Proposed có số lô trong BC, người duyệt nhận thẻ; bấm lần hai báo trùng.", "numbers"),
      num("Sửa Near Expiry Days trên NWV Agent Setup rồi chạy lại: số dòng cận hạn đổi.", "numbers"),
      h2("7.3 Giả định và rủi ro"),
      bullet("Kết quả chỉ đúng khi mọi xuất, bán, hủy đều ghi vào BC đúng lô. Bánh tươi hủy cuối ngày không ghi là rủi ro lớn nhất."),
      bullet("Bán lẻ không quản lý lô: phân tầng theo lô chỉ đúng ở phía sản xuất; hạn dùng hàng ở cửa hàng phải suy từ đợt giao."),
      bullet("Giá trị dùng Unit Cost, có thể lệch sổ kế toán."),
      bullet("Dữ liệu demo 6 tháng, chưa có mùa Tết; ngưỡng mặc định chưa phải của Marou."),
      bullet("Tính năng AI phụ thuộc chất lượng dữ liệu nguồn; nếu mã lý do hủy, lịch nhận hàng không có thì D2, S3 chưa làm được."));
  } else {
    // ================================================================ 5. Cau hoi khao sat (ban gui khach)
    // Chi giu cau dat gia: moi cau nham mot tinh nang AI o muc 2. Dung chot ngay 14/09/2026: khong hoi cai gi cung hoi,
    // bo phieu cham diem dau. Marou co hai entity: Marou san xuat (co lo), Dakao ban le (khong quan ly lo); agent lam cho
    // ca hai. Khong hoi cau nao ve POS co lo; khong ghi thong tin entity vao tai lieu.
    them(pageBreak(), h1("5. Câu hỏi khảo sát"),
      p("Tám câu dưới đây, mỗi câu nhắm một tính năng AI ở mục 2. Câu trả lời quyết định có làm tính năng đó không, và agent phải theo quy tắc nào của Marou khi làm. Xin anh chị trả lời bằng lần gần nhất chuyện đó xảy ra, kèm con số ước lượng."),
      table(["#", "Câu hỏi", "Hỏi ai", "Câu trả lời định hình tính năng"], [
        ["1", "Tháng gần nhất, lần hủy hàng có giá trị lớn nhất là mặt hàng nào, ở nhà máy hay ở cửa hàng? Nhìn lại, phải biết từ ngày nào và làm gì thì không phải hủy?", "Supply Chain, quản lý kho nhà máy, quản lý cửa hàng",
          "Agent tự quét và nhắc mỗi sáng (A2): nhắc trước bao nhiêu ngày, nhắc ai. Giá trị lần hủy này là mức để so khi đánh giá POC."],
        ["2", "Khi hàng sắp hết hạn, người xử lý giỏi nhất trong đội anh chị dựa vào những điều gì để chọn chuyển sang nơi bán nhanh hơn, giảm giá, dùng nội bộ hay hủy? Điều nào trong đó hệ thống hiện không biết?", "Điều phối, quản lý cửa hàng",
          "Gợi ý hành động cho hàng cận date (D4): đưa kinh nghiệm của người giỏi nhất thành quy tắc agent dùng cho mọi cửa hàng."],
        ["3", "Mỗi sáng trước khi mở cửa hoặc vào ca, anh chị muốn biết đúng ba điều gì về hàng hóa? Hiện lấy ba điều đó từ đâu, mất bao lâu?", "Quản lý cửa hàng, điều phối, Supply Chain",
          "Bản tóm tắt buổi sáng do AI viết (S1): nội dung, thứ tự ưu tiên và độ dài cho từng vai."],
        ["4", "Câu hỏi nào về tồn kho hoặc hàng hủy mà quản lý hỏi, đội anh chị phải mất hơn nửa ngày mới trả lời được?", "Supply Chain, quản lý",
          "Hỏi đáp tự do và tìm nguyên nhân gốc (D1, D2): những câu hỏi agent phải trả lời được ngay, kèm số có nguồn."],
        ["5", "Chuyện bất thường nào về hàng hóa anh chị từng phát hiện quá muộn: hàng từ nhà máy giao sang cửa hàng đã gần hạn, lô sản xuất có hạn ngắn hơn thường lệ, lệch kiểm kê lớn, một cửa hàng hủy tăng đột biến? Nếu có người canh suốt ngày, anh chị muốn họ canh điều gì?", "QA, kế toán kho, quản lý cửa hàng",
          "Phát hiện bất thường (D3): danh sách tín hiệu agent theo dõi và ngưỡng báo."],
        ["6", "Từ lúc quyết định hủy hàng đến lúc sổ kho đã ghi xong, cần những giấy tờ nào, bao nhiêu người ký, mất mấy ngày? Bước nào hay bị treo?", "Kế toán kho, quản lý cửa hàng",
          "Biên bản và chứng từ hủy nháp, luồng hủy khép kín (G2, A3): mẫu giấy tờ agent soạn và bước agent đẩy việc."],
        ["7", "Nếu sáng mai phải thu hồi một lô sản xuất, anh chị biết lô đó đã giao đến những cửa hàng hoặc khách nào bằng cách nào? Cửa hàng nhận biết hàng cần rút dựa vào thông tin gì, và mất bao lâu để chắc mọi nơi đã rút?", "QA, quản lý kho nhà máy",
          "Thông báo thu hồi và điều phối thu hồi (G4, A4): agent dựa vào thông tin nào để khoanh vùng, làm thay những bước nào, xác nhận từng nơi ra sao."],
        ["8", "Việc gì anh chị sẵn sàng để hệ thống tự làm từ tuần sau mà không cần hỏi? Việc gì không bao giờ? Hạn mức giá trị bao nhiêu?", "Supply Chain, kế toán, QA",
          "Quy định phê duyệt: phạm vi agent được tự làm, phạm vi luôn cần người duyệt."],
      ], [0.3, 2.7, 1.2, 2.4]),
      pageBreak(), h2("Hai điều cần xác nhận về dữ liệu"),
      p("Hai câu này quyết định agent có đủ dữ liệu để làm các tính năng trên hay không."),
      table(["Câu hỏi", "Vì sao cần biết"], [
        ["Hàng tươi thừa cuối ngày ở cửa hàng (bánh, kem) có được ghi hủy vào Business Central không, có ghi lý do không?", "Nếu không ghi, tồn trên hệ thống cao hơn thực tế, cảnh báo cho nhóm hàng này sai và không phân tích được nguyên nhân hủy."],
        ["Khi hàng từ nhà máy giao sang cửa hàng, hạn dùng của từng đợt giao có được ghi lại ở phía cửa hàng không (trên chứng từ nhận hàng, trên nhãn, hay không ghi)?", "Quyết định agent tính được hạn dùng của hàng đang nằm ở cửa hàng, hay chỉ theo dõi hạn dùng tại nhà máy."],
      ], [3.2, 3.4]));
  }
  return c;
}

(async () => {
  await build(
    "UC2 Inventory Health & Traceability: tài liệu tính năng",
    "Kim chỉ nam bốn nhóm năng lực AI, user story, tính năng và bằng chứng, luồng hệ thống, khoảng trống",
    { headerLeft: "NaviWorld", headerRight: "Marou • UC2 Inventory Health • Nội bộ", footer: "UC2 Inventory Health & Traceability · Tài liệu tính năng · Bản 1.1",
      cover: ["Người đọc: team tư vấn, BA và dev NaviWorld", "Môi trường: Business Central NWV01, company NWV, app NWV Marou Agent 1.5.1.0", "Ngày: 14/09/2026, Work Date 18/09/2026", "Bản gửi khách: tài liệu 10."] },
    taiLieu("noi_bo"),
    __dirname + "/09 UC2 Inventory Health - Tai lieu tinh nang (noi bo).docx",
  );
  await build(
    "UC2 Inventory Health & Traceability",
    "Giới thiệu tính năng, mức đáp ứng, năng lực AI của agent và câu hỏi khảo sát",
    { headerLeft: "NaviWorld", headerRight: "Marou • UC2 Inventory Health", footer: "UC2 Inventory Health & Traceability · Bản 1.0, 14/09/2026",
      cover: ["Kính gửi: Marou Chocolate, bộ phận IT & Digital Transformation, Supply Chain, Retail", "Người soạn: NaviWorld Vietnam", "Ngày: 14/09/2026", "Hình ảnh chụp trên môi trường demo với dữ liệu mô phỏng."] },
    taiLieu("gui_khach"),
    __dirname + "/10 UC2 Inventory Health - Gioi thieu tinh nang va khao sat (ban gui khach).docx",
  );
})();
