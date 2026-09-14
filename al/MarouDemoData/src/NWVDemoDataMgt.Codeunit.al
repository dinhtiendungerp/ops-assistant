/// <summary>
/// Sinh du lieu gia lap cho sandbox, post THAT qua Item Journal de ra Item Ledger Entry co Lot No.,
/// Expiration Date va lich su ban. Cung item, location, kich ban voi python/bc_agent/make_fixtures.py,
/// nen demo web va demo tren BC ke cung mot cau chuyen.
///
/// Chay mot lan. Lan hai bao loi vi da co Item Ledger Entry cua item MAR-*.
/// Khong bao gio chay tren production: extension nay chi cai len sandbox.
///
/// Thu tu: master data -> nhap kho theo lo (Positive Adjmt.) -> ban hang tung ngay (Sale) -> tuyen chuyen kho.
/// Moi ngay ban la mot lan post batch, co commit, nen chay do giua chung thi chay lai tu ngay ke tiep.
/// </summary>
codeunit 70070 "NWV Demo Data Mgt."
{
    var
        Seed: BigInteger;
        HistoryDays: Integer;
        StartDate: Date;
        TemplateName: Code[10];
        BatchName: Code[10];
        GenProdGroup: Code[20];
        InvPostingGroup: Code[20];
        ItemTrackingCodeTok: Label 'LOTEXP', Locked = true;
        BatchTok: Label 'NWVDEMO', Locked = true;
        WhTok: Label 'WH-HCM', Locked = true;
        InTransitTok: Label 'IN-TRANSIT', Locked = true;
        AlreadyRunErr: Label 'Đã có Item Ledger Entry của item MAR-*. Dữ liệu demo chỉ tạo một lần trên mỗi company.';
        NoPostingGroupErr: Label 'Company này chưa có Gen. Prod. Posting Group hoặc Inventory Posting Group nào. Tạo company từ dữ liệu mẫu, hoặc cấu hình posting group trước rồi chạy lại.';
        NoTemplateErr: Label 'Chưa có Item Journal Template loại Item. Mở Item Journals một lần để BC tự tạo, rồi chạy lại.';
        DoneMsg: Label 'Đã tạo xong: %1 item, %2 location, %3 lô nhập kho, %4 dòng bán trong %5 ngày. Giờ chạy NWV Data Readiness rồi NWV Inv. Health Calc.';
        ProgressMsg: Label 'Đang post ngày #1######## (#2#### / #3####)';

    procedure CreateAll()
    var
        Window: Dialog;
        LotCount: Integer;
        SaleLines: Integer;
        DayIdx: Integer;
        D: Date;
    begin
        GuardNotRunTwice();
        HistoryDays := 120;
        StartDate := CalcDate('<-120D>', Today());
        ResolvePostingGroups();
        ResolveJournal();
        OpenPostingPeriod();

        EnsureUnitOfMeasure('PCS', 'Cái');
        EnsureItemTrackingCode();
        EnsureReasonCode('NWV-EXP', 'Huỷ hàng hết hạn (đề xuất NWV)');
        EnsureCategories();
        EnsureLocations();
        EnsureItems();
        EnsureTransferRoutes();

        LotCount := PostReceipts();

        Window.Open(ProgressMsg);
        for DayIdx := 0 to HistoryDays - 1 do begin
            D := StartDate + DayIdx;
            Window.Update(1, D);
            Window.Update(2, DayIdx + 1);
            Window.Update(3, HistoryDays);
            SaleLines += PostSalesForDay(D);
        end;
        Window.Close();

        Message(DoneMsg, 12, 5, LotCount, SaleLines, HistoryDays);
    end;

    // ------------------------------------------------------------------ guard va setup

    local procedure GuardNotRunTwice()
    var
        ItemLedgerEntry: Record "Item Ledger Entry";
    begin
        ItemLedgerEntry.SetFilter("Item No.", 'MAR-*');
        if not ItemLedgerEntry.IsEmpty() then
            Error(AlreadyRunErr);
    end;

    local procedure ResolvePostingGroups()
    var
        GenProdPostingGroup: Record "Gen. Product Posting Group";
        InventoryPostingGroup: Record "Inventory Posting Group";
    begin
        if GenProdPostingGroup.Get('RETAIL') then
            GenProdGroup := 'RETAIL'
        else
            if GenProdPostingGroup.FindFirst() then
                GenProdGroup := GenProdPostingGroup.Code;

        if InventoryPostingGroup.Get('RESALE') then
            InvPostingGroup := 'RESALE'
        else
            if InventoryPostingGroup.FindFirst() then
                InvPostingGroup := InventoryPostingGroup.Code;

        if (GenProdGroup = '') or (InvPostingGroup = '') then
            Error(NoPostingGroupErr);

        EnsureGeneralPostingSetup();
    end;

    /// <summary>
    /// Item Journal post voi Gen. Bus. Posting Group trong, nen can dong General Posting Setup ('' , GenProdGroup).
    /// Neu chua co thi chep tu dong bat ky cua cung Gen. Prod. Posting Group.
    /// </summary>
    local procedure EnsureGeneralPostingSetup()
    var
        GeneralPostingSetup: Record "General Posting Setup";
        Source: Record "General Posting Setup";
    begin
        if GeneralPostingSetup.Get('', GenProdGroup) then
            exit;
        Source.SetRange("Gen. Prod. Posting Group", GenProdGroup);
        if not Source.FindFirst() then
            Error(NoPostingGroupErr);
        GeneralPostingSetup := Source;
        GeneralPostingSetup."Gen. Bus. Posting Group" := '';
        GeneralPostingSetup.Insert();
    end;

    local procedure EnsureInventoryPostingSetup(LocationCode: Code[10])
    var
        InventoryPostingSetup: Record "Inventory Posting Setup";
        Source: Record "Inventory Posting Setup";
    begin
        if InventoryPostingSetup.Get(LocationCode, InvPostingGroup) then
            exit;
        Source.SetRange("Invt. Posting Group Code", InvPostingGroup);
        if not Source.FindFirst() then
            Error(NoPostingGroupErr);
        InventoryPostingSetup := Source;
        InventoryPostingSetup."Location Code" := LocationCode;
        InventoryPostingSetup.Insert();
    end;

    local procedure ResolveJournal()
    var
        ItemJournalTemplate: Record "Item Journal Template";
        ItemJournalBatch: Record "Item Journal Batch";
    begin
        ItemJournalTemplate.SetRange(Type, ItemJournalTemplate.Type::Item);
        ItemJournalTemplate.SetRange(Recurring, false);
        if ItemJournalTemplate.Get('ITEM') then
            TemplateName := 'ITEM'
        else
            if ItemJournalTemplate.FindFirst() then
                TemplateName := ItemJournalTemplate.Name
            else
                Error(NoTemplateErr);

        BatchName := CopyStr(BatchTok, 1, MaxStrLen(BatchName));
        if not ItemJournalBatch.Get(TemplateName, BatchName) then begin
            ItemJournalBatch.Init();
            ItemJournalBatch."Journal Template Name" := TemplateName;
            ItemJournalBatch.Name := BatchName;
            ItemJournalBatch.Description := 'Dữ liệu demo NWV';
            ItemJournalBatch."No. Series" := '';
            ItemJournalBatch.Insert(true);
        end;
    end;

    /// <summary>
    /// Lich su ban lui 120 ngay nen ky post phai mo toi do. Chi noi rong, khong thu hep.
    /// </summary>
    local procedure OpenPostingPeriod()
    var
        GeneralLedgerSetup: Record "General Ledger Setup";
        UserSetup: Record "User Setup";
    begin
        GeneralLedgerSetup.Get();
        if (GeneralLedgerSetup."Allow Posting From" <> 0D) and (GeneralLedgerSetup."Allow Posting From" > StartDate) then
            GeneralLedgerSetup."Allow Posting From" := StartDate;
        if (GeneralLedgerSetup."Allow Posting To" <> 0D) and (GeneralLedgerSetup."Allow Posting To" < Today()) then
            GeneralLedgerSetup."Allow Posting To" := Today();
        GeneralLedgerSetup.Modify();

        if UserSetup.Get(UserId()) then begin
            if (UserSetup."Allow Posting From" <> 0D) and (UserSetup."Allow Posting From" > StartDate) then
                UserSetup."Allow Posting From" := StartDate;
            if (UserSetup."Allow Posting To" <> 0D) and (UserSetup."Allow Posting To" < Today()) then
                UserSetup."Allow Posting To" := Today();
            UserSetup.Modify();
        end;
    end;

    local procedure EnsureUnitOfMeasure(UoMCode: Code[10]; Descr: Text[50])
    var
        UnitOfMeasure: Record "Unit of Measure";
    begin
        if UnitOfMeasure.Get(UoMCode) then
            exit;
        UnitOfMeasure.Init();
        UnitOfMeasure.Code := UoMCode;
        UnitOfMeasure.Description := Descr;
        UnitOfMeasure.Insert(true);
    end;

    local procedure EnsureItemTrackingCode()
    var
        ItemTrackingCode: Record "Item Tracking Code";
    begin
        if ItemTrackingCode.Get(ItemTrackingCodeTok) then
            exit;
        ItemTrackingCode.Init();
        ItemTrackingCode.Code := ItemTrackingCodeTok;
        ItemTrackingCode.Description := 'Theo lô, có hạn dùng';
        ItemTrackingCode.Insert(true);
        ItemTrackingCode.Validate("Lot Specific Tracking", true);
        ItemTrackingCode.Validate("Use Expiration Dates", true);
        ItemTrackingCode.Validate("Man. Expir. Date Entry Reqd.", true);
        ItemTrackingCode.Modify(true);
    end;

    local procedure EnsureReasonCode(ReasonCode: Code[10]; Descr: Text[100])
    var
        Reason: Record "Reason Code";
    begin
        if Reason.Get(ReasonCode) then
            exit;
        Reason.Init();
        Reason.Code := ReasonCode;
        Reason.Description := Descr;
        Reason.Insert(true);
    end;

    local procedure EnsureCategories()
    begin
        EnsureCategory('BAR', 'Thanh chocolate');
        EnsureCategory('CONF', 'Bonbon và kẹo');
        EnsureCategory('DRINK', 'Đồ uống');
        EnsureCategory('GIFT', 'Hộp quà');
        EnsureCategory('INGR', 'Nguyên liệu');
    end;

    local procedure EnsureCategory(CategoryCode: Code[20]; Descr: Text[100])
    var
        ItemCategory: Record "Item Category";
    begin
        if ItemCategory.Get(CategoryCode) then
            exit;
        ItemCategory.Init();
        ItemCategory.Code := CategoryCode;
        ItemCategory.Description := Descr;
        ItemCategory.Insert(true);
    end;

    local procedure EnsureLocations()
    begin
        EnsureLocation(WhTok, 'Kho trung tâm HCM', false);
        EnsureLocation('S-CALMETTE', 'Cửa hàng Calmette', false);
        EnsureLocation('S-THAODIEN', 'Cửa hàng Thảo Điền', false);
        EnsureLocation('S-HANOI', 'Cửa hàng Hà Nội', false);
        EnsureLocation('S-DANANG', 'Cửa hàng Đà Nẵng', false);
        EnsureLocation(InTransitTok, 'Hàng đang đi đường', true);
    end;

    local procedure EnsureLocation(LocationCode: Code[10]; LocationName: Text[100]; InTransit: Boolean)
    var
        Location: Record Location;
    begin
        if not Location.Get(LocationCode) then begin
            Location.Init();
            Location.Code := LocationCode;
            Location.Name := LocationName;
            Location."Use As In-Transit" := InTransit;
            Location.Insert(true);
        end;
        // Ke ca in-transit: transfer shipment dua ton vao location nay nen cung can Inventory Posting Setup
        EnsureInventoryPostingSetup(LocationCode);
    end;

    // Cung danh sach voi make_fixtures.py: ma, ten, nhom, gia von, nhu cau ngay co ban, han dung (ngay)
    local procedure EnsureItems()
    begin
        EnsureItem('MAR-BT78-80', 'Ben Tre 78% 80g', 'BAR', 45000);
        EnsureItem('MAR-TG70-80', 'Tien Giang 70% 80g', 'BAR', 45000);
        EnsureItem('MAR-DL64-80', 'Dak Lak 64% 80g', 'BAR', 45000);
        EnsureItem('MAR-LD74-80', 'Lam Dong 74% 80g', 'BAR', 45000);
        EnsureItem('MAR-BR76-80', 'Ba Ria 76% 80g', 'BAR', 45000);
        EnsureItem('MAR-DN72-80', 'Dong Nai 72% 80g', 'BAR', 45000);
        EnsureItem('MAR-MINI-24', 'Mini bar 24g', 'BAR', 18000);
        EnsureItem('MAR-BONBON-9', 'Bonbon box 9pcs', 'CONF', 120000);
        EnsureItem('MAR-BONBON-16', 'Bonbon box 16pcs', 'CONF', 210000);
        EnsureItem('MAR-HOTCHOC-250', 'Hot chocolate 250g', 'DRINK', 95000);
        EnsureItem('MAR-GIFT-TET', 'Gift box Tet 2026', 'GIFT', 380000);
        EnsureItem('MAR-COCOANIB-100', 'Cocoa nibs 100g', 'INGR', 60000);
    end;

    local procedure EnsureItem(ItemNo: Code[20]; Descr: Text[100]; CategoryCode: Code[20]; UnitCost: Decimal)
    var
        Item: Record Item;
        ItemUnitOfMeasure: Record "Item Unit of Measure";
    begin
        if Item.Get(ItemNo) then
            exit;
        Item.Init();
        Item."No." := ItemNo;
        Item.Description := Descr;
        Item.Insert(false);

        ItemUnitOfMeasure.Init();
        ItemUnitOfMeasure."Item No." := ItemNo;
        ItemUnitOfMeasure.Code := 'PCS';
        ItemUnitOfMeasure."Qty. per Unit of Measure" := 1;
        ItemUnitOfMeasure.Insert(true);

        Item.Validate("Base Unit of Measure", 'PCS');
        Item.Validate(Type, Item.Type::Inventory);
        Item.Validate("Item Category Code", CategoryCode);
        Item.Validate("Gen. Prod. Posting Group", GenProdGroup);
        Item.Validate("Inventory Posting Group", InvPostingGroup);
        Item.Validate("Costing Method", Item."Costing Method"::FIFO);
        Item.Validate("Unit Cost", UnitCost);
        Item.Validate("Unit Price", Round(UnitCost * 1.8, 1000));
        Item.Validate("Item Tracking Code", ItemTrackingCodeTok);
        Item.Modify(true);
    end;

    /// <summary>
    /// Tuyen chuyen kho tu kho trung tam toi tung cua hang. Khong co route thi Transfer Order khong tao duoc,
    /// va DR-32 trong Data Readiness bao Chan.
    /// </summary>
    local procedure EnsureTransferRoutes()
    begin
        EnsureRoute(WhTok, 'S-CALMETTE');
        EnsureRoute(WhTok, 'S-THAODIEN');
        EnsureRoute(WhTok, 'S-HANOI');
        EnsureRoute(WhTok, 'S-DANANG');
    end;

    local procedure EnsureRoute(FromLoc: Code[10]; ToLoc: Code[10])
    var
        TransferRoute: Record "Transfer Route";
    begin
        if TransferRoute.Get(FromLoc, ToLoc) then
            exit;
        TransferRoute.Init();
        TransferRoute."Transfer-from Code" := FromLoc;
        TransferRoute."Transfer-to Code" := ToLoc;
        TransferRoute.Validate("In-Transit Code", InTransitTok);
        TransferRoute.Insert(true);
    end;

    // ------------------------------------------------------------------ nhap kho theo lo

    /// <summary>
    /// Moi cap item x location mot lo nhap tai dau ky, so luong = tong se ban trong 120 ngay + ton muc tieu cuoi ky,
    /// de sau khi ban het lich su thi ton con lai dung bang kich ban. Vai cap co lo thu hai co chu y.
    /// Han dung dat theo kich ban, khong theo cong thuc, vi day la dieu demo can cho thay.
    /// </summary>
    local procedure PostReceipts(): Integer
    var
        ItemNo: Code[20];
        Loc: Code[10];
        i: Integer;
        j: Integer;
        Count: Integer;
        Target: Decimal;
        TotalSales: Decimal;
        ExpDate: Date;
        RecvDate: Date;
        LotNo: Code[50];
    begin
        for i := 1 to 12 do
            for j := 1 to 5 do begin
                ItemNo := ItemCode(i);
                Loc := LocationCode(j);
                Target := TargetOnHand(i, j);
                TotalSales := SimulatedTotalSales(i, j);
                RecvDate := StartDate - 1;
                ExpDate := RecvDate + ShelfLifeDays(i);
                LotNo := 'L' + Format(RecvDate, 0, '<Year,2><Month,2><Day,2>') + '0';
                if (Target + TotalSales) > 0 then begin
                    PostOneReceipt(ItemNo, Loc, LotNo, Target + TotalSales, ExpDate, RecvDate);
                    Count += 1;
                end;
                Count += PostScenarioLots(i, j);
            end;
        exit(Count);
    end;

    /// <summary>
    /// Lo thu hai cho cac tinh huong: het han, can date, ton dong lau ngay. Nhap cach day 60 ngay, khong bi ban toi.
    /// </summary>
    local procedure PostScenarioLots(i: Integer; j: Integer): Integer
    var
        RecvDate: Date;
        LotNo: Code[50];
    begin
        RecvDate := CalcDate('<-60D>', Today());
        LotNo := 'L' + Format(RecvDate, 0, '<Year,2><Month,2><Day,2>') + '1';
        // Bonbon 9 tai Da Nang: lo da het han 3 ngay, 27 hop, gia tri 3.240.000
        if (ItemCode(i) = 'MAR-BONBON-9') and (LocationCode(j) = 'S-DANANG') then begin
            PostOneReceipt(ItemCode(i), LocationCode(j), LotNo, 27, Today() - 3, RecvDate);
            exit(1);
        end;
        // Bonbon 16 tai Ha Noi: con 12 ngay den han, 40 hop, ban khong kip
        if (ItemCode(i) = 'MAR-BONBON-16') and (LocationCode(j) = 'S-HANOI') then begin
            PostOneReceipt(ItemCode(i), LocationCode(j), LotNo, 40, Today() + 12, RecvDate);
            exit(1);
        end;
        // Cocoa nibs tai kho: lo L2605190, 900 goi, du ton, nhap 19/05/2026 han 15/03/2027 (kich ban KB-2)
        if (ItemCode(i) = 'MAR-COCOANIB-100') and (LocationCode(j) = WhTok) then begin
            RecvDate := DMY2Date(19, 5, 2026);
            if RecvDate < StartDate then
                RecvDate := StartDate;
            PostOneReceipt(ItemCode(i), LocationCode(j), 'L2605190', 900, DMY2Date(15, 3, 2027), RecvDate);
            exit(1);
        end;
        exit(0);
    end;

    local procedure PostOneReceipt(ItemNo: Code[20]; Loc: Code[10]; LotNo: Code[50]; Qty: Decimal; ExpDate: Date; PostingDate: Date)
    var
        ItemJournalLine: Record "Item Journal Line";
    begin
        ClearBatch();
        InsertLine(ItemJournalLine, PostingDate, ItemJournalLine."Entry Type"::"Positive Adjmt.", ItemNo, Loc, Qty, 'DEMO-RCPT');
        AddLotTracking(ItemJournalLine, LotNo, ExpDate, Qty);
        PostBatch();
    end;

    // ------------------------------------------------------------------ ban hang tung ngay

    local procedure PostSalesForDay(D: Date): Integer
    var
        ItemJournalLine: Record "Item Journal Line";
        i: Integer;
        j: Integer;
        Qty: Decimal;
        Lines: Integer;
        LotNo: Code[50];
        ExpDate: Date;
    begin
        ClearBatch();
        LotNo := 'L' + Format(StartDate - 1, 0, '<Year,2><Month,2><Day,2>') + '0';
        for i := 1 to 12 do
            for j := 1 to 5 do begin
                Qty := DailySaleQty(i, j, D);
                if Qty > 0 then begin
                    ExpDate := (StartDate - 1) + ShelfLifeDays(i);
                    InsertLine(ItemJournalLine, D, ItemJournalLine."Entry Type"::Sale, ItemCode(i), LocationCode(j), Qty,
                        'DEMO-' + Format(D, 0, '<Year4><Month,2><Day,2>'));
                    AddLotTracking(ItemJournalLine, LotNo, ExpDate, Qty);
                    Lines += 1;
                end;
            end;
        if Lines > 0 then
            PostBatch();
        exit(Lines);
    end;

    /// <summary>
    /// Nhu cau ngay theo dung cong thuc cua make_fixtures.py: muc co ban x he so cua hang x cuoi tuan,
    /// cong cac tinh huong: hoi cho Da Nang (x2.4) roi dut hang 9 ngay, vai dot dut hang som,
    /// hop qua Tet khong ban sau thang 2, cocoa nibs chi ban 75 ngay gan day, kho trung tam xuat si vai ngay trong tuan.
    /// Sinh so bang LCG co seed nen chay lai ra dung bo so.
    /// </summary>
    local procedure DailySaleQty(i: Integer; j: Integer; D: Date): Decimal
    var
        Lam: Decimal;
        WeekDay: Integer;
        k: Integer;
        Q: Integer;
        Trials: Integer;
    begin
        Seed := (7919 * i + 104729 * j + (D - StartDate) * 31 + 20260907) mod 2147483648L;
        WeekDay := Date2DWY(D, 1); // 1 = thu hai ... 7 = chu nhat
        if LocationCode(j) = WhTok then begin
            // Kho trung tam: xuat si ngay trong tuan voi xac suat 40%, tru hop Tet va cocoa nibs
            if (i = 11) or (i = 12) or (WeekDay > 5) then
                exit(0);
            if NextRandom() < 0.4 then
                exit(Round(BaseDemand(i) * 6, 1));
            exit(0);
        end;

        Lam := BaseDemand(i) * StoreFactor(j);
        if WeekDay >= 6 then
            Lam := Lam * 1.35;

        if (ItemCode(i) = 'MAR-BR76-80') and (LocationCode(j) = 'S-DANANG') then begin
            if (D >= Today() - 30) and (D <= Today() - 14) then
                Lam := Lam * 2.4                       // hoi cho truoc cua hang
            else
                if (D >= Today() - 13) and (D <= Today() - 5) then
                    Lam := 0                            // dut hang sau su kien, cau bi cat cut chu khong phai bang 0
                else
                    if ((D >= Today() - 81) and (D <= Today() - 79)) or ((D >= Today() - 56) and (D <= Today() - 53)) then
                        Lam := 0;                       // dut hang som
        end;
        if (i = 11) and (Date2DMY(D, 2) > 2) then
            Lam := 0;                                   // hop qua Tet
        if (i = 12) and (D < Today() - 75) then
            Lam := 0;                                   // cocoa nibs moi ban gan day

        Trials := Round(Lam * 3, 1, '<');
        for k := 1 to Trials do
            if NextRandom() < 1 / 3 then
                Q += 1;
        exit(Q);
    end;

    /// <summary>
    /// Tong se ban trong ky. Vi DailySaleQty tu dat seed theo cap va ngay, cong lai la ra dung con so se post.
    /// Nho vay so nhap dau ky luon du cho so ban, ton cuoi ky dung bang muc tieu.
    /// </summary>
    local procedure SimulatedTotalSales(i: Integer; j: Integer): Decimal
    var
        DayIdx: Integer;
        Total: Decimal;
    begin
        for DayIdx := 0 to HistoryDays - 1 do
            Total += DailySaleQty(i, j, StartDate + DayIdx);
        exit(Total);
    end;

    /// <summary>
    /// LCG co seed. Seed duoc dat lai o dau moi DailySaleQty theo cap va ngay, nen thu tu goi khong anh huong ket qua.
    /// </summary>
    local procedure NextRandom(): Decimal
    begin
        // LCG 32-bit cua Numerical Recipes, du cho demo
        Seed := (Seed * 1103515245 + 12345) mod 2147483648L;
        if Seed < 0 then
            Seed := -Seed;
        exit(Seed / 2147483648.0);
    end;

    // ------------------------------------------------------------------ journal

    local procedure ClearBatch()
    var
        ItemJournalLine: Record "Item Journal Line";
        ReservationEntry: Record "Reservation Entry";
    begin
        ItemJournalLine.SetRange("Journal Template Name", TemplateName);
        ItemJournalLine.SetRange("Journal Batch Name", BatchName);
        ItemJournalLine.DeleteAll(true);
        ReservationEntry.SetRange("Source Type", Database::"Item Journal Line");
        ReservationEntry.SetRange("Source ID", TemplateName);
        ReservationEntry.SetRange("Source Batch Name", BatchName);
        ReservationEntry.DeleteAll();
    end;

    local procedure InsertLine(var ItemJournalLine: Record "Item Journal Line"; PostingDate: Date; EntryType: Enum "Item Ledger Entry Type"; ItemNo: Code[20]; Loc: Code[10]; Qty: Decimal; DocNo: Code[20])
    var
        LastLine: Record "Item Journal Line";
        LineNo: Integer;
    begin
        LastLine.SetRange("Journal Template Name", TemplateName);
        LastLine.SetRange("Journal Batch Name", BatchName);
        if LastLine.FindLast() then
            LineNo := LastLine."Line No." + 10000
        else
            LineNo := 10000;

        ItemJournalLine.Init();
        ItemJournalLine."Journal Template Name" := TemplateName;
        ItemJournalLine."Journal Batch Name" := BatchName;
        ItemJournalLine."Line No." := LineNo;
        ItemJournalLine.Insert(true);
        ItemJournalLine.Validate("Posting Date", PostingDate);
        ItemJournalLine.Validate("Entry Type", EntryType);
        ItemJournalLine.Validate("Document No.", DocNo);
        ItemJournalLine.Validate("Item No.", ItemNo);
        ItemJournalLine.Validate("Location Code", Loc);
        ItemJournalLine.Validate(Quantity, Qty);
        ItemJournalLine.Modify(true);
    end;

    /// <summary>
    /// Gan lo va han dung cho dong journal qua Reservation Entry trang thai Prospect, dung cach BC chuan lam.
    /// Dau cua so luong lay tu Signed() cua dong journal: nhap duong, ban am.
    /// </summary>
    local procedure AddLotTracking(ItemJournalLine: Record "Item Journal Line"; LotNo: Code[50]; ExpDate: Date; Qty: Decimal)
    var
        TempReservationEntry: Record "Reservation Entry" temporary;
        CreateReservEntry: Codeunit "Create Reserv. Entry";
        SignedQty: Decimal;
    begin
        SignedQty := ItemJournalLine.Signed(Qty);
        TempReservationEntry.Init();
        TempReservationEntry."Lot No." := LotNo;
        CreateReservEntry.SetDates(0D, ExpDate);
        CreateReservEntry.CreateReservEntryFor(
            Database::"Item Journal Line", ItemJournalLine."Entry Type".AsInteger(),
            ItemJournalLine."Journal Template Name", ItemJournalLine."Journal Batch Name", 0, ItemJournalLine."Line No.",
            ItemJournalLine."Qty. per Unit of Measure", SignedQty, SignedQty * ItemJournalLine."Qty. per Unit of Measure",
            TempReservationEntry);
        CreateReservEntry.CreateEntry(
            ItemJournalLine."Item No.", ItemJournalLine."Variant Code", ItemJournalLine."Location Code",
            ItemJournalLine.Description, 0D, 0D, 0, Enum::"Reservation Status"::Prospect);
    end;

    local procedure PostBatch()
    var
        ItemJournalLine: Record "Item Journal Line";
        ItemJnlPostBatch: Codeunit "Item Jnl.-Post Batch";
    begin
        ItemJournalLine.SetRange("Journal Template Name", TemplateName);
        ItemJournalLine.SetRange("Journal Batch Name", BatchName);
        if ItemJournalLine.IsEmpty() then
            exit;
        ItemJournalLine.FindFirst();
        ItemJnlPostBatch.Run(ItemJournalLine);
    end;

    // ------------------------------------------------------------------ bang tra cuu, cung so voi make_fixtures.py

    local procedure ItemCode(i: Integer): Code[20]
    begin
        case i of
            1: exit('MAR-BT78-80');
            2: exit('MAR-TG70-80');
            3: exit('MAR-DL64-80');
            4: exit('MAR-LD74-80');
            5: exit('MAR-BR76-80');
            6: exit('MAR-DN72-80');
            7: exit('MAR-MINI-24');
            8: exit('MAR-BONBON-9');
            9: exit('MAR-BONBON-16');
            10: exit('MAR-HOTCHOC-250');
            11: exit('MAR-GIFT-TET');
            12: exit('MAR-COCOANIB-100');
        end;
    end;

    local procedure BaseDemand(i: Integer): Decimal
    begin
        case i of
            1: exit(6.0);
            2: exit(5.0);
            3: exit(4.5);
            4: exit(3.5);
            5: exit(2.5);
            6: exit(2.0);
            7: exit(12.0);
            8: exit(1.5);
            9: exit(0.8);
            10: exit(1.2);
            11: exit(0.05);
            12: exit(0.3);
        end;
    end;

    local procedure ShelfLifeDays(i: Integer): Integer
    begin
        case i of
            7: exit(300);
            8, 9: exit(90);
            10: exit(240);
            11: exit(400);
            12: exit(300);
            else
                exit(365);
        end;
    end;

    local procedure LocationCode(j: Integer): Code[10]
    begin
        case j of
            1: exit(WhTok);
            2: exit('S-CALMETTE');
            3: exit('S-THAODIEN');
            4: exit('S-HANOI');
            5: exit('S-DANANG');
        end;
    end;

    local procedure StoreFactor(j: Integer): Decimal
    begin
        case j of
            2: exit(1.3);
            3: exit(1.0);
            4: exit(0.9);
            5: exit(0.6);
            else
                exit(1.0);
        end;
    end;

    /// <summary>
    /// Ton cuoi ky theo kich ban. Cac cap khong co chu y: khoang 15 ngay ban tai cua hang, 20 ngay tai kho.
    /// </summary>
    local procedure TargetOnHand(i: Integer; j: Integer): Decimal
    begin
        if (ItemCode(i) = 'MAR-BR76-80') and (LocationCode(j) = 'S-DANANG') then
            exit(3);                                   // stock-out risk
        if (ItemCode(i) = 'MAR-MINI-24') and (LocationCode(j) = 'S-CALMETTE') then
            exit(12);                                  // stock-out risk cua hang lon
        if (ItemCode(i) = 'MAR-MINI-24') and (LocationCode(j) = WhTok) then
            exit(488);
        if (ItemCode(i) = 'MAR-MINI-24') and (LocationCode(j) = 'S-THAODIEN') then
            exit(313);
        if ItemCode(i) = 'MAR-GIFT-TET' then
            exit(40);                                  // slow-moving o moi noi
        if (ItemCode(i) = 'MAR-COCOANIB-100') and (LocationCode(j) = WhTok) then
            exit(0);                                   // ton nam o lo L2605190 rieng
        if LocationCode(j) = WhTok then
            exit(Round(BaseDemand(i) * 4 * 20, 1));
        exit(Round(BaseDemand(i) * StoreFactor(j) * 15, 1));
    end;
}
