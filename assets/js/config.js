/* ==========================================================================
   config.js - Cau hinh trung tam cua he thong
   --------------------------------------------------------------------------
   Day la noi duy nhat can sua khi them lop du lieu moi hoac doi ky hieu.
   Moi lop khai bao: ten, ten tep, kieu hinh hoc, ky hieu, danh sach truong
   thuoc tinh va chu giai. Cac tep JS khac chi doc cau hinh nay.

   Tep nay dung CHUNG cho moi tinh. Nhung gi khac nhau giua cac tinh, nhu ten
   tinh, pham vi ban do hay danh sach lop co san, nam trong tinh/<ma>.json.
   Truong "tep" chi ghi ten tep; duong dan day du do ham duong_dan_du_lieu()
   trong tinh.js ghep lai thanh data/<ma_tinh>/<ten tep>.
   ========================================================================== */

/* --------------------------------------------------------------------------
   Bang mau trang thai, dung chung cho toan he thong
   -------------------------------------------------------------------------- */
const MAU = {
  tot:      '#16a34a',   // con kha nang / binh thuong
  theo_doi: '#f59e0b',   // gan nguong / can theo doi
  xau:      '#dc2626',   // vuot nguong / canh bao
  tran:     '#7c3aed',   // ho gan tran
  trung_tinh: '#64748b',
  song:     '#1572a1',
  mat_nuoc: '#4cadd4',
  luu_vuc:  '#3d8fa8',
  /* Ho ao dam khong duoc san lap. Mau rieng, KHONG dung lai mat_nuoc: hai lop
     nam canh nhau trong cung mot nhom ma mot ben la du lieu that, mot ben la
     mo phong, trung mau la nguoi xem khong phan biet duoc. */
  ao_ho_giu: '#0f766e',
};

/* Mau theo phan loai WQI, dung NGUYEN ma mau RGB cua bang o muc 1.4 Quyet dinh
   1460/QD-TCMT (ban goc: CSDL/dulieu_thuc/WQI_1460_QD-TCMT_428277.doc). Khoa la
   dung chuoi ma phan_loai_wqi() cua backend/wqi.py tra ve. Khong tu doi sac
   do: nguoi lam quan trac doc ban do theo dung sau mau nay. */
const MAU_WQI = {
  'Rất tốt': '#3333ff',            // 91 - 100, xanh nuoc bien
  'Tốt': '#00e400',                // 76 - 90, xanh la cay
  'Trung bình': '#ffff00',         // 51 - 75, vang
  'Xấu': '#ff7e00',                // 26 - 50, da cam
  'Kém': '#ff0000',                // 10 - 25, do
  'Ô nhiễm rất nặng': '#7e0023',   // duoi 10, nau
};

/* --------------------------------------------------------------------------
   Ham dinh dang gia tri hien thi
   -------------------------------------------------------------------------- */
const DINH_DANG = {
  chu: function (v) {
    return (v === null || v === undefined || v === '') ? null : String(v);
  },

  so: function (v) {
    if (v === null || v === undefined || v === '') return null;
    return Number(v).toLocaleString('vi-VN');
  },

  so_le: function (v) {
    if (v === null || v === undefined || v === '') return null;
    return Number(v).toLocaleString('vi-VN', { maximumFractionDigits: 2 });
  },

  phan_tram: function (v) {
    if (v === null || v === undefined || v === '') return null;
    return (Number(v) * 100).toLocaleString('vi-VN', { maximumFractionDigits: 1 }) + '%';
  },

  ngay: function (v) {
    if (!v) return null;
    var d = new Date(v);
    if (isNaN(d.getTime())) return String(v);
    return d.toLocaleDateString('vi-VN');
  },
};

/* Dinh dang mot gia tri theo khai bao truong, co kem don vi */
function dinh_dang_gia_tri(truong, gia_tri) {
  var ham = DINH_DANG[truong.dinh_dang || 'chu'] || DINH_DANG.chu;
  var ket_qua = ham(gia_tri);
  if (ket_qua === null) return null;
  return truong.don_vi ? ket_qua + ' ' + truong.don_vi : ket_qua;
}

/* --------------------------------------------------------------------------
   Cau hinh chinh
   -------------------------------------------------------------------------- */
const CAU_HINH = {

  he_thong: {
    /* Ten tinh, don vi chu quan va pham vi ban do nay nam trong tinh/<ma>.json
       va duoc truy cap qua bien toan cuc TINH. Khong dat o day nua vi moi tinh
       mot khac, trong khi tep config.js thi dung chung cho moi tinh. */
    phien_ban: '1.0.0',
    /* Chu ky lam moi du lieu quan trac, don vi phut */
    chu_ky_lam_moi_phut: 10,
  },

  /* ---------------- Backend trung gian quan trac QTQG ----------------
     Chi trang pages/quan-trac.html dung khoi nay. Trang ban do van doc
     data/realtime.json nhu cu, khong goi dich vu nao.

     goc de RONG nghia la tu suy: lay hostname dang mo cong voi cong.backend
     trong tinh.json. Nho vay moi tinh mot cap cong rieng ma khong phai sua
     tep nay, xem dia_chi_backend() trong assets/js/tinh.js.

     Khi len may chu that thi dien dia chi day du vao day, vi du
     'https://quantrac.khanhhoa.gov.vn'. Sua DUNG MOT dong nay. */
  api: {
    goc: '',
    chu_ky_lam_moi_phut: 5,
    het_gio_ms: 15000,
  },

  /* Thiet dat ban do dung chung cho moi tinh. Tam va pham vi thi rieng tung
     tinh nen nam trong tinh/<ma>.json. */
  ban_do_chung: {
    zoom_min: 6,
    zoom_max: 18,
  },

  /* ---------------- Ban do nen ---------------- */
  ban_do_nen: [
    /* Luu y khi doi nguon tile: nhieu dich vu mien phi truoc day (vi du CARTO
       basemaps) nay da yeu cau API key. Cac nguon duoi day dung duoc truc tiep
       khong can dang ky, phu hop cho mot trang tinh tren GitHub Pages. */
    {
      ma: 'sang', ten: 'Nền sáng', mac_dinh: true,
      url: 'https://server.arcgisonline.com/ArcGIS/rest/services/Canvas/World_Light_Gray_Base/MapServer/tile/{z}/{y}/{x}',
      ghi_nguon: 'Nền bản đồ: Esri, HERE, Garmin, &copy; OpenStreetMap contributors',
      zoom_max: 16,
    },
    {
      ma: 'duong_pho', ten: 'Đường phố',
      url: 'https://tile.openstreetmap.org/{z}/{x}/{y}.png',
      ghi_nguon: '&copy; OpenStreetMap contributors',
      zoom_max: 19,
    },
    {
      ma: 've_tinh', ten: 'Ảnh vệ tinh',
      url: 'https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}',
      ghi_nguon: 'Nguồn ảnh: Esri, Maxar, Earthstar Geographics',
      zoom_max: 18,
    },
    {
      ma: 'dia_hinh', ten: 'Địa hình',
      url: 'https://{s}.tile.opentopomap.org/{z}/{x}/{y}.png',
      ghi_nguon: 'Bản đồ: &copy; OpenTopoMap (CC-BY-SA)',
      zoom_max: 17,
    },
    {
      /* Nen dung tu du lieu dia phuong, khong goi dich vu ngoai nao.
         Dia danh bang tieng Viet, co san song suoi dang vung va mat nuoc.
         Cac tep chi duoc tai ve khi nguoi dung chon nen nay. */
      ma: 'dia_phuong', ten: 'Nền địa phương', kieu: 'vector',
      ghi_nguon: 'Bản đồ nền quốc gia (BaseMapVietNam.gdb), cắt theo phạm vi tỉnh',
    },
    {
      ma: 'toi', ten: 'Nền tối',
      url: 'https://server.arcgisonline.com/ArcGIS/rest/services/Canvas/World_Dark_Gray_Base/MapServer/tile/{z}/{y}/{x}',
      ghi_nguon: 'Nền bản đồ: Esri, HERE, Garmin, &copy; OpenStreetMap contributors',
      zoom_max: 16,
    },
  ],

  /* ---------------- Nen ban do dung tu du lieu dia phuong ----------------
     Cac tep nay sinh ra tu scripts/04_tao_nen_dia_phuong.py, cat tu bo ban do
     nen quoc gia BaseMapVietNam.gdb theo pham vi dat lien cua tinh.
     Lop "dat" dung lai chinh tep ranh gioi xa nen khong ton them dung luong:
     no phu mau dat len nen bien, cac lop con lai ve chong len tren. */
  nen_vector: {
    mau_bien: '#cfe7f2',
    mau_bien_toi: '#16313d',
    lop: [
      { ma: 'dat', ten: 'Phần đất liền', tep: 'ranh_gioi_xa.geojson',
        z: 205, kieu_ve: { color: '#e2ddd2', weight: 0.6, opacity: 0.9,
                           fillColor: '#f4f1e8', fillOpacity: 1 } },

      { ma: 'rung', ten: 'Rừng', tep: 'nen/rung.geojson',
        z: 210, kieu_ve: { stroke: false, fillColor: '#cfe3c4', fillOpacity: 0.95 } },

      { ma: 'bao_ton', ten: 'Vườn quốc gia, khu bảo tồn', tep: 'nen/bao_ton.geojson',
        z: 215, kieu_ve: { color: '#5f9150', weight: 1, opacity: 0.8, dashArray: '4 3',
                           fillColor: '#b9d9ab', fillOpacity: 0.5 } },

      { ma: 'mat_nuoc', ten: 'Mặt nước', tep: 'nen/mat_nuoc.geojson',
        z: 220, kieu_ve: { color: '#6ba8c7', weight: 0.6, opacity: 0.9,
                           fillColor: '#a9d6ea', fillOpacity: 1 } },

      { ma: 'song_vung', ten: 'Sông, suối dạng vùng', tep: 'nen/song_vung.geojson',
        z: 225, kieu_ve: { color: '#6ba8c7', weight: 0.6, opacity: 0.9,
                           fillColor: '#a9d6ea', fillOpacity: 1 } },

      /* Duong bo to mau theo cap: quoc lo dam nhat, duong do thi nhat nhat */
      { ma: 'duong_bo', ten: 'Đường bộ', tep: 'nen/duong_bo.geojson',
        z: 230, zoom_min: 9,
        kieu_ve: function (p) {
          if (p.loaiduongbo === 1) return { color: '#e09b3d', weight: 2.4, opacity: 0.95 };
          if (p.loaiduongbo === 2) return { color: '#edc383', weight: 1.6, opacity: 0.9 };
          return { color: '#d8d4cc', weight: 1.0, opacity: 0.9 };
        } },

      /* Hai lop nhan chu. Trong pham vi tinh co 658 dia danh va 1.432
         diem dan cu, phan lon la thon, lang. Neu hien tu zoom 12 thi chu
         chong len nhau day dac. Dat nguong rieng: dia danh son van thua
         hon nen cho hien som hon mot muc. */
      { ma: 'dia_danh', ten: 'Địa danh', tep: 'nen/dia_danh.geojson',
        z: 240, zoom_min: 13, nhan: 'ten', mau_nhan: '#6b6150',
        kieu_ve: { radius: 1.5, fillColor: '#8a7f6b', color: '#8a7f6b',
                   weight: 0, fillOpacity: 0.8 } },

      { ma: 'dan_cu', ten: 'Điểm dân cư', tep: 'nen/dan_cu.geojson',
        z: 245, zoom_min: 14, nhan: 'ten', mau_nhan: '#4a4a4a',
        kieu_ve: { radius: 2, fillColor: '#777', color: '#fff',
                   weight: 0.8, fillOpacity: 1 } },
    ],
  },

  /* ---------------- Nhom lop trong cay du lieu ---------------- */
  nhom_lop: [
    { ma: 'hanh_chinh', ten: 'Nền và hành chính', mo: true,
      lop: ['ranh_gioi_tinh', 'ranh_gioi_xa'] },
    { ma: 'kiem_ke', ten: 'Kiểm kê nguồn nước mặt', mo: true,
      lop: ['luu_vuc', 'mat_nuoc', 'ao_ho', 'ao_ho_khong_san_lap', 'song_suoi',
            'ho_chua'] },
    { ma: 'khai_thac_xa_thai', ten: 'Khai thác và xả thải', mo: true,
      lop: ['khai_thac', 'xa_thai'] },
    { ma: 'giam_sat', ten: 'Quan trắc và sức chịu tải', mo: true,
      lop: ['doan_song', 'quan_trac', 'quan_trac_dia_phuong', 'quan_trac_ndd'] },
  ],

  /* ---------------- Dinh nghia tung lop ---------------- */
  lop: {

    /* ===== Ranh gioi hanh chinh (du lieu that) ===== */
    ranh_gioi_tinh: {
      ten: 'Ranh giới tỉnh',
      tep: 'ranh_gioi_tinh.geojson',
      kieu: 'vung',
      hien: true,
      z: 420,
      khoa: 'ma',
      truong_nhan: 'ten',
      du_lieu_that: true,
      khong_truy_van: true,      /* khong tham gia truy van click */
      mo_ta: 'Địa giới hành chính cấp tỉnh sau sáp nhập, hiệu lực từ 01/07/2025',
      kieu_ve: function () {
        return { color: '#475569', weight: 1.8, opacity: 0.85, fill: false,
                 dashArray: null, interactive: false };
      },
      truong: [
        { ma: 'ten', ten: 'Tên đơn vị' },
        { ma: 'dien_tich_km2', ten: 'Diện tích', dinh_dang: 'so_le', don_vi: 'km²' },
        { ma: 'dan_so', ten: 'Dân số', dinh_dang: 'so', don_vi: 'người' },
        { ma: 'hop_thanh_tu', ten: 'Hợp thành từ' },
        { ma: 'trung_tam_hc', ten: 'Trung tâm hành chính' },
      ],
      cot_bang: ['ten', 'dien_tich_km2', 'dan_so', 'hop_thanh_tu'],
      chu_giai: [{ kieu: 'duong', mau: '#475569', nhan: 'Địa giới tỉnh' }],
    },

    /* ===== Ranh gioi cap xa (du lieu that) ===== */
    ranh_gioi_xa: {
      ten: 'Ranh giới xã, phường',
      tep: 'ranh_gioi_xa.geojson',
      kieu: 'vung',
      hien: true,
      z: 405,
      khoa: 'ma',
      truong_nhan: 'ten',
      du_lieu_that: true,
      mo_ta: 'Ranh giới các xã, phường, đặc khu của tỉnh sau sáp nhập',
      kieu_ve: function () {
        return { color: '#94a3b8', weight: 0.8, opacity: 0.75,
                 fillColor: '#94a3b8', fillOpacity: 0.04 };
      },
      truong: [
        { ma: 'ten', ten: 'Tên đơn vị' },
        { ma: 'phan_loai', ten: 'Phân loại' },
        { ma: 'tinh', ten: 'Thuộc tỉnh' },
        { ma: 'dien_tich_km2', ten: 'Diện tích', dinh_dang: 'so_le', don_vi: 'km²' },
        { ma: 'dan_so', ten: 'Dân số', dinh_dang: 'so', don_vi: 'người' },
      ],
      cot_bang: ['ma', 'ten', 'phan_loai', 'dien_tich_km2', 'dan_so'],
      chu_giai: [{ kieu: 'vung', mau: '#94a3b8', nhan: 'Ranh giới xã, phường' }],
    },

    /* ===== Luu vuc song ===== */
    luu_vuc: {
      ten: 'Ranh giới lưu vực sông',
      tep: 'luu_vuc.geojson',
      kieu: 'vung',
      hien: true,
      z: 400,
      khoa: 'ma',
      truong_nhan: 'ten',
      mo_ta: 'Ranh giới các lưu vực sông trên địa bàn tỉnh (lưu vực sông chính quốc gia, cắt theo ranh giới tỉnh)',
      kieu_ve: function () {
        return { color: MAU.luu_vuc, weight: 1.4, opacity: 0.8, dashArray: '5 4',
                 fillColor: MAU.luu_vuc, fillOpacity: 0.08 };
      },
      truong: [
        { ma: 'ten', ten: 'Tên lưu vực' },
        { ma: 'dien_tich_trong_tinh_km2', ten: 'Diện tích trong tỉnh', dinh_dang: 'so_le', don_vi: 'km²' },
        { ma: 'dien_tich_km2', ten: 'Diện tích toàn lưu vực', dinh_dang: 'so_le', don_vi: 'km²' },
      ],
      cot_bang: ['ma', 'ten', 'dien_tich_trong_tinh_km2', 'dien_tich_km2'],
      chu_giai: [{ kieu: 'vung', mau: MAU.luu_vuc, nhan: 'Lưu vực sông' }],
    },

    /* ===== Ao, ho, dam tu nhien ===== */
    mat_nuoc: {
      ten: 'Ao, hồ, đầm tự nhiên',
      tep: 'mat_nuoc.geojson',
      kieu: 'vung',
      hien: true,
      z: 410,
      khoa: 'ma',
      truong_nhan: 'ten',
      mo_ta: 'Các vùng mặt nước tự nhiên: đầm, ao, hồ, bàu',
      kieu_ve: function () {
        return { color: '#2d7d9a', weight: 1, opacity: 0.9,
                 fillColor: MAU.mat_nuoc, fillOpacity: 0.55 };
      },
      truong: [
        { ma: 'ten', ten: 'Tên' },
        { ma: 'loai', ten: 'Loại hình' },
        { ma: 'dien_tich_ha', ten: 'Diện tích', dinh_dang: 'so_le', don_vi: 'ha' },
        { ma: 'ten_luu_vuc', ten: 'Lưu vực' },
      ],
      cot_bang: ['ma', 'ten', 'loai', 'dien_tich_ha', 'ten_luu_vuc'],
      chu_giai: [{ kieu: 'vung', mau: MAU.mat_nuoc, nhan: 'Mặt nước tự nhiên' }],
    },

    /* ===== Song, suoi ===== */
    song_suoi: {
      ten: 'Sông, suối',
      tep: 'song_suoi.geojson',
      kieu: 'duong',
      hien: true,
      z: 440,
      khoa: 'ma',
      truong_nhan: 'ten',
      nhan_tren_ban_do: true,
      nhan_dieu_kien: function (p) { return p.cap_song === 'Cấp I'; },
      mo_ta: 'Mạng lưới sông, suối theo kết quả kiểm kê nguồn nước mặt',
      /* Cap theo ma song: 22 la cap I, 22.1 la cap II, 22.3.1 la cap III ... */
      kieu_ve: function (p) {
        var day = p.cap_song === 'Cấp I' ? 4.2 : (p.cap_song === 'Cấp II' ? 2.6 : 1.5);
        return { color: MAU.song, weight: day, opacity: 0.9, lineCap: 'round' };
      },
      truong: [
        { ma: 'ten', ten: 'Tên sông, suối' },
        { ma: 'cap_song', ten: 'Cấp sông' },
        { ma: 'ma_song_goc', ten: 'Mã sông kiểm kê' },
        { ma: 'chay_ra', ten: 'Chảy ra' },
        { ma: 'chieu_dai_km', ten: 'Chiều dài', dinh_dang: 'so_le', don_vi: 'km' },
        { ma: 'vi_tri_dau', ten: 'Vị trí đầu' },
        { ma: 'vi_tri_cuoi', ten: 'Vị trí cuối' },
        { ma: 'ten_luu_vuc', ten: 'Lưu vực' },
      ],
      cot_bang: ['ma', 'ten', 'cap_song', 'chay_ra', 'chieu_dai_km', 'ten_luu_vuc'],
      chu_giai: [
        { kieu: 'duong', mau: MAU.song, nhan: 'Sông, suối cấp I (đổ ra biển)', day: 4 },
        { kieu: 'duong', mau: MAU.song, nhan: 'Cấp II', day: 2.5 },
        { kieu: 'duong', mau: MAU.song, nhan: 'Cấp III trở xuống', day: 1.5 },
      ],
    },

    /* ===== Ho chua, dap dang ===== */
    ho_chua: {
      ten: 'Hồ chứa, đập dâng',
      tep: 'ho_chua.geojson',
      kieu: 'diem',
      hien: true,
      z: 450,
      khoa: 'ma',
      truong_nhan: 'ten',
      nhan_tren_ban_do: true,
      realtime: true,          /* ghep voi du lieu quan trac thoi gian thuc */
      mo_ta: 'Hồ chứa và đập dâng, tô màu theo tỷ lệ dung tích hữu ích hiện tại',
      /* Ban kinh theo dung tich, mau theo ty le tich nuoc thoi gian thuc */
      kieu_ve: function (p, rt) {
        var w = p.w_toan_bo_trieu_m3 || 1;
        var bk = Math.max(5, Math.min(14, 4 + Math.sqrt(w) * 1.2));
        var mau = MAU.trung_tinh;
        if (rt) {
          var tl = rt.ty_le_dung_tich;
          if (tl > 0.95) mau = MAU.tran;
          else if (tl < 0.30) mau = MAU.xau;
          else if (tl < 0.50) mau = MAU.theo_doi;
          else mau = MAU.tot;
        }
        return { radius: bk, fillColor: mau, color: '#ffffff', weight: 1.6,
                 opacity: 1, fillOpacity: 0.9 };
      },
      truong: [
        { ma: 'ten', ten: 'Tên hồ' },
        { ma: 'ten_luu_vuc', ten: 'Lưu vực' },
        { ma: 'w_toan_bo_trieu_m3', ten: 'Dung tích toàn bộ', dinh_dang: 'so_le', don_vi: 'triệu m³' },
        { ma: 'w_huu_ich_trieu_m3', ten: 'Dung tích hữu ích', dinh_dang: 'so_le', don_vi: 'triệu m³' },
        { ma: 'h_nguong_tran_m', ten: 'Cao trình ngưỡng tràn', dinh_dang: 'so_le', don_vi: 'm' },
        { ma: 'nam_hoan_thanh', ten: 'Năm hoàn thành' },
        { ma: 'muc_dich', ten: 'Mục đích' },
        { ma: 'don_vi_quan_ly', ten: 'Đơn vị quản lý' },
      ],
      cot_bang: ['ma', 'ten', 'w_toan_bo_trieu_m3', 'w_huu_ich_trieu_m3', 'h_nguong_tran_m', 'ten_luu_vuc'],
      chu_giai: [
        { kieu: 'diem', mau: MAU.tot, nhan: 'Dung tích 50 - 95%' },
        { kieu: 'diem', mau: MAU.theo_doi, nhan: 'Dung tích 30 - 50%' },
        { kieu: 'diem', mau: MAU.xau, nhan: 'Dung tích dưới 30%' },
        { kieu: 'diem', mau: MAU.tran, nhan: 'Trên 95%, gần ngưỡng tràn' },
      ],
    },

    /* ===== Ho, ao, dam khong duoc san lap (danh muc phap ly, du lieu that) =====
       KHONG gop voi lop mat_nuoc o tren. Hai lop nghe giong nhau nhung khac
       han: mat_nuoc la "Ao, ho, dam tu nhien" va dang la DU LIEU MO PHONG,
       con lop nay la danh muc tinh cong bo va la DU LIEU THAT. Tron vao nhau
       la mat ranh gioi that/mo phong ma ca du an dang giu.

       Sinh boi scripts/09_chuan_hoa_ao_ho_khong_san_lap.py. Cac truong duoi
       day la toan bo truong script co the sinh ra; CSV nguon thieu cot nao
       thi truong do khuyet, giao dien tu bo qua. */
    ao_ho_khong_san_lap: {
      ten: 'Hồ, ao, đầm không được san lấp',
      tep: 'ao_ho_khong_san_lap.geojson',
      kieu: 'diem',
      hien: true,
      z: 455,                  /* tren ho_chua 450, duoi khai_thac 460 */
      khoa: 'ma',
      truong_nhan: 'ten',
      du_lieu_that: true,
      mo_ta: 'Danh mục hồ, ao, đầm không được san lấp do tỉnh công bố',
      /* Ban kinh theo dien tich mat nuoc, cung cach ho_chua lam voi dung tich.
         Dien tich trai rong tu vai ha den hang nghin ha nen lay can bac hai,
         neu khong thi mot cai dam lam moi diem con lai thanh cham nho. */
      kieu_ve: function (p) {
        var s = p.dien_tich_ha || 0;
        var bk = Math.max(5, Math.min(13, 4.5 + Math.sqrt(s) * 0.5));
        return { radius: bk, fillColor: MAU.ao_ho_giu, color: '#ffffff',
                 weight: 1.6, opacity: 1, fillOpacity: 0.9 };
      },
      truong: [
        { ma: 'ten', ten: 'Tên hồ, ao, đầm' },
        { ma: 'vi_tri_hc', ten: 'Vị trí, địa điểm' },
        { ma: 'dien_tich_ha', ten: 'Diện tích mặt nước', dinh_dang: 'so_le', don_vi: 'ha' },
        { ma: 'chuc_nang', ten: 'Mục đích sử dụng' },
        { ma: 'don_vi_quan_ly', ten: 'Đơn vị quản lý' },
        { ma: 'nam_xd', ten: 'Năm xây dựng, hoàn thành' },
        { ma: 'quyet_dinh', ten: 'Căn cứ pháp lý' },
        { ma: 'ghi_chu', ten: 'Ghi chú' },
      ],
      cot_bang: ['ma', 'ten', 'vi_tri_hc', 'dien_tich_ha', 'chuc_nang',
                 'don_vi_quan_ly'],
      chu_giai: [
        { kieu: 'diem', mau: MAU.ao_ho_giu,
          nhan: 'Hồ, ao, đầm không được san lấp' },
      ],
    },

    /* ===== Ao, ho thuc (ket qua kiem ke) =====
       DU LIEU THAT. Tep ao_ho.geojson co hai kieu, khoi nay khai bao truong
       cua ca hai; truong nao tep khong co thi giao dien tu bo qua.

       Kieu cu, scripts/05_chuan_hoa_chuyen_de.py: cac cong trinh khai thac co
       loai hinh "Ho" tach tu bang khai thac, mang luu luong khai thac.
       Kieu moi, scripts/12_nap_ao_ho_kiem_ke.py: danh muc nguon nuoc (ho, ao,
       dam) cua ban ra soat kiem ke, mang dien tich va dung tich, KHONG co luu
       luong; khi do ho khai thac nam o lop khai_thac. Tep kieu moi mang dau
       "sinh_boi" o cap FeatureCollection. */
    ao_ho: {
      ten: 'Ao, hồ, hồ chứa (kiểm kê)',
      tep: 'ao_ho.geojson',
      kieu: 'diem',
      hien: true,
      z: 453,
      khoa: 'ma',
      truong_nhan: 'ten_cong_trinh',
      du_lieu_that: true,
      mo_ta: 'Hồ, ao, đầm và hồ chứa theo kết quả kiểm kê nguồn nước mặt',
      kieu_ve: function (p) {
        var v = p.dung_tich_ho_trieu_m3 || 0;
        var bk = Math.max(3.5, Math.min(8, 3.5 + Math.sqrt(v) * 0.9));
        var mau = String(p.loai_hinh || '').indexOf('thủy điện') >= 0 ? '#2563eb' : '#0b5e72';
        return { radius: bk, fillColor: mau, color: '#ffffff', weight: 1,
                 opacity: 1, fillOpacity: 0.9 };
      },
      truong: [
        { ma: 'ten_cong_trinh', ten: 'Tên hồ' },
        { ma: 'loai_hinh', ten: 'Loại hình' },
        { ma: 'muc_dich_su_dung', ten: 'Mục đích sử dụng' },
        { ma: 'nguon_nuoc_khai_thac', ten: 'Nguồn nước' },
        { ma: 'xa_phuong', ten: 'Xã, phường' },
        { ma: 'dien_tich_mat_nuoc_m2', ten: 'Diện tích mặt nước', dinh_dang: 'so', don_vi: 'm²' },
        { ma: 'dung_tich_ho_trieu_m3', ten: 'Dung tích hồ chứa', dinh_dang: 'so_le', don_vi: 'triệu m³' },
        { ma: 'dung_tich_huu_ich_trieu_m3', ten: 'Dung tích hữu ích', dinh_dang: 'so_le', don_vi: 'triệu m³' },
        { ma: 'luu_vuc_kiem_ke', ten: 'Thuộc hệ thống sông' },
        { ma: 'ghi_chu', ten: 'Ghi chú' },
        { ma: 'q_tuoi_m3s', ten: 'Lưu lượng tưới', dinh_dang: 'so_le', don_vi: 'm³/s' },
        { ma: 'q_san_xuat_m3_ngay', ten: 'Lưu lượng sản xuất', dinh_dang: 'so', don_vi: 'm³/ngày' },
        { ma: 'q_khac_m3_ngay', ten: 'Lưu lượng mục đích khác', dinh_dang: 'so', don_vi: 'm³/ngày' },
        { ma: 'cong_suat_dien_kw', ten: 'Công suất phát điện', dinh_dang: 'so', don_vi: 'kW' },
        { ma: 'q_khai_thac_m3_ngay', ten: 'Tổng lưu lượng khai thác quy đổi', dinh_dang: 'so', don_vi: 'm³/ngày' },
        { ma: 'ten_luu_vuc', ten: 'Lưu vực' },
      ],
      cot_bang: ['ma', 'ten_cong_trinh', 'loai_hinh', 'muc_dich_su_dung',
                 'dung_tich_ho_trieu_m3', 'xa_phuong', 'ten_luu_vuc'],
      chu_giai: [
        { kieu: 'diem', mau: '#0b5e72', nhan: 'Hồ chứa, hồ chứa thủy lợi' },
        { kieu: 'diem', mau: '#2563eb', nhan: 'Hồ thủy điện' },
      ],
    },

    /* ===== Cong trinh khai thac, su dung nuoc ===== */
    khai_thac: {
      ten: 'Công trình khai thác',
      tep: 'khai_thac.geojson',
      kieu: 'diem',
      hien: true,
      z: 460,
      khoa: 'ma',
      truong_nhan: 'ten_cong_trinh',
      mo_ta: 'Công trình khai thác, sử dụng nước mặt theo kết quả kiểm kê (đập dâng, trạm bơm, trạm cấp nước, cống; hồ chứa nằm ở lớp Ao, hồ, hồ chứa)',
      /* Cong trinh khai thac luon la hinh vuong, mau van theo loai cong trinh */
      ky_hieu: { hinh: 'vuong' },
      /* Mau theo nhom cong trinh, ban kinh theo luu luong khai thac quy doi */
      kieu_ve: function (p) {
        var loai = String(p.loai_hinh || '');
        var mau = '#64748b';
        if (loai.indexOf('Đập') === 0) mau = '#0f766e';
        else if (loai.indexOf('Trạm bơm') === 0) mau = '#7c3aed';
        else if (loai.indexOf('Trạm cấp nước') === 0) mau = '#2563eb';
        var q = p.q_khai_thac_m3_ngay || 100;
        var bk = Math.max(3, Math.min(7, 1.5 + Math.log10(q) * 1.1));
        return { radius: bk, fillColor: mau, color: '#ffffff', weight: 1,
                 opacity: 1, fillOpacity: 0.9 };
      },
      truong: [
        { ma: 'ten_cong_trinh', ten: 'Tên công trình' },
        { ma: 'loai_hinh', ten: 'Loại công trình' },
        { ma: 'muc_dich_su_dung', ten: 'Mục đích sử dụng' },
        { ma: 'nguon_nuoc_khai_thac', ten: 'Nguồn nước khai thác' },
        { ma: 'xa_phuong', ten: 'Xã, phường' },
        { ma: 'dung_tich_ho_trieu_m3', ten: 'Dung tích hồ chứa', dinh_dang: 'so_le', don_vi: 'triệu m³' },
        { ma: 'q_tuoi_m3s', ten: 'Lưu lượng tưới', dinh_dang: 'so_le', don_vi: 'm³/s' },
        { ma: 'q_san_xuat_m3_ngay', ten: 'Lưu lượng sản xuất', dinh_dang: 'so', don_vi: 'm³/ngày' },
        { ma: 'q_khac_m3_ngay', ten: 'Lưu lượng mục đích khác', dinh_dang: 'so', don_vi: 'm³/ngày' },
        { ma: 'cong_suat_dien_kw', ten: 'Công suất phát điện', dinh_dang: 'so', don_vi: 'kW' },
        { ma: 'q_khai_thac_m3_ngay', ten: 'Tổng lưu lượng khai thác quy đổi', dinh_dang: 'so', don_vi: 'm³/ngày' },
        { ma: 'ten_luu_vuc', ten: 'Lưu vực' },
      ],
      cot_bang: ['ma', 'ten_cong_trinh', 'loai_hinh', 'muc_dich_su_dung',
                 'xa_phuong', 'q_khai_thac_m3_ngay', 'ten_luu_vuc'],
      chu_giai: [
        { kieu: 'diem', mau: '#0f766e', nhan: 'Đập dâng' },
        { kieu: 'diem', mau: '#7c3aed', nhan: 'Trạm bơm' },
        { kieu: 'diem', mau: '#2563eb', nhan: 'Trạm cấp nước' },
        { kieu: 'diem', mau: '#64748b', nhan: 'Cống và loại khác' },
      ],
    },

    /* ===== Diem xa nuoc thai ===== */
    xa_thai: {
      ten: 'Điểm xả nước thải',
      tep: 'xa_thai.geojson',
      kieu: 'diem',
      hien: true,
      z: 470,
      khoa: 'ma',
      truong_nhan: 'ten_cong_trinh',
      mo_ta: 'Các điểm xả nước thải vào nguồn nước theo kết quả kiểm kê',
      /* Diem xa thai luon la hinh tam giac, mau van theo loai nguon thai */
      ky_hieu: { hinh: 'tam_giac' },
      kieu_ve: function (p) {
        var mau = '#ea580c';
        if (p.nguon_thai === 'Y tế') mau = '#be185d';
        else if (p.nguon_thai === 'Sinh hoạt') mau = '#2563eb';
        var q = p.q_xa_m3_ngay || 100;
        var bk = Math.max(3, Math.min(7, 1.5 + Math.log10(q) * 1.1));
        return { radius: bk, fillColor: mau, color: '#ffffff', weight: 1,
                 opacity: 1, fillOpacity: 0.9 };
      },
      truong: [
        { ma: 'ten_cong_trinh', ten: 'Tên cơ sở' },
        { ma: 'nguon_thai', ten: 'Loại nguồn thải' },
        { ma: 'nguon_tiep_nhan', ten: 'Nguồn tiếp nhận' },
        { ma: 'xa_phuong', ten: 'Xã, phường' },
        { ma: 'q_xa_m3_ngay', ten: 'Lưu lượng xả', dinh_dang: 'so', don_vi: 'm³/ngày' },
        { ma: 'ten_luu_vuc', ten: 'Lưu vực' },
      ],
      cot_bang: ['ma', 'ten_cong_trinh', 'nguon_thai', 'nguon_tiep_nhan',
                 'xa_phuong', 'q_xa_m3_ngay'],
      chu_giai: [
        { kieu: 'diem', mau: '#ea580c', nhan: 'Sản xuất công nghiệp' },
        { kieu: 'diem', mau: '#be185d', nhan: 'Y tế' },
        { kieu: 'diem', mau: '#2563eb', nhan: 'Sinh hoạt' },
      ],
    },

    /* ===== Phan doan song danh gia suc chiu tai ===== */
    doan_song: {
      ten: 'Sức chịu tải đoạn sông',
      tep: 'doan_song.geojson',
      kieu: 'duong',
      hien: false,
      z: 430,
      khoa: 'ma',
      truong_nhan: 'ten_doan',
      mo_ta: 'Khả năng tiếp nhận nước thải theo thông số BOD5, '
           + 'đánh giá theo TT 76/2017/TT-BTNMT',
      kieu_ve: function (p) {
        var mau = MAU.tot;
        if (p.trang_thai === 'Không còn khả năng tiếp nhận') mau = MAU.xau;
        else if (p.trang_thai === 'Gần ngưỡng') mau = MAU.theo_doi;
        return { color: mau, weight: 6, opacity: 0.8, lineCap: 'round' };
      },
      truong: [
        { ma: 'ten_doan', ten: 'Tên đoạn sông' },
        { ma: 'ten_song', ten: 'Thuộc sông' },
        { ma: 'chieu_dai_km', ten: 'Chiều dài đoạn', dinh_dang: 'so_le', don_vi: 'km' },
        { ma: 'thong_so', ten: 'Thông số đánh giá' },
        { ma: 'q_s_m3s', ten: 'Lưu lượng dòng chảy Qs', dinh_dang: 'so_le', don_vi: 'm³/s' },
        { ma: 'c_qc_mg_l', ten: 'Giới hạn quy chuẩn Cqc', dinh_dang: 'so_le', don_vi: 'mg/L' },
        { ma: 'c_nn_mg_l', ten: 'Nồng độ hiện có Cnn', dinh_dang: 'so_le', don_vi: 'mg/L' },
        { ma: 'l_td_kg_ngay', ten: 'Tải lượng tối đa Ltđ', dinh_dang: 'so_le', don_vi: 'kg/ngày' },
        { ma: 'l_nn_kg_ngay', ten: 'Tải lượng sẵn có Lnn', dinh_dang: 'so_le', don_vi: 'kg/ngày' },
        { ma: 'l_t_kg_ngay', ten: 'Tải lượng nguồn thải Lt', dinh_dang: 'so_le', don_vi: 'kg/ngày' },
        { ma: 'f_s', ten: 'Hệ số an toàn Fs', dinh_dang: 'so_le' },
        { ma: 'l_tn_kg_ngay', ten: 'Khả năng tiếp nhận Ltn', dinh_dang: 'so_le', don_vi: 'kg/ngày' },
        { ma: 'ty_le_con_lai', ten: 'Tỷ lệ còn lại', dinh_dang: 'phan_tram' },
        { ma: 'trang_thai', ten: 'Kết luận' },
        { ma: 'can_cu', ten: 'Căn cứ phương pháp' },
      ],
      cot_bang: ['ma', 'ten_doan', 'q_s_m3s', 'l_td_kg_ngay', 'l_nn_kg_ngay',
                 'l_tn_kg_ngay', 'ty_le_con_lai', 'trang_thai'],
      chu_giai: [
        { kieu: 'duong', mau: MAU.tot, nhan: 'Còn khả năng tiếp nhận', day: 5 },
        { kieu: 'duong', mau: MAU.theo_doi, nhan: 'Gần ngưỡng', day: 5 },
        { kieu: 'duong', mau: MAU.xau, nhan: 'Không còn khả năng tiếp nhận', day: 5 },
      ],
    },

    /* ===== Tram, diem quan trac ===== */
    quan_trac: {
      ten: 'Trạm, điểm quan trắc',
      tep: 'quan_trac.geojson',
      kieu: 'diem',
      hien: true,
      z: 480,
      khoa: 'ma',
      truong_nhan: 'ten',
      realtime: true,
      mo_ta: 'Trạm quan trắc nước mặt, trạm thủy văn, trạm khí tượng (QTQG và mạng trạm KTTV quốc gia). Lớp này chỉ có vị trí và thông tin trạm, số đo xem ở trang Quan trắc',
      /* Ky hieu lay tu bo .qml cua QGIS, chuyen sang SVG bang
         scripts/06_tao_ky_hieu.py. Moi loai tram mot ky hieu. */
      ky_hieu: function (p) {
        if (p && p.loai_tram === 'Thủy văn') return { tep: 'Tramthuyvan' };
        if (p && (p.loai_tram === 'Mưa' || p.loai_tram === 'Khí tượng')) return { tep: 'Tramkhituong' };
        if (p && p.loai_tram === 'Nước dưới đất') return { tep: 'Lokhoan_TK' };
        return { tep: 'Diemlaymaunuocsong', co_px: 26 };
      },
      /* Hai gia tri loai_tram cuoi do CSDL QTQG tra ve, khong co trong lop mo
         phong: 'Tài nguyên nước mặt' va 'Nước dưới đất'. Khai bao o day de tab
         Quan trac dung lai duoc dung khai bao lop nay.

         radius phai sat voi BAN KINH THAT cua ky hieu khai bao o ky_hieu phia
         tren, vi identify.js lay nguong bam tu radius chu khong doc kich thuoc
         ky hieu. Lech nhau thi vung bam khong trung voi hinh nguoi dung thay.
         Co ky hieu = kich_thuoc_mm trong assets/ky_hieu/ky_hieu.json nhan
         PX_MOI_MM (3,2), tru khi khai bao co_px de ghi de. */
      kieu_ve: function (p, rt) {
        var mau, bk;
        if (p.loai_tram === 'Thủy văn') { mau = '#2563eb'; bk = 11; }
        else if (p.loai_tram === 'Mưa' || p.loai_tram === 'Khí tượng') { mau = '#7c3aed'; bk = 8; }
        else if (p.loai_tram === 'Nước dưới đất') { mau = '#b45309'; bk = 11; }
        else { mau = '#059669'; bk = 13; }
        var vien = '#ffffff';
        var day = 1.5;
        /* Vien do khi diem quan trac dang o trang thai canh bao */
        if (rt && rt.trang_thai === 'canh_bao') { vien = MAU.xau; day = 2.6; }
        else if (rt && rt.trang_thai === 'theo_doi') { vien = MAU.theo_doi; day = 2.4; }
        return { radius: bk, fillColor: mau, color: vien, weight: day,
                 opacity: 1, fillOpacity: 0.95 };
      },
      truong: [
        { ma: 'ten', ten: 'Tên trạm, điểm' },
        { ma: 'loai_tram', ten: 'Loại' },
        { ma: 'song_ho', ten: 'Trên sông, hồ' },
        { ma: 'thong_so', ten: 'Thông số quan trắc' },
        { ma: 'ten_luu_vuc', ten: 'Lưu vực' },
        { ma: 'tan_suat_do', ten: 'Tần suất đo' },
        { ma: 'don_vi_quan_ly', ten: 'Đơn vị quản lý' },
        { ma: 'tinh_trang', ten: 'Tình trạng' },
        { ma: 'nguon_so_lieu', ten: 'Nguồn thông tin trạm' },
        { ma: 'ghi_chu', ten: 'Ghi chú' },
        /* Rieng cua lo khoan quan trac nuoc duoi dat, do CSDL QTQG tra ve qua
           tab Quan trac. Tram nuoc mat de khuyet cac truong nay va giao dien
           bo qua o khuyet. */
        { ma: 'tang_chua_nuoc', ten: 'Tầng chứa nước' },
        { ma: 'cao_do_mieng_lk_m', ten: 'Cao độ miệng lỗ khoan', dinh_dang: 'so_le', don_vi: 'm' },
        { ma: 'vi_tri_hc', ten: 'Vị trí hành chính' },
        { ma: 'mang_quan_trac', ten: 'Mạng quan trắc' },
        { ma: 'thiet_bi_do', ten: 'Thiết bị quan trắc' },
        { ma: 'ngay_bat_dau', ten: 'Bắt đầu quan trắc', dinh_dang: 'ngay' },
      ],
      cot_bang: ['ma', 'ten', 'loai_tram', 'song_ho', 'ten_luu_vuc', 'tan_suat_do'],
      /* Khong khai bao lo khoan nuoc duoi dat o day. Chu giai nay la cua
         TRANG BAN DO, ma trang ban do doc data/quan_trac.geojson tinh, trong
         do khong co lo khoan nao; them vao se la mot muc chu giai khong ung
         voi doi tuong nao tren ban do. Lo khoan co lop rieng quan_trac_ndd, va
         tab Quan trac thi tu sinh chu giai tu cac loai tram dang ve, xem
         ve_chu_giai_qt() trong assets/js/quan_trac.js. */
      chu_giai: [
        { kieu: 'diem', mau: '#2563eb', nhan: 'Trạm thủy văn' },
        { kieu: 'diem', mau: '#7c3aed', nhan: 'Trạm khí tượng' },
        { kieu: 'diem', mau: '#059669', nhan: 'Trạm quan trắc nước mặt (QTQG)' },
      ],
    },

    /* ===== Lo khoan quan trac nuoc duoi dat (du lieu that, QTQG) =====

       Lop nay do scripts/08_xuat_lo_khoan_ndd.py sinh ra tu CSDL QTQG, KHONG
       phai tu CSDL/ nhu cac lop chuyen de khac.

       Vi sao la lop tinh chu khong goi thang backend: ban do chinh phai chay
       duoc khi khong co dich vu nao dang chay. Doi lai, so do trong lop nay
       la so do o thoi diem xuat; truong nguon_dl cua tung doi tuong ghi ro
       dieu do, va tab Quan trac moi la cho xem so moi nhat.

       Khong co truong WQI: Quyet dinh 1460/QD-TCMT la chi so chat luong nuoc
       MAT luc dia, nguong nuoc duoi dat theo QCVN 09-MT:2015/BTNMT. */
    quan_trac_ndd: {
      ten: 'Lỗ khoan quan trắc nước dưới đất',
      tep: 'quan_trac_ndd.geojson',
      kieu: 'diem',
      hien: true,
      z: 478,
      khoa: 'ma',
      truong_nhan: 'ten',
      mo_ta: 'Các lỗ khoan đang hoạt động của mạng quan trắc nước dưới đất quốc gia',
      ky_hieu: { tep: 'Lokhoan_TK' },
      /* Ky hieu la tep SVG nen mau tu tep quyet dinh. Khai bao nay chi dung
         lam du phong khi danh muc ky hieu chua nap xong. */
      /* radius 11 de khop ban kinh that cua ky hieu Lokhoan_TK (7 mm x 3,2
         px/mm = 22 px duong kinh). identify.js lay nguong bam tu radius. */
      kieu_ve: function () {
        return { radius: 11, fillColor: '#b45309', color: '#ffffff',
                 weight: 1.5, opacity: 1, fillOpacity: 0.95 };
      },
      truong: [
        { ma: 'ten', ten: 'Tên lỗ khoan' },
        { ma: 'tang_chua_nuoc', ten: 'Tầng chứa nước' },
        { ma: 'vi_tri_hc', ten: 'Vị trí hành chính' },
        { ma: 'ten_luu_vuc', ten: 'Lưu vực' },
        { ma: 'cao_do_mieng_lk_m', ten: 'Cao độ miệng lỗ khoan', dinh_dang: 'so_le', don_vi: 'm' },
        /* Số đo tại thời điểm xuất lớp */
        { ma: 'h_ngam_m', ten: 'Mực nước (dưới miệng lỗ khoan)', dinh_dang: 'so_le', don_vi: 'm' },
        { ma: 'cao_do_mn_m', ten: 'Cao độ mặt nước', dinh_dang: 'so_le', don_vi: 'm' },
        { ma: 'thoi_diem_muc_nuoc', ten: 'Thời điểm đo mực nước', dinh_dang: 'thoi_diem' },
        { ma: 'nhiet_do_c', ten: 'Nhiệt độ', dinh_dang: 'so_le', don_vi: '°C' },
        { ma: 'thoi_diem_chat_luong', ten: 'Thời điểm lấy mẫu phân tích', dinh_dang: 'thoi_diem' },
        { ma: 'ph', ten: 'pH', dinh_dang: 'so_le' },
        { ma: 'tds_mg_l', ten: 'Tổng chất rắn hòa tan (TDS)', dinh_dang: 'so_le', don_vi: 'mg/L' },
        { ma: 'do_cung_mg_l', ten: 'Độ cứng (theo CaCO₃)', dinh_dang: 'so_le', don_vi: 'mg/L' },
        { ma: 'permanganat_mg_l', ten: 'Chỉ số pemanganat', dinh_dang: 'so_le', don_vi: 'mg/L' },
        { ma: 'amoni_mg_l', ten: 'Amoni (N-NH₄⁺)', dinh_dang: 'vi_luong', don_vi: 'mg/L' },
        { ma: 'nitrat_mg_l', ten: 'Nitrat (N-NO₃⁻)', dinh_dang: 'vi_luong', don_vi: 'mg/L' },
        { ma: 'nitrit_mg_l', ten: 'Nitrit (N-NO₂⁻)', dinh_dang: 'vi_luong', don_vi: 'mg/L' },
        { ma: 'clorua_mg_l', ten: 'Clorua (Cl⁻)', dinh_dang: 'so_le', don_vi: 'mg/L' },
        { ma: 'sunfat_mg_l', ten: 'Sunfat (SO₄²⁻)', dinh_dang: 'so_le', don_vi: 'mg/L' },
        { ma: 'florua_mg_l', ten: 'Florua (F⁻)', dinh_dang: 'vi_luong', don_vi: 'mg/L' },
        { ma: 'xyanua_mg_l', ten: 'Xyanua (CN⁻)', dinh_dang: 'vi_luong', don_vi: 'mg/L' },
        { ma: 'fe_mg_l', ten: 'Sắt tổng (Fe)', dinh_dang: 'vi_luong', don_vi: 'mg/L' },
        { ma: 'fe2_mg_l', ten: 'Sắt (II)', dinh_dang: 'vi_luong', don_vi: 'mg/L' },
        { ma: 'fe3_mg_l', ten: 'Sắt (III)', dinh_dang: 'vi_luong', don_vi: 'mg/L' },
        { ma: 'mn_mg_l', ten: 'Mangan (Mn)', dinh_dang: 'vi_luong', don_vi: 'mg/L' },
        { ma: 'as_mg_l', ten: 'Asen (As)', dinh_dang: 'vi_luong', don_vi: 'mg/L' },
        { ma: 'cd_mg_l', ten: 'Cadimi (Cd)', dinh_dang: 'vi_luong', don_vi: 'mg/L' },
        { ma: 'pb_mg_l', ten: 'Chì (Pb)', dinh_dang: 'vi_luong', don_vi: 'mg/L' },
        { ma: 'cr_mg_l', ten: 'Crom tổng (Cr)', dinh_dang: 'vi_luong', don_vi: 'mg/L' },
        { ma: 'cu_mg_l', ten: 'Đồng (Cu)', dinh_dang: 'vi_luong', don_vi: 'mg/L' },
        { ma: 'zn_mg_l', ten: 'Kẽm (Zn)', dinh_dang: 'vi_luong', don_vi: 'mg/L' },
        { ma: 'hg_mg_l', ten: 'Thủy ngân (Hg)', dinh_dang: 'vi_luong', don_vi: 'mg/L' },
        { ma: 'se_mg_l', ten: 'Selen (Se)', dinh_dang: 'vi_luong', don_vi: 'mg/L' },
        { ma: 'phenol_mg_l', ten: 'Phenol', dinh_dang: 'vi_luong', don_vi: 'mg/L' },
        { ma: 'coliform_mpn_100ml', ten: 'Coliform', dinh_dang: 'so', don_vi: 'MPN/100mL' },
        { ma: 'ecoli_mpn_100ml', ten: 'E. coli', dinh_dang: 'so', don_vi: 'MPN/100mL' },
        { ma: 'mang_quan_trac', ten: 'Mạng quan trắc' },
        { ma: 'thiet_bi_do', ten: 'Thiết bị quan trắc' },
        { ma: 'ngay_bat_dau', ten: 'Bắt đầu quan trắc', dinh_dang: 'ngay' },
      ],
      cot_bang: ['ma', 'ten', 'tang_chua_nuoc', 'vi_tri_hc', 'h_ngam_m',
                 'thoi_diem_muc_nuoc'],
      chu_giai: [
        { kieu: 'diem', mau: '#b45309',
          nhan: 'Lỗ khoan quan trắc nước dưới đất' },
      ],
    },

    /* ===== Vi tri quan trac chat luong nuoc mat cua dia phuong (du lieu that) =====

       Sinh boi scripts/13_nap_wqi_dia_phuong.py tu Bieu 10 cua ban ra soat
       kiem ke. KHONG tron vao lop quan_trac o tren: lop do la tram cua CSDL
       Quan trac Quoc gia, con day la mang quan trac cua tinh.

       WQI la so CO SAN trong bieu, khong tinh lai. Moi vi tri co so ky do
       khac nhau (12 thang, 10 thang, 4 quy, hoac 1 lan lay mau bo sung) nen
       khong co cot theo thang: truong wqi la ky MOI NHAT, ca chuoi nam o
       chuoi_wqi. Mau diem theo phan loai cua ky moi nhat.

       Vien toi mau chu khong vien trang nhu cac lop khac: muc "Trung binh" la
       mau vang, vien trang thi chim tren nen sang. */
    quan_trac_dia_phuong: {
      ten: 'Chất lượng nước mặt (WQI, quan trắc địa phương)',
      tep: 'quan_trac_dia_phuong.geojson',
      kieu: 'diem',
      hien: true,
      z: 479,                  /* duoi quan_trac 480, tren quan_trac_ndd 478 */
      khoa: 'ma',
      truong_nhan: 'ten',
      du_lieu_that: true,
      mo_ta: 'Vị trí quan trắc chất lượng nước mặt của tỉnh, chỉ số WQI theo kết quả kiểm kê (Biểu 10)',
      kieu_ve: function (p) {
        return { radius: 6, fillColor: MAU_WQI[p.phan_loai_wqi] || MAU.trung_tinh,
                 color: '#1e293b', weight: 1.2, opacity: 1, fillOpacity: 0.95 };
      },
      truong: [
        { ma: 'ten', ten: 'Vị trí quan trắc' },
        { ma: 'xa_phuong', ten: 'Xã, phường' },
        { ma: 'xa_cu', ten: 'Xã (cũ)' },
        { ma: 'huyen_cu', ten: 'Huyện (cũ)' },
        { ma: 'tinh_cu', ten: 'Tỉnh (cũ)' },
        { ma: 'luu_vuc_kiem_ke', ten: 'Thuộc lưu vực sông' },
        { ma: 'ten_luu_vuc', ten: 'Lưu vực' },
        { ma: 'wqi', ten: 'WQI kỳ mới nhất', dinh_dang: 'so' },
        { ma: 'phan_loai_wqi', ten: 'Phân loại' },
        { ma: 'thoi_diem_wqi', ten: 'Kỳ quan trắc mới nhất' },
        { ma: 'wqi_thap_nhat', ten: 'WQI thấp nhất', dinh_dang: 'so' },
        { ma: 'ky_wqi_thap_nhat', ten: 'Kỳ có WQI thấp nhất' },
        { ma: 'so_ky', ten: 'Số kỳ quan trắc', dinh_dang: 'so' },
        { ma: 'chuoi_wqi', ten: 'WQI các kỳ' },
        { ma: 'dot_quan_trac', ten: 'Đợt quan trắc' },
      ],
      cot_bang: ['ma', 'ten', 'xa_phuong', 'luu_vuc_kiem_ke', 'wqi',
                 'phan_loai_wqi', 'thoi_diem_wqi', 'wqi_thap_nhat'],
      chu_giai: [
        { kieu: 'diem', mau: MAU_WQI['Rất tốt'], nhan: 'WQI 91 - 100: Rất tốt' },
        { kieu: 'diem', mau: MAU_WQI['Tốt'], nhan: 'WQI 76 - 90: Tốt' },
        { kieu: 'diem', mau: MAU_WQI['Trung bình'], nhan: 'WQI 51 - 75: Trung bình' },
        { kieu: 'diem', mau: MAU_WQI['Xấu'], nhan: 'WQI 26 - 50: Xấu' },
        { kieu: 'diem', mau: MAU_WQI['Kém'], nhan: 'WQI 10 - 25: Kém' },
        { kieu: 'diem', mau: MAU_WQI['Ô nhiễm rất nặng'], nhan: 'WQI dưới 10: Ô nhiễm rất nặng' },
      ],
    },
  },

  /* ---------------- Nhan trang thai thoi gian thuc ---------------- */
  nhan_trang_thai: {
    binh_thuong: 'Bình thường',
    theo_doi: 'Cần theo dõi',
    canh_bao: 'Cảnh báo',
  },

  /* ---------------- Truong hien thi cho du lieu thoi gian thuc ---------------- */
  truong_realtime: {
    ho_chua: [
      { ma: 'muc_nuoc_m', ten: 'Mực nước hiện tại', dinh_dang: 'so_le', don_vi: 'm' },
      { ma: 'ty_le_dung_tich', ten: 'Tỷ lệ dung tích hữu ích', dinh_dang: 'phan_tram' },
      { ma: 'w_hien_tai_trieu_m3', ten: 'Lượng nước hiện có', dinh_dang: 'so_le', don_vi: 'triệu m³' },
    ],
    thuy_van: [
      { ma: 'h_m', ten: 'Mực nước', dinh_dang: 'so_le', don_vi: 'm' },
      { ma: 'q_m3s', ten: 'Lưu lượng', dinh_dang: 'so_le', don_vi: 'm³/s' },
    ],
    mua: [
      { ma: 'mua_1h_mm', ten: 'Lượng mưa 1 giờ', dinh_dang: 'so_le', don_vi: 'mm' },
      { ma: 'mua_24h_mm', ten: 'Lượng mưa 24 giờ', dinh_dang: 'so_le', don_vi: 'mm' },
    ],
    /* Danh sach nay la nguon su that duy nhat ve nhan, don vi va dinh dang cua
       moi thong so chat luong nuoc. Bang, bang chi tiet, bieu do va CSV deu
       sinh tu day. Ban ghi nao khong co thong so nao thi giao dien bo qua,
       khong hien dong trong. */
    chat_luong_nuoc: [
      { ma: 'wqi', ten: 'Chỉ số WQI', dinh_dang: 'so' },
      { ma: 'phan_loai_wqi', ten: 'Phân loại' },
      /* Nhom co ban */
      { ma: 'ph', ten: 'pH', dinh_dang: 'so_le' },
      { ma: 'do_mg_l', ten: 'DO', dinh_dang: 'so_le', don_vi: 'mg/L' },
      { ma: 'nhiet_do_c', ten: 'Nhiệt độ', dinh_dang: 'so_le', don_vi: '°C' },
      { ma: 'ec_us_cm', ten: 'Độ dẫn điện', dinh_dang: 'so', don_vi: 'µS/cm' },
      { ma: 'tss_mg_l', ten: 'TSS', dinh_dang: 'so_le', don_vi: 'mg/L' },
      { ma: 'do_duc_ntu', ten: 'Độ đục', dinh_dang: 'so_le', don_vi: 'NTU' },
      /* Nhom mo rong */
      { ma: 'cod_mg_l', ten: 'COD', dinh_dang: 'so_le', don_vi: 'mg/L' },
      { ma: 'bod5_mg_l', ten: 'BOD5', dinh_dang: 'so_le', don_vi: 'mg/L' },
      { ma: 'amoni_mg_l', ten: 'Amoni (N-NH₄⁺)', dinh_dang: 'vi_luong', don_vi: 'mg/L' },
      { ma: 'nitrat_mg_l', ten: 'Nitrat (N-NO₃⁻)', dinh_dang: 'vi_luong', don_vi: 'mg/L' },
      { ma: 'nitrit_mg_l', ten: 'Nitrit (N-NO₂⁻)', dinh_dang: 'vi_luong', don_vi: 'mg/L' },
      { ma: 'photphat_mg_l', ten: 'Photphat (P-PO₄³⁻)', dinh_dang: 'vi_luong', don_vi: 'mg/L' },
      { ma: 'toc_mg_l', ten: 'TOC', dinh_dang: 'so_le', don_vi: 'mg/L' },
      { ma: 'coliform_mpn_100ml', ten: 'Tổng Coliform', dinh_dang: 'so', don_vi: 'MPN/100mL' },
      { ma: 'ecoli_mpn_100ml', ten: 'E. coli', dinh_dang: 'so', don_vi: 'MPN/100mL' },
      /* Kim loai nang, nhom III cua Quyet dinh 1460 */
      { ma: 'as_mg_l', ten: 'Asen (As)', dinh_dang: 'vi_luong', don_vi: 'mg/L' },
      { ma: 'cd_mg_l', ten: 'Cadimi (Cd)', dinh_dang: 'vi_luong', don_vi: 'mg/L' },
      { ma: 'pb_mg_l', ten: 'Chì (Pb)', dinh_dang: 'vi_luong', don_vi: 'mg/L' },
      { ma: 'cr6_mg_l', ten: 'Crom VI (Cr⁶⁺)', dinh_dang: 'vi_luong', don_vi: 'mg/L' },
      { ma: 'cu_mg_l', ten: 'Đồng (Cu)', dinh_dang: 'vi_luong', don_vi: 'mg/L' },
      { ma: 'zn_mg_l', ten: 'Kẽm (Zn)', dinh_dang: 'vi_luong', don_vi: 'mg/L' },
      { ma: 'hg_mg_l', ten: 'Thủy ngân (Hg)', dinh_dang: 'vi_luong', don_vi: 'mg/L' },
      /* Thuoc bao ve thuc vat, nhom II cua Quyet dinh 1460, don vi microgam */
      { ma: 'aldrin_ug_l', ten: 'Aldrin', dinh_dang: 'vi_luong', don_vi: 'µg/L' },
      { ma: 'bhc_ug_l', ten: 'BHC', dinh_dang: 'vi_luong', don_vi: 'µg/L' },
      { ma: 'dieldrin_ug_l', ten: 'Dieldrin', dinh_dang: 'vi_luong', don_vi: 'µg/L' },
      { ma: 'ddts_ug_l', ten: 'Tổng DDT', dinh_dang: 'vi_luong', don_vi: 'µg/L' },
      { ma: 'heptachlor_ug_l', ten: 'Heptachlor', dinh_dang: 'vi_luong', don_vi: 'µg/L' },
    ],
    /* Nhom nuoc duoi dat, lay tu mang quan trac quoc gia qua backend QTQG:
       cac lo khoan dang hoat dong trong pham vi tinh.

       Vi sao h_ngam_m khong dung chung truong voi h_m cua nuoc mat: nuoc mat
       la cao do mat nuoc theo moc cua tram (so duong), con day la do sau mat
       nuoc duoi mieng lo khoan (so AM). Hai dai luong nguoc nghia, gop lam
       mot truong la ve chung mot bieu do va chung mot cot bang.

       KHONG co truong WQI o nhom nay. Quyet dinh 1460/QD-TCMT la chi so chat
       luong nuoc MAT luc dia; nguong cac thong so nuoc duoi dat theo
       QCVN 09-MT:2015/BTNMT. Backend chan viec tinh WQI cho ban ghi lo khoan,
       xem wqi.gan_wqi(). */
    nuoc_duoi_dat: [
      { ma: 'h_ngam_m', ten: 'Mực nước (dưới miệng lỗ khoan)', dinh_dang: 'so_le', don_vi: 'm' },
      { ma: 'cao_do_mn_m', ten: 'Cao độ mặt nước', dinh_dang: 'so_le', don_vi: 'm' },
      { ma: 'thoi_diem_muc_nuoc', ten: 'Thời điểm đo mực nước', dinh_dang: 'thoi_diem' },
      { ma: 'tang_chua_nuoc', ten: 'Tầng chứa nước' },
      { ma: 'nhiet_do_c', ten: 'Nhiệt độ', dinh_dang: 'so_le', don_vi: '°C' },
      { ma: 'thoi_diem_chat_luong', ten: 'Thời điểm lấy mẫu phân tích', dinh_dang: 'thoi_diem' },
      /* Thong so hoa hoc theo QCVN 09-MT:2015/BTNMT */
      { ma: 'ph', ten: 'pH', dinh_dang: 'so_le' },
      { ma: 'tds_mg_l', ten: 'Tổng chất rắn hòa tan (TDS)', dinh_dang: 'so_le', don_vi: 'mg/L' },
      { ma: 'do_cung_mg_l', ten: 'Độ cứng (theo CaCO₃)', dinh_dang: 'so_le', don_vi: 'mg/L' },
      { ma: 'permanganat_mg_l', ten: 'Chỉ số pemanganat', dinh_dang: 'so_le', don_vi: 'mg/L' },
      { ma: 'ec_us_cm', ten: 'Độ dẫn điện', dinh_dang: 'so', don_vi: 'µS/cm' },
      { ma: 'do_mg_l', ten: 'DO', dinh_dang: 'so_le', don_vi: 'mg/L' },
      { ma: 'amoni_mg_l', ten: 'Amoni (N-NH₄⁺)', dinh_dang: 'vi_luong', don_vi: 'mg/L' },
      { ma: 'nitrat_mg_l', ten: 'Nitrat (N-NO₃⁻)', dinh_dang: 'vi_luong', don_vi: 'mg/L' },
      { ma: 'nitrit_mg_l', ten: 'Nitrit (N-NO₂⁻)', dinh_dang: 'vi_luong', don_vi: 'mg/L' },
      { ma: 'photphat_mg_l', ten: 'Photphat (P-PO₄³⁻)', dinh_dang: 'vi_luong', don_vi: 'mg/L' },
      { ma: 'clorua_mg_l', ten: 'Clorua (Cl⁻)', dinh_dang: 'so_le', don_vi: 'mg/L' },
      { ma: 'sunfat_mg_l', ten: 'Sunfat (SO₄²⁻)', dinh_dang: 'so_le', don_vi: 'mg/L' },
      { ma: 'florua_mg_l', ten: 'Florua (F⁻)', dinh_dang: 'vi_luong', don_vi: 'mg/L' },
      { ma: 'xyanua_mg_l', ten: 'Xyanua (CN⁻)', dinh_dang: 'vi_luong', don_vi: 'mg/L' },
      /* Sat: nguon ghi ba cot roi. Khong cong Fe(II) voi Fe(III) de ra sat
         tong, vi do la suy dien chu khong phai so do. */
      { ma: 'fe_mg_l', ten: 'Sắt tổng (Fe)', dinh_dang: 'vi_luong', don_vi: 'mg/L' },
      { ma: 'fe2_mg_l', ten: 'Sắt (II)', dinh_dang: 'vi_luong', don_vi: 'mg/L' },
      { ma: 'fe3_mg_l', ten: 'Sắt (III)', dinh_dang: 'vi_luong', don_vi: 'mg/L' },
      { ma: 'mn_mg_l', ten: 'Mangan (Mn)', dinh_dang: 'vi_luong', don_vi: 'mg/L' },
      { ma: 'as_mg_l', ten: 'Asen (As)', dinh_dang: 'vi_luong', don_vi: 'mg/L' },
      { ma: 'cd_mg_l', ten: 'Cadimi (Cd)', dinh_dang: 'vi_luong', don_vi: 'mg/L' },
      { ma: 'pb_mg_l', ten: 'Chì (Pb)', dinh_dang: 'vi_luong', don_vi: 'mg/L' },
      /* Crom TONG, khong phai Cr(VI): nguon chi co cot crom chung */
      { ma: 'cr_mg_l', ten: 'Crom tổng (Cr)', dinh_dang: 'vi_luong', don_vi: 'mg/L' },
      { ma: 'cu_mg_l', ten: 'Đồng (Cu)', dinh_dang: 'vi_luong', don_vi: 'mg/L' },
      { ma: 'zn_mg_l', ten: 'Kẽm (Zn)', dinh_dang: 'vi_luong', don_vi: 'mg/L' },
      { ma: 'hg_mg_l', ten: 'Thủy ngân (Hg)', dinh_dang: 'vi_luong', don_vi: 'mg/L' },
      { ma: 'se_mg_l', ten: 'Selen (Se)', dinh_dang: 'vi_luong', don_vi: 'mg/L' },
      { ma: 'phenol_mg_l', ten: 'Phenol', dinh_dang: 'vi_luong', don_vi: 'mg/L' },
      { ma: 'coliform_mpn_100ml', ten: 'Coliform', dinh_dang: 'so', don_vi: 'MPN/100mL' },
      { ma: 'ecoli_mpn_100ml', ten: 'E. coli', dinh_dang: 'so', don_vi: 'MPN/100mL' },
    ],
    khai_thac: [
      { ma: 'q_thuc_te_m3_ngay', ten: 'Lưu lượng khai thác hôm nay', dinh_dang: 'so', don_vi: 'm³/ngày' },
      { ma: 'ty_le_su_dung', ten: 'So với hạn mức giấy phép', dinh_dang: 'phan_tram' },
    ],
  },
};

/* --------------------------------------------------------------------------
   Tien ich dung chung
   -------------------------------------------------------------------------- */

/* So ngay tu hom nay den mot ngay cho truoc, am neu da qua */
function so_ngay_den(chuoi_ngay) {
  if (!chuoi_ngay) return null;
  var d = new Date(chuoi_ngay);
  if (isNaN(d.getTime())) return null;
  var hom_nay = new Date();
  hom_nay.setHours(0, 0, 0, 0);
  return Math.round((d - hom_nay) / 86400000);
}

/* Bo dau tieng Viet de tim kiem khong phan biet dau */
function bo_dau(chu) {
  return String(chu || '')
    .normalize('NFD')
    .replace(/[̀-ͯ]/g, '')
    .replace(/đ/g, 'd').replace(/Đ/g, 'D')
    .toLowerCase();
}

/* Lay nhan hien thi cua mot doi tuong */
function nhan_doi_tuong(ma_lop, props) {
  var dn = CAU_HINH.lop[ma_lop];
  if (!dn) return '';
  return props[dn.truong_nhan] || props[dn.khoa] || '(không tên)';
}
