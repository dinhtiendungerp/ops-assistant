/// <summary>
/// GET  /api/naviworld/marouagent/v1.0/companies({id})/discountExceptions
/// PATCH ... /discountExceptions({id})  : agent chi duoc doi status sang "Under Review" (kiem tra trong OnModify)
/// </summary>
page 70112 "NWV Discount Exception API"
{
    PageType = API;
    APIPublisher = 'naviworld';
    APIGroup = 'marouagent';
    APIVersion = 'v1.0';
    EntityName = 'discountException';
    EntitySetName = 'discountExceptions';
    SourceTable = "NWV Discount Exception";
    DelayedInsert = true;
    InsertAllowed = false;
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
                field(entryNo; Rec."Entry No.") { Editable = false; }
                field(ruleCode; Rec."Rule Code") { Editable = false; }
                field(severity; Rec.Severity) { Editable = false; }
                field(storeNo; Rec."Store No.") { Editable = false; }
                field(staffId; Rec."Staff ID") { Editable = false; }
                field(transDate; Rec."Trans. Date") { Editable = false; }
                field(transactionNo; Rec."Transaction No.") { Editable = false; }
                field(posTerminalNo; Rec."POS Terminal No.") { Editable = false; }
                field(itemNo; Rec."Item No.") { Editable = false; }
                field(metricValue; Rec."Metric Value") { Editable = false; }
                field(thresholdValue; Rec."Threshold Value") { Editable = false; }
                field(discountAmount; Rec."Discount Amount") { Editable = false; }
                field(occurrenceCount; Rec."Occurrence Count") { Editable = false; }
                field(description; Rec.Description) { Editable = false; }
                field(status; Rec.Status) { }
                field(detectedAt; Rec."Detected At") { Editable = false; }
                field(referenceKey; Rec."Reference Key") { Editable = false; }
            }
        }
    }

    trigger OnModifyRecord(): Boolean
    var
        AgentStatusErr: Label 'Agent may only set status to Under Review. Confirmed/Dismissed/Explained are reserved for human reviewers.';
    begin
        if IsAgentSession() and not (Rec.Status in [Rec.Status::Open, Rec.Status::UnderReview]) then
            Error(AgentStatusErr);
        exit(true);
    end;

    local procedure IsAgentSession(): Boolean
    var
        Setup: Record "NWV Agent Setup";
    begin
        Setup.GetRecordOnce();
        exit((Setup."Agent User Name" <> '') and (UpperCase(UserId()) = UpperCase(Setup."Agent User Name")));
    end;
}
