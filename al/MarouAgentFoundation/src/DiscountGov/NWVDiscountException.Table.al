/// <summary>
/// Ngoai le discount do lop logic phat hien. Agent doc bang nay, viet ghi chu audit va de xuat Escalate.
/// Agent KHONG tu tao exception; rule nam trong codeunit NWV Discount Gov. Calc de nguoi kiem toan doc duoc.
/// </summary>
table 70105 "NWV Discount Exception"
{
    Caption = 'NWV Discount Exception';
    DataClassification = CustomerContent;

    fields
    {
        field(1; "Entry No."; Integer)
        {
            Caption = 'Entry No.';
            AutoIncrement = true;
        }
        field(2; "Rule Code"; Code[20]) { Caption = 'Rule Code'; }
        field(3; Severity; Enum "NWV Exception Severity") { Caption = 'Severity'; }
        field(10; "Store No."; Code[10]) { Caption = 'Store No.'; }
        field(11; "Staff ID"; Code[20]) { Caption = 'Staff ID'; }
        field(12; "Trans. Date"; Date) { Caption = 'Transaction Date'; }
        field(13; "Transaction No."; Integer) { Caption = 'Transaction No.'; }
        field(14; "POS Terminal No."; Code[10]) { Caption = 'POS Terminal No.'; }
        field(15; "Item No."; Code[20]) { Caption = 'Item No.'; }
        field(20; "Metric Value"; Decimal) { Caption = 'Metric Value'; DecimalPlaces = 0 : 2; }
        field(21; "Threshold Value"; Decimal) { Caption = 'Threshold Value'; DecimalPlaces = 0 : 2; }
        field(22; "Discount Amount"; Decimal) { Caption = 'Discount Amount'; }
        field(23; "Occurrence Count"; Integer) { Caption = 'Occurrence Count'; }
        field(24; Description; Text[250]) { Caption = 'Description'; }
        field(30; Status; Enum "NWV Exception Status") { Caption = 'Status'; }
        field(31; "Detected At"; DateTime) { Caption = 'Detected At'; }
        field(32; "Reference Key"; Text[100]) { Caption = 'Reference Key'; }
    }

    keys
    {
        key(PK; "Entry No.") { Clustered = true; }
        key(Open; Status, Severity, "Trans. Date") { }
        key(Ref; "Reference Key") { }
    }
}

enum 70106 "NWV Exception Severity"
{
    Extensible = true;
    value(0; Low) { Caption = 'Low'; }
    value(1; Medium) { Caption = 'Medium'; }
    value(2; High) { Caption = 'High'; }
}

enum 70107 "NWV Exception Status"
{
    Extensible = true;
    value(0; Open) { Caption = 'Open'; }
    value(1; UnderReview) { Caption = 'Under Review'; }
    value(2; Explained) { Caption = 'Explained'; }
    value(3; Confirmed) { Caption = 'Confirmed'; }
    value(4; Dismissed) { Caption = 'Dismissed'; }
}
