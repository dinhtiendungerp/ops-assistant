const { build } = require("./lib");
const { part1 } = require("./build_plan_06");
const { part2 } = require("./build_plan_06_p2");
const { part3 } = require("./build_plan_06_p3");
const { part4 } = require("./build_plan_06_p4");

build(
  "UC2 Inventory Health: kế hoạch sản phẩm hoàn chỉnh và các phương án",
  "Từ tổng thể tới chi tiết: xương sống AL, cửa vào lớp AI, đo lường, lịch, effort và điểm cần quyết.",
  {
    header: "NaviWorld Vietnam | Marou POC | UC2 kế hoạch",
    footer: "Bản 1.0, 10/09/2026",
    cover: [
      "Soạn: Đinh Tiến Dũng, Principal Consultant",
      "Ngày: 10/09/2026",
      "Người đọc: nội bộ NaviWorld, để chọn phương án trước khi viết đề xuất gửi Marou",
      "Trạng thái tính năng Microsoft tra ngày 10/09/2026, nguồn ở Phụ lục B. Tra lại trước khi ký",
      "Effort là ước tính nội bộ, chưa phải báo giá",
    ],
  },
  [...part1, ...part2, ...part3, ...part4],
  __dirname + "/06 UC2 Inventory Health - Ke hoach san pham va phuong an.docx",
);
