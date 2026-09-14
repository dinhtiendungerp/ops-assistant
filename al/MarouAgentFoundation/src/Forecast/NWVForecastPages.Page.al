/// <summary>UC1: trang nguoi nghiem thu mo de doi chieu do chinh xac du bao voi so tro ly noi.</summary>
page 70120 "NWV Forecast Accuracy"
{
    Caption = 'NWV Forecast Accuracy';
    PageType = List;
    SourceTable = "NWV Forecast Accuracy";
    ApplicationArea = All;
    UsageCategory = Lists;
    Editable = false;

    layout
    {
        area(Content)
        {
            repeater(Lines)
            {
                field("Item No."; Rec."Item No.") { }
                field("Item Description"; Rec."Item Description") { }
                field("Item Category Code"; Rec."Item Category Code") { }
                field("Location Code"; Rec."Location Code") { }
                field(Method; Rec.Method) { }
                field("WAPE %"; Rec."WAPE %") { StyleExpr = WapeStyle; }
                field("Bias %"; Rec."Bias %") { }
                field("Actual Qty"; Rec."Actual Qty") { }
                field("Forecast Qty"; Rec."Forecast Qty") { }
                field("Daily Level"; Rec."Daily Level") { }
                field("Days Evaluated"; Rec."Days Evaluated") { }
                field("Days Censored"; Rec."Days Censored") { }
                field("Days Excluded"; Rec."Days Excluded") { }
                field("Is Exception"; Rec."Is Exception") { }
                field("Exception Reason"; Rec."Exception Reason") { }
                field("Demand Basis"; Rec."Demand Basis") { }
                field("Holdout From"; Rec."Holdout From") { }
                field("Holdout To"; Rec."Holdout To") { }
                field("Calculated At"; Rec."Calculated At") { }
            }
        }
    }

    actions
    {
        area(Processing)
        {
            action(Recalculate)
            {
                Caption = 'Run Forecast Accuracy';
                ApplicationArea = All;
                Image = Calculate;
                ToolTip = 'Tinh lai do chinh xac du bao baseline theo Work Date.';
                trigger OnAction()
                var
                    Calc: Codeunit "NWV Forecast Accuracy Calc";
                begin
                    Calc.Run();
                    CurrPage.Update(false);
                end;
            }
        }
        area(Navigation)
        {
            action(Daily)
            {
                Caption = 'Forecast vs Actual by Day';
                ApplicationArea = All;
                Image = Line;
                RunObject = page "NWV Forecast Daily";
                RunPageLink = "Item No." = field("Item No."), "Location Code" = field("Location Code"), Method = field(Method);
                ToolTip = 'Du bao va ban thuc te tung ngay trong ky kiem tra.';
            }
        }
    }

    var
        WapeStyle: Text;

    trigger OnAfterGetRecord()
    begin
        if Rec."Is Exception" then
            WapeStyle := 'Unfavorable'
        else
            WapeStyle := 'Standard';
    end;
}

page 70121 "NWV Forecast Daily"
{
    Caption = 'NWV Forecast vs Actual';
    PageType = List;
    SourceTable = "NWV Forecast Daily";
    ApplicationArea = All;
    UsageCategory = None;
    Editable = false;

    layout
    {
        area(Content)
        {
            repeater(Lines)
            {
                field("Item No."; Rec."Item No.") { }
                field("Location Code"; Rec."Location Code") { }
                field(Method; Rec.Method) { }
                field("Date"; Rec."Date") { }
                field("Actual Qty"; Rec."Actual Qty") { }
                field("Forecast Qty"; Rec."Forecast Qty") { }
                field(Censored; Rec.Censored) { }
                field(Excluded; Rec.Excluded) { }
            }
        }
    }
}

/// <summary>GET .../forecastAccuracies. Chi doc.</summary>
page 70122 "NWV Forecast Accuracy API"
{
    PageType = API;
    APIPublisher = 'naviworld';
    APIGroup = 'marouagent';
    APIVersion = 'v1.0';
    EntityName = 'forecastAccuracy';
    EntitySetName = 'forecastAccuracies';
    SourceTable = "NWV Forecast Accuracy";
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
                field(itemNo; Rec."Item No.") { }
                field(locationCode; Rec."Location Code") { }
                field(method; Rec.Method) { }
                field(itemDescription; Rec."Item Description") { }
                field(itemCategoryCode; Rec."Item Category Code") { }
                field(demandBasis; Rec."Demand Basis") { }
                field(holdoutFrom; Rec."Holdout From") { }
                field(holdoutTo; Rec."Holdout To") { }
                field(daysEvaluated; Rec."Days Evaluated") { }
                field(daysCensored; Rec."Days Censored") { }
                field(daysExcluded; Rec."Days Excluded") { }
                field(actualQty; Rec."Actual Qty") { }
                field(forecastQty; Rec."Forecast Qty") { }
                field(absErrorQty; Rec."Abs Error Qty") { }
                field(wapePct; Rec."WAPE %") { }
                field(biasPct; Rec."Bias %") { }
                field(dailyLevel; Rec."Daily Level") { }
                field(modelParameters; Rec."Model Parameters") { }
                field(isException; Rec."Is Exception") { }
                field(exceptionReason; Rec."Exception Reason") { }
                field(calculatedAt; Rec."Calculated At") { }
                field(asOfDate; Rec."As Of Date") { }
            }
        }
    }
}

/// <summary>GET .../forecastDailies. Chi doc.</summary>
page 70123 "NWV Forecast Daily API"
{
    PageType = API;
    APIPublisher = 'naviworld';
    APIGroup = 'marouagent';
    APIVersion = 'v1.0';
    EntityName = 'forecastDaily';
    EntitySetName = 'forecastDailies';
    SourceTable = "NWV Forecast Daily";
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
                field(itemNo; Rec."Item No.") { }
                field(locationCode; Rec."Location Code") { }
                field(method; Rec.Method) { }
                field(date; Rec."Date") { }
                field(actualQty; Rec."Actual Qty") { }
                field(forecastQty; Rec."Forecast Qty") { }
                field(censored; Rec.Censored) { }
                field(excluded; Rec.Excluded) { }
            }
        }
    }
}
