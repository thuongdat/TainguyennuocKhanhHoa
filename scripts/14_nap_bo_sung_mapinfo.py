# -*- coding: utf-8 -*-
r"""
Nap bo du lieu that bo sung dang MapInfo TAB thanh 5 lop GeoJSON.

Dau vao : CSDL/KHANHHOA_BS/KHANHHOA_BS/MAP/*.TAB
Dau ra  : data/<lop>.geojson (EPSG:4326)

    1.TH_CLN_KK_KHANHHOA_FINAL  -> quan_trac_dia_phuong.geojson  (111 diem WQI)
    2.TH_HoAo_co_XY             -> ao_ho_khong_san_lap.geojson   (ho, ao, dam)
    3.Luong_dc                  -> luu_luong.geojson             (luu luong dong chay)
    4.TH_VETLU                  -> vet_lu.geojson                (vet lu)
    5.SAT_LO_KH                 -> sat_lo.geojson                (sat lo bo song, duong)

BON DIEU CAN BIET VE BO TEP NAY

1. He toa do khai la Transverse Mercator kinh tuyen 108d15', k=0.9999 nhung
   datum ghi WGS84. Day la VN-2000 / TM-3 108-15 (EPSG:9217), giong bo
   SD_TLTT_DTHT_XA_THAI, nen phai set_crs(9217, allow_override=True) de pyproj
   dung dung phep chuyen datum.
2. Chu tieng Viet la ma TCVN3 (ABC) bi doc nhu cp1252 ("Kh¸nh Hßa"). Doi bang
   tcvn3_sang_unicode() cua script 05, khong chep lai bang ma.
3. Cot X trong bang la TUNG DO (northing), cot Y la HOANH DO. Khong dung hai
   cot do, lay toa do tu hinh hoc.
4. WQI bang 0 nghia la ky do CHUA DO (cot 7/2026 gan nhu toan 0), khong phai
   nuoc o nhiem rat nang. Coi la thieu.

Chay:  python scripts/14_nap_bo_sung_mapinfo.py
       python scripts/14_nap_bo_sung_mapinfo.py --lop vet_lu --thu-muc-ra <thu muc>
"""

import argparse
import glob
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import tinh as mod_tinh
import kiem_ke_xlsx as kk

# Nap script 05 cung la luc sua_duong_dan_proj() chay, truoc geopandas
m05 = kk.nap_script("05_chuan_hoa_chuyen_de")
m13 = kk.nap_script("13_nap_wqi_dia_phuong")
gpd = m05.gpd

THU_MUC_NGUON = "CSDL/KHANHHOA_BS/KHANHHOA_BS/MAP"
EPSG_NGUON = 9217
NGUON_DL = "Bộ dữ liệu bổ sung kiểm kê tài nguyên nước tỉnh Khánh Hòa (MapInfo)"


# ---------------------------------------------------------------------------
# Ham dung chung
# ---------------------------------------------------------------------------

def chu(gia_tri, viet_hoa=False):
    """O chu TCVN3 -> Unicode da lam sach, rong thanh None."""
    return kk.sach(m05.tcvn3_sang_unicode(gia_tri, viet_hoa))


def so(gia_tri, so_le=None):
    """O so (Float hoac chu '1,36') -> so thuc. NaN thanh None."""
    if gia_tri is None:
        return None
    if isinstance(gia_tri, float) and gia_tri != gia_tri:
        return None
    return kk.so_hoc(gia_tri, so_le)


def viet_hoa_dau(s):
    """'song Tam Ich' -> 'Song Tam Ich'."""
    return s[:1].upper() + s[1:] if s else s


def gon(x):
    """3.0 -> 3 de hien thi gon."""
    if isinstance(x, float) and x.is_integer():
        return int(x)
    return x


def tim_tep(tt, tien_to):
    mau = os.path.join(mod_tinh.GOC, THU_MUC_NGUON, tien_to + "*.TAB")
    cac_tep = sorted(glob.glob(mau))
    if not cac_tep:
        raise SystemExit("DỪNG: không tìm thấy {}".format(mau))
    return cac_tep[0]


def doc_lop(tt, tien_to):
    """Doc TAB, ep he 9217, bo doi tuong ngoai khung_bao_nen, doi ve 4326."""
    tep = tim_tep(tt, tien_to)
    g = gpd.read_file(tep)
    g = g.set_crs(EPSG_NGUON, allow_override=True)
    g = g[g.geometry.notna() & ~g.geometry.is_empty].to_crs(4326)

    x0, y0, x1, y1 = tt["khung_bao_nen"]
    tam = g.geometry.representative_point()
    trong = (tam.x >= x0) & (tam.x <= x1) & (tam.y >= y0) & (tam.y <= y1)
    print("\nĐọc: {}".format(os.path.basename(tep)))
    print("  Số đối tượng    : {}".format(len(g)))
    if (~trong).sum():
        print("  Ngoài khung bao : {} (không đưa vào tệp, kiểm lại tọa độ):"
              .format(int((~trong).sum())))
        g_goc = g.to_crs(EPSG_NGUON)
        for i in g.index[~trong]:
            r = g_goc.loc[i]
            print("    STT {}: {} (x={:.0f}, y={:.0f})".format(
                gon(r.get("STT")), chu(r.iloc[1], True),
                r.geometry.x if r.geometry.geom_type == "Point" else 0,
                r.geometry.y if r.geometry.geom_type == "Point" else 0))
    return os.path.basename(tep), g[trong].reset_index(drop=True)


def ma_theo_stt(tien_to, stt, i):
    try:
        n = int(stt)
    except (TypeError, ValueError):
        n = i + 1
    return "{}-{:03d}".format(tien_to, n)


def thanh_feature(hinh, thuoc_tinh):
    """Hinh hoc shapely 4326 -> Feature GeoJSON, lam tron 7 chu so."""
    if hinh.geom_type == "Point":
        return kk.diem(hinh.x, hinh.y, thuoc_tinh)
    toa_do = [[round(x, 7), round(y, 7)] for x, y in hinh.coords]
    return {"type": "Feature",
            "geometry": {"type": "LineString", "coordinates": toa_do},
            "properties": thuoc_tinh}


def kiem_ma_trung(cac_doi_tuong):
    da_co = set()
    for d in cac_doi_tuong:
        ma = d["properties"]["ma"]
        if ma in da_co:
            raise SystemExit("DỪNG: mã {} bị trùng (STT lặp). Sửa STT trong "
                             "tệp MapInfo rồi chạy lại.".format(ma))
        da_co.add(ma)


def gan_luu_vuc_duong(tt, cac_doi_tuong):
    """Gan luu vuc cho lop duong theo trung diem cua doan."""
    tam = []
    for d in cac_doi_tuong:
        c = d["geometry"]["coordinates"]
        tam.append(kk.diem(c[len(c) // 2][0], c[len(c) // 2][1], {}))
    kk.gan_luu_vuc(tt, tam)
    for d, t in zip(cac_doi_tuong, tam):
        d["properties"]["ma_luu_vuc"] = t["properties"].get("ma_luu_vuc")
        d["properties"]["ten_luu_vuc"] = t["properties"].get("ten_luu_vuc")


# ---------------------------------------------------------------------------
# Tung lop
# ---------------------------------------------------------------------------

def lop_quan_trac_dia_phuong(tt):
    ten_tep, g = doc_lop(tt, "1.")
    # Cot WQI__<thang>_<nam>, giu thu tu thoi gian theo thu tu cot trong bang
    cot_wqi = [c for c in g.columns if re.fullmatch(r"WQI__\d+_\d{4}", c)]
    cot_wqi.sort(key=lambda c: (int(c.split("_")[-1]), int(c.split("_")[2])))

    ra = []
    for i, r in g.iterrows():
        cac_ky = []
        for c in cot_wqi:
            w = so(r[c], 1)
            if w is not None and w <= 0:
                w = None                  # 0 la chua do, xem chu thich dau tep
            _, _, thang, nam = c.split("_")
            cac_ky.append(("{}/{}".format(thang, nam), w))
        tt_dt = {
            "ma": ma_theo_stt("QD", r.get("STT"), i),
            "ten": chu(r.get("VI_TRI"), True),
            "nguon_nuoc": chu(r.get("NGUON_NUOC"), True),
            "xa_phuong": chu(r.get("XA"), True),
            "tinh": chu(r.get("TINH"), True),
            "luu_vuc_kiem_ke": chu(r.get("LVS"), True),
        }
        tt_dt.update(m13.tom_tat_chuoi(cac_ky))
        wtb = so(r.get("WQI_TB"), 1)
        tt_dt["wqi_tb"] = gon(wtb) if wtb else None
        tt_dt["phan_loai_wqi"] = m13.phan_loai_wqi(tt_dt["wqi"])
        tt_dt["nguon_dl"] = nguon_dl(ten_tep)
        ra.append(thanh_feature(r.geometry, tt_dt))
    kk.gan_luu_vuc(tt, ra)
    return ra


def lop_ao_ho_khong_san_lap(tt):
    ten_tep, g = doc_lop(tt, "2.")
    ra = []
    for i, r in g.iterrows():
        dt_m2 = so(r.get("DIENTICH_MATNUOC_m2"), 1)
        tt_dt = {
            "ma": ma_theo_stt("HKSL", r.get("STT"), i),
            "ten": chu(r.get("TEN_CongTrinh"), True),
            "vi_tri_hc": chu(r.get("XA_PHUONG")),
            "tinh": chu(r.get("TINH"), True),
            "dien_tich_mat_nuoc_m2": gon(dt_m2) if dt_m2 is not None else None,
            "dien_tich_ha": round(dt_m2 / 10000.0, 3) if dt_m2 else None,
            "dung_tich_trieu_m3": so(r.get("DUNGTICH_TOANBO__Trm3"), 4),
            "dung_tich_huu_ich_trieu_m3": so(r.get("DUNGTICH_HuuIch__Trm3"), 4),
            "chuc_nang": chu(r.get("MUCDICH_SUDUNG")),
            "luu_vuc_kiem_ke": chu(r.get("LVS"), True),
            "ghi_chu": chu(r.get("GHI_CHU")),
            "nguon_dl": nguon_dl(ten_tep),
        }
        ra.append(thanh_feature(r.geometry, tt_dt))
    kk.gan_luu_vuc(tt, ra)
    return ra


def lop_luu_luong(tt):
    ten_tep, g = doc_lop(tt, "3.")
    # Ten cot luu vuc, xa, tinh cung bi loi phong TCVN3 nen tim theo vi tri:
    # cot thu 2, 5, 6 cua bang (sau STT la luu vuc, X, Y, xa, tinh)
    cot = list(g.columns)
    cot_lv, cot_xa, cot_tinh = cot[1], cot[4], cot[5]
    ra = []
    for i, r in g.iterrows():
        tt_dt = {
            "ma": ma_theo_stt("LL", r.get("STT"), i),
            "luu_vuc_kiem_ke": chu(r[cot_lv], True),
            "xa_phuong": chu(r[cot_xa], True),
            "tinh": chu(r[cot_tinh], True),
        }
        for t in range(1, 13):
            tt_dt["q_thang_{}".format(t)] = so(r.get("Q_Thang_{}_trm3".format(t)), 3)
        tt_dt["q_mua_mua"] = so(r.get("Q_Muamua_trm3"), 3)
        tt_dt["q_mua_kho"] = so(r.get("Q_Muakho_trm3"), 3)
        tt_dt["q_ca_nam"] = so(r.get("Q_canam_trm3"), 3)
        tt_dt["nguon_dl"] = nguon_dl(ten_tep)
        ra.append(thanh_feature(r.geometry, tt_dt))
    kk.gan_luu_vuc(tt, ra)
    return ra


def lop_vet_lu(tt):
    ten_tep, g = doc_lop(tt, "4.")
    # Cot NGUOI_CUNGCAP_THONGTIN (ho ten nguoi dan cung cap thong tin) co y
    # KHONG dua ra: data/ duoc xuat ban cong khai tren GitHub Pages.
    ra = []
    for i, r in g.iterrows():
        tt_dt = {
            "ma": ma_theo_stt("VL", r.get("STT"), i),
            "thon": chu(r.get("THON"), True),
            "xa_phuong": chu(r.get("XA"), True),
            "tinh": chu(r.get("TINH"), True),
            "luu_vuc_kiem_ke": chu(r.get("LVS"), True),
            "chieu_cao_vet_lu_m": so(r.get("CHIEUCAO_VETLU_m"), 2),
            "doi_tuong_quan_sat": chu(r.get("DOITUONG__QUANSAT")),
            "nguon_dl": nguon_dl(ten_tep),
        }
        ra.append(thanh_feature(r.geometry, tt_dt))
    kk.gan_luu_vuc(tt, ra)
    return ra


def lop_sat_lo(tt):
    ten_tep, g = doc_lop(tt, "5.")
    # STT cua bang nay phan lon la 0 nen khong dung lam ma: danh so theo thu
    # tu dong trong bang
    ra = []
    for i, r in g.iterrows():
        tt_dt = {
            "ma": "SL-{:03d}".format(i + 1),
            "ten_song": viet_hoa_dau(chu(r.get("TEN_SONG"), True)),
            "thon": chu(r.get("THON"), True),
            "xa_phuong": chu(r.get("XA"), True),
            "tinh": chu(r.get("TINH"), True),
            "luu_vuc_kiem_ke": chu(r.get("LVS"), True),
            "bo_song": chu(r.get("BO_SONG")),
            "chieu_dai_m": so(r.get("CHIEUDAI_SATLO_m"), 1),
            "mo_ta": chu(r.get("MO_TA")),
            "nguon_dl": nguon_dl(ten_tep),
        }
        ra.append(thanh_feature(r.geometry, tt_dt))
    gan_luu_vuc_duong(tt, ra)
    return ra


def nguon_dl(ten_tep):
    return "{}, tệp {}, nạp ngày {}".format(NGUON_DL, ten_tep, kk.ngay_hom_nay())


# Ma lop -> ham dung lop. Ma lop cung la ten tep dau ra va khoa trong config.js
CAC_LOP = {
    "quan_trac_dia_phuong": lop_quan_trac_dia_phuong,
    "ao_ho_khong_san_lap": lop_ao_ho_khong_san_lap,
    "luu_luong": lop_luu_luong,
    "vet_lu": lop_vet_lu,
    "sat_lo": lop_sat_lo,
}


def ky_tu_sot(cac_doi_tuong):
    sot = set()
    for d in cac_doi_tuong:
        for v in d["properties"].values():
            if isinstance(v, str):
                sot.update(m05.con_ky_tu_la(v))
    return sot


def main():
    p = argparse.ArgumentParser(description=__doc__.splitlines()[1])
    p.add_argument("--lop", choices=sorted(CAC_LOP), action="append",
                   help="chi nap lop nay (lap lai duoc); mac dinh nap ca 5")
    p.add_argument("--thu-muc-ra", help="ghi ra thu muc khac thay vi data/")
    tham_so = p.parse_args()
    tt = mod_tinh.nap()

    tom_tat = []
    for ma_lop in (tham_so.lop or list(CAC_LOP)):
        cac_doi_tuong = CAC_LOP[ma_lop](tt)
        kiem_ma_trung(cac_doi_tuong)
        sot = ky_tu_sot(cac_doi_tuong)
        if sot:
            print("CẢNH BÁO: còn ký tự TCVN3 chưa đổi được: {}".format(
                "".join(sorted(sot))))
        kk.ghi_geojson(tt, ma_lop + ".geojson", ma_lop, cac_doi_tuong,
                       {"sinh_boi": "14_nap_bo_sung_mapinfo",
                        "nguon_dl": NGUON_DL},
                       tham_so.thu_muc_ra)
        tom_tat.append((ma_lop, len(cac_doi_tuong)))

    print("\nTóm tắt:")
    for ma_lop, n in tom_tat:
        print("  {:<24} {} đối tượng".format(ma_lop, n))
    print("\nNhớ đăng ký các lớp trên vào lop_co_san trong tinh.json.")


if __name__ == "__main__":
    main()
