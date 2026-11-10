"""Cau hinh backend trung gian QTQG.

Moi tham so van hanh doc tu bien moi truong, khong viet cung o bat ky dau.
Day la cho duy nhat doc os.environ, cac mo-dun khac chi dung CAU_HINH.

Thong tin dang nhap CSDL chi nam trong backend/.env (da gitignore) hoac trong
bien moi truong cua may chu. Khong ghi vao ma nguon, test hay README.
"""

import os
import sys

GOC_BACKEND = os.path.dirname(os.path.abspath(__file__))
GOC_DU_AN = os.path.dirname(GOC_BACKEND)


def _nap_env():
    """Doc backend/.env neu co. Thieu python-dotenv thi bo qua, van chay duoc
    bang bien moi truong cua he thong."""
    duong_dan = os.path.join(GOC_BACKEND, ".env")
    if not os.path.isfile(duong_dan):
        return
    try:
        from dotenv import load_dotenv
    except ImportError:
        print("Canh bao: chua co python-dotenv, bo qua backend/.env.",
              file=sys.stderr)
        return
    load_dotenv(duong_dan)


_nap_env()


def _chu(ten, mac_dinh=""):
    return (os.environ.get(ten) or mac_dinh).strip()


def _so(ten, mac_dinh):
    gia_tri = _chu(ten)
    if not gia_tri:
        return mac_dinh
    try:
        return int(gia_tri)
    except ValueError:
        print("Canh bao: bien {} khong phai so, dung mac dinh {}.".format(
            ten, mac_dinh), file=sys.stderr)
        return mac_dinh


CHE_DO = _chu("CHE_DO", "thu_nghiem")

QTQG_MAY_CHU = _chu("QTQG_MAY_CHU")
QTQG_CONG = _so("QTQG_CONG", 5432)
QTQG_CSDL = _chu("QTQG_CSDL")
QTQG_TAI_KHOAN = _chu("QTQG_TAI_KHOAN")
QTQG_MAT_KHAU = _chu("QTQG_MAT_KHAU")

# --------------------------------------------------------------------------
# Cong, doc tu tinh.json
# --------------------------------------------------------------------------
# Moi tinh mot cap cong rieng khi chay thu tren may ca nhan: Khanh Hoa
# 8000/8001, Gia Lai 8010/8011. Khac cong la khac origin, nen cache cua trinh
# duyet khong lan giua hai du an. Xem ghi_chu_cong trong tinh.json.
#
# Doc o day chu khong ghi cung, va cung khong doc qua khong_gian.py: mo-dun do
# import cau_hinh nen goi nguoc lai la vong tron.
GOC_DU_AN_TAM = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def _cong_tu_tinh_json():
    """Tra ve (cong_web, cong_backend). Thieu tinh.json thi dung mac dinh."""
    duong_dan = os.path.join(GOC_DU_AN_TAM, "tinh.json")
    try:
        import json
        with open(duong_dan, encoding="utf-8") as f:
            cong = (json.load(f).get("cong") or {})
        return int(cong.get("web", 8000)), int(cong.get("backend", 8001))
    except Exception as e:
        print("Canh bao: khong doc duoc cong tu tinh.json ({}), dung 8000/8001."
              .format(e), file=sys.stderr)
        return 8000, 8001


_CONG_WEB, _CONG_BACKEND = _cong_tu_tinh_json()

# Cong dich vu. Bien moi truong CONG ghi de duoc, de con chay hai ban song song
# khi can.
CONG = _so("CONG", _CONG_BACKEND)

# Mac dinh chi mo cho cong web cua chinh tinh nay, khong mo bua cho 8000.
CORS_NGUON = [x.strip() for x in _chu(
    "CORS_NGUON",
    "http://localhost:{0},http://127.0.0.1:{0}".format(_CONG_WEB)).split(",")
    if x.strip()]

CACHE_GIAY = _so("CACHE_GIAY", 60)

# Uoc nhiet do nuoc tu trung binh nhieu nam cua chinh tram khi ky do thieu so
# do nhiet do. Can cho viec quy DO ra phan tram bao hoa; thieu no thi nhom IV
# thuong tut xuong duoi ba thong so va WQI khong du dieu kien cong bo.
#
# LUU Y: day la so SUY DIEN, khong phai so do, nen trai voi yeu cau ve du lieu
# dau vao o muc 2.1.a cua Quyet dinh 1460. Bat theo quyet dinh cua nguoi dung,
# doi lai moi ban ghi dung no deu mang co nhiet_do_uoc_tinh va giao dien noi ro.
# Dat UOC_NHIET_DO=0 de tat.
UOC_NHIET_DO = _chu("UOC_NHIET_DO", "1") not in ("0", "khong", "false", "")

# Hop danh sach tram dia phuong (data/quan_trac.geojson) vao danh sach tram
# QTQG o che do that.
#
# Gia Lai bat cai nay, vi lop quan trac dia phuong cua Gia Lai la du lieu THAT
# va QTQG chi co mot tram co so do trong tinh. Khanh Hoa TAT, vi lop
# data/quan_trac.geojson hien con la du lieu mo phong: tron vi tri bia vao
# cung so do thuc cua QTQG tren mot ban do la gay hieu nham.
#
# Khi nao tinh co lop quan trac dia phuong that thi dat HOP_TRAM_DIA_PHUONG=1.
#
# Bien nay KHONG anh huong che do thu_nghiem: che do do khong noi CSDL nen
# nguon vi tri duy nhat la lop dia phuong, va giao dien da gan nhan ro rang.
HOP_TRAM_DIA_PHUONG = _chu("HOP_TRAM_DIA_PHUONG", "0") not in (
    "0", "khong", "false", "")

# An ban ghi so do cu hon bao nhieu NGAY. Mac dinh 730 ngay, tuc 2 nam.
#
# Vi sao can: CSDL QTQG giu ca nhung tram lau khong do. Trong pham vi tinh nay,
# tram nuoc mat NP01 co so do moi nhat tu 31/12/2017, trong khi cac lo khoan do
# hang ngay. Hai moc cach nhau gan 9 nam ma nam chung mot ban do va mot bang:
# nguoi xem quet nhanh chi thay huy hieu xanh va chi so WQI, khong thay cot
# "Thoi diem do". Day dung la tinh huong da tranh o nhanh nuoc duoi dat bang
# cach chi lay lo khoan hientrang = 'Dang hoat dong'.
#
# Loc o day la BAN GHI SO DO, khong phai cong trinh. Tram van hien tren ban do
# va trong bang, chi la khong co so do nao di kem, giong nhu 5 tram thuy van
# von khong co so do. Khong xoa mot cong trinh that khoi danh muc kiem ke.
#
# Dat 0 de tat hoan toan.
SO_DO_CU_TOI_DA_NGAY = _so("SO_DO_CU_TOI_DA_NGAY", 730)

DUONG_DAN_SQLITE = os.path.join(
    GOC_BACKEND, _chu("DUONG_DAN_SQLITE", "chuoi_quan_trac.sqlite3"))

# Thu muc du lieu cua trang web, dung o che do thu_nghiem va de doc tinh.json
THU_MUC_DU_LIEU = os.path.join(GOC_DU_AN, "data")
TEP_THAM_SO_TINH = os.path.join(GOC_DU_AN, "tinh.json")

TEP_ANH_XA_TRAM = os.path.join(GOC_BACKEND, "anh_xa_tram.csv")

# Nhung bien bat buoc phai co khi chay voi nguon that
BIEN_BAT_BUOC = ["QTQG_MAY_CHU", "QTQG_CSDL", "QTQG_TAI_KHOAN", "QTQG_MAT_KHAU"]


def canh_bao_cors():
    """Cau canh bao neu CORS_NGUON duoc ghi de ma thieu cong web cua tinh.

    Bay im lang: CORS_NGUON trong backend/.env ghi de gia tri tu suy. Neu tep
    .env duoc sao tu du an tinh khac thi no con mang cong cua tinh do, va moi
    lan goi API deu bi chan voi thong bao "Failed to fetch" khong noi ly do.
    Doi cong.web trong tinh.json cung khong co tac dung gi.

    Tra ve None khi khong co van de.
    """
    if not os.environ.get("CORS_NGUON"):
        return None            # de trong thi dang tu suy, khong the lech

    can_co = "http://localhost:{}".format(_CONG_WEB)
    if any(can_co in nguon for nguon in CORS_NGUON):
        return None

    return ("CANH BAO: CORS_NGUON trong backend/.env dang la {} nhung cong web "
            "cua tinh nay la {} (cong.web trong tinh.json). Trang se bi chan "
            "khi goi API. Xoa trong gia tri CORS_NGUON trong .env de nó tu suy."
            .format(", ".join(CORS_NGUON), _CONG_WEB))


def la_nguon_that():
    return CHE_DO == "that"


def thieu_thong_tin_ket_noi():
    """Danh sach bien ket noi con thieu, khong phu thuoc CHE_DO.

    Script kham pha schema can goi truc tiep CSDL du CHE_DO dang la thu_nghiem,
    nen phep kiem tra nay phai tach khoi kiem_tra_cau_hinh().
    """
    return [ten for ten in BIEN_BAT_BUOC if not globals().get(ten)]


def kiem_tra_cau_hinh():
    """Tra ve danh sach bien con thieu. Rong nghia la du dieu kien chay.

    Goi luc khoi dong dich vu: thieu thong tin ket noi thi phai bao ngay, khong
    de den luc co nguoi mo trang moi phat hien.
    """
    if not la_nguon_that():
        return []
    return thieu_thong_tin_ket_noi()


def mo_ta_nguon():
    """Chuoi nguon du lieu hien ra giao dien. Khong chua tai khoan, mat khau
    hay dia chi may chu, vi chuoi nay di ra trinh duyet."""
    if la_nguon_that():
        return ("Số liệu quan trắc lấy từ cơ sở dữ liệu phần mềm "
                "Quan trắc Quốc gia (QTQG)")
    return ("Dữ liệu thử nghiệm sinh từ vị trí trạm thật, dùng để kiểm thử "
            "giao diện khi chưa kết nối được cơ sở dữ liệu QTQG")
