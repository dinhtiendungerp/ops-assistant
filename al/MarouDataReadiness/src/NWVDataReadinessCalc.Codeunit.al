/// <summary>
/// Dem do phu du lieu de tra loi bon cau hoi truoc khi chot pham vi POC:
///   1. Ty le Item Ledger Entry con mo co Lot No.
///   2. Ty le Item Ledger Entry con mo co Expiration Date
///   3. Lich su ban dai bao nhieu thang
///   4. Master data da du de quy ton ra tien va phan nhom nguong chua
///
/// Chi doc. Khong ghi gi vao du lieu chuan. Chay thu cong mot lan, khong phai job hang dem,
/// nen chap nhan quet het bang Item Ledger Entry thay vi toi uu theo key.
/// Nguon truong: Expiration Date nam tren Item Ledger Entry, khong nam tren Lot No. Information.
/// </summary>
codeunit 70050 "NWV Data Readiness Calc"
{
    var
        NextEntryNo: Integer;
        RunAt: DateTime;

    procedure Run()
    var
        ReadinessLine: Record "NWV Data Readiness Line";
    begin
        ReadinessLine.DeleteAll();
        NextEntryNo := 0;
        RunAt := CurrentDateTime();

        CheckLotAndExpiry();
        CheckSalesHistory();
        CheckMasterData();
        CheckReplenishmentReadiness();
    end;

    // ---------------------------------------------------------------- nhom 1
    local procedure CheckLotAndExpiry()
    var
        ItemLedgerEntry: Record "Item Ledger Entry";
        Item: Record Item;
        LotKeys: Dictionary of [Text, Boolean];
        LotKey: Text;
        TotalOpen: Integer;
        WithLot: Integer;
        WithExpiry: Integer;
        TotalItems: Integer;
        WithTracking: Integer;
    begin
        ItemLedgerEntry.Reset();
        ItemLedgerEntry.SetRange(Open, true);
        ItemLedgerEntry.SetFilter("Remaining Quantity", '>%1', 0);
        ItemLedgerEntry.SetLoadFields("Item No.", "Lot No.", "Expiration Date", "Location Code");
        if ItemLedgerEntry.FindSet() then
            repeat
                TotalOpen += 1;
                if ItemLedgerEntry."Lot No." <> '' then begin
                    WithLot += 1;
                    LotKey := ItemLedgerEntry."Item No." + '|' + ItemLedgerEntry."Lot No.";
                    if not LotKeys.ContainsKey(LotKey) then
                        LotKeys.Add(LotKey, true);
                end;
                if ItemLedgerEntry."Expiration Date" <> 0D then
                    WithExpiry += 1;
            until ItemLedgerEntry.Next() = 0;

        AddInfo('DR-01', 'Lô và hạn dùng', 'Số dòng Item Ledger Entry còn tồn',
                Format(TotalOpen), 'Đây là mẫu số của mọi tỷ lệ bên dưới. Bằng 0 thì công ty đang trống tồn kho.');

        AddPct('DR-02', 'Lô và hạn dùng', 'Tỷ lệ dòng tồn có Lot No.',
               WithLot, TotalOpen, 80, 40,
               'Không có lô thì phân tầng chỉ chạy được ở mức Item và Location. Mất hẳn phần theo dõi cận date theo lô.');

        AddPct('DR-03', 'Lô và hạn dùng', 'Tỷ lệ dòng tồn có Expiration Date',
               WithExpiry, TotalOpen, 80, 40,
               'Thiếu thì bậc Expired và Near Expiry của cây phân tầng rỗng, tức mất phần giá trị nhất của UC2.');

        AddInfo('DR-04', 'Lô và hạn dùng', 'Số lô riêng biệt đang còn tồn',
                Format(LotKeys.Count()), 'Số dòng mà cây phân tầng sẽ chạy trên đó.');

        Item.Reset();
        Item.SetRange(Type, Item.Type::Inventory);
        Item.SetRange(Blocked, false);
        Item.SetLoadFields("Item Tracking Code", "Item Category Code", "Unit Cost");
        if Item.FindSet() then
            repeat
                TotalItems += 1;
                if Item."Item Tracking Code" <> '' then
                    WithTracking += 1;
            until Item.Next() = 0;

        AddPct('DR-05', 'Lô và hạn dùng', 'Tỷ lệ mặt hàng tồn kho có Item Tracking Code',
               WithTracking, TotalItems, 80, 40,
               'Mặt hàng không bật item tracking thì hàng nhập sau này vẫn không có lô, nên tỷ lệ DR-02 sẽ không tự cải thiện.');
    end;

    // ---------------------------------------------------------------- nhom 2
    local procedure CheckSalesHistory()
    var
        ItemLedgerEntry: Record "Item Ledger Entry";
        PairKeys: Dictionary of [Text, Boolean];
        PairKey: Text;
        FirstSale: Date;
        Since: Date;
        Recent: Integer;
        Months: Decimal;
    begin
        ItemLedgerEntry.Reset();
        ItemLedgerEntry.SetRange("Entry Type", ItemLedgerEntry."Entry Type"::Sale);
        ItemLedgerEntry.SetLoadFields("Posting Date");
        if ItemLedgerEntry.FindSet() then
            repeat
                if (FirstSale = 0D) or (ItemLedgerEntry."Posting Date" < FirstSale) then
                    FirstSale := ItemLedgerEntry."Posting Date";
            until ItemLedgerEntry.Next() = 0;

        if FirstSale = 0D then begin
            AddInfo('DR-10', 'Lịch sử bán', 'Ngày bán sớm nhất trong Item Ledger Entry',
                    'không có dòng bán nào', 'Không có lịch sử bán thì không tính được tốc độ bán, Days of Cover và dự báo.');
            AddNum('DR-11', 'Lịch sử bán', 'Độ dài lịch sử bán', 0, 'tháng', 12, 6,
                   'Dưới 6 tháng thì tốc độ bán bình quân không đáng tin, kéo theo Days of Cover sai. Dưới 12 tháng thì không bắt được mùa Tết.');
            exit;
        end;

        Months := Round((WorkDate() - FirstSale) / 30, 0.1);
        AddInfo('DR-10', 'Lịch sử bán', 'Ngày bán sớm nhất trong Item Ledger Entry',
                Format(FirstSale), 'Mốc bắt đầu của mọi phép tính lịch sử.');
        AddNum('DR-11', 'Lịch sử bán', 'Độ dài lịch sử bán', Months, 'tháng', 12, 6,
               'Dưới 6 tháng thì tốc độ bán bình quân không đáng tin, kéo theo Days of Cover sai. Dưới 12 tháng thì không bắt được mùa Tết.');

        Since := CalcDate('<-90D>', WorkDate());
        ItemLedgerEntry.Reset();
        ItemLedgerEntry.SetRange("Entry Type", ItemLedgerEntry."Entry Type"::Sale);
        ItemLedgerEntry.SetRange("Posting Date", Since, WorkDate());
        ItemLedgerEntry.SetLoadFields("Item No.", "Location Code");
        if ItemLedgerEntry.FindSet() then
            repeat
                Recent += 1;
                PairKey := ItemLedgerEntry."Item No." + '|' + ItemLedgerEntry."Location Code";
                if not PairKeys.ContainsKey(PairKey) then
                    PairKeys.Add(PairKey, true);
            until ItemLedgerEntry.Next() = 0;

        AddInfo('DR-12', 'Lịch sử bán', 'Số dòng bán trong 90 ngày gần nhất',
                Format(Recent), 'Cửa sổ mặc định để tính tốc độ bán bình quân.');
        AddNum('DR-13', 'Lịch sử bán', 'Số cặp mặt hàng và cửa hàng có bán trong 90 ngày',
               PairKeys.Count(), 'cặp', 20, 5,
               'Mỗi cặp là một dòng trong bảng bổ sung hàng. Quá ít thì UC5 không có gì để chạy.');
    end;

    // ---------------------------------------------------------------- nhom 3
    local procedure CheckMasterData()
    var
        Item: Record Item;
        Location: Record Location;
        CategoryKeys: Dictionary of [Text, Boolean];
        TotalItems: Integer;
        WithCategory: Integer;
        WithCost: Integer;
        Locations: Integer;
    begin
        Item.Reset();
        Item.SetRange(Type, Item.Type::Inventory);
        Item.SetRange(Blocked, false);
        Item.SetLoadFields("Item Category Code", "Unit Cost");
        if Item.FindSet() then
            repeat
                TotalItems += 1;
                if Item."Item Category Code" <> '' then begin
                    WithCategory += 1;
                    if not CategoryKeys.ContainsKey(Item."Item Category Code") then
                        CategoryKeys.Add(Item."Item Category Code", true);
                end;
                if Item."Unit Cost" > 0 then
                    WithCost += 1;
            until Item.Next() = 0;

        AddInfo('DR-19', 'Master data', 'Số mặt hàng tồn kho chưa bị chặn',
                Format(TotalItems), 'Mẫu số của hai tỷ lệ bên dưới.');

        AddPct('DR-20', 'Master data', 'Tỷ lệ mặt hàng có Item Category Code',
               WithCategory, TotalItems, 90, 60,
               'Không phân nhóm thì phải dùng một ngưỡng cận date chung cho cả thanh bar lẫn bonbon, trong khi hạn dùng hai nhóm chênh nhau rất xa.');

        AddInfo('DR-21', 'Master data', 'Số Item Category đang được dùng',
                Format(CategoryKeys.Count()), 'Số ngưỡng cận date riêng có thể đặt được.');

        AddPct('DR-22', 'Master data', 'Tỷ lệ mặt hàng có Unit Cost lớn hơn 0',
               WithCost, TotalItems, 95, 80,
               'Thiếu giá vốn thì không quy tồn ra tiền được, và toàn bộ con số giá trị tồn xấu trong báo cáo sẽ thấp hơn thực tế.');

        Location.Reset();
        Location.SetRange("Use As In-Transit", false);
        Locations := Location.Count();
        AddNum('DR-23', 'Master data', 'Số kho và cửa hàng không tính kho trung chuyển',
               Locations, 'địa điểm', 2, 1,
               'Chỉ có một địa điểm thì không có gì để điều chuyển, UC5 mất ý nghĩa.');
    end;

    // ---------------------------------------------------------------- nhom 4
    local procedure CheckReplenishmentReadiness()
    var
        Item: Record Item;
        StockkeepingUnit: Record "Stockkeeping Unit";
        TransferRoute: Record "Transfer Route";
        TotalItems: Integer;
        WithPolicy: Integer;
    begin
        Item.Reset();
        Item.SetRange(Type, Item.Type::Inventory);
        Item.SetRange(Blocked, false);
        Item.SetLoadFields("Reordering Policy");
        if Item.FindSet() then
            repeat
                TotalItems += 1;
                if Item."Reordering Policy" <> Item."Reordering Policy"::" " then
                    WithPolicy += 1;
            until Item.Next() = 0;

        // Ba dong duoi day chi la thong tin, tru DR-32. Ly do: lop AL cua POC tu tinh nguong rieng,
        // nen Reordering Policy va Stockkeeping Unit khong phai dieu kien de POC chay duoc.
        // Nguoc lai, khong co Transfer Route thi that su khong tao duoc chung tu chuyen hang.
        if TotalItems > 0 then
            AddInfo('DR-30', 'Sẵn sàng cho UC5', 'Số mặt hàng đã đặt Reordering Policy',
                    StrSubstNo('%1 / %2', WithPolicy, TotalItems),
                    'Không bắt buộc cho POC vì lớp AL tự tính ngưỡng riêng. Con số này chỉ cho biết Marou đang dùng phần lập kế hoạch chuẩn của BC tới đâu.')
        else
            AddInfo('DR-30', 'Sẵn sàng cho UC5', 'Số mặt hàng đã đặt Reordering Policy', '0 / 0',
                    'Không có mặt hàng tồn kho nào để đếm.');

        AddInfo('DR-31', 'Sẵn sàng cho UC5', 'Số Stockkeeping Unit đã tạo',
                Format(StockkeepingUnit.Count()),
                'Bằng 0 thì ngưỡng chuẩn của BC chỉ đặt được ở cấp mặt hàng. Không chặn POC, vì lớp AL đặt ngưỡng theo từng cặp cửa hàng và mặt hàng.');

        AddNum('DR-32', 'Sẵn sàng cho UC5', 'Số Transfer Route đã cấu hình',
               TransferRoute.Count(), 'tuyến', 1, 1,
               'Bằng 0 thì không tạo được Transfer Order giữa các địa điểm, tức là phần hành động của UC2 và UC5 dừng ở mức đề xuất.');
    end;

    // ---------------------------------------------------------------- ghi dong
    local procedure AddInfo(CheckCode: Code[10]; GroupName: Text; Descr: Text; ValueText: Text; ImpactText: Text)
    var
        ReadinessLine: Record "NWV Data Readiness Line";
    begin
        NextEntryNo += 1;
        ReadinessLine.Init();
        ReadinessLine."Entry No." := NextEntryNo;
        ReadinessLine."Check Code" := CheckCode;
        ReadinessLine."Group Name" := CopyStr(GroupName, 1, MaxStrLen(ReadinessLine."Group Name"));
        ReadinessLine.Description := CopyStr(Descr, 1, MaxStrLen(ReadinessLine.Description));
        ReadinessLine."Value Text" := CopyStr(ValueText, 1, MaxStrLen(ReadinessLine."Value Text"));
        ReadinessLine.Verdict := ReadinessLine.Verdict::Info;
        ReadinessLine.Impact := CopyStr(ImpactText, 1, MaxStrLen(ReadinessLine.Impact));
        ReadinessLine."Calculated At" := RunAt;
        ReadinessLine.Insert();
    end;

    local procedure AddPct(CheckCode: Code[10]; GroupName: Text; Descr: Text; Num: Integer; Den: Integer; OkPct: Decimal; WarnPct: Decimal; ImpactText: Text)
    var
        ReadinessLine: Record "NWV Data Readiness Line";
        Pct: Decimal;
    begin
        if Den > 0 then
            Pct := Round(Num / Den * 100, 0.1)
        else
            Pct := 0;

        NextEntryNo += 1;
        ReadinessLine.Init();
        ReadinessLine."Entry No." := NextEntryNo;
        ReadinessLine."Check Code" := CheckCode;
        ReadinessLine."Group Name" := CopyStr(GroupName, 1, MaxStrLen(ReadinessLine."Group Name"));
        ReadinessLine.Description := CopyStr(Descr, 1, MaxStrLen(ReadinessLine.Description));
        ReadinessLine.Numerator := Num;
        ReadinessLine.Denominator := Den;
        ReadinessLine."Percent" := Pct;
        ReadinessLine."Value Text" := CopyStr(StrSubstNo('%1 / %2  (%3%)', Num, Den, Pct), 1, MaxStrLen(ReadinessLine."Value Text"));
        if Den = 0 then
            ReadinessLine.Verdict := ReadinessLine.Verdict::Blocker
        else
            if Pct >= OkPct then
                ReadinessLine.Verdict := ReadinessLine.Verdict::OK
            else
                if Pct >= WarnPct then
                    ReadinessLine.Verdict := ReadinessLine.Verdict::Warning
                else
                    ReadinessLine.Verdict := ReadinessLine.Verdict::Blocker;
        ReadinessLine.Impact := CopyStr(ImpactText, 1, MaxStrLen(ReadinessLine.Impact));
        ReadinessLine."Calculated At" := RunAt;
        ReadinessLine.Insert();
    end;

    local procedure AddNum(CheckCode: Code[10]; GroupName: Text; Descr: Text; Value: Decimal; UnitText: Text; OkMin: Decimal; WarnMin: Decimal; ImpactText: Text)
    var
        ReadinessLine: Record "NWV Data Readiness Line";
    begin
        NextEntryNo += 1;
        ReadinessLine.Init();
        ReadinessLine."Entry No." := NextEntryNo;
        ReadinessLine."Check Code" := CheckCode;
        ReadinessLine."Group Name" := CopyStr(GroupName, 1, MaxStrLen(ReadinessLine."Group Name"));
        ReadinessLine.Description := CopyStr(Descr, 1, MaxStrLen(ReadinessLine.Description));
        ReadinessLine.Numerator := Value;
        ReadinessLine."Value Text" := CopyStr(StrSubstNo('%1 %2', Value, UnitText), 1, MaxStrLen(ReadinessLine."Value Text"));
        if Value >= OkMin then
            ReadinessLine.Verdict := ReadinessLine.Verdict::OK
        else
            if Value >= WarnMin then
                ReadinessLine.Verdict := ReadinessLine.Verdict::Warning
            else
                ReadinessLine.Verdict := ReadinessLine.Verdict::Blocker;
        ReadinessLine.Impact := CopyStr(ImpactText, 1, MaxStrLen(ReadinessLine.Impact));
        ReadinessLine."Calculated At" := RunAt;
        ReadinessLine.Insert();
    end;
}
