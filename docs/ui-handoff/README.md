# Làm lại UI cho Marou Operations Assistant

Gói này đủ để một người, hoặc một AI khác, sửa hay làm lại giao diện mà không cần đọc phần còn lại
của dự án. Nghiệp vụ, dữ liệu và phân quyền giữ nguyên; chỉ giao diện được thay.

Bản cập nhật ngày 13/09/2026 tối. Gói zip do `tools/goi_ui_handoff.py` đóng, mẫu API do
`tools/sinh_api_mau.py` sinh, cả hai đọc thẳng từ chỗ thật trong repo.

## Trong gói có gì

| Tệp | Chỗ thật trong repo | Vai trò |
|---|---|---|
| `files/index.html` | `python/assistant/static/index.html` | Toàn bộ giao diện trong một tệp: HTML, CSS, JavaScript. 1.633 dòng, 115 KB. Không framework, không build step. **Đây là tệp cần sửa.** |
| `files/web.py` | `python/assistant/channels/web.py` | Hợp đồng API. Chỉ đọc, không sửa. |
| `api-mau.json` | `docs/ui-handoff/api-mau.json` | Phản hồi JSON thật của 22 lượt gọi API, mỗi mảng cắt còn 2 phần tử. Có cả mẫu lỗi 400 và 403. Dùng cái này thay vì đoán hình dạng dữ liệu. |
| `files/mascot*.png` | `python/assistant/static/` | Linh vật nền trong suốt: `mascot.png` cả người 440px cho màn hình chào; ba cái đầu 128px `mascot-san-sang`, `mascot-suy-nghi`, `mascot-hoan-tat`. Máy chủ phục vụ tại `/<tên>.png`, tên khác trả 404. Hiện ba cái đầu **giống hệt nhau** vì ảnh linh vật mới chỉ có một khuôn mặt; muốn ba trạng thái khác nhau thì cần ảnh mới. |

## Chạy để xem kết quả

Cần repo đầy đủ để chạy máy chủ. Người nhận gói chỉ sửa `index.html` rồi gửi lại tệp đó.

```bash
cd python
python -m uvicorn assistant.channels.web:app --port 8188 --reload
```

Mở `http://localhost:8188`. `index.html` được trả với `Cache-Control: no-store`, sửa xong F5 là thấy.
Mặc định chạy trên dữ liệu mô phỏng, không cần Business Central, không cần khoá API.

## Ràng buộc phải giữ

**Một tệp, không build step.** Không thêm React, bundler hay thư viện tải từ CDN. Font Google Fonts
đang dùng có fallback Georgia và Segoe UI khi không có mạng.

**Không tính lại con số.** Mọi con số do Business Central tính bằng AL, trợ lý chỉ đọc lại. Giao
diện được định dạng, không được cộng trừ hay suy ra số mới.

**Phân quyền theo vai trò.** Hai tab **Nhật ký agent** và **Cài đặt AI** chỉ hiện với vai trò `admin`
(người dùng demo `dung.admin`). Máy chủ trả 403 cho vai trò khác, nên ẩn ở giao diện là để gọn,
không phải để bảo mật. Nút Duyệt chỉ có tác dụng với `dispatcher` và `supply_chain`.

**Đổi vai trò thì quay về tab Trò chuyện.** Dũng yêu cầu ngày 13/09.

**Lỗi phải hiện ra.** Khi Business Central từ chối, máy chủ trả 502 kèm nguyên văn câu lỗi (câu đó
nêu đích danh bảng thiếu quyền). Lỗi 400 và 403 trả `{"detail": "..."}`. Giao diện in nguyên văn,
không nuốt lỗi.

**Giờ hiển thị theo GMT+7.** Máy chủ trả thời gian UTC dạng ISO. Giao diện đổi sang
`Asia/Ho_Chi_Minh` bằng hàm `gioTin()`, không dùng giờ máy người xem.

**Không tạo API giả.** Nghiệp vụ nào chưa có đường API thì không dựng dữ liệu mẫu cho đẹp.

**Không in tên hàm, tên bảng, tên biến môi trường ra màn hình người dùng.** Người đọc là nhân viên
cửa hàng và điều phối, không phải developer.

## Cấu trúc màn hình hiện tại

- **Thanh trên** 64px "MAROU / Operations", dưới là **dải báo nguồn dữ liệu** (mô phỏng hay BC thật,
  environment, company, số dòng, ngày chốt) với nút đổi nguồn và nút Đọc lại từ BC.
- **Cột trái 250px:** bốn mục không gian làm việc (Trò chuyện, Sức khỏe tồn kho, Nhật ký agent,
  Cài đặt AI), chọn vai trò kèm chấm báo tin mới, kịch bản demo, khối "Cách hệ thống hoạt động".
- **Giữa:**
  - *Trò chuyện:* thanh đoạn chat (mỗi vai trò nhiều đoạn), màn hình chào có linh vật và 4 thẻ gợi ý
    khi đoạn còn trống, bong bóng tin, thẻ nghiệp vụ (đề xuất chuyển hàng có ô sửa số lượng và nút
    Duyệt/Từ chối, bậc thang, brief, câu trả lời của planner kèm nút "Trả lời đúng / Chưa đúng /
    Hỏi lại bằng model"), bong bóng "đang xử lý", nút Trả lời một tin cụ thể, ô soạn tự cao
    44 đến 160px, nút Brief cạnh ô nhập.
  - *Sức khỏe tồn kho:* số lớn theo tầng, thanh công cụ, bảng dòng, trang Chi tiết lô.
  - *Nhật ký agent (admin):* KPI trong ngày, bảng câu hỏi ngoài kịch bản với nút "Lưu thành kịch bản"
    và khung xem trước mẫu, danh sách kịch bản đã duyệt có công tắc bật tắt, bảng quyết định.
  - *Cài đặt AI (admin):* bật tắt AI, token và chi phí, trần chi phí, câu nào cần model, policy và câu chữ.
- **Cột phải 340px** "Theo dõi xử lý": đề xuất trong BC, Transfer Order, việc đang theo dõi; khay
  "Điều khiển demo (không thuộc sản phẩm)" thu gọn dưới cùng.

Điểm gãy: dưới 1180px bỏ cột phải xuống dưới, dưới 860px xếp một cột và cho cả trang cuộn. Chưa có
drawer cho điện thoại. Grid item cấp một phải có `min-width:0`, thiếu là trang tràn ngang.

## Vòng đời dữ liệu

`poll()` mỗi 2 giây đọc `/api/inbox`, `/api/state`, `/api/policy`. Chỉ một vòng chạy tại một thời
điểm, xếp tối đa một vòng kế tiếp. Máy chủ nhớ bảng kết quả 60 giây, lịch sử bán 15 phút.

## Danh sách đường API giao diện dùng

| Method | Đường | Dùng để |
|---|---|---|
| GET | `/api/users` | Danh sách vai trò |
| GET | `/api/inbox?user=&after=` | Tin của đoạn chat đang mở; mỗi tin có `card` (thẻ, có `actions[].id`), `reply_to`, `trich` |
| POST | `/api/message` | Gửi tin. Body `{user, text, reply_to?}` |
| POST | `/api/action` | Bấm nút trên thẻ. Body `{user, verb, ref, payload}`, `verb` là `actions[].id`. Trả `{delivered, con_mo}`; `con_mo` true là bị từ chối, phải bật lại nút |
| POST | `/api/brief` | Brief sáng nay. Body `{user, text:""}` |
| GET / POST | `/api/doan-chat` | Liệt kê đoạn chat `?user=`; POST `{user, conv_id?}` mở đoạn cũ hoặc đoạn mới |
| GET | `/api/state` | Chế độ, nguồn dữ liệu, chi phí, đề xuất, chứng từ, việc theo dõi, `tin_ra` cho chấm báo |
| GET / POST | `/api/mode` | Đọc và đổi nguồn dữ liệu. Body `{bc: "mock"｜"live"｜"env"}` |
| GET | `/api/policy` | Mô tả các dòng policy, mọi vai trò |
| GET | `/api/uc2/summary` | Sáu tầng sức khỏe tồn kho |
| GET | `/api/uc2/lines?tier=` | Dòng theo tầng |
| GET | `/api/uc2/trace?line_id=` | Chi tiết một lô |
| GET | `/api/uc2/readiness` | Độ phủ dữ liệu |
| POST | `/api/lam-moi` | Bỏ bản nhớ, đọc lại từ BC |
| GET | `/api/nhat-ky?user=` | Nhật ký agent. Chỉ admin |
| POST | `/api/kich-ban/xem-truoc` | Lập mẫu kịch bản từ một câu hỏi. Body `{user, cau_hoi_id}`. Chỉ admin |
| POST | `/api/kich-ban` | Lưu kịch bản. Body `{user, cau_hoi_id, tra_loi_mau?}`. Chỉ admin |
| POST | `/api/kich-ban/bat` | Bật tắt kịch bản. Body `{user, id, bat}`. Chỉ admin |
| GET | `/api/usage?user=` | Token, chi phí, trạng thái AI. Chỉ admin |
| POST | `/api/ai` | Bật tắt AI. Body `{on, user}`. Chỉ admin |
| POST | `/api/tran` | Trần chi phí. Body `{user, ngay_usd, cong_don_usd}`. Chỉ admin |
| GET / POST | `/api/policy-setup?user=` | Policy và câu chữ. Chỉ admin |
| POST | `/api/reset` | Dựng lại trợ lý |

Thuộc khay điều khiển demo, không phải sản phẩm: `/api/clock`, `/api/autonomy`, `/api/brief_all`,
`/api/self_review`, `/api/kpi`, `/api/followups`. `/mcp` là cổng cho client AI khác, giao diện không dùng.

FastAPI tự sinh tài liệu kiểu dữ liệu ở `http://localhost:8188/docs`.

## Kiểm trước khi coi là xong

1. Ba độ rộng 1920×1080, 1440×900, 390×844: không tràn ngang, ô nhập luôn bấm được.
2. Đổi vai trò: tên, quyền, dữ liệu đổi theo; về tab Trò chuyện; hai tab admin biến mất với vai trò khác.
3. Đoạn chat trống (hiện màn hình chào), đoạn có sẵn, sau tin đầu tiên, khi máy chủ trả lỗi.
4. Enter gửi, Shift+Enter xuống dòng, bộ gõ tiếng Việt không bị Enter cắt ngang.
5. Thẻ đề xuất: sửa số rồi Duyệt; bị từ chối thì nút bật lại.
6. `cd python && python -m pytest -q` vẫn 260 test qua. Giao diện không có test riêng, con số này chỉ
   để chắc không đụng nhầm nghiệp vụ.
