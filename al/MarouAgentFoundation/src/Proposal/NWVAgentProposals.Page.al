/// <summary>
/// Page nguoi duyet dung hang ngay. Day la noi "ket qua nhin thay duoc" cua POC:
/// so de xuat, ty le duyet, chung tu tao ra.
/// </summary>
page 70101 "NWV Agent Proposals"
{
    Caption = 'NWV Agent Proposals';
    PageType = List;
    SourceTable = "NWV Agent Proposal";
    SourceTableView = sorting(Scenario, Status, "Priority Score") order(descending);
    ApplicationArea = All;
    UsageCategory = Tasks;
    InsertAllowed = false;
    DeleteAllowed = false;
    ModifyAllowed = false;

    layout
    {
        area(Content)
        {
            repeater(Lines)
            {
                field(Scenario; Rec.Scenario) { }
                field(Status; Rec.Status) { StyleExpr = StatusStyle; }
                field("Priority Score"; Rec."Priority Score") { }
                field("Action Type"; Rec."Action Type") { }
                field("Item No."; Rec."Item No.") { }
                field("Lot No."; Rec."Lot No.") { }
                field("From Location Code"; Rec."From Location Code") { }
                field("To Location Code"; Rec."To Location Code") { }
                field(Quantity; Rec.Quantity) { }
                field(Rationale; Rec.Rationale) { }
                field("Created At"; Rec."Created At") { }
                field("Created By Agent"; Rec."Created By Agent") { }
                field("Model Name"; Rec."Model Name") { Visible = false; }
                field("Run Id"; Rec."Run Id") { Visible = false; }
                field("Reviewed By"; Rec."Reviewed By") { }
                field("Review Comment"; Rec."Review Comment") { }
                field("Result Document No."; Rec."Result Document No.") { }
            }
        }
    }

    actions
    {
        area(Processing)
        {
            action(Approve)
            {
                Caption = 'Approve';
                ApplicationArea = All;
                Image = Approve;
                Promoted = true;
                PromotedCategory = Process;
                PromotedIsBig = true;
                ToolTip = 'Duyet de xuat. Voi Transfer, he thong tao Transfer Order o trang thai Open.';
                trigger OnAction()
                var
                    ProposalMgt: Codeunit "NWV Agent Proposal Mgt.";
                begin
                    ProposalMgt.Approve(Rec, '');
                    CurrPage.Update(false);
                end;
            }
            action(Reject)
            {
                Caption = 'Reject';
                ApplicationArea = All;
                Image = Reject;
                Promoted = true;
                PromotedCategory = Process;
                PromotedIsBig = true;
                ToolTip = 'Tu choi de xuat. Ghi ly do de agent hoc rule (thu cong, POC).';
                trigger OnAction()
                var
                    ProposalMgt: Codeunit "NWV Agent Proposal Mgt.";
                begin
                    ProposalMgt.Reject(Rec, '');
                    CurrPage.Update(false);
                end;
            }
            action(ShowEvidence)
            {
                Caption = 'Show Evidence';
                ApplicationArea = All;
                Image = View;
                ToolTip = 'Xem so lieu agent da doc khi ra de xuat nay.';
                trigger OnAction()
                begin
                    Message(Rec.GetEvidence());
                end;
            }
            // Don bang de xuat giua cac lan demo. Xoa theo BO LOC dang ap tren trang, khong phai
            // ca bang: loc Status = Proposed roi bam la chi xoa de xuat chua duyet. Transfer Order
            // da tao tu de xuat khong bi dong vao. Can quyen D tren bang; permission set cua agent
            // (NWV AGENT RUN) chi co RIM nen tai khoan agent khong xoa duoc.
            action(DeleteAll)
            {
                Caption = 'Delete All';
                ApplicationArea = All;
                Image = Delete;
                Promoted = true;
                PromotedCategory = Process;
                ToolTip = 'Xoa tat ca de xuat dang hien theo bo loc hien tai. Transfer Order da tao van giu nguyen.';
                trigger OnAction()
                var
                    Proposal: Record "NWV Agent Proposal";
                    SoDong: Integer;
                begin
                    Proposal.CopyFilters(Rec);
                    SoDong := Proposal.Count();
                    if SoDong = 0 then
                        exit;
                    if not Confirm(DeleteAllQst, false, SoDong) then
                        exit;
                    Proposal.DeleteAll(true);
                    CurrPage.Update(false);
                    Message(DeleteAllDoneMsg, SoDong);
                end;
            }
        }
    }

    var
        StatusStyle: Text;
        DeleteAllQst: Label 'Xoa %1 de xuat dang hien theo bo loc hien tai?\De xuat da duyet cung bi xoa; Transfer Order da tao van giu nguyen trong BC. Khong hoan tac duoc.', Comment = '%1 = so de xuat';
        DeleteAllDoneMsg: Label 'Da xoa %1 de xuat.', Comment = '%1 = so de xuat';

    trigger OnAfterGetRecord()
    begin
        case Rec.Status of
            Rec.Status::Proposed:
                StatusStyle := 'Attention';
            Rec.Status::Executed:
                StatusStyle := 'Favorable';
            Rec.Status::Rejected, Rec.Status::Failed:
                StatusStyle := 'Unfavorable';
            else
                StatusStyle := 'Standard';
        end;
    end;
}

page 70102 "NWV Inv. Health Lines"
{
    Caption = 'NWV Inventory Health';
    PageType = List;
    SourceTable = "NWV Inv. Health Line";
    SourceTableView = sorting("Risk Score") order(descending);
    ApplicationArea = All;
    UsageCategory = Lists;
    Editable = false;

    layout
    {
        area(Content)
        {
            repeater(Lines)
            {
                field("Item No."; Rec."Item No.") { }
                field("Item Description"; Rec."Item Description") { }
                field("Location Code"; Rec."Location Code") { }
                field("Lot No."; Rec."Lot No.") { }
                field(Tier; Rec.Tier) { }
                field("Risk Score"; Rec."Risk Score") { }
                field("Quantity on Hand"; Rec."Quantity on Hand") { }
                field("Inventory Value"; Rec."Inventory Value") { }
                field("Avg Daily Sales Qty"; Rec."Avg Daily Sales Qty") { }
                field("Days of Cover"; Rec."Days of Cover") { }
                field("Days Since Last Sale"; Rec."Days Since Last Sale") { }
                field("Expiration Date"; Rec."Expiration Date") { }
                field("Days To Expiry"; Rec."Days To Expiry") { }
                field("Risk Reason"; Rec."Risk Reason") { }
                field("Calculated At"; Rec."Calculated At") { }
            }
        }
    }
}

page 70103 "NWV Discount Exceptions"
{
    Caption = 'NWV Discount Exceptions';
    PageType = List;
    SourceTable = "NWV Discount Exception";
    SourceTableView = sorting(Status, Severity, "Trans. Date") order(descending);
    ApplicationArea = All;
    UsageCategory = Tasks;
    InsertAllowed = false;
    DeleteAllowed = false;

    layout
    {
        area(Content)
        {
            repeater(Lines)
            {
                field("Rule Code"; Rec."Rule Code") { Editable = false; }
                field(Severity; Rec.Severity) { Editable = false; }
                field(Status; Rec.Status) { }
                field("Store No."; Rec."Store No.") { Editable = false; }
                field("Staff ID"; Rec."Staff ID") { Editable = false; }
                field("Trans. Date"; Rec."Trans. Date") { Editable = false; }
                field("Transaction No."; Rec."Transaction No.") { Editable = false; }
                field("Item No."; Rec."Item No.") { Editable = false; }
                field("Metric Value"; Rec."Metric Value") { Editable = false; }
                field("Threshold Value"; Rec."Threshold Value") { Editable = false; }
                field("Discount Amount"; Rec."Discount Amount") { Editable = false; }
                field("Occurrence Count"; Rec."Occurrence Count") { Editable = false; }
                field(Description; Rec.Description) { Editable = false; }
                field("Detected At"; Rec."Detected At") { Editable = false; }
            }
        }
    }
}
