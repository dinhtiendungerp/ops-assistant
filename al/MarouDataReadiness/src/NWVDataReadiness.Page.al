/// <summary>
/// Bang do phu du lieu. Bam Chay kiem tra la ra ket qua, khong can cau hinh gi truoc.
/// Doc tu tren xuong: dong mau do la thu phai sua truoc khi chot pham vi POC.
/// </summary>
page 70050 "NWV Data Readiness"
{
    Caption = 'NWV Data Readiness';
    PageType = List;
    ApplicationArea = All;
    UsageCategory = Administration;
    SourceTable = "NWV Data Readiness Line";
    SourceTableView = sorting("Entry No.");
    InsertAllowed = false;
    DeleteAllowed = false;
    ModifyAllowed = false;
    Editable = false;

    layout
    {
        area(Content)
        {
            repeater(Lines)
            {
                field("Check Code"; Rec."Check Code")
                {
                    ApplicationArea = All;
                    ToolTip = 'Mã của dòng kiểm tra, dùng để trích dẫn trong biên bản.';
                    StyleExpr = StyleTxt;
                }
                field("Group Name"; Rec."Group Name")
                {
                    ApplicationArea = All;
                    ToolTip = 'Nhóm kiểm tra.';
                    StyleExpr = StyleTxt;
                }
                field(Description; Rec.Description)
                {
                    ApplicationArea = All;
                    ToolTip = 'Nội dung của phép đếm.';
                    StyleExpr = StyleTxt;
                }
                field("Value Text"; Rec."Value Text")
                {
                    ApplicationArea = All;
                    ToolTip = 'Kết quả đếm được trên dữ liệu hiện tại.';
                    StyleExpr = StyleTxt;
                }
                field("Percent"; Rec."Percent")
                {
                    ApplicationArea = All;
                    ToolTip = 'Tỷ lệ phần trăm, chỉ có ý nghĩa với các dòng dạng tỷ lệ.';
                    StyleExpr = StyleTxt;
                }
                field(Verdict; Rec.Verdict)
                {
                    ApplicationArea = All;
                    ToolTip = 'Đạt, cần xem lại, hoặc chặn. Chặn nghĩa là phải sửa dữ liệu trước khi cam kết phạm vi.';
                    StyleExpr = StyleTxt;
                }
                field(Impact; Rec.Impact)
                {
                    ApplicationArea = All;
                    ToolTip = 'Nếu chỉ số này thấp thì ảnh hưởng tới phần nào của POC.';
                    StyleExpr = StyleTxt;
                }
                field("Calculated At"; Rec."Calculated At")
                {
                    ApplicationArea = All;
                    ToolTip = 'Thời điểm chạy.';
                    Visible = false;
                }
            }
        }
    }

    actions
    {
        area(Processing)
        {
            action(RunCheck)
            {
                ApplicationArea = All;
                Caption = 'Chạy kiểm tra';
                ToolTip = 'Đếm lại toàn bộ trên dữ liệu hiện tại. Chỉ đọc, không thay đổi gì trong hệ thống.';
                Image = Refresh;
                Promoted = true;
                PromotedCategory = Process;
                PromotedIsBig = true;

                trigger OnAction()
                var
                    ReadinessCalc: Codeunit "NWV Data Readiness Calc";
                begin
                    ReadinessCalc.Run();
                    CurrPage.Update(false);
                    Message(DoneMsg);
                end;
            }
        }
    }

    var
        StyleTxt: Text;
        DoneMsg: Label 'Đã chạy xong. Dòng màu đỏ là thứ cần sửa trước khi chốt phạm vi POC.';

    trigger OnAfterGetRecord()
    begin
        case Rec.Verdict of
            Rec.Verdict::OK:
                StyleTxt := 'Favorable';
            Rec.Verdict::Warning:
                StyleTxt := 'Ambiguous';
            Rec.Verdict::Blocker:
                StyleTxt := 'Unfavorable';
            else
                StyleTxt := 'Standard';
        end;
    end;
}
