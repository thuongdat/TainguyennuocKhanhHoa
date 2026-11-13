"""Kiem thu hai lop nap tu ban ra soat kiem ke (tep Excel).

    scripts/12_nap_ao_ho_kiem_ke.py   -> data/ao_ho.geojson
    scripts/13_nap_wqi_dia_phuong.py  -> data/quan_trac_dia_phuong.geojson

Ba sai sot de xay ra nhat, va day la noi khoa chung lai:

  1. Dang ky lop va tep du lieu lech nhau. Dang ky ma thieu tep thi moi lan mo
     trang la mot loi 404; co tep ma khong dang ky thi lop khong bao gio nap.

  2. Chay script 12 roi QUEN chay lai script 05. Khi do ao_ho da la danh muc
     nguon nuoc (khong co luu luong) ma cac ho khai thac chua quay ve
     khai_thac.geojson: luu luong cua chung bien mat khoi trang Thong ke va
     khong co loi nao bao.

  3. Doc sai cau truc Bieu 10. Bieu khong deu: moi vi tri mot khoi nhieu dong,
     so ky khac nhau (12 thang, 4 quy, 1 lan), xen dong tieu de phan va dong
     danh so cot. Doc lech mot dong van cho ra so hop le.

Cac ham duoc thu deu la ham thuan, khong doc tep Excel va khong can geopandas.
"""

import importlib
import json
import os
import sys

import cau_hinh

THU_MUC_SCRIPTS = os.path.join(cau_hinh.GOC_DU_AN, "scripts")
# Them vao CUOI sys.path de mo-dun cua backend luon duoc uu tien
if THU_MUC_SCRIPTS not in sys.path:
    sys.path.append(THU_MUC_SCRIPTS)

s12 = importlib.import_module("12_nap_ao_ho_kiem_ke")
s13 = importlib.import_module("13_nap_wqi_dia_phuong")
kk = importlib.import_module("kiem_ke_xlsx")


def _doc_json(*phan):
    with open(os.path.join(cau_hinh.GOC_DU_AN, *phan), encoding="utf-8") as f:
        return json.load(f)


def _doc_config_js():
    duong_dan = os.path.join(cau_hinh.GOC_DU_AN, "assets", "js", "config.js")
    with open(duong_dan, encoding="utf-8") as f:
        return f.read()


def _khoi_lop(chu, ma_lop):
    """Cat dung khoi khai bao cua mot lop trong CAU_HINH.lop."""
    vi_tri = chu.find("\n    " + ma_lop + ": {")
    assert vi_tri > 0, "config.js chua khai bao lop " + ma_lop
    ket = chu.find("\n    },\n", vi_tri)
    assert ket > vi_tri
    return chu[vi_tri:ket]


# ---------------------------------------------------------------------------
# Dang ky lop <-> tep du lieu
# ---------------------------------------------------------------------------

def test_dang_ky_lop_wqi_dia_phuong_khop_voi_du_lieu():
    co_tep = os.path.isfile(os.path.join(
        cau_hinh.GOC_DU_AN, "data", s13.TEN_TEP_RA))
    da_dang_ky = s13.TEN_LOP in _doc_json("tinh.json")["lop_co_san"]

    if co_tep:
        assert da_dang_ky, (
            "da co data/quan_trac_dia_phuong.geojson nhung chua them "
            "quan_trac_dia_phuong vao lop_co_san trong tinh.json")
    else:
        assert not da_dang_ky, (
            "tinh.json dang ky quan_trac_dia_phuong nhung chua co tep; chay "
            "scripts/13_nap_wqi_dia_phuong.py truoc, hoac bo dang ky di")


def test_config_js_khai_bao_lop_wqi_dia_phuong():
    chu = _doc_config_js()
    khoi = _khoi_lop(chu, "quan_trac_dia_phuong")
    assert s13.TEN_TEP_RA in khoi

    # Lop phai nam trong mot nhom thi cay lop moi hien no
    nhom = chu[chu.index("nhom_lop: ["):chu.index("/* ---------------- Dinh nghia tung lop")]
    assert "'quan_trac_dia_phuong'" in nhom

    # Ten truong dau ra cua script phai khop khai bao trong config.js
    for ten in ["ten", "xa_phuong", "luu_vuc_kiem_ke", "wqi", "phan_loai_wqi",
                "thoi_diem_wqi", "wqi_thap_nhat", "so_ky", "chuoi_wqi"]:
        assert "'" + ten + "'" in khoi, ten


def test_bang_mau_wqi_du_sau_muc_cua_backend():
    """Khoa cua MAU_WQI phai la dung chuoi phan_loai_wqi() tra ve. Lech mot
    dau la diem do ve mau xam ma khong co loi nao."""
    import wqi
    chu = _doc_config_js()
    bang = chu[chu.index("const MAU_WQI = {"):]
    bang = bang[:bang.index("};")]
    for gia_tri in [95, 80, 60, 40, 15, 5]:
        assert "'" + wqi.phan_loai_wqi(gia_tri) + "'" in bang, gia_tri


def test_config_js_lop_ao_ho_khai_bao_truong_cua_ca_hai_kieu_tep():
    khoi = _khoi_lop(_doc_config_js(), "ao_ho")
    # Truong cua tep do script 12 sinh
    for ten in ["dien_tich_mat_nuoc_m2", "dung_tich_huu_ich_trieu_m3",
                "luu_vuc_kiem_ke", "ghi_chu"]:
        assert "'" + ten + "'" in khoi, ten
    # Truong dung chung cua ca hai kieu
    for ten in ["ten_cong_trinh", "loai_hinh", "dung_tich_ho_trieu_m3"]:
        assert "'" + ten + "'" in khoi, ten


# ---------------------------------------------------------------------------
# Quan he giua script 12 va script 05
# ---------------------------------------------------------------------------

def test_ao_ho_kieu_moi_thi_ho_khai_thac_phai_nam_o_khai_thac():
    duong_ao_ho = os.path.join(cau_hinh.GOC_DU_AN, "data", "ao_ho.geojson")
    if not os.path.isfile(duong_ao_ho):
        return
    ao_ho = _doc_json("data", "ao_ho.geojson")
    if ao_ho.get("sinh_boi") != s12.SINH_BOI:
        return          # tep kieu cu do script 05 tach, khong co gi de kiem

    # Tep kieu moi khong duoc mang luu luong: trang Thong ke dua vao viec
    # THIEU khoa nay de khong cong trung voi khai_thac
    for d in ao_ho["features"]:
        assert "q_khai_thac_m3_ngay" not in d["properties"]

    khai_thac = _doc_json("data", "khai_thac.geojson")
    so_ho = len([1 for d in khai_thac["features"]
                 if str(d["properties"].get("loai_hinh") or "").startswith("Hồ")])
    assert so_ho > 0, (
        "ao_ho.geojson da do script 12 sinh nhung khai_thac.geojson khong co "
        "ho nao: chua chay lai scripts/05_chuan_hoa_chuyen_de.py, trang Thong "
        "ke dang thieu luu luong cua cac ho chua")


def test_script_05_nhan_ra_dau_cua_script_12():
    """Hai script phai thong nhat ten khoa danh dau, neu khong script 05 se
    ghi de len ket qua cua script 12."""
    duong_dan = os.path.join(THU_MUC_SCRIPTS, "05_chuan_hoa_chuyen_de.py")
    with open(duong_dan, encoding="utf-8") as f:
        chu = f.read()
    assert '.get("sinh_boi")' in chu
    assert "ao_ho_do_script_khac_sinh(tt)" in chu


def test_trang_thong_ke_khong_cong_trung_ho():
    duong_dan = os.path.join(cau_hinh.GOC_DU_AN, "assets", "js", "thong-ke.js")
    with open(duong_dan, encoding="utf-8") as f:
        chu = f.read()
    assert "function ho_khai_thac_trong_ao_ho" in chu
    # Khong con cho nao cong thang ca lop ao_ho vao khai thac
    assert "concat(loc('ao_ho'))" not in chu
    assert "concat(DL.ao_ho" not in chu


# ---------------------------------------------------------------------------
# Script 12: ham thuan
# ---------------------------------------------------------------------------

def test_suy_loai_hinh_theo_tien_to_ten():
    assert s12.suy_loai_hinh("Hồ Hoa Sơn") == "Hồ"
    assert s12.suy_loai_hinh("Ao số 1") == "Ao"
    assert s12.suy_loai_hinh("Đầm Nại") == "Đầm"
    assert s12.suy_loai_hinh("Cụm ao số 10") == "Ao"
    assert s12.suy_loai_hinh("Cụm hồ số 2") == "Hồ"
    assert s12.suy_loai_hinh("Thủy điện Hạ Sông Pha 1") == "Hồ thủy điện"


def test_suy_loai_hinh_khong_doan_khi_ten_la():
    assert s12.suy_loai_hinh("Hợp thuỷ thôn Đông 1") is None
    assert s12.suy_loai_hinh(None) is None
    # "Hồng ..." khong phai "Hồ ...": phai co khoang trang sau tien to
    assert s12.suy_loai_hinh("Hồng Ngự") is None


def test_tach_xa():
    assert s12.tach_xa("xã Tu Bông, tỉnh Khánh Hòa") == "Xã Tu Bông"
    assert s12.tach_xa(" Phường Nha Trang, tỉnh Khánh Hòa") == "Phường Nha Trang"
    assert s12.tach_xa("-") is None
    assert s12.tach_xa(None) is None


def test_khoa_so_khop_bo_tien_to_hanh_chinh():
    assert (s12.khoa_so_khop("Hồ Hoa Sơn", "Xã Tu Bông")
            == s12.khoa_so_khop("hồ  Hoa Sơn", "Tu Bông"))
    assert (s12.khoa_so_khop("Hồ Hoa Sơn", "Xã Tu Bông")
            != s12.khoa_so_khop("Hồ Hoa Sơn", "Xã Vạn Ninh"))


def test_dung_thuoc_tinh_lam_sach_o_excel():
    anh_xa = {"stt": 0, "ten_cong_trinh": 1, "dien_tich_mat_nuoc_m2": 2,
              "dung_tich_ho_trieu_m3": 3, "dung_tich_huu_ich_trieu_m3": 4,
              "vi_tri_hc": 5, "muc_dich_su_dung": 6}
    dong = [199, "Ao Xoài (Bầu Xoài)", 3600, 0.005039999999999999, "-",
            "xã Phước Dinh, tỉnh Khánh Hòa", "\t\nSản xuất nông nghiệp"]
    tt = s12.dung_thuoc_tinh(dong, anh_xa)

    assert tt["ten_cong_trinh"] == "Ao Xoài (Bầu Xoài)"
    assert tt["dien_tich_mat_nuoc_m2"] == 3600.0
    assert tt["dung_tich_ho_trieu_m3"] == 0.00504     # bo nhieu dau phay dong
    assert tt["dung_tich_huu_ich_trieu_m3"] is None   # "-" la khong co so
    assert tt["muc_dich_su_dung"] == "Sản xuất nông nghiệp"
    assert tt["loai_hinh"] == "Ao"
    assert tt["xa_phuong"] == "Xã Phước Dinh"
    assert "stt" not in tt


def test_so_hoc_doc_dau_phay_thap_phan():
    # Gia tri nay co that trong sheet B3.2.Ho. Doc thanh 18 la mot cai ao
    # co dung tich 18 trieu m3.
    assert kk.so_hoc("0,018") == 0.018
    assert kk.so_hoc("1.234,5") == 1234.5
    assert kk.so_hoc("1.234.567") == 1234567.0
    assert kk.so_hoc(" 12,5 ") == 12.5
    assert kk.so_hoc("khoảng 3") is None      # khong phai so thi khong doan
    assert kk.so_hoc("-") is None
    assert kk.so_hoc(None) is None
    assert kk.so_hoc(True) is None


def test_gan_ma_khai_thac_chi_khi_khop_dung_mot():
    bang = {s12.khoa_so_khop("Hồ A", "Tu Bông"): {"KT001"},
            s12.khoa_so_khop("Hồ số 1", "Vĩnh Hải"): {"KT002", "KT003"}}
    ds = [{"properties": {"ten_cong_trinh": "Hồ A", "xa_phuong": "Xã Tu Bông"}},
          {"properties": {"ten_cong_trinh": "Hồ số 1", "xa_phuong": "Xã Vĩnh Hải"}},
          {"properties": {"ten_cong_trinh": "Ao B", "xa_phuong": "Xã Tu Bông"}}]
    assert s12.gan_ma_khai_thac(ds, bang) == 1
    assert ds[0]["properties"]["ma_khai_thac"] == "KT001"
    assert ds[1]["properties"]["ma_khai_thac"] is None    # khop hai: khong doan
    assert ds[2]["properties"]["ma_khai_thac"] is None


# ---------------------------------------------------------------------------
# Nhan cot toa do
# ---------------------------------------------------------------------------

def test_nhan_ten_cot_toa_do_nguoi_dung_co_the_dat():
    for ten in ["X", "X (m)", "Tọa độ X", "X VN2000", "Kinh độ",
                "Kinh độ (WGS84)", "Longitude"]:
        assert kk.vai_toa_do(ten) == "kinh_do", ten
    for ten in ["Y", "Y (m)", "Tọa độ Y", "Y VN2000", "Vĩ độ", "Latitude"]:
        assert kk.vai_toa_do(ten) == "vi_do", ten
    for ten in ["Tọa độ", "Tọa độ (WGS84)"]:
        assert kk.vai_toa_do(ten) == "gop", ten


def test_cot_thuong_khong_bi_nhan_nham_la_toa_do():
    for ten in ["STT", "Xã", "Xã (Cũ)", "Vị trí hành chính", "Tỉnh",
                "Giá trị WQI", "Thời gian", "Tên hồ chứa", "Ghi chú", None]:
        assert kk.vai_toa_do(ten) is None, ten


# ---------------------------------------------------------------------------
# Script 13: cau truc Bieu 10
# ---------------------------------------------------------------------------

# Cot: STT, ten, xa, tinh, xa cu, huyen cu, tinh cu, luu vuc, WQI, ky
ANH_XA_13 = {"stt": 0, "ten": 1, "xa_phuong": 2, "tinh": 3, "xa_cu": 4,
             "huyen_cu": 5, "tinh_cu": 6, "luu_vuc_kiem_ke": 7, "wqi": 8,
             "ky": 9}


def _dong(*gia_tri):
    return list(gia_tri) + [None] * (10 - len(gia_tri))


def _bieu_mau():
    """Thu nho cua Bieu 10, giu du cac loai dong gap trong ban that."""
    r = None
    return [
        _dong(1, 2, 3, r, r, r, r, 4, 5, 6),                 # dong danh so cot
        _dong("NĂM 2025 - Bắc Khánh Hòa"),
        _dong(1, "Đồng Trăng", "Xã Diên Lâm", "Khánh Hòa", "Diên Thọ",
              "Diên Khánh", "Khánh Hòa", "Sông Cái Nha Trang", 98,
              "Tháng 1/2025"),
        _dong(r, r, r, r, r, r, r, r, 92, "Tháng 2/2025"),
        _dong(r, r, r, r, r, r, r, r, 96, "Tháng 3/2025"),
        _dong("NĂM 2025 - Nam Khánh Hòa (Ninh Thuận cũ)"),
        _dong(1, "Cuối nguồn suối Cạn", "Xã Ninh Sơn", "Khánh Hòa",
              "Quảng Sơn", "Ninh Sơn", "Ninh Thuận", "Suối Cạn", 90,
              "Quý I/2025"),
        _dong(r, r, r, r, r, r, r, r, 60, "Quý II/2025"),
        _dong("MẪU BỔ SUNG THÁNG 7/2026"),
        _dong("Sông Hiền Lương"),                             # tieu de nhom
        _dong(1, "Suối Đồng Công", "Xã Vạn Ninh", "Khánh Hòa", r, r, r,
              "Sông Hiền Lương", 94, "Tháng 7/2026"),
        _dong("các hồ chứa và sông suối chảy ra biển"),
        _dong(7, "Sông Tam Ích", "Xã Nam Ninh Hòa", "Khánh Hòa", r, r, r, r,
              91, "Tháng 7/2026"),
        _dong(),                                              # dong trong
        _dong(r, "Người lập biểu", r, "Người kiểm tra"),      # chu ky cuoi bieu
        _dong(r, "Ghi chú:"),
    ]


def test_gop_tieu_de_hai_tang():
    tren = ["STT", "Nguồn nước", "Vị trí hành chính", None, "Giá trị WQI"]
    duoi = [None, None, "Xã", "Tỉnh", None]
    assert s13.gop_tieu_de(tren, duoi) == [
        "STT", "Nguồn nước", "Xã", "Tỉnh", "Giá trị WQI"]


def test_tach_khoi_dem_dung_so_vi_tri_va_so_ky():
    cac_vi_tri = s13.tach_khoi(_bieu_mau(), ANH_XA_13)
    # Dong danh so cot, dong tieu de va dong chu ky khong duoc thanh vi tri
    assert [vt["dong_dau"][1] for vt in cac_vi_tri] == [
        "Đồng Trăng", "Cuối nguồn suối Cạn", "Suối Đồng Công", "Sông Tam Ích"]
    assert [len(vt["ky"]) for vt in cac_vi_tri] == [3, 2, 1, 1]
    assert [vt["so_phan"] for vt in cac_vi_tri] == [1, 2, 3, 3]
    assert cac_vi_tri[0]["ky"][1] == ("Tháng 2/2025", 92.0)


def test_tach_khoi_gan_dung_phan_va_nhom():
    cac_vi_tri = s13.tach_khoi(_bieu_mau(), ANH_XA_13)
    assert cac_vi_tri[0]["phan"] == "NĂM 2025 - Bắc Khánh Hòa"
    assert cac_vi_tri[0]["nhom"] is None
    assert cac_vi_tri[2]["nhom"] == "Sông Hiền Lương"
    # Nhom cua phan truoc khong duoc tran sang phan sau
    assert cac_vi_tri[1]["nhom"] is None


def test_tom_tat_chuoi_lay_ky_cuoi_co_so():
    tt = s13.tom_tat_chuoi([("Tháng 1/2025", 98.0), ("Tháng 2/2025", 92.0),
                            ("Tháng 3/2025", 96.0), ("Tháng 4/2025", None)])
    assert tt["wqi"] == 96 and isinstance(tt["wqi"], int)
    assert tt["thoi_diem_wqi"] == "Tháng 3/2025"
    assert tt["so_ky"] == 3
    assert tt["wqi_thap_nhat"] == 92
    assert tt["ky_wqi_thap_nhat"] == "Tháng 2/2025"
    assert tt["chuoi_wqi"] == ("Tháng 1/2025: 98; Tháng 2/2025: 92; "
                               "Tháng 3/2025: 96")


def test_tom_tat_chuoi_khong_co_so_nao():
    tt = s13.tom_tat_chuoi([("Tháng 1/2025", None)])
    assert tt["wqi"] is None and tt["so_ky"] == 0
    assert s13.phan_loai_wqi(tt["wqi"]) is None      # khong so thi khong xep loai


def test_dung_thuoc_tinh_vi_tri():
    cac_vi_tri = s13.tach_khoi(_bieu_mau(), ANH_XA_13)
    tt = s13.dung_thuoc_tinh(cac_vi_tri[1], ANH_XA_13)
    assert tt["ten"] == "Cuối nguồn suối Cạn"
    assert tt["tinh_cu"] == "Ninh Thuận"
    assert tt["wqi"] == 60 and tt["thoi_diem_wqi"] == "Quý II/2025"
    assert s13.phan_loai_wqi(tt["wqi"]) == "Trung bình"

    # Mau bo sung de trong cot luu vuc: lay ten nhom thay the
    tt = s13.dung_thuoc_tinh(cac_vi_tri[3], ANH_XA_13)
    assert tt["luu_vuc_kiem_ke"] == "các hồ chứa và sông suối chảy ra biển"


def test_ma_vi_tri_tach_theo_phan():
    """STT dem lai tu 1 o moi phan, nen ma phai mang so thu tu phan."""
    assert s13.ma_vi_tri(1, 1, 1) == "QD1-01"
    assert s13.ma_vi_tri(2, 1, 1) == "QD2-01"
    assert s13.ma_vi_tri(3, None, 12) == "QD3-12"
