# -*- coding: utf-8 -*-
r"""
Nap danh muc ho, ao, dam cua ban ra soat kiem ke thanh lop Ao ho.

Dau vao : CSDL/dulieu_thuc/TH_Kiemke_*.xlsx, sheet "B3.2.Hồ"
          (Phu luc II: so luong nguon nuoc mat la cac ho, ao, dam, pha)
Dau ra  : data/ao_ho.geojson  (EPSG:4326)

SHEET NAY KHONG CO TOA DO TRONG BAN GOC. Nguoi dung tu bo sung cot toa do vao
Excel; chua co cot do thi script in bang anh xa cot, so dong doc duoc roi
DUNG, khong ghi de tep nao. Cach dat ten cot toa do: xem thong bao khi dung.

QUAN HE VOI SCRIPT 05, PHAI HIEU TRUOC KHI CHAY

Truoc day ao_ho.geojson la 51 ho do script 05 TACH tu bang cong trinh khai
thac, mang ca luu luong khai thac. Sheet nay la danh muc NGUON NUOC (hon 200
ho, ao, dam) va khong co luu luong. Hai thu khac nghia nhau, nen:

  - Tep do script nay ghi mang dau "sinh_boi" o cap FeatureCollection.
  - Script 05 thay dau do thi KHONG tach ho nua va KHONG ghi de ao_ho.geojson;
    cac ho khai thac quay ve khai_thac.geojson cung luu luong cua chung.
  - Vi vay SAU KHI CHAY SCRIPT NAY PHAI CHAY LAI SCRIPT 05. Quen thi luu luong
    cua cac ho bien mat khoi trang Thong ke ma khong co loi nao bao;
    backend/tests/test_lop_kiem_ke_xlsx.py chot dieu do.

Chay:  python scripts/12_nap_ao_ho_kiem_ke.py
       python scripts/12_nap_ao_ho_kiem_ke.py --tep <xlsx> --thu-muc-ra <thu muc>
"""

import json
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import tinh as mod_tinh
import kiem_ke_xlsx as kk

KHOA_SHEET = "b32ho"
TEN_TEP_RA = "ao_ho.geojson"
TIEN_TO_MA = "AH"
# Dau nhan biet tep do script nay sinh ra. Script 05 va bo kiem thu doc dau nay.
SINH_BOI = "12_nap_ao_ho_kiem_ke"

NGUON_DL = ("Bản rà soát kết quả kiểm kê nguồn nước mặt, Phụ lục II "
            "(hồ, ao, đầm, phá)")

# Khoa la ten truong dau ra, phai khop khai bao lop ao_ho trong
# assets/js/config.js. Gia tri la ten cot Excel da qua khoa_cot().
BANG_ANH_XA = {
    "stt": ["stt", "tt", "sott"],
    "ten_cong_trinh": ["tenhochua", "tenho", "tenhoaodam", "ten",
                       "tennguonnuoc"],
    "nguon_nuoc_khai_thac": ["nguonnuockhaithac", "nguonnuoc"],
    "luu_vuc_kiem_ke": ["thuochethongsong", "hethongsong", "thuocluuvucsong",
                        "luuvucsong"],
    "dien_tich_mat_nuoc_m2": ["dientichmatnuocm2", "dientichmatnuoc",
                              "dientichm2", "dientich"],
    "dung_tich_ho_trieu_m3": ["dungtichtoanbotrieum3", "dungtichtoanbo",
                              "dungtich"],
    "dung_tich_huu_ich_trieu_m3": ["dungtichhuuichtrieum3", "dungtichhuuich"],
    "vi_tri_hc": ["vitrihanhchinh", "vitri", "diadiem"],
    "muc_dich_su_dung": ["mucdichsudung", "mucdich", "chucnang"],
    "ghi_chu": ["ghichu"],
}

TRUONG_SO = {"dien_tich_mat_nuoc_m2": 1,
             "dung_tich_ho_trieu_m3": 6,
             "dung_tich_huu_ich_trieu_m3": 6}


# ---------------------------------------------------------------------------
# Ham thuan, co kiem thu trong backend/tests/test_lop_kiem_ke_xlsx.py
# ---------------------------------------------------------------------------

def suy_loai_hinh(ten):
    """Loai hinh theo TIEN TO cua ten, khong doan them.

    "Cum ao", "Cum ho" van la ao, ho. "Thuy dien X" la ho thuy dien (lop ao_ho
    to mau rieng cho loai nay). Ten khong co tien to quen thuoc thi tra ve
    None: de trong con hon gan nham.
    """
    k = kk.bo_dau(ten or "").strip()
    k = re.sub(r"^cum\s+", "", k)
    if k.startswith("thuy dien"):
        return "Hồ thủy điện"
    if k.startswith("ho "):
        return "Hồ"
    if k.startswith("ao "):
        return "Ao"
    if k.startswith("dam "):
        return "Đầm"
    return None


def tach_xa(vi_tri_hc):
    """'xã Tu Bông, tỉnh Khánh Hòa' -> 'Xã Tu Bông'."""
    s = kk.sach(vi_tri_hc)
    if not s:
        return None
    phan = s.split(",")[0].strip()
    if not phan:
        return None
    return phan[0].upper() + phan[1:]


def khoa_so_khop(ten, xa):
    """Khoa de noi mot ho voi cong trinh khai thac: ten + xa, da bo dau.

    Bo tien to hanh chinh (xa, phuong, thi tran) vi bang khai thac ghi
    'Tu Bông' con sheet nay ghi 'xã Tu Bông'.
    """
    t = re.sub(r"[^a-z0-9]", "", kk.bo_dau(ten or ""))
    x = kk.bo_dau(xa or "").strip()
    x = re.sub(r"^(xa|phuong|thi tran|tt\.?|p\.)\s+", "", x)
    x = re.sub(r"[^a-z0-9]", "", x)
    return (t, x)


def dung_thuoc_tinh(dong, anh_xa):
    """Mot dong Excel -> thuoc tinh dau ra (chua co ma, toa do, luu vuc)."""
    tt = {}
    for truong, chi_so in anh_xa.items():
        if truong == "stt":
            continue
        gia_tri = kk.o(dong, chi_so)
        if truong in TRUONG_SO:
            tt[truong] = kk.so_hoc(gia_tri, TRUONG_SO[truong])
        else:
            tt[truong] = kk.sach(gia_tri)
    tt["loai_hinh"] = suy_loai_hinh(tt.get("ten_cong_trinh"))
    tt["xa_phuong"] = tach_xa(tt.get("vi_tri_hc"))
    return tt


# ---------------------------------------------------------------------------
# Noi voi cong trinh khai thac
# ---------------------------------------------------------------------------

def doc_ho_khai_thac(tt):
    """{khoa_so_khop -> [ma KT]} cua cac cong trinh khai thac loai 'Ho'.

    Ho khai thac nam o khai_thac.geojson (sau khi script 05 thoi tach) hoac
    con o ao_ho.geojson kieu cu (truong ma_khai_thac). Doc ca hai noi.
    """
    bang = {}

    def them(ten, xa, ma):
        if ten and ma:
            bang.setdefault(khoa_so_khop(ten, xa), set()).add(ma)

    for ten_tep in ("khai_thac.geojson", "ao_ho.geojson"):
        duong = mod_tinh.duong_dan_ra(tt, ten_tep)
        if not os.path.isfile(duong):
            continue
        with open(duong, encoding="utf-8") as f:
            tap = json.load(f)
        if tap.get("sinh_boi") == SINH_BOI:
            continue          # tep do chinh script nay ghi, khong phai nguon
        for d in tap.get("features", []):
            p = d.get("properties") or {}
            if not str(p.get("loai_hinh") or "").startswith("Hồ"):
                continue
            ma = p.get("ma_khai_thac") or p.get("ma")
            them(p.get("ten_cong_trinh"), p.get("xa_phuong"), ma)
    return bang


def gan_ma_khai_thac(cac_doi_tuong, bang):
    """Gan ma_khai_thac khi khop DUNG MOT cong trinh. Tra ve so ho da noi."""
    so_noi = 0
    for d in cac_doi_tuong:
        p = d["properties"]
        ung_vien = bang.get(khoa_so_khop(p.get("ten_cong_trinh"),
                                         p.get("xa_phuong")), set())
        if len(ung_vien) == 1:
            p["ma_khai_thac"] = sorted(ung_vien)[0]
            so_noi += 1
        else:
            p["ma_khai_thac"] = None
    return so_noi


# ---------------------------------------------------------------------------
# Chuong trinh chinh
# ---------------------------------------------------------------------------

def main():
    tham_so = kk.doc_tham_so("Nap sheet B3.2.Ho thanh data/ao_ho.geojson")
    tt = mod_tinh.nap()

    tep = kk.tim_tep_xlsx(tt, tham_so.tep)
    print("Đọc: {}".format(tep))
    cac_dong = kk.doc_sheet(tep, KHOA_SHEET)

    i_td = kk.tim_dong_tieu_de(cac_dong)
    ten_cac_cot = cac_dong[i_td]
    anh_xa, cot_toa_do, cot_la = kk.dung_anh_xa(ten_cac_cot, BANG_ANH_XA)
    kk.in_anh_xa(ten_cac_cot, anh_xa, cot_toa_do, cot_la)

    for bat_buoc in ("stt", "ten_cong_trinh"):
        if bat_buoc not in anh_xa:
            raise SystemExit("DỪNG: không nhận ra cột '{}'. Thêm tên cột vào "
                             "BANG_ANH_XA rồi chạy lại.".format(bat_buoc))

    # Dong du lieu: o STT la so nguyen. Dong danh so "(1) (2) ..." va dong
    # trong tu loai.
    cac_ban_ghi = []
    for dong in cac_dong[i_td + 1:]:
        stt = kk.o(dong, anh_xa["stt"])
        if isinstance(stt, bool) or not isinstance(stt, (int, float)):
            continue
        if not kk.sach(kk.o(dong, anh_xa["ten_cong_trinh"])):
            continue
        cac_ban_ghi.append(dong)

    print("\nSố hồ, ao, đầm đọc được: {}".format(len(cac_ban_ghi)))
    if not cac_ban_ghi:
        raise SystemExit("DỪNG: không có dòng dữ liệu nào, KHÔNG ghi đè.")

    dem_loai = {}
    for dong in cac_ban_ghi:
        loai = suy_loai_hinh(kk.o(dong, anh_xa["ten_cong_trinh"])) or "(không rõ)"
        dem_loai[loai] = dem_loai.get(loai, 0) + 1
    print("Theo loại hình (suy từ tiền tố tên): {}".format(dem_loai))

    if not cot_toa_do or ("gop" not in cot_toa_do
                          and not ("kinh_do" in cot_toa_do
                                   and "vi_do" in cot_toa_do)):
        kk.bao_thieu_cot_toa_do("B3.2.Hồ", ten_cac_cot)

    def ten_cua(dong):
        return "STT {} {}".format(kk.o(dong, anh_xa["stt"]),
                                  kk.sach(kk.o(dong, anh_xa["ten_cong_trinh"])))

    trong_khung, thong_ke = kk.giai_toa_do(tt, cac_ban_ghi, cot_toa_do, ten_cua)

    nguon_dl = "{}, nạp ngày {}".format(NGUON_DL, kk.ngay_hom_nay())
    cac_doi_tuong = []
    for vi_tri, kd, vd in trong_khung:
        dong = cac_ban_ghi[vi_tri]
        thuoc_tinh = {"ma": "{}{:03d}".format(
            TIEN_TO_MA, int(kk.o(dong, anh_xa["stt"])))}
        thuoc_tinh.update(dung_thuoc_tinh(dong, anh_xa))
        thuoc_tinh["nguon_dl"] = nguon_dl
        cac_doi_tuong.append(kk.diem(kd, vd, thuoc_tinh))

    so_noi = gan_ma_khai_thac(cac_doi_tuong, doc_ho_khai_thac(tt))
    print("\nNối được với công trình khai thác (khớp tên + xã, đúng một): "
          "{} / {}".format(so_noi, len(cac_doi_tuong)))

    kk.gan_luu_vuc(tt, cac_doi_tuong)

    kk.ghi_geojson(tt, TEN_TEP_RA, "ao_ho", cac_doi_tuong,
                   {"sinh_boi": SINH_BOI, "nguon_dl": nguon_dl},
                   tham_so.thu_muc_ra)
    print("  Thiếu tọa độ    : {} (không đưa vào tệp)".format(
        thong_ke["thieu_toa_do"]))
    print("  Ngoài khung bao : {} (không đưa vào tệp)".format(
        thong_ke["ngoai_khung"]))
    print("\nVIỆC PHẢI LÀM TIẾP: chạy lại scripts/05_chuan_hoa_chuyen_de.py để "
          "các hồ khai thác\nquay về khai_thac.geojson cùng lưu lượng của "
          "chúng. Quên bước này thì trang Thống kê\nthiếu lưu lượng của các "
          "hồ chứa.")


if __name__ == "__main__":
    main()
