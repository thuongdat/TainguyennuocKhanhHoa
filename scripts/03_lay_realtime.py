# -*- coding: utf-8 -*-
"""
Cap nhat du lieu quan trac "thoi gian thuc" cho WebGIS Tai nguyen nuoc Khanh Hoa.

HIEN TAI: che do MO PHONG. Script sinh so lieu theo mot ham bien thien tron
theo thoi gian (mua + chu ky ngay), nen cac lan chay lien tiep cho ra chuoi so
lien tuc, giong du lieu quan trac that. Khong co so lieu that nao o day.

KHI CO NGUON THAT: chi can thay ham doc_tu_nguon_that() va dat bien moi truong
CHE_DO=that. Cau truc file dau ra khong doi, nen phan giao dien web khong phai
sua gi.

Dau ra:
  data/realtime.json          - trang thai hien tai + chuoi 24 gio
  data/history/YYYY-MM.csv    - lich su de ve bieu do dai han

Tinh nao chua co lop ho chua va quan trac thi script bo qua, khong bao loi.

Chay:  python scripts/03_lay_realtime.py
Chi dung thu vien chuan Python.
"""

import csv
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
THU_MUC_HISTORY = None

MUI_GIO_VN = timezone(timedelta(hours=7))
CHE_DO = os.environ.get("CHE_DO", "mo_phong")

# Nguong canh bao, co the chinh theo quy dinh dieu tiet cua tung ho
NGUONG_HO_THIEU_NUOC = 0.30      # ty le dung tich huu ich
NGUONG_HO_THEO_DOI = 0.50
NGUONG_HO_GAN_TRAN = 0.95
NGUONG_WQI_XAU = 50             # QD 1460/QD-TCMT: duoi 50 la xau
NGUONG_WQI_TRUNG_BINH = 75


# ----------------------------------------------------------------------------
# Tien ich
# ----------------------------------------------------------------------------

def doc_geojson(ten_tep):
    duong_dan = os.path.join(THU_MUC_DATA, ten_tep)
    with open(duong_dan, "r", encoding="utf-8") as f:
        return json.load(f)


def nhieu_on_dinh(khoa, bien_do):
    """Sinh nhieu ngau nhien nhung on dinh theo khoa, de chuoi so khong giat."""
    rng = random.Random(khoa)
    return rng.uniform(-bien_do, bien_do)


def he_so_mua(thoi_diem):
    """He so theo mua: cao nhat thang 12, thap nhat thang 6 (Nam Trung Bo)."""
    ngay_trong_nam = thoi_diem.timetuple().tm_yday
    return math.cos(2 * math.pi * (ngay_trong_nam - 345) / 365)


def he_so_gio(thoi_diem):
    """Bien thien trong ngay, dinh vao chieu."""
    gio = thoi_diem.hour + thoi_diem.minute / 60
    return math.sin(2 * math.pi * (gio - 8) / 24)


# ----------------------------------------------------------------------------
# Mo phong tung loai doi tuong
# ----------------------------------------------------------------------------

def mo_phong_ho_chua(props, thoi_diem):
    """Muc nuoc va ty le dung tich huu ich cua ho chua."""
    ma = props["ma"]
    w_huu_ich = props["w_huu_ich_trieu_m3"]
    h_nguong = props["h_nguong_tran_m"]

    # Ty le dung tich: nen theo mua + lech rieng tung ho
    nen = 0.58 + 0.30 * he_so_mua(thoi_diem)
    lech = nhieu_on_dinh("ho_" + ma, 0.22)
    ty_le = max(0.05, min(1.0, nen + lech + 0.01 * he_so_gio(thoi_diem)))

    # Muc nuoc suy ra tu ty le, gia dinh quan he gan tuyen tinh phia tren muc chet
    h_chet = h_nguong * 0.55
    muc_nuoc = round(h_chet + (h_nguong - h_chet) * ty_le, 2)

    if ty_le < NGUONG_HO_THIEU_NUOC:
        trang_thai = "canh_bao"
    elif ty_le < NGUONG_HO_THEO_DOI:
        trang_thai = "theo_doi"
    elif ty_le > NGUONG_HO_GAN_TRAN:
        trang_thai = "canh_bao"
    else:
        trang_thai = "binh_thuong"

    return {
        "loai": "ho_chua",
        "ten": props["ten"],
        "muc_nuoc_m": muc_nuoc,
        "ty_le_dung_tich": round(ty_le, 3),
        "w_hien_tai_trieu_m3": round(w_huu_ich * ty_le, 2),
        "w_huu_ich_trieu_m3": w_huu_ich,
        "h_nguong_tran_m": h_nguong,
        "trang_thai": trang_thai,
        "chuoi": chuoi_24_gio(thoi_diem, lambda t: round(
            h_chet + (h_nguong - h_chet) * max(0.05, min(1.0,
                0.58 + 0.30 * he_so_mua(t) + lech + 0.01 * he_so_gio(t))), 2)),
        "don_vi_chuoi": "m",
        "nhan_chuoi": "Mực nước hồ",
    }


def mo_phong_thuy_van(props, thoi_diem):
    """Muc nuoc va luu luong tai tram thuy van."""
    ma = props["ma"]
    q_nen = 8.0 + 12.0 * abs(nhieu_on_dinh("q_" + ma, 1.0))
    he_so = 1.0 + 0.75 * he_so_mua(thoi_diem) + 0.08 * he_so_gio(thoi_diem)
    q = max(0.3, q_nen * he_so)
    h = round(0.8 + 0.55 * math.log1p(q), 2)

    if q > q_nen * 2.2:
        trang_thai = "canh_bao"
    elif q < q_nen * 0.35:
        trang_thai = "theo_doi"
    else:
        trang_thai = "binh_thuong"

    return {
        "loai": "thuy_van",
        "ten": props["ten"],
        "h_m": h,
        "q_m3s": round(q, 2),
        "trang_thai": trang_thai,
        "chuoi": chuoi_24_gio(thoi_diem, lambda t: round(max(0.3, q_nen * (
            1.0 + 0.75 * he_so_mua(t) + 0.08 * he_so_gio(t))), 2)),
        "don_vi_chuoi": "m3/s",
        "nhan_chuoi": "Lưu lượng",
    }


def mo_phong_mua(props, thoi_diem):
    """Luong mua 1 gio va tich luy 24 gio."""
    ma = props["ma"]
    kha_nang_mua = max(0.0, 0.5 + 0.5 * he_so_mua(thoi_diem))
    rng = random.Random(ma + thoi_diem.strftime("%Y%m%d%H"))
    mua_1h = round(rng.random() ** 3 * 45 * kha_nang_mua, 1)
    mua_24h = round(sum(
        random.Random(ma + (thoi_diem - timedelta(hours=i)).strftime("%Y%m%d%H")).random() ** 3
        * 45 * kha_nang_mua for i in range(24)), 1)

    if mua_24h > 100:
        trang_thai = "canh_bao"
    elif mua_24h > 50:
        trang_thai = "theo_doi"
    else:
        trang_thai = "binh_thuong"

    return {
        "loai": "mua",
        "ten": props["ten"],
        "mua_1h_mm": mua_1h,
        "mua_24h_mm": mua_24h,
        "trang_thai": trang_thai,
        "chuoi": chuoi_24_gio(thoi_diem, lambda t: round(
            random.Random(ma + t.strftime("%Y%m%d%H")).random() ** 3
            * 45 * max(0.0, 0.5 + 0.5 * he_so_mua(t)), 1)),
        "don_vi_chuoi": "mm",
        "nhan_chuoi": "Lượng mưa giờ",
    }


def mo_phong_chat_luong_nuoc(props, thoi_diem):
    """Chi so WQI va cac thong so chat luong nuoc co ban."""
    ma = props["ma"]
    wqi_nen = 68 + 22 * nhieu_on_dinh("wqi_" + ma, 1.0)
    # Mua mua pha loang chat o nhiem nen WQI tot hon
    wqi = max(12, min(98, wqi_nen + 8 * he_so_mua(thoi_diem)))
    do_oxy = round(4.5 + 0.035 * wqi + nhieu_on_dinh("do_" + ma, 0.4), 2)
    bod5 = round(max(1.0, 26 - 0.22 * wqi + nhieu_on_dinh("bod_" + ma, 1.5)), 2)
    amoni = round(max(0.02, 3.2 - 0.030 * wqi + nhieu_on_dinh("nh4_" + ma, 0.3)), 3)

    if wqi < NGUONG_WQI_XAU:
        trang_thai = "canh_bao"
    elif wqi < NGUONG_WQI_TRUNG_BINH:
        trang_thai = "theo_doi"
    else:
        trang_thai = "binh_thuong"

    return {
        "loai": "chat_luong_nuoc",
        "ten": props["ten"],
        "wqi": round(wqi),
        "phan_loai_wqi": phan_loai_wqi(wqi),
        "do_mg_l": do_oxy,
        "bod5_mg_l": bod5,
        "amoni_mg_l": amoni,
        "trang_thai": trang_thai,
        "chuoi": chuoi_24_gio(thoi_diem, lambda t: round(max(12, min(98,
            wqi_nen + 8 * he_so_mua(t)))), buoc_gio=3),
        "don_vi_chuoi": "WQI",
        "nhan_chuoi": "Chỉ số WQI",
    }


def phan_loai_wqi(wqi):
    """Phan loai theo Quyet dinh 1460/QD-TCMT ngay 12/11/2019."""
    if wqi >= 91:
        return "Rất tốt"
    if wqi >= 76:
        return "Tốt"
    if wqi >= 51:
        return "Trung bình"
    if wqi >= 26:
        return "Xấu"
    if wqi >= 10:
        return "Kém"
    return "Ô nhiễm rất nặng"


# Khong mo phong so do khai_thac: lop khai_thac nay la kiem ke THAT (script 05),
# khong co so do theo thoi gian, mo phong se tao so lieu gia cho cong trinh that.


def chuoi_24_gio(thoi_diem, ham_gia_tri, buoc_gio=1):
    """Tao chuoi gia tri 24 gio gan nhat de ve bieu do."""
    nhan = []
    gia_tri = []
    so_diem = 24 // buoc_gio
    for i in range(so_diem, -1, -1):
        t = thoi_diem - timedelta(hours=i * buoc_gio)
        nhan.append(t.strftime("%H:%M"))
        gia_tri.append(ham_gia_tri(t))
    return {"nhan": nhan, "gia_tri": gia_tri}


# ----------------------------------------------------------------------------
# Sinh canh bao tu trang thai cac doi tuong
# ----------------------------------------------------------------------------

def tao_canh_bao(doi_tuong):
    ds = []
    for ma, dt in doi_tuong.items():
        if dt["trang_thai"] == "binh_thuong":
            continue
        muc = "canh_bao" if dt["trang_thai"] == "canh_bao" else "theo_doi"
        if dt["loai"] == "ho_chua":
            pt = dt["ty_le_dung_tich"]
            if pt > NGUONG_HO_GAN_TRAN:
                noi_dung = "Dung tích đạt {:.0f}% dung tích hữu ích, gần ngưỡng tràn".format(pt * 100)
            else:
                noi_dung = "Dung tích còn {:.0f}% dung tích hữu ích".format(pt * 100)
        elif dt["loai"] == "chat_luong_nuoc":
            noi_dung = "WQI = {} ({})".format(dt["wqi"], dt["phan_loai_wqi"])
        elif dt["loai"] == "thuy_van":
            noi_dung = "Lưu lượng {} m3/s".format(dt["q_m3s"])
        elif dt["loai"] == "mua":
            noi_dung = "Mưa 24 giờ đạt {} mm".format(dt["mua_24h_mm"])
        elif dt["loai"] == "khai_thac":
            noi_dung = "Khai thác đạt {:.0f}% hạn mức giấy phép".format(dt["ty_le_su_dung"] * 100)
        else:
            noi_dung = "Cần theo dõi"
        ds.append({"ma": ma, "ten": dt["ten"], "loai": dt["loai"],
                   "muc": muc, "noi_dung": noi_dung})
    # Canh bao muc cao hien truoc
    ds.sort(key=lambda c: (c["muc"] != "canh_bao", c["ten"]))
    return ds


# ----------------------------------------------------------------------------
# Ghi lich su
# ----------------------------------------------------------------------------

def ghi_lich_su(thoi_diem, doi_tuong):
    """Noi them mot dong cho moi doi tuong vao file CSV theo thang."""
    os.makedirs(THU_MUC_HISTORY, exist_ok=True)
    duong_dan = os.path.join(THU_MUC_HISTORY, thoi_diem.strftime("%Y-%m") + ".csv")
    da_co = os.path.exists(duong_dan)
    cot = ["thoi_diem", "ma", "loai", "ten", "gia_tri_chinh", "don_vi", "trang_thai"]
    with open(duong_dan, "a", encoding="utf-8-sig", newline="") as f:
        ghi = csv.DictWriter(f, fieldnames=cot)
        if not da_co:
            ghi.writeheader()
        for ma, dt in doi_tuong.items():
            ghi.writerow({
                "thoi_diem": thoi_diem.isoformat(timespec="minutes"),
                "ma": ma,
                "loai": dt["loai"],
                "ten": dt["ten"],
                "gia_tri_chinh": dt["chuoi"]["gia_tri"][-1],
                "don_vi": dt["don_vi_chuoi"],
                "trang_thai": dt["trang_thai"],
            })
    return duong_dan


# ----------------------------------------------------------------------------
# Doc tu nguon that - cho cai dat sau
# ----------------------------------------------------------------------------

def doc_tu_nguon_that():
    """
    Diem mo rong khi co nguon du lieu that.

    Can thuc hien:
      1. Goi API quan trac (requests.get) hoac doc file do don vi cung cap
      2. Anh xa ma tram cua nguon ve truong "ma" trong cac lop GeoJSON
      3. Tra ve dict co cung cau truc voi phan mo phong o tren
    """
    raise NotImplementedError(
        "Chua ket noi nguon that. Dat CHE_DO=mo_phong hoac cai dat ham nay.")


# ----------------------------------------------------------------------------
# Chay chinh
# ----------------------------------------------------------------------------

def main():
    global THU_MUC_DATA, THU_MUC_HISTORY
    tt = mod_tinh.nap()
    THU_MUC_DATA = tt["_thu_muc_data"]
    THU_MUC_HISTORY = os.path.join(THU_MUC_DATA, "history")

    # Khong co lop quan trac thi khong co gi de cap nhat
    co_ho_chua = "ho_chua" in tt["lop_co_san"]
    can_co = ["ho_chua.geojson"] if co_ho_chua else []
    thieu = [t for t in can_co if not os.path.exists(os.path.join(THU_MUC_DATA, t))]
    if thieu:
        print("Bo qua: {} chua co cac lop {}".format(tt["ten_tinh"], ", ".join(thieu)))
        return

    thoi_diem = datetime.now(MUI_GIO_VN).replace(second=0, microsecond=0)

    if CHE_DO == "that":
        doi_tuong = doc_tu_nguon_that()
    else:
        doi_tuong = {}
        # ho_chua la lop mo phong da bi go khoi lop_co_san (thay bang ao_ho that)
        if co_ho_chua:
            for f in doc_geojson("ho_chua.geojson")["features"]:
                p = f["properties"]
                doi_tuong[p["ma"]] = mo_phong_ho_chua(p, thoi_diem)

        # quan_trac la lop THAT (scripts/10) chi co vi tri tram, khong mo phong so do.
        # So do that xem o tab Quan trac.

    canh_bao = tao_canh_bao(doi_tuong)

    ket_qua = {
        "thoi_diem": thoi_diem.isoformat(timespec="minutes"),
        "che_do": CHE_DO,
        "nguon_dl": ("Số liệu mô phỏng - chưa kết nối nguồn quan trắc chính thức"
                     if CHE_DO != "that" else "Nguồn quan trắc chính thức"),
        "so_doi_tuong": len(doi_tuong),
        "doi_tuong": doi_tuong,
        "canh_bao": canh_bao,
    }

    duong_dan = os.path.join(THU_MUC_DATA, "realtime.json")
    with open(duong_dan, "w", encoding="utf-8") as f:
        json.dump(ket_qua, f, ensure_ascii=False, separators=(",", ":"))

    tep_ls = ghi_lich_su(thoi_diem, doi_tuong)

    print("Cap nhat du lieu thoi gian thuc - che do: {}".format(CHE_DO))
    print("  Thoi diem    : {}".format(ket_qua["thoi_diem"]))
    print("  So doi tuong : {}".format(len(doi_tuong)))
    print("  So canh bao  : {} (muc canh bao: {})".format(
        len(canh_bao), sum(1 for c in canh_bao if c["muc"] == "canh_bao")))
    print("  Ghi ra       : {} ({:.1f} KB)".format(
        duong_dan, os.path.getsize(duong_dan) / 1024))
    print("  Lich su      : {}".format(tep_ls))


if __name__ == "__main__":
    main()
