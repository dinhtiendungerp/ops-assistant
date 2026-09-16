/**
 * Tai lieu 13, ban 2.4: demo script cho buoi trinh dien ngay 17/09/2026.
 * Khac voi speaker note trong slide 12: cho nay la runbook thao tac, ai bam gi, o dau, cho bao lau, khach thay gi, noi cau nao.
 * Ban 2.0 (toi 16/09) di theo MOT cau chuyen: cua hang het hang, LS tinh, AI de xuat, nguoi duyet, don sang Marou, Marou xuat kho,
 * tro ly bao nhan, phieu nhan; xen giua la du bao (UC1) va khuyen mai noi sang LS (UC5). Han dung chi con mot canh.
 * Thu tu 20 buoc trung voi cot "Kich ban demo, bam theo thu tu" tren console.
 * Chay: cd docs; node build_13.js
 */
const { p, h1, h2, h3, bullet, table, pageBreak, build, ghiChu, luuY } = require("./lib_brand");

const NGAY = "16/09/2026";

function noiDung() {
  const c = [];

  // ------------------------------------------------------------------ 0
  c.push(h1("0. Mạch của buổi demo"));
  c.push(p("Trọng tâm là UC2 Sức khỏe tồn kho và truy xuất, xen một nhịp UC5 và một nhịp UC1 để thấy trợ lý nối các UC với nhau. "
    + "Mạch: sáng nay Marou nhìn tồn kho, AI chọn ba việc; một lô cận date được AI phân tích và đề xuất chuyển sang cửa hàng bán nhanh; "
    + "một cửa hàng bán lẻ kêu hết hàng, LS tính, AI đề xuất đặt mua từ Marou; dự báo và khuyến mãi nối sang bổ sung; hàng về cửa hàng "
    + "qua liên công ty, trợ lý báo và xin phép post phiếu nhận; cuối cùng truy xuất lô, bất thường và chi phí. Sáu phần, 18 bước, mỗi "
    + "bước là một nút trên cột trái của console, tên nút chính là câu sẽ gửi."));
  c.push(...table(["Phần", "Bước", "UC", "Phút"], [
    ["1 · Sáng nay ở Marou: sức khỏe tồn kho", "1, 2", "UC2, AI", "0 đến 5"],
    ["2 · Một lô cận date: AI phân tích, chọn phương án", "3 đến 5", "UC2 nối UC5, AI", "5 đến 12"],
    ["3 · Cửa hàng bán lẻ hết hàng: LS tính, AI đề xuất", "6 đến 9", "UC5, AI", "12 đến 21"],
    ["4 · Dự báo, một nhịp", "10, 11", "UC1, UC7 nối UC5", "21 đến 25"],
    ["5 · Hàng về cửa hàng: liên công ty khép vòng", "12 đến 15", "UC2 nhận hàng, A4", "25 đến 33"],
    ["6 · Truy xuất, bất thường, chi phí", "16 đến 18", "UC2, AI", "33 đến 38"],
  ], [4.6, 2.2, 3.0, 2.2]));
  c.push(...ghiChu("Với AI đang bật, mọi câu trả lời dạng dữ liệu (dự báo, vì sao LS, CTKM, đơn quá hạn, nhà cung cấp, lô hết hạn, truy xuất) "
    + "có phần lời do model viết: điều quan trọng nhất, một hai insight, việc nên làm. Bảng số thu gọn bên dưới, bấm “Dữ liệu code đã tra” "
    + "để mở. Nhãn ở chân câu trả lời cho biết câu đó AI viết, câu mẫu, hay đọc thẳng từ dữ liệu. Mỗi con số model viết đều phải có trong "
    + "bảng; sai một số là hệ thống giữ nguyên câu của rule, nên thỉnh thoảng một câu không có nhãn AI: đó là phép kiểm đã chặn, nói thẳng với khách.",
    "AI kể lại kết quả tra cứu"));
  c.push(...ghiChu("Khi bị cắt giờ, giữ các bước 2, 3, 4, 5, 6, 8, 12, 14. Đó là một vòng trọn của UC2: AI tóm tắt, lô cận date được AI "
    + "chọn phương án, người duyệt, cửa hàng kêu hết hàng, đơn sang Marou, hàng về và trợ lý post phiếu nhận sau khi được duyệt.",
    "Bản 15 phút"));

  // ------------------------------------------------------------------ 1
  c.push(pageBreak());
  c.push(h1("1. Đã tạo sẵn gì, đã dọn gì"));
  c.push(p("Tối 16/09 tôi dựng sẵn trạng thái dưới đây trên Business Central NWV01. Không phải làm lại gì trước buổi họp, chỉ kiểm."));
  c.push(...table(["Đã có sẵn", "Ở đâu", "Dùng cho bước"], [
    ["Bộ dữ liệu tính lại theo ngày làm việc 17/09/2026: Inventory Health, dự báo, scorecard, LS Replenishment, cả hai company", "NWV-MAROU và NWV-DAKAO", "Tất cả"],
    ["Lô Choco pillar L260829-33310-SD tại S0010: 470 cái, hạn 13/10, bán không kịp; S0001 bán nhanh hơn", "Inventory Health NWV-MAROU", "3 đến 5"],
    ["LS ở Dakao đề xuất 12 Ice cream cho S0002 (min-max 8/20), 7 Croissant chocolate cho S0002 (42 ngày hết hàng), 2 Choco nuts cho S0001 (tồn 0, 82 đang về)", "Journal MAROU-PO của NWV-DAKAO", "6, 7, 9"],
    ["Bốn CTKM và bốn Planned Event của LS: Choco bowl giảm 15% ngày 23 đến 25/09 có nhu cầu cho S0001 và S0010, cố ý thiếu S0002 và S0005; dự báo Holt-Winters 28 ngày tới đã ghi vào Retail Forecast Entry", "LS Forecast Entry, Periodic Discount, Planned Event", "10, 11"],
    ["Đơn mua HO106202: 82 Choco nuts từ Marou giao S0001. Đã sang Marou thành Sales Order S90015, Marou đã post xuất kho phiếu 102045 đề ngày 17/09", "NWV-DAKAO và NWV-MAROU", "12, 13"],
    ["Đơn mua HO106200: 1 Blueberry muffin giao S0005, Marou xuất kho phiếu 102044 ngày 16/09, chưa post nhận", "NWV-DAKAO", "12, 14"],
    ["Lô Choco nuts L260906-33323C: Marou xuất 81 cái theo HO106202 sang S0001, hạn 22/04/2027, sổ kho ở W0003", "Item Ledger Entry NWV-MAROU", "16"],
  ], [6.4, 3.4, 2.2]));
  c.push(h2("Đã dọn"));
  c.push(...table(["Đã xoá", "Vì sao"], [
    ["19 đề xuất chuyển hàng đã từ chối ở Marou, 7 đề xuất đặt mua đã từ chối ở Dakao", "Tính theo ngày làm việc 18/09, không còn khớp LS. Cột Theo dõi xử lý giờ không còn dòng Rejected."],
    ["13 đề xuất huỷ lô hết hạn ở Dakao", "Sinh ra từ các lần chạy quét sáng khi thử. Mạch demo không dùng luồng huỷ."],
    ["Các đề xuất post nhận hàng còn treo và đề xuất thử tối 16/09", "Trợ lý ghi lại đúng lúc khi bấm Kiểm hàng Marou đã xuất kho ở bước 12."],
    ["Đơn mua HO106199 (1 muffin, tạo trước khi có Intercompany) và hai dòng Item Journal rỗng SL260918", "Rác của các lần thử, không thuộc kịch bản nào."],
  ], [6.0, 6.0]));
  c.push(...luuY("Lịch quét nền 07:30 (quét sáng UC2, nhắc post 08:00) đang TẠM DỪNG bằng khoá tam_dung trong runs/lich-nhac.json. Không tạm "
    + "dừng thì khởi động máy chủ sau 07:30 là nó chạy ngay, ghi tới 10 đề xuất huỷ mỗi company và gửi email trước giờ họp. Sau demo "
    + "xoá khoá đó là lịch chạy lại."));

  // ------------------------------------------------------------------ 2
  c.push(pageBreak());
  c.push(h1("2. Trước buổi demo: 15 phút kiểm"));
  c.push(...table(["Việc", "Cách làm", "Dấu hiệu đã xong"], [
    ["Chạy máy chủ trợ lý", "Trong thư mục python: python -m uvicorn assistant.channels.web:app --port 8188 --reload", "Mở http://127.0.0.1:8188 thấy màn hình chào; đợi khoảng 30 giây để máy chủ làm nóng hai company"],
    ["Bấm Reset MỘT lần lúc bắt đầu, rồi thôi", "Khay Điều khiển demo ở góc dưới phải, nút Reset", "Hộp thư mọi vai về màn hình chào (xoá dấu vết các lần bấm thử tối 16/09). Sau đó không bấm Reset nữa, không bấm +24 giờ trước bước 13"],
    ["Nguồn dữ liệu là Business Central", "Dải ngay dưới thanh tiêu đề, nút Business Central đang tô", "Dải xanh ghi Đang đọc Business Central NWV01"],
    ["Bật AI", "Vai Dũng (Quản trị), tab Cài đặt AI", "Ô trạng thái ghi AI đang bật; trần ngày còn ít nhất 1 USD"],
    ["Cột Theo dõi xử lý sạch", "Vai Hùng, xem cột phải ở cả hai company", "Marou: chưa có đề xuất nào. Dakao: chỉ các dòng Executed của HO106200, HO106201, HO106202 và phiếu nhận 107110"],
    ["Mở sẵn Business Central", "Một tab trình duyệt riêng, đăng nhập NWV01", "Bấm link trong thẻ là mở được, không phải đăng nhập giữa buổi"],
  ], [2.6, 5.2, 4.2]));
  c.push(h2("Người dùng demo"));
  c.push(...table(["Đăng nhập", "Vai", "Đơn vị", "Bước"], [
    ["trang.sc", "Supply Chain", "Cả hai", "1 đến 4, 7, 9 đến 11, 16, 17"],
    ["hung.dieuphoi", "Điều phối kho", "Cả hai", "5, 8, 12, 14, 15"],
    ["minh.s0002", "Quản lý Cửa hàng Hà Nội (S0002)", "Dakao", "6, và xem hộp thư sau bước 15"],
    ["lan.s0001", "Quản lý Cửa hàng Quận 1 (S0001)", "Dakao", "13"],
    ["dung.admin", "Quản trị", "Cả hai", "18"],
  ], [2.2, 4.0, 2.0, 3.8]));
  c.push(...ghiChu("Bấm nút kịch bản là console tự đổi vai và đổi company cho đúng bước, rồi điền câu và gửi; tên nút chính là câu gửi đi, dòng "
    + "nhỏ dưới tên là mạch chuyện. Ô hướng dẫn hiện ngay dưới nút vừa bấm. Các bước vẽ nét đứt là bước bấm trên thẻ trong hộp thư, "
    + "console chỉ đổi vai và nói bấm gì. Bước gọi vòng (12, 15) báo đã gửi tin cho những ai, vì tin đi sang hộp thư người khác.",
    "Cách dùng cột Kịch bản demo"));

  // ------------------------------------------------------------------ 3
  c.push(pageBreak());
  c.push(h1("3. Mười tám bước"));
  c.push(p("Mỗi bước ba cột: bấm gì, khách thấy gì, nói gì. Cột khách thấy gì là dấu hiệu bước đã xong, đừng bấm tiếp khi chưa thấy."));

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
    "Bốn con số lớn ở hàng trên, bảng dòng ở dưới, thẻ Ngày làm việc 17/09/2026. Bấm một tầng để lọc.",
    ["Bốn con số này do lớp tính toán trong Business Central chạy, trợ lý chỉ đọc lại. Không có dịch vụ ngoài nào phải chạy thì số mới hiện ra.",
     "Sáu tầng: quá hạn, cận date, rủi ro đứt hàng, chậm luân chuyển, tồn thừa, bình thường. Rủi ro đứt hàng ở bản này lấy từ LS Replenishment.",
     "Số liệu là bộ mô phỏng NaviWorld dựng trên danh mục thật của Marou. Nói câu này một lần."]);
  buoc(2, "Brief sáng nay do AI viết", "trang.sc · Marou",
    "Nút 2. Console bấm Brief sáng nay.",
    "Sau khoảng 20 giây: thẻ Ba việc quan trọng nhất sáng nay, dòng Người soạn ghi AI (gpt-4.1-mini), rồi các thẻ dòng bên dưới.",
    ["Trợ lý đọc bảng kết quả, chọn ba việc trong danh sách code đưa, và nói vì sao chọn. Mỗi việc có link mở sổ kho trong Business Central.",
     "Mọi chữ số model viết đều bị đối chiếu với dữ liệu; sai một chỗ là bỏ cả đoạn và thay bằng câu mẫu, thẻ ghi rõ lý do. Đó là điểm bán, không phải lỗi.",
     "Bản này cũng tự chạy lúc 07:30 và gửi email, hôm nay tạm dừng để giữ dữ liệu cho buổi họp."],
    ["Phần lớn 20 giây là đọc Business Central. Nói trước để người xem không tưởng máy treo."]);

  c.push(h2("Phần 2 · Một lô cận date: AI phân tích, chọn phương án"));
  buoc(3, "Lô nào sắp hết hạn?", "trang.sc · Marou",
    "Nút 3.",
    "36 lô cận date, chia theo địa điểm; 5 thẻ lô giá trị lớn nhất. Thẻ Choco pillar S0010: 470 cái, 26 ngày, bán không kịp; hai nút Đề xuất giảm giá và Phương án xử lý.",
    ["Câu này trợ lý đọc thẳng bảng. Điều phối thấy toàn hệ thống; quản lý cửa hàng hỏi cùng câu chỉ thấy cửa hàng mình.",
     "Chọn Choco pillar để đi tiếp: 470 cái mà 26 ngày nữa hết hạn, tại chỗ bán không kịp."]);
  buoc(4, "Phương án xử lý cho Choco pillar", "trang.sc · Marou",
    "Nút 4 chỉ hiện hướng dẫn. Trên thẻ Choco pillar bấm Phương án xử lý.",
    "Sau khoảng 6 giây: thẻ bảng năm phương án kèm giá trị cứu được hoặc mất, lời khuyên của model (chuyển 199 sang S0001 bán nhanh hơn), nút ghi đề xuất. Bấm nút đó. Sau khi ghi: thẻ Email cho người duyệt, phần lời do AI viết, kênh SMTP đã gửi.",
    ["Code tính năm phương án: giữ, chuyển, chuyển kèm giảm giá, giảm giá, huỷ. Khả năng nhận của từng cửa hàng bằng bán bình quân nhân ngày còn lại trừ tồn họ đang có.",
     "Model chọn một và nói vì sao. Nó được chọn khác code, miễn nói được lý do trên số đã có. Khoá phương án phải nằm trong bảng, chữ số phải có trong dữ liệu.",
     "Đây là UC2 nối sang UC5: hàng cận date đi về nơi bán nhanh, không phải huỷ.",
     "Người duyệt được gọi hai đường: thẻ trong chat cho ai đang mở trợ lý, email cho ai không mở. Code điền bảng số liệu và link BC; AI chỉ viết đoạn mở đầu và đoạn kết, mỗi con số phải có trong dữ liệu, sai thì dùng mẫu và ghi rõ."]);
  buoc(5, "Hùng duyệt chuyển hàng", "hung.dieuphoi · Marou",
    "Nút 5 đổi sang Hùng. Bấm Duyệt chuyển hàng trên thẻ đề xuất 199 Choco pillar S0010 sang S0001.",
    "Thẻ Đã duyệt kèm số Transfer Order và link mở trong BC; cột phải Transfer Order có dòng mới, trạng thái Open.",
    ["Đề xuất ghi vào một bảng riêng trong Business Central, trạng thái luôn vào ở Proposed. Không có đường tắt cho trợ lý ghi thẳng chứng từ.",
     "Chứng từ mang số đề xuất, kiểm toán truy ngược được từ chứng từ về đề xuất và về dòng dữ liệu gốc."]);

  c.push(h2("Phần 3 · Cửa hàng bán lẻ hết hàng: LS tính, AI đề xuất"));
  buoc(6, "Sắp hết Ice cream ở cửa hàng tôi", "minh.s0002 · Dakao",
    "Nút 6. Console đổi sang Minh và gửi câu.",
    "Trợ lý: Ice cream tại S0002 còn 8, đủ 5,5 ngày; theo LS Replenishment đề xuất đặt mua 12 từ MAROU giao thẳng tới S0002, đang xin điều phối duyệt.",
    ["Cửa hàng chỉ nói một câu tự nhiên. Trợ lý nhận ra mặt hàng và cửa hàng của người hỏi, đọc con số LS đã tính, ghi đề xuất vào Business Central và gửi người duyệt.",
     "Trợ lý không tự tính số. 12 là số của LS Replenishment, kiểu min-max: điểm đặt lại 8, mức tối đa 20.",
     "Dakao là bán lẻ, không có kho trung tâm: đề xuất là đặt mua từ Marou, giao thẳng cửa hàng. Đây là mô hình hai đơn vị của Marou."],
    ["Bước này ghi thật một đề xuất vào Business Central. Bấm lần hai thì trợ lý nói đã có đề xuất, không ghi thêm."]);
  buoc(7, "Vì sao LS đề xuất Ice cream cho S0002?", "trang.sc · Dakao",
    "Nút 7.",
    "AI viết vài câu: Stock Levels, Reorder Point 8, Maximum 20, tồn 8 nên mua 12; bảng nhật ký tính thu gọn bên dưới; link mở nhật ký tính của LS.",
    ["Từng bước là nhật ký tính của LS Replenishment, trợ lý không tính lại. Ai cũng đối chiếu được bằng link.",
     "Tham số nằm trên Item Card của LS, Marou tự sửa, không sửa code."]);
  buoc(8, "Hùng duyệt đặt mua, gửi đơn sang Marou", "hung.dieuphoi · Dakao",
    "Nút 8 đổi sang Hùng. Thẻ Đề xuất đặt mua Ice cream: bấm Duyệt đặt mua. Thẻ Đã tạo Purchase Order hiện nút Gửi đơn sang Marou, bấm tiếp.",
    "Thẻ Đã tạo Purchase Order HO1062xx kèm link mở đơn. Sau khi gửi: thẻ báo đơn Released, bên Marou có Sales Order S900xx.",
    ["Gửi đơn sang Marou là Intercompany chuẩn của Business Central: đơn mua bên Dakao thành đơn bán bên Marou, không nhập lại. Trợ lý không tự bấm nút này vì gửi kéo theo Release."]);
  buoc(9, "Tổng hợp những đề xuất bổ sung bất thường", "trang.sc · Dakao",
    "Nút 9.",
    "Sau khoảng 15 giây: danh sách đề xuất của LS theo cửa hàng, dòng nào có dấu hiệu lạ nói vì sao (hết hàng quá nửa cửa sổ tính, không có bán bình quân, tồn bằng 0) và việc nên làm. Nhãn AI viết.",
    ["Đây là nhóm Khám phá và phân tích insight. Không ai viết sẵn câu trả lời: model gọi tool đọc toàn bộ đề xuất của LS, đọc các cờ do code tính, chọn dòng đáng xem và giải thích.",
     "Croissant chocolate lộ ra ở đây: LS đếm 42 trên 56 ngày là hết hàng, vì bánh tươi huỷ cuối ngày nên tồn về 0 mỗi tối. Đó là Out of Stock cần xem lại cách ghi."],
    ["Câu trả lời đổi theo dữ liệu, không học thuộc. Nếu model chọn dòng khác với dự kiến thì đọc lý do nó nêu."]);

  c.push(h2("Phần 4 · Dự báo, một nhịp"));
  buoc(10, "Dự báo Choco bowl ở S0010 sai bao nhiêu?", "trang.sc · Dakao",
    "Nút 10. Nếu khách hỏi WAPE, Bias là gì: mở tab Dự báo, phần Cách đọc ngay dưới tiêu đề.",
    "Thẻ Dự báo Choco bowl tại S0010: ba phương pháp, dự báo 7 ngày tới đã ghi vào Retail Forecast Entry của LS, sự kiện KM-CHOCOBOWL-09 cộng 150% từ 23 đến 25/09.",
    ["Dự báo không nằm ở bảng riêng của NaviWorld. Nó ghi vào bảng chuẩn của LS, nên LS Replenishment dùng được ngay.",
     "Holt-Winters là thống kê chuỗi thời gian, chưa phải AI. Nói thẳng. AI ở đây là phần kể lại kết quả."]);
  buoc(11, "CTKM nào đang chạy và sắp tới?", "trang.sc · Dakao",
    "Nút 11.",
    "AI viết vài câu: 3 đang chạy, 2 sắp tới, 2 CTKM thiếu nhu cầu trong LS; Choco bowl giảm 15% có Planned Event cho S0001, S0010 nhưng S0002, S0005 chưa có.",
    ["Trợ lý đọc Periodic Discount của LS và soi xem LS đã cộng nhu cầu khuyến mãi cho cửa hàng nào. Thiếu thì nói rõ: cửa hàng đó sẽ thiếu hàng đúng ngày khuyến mãi.",
     "Lỗ hổng này tôi cố ý để lại trong dữ liệu để thấy trợ lý bắt được."]);

  c.push(h2("Phần 5 · Hàng về cửa hàng: liên công ty khép vòng"));
  buoc(12, "Kiểm hàng Marou đã xuất kho", "hung.dieuphoi · Dakao",
    "Nút 12. Console gọi vòng kiểm đơn liên công ty và báo đã gửi tin cho những ai.",
    "Thẻ Marou đã xuất kho đơn HO106202 (82 Choco nuts, giao Cửa hàng Quận 1, phiếu 102045); dòng đơn HO106200 xuất từ 16/09 chưa post nhận kèm thẻ Cho trợ lý post nhận hàng; dòng đã gửi email.",
    ["Bên Marou không có gì tự động, người kho post xuất kho như mọi ngày. Bên Dakao, trợ lý đọc sang company bên kia bằng Intercompany và nối hai chứng từ.",
     "Xuất kho trong ngày thì chỉ báo. Qua ngày hôm sau vẫn chưa post nhận thì nhắc lại và xin phép post thay. Không ai duyệt thì không có gì được post.",
     "Đây là vấn đề số một trong khảo sát: hàng về mà chứng từ dồn tới cuối tháng, Marou đang thuê người ngoài để post."]);
  buoc(13, "Lan (S0001) nhận tin chuẩn bị nhận hàng", "lan.s0001 · Dakao",
    "Nút 13 đổi sang Lan.",
    "Hộp thư Lan có thẻ Marou đã xuất kho đơn HO106202: Choco nuts 82, giao Cửa hàng Quận 1, link mở đơn mua. Email cùng nội dung đã tới hộp thư.",
    ["Cửa hàng Quận 1 đang hết Choco nuts; giờ họ biết 82 cái đang tới, trước khi xe về.",
     "Thẻ không có số lô: bán lẻ không quản lý lô, trợ lý không đẩy số lô ra cho cửa hàng."]);
  buoc(14, "Hùng duyệt cho trợ lý post nhận HO106200", "hung.dieuphoi · Dakao",
    "Nút 14 đổi sang Hùng. Trên thẻ Cho trợ lý post nhận hàng đơn HO106200, bấm Duyệt cho post nhận hàng.",
    "Thẻ Đã post phiếu nhận 1071xx kèm link mở phiếu nhận trong BC. Mở link: phiếu nhận đã post, đúng mặt hàng và số lượng của đơn mua.",
    ["Đây là loại đề xuất duy nhất mà việc duyệt làm Business Central post thật một chứng từ. Mọi loại khác dừng ở chứng từ nháp.",
     "Quyền post nằm trong permission set riêng, gán tay. Không gán thì bấm Duyệt báo thiếu quyền, không âm thầm bỏ qua.",
     "Số lượng lấy từ đơn mua. Mặt hàng bên mua có bật quản lý lô thì số lô lấy từ sổ kho bên bán, không bịa; bán lẻ không bật thì phiếu post bình thường."],
    ["HO106200 xuất kho ngày 16/09 nên tối 16/09 nó còn là “trong ngày” và chưa có thẻ đề xuất; sáng 17/09 mới có. Đừng thấy tối nay thiếu thẻ mà tưởng hỏng."]);
  buoc(15, "Marou xuất kho đơn Ice cream vừa gửi", "hung.dieuphoi · Dakao, rồi xem hộp thư Minh",
    "Nút 15. Nút demo post xuất kho thay người kho Marou cho đơn Ice cream ở bước 8. Sau đó bấm vai Minh.",
    "Console báo đã gửi tin cho Minh, Hùng, Trang. Hộp thư Minh có thẻ chuẩn bị nhận 12 Ice cream.",
    ["Vòng khép lại: mười lăm phút trước Minh gõ một câu là sắp hết Ice cream; giờ hàng đã rời kho Marou và Minh được báo trước.",
     "Nút này là công cụ demo, không thuộc sản phẩm. Trên hệ thật đó là người kho Marou bấm Post Shipment."],
    ["Cần đơn Ice cream ở bước 8 đã gửi sang Marou; chưa gửi thì nút báo không còn đơn nào chờ xuất kho."]);

  c.push(h2("Phần 6 · Truy xuất, bất thường, chi phí"));
  buoc(16, "Truy xuất lô L260906-33323C", "trang.sc · Marou",
    "Nút 16. Console đổi về Marou.",
    "AI kể lại hành trình lô Choco nuts: nhập kho W0003, xuất 81 cái theo đơn liên công ty HO106202 sang Cửa hàng Quận 1, còn tồn ở đâu; bảng Item Ledger Entry thu gọn bên dưới.",
    ["Đây là phần traceability của UC2: một lô có vấn đề thì biết ngay nó nằm ở những địa điểm nào và còn bao nhiêu, thu hồi lấy lại ở đâu.",
     "Lô này chính là lô vừa đi ở phần 5: Marou chọn lô còn hạn (22/04/2027) để xuất, bên bán quản lý lô còn bên bán lẻ chỉ thấy mặt hàng và số lượng."],
    ["Lô L260908-33110B (đơn HO106201 hôm 16/09) cũng truy được nhưng là lô đã quá hạn, bị chọn trước khi sửa quy tắc FEFO; đừng dùng lô đó trên sân khấu."]);
  buoc(17, "Có gì bất thường trong 28 ngày qua không?", "trang.sc · Dakao",
    "Nút 17.",
    "Câu trả lời do AI viết: ưu tiên ba tín hiệu ở S0001 (nhận hàng hạn quá ngắn); danh sách 16 tín hiệu thu gọn bên dưới.",
    ["Năm tín hiệu code quét: bán sau hạn, nhận hàng hạn ngắn bất thường, huỷ tăng gấp đôi, tồn không bán, hết hàng lặp lại. Model chọn tối đa ba và giải thích; mã tín hiệu phải nằm trong danh sách.",
     "Lệch kiểm kê chưa đo được vì bộ dữ liệu không có phiếu kiểm kê. Nói thẳng chỗ này."]);
  buoc(18, "Chi phí AI đo được", "dung.admin · Marou",
    "Nút 18. Console mở tab Cài đặt AI.",
    "Token vào, token ra, ước tính tiền theo ngày và theo việc; công tắc bật tắt AI; trần chi phí sửa được tại chỗ.",
    ["Token là số đếm thật từ nhà cung cấp, tiền là ước tính theo đơn giá công bố; hoá đơn thật mới là số cuối.",
     "Tắt AI thì hệ thống vẫn chạy: số liệu, dashboard, luồng duyệt không đổi, các đoạn văn chuyển sang câu mẫu."]);

  // ------------------------------------------------------------------ 4
  c.push(pageBreak());
  c.push(h1("4. Câu hỏi hay gặp và cách trả lời"));
  c.push(...table(["Khách hỏi", "Trả lời"], [
    ["AI nằm ở đâu, hay chỉ là phần mềm thường?",
     "Trong buổi này AI ở năm chỗ: brief chọn việc (bước 2), chọn phương án cho lô cận date (4), phân tích đề xuất bổ sung bất thường (9), đọc tín hiệu bất thường (17), và kể lại mọi kết quả tra cứu bằng lời (7, 10, 11, 16). Còn lại là LS và Business Central tính, trợ lý đọc và giải thích. Tính năng không thuộc bốn nhóm tóm tắt, tạo sinh, phân tích, tự động hoá thì chúng tôi gọi đúng tên là tính năng ứng dụng."],
    ["Khách gõ một câu không có trong kịch bản thì sao?",
     "Cứ để khách gõ. Câu nào rule đọc chắc thì trả lời bằng dữ liệu, không tốn model; câu nào rule không giải được thì "
     + "chuyển cho model tự chọn tool (tồn theo địa điểm, sức khỏe tồn kho theo tầng, LS đề xuất bổ sung, tốc độ bán, lô, khuyến mãi) "
     + "rồi tổng hợp, thẻ có nút xem từng bước đã tra. Ví dụ đã chạy: “có những mặt hàng nào sắp hết hàng” từ quản lý cửa hàng."],
    ["Nhìn vào đâu để biết câu này AI viết hay câu soạn sẵn?",
     "Nhãn nhỏ dưới mỗi câu trả lời của trợ lý: “AI viết · gpt-4.1-mini” (đỏ) là model viết và đã qua phép kiểm số; “câu mẫu” (vàng) là "
     + "AI bị chặn hoặc đang tắt nên code ghép câu; “đọc từ dữ liệu, không gọi model” (xám) là rule đọc thẳng bảng. Thẻ AI còn có dòng Người soạn."],
    ["AI có bịa số không?",
     "Không thể đưa ra con số không có trong dữ liệu. Mọi chữ số model viết đều bị đối chiếu với dữ liệu code đưa; sai một chỗ là bỏ cả đoạn và thay bằng câu mẫu, thẻ ghi rõ lý do."],
    ["Trợ lý có tự ghi vào sổ không?",
     "Chỉ một trường hợp: post phiếu nhận hàng liên công ty, và chỉ sau khi một người bấm Duyệt. Mọi loại khác dừng ở chứng từ nháp."],
    ["Con số bổ sung là của ai?",
     "Của LS Replenishment, module có sẵn trong LS Central. Trợ lý đọc nhật ký tính của LS và kể lại, có link đối chiếu. Tham số trên Item Card, Marou tự sửa."],
    ["Dự báo dùng AI không?",
     "Chưa. Holt-Winters là thống kê chuỗi thời gian, dùng làm thước đo. Kết quả ghi vào bảng chuẩn của LS nên đổi mô hình sau này không phải đổi luồng."],
    ["Chi phí AI bao nhiêu?",
     "Ngày kiểm thử 16/09 tốn dưới 0,3 USD cho vài trăm lượt gọi. Xem tab Cài đặt AI: token là số đếm thật, tiền là ước tính theo đơn giá công bố."],
    ["Tắt AI thì hệ thống còn chạy không?",
     "Còn. Số liệu, dashboard và luồng duyệt không đổi. Các đoạn văn chuyển sang câu mẫu do code ghép."],
    ["Dữ liệu có ra khỏi Việt Nam không?",
     "Môi trường demo dùng Azure OpenAI ở Mỹ. Khi triển khai, extension của NaviWorld tự chọn vùng xử lý, giữ được trong Asia Pacific. Ghi vào phần governance."],
    ["Sao bên bán lẻ Dakao cũng thấy số lô trên phiếu nhận?",
     "Hai đơn vị đang dùng chung một bộ dữ liệu mô phỏng nên bên Dakao vẫn còn bật quản lý lô. Trợ lý xử lý số lô chỉ khi mặt hàng bên mua có bật, và không đẩy số lô ra cho cửa hàng. Cho cửa hàng giữ lô hay không là quyết định của Marou."],
    ["Email báo người duyệt có phải AI viết không?",
     "Có, phần lời. Bảng mặt hàng, lô, tồn, giá trị, tầng, policy và link Business Central do code điền; AI viết hai đoạn mở đầu và kết, mỗi chữ số phải có trong dữ liệu đưa nó, không thì thư dùng mẫu và thẻ ghi rõ. Thẻ Email cho người duyệt trong chat của người đề nghị hiện đúng hai đoạn đó kèm nhãn nguồn."],
    ["Sao email gửi từ một địa chỉ Gmail?",
     "Tenant demo không có license Exchange Online nên POC gửi qua SMTP. Triển khai thật thì thư đi bằng hộp thư của Marou, cấu hình một lần."],
    ["Ngày trên email và bảng tồn kho lấy từ đâu?",
     "Từ ngày lớp tính toán trong Business Central chạy lần gần nhất, tức 17/09. Chứng từ mua bán mang ngày thật lúc thao tác."],
    ["Số liệu trong buổi này là thật chứ?",
     "Không. Bộ dữ liệu mô phỏng do NaviWorld dựng trên danh mục thật của Marou, chạy trên môi trường demo. Nói ít nhất một lần."],
  ], [4.2, 7.8]));

  // ------------------------------------------------------------------ 5
  c.push(h1("5. Sự cố và phương án dự phòng"));
  c.push(...table(["Hiện tượng", "Nguyên nhân thường gặp", "Xử lý tại chỗ"], [
    ["Dải đỏ ghi Không chạy được, Failed to fetch", "Máy chủ đang khởi động lại sau khi sửa file", "Chờ vài giây, dải tự tắt khi kết nối lại"],
    ["Bấm nút kịch bản mà hộp thư trống, không có màn hình chào", "Vòng đọc hộp thư chưa xong hoặc bị lỗi một thẻ", "Đã vá tối 16/09: màn hình chào luôn hiện khi hộp thư trống. Nếu vẫn trống, bấm F5"],
    ["Bước 6 trả lời “chuyển từ W0003” thay vì đặt mua từ MAROU", "Đang ở company Marou chứ không phải Dakao", "Nhìn dải nguồn: nút Dakao (bán lẻ) phải đang tô. Bấm lại nút 6"],
    ["Câu hỏi mở trả lời về hàng liên công ty", "Câu hỏi có chữ Marou kèm về hoặc xuất kho", "Dùng đúng câu trên nút; không thêm chữ Marou"],
    ["Đoạn văn ghi mẫu có sẵn thay vì AI", "Phép kiểm số đã chặn, hoặc AI đang tắt, hoặc hết trần", "Hành vi đúng. Mở tab Cài đặt AI xem trạng thái rồi giải thích"],
    ["Màn hình chậm khoảng 20 giây", "Đang đọc dữ liệu thật từ Business Central (brief, câu hỏi mở)", "Nói trước khi bấm. Đổi vai hay đổi company thì không còn chậm: cột phải lấy từ bản chụp, làm mới ở luồng nền"],
    ["Cột Theo dõi xử lý chưa cập nhật ngay sau khi Duyệt", "Bản chụp làm mới mỗi 8 giây", "Đợi một nhịp, không bấm lại"],
    ["Bước 12 không thấy thẻ HO106202", "Đơn đã được post nhận, hoặc đồng hồ ảo đã bị đẩy sang ngày khác", "Xem dòng Giờ hệ thống trong khay demo. Nếu đã +24 giờ thì HO106202 thành quá ngày, vẫn có thẻ đề xuất post, diễn tiếp bằng thẻ đó"],
    ["Trợ lý nhắc một đơn cũ không nằm trong kịch bản", "Đơn đó xuất kho từ hôm trước mà chưa ai post nhận", "Đó là đúng việc trợ lý phải làm. Duyệt luôn hoặc nói rõ đây là đơn tồn từ hôm trước"],
  ], [3.4, 4.2, 4.4]));
  c.push(...ghiChu("Phương án cuối cùng nếu mạng hỏng: đổi dải nguồn sang dữ liệu mô phỏng. Bộ mô phỏng neo ngày 18/09 và LS trong đó là công thức "
    + "cũ, nên các bước 7, 9 (nhật ký tính LS) không có; các bước còn lại diễn được nhưng số khác. Nói rõ với khách là đang ở bộ mô phỏng.",
    "Mất mạng giữa buổi"));

  return c;
}

(async () => {
  await build(
    "Demo script: một buổi sáng ở Dakao và Marou",
    "Runbook 18 bước cho buổi trình diễn 17/09/2026: dữ liệu đã tạo sẵn, bấm gì, khách thấy gì, nói gì",
    {
      headerLeft: "NaviWorld", headerRight: "Marou • Demo script • Nội bộ",
      footer: `Demo script · Bản 2.4, ${NGAY}`,
      cover: ["Người đọc: người trình diễn và người hỗ trợ kỹ thuật trong buổi họp",
        "Môi trường: Business Central NWV01, hai company NWV-MAROU và NWV-DAKAO, Work Date 17/09/2026",
        `Soạn tối ${NGAY}. Thứ tự bước trùng với cột Kịch bản demo trên console.`,
        "Đi kèm bộ slide 12; slide có speaker note, tài liệu này có thao tác."],
    },
    noiDung(),
    __dirname + "/13 Marou POC - Demo script (noi bo).docx",
  );
})();
