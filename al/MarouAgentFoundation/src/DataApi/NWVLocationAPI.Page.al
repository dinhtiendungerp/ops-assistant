/// <summary>
/// GET /api/naviworld/marouagent/v1.0/companies({id})/nwvLocations
/// Chi doc. API chuan v2.0 da co entity locations nhung khong phoi Use As In-Transit,
/// Bin Mandatory, Require Pick, Require Receive. Nhung co nay quyet dinh mot kho co duoc
/// tinh vao ton kha dung hay khong, nen phai co de phan tang cho dung.
/// </summary>
page 70204 "NWV Location API"
{
    PageType = API;
    Caption = 'NWV Location API';
    APIPublisher = 'naviworld';
    APIGroup = 'marouagent';
    APIVersion = 'v1.0';
    EntityName = 'nwvLocation';
    EntitySetName = 'nwvLocations';
    SourceTable = Location;
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
                field(name; Rec.Name) { }
                field(city; Rec.City) { }
                field(countryRegionCode; Rec."Country/Region Code") { }
                field(useAsInTransit; Rec."Use As In-Transit") { }
                field(binMandatory; Rec."Bin Mandatory") { }
                field(requirePick; Rec."Require Pick") { }
                field(requireReceive; Rec."Require Receive") { }
                field(requireShipment; Rec."Require Shipment") { }
                field(requirePutAway; Rec."Require Put-away") { }
                // Vai tro theo LS Central (codeunit NWV Location Role): tro ly doc o day, khong doan theo ma dia diem.
                field(isStore; IsStore) { }
                field(storeNo; StoreNo) { }
                field(isWarehouse; IsWarehouse) { }
                field(isCentralWarehouse; IsCentralWarehouse) { }
                field(lastModifiedDateTime; Rec.SystemModifiedAt) { }
            }
        }
    }

    var
        LocationRole: Codeunit "NWV Location Role";
        IsStore: Boolean;
        IsWarehouse: Boolean;
        IsCentralWarehouse: Boolean;
        StoreNo: Code[10];

    trigger OnAfterGetRecord()
    begin
        IsStore := LocationRole.IsStore(Rec.Code);
        StoreNo := LocationRole.StoreNo(Rec.Code);
        IsWarehouse := LocationRole.IsWarehouse(Rec.Code);
        IsCentralWarehouse := (Rec.Code <> '') and (Rec.Code = LocationRole.CentralWarehouse());
    end;
}
