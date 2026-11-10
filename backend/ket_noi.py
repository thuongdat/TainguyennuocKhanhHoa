"""Mo ket noi tai CSDL Quan trac Quoc gia, CHI DOC.

Day la lop chan cuoi cung. CSDL QTQG la he thong dang chay that, backend nay
chi co nhiem vu doc. Co default_transaction_read_only=on dat ngay o tang ket
noi, nen du mot cho nao trong ma nguon viet sai thanh cau lenh ghi thi
PostgreSQL van tu choi. Dung bo co nay.

statement_timeout chan mot cau truy van nang treo ket noi va lam nang CSDL.
"""

import re

import cau_hinh

# -c ... la tham so khoi tao phien lam viec, PostgreSQL ap dung ngay khi ket noi
TUY_CHON = " ".join([
    "-c default_transaction_read_only=on",   # khong ghi duoc gi, ke ca do loi ma
    "-c statement_timeout=15000",            # 15 giay moi cau truy van
    "-c idle_in_transaction_session_timeout=20000",
])

# Tu khoa khong duoc xuat hien trong bat ky cau SQL nao gui len QTQG
TU_KHOA_CAM = ["insert", "update", "delete", "drop", "alter", "truncate",
               "create", "grant", "revoke"]


class LoiKetNoi(Exception):
    """Khong mo duoc ket noi hoac truy van that bai."""


def _kiem_tra_cau_sql(cau_sql):
    """Chan cau lenh ghi ngay tren duong ra. Hai lop bao ve van hon mot lop:
    co read_only cua PostgreSQL va kiem tra nay o phia Python.

    So khop theo bien tu (\b) de ten cot nhu "updated_at" hay "created_by"
    khong bi bao dong gia.
    """
    chu = cau_sql.lower()
    for tu in TU_KHOA_CAM:
        if re.search(r"\b" + tu + r"\b", chu):
            raise LoiKetNoi(
                "Câu truy vấn chứa từ khóa ghi dữ liệu: {}".format(tu))
    return cau_sql


def mo_ket_noi():
    """Tra ve ket noi psycopg moi, da khoa che do chi doc.

    Nguoi goi dung trong cau lenh with de ket noi tu dong dong lai.
    """
    thieu = cau_hinh.thieu_thong_tin_ket_noi()
    if thieu:
        raise LoiKetNoi(
            "Thiếu thông tin kết nối: {}. Điền vào backend/.env."
            .format(", ".join(thieu)))

    try:
        import psycopg
        from psycopg.rows import dict_row
    except ImportError as e:
        raise LoiKetNoi(
            "Chưa cài thư viện psycopg. Chạy: conda env update "
            "-f environment.yml -n tainguyennuoc") from e

    try:
        return psycopg.connect(
            host=cau_hinh.QTQG_MAY_CHU,
            port=cau_hinh.QTQG_CONG,
            dbname=cau_hinh.QTQG_CSDL,
            user=cau_hinh.QTQG_TAI_KHOAN,
            password=cau_hinh.QTQG_MAT_KHAU,
            connect_timeout=10,
            options=TUY_CHON,
            row_factory=dict_row,
        )
    except Exception as e:
        # Khong dua nguyen van loi cua psycopg ra ngoai: no co the chua ten
        # tai khoan va dia chi may chu.
        raise LoiKetNoi("Không kết nối được cơ sở dữ liệu QTQG") from e


def truy_van(cau_sql, tham_so=None, gioi_han=None):
    """Chay mot cau SELECT, tra ve danh sach dict.

    Tham so luon truyen qua placeholder %s, khong bao gio noi chuoi vao SQL.
    """
    _kiem_tra_cau_sql(cau_sql)
    with mo_ket_noi() as kn:
        with kn.cursor() as con_tro:
            con_tro.execute(cau_sql, tham_so or ())
            if gioi_han:
                return con_tro.fetchmany(gioi_han)
            return con_tro.fetchall()
