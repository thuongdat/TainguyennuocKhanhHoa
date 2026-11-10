/* ==========================================================================
   identify.js - Truy van doi tuong bang cach nhap chuot
   --------------------------------------------------------------------------
   Diem khac biet: thay vi dua vao su kien click cua tung hinh (SVG chi bat
   duoc hinh nam tren cung), tep nay tu kiem tra hinh hoc cua MOI doi tuong
   dang hien. Nho vay neu mot diem nhap trung nhieu doi tuong thuoc nhieu lop
   khac nhau, ta liet ke duoc tat ca trong mot danh sach tha xuong.
   ========================================================================== */

/* Dung sai nhap chuot, tinh bang pixel tren man hinh */
var DUNG_SAI_PX = 10;

/* Danh sach doi tuong trung o lan nhap gan nhat */
var KET_QUA_TRUNG = [];

/* Doi tuong bieu do Chart.js dang hien, can huy truoc khi ve cai moi */
var bieu_do_hien_tai = null;

/* --------------------------------------------------------------------------
   Truy van tai mot diem tren ban do
   -------------------------------------------------------------------------- */
function truy_van_tai_diem(latlng) {
  var ket_qua = [];

  Object.keys(LOP).forEach(function (ma_lop) {
    var l = LOP[ma_lop];
    if (!l || l.loi || !l.hien || l.dn.khong_truy_van) return;

    l.doi_tuong.filter(qua_bo_loc).forEach(function (dt) {
      var kq = kiem_tra_trung(dt, latlng, l.dn);
      if (!kq) return;
      ket_qua.push({
        ma_lop: ma_lop,
        ten_lop: l.dn.ten,
        chi_so: dt.chi_so,
        ten: nhan_doi_tuong(ma_lop, dt.thuoc_tinh),
        uu_tien: kq.uu_tien,
        khoang_cach: kq.khoang_cach,
      });
    });
  });

  /* Sap xep: diem truoc, roi duong, roi vung; cung loai thi gan hon truoc */
  ket_qua.sort(function (a, b) {
    return a.uu_tien - b.uu_tien || a.khoang_cach - b.khoang_cach;
  });

  KET_QUA_TRUNG = ket_qua;

  if (ket_qua.length === 0) {
    dong_chi_tiet();
    hien_mach_bao('Không có đối tượng nào tại vị trí nhấp. '
                + 'Thử nhấp gần hơn hoặc bật thêm lớp dữ liệu.', 3000);
    return;
  }

  hien_chi_tiet(ket_qua, 0);
}

/* --------------------------------------------------------------------------
   Kiem tra mot doi tuong co trung diem nhap hay khong
   Tra ve null neu khong trung, hoac { uu_tien, khoang_cach }
   -------------------------------------------------------------------------- */
function kiem_tra_trung(dt, latlng, dn) {
  var hh = dt.hinh_hoc;
  if (!hh) return null;
  var p_nhap = ban_do.latLngToLayerPoint(latlng);

  /* --- Diem --- */
  if (hh.type === 'Point' || hh.type === 'MultiPoint') {
    var cac_diem = (hh.type === 'Point') ? [hh.coordinates] : hh.coordinates;
    var gan_nhat = Infinity;
    cac_diem.forEach(function (c) {
      var d = p_nhap.distanceTo(toa_do_sang_pixel(c));
      if (d < gan_nhat) gan_nhat = d;
    });
    /* Dung sai bang ban kinh ky hieu cong them mot chut cho de nhap */
    var kieu_ve = dn.kieu_ve(dt.thuoc_tinh, lay_realtime(dt.thuoc_tinh[dn.khoa]));
    var nguong = Math.max(DUNG_SAI_PX, (kieu_ve.radius || 6) + 4);
    return gan_nhat <= nguong ? { uu_tien: 1, khoang_cach: gan_nhat } : null;
  }

  /* --- Duong --- */
  if (hh.type === 'LineString' || hh.type === 'MultiLineString') {
    var cac_duong = (hh.type === 'LineString') ? [hh.coordinates] : hh.coordinates;
    var min_d = Infinity;
    cac_duong.forEach(function (duong) {
      var d = khoang_cach_den_duong(p_nhap, duong);
      if (d < min_d) min_d = d;
    });
    var kv = dn.kieu_ve(dt.thuoc_tinh, null);
    var nguong_duong = DUNG_SAI_PX + (kv.weight || 2) / 2;
    return min_d <= nguong_duong ? { uu_tien: 2, khoang_cach: min_d } : null;
  }

  /* --- Vung ---
     Vung chi tinh la trung khi diem nhap nam BEN TRONG. Khong dung dung sai
     theo pixel nhu diem va duong, vi o muc zoom xa, 10 pixel tuong duong vai
     km tren thuc dia: mot cu nhap se trung duong bien cua hang loat xa lan can
     va danh sach tra ve day nhung doi tuong nguoi dung khong he nham toi.
     Vung von la doi tuong dien tich, nham vao giua la du. */
  if (hh.type === 'Polygon' || hh.type === 'MultiPolygon') {
    var cac_vung = (hh.type === 'Polygon') ? [hh.coordinates] : hh.coordinates;
    var diem_ll = [latlng.lng, latlng.lat];

    for (var i = 0; i < cac_vung.length; i++) {
      if (diem_trong_vung(diem_ll, cac_vung[i])) {
        return { uu_tien: 3, khoang_cach: 0 };
      }
    }
    return null;
  }

  return null;
}

/* Chuyen mot cap [lon, lat] sang toa do pixel tren man hinh */
function toa_do_sang_pixel(c) {
  return ban_do.latLngToLayerPoint(L.latLng(c[1], c[0]));
}

/* Khoang cach pixel ngan nhat tu mot diem den mot chuoi doan thang */
function khoang_cach_den_duong(p, duong) {
  var min_d = Infinity;
  for (var i = 0; i < duong.length - 1; i++) {
    var d = khoang_cach_den_doan(p, toa_do_sang_pixel(duong[i]),
                                    toa_do_sang_pixel(duong[i + 1]));
    if (d < min_d) min_d = d;
  }
  /* Truong hop duong chi co mot dinh */
  if (duong.length === 1) min_d = p.distanceTo(toa_do_sang_pixel(duong[0]));
  return min_d;
}

/* Khoang cach tu diem p den doan thang ab, tat ca trong khong gian pixel */
function khoang_cach_den_doan(p, a, b) {
  var dx = b.x - a.x, dy = b.y - a.y;
  var do_dai_binh_phuong = dx * dx + dy * dy;
  if (do_dai_binh_phuong === 0) return p.distanceTo(a);
  /* t la vi tri hinh chieu cua p tren ab, kep trong doan [0, 1] */
  var t = ((p.x - a.x) * dx + (p.y - a.y) * dy) / do_dai_binh_phuong;
  t = Math.max(0, Math.min(1, t));
  var cx = a.x + t * dx, cy = a.y + t * dy;
  return Math.sqrt((p.x - cx) * (p.x - cx) + (p.y - cy) * (p.y - cy));
}

/* Kiem tra diem trong polygon bang thuat toan phong tia (ray casting).
   vung[0] la vong ngoai, cac vong sau la lo khoet. */
function diem_trong_vung(diem, vung) {
  if (!trong_vong(diem, vung[0])) return false;
  for (var i = 1; i < vung.length; i++) {
    if (trong_vong(diem, vung[i])) return false;   /* nam trong lo khoet */
  }
  return true;
}

function trong_vong(diem, vong) {
  var x = diem[0], y = diem[1];
  var ben_trong = false;
  for (var i = 0, j = vong.length - 1; i < vong.length; j = i++) {
    var xi = vong[i][0], yi = vong[i][1];
    var xj = vong[j][0], yj = vong[j][1];
    var cat = ((yi > y) !== (yj > y))
           && (x < (xj - xi) * (y - yi) / (yj - yi) + xi);
    if (cat) ben_trong = !ben_trong;
  }
  return ben_trong;
}

/* --------------------------------------------------------------------------
   Hien thi bang thong tin ben phai
   -------------------------------------------------------------------------- */
function hien_chi_tiet(danh_sach, vi_tri_chon) {
  document.getElementById('huong-dan-click').hidden = true;

  var o_chon = document.getElementById('chon-doi-tuong');
  var o_select = document.getElementById('danh-sach-trung');

  /* Danh sach tha xuong chi hien khi mot diem nhap trung nhieu doi tuong */
  if (danh_sach.length > 1) {
    document.getElementById('so-doi-tuong-trung').textContent = danh_sach.length;
    o_select.innerHTML = '';
    danh_sach.forEach(function (r, i) {
      var opt = document.createElement('option');
      opt.value = String(i);
      opt.textContent = r.ten + '  —  ' + r.ten_lop;
      o_select.appendChild(opt);
    });
    o_select.value = String(vi_tri_chon);
    o_chon.hidden = false;
  } else {
    o_chon.hidden = true;
  }

  var chon = danh_sach[vi_tri_chon];
  var l = LOP[chon.ma_lop];
  var dt = l.doi_tuong[chon.chi_so];

  var hop = document.getElementById('chi-tiet-doi-tuong');
  hop.hidden = false;
  hop.innerHTML = dung_html_chi_tiet(chon.ma_lop, dt);

  gan_su_kien_chi_tiet(chon.ma_lop, dt);
  ve_bieu_do_realtime(dt.thuoc_tinh[l.dn.khoa]);
  nhay_sang_doi_tuong(dt);
  chon_hang_bang(chon.ma_lop, chon.chi_so);
}

function dung_html_chi_tiet(ma_lop, dt) {
  var dn = CAU_HINH.lop[ma_lop];
  var tt = dt.thuoc_tinh;
  var ma = tt[dn.khoa];
  var rt = lay_realtime(ma);

  var html = '<div class="ct-dau">'
           + '<span class="ct-lop">' + dn.ten + '</span>'
           + '<div class="ct-ten">' + nhan_doi_tuong(ma_lop, tt) + '</div>'
           + '<div class="ct-ma">Mã đối tượng: ' + (ma || '--') + '</div>';

  if (rt) {
    /* Lop CSS dat ten bang gach ngang (.tt-binh-thuong) con gia tri
       trang_thai dung gach duoi, nen phai doi truoc khi ghep vao class. */
    html += '<span class="ct-trang-thai tt-'
          + rt.trang_thai.replace(/_/g, '-') + '">'
          + CAU_HINH.nhan_trang_thai[rt.trang_thai] + '</span>';
  }
  html += '</div>';

  /* ----- Khoi so lieu quan trac thoi gian thuc ----- */
  if (rt) {
    var truong_rt = CAU_HINH.truong_realtime[rt.loai] || [];
    html += '<div class="ct-khoi"><div class="ct-khoi__ten">'
          + 'Số liệu quan trắc mới nhất</div><table class="ct-bang"><tbody>';
    truong_rt.forEach(function (tr) {
      var gt = dinh_dang_gia_tri(tr, rt[tr.ma]);
      if (gt === null) return;
      html += '<tr><th>' + tr.ten + '</th><td>' + gt + '</td></tr>';
    });
    html += '</tbody></table>';

    /* Thanh ty le dung tich ho chua */
    if (rt.loai === 'ho_chua') {
      html += thanh_ty_le(rt.ty_le_dung_tich, mau_theo_dung_tich(rt.ty_le_dung_tich));
    }

    html += '<div class="ct-bieu-do"><canvas id="canvas-bieu-do"></canvas></div>';
    html += '</div>';
  }

  /* ----- Khoi suc chiu tai, chi co o lop doan song ----- */
  if (ma_lop === 'doan_song') {
    var mau_sct = tt.trang_thai === 'Không còn khả năng tiếp nhận' ? MAU.xau
                : (tt.trang_thai === 'Gần ngưỡng' ? MAU.theo_doi : MAU.tot);
    html += '<div class="ct-khoi"><div class="ct-khoi__ten">'
          + 'Khả năng tiếp nhận nước thải</div>'
          + thanh_ty_le(tt.ty_le_con_lai, mau_sct)
          + '<p class="ghi-chu-nho">Còn lại '
          + DINH_DANG.so_le(tt.l_tn_kg_ngay) + ' kg/ngày, tương đương '
          + DINH_DANG.phan_tram(tt.ty_le_con_lai) + ' tải lượng tối đa. '
          + 'Kết luận: <strong>' + tt.trang_thai + '</strong>.</p></div>';
  }

  /* ----- Khoi thuoc tinh ----- */
  html += '<div class="ct-khoi"><div class="ct-khoi__ten">Thuộc tính đối tượng</div>'
        + '<table class="ct-bang"><tbody>';
  dn.truong.forEach(function (tr) {
    var gt = dinh_dang_gia_tri(tr, tt[tr.ma]);
    if (gt === null) return;
    html += '<tr><th>' + tr.ten + '</th><td>' + gt + '</td></tr>';
  });
  html += '</tbody></table></div>';

  /* ----- Canh bao giay phep sap het han ----- */
  if (tt.ngay_het_han) {
    var con_lai = so_ngay_den(tt.ngay_het_han);
    if (con_lai !== null && con_lai < 180) {
      var loi_nhac = con_lai < 0
        ? 'Giấy phép đã hết hạn ' + Math.abs(con_lai) + ' ngày.'
        : 'Giấy phép còn hiệu lực ' + con_lai + ' ngày.';
      html += '<div class="ct-nguon" style="border-left-color:'
            + (con_lai < 0 ? MAU.xau : MAU.theo_doi) + '"><strong>'
            + loi_nhac + '</strong></div>';
    }
  }

  /* ----- Nut tac vu ----- */
  html += '<div class="ct-nut">'
        + '<button class="nut nut--chinh" id="nut-xuat-doi-tuong">Xuất CSV</button>'
        + '<button class="nut" id="nut-phong-to">Phóng tới</button>'
        + '</div>';

  /* ----- Ghi chu nguon du lieu ----- */
  if (tt.nguon_dl) {
    html += '<div class="ct-nguon"><strong>Nguồn dữ liệu:</strong> '
          + tt.nguon_dl + '</div>';
  } else if (dn.du_lieu_that) {
    html += '<div class="ct-nguon" style="border-left-color:' + MAU.tot
          + '"><strong>Dữ liệu thật</strong>, nhập từ shapefile ranh giới '
          + 'hành chính trong thư mục CSDL.</div>';
  }

  return html;
}

/* Thanh ty le ngang, dung cho dung tich ho va suc chiu tai */
function thanh_ty_le(ty_le, mau) {
  var pt = Math.max(0, Math.min(1, Number(ty_le) || 0)) * 100;
  return '<div class="thanh-ty-le"><div class="thanh-ty-le__phan" style="width:'
       + pt.toFixed(1) + '%;background:' + mau + '"></div></div>';
}

function mau_theo_dung_tich(ty_le) {
  if (ty_le > 0.95) return MAU.tran;
  if (ty_le < 0.30) return MAU.xau;
  if (ty_le < 0.50) return MAU.theo_doi;
  return MAU.tot;
}

/* --------------------------------------------------------------------------
   Gan su kien cho cac nut trong bang chi tiet
   -------------------------------------------------------------------------- */
function gan_su_kien_chi_tiet(ma_lop, dt) {
  var nut_xuat = document.getElementById('nut-xuat-doi-tuong');
  if (nut_xuat) {
    nut_xuat.addEventListener('click', function () {
      xuat_mot_doi_tuong(ma_lop, dt);
    });
  }

  var nut_phong = document.getElementById('nut-phong-to');
  if (nut_phong) {
    nut_phong.addEventListener('click', function () {
      di_den_doi_tuong(ma_lop, dt.chi_so);
    });
  }
}

/* Xuat thuoc tinh cua mot doi tuong ra CSV dang hai cot */
function xuat_mot_doi_tuong(ma_lop, dt) {
  var dn = CAU_HINH.lop[ma_lop];
  var tt = dt.thuoc_tinh;
  var hang = [];

  dn.truong.forEach(function (tr) {
    hang.push([tr.ten, tt[tr.ma] === undefined ? '' : tt[tr.ma],
               tr.don_vi || '']);
  });

  var rt = lay_realtime(tt[dn.khoa]);
  if (rt) {
    (CAU_HINH.truong_realtime[rt.loai] || []).forEach(function (tr) {
      hang.push([tr.ten + ' (quan trắc)', rt[tr.ma] === undefined ? '' : rt[tr.ma],
                 tr.don_vi || '']);
    });
  }

  var ten_tep = 'doi_tuong_' + (tt[dn.khoa] || ma_lop) + '.csv';
  tai_ve_csv(ten_tep, ['Thuộc tính', 'Giá trị', 'Đơn vị'], hang);
}

/* --------------------------------------------------------------------------
   Ve bieu do chuoi thoi gian cho doi tuong dang chon
   -------------------------------------------------------------------------- */
function ve_bieu_do_realtime(ma) {
  if (bieu_do_hien_tai) { bieu_do_hien_tai.destroy(); bieu_do_hien_tai = null; }

  var rt = lay_realtime(ma);
  if (!rt || !rt.chuoi) return;

  var canvas = document.getElementById('canvas-bieu-do');
  if (!canvas || typeof Chart === 'undefined') return;

  var mau_chu = getComputedStyle(document.body)
    .getPropertyValue('--chu-mo').trim() || '#5c6b7a';
  var mau_vien = getComputedStyle(document.body)
    .getPropertyValue('--vien-nhat').trim() || '#e7ebef';

  bieu_do_hien_tai = new Chart(canvas, {
    type: rt.loai === 'mua' ? 'bar' : 'line',
    data: {
      labels: rt.chuoi.nhan,
      datasets: [{
        label: rt.nhan_chuoi + ' (' + rt.don_vi_chuoi + ')',
        data: rt.chuoi.gia_tri,
        borderColor: '#16a6c9',
        backgroundColor: 'rgba(22,166,201,.18)',
        borderWidth: 2,
        pointRadius: 0,
        tension: 0.3,
        fill: true,
      }],
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      plugins: {
        legend: { display: true, labels: { boxWidth: 10, font: { size: 10 }, color: mau_chu } },
        tooltip: { intersect: false, mode: 'index' },
      },
      scales: {
        x: { ticks: { font: { size: 9 }, color: mau_chu, maxTicksLimit: 7 },
             grid: { display: false } },
        y: { ticks: { font: { size: 9 }, color: mau_chu },
             grid: { color: mau_vien } },
      },
    },
  });
}

/* --------------------------------------------------------------------------
   Dong bang chi tiet
   -------------------------------------------------------------------------- */
function dong_chi_tiet() {
  if (bieu_do_hien_tai) { bieu_do_hien_tai.destroy(); bieu_do_hien_tai = null; }
  document.getElementById('huong-dan-click').hidden = false;
  document.getElementById('chon-doi-tuong').hidden = true;
  var hop = document.getElementById('chi-tiet-doi-tuong');
  hop.hidden = true;
  hop.innerHTML = '';
  KET_QUA_TRUNG = [];
  if (hinh_nhay_sang) { nhom_ve_phu.removeLayer(hinh_nhay_sang); hinh_nhay_sang = null; }
  bo_chon_hang_bang();
}
