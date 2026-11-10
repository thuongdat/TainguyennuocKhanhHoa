# Ban dong backend trung gian QTQG.
#
# Dung tu thu muc GOC du an, khong phai tu backend/, vi che do thu_nghiem can
# doc data/quan_trac.geojson va tinh.json:
#     docker build -f backend/Dockerfile -t quan-trac-qtqg .
#     docker run --env-file backend/.env -p 8001:8001 quan-trac-qtqg
#
# Cong 8001 la cong.backend trong tinh.json cua tinh NAY. Moi tinh mot cap
# cong rieng (Khanh Hoa 8000/8001, Gia Lai 8010/8011) nen khi sao du an sang
# tinh khac thi doi ca so o lenh -p va o dong EXPOSE duoi day. Ben trong anh
# thi khong phai doi gi: CMD goi main.py, va main.py doc cong tu tinh.json.
FROM python:3.12-slim

WORKDIR /app

COPY backend/requirements.txt /app/backend/requirements.txt
RUN pip install --no-cache-dir -r /app/backend/requirements.txt

COPY backend/ /app/backend/
COPY tinh.json /app/tinh.json
COPY data/quan_trac.geojson /app/data/quan_trac.geojson

WORKDIR /app/backend

# Khong chay bang vai root
RUN useradd --create-home dichvu && chown -R dichvu /app
USER dichvu

# Chi la ghi chu cho nguoi doc, Docker khong mo cong theo dong nay
EXPOSE 8001

# Goi main.py chu khong goi uvicorn truc tiep: main.py doc cong tu tinh.json
# nen khong bao gio lech voi cong ma giao dien goi den.
# CONG_LANG_NGHE=0.0.0.0 vi trong container phai nghe moi dia chi.
ENV CONG_LANG_NGHE=0.0.0.0
CMD ["python", "main.py"]
