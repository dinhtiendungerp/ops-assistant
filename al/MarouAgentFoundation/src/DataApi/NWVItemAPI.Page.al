/// <summary>
/// GET /api/naviworld/marouagent/v1.0/companies({id})/nwvItems
/// Chi doc. API chuan v2.0 co entity items nhung khong phoi cac truong hoach dinh
/// (Reorder Point, Safety Stock Quantity, Reordering Policy, Minimum Order Quantity)
/// va khong phoi Item Tracking Code. Ba thu do la dau vao bat buoc cua UC2.
/// Khong phoi truong kieu DateFormula (Lead Time Calculation, Safety Lead Time),
/// se bo sung o ban sau neu can.
/// </summary>
page 70200 "NWV Item API"
{
    PageType = API;
    Caption = 'NWV Item API';
    APIPublisher = 'naviworld';
    APIGroup = 'marouagent';
    APIVersion = 'v1.0';
    EntityName = 'nwvItem';
    EntitySetName = 'nwvItems';
    SourceTable = Item;
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
                field(itemNo; Rec."No.") { }
                field(description; Rec.Description) { }
                field(itemCategoryCode; Rec."Item Category Code") { }
                field(baseUnitOfMeasure; Rec."Base Unit of Measure") { }
                field(itemTrackingCode; Rec."Item Tracking Code") { }
                field(unitCost; Rec."Unit Cost") { }
                field(unitPrice; Rec."Unit Price") { }
                field(lastDirectCost; Rec."Last Direct Cost") { }
                field(costingMethod; Rec."Costing Method") { }
                field(blocked; Rec.Blocked) { }
                field(replenishmentSystem; Rec."Replenishment System") { }
                field(reorderingPolicy; Rec."Reordering Policy") { }
                field(reorderPoint; Rec."Reorder Point") { }
                field(reorderQuantity; Rec."Reorder Quantity") { }
                field(safetyStockQuantity; Rec."Safety Stock Quantity") { }
                field(maximumInventory; Rec."Maximum Inventory") { }
                field(minimumOrderQuantity; Rec."Minimum Order Quantity") { }
                field(maximumOrderQuantity; Rec."Maximum Order Quantity") { }
                field(orderMultiple; Rec."Order Multiple") { }
                field(vendorNo; Rec."Vendor No.") { }
                field(inventory; Rec.Inventory) { }
                field(qtyOnPurchOrder; Rec."Qty. on Purch. Order") { }
                field(qtyOnSalesOrder; Rec."Qty. on Sales Order") { }
                field(lastDateModified; Rec."Last Date Modified") { }
            }
        }
    }
}
