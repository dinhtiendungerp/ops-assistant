/// <summary>
/// Cua so ngay bat thuong. Day la cho duy nhat trong he thong ma du lieu den tu mieng nguoi
/// chu khong den tu chung tu: "thang 8 co hoi cho ngay truoc cua hang".
/// Khong bang nao trong BC chua chuyen do, va no la ly do that khien moi con so thang do lech.
///
/// Dung o hai cho: bo nhung ngay nay ra khi tinh toc do ban binh quan, va bo nhung dot
/// dut hang roi trong cua so nay ra khi danh gia mot cap cua hang va mat hang co van de he thong hay khong.
/// </summary>
table 70107 "NWV Demand Exception"
{
    Caption = 'NWV Demand Exception';
    DataClassification = CustomerContent;
    LookupPageId = "NWV Demand Exceptions";
    DrillDownPageId = "NWV Demand Exceptions";

    fields
    {
        field(1; "Entry No."; Integer)
        {
            Caption = 'Entry No.';
            DataClassification = SystemMetadata;
            AutoIncrement = true;
        }
        field(10; "Item No."; Code[20])
        {
            Caption = 'Item No.';
            DataClassification = CustomerContent;
            TableRelation = Item;
            ToolTip = 'Để trống nghĩa là áp cho mọi mặt hàng tại địa điểm này.';
        }
        field(11; "Location Code"; Code[10])
        {
            Caption = 'Location Code';
            DataClassification = CustomerContent;
            TableRelation = Location;
            ToolTip = 'Để trống nghĩa là áp cho mọi địa điểm.';
        }
        field(20; "From Date"; Date)
        {
            Caption = 'From Date';
            DataClassification = CustomerContent;
            NotBlank = true;
        }
        field(21; "To Date"; Date)
        {
            Caption = 'To Date';
            DataClassification = CustomerContent;
            NotBlank = true;

            trigger OnValidate()
            begin
                if (Rec."To Date" <> 0D) and (Rec."From Date" <> 0D) and (Rec."To Date" < Rec."From Date") then
                    Error(DateOrderErr);
            end;
        }
        field(30; "Reason"; Text[250])
        {
            Caption = 'Lý do';
            DataClassification = CustomerContent;
            ToolTip = 'Chuyện gì đã xảy ra trong khoảng ngày này. Viết đủ để người sau đọc còn hiểu.';
        }
        field(31; "Exclude From Demand"; Boolean)
        {
            Caption = 'Bỏ khỏi phép tính nhu cầu';
            DataClassification = CustomerContent;
            InitValue = true;
            ToolTip = 'Bật thì những ngày này không được tính vào tốc độ bán bình quân.';
        }
        field(40; "Registered By"; Code[50])
        {
            Caption = 'Người ghi nhận';
            DataClassification = EndUserIdentifiableInformation;
            Editable = false;
        }
        field(41; "Registered At"; DateTime)
        {
            Caption = 'Ghi nhận lúc';
            DataClassification = SystemMetadata;
            Editable = false;
        }
    }

    keys
    {
        key(PK; "Entry No.")
        {
            Clustered = true;
        }
        key(ByScope; "Item No.", "Location Code", "From Date") { }
    }

    var
        DateOrderErr: Label 'Ngày kết thúc không được sớm hơn ngày bắt đầu.';

    trigger OnInsert()
    begin
        Rec."Registered By" := CopyStr(UserId(), 1, MaxStrLen(Rec."Registered By"));
        Rec."Registered At" := CurrentDateTime();
    end;

    /// <summary>
    /// Ngay nay co nam trong cua so ngoai le nao khong. Cap cu the thang cap de trong.
    /// </summary>
    procedure IsExcluded(ItemNo: Code[20]; LocationCode: Code[10]; CheckDate: Date): Boolean
    var
        DemandException: Record "NWV Demand Exception";
    begin
        DemandException.Reset();
        DemandException.SetRange("Exclude From Demand", true);
        DemandException.SetFilter("Item No.", '%1|%2', ItemNo, '');
        DemandException.SetFilter("Location Code", '%1|%2', LocationCode, '');
        DemandException.SetFilter("From Date", '<=%1', CheckDate);
        DemandException.SetFilter("To Date", '>=%1', CheckDate);
        exit(not DemandException.IsEmpty());
    end;
}
