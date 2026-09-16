/// <summary>
/// GET /api/naviworld/marouagent/v1.0/companies({id})/nwvItemJournalLines
/// Chi doc. UC2 A3 (16/09/2026): tro ly theo doi dong Item Journal do duyet de xuat Write-off sinh ra (Document No. AGENT-{id})
/// con nam trong journal (chua post) hay da bien mat (ke toan da post, ILE mang cung Document No.).
/// </summary>
page 70289 "NWV Item Journal Line API"
{
    PageType = API;
    Caption = 'NWV Item Journal Line API';
    APIPublisher = 'naviworld';
    APIGroup = 'marouagent';
    APIVersion = 'v1.0';
    EntityName = 'nwvItemJournalLine';
    EntitySetName = 'nwvItemJournalLines';
    SourceTable = "Item Journal Line";
    DelayedInsert = true;
    Editable = false;
    InsertAllowed = false;
    ModifyAllowed = false;
    DeleteAllowed = false;
    ODataKeyFields = SystemId;
    Extensible = false;

    layout
    {
        area(Content)
        {
            repeater(Lines)
            {
                field(id; Rec.SystemId) { }
                field(journalTemplateName; Rec."Journal Template Name") { }
                field(journalBatchName; Rec."Journal Batch Name") { }
                field(lineNo; Rec."Line No.") { }
                field(postingDate; Rec."Posting Date") { }
                field(entryType; Rec."Entry Type") { }
                field(documentNo; Rec."Document No.") { }
                field(itemNo; Rec."Item No.") { }
                field(description; Rec.Description) { }
                field(locationCode; Rec."Location Code") { }
                field(quantity; Rec.Quantity) { }
                field(unitOfMeasureCode; Rec."Unit of Measure Code") { }
                field(lotNo; Rec."Lot No.") { }
                field(reasonCode; Rec."Reason Code") { }
                field(unitCost; Rec."Unit Cost") { }
            }
        }
    }
}
