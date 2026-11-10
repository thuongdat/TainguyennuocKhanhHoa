/* ==========================================================================
   tinh.js - Nap tham so cua tinh
   --------------------------------------------------------------------------
   Phai nap TRUOC moi tep JavaScript khac, vi cac tep do deu can ten tinh,
   pham vi ban do va danh sach lop co san.

   Tep tinh.json o goc du an la nguon su that duy nhat: scripts/tinh.py doc
   cung tep do, nen khong bao gio lech giua Python va trinh duyet. Doi tinh,
   doi ten don vi hay doi pham vi ban do deu chi sua mot cho do.

   Moi trang phai khai bao bien GOC_TRANG truoc khi nap tep nay:
     index.html          -> var GOC_TRANG = '';
     pages/thong-ke.html -> var GOC_TRANG = '../';
   ========================================================================== */

var TINH = null;


/* --------------------------------------------------------------------------
   Nap tham so, tra ve Promise
   -------------------------------------------------------------------------- */
function nap_tinh() {
  /* Chong cache: tep nay chi vai KB ma quyet dinh ten tinh, tam ban do va
     danh sach lop, nen khong duoc phep la ban cu. Xem ghi chu o
     duong_dan_du_lieu() ve viec hai du an dung chung mot localhost. */
  return fetch(GOC_TRANG + 'tinh.json?t=' + Date.now(), { cache: 'no-store' })
    .then(function (r) {
      if (!r.ok) throw new Error('Không đọc được tệp tinh.json');
      return r.json();
    })
    .then(function (tt) {
      TINH = tt;
      ap_dung_ten_tinh();
      return tt;
    });
}


/* --------------------------------------------------------------------------
   Duong dan den mot tep du lieu
   --------------------------------------------------------------------------
   Duong dan mang them tham so ?tinh=<ma>. Tham so nay KHONG den may chu lam
   gi ca, no chi de tach khoa cache cua trinh duyet.

   Vi sao can: moi tinh la mot du an rieng, va khi chay thu tren may ca nhan
   thi cac du an deu dung  http://localhost:8000  - CUNG MOT ORIGIN. Trinh
   duyet lay URL lam khoa cache, nen  data/ranh_gioi_tinh.geojson  cua tinh
   nay va cua tinh khac la cung mot khoa. Mo du an B sau du an A thi ban do co
   the ve ranh gioi cua A trong khi tieu de trang da la B: mot loi rat kho
   doan ra, vi ma nguon khong co gi sai.

   Them ?tinh=<ma> thi hai du an thanh hai khoa khac nhau, va trong cung mot
   tinh thi tep van duoc cache binh thuong - khong hy sinh toc do tai, dieu
   quan trong voi cac tep nen nang vai MB tren GitHub Pages.

   Ham tra ve chuoi DA co dau "?", nen ben goi muon them tham so phai dung
   "&", xem nap_realtime() trong realtime.js.
   -------------------------------------------------------------------------- */
function duong_dan_du_lieu(ten_tep) {
  var ma = (TINH && TINH.ma) ? TINH.ma : 'chua-biet';
  return GOC_TRANG + 'data/' + ten_tep + '?tinh=' + encodeURIComponent(ma);
}

/* --------------------------------------------------------------------------
   Dia chi backend trung gian QTQG
   --------------------------------------------------------------------------
   Thu tu uu tien:
     1. CAU_HINH.api.goc neu da dien  -> dia chi may chu that khi trien khai.
     2. Tu suy: giao thuc va hostname dang mo, cong lay tu TINH.cong.backend.

   Vi sao tu suy chu khong ghi cung 'http://localhost:8001': moi tinh la mot
   du an rieng va moi tinh mot cap cong rieng (xem ghi_chu_cong trong
   tinh.json). Ghi cung thi sao du an sang tinh khac la hai backend tranh nhau
   cung mot cong.
   -------------------------------------------------------------------------- */
function dia_chi_backend() {
  if (CAU_HINH.api && CAU_HINH.api.goc) return CAU_HINH.api.goc;

  var cong = (TINH && TINH.cong && TINH.cong.backend) || 8001;
  var ten_may = location.hostname || 'localhost';
  return location.protocol + '//' + ten_may + ':' + cong;
}


/* Lop da co du lieu hay chua. Luc moi lap he thong thuong chi co vai lop nen
   khong the gia dinh lop nao cung ton tai. */
function lop_co_san(ma_lop) {
  if (!TINH || !TINH.lop_co_san) return true;
  return TINH.lop_co_san.indexOf(ma_lop) >= 0;
}


/* --------------------------------------------------------------------------
   Dien ten tinh vao giao dien
   Moi cho can thay ten chi viec dat thuoc tinh data-tinh trong HTML,
   gia tri la ten truong trong tinh.json.
   -------------------------------------------------------------------------- */
function ap_dung_ten_tinh() {
  var cac_o = document.querySelectorAll('[data-tinh]');
  for (var i = 0; i < cac_o.length; i++) {
    var truong = cac_o[i].getAttribute('data-tinh');
    if (TINH[truong] !== undefined) cac_o[i].textContent = TINH[truong];
  }

  var tieu_de = document.querySelector('title');
  if (tieu_de) {
    tieu_de.textContent = tieu_de.textContent.replace(/\{ten\}/g, TINH.ten_ngan);
  }
}
