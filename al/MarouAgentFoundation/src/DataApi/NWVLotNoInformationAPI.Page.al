/// <summary>
/// GET /api/naviworld/marouagent/v1.0/companies({id})/nwvLotNoInformation
/// Chi doc. Table 6505 Lot No. Information. API chuan khong co entity nao cho bang nay.
/// Luu y da kiem tren tai lieu AL: bang nay KHONG co truong Expiration Date va khong co
/// Expiration Action Date. Han dung nam tren Item Ledger Entry, lay o page 70201.
/// Truong expiredInventory la FlowField phu thuoc Date Filter, khong dat filter thi tra 0.
/// </summary>
page 70202 "NWV Lot No. Information API"
{
    PageType = API;
    Caption = 'NWV Lot No. Information API';
    APIPublisher = 'naviworld';
    APIGroup = 'marouagent';
    APIVersion = 'v1.0';
    EntityName = 'nwvLotNoInfo';
    EntitySetName = 'nwvLotNoInformation';
    SourceTable = "Lot No. Information";
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
                field(itemNo; Rec."Item No.") { }
                field(variantCode; Rec."Variant Code") { }
                field(lotNo; Rec."Lot No.") { }
                field(description; Rec.Description) { }
                field(certificateNumber; Rec."Certificate Number") { }
                field(blocked; Rec.Blocked) { }
                field(inventory; Rec.Inventory) { }
                field(expiredInventory; Rec."Expired Inventory") { }
                field(lastModifiedDateTime; Rec.SystemModifiedAt) { }
            }
        }
    }
}
