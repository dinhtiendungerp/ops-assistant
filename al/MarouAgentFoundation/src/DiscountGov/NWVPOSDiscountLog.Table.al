/// <summary>
/// Log discount tai POS, mot dong = mot dong ban co discount. Bang trung gian, khong phu thuoc LS Central.
/// Duoc nap boi app NWV Marou Agent LS Adapter (doc Trans. Sales Entry cua LS Central),
/// hoac boi Python (mock) trong POC. Tach nhu vay de Foundation compile duoc tren BC standard.
/// </summary>
table 70104 "NWV POS Discount Log"
{
    Caption = 'NWV POS Discount Log';
    DataClassification = CustomerContent;

    fields
    {
        field(1; "Entry No."; Integer)
        {
            Caption = 'Entry No.';
            AutoIncrement = true;
        }
        field(2; "Store No."; Code[10]) { Caption = 'Store No.'; }
        field(3; "POS Terminal No."; Code[10]) { Caption = 'POS Terminal No.'; }
        field(4; "Transaction No."; Integer) { Caption = 'Transaction No.'; }
        field(5; "Line No."; Integer) { Caption = 'Line No.'; }
        field(6; "Receipt No."; Code[20]) { Caption = 'Receipt No.'; }
        field(10; "Trans. Date"; Date) { Caption = 'Transaction Date'; }
        field(11; "Trans. Time"; Time) { Caption = 'Transaction Time'; }
        field(12; "Staff ID"; Code[20]) { Caption = 'Staff ID'; }
        field(13; "Item No."; Code[20]) { Caption = 'Item No.'; }
        field(14; Quantity; Decimal) { Caption = 'Quantity'; DecimalPlaces = 0 : 5; }
        field(15; "Gross Amount"; Decimal) { Caption = 'Gross Amount'; }
        field(16; "Discount Amount"; Decimal) { Caption = 'Discount Amount'; }
        field(17; "Discount %"; Decimal) { Caption = 'Discount %'; DecimalPlaces = 0 : 2; }
        field(18; "Discount Type"; Enum "NWV POS Discount Type") { Caption = 'Discount Type'; }
        field(19; "Offer No."; Code[20]) { Caption = 'Offer No.'; }
        field(20; "Manager Override"; Boolean) { Caption = 'Manager Override'; }
        field(21; "Infocode Reason"; Code[20]) { Caption = 'Infocode Reason'; }
        field(22; "Member Card No."; Code[50]) { Caption = 'Member Card No.'; }
        field(30; "Source System"; Code[20]) { Caption = 'Source System'; }
        field(31; "Source Entry Key"; Text[100])
        {
            Caption = 'Source Entry Key';
            ToolTip = 'Khoa dong nguon o LS Central de truy nguoc: Store|Terminal|TransNo|LineNo.';
        }
    }

    keys
    {
        key(PK; "Entry No.") { Clustered = true; }
        key(StaffDay; "Store No.", "Staff ID", "Trans. Date") { }
        key(Source; "Source Entry Key") { }
    }
}

enum 70105 "NWV POS Discount Type"
{
    Extensible = true;
    value(0; "Offer") { Caption = 'Offer / Promotion'; }
    value(1; ManualLine) { Caption = 'Manual Line Discount'; }
    value(2; ManualTotal) { Caption = 'Manual Total Discount'; }
    value(3; PriceOverride) { Caption = 'Price Override'; }
    value(4; "Member") { Caption = 'Member Discount'; }
    value(5; "Coupon") { Caption = 'Coupon'; }
}
