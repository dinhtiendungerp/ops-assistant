// UC3: scorecard nha cung cap tu dong don mua (Purchase Line, Document Type = Order, Type = Item) va phieu nhan da post
// (Purch. Rcpt. Line). AL thuan, khong goi AI. Cong thuc chep sang python/bc_agent/supplier.py de doi chieu doc lap.
//
// Moi dong don mua trong ky (Expected Receipt Date tu WorkDate() - Supplier History Days den WorkDate()):
// - Den han: Expected Receipt Date <= WorkDate().
// - Nhan du: Quantity Received >= Quantity. Ngay nhan du = Posting Date lon nhat cua phieu nhan cho dong do.
// - Dung han: nhan du va ngay nhan du <= Expected Receipt Date + On-time Tolerance Days.
// - Giao du lan dau: phieu nhan co Posting Date nho nhat da du so luong dong (cong cac phieu cung ngay).
// - Tre: ngay nhan du - Expected Receipt Date neu > 0; dong den han chua nhan du: WorkDate() - Expected Receipt Date.
// - Lead time hua = Expected Receipt Date - Order Date; lead time thuc = ngay nhan du - Order Date.
// - Qua han: con Outstanding Quantity, Expected Receipt Date trong ky lich su va WorkDate() > Expected Receipt Date + tolerance.
// Can xem: On-time % < Supplier On-time Warn % (khi co it nhat 3 dong den han), hoac co dong qua han.
codeunit 70121 "NWV Supplier Scorecard Calc"
{
    trigger OnRun()
    begin
        CalculateAll();
    end;

    var
        Setup: Record "NWV Agent Setup";
        LowOnTimeTxt: Label 'Giao đúng hạn %1%, dưới ngưỡng %2%.', Comment = '%1 = ty le, %2 = nguong';
        OverdueTxt: Label '%1 dòng quá hạn chưa nhận đủ.', Comment = '%1 = so dong';
        LateByKey: Dictionary of [Text, Integer];
        ReceivedByKey: Dictionary of [Text, Integer];

    procedure CalculateAll()
    var
        Card: Record "NWV Supplier Scorecard";
        Buf: Record "NWV Supplier Scorecard" temporary;
        PurchLine: Record "Purchase Line";
        AsOf: Date;
        FromDate: Date;
        RunAt: DateTime;
        Tolerance: Integer;
    begin
        Setup.GetRecordOnce();
        Clear(LateByKey);
        Clear(ReceivedByKey);
        AsOf := WorkDate();
        FromDate := AsOf - Setup.EffSupplierHistoryDays();
        Tolerance := Setup."On-time Tolerance Days";
        RunAt := CurrentDateTime();

        PurchLine.SetRange("Document Type", PurchLine."Document Type"::Order);
        PurchLine.SetRange(Type, PurchLine.Type::Item);
        PurchLine.SetFilter(Quantity, '>0');
        PurchLine.SetFilter("Buy-from Vendor No.", '<>%1', '');
        if PurchLine.FindSet() then
            repeat
                AddLine(Buf, PurchLine, PurchLine."Item Category Code", AsOf, FromDate, Tolerance);
                AddLine(Buf, PurchLine, '', AsOf, FromDate, Tolerance);
            until PurchLine.Next() = 0;

        Card.DeleteAll();
        Buf.Reset();
        if Buf.FindSet() then
            repeat
                // Nha cung cap khong co dong den han va khong co dong qua han trong ky thi khong co gi de cham
                // (vi du don Cronus treo tu 2024). Bo qua de scorecard khong day dong trong.
                if (Buf."Lines Due" > 0) or (Buf."Overdue Lines" > 0) then begin
                    Card := Buf;
                    Finish(Card, AsOf, FromDate, RunAt);
                    Card.Insert();
                end;
            until Buf.Next() = 0;

        Setup."Last Supplier Scorecard Run" := RunAt;
        Setup.Modify();
    end;

    // Buf dung tam cac truong: "Avg Delay Days" = tong ngay tre, "Avg Promised Lead Time" = tong lead hua (so dong = Lines Due),
    // "Avg Actual Lead Time" = tong lead thuc (so dong = Lines Completed), "First Delivery Complete %" = so dong giao du lan dau,
    // "Overdue Amount" = gia tri, "Lines On Time" dung dung nghia. So dong da nhan it nhat mot lan va so dong tre de o
    // hai dictionary rieng.
    local procedure AddLine(var Buf: Record "NWV Supplier Scorecard" temporary; PurchLine: Record "Purchase Line"; Category: Code[20]; AsOf: Date; FromDate: Date; Tolerance: Integer)
    var
        Vendor: Record Vendor;
        CompletedOn: Date;
        FirstReceiptDate: Date;
        FirstDayQty: Decimal;
        InPeriod: Boolean;
        Due: Boolean;
        Completed: Boolean;
        HasReceipt: Boolean;
        Delay: Integer;
    begin
        if not Buf.Get(PurchLine."Buy-from Vendor No.", Category) then begin
            Buf.Init();
            Buf."Vendor No." := PurchLine."Buy-from Vendor No.";
            Buf."Item Category Code" := Category;
            if Vendor.Get(PurchLine."Buy-from Vendor No.") then
                Buf."Vendor Name" := Vendor.Name;
            Buf.Insert();
        end;

        ReceiptInfo(PurchLine, CompletedOn, FirstReceiptDate, FirstDayQty, HasReceipt);
        Completed := (PurchLine."Quantity Received" >= PurchLine.Quantity) and HasReceipt;
        InPeriod := (PurchLine."Expected Receipt Date" >= FromDate) and (PurchLine."Expected Receipt Date" <= AsOf);
        Due := InPeriod;

        if PurchLine."Outstanding Quantity" > 0 then begin
            Buf."Open Lines" += 1;
            // Chi tinh qua han trong ky lich su: don treo nhieu nam (Cronus) khong noi gi ve nha cung cap hom nay.
            if (PurchLine."Expected Receipt Date" >= FromDate) and (AsOf > PurchLine."Expected Receipt Date" + Tolerance) then begin
                Buf."Overdue Lines" += 1;
                Buf."Overdue Qty" += PurchLine."Outstanding Quantity";
                Buf."Overdue Amount" += PurchLine."Outstanding Quantity" * PurchLine."Direct Unit Cost";
            end;
        end;
        if HasReceipt and (CompletedOn > Buf."Last Receipt Date") then
            Buf."Last Receipt Date" := CompletedOn;

        if Due then begin
            Buf."Lines Due" += 1;
            if PurchLine."Order Date" <> 0D then
                Buf."Avg Promised Lead Time" += PurchLine."Expected Receipt Date" - PurchLine."Order Date";
            if Completed then begin
                Buf."Lines Completed" += 1;
                if CompletedOn <= PurchLine."Expected Receipt Date" + Tolerance then
                    Buf."Lines On Time" += 1;
                if PurchLine."Order Date" <> 0D then
                    Buf."Avg Actual Lead Time" += CompletedOn - PurchLine."Order Date";
                Delay := CompletedOn - PurchLine."Expected Receipt Date";
            end else
                Delay := AsOf - PurchLine."Expected Receipt Date";
            if Delay > Tolerance then begin
                Buf."Avg Delay Days" += Delay;
                LateCount(Buf, 1);
            end;
            if HasReceipt then begin
                ReceivedCount(Buf, 1);
                if FirstDayQty >= PurchLine.Quantity then
                    Buf."First Delivery Complete %" += 1;
            end;
        end;
        Buf.Modify();
    end;

    local procedure ReceiptInfo(PurchLine: Record "Purchase Line"; var CompletedOn: Date; var FirstReceiptDate: Date; var FirstDayQty: Decimal; var HasReceipt: Boolean)
    var
        RcptLine: Record "Purch. Rcpt. Line";
    begin
        CompletedOn := 0D;
        FirstReceiptDate := 0D;
        FirstDayQty := 0;
        HasReceipt := false;
        RcptLine.SetRange("Order No.", PurchLine."Document No.");
        RcptLine.SetRange("Order Line No.", PurchLine."Line No.");
        RcptLine.SetFilter(Quantity, '<>0');
        if RcptLine.FindSet() then
            repeat
                HasReceipt := true;
                if RcptLine."Posting Date" > CompletedOn then
                    CompletedOn := RcptLine."Posting Date";
                if (FirstReceiptDate = 0D) or (RcptLine."Posting Date" < FirstReceiptDate) then begin
                    FirstReceiptDate := RcptLine."Posting Date";
                    FirstDayQty := 0;
                end;
                if RcptLine."Posting Date" = FirstReceiptDate then
                    FirstDayQty += RcptLine.Quantity;
            until RcptLine.Next() = 0;
    end;

    local procedure KeyOf(Buf: Record "NWV Supplier Scorecard" temporary): Text
    begin
        exit(Buf."Vendor No." + '|' + Buf."Item Category Code");
    end;

    local procedure LateCount(Buf: Record "NWV Supplier Scorecard" temporary; Add: Integer): Integer
    var
        V: Integer;
    begin
        if LateByKey.Get(KeyOf(Buf), V) then;
        V += Add;
        LateByKey.Set(KeyOf(Buf), V);
        exit(V);
    end;

    local procedure ReceivedCount(Buf: Record "NWV Supplier Scorecard" temporary; Add: Integer): Integer
    var
        V: Integer;
    begin
        if ReceivedByKey.Get(KeyOf(Buf), V) then;
        V += Add;
        ReceivedByKey.Set(KeyOf(Buf), V);
        exit(V);
    end;

    local procedure Finish(var Card: Record "NWV Supplier Scorecard"; AsOf: Date; FromDate: Date; RunAt: DateTime)
    var
        Late: Integer;
        Received: Integer;
        Reason: Text;
    begin
        Late := LateCount(Card, 0);
        Received := ReceivedCount(Card, 0);
        Card."Period From" := FromDate;
        Card."Period To" := AsOf;
        Card."As Of Date" := AsOf;
        Card."Calculated At" := RunAt;
        if Late > 0 then
            Card."Avg Delay Days" := Round(Card."Avg Delay Days" / Late, 0.1)
        else
            Card."Avg Delay Days" := 0;
        if Card."Lines Due" > 0 then begin
            Card."On-time %" := Round(Card."Lines On Time" / Card."Lines Due" * 100, 0.1);
            Card."Avg Promised Lead Time" := Round(Card."Avg Promised Lead Time" / Card."Lines Due", 0.1);
        end else
            Card."Avg Promised Lead Time" := 0;
        if Card."Lines Completed" > 0 then
            Card."Avg Actual Lead Time" := Round(Card."Avg Actual Lead Time" / Card."Lines Completed", 0.1)
        else
            Card."Avg Actual Lead Time" := 0;
        if Received > 0 then
            Card."First Delivery Complete %" := Round(Card."First Delivery Complete %" / Received * 100, 0.1)
        else
            Card."First Delivery Complete %" := 0;
        Card."Overdue Amount" := Round(Card."Overdue Amount", 0.01);

        if (Card."Lines Due" >= 3) and (Card."On-time %" < Setup.EffOnTimeWarn()) then
            Reason := StrSubstNo(LowOnTimeTxt, Format(Card."On-time %", 0, 9), Format(Setup.EffOnTimeWarn(), 0, 9));
        if Card."Overdue Lines" > 0 then begin
            if Reason <> '' then
                Reason += ' ';
            Reason += StrSubstNo(OverdueTxt, Card."Overdue Lines");
        end;
        Card."Needs Attention" := Reason <> '';
        Card."Attention Reason" := CopyStr(Reason, 1, MaxStrLen(Card."Attention Reason"));
    end;
}
