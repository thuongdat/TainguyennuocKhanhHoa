# -*- coding: utf-8 -*-
"""
Sinh bo du lieu MAU (mo phong) cho WebGIS Tai nguyen nuoc Khanh Hoa.

Muc dich: de khung trang web chay duoc va kiem thu day du chuc nang truoc khi
co du lieu kiem ke chinh thuc. Toan bo so lieu thuoc tinh o day la mo phong,
vi tri hinh hoc chi gan dung. Moi doi tuong deu co truong "nguon_dl" ghi ro
dieu do, va giao dien web hien thi canh bao tuong ung.

Khi co du lieu that: thay script nay bang 02_chuan_hoa_chuyen_de.py doc
shapefile/GDB bang GeoPandas, giu nguyen ten truong da quy uoc trong
assets/js/config.js.

Chi ap dung cho tinh co co_du_lieu_mo_phong = true trong tep tham so. Danh
muc song, ho, luu vuc o day la cua rieng Khanh Hoa; tinh khac muon co du lieu
mau thi phai tu lap danh muc cua minh, khong dung lai duoc.

Chay:  python scripts/00_tao_du_lieu_mau.py
Chi dung thu vien chuan Python, khong can cai them goi nao.
"""

import json
import math
import os
import random
from datetime import datetime, timedelta, timezone

import sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import tinh as mod_tinh

# Gan trong main() sau khi biet dang xu ly tinh nao
THU_MUC_DATA = None

NGUON_DL = "Du lieu mau mo phong - khong dung cho muc dich chinh thuc"
MUI_GIO_VN = timezone(timedelta(hours=7))

# Co dinh hat giong de moi lan chay ra cung ket qua, de so sanh khi go loi
random.seed(2026)


# ----------------------------------------------------------------------------
# Tien ich hinh hoc
# ----------------------------------------------------------------------------

def khoang_cach_km(toa_do_1, toa_do_2):
    """Khoang cach haversine giua hai diem [lon, lat], don vi km."""
    lon1, lat1 = math.radians(toa_do_1[0]), math.radians(toa_do_1[1])
    lon2, lat2 = math.radians(toa_do_2[0]), math.radians(toa_do_2[1])
    a = (math.sin((lat2 - lat1) / 2) ** 2
         + math.cos(lat1) * math.cos(lat2) * math.sin((lon2 - lon1) / 2) ** 2)
    return 6371.0 * 2 * math.asin(math.sqrt(a))


def chieu_dai_km(duong):
    """Tong chieu dai mot chuoi toa do, don vi km."""
    return sum(khoang_cach_km(duong[i], duong[i + 1]) for i in range(len(duong) - 1))


def vung_tron(tam_lon, tam_lat, ban_kinh_do, so_dinh=24, meo=1.0):
    """Tao polygon gan tron (hoac elip neu meo != 1) quanh mot tam."""
    vong = []
    for i in range(so_dinh):
        goc = 2 * math.pi * i / so_dinh
        vong.append([
            round(tam_lon + ban_kinh_do * math.cos(goc) * meo, 5),
            round(tam_lat + ban_kinh_do * math.sin(goc), 5),
        ])
    vong.append(vong[0])  # dong vong
    return [vong]


def dien_tich_km2(vong_ngoai):
    """Dien tich gan dung cua polygon theo cong thuc shoelace, hieu chinh vi do."""
    lat_tb = sum(p[1] for p in vong_ngoai) / len(vong_ngoai)
    km_tren_do_lat = 110.574
    km_tren_do_lon = 111.320 * math.cos(math.radians(lat_tb))
    tong = 0.0
    for i in range(len(vong_ngoai) - 1):
        x1 = vong_ngoai[i][0] * km_tren_do_lon
        y1 = vong_ngoai[i][1] * km_tren_do_lat
        x2 = vong_ngoai[i + 1][0] * km_tren_do_lon
        y2 = vong_ngoai[i + 1][1] * km_tren_do_lat
        tong += x1 * y2 - x2 * y1
    return abs(tong) / 2


def ghi_geojson(ten_tep, danh_sach_feature, mo_ta):
    """Ghi mot FeatureCollection ra file GeoJSON trong thu muc data/."""
    os.makedirs(THU_MUC_DATA, exist_ok=True)
    duong_dan = os.path.join(THU_MUC_DATA, ten_tep)
    bo_suu_tap = {
        "type": "FeatureCollection",
        "name": os.path.splitext(ten_tep)[0],
        "crs": {"type": "name", "properties": {"name": "urn:ogc:def:crs:OGC:1.3:CRS84"}},
        "metadata": {
            "mo_ta": mo_ta,
            "nguon_dl": NGUON_DL,
            "ngay_tao": datetime.now(MUI_GIO_VN).isoformat(timespec="seconds"),
        },
        "features": danh_sach_feature,
    }
    with open(duong_dan, "w", encoding="utf-8") as f:
        json.dump(bo_suu_tap, f, ensure_ascii=False, separators=(",", ":"))
    kb = os.path.getsize(duong_dan) / 1024
    print("  {:<24} {:>4} doi tuong  {:>8.1f} KB".format(ten_tep, len(danh_sach_feature), kb))


def feature(hinh_hoc_loai, toa_do, thuoc_tinh):
    """Goi mot doi tuong thanh GeoJSON Feature, tu them truong nguon du lieu."""
    thuoc_tinh["nguon_dl"] = NGUON_DL
    return {
        "type": "Feature",
        "geometry": {"type": hinh_hoc_loai, "coordinates": toa_do},
        "properties": thuoc_tinh,
    }


# ----------------------------------------------------------------------------
# 1. Luu vuc song
# ----------------------------------------------------------------------------

LUU_VUC = [
    # ma, ten, tam lon, tam lat, ban kinh do, do meo, luong mua mm/nam
    ("LV01", "Luu vuc song Cai Nha Trang", 109.00, 12.28, 0.24, 1.15, 1680),
    ("LV02", "Luu vuc song Dinh Ninh Hoa", 109.07, 12.58, 0.17, 1.10, 1450),
    ("LV03", "Luu vuc song Cai Phan Rang", 108.85, 11.63, 0.26, 1.05, 1050),
    ("LV04", "Luu vuc song Trau", 109.02, 11.78, 0.11, 1.00, 980),
    ("LV05", "Luu vuc song Lu", 108.88, 11.45, 0.13, 1.00, 820),
    ("LV06", "Luu vuc song To Hap", 108.86, 12.02, 0.13, 1.20, 1920),
]

TEN_LUU_VUC_DAY_DU = {
    "LV01": "Lưu vực sông Cái Nha Trang",
    "LV02": "Lưu vực sông Dinh Ninh Hòa",
    "LV03": "Lưu vực sông Cái Phan Rang",
    "LV04": "Lưu vực sông Trâu",
    "LV05": "Lưu vực sông Lu",
    "LV06": "Lưu vực sông Tô Hạp",
}


def tao_luu_vuc():
    ds = []
    for ma, _ten_khong_dau, lon, lat, bk, meo, mua in LUU_VUC:
        vung = vung_tron(lon, lat, bk, so_dinh=28, meo=meo)
        dt = round(dien_tich_km2(vung[0]), 1)
        # Tong luong nuoc xap xi: dien tich x luong mua x he so dong chay
        he_so_dong_chay = 0.45 if mua > 1400 else 0.32
        tong_luong = round(dt * mua * he_so_dong_chay / 1000, 1)
        ds.append(feature("Polygon", vung, {
            "ma": ma,
            "ten": TEN_LUU_VUC_DAY_DU[ma],
            "dien_tich_km2": dt,
            "luong_mua_tb_mm": mua,
            "he_so_dong_chay": he_so_dong_chay,
            "tong_luong_nuoc_trieu_m3": tong_luong,
        }))
    return ds


# ----------------------------------------------------------------------------
# 2. Song, suoi
# ----------------------------------------------------------------------------

SONG_SUOI = [
    ("S01", "Sông Cái Nha Trang", "Cấp I", "LV01", 42.0,
     [[108.78, 12.33], [108.88, 12.31], [108.97, 12.28], [109.05, 12.27],
      [109.12, 12.26], [109.19, 12.255]]),
    ("S02", "Sông Chò", "Cấp II", "LV01", 9.5,
     [[108.92, 12.47], [108.97, 12.41], [109.01, 12.35], [109.04, 12.285]]),
    ("S03", "Sông Giang", "Cấp II", "LV01", 7.8,
     [[108.73, 12.18], [108.82, 12.22], [108.90, 12.27], [108.97, 12.28]]),
    ("S04", "Sông Dinh Ninh Hòa", "Cấp I", "LV02", 18.6,
     [[108.92, 12.62], [109.00, 12.57], [109.07, 12.53], [109.13, 12.50], [109.20, 12.52]]),
    ("S05", "Sông Tô Hạp", "Cấp II", "LV06", 6.2,
     [[108.98, 12.06], [108.90, 12.02], [108.82, 11.99], [108.74, 11.96]]),
    ("S06", "Sông Cái Phan Rang", "Cấp I", "LV03", 31.5,
     [[108.70, 11.76], [108.78, 11.70], [108.85, 11.64], [108.92, 11.59],
      [108.99, 11.57], [109.03, 11.55]]),
    ("S07", "Sông Lu", "Cấp II", "LV05", 5.4,
     [[108.78, 11.42], [108.85, 11.47], [108.92, 11.52], [108.98, 11.56]]),
    ("S08", "Sông Trâu", "Cấp II", "LV04", 4.1,
     [[108.93, 11.84], [108.99, 11.78], [109.04, 11.72], [109.08, 11.67]]),
    ("S09", "Sông Quao", "Cấp II", "LV03", 3.6,
     [[108.66, 11.62], [108.74, 11.60], [108.82, 11.60], [108.88, 11.605]]),
    ("S10", "Suối Dầu", "Cấp III", "LV01", 2.2,
     [[109.00, 12.08], [109.06, 12.11], [109.12, 12.14], [109.17, 12.18]]),
    ("S11", "Suối Cát", "Cấp III", "LV01", 1.8,
     [[108.95, 12.15], [109.00, 12.19], [109.05, 12.23]]),
    ("S12", "Sông Bà", "Cấp III", "LV02", 2.6,
     [[109.02, 12.70], [109.06, 12.65], [109.09, 12.59]]),
]


def tao_song_suoi():
    ds = []
    for ma, ten, cap, lv, q_tb, toa_do in SONG_SUOI:
        ds.append(feature("LineString", toa_do, {
            "ma": ma,
            "ten": ten,
            "cap_song": cap,
            "ma_luu_vuc": lv,
            "ten_luu_vuc": TEN_LUU_VUC_DAY_DU[lv],
            "chieu_dai_km": round(chieu_dai_km(toa_do), 1),
            "q_trung_binh_m3s": q_tb,
            "q_mua_kho_m3s": round(q_tb * 0.18, 2),
            "muc_dich_su_dung": "Cấp nước sinh hoạt, tưới, công nghiệp",
        }))
    return ds


# ----------------------------------------------------------------------------
# 3. Ho chua (diem) va mat nuoc tu nhien (vung)
# ----------------------------------------------------------------------------

HO_CHUA = [
    # ma, ten, lon, lat, W toan bo, W huu ich, H nguong tran, nam, muc dich
    ("HC01", "Hồ Đá Bàn", 109.0355, 12.6372, 75.0, 69.0, 56.0, 1988, "Tưới, cấp nước"),
    ("HC02", "Hồ Suối Dầu", 109.0700, 12.1000, 32.0, 29.0, 42.0, 1999, "Tưới, cấp nước"),
    ("HC03", "Hồ Cam Ranh", 109.0500, 11.9500, 22.1, 20.3, 40.0, 1995, "Tưới, cấp nước"),
    ("HC04", "Hồ Tà Rục", 108.9800, 11.8800, 20.4, 18.9, 60.0, 2012, "Tưới"),
    ("HC05", "Hồ Hoa Sơn", 109.2500, 12.7500, 19.6, 18.1, 35.0, 2009, "Tưới, cấp nước"),
    ("HC06", "Hồ Sông Chò 1", 108.9500, 12.4200, 10.5, 9.5, 75.0, 2018, "Tưới"),
    ("HC07", "Hồ Suối Hành", 109.0200, 11.9200, 7.8, 7.0, 38.0, 1986, "Tưới"),
    ("HC08", "Hồ Am Chúa", 109.1200, 12.3200, 4.6, 4.2, 22.0, 1984, "Tưới"),
    ("HC09", "Hồ Sông Sắt", 108.8500, 11.7500, 69.3, 63.0, 92.0, 2008, "Tưới, cấp nước"),
    ("HC10", "Hồ Sông Trâu", 109.0000, 11.7800, 31.5, 28.9, 65.0, 2005, "Tưới"),
    ("HC11", "Hồ Tân Giang", 108.8800, 11.4500, 13.4, 12.0, 58.0, 2001, "Tưới"),
    ("HC12", "Hồ Lanh Ra", 108.8500, 11.5200, 13.9, 12.6, 50.0, 2013, "Tưới"),
    ("HC13", "Hồ Sông Biêu", 108.8200, 11.4000, 23.5, 21.3, 70.0, 2014, "Tưới"),
    ("HC14", "Hồ Cho Mo", 108.9200, 11.7200, 8.8, 7.9, 80.0, 2011, "Tưới"),
]

MAT_NUOC = [
    # ma, ten, loai, lon, lat, ban kinh do, do meo
    ("MN01", "Đầm Nha Phu", "Đầm nước mặn", 109.175, 12.420, 0.055, 1.3),
    ("MN02", "Đầm Thủy Triều", "Đầm nước mặn", 109.155, 12.030, 0.040, 0.6),
    ("MN03", "Đầm Nại", "Đầm nước mặn", 109.045, 11.655, 0.030, 1.0),
    ("MN04", "Ao hồ Diên Khánh", "Ao, hồ tự nhiên", 109.080, 12.255, 0.012, 1.0),
    ("MN05", "Bàu Ninh Chữ", "Ao, hồ tự nhiên", 109.010, 11.600, 0.015, 1.2),
]


def gan_luu_vuc(lon, lat):
    """Gan doi tuong vao luu vuc co tam gan nhat (chi dung cho du lieu mau)."""
    gan_nhat = min(LUU_VUC, key=lambda lv: khoang_cach_km([lon, lat], [lv[2], lv[3]]))
    return gan_nhat[0]


def tao_ho_chua():
    ds = []
    for ma, ten, lon, lat, w_tb, w_hi, h_ng, nam, mdich in HO_CHUA:
        lv = gan_luu_vuc(lon, lat)
        ds.append(feature("Point", [lon, lat], {
            "ma": ma,
            "ten": ten,
            "ma_luu_vuc": lv,
            "ten_luu_vuc": TEN_LUU_VUC_DAY_DU[lv],
            "nam_hoan_thanh": nam,
            "w_toan_bo_trieu_m3": w_tb,
            "w_huu_ich_trieu_m3": w_hi,
            "h_nguong_tran_m": h_ng,
            "muc_dich": mdich,
            "don_vi_quan_ly": "Công ty TNHH MTV Khai thác công trình thủy lợi",
        }))
    return ds


def tao_mat_nuoc():
    ds = []
    for ma, ten, loai, lon, lat, bk, meo in MAT_NUOC:
        vung = vung_tron(lon, lat, bk, so_dinh=20, meo=meo)
        lv = gan_luu_vuc(lon, lat)
        ds.append(feature("Polygon", vung, {
            "ma": ma,
            "ten": ten,
            "loai": loai,
            "dien_tich_ha": round(dien_tich_km2(vung[0]) * 100, 1),
            "ma_luu_vuc": lv,
            "ten_luu_vuc": TEN_LUU_VUC_DAY_DU[lv],
        }))
    return ds


# ----------------------------------------------------------------------------
# 4. Cong trinh khai thac, su dung nuoc
# ----------------------------------------------------------------------------

LOAI_KHAI_THAC = [
    "Cấp nước sinh hoạt", "Cấp nước công nghiệp", "Tưới nông nghiệp",
    "Thủy điện", "Nuôi trồng thủy sản",
]

CHU_GIAY_PHEP = [
    "Công ty CP Cấp thoát nước Khánh Hòa",
    "Công ty TNHH MTV Khai thác công trình thủy lợi",
    "Công ty CP Đường Khánh Hòa",
    "Ban Quản lý KCN Suối Dầu",
    "Công ty CP Thủy điện Sông Giang",
    "Công ty CP Cấp nước Ninh Thuận",
    "Hợp tác xã Nông nghiệp Ninh Phước",
]

VI_TRI_KHAI_THAC = [
    ("KT01", "Trạm bơm Xuân Phong", 109.045, 12.272, 0),
    ("KT02", "Nhà máy nước Võ Cạnh", 109.142, 12.258, 0),
    ("KT03", "Trạm bơm KCN Suối Dầu", 109.082, 12.112, 1),
    ("KT04", "Đập dâng Ninh Hòa", 109.098, 12.528, 2),
    ("KT05", "Thủy điện Sông Giang 2", 108.805, 12.215, 3),
    ("KT06", "Trạm bơm Diên Thọ", 109.012, 12.235, 2),
    ("KT07", "Nhà máy nước Cam Ranh", 109.148, 11.925, 0),
    ("KT08", "Đập Nha Trinh", 108.922, 11.598, 2),
    ("KT09", "Đập Lâm Cấm", 108.962, 11.578, 2),
    ("KT10", "Trạm bơm Phước Dân", 108.925, 11.512, 2),
    ("KT11", "Nhà máy nước Phan Rang", 108.985, 11.575, 0),
    ("KT12", "Trạm bơm Thuận Bắc", 109.018, 11.772, 2),
    ("KT13", "Vùng nuôi tôm Đầm Nại", 109.052, 11.648, 4),
    ("KT14", "Trạm bơm Vạn Ninh", 109.228, 12.705, 2),
    ("KT15", "Trạm bơm Khánh Sơn", 108.885, 12.015, 2),
]


def tao_khai_thac():
    ds = []
    hom_nay = datetime.now(MUI_GIO_VN).date()
    ten_nguon_nuoc = [s[1] for s in SONG_SUOI] + [h[1] for h in HO_CHUA]
    for i, (ma, ten, lon, lat, idx_loai) in enumerate(VI_TRI_KHAI_THAC):
        q_cp = random.choice([500, 1200, 2500, 5000, 12000, 25000, 48000])
        # Mot vai giay phep co tinh sap het han de kiem thu chuc nang canh bao
        so_ngay_con = random.choice([45, 120, 300, 900, 1500, 2200, -30])
        lv = gan_luu_vuc(lon, lat)
        ds.append(feature("Point", [lon, lat], {
            "ma": ma,
            "ten_cong_trinh": ten,
            "loai_hinh": LOAI_KHAI_THAC[idx_loai],
            "chu_giay_phep": CHU_GIAY_PHEP[i % len(CHU_GIAY_PHEP)],
            "so_giay_phep": "{}/GP-UBND".format(1200 + i * 7),
            "ngay_cap": str(hom_nay - timedelta(days=so_ngay_con + 1825)),
            "ngay_het_han": str(hom_nay + timedelta(days=so_ngay_con)),
            "nguon_nuoc_khai_thac": random.choice(ten_nguon_nuoc),
            "q_cap_phep_m3_ngay": q_cp,
            "q_thuc_te_m3_ngay": int(q_cp * random.uniform(0.45, 1.12)),
            "ma_luu_vuc": lv,
            "ten_luu_vuc": TEN_LUU_VUC_DAY_DU[lv],
        }))
    return ds


# ----------------------------------------------------------------------------
# 5. Diem xa thai vao nguon nuoc
# ----------------------------------------------------------------------------

VI_TRI_XA_THAI = [
    ("XT01", "KCN Suối Dầu", 109.090, 12.105, "Nước thải công nghiệp"),
    ("XT02", "Nhà máy XLNT Nha Trang", 109.186, 12.232, "Nước thải sinh hoạt"),
    ("XT03", "KCN Ninh Thủy", 109.212, 12.618, "Nước thải công nghiệp"),
    ("XT04", "Nhà máy đường Ninh Hòa", 109.085, 12.512, "Nước thải chế biến"),
    ("XT05", "Bệnh viện đa khoa Khánh Hòa", 109.178, 12.248, "Nước thải y tế"),
    ("XT06", "Khu dân cư Diên Khánh", 109.065, 12.248, "Nước thải sinh hoạt"),
    ("XT07", "KCN Thành Hải", 108.998, 11.598, "Nước thải công nghiệp"),
    ("XT08", "Nhà máy XLNT Phan Rang", 108.992, 11.565, "Nước thải sinh hoạt"),
    ("XT09", "Cơ sở chế biến thủy sản Đông Hải", 109.022, 11.548, "Nước thải chế biến"),
    ("XT10", "Khu dân cư Phước Dân", 108.930, 11.518, "Nước thải sinh hoạt"),
    ("XT11", "Trang trại chăn nuôi Bác Ái", 108.862, 11.742, "Nước thải chăn nuôi"),
    ("XT12", "KCN Vạn Thắng", 109.235, 12.712, "Nước thải công nghiệp"),
]


def tao_xa_thai():
    ds = []
    hom_nay = datetime.now(MUI_GIO_VN).date()
    ten_song = [s[1] for s in SONG_SUOI]
    for i, (ma, ten, lon, lat, nguon_thai) in enumerate(VI_TRI_XA_THAI):
        q_xa = random.choice([150, 400, 900, 1800, 3500, 7000])
        # Mot so diem co tinh vuot quy chuan de kiem thu to mau canh bao
        vuot = (i % 4 == 1)
        bod5 = round(random.uniform(38, 62) if vuot else random.uniform(8, 28), 1)
        lv = gan_luu_vuc(lon, lat)
        ds.append(feature("Point", [lon, lat], {
            "ma": ma,
            "ten_cong_trinh": ten,
            "nguon_thai": nguon_thai,
            "chu_giay_phep": CHU_GIAY_PHEP[i % len(CHU_GIAY_PHEP)],
            "so_giay_phep": "{}/GP-XT".format(300 + i * 11),
            "ngay_het_han": str(hom_nay + timedelta(days=random.choice([60, 200, 700, 1400]))),
            "nguon_tiep_nhan": random.choice(ten_song),
            "q_xa_m3_ngay": q_xa,
            "bod5_mg_l": bod5,
            "cod_mg_l": round(bod5 * random.uniform(1.6, 2.2), 1),
            "amoni_mg_l": round(random.uniform(0.4, 12.0), 2),
            "tong_n_mg_l": round(random.uniform(5, 45), 1),
            "tong_p_mg_l": round(random.uniform(0.3, 6.0), 2),
            "qcvn_ap_dung": "QCVN 40:2021/BTNMT, cột B",
            "vuot_quy_chuan": "Có" if vuot else "Không",
            "ma_luu_vuc": lv,
            "ten_luu_vuc": TEN_LUU_VUC_DAY_DU[lv],
        }))
    return ds


# ----------------------------------------------------------------------------
# 6. Tram quan trac
# ----------------------------------------------------------------------------

TRAM_QUAN_TRAC = [
    ("QT01", "Trạm thủy văn Đồng Trăng", "Thủy văn", 108.975, 12.282, "Sông Cái Nha Trang"),
    ("QT02", "Trạm thủy văn Ninh Hòa", "Thủy văn", 109.095, 12.525, "Sông Dinh Ninh Hòa"),
    ("QT03", "Trạm thủy văn Tân Mỹ", "Thủy văn", 108.782, 11.702, "Sông Cái Phan Rang"),
    ("QT04", "Trạm mưa Khánh Vĩnh", "Mưa", 108.812, 12.292, ""),
    ("QT05", "Trạm mưa Nha Trang", "Mưa", 109.195, 12.238, ""),
    ("QT06", "Trạm mưa Khánh Sơn", "Mưa", 108.902, 12.028, ""),
    ("QT07", "Trạm mưa Phan Rang", "Mưa", 108.988, 11.578, ""),
    ("QT08", "Điểm quan trắc CLN Xóm Bóng", "Chất lượng nước", 109.192, 12.258, "Sông Cái Nha Trang"),
    ("QT09", "Điểm quan trắc CLN Hà Dừa", "Chất lượng nước", 109.112, 12.262, "Sông Cái Nha Trang"),
    ("QT10", "Điểm quan trắc CLN Dinh Ninh Hòa", "Chất lượng nước", 109.128, 12.502, "Sông Dinh Ninh Hòa"),
    ("QT11", "Điểm quan trắc CLN Đạo Long", "Chất lượng nước", 108.995, 11.572, "Sông Cái Phan Rang"),
    ("QT12", "Điểm quan trắc CLN Sông Lu", "Chất lượng nước", 108.952, 11.538, "Sông Lu"),
]


def tao_quan_trac():
    ds = []
    for ma, ten, loai, lon, lat, song in TRAM_QUAN_TRAC:
        lv = gan_luu_vuc(lon, lat)
        ds.append(feature("Point", [lon, lat], {
            "ma": ma,
            "ten": ten,
            "loai_tram": loai,
            "song_ho": song,
            "ma_luu_vuc": lv,
            "ten_luu_vuc": TEN_LUU_VUC_DAY_DU[lv],
            "don_vi_quan_ly": "Đài Khí tượng Thủy văn khu vực Nam Trung Bộ",
            "tan_suat_do": ("Định kỳ, 1 tháng/lần" if loai == "Chất lượng nước"
                            else "Tự động, 15 phút/lần"),
        }))
    return ds


# ----------------------------------------------------------------------------
# 7. Phan doan song danh gia suc chiu tai
#    Theo phuong phap danh gia truc tiep, Thong tu 76/2017/TT-BTNMT
#    (sua doi boi Thong tu 02/2022/TT-BTNMT):
#       Ltd = Cqc x Qs x 86,4          (tai luong toi da, kg/ngay)
#       Lnn = Cnn x Qs x 86,4          (tai luong o nhiem san co)
#       Ltn = (Ltd - Lnn - Lt) x Fs    (kha nang tiep nhan con lai)
# ----------------------------------------------------------------------------

def tao_doan_song():
    """Cat moi con song cap I, II thanh cac doan va tinh suc chiu tai BOD5."""
    ds = []
    dem = 0
    for ma_song, ten_song, cap, lv, q_tb, toa_do in SONG_SUOI:
        if cap == "Cấp III":
            continue
        so_doan = len(toa_do) - 1
        for i in range(so_doan):
            dem += 1
            doan = [toa_do[i], toa_do[i + 1]]
            # Luu luong tang dan ve phia ha luu
            q_s = round(q_tb * (0.35 + 0.65 * (i + 1) / so_doan), 2)
            c_qc = 15.0   # BOD5 gioi han theo QCVN 08:2023/BTNMT, muc B
            c_nn = round(random.uniform(3.0, 13.5), 1)
            l_td = round(c_qc * q_s * 86.4, 1)
            l_nn = round(c_nn * q_s * 86.4, 1)
            l_t = round(l_td * random.uniform(0.05, 0.55), 1)
            f_s = 0.7     # he so an toan
            l_tn = round((l_td - l_nn - l_t) * f_s, 1)
            if l_tn <= 0:
                trang_thai = "Không còn khả năng tiếp nhận"
            elif l_tn < l_td * 0.15:
                trang_thai = "Gần ngưỡng"
            else:
                trang_thai = "Còn khả năng tiếp nhận"
            ds.append(feature("LineString", doan, {
                "ma": "DS{:02d}".format(dem),
                "ten_doan": "{} - đoạn {}".format(ten_song, i + 1),
                "ma_song": ma_song,
                "ten_song": ten_song,
                "ma_luu_vuc": lv,
                "ten_luu_vuc": TEN_LUU_VUC_DAY_DU[lv],
                "chieu_dai_km": round(chieu_dai_km(doan), 2),
                "thong_so": "BOD5",
                "q_s_m3s": q_s,
                "c_qc_mg_l": c_qc,
                "c_nn_mg_l": c_nn,
                "l_td_kg_ngay": l_td,
                "l_nn_kg_ngay": l_nn,
                "l_t_kg_ngay": l_t,
                "f_s": f_s,
                "l_tn_kg_ngay": l_tn,
                "ty_le_con_lai": round(max(l_tn, 0) / l_td, 3),
                "trang_thai": trang_thai,
                "can_cu": "TT 76/2017/TT-BTNMT, sửa đổi bởi TT 02/2022/TT-BTNMT",
            }))
    return ds


# ----------------------------------------------------------------------------
# Chay chinh
# ----------------------------------------------------------------------------

def main():
    global THU_MUC_DATA
    tt = mod_tinh.nap()

    if not tt.get("co_du_lieu_mo_phong"):
        raise SystemExit(
            "Tinh {} khai bao co_du_lieu_mo_phong = false nen bo qua script nay. "
            "Danh muc song, ho, luu vuc trong script la cua rieng Khanh Hoa."
            .format(tt["ten_tinh"]))

    THU_MUC_DATA = tt["_thu_muc_data"]

    print("Sinh du lieu mau cho {}".format(tt["ten_tinh"]))
    print("-" * 62)
    ghi_geojson("luu_vuc.geojson", tao_luu_vuc(), "Ranh gioi luu vuc song")
    ghi_geojson("song_suoi.geojson", tao_song_suoi(), "Mang luoi song, suoi")
    ghi_geojson("mat_nuoc.geojson", tao_mat_nuoc(), "Ao, ho, dam tu nhien")
    ghi_geojson("ho_chua.geojson", tao_ho_chua(), "Ho chua, dap dang")
    ghi_geojson("khai_thac.geojson", tao_khai_thac(), "Cong trinh khai thac, su dung nuoc")
    ghi_geojson("xa_thai.geojson", tao_xa_thai(), "Diem xa nuoc thai vao nguon nuoc")
    ghi_geojson("quan_trac.geojson", tao_quan_trac(), "Tram, diem quan trac")
    ghi_geojson("doan_song.geojson", tao_doan_song(), "Phan doan song danh gia suc chiu tai")
    print("-" * 62)
    print("Xong. Du lieu ghi tai: {}".format(THU_MUC_DATA))
    print("Luu y: toan bo la du lieu mo phong, chi dung de kiem thu giao dien.")


if __name__ == "__main__":
    main()
