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
            Customer.Modify();
            Result.Add('customer', CustNo);
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
