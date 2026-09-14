/// <summary>
/// Cac thao tac quanh viec nap bo du lieu demo Marou. Moi thu o day deu la viec truoc kia
/// phai bam tay trong BC.
///
/// Bon viec:
///   1. Tao Item Journal Template ITEM va batch NWVDEMO, de Config Package co cho ma chen dong.
///   2. Noi rong Allow Posting From/To cho phu khoang ngay cua du lieu.
///   3. Post batch NWVDEMO theo tung thang. 24.759 dong post mot lan la mot giao dich qua lon.
///      Codeunit 23 "Item Jnl.-Post Batch" giu nguyen bo loc cua record truyen vao, va
///      HandleNonRecurringLine xoa dong bang ItemJnlLine3.Copy roi DeleteAll nen chi xoa
///      dong nam trong bo loc. Vi vay cat theo Posting Date la an toan.
///   4. Khoa lo dung cho kich ban thu hoi. Phai lam sau khi post, vi CheckLotNoInfoNotBlocked
///      trong ItemJnlPostLine chan post neu lo da bi khoa.
/// </summary>
codeunit 70250 "NWV Demo Setup Mgt"
{
    var
        TemplateNameTok: Label 'ITEM', Locked = true;
        BatchNameTok: Label 'NWVDEMO', Locked = true;
        BlockedItemTok: Label '33170', Locked = true;
        BlockedLotTok: Label 'L260908-33170B', Locked = true;
        TemplateDescTxt: Label 'Item Journal';
        BatchDescTxt: Label 'Du lieu demo Marou';
        NoLinesErr: Label 'Batch %1 khong co dong nao de post. Import Config Package truoc da.', Comment = '%1 = ten batch';
        NoLotErr: Label 'Khong thay Lot No. Information cho item %1 lo %2. Post du lieu xong roi hay chay lai.', Comment = '%1 = so item, %2 = so lo';
        LotBlockedMsg: Label 'Da khoa lo %1 cua item %2.', Comment = '%1 = so lo, %2 = so item';
        PostedMsg: Label 'Da post %1 dot theo thang. Con %2 dong chua post trong batch.', Comment = '%1 = so dot, %2 = so dong';
        PreparedMsg: Label 'Template %1 va batch %2 da san sang. Allow Posting From %3, Allow Posting To %4.', Comment = '%1 = template, %2 = batch, %3 = tu ngay, %4 = den ngay';
        DeleteQst: Label 'Xoa toan bo dong chua post trong batch %1?', Comment = '%1 = ten batch';
        DeletedMsg: Label 'Da xoa %1 dong.', Comment = '%1 = so dong';
        StuckErr: Label 'Post dot %1..%2 khong lam giam so dong con lai. Dung lai de khong lap vo han.', Comment = '%1 = tu ngay, %2 = den ngay';
        ProgressTxt: Label 'Post batch #1##########', Comment = '#1 = khoang ngay dang post';
        DefaultFromDate: Label '2026-03-01', Locked = true;
        DefaultToDate: Label '2026-09-30', Locked = true;

    procedure TemplateName(): Code[10]
    begin
        exit(CopyStr(TemplateNameTok, 1, 10));
    end;

    procedure BatchName(): Code[10]
    begin
        exit(CopyStr(BatchNameTok, 1, 10));
    end;

    // ------------------------------------------------------------------ chuan bi truoc khi import
    procedure PrepareForImport()
    var
        FromDate: Date;
        ToDate: Date;
    begin
        EnsureTemplateAndBatch();
        DataDateRange(FromDate, ToDate);
        WidenPostingDates(FromDate, ToDate);
        Message(PreparedMsg, TemplateName(), BatchName(), FromDate, ToDate);
    end;

    /// Ban khong hop thoai cho web service NWVDemoRepost.
    procedure PrepareNoDialog(): Text
    var
        FromDate: Date;
        ToDate: Date;
    begin
        EnsureTemplateAndBatch();
        DataDateRange(FromDate, ToDate);
        WidenPostingDates(FromDate, ToDate);
        exit(StrSubstNo(PreparedMsg, TemplateName(), BatchName(), FromDate, ToDate));
    end;

    local procedure EnsureTemplateAndBatch()
    var
        ItemJnlTemplate: Record "Item Journal Template";
        ItemJnlBatch: Record "Item Journal Batch";
    begin
        if not ItemJnlTemplate.Get(TemplateName()) then begin
            ItemJnlTemplate.Init();
            ItemJnlTemplate.Validate(Name, TemplateName());
            ItemJnlTemplate.Validate(Description, TemplateDescTxt);
            ItemJnlTemplate.Validate(Type, ItemJnlTemplate.Type::Item);
            ItemJnlTemplate.Insert(true);
        end;

        if not ItemJnlBatch.Get(TemplateName(), BatchName()) then begin
            ItemJnlBatch.Init();
            ItemJnlBatch.Validate("Journal Template Name", TemplateName());
            ItemJnlBatch.Validate(Name, BatchName());
            ItemJnlBatch.Validate(Description, BatchDescTxt);
            ItemJnlBatch.Insert(true);
        end;
        // Bat buoc. Lot No. va Expiration Date nam ngay tren dong journal (Config Package do vao
        // field 6501 va 6506). Item Journal Line.CheckItemTracking() xoa sach hai truong do neu
        // batch khong bat "Item Tracking on Lines". Lan import dau tien vao company NWV ngay
        // 12/09/2026 da mat toan bo Lot No. vi thieu co nay.
        if not ItemJnlBatch."Item Tracking on Lines" then begin
            ItemJnlBatch.Validate("Item Tracking on Lines", true);
            ItemJnlBatch.Modify(true);
        end;
    end;

    /// <summary>
    /// Khoang ngay cua du lieu. Neu batch da co dong thi lay tu chinh no, chua co thi lay
    /// khoang mac dinh cua bo du lieu demo.
    /// </summary>
    procedure DataDateRange(var FromDate: Date; var ToDate: Date)
    var
        ItemJnlLine: Record "Item Journal Line";
    begin
        Evaluate(FromDate, DefaultFromDate, 9);
        Evaluate(ToDate, DefaultToDate, 9);

        FilterBatch(ItemJnlLine);
        if ItemJnlLine.FindFirst() then begin
            if ItemJnlLine."Posting Date" < FromDate then
                FromDate := ItemJnlLine."Posting Date";
            if ItemJnlLine.FindLast() and (ItemJnlLine."Posting Date" > ToDate) then
                ToDate := ItemJnlLine."Posting Date";
        end;
        FromDate := CalcDate('<-CM>', FromDate);
        ToDate := CalcDate('<CM>', ToDate);
    end;

    /// <summary>
    /// Chi noi rong, khong bao gio thu hep. Cham vao General Ledger Setup va User Setup cua
    /// nguoi dang dang nhap, khong cham user khac.
    /// </summary>
    local procedure WidenPostingDates(FromDate: Date; ToDate: Date)
    var
        GLSetup: Record "General Ledger Setup";
        UserSetup: Record "User Setup";
    begin
        GLSetup.Get();
        if (GLSetup."Allow Posting From" <> 0D) and (GLSetup."Allow Posting From" > FromDate) then
            GLSetup."Allow Posting From" := FromDate;
        if (GLSetup."Allow Posting To" <> 0D) and (GLSetup."Allow Posting To" < ToDate) then
            GLSetup."Allow Posting To" := ToDate;
        GLSetup.Modify();

        if UserSetup.Get(UserId()) then begin
            if (UserSetup."Allow Posting From" <> 0D) and (UserSetup."Allow Posting From" > FromDate) then
                UserSetup."Allow Posting From" := FromDate;
            if (UserSetup."Allow Posting To" <> 0D) and (UserSetup."Allow Posting To" < ToDate) then
                UserSetup."Allow Posting To" := ToDate;
            UserSetup.Modify();
        end;
    end;

    // ------------------------------------------------------------------ post theo tung thang
    procedure PostAllByMonth()
    var
        Slices: Integer;
    begin
        Slices := PostAllByMonthNoDialog();
        Message(PostedMsg, Slices, UnpostedLineCount());
    end;

    procedure PostAllByMonthNoDialog() Slices: Integer
    var
        ItemJnlLine: Record "Item Journal Line";
        FromDate: Date;
        ToDate: Date;
        LastDate: Date;
        Remaining: Integer;
        Progress: Dialog;
    begin
        FilterBatch(ItemJnlLine);
        if not ItemJnlLine.FindFirst() then
            Error(NoLinesErr, BatchName());
        FromDate := CalcDate('<-CM>', ItemJnlLine."Posting Date");
        ItemJnlLine.FindLast();
        LastDate := ItemJnlLine."Posting Date";

        if GuiAllowed() then
            Progress.Open(ProgressTxt);

        while FromDate <= LastDate do begin
            ToDate := CalcDate('<CM>', FromDate);
            if GuiAllowed() then
                Progress.Update(1, Format(FromDate) + ' .. ' + Format(ToDate));
            Remaining := UnpostedLineCount();
            if PostSlice(FromDate, ToDate) then begin
                Slices += 1;
                if UnpostedLineCount() >= Remaining then
                    Error(StuckErr, FromDate, ToDate);
            end;
            FromDate := CalcDate('<1M>', FromDate);
        end;

        if GuiAllowed() then
            Progress.Close();
    end;

    procedure PostRangeNoDialog(FromDate: Date; ToDate: Date): Boolean
    begin
        exit(PostSlice(FromDate, ToDate));
    end;

    /// Post tung chung tu (Posting Date + Document No.) theo thu tu dong dau tien cua no trong batch.
    ///
    /// Vi sao (doc trong ItemJnlPostBatch.PostLines, Base App 28.4): khi Inventory Setup khong bat legacy
    /// posting, batch post theo khoa "Document No., Item No., Location Code", KHONG theo Line No. Post ca
    /// nua thang mot lan thi SL260322 (ban) chay truoc TR260322 (hang ve cua hang) va lo chua kip ve:
    /// "Lot No. ... cannot be fully applied". Bat gap ngay 13/09/2026 khi post lai co item tracking.
    local procedure PostSlice(FromDate: Date; ToDate: Date): Boolean
    var
        ItemJnlLine: Record "Item Journal Line";
        DocLine: Record "Item Journal Line";
        ItemJnlPostBatch: Codeunit "Item Jnl.-Post Batch";
        Seen: Dictionary of [Text, Boolean];
        DocKeys: List of [Text];
        DocKey: Text;
        Parts: List of [Text];
        PostDate: Date;
    begin
        FilterBatch(ItemJnlLine);
        ItemJnlLine.SetRange("Posting Date", FromDate, ToDate);
        ItemJnlLine.SetLoadFields("Posting Date", "Document No.");
        if not ItemJnlLine.FindSet() then
            exit(false);
        repeat
            DocKey := Format(ItemJnlLine."Posting Date", 0, 9) + '|' + ItemJnlLine."Document No.";
            if not Seen.ContainsKey(DocKey) then begin
                Seen.Add(DocKey, true);
                DocKeys.Add(DocKey);
            end;
        until ItemJnlLine.Next() = 0;

        foreach DocKey in DocKeys do begin
            Parts := DocKey.Split('|');
            Evaluate(PostDate, Parts.Get(1), 9);
            FilterBatch(DocLine);
            DocLine.SetRange("Posting Date", PostDate);
            DocLine.SetRange("Document No.", Parts.Get(2));
            if DocLine.FindFirst() then begin
                Clear(ItemJnlPostBatch);
                ItemJnlPostBatch.Run(DocLine);
            end;
        end;
        exit(true);
    end;

    // ------------------------------------------------------------------ chot du lieu sau khi post
    /// <summary>
    /// Khoa lo dung cho kich ban thu hoi. Chi chay duoc sau khi post, vi Lot No. Information
    /// do chinh viec post sinh ra khi Item Tracking Code bat co Create Lot No. Info. on posting.
    /// </summary>
    procedure BlockDemoLot()
    var
        LotNoInfo: Record "Lot No. Information";
    begin
        if not LotNoInfo.Get(BlockedItemTok, '', BlockedLotTok) then
            Error(NoLotErr, BlockedItemTok, BlockedLotTok);
        LotNoInfo.Validate(Blocked, true);
        LotNoInfo.Modify(true);
        Message(LotBlockedMsg, BlockedLotTok, BlockedItemTok);
    end;

    procedure BlockDemoLotNoDialog(): Text
    var
        LotNoInfo: Record "Lot No. Information";
    begin
        if not LotNoInfo.Get(BlockedItemTok, '', BlockedLotTok) then
            Error(NoLotErr, BlockedItemTok, BlockedLotTok);
        LotNoInfo.Validate(Blocked, true);
        LotNoInfo.Modify(true);
        exit(StrSubstNo(LotBlockedMsg, BlockedLotTok, BlockedItemTok));
    end;

    procedure BlockedLotExists(): Boolean
    var
        LotNoInfo: Record "Lot No. Information";
    begin
        exit(LotNoInfo.Get(BlockedItemTok, '', BlockedLotTok));
    end;

    procedure BlockedLotIsBlocked(): Boolean
    var
        LotNoInfo: Record "Lot No. Information";
    begin
        if not LotNoInfo.Get(BlockedItemTok, '', BlockedLotTok) then
            exit(false);
        exit(LotNoInfo.Blocked);
    end;

    // ------------------------------------------------------------------ don dep khi import hong
    procedure DeleteBatchLines()
    var
        ItemJnlLine: Record "Item Journal Line";
        Removed: Integer;
    begin
        if not Confirm(DeleteQst, false, BatchName()) then
            exit;
        FilterBatch(ItemJnlLine);
        Removed := ItemJnlLine.Count();
        ItemJnlLine.DeleteAll(true);
        Message(DeletedMsg, Removed);
    end;

    // ------------------------------------------------------------------ so lieu cho trang
    procedure UnpostedLineCount(): Integer
    var
        ItemJnlLine: Record "Item Journal Line";
    begin
        FilterBatch(ItemJnlLine);
        exit(ItemJnlLine.Count());
    end;

    procedure ItemLedgerEntryCount(): Integer
    var
        ItemLedgEntry: Record "Item Ledger Entry";
    begin
        exit(ItemLedgEntry.Count());
    end;

    procedure LotInfoCount(): Integer
    var
        LotNoInfo: Record "Lot No. Information";
    begin
        exit(LotNoInfo.Count());
    end;

    procedure BatchExists(): Boolean
    var
        ItemJnlBatch: Record "Item Journal Batch";
    begin
        exit(ItemJnlBatch.Get(TemplateName(), BatchName()));
    end;

    /// <summary>
    /// Loc dong that cua batch. Bo qua dong trong ma BC tu chen sau moi lan post.
    /// </summary>
    local procedure FilterBatch(var ItemJnlLine: Record "Item Journal Line")
    begin
        ItemJnlLine.Reset();
        ItemJnlLine.SetRange("Journal Template Name", TemplateName());
        ItemJnlLine.SetRange("Journal Batch Name", BatchName());
        ItemJnlLine.SetFilter("Item No.", '<>%1', '');
    end;
}
