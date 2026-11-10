# -*- coding: utf-8 -*-
"""
Xuat mang quan trac nuoc duoi dat cua QTQG thanh lop tinh cho ban do chinh.

Dau vao : CSDL Quan trac Quoc gia, bang monitoring_well va cac bang so do
Dau ra  : data/quan_trac_ndd.geojson, EPSG:4326

Chay:
    set CHE_DO=that
    D:\\Anaconda_Data\\envs\\tainguyennuoc\\python.exe scripts/08_xuat_lo_khoan_ndd.py

VI SAO CAN SCRIPT NAY

Tab Quan trac (pages/quan-trac.html) goi thang backend nen luon co so moi
nhat. Ban do chinh (index.html) thi THUAN TINH: no chi doc data/*.geojson va
khong duoc phep phu thuoc mot dich vu dang chay, neu khong thi tat backend la
ban do chinh hong. Vi vay lo khoan len ban do chinh qua mot lop tinh, sinh lai
bang script nay khi can.

Hai he qua phai chap nhan va da duoc noi ro tren giao dien:

  1. So do trong lop tinh la so do o THOI DIEM XUAT, khong tu cap nhat. Moi
     doi tuong mang truong nguon_dl ghi ro ngay xuat, va giu rieng
     thoi_diem_muc_nuoc, thoi_diem_chat_luong de nguoi dung thay ky do that.
  2. Muon so moi nhat thi xem tab Quan trac.

KHONG nhan ban hieu biet ve schema QTQG o day. Script goi hai ham cong khai
cua backend/nguon_qtqg.py, la mo-dun duy nhat biet CSDL QTQG co hinh dang gi.
Nho vay doi schema chi phai sua mot cho.

Script nay KHONG dung GeoPandas: truy van SQL da ST_Transform san ve EPSG:4326
nen khong can pyproj, va cung khong dinh bay PROJ_LIB cua may nay.
"""

import json
import os
import sys
from datetime import datetime, timedelta, timezone

GOC_DU_AN = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
GOC_BACKEND = os.path.join(GOC_DU_AN, "backend")
TEP_RA = os.path.join(GOC_DU_AN, "data", "quan_trac_ndd.geojson")

MUI_GIO_VN = timezone(timedelta(hours=7))

# Thuoc tinh tinh cua lo khoan, lay tu bang monitoring_well
TRUONG_TRAM = ["ma", "ten", "loai_tram", "tang_chua_nuoc",
               "cao_do_mieng_lk_m", "vi_tri_hc", "ten_luu_vuc",
               "mang_quan_trac", "thiet_bi_do", "ngay_bat_dau"]

# So do nhung KHONG dua vao lop tinh: cac truong noi bo cua backend
TRUONG_BO_QUA = {"ma", "ten", "loai", "loai_tram", "nguon", "kinh_do",
                 "vi_do", "nguon_dl"}


def _nap_backend():
    """Nap mo-dun cua backend. Phai dat CHE_DO truoc khi nap cau_hinh, vi
    cau_hinh doc os.environ ngay luc nap mo-dun."""
    if not os.environ.get("CHE_DO"):
        os.environ["CHE_DO"] = "that"
    sys.path.insert(0, GOC_BACKEND)

    import cau_hinh
    if not cau_hinh.la_nguon_that():
        raise SystemExit(
            "Script nay can nguon that. Dat CHE_DO=that roi chay lai.")

    thieu = cau_hinh.thieu_thong_tin_ket_noi()
    if thieu:
        raise SystemExit(
            "Thieu thong tin ket noi: {}. Dien vao backend/.env."
            .format(", ".join(thieu)))

    import nguon_qtqg
    return cau_hinh, nguon_qtqg


def _mot_feature(lo, so_do, cau_nguon):
    kinh_do = lo.get("kinh_do")
    vi_do = lo.get("vi_do")
    if kinh_do is None or vi_do is None:
        return None

    thuoc_tinh = {}
    for ten in TRUONG_TRAM:
        thuoc_tinh[ten] = lo.get(ten)

    # So do moi nhat, nhap thang vao thuoc tinh de cong cu truy van bang nhap
    # chuot doc duoc ma khong can tep realtime rieng.
    for ten, gia_tri in (so_do or {}).items():
        if ten in TRUONG_BO_QUA:
            continue
        if thuoc_tinh.get(ten) is None:
            thuoc_tinh[ten] = gia_tri

    thuoc_tinh["nguon_dl"] = cau_nguon

    return {
        "type": "Feature",
        "properties": thuoc_tinh,
        "geometry": {
            "type": "Point",
            "coordinates": [round(float(kinh_do), 6), round(float(vi_do), 6)],
        },
    }


def main():
    cau_hinh, nguon_qtqg = _nap_backend()

    print("[08] Xuat mang quan trac nuoc duoi dat tu QTQG")

    cac_lo = nguon_qtqg.lay_danh_sach_lo_khoan()
    print("   Lo khoan dang hoat dong: {}".format(len(cac_lo)))
    if not cac_lo:
        raise SystemExit("Khong lay duoc lo khoan nao, khong ghi de tep cu.")

    # Cung quy tac an so do qua cu nhu tab Quan trac, xem
    # backend/cau_hinh.py SO_DO_CU_TOI_DA_NGAY. Lo khoan van duoc xuat, chi la
    # khong mang so do nao di kem.
    import tong_hop
    con_hieu_luc, qua_cu = tong_hop.tach_ban_ghi_qua_cu(
        nguon_qtqg.lay_so_do_lo_khoan())
    cac_so_do = {bg["ma"]: bg for bg in con_hieu_luc if bg.get("ma")}
    print("   Lo khoan co so do:       {}".format(len(cac_so_do)))
    if qua_cu:
        print("   An so do qua cu ({} ngay): {}".format(
            cau_hinh.SO_DO_CU_TOI_DA_NGAY,
            ", ".join("{} ({})".format(bg.get("ma"), bg.get("thoi_diem"))
                      for bg in qua_cu)))

    luc_xuat = datetime.now(MUI_GIO_VN)
    cau_nguon = ("Mạng quan trắc nước dưới đất quốc gia, cơ sở dữ liệu phần "
                 "mềm Quan trắc Quốc gia (QTQG). Số đo trong lớp này là số "
                 "tại thời điểm xuất {}; số mới nhất xem tab Quan trắc."
                 .format(luc_xuat.strftime("%d/%m/%Y")))

    cac_feature = []
    bo_thieu_toa_do = 0
    for lo in cac_lo:
        f = _mot_feature(lo, cac_so_do.get(lo.get("ma")), cau_nguon)
        if f is None:
            bo_thieu_toa_do += 1
            continue
        cac_feature.append(f)

    if bo_thieu_toa_do:
        print("   Bo vi thieu toa do:      {}".format(bo_thieu_toa_do))

    tap = {
        "type": "FeatureCollection",
        "name": "quan_trac_ndd",
        "crs": {"type": "name",
                "properties": {"name": "urn:ogc:def:crs:OGC:1.3:CRS84"}},
        "nguon_dl": cau_nguon,
        "thoi_diem_xuat": luc_xuat.isoformat(timespec="minutes"),
        "features": cac_feature,
    }

    os.makedirs(os.path.dirname(TEP_RA), exist_ok=True)
    with open(TEP_RA, "w", encoding="utf-8") as f:
        json.dump(tap, f, ensure_ascii=False, indent=1)

    print("   Da ghi {} voi {} doi tuong".format(TEP_RA, len(cac_feature)))

    co_muc_nuoc = sum(1 for f in cac_feature
                      if f["properties"].get("h_ngam_m") is not None)
    co_hoa_hoc = sum(1 for f in cac_feature
                     if f["properties"].get("ph") is not None)
    print("   Co muc nuoc: {} | co ket qua phan tich: {}".format(
        co_muc_nuoc, co_hoa_hoc))


if __name__ == "__main__":
    main()
