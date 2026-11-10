# -*- coding: utf-8 -*-
r"""
Xuat lop "Tram, diem quan trac" THAT cho ban do chinh.

Dau vao : 1. CSDL QTQG (qua backend/nguon_qtqg.py): tram nuoc mat va tram thuy van.
             Lo khoan nuoc duoi dat KHONG lay o day, da co lop quan_trac_ndd.
          2. CSDL/dulieu_thuc/BD_CAC CAP SONG_Viet Nam/Tram KTVN.TAB, Tram TVVN.TAB
             Mang tram khi tuong va thuy van quoc gia, cat theo ranh gioi tinh.
Dau ra  : data/quan_trac.geojson (EPSG:4326)

Lop nay chi co VI TRI va THONG TIN TRAM, khong co so do. So do that xem o tab
Quan trac. Moi tram mang truong nguon_so_lieu va tinh_trang de nguoi dung biet
tram do den tu dau va con quan trac hay da ngung.

Tram QTQG va tram KTTV o cung vi tri (< KHOANG_CACH_TRUNG_M) va cung loai la mot
tram: giu ban ghi QTQG, ghi chu tram KTTV trung. Cac cap trung duoc IN RA.

Chay:
    set CHE_DO=that
    D:\Anaconda_Data\envs\tainguyennuoc\python.exe scripts/10_xuat_tram_quan_trac.py
"""

import importlib.util
import json
import os
import sys

HIEN_TAI = os.path.dirname(os.path.abspath(__file__))
GOC_DU_AN = os.path.dirname(HIEN_TAI)
GOC_BACKEND = os.path.join(GOC_DU_AN, "backend")

sys.path.insert(0, HIEN_TAI)
from moi_truong_proj import sua_duong_dan_proj
sua_duong_dan_proj()

import geopandas as gpd
import pandas as pd
import shapely

import tinh as mod_tinh

KHOANG_CACH_TRUNG_M = 2000


def _nap_script_05():
    """Dung lai bang ma TCVN3 va ham gan luu vuc cua script 05, khong chep lai."""
    duong = os.path.join(HIEN_TAI, "05_chuan_hoa_chuyen_de.py")
    spec = importlib.util.spec_from_file_location("chuan_hoa_chuyen_de", duong)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def _nap_backend():
    if not os.environ.get("CHE_DO"):
        os.environ["CHE_DO"] = "that"
    sys.path.insert(0, GOC_BACKEND)
    import cau_hinh
    if not cau_hinh.la_nguon_that():
        raise SystemExit("Script nay can nguon that. Dat CHE_DO=that roi chay lai.")
    thieu = cau_hinh.thieu_thong_tin_ket_noi()
    if thieu:
        raise SystemExit("Thieu thong tin ket noi: {}. Dien vao backend/.env."
                         .format(", ".join(thieu)))
    import nguon_qtqg
    import khong_gian
    return nguon_qtqg, khong_gian


def doc_ngay(chuoi):
    """'01/01/76' hoac '1990-02-03 00:00:00' -> 'dd/mm/yyyy', hoac None."""
    if chuoi is None or (isinstance(chuoi, float) and pd.isna(chuoi)):
        return None
    s = str(chuoi).strip()
    if not s or s in ("-", "x"):
        return None
    for dinh_dang in ("%d/%m/%y", "%d/%m/%Y", "%Y-%m-%d %H:%M:%S", "%Y-%m-%d"):
        try:
            d = pd.to_datetime(s, format=dinh_dang)
            if d.year > 2030:          # %y hieu 76 thanh 2076 thi tru 100
                d = d.replace(year=d.year - 100)
            return d.strftime("%d/%m/%Y")
        except (ValueError, TypeError):
            continue
    return None


def tram_qtqg(m05, nguon_qtqg, khong_gian):
    print("\n[1/3] Tram QTQG (nuoc mat, thuy van)")
    cac_tram = nguon_qtqg.lay_danh_sach_tram()
    tap = khong_gian.tap_feature(cac_tram, loc_theo_tinh=True)
    cac = []
    for f in tap["features"]:
        p = f["properties"]
        if p.get("loai_tram") == "Nước dưới đất":
            continue
        cac.append(f)
    print("   Tram nuoc mat va thuy van trong tinh: {}".format(len(cac)))

    out = []
    for f in cac:
        p = f["properties"]
        x, y = f["geometry"]["coordinates"]
        out.append({
            "ma": p.get("ma"), "ten": p.get("ten"),
            "loai_tram": p.get("loai_tram"),
            "song_ho": p.get("song_ho"), "thong_so": p.get("thong_so"),
            "don_vi_quan_ly": p.get("don_vi_quan_ly"),
            "mang_quan_trac": p.get("mang_quan_trac"),
            "ngay_bat_dau": p.get("ngay_bat_dau"),
            "tinh_trang": "Có trong danh mục trạm QTQG",
            "nguon_so_lieu": "QTQG",
            "nguon_dl": "Cơ sở dữ liệu phần mềm Quan trắc Quốc gia (QTQG)",
            "_x": x, "_y": y,
        })
    return out


def tram_kttv(m05, tt, ranh):
    print("\n[2/3] Mang tram KTTV quoc gia (MapInfo)")
    thu_muc = "CSDL/dulieu_thuc/BD_CAC CAP SONG_Viet Nam/"
    out = []

    # Cot do tu bang xlsx di kem va doi chieu voi gia tri tho (cot D cua tram
    # khi tuong va cot D cua tram thuy van bo trong nen moi cot lech mot so voi
    # ten ban dau). (tep, loai, bat dau, ket thuc, song, xa, huyen, tinh)
    cau_hinh = [
        ("Tram KTVN.TAB", "Khí tượng", "P", "Q", None, "E", "F", "G"),
        ("Tram TVVN.TAB", "Thủy văn", "S", "T", "F", "I", "J", "K"),
    ]
    for ten_tep, loai, cot_bd, cot_kt, cot_song, cot_xa, cot_huyen, cot_tinh in cau_hinh:
        duong = mod_tinh.tim_tep_nguon(thu_muc + ten_tep)
        g = gpd.read_file(duong, on_invalid="ignore")
        g = g[g.geometry.notna() & ~g.geometry.is_empty].copy()
        g = g.set_crs(4326, allow_override=True)
        # ranh gioi toan tinh ke ca Truong Sa; dem 0.02 do vi toa do tram chi chinh den phut
        trong = g[g.within(ranh.buffer(0.02))]
        print("   {}: {} tram, {} trong tinh".format(ten_tep, len(g), len(trong)))
        for _, r in trong.iterrows():
            ten = m05.tcvn3_sang_unicode(r["Tentram"], True)
            bd = doc_ngay(r.get(cot_bd))
            kt = doc_ngay(r.get(cot_kt))
            if kt:
                tinh_trang = "Đã ngừng quan trắc từ {}".format(kt)
            else:
                tinh_trang = "Danh mục KTTV chưa ghi ngày kết thúc"
            out.append({
                "ma": None, "ten": ten, "loai_tram": loai,
                "song_ho": (m05.tcvn3_sang_unicode(r.get(cot_song), True)
                            if cot_song else None),
                "thong_so": "Khí tượng, mưa" if loai == "Khí tượng" else "Mực nước, lưu lượng",
                "vi_tri_hc": ", ".join(x for x in [
                    m05.tcvn3_sang_unicode(r.get(cot_xa)),
                    m05.tcvn3_sang_unicode(r.get(cot_huyen)),
                    m05.tcvn3_sang_unicode(r.get(cot_tinh))] if x),
                "mang_quan_trac": "Mạng trạm khí tượng thủy văn quốc gia",
                "ngay_bat_dau": bd, "ngay_ket_thuc": kt,
                "tinh_trang": tinh_trang,
                "nguon_so_lieu": "Danh mục trạm KTTV quốc gia",
                "nguon_dl": "Bộ dữ liệu mạng lưới trạm khí tượng thủy văn quốc gia (MapInfo)",
                "_x": r.geometry.x, "_y": r.geometry.y,
            })
    return out


def _bo_dau(s):
    import unicodedata
    s = unicodedata.normalize("NFD", str(s or "").replace("đ", "d").replace("Đ", "D"))
    return "".join(c for c in s if unicodedata.category(c) != "Mn").lower().strip()


KHOANG_CACH_CUNG_TEN_M = 10000


def gop_va_loai_trung(qtqg, kttv, epsg):
    """Tram KTTV cung loai voi mot tram QTQG thi coi la mot tram neu:
    cach nhau duoi KHOANG_CACH_TRUNG_M, hoac cung ten (bo dau) va cach nhau duoi
    KHOANG_CACH_CUNG_TEN_M. Moi cap duoc in kem khoang cach de nguoi dung duyet."""
    print("\n[3/3] Loai trung")
    ds_q = gpd.GeoSeries([shapely.Point(t["_x"], t["_y"]) for t in qtqg], crs=4326).to_crs(epsg)
    giu = []
    for t in kttv:
        diem = gpd.GeoSeries([shapely.Point(t["_x"], t["_y"])], crs=4326).to_crs(epsg).iloc[0]
        trung = None
        for i, q in enumerate(qtqg):
            if not ((q["loai_tram"] or "").startswith("Thủy văn") and t["loai_tram"] == "Thủy văn"):
                continue
            kc = ds_q.iloc[i].distance(diem)
            cung_ten = _bo_dau(q["ten"]) == _bo_dau(t["ten"])
            if kc < KHOANG_CACH_TRUNG_M or (cung_ten and kc < KHOANG_CACH_CUNG_TEN_M):
                trung = q
                print("   TRUNG: KTTV '{}' = QTQG '{}' ({}), cach {:.0f} m, giu ban ghi QTQG".format(
                    t["ten"], q["ten"], q["ma"], kc))
                break
        if trung:
            trung["ghi_chu"] = "Trùng trạm KTTV quốc gia '{}' ({})".format(
                t["ten"], t["tinh_trang"])
        else:
            giu.append(t)
    return qtqg + giu


def main():
    tt = mod_tinh.nap()
    m05 = _nap_script_05()
    nguon_qtqg, khong_gian = _nap_backend()
    epsg = tt["epsg_chuyen_de"]

    ranh = gpd.read_file(mod_tinh.tim_tep_nguon("CSDL/dulieu_thuc/KhanhHoa.shp")).to_crs(4326)
    ranh = shapely.make_valid(ranh.geometry.union_all())

    qtqg = tram_qtqg(m05, nguon_qtqg, khong_gian)
    kttv = tram_kttv(m05, tt, ranh)
    tat_ca = gop_va_loai_trung(qtqg, kttv, epsg)
    if not tat_ca:
        raise SystemExit("Khong co tram nao, KHONG ghi de tep cu.")

    # ma cho tram KTTV: KTTV01.. theo thu tu
    dem = 0
    for t in tat_ca:
        if not t["ma"]:
            dem += 1
            t["ma"] = "KTTV{:02d}".format(dem)

    gdf = gpd.GeoDataFrame(
        pd.DataFrame(tat_ca),
        geometry=[shapely.Point(t["_x"], t["_y"]) for t in tat_ca], crs=4326
    ).drop(columns=["_x", "_y"])

    # gan luu vuc theo luu vuc da sinh o script 05
    lv = gpd.read_file(os.path.join(tt["_thu_muc_data"], "luu_vuc.geojson"))
    ma, ten, thieu = m05.gan_luu_vuc(gdf.to_crs(epsg), lv, epsg)
    gdf["ma_luu_vuc"] = ma.values
    gdf["ten_luu_vuc"] = ten.values
    if thieu:
        print("   {} tram khong gan duoc luu vuc".format(thieu))

    duong = mod_tinh.duong_dan_ra(tt, "quan_trac.geojson")
    gdf.to_file(duong, driver="GeoJSON", engine="pyogrio", COORDINATE_PRECISION=6)

    print("\nGhi {} ({} tram)".format(duong, len(gdf)))
    print(gdf.groupby(["loai_tram", "nguon_so_lieu"]).size().to_string())
    print()
    print(gdf[["ma", "ten", "loai_tram", "tinh_trang", "ten_luu_vuc"]].to_string(index=False))


if __name__ == "__main__":
    main()
