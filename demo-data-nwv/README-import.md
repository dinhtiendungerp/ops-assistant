# Bo du lieu demo Marou tren company NWV, environment NWV01

Tam file, import theo dung so thu tu trong ten file.

| File | Noi dung |
|---|---|
| `00-MasterData.xlsx` | cap nhat 21 mat hang co san, 92 Stockkeeping Unit, 71 dong Lot No. Information |
| `01` den `07-ItemJournals-*.xlsx` | 24.759 dong Item Journal, tu 22/03/2026 den 18/09/2026 |

Khong tao mat hang moi, khong tao dia diem moi, khong tao nhom hang moi. Tat ca deu la
master data co san cua company NWV.

## Ngay neo cua kich ban

Neo vao **18/09/2026**, tuc khoang mot tuan ke tu hom nay, cho khop voi lich demo.
Dat Work Date cua BC la 18/09/2026 khi demo thi moi con so "con bao nhieu ngay den han"
va "days of cover" trong tai lieu nay deu dung. Lech mot hai ngay thi khong sai ban chat.

Trong file co dong ghi ngay sau ngay import, do la co y. BC cho post ngay tuong lai mien la
Allow Posting To trong General Ledger Setup va User Setup khong chan.

## Tam ma co lot tracking

| Mat hang | Han dung | Ghi chu |
|---|---|---|
| 33110 Croissant - chocolate | 3 ngay | kich ban qua han |
| 33170 Chocolate cake | 5 ngay | lo bi khoa |
| 33130 Tiramisu | 7 ngay | kich ban can han |
| 10000 Milk 1 liter | 7 ngay | kich ban qua han |
| 10045 Cream 250 ml | 14 ngay | kich ban can han |
| 33341 Choco bowl | 180 ngay | nhan hang can date |
| 33323 Choco nuts | 240 ngay | qua han, va kich ban dieu chuyen |
| 33310 Choco pillar | 240 ngay | can han, va kich ban khuyen mai |

Tam ma nay can co Item Tracking Code `LOTALLEXP` va Lot Nos. `R-LOT` tren Item Card.
Kiem tren company NWV ngay 11/09/2026 qua API: chi `33310` da co san, bay ma con lai
deu chua co. Sheet Item trong file master data da dien san hai cot do cho ca tam ma,
import sheet do la xong.

Muoi ba ma con lai khong co tracking code, nen hai cot Lot No. va Expiration Date trong
Item Journal **de trong**. Dien lot cho mat hang khong co tracking code se bi BC chan luc post.
Toan bo 24.759 dong da duoc kiem lai tung dong dung quy tac nay.

## Do da dang cua lo va han dung

Moi mat hang co hang chuc lo khac nhau chu khong phai vai lo, va han dung lech nhau tung lo:

| Mat hang | So lo | So han dung khac nhau |
|---|---|---|
| 33110 Croissant - chocolate | 183 | 125 |
| 10000 Milk 1 liter | 159 | 106 |
| 33170 Chocolate cake | 124 | 91 |
| 10045 Cream 250 ml | 108 | 89 |
| 33130 Tiramisu | 70 | 64 |
| 33341 Choco bowl | 40 | 37 |
| 33323 Choco nuts | 40 | 40 |
| 33310 Choco pillar | 40 | 38 |

Co duoc nhu vay vi chu ky san xuat ngan hon nhieu so voi han dung, moi lan san xuat lai chia
thanh hai ba me (hau to A, B, C trong so lo), va han dung moi me lech nhau trong khoang
mot phan tam han dung danh nghia. Thuc te khong me nao giong me nao, du lieu cung khong nen giong.

So lo dat theo `L<yymmdd>-<so item><me>`, vi du `L260914-33110B`. Hau to `-SD` danh dau lo
nhan hang can date. Mot lo san xuat mot lan tai kho roi chia ve nhieu cua hang, nen cung mot
so lo xuat hien o nhieu dia diem. Do la ban chat cua bai toan truy xuat nguon goc.

## Truoc khi import

1. Gan Item Tracking Code `LOTALLEXP` va Lot Nos. `R-LOT` cho 33110, 33170, 33130, 10000, 10045.
   Gan duoc vi company NWV chua co Item Ledger Entry nao, ma `TestNoEntriesExist` trong
   `Item.Table.al` chi chan khi item da co phat sinh.
2. Mo Item Journals mot lan de BC tu tao Item Journal Template, roi tao batch ten `NWVDEMO`.
3. Neu General Ledger Setup hoac User Setup gioi han Allow Posting From / To thi mo tu 22/03/2026
   den het 30/09/2026.

Khong phai tao Item Tracking Code, khong phai sua posting setup: `LOTALLEXP` da co san
voi Strict Expiration Posting tat, va dong General Posting Setup (`` , `RETAIL``) cung da co san.
Strict Expiration Posting phai giu nguyen trang thai tat, vi trong du lieu co lo ban ra khi
da gan han va co lo qua han con nam tren so.

## Thu tu import

1. `00-MasterData.xlsx`: sheet Item truoc, roi Stockkeeping Unit. Sheet Lot No. Information de sau cung.
2. Post lan luot `01` den `07`. Moi file mot thang, khoang 3.500 dong. **Khong duoc dao thu tu**.
3. Import sheet Lot No. Information sau khi post xong bay file, vi lo phai ton tai truoc.

## Quy mo

| Entry Type | So dong | Y nghia |
|---|---|---|
| Purchase | 1.525 | nhap san xuat vao kho trung tam theo lo |
| Positive Adjmt. | 4.196 | nhan hang tai cua hang, giu nguyen so lo cua kho |
| Negative Adjmt. | 5.350 | xuat kho di cua hang, huy hang qua han, chenh lech kiem ke |
| Sale | 13.688 | ban le tai nam cua hang va ban si tu kho |

Dong hang: nhap san xuat vao `W0003` theo lo, chuyen ra cua hang bang cap Negative Adjmt.
o kho va Positive Adjmt. o cua hang giu nguyen so lo, roi ban tai cua hang. Xuat luon theo FEFO.
Khong lo nao am o bat ky thoi diem nao, da kiem lai toan bo bay file.

Cuoi ky con 166 to hop mat hang x dia diem x lo, 7.288 don vi. Chay lop tinh toan UC2 tren
chinh bo du lieu nay ra phan tang: 31 lo qua han (625 don vi), 38 lo can han (1.407 don vi),
48 to hop rui ro dut hang, 4 cham luan chuyen, 1 ton thua nang, 44 binh thuong.

## 21 mat hang, deu la ma co san

Uu tien chocolate: 33110 Croissant - chocolate, 33170 Chocolate cake, 33200 Chocolate ice cream,
33310 Choco pillar, 33323 Choco nuts, 33341 Choco bowl. Lay them nhom trang mieng, kem dong goi,
do uong va sua: 33100, 33116, 33120, 33130, 33150, 33160, 33250, 18120, 18200, 18230, 30091,
10000, 10045, 10070, 10100.

Bay ma dang de Unit Cost bang 0 tren Item Card. File master data dat gia von cho chung, vi khong
co gia von thi khong tinh duoc gia tri ton kho lan bien loi nhuan. Cot "Gia von moi dat" trong
sheet Item danh dau ro ma nao bi sua.

## Sau dia diem, deu la ma co san

Kho `W0003` Warehouse W0003 - CENTRAL, va nam cua hang `S0001` Cronus Super Market South,
`S0002` Cronus Super Market North, `S0005` Cronus Restaurant, `S0010` Cronus Coffeehouse,
`S0013` Cronus Web Store.

Assortment khac nhau that: nha hang va quan ca phe khong ban hang dong goi cua sieu thi,
web store khong ban banh tuoi. Nhieu to hop mat hang x cua hang vi vay khong co dong ban nao.
Do la du lieu dung, va no test duoc chuyen mo hinh co phan biet noi "khong ban vi khong bay"
voi "khong ban vi het hang" hay khong.

## Muoi tinh huong ghim san

1. **Su kien mot lan roi dut hang.** `33200` Chocolate ice cream tai `S0001` ban gap 2,4 lan tu
   08/08 den 24/08. Trong ba khoang 08/06-20/06, 03/07-16/07 va 12/08-02/09, kho ngung chuyen
   hang ra cua hang nay, ton tu rut ve 0 roi dong ban dung han. Tong cong 14 ngay khong ban duoc
   don vi nao vi khong con hang, khong phai vi khong co nhu cau.
   Day la diem de sai nhat cua UC1 va UC2: chia tong luong ban cho 90 ngay se ra 6,54 don vi
   mot ngay, con loai 14 ngay do ra thi la 7,75, lech 18%. Nguong bo sung tinh tren con so thap
   se lam cua hang dut hang tiep, roi vong lap sieu chat lai.
2. **Lo qua han con nam tren so.** 31 lo, 625 don vi. Nang nhat la `33323` tai `S0002`,
   lo `L260720-33323-SD`, 285 don vi, qua han 5 ngay. Ke do la `10000` Milk tai `S0001`,
   lo `L260910-10000-SD`, 98 don vi, va `33170` Chocolate cake tai `S0010`, 28 don vi.
3. **Can han ban khong kip.** 38 lo, 1.407 don vi. Ro nhat: `33310` tai `S0010`
   lo `L260829-33310-SD` 470 don vi con 25 ngay den han trong khi days of cover la 43;
   `33341` tai `S0005` 144 don vi con 30 ngay ma days of cover 61; `10045` Cream tai `S0013`
   143 don vi con 3 ngay den han, days of cover 30.
4. **Ton thua tai kho.** `30091` Flavored syrup tai `W0003`, 587 don vi, ban binh quan
   0,82 don vi mot ngay, days of cover 714.
5. **Cua hang thieu trong khi kho thua.** `33323` Choco nuts: `S0001` la cua hang lon nhat,
   ban binh quan 11,6 don vi mot ngay, nhung ton bang **0**, trong khi kho con 681 va
   `S0002` con 405. Day la tinh huong de xuat dieu chuyen chu khong phai de xuat mua.
6. **Ton chet sau khi ngung kinh doanh.** `18230` Ice cream strawberry ban den 31/05 roi dung han,
   den nay 110 ngay khong co dong ban.
7. **Hang moi ra mat giua ky.** `18120` Frozen waffles chi co lich su tu 26/07, tuc 54 ngay.
   Mo hinh du bao phai xu ly duoc truong hop khong du lich su thay vi tra ve so bua.
8. **Khuyen mai.** `33310` giam gia 25% tai `S0001` va `S0002` tu 06/07 den 19/07, san luong gap ba.
   Tong Discount Amount 922,50. Use case quan tri chiet khau co so that de chay.
9. **Huy hang dinh ky.** 1.165 lan huy hang qua han rai deu suot ky, tap trung o banh tuoi:
   33100 Croissant - plain 240 lan, 33110 Croissant - chocolate 199 lan, 33116 Blueberry muffin
   162 lan, 33170 Chocolate cake 151 lan. Day la ty le hao hut that de tinh baseline.
10. **Lo bi khoa.** `33170` Chocolate cake, lo `L260908-33170B`, Blocked bat trong
    Lot No. Information. Dung cho demo thu hoi lo va truy xuat nguon goc.

## Mot diem ve cach tinh nguong tai kho

Kho `W0003` xuat hang di cua hang bang Negative Adjmt. chu khong phai bang dong Sale. Logic nao
tinh nhu cau cua kho bang cach dem dong Sale se thay kho khong co nhu cau va xep moi lo o kho
vao nhom cham luan chuyen. Nhu cau cua kho phai tinh bang tong luong xuat di cong phan ban si.
Day la mot trong nhung cho de sai nhat khi chuyen tu bang tinh sang he thong.

## Han dung do tu du lieu

Lop tinh toan khong doc truong Expiration Calculation tren Item, ma do han dung that tu chinh
du lieu: trung vi cua (Expiration Date tru Posting Date) tren cac dong nhap. Ket qua tren bo
du lieu nay:

| Mat hang | Han dung do duoc |
|---|---|
| 33110 Croissant - chocolate | 2 ngay |
| 33170 Chocolate cake | 3 ngay |
| 33130 Tiramisu | 5 ngay |
| 10000 Milk 1 liter | 5 ngay |
| 10045 Cream 250 ml | 12 ngay |
| 33341 Choco bowl | 165 ngay |
| 33323 Choco nuts | 223 ngay |
| 33310 Choco pillar | 229 ngay |

Con so nay dung de chan muc ton muc tieu khi de xuat bo sung. De xuat bo sung du ban 14 ngay
cho mat hang han dung 2 ngay la cam ket truoc mot lan huy hang, nen muc tieu bi ha xuong
con han dung tru mot ngay.
