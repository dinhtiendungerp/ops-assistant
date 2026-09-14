/// <summary>
/// Mot trang duy nhat cho toan bo viec nap du lieu demo. Tell me, go "NWV Marou Demo Setup".
/// Thu tu chay: Chuan bi, import Config Package, Post theo thang, Khoa lo demo.
/// </summary>
page 70250 "NWV Marou Demo Setup"
{
    PageType = Card;
    ApplicationArea = All;
    UsageCategory = Administration;
    Caption = 'NWV Marou Demo Setup';
    InsertAllowed = false;
    DeleteAllowed = false;
    ModifyAllowed = false;
    Editable = false;

    layout
    {
        area(Content)
        {
            group(TrangThai)
            {
                Caption = 'Trang thai';

                field(BatchSanSang; BatchSanSang)
                {
                    ApplicationArea = All;
                    Caption = 'Batch NWVDEMO da co';
                    ToolTip = 'Cho biet Item Journal Template ITEM va batch NWVDEMO da ton tai chua.';
                }
                field(SoDongChuaPost; SoDongChuaPost)
                {
                    ApplicationArea = All;
                    Caption = 'So dong chua post trong batch';
                    ToolTip = 'So dong Item Journal con lai trong batch NWVDEMO.';
                }
                field(SoItemLedgerEntry; SoItemLedgerEntry)
                {
                    ApplicationArea = All;
                    Caption = 'So Item Ledger Entry';
                    ToolTip = 'Tong so dong Item Ledger Entry trong company.';
                }
                field(SoLotInfo; SoLotInfo)
                {
                    ApplicationArea = All;
                    Caption = 'So Lot No. Information';
                    ToolTip = 'So ban ghi Lot No. Information, do viec post tu sinh ra.';
                }
                field(LoDemoDaKhoa; LoDemoDaKhoa)
                {
                    ApplicationArea = All;
                    Caption = 'Lo demo da khoa';
                    ToolTip = 'Cho biet lo dung cho kich ban thu hoi da bat Blocked chua.';
                }
            }
            group(KhoangNgay)
            {
                Caption = 'Khoang ngay cua du lieu';

                field(TuNgay; TuNgay)
                {
                    ApplicationArea = All;
                    Caption = 'Tu ngay';
                    ToolTip = 'Dau khoang ngay se duoc mo trong Allow Posting From.';
                }
                field(DenNgay; DenNgay)
                {
                    ApplicationArea = All;
                    Caption = 'Den ngay';
                    ToolTip = 'Cuoi khoang ngay se duoc mo trong Allow Posting To.';
                }
            }
        }
    }

    actions
    {
        area(Processing)
        {
            action(ChuanBi)
            {
                ApplicationArea = All;
                Caption = '1. Chuan bi truoc khi import';
                ToolTip = 'Tao Item Journal Template ITEM va batch NWVDEMO, noi rong Allow Posting From/To cho phu khoang ngay cua du lieu.';
                Image = Setup;
                Promoted = true;
                PromotedCategory = Process;
                PromotedIsBig = true;

                trigger OnAction()
                begin
                    DemoSetup.PrepareForImport();
                    LoadStatus();
                end;
            }
            action(PostTheoThang)
            {
                ApplicationArea = All;
                Caption = '2. Post batch theo tung thang';
                ToolTip = 'Post batch NWVDEMO, moi thang mot dot, theo dung thu tu thoi gian.';
                Image = PostBatch;
                Promoted = true;
                PromotedCategory = Process;
                PromotedIsBig = true;

                trigger OnAction()
                begin
                    DemoSetup.PostAllByMonth();
                    LoadStatus();
                end;
            }
            action(KhoaLoDemo)
            {
                ApplicationArea = All;
                Caption = '3. Khoa lo cho kich ban thu hoi';
                ToolTip = 'Bat Blocked tren lo dung cho kich ban thu hoi. Chi chay duoc sau khi post xong.';
                Image = Lock;
                Promoted = true;
                PromotedCategory = Process;

                trigger OnAction()
                begin
                    DemoSetup.BlockDemoLot();
                    LoadStatus();
                end;
            }
            action(XoaDongChuaPost)
            {
                ApplicationArea = All;
                Caption = 'Xoa dong chua post';
                ToolTip = 'Xoa toan bo dong con lai trong batch NWVDEMO, dung khi can import lai tu dau.';
                Image = Delete;

                trigger OnAction()
                begin
                    DemoSetup.DeleteBatchLines();
                    LoadStatus();
                end;
            }
            action(LamMoi)
            {
                ApplicationArea = All;
                Caption = 'Lam moi';
                ToolTip = 'Doc lai cac con so tren trang.';
                Image = Refresh;

                trigger OnAction()
                begin
                    LoadStatus();
                end;
            }
        }
    }

    var
        DemoSetup: Codeunit "NWV Demo Setup Mgt";
        BatchSanSang: Boolean;
        LoDemoDaKhoa: Boolean;
        SoDongChuaPost: Integer;
        SoItemLedgerEntry: Integer;
        SoLotInfo: Integer;
        TuNgay: Date;
        DenNgay: Date;

    trigger OnOpenPage()
    begin
        LoadStatus();
    end;

    local procedure LoadStatus()
    begin
        BatchSanSang := DemoSetup.BatchExists();
        SoDongChuaPost := DemoSetup.UnpostedLineCount();
        SoItemLedgerEntry := DemoSetup.ItemLedgerEntryCount();
        SoLotInfo := DemoSetup.LotInfoCount();
        LoDemoDaKhoa := DemoSetup.BlockedLotIsBlocked();
        DemoSetup.DataDateRange(TuNgay, DenNgay);
    end;
}
