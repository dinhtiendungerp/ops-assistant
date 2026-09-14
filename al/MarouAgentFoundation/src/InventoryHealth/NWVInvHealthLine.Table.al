/// <summary>
/// Ket qua phan tang ton kho theo Item x Location x Lot. Bang nay la "so lieu da tinh",
/// agent chi doc. Tinh lai bang codeunit NWV Inv. Health Calc (Job Queue hang dem hoac chay tay).
/// </summary>
table 70101 "NWV Inv. Health Line"
{
    Caption = 'NWV Inventory Health Line';
    DataClassification = CustomerContent;

    fields
    {
        field(1; "Item No."; Code[20])
        {
            Caption = 'Item No.';
            TableRelation = Item;
        }
        field(2; "Location Code"; Code[10])
        {
            Caption = 'Location Code';
            TableRelation = Location;
        }
        field(3; "Lot No."; Code[50])
        {
            Caption = 'Lot No.';
        }
        field(10; "Item Description"; Text[100]) { Caption = 'Item Description'; }
        field(11; "Item Category Code"; Code[20]) { Caption = 'Item Category Code'; }
        field(12; "Base Unit of Measure"; Code[10]) { Caption = 'Base Unit of Measure'; }
        field(20; "Quantity on Hand"; Decimal)
        {
            Caption = 'Quantity on Hand';
            DecimalPlaces = 0 : 5;
        }
        field(21; "Inventory Value"; Decimal)
        {
            Caption = 'Inventory Value (LCY)';
            AutoFormatType = 1;
        }
        field(22; "Avg Daily Sales Qty"; Decimal)
        {
            Caption = 'Avg Daily Sales Qty';
            DecimalPlaces = 0 : 3;
        }
        field(23; "Days of Cover"; Decimal)
        {
            Caption = 'Days of Cover';
            DecimalPlaces = 0 : 1;
            ToolTip = '9999 nghia la khong co ban trong ky nen khong tinh duoc.';
        }
        field(24; "Last Sale Date"; Date) { Caption = 'Last Sale Date'; }
        field(25; "Days Since Last Sale"; Integer) { Caption = 'Days Since Last Sale'; }
        field(26; "Expiration Date"; Date) { Caption = 'Expiration Date'; }
        field(27; "Days To Expiry"; Integer) { Caption = 'Days To Expiry'; }
        field(28; "Demand Basis"; Option)
        {
            Caption = 'Demand Basis';
            OptionMembers = Sale,Outflow;
            OptionCaption = 'Sale,Outflow';
            ToolTip = 'Sale: nhu cau tinh tren dong ban. Outflow: dia diem khong he ban, tinh tren tong luong xuat, thuong la kho trung tam.';
        }
        field(29; "Days Censored"; Integer)
        {
            Caption = 'Days Censored';
            ToolTip = 'So ngay trong cua so lich su khong con hang va khong ban duoc gi, da loai khoi phep tinh binh quan.';
        }
        field(30; Tier; Enum "NWV Inv. Health Tier") { Caption = 'Tier'; }
        field(31; "Risk Score"; Integer)
        {
            Caption = 'Risk Score';
            ToolTip = '0..100. Cang cao cang can xu ly som. Cong thuc trong codeunit NWV Inv. Health Calc.';
        }
        field(32; "Risk Reason"; Text[250]) { Caption = 'Risk Reason'; }
        field(40; "Calculated At"; DateTime) { Caption = 'Calculated At'; }
        field(41; "As Of Date"; Date)
        {
            Caption = 'As Of Date';
            ToolTip = 'Ngay neo cua lan tinh, la Work Date luc chay. Days To Expiry va Days Since Last Sale tinh tu ngay nay.';
        }
    }

    keys
    {
        key(PK; "Item No.", "Location Code", "Lot No.") { Clustered = true; }
        key(Risk; "Risk Score") { }
        key(Tier; Tier, "Location Code") { }
    }
}

enum 70101 "NWV Inv. Health Tier"
{
    Extensible = true;
    value(0; Healthy) { Caption = 'Healthy'; }
    value(1; StockOutRisk) { Caption = 'Stock-out Risk'; }
    value(2; Excess) { Caption = 'Excess'; }
    value(3; SlowMoving) { Caption = 'Slow-moving'; }
    value(4; NearExpiry) { Caption = 'Near Expiry'; }
    value(5; Expired) { Caption = 'Expired'; }
}
