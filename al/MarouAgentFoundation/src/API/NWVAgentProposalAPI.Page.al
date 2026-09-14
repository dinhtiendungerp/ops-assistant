/// <summary>
/// POST /api/naviworld/marouagent/v1.0/companies({id})/agentProposals  : agent ghi de xuat (Status luon = Proposed)
/// GET  ...                                                            : agent doc lai de tranh de xuat trung
/// POST .../agentProposals({id})/Microsoft.NAV.approve  body {"comment": "..."} : nguoi duyet (KHONG phai agent)
/// POST .../agentProposals({id})/Microsoft.NAV.reject   body {"comment": "..."}
/// </summary>
page 70113 "NWV Agent Proposal API"
{
    PageType = API;
    APIPublisher = 'naviworld';
    APIGroup = 'marouagent';
    APIVersion = 'v1.0';
    EntityName = 'agentProposal';
    EntitySetName = 'agentProposals';
    SourceTable = "NWV Agent Proposal";
    DelayedInsert = true;
    DeleteAllowed = false;
    ODataKeyFields = SystemId;
    Extensible = false;

    layout
    {
        area(Content)
        {
            repeater(Lines)
            {
                field(id; Rec.SystemId) { Editable = false; }
                field(proposalId; Rec."Proposal Id") { Editable = false; }
                field(scenario; Rec.Scenario) { }
                field(actionType; Rec."Action Type") { }
                field(status; Rec.Status) { Editable = false; }
                field(itemNo; Rec."Item No.") { }
                field(lotNo; Rec."Lot No.") { }
                field(fromLocationCode; Rec."From Location Code") { }
                field(toLocationCode; Rec."To Location Code") { }
                field(quantity; Rec.Quantity) { }
                field(referenceKey; Rec."Reference Key") { }
                field(rationale; Rec.Rationale) { }
                field(evidenceJson; EvidenceText)
                {
                    Caption = 'Evidence JSON';
                    trigger OnValidate()
                    begin
                        Rec.SetEvidence(EvidenceText);
                    end;
                }
                field(priorityScore; Rec."Priority Score") { }
                field(createdByAgent; Rec."Created By Agent") { Editable = false; }
                field(createdAt; Rec."Created At") { Editable = false; }
                field(modelName; Rec."Model Name") { }
                field(runId; Rec."Run Id") { }
                field(reviewedBy; Rec."Reviewed By") { Editable = false; }
                field(reviewedAt; Rec."Reviewed At") { Editable = false; }
                field(reviewComment; Rec."Review Comment") { Editable = false; }
                field(resultDocumentType; Rec."Result Document Type") { Editable = false; }
                field(resultDocumentNo; Rec."Result Document No.") { Editable = false; }
            }
        }
    }

    var
        EvidenceText: Text;

    trigger OnAfterGetRecord()
    begin
        EvidenceText := Rec.GetEvidence();
    end;

    trigger OnInsertRecord(BelowxRec: Boolean): Boolean
    begin
        // Agent khong duoc chon status; moi de xuat vao o Proposed
        Rec.Status := Rec.Status::Proposed;
        Rec."Reviewed By" := '';
        Rec."Reviewed At" := 0DT;
        exit(true);
    end;

    trigger OnModifyRecord(): Boolean
    var
        ProposedOnlyErr: Label 'Only proposals in status Proposed can be modified through the API.';
    begin
        if xRec.Status <> xRec.Status::Proposed then
            Error(ProposedOnlyErr);
        Rec.Status := Rec.Status::Proposed;
        exit(true);
    end;

    [ServiceEnabled]
    procedure approve(comment: Text[250])
    var
        ProposalMgt: Codeunit "NWV Agent Proposal Mgt.";
    begin
        ProposalMgt.Approve(Rec, comment);
    end;

    [ServiceEnabled]
    procedure reject(comment: Text[250])
    var
        ProposalMgt: Codeunit "NWV Agent Proposal Mgt.";
    begin
        ProposalMgt.Reject(Rec, comment);
    end;
}
