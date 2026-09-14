# NWV Marou Demo Setup

Extension mot trang, gom cac thao tac quanh viec nap bo du lieu demo cho POC. Chi dung tren
sandbox. Doc lap, khong phu thuoc extension nao khac, khong phu thuoc LS Central.

Mo bang Tell me, go `NWV Marou Demo Setup`.

## Vi sao co no

Bo du lieu demo di vao BC bang Config Package. Quanh viec do con bon thao tac khong nam trong
package, truoc day phai bam tay tren nhieu trang khac nhau. Dua het vao mot trang thi khong
quen buoc nao, va lam lai lan sau khong phai nho.

## Bon nut

| Nut | Lam gi |
|---|---|
| 1. Chuan bi truoc khi import | Tao Item Journal Template `ITEM` va batch `NWVDEMO` neu chua co. Noi rong Allow Posting From/To tren General Ledger Setup va User Setup cua nguoi dang dang nhap cho phu khoang ngay cua du lieu. |
| 2. Post batch theo tung thang | Post `NWVDEMO`, moi thang mot dot, theo dung thu tu thoi gian. |
| 3. Khoa lo cho kich ban thu hoi | Bat Blocked tren lo `L260908-33170B` cua item `33170`. |
| Xoa dong chua post | Xoa het dong con lai trong batch, dung khi can import lai tu dau. |

Trang con hien so dong chua post, so Item Ledger Entry, so Lot No. Information va tinh trang
cua lo demo, de biet dang o buoc nao.

## Ba dieu rang buoc thu tu, deu doc duoc trong source base app

**Noi rong ngay post chi noi rong.** Neu Allow Posting From dang chan sau ngay dau tien cua du
lieu thi keo lui, con dang de trong thi de nguyen. Khong bao gio thu hep khoang dang mo.

**Post theo thang chu khong mot lan.** 24.759 dong trong mot giao dich la qua lon.
`ItemJnlPostBatch.Codeunit.al` giu nguyen bo loc cua record truyen vao, chi dat lai hai bo loc
Journal Template Name va Journal Batch Name, nen bo loc Posting Date song sot. `HandleNonRecurringLine`
xoa dong da post bang `ItemJnlLine3.Copy(ItemJnlLine)` roi `DeleteAll()`, ma `Copy` mang theo
bo loc, nen chi xoa dong trong dot vua post. Cat theo thang vi vay an toan.

**Khoa lo phai lam sau khi post.** `CheckLotNoInfoNotBlocked` trong `ItemJnlPostLine.Codeunit.al`
goi `LotNoInfo.TestField(Blocked, false)` cho moi dong co lo. Khoa truoc thi khong post duoc dong
nao cua lo do. Ban ghi Lot No. Information cung do chinh viec post sinh ra, voi dieu kien Item
Tracking Code bat co `Create Lot No. Info. on posting`, xem `ItemJnlPostBatch` va sheet 6502 trong
Config Package.

## Post chay nen

Codeunit `NWV Demo Post Job` (70251) chay dung viec cua nut so 2 nhung khong co giao dien. Dat
no lam Object ID to Run cua mot Job Queue Entry neu khong muon ngoi doi trong trinh duyet.

## Permission set

`NWV Marou Demo Setup` (70252), co quyen ghi. Danh cho nguoi nap du lieu, **khong gan cho Entra
app dung S2S**. App do chi can `NWV MAROU DATA API` va `NWVMAROULSC`, ca hai deu chi doc.

## Build

```
dotnet alc.dll /project:al/MarouDemoSetup /packagecachepath:.alpackages /outfolder:al/MarouDemoSetup/out
```

Duong dan day du cua `dotnet` va `alc.dll` xem muc Cach chay trong `CLAUDE.md`.
