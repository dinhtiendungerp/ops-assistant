/// <summary>
/// Duyet / tu choi / thuc thi de xuat. Chi nguoi dung (khong phai agent) goi Approve.
/// Thuc thi Transfer = tao Transfer Order o trang thai Open, KHONG release, KHONG post.
/// Nguoi kho van phai release va ship nhu quy trinh hien tai.
/// </summary>
codeunit 70102 "NWV Agent Proposal Mgt."
{
    var
        NotProposedErr: Label 'Proposal %1 is not in status Proposed (current: %2).', Comment = '%1 = Proposal Id, %2 = Status';
        AgentCannotApproveErr: Label 'The agent user %1 is not allowed to approve proposals.', Comment = '%1 = user id';
        MissingTransferDataErr: Label 'Proposal %1 lacks From/To Location or Quantity for a Transfer.', Comment = '%1 = Proposal Id';

    procedure Approve(var Proposal: Record "NWV Agent Proposal"; Comment: Text[250])
    begin
        CheckNotAgent();
        if Proposal.Status <> Proposal.Status::Proposed then
            Error(NotProposedErr, Proposal."Proposal Id", Proposal.Status);
        Proposal.Status := Proposal.Status::Approved;
        Proposal."Reviewed By" := CopyStr(UserId(), 1, MaxStrLen(Proposal."Reviewed By"));
        Proposal."Reviewed At" := CurrentDateTime();
        Proposal."Review Comment" := Comment;
        Proposal.Modify(true);
        Execute(Proposal);
    end;

    procedure Reject(var Proposal: Record "NWV Agent Proposal"; Comment: Text[250])
    begin
        CheckNotAgent();
        if Proposal.Status <> Proposal.Status::Proposed then
            Error(NotProposedErr, Proposal."Proposal Id", Proposal.Status);
        Proposal.Status := Proposal.Status::Rejected;
        Proposal."Reviewed By" := CopyStr(UserId(), 1, MaxStrLen(Proposal."Reviewed By"));
        Proposal."Reviewed At" := CurrentDateTime();
        Proposal."Review Comment" := Comment;
        Proposal.Modify(true);
    end;

    local procedure Execute(var Proposal: Record "NWV Agent Proposal")
    var
        TransferNo: Code[20];
    begin
        case Proposal."Action Type" of
            Proposal."Action Type"::Transfer:
                begin
                    TransferNo := CreateTransferOrder(Proposal);
                    Proposal."Result Document Type" := 'Transfer Order';
                    Proposal."Result Document No." := TransferNo;
                    Proposal.Status := Proposal.Status::Executed;
                end;
            else
                // Review Only, Markdown, Block Purchase, Write-off, Audit Note, Escalate:
                // POC chi ghi nhan quyet dinh. Markdown/Write-off can chung tu rieng, de ngoai pham vi POC.
                Proposal.Status := Proposal.Status::Executed;
        end;
        Proposal.Modify(true);
    end;

    local procedure CreateTransferOrder(Proposal: Record "NWV Agent Proposal"): Code[20]
    var
        TransferHeader: Record "Transfer Header";
        TransferLine: Record "Transfer Line";
    begin
        if (Proposal."From Location Code" = '') or (Proposal."To Location Code" = '') or (Proposal.Quantity <= 0) then
            Error(MissingTransferDataErr, Proposal."Proposal Id");

        TransferHeader.Init();
        TransferHeader.Insert(true);
        TransferHeader.Validate("Transfer-from Code", Proposal."From Location Code");
        TransferHeader.Validate("Transfer-to Code", Proposal."To Location Code");
        // In-Transit Code: BC tu dien tu Transfer Route (from/to). Neu Marou chua setup Transfer Route
        // thi nguoi kho dien tay truoc khi release; POC khong bia gia tri.
        TransferHeader.Validate("Posting Date", Today());
        TransferHeader."External Document No." := CopyStr('AGENT ' + Format(Proposal."Proposal Id"), 1, MaxStrLen(TransferHeader."External Document No."));
        TransferHeader.Modify(true);

        TransferLine.Init();
        TransferLine."Document No." := TransferHeader."No.";
        TransferLine."Line No." := 10000;
        TransferLine.Insert(true);
        TransferLine.Validate("Item No.", Proposal."Item No.");
        TransferLine.Validate(Quantity, Proposal.Quantity);
        TransferLine.Modify(true);
        // Lot No.: neu de xuat chi dinh lot, nguoi kho gan Item Tracking khi pick. POC khong tu gan reservation entry.

        exit(TransferHeader."No.");
    end;

    local procedure CheckNotAgent()
    var
        Setup: Record "NWV Agent Setup";
    begin
        Setup.GetRecordOnce();
        if (Setup."Agent User Name" <> '') and (UpperCase(UserId()) = UpperCase(Setup."Agent User Name")) then
            Error(AgentCannotApproveErr, UserId());
    end;
}
