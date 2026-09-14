/// <summary>
/// GET/POST /api/naviworld/marouagent/v1.0/companies({id})/posDiscountLogs
/// POST chi dung cho POC de nap du lieu mau khi chua co LS Adapter. Tren moi truong that, khoa POST bang permission.
/// </summary>
page 70114 "NWV POS Discount Log API"
{
    PageType = API;
    APIPublisher = 'naviworld';
    APIGroup = 'marouagent';
    APIVersion = 'v1.0';
    EntityName = 'posDiscountLog';
    EntitySetName = 'posDiscountLogs';
    SourceTable = "NWV POS Discount Log";
    DelayedInsert = true;
    ODataKeyFields = SystemId;
    Extensible = false;

    layout
    {
        area(Content)
        {
            repeater(Lines)
            {
                field(id; Rec.SystemId) { Editable = false; }
                field(storeNo; Rec."Store No.") { }
                field(posTerminalNo; Rec."POS Terminal No.") { }
                field(transactionNo; Rec."Transaction No.") { }
                field(lineNo; Rec."Line No.") { }
                field(receiptNo; Rec."Receipt No.") { }
                field(transDate; Rec."Trans. Date") { }
                field(transTime; Rec."Trans. Time") { }
                field(staffId; Rec."Staff ID") { }
                field(itemNo; Rec."Item No.") { }
                field(quantity; Rec.Quantity) { }
                field(grossAmount; Rec."Gross Amount") { }
                field(discountAmount; Rec."Discount Amount") { }
                field(discountPct; Rec."Discount %") { }
                field(discountType; Rec."Discount Type") { }
                field(offerNo; Rec."Offer No.") { }
                field(managerOverride; Rec."Manager Override") { }
                field(infocodeReason; Rec."Infocode Reason") { }
                field(memberCardNo; Rec."Member Card No.") { }
                field(sourceSystem; Rec."Source System") { }
                field(sourceEntryKey; Rec."Source Entry Key") { }
            }
        }
    }
}
