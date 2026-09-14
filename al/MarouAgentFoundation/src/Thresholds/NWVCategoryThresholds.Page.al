page 70106 "NWV Category Thresholds"
{
    Caption = 'NWV Category Thresholds';
    PageType = List;
    ApplicationArea = All;
    UsageCategory = Administration;
    SourceTable = "NWV Category Threshold";

    layout
    {
        area(Content)
        {
            repeater(Lines)
            {
                field("Item Category Code"; Rec."Item Category Code") { ApplicationArea = All; }
                field("Near Expiry Days"; Rec."Near Expiry Days") { ApplicationArea = All; }
                field("Slow-moving Days"; Rec."Slow-moving Days") { ApplicationArea = All; }
                field("Excess Days"; Rec."Excess Days") { ApplicationArea = All; }
                field("Reason"; Rec."Reason") { ApplicationArea = All; }
            }
        }
    }
}
