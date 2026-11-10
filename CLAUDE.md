# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Yêu cầu gốc của dự án

Vai trò: chuyên gia GIS và tài nguyên nước, đồng thời là chuyên gia phần mềm.

Xây dựng trang web `tainguyennuocKhanhHoa` dạng WebGIS để đưa lên GitHub. Nội dung
thể hiện các lớp kiểm kê nguồn nước mặt (sông suối, ao hồ), khai thác, xả thải,
sức chịu tải của lưu vực sông theo thời gian thực, có bản đồ nền. Có công cụ hỗ
trợ ra quyết định: truy vấn thuộc tính đối tượng bằng cách nhấp chuột, khi trúng
nhiều đối tượng thì hiện danh sách thả xuống; xuất thông tin ra tệp CSV. Trang có
header, nội dung và footer.

Phạm vi là tỉnh Khánh Hòa sau sáp nhập với Ninh Thuận, hiệu lực 01/07/2025.

Dự án này phục vụ **đúng một tỉnh**. Tỉnh khác được làm thành dự án riêng bằng
cách sao chép dự án rồi sửa `tinh.json`; Gia Lai đặt tại `E:\DuAnAI\GIALAI`.
Không thêm cơ chế chọn tỉnh vào đây.

## Lệnh thường dùng

Dự án **không có bước build, không dùng npm**. Phần trang web không có kiểm thử
tự động: việc kiểm chứng là chạy script pipeline rồi mở trang và xem các lớp có
nạp đủ không. Riêng `backend/` **có** bộ kiểm thử, xem mục dưới.

### Chạy trang web

```bash
python scripts/chay_web.py
```

Bắt buộc phải qua máy chủ web. Trình duyệt chặn `fetch()` trên giao thức `file://`
nên mở trực tiếp `index.html` sẽ không nạp được GeoJSON; `app.js` phát hiện trường
hợp này và hiện hướng dẫn thay cho bản đồ.

**Dùng script đó, đừng gõ `python -m http.server 8000`.** Lý do ở mục
[Mỗi tỉnh một cặp cổng riêng](#mỗi-tỉnh-một-cặp-cổng-riêng): gõ tay thì sai thư
mục hoặc trùng cổng mà không có thông báo lỗi nào.

### Chạy backend trung gian QTQG

Chỉ cần khi làm việc với tab Quan trắc. Cửa sổ riêng, song song với lệnh trên:

```bash
cd backend
D:\Anaconda_Data\envs\tainguyennuoc\python.exe main.py
```

Gọi `main.py` chứ không gọi `uvicorn` trực tiếp: nó đọc cổng từ `cong.backend`
trong `tinh.json` nên không lệch với cổng mà giao diện gọi đến.

Rồi mở <http://localhost:8000/pages/quan-trac.html>. Tài liệu API tự sinh ở
<http://localhost:8001/docs>.

### Mỗi tỉnh một cặp cổng riêng

| Tỉnh | Trang web | Backend |
|---|---|---|
| Khánh Hòa (dự án này) | **8000** | **8001** |
| Gia Lai | 8010 | 8011 |
| Tỉnh tiếp theo | 8020 | 8021 |

Hai số này nằm ở `cong.web` và `cong.backend` trong `tinh.json`, **không gắn
cứng ở đâu khác**. Quy ước: cổng backend luôn là cổng web cộng 1.

Vì sao phải tách cổng, đây là hai lỗi đã xảy ra thật:

1. **Cache trình duyệt lẫn giữa hai dự án.** Mọi dự án đều chạy trên
   `http://localhost:8000` nên cùng một origin, mà trình duyệt lấy URL làm khóa
   cache. Mở Khánh Hòa sau Gia Lai thì bản đồ vẽ ranh giới Gia Lai trong khi
   tiêu đề trang đã là Khánh Hòa. Khác cổng là khác origin, cache không bao giờ
   lẫn. Tham số `?tinh=<ma>` ở mục dưới là lớp bảo vệ thứ hai.
2. **Nhiều máy chủ cùng nghe một cổng.** Python đặt `SO_REUSEADDR` nên nhiều
   tiến trình `http.server` bind được cùng cổng 8000, mỗi tiến trình phục vụ
   thư mục mà nó được khởi động từ đó, và hệ điều hành chia yêu cầu cho tất cả.
   Đã đo trên máy này: **8 tiến trình cùng nghe cổng 8000** mà không ai báo
   lỗi. Nếu một trong số đó chạy từ thư mục tỉnh khác thì trang trộn dữ liệu
   hai tỉnh.

`scripts/chay_web.py` chặn cả hai: luôn phục vụ thư mục gốc dự án chứa chính
nó, lấy cổng từ `tinh.json`, và **từ chối chạy nếu cổng đã có người dùng**.
Phép kiểm là `connect()` chứ không phải `bind()` — trên Windows bind thành công
không chứng minh được cổng đang trống.

Khi lên máy chủ thật thì hai số này không dùng nữa: khai địa chỉ dịch vụ vào
`CAU_HINH.api.goc` trong `assets/js/config.js`.

```bash
cd backend
D:\Anaconda_Data\envs\tainguyennuoc\python.exe -m pytest tests -v
```

Toàn bộ test chạy ở `CHE_DO=thu_nghiem`, **không test nào kết nối QTQG thật**.

### Mật khẩu xuất CSV/GeoJSON

Mọi nút tải tệp đi qua `tai_ve_tep()` trong `assets/js/xuat_tep.js`, và hàm đó
đòi mật khẩu trước khi tải. Đặt mật khẩu bằng lệnh sau (gõ hai lần, không hiện
trên màn hình), nó ghi muối và mã băm PBKDF2-SHA256 vào `xuat_du_lieu` trong
`tinh.json`:

```bash
D:\Anaconda_Data\envs\tainguyennuoc\python.exe scripts/11_dat_mat_khau_xuat.py
```

Ba điều **đừng đổi**: chưa có mã băm thì cổng **đóng** (không bao giờ mở); mật
khẩu không được ghi ở đâu cả, chỉ mã băm; đây là cổng phía trình duyệt nên
**không chặn được người có ý**, vì các tệp `data/*.geojson` vẫn tải thẳng được.
Chặn thật cần kiểm ở máy chủ, không làm được trên trang tĩnh. Tỉnh mới sao chép
dự án thì xuất dữ liệu bị khóa cho đến khi chạy script này.

### Môi trường Python

Môi trường conda tên `tainguyennuoc`, định nghĩa trong `environment.yml`.

```bash
conda env create -f environment.yml
```

Ba điều cần biết khi chạy script trên máy này:

1. **Gọi thẳng python của môi trường, không dùng `conda run`.** conda ở đây là bản
   4.10, `conda run -n tainguyennuoc` vẫn nạp `site-packages` của base và gây lỗi
   kiểu `module 'fiona' has no attribute 'path'`. Lấy đường dẫn đúng bằng
   `conda env list` rồi gọi trực tiếp, ví dụ
   `D:\Anaconda_Data\envs\tainguyennuoc\python.exe scripts/01_chuan_hoa_ranh_gioi.py`.
2. `conda env create` của bản 4.10 **không nhận cờ `--yes`**, truyền vào sẽ lỗi.
3. Với script chỉ dùng thư viện chuẩn, chạy `python -I -X utf8` để console Windows
   in được tiếng Việt. Dùng `-I` thì biến `PYTHONIOENCODING` bị bỏ qua, phải dùng
   `-X utf8`.

### Pipeline dữ liệu

Chạy theo thứ tự số. Script 00 và 03 chỉ cần thư viện chuẩn, còn lại cần GeoPandas.

```bash
python scripts/00_tao_du_lieu_mau.py          # sinh 8 lớp GeoJSON mô phỏng
python scripts/01_chuan_hoa_ranh_gioi.py      # ranh giới tỉnh
python scripts/02_chuan_hoa_ranh_gioi_xa.py   # 65 xã, VN-2000 UTM48 -> WGS84
python scripts/03_lay_realtime.py             # data/realtime.json + lịch sử
python scripts/04_tao_nen_dia_phuong.py       # cắt nền quốc gia theo tỉnh
python scripts/06_tao_ky_hieu.py              # .qml của QGIS -> assets/ky_hieu/*.svg
python scripts/08_xuat_lo_khoan_ndd.py        # data/quan_trac_ndd.geojson, từ QTQG
python scripts/09_chuan_hoa_ao_ho_khong_san_lap.py   # data/ao_ho_khong_san_lap.geojson
```

Script 04 nhận tên lớp làm tham số để chỉ làm lại một phần, ví dụ
`python scripts/04_tao_nen_dia_phuong.py DoanTimDuongBo`. Chạy toàn bộ script này
mất vài phút vì phải đọc geodatabase 473 MB.

Script 03 đọc biến môi trường `CHE_DO`: `mo_phong` (mặc định) hoặc `that`.

Script 06 cần bộ `.qml` ở `CSDL/symbol_QGIS/`; thiếu thư mục đó thì script in
thông báo rồi dừng, không ghi đè danh mục ký hiệu đang có.

Script 08 đứng riêng khỏi pipeline: nó **không đọc `CSDL/`** mà gọi thẳng cơ sở
dữ liệu QTQG qua `backend/nguon_qtqg.py`, nên cần `backend/.env` và tự đặt
`CHE_DO=that`. Nó cũng không dùng GeoPandas, vì câu SQL đã `ST_Transform` sẵn về
EPSG:4326 — nhờ vậy tránh luôn bẫy PROJ ở mục dưới.

Script 09 đọc `data_goc/ao_ho_khong_san_lap/*.csv`, là bản xuất tay của Google
Sheet đứng sau ứng dụng Apps Script "THÔNG TIN HỒ, AO, ĐẦM KHÔNG ĐƯỢC SAN LẤP"
của tỉnh. Nó tự tìm tệp `.csv` đầu tiên trong thư mục đó nên tên tệp đặt thế nào
cũng được.

**Vì sao phải xuất tay chứ không nối tự động.** Ứng dụng đó phơi 31 hàm máy chủ
nhưng tất cả gọi qua kênh RPC `google.script.run`, chỉ chạy được từ bên trong
trang; đường HTTP duy nhất là `doGet` và nó trả HTML, nội dung lại nằm trong
iframe sandbox khác origin. Ứng dụng còn có phân quyền và khóa tải về bằng mật
khẩu. Đừng mất công viết trình bóc HTML cho nó.

Ba chốt trong script 09, **đừng gỡ**:

1. **Dò tên cột theo tên ứng viên sau khi bỏ dấu**, không gắn cứng, và in ra
   bảng ánh xạ đã chọn cộng danh sách cột không nhận ra. Một cột ánh xạ nhầm
   vẫn cho ra số hợp lệ nên không nhìn thấy thì không bao giờ phát hiện.
2. **Tự nhận hệ tọa độ theo độ lớn, không tin khai báo.** Ứng dụng ghi nhãn là
   "Tọa độ WGS84" còn người dùng nhớ là VN-2000 X/Y. Độ lớn thì không nói dối:
   độ thập phân nằm trong ±180, mét thì hàng trăm nghìn. Thứ tự hai số cũng tự
   suy được vì ở Việt Nam kinh độ (102–118) và vĩ độ (8–24) không giao nhau,
   còn VN-2000 múi 3 độ thì tung độ (>1,2 triệu) luôn lớn hơn hoành độ (quanh
   500 nghìn). Nhờ vậy lộn X với Y cũng tự chữa được.
3. **Chỉ nạp pyproj khi thật sự phải chuyển hệ**, và gọi `sua_duong_dan_proj()`
   trước. CSV đã là WGS84 thì script chỉ cần thư viện chuẩn, né hẳn bẫy PROJ.

Bản ghi thiếu tọa độ và điểm nằm ngoài `khung_bao_nen` đều bị **bỏ khỏi tệp và
báo số lượng ra màn hình**, giống cách `backend/khong_gian.tap_feature()` làm
với `bo_ngoai_tinh`. Không dòng nào trong khung thì script dừng, không ghi đè.

### Bẫy PROJ, bắt buộc tuân thủ

Máy này có `PROJ_LIB` trỏ sang PostGIS và `PROJ_DATA` trỏ sang một env conda khác,
làm pyproj đọc nhầm `proj.db` cũ và báo lỗi `DATABASE.LAYOUT.VERSION.MINOR`.

Mọi script dùng GeoPandas **phải** gọi `sua_duong_dan_proj()` từ
`scripts/moi_truong_proj.py` **trước** khi `import geopandas`:

```python
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from moi_truong_proj import sua_duong_dan_proj
sua_duong_dan_proj()

import geopandas as gpd
```

## Kiến trúc

### Tham số của tỉnh

Mọi thứ gắn với địa phương nằm trong `tinh.json` ở gốc dự án, không nằm trong mã.
Tệp đó là **nguồn sự thật cho cả hai phía**: `scripts/tinh.py` đọc bằng
`json.load`, `assets/js/tinh.js` đọc bằng `fetch`. Không khai báo tham số tỉnh ở
hai nơi.

```
tinh.json    ma, ten_tinh, ten_ngan, ten_he_thong, don_vi, hop_thanh_tu,
             ban_do.{tam, zoom, pham_vi_dat_lien, pham_vi_toan_tinh},
             khung_bao_nen, epsg_chuyen_de, co_du_lieu_mo_phong,
             lop_co_san[], ten_tinh_trong_qtqg[], cong.{web, backend},
             dung_sai_nen{} (tùy chọn)
```

Ba quy tắc bắt buộc khi sửa mã:

1. **Không gắn cứng tên tỉnh, toạ độ hay đường dẫn `data/` vào mã.** Tên tỉnh
   hiển thị qua thuộc tính `data-tinh="<tên trường>"` trong HTML, `tinh.js` tự
   điền. Đường dẫn dữ liệu luôn qua `duong_dan_du_lieu(ten_tep)`.
2. **Trường `tep` trong `CAU_HINH.lop` chỉ ghi tên tệp**, không ghi `data/`.
3. **Lọc qua `lop_co_san(ma_lop)`** trước khi nạp hay dựng giao diện cho một lớp.
   Lớp nào chưa có dữ liệu thì khai báo thiếu trong `lop_co_san`, giao diện tự
   ẩn nhóm tương ứng; trang thống kê ẩn cả mục qua thuộc tính `data-can-lop`.

Ba bộ dữ liệu quốc gia tùy dự án mà nằm trong `CSDL/` hay `data_goc/`, nên script
dò vị trí qua `mod_tinh.tim_tep_nguon(...)` thay vì gắn cứng đường dẫn.

#### Tham số `?tinh=<ma>` trên mọi URL dữ liệu

`duong_dan_du_lieu()` trả về đường dẫn **đã kèm `?tinh=<ma>`**. Tham số đó không
để máy chủ làm gì cả, nó chỉ để **tách khóa cache của trình duyệt**.

Vì sao cần, đây là lỗi đã xảy ra thật: mỗi tỉnh là một dự án riêng, nhưng khi
chạy thử trên máy cá nhân thì mọi dự án đều dùng `http://localhost:8000` —
**cùng một origin**. Trình duyệt lấy URL làm khóa cache, nên
`data/ranh_gioi_tinh.geojson` của tỉnh này và của tỉnh khác là **cùng một khóa**.
Mở dự án B sau dự án A thì bản đồ vẽ ranh giới của A trong khi tiêu đề trang đã
là B. Rất khó đoán ra, vì mã nguồn không có gì sai và không có thông báo lỗi nào.

Hệ quả khi sửa mã:

- Hàm trả về chuỗi **đã có dấu `?`**, nên muốn thêm tham số phải dùng `&`, xem
  `nap_realtime()` trong `realtime.js`.
- `tinh.json` thì không đi qua hàm này (phải đọc nó mới biết mã tỉnh), nên nó
  dùng `?t=<timestamp>` kèm `cache: 'no-store'`. Tệp chỉ vài KB nên không sao.
- `ky_hieu.js` cũng kèm `?tinh=` cho danh mục và cho từng tệp SVG, cùng lý do.
- Trong cùng một tỉnh thì tệp vẫn được cache bình thường. Đừng đổi sang
  `?t=<timestamp>`: các tệp nền nặng vài MB, mất cache là mỗi lần mở trang tải
  lại hết.

### Luồng dữ liệu

```
data_goc/, CSDL/              dữ liệu gốc, trang web không bao giờ đọc trực tiếp
      |
      v  scripts/*.py, chuẩn hóa tên trường + ép về EPSG:4326
data/*.geojson                trang web chỉ đọc từ đây
data/realtime.json            số đo theo thời gian, do GitHub Actions ghi lại
data/nen/*.geojson            nền địa phương, tải trễ
      |
      v  fetch() trong trình duyệt, đường dẫn do duong_dan_du_lieu() ghép
index.html + pages/thong-ke.html + assets/js          [THUẦN TĨNH]


CSDL Quan trắc Quốc gia (PostgreSQL + PostGIS, toàn quốc)
      |
      v  backend/ đọc chỉ đọc, lọc về phạm vi tỉnh, chuẩn hóa, tính WQI
GET http://localhost:8001/api/quan-trac/...
      |
      v  fetch() trong api_quan_trac.js
pages/quan-trac.html                                   [ĐỘNG]

      và  scripts/08_xuat_lo_khoan_ndd.py gọi backend/nguon_qtqg.py như thư viện
      ->  data/quan_trac_ndd.geojson -> index.html     [TĨNH]
```

Quy tắc then chốt: **tên trường đầu ra của script phải khớp khai báo trong
`assets/js/config.js`**. Khi tên trường nguồn khác, sửa bảng ánh xạ trong script
(hoặc `BANG_ANH_XA` trong `backend/chuan_hoa.py`) chứ không sửa giao diện.

### Backend trung gian QTQG

`backend/` là dịch vụ FastAPI đứng giữa cơ sở dữ liệu phần mềm Quan trắc Quốc gia
(PostgreSQL) và tab Quan trắc. Đây là **thành phần duy nhất của dự án không phải
tĩnh**; `index.html` và `pages/thong-ke.html` vẫn chạy thuần tĩnh như cũ và
**không được nạp `api_quan_trac.js`**.

Vì sao không cho trình duyệt gọi thẳng cơ sở dữ liệu: thông tin đăng nhập không
được ra đến trình duyệt; cơ sở dữ liệu QTQG là của cả nước nên phải lọc về phạm
vi tỉnh rồi đổi thành GeoJSON; và bộ nhớ đệm 60 giây bảo vệ một hệ thống đang
chạy thật khỏi lượt gọi lặp.

Quyết định then chốt: `GET /api/quan-trac/so-do` trả về **đúng schema của
`data/realtime.json`**. Nhờ vậy `lay_realtime()`, `kieu_ve(p, rt)` và
`CAU_HINH.truong_realtime` dùng lại nguyên vẹn, không phải viết lại phần hiển
thị số đo. Sửa cấu trúc một trong hai thì phải sửa cả hai.

**Ba ranh giới không được phá:**

1. **`backend/nguon_qtqg.py` là lớp duy nhất biết schema QTQG.** Đổi nguồn chỉ
   sửa tệp đó cộng `backend/truy_van.sql` (16 câu SELECT, chia khối bằng chú
   thích `-- @ten:`).
2. **Mọi kết nối tới QTQG là chỉ đọc**, khóa cứng bằng
   `default_transaction_read_only=on` trong `ket_noi.py`, kèm `statement_timeout`
   15 giây và danh sách từ khóa ghi bị cấm. Có test hồi quy quét văn bản toàn bộ
   `backend/` để chặn câu lệnh ghi lọt vào.
3. **Thông tin đăng nhập chỉ nằm trong `backend/.env`** (đã gitignore, và
   `.gitignore` được đặt trước khi tạo tệp đó). Không bao giờ đưa vào mã nguồn,
   test, README hay thân lỗi trả về trình duyệt. `cau_hinh.py` là nơi **duy
   nhất** đọc `os.environ`.

**Không đặt dịch vụ này ra Internet công khai.** Nó giữ thông tin kết nối vào một
cơ sở dữ liệu ngành đang vận hành. Nếu buộc phải mở ra ngoài thì đặt sau reverse
proxy có HTTPS và hạn chế theo địa chỉ IP. `deploy-pages.yml` cố ý **không** đóng
gói `backend/`.

Khi lên máy chủ tỉnh: thêm tên miền thật vào `CORS_NGUON` trong `backend/.env`,
và sửa **đúng một dòng** `CAU_HINH.api.goc` trong `assets/js/config.js`.

**Tab Quan trắc có cả nước dưới đất.** Phạm vi kiểm kê của trang (các lớp trong
`data/`) vẫn chỉ là nước mặt, nhưng tab Quan trắc hiển thị thêm các lỗ khoan quan
trắc quốc gia đang hoạt động trong tỉnh, đọc từ bảng `monitoring_well` của QTQG.
Bốn điều phải nhớ khi đụng vào nhánh này:

1. **`h_ngam_m` không được gộp với `h_m`.** Nước mặt là cao độ mặt nước theo mốc
   của trạm (số dương, nguồn ghi bằng centimet nên SQL chia 100); nước dưới đất
   là độ sâu mặt nước dưới miệng lỗ khoan (số **âm**, nguồn ghi bằng mét).
2. **Không tính WQI cho nước dưới đất.** QĐ 1460/QĐ-TCMT là chỉ số nước **mặt**
   lục địa; ngưỡng nước dưới đất theo QCVN 09-MT:2015/BTNMT. `wqi.gan_wqi()`
   thoát sớm khi `loai == "nuoc_duoi_dat"`.
3. **Không có ngưỡng cảnh báo.** Hai cột `hcp` và `h_chophep` rỗng, nên lỗ khoan
   không bao giờ mang `trang_thai`. Đừng tự nghĩ ra ngưỡng.
4. **Cách lấy dòng mới nhất khác nhau theo bảng**, vì `statement_timeout` là 15
   giây. `water_level` dùng `CROSS JOIN LATERAL`, `water_temperature` dùng
   `DISTINCT ON` cộng cửa sổ 730 ngày và một câu bù. Đổi cách viết là đụng trần.

**Lớp quan trắc địa phương không trộn vào tab Quan trắc.**
`data/quan_trac.geojson` còn là dữ liệu mô phỏng, nên `HOP_TRAM_DIA_PHUONG=0`:
tab chỉ hiện trạm QTQG thật. Cơ chế hợp danh sách vẫn còn nguyên trong
`khong_gian.hop_danh_sach_tram()`, bật lại bằng biến môi trường khi tỉnh có lớp
quan trắc địa phương thật.

### Tách hình học khỏi số đo thời gian

Vị trí hồ, trạm, công trình nằm trong GeoJSON tĩnh. Số đo theo thời gian nằm riêng
trong `data/realtime.json`, ghép với hình học qua trường `ma`. Đây là lý do đổi từ
dữ liệu mô phỏng sang nguồn quan trắc thật chỉ phải sửa hàm
`doc_tu_nguon_that()` trong `scripts/03_lay_realtime.py`, không đụng gì đến bản đồ.

### Ba trang, dùng chung bảng màu

`index.html` là trang bản đồ. `pages/thong-ke.html` là trang thống kê,
`pages/quan-trac.html` là tab Quan trắc. Cả hai trang con nạp lại `style.css`
rồi chồng thêm `thong-ke.css` (trang quan trắc chồng thêm `quan-trac.css`), nên
mọi biến màu và lớp tiện ích như `.the-so`, `.nut`, `.bang-tt` đều dùng chung.
Đổi bảng màu ở `style.css` là cả ba trang cùng đổi. Trang thống kê chỉ cần
`config.js`, `tinh.js`, `dung_chung.js`, `xuat_tep.js` và `thong-ke.js`, không
nạp bộ mã của bản đồ.

`assets/js/dung_chung.js` giữ bốn hàm mà cả ba trang đều cần nhưng nằm ngoài bộ
mã của bản đồ: `the_so()`, `dinh_dang_thoi_diem()`, `mo_hop_thoai()`,
`dong_hop_thoai()`. Trước kia chúng nằm trong `realtime.js` và `app.js`, là hai
tệp gắn chặt với `LOP` và `ban_do`. **Không định nghĩa lại chúng ở nơi khác.**

Hàm xuất tệp nằm riêng ở `xuat_tep.js` để quy ước CSV chỉ định nghĩa một chỗ.
`tai_ve_tep()` gọi `hien_mach_bao()` có kiểm tra tồn tại, vì hàm đó chỉ có ở
trang bản đồ.

### JavaScript

Không có bundler. Các tệp nạp tuần tự bằng thẻ `<script>` ở cuối `index.html` và
**thứ tự này quan trọng**, vì chúng giao tiếp qua biến toàn cục:

```
config.js     -> CAU_HINH, MAU, DINH_DANG, dinh_dang_gia_tri(), so_ngay_den(), bo_dau()
tinh.js       -> TINH, nap_tinh(), duong_dan_du_lieu(), lop_co_san()
dung_chung.js -> the_so(), dinh_dang_thoi_diem(), mo_hop_thoai(), dong_hop_thoai()
ky_hieu.js    -> DANH_MUC_KY_HIEU, nap_danh_muc_ky_hieu(), tao_diem_co_ky_hieu()
map.js        -> ban_do (Leaflet Map), nhom_ve_phu, NEN_VECTOR, các công cụ bản đồ
layers.js     -> LOP (kho dữ liệu chính), CHI_MUC_TIM, BO_LOC, ve_lop(), qua_bo_loc()
identify.js   -> KET_QUA_TRUNG, truy_van_tai_diem(), hien_chi_tiet()
table.js      -> BANG, tai_ve_csv(), ve_lai_bang()
realtime.js   -> DU_LIEU_RT, lay_realtime()
xuat_tep.js   -> tai_ve_csv(), tai_ve_tep()
app.js        -> khởi động, gắn sự kiện, hộp thoại
```

`pages/quan-trac.html` nạp bộ khác, **không** có `map.js`, `layers.js`,
`identify.js`, `table.js`, `realtime.js`, `app.js`:

```
config.js, tinh.js, dung_chung.js, ky_hieu.js, xuat_tep.js,
api_quan_trac.js -> API_QT, kiem_tra_suc_khoe(), nap_tram_qtqg(), lay_so_do()
quan_trac.js     -> khởi động trang, bản đồ nhỏ, biểu đồ, bảng
```

`lay_so_do(ma)` trong `api_quan_trac.js` có **cùng chữ ký** với `lay_realtime(ma)`
trong `realtime.js`, nên các hàm vẽ ký hiệu và bảng chi tiết dùng được cho cả hai
nguồn. Giữ nguyên điều này.

`app.js` gọi `nap_tinh()` trước rồi mới `khoi_tao_ban_do()`, vì tâm bản đồ, phạm
vi và danh sách lớp đều lấy từ tham số tỉnh. Mỗi trang khai báo `GOC_TRANG` trước
khi nạp `tinh.js`: `''` ở `index.html`, `'../'` ở hai trang trong `pages/`.

`LOP` là kho trung tâm: `LOP[ma_lop] = { dn, doi_tuong[], nhom, hien, loi }`, trong
đó `doi_tuong[i] = { ma_lop, chi_so, thuoc_tinh, hinh_hoc, hinh }`.

### config.js là nguồn sự thật duy nhất về lớp dữ liệu

Thêm một lớp chuyên đề mới chỉ cần hai việc: thêm một khối vào `CAU_HINH.lop` và
đưa mã lớp vào một nhóm trong `CAU_HINH.nhom_lop`. Cây lớp, chú giải, bảng thuộc
tính, bộ lọc, tìm kiếm và xuất CSV đều tự sinh từ khai báo đó. Mỗi lớp khai báo
`tep`, `kieu`, `z`, `khoa`, `truong_nhan`, hàm `kieu_ve(props, rt)`, danh sách
`truong` kèm đơn vị và định dạng, `cot_bang`, `chu_giai`.

### Truy vấn bằng nhấp chuột

`identify.js` **không** dùng sự kiện click của Leaflet, mà tự kiểm tra hình học của
mọi đối tượng đang hiển thị. Lý do: SVG chỉ bắt được hình nằm trên cùng, trong khi
yêu cầu của dự án là một điểm nhấp trúng nhiều đối tượng phải liệt kê được tất cả
trong danh sách thả xuống.

Quy tắc trúng, khác nhau theo loại hình học và đã được cân nhắc, đừng đổi tùy tiện:

- **Điểm**: dung sai pixel, tối thiểu bằng bán kính ký hiệu cộng 4.
- **Đường**: dung sai pixel cộng nửa độ dày nét.
- **Vùng**: chỉ tính khi điểm nhấp nằm **bên trong**. Không dùng dung sai pixel, vì
  ở mức zoom xa 10 pixel tương đương vài km, khiến một cú nhấp trúng đường biên của
  hàng loạt xã lân cận và danh sách đầy đối tượng người dùng không nhắm tới.

Kết quả sắp theo `uu_tien` (điểm 1, đường 2, vùng 3) rồi theo khoảng cách.

### Pane và thứ tự vẽ của Leaflet

- `pane-nen-<ma>`: z 205 đến 245, các lớp nền địa phương
- `pane-<ma_lop>`: z 400 đến 480, lớp chuyên đề, lấy từ `CAU_HINH.lop[ma].z`
  (`quan_trac` 480, `quan_trac_ndd` 478)
- `pane-nhan`: z 620, nhãn tên đối tượng, `pointer-events: none`

Bản đồ đặt `zoomSnap: 0.25` vì tỉnh kéo dài theo chiều bắc nam trong khi khung bản
đồ rộng và thấp; nếu chỉ dùng mức zoom nguyên thì `fitBounds` phải lùi ra một mức
và để lại nhiều khoảng trống.

Bản đồ đặt `preferCanvas: true`. Vẽ hàng trăm polygon xã bằng SVG làm trình duyệt
đứng hình mỗi lần vẽ lại; canvas không tạo phần tử DOM cho từng đối tượng nên
nhanh hơn hẳn. Đổi được vì hệ thống không dựa vào sự kiện click của SVG:
`identify.js` tự kiểm tra hình học.

### Bản đồ nền

`CAU_HINH.ban_do_nen` có hai loại. Loại tile gọi dịch vụ ngoài. Loại `kieu: 'vector'`
(mã `dia_phuong`) dựng từ `data/nen/*.geojson` theo khai báo `CAU_HINH.nen_vector`,
chỉ tải khi người dùng chọn rồi giữ trong `NEN_VECTOR` để lần sau bật lại là hiện ngay.

Hai điểm đã gặp khi chọn nguồn tile: CARTO basemaps nay yêu cầu API key và hiện chữ
chìm "API KEY REQUIRED"; tile canvas của Esri chỉ có tới zoom 16 nên phải đặt
`maxNativeZoom` để Leaflet phóng to tile sẵn có thay vì để trống.

### GitHub Actions

- `update-realtime.yml`: cron mỗi giờ, chạy script 03, tự commit `data/realtime.json`
  và `data/history/`. Đây là cơ chế "thời gian thực" trên một trang tĩnh.
  Vẫn để `CHE_DO: mo_phong`: workflow chạy trên runner của GitHub, **không với
  tới được CSDL QTQG của ngành**. Số thật đi qua `backend/`, ở tab Quan trắc.
- `deploy-pages.yml`: chỉ đóng gói `index.html`, `assets/`, `data/`, `pages/` và
  `tinh.json` vào `_site`. `CSDL/` và `data_goc/` cố ý không được xuất bản vì rất
  nặng; `backend/` cố ý không được xuất bản vì nó giữ thông tin kết nối vào một
  cơ sở dữ liệu ngành đang vận hành.

## Tình trạng dữ liệu

Phải nắm rõ trước khi sửa bất cứ thứ gì liên quan đến số liệu.

| Lớp | Trạng thái |
|---|---|
| `ranh_gioi_tinh`, `ranh_gioi_xa`, `data/nen/*` | Dữ liệu thật |
| Sông suối, ao hồ, hồ chứa, lưu vực, khai thác, xả thải, quan trắc, sức chịu tải | **Mô phỏng** |
| `data/realtime.json` | **Mô phỏng** |
| Tab Quan trắc ở `CHE_DO=that` | Dữ liệu thật, từ CSDL QTQG |
| Tab Quan trắc ở `CHE_DO=thu_nghiem` | **Thử nghiệm**, sinh từ vị trí trạm |
| `data/quan_trac_ndd.geojson`, 28 lỗ khoan | Dữ liệu thật, đã sinh 27/10/2026 |
| `data/ao_ho_khong_san_lap.geojson` | Dữ liệu thật, danh mục tỉnh công bố. **Chưa sinh**, chờ bản xuất CSV |

Dữ liệu mô phỏng do `scripts/00_tao_du_lieu_mau.py` sinh ra, mỗi đối tượng mang
trường `nguon_dl` ghi rõ điều đó, và `index.html` có dải cảnh báo ở đầu trang.
**Không gỡ dải cảnh báo đó chừng nào các lớp chuyên đề còn là dữ liệu mô phỏng.**

### Lớp lỗ khoan nước dưới đất đã nạp

`scripts/08_xuat_lo_khoan_ndd.py` đã chạy với CSDL QTQG thật ngày 27/10/2026 và
sinh `data/quan_trac_ndd.geojson`: **28 lỗ khoan** `hientrang = 'Đang hoạt động'`
trong địa giới Khánh Hòa sau sáp nhập, cả 28 đều có cả mực nước và kết quả phân
tích. Mã dạng `QT*-KH`. Tầng chứa nước: qh 12, qp 10, j 4, q 1, n 1.

Bộ lọc `ten_tinh_trong_qtqg` chạy đúng: danh sách xã trải cả hai tỉnh cũ, từ Tu
Bông, Vạn Ninh, Diên Khánh, Cam Lâm, Khánh Vĩnh (Khánh Hòa cũ) đến Mỹ Sơn, Bảo
An, Phước Hậu, Phước Dinh, Thuận Bắc (Ninh Thuận cũ).

**Chạy lại script 08 thì phải đồng bộ hai nơi.** `quan_trac_ndd` chỉ được có
trong `lop_co_san` của `tinh.json` khi `data/quan_trac_ndd.geojson` tồn tại:
đăng ký mà thiếu tệp thì mỗi lần mở trang là một lỗi 404 trong console, còn có
tệp mà không đăng ký thì lớp không bao giờ được nạp.
`backend/tests/test_nuoc_duoi_dat.py` chốt ràng buộc hai chiều đó.

**Ràng buộc đó áp dụng cho mọi lớp sinh bằng script**, kể cả
`ao_ho_khong_san_lap` của script 09: khai báo trong `config.js` thì cứ khai báo
trước cũng không sao (không có trong `lop_co_san` thì lớp chỉ không được nạp),
nhưng **đưa vào `lop_co_san` thì tệp GeoJSON phải có thật**.

Số đo trong lớp này là số **tại thời điểm xuất**, ghi ở `thoi_diem_xuat` cấp
FeatureCollection và trong `nguon_dl` của từng đối tượng. Muốn số mới nhất thì
xem tab Quan trắc. Lớp này **không mang trường `wqi`** và `h_ngam_m` là số **âm**
(độ sâu mặt nước dưới miệng lỗ khoan), hiện dao động từ −0,7 đến −18,01 m.

### QTQG thực tế phủ đến đâu

Khảo sát 27/10/2026, `CHE_DO=that`, `csdl_ket_noi = true`. Tab Quan trắc có
**34 công trình**, trong đó 29 ghép được số đo:

| Nhóm | Số lượng | Số đo |
|---|---|---|
| Trạm nước mặt (`surfacewater_station`) | 1 | `NP01` Trạm Nha Phu, mới nhất **31/12/2017** |
| Trạm thủy văn (`hydrology_station`) | 5 | Không có, chỉ có vị trí |
| Lỗ khoan (`monitoring_well`, đang hoạt động) | 28 | Đủ cả mực nước và phân tích, 06/10/2026 |

### Ẩn bản ghi số đo quá cũ

Số của NP01 là của 31/12/2017 còn số của lỗ khoan là của 06/10/2026 — hai mốc
cách nhau gần 9 năm mà nằm chung một bản đồ. Cột "Thời điểm đo" có ghi rõ, nhưng
người xem quét nhanh chỉ thấy huy hiệu xanh "Bình thường" và WQI 89. Đây đúng là
tình huống dự án đã tránh ở nhánh nước dưới đất bằng cách chỉ lấy lỗ khoan đang
hoạt động.

Theo quyết định của chủ đầu tư, backend **ẩn bản ghi số đo cũ hơn 2 năm**
(`SO_DO_CU_TOI_DA_NGAY=730`, đặt `0` để tắt).

**Ẩn là ẩn BẢN GHI SỐ ĐO, không phải công trình.** NP01 vẫn nằm trong
`/api/quan-trac/tram.geojson` (34 công trình, không đổi), vẫn hiện trên bản đồ,
trong bảng và ở ô chọn trạm — chỉ là không có số đo đi kèm, giống 5 trạm thủy
văn vốn không có số đo. Không xóa một công trình thật khỏi danh mục kiểm kê.

Phép lọc ở `tong_hop.tach_ban_ghi_qua_cu()`, gọi từ hai nơi dùng chung một quy
tắc: endpoint `/api/quan-trac/so-do` trong `main.py`, và
`scripts/08_xuat_lo_khoan_ndd.py`. Lọc **sau** bộ nhớ đệm chứ không trong đó, để
bộ đệm giữ dữ liệu thô.

Bốn điều **đừng sửa** khi đụng vào phép lọc này:

1. **Bản ghi không đọc được `thoi_diem` thì giữ lại.** Không biết tuổi thì không
   được đoán là cũ rồi bỏ đi.
2. **Chỉ xét `thoi_diem`**, không xét `thoi_diem_chat_luong` riêng. Nước dưới
   đất lấy mẫu hóa học vài lần một năm nên mốc đó cách mốc mực nước nhiều tháng;
   xét riêng sẽ bỏ cả lỗ khoan đang đo hàng ngày.
3. **Đã ẩn thì phải nói rõ.** Gói dữ liệu mang khóa `so_do_cu`, và tab Quan trắc
   hiện dải thông báo kèm tên công trình, thời điểm đo, cộng một thẻ chỉ tiêu.
4. **`/api/quan-trac/chuoi` cố ý không lọc.** Chuỗi của NP01 (59 kỳ WQI
   2013-2017, 2.315 mốc mực nước từ 2011) vẫn vẽ được; biểu đồ có trục ngày nên
   tự nói lên số liệu dừng ở năm nào.
5. **Ẩn giá trị nhưng vẫn gửi TÊN thông số.** Mỗi mục trong
   `so_do_cu.cong_trinh` mang thêm `thong_so[]`, là tên các trường số học của
   bản ghi bị ẩn, do `tong_hop.thong_so_so_hoc()` dựng.

Điều 5 không phải để trang trí, thiếu nó là điều 4 thành vô nghĩa trên giao
diện. Ô chọn thông số của tab Quan trắc dựng từ bản ghi số đo hiện hành
(`thong_so_ve_duoc()` trong `assets/js/quan_trac.js`); bản ghi bị ẩn thì ô đó
rỗng và hiện "Không có thông số số học", nên tuy endpoint không lọc nhưng
người dùng **không còn đường nào bấm tới chuỗi**. Lỗi này đã xảy ra thật và
được phát hiện khi kiểm trang, không phải khi chạy test.

Hai điều kèm theo khi đụng vào nhánh này:

- **Loại `bool` ra khỏi danh sách thông số.** Trong Python `bool` là kiểu con
  của `int`, không loại thì `wqi_tu_tinh=True` bị kể là một thông số vẽ được
  biểu đồ, và ô chọn hiện một mục bấm vào chỉ ra biểu đồ rỗng.
- **Trạm chưa bao giờ có số đo thì không nằm trong `so_do_cu`.** Nhờ vậy giao
  diện phân biệt được hai trường hợp: 5 trạm thủy văn vẫn hiện "Trạm này chưa
  có thông số nào vẽ được biểu đồ", còn NP01 thì vẽ được kèm câu nói rõ đây là
  chuỗi lịch sử.

`backend/tests/test_so_do_cu.py` chốt lại toàn bộ hành vi trên.

### Việc còn lại

**Bắt buộc trước khi coi là xong:** đối chiếu NP01 và vài lỗ khoan với số liệu
đọc trực tiếp trên phần mềm QTQG. Đó là cách duy nhất phát hiện ánh xạ cột sai,
vì một cột ánh xạ nhầm vẫn trả về số hợp lệ.

Bộ ký hiệu trong `assets/ky_hieu/` được sao sẵn ở dạng SVG. Muốn sinh lại thì cần
bộ `.qml` của QGIS đặt ở `CSDL/symbol_QGIS/` rồi chạy `scripts/06_tao_ky_hieu.py`;
thiếu thư mục đó thì script in thông báo và không ghi đè danh mục đang có.

Bộ kiểm kê thật ở `CSDL/SD_TLTT_DTHT_XA_THAI` (MapInfo TAB) hiện **chưa được nạp**
vì mới có phạm vi Khánh Hòa cũ, thiếu Ninh Thuận cũ. Người dùng sẽ lọc các lớp cần
dùng vào `data_goc/` khi có đủ; khi đó mới viết `05_chuan_hoa_chuyen_de.py`.

## Hệ quy chiếu của các nguồn dữ liệu

| Nguồn | EPSG |
|---|---|
| `CSDL/Vietnam/VietNam.shp` | 4326, không cần chuyển |
| `data_goc/VN2000_UTM48/Commune.shp` | 3405, VN-2000 / UTM 48N |
| `data_goc/Basemap/BaseMapVietNam.gdb` | 32648 |
| `CSDL/SD_TLTT_DTHT_XA_THAI/*.TAB` | **9217**, VN-2000 / TM-3 108-15 |

Tệp `.TAB` khai báo datum là `WGS_1984` chứ không phải VN-2000, nên phải
`set_crs(9217, allow_override=True)` để pyproj dùng đúng phép chuyển datum. Tên
trường tiếng Việt trong các tệp này đọc ra bị lỗi phông.

Ranh giới tỉnh bao gồm huyện đảo Trường Sa nên kinh độ mở rộng tới khoảng 117,4°Đ.
Vì vậy `CAU_HINH.ban_do.pham_vi_dat_lien` được tách riêng khỏi `pham_vi_toan_tinh`,
và nút "về toàn tỉnh" dùng phạm vi đất liền.

## Quy ước viết mã

- Tên hàm, tên biến và chú thích bằng tiếng Việt.
- Chú thích trong mã nguồn Python và JavaScript viết **không dấu**; chuỗi hiển thị
  cho người dùng và dữ liệu thì viết **có dấu** đầy đủ.
- JavaScript viết theo kiểu ES5: `var`, `function`, không dùng module. Trang chạy
  trực tiếp không qua biên dịch nên không dùng cú pháp cần transpile.
- CSV xuất ra có BOM UTF-8, phân cách bằng dấu phẩy, mọi ô đều bọc ngoặc kép, để
  vừa mở đúng trong Excel tiếng Việt vừa đọc được bằng pandas, GeoPandas và QGIS.
