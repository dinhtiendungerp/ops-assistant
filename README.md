# Marou Ops Assistant, POC A + D (NaviWorld)

POC cho RFP của Marou Chocolate (IT & Digital Transformation, 20/08/2026): UC1 dự báo, UC2 sức khỏe tồn kho và truy xuất lô,
UC5 bổ sung hàng cho cửa hàng (POC A), UC10 trợ lý AI và dashboard (POC D). Chạy trên Business Central có LS Central 28.

Đọc trước:

| Cần gì | Đọc |
|---|---|
| Bức tranh tổng, kịch bản demo theo vai trò, cách từng phần xử lý số liệu | `docs/08 Marou Ops Assistant - Kien truc, muc dap ung UC va kich ban demo (noi bo).docx` |
| Sự thật đã kiểm, bẫy đã gặp, lịch sử quyết định | `CLAUDE.md` |
| Prompt mẫu theo vai trò | `python/assistant/goi_y.py`, `docs/demo/goi-y.json` |

## Kiến trúc bốn lớp

1. **Dữ liệu**: bảng chuẩn của BC và LS. App mở ra ngoài qua API page chỉ đọc.
2. **Tính toán**: code AL trong BC (`al/MarouAgentFoundation`) và module Replenishment của LS. Không gọi model.
3. **Đề xuất và người duyệt**: bảng `NWV Agent Proposal`, trạng thái luôn vào Proposed; duyệt thì BC tạo Transfer Order.
4. **Trợ lý**: `python/assistant` (FastAPI, web console, MCP server). Đọc số đã tính, không tự tính lại.

`python/bc_agent` giữ bản Python của các công thức AL để đối chiếu độc lập (`uc1-`, `uc2-`, `uc3-reconcile`).

## Cấu trúc

```
al/MarouAgentFoundation   app sản phẩm "NWV Marou Agent" (phụ thuộc LS Central), id 70100-70249, 70270-70299
al/MarouDemoSetup         app chỉ dùng trên sandbox "NWV Marou Demo Setup": post dữ liệu demo, cấu hình LS, id 70250-70269
al/MarouDataReadiness     đo độ phủ dữ liệu (chưa build)
al/MarouDemoData          sinh dữ liệu bằng AL (đã thay bằng đường import file, giữ để tham khảo)
python/assistant          trợ lý: core, nlu, dinh_tuyen, planner, skills/, channels/web.py, static/index.html, mcp_server
python/bc_agent           client BC (S2S, OData), mock + fixtures, inventory.py, forecast.py, supplier.py, cli
python/tests              pytest
tools/                    sinh dữ liệu demo, cấu hình LS, chụp màn hình, build AL
demo-data-nwv/            bộ dữ liệu demo đã import vào company NWV
docs/                     tài liệu (.docx dựng bằng build_*.js), ảnh demo, kiến trúc
```

---

## 1. Cài đặt máy dev

| Cần | Để làm gì |
|---|---|
| Git, Python 3.12 | Bắt buộc. Đã chạy thử trên Windows với Python 3.12. |
| VS Code + extension AL Language | Chỉ khi sửa hoặc build app AL. |
| Node.js 20+ và `npm install -g docx` | Chỉ khi dựng lại tài liệu `.docx` (`cd docs; node build_08.js`). |
| Google Chrome | Chỉ khi chụp lại ảnh demo (`node tools/chup_man_hinh.mjs`). |

```powershell
git clone https://github.com/dinhtiendungerp/ops-assistant.git
cd ops-assistant\python
python -m venv .venv
.venv\Scripts\activate                 # macOS/Linux: source .venv/bin/activate
pip install -r requirements.txt
copy .env.example .env                 # macOS/Linux: cp .env.example .env
```

`requirements-tools.txt` chỉ cần cho `tools/forecast_lab.py` và `tools/cat_linh_vat.py`.

## 2. Chạy bằng dữ liệu mô phỏng (không cần BC, không cần key)

`.env` vừa chép để sẵn `BC_MODE=mock` và `LLM_MODE=scripted`, nên chạy được ngay.

```powershell
cd python
python -m pytest -q                                                  # toàn bộ test phải qua
python -m uvicorn assistant.channels.web:app --port 8188 --reload
```

Mở http://localhost:8188, chọn vai ở cột trái, bấm thẻ gợi ý trên màn hình chào hoặc nút trong nhóm Kịch bản demo.
Dải nguồn dữ liệu trên cùng cho biết đang đọc dữ liệu mô phỏng hay Business Central.

Giới hạn của bản mô phỏng: câu "vì sao LS đề xuất ..." cần nhật ký tính của LS nên chỉ trả lời được khi nối BC; câu yêu
cầu mở chỉ đi lại được ba bản ghi đã duyệt (tiệc 150 khách, 220 khách, kho mưa dột).

## 3. Chạy trên Business Central thật (environment NWV01 của NaviWorld)

Environment NWV01, company NWV đã có đủ app, dữ liệu demo và Entra app. Dev chỉ cần secret.

1. Xin **client secret** của Entra app (tên secret "Marou") từ người phụ trách dự án, qua kênh an toàn. Không gửi qua chat,
   không commit, không chụp màn hình.
2. Sửa `python/.env`:

   ```ini
   BC_MODE=api
   BC_TENANT_ID=bfea8d1a-c0a1-45fd-ba95-903daff0cb05
   BC_CLIENT_ID=70b548dd-6795-4dcc-9a19-7e3809f8f06b
   BC_CLIENT_SECRET=<secret vừa nhận>
   BC_ENVIRONMENT=NWV01
   BC_COMPANY_NAME=NWV
   ```

3. Kiểm kết nối, lệnh này chỉ đọc:

   ```powershell
   cd python
   python -m bc_agent.probe
   ```

   Probe báo lần lượt: lấy được token chưa, thấy company chưa, đọc được từng API page chưa.
4. Chạy trợ lý như mục 2. Dải trên cùng phải ghi "Đang đọc Business Central NWV01 / NWV" và ngày chốt 18/09/2026.
   Có thể bấm "Dữ liệu mô phỏng" / "Business Central" trên dải đó để đổi nguồn mà không sửa `.env`.

Lưu ý khi QA trên BC thật:

- Brief của vai điều phối và nút Duyệt **ghi thật vào BC** (đề xuất Proposed, Transfer Order Open). Sau khi thử phải từ
  chối đề xuất hoặc xoá Transfer Order tạo thử, vì Transfer Order Open làm lệch lần tính tiếp theo của LS.
- Muốn số khớp tài liệu thì Work Date trên BC là 18/09/2026 và các bảng kết quả đã được tính (mục 5).

## 4. Bật AI (Azure OpenAI)

Mặc định trợ lý không gọi model. Các câu trả lời bằng rule, kịch bản đã duyệt và bản ghi không cần key.

1. Xin **API key** của resource Azure OpenAI `Marou` (Azure portal, resource Marou, Keys and Endpoint), qua kênh an toàn.
2. Sửa `python/.env`:

   ```ini
   LLM_PROVIDER=azure
   AZURE_OPENAI_ENDPOINT=https://marou.openai.azure.com
   AZURE_OPENAI_DEPLOYMENT=gpt-4.1-mini
   AZURE_OPENAI_API_KEY=<key vừa nhận>
   ```

   `AZURE_OPENAI_DEPLOYMENT` là tên deployment, phải giữ đúng `gpt-4.1-mini` để sổ chi phí tính đúng giá.
3. Kiểm key: `python tools/check_azure_openai.py` (chạy từ thư mục gốc repo). 401 là sai key, 404 là sai tên deployment,
   429 là hết quota theo phút.
4. Bật AI theo một trong hai cách:
   - Trên giao diện: chọn vai Dũng (quản trị), tab Cài đặt AI, bật công tắc. Tắt lại cũng ở đó.
   - Từ lúc khởi động: đặt `LLM_MODE=live` trong `.env`.

Chi phí được chặn bởi `AGENT_DAILY_BUDGET_USD` (mặc định 2) và `AGENT_TOTAL_BUDGET_USD` (mặc định 10). Chạm trần thì trợ
lý tự về rule, không báo lỗi. Một câu hỏi mở tốn khoảng 6 đến 14 nghìn token.

## 5. Dựng trên một environment BC khác

Chỉ cần khi không dùng NWV01. Chi tiết từng bẫy ở `CLAUDE.md`.

1. **Entra app** (Microsoft Entra admin center, App registrations): single tenant, tạo client secret, API permissions
   Dynamics 365 Business Central, Application: `API.ReadWrite.All` và `Automation.ReadWrite.All`, grant admin consent.
2. **Trong BC**, page Microsoft Entra Applications: New, dán Client ID, State = Enabled, gán permission set:

   | Permission set | Để làm gì |
   |---|---|
   | `NWV AGENT RUN`, `NWV AGENT REVIEW` | Đọc bảng kết quả, ghi đề xuất, duyệt |
   | `NWV Marou Data API` | Đọc API page dữ liệu (Item Ledger Entry, Item, Location ...) |
   | `NWV AGENT LS READ` | Đọc kết quả LS Replenishment, Forecast Entry, CTKM |
   | `NWV AGENT LS CALC`, `NWV Marou Demo Setup` | Chỉ sandbox: tính LS, dựng dữ liệu demo |
   | `D365 AUTOMATION`, `EXTEN. MGT. - ADMIN` | Publish app qua Automation API |

   Nếu BC trả HTTP 403 kèm số bảng của LS Central (đã gặp 10000788 khi đọc Item, 10000700 khi ghi đề xuất), tạo permission
   set tenant chứa `TableData <số bảng> = R` và gán thêm cho Entra app. Câu lỗi của BC luôn ghi rõ số bảng.
3. **Build và publish app AL**: mở `al/MarouAgentFoundation` và `al/MarouDemoSetup` trong VS Code, `AL: Download Symbols`
   (cần symbol Base Application 28 và LS Central 28 của environment đó), `AL: Package`, rồi `AL: Publish`. Hoặc publish bằng
   `python python/tools_bc.py upload <file .app>` (Automation API `extensionUpload`, Microsoft ghi là sẽ bỏ ở 2027 release
   wave 1). `tools/build_al.sh` là script build dòng lệnh trên máy người viết, phải sửa đường dẫn `alc.dll` trước khi dùng.
4. **Dữ liệu demo và cấu hình LS** (chạy trong thư mục `python`, chỉ trên sandbox):

   ```powershell
   python ../tools/repost_demo.py preview        # xem trước; reset / master / import / post xoá và post lại sổ kho
   python ../tools/ls_replen_setup.py apply      # master data LS, min-max, Retail Forecast, lịch sự kiện, CTKM
   python ../tools/supplier_demo.py apply        # đơn mua và phiếu nhận demo cho UC3
   ```

5. **Tính kết quả**: đặt Work Date 18/09/2026, page `NWV Agent Setup` bấm Run Inventory Health, Run Forecast Accuracy
   (bật Publish LS Forecast), Run Supplier Scorecard; rồi `python ../tools/ls_replen_setup.py calc`.
6. **Đối chiếu**: `python -m bc_agent.cli uc1-reconcile`, `uc2-reconcile --from al`, `uc3-reconcile`. Cả ba phải báo khớp.

## 6. Biến môi trường

| Biến | Mặc định | Ý nghĩa |
|---|---|---|
| `BC_MODE` | `mock` | `mock` dữ liệu mô phỏng, `api` Business Central thật |
| `BC_SOURCE` | `api` | `api` custom API page của app, `odata` web service khai tay (dự phòng) |
| `BC_TENANT_ID`, `BC_CLIENT_ID`, `BC_CLIENT_SECRET` | | Entra app S2S |
| `BC_ENVIRONMENT`, `BC_COMPANY_NAME` | | Environment và company BC |
| `LLM_MODE` | `scripted` | `scripted` không gọi model, `live` gọi model từ lúc khởi động |
| `LLM_PROVIDER` | `azure` | `azure` hoặc `anthropic` |
| `AZURE_OPENAI_ENDPOINT`, `AZURE_OPENAI_DEPLOYMENT`, `AZURE_OPENAI_API_KEY` | | Azure OpenAI |
| `ANTHROPIC_API_KEY` | | Chỉ khi `LLM_PROVIDER=anthropic` |
| `AGENT_DAILY_BUDGET_USD`, `AGENT_TOTAL_BUDGET_USD` | `2`, `10` | Trần chi phí AI |
| `AGENT_SHADOW_MODE` | `true` | Việc policy cho tự làm chỉ báo trước, không làm |
| `MCP_KEYS` | | `khoa:user_id,...` cho MCP server gọi từ máy khác |
| `AGENT_LOG_DIR` | `./runs` | Sổ chi phí, cài đặt, kịch bản đã lưu, log từng lần chạy |

## 7. Lệnh hay dùng

```powershell
cd python
python -m pytest -q                                      # test
python -m bc_agent.cli make-fixtures                     # sinh lại dữ liệu mô phỏng từ demo-data-nwv
python -m bc_agent.probe --json --sample 2000            # kiểm BC (luôn gọi BC thật)
python ../tools/ls_knowledge_coverage.py                 # tỷ lệ nhận dạng nhật ký tính LS trên BC
python -m uvicorn assistant.channels.web:app --port 8188 --reload
```

## 8. Lỗi hay gặp

| Hiện tượng | Nguyên nhân và cách xử lý |
|---|---|
| Dải đỏ "Mất kết nối tới trợ lý" / "Failed to fetch" | Máy chủ đang khởi động lại (`--reload` sau khi sửa file Python). Đợi vài giây, tự hết. |
| `BC_MODE=... khong hop le` | Chỉ nhận `mock`, `live`, `api`. |
| `BC_MODE=live nhung thieu bien` | Thiếu biến BC trong `.env`, xem mục 3. |
| HTTP 403 kèm số bảng LS | Entra app thiếu quyền đọc bảng đó, xem mục 5 bước 2. |
| Trợ lý trả lời "Giải thích theo LS Replenishment chỉ có khi nối Business Central" | Đang ở dữ liệu mô phỏng. |
| Câu mở trả lời "chưa trả lời được" | AI đang tắt hoặc chạm trần chi phí, xem mục 4. |
| Azure trả 429 | Hết token mỗi phút của deployment; đợi hoặc nâng TPM trên Foundry. |
