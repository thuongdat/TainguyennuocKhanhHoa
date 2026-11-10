"""Dung GeoJSON cho cac tram quan trac va loc theo pham vi tinh.

Ten truong thuoc tinh dat GIONG data/quan_trac.geojson, nho vay khai bao lop
CAU_HINH.lop.quan_trac trong assets/js/config.js dung lai duoc nguyen ven cho
du lieu QTQG: nhan truong, don vi, cot bang va chu giai khong phai viet lai.

He quy chieu dau ra luon la EPSG:4326, giong moi tep trong data/.
"""

import csv
import json
import os

import cau_hinh

# Truong thuoc tinh cua moi tram, dat theo data/quan_trac.geojson
TRUONG_THUOC_TINH = ["ma", "ten", "loai_tram", "song_ho", "thong_so",
                     "ten_luu_vuc", "don_vi_quan_ly", "nguon_dl",
                     "ma_dia_phuong", "nguon",
                     # Rieng cua lo khoan nuoc duoi dat. Tram nuoc mat de
                     # khuyet cac truong nay, giao dien bo qua o khuyet.
                     "tang_chua_nuoc", "cao_do_mieng_lk_m", "vi_tri_hc",
                     "mang_quan_trac", "thiet_bi_do", "ngay_bat_dau"]

_tham_so_tinh = None
_anh_xa_tram = None


def tham_so_tinh():
    """Doc tinh.json mot lan. Day la nguon su that duy nhat ve pham vi tinh,
    dung chung giua Python va trinh duyet."""
    global _tham_so_tinh
    if _tham_so_tinh is None:
        with open(cau_hinh.TEP_THAM_SO_TINH, encoding="utf-8") as f:
            _tham_so_tinh = json.load(f)
    return _tham_so_tinh


def khung_bao():
    """Khung bao cua tinh: (kinh_do_min, vi_do_min, kinh_do_max, vi_do_max)."""
    kb = tham_so_tinh().get("khung_bao_nen")
    if not kb or len(kb) != 4:
        return None
    return tuple(float(x) for x in kb)


def trong_pham_vi_tinh(kinh_do, vi_do):
    """CSDL QTQG la cua ca nuoc, phai loc ve pham vi tinh truoc khi ve."""
    kb = khung_bao()
    if kb is None:
        return True
    if kinh_do is None or vi_do is None:
        return False
    return kb[0] <= kinh_do <= kb[2] and kb[1] <= vi_do <= kb[3]


def anh_xa_tram():
    """Bang ghi tay: ma tram QTQG -> ma trong data/quan_trac.geojson.

    Khong tu dong so khop theo ten. Ham do_giong() trong
    scripts/03_lay_realtime.py hien chi ghep duoc 49 tren 98 diem, do chinh
    xac chua du de chay ngam ma khong ai soat.
    """
    global _anh_xa_tram
    if _anh_xa_tram is not None:
        return _anh_xa_tram

    _anh_xa_tram = {}
    if not os.path.isfile(cau_hinh.TEP_ANH_XA_TRAM):
        return _anh_xa_tram

    with open(cau_hinh.TEP_ANH_XA_TRAM, encoding="utf-8-sig", newline="") as f:
        for dong in csv.DictReader(f):
            ma_qtqg = (dong.get("ma_qtqg") or "").strip()
            ma_dp = (dong.get("ma_dia_phuong") or "").strip()
            if ma_qtqg and ma_dp:
                _anh_xa_tram[ma_qtqg] = ma_dp
    return _anh_xa_tram


def ten_tinh_trong_qtqg():
    """Ten tinh nhu CSDL QTQG dang ghi, doc tu tinh.json."""
    return tham_so_tinh().get("ten_tinh_trong_qtqg") or []


def thuoc_tinh_nay(ten_tinh):
    """Tram co thuoc don vi hanh chinh cua tinh hay khong.

    Khung bao la hinh chu nhat nen trum ca mot phan cac tinh lan can. Loc theo
    toa do thoi se keo vao tram cua tinh khac. Phep loc nay dua vao chinh cot
    tinh cua QTQG.

    QTQG ghi ten khong thong nhat giua cac bang: cung mot tinh, bang nay ghi
    "<ten tinh>" con bang kia ghi "Tinh <ten tinh>". Vi vay so khop theo chuoi
    con, sau khi bo dau.
    """
    import chuan_hoa
    cac_ten = ten_tinh_trong_qtqg()
    if not cac_ten:
        return True            # chua khai bao thi khong loc
    if not ten_tinh:
        return False
    chu = chuan_hoa.bo_dau(ten_tinh)
    return any(chuan_hoa.bo_dau(t) in chu for t in cac_ten)


def hop_danh_sach_tram(tram_dia_phuong, tram_qtqg):
    """Hop lop quan trac dia phuong voi cac tram cua QTQG.

    Vi sao can hop: trong pham vi mot tinh, CSDL QTQG thuong chi co vai tram
    co so do. Neu chi ve tram cua QTQG thi ban do gan nhu trong. Nguoc lai,
    neu chi ve lop dia phuong thi mat phan so lieu theo thoi gian. Hop lai, moi
    tram mang truong "nguon" de nguoi dung phan biet duoc tram nao co so lieu
    cap nhat.

    Ham nay chi duoc goi khi HOP_TRAM_DIA_PHUONG bat. Du an nay TAT, vi lop
    quan trac dia phuong con la du lieu mo phong; xem cau_hinh.py.

    Tram QTQG da duoc anh xa sang mot ma dia phuong (qua anh_xa_tram.csv) thi
    GOP vao tram dia phuong do chu khong ve them mot diem chong len.
    """
    anh_xa = anh_xa_tram()
    theo_ma_dia_phuong = {}
    for t in tram_dia_phuong:
        if t.get("ma"):
            theo_ma_dia_phuong[t["ma"]] = dict(t)

    con_lai = []
    for t in tram_qtqg:
        ma_qtqg = t.get("ma")
        ma_dp = anh_xa.get(ma_qtqg)

        if ma_dp and ma_dp in theo_ma_dia_phuong:
            # Tram dia phuong nay chinh la tram QTQG do: danh dau de giao dien
            # biet no co so lieu theo thoi gian, khong ve them diem moi.
            goc = theo_ma_dia_phuong[ma_dp]
            goc["nguon"] = "QTQG"
            goc["ma_qtqg"] = ma_qtqg
            continue

        moi = dict(t)
        moi["ma_dia_phuong"] = ma_dp
        con_lai.append(moi)

    return list(theo_ma_dia_phuong.values()) + con_lai


def mot_feature(tram):
    """Doi mot ban ghi tram thanh Feature GeoJSON, hoac None neu thieu toa do."""
    kinh_do = tram.get("kinh_do")
    vi_do = tram.get("vi_do")
    if kinh_do is None or vi_do is None:
        return None

    thuoc_tinh = {}
    for ten in TRUONG_THUOC_TINH:
        thuoc_tinh[ten] = tram.get(ten)

    if not thuoc_tinh.get("ma_dia_phuong"):
        thuoc_tinh["ma_dia_phuong"] = anh_xa_tram().get(tram.get("ma"))
    if not thuoc_tinh.get("nguon_dl"):
        thuoc_tinh["nguon_dl"] = cau_hinh.mo_ta_nguon()

    return {
        "type": "Feature",
        "properties": thuoc_tinh,
        "geometry": {
            "type": "Point",
            "coordinates": [round(float(kinh_do), 6), round(float(vi_do), 6)],
        },
    }


def tap_feature(cac_tram, loc_theo_tinh=True):
    """Dung FeatureCollection tu danh sach tram da chuan hoa.

    Tra ve ca thong ke de endpoint bao duoc da bo bao nhieu tram va vi sao,
    thay vi im lang lam mat du lieu.
    """
    cac_feature = []
    bo_ngoai_tinh = 0
    bo_thieu_toa_do = 0

    for tram in cac_tram:
        kinh_do = tram.get("kinh_do")
        vi_do = tram.get("vi_do")

        if kinh_do is None or vi_do is None:
            bo_thieu_toa_do += 1
            continue
        if loc_theo_tinh and not trong_pham_vi_tinh(kinh_do, vi_do):
            bo_ngoai_tinh += 1
            continue

        f = mot_feature(tram)
        if f:
            cac_feature.append(f)

    return {
        "type": "FeatureCollection",
        "name": "quan_trac_qtqg",
        "crs": {"type": "name",
                "properties": {"name": "urn:ogc:def:crs:OGC:1.3:CRS84"}},
        "nguon_dl": cau_hinh.mo_ta_nguon(),
        "che_do": cau_hinh.CHE_DO,
        "thong_ke": {
            "so_tram": len(cac_feature),
            "bo_ngoai_tinh": bo_ngoai_tinh,
            "bo_thieu_toa_do": bo_thieu_toa_do,
        },
        "features": cac_feature,
    }
