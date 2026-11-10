"""Gop so do thanh goi du lieu dung schema cua data/realtime.json.

Day la quyet dinh kien truc quan trong nhat cua tab Quan trac: backend tra ve
DUNG cau truc ma trang web da doc tu truoc. Nho vay lay_realtime(),
kieu_ve(p, rt), CAU_HINH.truong_realtime, cap_nhat_thoi_diem() va the_so()
dung lai nguyen ven, khong phai viet lai phan hien thi so do.

Cau truc:
    {
      "thoi_diem":   chuoi ISO hoac ten ky quan trac,
      "che_do":      "that" | "thu_nghiem",
      "nguon_dl":    cau mo ta nguon, hien o tooltip chan trang,
      "so_doi_tuong": so tram co so do,
      "doi_tuong":   { ma_tram: { loai, ten, trang_thai, ...so do... } },
      "canh_bao":    [ { ma, ten, loai, muc, noi_dung } ],
      "so_do_cu":    { nguong_ngay, so_ban_ghi,
                       cong_trinh[ {ma, ten, thoi_diem, thong_so[]} ] }
    }

Khoa "so_do_cu" la phan BO SUNG so voi data/realtime.json, bao cac cong trinh
da bi an so do vi qua cu. Trang web cu khong doc khoa nay nen them vao khong
pha hop dong gi; tab Quan trac doc de noi ro voi nguoi dung.
"""

from datetime import datetime, timezone, timedelta

import cau_hinh

MUI_GIO_VN = timezone(timedelta(hours=7))

# Truong khong phai so do, khong dua vao ban ghi doi_tuong
TRUONG_BO_QUA = {"kinh_do", "vi_do", "loai_tram", "song_ho", "thong_so",
                 "ten_luu_vuc", "don_vi_quan_ly", "nguon_dl"}


def _noi_dung_canh_bao(ban_ghi):
    """Cau mo ta ngan gon ly do canh bao, hien trong hop thoai Canh bao."""
    if ban_ghi.get("wqi") is not None:
        return "WQI = {} ({})".format(ban_ghi["wqi"],
                                      ban_ghi.get("phan_loai_wqi") or "")
    if ban_ghi.get("h_m") is not None:
        return "Mực nước {} m".format(ban_ghi["h_m"])
    if ban_ghi.get("q_m3s") is not None:
        return "Lưu lượng {} m³/s".format(ban_ghi["q_m3s"])
    return "Trạng thái cần theo dõi"


def dung_canh_bao(cac_ban_ghi):
    """Danh sach canh bao, sap muc canh_bao len truoc roi theo ten.

    Giong thu tu cua dung_canh_bao trong scripts/03_lay_realtime.py de hai
    nguon hien ra giao dien giong nhau.
    """
    danh_sach = []
    for bg in cac_ban_ghi:
        trang_thai = bg.get("trang_thai")
        if trang_thai not in ("canh_bao", "theo_doi"):
            continue
        danh_sach.append({
            "ma": bg.get("ma"),
            "ten": bg.get("ten"),
            "loai": bg.get("loai"),
            "muc": trang_thai,
            "noi_dung": _noi_dung_canh_bao(bg),
        })
    danh_sach.sort(key=lambda c: (c["muc"] != "canh_bao", c["ten"] or ""))
    return danh_sach


def doc_moc_thoi_gian(chuoi):
    """Doi chuoi thoi diem cua nguon thanh datetime co mui gio, hoac None.

    Nguon ghi khong thong nhat, da gap ba dang:
        "2026-10-06 07:00"        muc nuoc, theo gio
        "2026-05-03"              ngay lay mau phan tich, khong co gio
        "2026-10-27T09:31+07:00"  ISO day du, do che do thu_nghiem sinh ra
    Chuoi khong doc duoc thi tra None, va ben goi phai coi nhu KHONG BIET tuoi
    cua ban ghi chu khong coi la cu: doan sai thi am tham lam mat so lieu that.
    """
    if not chuoi:
        return None
    chu = str(chuoi).strip()
    if not chu:
        return None
    try:
        moc = datetime.fromisoformat(chu.replace(" ", "T"))
    except ValueError:
        return None
    if moc.tzinfo is None:
        moc = moc.replace(tzinfo=MUI_GIO_VN)
    return moc


def tach_ban_ghi_qua_cu(cac_ban_ghi, nguong_ngay=None, bay_gio=None):
    """Tach danh sach ban ghi thanh (con_hieu_luc, qua_cu).

    Ban ghi "qua cu" la ban ghi co thoi_diem cach bay gio hon nguong_ngay. Mac
    dinh nguong lay tu cau_hinh.SO_DO_CU_TOI_DA_NGAY; dat 0 la tat phep loc.

    HAI DIEU CO Y:

    1. Ban ghi KHONG co thoi_diem doc duoc thi giu lai. Khong biet tuoi thi
       khong duoc phep doan la cu roi bo di.
    2. Chi xet truong thoi_diem, la moc MOI NHAT cua ban ghi. Khong xet
       thoi_diem_chat_luong rieng: nuoc duoi dat lay mau hoa hoc vai lan mot
       nam nen moc do thuong cach moc muc nuoc nhieu thang, xet rieng thi se
       bo ca nhung lo khoan dang do hang ngay. Giao dien hien du ca hai moc
       nen nguoi doc van thay ky lay mau la bao gio.
    """
    if nguong_ngay is None:
        nguong_ngay = cau_hinh.SO_DO_CU_TOI_DA_NGAY
    if not nguong_ngay or nguong_ngay <= 0:
        return list(cac_ban_ghi), []

    if bay_gio is None:
        bay_gio = datetime.now(MUI_GIO_VN)
    han = bay_gio - timedelta(days=nguong_ngay)

    con_hieu_luc, qua_cu = [], []
    for bg in cac_ban_ghi:
        moc = doc_moc_thoi_gian(bg.get("thoi_diem"))
        if moc is not None and moc < han:
            qua_cu.append(bg)
        else:
            con_hieu_luc.append(bg)
    return con_hieu_luc, qua_cu


def thoi_diem_chung(cac_ban_ghi):
    """Thoi diem cua goi du lieu.

    Uu tien thoi diem do moi nhat trong cac ban ghi. Khong co thi lay luc goi
    nguon, vi do la thoi diem so lieu nay duoc doc ve.
    """
    cac_moc = [bg.get("thoi_diem") for bg in cac_ban_ghi
               if bg.get("thoi_diem")]
    if cac_moc:
        return max(cac_moc)
    return datetime.now(MUI_GIO_VN).isoformat(timespec="minutes")


def thong_so_so_hoc(ban_ghi):
    """Ten cac truong so do co gia tri la SO trong mot ban ghi.

    Dung cho khoi "so_do_cu": ban ghi bi an thi gia tri khong ra den trinh
    duyet nua, nhung TEN thong so thi van phai ra, de giao dien biet con thong
    so nao ve duoc bieu do chuoi thoi gian. Khong co danh sach nay thi o chon
    thong so rong, va chuoi cua tram do thanh khong the voi toi tu giao dien
    du /api/quan-trac/chuoi co y khong loc.

    Loai bool ra, vi trong Python bool la mot kieu con cua int: khong loai thi
    co wqi_tu_tinh=True bi ke la mot thong so ve duoc bieu do.
    """
    return [k for k, v in ban_ghi.items()
            if k != "ma" and k not in TRUONG_BO_QUA
            and isinstance(v, (int, float)) and not isinstance(v, bool)]


def goi_so_do(cac_ban_ghi, qua_cu=None):
    """Dung goi du lieu hoan chinh tu danh sach ban ghi da chuan hoa.

    qua_cu la cac ban ghi da bi an vi so do qua cu, do tang nguon tach ra. Goi
    du lieu bao ro so luong va danh sach ma, khong im lang lam mat du lieu roi
    de nguoi dung tu phat hien - cung nguyen tac voi khoi thong_ke cua
    khong_gian.tap_feature().
    """
    doi_tuong = {}

    for bg in cac_ban_ghi:
        ma = bg.get("ma")
        if not ma:
            continue
        ban_ghi = {k: v for k, v in bg.items()
                   if k not in TRUONG_BO_QUA and k != "ma"}
        doi_tuong[ma] = ban_ghi

    qua_cu = qua_cu or []
    return {
        "thoi_diem": thoi_diem_chung(cac_ban_ghi),
        "che_do": cau_hinh.CHE_DO,
        "nguon_dl": cau_hinh.mo_ta_nguon(),
        "so_doi_tuong": len(doi_tuong),
        "doi_tuong": doi_tuong,
        "canh_bao": dung_canh_bao(cac_ban_ghi),
        "so_do_cu": {
            "nguong_ngay": cau_hinh.SO_DO_CU_TOI_DA_NGAY,
            "so_ban_ghi": len(qua_cu),
            "cong_trinh": [
                {"ma": bg.get("ma"), "ten": bg.get("ten"),
                 "thoi_diem": bg.get("thoi_diem"),
                 "thong_so": thong_so_so_hoc(bg)}
                for bg in qua_cu if bg.get("ma")
            ],
        },
    }
