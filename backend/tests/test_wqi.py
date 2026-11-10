"""Kiem thu tinh va phan loai VN_WQI theo Quyet dinh 1460/QD-TCMT.

Ban goc dung de doi chieu: CSDL/WQI_1460_QD-TCMT_428277.doc

Bo test nay chia lam ba phan:
  1. Phan loai va trang thai, kiem tai dung bien.
  2. WQI tung thong so, doi chieu voi VI DU MAU o muc 2.3 cua quyet dinh.
     Day la phan dang tin nhat: moi con so mong doi deu lay nguyen tu van ban.
  3. Tong hop WQI cuoi cung va dieu kien du lieu toi thieu.
"""

import pytest

import wqi


# ===========================================================================
# 1. Phan loai va trang thai
# ===========================================================================

@pytest.mark.parametrize("gia_tri, mong_doi", [
    (100, "Rất tốt"),
    (91, "Rất tốt"),       # bien duoi cua Rat tot
    (90.9, "Tốt"),
    (76, "Tốt"),
    (75.9, "Trung bình"),
    (51, "Trung bình"),
    (50.9, "Xấu"),
    (26, "Xấu"),
    (25.9, "Kém"),
    (10, "Kém"),
    (9.9, "Ô nhiễm rất nặng"),
    (0, "Ô nhiễm rất nặng"),
])
def test_phan_loai_tai_bien(gia_tri, mong_doi):
    assert wqi.phan_loai_wqi(gia_tri) == mong_doi


@pytest.mark.parametrize("gia_tri, mong_doi", [
    (100, "binh_thuong"),
    (51, "binh_thuong"),
    (50.9, "theo_doi"),
    (26, "theo_doi"),
    (25.9, "canh_bao"),
    (0, "canh_bao"),
])
def test_trang_thai_tai_bien(gia_tri, mong_doi):
    assert wqi.trang_thai_theo_wqi(gia_tri) == mong_doi


def test_trang_thai_khop_nhan_trong_config():
    """Ba trang thai phai khop khoa trong CAU_HINH.nhan_trang_thai cua
    assets/js/config.js, vi giao dien tra nhan theo chinh ba chuoi nay."""
    cac = {wqi.trang_thai_theo_wqi(v) for v in (95, 40, 10)}
    assert cac == {"binh_thuong", "theo_doi", "canh_bao"}


@pytest.mark.parametrize("gia_tri", [None, "", -1, 101, "khong phai so", []])
def test_hop_le_loai_gia_tri_ngoai_khoang(gia_tri):
    assert wqi.hop_le(gia_tri) is False


# ===========================================================================
# 2. WQI tung thong so, doi chieu vi du mau muc 2.3
# ===========================================================================

# Bang so lieu o muc 2.3.a cua quyet dinh
MAU_2_3 = {
    "ph": 7.2,
    "cu_mg_l": 0.05,
    "as_mg_l": 0.02,
    "nhiet_do_c": 27.5,
    "do_mg_l": 5.7,
    "bod5_mg_l": 20.0,
    "cod_mg_l": 25.0,
    "amoni_mg_l": 0.2,
    "photphat_mg_l": 0.3,
    "aldrin_ug_l": 0.05,
    "dieldrin_ug_l": 0.05,
    "coliform_mpn_100ml": 10000,
}

# Ket qua WQI tung thong so do chinh quyet dinh ghi ra
KET_QUA_2_3 = {
    "ph": 100,
    "cu_mg_l": 100,
    "as_mg_l": 75,
    "do_mg_l": 73.3,
    "bod5_mg_l": 37.5,
    "cod_mg_l": 58.3,
    "amoni_mg_l": 100,
    "photphat_mg_l": 50,
    "coliform_mpn_100ml": 25,
    "aldrin_ug_l": 100,
    "dieldrin_ug_l": 100,
}


@pytest.mark.parametrize("ten, mong_doi", sorted(KET_QUA_2_3.items()))
def test_vi_du_mau_tung_thong_so(ten, mong_doi):
    """Tung con so trong vi du mau cua quyet dinh phai tai lap duoc.

    Dung sai 0,25 danh cho mot cho duy nhat: WQI_DO. Quyet dinh lam tron
    DO_baohoa thanh 7,78 roi moi chia, ra 73,3; o day giu nguyen 7,7965 nen ra
    73,1. Chenh lech la do lam tron trung gian cua van ban, khong phai sai sot
    cua cong thuc.
    """
    diem = wqi.wqi_tung_thong_so(MAU_2_3)
    assert ten in diem
    assert diem[ten] == pytest.approx(mong_doi, abs=0.25)


def test_do_bao_hoa_theo_cong_thuc_bac_ba():
    """Quyet dinh ghi DO_baohoa tai 27,5 do C bang 7,78."""
    assert wqi.do_bao_hoa(27.5) == pytest.approx(7.78, abs=0.02)


def test_do_bao_hoa_can_ca_nhiet_do():
    """Thieu nhiet do thi khong tinh duoc DO phan tram bao hoa, phai tra None
    chu khong duoc doan mot nhiet do mac dinh."""
    assert wqi.wqi_do(5.7, None) is None
    assert wqi.wqi_do(None, 27.5) is None


# ---------------------------------------------------------------------------
# pH, Bang 4
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("ph, mong_doi", [
    (5.4, 10),      # pH < 5,5
    (9.1, 10),      # pH > 9
    (6, 100),       # bien duoi cua doan dat 100 diem
    (7.2, 100),
    (8.5, 100),     # bien tren cua doan dat 100 diem
    (5.75, 75),     # giua 5,5 va 6, cong thuc 2
    (8.75, 75),     # giua 8,5 va 9, cong thuc 1
    (5.5, 50),
    (9, 50),
])
def test_wqi_ph(ph, mong_doi):
    assert wqi.wqi_ph(ph) == pytest.approx(mong_doi, abs=0.01)


# ---------------------------------------------------------------------------
# DO phan tram bao hoa, Bang 3
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("phan_tram, mong_doi", [
    (10, 10),       # duoi 20
    (250, 10),      # tren 200
    (88, 100),      # bien duoi cua doan 100 diem
    (100, 100),
    (112, 100),     # bien tren cua doan 100 diem
    (50, 50),
    (75, 75),
])
def test_wqi_do_theo_phan_tram(phan_tram, mong_doi, monkeypatch):
    """Dat truc tiep phan tram bao hoa de kiem rieng Bang 3."""
    monkeypatch.setattr(wqi, "phan_tram_bao_hoa",
                        lambda a, b: phan_tram)
    assert wqi.wqi_do(1, 1) == pytest.approx(mong_doi, abs=0.01)


# ---------------------------------------------------------------------------
# Dau so sanh cua Bang 1 va Bang 2
# ---------------------------------------------------------------------------

def test_muc_5_dau_lon_hon_han():
    """Coliform muc 5 ghi ">10.000": dung 10.000 van thuoc muc 4, duoc 25
    diem. Day chinh la con so trong vi du mau cua quyet dinh."""
    b = wqi.BANG_NHOM_V["coliform_mpn_100ml"]
    assert wqi.wqi_theo_bang(10000, b) == pytest.approx(25)
    assert wqi.wqi_theo_bang(10001, b) == pytest.approx(10)


def test_muc_5_dau_lon_hon_bang():
    """Cd muc 5 ghi ">=0,1": dung 0,1 da tut xuong 10 diem."""
    b = wqi.BANG_NHOM_III["cd_mg_l"]
    assert wqi.wqi_theo_bang(0.1, b) == pytest.approx(10)


def test_muc_1_dau_nho_hon_han():
    """N-NH4 muc 1 ghi "<0,3": dung 0,3 roi vao muc 2, duoc 75 diem."""
    b = wqi.BANG_NHOM_IV["amoni_mg_l"]
    assert wqi.wqi_theo_bang(0.29, b) == pytest.approx(100)
    assert wqi.wqi_theo_bang(0.3, b) == pytest.approx(75)


def test_muc_1_dau_nho_hon_bang():
    """BOD5 muc 1 ghi "<=4": dung 4 van duoc 100 diem."""
    b = wqi.BANG_NHOM_IV["bod5_mg_l"]
    assert wqi.wqi_theo_bang(4, b) == pytest.approx(100)


def test_cp_trung_moc_thi_bang_dung_qi():
    """Ghi chu sau Bang 2: Cp trung voi BPi thi WQI bang dung qi tuong ung."""
    b = wqi.BANG_NHOM_III["as_mg_l"]
    assert wqi.wqi_theo_bang(0.02, b) == pytest.approx(75)
    assert wqi.wqi_theo_bang(0.05, b) == pytest.approx(50)


def test_nitrit_la_bac_thang():
    """N-NO2 trong Bang 1 chi co hai muc, ba muc giua bo trong."""
    assert wqi.wqi_bac_thang(0.05, 0.05) == 100
    assert wqi.wqi_bac_thang(0.06, 0.05) == 10


# ===========================================================================
# 3. Tong hop WQI cuoi cung
# ===========================================================================

def test_vi_du_mau_tong_hop_theo_dung_cong_thuc():
    """Tong hop cho vi du mau muc 2.3.

    QUAN TRONG: quyet dinh IN ra 16 (khong trong so) va 19 (co trong so),
    nhung hai con so do KHONG ra tu chinh cong thuc in ngay phia tren chung.
    Thay dung cac so ma quyet dinh tu viet trong anh cong thuc:

        100/100 x (100x100)^(1/2)/100 x (100x75)^(1/2)/100
                x [ (73,3+37,5+58,3+100+50)/5 x 25 ]^(1/2)
      = 1 x 1 x 0,866 x (63,82 x 25)^(1/2)
      = 0,866 x 39,94
      = 34,59

    tuc 35 chu khong phai 16. Tuong tu, ban co trong so ra 40,44 chu khong
    phai 19. Day la sai sot so hoc cua vi du mau trong van ban.

    Cai dat o day bam theo CONG THUC, vi do moi la phan quy pham (muc 2.2.b).
    Dung sua ham tinh de ep ra 16 va 19.
    """
    kq3 = wqi.tinh_wqi_tu_thong_so(MAU_2_3)
    kq5 = wqi.tinh_wqi_tu_thong_so(MAU_2_3, co_trong_so=True)

    assert kq3["cong_thuc"] == "3"
    assert kq5["cong_thuc"] == "5"
    assert kq3["wqi"] == 35
    assert kq5["wqi"] == 40
    # Co trong so thi nhom IV nang hon, ma nhom IV o day tot hon nhom V
    assert kq5["wqi"] > kq3["wqi"]


def test_khong_co_nhom_v_thi_dung_cong_thuc_4():
    mau = dict(MAU_2_3)
    del mau["coliform_mpn_100ml"]
    kq = wqi.tinh_wqi_tu_thong_so(mau)
    assert kq["cong_thuc"] == "4"
    assert kq["wqi"] is not None


def test_nhom_khuyet_bi_bo_khoi_tich_chu_khong_thanh_khong():
    """Nhom II khong co so lieu thi thua so cua no phai bi bo han. Neu coi la
    0 thi WQI thanh 0, neu coi la 100 diem chia 100 thi vo tinh dung nhung
    phai la do bo han, khong phai do may man."""
    mau = dict(MAU_2_3)
    del mau["aldrin_ug_l"]
    del mau["dieldrin_ug_l"]
    kq = wqi.tinh_wqi_tu_thong_so(mau)
    assert kq["wqi"] == 35        # giong truong hop co nhom II deu 100 diem


def test_wqi_lam_tron_thanh_so_nguyen():
    """Muc 2.2.b: gia tri WQI sau khi tinh toan se duoc lam tron thanh so
    nguyen."""
    kq = wqi.tinh_wqi_tu_thong_so(MAU_2_3)
    assert isinstance(kq["wqi"], int)


def test_wqi_luon_nam_trong_khoang_0_den_100():
    rat_sach = {"ph": 7, "do_mg_l": 8, "nhiet_do_c": 25, "bod5_mg_l": 1,
                "cod_mg_l": 5, "amoni_mg_l": 0.05, "photphat_mg_l": 0.05,
                "coliform_mpn_100ml": 100}
    rat_ban = {"ph": 3, "do_mg_l": 0.1, "nhiet_do_c": 25, "bod5_mg_l": 500,
               "cod_mg_l": 900, "amoni_mg_l": 50, "photphat_mg_l": 40,
               "coliform_mpn_100ml": 9000000}
    for mau in (rat_sach, rat_ban):
        kq = wqi.tinh_wqi_tu_thong_so(mau)
        assert 0 <= kq["wqi"] <= 100


def test_nuoc_rat_sach_duoc_xep_loai_cao():
    rat_sach = {"ph": 7, "do_mg_l": 8, "nhiet_do_c": 25, "bod5_mg_l": 1,
                "cod_mg_l": 5, "amoni_mg_l": 0.05, "photphat_mg_l": 0.05,
                "coliform_mpn_100ml": 100}
    kq = wqi.tinh_wqi_tu_thong_so(rat_sach)
    assert wqi.phan_loai_wqi(kq["wqi"]) in ("Rất tốt", "Tốt")


# ---------------------------------------------------------------------------
# Dieu kien du lieu toi thieu, muc 2.1.b
# ---------------------------------------------------------------------------

def test_bat_buoc_co_nhom_iv():
    """Khong co nhom IV thi khong duoc cong bo WQI, du co du nhom khac."""
    mau = {"ph": 7.2, "as_mg_l": 0.01, "coliform_mpn_100ml": 100}
    kq = wqi.tinh_wqi_tu_thong_so(mau)
    assert kq["wqi"] is None
    assert "nhóm IV" in kq["ly_do"]


def test_nhom_iv_phai_co_toi_thieu_ba_thong_so():
    mau = {"ph": 7.2, "bod5_mg_l": 5, "cod_mg_l": 12,
           "coliform_mpn_100ml": 100}
    kq = wqi.tinh_wqi_tu_thong_so(mau)
    assert kq["wqi"] is None
    assert "tối thiểu 3" in kq["ly_do"]


def test_phai_co_toi_thieu_ba_nhom():
    """Chi co moi nhom IV, du ba thong so, van chua du ba nhom."""
    mau = {"bod5_mg_l": 5, "cod_mg_l": 12, "amoni_mg_l": 0.1,
           "photphat_mg_l": 0.05}
    kq = wqi.tinh_wqi_tu_thong_so(mau)
    assert kq["wqi"] is None
    assert "nhóm" in kq["ly_do"]


def test_du_ba_nhom_thi_tinh_duoc():
    """pH (nhom I) + ba thong so nhom IV + Coliform (nhom V) = 3 nhom."""
    mau = {"ph": 7.2, "bod5_mg_l": 5, "cod_mg_l": 12, "amoni_mg_l": 0.1,
           "coliform_mpn_100ml": 100}
    kq = wqi.tinh_wqi_tu_thong_so(mau)
    assert kq["wqi"] is not None


# ---------------------------------------------------------------------------
# gan_wqi: duong di trong ban ghi so do
# ---------------------------------------------------------------------------

def test_uu_tien_so_wqi_cua_nguon():
    """QTQG la co quan cong bo so chinh thuc. Co san WQI thi dung, khong tinh
    lai roi ra so khac."""
    ban_ghi = dict(MAU_2_3)
    ban_ghi["wqi"] = 72.4
    wqi.gan_wqi(ban_ghi)
    assert ban_ghi["wqi"] == 72.4
    assert ban_ghi["phan_loai_wqi"] == "Trung bình"
    assert "wqi_tu_tinh" not in ban_ghi


def test_tu_tinh_khi_nguon_khong_co_wqi():
    ban_ghi = dict(MAU_2_3)
    wqi.gan_wqi(ban_ghi)
    assert ban_ghi["wqi"] == 35
    assert ban_ghi["wqi_tu_tinh"] is True
    assert ban_ghi["trang_thai"] == "theo_doi"


def test_khong_du_dieu_kien_thi_de_khuyet_kem_ly_do():
    ban_ghi = {"ma": "X1", "ph": 7.1}
    wqi.gan_wqi(ban_ghi)
    assert "wqi" not in ban_ghi
    assert ban_ghi["wqi_ly_do"]
    assert ban_ghi["wqi_thieu_thong_so"]


def test_tram_thuy_van_khong_bi_hoi_ve_wqi():
    """Tram thuy van khong bao gio do WQI, bao thieu thong so o do la vo nghia
    va lam nhieu giao dien."""
    ban_ghi = {"ma": "TV-01", "h_m": 2.5, "q_m3s": 40.0}
    wqi.gan_wqi(ban_ghi)
    assert "wqi" not in ban_ghi
    assert "wqi_thieu_thong_so" not in ban_ghi
    assert "wqi_ly_do" not in ban_ghi


def test_khong_ghi_de_trang_thai_cua_nguon():
    ban_ghi = {"ma": "X1", "wqi": 95, "trang_thai": "canh_bao"}
    wqi.gan_wqi(ban_ghi)
    assert ban_ghi["trang_thai"] == "canh_bao"


def test_gia_tri_bao_loi_cua_thiet_bi_khong_thanh_wqi():
    ban_ghi = {"ma": "X1", "wqi": -9999, "ph": 7.0}
    wqi.gan_wqi(ban_ghi)
    assert ban_ghi.get("wqi") != -9999
