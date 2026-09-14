/// <summary>
/// Lop logic Discount Governance (POC B, use case 7). AL thuan, rule doc duoc bang mat.
/// Ba rule POC:
///   DG-01 High   : mot dong manual discount / price override co Discount % > Max Manual Discount % (tru khi Manager Override = true)
///   DG-02 Medium : mot staff trong mot ngay tai mot store co ty trong doanh so manual discount > Manual Disc. Share Warn %
///   DG-03 Medium : mot staff trong mot ngay dung manual discount qua Repeat Discount Count lan
/// Kiem soat TRUOC khi giam gia (staff permission, approval tai POS) la cau hinh LS Central; codeunit nay lam kiem soat SAU.
/// </summary>
codeunit 70104 "NWV Discount Gov. Calc"
{
    trigger OnRun()
    begin
        CalculateAll();
    end;

    var
        Setup: Record "NWV Agent Setup";

    procedure CalculateAll()
    var
        Exception: Record "NWV Discount Exception";
        RunAt: DateTime;
    begin
        Setup.GetRecordOnce();
        RunAt := CurrentDateTime();

        // Chi xoa exception con Open de giu lai lich su da xu ly
        Exception.SetRange(Status, Exception.Status::Open);
        Exception.DeleteAll();

        RuleSingleLineOverMax(RunAt);
        RuleStaffDayShareAndRepeat(RunAt);

        Setup."Last Discount Gov. Run" := RunAt;
        Setup.Modify();
    end;

    local procedure IsManual(DiscountLog: Record "NWV POS Discount Log"): Boolean
    begin
        exit(DiscountLog."Discount Type" in [DiscountLog."Discount Type"::ManualLine, DiscountLog."Discount Type"::ManualTotal, DiscountLog."Discount Type"::PriceOverride]);
    end;

    local procedure RuleSingleLineOverMax(RunAt: DateTime)
    var
        DiscountLog: Record "NWV POS Discount Log";
    begin
        DiscountLog.SetFilter("Discount Type", '%1|%2|%3', DiscountLog."Discount Type"::ManualLine, DiscountLog."Discount Type"::ManualTotal, DiscountLog."Discount Type"::PriceOverride);
        DiscountLog.SetFilter("Discount %", '>%1', Setup."Max Manual Discount %");
        DiscountLog.SetRange("Manager Override", false);
        if DiscountLog.FindSet() then
            repeat
                InsertException('DG-01', "NWV Exception Severity"::High, DiscountLog."Store No.", DiscountLog."Staff ID", DiscountLog."Trans. Date",
                    DiscountLog."Transaction No.", DiscountLog."POS Terminal No.", DiscountLog."Item No.",
                    DiscountLog."Discount %", Setup."Max Manual Discount %", DiscountLog."Discount Amount", 1,
                    StrSubstNo('Manual discount %1% trên item %2, vượt mức %3% mà không có manager override.', DiscountLog."Discount %", DiscountLog."Item No.", Setup."Max Manual Discount %"),
                    DiscountLog."Source Entry Key", RunAt);
            until DiscountLog.Next() = 0;
    end;

    local procedure RuleStaffDayShareAndRepeat(RunAt: DateTime)
    var
        DiscountLog: Record "NWV POS Discount Log";
        ManualDiscTotal: Decimal;
        GrossTotal: Decimal;
        ManualCount: Integer;
        CurStore: Code[10];
        CurStaff: Code[20];
        CurDate: Date;
    begin
        DiscountLog.SetCurrentKey("Store No.", "Staff ID", "Trans. Date");
        if not DiscountLog.FindSet() then
            exit;
        CurStore := DiscountLog."Store No.";
        CurStaff := DiscountLog."Staff ID";
        CurDate := DiscountLog."Trans. Date";
        repeat
            if (DiscountLog."Store No." <> CurStore) or (DiscountLog."Staff ID" <> CurStaff) or (DiscountLog."Trans. Date" <> CurDate) then begin
                FlushStaffDay(CurStore, CurStaff, CurDate, ManualDiscTotal, GrossTotal, ManualCount, RunAt);
                CurStore := DiscountLog."Store No.";
                CurStaff := DiscountLog."Staff ID";
                CurDate := DiscountLog."Trans. Date";
                ManualDiscTotal := 0;
                GrossTotal := 0;
                ManualCount := 0;
            end;
            GrossTotal += DiscountLog."Gross Amount";
            if IsManual(DiscountLog) then begin
                ManualDiscTotal += DiscountLog."Discount Amount";
                ManualCount += 1;
            end;
        until DiscountLog.Next() = 0;
        FlushStaffDay(CurStore, CurStaff, CurDate, ManualDiscTotal, GrossTotal, ManualCount, RunAt);
    end;

    local procedure FlushStaffDay(StoreNo: Code[10]; StaffId: Code[20]; TransDate: Date; ManualDiscTotal: Decimal; GrossTotal: Decimal; ManualCount: Integer; RunAt: DateTime)
    var
        SharePct: Decimal;
        RefKey: Text[100];
    begin
        RefKey := CopyStr(StrSubstNo('%1|%2|%3', StoreNo, StaffId, Format(TransDate, 0, 9)), 1, 100);
        if GrossTotal > 0 then
            SharePct := Round(ManualDiscTotal / GrossTotal * 100, 0.01)
        else
            SharePct := 0;

        if SharePct > Setup."Manual Disc. Share Warn %" then
            InsertException('DG-02', "NWV Exception Severity"::Medium, StoreNo, StaffId, TransDate, 0, '', '',
                SharePct, Setup."Manual Disc. Share Warn %", ManualDiscTotal, ManualCount,
                StrSubstNo('Ty trong manual discount %1% tren doanh so cac dong co discount, vuot %2%.', SharePct, Setup."Manual Disc. Share Warn %"),
                RefKey, RunAt);

        if ManualCount > Setup."Repeat Discount Count" then
            InsertException('DG-03', "NWV Exception Severity"::Medium, StoreNo, StaffId, TransDate, 0, '', '',
                ManualCount, Setup."Repeat Discount Count", ManualDiscTotal, ManualCount,
                StrSubstNo('%1 lần manual discount trong ngày, vượt mức %2 lần.', ManualCount, Setup."Repeat Discount Count"),
                RefKey, RunAt);
    end;

    local procedure InsertException(RuleCode: Code[20]; Severity: Enum "NWV Exception Severity"; StoreNo: Code[10]; StaffId: Code[20]; TransDate: Date; TransNo: Integer; TerminalNo: Code[10]; ItemNo: Code[20]; MetricValue: Decimal; ThresholdValue: Decimal; DiscAmount: Decimal; Occurrences: Integer; Descr: Text; RefKey: Text[100]; RunAt: DateTime)
    var
        Exception: Record "NWV Discount Exception";
    begin
        // Khong tao trung neu da co exception cung rule + reference dang duoc xu ly
        Exception.SetRange("Rule Code", RuleCode);
        Exception.SetRange("Reference Key", RefKey);
        Exception.SetFilter(Status, '<>%1', Exception.Status::Open);
        if not Exception.IsEmpty() then
            exit;

        Exception.Init();
        Exception."Rule Code" := RuleCode;
        Exception.Severity := Severity;
        Exception."Store No." := StoreNo;
        Exception."Staff ID" := StaffId;
        Exception."Trans. Date" := TransDate;
        Exception."Transaction No." := TransNo;
        Exception."POS Terminal No." := TerminalNo;
        Exception."Item No." := ItemNo;
        Exception."Metric Value" := MetricValue;
        Exception."Threshold Value" := ThresholdValue;
        Exception."Discount Amount" := DiscAmount;
        Exception."Occurrence Count" := Occurrences;
        Exception.Description := CopyStr(Descr, 1, MaxStrLen(Exception.Description));
        Exception.Status := Exception.Status::Open;
        Exception."Detected At" := RunAt;
        Exception."Reference Key" := RefKey;
        Exception.Insert();
    end;
}
