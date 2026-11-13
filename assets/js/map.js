/* ==========================================================================
   map.js - Khoi tao ban do, ban do nen va cac cong cu tren ban do
   ========================================================================== */

/* Bien toan cuc dung chung cho cac tep khac */
var ban_do = null;              /* doi tuong Leaflet Map */
var lop_nen_dang_dung = null;   /* lop tile dang hien */
var ma_nen_dang_dung = null;    /* ma nen dang chon, ke ca nen vector */
var nhom_ve_phu = null;         /* nhom chua hinh ve tam: do khoang cach, vong chon */
var cong_cu_dang_bat = null;    /* 'do_khoang_cach' | 'chon_ban_kinh' | 'toa_do' | null */

/* --------------------------------------------------------------------------
   Khoi tao ban do
   -------------------------------------------------------------------------- */
function khoi_tao_ban_do() {
  ban_do = L.map('ban-do', {
    center: TINH.ban_do.tam,
    zoom: TINH.ban_do.zoom,
    minZoom: CAU_HINH.ban_do_chung.zoom_min,
    maxZoom: CAU_HINH.ban_do_chung.zoom_max,
    zoomControl: false,
    /* Cho phep zoom theo buoc 1/4 muc. Tinh Khanh Hoa keo dai theo chieu bac
       nam, trong khi khung ban do lai rong va thap, nen neu chi dung muc zoom
       nguyen thi fitBounds phai lui ra mot muc va de lai nhieu khoang trong. */
    zoomSnap: 0.25,
    zoomDelta: 0.5,
    /* Ve bang canvas thay vi SVG. Khanh Hoa co 65 xa thi SVG con chiu duoc,
       nhung Gia Lai co 135 xa voi hinh hoc chi tiet hon thi trinh duyet dung
       hinh vai giay moi lan ve lai. Canvas khong tao phan tu DOM cho tung doi
       tuong nen nhanh hon han. Doi duoc vi he thong khong dua vao su kien click
       cua SVG: identify.js tu kiem tra hinh hoc, xem ghi chu trong tep do. */
    preferCanvas: true,
  });

  L.control.zoom({ position: 'topleft' }).addTo(ban_do);
  L.control.scale({ position: 'bottomleft', imperial: false, metric: true }).addTo(ban_do);

  tao_cac_pane();
  nhom_ve_phu = L.layerGroup().addTo(ban_do);

  dat_lop_nen(lay_nen_mac_dinh().ma);
  dung_danh_sach_nen();
  theo_doi_con_tro();

  /* Nhap vao vung trong tren ban do thi dong bang thong tin */
  ban_do.on('click', function (e) {
    if (cong_cu_dang_bat) return;    /* dang dung cong cu khac */
    truy_van_tai_diem(e.latlng);
  });

  return ban_do;
}

/* Tao pane rieng cho tung lop de kiem soat thu tu ve */
function tao_cac_pane() {
  Object.keys(CAU_HINH.lop).forEach(function (ma_lop) {
    var dn = CAU_HINH.lop[ma_lop];
    var pane = ban_do.createPane('pane-' + ma_lop);
    pane.style.zIndex = dn.z;
  });
  /* Pane rieng cho nhan ten doi tuong, nam tren tat ca */
  var pane_nhan = ban_do.createPane('pane-nhan');
  pane_nhan.style.zIndex = 620;
  pane_nhan.style.pointerEvents = 'none';
}

/* --------------------------------------------------------------------------
   Ban do nen
   -------------------------------------------------------------------------- */
function lay_nen_mac_dinh() {
  for (var i = 0; i < CAU_HINH.ban_do_nen.length; i++) {
    if (CAU_HINH.ban_do_nen[i].mac_dinh) return CAU_HINH.ban_do_nen[i];
  }
  return CAU_HINH.ban_do_nen[0];
}

function dat_lop_nen(ma_nen) {
  var dn = CAU_HINH.ban_do_nen.filter(function (n) { return n.ma === ma_nen; })[0];
  if (!dn) return;

  if (lop_nen_dang_dung) ban_do.removeLayer(lop_nen_dang_dung);
  lop_nen_dang_dung = null;
  tat_nen_vector();
  danh_dau_the_nen(ma_nen);
  ma_nen_dang_dung = ma_nen;

  /* Nen dung tu du lieu dia phuong, khong phai tile */
  if (dn.kieu === 'vector') {
    bat_nen_vector(dn);
    return;
  }

  lop_nen_dang_dung = L.tileLayer(dn.url, {
    attribution: dn.ghi_nguon,
    /* maxNativeZoom la muc zoom cao nhat ma dich vu co tile that.
       Vuot qua muc do, Leaflet phong to tile san co thay vi de trong,
       nho vay nguoi dung van zoom duoc den muc zoom_max cua ban do. */
    maxNativeZoom: dn.zoom_max || 19,
    maxZoom: CAU_HINH.ban_do_chung.zoom_max,
    subdomains: dn.url.indexOf('{s}') >= 0 ? 'abc' : [],
  }).addTo(ban_do);

  /* Dua lop nen xuong duoi cung */
  lop_nen_dang_dung.setZIndex(1);
}

function danh_dau_the_nen(ma_nen) {
  var cac_the = document.querySelectorAll('#danh-sach-nen .the-nen');
  for (var i = 0; i < cac_the.length; i++) {
    cac_the[i].classList.toggle('dang-chon', cac_the[i].dataset.nen === ma_nen);
  }
}

/* --------------------------------------------------------------------------
   Nen ban do dung tu du lieu dia phuong
   Cac tep GeoJSON chi duoc tai ve o lan dau nguoi dung chon nen nay, sau do
   giu lai trong bo nho de lan sau bat lai la hien ngay.
   -------------------------------------------------------------------------- */
var NEN_VECTOR = {};          /* ma lop -> nhom Leaflet da dung xong */
var dang_tai_nen_vector = false;

function bat_nen_vector(dn) {
  document.getElementById('ban-do').classList.add('nen-dia-phuong');

  /* Da tai truoc do thi chi can bat lai */
  if (Object.keys(NEN_VECTOR).length > 0) {
    Object.keys(NEN_VECTOR).forEach(function (ma) {
      NEN_VECTOR[ma].addTo(ban_do);
    });
    cap_nhat_nen_theo_zoom();
    ghi_nguon_nen(dn.ghi_nguon);
    return;
  }

  if (dang_tai_nen_vector) return;
  dang_tai_nen_vector = true;
  hien_mach_bao('Đang tải nền địa phương lần đầu, khoảng 3,5 MB...', 6000);

  var cac_viec = CAU_HINH.nen_vector.lop.map(function (lop) {
    return fetch(duong_dan_du_lieu(lop.tep))
      .then(function (r) {
        if (!r.ok) throw new Error('HTTP ' + r.status);
        return r.json();
      })
      .then(function (gj) { ve_lop_nen_vector(lop, gj); })
      .catch(function (e) {
        console.warn('Không nạp được lớp nền ' + lop.ma + ': ' + e.message);
      });
  });

  Promise.all(cac_viec).then(function () {
    dang_tai_nen_vector = false;
    cap_nhat_nen_theo_zoom();
    ghi_nguon_nen(dn.ghi_nguon);
    hien_mach_bao('Đã tải xong nền địa phương.', 2500);
  });
}

function ve_lop_nen_vector(lop, gj) {
  /* Moi lop nen mot pane rieng, z nho hon 400 de luon nam duoi lop chuyen de */
  var ten_pane = 'pane-nen-' + lop.ma;
  if (!ban_do.getPane(ten_pane)) {
    var pane = ban_do.createPane(ten_pane);
    pane.style.zIndex = lop.z;
    if (lop.nhan) pane.style.pointerEvents = 'none';
  }

  var tuy_chon = {
    pane: ten_pane,
    interactive: false,
    style: (typeof lop.kieu_ve === 'function')
      ? function (f) { return lop.kieu_ve(f.properties); }
      : lop.kieu_ve,
  };

  /* Lop diem kem nhan chu */
  if (lop.nhan) {
    tuy_chon.pointToLayer = function (f, latlng) {
      var m = L.circleMarker(latlng, Object.assign({ pane: ten_pane }, lop.kieu_ve));
      var chu = (f.properties[lop.nhan] || '').trim();
      if (chu) {
        m.bindTooltip(chu, {
          permanent: true, direction: 'right', offset: [4, 0],
          className: 'nhan-nen', pane: ten_pane, opacity: 1,
        });
      }
      return m;
    };
  }

  NEN_VECTOR[lop.ma] = L.geoJSON(gj, tuy_chon).addTo(ban_do);
}

function tat_nen_vector() {
  document.getElementById('ban-do').classList.remove('nen-dia-phuong');
  Object.keys(NEN_VECTOR).forEach(function (ma) {
    ban_do.removeLayer(NEN_VECTOR[ma]);
  });
}

/* An cac lop nen chi co y nghia o muc zoom gan, vi du nhan dia danh */
function cap_nhat_nen_theo_zoom() {
  if (Object.keys(NEN_VECTOR).length === 0) return;
  var z = ban_do.getZoom();
  CAU_HINH.nen_vector.lop.forEach(function (lop) {
    var pane = ban_do.getPane('pane-nen-' + lop.ma);
    if (!pane) return;
    pane.style.display = (lop.zoom_min && z < lop.zoom_min) ? 'none' : '';
  });
}

function ghi_nguon_nen(chu) {
  if (!ban_do.attributionControl) return;
  ban_do.attributionControl.setPrefix(
    '<a href="https://leafletjs.com">Leaflet</a>');
  ban_do.attributionControl.addAttribution(chu);
}

function dung_danh_sach_nen() {
  var hop = document.getElementById('danh-sach-nen');
  hop.innerHTML = '';
  CAU_HINH.ban_do_nen.forEach(function (n) {
    var nut = document.createElement('button');
    nut.className = 'the-nen' + (n.mac_dinh ? ' dang-chon' : '');
    nut.dataset.nen = n.ma;
    nut.textContent = n.ten;
    nut.addEventListener('click', function () { dat_lop_nen(n.ma); });
    hop.appendChild(nut);
  });
}

/* --------------------------------------------------------------------------
   Hien toa do va ty le theo con tro
   -------------------------------------------------------------------------- */
function theo_doi_con_tro() {
  var o_toa_do = document.getElementById('toa-do-chuot');
  var o_ty_le = document.getElementById('ty-le-ban-do');

  ban_do.on('mousemove', function (e) {
    o_toa_do.textContent = e.latlng.lat.toFixed(5) + '° B, '
                         + e.latlng.lng.toFixed(5) + '° Đ';
  });

  function cap_nhat_ty_le() {
    o_ty_le.textContent = '1 : ' + Math.round(ty_le_hien_tai()).toLocaleString('vi-VN');
  }

  ban_do.on('zoomend', cap_nhat_ty_le);
  cap_nhat_ty_le();
}

/* Ty le ban do xap xi tai tam man hinh */
function ty_le_hien_tai() {
  var lat = ban_do.getCenter().lat;
  var met_tren_pixel = 156543.03392 * Math.cos(lat * Math.PI / 180)
                     / Math.pow(2, ban_do.getZoom());
  /* Gia dinh man hinh 96 dpi -> 1 pixel = 0,0254/96 met */
  return met_tren_pixel / (0.0254 / 96);
}

/* --------------------------------------------------------------------------
   Cong cu: ve toan tinh
   -------------------------------------------------------------------------- */
function ve_toan_tinh() {
  ban_do.fitBounds(TINH.ban_do.pham_vi_dat_lien, { padding: [20, 20] });
}

/* --------------------------------------------------------------------------
   Cong cu: do khoang cach
   -------------------------------------------------------------------------- */
var diem_do = [];
var duong_do = null;

function bat_tat_cong_cu(ten_cong_cu, id_nut) {
  /* Tat cong cu dang bat (neu co) */
  if (cong_cu_dang_bat) {
    document.getElementById(cong_cu_dang_bat.id_nut).classList.remove('dang-bat');
    huy_cong_cu();
  }

  if (cong_cu_dang_bat && cong_cu_dang_bat.ten === ten_cong_cu) {
    cong_cu_dang_bat = null;
    return;
  }

  cong_cu_dang_bat = { ten: ten_cong_cu, id_nut: id_nut };
  document.getElementById(id_nut).classList.add('dang-bat');
  ban_do.getContainer().style.cursor = 'crosshair';

  if (ten_cong_cu === 'do_khoang_cach') bat_dau_do_khoang_cach();
  if (ten_cong_cu === 'chon_ban_kinh') bat_dau_chon_ban_kinh();
  if (ten_cong_cu === 'toa_do') bat_dau_xem_toa_do();
}

function huy_cong_cu() {
  ban_do.off('click', xu_ly_click_do);
  ban_do.off('mousemove', xu_ly_move_do);
  ban_do.off('click', xu_ly_click_ban_kinh);
  ban_do.off('mousemove', xu_ly_move_ban_kinh);
  ban_do.off('click', xu_ly_click_toa_do);
  nhom_ve_phu.clearLayers();
  diem_do = [];
  duong_do = null;
  tam_vong = null;
  vong_chon = null;
  ban_do.getContainer().style.cursor = '';
  cong_cu_dang_bat = null;
}

function bat_dau_do_khoang_cach() {
  diem_do = [];
  nhom_ve_phu.clearLayers();
  ban_do.on('click', xu_ly_click_do);
  ban_do.on('mousemove', xu_ly_move_do);
  hien_mach_bao('Nhấp lần lượt các điểm để đo. Nhấp đúp để kết thúc.');
}

function xu_ly_click_do(e) {
  diem_do.push(e.latlng);
  L.circleMarker(e.latlng, {
    radius: 4, color: '#dc2626', fillColor: '#fff', weight: 2, fillOpacity: 1,
  }).addTo(nhom_ve_phu);
  ve_duong_do(diem_do);
}

function xu_ly_move_do(e) {
  if (diem_do.length === 0) return;
  ve_duong_do(diem_do.concat([e.latlng]));
}

function ve_duong_do(cac_diem) {
  if (duong_do) nhom_ve_phu.removeLayer(duong_do);
  duong_do = L.polyline(cac_diem, {
    color: '#dc2626', weight: 2.5, dashArray: '6 4',
  }).addTo(nhom_ve_phu);

  var tong = 0;
  for (var i = 0; i < cac_diem.length - 1; i++) {
    tong += cac_diem[i].distanceTo(cac_diem[i + 1]);
  }
  duong_do.bindTooltip(dinh_dang_khoang_cach(tong), {
    permanent: true, direction: 'center', className: 'nhan-ban-do',
  }).openTooltip(cac_diem[cac_diem.length - 1]);
}

function dinh_dang_khoang_cach(met) {
  if (met < 1000) return Math.round(met).toLocaleString('vi-VN') + ' m';
  return (met / 1000).toLocaleString('vi-VN', { maximumFractionDigits: 2 }) + ' km';
}

/* --------------------------------------------------------------------------
   Cong cu: chon doi tuong theo ban kinh
   Rat huu dung khi tham dinh cap phep: tim moi diem xa thai quanh mot
   cong trinh khai thac.
   -------------------------------------------------------------------------- */
var tam_vong = null;
var vong_chon = null;

function bat_dau_chon_ban_kinh() {
  tam_vong = null;
  nhom_ve_phu.clearLayers();
  ban_do.on('click', xu_ly_click_ban_kinh);
  ban_do.on('mousemove', xu_ly_move_ban_kinh);
  hien_mach_bao('Nhấp để đặt tâm, nhấp lần hai để chốt bán kính.');
}

function xu_ly_click_ban_kinh(e) {
  if (!tam_vong) {
    tam_vong = e.latlng;
    L.circleMarker(e.latlng, {
      radius: 4, color: '#0b5e72', fillColor: '#fff', weight: 2, fillOpacity: 1,
    }).addTo(nhom_ve_phu);
    return;
  }
  /* Nhap lan hai: chot ban kinh va liet ke doi tuong ben trong */
  var ban_kinh = tam_vong.distanceTo(e.latlng);
  liet_ke_trong_vong(tam_vong, ban_kinh);
  ban_do.off('click', xu_ly_click_ban_kinh);
  ban_do.off('mousemove', xu_ly_move_ban_kinh);
  ban_do.getContainer().style.cursor = '';
  if (cong_cu_dang_bat) {
    document.getElementById(cong_cu_dang_bat.id_nut).classList.remove('dang-bat');
    cong_cu_dang_bat = null;
  }
}

function xu_ly_move_ban_kinh(e) {
  if (!tam_vong) return;
  if (vong_chon) nhom_ve_phu.removeLayer(vong_chon);
  var r = tam_vong.distanceTo(e.latlng);
  vong_chon = L.circle(tam_vong, {
    radius: r, color: '#0b5e72', weight: 2, dashArray: '6 4',
    fillColor: '#16a6c9', fillOpacity: 0.1,
  }).addTo(nhom_ve_phu);
  vong_chon.bindTooltip('Bán kính ' + dinh_dang_khoang_cach(r), {
    permanent: true, direction: 'top', className: 'nhan-ban-do',
  }).openTooltip();
}

/* --------------------------------------------------------------------------
   Cong cu: xem toa do mot diem
   -------------------------------------------------------------------------- */
function bat_dau_xem_toa_do() {
  ban_do.on('click', xu_ly_click_toa_do);
  hien_mach_bao('Nhấp vào bản đồ để xem toạ độ điểm đó.');
}

function xu_ly_click_toa_do(e) {
  var vn2000 = ' (VN-2000 cần chuyển bằng pyproj ở bước xử lý dữ liệu)';
  L.popup({ className: 'popup-toa-do' })
    .setLatLng(e.latlng)
    .setContent(
      '<div style="font-size:12.5px;line-height:1.6">'
      + '<strong>Toạ độ WGS84</strong><br>'
      + 'Vĩ độ: ' + e.latlng.lat.toFixed(6) + '° B<br>'
      + 'Kinh độ: ' + e.latlng.lng.toFixed(6) + '° Đ'
      + '</div>')
    .openOn(ban_do);
}

/* --------------------------------------------------------------------------
   Thong bao ngan tren ban do
   -------------------------------------------------------------------------- */
var o_mach_bao = null;

function hien_mach_bao(noi_dung, thoi_gian_ms) {
  if (!o_mach_bao) {
    o_mach_bao = document.createElement('div');
    o_mach_bao.style.cssText =
      'position:absolute;top:12px;left:50%;transform:translateX(-50%);'
      + 'padding:7px 14px;border-radius:16px;background:rgba(11,94,114,.94);'
      + 'color:#fff;font-size:12.5px;z-index:850;box-shadow:0 2px 10px rgba(0,0,0,.25);'
      + 'pointer-events:none;max-width:84%;text-align:center';
    document.querySelector('.khu-ban-do').appendChild(o_mach_bao);
  }
  o_mach_bao.textContent = noi_dung;
  o_mach_bao.style.display = 'block';
  clearTimeout(o_mach_bao._hen);
  o_mach_bao._hen = setTimeout(function () {
    o_mach_bao.style.display = 'none';
  }, thoi_gian_ms || 4000);
}
