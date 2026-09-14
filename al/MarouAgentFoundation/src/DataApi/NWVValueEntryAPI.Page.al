/// <summary>
/// GET /api/naviworld/marouagent/v1.0/companies({id})/nwvValueEntries
/// Chi doc. Gia von va doanh thu thuc te theo tung lan xuat, dung cho use case bien loi
/// nhuan ban le. Tach khoi Item Ledger Entry vi mot dong ILE co the sinh nhieu Value Entry
/// (dieu chinh gia von, item charge), lay so tien tren ILE se thieu.
/// Bang nay lon, luon dat $filter theo postingDate va $top khi goi.
/// </summary>
page 70208 "NWV Value Entry API"
{
    PageType = API;
    Caption = 'NWV Value Entry API';
    APIPublisher = 'naviworld';
    APIGroup = 'marouagent';
    APIVersion = 'v1.0';
    EntityName = 'nwvValueEntry';
    EntitySetName = 'nwvValueEntries';
    SourceTable = "Value Entry";
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
                field(itemLedgerEntryNo; Rec."Item Ledger Entry No.") { }
                field(postingDate; Rec."Posting Date") { }
                field(itemLedgerEntryType; Rec."Item Ledger Entry Type") { }
                field(entryType; Rec."Entry Type") { }
                field(documentNo; Rec."Document No.") { }
                field(sourceType; Rec."Source Type") { }
                field(sourceNo; Rec."Source No.") { }
                field(itemNo; Rec."Item No.") { }
                field(variantCode; Rec."Variant Code") { }
                field(locationCode; Rec."Location Code") { }
                field(itemChargeNo; Rec."Item Charge No.") { }
                field(valuedQuantity; Rec."Valued Quantity") { }
                field(invoicedQuantity; Rec."Invoiced Quantity") { }
                field(costAmountActual; Rec."Cost Amount (Actual)") { }
                field(costAmountExpected; Rec."Cost Amount (Expected)") { }
                field(salesAmountActual; Rec."Sales Amount (Actual)") { }
                field(discountAmount; Rec."Discount Amount") { }
                field(globalDimension1Code; Rec."Global Dimension 1 Code") { }
                field(globalDimension2Code; Rec."Global Dimension 2 Code") { }
                field(lastModifiedDateTime; Rec.SystemModifiedAt) { }
            }
        }
    }
}
