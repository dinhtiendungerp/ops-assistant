/// <summary>
/// Nguong va tham so cho lop logic. Agent khong duoc doi nguong, chi doc.
/// Nguoi nghiep vu doi nguong tren page "NWV Agent Setup".
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
            ToolTip = 'So ngay lich su ban (Item Ledger Entry, Entry Type = Sale) dung de tinh toc do ban binh quan.';
        }
        field(11; "Stock-out Risk Days"; Decimal)
        {
            Caption = 'Stock-out Risk Days of Cover';
            InitValue = 7;
            DecimalPlaces = 0 : 1;
            ToolTip = 'Days of cover nho hon nguong nay thi xep vao Stock-out Risk.';
        }
        field(12; "Excess Days"; Decimal)
        {
            Caption = 'Excess Days of Cover';
            InitValue = 90;
            DecimalPlaces = 0 : 1;
            ToolTip = 'Days of cover lon hon nguong nay thi xep vao Excess.';
        }
        field(13; "Slow-moving Days"; Integer)
        {
            Caption = 'Slow-moving No-Sale Days';
            InitValue = 60;
            ToolTip = 'Khong co dong ban nao trong so ngay nay thi xep vao Slow-moving.';
        }
        field(14; "Near Expiry Days"; Integer)
        {
            Caption = 'Near Expiry Days';
            InitValue = 45;
            ToolTip = 'Lot co Expiration Date trong vong so ngay nay tinh tu hom nay thi xep vao Near Expiry.';
        }
        // ---------- Replenishment ----------
        field(22; "Central Warehouse Code"; Code[10])
        {
            Caption = 'Central Warehouse Code';
            TableRelation = Location;
            ToolTip = 'Location cap hang cho cac store (Transfer-from).';
        }
        field(23; "Store Location Filter"; Text[250])
        {
            Caption = 'Store Location Filter';
            ToolTip = 'Filter tren Location Code de xac dinh dau la store, vi du S001..S099.';
        }
        // ---------- Discount Governance ----------
        field(30; "Max Manual Discount %"; Decimal)
        {
            Caption = 'Max Manual Discount %';
            InitValue = 15;
            DecimalPlaces = 0 : 2;
            ToolTip = 'Manual discount vuot % nay thi tao exception muc High.';
        }
        field(31; "Manual Disc. Share Warn %"; Decimal)
        {
            Caption = 'Manual Discount Share Warning %';
            InitValue = 20;
            DecimalPlaces = 0 : 2;
            ToolTip = 'Ty trong doanh so co manual discount tren mot staff trong ngay vuot % nay thi tao exception muc Medium.';
        }
        field(32; "Repeat Discount Count"; Integer)
        {
            Caption = 'Repeat Discount Count per Day';
            InitValue = 5;
            ToolTip = 'Mot staff dung manual discount qua so lan nay trong mot ngay thi tao exception.';
        }
        // ---------- Agent ----------
        field(40; "Agent User Name"; Code[50])
        {
            Caption = 'Agent User Name';
            ToolTip = 'Ten user (Entra app) ma agent dung khi ghi de xuat, de audit tach nguoi va agent.';
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
        // UC1. Ban ghi Setup co san tu truoc khong nhan InitValue, nen code coi 0 la gia tri mac dinh (xem cac ham Eff*).
        field(50; "Forecast Holdout Days"; Integer)
        {
            Caption = 'Forecast Holdout Days';
            InitValue = 28;
            MinValue = 0;
            ToolTip = 'So ngay cuoi lich su dung de do do chinh xac: du bao lap tu du lieu truoc do roi so voi ban thuc te. 0 = 28.';
        }
        field(51; "Forecast WAPE Warn %"; Decimal)
        {
            Caption = 'Forecast WAPE Warn %';
            InitValue = 50;
            MinValue = 0;
            ToolTip = 'Cap mat hang x dia diem co WAPE vuot nguong nay vao danh sach ngoai le. 0 = 50.';
        }
        field(52; "Forecast Bias Warn %"; Decimal)
        {
            Caption = 'Forecast Bias Warn %';
            InitValue = 30;
            MinValue = 0;
            ToolTip = 'Du bao lech mot phia (cao hoac thap) qua nguong nay vao danh sach ngoai le. 0 = 30.';
        }
        field(53; "Forecast Min Actual Qty"; Decimal)
        {
            Caption = 'Forecast Min Actual Qty';
            InitValue = 20;
            MinValue = 0;
            ToolTip = 'Cap ban it hon so nay trong ky do khong xet ngoai le, vi WAPE tren so nho khong co y nghia. 0 = 20.';
        }
        // UC3
        field(54; "Forecast Horizon Days"; Integer)
        {
            Caption = 'Forecast Horizon Days';
            InitValue = 28;
            MinValue = 0;
            ToolTip = 'So ngay toi duoc du bao bang Holt-Winters va ghi vao LSC Forecast Entry. Phai phu lead time cong so ngay phu ton cua LS. 0 = 28, toi da 90.';
        }
        field(55; "Publish LS Forecast"; Boolean)
        {
            Caption = 'Publish LS Forecast';
            ToolTip = 'Bat thi moi lan tinh ghi du bao Holt-Winters cua cac cap cua hang vao LSC Forecast Entry (xoa du bao cu tu ngay mai tro di). Mat hang dat LSC Replen. Calculation Type = Retail Forecast se bo sung hang theo du bao nay, cong Planned Sales Demand.';
        }
        field(60; "On-time Tolerance Days"; Integer)
        {
            Caption = 'On-time Tolerance Days';
            MinValue = 0;
            ToolTip = 'Hang ve tre khong qua so ngay nay so voi Expected Receipt Date van tinh la dung han.';
        }
        field(61; "Supplier On-time Warn %"; Decimal)
        {
            Caption = 'Supplier On-time Warn %';
            InitValue = 80;
            MinValue = 0;
            ToolTip = 'Nha cung cap co ty le giao dung han duoi nguong nay bi danh dau can xem. 0 = 80.';
        }
        field(62; "Supplier History Days"; Integer)
        {
            Caption = 'Supplier History Days';
            InitValue = 180;
            MinValue = 0;
            ToolTip = 'Chi xet dong don mua co Expected Receipt Date trong so ngay gan nhat nay. 0 = 180.';
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
        if "Forecast Holdout Days" > 100 then     // mang ngay 500 phan tu = 365 ngay hoc Holt-Winters + ky kiem tra
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
