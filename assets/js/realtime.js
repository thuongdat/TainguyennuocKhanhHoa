/* ==========================================================================
   realtime.js - Du lieu quan trac theo thoi gian thuc va canh bao
   --------------------------------------------------------------------------
   Du lieu hinh hoc (vi tri ho, tram, cong trinh) nam trong cac tep GeoJSON
   tinh. So do theo thoi gian nam rieng trong data/realtime.json, duoc GitHub
   Actions cap nhat dinh ky. Hai nguon ghep voi nhau qua truong "ma".
   Nho tach doi nhu vay, khi doi tu du lieu mo phong sang nguon quan trac that
   thi khong phai sua gi o phan ban do.
   ========================================================================== */

var DU_LIEU_RT = null;

/* --------------------------------------------------------------------------
   Nap tep realtime.json
   -------------------------------------------------------------------------- */
function nap_realtime() {
  /* Them tham so thoi gian de tranh trinh duyet dung ban cache cu */
  return fetch(duong_dan_du_lieu('realtime.json') + '&t=' + Date.now())
    .then(function (r) {
      if (!r.ok) throw new Error('HTTP ' + r.status);
      return r.json();
    })
    .then(function (dl) {
      DU_LIEU_RT = dl;
      cap_nhat_thoi_diem();
      cap_nhat_huy_hieu_canh_bao();
      return dl;
    })
    .catch(function (e) {
      console.warn('Không nạp được dữ liệu thời gian thực: ' + e.message);
      document.getElementById('thoi-diem-cap-nhat').textContent = 'chưa có dữ liệu';
      return null;
    });
}

/* Tra ve ban ghi quan trac cua mot ma doi tuong, hoac null */
function lay_realtime(ma) {
  if (!DU_LIEU_RT || !DU_LIEU_RT.doi_tuong || !ma) return null;
  return DU_LIEU_RT.doi_tuong[ma] || null;
}

/* --------------------------------------------------------------------------
   Lam moi: nap lai du lieu va ve lai cac lop co ghep quan trac
   -------------------------------------------------------------------------- */
function lam_moi_realtime() {
  return nap_realtime().then(function (dl) {
    if (!dl) return;
    Object.keys(CAU_HINH.lop).forEach(function (ma_lop) {
      if (CAU_HINH.lop[ma_lop].realtime) ve_lop(ma_lop);
    });
    dung_chu_giai();
  });
}

/* Hen gio lam moi dinh ky */
function bat_lam_moi_dinh_ky() {
  var phut = CAU_HINH.he_thong.chu_ky_lam_moi_phut;
  if (!phut || phut <= 0) return;
  setInterval(lam_moi_realtime, phut * 60000);
}

/* --------------------------------------------------------------------------
   Hien thi thoi diem cap nhat o chan trang
   -------------------------------------------------------------------------- */
function cap_nhat_thoi_diem() {
  var o = document.getElementById('thoi-diem-cap-nhat');
  if (!DU_LIEU_RT || !DU_LIEU_RT.thoi_diem || !DU_LIEU_RT.so_doi_tuong) { o.textContent = '--'; return; }

  var d = new Date(DU_LIEU_RT.thoi_diem);
  var chu = isNaN(d.getTime())
    ? DU_LIEU_RT.thoi_diem
    : d.toLocaleString('vi-VN', { day: '2-digit', month: '2-digit', year: 'numeric',
                                 hour: '2-digit', minute: '2-digit' });

  o.textContent = chu;
  o.title = DU_LIEU_RT.nguon_dl || '';

  /* Danh dau ro khi so lieu dang la mo phong */
  if (DU_LIEU_RT.che_do !== 'that') {
    o.textContent = chu + ' (mô phỏng)';
  }
}

/* --------------------------------------------------------------------------
   Huy hieu so canh bao tren thanh menu
   -------------------------------------------------------------------------- */
function cap_nhat_huy_hieu_canh_bao() {
  var o = document.getElementById('so-canh-bao');
  if (!DU_LIEU_RT || !DU_LIEU_RT.canh_bao) { o.hidden = true; return; }

  var so_nghiem_trong = DU_LIEU_RT.canh_bao.filter(function (c) {
    return c.muc === 'canh_bao';
  }).length;

  if (so_nghiem_trong === 0) { o.hidden = true; return; }
  o.hidden = false;
  o.textContent = so_nghiem_trong;
}

/* --------------------------------------------------------------------------
   Hop thoai danh sach canh bao
   -------------------------------------------------------------------------- */
function mo_hop_canh_bao() {
  if (!DU_LIEU_RT || !DU_LIEU_RT.canh_bao || DU_LIEU_RT.canh_bao.length === 0) {
    mo_hop_thoai('Cảnh báo',
      '<p class="ghi-chu-nho">Hiện không có cảnh báo nào. '
      + 'Tất cả đối tượng quan trắc đang ở trạng thái bình thường.</p>');
    return;
  }

  var cb = DU_LIEU_RT.canh_bao;
  var so_cao = cb.filter(function (c) { return c.muc === 'canh_bao'; }).length;

  var html = '<div class="the-so">'
    + the_so('Mức cảnh báo', so_cao, 'cần xử lý')
    + the_so('Mức theo dõi', cb.length - so_cao, 'tiếp tục giám sát')
    + the_so('Đối tượng quan trắc', DU_LIEU_RT.so_doi_tuong || 0, 'đang theo dõi')
    + '</div>';

  html += '<p class="ghi-chu-nho" style="margin-bottom:10px">'
        + 'Nhấp vào một dòng để phóng tới đối tượng tương ứng trên bản đồ.</p>';

  cb.forEach(function (c) {
    html += '<div class="hang-canh-bao muc-' + c.muc + '" data-ma="' + c.ma + '">'
          + '<div><div class="hang-canh-bao__ten">' + c.ten + '</div>'
          + '<div class="hang-canh-bao__nd">' + c.noi_dung + '</div></div></div>';
  });

  html += '<div class="ct-nut" style="margin-top:14px">'
        + '<button class="nut nut--chinh" id="xuat-canh-bao">Xuất danh sách ra CSV</button>'
        + '</div>';

  mo_hop_thoai('Cảnh báo quan trắc', html);

  var cac_hang = document.querySelectorAll('#hop-thoai-than .hang-canh-bao');
  for (var i = 0; i < cac_hang.length; i++) {
    cac_hang[i].addEventListener('click', function () {
      var vi_tri = tim_doi_tuong_theo_ma(this.dataset.ma);
      if (!vi_tri) {
        hien_mach_bao('Không tìm thấy đối tượng này trong các lớp đã nạp.');
        return;
      }
      dong_hop_thoai();
      di_den_doi_tuong(vi_tri.ma_lop, vi_tri.chi_so);
    });
  }

  document.getElementById('xuat-canh-bao').addEventListener('click', function () {
    var hang = cb.map(function (c) {
      return [c.ma, c.ten, c.loai,
              c.muc === 'canh_bao' ? 'Cảnh báo' : 'Theo dõi', c.noi_dung];
    });
    tai_ve_csv('canh_bao_' + (DU_LIEU_RT.thoi_diem || '').slice(0, 10) + '.csv',
               ['Mã', 'Tên đối tượng', 'Loại', 'Mức', 'Nội dung'], hang);
  });
}

/* Tim mot doi tuong trong moi lop theo ma, de nhay tu canh bao sang ban do */
function tim_doi_tuong_theo_ma(ma) {
  var ket_qua = null;
  Object.keys(LOP).some(function (ma_lop) {
    var l = LOP[ma_lop];
    if (l.loi) return false;
    for (var i = 0; i < l.doi_tuong.length; i++) {
      if (l.doi_tuong[i].thuoc_tinh[l.dn.khoa] === ma) {
        ket_qua = { ma_lop: ma_lop, chi_so: i };
        return true;
      }
    }
    return false;
  });
  return ket_qua;
}

/* the_so() da chuyen sang assets/js/dung_chung.js, vi trang thong ke va trang
   quan trac cung dung ma khong nap duoc tep nay. Khong dinh nghia lai o day. */
