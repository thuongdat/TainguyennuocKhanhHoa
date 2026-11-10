# -*- coding: utf-8 -*-
r"""
Dat mat khau cho chuc nang xuat CSV/GeoJSON cua trang web.

Ghi muoi va ma bam PBKDF2-SHA256 vao tinh.json (khoa xuat_du_lieu). Mat khau
KHONG duoc ghi o dau ca, chi ma bam. Trinh duyet bam lai mat khau nguoi dung
nhap bang Web Crypto voi cung tham so roi so sanh, xem assets/js/xuat_tep.js.

Chay (go mat khau hai lan, khong hien tren man hinh):
    D:\Anaconda_Data\envs\tainguyennuoc\python.exe scripts/11_dat_mat_khau_xuat.py

Chi can thu vien chuan, khong can GeoPandas.

LUU Y: day la cong o phia trinh duyet, khong chan duoc nguoi co y (cac tep
data/*.geojson van tai thang duoc). Xem ghi chu dau assets/js/xuat_tep.js.
Ma bam nam trong tinh.json la tep cong khai; hay dung mat khau DAI, khong dung
lai mat khau o noi khac.
"""

import getpass
import hashlib
import json
import os
import sys

GOC = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TEP = os.path.join(GOC, "tinh.json")
SO_VONG = 200000
DO_DAI_TOI_THIEU = 8


def doc_mat_khau():
    """Hai lan tren terminal; khi stdin khong phai terminal thi doc mot dong."""
    if sys.stdin.isatty():
        a = getpass.getpass("Mat khau xuat du lieu: ")
        b = getpass.getpass("Nhap lai: ")
        if a != b:
            raise SystemExit("Hai lan nhap khong khop, khong thay doi gi.")
        return a
    return sys.stdin.readline().rstrip("\r\n")


def main():
    mat_khau = doc_mat_khau()
    if len(mat_khau) < DO_DAI_TOI_THIEU:
        raise SystemExit("Mat khau qua ngan (can tu {} ky tu), khong thay doi gi."
                         .format(DO_DAI_TOI_THIEU))

    muoi = os.urandom(16)
    ma_bam = hashlib.pbkdf2_hmac("sha256", mat_khau.encode("utf-8"), muoi, SO_VONG)

    with open(TEP, encoding="utf-8") as f:
        tt = json.load(f)
    khoi = tt.setdefault("xuat_du_lieu", {})
    khoi["yeu_cau_mat_khau"] = True
    khoi["muoi"] = muoi.hex()
    khoi["ma_bam"] = ma_bam.hex()
    khoi["so_vong"] = SO_VONG
    with open(TEP, "w", encoding="utf-8") as f:
        json.dump(tt, f, ensure_ascii=False, indent=2)
        f.write("\n")

    print("Da ghi muoi va ma bam vao {}".format(TEP))
    print("Nguoi dung dang mo trang se phai nhap lai mat khau (doi mat khau la het hieu luc).")


if __name__ == "__main__":
    main()
