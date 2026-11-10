# -*- coding: utf-8 -*-
r"""
Chuan hoa danh muc ho, ao, dam KHONG DUOC SAN LAP thanh lop GeoJSON.

Dau vao : data_goc/ao_ho_khong_san_lap/*.csv
          Ban xuat cua Google Sheet dung sau ung dung Apps Script
          "THONG TIN HO, AO, DAM KHONG DUOC SAN LAP" cua tinh.
Dau ra  : data/ao_ho_khong_san_lap.geojson  (EPSG:4326)

VI SAO PHAI XUAT CSV BANG TAY

Ung dung Apps Script do KHONG co duong tra JSON: 31 ham may chu cua no
(getStationData, getDataSourceInfo, _sheetToJSON, ...) deu goi qua kenh RPC
google.script.run, chi chay duoc tu ben trong trang. Duong HTTP duy nhat la
doGet va no tra ve HTML, noi dung lai nam trong iframe sandbox khac origin.
Ung dung con co phan quyen (isUserAuthorized, logAccess) va khoa tai ve bang
mat khau. Vi vay khong tu dong hoa duoc, phai xuat Sheet ra CSV.

BA DIEU SCRIPT TU XOAY XO, VI CHUA AI BIET CSV CO COT GI

1. Do ten cot theo danh sach ten ung vien sau khi bo dau, giong cach
   BANG_ANH_XA trong backend/chuan_hoa.py lam. Cot la thi GIU LAI chu khong
   vut di. Bang anh xa da chon duoc IN RA, vi mot cot anh xa nham van cho ra
   so hop le va se khong ai phat hien.

2. Tu nhan biet he toa do THEO DO LON, khong tin khai bao. Nguoi dung nho la
   VN-2000 X/Y con ung dung ghi nhan la "Toa do WGS84", hai dieu do lech nhau.
   Do lon thi khong noi doi: do thap phan nam trong +-180, con met thi hang
   tram nghin. Thu tu hai so cung tu suy duoc, xem nhan_biet_he().

3. Kiem diem co roi vao khung bao cua tinh khong. Diem ngoai khung duoc DEM
   va LIET KE, khong im lang bo di - cung nguyen tac voi khoi thong_ke cua
   backend/khong_gian.tap_feature(). Nhieu diem ngoai khung thuong nghia la
   nhan nham he toa do hoac lon X voi Y.

Khong doc duoc ban ghi nao thi dung han, KHONG ghi de tep cu. Chot nay lay tu
scripts/08_xuat_lo_khoan_ndd.py.

Script chi dung thu vien chuan khi toa do da la WGS84. Chi khi phai chuyen he
no moi nap pyproj, va khi do goi sua_duong_dan_proj() truoc - bay PROJ cua may
nay, xem CLAUDE.md.

Chay:  python scripts/09_chuan_hoa_ao_ho_khong_san_lap.py
"""

import csv
import glob
import io
import json
import os
import re
import sys
import unicodedata
from datetime import datetime, timedelta, timezone

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import tinh as mod_tinh

MUI_GIO_VN = timezone(timedelta(hours=7))

THU_MUC_NGUON = os.path.join("data_goc", "ao_ho_khong_san_lap")
TEN_TEP_RA = "ao_ho_khong_san_lap.geojson"
TIEN_TO_MA = "AH"

NGUON_DL = ("Danh mục hồ, ao, đầm không được san lấp do tỉnh công bố, "
            "trích xuất từ bảng dữ liệu của phần mềm quản lý danh mục")


# ---------------------------------------------------------------------------
# So khop ten cot
# ---------------------------------------------------------------------------

def bo_dau(chu):
    """Bo dau tieng Viet va ha chu thuong.

    Giong bo_dau() trong assets/js/config.js va backend/chuan_hoa.py, de moi
    noi trong du an so khop giong nhau.
    """
    if chu is None:
        return ""
    chu = unicodedata.normalize("NFD", str(chu))
    chu = "".join(c for c in chu if unicodedata.category(c) != "Mn")
    return chu.replace("đ", "d").replace("Đ", "D").lower()


def khoa_cot(ten_cot):
    """Dua ten cot ve dang so khop: bo dau, bo moi ky tu khong phai chu so."""
    return re.sub(r"[^a-z0-9]", "", bo_dau(ten_cot))


# Khoa la ten truong dau ra, phai khop khai bao trong assets/js/config.js.
# Gia tri la cac ten cot co the gap trong CSV, da qua khoa_cot().
# Ten tu ung dung Apps Script duoc dat len dau moi danh sach.
BANG_ANH_XA = {
    "ma": ["ma", "mahieu", "masohieu", "sohieu", "stt", "id", "code"],
    "ten": ["name", "ten", "tenho", "tenhoao", "tencongtrinh", "tenhoaodam"],
    "vi_tri_hc": ["description", "vitri", "diadiem", "vitridiadiem", "diachi",
                  "xa", "phuong", "xaphuong", "vitrihanhchinh"],
    "dien_tich_ha": ["sdieutra", "dientich", "dientichmatnuoc", "dientichha",
                     "smatnuoc", "dientichdieutra"],
    "chuc_nang": ["chucnang", "mucdichsudung", "mucdich", "congdung"],
    "don_vi_quan_ly": ["dvquanly", "donviquanly", "donvi", "quanly"],
    "nam_xd": ["namxdht", "namxaydung", "namxd", "namhoanthanh"],
    "quyet_dinh": ["quyetdinh", "sovanban", "vanban", "qd", "canccuphaply",
                   "cancuphaply"],
    "ghi_chu": ["ghichu", "note", "remark"],
}

# Cot toa do. Tach rieng vi chung khong di vao thuoc tinh dau ra.
COT_TOA_DO_GOP = ["coordinates", "coordinate", "toado", "toadowgs84",
                  "toadodiem", "toadovitri", "latlon", "latlong"]
COT_KINH_DO = ["kinhdo", "longitude", "long", "lon", "lng", "x", "toadox",
               "xvn2000", "xm"]
COT_VI_DO = ["vido", "latitude", "lat", "y", "toadoy", "yvn2000", "ym"]


def dung_anh_xa(ten_cac_cot):
    """Tra ve (anh_xa, cot_toa_do, cot_la).

    anh_xa     : {ten cot goc -> ten truong noi bo}
    cot_toa_do : {"gop"|"kinh_do"|"vi_do" -> ten cot goc}
    cot_la     : danh sach ten cot khong anh xa duoc, van se duoc giu lai
    """
    anh_xa = {}
    cot_toa_do = {}
    cot_la = []
    da_dung = set()

    for cot in ten_cac_cot:
        k = khoa_cot(cot)
        if not k:
            continue

        if k in COT_TOA_DO_GOP and "gop" not in cot_toa_do:
            cot_toa_do["gop"] = cot
            continue
        if k in COT_KINH_DO and "kinh_do" not in cot_toa_do:
            cot_toa_do["kinh_do"] = cot
            continue
        if k in COT_VI_DO and "vi_do" not in cot_toa_do:
            cot_toa_do["vi_do"] = cot
            continue

        truong = None
        for ten_truong, ung_vien in BANG_ANH_XA.items():
            if ten_truong in da_dung:
                continue
            if k in ung_vien:
                truong = ten_truong
                break

        if truong:
            anh_xa[cot] = truong
            da_dung.add(truong)
        else:
            cot_la.append(cot)

    return anh_xa, cot_toa_do, cot_la


def ten_truong_cho_cot_la(cot):
    """Ten truong cho mot cot khong anh xa duoc: bo dau, gach duoi.

    Giu lai cot la chu khong vut di, vi bang nguon cua tinh co the co cot
    quan trong ma bang anh xa chua biet. Ten duoc chuan hoa de con dung lam
    khoa JSON va cot CSV khi xuat.
    """
    ten = re.sub(r"[^a-z0-9]+", "_", bo_dau(cot)).strip("_")
    return ten or "cot_khong_ten"


# ---------------------------------------------------------------------------
# Doc so va toa do
# ---------------------------------------------------------------------------

def doc_so(chu):
    """Doc mot so tu chuoi, chiu duoc dau phay thap phan va dau phan nhom.

    Bang tieng Viet hay ghi 1.234,56 con ban xuat tieng Anh ghi 1,234.56. Cach
    phan biet: dau nao DUNG SAU cung thi dau do la dau thap phan.
    """
    if chu is None:
        return None
    s = str(chu).strip().replace(" ", "")
    if not s:
        return None
    s = re.sub(r"[^0-9,.\-+]", "", s)
    if not s or s in ("-", "+", ".", ","):
        return None

    vi_phay = s.rfind(",")
    vi_cham = s.rfind(".")
    if vi_phay >= 0 and vi_cham >= 0:
        if vi_phay > vi_cham:
            s = s.replace(".", "").replace(",", ".")
        else:
            s = s.replace(",", "")
    elif vi_phay >= 0:
        # Chi co dau phay. La thap phan tru khi no dung lam dau phan nhom
        # (vi du 1,234,567), nhan ra bang viec co dung ba chu so sau moi dau.
        if re.fullmatch(r"[-+]?\d{1,3}(,\d{3})+", s):
            s = s.replace(",", "")
        else:
            s = s.replace(",", ".")

    try:
        return float(s)
    except ValueError:
        return None


def doc_do_phut_giay(chu):
    """Doc toa do dang do-phut-giay, vi du 109°10'48\"E hoac 12 15 30 N.

    Truong Coordinates cua ung dung la van ban tu do nen phai chiu duoc dang
    nay. Tra ve None neu chuoi khong phai do-phut-giay.
    """
    if chu is None:
        return None
    s = str(chu).strip()
    if not s:
        return None

    cac_so = re.findall(r"\d+(?:[.,]\d+)?", s)
    if len(cac_so) < 2:
        return None
    # Phai co it nhat mot ky hieu do/phut/giay, neu khong thi day chi la mot
    # cap so thuong va phai de ham khac xu ly.
    if not re.search(r"[°'\"\u2032\u2033d]", s, re.IGNORECASE):
        return None

    phan = [doc_so(x) for x in cac_so[:3]]
    phan = [p for p in phan if p is not None]
    if not phan:
        return None

    gia_tri = phan[0]
    if len(phan) > 1:
        gia_tri += phan[1] / 60.0
    if len(phan) > 2:
        gia_tri += phan[2] / 3600.0

    if re.search(r"[SW]\b|[SW]$", s.upper()):
        gia_tri = -gia_tri
    return gia_tri


def doc_mot_toa_do(chu):
    """Doc mot gia tri toa do, chap nhan ca do thap phan va do-phut-giay."""
    gia_tri = doc_do_phut_giay(chu)
    if gia_tri is not None:
        return gia_tri
    return doc_so(chu)


def tach_cap_toa_do(chu):
    """Tach mot o toa do gop thanh hai so, vi du "12.25, 109.18".

    Chua biet so nao truoc: nhan_biet_he() se tu sap xep lai.
    """
    if chu is None:
        return None
    s = str(chu).strip()
    if not s:
        return None

    # Tach theo dau phay, cham phay hoac khoang trang, nhung khong duoc tach
    # nham dau phay thap phan. Thu dau phay truoc, neu ra dung hai manh co so
    # thi dung.
    for dau in [";", ",", "|", "/"]:
        if dau in s:
            manh = [m for m in s.split(dau) if m.strip()]
            if len(manh) == 2:
                a = doc_mot_toa_do(manh[0])
                b = doc_mot_toa_do(manh[1])
                if a is not None and b is not None:
                    return (a, b)

    cac_so = re.findall(r"[-+]?\d+(?:[.,]\d+)?", s)
    if len(cac_so) >= 2:
        a = doc_so(cac_so[0])
        b = doc_so(cac_so[1])
        if a is not None and b is not None:
            return (a, b)
    return None


def nhan_biet_he(cac_cap):
    """Nhan biet he toa do va thu tu hai so, tra ve (ten_he, doi_cho).

    ten_he  : "wgs84" neu da la do thap phan, "met" neu la toa do phang
    doi_cho : True neu so thu nhat la vi do / tung do (phai dao lai)

    VI SAO DOAN DUOC CHAC: hai khoang gia tri khong giao nhau.
      - WGS84 o Viet Nam: vi do 8..24, kinh do 102..118. So nao lon hon 100 la
        kinh do, khong the nham.
      - VN-2000 mui 3 do: hoanh do quanh 500.000 m (false easting), tung do
        hon 1.200.000 m. So lon hon la tung do.
    """
    if not cac_cap:
        return ("wgs84", False)

    lon_nhat = max(max(abs(a), abs(b)) for a, b in cac_cap)
    he = "wgs84" if lon_nhat <= 180 else "met"

    # Dem xem trong moi cap, so thu nhat hay so thu hai dong vai "kinh do"
    # (WGS84) hay "hoanh do" (met). Lay da so de chiu duoc vai dong hong.
    thu_nhat_lon_hon = 0
    for a, b in cac_cap:
        if abs(a) > abs(b):
            thu_nhat_lon_hon += 1

    if he == "wgs84":
        # Kinh do lon hon vi do. Neu so thu nhat KHONG lon hon thi no la vi do
        # va phai dao lai, vi GeoJSON can [kinh do, vi do].
        doi_cho = thu_nhat_lon_hon < len(cac_cap) / 2.0
    else:
        # Tung do lon hon hoanh do. So thu nhat lon hon nghia la no la tung
        # do, phai dao lai de thanh (hoanh do, tung do).
        doi_cho = thu_nhat_lon_hon > len(cac_cap) / 2.0

    return (he, doi_cho)


def chuyen_ve_wgs84(cac_cap, epsg_nguon):
    """Chuyen danh sach (x, y) tu he phang ve (kinh do, vi do).

    Chi goi khi THUC SU phai chuyen he. pyproj duoc nap ngay tai day, sau khi
    sua_duong_dan_proj() da chay - bay PROJ cua may nay lam pyproj doc nham
    proj.db neu nap som.
    """
    from moi_truong_proj import sua_duong_dan_proj
    sua_duong_dan_proj()

    from pyproj import Transformer
    bo_chuyen = Transformer.from_crs("EPSG:{}".format(epsg_nguon),
                                     "EPSG:4326", always_xy=True)
    return [bo_chuyen.transform(x, y) for x, y in cac_cap]


# ---------------------------------------------------------------------------
# Doc tep CSV
# ---------------------------------------------------------------------------

def tim_tep_csv(goc):
    """Tim tep CSV dau tien trong thu muc nguon."""
    thu_muc = os.path.join(goc, THU_MUC_NGUON)
    cac_tep = sorted(glob.glob(os.path.join(thu_muc, "*.csv")))
    if not cac_tep:
        raise SystemExit(
            "Không thấy tệp CSV nào trong:\n"
            "    {}\n\n"
            "Cách lấy: mở Google Sheet nguồn của ứng dụng danh mục hồ ao đầm,\n"
            "chọn Tệp > Tải xuống > Giá trị phân tách bằng dấu phẩy (.csv),\n"
            "rồi đặt tệp vào thư mục trên. Tên tệp đặt thế nào cũng được."
            .format(thu_muc))
    if len(cac_tep) > 1:
        print("Có {} tệp CSV, dùng tệp đầu: {}"
              .format(len(cac_tep), os.path.basename(cac_tep[0])))
    return cac_tep[0]


def doc_csv(duong_dan):
    """Doc CSV, tra ve (ten_cac_cot, cac_dong).

    utf-8-sig de nuot BOM: ban xuat cua Google Sheet luon co BOM, khong bo thi
    ten cot dau tien dinh ky tu la va khong anh xa duoc.
    """
    for ma_hoa in ("utf-8-sig", "utf-8", "cp1258", "latin-1"):
        try:
            with io.open(duong_dan, encoding=ma_hoa, newline="") as f:
                mau = f.read(8192)
                f.seek(0)
                try:
                    dau_tach = csv.Sniffer().sniff(mau, delimiters=",;\t").delimiter
                except csv.Error:
                    dau_tach = ","
                doc = csv.DictReader(f, delimiter=dau_tach)
                cac_dong = list(doc)
                ten_cac_cot = list(doc.fieldnames or [])
            if ma_hoa != "utf-8-sig":
                print("  Cảnh báo: tệp không phải UTF-8, đã đọc bằng {}."
                      .format(ma_hoa))
            return ten_cac_cot, cac_dong
        except UnicodeDecodeError:
            continue
    raise SystemExit("Không đọc được tệp CSV bằng bất kỳ bảng mã nào đã thử.")


# ---------------------------------------------------------------------------
# Chuong trinh chinh
# ---------------------------------------------------------------------------

def main():
    tt = mod_tinh.nap()
    goc = tt["_goc"]
    tep_ra = mod_tinh.duong_dan_ra(tt, TEN_TEP_RA)

    tep_vao = tim_tep_csv(goc)
    print("Đọc: {}".format(tep_vao))
    ten_cac_cot, cac_dong = doc_csv(tep_vao)
    print("  Số cột  : {}".format(len(ten_cac_cot)))
    print("  Số dòng : {}".format(len(cac_dong)))
    if not cac_dong:
        raise SystemExit("Tệp CSV không có dòng dữ liệu nào. Dừng, không ghi đè.")

    # --- Anh xa ten cot ---
    anh_xa, cot_toa_do, cot_la = dung_anh_xa(ten_cac_cot)

    print("\nÁnh xạ cột đã chọn:")
    for cot, truong in anh_xa.items():
        print("  {:<38} -> {}".format(cot[:38], truong))
    for vai, cot in cot_toa_do.items():
        print("  {:<38} -> (tọa độ: {})".format(cot[:38], vai))
    if cot_la:
        print("\nCột không có trong bảng ánh xạ, vẫn được giữ lại:")
        for cot in cot_la:
            print("  {:<38} -> {}".format(cot[:38], ten_truong_cho_cot_la(cot)))
        print("  Nếu cột nào quan trọng, thêm tên nó vào BANG_ANH_XA rồi chạy lại.")

    if not cot_toa_do:
        raise SystemExit(
            "\nKhông nhận ra cột tọa độ nào. Các cột có trong tệp:\n  {}\n"
            "Thêm tên cột tọa độ vào COT_TOA_DO_GOP, COT_KINH_DO hoặc "
            "COT_VI_DO rồi chạy lại.".format("\n  ".join(ten_cac_cot)))

    # --- Doc toa do tho ---
    cac_cap = []          # [(a, b)] theo dung thu tu trong tep
    chi_so_co_toa_do = []  # vi tri dong tuong ung
    so_thieu_toa_do = 0

    for i, dong in enumerate(cac_dong):
        cap = None
        if "gop" in cot_toa_do:
            cap = tach_cap_toa_do(dong.get(cot_toa_do["gop"]))
        if cap is None and "kinh_do" in cot_toa_do and "vi_do" in cot_toa_do:
            a = doc_mot_toa_do(dong.get(cot_toa_do["kinh_do"]))
            b = doc_mot_toa_do(dong.get(cot_toa_do["vi_do"]))
            if a is not None and b is not None:
                cap = (a, b)
        if cap is None:
            so_thieu_toa_do += 1
            continue
        cac_cap.append(cap)
        chi_so_co_toa_do.append(i)

    if not cac_cap:
        raise SystemExit(
            "\nKhông đọc được tọa độ của dòng nào. Dừng, không ghi đè tệp cũ.")

    # --- Nhan biet he toa do ---
    he, doi_cho = nhan_biet_he(cac_cap)
    print("\nHệ tọa độ script tự nhận: {}{}".format(
        "WGS84 (độ thập phân)" if he == "wgs84"
        else "tọa độ phẳng, mét (EPSG:{})".format(tt.get("epsg_chuyen_de")),
        ", hai số bị đảo thứ tự nên đã hoán lại" if doi_cho else ""))

    if doi_cho:
        cac_cap = [(b, a) for a, b in cac_cap]

    if he == "met":
        cac_cap = chuyen_ve_wgs84(cac_cap, tt.get("epsg_chuyen_de", 9217))

    # --- Kiem khung bao ---
    # Diem ngoai khung bi BO khoi tep va duoc BAO ro, giong cach
    # backend/khong_gian.tap_feature() lam voi bo_ngoai_tinh. Giu lai thi ban
    # do ve mot diem o tinh khac va khong ai hieu vi sao.
    kb = tt.get("khung_bao_nen") or [-180, -90, 180, 90]
    trong_khung = []
    ngoai_khung = []
    for vi_tri, (kd, vd) in zip(chi_so_co_toa_do, cac_cap):
        if kb[0] <= kd <= kb[2] and kb[1] <= vd <= kb[3]:
            trong_khung.append((vi_tri, kd, vd))
        else:
            ngoai_khung.append((vi_tri, kd, vd))

    print("\nKiểm tra khung bao của tỉnh [{}, {}, {}, {}]:".format(*kb))
    print("  Trong khung : {}".format(len(trong_khung)))
    print("  Ngoài khung : {} (bỏ khỏi tệp)".format(len(ngoai_khung)))
    if ngoai_khung:
        print("  Các dòng nằm ngoài (dòng 1 là dòng dữ liệu đầu tiên):")
        for vi_tri, kd, vd in ngoai_khung[:20]:
            ten = ""
            for cot, truong in anh_xa.items():
                if truong == "ten":
                    ten = (cac_dong[vi_tri].get(cot) or "").strip()
            print("    dòng {:<5} {:<34} {:.5f}, {:.5f}"
                  .format(vi_tri + 1, ten[:34], kd, vd))
        if len(ngoai_khung) > 20:
            print("    ... và {} dòng nữa".format(len(ngoai_khung) - 20))
        print("  Nhiều dòng ngoài khung thường nghĩa là nhận nhầm hệ tọa độ")
        print("  hoặc lộn X với Y. Xem lại trước khi dùng tệp kết quả.")

    if not trong_khung:
        raise SystemExit(
            "\nKhông dòng nào nằm trong khung bao của tỉnh. Dừng, không ghi "
            "đè tệp cũ.\nGần như chắc chắn là nhận nhầm hệ tọa độ: kiểm lại "
            "cột tọa độ trong CSV.")

    # --- Dung doi tuong ---
    thoi_diem_xuat = datetime.now(MUI_GIO_VN).isoformat(timespec="minutes")
    nguon_dl = "{}, trích xuất ngày {}".format(
        NGUON_DL, datetime.now(MUI_GIO_VN).strftime("%d/%m/%Y"))

    cac_doi_tuong = []
    so_thu_tu = 0
    for vi_tri, kd, vd in trong_khung:
        dong = cac_dong[vi_tri]
        so_thu_tu += 1

        thuoc_tinh = {}
        for cot, truong in anh_xa.items():
            gia_tri = (dong.get(cot) or "").strip()
            if not gia_tri:
                continue
            if truong in ("dien_tich_ha",):
                so = doc_so(gia_tri)
                if so is not None:
                    thuoc_tinh[truong] = so
            else:
                thuoc_tinh[truong] = gia_tri

        for cot in cot_la:
            gia_tri = (dong.get(cot) or "").strip()
            if gia_tri:
                thuoc_tinh[ten_truong_cho_cot_la(cot)] = gia_tri

        # Ma: giu ma cua nguon neu co, khong thi tu danh so. Lop nao cung can
        # truong khoa vi config.js dung no lam "khoa" va xuat CSV theo no.
        if not thuoc_tinh.get("ma"):
            thuoc_tinh["ma"] = "{}-{:03d}".format(TIEN_TO_MA, so_thu_tu)
        if not thuoc_tinh.get("ten"):
            thuoc_tinh["ten"] = "Hồ, ao, đầm {}".format(thuoc_tinh["ma"])

        thuoc_tinh["nguon_dl"] = nguon_dl

        cac_doi_tuong.append({
            "type": "Feature",
            "geometry": {"type": "Point",
                         "coordinates": [round(kd, 7), round(vd, 7)]},
            "properties": thuoc_tinh,
        })

    tap = {
        "type": "FeatureCollection",
        "name": "ao_ho_khong_san_lap",
        "crs": {"type": "name",
                "properties": {"name": "urn:ogc:def:crs:OGC:1.3:CRS84"}},
        "nguon_dl": nguon_dl,
        "thoi_diem_xuat": thoi_diem_xuat,
        "features": cac_doi_tuong,
    }

    with io.open(tep_ra, "w", encoding="utf-8", newline="\n") as f:
        json.dump(tap, f, ensure_ascii=False, indent=1)

    print("\nĐã ghi: {}".format(tep_ra))
    print("  Đối tượng       : {}".format(len(cac_doi_tuong)))
    print("  Thiếu tọa độ    : {} (không đưa vào tệp)".format(so_thieu_toa_do))
    print("  Ngoài khung bao : {} (không đưa vào tệp)".format(len(ngoai_khung)))
    print("  Thời điểm xuất  : {}".format(thoi_diem_xuat))
    print("\nNhớ thêm \"ao_ho_khong_san_lap\" vào lop_co_san trong tinh.json,")
    print("nếu chưa có. Có tệp mà không đăng ký thì lớp không bao giờ được nạp.")


if __name__ == "__main__":
    main()
