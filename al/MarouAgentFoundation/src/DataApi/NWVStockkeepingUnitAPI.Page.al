/// <summary>
/// GET /api/naviworld/marouagent/v1.0/companies({id})/nwvStockkeepingUnits
/// Chi doc. Nguong bo sung hang theo tung cua hang nam o day chu khong nam tren Item.
/// Neu Marou khong dung Stockkeeping Unit thi entity nay rong, va do chinh la mot phat hien
/// ve do san sang du lieu, khong phai loi.
/// </summary>
page 70203 "NWV Stockkeeping Unit API"
{
    PageType = API;
    Caption = 'NWV Stockkeeping Unit API';
    APIPublisher = 'naviworld';
    APIGroup = 'marouagent';
    APIVersion = 'v1.0';
    EntityName = 'nwvStockkeepingUnit';
    EntitySetName = 'nwvStockkeepingUnits';
    SourceTable = "Stockkeeping Unit";
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
                field(locationCode; Rec."Location Code") { }
                field(itemNo; Rec."Item No.") { }
                field(variantCode; Rec."Variant Code") { }
                field(description; Rec.Description) { }
                field(replenishmentSystem; Rec."Replenishment System") { }
                field(reorderingPolicy; Rec."Reordering Policy") { }
                field(reorderPoint; Rec."Reorder Point") { }
                field(reorderQuantity; Rec."Reorder Quantity") { }
                field(safetyStockQuantity; Rec."Safety Stock Quantity") { }
                field(maximumInventory; Rec."Maximum Inventory") { }
                field(minimumOrderQuantity; Rec."Minimum Order Quantity") { }
                field(maximumOrderQuantity; Rec."Maximum Order Quantity") { }
                field(orderMultiple; Rec."Order Multiple") { }
                field(transferFromCode; Rec."Transfer-from Code") { }
                field(vendorNo; Rec."Vendor No.") { }
                field(unitCost; Rec."Unit Cost") { }
                field(inventory; Rec.Inventory) { }
                field(qtyOnPurchOrder; Rec."Qty. on Purch. Order") { }
                field(qtyOnSalesOrder; Rec."Qty. on Sales Order") { }
                field(lastDateModified; Rec."Last Date Modified") { }
            }
        }
    }
}
