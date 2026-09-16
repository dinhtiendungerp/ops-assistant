/// <summary>
/// Doi tac intercompany cho demo hai company (15/09/2026): Marou san xuat ban cho Dakao ban le.
///   - Trong NWV-DAKAO: vendor MAROU (hang cua hang mua tu Marou, giao thang toi tung cua hang).
///   - Trong NWV-MAROU: customer DAKAO.
/// Posting group chep tu mot vendor/customer noi dia co san (Cronus), vi API v2.0 khong phoi cac truong do.
/// Chi dung tren sandbox. Phoi ra ODataV4 ten `NWVDemoIntercompany`. Chay lai nhieu lan khong tao trung.
/// </summary>
codeunit 70258 "NWV Demo Intercompany"
{
    var
        ThieuMaErr: Label 'Phai truyen minhLa va doiTac (ma IC Partner).';
        KhongPhaiICErr: Label 'Don mua %1 khong co IC Partner: vendor chua duoc gan IC Partner Code.', Comment = '%1 = so don';
        KhongThayDonBanErr: Label 'Khong thay don ban nao trong company %2 mang External Document No. hoac so %1.', Comment = '%1 = so don, %2 = company';
        KhongDuLoErr: Label 'Ton dang mo cua %1 tai %2 khong du de gan lo cho don ban %3.', Comment = '%1 = item, %2 = location, %3 = so don';

    procedure EnsurePartners(configJson: Text): Text
    var
        Config: JsonObject;
        Token: JsonToken;
        Result: JsonObject;
        Output: Text;
    begin
        Config.ReadFrom(configJson);
        if Config.Get('vendor', Token) then
            Result.Add('vendor', EnsureVendor(Token.AsObject()));
        if Config.Get('customer', Token) then
            Result.Add('customer', EnsureCustomer(Token.AsObject()));
        Result.Add('company', CompanyName());
        Result.WriteTo(Output);
        exit(Output);
    end;

    /// <summary>
    /// Bat Intercompany chuan cua BC giua hai company (16/09/2026, Dung bac "demo thi lien quan gi ke toan"):
    ///   - IC Setup cua company hien tai: ma doi tac cua chinh minh, bat Auto. Send Transactions.
    ///   - IC Partner tro sang company kia: Inbox Type = Database, Inbox Details = ten company do, bat Auto. Accept Transactions,
    ///     Outbound Item No. Type = Internal No. (hai company dung chung danh muc nen khong can Common Item No.).
    ///   - Gan IC Partner Code len customer hoac vendor doi tac, de Purchase/Sales Header tu bat "Send IC Document".
    /// Tai khoan phai thu / phai tra lay tu posting group cua chinh customer/vendor do, khong bia so hieu tai khoan.
    /// config: {"minhLa":"DAKAO","doiTac":"MAROU","tenDoiTac":"Marou (san xuat)","companyDoiTac":"NWV-MAROU","vendorNo":"MAROU"}
    ///         hoac ...,"customerNo":"DAKAO" o phia ban.
    /// </summary>
    procedure EnsureIntercompany(configJson: Text): Text
    var
        ICSetup: Record "IC Setup";
        ICPartner: Record "IC Partner";
        Customer: Record Customer;
        Vendor: Record Vendor;
        CustPostingGroup: Record "Customer Posting Group";
        VendPostingGroup: Record "Vendor Posting Group";
        Config: JsonObject;
        Result: JsonObject;
        Output: Text;
        MinhLa: Code[20];
        DoiTac: Code[20];
        CustNo: Code[20];
        VendNo: Code[20];
    begin
        Config.ReadFrom(configJson);
        MinhLa := CopyStr(GetText(Config, 'minhLa'), 1, MaxStrLen(MinhLa));
        DoiTac := CopyStr(GetText(Config, 'doiTac'), 1, MaxStrLen(DoiTac));
        CustNo := CopyStr(GetText(Config, 'customerNo'), 1, MaxStrLen(CustNo));
        VendNo := CopyStr(GetText(Config, 'vendorNo'), 1, MaxStrLen(VendNo));
        if (MinhLa = '') or (DoiTac = '') then
            Error(ThieuMaErr);

        // 1. IC Setup cua company nay
        if not ICSetup.Get() then begin
            ICSetup.Init();
            ICSetup.Insert();
        end;
        ICSetup."IC Partner Code" := MinhLa;
        ICSetup."Auto. Send Transactions" := true;
        ICSetup.Modify();
        Result.Add('icPartnerCodeCuaMinh', MinhLa);

        // 2. IC Partner tro sang company kia
        if not ICPartner.Get(DoiTac) then begin
            ICPartner.Init();
            ICPartner.Code := DoiTac;
            ICPartner.Insert();
        end;
        ICPartner.Name := CopyStr(GetText(Config, 'tenDoiTac'), 1, MaxStrLen(ICPartner.Name));
        ICPartner."Inbox Type" := ICPartner."Inbox Type"::Database;
        ICPartner."Inbox Details" := CopyStr(GetText(Config, 'companyDoiTac'), 1, MaxStrLen(ICPartner."Inbox Details"));
        ICPartner."Auto. Accept Transactions" := true;
        ICPartner.Blocked := false;
        ICPartner."Outbound Sales Item No. Type" := ICPartner."Outbound Sales Item No. Type"::"Internal No.";
        ICPartner."Outbound Purch. Item No. Type" := ICPartner."Outbound Purch. Item No. Type"::"Internal No.";
        if CustNo <> '' then begin
            Customer.Get(CustNo);
            ICPartner."Customer No." := CustNo;
            if CustPostingGroup.Get(Customer."Customer Posting Group") then
                ICPartner."Receivables Account" := CustPostingGroup."Receivables Account";
            Customer."IC Partner Code" := DoiTac;
            // Kho xuat cho don ban intercompany. Dung chot 16/09/2026: lay W0003. Sales Header lay Location Code cua khach
            // khi validate Sell-to Customer No., nen dat o day la moi don ban tu Dakao deu co kho xuat.
            if GetText(Config, 'locationCode') <> '' then
                Customer.Validate("Location Code", CopyStr(GetText(Config, 'locationCode'), 1, MaxStrLen(Customer."Location Code")));
            Customer.Modify(true);
            Result.Add('customer', CustNo);
            Result.Add('customerLocation', Customer."Location Code");
        end;
        if VendNo <> '' then begin
            Vendor.Get(VendNo);
            ICPartner."Vendor No." := VendNo;
            if VendPostingGroup.Get(Vendor."Vendor Posting Group") then
                ICPartner."Payables Account" := VendPostingGroup."Payables Account";
            Vendor."IC Partner Code" := DoiTac;
            Vendor.Modify();
            Result.Add('vendor', VendNo);
        end;
        ICPartner.Modify();

        Result.Add('company', CompanyName());
        Result.Add('doiTac', DoiTac);
        Result.Add('inboxDetails', ICPartner."Inbox Details");
        Result.Add('receivablesAccount', ICPartner."Receivables Account");
        Result.Add('payablesAccount', ICPartner."Payables Account");
        Result.WriteTo(Output);
        exit(Output);
    end;

    /// <summary>
    /// Gui mot Purchase Order sang company doi tac. `SendPurchDoc` cua BC tu RELEASE don roi tao IC Outbox Transaction;
    /// Auto. Send Transactions dua sang inbox ben kia, Auto. Accept Transactions ben do tao Sales Order.
    /// Day la hanh dong cua NGUOI MUA, khong phai cua agent: tro ly chi goi khi co nguoi bam nut.
    /// </summary>
    procedure SendPurchaseOrder(docNo: Text): Text
    var
        PurchHeader: Record "Purchase Header";
        ICOutbox: Record "IC Outbox Transaction";
        ICInboxOutboxMgt: Codeunit ICInboxOutboxMgt;
        Result: JsonObject;
        Output: Text;
    begin
        PurchHeader.Get(PurchHeader."Document Type"::Order, CopyStr(docNo, 1, MaxStrLen(PurchHeader."No.")));
        if PurchHeader."Buy-from IC Partner Code" = '' then
            Error(KhongPhaiICErr, PurchHeader."No.");
        ICInboxOutboxMgt.SendPurchDoc(PurchHeader, false);
        PurchHeader.Get(PurchHeader."Document Type"::Order, PurchHeader."No.");
        Result.Add('company', CompanyName());
        Result.Add('purchaseOrder', PurchHeader."No.");
        Result.Add('status', Format(PurchHeader.Status));
        Result.Add('icPartner', PurchHeader."Buy-from IC Partner Code");
        ICOutbox.SetRange("Document No.", PurchHeader."No.");
        Result.Add('outboxTransactions', ICOutbox.Count());
        Result.WriteTo(Output);
        exit(Output);
    end;

    /// <summary>
    /// Marou xuat kho: post Ship cho don ban ma Intercompany da tao tu don mua `docNo` cua Dakao.
    ///
    /// Tren he that day la viec cua nguoi kho Marou, bam Post Shipment trong BC. O day co ham nay de demo chay duoc mot
    /// minh, va de khoi phai chon lo bang tay: mat hang cua Marou quan ly lo nen dong ban phai co Item Tracking truoc khi
    /// post. Lo chon theo FEFO (han dung gan nhat truoc) tren chinh ton dang mo tai kho xuat, khong bia so lo.
    /// </summary>
    procedure PostSalesShipment(docNo: Text): Text
    begin
        exit(PostSalesShipmentOn(docNo, ''));
    end;

    /// <summary>
    /// Nhu PostSalesShipment nhung dat ngay post. `postingDateText` dang yyyy-MM-dd, bo trong thi giu ngay cua don ban.
    ///
    /// Vi sao can (17/09/2026): tro ly so ngay xuat kho voi ngay hom nay de biet nen bao truoc hay nhac. Ngay cua don ban
    /// lay theo Work Date cua BC (bo demo neo 18/09), con tro ly chay theo ngay that, nen hai ben lech va buoc "bao trong
    /// ngay" khong bao gio chay. Truyen ngay vao thi demo dien duoc vao bat ky ngay nao.
    /// </summary>
    procedure PostSalesShipmentOn(docNo: Text; postingDateText: Text): Text
    var
        SalesHeader: Record "Sales Header";
        SalesShptHeader: Record "Sales Shipment Header";
        SalesPost: Codeunit "Sales-Post";
        Result: JsonObject;
        Output: Text;
        NgayPost: Date;
    begin
        SalesHeader.SetRange("Document Type", SalesHeader."Document Type"::Order);
        SalesHeader.SetRange("External Document No.", CopyStr(docNo, 1, MaxStrLen(SalesHeader."External Document No.")));
        if not SalesHeader.FindLast() then begin
            SalesHeader.Reset();
            if not SalesHeader.Get(SalesHeader."Document Type"::Order, CopyStr(docNo, 1, MaxStrLen(SalesHeader."No."))) then
                Error(KhongThayDonBanErr, docNo, CompanyName());
        end;
        if (postingDateText <> '') and Evaluate(NgayPost, postingDateText, 9) and (NgayPost <> 0D) then begin
            SalesHeader.Validate("Posting Date", NgayPost);
            SalesHeader.Modify(true);
        end;
        GanLoFEFO(SalesHeader);
        SalesHeader.Ship := true;
        SalesHeader.Invoice := false;
        SalesPost.Run(SalesHeader);
        Result.Add('company', CompanyName());
        Result.Add('salesOrder', SalesHeader."No.");
        Result.Add('externalDocumentNo', SalesHeader."External Document No.");
        SalesShptHeader.SetCurrentKey("Order No.");
        SalesShptHeader.SetRange("Order No.", SalesHeader."No.");
        if SalesShptHeader.FindLast() then begin
            Result.Add('shipment', SalesShptHeader."No.");
            Result.Add('postingDate', Format(SalesShptHeader."Posting Date", 0, 9));
        end;
        Result.WriteTo(Output);
        exit(Output);
    end;

    local procedure GanLoFEFO(SalesHeader: Record "Sales Header")
    var
        SalesLine: Record "Sales Line";
        Item: Record Item;
        Customer: Record Customer;
    begin
        SalesLine.SetRange("Document Type", SalesHeader."Document Type");
        SalesLine.SetRange("Document No.", SalesHeader."No.");
        SalesLine.SetRange(Type, SalesLine.Type::Item);
        SalesLine.SetFilter("Outstanding Quantity", '>%1', 0);
        if SalesLine.FindSet() then
            repeat
                // Don ban tao truoc khi gan Location Code cho khach hang DAKAO (16/09/2026) khong co dia diem xuat, nen FEFO
                // di tim ton tai dia diem rong va khong thay gi. Lay kho cua chinh khach hang de don cu van xuat duoc.
                if SalesLine."Location Code" = '' then
                    if Customer.Get(SalesHeader."Sell-to Customer No.") then
                        if Customer."Location Code" <> '' then begin
                            SalesLine.Validate("Location Code", Customer."Location Code");
                            SalesLine.Modify(true);
                        end;
                if Item.Get(SalesLine."No.") then
                    if Item."Item Tracking Code" <> '' then
                        GanLoChoDongBan(SalesLine);
            until SalesLine.Next() = 0;
    end;

    local procedure GanLoChoDongBan(SalesLine: Record "Sales Line")
    var
        ReservEntry: Record "Reservation Entry";
        ConLai: Decimal;
    begin
        ReservEntry.SetSourceFilter(Database::"Sales Line", SalesLine."Document Type".AsInteger(), SalesLine."Document No.", SalesLine."Line No.", false);
        if not ReservEntry.IsEmpty() then
            exit;
        ConLai := SalesLine."Qty. to Ship";
        if ConLai <= 0 then
            ConLai := SalesLine."Outstanding Quantity";
        // Hai luot, khong mot luot. FEFO tho lay lo co han gan nhat, ma kho demo con lo da qua han nen luot dau tien
        // xuat ngay mot lo het han sang cua hang (bat duoc 16/09/2026 voi don HO106201, lo L260908-33110B han 11/09).
        // Luot 1 chi lay lo con han tinh theo Work Date; luot 2 moi den lo qua han, va chi khi khong con gi khac.
        ConLai := LayLo(SalesLine, ConLai, StrSubstNo('%1..', Format(WorkDate(), 0, 9)));
        if ConLai > 0 then
            ConLai := LayLo(SalesLine, ConLai, StrSubstNo('<%1', Format(WorkDate(), 0, 9)));
        if ConLai > 0 then
            Error(KhongDuLoErr, SalesLine."No.", SalesLine."Location Code", SalesLine."Document No.");
    end;

    local procedure LayLo(SalesLine: Record "Sales Line"; ConLai: Decimal; LocHanDung: Text) ConThieu: Decimal
    var
        ItemLedgEntry: Record "Item Ledger Entry";
        Qty: Decimal;
    begin
        ConThieu := ConLai;
        ItemLedgEntry.SetCurrentKey("Item No.", Open, "Variant Code", Positive, "Location Code", "Expiration Date");
        ItemLedgEntry.SetRange("Item No.", SalesLine."No.");
        ItemLedgEntry.SetRange(Open, true);
        ItemLedgEntry.SetRange(Positive, true);
        ItemLedgEntry.SetRange("Location Code", SalesLine."Location Code");
        ItemLedgEntry.SetFilter("Lot No.", '<>%1', '');
        ItemLedgEntry.SetFilter("Remaining Quantity", '>%1', 0);
        ItemLedgEntry.SetFilter("Expiration Date", LocHanDung);
        ItemLedgEntry.SetAscending("Expiration Date", true);
        if ItemLedgEntry.FindSet() then
            repeat
                Qty := ItemLedgEntry."Remaining Quantity";
                if Qty > ConThieu then
                    Qty := ConThieu;
                if Qty > 0 then begin
                    ChenLo(SalesLine, ItemLedgEntry."Lot No.", ItemLedgEntry."Expiration Date", Qty);
                    ConThieu -= Qty;
                end;
            until (ItemLedgEntry.Next() = 0) or (ConThieu <= 0);
    end;

    local procedure ChenLo(SalesLine: Record "Sales Line"; LotNo: Code[50]; HanDung: Date; Qty: Decimal)
    var
        ForReservEntry: Record "Reservation Entry";
        CreateReservEntry: Codeunit "Create Reserv. Entry";
        ReservStatus: Enum "Reservation Status";
    begin
        ForReservEntry.Init();
        ForReservEntry."Lot No." := LotNo;
        CreateReservEntry.SetDates(0D, HanDung);
        CreateReservEntry.CreateReservEntryFor(
            Database::"Sales Line", SalesLine."Document Type".AsInteger(), SalesLine."Document No.", '', 0, SalesLine."Line No.",
            SalesLine."Qty. per Unit of Measure", Qty, Qty * SalesLine."Qty. per Unit of Measure", ForReservEntry);
        CreateReservEntry.CreateEntry(
            SalesLine."No.", SalesLine."Variant Code", SalesLine."Location Code", SalesLine.Description,
            0D, SalesLine."Shipment Date", 0, ReservStatus::Surplus);
    end;

    /// <summary>Dem chung tu IC de kiem sau khi gui: outbox ben gui, inbox va Sales Order ben nhan.</summary>
    procedure ICStatus(): Text
    var
        ICOutbox: Record "IC Outbox Transaction";
        ICInbox: Record "IC Inbox Transaction";
        HandledInbox: Record "Handled IC Inbox Trans.";
        SalesHeader: Record "Sales Header";
        Result: JsonObject;
        Output: Text;
    begin
        Result.Add('company', CompanyName());
        Result.Add('outbox', ICOutbox.Count());
        Result.Add('inbox', ICInbox.Count());
        Result.Add('handledInbox', HandledInbox.Count());
        SalesHeader.SetRange("Document Type", SalesHeader."Document Type"::Order);
        Result.Add('salesOrders', SalesHeader.Count());
        Result.WriteTo(Output);
        exit(Output);
    end;

    local procedure EnsureVendor(O: JsonObject): Text
    var
        Vendor: Record Vendor;
        Template: Record Vendor;
        No: Code[20];
    begin
        No := CopyStr(GetText(O, 'no'), 1, 20);
        if Vendor.Get(No) then
            exit('da co');
        if not Template.Get(CopyStr(GetText(O, 'copyFrom'), 1, 20)) then begin
            Template.SetRange("Currency Code", '');
            Template.SetFilter("Vendor Posting Group", '<>%1', '');
            Template.FindFirst();
        end;
        Vendor.Init();
        Vendor."No." := No;
        Vendor.Insert(true);
        Vendor.Validate(Name, CopyStr(GetText(O, 'name'), 1, MaxStrLen(Vendor.Name)));
        Vendor.Validate("Gen. Bus. Posting Group", Template."Gen. Bus. Posting Group");
        Vendor.Validate("VAT Bus. Posting Group", Template."VAT Bus. Posting Group");
        Vendor.Validate("Vendor Posting Group", Template."Vendor Posting Group");
        Vendor.Validate("Payment Terms Code", Template."Payment Terms Code");
        Vendor."Country/Region Code" := Template."Country/Region Code";
        Vendor.Modify(true);
        exit('tao moi, posting group chep tu ' + Template."No.");
    end;

    local procedure EnsureCustomer(O: JsonObject): Text
    var
        Customer: Record Customer;
        Template: Record Customer;
        No: Code[20];
    begin
        No := CopyStr(GetText(O, 'no'), 1, 20);
        if Customer.Get(No) then
            exit('da co');
        if not Template.Get(CopyStr(GetText(O, 'copyFrom'), 1, 20)) then begin
            Template.SetRange("Currency Code", '');
            Template.SetFilter("Customer Posting Group", '<>%1', '');
            Template.FindFirst();
        end;
        Customer.Init();
        Customer."No." := No;
        Customer.Insert(true);
        Customer.Validate(Name, CopyStr(GetText(O, 'name'), 1, MaxStrLen(Customer.Name)));
        Customer.Validate("Gen. Bus. Posting Group", Template."Gen. Bus. Posting Group");
        Customer.Validate("VAT Bus. Posting Group", Template."VAT Bus. Posting Group");
        Customer.Validate("Customer Posting Group", Template."Customer Posting Group");
        Customer.Validate("Payment Terms Code", Template."Payment Terms Code");
        Customer."Country/Region Code" := Template."Country/Region Code";
        Customer.Modify(true);
        exit('tao moi, posting group chep tu ' + Template."No.");
    end;

    local procedure GetText(O: JsonObject; Name: Text): Text
    var
        T: JsonToken;
    begin
        if O.Get(Name, T) then
            exit(T.AsValue().AsText());
        exit('');
    end;
}
