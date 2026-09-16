/// <summary>
/// Lop logic cua Inventory Health. AL thuan, khong goi AI.
/// Dau vao: Item Ledger Entry. Dau ra: NWV Inv. Health Line, moi dong = Item x Location x Lot.
///
/// Gia dinh, ghi ro trong tai lieu 05:
/// - Ton kho = tong Remaining Quantity cua Item Ledger Entry co Open = true.
/// - Gia tri ton = Quantity x Item."Unit Cost" cho POC. Ban chinh thuc dung Value Entry.
/// - Nhu cau tinh theo Item x Location bang codeunit NWV Demand Calc, cong thuc chep tu
///   python/bc_agent/inventory.py: loai ngay cau bi cat cut, va dia diem khong he ban thi lay
///   tong luong xuat. Lot chi anh huong Near Expiry.
/// - Ngay neo la WorkDate(), khong phai Today(), de demo dat Work Date la so khop tai lieu.
///
/// Cay phan tang sau bac, dung o bac dau tien khop:
///   Expired > Near Expiry > Stock-out Risk > Slow-moving > Excess > Healthy.
/// </summary>
codeunit 70101 "NWV Inv. Health Calc"
{
    trigger OnRun()
    begin
        CalculateAll();
    end;

    var
        Setup: Record "NWV Agent Setup";
        DemandCalc: Codeunit "NWV Demand Calc";
        AsOfDate: Date;
        NoSalesDaysOfCover: Decimal;
        ExpiredTxt: Label 'Lô đã hết hạn %1 ngày.', Comment = '%1 = so ngay';
        NearNoDemandTxt: Label 'Còn %1 ngày đến hạn, chưa có dòng bán nào để ước lượng.', Comment = '%1 = so ngay';
        NearWillNotSellTxt: Label 'Còn %1 ngày đến hạn nhưng days of cover là %2, sẽ không bán hết.', Comment = '%1 = so ngay, %2 = days of cover';
        NearWillSellTxt: Label 'Còn %1 ngày đến hạn, dự kiến bán hết trước hạn.', Comment = '%1 = so ngay';
        StockOutTxt: Label 'Days of cover %1 dưới ngưỡng %2. Bán bình quân %3 một ngày (%4).', Comment = '%1 = days of cover, %2 = nguong, %3 = binh quan, %4 = co so';
        SlowNoSaleTxt: Label '%1 ngày không có dòng bán. Giá trị tồn %2.', Comment = '%1 = so ngay, %2 = gia tri';
        SlowNoDemandTxt: Label 'Không có dòng bán nào trong cửa sổ lịch sử.';
        ExcessTxt: Label 'Days of cover %1 vượt ngưỡng %2.', Comment = '%1 = days of cover, %2 = nguong';
        HealthyTxt: Label 'Trong ngưỡng.';
        CensoredTxt: Label ' Đã loại %1 ngày hết hàng khỏi phép tính.', Comment = '%1 = so ngay';

    procedure CalculateAll()
    var
        HealthLine: Record "NWV Inv. Health Line";
        TempBuffer: Record "NWV Inv. Health Line" temporary;
        ItemLedgerEntry: Record "Item Ledger Entry";
        RunAt: DateTime;
    begin
        Setup.GetRecordOnce();
        NoSalesDaysOfCover := 9999;
        RunAt := CurrentDateTime();
        AsOfDate := WorkDate();

        DemandCalc.Build(AsOfDate, Setup."Sales History Days");

        HealthLine.DeleteAll();

        // Buoc 1: gom ton theo Item / Location / Lot tu open entries vao buffer tam,
        // khong phu thuoc thu tu sort cua Item Ledger Entry.
        ItemLedgerEntry.SetRange(Open, true);
        ItemLedgerEntry.SetFilter("Remaining Quantity", '<>0');
        if ItemLedgerEntry.FindSet() then
            repeat
                if TempBuffer.Get(ItemLedgerEntry."Item No.", ItemLedgerEntry."Location Code", ItemLedgerEntry."Lot No.") then begin
                    TempBuffer."Quantity on Hand" += ItemLedgerEntry."Remaining Quantity";
                    if (ItemLedgerEntry."Expiration Date" <> 0D) and
                       ((TempBuffer."Expiration Date" = 0D) or (ItemLedgerEntry."Expiration Date" < TempBuffer."Expiration Date"))
                    then
                        TempBuffer."Expiration Date" := ItemLedgerEntry."Expiration Date";
                    TempBuffer.Modify();
                end else begin
                    TempBuffer.Init();
                    TempBuffer."Item No." := ItemLedgerEntry."Item No.";
                    TempBuffer."Location Code" := ItemLedgerEntry."Location Code";
                    TempBuffer."Lot No." := ItemLedgerEntry."Lot No.";
                    TempBuffer."Quantity on Hand" := ItemLedgerEntry."Remaining Quantity";
                    TempBuffer."Expiration Date" := ItemLedgerEntry."Expiration Date";
                    TempBuffer.Insert();
                end;
            until ItemLedgerEntry.Next() = 0;

        // Buoc 2: nhu cau, days of cover, tier cho tung dong buffer
        if TempBuffer.FindSet() then
            repeat
                WriteLine(TempBuffer."Item No.", TempBuffer."Location Code", TempBuffer."Lot No.",
                          TempBuffer."Quantity on Hand", TempBuffer."Expiration Date", RunAt);
            until TempBuffer.Next() = 0;

        Setup."Last Inv. Health Run" := RunAt;
        Setup.Modify();
    end;

    local procedure WriteLine(ItemNo: Code[20]; LocationCode: Code[10]; LotNo: Code[50]; QtyOnHand: Decimal; ExpDate: Date; RunAt: DateTime)
    var
        HealthLine: Record "NWV Inv. Health Line";
        Profile: Record "NWV Demand Profile Buffer" temporary;
        Item: Record Item;
    begin
        if QtyOnHand <= 0 then
            exit; // POC: bo qua ton am, ghi rieng o phan data quality

        if not Item.Get(ItemNo) then
            exit;

        if not DemandCalc.GetProfile(ItemNo, LocationCode, Profile) then
            Profile.Init();

        HealthLine.Init();
        HealthLine."Item No." := ItemNo;
        HealthLine."Location Code" := LocationCode;
        HealthLine."Lot No." := LotNo;
        HealthLine."Item Description" := Item.Description;
        HealthLine."Item Category Code" := Item."Item Category Code";
        HealthLine."Base Unit of Measure" := Item."Base Unit of Measure";
        HealthLine."Quantity on Hand" := QtyOnHand;
        HealthLine."Inventory Value" := QtyOnHand * Item."Unit Cost";
        HealthLine."Avg Daily Sales Qty" := Profile."Avg Daily";
        if Profile."Avg Daily" > 0 then
            HealthLine."Days of Cover" := Round(QtyOnHand / Profile."Avg Daily", 0.1)
        else
            HealthLine."Days of Cover" := NoSalesDaysOfCover;
        HealthLine."Last Sale Date" := Profile."Last Sale Date";
        if Profile."Last Sale Date" <> 0D then
            HealthLine."Days Since Last Sale" := AsOfDate - Profile."Last Sale Date"
        else
            HealthLine."Days Since Last Sale" := Setup."Sales History Days" + 1;
        HealthLine."Expiration Date" := ExpDate;
        if ExpDate <> 0D then
            HealthLine."Days To Expiry" := ExpDate - AsOfDate
        else
            HealthLine."Days To Expiry" := 99999;
        if Profile.Basis = Profile.Basis::Outflow then
            HealthLine."Demand Basis" := HealthLine."Demand Basis"::Outflow
        else
            HealthLine."Demand Basis" := HealthLine."Demand Basis"::Sale;
        HealthLine."Days Censored" := Profile."Days Censored";

        ClassifyTier(HealthLine, Profile."Last Sale Date" <> 0D);
        HealthLine."Calculated At" := RunAt;
        HealthLine."As Of Date" := AsOfDate;
        HealthLine.Insert();
    end;

    /// <summary>
    /// Nguong rieng theo nhom hang neu co, nguoc lai dung nguong chung tren Setup.
    /// Ly do: han dung cua thanh bar va cua bonbon chenh nhau rat xa.
    /// </summary>
    local procedure ThresholdsFor(CategoryCode: Code[20]; var NearDays: Integer; var SlowDays: Integer; var ExcessDays: Decimal)
    var
        CategoryThreshold: Record "NWV Category Threshold";
    begin
        NearDays := Setup."Near Expiry Days";
        SlowDays := Setup."Slow-moving Days";
        ExcessDays := Setup."Excess Days";
        if CategoryCode = '' then
            exit;
        if not CategoryThreshold.Get(CategoryCode) then
            exit;
        if CategoryThreshold."Near Expiry Days" > 0 then
            NearDays := CategoryThreshold."Near Expiry Days";
        if CategoryThreshold."Slow-moving Days" > 0 then
            SlowDays := CategoryThreshold."Slow-moving Days";
        if CategoryThreshold."Excess Days" > 0 then
            ExcessDays := CategoryThreshold."Excess Days";
    end;

    /// <summary>
    /// Thu tu uu tien khi mot dong thoa nhieu dieu kien: Expired > Near Expiry > Stock-out Risk
    /// > Slow-moving > Excess > Healthy. Risk Score 0..100 de sap thu tu, khong phai xac suat.
    ///
    /// HasLastSale = false nghia la dia diem chua he co dong Sale. Khi do "Days Since Last Sale"
    /// khong co nghia, khong duoc dung de ket luan cham luan chuyen. Cham luan chuyen luc do chi
    /// khi nhu cau (tinh tren luong xuat) bang 0.
    /// </summary>
    local procedure ClassifyTier(var HealthLine: Record "NWV Inv. Health Line"; HasLastSale: Boolean)
    var
        Score: Integer;
        Reason: Text;
        NearDays: Integer;
        SlowDays: Integer;
        ExcessDays: Decimal;
        HasDemand: Boolean;
    begin
        Score := 0;
        Reason := '';
        ThresholdsFor(HealthLine."Item Category Code", NearDays, SlowDays, ExcessDays);
        HasDemand := HealthLine."Avg Daily Sales Qty" > 0;

        if HealthLine."Days To Expiry" < 0 then begin
            HealthLine.Tier := HealthLine.Tier::Expired;
            Score := 100;
            Reason := StrSubstNo(ExpiredTxt, -HealthLine."Days To Expiry");
        end else
            if HealthLine."Days To Expiry" <= NearDays then begin
                HealthLine.Tier := HealthLine.Tier::NearExpiry;
                Score := 60 + Round(40 * (1 - HealthLine."Days To Expiry" / NearDays), 1);
                if not HasDemand then
                    Reason := StrSubstNo(NearNoDemandTxt, HealthLine."Days To Expiry")
                else
                    if HealthLine."Days of Cover" > HealthLine."Days To Expiry" then
                        Reason := StrSubstNo(NearWillNotSellTxt, HealthLine."Days To Expiry", HealthLine."Days of Cover")
                    else begin
                        Reason := StrSubstNo(NearWillSellTxt, HealthLine."Days To Expiry");
                        if Score > 65 then
                            Score := 65;
                    end;
            end else
                if HasDemand and (HealthLine."Days of Cover" < Setup."Stock-out Risk Days") then begin
                    HealthLine.Tier := HealthLine.Tier::StockOutRisk;
                    Score := 50 + Round(40 * (1 - HealthLine."Days of Cover" / Setup."Stock-out Risk Days"), 1);
                    Reason := StrSubstNo(StockOutTxt, HealthLine."Days of Cover", Setup."Stock-out Risk Days",
                                         HealthLine."Avg Daily Sales Qty", Format(HealthLine."Demand Basis"));
                end else
                    if HasLastSale and (HealthLine."Days Since Last Sale" >= SlowDays) then begin
                        HealthLine.Tier := HealthLine.Tier::SlowMoving;
                        Score := SlowMovingScore(HealthLine."Inventory Value");
                        Reason := StrSubstNo(SlowNoSaleTxt, HealthLine."Days Since Last Sale", HealthLine."Inventory Value");
                    end else
                        if not HasDemand then begin
                            HealthLine.Tier := HealthLine.Tier::SlowMoving;
                            Score := SlowMovingScore(HealthLine."Inventory Value");
                            Reason := SlowNoDemandTxt;
                        end else
                            if HealthLine."Days of Cover" > ExcessDays then begin
                                HealthLine.Tier := HealthLine.Tier::Excess;
                                Score := 20 + Round(30 * HealthLine."Inventory Value" / 10000, 1);
                                if Score > 60 then
                                    Score := 60;
                                Reason := StrSubstNo(ExcessTxt, HealthLine."Days of Cover", ExcessDays);
                            end else begin
                                HealthLine.Tier := HealthLine.Tier::Healthy;
                                Score := 0;
                                Reason := HealthyTxt;
                            end;

        if HealthLine."Days Censored" > 0 then
            Reason += StrSubstNo(CensoredTxt, HealthLine."Days Censored");

        HealthLine."Risk Score" := Score;
        HealthLine."Risk Reason" := CopyStr(Reason, 1, MaxStrLen(HealthLine."Risk Reason"));
    end;

    local procedure SlowMovingScore(InventoryValue: Decimal): Integer
    var
        Score: Integer;
    begin
        // Cung thang do voi python: moi 10.000 don vi tien ton them 30 diem, tran 70.
        Score := 30 + Round(30 * InventoryValue / 10000, 1);
        if Score > 70 then
            Score := 70;
        exit(Score);
    end;
}
