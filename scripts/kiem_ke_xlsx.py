# -*- coding: utf-8 -*-
r"""
Phan dung chung cua hai script nap ban ra soat kiem ke (tep Excel):

    scripts/12_nap_ao_ho_kiem_ke.py     sheet B3.2.Ho  -> data/ao_ho.geojson
    scripts/13_nap_wqi_dia_phuong.py    sheet Bieu 10  -> data/quan_trac_dia_phuong.geojson

Tep nguon: CSDL/dulieu_thuc/TH_Kiemke_*.xlsx

VI SAO CO MO-DUN NAY

Ca hai sheet deu KHONG co toa do trong ban goc; nguoi dung tu bo sung cot toa
do vao Excel. Chua ai biet cot do se duoc dat ten gi, ghi theo he nao, nen ca
hai script can dung mot cach xu ly, va cach do da co san trong
scripts/09_chuan_hoa_ao_ho_khong_san_lap.py. Mo-dun nay GOI LAI cac ham cua
script 09 (doc so, tach cap toa do, nhan biet he theo do lon, chuyen he) chu
khong chep lai, de quy tac chi nam mot noi.

Ba chot giu nguyen tu script 09:

1. Do ten cot theo ten ung vien sau khi bo dau va IN RA bang anh xa. Mot cot
   anh xa nham van cho ra so hop le nen khong nhin thay thi khong phat hien.
2. Tu nhan he toa do THEO DO LON, khong tin khai bao.
3. Dong thieu toa do va diem ngoai khung_bao_nen bi BO khoi tep va BAO SO
   LUONG. Khong con dong nao thi dung han, KHONG ghi de tep cu.

geopandas chi duoc nap khi gan luu vuc, tuc la sau khi da co toa do hop le.
Excel chua co cot toa do thi script dung som va chi can openpyxl.
"""

import argparse
import glob
import importlib
import io
import json
import os
import re
import sys
from datetime import datetime, timedelta, timezone

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import tinh as mod_tinh

MUI_GIO_VN = timezone(timedelta(hours=7))

# Tep nguon, duong dan tuong doi so voi goc du an. Dau * vi ten tep mang ca
# danh sach bieu va chu "rasoat", se doi theo tung dot ra soat.
MAU_TEP_NGUON = ["CSDL/dulieu_thuc/TH_Kiemke*.xlsx",
                 "data_goc/TH_Kiemke*.xlsx"]

# Ten cot toa do co the gap, ngoai danh sach cua script 09. So khop theo TIEN
# TO vi nguoi dung hay ghi kem don vi hoac ten he: "Kinh do (WGS84)", "X VN2000".
TIEN_TO_KINH_DO = ["kinhdo", "longitude", "toadox", "xvn", "xm", "xwgs"]
TIEN_TO_VI_DO = ["vido", "latitude", "toadoy", "yvn", "ym", "ywgs"]
TIEN_TO_GOP = ["toado", "coordinate", "latlon", "latlong"]


def nap_script(ten):
    """Nap mot script co ten bat dau bang chu so nhu mot mo-dun.

    Cau lenh "import 09_..." khong viet duoc vi ten bat dau bang so, nhung
    importlib thi nap duoc. Dung de goi lai ham cua script 05 va 09.
    """
    return importlib.import_module(ten)


def ham_toa_do():
    """Mo-dun script 09, noi giu cac ham doc so va nhan biet he toa do."""
    return nap_script("09_chuan_hoa_ao_ho_khong_san_lap")


def khoa_cot(ten_cot):
    return ham_toa_do().khoa_cot(ten_cot)


def bo_dau(chu):
    return ham_toa_do().bo_dau(chu)


# ---------------------------------------------------------------------------
# Tham so dong lenh va tep nguon
# ---------------------------------------------------------------------------

def doc_tham_so(mo_ta):
    """Hai tham so tuy chon, chu yeu de chay thu ma khong dung vao data/."""
    bo = argparse.ArgumentParser(description=mo_ta)
    bo.add_argument("--tep", help="Tep Excel nguon. Mac dinh tu tim trong "
                                  "CSDL/dulieu_thuc/")
    bo.add_argument("--thu-muc-ra", dest="thu_muc_ra",
                    help="Thu muc ghi ket qua. Mac dinh la data/ cua du an")
    return bo.parse_args()


def tim_tep_xlsx(tt, tep_chi_dinh=None):
    if tep_chi_dinh:
        if not os.path.isfile(tep_chi_dinh):
            raise SystemExit("Không thấy tệp: {}".format(tep_chi_dinh))
        return tep_chi_dinh
    for mau in MAU_TEP_NGUON:
        cac_tep = sorted(glob.glob(os.path.join(tt["_goc"], *mau.split("/"))))
        # Bo tep tam cua Excel (~$...) sinh ra khi tep dang mo
        cac_tep = [t for t in cac_tep
                   if not os.path.basename(t).startswith("~$")]
        if cac_tep:
            if len(cac_tep) > 1:
                print("Có {} tệp khớp, dùng tệp đầu: {}".format(
                    len(cac_tep), os.path.basename(cac_tep[0])))
            return cac_tep[0]
    raise SystemExit("Không thấy tệp Excel kiểm kê. Đã tìm theo mẫu:\n  {}"
                     .format("\n  ".join(MAU_TEP_NGUON)))


def doc_sheet(tep, khoa_sheet):
    """Doc mot sheet thanh danh sach dong (moi dong la mot list gia tri).

    khoa_sheet la ten sheet da qua khoa_cot(), vi du "b32ho" cho "B3.2.Hồ".
    So khop theo khoa de chiu duoc thay doi nho ve dau cham, khoang trang.
    """
    import openpyxl
    so = openpyxl.load_workbook(tep, read_only=True, data_only=True)
    try:
        ten_sheet = None
        for ten in so.sheetnames:
            if khoa_cot(ten) == khoa_sheet:
                ten_sheet = ten
                break
        if ten_sheet is None:
            raise SystemExit("Không thấy sheet có khóa '{}'. Các sheet có "
                             "trong tệp: {}".format(khoa_sheet,
                                                    ", ".join(so.sheetnames)))
        cac_dong = [list(d) for d in so[ten_sheet].iter_rows(values_only=True)]
    finally:
        so.close()
    print("Sheet '{}': {} dòng".format(ten_sheet, len(cac_dong)))
    return cac_dong


def tim_dong_tieu_de(cac_dong):
    """Chi so dong tieu de: dong dau tien co o dau la 'STT'."""
    for i, dong in enumerate(cac_dong):
        if dong and khoa_cot(dong[0]) == "stt":
            return i
    raise SystemExit("Không thấy dòng tiêu đề (dòng có ô đầu là 'STT').")


def sach(gia_tri):
    """Lam sach mot o chu: bo khoang trang thua, o rong va '-' thanh None."""
    if gia_tri is None:
        return None
    s = re.sub(r"\s+", " ", str(gia_tri)).strip()
    if not s or s in ("-", "--", "—"):
        return None
    return s


def so_hoc(gia_tri, so_le=None):
    """O so cua Excel -> so thuc. '-' va o rong thanh None, '0,018' thanh 0.018.

    KHONG dung doc_so() cua script 09 cho o thuoc tinh. Ham do coi "0,018" la
    dau phan nhom kieu tieng Anh va tra ve 18: dung tich mot cai ho se thanh
    18 trieu m3 thay vi 0,018. O day la bieu tieng Viet, o nao Excel da hieu
    la so thi den day da la so; o con la CHU thi dau phay la dau thap phan.
    Dau cham chi la dau phan nhom khi di kem dau phay hoac lap lai (1.234.567).
    """
    if gia_tri is None or isinstance(gia_tri, bool):
        return None
    if isinstance(gia_tri, (int, float)):
        so = float(gia_tri)
    else:
        s = re.sub(r"\s", "", str(gia_tri))
        if "," in s:
            s = s.replace(".", "").replace(",", ".")
        elif s.count(".") > 1:
            s = s.replace(".", "")
        if not re.fullmatch(r"[-+]?\d+(\.\d+)?", s):
            return None
        so = float(s)
    if so_le is not None:
        # Lam tron de bo nhieu dau phay dong cua Excel (0.005039999999999999)
        so = round(so, so_le)
    return so


# ---------------------------------------------------------------------------
# Anh xa cot
# ---------------------------------------------------------------------------

def _bat_dau_bang(khoa, cac_tien_to):
    return any(khoa.startswith(t) for t in cac_tien_to)


def vai_toa_do(ten_cot):
    """'kinh_do' | 'vi_do' | 'gop' neu ten cot la cot toa do, khong thi None."""
    m09 = ham_toa_do()
    k = khoa_cot(ten_cot)
    if not k:
        return None
    if k in m09.COT_KINH_DO or _bat_dau_bang(k, TIEN_TO_KINH_DO):
        return "kinh_do"
    if k in m09.COT_VI_DO or _bat_dau_bang(k, TIEN_TO_VI_DO):
        return "vi_do"
    if k in m09.COT_TOA_DO_GOP or _bat_dau_bang(k, TIEN_TO_GOP):
        return "gop"
    return None


def dung_anh_xa(ten_cac_cot, bang_anh_xa):
    """Tra ve (anh_xa, cot_toa_do, cot_la), tat ca theo CHI SO cot.

    anh_xa     : {ten truong -> chi so cot}
    cot_toa_do : {"gop"|"kinh_do"|"vi_do" -> chi so cot}
    cot_la     : [chi so cot] co ten nhung khong nhan ra
    """
    anh_xa = {}
    cot_toa_do = {}
    cot_la = []
    for i, ten in enumerate(ten_cac_cot):
        k = khoa_cot(ten)
        if not k:
            continue
        vai = vai_toa_do(ten)
        if vai and vai not in cot_toa_do:
            cot_toa_do[vai] = i
            continue
        truong = None
        for ten_truong, ung_vien in bang_anh_xa.items():
            if ten_truong not in anh_xa and k in ung_vien:
                truong = ten_truong
                break
        if truong:
            anh_xa[truong] = i
        else:
            cot_la.append(i)
    return anh_xa, cot_toa_do, cot_la


def in_anh_xa(ten_cac_cot, anh_xa, cot_toa_do, cot_la):
    def nhan(i):
        return re.sub(r"\s+", " ", str(ten_cac_cot[i]))[:44]

    print("\nÁnh xạ cột đã chọn:")
    for truong, i in sorted(anh_xa.items(), key=lambda x: x[1]):
        print("  {:<46} -> {}".format(nhan(i), truong))
    for vai, i in cot_toa_do.items():
        print("  {:<46} -> (tọa độ: {})".format(nhan(i), vai))
    if cot_la:
        print("Cột không nhận ra, KHÔNG đưa vào tệp kết quả:")
        for i in cot_la:
            print("  {}".format(nhan(i)))


def o(dong, chi_so):
    """Gia tri mot o, chiu duoc dong ngan hon so cot."""
    if chi_so is None or chi_so >= len(dong):
        return None
    return dong[chi_so]


# ---------------------------------------------------------------------------
# Toa do
# ---------------------------------------------------------------------------

def bao_thieu_cot_toa_do(ten_sheet, ten_cac_cot):
    cac_ten = [re.sub(r"\s+", " ", str(t)) for t in ten_cac_cot if sach(t)]
    raise SystemExit(
        "\nDỪNG: sheet {} chưa có cột tọa độ, KHÔNG ghi đè tệp nào.\n"
        "Các cột đang có:\n  {}\n\n"
        "Thêm vào sheet hai cột tọa độ đặt tên 'X' và 'Y' (hoặc 'Kinh độ' và\n"
        "'Vĩ độ'), hoặc một cột 'Tọa độ' ghi cả hai số, tiêu đề đặt cùng dòng\n"
        "với ô 'STT'. Ghi theo VN-2000 (mét) hay WGS84 (độ) đều được, thứ tự\n"
        "hai số cũng không quan trọng: script tự nhận theo độ lớn. Rồi chạy lại."
        .format(ten_sheet, "\n  ".join(cac_ten)))


def giai_toa_do(tt, cac_ban_ghi, cot_toa_do, ten_cua):
    """Doc, nhan biet he va kiem khung bao toa do cho danh sach ban ghi.

    cac_ban_ghi : danh sach dong Excel (moi dong mot doi tuong)
    cot_toa_do  : ket qua cua dung_anh_xa()
    ten_cua     : ham (dong) -> ten doi tuong, chi de in thong bao

    Tra ve (ket_qua, thong_ke): ket_qua la [(vi_tri, kinh_do, vi_do)] cua cac
    dong nam trong khung bao, vi_tri la chi so trong cac_ban_ghi.
    """
    m09 = ham_toa_do()
    cac_cap = []
    vi_tri_co = []
    thieu = []

    for i, dong in enumerate(cac_ban_ghi):
        cap = None
        if "gop" in cot_toa_do:
            cap = m09.tach_cap_toa_do(o(dong, cot_toa_do["gop"]))
        if cap is None and "kinh_do" in cot_toa_do and "vi_do" in cot_toa_do:
            a = m09.doc_mot_toa_do(o(dong, cot_toa_do["kinh_do"]))
            b = m09.doc_mot_toa_do(o(dong, cot_toa_do["vi_do"]))
            if a is not None and b is not None:
                cap = (a, b)
        if cap is None:
            thieu.append(i)
            continue
        cac_cap.append(cap)
        vi_tri_co.append(i)

    print("\nTọa độ: đọc được {} / {} dòng".format(len(cac_cap),
                                                 len(cac_ban_ghi)))
    if thieu:
        print("  Thiếu tọa độ {} dòng (bỏ khỏi tệp):".format(len(thieu)))
        for i in thieu[:15]:
            print("    {}".format(ten_cua(cac_ban_ghi[i])))
        if len(thieu) > 15:
            print("    ... và {} dòng nữa".format(len(thieu) - 15))

    if not cac_cap:
        raise SystemExit("\nDỪNG: không đọc được tọa độ của dòng nào, "
                         "KHÔNG ghi đè tệp cũ.")

    he, doi_cho = m09.nhan_biet_he(cac_cap)
    print("Hệ tọa độ script tự nhận: {}{}".format(
        "WGS84 (độ thập phân)" if he == "wgs84"
        else "tọa độ phẳng, mét (EPSG:{})".format(tt.get("epsg_chuyen_de")),
        ", hai số bị đảo thứ tự nên đã hoán lại" if doi_cho else ""))
    if doi_cho:
        cac_cap = [(b, a) for a, b in cac_cap]
    if he == "met":
        cac_cap = m09.chuyen_ve_wgs84(cac_cap, tt.get("epsg_chuyen_de", 9217))

    kb = tt.get("khung_bao_nen") or [-180, -90, 180, 90]
    trong = []
    ngoai = []
    for vi_tri, (kd, vd) in zip(vi_tri_co, cac_cap):
        if kb[0] <= kd <= kb[2] and kb[1] <= vd <= kb[3]:
            trong.append((vi_tri, kd, vd))
        else:
            ngoai.append((vi_tri, kd, vd))

    print("Khung bao của tỉnh [{}, {}, {}, {}]: trong {} , ngoài {} "
          "(bỏ khỏi tệp)".format(kb[0], kb[1], kb[2], kb[3],
                                 len(trong), len(ngoai)))
    for vi_tri, kd, vd in ngoai[:20]:
        print("    {:<40} {:.5f}, {:.5f}".format(
            str(ten_cua(cac_ban_ghi[vi_tri]))[:40], kd, vd))
    if len(ngoai) > 20:
        print("    ... và {} dòng nữa".format(len(ngoai) - 20))
    if ngoai:
        print("  Nhiều dòng ngoài khung thường nghĩa là nhận nhầm hệ tọa độ "
              "hoặc lộn X với Y.")

    if not trong:
        raise SystemExit("\nDỪNG: không dòng nào nằm trong khung bao của "
                         "tỉnh, KHÔNG ghi đè tệp cũ. Kiểm lại cột tọa độ.")

    return trong, {"thieu_toa_do": len(thieu), "ngoai_khung": len(ngoai)}


# ---------------------------------------------------------------------------
# Luu vuc va ghi tep
# ---------------------------------------------------------------------------

def gan_luu_vuc(tt, cac_doi_tuong):
    """Dien ma_luu_vuc, ten_luu_vuc cho cac Feature diem.

    Goi lai gan_luu_vuc() cua script 05 de moi lop dung chung mot quy tac
    (diem trong luu vuc nao lay luu vuc do, ngoai thi lay luu vuc gan nhat
    trong 10 km). Luon doc data/luu_vuc.geojson cua du an, ke ca khi ket qua
    duoc ghi ra thu muc khac.
    """
    duong_lv = mod_tinh.duong_dan_ra(tt, "luu_vuc.geojson")
    if not os.path.isfile(duong_lv):
        print("\nChưa có data/luu_vuc.geojson nên không gán được lưu vực. "
              "Chạy script 05 rồi chạy lại script này.")
        return

    # Nap script 05 cung la luc sua_duong_dan_proj() chay, truoc geopandas
    m05 = nap_script("05_chuan_hoa_chuyen_de")
    gpd = m05.gpd
    epsg = tt["epsg_chuyen_de"]

    luu_vuc = gpd.read_file(duong_lv)
    diem = gpd.GeoDataFrame(
        geometry=gpd.points_from_xy(
            [d["geometry"]["coordinates"][0] for d in cac_doi_tuong],
            [d["geometry"]["coordinates"][1] for d in cac_doi_tuong]),
        crs=4326).to_crs(epsg)
    ma, ten, thieu = m05.gan_luu_vuc(diem, luu_vuc, epsg)

    for d, m, t in zip(cac_doi_tuong, ma, ten):
        d["properties"]["ma_luu_vuc"] = m if isinstance(m, str) else None
        d["properties"]["ten_luu_vuc"] = t if isinstance(t, str) else None
    print("\nGán lưu vực: {} điểm, {} điểm không gán được".format(
        len(cac_doi_tuong), thieu))


def ghi_geojson(tt, ten_tep, ten_lop, cac_doi_tuong, them, thu_muc_ra=None):
    """Ghi FeatureCollection EPSG:4326. `them` la cac khoa cap tap doi tuong."""
    if not cac_doi_tuong:
        raise SystemExit("DỪNG: không còn đối tượng nào, KHÔNG ghi đè tệp cũ.")
    if thu_muc_ra:
        os.makedirs(thu_muc_ra, exist_ok=True)
        tep_ra = os.path.join(thu_muc_ra, ten_tep)
    else:
        tep_ra = mod_tinh.duong_dan_ra(tt, ten_tep)

    tap = {
        "type": "FeatureCollection",
        "name": ten_lop,
        "crs": {"type": "name",
                "properties": {"name": "urn:ogc:def:crs:OGC:1.3:CRS84"}},
    }
    tap.update(them)
    tap["thoi_diem_xuat"] = datetime.now(MUI_GIO_VN).isoformat(
        timespec="minutes")
    tap["features"] = cac_doi_tuong

    with io.open(tep_ra, "w", encoding="utf-8", newline="\n") as f:
        json.dump(tap, f, ensure_ascii=False, indent=1)
    print("\nĐã ghi: {} ({} đối tượng)".format(tep_ra, len(cac_doi_tuong)))
    return tep_ra


def diem(kinh_do, vi_do, thuoc_tinh):
    return {
        "type": "Feature",
        "geometry": {"type": "Point",
                     "coordinates": [round(kinh_do, 7), round(vi_do, 7)]},
        "properties": thuoc_tinh,
    }


def ngay_hom_nay():
    return datetime.now(MUI_GIO_VN).strftime("%d/%m/%Y")
