/// <summary>
/// Dien master data module Replenishment cua LS Central cho bo du lieu demo Marou tren company NWV.
/// Chi dung tren sandbox. Phoi ra ODataV4 ten `NWVDemoReplenSetup`.
///
/// Cau hinh KHONG nam trong AL: Python sinh tu tools/demo_scenario.py (mot nguon duy nhat cho danh sach
/// mat hang, cua hang, han dung) roi truyen vao `Apply(configJson)`. Chay lai bao nhieu lan cung ra cung
/// ket qua. Moi thay doi tra ve kem gia tri truoc va sau de doc lai duoc.
///
/// Ly do tung buoc, doc tu source LS Central 28.0.10.3586:
///   - Location."LSC Active for Autom. Replen." tat thi InitLocation bo cua hang khoi phep tinh.
///   - Replen. Setup."Store Items Ranged By" = Store Groups: ShouldPlanItem chi tinh khi co
///     Item Distribution loai Store, Status Active, Ordered by Central, Ordering Method Calculate.
///     Du lieu Cronus chi co ban ghi cap nhom va "By hand", nen khong mon nao duoc tinh.
///   - Item."LSC Replen. Calculation Type" = "Automatic - From Data Profile" ma khong co Data Profile thi
///     ReturnReplItemStoreRec tra ve rong va mon do bi bo qua.
///   - Replenish From Warehouse lay tu bang Replen. From Warehouse, khong co thi lay Default Central
///     Warehouse (dang la W0001 cua Cronus). Kho tong Marou la W0003 nen them quy tac theo tung mat hang.
/// </summary>
codeunit 70253 "NWV Demo LS Replen. Setup"
{
    var
        Log: JsonArray;

    procedure Apply(configJson: Text): Text
    var
        Config: JsonObject;
        Token: JsonToken;
        Result: JsonObject;
        Output: Text;
        Warehouse: Code[10];
    begin
        Clear(Log);
        Config.ReadFrom(configJson);
        Config.Get('centralWarehouse', Token);
        Warehouse := CopyStr(Token.AsValue().AsCode(), 1, 10);

        if Config.Get('stores', Token) then
            ApplyStores(Token.AsArray());
        if Config.Get('items', Token) then
            ApplyItems(Token.AsArray(), Warehouse);
        if Config.Get('distribution', Token) then
            ApplyDistribution(Token.AsArray());
        if Config.Get('templates', Token) then
            ApplyTemplates(Token.AsArray());
        if Config.Get('deleteOpenOutOfStockBefore', Token) then
            DeleteStaleOutOfStock(Token.AsValue().AsText(), Config);
        if Config.Get('lsForecastSetup', Token) then
            EnsureForecastSetup();
        if Config.Get('offers', Token) then
            ApplyOffers(Token.AsArray());
        if Config.Get('plannedEvents', Token) then
            ApplyPlannedEvents(Token.AsArray());

        Result.Add('changes', Log.Count());
        Result.Add('log', Log);
        Result.WriteTo(Output);
        exit(Output);
    end;

    local procedure ApplyStores(Stores: JsonArray)
    var
        Location: Record Location;
        Token: JsonToken;
    begin
        foreach Token in Stores do begin
            Location.Get(CopyStr(Token.AsValue().AsCode(), 1, 10));
            if not Location."LSC Active for Autom. Replen." then begin
                AddLog('Location', Location.Code, 'LSC Active for Autom. Replen.', 'false', 'true');
                Location.Validate("LSC Active for Autom. Replen.", true);
                Location.Modify(true);
            end;
        end;
    end;

    local procedure ApplyItems(Items: JsonArray; Warehouse: Code[10])
    var
        Item: Record Item;
        ItemObj: JsonObject;
        Token: JsonToken;
        Value: JsonToken;
        StoreCover: Decimal;
        WhseCover: Decimal;
        SalesProfile: Code[10];
        CalcType: Enum "LSC Replen. Calculation Type";
        ReorderPoint: Decimal;
        MaxInventory: Decimal;
        Changed: Boolean;
    begin
        foreach Token in Items do begin
            ItemObj := Token.AsObject();
            ItemObj.Get('no', Value);
            Item.Get(CopyStr(Value.AsValue().AsCode(), 1, 20));
            ItemObj.Get('storeCoverDays', Value);
            StoreCover := Value.AsValue().AsDecimal();
            ItemObj.Get('whseCoverDays', Value);
            WhseCover := Value.AsValue().AsDecimal();
            ItemObj.Get('salesProfile', Value);
            SalesProfile := CopyStr(Value.AsValue().AsCode(), 1, 10);
            Changed := false;
            // Mac dinh Average Usage. Mat hang min-max (UC5) truyen calcType = "Stock Levels" kem reorderPoint va
            // maxInventory: Calc-StockLevels cua LS chi dung Item."Reorder Point" va Item."Maximum Inventory".
            CalcType := CalcType::"Average Usage";
            if ItemObj.Get('calcType', Value) then
                case Value.AsValue().AsText() of
                    'Stock Levels':
                        CalcType := CalcType::"Stock Levels";
                    'LS Forecast':
                        CalcType := CalcType::"LS Forecast";
                end;
            ReorderPoint := Item."Reorder Point";
            MaxInventory := Item."Maximum Inventory";
            if ItemObj.Get('reorderPoint', Value) then
                ReorderPoint := Value.AsValue().AsDecimal();
            if ItemObj.Get('maxInventory', Value) then
                MaxInventory := Value.AsValue().AsDecimal();

            if Item."LSC Replen. Calculation Type" <> CalcType then begin
                AddLog('Item', Item."No.", 'LSC Replen. Calculation Type', Format(Item."LSC Replen. Calculation Type"), Format(CalcType));
                Item.Validate("LSC Replen. Calculation Type", CalcType);
                Changed := true;
            end;
            if Item."Reorder Point" <> ReorderPoint then begin
                AddLog('Item', Item."No.", 'Reorder Point', Format(Item."Reorder Point", 0, 9), Format(ReorderPoint, 0, 9));
                Item.Validate("Reorder Point", ReorderPoint);
                Changed := true;
            end;
            if Item."Maximum Inventory" <> MaxInventory then begin
                AddLog('Item', Item."No.", 'Maximum Inventory', Format(Item."Maximum Inventory", 0, 9), Format(MaxInventory, 0, 9));
                Item.Validate("Maximum Inventory", MaxInventory);
                Changed := true;
            end;
            if Item."LSC Replenishment Sales Prof" <> SalesProfile then begin
                AddLog('Item', Item."No.", 'LSC Replenishment Sales Prof', Item."LSC Replenishment Sales Prof", SalesProfile);
                Item.Validate("LSC Replenishment Sales Prof", SalesProfile);
                Changed := true;
            end;
            if Item."LSC Store Stock Cover Reqd (D)" <> StoreCover then begin
                AddLog('Item', Item."No.", 'LSC Store Stock Cover Reqd (D)', Format(Item."LSC Store Stock Cover Reqd (D)", 0, 9), Format(StoreCover, 0, 9));
                Item.Validate("LSC Store Stock Cover Reqd (D)", StoreCover);
                Changed := true;
            end;
            if Item."LSC Wareh Stock Cover Reqd (D)" <> WhseCover then begin
                AddLog('Item', Item."No.", 'LSC Wareh Stock Cover Reqd (D)', Format(Item."LSC Wareh Stock Cover Reqd (D)", 0, 9), Format(WhseCover, 0, 9));
                Item.Validate("LSC Wareh Stock Cover Reqd (D)", WhseCover);
                Changed := true;
            end;
            if Item."LSC Exclude from Replenishment" then begin
                AddLog('Item', Item."No.", 'LSC Exclude from Replenishment', 'true', 'false');
                Item.Validate("LSC Exclude from Replenishment", false);
                Changed := true;
            end;
            if Item."LSC Consider Consumpt as Sales" then begin
                // Cua hang Marou co dong Sale; Negative Adjmt. o cua hang la huy hang het han, khong phai ban.
                AddLog('Item', Item."No.", 'LSC Consider Consumpt as Sales', 'true', 'false');
                Item.Validate("LSC Consider Consumpt as Sales", false);
                Changed := true;
            end;
            if (Item."Sales Unit of Measure" <> '') and (Item."Sales Unit of Measure" <> Item."Base Unit of Measure") then begin
                // Item Journal Line lay Sales Unit of Measure cho dong Sale khi file import khong co cot UoM.
                // Cronus dat SLICE (0,1) / PORTION cho banh va kem hop, nen so ban bi chia 10 lan khi post.
                AddLog('Item', Item."No.", 'Sales Unit of Measure', Item."Sales Unit of Measure", Item."Base Unit of Measure");
                Item.Validate("Sales Unit of Measure", Item."Base Unit of Measure");
                Changed := true;
            end;
            if Changed then
                Item.Modify(true);

            EnsureFromWarehouse(Item."No.", Warehouse);
        end;
    end;

    local procedure EnsureFromWarehouse(ItemNo: Code[20]; Warehouse: Code[10])
    var
        FromWarehouse: Record "LSC Replen. From Warehouse";
    begin
        if FromWarehouse.Get('', '', '', ItemNo, '') then begin
            if FromWarehouse."Warehouse Location Code" = Warehouse then
                exit;
            AddLog('Replen. From Warehouse', ItemNo, 'Warehouse Location Code', FromWarehouse."Warehouse Location Code", Warehouse);
            FromWarehouse.Validate("Warehouse Location Code", Warehouse);
            FromWarehouse.Modify(true);
            exit;
        end;
        FromWarehouse.Init();
        FromWarehouse."Item No." := ItemNo;
        FromWarehouse.Validate("Warehouse Location Code", Warehouse);
        FromWarehouse.Insert(true);
        AddLog('Replen. From Warehouse', ItemNo, 'Warehouse Location Code', '(chua co)', Warehouse);
    end;

    local procedure ApplyDistribution(Rows: JsonArray)
    var
        ItemDistribution: Record "LSC Item Distribution";
        RowObj: JsonObject;
        Token: JsonToken;
        Value: JsonToken;
        StoreNo: Code[20];
        ItemNo: Code[20];
        StatusText: Text;
        NewStatus: Option Active,"On hold","Not purchased again","Out of stock";
        KeyText: Text;
    begin
        foreach Token in Rows do begin
            RowObj := Token.AsObject();
            RowObj.Get('store', Value);
            StoreNo := CopyStr(Value.AsValue().AsCode(), 1, 20);
            RowObj.Get('item', Value);
            ItemNo := CopyStr(Value.AsValue().AsCode(), 1, 20);
            RowObj.Get('status', Value);
            StatusText := Value.AsValue().AsText();
            Evaluate(NewStatus, StatusText);
            KeyText := StoreNo + ' x ' + ItemNo;

            if not ItemDistribution.Get(ItemDistribution.Type::Store, StoreNo, ItemNo) then begin
                ItemDistribution.Init();
                ItemDistribution.Type := ItemDistribution.Type::Store;
                ItemDistribution.Code := StoreNo;
                ItemDistribution."Item No." := ItemNo;
                ItemDistribution.Status := NewStatus;
                ItemDistribution."Ordered by" := ItemDistribution."Ordered by"::Central;
                ItemDistribution."Ordering Method" := ItemDistribution."Ordering Method"::Calculate;
                ItemDistribution.Insert(true);
                // OnInsert cua LS (AssignItemFieldsOnInsert) chep de "Ordering Method" bang Item."LSC Def. Ordering Method"
                // (By hand), nen phai ghi lai sau khi insert.
                ItemDistribution.Status := NewStatus;
                ItemDistribution."Ordered by" := ItemDistribution."Ordered by"::Central;
                ItemDistribution."Ordering Method" := ItemDistribution."Ordering Method"::Calculate;
                ItemDistribution.Modify(true);
                AddLog('Item Distribution', KeyText, 'Status/Ordered by/Ordering Method', '(chua co)', StatusText + '/Central/Calculate');
            end else
                if (ItemDistribution.Status <> NewStatus) or
                   (ItemDistribution."Ordered by" <> ItemDistribution."Ordered by"::Central) or
                   (ItemDistribution."Ordering Method" <> ItemDistribution."Ordering Method"::Calculate)
                then begin
                    AddLog('Item Distribution', KeyText, 'Status/Ordered by/Ordering Method',
                        Format(ItemDistribution.Status) + '/' + Format(ItemDistribution."Ordered by") + '/' + Format(ItemDistribution."Ordering Method"),
                        StatusText + '/Central/Calculate');
                    ItemDistribution.Status := NewStatus;
                    ItemDistribution."Ordered by" := ItemDistribution."Ordered by"::Central;
                    ItemDistribution."Ordering Method" := ItemDistribution."Ordering Method"::Calculate;
                    ItemDistribution.Modify(true);
                end;
        end;
    end;

    local procedure ApplyTemplates(Rows: JsonArray)
    var
        ReplenTemplate: Record "LSC Replen. Template";
        RowObj: JsonObject;
        Token: JsonToken;
        Value: JsonToken;
        TemplateCode: Code[20];
        IsNew: Boolean;
    begin
        foreach Token in Rows do begin
            RowObj := Token.AsObject();
            RowObj.Get('code', Value);
            TemplateCode := CopyStr(Value.AsValue().AsCode(), 1, 20);
            IsNew := not ReplenTemplate.Get(TemplateCode);
            if IsNew then begin
                ReplenTemplate.Init();
                ReplenTemplate.Code := TemplateCode;
            end;

            RowObj.Get('type', Value);
            if Value.AsValue().AsText() = 'Transfer' then
                ReplenTemplate.Validate("Replenishment Type", "LSC Replenishment Type"::Transfer)
            else begin
                ReplenTemplate.Validate("Replenishment Type", "LSC Replenishment Type"::Purchase);
                ReplenTemplate.Validate("Purchase Order Type", "LSC Rpln. Tmpl. Pur. Ord. Type"::"One Purchase Order per Vendor");
            end;
            RowObj.Get('description', Value);
            ReplenTemplate.Description := CopyStr(Value.AsValue().AsText(), 1, MaxStrLen(ReplenTemplate.Description));
            RowObj.Get('location', Value);
            ReplenTemplate."Location Code" := CopyStr(Value.AsValue().AsCode(), 1, 10);
            RowObj.Get('storeGroupFilter', Value);
            ReplenTemplate."Store Group Filter" := CopyStr(Value.AsValue().AsCode(), 1, MaxStrLen(ReplenTemplate."Store Group Filter"));
            RowObj.Get('itemNoFilter', Value);
            ReplenTemplate."Item No. Filter" := CopyStr(Value.AsValue().AsCode(), 1, MaxStrLen(ReplenTemplate."Item No. Filter"));
            // Tro ly khong tao chung tu: nguoi mua hang tu bam Create Orders tren journal.
            ReplenTemplate."Create Orders Automatically" := ReplenTemplate."Create Orders Automatically"::"Do Not Create Orders Automatically";

            if IsNew then begin
                ReplenTemplate.Insert(true);
                AddLog('Replen. Template', TemplateCode, '(tao moi, kem batch DEFAULT)', '', ReplenTemplate.Description);
            end else begin
                ReplenTemplate.Modify(true);
                AddLog('Replen. Template', TemplateCode, '(ghi lai cau hinh)', '', ReplenTemplate.Description);
            end;
        end;
    end;

    /// Du lieu Cronus con dong Out of Stock Log mo tu truoc khi co du lieu Marou (vd 10070 x S0002 tu 01/01/2018,
    /// khong co Date In Stock). LS coi moi ngay la het hang nen ban binh quan ra 0. Cung dieu kien voi bao cao
    /// "Delete Open Replen. Out of Stock Logs" cua LS, nhung chi trong pham vi mat hang va dia diem demo.
    local procedure DeleteStaleOutOfStock(BeforeText: Text; Config: JsonObject)
    var
        OutOfStockLog: Record "LSC Replen. Out of Stock Log";
        LastEntry: Record "LSC Replen. Last Entr for OOS";
        Token: JsonToken;
        ItemObj: JsonToken;
        Value: JsonToken;
        BeforeDate: Date;
        LocationFilter: Text;
        ItemFilter: Text;
        ResetAll: Boolean;
    begin
        Evaluate(BeforeDate, BeforeText, 9);
        Config.Get('stores', Token);
        foreach Value in Token.AsArray() do
            LocationFilter += '|' + Value.AsValue().AsText();
        Config.Get('centralWarehouse', Value);
        LocationFilter := Value.AsValue().AsText() + LocationFilter;
        Config.Get('items', Token);
        foreach ItemObj in Token.AsArray() do begin
            ItemObj.AsObject().Get('no', Value);
            if ItemFilter <> '' then
                ItemFilter += '|';
            ItemFilter += Value.AsValue().AsText();
        end;
        OutOfStockLog.SetFilter("Item No.", ItemFilter);
        OutOfStockLog.SetFilter("Location Code", LocationFilter);
        // AL khong short-circuit `and`: thieu khoa thi Token van la mang items va AsValue() bao loi, nen doc rieng.
        ResetAll := false;
        if Config.Get('resetOutOfStockLog', Token) then
            ResetAll := Token.AsValue().AsBoolean();
        // resetOutOfStockLog = true: xoa MOI dong cua mat hang va dia diem demo, dung sau khi post lai
        // Item Ledger Entry, vi log cu tinh tren so ton cu. Khong co co do thi chi xoa dong mo truoc ngay dau.
        if not ResetAll then begin
            OutOfStockLog.SetRange("Date In Stock", 0D);
            OutOfStockLog.SetFilter("Date Out of Stock", '<%1', BeforeDate);
        end;
        if OutOfStockLog.FindSet() then
            repeat
                AddLog('Replen. Out of Stock Log', OutOfStockLog."Item No." + ' x ' + OutOfStockLog."Location Code",
                    'Date Out of Stock (xoa)', Format(OutOfStockLog."Date Out of Stock", 0, 9), '(xoa)');
            until OutOfStockLog.Next() = 0;
        OutOfStockLog.DeleteAll(true);

        // Con tro "ILE cuoi da quet" theo tung ma. Sau khi post lai ILE, so entry bat dau lai tu 1 nen con tro cu
        // lam LS bo qua ILE moi hoac sua mot dong log da xoa (loi "Replen. Out of Stock Log does not exist").
        if ResetAll then begin
            LastEntry.SetFilter("Item No.", ItemFilter);
            if not LastEntry.IsEmpty() then
                AddLog('Replen. Last Entr for OOS', ItemFilter, '(xoa con tro ILE)', Format(LastEntry.Count()), '0');
            LastEntry.DeleteAll();
        end;
    end;

    // Kieu tinh Retail Forecast (LS Forecast) cua LS bao "LS Forecast Setup not found" neu thieu ban ghi nay. Ngay nao chua co
    // Forecast Entry thi lay ban binh quan cua Average Usage thay vi coi la 0.
    local procedure EnsureForecastSetup()
    var
        ForecastSetup: Record "LSC Forecast Setup";
    begin
        if not ForecastSetup.Get() then begin
            ForecastSetup.Init();
            ForecastSetup."Forecast Exception Handling" := ForecastSetup."Forecast Exception Handling"::UseAvgUsage;
            ForecastSetup.Insert(true);
            AddLog('LSC Forecast Setup', '', 'Forecast Exception Handling', '(chua co)', 'Use Average Usage Result');
            exit;
        end;
        if ForecastSetup."Forecast Exception Handling" <> ForecastSetup."Forecast Exception Handling"::UseAvgUsage then begin
            AddLog('LSC Forecast Setup', '', 'Forecast Exception Handling', Format(ForecastSetup."Forecast Exception Handling"), 'Use Average Usage Result');
            ForecastSetup."Forecast Exception Handling" := ForecastSetup."Forecast Exception Handling"::UseAvgUsage;
            ForecastSetup.Modify(true);
        end;
    end;

    // Lich khuyen mai va su kien bang bang chuan cua LS: LSC Replen. Planned Event (dau) va LSC Replen. Planned Sales Dem.
    // (tung mat hang x dia diem x ngay). Chay lai thi tat su kien, xoa dong cu, tao lai, bat lai; LS cam xoa dong dang Enabled.
    // Config: [{code, description, startDate, endDate, type, demand, lines: [{item, location}]}], type la ten enum
    // LSC Planned Demand Type, demand la so luong hoac % tuy type.
    local procedure ApplyPlannedEvents(Events: JsonArray)
    var
        PlannedEvent: Record "LSC Replen. Planned Event";
        Demand: Record "LSC Replen. Planned Sales Dem.";
        EventToken: JsonToken;
        LineToken: JsonToken;
        Value: JsonToken;
        EventObj: JsonObject;
        LineObj: JsonObject;
        EventCode: Code[20];
        StartDate: Date;
        EndDate: Date;
        D: Date;
        DemandType: Enum "LSC Planned Demand Type";
        DemandQty: Decimal;
        ItemNo: Code[20];
        LocationCode: Code[10];
        LineCount: Integer;
    begin
        foreach EventToken in Events do begin
            EventObj := EventToken.AsObject();
            EventObj.Get('code', Value);
            EventCode := CopyStr(Value.AsValue().AsCode(), 1, 20);
            EventObj.Get('startDate', Value);
            Evaluate(StartDate, Value.AsValue().AsText(), 9);
            EventObj.Get('endDate', Value);
            Evaluate(EndDate, Value.AsValue().AsText(), 9);
            EventObj.Get('type', Value);
            Evaluate(DemandType, Value.AsValue().AsText());
            EventObj.Get('demand', Value);
            DemandQty := Value.AsValue().AsDecimal();

            if PlannedEvent.Get(EventCode) then begin
                PlannedEvent.Status := PlannedEvent.Status::Disabled;
                PlannedEvent.Modify();
                Demand.Reset();
                Demand.SetRange("Planned Demand Event", EventCode);
                Demand.ModifyAll(Status, Demand.Status::Disabled);
                Demand.DeleteAll(true);
            end else begin
                PlannedEvent.Init();
                PlannedEvent."Event Code" := EventCode;
                PlannedEvent.Insert(true);
            end;
            EventObj.Get('description', Value);
            PlannedEvent.Description := CopyStr(Value.AsValue().AsText(), 1, MaxStrLen(PlannedEvent.Description));
            PlannedEvent."End Date" := 0D;
            PlannedEvent.Validate("Start Date", StartDate);
            PlannedEvent.Validate("End Date", EndDate);
            // Gan truc tiep, khong Validate: OnValidate cua Source Type/Code hoi Confirm khi da co dong, web service khong co UI.
            PlannedEvent."Source Type" := PlannedEvent."Source Type"::Manual;
            PlannedEvent."Source Code" := '';
            if EventObj.Get('offerNo', Value) then
                if Value.AsValue().AsText() <> '' then begin
                    PlannedEvent."Source Type" := PlannedEvent."Source Type"::Discount;
                    PlannedEvent."Source Code" := CopyStr(Value.AsValue().AsCode(), 1, 20);
                end;
            PlannedEvent.Modify(true);

            LineCount := 0;
            EventObj.Get('lines', Value);
            foreach LineToken in Value.AsArray() do begin
                LineObj := LineToken.AsObject();
                LineObj.Get('item', Value);
                ItemNo := CopyStr(Value.AsValue().AsCode(), 1, 20);
                LineObj.Get('location', Value);
                LocationCode := CopyStr(Value.AsValue().AsCode(), 1, 10);
                for D := StartDate to EndDate do begin
                    Demand.Reset();
                    Demand.SetRange("Item No.", ItemNo);
                    Demand.SetRange("Variant Code", '');
                    Demand.SetRange("Location Code", LocationCode);
                    Demand.SetRange(Date, D);
                    Demand.Init();
                    if Demand.FindLast() then
                        Demand."Line No." += 10000
                    else
                        Demand."Line No." := 10000;
                    Demand."Item No." := ItemNo;
                    Demand."Variant Code" := '';
                    Demand."Location Code" := LocationCode;
                    Demand.Date := D;
                    Demand."Planned Demand Type" := DemandType;
                    Demand."Planned Demand" := DemandQty;
                    Demand."Planned Demand Event" := EventCode;
                    Demand.Status := Demand.Status::Enabled;
                    Demand.Insert(true);
                    LineCount += 1;
                end;
            end;
            PlannedEvent.Status := PlannedEvent.Status::Enabled;
            PlannedEvent.Modify(true);
            AddLog('Replen. Planned Event', EventCode, 'Planned Sales Demand (dong)', '', Format(LineCount) + ' dong, ' + Format(DemandType) + ' ' + Format(DemandQty, 0, 9));
        end;
    end;

    // Chuong trinh khuyen mai chuan cua LS: LSC Validation Period (ngay, gio) + LSC Periodic Discount (dau) + Line.
    // Doc trong source LS 28.0.10.3586:
    //   - Dau dang Enabled thi khong sua duoc dau, dong, va Validation Period dang dung (OnModify bao loi). Phai tat truoc.
    //   - Validate Status = Enabled goi CheckOffer: bao loi neu Ending Date da qua Today, nen chuong trinh da ket thuc de Disabled.
    //   - Validate "No." cua dau goi TestManual cua No. Series cua cua hang; gan truc tiep roi Insert thi khong can.
    // Config: [{no, description, type, priceGroup, discountPct, validationId, startDate, endDate, startTime, endTime,
    //           enabled, lines: [{item, discPct}]}]
    local procedure ApplyOffers(Offers: JsonArray)
    var
        Offer: Record "LSC Periodic Discount";
        OfferLine: Record "LSC Periodic Discount Line";
        Period: Record "LSC Validation Period";
        OfferToken: JsonToken;
        LineToken: JsonToken;
        Value: JsonToken;
        OfferObj: JsonObject;
        LineObj: JsonObject;
        OfferNo: Code[20];
        PeriodId: Code[10];
        D: Date;
        T: Time;
        LineNo: Integer;
        WantEnabled: Boolean;
        TypeText: Text;
    begin
        foreach OfferToken in Offers do begin
            OfferObj := OfferToken.AsObject();
            OfferObj.Get('no', Value);
            OfferNo := CopyStr(Value.AsValue().AsCode(), 1, 20);
            OfferObj.Get('validationId', Value);
            PeriodId := CopyStr(Value.AsValue().AsCode(), 1, 10);

            if Offer.Get(OfferNo) then
                if Offer.Status = Offer.Status::Enabled then begin
                    Offer.Validate(Status, Offer.Status::Disabled);
                    Offer.Modify(true);
                end;

            if not Period.Get(PeriodId) then begin
                Period.Init();
                Period.ID := PeriodId;
                Period.Insert(true);
            end;
            OfferObj.Get('description', Value);
            Period.Description := CopyStr(Value.AsValue().AsText(), 1, MaxStrLen(Period.Description));
            Period."Ending Date" := 0D;
            OfferObj.Get('startDate', Value);
            Evaluate(D, Value.AsValue().AsText(), 9);
            Period.Validate("Starting Date", D);
            OfferObj.Get('endDate', Value);
            Evaluate(D, Value.AsValue().AsText(), 9);
            Period.Validate("Ending Date", D);
            T := 0T;
            if OfferObj.Get('startTime', Value) then
                Evaluate(T, Value.AsValue().AsText(), 9);
            Period.Validate("Starting Time", T);
            T := 0T;
            if OfferObj.Get('endTime', Value) then
                Evaluate(T, Value.AsValue().AsText(), 9);
            Period.Validate("Ending Time", T);
            Period.Modify(true);

            if not Offer.Get(OfferNo) then begin
                Offer.Init();
                Offer."No." := OfferNo;
                OfferObj.Get('type', Value);
                TypeText := Value.AsValue().AsText();
                Evaluate(Offer.Type, TypeText);
                Offer.Insert(true);
            end;
            OfferObj.Get('description', Value);
            Offer.Description := CopyStr(Value.AsValue().AsText(), 1, MaxStrLen(Offer.Description));
            OfferObj.Get('priceGroup', Value);
            Offer."Price Group" := CopyStr(Value.AsValue().AsCode(), 1, 10);
            Offer."Validation Period ID" := PeriodId;
            Offer."Discount Type" := Offer."Discount Type"::"Deal Price";
            OfferObj.Get('discountPct', Value);
            Offer."Discount % Value" := Value.AsValue().AsDecimal();
            Offer.Modify(true);

            OfferLine.Reset();
            OfferLine.SetRange("Offer No.", OfferNo);
            if OfferLine.FindSet() then
                repeat
                    OfferLine.Delete(true);
                until OfferLine.Next() = 0;

            LineNo := 0;
            OfferObj.Get('lines', Value);
            foreach LineToken in Value.AsArray() do begin
                LineObj := LineToken.AsObject();
                LineNo += 10000;
                OfferLine.Init();
                OfferLine."Offer No." := OfferNo;
                OfferLine."Line No." := LineNo;
                OfferLine.Validate(Type, OfferLine.Type::Item);
                LineObj.Get('item', Value);
                OfferLine.Validate("No.", CopyStr(Value.AsValue().AsCode(), 1, 20));
                OfferLine.Insert(true);
                LineObj.Get('discPct', Value);
                OfferLine.Validate("Deal Price/Disc. %", Value.AsValue().AsDecimal());
                OfferLine.Modify(true);
            end;

            WantEnabled := false;
            if OfferObj.Get('enabled', Value) then
                WantEnabled := Value.AsValue().AsBoolean();
            Offer.Get(OfferNo);
            if WantEnabled then begin
                Offer.Validate(Status, Offer.Status::Enabled);
                Offer.Modify(true);
            end;
            AddLog('LSC Periodic Discount', OfferNo, 'Chuong trinh', '',
              Format(Offer.Type) + ', ' + Format(LineNo div 10000) + ' dong, ' + Format(Offer.Status) + ', ' +
              Format(Period."Starting Date", 0, 9) + '..' + Format(Period."Ending Date", 0, 9));
        end;
    end;

    local procedure AddLog(TableName: Text; KeyText: Text; FieldName: Text; OldValue: Text; NewValue: Text)
    var
        Entry: JsonObject;
    begin
        Entry.Add('table', TableName);
        Entry.Add('key', KeyText);
        Entry.Add('field', FieldName);
        Entry.Add('old', OldValue);
        Entry.Add('new', NewValue);
        Log.Add(Entry);
    end;
}

codeunit 70254 "NWV Demo LS Replen. Install"
{
    Subtype = Install;

    trigger OnInstallAppPerCompany()
    begin
        Register();
    end;

    procedure Register()
    var
        TenantWebService: Record "Tenant Web Service";
        WebServiceManagement: Codeunit "Web Service Management";
    begin
        WebServiceManagement.CreateTenantWebService(
            TenantWebService."Object Type"::Codeunit, Codeunit::"NWV Demo LS Replen. Setup", 'NWVDemoReplenSetup', true);
        WebServiceManagement.CreateTenantWebService(
            TenantWebService."Object Type"::Codeunit, Codeunit::"NWV Demo Repost", 'NWVDemoRepost', true);
        WebServiceManagement.CreateTenantWebService(
            TenantWebService."Object Type"::Codeunit, Codeunit::"NWV Demo Supplier Data", 'NWVDemoSupplier', true);
    end;
}

codeunit 70255 "NWV Demo LS Replen. Upgrade"
{
    Subtype = Upgrade;

    trigger OnUpgradePerCompany()
    var
        Install: Codeunit "NWV Demo LS Replen. Install";
    begin
        Install.Register();
    end;
}
