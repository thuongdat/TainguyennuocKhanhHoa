"""Bo nho dem theo thoi gian song (TTL).

Hai ly do ton tai:
  1. CSDL QTQG la he thong dang chay that. Nhieu trinh duyet mo cung luc khong
     duoc bien thanh nhieu luot truy van. Trong mot cua so TTL, moi endpoint
     chi goi nguon dung mot lan.
  2. Trang Quan trac tu lam moi 5 phut. Khong co bo dem thi moi nguoi dung la
     mot luot truy van rieng.

Dich vu chay mot tien trinh uvicorn nen giu trong bo nho la du. Khi nao chay
nhieu tien trinh thi doi sang Redis, chi phai sua mo-dun nay.
"""

import threading
import time

import cau_hinh

_KHO = {}
_KHOA = threading.Lock()


def lay_hoac_tinh(khoa, ham_tinh, ttl_giay=None):
    """Tra ve gia tri trong bo dem con han, neu khong thi goi ham_tinh().

    Ham_tinh() chay NGOAI vung khoa de mot truy van cham khong chan cac yeu
    cau khac. Doi lai, hai yeu cau den cung luc luc bo dem rong co the cung
    goi nguon mot lan; chap nhan duoc, va van hon la khoa ca dich vu lai.
    """
    if ttl_giay is None:
        ttl_giay = cau_hinh.CACHE_GIAY

    bay_gio = time.time()

    with _KHOA:
        o = _KHO.get(khoa)
        if o and bay_gio - o["luc"] < ttl_giay:
            return o["gia_tri"]

    gia_tri = ham_tinh()

    with _KHOA:
        _KHO[khoa] = {"gia_tri": gia_tri, "luc": bay_gio}

    return gia_tri


def tuoi_cua(khoa):
    """So giay ke tu lan tinh gan nhat, None neu chua co trong bo dem."""
    with _KHOA:
        o = _KHO.get(khoa)
    if not o:
        return None
    return time.time() - o["luc"]


def xoa(khoa=None):
    """Xoa mot khoa, hoac xoa toan bo khi khong truyen khoa.

    Nut Lam moi tren giao dien khong goi ham nay: nguoi dung bam lien tuc se
    thanh ra dap vao CSDL QTQG. Ham nay danh cho test va cho viec van hanh.
    """
    with _KHOA:
        if khoa is None:
            _KHO.clear()
        else:
            _KHO.pop(khoa, None)
