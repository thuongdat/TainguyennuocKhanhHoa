"""Chuan hoa ban ghi tu CSDL QTQG ve ten truong noi bo.

Quy tac cua du an (CLAUDE.md): ten truong dau ra phai khop khai bao trong
assets/js/config.js. Khi ten truong nguon khac, sua BANG_ANH_XA o day chu
KHONG sua giao dien.

Moi khoa trong BANG_ANH_XA la ten truong noi bo, gia tri la danh sach ten cot
co the gap trong nguon, viet thuong va bo dau. Cach nay chiu duoc viec CSDL
QTQG dat ten cot khac du doan: chi them mot phan tu vao danh sach.

Nguyen tac khong doi: thong so nguon khong co thi DE KHUYET. Khong dien 0,
khong noi suy, khong lay gia tri ky truoc. Giao dien chi ve truong co gia tri.
"""

import re
import unicodedata

import wqi


def bo_dau(chu):
    """Bo dau tieng Viet va ha chu thuong. Giong bo_dau() trong config.js va
    trong scripts/nguon_mapinfo.py, de hai phia so khop giong nhau."""
    if chu is None:
        return ""
    chu = unicodedata.normalize("NFD", str(chu))
    chu = "".join(c for c in chu if unicodedata.category(c) != "Mn")
    return chu.replace("đ", "d").replace("Đ", "D").lower()


def _khoa(ten_cot):
    """Dua ten cot ve dang so khop: bo dau, bo moi ky tu khong phai chu so."""
    return re.sub(r"[^a-z0-9]", "", bo_dau(ten_cot))


# --------------------------------------------------------------------------
# Bang anh xa. CAN DOI CHIEU voi bao cao cua kiem_tra_ket_noi.py roi bo sung
# ten cot that cua QTQG vao tung danh sach.
# --------------------------------------------------------------------------

BANG_ANH_XA = {
    # ---- Nhan dang tram ----
    "ma": ["ma", "ma_tram", "matram", "station_code", "code", "ma_diem",
           "ma_vi_tri"],
    "ten": ["ten", "ten_tram", "tentram", "station_name", "name", "ten_diem",
            "ten_vi_tri"],
    "loai_tram": ["loai_tram", "loaitram", "station_type", "type", "loai"],
    "song_ho": ["song_ho", "songho", "ten_song", "river", "nguon_nuoc",
                "thuy_he"],
    "thong_so": ["thong_so", "thongso", "parameters"],
    "ten_luu_vuc": ["ten_luu_vuc", "tenluuvuc", "luu_vuc", "basin"],
    "don_vi_quan_ly": ["don_vi_quan_ly", "donviquanly", "don_vi", "owner",
                       "managed_by"],
    "kinh_do": ["kinh_do", "kinhdo", "longitude", "lon", "lng", "toa_do_x"],
    "vi_do": ["vi_do", "vido", "latitude", "lat", "toa_do_y"],

    # ---- Thoi diem do ----
    "thoi_diem": ["thoi_diem", "thoidiem", "thoi_gian", "ngay_do", "datetime",
                  "measure_time", "observed_at", "time", "ngay_quan_trac"],

    # ---- Thuy van ----
    "h_m": ["h", "h_m", "muc_nuoc", "mucnuoc", "water_level", "level"],
    "q_m3s": ["q", "q_m3s", "luu_luong", "luuluong", "discharge", "flow"],
    "mua_1h_mm": ["mua_1h", "mua1h", "rain_1h", "luong_mua_1h"],
    "mua_24h_mm": ["mua_24h", "mua24h", "rain_24h", "luong_mua_24h"],

    # ---- Chat luong nuoc, nhom co ban ----
    "ph": ["ph", "do_ph", "ph_value"],
    "do_mg_l": ["do", "do_mg_l", "oxy_hoa_tan", "dissolved_oxygen"],
    "nhiet_do_c": ["nhiet_do", "nhietdo", "temperature", "temp", "t_c"],
    "ec_us_cm": ["ec", "do_dan_dien", "dodandien", "conductivity"],
    "tss_mg_l": ["tss", "chat_ran_lo_lung", "suspended_solids"],
    "do_duc_ntu": ["do_duc", "doduc", "turbidity", "ntu"],

    # ---- Chat luong nuoc, nhom mo rong ----
    "cod_mg_l": ["cod", "cod_mg_l"],
    "bod5_mg_l": ["bod5", "bod", "bod5_mg_l"],
    "amoni_mg_l": ["nh4", "amoni", "n_nh4", "nnh4", "ammonium"],
    "nitrat_mg_l": ["no3", "nitrat", "n_no3", "nno3", "nitrate"],
    "nitrit_mg_l": ["no2", "nitrit", "n_no2", "nno2", "nitrite"],
    "photphat_mg_l": ["po4", "photphat", "p_po4", "ppo4", "phosphate"],
    "toc_mg_l": ["toc", "tong_cacbon_huu_co"],
    "coliform_mpn_100ml": ["coliform", "tong_coliform", "totalcoliform"],
    "ecoli_mpn_100ml": ["ecoli", "e_coli", "escherichia_coli"],
    "as_mg_l": ["as", "asen", "arsenic"],
    "pb_mg_l": ["pb", "chi", "lead"],
    "cd_mg_l": ["cd", "cadimi", "cadmium"],
    "hg_mg_l": ["hg", "thuy_ngan", "thuyngan", "mercury"],
    "cr6_mg_l": ["cr6", "cr_vi", "crom6", "crom_vi", "chromium6"],
    # Khong dat "dong" va "kem" lam ten ung vien: sau khi bo dau chung trung
    # voi "dong" (dong chay) va "kem" (chat luong kem), de bat nham cot.
    "cu_mg_l": ["cu", "copper"],
    "zn_mg_l": ["zn", "zinc"],

    # ---- Nhom II cua Quyet dinh 1460: thuoc bao ve thuc vat, don vi ug/L ----
    "aldrin_ug_l": ["aldrin"],
    "bhc_ug_l": ["bhc", "benzene_hexachloride", "hexaclobenzen"],
    "dieldrin_ug_l": ["dieldrin"],
    "ddts_ug_l": ["ddt", "ddts", "tong_ddt"],
    "heptachlor_ug_l": ["heptachlor", "heptachlorepoxide"],

    # ---- Nuoc duoi dat ----
    # h_ngam_m KHONG dung chung ten voi h_m cua nuoc mat: nuoc mat la cao do
    # mat nuoc theo moc tram (so duong, nguon ghi bang centimet), con day la
    # do sau mat nuoc duoi mieng lo khoan (so AM, nguon ghi bang met). Gop hai
    # so nay vao mot truong la ve chung mot bieu do hai dai luong nguoc nghia.
    # Vi vay KHONG dat "water_level" lam ung vien o day: cot do la cua nuoc
    # mat, truy_van.sql da doi ten san thanh h_ngam_m.
    "h_ngam_m": ["h_ngam", "muc_nuoc_ngam", "mucnuocngam", "do_sau_mat_nuoc"],
    "cao_do_mn_m": ["cao_do_mn", "cao_do_mat_nuoc", "caodomatnuoc"],
    "cao_do_mieng_lk_m": ["cao_do_mieng_lk", "cao_do_mieng", "elevation"],
    "tang_chua_nuoc": ["tang_chua_nuoc", "tangchuanuoc", "water_layer"],
    "vi_tri_hc": ["vi_tri_hc", "vi_tri_hanh_chinh"],
    # Lo khoan do muc nuoc hang ngay nhung chi lay mau hoa hoc vai lan mot
    # nam, nen hai nhom thong so trong CUNG mot ban ghi co the lech nhau nhieu
    # thang. Mot truong thoi_diem duy nhat se khien so hoa hoc cu trong nhu
    # vua do xong, vi vay moi nhom giu rieng moc thoi gian cua no.
    "thoi_diem_muc_nuoc": ["thoi_diem_muc_nuoc", "thoidiemmucnuoc"],
    "thoi_diem_chat_luong": ["thoi_diem_chat_luong", "thoidiemchatluong"],
    "mang_quan_trac": ["mang_quan_trac", "network_type"],
    "thiet_bi_do": ["thiet_bi_do", "thietbiquantrac"],
    "ngay_bat_dau": ["ngay_bat_dau", "start_date"],
    # Thong so hoa hoc dac trung cua nuoc duoi dat, theo QCVN 09-MT:2015/BTNMT
    "tds_mg_l": ["tds", "tds_total", "tds105", "tds180",
                 "tong_chat_ran_hoa_tan"],
    "do_cung_mg_l": ["do_cung", "docung", "hardness", "hardness_general"],
    "permanganat_mg_l": ["permanganat", "pemanganat", "chi_so_permanganat"],
    "clorua_mg_l": ["clorua", "cl"],
    "sunfat_mg_l": ["sunfat", "so4"],
    "florua_mg_l": ["florua", "f"],
    "xyanua_mg_l": ["xyanua", "cn"],
    # Sat tong, sat hai va sat ba de RIENG ba truong. Khong cong fe2 voi fe3
    # thanh sat tong: do la suy dien, trai quy tac "thieu thi de khuyet".
    "fe_mg_l": ["fe", "sat", "fe_total", "sat_tong"],
    "fe2_mg_l": ["fe2", "sat_hai"],
    "fe3_mg_l": ["fe3", "sat_ba"],
    "mn_mg_l": ["mn", "mangan"],
    # cr la crom TONG trong water_chemistry, khong phai Cr(VI). De rieng khoi
    # cr6_mg_l, vi hai thong so co nguong khac nhau trong quy chuan.
    "cr_mg_l": ["cr", "crom", "crom_tong"],
    "se_mg_l": ["se", "selen"],
    "phenol_mg_l": ["phenol"],

    # ---- Tong hop ----
    "wqi": ["wqi", "vn_wqi", "vnwqi", "chi_so_wqi", "gia_tri_wqi"],
    "phan_loai_wqi": ["phan_loai_wqi", "phanloaiwqi", "muc_wqi",
                      "danh_gia_wqi"],
    "trang_thai": ["trang_thai", "trangthai", "status"],
    # QTQG hay dia_phuong. Giao dien dung de phan biet tram co so lieu theo
    # thoi gian voi tram chi co ket qua kiem ke mot ky.
    "nguon": ["nguon"],
}

# Tra cuu nguoc: khoa so khop cua ten cot nguon -> ten truong noi bo.
# Dung chung cho moi ban ghi nen dung mot lan luc nap mo-dun.
#
# Dang ky CHINH ten truong noi bo truoc, roi moi den cac ten ung vien. Thieu
# buoc nay thi mot ban ghi da dung ten noi bo (vi du do che do thu_nghiem sinh
# ra, hoac do mot lop goi lai chuan_hoa lan hai) se bi roi mat cac truong co
# ten khong nam trong danh sach ung vien cua chinh no, vi du nhiet_do_c hay
# tss_mg_l.
_TRA_CUU = {}
for _noi_bo in BANG_ANH_XA:
    _TRA_CUU.setdefault(_khoa(_noi_bo), _noi_bo)
for _noi_bo, _cac_ten in BANG_ANH_XA.items():
    for _ten in _cac_ten:
        _TRA_CUU.setdefault(_khoa(_ten), _noi_bo)

# Khoang gia tri hop ly. Gia tri ngoai khoang bi loai thanh khuyet, vi do gan
# nhu luon la o ghi chu hoac gia tri bao loi cua thiet bi, vi du -9999.
KHOANG_HOP_LY = {
    "ph": (0, 14),
    "do_mg_l": (0, 25),
    "nhiet_do_c": (-5, 60),
    "ec_us_cm": (0, 200000),
    "tss_mg_l": (0, 100000),
    "do_duc_ntu": (0, 100000),
    "cod_mg_l": (0, 100000),
    "bod5_mg_l": (0, 100000),
    "amoni_mg_l": (0, 10000),
    "nitrat_mg_l": (0, 10000),
    "nitrit_mg_l": (0, 10000),
    "photphat_mg_l": (0, 10000),
    "coliform_mpn_100ml": (0, 100000000),
    "toc_mg_l": (0, 100000),
    "ecoli_mpn_100ml": (0, 100000000),
    "as_mg_l": (0, 1000),
    "pb_mg_l": (0, 1000),
    "cd_mg_l": (0, 1000),
    "hg_mg_l": (0, 1000),
    "cr6_mg_l": (0, 1000),
    "cu_mg_l": (0, 1000),
    "zn_mg_l": (0, 1000),
    "aldrin_ug_l": (0, 10000),
    "bhc_ug_l": (0, 10000),
    "dieldrin_ug_l": (0, 10000),
    "ddts_ug_l": (0, 10000),
    "heptachlor_ug_l": (0, 10000),
    "wqi": (0, 100),
    # Nuoc duoi dat. h_ngam_m thuong la so am (sau duoi mieng lo khoan) nhung
    # co the duong khi nuoc tu phun, nen khoang phai phu ca hai phia.
    "h_ngam_m": (-500, 100),
    "cao_do_mn_m": (-100, 3000),
    "cao_do_mieng_lk_m": (-100, 3000),
    "tds_mg_l": (0, 100000),
    "do_cung_mg_l": (0, 100000),
    "permanganat_mg_l": (0, 10000),
    "clorua_mg_l": (0, 100000),
    "sunfat_mg_l": (0, 100000),
    "florua_mg_l": (0, 10000),
    "xyanua_mg_l": (0, 10000),
    "fe_mg_l": (0, 10000),
    "fe2_mg_l": (0, 10000),
    "fe3_mg_l": (0, 10000),
    "mn_mg_l": (0, 10000),
    "cr_mg_l": (0, 1000),
    "se_mg_l": (0, 1000),
    "phenol_mg_l": (0, 10000),
    "h_m": (-100, 5000),
    "q_m3s": (0, 1000000),
    "mua_1h_mm": (0, 2000),
    "mua_24h_mm": (0, 5000),
    "kinh_do": (-180, 180),
    "vi_do": (-90, 90),
}

# Truong la chu, khong ep sang so
TRUONG_CHU = {"ma", "ten", "loai_tram", "song_ho", "thong_so", "ten_luu_vuc",
              "don_vi_quan_ly", "phan_loai_wqi", "trang_thai", "thoi_diem",
              "nguon", "tang_chua_nuoc", "vi_tri_hc", "mang_quan_trac",
              "thiet_bi_do", "ngay_bat_dau", "thoi_diem_muc_nuoc",
              "thoi_diem_chat_luong"}

# Thong so thuoc nhom thuy van va nhom mua, dung de doan loai ban ghi
THONG_SO_THUY_VAN = {"h_m", "q_m3s"}
THONG_SO_MUA = {"mua_1h_mm", "mua_24h_mm"}

# Thong so chi co o nuoc duoi dat. Dung de doan loai khi nguoi goi khong noi
# ro, vi du khi mot lop khac goi lai chuan_hoa_ban_ghi() lan hai tren ban ghi
# da chuan hoa.
THONG_SO_NUOC_DUOI_DAT = {"h_ngam_m", "cao_do_mn_m", "cao_do_mieng_lk_m",
                          "tang_chua_nuoc", "tds_mg_l", "do_cung_mg_l",
                          "permanganat_mg_l", "clorua_mg_l", "sunfat_mg_l",
                          "florua_mg_l", "xyanua_mg_l", "fe_mg_l",
                          "fe2_mg_l", "fe3_mg_l", "mn_mg_l", "cr_mg_l",
                          "se_mg_l", "phenol_mg_l"}

LOAI_NUOC_DUOI_DAT = "nuoc_duoi_dat"

# Chuoi nguon dung de bao khong co so do
CHUOI_KHUYET = {"kph", "kpht", "na", "n/a", "-", "--", "khong", "null", "nd"}


def _so(gia_tri):
    """Ep ve so thuc, tra None neu khong phai so.

    Nguon co the ghi so dang chuoi, dung dau phay thap phan kieu Viet, hoac
    ghi KPH (khong phat hien), dau gach ngang, n/a.
    """
    if gia_tri is None:
        return None
    if isinstance(gia_tri, bool):
        return None
    if isinstance(gia_tri, (int, float)):
        return float(gia_tri)

    chu = str(gia_tri).strip()
    if not chu:
        return None
    if bo_dau(chu) in CHUOI_KHUYET:
        return None
    # Bo ky tu so sanh truoc gia tri gioi han phat hien, vi du nho hon 0,003
    chu = chu.lstrip("<>=~").strip()
    chu = chu.replace(" ", "").replace(",", ".")
    try:
        return float(chu)
    except ValueError:
        return None


def _trong_khoang(ten_truong, so):
    if ten_truong not in KHOANG_HOP_LY:
        return True
    thap, cao = KHOANG_HOP_LY[ten_truong]
    return thap <= so <= cao


def chuan_hoa_ban_ghi(dong_nguon, loai=None):
    """Doi mot dong du lieu tho cua QTQG thanh ban ghi theo ten truong noi bo.

    Cot nao khong nhan ra thi bo qua, khong mang theo rac ra trinh duyet.

    Tham so loai noi RO nhom thong so cua ban ghi, thay vi de doan_loai() suy
    ra. Nguon nuoc duoi dat BAT BUOC truyen loai="nuoc_duoi_dat": mot ky lay
    mau nuoc duoi dat co the chi con dung cot pH, luc do doan_loai() se xep no
    vao "chat_luong_nuoc" va wqi.gan_wqi() di tinh VN_WQI cho nuoc duoi dat.
    Quyet dinh 1460/QD-TCMT chi ap dung cho nuoc mat luc dia, nen con so do se
    la vo nghia.
    """
    ket_qua = {}

    for ten_cot, gia_tri in dong_nguon.items():
        ten_noi_bo = _TRA_CUU.get(_khoa(ten_cot))
        if not ten_noi_bo:
            continue
        if ket_qua.get(ten_noi_bo) is not None:
            continue   # da co gia tri tu mot cot khop truoc do

        if ten_noi_bo in TRUONG_CHU:
            chu = None if gia_tri is None else str(gia_tri).strip()
            ket_qua[ten_noi_bo] = chu or None
            continue

        so = _so(gia_tri)
        if so is None or not _trong_khoang(ten_noi_bo, so):
            ket_qua[ten_noi_bo] = None
            continue
        ket_qua[ten_noi_bo] = so

    # Bo moi khoa khuyet de ban ghi gon, giao dien tu hieu la khong co so do
    ket_qua = {k: v for k, v in ket_qua.items() if v is not None}

    ket_qua["loai"] = loai or doan_loai(ket_qua)
    return wqi.gan_wqi(ket_qua)


# Thong so dac trung cua nhom chat luong nuoc, dung de doan loai ban ghi
THONG_SO_CHAT_LUONG = {"ph", "do_mg_l", "cod_mg_l", "bod5_mg_l", "tss_mg_l",
                       "amoni_mg_l", "nitrat_mg_l", "photphat_mg_l",
                       "coliform_mpn_100ml", "wqi"}


def doan_loai(ban_ghi):
    """Nhom thong so cua ban ghi, khop khoa trong CAU_HINH.truong_realtime.

    Uu tien theo so do co that trong ban ghi chu khong theo loai_tram, vi mot
    tram thuy van van co the kem vai thong so chat luong nuoc.

    Chat luong nuoc duoc xet TRUOC thuy van: co tram QTQG do ca muc nuoc lan
    chat luong nuoc, ma chi so WQI va trang thai canh bao deu nam o nhom chat
    luong nuoc. Xet thuy van truoc se lam mat WQI cua chinh nhung tram day du
    nhat.

    Nuoc duoi dat duoc xet TRUOC CA HAI: lo khoan do muc nuoc va do ca thanh
    phan hoa hoc, neu xet chat luong nuoc truoc thi ban ghi lo khoan se bi xep
    vao nhom nuoc mat va bi tinh VN_WQI.
    """
    co = set(ban_ghi.keys())
    if co & THONG_SO_NUOC_DUOI_DAT:
        return LOAI_NUOC_DUOI_DAT
    if co & THONG_SO_CHAT_LUONG:
        return "chat_luong_nuoc"
    if co & THONG_SO_THUY_VAN:
        return "thuy_van"
    if co & THONG_SO_MUA:
        return "mua"
    return "chat_luong_nuoc"


def chuan_hoa_nhieu(cac_dong):
    """Chuan hoa mot danh sach dong, bo cac dong khong co ma tram."""
    ket_qua = []
    for dong in cac_dong:
        ban_ghi = chuan_hoa_ban_ghi(dong)
        if not ban_ghi.get("ma"):
            continue
        ket_qua.append(ban_ghi)
    return ket_qua
