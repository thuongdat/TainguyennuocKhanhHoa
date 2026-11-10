r"""Buoc 0: thu ket noi CSDL QTQG va kham pha schema.

Chay mot lan, chi doc, chi in ra man hinh va ghi mot bao cao Markdown ngoai
repo. Khong co cau lenh ghi nao.

Cach chay:
    D:\Anaconda_Data\envs\tainguyennuoc\python.exe backend/kiem_tra_ket_noi.py

Ket qua quyet dinh noi dung cac cau SELECT trong backend/truy_van.sql. Chua
biet CSDL co bang gi thi khong viet truy van duoc.
"""

import io
import os
import sys
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import cau_hinh
import ket_noi

# Tu khoa de nhan ra bang dang quan tam trong mot CSDL co the rat nhieu bang
TU_KHOA_BANG = ["tram", "station", "quan_trac", "quantrac", "monitor",
                "thong_so", "thongso", "parameter", "indicator",
                "ket_qua", "ketqua", "measure", "result", "value",
                "du_lieu", "data", "wqi", "muc_nuoc", "mucnuoc"]

SO_BANG_MO_TA_TOI_DA = 25
SO_DONG_MAU = 3


def in_ra(cac_dong, chu, muc=0):
    """In ra console va gom vao bao cao cung luc."""
    print(("  " * muc) + chu)
    cac_dong.append(chu)


def ten_bang_dang_quan_tam(ten):
    thap = ten.lower()
    return any(tu in thap for tu in TU_KHOA_BANG)


def mo_ta_mot_bang(kn, schema, bang, cac_dong):
    """In danh sach cot va vai dong mau cua mot bang."""
    with kn.cursor() as ct:
        ct.execute("""
            SELECT column_name, data_type, is_nullable
            FROM information_schema.columns
            WHERE table_schema = %s AND table_name = %s
            ORDER BY ordinal_position
        """, (schema, bang))
        cac_cot = ct.fetchall()

    in_ra(cac_dong, "")
    in_ra(cac_dong, "### {}.{}".format(schema, bang))
    in_ra(cac_dong, "")
    in_ra(cac_dong, "| Cot | Kieu | Cho rong |")
    in_ra(cac_dong, "|---|---|---|")
    for c in cac_cot:
        in_ra(cac_dong, "| {} | {} | {} |".format(
            c["column_name"], c["data_type"], c["is_nullable"]))

    # Vai dong mau. Bang rat lon nen bat buoc co LIMIT.
    ten_day_du = '"{}"."{}"'.format(schema, bang)
    try:
        with kn.cursor() as ct:
            ct.execute("SELECT * FROM {} LIMIT {}".format(
                ten_day_du, SO_DONG_MAU))
            cac_dong_mau = ct.fetchall()
    except Exception as e:
        in_ra(cac_dong, "")
        in_ra(cac_dong, "Khong doc duoc dong mau: {}".format(e))
        return

    in_ra(cac_dong, "")
    in_ra(cac_dong, "Dong mau:")
    in_ra(cac_dong, "")
    for d in cac_dong_mau:
        in_ra(cac_dong, "- `{}`".format(
            {k: (str(v)[:60] if v is not None else None)
             for k, v in d.items()}))


def main():
    thieu = cau_hinh.thieu_thong_tin_ket_noi()
    if thieu:
        print("Thiếu thông tin kết nối: {}".format(", ".join(thieu)))
        print("Sao backend/.env.mau thành backend/.env rồi điền giá trị.")
        return 2

    cac_dong = []
    in_ra(cac_dong, "# Bao cao schema CSDL QTQG")
    in_ra(cac_dong, "")
    in_ra(cac_dong, "Sinh luc: {}".format(
        datetime.now().strftime("%d/%m/%Y %H:%M")))
    in_ra(cac_dong, "")

    print("Đang kết nối {}:{}/{} ...".format(
        cau_hinh.QTQG_MAY_CHU, cau_hinh.QTQG_CONG, cau_hinh.QTQG_CSDL))

    try:
        kn = ket_noi.mo_ket_noi()
    except ket_noi.LoiKetNoi as e:
        print("THẤT BẠI: {}".format(e))
        gay_ra = e.__cause__
        if gay_ra:
            # In nguyen van loi cua psycopg o day la can thiet de chan doan,
            # script nay chi chay tay tren may cua nguoi quan tri.
            print("Nguyên nhân: {}".format(gay_ra))
        print("")
        print("Nếu là lỗi xác thực: tài khoản đăng nhập trang web QTQG không "
              "phải vai trong PostgreSQL, cần xin tài khoản cơ sở dữ liệu "
              "riêng, nên là quyền chỉ đọc.")
        print("Nếu là lỗi hết giờ: tường lửa hoặc cổng 5432 không mở ra ngoài.")
        return 1

    with kn:
        with kn.cursor() as ct:
            ct.execute("SELECT version() AS v")
            in_ra(cac_dong, "- PostgreSQL: {}".format(ct.fetchone()["v"]))

            ct.execute("SELECT extname FROM pg_extension ORDER BY extname")
            cac_mo_rong = [r["extname"] for r in ct.fetchall()]
            in_ra(cac_dong, "- Mo rong: {}".format(", ".join(cac_mo_rong)))
            co_postgis = "postgis" in cac_mo_rong
            in_ra(cac_dong, "- Co PostGIS: {}".format(
                "co" if co_postgis else "khong"))

            ct.execute("""
                SELECT t.table_schema, t.table_name,
                       COALESCE(c.reltuples, -1)::bigint AS so_dong_xap_xi
                FROM information_schema.tables t
                LEFT JOIN pg_class c
                       ON c.relname = t.table_name
                LEFT JOIN pg_namespace n
                       ON n.oid = c.relnamespace AND n.nspname = t.table_schema
                WHERE t.table_schema NOT IN ('pg_catalog', 'information_schema')
                  AND t.table_type = 'BASE TABLE'
                ORDER BY so_dong_xap_xi DESC, t.table_schema, t.table_name
            """)
            cac_bang = ct.fetchall()

        in_ra(cac_dong, "")
        in_ra(cac_dong, "## Danh muc bang ({} bang)".format(len(cac_bang)))
        in_ra(cac_dong, "")
        in_ra(cac_dong, "| Schema | Bang | So dong xap xi | Quan tam |")
        in_ra(cac_dong, "|---|---|---|---|")
        for b in cac_bang:
            in_ra(cac_dong, "| {} | {} | {} | {} |".format(
                b["table_schema"], b["table_name"], b["so_dong_xap_xi"],
                "x" if ten_bang_dang_quan_tam(b["table_name"]) else ""))

        if co_postgis:
            with kn.cursor() as ct:
                ct.execute("""
                    SELECT f_table_schema, f_table_name, f_geometry_column,
                           srid, type
                    FROM geometry_columns
                    ORDER BY f_table_schema, f_table_name
                """)
                cac_lop = ct.fetchall()
            in_ra(cac_dong, "")
            in_ra(cac_dong, "## Cot hinh hoc ({} lop)".format(len(cac_lop)))
            in_ra(cac_dong, "")
            in_ra(cac_dong, "| Schema | Bang | Cot | SRID | Kieu |")
            in_ra(cac_dong, "|---|---|---|---|---|")
            for l in cac_lop:
                in_ra(cac_dong, "| {} | {} | {} | {} | {} |".format(
                    l["f_table_schema"], l["f_table_name"],
                    l["f_geometry_column"], l["srid"], l["type"]))

        quan_tam = [b for b in cac_bang
                    if ten_bang_dang_quan_tam(b["table_name"])]
        in_ra(cac_dong, "")
        in_ra(cac_dong, "## Chi tiet bang dang quan tam")
        if not quan_tam:
            in_ra(cac_dong, "")
            in_ra(cac_dong, "Khong bang nao khop tu khoa. Xem lai danh muc "
                            "tren va chon tay.")
        for b in quan_tam[:SO_BANG_MO_TA_TOI_DA]:
            mo_ta_mot_bang(kn, b["table_schema"], b["table_name"], cac_dong)

    thu_muc = os.environ.get("THU_MUC_BAO_CAO") or cau_hinh.GOC_BACKEND
    duong_dan = os.path.join(thu_muc, "schema_qtqg.md")
    with io.open(duong_dan, "w", encoding="utf-8", newline="\n") as f:
        f.write("\n".join(cac_dong) + "\n")
    print("")
    print("Đã ghi báo cáo: {}".format(duong_dan))
    return 0


if __name__ == "__main__":
    sys.exit(main())
