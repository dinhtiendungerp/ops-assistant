/// <summary>
/// UC1: cua vao S2S cho module Replenishment cua LS Central. Phoi ra ODataV4 ten `NWVReplenService`
/// (dang ky trong codeunit "NWV Replen. Service Install").
///
///   ReadTable       doc bat ky bang nao trong danh sach cho phep, tra JSON theo ten field. Chi doc.
///                   Dung de tro ly va nguoi tu van xem master data Replenishment ma khong phai viet
///                   mot API page cho moi bang.
///   CalcItemQuantities   chay dung ham ma bao cao "Replen. - Calc. Item Qty" goi (codeunit 10012200).
///   UpdateOutOfStock     chay bao cao "Replen. Upd Out of Stock" (can Stock Out Functionality bat).
///   CalculateJournal     chay "Add Items to Replenishm. Jrnl." cho mot batch, ap cung bo loc template
///                        nhu nut tren trang Purchase/Transfer Replenishment Journal.
///
/// Ranh gioi: CalculateJournal TU CHOI chay neu template dat Create Orders Automatically khac
/// "Do Not Create Orders Automatically", vi luc do LS tu tao PO/TO. Tro ly khong tao chung tu.
/// Logic cua LS doc tu source LS Central 28.0.10.3586, khong doan.
/// </summary>
codeunit 70275 "NWV Replen. Service"
{
    var
        NotAllowedErr: Label 'Bang %1 khong nam trong danh sach duoc doc qua NWVReplenService.', Comment = '%1 = table no.';
        FieldNotFoundErr: Label 'Bang %1 khong co field ten "%2".', Comment = '%1 = table no., %2 = field name';
        AutoCreateErr: Label 'Template %1 dang dat Create Orders Automatically = %2. Tro ly khong chay tinh journal khi LS se tu tao chung tu; doi ve "Do Not Create Orders Automatically" truoc.', Comment = '%1 = template, %2 = value';
        BatchNotFoundErr: Label 'Khong tim thay Replenishment Journal Batch %1 / %2.', Comment = '%1 = template, %2 = batch';

    procedure ReadTable(tableNo: Integer; filtersJson: Text; fieldFilter: Text; maxRows: Integer): Text
    var
        RecRef: RecordRef;
        Rows: JsonArray;
        Result: JsonObject;
        FieldNos: List of [Integer];
        Count: Integer;
        Total: Integer;
        Output: Text;
    begin
        if not IsAllowedTable(tableNo) then
            Error(NotAllowedErr, tableNo);
        if (maxRows <= 0) or (maxRows > 5000) then
            maxRows := 5000;

        RecRef.Open(tableNo);
        ApplyFilters(RecRef, filtersJson);
        CollectFields(tableNo, fieldFilter, FieldNos);
        Total := RecRef.Count();
        if RecRef.FindSet() then
            repeat
                Rows.Add(RowToJson(RecRef, FieldNos));
                Count += 1;
            until (RecRef.Next() = 0) or (Count >= maxRows);

        Result.Add('table', tableNo);
        Result.Add('tableName', RecRef.Name);
        Result.Add('total', Total);
        Result.Add('returned', Count);
        Result.Add('rows', Rows);
        RecRef.Close();
        Result.WriteTo(Output);
        exit(Output);
    end;

    procedure CalcItemQuantities(itemFilter: Text; workDateText: Text): Text
    var
        Item: Record Item;
        ReplenItemQuantity: Record "LSC Replen. Item Quantity";
        ReplenCalcQtys: Codeunit "LSC Replen. - Calc. Qtys";
        Result: JsonObject;
        Started: DateTime;
        Output: Text;
    begin
        Started := CurrentDateTime();
        SetWorkDate(workDateText);
        if itemFilter <> '' then
            Item.SetFilter("No.", itemFilter);
        ReplenCalcQtys.SetParameters(true);
        ReplenCalcQtys.CalculateReplenishmentQuanties(Item);

        if itemFilter <> '' then
            ReplenItemQuantity.SetFilter("Item No.", itemFilter);
        Result.Add('action', 'CalcItemQuantities');
        Result.Add('itemFilter', itemFilter);
        Result.Add('items', Item.Count());
        Result.Add('replenItemQuantityRows', ReplenItemQuantity.Count());
        Result.Add('workDate', Format(WorkDate(), 0, 9));
        Result.Add('durationMs', CurrentDateTime() - Started);
        Result.WriteTo(Output);
        exit(Output);
    end;

    procedure UpdateOutOfStock(workDateText: Text): Text
    var
        OutOfStockLog: Record "LSC Replen. Out of Stock Log";
        UpdOutOfStock: Report "LSC Replen. Upd Out of Stock";
        Result: JsonObject;
        Output: Text;
    begin
        SetWorkDate(workDateText);
        UpdOutOfStock.UseRequestPage(false);
        UpdOutOfStock.RunModal();
        Result.Add('action', 'UpdateOutOfStock');
        Result.Add('outOfStockLogRows', OutOfStockLog.Count());
        Result.WriteTo(Output);
        exit(Output);
    end;

    procedure CalculateJournal(templateCode: Text; batchNo: Text; recalcItemQuantities: Boolean; workDateText: Text): Text
    var
        Item: Record Item;
        ReplenTemplate: Record "LSC Replen. Template";
        ReplenJournalBatch: Record "LSC Replen. Journal Batch";
        ReplenItemQuantity: Record "LSC Replen. Item Quantity";
        JournalLines: Record "LSC Replen. Journal Lines";
        JrnlDetails: Record "LSC Replen. Jrnl. Details";
        LogLines: Record "LSC Replen. Calc. Log Lines V2";
        ReplenCalcQtys: Codeunit "LSC Replen. - Calc. Qtys";
        AddItems: Report "LSC Add Items to Replen. Jrnl";
        Result: JsonObject;
        Started: DateTime;
        Output: Text;
    begin
        Started := CurrentDateTime();
        SetWorkDate(workDateText);
        if not ReplenJournalBatch.Get(CopyStr(templateCode, 1, 20), CopyStr(batchNo, 1, 10)) then
            Error(BatchNotFoundErr, templateCode, batchNo);
        ReplenTemplate.Get(ReplenJournalBatch."Replenishment Template Code");
        if ReplenTemplate."Create Orders Automatically" <> ReplenTemplate."Create Orders Automatically"::"Do Not Create Orders Automatically" then
            Error(AutoCreateErr, ReplenTemplate.Code, ReplenTemplate."Create Orders Automatically");

        if recalcItemQuantities then begin
            if ReplenTemplate."Item No. Filter" <> '' then
                Item.SetFilter("No.", ReplenTemplate."Item No. Filter");
            if ReplenTemplate."Vendor No. Filter" <> '' then
                Item.SetFilter("Vendor No.", ReplenTemplate."Vendor No. Filter");
            if ReplenTemplate."Item Category Filter" <> '' then
                Item.SetFilter("Item Category Code", ReplenTemplate."Item Category Filter");
            ReplenCalcQtys.SetParameters(true);
            ReplenCalcQtys.CalculateReplenishmentQuanties(Item);
            Commit();
        end;

        ApplyTemplateFilters(ReplenTemplate, ReplenItemQuantity);
        Clear(AddItems);
        AddItems.SetTableView(ReplenItemQuantity);
        // pIsScheduler = true de LS ghi Calc. Log Lines (Replen. Setup."Create Calc. Log Lines" dang bat). Chay khong
        // request page va khong scheduler thi report bo qua co do, journal ra so ma khong co dong giai thich nao.
        // Voi Job ID rong, che do scheduler khong doi Next Run Date va khong bat tinh song song (doc trong report 10012201).
        AddItems.SetParameters(ReplenJournalBatch, true, false);
        AddItems.UseRequestPage(false);
        Commit();
        AddItems.RunModal();

        ReplenJournalBatch.Get(ReplenJournalBatch."Replenishment Template Code", ReplenJournalBatch."Batch No.");
        JournalLines.SetRange("Replenishment Template Code", ReplenJournalBatch."Replenishment Template Code");
        JournalLines.SetRange("Batch No.", ReplenJournalBatch."Batch No.");
        JrnlDetails.SetRange("Replenishment Template Code", ReplenJournalBatch."Replenishment Template Code");
        JrnlDetails.SetRange("Batch No.", ReplenJournalBatch."Batch No.");
        LogLines.SetRange("Replenishment Template Code", ReplenJournalBatch."Replenishment Template Code");
        LogLines.SetRange("Batch No.", ReplenJournalBatch."Batch No.");

        Result.Add('action', 'CalculateJournal');
        Result.Add('template', ReplenTemplate.Code);
        Result.Add('replenishmentType', Format(ReplenTemplate."Replenishment Type"));
        Result.Add('batch', ReplenJournalBatch."Batch No.");
        Result.Add('replenItemQuantityInScope', ReplenItemQuantity.Count());
        Result.Add('journalLines', JournalLines.Count());
        Result.Add('journalDetails', JrnlDetails.Count());
        Result.Add('calcLogLines', LogLines.Count());
        Result.Add('calculationStatus', Format(ReplenJournalBatch."Calculation Status"));
        Result.Add('workDate', Format(WorkDate(), 0, 9));
        Result.Add('durationMs', CurrentDateTime() - Started);
        Result.WriteTo(Output);
        exit(Output);
    end;

    /// Chep tu action "Add Items to Journal" cua trang Purchase Replenishment Journal (LS 28.0.10.3586),
    /// phan loc theo template. Bo qua loc ABC, item hierarchy, special group va attribute vi Marou khong dung;
    /// neu template co nhung loc do thi tinh se rong hon tren giao dien.
    local procedure ApplyTemplateFilters(ReplenTemplate: Record "LSC Replen. Template"; var ReplenItemQuantity: Record "LSC Replen. Item Quantity")
    begin
        ReplenItemQuantity.Reset();
        ReplenItemQuantity.FilterGroup(3);
        if not ((ReplenTemplate."Replenishment Type" = "LSC Replenishment Type"::Purchase) and
           (ReplenTemplate."Purchase Order Type" = "LSC Rpln. Tmpl. Pur. Ord. Type"::"Purchase Orders for Receiving Locations"))
        then
            ReplenItemQuantity.SetRange("Replenish From Warehouse", ReplenTemplate."Location Code");
        ReplenItemQuantity.FilterGroup(0);
        if ReplenTemplate."Item Division Filter" <> '' then
            ReplenItemQuantity.SetFilter("Item Division Code", ReplenTemplate."Item Division Filter");
        if ReplenTemplate."Item Category Filter" <> '' then
            ReplenItemQuantity.SetFilter("Item Category Code", ReplenTemplate."Item Category Filter");
        if ReplenTemplate."Retail Product Filter" <> '' then
            ReplenItemQuantity.SetFilter("Retail Product Code", ReplenTemplate."Retail Product Filter");
        if ReplenTemplate."Item No. Filter" <> '' then
            ReplenItemQuantity.SetFilter("Item No.", ReplenTemplate."Item No. Filter");
        if ReplenTemplate."Vendor No. Filter" <> '' then
            ReplenItemQuantity.SetFilter("Vendor No.", ReplenTemplate."Vendor No. Filter");
        if ReplenTemplate."Replenishm. Calc. Type Filter" <> '' then
            ReplenItemQuantity.SetFilter("Replenishment Calculation Type", ReplenTemplate."Replenishm. Calc. Type Filter");
        if ReplenTemplate."Season Filter" <> '' then
            ReplenItemQuantity.SetFilter("Season Code", ReplenTemplate."Season Filter");
        if ReplenTemplate."Store Group Filter" <> '' then
            ReplenItemQuantity.SetFilter("Store Group Filter", ReplenTemplate."Store Group Filter");
    end;

    /// Phien web service khong co Work Date cua nguoi dung. Truyen ngay neo demo (vd 2026-09-18) de cua so
    /// ban hang cua Sales Profile tinh dung; rong thi giu ngay he thong.
    local procedure SetWorkDate(workDateText: Text)
    var
        NewDate: Date;
    begin
        if workDateText = '' then
            exit;
        Evaluate(NewDate, workDateText, 9);
        WorkDate(NewDate);
    end;

    local procedure IsAllowedTable(tableNo: Integer): Boolean
    begin
        // Module Replenishment cua LS Central
        if tableNo in [10012200 .. 10012399] then
            exit(true);
        exit(tableNo in [
            Database::Item, Database::Location, Database::"Stockkeeping Unit", Database::Vendor,
            Database::"Item Variant", Database::"Item Category", Database::"Item Unit of Measure",
            10000704, // LSC Item Distribution
            10000758, // LSC Retail System Log
            10000779, // LSC Store Group
            10000782, // LSC Store Group Setup
            99001470, // LSC Store
            99009051, // LSC Retail Calendar
            99009052  // LSC Retail Calendar Line
        ]);
    end;

    local procedure ApplyFilters(var RecRef: RecordRef; filtersJson: Text)
    var
        Filters: JsonObject;
        FilterToken: JsonToken;
        FieldName: Text;
        FldRef: FieldRef;
    begin
        if filtersJson = '' then
            exit;
        Filters.ReadFrom(filtersJson);
        foreach FieldName in Filters.Keys do begin
            Filters.Get(FieldName, FilterToken);
            FldRef := RecRef.Field(FieldNoByName(RecRef.Number, FieldName));
            FldRef.SetFilter(FilterToken.AsValue().AsText());
        end;
    end;

    local procedure FieldNoByName(tableNo: Integer; FieldName: Text): Integer
    var
        Fld: Record Field;
    begin
        Fld.SetRange(TableNo, tableNo);
        Fld.SetRange(FieldName, CopyStr(FieldName, 1, MaxStrLen(Fld.FieldName)));
        if not Fld.FindFirst() then
            Error(FieldNotFoundErr, tableNo, FieldName);
        exit(Fld."No.");
    end;

    /// fieldFilter: rong = moi field thuong; hoac danh sach ten cach nhau boi dau phay, ten ket thuc bang *
    /// la loc theo tien to (vd "No.,Description,LSC Replen*"). FlowField, Blob, Media khong doc.
    local procedure CollectFields(tableNo: Integer; fieldFilter: Text; var FieldNos: List of [Integer])
    var
        Fld: Record Field;
        Tokens: List of [Text];
        Token: Text;
        Keep: Boolean;
    begin
        if fieldFilter <> '' then
            Tokens := fieldFilter.Split(',');
        Fld.SetRange(TableNo, tableNo);
        Fld.SetRange(Class, Fld.Class::Normal);
        Fld.SetRange(Enabled, true);
        Fld.SetFilter(ObsoleteState, '<>%1', Fld.ObsoleteState::Removed);
        Fld.SetFilter(Type, '<>%1&<>%2&<>%3&<>%4&<>%5', Fld.Type::BLOB, Fld.Type::Media, Fld.Type::MediaSet, Fld.Type::RecordID, Fld.Type::TableFilter);
        if Fld.FindSet() then
            repeat
                Keep := Tokens.Count() = 0;
                foreach Token in Tokens do begin
                    Token := Token.Trim();
                    if Token.EndsWith('*') then begin
                        if Fld.FieldName.StartsWith(Token.TrimEnd('*')) then
                            Keep := true;
                    end else
                        if Fld.FieldName = Token then
                            Keep := true;
                end;
                if Keep then
                    FieldNos.Add(Fld."No.");
            until Fld.Next() = 0;
    end;

    local procedure RowToJson(var RecRef: RecordRef; FieldNos: List of [Integer]): JsonObject
    var
        Row: JsonObject;
        FldRef: FieldRef;
        FieldNo: Integer;
        DecValue: Decimal;
        IntValue: Integer;
        BoolValue: Boolean;
    begin
        foreach FieldNo in FieldNos do begin
            FldRef := RecRef.Field(FieldNo);
            case FldRef.Type of
                FieldType::Decimal:
                    begin
                        DecValue := FldRef.Value;
                        Row.Add(FldRef.Name, DecValue);
                    end;
                FieldType::Integer:
                    begin
                        IntValue := FldRef.Value;
                        Row.Add(FldRef.Name, IntValue);
                    end;
                FieldType::Boolean:
                    begin
                        BoolValue := FldRef.Value;
                        Row.Add(FldRef.Name, BoolValue);
                    end;
                FieldType::Option:
                    Row.Add(FldRef.Name, Format(FldRef.Value));
                else
                    Row.Add(FldRef.Name, Format(FldRef.Value, 0, 9));
            end;
        end;
        exit(Row);
    end;
}
