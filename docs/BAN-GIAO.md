# Ban giao sang Claude Code

Ngay 11/09/2026. Phien Cowork ket thuc o day, ly do chuyen: container cua Cowork khong co
AL compiler va proxy chan moi nguon lay ve (marketplace, nuget, dot.net, bcartifacts, open-vsx),
nen khong xuat duoc file `.app`. Claude Code chay tren may nen khong vuong cho do.

## Doc theo thu tu nay

1. `CLAUDE.md` - brief day du, dat o goc thu muc `AL/Marou`. Claude Code doc tu dong.
2. `demo-data-nwv/README-import.md` - cach import bo du lieu va muoi tinh huong ghim san.
3. `al/MarouDataApi/README.md` - extension lam gi, vi sao can no.
4. `lich-su-chat.md` - loi thoai cua phien Cowork, neu can tra lai boi canh mot quyet dinh.

## Trang thai tung phan

| Phan | Trang thai |
|---|---|
| Extension `MarouDataApi` (9 API page chi doc) | source xong, **chua build** |
| Bo du lieu demo 24.759 dong | xong, **chua import** |
| Lop doc BC `bc_agent/bc_data.py` | xong, 97 test pass, **chua chay tren BC that** |
| Lop tinh toan UC2 `bc_agent/inventory.py` | xong, da chay tren bo du lieu demo offline |
| Probe `bc_agent/probe.py` | xong, **chua chay tren BC that** |
| `LLM_MODE=live` | **chua chay lan nao** |
| Extension logic AL (`MarouAgentFoundation`) | chua build, da duoc thay tam bang Python |
| Phan commercial model cua de xuat | chua viet |

## Viec dau tien nen lam

```
cd "C:\Users\dungdt.NWV\OneDrive - NaviWorld\Documents\AL\Marou\al\MarouDataApi"
copy ..\..\..\Demo\.alpackages .alpackages   # hoac AL: Download Symbols trong VS Code
code .
# Ctrl+Shift+B de build, F5 de build va publish
```

Neu build loi thi day la lan build dau tien cua extension nay. 145 ten truong da doi chieu voi
source base app 28.4 nen kha nang sai ten truong la thap, loi neu co se thuoc ve cu phap page
hoac thuoc tinh API page.

## Nhung con so de doi chieu sau khi import

Chay `python tools/make_demo_data.py` roi chay lop tinh toan UC2 tren ket qua, offline, se ra:

| Phan tang | So lo |
|---|---|
| Qua han | 31 (625 don vi) |
| Can han | 38 (1.407 don vi) |
| Rui ro dut hang | 48 |
| Cham luan chuyen | 4 |
| Ton thua | 1 |
| Binh thuong | 44 |

22 de xuat dieu chuyen. 33200 tai S0001 co 14 ngay cau bi cat cut, ban binh quan dung la 7,75
don vi mot ngay so voi 6,54 neu chia deu 90 ngay.

Sau khi import vao BC va chay qua custom API, con so phai trung. Lech la co cho sai, thuong la
o cach doc Quantity co dau hoac o cach xac dinh ngay het hang.

## Thu tu uu tien neu thoi gian gap (demo tuan sau)

1. Build va publish extension. Khong co no thi khong doc duoc du lieu.
2. Import du lieu. Post bay file theo dung thu tu thang.
3. Chay probe, chup lai ket qua. Day la phan "baseline truoc, moi thu khac sau" de noi voi khach.
4. Chay UC2 tren du lieu that, doi chieu bang tren.
5. Nhung thu con lai deu co the lui: agent, LLM live, phan commercial.
