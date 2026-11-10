# -*- coding: utf-8 -*-
"""
Chuan hoa lop ranh gioi cap xa cho tinh Khanh Hoa.

Dau vao : data_goc/VN2000_UTM48/Commune.shp
          Bo ranh gioi 3.321 xa, phuong, dac khu tren ca nuoc sau sap nhap 2025.
          He quy chieu VN-2000 / UTM mui 48N, don vi met, ma hoa UTF-8.
Dau ra  : data/ranh_gioi_xa.geojson
          Chi giu cac xa thuoc tinh dang xu ly, da chuyen ve WGS84.

Cac buoc:
  1. Doc shapefile
  2. Loc theo truong Province
  3. Doi ten truong ve quy uoc cua he thong
  4. Khai bao lai CRS la EPSG:3405 roi chuyen sang EPSG:4326
  5. Don gian hoa hinh hoc
  6. Ghi GeoJSON

Chay:  python scripts/02_chuan_hoa_ranh_gioi_xa.py
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

TEP_VAO = mod_tinh.tim_tep_nguon("data_goc/VN2000_UTM48/Commune.shp",
                                "CSDL/VN2000_UTM48/Commune.shp")

# Dung sai don gian hoa, don vi met vi du lieu goc dang he toa do phang.
# 30 m du min cho ty le hien thi cap tinh va cap xa.
DUNG_SAI_MET = 30

DOI_TEN_TRUONG = {
    "maDonViHan": "ma",
    "ten": "ten",
    "Province": "tinh",
    "Partition": "phan_loai",
    "Area": "dien_tich_km2",
    "Population": "dan_so",
}

TRUONG_GIU_LAI = ["ma", "ten", "tinh", "phan_loai", "dien_tich_km2", "dan_so"]


def main():
    tt = mod_tinh.nap()
    ten_tinh = tt["ten_tinh"]
    tep_ra = mod_tinh.duong_dan_ra(tt, "ranh_gioi_xa.geojson")

    print("Doc: {}".format(TEP_VAO))
    gdf = gpd.read_file(TEP_VAO)
    print("  Tong so xa ca nuoc : {}".format(len(gdf)))
    print("  He quy chieu goc    : {}".format(ten_crs(gdf.crs)))

    # --- Buoc 2: loc theo tinh ---
    if "Province" not in gdf.columns:
        raise SystemExit("Du lieu khong co truong Province de loc theo tinh.")

    gdf = gdf[gdf["Province"].astype(str).str.strip() == ten_tinh].copy()
    print("  So xa cua {} : {}".format(ten_tinh, len(gdf)))
    if len(gdf) == 0:
        co = sorted(set(xa.strip() for xa in
                        gpd.read_file(TEP_VAO, columns=["Province"])["Province"].astype(str)))
        print("Khong loc duoc xa nao cho {!r}. Cac ten co trong du lieu:"
              .format(ten_tinh))
        for ten in co:
            print("   ", ten)
        raise SystemExit(1)

    # --- Buoc 3: doi ten truong ---
    gdf = gdf.rename(columns=DOI_TEN_TRUONG)

    # --- Buoc 4: chuyen he quy chieu ---
    # File .prj viet theo chuan ESRI, khai bao VN_2000_UTM_Zone_48N nhung khong
    # kem tham so chuyen doi datum. Khai bao lai thanh EPSG:3405 de pyproj dung
    # dinh nghia VN-2000 chinh thuc, phep chuyen sang WGS84 nho do ro rang hon.
    gdf = gdf.set_crs(3405, allow_override=True)

    # --- Buoc 5: don gian hoa khi con o he met, roi moi chuyen sang do ---
    gdf["geometry"] = gdf.geometry.simplify(DUNG_SAI_MET, preserve_topology=True)
    gdf = gdf.to_crs(4326)

    cac_cot = [c for c in TRUONG_GIU_LAI if c in gdf.columns] + ["geometry"]
    gdf = gdf[cac_cot]

    # Lam sach truong chu: du lieu goc co gia tri thua dau phay o cuoi, vi du
    # "Mien nui," ben canh "Mien nui", khien cung mot phan loai bi dem thanh hai.
    for cot in ("ten", "tinh", "phan_loai"):
        if cot in gdf.columns:
            gdf[cot] = (gdf[cot].astype(str)
                                .str.strip()
                                .str.rstrip(",;.")
                                .str.strip())

    # Area trong du lieu goc da tinh bang km2, Population la so nguoi
    for cot in ("dien_tich_km2", "dan_so"):
        if cot in gdf.columns:
            gdf[cot] = gdf[cot].astype(float).round(2)

    # --- Buoc 6: ghi GeoJSON ---
    gdf.to_file(tep_ra, driver="GeoJSON")
    them_metadata(tep_ra, tt, len(gdf))

    print("Ghi: {}".format(tep_ra))
    print("  So doi tuong : {}".format(len(gdf)))
    print("  Dung luong   : {:.2f} MB".format(os.path.getsize(tep_ra) / 1048576))
    print("  Pham vi      : {}".format([round(float(v), 5) for v in gdf.total_bounds]))
    print("  Tong dien tich: {:.1f} km2".format(gdf["dien_tich_km2"].sum()))
    print("  Tong dan so   : {:,.0f} nguoi".format(gdf["dan_so"].sum()))
    print("Xong.")


def ten_crs(crs):
    try:
        return "{} (EPSG:{})".format(crs.name, crs.to_epsg())
    except Exception:
        return str(crs)


def them_metadata(duong_dan, tt, so_doi_tuong):
    """Chen khoi metadata vao GeoJSON de ghi ro nguon goc du lieu."""
    with open(duong_dan, "r", encoding="utf-8") as f:
        gj = json.load(f)

    gj["name"] = "ranh_gioi_xa"
    gj["metadata"] = {
        "mo_ta": "Ranh gioi cap xa {} sau sap nhap".format(tt["ten_tinh"]),
        "nguon_dl": "Shapefile Commune.shp, thu muc data_goc/VN2000_UTM48",
        "crs_goc": "VN-2000 / UTM zone 48N (EPSG:3405)",
        "hieu_luc": tt["hieu_luc_sap_nhap"],
        "so_doi_tuong": so_doi_tuong,
        "dung_sai_don_gian_met": DUNG_SAI_MET,
    }

    with open(duong_dan, "w", encoding="utf-8") as f:
        json.dump(gj, f, ensure_ascii=False, separators=(",", ":"))


if __name__ == "__main__":
    main()
