permissionset 70050 "NWV DATA READINESS"
{
    Assignable = true;
    Caption = 'NWV Data Readiness';

    Permissions =
        table "NWV Data Readiness Line" = X,
        tabledata "NWV Data Readiness Line" = RIMD,
        codeunit "NWV Data Readiness Calc" = X,
        page "NWV Data Readiness" = X,
        tabledata Item = R,
        tabledata "Item Ledger Entry" = R,
        tabledata Location = R,
        tabledata "Stockkeeping Unit" = R,
        tabledata "Transfer Route" = R;
}
