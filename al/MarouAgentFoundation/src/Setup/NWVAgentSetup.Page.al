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
                Caption = 'Inventory Health (UC2)';
                field("Sales History Days"; Rec."Sales History Days") { }
                field("Stock-out Risk Days"; Rec."Stock-out Risk Days") { }
                field("Excess Days"; Rec."Excess Days") { }
                field("Slow-moving Days"; Rec."Slow-moving Days") { }
                field("Near Expiry Days"; Rec."Near Expiry Days") { }
                field("Last Inv. Health Run"; Rec."Last Inv. Health Run") { }
            }
            group(Locations)
            {
                Caption = 'Locations (from LS Central)';
                // Read-only: stores and warehouses come from LSC Store, LSC Store Location and LSC Replen. Setup
                // (codeunit NWV Location Role). Nothing to type here; change them on the LS pages.
                field(CentralWarehouse; CentralWarehouse)
                {
                    Caption = 'Central Warehouse';
                    Editable = false;
                    ToolTip = 'Default Central Warehouse from LSC Replen. Setup. Demand at a warehouse is measured as total outflow. Change it on the Replenishment Setup page.';
                }
                field(StoreLocations; StoreLocations)
                {
                    Caption = 'Store Locations';
                    Editable = false;
                    ToolTip = 'Number of locations linked to a store through LSC Store (Location Code) or LSC Store Location. Only these locations are measured for forecast accuracy.';
                }
            }
            group(DiscountGovernance)
            {
                Caption = 'Discount Governance (UC7)';
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
            group(WriteOff)
            {
                Caption = 'Write-off Drafts (UC2)';
                InstructionalText = 'Approving a Write-off proposal creates an unposted Item Journal line in this batch, with lot number and reason code. Accounting reviews and posts it; the agent never posts.';
                field("Write-off Jnl. Template"; Rec."Write-off Jnl. Template") { }
                field("Write-off Jnl. Batch"; Rec."Write-off Jnl. Batch") { }
                field("Write-off Reason Code"; Rec."Write-off Reason Code") { }
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
                ToolTip = 'Recalculate NWV Inv. Health Line for every item and location as of the work date.';
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
                ToolTip = 'Recalculate forecast accuracy (MA28, SWA8, Holt-Winters) and, when Publish LS Forecast is on, write the next days into LSC Forecast Entry.';
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
                ToolTip = 'Recalculate the supplier scorecard (UC3) from posted purchase receipts.';
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
                ToolTip = 'Scan NWV POS Discount Log and create discount exceptions.';
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

    var
        CentralWarehouse: Code[10];
        StoreLocations: Integer;

    trigger OnOpenPage()
    var
        LocationRole: Codeunit "NWV Location Role";
    begin
        Rec.GetRecordOnce();
        CentralWarehouse := LocationRole.CentralWarehouse();
        StoreLocations := LocationRole.StoreCount();
    end;
}
