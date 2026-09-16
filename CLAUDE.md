# Marou POC - brief cho phien lam viec

Doc file nay truoc khi lam bat cu viec gi trong thu muc nay.

## Viec dang lam

NaviWorld tra loi Request for POC Proposal cua Marou Chocolate (phat hanh 20/08/2026).
Dung (Principal Consultant) chu tri. Nguoi doc moi thu viet ra la dan tu van ERP va ban lanh
dao, khong phai developer.

Luu y de nham nhat cua du an: Marou co **hai luong yeu cau khac nhau**, noi dung khong khop.
Mail recap cua CFO thang 6/2026 thien ve tai chinh. RFP thang 8/2026 do IT & Digital
Transformation soan, thien ve Supply Chain va Retail. Khi Dung hoi "yeu cau cua Marou" thi
phai xac dinh dang noi luong nao, chua ro thi hoi lai, dung gop hai luong lam mot.

## Moi truong ky thuat

| Muc | Gia tri |
|---|---|
| Tenant | `bfea8d1a-c0a1-45fd-ba95-903daff0cb05` (tenant demo, CONTOSO M365x8772913) |
| BC environment | `NWV01`, ban 28.4.53241.53312, co LS Central |
| Company dich | `NWV-MAROU` (san xuat) va `NWV-DAKAO` (ban le) tu 15/09/2026; `NWV` la company goc da sao chep |
| Entra app (S2S) | client `70b548dd-6795-4dcc-9a19-7e3809f8f06b`, secret ten `Marou` het han 3/10/2027 |

Company `NWV` co day du master data (865 item, 32 location, Item Tracking Code) va **khong co
mot dong Item Ledger Entry nao**. Dac diem nay quan trong, xem muc "Su that da kiem".
So location doc that qua API ngay 11/09/2026 la 32, khong phai 33.

Cac company khac trong environment: CRONUS, DEMO, NWV-DEMO, NWV-DEMO-06/2026, NWV-TRAINING,
TRAINING, Van Demo, WMS, WMS Demo.

Moi truong cu (tenant NaviWorld `3b5ff753-...`, environment `SandboxVN`, company `Marou`)
da bo, khong dung nua.

Secret nam trong `python/.env` tren may Dung. Khong dan secret vao chat, khong chup man hinh no.

## Repo git

Tu 14/09/2026 thu muc nay la repo git, remote `https://github.com/dinhtiendungerp/ops-assistant` (private, nhanh `main`),
de chia se cho dev NaviWorld QA. `.gitignore` loai: `python/.env`, `runs/`, `.alpackages/`, `unpacked/` (source Microsoft
va LS, ban quyen cua ho), goi `.app` va `out/`, `_to_delete/`, `Claude outputs/`, `demo-data/`, `demo-data-cronus/`, file zip,
anh va app.json rac o thu muc goc. Truoc moi lan push kiem khong file nao chua gia tri secret cua `.env`.
README.md la huong dan cho dev (cai dat, chay mo phong, noi BC, nhap key, bat AI, dung environment moi). Da thu clone sach,
venv moi, `pip install -r requirements.txt`: 502 test qua, tro ly chay. `_LSAdapter_chua_build` da xoa (khong dung, trung id 70270).

## Cau truc thu muc

```
AL/Marou/
  al/MarouAgentFoundation/  APP SAN PHAM, ten app la `NWV Marou Agent`, id 70100-70249 va 70270-70299.
                            Tu 1.1.0.0 phu thuoc LS Central va chua cua vao LS Replenishment.
                            Lop tinh toan UC2 bang AL, bang de xuat, trang nguoi duyet, Job Queue,
                            cong 9 API page chi doc (truoc kia la app MarouDataApi rieng, da gop vao).
                            Da build 1.0.0.0 ngay 12/09/2026, khong loi khong canh bao.
  al/MarouDemoSetup/        APP SANDBOX, id 70250-70269. Tao batch NWVDEMO, noi rong Allow Posting
                            From/To, post theo tung thang, khoa lo demo. Da build 1.0.0.0.
  al/MarouDataReadiness/    do do phu du lieu. Chua build, probe ben Python da lam viec nay.
  _to_delete/superseded/    MarouDataApi va MarouAgentProposals, ca hai da gop vao app san pham.
  al/MarouDemoData/         sinh du lieu demo bang AL. Chua build, da duoc thay bang duong Excel.
  _to_delete/superseded/MarouAgentLSAdapter  da gop vao app san pham ngay 13/09/2026 (khong tach nhieu app).
  python/bc_agent/          lop doc BC, lop tinh toan UC2, va uc2.py noi hai cai do lai.
                            demo_data.py doc bo demo-data-nwv; make_fixtures.py dung mock cua tro ly
                            tu chinh bo do (xem "Mock cua tro ly").
  python/assistant/         tro ly cua C: skill, planner, replays, giao dien web, so chi phi
  python/tests/             502 test, chay bang `python -m pytest` trong thu muc python
  tools/                    sinh du lieu demo
  demo-data-nwv/            bo du lieu sap import, kem README-import.md
  docs/                     tai lieu
AL/Demo/                    project rieng, chua .alpackages (symbol cua NWV01) va base app da giai nen
```

`AL/Demo/Unpacked` chua vai nghin file .al cua base app. **Khong bao gio build trong thu muc do**,
AL compiler se gom het va chet. Chi lay `.alpackages` tu do.

## Kien truc da chot, ban 12/09/2026

Lop tinh toan chay **bang AL trong BC**, dung nhu so do UC2 trong `docs/`. Job Queue chay hang dem,
ket qua nam trong bang cua BC, nguoi nghiem thu mo page ma doi chieu. Khong co dich vu ben ngoai
nao phai chay thi con so moi hien ra.

Ban brief truoc ghi "chot cua 3, logic nam o Python", ly do la Foundation chua build duoc. Ly do do
den tu container Cowork khong co AL compiler chu khong phai tu code. Ngay 12/09/2026 build lai
tren may Dung: 25 file, 2.179 dong, khong mot loi nao. Tien de cu het hieu luc, nen quay ve so do.

Fact ve MCP van dung va khong lien quan den chuyen tren: BC MCP Server chi ho tro OAuth
authorization code kem PKCE, moi thao tac chay duoi danh tinh nguoi dang nhap, khong co duong
client credentials. Nen chat thi qua MCP, con viec chay khong nguoi truc thi qua S2S hoac
Job Queue, hai thu do khong the la mot.

Bon lop, khong duoc gop:
1. **Du lieu**: bang chuan cua BC. Custom API page chi doc phoi ra ngoai cho lop 4 va cho ban
   doi chieu bang Python.
2. **Tinh toan**: `NWV Inv. Health Calc`, `NWV Replenishment Calc`, `NWV Discount Gov. Calc`,
   viet bang AL, chay trong BC. Nguong nam tren page `NWV Agent Setup`, Marou tu sua, khong sua code.
3. **De xuat va nguoi duyet**: bang `NWV Agent Proposal` va page `NWV Agent Proposals`. Agent chi
   ghi vao day, trang thai luon vao o Proposed. Duyet mot de xuat dieu chuyen thi BC tao Transfer
   Order o trang thai Open. Khong co duong tat cho agent ghi thang vao chung tu.
4. **Agent va tro ly**: `python/assistant/`, `python/bc_agent/runner.py`. Doc so da tinh, dat cau
   hoi, chuan bi de xuat. Khong tu tinh lai con so.

Lop Python trong `bc_agent/inventory.py`, `forecast.py`, `uc2.py` giu lai lam **ban doi chieu doc
lap**: chay tren cung du lieu, phai ra cung con so voi lop AL. Lech la biet ngay mot trong hai sai.
Do khong con la duong chay chinh nua.

Hai app, khong hon:
- **`al/MarouAgentFoundation`**, ten app la `NWV Marou Agent`. App san pham. Chua lop 1, 2, 3.
- **`al/MarouDemoSetup`**, ten app la `NWV Marou Demo Setup`. Chi dung tren sandbox, vi no ghi vao
  General Ledger Setup va Item Journal. Khong bao gio cai len he thong that cua khach.

Moi de xuat gui Marou phai giao duoc ket qua ke ca khi phan agent bi truot.

## Su that da kiem, dung suy dien lai

Doc truc tiep trong source cua Base Application 28.4.53241.54346, lay tu `AL/Demo/.alpackages`
(package co kem source vi `includeSourceInSymbolFile` bat).

- `Item.Table.al` field 6500 `Item Tracking Code`, OnValidate goi `TestNoEntriesExist`. Ham do
  bao loi neu item **co bat ky Item Ledger Entry nao**, khong phai chi dong con mo. Vi vay khong
  gan duoc tracking code cho item da co phat sinh. Company NWV chua co dong nao nen gan duoc.
- Bang `Lot No. Information` (6505) **khong co** Expiration Date, cung khong co Expiration Action
  Date. Han dung chi nam tren Item Ledger Entry.
- Bang `Item Ledger Entry` (32) **co** Item Category Code. Khong can join sang Item de nhom.
- API chuan v2.0 resource `itemLedgerEntry` **khong co** locationCode, lotNumber, expirationDate,
  remainingQuantity. Day la ly do bat buoc phai co custom API page.
- 145 ten truong dung trong `MarouDataApi` da doi chieu voi source base app, khong truong nao sai
  va khong truong nao dang obsolete.
- `Item Tracking Code` `LOTALLEXP` co san trong NWV: Lot Specific Tracking bat, Man. Expir. Date
  Entry Reqd. bat, **Strict Expiration Posting tat**. Phai giu nguyen trang thai tat, vi du lieu
  demo co lo qua han va lo ban ra khi da gan han.
- Dong `General Posting Setup` (`` , `RETAIL``) co san, COGS 7190, Inventory Adjmt. 7170.
  Nen Item Journal post voi Gen. Bus. Posting Group de trong chay duoc.
- Trong NWV01, **moi lenh doc bang Item deu keo theo code cua LS Central doc bang 10000788
  `LSC Attribute Setup`**. Thieu quyen do thi tra ve HTTP 403 "the current permissions prevented
  the action". Da thu ca API chuan v2.0 `items` lan custom API page, hai duong bao giong het nhau,
  nen khong phai loi cua page 70200. Cach xu ly da chay duoc: tao permission set tenant
  `NWVMAROULSC` chi co `TableData 10000788 = R` roi gan them cho Entra app. Khong dua bang do vao
  permission set cua extension, vi lam vay la buoc extension phu thuoc LS Central.
- **LS Central con doi quyen khi GHI, khong chi khi doc.** POST vao `agentProposals` tra HTTP 403
  `(TableData 10000700 LSC Retail Setup Retail Setup Read: LS Central)`. Cung ho voi chuyen
  bang 10000788 luc doc Item. Cach xu ly giong het: them `TableData 10000700 = R` vao permission
  set tenant `NWVMAROULSC` roi gan lai cho Entra app. Khong dua vao permission set cua extension,
  vi lam vay la buoc extension phu thuoc LS Central. Bat duoc ngay 13/09/2026: brief cua dieu
  phoi va nut "Ghi de xuat vao BC" deu chet im, vi ca hai deu ghi de xuat.
  Bai hoc rong hon: moi thao tac moi tren BC that co the keo them mot bang cua LS Central, va
  cau bao loi cua BC luon noi ro so bang. Phai de cau do len den man hinh.
- Trong tam ma can lot tracking, den 11/09/2026 chi `33310` da co `LOTALLEXP` tren Item Card,
  bay ma con lai chua co. Cau "ba ma da co roi" trong README-import.md ban cu la sai, da sua.
- **Item Journal Line xoa Lot No. neu batch khong bat "Item Tracking on Lines".** Doc trong
  `ItemJournalLine.Table.al`: field 6501 `Lot No.` OnValidate goi `CheckItemTracking()`; ham do
  goi `IsItemTrackingEnabledInBatch()` doc co `Item Journal Batch."Item Tracking on Lines"`
  (field 6500), thay tat thi chay `ClearTracking(); ClearDates(); exit`. `ClearTracking()` xoa
  `Serial No.` va `Lot No.`.
- **Nhung han dung thi song, va day la ly do du lieu nhin rat kho hieu.** `ClearDates()` chi xoa
  field 44 `Expiration Date` (ngay het hieu luc cua recurring journal) va `Warranty Date`.
  Han dung that cua lo nam o field 6506 `Item Expiration Date`, field do `Editable = false` va
  **khong co OnValidate nao**, nen khong ai xoa no.
- **O nhap han dung cua lo la field 44 `Expiration Date`, khong phai 6506.** Tooltip cua field 44
  noi ve recurring journal nen rat de hieu nham, nhung khi batch bat `Item Tracking on Lines` thi
  no chinh la o nhap. Chuoi day du, da doc het:
  `ItemJnlPostBatch` dong 975 goi `CreateItemTrackingLines`; `ItemJnlLineReserve.CreateItemTracking`
  dong 446 lay `TempTrackingSpecification."Expiration Date" := ItemJournalLine."Expiration Date"`
  roi tao Reservation Entry; `ItemJnlPostLine` dong 5814 dat 6506 tu tracking specification;
  dong 2021 chep 6506 sang Item Ledger Entry. Nghia la 6506 **duoc suy ra**, ghi thang vao no la
  di duong tat: khong co Reservation Entry nen khong co Lot No. Information.
  Cung o `CreateItemTracking` dong 437: item khong co Item Tracking Code thi ham thoat ngay,
  Lot No. tren dong bi bo qua ma khong bao loi nao.
  Ban xuat "Table data for Item Journal Line" cua BC dung field 44, tuc dung san, khong phai
  doi ten cot gi ca. Dung ngay 12/09/2026 da chi ra cho nay khi toi viet nguoc. Ket qua sau khi post: Item Ledger Entry co
  Expiration Date day du ma Lot No. rong sach.
- **Dong xuat cua mot lo phai tim du so luong dang mo cua DUNG lo do tai DUNG dia diem.**
  `ItemJnlPostLine.Codeunit.al` dong 2081: dong xuat cua mat hang lot specific ma sau khi ap dung
  van con `Open` thi bao `Item Tracking Serial No. %1 Lot No. %2 for Item No. %3 Variant %4 cannot
  be fully applied.` Kiem ton theo cap Item x Location la chua du, phai kiem theo tung lo.
- **API tra ten Option da ma hoa.** `Negative Adjmt.` ve thanh `Negative_x0020_Adjmt_x002E_`,
  option rong ve thanh `_x0020_`. Quy tac: `_xHHHH_` la ma Unicode cua mot ky tu. Giai ma o
  `bc_data.unescape_option`, ap cho cac truong trong `OPTION_FIELDS`. Khong giai ma thi moi phep
  so `entry_type` ben Python deu truot.
- **API tra ngay rong la `0001-01-01`, khong phai rong.** Do la gia tri 0D cua BC. De nguyen thi
  moi phep tru ngay ra so am bay tram nghin. Chuan hoa o `bc_data.norm_date` va lop thu hai o
  `inventory._d` (nam nho hon hoac bang 1 thi coi la khong co ngay).
- **Ngay trong `$filter` la Edm.Date, viet tran khong dau nhay.** `postingDate ge 2026-06-14`
  chay duoc; boc dau nhay thi BC tra HTTP 400 "Found operand types 'Edm.Date' and 'Edm.String'".
  Xu ly o `odata._literal`.

Page ID hay dung: 15 Locations, 31 Items, 38 Item Ledger Entries, 40 Item Journal,
102 Item Journal Templates, 262 Item Journal Batches, 810 Web Services, 2500 Extension Management,
6501 Item Tracking Entries, 6502 Item Tracking Codes, 6505 Lot No. Information Card,
6508 Lot No. Information List, 6512 Item Tracking Code Card.

## Ket luan ve Copilot Studio, da chung minh bang chay thu

- Harness GitHub Copilot **khong nap duoc** tool cua connector hay MCP luc chay. Trace cua chinh
  no chi liet ke bash, view, create, edit, grep, glob, skill. Da loai tru ba gia thuyet khac
  (Dynamic mode, chua publish, session cu) truoc khi ket luan.
- Harness Standard cong BC MCP o **Static Tool Mode** chay duoc, tra ve du lieu that trong mot
  luot, khoang 30 giay.
- Dynamic Tool Mode gay `ConnectorTimeoutError` sau 120 giay va gay vong lap hoi lai tham so.
  Viet "khong hoi lai tham so ky thuat" vao Instructions **khong chan duoc**, vi do la slot
  filling cua nen tang chu khong phai lua chon cua mo hinh. Chinh sach phai cuong che trong code.

## Quy uoc dau ra

Tieng Viet, tru khi Dung yeu cau tieng Anh hoac dang soan van ban gui khach nuoc ngoai.
Van phong theo skill `natural-writing`: khong gach ngang dai, khong mui ten thay tu noi,
khong in dam giua cau, khong cau ket rong kieu "qua do giup nang cao hieu qua".
Giu nguyen ten dinh danh ky thuat, khong dich: Item Ledger Entry, Demand Forecast,
Cust. Ledger Entry, Agent Designer, Copilot Credits.

Khi dua so lieu hay tinh nang san pham Microsoft thi tra web truoc roi moi viet. Agent va Copilot
cua Microsoft thay doi theo tung release wave. Khong hua tren tinh nang preview.

Co tai lieu hoac source thi doc, khong suy dien. Suy dien tu kinh nghiem ve cach BC thuong hoat
dong nghe rat troi va sai rat kho phat hien.

File ghi chu `.md` khong phai tai lieu chinh thuc, khong bao gio liet ke no la deliverable hay
trich no lam bang chung gui PM hay khach.

## Nhung loi da mac trong phien truoc, dung lap lai

1. Doan page 6506 la Lot No. Information. Thuc te 6505 la card, 6506 la Item Tracking Comments.
2. Khai them web service cho Item va Location trong khi API chuan da co san.
3. Ket luan BC khong luu web service chi vi o tim kiem cua page 810 khong ra ket qua. Phai kiem
   bang cach cuon danh sach hoac doc `$metadata`, khong tin o tim kiem.
4. Tu doi sang company CRONUS ma khong hoi, trong khi Dung da chi dinh company NWV.
5. Mo phong dut hang bang cach ep luong ban ve 0. Nhin vao so lieu thi cua hang van con ton ma
   khong ban duoc, khong ai hieu tai sao, va thuat toan phat hien cau bi cat cut khong co gi de
   bam vao. Dung cach: ngung chuyen hang, de ton tu rut ve 0.
6. Tinh nhu cau cua kho bang cach dem dong Sale. Kho xuat hang bang Negative Adjmt. nen se ra
   ket luan kho khong co nhu cau va moi lo o kho roi vao nhom cham luan chuyen.
7. De xuat bo sung du ban 14 ngay cho mat hang han dung 2 ngay. Muc ton muc tieu phai bi chan
   theo han dung.
8. Import Item Journal co Lot No. ma khong bat `Item Tracking on Lines` tren batch. Mat sach
   11.615 so lo, nhung han dung van con nen nhin vao khong thay co gi sai. Da xay ra that trong
   lan import dau tien vao company NWV ngay 12/09/2026. App `NWV Marou Demo Setup` 1.0.1.0 bat
   co nay ngay trong `EnsureTemplateAndBatch()`, nut 1 lo luon.
9. Import Item Journal truoc khi gan Item Tracking Code cho Item. `TestNoEntriesExist` chan
   viec gan tracking code khi item da co Item Ledger Entry, nen sheet "27 Item" cua Config
   Package **im lang khong ap duoc** cot do. Thu tu dung: gan tracking code truoc, post sau.
10. So chuoi voi ten Option doc tu API ma khong giai ma. Ngay 12/09/2026 lan doi chieu dau tien
   tren BC that ra 42 rui ro dut hang va 13 cham luan chuyen, trong khi ban offline ra 58 va 4.
   Du lieu dung, phep so sanh sai: `entry_type` ve la `Negative_x0020_Adjmt_x002E_` nen toan bo
   dong xuat kho bi bo khoi phep tinh nhu cau. Mat mot vong doi chieu moi tim ra.
11. Coi `0001-01-01` la mot ngay. `observed_shelf_life` ra -739.787 ngay cho moi mat hang khong
   co han dung, roi muc ton muc tieu bi chan xuong 1 ngay: 21 de xuat bao la "chan theo han
   dung" thay vi 9. Ban Python con thieu dieu kien `shelf_days > 0` ma ban AL da co, nen hai ben
   lech. Sua cong thuc o mot ben thi phai doi chieu ngay ben kia.
12. Doc `BC_MODE` bang cach so `== "live"` trong khi brief va `.env` ghi `BC_MODE=api`. Tro ly
   am tham chay tren fixtures, con man hinh in lai chinh bien moi truong nen nhin vao tuong dang
   chay tren BC that. Gio co `Settings.bc_live` nhan ca hai ten va bao loi neu gia tri la nao
   khac, va `/api/state` tra ve che do co hieu luc chu khong phai ten bien.

## Cach chay

```
cd python
python -m pytest -q                      # 502 test
python tools_bc.py extensions | upload <app> | ws <Ham> '<json>'   # quan tri BC qua S2S: publish, goi web service
python -m bc_agent.probe --json --sample 2000   # kiem S2S va do san sang du lieu
                                                # probe luon goi BC that, khong phu thuoc BC_MODE
python -m bc_agent.cli uc2                      # chay UC2 tren du lieu that qua custom API page
python -m bc_agent.cli uc2-reconcile            # so voi ket qua tinh offline
python -m bc_agent.cli uc1-reconcile            # so NWV Forecast Accuracy tren BC voi forecast.backtest_bc
python -m bc_agent.cli uc3-reconcile            # so NWV Supplier Scorecard tren BC voi supplier.scorecard
python ../tools/ls_replen_setup.py apply | calc # master data LS (ca min-max UC5) roi tinh lai LS
python ../tools/ls_knowledge_coverage.py        # ty le nhan dang nhat ky tinh LS tren BC
python -m bc_agent.cli run inventory_health     # chay kich ban voi BC_MODE=mock
LLM_MODE=live python -m bc_agent.cli run inventory_health   # goi model that, Azure OpenAI mac dinh
cd ..
python tools/make_demo_data.py --out <thu muc>  # sinh lai bo du lieu demo
python tools/uc2_offline.py                     # tinh lai demo-data-nwv/uc2-expected.json
python tools/fill_config_package.py <package> <ket qua>   # do du lieu vao Config Package
python tools/fill_ile_lots.py <file table data>  # dien Lot No. vao file Item Ledger Entry xuat tu BC
```

Bien moi truong trong `python/.env`: `LLM_MODE`, `LLM_PROVIDER=azure`, `BC_MODE=api`, `BC_SOURCE=api`, `BC_TENANT_ID`,
`BC_CLIENT_ID`, `BC_CLIENT_SECRET`, `BC_ENVIRONMENT=NWV01`, `BC_COMPANY_NAME=NWV`.
`BC_SOURCE=odata` la duong du phong doc web service khai tay, dung khi extension chua publish.

**Chay tro ly thi them `--reload`.** `index.html` duoc phuc vu voi `Cache-Control: no-store` nen
sua xong F5 la thay, nhung sua file Python thi phai khoi dong lai. Ngay 13/09/2026 mat mot vong
vi Dung khoi dong lai truoc khi duong `/mascot.png` duoc them, roi anh linh vat 404 ma nhin vao
tuong code sai. `--reload` tu khoi dong lai khi file doi, het han loi nay:

    cd python; python -m uvicorn assistant.channels.web:app --port 8188 --reload

PowerShell 5.1 khong nhan `&&` lam dau noi lenh, phai dung `;`.

## Da xong ngay 11/09/2026

1. Build `al/MarouDataApi` bang dong lenh va publish 1.0.1.0 len NWV01. `alc.exe` cua extension
   AL 18.0 doi .NET 10, may chi co 8.0.31 o Program Files, ban 10.0.12 nam trong globalStorage
   cua extension vscode-dotnet-runtime. Symbol lay tu `AL/Marou/.alpackages`.
2. Gan permission set `NWV MAROU DATA API` va `NWVMAROULSC` cho Entra app.
3. Viet hai module con thieu trong `python/bc_agent`: `auth.py` (TokenProvider) va
   `odata_client.py` (ODataWSClient, doc $metadata). `bc_data.py` import chung tu truoc nhung
   chua ai viet, nen toan bo test khong collect duoc. Viet lai them `tests/test_bc_data.py`.
4. Chay probe tren BC that. Chin entity set doc duoc het. 865 item, 32 location, 38 item category,
   22 stockkeeping unit, 8 dong don mua, 6 dong don ban. Item Ledger Entry, Lot No. Information
   va Value Entry deu rong vi chua import.
5. Do day master data tren 865 item: 84,5% co Item Category, 6,9% co Item Tracking Code,
   10,5% co Reorder Point, 1,2% co Safety Stock Quantity.

## Da chot ngay 12/09/2026

- Cua vao lop AI: **cua C**, tro ly do NaviWorld host, tuc `python/assistant/`. Tro ly doc so
  da tinh qua API cua app `NWV Marou Agent` bang `bc_client.py`, khong tu tinh lai.
- Ngay neo demo: **18/09/2026**. Lop AL dung `WorkDate()`, hom demo dat Work Date la du.
- Bon loi trong lop AL da sua ngay 12/09: nhu cau tai kho tinh bang luong xuat, loai ngay cau
  bi cat cut, chan muc ton muc tieu theo han dung, WorkDate() thay Today().
- **Nhu cau tai kho trung tam = tong luong xuat**, ke ca khi kho co ban si tai cho. Chot chieu
  12/09 sau khi mock lo ra syrup 30091: kho vua ban si vua chuyen di, chi dem Sale thi ra 0,81
  chai mot ngay va days of cover 735, trong khi ca he thong tieu thu 3 chai mot ngay. Quy tac:
  dia diem la `Central Warehouse Code` thi luon lay Outflow (Sale + Negative Adjmt. + Transfer);
  cua hang co dong Sale thi lay Sale; cua hang khong co dong Sale thi lay Outflow. Sua cung luc
  `NWV Demand Calc.Build()` (them tham so CentralWh) va `inventory.py` (`Thresholds.central_warehouse`).
  Ket qua mong doi doi tu 31/38/48/4/1/44 sang **31/38/58/4/1/34**, 22 de xuat, 9 bi chan boi
  han dung: muoi dong o kho tu Healthy sang StockOutRisk vi nhu cau kho gio tinh dung. App
  `NWV Marou Agent` 1.0.0.0 da build lai 18:38 ngay 12/09 (chua publish, nen khong bump version). Logic nhu cau nam
  o codeunit `NWV Demand Calc` (70110), dung chung cho Inventory Health va Replenishment,
  cong thuc chep tu `inventory.py`. Chua doi chieu tren BC that, xem viec 4 duoi.
- Ban QA day du: `docs/QA-UC2-2026-09-12.md`.
- Model cua cua C: **Azure OpenAI `gpt-4.1-mini`**, tu 12/09/2026, cho ca tro ly lan vong lap
  agent. Claude chi con la duong doi chieu (`LLM_PROVIDER=anthropic`). Cua D sau demo dung cung
  resource Azure do.

## Mock cua tro ly, dung lai tu bo du lieu demo ngay 12/09/2026

Truoc do fixtures cua tro ly la mot the gioi bia (WH-HCM, S-CALMETTE, S-DANANG, MAR-MINI-24)
khong lien quan gi den bo du lieu demo, nen tro ly chay mock ra mot bo so con BC that se ra bo so
khac. Gio `python -m bc_agent.cli make-fixtures` doc thang `demo-data-nwv/` (qua
`bc_agent/demo_data.py`, cung bo doc voi `tools/uc2_offline.py`) va chay `bc_agent/inventory.py`
tren do. Ket qua: 167 dong Inventory Health dung 45/32/47/4/1/38, 77 dong Replenishment
Suggestion trong do 22 co rui ro, khop `uc2-expected.json`. Hom import xong chi doi
`BC_MODE=api`, khong doi gi khac.

Nhung thu khong co trong bo demo van la du lieu dung nhung dat tren dung cua hang va mat hang:
POS discount log (nhan vien NV22 tai S0002 ngay 14/09, NV03 tai S0001 ngay 16/09) va hai lan tro
ly da chuyen hang cho cap S0001 x 33200 (TO-0944 ngay 21/06, TO-0977 ngay 19/07) sau hai dot
ngung chuyen hang trong kich ban demo. Cap do la cap dung cho bac thang chan doan: 12 tuan qua
dut 14 ngay trong 2 dot, da chuyen 2 lan, nen len bac 2.

Nguoi dung demo: `lan.s0001`, `minh.s0002`, `tuan.s0005`, `ha.s0010`, `thao.s0013`,
`hung.dieuphoi`, `kho.w0003`, `trang.sc`, `thu.retailops`. Ten cua hang bang loi de go trong tin
nhan nam o `STORE_LABEL` trong `assistant/core.py`: Sieu thi Nam = S0001, Sieu thi Bac = S0002,
Nha hang = S0005, Quan ca phe = S0010, Web store = S0013.

Ba ban ghi replay viet lai tren danh muc cua company NWV: KB-1 tiec 150 khach o nha hang (kho
khong con mon khong chay nao du 150 ma khong pha ke hoach bo sung, cho du la kem, hoi lai tiec co
giu lanh duoc khong), KB-3 chot dung kem va 220 khach (lay 100 Choco pillar tu lo can date
L260829-33310-SD o S0010, 120 tu kho, 220 Choco nuts tu kho), KB-2 syrup 30091 o kho bi uot.
Con so trong cau tra loi van doc lai tu du lieu luc chay.

Gia von cua company NWV kieu Cronus, mot mon tu 0,45 den 7,5, khong phai dong Viet Nam. Nen
`fmt_vnd` khong ghi don vi nua, va nguong policy P-01 la gia von duoi 200 (P-06 duoi 100). Tren
he thong that cua Marou thi Marou dat lai.

`sales_history` gio loc theo cua so `days` that, ca mock lan live. Truoc day mock tra ca 180 ngay
bat ke `days`, nen `sales_rate` ra cung mot tong cho 7 va 14 ngay.

Ly do phan tang va rationale de xuat trong `inventory.py` gio viet tieng Viet co dau, trung tung
chu voi Label trong `NWV Inv. Health Calc`, de mock va BC that hien cung mot cau.

### Giao dien web, viet lai chieu 12/09/2026

`python/assistant/static/index.html`, theo mau Dung dua: ba cot, thanh tren "MAROU / Operations",
cot trai la khong gian lam viec (Tro chuyen, Suc khoe ton kho, Brief buoi sang), chon vai tro,
kich ban demo, va muc "Cach he thong hoat dong" thu gon; giua la hoi thoai hoac Suc khoe ton kho;
phai la "Theo doi xu ly" (de xuat trong BC, Transfer Order, viec dang theo doi) va khay
"Dieu khien demo (khong thuoc san pham)" thu gon duoi cung. Font Playfair Display cho tieu de,
Inter cho chu, tai tu Google Fonts, khong co mang thi roi ve Georgia va Segoe UI.

The de xuat chuyen hang ve theo mau: cau tom tat, mat hang, o Tu va Den, bon con so lon, o sua so
luong va ly do tu chuoi, hai nut Duyet chuyen hang va Tu choi, dong nguon so lieu duoi cung. The
khac (bac thang, dieu tra, brief) dung khung chung voi bang chi tiet.

Man hinh Suc khoe ton kho: con so lon o bon tang xau, sau o tang bam de loc, thanh cong cu
"Tat ca cac tang / Do phu du lieu / Chay kich ban demo" gio doi mau dung nut dang chon (loi cu:
nut Do phu du lieu khong bao gio sang), o tim theo mat hang, ma, lo. Bam mot dong mo trang
"Chi tiet lo": Nguon so lieu, Quy tac phan tang (dung tai dieu kien dau tien khop), Lich su ban
doi chieu. Bang Nguon so lieu doc con so cua chinh dong ket qua (avg, so ngay het hang bi loai,
co so Sale hay Outflow), khong tinh lai tho nhu truoc.

Da kiem tren trinh duyet: hoi thoai, the de xuat, bac thang, brief, Suc khoe ton kho, Do phu
du lieu, Chi tiet lo. Phim Enter gui duoc tin.

### Sua theo phan hoi cua Dung, toi 12/09/2026

- **Xung ho tro ly doi tu em/anh chi sang toi/ban**, 16 file gom ca ba ban ghi kich ban.
- **Khong in ten ham ra chat.** Nut "Xem toi da tra gi" gio ke bang tieng Viet: "Doc toc do ban
  cua Flavored syrup (30091) tren toan he thong, 90 ngay gan nhat, doc duoc 1 dong." Ten ham chi
  con trong log `runs/`. Cung don ba cau con ke ten bien moi truong, ten bang va ten nguoi noi bo
  ra cho nguoi van hanh doc.
- **Ten dia diem** trong `STORE_LABEL`: S0001 Cua hang Quan 1, S0002 Cua hang Ha Noi, S0005 Nha
  hang Thao Dien, S0010 Quan ca phe Da Nang, S0013 Cua hang truc tuyen, W0003 Kho trung tam.
  Doi ten xong lo ra mot loi: chu "cua hang" nam trong `_STOPWORDS` nen bi cat khoi `item_text`,
  tro ly khong con nhan ra cua hang nao. Gio do ten tren CAU GOC chu khong tren phan da cat.
- **Lich su ban doi chieu** thanh bang ngay va so luong kem dong tong, va mot cau noi ro no dung
  de lam gi. Dong cua kho trung tam ghi ro dang dem luong xuat chu khong phai chi dong Sale.
- **Chay kich ban demo** co dai vang ghi buoc may tren sau, ten buoc, va mot cau noi buoc do
  chung minh dieu gi, kem nut Dung. Truoc day man hinh tu nhay ma khong ai biet dang xem gi.
- **Brief thanh nut canh o nhap**, khong con la tab. Truoc day phai bam hai lan moi ra du lieu vi
  no vua la tab vua la hanh dong.
- **Bo nut "Sua so luong".** Nguoi duyet sua so ngay trong o roi bam Duyet; neu so khac so de
  xuat thi di duong `edit`, van kiem tran ton kho nguon nhu cu.
- **Kich ban noi tiep tu chay cai truoc no.** "Sep chot kem, 220 khach" la cau tiep cua "Tiec 150
  khach"; bam thang vao no thi truoc day tro ly tra loi khong hieu. Gio khai bang truong `sau`,
  bam mot nut la chay ca hai dung thu tu. Nut dang chon moi duoc to, truoc day nut dau bi to cung.
- **Giai trinh chiet khau khong nhan cau rong.** Go "ok" thi cau hoi van treo va tro ly hoi lai;
  cau giai thich that o tin nhan sau khong con bi roi vao HELP. Noi "toi nham" thi mo lai dung
  exception do de go lai, chung nao Retail Ops chua ket luan. Ba test trong `test_assistant.py`.
- **Nut bi lech.** Hai cho. Mot: `.scn` co `width:100%` ma `.scn.sub` them `margin-left:14px`,
  nen nut kich ban noi tiep thua ra 14px o ben phai va khong thang hang voi bon nut kia; sua bang
  `width:calc(100% - 14px)`. Hai: `.actions` de o nhap va nut chung mot hang flex, o nhap cao hon
  nut nen `align-items:center` day nut xuong giua, va nut thu ba xuong hang moi thi lech tiep.
  Gio tach lam hai hang, `.inputs` roi `.buttons`, o nhap chia deu bang `flex:1 1 230px`.
- **Placeholder khong duoc chep lai label.** O nhap ghi y het cai nhan ben tren no
  ("Ly do tu choi (neu co)" / "Ly do tu choi (neu co)") thi o do khong noi them duoc gi. Gio
  `GOI_Y` cho mot vi du that: "vd: cua hang ben kia cung dang thieu", "vd: hai tuan do tu dong
  hong nen phai ngung ban".
- Dot doi xung ho em/anh sang toi/ban da thay ca the HTML `<em>` thanh `<tôi>`, ba cho trong
  `index.html` gom mot dong CSS. Trinh duyet van hien dung nen khong ai thay. Da tra ve `<em>`.
- **Dong chu duoi logo bi rot chu.** Cot trai 250px, tru padding con 206px, ma
  "Faiseurs de chocolat au Việt Nam" o 9,5px voi letter-spacing .16em can 244px, nen "NAM" xuong
  hang va roi ra ngoai khung 64px. Ha xuong 8,2px va .105em, them `white-space:nowrap`: do 183px,
  con du cho. Khong duoc cat bot chu, day la dong chu chinh cua Maison Marou.
- **Dai bao nguon con in ten bien moi truong** ra man hinh: "(chon tay, .env dang de BC_MODE=mock)".
  Gio la "(ban vua chon tay; mo lai tro ly thi no quay ve du lieu mo phong)". Trong khay dieu
  khien demo cung vay, "LLM=rule (gpt-4.1-mini)" thanh mot cau doc duoc.
- Sua `.actions` thanh hai hang lam vo ba cho trong khay dieu khien demo, vi khay do cung dung
  class do lam mot hang ngang. Da tach ra `.actions.stack`, chi the trong hoi thoai moi lay.
- Con hoi Dung: nut "Da ship" hien chi danh dau trong bo nho tro ly, khong dung gi toi BC. Tren
  he thong that kho vao Transfer Order bam Post Shipment, BC sinh ILE va tu doi trang thai, tro
  ly chi doc. Chua chot de nut do trong luong chat hay chuyen xuong khay dieu khien demo.

### Trang Cai dat AI, them ngay 13/09/2026

Dung yeu cau tu kiem soat duoc chi phi thay vi hoi NaviWorld. Tab thu ba trong khong gian lam
viec, `showTab('caidat')`, tra loi ba cau: AI dang bat hay tat, da tieu bao nhieu, con bao nhieu.

- **Token la so dem that**, doc lai tu `response.usage` sau moi luot goi, luu tung dong trong
  bang `llm_calls`. **Tien la uoc tinh** theo bang gia trong `assistant/budget.py`. Trang noi ro
  cho nay, vi hoa don that cua Azure moi la con so cuoi cung.
- Bon phep cong moi trong `Budget`: `tong(day)`, `theo_ngay(n)`, `theo_viec(day)`, `theo_model()`.
  `token_tong` cong ca cache read va cache write, khong chi vao cong ra.
- **Cong tac bat tat AI** di dung con duong ma het tran ngan sach van di: `Budget.ai_off` lam
  `allow()` tra False, va ca nam cho goi model deu da kiem `allow()` truoc khi goi. Khong them
  nhanh moi nao trong luong xu ly.
  Bat lai thi `Assistant.set_ai(True)` dung lai `LiveNLU`, `LivePlanner`, `LiveEvidence` va nguoi
  viet cau. Ba ham `build_nlu`, `build_planner`, `evidence.build` gio nhan tham so `live`;
  `live=None` van la theo `LLM_MODE` nhu cu.
  **Khac voi doi nguon du lieu: bat tat AI KHONG dung tro ly moi**, nen hoi thoai, bo nho va
  baseline con nguyen.
- `validate_live_llm()` nem `SystemExit`. Bat AI khi thieu credential ma khong bat lai thi
  bam nut la sap server, nen `/api/ai` bat `BaseException` va tra ly do ra man hinh.
- Tran chi phi sua duoc ngay tren trang, co tac dung ngay, va tro ve mac dinh khi khoi dong lai.
- API: `GET /api/usage`, `POST /api/ai {on}`, `POST /api/tran {ngay_usd, cong_don_usd}`.
- Da chay that mot luot tren Azure de kiem dong ho: 207 token vao, 26 token ra, 0,000124 do,
  ghi dung vao muc `nlu`, va so con lai cua tran ngay giam dung bang do.
- **Chi vai tro quan tri mo duoc.** Them nguoi dung demo `khanh.it`, role `admin`, va
  `core.ADMIN_ROLES`. An tab di la chua du: nam duong API deu goi
  `_chan_neu_khong_phai_quan_tri` va tra 403, vi ai go dung duong dan cung goi duoc.
  Tren ban demo nguoi dung tu chon minh la ai nen day la ranh gioi vai tro, chua phai xac thuc;
  tren he thong that no gan vao danh tinh Entra va permission set cua BC.
- **Cai dat luu tren dia, o `runs/cai-dat.json`** (`assistant/caidat.py`). Tran chi phi, cong tac
  AI, nguong policy va cau chu deu nho qua lan khoi dong lai. Cai gi de None thi giu mac dinh cua
  `.env`. `caidat.ap_vao(budget, policy)` goi trong `Assistant.__init__`.
- **So chi phi cung nam tren dia**, `runs/chi-phi.sqlite` (`budget.so_chi_phi`). Truoc day
  `Budget` dung chung connection voi `Memory(":memory:")`, ma bo nho tro ly bi dung moi lan doi
  nguon du lieu hoac khoi dong lai, nen trang Cai dat luon hien 0 do. Dung hoi
  "ro rang da chay roi sao chi phi hom nay chua co" ngay 13/09/2026.
- **Sua policy va cau chu ngay tren trang.** `GET/POST /api/policy-setup`. Moi dong policy doi
  duoc mode (tu lam / dua nguoi duyet / khong bao gio lam) va tran gia tri; them cong tac Shadow
  mode va tran so viec tu lam mot ngay. Ba cau chu sua duoc: chi thi cho model khi viet lai cau,
  cau tro ly noi khi khong hieu yeu cau, cau xac nhan sau khi ghi giai trinh. Sua xong ap ngay,
  khong khoi dong lai.
  Duong ten `policy-setup` chu khong phai `policy` vi `/api/policy` da co san va moi vong poll
  cua MOI vai tro deu goi no de lay mo ta dong policy hien tren the, nen khong gate duoc.
  "Da sua" tinh bang cach so voi ban goc, khong phai bang "co dong trong file cai dat khong":
  bam "Ve cau goc" ghi mot chuoi rong nen dong do van con trong file.
- **Rule va cau mau khong nam tren Azure.** Azure chi chay model. Nguong tang cua UC2 nam tren
  page `NWV Agent Setup` trong BC; policy va cau chu nam o day. Cau hoi cua Dung ngay 13/09.
- 21 test trong `tests/test_caidat.py`, cong `tests/conftest.py` doi so chi phi va file cai dat
  sang thu muc tam de chay test khong dung vao file that.

### Ba cho cham va mot cho lap tin, sua ngay 13/09/2026

Do tren BC that, khong uoc luong.

| Cho | Truoc | Sau | Nguyen nhan |
|---|---|---|---|
| Bam nut Business Central | 137 giay | 24 giay | `kpi._stockout_baseline` goi `sales_history(item, store)` trong vong lap 74 cap, moi luot 1,7 giay. Gio doc mot lan roi nhom trong Python. |
| Doc lich su ban 120 ngay | 18,5 giay | 9,5 giay | Keo ca ban ghi. Gio `$select=postingDate,itemNo,locationCode,quantity`. `BCClient.query` nhan them tham so `select`. |
| Moi vong poll (`GET /api/state`) | 3,4 giay | 0,21 giay | `bc_status()` dem hai bang ket qua bang hai lenh 5000 dong MOI 2 GIAY. Gio nho lai 30 giay, `quen_dem()` khi doi nguon. Vong poll lau hon chu ky poll nen cac vong con chong len nhau; gio chi chay mot vong, xep dung mot vong ke tiep. |

**Go "brief" trong chat ra hai lan cung mot cau.** `handle_message` goi `_deliver` cho ket qua
cuoi cung, con `morning_brief` da tu goi vi no cung la cua vao rieng cua `POST /api/brief`.
Sua bang cach danh dau tung `Delivery` da ghi (`meta["da_ghi"]`) thay vi go bo mot trong hai
tang, vi con vai duong khac cung co hinh nay. `tests/test_khong_lap_tin.py`.

**Nut Duyet bi mo sau khi tro ly tu choi.** Giao dien tat nut ngay khi bam de khong ai bam hai
lan, nhung khong bat lai khi hanh dong bi tu choi (so luong vuot ton, khong du quyen, thieu ly
do), nen nguoi duyet sua so xong khong bam tiep duoc. `POST /api/action` gio tra them `con_mo`
= de xuat van o `Proposed`, tuc khong doi duoc gi; giao dien mo lai nut. Mot co chung cho moi ly
do tu choi, khong doan theo cau tra loi.

## Doi chieu tren BC that, lan dau ngay 12/09/2026

Trang thai company NWV sau khi import va va lot: **24.759 dong Item Ledger Entry, 11.615 dong co
Lot No., 764 lo, khong dong nao lech giua Lot No. va Expiration Date.** Da doc lai qua API de
xac nhan, khong tin vao ket qua cua buoc update.

`python -m bc_agent.cli uc2-reconcile --from python` doc Item Ledger Entry that roi tu tinh:
**trung khop hoan toan** voi bo so luc do (31/38/58/4/1/34, 22 de xuat). Bo so mong doi sau do
doi vi danh sach ma quan ly lo doi, xem muc duoi.
Day la lan dau lop tinh toan chay tren du lieu that thay vi tren bo demo offline.

Bon bay tren duong doc API da sua trong lan nay, xem muc "Su that da kiem": ten Option ma hoa,
ngay 0D, ngay trong `$filter`, va `BC_MODE=api`. Moi cai deu co test trong
`tests/test_option_escape.py`. Tong 174 test.

### Lop AL da chay, va no lo ra mot van de cua du lieu

Chieu 12/09 Dung dat Work Date 18/09/2026 roi bam hai nut. Lop AL ghi **150 dong** Inventory
Health va **74 dong** Replenishment Suggestion, phan tang 18/42/52/4/1/33. Ban offline ra 166
dong va 31/38/58/4/1/34.

Nguyen nhan khong nam o cong thuc, nam o cach hai ben doc ton theo lo:

| | Cach doc ton mot lo |
|---|---|
| Lop AL (dung cach cua BC) | tong `Remaining Quantity` cua dong con `Open` |
| Ban offline va ban Python | tong `Quantity` co dau cua moi dong cua lo do |

Tren mot so cai da tracking lo tu dau thi hai cach nay luon bang nhau, vi BC ap dong xuat vao
dong nhap theo tung lo. O day thi khong, vi **so lo duoc va vao ILE sau khi da post**. Luc post,
Item Application Entry duoc tao khi chua co lo nao, nen BC tru hang theo FIFO tren toan bo
Item x Location chu khong theo lo. Ket qua da do:

- Tong ton theo Item x Location: **0 cap lech**. So tong hoan toan dung.
- Phan bo theo lo: **61 to hop lech**. Vi du `33310` tai W0003 lo `L260823-33310C` tong co dau
  la 250 nhung Remaining Quantity la 0, con lo `L260906-33310C` thi nguoc lai.

Nghia la lop AL doc BC dung, con ban than du lieu trong BC dang mau thuan o muc lo. Va muc lo
chinh la thu UC2 ban. Chi co mot duong sua that: **post lai**. Xoa Item Ledger Entry, Value Entry
va Item Application Entry; gan Item Tracking Code cho 8 ma (luc do ILE rong nen
`TestNoEntriesExist` khong chan nua); publish `NWV Marou Demo Setup` **1.0.1.0**; bam nut 1,
import lai sheet 83, bam nut 2. Lam vay thi Lot No. Information tu sinh va nut 3 chay duoc luon.

### Doi danh sach ma quan ly lo, chieu 12/09/2026

Ban dau chon tam ma theo do dai han dung, trong do co `10000` Milk 1 liter va `10045` Cream
250 ml. Dung bac: khong ai quan ly lo cho sua hop va kem tuoi dong hop. Chon lai theo nghiep vu,
**chin ma**, tat ca deu la thu Maison Marou lam va ban:

| Nhom | Ma |
|---|---|
| Banh tuoi, han 3 den 7 ngay | `33110` Croissant chocolate, `33100` Croissant plain, `33170` Chocolate cake, `33116` Blueberry muffin, `33130` Tiramisu, `33160` Carrot cake |
| Kem, han 180 den 240 ngay | `33310` Choco pillar, `33323` Choco nuts, `33341` Choco bowl |

`TRACKED` trong `tools/demo_scenario.py` la nguon duy nhat cua danh sach nay. Test khong duoc
chep lai no, phai import tu day, neu khong doi danh sach la test bao do ma khong sai gi.

Bo du lieu sinh lai voi cung SEED thi **so luong va ngay khong doi mot dong nao**, da kiem: chay
lai `make_demo_data.py` roi so tung dong, 24.759 dong giong het. `TRACKED` chi quyet dinh co ghi
Lot No. va Expiration Date len dong hay khong, khong dung vao mo phong. Nho vay doi danh sach ma
tracking khong bat buoc import lai toan bo.

Bo so mong doi doi theo, `uc2-expected.json` da cap nhat:

| | Truoc | Sau |
|---|---|---|
| So dong | 166 | **167** |
| Qua han | 31 | **45** |
| Can han | 38 | **32** |
| Rui ro dut hang | 58 | **47** |
| Cham luan chuyen | 4 | 4 |
| Ton thua | 1 | 1 |
| Binh thuong | 34 | **38** |
| De xuat dieu chuyen | 22 | 22 |
| Bi chan boi han dung | 9 | **18** |

Tang qua han va can han manh hon han ban cu (77 dong so voi 69) vi sau ma banh tuoi deu han
3 den 7 ngay. So de xuat bi chan boi han dung tang gap doi, do la diem ban: khong de xuat bo
sung du ban 14 ngay cho mat hang han 3 ngay.

### File import de post lai, da kiem truoc khi giao

`tools/make_journal_import.py` sinh file import, dung dinh dang va dung thu tu cot cua ban
"Table data for Item Journal Line" xuat tu BC, khong them bot cot nao.

    python tools/make_journal_import.py --all --out demo-data-nwv/import-full-journal.txt

**24.759 dong, ca 21 mat hang**, dung khi xoa sach Item Ledger Entry va post lai tu dau. Day la
duong da chon ngay 12/09/2026 sau khi va tung phan hai lan deu vuong. 13.578 dong cua chin ma
trong `TRACKED` co Lot No. va Expiration Date; 11.181 dong cua 12 ma con lai de trong hai cot do.

Ban va tung phan (`--also 10000,10045`, 16.500 dong) van chay duoc, dung khi chi post lai mot so
ma. Hai ma nay phai co trong file vi ILE cua
chung da bi xoa trong dot dau, nhung gio khong con quan ly lo nua. Phai de trong that:
`ItemLedgEntry.CopyTrackingFromItemJnlLine` van chep Lot No. tu dong journal sang ILE ke ca khi
item khong co tracking code, tuc se ra ILE co lo ma Item Card thi khong quan ly lo.

Script tu chan ba loi truoc khi ghi file: Posting Date phai tang dan; khong dong nao duoc lam am
ton o bat ky cap Item x Location nao (98 cap); va khong dong nao duoc lam am ton **theo tung lo**
(3.222 to hop lo x dia diem). Kiem theo lo la bat buoc, xem muc "Su that da kiem": thieu no thi
post bao "cannot be fully applied" ma nhin file khong thay gi sai.

Da kiem bang cach chay lop tinh toan tren dung noi dung file, khong tron gi tu BC: ra dung
**167 dong, 45/32/47/4/1/38, 22 de xuat, 18 bi chan boi han dung**, trung khop
`uc2-expected.json`. 21 ma, 876 lo. Khong dong nao cua ma khong tracking bi dinh lot, va khong
dong nao cua ma tracking bi thieu lot.

#### Ban nho cho cac lenh doc BC, 13/09/2026

`BCGateway.doc(entity_set, conds, ttl, **kw)` nho lai ket qua 60 giay. Moi lenh doc trong
gateway di qua day, cong `uc2._all` va `kpi.baseline`. Chi ap khi chay that; mock doc tu bo nho
san va `MockBCClient.query` tra deepcopy nen nho lai se lam mat tinh chat do.

Ly do: bang ket qua cua AL chi doi khi Job Queue chay hoac co nguoi bam nut, ma mot man hinh
Suc khoe ton kho la ba lenh doc 5000 dong, moi vong poll them hai lenh nua, `items()` va
`unit_cost()` moi lan goi lai doc lai ca bang. Ghi vao BC thi `create_proposal` goi `quen_nho()`.
Nut **"Doc lai tu BC"** tren thanh cong cu (`POST /api/lam-moi`) de bam ngay sau khi chay
Run Inventory Health, khong phai doi het mot phut.

Do tren BC that, giay:

| | Truoc | Sau, lan dau | Sau, lan hai |
|---|---|---|---|
| `/api/uc2/summary` | 2,95 | 0,26 | 0,20 |
| `/api/uc2/lines` | 3,10 | 0,23 | 0,22 |
| `/api/uc2/readiness` | 14,79 | 8,21 | 0,21 |
| `/api/uc2/trace` (chi tiet lo) | ~3,5 | 8,3 | 0,006 |
| `/api/state` (moi 2 giay) | 3,40 | 0,21 | 0,21 |

Ba cho nua sua cung ngay:
- `sales_history` doc theo CUA SO CHUNG (`CUA_SO_BAN = (120, 400)`) roi loc trong Python, thay vi
  hoi BC rieng cho tung cap mat hang x dia diem. Moi trang Chi tiet lo truoc day la mot cau hoi
  rieng 1,7 giay; gio ca trang, brief va planner dung chung mot lan doc.
- `uc2.trace` lay dong tu ban danh sach da nho thay vi mot lenh `GET` rieng (1,5 giay).
- `quen_nho()` nhan tham so `entity_set`. Ban dau `create_proposal` bo HET ban nho, ma brief cua
  dieu phoi tao 10 de xuat lien tiep nen no doc lai moi thu 10 lan: 74 giay cho mot cai brief.
  Ghi de xuat thi chi bang de xuat doi.
- TTL theo bang: `nwvItemLedgerEntries` 15 phut, con lai 60 giay. Cua so 120 ngay mat 8 giay de
  doc va khong co vong poll nao giu no am, nen de 60 giay thi ngoi khong mot phut la lan bam
  tiep theo lai cho 8 giay.

Man hinh do phu con doc ca 400 ngay lich su ban chi de lay ngay ban som nhat. Gio
`gw.ngay_ban_dau_tien()` lay dung mot dong bang `$orderby=postingDate asc&$top=1`, va phan con
lai chi can cua so 90 ngay, cua so ma cac man hinh khac cung doc nen dung chung ban nho.

### Man hinh chao, theo goi Marou-Chat-Design ngay 13/09/2026

Dung dua goi thiet ke (anh redesign, token CSS, brief trien khai). Da lam:
- Bang mau doi sang token cua goi, sat ban cu, them `--icon` cho icon chuc nang.
- `#hero`: loi chao theo ten vai tro dang chon, minh hoa cacao, duong ke vang co hinh thoi,
  luoi 2x2 bon the goi y. Chi hien khi hoi thoai dang chon con TRONG **va** da tai xong hop thu
  (`daTaiHopThu`), de khong nhay man hinh chao ra roi lai bo di.
- Ba the goi y chi DIEN san cau vao o nhap roi dat con tro o cuoi, khong tu gui; dang co ban
  nhap thi giu nguyen. Rieng the "Brief sang nay" chay thang handler brief, giong nut o o nhap:
  nghiep vu nay da co duong rieng, de tro ly doan lai tu mot cau chu thi ra cau tra loi kem hon.
- Composer thanh textarea tu cao 44 den 160px, Enter gui, Shift+Enter xuong dong,
  `isComposing` de bo go tieng Viet khong bi Enter cat ngang. Gui hong thi tra lai cau da go.
- Anh `marou-cacao.png` thu tu 1536x1024 (2,9 MB) xuong 720x480 (0,49 MB), phuc vu o
  `GET /marou-cacao.png` voi cache mot ngay.
- Diem gay: duoi 1180px bo cot phai xuong duoi; duoi 860px xep mot cot, dat `grid-row` bang tay
  va cho ca trang cuon. **Grid item mac dinh la `min-width:auto`** nen phai dat `min-width:0`
  cho cac vung cap mot, neu khong mot phan tu con rong hon man hinh keo ca cot rong theo va
  trang tran ngang 12px. Da kiem 1920, 1440 va 390: khong tran ngang.
- Chua lam: drawer cho dien thoai, va container query (dung media query theo viewport).

### Linh vat, ngay 13/09/2026

Dung dua mot bo nhan dien linh vat (qua cacao co mat, ba trang thai). Anh goc luu o
`docs/linh-vat-goc.png`, `tools/cat_linh_vat.py` cat ra bon tep trong `assistant/static/`:
`mascot.png` (ca nguoi, 440px, cho man hinh chao) va ba cai dau 128px
`mascot-san-sang.png`, `mascot-suy-nghi.png`, `mascot-hoan-tat.png`.

Hai cho de mat thoi gian nhat khi cat, ghi lai de lan sau khong lam lai:
- **Anh goc DA CO san kenh alpha** (45% pixel trong suot). Toi tach nen mot vong roi moi phat
  hien, vi `Image.convert("RGB")` dan anh len nen den nen nhin vao tuong nen la mau dac.
- Chu "MAROU AI ASSISTANT" nam chung khung voi than linh vat, ma mep trai cua than chay tu
  x=363 (canh tay) den x=543 (ban chan) chu khong thang. Xoa theo chin dai chieu cao, moc lay
  tu phep quet alpha tung hang, roi **chi giu mang lien thong lon nhat** de bo net chu sot lai.
- Dau phai cat rieng: de ca nguoi vao vong tron 38px thi khuon mat chi con vai pixel.

`GET /{ten}.png` phuc vu bon tep nay, co cache mot ngay, ten nao khong nam trong danh sach thi
404. Anh cu `marou-cacao.png` da bo.

### Chung minh phan agent, 13/09/2026, lam lai cung ngay

Cau khach chac chan hoi: "tinh AI Agent o dau, toan thay BC tinh va web hien".

**Ca dem da BO.** Ban dau lam `assistant/ca_dem.py` va nut "Chay ca dem". Dung doc lai UC va bac:
ca dem chi chay lai Brief cua dieu phoi theo lo, khong goi model, trong khi tai lieu 04 muc 2 xep
dung loai viec do vao cot "Job Queue lam duoc". Dem no ra tra loi "agent o dau" la tu dua bang
chung agent chi la kich ban. Khach lam 8 tieng thi agent cung khong can chay dem; thu chay dem la
phep tinh AL. Bai hoc: truoc khi dung tinh nang "chung minh agent", doi chieu voi bang ranh gioi
AI va Job Queue o tai lieu 04 muc 2. Agent nam o bon viec: doc rang buoc trong cau tu do, tu chon
doc gi cho cau chua gap, doi ke hoach khi rang buoc doi, hoi lai dung mot cau.

**Tab "Nhat ky agent"** (`assistant/nhat_ky.py`, `GET /api/nhat-ky`) gio doc lai viec THAT trong
ngay: de xuat nao duoc soan, policy nao cho tu lam hay bat hoi, ai duyet, ai tu choi, cau hoi nao
di qua model hay qua kich ban. Khong tu chay gi.

**`docs/lo-trinh-demo-agent.md` ban 2** theo tai lieu 05 muc 8: mo bang con so tien UC2, noi truoc
phan nao khong can model, roi moi toi yeu cau mo va vong hoc kich ban. Ghi chu noi bo.

### Cau ngoai kich ban thanh kich ban da duyet, 13/09/2026

Cau Dung du doan khach hoi: "80% cau hoi la ngoai kich ban, muon chuyen hoa thanh kich ban thi sao".
`assistant/kich_ban.py`, luu o `runs/kich-ban.sqlite` (song qua lan khoi dong lai, test doi sang
thu muc tam trong `conftest.py`). Khong huan luyen lai model:

1. Moi cau di qua planner ghi vao bang `cau_hoi`: cau, chuoi tool kem ket qua, cau tra loi, token,
   nguon (`model`, `ban_ghi`, `kich_ban`, `khong_tra_loi`). The tra loi co nut "Tra loi dung" va
   "Chua dung".
2. Quan tri bam "Luu thanh kich ban". **Code lap mau, khong phai model**: moi con so trong cau tra
   loi phai khop mot o trong ket qua tool (`_chi_muc` sinh duong dan kieu `#locationCode=S0002.qty`,
   `@sum:qty`, `@len`, dung lai `planner._resolve`); mat hang va dia diem nhac nguyen van trong cau
   thanh bien `{item_no}`, `{item_desc}`, `{location}`. So nao khong truy duoc thi bao ra, vi do la
   so model tu tinh. Tham so trong args (90 ngay) la hang so, khong gan vao o ket qua.
3. Cau moi: truoc khi goi NLU cua model, neu rule ra HELP thi thu `kich_ban.khop`. Phai co du bien
   (so ten CHINH XAC, khong so khop mo), phan chu con lai giong tu 0,6 (Jaccard), va moi o so doc
   ra duoc tren du lieu moi; thieu mot dieu la tra ve model. The ghi "kich ban K-001 do Dung duyet,
   khong goi model" kem nut "Hoi lai bang model".
API: `POST /api/kich-ban/xem-truoc`, `POST /api/kich-ban`, `POST /api/kich-ban/bat`, deu chan
khong phai quan tri. 14 test trong `tests/test_kich_ban.py`.

Da chay that tren Azure ngay 13/09/2026 (mock data): cau "so sanh toc do ban Choco nuts giua cac
cua hang trong 30 ngay qua..." het 9.904 token; luu thanh K-001; hoi lai cho Croissant - plain ra
cau tra loi dung so cua Croissant, 0 token. Lan chay that lo ra hai loi ma test gia khong bat:
- **Hai o cung gia tri** (S0005 va S0010 cung 9,1 ngay) thi so cua S0010 bi gan vao o S0005. Gio
  chon o co ma dia diem duoc nhac GAN NHAT phia truoc con so trong cau.
- **Cau ket luan bi dong bang.** "Dia diem ban cham nhat la S0005" lap nguyen chu cho mat hang khac.
  Kich ban dien lai so, khong suy luan lai. Gio bao ra moi cau co tu so sanh hay khuyen nghi de
  nguoi duyet sua thanh cau trung tinh. Day la gioi han that, phai noi voi khach.

### Ba loi lo ra khi chay planner that, 13/09/2026

- **Bat AI ma cau mo co ten mat hang khong bao gio toi planner.** Enum intent cua `LiveNLU` khong co
  loai "yeu cau mo" va prompt khong ta tung intent, nen model ep "so sanh toc do ban Choco nuts..."
  vao STOCK_QUERY va tra mot dong ton kho. Them intent `PLAN` kem mo ta tung intent; `core` dua PLAN
  cho planner.
- **Azure 429 lam sap ca request thanh loi 500.** Deployment dang 10.000 token moi phut, mot cau hoi
  mo can 10 den 12 nghin. `azure_llm._post` gio cho theo `retry-after` roi thu lai mot lan (toi da 20
  giay); `plan.handle` bat loi va noi ro ra chat. **Truoc buoi demo phai nang TPM len it nhat 30.000.**
- **Model doc thua.** Lan dau model goi `list_stock` cho tung cua hang (moi lan 4 den 7 nghin ky tu)
  de tra loi mot cau ve MOT mat hang: 46.000 token roi 429. Sua mo ta tool (hoi mot mat hang thi dung
  `stock_by_item`), them vao SYSTEM cua planner "goi it tool nhat", va `list_stock` gon danh sach lo
  thanh so lo cong lo gan han nhat. Lan sau: 3 tool, 9.904 token.

### MCP server cua tro ly, 13/09/2026

`POST /mcp` tren cung server web (`assistant/mcp_server.py`), MCP Streamable HTTP, JSON-RPC, tra JSON
thang khong mo SSE. Tu viet vi may chua cai goi `mcp`. 10 tool: bay tool doc cua planner (bo
`ask_human`), `inventory_health_summary`, `proposal_status`, `create_proposal`. `create_proposal` ghi
THAT (Proposed), chan so luong vuot ton nguon, chong trung theo reference key `MCP|ma|tu|den`, chay
policy va day the cho nguoi duyet y het luong chat. Khong co tool duyet hay tao chung tu.
Danh tinh: `MCP_KEYS=khoa:user_id,...` trong `.env`; goi tu 127.0.0.1 thi khong can khoa, nguoi dung
lay tu header `X-Marou-User`. Da goi that tren server 8188: initialize, tools/list, tools/call.
Chua thu voi client MCP that (Foundry, VS Code). Foundry va Copilot Studio can dia chi cong khai.
8 test trong `tests/test_mcp_server.py`, co test schema khong dung `anyOf` vi Foundry bao loi schema.

Ten goi cach dang lam: **cua C, tro ly NaviWorld tu host** (tai lieu 06 muc 6).

### So token bi dem doi phan cache, sua 13/09/2026

`prompt_tokens` cua Azure OpenAI DA GOM `prompt_tokens_details.cached_tokens`, con `input_tokens` cua
Anthropic thi khong. `azure_llm.response_to_anthropic` chep thang prompt_tokens nen phan cache bi cong
hai lan. Bang chung: luot goi dau prompt 1.054 ma cached 1.024. Hau qua: bao "46 nghin token" cho mot
cau trong khi that la 27,8 nghin (18,7 nghin la cache, tinh 25% gia), va tien thoi phong hon gap doi.
Dung giat minh "tien dau cho du". Da sua va chinh lai 6 dong trong `runs/chi-phi.sqlite`.
So that: cau hoi mo sau khi sua mo ta tool khoang 6 nghin token gui di, 0,001 den 0,002 USD. Foundry
Monitor ngay 13/09/2026: 54 luot, 109,81K token, uoc tinh 0,03 bang Anh cho toan bo tu truoc toi gio.
Doi chieu so cua tro ly voi Foundry Monitor, dung tin mot minh so tu tinh.

### Brief cua dieu phoi im lang khi de xuat da co, 13/09/2026

Ca 10 dong rui ro da co de xuat trong BC tu lan Brief truoc, nhanh chong tao trung chi `continue`,
nen Hung chi thay "ban duyet tung dong:" roi khong co the nao. Gio de xuat chua duyet hien lai thanh
the ("cho duyet tu 13/09"), nap vao bo nho tro ly de nut Duyet tim thay (`_nap_de_xuat_cu`), va cau
mo dau ke dung: moi, dang cho, dang di, kho het. `gw.approve` va `gw.reject` bo ban nho bang de xuat.
Da chay tren BC that: 10 the, khong ghi them de xuat. `tests/test_brief_dieu_phoi.py`.

### Dinh tuyen de tiet kiem token, 13/09/2026

Bat AI len thi truoc day MOI tin nhan deu di qua model de phan loai, ke ca "brief" hay "sap het
Croissant plain" la nhung cau rule doc duoc chac chan.

`assistant/dinh_tuyen.py`: rule chay TRUOC va khong ton gi, model chi duoc goi khi rule khong
chac. Chac nghia la (1) phan loai ra mot intent that, khong phai HELP, va (2) intent nao can biet
mat hang thi phai tra duoc ma tu chu nguoi go. Cho de sai nhat la (2): rule bat trung tu khoa
nhung khong biet nguoi ta noi ve mon nao, luc do van phai day sang model. Doan sai dat hon goi
model.

`LiveNLU` giu mot bo dem `SoDinhTuyen`, tab Cai dat AI hien "Cau nao can model": bao nhieu cau
tra loi bang du lieu, bao nhieu phai goi model, ty le tiet kiem, va ly do tung nhom.
12 test trong `tests/test_dinh_tuyen.py`.

### De xuat trong BC ma tro ly khong thay, 13/09/2026

`/api/state` va skill `tracking` truoc day chi doc `mem.proposals()`, tuc chi nhung de xuat do
CHINH phien nay tao ra. Mo tro ly ra thay bang rong trong khi BC dang co 61 dong.

`gw.de_xuat()` doc bang `agentProposals` roi doi ten truong sang ten bo nho tro ly dang dung;
`Assistant.de_xuat_gop()` gop hai nguon: trang thai lay theo BC vi BC la so goc, con bo nho bo
sung dong policy da khop va ten mat hang. Mock khong co bang do nen bo nho van la nguon duy nhat.

### Tra loi mot tin cu the, 13/09/2026

Tro ly hoi mot cau, chua kip tra loi thi da co tin khac chen vao, va cau tra loi bi gan nham vao
cau hoi moi nhat. Dung gap dung ca do voi cau hoi giai trinh chiet khau.

Cach lam: bang `messages` them cot `reply_to`; `handle_message(user, text, reply_to)` tra ve tin
goc, lay `ref` cua no roi goi `pending_question(user, ref)` de chon DUNG cau hoi do thay vi cau
moi nhat. Neu tin duoc tra loi chinh la cau hoi dang cho thi ep intent thanh `ANSWER`, khong de
rule doan lai. Hop thu tra kem truong `trich` de giao dien ve lai doan van ban da tra loi.

Giao dien: nut "Tra loi" an trong tung tin, hien khi ro chuot vao; dai trich dan tren o nhap co
nut bo; bong bong cua nguoi dung hien lai doan da trich. 5 test trong `tests/test_tra_loi_tin.py`.

Man hinh chao thu gon lan hai: loi chao gop thanh mot dong, anh 130px. Cao 433px o 1440x860,
luoi goi y cach day man hinh 74px, khong phai cuon.

### Doan chat, 13/09/2026

Moi vai tro co nhieu doan chat, giong cac tro ly khac. Bang `messages` them cot `conv_id`, doan
dang mo cua tung nguoi luu trong `kv` khoa `doan:<user_id>`, va `inbox()` loc theo doan do.
**Tin cu khong mat**, chi la hop thu khong hien; mo lai doan cu la doc duoc het.

Ten doan lay cau dau tien nguoi do go. Doan chua co tin nao thi khong liet ke, de bam "Doan moi"
hai lan khong sinh ra hai dong rong. `GET /api/doan-chat?user=`, `POST /api/doan-chat {user,
conv_id}` (khong co `conv_id` la mo doan moi). 6 test trong `tests/test_doan_chat.py`.

### Bon cho nua theo phan hoi sang 13/09/2026

- **Bam Brief lai sinh de xuat trung.** Truoc day chi so voi bo nho tro ly, ma bo nho bi dung
  moi lan khoi dong lai con BC thi giu. Gio `gw.de_xuat_dang_co()` doc `Reference Key` cua cac
  de xuat con hieu luc TRONG BC, dung trong `brief_for_dispatcher` va `inventory_health.on_propose`.
- **Nut khong bao ket qua.** Dai bao loi gio dung chung cho ca viec chay xong: `baoOk()` to xanh
  va tu tat sau 5 giay, `baoLoi()` to do va de nguyen den khi nguoi dung dong. Gan vao Doc lai
  tu BC, bat tat AI, luu tran, luu policy, luu cau chu, doi nguon du lieu.
- **Man hinh chao chiem cho.** Thu gon con khoang mot nua chieu cao: anh 170px thay vi 260px,
  chu chao 26-38px thay vi 34-52px, the goi y cao 66px thay vi 92px. O 1440x860 gio thay het
  ca bon the ma khong phai cuon.
- **The kich ban noi tiep khong thut vao nua**, chi giu chu "tiep theo" to do. Thut vao thi nhin
  nhu bi lech chu khong doc ra la no phu thuoc cai tren.

### Khong giu ban sao tep trong repo, 13/09/2026

`docs/ui-handoff/files/` truoc day giu mot BAN SAO cua `index.html`, `web.py` va cac anh linh
vat. Dung sua anh trong thu muc do roi thac mac sao web khong doi, vi web doc
`python/assistant/static/`. Da bo thu muc ban sao; `tools/goi_ui_handoff.py` dong goi zip doc
thang tu cho that moi khi can gui.

Bai hoc chung: bo mot tep nhi phan vao hai cho trong cung mot repo la dat bay cho chinh minh.

### Bon cho theo phan hoi cuoi ngay 13/09/2026

- **The "Brief sang nay" tro lai dien cau mau** nhu ba the kia, vi de no chay thang handler thi
  trung y het nut Brief o o nhap. Cau mau di qua rule va van ra dung brief, nho `_BRIEF` da nhan
  "tom tat" va "viec can uu tien".
- **Bao dang xu ly.** Mot bong bong tam trong hoi thoai (`dangXuLy` / `thoiXuLy`), bo di khi cau
  tra loi that ve. Dat trong hoi thoai chu khong lam popup: nguoi dung dang nhin cho do, va popup
  che mat cai ho vua go. Ba duong lau deu co: gui tin, brief, va cac nut ghi vao BC. Rieng brief
  cua dieu phoi noi truoc la mat khoang 15 giay vi no ghi tung de xuat vao BC.
- **De xuat phai den tay nguoi duyet.** `inventory_health.on_propose` truoc day chi ghi vao BC
  roi bao lai chinh nguoi vua bam; doi vai tro sang nguoi duyet thi hoi thoai trong tron, phai
  bam Brief moi thay. Gio co `_bao_nguoi_duyet` day the sang hop thu cua `supply_chain` va
  `dispatcher`, kem ten nguoi de nghi va dong policy da khop.
- **Cham bao tin moi tren danh sach vai tro.** `/api/state` tra them `tin_ra` (so tin tro ly da
  gui cho tung nguoi); giao dien lay moc so sanh luc thay nguoi do lan dau nen cham chi bao viec
  den SAU khi mo man hinh. Vong poll goi `veDanhSachVaiTro()` chu khong goi `loadUsers()`, de
  khong hoi lai danh sach nguoi dung moi hai giay.
- **Nhan nut do skill quyet dinh, khong phai bang LABEL o giao dien.** Bang do tung de len het
  nen the "De xuat huy" lai hien nut "Duyet chuyen hang". Gio `a.label` thang, LABEL chi la
  duong lui.

### Tra loi "viec cua toi den dau roi", 13/09/2026

Intent `TRACKING` moi trong `nlu.py`, skill `assistant/skills/tracking.py`. **Khong goi model**:
cau tra loi ghep tu bang de xuat trong bo nho tro ly cong Transfer Order, tuc dung nhung con so
cot phai dang hien. Quan ly cua hang chi thay viec cua cua hang minh.

Ly do: cot phai da hien san de xuat va chung tu, nhung hoi cung noi dung do bang cau chu thi tro
ly bao "chua tra loi duoc". Dung chi ra: "cai nay cung co thong tin het roi ma". 6 test trong
`tests/test_tracking.py`.

Cung dot nay: `_BRIEF` nhan them "tom tat", "viec can uu tien", "viec sang nay"; va nguong
"cau phai tu sau tu tro len moi dua cho planner" gio chi con ap khi TAT AI
(`Assistant._dua_cho_planner`). Bat AI ma van chan cau bon tu nhu "liet ke 5 mat hang" thi nguoi
dung nhan lai cau tro giup va tuong AI khong chay.

### Goi ban giao de lam lai UI, 13/09/2026

`docs/ui-handoff/` va `docs/ui-handoff/Marou-UI-handoff.zip`. Gom `index.html`, `web.py`,
`marou-cacao.png`, cong `api-mau.json` (phan hoi JSON that cua 14 duong API, moi mang cat con 2
phan tu) va `README.md` ghi rang buoc: mot tep khong build step, khong tinh lai con so, phan
quyen theo vai tro, loi phai hien ra, khong tao API gia. Sinh lai bo mau bang TestClient.

### Loi cua BC phai len den man hinh, 13/09/2026

`BCError` gio co exception handler rieng: tra 502 kem nguyen van cau cua BC thay vi 500 tron.
Ben giao dien, `post()` doc than loi va hien dai do ngay duoi thanh tieu de; `_poll()` cung
bao loi thay vi chet im. Truoc do mot loi 403 lam bam Brief khong thay gi va bam
"Ghi de xuat vao BC" khong thay gi, mat mot vong doi chieu moi biet la BC tu choi chu khong
phai du lieu rong.

### Hai file sua du lieu lo sau khi post, 13/09/2026

`tools/fix_lot_data.py` doc ban xuat "Table data" cua BC roi sinh hai file trong `demo-data-nwv/`.

**`import-ile-expiry.txt`, 3.259 dong.** File journal chi ghi Expiration Date tren DONG NHAP.
Khi post, BC chep han dung sang ILE cua dong nhap, con dong xuat de trong, vi han dung cua dong
xuat duoc suy tu dong nhap ma no ap vao chu khong nhap tay. Nhin vao ILE thay 3.259 dong
Negative Adjmt. co so lo ma khong co han dung.
**Chuyen do khong lam sai mot con so nao cua UC2**: `inventory.py` lay han dung cua mot lo tu bat
ky dong nao cua lo do co han dung (`if e and lot`), va dong nhap thi luon co. Day la viec lam cho
du lieu nhin dung, khong phai sua loi tinh toan.

**`import-lot-info.txt`, 836 dong.** BC chi tu sinh `Lot No. Information` cho 40 lo, deu cua
33310, trong khi bo du lieu co 876 lo. Bang 6505 **khong co** truong Expiration Date (da doc
trong source base app), nen han dung duoc ghi vao Description dang `HSD dd/mm/yyyy`. Script bo
qua dung nhung dong BC dang co, de khong de len thu Dung da dat (vi du lo demo da Block).

Ban do lo -> han dung doc tu chinh `demo-data-nwv/import-full-journal.txt`, tuc dung thu da post,
khong tinh lai. 876 lo, khong lo nao co hai han dung khac nhau; script tu dung neu co.

## Doi nguon du lieu ngay tren giao dien

Dai bao nguon nam ngay duoi thanh tieu de, luon nhin thay, khong nam trong khay demo. No noi ro
dang doc fixtures hay dang doc BC that, kem ten environment va company, so dong ket qua doc duoc,
va ngay chot. Hai nut ben phai doi nguon ngay tai cho, khong phai sua `.env` roi khoi dong lai.

Duong API: `GET /api/mode` va `POST /api/mode {"bc": "mock" | "live" | "env"}`. Doi nguon thi
dung tro ly moi, vi bo nho, baseline va so chi phi deu gan voi mot nguon. Len khong duoc BC that
thi quay ve mock va in loi ra dai bao chu khong de tro ly chet. `env` la quay ve theo `.env`.

Dai bao chuyen mau do va noi ro khi dang tro vao BC that ma hai bang ket qua con rong, tuc chua
ai bam Run Inventory Health. Truoc day cho nay chi hien mot dong `BC=mock` trong khay demo, nhin
vao khong biet so dang xem la that hay mo phong.

Da kiem tren trinh duyet: doi sang Business Central thi dai bao xanh, ghi
"150 dong ket qua, 74 dong de xuat, chot ngay 18/09/2026", man hinh Suc khoe ton kho ve dung
150 dong do.

Tro ly neo ngay theo `As Of Date` tren bang ket qua cua AL chu khong theo ngay may chay
(`BCGateway.today()`). Bang rong thi no ghi mot dong canh bao roi tam dung ngay he thong. Hai
con so nay lech nhau thi cua so lich su ban va so ngay ke tu lan ban cuoi deu sai ma khong co gi
bao loi.

## Azure OpenAI, da dung xong ngay 12/09/2026

| Muc | Gia tri |
|---|---|
| Subscription | `Azure subscription 1`, id `cfd10962-3d10-4742-b2e5-04ce900339fe` |
| Resource group | `POC` |
| Resource | `Marou`, kind AIServices, region **eastus**, pricing tier S0 |
| Deployment | `gpt-4.1-mini` ban 2025-04-14, kieu **Standard global**, 100k TPM, bo loc DefaultV2 |
| Endpoint | `https://marou.openai.azure.com`, duong goi la `/openai/v1/chat/completions` |

Ba bien nam trong `python/.env`: `AZURE_OPENAI_ENDPOINT`, `AZURE_OPENAI_DEPLOYMENT`,
`AZURE_OPENAI_API_KEY`. Kiem bang `python tools/check_azure_openai.py`, da chay that,
HTTP 200 trong 2,8 giay, model tra ve `gpt-4.1-mini-2025-04-14`.

Region la eastus nen du lieu xu ly tai Hoa Ky. Region khong doi duoc sau khi tao. Neu Marou doi
giu du lieu trong Asia Pacific thi phai tao resource moi o region khac, va luc do nho
`gpt-4.1-mini` o `southeastasia` chi co voi Global Standard hoac Data Zone Standard.

**Lan goi thu dau tien da bat duoc mot dieu dang nho.** Hoi mot cau don gian: ton 470, con 25
ngay den han, ban 11 mot ngay, co ban het truoc han khong. `gpt-4.1-mini` tra loi:
"Co kha nang het truoc han vi tong so ban trong 25 ngay la 275 don vi, con lai 195 don vi chua ban."
Phep tinh dung nhung ket luan nguoc voi chinh phep tinh do. Day la bang chung cu the cho nguyen
tac da chot: con so phai do lop AL tinh, model chi dien dat lai ket luan da co san, khong duoc
tu ket luan. Khi lam cua D, prompt phai dua san ket luan va cam model tu suy ra.

### Doi toan bo sang Azure OpenAI, xong ngay 12/09/2026

`LLM_PROVIDER=azure` la mac dinh, `anthropic` de doi chieu, chi co tac dung khi `LLM_MODE=live`.
Chay live **khong can** `ANTHROPIC_API_KEY` nua.

Mot cho duy nhat chon model: `bc_agent/llm.py`, ham `build_llm()` (model chinh) va
`build_llm(fast=True)` (viec ngan: phan loai tin, doc cau giai thich). Tren Azure hai cai la
mot deployment, tren Claude la Opus va Haiku. Moi backend co `complete()` cho vong lap tool use
va `text()` cho mot hoi mot dap co ep JSON theo schema. Nam cho goi model deu di qua day:
`runner.py`, `assistant/core.py` (viet lai cau), `nlu.py`, `planner.py`, `skills/evidence.py`.
Khong con cho nao import `anthropic` truc tiep ngoai `llm.py`.

Ten deployment phai trung ten model (`gpt-4.1-mini`) vi `assistant/budget.py` tra gia theo
ten do. Dat ten khac thi so chi phi tinh theo gia Claude Opus, sai gap muoi lan.

Khong phai chi doi ten model. Bon cho trong `assistant/` chi gui prompt roi doc chu ve, doi
that su chi la doi client (structured output cua Azure la `response_format.json_schema` strict,
hai schema INTENT_SCHEMA va evidence SCHEMA da co san `additionalProperties: false` nen dung
duoc ngay). Nhung vong lap agent trong `runner.py` noi bang giao thuc tool use cua Anthropic,
con Azure OpenAI noi giao thuc khac:

| | Anthropic | Azure OpenAI |
|---|---|---|
| Model goi tool | content block `tool_use` | `choices[0].message.tool_calls` |
| Ly do dung | `stop_reason = "tool_use"` | `finish_reason = "tool_calls"` |
| Tra ket qua | `tool_result` kem `tool_use_id`, gop nhieu cai trong mot message | moi ket qua mot message `role="tool"` kem `tool_call_id` |
| Khai bao tool | `input_schema` | boc trong `function`, goi la `parameters` |

`bc_agent/azure_llm.py` la lop phien dich giua hai giao thuc do, dung lai ket qua thanh dung
hinh dang ma `AgentRunner` dang doc nen runner khong sua mot dong. 11 test trong
`tests/test_azure_llm.py`.

**Da chay that, vong lap agent:** `LLM_MODE=live python -m bc_agent.cli run inventory_health`,
11 luot goi tool, tao 9 de xuat, ra ket luan tieng Viet doc duoc.

**Da chay that, tro ly (BC_MODE=mock):** NLU phan loai dung ca ba cau thu (STOCKOUT, STOCK_QUERY,
BRIEF, co item_text). Evidence doc dung ba nhan one_off (ra dung khoang 01/08 den 31/08),
permanent, supply; nhan `unknown` chua thu. Viet lai cau giu nguyen moi con so va ma. Planner
chay 3 vong, 5 tool call, ra cau tra loi. Tong 11 luot goi het 0,004 USD.

Hai cho lo ra tu lan chay do da sua cung ngay: fixtures doi sang bo demo (xem "Mock cua tro
ly") va `sales_history` loc theo cua so ngay that. Chay lai planner tren bo moi: 5 tool call,
`sales_rate` 7 va 14 ngay ra hai tong khac nhau, model so sanh dung hai so cung don vi, va tu
doc duoc S0001 dang cho 182 Choco nuts truoc khi noi kho du hang. 0,005 USD.

**Nhung lai bat duoc loi thu hai cung loai voi loi dau.** Model tu tong ket la "tao 10 de xuat",
lap lai hai lan trong cau tra loi. Log cho thay chi 9 lan goi `create_proposal`, khong lan nao
loi. No dem sai chinh viec no vua lam. Cong voi loi truoc (phep tinh dung nhung ket luan nguoc),
day la hai bang chung doc lap cho cung mot ket luan: **moi con so trong cau tra loi phai lay tu
tool result hoac tu bang da tinh, khong duoc de model tu dem hay tu suy**. Voi cua D, prompt phai
dua san ca ket luan. Voi cua C, cau tong ket phai do code ghep tu log chu khong phai model viet.

### Don gia va tran chi phi

Don gia lay ngay 12/09/2026 tu **Azure Retail Prices API**, region eastus, USD. Day la nguon
chuan, trang gia tren azure.microsoft.com render dong nen khong doc duoc bang script.

| gpt-4.1-mini | Vao (USD/trieu token) | Ra | Cache read |
|---|---|---|---|
| Global Standard | 0,40 | 1,60 | 0,10 |
| Regional va Data Zone | 0,44 | 1,76 | 0,11 |

Voi 10 do tren Global Standard: 25 trieu token neu toan vao, 6,25 trieu neu toan ra,
**11,8 trieu token** theo ty le that do duoc la 62,6% vao va 37,4% ra.

**Azure budget chi canh bao, khong chan.** Muon chan that phai gan action group va automation.
Rieng subscription nay thi Cost Management khong ho tro loai offer nen budget cung khong chay.

Cho chan that nam trong `assistant/budget.py`, hai tran, vuot cai nao cung chan va tu quay ve
che do rule chu khong bao loi:

    AGENT_DAILY_BUDGET_USD   tran theo ngay, mac dinh 2
    AGENT_TOTAL_BUDGET_USD   tran cong don khong reset theo ngay, mac dinh 10

Lop chan thu hai la TPM tren deployment. Dang de 100.000 token mot phut. Neu code lap vo han va
toan sinh token ra thi 0,16 do mot phut, tuc 9,6 do mot gio, het sach 10 do trong mot tieng.
Da ha xuong 10.000 TPM ngay 12/09/2026, Dung tu lam tren Foundry. Sua bang tool tu dong ba lan
deu khong an du trang bao da luu, nen lan sau chinh quota thi lam tay.

### Xem muc tieu thu va chi phi o dau

**Token, co ngay sau vai phut.** Foundry portal, Build, Modeles, Deploiements, bam
`gpt-4.1-mini`, tab Surveillance. Hien so luot goi, tong token, token vao, token ra, kem bieu do.

**Tien, khong xem duoc tren subscription nay.** Chinh trang do bao: "Les donnees de cout ne sont
pas disponibles pour cet abonnement. Votre abonnement Azure utilise un type d'offre qui n'est pas
pris en charge par Azure Cost Management." Subscription la `Azure subscription 1`, plan
`Azure Plan`, nam trong tenant demo CONTOSO. Trang Overview cua subscription cung hien
"No data to display".

Ke ca khi subscription duoc ho tro thi cung khong xem duoc ngay: tai lieu Microsoft ghi
pay-as-you-go mat **toi 72 gio** de du lieu chi phi len Cost Management, va subscription moi tao
co the mat **48 gio** truoc khi dung duoc cac tinh nang Cost Management.

Hau qua cho phan commercial model: o tenant nay chi do duoc bang token, roi nhan voi don gia
cong bo. Khong lay con so tien tu tenant demo nay de hua voi Marou.

## Azure OpenAI, tra tren Microsoft Learn ngay 12/09/2026

- BC gio co **Business Central AI resources** do Microsoft quan, goi bang
  `SetManagedResourceAuthorization`, ho tro GPT-4.1 va GPT-4.1-mini. Nhung no dang **preview**
  va **chi dung duoc tren moi truong production cua khach**. Microsoft khuyen doi tac tu co
  subscription Azure OpenAI rieng cho phan dung, phat trien, kiem thu. Tai lieu cung ghi phai
  co Azure subscription moi dung duoc bo cong cu AI trong BC. Khong hua tren preview.
- **Bay ve region.** `gpt-4.1-mini` o `southeastasia` **khong co** o deployment type
  Standard/Regional. No chi co o **Global Standard** (va Global Provisioned Managed).
  Muon giu du lieu trong khu vuc thi dung **Data Zone Standard**, Microsoft xu ly trong pham vi
  Asia Pacific, thay vi Global Standard di bat ky dau.
- **Ten deployment khong phai ten model.** Khi goi API, Azure OpenAI doi ten deployment tu dat.
  Day la khac biet chinh so voi OpenAI thuong, va la cho hay sai nhat luc dau.
- **Data movement cua Copilot chuan.** BC dat o Asia (East, South East) thi Copilot cua Microsoft
  dung Azure OpenAI o **Hoa Ky**, can dong y data movement, toggle mac dinh bat tu ban 25.
  Nhung extension cua ben thu ba **tu chon region rieng**. Nghia la cua D cua NaviWorld co the
  giu trong Asia Pacific ke ca khi Copilot chuan cua Microsoft di My. Day la diem ban duoc voi
  Marou o buoc governance, va cung la cau tra loi cho rui ro "du lieu di ra ngoai Viet Nam"
  trong tai lieu 06.

## Viec con lai

**Dung phia khach (Dung). Post lai tam ma co lot, day la viec chan duong moi thu con lai.**
Chi dung den tam ma `33110 33130 33170 33310 33323 33341 10000 10045`, 13 ma con lai giu nguyen
ILE dang co.

1. Xoa sach `Item Ledger Entry`, `Value Entry` va `Item Application Entry` cua company NWV.
   Va tung phan da thu hai lan va deu vuong, nen lam lai tu dau cho gon.
2. Gan `Item Tracking Code` = `LOTALLEXP` cho chin ma: `33100 33110 33116 33130 33160 33170
   33310 33323 33341`. Chi lam duoc khi ILE da rong, xem `TestNoEntriesExist`.
   `10000` va `10045` **khong** gan tracking code.
3. Publish `NWV Marou Demo Setup` **1.0.1.0** (ban nay bat `Item Tracking on Lines`), roi bam
   nut 1.
4. Kiem batch NWVDEMO rong (dung nut xoa dong chua post neu can), roi import
   `demo-data-nwv/import-full-journal.txt`. So dong chua post phai dung **24.759**. Bam nut 2 de
   post theo tung thang, bam nut 3 de khoa lo demo.
5. Dat Work Date = **18/09/2026** roi bam **Run Inventory Health** va **Run Store
   Replenishment**. Muc tieu: 167 dong va 77 dong.

**Dung phia NaviWorld:**

6. Chay `python -m bc_agent.cli uc2-reconcile --from al`. Muc tieu trung 100% voi
   `demo-data-nwv/uc2-expected.json`: 45 qua han, 32 can han, 47 rui ro dut hang, 4 cham luan
   chuyen, 1 ton thua, 38 binh thuong, 22 de xuat dieu chuyen, 18 bi chan boi han dung.
   `--from python` da trung khop hoan toan, xem muc "Doi chieu tren BC that".
7. Cau tong ket cua vong lap agent (`runner.py`) va cua planner phai do code ghep tu log tool
   call, khong de model viet, vi hai lan model dem sai (xem muc Azure OpenAI). Chua lam.
8. Theo QA: nut mo Item Ledger Entry va Lot No. Information tu page 70102, nut tao de xuat tu
   dong xau khong can model, nut dat Job Queue.
9. Soan phan commercial model cua de xuat gui Marou.
10. Claude chi con de doi chieu: `AGENT_MODEL=claude-opus-4-8` la ten hop le, ban moi hon la
   `claude-opus-5` cung gia; ca hai nhan `thinking={"type": "adaptive"}`, tu choi `budget_tokens`.

## Khao sat Marou ngay 13/09/2026 (Dung cung cap), va UC1, UC3 lam lai

**Cau truc entity, Dung dinh chinh ngay 14/09/2026 (thay dong ghi ngay 13/09 bi nguoc):** Marou co hai entity.
**Marou la san xuat, co quan ly lo. Dakao la ban le, KHONG quan ly lo.** Agent lam cho ca hai entity. Hang di tu
san xuat sang ban le qua nghiep vu intercompany mua ban giua hai company (chung mot moi truong BC).
He qua cho UC2: phan tang theo lo chi dung o phia san xuat; ben ban le theo mat hang x dia diem, han dung phai suy tu
dot giao. Khi khao sat khong hoi cau nao ve POS co lo. Khong can ghi thong tin entity vao tai lieu gui khach.
(Dong cu ghi "Dakao nha may, Marou Retail ban le" la sai.)

Van de ton kho ban le Dung khao sat duoc:
1. Nhap PO khong kip thoi: hang mua ve cua hang don chung tu toi cuoi thang moi post receive. Marou
   dang thue mot nhan su ben ngoai de post don. Muon co workflow cho AI post don.
2. Ket ca khong du ton nguyen lieu. Da co tool kiem ton ket ca.
3. Muon tu dong hoa intercompany Marou va Dakao: post SO tu dong post PO va nguoc lai.

UC1 theo Dung: dung module Replenishment co san cua LS Central (trang Replen. Item Quantities, bao
cao Add Items to Replenishm. Jrnl.) thay vi tu tinh. Tai lieu LS Central tra ngay 13/09/2026:
Replenishment Item Quantity khoa theo Item, Variant, Location, co Inventory, Quantity on Purchase
Order, Quantity in Transfer In/Out, Daily Sales, No. of Days Out of Stock, Replenishment Calculation
Type, Vendor No., Replenish From Warehouse; tinh bang Scheduler Job codeunit 10012200
(LSC Replen. - Calc. Qtys) hoac bao cao Replen. - Calc. Item Qty; Replenishment Journal dung no de ra
de xuat PO va TO. **Symbol LS Central da co tu 13/09/2026** trong `AL/Demo/.alpackages`: LS Central
28.0.10.3586 (kem source, unpack ra 8.658 file .al o `AL/Demo/Unpacked/LS Retail_LS Central_28.0.10.3586`)
va LS Central System App 28.0.2.3586 (khong kem source, chi co SymbolReference.json). Tai bang token
S2S qua dev endpoint `.../dev/packages`, khong can dang nhap VS Code. Ten file trong goi LS bi ma hoa
URL hai lan (`%2520`), phai giai ma khi unpack.

Intercompany chuan BC (Microsoft Learn tra 13/09/2026): cung database thi bat Auto. Send Transactions
(Intercompany Setup) va Auto. Accept Transactions (Intercompany Partner) de tu tao chung tu ben kia,
**nhung khong post**. SO va PO gui duoc truoc khi post; sales invoice da post sang ben kia thanh
purchase invoice. Post tu dong ben kia la phan phai lam them. API v2.0 `purchaseOrders` chi co bound
action `receiveAndInvoice` (nhan va xuat hoa don cung luc), khong co nhan rieng.

**Mau thuan voi ranh gioi da chot:** tai lieu 04 va 05 ghi tro ly khong post chung tu o bat ky giai
doan nao. Van de 1 va 3 doi AI post. Phai chot lai ranh gioi truoc khi lam, khong tu noi long.

Dung tra loi ngay 13/09/2026: Dakao va Marou Retail **chung mot moi truong BC** (nen intercompany cung
database, Auto. Send va Auto. Accept dung duoc). Nhan su thue ngoai post nhan dua vao chung tu gi: **chua biet**.

### UC1 tren LS Replenishment, lam toi 13/09/2026

**Gop app.** Dung bac tach app adapter rieng. `NWV Marou Agent` **1.1.1.0** gio phu thuoc LS Central va chua
luon 5 API page doc ket qua LS (70270-70274), permission set 70270 `NWV AGENT LS READ` va 70271
`NWV AGENT LS CALC` (gom `LSCentralPermissions`), codeunit 70275 `NWV Replen. Service` phoi ODataV4
`NWVReplenService`: `ReadTable` (doc bang trong danh sach cho phep, tra JSON theo ten field, dai 10012200-10012399
cong Item, Location, SKU, Vendor, Item Variant, Item UoM, LS Store, Store Group, Item Distribution),
`CalcItemQuantities`, `UpdateOutOfStock`, `CalculateJournal` (tu choi neu template tu tao chung tu). Moi ham
nhan `workDateText` vi phien web service khong co Work Date. `NWV Marou Demo Setup` **1.1.1.0** them codeunit
70253 phoi `NWVDemoReplenSetup.Apply(configJson)`. Van la hai app. Ca hai **da publish len NWV01 bang S2S**
qua Automation API `extensionUpload` (`python/tools_bc.py upload`), Entra app du quyen, khong gap 403.

**Chay:** `cd python; python ../tools/ls_replen_setup.py apply | calc | summary`. Cau hinh sinh tu
`tools/demo_scenario.py` (ASSORTMENT, han dung, move_days, DISCONTINUED), khong chep tay.

**Vi sao du lieu LS truoc do "chua dung", doc trong source LS 28.0.10.3586:**
- Bang Replen. Item Quantity la ban chup Cronus 2010-2023, chua ai tinh lai tren du lieu Marou.
- Replen. Setup `Store Items Ranged By = Store Groups`: `ShouldPlanItem` chi tinh cua hang khi co
  Item Distribution loai Store, Active, Ordered by Central, **Ordering Method = Calculate**. Cronus chi co "By hand".
- **Bay:** `LSC Item Distribution.OnInsert` goi `AssignItemFieldsOnInsert`, chep de Ordering Method bang
  `Item."LSC Def. Ordering Method"` (By hand). Insert xong phai ghi lai. Lan chay dau 0 dong cua hang vi vay.
- Item `LSC Replen. Calculation Type = Automatic - From Data Profile` ma khong co Data Profile thi bi bo qua.
- Replenish From Warehouse lay tu Replen. From Warehouse, khong co thi Default Central Warehouse = W0001 (Cronus).
  Da them quy tac theo tung ma ve W0003; khong doi Default de khong dung vao Cronus.
- S0010 tat `LSC Active for Autom. Replen.`
- Out of Stock Log Cronus mo tu 01/01/2018 cho 10070 x S0002, khong co Date In Stock: LS coi 56/56 ngay het hang,
  ban binh quan 0. Da xoa (cung dieu kien bao cao Delete Open Replen. OOS). Sau khi xoa ra 4,97/ngay.
Da ghi 175 + 79 + 8 thay doi, moi thay doi co gia tri truoc va sau trong log cua `apply`.

**Ket qua tinh (Work Date 18/09/2026):** 216 dong Replen. Item Quantity. MAROU-TO 109 dong chi tiet, 5 de xuat,
trong do **33323 x S0001 ton 0, ban 11,7/ngay, de xuat chuyen 82** (dung kich ban UNDERSHIP ngung chuyen 21 ngay).
MAROU-PO 25 dong co de xuat nhung chi 3 ma ra so luong mua vi ICECREAM (33310, 33323, 33341) khong co Vendor No.

**Hai loi du lieu CON LAI, chua sua, can Dung quyet:**
1. **Dong Sale cua 33120, 33130, 33160, 33170 lay Sales UoM SLICE (0,1 / 0,08333), 33150 lay PORTION.** File
   import khong co cot Unit of Measure Code nen Item Journal Line lay `Item."Sales Unit of Measure"` cho dong Sale.
   3.351 dong ILE ban bang mot phan muoi. Vi du 33170 x S0001: file ban 181 cai trong 56 ngay, BC ghi 18,1;
   ton 547,9. Anh huong ca UC2 tren BC. Da doi Sales UoM 5 ma ve don vi co so (apply). Bu bang dong Sale
   lui ngay **khong lam duoc**: 215 to hop lo x cua hang da het ton lo. Duong sua: post lai.
2. **30091 co 9 variant, 33150 co 4 variant (Cronus)** ma ILE khong co variant. LS co variant thi chi tinh theo
   variant (`ProcessVariantRecord`), ton khong variant bi bo qua: 30091 ra ton 0 moi noi. Can xoa variant Cronus.

**Kiem truoc khi post lai (`python ../tools/ls_replen_setup.py preflight`, chay 13/09/2026 22:52):** ILE con du lieu;
**8/9 ma TRACKED chua co Item Tracking Code** (chi 33310 co), tuc ILE hien tai la ban lo duoc va vao sau khi post,
chua bao gio post lai sach nhu ke hoach 12/09; 13 Item Variant tren 30091 va 33150. Ket luan gui Dung: phai xoa
ledger va post lai toan bo bang `import-full-journal.txt` (file khong can sua vi Sales UoM da ve don vi co so),
khong can xoa company. Sau khi post: Run Inventory Health va Store Replenishment, roi
`ls_replen_setup.py apply --reset-oos` (xoa het Out of Stock Log demo vi tinh tren ton cu) va `calc`.

### Post lai du lieu kho qua S2S, 13/09/2026 dem

Dung bao "tu lam 7 buoc". `tools/repost_demo.py preview|reset|master|import|post|calc`, goi web service
`NWVDemoRepost` (codeunit 70256, app `NWV Marou Demo Setup` 1.2.0.0) va `NWVAgentCalcService` (codeunit 70278,
app `NWV Marou Agent` 1.1.2.0, chay lop AL voi Work Date truyen vao).
- `ResetInventoryLedger` chi xoa bang kho (ILE, Value Entry, Item Application Entry va lich su, Item Register,
  Item/Value Entry Relation, Avg. Cost Adjmt. Entry Point, Post Value Entry to G/L, G/L - Item Ledger Relation,
  reservation cua Item Journal, dong batch NWVDEMO), bat buoc chuoi xac nhan, chi chay o company NWV. Mo khoa
  moi Lot No. Information vi lo bi khoa chan post. Khong dung G/L Entry, Transfer Order, don mua ban.
  App `NWV Configuration tools` (Dung dung hom 12/09) xoa giao dich CA company, khong dung cho viec nay.
- Da chay: xoa 24.759 ILE, 24.759 Value Entry, 27.228 Item Application Entry; gan LOTALLEXP cho 8 ma;
  xoa 13 variant Cronus cua 30091 va 33150; preflight sach.
- Import 24.759 dong qua `ImportLines` (1.000 dong mot lan, 55 giay). Post lan dau loi
  `Lot No. L260322-33100A ... cannot be fully applied` du file khong am ton theo lo. **Nguyen nhan, doc trong
  `ItemJnlPostBatch.PostLines` Base App 28.4:** Inventory Setup khong bat legacy posting thi batch post theo khoa
  `Document No., Item No., Location Code`, KHONG theo Line No. SL260322 (ban) chay truoc TR260322 (hang ve cua
  hang). Lan 12/09 khong gap vi luc do lo bi xoa khoi dong journal. Sua: `PostSlice` post tung chung tu
  (ngay + so chung tu) theo thu tu dong dau tien trong batch. Nua thang mat khoang 150 giay.

### Ket qua post lai va chuyen UC1 sang LS, 14/09/2026

- Toi post den 31/07 (18.057 ILE), Dung post tay phan con lai bang nut 2 cua trang Demo Setup va khoa lo.
- `repost_demo.py calc`: lop AL chi chay INVHEALTH va DISCGOV. **Inventory Health tren BC khop 100%
  `uc2-expected.json`: 45/32/47/4/1/38**, lan dau khop sau khi post lai co lo. Dong "de xuat dieu chuyen 16 vs 22"
  cua `uc2-reconcile` la bang NWV Repl. Suggestion cu, khong tinh lai nua.
- Update Out of Stock cua LS loi `Replen. Out of Stock Log does not exist` sau khi post lai: bang
  `LSC Replen. Last Entr for OOS` (10012237) giu so ILE cuoi da quet cho tung ma. `apply --reset-oos` gio xoa ca
  con tro nay (Demo Setup 1.2.2.0). LS sau khi tinh: 139 dong Replen. Item Quantity, MAROU-TO 65 dong chi tiet.
- **Dung bac: da bao dung LS Replenishment ma van chay NWV Replenishment Calc.** Da sua:
  `NWV Agent Job Runner` va `NWVAgentCalcService` voi ALL khong chay REPLEN nua (app 1.1.3.0, chi chay khi truyen
  REPLEN). Tren BC that `BCGateway.doc("replenishmentSuggestions")` doc `replenJournalDetails` template MAROU-TO
  cong `replenItemQuantities` roi dua ve hinh dang cu (`goi_y_ls`), nen brief dieu phoi, bao sap het, dieu tra,
  tu cham, KPI, MCP deu doc LS. `stockOutRisk` = LS de xuat > 0; so luong va so ngay phu lay tu LS; bao sap het
  khong nhan 14 ngay nua (lan thu dau ra 164 trong khi LS de xuat 82). Mock van dung fixtures cu.
  4 test `tests/test_goi_y_ls.py`. Nut "Run Store Replenishment" tren page NWV Agent Setup van con.
- Lan thu tren BC that ghi nham mot de xuat that (Choco nuts x S0001, 164); da Reject kem ghi chu. Con 6 de xuat
  cu 183 cai tu 12-13/09 (tinh tren du lieu sai) dang Proposed trong BC.

### Giai thich so cua LS va don custom tren BC, 14/09/2026

**Cong thuc LS, doc trong `LSC Replen. Calculation.CalcAveMan` (template chuyen hang, khong bat lead time):**
System Suggested Quantity = Daily Sales x Store Stock Cover Reqd (Days) x Forward Sales Forecast Factor - Effective
Inventory, lam tron len theo Transfer Multiple, am thi ve 0. Effective Inventory = `CalculateEffectiveInventory`
(ton + PO - tra NCC + chuyen den - chuyen di - SO + assembly - unavailable; journal chuyen hang bo PO theo Replen. Setup).
Daily Sales = `Calc-DailySale` tren cua so Sales Profile DEFAULT (-3W..-1D 75, -6W..-3W-1D 15, -8W..-6W-1D 10), bo ngay
het hang. Kiem tren BC: 33323 x S0001 = 11.675 x 7 x 1 - 0 = 82; 33110 x S0002 = 7.925 x 2 - 11 = 5.
- **LS chi ghi Calc. Log Lines khi chay co request page hoac scheduler.** Chay qua web service khong request page thi
  bo qua co `Create Calc. Log Lines`. `NWVReplenService.CalculateJournal` goi `SetParameters(batch, true, false)`
  (Job ID rong nen khong doi Next Run Date, khong chay song song): 1.090 dong log cho MAROU-TO.
- `NWV Marou Agent` **1.2.0.0**: API page 70279 `replenCalcLogLines`, 70280 `replenItemParameters` (field LSC tren
  Item), 70281 `replenSalesProfileLines`, them `forwardSalesForecastFactor` vao detail.
- Tro ly: `assistant/skills/ls_giai_thich.py`, intent `REPLEN_WHY` ("vi sao LS de xuat ..."), nut "Vi sao LS ra so
  nay" tren the de xuat co nguon LS, MCP tool `explain_replenishment`. Doc so va trich nguyen van log LS, khong tinh lai.
  Canh bao khi LS dem qua nua cua so la het hang (Croissant chocolate 42/56 ngay: banh tuoi huy cuoi ngay nen ton ve 0).
- **Tham so replenishment** nam tren Item (LSC Replen. Calculation Type, Sales Profile, Store/Wareh Stock Cover Reqd,
  Transfer Multiple, Reorder Point, Maximum Inventory), Item Distribution, Replen. From Warehouse, Replen. Setup. Gia tri
  do `tools/ls_replen_setup.py apply` dien tu demo_scenario. Nguong custom cua tro ly khong con dung tren BC that.
- **Da xoa khoi BC (1.2.0.0, publish Force Sync):** codeunit `NWV Replenishment Calc`, table `NWV Repl. Suggestion`,
  page `NWV Repl. Suggestions`, API page `NWV Repl. Suggestion API`, nut Run Store Replenishment, field Setup 20 Target
  Days of Cover, 21 Reorder Point Days, 42 Last Replenishment Run, nhanh REPLEN cua Job Runner va Calc Service.
  Unpublish 7 ban app cu khong cai (Agent 1.1.0-1.1.3, Demo Setup 1.0.0 va 1.2.1, NWV Marou Data API) bang
  `extensions(...)/Microsoft.NAV.unpublish` (co tu BC 25.4). `tools_bc.py upload <app> force` de publish Force Sync.
- Python: `uc2-reconcile --from al` khong so de xuat nua; `bc_agent/tools.py` (vong lap agent cu) tren BC that doc LS.
  Mock van dung `replenishment_suggestions.json` va cong thuc 14 ngay cu, chua doi sang hinh LS.

### Don TO thu va doi chieu RFP, 14/09/2026 rang sang

- **Dung bac: don custom ma giu lai 5 Transfer Order thu (HO1034-HO1038).** Sinh ra khi duyet thu de xuat 12-13/09
  (External Document No. `AGENT <id>`). TO Open van cong vao Quantity in Transfer In/Out cua Replen. Item Quantity nen
  lam lech ton hieu dung. Bai hoc: don mot tinh nang thi don ca DU LIEU no da sinh ra, khong chi object.
  `NWV Marou Demo Setup` **1.2.3.0** them `NWVDemoRepost.CleanupAgentTests('XOA-THU-AGENT-NWV')`: xoa TO co External
  Document No. `AGENT *` chua ship va toan bo bang 70102 qua RecordRef. Da chay: xoa 5 TO va 62 de xuat (so tra ve
  `proposalsDeleted` bao 0 nhung API xac nhan con 0 dong, dung tin so tra ve cua ham nay). Tinh lai LS: 33100 W0003
  chuyen di 150 ve 0, 33116 W0003 84 ve 0; MAROU-TO 11 dong de xuat, them 33116 x S0005 = 1.
- **RFP goc da co** (Dung gui 14/09, file trong Downloads: `Supply_Chain_Retail_Store_Data_Platform_AI_RFP_POC_Request_EN_VI`).
  Muoi UC: 1 Demand Planning & Forecast, 2 Inventory Health & Traceability, 3 Procurement & Supplier Performance,
  4 Production & Distribution Planning, 5 Store Replenishment Optimization, 6 Retail Sales Margin & Store Performance,
  7 Promotion & Discount Governance, 8 Loyalty Wallet Pass, 9 Multi-store Operations & Service Category (MMV First),
  **10 Supply Chain & Retail AI Assistant**. POC A = UC1+UC2+UC5, B = UC7+UC6+UC9, C = loyalty, D = dashboard + cau hoi
  ngon ngu tu nhien da duyet.
- **Tai lieu 03, 04, 07 goi sai UC10 la "yeu cau mo" (tiec 150 khach).** UC10 cua RFP la chinh tro ly: approved questions,
  exception explanation, dashboard links, recommended actions. Tiec 150 khach chi la mot cau hoi minh hoa. UC3 cua RFP
  doi supplier scorecard va lead time, khong chi PO qua han.
- Tren BC that 14/09: `posDiscountLogs` 0 dong, `discountExceptions` 0, `demandExceptions` 0, `nwvPurchaseOrderLines` 8
  (Cronus). UC7 va UC3 hien chua demo duoc tren BC.
- Dung chot POC A (UC1+UC2+UC5) + D (UC10 + dashboard) va dong y tao PO demo tren BC cho UC3. Thu tu lam: knowledge LS,
  UC1 backtest, UC3, link BC trong the, truy xuat lo.

### Knowledge chung giai thich LS Replenishment, 14/09/2026

Truoc do `ls_giai_thich.py` viet tay cho mot nhanh (Average Usage, chuyen hang, khong lead time), giai thich sai khi kho
khong du hang, Stock Levels, tham so tu Data Profile. Gio ba lop trong `python/assistant/knowledge/ls_replen/`:
- `mau_log.json`: **194 Label** trong source LS 28.0.10.3586 ma LS ghi vao Calc. Log Lines, sinh bang
  `tools/ls_knowledge_build.py` tu sau file (Replen. Calculation, Add Items to Replen. Jrnl., Multi-Whse. Utils, Redist.
  Calculation, Add BOM/Comp). Khong go tay; nang version LS thi chay lai.
- `dien_giai.yaml`: cau tieng Viet cho 116 Label (phan con lai la thong bao tao chung tu, thanh tien trinh), kem buoc,
  `doi_so`, tham so lien quan, thu tuc nguon.
- `tham_so.yaml`: 65 tham so khoa theo caption LS in trong log: y nghia, sua o dau, thu tuc nguon, va quy tac nguon tham
  so (Replen. Source Item / ItemStore / DataProfile, thu tu tim Data Profile).
`assistant/ls_knowledge.py` doc tung dong: boc the "[Cross Dock]", khop tron voi Label co phan bat duoc ngan nhat, khop
Label o dau dong roi doc tiep phan ghep (vi du Text009 + Text202 AD202), tach cap "A = x - B = y" chiu duoc gia tri rong,
nhom tham so chiu ngoac can bang ("Store Stock Cover Reqd (Days)(7)"). Dong khong doc duoc hien nguyen van.
`skills/ls_giai_thich.py` viet lai tren bo doc do, cong phan LS khong ghi log (ban binh quan tu RIQ va Sales Profile, thanh
phan ton). `tools/ls_knowledge_coverage.py` do tren BC: **2.938 dong, nhan dang 100%**. Da chay that 33323 S0001 (82),
33310 S0001 (CA100 ve 0), 33150 S0001 journal mua (19 thanh 11 do kho da co 25, AD202).
`tests/test_ls_knowledge.py` dien gia tri gia vao CHINH van ban moi Label roi kiem doc lai dung, nen nhanh du lieu demo
chua chay toi (Stock Levels, Reorder Point, boi so, kho het hang, Planned Sales Demand, forward factor) cung duoc kiem.
Doc trong source khi lam: Quantity in Transfer In/Out cong MOI Transfer Line khong loc Status (TO Open cung tinh);
No. of Sales Dates va No. of Days Out of Stock la tong qua cac cua so Sales Profile.
**Bay heredoc lan ba**: sua file Python co `\b`, `\d`, `\0` qua `python - <<EOF` voi chuoi thuong thi ra ky tu backspace
hoac null. Dung Edit/Write, hoac viet script vao scratchpad bang Write roi chay.
- **`/api/inbox` 500 `sqlite3.InterfaceError: bad parameter or other API misuse`** ngay sau khi doi nguon du lieu.
  FastAPI chay request dong bo tren threadpool, `Memory` va `Budget` giu mot ket noi `check_same_thread=False`; hai luong
  chong lenh thi sqlite3 bao loi. `assistant/ket_noi_sqlite.py` boc ket noi: moi `execute` chay trong RLock va doc het
  ket qua truoc khi nha khoa. `tests/test_ket_noi_sqlite.py` tai hien dung loi do khi bo khoa.
- **De xuat huy lo het han len BC khong co Lot No.** `gateway.create_proposal` ghi cung `lotNo = ""`; so lo chi nam trong
  Reference Key. Gio co tham so `lot_no`, `inventory_health.on_propose` truyen lo cua dong Inventory Health, va khoa chong
  trung trong bo nho la item x kho x lo (truoc chi item x kho nen lo thu hai bi chan nham). Da PATCH lo `L260910-33100B`
  cho de xuat 33100 W0003 dang Proposed. `tests/test_de_xuat_co_lo.py`.
- **Go chat Enter xong cau bien mat den khi tro ly tra loi xong.** Cau chi hien khi vong poll doc `/api/inbox`, ma server
  chi ghi tin sau khi xu ly xong. `send()` gio chen ngay mot bong bong tam (`.msg.tam`), vong poll thay bang tin that
  cung noi dung; gui hong thi bo bong bong va tra cau ve o nhap. Da kiem tren trinh duyet.
- **"kiem tra ton kho cua choco cake cua S001" bi tu choi.** Ma cua hang nam trong `item_text` lam `find_item` rot
  nguong. `nlu.ma_dia_diem` tach ma dia diem (chuan hoa bon chu so, S001 thanh S0001) vao `store_hint`, `_TU_DEM` bo
  tu dem ("toi muon kiem tra", "cua", "kho"). `stock_query` loc theo cua hang; quan ly cua hang yeu cau bo sung cho cua
  hang khac thi tro ly noi ro thay vi tra so cua cua hang minh. `tests/test_ma_cua_hang_trong_cau.py`.
  Lai dinh bay heredoc: `` trong chuoi Python thuong thanh ky tu backspace, regex im lang khong khop.
- **Dieu phoi hoi "co mat hang nao da het han chua" bi hoi lai "ban thuoc cua hang nao".** "het" dua cau vao STOCKOUT.
  Intent moi `EXPIRY` (dat truoc WHY va STOCKOUT), `inventory_health.het_han`: doc bang Inventory Health, vai co dia diem
  chi thay dia diem minh, dieu phoi/Supply Chain/Retail Ops thay het kem chia theo dia diem; "sap het han, can date" lay
  NearExpiry. Vai khong gan cua hang hoi "sap het X" thi tra ton moi dia diem thay vi hoi lai. `tests/test_hoi_het_han.py`.
- Dung chot doi chu "ton hieu dung" thanh **"ton kha dung"** cho Effective Inventory trong moi cau tieng Viet.

### UC1 backtest, UC3 scorecard, truy xuat lo, link BC, UC5 min-max: xong dem 13 rang sang 14/09/2026

App dang chay tren NWV01: `NWV Marou Agent` **1.3.2.0**, `NWV Marou Demo Setup` **1.3.4.0**.

- **UC1 do chinh xac du bao**: codeunit 70120, bang 70120 `NWV Forecast Accuracy` va 70121 `NWV Forecast Daily`, page
  70120/70121, API `forecastAccuracies`, `forecastDailies`. Ky kiem tra 28 ngay ket thuc o WorkDate, hoc 84 ngay truoc do.
  MA28 va SWA8 (trung binh cung thu 8 tuan). Bo ngay cau bi cat cut (dau ngay ton <= 0 va ban 0) va ngay trong
  NWV Demand Exception. **Chi do cap cua hang co dong Sale, khong do kho trung tam**: luong xuat cua kho cuc (WAPE 93-129%)
  va kho khong phai diem dat du bao ban. Nguong tren Setup: 50 Holdout, 51 WAPE Warn, 52 Bias Warn, 53 Min Actual Qty.
  BC 14/09: 148 dong, 74 cap, MA28 38,7%, SWA8 41,2%. Skill `du_bao` (intent FORECAST), tab Du bao co bieu do theo ngay.
  The ghi ro "chua phai mo hinh AI": baseline la thuoc do cho mo hinh mua sau.
- **UC3 scorecard nha cung cap**: codeunit 70121, bang 70122, page 70124, API `supplierScorecards` va
  `nwvPurchaseReceiptLines` (70126). Dung han %, giao du lan dau %, tre trung binh, lead time hua va thuc te, dong qua han
  trong cua so lich su. Bo nha cung cap khong co dong den han. Skill `nha_cung_cap` (SUPPLIER), tab Nha cung cap.
- **Du lieu nha cung cap demo**: `tools/supplier_demo.py plan|apply|calc`, web service `NWVDemoSupplier` (codeunit 70257).
  71 PO va 71 phieu nhan cho 44020 AL-s Foods (hua 7 ngay, xau di tu 27/07) va 44030 Dan-s Dairy (hua 3 ngay), cong 5 don
  mo NCC-MO-01..05. **Phieu nhan post vao location rieng NCC-NHAN roi Negative Adjmt. bu**, nen UC2 va LS khong doi (da
  kiem: van 167 dong 45/32/47/4/1/38). Order Date tren Purchase Line bi BC tinh lai theo Expected Receipt Date nen phai gan
  lai sau validate. Phai noi voi khach day la du lieu demo NaviWorld tao.
- **Doi chieu**: `uc1-reconcile` 148 dong va `uc3-reconcile` 6 dong, trung khop hoan toan ngay 14/09. UC3 phai doc nhom
  hang tu `nwvItems`: ma thieu nhom roi vao dong nhom rong, trung khoa voi dong tong cua nha cung cap, lech 11 cho.
- **Truy xuat lo** (UC2 traceability): skill `truy_xuat` (TRACE), `gw.ile_theo_lo`, MCP `trace_lot`. Gom ILE cua lo theo dia
  diem, noi con ton o dau va thu hoi lay lai o dau, bao lo da qua han ma con ton. Ngay hien dd/mm/yyyy.
- **Link sang BC trong the**: `assistant/bc_link.py`, dang `https://businesscentral.dynamics.com/<tenant>/<env>/?company=..&
  page=..&filter='Field' IS 'value' AND ...` (tra Microsoft Learn). Da mo that tren Chrome: page 38 loc Item No. va Lot No.,
  page 70124 loc Vendor No., deu dung.
- **UC5 min-max**: `tools/ls_replen_setup.py` co `STOCK_LEVELS`: 30091 Reorder Point 3 / Maximum Inventory 12, 33150 8 / 20.
  LS `Calc-StockLevels` doc Item."Reorder Point" va "Maximum Inventory": ton kha dung <= Reorder Point thi dua len Maximum,
  khong thi 0. Demo: 33150 S0002 ton 8, dua len 20, can 12, kho chi con 25 cho tong 26 nen chia lai con 11 (AD203).
  Knowledge doc 100% 2.861 dong log sau khi doi. `Apply` chi dung Reorder Point/Maximum khi cau hinh co truyen, de khong xoa
  gia tri cua ma Average Usage.
- **AL khong short-circuit `and`**: `if Config.Get('k', Token) and Token.AsValue()...` van goi AsValue khi thieu khoa, Token con
  giu gia tri cu (mang items) nen bao "Unable to convert NavJsonToken to NavJsonValue". Loi nam san trong `DeleteStaleOutOfStock`,
  chi lo ra khi chay `apply` khong co `--reset-oos`. Sua bang if long (Demo Setup 1.3.4.0).
- **Da tu choi 4 de xuat cu** (30091 x S0001/S0002/S0010, 33150 x S0002) vi LS tinh lai theo min-max ra so khac; ghi chu
  trong review comment. Khong xoa dong nao. 7 de xuat con lai trung so LS nen giu.
- **Tro ly sua trong dem**: `find_item` chon ten mat hang khop nguyen cum dai nhat truoc khi so mo ("Ice cream" tung thanh
  "Ice cream blueberry"); `_tim_cua_hang` nhan ten ngan (Quan 1, Ha Noi, Thao Dien, Da Nang, truc tuyen) cho ca cau vi sao LS
  va dieu tra; khong in "Quyet dinh: ." khi Decision cua LS rong; the Stock Levels so so cuoi voi "so can theo muc ton" chu
  khong voi Maximum Inventory; khong gui tin khi dang doi nguon du lieu (tin bi mat cung tro ly cu).
- **Kiem so gan nham dia diem trong cau tra loi cua planner**: `kich_ban.so_sai_dia_diem`. Chay that 14/09 model viet
  "S0010 ton 2 chai" trong khi list_stock S0010 khong co mon do; so 2 la ton cua S0005 nen kiem theo gia tri khong bat duoc.
  Moi so dung sau ma dia diem phai co o ket qua cua dung dia diem va dung mat hang (tu buoc find_item), khong thi the ghi
  "Kiem tra so" va liet ke so do. Chi canh bao, khong sua cau tra loi.
- **Nhom nut kich ban "POC"** tren giao dien, thu tu theo POC A+D. Lo trinh demo ban 3 o `docs/lo-trinh-demo-agent.md`.
- **Chay AI that de kiem dinh tuyen** (Azure, BC that): cau viet khac kieu rule vao dung FORECAST, SUPPLIER, TRACE. Tong chi
  phi ca dot thu khoang 0,01 USD. `runs/cai-dat.json` van de AI tat; test bat AI trong tien trinh bang `set_ai(True)`.

### Tai lieu va anh chup, sang 14/09/2026

- `.env` doi `BC_MODE=api`. Dung da nang TPM deployment `gpt-4.1-mini` len **30.000**.
- Anh kien truc chi tiet: `docs/kien-truc/kien-truc-chi-tiet.html` render bang Chrome headless ra `kien-truc-chi-tiet.png`.
- `tools/chup_man_hinh.mjs`: Chrome headless qua DevTools Protocol (Node 24 co WebSocket san), chup 16 anh theo kich ban
  demo vao `docs/anh-demo/`. Vai quan tri la `dung.admin`. Buoc 13 bat AI tam thoi roi tat.
- `docs/08 ... Kien truc, muc dap ung UC va kich ban demo (noi bo).docx` (`build_08.js`). Tai lieu 02 doi sang POC A+D
  (`build_proposal.js`, ban nhap 0.2); ban A+B cu chuyen vao `_to_delete/superseded/`.
- Loi lo ra khi chup, da sua: `gw.goi_y_ls` lay `systemSuggestedQuantity` lam so chuyen, voi Stock Levels do la Maximum
  Inventory (Ice cream S0002 ghi 20 thay vi 11). Gio lay `quantity` cuoi cua LS; tu choi 3 de xuat sai kem ghi chu. Dong
  nguon duoi the ghi bang NWV Repl. Suggestion da xoa, gio theo skill. The de xuat ghi cung "dap ung 14 ngay ban", gio tinh.
- Con do: the de xuat min-max hien ban binh quan 0 (journal Stock Levels khong co so nay, lay tu RIQ); kiem so cua planner
  bao nham khi mot dong nhac nhieu cua hang.

### Thu mo hinh du bao pho bien cho UC1, 14/09/2026

`tools/forecast_lab.py chuoi` (Python chung) roi `chay` (venv rieng co statsmodels, lightgbm, scikit-learn, pandas; venv
tam o scratchpad, khong cai vao Python chung). Cung 74 cap, cung ky 22/08-18/09, cung quy tac bo ngay het hang voi codeunit
70120; MA28 tai tao dung 38,7%. Ket qua WAPE gop (bias): tran ly thuyet tu ham sinh du lieu demo 34,6 (+7,9); Holt-Winters
37,7 (+6,9); SARIMA(1,0,1)(0,1,1)7 37,8; MA28 38,7; ket hop ETS+LightGBM 39,8; SWA8 41,2; LightGBM global tweedie 42,9;
seasonal naive 48,6. Ket qua o `docs/du-bao/ket-qua-thu-mo-hinh.json`.
Doc: du lieu demo la mo phong (nhieu nhi thuc quanh ky vong) nen tran chi con 4 diem de cai thien; ICECREAM co cho cai thien
nhat (tran 20,2, ETS 27,9, MA28 31,9) vi he thang 6-8 roi thang 9 giam. LightGBM thua vi 74 chuoi x 6 thang, khong co bien
gia, khuyen mai, le. Khong dung so nay de hua voi Marou; phai chay lai tren du lieu that.
Da tra: BC Sales and Inventory Forecast dung Azure AI voi ARIMA, ETS, STL, TBATS (Forecasting API, codeunit 2000); LS Forecast
(tai lieu LS Central 20) dung ARIMA, Seasonal ARIMA, Additive, Multiplicative, chay qua LS Insight; M5 (Walmart) top dau deu
LightGBM, exponential smoothing van canh tranh o cap san pham.

### Holt-Winters cho UC1, lich su kien chuan LS, du bao vao LS Forecast Entry: 14/09/2026 chieu

App `NWV Marou Agent` **1.4.0.0**, `NWV Marou Demo Setup` **1.4.0.0**, da publish NWV01.
- **Codeunit 70120 them phuong phap `HW`** (Holt-Winters cong tinh, mua vu tuan danh theo thu 1..7). Hoc tren toi da 365
  ngay truoc moc; ngay het hang va ngay su kien duoc dien bang trung binh cung thu 8 tuan truoc. Tham so chon theo SSE mot
  buoc (bo 7 ngay dau): alpha {0.05,0.1,0.2,0.3,0.5} x gamma {0.05,0.1,0.2,0.3} x (khong xu huong | beta 0.1, phi 0.9).
  Khoi tao: muc nen = trung binh 4 tuan dau, mua vu = trung binh tung thu tru muc nen. Truong moi 36 `Model Parameters`.
  Mang ngay 500 phan tu. Chay ca 74 cap tren BC mat 10 giay.
- **Ngay su kien lay tu bang chuan LS** `LSC Replen. Planned Sales Dem.` (Enabled, Planned Demand Type khac rong, variant
  rong), cong NWV Demand Exception, doc vao Dictionary mot lan. Dung phan hoi: "sao khong dung Replen. Planned Events,
  Replen. Planned Sales Demand". Doc trong source LS 28: `ReturnPlannedSalesDemandUpdatedQty` chinh du bao tung ngay theo
  Substitute Quantity (Use Base Value if Higher/Lower, Always), Additional Quantity, Additional % Factor; Average Usage cung
  goi ham nay khi co lead time. Qua khu thi LS co bao cao `Calc. Sales Hist. Adj. PDE` ghi `LSC Replen. Sales Hist. Adj.`
  de bo phan ban tang do su kien khoi ban binh quan (chua cau hinh Sales Hist. Adj. Rule tren NWV01).
- **Du bao 28 ngay toi ghi vao `LSC Forecast Entry`** (table 10012318, caption Retail Forecast Entry) khi bat Setup 55
  `Publish LS Forecast` (54 `Forecast Horizon Days`). Xoa dong cua cap tu ngay mai tro di roi ghi lai; Lower/Upper =
  +-1,2816 x do lech sai so mot buoc; `Forecast Quality %` = 100 - WAPE HW. Du bao la muc nen, KHONG cong khuyen mai, vi
  `Calc-LSForecast` tu cong Planned Sales Demand. Ngay thieu Forecast Entry thi LS dung ban binh quan neu
  `LSC Forecast Setup."Forecast Exception Handling"` = Use Average Usage Result (demo setup dam bao). Web service
  `NWVAgentCalcService.SetForecastPublishing(publish, horizonDays)`.
- **Demo:** 33310 Choco pillar va 33341 Choco bowl doi sang `LSC Replen. Calculation Type` = LS Forecast (caption Retail
  Forecast); 33323 Choco nuts giu Average Usage de dat canh nhau. `ls_replen_setup.ngay_su_kien()` tao 4 Planned Event:
  KM-CHOCOPILLAR-07 va SK-ICECREAM-08 (dung PROMO, EVENT cua demo_scenario), KM-CHOCOPILLAR-09 va KM-CHOCOBOWL-09
  (23-25/09, sap toi). Ket qua LS: 33341 S0010 du bao 24,2 cong khuyen mai thanh 38,66 tru ton 34 ra 5; S0001 ra 10;
  33310 S0001 94,21 thanh 129,79 nhung ton 154 nen 0. Knowledge van nhan dang 100% (2.831 dong).
- **So tren BC (74 cap, 22/08-18/09, da bo ngay su kien):** MA28 38,2%, SWA8 37,2%, HW 37,1%. Truoc khi bo ngay su kien
  MA28 38,7%, SWA8 41,2%: khuyen mai thang 7 lam SWA8 lech nhieu nhat. `uc1-reconcile` so ca 222 dong (ca tham so) va 2.072
  dong Forecast Entry voi `forecast.backtest_bc(..., planned, forward=[])`: trung khop hoan toan.
- API page moi: 70282 `lsForecastEntries`, 70283 `plannedSalesDemands`. Permission: RIMD LSC Forecast Entry trong
  NWV AGENT REVIEW, R ca hai bang trong NWV AGENT LS READ.
- Tro ly: `du_bao` co HW, tham so, du bao 7 ngay toi va su kien sap toi; tab Du bao ve them 28 ngay toi va to vang ngay su
  kien, link page LS 10012431 `LSC Forecast Entries`; `ls_giai_thich` nhanh Retail Forecast liet ke du bao tung ngay va su
  kien thay vi ban binh quan. `ls_knowledge._khop` gio so ca cach doc ghep hai Label voi cach khop tron, chon cach de lai it
  chu chua giai thich (dong "%1 found within ... %1 adjusted from ..." truoc day bi doc thanh mot Label).
- Anh demo `docs/anh-demo/` va tai lieu 08 chup TRUOC dot nay (UC1 con 2 phuong phap).

### CTKM cua LS tren tro ly, 14/09/2026 chieu

Dung hoi "tren agent truy cuu, hoi dap duoc cac CTKM sap toi, hien co khong". App `NWV Marou Agent` **1.5.1.0**, `NWV Marou
Demo Setup` **1.5.0.0**, da publish NWV01.
- **Nguon chuan LS** (doc source 28.0.10.3586): `LSC Periodic Discount` 99001453 (Type Multibuy, Mix&Match, Disc. Offer, Total
  Discount, Tender Type, Item Point, Line Discount; Starting/Ending Date la FlowField tu `LSC Validation Period` 99001481),
  `LSC Periodic Discount Line` 99001454 (Item, Item Category, Product Group, Special Group, All, Exclude), `LSC Store Price
  Group` 99001575 (Price Group rong = moi cua hang). LS noi CTKM voi Replenishment bang Planned Event Source Type = Discount,
  Source Code = so CTKM, bao cao 10012219 `Update Planned Sales Demand from Discount` sinh dong nhu cau.
- API page chi doc 70284 `lsPeriodicDiscounts`, 70285 `lsPeriodicDiscountLines`, 70286 `lsStorePriceGroups`, 70287
  `plannedEvents`, 70288 `lsValidationPeriods`; quyen R trong NWV AGENT LS READ.
- **Bay khi tao CTKM bang code:** dau dang Enabled thi OnModify cua dau, dong, va Validation Period dang dung deu bao loi, phai
  tat truoc; Validate Status = Enabled goi CheckOffer, bao loi neu Ending Date < Today (nen CTKM da qua de Disabled); Validate
  "No." goi TestManual cua No. Series cua cua hang, gan truc tiep roi Insert. OnValidate Source Type/Code cua Planned Event hoi
  Confirm khi da co dong: web service khong co UI, gan truc tiep.
- Demo (`ls_replen_setup.chuong_trinh_km`): MR2607-CP (thang 7, FOOD, Disabled), MR2609-CP (Choco pillar -20% 23-25/09, FOOD,
  Planned Event du S0001, S0002), MR2609-CB (Choco bowl -15% 23-25/09, ALL, Planned Event chi S0001, S0010: **co y lech**, tro
  ly phai chi ra S0002, S0005 chua co nhu cau), MR2609-CR (banh sung bo -30% 01-30/09 19h-22h, khong Planned Event).
  KM-CHOCOPILLAR-09 them S0002; LS tinh lai van ra Choco bowl S0001 = 10, S0010 = 5.
- Tro ly: intent `PROMO` (rule, truoc BRIEF, nhuong REPLEN_WHY va FORECAST), `skills/khuyen_mai.py`, MCP tool `promotions`,
  mot dong trong brief cua supply_chain, dieu phoi, quan ly cua hang, nut POC "CTKM dang chay va sap toi". Trang thai: dang
  chay, sap toi, chua bat (Disabled ma sap/vua toi ngay), da tat (Disabled tu truoc 28 ngay, chi dem), da ket thuc. Chi liet ke
  CTKM co mat hang ban trong 90 ngay tai cua hang ap dung (NWV con 31 CTKM Cronus dang bat cho hang thoi trang, golf).
  Canh bao thieu nhu cau chi voi CTKM sap toi hoac bat dau trong 28 ngay, vi CTKM chay tu lau da nam trong lich su ban.
- Lan thu brief dieu phoi tren BC ngay 14/09 ghi 2 de xuat that (Choco bowl S0001 = 10, S0010 = 5), trung so LS, de nguyen.
- Chua lam: giai Product Group va Special Group ra mat hang; Deal (`LSC Offer` 99001502) chua doc.

### Prompt mau theo vai tro va tai lieu demo noi bo ban 2.0, 14/09/2026 chieu

- `python/assistant/goi_y.py`: prompt mau theo vai (quan ly cua hang theo tung cua hang, dieu phoi, kho, Supply Chain,
  Retail Ops, quan tri), `GET /api/goi-y?user=`. Man hinh chao hien 4 the lon va hang "Goi y khac"; danh dau cau can bat AI
  va cau ghi de xuat vao BC. Mon cua quan ly cua hang chon theo so LS tren BC: S0001 Choco nuts, S0002 Ice cream, S0005
  Tiramisu, S0010 Choco bowl, S0013 Milk 1 liter. `tests/test_goi_y.py` gui tung cau cua tung nguoi dung demo (145 test).
  Da chay het cau chi doc tren BC: dung het.
- Sua khi thu prompt: quan ly cua hang hoi ton "o cua hang toi" gio noi cua hang minh truoc, ke ca khi da het (truoc do
  Lan hoi Choco nuts S0001 = 0 thi cau tra loi khong nhac S0001); brief quan ly cua hang dem de xuat dang cho tu BC
  (`de_xuat_gop`) thay vi bo nho tro ly (truoc bao 0 trong khi BC co 4).
- Dai do "Khong chay duoc. Failed to fetch" la may chu dang khoi dong lai (`--reload` sau moi lan sua file Python). Gio vong
  poll noi ro mat ket noi va tu tat dai do khi ket noi lai.
- Tai lieu 08 viet lai thanh **ban 2.0** (`docs/build_08.js`, 39 trang): thong diep va checklist chuan bi, kien truc, prompt
  mau theo vai kem cau tra loi that tren BC (doc `docs/demo/goi-y.json`), 8 man demo kem 25 anh, muc dap ung UC, muc 6
  chi tiet cach xu ly (du bao Holt-Winters tung buoc voi vi du Choco bowl S0010, LS Replenishment ba kieu tinh, CTKM, ton
  kho, scorecard, tro ly), cau hoi hay gap. Anh chup lai bang `tools/chup_man_hinh.mjs` (them 01b, 01c, 03b, 05b, 16, 16b,
  17, 18). Anh kien truc cap nhat 1.5.1.0, 33 API page, 16 tool MCP.
- Doc PDF cua docx tren may nay: Word COM (`SaveAs2` dinh dang 17) roi `pypdfium2`; khong co soffice va pdftoppm.

### UC2: kim chi nam 4 nhom nang luc AI va hai tai lieu, 14/09/2026 toi

Dung nhan xet: tinh nang UC2 "deu thay la application, khong thay AI can thiep nhieu". Chot kim chi nam: moi tinh nang AI
cua agent phai thuoc mot trong bon nhom **Tom tat, Tao sinh noi dung, Kham pha va phan tich insight, Tu dong hoa**;
tinh nang khong thuoc nhom nao la tinh nang ung dung. Nguyen tac: BC tinh so, AI khong tinh lai; moi dau ra AI co nguon;
hanh dong ghi so qua policy va nguoi duyet; AI bat tat duoc, co tran chi phi; model chi nhan ket qua tool da loc.
- Hien trang doc code: trong UC2 model chi o hai cho, planner cau hoi mo (D1) va write_rationale viet lai ly do de xuat
  (G1), ca hai khi bat AI. Brief, hoi het han, truy xuat la rule; de xuat va duyet la luong ung dung.
- Danh muc 17 tinh nang AI co ma S1-S4, G1-G4, D1-D5, A1-A4 nam trong `docs/build_uc2.js` (mang AI). Thu tu de xuat lam
  tiep: S1 brief do AI viet, S2 giai thich lo bang loi, D4 goi y hanh dong toi uu cho lo can date (sua luon viec de xuat
  chuyen ca ton lo), G2+A3 luong huy khep kin co chung tu nhap, A2 tu quet va nhac qua Teams.
- `docs/build_uc2.js` ra hai file tu cung noi dung: "09 UC2 Inventory Health - Tai lieu tinh nang (noi bo).docx" (26
  trang, co kim chi nam, bang chung, luong, khoang trong, KPI; khong co cau hoi khao sat) va "10 UC2 Inventory Health -
  Gioi thieu tinh nang va khao sat (ban gui khach).docx" (21 trang: gioi thieu, 4 nhom nang luc voi muc dap ung, user
  story, man hinh, 8 cau hoi khao sat dat gia moi cau nham mot tinh nang AI cong 2 cau xac nhan du lieu, da bo phieu cham diem dau; khong co bang chung ky thuat, luong,
  khoang trong, de xuat them, cach khao sat). Ban 09 cu (co khao sat) va build_09.js chuyen vao `_to_delete/superseded`.
- **Brand kit Word "Aqua Blue & Warm Sand"** (Dung gui 14/09/2026) nam trong `docs/lib_brand.js`, cung API voi lib.js cong
  `ghiChu()` (nen Ice Blue #DAEEF3, vach Aqua #4BACC6) va `luuY()` (vach Warm Sand #C89B72): Aptos Display 20pt / Aptos Semibold
  14 va 12pt co vach Aqua trai / Aptos 11pt / caption Aptos Italic 9pt, chu Graphite #27343A, A4 le 20 mm, gian dong 1,15, bang
  header nen Aqua vien 0,5 pt dem 2 mm lap header, header trang "NaviWorld | MAROU • ..." va footer co duong ke Aqua.
  Tai lieu moi dung lib_brand.js.
- Cau hoi khao sat da sua theo hai entity (xem muc Khao sat Marou): khong con cau POS quet lo.
- Hai tai lieu da ra van phong bang skill `natural-writing` (Dung hoi co dung chua, lan dau chua). Viet tai lieu phai goi skill do.
- Slide "11 UC2 Inventory Health - Kien truc va kich ban (slide).pptx" (20 slide, 15/09/2026): kien truc ve bang shape, luong du lieu,
  phan tang, 10 kich ban dau vao / thao tac / dau ra kem anh, muc dap ung. `python tools/cat_anh_slide_uc2.py` cat anh vao
  `docs/uc2/slide`, roi `cd docs; node build_slide_uc2.js`. pptxgenjs cai o `C:\Users\dungdt.NWV\node_modules`. Soat hinh bang
  PowerPoint COM `Slide.Export` (may khong co soffice). Margin o bang cua pptxgenjs tinh bang inch, margin cua text box tinh bang point.
- Anh `docs/anh-uc2` chup bang `node tools/chup_uc2.mjs` (anh 10-12 tam doi nguon sang mo phong de khong ghi de xuat that);
  so do luong `docs/uc2` ve bang `python tools/ve_luong_uc2.py`.
- Sua cung dot: `uc2-reconcile --from al` het KeyError dong de xuat dieu chuyen; lo NearExpiry con 0 ngay bam chuyen thi noi
  "het han hom nay" thay vi "da het han".

### Hai company NWV-MAROU va NWV-DAKAO, email nhac post, 15/09/2026

Dung tao hai company tren NWV01: **NWV-MAROU** (san xuat, co lo) va **NWV-DAKAO** (ban le, khong lo). Luc tao, ca hai la
ban sao y het company NWV (25.177 ILE, 167 dong Inventory Health, 22 de xuat, ngay chot 18/09). Dung chot: du lieu Dakao
con lo thi ke, Marou con cua hang thi ke, dung lai du lieu sau.
- **Ket noi da kiem:** Entra app doc duoc ca hai company (permission set gan cho moi company, khong 403). Web service
  `NWVReplenService.ReadTable` va `NWVAgentCalcService.RunCalculations INVHEALTH` chay o Dakao, ghi 167 dong. App cai theo
  environment nen khong phai publish lai.
- **Python:** `.env` co `BC_COMPANIES=NWV-MAROU,NWV-DAKAO`, `BC_COMPANY_NAME=NWV-MAROU` (mac dinh cho cong cu dong lenh).
  `assistant/cong_ty.py`: vai nao o company nao (quan ly cua hang va Retail Ops o Dakao; kho o Marou; Supply Chain, dieu phoi,
  quan tri o ca hai). `web.py` giu **moi company mot tro ly rieng** (bo nho, de xuat, policy rieng), dung khi co request dau
  tien. Giao dien gan header `X-Cong-Ty` vao moi lenh goi (boc `window.fetch`); middleware ASGI dat ContextVar
  `cong_ty.hien_tai`, `bc_link` doc ra de link BC mo dung company. Nguoi chi co mot company thay nhan co dinh, nguoi co hai
  thay hai nut tren dai nguon. `tools_bc.py --company NWV-DAKAO ...`. Cong tac AI, tran chi phi, policy ap cho moi company.
  Test gan `web.state["asst"]` van chay (moi company dung tro ly do).
- **Nhac post nhan hang** (`skills/nhac_post.py`, intent `NHAC_POST`): cua hang bam "Hang da ve, chua nhap" thi tro ly gui
  email ngay cho bo phan post (`MAIL_TO`); moi sang 08:00 (`NHAC_POST_GIO`, thread trong web.py, ghi `runs/lich-nhac.json`)
  va khi Supply Chain go "gui mail nhac post" thi nhac lai qua chat va email; don khong con Outstanding thi bao da post va
  dong viec. Danh sach don, so luong, ngay, link BC do code dien; model chi viet doan mo dau va cau ket, doan co chu so khong
  co trong du lieu thi bo, dung mau. Chong gui trung theo khoa trong ngay (ngay theo dong ho tro ly, co dong ho ao).
- **Gui mail** (`assistant/thu_dien_tu.py`): MAIL_MODE auto: `MAIL_SENDER` thi Microsoft Graph sendMail bang chinh Entra app
  (can quyen Mail.Send loai Application + admin consent, Dung tu cap; ngay 15/09 token Graph cua app chua co role nao),
  `SMTP_HOST` thi SMTP, khong co gi thi chi luu `.eml` vao `runs/thu-di/`. Moi thu ghi `runs/thu-di.sqlite`, xem
  `GET /api/thu-di?user=dung.admin`. `MAIL_TO=dungdt@naviworld.com.vn`. Test luon ep kenh file (conftest).
- Bat duoc khi chay that: thu dau ghi "lan nhac thu 2" (dem hai lan); model viet ngay 13/09 nhung du lieu dua model thieu
  ngay du kien nen bi loai; the tra loi cua hang hua "da gui email" trong khi hom do da gui roi. Da sua ca ba, 516 test.
- Chua lam: Job Queue theo tung company (chua kiem trong ban sao), brief Supply Chain gop hai company, luong intercompany.
- **Email qua Graph tren tenant CONTOSO khong gui duoc**: Dung da cap Mail.Send + admin consent (token co role), nhung moi
  hop thu trong tenant (admin@, NestorW@, LidiaH@M365x87729130.OnMicrosoft.com) tra `MailboxNotEnabledForRESTAPI`, tuc khong
  co license Exchange Online. Duong con lai: SMTP (Gmail App Password) hoac app Graph rieng trong tenant NaviWorld.
- Dung chot: hang tu Marou giao thang toi tung cua hang Dakao, khong qua kho trung tam Dakao.

### Dot 1 hai company: Dakao mua thang tu Marou, giao toi tung cua hang, 15/09/2026 chieu

Dung chot: hang tu Marou giao thang toi cua hang Dakao, khong qua kho trung tam Dakao; tu tao doi tac MAROU va DAKAO;
Default Central Warehouse cua NWV-MAROU da sua ve W0003.
- `NWV Marou Demo Setup` **1.6.1.0**: codeunit 70258 `NWV Demo Intercompany` (web service `NWVDemoIntercompany.EnsurePartners`)
  tao vendor MAROU trong NWV-DAKAO (posting group chep tu 44020) va customer DAKAO trong NWV-MAROU (chep tu customer "1").
  `Apply` nhan them cho item `vendor`, `fromWarehouse=false` (xoa quy tac Replen. From Warehouse), `purchOrderDelivery`
  ("To Store") va cho template `purchaseOrderType` ("Receiving Locations").
- `tools/ls_replen_setup.py --company NWV-DAKAO partners|apply|calc`: cau hinh Dakao = Item."Vendor No." MAROU,
  `LSC Purch. Order Delivery` = To Store, template MAROU-PO kieu "Purchase Orders for Receiving Locations", Location Code
  rong (mau RT00003 cua Cronus). **Doc trong Calc. Log cua LS:** journal Receiving Locations chi xet mat hang To Store,
  mat hang To Warehouse ghi "NOT processed"; ma To Store thi journal chuyen hang MAROU-TO khong xet nua (Dakao: 0 dong).
  Ket qua Dakao: MAROU-PO 19 dong, 71 chi tiet, 13 co so luong mua, 33323 x S0001 = 82 tu MAROU (bang so TO truoc day).
  Vendor tren RIQ lay theo FindReplenVendor: Replen. Item Store Rec, SKU, roi Item.
- Tro ly: `BCGateway.goi_y_ls` doc ca hai template, dong mua ve kho bo, dong mua thang cua hang co `replenType=Purchase`,
  `vendorNo`, `sourceLocationCode` = vendor. Brief dieu phoi chi BAO dong mua (the thong tin, link journal MAROU-PO), khong
  tao de xuat chuyen; `ls_giai_thich` tim journal TO roi PO. Chua co loai de xuat "mua" trong bang NWV Agent Proposal va chua
  co luong tao PO intercompany: viec dot ke tiep.
- NWV-MAROU chua doi: van MAROU-TO tu W0003 va MAROU-PO ve kho, cho den khi dung lai du lieu.

**Toi 15/09/2026, tiep:**
- Email SMTP Gmail da gui that (App Password Dung dien vao `SMTP_PASSWORD`; `.env` co du SMTP_HOST/PORT/USER/PASSWORD). Thu dau
  di kenh smtp trang thai `da_gui` toi dungdt@naviworld.com.vn. Doi `.env` phai khoi dong lai server (Settings doc luc import).
- `NWV Marou Demo Setup` **1.6.2.0**: `NWVDemoRepost.DeleteProposals(confirmText, actionType)` xoa de xuat theo loai o company
  NWV-*. Da xoa 19 de xuat Transfer sao chep trong NWV-DAKAO (con 3 WriteOff). NWV-MAROU van giu 22 de xuat cu.
- `NWV Marou Agent` **1.5.3.0**: enum NWV Proposal Action them `Purchase` (8), bang de xuat them field 16 `Vendor No.`, API
  `vendorNo`. `NWV Agent Proposal Mgt.Execute` Purchase -> `CreatePurchaseOrder`: Purchase Header Order, Buy-from = Vendor No.,
  Location = To Location, Your Reference 'AGENT <id>', mot Purchase Line; trang thai Open, khong release. Permission set
  NWV AGENT REVIEW them Purchase Header/Line = RIM. Da duyet that mot de xuat o NWV-DAKAO: **PO HO106199**, 1 Blueberry
  muffin tu MAROU giao S0010.
- Tro ly: brief dieu phoi o Dakao tao de xuat loai Purchase (vendor tu dong LS), the "De xuat dat mua" nut "Duyet dat mua";
  policy P-11 StoreReplenishment/Purchase = APPROVE; duyet thi bao PO kem link, khong bao kho ship. `memory.proposals` them cot
  `vendor_no`. Mock gia lap PO-xxxx. 517 test.
- Chua co: Intercompany (PO cua Dakao thanh Sales Order ben Marou): can Intercompany Partner, IC Setup Auto Send/Accept.

### UC2 nhom Tom tat: S1 brief do AI viet, S2 giai thich lo bang loi, 15/09/2026 toi

Dung nhac: ke hoach phai tap trung tinh nang AI cho UC2, khong troi sang viec ung dung (intercompany, dung lai du lieu). Thu tu
lam theo tai lieu 09: S1, S2 (xong), roi D4, G2+A3, A2. `assistant/skills/uc2_tom_tat.py`, 10 test `tests/test_uc2_tom_tat.py`, 527 test.
- **Cach lam chung, giong email nhac post:** code doc bang Inventory Health da tinh, chon dong ung vien, tinh "du kien du"
  (ton tru ban duoc truoc han), tim cua hang ban nhanh hon, gom de xuat dang cho va ly do tu choi 14 ngay gan day (tu
  `outcome_note`, `on_reject` gio luu ly do). Model chi viet loi theo JSON schema. Sau khi model viet: moi chu so phai co trong
  du lieu dua model, moi dong chon phai co trong danh sach; sai la dung mau do code ghep, the ghi ro "Nguoi soan: mau co san
  (ly do)". Tat AI thi khong goi model. Chi phi ghi muc `brief` va `giai_thich_lo` tren trang Cai dat AI.
- **S1** `brief_ai`: the kind `brief` "3 viec quan trong nhat sang nay" (mo dau, 3 viec kem ly do, ket) len dau brief cua
  Supply Chain, va them vao brief quan ly cua hang (chi cua hang minh); the tung dong xep dong duoc chon truoc. Link mo so kho
  cua tung lo. Chay that tren NWV-MAROU: 22,8 giay (phan lon la doc BC), model chon 3 lo Croissant - plain, cau dung so.
- **S2** `giai_thich_lo`, `GET /api/uc2/giai-thich?line_id=`: doan 3-5 cau tren trang Chi tiet lo, muc "Noi bang loi" ngay duoi
  ten lo, tu load. Doan AI nho theo dong va `calculatedAt` (kv `giai_thich_lo:<id>|<calculatedAt>`) nen mo lai khong tra tien.
  Chay that: Choco pillar S0010 6,4 giay, dung; lo Choco nuts het han bi bo vi model viet "07" (doc ma lo L260720 thanh ngay
  20/07, tuc tu suy ra), roi ve mau. Day la dung y thiet ke, dung noi long phep kiem so.
- Gioi han da biet: phep kiem so theo `\d+` nen so nho (1, 2) gan nhu luon co trong du lieu; model bia "2 lo" thi khong bat duoc.
  Model chon viec theo diem rui ro nen ba viec co the cung mot mat hang; muon da dang thi them quy tac vao prompt, chua lam.

### UC2 D4: goi y hanh dong toi uu cho lo can date, 16/09/2026

`assistant/skills/uc2_hanh_dong.py`, 7 test `tests/test_uc2_hanh_dong.py`. Thay nut "Chuyen sang store ban nhanh" (de xuat chuyen
CA TON LO sang cua hang ban nhanh nhat, khong xet ho co ban het khong) bang nut "Phuong an xu ly" tren the lo can date.
- **Code tinh** (`phan_tich`, ham thuan): ban duoc tai cho truoc han = ban binh quan x ngay con lai (lam tron xuong), phan du;
  kha nang nhan cua tung cua hang = ban binh quan cua ho x (ngay con lai - 1 ngay van chuyen) - ton ho dang co; chuyen greedy toi
  da 2 noi; bang phuong an giu / chuyen / chuyen + giam gia / giam gia / huy kem gia tri cuu duoc hay mat theo gia von; mot de xuat
  theo quy tac. Muc giam gia chua co quy tac cua Marou (G3) nen de xuat giam gia chi mang so luong.
- **Model chon va giai thich** (`goi_y`, muc chi phi `d4`): doc bang phuong an, chon mot khoa, viet vi sao; duoc chon khac code neu
  noi duoc ly do tren so da co. Kiem: khoa phai co trong bang, moi chu so phai co trong du lieu; sai thi ve de xuat cua code va cau
  mau. Nho theo dong va `calculatedAt` (kv `d4:`).
- **Nguoi ghi de xuat** (`on_ap_dung`, verb `ih_d4_apply`): moi phan mot de xuat, khoa rieng `item|kho|lo|TO|<den>`, `|MD`, `|WO`,
  `|GIU` de khong bi coi la trung nhau; `inventory_health.on_propose` nhan `quantity`, `ref`, `rationale` va gio ghi `value_vnd`
  (so luong x gia von) nen policy P-06 (chuyen lo can date gia von duoi 100 tu lam) xet duoc gia tri that.
- Trang Chi tiet lo co muc "Phuong an xu ly" (`GET /api/uc2/phuong-an`) cho lo NearExpiry: bang phuong an va loi khuyen, chi doc;
  ghi de xuat thi qua the trong Tro chuyen.
- Chay that NWV-MAROU (AI bat): Choco pillar S0010 470 cai con 25 ngay ban 10,8/ngay: giu thi du 199; S0001 (21,2/ngay, ton 154)
  nhan duoc 354 nen chuyen 199, du 0, cuu 218,90; model chon "chuyen", cau dung so, 5,5 giay. Choco bowl S0005 chuyen 74 sang S0001.
  Carrot cake W0003 ban het truoc han, model chon "giu". Loi van cua model doi cho lung cung ("chuyen dung ngay 1") nhung so dung.
- Gioi han: kha nang nhan gia dinh ton cua noi nhan ban het truoc (khong xet han cua ton do); chua tinh chi phi van chuyen; chua co
  phuong an "dung noi bo" vi chua co du lieu.

### UC2 G2 + A3 luong huy khep kin, A2 quet sang tu dong, 16/09/2026

App `NWV Marou Agent` **1.6.1.0** da publish NWV01. `assistant/skills/uc2_huy.py`, `uc2_quet.py`, 8 test `tests/test_uc2_huy_quet.py`.
- **BC (codeunit 70102):** duyet de xuat Write-off tao dong Item Journal Negative Adjmt. CHUA POST trong template/batch/reason cua
  Setup (field 70-72, mac dinh ITEM / AGENT / AGENT-EXP, tu tao neu thieu, batch bat Item Tracking on Lines de Lot No. song),
  Document No. `AGENT-<Entry No.>`, Result Document Type 'Item Journal Line'. Lan dau dung Proposal Id (GUID) nen ra
  `AGENT-{F8D9F9A9-AF40`, da doi sang Entry No. (1.6.1.0); dong thu do (1 Blueberry muffin S0010) van nam trong batch AGENT
  cua NWV-MAROU, xoa tay hoac post. API page 70289 `nwvItemJournalLines` chi doc. Permission REVIEW them Item Journal
  Line/Batch RIM, Template va Reason Code RI; RUN them Item Journal Line R. Khong co quyen post.
- **G2 bien ban** (`uc2_huy.soan_bien_ban`, muc chi phi `bien_ban`): code dien bang so lieu (lo lay tu dong journal vi bo nho tro ly
  khong luu lot_no), model viet `dien_bien` va `de_nghi`, kiem so nhu S1. The cho nguoi duyet va nguoi de nghi, email cho MAIL_TO
  kem link page 40 loc batch. `replenishment.on_approve` re nhanh khi Result Document Type = 'Item Journal Line'.
- **A3 theo doi** (`uc2_huy.theo_doi`, followup kind `write_off_post`, 24 gio mot lan): co ILE cung Document No. thi bao "da post",
  dong viec; con trong journal thi nhac lan N qua chat + email (mot thu mot ngay), lan 3 bao nguoi duyet; khong con trong journal
  ma khong co ILE thi bao co the bi xoa, dong viec. Mock: `gw.gia_lap_post_journal()`, nut demo "Gia lap ke toan post chung tu huy",
  `POST /api/demo/post-huy`.
- **A2 quet sang** (`uc2_quet.quet`): lo het han chua co de xuat -> tu ghi de xuat Write-off (nguoi de nghi `tro_ly`, toi da 10 mot
  lan, P-05 bat nguoi duyet); lo can date moi con du -> the D4 cho Supply Chain (toi da 3); brief S1 cho Supply Chain va tung cua
  hang, ban Supply Chain gui email; nhac de xuat cho duyet qua 1 ngay; chay followups. Da bao thi kv `quet_da_bao:<lo>`, mot ngay
  mot lan (kv `quet_uc2_ngay`), `POST /api/quet-uc2 {user, chay_lai}`, nut demo, lich nen `QUET_UC2_GIO` (mac dinh 07:30, thread
  `_chay_lich_nhac` gio chay ca hai viec, khoa `<company>|quet_uc2` trong runs/lich-nhac.json).
- Chay that NWV-MAROU 16/09: duyet huy Blueberry muffin S0010 -> dong journal that co lot va reason, bien ban AI dung so, email
  da gui, 11,6 giay. Quet sang: 112 giay, 10 de xuat huy ghi vao BC (Proposed, cho Hung duyet), 3 phuong an, brief 5 nguoi, email.
- Bay: chay smoke ngoai pytest thi conftest khong chan email, thu di that (4 thu sang 16/09 la thu nghiem). Server `--reload` mat
  bo nho `Memory(":memory:")` moi lan sua file Python, nen hop thu trong sau khi sua code.

### UC2 D3 bat thuong, D2 nguyen nhan huy, S3 bao cao tuan hang huy, va QA AI, 16/09/2026

`assistant/skills/uc2_bat_thuong.py`, `uc2_nguyen_nhan.py`, `uc2_bao_cao_huy.py`; 15 test `tests/test_uc2_phan_tich.py`; 558 test.
Nguon chung: `BCGateway.ile_cua_so(days)` (moi loai ILE, live doc theo cua so chung `CUA_SO_BAN` roi loc, mock lay `_ILE_DEMO`),
`gw.la_kho(loc)`. Trong bo demo va tren BC: cua hang nhan bang Positive Adjmt., huy bang Negative Adjmt. co lo ngay sau khi het han;
khong co dong Sale sau han; document no rong.
- **D3** (`quet`, 28 ngay, chi cua hang): 5 tin hieu ban_sau_han, nhan_han_ngan (han luc nhan < 1/2 trung vi mat hang), huy_tang
  (14 ngay gap doi 14 ngay truoc, >= 5), ton_khong_ban (7 ngay khong ban ma noi khac ban), het_hang_lap (StockOutRisk, censored >= 5).
  "Lech kiem ke lon" khong lam duoc: khong co phieu kiem ke / reason code. Model chon toi da 3 id va viet nhan xet (kiem id + so).
  Intent `ANOMALY`, `GET /api/uc2/bat-thuong?noi=`, cua hang chi thay cua hang minh. BC that: 16 tin hieu (15 nhan han ngan, 1 het
  hang lap), model uu tien T2-T4 deu o S0001.
- **D2** (`phan_tich`, 90 ngay): moi cap mat hang x cua hang co huy: nhan/ban (> 1,25 nhan du), ban binh quan so voi cua hang khac
  (< 0,7 ban cham), han luc nhan so voi trung vi (< 0,7 han ngan), lan nhan lon nhat > 1,5 x ban binh quan x han thong thuong
  (don cuc; nguong 1,0 bat 22/25 cap nen vo nghia). "Chuyen tre" khong do duoc (khong co TO). Model viet ket luan. Intent
  `WASTE_WHY` ("vi sao X huy nhieu", ten cua hang qua `_tim_cua_hang`), `GET /api/uc2/nguyen-nhan-huy?item=&noi=`.
  BC that: Chocolate cake 355 cai, S0001 huy 41,9% so nhan.
- **S3** (`so_lieu`, tuan 7 ngay so tuan truoc, top mat hang va cua hang theo gia tri, lo het han con ton, de xuat huy cho duyet,
  chung tu chua post, nguyen nhan D2 28 ngay): model viet mo_dau, nhan_xet, viec_tuan_toi. The kind brief cho Supply Chain va admin,
  email mot lan moi tuan ISO. Intent `WASTE_REPORT`, `POST /api/bao-cao-huy`, quet sang A2 tu gui vao thu Hai. Tuan 12-18/09 huy 0
  vi 45 lo het han chua post huy (dung, khong phai loi). Lan chay dau model viet "(trieu dong)" va "don hang": prompt gio noi ro
  don vi cai va khong them don vi tien.
- **QA AI tren NWV-MAROU 16/09 (AI bat, qua API tro ly):** S1, S2, D4, D3, D2, S3, G2 (bien ban), A2 deu ra "AI (gpt-4.1-mini)",
  so qua phep kiem; chat ba intent moi di duong rule khong goi model. Chi phi ca ngay 0,085 USD / 146 luot. A2 chay lai them 10 de
  xuat huy, khong trung; NWV-MAROU dang co 31 de xuat WriteOff Proposed do quet (xoa bang `NWVDemoRepost.DeleteProposals` neu can).
  Bay: server `--reload` moi lan sua file la mat hop thu (Memory :memory:), QA qua API phai doc lai ngay sau khi goi.

### Bo nho tro ly xuong dia, don de xuat huy, kien truc 16/09/2026

- `web._bo_nho(live, ten)`: moi company va moi nguon mot file `runs/bo-nho-<bc|mock>-<company>.sqlite` (hop thu, de xuat, viec theo
  doi A3, kv gom doan AI da soan va lich quet). `--reload` hay khoi dong lai khong mat gi nua. Nut Reset (`POST /api/reset`) xoa file
  cua nguon dang chay; doi nguon (`/api/mode`) giu file. Duoi pytest van dung ":memory:". Da kiem: hai file tao ra, 10 user moi file.
- Da xoa 34 de xuat WriteOff trong NWV-MAROU (`NWVDemoRepost.DeleteProposals`, ca Proposed lan Executed).
- `NWV Marou Demo Setup` **1.6.3.0**: `NWVDemoRepost.DeleteJournalLines(confirmText, templateName, batchName)` xoa dong Item Journal
  chua post trong mot batch o company NWV-*; bat buoc ten batch (khong xoa ca Item Journal). Da xoa hai dong thu cua luong huy trong
  batch ITEM/AGENT cua NWV-MAROU (AGENT-{F8D9F9A9-AF40 va AGENT-95). Kiem lai: batch AGENT rong, khong ILE nao mang hai Document No.
  do, ton hai lo khong doi (33116 L260908-33116B 9, 33130 L260910-33130 17) vi dong chua post. Dong ITEM/NWVDEMO cua bo demo giu nguyen.
- **Hai so do kien truc, dung hai cho khac nhau** (Hung dev de nghi 16/09: hinh chi tiet present cho nguoi moi thi mat thoi gian
  nam bat, can them mot hinh tong quan tach bach thong tin). `kien-truc-tong-quan.html` + `.png` (1600x1025): mot vong
  Nguoi dung <-> Tro ly -> 1 Doc, 2 Suy luan, 3 De xuat va nhac, roi bang "Nguoi cua Marou bam Duyet -> BC tao chung tu nhap".
  Bo cuc theo mau Hung gui (User Request / AI Agent / Perception / Cognition / Action) nhung nhan va noi dung ANH XA sang he thong
  that, khong bung nhan cua mau (khong co camera, audio, sensor). Mau theo bo tai lieu Marou de hai hinh noi duoc voi nhau:
  xanh = doc tu BC, vang = phan AI, do = tro ly va hanh dong. Mo dau buoi present bang hinh nay, hinh chi tiet de phan sau.
- So do kien truc `docs/kien-truc/kien-truc-chi-tiet.html` viet lai theo trang thai 16/09: hai company, email va lich nen, dai
  "AI o dau trong UC2" bon nhom 12 tinh nang, lop 3 co Purchase va WriteOff, 34 API page. Render: Chrome headless
  `--screenshot --window-size=1800,3400` roi cat day bang Pillow (lenh trong lich su phien, khong co script rieng).

### Vai tro dia diem doc tu LS Central, app 1.5.2.0, 15/09/2026

Dung bac hai field tren NWV Agent Setup: `Central Warehouse Code` trung `LSC Replen. Setup."Default Central Warehouse"`,
`Store Location Filter` khong duoc phep tinh nao dung. Da lam:
- Codeunit 70112 `NWV Location Role`: store = `LSC Store."Location Code"` (Store Type = Store) hoac `LSC Store Location`
  (10001416); warehouse = Default Central Warehouse / Warehouse 2 / 3 cua Replen. Setup hoac `Location."LSC Location is a
  Warehouse"`. `NWV Demand Calc.Build(AsOf, Days)` bo tham so kho; kho nao cung lay Outflow. Forecast chi do cap `IsStore`.
- Hai field cu ObsoleteState = Pending (khong doi schema), bo khoi page. Nhom Locations tren page hien Central Warehouse va
  so store (chi doc). Moi caption va ToolTip cua Setup, page va action doi sang tieng Anh (Dung yeu cau).
- API `nwvLocations` them `isStore`, `storeNo`, `isWarehouse`, `isCentralWarehouse`. `BCGateway.central_wh` tren BC that doc
  tu day (mot lan, TTL 1 gio), mock giu W0003. Permission set NWV AGENT LS READ them `LSC Store Location` = R.
- Kiem sau publish: ca hai company van 167 dong 45/32/47/4/1/38, 222 dong forecast, 2.072 Forecast Entry. W0001-3 co co
  Warehouse nen nhu cau kho khong doi. **NWV-MAROU dang de Default Central Warehouse = W0001 (Cronus)**, Dakao = W0003;
  Dung can sua Replen. Setup cua NWV-MAROU ve W0003, neu khong tro ly o Marou de xuat chuyen tu W0001.
- Build: `"$DOTNET" "$ALC" /project:al/MarouAgentFoundation /packagecachepath:../Demo/.alpackages /outfolder:al/MarouAgentFoundation/out`
  (symbol LS nam o AL/Demo/.alpackages), publish `python tools_bc.py upload <app>`.

### UC3: tro ly bao don mua qua han nhan, lam ngay 13/09/2026 toi

`assistant/skills/po_qua_han.py`, intent `PO_OVERDUE` (rule, dat truoc BRIEF va TRACKING, khong goi model).
Doc `nwvPurchaseOrderLines` (page 70206 co san): dong con `outstandingQuantity` > 0 va `expectedReceiptDate`
truoc ngay neo. Gom theo so don x dia diem nhan, so ngay tre, nhan mot phan. Tre hon 60 ngay la don treo:
van bao nhung khong hoi cua hang.
- Supply Chain, dieu phoi, admin, Retail Ops thay het; cua hang va kho chi thay don ve dia diem minh.
- Supply Chain hoi thi tro ly GUI THE hoi nguoi nhan hang tai dia diem ("Hang da ve, chua nhap" / "Hang chua
  ve"), moi don hoi mot lan (kv `po_da_hoi:<so don>|<dia diem>`). Cau tra loi luu kv `po_xac_nhan:...`, bao
  Supply Chain kem viec can lam (post Receive, hoac hoi nha cung cap). **Khong ghi gi vao BC.**
- Brief sang cua supply_chain, store_manager, warehouse them mot dong neu co don qua han.
- MCP tool `overdue_purchase_orders`.
- Mock: `bc_agent/fixtures/purchase_order_lines.json` (7 dong kich ban Marou + 1 dong Cronus treo). 16 test trong
  `tests/test_po_qua_han.py`.
- BC that ngay 13/09/2026: chi 3 PO Cronus 2024-2025 (HO106121-3) tre 594-958 ngay, deu thanh don treo. Muon
  demo UC3 tren BC can tao PO demo cua Marou; chua tao, cho Dung dong y.

### Ngay 13/09/2026 toi

- Nhat ky agent chi quan tri (an tab va chan `GET /api/nhat-ky`). Doi vai tro thi ve Tro chuyen.
- `NWV Marou Agent` 1.0.1.0: nut **Delete All** tren page 70101, xoa theo bo loc dang ap, hoi xac
  nhan kem so dong, Transfer Order da tao khong bi dong. Can quyen D; NWV AGENT RUN chi co RIM.
  Da build sach, chua publish.

## Diem chua xac nhan, phai hoi chu khong doan

- Ai thuc su chu tri sang kien phia Marou: CFO hay IT & Digital Transformation.
- Mail CFO thang 6 con hieu luc hay da bi RFP thay the.
- OneTrace la gi, ai cung cap, du lieu ra sao (RFP nhac o use case truy xuat nguon goc).
- MMV First la gi (RFP nhac o use case service category).
- Co dua Microsoft Fabric vao pham vi khong, ai tra tien capacity.
- Marou that su chay BC SaaS hay on-prem, version nao. Toan bo cong viec hien tai dang lam tren
  tenant demo chu khong phai he thong that cua Marou.
