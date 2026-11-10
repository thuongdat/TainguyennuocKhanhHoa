r"""Chuyen ky hieu diem tu tep .qml cua QGIS thanh SVG dung duoc tren web.

Nguon:  CSDL/symbol_QGIS/*.qml
Ra:     assets/ky_hieu/*.svg  va  assets/ky_hieu/ky_hieu.json

Chay:
    D:\Anaconda_Data\envs\tainguyennuoc\python.exe -X utf8 scripts/06_tao_ky_hieu.py

Script chi dung thu vien chuan nen khong can goi sua_duong_dan_proj().

VI SAO PHAI CHUYEN
QML la dinh dang rieng cua QGIS, trinh duyet khong doc duoc. Hai loai lop ky
hieu diem can xu ly khac nhau:

  SimpleMarker  hinh dung san (circle, line, diamond, equilateral_triangle...).
                Ve lai bang the SVG tuong ung.
  SvgMarker     tro toi mot tep SVG trong thu vien cua QGIS, vi du
                "tourist/tourist_beach.svg". Phai doc tep do tu thu muc cai
                dat QGIS roi nhung vao.

Tep SVG cua QGIS co hai kieu:
  - Tranh mau co dinh (tourist_beach, blue-marker): mau trong QML bi bo qua.
  - Co cho thay mau, viet dang param(fill), param(outline), param(outline-width).
    Nhung cho nay duoc thay bang mau ghi trong QML.

HE TOA DO CUA TEP SINH RA
Moi ky hieu ve trong viewBox "-50 -50 100 100", goc toa do o giua. Mot milimet
cua QGIS bang 10 don vi trong viewBox. Nho the mot tep SVG dung duoc o moi co,
con co thuc te thi lay tu truong kich_thuoc_mm trong ky_hieu.json.
"""

import glob
import io
import json
import os
import re
import sys
import xml.etree.ElementTree as ET

GOC = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
THU_MUC_QML = os.path.join(GOC, "CSDL", "symbol_QGIS")
THU_MUC_RA = os.path.join(GOC, "assets", "ky_hieu")

# Thu muc svg cua QGIS, do SvgMarker tro toi. Thu lan luot cac ban da cai.
UNG_VIEN_SVG_QGIS = [
    r"C:\Program Files\QGIS 3.32.1\apps\qgis\svg",
    r"C:\Program Files\QGIS 3.28.3\apps\qgis\svg",
    r"C:\OSGeo4W\apps\qgis\svg",
    r"C:\OSGeo4W64\apps\qgis\svg",
]

# Mot milimet cua QGIS bang bao nhieu don vi trong viewBox
DON_VI_MOI_MM = 10.0

KIEU_HINH_HOC_DIEM = "0"


# ---------------------------------------------------------------------------
# Doc QML
# ---------------------------------------------------------------------------

def doc_tuy_chon(lop):
    """Cac Option nam truc tiep trong mot <layer>, bo data_defined_properties."""
    o = {}
    for con in lop:
        if con.tag != "Option":
            continue
        for op in con.findall("Option"):
            if op.get("value") is not None:
                o[op.get("name")] = op.get("value")
    return o


def doc_ky_hieu(duong_dan):
    """Tra ve (kieu_hinh_hoc, danh sach lop ky hieu diem) cua mot tep QML."""
    cay = ET.parse(duong_dan).getroot()

    g = cay.find("layerGeometryType")
    kieu_hh = g.text.strip() if g is not None and g.text else None

    r = cay.find("renderer-v2")
    if r is None:
        return kieu_hh, []

    cac_lop = []
    for sym in r.iter("symbol"):
        if sym.get("type") != "marker":
            continue
        for lop in sym.findall("layer"):
            cac_lop.append((lop.get("class"), doc_tuy_chon(lop)))
        break      # chi lay ky hieu dau tien cua renderer
    return kieu_hh, cac_lop


def mau_qgis(chuoi, mac_dinh="#000000"):
    """Doi "r,g,b,a" cua QGIS thanh (mau hex, do mo tu 0 den 1)."""
    if not chuoi:
        return mac_dinh, 1.0
    phan = [p.strip() for p in chuoi.split(",")]
    try:
        r, g, b = int(phan[0]), int(phan[1]), int(phan[2])
    except (ValueError, IndexError):
        return mac_dinh, 1.0
    a = 1.0
    if len(phan) > 3:
        try:
            a = int(phan[3]) / 255.0
        except ValueError:
            a = 1.0
    return "#{:02x}{:02x}{:02x}".format(r, g, b), a


def so(chuoi, mac_dinh=0.0):
    try:
        return float(chuoi)
    except (TypeError, ValueError):
        return mac_dinh


def doi_ly(chuoi):
    """Cap "x,y" tinh bang mm, doi sang don vi viewBox. Truc y cua QGIS huong
    len tren, cua SVG huong xuong, nen phai doi dau."""
    if not chuoi:
        return 0.0, 0.0
    phan = chuoi.split(",")
    x = so(phan[0]) * DON_VI_MOI_MM
    y = -so(phan[1]) * DON_VI_MOI_MM if len(phan) > 1 else 0.0
    return x, y


# ---------------------------------------------------------------------------
# SimpleMarker: ve lai hinh dung san cua QGIS
# ---------------------------------------------------------------------------

def _da_giac(cac_diem):
    return " ".join("{:.3f},{:.3f}".format(x, y) for x, y in cac_diem)


def hinh_simple_marker(ten_hinh, nua):
    """Tra ve (ten the SVG, dict thuoc tinh, co_to_mau).

    nua la nua kich thuoc, tinh bang don vi viewBox.
    co_to_mau = False voi cac hinh chi co net, QGIS khong to mau chung.
    """
    t = (ten_hinh or "circle").lower()

    if t in ("circle", "circle_fill"):
        return "circle", {"cx": "0", "cy": "0", "r": "{:.3f}".format(nua)}, True

    if t == "square":
        return "rect", {"x": "{:.3f}".format(-nua), "y": "{:.3f}".format(-nua),
                        "width": "{:.3f}".format(nua * 2),
                        "height": "{:.3f}".format(nua * 2)}, True

    if t == "diamond":
        return "polygon", {"points": _da_giac(
            [(0, -nua), (nua, 0), (0, nua), (-nua, 0)])}, True

    if t in ("triangle", "equilateral_triangle"):
        # Tam giac deu noi tiep duong tron ban kinh nua
        return "polygon", {"points": _da_giac(
            [(0, -nua), (nua * 0.866, nua * 0.5), (-nua * 0.866, nua * 0.5)])}, True

    if t == "pentagon":
        import math
        cac = [(nua * math.sin(2 * math.pi * i / 5),
                -nua * math.cos(2 * math.pi * i / 5)) for i in range(5)]
        return "polygon", {"points": _da_giac(cac)}, True

    if t == "hexagon":
        import math
        cac = [(nua * math.cos(math.pi / 3 * i),
                nua * math.sin(math.pi / 3 * i)) for i in range(6)]
        return "polygon", {"points": _da_giac(cac)}, True

    if t == "line":
        # Doan thang dung, dai bang kich thuoc
        return "line", {"x1": "0", "y1": "{:.3f}".format(-nua),
                        "x2": "0", "y2": "{:.3f}".format(nua)}, False

    if t in ("cross", "cross2", "cross_fill"):
        d = "M {0:.3f},0 L {1:.3f},0 M 0,{0:.3f} L 0,{1:.3f}".format(-nua, nua)
        if t == "cross2":
            d = ("M {0:.3f},{0:.3f} L {1:.3f},{1:.3f} "
                 "M {1:.3f},{0:.3f} L {0:.3f},{1:.3f}").format(-nua, nua)
        return "path", {"d": d}, False

    if t in ("asterisk_fill", "star"):
        import math
        d = []
        for i in range(6):
            goc = math.pi / 3 * i
            d.append("M 0,0 L {:.3f},{:.3f}".format(
                nua * math.cos(goc), nua * math.sin(goc)))
        return "path", {"d": " ".join(d)}, False

    if t == "arrowhead":
        d = "M {0:.3f},{1:.3f} L 0,0 L {0:.3f},{2:.3f}".format(-nua, -nua, nua)
        return "path", {"d": d}, False

    print("   canh bao: chua ve duoc hinh '{}', tam dung hinh tron".format(t))
    return "circle", {"cx": "0", "cy": "0", "r": "{:.3f}".format(nua)}, True


def ve_simple_marker(tuy_chon):
    """Mot lop SimpleMarker thanh mot chuoi the SVG."""
    kich_thuoc = so(tuy_chon.get("size"), 2.0) * DON_VI_MOI_MM
    nua = kich_thuoc / 2.0
    do_day = so(tuy_chon.get("outline_width"), 0.0) * DON_VI_MOI_MM

    mau_nen, mo_nen = mau_qgis(tuy_chon.get("color"), "#000000")
    mau_vien, mo_vien = mau_qgis(tuy_chon.get("outline_color"), "#000000")

    the, thuoc_tinh, co_to_mau = hinh_simple_marker(tuy_chon.get("name"), nua)

    if co_to_mau:
        thuoc_tinh["fill"] = mau_nen
        if mo_nen < 1:
            thuoc_tinh["fill-opacity"] = "{:.3f}".format(mo_nen)
        if do_day > 0 and tuy_chon.get("outline_style", "solid") != "no":
            thuoc_tinh["stroke"] = mau_vien
            thuoc_tinh["stroke-width"] = "{:.3f}".format(do_day)
            if mo_vien < 1:
                thuoc_tinh["stroke-opacity"] = "{:.3f}".format(mo_vien)
    else:
        # Hinh chi co net. QGIS ve bang but, lay mau nen cua lop lam mau net.
        thuoc_tinh["fill"] = "none"
        thuoc_tinh["stroke"] = mau_nen
        # outline_width = 0 nghia la net manh nhat, khong phai khong ve
        thuoc_tinh["stroke-width"] = "{:.3f}".format(do_day if do_day > 0 else 2.0)
        thuoc_tinh["stroke-linecap"] = "round"
        if mo_nen < 1:
            thuoc_tinh["stroke-opacity"] = "{:.3f}".format(mo_nen)

    dx, dy = doi_ly(tuy_chon.get("offset"))
    chuoi_tt = " ".join('{}="{}"'.format(k, v)
                        for k, v in sorted(thuoc_tinh.items()))
    the_svg = "<{} {}/>".format(the, chuoi_tt)

    if dx or dy:
        return '<g transform="translate({:.3f},{:.3f})">{}</g>'.format(
            dx, dy, the_svg)
    return the_svg


# ---------------------------------------------------------------------------
# SvgMarker: nhung tep SVG cua QGIS
# ---------------------------------------------------------------------------

def tim_thu_muc_svg_qgis():
    for d in UNG_VIEN_SVG_QGIS:
        if os.path.isdir(d):
            return d
    return None


def ve_svg_marker(tuy_chon, thu_muc_svg, chi_so_lop=0):
    """Mot lop SvgMarker thanh mot chuoi the SVG long nhau."""
    ten_tep = (tuy_chon.get("name") or "").replace("\\", "/")
    if not ten_tep:
        return None

    duong_dan = os.path.join(thu_muc_svg, *ten_tep.split("/"))
    if not os.path.isfile(duong_dan):
        print("   canh bao: khong tim thay {}".format(ten_tep))
        return None

    with io.open(duong_dan, encoding="utf-8") as f:
        noi_dung = f.read()

    mau_nen, mo_nen = mau_qgis(tuy_chon.get("color"), "#000000")
    mau_vien, mo_vien = mau_qgis(tuy_chon.get("outline_color"), "#232323")
    do_day = so(tuy_chon.get("outline_width"), 0.0) * DON_VI_MOI_MM

    # Thay cac cho de trong cua QGIS bang mau ghi trong QML
    thay = {
        "param(fill)": mau_nen,
        "param(outline)": mau_vien,
        "param(stroke)": mau_vien,
        "param(fill-opacity)": "{:.3f}".format(mo_nen),
        "param(outline-opacity)": "{:.3f}".format(mo_vien),
        "param(stroke-opacity)": "{:.3f}".format(mo_vien),
        "param(outline-width)": "{:.3f}".format(max(do_day, 0.0)),
        "param(stroke-width)": "{:.3f}".format(max(do_day, 0.0)),
    }
    for cu, moi in thay.items():
        noi_dung = noi_dung.replace(cu, moi)
    # Con cho nao khong biet thi bo di, de trinh duyet khong bao loi
    noi_dung = re.sub(r"param\([^)]*\)", "none", noi_dung)

    # Lay viewBox de biet kich thuoc goc
    khop = re.search(r'viewBox="([^"]+)"', noi_dung)
    if khop:
        p = [so(x) for x in khop.group(1).replace(",", " ").split()]
        goc_x, goc_y, rong, cao = (p + [0, 0, 100, 100])[:4]
    else:
        goc_x, goc_y, rong, cao = 0, 0, 100, 100
    if not rong or not cao:
        rong = cao = 100

    # Lay phan ben trong the <svg>
    ben_trong = re.sub(r"^.*?<svg[^>]*>", "", noi_dung, flags=re.S)
    ben_trong = re.sub(r"</svg>\s*$", "", ben_trong, flags=re.S)
    # Bo khai bao XML va DOCTYPE neu lot vao
    ben_trong = re.sub(r"<\?xml[^>]*\?>", "", ben_trong)
    ben_trong = re.sub(r"<!DOCTYPE[^>]*>", "", ben_trong)

    # Doi ten moi id thanh duy nhat trong tep sinh ra. Nhieu tep cua QGIS dat
    # id rat ngan nhu "a", "b"; hai lop cung dung thi tham chieu gradient se
    # tro nham sang lop kia.
    tien_to = "k{}_".format(chi_so_lop)
    ben_trong = re.sub(r'id="([^"]+)"',
                       lambda m: 'id="' + tien_to + m.group(1) + '"',
                       ben_trong)
    ben_trong = re.sub(r"url\(#([^)]+)\)",
                       lambda m: "url(#" + tien_to + m.group(1) + ")",
                       ben_trong)
    ben_trong = re.sub(r'xlink:href="#([^"]+)"',
                       lambda m: 'xlink:href="#' + tien_to + m.group(1) + '"',
                       ben_trong)

    kich_thuoc = so(tuy_chon.get("size"), 4.0) * DON_VI_MOI_MM
    ty_le = kich_thuoc / max(rong, cao)
    dx, dy = doi_ly(tuy_chon.get("offset"))

    return ('<g transform="translate({:.3f},{:.3f}) scale({:.5f}) '
            'translate({:.3f},{:.3f})">{}</g>').format(
        dx - kich_thuoc / 2.0, dy - kich_thuoc / 2.0, ty_le,
        -goc_x, -goc_y, ben_trong)


# ---------------------------------------------------------------------------
# Sinh tep
# ---------------------------------------------------------------------------

def kich_thuoc_mm(cac_lop):
    """Co lon nhat trong cac lop, dung lam co hien thi mac dinh."""
    lon_nhat = 0.0
    for _, tc in cac_lop:
        lon_nhat = max(lon_nhat, so(tc.get("size"), 0.0))
    return lon_nhat or 4.0


def tao_mot_ky_hieu(duong_dan_qml, thu_muc_svg):
    ten = os.path.splitext(os.path.basename(duong_dan_qml))[0]
    kieu_hh, cac_lop = doc_ky_hieu(duong_dan_qml)

    if kieu_hh != KIEU_HINH_HOC_DIEM or not cac_lop:
        return None

    print(" {} ({} lop)".format(ten, len(cac_lop)))

    cac_the = []
    for lop_class, tc in cac_lop:
        if lop_class == "SimpleMarker":
            cac_the.append(ve_simple_marker(tc))
        elif lop_class in ("SvgMarker", "RasterMarker"):
            if not thu_muc_svg:
                print("   canh bao: chua tim thay thu muc svg cua QGIS")
                continue
            the = ve_svg_marker(tc, thu_muc_svg, len(cac_the))
            if the:
                cac_the.append(the)
        elif lop_class == "FilledMarker":
            print("   canh bao: FilledMarker chua ho tro, bo qua mot lop")
        else:
            print("   canh bao: chua ho tro lop {}".format(lop_class))

    if not cac_the:
        return None

    # Phai khai bao ca xlink: nhieu tep cua QGIS dung xlink:href de tham chieu
    # gradient. Thieu namespace thi trinh duyet coi la SVG hong, khong ve gi.
    svg = ('<svg xmlns="http://www.w3.org/2000/svg" '
           'xmlns:xlink="http://www.w3.org/1999/xlink" '
           'viewBox="-50 -50 100 100">\n'
           '<!-- Sinh tu CSDL/symbol_QGIS/{}.qml bang scripts/06_tao_ky_hieu.py.\n'
           '     Dung sua tay: chay lai script se ghi de. -->\n'
           '{}\n</svg>\n').format(ten, "\n".join(cac_the))

    duong_dan_ra = os.path.join(THU_MUC_RA, ten + ".svg")
    with io.open(duong_dan_ra, "w", encoding="utf-8", newline="\n") as f:
        f.write(svg)

    return {"tep": "ky_hieu/" + ten + ".svg",
            "kich_thuoc_mm": round(kich_thuoc_mm(cac_lop), 3),
            "so_lop": len(cac_lop)}


def main():
    if not os.path.isdir(THU_MUC_QML):
        print("Không tìm thấy thư mục {}".format(THU_MUC_QML))
        return 2

    os.makedirs(THU_MUC_RA, exist_ok=True)

    thu_muc_svg = tim_thu_muc_svg_qgis()
    if thu_muc_svg:
        print("Thư viện SVG của QGIS: {}".format(thu_muc_svg))
    else:
        print("Cảnh báo: không tìm thấy thư viện SVG của QGIS. "
              "Các ký hiệu dạng SvgMarker sẽ bị bỏ qua.")
    print("")

    danh_muc = {}
    for qml in sorted(glob.glob(os.path.join(THU_MUC_QML, "*.qml"))):
        try:
            ket_qua = tao_mot_ky_hieu(qml, thu_muc_svg)
        except Exception as e:
            print(" {}: LỖI {}".format(os.path.basename(qml), e))
            continue
        if ket_qua:
            ten = os.path.splitext(os.path.basename(qml))[0]
            danh_muc[ten] = ket_qua

    duong_dan_danh_muc = os.path.join(THU_MUC_RA, "ky_hieu.json")
    with io.open(duong_dan_danh_muc, "w", encoding="utf-8", newline="\n") as f:
        f.write(json.dumps({
            "ghi_chu": ("Danh mục ký hiệu điểm, sinh từ CSDL/symbol_QGIS "
                        "bằng scripts/06_tao_ky_hieu.py. Mỗi tệp SVG vẽ trong "
                        "viewBox -50 -50 100 100, gốc tọa độ ở giữa, một "
                        "milimét của QGIS bằng 10 đơn vị viewBox."),
            "ky_hieu": danh_muc,
        }, ensure_ascii=False, indent=2) + "\n")

    print("")
    print("Đã tạo {} ký hiệu trong {}".format(len(danh_muc), THU_MUC_RA))
    return 0


if __name__ == "__main__":
    sys.exit(main())
