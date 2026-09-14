/// <summary>
/// Chay lop tinh toan AL qua S2S (ODataV4 `NWVAgentCalcService`), giong nut Run Inventory Health va
/// Run Store Replenishment tren page, nhung truyen duoc Work Date. Phien web service khong co Work Date cua
/// nguoi dung, ma lop AL tinh theo WorkDate(), nen hom demo phai truyen ngay neo 18/09/2026.
/// </summary>
codeunit 70278 "NWV Agent Calc Service"
{
    /// <summary>Bat tat viec ghi du bao Holt-Winters vao LSC Forecast Entry, va so ngay du bao. Tra ve gia tri sau khi doi.</summary>
    procedure SetForecastPublishing(publish: Boolean; horizonDays: Integer): Text
    var
        Setup: Record "NWV Agent Setup";
        Result: JsonObject;
        Output: Text;
    begin
        Setup.GetRecordOnce();
        Setup."Publish LS Forecast" := publish;
        if horizonDays > 0 then
            Setup."Forecast Horizon Days" := horizonDays;
        Setup.Modify();
        Result.Add('publishLSForecast', Setup."Publish LS Forecast");
        Result.Add('forecastHorizonDays', Setup.EffForecastHorizon());
        Result.WriteTo(Output);
        exit(Output);
    end;

    procedure RunCalculations(param: Text; workDateText: Text): Text
    var
        InvHealth: Codeunit "NWV Inv. Health Calc";
        DiscGov: Codeunit "NWV Discount Gov. Calc";
        Forecast: Codeunit "NWV Forecast Accuracy Calc";
        Scorecard: Codeunit "NWV Supplier Scorecard Calc";
        ForecastAcc: Record "NWV Forecast Accuracy";
        SupplierCard: Record "NWV Supplier Scorecard";
        HealthLine: Record "NWV Inv. Health Line";
        Tiers: JsonObject;
        Result: JsonObject;
        NewDate: Date;
        Tier: Enum "NWV Inv. Health Tier";
        Output: Text;
    begin
        if workDateText <> '' then begin
            Evaluate(NewDate, workDateText, 9);
            WorkDate(NewDate);
        end;
        param := UpperCase(param);
        if param = '' then
            param := 'ALL';
        if param in ['ALL', 'INVHEALTH'] then
            InvHealth.CalculateAll();
        if param in ['ALL', 'DISCGOV'] then
            DiscGov.CalculateAll();
        if param in ['ALL', 'FORECAST'] then
            Forecast.CalculateAll();
        if param in ['ALL', 'SUPPLIER'] then
            Scorecard.CalculateAll();

        foreach Tier in Enum::"NWV Inv. Health Tier".Ordinals() do begin
            HealthLine.SetRange(Tier, Tier);
            Tiers.Add(Format(Tier), HealthLine.Count());
        end;
        HealthLine.SetRange(Tier);
        Result.Add('workDate', Format(WorkDate(), 0, 9));
        Result.Add('inventoryHealthLines', HealthLine.Count());
        Result.Add('tiers', Tiers);
        Result.Add('forecastAccuracyRows', ForecastAcc.Count());
        ForecastAcc.SetRange("Is Exception", true);
        Result.Add('forecastExceptions', ForecastAcc.Count());
        Result.Add('supplierScorecardRows', SupplierCard.Count());
        if param in ['ALL', 'FORECAST'] then
            Result.Add('lsForecastEntriesWritten', Forecast.LSForecastEntriesWritten());
        Result.WriteTo(Output);
        exit(Output);
    end;
}
