/// <summary>
/// GET /api/naviworld/marouagent/v1.0/companies({id})/inventoryHealthLines
/// Read-only. Agent loc bang $filter (tier, locationCode, riskScore ge N) va $orderby=riskScore desc.
/// </summary>
page 70110 "NWV Inv. Health API"
{
    PageType = API;
    APIPublisher = 'naviworld';
    APIGroup = 'marouagent';
    APIVersion = 'v1.0';
    EntityName = 'inventoryHealthLine';
    EntitySetName = 'inventoryHealthLines';
    SourceTable = "NWV Inv. Health Line";
    DelayedInsert = true;
    Editable = false;
    ODataKeyFields = SystemId;
    Extensible = false;

    layout
    {
        area(Content)
        {
            repeater(Lines)
            {
                field(id; Rec.SystemId) { }
                field(itemNo; Rec."Item No.") { }
                field(locationCode; Rec."Location Code") { }
                field(lotNo; Rec."Lot No.") { }
                field(itemDescription; Rec."Item Description") { }
                field(itemCategoryCode; Rec."Item Category Code") { }
                field(baseUnitOfMeasure; Rec."Base Unit of Measure") { }
                field(quantityOnHand; Rec."Quantity on Hand") { }
                field(inventoryValue; Rec."Inventory Value") { }
                field(avgDailySalesQty; Rec."Avg Daily Sales Qty") { }
                field(daysOfCover; Rec."Days of Cover") { }
                field(lastSaleDate; Rec."Last Sale Date") { }
                field(daysSinceLastSale; Rec."Days Since Last Sale") { }
                field(expirationDate; Rec."Expiration Date") { }
                field(daysToExpiry; Rec."Days To Expiry") { }
                field(demandBasis; Rec."Demand Basis") { }
                field(daysCensored; Rec."Days Censored") { }
                field(tier; Rec.Tier) { }
                field(riskScore; Rec."Risk Score") { }
                field(riskReason; Rec."Risk Reason") { }
                field(calculatedAt; Rec."Calculated At") { }
                field(asOfDate; Rec."As Of Date") { }
            }
        }
    }
}
