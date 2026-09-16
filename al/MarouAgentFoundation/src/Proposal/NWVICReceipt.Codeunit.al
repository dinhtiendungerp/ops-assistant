/// <summary>
/// Intercompany phia NGUOI MUA (16/09/2026, Dung chot): Dakao mua tu Marou, Marou post xuat kho, Dakao nhan hang.
///
/// Hai viec:
///   1. `ShipmentStatus` doc sang company doi tac (ChangeCompany) xem don mua ben nay da co phieu giao hang ben kia chua.
///      Noi hai chung tu voi nhau bang `Sales Shipment Header."External Document No."` = so don mua, do Intercompany dien san.
///      Chi doc, khong ghi gi, nen goi bao nhieu lan cung duoc.
///   2. `PostReceipt` post nhan hang cho don mua do. CHI chay khi mot de xuat PostReceipt duoc NGUOI duyet
///      (codeunit "NWV Agent Proposal Mgt."), khong co duong nao khac goi toi. Quyen post nam trong permission set rieng
///      "NWV AGENT POST RCPT"; khong gan set do thi ham nay bao thieu quyen chu khong am tham bo qua.
///
/// So lo khong bia: lay dung lo ma doi tac da xuat, doc trong Item Ledger Entry cua phieu giao hang ben do, roi gan thanh
/// Reservation Entry tren dong don mua truoc khi post. Nho vay lo o Marou va lo o Dakao la mot, truy xuat duoc ca chuoi.
/// </summary>
codeunit 70113 "NWV IC Receipt"
{
    var
        NoPartnerErr: Label 'Purchase order %1 has no intercompany partner company to read from.', Comment = '%1 = purchase order no.';
        NoShipmentErr: Label 'Partner company %1 has not posted a shipment for purchase order %2 yet.', Comment = '%1 = company, %2 = order no.';
        NothingToReceiveErr: Label 'Purchase order %1 has no quantity left to receive.', Comment = '%1 = purchase order no.';
        MissingLotErr: Label 'Item %1 on purchase order %2 needs lot numbers, but the partner shipment does not carry any.', Comment = '%1 = item, %2 = order';

    // ------------------------------------------------------------------ doc trang thai giao hang
    /// <summary>
    /// config: {"vendorNo":"MAROU"} loc theo nha cung cap, bo trong thi lay moi don mua co IC Partner.
    /// Tra JSON: {"company":..,"workDate":..,"docs":[{purchaseOrder, outstanding, received, lines[], shipment:{posted,..,lines[]}}]}
    /// </summary>
    procedure ShipmentStatus(ConfigJson: Text): Text
    var
        PurchHeader: Record "Purchase Header";
        Config: JsonObject;
        Result: JsonObject;
        Docs: JsonArray;
        Output: Text;
        VendorNo: Code[20];
    begin
        if ConfigJson <> '' then
            Config.ReadFrom(ConfigJson);
        VendorNo := CopyStr(GetText(Config, 'vendorNo'), 1, MaxStrLen(VendorNo));
        PurchHeader.SetRange("Document Type", PurchHeader."Document Type"::Order);
        if VendorNo <> '' then
            PurchHeader.SetRange("Buy-from Vendor No.", VendorNo);
        PurchHeader.SetFilter("Buy-from IC Partner Code", '<>%1', '');
        if PurchHeader.FindSet() then
            repeat
                Docs.Add(OneOrder(PurchHeader));
            until PurchHeader.Next() = 0;
        Result.Add('company', CompanyName());
        Result.Add('workDate', Format(WorkDate(), 0, 9));
        Result.Add('docs', Docs);
        Result.WriteTo(Output);
        exit(Output);
    end;

    local procedure OneOrder(PurchHeader: Record "Purchase Header"): JsonObject
    var
        PurchLine: Record "Purchase Line";
        O: JsonObject;
        Lines: JsonArray;
        Partner: Text;
        Total: Decimal;
        Outstanding: Decimal;
        Received: Decimal;
    begin
        Partner := PartnerCompany(PurchHeader."Buy-from IC Partner Code");
        PurchLine.SetRange("Document Type", PurchHeader."Document Type");
        PurchLine.SetRange("Document No.", PurchHeader."No.");
        PurchLine.SetRange(Type, PurchLine.Type::Item);
        if PurchLine.FindSet() then
            repeat
                Lines.Add(OneOrderLine(PurchLine));
                Total += PurchLine.Quantity;
                Outstanding += PurchLine."Outstanding Quantity";
                Received += PurchLine."Quantity Received";
            until PurchLine.Next() = 0;
        O.Add('purchaseOrder', PurchHeader."No.");
        O.Add('vendorNo', PurchHeader."Buy-from Vendor No.");
        O.Add('vendorName', PurchHeader."Buy-from Vendor Name");
        O.Add('icPartner', PurchHeader."Buy-from IC Partner Code");
        O.Add('partnerCompany', Partner);
        O.Add('status', Format(PurchHeader.Status));
        O.Add('orderDate', Format(PurchHeader."Order Date", 0, 9));
        O.Add('expectedReceiptDate', Format(PurchHeader."Expected Receipt Date", 0, 9));
        O.Add('locationCode', PurchHeader."Location Code");
        O.Add('quantity', Total);
        O.Add('outstanding', Outstanding);
        O.Add('received', Received);
        O.Add('lines', Lines);
        O.Add('shipment', Shipment(Partner, PurchHeader."No."));
        exit(O);
    end;

    local procedure OneOrderLine(PurchLine: Record "Purchase Line"): JsonObject
    var
        O: JsonObject;
    begin
        O.Add('lineNo', PurchLine."Line No.");
        O.Add('itemNo', PurchLine."No.");
        O.Add('description', PurchLine.Description);
        O.Add('locationCode', PurchLine."Location Code");
        O.Add('quantity', PurchLine.Quantity);
        O.Add('outstanding', PurchLine."Outstanding Quantity");
        O.Add('received', PurchLine."Quantity Received");
        O.Add('unitOfMeasureCode', PurchLine."Unit of Measure Code");
        exit(O);
    end;

    local procedure Shipment(Partner: Text; OrderNo: Code[20]): JsonObject
    var
        SalesShptHeader: Record "Sales Shipment Header";
        O: JsonObject;
        Count: Integer;
    begin
        if (Partner = '') or not FindShipments(SalesShptHeader, Partner, OrderNo) then begin
            O.Add('posted', false);
            exit(O);
        end;
        Count := SalesShptHeader.Count();
        SalesShptHeader.FindLast();
        O.Add('posted', true);
        O.Add('no', SalesShptHeader."No.");
        O.Add('postingDate', Format(SalesShptHeader."Posting Date", 0, 9));
        O.Add('salesOrder', SalesShptHeader."Order No.");
        O.Add('sellToCustomerNo', SalesShptHeader."Sell-to Customer No.");
        O.Add('locationCode', SalesShptHeader."Location Code");
        O.Add('shipmentCount', Count);
        O.Add('lines', ShipmentLines(Partner, SalesShptHeader."No."));
        exit(O);
    end;

    local procedure FindShipments(var SalesShptHeader: Record "Sales Shipment Header"; Partner: Text; OrderNo: Code[20]): Boolean
    begin
        SalesShptHeader.Reset();
        SalesShptHeader.ChangeCompany(CopyStr(Partner, 1, 30));
        SalesShptHeader.SetRange("External Document No.", OrderNo);
        exit(SalesShptHeader.FindSet());
    end;

    local procedure ShipmentLines(Partner: Text; ShipmentNo: Code[20]): JsonArray
    var
        SalesShptLine: Record "Sales Shipment Line";
        Arr: JsonArray;
    begin
        SalesShptLine.ChangeCompany(CopyStr(Partner, 1, 30));
        SalesShptLine.SetRange("Document No.", ShipmentNo);
        SalesShptLine.SetRange(Type, SalesShptLine.Type::Item);
        if SalesShptLine.FindSet() then
            repeat
                Arr.Add(OneShipmentLine(Partner, SalesShptLine));
            until SalesShptLine.Next() = 0;
        exit(Arr);
    end;

    local procedure OneShipmentLine(Partner: Text; SalesShptLine: Record "Sales Shipment Line"): JsonObject
    var
        ItemLedgEntry: Record "Item Ledger Entry";
        O: JsonObject;
        Lots: JsonArray;
    begin
        O.Add('itemNo', SalesShptLine."No.");
        O.Add('description', SalesShptLine.Description);
        O.Add('quantity', SalesShptLine.Quantity);
        O.Add('unitOfMeasureCode', SalesShptLine."Unit of Measure Code");
        ItemLedgEntry.ChangeCompany(CopyStr(Partner, 1, 30));
        ItemLedgEntry.SetRange("Document No.", SalesShptLine."Document No.");
        ItemLedgEntry.SetRange("Document Line No.", SalesShptLine."Line No.");
        if ItemLedgEntry.FindSet() then
            repeat
                if ItemLedgEntry."Lot No." <> '' then
                    Lots.Add(OneLot(ItemLedgEntry));
            until ItemLedgEntry.Next() = 0;
        O.Add('lots', Lots);
        exit(O);
    end;

    local procedure OneLot(ItemLedgEntry: Record "Item Ledger Entry"): JsonObject
    var
        O: JsonObject;
    begin
        O.Add('lotNo', ItemLedgEntry."Lot No.");
        O.Add('quantity', -ItemLedgEntry.Quantity);
        O.Add('expirationDate', Format(ItemLedgEntry."Expiration Date", 0, 9));
        exit(O);
    end;

    // ------------------------------------------------------------------ post nhan hang
    /// <summary>
    /// Post Receive cho don mua. Goi tu "NWV Agent Proposal Mgt." sau khi nguoi duyet bam Duyet. Tra so phieu nhan.
    /// </summary>
    procedure PostReceipt(var PurchHeader: Record "Purchase Header"): Code[20]
    var
        PurchRcptHeader: Record "Purch. Rcpt. Header";
        PurchPost: Codeunit "Purch.-Post";
        Partner: Text;
    begin
        Partner := PartnerCompany(PurchHeader."Buy-from IC Partner Code");
        if Partner = '' then
            Error(NoPartnerErr, PurchHeader."No.");
        if not ShipmentPosted(Partner, PurchHeader."No.") then
            Error(NoShipmentErr, Partner, PurchHeader."No.");
        if OutstandingQty(PurchHeader) <= 0 then
            Error(NothingToReceiveErr, PurchHeader."No.");
        AssignLots(PurchHeader, Partner);
        PurchHeader.Receive := true;
        PurchHeader.Invoice := false;
        PurchPost.Run(PurchHeader);
        PurchRcptHeader.SetCurrentKey("Order No.");
        PurchRcptHeader.SetRange("Order No.", PurchHeader."No.");
        if PurchRcptHeader.FindLast() then
            exit(PurchRcptHeader."No.");
        exit('');
    end;

    procedure ShipmentPosted(Partner: Text; OrderNo: Code[20]): Boolean
    var
        SalesShptHeader: Record "Sales Shipment Header";
    begin
        if Partner = '' then
            exit(false);
        exit(FindShipments(SalesShptHeader, Partner, OrderNo));
    end;

    procedure PartnerCompany(ICPartnerCode: Code[20]): Text
    var
        ICPartner: Record "IC Partner";
        Company: Record Company;
    begin
        if ICPartnerCode = '' then
            exit('');
        if not ICPartner.Get(ICPartnerCode) then
            exit('');
        if ICPartner."Inbox Type" <> ICPartner."Inbox Type"::Database then
            exit('');
        if not Company.Get(CopyStr(ICPartner."Inbox Details", 1, 30)) then
            exit('');
        exit(Company.Name);
    end;

    local procedure OutstandingQty(PurchHeader: Record "Purchase Header") Qty: Decimal
    var
        PurchLine: Record "Purchase Line";
    begin
        PurchLine.SetRange("Document Type", PurchHeader."Document Type");
        PurchLine.SetRange("Document No.", PurchHeader."No.");
        PurchLine.SetRange(Type, PurchLine.Type::Item);
        if PurchLine.FindSet() then
            repeat
                Qty += PurchLine."Outstanding Quantity";
            until PurchLine.Next() = 0;
    end;

    /// <summary>Gan Reservation Entry mang so lo cua phieu giao hang doi tac len tung dong don mua co quan ly lo.</summary>
    local procedure AssignLots(PurchHeader: Record "Purchase Header"; Partner: Text)
    var
        PurchLine: Record "Purchase Line";
        Item: Record Item;
    begin
        PurchLine.SetRange("Document Type", PurchHeader."Document Type");
        PurchLine.SetRange("Document No.", PurchHeader."No.");
        PurchLine.SetRange(Type, PurchLine.Type::Item);
        PurchLine.SetFilter("Outstanding Quantity", '>%1', 0);
        if PurchLine.FindSet() then
            repeat
                if Item.Get(PurchLine."No.") then
                    if Item."Item Tracking Code" <> '' then
                        AssignLotsForLine(PurchLine, Partner, PurchHeader."No.");
            until PurchLine.Next() = 0;
    end;

    local procedure AssignLotsForLine(PurchLine: Record "Purchase Line"; Partner: Text; OrderNo: Code[20])
    var
        ReservEntry: Record "Reservation Entry";
        SalesShptHeader: Record "Sales Shipment Header";
        ItemLedgEntry: Record "Item Ledger Entry";
        Remaining: Decimal;
        Qty: Decimal;
    begin
        // Ai do da gan item tracking tay tren dong nay thi khong dung vao.
        ReservEntry.SetSourceFilter(Database::"Purchase Line", PurchLine."Document Type".AsInteger(), PurchLine."Document No.", PurchLine."Line No.", false);
        if not ReservEntry.IsEmpty() then
            exit;
        Remaining := PurchLine."Qty. to Receive";
        if Remaining <= 0 then
            Remaining := PurchLine."Outstanding Quantity";
        if not FindShipments(SalesShptHeader, Partner, OrderNo) then
            exit;
        repeat
            ItemLedgEntry.Reset();
            ItemLedgEntry.ChangeCompany(CopyStr(Partner, 1, 30));
            ItemLedgEntry.SetRange("Document No.", SalesShptHeader."No.");
            ItemLedgEntry.SetRange("Item No.", PurchLine."No.");
            ItemLedgEntry.SetFilter("Lot No.", '<>%1', '');
            if ItemLedgEntry.FindSet() then
                repeat
                    Qty := -ItemLedgEntry.Quantity;
                    if Qty > Remaining then
                        Qty := Remaining;
                    if Qty > 0 then begin
                        InsertLot(PurchLine, ItemLedgEntry."Lot No.", ItemLedgEntry."Expiration Date", Qty);
                        Remaining -= Qty;
                    end;
                until (ItemLedgEntry.Next() = 0) or (Remaining <= 0);
        until (SalesShptHeader.Next() = 0) or (Remaining <= 0);
        if Remaining > 0 then
            Error(MissingLotErr, PurchLine."No.", OrderNo);
    end;

    local procedure InsertLot(PurchLine: Record "Purchase Line"; LotNo: Code[50]; ExpirationDate: Date; Qty: Decimal)
    var
        ForReservEntry: Record "Reservation Entry";
        CreateReservEntry: Codeunit "Create Reserv. Entry";
        ReservStatus: Enum "Reservation Status";
    begin
        ForReservEntry.Init();
        ForReservEntry."Lot No." := LotNo;
        CreateReservEntry.SetDates(0D, ExpirationDate);
        CreateReservEntry.CreateReservEntryFor(
            Database::"Purchase Line", PurchLine."Document Type".AsInteger(), PurchLine."Document No.", '', 0, PurchLine."Line No.",
            PurchLine."Qty. per Unit of Measure", Qty, Qty * PurchLine."Qty. per Unit of Measure", ForReservEntry);
        CreateReservEntry.CreateEntry(
            PurchLine."No.", PurchLine."Variant Code", PurchLine."Location Code", PurchLine.Description,
            PurchLine."Expected Receipt Date", 0D, 0, ReservStatus::Surplus);
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
