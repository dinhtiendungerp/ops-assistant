// Du lieu demo cho UC3 (scorecard nha cung cap va don mua qua han). Chi dung tren sandbox. Web service NWVDemoSupplier.
//
// Vi sao phai co dia diem nhan rieng (14/09/2026): scorecard can phieu nhan da post, ma post nhan hang tao Item Ledger
// Entry. Nhan vao W0003 hay cua hang se lam doi ton, doi bang Inventory Health (dang khop 100% voi uc2-expected.json)
// va doi so LS Replenishment. Nen lich su nhan hang di vao dia diem NCC-NHAN, va ngay sau moi phieu nhan co mot dong
// Negative Adjmt. cung so luong de ton tai NCC-NHAN luon ve 0: Inventory Health chi lap dong cho ton con mo, LS khong
// tinh dia diem nay. Don mua CON MO (chua nhan) thi dat o W0003 va cua hang that, vi do la thu tro ly phai bao.
//
// Ke hoach don mua (ngay, so luong, lan giao) sinh bang tools/supplier_demo.py voi seed co dinh, gui vao dang JSON:
// {"receivingLocation": "NCC-NHAN", "orders": [{"key": "NCC-0001", "vendorNo": "44030", "orderDate": "2026-04-06",
//   "locationCode": "NCC-NHAN", "lines": [{"itemNo": "10000", "quantity": 48, "unitCost": 0.9, "expectedReceiptDate": "2026-04-09"}],
//   "receipts": [{"date": "2026-04-09", "lines": [{"line": 0, "quantity": 48}]}]}]}
// Moi don gan "Vendor Order No." = key; don co key da ton tai (don mo hoac phieu nhan) thi bo qua, nen chay lai an toan.
codeunit 70257 "NWV Demo Supplier Data"
{
    Permissions =
        tabledata "Purchase Header" = rimd,
        tabledata "Purchase Line" = rimd,
        tabledata "Purch. Rcpt. Header" = r,
        tabledata Location = ri,
        tabledata "Inventory Posting Setup" = ri,
        tabledata "VAT Product Posting Group" = ri,
        tabledata "VAT Posting Setup" = ri;

    var
        CompanyErr: Label 'Chi chay tren company NWV, dang o %1.', Comment = '%1 = company';
        LocationNameTxt: Label 'Khu nhận hàng NCC (demo)';

    procedure CreateSupplierHistory(planJson: Text): Text
    var
        Plan: JsonObject;
        Orders: JsonArray;
        OrderTok: JsonToken;
        Result: JsonObject;
        Errors: JsonArray;
        Created: Integer;
        Skipped: Integer;
        Receipts: Integer;
        RecvLoc: Code[10];
        Output: Text;
        Msg: Text;
    begin
        if CompanyName() <> 'NWV' then
            Error(CompanyErr, CompanyName());
        Plan.ReadFrom(planJson);
        RecvLoc := CopyStr(GetText(Plan, 'receivingLocation'), 1, 10);
        if RecvLoc <> '' then
            EnsureLocation(RecvLoc, 'W0003');
        Plan.Get('orders', OrderTok);
        Orders := OrderTok.AsArray();
        foreach OrderTok in Orders do begin
            Msg := CreateOrder(OrderTok.AsObject(), Receipts);
            case Msg of
                'created':
                    Created += 1;
                'skipped':
                    Skipped += 1;
                else
                    Errors.Add(Msg);
            end;
        end;
        Result.Add('ordersCreated', Created);
        Result.Add('ordersSkipped', Skipped);
        Result.Add('receiptsPosted', Receipts);
        Result.Add('errors', Errors);
        Result.WriteTo(Output);
        exit(Output);
    end;

    local procedure CreateOrder(O: JsonObject; var Receipts: Integer): Text
    var
        PurchHeader: Record "Purchase Header";
        PurchLine: Record "Purchase Line";
        RcptHeader: Record "Purch. Rcpt. Header";
        LinesTok: JsonToken;
        LineTok: JsonToken;
        RcptTok: JsonToken;
        L: JsonObject;
        OrderKey: Text[35];
        LineNo: Integer;
        OrderDate: Date;
        ExpDate: Date;
    begin
        OrderKey := CopyStr(GetText(O, 'key'), 1, 35);
        OrderDate := GetDate(O, 'orderDate');
        PurchHeader.SetRange("Document Type", PurchHeader."Document Type"::Order);
        PurchHeader.SetRange("Vendor Order No.", OrderKey);
        if PurchHeader.FindFirst() then begin
            FixOrderDate(PurchHeader."No.", OrderDate);
            exit('skipped');
        end;
        RcptHeader.SetRange("Vendor Order No.", OrderKey);
        if not RcptHeader.IsEmpty() then
            exit('skipped');

        PurchHeader.Init();
        PurchHeader."Document Type" := PurchHeader."Document Type"::Order;
        PurchHeader.Insert(true);
        PurchHeader.Validate("Buy-from Vendor No.", CopyStr(GetText(O, 'vendorNo'), 1, 20));
        PurchHeader.Validate("Order Date", OrderDate);
        PurchHeader.Validate("Posting Date", OrderDate);
        PurchHeader.Validate("Document Date", OrderDate);
        PurchHeader."Vendor Order No." := OrderKey;
        PurchHeader.Validate("Location Code", CopyStr(GetText(O, 'locationCode'), 1, 10));
        PurchHeader.Modify(true);

        O.Get('lines', LinesTok);
        foreach LineTok in LinesTok.AsArray() do begin
            L := LineTok.AsObject();
            LineNo += 10000;
            PurchLine.Init();
            PurchLine."Document Type" := PurchHeader."Document Type";
            PurchLine."Document No." := PurchHeader."No.";
            PurchLine."Line No." := LineNo;
            PurchLine.Insert(true);
            PurchLine.Validate(Type, PurchLine.Type::Item);
            EnsureVat(CopyStr(GetText(L, 'itemNo'), 1, 20), PurchHeader."VAT Bus. Posting Group");
            PurchLine.Validate("No.", CopyStr(GetText(L, 'itemNo'), 1, 20));
            PurchLine.Validate("Location Code", PurchHeader."Location Code");
            PurchLine.Validate(Quantity, GetDec(L, 'quantity'));
            PurchLine.Validate("Direct Unit Cost", GetDec(L, 'unitCost'));
            ExpDate := GetDate(L, 'expectedReceiptDate');
            PurchLine.Validate("Expected Receipt Date", ExpDate);
            PurchLine."Expected Receipt Date" := ExpDate;
            // Validate Expected Receipt Date tinh nguoc Order Date = Planned Receipt Date - Lead Time Calculation (rong thi
            // bang ngay hen), nen lead time hua ve 0. Gan lai ngay dat that. Bat duoc o don demo dau tien 14/09/2026.
            PurchLine."Order Date" := OrderDate;
            PurchLine.Modify(true);
        end;
        Commit();

        if O.Get('receipts', RcptTok) then
            foreach RcptTok in RcptTok.AsArray() do begin
                if not PostReceipt(PurchHeader."No.", RcptTok.AsObject()) then
                    exit(StrSubstNo('%1: %2', OrderKey, GetLastErrorText()));
                Receipts += 1;
            end;
        exit('created');
    end;

    local procedure PostReceipt(OrderNo: Code[20]; R: JsonObject): Boolean
    var
        PurchHeader: Record "Purchase Header";
        PurchLine: Record "Purchase Line";
        RcptHeader: Record "Purch. Rcpt. Header";
        RcptLine: Record "Purch. Rcpt. Line";
        LinesTok: JsonToken;
        LineTok: JsonToken;
        L: JsonObject;
        Qty: Dictionary of [Integer, Decimal];
        PostDate: Date;
        Idx: Integer;
        Q: Decimal;
    begin
        PostDate := GetDate(R, 'date');
        R.Get('lines', LinesTok);
        foreach LineTok in LinesTok.AsArray() do begin
            L := LineTok.AsObject();
            Qty.Set((GetInt(L, 'line') + 1) * 10000, GetDec(L, 'quantity'));
        end;

        PurchHeader.Get(PurchHeader."Document Type"::Order, OrderNo);
        PurchLine.SetRange("Document Type", PurchHeader."Document Type");
        PurchLine.SetRange("Document No.", OrderNo);
        if PurchLine.FindSet(true) then
            repeat
                if Qty.Get(PurchLine."Line No.", Q) then
                    PurchLine.Validate("Qty. to Receive", Q)
                else
                    PurchLine.Validate("Qty. to Receive", 0);
                PurchLine.Validate("Qty. to Invoice", 0);
                PurchLine.Modify(true);
            until PurchLine.Next() = 0;
        PurchHeader.Validate("Posting Date", PostDate);
        PurchHeader.Receive := true;
        PurchHeader.Invoice := false;
        PurchHeader.Modify(true);
        Commit();
        if not Codeunit.Run(Codeunit::"Purch.-Post", PurchHeader) then
            exit(false);

        // Dua ton tai dia diem nhan ve 0 ngay trong ngay, xem giai thich dau file.
        RcptHeader.SetRange("Order No.", OrderNo);
        RcptHeader.SetRange("Posting Date", PostDate);
        if RcptHeader.FindLast() then begin
            RcptLine.SetRange("Document No.", RcptHeader."No.");
            RcptLine.SetRange(Type, RcptLine.Type::Item);
            RcptLine.SetFilter(Quantity, '>0');
            if RcptLine.FindSet() then
                repeat
                    if IsReceivingOnly(RcptLine."Location Code") then
                        PostOffset(RcptLine, RcptHeader."No.");
                until RcptLine.Next() = 0;
        end;
        Commit();
        exit(true);
    end;

    local procedure FixOrderDate(OrderNo: Code[20]; OrderDate: Date)
    var
        PurchLine: Record "Purchase Line";
    begin
        PurchLine.SetRange("Document Type", PurchLine."Document Type"::Order);
        PurchLine.SetRange("Document No.", OrderNo);
        PurchLine.SetFilter("Order Date", '<>%1', OrderDate);
        PurchLine.ModifyAll("Order Date", OrderDate);
    end;

    local procedure IsReceivingOnly(LocationCode: Code[10]): Boolean
    begin
        exit(LocationCode = 'NCC-NHAN');
    end;

    local procedure PostOffset(RcptLine: Record "Purch. Rcpt. Line"; DocNo: Code[20])
    var
        ItemJnlLine: Record "Item Journal Line";
        ItemJnlPostLine: Codeunit "Item Jnl.-Post Line";
    begin
        ItemJnlLine.Init();
        ItemJnlLine."Posting Date" := RcptLine."Posting Date";
        ItemJnlLine."Document Date" := RcptLine."Posting Date";
        ItemJnlLine."Document No." := DocNo;
        ItemJnlLine."Entry Type" := ItemJnlLine."Entry Type"::"Negative Adjmt.";
        ItemJnlLine.Validate("Item No.", RcptLine."No.");
        ItemJnlLine.Validate("Location Code", RcptLine."Location Code");
        ItemJnlLine.Validate("Unit of Measure Code", RcptLine."Unit of Measure Code");
        ItemJnlLine.Validate(Quantity, RcptLine.Quantity);
        ItemJnlLine.Description := CopyStr('Chuyen vao kho sau nhan hang NCC (demo)', 1, MaxStrLen(ItemJnlLine.Description));
        ItemJnlPostLine.RunWithCheck(ItemJnlLine);
    end;

    // Du lieu Cronus cua company NWV co item mang VAT Prod. Posting Group REDUCED ma bang VAT Product Posting Group khong
    // co dong nao (bat duoc 14/09/2026 khi tao dong don mua dau tien). Tao nhom va VAT Posting Setup 0% cho cap con thieu,
    // chep tai khoan tu mot dong co san cung VAT Bus. Posting Group. Phieu nhan khong post VAT nen 0% khong anh huong so.
    local procedure EnsureVat(ItemNo: Code[20]; VatBus: Code[20])
    var
        Item: Record Item;
        VatProd: Record "VAT Product Posting Group";
        VatSetup: Record "VAT Posting Setup";
        Template: Record "VAT Posting Setup";
    begin
        if not Item.Get(ItemNo) then
            exit;
        if Item."VAT Prod. Posting Group" = '' then
            exit;
        if not VatProd.Get(Item."VAT Prod. Posting Group") then begin
            VatProd.Init();
            VatProd.Code := Item."VAT Prod. Posting Group";
            VatProd.Description := CopyStr('Demo Marou', 1, MaxStrLen(VatProd.Description));
            VatProd.Insert();
        end;
        if VatSetup.Get(VatBus, Item."VAT Prod. Posting Group") then
            exit;
        Template.SetRange("VAT Bus. Posting Group", VatBus);
        if Template.FindFirst() then
            VatSetup := Template
        else
            VatSetup.Init();
        VatSetup."VAT Bus. Posting Group" := VatBus;
        VatSetup."VAT Prod. Posting Group" := Item."VAT Prod. Posting Group";
        VatSetup."VAT Identifier" := Item."VAT Prod. Posting Group";
        VatSetup."VAT %" := 0;
        VatSetup.Insert();
    end;

    local procedure EnsureLocation(LocCode: Code[10]; CopyPostingFrom: Code[10])
    var
        Location: Record Location;
        InvPostSetup: Record "Inventory Posting Setup";
        NewSetup: Record "Inventory Posting Setup";
    begin
        if not Location.Get(LocCode) then begin
            Location.Init();
            Location.Code := LocCode;
            Location.Name := LocationNameTxt;
            Location.Insert(true);
        end;
        InvPostSetup.SetRange("Location Code", CopyPostingFrom);
        if InvPostSetup.FindSet() then
            repeat
                if not NewSetup.Get(LocCode, InvPostSetup."Invt. Posting Group Code") then begin
                    NewSetup := InvPostSetup;
                    NewSetup."Location Code" := LocCode;
                    NewSetup.Insert();
                end;
            until InvPostSetup.Next() = 0;
    end;

    local procedure GetText(O: JsonObject; Name: Text): Text
    var
        T: JsonToken;
    begin
        if not O.Get(Name, T) then
            exit('');
        if T.AsValue().IsNull() then
            exit('');
        exit(T.AsValue().AsText());
    end;

    local procedure GetDec(O: JsonObject; Name: Text): Decimal
    var
        T: JsonToken;
    begin
        if not O.Get(Name, T) then
            exit(0);
        exit(T.AsValue().AsDecimal());
    end;

    local procedure GetInt(O: JsonObject; Name: Text): Integer
    var
        T: JsonToken;
    begin
        O.Get(Name, T);
        exit(T.AsValue().AsInteger());
    end;

    local procedure GetDate(O: JsonObject; Name: Text): Date
    var
        D: Date;
    begin
        Evaluate(D, GetText(O, Name), 9);
        exit(D);
    end;
}
