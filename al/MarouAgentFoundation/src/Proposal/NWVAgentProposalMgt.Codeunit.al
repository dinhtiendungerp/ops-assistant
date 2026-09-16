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
        MissingPurchaseDataErr: Label 'Proposal %1 lacks Vendor No., To Location or Quantity for a Purchase.', Comment = '%1 = Proposal Id';
        MissingWriteOffDataErr: Label 'Proposal %1 lacks From Location or Quantity for a Write-off.', Comment = '%1 = Proposal Id';
        MissingReceiptDataErr: Label 'Proposal %1 lacks the purchase order number (Source Document No.) to post a receipt for.', Comment = '%1 = Proposal Id';
        DefaultTemplateTok: Label 'ITEM', Locked = true;
        DefaultBatchTok: Label 'AGENT', Locked = true;
        DefaultReasonTok: Label 'AGENT-EXP', Locked = true;
        TemplateDescTxt: Label 'Item Journal';
        BatchDescTxt: Label 'Agent write-off drafts (review and post)';
        ReasonDescTxt: Label 'Expired / damaged stock, proposed by agent';
        WriteOffDescTxt: Label 'Agent write-off, lot %1', Comment = '%1 = Lot No.';

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
            Proposal."Action Type"::Purchase:
                begin
                    // Dakao mua thang tu Marou, giao toi cua hang (15/09/2026). Purchase Order o trang thai Open, KHONG release,
                    // KHONG post; nguoi mua xem lai roi gui. Sang Marou thanh Sales Order la viec cua Intercompany, lam sau.
                    TransferNo := CreatePurchaseOrder(Proposal);
                    Proposal."Result Document Type" := 'Purchase Order';
                    Proposal."Result Document No." := TransferNo;
                    Proposal.Status := Proposal.Status::Executed;
                end;
            Proposal."Action Type"::PostReceipt:
                begin
                    // Intercompany (16/09/2026): Marou da post xuat kho, don mua ben Dakao qua ngay van chua nhan.
                    // Day la loai de xuat DUY NHAT post chung tu, va chi post khi nguoi duyet bam Duyet: so lo lay tu phieu
                    // giao hang cua doi tac, khong bia. Thieu quyen post thi codeunit ben duoi bao loi, khong am tham bo qua.
                    TransferNo := PostPurchaseReceipt(Proposal);
                    Proposal."Result Document Type" := 'Purchase Receipt';
                    Proposal."Result Document No." := TransferNo;
                    Proposal.Status := Proposal.Status::Executed;
                end;
            Proposal."Action Type"::WriteOff:
                begin
                    // UC2 G2/A3 (16/09/2026): dong Item Journal (Negative Adjmt.) CHUA POST, co lo va reason code. Ke toan
                    // xem lai roi post; agent khong post. Document No. = AGENT-<id> de tro ly theo doi ILE sau khi post.
                    TransferNo := CreateWriteOffJournalLine(Proposal);
                    Proposal."Result Document Type" := 'Item Journal Line';
                    Proposal."Result Document No." := TransferNo;
                    Proposal.Status := Proposal.Status::Executed;
                end;
            else
                // Review Only, Markdown, Block Purchase, Audit Note, Escalate:
                // POC chi ghi nhan quyet dinh. Markdown can chung tu rieng (G3), de ngoai pham vi POC.
                Proposal.Status := Proposal.Status::Executed;
        end;
        Proposal.Modify(true);
    end;

    local procedure PostPurchaseReceipt(Proposal: Record "NWV Agent Proposal"): Code[20]
    var
        PurchHeader: Record "Purchase Header";
        ICReceipt: Codeunit "NWV IC Receipt";
    begin
        if Proposal."Source Document No." = '' then
            Error(MissingReceiptDataErr, Proposal."Proposal Id");
        PurchHeader.Get(PurchHeader."Document Type"::Order, Proposal."Source Document No.");
        exit(ICReceipt.PostReceipt(PurchHeader));
    end;

    local procedure CreateWriteOffJournalLine(Proposal: Record "NWV Agent Proposal"): Code[20]
    var
        Setup: Record "NWV Agent Setup";
        ItemJnlLine: Record "Item Journal Line";
        LastLine: Record "Item Journal Line";
        TemplateName: Code[10];
        BatchName: Code[10];
        ReasonCode: Code[10];
        DocNo: Code[20];
    begin
        if (Proposal."From Location Code" = '') or (Proposal.Quantity <= 0) then
            Error(MissingWriteOffDataErr, Proposal."Proposal Id");
        Setup.GetRecordOnce();
        TemplateName := Setup."Write-off Jnl. Template";
        if TemplateName = '' then
            TemplateName := DefaultTemplateTok;
        BatchName := Setup."Write-off Jnl. Batch";
        if BatchName = '' then
            BatchName := DefaultBatchTok;
        ReasonCode := Setup."Write-off Reason Code";
        if ReasonCode = '' then
            ReasonCode := DefaultReasonTok;
        EnsureWriteOffBatch(TemplateName, BatchName, ReasonCode);

        // Entry No. chu khong phai Proposal Id: Proposal Id la GUID, cat 20 ky tu thanh 'AGENT-{F8D9F9A9-AF40', khong doc duoc
        // va khong chac duy nhat. Lan chay dau 16/09/2026 da tao mot dong nhu vay trong NWV-MAROU.
        DocNo := CopyStr('AGENT-' + Format(Proposal."Entry No."), 1, MaxStrLen(DocNo));
        LastLine.SetRange("Journal Template Name", TemplateName);
        LastLine.SetRange("Journal Batch Name", BatchName);
        if not LastLine.FindLast() then
            LastLine."Line No." := 0;

        ItemJnlLine.Init();
        ItemJnlLine."Journal Template Name" := TemplateName;
        ItemJnlLine."Journal Batch Name" := BatchName;
        ItemJnlLine."Line No." := LastLine."Line No." + 10000;
        ItemJnlLine.SetUpNewLine(LastLine);
        ItemJnlLine.Insert(true);
        ItemJnlLine.Validate("Entry Type", ItemJnlLine."Entry Type"::"Negative Adjmt.");
        ItemJnlLine.Validate("Posting Date", WorkDate());
        ItemJnlLine.Validate("Document No.", DocNo);
        ItemJnlLine.Validate("Item No.", Proposal."Item No.");
        ItemJnlLine.Validate("Location Code", Proposal."From Location Code");
        ItemJnlLine.Validate(Quantity, Proposal.Quantity);
        ItemJnlLine.Validate("Reason Code", ReasonCode);
        // Lot No. tren dong chi song khi batch bat "Item Tracking on Lines" (EnsureWriteOffBatch), xem CLAUDE.md.
        if Proposal."Lot No." <> '' then
            ItemJnlLine.Validate("Lot No.", Proposal."Lot No.");
        ItemJnlLine.Description := CopyStr(StrSubstNo(WriteOffDescTxt, Proposal."Lot No."), 1, MaxStrLen(ItemJnlLine.Description));
        ItemJnlLine.Modify(true);
        exit(DocNo);
    end;

    local procedure EnsureWriteOffBatch(TemplateName: Code[10]; BatchName: Code[10]; ReasonCode: Code[10])
    var
        ItemJnlTemplate: Record "Item Journal Template";
        ItemJnlBatch: Record "Item Journal Batch";
        Reason: Record "Reason Code";
    begin
        if not ItemJnlTemplate.Get(TemplateName) then begin
            ItemJnlTemplate.Init();
            ItemJnlTemplate.Validate(Name, TemplateName);
            ItemJnlTemplate.Validate(Description, TemplateDescTxt);
            ItemJnlTemplate.Validate(Type, ItemJnlTemplate.Type::Item);
            ItemJnlTemplate.Insert(true);
        end;
        if not ItemJnlBatch.Get(TemplateName, BatchName) then begin
            ItemJnlBatch.Init();
            ItemJnlBatch.Validate("Journal Template Name", TemplateName);
            ItemJnlBatch.Validate(Name, BatchName);
            ItemJnlBatch.Validate(Description, BatchDescTxt);
            ItemJnlBatch.Insert(true);
        end;
        if not ItemJnlBatch."Item Tracking on Lines" then begin
            ItemJnlBatch.Validate("Item Tracking on Lines", true);
            ItemJnlBatch.Modify(true);
        end;
        if not Reason.Get(ReasonCode) then begin
            Reason.Init();
            Reason.Code := ReasonCode;
            Reason.Description := ReasonDescTxt;
            Reason.Insert(true);
        end;
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
        // Entry No. chu khong phai Proposal Id. Proposal Id la GUID 38 ky tu, ma External Document No. chi co 35, nen no ra
        // 'AGENT {EAB7F98D-D8B3-4F2D-8248-6F36': khong doc duoc, khong tra nguoc ve de xuat duoc, va khong chac duy nhat.
        // Dung bat duoc 16/09/2026 tren Your Reference cua don mua, cung mot loi voi Document No. cua chung tu huy.
        TransferHeader."External Document No." := CopyStr('AGENT ' + Format(Proposal."Entry No."), 1, MaxStrLen(TransferHeader."External Document No."));
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

    local procedure CreatePurchaseOrder(Proposal: Record "NWV Agent Proposal"): Code[20]
    var
        PurchaseHeader: Record "Purchase Header";
        PurchaseLine: Record "Purchase Line";
    begin
        if (Proposal."Vendor No." = '') or (Proposal."To Location Code" = '') or (Proposal.Quantity <= 0) then
            Error(MissingPurchaseDataErr, Proposal."Proposal Id");

        PurchaseHeader.Init();
        PurchaseHeader."Document Type" := PurchaseHeader."Document Type"::Order;
        PurchaseHeader.Insert(true);
        PurchaseHeader.Validate("Buy-from Vendor No.", Proposal."Vendor No.");
        PurchaseHeader.Validate("Location Code", Proposal."To Location Code");
        PurchaseHeader.Validate("Order Date", WorkDate());
        PurchaseHeader.Validate("Posting Date", WorkDate());
        PurchaseHeader."Your Reference" := CopyStr('AGENT ' + Format(Proposal."Entry No."), 1, MaxStrLen(PurchaseHeader."Your Reference"));
        PurchaseHeader.Modify(true);

        PurchaseLine.Init();
        PurchaseLine."Document Type" := PurchaseHeader."Document Type";
        PurchaseLine."Document No." := PurchaseHeader."No.";
        PurchaseLine."Line No." := 10000;
        PurchaseLine.Insert(true);
        PurchaseLine.Validate(Type, PurchaseLine.Type::Item);
        PurchaseLine.Validate("No.", Proposal."Item No.");
        PurchaseLine.Validate("Location Code", Proposal."To Location Code");
        PurchaseLine.Validate(Quantity, Proposal.Quantity);
        PurchaseLine.Modify(true);

        exit(PurchaseHeader."No.");
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
