/**
 * Tai lieu 13: demo script cho buoi trinh dien UC2 + tro ly.
 * Khac voi speaker note trong slide 12: cho nay la runbook thao tac, ai bam gi, o dau, cho bao lau, noi cau nao.
 * Chay: cd docs; node build_13.js
 */
const { p, h1, h2, h3, bullet, num, table, pageBreak, build, ghiChu, luuY } = require("./lib_brand");

const NGAY = "16/09/2026";

function noiDung() {
  const c = [];

  // ------------------------------------------------------------------ 1
  c.push(h1("0. Ngày demo không trùng ngày neo của dữ liệu"));
  c.push(p("Bộ dữ liệu trình diễn đã được tính lại với Work Date 17/09/2026, đúng ngày demo. Ba điều dưới đây để giữ cho nó "
    + "không lệch trong lúc trình bày."));
  c.push(...table(["Điều", "Làm gì", "Vì sao"], [
    ["Giữ Work Date 17/09/2026", "Không đổi Work Date của phiên Business Central, không chạy lại Run Inventory Health",
      "Kết quả sáu tầng và số dòng đã tính theo ngày này. Đổi ngày rồi tính lại thì mọi con số đổi theo."],
    ["Chứng từ mua bán vẫn mang ngày thật", "Không phải làm gì, Business Central tự ghi",
      "Đơn mua và phiếu giao hàng post theo ngày thao tác, nên hai loại ngày này lệch nhau. Đó là bình thường."],
    ["Đồng hồ trợ lý là ngày thật", "Xem dòng “Giờ hệ thống” trong khay Điều khiển demo",
      "Vòng nhận hàng liên công ty so ngày xuất kho với đồng hồ này, nên nút +24 giờ vẫn diễn được cảnh sáng hôm sau."],
  ], [3.0, 4.6, 4.4]));
  c.push(...ghiChu("Ngày chốt hiện ở màn hình Sức khỏe tồn kho, trên thẻ “Chốt ngày 17/09/2026”, chứ không nằm trên dải nguồn. "
    + "Dải nguồn chỉ ghi đang đọc Business Central hay dữ liệu mô phỏng, kèm số dòng kết quả.",
    "Ngày chốt hiện ở đâu"));

  c.push(pageBreak());
  c.push(h1("1. Trước buổi demo: 20 phút chuẩn bị"));
  c.push(p("Làm đủ bảy việc dưới đây rồi mới mở phòng họp. Mỗi việc đều có cách kiểm, đừng tin là xong nếu chưa nhìn thấy dấu hiệu."));
  c.push(...table(["Việc", "Cách làm", "Dấu hiệu đã xong"], [
    ["Chạy máy chủ trợ lý", "Trong thư mục python: python -m uvicorn assistant.channels.web:app --port 8188 --reload", "Mở http://127.0.0.1:8188 thấy màn hình chào"],
    ["Chọn nguồn dữ liệu", "Dải ngay dưới thanh tiêu đề, bấm Business Central", "Dải chuyển xanh và ghi số dòng kết quả; mở tab Sức khỏe tồn kho thấy thẻ Chốt ngày 17/09/2026"],
    ["Kiểm hai đơn vị", "Trên dải nguồn có hai nút NWV-MAROU và NWV-DAKAO", "Bấm qua lại, số dòng kết quả đổi theo"],
    ["Bật AI", "Chọn vai quản trị, tab Cài đặt AI, bật công tắc", "Ô trạng thái ghi AI đang bật, còn trần chi phí"],
    ["Kiểm trần chi phí", "Cùng tab Cài đặt AI", "Còn ít nhất 1 USD trong trần ngày"],
    ["Mở sẵn Business Central", "Một tab trình duyệt riêng, đăng nhập môi trường NWV01", "Bấm link trong thẻ là mở được ngay, không phải đăng nhập giữa buổi"],
    ["Biết đơn liên công ty đang ở trạng thái nào", "Khay Điều khiển demo, bấm Kiểm hàng Marou đã xuất kho", "Trợ lý liệt kê đơn nào vừa xuất kho hôm nay, đơn nào đã quá ngày mà chưa nhận. Đọc kỹ để biết màn 16 bắt đầu từ bước nào"],
  ], [2.4, 5.4, 4.2]));
  c.push(...ghiChu("Work Date của Business Central để 17/09/2026: lớp tính toán trong BC dùng Work Date, còn chứng từ mua bán thì post theo ngày thật. "
    + "Và đừng bấm Reset trong khay demo trước buổi họp, nó xoá hộp thư cùng các việc đang theo dõi, và bạn sẽ mất đơn đang chờ nhận hàng.",
    "Hai điều dễ quên"));

  c.push(h2("Người dùng demo và vai trò"));
  c.push(...table(["Đăng nhập", "Vai", "Đơn vị", "Dùng trong màn"], [
    ["trang.sc", "Supply Chain", "Cả hai", "01 đến 08, 12 đến 16"],
    ["hung.dieuphoi", "Điều phối kho", "Cả hai", "06, 09, 10, 15, 16"],
    ["lan.s0001", "Quản lý cửa hàng Quận 1", "Dakao", "07"],
    ["tuan.s0005", "Quản lý Nhà hàng Thảo Điền", "Dakao", "16"],
    ["kho.w0003", "Kho trung tâm", "Marou", "09"],
    ["thu.retailops", "Retail Ops", "Dakao", "13"],
    ["dung.admin", "Quản trị", "Cả hai", "Cài đặt AI, chi phí, quét sáng"],
  ], [2.2, 3.4, 2.4, 4.0]));
  c.push(...luuY("Đổi vai là đổi cả hộp thư. Thẻ trợ lý gửi cho người duyệt chỉ hiện khi bạn đang ở vai đó, nên thứ tự đổi vai trong script phải giữ đúng."));

  // ------------------------------------------------------------------ 2
  c.push(pageBreak());
  c.push(h1("2. Bản rút gọn 25 phút"));
  c.push(p("Khi lịch bị cắt, diễn đúng năm màn này. Nó đi hết một vòng: nhìn số, được nhắc, chọn cách xử lý, duyệt, ra chứng từ."));
  c.push(...table(["Phút", "Màn", "Câu mở đầu gợi ý"], [
    ["0 đến 4", "01 · Dashboard sức khỏe tồn kho", "Đây là số Business Central tính, trợ lý chỉ đọc lại."],
    ["4 đến 9", "05 · Brief buổi sáng do AI viết", "Người đọc không phải tự lọc; trợ lý chọn ba việc và nói vì sao."],
    ["9 đến 14", "08 · Phương án cho lô cận date", "Code tính từng phương án, model chọn một và giải thích."],
    ["14 đến 18", "09 · Đề xuất và người duyệt", "Trợ lý không tự làm; chứng từ sinh ra khi người của Marou bấm Duyệt."],
    ["18 đến 21", "11 · Truy xuất lô", "Một lô có vấn đề thì biết ngay nó nằm ở đâu, còn bao nhiêu."],
    ["21 đến 28", "16 · Nhận hàng liên công ty", "Đây là điểm đau Marou nêu trong khảo sát, và là chỗ duy nhất trợ lý post thật."],
  ], [1.8, 4.6, 5.6]));
  c.push(...ghiChu("Bộ slide đi kèm bản rút gọn này là `Marou POC - slide demo (ban ngan).pptx`, 16 slide, trong thư mục "
    + "C:\Users\dungdt.NWV\Demo-Marou. Bộ đầy đủ 30 slide vẫn giữ nguyên để mở khi khách hỏi sâu.",
    "Dùng bộ slide nào"));

  // ------------------------------------------------------------------ 3
  c.push(pageBreak());
  c.push(h1("3. Bản đầy đủ: mười sáu màn"));
  c.push(p("Mỗi màn ghi ba cột: bấm gì, chờ gì, nói gì. Cột “chờ gì” là dấu hiệu để biết thao tác đã xong, đừng bấm tiếp khi chưa thấy."));

  const man = (ma, ten, vai, buoc, noi, luuYs) => {
    c.push(h2(`Màn ${ma} · ${ten}`));
    c.push(p(`Vai: ${vai}`));
    c.push(...table(["Bấm gì", "Chờ gì"], buoc, [5.6, 6.4]));
    c.push(h3("Nói gì"));
    noi.forEach((x) => c.push(bullet(x)));
    if (luuYs) c.push(...luuY(luuYs.join(" ")));
  };

  man("01", "Dashboard sức khỏe tồn kho", "trang.sc, đơn vị NWV-MAROU",
    [["Tab Sức khỏe tồn kho", "Bốn con số lớn ở hàng trên, bảng dòng ở dưới"],
     ["Bấm một tầng bất kỳ để lọc", "Bảng rút còn đúng tầng đó"]],
    ["Bốn con số này do lớp tính toán trong Business Central chạy, không phải trợ lý tính.",
     "Sáu tầng: quá hạn, cận date, rủi ro đứt hàng, chậm luân chuyển, tồn thừa, bình thường.",
     "Dải nguồn phía trên ghi rõ đang đọc dữ liệu thật hay mô phỏng, và ngày chốt của lần tính gần nhất."]);

  man("02", "Lọc đúng tầng, tìm đúng lô", "trang.sc",
    [["Gõ tên hàng vào ô tìm trên bảng", "Bảng lọc theo tên, mã hoặc số lô"],
     ["Bấm một dòng", "Mở trang Chi tiết lô"]],
    ["Tìm được theo cả ba: tên hàng, mã hàng, số lô.",
     "Trang chi tiết mở ra là để người kiểm số đối chiếu, không phải để trình bày."]);

  man("03", "Vì sao một lô vào tầng đó", "trang.sc",
    [["Ở trang Chi tiết lô, xem mục Nói bằng lời", "Đoạn văn tự nạp sau vài giây"],
     ["Cuộn xuống mục Quy tắc phân tầng", "Bảng điều kiện, dòng đầu tiên khớp được tô"]],
    ["Đoạn văn này do model viết, nhưng mọi con số trong đó phải có trong dữ liệu đưa cho model.",
     "Nếu model viết một con số không có trong dữ liệu, hệ thống bỏ đoạn đó và thay bằng câu mẫu, thẻ ghi rõ lý do.",
     "Phía dưới là quy tắc phân tầng, dùng tại điều kiện đầu tiên khớp; ai cũng kiểm lại được."],
    ["Nếu đoạn văn ghi “Người soạn: mẫu có sẵn” thì đó không phải lỗi, mà là phép kiểm số đã chặn. Nói thẳng điều đó, nó là điểm bán."]);

  man("04", "Độ phủ dữ liệu trước khi tin kết quả", "trang.sc",
    [["Thanh công cụ, bấm Độ phủ dữ liệu", "Bảng tỷ lệ mặt hàng có nhóm, có lô, có điểm đặt hàng"]],
    ["Trước khi tin kết quả thì phải biết dữ liệu phủ tới đâu.",
     "Đây cũng là danh sách việc cần làm khi triển khai thật: mã nào còn thiếu nhóm hàng, thiếu mã quản lý lô."]);

  man("05", "Brief buổi sáng do AI viết", "trang.sc",
    [["Bấm nút Brief cạnh ô nhập", "Thẻ Ba việc quan trọng nhất sáng nay, rồi các thẻ dòng bên dưới"]],
    ["Trợ lý đọc bảng kết quả, chọn ba việc, và nói vì sao chọn.",
     "Mỗi việc có link mở thẳng sổ kho của lô đó trong Business Central.",
     "Brief này cũng tự chạy lúc 7 giờ 30 mỗi sáng và gửi email, không cần ai bấm."],
    ["Brief trên dữ liệu thật mất khoảng 20 giây, phần lớn là đọc Business Central. Nói trước để người xem không tưởng máy treo."]);

  man("06", "Hỏi hàng đã hết hạn toàn hệ thống", "hung.dieuphoi",
    [["Gõ: có mặt hàng nào đã hết hạn chưa", "Trợ lý trả lời kèm bảng chia theo địa điểm"]],
    ["Câu này không gọi model, trợ lý đọc thẳng bảng kết quả.",
     "Điều phối thấy toàn hệ thống; quản lý cửa hàng hỏi cùng câu chỉ thấy cửa hàng của mình."]);

  man("07", "Tra tồn tại cửa hàng của mình", "lan.s0001",
    [["Gõ: còn bao nhiêu Choco nuts ở cửa hàng tôi", "Trợ lý trả lời, nhắc cửa hàng S0001 trước tiên"]],
    ["Phân quyền theo vai, không phải chỉ ẩn nút: hỏi sang cửa hàng khác thì trợ lý nói rõ là không thuộc phạm vi của bạn."]);

  man("08", "Phương án cho lô cận date", "trang.sc",
    [["Mở Chi tiết lô của một lô cận date", "Mục Phương án xử lý hiện bảng"],
     ["Đọc bảng năm phương án", "Mỗi phương án có số lượng và giá trị cứu được hoặc mất"],
     ["Trong Trò chuyện, bấm Phương án xử lý trên thẻ lô cận date", "Thẻ có lời khuyên và nút ghi đề xuất"]],
    ["Code tính năm phương án: giữ, chuyển, chuyển kèm giảm giá, giảm giá, huỷ.",
     "Khả năng nhận của từng cửa hàng tính bằng bán bình quân nhân số ngày còn lại, trừ đi tồn họ đang có.",
     "Model chọn một phương án và nói vì sao. Nó được chọn khác code, miễn là nói được lý do trên số đã có.",
     "Chốt chặn: khoá phương án model chọn phải nằm trong bảng, và mọi chữ số phải có trong dữ liệu."]);

  man("09", "Đề xuất và người duyệt", "trang.sc rồi đổi sang hung.dieuphoi",
    [["Ở vai trang.sc, bấm nút ghi đề xuất trên thẻ", "Trợ lý xác nhận đã ghi vào Business Central, trạng thái Proposed"],
     ["Đổi vai sang hung.dieuphoi", "Hộp thư có thẻ đề xuất mới"],
     ["Bấm Duyệt", "Thẻ báo đã tạo chứng từ, kèm link mở trong BC"],
     ["Bấm link, xem chứng từ trong BC", "Chứng từ ở trạng thái Open hoặc nháp"]],
    ["Đề xuất ghi vào một bảng riêng trong Business Central, trạng thái luôn vào ở Proposed.",
     "Không có đường tắt nào cho trợ lý ghi thẳng vào chứng từ.",
     "Chứng từ sinh ra mang số đề xuất, nên kiểm toán truy ngược được từ chứng từ về đề xuất và về dòng dữ liệu gốc."],
    ["Màn này ghi thật vào Business Central. Nếu chỉ muốn diễn mà không ghi, đổi dải nguồn sang mô phỏng trước khi bấm."]);

  man("10", "Luồng huỷ khép kín", "hung.dieuphoi",
    [["Duyệt một đề xuất huỷ", "Thẻ Đã duyệt huỷ, kèm biên bản và số chứng từ AGENT-…"],
     ["Đọc biên bản trên thẻ", "Bảng số liệu do code điền, hai đoạn văn do model viết"],
     ["Khay demo, bấm Giả lập kế toán post chứng từ huỷ", "Trợ lý báo đã post và đóng việc"]],
    ["Duyệt huỷ thì Business Central tạo một dòng Item Journal chưa post, có số lô và mã lý do.",
     "Trợ lý soạn biên bản, gửi thẻ cho người duyệt và người đề nghị, gửi email cho bộ phận post.",
     "Rồi nó theo: mỗi ngày kiểm xem kế toán đã post chưa, chưa thì nhắc, nhắc ba lần thì báo người duyệt.",
     "Trợ lý không post. Quyền post không nằm trong permission set của nó."],
    ["Nút giả lập chỉ chạy ở chế độ mô phỏng. Trên dữ liệu thật thì kế toán post trong Item Journal, và trợ lý tự thấy."]);

  man("11", "Truy xuất lô và khoanh vùng thu hồi", "trang.sc",
    [["Gõ: truy xuất lô L260908-33110B", "Trợ lý liệt kê lô đi những đâu, còn tồn ở đâu"]],
    ["Đây là phần traceability của UC2: một lô có vấn đề thì biết ngay nó nằm ở những địa điểm nào và còn bao nhiêu.",
     "Với hàng liên công ty, lô ở Marou và lô ở cửa hàng Dakao là một, nên truy được cả chuỗi."]);

  man("12", "Phát hiện bất thường trong sổ kho", "trang.sc",
    [["Gõ: có gì bất thường trong sổ kho không", "Thẻ liệt kê các tín hiệu, kèm nhận xét của model"]],
    ["Năm tín hiệu: bán sau hạn, nhận hàng hạn ngắn bất thường, huỷ tăng gấp đôi, tồn không bán, hết hàng lặp lại.",
     "Model chọn tối đa ba tín hiệu đáng xem trước và viết nhận xét; mã tín hiệu nó chọn phải nằm trong danh sách code đưa."]);

  man("13", "Nguyên nhân hàng huỷ", "thu.retailops",
    [["Gõ: vì sao Chocolate cake huỷ nhiều", "Thẻ bốn chỉ số kèm kết luận"]],
    ["Bốn cách đo: nhận nhiều hơn bán, bán chậm hơn nơi khác, hạn lúc nhận ngắn hơn thông thường, một đợt nhận quá lớn.",
     "Chuyển hàng trễ chưa đo được vì bộ dữ liệu chưa có Transfer Order; nói thẳng chỗ này."]);

  man("14", "Quét sáng mỗi ngày", "dung.admin",
    [["Khay demo, bấm Chạy quét sáng UC2 ngay", "Dòng tóm tắt: bao nhiêu đề xuất huỷ, bao nhiêu phương án, brief gửi mấy người"],
     ["Đổi vai sang hung.dieuphoi", "Hộp thư có các thẻ đề xuất trợ lý tự ghi"]],
    ["Đây là phần tự động hoá: không ai bấm gì, trợ lý tự quét lúc 7 giờ 30, tự ghi đề xuất cho lô đã hết hạn, tự gửi brief và email.",
     "Vẫn qua policy: đề xuất huỷ luôn phải có người duyệt, nên tự động hoá này có phanh.",
     "Đã báo rồi thì không báo lại, mỗi sáng chỉ còn cái mới."],
    ["Quét trên dữ liệu thật mất khoảng hai phút và ghi đề xuất thật vào Business Central. Cân nhắc chạy trước buổi họp rồi chỉ trình kết quả."]);

  man("15", "Báo cáo tuần hàng huỷ", "trang.sc",
    [["Gõ: báo cáo tuần hàng huỷ", "Thẻ báo cáo, kèm email đã gửi"]],
    ["Báo cáo so tuần này với tuần trước, xếp theo giá trị, kèm nguyên nhân đọc từ phần phân tích.",
     "Email gửi mỗi tuần một lần tính theo tuần ISO, nên bấm lại trong tuần không gửi trùng."]);

  man("16", "Nhận hàng liên công ty", "hung.dieuphoi, quản lý cửa hàng nhận hàng, trang.sc · đơn vị NWV-DAKAO",
    [["Trên dải nguồn chọn NWV-DAKAO, vai hung.dieuphoi, bấm Kiểm hàng Marou đã xuất kho", "Trợ lý báo đơn nào vừa xuất kho, đơn nào quá ngày"],
     ["Đổi vai sang quản lý cửa hàng được nhắc tên", "Hộp thư cửa hàng có thẻ chuẩn bị nhận hàng"],
     ["Về vai hung.dieuphoi, đọc thẻ đề xuất của đơn quá ngày", "Thẻ Cho trợ lý post nhận hàng đơn …, hai nút Duyệt và Để người post"],
     ["Bấm Duyệt cho post nhận hàng", "Thẻ Đã post phiếu nhận, kèm link mở phiếu trong BC"],
     ["Bấm link, xem phiếu nhận trong BC", "Phiếu nhận đã post, đúng mặt hàng và số lượng của đơn mua"]],
    ["Đây là vấn đề số một và số ba trong khảo sát: nhập đơn không kịp thời, và muốn tự động hoá hai chiều giữa hai công ty.",
     "Cách xử lý không đối xứng hai đầu, và đó là chủ ý. Bên Marou không có gì tự động, người kho vẫn post xuất kho như mọi ngày.",
     "Bên Dakao, Marou xuất kho trong ngày thì trợ lý báo ngay cho cửa hàng và Supply Chain để chuẩn bị nhận. Chỉ báo, không ghi gì.",
     "Qua ngày hôm sau mà vẫn chưa post nhận thì trợ lý nhắc lại, và xin phép: cho trợ lý post phiếu nhận thay không.",
     "Người duyệt bấm Duyệt thì Business Central mới post. Không ai duyệt thì không có gì được post.",
     "Trợ lý không nghĩ ra số nào: số lượng lấy từ đơn mua. Mặt hàng nào bên mua có bật quản lý lô thì số lô cũng lấy từ sổ kho bên bán, "
     + "còn không bật thì phiếu nhận post bình thường, không có lô. Bán lẻ theo nghiệp vụ không quản lý lô; bộ demo đang bật nên ảnh có lô."],
    ["Đây là loại đề xuất duy nhất mà việc duyệt làm Business Central post thật một chứng từ. Mọi loại khác chỉ tạo chứng từ nháp.",
     "Quyền post nằm trong permission set riêng tên NWV AGENT POST RCPT, phải gán tay. Không gán thì bấm Duyệt sẽ báo thiếu quyền chứ không âm thầm bỏ qua.",
     "Muốn diễn trọn vòng từ đầu thì làm thêm ba bước dưới đây trước khi vào màn này."]);

  c.push(h3("Nếu muốn diễn trọn vòng, làm trước ba bước này"));
  c.push(...table(["Bấm gì", "Chờ gì"], [
    ["Vai hung.dieuphoi, đơn vị NWV-DAKAO, bấm Brief", "Có thẻ Đề xuất đặt mua từ Marou"],
    ["Bấm Duyệt đặt mua", "Thẻ Đã tạo Purchase Order, kèm nút Gửi đơn sang Marou"],
    ["Bấm Gửi đơn sang Marou", "Thẻ báo đơn đã Released và bên Marou đã tạo Sales Order"],
    ["Khay demo, bấm Marou xuất kho đơn liên công ty", "Trợ lý báo Marou đã xuất kho, kèm số phiếu giao hàng"],
    ["Khay demo, bấm +24 giờ (sáng hôm sau)", "Đồng hồ hệ thống nhảy sang hôm sau"],
    ["Bấm Kiểm hàng Marou đã xuất kho", "Trợ lý nhắc lại, và gửi đề xuất cho người duyệt"],
  ], [5.6, 6.4]));
  c.push(...luuY("Nút Marou xuất kho ghi ngày post bằng đồng hồ trợ lý, nên phiếu giao hàng luôn là của hôm nay và bước báo trước chạy đúng. "
    + "Nếu bấm +24 giờ trước khi xuất kho thì thứ tự hỏng, phải xuất kho trước rồi mới nhảy ngày."));

  // ------------------------------------------------------------------ 4
  c.push(pageBreak());
  c.push(h1("4. Câu hỏi hay gặp và cách trả lời"));
  c.push(...table(["Khách hỏi", "Trả lời"], [
    ["AI nằm ở đâu, hay chỉ là phần mềm thường?",
     "Mười ba tính năng xếp theo bốn nhóm: tóm tắt, tạo sinh nội dung, khám phá phân tích, tự động hoá. Tính năng không thuộc nhóm nào thì chúng tôi gọi đúng tên là tính năng ứng dụng, không gán nhãn AI."],
    ["AI có bịa số không?",
     "Không thể đưa ra con số không có trong dữ liệu. Mọi chữ số model viết đều bị đối chiếu với dữ liệu code đưa; sai một chỗ là bỏ cả đoạn và thay bằng câu mẫu, thẻ ghi rõ lý do."],
    ["Trợ lý có tự ghi vào sổ không?",
     "Chỉ một trường hợp: post phiếu nhận hàng liên công ty, và chỉ sau khi một người bấm Duyệt. Mọi loại khác dừng ở chứng từ nháp."],
    ["Chi phí AI bao nhiêu?",
     "Cả ngày kiểm thử 16/09 tốn 0,085 USD cho 146 lượt gọi. Token là số đếm thật từ nhà cung cấp, tiền là ước tính theo đơn giá công bố; hoá đơn thật mới là số cuối cùng."],
    ["Tắt AI thì hệ thống còn chạy không?",
     "Còn. Số liệu, dashboard và luồng duyệt không đổi. Các đoạn văn chuyển sang câu mẫu do code ghép."],
    ["Dữ liệu có ra khỏi Việt Nam không?",
     "Môi trường demo hiện dùng Azure OpenAI ở Mỹ. Khi triển khai, extension của NaviWorld tự chọn được vùng xử lý, giữ được trong Asia Pacific. Đây là điểm cần ghi vào phần governance."],
    ["Ngày trên email, báo cáo và bảng tồn kho lấy từ đâu?",
     "Từ ngày lớp tính toán trong Business Central chạy lần gần nhất, không phải ngày máy chủ. Nếu neo theo ngày máy thì cửa sổ lịch sử "
     + "bán và số ngày kể từ lần bán cuối đều lệch. Chứng từ mua bán thì vẫn mang ngày thật của lúc thao tác."],
    ["Sao bên bán lẻ Dakao cũng thấy số lô, trong khi bán lẻ không quản lý lô?",
     "Vì hai đơn vị đang dùng chung một bộ dữ liệu mô phỏng, bên Dakao vẫn còn bật quản lý lô. Trợ lý xử lý số lô chỉ khi mặt hàng bên "
     + "mua có bật; lúc đó nó lấy đúng lô bên bán đã xuất chứ không bịa, còn không bật thì phiếu nhận post bình thường không có lô. "
     + "Có cho cửa hàng giữ lô hay không là quyết định của Marou, chưa chốt."],
    ["Sao email gửi từ một địa chỉ Gmail?",
     "Môi trường demo nằm trên tenant thử nghiệm không có license Exchange Online, nên POC gửi qua SMTP. "
     + "Khi triển khai thật, thư đi bằng hộp thư của Marou; đây là cấu hình một lần, không đụng vào code."],
    ["Số liệu trong buổi này là thật chứ?",
     "Không. Đây là bộ dữ liệu mô phỏng do NaviWorld dựng trên danh mục thật của Marou, chạy trên môi trường demo. Nói câu này ít nhất một lần trong buổi."],
  ], [4.2, 7.8]));

  // ------------------------------------------------------------------ 5
  c.push(h1("5. Sự cố và phương án dự phòng"));
  c.push(...table(["Hiện tượng", "Nguyên nhân thường gặp", "Xử lý tại chỗ"], [
    ["Dải đỏ ghi Không chạy được, Failed to fetch", "Máy chủ đang khởi động lại sau khi sửa file", "Chờ vài giây, dải tự tắt khi kết nối lại"],
    ["Bấm Brief không thấy gì", "Business Central từ chối vì thiếu quyền", "Đọc câu lỗi hiện dưới thanh tiêu đề, nó ghi rõ số bảng thiếu quyền"],
    ["Thẻ báo Đề xuất này không còn trong Business Central", "Đề xuất thuộc phiên dữ liệu trước hoặc đã bị xoá", "Bấm Brief để lấy danh sách đề xuất hiện tại"],
    ["Đoạn văn ghi mẫu có sẵn thay vì AI", "Phép kiểm số đã chặn, hoặc AI đang tắt, hoặc hết trần", "Đây là hành vi đúng. Mở tab Cài đặt AI xem trạng thái rồi giải thích"],
    ["Màn hình chậm khoảng 20 giây", "Đang đọc dữ liệu thật từ Business Central", "Nói trước khi bấm; hoặc bấm Đọc lại từ BC trước buổi họp để làm nóng bộ nhớ đệm"],
    ["Không còn đơn liên công ty để diễn màn 16", "Đơn trước đã nhận xong", "Làm ba bước diễn trọn vòng ở cuối màn 16: duyệt một đề xuất đặt mua mới, gửi sang Marou, rồi bấm Marou xuất kho"],
    ["Trợ lý nhắc một đơn cũ không nằm trong kịch bản", "Đơn đó xuất kho từ hôm trước mà chưa ai post nhận", "Đừng bối rối, đó là đúng việc trợ lý phải làm. Duyệt luôn cho nó, hoặc nói rõ đây là đơn tồn từ hôm trước"],
  ], [3.4, 4.2, 4.4]));
  c.push(...ghiChu("Phương án cuối cùng nếu mạng hỏng: đổi dải nguồn sang dữ liệu mô phỏng. Toàn bộ mười sáu màn vẫn diễn được, "
    + "chỉ khác là số liệu mô phỏng và không ghi gì vào Business Central.", "Mất mạng giữa buổi"));

  return c;
}

(async () => {
  await build(
    "Demo script: UC2 Inventory Health và trợ lý vận hành",
    "Runbook cho người trình diễn: chuẩn bị, mười sáu màn, câu trả lời sẵn và phương án dự phòng",
    {
      headerLeft: "NaviWorld", headerRight: "Marou • Demo script • Nội bộ",
      footer: `Demo script UC2 · Bản 1.0, ${NGAY}`,
      cover: ["Người đọc: người trình diễn và người hỗ trợ kỹ thuật trong buổi họp",
        "Môi trường: Business Central NWV01, hai company NWV-MAROU và NWV-DAKAO",
        `Soạn ngày ${NGAY}. Bộ dữ liệu đã tính lại với Work Date 17/09/2026, đúng ngày demo.`,
        "Đi kèm bộ slide 12; slide có speaker note, tài liệu này có thao tác."],
    },
    noiDung(),
    __dirname + "/13 Marou POC - Demo script (noi bo).docx",
  );
})();
