# -*- coding: utf-8 -*-
"""
Tao bo "nen dia phuong" tu file geodatabase ban do nen quoc gia.

Dau vao : data_goc/Basemap/BaseMapVietNam.gdb  (khoang 473 MB, 25 lop)
Dau ra  : data/nen/*.geojson                   (cat theo khung bao cua tinh)

Vi sao can: cac dich vu tile quoc te deu ghi dia danh bang tieng Anh va khong
co lop chuyen de ve nuoc. Bo GDB nay la ban do nen quoc gia tieng Viet, co san
song suoi dang vung, mat nuoc, rung, khu bao ton, diem dan cu. Cat theo pham vi
tinh roi chuyen sang GeoJSON thi dung duoc truc tiep tren web ma khong phu
thuoc nha cung cap nao, cung khong can khoa API.

Khong the day nguyen 473 MB len web, nen script lam ba viec:
  1. Loc theo pham vi bao cua tinh ngay khi doc (nhanh hon nhieu so voi doc het)
  2. Chuyen he quy chieu ve EPSG:4326
  3. Don gian hoa hinh hoc theo tung lop, lop nen tho hon lop chi tiet

Chay:  python scripts/04_tao_nen_dia_phuong.py

Them ten lop o cuoi de chi lam lai mot phan:
       python scripts/04_tao_nen_dia_phuong.py DoanTimDuongBo
"""

import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from moi_truong_proj import sua_duong_dan_proj
sua_duong_dan_proj()

import geopandas as gpd
import pyogrio
from shapely.geometry import box

import tinh as mod_tinh

GDB = mod_tinh.tim_tep_nguon("data_goc/Basemap/BaseMapVietNam.gdb",
                            "CSDL/Basemap/BaseMapVietNam.gdb")

# Khung bao de cat nen lay tu truong khung_bao_nen trong tep tham so cua tinh,
# dang lon_min, lat_min, lon_max, lat_max trong he WGS84.

# Danh sach lop can lay.
#   ten_gdb      : ten lop trong geodatabase
#   ten_ra       : ten tep GeoJSON dau ra
#   dung_sai_met : muc do don gian hoa, cang lon cang tho
#   mo_ta        : ghi chu de doc lai sau
# Khong lay lop "Bien": do la mot polygon bien toan quoc gom hang nghin phan,
# loc theo khung bao van tra ve nguyen khoi nen rat cham va rat nang. Mau nen
# bien da duoc xu ly bang mau nen cua khung ban do trong style.css.
CAC_LOP = [
    ("Rung",                 "rung",        120, "Rừng"),
    ("VuonQuocGiaKhuBaoTon", "bao_ton",     100, "Vườn quốc gia, khu bảo tồn"),
    ("MatNuocTinh",          "mat_nuoc",     40, "Mặt nước: hồ, đầm, ao"),
    ("SongSuoiA",            "song_vung",    30, "Sông suối dạng vùng"),
    ("DoanTimDuongBo",       "duong_bo",     40, "Đường bộ: quốc lộ, tỉnh lộ, đường chính"),
    ("DiemDanCu",            "dan_cu",        0, "Điểm dân cư"),
    ("DiaDanhSonVan",        "dia_danh",      0, "Địa danh sơn văn"),
]


def loc_duong_chinh(gdf):
    """Chi giu quoc lo, tinh lo va duong chinh do thi.

    Truong loaiduongbo trong du lieu nen quoc gia: 1 = quoc lo, 2 = tinh lo,
    3 = duong chinh do thi. Ma 4 va 6 la duong huyen, duong xa, chiem hon
    10.000 doi tuong trong pham vi tinh. Giu het thi tep nen nang hon 5 MB va
    o muc zoom cap tinh cung chi thanh mot dam roi.
    """
    return gdf[gdf["loaiduongbo"].isin([1, 2, 3])]


# Ham loc rieng cho tung lop, ap dung ngay sau khi doc
BO_LOC_LOP = {
    "DoanTimDuongBo": loc_duong_chinh,
}


def main():
    tt = mod_tinh.nap()
    pham_vi_wgs84 = tuple(tt["khung_bao_nen"])
    thu_muc_ra = os.path.join(tt["_thu_muc_data"], "nen")

    os.makedirs(thu_muc_ra, exist_ok=True)

    # Xac dinh he quy chieu cua GDB de dung pham vi loc cho dung
    thong_tin = pyogrio.read_info(GDB, layer=CAC_LOP[0][0])
    crs_goc = thong_tin["crs"]
    print("He quy chieu cua GDB: {}".format(crs_goc))

    pham_vi_goc = doi_pham_vi(pham_vi_wgs84, crs_goc)
    print("Pham vi loc (he goc): {}".format(
        tuple(round(v, 2) for v in pham_vi_goc)))
    print("-" * 68)
    print("{:<24}{:>8}{:>12}{:>12}".format("Lop", "Doi tuong", "Dung luong", "Trang thai"))
    print("-" * 68)

    # Cho phep chi lam lai mot vai lop: python scripts/04_... DoanTimDuongBo
    chi_lam = set(sys.argv[1:])
    tong_mb = 0.0
    for ten_gdb, ten_ra, dung_sai, mo_ta in CAC_LOP:
        if chi_lam and ten_gdb not in chi_lam:
            continue
        # Tinh rong hon thi cung mot dung sai se cho ra tep nang hon nhieu.
        # Cho phep tep tham so cua tinh ghi de dung sai cua tung lop.
        dung_sai = tt.get("dung_sai_nen", {}).get(ten_gdb, dung_sai)
        try:
            mb = xu_ly_mot_lop(ten_gdb, ten_ra, dung_sai, mo_ta,
                               pham_vi_goc, thu_muc_ra, tt)
            tong_mb += mb
        except Exception as loi:
            print("{:<24}{:>8}{:>12}{:>12}".format(ten_gdb, "-", "-", "loi"))
            print("    {}".format(loi))

    print("-" * 68)
    print("Tong dung luong nen dia phuong: {:.2f} MB".format(tong_mb))
    print("Ghi tai: {}".format(thu_muc_ra))


def doi_pham_vi(pham_vi_wgs84, crs_dich):
    """Chuyen pham vi bao tu WGS84 sang he quy chieu cua du lieu goc."""
    if crs_dich is None:
        return pham_vi_wgs84
    hop = gpd.GeoSeries([box(*pham_vi_wgs84)], crs=4326)
    try:
        if hop.to_crs(crs_dich).crs.to_epsg() == 4326:
            return pham_vi_wgs84
    except Exception:
        pass
    return tuple(hop.to_crs(crs_dich).total_bounds)


def xu_ly_mot_lop(ten_gdb, ten_ra, dung_sai_met, mo_ta, pham_vi_goc,
                  thu_muc_ra, tt):
    """Doc mot lop trong pham vi da cho, don gian hoa va ghi ra GeoJSON."""
    gdf = gpd.read_file(GDB, layer=ten_gdb, bbox=pham_vi_goc)

    if ten_gdb in BO_LOC_LOP:
        gdf = BO_LOC_LOP[ten_gdb](gdf)

    if len(gdf) == 0:
        print("{:<24}{:>8}{:>12}{:>12}".format(ten_gdb, 0, "-", "bo qua"))
        return 0.0

    # Loc theo khung bao chi loai bo doi tuong nam hoan toan ben ngoai. Mot doi
    # tuong lon nhu vung rung hay con song dai van duoc giu nguyen toan bo, keo
    # theo ca phan nam ngoai tinh. Phai cat that de tep dau ra khong phinh to.
    if gdf.geom_type.isin(["Polygon", "MultiPolygon"]).any():
        khung = gpd.GeoDataFrame(geometry=[box(*pham_vi_goc)], crs=gdf.crs)
        gdf = gpd.clip(gdf, khung)

    # Don gian hoa khi con o he toa do phang, don vi met
    if dung_sai_met > 0 and gdf.crs is not None and not gdf.crs.is_geographic:
        gdf["geometry"] = gdf.geometry.simplify(dung_sai_met, preserve_topology=True)

    if gdf.crs is None:
        gdf = gdf.set_crs(4326)
    elif gdf.crs.to_epsg() != 4326:
        gdf = gdf.to_crs(4326)

    # Neu du lieu goc von da o he do thi don gian hoa sau khi chuyen
    if dung_sai_met > 0 and (gdf.crs is None or gdf.crs.is_geographic):
        gdf["geometry"] = gdf.geometry.simplify(dung_sai_met / 111000.0,
                                                preserve_topology=True)

    gdf = gdf[~gdf.geometry.is_empty & gdf.geometry.notna()]
    gdf = giu_truong_can_thiet(gdf)

    duong_dan = os.path.join(thu_muc_ra, ten_ra + ".geojson")
    gdf.to_file(duong_dan, driver="GeoJSON")
    them_metadata(duong_dan, ten_gdb, mo_ta, len(gdf), dung_sai_met, tt)

    mb = os.path.getsize(duong_dan) / 1048576
    print("{:<24}{:>8}{:>11.2f}M{:>12}".format(ten_gdb, len(gdf), mb, "xong"))
    return mb


def giu_truong_can_thiet(gdf):
    """Bo cac truong he thong cua ArcGIS, chi giu truong co ten va phan loai."""
    bo_di = {"Shape_Length", "Shape_Area", "OBJECTID", "GlobalID", "SHAPE_Length",
             "SHAPE_Area", "Shape_Leng"}
    cot = [c for c in gdf.columns
           if c != "geometry" and c not in bo_di and not c.lower().startswith("objectid")]
    # Gioi han so truong de tep khong phinh to
    return gdf[cot[:8] + ["geometry"]]


def them_metadata(duong_dan, ten_gdb, mo_ta, so_doi_tuong, dung_sai, tt):
    with open(duong_dan, "r", encoding="utf-8") as f:
        gj = json.load(f)
    gj["metadata"] = {
        "mo_ta": mo_ta,
        "lop_goc": ten_gdb,
        "nguon_dl": "BaseMapVietNam.gdb - bản đồ nền quốc gia",
        "pham_vi": "Phần đất liền {}".format(tt["ten_tinh"]),
        "so_doi_tuong": so_doi_tuong,
        "dung_sai_don_gian_met": dung_sai,
    }
    with open(duong_dan, "w", encoding="utf-8") as f:
        json.dump(gj, f, ensure_ascii=False, separators=(",", ":"))


if __name__ == "__main__":
    main()
