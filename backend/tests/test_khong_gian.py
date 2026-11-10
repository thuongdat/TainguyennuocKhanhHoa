"""Kiem thu dung GeoJSON va loc theo pham vi tinh.

CSDL QTQG la cua ca nuoc. Khong loc thi ban do nho se phai thu nho ra ca Viet
Nam de chua het cac diem, va bang se day tram khong thuoc tinh.
"""

import json
import os

import conftest

import cau_hinh
import khong_gian


# Toa do mau suy tu khung_bao_nen trong tinh.json chu KHONG gan cung. Gan cung
# toa do cua mot tinh thi khi sao du an sang tinh khac, moi test loc khong gian
# deu do ma khong phai vi ma sai.
_KB = khong_gian.khung_bao()
TAM_TINH = ((_KB[0] + _KB[2]) / 2.0, (_KB[1] + _KB[3]) / 2.0)
# Diem thu hai cung nam trong khung bao, lech ve goc duoi trai mot phan tu.
TRONG_TINH_2 = (_KB[0] + (_KB[2] - _KB[0]) / 4.0,
                _KB[1] + (_KB[3] - _KB[1]) / 4.0)
NGOAI_TINH_HA_NOI = (105.85, 21.03)
NGOAI_TINH_CAN_THO = (105.78, 10.03)


def _tram(ma="X1", kinh_do=TAM_TINH[0], vi_do=TAM_TINH[1], **thuoc_tinh):
    bg = {"ma": ma, "ten": "Tram " + ma,
          "kinh_do": kinh_do, "vi_do": vi_do}
    bg.update(thuoc_tinh)
    return bg


# ---------------------------------------------------------------------------
# Khung bao doc tu tinh.json
# ---------------------------------------------------------------------------

def test_khung_bao_doc_duoc_tu_tinh_json():
    kb = khong_gian.khung_bao()
    assert kb is not None
    assert len(kb) == 4
    # kinh do min < max, vi do min < max
    assert kb[0] < kb[2] and kb[1] < kb[3]


def test_tham_so_tinh_la_nguon_su_that_dung_chung():
    """Backend va trinh duyet phai doc cung mot tep tinh.json.

    Doi chieu voi chinh tep o goc du an, khong gan cung ma tinh: gan cung thi
    test nay do ngay khi sao du an sang tinh khac, ma do vi ly do vo nghia.
    """
    tt = khong_gian.tham_so_tinh()
    with open(os.path.join(cau_hinh.GOC_DU_AN, "tinh.json"), encoding="utf-8") as f:
        tu_tep = json.load(f)
    assert tt["ma"] == tu_tep["ma"]
    assert tt["khung_bao_nen"] == tu_tep["khung_bao_nen"]


# ---------------------------------------------------------------------------
# Loc theo pham vi tinh
# ---------------------------------------------------------------------------

def test_tram_trong_tinh_duoc_giu():
    assert khong_gian.trong_pham_vi_tinh(*TAM_TINH) is True
    assert khong_gian.trong_pham_vi_tinh(*TRONG_TINH_2) is True


def test_tram_ngoai_tinh_bi_loai():
    assert khong_gian.trong_pham_vi_tinh(*NGOAI_TINH_HA_NOI) is False
    assert khong_gian.trong_pham_vi_tinh(*NGOAI_TINH_CAN_THO) is False


def test_tram_thieu_toa_do_khong_tinh_la_trong_tinh():
    assert khong_gian.trong_pham_vi_tinh(None, TAM_TINH[1]) is False
    assert khong_gian.trong_pham_vi_tinh(TAM_TINH[0], None) is False


def test_tap_feature_dem_dung_so_tram_bi_bo():
    """Phai bao ro da bo bao nhieu tram va vi sao, khong im lang lam mat du
    lieu roi de nguoi dung tu phat hien."""
    cac_tram = [
        _tram("TRONG-1"),
        _tram("TRONG-2", *TRONG_TINH_2),
        _tram("NGOAI-1", *NGOAI_TINH_HA_NOI),
        _tram("THIEU-1", None, None),
    ]
    tap = khong_gian.tap_feature(cac_tram)
    assert tap["thong_ke"]["so_tram"] == 2
    assert tap["thong_ke"]["bo_ngoai_tinh"] == 1
    assert tap["thong_ke"]["bo_thieu_toa_do"] == 1
    assert len(tap["features"]) == 2


def test_tat_loc_thi_giu_tram_ngoai_tinh():
    cac_tram = [_tram("NGOAI-1", *NGOAI_TINH_HA_NOI)]
    tap = khong_gian.tap_feature(cac_tram, loc_theo_tinh=False)
    assert tap["thong_ke"]["so_tram"] == 1


# ---------------------------------------------------------------------------
# Cau truc FeatureCollection
# ---------------------------------------------------------------------------

def test_tap_feature_hop_le_va_doc_duoc_bang_json():
    tap = khong_gian.tap_feature([_tram()])
    json.dumps(tap)   # khong duoc nem loi
    assert tap["type"] == "FeatureCollection"
    assert tap["crs"]["properties"]["name"] == "urn:ogc:def:crs:OGC:1.3:CRS84"


def test_feature_dung_ten_truong_nhu_quan_trac_geojson():
    """Dung ten truong giong data/quan_trac.geojson thi khai bao lop
    CAU_HINH.lop.quan_trac trong config.js dung lai duoc nguyen ven."""
    tap = khong_gian.tap_feature([_tram(loai_tram="Thủy văn")])
    tt = tap["features"][0]["properties"]
    for ten in ["ma", "ten", "loai_tram", "song_ho", "thong_so",
                "ten_luu_vuc", "don_vi_quan_ly", "nguon_dl"]:
        assert ten in tt, "thieu truong " + ten


def test_hinh_hoc_la_diem_dung_thu_tu_kinh_do_vi_do():
    """GeoJSON quy dinh thu tu [kinh do, vi do]. Dao thu tu la loi kinh dien,
    diem se roi xuong bien Dong hoac sang Trung Quoc."""
    kinh_do = round(TAM_TINH[0], 6)
    vi_do = round(TAM_TINH[1], 6)
    tap = khong_gian.tap_feature([_tram(kinh_do=kinh_do, vi_do=vi_do)])
    hh = tap["features"][0]["geometry"]
    assert hh["type"] == "Point"
    assert hh["coordinates"] == [kinh_do, vi_do]
    # Dao thu tu phai bi loai vi vi do cua tinh khong bao gio la mot kinh do
    # hop le trong khung bao.
    assert khong_gian.trong_pham_vi_tinh(vi_do, kinh_do) is False


def test_ma_dia_phuong_khuyet_khi_chua_anh_xa():
    """Bang anh_xa_tram.csv dien tay, chua dien thi phai de khuyet chu khong
    doan theo ten."""
    khong_gian._anh_xa_tram = None      # nap lai tu tep
    tap = khong_gian.tap_feature([_tram("QTQG-999")])
    assert tap["features"][0]["properties"]["ma_dia_phuong"] is None


def test_nguon_dl_duoc_dien_tu_cau_hinh():
    tap = khong_gian.tap_feature([_tram()])
    assert tap["features"][0]["properties"]["nguon_dl"] == cau_hinh.mo_ta_nguon()


def test_mo_ta_nguon_khong_lo_thong_tin_ket_noi():
    """Chuoi nay di ra trinh duyet, khong duoc chua dia chi may chu hay tai
    khoan."""
    mo_ta = cau_hinh.mo_ta_nguon().lower()
    for bi_mat in conftest.cac_chuoi_bi_mat():
        assert bi_mat.lower() not in mo_ta
    assert "postgres" not in mo_ta
