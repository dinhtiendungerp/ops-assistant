/// <summary>
/// UC1: tro ly doc ket qua tinh cua module Replenishment LS Central, KHONG tu tinh lai.
/// Truoc 1.1.0.0 nam o app rieng NWV Marou Agent LS Adapter; da gop vao app san pham ngay 13/09/2026.
///
/// Ten bang va field doc tu source LS Central 28.0.10.3586 (AL/Marou/unpacked), khong doan:
///   10012205 "LSC Replen. Item Quantity"  anh chup ton, dang ve, ban binh quan theo Item x Variant x Location
///   10012201 "LSC Replen. Template"       loai Purchase / Transfer / Redistribution
///   10012202 "LSC Replen. Journal Batch"  mot lan tinh cua journal
///   10012203 "LSC Replen. Journal Lines"  tong theo mat hang
///   10012204 "LSC Replen. Jrnl. Details"  so theo tung cua hang: ton hieu dung, ban binh quan, so ngay phu,
///                                          so he thong de xuat va so nguoi mua hang da sua
/// Tat ca chi doc. Master data va cac nut tinh di qua codeunit "NWV Replen. Service".
/// </summary>
page 70270 "NWV Replen. Item Qty API"
{
    PageType = API;
    APIPublisher = 'naviworld';
    APIGroup = 'marouagent';
    APIVersion = 'v1.0';
    EntityName = 'replenItemQuantity';
    EntitySetName = 'replenItemQuantities';
    SourceTable = "LSC Replen. Item Quantity";
    Editable = false;
    DataAccessIntent = ReadOnly;
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
                field(itemNo; Rec."Item No.") { }
                field(variantCode; Rec."Variant Code") { }
                field(locationCode; Rec."Location Code") { }
                field(inventory; Rec.Inventory) { }
                field(quantityOnPurchaseOrder; Rec."Quantity on Purchase Order") { }
                field(quantityOnSalesOrder; Rec."Quantity on Sales Order") { }
                field(quantityInTransferIn; Rec."Quantity in Transfer In") { }
                field(quantityInTransferOut; Rec."Quantity in Transfer Out") { }
                field(qtySoldNotPosted; Rec."Qty. Sold not Posted") { }
                field(dailySales; Rec."Daily Sales") { }
                field(salesDateFrom; Rec."Sales Date From") { }
                field(salesDateTo; Rec."Sales Date To") { }
                field(noOfSalesDates; Rec."No. of Sales Dates") { }
                field(noOfDaysOutOfStock; Rec."No. of Days Out of Stock") { }
                field(noOfClosedDaysNotOOS; Rec."No. of Closed Days Not OOS") { }
                field(dateOfFirstSale; Rec."Date of First Sale") { }
                field(replenishFromWarehouse; Rec."Replenish From Warehouse") { }
                field(itemCategoryCode; Rec."Item Category Code") { }
                field(vendorNo; Rec."Vendor No.") { }
                field(replenishmentCalculationType; Rec."Replenishment Calculation Type") { }
                field(storeStockCoverReqdDays; Rec."Store Stock Cover Reqd (Days)") { }
                field(warehStockCoverReqdDays; Rec."Wareh Stock Cover Reqd (Days)") { }
                field(isAWhse; Rec."Is a Whse") { }
                field(blocked; Rec.Blocked) { }
                field(poBlocked; Rec."PO Blocked") { }
                field(toBlocked; Rec."TO Blocked") { }
                field(dateModified; Rec."Date Modified") { }
            }
        }
    }
}

page 70271 "NWV Replen. Template API"
{
    PageType = API;
    APIPublisher = 'naviworld';
    APIGroup = 'marouagent';
    APIVersion = 'v1.0';
    EntityName = 'replenTemplate';
    EntitySetName = 'replenTemplates';
    SourceTable = "LSC Replen. Template";
    Editable = false;
    DataAccessIntent = ReadOnly;
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
                field(code; Rec."Code") { }
                field(description; Rec.Description) { }
                field(replenishmentType; Rec."Replenishment Type") { }
                field(templateType; Rec."Template Type") { }
                field(locationCode; Rec."Location Code") { }
                field(buyerId; Rec."Buyer ID") { }
                field(createOrdersAutomatically; Rec."Create Orders Automatically") { }
            }
        }
    }
}

page 70272 "NWV Replen. Jnl. Batch API"
{
    PageType = API;
    APIPublisher = 'naviworld';
    APIGroup = 'marouagent';
    APIVersion = 'v1.0';
    EntityName = 'replenJournalBatch';
    EntitySetName = 'replenJournalBatches';
    SourceTable = "LSC Replen. Journal Batch";
    Editable = false;
    DataAccessIntent = ReadOnly;
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
                field(replenishmentTemplateCode; Rec."Replenishment Template Code") { }
                field(batchNo; Rec."Batch No.") { }
                field(description; Rec.Description) { }
                field(noOfLines; Rec."No. of Lines") { }
                field(lastRunDate; Rec."Last Run Date") { }
                field(lastRunTime; Rec."Last Run Time") { }
                field(nextRunDate; Rec."Next Run Date") { }
                field(runFrequency; Rec."Run Frequency") { }
                field(buyerId; Rec."Buyer ID") { }
                field(calculationStatus; Rec."Calculation Status") { }
                field(calculationMessage; Rec."Calculation Message") { }
            }
        }
    }
}

page 70273 "NWV Replen. Jnl. Line API"
{
    PageType = API;
    APIPublisher = 'naviworld';
    APIGroup = 'marouagent';
    APIVersion = 'v1.0';
    EntityName = 'replenJournalLine';
    EntitySetName = 'replenJournalLines';
    SourceTable = "LSC Replen. Journal Lines";
    Editable = false;
    DataAccessIntent = ReadOnly;
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
                field(replenishmentTemplateCode; Rec."Replenishment Template Code") { }
                field(batchNo; Rec."Batch No.") { }
                field(lineNo; Rec."Line No.") { }
                field(itemNo; Rec."Item No.") { }
                field(description; Rec.Description) { }
                field(systemSuggestedQuantity; Rec."System Suggested Quantity") { }
                field(quantity; Rec.Quantity) { }
                field(unitOfMeasureCode; Rec."Unit of Measure Code") { }
                field(warehouseLocationCode; Rec."Warehouse Location Code") { }
                field(storeEffectiveInventory; Rec."Store Effective Inventory") { }
                field(warehouseEffectiveInventory; Rec."Warehouse Effective Inventory") { }
                field(vendorNo; Rec."Vendor No.") { }
                field(costAmount; Rec."Cost Amount") { }
                field(noOfJournalDetailLines; Rec."No. of Journal Detail Lines") { }
            }
        }
    }
}

page 70274 "NWV Replen. Jnl. Detail API"
{
    PageType = API;
    APIPublisher = 'naviworld';
    APIGroup = 'marouagent';
    APIVersion = 'v1.0';
    EntityName = 'replenJournalDetail';
    EntitySetName = 'replenJournalDetails';
    SourceTable = "LSC Replen. Jrnl. Details";
    Editable = false;
    DataAccessIntent = ReadOnly;
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
                field(replenishmentTemplateCode; Rec."Replenishment Template Code") { }
                field(batchNo; Rec."Batch No.") { }
                field(lineNo; Rec."Line No.") { }
                field(detailLineNo; Rec."Detail Line No.") { }
                field(itemNo; Rec."Item No.") { }
                field(variantCode; Rec."Variant Code") { }
                field(description; Rec.Description) { }
                field(locationCode; Rec."Location Code") { }
                field(replenishmentLocationCode; Rec."Replenishment Location Code") { }
                field(calculationType; Rec."Calculation Type") { }
                field(systemSuggestedQuantity; Rec."System Suggested Quantity") { }
                field(quantity; Rec.Quantity) { }
                field(effectiveInventory; Rec."Effective Inventory") { }
                field(averageDailySales; Rec."Average Daily Sales") { }
                field(requiredCoverageDays; Rec."Required Coverage Days") { }
                field(noOfClosedDays; Rec."No. of Closed Days") { }
                field(leadTimeSalesQuantity; Rec."Lead Time Sales Quantity") { }
                field(forwardSalesForecastFactor; Rec."Forward Sales Forecast Factor") { }
                field(projectedEffInventory; Rec."Projected Eff. Inventory") { }
                field(warehouseEffectiveInventory; Rec."Warehouse Effective Inventory") { }
                field(decision; Rec.Decision) { }
                field(vendorNo; Rec."Vendor No.") { }
                field(directUnitCost; Rec."Direct Unit Cost") { }
                field(costAmount; Rec."Cost Amount") { }
                field(thresholdExceptionExists; Rec."Threshold Exception Exists") { }
                field(plannedStockDemand; Rec."Planned Stock Demand") { }
            }
        }
    }
}

/// Dong giai thich LS tu ghi khi tinh journal, vd "System Suggested Quantity(82) = Daily Sales(11.675) * Store Stock
/// Cover Reqd (Days)(7) * Forward Sales Forecast Factor(1) - Effective Inventory(0)". Tro ly trich nguyen van.
page 70279 "NWV Replen. Calc. Log API"
{
    PageType = API;
    APIPublisher = 'naviworld';
    APIGroup = 'marouagent';
    APIVersion = 'v1.0';
    EntityName = 'replenCalcLogLine';
    EntitySetName = 'replenCalcLogLines';
    SourceTable = "LSC Replen. Calc. Log Lines V2";
    Editable = false;
    DataAccessIntent = ReadOnly;
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
                field(replenishmentTemplateCode; Rec."Replenishment Template Code") { }
                field(batchNo; Rec."Batch No.") { }
                field(entryNo; Rec."Entry No.") { }
                field(itemNo; Rec."Item No.") { }
                field(variantCode; Rec."Variant Code") { }
                field(locationCode; Rec."Location Code") { }
                field(replenishmentBatchLineNo; Rec."Replenishment Batch Line No.") { }
                field(messageText; Rec."Message Text") { }
                field(dateInserted; Rec."Date Inserted") { }
            }
        }
    }
}

/// Tham so replenishment tren Item (cac field LSC). Day la cho Marou chinh so ngay phu ton, sales profile, boi so.
page 70280 "NWV Replen. Item Param. API"
{
    PageType = API;
    APIPublisher = 'naviworld';
    APIGroup = 'marouagent';
    APIVersion = 'v1.0';
    EntityName = 'replenItemParameter';
    EntitySetName = 'replenItemParameters';
    SourceTable = Item;
    Editable = false;
    DataAccessIntent = ReadOnly;
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
                field(replenCalculationType; Rec."LSC Replen. Calculation Type") { }
                field(replenDataProfile; Rec."LSC Replen. Data Profile") { }
                field(salesProfile; Rec."LSC Replenishment Sales Prof") { }
                field(storeStockCoverDays; Rec."LSC Store Stock Cover Reqd (D)") { }
                field(warehStockCoverDays; Rec."LSC Wareh Stock Cover Reqd (D)") { }
                field(manualEstDailySale; Rec."LSC Manual Est. Daily Sale") { }
                field(transferMultiple; Rec."LSC Transfer Multiple") { }
                field(orderMultiple; Rec."Order Multiple") { }
                field(reorderPoint; Rec."Reorder Point") { }
                field(maximumInventory; Rec."Maximum Inventory") { }
                field(excludeFromReplenishment; Rec."LSC Exclude from Replenishment") { }
                field(considerConsumptionAsSales; Rec."LSC Consider Consumpt as Sales") { }
                field(vendorNo; Rec."Vendor No.") { }
            }
        }
    }
}

/// Dong Sales Profile: cua so ngay va trong so LS dung de tinh ban binh quan.
page 70281 "NWV Replen. Sales Prof. API"
{
    PageType = API;
    APIPublisher = 'naviworld';
    APIGroup = 'marouagent';
    APIVersion = 'v1.0';
    EntityName = 'replenSalesProfileLine';
    EntitySetName = 'replenSalesProfileLines';
    SourceTable = "LSC Replen. Sales Profile Line";
    Editable = false;
    DataAccessIntent = ReadOnly;
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
                field(salesProfileCode; Rec."Replenishm. Sales Profile Code") { }
                field(lineNo; Rec."Line No.") { }
                field(startDateFormula; Rec."Date Formula for Start Date") { }
                field(endDateFormula; Rec."Date Formula for End Date") { }
                field(weight; Rec.Weight) { }
            }
        }
    }
}
