/// <summary>
/// Chuong trinh khuyen mai chuan cua LS Central, chi doc, cho tro ly tra loi "CTKM nao dang chay, sap toi".
///   LSC Periodic Discount (99001453): dau chuong trinh, loai (Multibuy, Mix and Match, Disc. Offer...), trang thai,
///     nhom gia ap dung (Price Group), Validation Period quyet dinh ngay bat dau va ket thuc.
///   LSC Periodic Discount Line (99001454): mat hang, nhom hang hoac tat ca ma chuong trinh ap vao.
///   LSC Store Price Group (99001575): cua hang nao thuoc nhom gia nao. Chuong trinh khong co Price Group thi ap moi cua hang.
///   LSC Replen. Planned Event: Source Type = Discount va Source Code = so chuong trinh la cach chuan cua LS de
///     Replenishment biet chuong trinh (bao cao Update Planned Sales Demand from Discount sinh dong nhu cau).
/// </summary>
page 70284 "NWV LS Periodic Discount API"
{
    PageType = API;
    APIPublisher = 'naviworld';
    APIGroup = 'marouagent';
    APIVersion = 'v1.0';
    EntityName = 'lsPeriodicDiscount';
    EntitySetName = 'lsPeriodicDiscounts';
    SourceTable = "LSC Periodic Discount";
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
                field(no; Rec."No.") { }
                field(description; Rec.Description) { }
                field(status; Rec.Status) { }
                field(type; Rec.Type) { }
                field(discountType; Rec."Discount Type") { }
                field(priceGroup; Rec."Price Group") { }
                field(priority; Rec.Priority) { }
                field(validationPeriodId; Rec."Validation Period ID") { }
                field(validationDescription; Rec."Validation Description") { }
                field(startingDate; Rec."Starting Date") { }
                field(endingDate; Rec."Ending Date") { }
                field(discountPctValue; Rec."Discount % Value") { }
                field(dealPriceValue; Rec."Deal Price Value") { }
                field(discountAmountValue; Rec."Discount Amount Value") { }
                field(noOfLinesToTrigger; Rec."No. of Lines to Trigger") { }
                field(amountToTrigger; Rec."Amount to Trigger") { }
                field(memberType; Rec."Member Type") { }
                field(memberValue; Rec."Member Value") { }
                field(couponCode; Rec."Coupon Code") { }
                field(plannedDemandType; Rec."Planned Demand Type") { }
                field(plannedDemand; Rec."Planned Demand") { }
                field(lastDateModified; Rec."Last Date Modified") { }
            }
        }
    }
}

page 70285 "NWV LS Periodic Disc. Line API"
{
    PageType = API;
    APIPublisher = 'naviworld';
    APIGroup = 'marouagent';
    APIVersion = 'v1.0';
    EntityName = 'lsPeriodicDiscountLine';
    EntitySetName = 'lsPeriodicDiscountLines';
    SourceTable = "LSC Periodic Discount Line";
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
                field(offerNo; Rec."Offer No.") { }
                field(lineNo; Rec."Line No.") { }
                field(type; Rec.Type) { }
                field(no; Rec."No.") { }
                field(variantCode; Rec."Variant Code") { }
                field(description; Rec.Description) { }
                field(unitOfMeasure; Rec."Unit of Measure") { }
                field(standardPrice; Rec."Standard Price") { }
                field(dealPriceDiscPct; Rec."Deal Price/Disc. %") { }
                field(discType; Rec."Disc. Type") { }
                field(offerPrice; Rec."Offer Price") { }
                field(discountAmount; Rec."Discount Amount") { }
                field(lineGroup; Rec."Line Group") { }
                field(noOfItemsNeeded; Rec."No. of Items Needed") { }
                field(exclude; Rec.Exclude) { }
                field(status; Rec.Status) { }
                field(headerType; Rec."Header Type") { }
                field(plannedDemandType; Rec."Planned Demand Type") { }
                field(plannedDemand; Rec."Planned Demand") { }
            }
        }
    }
}

page 70286 "NWV LS Store Price Group API"
{
    PageType = API;
    APIPublisher = 'naviworld';
    APIGroup = 'marouagent';
    APIVersion = 'v1.0';
    EntityName = 'lsStorePriceGroup';
    EntitySetName = 'lsStorePriceGroups';
    SourceTable = "LSC Store Price Group";
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
                field(store; Rec.Store) { }
                field(priceGroupCode; Rec."Price Group Code") { }
                field(priority; Rec.Priority) { }
            }
        }
    }
}

page 70287 "NWV LS Planned Event API"
{
    PageType = API;
    APIPublisher = 'naviworld';
    APIGroup = 'marouagent';
    APIVersion = 'v1.0';
    EntityName = 'plannedEvent';
    EntitySetName = 'plannedEvents';
    SourceTable = "LSC Replen. Planned Event";
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
                field(eventCode; Rec."Event Code") { }
                field(description; Rec.Description) { }
                field(startDate; Rec."Start Date") { }
                field(endDate; Rec."End Date") { }
                field(status; Rec.Status) { }
                field(noOfLines; Rec."No. of Lines") { }
                field(sourceType; Rec."Source Type") { }
                field(sourceCode; Rec."Source Code") { }
            }
        }
    }
}

/// <summary>
/// LSC Validation Period: ngay va gio chuong trinh co hieu luc (vi du chi 19h-22h). Chi doc.
/// </summary>
page 70288 "NWV LS Validation Period API"
{
    PageType = API;
    APIPublisher = 'naviworld';
    APIGroup = 'marouagent';
    APIVersion = 'v1.0';
    EntityName = 'lsValidationPeriod';
    EntitySetName = 'lsValidationPeriods';
    SourceTable = "LSC Validation Period";
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
                field(validationId; Rec.ID) { }
                field(description; Rec.Description) { }
                field(startingDate; Rec."Starting Date") { }
                field(endingDate; Rec."Ending Date") { }
                field(startingTime; Rec."Starting Time") { }
                field(endingTime; Rec."Ending Time") { }
            }
        }
    }
}
