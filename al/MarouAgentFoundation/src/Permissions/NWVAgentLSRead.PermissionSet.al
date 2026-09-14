/// <summary>
/// Hai permission set cho phan LS Replenishment, gan THEM cho Entra app cua tro ly ben canh NWV AGENT RUN.
///   NWV AGENT LS READ : doc ket qua tinh qua API page va doc master data qua NWVReplenService.ReadTable.
///   NWV AGENT LS CALC : chay tinh (Calc. Item Qty, Upd Out of Stock, Add Items to Replen. Jrnl.).
///                       Tinh cua LS ghi vao hang chuc bang cua LS nen lay nguyen LSCentralPermissions.
///                       Chi gan tren sandbox demo hoac cho vai tro van hanh; khong gan cho tro ly tren he thong that.
/// Doc bang LS co the keo them bang LS hoac bang add-on khac (xem CLAUDE.md, bang 10000788, 10000700, 6181271).
/// Neu BC tra 403 kem so bang thi them bang do vao permission set tenant NWVMAROULSC.
/// </summary>
permissionset 70270 "NWV AGENT LS READ"
{
    Caption = 'NWV Agent - LS Replenishment Read';
    Assignable = true;

    Permissions =
        tabledata "LSC Replen. Item Quantity" = R,
        tabledata "LSC Replen. Template" = R,
        tabledata "LSC Replen. Journal Batch" = R,
        tabledata "LSC Replen. Journal Lines" = R,
        tabledata "LSC Replen. Jrnl. Details" = R,
        tabledata "LSC Replen. Setup" = R,
        tabledata "LSC Replen. Data Profile" = R,
        tabledata "LSC Replen. Data Prof. Links" = R,
        tabledata "LSC Replen. Sales Profile" = R,
        tabledata "LSC Replen. Sales Profile Line" = R,
        tabledata "LSC Replen. Item Store Rec" = R,
        tabledata "LSC Replen. Loc. Item Grades" = R,
        tabledata "LSC Replen. Grade" = R,
        tabledata "LSC Replen. From Warehouse" = R,
        tabledata "LSC Replen. Out of Stock Log" = R,
        tabledata "LSC Replen. Calc. Log Lines V2" = R,
        tabledata "LSC Item Distribution" = R,
        tabledata "LSC Forecast Entry" = R,
        tabledata "LSC Replen. Planned Sales Dem." = R,
        tabledata "LSC Replen. Planned Event" = R,
        tabledata "LSC Periodic Discount" = R,
        tabledata "LSC Periodic Discount Line" = R,
        tabledata "LSC Validation Period" = R,
        tabledata "LSC Store Price Group" = R,
        tabledata "LSC Store" = R,
        tabledata "LSC Store Group" = R,
        tabledata Item = R,
        tabledata Location = R,
        tabledata "Stockkeeping Unit" = R,
        page "NWV Replen. Item Qty API" = X,
        page "NWV Replen. Template API" = X,
        page "NWV Replen. Jnl. Batch API" = X,
        page "NWV Replen. Jnl. Line API" = X,
        page "NWV Replen. Jnl. Detail API" = X,
        page "NWV Replen. Calc. Log API" = X,
        page "NWV Replen. Item Param. API" = X,
        page "NWV Replen. Sales Prof. API" = X,
        page "NWV LS Forecast Entry API" = X,
        page "NWV Planned Sales Demand API" = X,
        page "NWV LS Periodic Discount API" = X,
        page "NWV LS Periodic Disc. Line API" = X,
        page "NWV LS Store Price Group API" = X,
        page "NWV LS Planned Event API" = X,
        page "NWV LS Validation Period API" = X,
        codeunit "NWV Replen. Service" = X;
}

permissionset 70271 "NWV AGENT LS CALC"
{
    Caption = 'NWV Agent - LS Replenishment Calculate';
    Assignable = true;
    IncludedPermissionSets = "NWV AGENT LS READ", LSCentralPermissions;

    Permissions =
        tabledata "Item Ledger Entry" = R,
        tabledata "Purchase Line" = R,
        tabledata "Sales Line" = R,
        tabledata "Transfer Line" = R,
        tabledata "Item Variant" = R,
        tabledata Vendor = R,
        tabledata "Job Queue Entry" = RIMD;
}
