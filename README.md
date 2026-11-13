# WebGIS Tài nguyên nước Khánh Hòa

Hệ thống bản đồ trực tuyến phục vụ kiểm kê, giám sát và hỗ trợ ra quyết định về
tài nguyên nước mặt tỉnh Khánh Hòa (sau sáp nhập với Ninh Thuận, hiệu lực từ
01/07/2025).

Bản đồ và trang thống kê là trang tĩnh, chạy được trên GitHub Pages mà không cần
máy chủ riêng. Riêng tab **Quan trắc** lấy số liệu trực tiếp từ cơ sở dữ liệu
phần mềm Quan trắc Quốc gia nên cần một dịch vụ trung gian (`backend/`) chạy
trong mạng của tỉnh; tắt dịch vụ đó thì bản đồ vẫn hoạt động đầy đủ.

---

## Tham số của tỉnh

Mọi thứ gắn với địa phương nằm trong một tệp duy nhất ở gốc dự án: `tinh.json`.
Tệp này là **nguồn sự thật cho cả hai phía** — `scripts/tinh.py` đọc bằng
`json.load`, `assets/js/tinh.js` đọc bằng `fetch` — nên không bao giờ lệch giữa
Python và trình duyệt.

```json
{
  "ma": "khanh-hoa",
  "ten_tinh": "Tỉnh Khánh Hòa",
  "ten_he_thong": "Tài nguyên nước Khánh Hòa",
  "don_vi": "Sở Nông nghiệp và Môi trường tỉnh Khánh Hòa",
  "ban_do": { "tam": [...], "zoom": 9, "pham_vi_dat_lien": [...] },
  "khung_bao_nen": [...],
  "epsg_chuyen_de": 9217,
  "co_du_lieu_mo_phong": true,
  "lop_co_san": [...]
}
```

Đổi tên đơn vị chủ quản, dời tâm bản đồ hay khai báo thêm lớp mới đều chỉ sửa ở
đây, không đụng vào mã. Tên tỉnh hiển thị trên giao diện qua thuộc tính
`data-tinh="<tên trường>"` trong HTML, `tinh.js` tự điền.

Mỗi dự án phục vụ đúng một tỉnh. Muốn làm tỉnh khác thì tạo một bản sao của dự án
rồi sửa `tinh.json`, không thêm tỉnh vào đây. Dự án Gia Lai đặt tại
`E:\DuAnAI\GIALAI` theo đúng cách đó.

---

## Tình trạng dữ liệu

Đây là điều cần đọc trước tiên.

| Lớp | Nguồn | Trạng thái |
|---|---|---|
| Ranh giới tỉnh | `CSDL/KhanhHoa/KhanhHoa.shp` | **Dữ liệu thật** |
| Ranh giới 65 xã, phường | `data_goc/VN2000_UTM48/Commune.shp` | **Dữ liệu thật** |
| Nền địa phương (rừng, mặt nước, đường bộ, địa danh) | `data_goc/Basemap/BaseMapVietNam.gdb` | **Dữ liệu thật** |
| Lưu vực, sông suối, ao hồ, hồ chứa | Sinh bằng `scripts/00_tao_du_lieu_mau.py` | Mô phỏng |
| Khai thác, xả thải, quan trắc, sức chịu tải | Sinh bằng `scripts/00_tao_du_lieu_mau.py` | Mô phỏng |
| Số liệu quan trắc thời gian thực (bản đồ chính) | Sinh bằng `scripts/03_lay_realtime.py` | Mô phỏng |
| Tab Quan trắc | CSDL phần mềm Quan trắc Quốc gia, qua `backend/` | **Dữ liệu thật** khi `CHE_DO=that` |
| Lỗ khoan quan trắc nước dưới đất (28 lỗ khoan) | CSDL QTQG, qua `scripts/08_xuat_lo_khoan_ndd.py` | **Dữ liệu thật** |
| Hồ, ao, đầm không được san lấp | Danh mục tỉnh công bố, qua `scripts/09_chuan_hoa_ao_ho_khong_san_lap.py` | **Dữ liệu thật**, chờ bản xuất CSV |

Các lớp mô phỏng dùng để kiểm thử giao diện trước khi có dữ liệu kiểm kê chính
thức. Mọi đối tượng mô phỏng đều mang trường `nguon_dl` ghi rõ điều đó. Vị trí
hình học chỉ gần đúng.

Số liệu trên **tab Quan trắc** thì khác: nó không đi qua `data/`, mà lấy trực
tiếp từ cơ sở dữ liệu phần mềm Quan trắc Quốc gia qua một backend trung gian.
Khi backend chạy ở `CHE_DO=thu_nghiem` (mặc định, không cần kết nối) thì trang
tự gắn nhãn vàng "dữ liệu thử nghiệm"; chỉ `CHE_DO=that` mới là số liệu thật.

---

## Chạy thử trên máy

Trình duyệt chặn việc đọc tệp GeoJSON qua đường dẫn `file://`, nên cần một máy
chủ web cục bộ:

```bash
cd E:\DuAnAI\KHANHHOA
python scripts/chay_web.py
```

Rồi mở <http://localhost:8000>. Trang web tự phát hiện và hướng dẫn nếu bạn mở
nhầm bằng cách nhấp đúp vào `index.html`.

Bản đồ và trang thống kê chạy được ngay như vậy. Riêng **tab Quan trắc** cần
thêm backend trung gian, chạy ở một cửa sổ khác:

```bash
cd E:\DuAnAI\KHANHHOA\backend
copy .env.mau .env
D:\Anaconda_Data\envs\tainguyennuoc\python.exe main.py
```

Rồi mở <http://localhost:8000/pages/quan-trac.html>. Tài liệu API tự sinh ở
<http://localhost:8001/docs>. Không chạy backend thì tab đó hiện thông báo kèm
đúng lệnh cần chạy, chứ không vỡ trang; bản đồ chính không bị ảnh hưởng gì.

### Mỗi tỉnh một cặp cổng riêng

| Tỉnh | Trang web | Backend |
|---|---|---|
| Khánh Hòa (dự án này) | **8000** | **8001** |
| Gia Lai | 8010 | 8011 |

Hai số này nằm ở `cong.web` và `cong.backend` trong `tinh.json`, không gắn cứng
ở đâu khác. Cổng backend luôn là cổng web cộng 1.

Vì sao phải tách: mọi dự án đều chạy trên `localhost` nên nếu dùng chung cổng
thì chung một origin, và trình duyệt lấy URL làm khóa cache. Mở tỉnh này sau
tỉnh kia thì bản đồ có thể vẽ ranh giới của tỉnh trước trong khi tiêu đề trang
đã đúng — lỗi đã xảy ra thật và rất khó đoán, vì mã nguồn không có gì sai.

Hai lệnh ở trên đều **tự đọc cổng từ `tinh.json`**, nên không phải gõ số và
không gõ sai được. `scripts/chay_web.py` còn từ chối chạy nếu cổng đã có người
dùng — cũng là một lỗi đã gặp: Python cho nhiều tiến trình `http.server` cùng
nghe một cổng, mỗi tiến trình phục vụ một thư mục khác nhau.

---

## Môi trường xử lý dữ liệu

```bash
conda env create -f environment.yml
conda activate tainguyennuoc
```

Môi trường tên `tainguyennuoc`, gồm GeoPandas, Pandas, Shapely, pyproj, pyogrio.

### Lưu ý về PROJ

Trên máy đã cài sẵn PostGIS hoặc nhiều môi trường conda, biến môi trường
`PROJ_LIB` / `PROJ_DATA` thường còn trỏ sang thư mục `proj` của bản cài khác,
khiến pyproj đọc nhầm `proj.db` cũ và báo lỗi:

```
proj.db contains DATABASE.LAYOUT.VERSION.MINOR = 6 whereas a number >= 7 is expected.
```

Mô-đun `scripts/moi_truong_proj.py` xử lý việc này: nó trỏ hai biến đó về đúng
thư mục `proj` của môi trường đang chạy. Mọi script dùng GeoPandas cần gọi
`sua_duong_dan_proj()` **trước** khi `import geopandas`.

---

## Các script

| Script | Việc | Cần GeoPandas |
|---|---|---|
| `tinh.py` | Mô-đun nạp `tinh.json`, mọi script khác đều dùng | Không |
| `moi_truong_proj.py` | Mô-đun sửa đường dẫn PROJ | Không |
| `00_tao_du_lieu_mau.py` | Sinh 8 lớp GeoJSON mô phỏng | Không |
| `01_chuan_hoa_ranh_gioi.py` | Lọc ranh giới tỉnh từ `VietNam.shp` | Có |
| `02_chuan_hoa_ranh_gioi_xa.py` | Lọc ranh giới xã, VN-2000 → WGS84 | Có |
| `03_lay_realtime.py` | Sinh `realtime.json` và ghi lịch sử | Không |
| `04_tao_nen_dia_phuong.py` | Cắt nền quốc gia theo khung bao của tỉnh | Có |
| `06_tao_ky_hieu.py` | Đổi `.qml` của QGIS thành SVG dùng được trên web | Không |
| `08_xuat_lo_khoan_ndd.py` | Xuất lỗ khoan nước dưới đất từ CSDL QTQG | Không |
| `09_chuan_hoa_ao_ho_khong_san_lap.py` | Đổi danh mục hồ ao đầm không được san lấp từ CSV thành GeoJSON | Chỉ khi nguồn là VN-2000 |
| `chay_web.py` | Máy chủ web cục bộ, đúng thư mục và đúng cổng của tỉnh | Không |

Chạy đầy đủ một lượt:

```bash
python scripts/00_tao_du_lieu_mau.py
python scripts/01_chuan_hoa_ranh_gioi.py
python scripts/02_chuan_hoa_ranh_gioi_xa.py
python scripts/03_lay_realtime.py
python scripts/04_tao_nen_dia_phuong.py
```

Ba script cuối đứng ngoài lượt chạy đó vì có điều kiện riêng:

- `06_tao_ky_hieu.py` cần bộ `.qml` ở `CSDL/symbol_QGIS/`. Bộ ký hiệu SVG trong
  `assets/ky_hieu/` đã có sẵn; script này chỉ dùng khi muốn sinh lại.
- `08_xuat_lo_khoan_ndd.py` cần `backend/.env` đã điền thông tin kết nối QTQG.
  Nó gọi `backend/nguon_qtqg.py` như một thư viện, không đọc `CSDL/`.
- `09_chuan_hoa_ao_ho_khong_san_lap.py` cần một tệp `.csv` trong
  `data_goc/ao_ho_khong_san_lap/`, là bản xuất tay của bảng dữ liệu danh mục hồ
  ao đầm không được san lấp. Script tự dò tên cột, tự nhận hệ tọa độ (WGS84 hay
  VN-2000 X/Y) theo độ lớn con số, và chỉ cần pyproj khi thật sự phải chuyển hệ.

`04_tao_nen_dia_phuong.py` nhận thêm tên lớp để chỉ làm lại một phần, ví dụ
`python scripts/04_tao_nen_dia_phuong.py Rung`.

Ba bộ dữ liệu quốc gia (`VietNam.shp`, `Commune.shp`, `BaseMapVietNam.gdb`) tùy
dự án mà nằm trong `CSDL/` hay `data_goc/`. Script tự dò cả hai vị trí nên không
phải sửa đường dẫn khi chuyển dự án.

`01_chuan_hoa_ranh_gioi.py` giảm shapefile 2,12 MB xuống GeoJSON 0,50 MB bằng
cách đơn giản hóa hình học với dung sai 0,0003 độ (khoảng 33 m), đủ mịn cho tỷ
lệ hiển thị cấp tỉnh. Phạm vi lớp này mở rộng tới khoảng 117,4°Đ vì bao gồm
huyện đảo Trường Sa.

---

## Cấu trúc thư mục

```
KHANHHOA/
├── index.html                  Trang bản đồ chính
├── pages/
│   ├── quan-trac.html          Tab Quan trắc, số liệu từ CSDL QTQG
│   └── thong-ke.html           Trang thống kê tổng hợp
├── assets/
│   ├── css/
│   │   ├── style.css           Kiểu trình bày chung, có nền sáng và tối
│   │   ├── quan-trac.css       Phần riêng của tab Quan trắc
│   │   └── thong-ke.css        Phần riêng của trang thống kê
│   ├── ky_hieu/                Ký hiệu điểm dạng SVG + ky_hieu.json
│   └── js/
│       ├── config.js           Cấu hình lớp, ký hiệu, trường thuộc tính
│       ├── tinh.js             Nạp tinh.json, phải nạp trước các tệp khác
│       ├── dung_chung.js       Hàm tiện ích cả ba trang đều dùng
│       ├── ky_hieu.js          Dựng ký hiệu điểm từ danh mục SVG
│       ├── map.js              Khởi tạo bản đồ, bản đồ nền, công cụ
│       ├── layers.js           Nạp và vẽ lớp, cây lớp, chú giải, bộ lọc
│       ├── identify.js         Truy vấn bằng nhấp chuột, bảng thông tin
│       ├── table.js            Bảng thuộc tính, xuất CSV và GeoJSON
│       ├── realtime.js         Dữ liệu quan trắc và cảnh báo
│       ├── xuat_tep.js         Xuất CSV và tải tệp, dùng chung ba trang
│       ├── api_quan_trac.js    Máy khách gọi backend, chỉ tab Quan trắc dùng
│       ├── quan_trac.js        Logic tab Quan trắc
│       ├── thong-ke.js         Logic trang thống kê
│       └── app.js              Khởi động, hộp thoại
├── backend/                    Dịch vụ trung gian QTQG (KHÔNG xuất bản lên web)
│   ├── main.py                 FastAPI, CORS, các endpoint
│   ├── nguon_qtqg.py           Lớp duy nhất biết schema QTQG
│   ├── truy_van.sql            16 câu SELECT, tách khỏi mã Python
│   ├── .env.mau                Mẫu biến môi trường (bản .env đã gitignore)
│   └── tests/                  Bộ kiểm thử, chạy bằng pytest
├── tinh.json                   Tham số của tỉnh, Python và JS dùng chung
├── data/                       GeoJSON, realtime.json
│   ├── nen/                    Nền địa phương
│   └── history/                Lịch sử quan trắc theo tháng, dạng CSV
├── scripts/                    Pipeline Python
├── CSDL/                       Shapefile gốc (không xuất bản lên web)
├── data_goc/                   Nơi đặt dữ liệu chuyên đề thật khi có
├── .github/workflows/          Hai workflow GitHub Actions
└── environment.yml             Định nghĩa môi trường conda
```

---

## Cách hoạt động của phần "thời gian thực"

Trang tĩnh không có máy chủ, nên cơ chế là:

1. GitHub Actions chạy theo lịch cron (mặc định mỗi giờ một lần).
2. Workflow gọi `scripts/03_lay_realtime.py`, ghi ra `data/realtime.json` và nối
   thêm vào `data/history/YYYY-MM.csv`.
3. Workflow tự commit và đẩy lên nhánh `main`.
4. Workflow xuất bản chạy lại, trang web có dữ liệu mới.
5. Trình duyệt cũng tự `fetch` lại tệp đó mỗi 10 phút.

Điểm thiết kế quan trọng: **hình học và số đo được tách rời**. Vị trí hồ, trạm,
công trình nằm trong các tệp GeoJSON tĩnh; số đo theo thời gian nằm riêng trong
`realtime.json`, ghép với nhau qua trường `ma`. Nhờ vậy khi chuyển từ dữ liệu mô
phỏng sang nguồn quan trắc thật, chỉ phải sửa một hàm trong Python, không đụng
đến phần bản đồ.

### Chuyển sang nguồn quan trắc thật

1. Cài đặt hàm `doc_tu_nguon_that()` trong `scripts/03_lay_realtime.py`.
2. Ánh xạ mã trạm của nguồn về trường `ma` trong các lớp GeoJSON.
3. Đổi biến môi trường `CHE_DO` trong `.github/workflows/update-realtime.yml`
   từ `mo_phong` thành `that`.

Lưu ý: workflow đó chạy trên runner của GitHub nên **không với tới được cơ sở dữ
liệu của ngành**. Vì vậy `data/realtime.json` vẫn là nguồn mô phỏng cho bản đồ
chính; số liệu thật của Quan trắc Quốc gia đi theo đường riêng, mô tả ở mục dưới.

---

## Tab Quan trắc và backend trung gian QTQG

Số liệu mực nước, lưu lượng và chất lượng nước thật nằm trong cơ sở dữ liệu phần
mềm **Quan trắc Quốc gia (QTQG)** — một PostgreSQL + PostGIS của cả nước.

**Không nối trực tiếp từ trình duyệt.** Ba lý do:

1. Trình duyệt không nói được giao thức PostgreSQL.
2. Dù có cổng HTTP đi nữa thì tài khoản và mật khẩu cũng lọt ra trình duyệt của
   người dùng, và chính sách CORS của tên miền khác sẽ chặn.
3. Cơ sở dữ liệu QTQG là của cả nước và đang vận hành thật, không chịu được việc
   mỗi người mở trang là một lượt truy vấn riêng.

Vì vậy có `backend/`: một dịch vụ FastAPI giữ thông tin kết nối, lọc về phạm vi
tỉnh, chuẩn hóa thành GeoJSON, tính chỉ số WQI, có bộ nhớ đệm 60 giây, rồi trang
web mới gọi dịch vụ đó.

```
CSDL QTQG (PostgreSQL + PostGIS, toàn quốc)
   |  psycopg, kết nối CHỈ ĐỌC, chỉ tồn tại trong backend/
   v
backend/  FastAPI cổng 8001   <-- backend/.env giữ máy chủ, tài khoản, mật khẩu
   |  lọc theo khung bao tỉnh + tên tỉnh, chuẩn hóa tên trường, cache 60 giây
   v
GET /api/quan-trac/so-do  (đúng schema data/realtime.json)
   |  fetch() trong assets/js/api_quan_trac.js
   v
pages/quan-trac.html
```

Quyết định then chốt: endpoint `/api/quan-trac/so-do` trả về **đúng cấu trúc mà
trang web đã đọc từ trước**. Nhờ vậy toàn bộ phần hiển thị số đo — ký hiệu theo
trạng thái, bảng chi tiết, thẻ chỉ tiêu — dùng lại nguyên vẹn, không phải viết
lại một dòng nào.

**Bản đồ chính vẫn thuần tĩnh.** `index.html` và trang thống kê không nạp
`api_quan_trac.js` và không gọi dịch vụ nào, nên tắt backend thì chúng vẫn đủ
chức năng. Đó là điều giữ cho trang chạy được trên GitHub Pages.

Dữ liệu QTQG vào bản đồ chính theo đường khác: `scripts/08_xuat_lo_khoan_ndd.py`
gọi `backend/nguon_qtqg.py` như một thư viện rồi ghi ra
`data/quan_trac_ndd.geojson`. Số đo trong lớp tĩnh đó là số tại thời điểm xuất,
ghi rõ trong trường `nguon_dl` của từng đối tượng; muốn số mới nhất thì xem tab
Quan trắc.

Chi tiết vận hành, danh sách biến môi trường, sơ đồ bảng của QTQG và các bẫy đơn
vị đo: xem **`backend/README.md`**.

**Không đặt dịch vụ này ra Internet công khai.** Nó giữ thông tin kết nối vào một
cơ sở dữ liệu ngành đang vận hành. Nếu buộc phải mở ra ngoài thì đặt sau reverse
proxy có HTTPS và hạn chế theo địa chỉ IP. Workflow xuất bản cố ý không đóng gói
`backend/`.

---

## Thay dữ liệu mô phỏng bằng dữ liệu thật

Đặt shapefile hoặc file GDB chuyên đề vào `data_goc/`, rồi viết
`scripts/02_chuan_hoa_chuyen_de.py` theo khuôn mẫu của
`01_chuan_hoa_ranh_gioi.py`. Điều kiện duy nhất là **tên trường đầu ra phải
khớp với khai báo trong `assets/js/config.js`**. Nếu tên trường nguồn khác, sửa
bảng ánh xạ trong script thay vì sửa giao diện.

Mỗi lớp trong `config.js` khai báo: tên hiển thị, đường dẫn tệp, kiểu hình học,
hàm ký hiệu, danh sách trường thuộc tính kèm đơn vị và định dạng, các cột mặc
định của bảng, và chú giải. Thêm một lớp mới chỉ cần thêm một khối vào
`CAU_HINH.lop` và đưa mã lớp vào một nhóm trong `CAU_HINH.nhom_lop`.

---

## Chức năng hỗ trợ ra quyết định

- **Truy vấn bằng nhấp chuột.** Hệ thống tự kiểm tra hình học của mọi đối tượng
  đang hiển thị thay vì dựa vào sự kiện click của SVG (vốn chỉ bắt được hình
  nằm trên cùng). Nhờ vậy một điểm nhấp trúng nhiều đối tượng thuộc nhiều lớp
  khác nhau sẽ hiện danh sách thả xuống đầy đủ, sắp theo thứ tự điểm, đường,
  vùng và theo khoảng cách.
- **Xuất dữ liệu.** CSV có BOM UTF-8 để Excel đọc đúng tiếng Việt, phân cách
  bằng dấu phẩy theo chuẩn RFC 4180 nên pandas, GeoPandas và QGIS đều đọc được.
  GeoJSON giữ nguyên hình học.
- **Chọn theo bán kính.** Liệt kê mọi đối tượng quanh một điểm, sắp theo khoảng
  cách. Dùng khi thẩm định cấp phép, ví dụ tìm các điểm xả thải quanh một công
  trình cấp nước.
- **Sức chịu tải đoạn sông.** Tính theo phương pháp đánh giá trực tiếp của
  Thông tư 76/2017/TT-BTNMT (sửa đổi bởi Thông tư 02/2022/TT-BTNMT):
  `Ltđ = Cqc × Qs × 86,4`, `Lnn = Cnn × Qs × 86,4`,
  `Ltn = (Ltđ − Lnn − Lt) × Fs`. Bảng thông tin hiển thị đủ các thành phần.
- **Thống kê theo lưu vực**, **cảnh báo ngưỡng**, **biểu đồ chuỗi 24 giờ**,
  **đo khoảng cách**, **tìm kiếm không phân biệt dấu**.

---

## Trang thống kê

`pages/thong-ke.html`, mở từ mục **Thống kê** trên thanh menu của trang bản đồ.
Trang này đọc thẳng các tệp trong `data/` chứ không giữ bản sao dữ liệu riêng,
nên chạy lại pipeline là số liệu tự cập nhật.

Nội dung gồm năm thẻ chỉ tiêu (lưu lượng khai thác cấp phép, xả thải, dung tích
hồ chứa hiện tại, số đoạn sông hết khả năng tiếp nhận, giấy phép cần xử lý), bảy
biểu đồ và một bảng danh sách công trình khai thác xuất được ra CSV. Bộ lọc theo
lưu vực trên thanh đầu trang áp dụng đồng thời cho thẻ chỉ tiêu, biểu đồ và bảng.

Vì phần lớn chỉ tiêu về nước còn dựa trên dữ liệu mô phỏng, mỗi thẻ số và mỗi
mục đều mang nhãn phân biệt: nhãn vàng **mô phỏng** và nhãn xanh **dữ liệu thật**.
Mục "Đơn vị hành chính" dùng số liệu thật từ bộ ranh giới xã nên không chịu ảnh
hưởng của bộ lọc lưu vực.

## Triển khai lên GitHub Pages

1. Đẩy mã nguồn lên GitHub, nhánh `main`.
2. Vào Settings → Pages, mục Source chọn **GitHub Actions**.
3. Workflow `deploy-pages.yml` tự chạy khi có commit mới.

Workflow chỉ đóng gói `index.html`, `assets/`, `data/`, `pages/` và `tinh.json`.
Thư mục `CSDL/` chứa shapefile gốc không được xuất bản vì dung lượng lớn và trình
duyệt không cần đến.

Thư mục `backend/` **cố ý không được xuất bản, và không bao giờ được xuất bản**:
đó là dịch vụ chạy trên máy chủ của tỉnh, giữ thông tin kết nối vào cơ sở dữ
liệu ngành. Trên GitHub Pages, tab Quan trắc sẽ hiện thông báo chưa nối được
dịch vụ — đúng như thiết kế. Muốn tab đó hoạt động cho người dùng thì triển khai
`backend/` trong mạng của tỉnh rồi sửa `CAU_HINH.api.goc` trong
`assets/js/config.js` trỏ về địa chỉ đó, kèm thêm tên miền vào `CORS_NGUON`.

---

## Bản đồ nền

Có sáu lựa chọn, chia làm hai nhóm.

**Nền từ dịch vụ tile ngoài**, không cần đăng ký khóa API: Esri World Light Gray
Base, World Dark Gray Base, World Imagery, OpenStreetMap, OpenTopoMap. Lưu ý khi
muốn đổi nguồn: nhiều dịch vụ trước đây miễn phí, chẳng hạn CARTO basemaps, nay
đã yêu cầu API key và sẽ hiện chữ chìm "API KEY REQUIRED" trên bản đồ.

**Nền địa phương**, dựng từ chính dữ liệu của đơn vị. Script
`04_tao_nen_dia_phuong.py` cắt bộ bản đồ nền quốc gia `BaseMapVietNam.gdb`
(473 MB, 25 lớp, EPSG:32648) theo phạm vi đất liền của tỉnh và xuất ra
`data/nen/*.geojson`, tổng khoảng 3,5 MB:

| Tệp | Nội dung | Đối tượng |
|---|---|---|
| `rung.geojson` | Rừng | 1 (đã cắt) |
| `bao_ton.geojson` | Vườn quốc gia, khu bảo tồn | 6 |
| `mat_nuoc.geojson` | Hồ, đầm, ao | 577 |
| `song_vung.geojson` | Sông suối dạng vùng | 165 |
| `duong_bo.geojson` | Quốc lộ, tỉnh lộ, đường chính đô thị | 1.495 |
| `dan_cu.geojson` | Điểm dân cư | 1.432 |
| `dia_danh.geojson` | Địa danh sơn văn | 658 |

Ưu điểm: địa danh bằng tiếng Việt, có sẵn sông suối dạng vùng và mặt nước là
những lớp mà tile quốc tế không có, và không phụ thuộc nhà cung cấp nào. Các tệp
chỉ được tải về khi người dùng chọn nền này, sau đó giữ trong bộ nhớ.

Hai lớp nhãn chữ chỉ hiện khi đã phóng đủ gần (địa danh từ mức 13, điểm dân cư
từ mức 14), vì trong phạm vi tỉnh có tới 2.090 nhãn, hiện hết ở mức zoom thấp
thì chữ chồng lên nhau.

Lớp đường bộ đã lọc còn quốc lộ, tỉnh lộ và đường chính đô thị
(`loaiduongbo` 1, 2, 3). Giữ cả đường huyện và đường xã thì lên hơn 10.000 đối
tượng, tệp nặng 5,3 MB mà ở tỷ lệ cấp tỉnh cũng chỉ thành một đám rối.

---

## Căn cứ pháp lý tham chiếu

- Luật Tài nguyên nước số 28/2023/QH15
- Nghị định 53/2024/NĐ-CP quy định chi tiết thi hành một số điều của Luật
- Nghị định 54/2024/NĐ-CP về khai thác, sử dụng tài nguyên nước
- Thông tư 76/2017/TT-BTNMT, sửa đổi bởi Thông tư 02/2022/TT-BTNMT, về đánh giá
  khả năng tiếp nhận nước thải và sức chịu tải của nguồn nước sông, hồ
- Quyết định 1460/QĐ-TCMT ngày 12/11/2019 về tính toán và phân loại chỉ số chất
  lượng nước WQI. `backend/wqi.py` cài đặt đầy đủ; thứ tự ưu tiên là dùng số WQI
  của QTQG nếu có, không có thì tự tính khi đủ điều kiện ở mục 2.1.b, không đủ
  thì **để khuyết** kèm lý do — không bao giờ đoán một con số.
- QCVN 09-MT:2015/BTNMT về chất lượng nước dưới đất. Dùng cho ngưỡng các thông số
  của lỗ khoan quan trắc. WQI **không** áp cho nước dưới đất, vì QĐ 1460 là chỉ
  số chất lượng nước **mặt** lục địa.

---

## Dữ liệu kiểm kê chính thức (đang chờ bổ sung)

Thư mục `CSDL/SD_TLTT_DTHT_XA_THAI` chứa bộ dữ liệu kiểm kê dạng MapInfo TAB.
**Bộ này chưa được nạp vào hệ thống** vì mới có phạm vi Khánh Hòa cũ, còn thiếu
Ninh Thuận cũ. Khi có đủ cả hai phần, các lớp cần dùng sẽ được lọc vào
`data_goc/` rồi chuẩn hóa bằng một script mới (đặt tên `05_chuan_hoa_chuyen_de.py`).

### Hệ quy chiếu

Toàn bộ 23 tệp TAB dùng chung một phép chiếu, đã đối chiếu tham số và xác nhận
bằng pyproj:

| Tham số | Giá trị |
|---|---|
| Phép chiếu | Transverse Mercator |
| Kinh tuyến trục | 108°15' (108,25) |
| Hệ số tỷ lệ | 0,9999 |
| False easting | 500.000 m |
| Vĩ tuyến gốc | 0 |
| **Mã EPSG** | **9217 — VN-2000 / TM-3 108-15** |

Đây đúng là múi 3° của Khánh Hòa. Khi bổ sung phần Ninh Thuận cũ, cần kiểm tra
kinh tuyến trục của bộ đó ngay trong tệp thay vì giả định: nếu cũng là 108°15'
thì cả tỉnh dùng chung một hệ, không phải ghép múi.

Hai điểm cần lưu ý khi chuyển đổi:

1. Tệp `.TAB` khai báo datum là `WGS_1984` chứ không phải VN-2000. Phải
   `set_crs(9217, allow_override=True)` để pyproj dùng đúng phép chuyển datum
   khi đưa về WGS84, giống cách `02_chuan_hoa_ranh_gioi_xa.py` đang làm.
2. Tên trường tiếng Việt đọc ra bị lỗi phông, ví dụ `S__hi_u_di_m` đáng lẽ là
   "Số hiệu điểm". Cần chỉ định bảng mã khi đọc, hoặc đổi sang tên trường không
   dấu ngay ở bước xuất từ MapInfo. Cách thứ hai đơn giản hơn.

### Các lớp đã khảo sát và dự kiến ánh xạ

| Tệp TAB | Hình học | Đối tượng | Lớp tương ứng trong hệ thống |
|---|---|---|---|
| `TH_Kiemke_KhanhHoa_13.9.26` | Point | 119, 76 trường | `khai_thac` (đầy đủ nhất: giấy phép, lưu lượng, lưu vực, mục đích) |
| `DKS_CT_KT_NM` | Point | 119 | `khai_thac` (điểm khảo sát) |
| `KT_NT` | Point | 51 | `khai_thac` |
| `DKS_CT_XT_6_9` | Point | 34 | `xa_thai` |
| `Song_KhanhHoa_Moi` | LineString | 184, 101 trường | `song_suoi` (có `TENSONG`, `LOAISONG`, `DAIKM`, mã phân cấp sông) |
| `Hanhtrinh_CT_KT`, `Hanhtrinh_CT_XT` | LineString | 9 và 5 | hành trình khảo sát, không đưa lên web |
| `NEN_DH50/*` | nhiều | | nền địa hình 1:50.000, đã có nền địa phương thay thế |

Còn thiếu so với thiết kế: ao hồ đầm dạng vùng, hồ chứa, ranh giới lưu vực,
trạm quan trắc và phân đoạn đánh giá sức chịu tải. Các lớp này hiện vẫn dùng
dữ liệu mô phỏng.
