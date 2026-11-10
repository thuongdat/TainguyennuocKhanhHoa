# Backend trung gian quan trắc QTQG

Dịch vụ đứng giữa cơ sở dữ liệu phần mềm Quan trắc Quốc gia (QTQG) và tab
**Quan trắc** của trang WebGIS.

## Vì sao cần lớp trung gian

Trình duyệt không gọi thẳng PostgreSQL được, và cũng không nên:

1. **Thông tin đăng nhập cơ sở dữ liệu không được ra đến trình duyệt.** Nó chỉ
   nằm trong `backend/.env`, tệp này đã được `.gitignore`.
2. **Cơ sở dữ liệu QTQG là của cả nước** và không phải định dạng không gian cho
   web. Ở đây nó được lọc về phạm vi tỉnh rồi đổi thành GeoJSON.
3. **Bộ nhớ đệm 60 giây** bảo vệ một hệ thống đang chạy thật khỏi lượt gọi lặp:
   mỗi trang tự làm mới 5 phút, không có bộ đệm thì mỗi người dùng là một lượt
   truy vấn riêng.

Toàn bộ kết nối khóa ở chế độ **chỉ đọc**, xem `ket_noi.py`.

## Chạy trên máy cục bộ

```bash
cp backend/.env.mau backend/.env     # rồi điền giá trị thật
cd backend
D:\Anaconda_Data\envs\tainguyennuoc\python.exe main.py
```

Gọi `main.py` chứ không gọi `uvicorn` trực tiếp: nó **đọc cổng từ
`cong.backend` trong `tinh.json`** nên không bao giờ lệch với cổng mà giao diện
gọi đến. Mỗi tỉnh một cặp cổng riêng — Khánh Hòa 8000/8001, Gia Lai 8010/8011 —
nên gõ tay `--port` là việc dễ sai nhất.

Gọi thẳng python của môi trường, **không dùng `conda run`** (lý do ghi trong
`CLAUDE.md` ở thư mục gốc).

Trang web chạy ở một cửa sổ khác, tại thư mục gốc dự án:

```bash
python scripts/chay_web.py
```

Script đó cũng lấy cổng từ `tinh.json`, luôn phục vụ đúng thư mục gốc dự án, và
từ chối chạy nếu cổng đã có người dùng.

Rồi mở <http://localhost:8000/pages/quan-trac.html>.

Tài liệu API tự sinh: <http://localhost:8001/docs>.

## Biến môi trường

| Biến | Mặc định | Ý nghĩa |
|---|---|---|
| `CHE_DO` | `thu_nghiem` | `thu_nghiem` sinh số liệu thử từ vị trí trạm thật; `that` đọc cơ sở dữ liệu QTQG |
| `CONG` | `cong.backend` trong `tinh.json` (**8001**) | Cổng dịch vụ. Mỗi tỉnh một cặp cổng riêng |
| `QTQG_MAY_CHU` | | Địa chỉ máy chủ PostgreSQL |
| `QTQG_CONG` | `5432` | Cổng |
| `QTQG_CSDL` | | Tên cơ sở dữ liệu |
| `QTQG_TAI_KHOAN` | | Tài khoản, nên là quyền chỉ đọc |
| `QTQG_MAT_KHAU` | | Mật khẩu |
| `CORS_NGUON` | suy từ `cong.web` trong `tinh.json` (**8000**) | Các nguồn được phép gọi, phân cách bằng dấu phẩy |
| `CACHE_GIAY` | `60` | Thời gian giữ kết quả trong bộ nhớ đệm |
| `DUONG_DAN_SQLITE` | `chuoi_quan_trac.sqlite3` | Tệp tích lũy chuỗi thời gian |
| `UOC_NHIET_DO` | `1` | Ước nhiệt độ nước từ trung bình nhiều năm cùng tháng của chính trạm khi kỳ đo thiếu. Là số **suy diễn**; đặt `0` để tắt |
| `HOP_TRAM_DIA_PHUONG` | `0` | Hợp lớp `data/quan_trac.geojson` vào danh sách trạm QTQG. Dự án này **tắt** vì lớp đó còn là dữ liệu mô phỏng |
| `SO_DO_CU_TOI_DA_NGAY` | `730` | Ẩn bản ghi số đo cũ hơn bao nhiêu ngày (730 = 2 năm). Ẩn bản ghi, **không** ẩn công trình; đặt `0` để tắt |

## Các endpoint

| Đường dẫn | Trả về |
|---|---|
| `GET /api/suc-khoe` | Trạng thái dịch vụ, chế độ, số trạm |
| `GET /api/quan-trac/tram.geojson` | Vị trí trạm, FeatureCollection EPSG:4326 |
| `GET /api/quan-trac/so-do` | Số đo mới nhất, **đúng schema `data/realtime.json`** |
| `GET /api/quan-trac/chuoi?ma=&thong_so=` | Chuỗi thời gian để vẽ biểu đồ |
| `GET /api/quan-trac/thong-so-co-chuoi?ma=` | Thông số đã tích lũy được chuỗi |

`/api/quan-trac/so-do` trả về đúng cấu trúc mà trang web đã đọc từ trước. Nhờ
vậy `lay_realtime()`, `kieu_ve(p, rt)` và `CAU_HINH.truong_realtime` dùng lại
nguyên vẹn, không phải viết lại phần hiển thị số đo.

## Dữ liệu QTQG thực tế có gì cho tỉnh này

> **CHƯA KHẢO SÁT CHO KHÁNH HÒA.** Các bảng dưới đây là cấu trúc của cơ sở dữ
> liệu QTQG, đã kiểm chứng và dùng chung cho cả nước. Riêng **số lượng trạm,
> lỗ khoan và kỳ đo trong phạm vi Khánh Hòa thì chưa có**. Chạy
> `backend/kiem_tra_ket_noi.py` rồi điền vào mục này trước khi nói với người
> dùng rằng tab Quan trắc thể hiện mạng quan trắc của tỉnh.

PostgreSQL 9.6.8 + PostGIS, 151 bảng.

Các bảng nước **mặt** dùng ở đây:

| Bảng | Khóa | Ghi chú |
|---|---|---|
| `surfacewater_station` | `matram` | 131 trạm toàn quốc, `geom` EPSG:3405 |
| `surfacewater_chatluongnuoc` | `sohieutram`, `ngaylaymau` | 35.442 dòng toàn quốc |
| `surfacewater_level` | `station_code`, `date_measure` | 303.365 dòng, theo giờ |
| `surfacewater_flow` | `station_code`, `date_measure` | 5.139 dòng |
| `hydrology_station` | `matram` | 385 trạm, chỉ có vị trí |

Các bảng `water_level`, `water_temperature`, `water_chemistry` là **nước dưới
đất** (khóa `well_code`), xem mục "Nước dưới đất" bên dưới.

### Hai điểm bất ngờ của schema, đã kiểm chứng

1. **`surfacewater_chatluongnuoc` lưu mỗi dòng một vài thông số**, phần còn lại
   để NULL. Một lần lấy mẫu trải ra nhiều dòng cùng `(sohieutram, ngaylaymau)`.
   Phải gộp bằng `MAX(...) GROUP BY` trạm, ngày. Đọc từng dòng rời rạc sẽ thấy
   gần hết thông số bị khuyết.
2. **`water_level` và `stake_high` tính bằng centimet**, trên mốc cao độ riêng
   của từng trạm. Hai ví dụ đo thẳng từ cơ sở dữ liệu toàn quốc: trạm YYH01 dao
   động 20.734-21.189 cm (tức 207,3-211,9 m), trạm AT01 dao động 210-972 cm.
   Đó là **cao độ mặt nước theo mốc trạm**, không phải độ sâu. Chia 100 để ra
   mét.

### Phạm vi thực tế: phải đếm, không được suy

Số trạm **có số đo** trong một tỉnh thường ít hơn hẳn số trạm có trong danh
mục. Ba trường hợp đã gặp ở tỉnh khác dùng chung bộ mã này:

- Trạm thủy văn chỉ có vị trí, bảng `tramthuyvan_*` dùng hệ mã khác hẳn và
  không nối được.
- "Trạm lồng ghép" là các hồ chứa lớn nhưng **không có mã trạm** nên không nối
  được với bảng số đo.
- Trạm có mã nhưng chuỗi số đo dừng lại từ nhiều năm trước.

Vì vậy đừng suy con số từ tỉnh khác. Kết quả khảo sát của tỉnh này:

```
Ngày khảo sát:                      27/10/2026
Trạm nước mặt (surfacewater_station):  1   NP01 Trạm Nha Phu, CÓ số đo
Trạm thủy văn (hydrology_station):     5   TV_KH*, TV_NT*, chỉ có vị trí
Lỗ khoan đang hoạt động:              28   cả 28 đều có mực nước và phân tích
Tổng công trình trên tab Quan trắc:   34   trong đó 29 ghép được số đo
```

**Nước dưới đất, 28 lỗ khoan.** Mã dạng `QT*-KH` và `QT*-NT`. Tầng chứa nước:
qh 12, qp 10, j 4, q 1, n 1. Mực nước từ −0,7 đến −18,01 m so với miệng lỗ
khoan, đo ngày 06/10/2026; kết quả phân tích hóa học lấy mẫu 03/05/2026. Danh
sách xã trải cả hai tỉnh cũ (Tu Bông, Vạn Ninh, Diên Khánh, Cam Lâm, Khánh Vĩnh,
và Mỹ Sơn, Bảo An, Phước Hậu, Phước Dinh, Thuận Bắc), nên bộ lọc theo
`ten_tinh_trong_qtqg = ["Khánh Hòa", "Ninh Thuận"]` chạy đúng.

**Nước mặt: đúng một trạm có số đo, và số đó đã rất cũ.**

| Trạm | Loại | Số đo |
|---|---|---|
| `NP01` Trạm Nha Phu (sông Dinh) | Tài nguyên nước mặt | Có, mới nhất **31/12/2017** |
| `TV_KHDT01` Đồng Trăng (sông Cái) | Thủy văn | Không |
| `TV_KHNH01` Ninh Hoà (sông Cái) | Thủy văn | Không |
| `TV_NTPH01` Phước Hà (sông Lu) | Thủy văn | Không |
| `TV_NTPR01` Phan Rang (sông Cái) | Thủy văn | Không |
| `TV_NTQN01` Quảng Ninh (sông Cái Phan Rang) | Thủy văn | Không |

NP01 có đủ thông số để tính WQI nên backend tự tính được: **WQI 89, phân loại
"Tốt"**, mang cờ `wqi_tu_tinh`. Nó **không** cần ước nhiệt độ (có số đo thật
26,4 °C) nên không mang cờ `nhiet_do_uoc_tinh`.

Số của NP01 là của **31/12/2017**, trong khi số của 28 lỗ khoan là của
**06/10/2026** — hai mốc cách nhau gần 9 năm. Cột "Thời điểm đo" có ghi rõ,
nhưng người xem quét nhanh chỉ thấy huy hiệu xanh "Bình thường" và WQI 89. Đây
đúng là tình huống dự án đã tránh ở nhánh nước dưới đất bằng cách chỉ lấy lỗ
khoan `hientrang = 'Đang hoạt động'`.

## Ẩn bản ghi số đo quá cũ

Theo quyết định của chủ đầu tư, backend **ẩn bản ghi số đo cũ hơn 2 năm**
(`SO_DO_CU_TOI_DA_NGAY=730`). Với bộ dữ liệu hiện tại, đúng một bản ghi bị ẩn:
NP01.

**Ẩn là ẩn BẢN GHI SỐ ĐO, không phải công trình.** NP01 vẫn nằm trong
`/api/quan-trac/tram.geojson` (34 công trình, không đổi), vẫn hiện trên bản đồ
và trong bảng, vẫn chọn được ở ô chọn trạm — chỉ là không có số đo đi kèm,
giống 5 trạm thủy văn vốn không có số đo. Không xóa một công trình thật khỏi
danh mục kiểm kê.

Hệ quả, đúng như mong muốn: NP01 không còn `trang_thai` nên mất huy hiệu xanh,
không còn WQI 89, không vào danh sách cảnh báo, và không kéo lùi mốc "Cập nhật"
của cả gói dữ liệu về năm 2017.

Phép lọc nằm ở `tong_hop.tach_ban_ghi_qua_cu()`, gọi từ hai nơi dùng chung một
quy tắc: endpoint `/api/quan-trac/so-do` trong `main.py`, và
`scripts/08_xuat_lo_khoan_ndd.py`. Lọc **sau** bộ nhớ đệm chứ không trong đó, để
bộ đệm giữ dữ liệu thô: đổi ngưỡng thì không phải xóa đệm.

**Hai điều cố ý:**

1. **Bản ghi không đọc được `thoi_diem` thì GIỮ LẠI.** Không biết tuổi thì không
   được đoán là cũ rồi bỏ đi; đoán sai là âm thầm làm mất số liệu thật.
2. **Chỉ xét trường `thoi_diem`** (mốc mới nhất của bản ghi), không xét
   `thoi_diem_chat_luong` riêng. Nước dưới đất lấy mẫu hóa học vài lần một năm
   nên mốc đó thường cách mốc mực nước nhiều tháng; xét riêng sẽ bỏ cả những lỗ
   khoan đang đo hàng ngày. Giao diện hiện đủ cả hai mốc nên người đọc vẫn thấy
   kỳ lấy mẫu là bao giờ.

**Đã ẩn thì phải nói rõ.** Gói dữ liệu mang thêm khóa `so_do_cu`, và tab Quan
trắc hiện một dải thông báo kèm tên công trình và thời điểm đo, cộng một thẻ chỉ
tiêu "Ẩn vì số đo quá cũ". Không im lặng làm mất dữ liệu rồi để người dùng tự
phát hiện.

```json
"so_do_cu": {
  "nguong_ngay": 730,
  "so_ban_ghi": 1,
  "cong_trinh": [
    { "ma": "NP01", "ten": "Trạm Nha Phu", "thoi_diem": "2017-12-31 22:00",
      "thong_so": ["ph", "do_mg_l", "...", "h_m", "q_m3s", "wqi"] }
  ]
}
```

**Endpoint `/api/quan-trac/chuoi` cố ý KHÔNG lọc.** Chuỗi thời gian của NP01
(59 kỳ WQI từ 2013 đến 2017, 2.315 mốc mực nước từ 2011) vẫn vẽ được. Biểu đồ có
trục ngày nên tự nói lên số liệu dừng ở năm nào — đó là tư liệu lịch sử có ích,
khác hẳn một con số trần trông như vừa đo xong.

**Vì sao `cong_trinh[].thong_so` phải có.** Ẩn là ẩn GIÁ TRỊ, không ẩn tên
thông số. Ô chọn thông số của tab Quan trắc dựng từ bản ghi số đo hiện hành;
bản ghi bị ẩn thì ô đó rỗng và endpoint không lọc ở trên thành vô dụng vì giao
diện không còn chỗ nào gọi tới nó. Danh sách tên này là đường đi còn lại.
`tong_hop.thong_so_so_hoc()` dựng nó, và cố ý loại `bool` ra vì trong Python
`bool` là kiểu con của `int`: không loại thì `wqi_tu_tinh=True` bị kể là một
thông số vẽ được biểu đồ.

Đổi ngưỡng hoặc tắt hẳn: sửa `SO_DO_CU_TOI_DA_NGAY` trong `backend/.env`
(đặt `0` để tắt). `tests/test_so_do_cu.py` chốt lại toàn bộ hành vi này.

Khung bao của tỉnh là hình chữ nhật nên trùm cả một phần các tỉnh lân cận; vì
vậy sau bước lọc theo khung bao trong SQL còn một bước lọc theo tên tỉnh, lấy
từ `ten_tinh_trong_qtqg` trong `tinh.json`. Với Khánh Hòa, danh sách đó là
`["Khánh Hòa", "Ninh Thuận"]` vì QTQG chưa cập nhật việc sáp nhập.

**Lớp quan trắc địa phương không được trộn vào.** `data/quan_trac.geojson` của
dự án này còn là dữ liệu mô phỏng, nên `HOP_TRAM_DIA_PHUONG=0`: tab Quan trắc
chỉ hiện trạm QTQG thật. Khi tỉnh có lớp quan trắc địa phương thật thì đặt
`HOP_TRAM_DIA_PHUONG=1`, cơ chế hợp danh sách vẫn còn nguyên trong
`khong_gian.hop_danh_sach_tram()`.


### Ước nhiệt độ nước

Chín kỳ gần nhất của YYH01 (năm 2026) **không có số đo nhiệt độ**. Thiếu nhiệt
độ thì không quy được DO ra phần trăm bão hòa, nhóm IV tụt xuống 2 thông số và
WQI không đủ điều kiện công bố theo mục 2.1.b.

Theo quyết định của người dùng, backend ước nhiệt độ bằng trung bình nhiều năm
cùng tháng của **chính trạm đó**. Đây là số **suy diễn**, không phải số đo, nên
trái với yêu cầu về dữ liệu đầu vào ở mục 2.1.a. Bù lại:

- Mỗi bản ghi dùng nó mang cờ `nhiet_do_uoc_tinh: true`.
- Hộp thoại chi tiết trạm ghi rõ bằng tiếng Việt.
- Tắt được bằng `UOC_NHIET_DO=0` trong `backend/.env`.

## Nước dưới đất

Phạm vi kiểm kê của trang web là nước mặt, nhưng mạng quan trắc quốc gia nước
dưới đất nằm trong cùng cơ sở dữ liệu QTQG và cũng là công trình quan trắc của
tỉnh, nên tab Quan trắc hiển thị luôn.

| Bảng | Khóa | Nội dung |
|---|---|---|
| `monitoring_well` | `well_code` | Lỗ khoan, lọc theo cột `province`, `geom` EPSG:3405 |
| `water_level` | `well_code` | mực nước theo giờ, 40,9 triệu dòng toàn quốc |
| `water_temperature` | `well_code` | nhiệt độ nước, 24,6 triệu dòng |
| `water_chemistry` | `well_code` | 93 cột thành phần hóa học |

**Chỉ lấy lỗ khoan `hientrang = 'Đang hoạt động'`.** Cơ sở dữ liệu còn giữ cả
lỗ khoan đã dừng quan trắc; số đo cuối cùng của chúng có thể cũ nhiều năm, để
chung một bản đồ với số đo hôm qua là gây hiểu nhầm.

Bảng này ghi tỉnh theo đơn vị hành chính **sau** sáp nhập, nên lỗ khoan nằm
trên địa bàn tỉnh cũ nào cũng được trả về, miễn là cột `province` khớp
`ten_tinh_trong_qtqg`.


### Bốn điểm khác hẳn nhánh nước mặt

1. **`water_level` của nước dưới đất tính bằng mét và là số âm.** `-14,45`
   nghĩa là mặt nước nằm sâu 14,45 m dưới miệng lỗ khoan. Không chia 100 như
   `surfacewater_level`. Vì vậy dùng trường riêng `h_ngam_m`; gộp với `h_m`
   của nước mặt là vẽ chung một biểu đồ hai đại lượng ngược nghĩa.
   `cao_do_mn_m` = `elevation` + `water_level`, là phép cộng đúng nghĩa.
2. **Không tính WQI.** Quyết định 1460/QĐ-TCMT là chỉ số chất lượng nước **mặt**
   lục địa. Bản ghi lỗ khoan có pH, amoni, nitrat, coliform nên hàm tính WQI
   vẫn chạy trót lọt và trả về một con số — đúng hình thức mà sai chuyên môn.
   `wqi.gan_wqi()` thoát sớm khi `loai == "nuoc_duoi_dat"`; ngưỡng các thông
   số nước dưới đất theo QCVN 09-MT:2015/BTNMT.
3. **Không có ngưỡng cảnh báo.** `hcp` và `h_chophep` (mực nước hạ thấp cho
   phép) rỗng ở mọi lỗ khoan đã kiểm, nên không có căn cứ nào để đặt trạng
   thái. Lỗ khoan không bao giờ mang `trang_thai`.
4. **Hai nhóm thông số lệch nhau nhiều tháng.** Mực nước đo hàng ngày (mới
   nhất 06/10/2026) còn hóa học lấy mẫu vài lần một năm (13/05/2026) và nhiệt
   độ còn thưa hơn (25/12/2025). Vì vậy bản ghi mang thêm
   `thoi_diem_muc_nuoc` và `thoi_diem_chat_luong` bên cạnh `thoi_diem` chung;
   một mốc duy nhất sẽ làm số hóa học cũ trông như vừa đo xong.

### Vì sao mỗi bảng một cách lấy dòng mới nhất

`statement_timeout` là 15 giây, và cách viết sai đụng trần rất nhanh:

| Cách | Thời gian |
|---|---|
| `water_level`, `DISTINCT ON` | 8,5 s |
| `water_level`, `CROSS JOIN LATERAL` | **2,0 s** |
| `water_temperature`, `LATERAL` không lọc ngày | 7,9 s |
| `water_temperature`, `DISTINCT ON` + cửa sổ 730 ngày | **1,7 s** |

`water_level` có chỉ mục `well_code` nên `LATERAL` nhảy thẳng vào từng lỗ
khoan. `water_temperature` không có chỉ mục ghép phù hợp nên phải lọc trước
theo ngày để dùng `idx_watertemperature_datemeasure`. Cửa sổ ngày có thể bỏ
sót lỗ khoan lâu không đo, nên có thêm câu `nhiet_do_ngam_bu` chạy riêng cho
những mã còn thiếu; bình thường không mã nào thiếu nên câu đó không chạy.

Toàn bộ nhóm nước dưới đất mất khoảng **4,8 giây** (đo ở một tỉnh có 65 lỗ
khoan), nằm trong bộ nhớ đệm 60 giây nên chỉ lượt gọi đầu phải chờ.

## Nối với cơ sở dữ liệu QTQG thật

Mười sáu câu `SELECT` trong `truy_van.sql` (8 nước mặt, 8 nước dưới đất) **đã
viết xong và chạy thật** với cơ sở dữ liệu QTQG. Chỉ còn hai bước:

1. Điền thông tin kết nối vào `backend/.env`.
2. Đặt `CHE_DO=that`, khởi động lại dịch vụ, gọi `/api/suc-khoe` xem
   `csdl_ket_noi` có bằng `true` không.

Nếu QTQG đổi cấu trúc bảng, chạy lại script khảo sát (chỉ đọc, chỉ in ra):

```bash
D:\Anaconda_Data\envs\tainguyennuoc\python.exe backend/kiem_tra_ket_noi.py
```

Kết quả ghi ra `backend/schema_qtqg.md` (đã gitignore). Đối chiếu rồi sửa
`truy_van.sql` và `BANG_ANH_XA` trong `chuan_hoa.py`.

**Bắt buộc:** đối chiếu vài trạm với số liệu đọc trực tiếp trên phần mềm QTQG
trước khi coi là xong. Đó là cách duy nhất phát hiện ánh xạ cột sai, vì một cột
ánh xạ nhầm vẫn trả về số hợp lệ.

## Kiểm thử

```bash
cd backend
D:\Anaconda_Data\envs\tainguyennuoc\python.exe -m pytest tests -v
```

Toàn bộ chạy ở `CHE_DO=thu_nghiem`, **không test nào kết nối QTQG thật**.

Hai test phải giữ bằng mọi giá:

- `tests/test_ket_noi.py` quét văn bản toàn bộ `backend/` để chặn câu lệnh ghi
  lọt vào.
- `conftest.cac_chuoi_bi_mat()` quét mọi phản hồi API tìm địa chỉ máy chủ, tài
  khoản và mật khẩu. Nó đọc từ `cau_hinh`, không viết cứng giá trị vào test.

Các test lấy tọa độ mẫu từ `khung_bao_nen` trong `tinh.json` chứ không viết
cứng, nên khi sao dự án sang tỉnh khác chúng vẫn đúng.

`tests/test_vi_tri_diem.py` soi vị trí các lớp điểm trong `data/`. Hiện các lớp
chuyên đề của dự án này còn là dữ liệu mô phỏng nên toàn bộ nhóm đó **bỏ qua**
(skip); chúng đặt sẵn làm chốt chặn cho lúc nạp bộ kiểm kê thật, khi đó điền
`HO_MOC` rồi chạy lại.

## Triển khai lên máy chủ tỉnh

```bash
docker build -f backend/Dockerfile -t quan-trac-qtqg .
docker run --env-file backend/.env -p 8001:8001 quan-trac-qtqg
```

Dựng ảnh từ **thư mục gốc dự án**, không phải từ `backend/`, vì chế độ thử
nghiệm cần đọc `data/quan_trac.geojson` và `tinh.json`.

Hai việc phải làm khi lên máy chủ thật:

- Thêm tên miền thật vào `CORS_NGUON`.
- Sửa `CAU_HINH.api.goc` trong `assets/js/config.js` trỏ về địa chỉ dịch vụ.

**Không đặt dịch vụ này ra Internet công khai.** Nó giữ thông tin kết nối vào
một cơ sở dữ liệu ngành đang vận hành. Nếu bắt buộc phải mở ra ngoài thì đặt
sau reverse proxy có HTTPS và hạn chế theo địa chỉ IP.

## Cấu trúc mã nguồn

| Tệp | Việc |
|---|---|
| `main.py` | Tạo app, CORS, các endpoint |
| `cau_hinh.py` | Nơi **duy nhất** đọc biến môi trường |
| `ket_noi.py` | Mở kết nối chỉ đọc, chặn câu lệnh ghi |
| `nguon_qtqg.py` | **Lớp duy nhất biết schema QTQG.** Đổi nguồn chỉ sửa tệp này |
| `truy_van.sql` | Các câu SELECT, tách khỏi mã Python cho dễ soát |
| `chuan_hoa.py` | Ánh xạ tên cột nguồn sang tên trường nội bộ |
| `wqi.py` | Phân loại WQI theo QĐ 1460/QĐ-TCMT |
| `khong_gian.py` | Dựng GeoJSON, lọc theo phạm vi tỉnh |
| `tong_hop.py` | Gói số đo đúng schema `data/realtime.json` |
| `bo_nho_dem.py` | Bộ nhớ đệm TTL |
| `luu_tru.py` | Tích lũy chuỗi thời gian vào SQLite cục bộ |

## Tính chỉ số WQI

`wqi.py` cài đặt đầy đủ VN_WQI theo Quyết định 1460/QĐ-TCMT ngày 12/11/2019.
Bản gốc để đối chiếu: `CSDL/WQI_1460_QD-TCMT_428277.doc`.

Thứ tự ưu tiên trong `gan_wqi()`:

1. QTQG có sẵn cột WQI hợp lệ thì **dùng số của QTQG**, không tính lại. Cơ quan
   chủ quản là nơi công bố số chính thức; tính lại rồi ra số khác sẽ gây mâu
   thuẫn giữa hai hệ thống.
2. Không có thì tự tính, với điều kiện đủ dữ liệu theo mục 2.1.b: tối thiểu 3
   trên 5 nhóm, bắt buộc có nhóm IV, và nhóm IV có tối thiểu 3 thông số.
3. Không đủ điều kiện thì **để khuyết**, kèm `wqi_ly_do` và
   `wqi_thieu_thong_so`. Không bao giờ đoán một con số.

Bản ghi tự tính mang thêm cờ `wqi_tu_tinh: true`, và giao diện nói rõ điều đó
trong hộp thoại chi tiết trạm.

Nhóm nào không có số liệu thì thừa số của nó bị **bỏ hẳn** khỏi tích, không
phải coi là 100 hay 0.

### Một sai sót trong ví dụ mẫu của quyết định

Mục 2.3 của quyết định có một ví dụ tính mẫu. **Mười một giá trị WQI từng thông
số trong ví dụ đó đều tái lập được chính xác** bằng mã nguồn này (xem
`tests/test_wqi.py`). Nhưng hai con số tổng hợp cuối cùng thì không: quyết định
in ra 16 và 19, trong khi thay chính các con số của nó vào chính công thức in
ngay phía trên lại ra 34,59 và 40,44.

```
100/100 x (100x100)^(1/2)/100 x (100x75)^(1/2)/100
        x [ (73,3+37,5+58,3+100+50)/5 x 25 ]^(1/2)
  = 1 x 1 x 0,866 x 39,94 = 34,59
```

Mã nguồn bám theo **công thức**, vì đó mới là phần quy phạm (mục 2.2.b). Đừng
sửa hàm tính để ép ra 16 và 19.
