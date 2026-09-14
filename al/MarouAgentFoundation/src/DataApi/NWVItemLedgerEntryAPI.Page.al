/// <summary>
/// GET /api/naviworld/marouagent/v1.0/companies({id})/nwvItemLedgerEntries
/// Chi doc. Day la ly do phai co extension nay. Resource itemLedgerEntry cua API chuan
/// v2.0 khong co Location Code, Lot No., Expiration Date, Remaining Quantity, nen khong
/// dung duoc cho phan tang ton kho va truy xuat lot.
/// Bang nay lon, luon dat $filter theo postingDate va $top khi goi.
/// </summary>
page 70201 "NWV Item Ledger Entry API"
{
    PageType = API;
    Caption = 'NWV Item Ledger Entry API';
    APIPublisher = 'naviworld';
    APIGroup = 'marouagent';
    APIVersion = 'v1.0';
    EntityName = 'nwvItemLedgerEntry';
    EntitySetName = 'nwvItemLedgerEntries';
    SourceTable = "Item Ledger Entry";
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
                field(entryNo; Rec."Entry No.") { }
                field(postingDate; Rec."Posting Date") { }
                field(entryType; Rec."Entry Type") { }
                field(documentType; Rec."Document Type") { }
                field(documentNo; Rec."Document No.") { }
                field(sourceType; Rec."Source Type") { }
                field(sourceNo; Rec."Source No.") { }
                field(itemNo; Rec."Item No.") { }
                field(itemCategoryCode; Rec."Item Category Code") { }
                field(description; Rec.Description) { }
                field(variantCode; Rec."Variant Code") { }
                field(locationCode; Rec."Location Code") { }
                field(unitOfMeasureCode; Rec."Unit of Measure Code") { }
                field(quantity; Rec.Quantity) { }
                field(invoicedQuantity; Rec."Invoiced Quantity") { }
                field(remainingQuantity; Rec."Remaining Quantity") { }
                field(reservedQuantity; Rec."Reserved Quantity") { }
                field(open; Rec.Open) { }
                field(positive; Rec.Positive) { }
                field(lotNo; Rec."Lot No.") { }
                field(serialNo; Rec."Serial No.") { }
                field(packageNo; Rec."Package No.") { }
                field(expirationDate; Rec."Expiration Date") { }
                field(warrantyDate; Rec."Warranty Date") { }
                field(costAmountActual; Rec."Cost Amount (Actual)") { }
                field(salesAmountActual; Rec."Sales Amount (Actual)") { }
                field(globalDimension1Code; Rec."Global Dimension 1 Code") { }
                field(globalDimension2Code; Rec."Global Dimension 2 Code") { }
                field(orderType; Rec."Order Type") { }
                field(orderNo; Rec."Order No.") { }
                field(correction; Rec.Correction) { }
                field(lastModifiedDateTime; Rec.SystemModifiedAt) { }
            }
        }
    }
}
