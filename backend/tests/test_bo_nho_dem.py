"""Kiem thu bo nho dem.

Bo nho dem khong phai de chay nhanh hon ma de BAO VE CSDL QTQG dang chay that:
nhieu trinh duyet mo cung luc, moi trang tu lam moi 5 phut, neu khong co bo dem
thi moi nguoi dung la mot luot truy van rieng.
"""

import bo_nho_dem


def setup_function():
    bo_nho_dem.xoa()


def test_trong_ttl_chi_goi_nguon_mot_lan():
    so_lan = {"n": 0}

    def tinh():
        so_lan["n"] += 1
        return so_lan["n"]

    a = bo_nho_dem.lay_hoac_tinh("k", tinh, ttl_giay=60)
    b = bo_nho_dem.lay_hoac_tinh("k", tinh, ttl_giay=60)
    c = bo_nho_dem.lay_hoac_tinh("k", tinh, ttl_giay=60)

    assert so_lan["n"] == 1
    assert a == b == c == 1


def test_het_ttl_thi_goi_lai_nguon():
    so_lan = {"n": 0}

    def tinh():
        so_lan["n"] += 1
        return so_lan["n"]

    bo_nho_dem.lay_hoac_tinh("k", tinh, ttl_giay=60)
    # ttl = 0 nghia la moi o trong bo dem deu da qua han
    bo_nho_dem.lay_hoac_tinh("k", tinh, ttl_giay=0)
    assert so_lan["n"] == 2


def test_hai_khoa_khac_nhau_khong_lan_vao_nhau():
    bo_nho_dem.lay_hoac_tinh("tram", lambda: "A", ttl_giay=60)
    bo_nho_dem.lay_hoac_tinh("so_do", lambda: "B", ttl_giay=60)
    assert bo_nho_dem.lay_hoac_tinh("tram", lambda: "X", ttl_giay=60) == "A"
    assert bo_nho_dem.lay_hoac_tinh("so_do", lambda: "X", ttl_giay=60) == "B"


def test_tuoi_cua_khoa():
    assert bo_nho_dem.tuoi_cua("k") is None
    bo_nho_dem.lay_hoac_tinh("k", lambda: 1, ttl_giay=60)
    tuoi = bo_nho_dem.tuoi_cua("k")
    assert tuoi is not None and tuoi >= 0


def test_xoa_mot_khoa():
    bo_nho_dem.lay_hoac_tinh("a", lambda: 1, ttl_giay=60)
    bo_nho_dem.lay_hoac_tinh("b", lambda: 2, ttl_giay=60)
    bo_nho_dem.xoa("a")
    assert bo_nho_dem.tuoi_cua("a") is None
    assert bo_nho_dem.tuoi_cua("b") is not None


def test_gia_tri_none_van_duoc_dem():
    """Nguon tra None cung la mot cau tra loi, khong duoc goi lai nguon lien
    tuc chi vi ket qua rong."""
    so_lan = {"n": 0}

    def tinh():
        so_lan["n"] += 1
        return None

    bo_nho_dem.lay_hoac_tinh("k", tinh, ttl_giay=60)
    bo_nho_dem.lay_hoac_tinh("k", tinh, ttl_giay=60)
    assert so_lan["n"] == 1
