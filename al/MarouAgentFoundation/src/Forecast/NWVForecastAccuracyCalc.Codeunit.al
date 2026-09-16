// UC1 Demand Planning: do chinh xac du bao tren du lieu that va lap du bao cho cac ngay toi.
// AL thuan, khong goi AI. Cong thuc chep sang python/bc_agent/forecast.py (backtest_bc, holt_winters) de doi chieu doc lap.
//
// Cach do (backtest):
// - Ky kiem tra la Holdout Days ngay cuoi, ket thuc tai WorkDate(). Du bao lap bang du lieu TRUOC ky do, roi so voi ban that.
// - Nhu cau moi ngay lay tu NWV Demand Calc: cua hang co ban thi dem Sale.
// - Ngay het hang ma khong ban duoc gi (ton dau ngay <= 0 va nhu cau = 0) bo khoi ca du lieu hoc lan phep tinh sai so.
// - Ngay co su kien cung bo: dong LSC Replen. Planned Sales Demand dang Enabled cua dung mat hang, dia diem, ngay (lich
//   khuyen mai chuan cua LS), va NWV Demand Exception (gia dinh khac nguoi dung khai).
// - MA28: trung binh 28 ngay hop le gan nhat truoc ky kiem tra, nhin lui toi da 84 ngay.
// - SWA8: trung binh cung thu trong tuan tren cac ngay hop le cua 56 ngay truoc ky kiem tra.
// - HW: Holt-Winters cong tinh, mua vu tuan. Ngay khong hop le duoc dien bang trung binh cung thu 8 tuan truoc. Tham so chon
//   theo tong binh phuong sai so mot buoc tren du lieu hoc, luoi alpha x gamma x (khong xu huong | xu huong tat dan).
// - WAPE % = tong |thuc te - du bao| / tong thuc te x 100. Bias % = (tong du bao - tong thuc te) / tong thuc te x 100.
//
// Du bao cho cac ngay toi: HW hoc tren toan bo lich su den WorkDate(), du bao Forecast Horizon Days ngay, ghi vao
// LSC Forecast Entry khi bat Publish LS Forecast. Kieu tinh "Retail Forecast" (LS Forecast) cua LS Replenishment doc bang do,
// roi tu cong Planned Sales Demand cua cac ngay toi; nen du bao o day la muc nen, KHONG cong khuyen mai.
codeunit 70120 "NWV Forecast Accuracy Calc"
{
    trigger OnRun()
    begin
        CalculateAll();
    end;

    var
        Setup: Record "NWV Agent Setup";
        DemandCalc: Codeunit "NWV Demand Calc";
        ExceptionDays: Dictionary of [Text, Boolean];
        HighWapeTxt: Label 'WAPE %1% vượt ngưỡng %2%.', Comment = '%1 = wape, %2 = nguong';
        OverTxt: Label 'Dự báo cao hơn bán thực tế %1%.', Comment = '%1 = bias';
        UnderTxt: Label 'Dự báo thấp hơn bán thực tế %1%.', Comment = '%1 = bias';
        ParamsTxt: Label 'alpha %1, gamma %2, %3', Comment = '%1 alpha, %2 gamma, %3 xu huong', Locked = true;
        NoTrendTxt: Label 'khong xu huong', Locked = true;
        DampedTxt: Label 'xu huong tat dan (beta 0.1, phi 0.9)', Locked = true;
        MethodMA28Tok: Label 'MA28', Locked = true;
        MethodSWA8Tok: Label 'SWA8', Locked = true;
        MethodHWTok: Label 'HW', Locked = true;
        TrainLookbackDays: Integer;
        HWLookbackDays: Integer;
        EntriesWritten: Integer;
        LocationRole: Codeunit "NWV Location Role";

    procedure CalculateAll()
    var
        Acc: Record "NWV Forecast Accuracy";
        Daily: Record "NWV Forecast Daily";
        Profiles: Record "NWV Demand Profile Buffer" temporary;
        AsOf: Date;
        HoldoutFrom: Date;
        RunAt: DateTime;
    begin
        Setup.GetRecordOnce();
        TrainLookbackDays := 84;
        HWLookbackDays := 365;
        EntriesWritten := 0;
        AsOf := WorkDate();
        HoldoutFrom := AsOf - Setup.EffHoldoutDays() + 1;
        RunAt := CurrentDateTime();
        // Cua so profile giu nhu cu (ky hoc 84 ngay + ky kiem tra) de tap cap duoc do khong doi; ILE doc het vao bo dem.
        DemandCalc.Build(AsOf, Setup.EffHoldoutDays() + TrainLookbackDays);
        DemandCalc.CopyProfiles(Profiles);
        LoadExceptionDays(AsOf - HWLookbackDays - Setup.EffHoldoutDays(), AsOf);

        Acc.DeleteAll();
        Daily.DeleteAll();
        Profiles.Reset();
        if Profiles.FindSet() then
            repeat
                // Chi do nhu cau ban tai cua hang (LSC Store, LSC Store Location). Kho xuat hang theo lich chuyen nen luong xuat
                // tung ngay giat cuc, WAPE ngay tren 100% khong noi gi ve du bao. Do lan dau tren BC 14/09/2026: cua hang 32-48%,
                // W0003 93-129%.
                if Profiles."Has Sale" and LocationRole.IsStore(Profiles."Location Code") then
                    CalculatePair(Profiles, AsOf, HoldoutFrom, RunAt);
            until Profiles.Next() = 0;

        Setup."Last Forecast Run" := RunAt;
        Setup.Modify();
    end;

    procedure LSForecastEntriesWritten(): Integer
    begin
        exit(EntriesWritten);
    end;

    local procedure CalculatePair(Profile: Record "NWV Demand Profile Buffer" temporary; AsOf: Date; HoldoutFrom: Date; RunAt: DateTime)
    var
        Item: Record Item;
        Demand: array[500] of Decimal;
        Valid: array[500] of Boolean;
        Censored: array[500] of Boolean;
        Excluded: array[500] of Boolean;
        Fc: array[100] of Decimal;
        Season: array[7] of Decimal;
        FirstDate: Date;
        D: Date;
        I: Integer;
        H: Integer;
        N: Integer;
        TrainEnd: Integer;
        ShortStart: Integer;
        Holdout: Integer;
        Balance: Decimal;
        DemandQty: Decimal;
        MoveQty: Decimal;
        HasHistory: Boolean;
        TotalDemand: Decimal;
        Level: Decimal;
        Trend: Decimal;
        Alpha: Decimal;
        Gamma: Decimal;
        Beta: Decimal;
        Phi: Decimal;
        Sigma: Decimal;
        WeekdayLevel: array[7] of Decimal;
        HWWape: Decimal;
        Params: Text;
    begin
        Holdout := Setup.EffHoldoutDays();
        FirstDate := HoldoutFrom - HWLookbackDays;
        N := AsOf - FirstDate + 1;
        TrainEnd := HoldoutFrom - FirstDate;              // chi so ngay cuoi cua du lieu hoc
        ShortStart := TrainEnd - TrainLookbackDays + 1;   // ngay dau cua cua so 84 ngay dung cho MA28, SWA8
        Balance := DemandCalc.BalanceBefore(Profile."Item No.", Profile."Location Code", FirstDate);
        for I := 1 to N do begin
            D := FirstDate + I - 1;
            if I = ShortStart then
                HasHistory := Balance <> 0;
            DemandCalc.GetDay(Profile."Item No.", Profile."Location Code", D, DemandQty, MoveQty);
            if (MoveQty <> 0) and (I >= ShortStart) and (I <= TrainEnd - 27) then
                HasHistory := true;
            Demand[I] := DemandQty;
            Censored[I] := (Balance <= 0.0001) and (DemandQty <= 0.0001);
            Excluded[I] := IsExceptionDay(Profile."Item No.", Profile."Location Code", D);
            Valid[I] := not Censored[I] and not Excluded[I];
            if I >= ShortStart then
                TotalDemand += DemandQty;
            Balance += MoveQty;
        end;
        // Can it nhat 28 ngay co bien dong truoc ky kiem tra, va phai co ban trong cua so 84 ngay + ky kiem tra.
        if not HasHistory or (TotalDemand <= 0) then
            exit;
        if not Item.Get(Profile."Item No.") then
            Clear(Item);

        Level := MA28Level(Demand, Valid, TrainEnd);
        for H := 1 to Holdout do
            Fc[H] := Level;
        WriteMethod(Profile, Item, MethodMA28Tok, Demand, Censored, Excluded, TrainEnd, N, FirstDate, AsOf, HoldoutFrom, RunAt, Fc, '');

        SWA8Levels(Demand, Valid, TrainEnd, FirstDate, Level, WeekdayLevel);
        for H := 1 to Holdout do
            Fc[H] := WeekdayLevel[Date2DWY(HoldoutFrom + H - 1, 1)];
        WriteMethod(Profile, Item, MethodSWA8Tok, Demand, Censored, Excluded, TrainEnd, N, FirstDate, AsOf, HoldoutFrom, RunAt, Fc, '');

        // Holt-Winters tren du lieu hoc; khong du 28 ngay tu lan ban dau thi lay muc MA28 va ghi ro.
        if FitHoltWinters(Demand, Valid, TrainEnd, FirstDate, Level, Trend, Season, Alpha, Gamma, Beta, Phi, Sigma) then begin
            for H := 1 to Holdout do
                Fc[H] := HWForecast(Level, Trend, Season, Phi, H, Date2DWY(HoldoutFrom + H - 1, 1));
            Params := StrSubstNo(ParamsTxt, Format(Alpha, 0, 9), Format(Gamma, 0, 9), TrendText(Beta));
        end else begin
            Level := MA28Level(Demand, Valid, TrainEnd);
            for H := 1 to Holdout do
                Fc[H] := Level;
            Params := 'thieu lich su, dung MA28';
        end;
        HWWape := WriteMethod(Profile, Item, MethodHWTok, Demand, Censored, Excluded, TrainEnd, N, FirstDate, AsOf, HoldoutFrom, RunAt, Fc, Params);

        if Setup."Publish LS Forecast" then
            if FitHoltWinters(Demand, Valid, N, FirstDate, Level, Trend, Season, Alpha, Gamma, Beta, Phi, Sigma) then
                PublishLSForecast(Profile."Item No.", Profile."Location Code", AsOf, Level, Trend, Season, Phi, Sigma, HWWape);
    end;

    local procedure MA28Level(var Demand: array[500] of Decimal; var Valid: array[500] of Boolean; TrainEnd: Integer): Decimal
    var
        I: Integer;
        Counted: Integer;
        Total: Decimal;
    begin
        I := TrainEnd;
        while (I >= 1) and (I > TrainEnd - TrainLookbackDays) and (Counted < 28) do begin
            if Valid[I] then begin
                Total += Demand[I];
                Counted += 1;
            end;
            I -= 1;
        end;
        if Counted = 0 then
            exit(0);
        exit(Total / Counted);
    end;

    local procedure SWA8Levels(var Demand: array[500] of Decimal; var Valid: array[500] of Boolean; TrainEnd: Integer; FirstDate: Date; MA28: Decimal; var WeekdayLevel: array[7] of Decimal)
    var
        Totals: array[7] of Decimal;
        Counts: array[7] of Integer;
        I: Integer;
        W: Integer;
    begin
        for I := TrainEnd - 55 to TrainEnd do
            if I >= 1 then
                if Valid[I] then begin
                    W := Date2DWY(FirstDate + I - 1, 1);
                    Totals[W] += Demand[I];
                    Counts[W] += 1;
                end;
        for W := 1 to 7 do
            if Counts[W] > 0 then
                WeekdayLevel[W] := Totals[W] / Counts[W]
            else
                WeekdayLevel[W] := MA28;
    end;

    // Hoc Holt-Winters tren Demand[Start..EndIdx], Start la ngay dau co ban. Tra ve trang thai cuoi (Level, Trend, Season theo
    // thu 1..7) va tham so da chon. False khi co it hon 28 ngay tu lan ban dau.
    local procedure FitHoltWinters(var Demand: array[500] of Decimal; var Valid: array[500] of Boolean; EndIdx: Integer; FirstDate: Date;
        var Level: Decimal; var Trend: Decimal; var Season: array[7] of Decimal; var Alpha: Decimal; var Gamma: Decimal;
        var Beta: Decimal; var Phi: Decimal; var Sigma: Decimal): Boolean
    var
        Y: array[500] of Decimal;
        Alphas: array[5] of Decimal;
        Gammas: array[4] of Decimal;
        TryLevel: Decimal;
        TryTrend: Decimal;
        TrySeason: array[7] of Decimal;
        Sse: Decimal;
        BestSse: Decimal;
        Cnt: Integer;
        BestCnt: Integer;
        Start: Integer;
        I: Integer;
        A: Integer;
        G: Integer;
        T: Integer;
        W: Integer;
        Found: Boolean;
    begin
        Start := 0;
        I := 1;
        while (Start = 0) and (I <= EndIdx) do begin
            if Demand[I] > 0 then
                Start := I;
            I += 1;
        end;
        if (Start = 0) or (EndIdx - Start + 1 < 28) then
            exit(false);
        FillInvalidDays(Demand, Valid, EndIdx, Y);

        Alphas[1] := 0.05;
        Alphas[2] := 0.1;
        Alphas[3] := 0.2;
        Alphas[4] := 0.3;
        Alphas[5] := 0.5;
        Gammas[1] := 0.05;
        Gammas[2] := 0.1;
        Gammas[3] := 0.2;
        Gammas[4] := 0.3;
        for T := 0 to 1 do
            for A := 1 to 5 do
                for G := 1 to 4 do begin
                    RunHoltWinters(Y, Start, EndIdx, FirstDate, Alphas[A], Gammas[G], T * 0.1, T * 0.9, TryLevel, TryTrend, TrySeason, Sse, Cnt);
                    if (not Found) or (Sse < BestSse) then begin
                        Found := true;
                        BestSse := Sse;
                        BestCnt := Cnt;
                        Alpha := Alphas[A];
                        Gamma := Gammas[G];
                        Beta := T * 0.1;
                        Phi := T * 0.9;
                        Level := TryLevel;
                        Trend := TryTrend;
                        for W := 1 to 7 do
                            Season[W] := TrySeason[W];
                    end;
                end;
        if BestCnt > 0 then
            Sigma := Power(BestSse / BestCnt, 0.5)
        else
            Sigma := 0;
        exit(true);
    end;

    local procedure RunHoltWinters(var Y: array[500] of Decimal; Start: Integer; EndIdx: Integer; FirstDate: Date; Alpha: Decimal; Gamma: Decimal;
        Beta: Decimal; Phi: Decimal; var Level: Decimal; var Trend: Decimal; var Season: array[7] of Decimal; var Sse: Decimal; var Cnt: Integer)
    var
        WeekCount: Integer;
        Base: Decimal;
        Sum: Decimal;
        Fcst: Decimal;
        NewLevel: Decimal;
        P: Integer;
        J: Integer;
        T: Integer;
        W: Integer;
    begin
        // Khoi tao: muc nen = trung binh K tuan dau (K toi da 4), mua vu cua moi thu = trung binh thu do trong K tuan tru muc nen.
        WeekCount := (EndIdx - Start + 1) div 7;
        if WeekCount > 4 then
            WeekCount := 4;
        Sum := 0;
        for T := Start to Start + 7 * WeekCount - 1 do
            Sum += Y[T];
        Base := Sum / (7 * WeekCount);
        for P := 0 to 6 do begin
            Sum := 0;
            for J := 0 to WeekCount - 1 do
                Sum += Y[Start + P + 7 * J];
            Season[Date2DWY(FirstDate + Start + P - 1, 1)] := Sum / WeekCount - Base;
        end;
        Level := Base;
        Trend := 0;
        Sse := 0;
        Cnt := 0;
        for T := Start to EndIdx do begin
            W := Date2DWY(FirstDate + T - 1, 1);
            Fcst := Level + Phi * Trend + Season[W];
            if T >= Start + 7 then begin
                Sse += (Y[T] - Fcst) * (Y[T] - Fcst);
                Cnt += 1;
            end;
            NewLevel := Alpha * (Y[T] - Season[W]) + (1 - Alpha) * (Level + Phi * Trend);
            Trend := Beta * (NewLevel - Level) + (1 - Beta) * Phi * Trend;
            Season[W] := Gamma * (Y[T] - NewLevel) + (1 - Gamma) * Season[W];
            Level := NewLevel;
        end;
    end;

    // Ngay het hang hoac co su kien: thay bang trung binh cac ngay hop le cung thu trong 8 tuan truoc; khong co thi lay trung binh
    // 56 ngay hop le gan nhat. Neu khong, mo hinh hoc nham rang nhu cau giam (het hang) hoac tang (khuyen mai).
    local procedure FillInvalidDays(var Demand: array[500] of Decimal; var Valid: array[500] of Boolean; EndIdx: Integer; var Y: array[500] of Decimal)
    var
        Overall: Decimal;
        Sum: Decimal;
        Counted: Integer;
        I: Integer;
        S: Integer;
    begin
        I := EndIdx;
        while (I >= 1) and (Counted < 56) do begin
            if Valid[I] then begin
                Sum += Demand[I];
                Counted += 1;
            end;
            I -= 1;
        end;
        if Counted > 0 then
            Overall := Sum / Counted;
        for I := 1 to EndIdx do
            if Valid[I] then
                Y[I] := Demand[I]
            else begin
                Sum := 0;
                Counted := 0;
                S := I - 7;
                while (S >= 1) and (S >= I - 56) do begin
                    if Valid[S] then begin
                        Sum += Demand[S];
                        Counted += 1;
                    end;
                    S -= 7;
                end;
                if Counted > 0 then
                    Y[I] := Sum / Counted
                else
                    Y[I] := Overall;
            end;
    end;

    local procedure HWForecast(Level: Decimal; Trend: Decimal; var Season: array[7] of Decimal; Phi: Decimal; H: Integer; Weekday: Integer): Decimal
    var
        Damp: Decimal;
        PhiPow: Decimal;
        K: Integer;
        Value: Decimal;
    begin
        PhiPow := 1;
        for K := 1 to H do begin
            PhiPow := PhiPow * Phi;
            Damp += PhiPow;
        end;
        Value := Level + Damp * Trend + Season[Weekday];
        if Value < 0 then
            exit(0);
        exit(Value);
    end;

    local procedure TrendText(Beta: Decimal): Text
    begin
        if Beta = 0 then
            exit(NoTrendTxt);
        exit(DampedTxt);
    end;

    // Ghi du bao vao bang chuan cua LS. Xoa du bao cu tu ngay mai tro di cua cap nay truoc, de LS khong doc lan so cu.
    // Khoang Lower/Upper la +-1,2816 lan do lech sai so mot buoc (khoang 80%); LS dung Upper khi bat Safety Stock Calculation.
    local procedure PublishLSForecast(ItemNo: Code[20]; LocationCode: Code[10]; AsOf: Date; Level: Decimal; Trend: Decimal;
        var Season: array[7] of Decimal; Phi: Decimal; Sigma: Decimal; HWWape: Decimal)
    var
        Entry: Record "LSC Forecast Entry";
        H: Integer;
        Qty: Decimal;
        Quality: Decimal;
    begin
        Entry.SetRange("Item No.", ItemNo);
        Entry.SetRange("Variant Code", '');
        Entry.SetRange("Location Code", LocationCode);
        Entry.SetFilter(Date, '>%1', AsOf);
        Entry.DeleteAll();
        Quality := 100 - HWWape;
        if Quality < 0 then
            Quality := 0;
        for H := 1 to Setup.EffForecastHorizon() do begin
            Qty := HWForecast(Level, Trend, Season, Phi, H, Date2DWY(AsOf + H, 1));
            Entry.Init();
            Entry."Item No." := ItemNo;
            Entry."Variant Code" := '';
            Entry."Location Code" := LocationCode;
            Entry.Date := AsOf + H;
            Entry."Forecast Quantity" := Round(Qty, 0.01);
            Entry."Forecast Quantity (Lower)" := Round(MaxOf(0, Qty - 1.2816 * Sigma), 0.01);
            Entry."Forecast Quantity (Upper)" := Round(Qty + 1.2816 * Sigma, 0.01);
            Entry."Forecast Quality %" := Round(Quality, 0.1);
            Entry.Insert();
            EntriesWritten += 1;
        end;
    end;

    local procedure MaxOf(A: Decimal; B: Decimal): Decimal
    begin
        if A > B then
            exit(A);
        exit(B);
    end;

    local procedure WriteMethod(Profile: Record "NWV Demand Profile Buffer" temporary; Item: Record Item; Method: Code[10];
        var Demand: array[500] of Decimal; var Censored: array[500] of Boolean; var Excluded: array[500] of Boolean;
        TrainEnd: Integer; N: Integer; FirstDate: Date; AsOf: Date; HoldoutFrom: Date; RunAt: DateTime;
        var Fc: array[100] of Decimal; Params: Text): Decimal
    var
        Acc: Record "NWV Forecast Accuracy";
        Daily: Record "NWV Forecast Daily";
        I: Integer;
        H: Integer;
        D: Date;
        FcSum: Decimal;
    begin
        Acc.Init();
        Acc."Item No." := Profile."Item No.";
        Acc."Location Code" := Profile."Location Code";
        Acc.Method := Method;
        Acc."Item Description" := Item.Description;
        Acc."Item Category Code" := Item."Item Category Code";
        if Profile.Basis = Profile.Basis::Sale then
            Acc."Demand Basis" := Acc."Demand Basis"::Sale
        else
            Acc."Demand Basis" := Acc."Demand Basis"::Outflow;
        Acc."Holdout From" := HoldoutFrom;
        Acc."Holdout To" := AsOf;
        Acc."As Of Date" := AsOf;
        Acc."Calculated At" := RunAt;
        Acc."Model Parameters" := CopyStr(Params, 1, MaxStrLen(Acc."Model Parameters"));

        for I := TrainEnd + 1 to N do begin
            H := I - TrainEnd;
            D := FirstDate + I - 1;
            FcSum += Fc[H];
            Daily.Init();
            Daily."Item No." := Profile."Item No.";
            Daily."Location Code" := Profile."Location Code";
            Daily.Method := Method;
            Daily."Date" := D;
            Daily."Actual Qty" := Demand[I];
            Daily."Forecast Qty" := Round(Fc[H], 0.001);
            Daily.Censored := Censored[I];
            Daily.Excluded := Excluded[I];
            Daily.Insert();
            if Censored[I] then
                Acc."Days Censored" += 1
            else
                if Excluded[I] then
                    Acc."Days Excluded" += 1
                else begin
                    Acc."Days Evaluated" += 1;
                    Acc."Actual Qty" += Demand[I];
                    Acc."Forecast Qty" += Fc[H];
                    Acc."Abs Error Qty" += Abs(Demand[I] - Fc[H]);
                end;
        end;
        if N > TrainEnd then
            Acc."Daily Level" := Round(FcSum / (N - TrainEnd), 0.001);
        Acc."Actual Qty" := Round(Acc."Actual Qty", 0.001);
        Acc."Forecast Qty" := Round(Acc."Forecast Qty", 0.001);
        Acc."Abs Error Qty" := Round(Acc."Abs Error Qty", 0.001);
        if Acc."Actual Qty" > 0 then begin
            Acc."WAPE %" := Round(Acc."Abs Error Qty" / Acc."Actual Qty" * 100, 0.1);
            Acc."Bias %" := Round((Acc."Forecast Qty" - Acc."Actual Qty") / Acc."Actual Qty" * 100, 0.1);
        end;
        SetException(Acc);
        Acc.Insert();
        exit(Acc."WAPE %");
    end;

    local procedure SetException(var Acc: Record "NWV Forecast Accuracy")
    var
        Reason: Text;
    begin
        if (Acc."Actual Qty" <= 0) or (Acc."Actual Qty" < Setup.EffMinActual()) then
            exit;
        if Acc."WAPE %" > Setup.EffWapeWarn() then
            Reason := StrSubstNo(HighWapeTxt, Format(Acc."WAPE %", 0, 9), Format(Setup.EffWapeWarn(), 0, 9));
        if Abs(Acc."Bias %") > Setup.EffBiasWarn() then begin
            if Reason <> '' then
                Reason += ' ';
            if Acc."Bias %" > 0 then
                Reason += StrSubstNo(OverTxt, Format(Acc."Bias %", 0, 9))
            else
                Reason += StrSubstNo(UnderTxt, Format(-Acc."Bias %", 0, 9));
        end;
        if Reason <> '' then begin
            Acc."Is Exception" := true;
            Acc."Exception Reason" := CopyStr(Reason, 1, MaxStrLen(Acc."Exception Reason"));
        end;
    end;

    // Doc san ngay su kien vao bo nho mot lan: moi cap x moi ngay ma hoi CSDL thi 74 cap x 470 ngay la hon 60 nghin lenh doc.
    local procedure LoadExceptionDays(FromDate: Date; ToDate: Date)
    var
        Planned: Record "LSC Replen. Planned Sales Dem.";
        Exc: Record "NWV Demand Exception";
    begin
        Clear(ExceptionDays);
        Planned.SetRange(Date, FromDate, ToDate);
        Planned.SetRange(Status, Planned.Status::Enabled);
        Planned.SetFilter("Planned Demand Type", '<>%1', Planned."Planned Demand Type"::" ");
        Planned.SetRange("Variant Code", '');
        if Planned.FindSet() then
            repeat
                AddExceptionDay(Planned."Item No.", Planned."Location Code", Planned.Date);
            until Planned.Next() = 0;
        if Exc.FindSet() then
            repeat
                AddExceptionRange(Exc, FromDate, ToDate);
            until Exc.Next() = 0;
    end;

    local procedure AddExceptionRange(Exc: Record "NWV Demand Exception"; FromDate: Date; ToDate: Date)
    var
        D: Date;
    begin
        D := Exc."From Date";
        if D < FromDate then
            D := FromDate;
        while (D <= Exc."To Date") and (D <= ToDate) do begin
            AddExceptionDay(Exc."Item No.", Exc."Location Code", D);
            D += 1;
        end;
    end;

    local procedure AddExceptionDay(ItemNo: Code[20]; LocationCode: Code[10]; D: Date)
    var
        KeyText: Text;
    begin
        KeyText := ItemNo + '|' + LocationCode + '|' + Format(D, 0, 9);
        if not ExceptionDays.ContainsKey(KeyText) then
            ExceptionDays.Add(KeyText, true);
    end;

    // Mat hang hoac dia diem de trong trong NWV Demand Exception nghia la ap cho moi mat hang, moi dia diem.
    local procedure IsExceptionDay(ItemNo: Code[20]; LocationCode: Code[10]; D: Date): Boolean
    var
        DayText: Text;
    begin
        DayText := Format(D, 0, 9);
        exit(ExceptionDays.ContainsKey(ItemNo + '|' + LocationCode + '|' + DayText) or
             ExceptionDays.ContainsKey('|' + LocationCode + '|' + DayText) or
             ExceptionDays.ContainsKey(ItemNo + '||' + DayText) or
             ExceptionDays.ContainsKey('||' + DayText));
    end;
}
