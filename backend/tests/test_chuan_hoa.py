"""Kiem thu chuan hoa ten truong va gia tri.

Day la cho de sinh loi im lang nhat cua ca backend: mot ten cot khong khop thi
thong so bi roi mat ma khong co thong bao nao, nguoi dung chi thay bang thieu
cot. Cac test duoi day khoa lai nhung quy tac da chon.
"""

import pytest

import chuan_hoa


# ---------------------------------------------------------------------------
# Anh xa ten cot
# ---------------------------------------------------------------------------

def test_anh_xa_ten_cot_tieng_viet_co_dau():
    dong = {"Mã trạm": "GL-M9", "Tên trạm": "Cầu Ca Tung", "Mực nước": 3.2}
    bg = chuan_hoa.chuan_hoa_ban_ghi(dong)
    assert bg["ma"] == "GL-M9"
    assert bg["ten"] == "Cầu Ca Tung"
    assert bg["h_m"] == 3.2


def test_anh_xa_khong_phan_biet_dau_gach_va_chu_hoa():
    """Ten cot thuc te rat da dang: station_code, STATION CODE, Station-Code."""
    for ten in ["station_code", "STATION CODE", "Station-Code", "stationcode"]:
        bg = chuan_hoa.chuan_hoa_ban_ghi({ten: "X1"})
        assert bg["ma"] == "X1", ten


def test_moi_ten_truong_noi_bo_tu_nhan_duoc_chinh_no():
    """Ban ghi da dung ten noi bo phai di qua chuan hoa ma khong mat truong.

    Thieu quy tac nay thi nhung truong co ten khong nam trong danh sach ung
    vien cua chinh no, vi du nhiet_do_c hay tss_mg_l, bi roi mat lang le.
    """
    dong = {ten: 1 for ten in chuan_hoa.BANG_ANH_XA
            if ten not in chuan_hoa.TRUONG_CHU}
    bg = chuan_hoa.chuan_hoa_ban_ghi(dong)
    for ten in dong:
        assert ten in bg, "roi mat truong " + ten


def test_cot_khong_nhan_ra_thi_bo_qua():
    """Khong mang theo rac ra trinh duyet."""
    bg = chuan_hoa.chuan_hoa_ban_ghi({"ma": "X1", "cot_la_lung_123": 9})
    assert "cot_la_lung_123" not in bg


# ---------------------------------------------------------------------------
# Ep gia tri ve so
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("tho, mong_doi", [
    (7.1, 7.1),
    ("7.1", 7.1),
    ("7,1", 7.1),          # dau phay thap phan kieu Viet
    (" 7.1 ", 7.1),
    ("<0,003", 0.003),     # gia tri duoi gioi han phat hien
    (">14", 14.0),
])
def test_ep_so(tho, mong_doi):
    bg = chuan_hoa.chuan_hoa_ban_ghi({"ma": "X1", "ph": tho})
    assert bg["ph"] == pytest.approx(mong_doi)


@pytest.mark.parametrize("tho", ["KPH", "kph", "n/a", "-", "", None,
                                 "khong", "chua do"])
def test_gia_tri_khuyet_thi_bo_khoa(tho):
    """Khong co so do thi khoa bi bo han, khong dien 0."""
    bg = chuan_hoa.chuan_hoa_ban_ghi({"ma": "X1", "ph": tho})
    assert "ph" not in bg


def test_khong_bao_gio_dien_0_thay_cho_khuyet():
    """Quy tac khong doi cua du an: thieu so do thi de khuyet, khong dien 0.
    Dien 0 vao pH hay DO la bao sai ket qua quan trac."""
    bg = chuan_hoa.chuan_hoa_ban_ghi({"ma": "X1", "ph": None,
                                      "do_mg_l": "KPH"})
    assert bg.get("ph") != 0
    assert bg.get("do_mg_l") != 0
    assert "ph" not in bg and "do_mg_l" not in bg


# ---------------------------------------------------------------------------
# Khoang gia tri hop ly
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("ten, gia_tri", [
    ("ph", 15),            # pH chi tu 0 den 14
    ("ph", -1),
    ("ph", -9999),         # gia tri bao loi quen thuoc cua thiet bi
    ("wqi", 101),
    ("nhiet_do_c", 999),
    ("vi_do", 200),
])
def test_gia_tri_ngoai_khoang_bi_loai(ten, gia_tri):
    bg = chuan_hoa.chuan_hoa_ban_ghi({"ma": "X1", ten: gia_tri})
    assert ten not in bg, "{} = {} dang le phai bi loai".format(ten, gia_tri)


def test_gia_tri_dung_bien_thi_duoc_nhan():
    bg = chuan_hoa.chuan_hoa_ban_ghi({"ma": "X1", "ph": 14, "wqi": 100})
    assert bg["ph"] == 14
    assert bg["wqi"] == 100


# ---------------------------------------------------------------------------
# Doan nhom thong so
# ---------------------------------------------------------------------------

def test_doan_loai_thuy_van():
    bg = chuan_hoa.chuan_hoa_ban_ghi({"ma": "TV-01", "muc_nuoc": 2.5})
    assert bg["loai"] == "thuy_van"


def test_doan_loai_mua():
    bg = chuan_hoa.chuan_hoa_ban_ghi({"ma": "M-01", "mua_24h": 60})
    assert bg["loai"] == "mua"


def test_doan_loai_chat_luong_nuoc():
    bg = chuan_hoa.chuan_hoa_ban_ghi({"ma": "X1", "ph": 7.1})
    assert bg["loai"] == "chat_luong_nuoc"


def test_loai_khop_khoa_truong_realtime():
    """Ba gia tri loai phai khop khoa trong CAU_HINH.truong_realtime cua
    assets/js/config.js, vi giao dien tra danh sach truong theo chinh chung."""
    cac_loai = {
        chuan_hoa.chuan_hoa_ban_ghi({"ma": "a", "muc_nuoc": 1})["loai"],
        chuan_hoa.chuan_hoa_ban_ghi({"ma": "b", "mua_24h": 1})["loai"],
        chuan_hoa.chuan_hoa_ban_ghi({"ma": "c", "ph": 7})["loai"],
    }
    assert cac_loai == {"thuy_van", "mua", "chat_luong_nuoc"}


# ---------------------------------------------------------------------------
# Chuan hoa nhieu dong
# ---------------------------------------------------------------------------

def test_bo_dong_khong_co_ma_tram():
    """Ban ghi khong co ma thi khong ghep duoc vao hinh hoc, giu lai vo ich."""
    cac_dong = [{"ma": "X1", "ph": 7}, {"ph": 7}, {"ma": "", "ph": 7}]
    assert len(chuan_hoa.chuan_hoa_nhieu(cac_dong)) == 1


def test_bo_dau():
    assert chuan_hoa.bo_dau("Đắk Pơ") == "dak po"
    assert chuan_hoa.bo_dau(None) == ""
