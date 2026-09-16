/// <summary>
/// Doi tac intercompany cho demo hai company (15/09/2026): Marou san xuat ban cho Dakao ban le.
///   - Trong NWV-DAKAO: vendor MAROU (hang cua hang mua tu Marou, giao thang toi tung cua hang).
///   - Trong NWV-MAROU: customer DAKAO.
/// Posting group chep tu mot vendor/customer noi dia co san (Cronus), vi API v2.0 khong phoi cac truong do.
/// Chi dung tren sandbox. Phoi ra ODataV4 ten `NWVDemoIntercompany`. Chay lai nhieu lan khong tao trung.
/// </summary>
codeunit 70258 "NWV Demo Intercompany"
{
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
