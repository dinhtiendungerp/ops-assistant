page 70100 "NWV Agent Setup"
{
    Caption = 'NWV Agent Setup';
    PageType = Card;
    SourceTable = "NWV Agent Setup";
    ApplicationArea = All;
    UsageCategory = Administration;
    InsertAllowed = false;
    DeleteAllowed = false;

    layout
    {
        area(Content)
        {
            group(InventoryHealth)
            {
                Caption = 'Inventory Health';
                field("Sales History Days"; Rec."Sales History Days") { }
                field("Stock-out Risk Days"; Rec."Stock-out Risk Days") { }
                field("Excess Days"; Rec."Excess Days") { }
                field("Slow-moving Days"; Rec."Slow-moving Days") { }
                field("Near Expiry Days"; Rec."Near Expiry Days") { }
                field("Last Inv. Health Run"; Rec."Last Inv. Health Run") { }
            }
            group(Locations)
            {
                Caption = 'Dia diem';
                // De xuat bo sung cua hang lay tu LS Replenishment (template MAROU-TO), khong con nguong o day.
                field("Central Warehouse Code"; Rec."Central Warehouse Code") { }
                field("Store Location Filter"; Rec."Store Location Filter") { }
            }
            group(DiscountGovernance)
            {
                Caption = 'Discount Governance';
                field("Max Manual Discount %"; Rec."Max Manual Discount %") { }
                field("Manual Disc. Share Warn %"; Rec."Manual Disc. Share Warn %") { }
                field("Repeat Discount Count"; Rec."Repeat Discount Count") { }
                field("Last Discount Gov. Run"; Rec."Last Discount Gov. Run") { }
            }
            group(Forecast)
            {
                Caption = 'Demand Forecast (UC1)';
                field("Forecast Holdout Days"; Rec."Forecast Holdout Days") { }
                field("Forecast WAPE Warn %"; Rec."Forecast WAPE Warn %") { }
                field("Forecast Bias Warn %"; Rec."Forecast Bias Warn %") { }
                field("Forecast Min Actual Qty"; Rec."Forecast Min Actual Qty") { }
                field("Forecast Horizon Days"; Rec."Forecast Horizon Days") { }
                field("Publish LS Forecast"; Rec."Publish LS Forecast") { }
                field("Last Forecast Run"; Rec."Last Forecast Run") { }
            }
            group(Supplier)
            {
                Caption = 'Supplier Performance (UC3)';
                field("On-time Tolerance Days"; Rec."On-time Tolerance Days") { }
                field("Supplier On-time Warn %"; Rec."Supplier On-time Warn %") { }
                field("Supplier History Days"; Rec."Supplier History Days") { }
                field("Last Supplier Scorecard Run"; Rec."Last Supplier Scorecard Run") { }
            }
            group(Agent)
            {
                Caption = 'Agent';
                field("Agent User Name"; Rec."Agent User Name") { }
            }
        }
    }

    actions
    {
        area(Processing)
        {
            action(RunInventoryHealth)
            {
                Caption = 'Run Inventory Health';
                ApplicationArea = All;
                Image = Calculate;
                ToolTip = 'Tinh lai bang NWV Inv. Health Line cho toan bo item/location.';
                trigger OnAction()
                var
                    Calc: Codeunit "NWV Inv. Health Calc";
                begin
                    Calc.Run();
                    CurrPage.Update(false);
                end;
            }
            action(RunForecast)
            {
                Caption = 'Run Forecast Accuracy';
                ApplicationArea = All;
                Image = Calculate;
                ToolTip = 'Tinh lai do chinh xac du bao baseline (UC1).';
                trigger OnAction()
                var
                    Calc: Codeunit "NWV Forecast Accuracy Calc";
                begin
                    Calc.Run();
                    CurrPage.Update(false);
                end;
            }
            action(RunSupplier)
            {
                Caption = 'Run Supplier Scorecard';
                ApplicationArea = All;
                Image = Calculate;
                ToolTip = 'Tinh lai scorecard nha cung cap (UC3).';
                trigger OnAction()
                var
                    Calc: Codeunit "NWV Supplier Scorecard Calc";
                begin
                    Calc.Run();
                    CurrPage.Update(false);
                end;
            }
            action(RunDiscountGov)
            {
                Caption = 'Run Discount Governance';
                ApplicationArea = All;
                Image = Calculate;
                ToolTip = 'Quet NWV POS Discount Log va tao exception.';
                trigger OnAction()
                var
                    Calc: Codeunit "NWV Discount Gov. Calc";
                begin
                    Calc.Run();
                    CurrPage.Update(false);
                end;
            }
        }
    }

    trigger OnOpenPage()
    begin
        Rec.GetRecordOnce();
    end;
}
