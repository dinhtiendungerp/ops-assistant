/// <summary>
/// Danh cho nguoi nap du lieu demo tren sandbox. Co quyen ghi, khong gan cho Entra app
/// dung S2S. Extension doc du lieu la NWV Marou Data API, permission set cua no chi doc.
/// </summary>
permissionset 70252 "NWV Marou Demo Setup"
{
    Assignable = true;
    Caption = 'NWV Marou Demo Setup';

    Permissions =
        tabledata "Item Journal Template" = RIMD,
        tabledata "Item Journal Batch" = RIMD,
        tabledata "Item Journal Line" = RIMD,
        tabledata "Lot No. Information" = RIMD,
        tabledata "General Ledger Setup" = RM,
        tabledata "User Setup" = RM,
        tabledata "Item Ledger Entry" = R,
        codeunit "NWV Demo Setup Mgt" = X,
        codeunit "NWV Demo Post Job" = X,
        codeunit "NWV Demo LS Replen. Setup" = X,
        codeunit "NWV Demo Repost" = X,
        codeunit "NWV Demo Supplier Data" = X,
        tabledata "Item Variant" = RD,
        tabledata Location = RM,
        tabledata Item = RM,
        tabledata "LSC Replen. From Warehouse" = RIM,
        tabledata "LSC Item Distribution" = RIM,
        tabledata "LSC Replen. Template" = RIM,
        tabledata "LSC Replen. Journal Batch" = RIM,
        tabledata "LSC Replen. Out of Stock Log" = RD,
        tabledata "LSC Replen. Last Entr for OOS" = RD,
        page "NWV Marou Demo Setup" = X;
}
