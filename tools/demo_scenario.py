"""Kich ban du lieu demo Marou tren company NWV, environment NWV01.

Dung dung mat hang co san cua company, khong tao ma moi. Lam duoc vi company NWV chua co
mot dong Item Ledger Entry nao, nen `TestNoEntriesExist` trong Item.Table.al khong chan
viec gan Item Tracking Code. Da kiem tren giao dien: page 38 rong, page 6501 rong.

Master data lay nguyen cua company: 24 mat hang co san, 6 dia diem co san, Item Tracking Code
LOTALLEXP co san (Lot Specific Tracking bat, Man. Expir. Date Entry Reqd. bat, Strict Expiration
Posting tat), nhom hang DESSERTS / ICECREAM / FROZEN / BEVERAGES / DAIRY co san,
Gen. Prod. Posting Group RETAIL, Inventory Posting Group RESALE.

Chi sua tren item nhung gi bat buoc phai co cho UC2: Item Tracking Code, Expiration Calculation,
va Unit Cost cho nhung mat hang dang de 0 (khong co gia von thi khong tinh duoc gia tri ton kho
lan bien loi nhuan).
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import date, timedelta

TODAY = date(2026, 9, 18)   # neo sat ngay demo, khoi phai chinh Work Date
HISTORY_DAYS = 180
START = TODAY - timedelta(days=HISTORY_DAYS)

WH = "W0003"                       # Warehouse W0003 - CENTRAL
STORES = ["S0001", "S0002", "S0005", "S0010", "S0013"]
STORE_NAME = {
    "S0001": "Cronus Super Market South",
    "S0002": "Cronus Super Market North",
    "S0005": "Cronus Restaurant",
    "S0010": "Cronus Coffeehouse",
    "S0013": "Cronus Web Store",
}
STORE_FACTOR = {"S0001": 1.30, "S0002": 1.00, "S0005": 0.55, "S0010": 0.85, "S0013": 0.45}

TRACKING_CODE = "LOTALLEXP"
LOT_NOS_SERIES = "R-LOT"
BATCH = "NWVDEMO"

# Cac ma duoc gan Item Tracking Code, tuc duoc ghi Lot No. va Expiration Date len dong
# Item Journal. Cac ma con lai khong co tracking code nen hai cot do PHAI de trong, dien vao
# thi `ItemJnlLineReserve.CreateItemTracking` thoat ngay va lot bi bo qua khong bao loi.
#
# Chon theo nghiep vu chu khong theo do dai han dung: banh tuoi va kem la thu Maison Marou lam
# va ban, quan theo lo thi hop ly. Ban truoc co Milk 1 liter va Cream 250 ml chi vi chung han
# ngan, nhung khong ai quan ly lo cho sua hop, Dung da bac ngay 12/09/2026.
TRACKED = {
    # kem, han dung dai, cho kich ban truy xuat nguon goc va dieu chuyen
    "33310",   # Choco pillar        240 ngay
    "33323",   # Choco nuts          240 ngay
    "33341",   # Choco bowl          180 ngay
    # banh tuoi, han dung ngan, cho kich ban han dung
    "33110",   # Croissant - chocolate  3 ngay
    "33100",   # Croissant - plain      3 ngay
    "33170",   # Chocolate cake         5 ngay
    "33116",   # Blueberry muffin       5 ngay
    "33130",   # Tiramisu               7 ngay
    "33160",   # Carrot cake            7 ngay
}


@dataclass(frozen=True)
class Item:
    no: str
    desc: str
    cat: str
    uom: str
    cost: float          # gia von dung cho du lieu; bang gia von hien co, tru khi dang de 0
    price: float
    shelf: int
    daily: float
    move_days: int = 7
    cost_was_zero: bool = False   # co phai minh dat gia von moi khong, de ghi ro trong README


# 24 mat hang co san cua company NWV. Uu tien mat hang chocolate, sau do la nhom trang mieng,
# kem va sua, de bo du lieu co du bien ve han dung, toc do ban va gia tri ton.
ITEMS: list[Item] = [
    # --- dich danh chocolate
    Item("33110", "Croissant - chocolate", "DESSERTS", "PCS", 1.20, 1.59, 3, 8.0, move_days=2),
    Item("33170", "Chocolate cake", "DESSERTS", "PCS", 5.50, 7.18, 5, 3.0, move_days=3),
    Item("33200", "Chocolate ice cream", "DESSERTS", "PCS", 4.20, 5.91, 270, 4.0),
    Item("33310", "Choco pillar", "ICECREAM", "PCS", 1.10, 3.00, 240, 9.0, cost_was_zero=True),
    Item("33323", "Choco nuts", "ICECREAM", "PCS", 1.10, 3.00, 240, 7.0, cost_was_zero=True),
    Item("33341", "Choco bowl", "ICECREAM", "PORTION", 2.10, 5.75, 180, 3.0, cost_was_zero=True),
    # --- banh va trang mieng, han dung ngan
    Item("33100", "Croissant - plain", "DESSERTS", "PCS", 1.00, 1.36, 3, 7.0, move_days=3),
    Item("33116", "Blueberry muffin", "DESSERTS", "PCS", 0.78, 1.09, 5, 4.0, move_days=3),
    Item("33120", "Pecan pie", "DESSERTS", "PCS", 6.50, 8.64, 10, 1.2, move_days=3),
    Item("33130", "Tiramisu", "DESSERTS", "PCS", 7.10, 9.55, 7, 1.5, move_days=3),
    Item("33160", "Carrot cake", "DESSERTS", "PCS", 5.50, 7.18, 7, 2.0, move_days=3),
    # --- kem, han dung dai
    Item("33150", "Ice cream", "DESSERTS", "BOX", 7.50, 11.36, 270, 1.0),
    Item("33250", "Vanilla ice cream", "DESSERTS", "PCS", 4.10, 5.36, 270, 3.5),
    Item("18200", "Ice cream blueberry", "FROZEN", "PCS", 0.95, 1.64, 270, 2.5, cost_was_zero=True),
    Item("18230", "Ice cream strawberry", "FROZEN", "PCS", 0.95, 1.64, 270, 1.8, cost_was_zero=True),
    Item("18120", "Frozen waffles", "FROZEN", "PCS", 1.00, 1.36, 180, 2.5, cost_was_zero=True),
    # --- do uong va sua, bo sung bien ve han dung va vong quay
    Item("30091", "Flavored syrup", "BEVERAGES", "BOTTLE", 2.80, 4.18, 300, 0.4, move_days=14),
    Item("10045", "Cream 250 ml", "DAIRY", "CARTON", 0.45, 0.86, 14, 5.0, move_days=4),
    Item("10070", "Yogurt strawberry", "DAIRY", "PCS", 0.50, 1.82, 21, 4.0, move_days=7),
    Item("10100", "Butter", "DAIRY", "BOX", 1.70, 2.80, 60, 2.0),
    Item("10000", "Milk 1 liter", "DAIRY", "BOTTLE", 0.90, 1.00, 7, 9.0, move_days=3),
]
BY_NO = {i.no: i for i in ITEMS}

# Assortment that: nha hang va quan ca phe khong ban hang dong goi cua sieu thi, web store
# khong ban hang tuoi. Nhieu to hop mat hang x cua hang vi vay khong co dong ban nao.
ASSORTMENT = {
    "DESSERTS":  ["S0001", "S0002", "S0005", "S0010"],
    "ICECREAM":  ["S0001", "S0002", "S0005", "S0010"],
    "FROZEN":    ["S0001", "S0002", "S0013"],
    "BEVERAGES": ["S0001", "S0002", "S0005", "S0010"],
    "DAIRY":     ["S0001", "S0002", "S0013"],
}

# ------------------------------------------------------------------ kich ban ghim san
LAUNCH = {"18120": START + timedelta(days=120)}       # hang moi, chi co 60 ngay lich su
DISCONTINUED = {"18230": date(2026, 6, 1)}            # ngung kinh doanh tu 01/06

EVENT = ("33200", "S0001", date(2026, 8, 8), date(2026, 8, 24), 2.4)

# Dut hang duoc mo phong bang cach NGUNG CHUYEN HANG, khong phai bang cach ep luong ban ve 0.
# Khac biet nay quan trong: ep ve 0 thi trong so lieu cua hang van con ton, nhin vao khong hieu
# vi sao khong ban duoc. Ngung chuyen thi ton tu rut ve 0 roi ban dung lai, dung nhu thuc te,
# va thuat toan phat hien cau bi cat cut moi co cai de bam vao.
NO_REPLEN = [
    ("33200", "S0001", date(2026, 8, 12), date(2026, 9, 2)),
    ("33200", "S0001", date(2026, 6, 8), date(2026, 6, 20)),
    ("33200", "S0001", date(2026, 7, 3), date(2026, 7, 16)),
]

PROMO = ("33310", ["S0001", "S0002"], date(2026, 7, 6), date(2026, 7, 19), 3.0, 0.25)

TREND = {"S0013": 0.9, "S0005": 0.0}

OVERSHIP = [
    ("33250", "S0002", 60, 14.0),   # Vanilla ice cream ton thua tai cua hang
    ("30091", WH,      95, 12.0),   # syrup ton thua tai kho
    ("18230", "S0013", 115, 7.0),   # kem dau ngung kinh doanh, con ton chet
    ("33120", "S0001", 40, 4.0),    # pecan pie ton cao nhung chua toi muc bao dong
]
UNDERSHIP = [("33323", "S0001", 21)]   # ngung chuyen Choco nuts ra S0001 trong 21 ngay cuoi

# Lo nhap ve da can date. Co that trong nganh lanh: nhan hang gan han de duoc gia tot, hoac
# lo bi rut ngan han sau su co kho lanh. Ghim o day de hai mat hang kem co tinh huong han dung
# ma khong phai bia han dung ngan cho ca dong hang.
SHORT_DATED = [
    # item, cua hang nhan, so ngay truoc TODAY, so ngay han dung con lai luc nhap,
    # he so nhan so luong so voi luong ban duoc trong quang thoi gian con lai
    ("33323", "S0002", 60, 55, 1.6),   # kem, den nay da qua han, con nam tren so
    ("33341", "S0005", 30, 60, 1.8),   # kem, con 30 ngay den han, days of cover vuot qua
    ("33310", "S0010", 20, 45, 1.7),   # kem, con 25 ngay den han, ban khong kip
    ("10045", "S0013",  9, 12, 2.4),   # cream, con 3 ngay den han, ban khong kip
    ("33130", "S0002",  5,  7, 2.6),   # tiramisu, con 2 ngay den han
    ("33170", "S0010",  6,  5, 2.2),   # chocolate cake, da qua han 1 ngay
    ("33110", "S0005",  4,  3, 2.0),   # croissant chocolate, da qua han 1 ngay
    ("10000", "S0001",  8,  7, 1.9),   # milk, da qua han 1 ngay
]

BLOCKED_LOT_ITEM = "33170"             # lo bi khoa, phuc vu demo thu hoi va truy xuat

# Han dung duoi 30 ngay thi coi la hang tuoi, co huy hang dinh ky
def is_fresh(it: Item) -> bool:
    return it.shelf <= 30


WASTE_ITEMS = {i.no for i in ITEMS if is_fresh(i)}
COUNT_ADJ_LOCATIONS = ["S0001", "S0002"]

WHOLESALE_CATEGORIES = {"FROZEN", "ICECREAM", "BEVERAGES"}
WHOLESALE_WEEKDAYS = {1, 3, 5}
WHOLESALE_MULT = 3.2


def stores_for(it: Item) -> list[str]:
    return ASSORTMENT[it.cat]


def is_active(it: Item, d: date) -> bool:
    if it.no in LAUNCH and d < LAUNCH[it.no]:
        return False
    if it.no in DISCONTINUED and d >= DISCONTINUED[it.no]:
        return False
    return True


def demand_lambda(it: Item, store: str, d: date) -> float:
    if not is_active(it, d):
        return 0.0
    lam = it.daily * STORE_FACTOR[store]

    wd = d.weekday()
    if wd >= 5:
        lam *= 1.35
    if is_fresh(it) and wd < 5:
        lam *= 1.15

    if store in TREND:
        lam *= 1.0 + TREND[store] * ((d - START).days / HISTORY_DAYS)

    if it.cat in ("ICECREAM", "FROZEN") and d.month in (6, 7, 8):
        lam *= 1.30                                    # kem ban manh mua he

    e_item, e_store, e_from, e_to, e_mult = EVENT
    if it.no == e_item and store == e_store and e_from <= d <= e_to:
        lam *= e_mult

    p_item, p_stores, p_from, p_to, p_mult, _ = PROMO
    if it.no == p_item and store in p_stores and p_from <= d <= p_to:
        lam *= p_mult

    return lam


def wholesale_lambda(it: Item, d: date) -> float:
    if it.cat not in WHOLESALE_CATEGORIES or d.weekday() not in WHOLESALE_WEEKDAYS:
        return 0.0
    if not is_active(it, d):
        return 0.0
    return sum(demand_lambda(it, s, d) for s in stores_for(it)) * WHOLESALE_MULT / 3


def unit_price(it: Item, store: str, d: date) -> float:
    p_item, p_stores, p_from, p_to, _, p_disc = PROMO
    if it.no == p_item and store in p_stores and p_from <= d <= p_to:
        return round(it.price * (1 - p_disc), 2)
    return it.price
