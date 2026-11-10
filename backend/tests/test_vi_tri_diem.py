"""Kiem thu vi tri cac lop diem trong data/.

Day la bo kiem thu cua backend, nhung cac test duoi day soi du lieu do
scripts/ sinh ra. Dat o day vi ca du an chi co mot goc pytest; chay bang
    python -m pytest backend/tests

Vi sao can: mot diem dat sai cho KHONG lam hong gi ca. Trang web van chay,
bang van day du, khong co thong bao loi nao. Day la loi tung xay ra that o du
an cung bo ma nay: ca mot lop ho chua bi day sang tay 27 km trong nhieu thang
ma khong ai thay, cho den khi nguoi dung nhin ban do va noi "ho chua bi lech".

Nguyen nhan la doan sai kinh tuyen truc. Giua 108 do 15 phut va 108 do 30 phut
cach nhau 0,25 do kinh, khoang 27 km. Tinh nao cung rong hon han con so do theo
chieu dong tay, nen diem sai VAN nam trong tinh, tuc moi phep kiem chi xet ranh
gioi tinh deu bao "dat". Bay nay dung voi Khanh Hoa: cac tep MapInfo o
CSDL/SD_TLTT_DTHT_XA_THAI khai datum la WGS_1984 chu khong phai VN-2000, va
EPSG dung la 9217 (TM-3 108-15), xem ghi_chu_epsg trong tinh.json.

HIEN TRANG O DU AN NAY: cac lop chuyen de con la du lieu mo phong, chua di qua
buoc chuyen he quy chieu nao, nen moi test duoi day deu SKIP. Chung dat san o
day lam cho chan cho luc nap bo kiem ke that; khi do dien HO_MOC va chay lai.

Ba nhom test duoi day chot lai:
  - Ty le diem chi kiem duoc o muc "nam trong tinh" phai rat nho.
  - Vi tri phai khop ranh gioi xa that, khong co do lech he thong.
  - Vai ho chua lon phai dung vi tri dia ly da biet.
"""

import json
import math
import os
import statistics

import pytest

import cau_hinh

shapely = pytest.importorskip("shapely", reason="can shapely de kiem hinh hoc")
from shapely.geometry import shape, Point     # noqa: E402

THU_MUC_DATA = os.path.join(cau_hinh.GOC_DU_AN, "data")

# Muc kiem chung yeu nhat ma diem_tu_toa_do() gan cho mot diem: chi biet no
# nam trong tinh, khong doi chieu duoc voi xa nao. Diem o muc nay co the lech
# mot mui chieu ma khong ai phat hien.
MUC_YEU_NHAT = "Chỉ kiểm được là nằm trong tỉnh"


def _doc(ten_tep):
    duong_dan = os.path.join(THU_MUC_DATA, ten_tep)
    if not os.path.isfile(duong_dan):
        pytest.skip("Chưa có {}".format(ten_tep))
    with open(duong_dan, encoding="utf-8") as f:
        return json.load(f)


def _bo_dau(chu):
    import unicodedata
    chu = unicodedata.normalize("NFD", str(chu or ""))
    chu = "".join(c for c in chu if unicodedata.category(c) != "Mn")
    return chu.replace("đ", "d").replace("Đ", "D").lower().strip()


# ---------------------------------------------------------------------------
# Muc kiem chung vi tri
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("ten_tep,toi_da", [
    # Ty le toi da duoc phep o muc yeu nhat. Con so lay tu ket qua that sau
    # khi sua, nong len mot chut de thay doi nho o nguon khong lam do test:
    #   ho_chua    3 / 400 diem cua bieu 3.2
    #   xa_thai   15 / 155
    #   khai_thac 105 / 654
    ("ho_chua.geojson", 0.05),
    ("xa_thai.geojson", 0.20),
    ("khai_thac.geojson", 0.25),
])
def test_it_diem_chi_kiem_duoc_la_nam_trong_tinh(ten_tep, toi_da):
    """Phan lon diem phai doi chieu duoc voi xa hoac voi cap toa do khac.

    Diem chi dat muc yeu nhat la diem khong ai kiem chung duoc mui chieu, va
    doan sai mui chieu o day khong lo ra vi diem van nam trong tinh.
    """
    tap = _doc(ten_tep)
    cac_muc = [f["properties"].get("kiem_chung") for f in tap["features"]]
    # Diem cua nguon khac bieu dieu tra khong di qua diem_tu_toa_do()
    xet = [m for m in cac_muc
           if m in (MUC_YEU_NHAT, "Khớp đúng xã ghi trong biểu",
                    "Các cặp tọa độ khớp nhau và đúng xã ghi trong biểu",
                    "Các cặp tọa độ khớp nhau, khác xã ghi trong biểu")]
    if not xet:
        pytest.skip("{} chưa có trường kiểm chứng".format(ten_tep))

    yeu = sum(1 for m in xet if m == MUC_YEU_NHAT)
    ty_le = yeu / len(xet)
    assert ty_le <= toi_da, (
        "{}: {} / {} điểm ({:.0%}) chỉ kiểm được là nằm trong tỉnh. "
        "Ngưỡng cho phép {:.0%}. Xem lại khai báo EPSG của từng cặp tọa độ "
        "trong scripts/05_chuan_hoa_chuyen_de.py."
        .format(ten_tep, yeu, len(xet), ty_le, toi_da))


# ---------------------------------------------------------------------------
# Khong co do lech he thong so voi ranh gioi xa
# ---------------------------------------------------------------------------

def _do_lech_so_voi_xa(ten_tep):
    """Do lech trung vi giua diem va tam cai xa ma ban ghi khai bao."""
    xa = _doc("ranh_gioi_xa.geojson")
    theo_khoa = {}
    for f in xa["features"]:
        k = _bo_dau(f["properties"].get("ten"))
        for tien_to in ("xa ", "phuong ", "thi tran ", "dac khu "):
            if k.startswith(tien_to):
                k = k[len(tien_to):]
                break
        theo_khoa[k.replace(" ", "")] = shape(f["geometry"])

    tap = _doc(ten_tep)
    dx, dy = [], []
    for f in tap["features"]:
        # Moi lop dat ten truong vi tri mot khac: ho_chua giu nguyen cum
        # "vi_tri_hc" cua bieu, con khai_thac va xa_thai da tach rieng cot xa.
        tt = f["properties"]
        vi_tri = tt.get("vi_tri_hc") or tt.get("xa")
        if not vi_tri or f["geometry"]["type"] != "Point":
            continue
        for cum in str(vi_tri).split(","):
            k = _bo_dau(cum).replace("'", "").replace("-", "")
            for tien_to in ("xa ", "phuong ", "thi tran ", "dac khu ", "tt "):
                if k.startswith(tien_to):
                    k = k[len(tien_to):]
                    break
            g = theo_khoa.get(k.replace(" ", ""))
            if g is None:
                continue
            x, y = f["geometry"]["coordinates"]
            tam = g.centroid
            dx.append(tam.x - x)
            dy.append(tam.y - y)
            break
    return dx, dy


# 0,25 do kinh la khoang cach giua hai kinh tuyen truc 108 do 15 phut va
# 108 do 30 phut. Do lech trung vi phai nho hon han con so do; dat nguong o
# mot phan ba de bat duoc ca truong hop chi mot nua so diem bi day lech.
NGUONG_LECH_DO = 0.08


@pytest.mark.parametrize("ten_tep", ["ho_chua.geojson", "khai_thac.geojson",
                                     "xa_thai.geojson"])
def test_khong_co_do_lech_he_thong_so_voi_ranh_gioi_xa(ten_tep):
    """Diem phai nam quanh cai xa ma ban ghi khai bao, khong lech ve mot phia.

    Dung trung vi chu khong dung trung binh: tam xa chi la xap xi vi tri that
    nen tung diem le lech vai km la binh thuong, nhung neu CA DAM diem cung
    lech ve mot huong thi do la sai mui chieu.
    """
    dx, dy = _do_lech_so_voi_xa(ten_tep)
    if len(dx) < 30:
        pytest.skip("{}: quá ít bản ghi đối chiếu được tên xã".format(ten_tep))

    lech_x = statistics.median(dx)
    lech_y = statistics.median(dy)
    assert abs(lech_x) < NGUONG_LECH_DO, (
        "{}: lệch hệ thống {:+.4f} độ kinh so với xã khai báo ({:.1f} km). "
        "0,25 độ là khoảng cách giữa hai kinh tuyến trục 108°15′ và 108°30′."
        .format(ten_tep, lech_x, abs(lech_x) * 108))
    assert abs(lech_y) < NGUONG_LECH_DO, (
        "{}: lệch hệ thống {:+.4f} độ vĩ so với xã khai báo ({:.1f} km)."
        .format(ten_tep, lech_y, abs(lech_y) * 110.6))


# ---------------------------------------------------------------------------
# Vai ho chua lon, doi chieu bang tay
# ---------------------------------------------------------------------------

# (ten ho, kinh do, vi do) theo vi tri dia ly da biet cua tung ho, KHONG lay
# tu dau ra cua chinh pipeline nay. Do la diem mau chot: mot moc lay tu ket
# qua cua chinh minh thi khong kiem duoc gi ca.
#
# Dung sai 8 km. Rong, vi ho chua la mot vung lon va bieu co the ghi toa do
# dap, toa do long ho hay toa do tram quan ly. Nhung van hep hon han 27 km,
# tuc khoang cach ma mot sai mui chieu day diem di, nen test nay bat duoc dung
# cai loi can bat.
#
# DANH SACH DE RONG CO Y. Lop ho_chua cua du an nay con la du lieu mo phong,
# toa do do scripts/00_tao_du_lieu_mau.py sinh ra chu khong phai vi tri that;
# dien moc that vao day bay gio thi test do ma khong noi len dieu gi dung.
# Khi nap bo kiem ke that thi dien vao, vi du:
#     ("Hồ Đá Bàn", 109.19, 12.63),
HO_MOC = []

DUNG_SAI_KM = 8.0


@pytest.mark.parametrize("ten_ho,kinh_do,vi_do", HO_MOC)
def test_ho_chua_lon_dung_vi_tri_dia_ly(ten_ho, kinh_do, vi_do):
    tap = _doc("ho_chua.geojson")
    khop = [f for f in tap["features"]
            if _bo_dau(f["properties"].get("ten")) == _bo_dau(ten_ho)]
    if not khop:
        pytest.skip("Không có hồ {} trong lớp".format(ten_ho))

    x, y = khop[0]["geometry"]["coordinates"]
    cach = math.hypot((x - kinh_do) * 111.32 * math.cos(math.radians(vi_do)),
                      (y - vi_do) * 110.57)
    assert cach <= DUNG_SAI_KM, (
        "{} đang ở ({:.4f}, {:.4f}), cách vị trí đã biết ({:.3f}, {:.3f}) "
        "{:.1f} km. Lệch khoảng 27 km là dấu hiệu đọc sai kinh tuyến trục."
        .format(ten_ho, x, y, kinh_do, vi_do, cach))
