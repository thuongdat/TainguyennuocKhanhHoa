"""Thiet dat chung cho bo kiem thu backend.

Nguyen tac: KHONG test nao duoc ket noi vao CSDL QTQG that. QTQG la he thong
dang chay cua co quan khac, bo kiem thu phai chay duoc tren may bat ky va
khong dung den no. Moi test chay o CHE_DO=thu_nghiem.
"""

import os
import sys

# Dat bien moi truong TRUOC khi nap cau_hinh, vi cau_hinh doc os.environ ngay
# luc nap mo-dun. load_dotenv() khong ghi de bien da co nen backend/.env khong
# lam sai lech dieu nay.
os.environ["CHE_DO"] = "thu_nghiem"

GOC_BACKEND = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, GOC_BACKEND)


def cac_chuoi_bi_mat():
    """Nhung chuoi khong duoc phep xuat hien trong bat ky thu gi gui ra
    trinh duyet: dia chi may chu, ten tai khoan, mat khau, cong.

    Doc tu cau_hinh chu KHONG viet cung vao tep test, vi tep test duoc commit
    con backend/.env thi khong. Gia tri rong bi bo qua: chuoi rong nam trong
    moi van ban nen se lam test bao dong gia.
    """
    import cau_hinh
    cac = [cau_hinh.QTQG_MAY_CHU, cau_hinh.QTQG_TAI_KHOAN,
           cau_hinh.QTQG_MAT_KHAU, str(cau_hinh.QTQG_CONG)]
    return [c for c in cac if c and len(c) >= 3]
