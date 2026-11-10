"""Tinh va phan loai chi so chat luong nuoc Viet Nam (VN_WQI).

Can cu: Quyet dinh 1460/QD-TCMT ngay 12/11/2019 cua Tong cuc Moi truong,
"Huong dan ky thuat tinh toan va cong bo chi so chat luong nuoc cua Viet Nam".
Ban goc dung de doi chieu: CSDL/WQI_1460_QD-TCMT_428277.doc

Nguong phan loai GIONG scripts/03_lay_realtime.py, neu khong thi cung mot gia
tri WQI se bi hai duong du lieu cua he thong xep hai loai khac nhau.

Nam nhom thong so theo muc 2.1.b cua quyet dinh:
    Nhom I    pH
    Nhom II   thuoc bao ve thuc vat (Aldrin, BHC, Dieldrin, DDTs, Heptachlor)
    Nhom III  kim loai nang (As, Cd, Pb, Cr6+, Cu, Zn, Hg)
    Nhom IV   huu co va dinh duong (DO, BOD5, COD, TOC, N-NH4, N-NO3, N-NO2,
              P-PO4)
    Nhom V    vi sinh (Coliform, E.coli)
"""

# ---------------------------------------------------------------------------
# Nguong phan loai
# ---------------------------------------------------------------------------

# Giong scripts/03_lay_realtime.py dong 47-48
NGUONG_CANH_BAO = 26      # duoi muc nay la "Xau" tro xuong
NGUONG_THEO_DOI = 51      # duoi muc nay la "Trung binh" tro xuong

# Thang diem q dung chung cho Bang 1 va Bang 2
THANG_Q = [100, 75, 50, 25, 10]


def phan_loai_wqi(wqi):
    """Phan loai theo bang o muc 1.4 cua Quyet dinh 1460.

    Luu y: Bang 7 o muc 3 cua chinh quyet dinh dat ten khac cho ba muc duoi
    (26-50 goi la "Kem", 10-25 goi la "O nhiem nang"). Du an dung ten o muc
    1.4, vi do la bang gan voi ma mau hien thi va cung la ten ma
    scripts/03_lay_realtime.py da dung tu truoc.
    """
    if wqi is None:
        return None
    if wqi >= 91:
        return "Rất tốt"
    if wqi >= 76:
        return "Tốt"
    if wqi >= 51:
        return "Trung bình"
    if wqi >= 26:
        return "Xấu"
    if wqi >= 10:
        return "Kém"
    return "Ô nhiễm rất nặng"


def trang_thai_theo_wqi(wqi):
    """Trang thai giao dien: binh_thuong, theo_doi hay canh_bao.

    Ba gia tri nay khop CAU_HINH.nhan_trang_thai trong assets/js/config.js va
    cac lop CSS .tt-binh-thuong, .tt-theo-doi, .tt-canh-bao trong style.css.
    """
    if wqi is None:
        return None
    if wqi < NGUONG_CANH_BAO:
        return "canh_bao"
    if wqi < NGUONG_THEO_DOI:
        return "theo_doi"
    return "binh_thuong"


def hop_le(wqi):
    """WQI chi co nghia trong khoang 0 den 100."""
    if wqi is None:
        return False
    try:
        so = float(wqi)
    except (TypeError, ValueError):
        return False
    return 0 <= so <= 100


# ---------------------------------------------------------------------------
# Bang 1: nhom IV va nhom V
# ---------------------------------------------------------------------------
# Moi muc la danh sach nam gia tri BPi ung voi qi = 100, 75, 50, 25, 10.
#
# Hai co danh dau dau so sanh cua quyet dinh, va ca hai deu doi ket qua:
#   duoi_nghiem  muc 1 viet dau "<" chu khong phai "<=". Cp bang dung BP1 thi
#                roi vao muc 2, khong duoc 100 diem. Vi du N-NH4 ghi "<0,3".
#   tren_nghiem  muc 5 viet dau ">" chu khong phai ">=". Cp bang dung BP5 thi
#                van thuoc doan noi suy cua muc 4, khong tut xuong 10 diem.
#                Vi du Coliform ghi ">10.000": dung 10.000 duoc 25 diem.

BANG_NHOM_IV = {
    "bod5_mg_l":     {"moc": [4, 6, 15, 25, 50],
                      "duoi_nghiem": False, "tren_nghiem": False},
    "cod_mg_l":      {"moc": [10, 15, 30, 50, 150],
                      "duoi_nghiem": False, "tren_nghiem": False},
    "toc_mg_l":      {"moc": [4, 6, 15, 25, 50],
                      "duoi_nghiem": False, "tren_nghiem": False},
    "amoni_mg_l":    {"moc": [0.3, 0.3, 0.6, 0.9, 5],
                      "duoi_nghiem": True, "tren_nghiem": False},
    "nitrat_mg_l":   {"moc": [2, 5, 10, 15, 15],
                      "duoi_nghiem": False, "tren_nghiem": True},
    "photphat_mg_l": {"moc": [0.1, 0.2, 0.3, 0.5, 4],
                      "duoi_nghiem": False, "tren_nghiem": False},
}

# N-NO2 trong Bang 1 chi co hai muc: <= 0,05 duoc 100 diem, > 0,05 duoc 10.
# Ba muc giua bo trong nen khong noi suy duoc, phai xu ly nhu bac thang.
BAC_THANG_NHOM_IV = {
    "nitrit_mg_l": 0.05,
}

BANG_NHOM_V = {
    "coliform_mpn_100ml": {"moc": [2500, 5000, 7500, 10000, 10000],
                           "duoi_nghiem": False, "tren_nghiem": True},
    "ecoli_mpn_100ml":    {"moc": [20, 50, 100, 200, 200],
                           "duoi_nghiem": False, "tren_nghiem": True},
}

# ---------------------------------------------------------------------------
# Bang 2: nhom III, kim loai nang, don vi mg/L
# ---------------------------------------------------------------------------

BANG_NHOM_III = {
    "as_mg_l":  {"moc": [0.01, 0.02, 0.05, 0.1, 0.1],
                 "duoi_nghiem": False, "tren_nghiem": True},
    "cd_mg_l":  {"moc": [0.005, 0.005, 0.008, 0.01, 0.1],
                 "duoi_nghiem": True, "tren_nghiem": False},
    "pb_mg_l":  {"moc": [0.02, 0.02, 0.04, 0.05, 0.5],
                 "duoi_nghiem": True, "tren_nghiem": False},
    "cr6_mg_l": {"moc": [0.01, 0.02, 0.04, 0.05, 0.1],
                 "duoi_nghiem": False, "tren_nghiem": False},
    "cu_mg_l":  {"moc": [0.1, 0.2, 0.5, 1.0, 2],
                 "duoi_nghiem": False, "tren_nghiem": False},
    "zn_mg_l":  {"moc": [0.5, 1.0, 1.5, 2.0, 3],
                 "duoi_nghiem": False, "tren_nghiem": False},
    "hg_mg_l":  {"moc": [0.001, 0.001, 0.0015, 0.002, 0.01],
                 "duoi_nghiem": True, "tren_nghiem": False},
}

# ---------------------------------------------------------------------------
# Nhom II: thuoc bao ve thuc vat. Chi hai muc, don vi microgam/L.
# ---------------------------------------------------------------------------

BAC_THANG_NHOM_II = {
    "aldrin_ug_l":     0.1,
    "bhc_ug_l":        0.02,
    "dieldrin_ug_l":   0.1,
    "ddts_ug_l":       1.0,
    "heptachlor_ug_l": 0.2,
}

# ---------------------------------------------------------------------------
# Bang 3 (DO % bao hoa) va Bang 4 (pH)
# ---------------------------------------------------------------------------

BANG_DO_BAO_HOA = {
    "moc": [20, 50, 75, 88, 112, 125, 150, 200],
    "q":   [25, 50, 75, 100, 100, 75, 50, 25],
}

BANG_PH = {
    "moc": [5.5, 6, 8.5, 9],
    "q":   [50, 100, 100, 50],
}

# Ten truong cua tung nhom, dung de dem so nhom co du lieu
THONG_SO_NHOM_IV = (["do_mg_l"] + list(BANG_NHOM_IV.keys())
                    + list(BAC_THANG_NHOM_IV.keys()))
THONG_SO_NHOM_V = list(BANG_NHOM_V.keys())
THONG_SO_NHOM_III = list(BANG_NHOM_III.keys())
THONG_SO_NHOM_II = list(BAC_THANG_NHOM_II.keys())

SO_NHOM_TOI_THIEU = 3      # muc 2.1.b: toi thieu 03 trong 05 nhom
SO_THONG_SO_NHOM_IV_TOI_THIEU = 3


# ---------------------------------------------------------------------------
# Hai cong thuc noi suy
# ---------------------------------------------------------------------------

def cong_thuc_1(cp, bp_i, bp_i1, q_i, q_i1):
    """Cong thuc 1 trong quyet dinh, dung cho doan chat luong GIAM dan.

        WQI_SI = (q_i - q_i+1) / (BP_i+1 - BP_i) * (BP_i+1 - Cp) + q_i+1
    """
    if bp_i1 == bp_i:
        return float(q_i)
    return (q_i - q_i1) / (bp_i1 - bp_i) * (bp_i1 - cp) + q_i1


def cong_thuc_2(cp, bp_i, bp_i1, q_i, q_i1):
    """Cong thuc 2 trong quyet dinh, dung cho doan chat luong TANG dan.

        WQI_SI = (q_i+1 - q_i) / (BP_i+1 - BP_i) * (Cp - BP_i) + q_i
    """
    if bp_i1 == bp_i:
        return float(q_i)
    return (q_i1 - q_i) / (bp_i1 - bp_i) * (cp - bp_i) + q_i


def wqi_theo_bang(cp, khai_bao):
    """WQI thong so cho mot muc trong Bang 1 hoac Bang 2.

    Cac thong so nay deu la "cang cao cang xau" nen dung cong thuc 1.
    """
    moc = khai_bao["moc"]

    # Duoi muc 1 thi dat diem toi da
    if khai_bao.get("duoi_nghiem"):
        if cp < moc[0]:
            return 100.0
    elif cp <= moc[0]:
        return 100.0

    # Vuot muc 5 thi diem thap nhat
    if khai_bao.get("tren_nghiem"):
        if cp > moc[-1]:
            return 10.0
    elif cp >= moc[-1]:
        return 10.0

    for i in range(len(moc) - 1):
        bp_i, bp_i1 = moc[i], moc[i + 1]
        if bp_i1 <= bp_i:
            continue           # cap moc trung nhau, khong co doan de noi suy
        if bp_i <= cp <= bp_i1:
            return cong_thuc_1(cp, bp_i, bp_i1, THANG_Q[i], THANG_Q[i + 1])

    return 10.0


def wqi_bac_thang(cp, nguong):
    """Thong so chi co hai muc: khong vuot nguong duoc 100, vuot thi 10."""
    return 100.0 if cp <= nguong else 10.0


# ---------------------------------------------------------------------------
# pH va DO
# ---------------------------------------------------------------------------

def wqi_ph(ph):
    """WQI cua thong so pH, theo Bang 4 va cac dieu kien kem theo."""
    if ph is None:
        return None
    if ph < 5.5 or ph > 9:
        return 10.0
    if 6 <= ph <= 8.5:
        return 100.0
    if 5.5 <= ph < 6:
        # Chat luong tang dan: cong thuc 2
        return cong_thuc_2(ph, 5.5, 6, 50, 100)
    # 8,5 < pH <= 9, chat luong giam dan: cong thuc 1
    return cong_thuc_1(ph, 8.5, 9, 100, 50)


def do_bao_hoa(nhiet_do_c):
    """Nong do oxy hoa tan bao hoa theo nhiet do nuoc, muc 2.2.a.

        DO_baohoa = 14,652 - 0,41022*T + 0,0079910*T^2 - 0,000077774*T^3
    """
    if nhiet_do_c is None:
        return None
    t = float(nhiet_do_c)
    return (14.652 - 0.41022 * t + 0.0079910 * t ** 2
            - 0.000077774 * t ** 3)


def phan_tram_bao_hoa(do_mg_l, nhiet_do_c):
    """DO phan tram bao hoa. Can CA hai so do, thieu mot la khong tinh duoc."""
    if do_mg_l is None:
        return None
    bh = do_bao_hoa(nhiet_do_c)
    if not bh:
        return None
    return float(do_mg_l) / bh * 100.0


def wqi_do(do_mg_l, nhiet_do_c):
    """WQI cua thong so DO, tinh qua phan tram bao hoa theo Bang 3."""
    pt = phan_tram_bao_hoa(do_mg_l, nhiet_do_c)
    if pt is None:
        return None

    if pt < 20 or pt > 200:
        return 10.0
    if 88 <= pt <= 112:
        return 100.0

    moc = BANG_DO_BAO_HOA["moc"]
    q = BANG_DO_BAO_HOA["q"]

    if pt < 88:
        # Doan chat luong tang dan: cong thuc 2
        for i in range(len(moc) - 1):
            if moc[i] <= pt <= moc[i + 1] and moc[i + 1] <= 88:
                return cong_thuc_2(pt, moc[i], moc[i + 1], q[i], q[i + 1])
        return 10.0

    # 112 < pt < 200, doan chat luong giam dan: cong thuc 1
    for i in range(len(moc) - 1):
        if moc[i] <= pt <= moc[i + 1] and moc[i] >= 112:
            return cong_thuc_1(pt, moc[i], moc[i + 1], q[i], q[i + 1])
    return 10.0


# ---------------------------------------------------------------------------
# WQI cua tung thong so trong mot ban ghi
# ---------------------------------------------------------------------------

def wqi_tung_thong_so(ban_ghi):
    """Tra ve dict ten_thong_so -> WQI_SI cho moi thong so co trong ban ghi."""
    ket_qua = {}

    gia_tri_ph = ban_ghi.get("ph")
    if gia_tri_ph is not None:
        ket_qua["ph"] = wqi_ph(float(gia_tri_ph))

    diem_do = wqi_do(ban_ghi.get("do_mg_l"), ban_ghi.get("nhiet_do_c"))
    if diem_do is not None:
        ket_qua["do_mg_l"] = diem_do

    for cac_bang in (BANG_NHOM_IV, BANG_NHOM_V, BANG_NHOM_III):
        for ten, khai_bao in cac_bang.items():
            gt = ban_ghi.get(ten)
            if gt is not None:
                ket_qua[ten] = wqi_theo_bang(float(gt), khai_bao)

    for cac_bac in (BAC_THANG_NHOM_IV, BAC_THANG_NHOM_II):
        for ten, nguong in cac_bac.items():
            gt = ban_ghi.get(ten)
            if gt is not None:
                ket_qua[ten] = wqi_bac_thang(float(gt), nguong)

    return ket_qua


# ---------------------------------------------------------------------------
# Dieu kien du lieu toi thieu, muc 2.1.b
# ---------------------------------------------------------------------------

def _nhan(cac_diem, cac_ten):
    return [cac_diem[t] for t in cac_ten if t in cac_diem]


def kiem_tra_du_dieu_kien(cac_diem):
    """Tra ve (du_dieu_kien, ly_do).

    Quyet dinh yeu cau: toi thieu 03 trong 05 nhom, BAT BUOC co nhom IV, va
    trong nhom IV phai co toi thieu 03 thong so.
    """
    nhom_iv = _nhan(cac_diem, THONG_SO_NHOM_IV)
    if not nhom_iv:
        return False, "thiếu hoàn toàn nhóm IV (hữu cơ và dinh dưỡng)"
    if len(nhom_iv) < SO_THONG_SO_NHOM_IV_TOI_THIEU:
        return False, ("nhóm IV chỉ có {} thông số, cần tối thiểu {}"
                       .format(len(nhom_iv), SO_THONG_SO_NHOM_IV_TOI_THIEU))

    so_nhom = sum([
        1 if "ph" in cac_diem else 0,
        1 if _nhan(cac_diem, THONG_SO_NHOM_II) else 0,
        1 if _nhan(cac_diem, THONG_SO_NHOM_III) else 0,
        1,                                      # nhom IV, da kiem tra o tren
        1 if _nhan(cac_diem, THONG_SO_NHOM_V) else 0,
    ])
    if so_nhom < SO_NHOM_TOI_THIEU:
        return False, ("chỉ có {} trên 5 nhóm thông số, cần tối thiểu {}"
                       .format(so_nhom, SO_NHOM_TOI_THIEU))

    return True, None


def thong_so_con_thieu(ban_ghi):
    """Danh sach thong so can bo sung de tinh duoc WQI.

    Chi liet ke nhung thong so thuc su co trong bang cua quyet dinh, de nguoi
    dung biet phai xin nguon bo sung cai gi.
    """
    cac_diem = wqi_tung_thong_so(ban_ghi)
    du, _ = kiem_tra_du_dieu_kien(cac_diem)
    if du:
        return []

    thieu = []
    nhom_iv = _nhan(cac_diem, THONG_SO_NHOM_IV)
    if len(nhom_iv) < SO_THONG_SO_NHOM_IV_TOI_THIEU:
        for ten in THONG_SO_NHOM_IV:
            if ten not in cac_diem:
                thieu.append(ten)
    if "ph" not in cac_diem:
        thieu.append("ph")
    if not _nhan(cac_diem, THONG_SO_NHOM_V):
        thieu.extend(THONG_SO_NHOM_V)
    return thieu


# ---------------------------------------------------------------------------
# Tong hop WQI cuoi cung
# ---------------------------------------------------------------------------

def _trung_binh_nhan(cac_gia_tri):
    """Trung binh nhan, tuc (tich)^(1/so_phan_tu)."""
    tich = 1.0
    for v in cac_gia_tri:
        tich *= v
    return tich ** (1.0 / len(cac_gia_tri))


def tinh_wqi_tu_thong_so(ban_ghi, co_trong_so=False):
    """Tinh VN_WQI cuoi cung tu cac thong so tho trong mot ban ghi.

    co_trong_so = True thi dung cong thuc 5, danh cho thuy vuc can chu y o
    nhiem huu co: nhom IV trong so 2, nhom V trong so 1 (Bang 5).

    Tra ve dict:
        {"wqi": so nguyen hoac None,
         "chi_tiet": {ten_thong_so: WQI_SI},
         "cong_thuc": "3" | "4" | "5" | None,
         "ly_do": chuoi khi khong tinh duoc}

    Nhom nao khong co so lieu thi thua so cua no duoc BO HAN khoi tich, chu
    khong phai coi la 100. Dua them mot thua so "khong co du lieu" vao tich se
    keo ket qua xuong sai.
    """
    cac_diem = wqi_tung_thong_so(ban_ghi)

    du, ly_do = kiem_tra_du_dieu_kien(cac_diem)
    if not du:
        return {"wqi": None, "chi_tiet": cac_diem, "cong_thuc": None,
                "ly_do": ly_do}

    diem_i = cac_diem.get("ph")
    diem_ii = _nhan(cac_diem, THONG_SO_NHOM_II)
    diem_iii = _nhan(cac_diem, THONG_SO_NHOM_III)
    diem_iv = _nhan(cac_diem, THONG_SO_NHOM_IV)
    diem_v = _nhan(cac_diem, THONG_SO_NHOM_V)

    ket_qua = 1.0
    if diem_i is not None:
        ket_qua *= diem_i / 100.0
    if diem_ii:
        ket_qua *= _trung_binh_nhan(diem_ii) / 100.0
    if diem_iii:
        ket_qua *= _trung_binh_nhan(diem_iii) / 100.0

    tb_iv = sum(diem_iv) / len(diem_iv)

    if not diem_v:
        # Cong thuc 4: khong co nhom V
        ket_qua *= tb_iv
        ten_cong_thuc = "4"
    else:
        tb_v = sum(diem_v) / len(diem_v)
        if co_trong_so:
            # Cong thuc 5: nhom IV trong so 2, nhom V trong so 1
            ket_qua *= (tb_iv ** 2 * tb_v) ** (1.0 / 3.0)
            ten_cong_thuc = "5"
        else:
            # Cong thuc 3
            ket_qua *= (tb_iv * tb_v) ** 0.5
            ten_cong_thuc = "3"

    # Muc 2.2.b: gia tri WQI sau khi tinh toan duoc lam tron thanh so nguyen
    wqi_cuoi = int(round(min(100.0, max(0.0, ket_qua))))

    return {"wqi": wqi_cuoi, "chi_tiet": cac_diem,
            "cong_thuc": ten_cong_thuc, "ly_do": None}


# ---------------------------------------------------------------------------
# Gan vao ban ghi so do
# ---------------------------------------------------------------------------

def la_ban_ghi_chat_luong(ban_ghi):
    """Ban ghi nay co phai ket qua do chat luong nuoc hay khong.

    Can cu vao thong so co that trong ban ghi chu khong vao loai tram: mot tram
    thuy van van co the kem vai thong so chat luong nuoc, va nguoc lai mot diem
    chat luong nuoc chua co ket qua thi khong nen bi hoi la thieu WQI.
    """
    if ban_ghi.get("wqi") is not None:
        return True
    return bool(wqi_tung_thong_so(ban_ghi))


def gan_wqi(ban_ghi):
    """Dien wqi, phan_loai_wqi va trang_thai vao mot ban ghi so do.

    Thu tu uu tien:
      1. QTQG co san cot WQI hop le  -> dung so cua QTQG, khong tinh lai.
         Co quan chu quan la noi cong bo so chinh thuc; tinh lai roi ra so khac
         se gay mau thuan giua hai he thong.
      2. Du dieu kien theo muc 2.1.b -> tu tinh theo Quyet dinh 1460.
      3. Khong du                    -> de KHUYET han, kem ly do va danh sach
         thong so con thieu. Khong bao gio doan mot con so.
    """
    # Quyet dinh 1460/QD-TCMT la chi so chat luong NUOC MAT luc dia. Ap no
    # cho nuoc duoi dat la sai can ban: nuoc duoi dat khong co BOD5, DO hay
    # do duc theo nghia cua quy chuan nuoc mat, va nguong cac thong so do theo
    # QCVN 09-MT:2015/BTNMT, khong theo QCVN 08. Ban ghi lo khoan co pH va
    # amoni nen neu khong chan o day thi ham duoi se tinh ra mot con so WQI
    # trong hinh thuc ma vo nghia ve chuyen mon.
    if ban_ghi.get("loai") == "nuoc_duoi_dat":
        return ban_ghi

    gia_tri = ban_ghi.get("wqi")

    if hop_le(gia_tri):
        so = float(gia_tri)
        ban_ghi["wqi"] = so
        ban_ghi["phan_loai_wqi"] = phan_loai_wqi(so)
        if not ban_ghi.get("trang_thai"):
            ban_ghi["trang_thai"] = trang_thai_theo_wqi(so)
        return ban_ghi

    ban_ghi.pop("wqi", None)
    ban_ghi.pop("phan_loai_wqi", None)

    if not la_ban_ghi_chat_luong(ban_ghi):
        return ban_ghi            # tram thuy van, khong lien quan den WQI

    ket_qua = tinh_wqi_tu_thong_so(ban_ghi)

    if ket_qua["wqi"] is None:
        ban_ghi["wqi_ly_do"] = ket_qua["ly_do"]
        thieu = thong_so_con_thieu(ban_ghi)
        if thieu:
            ban_ghi["wqi_thieu_thong_so"] = thieu
        return ban_ghi

    ban_ghi["wqi"] = ket_qua["wqi"]
    ban_ghi["phan_loai_wqi"] = phan_loai_wqi(ket_qua["wqi"])
    ban_ghi["wqi_tu_tinh"] = True
    if not ban_ghi.get("trang_thai"):
        ban_ghi["trang_thai"] = trang_thai_theo_wqi(ket_qua["wqi"])
    return ban_ghi
