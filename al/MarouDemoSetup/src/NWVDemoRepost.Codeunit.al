/// <summary>
/// Post lai du lieu kho demo tu dau, chay qua S2S (ODataV4 `NWVDemoRepost`). Chi dung tren sandbox.
///
/// Vi sao co file nay (13/09/2026): Item Ledger Entry cua company NWV la ban lo duoc va vao sau khi post
/// (8/9 ma TRACKED chua co Item Tracking Code) va dong Sale cua 5 ma bi quy doi theo SLICE/PORTION. Chi sua
/// duoc bang xoa ledger kho roi post lai file import-full-journal.txt. Truoc day Dung xoa bang app
/// NWV Configuration tools, app do xoa giao dich cua ca company; o day chi xoa bang cua kho.
///
/// Thu tu goi: Preview -> ResetInventoryLedger('XOA-LEDGER-KHO-NWV') -> AssignTracking -> DeleteVariants ->
/// Prepare -> ImportLines (nhieu lan) -> PostRange (tung thang) -> BlockDemoLot.
/// </summary>
codeunit 70256 "NWV Demo Repost"
{
    Permissions =
        tabledata "Item Ledger Entry" = rd,
        tabledata "Value Entry" = rd,
        tabledata "Item Application Entry" = rd,
        tabledata "Item Application Entry History" = rd,
        tabledata "Item Register" = rd,
        tabledata "Item Entry Relation" = rd,
        tabledata "Value Entry Relation" = rd,
        tabledata "Avg. Cost Adjmt. Entry Point" = rd,
        tabledata "Post Value Entry to G/L" = rd,
        tabledata "G/L - Item Ledger Relation" = rd,
        tabledata "Reservation Entry" = rd,
        tabledata "Item Journal Line" = rimd,
        tabledata "Lot No. Information" = rm,
        tabledata "Transfer Header" = rd,
        tabledata "Transfer Line" = rd;

    var
        ConfirmTok: Label 'XOA-LEDGER-KHO-NWV', Locked = true;
        CleanupTok: Label 'XOA-THU-AGENT-NWV', Locked = true;
        WrongConfirmErr: Label 'Sai chuoi xac nhan. Truyen dung %1 de xoa ledger kho.', Comment = '%1 = chuoi';
        CompanyErr: Label 'Chi chay tren company NWV, dang o %1.', Comment = '%1 = company';
        MissingFilterErr: Label 'Phai truyen it nhat mot bo loc: actionType, status hoac resultDocNo.';
        MissingBatchErr: Label 'Phai truyen ten batch. Khong xoa toan bo Item Journal.';

    procedure Preview(): Text
    var
        Result: JsonObject;
        TransferLine: Record "Transfer Line";
        PurchLine: Record "Purchase Line";
        SalesLine: Record "Sales Line";
        WhseEntry: Record "Warehouse Entry";
        ReservEntry: Record "Reservation Entry";
        ItemJnlLine: Record "Item Journal Line";
        DemoSetup: Codeunit "NWV Demo Setup Mgt";
        Output: Text;
    begin
        AddCounts(Result);
        Result.Add('transferLines', TransferLine.Count());
        Result.Add('purchaseLines', PurchLine.Count());
        Result.Add('salesLines', SalesLine.Count());
        Result.Add('warehouseEntries', WhseEntry.Count());
        ReservEntry.SetRange("Source Type", Database::"Item Journal Line");
        Result.Add('reservationEntriesItemJournal', ReservEntry.Count());
        ReservEntry.SetRange("Source Type");
        Result.Add('reservationEntriesAll', ReservEntry.Count());
        ItemJnlLine.SetRange("Journal Template Name", DemoSetup.TemplateName());
        ItemJnlLine.SetRange("Journal Batch Name", DemoSetup.BatchName());
        Result.Add('batchLines', ItemJnlLine.Count());
        Result.Add('company', CompanyName());
        Result.WriteTo(Output);
        exit(Output);
    end;

    procedure ResetInventoryLedger(confirmText: Text): Text
    var
        ItemLedgEntry: Record "Item Ledger Entry";
        ValueEntry: Record "Value Entry";
        ItemApplEntry: Record "Item Application Entry";
        ItemApplHist: Record "Item Application Entry History";
        ItemRegister: Record "Item Register";
        ItemEntryRel: Record "Item Entry Relation";
        ValueEntryRel: Record "Value Entry Relation";
        AvgCostEntryPoint: Record "Avg. Cost Adjmt. Entry Point";
        PostValueToGL: Record "Post Value Entry to G/L";
        GLItemRel: Record "G/L - Item Ledger Relation";
        ReservEntry: Record "Reservation Entry";
        ItemJnlLine: Record "Item Journal Line";
        LotInfo: Record "Lot No. Information";
        DemoSetup: Codeunit "NWV Demo Setup Mgt";
        Before: JsonObject;
        Result: JsonObject;
        Output: Text;
    begin
        if confirmText <> ConfirmTok then
            Error(WrongConfirmErr, ConfirmTok);
        if CompanyName() <> 'NWV' then
            Error(CompanyErr, CompanyName());
        AddCounts(Before);

        ItemJnlLine.SetRange("Journal Template Name", DemoSetup.TemplateName());
        ItemJnlLine.SetRange("Journal Batch Name", DemoSetup.BatchName());
        ItemJnlLine.DeleteAll();
        ReservEntry.SetRange("Source Type", Database::"Item Journal Line");
        ReservEntry.DeleteAll();

        ItemApplEntry.DeleteAll();
        ItemApplHist.DeleteAll();
        ValueEntryRel.DeleteAll();
        ItemEntryRel.DeleteAll();
        GLItemRel.DeleteAll();
        PostValueToGL.DeleteAll();
        AvgCostEntryPoint.DeleteAll();
        ValueEntry.DeleteAll();
        ItemLedgEntry.DeleteAll();
        ItemRegister.DeleteAll();

        // Lo bi khoa thi CheckLotNoInfoNotBlocked chan post. Mo khoa, BlockDemoLot khoa lai sau khi post.
        LotInfo.SetRange(Blocked, true);
        LotInfo.ModifyAll(Blocked, false);

        Result.Add('before', Before);
        AddCounts(Result);
        Result.WriteTo(Output);
        exit(Output);
    end;

    procedure AssignTracking(itemsCsv: Text; trackingCode: Text): Text
    var
        Item: Record Item;
        Result: JsonArray;
        No: Text;
        Output: Text;
    begin
        foreach No in itemsCsv.Split(',') do begin
            Item.Get(CopyStr(No.Trim(), 1, 20));
            if Item."Item Tracking Code" <> trackingCode then begin
                Item.Validate("Item Tracking Code", CopyStr(trackingCode, 1, MaxStrLen(Item."Item Tracking Code")));
                Item.Modify(true);
                Result.Add(Item."No.");
            end;
        end;
        Result.WriteTo(Output);
        exit(Output);
    end;

    procedure DeleteVariants(itemsCsv: Text): Text
    var
        ItemVariant: Record "Item Variant";
        Result: JsonArray;
        No: Text;
        Output: Text;
    begin
        foreach No in itemsCsv.Split(',') do begin
            ItemVariant.SetRange("Item No.", CopyStr(No.Trim(), 1, 20));
            if ItemVariant.FindSet() then
                repeat
                    Result.Add(ItemVariant."Item No." + '/' + ItemVariant.Code);
                    ItemVariant.Delete(true);
                until ItemVariant.Next() = 0;
        end;
        Result.WriteTo(Output);
        exit(Output);
    end;

    procedure Prepare(): Text
    var
        DemoSetup: Codeunit "NWV Demo Setup Mgt";
    begin
        exit(DemoSetup.PrepareNoDialog());
    end;

    /// Chen dong vao batch NWVDEMO theo dung thu tu field ma Config Package ap: Item No., Posting Date,
    /// Entry Type, Document No., Location Code, Quantity, Unit Amount, Unit Cost, Amount, Discount Amount,
    /// Expiration Date (field 44, la o nhap han dung khi batch bat Item Tracking on Lines), Lot No.
    /// Moi phan tu: {line, item, date (yyyy-mm-dd), type, doc, loc, qty, unitAmount, unitCost, amount, discount, exp, lot}
    procedure ImportLines(linesJson: Text): Text
    var
        ItemJnlLine: Record "Item Journal Line";
        DemoSetup: Codeunit "NWV Demo Setup Mgt";
        Lines: JsonArray;
        Token: JsonToken;
        L: JsonObject;
        Result: JsonObject;
        D: Date;
        TypeText: Text;
        Count: Integer;
        Output: Text;
    begin
        Lines.ReadFrom(linesJson);
        foreach Token in Lines do begin
            L := Token.AsObject();
            ItemJnlLine.Init();
            ItemJnlLine."Journal Template Name" := DemoSetup.TemplateName();
            ItemJnlLine."Journal Batch Name" := DemoSetup.BatchName();
            ItemJnlLine."Line No." := GetInt(L, 'line');
            ItemJnlLine.Insert(true);
            ItemJnlLine.Validate("Item No.", CopyStr(GetText(L, 'item'), 1, 20));
            Evaluate(D, GetText(L, 'date'), 9);
            ItemJnlLine.Validate("Posting Date", D);
            TypeText := GetText(L, 'type');
            case TypeText of
                'Purchase':
                    ItemJnlLine.Validate("Entry Type", ItemJnlLine."Entry Type"::Purchase);
                'Sale':
                    ItemJnlLine.Validate("Entry Type", ItemJnlLine."Entry Type"::Sale);
                'Positive Adjmt.':
                    ItemJnlLine.Validate("Entry Type", ItemJnlLine."Entry Type"::"Positive Adjmt.");
                'Negative Adjmt.':
                    ItemJnlLine.Validate("Entry Type", ItemJnlLine."Entry Type"::"Negative Adjmt.");
                else
                    Error('Entry Type %1 chua ho tro.', TypeText);
            end;
            ItemJnlLine.Validate("Document No.", CopyStr(GetText(L, 'doc'), 1, 20));
            ItemJnlLine.Validate("Location Code", CopyStr(GetText(L, 'loc'), 1, 10));
            ItemJnlLine.Validate(Quantity, GetDec(L, 'qty'));
            ItemJnlLine.Validate("Unit Amount", GetDec(L, 'unitAmount'));
            ItemJnlLine.Validate("Unit Cost", GetDec(L, 'unitCost'));
            ItemJnlLine.Validate(Amount, GetDec(L, 'amount'));
            ItemJnlLine.Validate("Discount Amount", GetDec(L, 'discount'));
            if GetText(L, 'exp') <> '' then begin
                Evaluate(D, GetText(L, 'exp'), 9);
                ItemJnlLine.Validate("Expiration Date", D);
            end;
            if GetText(L, 'lot') <> '' then
                ItemJnlLine.Validate("Lot No.", CopyStr(GetText(L, 'lot'), 1, 50));
            ItemJnlLine.Modify(true);
            Count += 1;
        end;
        Result.Add('imported', Count);
        Result.Add('batchLines', DemoSetup.UnpostedLineCount());
        Result.WriteTo(Output);
        exit(Output);
    end;

    procedure PostRange(fromText: Text; toText: Text): Text
    var
        DemoSetup: Codeunit "NWV Demo Setup Mgt";
        FromDate: Date;
        ToDate: Date;
        Result: JsonObject;
        Output: Text;
    begin
        Evaluate(FromDate, fromText, 9);
        Evaluate(ToDate, toText, 9);
        DemoSetup.PostRangeNoDialog(FromDate, ToDate);
        Result.Add('from', fromText);
        Result.Add('to', toText);
        Result.Add('batchLinesLeft', DemoSetup.UnpostedLineCount());
        AddCounts(Result);
        Result.WriteTo(Output);
        exit(Output);
    end;

    procedure BlockDemoLot(): Text
    var
        DemoSetup: Codeunit "NWV Demo Setup Mgt";
    begin
        exit(DemoSetup.BlockDemoLotNoDialog());
    end;

    /// <summary>
    /// Don du lieu thu cua agent (14/09/2026). Transfer Order sinh ra khi duyet thu de xuat mang External Document No.
    /// 'AGENT ...'; con Open thi van cong vao Quantity in Transfer In/Out cua LS Replen. Item Quantity va lam lech
    /// ton hieu dung. Chi xoa TO chua ship. De xuat (bang 70102 cua app NWV Marou Agent) xoa qua RecordRef vi app nay
    /// khong phu thuoc app kia.
    /// </summary>
    procedure CleanupAgentTests(confirmText: Text): Text
    var
        TransferHeader: Record "Transfer Header";
        TransferLine: Record "Transfer Line";
        Proposals: RecordRef;
        Result: JsonObject;
        Deleted: JsonArray;
        Skipped: JsonArray;
        Output: Text;
    begin
        if confirmText <> CleanupTok then
            Error(WrongConfirmErr, CleanupTok);
        if CompanyName() <> 'NWV' then
            Error(CompanyErr, CompanyName());
        TransferHeader.SetFilter("External Document No.", 'AGENT *');
        if TransferHeader.FindSet() then
            repeat
                TransferLine.SetRange("Document No.", TransferHeader."No.");
                TransferLine.SetFilter("Quantity Shipped", '<>0');
                if TransferLine.IsEmpty() then begin
                    Deleted.Add(TransferHeader."No.");
                    TransferHeader.Delete(true);
                end else
                    Skipped.Add(TransferHeader."No.");
            until TransferHeader.Next() = 0;
        Result.Add('transferOrdersDeleted', Deleted);
        Result.Add('transferOrdersShippedKept', Skipped);
        Proposals.Open(70102);
        Result.Add('proposalsDeleted', Proposals.Count());
        Proposals.DeleteAll(true);
        Proposals.Close();
        Result.WriteTo(Output);
        exit(Output);
    end;

    /// <summary>
    /// Xoa Transfer Order do agent tao (External Document No. 'AGENT *') chua xuat, o company NWV-* bat ky. Khong dung de xuat.
    /// Vi sao (dem 16/09/2026): QA kich ban demo tren NWV-MAROU tao HO1039; CleanupAgentTests chi chay o company NWV.
    /// </summary>
    procedure DeleteAgentTransferOrders(confirmText: Text): Text
    var
        TransferHeader: Record "Transfer Header";
        TransferLine: Record "Transfer Line";
        Result: JsonObject;
        Deleted: JsonArray;
        Skipped: JsonArray;
        Output: Text;
    begin
        if confirmText <> CleanupTok then
            Error(WrongConfirmErr, CleanupTok);
        if CopyStr(CompanyName(), 1, 3) <> 'NWV' then
            Error(CompanyErr, CompanyName());
        TransferHeader.SetFilter("External Document No.", 'AGENT *');
        if TransferHeader.FindSet() then
            repeat
                TransferLine.SetRange("Document No.", TransferHeader."No.");
                TransferLine.SetFilter("Quantity Shipped", '<>0');
                if TransferLine.IsEmpty() then begin
                    Deleted.Add(TransferHeader."No.");
                    TransferHeader.Delete(true);
                end else
                    Skipped.Add(TransferHeader."No.");
            until TransferHeader.Next() = 0;
        Result.Add('company', CompanyName());
        Result.Add('transferOrdersDeleted', Deleted);
        Result.Add('transferOrdersShippedKept', Skipped);
        Result.WriteTo(Output);
        exit(Output);
    end;

    /// <summary>
    /// Xoa de xuat cua agent theo loai (vi du 'Transfer'), o company NWV-* bat ky. Dung 15/09/2026: NWV-DAKAO sao chep
    /// tu NWV mang theo 22 de xuat chuyen hang tu W0003, khong con dung khi Dakao mua thang tu Marou. Xoa hang loat, khong
    /// dong Transfer Order nao (de xuat da Executed thi TO da co nguoi xu ly). actionType rong la xoa het.
    /// </summary>
    procedure DeleteProposals(confirmText: Text; actionType: Text): Text
    var
        Proposals: RecordRef;
        ActionField: FieldRef;
        Result: JsonObject;
        Output: Text;
    begin
        if confirmText <> CleanupTok then
            Error(WrongConfirmErr, CleanupTok);
        if CopyStr(CompanyName(), 1, 3) <> 'NWV' then
            Error(CompanyErr, CompanyName());
        Proposals.Open(70102);
        if actionType <> '' then begin
            ActionField := Proposals.Field(4);          // "Action Type"
            ActionField.SetFilter(actionType);
        end;
        Result.Add('company', CompanyName());
        Result.Add('actionType', actionType);
        Result.Add('deleted', Proposals.Count());
        Proposals.DeleteAll(true);
        Proposals.Close();
        Result.WriteTo(Output);
        exit(Output);
    end;

    /// <summary>
    /// Xoa de xuat theo bo loc hep hon DeleteProposals: loai hanh dong, trang thai, va so chung tu ket qua. Dung 16/09/2026
    /// de don du lieu truoc buoi demo: bo 19 de xuat Transfer da tu choi o Marou, 7 Purchase da tu choi o Dakao, hai de xuat
    /// PostReceipt con Proposed cua lan dien thu, ma KHONG dung den de xuat Executed dang tro toi PO va phieu nhan that.
    /// Tham so rong la khong loc theo truong do. Chi chay o company NWV-*.
    /// </summary>
    procedure DeleteProposalsFiltered(confirmText: Text; actionType: Text; status: Text; resultDocNo: Text): Text
    var
        Proposals: RecordRef;
        F: FieldRef;
        Result: JsonObject;
        Output: Text;
    begin
        if confirmText <> CleanupTok then
            Error(WrongConfirmErr, CleanupTok);
        if CopyStr(CompanyName(), 1, 3) <> 'NWV' then
            Error(CompanyErr, CompanyName());
        if (actionType = '') and (status = '') and (resultDocNo = '') then
            Error(MissingFilterErr);
        Proposals.Open(70102);
        if actionType <> '' then begin
            F := Proposals.Field(4);            // "Action Type"
            F.SetFilter(actionType);
        end;
        if status <> '' then begin
            F := Proposals.Field(5);            // "Status"
            F.SetFilter(status);
        end;
        if resultDocNo <> '' then begin
            F := Proposals.Field(51);           // "Result Document No."
            F.SetFilter(resultDocNo);
        end;
        Result.Add('company', CompanyName());
        Result.Add('actionType', actionType);
        Result.Add('status', status);
        Result.Add('resultDocNo', resultDocNo);
        Result.Add('deleted', Proposals.Count());
        Proposals.DeleteAll(true);
        Proposals.Close();
        Result.WriteTo(Output);
        exit(Output);
    end;

    /// <summary>
    /// Xoa dong Item Journal CHUA POST trong mot batch, o company NWV-*. Dung 16/09/2026: hai dong nhap do thu luong huy
    /// (UC2 G2) nam trong batch AGENT cua NWV-MAROU, trong do mot dong mang Document No. cat cut tu GUID truoc khi doi sang
    /// Entry No. Chi xoa dong journal; khong dung den Item Ledger Entry hay de xuat da sinh ra chung.
    /// </summary>
    procedure DeleteJournalLines(confirmText: Text; templateName: Text; batchName: Text): Text
    var
        ItemJnlLine: Record "Item Journal Line";
        Result: JsonObject;
        DocNos: JsonArray;
        Output: Text;
    begin
        if confirmText <> CleanupTok then
            Error(WrongConfirmErr, CleanupTok);
        if CopyStr(CompanyName(), 1, 3) <> 'NWV' then
            Error(CompanyErr, CompanyName());
        if batchName = '' then
            Error(MissingBatchErr);
        ItemJnlLine.SetRange("Journal Template Name", CopyStr(templateName, 1, MaxStrLen(ItemJnlLine."Journal Template Name")));
        ItemJnlLine.SetRange("Journal Batch Name", CopyStr(batchName, 1, MaxStrLen(ItemJnlLine."Journal Batch Name")));
        if ItemJnlLine.FindSet() then
            repeat
                DocNos.Add(ItemJnlLine."Document No.");
            until ItemJnlLine.Next() = 0;
        Result.Add('company', CompanyName());
        Result.Add('template', templateName);
        Result.Add('batch', batchName);
        Result.Add('deleted', ItemJnlLine.Count());
        Result.Add('documentNos', DocNos);
        ItemJnlLine.DeleteAll(true);
        Result.WriteTo(Output);
        exit(Output);
    end;

    local procedure AddCounts(var Result: JsonObject)
    var
        ItemLedgEntry: Record "Item Ledger Entry";
        ValueEntry: Record "Value Entry";
        ItemApplEntry: Record "Item Application Entry";
        LotInfo: Record "Lot No. Information";
    begin
        Result.Add('itemLedgerEntries', ItemLedgEntry.Count());
        ItemLedgEntry.SetFilter("Lot No.", '<>%1', '');
        Result.Add('itemLedgerEntriesWithLot', ItemLedgEntry.Count());
        Result.Add('valueEntries', ValueEntry.Count());
        Result.Add('itemApplicationEntries', ItemApplEntry.Count());
        Result.Add('lotNoInformation', LotInfo.Count());
    end;

    local procedure GetText(L: JsonObject; Name: Text): Text
    var
        T: JsonToken;
    begin
        if not L.Get(Name, T) then
            exit('');
        if T.AsValue().IsNull() then
            exit('');
        exit(T.AsValue().AsText());
    end;

    local procedure GetDec(L: JsonObject; Name: Text): Decimal
    var
        T: JsonToken;
    begin
        if not L.Get(Name, T) then
            exit(0);
        exit(T.AsValue().AsDecimal());
    end;

    local procedure GetInt(L: JsonObject; Name: Text): Integer
    var
        T: JsonToken;
    begin
        L.Get(Name, T);
        exit(T.AsValue().AsInteger());
    end;
}
