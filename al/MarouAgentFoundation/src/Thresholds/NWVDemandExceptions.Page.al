page 70107 "NWV Demand Exceptions"
{
    Caption = 'NWV Demand Exceptions';
    PageType = List;
    ApplicationArea = All;
    UsageCategory = Lists;
    SourceTable = "NWV Demand Exception";

    layout
    {
        area(Content)
        {
            repeater(Lines)
            {
                field("Item No."; Rec."Item No.") { ApplicationArea = All; }
                field("Location Code"; Rec."Location Code") { ApplicationArea = All; }
                field("From Date"; Rec."From Date") { ApplicationArea = All; }
                field("To Date"; Rec."To Date") { ApplicationArea = All; }
                field("Reason"; Rec."Reason") { ApplicationArea = All; }
                field("Exclude From Demand"; Rec."Exclude From Demand") { ApplicationArea = All; }
                field("Registered By"; Rec."Registered By") { ApplicationArea = All; }
                field("Registered At"; Rec."Registered At") { ApplicationArea = All; }
            }
        }
    }
}
