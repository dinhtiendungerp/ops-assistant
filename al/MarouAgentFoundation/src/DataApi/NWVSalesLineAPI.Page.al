/// <summary>
/// GET /api/naviworld/marouagent/v1.0/companies({id})/nwvSalesOrderLines
/// Chi doc. Dong don ban loai Item con mo, tuc nhu cau da cam ket nhung chua giao.
/// Dung de tru ra ton kha dung that su, khong phai ton so sach.
/// </summary>
page 70207 "NWV Sales Order Line API"
{
    PageType = API;
    Caption = 'NWV Sales Order Line API';
    APIPublisher = 'naviworld';
    APIGroup = 'marouagent';
    APIVersion = 'v1.0';
    EntityName = 'nwvSalesOrderLine';
    EntitySetName = 'nwvSalesOrderLines';
    SourceTable = "Sales Line";
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
                field(sellToCustomerNo; Rec."Sell-to Customer No.") { }
                field(itemNo; Rec."No.") { }
                field(variantCode; Rec."Variant Code") { }
                field(description; Rec.Description) { }
                field(locationCode; Rec."Location Code") { }
                field(quantity; Rec.Quantity) { }
                field(outstandingQuantity; Rec."Outstanding Quantity") { }
                field(quantityShipped; Rec."Quantity Shipped") { }
                field(unitOfMeasureCode; Rec."Unit of Measure Code") { }
                field(unitPrice; Rec."Unit Price") { }
                field(shipmentDate; Rec."Shipment Date") { }
                field(lastModifiedDateTime; Rec.SystemModifiedAt) { }
            }
        }
    }
}
