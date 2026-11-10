"""Kiem thu phep an ban ghi so do qua cu.

VI SAO CO PHEP LOC NAY
CSDL QTQG giu ca nhung tram lau khong do. Trong pham vi tinh nay, tram nuoc mat
NP01 co so do moi nhat tu 31/12/2017, trong khi 28 lo khoan do hang ngay. Hai
moc cach nhau gan 9 nam ma nam chung mot ban do va mot bang: nguoi xem quet
nhanh chi thay huy hieu xanh "Binh thuong" va chi so WQI 89, khong thay cot
"Thoi diem do". Day dung la tinh huong da tranh o nhanh nuoc duoi dat bang cach
chi lay lo khoan hientrang = 'Dang hoat dong'.

BA DIEU CAC TEST DUOI DAY CHOT LAI
  1. An la an BAN GHI SO DO, khong phai cong trinh. Danh sach tram khong doi.
  2. Ban ghi khong doc duoc thoi diem thi GIU LAI, khong doan la cu.
  3. Da an thi phai BAO RO, khong im lang lam mat du lieu.

Khong test nao o day ket noi vao CSDL QTQG, xem conftest.py.
"""

from datetime import datetime, timedelta, timezone

import cau_hinh
import tong_hop

MUI_GIO_VN = timezone(timedelta(hours=7))
BAY_GIO = datetime(2026, 10, 27, 9, 0, tzinfo=MUI_GIO_VN)


def _ban_ghi(ma, thoi_diem, **thuoc_tinh):
    bg = {"ma": ma, "ten": "Công trình " + ma, "thoi_diem": thoi_diem}
    bg.update(thuoc_tinh)
    return bg


# ---------------------------------------------------------------------------
# Doc moc thoi gian: nguon ghi khong thong nhat
# ---------------------------------------------------------------------------

def test_doc_duoc_ba_dang_thoi_diem_cua_nguon():
    """Da gap ba dang trong CSDL QTQG va o che do thu_nghiem."""
    assert tong_hop.doc_moc_thoi_gian("2026-10-06 07:00") is not None
    assert tong_hop.doc_moc_thoi_gian("2026-05-03") is not None
    assert tong_hop.doc_moc_thoi_gian("2026-10-27T09:31+07:00") is not None


def test_thoi_diem_khong_co_mui_gio_duoc_coi_la_gio_viet_nam():
    moc = tong_hop.doc_moc_thoi_gian("2026-10-06 07:00")
    assert moc.utcoffset() == timedelta(hours=7)


def test_chuoi_khong_doc_duoc_tra_ve_none():
    for chu in [None, "", "   ", "khong ro", "Năm 2025", "2026-13-45"]:
        assert tong_hop.doc_moc_thoi_gian(chu) is None, chu


# ---------------------------------------------------------------------------
# Tach ban ghi qua cu
# ---------------------------------------------------------------------------

def test_ban_ghi_cu_hon_nguong_bi_tach_ra():
    """Dung chinh truong hop that: NP01 do 31/12/2017."""
    cac_bg = [
        _ban_ghi("NP01", "2017-12-31 22:00", wqi=89),
        _ban_ghi("QT1-KH", "2026-10-06 07:00", h_ngam_m=-3.14),
    ]
    con, cu = tong_hop.tach_ban_ghi_qua_cu(cac_bg, 730, BAY_GIO)
    assert [bg["ma"] for bg in con] == ["QT1-KH"]
    assert [bg["ma"] for bg in cu] == ["NP01"]


def test_ban_ghi_ngay_truoc_han_van_duoc_giu():
    """Ngay sat han ben trong phai duoc giu: phep so la < han, khong phai <=."""
    sat_trong = (BAY_GIO - timedelta(days=729)).strftime("%Y-%m-%d %H:%M")
    sat_ngoai = (BAY_GIO - timedelta(days=731)).strftime("%Y-%m-%d %H:%M")
    con, cu = tong_hop.tach_ban_ghi_qua_cu(
        [_ban_ghi("TRONG", sat_trong), _ban_ghi("NGOAI", sat_ngoai)],
        730, BAY_GIO)
    assert [bg["ma"] for bg in con] == ["TRONG"]
    assert [bg["ma"] for bg in cu] == ["NGOAI"]


def test_ban_ghi_thieu_thoi_diem_thi_GIU_LAI():
    """Khong biet tuoi thi khong duoc doan la cu roi bo di: doan sai la am tham
    lam mat so lieu that."""
    cac_bg = [_ban_ghi("KHONG_MOC", None), _ban_ghi("MOC_LA", "Năm 2025")]
    con, cu = tong_hop.tach_ban_ghi_qua_cu(cac_bg, 730, BAY_GIO)
    assert sorted(bg["ma"] for bg in con) == ["KHONG_MOC", "MOC_LA"]
    assert cu == []


def test_nguong_bang_khong_la_tat_phep_loc():
    cac_bg = [_ban_ghi("RAT_CU", "2001-01-01 00:00")]
    con, cu = tong_hop.tach_ban_ghi_qua_cu(cac_bg, 0, BAY_GIO)
    assert len(con) == 1 and cu == []


def test_nguong_mac_dinh_la_hai_nam():
    """730 ngay. Doi mac dinh thi phai sua ca tai lieu, nen chot lai o day."""
    assert cau_hinh.SO_DO_CU_TOI_DA_NGAY == 730


def test_chi_xet_thoi_diem_chung_khong_xet_rieng_ky_lay_mau():
    """Nuoc duoi dat lay mau hoa hoc vai lan mot nam nen thoi_diem_chat_luong
    thuong cach thoi_diem_muc_nuoc nhieu thang. Xet rieng moc do se bo ca
    nhung lo khoan dang do hang ngay."""
    bg = _ban_ghi("QT1-KH", "2026-10-06 07:00",
                  thoi_diem_muc_nuoc="2026-10-06 07:00",
                  thoi_diem_chat_luong="2019-05-03")
    con, cu = tong_hop.tach_ban_ghi_qua_cu([bg], 730, BAY_GIO)
    assert len(con) == 1 and cu == []
    # Moc cu van con trong ban ghi de giao dien hien ra
    assert con[0]["thoi_diem_chat_luong"] == "2019-05-03"


# ---------------------------------------------------------------------------
# Da an thi phai bao ro
# ---------------------------------------------------------------------------

def test_goi_so_do_bao_ro_da_an_nhung_cong_trinh_nao():
    """Khong im lang lam mat du lieu roi de nguoi dung tu phat hien."""
    con = [_ban_ghi("QT1-KH", "2026-10-06 07:00", h_ngam_m=-3.14)]
    cu = [_ban_ghi("NP01", "2017-12-31 22:00", wqi=89)]
    goi = tong_hop.goi_so_do(con, cu)

    assert goi["so_do_cu"]["so_ban_ghi"] == 1
    assert goi["so_do_cu"]["nguong_ngay"] == cau_hinh.SO_DO_CU_TOI_DA_NGAY
    ct = goi["so_do_cu"]["cong_trinh"][0]
    assert ct["ma"] == "NP01"
    assert ct["thoi_diem"] == "2017-12-31 22:00"


def test_so_do_cu_mang_theo_TEN_thong_so_de_con_ve_duoc_chuoi():
    """Gia tri thi an, nhung TEN thong so phai ra den trinh duyet.

    /api/quan-trac/chuoi co y khong loc, nen chuoi cua NP01 van ve duoc. O
    chon thong so cua trang Quan trac dung tu ban ghi so do hien hanh; ban ghi
    bi an thi o do rong va chuoi thanh khong the voi toi tu giao dien. Danh
    sach ten nay la duong di con lai.
    """
    cu = [_ban_ghi("NP01", "2017-12-31 22:00",
                   wqi=89, h_m=0.316, ph=7.4, phan_loai_wqi="Tốt")]
    ct = tong_hop.goi_so_do([], cu)["so_do_cu"]["cong_trinh"][0]

    assert set(ct["thong_so"]) == {"wqi", "h_m", "ph"}
    # Chuoi khong ve duoc duong bieu do nen khong duoc co trong danh sach
    assert "phan_loai_wqi" not in ct["thong_so"]
    # Va gia tri thi van phai an
    assert "wqi" not in ct and 89 not in ct.values()


def test_thong_so_so_hoc_khong_ke_bool_la_so():
    """bool la kieu con cua int trong Python.

    Khong loai ra thi wqi_tu_tinh=True bi ke la mot thong so ve duoc bieu do,
    va o chon hien mot muc bam vao chi ra bieu do rong.
    """
    bg = _ban_ghi("NP01", "2017-12-31 22:00", wqi=89, wqi_tu_tinh=True)
    assert tong_hop.thong_so_so_hoc(bg) == ["wqi"]


def test_thong_so_so_hoc_bo_qua_truong_khong_phai_so_do():
    """Toa do va nhan khong phai thong so quan trac."""
    bg = _ban_ghi("NP01", "2017-12-31 22:00",
                  kinh_do=109.2, vi_do=12.5, loai_tram="Tài nguyên nước mặt",
                  h_m=0.316)
    assert tong_hop.thong_so_so_hoc(bg) == ["h_m"]


def test_tram_khong_co_so_do_thi_khong_co_muc_trong_so_do_cu():
    """Phan biet hai truong hop o chon thong so phai xu ly khac nhau.

    Tram thuy van chua bao gio co so do: no khong nam trong so_do_cu, nen giao
    dien biet la khong co chuoi de ve. Chi tram BI AN moi co muc o day.
    """
    cu = [_ban_ghi("NP01", "2017-12-31 22:00", wqi=89)]
    cac_ma = [c["ma"] for c in
              tong_hop.goi_so_do([], cu)["so_do_cu"]["cong_trinh"]]
    assert cac_ma == ["NP01"]


def test_ban_ghi_qua_cu_khong_lot_vao_doi_tuong_va_canh_bao():
    """Do la ca muc dich cua phep loc: khong con huy hieu trang thai va khong
    con chi so WQI cua mot ky do tu nhieu nam truoc."""
    con = [_ban_ghi("QT1-KH", "2026-10-06 07:00")]
    cu = [_ban_ghi("NP01", "2017-12-31 22:00", wqi=89,
                   trang_thai="binh_thuong", loai="chat_luong_nuoc")]
    goi = tong_hop.goi_so_do(con, cu)

    assert "NP01" not in goi["doi_tuong"]
    assert goi["so_doi_tuong"] == 1
    assert [c["ma"] for c in goi["canh_bao"]] == []


def test_thoi_diem_chung_khong_bi_keo_lui_boi_ban_ghi_cu():
    """thoi_diem cua goi la moc moi nhat. Neu ban ghi cu con lot vao thi dong
    "Cap nhat" tren giao dien se hien nam 2017."""
    con = [_ban_ghi("QT1-KH", "2026-10-06 07:00")]
    cu = [_ban_ghi("NP01", "2017-12-31 22:00")]
    goi = tong_hop.goi_so_do(con, cu)
    assert goi["thoi_diem"] == "2026-10-06 07:00"


def test_khong_co_ban_ghi_cu_thi_khoi_bao_cao_van_hop_le():
    goi = tong_hop.goi_so_do([_ban_ghi("QT1-KH", "2026-10-06 07:00")])
    assert goi["so_do_cu"]["so_ban_ghi"] == 0
    assert goi["so_do_cu"]["cong_trinh"] == []


def test_goi_so_do_giu_du_sau_khoa_cua_schema_realtime_json():
    """Them khoa so_do_cu khong duoc lam mat khoa nao cua hop dong cu."""
    goi = tong_hop.goi_so_do([_ban_ghi("X1", "2026-10-06 07:00")])
    for khoa in ["thoi_diem", "che_do", "nguon_dl", "so_doi_tuong",
                 "doi_tuong", "canh_bao"]:
        assert khoa in goi, khoa
