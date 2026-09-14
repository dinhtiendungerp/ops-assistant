/// <summary>
/// GET /api/naviworld/marouagent/v1.0/companies({id})/nwvItemCategories
/// Chi doc. Nguong phan tang cua UC2 dat theo nhom hang, nen can ca cay phan cap chu
/// khong chi ma nhom tren Item.
/// </summary>
page 70205 "NWV Item Category API"
{
    PageType = API;
    Caption = 'NWV Item Category API';
    APIPublisher = 'naviworld';
    APIGroup = 'marouagent';
    APIVersion = 'v1.0';
    EntityName = 'nwvItemCategory';
    EntitySetName = 'nwvItemCategories';
    SourceTable = "Item Category";
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
                field(code; Rec.Code) { }
                field(description; Rec.Description) { }
                field(parentCategory; Rec."Parent Category") { }
                field(indentation; Rec.Indentation) { }
                field(lastModifiedDateTime; Rec.SystemModifiedAt) { }
            }
        }
    }
}
