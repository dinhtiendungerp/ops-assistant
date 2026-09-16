/// <summary>
/// Moi hanh dong agent muon lam deu di qua bang nay: agent ghi de xuat (Status = Proposed),
/// nguoi duyet tren page NWV Agent Proposals, luc do he thong moi tao chung tu that (Transfer Order...).
/// Day la ranh gioi human-in-the-loop, khong co duong tat cho agent ghi thang vao chung tu.
/// </summary>
table 70102 "NWV Agent Proposal"
{
    Caption = 'NWV Agent Proposal';
    DataClassification = CustomerContent;

    fields
    {
        field(1; "Entry No."; Integer)
        {
            Caption = 'Entry No.';
            AutoIncrement = true;
        }
        field(2; "Proposal Id"; Guid)
        {
            Caption = 'Proposal Id';
        }
        field(3; Scenario; Enum "NWV Agent Scenario") { Caption = 'Scenario'; }
        field(4; "Action Type"; Enum "NWV Proposal Action") { Caption = 'Action Type'; }
        field(5; Status; Enum "NWV Proposal Status") { Caption = 'Status'; }
        field(10; "Item No."; Code[20])
        {
            Caption = 'Item No.';
            TableRelation = Item;
        }
        field(11; "Lot No."; Code[50]) { Caption = 'Lot No.'; }
        field(12; "From Location Code"; Code[10])
        {
            Caption = 'From Location Code';
            TableRelation = Location;
        }
        field(13; "To Location Code"; Code[10])
        {
            Caption = 'To Location Code';
            TableRelation = Location;
        }
        field(14; Quantity; Decimal)
        {
            Caption = 'Quantity';
            DecimalPlaces = 0 : 5;
        }
        field(16; "Vendor No."; Code[20])
        {
            Caption = 'Vendor No.';
            TableRelation = Vendor;
            ToolTip = 'Vendor for a Purchase proposal (Dakao buys directly from Marou). Empty for other action types.';
        }
        field(15; "Reference Key"; Text[100])
        {
            Caption = 'Reference Key';
            ToolTip = 'Khoa cua dong nguon: Item|Location|Lot voi inventory health, Store|Staff|Date voi discount governance.';
        }
        field(20; Rationale; Text[2048])
        {
            Caption = 'Rationale';
            ToolTip = 'Ly do agent viet, dua tren so lieu da tinh. Nguoi duyet doc cai nay.';
        }
        field(21; "Evidence JSON"; Blob)
        {
            Caption = 'Evidence JSON';
            ToolTip = 'So lieu agent da doc khi ra de xuat, de audit lai sau nay.';
        }
        field(22; "Priority Score"; Integer) { Caption = 'Priority Score'; }
        field(30; "Created By Agent"; Code[50]) { Caption = 'Created By Agent'; }
        field(31; "Created At"; DateTime) { Caption = 'Created At'; }
        field(32; "Model Name"; Text[50]) { Caption = 'Model Name'; }
        field(33; "Run Id"; Text[50]) { Caption = 'Run Id'; }
        field(40; "Reviewed By"; Code[50]) { Caption = 'Reviewed By'; }
        field(41; "Reviewed At"; DateTime) { Caption = 'Reviewed At'; }
        field(42; "Review Comment"; Text[250]) { Caption = 'Review Comment'; }
        field(50; "Result Document Type"; Text[30]) { Caption = 'Result Document Type'; }
        field(51; "Result Document No."; Code[20]) { Caption = 'Result Document No.'; }
    }

    keys
    {
        key(PK; "Entry No.") { Clustered = true; }
        key(Id; "Proposal Id") { Unique = true; }
        key(Status; Scenario, Status, "Priority Score") { }
    }

    trigger OnInsert()
    begin
        if IsNullGuid("Proposal Id") then
            "Proposal Id" := CreateGuid();
        if "Created At" = 0DT then
            "Created At" := CurrentDateTime();
        if "Created By Agent" = '' then
            "Created By Agent" := CopyStr(UserId(), 1, MaxStrLen("Created By Agent"));
    end;

    procedure SetEvidence(EvidenceText: Text)
    var
        OutStr: OutStream;
    begin
        Clear("Evidence JSON");
        "Evidence JSON".CreateOutStream(OutStr, TextEncoding::UTF8);
        OutStr.WriteText(EvidenceText);
    end;

    procedure GetEvidence(): Text
    var
        InStr: InStream;
        Result: Text;
    begin
        CalcFields("Evidence JSON");
        if not "Evidence JSON".HasValue() then
            exit('');
        "Evidence JSON".CreateInStream(InStr, TextEncoding::UTF8);
        InStr.ReadText(Result);
        exit(Result);
    end;
}

enum 70102 "NWV Agent Scenario"
{
    Extensible = true;
    value(0; InventoryHealth) { Caption = 'Inventory Health'; }
    value(1; StoreReplenishment) { Caption = 'Store Replenishment'; }
    value(2; DiscountGovernance) { Caption = 'Discount Governance'; }
}

enum 70103 "NWV Proposal Action"
{
    Extensible = true;
    value(0; ReviewOnly) { Caption = 'Review Only'; }
    value(1; "Transfer") { Caption = 'Transfer'; }
    value(2; "Markdown") { Caption = 'Markdown'; }
    value(3; BlockPurchase) { Caption = 'Block Purchase'; }
    value(4; WriteOff) { Caption = 'Write-off'; }
    value(5; AuditNote) { Caption = 'Audit Note'; }
    value(6; "Escalate") { Caption = 'Escalate'; }
    value(7; AdjustParameter) { Caption = 'Adjust Parameter'; }
    // 15/09/2026: Dakao mua thang tu Marou (vendor MAROU), giao toi cua hang. Duyet thi tao Purchase Order trang thai Open.
    value(8; "Purchase") { Caption = 'Purchase'; }
}

enum 70104 "NWV Proposal Status"
{
    Extensible = true;
    value(0; Proposed) { Caption = 'Proposed'; }
    value(1; Approved) { Caption = 'Approved'; }
    value(2; Rejected) { Caption = 'Rejected'; }
    value(3; Executed) { Caption = 'Executed'; }
    value(4; Failed) { Caption = 'Failed'; }
}
