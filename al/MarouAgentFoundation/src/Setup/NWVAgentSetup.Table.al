/// <summary>
/// Thresholds and parameters for the calculation layer. The agent only reads them; business users change them on
/// page "NWV Agent Setup". Stores and warehouses are NOT set here: they come from LS Central (LSC Store, LSC Store
/// Location, LSC Replen. Setup) through codeunit "NWV Location Role".
/// </summary>
table 70100 "NWV Agent Setup"
{
    Caption = 'NWV Agent Setup';
    DataClassification = CustomerContent;

    fields
    {
        field(1; "Primary Key"; Code[10])
        {
            Caption = 'Primary Key';
            DataClassification = SystemMetadata;
        }
        // ---------- Inventory Health ----------
        field(10; "Sales History Days"; Integer)
        {
            Caption = 'Sales History Days';
            InitValue = 90;
            MinValue = 7;
            ToolTip = 'Number of days of sales history (Item Ledger Entry) used to compute the average daily demand.';
        }
        field(11; "Stock-out Risk Days"; Decimal)
        {
            Caption = 'Stock-out Risk Days of Cover';
            InitValue = 7;
            DecimalPlaces = 0 : 1;
            ToolTip = 'Days of cover below this value puts the line in the Stock-out Risk tier.';
        }
        field(12; "Excess Days"; Decimal)
        {
            Caption = 'Excess Days of Cover';
            InitValue = 90;
            DecimalPlaces = 0 : 1;
            ToolTip = 'Days of cover above this value puts the line in the Excess tier.';
        }
        field(13; "Slow-moving Days"; Integer)
        {
            Caption = 'Slow-moving No-Sale Days';
            InitValue = 60;
            ToolTip = 'No sale within this number of days puts the line in the Slow-moving tier.';
        }
        field(14; "Near Expiry Days"; Integer)
        {
            Caption = 'Near Expiry Days';
            InitValue = 45;
            ToolTip = 'A lot whose expiration date falls within this number of days from the work date is Near Expiry. A per-category value on NWV Category Thresholds overrides it.';
        }
        // ---------- Locations: replaced by LS Central master data on 15/09/2026, see codeunit NWV Location Role ----------
        field(22; "Central Warehouse Code"; Code[10])
        {
            Caption = 'Central Warehouse Code';
            TableRelation = Location;
            ObsoleteState = Pending;
            ObsoleteReason = 'Read from LSC Replen. Setup."Default Central Warehouse" and Location."LSC Location is a Warehouse" (codeunit NWV Location Role).';
            ObsoleteTag = '1.5.2';
            ToolTip = 'Obsolete. The central warehouse now comes from LSC Replen. Setup.';
        }
        field(23; "Store Location Filter"; Text[250])
        {
            Caption = 'Store Location Filter';
            ObsoleteState = Pending;
            ObsoleteReason = 'Stores are read from LSC Store and LSC Store Location (codeunit NWV Location Role). This filter was never used by a calculation.';
            ObsoleteTag = '1.5.2';
            ToolTip = 'Obsolete. Store locations now come from LSC Store and LSC Store Location.';
        }
        // ---------- Discount Governance ----------
        field(30; "Max Manual Discount %"; Decimal)
        {
            Caption = 'Max Manual Discount %';
            InitValue = 15;
            DecimalPlaces = 0 : 2;
            ToolTip = 'A manual discount above this percentage creates a High severity exception.';
        }
        field(31; "Manual Disc. Share Warn %"; Decimal)
        {
            Caption = 'Manual Discount Share Warning %';
            InitValue = 20;
            DecimalPlaces = 0 : 2;
            ToolTip = 'Share of one staff member''s daily sales carrying a manual discount above this percentage creates a Medium severity exception.';
        }
        field(32; "Repeat Discount Count"; Integer)
        {
            Caption = 'Repeat Discount Count per Day';
            InitValue = 5;
            ToolTip = 'One staff member using a manual discount more than this many times in a day creates an exception.';
        }
        // ---------- Agent ----------
        field(40; "Agent User Name"; Code[50])
        {
            Caption = 'Agent User Name';
            ToolTip = 'User name (Microsoft Entra application) the agent writes proposals under, so that audit trails separate people from the agent.';
        }
        field(41; "Last Inv. Health Run"; DateTime)
        {
            Caption = 'Last Inventory Health Run';
            Editable = false;
        }
        field(43; "Last Discount Gov. Run"; DateTime)
        {
            Caption = 'Last Discount Governance Run';
            Editable = false;
        }
        field(44; "Last Forecast Run"; DateTime)
        {
            Caption = 'Last Forecast Accuracy Run';
            Editable = false;
        }
        field(45; "Last Supplier Scorecard Run"; DateTime)
        {
            Caption = 'Last Supplier Scorecard Run';
            Editable = false;
        }
        // UC1. An existing Setup record does not receive InitValue, so 0 means default (see the Eff* procedures).
        field(50; "Forecast Holdout Days"; Integer)
        {
            Caption = 'Forecast Holdout Days';
            InitValue = 28;
            MinValue = 0;
            ToolTip = 'Number of trailing days used to measure accuracy: the forecast is built from the history before them and compared with actual sales. 0 = 28.';
        }
        field(51; "Forecast WAPE Warn %"; Decimal)
        {
            Caption = 'Forecast WAPE Warn %';
            InitValue = 50;
            MinValue = 0;
            ToolTip = 'An item x location pair with WAPE above this percentage is listed as an exception. 0 = 50.';
        }
        field(52; "Forecast Bias Warn %"; Decimal)
        {
            Caption = 'Forecast Bias Warn %';
            InitValue = 30;
            MinValue = 0;
            ToolTip = 'A forecast that is consistently high or low by more than this percentage is listed as an exception. 0 = 30.';
        }
        field(53; "Forecast Min Actual Qty"; Decimal)
        {
            Caption = 'Forecast Min Actual Qty';
            InitValue = 20;
            MinValue = 0;
            ToolTip = 'Pairs that sold less than this quantity in the holdout period are not evaluated for exceptions, because WAPE on small numbers is meaningless. 0 = 20.';
        }
        field(54; "Forecast Horizon Days"; Integer)
        {
            Caption = 'Forecast Horizon Days';
            InitValue = 28;
            MinValue = 0;
            ToolTip = 'Number of future days forecast with Holt-Winters and written to LSC Forecast Entry. Must cover lead time plus the LS stock cover days. 0 = 28, maximum 90.';
        }
        field(55; "Publish LS Forecast"; Boolean)
        {
            Caption = 'Publish LS Forecast';
            ToolTip = 'When on, each run writes the Holt-Winters forecast of every store pair to LSC Forecast Entry (existing entries from tomorrow onward are replaced). Items with LSC Replen. Calculation Type = Retail Forecast are replenished from this forecast plus Planned Sales Demand.';
        }
        // UC3
        field(60; "On-time Tolerance Days"; Integer)
        {
            Caption = 'On-time Tolerance Days';
            MinValue = 0;
            ToolTip = 'A receipt this many days after the Expected Receipt Date still counts as on time.';
        }
        field(61; "Supplier On-time Warn %"; Decimal)
        {
            Caption = 'Supplier On-time Warn %';
            InitValue = 80;
            MinValue = 0;
            ToolTip = 'A supplier with an on-time rate below this percentage is flagged for review. 0 = 80.';
        }
        field(62; "Supplier History Days"; Integer)
        {
            Caption = 'Supplier History Days';
            InitValue = 180;
            MinValue = 0;
            ToolTip = 'Only purchase lines with an Expected Receipt Date within this many days are evaluated. 0 = 180.';
        }
        // Write-off (UC2 G2/A3, 16/09/2026): approving a Write-off proposal creates an unposted Item Journal Line
        // (Negative Adjmt.) in this batch. Accounting reviews and posts it; the agent never posts.
        field(70; "Write-off Jnl. Template"; Code[10])
        {
            Caption = 'Write-off Jnl. Template';
            TableRelation = "Item Journal Template" where(Type = const(Item));
            ToolTip = 'Item journal template that receives the draft write-off line when a Write-off proposal is approved. Blank = ITEM.';
        }
        field(71; "Write-off Jnl. Batch"; Code[10])
        {
            Caption = 'Write-off Jnl. Batch';
            TableRelation = "Item Journal Batch".Name where("Journal Template Name" = field("Write-off Jnl. Template"));
            ToolTip = 'Item journal batch that receives the draft write-off line. Blank = AGENT. The batch is created with Item Tracking on Lines so the lot number stays on the line.';
        }
        field(72; "Write-off Reason Code"; Code[10])
        {
            Caption = 'Write-off Reason Code';
            TableRelation = "Reason Code";
            ToolTip = 'Reason code stamped on the draft write-off line. Blank = AGENT-EXP (created if missing).';
        }
    }

    keys
    {
        key(PK; "Primary Key") { Clustered = true; }
    }

    procedure GetRecordOnce()
    begin
        if not Get() then begin
            Init();
            Insert();
        end;
    end;

    procedure EffHoldoutDays(): Integer
    begin
        if "Forecast Holdout Days" <= 0 then
            exit(28);
        if "Forecast Holdout Days" > 100 then     // 500-day array = 365 days of Holt-Winters training + holdout
            exit(100);
        exit("Forecast Holdout Days");
    end;

    procedure EffForecastHorizon(): Integer
    begin
        if "Forecast Horizon Days" <= 0 then
            exit(28);
        if "Forecast Horizon Days" > 90 then
            exit(90);
        exit("Forecast Horizon Days");
    end;

    procedure EffWapeWarn(): Decimal
    begin
        if "Forecast WAPE Warn %" <= 0 then
            exit(50);
        exit("Forecast WAPE Warn %");
    end;

    procedure EffBiasWarn(): Decimal
    begin
        if "Forecast Bias Warn %" <= 0 then
            exit(30);
        exit("Forecast Bias Warn %");
    end;

    procedure EffMinActual(): Decimal
    begin
        if "Forecast Min Actual Qty" <= 0 then
            exit(20);
        exit("Forecast Min Actual Qty");
    end;

    procedure EffOnTimeWarn(): Decimal
    begin
        if "Supplier On-time Warn %" <= 0 then
            exit(80);
        exit("Supplier On-time Warn %");
    end;

    procedure EffSupplierHistoryDays(): Integer
    begin
        if "Supplier History Days" <= 0 then
            exit(180);
        exit("Supplier History Days");
    end;
}
