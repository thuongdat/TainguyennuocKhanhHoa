r"""Chay may chu web cuc bo cho dung tinh nay, dung cong nay, dung thu muc nay.

    python scripts/chay_web.py

VI SAO CAN MOT TEP RIENG THAY VI GO  python -m http.server 8000

Moi tinh la mot du an rieng nhung deu chay tren localhost, nen co hai cach go
sai ma KHONG he bao loi:

  1. Sai thu muc. "python -m http.server 8000" phuc vu thu muc dang dung, nen
     go lenh do o thu muc tinh khac la trang hien du lieu tinh khac.
  2. Sai cong. Python dat SO_REUSEADDR nen NHIEU tien trinh bind duoc cung mot
     cong 8000, moi tien trinh phuc vu mot thu muc, va he dieu hanh chia yeu
     cau cho cac tien trinh do. Ban do co the ve ranh gioi tinh khac trong khi
     tieu de trang da dung. Rat kho doan ra vi ma nguon khong co gi sai.

Tep nay chan ca hai: no luon phuc vu thu muc goc du an chua chinh no, lay cong
tu cong.web trong tinh.json, va bao ngay neu cong da co nguoi dung.

Chi dung thu vien chuan, khong can moi truong conda.
"""

import json
import os
import socket
import sys
from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer

GOC_DU_AN = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TEP_THAM_SO = os.path.join(GOC_DU_AN, "tinh.json")


def _in_duoc_tieng_viet():
    """Ep stdout/stderr sang UTF-8.

    Console Windows mac dinh la cp1252, va khi chuyen huong ra tep thi Python
    cung dung cp1252. Chu "Tinh" co dau khi do lam UnicodeEncodeError va
    script CHET truoc khi kip phuc vu - may chu khong len ma loi bao ra lai la
    loi ma hoa, khong lien quan gi den web. errors="replace" de dam bao in
    duoc du moi truong co la gi.
    """
    for luong in (sys.stdout, sys.stderr):
        if hasattr(luong, "reconfigure"):
            try:
                luong.reconfigure(encoding="utf-8", errors="replace")
            except (OSError, ValueError):
                pass


_in_duoc_tieng_viet()


def doc_tham_so():
    if not os.path.isfile(TEP_THAM_SO):
        raise SystemExit("Không thấy {}".format(TEP_THAM_SO))
    with open(TEP_THAM_SO, encoding="utf-8") as f:
        return json.load(f)


def cong_dang_co_nguoi_dung(cong):
    """Co ai dang phuc vu o cong nay hay khong.

    Phep thu la KET NOI, khong phai bind. Tren Windows, SO_REUSEADDR cho nhieu
    tien trinh cung bind mot cong, nen bind thanh cong KHONG chung minh duoc
    cong dang trong. Da kiem tren may nay: 8 tien trinh http.server cung nghe
    cong 8000 va tien trinh thu 9 van bind duoc.
    """
    thu = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    thu.settimeout(0.6)
    try:
        return thu.connect_ex(("127.0.0.1", cong)) == 0
    finally:
        thu.close()


class MayChu(ThreadingHTTPServer):
    """Khong cho bind trung cong.

    allow_reuse_address = False la du tren Linux. Tren Windows phai dat thang
    SO_EXCLUSIVEADDRUSE, neu khong thi SO_REUSEADDR mac dinh van cho tien
    trinh thu hai bind cung cong va he dieu hanh chia yeu cau cho ca hai.
    """

    allow_reuse_address = False

    def server_bind(self):
        if hasattr(socket, "SO_EXCLUSIVEADDRUSE"):
            try:
                self.socket.setsockopt(
                    socket.SOL_SOCKET, socket.SO_EXCLUSIVEADDRUSE, 1)
            except OSError:
                pass        # khong dat duoc thi van chay, chi mat lop bao ve
        return ThreadingHTTPServer.server_bind(self)


def main():
    tt = doc_tham_so()
    cong = int((tt.get("cong") or {}).get("web", 8000))
    ten = tt.get("ten_ngan") or tt.get("ten_tinh") or tt.get("ma") or "?"

    if cong_dang_co_nguoi_dung(cong):
        raise SystemExit(
            "Cổng {0} đã có tiến trình khác dùng.\n"
            "Đây thường là một máy chủ cũ còn chạy, có thể đang phục vụ thư "
            "mục của tỉnh khác.\n"
            "Xem ai đang dùng:   netstat -ano | findstr :{0}\n"
            "Rồi dừng nó:        taskkill /PID <PID> /F".format(cong))

    bo_xu_ly = partial(SimpleHTTPRequestHandler, directory=GOC_DU_AN)
    try:
        may_chu = MayChu(("127.0.0.1", cong), bo_xu_ly)
    except OSError as e:
        raise SystemExit(
            "Không mở được cổng {0}: {1}\n"
            "Xem ai đang dùng:   netstat -ano | findstr :{0}".format(cong, e))

    print("Tỉnh:      {}".format(ten))
    print("Thư mục:   {}".format(GOC_DU_AN))
    print("Địa chỉ:   http://localhost:{}/".format(cong))
    print("Quan trắc: http://localhost:{}/pages/quan-trac.html".format(cong))
    print("Dừng bằng Ctrl+C")

    try:
        may_chu.serve_forever()
    except KeyboardInterrupt:
        print("\nĐã dừng.")
    finally:
        may_chu.server_close()


if __name__ == "__main__":
    sys.exit(main())
