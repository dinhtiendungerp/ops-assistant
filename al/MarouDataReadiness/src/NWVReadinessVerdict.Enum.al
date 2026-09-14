/// <summary>
/// Ket luan cua mot dong kiem tra. Blocker nghia la neu khong sua thi use case lien quan
/// khong chay duoc, khong phai la loi cua he thong.
/// </summary>
enum 70050 "NWV Readiness Verdict"
{
    Extensible = false;

    value(0; Info) { Caption = 'Thông tin'; }
    value(1; OK) { Caption = 'Đạt'; }
    value(2; Warning) { Caption = 'Cần xem lại'; }
    value(3; Blocker) { Caption = 'Chặn'; }
}
