/// <summary>
/// Du bao cho cac ngay toi trong bang chuan LSC Forecast Entry (Retail Forecast Entry) cua LS Central.
/// NWV Forecast Accuracy Calc ghi vao day khi bat Publish LS Forecast; LS Replenishment kieu Retail Forecast doc bang nay.
/// Chi doc.
/// </summary>
page 70282 "NWV LS Forecast Entry API"
{
    PageType = API;
    APIPublisher = 'naviworld';
    APIGroup = 'marouagent';
    APIVersion = 'v1.0';
    EntityName = 'lsForecastEntry';
    EntitySetName = 'lsForecastEntries';
    SourceTable = "LSC Forecast Entry";
    DelayedInsert = true;
    Editable = false;
    InsertAllowed = false;
    ModifyAllowed = false;
    DeleteAllowed = false;
    DataAccessIntent = ReadOnly;
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
                field(date; Rec.Date) { }
                field(forecastQuantity; Rec."Forecast Quantity") { }
                field(forecastQuantityLower; Rec."Forecast Quantity (Lower)") { }
                field(forecastQuantityUpper; Rec."Forecast Quantity (Upper)") { }
                field(forecastQualityPct; Rec."Forecast Quality %") { }
            }
        }
    }
}

/// <summary>
/// Lich su kien va khuyen mai chuan cua LS (LSC Replen. Planned Sales Dem., gan voi LSC Replen. Planned Event).
/// Ngay co dong Enabled bi bo khoi du lieu hoc va phep do sai so cua du bao. Chi doc.
/// </summary>
page 70283 "NWV Planned Sales Demand API"
{
    PageType = API;
    APIPublisher = 'naviworld';
    APIGroup = 'marouagent';
    APIVersion = 'v1.0';
    EntityName = 'plannedSalesDemand';
    EntitySetName = 'plannedSalesDemands';
    SourceTable = "LSC Replen. Planned Sales Dem.";
    DelayedInsert = true;
    Editable = false;
    InsertAllowed = false;
    ModifyAllowed = false;
    DeleteAllowed = false;
    DataAccessIntent = ReadOnly;
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
                field(date; Rec.Date) { }
                field(lineNo; Rec."Line No.") { }
                field(plannedDemand; Rec."Planned Demand") { }
                field(plannedDemandType; Rec."Planned Demand Type") { }
                field(plannedDemandEvent; Rec."Planned Demand Event") { }
                field(status; Rec.Status) { }
            }
        }
    }
}
