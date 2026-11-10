"""Kiem thu tich luy chuoi thoi gian vao SQLite cuc bo.

Day la CSDL rieng cua backend, khong lien quan gi den QTQG. Moi test dung tep
tam cua pytest de khong lam ban tep that trong backend/.

Diem quan trong nhat: lay so do moi 5 phut nghia la phan lon ban ghi la lap
lai cua lan truoc. Khong co rang buoc UNIQUE thi bang phinh ra rat nhanh va
bieu do co nhieu diem trung nhau tai cung mot thoi diem.
"""

import cau_hinh
import luu_tru


def _dung_tep_tam(tmp_path, monkeypatch):
    monkeypatch.setattr(cau_hinh, "DUONG_DAN_SQLITE",
                        str(tmp_path / "thu.sqlite3"))


def test_ghi_roi_doc_lai_duoc(tmp_path, monkeypatch):
    _dung_tep_tam(tmp_path, monkeypatch)

    them = luu_tru.ghi_mot_luot([
        {"ma": "X1", "thoi_diem": "2026-10-26T08:00+07:00", "wqi": 72.4,
         "ph": 7.1},
    ])
    assert them == 2

    chuoi = luu_tru.doc_chuoi("X1", "wqi")
    assert len(chuoi) == 1
    assert chuoi[0]["gia_tri"] == 72.4


def test_ghi_lap_khong_nhan_ban_dong(tmp_path, monkeypatch):
    _dung_tep_tam(tmp_path, monkeypatch)

    ban_ghi = [{"ma": "X1", "thoi_diem": "2026-10-26T08:00+07:00", "wqi": 72.4}]
    assert luu_tru.ghi_mot_luot(ban_ghi) == 1
    assert luu_tru.ghi_mot_luot(ban_ghi) == 0
    assert luu_tru.ghi_mot_luot(ban_ghi) == 0
    assert len(luu_tru.doc_chuoi("X1", "wqi")) == 1


def test_thoi_diem_khac_nhau_thi_la_hai_diem(tmp_path, monkeypatch):
    _dung_tep_tam(tmp_path, monkeypatch)

    luu_tru.ghi_mot_luot([
        {"ma": "X1", "thoi_diem": "2026-10-26T08:00+07:00", "wqi": 72.4}])
    luu_tru.ghi_mot_luot([
        {"ma": "X1", "thoi_diem": "2026-10-26T09:00+07:00", "wqi": 75.0}])

    chuoi = luu_tru.doc_chuoi("X1", "wqi")
    assert len(chuoi) == 2
    # Phai sap theo thoi diem tang dan, neu khong duong bieu do se zic zac
    assert chuoi[0]["thoi_diem"] < chuoi[1]["thoi_diem"]


def test_khong_ghi_truong_khong_phai_so_do(tmp_path, monkeypatch):
    """Ten tram, loai, trang thai khong phai so do, dua vao chuoi thoi gian la
    vo nghia."""
    _dung_tep_tam(tmp_path, monkeypatch)

    luu_tru.ghi_mot_luot([{
        "ma": "X1", "thoi_diem": "2026-10-26T08:00+07:00",
        "ten": "Cầu Ca Tung", "loai": "chat_luong_nuoc",
        "trang_thai": "binh_thuong", "phan_loai_wqi": "Tốt",
        "wqi": 80.0,
    }])

    cac_thong_so = [t["ten_thong_so"] for t in luu_tru.thong_so_co_chuoi("X1")]
    assert cac_thong_so == ["wqi"]


def test_bo_ban_ghi_thieu_ma_hoac_thieu_thoi_diem(tmp_path, monkeypatch):
    _dung_tep_tam(tmp_path, monkeypatch)

    them = luu_tru.ghi_mot_luot([
        {"wqi": 70.0, "thoi_diem": "2026-10-26T08:00+07:00"},   # thieu ma
        {"ma": "X2", "wqi": 70.0},                              # thieu thoi diem
    ])
    assert them == 0


def test_thoi_diem_chung_duoc_dung_khi_ban_ghi_khong_co(tmp_path, monkeypatch):
    _dung_tep_tam(tmp_path, monkeypatch)

    them = luu_tru.ghi_mot_luot(
        [{"ma": "X1", "wqi": 70.0}],
        thoi_diem_chung="2026-10-26T08:00+07:00")
    assert them == 1
    assert len(luu_tru.doc_chuoi("X1", "wqi")) == 1


def test_loc_theo_khoang_thoi_gian(tmp_path, monkeypatch):
    _dung_tep_tam(tmp_path, monkeypatch)

    for gio in ["08", "09", "10", "11"]:
        luu_tru.ghi_mot_luot([{
            "ma": "X1", "thoi_diem": "2026-10-26T{}:00+07:00".format(gio),
            "wqi": 70.0,
        }])

    chuoi = luu_tru.doc_chuoi("X1", "wqi",
                              tu="2026-10-26T09:00+07:00",
                              den="2026-10-26T10:00+07:00")
    assert len(chuoi) == 2


def test_gia_tri_boolean_khong_duoc_coi_la_so(tmp_path, monkeypatch):
    """True trong Python la mot so nguyen, de lot vao bang nhu gia tri 1."""
    _dung_tep_tam(tmp_path, monkeypatch)

    luu_tru.ghi_mot_luot([{
        "ma": "X1", "thoi_diem": "2026-10-26T08:00+07:00",
        "vuot_quy_chuan": True, "wqi": 70.0,
    }])
    cac_thong_so = [t["ten_thong_so"] for t in luu_tru.thong_so_co_chuoi("X1")]
    assert cac_thong_so == ["wqi"]


def test_dung_bang_goi_nhieu_lan_khong_loi(tmp_path, monkeypatch):
    _dung_tep_tam(tmp_path, monkeypatch)
    luu_tru.dung_bang()
    luu_tru.dung_bang()
