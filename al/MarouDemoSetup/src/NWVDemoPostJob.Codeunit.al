/// <summary>
/// Chay post batch NWVDEMO khong co giao dien. Dat lam Object ID to Run cua mot Job Queue Entry
/// neu muon post chay nen thay vi ngoi doi trong trinh duyet.
/// </summary>
codeunit 70251 "NWV Demo Post Job"
{
    trigger OnRun()
    var
        DemoSetup: Codeunit "NWV Demo Setup Mgt";
    begin
        DemoSetup.PostAllByMonthNoDialog();
    end;
}
