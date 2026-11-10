# -*- coding: utf-8 -*-
r"""
Chuan hoa du lieu kiem ke THAT thanh cac lop GeoJSON chuyen de.

Dau vao : CSDL/dulieu_thuc/Song_suoi_KH_polyline.shp   (song, suoi)
          CSDL/dulieu_thuc/TH_Khaithac_KH_point.shp    (cong trinh khai thac)
          CSDL/dulieu_thuc/TH_Xathai_KH_point.shp      (diem xa thai)
          CSDL/dulieu_thuc/KhanhHoa.shp                (ranh gioi tinh, de cat)
          CSDL/dulieu_thuc/BD_CAC CAP SONG_Viet Nam/LVSC_TQuoc.TAB (luu vuc)
Dau ra  : data/luu_vuc.geojson, song_suoi.geojson, khai_thac.geojson,
          ao_ho.geojson, xa_thai.geojson   (EPSG:4326)

          Cong trinh khai thac co loai_hinh bat dau bang "Ho" (ho chua, ho chua
          thuy loi, ho thuy dien) duoc TACH sang ao_ho.geojson; dap dang, tram
          bom, tram cap nuoc, cong o lai khai_thac.geojson. Hai lop dung chung
          truong, ma KT giu nguyen de truy nguoc ve bang kiem ke.

BA DIEU CAN BIET VE NGUON

1. Chu tieng Viet trong cac tep nay la ma TCVN3 (ABC) bi doc nhu cp1252,
   vi du "S«ng C¸i Nha Trang" la "Song Cai Nha Trang". Script doi ve Unicode
   bang bang ma TCVN3 trong tcvn3_sang_unicode().

2. He toa do: tep .prj khai bao "_MI_0" (Transverse Mercator, kinh tuyen truc
   108.25, k=0.9999) nen GeoPandas khong nhan ra. Do la VN-2000 mui 3 do
   (EPSG:9217, lay tu tinh.json). Script gan bang set_crs(allow_override=True).

3. LV_C1..C5_Tquoc cua bo MapInfo quoc gia co bang thuoc tinh LECH COT (ten
   song = -9999), khong dung duoc. Chi LVSC_TQuoc co ten luu vuc dung.

Hinh hoc rong/loi, doi tuong ngoai khung bao nen deu bi BO KHOI TEP va BAO SO
LUONG ra man hinh, khong im lang bo di. Khong doc duoc lop nao thi dung han,
khong ghi de tep cu.

Cuoi script dong bo ma_luu_vuc cua cac lop con mo phong (ho_chua, mat_nuoc,
quan_trac, doan_song) theo luu vuc moi, vi ma LV01.. cu khong con y nghia.

Chay:  python scripts/05_chuan_hoa_chuyen_de.py
"""

import json
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from moi_truong_proj import sua_duong_dan_proj
sua_duong_dan_proj()

import geopandas as gpd
import pandas as pd
import shapely

import tinh as mod_tinh

NGUON_DL = "Du lieu kiem ke thuc - bo du lieu so tinh (CSDL/dulieu_thuc)"
DIEN_TICH_TOI_THIEU_KM2 = 5.0      # manh luu vuc nho hon thi bo
KHOANG_CACH_TOI_DA_M = 10000       # diem ngoai moi luu vuc: gan vao luu vuc gan nhat trong ban kinh nay

# ---------------------------------------------------------------- TCVN3 -> Unicode

_BANG_TCVN3 = {}


def _dat(ma_dau, chuoi):
    """Gan lien tiep cac ma bat dau tu ma_dau cho cac ky tu trong chuoi."""
    for i, ch in enumerate(chuoi):
        _BANG_TCVN3[ma_dau + i] = ch


_dat(0xA1, "ĂÂÊÔƠƯĐ")
_dat(0xA8, "ăâêôơưđ")
_dat(0xB5, "àảãáạ")
_dat(0xBB, "ằẳẵắ")
_dat(0xC6, "ặ")
_dat(0xC7, "ầẩẫấậ")
_dat(0xCC, "è")
_dat(0xCE, "ẻẽéẹ")
_dat(0xD2, "ềểễếệ")
_dat(0xD7, "ìỉ")
_dat(0xDC, "ĩíị")
_dat(0xDF, "ò")
_dat(0xE1, "ỏõóọ")
_dat(0xE5, "ồổỗốộ")
_dat(0xEA, "ờởỡớợ")
_dat(0xEF, "ù")
_dat(0xF1, "ủũúụ")
_dat(0xF5, "ừửữứự")
_dat(0xFA, "ỳỷỹýỵ")

# Chu thuong co dau o dau tu: TCVN3 viet hoa co dau bang ma chu thuong, nen
# "Ích" ra "ích". Chi sua cho cac truong ten rieng, xem viet_hoa_dau_tu().
_CHU_THUONG_CO_DAU = set(_BANG_TCVN3[m] for m in _BANG_TCVN3 if m >= 0xB5)


def _ve_byte(ch):
    """Ky tu da bi doc nhu cp1252/latin1 -> gia tri byte goc, hoac None."""
    try:
        return ch.encode("cp1252")[0]
    except UnicodeEncodeError:
        return ord(ch) if ord(ch) < 256 else None


def tcvn3_sang_unicode(s, viet_hoa_dau_tu=False):
    """Doi mot chuoi TCVN3 (dang bi doc sai) ve Unicode.

    Chuoi da co ky tu Unicode tieng Viet that (ma > 0xFF, ngoai cac ky tu cp1252
    dac biet) thi giu nguyen, de chay lai tren du lieu da dung khong hong.
    """
    if s is None or (isinstance(s, float) and pd.isna(s)):
        return None
    s = str(s)
    if all(ord(c) < 128 for c in s):
        return s
    if any(_ve_byte(c) is None for c in s):
        return s                      # da la Unicode that
    ra = []
    for c in s:
        b = _ve_byte(c)
        ra.append(_BANG_TCVN3.get(b, c) if b >= 0x80 else c)
    ra = "".join(ra)
    if viet_hoa_dau_tu:
        ra = re.sub(r"(^|[\s(])([^\W\d_])",
                    lambda m: m.group(1) + (m.group(2).upper()
                                            if m.group(2) in _CHU_THUONG_CO_DAU
                                            else m.group(2)), ra)
    return ra.strip() or None


_LATIN1_TIENG_VIET = set("ÀÁÂÃÈÉÊÌÍÒÓÔÕÙÚÝàáâãèéêìíòóôõùúý")


def con_ky_tu_la(chuoi):
    """Cac ky tu Latin-1 con sot lai ma KHONG phai chu tieng Viet (bang ma thieu)."""
    return sorted(set(c for c in chuoi
                      if 0x80 <= ord(c) <= 0xFF and c not in _LATIN1_TIENG_VIET))


# ---------------------------------------------------------------- doc nguon

def doc(duong_dan, epsg_nguon=None):
    """Doc mot tep khong gian; bo hinh hoc rong/loi va bao so luong."""
    g = gpd.read_file(duong_dan, on_invalid="ignore")
    n0 = len(g)
    if epsg_nguon is not None:
        g = g.set_crs(epsg_nguon, allow_override=True)
    hong = g.geometry.isna() | g.geometry.is_empty
    if hong.any():
        print("   BO {} / {} doi tuong hinh hoc rong hoac loi".format(int(hong.sum()), n0))
        g = g[~hong].copy()
    return g


def so_hoc(chuoi):
    """Chuoi -> so thuc. Tra ve None neu khong doc duoc (khong doan)."""
    if chuoi is None or (isinstance(chuoi, float) and pd.isna(chuoi)):
        return None
    if isinstance(chuoi, (int, float)):
        return float(chuoi)
    s = str(chuoi).strip().replace(",", ".")
    if not s:
        return None
    try:
        return float(s)
    except ValueError:
        return None


def la_cot_chu(cot):
    """Cot chu (kieu object hoac str tuy phien ban pandas), khong tinh geometry."""
    return pd.api.types.is_string_dtype(cot) or cot.dtype == object


def dong_nhat_chu(s):
    """'Dap Dang' va 'Dap dang' la mot loai: chu dau hoa, con lai thuong."""
    if s is None or (isinstance(s, float) and pd.isna(s)) or not s:
        return s
    return s[0].upper() + s[1:].lower()


def lam_tron(x, n=2):
    return None if x is None or pd.isna(x) else round(float(x), n)


# ---------------------------------------------------------------- luu vuc

def chuan_hoa_ten_luu_vuc(ten):
    ten = re.sub(r"^S\.\s*", "Sông ", ten)
    ten = re.sub(r"^Sg\.\s*", "Sông ", ten)
    dau = ten.split(" ")[0]
    if dau in ("Sông", "Suối", "Lạch"):
        ten = dau.lower() + ten[len(dau):]
    return "Lưu vực " + ten


def tao_luu_vuc(tt, ranh_tinh):
    print("\n[1/4] Luu vuc (LVSC_TQuoc, cat theo ranh gioi tinh)")
    duong = mod_tinh.tim_tep_nguon("CSDL/dulieu_thuc/BD_CAC CAP SONG_Viet Nam/LVSC_TQuoc.TAB")
    g = doc(duong)
    g = g[g.geom_type.isin(["Polygon", "MultiPolygon"])].copy()
    epsg = tt["epsg_chuyen_de"]
    g = g.to_crs(epsg)
    g["geometry"] = shapely.make_valid(g.geometry.values)
    g = g[g.intersects(ranh_tinh)].copy()

    g["ten_goc"] = g["TENSONG"].apply(lambda s: tcvn3_sang_unicode(s, True))
    g["dien_tich_km2"] = g.geometry.area / 1e6
    cat = g.geometry.intersection(ranh_tinh)
    g["geometry"] = cat
    g["dien_tich_trong_tinh_km2"] = g.geometry.area / 1e6

    nho = g["dien_tich_trong_tinh_km2"] < DIEN_TICH_TOI_THIEU_KM2
    if nho.any():
        print("   BO {} manh luu vuc < {} km2 trong tinh: {}".format(
            int(nho.sum()), DIEN_TICH_TOI_THIEU_KM2, list(g.loc[nho, "ten_goc"])))
        g = g[~nho]

    # ma LV01.. theo dien tich trong tinh giam dan
    g = g.sort_values("dien_tich_trong_tinh_km2", ascending=False).reset_index(drop=True)
    g["ma"] = ["LV{:02d}".format(i + 1) for i in range(len(g))]
    g["ten"] = g["ten_goc"].apply(chuan_hoa_ten_luu_vuc)
    g["nguon_dl"] = NGUON_DL

    cot = ["ma", "ten", "dien_tich_km2", "dien_tich_trong_tinh_km2", "nguon_dl"]
    ra = g[cot + ["geometry"]].copy()
    for c in ("dien_tich_km2", "dien_tich_trong_tinh_km2"):
        ra[c] = ra[c].round(1)
    print("   Giu {} luu vuc:".format(len(ra)))
    for _, r in ra.iterrows():
        print("     {}  {:<38} toan LV {:>9.1f} km2, trong tinh {:>8.1f} km2".format(
            r["ma"], r["ten"], r["dien_tich_km2"], r["dien_tich_trong_tinh_km2"]))
    return ra


def gan_luu_vuc(gdf, luu_vuc, epsg):
    """Gan ma_luu_vuc/ten_luu_vuc cho gdf bang diem dai dien.

    Diem nam trong luu vuc nao thi lay luu vuc do (luu vuc chong lan thi lay
    luu vuc nho hon). Diem ngoai moi luu vuc (ven bien) lay luu vuc gan nhat
    trong KHOANG_CACH_TOI_DA_M. Tra ve (ma, ten, so_diem_khong_gan_duoc).
    """
    lv = luu_vuc.to_crs(epsg)[["ma", "ten", "geometry"]].copy()
    lv["_dt"] = lv.geometry.area

    if gdf.geom_type.iloc[0] in ("LineString", "MultiLineString"):
        dai_dien = gdf.geometry.apply(lambda x: x.interpolate(0.5, normalized=True))
    elif gdf.geom_type.iloc[0] in ("Polygon", "MultiPolygon"):
        dai_dien = gdf.geometry.representative_point()
    else:
        dai_dien = gdf.geometry
    diem = gpd.GeoDataFrame({"_i": range(len(gdf))}, geometry=list(dai_dien),
                            crs=gdf.crs, index=gdf.index)

    trong = gpd.sjoin(diem, lv, how="inner", predicate="within")
    trong = trong.sort_values("_dt").loc[~trong.sort_values("_dt").index.duplicated()]
    ma = trong["ma"].reindex(gdf.index)
    ten = trong["ten"].reindex(gdf.index)

    thieu = ma.isna()
    if thieu.any():
        gan = gpd.sjoin_nearest(diem[thieu], lv, how="left",
                                max_distance=KHOANG_CACH_TOI_DA_M)
        gan = gan.loc[~gan.index.duplicated()]
        ma = ma.fillna(gan["ma"])
        ten = ten.fillna(gan["ten"])
    return ma, ten, int(ma.isna().sum())


# ---------------------------------------------------------------- song suoi

def cap_tu_ma_song(ma_song):
    """22 -> cap I, 22.1 -> cap II, 22.3.1 -> cap III ... theo so thanh phan cua ma."""
    if not ma_song:
        return None
    n = len(str(ma_song).strip().split("."))
    return "Cấp " + ["I", "II", "III", "IV", "V", "VI"][min(n, 6) - 1]


def khoa_ma_song(ma):
    return [int(p) if p.isdigit() else 0 for p in str(ma).split(".")]


def tao_song_suoi(tt, luu_vuc):
    print("\n[2/4] Song, suoi")
    duong = mod_tinh.tim_tep_nguon("CSDL/dulieu_thuc/Song_suoi_KH_polyline.shp")
    g = doc(duong, tt["epsg_chuyen_de"])
    n_goc = len(g)
    for c in ("Ten_Song", "CHAY_RA", "VITRI_D", "VITRI_C", "GhiChu"):
        g[c] = g[c].apply(lambda s: tcvn3_sang_unicode(s, c in ("Ten_Song", "CHAY_RA")))
    g["MA_SONG"] = g["MA_SONG"].astype(str).str.strip()

    ma, ten, thieu = gan_luu_vuc(g, luu_vuc, tt["epsg_chuyen_de"])
    g["ma_luu_vuc"], g["ten_luu_vuc"] = ma, ten
    if thieu:
        print("   {} song/suoi khong gan duoc luu vuc".format(thieu))

    g["_k"] = g["MA_SONG"].apply(khoa_ma_song)
    g = g.sort_values("_k").reset_index(drop=True)
    ra = gpd.GeoDataFrame({
        "ma": ["S{:03d}".format(i + 1) for i in range(len(g))],
        "ten": g["Ten_Song"],
        "ma_song_goc": g["MA_SONG"],
        "cap_song": g["MA_SONG"].apply(cap_tu_ma_song),
        "chay_ra": g["CHAY_RA"],
        "chieu_dai_km": g["CHIEU_DAI"].round(2),
        "vi_tri_dau": g["VITRI_D"],
        "vi_tri_cuoi": g["VITRI_C"],
        "ghi_chu": g["GhiChu"],
        "ma_luu_vuc": g["ma_luu_vuc"],
        "ten_luu_vuc": g["ten_luu_vuc"],
        "nguon_dl": NGUON_DL,
    }, geometry=g.geometry, crs=g.crs)

    print("   Doc {} -> giu {} doan song/suoi".format(n_goc, len(ra)))
    print("   Theo cap: {}".format(ra["cap_song"].value_counts().sort_index().to_dict()))
    return ra


# ---------------------------------------------------------------- khai thac / xa thai

def doc_diem(tt, ten_tep, luu_vuc):
    duong = mod_tinh.tim_tep_nguon("CSDL/dulieu_thuc/" + ten_tep)
    g = doc(duong, tt["epsg_chuyen_de"])
    for c in g.columns:
        if c != "geometry" and la_cot_chu(g[c]):
            g[c] = g[c].apply(tcvn3_sang_unicode)
    ma, ten, thieu = gan_luu_vuc(g, luu_vuc, tt["epsg_chuyen_de"])
    g["ma_luu_vuc"], g["ten_luu_vuc"] = ma, ten
    if thieu:
        print("   {} diem khong gan duoc luu vuc".format(thieu))
    return g


def tao_khai_thac(tt, luu_vuc):
    print("\n[3/4] Cong trinh khai thac")
    g = doc_diem(tt, "TH_Khaithac_KH_point.shp", luu_vuc)
    # don vi theo bang MapInfo goc (CSDL/DULIEU_BD_SO_KH/.../MAP/TH_Khaithac_KH.TAB):
    #   Qkt_TUOI_m3_S m3/s, Qkt_SANXUAT_m3_ngay, Qkt_KHAC_m3_ngay m3/ngay,
    #   CONGSUAT_DIEN_KW kW, DUNGTICH_HOCHUA_TRIEUM3 trieu m3
    tuoi = g["Qkt_TUOI_m"].apply(so_hoc).fillna(0)
    sx = g["Qkt_SANXUA"].apply(so_hoc).fillna(0)
    khac = g["Qkt_KHAC_m"].apply(so_hoc).fillna(0)
    tong = tuoi * 86400 + sx + khac

    g = g.reset_index(drop=True)
    ra = gpd.GeoDataFrame({
        "ma": ["KT{:03d}".format(i + 1) for i in range(len(g))],
        "ten_cong_trinh": g["CONG_TRINH"],
        "loai_hinh": g["LO_I_CT"].apply(dong_nhat_chu),
        "muc_dich_su_dung": g["M_C_DICH_S"].apply(dong_nhat_chu),
        "nguon_nuoc_khai_thac": g["NGUON_KHAI"],
        "xa_phuong": g["XA_PHUONG"],
        "dung_tich_ho_trieu_m3": g["DUNGTICH_H"].apply(so_hoc).round(3),
        "q_tuoi_m3s": tuoi.round(4),
        "q_san_xuat_m3_ngay": sx.round(1),
        "cong_suat_dien_kw": g["CONGSUAT_D"].apply(so_hoc).round(1),
        "q_khac_m3_ngay": khac.round(1),
        "q_khai_thac_m3_ngay": tong.round(1),
        "luu_vuc_kiem_ke": g["LVS"],
        "ma_luu_vuc": g["ma_luu_vuc"],
        "ten_luu_vuc": g["ten_luu_vuc"],
        "nguon_dl": NGUON_DL,
    }, geometry=g.geometry, crs=g.crs)
    print("   Giu {} cong trinh. Loai hinh: {}".format(
        len(ra), ra["loai_hinh"].value_counts().to_dict()))
    print("   Muc dich: {}".format(ra["muc_dich_su_dung"].value_counts().head(8).to_dict()))
    return ra


def tao_xa_thai(tt, luu_vuc):
    print("\n[4/4] Diem xa thai")
    g = doc_diem(tt, "TH_Xathai_KH_point.shp", luu_vuc)
    q = g["Qxt_m3ngay"].apply(so_hoc)
    khong_doc = g.loc[q.isna() & g["Qxt_m3ngay"].notna(), "Qxt_m3ngay"]
    if len(khong_doc):
        print("   KHONG DOC DUOC luu luong xa (de trong): {}".format(list(khong_doc)))
    la = [v for v in g["Qxt_m3ngay"].dropna().astype(str)
          if not re.fullmatch(r"\d+(\.\d+)?", v.strip())]
    if la:
        print("   Cac gia tri luu luong dang la, can kiem tay: {}".format(la))

    g = g.reset_index(drop=True)
    ra = gpd.GeoDataFrame({
        "ma": ["XT{:03d}".format(i + 1) for i in range(len(g))],
        "ten_cong_trinh": g["CONG_TRINH"],
        "nguon_thai": g["LOAI_HINH"].apply(dong_nhat_chu),
        "nguon_tiep_nhan": g["NGUON_TIEP"],
        "xa_phuong": g["XA_PHUONG"],
        "q_xa_m3_ngay": q.round(1),
        "luu_vuc_kiem_ke": g["LVS"],
        "ma_luu_vuc": g["ma_luu_vuc"],
        "ten_luu_vuc": g["ten_luu_vuc"],
        "nguon_dl": NGUON_DL,
    }, geometry=g.geometry, crs=g.crs)
    print("   Giu {} diem xa. Loai hinh: {}".format(
        len(ra), ra["nguon_thai"].value_counts().to_dict()))
    return ra


# ---------------------------------------------------------------- kiem tra va ghi

def kiem_tra_khung_bao(ten, gdf, khung):
    """Bao va loai doi tuong nam ngoai khung bao nen cua tinh."""
    x0, y0, x1, y1 = khung
    b = gdf.geometry.bounds
    ngoai = (b.maxx < x0) | (b.minx > x1) | (b.maxy < y0) | (b.miny > y1)
    if ngoai.any():
        print("   {}: BO {} doi tuong ngoai khung bao nen".format(ten, int(ngoai.sum())))
        gdf = gdf[~ngoai]
    return gdf


def ghi(tt, ten_tep, gdf):
    """Ghi GeoJSON EPSG:4326. Khong ghi de neu khong con doi tuong nao."""
    if len(gdf) == 0:
        raise SystemExit("Lop {} khong con doi tuong nao, KHONG ghi de tep cu.".format(ten_tep))
    gdf = gdf.to_crs(4326)
    duong = mod_tinh.duong_dan_ra(tt, ten_tep)
    gdf.to_file(duong, driver="GeoJSON", engine="pyogrio", COORDINATE_PRECISION=6)
    print("   -> {} ({} doi tuong, {:.0f} KB)".format(
        duong, len(gdf), os.path.getsize(duong) / 1024))


def dong_bo_lop_mo_phong(tt, luu_vuc):
    """Gan lai ma_luu_vuc cho cac lop con mo phong theo luu vuc moi."""
    print("\nDong bo ma_luu_vuc cho cac lop mo phong")
    for ten in ("ho_chua", "mat_nuoc", "doan_song"):
        duong = mod_tinh.duong_dan_ra(tt, ten + ".geojson")
        if not os.path.exists(duong):
            continue
        g = gpd.read_file(duong).to_crs(tt["epsg_chuyen_de"])
        ma, tn, thieu = gan_luu_vuc(g, luu_vuc, tt["epsg_chuyen_de"])
        g["ma_luu_vuc"] = ma
        if "ten_luu_vuc" in g.columns:
            g["ten_luu_vuc"] = tn
        g.to_crs(4326).to_file(duong, driver="GeoJSON", engine="pyogrio",
                               COORDINATE_PRECISION=6)
        print("   {}: {} doi tuong, {} khong gan duoc luu vuc".format(ten, len(g), thieu))


def main():
    tt = mod_tinh.nap()
    epsg = tt["epsg_chuyen_de"]

    duong_ranh = mod_tinh.tim_tep_nguon("CSDL/dulieu_thuc/KhanhHoa.shp")
    ranh = gpd.read_file(duong_ranh).to_crs(epsg)
    ranh_tinh = shapely.make_valid(ranh.geometry.union_all())

    luu_vuc = tao_luu_vuc(tt, ranh_tinh)
    song = tao_song_suoi(tt, luu_vuc)
    khai = tao_khai_thac(tt, luu_vuc)
    xa = tao_xa_thai(tt, luu_vuc)

    print("\nKiem tra khung bao nen")
    khung = tt["khung_bao_nen"]
    song = kiem_tra_khung_bao("song_suoi", song.to_crs(4326), khung).to_crs(epsg)
    khai = kiem_tra_khung_bao("khai_thac", khai.to_crs(4326), khung).to_crs(epsg)
    xa = kiem_tra_khung_bao("xa_thai", xa.to_crs(4326), khung).to_crs(epsg)

    # tach ho ra lop rieng: loai_hinh bat dau bang "Ho" (ho chua, ho thuy dien)
    la_ho = khai["loai_hinh"].fillna("").str.startswith("Hồ")
    ao_ho = khai[la_ho].reset_index(drop=True)
    khai = khai[~la_ho].reset_index(drop=True)
    ao_ho.insert(0, "ma_khai_thac", ao_ho["ma"])
    ao_ho["ma"] = ["AH{:03d}".format(i + 1) for i in range(len(ao_ho))]
    print("\nTach lop ho: {} ho sang ao_ho, con {} cong trinh khai thac".format(
        len(ao_ho), len(khai)))

    print("\nGhi tep")
    # luu_vuc ghi truoc de dong_bo_lop_mo_phong dung cung ma
    ghi(tt, "luu_vuc.geojson", luu_vuc)
    ghi(tt, "song_suoi.geojson", song)
    ghi(tt, "khai_thac.geojson", khai)
    ghi(tt, "ao_ho.geojson", ao_ho)
    ghi(tt, "xa_thai.geojson", xa)

    dong_bo_lop_mo_phong(tt, luu_vuc)

    # canh bao ky tu con sot (bang ma TCVN3 thieu)
    sot = set()
    for gdf in (luu_vuc, song, khai, ao_ho, xa):
        for c in gdf.columns:
            if c != "geometry" and la_cot_chu(gdf[c]):
                for v in gdf[c].dropna():
                    sot.update(con_ky_tu_la(str(v)))
    if sot:
        print("\nCANH BAO: con ky tu chua doi duoc: {}".format("".join(sorted(sot))))
    else:
        print("\nKhong con ky tu la sau khi doi TCVN3.")


if __name__ == "__main__":
    main()
