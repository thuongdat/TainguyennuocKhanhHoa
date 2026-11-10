r"""Dich vu API trung gian giua CSDL Quan trac Quoc gia va trang WebGIS.

Chay cuc bo:
    cd backend
    D:\\Anaconda_Data\\envs\\tainguyennuoc\\python.exe -m uvicorn main:app --port 8001 --reload

Vi sao can lop trung gian nay chu khong cho trinh duyet goi thang CSDL:
  1. Thong tin dang nhap CSDL khong duoc ra den trinh duyet.
  2. CSDL QTQG la cua ca nuoc va khong phai dinh dang khong gian cho web;
     o day no duoc loc ve pham vi tinh roi doi thanh GeoJSON.
  3. Bo nho dem 60 giay bao ve CSDL dang chay that khoi luot goi lap.
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

import bo_nho_dem
import cau_hinh
import khong_gian
import luu_tru
import nguon_qtqg
import tong_hop

@asynccontextmanager
async def vong_doi(_app):
    """Chay luc khoi dong dich vu.

    Bao ngay neu thieu cau hinh, thay vi de den luc co nguoi mo trang moi phat
    hien ra khong co thong tin ket noi.
    """
    thieu = cau_hinh.kiem_tra_cau_hinh()
    if thieu:
        print("CANH BAO: chay o che do that nhung thieu bien {}."
              .format(", ".join(thieu)), file=sys.stderr)
    print("Che do: {}".format(cau_hinh.CHE_DO))
    print("Cong dich vu (tinh.json cong.backend): {}".format(cau_hinh.CONG))
    print("Nguon duoc phep goi (CORS): {}".format(
        ", ".join(cau_hinh.CORS_NGUON)))
    canh_bao = cau_hinh.canh_bao_cors()
    if canh_bao:
        print(canh_bao, file=sys.stderr)
    luu_tru.dung_bang()
    yield


app = FastAPI(
    lifespan=vong_doi,
    title="API trung gian quan trắc QTQG",
    description="Lấy số liệu quan trắc từ cơ sở dữ liệu Quan trắc Quốc gia, "
                "chuẩn hóa thành GeoJSON và gói số đo cho trang WebGIS.",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=cau_hinh.CORS_NGUON,
    allow_credentials=False,
    allow_methods=["GET"],
    allow_headers=["*"],
)


def _loi_nguon(e):
    """Doi loi cua tang nguon thanh HTTP 503.

    Chi tiet tra ve la cau da duoc soan san trong cac mo-dun nguon, khong bao
    gio chua chuoi ket noi, ten tai khoan hay dia chi may chu.
    """
    return HTTPException(status_code=503, detail={
        "loi": "Không lấy được số liệu quan trắc",
        "chi_tiet": str(e),
    })


@app.get("/api/suc-khoe")
def suc_khoe():
    """Trang thai dich vu. Giao dien goi dau tien de biet co nen nap tiep."""
    ket_qua = {
        "trang_thai": "san_sang",
        "che_do": cau_hinh.CHE_DO,
        "nguon_dl": cau_hinh.mo_ta_nguon(),
        "thoi_diem": tong_hop.thoi_diem_chung([]),
        "csdl_ket_noi": None,
        "so_tram": None,
        "thieu_cau_hinh": cau_hinh.kiem_tra_cau_hinh(),
    }

    try:
        cac_tram = bo_nho_dem.lay_hoac_tinh(
            "tram", nguon_qtqg.lay_danh_sach_tram)
        ket_qua["so_tram"] = len(cac_tram)
        ket_qua["csdl_ket_noi"] = cau_hinh.la_nguon_that()
    except Exception as e:
        ket_qua["trang_thai"] = "loi_nguon"
        ket_qua["csdl_ket_noi"] = False
        ket_qua["chi_tiet"] = str(e)

    return ket_qua


@app.get("/api/quan-trac/tram.geojson")
def tram_geojson(loc_theo_tinh: bool = Query(
        True, description="Lọc bỏ trạm ngoài khung bao của tỉnh")):
    """Vi tri cac tram quan trac, dang GeoJSON EPSG:4326."""
    try:
        cac_tram = bo_nho_dem.lay_hoac_tinh(
            "tram", nguon_qtqg.lay_danh_sach_tram)
    except Exception as e:
        raise _loi_nguon(e)

    tap = khong_gian.tap_feature(cac_tram, loc_theo_tinh=loc_theo_tinh)
    return JSONResponse(content=tap,
                        media_type="application/geo+json; charset=utf-8")


@app.get("/api/quan-trac/so-do")
def so_do():
    """So do moi nhat, dung schema cua data/realtime.json."""
    try:
        cac_ban_ghi = bo_nho_dem.lay_hoac_tinh(
            "so_do", nguon_qtqg.lay_so_do_moi_nhat)
    except Exception as e:
        raise _loi_nguon(e)

    # An ban ghi co so do qua cu. Loc o day chu khong trong bo nho dem, de
    # bo dem giu nguyen du lieu tho: doi nguong thi khong phai xoa dem, va con
    # bao duoc cho giao dien biet da an nhung cong trinh nao.
    con_hieu_luc, qua_cu = tong_hop.tach_ban_ghi_qua_cu(cac_ban_ghi)
    goi = tong_hop.goi_so_do(con_hieu_luc, qua_cu)

    # Tich luy vao SQLite cuc bo de bieu do co chuoi thoi gian. Loi ghi khong
    # duoc lam that bai yeu cau doc: so do van phai den duoc nguoi dung.
    try:
        luu_tru.ghi_mot_luot(con_hieu_luc, goi.get("thoi_diem"))
    except Exception as e:
        print("Canh bao: khong ghi duoc chuoi vao SQLite: {}".format(e),
              file=sys.stderr)

    return goi


@app.get("/api/quan-trac/chuoi")
def chuoi(
    ma: str = Query(..., min_length=1, description="Mã trạm"),
    thong_so: str = Query("wqi", min_length=1,
                          description="Tên trường số đo, ví dụ wqi, h_m, ph"),
    tu: str = Query(None, description="Thời điểm bắt đầu, dạng ISO"),
    den: str = Query(None, description="Thời điểm kết thúc, dạng ISO"),
):
    """Chuoi thoi gian cua mot tram, mot thong so, de ve bieu do."""
    try:
        cac_diem = nguon_qtqg.lay_chuoi(ma, thong_so, tu, den)
    except Exception as e:
        raise _loi_nguon(e)

    return {
        "ma": ma,
        "thong_so": thong_so,
        "che_do": cau_hinh.CHE_DO,
        "so_diem": len(cac_diem),
        "diem": cac_diem,
    }


@app.get("/api/quan-trac/thong-so-co-chuoi")
def thong_so_co_chuoi(ma: str = Query(..., min_length=1)):
    """Cac thong so da tich luy duoc chuoi cho mot tram.

    Giao dien dung de chi hien nhung thong so thuc su ve duoc bieu do.
    """
    if not cau_hinh.la_nguon_that():
        # O che do thu nghiem, moi thong so deu sinh duoc chuoi 48 gio
        return {"ma": ma, "che_do": cau_hinh.CHE_DO, "thong_so": []}
    try:
        return {"ma": ma, "che_do": cau_hinh.CHE_DO,
                "thong_so": luu_tru.thong_so_co_chuoi(ma)}
    except Exception as e:
        raise _loi_nguon(e)


# --------------------------------------------------------------------------
# Chay truc tiep:  python main.py
# --------------------------------------------------------------------------
# Cach nay lay cong tu tinh.json nen khong bao gio go sai so. Dung
# "uvicorn main:app --port <cong>" thi phai tu go cong, va moi tinh mot cong
# khac nhau nen de go nham sang cong cua tinh ben.
if __name__ == "__main__":
    import uvicorn

    # Mac dinh chi nghe tren may nay. Trong container thi phai nghe moi dia
    # chi, Dockerfile dat CONG_LANG_NGHE=0.0.0.0.
    dia_chi = os.environ.get("CONG_LANG_NGHE") or "127.0.0.1"
    tu_nap_lai = dia_chi == "127.0.0.1"

    uvicorn.run("main:app", host=dia_chi, port=cau_hinh.CONG,
                reload=tu_nap_lai)
