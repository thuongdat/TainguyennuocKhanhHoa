/* ==========================================================================
   quan_trac.js - Tab Quan trac, noi so lieu QTQG vao trang WebGIS
   --------------------------------------------------------------------------
   Nap cuoi cung trong pages/quan-trac.html. Phu thuoc:
     config.js         CAU_HINH, DINH_DANG, dinh_dang_gia_tri, bo_dau
     tinh.js           TINH, nap_tinh
     dung_chung.js     the_so, dinh_dang_thoi_diem, mo_hop_thoai
     xuat_tep.js       tai_ve_csv
     api_quan_trac.js  API_QT, nap_tram_qtqg, nap_so_do_qtqg, lay_so_do

   Trang nay KHONG nap map.js, layers.js, identify.js, table.js hay app.js:
   nhung tep do gan chat vao bien toan cuc ban_do, kho LOP va cac id DOM cua
   trang ban do. Phan dung lai o day la KHAI BAO chu khong phai ma: lop nen
   lay tu CAU_HINH.ban_do_nen, tam ban do tu TINH.ban_do, mau ky hieu tu
   CAU_HINH.lop.quan_trac.kieu_ve, nhan va don vi tu CAU_HINH.truong_realtime.
   ========================================================================== */

var ban_do_qt = null;          /* Leaflet Map cua ban do nho */
var lop_nen_qt = null;         /* lop tile dang dung */
var nhom_diem = null;          /* L.layerGroup chua cac circleMarker */
var DIEM_THEO_MA = {};         /* ma tram -> circleMarker */
var TRAM = [];                 /* danh sach tram da gop so do */
var TRAM_DANG_VE = [];         /* danh sach sau khi loc, dung cho bang va CSV */
var MA_DANG_CHON = null;
var bieu_do_chuoi = null;      /* doi tuong Chart.js */
var dong_ho_lam_moi = null;

/* Cot cua bang. Nhan lay tu CAU_HINH khi co, nen doi nhan chi sua config.js */
var COT_BANG = [
  { ma: 'ma', ten: 'Mã trạm' },
  { ma: 'ten', ten: 'Tên trạm, điểm' },
  { ma: 'loai_tram', ten: 'Loại' },
  { ma: 'nguon', ten: 'Nguồn số liệu' },
  { ma: 'ten_luu_vuc', ten: 'Lưu vực' },
  { ma: 'trang_thai', ten: 'Trạng thái' },
  { ma: 'wqi', ten: 'WQI', dinh_dang: 'so' },
  { ma: 'h_m', ten: 'Mực nước', dinh_dang: 'so_le', don_vi: 'm' },
  { ma: 'q_m3s', ten: 'Lưu lượng', dinh_dang: 'so_le', don_vi: 'm³/s' },
  /* Hai cot cua lo khoan nuoc duoi dat. h_ngam_m de rieng khoi h_m vi la do
     sau mat nuoc duoi mieng lo khoan (so am), khong phai cao do mat nuoc. */
  { ma: 'h_ngam_m', ten: 'Mực nước ngầm', dinh_dang: 'so_le', don_vi: 'm' },
  { ma: 'tang_chua_nuoc', ten: 'Tầng chứa nước' },
  { ma: 'thoi_diem', ten: 'Thời điểm đo' },
];

var BANG_QT = { cot_sap_xep: 'ma', tang_dan: true };


/* ==========================================================================
   Khoi dong
   ========================================================================== */

document.addEventListener('DOMContentLoaded', function () {
  khoi_phuc_giao_dien_qt();

  if (location.protocol === 'file:') {
    hien_loi('<strong>Phải mở trang qua máy chủ web.</strong> '
      + 'Trình duyệt chặn <code>fetch()</code> trên giao thức '
      + '<code>file://</code>. Tại thư mục gốc dự án chạy '
      + '<code>python -m http.server 8000</code> rồi mở '
      + '<code>http://localhost:8000/pages/quan-trac.html</code>.');
    return;
  }

  gan_su_kien();

  nap_tinh()
    .then(function () {
      cap_nhat_dai_thong_bao_qt();
      /* Danh muc ky hieu phai co truoc khi ve diem, neu khong lan ve dau
         van ra vong tron roi moi doi, nhin thay giat */
      return Promise.all([kiem_tra_suc_khoe(), nap_danh_muc_ky_hieu()]);
    })
    .then(function (ds) {
      return ds[0];
    })
    .then(function (sk) {
      if (!sk) {
        hien_loi(html_loi_dich_vu());
        return null;
      }
      return Promise.all([nap_tram_qtqg(), nap_so_do_qtqg()]);
    })
    .then(function (ket_qua) {
      if (!ket_qua) return;
      if (!ket_qua[0] || !ket_qua[1]) {
        hien_loi(html_loi_dich_vu());
        return;
      }
      gop_du_lieu();
      /* Goi lai o day chu khong chi o tren: luc nap_tinh() xong thi
         API_QT.so_do con rong, chua biet co ban ghi nao bi an vi qua cu. */
      cap_nhat_dai_thong_bao_qt();
      document.getElementById('man-cho').hidden = true;
      document.getElementById('noi-dung-qt').hidden = false;
      tao_ban_do_nho();
      dung_bo_loc_loai();
      dung_chon_thong_so();
      ve_tat_ca();
      bat_lam_moi_dinh_ky_qt();
    })
    .catch(function (e) {
      hien_loi('Không nạp được trang: ' + (e && e.message ? e.message : e));
    });
});


function hien_loi(html) {
  document.getElementById('man-cho').hidden = true;
  var o = document.getElementById('loi-nap');
  o.innerHTML = html;
  o.hidden = false;
}


function html_loi_dich_vu() {
  var goc = dia_chi_backend();
  /* Lenh goi y phai mang dung cong cua tinh nay, khong ghi cung 8001: moi
     tinh mot cap cong rieng, xem ghi_chu_cong trong tinh.json. */
  var cong = (TINH && TINH.cong && TINH.cong.backend) || 8001;
  return '<strong>Chưa nối được dịch vụ quan trắc.</strong><br>'
    + 'Lý do: ' + (API_QT.loi || 'không rõ') + '<br><br>'
    + 'Trang này lấy số liệu từ backend trung gian tại <code>' + goc
    + '</code>. Khởi động dịch vụ đó rồi tải lại trang:<br>'
    + '<code>cd backend</code><br>'
    + '<code>python main.py</code><br><br>'
    + '<span class="ghi-chu-nho">Hoặc <code>python -m uvicorn main:app --port '
    + cong + '</code>. Cổng lấy từ <code>cong.backend</code> trong '
    + '<code>tinh.json</code>; địa chỉ máy chủ thật thì khai trong '
    + '<code>CAU_HINH.api.goc</code> ở <code>assets/js/config.js</code>.</span>';
}


function cap_nhat_dai_thong_bao_qt() {
  var cac_doan = [];

  if (TINH && TINH.ghi_chu_dau_trang) cac_doan.push(TINH.ghi_chu_dau_trang);

  /* Backend an ban ghi so do qua cu, xem SO_DO_CU_TOI_DA_NGAY trong
     backend/cau_hinh.py. Phai noi ro da an cai gi: an ma khong noi thi nguoi
     dung tuong cong trinh do chua bao gio co so do. */
  cac_doan.push(html_so_do_cu());

  var noi_dung = cac_doan.filter(function (d) { return !!d; }).join(' ');
  if (!noi_dung) return;

  var o = document.getElementById('noi-dung-thong-bao');
  /* Noi dung khong doi thi khong mo lai dai da bi nguoi dung dong: lam moi 5
     phut mot lan ma lan nao cung bat dai len la quay nguoi doc. */
  if (o.innerHTML === noi_dung) return;
  o.innerHTML = noi_dung;
  document.getElementById('dai-thong-bao').hidden = false;
}


/* Cau mo ta cac cong trinh bi an so do vi qua cu, rong neu khong co cai nao */
function html_so_do_cu() {
  var sdc = API_QT.so_do && API_QT.so_do.so_do_cu;
  if (!sdc || !sdc.so_ban_ghi) return '';

  var nam = Math.round((sdc.nguong_ngay || 0) / 365 * 10) / 10;
  var ten = (sdc.cong_trinh || []).map(function (c) {
    return (c.ten || c.ma) + ' (đo ' + dinh_dang_thoi_diem(c.thoi_diem) + ')';
  }).join('; ');

  return '<strong>Đã ẩn số đo quá cũ.</strong> '
       + sdc.so_ban_ghi + ' công trình có số đo cũ hơn ' + nam
       + ' năm nên phần số đo không được hiển thị, để không nằm lẫn với số đo '
       + 'hiện hành: ' + ten + '. Công trình vẫn còn trên bản đồ và trong '
       + 'bảng, chỉ là không có số đo đi kèm.';
}


/* ==========================================================================
   Gop hinh hoc va so do
   --------------------------------------------------------------------------
   Giong nguyen tac cua realtime.js: vi tri tram nam trong GeoJSON, so do nam
   rieng, ghep voi nhau qua truong "ma". Khong tron hai nguon lai mot cho nen
   doi nguon so do khong phai sua gi o phan ban do.
   ========================================================================== */

function gop_du_lieu() {
  TRAM = [];
  var cac_feature = (API_QT.tram && API_QT.tram.features) || [];

  cac_feature.forEach(function (f) {
    var tt = f.properties || {};
    var hh = f.geometry || {};
    var td = hh.coordinates || [];
    if (!tt.ma || td.length < 2) return;

    TRAM.push({
      ma: tt.ma,
      thuoc_tinh: tt,
      kinh_do: td[0],
      vi_do: td[1],
      so_do: lay_so_do(tt.ma),
    });
  });

  cap_nhat_dong_cap_nhat();
}


function cap_nhat_dong_cap_nhat() {
  var goi = API_QT.so_do || {};

  document.getElementById('dong-cap-nhat').textContent =
    'Cập nhật: ' + dinh_dang_thoi_diem(goi.thoi_diem);

  var o = document.getElementById('thoi-diem-cap-nhat');
  if (o) {
    o.textContent = dinh_dang_thoi_diem(goi.thoi_diem);
    o.title = goi.nguon_dl || '';
  }

  /* Nhan che do: noi ro khi so lieu chua phai nguon chinh thuc */
  var nhan = document.getElementById('nhan-che-do');
  if (la_so_lieu_that()) {
    nhan.className = 'the-that';
    nhan.textContent = 'dữ liệu thật';
  } else {
    nhan.className = 'the-mp';
    nhan.textContent = 'dữ liệu thử nghiệm';
  }
  nhan.title = goi.nguon_dl || '';
}


/* ==========================================================================
   Ban do nho
   ========================================================================== */

function nen_theo_giao_dien() {
  var cac_nen = CAU_HINH.ban_do_nen.filter(function (n) {
    /* Nen vector doc tu data/nen, nang va khong can cho ban do nho nay */
    return n.kieu !== 'vector';
  });

  var la_toi = document.documentElement.getAttribute('data-giao-dien') === 'toi';
  var ma_can = la_toi ? 'toi' : 'sang';

  var chon = cac_nen.filter(function (n) { return n.ma === ma_can; })[0];
  if (chon) return chon;
  return cac_nen.filter(function (n) { return n.mac_dinh; })[0] || cac_nen[0];
}


/* Dat lai lop nen tile. Goi ca luc tao ban do lan luc doi nen sang toi, giong
   cach dat_lop_nen() trong map.js lam cho trang ban do. */
function dat_nen_ban_do_nho() {
  var dn = nen_theo_giao_dien();
  if (lop_nen_qt) ban_do_qt.removeLayer(lop_nen_qt);

  lop_nen_qt = L.tileLayer(dn.url, {
    attribution: dn.ghi_nguon,
    /* maxNativeZoom la muc zoom cao nhat ma dich vu co tile that. Vuot qua
       muc do, Leaflet phong to tile san co thay vi de trong. */
    maxNativeZoom: dn.zoom_max || 19,
    maxZoom: CAU_HINH.ban_do_chung.zoom_max,
    subdomains: dn.url.indexOf('{s}') >= 0 ? 'abc' : [],
  }).addTo(ban_do_qt);

  lop_nen_qt.setZIndex(1);
}


function tao_ban_do_nho() {
  var tam = (TINH.ban_do && TINH.ban_do.tam) || [16, 108];
  var zoom = (TINH.ban_do && TINH.ban_do.zoom) || 9;

  ban_do_qt = L.map('ban-do-qt', {
    center: tam,
    zoom: zoom,
    minZoom: CAU_HINH.ban_do_chung.zoom_min,
    maxZoom: CAU_HINH.ban_do_chung.zoom_max,
    /* Tinh keo dai theo chieu bac nam trong khi o ban do rong va thap, dung
       zoomSnap nho thi fitBounds khong phai lui ra mot muc nguyen. Giong ly do
       da ghi trong map.js. */
    zoomSnap: 0.25,
    scrollWheelZoom: true,
  });

  dat_nen_ban_do_nho();

  nhom_diem = L.layerGroup().addTo(ban_do_qt);
}


/* Mau va vien ky hieu. Dung lai dung ham ve cua lop quan_trac trong config.js
   de ky hieu tren tab nay giong het tren trang ban do. */
function kieu_diem(tram) {
  var dn = CAU_HINH.lop.quan_trac;
  return dn.kieu_ve(tram.thuoc_tinh, tram.so_do);
}


function ve_diem_tram() {
  nhom_diem.clearLayers();
  DIEM_THEO_MA = {};

  var dn = CAU_HINH.lop.quan_trac;

  TRAM_DANG_VE.forEach(function (tram) {
    var toa_do = [tram.vi_do, tram.kinh_do];

    /* Dung cung bo ky hieu voi trang ban do, xem assets/js/ky_hieu.js */
    var diem = tao_diem_co_ky_hieu(toa_do, dn, tram.thuoc_tinh, tram.so_do);
    if (!diem) diem = L.circleMarker(toa_do, kieu_diem(tram));

    diem.bindTooltip(tram.thuoc_tinh.ten || tram.ma, { direction: 'top' });
    diem.on('click', function () { chon_tram(tram.ma, true); });
    diem.addTo(nhom_diem);
    DIEM_THEO_MA[tram.ma] = diem;
  });

  if (TRAM_DANG_VE.length === 0) return;

  var cac_toa_do = TRAM_DANG_VE.map(function (t) {
    return [t.vi_do, t.kinh_do];
  });
  ban_do_qt.fitBounds(L.latLngBounds(cac_toa_do), { padding: [24, 24] });
}


/* Chu giai cua ban do nho.
   --------------------------------------------------------------------------
   Sinh tu chinh cac loai tram DANG VE chu khong tu mot danh sach viet cung:
   tab nay ve ba loai ky hieu khac nhau (tram thuy van, diem chat luong nuoc,
   lo khoan nuoc duoi dat) va con phu thuoc bo loc, nen danh sach viet cung se
   lech ngay lan dau du lieu nguon doi.

   Khong dung dung_chu_giai() cua layers.js: ham do doc kho LOP va cac id DOM
   chi co o trang ban do. */
function ve_chu_giai_qt() {
  var o = document.getElementById('chu-giai-qt');
  if (!o) return;

  var dn = CAU_HINH.lop.quan_trac;
  var da_co = {};
  var html = '';

  TRAM_DANG_VE.forEach(function (tram) {
    var loai = tram.thuoc_tinh.loai_tram || 'Chưa rõ loại';
    if (da_co[loai]) return;
    da_co[loai] = true;

    var kieu = dn.kieu_ve(tram.thuoc_tinh, null);
    var kb = typeof khai_bao_ky_hieu === 'function'
      ? khai_bao_ky_hieu(dn, tram.thuoc_tinh, null) : null;
    var hinh = (kb && typeof chu_giai_ky_hieu === 'function')
      ? chu_giai_ky_hieu(kb, kieu, 18) : '';

    html += '<span class="cg-qt__hang">'
          + (hinh
              ? '<span class="cg-qt__o">' + hinh + '</span>'
              : '<span class="cg-qt__o cg-qt__o--tron" style="background:'
                + kieu.fillColor + '"></span>')
          + loai + '</span>';
  });

  o.innerHTML = html;
}


/* ==========================================================================
   Bo loc theo loai tram
   ========================================================================== */

function dung_bo_loc_loai() {
  var o = document.getElementById('loc-loai-tram');
  var cac_loai = {};
  TRAM.forEach(function (t) {
    var l = t.thuoc_tinh.loai_tram;
    if (l) cac_loai[l] = true;
  });

  Object.keys(cac_loai).sort().forEach(function (l) {
    var op = document.createElement('option');
    op.value = l;
    op.textContent = l;
    o.appendChild(op);
  });
}


function ap_dung_loc() {
  var loai = document.getElementById('loc-loai-tram').value;
  TRAM_DANG_VE = TRAM.filter(function (t) {
    return !loai || t.thuoc_tinh.loai_tram === loai;
  });
}


/* ==========================================================================
   Ve lai toan bo
   ========================================================================== */

function ve_tat_ca() {
  ap_dung_loc();
  ve_the_kpi();
  ve_diem_tram();
  ve_chu_giai_qt();
  dung_chon_tram();
  ve_bang_tram();

  /* Giu tram dang chon neu no con trong danh sach sau khi loc */
  var con = TRAM_DANG_VE.some(function (t) { return t.ma === MA_DANG_CHON; });
  if (!con) MA_DANG_CHON = null;

  if (!MA_DANG_CHON && TRAM_DANG_VE.length) {
    chon_tram(tram_dang_chu_y().ma, false);
  } else if (MA_DANG_CHON) {
    chon_tram(MA_DANG_CHON, false);
  }
}


/* Tram mo san khi vao trang.
   Thu tu uu tien: muc canh bao, roi theo doi, roi tram co so do, roi tram dau.

   Buoc "co so do" la can thiet: trong pham vi tinh, QTQG chi co mot tram co
   so lieu tren tong so 109 tram. Khong xet den no thi trang mo ra dung vao
   mot tram chi co ket qua kiem ke, va bieu do trong tron. */
function tram_dang_chu_y() {
  var thu_tu = { canh_bao: 0, theo_doi: 1 };

  function hang(tram) {
    var tt = thu_tu[trang_thai_cua(tram)];
    if (tt !== undefined) return tt;
    return co_so_do_ve_duoc(tram) ? 2 : 3;
  }

  var sap = TRAM_DANG_VE.slice().sort(function (a, b) {
    return hang(a) - hang(b);
  });
  return sap[0];
}


/* Tram co it nhat mot thong so so hoc ve duoc bieu do */
function co_so_do_ve_duoc(tram) {
  if (!tram || !tram.so_do) return false;
  return moi_truong_so_do().some(function (tr) {
    return typeof tram.so_do[tr.ma] === 'number';
  });
}


function trang_thai_cua(tram) {
  return (tram.so_do && tram.so_do.trang_thai) || null;
}


/* ==========================================================================
   The chi tieu
   ========================================================================== */

function ve_the_kpi() {
  var co_so_do = 0, so_canh_bao = 0, so_theo_doi = 0;

  TRAM_DANG_VE.forEach(function (t) {
    if (t.so_do) co_so_do++;
    var tt = trang_thai_cua(t);
    if (tt === 'canh_bao') so_canh_bao++;
    else if (tt === 'theo_doi') so_theo_doi++;
  });

  var html = the_so('Công trình quan trắc', TRAM_DANG_VE.length, 'đang theo dõi')
    + the_so('Có số đo mới nhất', co_so_do, 'ghép được với số liệu')
    + the_so('Mức cảnh báo', so_canh_bao, 'cần xử lý')
    + the_so('Mức theo dõi', so_theo_doi, 'tiếp tục giám sát');

  /* Chi hien the nay khi thuc su co ban ghi bi an, de hang the khong dai them
     mot o bang 0 o nhung tinh khong gap truong hop do. */
  var sdc = API_QT.so_do && API_QT.so_do.so_do_cu;
  if (sdc && sdc.so_ban_ghi) {
    var nam = Math.round((sdc.nguong_ngay || 0) / 365 * 10) / 10;
    html += the_so('Ẩn vì số đo quá cũ', sdc.so_ban_ghi,
                   'cũ hơn ' + nam + ' năm');
  }

  document.getElementById('hang-kpi-qt').innerHTML = html;
}


/* ==========================================================================
   Bang toan bo tram
   --------------------------------------------------------------------------
   Dung bang bang DOM API theo dung mau ve_lai_bang() trong table.js: tieu de
   bam duoc de sap xep, o khuyet hien dau gach ngang kem lop .o-trong.
   ========================================================================== */

function gia_tri_o(tram, cot) {
  if (cot.ma === 'ma') return tram.ma;
  if (cot.ma === 'trang_thai') return trang_thai_cua(tram);
  if (tram.thuoc_tinh[cot.ma] !== undefined
      && tram.thuoc_tinh[cot.ma] !== null) {
    return tram.thuoc_tinh[cot.ma];
  }
  return tram.so_do ? tram.so_do[cot.ma] : null;
}


function ve_bang_tram() {
  var bang = document.getElementById('bang-quan-trac');
  var dau = bang.querySelector('thead');
  var than = bang.querySelector('tbody');
  dau.innerHTML = '';
  than.innerHTML = '';

  var hang_dau = document.createElement('tr');
  COT_BANG.forEach(function (cot) {
    var th = document.createElement('th');
    th.textContent = cot.ten + (cot.don_vi ? ' (' + cot.don_vi + ')' : '');
    if (BANG_QT.cot_sap_xep === cot.ma) {
      var mui = document.createElement('span');
      mui.className = 'huong';
      mui.textContent = BANG_QT.tang_dan ? ' ▲' : ' ▼';
      th.appendChild(mui);
    }
    th.addEventListener('click', function () { sap_xep_bang_qt(cot.ma); });
    hang_dau.appendChild(th);
  });
  dau.appendChild(hang_dau);

  sap_xep_danh_sach();

  TRAM_DANG_VE.forEach(function (tram) {
    var tr = document.createElement('tr');
    tr.dataset.ma = tram.ma;
    if (tram.ma === MA_DANG_CHON) tr.classList.add('dang-chon');

    COT_BANG.forEach(function (cot) {
      var td = document.createElement('td');
      var gt = gia_tri_o(tram, cot);

      if (cot.ma === 'nguon') {
        td.textContent = gt === 'QTQG' ? 'QTQG' : 'Kiểm kê tỉnh';
        if (gt !== 'QTQG') td.className = 'o-trong';
      } else if (cot.ma === 'trang_thai') {
        if (gt) {
          var o = document.createElement('span');
          o.className = 'o-tt o-tt--' + gt;
          o.textContent = CAU_HINH.nhan_trang_thai[gt] || gt;
          td.appendChild(o);
        } else {
          td.textContent = '--';
          td.className = 'o-trong';
        }
      } else if (cot.ma === 'thoi_diem') {
        td.textContent = gt ? dinh_dang_thoi_diem(gt) : '--';
        if (!gt) td.className = 'o-trong';
      } else {
        var chu = DINH_DANG[cot.dinh_dang || 'chu'](gt);
        if (chu === null) {
          td.textContent = '--';
          td.className = 'o-trong';
        } else {
          td.textContent = chu;
        }
      }
      tr.appendChild(td);
    });

    tr.addEventListener('click', function () { chon_tram(tram.ma, true); });
    than.appendChild(tr);
  });

  document.getElementById('tom-tat-bang').textContent =
    TRAM_DANG_VE.length + ' trạm'
    + (TRAM_DANG_VE.length === TRAM.length
        ? '' : ' (đã lọc từ ' + TRAM.length + ')');
}


function sap_xep_danh_sach() {
  var cot = COT_BANG.filter(function (c) {
    return c.ma === BANG_QT.cot_sap_xep;
  })[0] || COT_BANG[0];
  var dau = BANG_QT.tang_dan ? 1 : -1;

  TRAM_DANG_VE.sort(function (a, b) {
    var ga = gia_tri_o(a, cot);
    var gb = gia_tri_o(b, cot);

    /* O khuyet luon xuong cuoi, bat ke chieu sap xep */
    if (ga === null || ga === undefined || ga === '') return 1;
    if (gb === null || gb === undefined || gb === '') return -1;

    if (typeof ga === 'number' && typeof gb === 'number') {
      return (ga - gb) * dau;
    }
    return String(ga).localeCompare(String(gb), 'vi') * dau;
  });
}


function sap_xep_bang_qt(ma_cot) {
  if (BANG_QT.cot_sap_xep === ma_cot) {
    BANG_QT.tang_dan = !BANG_QT.tang_dan;
  } else {
    BANG_QT.cot_sap_xep = ma_cot;
    BANG_QT.tang_dan = true;
  }
  ve_bang_tram();
}


/* ==========================================================================
   Chon tram
   ========================================================================== */

function dung_chon_tram() {
  var o = document.getElementById('chon-tram');
  o.innerHTML = '';
  TRAM_DANG_VE.forEach(function (t) {
    var op = document.createElement('option');
    op.value = t.ma;
    op.textContent = t.ma + ' - ' + (t.thuoc_tinh.ten || '');
    o.appendChild(op);
  });
}


function chon_tram(ma, cho_ban_do_bay) {
  MA_DANG_CHON = ma;

  var o = document.getElementById('chon-tram');
  if (o.value !== ma) o.value = ma;

  /* To sang diem dang chon.
     L.circleMarker doi duoc kieu ve, con L.marker dung anh ky hieu thi khong,
     nen danh dau bang mot lop CSS tren chinh the cua no. */
  Object.keys(DIEM_THEO_MA).forEach(function (m) {
    var diem = DIEM_THEO_MA[m];
    var dang_chon = (m === ma);

    if (diem.setStyle) {
      var tram = tim_tram(m);
      if (!tram) return;
      var kieu = kieu_diem(tram);
      if (dang_chon) {
        kieu.weight = Math.max(kieu.weight || 1.5, 3.2);
        kieu.radius = (kieu.radius || 6) + 3;
        kieu.color = '#111827';
      }
      diem.setStyle(kieu);
    } else if (diem.getElement && diem.getElement()) {
      diem.getElement().classList.toggle('ky-hieu-dang-chon', dang_chon);
    }

    if (dang_chon && diem.bringToFront) diem.bringToFront();
  });

  /* Danh dau dong bang */
  var cac_dong = document.querySelectorAll('#bang-quan-trac tbody tr');
  for (var i = 0; i < cac_dong.length; i++) {
    cac_dong[i].classList.toggle('dang-chon', cac_dong[i].dataset.ma === ma);
  }

  var tram_chon = tim_tram(ma);
  if (cho_ban_do_bay && tram_chon && ban_do_qt) {
    ban_do_qt.panTo([tram_chon.vi_do, tram_chon.kinh_do]);
  }

  dung_chon_thong_so();
  nap_va_ve_chuoi();
}


function tim_tram(ma) {
  return TRAM.filter(function (t) { return t.ma === ma; })[0] || null;
}


/* ==========================================================================
   Chon thong so va ve bieu do chuoi thoi gian
   ========================================================================== */

/* Danh sach khai bao truong, HOP cua moi nhom trong CAU_HINH.truong_realtime,
   giu thu tu khai bao va khong lap truong.

   Khong dung rieng nhom cua rt.loai: co tram cua QTQG do ca muc nuoc lan chat
   luong nuoc, lay mot nhom thi mat phan con lai. */
function moi_truong_so_do() {
  var danh_sach = [];
  var da_co = {};
  Object.keys(CAU_HINH.truong_realtime).forEach(function (nhom) {
    CAU_HINH.truong_realtime[nhom].forEach(function (tr) {
      if (da_co[tr.ma]) return;
      da_co[tr.ma] = true;
      danh_sach.push(tr);
    });
  });
  return danh_sach;
}


/* Ten cac thong so cua mot tram da bi AN ban ghi so do vi qua cu.

   Ban ghi bi an thi gia tri khong ra den day nua, nhung backend van gui kem
   ten thong so trong khoi so_do_cu. Khong co danh sach nay thi o chon thong
   so rong, va chuoi cua tram do thanh khong the voi toi tu giao dien, du
   /api/quan-trac/chuoi co y khong loc. */
function thong_so_ban_ghi_bi_an(ma) {
  var sdc = API_QT.so_do && API_QT.so_do.so_do_cu;
  if (!ma || !sdc || !sdc.cong_trinh) return null;

  for (var i = 0; i < sdc.cong_trinh.length; i++) {
    if (sdc.cong_trinh[i].ma === ma) {
      return sdc.cong_trinh[i].thong_so || [];
    }
  }
  return null;
}


/* Cac thong so ve duoc bieu do cho tram dang chon.
   Lay tu CAU_HINH.truong_realtime nen nhan va don vi khong phai viet lai. */
function thong_so_ve_duoc() {
  var tram = tim_tram(MA_DANG_CHON);
  if (!tram) return [];

  if (!tram.so_do) {
    /* Khong co so do hien hanh. Hai truong hop khac han nhau: tram bi an ban
       ghi vi qua cu thi van con chuoi lich su de ve, con tram chua bao gio co
       so do (vi du tram thuy van) thi khong co gi ca. */
    var ten_bi_an = thong_so_ban_ghi_bi_an(tram.ma);
    if (!ten_bi_an || !ten_bi_an.length) return [];

    return moi_truong_so_do().filter(function (tr) {
      return ten_bi_an.indexOf(tr.ma) >= 0;
    });
  }

  return moi_truong_so_do().filter(function (tr) {
    /* Chi thong so so hoc moi ve duoc duong bieu do */
    return typeof tram.so_do[tr.ma] === 'number';
  });
}


function dung_chon_thong_so() {
  var o = document.getElementById('chon-thong-so');
  var dang_chon = o.value;
  var cac_thong_so = thong_so_ve_duoc();

  o.innerHTML = '';
  cac_thong_so.forEach(function (tr) {
    var op = document.createElement('option');
    op.value = tr.ma;
    op.textContent = tr.ten;
    o.appendChild(op);
  });

  if (cac_thong_so.length === 0) {
    var op0 = document.createElement('option');
    op0.value = '';
    op0.textContent = 'Không có thông số số học';
    o.appendChild(op0);
    return;
  }

  /* Giu thong so cu neu tram moi cung co, de nguoi dung so sanh duoc */
  var con = cac_thong_so.some(function (tr) { return tr.ma === dang_chon; });
  o.value = con ? dang_chon : cac_thong_so[0].ma;
}


function nap_va_ve_chuoi() {
  var ma = MA_DANG_CHON;
  var thong_so = document.getElementById('chon-thong-so').value;
  var tram = tim_tram(ma);

  var ten = (tram && tram.thuoc_tinh.ten) || ma || '';
  document.getElementById('ten-bieu-do').textContent =
    'Diễn biến theo thời gian — ' + ten;

  if (!ma || !thong_so) {
    xoa_bieu_do();
    document.getElementById('chu-thich-chuoi').textContent =
      'Trạm này chưa có thông số nào vẽ được biểu đồ.';
    return;
  }

  document.getElementById('chu-thich-chuoi').textContent = 'Đang nạp chuỗi...';

  nap_chuoi_qtqg(ma, thong_so).then(function (ch) {
    if (!ch) {
      xoa_bieu_do();
      document.getElementById('chu-thich-chuoi').textContent =
        'Không nạp được chuỗi: ' + (API_QT.loi || 'không rõ');
      return;
    }
    ve_bieu_do_chuoi(ch, thong_so);
  });
}


function khai_bao_thong_so(ma_thong_so) {
  var cac_nhom = CAU_HINH.truong_realtime;
  var ket_qua = null;
  Object.keys(cac_nhom).forEach(function (nhom) {
    cac_nhom[nhom].forEach(function (tr) {
      if (!ket_qua && tr.ma === ma_thong_so) ket_qua = tr;
    });
  });
  return ket_qua || { ma: ma_thong_so, ten: ma_thong_so };
}


function xoa_bieu_do() {
  if (bieu_do_chuoi) {
    bieu_do_chuoi.destroy();
    bieu_do_chuoi = null;
  }
}


function ve_bieu_do_chuoi(chuoi, ma_thong_so) {
  xoa_bieu_do();

  var tr = khai_bao_thong_so(ma_thong_so);
  var cac_diem = chuoi.diem || [];

  if (cac_diem.length === 0) {
    document.getElementById('chu-thich-chuoi').textContent =
      'Chưa có chuỗi số liệu cho thông số này. Chuỗi được tích lũy dần mỗi '
      + 'lượt làm mới, hoặc đọc trực tiếp nếu nguồn QTQG lưu lịch sử.';
    return;
  }

  /* Lay mau tu bien CSS nen bieu do tu doi theo nen sang toi, giong cach
     ve_bieu_do_realtime() trong identify.js dang lam. */
  var kieu = getComputedStyle(document.body);
  var mau_chu = kieu.getPropertyValue('--chu-mo').trim() || '#5c6b7a';
  var mau_luoi = kieu.getPropertyValue('--vien-nhat').trim() || '#e7ebef';

  var o = document.getElementById('bd-chuoi');
  bieu_do_chuoi = new Chart(o, {
    type: 'line',
    data: {
      labels: cac_diem.map(function (d) {
        return dinh_dang_thoi_diem(d.thoi_diem);
      }),
      datasets: [{
        label: tr.ten + (tr.don_vi ? ' (' + tr.don_vi + ')' : ''),
        data: cac_diem.map(function (d) { return d.gia_tri; }),
        borderColor: MAU.song,
        backgroundColor: 'rgba(21, 114, 161, .12)',
        borderWidth: 2,
        pointRadius: cac_diem.length > 60 ? 0 : 2.5,
        tension: 0.25,
        fill: true,
      }],
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      plugins: {
        legend: { labels: { color: mau_chu } },
        tooltip: {
          callbacks: {
            label: function (muc) {
              return dinh_dang_gia_tri(tr, muc.parsed.y);
            },
          },
        },
      },
      scales: {
        x: {
          ticks: { color: mau_chu, maxTicksLimit: 8 },
          grid: { color: mau_luoi },
        },
        y: {
          ticks: { color: mau_chu },
          grid: { color: mau_luoi },
        },
      },
    },
  });

  var chu = cac_diem.length + ' điểm đo'
          + (chuoi.che_do === 'that' ? '' : ' (dữ liệu thử nghiệm)');

  /* Tram bi an so do hien hanh van ve duoc chuoi lich su. Noi ro o day, de
     khong ai tuong duong bieu do nay la so lieu dang theo doi. */
  if (thong_so_ban_ghi_bi_an(MA_DANG_CHON)) {
    chu += '. Công trình này đã bị ẩn số đo hiện hành vì quá cũ; biểu đồ là '
         + 'chuỗi lịch sử, hãy xem mốc ngày trên trục ngang.';
  }

  document.getElementById('chu-thich-chuoi').textContent = chu;
}


/* ==========================================================================
   Lam moi
   ========================================================================== */

function lam_moi() {
  var nut = document.getElementById('nut-lam-moi');
  nut.disabled = true;
  nut.textContent = 'Đang nạp...';

  return Promise.all([nap_tram_qtqg(), nap_so_do_qtqg()])
    .then(function (kq) {
      if (kq[0] && kq[1]) {
        gop_du_lieu();
        cap_nhat_dai_thong_bao_qt();
        ve_tat_ca();
      } else {
        document.getElementById('dong-cap-nhat').textContent =
          'Làm mới thất bại: ' + (API_QT.loi || 'không rõ');
      }
    })
    .then(function () {
      nut.disabled = false;
      nut.textContent = 'Làm mới';
    });
}


function bat_lam_moi_dinh_ky_qt() {
  var phut = (CAU_HINH.api && CAU_HINH.api.chu_ky_lam_moi_phut) || 0;
  if (!phut || phut <= 0) return;
  if (dong_ho_lam_moi) clearInterval(dong_ho_lam_moi);
  dong_ho_lam_moi = setInterval(lam_moi, phut * 60000);
}


/* ==========================================================================
   Xuat CSV
   --------------------------------------------------------------------------
   Xuat dung bo dang hien thi: da loc va da sap xep, giong cach
   xuat_bang_csv() trong table.js lam voi BANG.hang_dang_ve.
   ========================================================================== */

function xuat_csv_quan_trac() {
  var cot_them = [
    { ma: 'kinh_do', ten: 'Kinh độ' },
    { ma: 'vi_do', ten: 'Vĩ độ' },
  ];

  var tieu_de = COT_BANG.map(function (c) {
    return c.ten + (c.don_vi ? ' (' + c.don_vi + ')' : '');
  }).concat(cot_them.map(function (c) { return c.ten; }));

  var cac_hang = TRAM_DANG_VE.map(function (tram) {
    var hang = COT_BANG.map(function (cot) {
      var gt = gia_tri_o(tram, cot);
      if (cot.ma === 'trang_thai' && gt) {
        return CAU_HINH.nhan_trang_thai[gt] || gt;
      }
      if (cot.ma === 'nguon') {
        return gt === 'QTQG' ? 'QTQG' : 'Kiểm kê tỉnh';
      }
      return gt === null || gt === undefined ? '' : gt;
    });
    hang.push(tram.kinh_do, tram.vi_do);
    return hang;
  });

  var goi = API_QT.so_do || {};
  var hau_to = la_so_lieu_that() ? '' : '_thu_nghiem';
  tai_ve_csv('quan_trac_qtqg' + hau_to + '.csv', tieu_de, cac_hang);
}


/* ==========================================================================
   Chi tiet mot tram trong hop thoai
   ========================================================================== */

function mo_chi_tiet_tram(ma) {
  var tram = tim_tram(ma);
  if (!tram) return;

  var tt = tram.thuoc_tinh;
  var rt = tram.so_do;
  var html = '';

  html += '<div class="ct-dau">'
        + '<div class="ct-lop">' + (tt.loai_tram || 'Trạm quan trắc') + '</div>'
        + '<div class="ct-ten">' + (tt.ten || ma) + '</div>'
        + '<div class="ct-ma">' + ma + '</div>';
  if (rt && rt.trang_thai) {
    /* Lop CSS dat ten bang gach ngang (.tt-binh-thuong) con gia tri
       trang_thai dung gach duoi, nen phai doi truoc khi ghep vao class. */
    html += '<div class="ct-trang-thai tt-'
          + rt.trang_thai.replace(/_/g, '-') + '">'
          + (CAU_HINH.nhan_trang_thai[rt.trang_thai] || rt.trang_thai)
          + '</div>';
  }
  html += '</div>';

  /* Khoi so do, lap theo khai bao trong config.js */
  if (rt) {
    var nhom = moi_truong_so_do();
    var cac_dong = '';
    nhom.forEach(function (tr) {
      var chu = dinh_dang_gia_tri(tr, rt[tr.ma]);
      if (chu === null) return;   /* thong so khong co thi bo qua, khong ve */
      cac_dong += '<tr><th>' + tr.ten + '</th><td>' + chu + '</td></tr>';
    });
    if (cac_dong) {
      html += '<div class="ct-khoi"><div class="ct-khoi__ten">'
            + 'Số đo mới nhất</div>'
            + '<table class="ct-bang">' + cac_dong + '</table></div>';
    }
    /* Noi ro WQI tu dau ra. Nguoi dung can phan biet so do co quan chu
       quan cong bo voi so do trang nay tu tinh. */
    if (rt.wqi !== undefined && rt.wqi !== null) {
      html += '<p class="ghi-chu-nho">'
            + (rt.wqi_tu_tinh
                ? 'Chỉ số WQI do hệ thống tự tính từ các thông số trên, theo '
                  + 'Quyết định 1460/QĐ-TCMT.'
                : 'Chỉ số WQI lấy trực tiếp từ nguồn Quan trắc Quốc gia.')
            + '</p>';
      if (rt.nhiet_do_uoc_tinh) {
        html += '<p class="ghi-chu-nho">Kỳ đo này không có số đo nhiệt độ '
              + 'nước. Nhiệt độ hiển thị là <strong>ước tính</strong> từ '
              + 'trung bình nhiều năm cùng tháng của chính trạm, dùng để quy '
              + 'DO ra phần trăm bão hòa. Đây là số suy diễn, không phải số '
              + 'đo.</p>';
      }
    } else if (rt.wqi_ly_do) {
      html += '<p class="ghi-chu-nho">Chưa tính được WQI: ' + rt.wqi_ly_do;
      if (rt.wqi_thieu_thong_so && rt.wqi_thieu_thong_so.length) {
        html += ' Cần bổ sung: ' + rt.wqi_thieu_thong_so.join(', ') + '.';
      }
      html += '</p>';
    }
  } else {
    html += '<p class="ghi-chu-nho">Trạm này chưa ghép được số đo nào.</p>';
  }

  /* Khoi thuoc tinh tinh */
  var tt_dong = '';
  CAU_HINH.lop.quan_trac.truong.forEach(function (tr) {
    var chu = dinh_dang_gia_tri(tr, tt[tr.ma]);
    if (chu === null) return;
    tt_dong += '<tr><th>' + tr.ten + '</th><td>' + chu + '</td></tr>';
  });
  if (tt_dong) {
    html += '<div class="ct-khoi"><div class="ct-khoi__ten">Thuộc tính</div>'
          + '<table class="ct-bang">' + tt_dong + '</table></div>';
  }

  html += '<div class="ct-nguon">Nguồn: ' + (tt.nguon_dl || '--') + '</div>';

  mo_hop_thoai('Chi tiết trạm quan trắc', html);
}


/* ==========================================================================
   Giao dien sang toi
   ========================================================================== */

function khoi_phuc_giao_dien_qt() {
  var da_luu = null;
  try { da_luu = localStorage.getItem('giao_dien'); } catch (e) { da_luu = null; }
  if (da_luu) document.documentElement.setAttribute('data-giao-dien', da_luu);
}


function doi_giao_dien_qt() {
  var hien_tai = document.documentElement.getAttribute('data-giao-dien');
  var moi;
  if (hien_tai === 'toi') moi = 'sang';
  else if (hien_tai === 'sang') moi = 'toi';
  else {
    /* Chua chon lan nao: dao nguoc so voi thiet dat cua he dieu hanh.
       Giong doi_giao_dien() trong app.js. */
    var he_toi = window.matchMedia('(prefers-color-scheme: dark)').matches;
    moi = he_toi ? 'sang' : 'toi';
  }

  document.documentElement.setAttribute('data-giao-dien', moi);
  try { localStorage.setItem('giao_dien', moi); } catch (e) { /* bo qua */ }

  /* Doi ban do nen cho khop voi nen giao dien */
  if (ban_do_qt) dat_nen_ban_do_nho();

  /* Bieu do lay mau tu bien CSS luc ve nen phai ve lai */
  nap_va_ve_chuoi();
}


/* ==========================================================================
   Gan su kien
   ========================================================================== */

function gan_su_kien() {
  document.getElementById('nut-lam-moi')
    .addEventListener('click', lam_moi);

  document.getElementById('loc-loai-tram')
    .addEventListener('change', ve_tat_ca);

  document.getElementById('chon-tram')
    .addEventListener('change', function () { chon_tram(this.value, true); });

  document.getElementById('chon-thong-so')
    .addEventListener('change', nap_va_ve_chuoi);

  document.getElementById('xuat-bang')
    .addEventListener('click', xuat_csv_quan_trac);

  document.getElementById('nut-giao-dien')
    .addEventListener('click', doi_giao_dien_qt);

  document.getElementById('dong-thong-bao')
    .addEventListener('click', function () {
      document.getElementById('dai-thong-bao').hidden = true;
    });

  document.getElementById('dong-hop-thoai')
    .addEventListener('click', dong_hop_thoai);
  document.getElementById('lop-mo')
    .addEventListener('click', dong_hop_thoai);

  document.addEventListener('keydown', function (e) {
    if (e.key === 'Escape') dong_hop_thoai();
  });

  /* Nhap doi vao dong bang de mo chi tiet day du */
  document.getElementById('bang-quan-trac')
    .addEventListener('dblclick', function (e) {
      var tr = e.target.closest('tr[data-ma]');
      if (tr) mo_chi_tiet_tram(tr.dataset.ma);
    });
}
