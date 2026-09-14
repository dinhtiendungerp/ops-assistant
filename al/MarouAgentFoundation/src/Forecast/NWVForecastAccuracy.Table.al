/// <summary>
/// UC1. Do chinh xac cua du bao baseline theo Item x Location x Method, do tren ky kiem tra (holdout) cuoi lich su.
/// Bang so lieu da tinh, agent chi doc. Tinh lai bang codeunit NWV Forecast Accuracy Calc.
/// </summary>
table 70120 "NWV Forecast Accuracy"
{
    Caption = 'NWV Forecast Accuracy';
    DataClassification = CustomerContent;
    LookupPageId = "NWV Forecast Accuracy";
    DrillDownPageId = "NWV Forecast Accuracy";

    fields
    {
        field(1; "Item No."; Code[20]) { Caption = 'Item No.'; TableRelation = Item; }
        field(2; "Location Code"; Code[10]) { Caption = 'Location Code'; TableRelation = Location; }
        field(3; Method; Code[10])
        {
            Caption = 'Method';
            ToolTip = 'MA28: trung binh 28 ngay con hang gan nhat. SWA8: trung binh cung thu trong tuan, 8 tuan gan nhat. HW: Holt-Winters mua vu tuan.';
        }
        field(10; "Item Description"; Text[100]) { Caption = 'Item Description'; }
        field(11; "Item Category Code"; Code[20]) { Caption = 'Item Category Code'; }
        field(12; "Demand Basis"; Option)
        {
            Caption = 'Demand Basis';
            OptionMembers = Sale,Outflow;
            OptionCaption = 'Sale,Outflow';
        }
        field(20; "Holdout From"; Date) { Caption = 'Holdout From'; }
        field(21; "Holdout To"; Date) { Caption = 'Holdout To'; }
        field(22; "Days Evaluated"; Integer) { Caption = 'Days Evaluated'; }
        field(23; "Days Censored"; Integer)
        {
            Caption = 'Days Censored';
            ToolTip = 'Ngay het hang ma khong ban duoc gi: nhu cau that khong do duoc nen khong tinh sai so.';
        }
        field(24; "Days Excluded"; Integer)
        {
            Caption = 'Days Excluded';
            ToolTip = 'Ngay co dong LSC Replen. Planned Sales Demand dang Enabled hoac nam trong NWV Demand Exception: su kien da khai, khong tinh sai so va khong dua vao du lieu hoc.';
        }
        field(30; "Actual Qty"; Decimal) { Caption = 'Actual Qty'; DecimalPlaces = 0 : 3; }
        field(31; "Forecast Qty"; Decimal) { Caption = 'Forecast Qty'; DecimalPlaces = 0 : 3; }
        field(32; "Abs Error Qty"; Decimal) { Caption = 'Abs Error Qty'; DecimalPlaces = 0 : 3; }
        field(33; "WAPE %"; Decimal)
        {
            Caption = 'WAPE %';
            DecimalPlaces = 0 : 1;
            ToolTip = 'Tong sai so tuyet doi chia tong ban thuc te, nhan 100. Thap la tot.';
        }
        field(34; "Bias %"; Decimal)
        {
            Caption = 'Bias %';
            DecimalPlaces = 0 : 1;
            ToolTip = 'Tong du bao tru tong thuc te, chia tong thuc te, nhan 100. Duong la du bao cao hon ban.';
        }
        field(35; "Daily Level"; Decimal)
        {
            Caption = 'Daily Level';
            DecimalPlaces = 0 : 3;
            ToolTip = 'Muc ban mot ngay ma phuong phap nay du bao (MA28), hoac trung binh cac thu (SWA8).';
        }
        field(36; "Model Parameters"; Text[100])
        {
            Caption = 'Model Parameters';
            ToolTip = 'Tham so Holt-Winters da chon tren du lieu hoc (alpha, gamma, xu huong). Trong voi MA28 va SWA8.';
        }
        field(40; "Is Exception"; Boolean) { Caption = 'Is Exception'; }
        field(41; "Exception Reason"; Text[250]) { Caption = 'Exception Reason'; }
        field(50; "Calculated At"; DateTime) { Caption = 'Calculated At'; }
        field(51; "As Of Date"; Date) { Caption = 'As Of Date'; }
    }

    keys
    {
        key(PK; "Item No.", "Location Code", Method) { Clustered = true; }
        key(Category; "Item Category Code", "Location Code") { }
    }
}

/// <summary>Du bao va thuc te tung ngay trong ky kiem tra, de ve bieu do du bao so voi thuc te.</summary>
table 70121 "NWV Forecast Daily"
{
    Caption = 'NWV Forecast Daily';
    DataClassification = CustomerContent;

    fields
    {
        field(1; "Item No."; Code[20]) { Caption = 'Item No.'; TableRelation = Item; }
        field(2; "Location Code"; Code[10]) { Caption = 'Location Code'; TableRelation = Location; }
        field(3; Method; Code[10]) { Caption = 'Method'; }
        field(4; "Date"; Date) { Caption = 'Date'; }
        field(10; "Actual Qty"; Decimal) { Caption = 'Actual Qty'; DecimalPlaces = 0 : 3; }
        field(11; "Forecast Qty"; Decimal) { Caption = 'Forecast Qty'; DecimalPlaces = 0 : 3; }
        field(12; Censored; Boolean) { Caption = 'Censored'; }
        field(13; Excluded; Boolean) { Caption = 'Excluded'; }
    }

    keys
    {
        key(PK; "Item No.", "Location Code", Method, "Date") { Clustered = true; }
    }
}
