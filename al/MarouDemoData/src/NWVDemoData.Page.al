/// <summary>
/// Mot nut duy nhat. Chi cai len sandbox.
/// </summary>
page 70070 "NWV Demo Data"
{
    Caption = 'NWV Demo Data (sandbox)';
    PageType = Card;
    ApplicationArea = All;
    UsageCategory = Administration;

    layout
    {
        area(Content)
        {
            group(Info)
            {
                Caption = 'Dữ liệu demo cho POC Marou';
                field(Explain; ExplainTxt)
                {
                    ApplicationArea = All;
                    ShowCaption = false;
                    MultiLine = true;
                    Editable = false;
                    ToolTip = 'Giải thích việc nút Tạo dữ liệu demo sẽ làm.';
                }
            }
        }
    }

    actions
    {
        area(Processing)
        {
            action(CreateAll)
            {
                Caption = 'Tạo dữ liệu demo';
                ApplicationArea = All;
                Image = CreateForm;
                Promoted = true;
                PromotedCategory = Process;
                PromotedOnly = true;
                ToolTip = 'Tạo item, location, lô nhập kho và 120 ngày lịch sử bán bằng cách post Item Journal. Chạy một lần trên sandbox.';

                trigger OnAction()
                var
                    DemoDataMgt: Codeunit "NWV Demo Data Mgt.";
                begin
                    if not Confirm(ConfirmQst, false) then
                        exit;
                    DemoDataMgt.CreateAll();
                end;
            }
        }
    }

    var
        ExplainTxt: Label 'Tạo 12 item chocolate có lô và hạn dùng, 5 location, tuyến chuyển kho, rồi post thật 120 ngày lịch sử bán qua Item Journal. Có sẵn các tình huống: lô hết hạn, lô cận date không bán kịp, hàng chậm luân chuyển, đứt hàng sau hội chợ. Mất vài phút. Chỉ chạy trên sandbox.';
        ConfirmQst: Label 'Sẽ post vài nghìn dòng Item Journal vào company này. Chỉ làm trên sandbox. Tiếp tục?';
}
