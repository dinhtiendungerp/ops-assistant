/// <summary>UC3: scorecard nha cung cap cho nguoi nghiem thu doi chieu.</summary>
page 70124 "NWV Supplier Scorecard"
{
    Caption = 'NWV Supplier Scorecard';
    PageType = List;
    SourceTable = "NWV Supplier Scorecard";
    ApplicationArea = All;
    UsageCategory = Lists;
    Editable = false;

    layout
    {
        area(Content)
        {
            repeater(Lines)
            {
                field("Vendor No."; Rec."Vendor No.") { }
                field("Vendor Name"; Rec."Vendor Name") { }
                field("Item Category Code"; Rec."Item Category Code") { }
                field("On-time %"; Rec."On-time %") { StyleExpr = OnTimeStyle; }
                field("Lines Due"; Rec."Lines Due") { }
                field("Lines Completed"; Rec."Lines Completed") { }
                field("Lines On Time"; Rec."Lines On Time") { }
                field("First Delivery Complete %"; Rec."First Delivery Complete %") { }
                field("Avg Delay Days"; Rec."Avg Delay Days") { }
                field("Avg Promised Lead Time"; Rec."Avg Promised Lead Time") { }
                field("Avg Actual Lead Time"; Rec."Avg Actual Lead Time") { }
                field("Open Lines"; Rec."Open Lines") { }
                field("Overdue Lines"; Rec."Overdue Lines") { }
                field("Overdue Qty"; Rec."Overdue Qty") { }
                field("Overdue Amount"; Rec."Overdue Amount") { }
                field("Last Receipt Date"; Rec."Last Receipt Date") { }
                field("Needs Attention"; Rec."Needs Attention") { }
                field("Attention Reason"; Rec."Attention Reason") { }
                field("Period From"; Rec."Period From") { }
                field("Period To"; Rec."Period To") { }
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
                Caption = 'Run Supplier Scorecard';
                ApplicationArea = All;
                Image = Calculate;
                ToolTip = 'Tinh lai scorecard nha cung cap theo Work Date.';
                trigger OnAction()
                var
                    Calc: Codeunit "NWV Supplier Scorecard Calc";
                begin
                    Calc.Run();
                    CurrPage.Update(false);
                end;
            }
        }
        area(Navigation)
        {
            action(OpenOrders)
            {
                Caption = 'Purchase Order Lines';
                ApplicationArea = All;
                Image = OrderList;
                RunObject = page "Purchase Lines";
                RunPageLink = "Document Type" = const(Order), "Buy-from Vendor No." = field("Vendor No.");
                ToolTip = 'Dong don mua cua nha cung cap nay.';
            }
        }
    }

    var
        OnTimeStyle: Text;

    trigger OnAfterGetRecord()
    begin
        if Rec."Needs Attention" then
            OnTimeStyle := 'Unfavorable'
        else
            OnTimeStyle := 'Favorable';
    end;
}

/// <summary>GET .../supplierScorecards. Chi doc.</summary>
page 70125 "NWV Supplier Scorecard API"
{
    PageType = API;
    APIPublisher = 'naviworld';
    APIGroup = 'marouagent';
    APIVersion = 'v1.0';
    EntityName = 'supplierScorecard';
    EntitySetName = 'supplierScorecards';
    SourceTable = "NWV Supplier Scorecard";
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
                field(vendorNo; Rec."Vendor No.") { }
                field(itemCategoryCode; Rec."Item Category Code") { }
                field(vendorName; Rec."Vendor Name") { }
                field(periodFrom; Rec."Period From") { }
                field(periodTo; Rec."Period To") { }
                field(linesDue; Rec."Lines Due") { }
                field(linesCompleted; Rec."Lines Completed") { }
                field(linesOnTime; Rec."Lines On Time") { }
                field(onTimePct; Rec."On-time %") { }
                field(firstDeliveryCompletePct; Rec."First Delivery Complete %") { }
                field(avgDelayDays; Rec."Avg Delay Days") { }
                field(avgPromisedLeadTime; Rec."Avg Promised Lead Time") { }
                field(avgActualLeadTime; Rec."Avg Actual Lead Time") { }
                field(openLines; Rec."Open Lines") { }
                field(overdueLines; Rec."Overdue Lines") { }
                field(overdueQty; Rec."Overdue Qty") { }
                field(overdueAmount; Rec."Overdue Amount") { }
                field(lastReceiptDate; Rec."Last Receipt Date") { }
                field(needsAttention; Rec."Needs Attention") { }
                field(attentionReason; Rec."Attention Reason") { }
                field(calculatedAt; Rec."Calculated At") { }
                field(asOfDate; Rec."As Of Date") { }
            }
        }
    }
}

/// <summary>
/// GET .../nwvPurchaseReceiptLines. Chi doc. Dong phieu nhan da post, de ban Python doi chieu scorecard doc lap.
/// </summary>
page 70126 "NWV Purch. Rcpt. Line API"
{
    PageType = API;
    APIPublisher = 'naviworld';
    APIGroup = 'marouagent';
    APIVersion = 'v1.0';
    EntityName = 'nwvPurchaseReceiptLine';
    EntitySetName = 'nwvPurchaseReceiptLines';
    SourceTable = "Purch. Rcpt. Line";
    SourceTableView = where(Type = const(Item));
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
                field(orderNo; Rec."Order No.") { }
                field(orderLineNo; Rec."Order Line No.") { }
                field(buyFromVendorNo; Rec."Buy-from Vendor No.") { }
                field(itemNo; Rec."No.") { }
                field(locationCode; Rec."Location Code") { }
                field(quantity; Rec.Quantity) { }
                field(postingDate; Rec."Posting Date") { }
                field(expectedReceiptDate; Rec."Expected Receipt Date") { }
            }
        }
    }
}
