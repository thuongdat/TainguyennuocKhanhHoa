/* ==========================================================================
   table.js - Bang thuoc tinh va cac chuc nang xuat du lieu
   ========================================================================== */

/* Trang thai cua bang */
var BANG = {
  ma_lop: null,     /* lop dang xem */
  cot_sap_xep: null,
  tang_dan: true,
  hang_dang_ve: [], /* danh sach doi tuong dang hien, theo dung thu tu da sap xep */
};

/* --------------------------------------------------------------------------
   Danh sach chon lop cho bang
   -------------------------------------------------------------------------- */
function dung_chon_lop_bang() {
  var o = document.getElementById('bang-chon-lop');
  o.innerHTML = '';

  Object.keys(CAU_HINH.lop).forEach(function (ma_lop) {
    var l = LOP[ma_lop];
    if (!l || l.loi) return;
    var opt = document.createElement('option');
    opt.value = ma_lop;
    opt.textContent = CAU_HINH.lop[ma_lop].ten;
    o.appendChild(opt);
  });

  o.addEventListener('change', function () {
    BANG.ma_lop = o.value;
    BANG.cot_sap_xep = null;
    ve_lai_bang();
  });

  /* Mo dau bang lop song suoi neu co */
  BANG.ma_lop = (LOP['song_suoi'] && !LOP['song_suoi'].loi) ? 'song_suoi' : o.value;
  o.value = BANG.ma_lop;
  ve_lai_bang();
}

/* --------------------------------------------------------------------------
   Ve lai toan bo bang
   -------------------------------------------------------------------------- */
function ve_lai_bang() {
  var bang = document.getElementById('bang-tt');
  var dau = bang.querySelector('thead');
  var than = bang.querySelector('tbody');
  dau.innerHTML = '';
  than.innerHTML = '';

  var l = LOP[BANG.ma_lop];
  if (!l || l.loi) {
    document.getElementById('bang-tom-tat').textContent = 'Không có dữ liệu.';
    return;
  }

  var dn = l.dn;
  var cac_cot = dn.cot_bang.map(function (ma_truong) {
    var tr = dn.truong.filter(function (t) { return t.ma === ma_truong; })[0];
    return tr || { ma: ma_truong, ten: ma_truong };
  });

  /* ----- Dong tieu de, nhap vao de sap xep ----- */
  var hang_dau = document.createElement('tr');
  cac_cot.forEach(function (cot) {
    var th = document.createElement('th');
    th.textContent = cot.ten + (cot.don_vi ? ' (' + cot.don_vi + ')' : '');
    if (BANG.cot_sap_xep === cot.ma) {
      var mui = document.createElement('span');
      mui.className = 'huong';
      mui.textContent = BANG.tang_dan ? ' ▲' : ' ▼';
      th.appendChild(mui);
    }
    th.addEventListener('click', function () { sap_xep_bang(cot.ma); });
    hang_dau.appendChild(th);
  });
  dau.appendChild(hang_dau);

  /* ----- Du lieu, co ap dung bo loc va sap xep ----- */
  var danh_sach = l.doi_tuong.filter(qua_bo_loc);

  if (BANG.cot_sap_xep) {
    var khoa = BANG.cot_sap_xep;
    var huong = BANG.tang_dan ? 1 : -1;
    danh_sach = danh_sach.slice().sort(function (a, b) {
      var va = a.thuoc_tinh[khoa], vb = b.thuoc_tinh[khoa];
      if (va === undefined || va === null) return 1;
      if (vb === undefined || vb === null) return -1;
      if (typeof va === 'number' && typeof vb === 'number') return (va - vb) * huong;
      return String(va).localeCompare(String(vb), 'vi') * huong;
    });
  }

  BANG.hang_dang_ve = danh_sach;

  danh_sach.forEach(function (dt) {
    var tr = document.createElement('tr');
    tr.dataset.chiSo = dt.chi_so;
    cac_cot.forEach(function (cot) {
      var td = document.createElement('td');
      var gt = dinh_dang_gia_tri(cot, dt.thuoc_tinh[cot.ma]);
      if (gt === null) {
        td.textContent = '--';
        td.className = 'o-trong';
      } else {
        /* Khong lap lai don vi trong tung o vi tieu de cot da co */
        td.textContent = (DINH_DANG[cot.dinh_dang || 'chu'] || DINH_DANG.chu)(
          dt.thuoc_tinh[cot.ma]) || '--';
      }
      tr.appendChild(td);
    });
    tr.addEventListener('click', function () {
      di_den_doi_tuong(BANG.ma_lop, dt.chi_so);
    });
    than.appendChild(tr);
  });

  /* ----- Dong tom tat ----- */
  var tom_tat = danh_sach.length.toLocaleString('vi-VN') + ' đối tượng';
  if (danh_sach.length !== l.doi_tuong.length) {
    tom_tat += ' (đã lọc từ ' + l.doi_tuong.length.toLocaleString('vi-VN') + ')';
  }
  document.getElementById('bang-tom-tat').textContent = tom_tat;
}

function sap_xep_bang(ma_cot) {
  if (BANG.cot_sap_xep === ma_cot) BANG.tang_dan = !BANG.tang_dan;
  else { BANG.cot_sap_xep = ma_cot; BANG.tang_dan = true; }
  ve_lai_bang();
}

/* --------------------------------------------------------------------------
   Dong bo lua chon giua ban do va bang
   -------------------------------------------------------------------------- */
function chon_hang_bang(ma_lop, chi_so) {
  /* Neu dang xem lop khac thi chuyen bang sang lop cua doi tuong */
  if (BANG.ma_lop !== ma_lop) {
    BANG.ma_lop = ma_lop;
    document.getElementById('bang-chon-lop').value = ma_lop;
    ve_lai_bang();
  }

  bo_chon_hang_bang();
  var hang = document.querySelector('#bang-tt tbody tr[data-chi-so="' + chi_so + '"]');
  if (!hang) return;
  hang.classList.add('dang-chon');

  /* Chi cuon den hang khi bang dang mo */
  if (document.getElementById('khu-bang').classList.contains('mo')) {
    hang.scrollIntoView({ block: 'nearest', behavior: 'smooth' });
  }
}

function bo_chon_hang_bang() {
  var cac_hang = document.querySelectorAll('#bang-tt tbody tr.dang-chon');
  for (var i = 0; i < cac_hang.length; i++) {
    cac_hang[i].classList.remove('dang-chon');
  }
}

/* --------------------------------------------------------------------------
   Xuat du lieu
   -------------------------------------------------------------------------- */

/* Xuat bang dang xem ra CSV, theo dung bo loc va thu tu sap xep hien tai */
function xuat_bang_csv() {
  var l = LOP[BANG.ma_lop];
  if (!l || l.loi) return;
  var dn = l.dn;

  /* Xuat day du moi truong da khai bao, khong chi cac cot dang hien */
  var cot = dn.truong.map(function (tr) {
    return tr.ten + (tr.don_vi ? ' (' + tr.don_vi + ')' : '');
  });
  cot.unshift('Mã');
  cot.push('Kinh độ');
  cot.push('Vĩ độ');

  var hang = BANG.hang_dang_ve.map(function (dt) {
    var d = [dt.thuoc_tinh[dn.khoa] || ''];
    dn.truong.forEach(function (tr) {
      var v = dt.thuoc_tinh[tr.ma];
      d.push(v === undefined || v === null ? '' : v);
    });
    var tam = tam_hinh_hoc(dt.hinh_hoc);
    d.push(tam ? tam.lng.toFixed(6) : '');
    d.push(tam ? tam.lat.toFixed(6) : '');
    return d;
  });

  tai_ve_csv(BANG.ma_lop + '.csv', cot, hang);
}

/* Xuat bang dang xem ra GeoJSON, giu nguyen hinh hoc */
function xuat_bang_geojson() {
  var l = LOP[BANG.ma_lop];
  if (!l || l.loi) return;

  var gj = {
    type: 'FeatureCollection',
    name: BANG.ma_lop,
    crs: { type: 'name', properties: { name: 'urn:ogc:def:crs:OGC:1.3:CRS84' } },
    metadata: {
      xuat_tu: CAU_HINH.he_thong.ten,
      thoi_diem_xuat: new Date().toISOString(),
      so_doi_tuong: BANG.hang_dang_ve.length,
    },
    features: BANG.hang_dang_ve.map(function (dt) {
      return { type: 'Feature', geometry: dt.hinh_hoc, properties: dt.thuoc_tinh };
    }),
  };

  tai_ve_tep(BANG.ma_lop + '.geojson',
             JSON.stringify(gj, null, 1),
             'application/geo+json');
}

/* Cac ham tai_ve_csv(), boc_o_csv() va tai_ve_tep() nam trong
   assets/js/xuat_tep.js vi trang thong ke cung dung chung. */
