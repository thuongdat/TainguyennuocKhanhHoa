"""Kiem thu bon endpoint cua dich vu.

Chay o CHE_DO=thu_nghiem (dat trong conftest.py), khong ket noi QTQG that.

Diem quan trong nhat: /api/quan-trac/so-do phai tra ve DUNG schema cua
data/realtime.json. Toan bo phan hien thi so do cua trang web dung lai nho su
trung khop nay; lech mot ten khoa la giao dien im lang khong hien gi.
"""

import json

import pytest
from fastapi.testclient import TestClient

import conftest

import bo_nho_dem
import cau_hinh
import main


@pytest.fixture
def khach():
    bo_nho_dem.xoa()
    with TestClient(main.app) as kh:
        yield kh


# ---------------------------------------------------------------------------
# Suc khoe
# ---------------------------------------------------------------------------

def test_suc_khoe_tra_200(khach):
    r = khach.get("/api/suc-khoe")
    assert r.status_code == 200
    dl = r.json()
    assert dl["trang_thai"] == "san_sang"
    assert dl["che_do"] == "thu_nghiem"
    assert dl["so_tram"] > 0


def test_suc_khoe_khong_lo_thong_tin_ket_noi(khach):
    chu = khach.get("/api/suc-khoe").text
    for bi_mat in conftest.cac_chuoi_bi_mat():
        assert bi_mat not in chu


# ---------------------------------------------------------------------------
# tram.geojson
# ---------------------------------------------------------------------------

def test_tram_geojson_hop_le(khach):
    r = khach.get("/api/quan-trac/tram.geojson")
    assert r.status_code == 200
    tap = r.json()
    assert tap["type"] == "FeatureCollection"
    assert len(tap["features"]) > 0


def test_moi_tram_nam_trong_pham_vi_tinh(khach):
    """CSDL QTQG la cua ca nuoc, endpoint phai loc ve pham vi tinh."""
    import khong_gian
    kb = khong_gian.khung_bao()
    tap = khach.get("/api/quan-trac/tram.geojson").json()

    for f in tap["features"]:
        kinh_do, vi_do = f["geometry"]["coordinates"]
        assert kb[0] <= kinh_do <= kb[2], f["properties"]["ma"]
        assert kb[1] <= vi_do <= kb[3], f["properties"]["ma"]


def test_moi_tram_co_ma(khach):
    """Thieu ma thi khong ghep duoc voi so do."""
    tap = khach.get("/api/quan-trac/tram.geojson").json()
    for f in tap["features"]:
        assert f["properties"]["ma"]


def test_kieu_noi_dung_la_geojson(khach):
    r = khach.get("/api/quan-trac/tram.geojson")
    assert "geo+json" in r.headers["content-type"]


# ---------------------------------------------------------------------------
# so-do: phai dung schema cua data/realtime.json
# ---------------------------------------------------------------------------

KHOA_BAT_BUOC = ["thoi_diem", "che_do", "nguon_dl", "so_doi_tuong",
                 "doi_tuong", "canh_bao"]


def test_so_do_dung_schema_realtime_json(khach):
    r = khach.get("/api/quan-trac/so-do")
    assert r.status_code == 200
    goi = r.json()
    for khoa in KHOA_BAT_BUOC:
        assert khoa in goi, "thieu khoa " + khoa
    assert isinstance(goi["doi_tuong"], dict)
    assert isinstance(goi["canh_bao"], list)


def test_so_do_khop_schema_cua_tep_realtime_that(khach):
    """Doi chieu truc tiep voi data/realtime.json dang co trong du an.

    Day la phep kiem quan trong nhat cua ca bo test: no khoa lai cam ket rang
    tab Quan trac khong phai viet lai phan hien thi so do.
    """
    import os
    duong_dan = os.path.join(cau_hinh.THU_MUC_DU_LIEU, "realtime.json")
    with open(duong_dan, encoding="utf-8") as f:
        tep_that = json.load(f)

    goi = khach.get("/api/quan-trac/so-do").json()

    # Moi khoa cap cao cua tep that phai co trong goi API
    for khoa in tep_that:
        assert khoa in goi, "API thieu khoa " + khoa + " ma tep that co"


def test_khoa_cua_doi_tuong_la_ma_tram(khach):
    """realtime.js tra cuu DU_LIEU_RT.doi_tuong[ma], nen khoa phai la ma tram."""
    goi = khach.get("/api/quan-trac/so-do").json()
    tap = khach.get("/api/quan-trac/tram.geojson").json()
    cac_ma_tram = {f["properties"]["ma"] for f in tap["features"]}

    assert set(goi["doi_tuong"]).issubset(cac_ma_tram) or cac_ma_tram

    for ma, bg in goi["doi_tuong"].items():
        assert ma
        assert "loai" in bg


def test_loai_ban_ghi_khop_truong_realtime(khach):
    """Moi gia tri loai phai la mot khoa trong CAU_HINH.truong_realtime, neu
    khong giao dien khong biet lay danh sach truong o dau."""
    cac_khoa_hop_le = {"ho_chua", "thuy_van", "mua", "chat_luong_nuoc",
                       "khai_thac"}
    goi = khach.get("/api/quan-trac/so-do").json()
    for bg in goi["doi_tuong"].values():
        assert bg["loai"] in cac_khoa_hop_le


def test_canh_bao_dung_cau_truc(khach):
    goi = khach.get("/api/quan-trac/so-do").json()
    for c in goi["canh_bao"]:
        for khoa in ["ma", "ten", "loai", "muc", "noi_dung"]:
            assert khoa in c
        assert c["muc"] in ("canh_bao", "theo_doi")


def test_canh_bao_sap_muc_nghiem_trong_len_truoc(khach):
    """Giong thu tu cua scripts/03_lay_realtime.py, de hai nguon hien ra giao
    dien giong nhau."""
    goi = khach.get("/api/quan-trac/so-do").json()
    cac_muc = [c["muc"] for c in goi["canh_bao"]]
    if "canh_bao" in cac_muc and "theo_doi" in cac_muc:
        assert cac_muc.index("theo_doi") > cac_muc.index("canh_bao")


def test_so_doi_tuong_khop_so_khoa(khach):
    goi = khach.get("/api/quan-trac/so-do").json()
    assert goi["so_doi_tuong"] == len(goi["doi_tuong"])


def test_khong_ban_ghi_nao_co_khoa_mang_gia_tri_none(khach):
    """Thong so khuyet phai bi bo khoa han. Giu khoa voi gia tri None lam giao
    dien hien dong trong."""
    goi = khach.get("/api/quan-trac/so-do").json()
    for ma, bg in goi["doi_tuong"].items():
        for khoa, gia_tri in bg.items():
            if khoa == "wqi_thieu_thong_so":
                continue
            assert gia_tri is not None, "{}.{} la None".format(ma, khoa)


def test_so_do_khong_mang_thuoc_tinh_tinh(khach):
    """Thuoc tinh tinh da nam trong tram.geojson, lap lai o day chi lam goi
    nang them vo ich."""
    goi = khach.get("/api/quan-trac/so-do").json()
    for bg in goi["doi_tuong"].values():
        assert "kinh_do" not in bg
        assert "vi_do" not in bg
        assert "ten_luu_vuc" not in bg


# ---------------------------------------------------------------------------
# chuoi
# ---------------------------------------------------------------------------

def test_chuoi_tra_du_diem(khach):
    goi = khach.get("/api/quan-trac/so-do").json()
    ma = sorted(goi["doi_tuong"])[0]

    r = khach.get("/api/quan-trac/chuoi",
                  params={"ma": ma, "thong_so": "wqi"})
    assert r.status_code == 200
    ch = r.json()
    assert ch["ma"] == ma
    assert ch["so_diem"] == len(ch["diem"])


def test_chuoi_sap_theo_thoi_diem_tang(khach):
    goi = khach.get("/api/quan-trac/so-do").json()
    ma = sorted(goi["doi_tuong"])[0]
    ch = khach.get("/api/quan-trac/chuoi",
                   params={"ma": ma, "thong_so": "wqi"}).json()
    cac_moc = [d["thoi_diem"] for d in ch["diem"]]
    assert cac_moc == sorted(cac_moc)


def test_chuoi_cua_tram_khong_ton_tai_tra_rong(khach):
    """Khong duoc nem loi 500 chi vi ma tram khong co."""
    r = khach.get("/api/quan-trac/chuoi",
                  params={"ma": "KHONG-CO-MA-NAY", "thong_so": "wqi"})
    assert r.status_code == 200
    assert r.json()["so_diem"] == 0


def test_chuoi_thieu_ma_tra_422(khach):
    assert khach.get("/api/quan-trac/chuoi").status_code == 422


# ---------------------------------------------------------------------------
# Loi nguon du lieu
# ---------------------------------------------------------------------------

def test_nguon_loi_tra_503_co_than_json(khach, monkeypatch):
    import nguon_qtqg

    def nem_loi():
        raise nguon_qtqg.LoiNguonDuLieu("Không đọc được bảng trạm")

    monkeypatch.setattr(nguon_qtqg, "lay_so_do_moi_nhat", nem_loi)
    bo_nho_dem.xoa()

    r = khach.get("/api/quan-trac/so-do")
    assert r.status_code == 503
    than = r.json()
    assert "loi" in than["detail"]
    assert "chi_tiet" in than["detail"]


def test_than_loi_khong_lo_thong_tin_ket_noi(khach, monkeypatch):
    """Thong bao loi di ra trinh duyet, khong duoc chua chuoi ket noi."""
    import nguon_qtqg

    def nem_loi():
        raise nguon_qtqg.LoiNguonDuLieu("Không kết nối được cơ sở dữ liệu QTQG")

    monkeypatch.setattr(nguon_qtqg, "lay_so_do_moi_nhat", nem_loi)
    bo_nho_dem.xoa()

    chu = khach.get("/api/quan-trac/so-do").text
    for bi_mat in conftest.cac_chuoi_bi_mat():
        assert bi_mat not in chu


# ---------------------------------------------------------------------------
# Truy van len QTQG chua duoc dien
# ---------------------------------------------------------------------------

CAU_TRUY_VAN_CAN_CO = ["danh_sach_tram", "chat_luong_moi_nhat",
                       "muc_nuoc_moi_nhat", "luu_luong_moi_nhat",
                       "nhiet_do_trung_binh_thang", "chuoi_chat_luong",
                       "chuoi_muc_nuoc", "chuoi_luu_luong"]


def _bo_chu_thich(cau_sql):
    """Bo cac dong chu thich dau cau, de kiem cau lenh that bat dau bang gi."""
    cac_dong = [d for d in cau_sql.splitlines()
                if d.strip() and not d.strip().startswith("--")]
    return "\n".join(cac_dong)


@pytest.mark.parametrize("ten", CAU_TRUY_VAN_CAN_CO)
def test_cau_truy_van_da_duoc_dien(ten):
    """Moi cau SELECT ma nguon that can den phai co trong truy_van.sql."""
    import nguon_qtqg
    cau = _bo_chu_thich(nguon_qtqg.cau_truy_van(ten))
    assert cau.lower().lstrip().startswith(("select", "with"))


@pytest.mark.parametrize("ten", CAU_TRUY_VAN_CAN_CO)
def test_cau_truy_van_co_gioi_han(ten):
    """Moi cau gui len CSDL QTQG dang chay that deu phai co LIMIT."""
    import nguon_qtqg
    assert "limit" in nguon_qtqg.cau_truy_van(ten).lower()


@pytest.mark.parametrize("ten", CAU_TRUY_VAN_CAN_CO)
def test_cau_truy_van_khong_bi_chan_boi_lop_chi_doc(ten):
    """Cac cau SELECT that phai di qua duoc phep kiem tra chong ghi du lieu."""
    import ket_noi
    import nguon_qtqg
    cau = nguon_qtqg.cau_truy_van(ten)
    assert ket_noi._kiem_tra_cau_sql(cau) == cau


def test_cau_truy_van_chua_co_thi_bao_loi_ro():
    import nguon_qtqg
    with pytest.raises(nguon_qtqg.LoiNguonDuLieu):
        nguon_qtqg.cau_truy_van("cau_khong_ton_tai")
