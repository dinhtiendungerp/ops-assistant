/**
 * Tai lieu 13, ban 3.0: demo script cho buoi trinh dien ngay 17/09/2026.
 * Khac voi speaker note trong slide 12: cho nay la runbook thao tac, ai bam gi, o dau, cho bao lau, khach thay gi, noi cau nao.
 * Ban 3.0 (dem 16 rang sang 17/09): UC2 len dau theo yeu cau cua Dung ("chu yeu la UC2"), them cau hoi tu do ve hang cham luan
 * chuyen noi sang de xuat CTKM, email cho nguoi duyet do AI soan, lich nen tu bao khi Marou post xuat kho. Da QA ca 20 buoc tren
 * BC that bang tools/qa_kich_ban_17_09.py truoc khi viet.
 * Thu tu 20 buoc trung voi cot "Kich ban demo, bam theo thu tu" tren console.
 * Chay: cd docs; node build_13.js
 */
const { p, h1, h2, h3, bullet, table, pageBreak, build, ghiChu, luuY } = require("./lib_brand");

const NGAY = "17/09/2026";

function noiDung() {
  const c = [];

  // ------------------------------------------------------------------ 0
  c.push(h1("0. Mạch của buổi demo"));
  c.push(p("Trọng tâm là UC2 Sức khỏe tồn kho và truy xuất. Ba phần đầu toàn UC2: sáng nay Marou nhìn tồn kho và AI chọn ba việc; một lô "
    + "cận date được AI phân tích và đề xuất chuyển sang cửa hàng bán nhanh; rồi người dùng hỏi tự do (hàng nào chậm luân chuyển, nên chạy "
    + "CTKM gì), truy xuất một lô và quét bất thường. Sau đó mới nối sang UC5 (cửa hàng bán lẻ hết hàng, LS tính, AI đề xuất đặt mua từ Marou), "
    + "UC1 (dự báo và khuyến mãi), và vòng liên công ty khép lại khi hàng về cửa hàng. Bảy phần, 20 bước, mỗi bước là một nút trên cột trái "
    + "của console, tên nút chính là câu sẽ gửi."));
  c.push(...table(["Phần", "Bước", "UC", "Phút"], [
    ["1 · Sáng nay ở Marou: sức khỏe tồn kho", "1, 2", "UC2, AI", "0 đến 4"],
    ["2 · Một lô cận date: AI phân tích, chọn phương án", "3 đến 5", "UC2 nối UC5, AI", "4 đến 10"],
    ["3 · Hỏi tự do trên tồn kho: chậm luân chuyển, CTKM, truy xuất, bất thường", "6 đến 9", "UC2, AI", "10 đến 19"],
    ["4 · Cửa hàng bán lẻ hết hàng: LS tính, AI đề xuất", "10 đến 13", "UC5, AI", "19 đến 27"],
    ["5 · Dự báo, một nhịp", "14, 15", "UC1, UC7 nối UC5", "27 đến 31"],
    ["6 · Hàng về cửa hàng: liên công ty khép vòng", "16 đến 19", "UC2 nhận hàng, A4", "31 đến 38"],
    ["7 · Vận hành", "20", "Chi phí AI", "38 đến 40"],
  ], [4.8, 2.0, 3.0, 2.2]));
  c.push(...ghiChu("Với AI đang bật, câu trả lời dạng dữ liệu (dự báo, vì sao LS, CTKM, truy xuất) có phần lời do model viết: điều quan trọng "
    + "nhất, một hai insight, việc nên làm. Bảng số thu gọn bên dưới, bấm “Dữ liệu code đã tra” để mở. Nhãn ở chân câu trả lời cho biết câu "
    + "đó AI viết, câu mẫu, hay đọc thẳng từ dữ liệu. Mỗi con số model viết đều phải có trong bảng; sai một số là hệ thống giữ nguyên câu "
    + "của rule, nên thỉnh thoảng một câu không có nhãn AI: đó là phép kiểm đã chặn, nói thẳng với khách.",
    "AI kể lại kết quả tra cứu"));
  c.push(...ghiChu("Khi bị cắt giờ, giữ các bước 2, 3, 4, 5, 6, 7, 8, 10, 12, 16, 18. Đó là UC2 trọn vẹn (AI tóm tắt, AI chọn phương án cho "
    + "lô cận date, người duyệt, câu hỏi tự do, truy xuất) cộng một vòng UC5 và liên công ty ngắn.",
    "Bản 20 phút"));

  // ------------------------------------------------------------------ 1
  c.push(pageBreak());
  c.push(h1("1. Đã tạo sẵn gì, đã dọn gì"));
  c.push(p("Đêm 16/09 tôi dựng sẵn trạng thái dưới đây trên Business Central NWV01, chạy thử cả 20 bước trên chính dữ liệu này, rồi dọn mọi "
    + "chứng từ do lần chạy thử sinh ra. Không phải làm lại gì trước buổi họp, chỉ kiểm theo mục 2."));
  c.push(...table(["Đã có sẵn", "Ở đâu", "Dùng cho bước"], [
    ["Bộ dữ liệu tính theo ngày làm việc 17/09/2026: Inventory Health, dự báo, scorecard, LS Replenishment, cả hai company", "NWV-MAROU và NWV-DAKAO", "Tất cả"],
    ["Lô Choco pillar L260829-33310-SD tại S0010: 470 cái, 26 ngày nữa hết hạn, bán không kịp; S0001 bán nhanh hơn", "Inventory Health NWV-MAROU", "3 đến 5"],
    ["Ice cream strawberry: 109 ngày không bán ở S0001, S0002, S0013 và kho; ba CTKM đang chạy không có mặt hàng này", "Inventory Health và Periodic Discount NWV-DAKAO", "6, 7"],
    ["Lô Choco nuts L260906-33323C: Marou xuất 81 cái theo HO106202 sang S0001, hạn 22/04/2027", "Item Ledger Entry NWV-MAROU", "8"],
    ["LS ở Dakao đề xuất 12 Ice cream cho S0002 (min-max 8/20), 7 Croissant chocolate cho S0002 (hết hàng quá nửa cửa sổ tính), 2 Choco nuts cho S0001", "Journal MAROU-PO của NWV-DAKAO", "10, 11, 13"],
    ["Bốn CTKM và bốn Planned Event của LS: Choco bowl giảm 15% ngày 23 đến 25/09 có nhu cầu cho S0001 và S0010, cố ý thiếu S0002 và S0005; dự báo Holt-Winters 28 ngày tới đã ghi vào Retail Forecast Entry", "LS Forecast Entry, Periodic Discount, Planned Event", "14, 15"],
    ["Đơn mua HO106202: 82 Choco nuts từ Marou giao S0001; Marou đã post xuất kho phiếu 102045 ngày 17/09", "NWV-DAKAO và NWV-MAROU", "16, 17"],
    ["Đơn mua HO106200: 1 Blueberry muffin giao S0005, Marou xuất kho phiếu 102044 ngày 16/09, chưa post nhận", "NWV-DAKAO", "16, 18"],
    ["Đơn mua HO106203: 5 Choco bowl giao S0010, đã sang Marou thành Sales Order S90016, kho xuất và lô đã gán sẵn, CHƯA post xuất kho", "NWV-MAROU", "Để bạn tự post trong BC, xem mục 3 bước 19"],
  ], [6.4, 3.4, 2.2]));
  c.push(h2("Đã dọn"));
  c.push(...table(["Đã xoá hoặc đóng", "Vì sao"], [
    ["Đề xuất huỷ Croissant plain ở Marou và đề xuất đặt mua Ice cream ở Dakao từ lần bạn chạy thử tối 16/09", "Để bước 4 và bước 10 ghi đề xuất mới, không bị báo “đã có đề xuất”."],
    ["Transfer Order HO1039 và đề xuất chuyển Choco pillar của lần QA", "Bước 5 sẽ tạo lại đúng trước mặt khách."],
    ["Đơn thử HO106204 (10 Choco pillar, S0005) và HO106205 (12 Ice cream, S0002): đã xuất kho và đã post nhận (phiếu 107111, 107112), đề xuất liên quan đã xoá", "Hai đơn dùng để kiểm lịch nền báo xuất kho và nút Marou xuất kho. Đóng lại để bước 16 chỉ còn HO106202 và HO106200."],
    ["Đề xuất post nhận HO106200 sinh ra khi QA bước 16", "Bước 16 sẽ ghi lại đúng lúc bấm."],
  ], [6.0, 6.0]));
  c.push(...luuY("Lịch quét nền 07:30 (quét sáng UC2, nhắc post 08:00) đang TẠM DỪNG bằng khoá tam_dung trong runs/lich-nhac.json. Riêng việc "
    + "đọc phiếu giao hàng liên công ty mỗi phút vẫn chạy, vì nó chỉ báo, không ghi gì. Sau demo xoá khoá tam_dung là lịch sáng chạy lại."));

  // ------------------------------------------------------------------ 2
  c.push(pageBreak());
  c.push(h1("2. Trước buổi demo: 15 phút kiểm"));
  c.push(...table(["Việc", "Cách làm", "Dấu hiệu đã xong"], [
    ["Chạy máy chủ trợ lý", "Trong thư mục python: python -m uvicorn assistant.channels.web:app --port 8188 --reload", "Mở http://127.0.0.1:8188 thấy màn hình chào, tab trình duyệt có icon linh vật; đợi khoảng 1 phút để máy chủ đọc trước các bảng nặng của hai company"],
    ["Bấm Reset MỘT lần lúc bắt đầu, rồi thôi", "Khay Điều khiển demo ở góc dưới phải, nút Reset", "Hộp thư mọi vai về màn hình chào. Sau đó không bấm Reset nữa, không bấm +24 giờ"],
    ["Nguồn dữ liệu là Business Central", "Dải ngay dưới thanh tiêu đề, nút Business Central đang tô", "Dải xanh ghi Đang đọc Business Central NWV01"],
    ["Bật AI", "Vai Dũng (Quản trị), tab Cài đặt AI", "Ô trạng thái ghi AI đang bật; trần ngày còn ít nhất 1 USD"],
    ["Cột Theo dõi xử lý sạch", "Vai Hùng, xem cột phải ở cả hai company", "Marou: chưa có đề xuất nào. Dakao: bốn dòng Executed (HO106200, HO106201, HO106202, phiếu nhận 107110)"],
    ["Mở sẵn Business Central", "Một tab trình duyệt riêng, đăng nhập NWV01, company NWV-MAROU", "Bấm link trong thẻ là mở được; muốn tự post xuất kho HO106203 thì mở sẵn Sales Order S90016"],
  ], [2.6, 5.2, 4.2]));
  c.push(h2("Người dùng demo"));
  c.push(...table(["Đăng nhập", "Vai", "Đơn vị", "Bước"], [
    ["trang.sc", "Supply Chain", "Cả hai", "1 đến 4, 6 đến 9, 11, 13 đến 15"],
    ["hung.dieuphoi", "Điều phối kho", "Cả hai", "5, 12, 16, 18, 19"],
    ["minh.s0002", "Quản lý Cửa hàng Hà Nội (S0002)", "Dakao", "10, và xem hộp thư sau bước 19"],
    ["lan.s0001", "Quản lý Cửa hàng Quận 1 (S0001)", "Dakao", "17"],
    ["dung.admin", "Quản trị", "Cả hai", "20"],
  ], [2.2, 4.0, 2.0, 3.8]));
  c.push(...ghiChu("Bấm nút kịch bản là console tự đổi vai và đổi company cho đúng bước, rồi điền câu và gửi; tên nút chính là câu gửi đi, dòng "
    + "nhỏ dưới tên là mạch chuyện. Ô hướng dẫn hiện ngay dưới nút vừa bấm. Các bước vẽ nét đứt là bước bấm trên thẻ trong hộp thư, "
    + "console chỉ đổi vai và nói bấm gì. Bước gọi vòng (16, 19) báo đã gửi tin cho những ai, vì tin đi sang hộp thư người khác.",
    "Cách dùng cột Kịch bản demo"));

  // ------------------------------------------------------------------ 3
  c.push(pageBreak());
  c.push(h1("3. Hai mươi bước"));
  c.push(p("Mỗi bước ba cột: bấm gì, khách thấy gì, nói gì. Cột khách thấy gì là dấu hiệu bước đã xong, đừng bấm tiếp khi chưa thấy. Thời "
    + "gian ghi trong từng bước là số đo khi chạy thử đêm 16/09 trên dữ liệu thật."));

  const buoc = (so, ten, vai, bam, thay, noi, luuYs) => {
    c.push(h2(`Bước ${so} · ${ten}`));
    c.push(p(`Vai: ${vai}`));
    c.push(...table(["Bấm gì", "Khách thấy gì"], [[bam, thay]], [5.4, 6.6]));
    c.push(h3("Nói gì"));
    noi.forEach((x) => c.push(bullet(x)));
    if (luuYs) c.push(...luuY(luuYs.join(" ")));
  };

  c.push(h2("Phần 1 · Sáng nay ở Marou: sức khỏe tồn kho"));
  buoc(1, "Sức khỏe tồn kho: bốn con số", "trang.sc · Marou",
    "Nút 1. Console mở tab Sức khỏe tồn kho.",
    "Bốn con số lớn ở hàng trên, bảng dòng ở dưới, thẻ Ngày làm việc 17/09/2026. 166 dòng, 38% giá trị tồn nằm ở bốn tầng xấu. Bấm một tầng để lọc.",
    ["Bốn con số này do lớp tính toán trong Business Central chạy, trợ lý chỉ đọc lại. Không có dịch vụ ngoài nào phải chạy thì số mới hiện ra.",
     "Sáu tầng: quá hạn, cận date, rủi ro đứt hàng, chậm luân chuyển, tồn thừa, bình thường. Rủi ro đứt hàng ở bản này lấy từ LS Replenishment.",
     "Số liệu là bộ mô phỏng NaviWorld dựng trên danh mục thật của Marou. Nói câu này một lần."]);
  buoc(2, "Brief sáng nay do AI viết", "trang.sc · Marou",
    "Nút 2. Console bấm Brief sáng nay.",
    "Sau khoảng 30 giây: thẻ Ba việc quan trọng nhất sáng nay, dòng Người soạn ghi AI (gpt-4.1-mini), rồi các thẻ lô hết hạn, CTKM sắp tới, đơn mua quá hạn.",
    ["Trợ lý đọc bảng kết quả, chọn ba việc trong danh sách code đưa, và nói vì sao chọn. Mỗi việc có link mở sổ kho trong Business Central.",
     "Mọi chữ số model viết đều bị đối chiếu với dữ liệu; sai một chỗ là bỏ cả đoạn và thay bằng câu mẫu, thẻ ghi rõ lý do. Đó là điểm bán, không phải lỗi.",
     "Bản này cũng tự chạy lúc 07:30 và gửi email, hôm nay tạm dừng để giữ dữ liệu cho buổi họp."],
    ["Phần lớn thời gian là đọc Business Central. Nói trước để người xem không tưởng máy treo."]);

  c.push(h2("Phần 2 · Một lô cận date: AI phân tích, chọn phương án"));
  buoc(3, "Lô nào sắp hết hạn?", "trang.sc · Marou",
    "Nút 3.",
    "Khoảng 5 giây: 36 lô cận date, chia theo địa điểm; 5 thẻ lô giá trị lớn nhất. Thẻ Choco pillar S0010: 470 cái, 26 ngày, bán không kịp; hai nút Đề xuất giảm giá và Phương án xử lý.",
    ["Câu này trợ lý đọc thẳng bảng. Điều phối thấy toàn hệ thống; quản lý cửa hàng hỏi cùng câu chỉ thấy cửa hàng mình.",
     "Chọn Choco pillar để đi tiếp: 470 cái mà 26 ngày nữa hết hạn, tại chỗ bán không kịp."]);
  buoc(4, "Phương án xử lý cho Choco pillar ở S0010", "trang.sc · Marou",
    "Nút 4 gửi câu “phương án xử lý cho Choco pillar ở S0010” (cùng kết quả với nút Phương án xử lý trên thẻ lô). Trên thẻ trả về, bấm nút Ghi đề xuất: Chuyển.",
    "Khoảng 5 giây: bảng năm phương án kèm giá trị cứu được hoặc mất, lời khuyên của model (chuyển 187 sang S0001, không còn phần dư). Sau khi ghi (khoảng 15 giây): câu đã ghi đề xuất, thẻ Email cho người duyệt với hai đoạn AI viết, kênh SMTP đã gửi.",
    ["Code tính năm phương án: giữ, chuyển, chuyển kèm giảm giá, giảm giá, huỷ. Khả năng nhận của từng cửa hàng bằng bán bình quân nhân ngày còn lại trừ tồn họ đang có.",
     "Model chọn một và nói vì sao. Khoá phương án phải nằm trong bảng, chữ số phải có trong dữ liệu, không được thêm đơn vị tiền, không được chọn giữ khi giữ vẫn còn dư. Vi phạm là về câu mẫu.",
     "Đây là UC2 nối sang UC5: hàng cận date đi về nơi bán nhanh, không phải huỷ.",
     "Người duyệt được gọi hai đường: thẻ trong chat cho ai đang mở trợ lý, email cho ai không mở. Code điền bảng số liệu và link BC; AI chỉ viết đoạn mở đầu và đoạn kết."]);
  buoc(5, "Hùng duyệt chuyển hàng", "hung.dieuphoi · Marou",
    "Nút 5 đổi sang Hùng. Bấm Duyệt chuyển hàng trên thẻ đề xuất Choco pillar S0010 sang S0001.",
    "Khoảng 5 giây: Đã duyệt, Transfer Order HO10xx tạo dưới tên Hùng, trạng thái Open; cột phải Transfer Order có dòng mới.",
    ["Đề xuất ghi vào một bảng riêng trong Business Central, trạng thái luôn vào ở Proposed. Không có đường tắt cho trợ lý ghi thẳng chứng từ.",
     "Chứng từ mang số đề xuất, kiểm toán truy ngược được từ chứng từ về đề xuất và về dòng dữ liệu gốc.",
     "Hai cửa hàng chưa có tuyến vận chuyển qua kho trung chuyển nên Business Central tạo lệnh chuyển thẳng. Có Transfer Route thì BC tự điền kho trung chuyển."]);

  c.push(h2("Phần 3 · Hỏi tự do trên tồn kho: chậm luân chuyển, CTKM, truy xuất, bất thường"));
  buoc(6, "Mặt hàng nào chậm luân chuyển ở các cửa hàng?", "trang.sc · Dakao",
    "Nút 6. Có thể mời khách gõ câu của họ thay cho câu trên nút.",
    "Khoảng 10 đến 20 giây: AI liệt kê Ice cream strawberry ở S0001, S0002, S0013, mỗi cửa hàng một dòng: tồn, giá trị, 109 ngày không bán. Thẻ Kế hoạch tôi dựng từ dữ liệu có nút xem từng bước đã tra.",
    ["Không có kịch bản viết sẵn cho câu này. Model tự chọn tool: đọc bảng sức khỏe tồn kho xếp theo số ngày tồn đủ bán và số ngày không bán, không chỉ nhìn tầng Chậm luân chuyển.",
     "Bấm Xem bước tôi đã tra để khách thấy model gọi tool gì với tham số gì. Mỗi con số trong câu trả lời đã được code đối chiếu với kết quả tool."],
    ["Câu trả lời đổi theo cách model đọc dữ liệu, không học thuộc. Nếu thẻ có dòng Kiểm tra số thì đọc to: đó là code bắt model viết số không có trong dữ liệu."]);
  buoc(7, "Đề xuất CTKM để bán các mặt hàng này", "trang.sc · Dakao",
    "Nút 7, trong CÙNG đoạn chat với bước 6.",
    "Khoảng 30 giây: đề xuất cho Ice cream strawberry (giảm giá, combo hoặc đưa ra khu trưng bày ở cửa hàng nào, vì sao), rồi ghi chú ba CTKM đang chạy không có mặt hàng này. Không có mức giảm phần trăm.",
    ["Câu nối tiếp: trợ lý đưa vài tin gần nhất của đoạn chat cho model để hiểu “các mặt hàng này”. Model đọc lại tồn kho và CTKM của LS, không nhớ số từ câu trước.",
     "Mức giảm bao nhiêu phần trăm là quy tắc của Marou, chưa có. Trợ lý nói rõ người phụ trách chốt, không bịa. Khi Marou có chính sách giá, đưa vào làm dữ liệu cho model."],
    ["Bước này gọi model nhiều lượt nhất (khoảng 13 nghìn token). Nói trước câu dẫn trong lúc chờ."]);
  buoc(8, "Truy xuất lô L260906-33323C", "trang.sc · Marou",
    "Nút 8. Console đổi về Marou.",
    "Khoảng 6 giây: AI kể lại hành trình lô Choco nuts: nhập 110 về W0003, 81 đã xuất, còn 29, hạn 22/04/2027, thu hồi lấy lại ở đâu; bảng Item Ledger Entry thu gọn bên dưới.",
    ["Đây là phần traceability của UC2: một lô có vấn đề thì biết ngay nó nằm ở những địa điểm nào và còn bao nhiêu.",
     "81 cái này đi sang Cửa hàng Quận 1 theo đơn liên công ty HO106202; phần 6 sẽ thấy cửa hàng được báo."],
    ["Đừng dùng lô L260908-33110B: lô đó đã quá hạn, bị chọn trước khi sửa quy tắc FEFO."]);
  buoc(9, "Có gì bất thường trong 28 ngày qua không?", "trang.sc · Dakao",
    "Nút 9.",
    "Khoảng 20 giây: AI ưu tiên ba tín hiệu ở S0001 (nhận hàng hạn quá ngắn, lặp 6 đến 7 lần) và nói vì sao; danh sách 16 tín hiệu thu gọn bên dưới.",
    ["Năm tín hiệu code quét: bán sau hạn, nhận hàng hạn ngắn bất thường, huỷ tăng gấp đôi, tồn không bán, hết hàng lặp lại. Model chọn tối đa ba và giải thích; mã tín hiệu phải nằm trong danh sách.",
     "Lệch kiểm kê chưa đo được vì bộ dữ liệu không có phiếu kiểm kê. Nói thẳng chỗ này."]);

  c.push(h2("Phần 4 · Cửa hàng bán lẻ hết hàng: LS tính, AI đề xuất"));
  buoc(10, "Sắp hết Ice cream ở cửa hàng tôi", "minh.s0002 · Dakao",
    "Nút 10. Console đổi sang Minh và gửi câu.",
    "Khoảng 20 giây: Ice cream tại S0002 còn 8, đủ 5,5 ngày; theo LS Replenishment đề xuất đặt mua 12 từ MAROU giao thẳng tới S0002, đang xin điều phối duyệt.",
    ["Cửa hàng chỉ nói một câu tự nhiên. Trợ lý nhận ra mặt hàng và cửa hàng của người hỏi, đọc con số LS đã tính, ghi đề xuất vào Business Central và gửi người duyệt.",
     "Trợ lý không tự tính số. 12 là số của LS Replenishment, kiểu min-max: điểm đặt lại 8, mức tối đa 20.",
     "Dakao là bán lẻ, không có kho trung tâm: đề xuất là đặt mua từ Marou, giao thẳng cửa hàng."],
    ["Bước này ghi thật một đề xuất vào Business Central. Bấm lần hai thì trợ lý nói đã có đề xuất, không ghi thêm."]);
  buoc(11, "Vì sao LS đề xuất Ice cream cho S0002?", "trang.sc · Dakao",
    "Nút 11.",
    "Khoảng 13 giây: AI viết vài câu: Stock Levels, đưa lên mức tối đa 20, tồn khả dụng 8 nên mua 12, quyết định Brought to Maximum Inventory; bảng nhật ký tính thu gọn bên dưới.",
    ["Từng bước là nhật ký tính của LS Replenishment, trợ lý không tính lại. Ai cũng đối chiếu được bằng link.",
     "Tham số nằm trên Item Card của LS, Marou tự sửa, không sửa code."]);
  buoc(12, "Hùng duyệt đặt mua, gửi đơn sang Marou", "hung.dieuphoi · Dakao",
    "Nút 12 đổi sang Hùng. Thẻ Đề xuất đặt mua Ice cream: bấm Duyệt đặt mua. Thẻ Đã tạo Purchase Order hiện nút Gửi đơn sang Marou, bấm tiếp.",
    "Khoảng 6 giây: Purchase Order HO1062xx Open. Sau khi gửi (2 giây): đơn Released, bên Marou tự sinh Sales Order.",
    ["Gửi đơn sang Marou là Intercompany chuẩn của Business Central: đơn mua bên Dakao thành đơn bán bên Marou, không nhập lại. Trợ lý không tự bấm nút này vì gửi kéo theo Release."]);
  buoc(13, "Tổng hợp những đề xuất bổ sung bất thường", "trang.sc · Dakao",
    "Nút 13.",
    "Khoảng 13 giây: danh sách đề xuất LS có dấu hiệu lạ, mỗi cửa hàng một dòng, nói vì sao (hết hàng quá nửa cửa sổ tính, không có bán bình quân, tồn bằng 0). Nhãn AI viết.",
    ["Nhóm Khám phá và phân tích insight. Không ai viết sẵn câu trả lời: model gọi tool đọc toàn bộ đề xuất của LS, đọc các cờ do code tính, chọn dòng đáng xem và giải thích.",
     "Croissant chocolate lộ ra ở đây: bánh tươi huỷ cuối ngày nên tồn về 0 mỗi tối, LS đếm là hết hàng. Đó là cách ghi Out of Stock cần xem lại."],
    ["Câu trả lời đổi theo dữ liệu. Nếu model chọn dòng khác thì đọc lý do nó nêu."]);

  c.push(h2("Phần 5 · Dự báo, một nhịp"));
  buoc(14, "Dự báo Choco bowl ở S0010 sai bao nhiêu?", "trang.sc · Dakao",
    "Nút 14. Nếu khách hỏi WAPE, Bias là gì: mở tab Dự báo, phần Cách đọc ngay dưới tiêu đề.",
    "Khoảng 10 giây: AI nói phương pháp sai ít nhất (trung bình cùng thứ 8 tuần, 26,2%), xu hướng dự báo thấp hơn thực tế, và việc nên làm; bảng ba phương pháp, dự báo 7 ngày tới và sự kiện khuyến mãi thu gọn bên dưới.",
    ["Dự báo không nằm ở bảng riêng của NaviWorld. Nó ghi vào Retail Forecast Entry của LS, nên LS Replenishment dùng được ngay.",
     "Holt-Winters là thống kê chuỗi thời gian, chưa phải AI. Nói thẳng. AI ở đây là phần kể lại kết quả."]);
  buoc(15, "CTKM nào đang chạy và sắp tới?", "trang.sc · Dakao",
    "Nút 15.",
    "AI viết vài câu: 3 đang chạy, 2 sắp tới, 2 CTKM thiếu nhu cầu trong LS; Choco bowl giảm 15% có Planned Event cho S0001, S0010 nhưng S0002, S0005 chưa có.",
    ["Trợ lý đọc Periodic Discount của LS và soi xem LS đã cộng nhu cầu khuyến mãi cho cửa hàng nào. Thiếu thì nói rõ: cửa hàng đó sẽ thiếu hàng đúng ngày khuyến mãi.",
     "Lỗ hổng này tôi cố ý để lại trong dữ liệu để thấy trợ lý bắt được."]);

  c.push(h2("Phần 6 · Hàng về cửa hàng: liên công ty khép vòng"));
  buoc(16, "Kiểm hàng Marou đã xuất kho", "hung.dieuphoi · Dakao",
    "Nút 16. Console gọi vòng kiểm đơn liên công ty và báo đã gửi tin cho những ai.",
    "Khoảng 10 giây: thẻ Marou đã xuất kho đơn HO106202 (82 Choco nuts, giao Cửa hàng Quận 1); dòng đơn HO106200 xuất từ 16/09 chưa post nhận kèm thẻ Cho trợ lý post nhận hàng; dòng đã gửi email. Console: đã gửi tin cho Hùng, Lan, Trang, Tuấn.",
    ["Bên Marou không có gì tự động, người kho post xuất kho như mọi ngày. Bên Dakao, trợ lý đọc sang company bên kia và nối hai chứng từ: phiếu giao hàng bên Marou mang số đơn mua bên Dakao ở External Document No.",
     "Xuất kho trong ngày thì chỉ báo. Qua ngày hôm sau vẫn chưa post nhận thì nhắc lại và xin phép post thay. Không ai duyệt thì không có gì được post.",
     "Đây là vấn đề số một trong khảo sát: hàng về mà chứng từ dồn tới cuối tháng, Marou đang thuê người ngoài để post."]);
  buoc(17, "Lan (S0001) nhận tin chuẩn bị nhận hàng", "lan.s0001 · Dakao",
    "Nút 17 đổi sang Lan.",
    "Hộp thư Lan có thẻ Marou đã xuất kho đơn HO106202: Choco nuts 82, giao Cửa hàng Quận 1, link mở đơn mua. Email cùng nội dung đã tới hộp thư.",
    ["Cửa hàng Quận 1 đang hết Choco nuts; giờ họ biết 82 cái đang tới, trước khi xe về.",
     "Thẻ không có số lô: bán lẻ không quản lý lô, trợ lý không đẩy số lô ra cho cửa hàng."]);
  buoc(18, "Hùng duyệt cho trợ lý post nhận HO106200", "hung.dieuphoi · Dakao",
    "Nút 18 đổi sang Hùng. Trên thẻ Cho trợ lý post nhận hàng đơn HO106200, bấm Duyệt cho post nhận hàng.",
    "Thẻ Đã post phiếu nhận 1071xx kèm link mở phiếu nhận trong BC. Mở link: phiếu nhận đã post, đúng mặt hàng và số lượng của đơn mua.",
    ["Đây là loại đề xuất duy nhất mà việc duyệt làm Business Central post thật một chứng từ. Mọi loại khác dừng ở chứng từ nháp.",
     "Quyền post nằm trong permission set riêng, gán tay. Không gán thì bấm Duyệt báo thiếu quyền, không âm thầm bỏ qua.",
     "Số lượng lấy từ đơn mua; số lô, nếu bên mua còn bật quản lý lô, lấy từ sổ kho bên bán, không bịa."]);
  buoc(19, "Marou xuất kho đơn Ice cream vừa gửi", "hung.dieuphoi · Dakao, rồi xem hộp thư Minh",
    "Hai cách. Cách an toàn: nút 19, nút demo post xuất kho thay người kho Marou cho đơn Ice cream ở bước 12. Cách thật: mở Business Central company NWV-MAROU, Sales Order S90016 (đơn HO106203, 5 Choco bowl, lô đã gán sẵn), bấm Post, chọn Ship; rồi đợi tối đa một phút, không bấm gì trên trợ lý.",
    "Nút 19: khoảng 12 giây, console báo đã gửi tin cho Hùng, Minh, Trang; hộp thư Minh có thẻ chuẩn bị nhận 12 Ice cream. Cách thật: trong vòng một phút hộp thư Hà (S0010), Hùng, Trang tự có thẻ Marou đã xuất kho đơn HO106203 và email tới.",
    ["Vòng khép lại: Minh gõ một câu là sắp hết Ice cream; giờ hàng đã rời kho Marou và Minh được báo trước.",
     "Cơ sở để trợ lý biết: mỗi phút nó đọc phiếu giao hàng bên Marou qua web service của app NaviWorld, phiếu nào mang số đơn mua của Dakao mà chưa từng báo thì báo cửa hàng nhận hàng và Supply Chain, gửi email. Chỉ đọc, không ghi gì.",
     "Nút 19 là công cụ demo, không thuộc sản phẩm. Trên hệ thật đó là người kho Marou bấm Post Shipment, như cách thật ở trên."],
    ["Cần đơn Ice cream ở bước 12 đã gửi sang Marou; chưa gửi thì nút xuất đơn mới nhất còn chờ (HO106203) hoặc báo không còn đơn nào. Đơn nào đã xuất trước lúc máy chủ khởi động thì lịch nền không tự báo, nút 16 vẫn báo được."]);

  c.push(h2("Phần 7 · Vận hành"));
  buoc(20, "Chi phí AI đo được", "dung.admin · Marou",
    "Nút 20. Console mở tab Cài đặt AI.",
    "Token vào, token ra, ước tính tiền theo ngày và theo việc; công tắc bật tắt AI; trần chi phí sửa được tại chỗ. Cả lần chạy thử 20 bước đêm 16/09 tốn khoảng 0,08 USD.",
    ["Token là số đếm thật từ nhà cung cấp, tiền là ước tính theo đơn giá công bố; hoá đơn thật mới là số cuối.",
     "Tắt AI thì hệ thống vẫn chạy: số liệu, dashboard, luồng duyệt không đổi, các đoạn văn chuyển sang câu mẫu."]);

  // ------------------------------------------------------------------ 4
  c.push(pageBreak());
  c.push(h1("4. Câu hỏi hay gặp và cách trả lời"));
  c.push(...table(["Khách hỏi", "Trả lời"], [
    ["AI nằm ở đâu, hay chỉ là phần mềm thường?",
     "Trong buổi này AI ở các chỗ: brief chọn việc (bước 2), chọn phương án cho lô cận date và soạn email cho người duyệt (4), trả lời câu hỏi tự do bằng cách tự chọn tool (6, 7, 13), đọc tín hiệu bất thường (9), và kể lại kết quả tra cứu bằng lời (8, 11, 14, 15). Còn lại là LS và Business Central tính, trợ lý đọc và giải thích. Tính năng không thuộc bốn nhóm tóm tắt, tạo sinh, phân tích, tự động hoá thì chúng tôi gọi đúng tên là tính năng ứng dụng."],
    ["Khách gõ một câu không có trong kịch bản thì sao?",
     "Cứ để khách gõ, bước 6 và 7 chính là loại câu đó. Câu nào rule đọc chắc thì trả lời bằng dữ liệu, không tốn model; câu nào rule không giải được thì chuyển cho model tự chọn tool rồi tổng hợp, thẻ có nút xem từng bước đã tra."],
    ["Sao câu cần AI trả lời chậm hơn?",
     "Một câu hỏi tự do là nhiều lượt: model chọn tool, code đọc Business Central, model đọc kết quả rồi viết, code kiểm từng con số. Thường 10 đến 30 giây. Máy chủ đã đọc trước các bảng nặng mỗi 12 phút để phần đọc BC không phải chờ. Nhanh hơn nữa thì tăng hạn mức token mỗi phút trên Azure và hiển thị câu trả lời dần; đó là việc cấu hình khi triển khai."],
    ["Nhìn vào đâu để biết câu này AI viết hay câu soạn sẵn?",
     "Nhãn nhỏ dưới mỗi câu trả lời: “AI viết · gpt-4.1-mini” (đỏ) là model viết và đã qua phép kiểm số; “câu mẫu” (vàng) là AI bị chặn hoặc đang tắt nên code ghép câu; “đọc từ dữ liệu, không gọi model” (xám) là rule đọc thẳng bảng."],
    ["AI có bịa số không?",
     "Mọi chữ số model viết đều bị đối chiếu với dữ liệu code đưa; sai một chỗ là bỏ cả đoạn và thay bằng câu mẫu, hoặc thẻ ghi Kiểm tra số liệt kê đúng số sai."],
    ["Trợ lý có tự ghi vào sổ không?",
     "Chỉ một trường hợp: post phiếu nhận hàng liên công ty, và chỉ sau khi một người bấm Duyệt. Mọi loại khác dừng ở chứng từ nháp."],
    ["Làm sao trợ lý biết Marou vừa post xuất kho?",
     "Mỗi phút nó đọc phiếu giao hàng bên Marou (Sales Shipment Header) qua web service chỉ đọc của app NaviWorld. Phiếu mang số đơn mua của Dakao ở External Document No., do Intercompany điền sẵn. Phiếu nào chưa từng báo thì báo cửa hàng và Supply Chain, gửi email."],
    ["Con số bổ sung là của ai?",
     "Của LS Replenishment, module có sẵn trong LS Central. Trợ lý đọc nhật ký tính của LS và kể lại, có link đối chiếu. Tham số trên Item Card, Marou tự sửa."],
    ["Dự báo dùng AI không?",
     "Chưa. Holt-Winters là thống kê chuỗi thời gian, dùng làm thước đo. Kết quả ghi vào bảng chuẩn của LS nên đổi mô hình sau này không phải đổi luồng."],
    ["Chi phí AI bao nhiêu?",
     "Chạy thử trọn 20 bước tốn khoảng 0,08 USD. Xem tab Cài đặt AI: token là số đếm thật, tiền là ước tính theo đơn giá công bố."],
    ["Tắt AI thì hệ thống còn chạy không?",
     "Còn. Số liệu, dashboard và luồng duyệt không đổi. Các đoạn văn chuyển sang câu mẫu do code ghép."],
    ["Dữ liệu có ra khỏi Việt Nam không?",
     "Môi trường demo dùng Azure OpenAI ở Mỹ. Khi triển khai, extension của NaviWorld tự chọn vùng xử lý, giữ được trong Asia Pacific. Ghi vào phần governance."],
    ["Email báo người duyệt có phải AI viết không?",
     "Có, phần lời. Bảng mặt hàng, lô, tồn, giá trị, tầng, policy và link Business Central do code điền; AI viết đoạn mở đầu và đoạn kết, mỗi chữ số phải có trong dữ liệu."],
    ["Sao email gửi từ một địa chỉ Gmail?",
     "Tenant demo không có license Exchange Online nên POC gửi qua SMTP. Triển khai thật thì thư đi bằng hộp thư của Marou, cấu hình một lần."],
    ["Số liệu trong buổi này là thật chứ?",
     "Không. Bộ dữ liệu mô phỏng do NaviWorld dựng trên danh mục thật của Marou, chạy trên môi trường demo. Nói ít nhất một lần."],
  ], [4.2, 7.8]));

  // ------------------------------------------------------------------ 5
  c.push(h1("5. Sự cố và phương án dự phòng"));
  c.push(...table(["Hiện tượng", "Nguyên nhân thường gặp", "Xử lý tại chỗ"], [
    ["Dải đỏ ghi Không chạy được, Failed to fetch", "Máy chủ đang khởi động lại", "Chờ vài giây, dải tự tắt khi kết nối lại"],
    ["Câu trả lời báo model vượt hạn mức token mỗi phút", "Hai câu hỏi tự do liền nhau vượt 30 nghìn token mỗi phút của Azure", "Nói thêm một câu dẫn rồi bấm lại sau khoảng một phút. Tránh bấm 6, 7, 13 sát nhau"],
    ["Bước 10 trả lời “chuyển từ W0003” thay vì đặt mua từ MAROU", "Đang ở company Marou chứ không phải Dakao", "Nhìn dải nguồn: nút Dakao (bán lẻ) phải đang tô. Bấm lại nút 10"],
    ["Bước 10 báo đã có đề xuất cho dòng này", "Đã bấm bước 10 một lần trước đó", "Chuyển sang bước 12, thẻ đề xuất đã nằm trong hộp thư Hùng"],
    ["Bước 7 trả lời chung chung về CTKM", "Bước 7 gửi ở đoạn chat khác với bước 6", "Bấm lại bước 6 rồi bước 7 liền nhau, không đổi đoạn chat"],
    ["Đoạn văn ghi mẫu có sẵn thay vì AI", "Phép kiểm số đã chặn, hoặc AI đang tắt, hoặc hết trần", "Hành vi đúng. Mở tab Cài đặt AI xem trạng thái rồi giải thích"],
    ["Cột Theo dõi xử lý chưa cập nhật ngay sau khi Duyệt", "Bản chụp làm mới mỗi 8 giây", "Đợi một nhịp, không bấm lại"],
    ["Bước 19 báo không còn đơn nào chờ xuất kho", "Chưa làm bước 12, và đơn HO106203 đã được post tay", "Làm bước 12 trước. Hoặc bỏ bước 19, kể bằng thẻ của bước 16"],
    ["Trợ lý nhắc một đơn cũ không nằm trong kịch bản", "Đơn đó xuất kho từ hôm trước mà chưa ai post nhận", "Đó là đúng việc trợ lý phải làm. Duyệt luôn hoặc nói rõ đây là đơn tồn từ hôm trước"],
  ], [3.4, 4.2, 4.4]));
  c.push(...ghiChu("Phương án cuối cùng nếu mạng hỏng: đổi dải nguồn sang dữ liệu mô phỏng. Bộ mô phỏng neo ngày 18/09 và LS trong đó là công thức "
    + "cũ, nên các bước 11, 13 (nhật ký tính LS) và phần liên công ty không có; các bước UC2 diễn được nhưng số khác. Nói rõ với khách là đang ở bộ mô phỏng.",
    "Mất mạng giữa buổi"));

  return c;
}

(async () => {
  await build(
    "Demo script: một buổi sáng ở Marou và Dakao",
    "Runbook 20 bước cho buổi trình diễn 17/09/2026: dữ liệu đã tạo sẵn, bấm gì, khách thấy gì, nói gì",
    {
      headerLeft: "NaviWorld", headerRight: "Marou • Demo script • Nội bộ",
      footer: `Demo script · Bản 3.0, ${NGAY}`,
      cover: ["Người đọc: người trình diễn và người hỗ trợ kỹ thuật trong buổi họp",
        "Môi trường: Business Central NWV01, hai company NWV-MAROU và NWV-DAKAO, Work Date 17/09/2026",
        `Soạn rạng sáng ${NGAY}, sau khi chạy thử cả 20 bước trên dữ liệu thật. Thứ tự bước trùng với cột Kịch bản demo trên console.`,
        "Đi kèm bộ slide rút gọn; slide có speaker note, tài liệu này có thao tác."],
    },
    noiDung(),
    __dirname + "/13 Marou POC - Demo script (noi bo).docx",
  );
})();
