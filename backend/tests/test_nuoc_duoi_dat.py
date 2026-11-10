"""Kiem thu nhanh nuoc duoi dat: mang quan trac quoc gia.

Hai sai sot de xay ra nhat o nhanh nay, va day la noi khoa chung lai:

  1. Tinh VN_WQI cho nuoc duoi dat. Ban ghi lo khoan co pH, amoni, nitrat,
     coliform, du de ham tinh WQI chay tron tru va tra ve mot con so. Nhung
     Quyet dinh 1460/QD-TCMT la chi so chat luong nuoc MAT luc dia; nguong cac
     thong so nuoc duoi dat theo QCVN 09-MT:2015/BTNMT. Con so do se dung hinh
     thuc ma sai ve chuyen mon.

  2. Gop muc nuoc ngam vao truong h_m cua nuoc mat. Nuoc mat: cao do mat nuoc
     theo moc cua tram, so duong, nguon ghi bang centimet. Nuoc duoi dat: do
     sau mat nuoc duoi mieng lo khoan, so AM, nguon ghi bang met. Mot truong
     chung nghia la mot cot bang va mot bieu do tron hai dai luong nguoc nhau.

Khong test nao o day ket noi vao CSDL QTQG, xem conftest.py.
"""

import json
import os
import re

import pytest

import cau_hinh
import chuan_hoa
import khong_gian
import ket_noi
import nguon_qtqg


# Toa do mau suy tu khung_bao_nen trong tinh.json chu KHONG gan cung, de bo
# kiem thu nay con dung khi sao du an sang tinh khac.
_KB = khong_gian.khung_bao()
TAM_TINH = ((_KB[0] + _KB[2]) / 2.0, (_KB[1] + _KB[3]) / 2.0)


# Mot ky do day du cua lo khoan, dat ten cot DUNG NHU truy_van.sql tra ve
BAN_GHI_LO_KHOAN = {
    "ma": "QT1-BĐ",
    "ten": "Lỗ khoan QT1-BĐ",
    "thoi_diem": "2026-10-06 09:00",
    "thoi_diem_muc_nuoc": "2026-10-06 09:00",
    "thoi_diem_chat_luong": "2026-05-13",
    "tang_chua_nuoc": "qp",
    "h_ngam_m": -4.39,
    "cao_do_mn_m": 0.95,
    "nhiet_do_c": 27.5,
    "ph": 8.05,
    "tds_mg_l": 64.0,
    "do_cung_mg_l": 8.0,
    "permanganat_mg_l": 0.3,
    "amoni_mg_l": 0.017,
    "nitrat_mg_l": 0.714,
    "nitrit_mg_l": 0.002,
    "clorua_mg_l": 16.307,
    "fe_mg_l": 0.02,
    "mn_mg_l": 0.008,
    "as_mg_l": 0.0015,
    "coliform_mpn_100ml": 1.8,
}


# ---------------------------------------------------------------------------
# Khong tinh WQI cho nuoc duoi dat
# ---------------------------------------------------------------------------

def test_ban_ghi_lo_khoan_khong_co_wqi():
    bg = chuan_hoa.chuan_hoa_ban_ghi(
        BAN_GHI_LO_KHOAN, loai=chuan_hoa.LOAI_NUOC_DUOI_DAT)
    assert bg["loai"] == "nuoc_duoi_dat"
    assert "wqi" not in bg
    assert "phan_loai_wqi" not in bg


def test_khong_doi_hoi_them_thong_so_de_tinh_wqi():
    """Khong duoc bao "thieu thong so de tinh WQI" cho lo khoan.

    Do la loi thuoc bai toan nuoc mat. Hien no tren giao dien se khien nguoi
    dung di tim so lieu khong bao gio ton tai o mang quan trac nuoc duoi dat.
    """
    bg = chuan_hoa.chuan_hoa_ban_ghi(
        BAN_GHI_LO_KHOAN, loai=chuan_hoa.LOAI_NUOC_DUOI_DAT)
    assert "wqi_ly_do" not in bg
    assert "wqi_thieu_thong_so" not in bg
    assert "wqi_tu_tinh" not in bg


def test_khong_tu_dat_trang_thai_canh_bao_cho_lo_khoan():
    """Hai cot nguong hcp va h_chophep rong o moi lo khoan da kiem, nen khong
    co can cu nao de dat canh bao. Khong duoc tu nghi ra nguong."""
    bg = chuan_hoa.chuan_hoa_ban_ghi(
        BAN_GHI_LO_KHOAN, loai=chuan_hoa.LOAI_NUOC_DUOI_DAT)
    assert "trang_thai" not in bg


def test_ban_ghi_nuoc_mat_van_duoc_tinh_wqi():
    """Chan canh bao hoi quy: viec chan WQI phai chi ap cho nuoc duoi dat."""
    bg = chuan_hoa.chuan_hoa_ban_ghi({
        "ma": "NM-01", "thoi_diem": "2026-09-26",
        "ph": 7.4, "do_mg_l": 6.8, "nhiet_do_c": 27.0, "bod5_mg_l": 3.0,
        "cod_mg_l": 9.0, "amoni_mg_l": 0.12, "photphat_mg_l": 0.05,
        "tss_mg_l": 18.0, "do_duc_ntu": 12.0, "coliform_mpn_100ml": 2400,
    })
    assert bg["loai"] == "chat_luong_nuoc"
    assert bg["wqi"] is not None


# ---------------------------------------------------------------------------
# Doan loai khi nguoi goi khong noi ro
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("truong", ["h_ngam_m", "cao_do_mn_m",
                                    "tang_chua_nuoc", "tds_mg_l",
                                    "do_cung_mg_l", "clorua_mg_l"])
def test_doan_ra_nuoc_duoi_dat_tu_thong_so_dac_trung(truong):
    """Mot lop khac goi lai chuan_hoa_ban_ghi() ma quen truyen loai thi van
    phai ra nuoc_duoi_dat, khong duoc roi sang nhanh WQI."""
    gia_tri = "qp" if truong == "tang_chua_nuoc" else 1.0
    bg = chuan_hoa.chuan_hoa_ban_ghi({"ma": "X", "ph": 7.0, truong: gia_tri})
    assert bg["loai"] == "nuoc_duoi_dat"
    assert "wqi" not in bg


def test_loai_truyen_vao_thang_hon_phep_doan():
    """Mot ky lay mau chi con dung cot pH thi doan_loai() khong the biet do la
    lo khoan. Tham so loai phai co tieng noi quyet dinh."""
    bg = chuan_hoa.chuan_hoa_ban_ghi(
        {"ma": "QT9-BĐ", "ph": 7.1},
        loai=chuan_hoa.LOAI_NUOC_DUOI_DAT)
    assert bg["loai"] == "nuoc_duoi_dat"
    assert "wqi" not in bg and "wqi_ly_do" not in bg


# ---------------------------------------------------------------------------
# Muc nuoc ngam tach khoi muc nuoc mat
# ---------------------------------------------------------------------------

def test_h_ngam_m_va_h_m_la_hai_truong_khac_nhau():
    bg = chuan_hoa.chuan_hoa_ban_ghi({"ma": "X", "h_m": 207.3,
                                      "h_ngam_m": -14.45})
    assert bg["h_m"] == 207.3
    assert bg["h_ngam_m"] == -14.45


def test_water_level_khong_duoc_anh_xa_sang_h_ngam_m():
    """Cot water_level la cua bang nuoc mat. truy_van.sql da doi ten san
    thanh h_ngam_m cho nhanh nuoc duoi dat, nen water_level phai tiep tuc ve
    h_m; neu khong, so centimet cua nuoc mat se chay vao cot muc nuoc ngam."""
    bg = chuan_hoa.chuan_hoa_ban_ghi({"ma": "X", "water_level": 207.3})
    assert bg.get("h_m") == 207.3
    assert "h_ngam_m" not in bg


def test_giu_duoc_muc_nuoc_ngam_am():
    """Muc nuoc ngam gan nhu luon la so am. Mot khoang hop ly chi nhan so
    duong se lam rong toan bo cot nay."""
    bg = chuan_hoa.chuan_hoa_ban_ghi({"ma": "X", "h_ngam_m": -27.26},
                                     loai=chuan_hoa.LOAI_NUOC_DUOI_DAT)
    assert bg["h_ngam_m"] == -27.26


# ---------------------------------------------------------------------------
# Anh xa ten cot rieng cua nuoc duoi dat
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("ten_cot,noi_bo", [
    ("water_layer", "tang_chua_nuoc"),
    ("elevation", "cao_do_mieng_lk_m"),
    ("hardness_general", "do_cung_mg_l"),
    ("tds105", "tds_mg_l"),
    ("tds_total", "tds_mg_l"),
    ("permanganat", "permanganat_mg_l"),
    ("cl", "clorua_mg_l"),
    ("so4", "sunfat_mg_l"),
    ("f", "florua_mg_l"),
    ("cn", "xyanua_mg_l"),
    ("mn", "mn_mg_l"),
    ("fe2", "fe2_mg_l"),
    ("fe3", "fe3_mg_l"),
    ("se", "se_mg_l"),
    ("phenol", "phenol_mg_l"),
])
def test_anh_xa_cot_nuoc_duoi_dat(ten_cot, noi_bo):
    gia_tri = "qp" if noi_bo == "tang_chua_nuoc" else 1.5
    bg = chuan_hoa.chuan_hoa_ban_ghi({"ma": "X", ten_cot: gia_tri},
                                     loai=chuan_hoa.LOAI_NUOC_DUOI_DAT)
    assert bg.get(noi_bo) == gia_tri


def test_crom_tong_khong_vao_truong_crom_sau():
    """Cot cr cua water_chemistry la crom TONG. Nguong cua Cr(VI) nghiem ngat
    hon nhieu, do nham hai thong so nay la bao sai muc o nhiem."""
    bg = chuan_hoa.chuan_hoa_ban_ghi({"ma": "X", "cr": 0.012},
                                     loai=chuan_hoa.LOAI_NUOC_DUOI_DAT)
    assert bg.get("cr_mg_l") == 0.012
    assert "cr6_mg_l" not in bg


def test_hai_moc_thoi_gian_duoc_giu_rieng():
    """Lo khoan do muc nuoc hang ngay nhung lay mau hoa hoc vai lan mot nam.
    Mot moc thoi_diem duy nhat se lam so hoa hoc cu trong nhu vua do xong."""
    bg = chuan_hoa.chuan_hoa_ban_ghi(
        BAN_GHI_LO_KHOAN, loai=chuan_hoa.LOAI_NUOC_DUOI_DAT)
    assert bg["thoi_diem_muc_nuoc"] == "2026-10-06 09:00"
    assert bg["thoi_diem_chat_luong"] == "2026-05-13"


# ---------------------------------------------------------------------------
# Cac cau truy van
# ---------------------------------------------------------------------------

CAC_CAU_NGAM = ["danh_sach_lo_khoan", "muc_nuoc_ngam_moi_nhat",
                "nhiet_do_ngam_moi_nhat", "nhiet_do_ngam_bu",
                "chat_luong_ngam_moi_nhat", "chuoi_muc_nuoc_ngam",
                "chuoi_nhiet_do_ngam", "chuoi_chat_luong_ngam"]


def _bo_chu_thich(cau_sql):
    """Bo cac dong chu thich dau cau, de con lai cau lenh that."""
    cac_dong = [d for d in cau_sql.splitlines()
                if d.strip() and not d.lstrip().startswith("--")]
    return "\n".join(cac_dong)


@pytest.mark.parametrize("ten", CAC_CAU_NGAM)
def test_cau_truy_van_ngam_da_duoc_dien(ten):
    cau = _bo_chu_thich(nguon_qtqg.cau_truy_van(ten))
    assert cau.lower().lstrip().startswith(("select", "with"))


@pytest.mark.parametrize("ten", CAC_CAU_NGAM)
def test_cau_truy_van_ngam_qua_duoc_lop_chan_chi_doc(ten):
    """Lop chan trong ket_noi.py chan tu khoa ghi theo bien tu. Ten cot nhu
    create_date khong duoc lam no bao dong gia, nhung cau that cung khong duoc
    lot qua, nen kiem ca hai chieu o day."""
    cau = nguon_qtqg.cau_truy_van(ten)
    assert ket_noi._kiem_tra_cau_sql(cau) == cau


@pytest.mark.parametrize("ten", CAC_CAU_NGAM)
def test_cau_truy_van_ngam_luon_co_gioi_han(ten):
    assert "LIMIT" in nguon_qtqg.cau_truy_van(ten)


def test_chi_lay_lo_khoan_dang_hoat_dong():
    """CSDL con giu ca lo khoan da dung quan trac. So do cuoi cung cua chung
    co the cu nhieu nam; de chung mot ban do voi so do hom qua la gay hieu
    nham, nen cau truy van chi lay nhom dang hoat dong."""
    cau = nguon_qtqg.cau_truy_van("danh_sach_lo_khoan")
    assert "hien_trang" in cau
    assert nguon_qtqg.HIEN_TRANG_DANG_HOAT_DONG == "Đang hoạt động"


def test_truy_van_ngam_doc_dung_bang():
    assert "monitoring_well" in nguon_qtqg.cau_truy_van("danh_sach_lo_khoan")
    assert "water_level" in nguon_qtqg.cau_truy_van("muc_nuoc_ngam_moi_nhat")
    assert "water_temperature" in nguon_qtqg.cau_truy_van(
        "nhiet_do_ngam_moi_nhat")
    assert "water_chemistry" in nguon_qtqg.cau_truy_van(
        "chat_luong_ngam_moi_nhat")


def test_hinh_hoc_lo_khoan_duoc_chuyen_ve_4326():
    """Bang monitoring_well dung EPSG:3405, khong chuyen thi diem roi ra
    giua Vinh Bac Bo."""
    cau = nguon_qtqg.cau_truy_van("danh_sach_lo_khoan")
    assert "ST_Transform" in cau and "4326" in cau


def test_chuoi_ngam_sap_giam_dan_de_lay_moc_moi_nhat():
    """LIMIT cat sau khi sap xep. Sap tang dan roi cat se lay cac moc CU NHAT:
    lo khoan LK10T co so do tu nam 1992, bieu do se dung lai o nhung nam 90."""
    for ten in ["chuoi_muc_nuoc_ngam", "chuoi_nhiet_do_ngam",
                "chuoi_chat_luong_ngam"]:
        assert re.search(r"ORDER BY\s+date_\w+\s+DESC",
                         nguon_qtqg.cau_truy_van(ten)), ten


def test_chon_bang_chuoi_theo_nguon_khong_theo_ten_thong_so():
    """nhiet_do_c co o ca nuoc mat lan nuoc duoi dat, nen bang phai duoc chon
    theo ma tram. h_m va h_ngam_m thi o hai bang khac nhau han."""
    assert nguon_qtqg.THONG_SO_NGAM_RIENG["h_ngam_m"] == "chuoi_muc_nuoc_ngam"
    assert nguon_qtqg.THONG_SO_NGAM_RIENG["cao_do_mn_m"] \
        == "chuoi_muc_nuoc_ngam"
    assert nguon_qtqg.THONG_SO_NGAM_RIENG["nhiet_do_c"] \
        == "chuoi_nhiet_do_ngam"
    assert nguon_qtqg.THONG_SO_THUY_VAN_RIENG["h_m"] == "chuoi_muc_nuoc"


# ---------------------------------------------------------------------------
# Thuoc tinh lo khoan den duoc trinh duyet
# ---------------------------------------------------------------------------

def test_feature_lo_khoan_mang_du_thuoc_tinh_rieng():
    lo = {
        "ma": "C2a", "ten": "Lỗ khoan C2a", "loai_tram": "Nước dưới đất",
        "tang_chua_nuoc": "B/N2-Q1", "cao_do_mieng_lk_m": 670.28,
        "vi_tri_hc": "Chư Păh", "mang_quan_trac": "Quốc gia",
        "thiet_bi_do": "Thủ công", "ngay_bat_dau": "1995-12-07",
        "kinh_do": TAM_TINH[0], "vi_do": TAM_TINH[1],
    }
    tap = khong_gian.tap_feature([lo])
    assert tap["thong_ke"]["so_tram"] == 1
    tt = tap["features"][0]["properties"]
    for ten in ["tang_chua_nuoc", "cao_do_mieng_lk_m", "vi_tri_hc",
                "mang_quan_trac", "thiet_bi_do", "ngay_bat_dau"]:
        assert tt.get(ten), ten


# ---------------------------------------------------------------------------
# Khai bao phia giao dien
# ---------------------------------------------------------------------------

def _doc_config_js():
    duong_dan = os.path.join(cau_hinh.GOC_DU_AN, "assets", "js", "config.js")
    with open(duong_dan, encoding="utf-8") as f:
        return f.read()


def test_config_js_khai_bao_nhom_nuoc_duoi_dat():
    """Quy tac cua CLAUDE.md: ten truong dau ra cua backend phai khop khai bao
    trong config.js. Truong khong duoc khai bao thi giao dien khong ve."""
    chu = _doc_config_js()
    vi_tri = chu.find("nuoc_duoi_dat: [")
    assert vi_tri > 0, "config.js chua co nhom truong nuoc_duoi_dat"
    khoi = chu[vi_tri:chu.index("],", vi_tri)]

    for ten in ["h_ngam_m", "cao_do_mn_m", "tang_chua_nuoc", "tds_mg_l",
                "do_cung_mg_l", "permanganat_mg_l", "clorua_mg_l",
                "sunfat_mg_l", "florua_mg_l", "xyanua_mg_l", "fe_mg_l",
                "mn_mg_l", "cr_mg_l", "se_mg_l", "phenol_mg_l",
                "thoi_diem_muc_nuoc", "thoi_diem_chat_luong"]:
        assert "'" + ten + "'" in khoi, ten

    # Nhom nay KHONG duoc co truong WQI: xem phan dau tep ve ly do.
    assert "'wqi'" not in khoi
    assert "'phan_loai_wqi'" not in khoi


def test_config_js_co_ky_hieu_cho_lo_khoan():
    chu = _doc_config_js()
    assert "Lokhoan_TK" in chu
    assert "Nước dưới đất" in chu


def test_config_js_khai_bao_lop_lo_khoan_cho_ban_do_chinh():
    """Ban do chinh thuan tinh nen lo khoan len do qua lop quan_trac_ndd,
    sinh bang scripts/08_xuat_lo_khoan_ndd.py."""
    chu = _doc_config_js()
    vi_tri = chu.find("quan_trac_ndd: {")
    assert vi_tri > 0, "config.js chua khai bao lop quan_trac_ndd"
    assert "'quan_trac_ndd'" in chu, "lop chua duoc dua vao nhom_lop nao"

    # Cat dung khoi cua lop: dau dong co 4 dau cach la muc thut cua mot lop
    # trong CAU_HINH.lop. Lay du 6000 ky tu se tran sang truong_realtime.
    ket = chu.find("\n    },\n", vi_tri)
    assert ket > vi_tri
    khoi = chu[vi_tri:ket]

    assert "quan_trac_ndd.geojson" in khoi
    assert "Lokhoan_TK" in khoi
    # Khong duoc co WQI, xem phan dau tep ve ly do
    assert "'wqi'" not in khoi


def test_dang_ky_lop_lo_khoan_khop_voi_du_lieu():
    """lop_co_san() trong tinh.js dung danh sach nay de biet lop nao co du lieu,
    nen dang ky va du lieu phai khop nhau theo CA HAI chieu:

      - Co tep ma khong dang ky  -> lop khong bao gio duoc nap, du lieu nam khong.
      - Dang ky ma khong co tep  -> moi lan mo trang la mot loi 404 trong console.

    Day la ly do khong dang ky truoc roi sinh tep sau.
    """
    co_tep = os.path.isfile(os.path.join(
        cau_hinh.GOC_DU_AN, "data", "quan_trac_ndd.geojson"))
    duong_dan = os.path.join(cau_hinh.GOC_DU_AN, "tinh.json")
    with open(duong_dan, encoding="utf-8") as f:
        da_dang_ky = "quan_trac_ndd" in json.load(f)["lop_co_san"]

    if co_tep:
        assert da_dang_ky, (
            "da co data/quan_trac_ndd.geojson nhung chua them quan_trac_ndd "
            "vao lop_co_san trong tinh.json")
    else:
        assert not da_dang_ky, (
            "tinh.json dang ky quan_trac_ndd nhung chua co "
            "data/quan_trac_ndd.geojson; chay scripts/08_xuat_lo_khoan_ndd.py "
            "truoc, hoac bo dang ky di")


def test_tep_lop_lo_khoan_da_duoc_sinh():
    duong_dan = os.path.join(cau_hinh.GOC_DU_AN, "data",
                             "quan_trac_ndd.geojson")
    if not os.path.isfile(duong_dan):
        pytest.skip("Chua chay scripts/08_xuat_lo_khoan_ndd.py")

    with open(duong_dan, encoding="utf-8") as f:
        tap = json.load(f)

    assert tap["type"] == "FeatureCollection"
    assert tap["crs"]["properties"]["name"] == "urn:ogc:def:crs:OGC:1.3:CRS84"
    assert len(tap["features"]) > 0

    khung = khong_gian.khung_bao()
    for f_ in tap["features"]:
        tt = f_["properties"]
        assert tt.get("ma"), "lo khoan thieu ma thi khong noi duoc voi so do"
        # Moi doi tuong phai noi ro so do la cua thoi diem xuat, khong phai
        # so theo thoi gian thuc
        assert "Quan trắc Quốc gia" in (tt.get("nguon_dl") or "")
        # Lop tinh nay KHONG duoc mang WQI
        assert "wqi" not in tt
        kd, vd = f_["geometry"]["coordinates"]
        assert khung[0] <= kd <= khung[2] and khung[1] <= vd <= khung[3]


def test_ky_hieu_lo_khoan_da_duoc_sinh():
    """scripts/06_tao_ky_hieu.py chuyen .qml cua QGIS thanh SVG. Thieu tep nay
    thi diem lo khoan ve ra vong tron mac dinh."""
    goc = cau_hinh.GOC_DU_AN
    tep_svg = os.path.join(goc, "assets", "ky_hieu", "Lokhoan_TK.svg")
    assert os.path.isfile(tep_svg)

    danh_muc = os.path.join(goc, "assets", "ky_hieu", "ky_hieu.json")
    with open(danh_muc, encoding="utf-8") as f:
        # nap_danh_muc_ky_hieu() trong assets/js/ky_hieu.js doc khoa "ky_hieu"
        assert "Lokhoan_TK" in json.load(f)["ky_hieu"]
