// UC3 Procurement & Supplier Performance. Scorecard theo Vendor x Item Category, dong co Item Category Code rong la tong
// cua nha cung cap. Bang so lieu da tinh, agent chi doc. Tinh lai bang codeunit NWV Supplier Scorecard Calc.
table 70122 "NWV Supplier Scorecard"
{
    Caption = 'NWV Supplier Scorecard';
    DataClassification = CustomerContent;
    LookupPageId = "NWV Supplier Scorecard";
    DrillDownPageId = "NWV Supplier Scorecard";

    fields
    {
        field(1; "Vendor No."; Code[20]) { Caption = 'Vendor No.'; TableRelation = Vendor; }
        field(2; "Item Category Code"; Code[20])
        {
            Caption = 'Item Category Code';
            ToolTip = 'Rong la dong tong cua nha cung cap.';
        }
        field(10; "Vendor Name"; Text[100]) { Caption = 'Vendor Name'; }
        field(20; "Period From"; Date) { Caption = 'Period From'; }
        field(21; "Period To"; Date) { Caption = 'Period To'; }
        field(30; "Lines Due"; Integer)
        {
            Caption = 'Lines Due';
            ToolTip = 'Dong don mua co Expected Receipt Date trong ky va khong sau ngay neo.';
        }
        field(31; "Lines Completed"; Integer) { Caption = 'Lines Completed'; }
        field(32; "Lines On Time"; Integer) { Caption = 'Lines On Time'; }
        field(33; "On-time %"; Decimal)
        {
            Caption = 'On-time %';
            DecimalPlaces = 0 : 1;
            ToolTip = 'Dong nhan du hang khong tre qua On-time Tolerance Days, chia cho dong den han.';
        }
        field(34; "First Delivery Complete %"; Decimal)
        {
            Caption = 'First Delivery Complete %';
            DecimalPlaces = 0 : 1;
            ToolTip = 'Dong nhan du so luong ngay trong lan giao dau tien, chia cho dong da nhan it nhat mot lan.';
        }
        field(35; "Avg Delay Days"; Decimal)
        {
            Caption = 'Avg Delay Days';
            DecimalPlaces = 0 : 1;
            ToolTip = 'Trung binh so ngay tre tren nhung dong tre, tinh ca dong qua han chua nhan du (den ngay neo).';
        }
        field(36; "Avg Promised Lead Time"; Decimal)
        {
            Caption = 'Avg Promised Lead Time (Days)';
            DecimalPlaces = 0 : 1;
            ToolTip = 'Expected Receipt Date tru Order Date.';
        }
        field(37; "Avg Actual Lead Time"; Decimal)
        {
            Caption = 'Avg Actual Lead Time (Days)';
            DecimalPlaces = 0 : 1;
            ToolTip = 'Ngay nhan du hang tru Order Date, tren dong da nhan du.';
        }
        field(40; "Open Lines"; Integer) { Caption = 'Open Lines'; }
        field(41; "Overdue Lines"; Integer)
        {
            Caption = 'Overdue Lines';
            ToolTip = 'Dong con so luong chua nhan va da qua Expected Receipt Date cong dung sai.';
        }
        field(42; "Overdue Qty"; Decimal) { Caption = 'Overdue Qty'; DecimalPlaces = 0 : 3; }
        field(43; "Overdue Amount"; Decimal) { Caption = 'Overdue Amount'; AutoFormatType = 1; }
        field(44; "Last Receipt Date"; Date) { Caption = 'Last Receipt Date'; }
        field(50; "Needs Attention"; Boolean) { Caption = 'Needs Attention'; }
        field(51; "Attention Reason"; Text[250]) { Caption = 'Attention Reason'; }
        field(60; "Calculated At"; DateTime) { Caption = 'Calculated At'; }
        field(61; "As Of Date"; Date) { Caption = 'As Of Date'; }
    }

    keys
    {
        key(PK; "Vendor No.", "Item Category Code") { Clustered = true; }
    }
}
