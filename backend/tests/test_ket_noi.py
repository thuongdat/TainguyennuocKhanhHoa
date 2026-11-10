"""Kiem thu lop chan ghi du lieu len CSDL QTQG.

CSDL QTQG la he thong dang chay cua co quan khac, backend nay chi duoc doc.
Cac test duoi day la hang rao chong hoi quy: neu sau nay co ai go bo co chi
doc hoac viet mot cau lenh ghi, bo kiem thu phai do ngay.

Khong test nao o day mo ket noi that.
"""

import os
import re

import pytest

import cau_hinh
import ket_noi


# ---------------------------------------------------------------------------
# Co chi doc o tang ket noi
# ---------------------------------------------------------------------------

def test_tuy_chon_ket_noi_khoa_che_do_chi_doc():
    assert "default_transaction_read_only=on" in ket_noi.TUY_CHON


def test_tuy_chon_ket_noi_co_han_thoi_gian_truy_van():
    """Thieu statement_timeout thi mot cau truy van nang se treo ket noi va
    lam nang CSDL dang chay that."""
    assert "statement_timeout" in ket_noi.TUY_CHON


# ---------------------------------------------------------------------------
# Chan cau lenh ghi o phia Python
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("cau_sql", [
    "INSERT INTO tram VALUES (1)",
    "insert into tram values (1)",
    "UPDATE tram SET ten = 'x'",
    "DELETE FROM tram",
    "DROP TABLE tram",
    "ALTER TABLE tram ADD COLUMN x int",
    "TRUNCATE tram",
    "SELECT 1; DROP TABLE tram",          # noi hai cau lenh
    "CREATE TABLE tam AS SELECT 1",
])
def test_chan_cau_lenh_ghi(cau_sql):
    with pytest.raises(ket_noi.LoiKetNoi):
        ket_noi._kiem_tra_cau_sql(cau_sql)


@pytest.mark.parametrize("cau_sql", [
    "SELECT * FROM tram LIMIT 10",
    "SELECT ma, updated_at FROM tram LIMIT 10",     # ten cot chua 'update'
    "SELECT created_by, deleted_flag FROM tram",    # 'create', 'delete'
    "SELECT ma AS ma_tram FROM tram_insertion",     # 'insert' trong ten bang
])
def test_khong_bao_dong_gia_voi_ten_cot(cau_sql):
    """So khop theo bien tu, khong theo chuoi con. Bao dong gia o day se chan
    mat nhung cau SELECT hoan toan hop le."""
    assert ket_noi._kiem_tra_cau_sql(cau_sql) == cau_sql


# ---------------------------------------------------------------------------
# Khong mo-dun nao trong backend chay cau lenh ghi len QTQG
# ---------------------------------------------------------------------------

# luu_tru.py ghi vao SQLite CUC BO cua backend, khong phai QTQG, nen duoc tru
TEP_DUOC_TRU = {"luu_tru.py", "ket_noi.py"}

TU_KHOA_GHI = re.compile(
    r"\b(insert\s+into|update\s+\w+\s+set|delete\s+from|drop\s+table|"
    r"alter\s+table|truncate)\b", re.IGNORECASE)


def test_khong_mo_dun_nao_ghi_len_qtqg():
    """Quet van ban toan bo mo-dun backend. Day la phep kiem tho nhung bat duoc
    dung truong hop dang lo: co ai them mot cau lenh ghi vao duong di cua
    QTQG."""
    vi_pham = []
    for ten_tep in sorted(os.listdir(cau_hinh.GOC_BACKEND)):
        if not ten_tep.endswith(".py") or ten_tep in TEP_DUOC_TRU:
            continue
        duong_dan = os.path.join(cau_hinh.GOC_BACKEND, ten_tep)
        with open(duong_dan, encoding="utf-8") as f:
            noi_dung = f.read()
        for khop in TU_KHOA_GHI.finditer(noi_dung):
            vi_pham.append("{}: {}".format(ten_tep, khop.group(0)))
    assert not vi_pham, "Co cau lenh ghi trong backend: " + "; ".join(vi_pham)


def test_truy_van_sql_chi_co_cau_select():
    """Tep truy_van.sql la noi duy nhat chua SQL gui len QTQG."""
    duong_dan = os.path.join(cau_hinh.GOC_BACKEND, "truy_van.sql")
    with open(duong_dan, encoding="utf-8") as f:
        # Bo dong chu thich, vi chu thich co the nhac den tu khoa de huong dan
        cac_dong = [d for d in f if not d.lstrip().startswith("--")]
    noi_dung = "".join(cac_dong)
    assert not TU_KHOA_GHI.search(noi_dung)


# ---------------------------------------------------------------------------
# Thong tin ket noi
# ---------------------------------------------------------------------------

def test_bao_loi_ro_khi_thieu_thong_tin_ket_noi(monkeypatch):
    for ten in cau_hinh.BIEN_BAT_BUOC:
        monkeypatch.setattr(cau_hinh, ten, "", raising=False)
    with pytest.raises(ket_noi.LoiKetNoi) as loi:
        ket_noi.mo_ket_noi()
    assert "backend/.env" in str(loi.value)


def test_thong_bao_loi_khong_lo_tai_khoan(monkeypatch):
    """Thong bao loi cua tang ket noi co the di ra trinh duyet, khong duoc chua
    mat khau hay dia chi may chu."""
    # Dung gia tri gia, khong dat dia chi may chu that vao tep duoc commit
    monkeypatch.setattr(cau_hinh, "QTQG_MAY_CHU", "may-chu-khong-co-that.test")
    monkeypatch.setattr(cau_hinh, "QTQG_CSDL", "csdl_thu")
    monkeypatch.setattr(cau_hinh, "QTQG_TAI_KHOAN", "nguoi_dung_thu")
    monkeypatch.setattr(cau_hinh, "QTQG_MAT_KHAU", "mat_khau_thu")

    try:
        ket_noi.mo_ket_noi()
    except ket_noi.LoiKetNoi as e:
        chu = str(e)
        assert "mat_khau_thu" not in chu
        assert "nguoi_dung_thu" not in chu
        assert "may-chu-khong-co-that.test" not in chu
