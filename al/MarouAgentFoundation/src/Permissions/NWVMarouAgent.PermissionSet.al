/// <summary>
/// Hai permission set tach vai tro:
///   NWV AGENT RUN  : gan cho Entra app cua agent. Doc so da tinh, ghi de xuat, doi status exception. KHONG duyet, KHONG post.
///   NWV AGENT REVIEW: gan cho nguoi duyet (Supply Chain / Retail Ops). Duyet de xuat, chay lai tinh toan, doi setup.
/// Nguyen tac: agent khong bao gio co quyen tren Transfer Header/Line hay Item Journal.
/// Transfer Order do codeunit tao khi NGUOI duyet, chay duoi quyen cua nguoi duyet.
/// </summary>
permissionset 70100 "NWV AGENT RUN"
{
    Caption = 'NWV Agent - Run (API)';
    Assignable = true;

    Permissions =
        tabledata "NWV Agent Setup" = R,
        tabledata "NWV Inv. Health Line" = R,
        tabledata "NWV Discount Exception" = RM,
        tabledata "NWV Agent Proposal" = RIM,
        tabledata "NWV POS Discount Log" = R,
        tabledata "NWV Category Threshold" = R,
        tabledata "NWV Demand Exception" = RI,
        tabledata "NWV Forecast Accuracy" = R,
        tabledata "NWV Forecast Daily" = R,
        tabledata "NWV Supplier Scorecard" = R,
        tabledata "Purch. Rcpt. Line" = R,
        tabledata "Purchase Line" = R,
        tabledata "Item Ledger Entry" = R,
        tabledata "Item Journal Line" = R,
        tabledata Item = R,
        tabledata Location = R,
        tabledata "Item Category" = R,
        page "NWV Item Journal Line API" = X,
        page "NWV Inv. Health API" = X,
        page "NWV Discount Exception API" = X,
        page "NWV Agent Proposal API" = X,
        page "NWV POS Discount Log API" = X,
        page "NWV Item Ledger Entry API" = X,
        page "NWV Demand Exception API" = X,
        page "NWV Forecast Accuracy API" = X,
        page "NWV Forecast Daily API" = X,
        page "NWV Supplier Scorecard API" = X,
        page "NWV Purch. Rcpt. Line API" = X;
}

permissionset 70101 "NWV AGENT REVIEW"
{
    Caption = 'NWV Agent - Reviewer';
    Assignable = true;

    Permissions =
        tabledata "NWV Agent Setup" = RIMD,
        tabledata "NWV Inv. Health Line" = RIMD,
        tabledata "NWV Discount Exception" = RIMD,
        tabledata "NWV Agent Proposal" = RIMD,
        tabledata "NWV POS Discount Log" = RIMD,
        tabledata "NWV Category Threshold" = RIMD,
        tabledata "NWV Demand Exception" = RIMD,
        tabledata "NWV Forecast Accuracy" = RIMD,
        tabledata "NWV Forecast Daily" = RIMD,
        tabledata "LSC Forecast Entry" = RIMD,
        tabledata "LSC Replen. Planned Sales Dem." = R,
        tabledata "NWV Supplier Scorecard" = RIMD,
        tabledata "Purch. Rcpt. Line" = R,
        // Duyet de xuat Purchase (Dakao mua thang tu Marou) tao Purchase Order Open, nhu Transfer Order voi de xuat Transfer.
        tabledata "Purchase Header" = RIM,
        tabledata "Purchase Line" = RIM,
        tabledata "Transfer Header" = RIM,
        tabledata "Transfer Line" = RIM,
        // Duyet de xuat Write-off tao dong Item Journal CHUA POST (UC2 G2/A3). Khong co quyen post: codeunit post khong nam trong set nay.
        tabledata "Item Journal Line" = RIM,
        tabledata "Item Journal Batch" = RIM,
        tabledata "Item Journal Template" = RI,
        tabledata "Reason Code" = RI,
        tabledata "Item Ledger Entry" = R,
        page "NWV Item Journal Line API" = X,
        page "NWV Agent Setup" = X,
        page "NWV Agent Proposals" = X,
        page "NWV Inv. Health Lines" = X,
        page "NWV Discount Exceptions" = X,
        page "NWV Category Thresholds" = X,
        page "NWV Demand Exceptions" = X,
        page "NWV Forecast Accuracy" = X,
        page "NWV Forecast Daily" = X,
        page "NWV Supplier Scorecard" = X,
        page "NWV Agent Proposal API" = X,
        page "NWV Discount Exception API" = X,
        codeunit "NWV Inv. Health Calc" = X,
        codeunit "NWV Discount Gov. Calc" = X,
        codeunit "NWV Forecast Accuracy Calc" = X,
        codeunit "NWV Supplier Scorecard Calc" = X,
        codeunit "NWV Agent Proposal Mgt." = X,
        codeunit "NWV Agent Job Runner" = X,
        codeunit "NWV Agent Calc Service" = X;
}
