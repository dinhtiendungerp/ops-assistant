/// <summary>
/// Permission set gan cho Entra application dung S2S. Chi doc, khong ghi.
/// Khong bao gio gan SUPER cho app tich hop.
/// </summary>
permissionset 70209 "NWV Marou Data API"
{
    Assignable = true;
    Caption = 'NWV Marou Data API';

    Permissions =
        tabledata Item = R,
        tabledata "Item Ledger Entry" = R,
        tabledata "Lot No. Information" = R,
        tabledata "Stockkeeping Unit" = R,
        tabledata Location = R,
        tabledata "Item Category" = R,
        tabledata "Purchase Line" = R,
        tabledata "Sales Line" = R,
        tabledata "Value Entry" = R,
        page "NWV Item API" = X,
        page "NWV Item Ledger Entry API" = X,
        page "NWV Lot No. Information API" = X,
        page "NWV Stockkeeping Unit API" = X,
        page "NWV Location API" = X,
        page "NWV Item Category API" = X,
        page "NWV Purchase Order Line API" = X,
        page "NWV Sales Order Line API" = X,
        page "NWV Value Entry API" = X;
}
