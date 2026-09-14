/// <summary>
/// GET /api/naviworld/marouagent/v1.0/companies({id})/nwvPurchaseOrderLines
/// Chi doc. Dong don mua loai Item, dung lam nguon cung dang ve. Day la du lieu de tra loi
/// nhan "nguon cung" trong phan loai cau giai thich cua UC2: thieu hang nhung da co hang
/// dang ve thi khong phai la mot lan dut hang.
/// API chuan v2.0 khong co entity nao cho dong don mua.
/// </summary>
page 70206 "NWV Purchase Order Line API"
{
    PageType = API;
    Caption = 'NWV Purchase Order Line API';
    APIPublisher = 'naviworld';
    APIGroup = 'marouagent';
    APIVersion = 'v1.0';
    EntityName = 'nwvPurchaseOrderLine';
    EntitySetName = 'nwvPurchaseOrderLines';
    SourceTable = "Purchase Line";
    SourceTableView = where("Document Type" = const(Order), Type = const(Item));
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
                field(documentNo; Rec."Document No.") { }
                field(lineNo; Rec."Line No.") { }
                field(buyFromVendorNo; Rec."Buy-from Vendor No.") { }
                field(itemNo; Rec."No.") { }
                field(variantCode; Rec."Variant Code") { }
                field(description; Rec.Description) { }
                field(locationCode; Rec."Location Code") { }
                field(quantity; Rec.Quantity) { }
                field(outstandingQuantity; Rec."Outstanding Quantity") { }
                field(quantityReceived; Rec."Quantity Received") { }
                field(unitOfMeasureCode; Rec."Unit of Measure Code") { }
                field(directUnitCost; Rec."Direct Unit Cost") { }
                field(orderDate; Rec."Order Date") { }
                field(expectedReceiptDate; Rec."Expected Receipt Date") { }
                field(plannedReceiptDate; Rec."Planned Receipt Date") { }
                field(lastModifiedDateTime; Rec.SystemModifiedAt) { }
            }
        }
    }
}
