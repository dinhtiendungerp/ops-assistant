/// <summary>
/// Nguong rieng theo nhom hang. Ly do co bang nay: han dung cua thanh bar 80g va cua bonbon
/// nhan ganache chenh nhau rat xa, nen mot nguong Near Expiry Days chung cho ca hai thi
/// vua bao dong gia voi bar vua bo sot voi bonbon.
/// Dong nao khong khai o day thi lay nguong chung tren "NWV Agent Setup".
/// Gia tri 0 nghia la khong dat rieng, dung nguong chung.
/// </summary>
table 70106 "NWV Category Threshold"
{
    Caption = 'NWV Category Threshold';
    DataClassification = CustomerContent;
    LookupPageId = "NWV Category Thresholds";
    DrillDownPageId = "NWV Category Thresholds";

    fields
    {
        field(1; "Item Category Code"; Code[20])
        {
            Caption = 'Item Category Code';
            DataClassification = CustomerContent;
            TableRelation = "Item Category";
            NotBlank = true;
        }
        field(10; "Near Expiry Days"; Integer)
        {
            Caption = 'Near Expiry Days';
            DataClassification = CustomerContent;
            MinValue = 0;
            ToolTip = 'Còn ít hơn ngần này ngày tới hạn thì xếp vào Near Expiry. Để 0 thì dùng ngưỡng chung.';
        }
        field(11; "Slow-moving Days"; Integer)
        {
            Caption = 'Slow-moving Days';
            DataClassification = CustomerContent;
            MinValue = 0;
            ToolTip = 'Không có dòng bán nào trong ngần này ngày thì xếp vào Slow Moving. Để 0 thì dùng ngưỡng chung.';
        }
        field(12; "Excess Days"; Decimal)
        {
            Caption = 'Excess Days';
            DataClassification = CustomerContent;
            MinValue = 0;
            DecimalPlaces = 0 : 1;
            ToolTip = 'Days of cover cao hơn ngần này thì xếp vào Excess. Để 0 thì dùng ngưỡng chung.';
        }
        field(20; "Reason"; Text[250])
        {
            Caption = 'Lý do đặt riêng';
            DataClassification = CustomerContent;
            ToolTip = 'Ghi lại vì sao nhóm này cần ngưỡng khác, để người sau đọc còn hiểu.';
        }
    }

    keys
    {
        key(PK; "Item Category Code")
        {
            Clustered = true;
        }
    }

    fieldgroups
    {
        fieldgroup(DropDown; "Item Category Code", "Near Expiry Days") { }
    }
}
