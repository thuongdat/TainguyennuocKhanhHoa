r"""Adapter nguon du lieu quan trac.

Day la mo-dun DUY NHAT biet CSDL QTQG co hinh dang gi. Moi phan con lai cua
backend chi goi ba ham cong khai ben duoi. Doi nguon du lieu, doi schema hay
doi ca cong nghe luu tru deu chi phai sua tep nay va truy_van.sql.

Hai che do, dat bang bien CHE_DO trong backend/.env:
  that        doc CSDL QTQG qua cac cau SELECT trong truy_van.sql
  thu_nghiem  sinh so do thu tu vi tri tram that trong data/quan_trac.geojson,
              de phat trien va kiem thu giao dien khi chua thong ket noi

Ban ghi tra ve o che do thu_nghiem luon mang che_do = thu_nghiem, de giao dien
gan nhan ro cho nguoi dung, khong bao gio de so lieu thu tron lan voi so that.

GHI CHEP VE PHAM VI THUC TE CUA NGUON THAT:
CSDL QTQG la CSDL toan quoc, va so tram thuc su CO SO DO trong mot tinh thuong
it hon han so tram co trong danh muc. Ba truong hop da gap: tram thuy van chi
co vi tri ma khong co so do trong bang tramthuyvan_*; "tram long ghep" la cac
ho chua lon nhung khong co ma tram nen khong noi duoc voi bang so do; va tram
co ma nhung chuoi so do dung lai tu nhieu nam truoc.

Vi vay PHAI chay backend/kiem_tra_ket_noi.py de biet con so thuc cua tinh nay
roi ghi vao backend/README.md, truoc khi noi voi nguoi dung rang tab Quan trac
the hien mang quan trac cua tinh. Dung suy con so tu mot tinh khac.
"""

import json
import math
import os
import re
import sys
from datetime import datetime, timezone, timedelta

import cau_hinh
import chuan_hoa

MUI_GIO_VN = timezone(timedelta(hours=7))

TEP_TRUY_VAN = os.path.join(cau_hinh.GOC_BACKEND, "truy_van.sql")
DAU_HIEU_CHUA_DIEN = "CHUA_DIEN_TRUY_VAN"

GIOI_HAN_TRAM = 5000
GIOI_HAN_CHUOI = 3000

# Thong so nao doc tu bang nao, dung cho endpoint chuoi thoi gian
THONG_SO_THUY_VAN_RIENG = {"h_m": "chuoi_muc_nuoc", "q_m3s": "chuoi_luu_luong"}

# Nuoc duoi dat co bang rieng cho tung nhom thong so
THONG_SO_NGAM_RIENG = {"h_ngam_m": "chuoi_muc_nuoc_ngam",
                       "cao_do_mn_m": "chuoi_muc_nuoc_ngam",
                       "nhiet_do_c": "chuoi_nhiet_do_ngam"}

# Gia tri cot hientrang cua lo khoan dang duoc quan trac. CSDL dung dung chuoi
# nay, gia tri con lai la "Dừng quan trắc".
HIEN_TRANG_DANG_HOAT_DONG = "Đang hoạt động"

_cac_truy_van = None
_nhiet_do_thang = None
_ma_lo_khoan = None


class LoiNguonDuLieu(Exception):
    """Khong lay duoc du lieu tu nguon."""


# --------------------------------------------------------------------------
# Doc truy_van.sql
# --------------------------------------------------------------------------

def _nap_truy_van():
    global _cac_truy_van
    if _cac_truy_van is not None:
        return _cac_truy_van

    _cac_truy_van = {}
    if not os.path.isfile(TEP_TRUY_VAN):
        return _cac_truy_van

    with open(TEP_TRUY_VAN, encoding="utf-8") as f:
        noi_dung = f.read()

    cac_phan = re.split(r"^--\s*@ten:\s*(\w+)\s*$", noi_dung,
                        flags=re.MULTILINE)
    # cac_phan: [phan dau, ten1, than1, ten2, than2, ...]
    for i in range(1, len(cac_phan) - 1, 2):
        _cac_truy_van[cac_phan[i].strip()] = cac_phan[i + 1].strip()
    return _cac_truy_van


def cau_truy_van(ten):
    """Lay mot cau SELECT theo ten, bao loi ro neu chua duoc dien."""
    cau = _nap_truy_van().get(ten)
    if not cau:
        raise LoiNguonDuLieu(
            "Chưa có câu truy vấn {} trong backend/truy_van.sql".format(ten))
    if DAU_HIEU_CHUA_DIEN in cau:
        raise LoiNguonDuLieu(
            "Câu truy vấn {} chưa được điền. Chạy backend/kiem_tra_ket_noi.py "
            "để lấy báo cáo schema, rồi viết câu SELECT thật vào "
            "backend/truy_van.sql.".format(ten))
    return cau


# --------------------------------------------------------------------------
# Che do that: doc CSDL QTQG
# --------------------------------------------------------------------------

def _khung_bao_tham_so():
    import khong_gian
    kb = khong_gian.khung_bao()
    if not kb:
        raise LoiNguonDuLieu("Thiếu khung bao của tỉnh trong tinh.json")
    return {"kd_min": kb[0], "vd_min": kb[1], "kd_max": kb[2], "vd_max": kb[3]}


def _tram_tu_csdl():
    """Tram QTQG thuoc don vi hanh chinh cua tinh.

    Hai lop loc: khung bao trong SQL cho nhe truy van, roi loc theo ten tinh
    o day. Chi loc bang khung bao thoi se keo vao tram cua Phu Yen, Kon Tum va
    Dak Lak, vi khung bao la hinh chu nhat.
    """
    import ket_noi
    import khong_gian

    tham = _khung_bao_tham_so()
    tham["gioi_han"] = GIOI_HAN_TRAM
    cac_dong = ket_noi.truy_van(cau_truy_van("danh_sach_tram"), tham)

    cac_tram = []
    for d in cac_dong:
        tho = dict(d)
        if not khong_gian.thuoc_tinh_nay(tho.pop("tinh_qtqg", None)):
            continue
        tram = chuan_hoa.chuan_hoa_ban_ghi(tho)
        if tram.get("ma"):
            tram["nguon"] = "QTQG"
            cac_tram.append(tram)
    return cac_tram


# --------------------------------------------------------------------------
# Nuoc duoi dat: mang quan trac quoc gia
# --------------------------------------------------------------------------

def _lo_khoan_tu_csdl():
    """Lo khoan quan trac quoc gia DANG HOAT DONG trong pham vi tinh.

    CHI lay lo khoan co hientrang = 'Dang hoat dong'. CSDL con giu ca lo
    khoan da dung quan trac, va so do cuoi cung cua chung co the cu nhieu nam;
    de chung mot ban do voi so do hom qua la gay hieu nham.

    QTQG ghi tinh theo don vi hanh chinh SAU sap nhap o bang nay, nen lo khoan
    nam tren dia ban tinh cu nao cung se duoc tra ve, mien la cot tinh khop
    danh sach ten_tinh_trong_qtqg trong tinh.json.
    """
    import ket_noi
    import khong_gian

    tham = _khung_bao_tham_so()
    tham["gioi_han"] = GIOI_HAN_TRAM
    tham["hien_trang"] = HIEN_TRANG_DANG_HOAT_DONG
    cac_dong = ket_noi.truy_van(cau_truy_van("danh_sach_lo_khoan"), tham)

    cac_lo = []
    for d in cac_dong:
        tho = dict(d)
        if not khong_gian.thuoc_tinh_nay(tho.pop("tinh_qtqg", None)):
            continue
        lo = chuan_hoa.chuan_hoa_ban_ghi(tho, loai=chuan_hoa.LOAI_NUOC_DUOI_DAT)
        if lo.get("ma"):
            lo["nguon"] = "QTQG"
            cac_lo.append(lo)
    return cac_lo


def ma_lo_khoan():
    """Tap ma cua cac lo khoan, de biet mot ma thuoc nuoc duoi dat hay nuoc mat.

    Can cho endpoint chuoi thoi gian: ten thong so khong du de chon bang, vi
    nhiet_do_c co o ca hai nguon. Doc mot lan roi giu lai.
    """
    global _ma_lo_khoan
    if _ma_lo_khoan is None:
        _ma_lo_khoan = set()
        try:
            _ma_lo_khoan = {l["ma"] for l in _lo_khoan_tu_csdl() if l.get("ma")}
        except Exception:
            _ma_lo_khoan = set()   # khong doc duoc thi coi nhu khong co lo khoan
    return _ma_lo_khoan


# Cua so ngay cua cau nhiet_do_ngam_moi_nhat. Hai nam du de phu moi lo khoan
# dang hoat dong (ky do nhiet do gan nhat la 25/12/2025), va du hep de
# PostgreSQL khong phai quet het 24,6 trieu dong.
CUA_SO_NHIET_DO_NGAY = 730


def _nhiet_do_ngam(cac_ma):
    """Nhiet do nuoc gan nhat cua tung lo khoan.

    Hai buoc: cau nhanh co loc cua so ngay, roi bu bang cau khong gioi han cho
    rieng nhung lo khoan cau nhanh khong tim thay. Xem ghi chep trong
    truy_van.sql ve ly do khong dung mot cau duy nhat.
    """
    import ket_noi

    try:
        cac_dong = ket_noi.truy_van(
            cau_truy_van("nhiet_do_ngam_moi_nhat"),
            {"cac_ma": list(cac_ma), "so_ngay": CUA_SO_NHIET_DO_NGAY,
             "gioi_han": GIOI_HAN_TRAM})
    except Exception as e:
        print("Canh bao: khong doc duoc nhiet_do_ngam_moi_nhat: {}".format(e),
              file=sys.stderr)
        cac_dong = []

    da_co = {d["ma"] for d in cac_dong if d.get("ma")}
    con_thieu = [m for m in cac_ma if m not in da_co]
    if not con_thieu:
        return cac_dong

    try:
        cac_dong = cac_dong + ket_noi.truy_van(
            cau_truy_van("nhiet_do_ngam_bu"),
            {"cac_ma": con_thieu, "gioi_han": GIOI_HAN_TRAM})
    except Exception as e:
        print("Canh bao: khong bu duoc nhiet do cho {} lo khoan: {}".format(
            len(con_thieu), e), file=sys.stderr)

    return cac_dong


def _so_do_lo_khoan_tu_csdl():
    """So do moi nhat cua tung lo khoan: muc nuoc, nhiet do, thanh phan hoa hoc.

    Ba nhom thong so nam o ba bang va co tan suat do rat khac nhau (muc nuoc
    moi ngay, nhiet do va hoa hoc vai lan mot nam), nen moi nhom mang theo moc
    thoi gian rieng ngoai truong thoi_diem chung.
    """
    import ket_noi

    cac_lo = _lo_khoan_tu_csdl()
    cac_ma = [l["ma"] for l in cac_lo if l.get("ma")]
    if not cac_ma:
        return []

    tham = {"cac_ma": cac_ma, "gioi_han": GIOI_HAN_TRAM}

    def doc(ten_cau):
        """Mot nhom thong so khong doc duoc thi bo nhom do, khong bo ca lo khoan.

        Truy van muc nuoc nang hon han hai truy van kia; neu no vuot
        statement_timeout thi van con nhiet do va hoa hoc de hien.
        """
        try:
            return ket_noi.truy_van(cau_truy_van(ten_cau), tham)
        except Exception as e:
            print("Canh bao: khong doc duoc {}: {}".format(ten_cau, e),
                  file=sys.stderr)
            return []

    gop = {}

    def nhap(cac_dong, ten_moc=None):
        for d in cac_dong:
            ma = d.get("ma")
            if not ma:
                continue
            o = gop.setdefault(ma, {"ma": ma})
            for khoa, gt in d.items():
                if khoa == "ma" or gt is None:
                    continue
                if khoa == "thoi_diem":
                    if ten_moc:
                        o[ten_moc] = str(gt)
                    if not o.get("thoi_diem") or str(gt) > str(o["thoi_diem"]):
                        o["thoi_diem"] = str(gt)
                    continue
                o[khoa] = gt

    nhap(doc("muc_nuoc_ngam_moi_nhat"), "thoi_diem_muc_nuoc")
    nhap(_nhiet_do_ngam(cac_ma))
    nhap(doc("chat_luong_ngam_moi_nhat"), "thoi_diem_chat_luong")

    thuoc_tinh_theo_ma = {l["ma"]: l for l in cac_lo}

    ket_qua = []
    for ma, tho in gop.items():
        goc = thuoc_tinh_theo_ma.get(ma) or {}
        if not tho.get("ten"):
            tho["ten"] = goc.get("ten")
        # Tang chua nuoc di theo so do de bang va hop thoai chi tiet doc duoc
        if goc.get("tang_chua_nuoc") and not tho.get("tang_chua_nuoc"):
            tho["tang_chua_nuoc"] = goc["tang_chua_nuoc"]
        ket_qua.append(chuan_hoa.chuan_hoa_ban_ghi(
            tho, loai=chuan_hoa.LOAI_NUOC_DUOI_DAT))

    return ket_qua


def _chuoi_ngam_tu_csdl(ma_lo, ten_thong_so, tu, den):
    """Chuoi thoi gian mot thong so cua mot lo khoan."""
    import ket_noi

    ten_cau = THONG_SO_NGAM_RIENG.get(ten_thong_so, "chuoi_chat_luong_ngam")
    cac_dong = ket_noi.truy_van(cau_truy_van(ten_cau), {
        "ma": ma_lo, "tu": tu, "den": den, "gioi_han": GIOI_HAN_CHUOI})

    ket_qua = []
    for d in cac_dong:
        tho = dict(d)
        tho["ma"] = ma_lo
        ban_ghi = chuan_hoa.chuan_hoa_ban_ghi(
            tho, loai=chuan_hoa.LOAI_NUOC_DUOI_DAT)
        gia_tri = ban_ghi.get(ten_thong_so)
        if gia_tri is None or not ban_ghi.get("thoi_diem"):
            continue
        ket_qua.append({"thoi_diem": ban_ghi["thoi_diem"],
                        "gia_tri": gia_tri})

    # Truy van sap giam dan de LIMIT cat lay cac moc MOI NHAT, dao lai cho
    # dung chieu thoi gian. Giong _chuoi_tu_csdl() cua nuoc mat.
    ket_qua.reverse()
    return ket_qua


def nhiet_do_trung_binh_thang(cac_ma):
    """Nhiet do nuoc trung binh nhieu nam theo thang, rieng tung tram.

    Dung cho viec UOC nhiet do o nhung ky thieu so do, de quy DO ra phan tram
    bao hoa. Day la so SUY DIEN chu khong phai so do, nen moi ban ghi su dung
    no deu bi danh dau nhiet_do_uoc_tinh = True.
    """
    global _nhiet_do_thang
    if _nhiet_do_thang is not None:
        return _nhiet_do_thang

    import ket_noi
    cac_dong = ket_noi.truy_van(
        cau_truy_van("nhiet_do_trung_binh_thang"),
        {"cac_ma": list(cac_ma), "gioi_han": GIOI_HAN_TRAM})

    _nhiet_do_thang = {}
    for d in cac_dong:
        if d["nhiet_do_c"] is None:
            continue
        _nhiet_do_thang[(d["ma"], int(d["thang"]))] = {
            "nhiet_do_c": float(d["nhiet_do_c"]),
            "so_lan_do": int(d["so_lan_do"]),
        }
    return _nhiet_do_thang


def _thang_cua(thoi_diem):
    if not thoi_diem:
        return None
    try:
        return int(str(thoi_diem)[5:7])
    except (ValueError, IndexError):
        return None


def _bu_nhiet_do(ban_ghi, bang_nhiet_do):
    """Dien nhiet do uoc tinh khi ky do thieu nhiet do nhung co DO.

    Khong co nhiet do thi khong quy duoc DO ra phan tram bao hoa, ma thieu
    WQI_DO thi nhom IV thuong tut xuong duoi ba thong so va ca chi so WQI
    khong con du dieu kien cong bo (muc 2.1.b cua Quyet dinh 1460).

    Day la so SUY DIEN, khong phai so do, nen trai voi yeu cau ve du lieu dau
    vao o muc 2.1.a. Nguoi dung da duoc bao dieu do va van chon dung, doi lai
    moi ban ghi deu mang co nhiet_do_uoc_tinh de giao dien noi ro.

    Tat bang UOC_NHIET_DO=0 trong backend/.env.
    """
    if not cau_hinh.UOC_NHIET_DO:
        return ban_ghi
    if ban_ghi.get("nhiet_do_c") is not None:
        return ban_ghi
    if ban_ghi.get("do_mg_l") is None:
        return ban_ghi      # khong co DO thi uoc nhiet do cung vo ich

    thang = _thang_cua(ban_ghi.get("thoi_diem"))
    if thang is None:
        return ban_ghi

    o = bang_nhiet_do.get((ban_ghi.get("ma"), thang))
    if not o:
        return ban_ghi

    ban_ghi["nhiet_do_c"] = round(o["nhiet_do_c"], 1)
    ban_ghi["nhiet_do_uoc_tinh"] = True
    return ban_ghi


def _so_do_tu_csdl():
    import ket_noi

    cac_tram = _tram_tu_csdl()
    cac_ma = [t["ma"] for t in cac_tram if t.get("ma")]
    if not cac_ma:
        return []

    tham = {"cac_ma": cac_ma, "gioi_han": GIOI_HAN_TRAM}

    def doc(ten_cau):
        try:
            return ket_noi.truy_van(cau_truy_van(ten_cau), tham)
        except LoiNguonDuLieu:
            raise
        except Exception as e:
            raise LoiNguonDuLieu("Lỗi khi đọc {}".format(ten_cau)) from e

    gop = {}

    def nhap(cac_dong):
        for d in cac_dong:
            ma = d.get("ma")
            if not ma:
                continue
            o = gop.setdefault(ma, {"ma": ma})
            for khoa, gt in d.items():
                if khoa == "ma" or gt is None:
                    continue
                # Thoi diem: giu moc muon nhat trong cac nguon
                if khoa == "thoi_diem":
                    if not o.get("thoi_diem") or str(gt) > str(o["thoi_diem"]):
                        o["thoi_diem"] = str(gt)
                    continue
                o[khoa] = gt

    nhap(doc("chat_luong_moi_nhat"))
    nhap(doc("muc_nuoc_moi_nhat"))
    nhap(doc("luu_luong_moi_nhat"))

    bang_nhiet_do = {}
    if cau_hinh.UOC_NHIET_DO:
        try:
            bang_nhiet_do = nhiet_do_trung_binh_thang(cac_ma)
        except Exception:
            bang_nhiet_do = {}   # thieu bang uoc thi van tra so do binh thuong

    ten_theo_ma = {t["ma"]: t.get("ten") for t in cac_tram}

    ket_qua = []
    for ma, tho in gop.items():
        if not tho.get("ten"):
            tho["ten"] = ten_theo_ma.get(ma)
        tho = _bu_nhiet_do(tho, bang_nhiet_do)
        ban_ghi = chuan_hoa.chuan_hoa_ban_ghi(tho)
        # chuan_hoa bo moi khoa khong nhan ra, gan lai co danh dau
        if tho.get("nhiet_do_uoc_tinh"):
            ban_ghi["nhiet_do_uoc_tinh"] = True
        ket_qua.append(ban_ghi)

    return ket_qua


def _chuoi_tu_csdl(ma_tram, ten_thong_so, tu, den):
    import ket_noi

    ten_cau = THONG_SO_THUY_VAN_RIENG.get(ten_thong_so, "chuoi_chat_luong")
    cac_dong = ket_noi.truy_van(cau_truy_van(ten_cau), {
        "ma": ma_tram, "tu": tu, "den": den, "gioi_han": GIOI_HAN_CHUOI})

    bang_nhiet_do = {}
    if ten_cau == "chuoi_chat_luong" and cau_hinh.UOC_NHIET_DO:
        try:
            bang_nhiet_do = nhiet_do_trung_binh_thang([ma_tram])
        except Exception:
            bang_nhiet_do = {}

    ket_qua = []
    for d in cac_dong:
        tho = dict(d)
        tho["ma"] = ma_tram
        if bang_nhiet_do:
            tho = _bu_nhiet_do(tho, bang_nhiet_do)
        ban_ghi = chuan_hoa.chuan_hoa_ban_ghi(tho)
        gia_tri = ban_ghi.get(ten_thong_so)
        if gia_tri is None or not ban_ghi.get("thoi_diem"):
            continue
        ket_qua.append({"thoi_diem": ban_ghi["thoi_diem"],
                        "gia_tri": gia_tri})

    # Truy van sap giam dan de LIMIT cat lay cac moc MOI NHAT. Dao lai cho
    # dung chieu thoi gian, neu khong duong bieu do se chay nguoc.
    ket_qua.reverse()
    return ket_qua


# --------------------------------------------------------------------------
# Che do thu_nghiem: sinh so do tu vi tri tram that
# --------------------------------------------------------------------------

def _doc_tram_dia_phuong():
    """Doc data/quan_trac.geojson de lay vi tri tram that."""
    duong_dan = os.path.join(cau_hinh.THU_MUC_DU_LIEU, "quan_trac.geojson")
    if not os.path.isfile(duong_dan):
        raise LoiNguonDuLieu(
            "Không tìm thấy data/quan_trac.geojson để sinh dữ liệu thử nghiệm")

    with open(duong_dan, encoding="utf-8") as f:
        tap = json.load(f)

    cac_tram = []
    for f_ in tap.get("features", []):
        tt = f_.get("properties") or {}
        hh = f_.get("geometry") or {}
        if hh.get("type") != "Point":
            continue
        toa_do = hh.get("coordinates") or []
        if len(toa_do) < 2:
            continue
        cac_tram.append({
            "ma": tt.get("ma"),
            "ten": tt.get("ten"),
            "loai_tram": tt.get("loai_tram"),
            "song_ho": tt.get("song_ho"),
            "thong_so": tt.get("thong_so"),
            "ten_luu_vuc": tt.get("ten_luu_vuc"),
            "don_vi_quan_ly": tt.get("don_vi_quan_ly"),
            "kinh_do": toa_do[0],
            "vi_do": toa_do[1],
            "nguon": "dia_phuong",
        })
    return cac_tram


def _dao_dong(ma, ten_thong_so, gio):
    """So dao dong tu 0 den 1, on dinh trong mot gio va khac nhau giua cac gio.

    Sinh tu ham bam cua chuoi nen khong can thu vien ngoai va khong doi giua
    hai lan goi trong cung mot gio. Dung sin de so di chuyen muot theo gio,
    nhin tren bieu do giong mot chuoi do that.
    """
    hat = 0
    for ky_tu in "{}|{}".format(ma or "", ten_thong_so):
        hat = (hat * 31 + ord(ky_tu)) % 100003
    pha = (hat % 360) * math.pi / 180.0
    return (math.sin(pha + gio * math.pi / 12.0) + 1.0) / 2.0


def _so_do_thu_nghiem_mot_tram(tram, thoi_diem):
    """Sinh mot ban ghi so do thu cho mot tram."""
    ma = tram.get("ma")
    gio = thoi_diem.hour + thoi_diem.day * 24
    la_thuy_van = tram.get("loai_tram") == "Thủy văn"

    ban_ghi = {
        "ma": ma,
        "ten": tram.get("ten"),
        "thoi_diem": thoi_diem.isoformat(timespec="minutes"),
    }

    if la_thuy_van:
        ban_ghi["h_m"] = round(2 + 6 * _dao_dong(ma, "h", gio), 2)
        ban_ghi["q_m3s"] = round(5 + 120 * _dao_dong(ma, "q", gio), 1)
        ban_ghi["mua_1h_mm"] = round(12 * _dao_dong(ma, "mua1h", gio), 1)
        ban_ghi["mua_24h_mm"] = round(60 * _dao_dong(ma, "mua24h", gio), 1)
        return chuan_hoa.chuan_hoa_ban_ghi(ban_ghi)

    # Diem chat luong nuoc: nhom co ban va nhom mo rong
    ban_ghi["ph"] = round(6.3 + 2.0 * _dao_dong(ma, "ph", gio), 2)
    ban_ghi["do_mg_l"] = round(3.5 + 4.5 * _dao_dong(ma, "do", gio), 2)
    ban_ghi["nhiet_do_c"] = round(23 + 8 * _dao_dong(ma, "t", gio), 1)
    ban_ghi["ec_us_cm"] = round(60 + 400 * _dao_dong(ma, "ec", gio), 0)
    ban_ghi["tss_mg_l"] = round(5 + 70 * _dao_dong(ma, "tss", gio), 1)
    ban_ghi["do_duc_ntu"] = round(2 + 40 * _dao_dong(ma, "duc", gio), 1)
    ban_ghi["cod_mg_l"] = round(4 + 30 * _dao_dong(ma, "cod", gio), 1)
    ban_ghi["bod5_mg_l"] = round(2 + 14 * _dao_dong(ma, "bod", gio), 1)
    ban_ghi["amoni_mg_l"] = round(0.02 + 1.2 * _dao_dong(ma, "nh4", gio), 3)
    ban_ghi["nitrat_mg_l"] = round(0.1 + 4 * _dao_dong(ma, "no3", gio), 2)
    ban_ghi["photphat_mg_l"] = round(0.01 + 0.5 * _dao_dong(ma, "po4", gio), 3)

    # Bien do cua nhom kim loai nang co y dat thap: WQI dung trung binh NHAN
    # cho nhom III, nen chi mot kim loai gan nguong la keo ca chi so xuong.
    # De bien do rong thi moi tram deu ra muc "Xau" va giao dien khong bao gio
    # hien duoc mau cua cac muc tot.
    ban_ghi["coliform_mpn_100ml"] = round(
        100 + 13000 * _dao_dong(ma, "coli", gio), 0)
    ban_ghi["as_mg_l"] = round(0.001 + 0.018 * _dao_dong(ma, "as", gio), 4)
    ban_ghi["pb_mg_l"] = round(0.001 + 0.035 * _dao_dong(ma, "pb", gio), 4)
    ban_ghi["cd_mg_l"] = round(0.0005 + 0.006 * _dao_dong(ma, "cd", gio), 4)
    ban_ghi["hg_mg_l"] = round(0.0001 + 0.0013 * _dao_dong(ma, "hg", gio), 5)
    ban_ghi["cu_mg_l"] = round(0.02 + 0.45 * _dao_dong(ma, "cu", gio), 3)
    ban_ghi["zn_mg_l"] = round(0.1 + 1.3 * _dao_dong(ma, "zn", gio), 3)

    # KHONG sinh san truong wqi. De khuyet thi chuan_hoa_ban_ghi() se goi
    # wqi.gan_wqi(), va ham do tu tinh VN_WQI tu chinh cac thong so o tren
    # theo Quyet dinh 1460. Nho vay che do thu nghiem chay qua dung duong ma
    # ma che do that se chay, thay vi mot nhanh rieng khong ai kiem thu.

    return chuan_hoa.chuan_hoa_ban_ghi(ban_ghi)


def _chuoi_thu_nghiem(ma_tram, ten_thong_so, so_diem=48):
    """Chuoi 48 gio gan nhat, cung ham dao dong nen noi tiep so do moi nhat."""
    bay_gio = datetime.now(MUI_GIO_VN).replace(minute=0, second=0,
                                               microsecond=0)
    cac_tram = {t["ma"]: t for t in _doc_tram_dia_phuong() if t.get("ma")}
    tram = cac_tram.get(ma_tram)
    if not tram:
        return []

    ket_qua = []
    for lui in range(so_diem - 1, -1, -1):
        luc = bay_gio - timedelta(hours=lui)
        ban_ghi = _so_do_thu_nghiem_mot_tram(tram, luc)
        gia_tri = ban_ghi.get(ten_thong_so)
        if gia_tri is None:
            continue
        ket_qua.append({"thoi_diem": luc.isoformat(timespec="minutes"),
                        "gia_tri": gia_tri})
    return ket_qua


# --------------------------------------------------------------------------
# Ba ham cong khai
# --------------------------------------------------------------------------

def lay_danh_sach_tram():
    """Danh sach tram kem toa do, da chuan hoa ten truong.

    O che do that, mac dinh chi tra ve tram QTQG. Lop quan trac dia phuong
    (data/quan_trac.geojson) cua du an nay con la du lieu mo phong, tron vi tri
    bia vao cung so do thuc cua QTQG tren mot ban do la gay hieu nham. Khi nao
    co lop dia phuong that thi dat HOP_TRAM_DIA_PHUONG=1 trong backend/.env,
    danh sach se la HOP cua hai nguon va moi tram mang truong "nguon" de giao
    dien phan biet duoc.

    O che do thu_nghiem thi khong co CSDL, nen nguon vi tri duy nhat la lop
    dia phuong; giao dien da gan nhan "du lieu thu nghiem" cho truong hop do.
    """
    if not cau_hinh.la_nguon_that():
        return _doc_tram_dia_phuong()

    # Lo khoan nuoc duoi dat dang hoat dong di cung danh sach tram nuoc mat:
    # ca hai deu la cong trinh quan trac cua tinh, nguoi dung loc bang bo loc
    # "Loai" tren tab Quan trac.
    tram_qtqg = _tram_tu_csdl() + _lo_khoan_tu_csdl()

    if not cau_hinh.HOP_TRAM_DIA_PHUONG:
        for t in tram_qtqg:
            t.setdefault("nguon", "QTQG")
        return tram_qtqg

    import khong_gian
    return khong_gian.hop_danh_sach_tram(_doc_tram_dia_phuong(), tram_qtqg)


def lay_so_do_moi_nhat():
    """So do moi nhat cua tung tram, da chuan hoa ten truong."""
    if cau_hinh.la_nguon_that():
        return _so_do_tu_csdl() + _so_do_lo_khoan_tu_csdl()
    return [_so_do_thu_nghiem_mot_tram(t, datetime.now(MUI_GIO_VN))
            for t in _doc_tram_dia_phuong() if t.get("ma")]


def lay_danh_sach_lo_khoan():
    """Rieng cac lo khoan nuoc duoi dat, khong kem tram nuoc mat.

    Dung cho scripts/08_xuat_lo_khoan_ndd.py, la script xuat lop tinh cho ban
    do chinh. Tach ra lam ham cong khai de script do khong phai goi ham rieng
    tu, va de hieu biet ve schema QTQG van chi nam o mot cho.
    """
    if not cau_hinh.la_nguon_that():
        raise LoiNguonDuLieu(
            "Chỉ lấy được lỗ khoan nước dưới đất khi CHE_DO=that")
    return _lo_khoan_tu_csdl()


def lay_so_do_lo_khoan():
    """So do moi nhat cua cac lo khoan. Xem lay_danh_sach_lo_khoan()."""
    if not cau_hinh.la_nguon_that():
        raise LoiNguonDuLieu(
            "Chỉ lấy được số đo lỗ khoan khi CHE_DO=that")
    return _so_do_lo_khoan_tu_csdl()


def lay_chuoi(ma_tram, ten_thong_so, tu=None, den=None):
    """Chuoi thoi gian mot tram, mot thong so.

    O che do that, uu tien doc tu QTQG. Khong lay duoc thi roi ve chuoi da
    tich luy trong SQLite cuc bo.
    """
    if not cau_hinh.la_nguon_that():
        return _chuoi_thu_nghiem(ma_tram, ten_thong_so)

    # Chon bang theo NGUON cua tram, khong theo ten thong so: nhiet_do_c co o
    # ca nuoc mat lan nuoc duoi dat, con h_m va h_ngam_m thi nam o hai bang
    # hoan toan khac nhau.
    try:
        if ma_tram in ma_lo_khoan():
            return _chuoi_ngam_tu_csdl(ma_tram, ten_thong_so, tu, den)
        return _chuoi_tu_csdl(ma_tram, ten_thong_so, tu, den)
    except Exception:
        import luu_tru
        return luu_tru.doc_chuoi(ma_tram, ten_thong_so, tu, den)
