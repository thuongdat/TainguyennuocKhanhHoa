# -*- coding: utf-8 -*-
"""
Chuan hoa lop ranh gioi hanh chinh cap tinh sang GeoJSON cho web.

Dau vao : CSDL/Vietnam/VietNam.shp hoac data_goc/Vietnam/VietNam.shp
          Bo ranh gioi 34 tinh sau sap nhap, he quy chieu WGS84, ma hoa UTF-8.
          Loc ra tinh dang xu ly theo truong tenTinh.
Dau ra  : data/ranh_gioi_tinh.geojson

Cac buoc:
  1. Doc shapefile toan quoc bang GeoPandas
  2. Loc dung tinh can xu ly
  3. Doi ten truong ve quy uoc dung trong assets/js/config.js
  4. Chuyen dienTich, danSo tu chuoi sang so
  5. Ep he quy chieu ve EPSG:4326 neu dau vao khac
  6. Don gian hoa hinh hoc de giam dung luong tai ve cho trinh duyet
  7. Ghi GeoJSON

Chay:  python scripts/01_chuan_hoa_ranh_gioi.py
"""

import json
import os
import sys

# Phai sua duong dan PROJ TRUOC khi nap geopandas, xem moi_truong_proj.py
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from moi_truong_proj import sua_duong_dan_proj
sua_duong_dan_proj()

import geopandas as gpd

import tinh as mod_tinh

# Bo ranh gioi 34 tinh, tuy du an ma nam trong CSDL/ hay data_goc/
TEP_VAO = mod_tinh.tim_tep_nguon("CSDL/Vietnam/VietNam.shp",
                                "data_goc/Vietnam/VietNam.shp")

# Dung sai don gian hoa, don vi do thap phan.
# 0,0003 do xap xi 33 m, du min cho ty le hien thi cap tinh.
DUNG_SAI_DON_GIAN = 0.0003

# Anh xa ten truong goc sang ten truong dung trong he thong
DOI_TEN_TRUONG = {
    "maTinh": "ma",
    "tenTinh": "ten",
    "dienTich": "dien_tich_km2",
    "danSo": "dan_so",
    "tptinhtruo": "hop_thanh_tu",
    "trungtamhc": "trung_tam_hc",
    "diaDanh": "dia_danh",
    "phanLoai": "phan_loai",
}

TRUONG_GIU_LAI = ["ma", "ten", "dien_tich_km2", "dan_so",
                  "hop_thanh_tu", "trung_tam_hc", "dia_danh", "phan_loai"]


def main():
    tt = mod_tinh.nap()

    print("Doc: {}".format(TEP_VAO))
    gdf = gpd.read_file(TEP_VAO)
    print("  So tinh trong tep : {}".format(len(gdf)))
    print("  He quy chieu      : {}".format(gdf.crs))

    # --- Buoc 2: loc dung tinh can xu ly ---
    gdf = gdf[gdf["tenTinh"].astype(str).str.strip() == tt["ten_tinh"]].copy()
    if len(gdf) == 0:
        co = sorted(gpd.read_file(TEP_VAO)["tenTinh"].astype(str).str.strip())
        raise SystemExit(
            "Khong tim thay {!r} trong tep.\nCac ten co trong du lieu:\n  {}".format(
                tt["ten_tinh"], "\n  ".join(co)))
    print("  Da loc            : {} ({} doi tuong)".format(tt["ten_tinh"], len(gdf)))

    # --- Buoc 3: doi ten truong ---
    gdf = gdf.rename(columns=DOI_TEN_TRUONG)

    # --- Buoc 4: chuyen chuoi sang so ---
    # Shapefile luu dienTich va danSo o dang ky tu, can ep ve so de web tinh toan
    for cot, kieu in (("dien_tich_km2", float), ("dan_so", int)):
        if cot in gdf.columns:
            gdf[cot] = (gdf[cot].astype(str)
                                 .str.replace(",", "", regex=False)
                                 .str.strip())
            gdf[cot] = gdf[cot].apply(lambda v: ep_so(v, kieu))

    # --- Buoc 5: ep he quy chieu ---
    if gdf.crs is None:
        print("  Canh bao: dau vao khong khai bao CRS, gia dinh EPSG:4326")
        gdf = gdf.set_crs(4326)
    elif gdf.crs.to_epsg() != 4326:
        print("  Chuyen {} -> EPSG:4326".format(gdf.crs))
        gdf = gdf.to_crs(4326)

    # --- Buoc 6: don gian hoa hinh hoc ---
    gdf["geometry"] = gdf.geometry.simplify(DUNG_SAI_DON_GIAN,
                                            preserve_topology=True)

    # Chi giu cac truong can dung, bo Shape_Leng, Shape_Area, OBJECTID
    cac_cot = [c for c in TRUONG_GIU_LAI if c in gdf.columns] + ["geometry"]
    gdf = gdf[cac_cot]

    # Lam sach truong chu
    for cot in ("ten", "hop_thanh_tu", "trung_tam_hc", "dia_danh", "phan_loai"):
        if cot in gdf.columns:
            gdf[cot] = (gdf[cot].astype(str).str.strip()
                                .str.rstrip(",;.").str.strip())

    # --- Buoc 7: ghi GeoJSON kem metadata ---
    tep_ra = mod_tinh.duong_dan_ra(tt, "ranh_gioi_tinh.geojson")
    gdf.to_file(tep_ra, driver="GeoJSON")
    them_metadata(tep_ra, tt, len(gdf))

    print("Ghi: {}".format(tep_ra))
    print("  Dung luong : {:.2f} MB".format(os.path.getsize(tep_ra) / 1048576))
    print("  Pham vi    : {}".format([round(float(v), 5) for v in gdf.total_bounds]))
    print("Xong.")


def ep_so(gia_tri, kieu):
    """Chuyen mot gia tri sang so, tra ve None neu khong chuyen duoc."""
    try:
        return kieu(float(gia_tri))
    except (TypeError, ValueError):
        return None


def them_metadata(duong_dan, tt, so_doi_tuong):
    """Chen khoi metadata vao GeoJSON de ghi ro nguon goc du lieu."""
    with open(duong_dan, "r", encoding="utf-8") as f:
        gj = json.load(f)

    gj["name"] = "ranh_gioi_tinh"
    gj["metadata"] = {
        "mo_ta": "Dia gioi hanh chinh {} sau sap nhap".format(tt["ten_tinh"]),
        "nguon_dl": "Shapefile ranh gioi 34 tinh, thu muc CSDL/Vietnam",
        "hieu_luc": tt["hieu_luc_sap_nhap"],
        "so_doi_tuong": so_doi_tuong,
        "dung_sai_don_gian_do": DUNG_SAI_DON_GIAN,
        "ghi_chu": tt["ban_do"].get("ghi_chu_pham_vi", ""),
    }

    with open(duong_dan, "w", encoding="utf-8") as f:
        json.dump(gj, f, ensure_ascii=False, separators=(",", ":"))


if __name__ == "__main__":
    main()
