/// <summary>
/// Chay tu Job Queue hang dem (Object Type = Codeunit, Object ID = 70105).
/// Parameter String: INVHEALTH | DISCGOV | FORECAST | SUPPLIER | ALL (mac dinh ALL).
/// Thu tu: inventory health -> discount governance. De xuat bo sung cua hang do LS Replenishment tinh (Scheduler
/// Job cua LS hoac NWVReplenService.CalculateJournal); NWV Replenishment Calc da xoa o 1.2.0.0.
/// </summary>
codeunit 70105 "NWV Agent Job Runner"
{
    TableNo = "Job Queue Entry";

    trigger OnRun()
    var
        InvHealth: Codeunit "NWV Inv. Health Calc";
        DiscGov: Codeunit "NWV Discount Gov. Calc";
        Forecast: Codeunit "NWV Forecast Accuracy Calc";
        Scorecard: Codeunit "NWV Supplier Scorecard Calc";
        Param: Text;
    begin
        Param := UpperCase(Rec."Parameter String");
        if Param = '' then
            Param := 'ALL';

        if Param in ['ALL', 'INVHEALTH'] then
            InvHealth.CalculateAll();
        if Param in ['ALL', 'DISCGOV'] then
            DiscGov.CalculateAll();
        if Param in ['ALL', 'FORECAST'] then
            Forecast.CalculateAll();
        if Param in ['ALL', 'SUPPLIER'] then
            Scorecard.CalculateAll();
    end;
}
