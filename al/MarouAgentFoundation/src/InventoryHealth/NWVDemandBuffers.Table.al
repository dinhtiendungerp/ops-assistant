/// <summary>
/// Ba bang tam cho codeunit NWV Demand Calc. Chi song trong bo nho, khong ghi xuong SQL,
/// nen khong can quyen tabledata.
/// </summary>
table 70110 "NWV Daily Move Buffer"
{
    Caption = 'NWV Daily Move Buffer';
    TableType = Temporary;

    fields
    {
        field(1; "Item No."; Code[20]) { Caption = 'Item No.'; }
        field(2; "Location Code"; Code[10]) { Caption = 'Location Code'; }
        field(3; "Posting Date"; Date) { Caption = 'Posting Date'; }
        field(10; "Move Qty"; Decimal)
        {
            Caption = 'Move Qty';
            DecimalPlaces = 0 : 5;
            ToolTip = 'Tong Quantity co dau cua moi Item Ledger Entry trong ngay, moi loai.';
        }
        field(11; "Sale Qty"; Decimal)
        {
            Caption = 'Sale Qty';
            DecimalPlaces = 0 : 5;
            ToolTip = 'Tong luong ban trong ngay, chi dong Sale co Quantity am, lay tri tuyet doi.';
        }
        field(12; "Out Qty"; Decimal)
        {
            Caption = 'Out Qty';
            DecimalPlaces = 0 : 5;
            ToolTip = 'Tong luong xuat trong ngay: Sale, Negative Adjmt., Transfer, Consumption, Output.';
        }
    }

    keys
    {
        key(PK; "Item No.", "Location Code", "Posting Date") { Clustered = true; }
    }
}

table 70111 "NWV Demand Profile Buffer"
{
    Caption = 'NWV Demand Profile Buffer';
    TableType = Temporary;

    fields
    {
        field(1; "Item No."; Code[20]) { Caption = 'Item No.'; }
        field(2; "Location Code"; Code[10]) { Caption = 'Location Code'; }
        field(10; "Has Sale"; Boolean)
        {
            Caption = 'Has Sale';
            ToolTip = 'Dia diem nay co it nhat mot dong Sale trong toan bo lich su.';
        }
        field(11; Basis; Option)
        {
            Caption = 'Basis';
            OptionMembers = Sale,Outflow;
            OptionCaption = 'Sale,Outflow';
            ToolTip = 'Nhu cau tinh tren dong Sale, hay tren tong luong xuat neu dia diem khong he ban.';
        }
        field(12; "Total Qty"; Decimal) { Caption = 'Total Qty'; DecimalPlaces = 0 : 3; }
        field(13; "Days Counted"; Integer) { Caption = 'Days Counted'; }
        field(14; "Days Censored"; Integer)
        {
            Caption = 'Days Censored';
            ToolTip = 'So ngay trong cua so khong con hang va cung khong ban duoc gi. Bi loai khoi mau so.';
        }
        field(15; "Last Sale Date"; Date) { Caption = 'Last Sale Date'; }
        field(16; "Avg Daily"; Decimal) { Caption = 'Avg Daily'; DecimalPlaces = 0 : 4; }
    }

    keys
    {
        key(PK; "Item No.", "Location Code") { Clustered = true; }
    }
}

table 70112 "NWV Shelf Life Buffer"
{
    Caption = 'NWV Shelf Life Buffer';
    TableType = Temporary;

    fields
    {
        field(1; "Item No."; Code[20]) { Caption = 'Item No.'; }
        field(2; "Span Days"; Integer) { Caption = 'Span Days'; }
        field(3; "Entry No."; Integer) { Caption = 'Entry No.'; }
    }

    keys
    {
        key(PK; "Item No.", "Span Days", "Entry No.") { Clustered = true; }
    }
}
