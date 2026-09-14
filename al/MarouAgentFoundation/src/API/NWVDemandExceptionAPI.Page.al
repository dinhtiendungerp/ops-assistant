/// <summary>
/// GET va POST /api/naviworld/marouagent/v1.0/companies({id})/demandExceptions
/// Day la duong tro ly ghi lai chuyen ma nguoi van hanh vua ke: mot su kien mot lan,
/// kem khoang ngay. Ghi duoc, khong xoa duoc, vi day la vet kiem toan cho viec tinh lai nhu cau.
/// </summary>
page 70116 "NWV Demand Exception API"
{
    PageType = API;
    APIPublisher = 'naviworld';
    APIGroup = 'marouagent';
    APIVersion = 'v1.0';
    EntityName = 'demandException';
    EntitySetName = 'demandExceptions';
    SourceTable = "NWV Demand Exception";
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
                field(id; Rec.SystemId) { }
                field(entryNo; Rec."Entry No.") { Editable = false; }
                field(itemNo; Rec."Item No.") { }
                field(locationCode; Rec."Location Code") { }
                field(fromDate; Rec."From Date") { }
                field(toDate; Rec."To Date") { }
                field(reason; Rec."Reason") { }
                field(excludeFromDemand; Rec."Exclude From Demand") { }
                field(registeredBy; Rec."Registered By") { Editable = false; }
                field(registeredAt; Rec."Registered At") { Editable = false; }
            }
        }
    }
}
