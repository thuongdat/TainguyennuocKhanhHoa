"""Tich luy chuoi so do vao SQLite de ve bieu do theo thoi gian.

Ly do: du lieu san co cua du an chi co MOT ky quan trac (data/history chi co
nam_2025.csv), nen khong co chuoi nao de ve bieu do. Neu CSDL QTQG luu du lich
su thi lay_chuoi() doc thang QTQG va tep nay chi la bo dem; neu QTQG chi giu
gia tri moi nhat thi day la cach duy nhat de bieu do co du lieu.

Tep sqlite nam trong backend/ va da duoc gitignore. Day la CSDL cuc bo cua
backend, hoan toan tach biet voi CSDL QTQG, khong bao gio ghi gi len QTQG.
"""

import os
import sqlite3

import cau_hinh

# UNIQUE de chay lai nhieu lan khong nhan ban dong. Moi lan lay so do, mot
# phan lon ban ghi la lap lai cua lan truoc, INSERT OR IGNORE bo qua chung.
_SO_DO_SQL = """
CREATE TABLE IF NOT EXISTS so_do (
    ma           TEXT    NOT NULL,
    thoi_diem    TEXT    NOT NULL,
    ten_thong_so TEXT    NOT NULL,
    gia_tri      REAL,
    UNIQUE (ma, thoi_diem, ten_thong_so)
)
"""

_CHI_MUC_SQL = """
CREATE INDEX IF NOT EXISTS chi_muc_so_do_tram
    ON so_do (ma, ten_thong_so, thoi_diem)
"""

# Truong khong phai so do, khong ghi vao chuoi thoi gian
TRUONG_BO_QUA = {"ma", "ten", "loai", "loai_tram", "song_ho", "thong_so",
                 "ten_luu_vuc", "don_vi_quan_ly", "thoi_diem", "trang_thai",
                 "phan_loai_wqi", "wqi_thieu_thong_so", "vi_tri_do",
                 "ky_quan_trac", "ma_dia_phuong", "kinh_do", "vi_do",
                 "nguon_dl", "che_do"}


def _mo():
    thu_muc = os.path.dirname(cau_hinh.DUONG_DAN_SQLITE)
    if thu_muc:
        os.makedirs(thu_muc, exist_ok=True)
    kn = sqlite3.connect(cau_hinh.DUONG_DAN_SQLITE)
    kn.row_factory = sqlite3.Row
    return kn


def dung_bang():
    """Tao bang va chi muc neu chua co. Goi duoc nhieu lan."""
    with _mo() as kn:
        kn.execute(_SO_DO_SQL)
        kn.execute(_CHI_MUC_SQL)


def ghi_mot_luot(cac_ban_ghi, thoi_diem_chung=None):
    """Ghi them so do cua mot luot lay du lieu.

    cac_ban_ghi la danh sach ban ghi da chuan hoa. Moi thong so so hoc trong
    ban ghi thanh mot dong. Tra ve so dong thuc su duoc them moi.
    """
    dung_bang()

    cac_dong = []
    for bg in cac_ban_ghi:
        ma = bg.get("ma")
        if not ma:
            continue
        thoi_diem = bg.get("thoi_diem") or thoi_diem_chung
        if not thoi_diem:
            continue
        for ten, gia_tri in bg.items():
            if ten in TRUONG_BO_QUA:
                continue
            if not isinstance(gia_tri, (int, float)) or isinstance(gia_tri, bool):
                continue
            cac_dong.append((ma, str(thoi_diem), ten, float(gia_tri)))

    if not cac_dong:
        return 0

    with _mo() as kn:
        truoc = kn.execute("SELECT COUNT(*) AS n FROM so_do").fetchone()["n"]
        kn.executemany(
            "INSERT OR IGNORE INTO so_do (ma, thoi_diem, ten_thong_so, "
            "gia_tri) VALUES (?, ?, ?, ?)", cac_dong)
        sau = kn.execute("SELECT COUNT(*) AS n FROM so_do").fetchone()["n"]

    return sau - truoc


def doc_chuoi(ma, ten_thong_so, tu=None, den=None, gioi_han=2000):
    """Chuoi thoi gian cua mot tram, mot thong so, sap theo thoi diem tang."""
    dung_bang()

    cau = ["SELECT thoi_diem, gia_tri FROM so_do",
           "WHERE ma = ? AND ten_thong_so = ?"]
    tham_so = [ma, ten_thong_so]

    if tu:
        cau.append("AND thoi_diem >= ?")
        tham_so.append(str(tu))
    if den:
        cau.append("AND thoi_diem <= ?")
        tham_so.append(str(den))

    cau.append("ORDER BY thoi_diem ASC LIMIT ?")
    tham_so.append(int(gioi_han))

    with _mo() as kn:
        cac_dong = kn.execute(" ".join(cau), tham_so).fetchall()

    return [{"thoi_diem": d["thoi_diem"], "gia_tri": d["gia_tri"]}
            for d in cac_dong]


def thong_so_co_chuoi(ma):
    """Cac thong so da tich luy duoc cho mot tram, kem so diem."""
    dung_bang()
    with _mo() as kn:
        cac_dong = kn.execute(
            "SELECT ten_thong_so, COUNT(*) AS so_diem FROM so_do "
            "WHERE ma = ? GROUP BY ten_thong_so ORDER BY ten_thong_so",
            (ma,)).fetchall()
    return [{"ten_thong_so": d["ten_thong_so"], "so_diem": d["so_diem"]}
            for d in cac_dong]
