/// <summary>
/// Tinh nhu cau binh quan ngay theo Item x Location, dung chung cho Inventory Health va
/// Replenishment. Cong thuc chep nguyen tu python/bc_agent/inventory.py, ham demand_profiles
/// va observed_shelf_life. Hai ben phai ra cung con so; lech la mot trong hai sai.
///
/// Ba diem ma ban AL truoc lam sai va o day sua lai:
///
/// 1. Cau bi cat cut. Ngay het hang khong phai ngay cau bang 0. Chia tong luong ban cho toan
///    bo so ngay trong cua so thi cang dut hang cang thay nhu cau thap, nguong bo sung cang
///    tut, roi lai cang dut hang. O day ngay ton bang 0 ma khong ban duoc gi bi loai khoi mau so.
///
/// 2. Nhu cau tai kho. Kho xuat hang di cua hang bang Negative Adjmt. hoac Transfer chu khong
///    bang dong Sale. Dem dong Sale se thay kho khong co nhu cau va xep moi lo o kho vao cham
///    luan chuyen. O day: kho (theo codeunit NWV Location Role: LSC Replen. Setup va co
///    "LSC Location is a Warehouse") luon lay tong luong xuat, ke ca khi kho co ban si tai cho;
///    cac dia diem khac khong he co dong Sale thi cung lay tong luong xuat. Chot ngay 12/09/2026,
///    doi nguon kho tu Setup sang LS ngay 15/09/2026.
///
/// 3. Han dung do tu du lieu: trung vi cua (Expiration Date - Posting Date) tren dong nhap.
///    Dung de chan muc ton muc tieu khi bo sung. Khong doc Expiration Calculation tren Item.
///
/// Mot luot doc Item Ledger Entry cho ca company, gom theo ngay vao bang tam, roi tinh.
/// </summary>
codeunit 70110 "NWV Demand Calc"
{
    var
        MoveBuf: Record "NWV Daily Move Buffer" temporary;
        ProfileBuf: Record "NWV Demand Profile Buffer" temporary;
        ShelfBuf: Record "NWV Shelf Life Buffer" temporary;
        ShelfDays: Dictionary of [Code[20], Integer];
        AsOfDate: Date;
        SinceDate: Date;
        LocationRole: Codeunit "NWV Location Role";
        IsBuilt: Boolean;
        NotBuiltErr: Label 'NWV Demand Calc chua duoc Build.';

    /// <summary>
    /// AsOf la ngay neo, HistoryDays la do dai cua so. Cua so gom HistoryDays ngay ket thuc
    /// tai AsOf, tuc tu AsOf - (HistoryDays - 1) den AsOf. Kho (theo NWV Location Role) luon
    /// lay nhu cau bang tong luong xuat.
    /// </summary>
    procedure Build(AsOf: Date; HistoryDays: Integer)
    var
        ItemLedgerEntry: Record "Item Ledger Entry";
    begin
        Clear(LocationRole);
        MoveBuf.Reset();
        MoveBuf.DeleteAll();
        ProfileBuf.Reset();
        ProfileBuf.DeleteAll();
        ShelfBuf.Reset();
        ShelfBuf.DeleteAll();
        Clear(ShelfDays);
        AsOfDate := AsOf;
        SinceDate := AsOf - (HistoryDays - 1);

        ItemLedgerEntry.SetLoadFields("Entry No.", "Item No.", "Location Code", "Posting Date",
                                      "Entry Type", Quantity, "Expiration Date");
        if ItemLedgerEntry.FindSet() then
            repeat
                AddMove(ItemLedgerEntry);
                if (ItemLedgerEntry.Quantity > 0) and (ItemLedgerEntry."Expiration Date" <> 0D) then
                    AddShelfSpan(ItemLedgerEntry."Item No.", ItemLedgerEntry."Entry No.",
                                 ItemLedgerEntry."Expiration Date" - ItemLedgerEntry."Posting Date");
            until ItemLedgerEntry.Next() = 0;

        ComputeProfiles();
        ComputeShelfLife();
        IsBuilt := true;
    end;

    procedure AsOf(): Date
    begin
        exit(AsOfDate);
    end;

    /// <summary>Tra ve false neu cap Item x Location khong co dong Item Ledger Entry nao.</summary>
    procedure GetProfile(ItemNo: Code[20]; LocationCode: Code[10]; var Profile: Record "NWV Demand Profile Buffer" temporary): Boolean
    begin
        if not IsBuilt then
            Error(NotBuiltErr);
        if not ProfileBuf.Get(ItemNo, LocationCode) then
            exit(false);
        Profile := ProfileBuf;
        exit(true);
    end;

    /// <summary>Chep toan bo profile sang bang tam cua ben goi, de duyet qua tung cap.</summary>
    procedure CopyProfiles(var Dest: Record "NWV Demand Profile Buffer" temporary)
    begin
        if not IsBuilt then
            Error(NotBuiltErr);
        Dest.Reset();
        Dest.DeleteAll();
        ProfileBuf.Reset();
        if ProfileBuf.FindSet() then
            repeat
                Dest := ProfileBuf;
                Dest.Insert();
            until ProfileBuf.Next() = 0;
    end;

    /// <summary>
    /// Nhu cau cua mot ngay theo dung co so cua cap do (Sale hoac tong luong xuat), va luong bien dong ton co dau.
    /// Dung cho NWV Forecast Accuracy Calc de dung chuoi ngay ma khong doc lai Item Ledger Entry.
    /// </summary>
    procedure GetDay(ItemNo: Code[20]; LocationCode: Code[10]; D: Date; var DemandQty: Decimal; var MoveQty: Decimal)
    begin
        if not IsBuilt then
            Error(NotBuiltErr);
        DemandQty := 0;
        MoveQty := 0;
        if not ProfileBuf.Get(ItemNo, LocationCode) then
            exit;
        if MoveBuf.Get(ItemNo, LocationCode, D) then begin
            if UseSale(ProfileBuf) then
                DemandQty := MoveBuf."Sale Qty"
            else
                DemandQty := MoveBuf."Out Qty";
            MoveQty := MoveBuf."Move Qty";
        end;
    end;

    /// <summary>Ton cua cap truoc ngay D: tong Quantity co dau cua moi dong co Posting Date nho hon D.</summary>
    procedure BalanceBefore(ItemNo: Code[20]; LocationCode: Code[10]; D: Date) Balance: Decimal
    var
        Move: Record "NWV Daily Move Buffer" temporary;
    begin
        if not IsBuilt then
            Error(NotBuiltErr);
        Move.Copy(MoveBuf, true);
        Move.Reset();
        Move.SetRange("Item No.", ItemNo);
        Move.SetRange("Location Code", LocationCode);
        Move.SetFilter("Posting Date", '<%1', D);
        if Move.FindSet() then
            repeat
                Balance += Move."Move Qty";
            until Move.Next() = 0;
    end;

    /// <summary>Han dung thuc te cua mat hang, so ngay. 0 nghia la khong do duoc.</summary>
    procedure ShelfLifeDays(ItemNo: Code[20]): Integer
    var
        Days: Integer;
    begin
        if ShelfDays.Get(ItemNo, Days) then
            exit(Days);
        exit(0);
    end;

    // ------------------------------------------------------------------ gom theo ngay
    local procedure AddMove(ItemLedgerEntry: Record "Item Ledger Entry")
    var
        IsSale: Boolean;
        IsOutbound: Boolean;
    begin
        IsSale := ItemLedgerEntry."Entry Type" = ItemLedgerEntry."Entry Type"::Sale;
        IsOutbound := ItemLedgerEntry."Entry Type" in
            [ItemLedgerEntry."Entry Type"::Sale,
             ItemLedgerEntry."Entry Type"::"Negative Adjmt.",
             ItemLedgerEntry."Entry Type"::Transfer,
             ItemLedgerEntry."Entry Type"::Consumption,
             ItemLedgerEntry."Entry Type"::Output];

        if not ProfileBuf.Get(ItemLedgerEntry."Item No.", ItemLedgerEntry."Location Code") then begin
            ProfileBuf.Init();
            ProfileBuf."Item No." := ItemLedgerEntry."Item No.";
            ProfileBuf."Location Code" := ItemLedgerEntry."Location Code";
            ProfileBuf.Insert();
        end;
        if IsSale then begin
            ProfileBuf."Has Sale" := true;
            if (ItemLedgerEntry.Quantity < 0) and (ItemLedgerEntry."Posting Date" > ProfileBuf."Last Sale Date") then
                ProfileBuf."Last Sale Date" := ItemLedgerEntry."Posting Date";
            ProfileBuf.Modify();
        end;

        if not MoveBuf.Get(ItemLedgerEntry."Item No.", ItemLedgerEntry."Location Code", ItemLedgerEntry."Posting Date") then begin
            MoveBuf.Init();
            MoveBuf."Item No." := ItemLedgerEntry."Item No.";
            MoveBuf."Location Code" := ItemLedgerEntry."Location Code";
            MoveBuf."Posting Date" := ItemLedgerEntry."Posting Date";
            MoveBuf.Insert();
        end;
        MoveBuf."Move Qty" += ItemLedgerEntry.Quantity;
        if IsSale and (ItemLedgerEntry.Quantity < 0) then
            MoveBuf."Sale Qty" += -ItemLedgerEntry.Quantity;
        if IsOutbound and (ItemLedgerEntry.Quantity < 0) then
            MoveBuf."Out Qty" += -ItemLedgerEntry.Quantity;
        MoveBuf.Modify();
    end;

    local procedure AddShelfSpan(ItemNo: Code[20]; EntryNo: Integer; SpanDays: Integer)
    begin
        ShelfBuf.Init();
        ShelfBuf."Item No." := ItemNo;
        ShelfBuf."Span Days" := SpanDays;
        ShelfBuf."Entry No." := EntryNo;
        ShelfBuf.Insert();
    end;

    // ------------------------------------------------------------------ nhu cau tung cap
    local procedure ComputeProfiles()
    var
        Balance: Decimal;
        Total: Decimal;
        Src: Decimal;
        MoveQty: Decimal;
        Counted: Integer;
        Censored: Integer;
        D: Date;
    begin
        ProfileBuf.Reset();
        if not ProfileBuf.FindSet() then
            exit;
        repeat
            Balance := OpeningBalance(ProfileBuf."Item No.", ProfileBuf."Location Code");
            Total := 0;
            Counted := 0;
            Censored := 0;
            D := SinceDate;
            while D <= AsOfDate do begin
                if MoveBuf.Get(ProfileBuf."Item No.", ProfileBuf."Location Code", D) then begin
                    if UseSale(ProfileBuf) then
                        Src := MoveBuf."Sale Qty"
                    else
                        Src := MoveBuf."Out Qty";
                    MoveQty := MoveBuf."Move Qty";
                end else begin
                    Src := 0;
                    MoveQty := 0;
                end;
                // Khong con hang va cung khong ban duoc gi: cau bi cat cut, khong tinh vao mau so
                if (Balance <= 0.0001) and (Src <= 0.0001) then
                    Censored += 1
                else begin
                    Counted += 1;
                    Total += Src;
                end;
                Balance += MoveQty;
                D += 1;
            end;

            if UseSale(ProfileBuf) then
                ProfileBuf.Basis := ProfileBuf.Basis::Sale
            else
                ProfileBuf.Basis := ProfileBuf.Basis::Outflow;
            ProfileBuf."Total Qty" := Round(Total, 0.001);
            ProfileBuf."Days Counted" := Counted;
            ProfileBuf."Days Censored" := Censored;
            if Counted > 0 then
                ProfileBuf."Avg Daily" := Round(Total / Counted, 0.0001)
            else
                ProfileBuf."Avg Daily" := 0;
            ProfileBuf.Modify();
        until ProfileBuf.Next() = 0;
    end;

    /// <summary>Cua hang co dong Sale thi dem Sale. Kho luon dem tong luong xuat.</summary>
    local procedure UseSale(Profile: Record "NWV Demand Profile Buffer" temporary): Boolean
    begin
        if LocationRole.IsWarehouse(Profile."Location Code") then
            exit(false);
        exit(Profile."Has Sale");
    end;

    /// <summary>So du dau cua so: tong Quantity co dau cua moi dong truoc SinceDate.</summary>
    local procedure OpeningBalance(ItemNo: Code[20]; LocationCode: Code[10]) Balance: Decimal
    var
        Move: Record "NWV Daily Move Buffer" temporary;
    begin
        Move.Copy(MoveBuf, true);
        Move.Reset();
        Move.SetRange("Item No.", ItemNo);
        Move.SetRange("Location Code", LocationCode);
        Move.SetFilter("Posting Date", '<%1', SinceDate);
        if Move.FindSet() then
            repeat
                Balance += Move."Move Qty";
            until Move.Next() = 0;
    end;

    // ------------------------------------------------------------------ han dung do tu du lieu
    /// <summary>Trung vi cua khoang cach han dung tren dong nhap, moi mat hang. Voi n gia tri
    /// da sap tang dan, lay phan tu thu n div 2 tinh tu 0, giong python.</summary>
    local procedure ComputeShelfLife()
    var
        Span: Record "NWV Shelf Life Buffer" temporary;
        ItemNo: Code[20];
        N: Integer;
    begin
        ShelfBuf.Reset();
        if not ShelfBuf.FindSet() then
            exit;
        repeat
            ItemNo := ShelfBuf."Item No.";
            if not ShelfDays.ContainsKey(ItemNo) then begin
                Span.Copy(ShelfBuf, true);
                Span.Reset();
                Span.SetRange("Item No.", ItemNo);
                N := Span.Count();
                Span.FindFirst();
                if N div 2 > 0 then
                    Span.Next(N div 2);
                ShelfDays.Add(ItemNo, Span."Span Days");
            end;
        until ShelfBuf.Next() = 0;
    end;
}
