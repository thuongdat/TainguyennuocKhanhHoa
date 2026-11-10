# -*- coding: utf-8 -*-
"""
Nap tham so cua tinh.

Tep tinh.json o goc du an la nguon su that duy nhat ve tham so cua tinh:
ca script Python va trinh duyet deu doc cung tep do, nen khong bao gio xay ra
chuyen khai bao mot dang o Python va mot dang o JavaScript.

Moi du an phuc vu dung mot tinh. Muon lam tinh khac thi tao mot ban sao cua
du an roi sua tinh.json, chu khong them tinh vao day.
"""

import json
import os

GOC = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TEP_THAM_SO = os.path.join(GOC, "tinh.json")


def nap(in_thong_bao=True):
    """Nap tham so cua tinh, tra ve dict kem hai khoa tien ich:

      _thu_muc_data : duong dan tuyet doi den data/, da tao san
      _goc          : duong dan tuyet doi den thu muc goc du an
    """
    if not os.path.exists(TEP_THAM_SO):
        raise SystemExit("Khong tim thay tep tham so: {}".format(TEP_THAM_SO))

    with open(TEP_THAM_SO, encoding="utf-8") as f:
        tt = json.load(f)

    tt["_goc"] = GOC
    tt["_thu_muc_data"] = os.path.join(GOC, "data")
    os.makedirs(tt["_thu_muc_data"], exist_ok=True)

    if in_thong_bao:
        print("Tinh: {} ({})".format(tt["ten_tinh"], tt["ma"]))
        print("Du lieu ra: {}".format(tt["_thu_muc_data"]))
        print("-" * 68)

    return tt


def duong_dan_ra(tt, ten_tep):
    """Duong dan day du cua mot tep dau ra trong thu muc data."""
    return os.path.join(tt["_thu_muc_data"], ten_tep)


def tim_tep_nguon(*ung_vien):
    """Tra ve duong dan dau tien ton tai trong danh sach ung vien.

    Cac bo du lieu quoc gia (VietNam.shp, Commune.shp, BaseMapVietNam.gdb) tuy
    du an ma duoc dat trong CSDL/ hay data_goc/. Thay vi gan cung mot duong dan
    roi moi du an lai phai sua script, cho script tu do qua vai vi tri quen
    thuoc. Duong dan truyen vao la duong dan tuong doi so voi goc du an.
    """
    for tuong_doi in ung_vien:
        duong_dan = os.path.join(GOC, *tuong_doi.split("/"))
        if os.path.exists(duong_dan):
            return duong_dan

    print("Khong tim thay tep nguon. Da tim o cac vi tri sau:")
    for tuong_doi in ung_vien:
        print("   ", os.path.join(GOC, *tuong_doi.split("/")))
    raise SystemExit(1)
