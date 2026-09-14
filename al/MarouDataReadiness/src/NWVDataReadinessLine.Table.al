/// <summary>
/// Ket qua kiem tra do phu du lieu. Bang nay bi xoa va ghi lai moi lan chay,
/// khong giu lich su, vi no chi dung de chot hien trang truoc khi bat dau POC.
/// </summary>
table 70050 "NWV Data Readiness Line"
{
    Caption = 'NWV Data Readiness Line';
    DataClassification = CustomerContent;
    LookupPageId = "NWV Data Readiness";
    DrillDownPageId = "NWV Data Readiness";

    fields
    {
        field(1; "Entry No."; Integer)
        {
            Caption = 'Entry No.';
            DataClassification = SystemMetadata;
        }
        field(2; "Check Code"; Code[10])
        {
            Caption = 'Mã kiểm tra';
            DataClassification = SystemMetadata;
        }
        field(3; "Group Name"; Text[50])
        {
            Caption = 'Nhóm';
            DataClassification = SystemMetadata;
        }
        field(4; Description; Text[250])
        {
            Caption = 'Nội dung kiểm tra';
            DataClassification = SystemMetadata;
        }
        field(5; "Value Text"; Text[100])
        {
            Caption = 'Kết quả';
            DataClassification = CustomerContent;
        }
        field(6; Numerator; Decimal)
        {
            Caption = 'Số đạt';
            DataClassification = CustomerContent;
            DecimalPlaces = 0 : 0;
        }
        field(7; Denominator; Decimal)
        {
            Caption = 'Tổng số';
            DataClassification = CustomerContent;
            DecimalPlaces = 0 : 0;
        }
        field(8; "Percent"; Decimal)
        {
            Caption = 'Tỷ lệ %';
            DataClassification = CustomerContent;
            DecimalPlaces = 1 : 1;
        }
        field(9; Verdict; Enum "NWV Readiness Verdict")
        {
            Caption = 'Kết luận';
            DataClassification = CustomerContent;
        }
        field(10; Impact; Text[250])
        {
            Caption = 'Thiếu thì ảnh hưởng gì';
            DataClassification = SystemMetadata;
        }
        field(11; "Calculated At"; DateTime)
        {
            Caption = 'Chạy lúc';
            DataClassification = SystemMetadata;
        }
    }

    keys
    {
        key(PK; "Entry No.")
        {
            Clustered = true;
        }
        key(ByCode; "Check Code") { }
    }

    fieldgroups
    {
        fieldgroup(DropDown; "Check Code", Description, "Value Text") { }
    }
}
