/**
 * Speaker note cua bo slide rut gon 17/09 (v7) ra file Word de Dung cam tay khi trinh bay.
 * Noi dung doc thang tu note trong file pptx (note_17_09.json, sinh tu docs/note_slide_17_09.py qua deck v7), khong viet lai.
 * Moi slide: tieu de slide, phan "Nói" (doc len), phan "Ghi chú" (cho nguoi trinh bay).
 * Chay: cd docs; node build_note_17_09.js
 */
const fs = require("fs");
const { p, h2, bullet, build, luuY } = require("./lib_brand");

const NOTE = JSON.parse(fs.readFileSync(__dirname + "/note_17_09.json", "utf8"));

function noiDung() {
  const c = [];
  for (const s of NOTE) {
    c.push(h2(`Slide ${s.so} · ${s.tieu_de}`));
    s.noi.forEach((d) => c.push(p(d)));
    s.ghi.forEach((g, i) => c.push(...luuY(g, i === 0 ? "Ghi chú" : "")));
  }
  return c;
}

(async () => {
  await build(
    "Speaker note: buổi demo 17/09/2026",
    "Lời nói cho từng slide của bộ slide rút gọn v7, kèm ghi chú cho người trình bày",
    {
      headerLeft: "NaviWorld", headerRight: "Marou • Speaker note • Nội bộ",
      footer: "Speaker note · slide rút gọn v7 · 17/09/2026",
      cover: ["Người đọc: người trình bày",
        "Phần in thường là lời nói; khung ghi chú là để nhắc mình, không đọc lên",
        "Đi kèm: Marou POC - slide demo (ban ngan, 17-09 v7).pptx và demo script bản 3.1"],
    },
    noiDung(),
    "C:/Users/dungdt.NWV/Demo-Marou/Marou POC - speaker note (17-09, v7).docx",
  );
})();
