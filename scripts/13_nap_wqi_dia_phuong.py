# -*- coding: utf-8 -*-
r"""
Nap ket qua WQI cua mang quan trac dia phuong thanh lop diem.

Dau vao : CSDL/dulieu_thuc/TH_Kiemke_*.xlsx, sheet "Biểu 10"
          (Kiem ke chat luong nuoc mat theo chi so WQI)
Dau ra  : data/quan_trac_dia_phuong.geojson  (EPSG:4326)

SHEET NAY KHONG CO TOA DO TRONG BAN GOC. Nguoi dung tu bo sung cot toa do vao
Excel (ghi o DONG DAU cua moi vi tri); chua co thi script in bang anh xa cot,
so vi tri doc duoc roi DUNG, khong ghi tep nao.

CAU TRUC SHEET, KHONG DEU NHU TEN BIEU GOI Y

  - Ba phan, ngan bang dong tieu de chi co o dau: "NĂM 2025 - Bắc Khánh Hòa",
    "NĂM 2025 - Nam Khánh Hòa (Ninh Thuận cũ)", "MẪU BỔ SUNG THÁNG 7/2026".
    STT dem lai tu 1 o moi phan.
  - Moi vi tri la mot KHOI nhieu dong: thong tin vi tri chi nam o dong dau,
    cac dong sau chi co gia tri WQI va ky do. So ky KHONG co dinh: 12 thang,
    10 thang, 4 quy, hoac 1 lan (mau bo sung). Vi vay khong tao cot theo
    thang ma giu ca chuoi trong truong chuoi_wqi.
  - Phan mau bo sung con co dong tieu de nhom theo ten song.

Ma vi tri = QD<so thu tu phan>-<STT>, vi ten bi trung giua cac phan.

WQI lay NGUYEN tu Excel, khong tinh lai. Phan loai dung phan_loai_wqi() cua
backend/wqi.py (Quyet dinh 1460/QD-TCMT), khong dat nguong moi.

Lop nay KHONG tron vao data/quan_trac.geojson (tram QTQG) va khong lien quan
den HOP_TRAM_DIA_PHUONG cua backend.

Chay:  python scripts/13_nap_wqi_dia_phuong.py
       python scripts/13_nap_wqi_dia_phuong.py --tep <xlsx> --thu-muc-ra <thu muc>
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import tinh as mod_tinh
import kiem_ke_xlsx as kk

KHOA_SHEET = "bieu10"
TEN_TEP_RA = "quan_trac_dia_phuong.geojson"
TEN_LOP = "quan_trac_dia_phuong"

NGUON_DL = ("Bản rà soát kết quả kiểm kê nguồn nước mặt, Biểu 10 "
            "(chất lượng nước mặt theo WQI), mạng quan trắc địa phương")

# Khoa la ten truong dau ra, phai khop khai bao lop quan_trac_dia_phuong trong
# assets/js/config.js. Gia tri la ten cot Excel da qua khoa_cot().
BANG_ANH_XA = {
    "stt": ["stt", "tt"],
    "ten": ["nguonnuocsongsuoikenhhodam", "nguonnuoc", "vitriquantrac",
            "tendiem", "ten"],
    "xa_phuong": ["xa", "xaphuong", "xamoi"],
    "tinh": ["tinh", "tinhmoi"],
    "xa_cu": ["xacu"],
    "huyen_cu": ["huyencu"],
    "tinh_cu": ["tinhcu"],
    "luu_vuc_kiem_ke": ["thuocluuvucsong", "luuvucsong", "luuvuc"],
    "wqi": ["giatriwqi", "wqi"],
    "ky": ["thoigian", "kyquantrac", "thoigianquantrac"],
}


def phan_loai_wqi(gia_tri):
    """Goi phan_loai_wqi() cua backend de ca he thong dung mot bang nguong."""
    thu_muc_backend = os.path.join(mod_tinh.GOC, "backend")
    if thu_muc_backend not in sys.path:
        sys.path.insert(0, thu_muc_backend)
    import wqi as mod_wqi
    return mod_wqi.phan_loai_wqi(gia_tri)


# ---------------------------------------------------------------------------
# Ham thuan, co kiem thu trong backend/tests/test_lop_kiem_ke_xlsx.py
# ---------------------------------------------------------------------------

def gop_tieu_de(dong_tren, dong_duoi):
    """Gop tieu de hai tang thanh mot danh sach ten cot.

    O tang duoi co chu thi lay tang duoi ("Xã", "Tỉnh", "Xã (Cũ)" nam duoi o
    gop "Vị trí hành chính"), khong thi lay tang tren. Dong danh so cot
    (1, 2, 3...) khong phai tang duoi: do la so chu khong phai chu.
    """
    n = max(len(dong_tren), len(dong_duoi))
    ket_qua = []
    for i in range(n):
        tren = dong_tren[i] if i < len(dong_tren) else None
        duoi = dong_duoi[i] if i < len(dong_duoi) else None
        if isinstance(duoi, str) and duoi.strip():
            ket_qua.append(duoi)
        else:
            ket_qua.append(tren)
    return ket_qua


def tach_khoi(cac_dong, anh_xa):
    """Tach cac dong du lieu thanh danh sach vi tri.

    Moi vi tri: {"phan", "so_phan", "nhom", "dong_dau", "ky": [(ten ky, wqi)]}.
    dong_dau la dong Excel mang thong tin vi tri (va toa do).
    """
    i_ten = anh_xa["ten"]
    i_wqi = anh_xa["wqi"]
    i_ky = anh_xa["ky"]

    cac_vi_tri = []
    phan = None
    so_phan = 0
    nhom = None

    for dong in cac_dong:
        co_chu = [v for v in dong if kk.sach(v) is not None]
        if not co_chu:
            continue

        # Dong danh so cot (1, 2, 3 ... 6) nam ngay duoi tieu de: o "Thời gian"
        # cua no la SO chu khong phai chu. Khong loai thi no thanh mot vi tri
        # gia ten "2" voi WQI = 5.
        if isinstance(kk.o(dong, i_ky), (int, float)):
            continue

        ten = kk.sach(kk.o(dong, i_ten))
        ky = kk.sach(kk.o(dong, i_ky))
        wqi = kk.so_hoc(kk.o(dong, i_wqi))

        # Dong tieu de: chi co o dau tien. "NĂM ..." va "MẪU ..." mo mot phan
        # moi, con lai la tieu de nhom theo ten song ben trong phan.
        if len(co_chu) == 1 and kk.sach(dong[0]) is not None and ky is None:
            chu = kk.sach(dong[0])
            khoa = kk.bo_dau(chu)
            if khoa.startswith("nam ") or khoa.startswith("mau "):
                phan = chu
                so_phan += 1
                nhom = None
            else:
                nhom = chu
            continue

        # Dong khong co ky do thi khong phai so lieu (chu ky, ghi chu cuoi bieu)
        if ky is None:
            continue

        if ten is not None:
            cac_vi_tri.append({"phan": phan, "so_phan": max(so_phan, 1),
                               "nhom": nhom, "dong_dau": dong, "ky": []})
        if not cac_vi_tri:
            continue
        cac_vi_tri[-1]["ky"].append((ky, wqi))

    return cac_vi_tri


def tom_tat_chuoi(cac_ky):
    """Tu [(ten ky, wqi)] theo thu tu thoi gian -> cac truong tom tat.

    Ky moi nhat la ky CUOI CUNG co so (cac dong trong bieu xep theo thoi gian).
    """
    co_so = [(ky, w) for ky, w in cac_ky if w is not None]
    if not co_so:
        return {"wqi": None, "thoi_diem_wqi": None, "so_ky": 0,
                "wqi_thap_nhat": None, "ky_wqi_thap_nhat": None,
                "chuoi_wqi": None}

    def gon(w):
        return int(w) if float(w).is_integer() else w

    ky_cuoi, w_cuoi = co_so[-1]
    ky_min, w_min = min(co_so, key=lambda x: x[1])
    return {
        "wqi": gon(w_cuoi),
        "thoi_diem_wqi": ky_cuoi,
        "so_ky": len(co_so),
        "wqi_thap_nhat": gon(w_min),
        "ky_wqi_thap_nhat": ky_min,
        "chuoi_wqi": "; ".join("{}: {}".format(ky, gon(w)) for ky, w in co_so),
    }


def ma_vi_tri(so_phan, stt, so_thu_tu):
    """QD<phan>-<STT>. STT khong doc duoc thi dung so thu tu trong phan."""
    try:
        so = int(stt)
    except (TypeError, ValueError):
        so = so_thu_tu
    return "QD{}-{:02d}".format(so_phan, so)


def dung_thuoc_tinh(vi_tri, anh_xa):
    """Mot vi tri -> thuoc tinh dau ra (chua co ma, toa do, luu vuc)."""
    dong = vi_tri["dong_dau"]
    tt = {}
    for truong in ("ten", "xa_phuong", "xa_cu", "huyen_cu", "tinh_cu",
                   "luu_vuc_kiem_ke"):
        tt[truong] = kk.sach(kk.o(dong, anh_xa.get(truong)))
    # Phan mau bo sung co dong de trong cot luu vuc: lay ten nhom thay the
    if tt["luu_vuc_kiem_ke"] is None:
        tt["luu_vuc_kiem_ke"] = vi_tri["nhom"]
    tt["dot_quan_trac"] = vi_tri["phan"]
    tt.update(tom_tat_chuoi(vi_tri["ky"]))
    return tt


# ---------------------------------------------------------------------------
# Chuong trinh chinh
# ---------------------------------------------------------------------------

def main():
    tham_so = kk.doc_tham_so(
        "Nap sheet Bieu 10 thanh data/quan_trac_dia_phuong.geojson")
    tt = mod_tinh.nap()

    tep = kk.tim_tep_xlsx(tt, tham_so.tep)
    print("Đọc: {}".format(tep))
    cac_dong = kk.doc_sheet(tep, KHOA_SHEET)

    i_td = kk.tim_dong_tieu_de(cac_dong)
    ten_cac_cot = gop_tieu_de(cac_dong[i_td], cac_dong[i_td + 1])
    anh_xa, cot_toa_do, cot_la = kk.dung_anh_xa(ten_cac_cot, BANG_ANH_XA)
    kk.in_anh_xa(ten_cac_cot, anh_xa, cot_toa_do, cot_la)

    for bat_buoc in ("ten", "wqi", "ky"):
        if bat_buoc not in anh_xa:
            raise SystemExit("DỪNG: không nhận ra cột '{}'. Thêm tên cột vào "
                             "BANG_ANH_XA rồi chạy lại.".format(bat_buoc))

    cac_vi_tri = tach_khoi(cac_dong[i_td + 2:], anh_xa)
    print("\nSố vị trí quan trắc đọc được: {}".format(len(cac_vi_tri)))
    if not cac_vi_tri:
        raise SystemExit("DỪNG: không có vị trí nào, KHÔNG ghi đè.")

    theo_phan = {}
    theo_so_ky = {}
    for vt in cac_vi_tri:
        theo_phan[vt["phan"]] = theo_phan.get(vt["phan"], 0) + 1
        n = len([1 for _, w in vt["ky"] if w is not None])
        theo_so_ky[n] = theo_so_ky.get(n, 0) + 1
    for phan, n in theo_phan.items():
        print("  {:<46} {} vị trí".format(str(phan)[:46], n))
    print("Số vị trí theo số kỳ có WQI: {}".format(
        dict(sorted(theo_so_ky.items()))))

    if not cot_toa_do or ("gop" not in cot_toa_do
                          and not ("kinh_do" in cot_toa_do
                                   and "vi_do" in cot_toa_do)):
        kk.bao_thieu_cot_toa_do("Biểu 10", ten_cac_cot)

    def ten_cua(dong):
        return kk.sach(kk.o(dong, anh_xa["ten"]))

    cac_dong_dau = [vt["dong_dau"] for vt in cac_vi_tri]
    trong_khung, thong_ke = kk.giai_toa_do(tt, cac_dong_dau, cot_toa_do,
                                           ten_cua)

    nguon_dl = "{}, nạp ngày {}".format(NGUON_DL, kk.ngay_hom_nay())
    dem_trong_phan = {}
    thu_tu = {}
    for i, vt in enumerate(cac_vi_tri):
        dem_trong_phan[vt["so_phan"]] = dem_trong_phan.get(vt["so_phan"], 0) + 1
        thu_tu[i] = dem_trong_phan[vt["so_phan"]]

    cac_doi_tuong = []
    da_dung = set()
    for vi_tri, kd, vd in trong_khung:
        vt = cac_vi_tri[vi_tri]
        ma = ma_vi_tri(vt["so_phan"], kk.o(vt["dong_dau"], anh_xa.get("stt")),
                       thu_tu[vi_tri])
        if ma in da_dung:
            raise SystemExit("DỪNG: mã {} bị trùng (STT lặp trong cùng một "
                             "phần của biểu). Sửa STT trong Excel rồi chạy "
                             "lại.".format(ma))
        da_dung.add(ma)

        thuoc_tinh = {"ma": ma}
        thuoc_tinh.update(dung_thuoc_tinh(vt, anh_xa))
        thuoc_tinh["phan_loai_wqi"] = phan_loai_wqi(thuoc_tinh["wqi"])
        thuoc_tinh["nguon_dl"] = nguon_dl
        cac_doi_tuong.append(kk.diem(kd, vd, thuoc_tinh))

    kk.gan_luu_vuc(tt, cac_doi_tuong)

    kk.ghi_geojson(tt, TEN_TEP_RA, TEN_LOP, cac_doi_tuong,
                   {"sinh_boi": "13_nap_wqi_dia_phuong", "nguon_dl": nguon_dl},
                   tham_so.thu_muc_ra)
    print("  Thiếu tọa độ    : {} (không đưa vào tệp)".format(
        thong_ke["thieu_toa_do"]))
    print("  Ngoài khung bao : {} (không đưa vào tệp)".format(
        thong_ke["ngoai_khung"]))
    print("\nNhớ thêm \"{}\" vào lop_co_san trong tinh.json. Có tệp mà không "
          "đăng ký thì lớp\nkhông bao giờ được nạp.".format(TEN_LOP))


if __name__ == "__main__":
    main()
