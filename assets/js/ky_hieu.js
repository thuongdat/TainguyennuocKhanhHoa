/* ==========================================================================
   ky_hieu.js - Ky hieu diem cho ban do
   --------------------------------------------------------------------------
   Nap sau config.js va tinh.js, truoc map.js va layers.js.

   Hai nguon ky hieu, khai bao trong CAU_HINH.lop[ma].ky_hieu:

   1. { tep: 'Lokhoan_TK' }
      Dung tep SVG trong assets/ky_hieu/, sinh tu tep .qml cua QGIS bang
      scripts/06_tao_ky_hieu.py. Giu nguyen net ve va mau cua ky hieu goc,
      nen dung cho nhung doi tuong da co ky hieu chuan nganh.

   2. { hinh: 'tam_giac' }
      Ve mot hinh don gian, MAU LAY TU kieu_ve() cua chinh lop do. Dung khi
      hinh dang phai co dinh theo quy uoc nhung mau van phai noi len duoc
      thuoc tinh: vi du cong trinh xa thai luon la tam giac, con mau thi dam
      nhat theo luu luong xa.

   Khong khai bao ky_hieu thi lop van ve bang L.circleMarker nhu truoc.

   Luu y ve truy van bang nhap chuot: identify.js van doc radius tu kieu_ve(),
   khong doc kich thuoc ky hieu. Vi vay kieu_ve() phai tra ve radius sat voi
   co that cua ky hieu, neu khong vung bam se lech voi hinh nhin thay.
   ========================================================================== */

/* Danh muc doc tu assets/ky_hieu/ky_hieu.json, nap mot lan luc khoi dong */
var DANH_MUC_KY_HIEU = null;

/* Mot milimet cua QGIS doi ra bao nhieu pixel tren ban do. QGIS ve cho ban do
   in kho A3, con day la man hinh: lay nguyen so milimet thi ky hieu to qua va
   che mat nhau. He so nay chon bang mat tren man hinh. */
var PX_MOI_MM = 3.2;


/* --------------------------------------------------------------------------
   Nap danh muc ky hieu
   --------------------------------------------------------------------------
   Khong nap duoc thi tra ve danh muc rong chu khong nem loi: ban do van phai
   ve duoc bang ky hieu vong tron mac dinh.
   -------------------------------------------------------------------------- */
function nap_danh_muc_ky_hieu() {
  /* Them ?tinh=<ma> de tach khoa cache giua cac du an cung chay tren
     http://localhost:8000, cung ly do nhu duong_dan_du_lieu() trong
     tinh.js. Danh muc ky hieu moi tinh mot khac. */
  var ma_tinh = (typeof TINH !== 'undefined' && TINH && TINH.ma)
    ? TINH.ma : 'chua-biet';
  return fetch(GOC_TRANG + 'assets/ky_hieu/ky_hieu.json?tinh='
               + encodeURIComponent(ma_tinh))
    .then(function (r) {
      if (!r.ok) throw new Error('HTTP ' + r.status);
      return r.json();
    })
    .then(function (dl) {
      DANH_MUC_KY_HIEU = dl.ky_hieu || {};
      return DANH_MUC_KY_HIEU;
    })
    .catch(function (e) {
      console.warn('Không nạp được danh mục ký hiệu: ' + e.message);
      DANH_MUC_KY_HIEU = {};
      return DANH_MUC_KY_HIEU;
    });
}


/* --------------------------------------------------------------------------
   Khai bao ky hieu cua mot lop, co the phu thuoc thuoc tinh
   --------------------------------------------------------------------------
   ky_hieu co the la mot doi tuong, hoac mot ham nhan (thuoc_tinh, realtime)
   de moi loai doi tuong mot ky hieu khac nhau.
   -------------------------------------------------------------------------- */
function khai_bao_ky_hieu(dn, thuoc_tinh, rt) {
  if (!dn || !dn.ky_hieu) return null;
  if (typeof dn.ky_hieu === 'function') return dn.ky_hieu(thuoc_tinh, rt);
  return dn.ky_hieu;
}


/* --------------------------------------------------------------------------
   Ky hieu dung tep SVG sinh tu QGIS
   -------------------------------------------------------------------------- */
function bieu_tuong_tu_tep(ten_tep, co_px) {
  if (!DANH_MUC_KY_HIEU) return null;
  var o = DANH_MUC_KY_HIEU[ten_tep];
  if (!o) {
    console.warn('Không có ký hiệu "' + ten_tep + '" trong danh mục.');
    return null;
  }

  var px = co_px || Math.round(o.kich_thuoc_mm * PX_MOI_MM);
  /* ?tinh=<ma> chi de tach khoa cache giua cac du an cung chay tren
     http://localhost:8000, xem duong_dan_du_lieu() trong tinh.js */
  var ma_tinh = (typeof TINH !== 'undefined' && TINH && TINH.ma)
    ? TINH.ma : 'chua-biet';
  return L.icon({
    iconUrl: GOC_TRANG + 'assets/' + o.tep
             + '?tinh=' + encodeURIComponent(ma_tinh),
    iconSize: [px, px],
    iconAnchor: [px / 2, px / 2],
    /* Goc toa do cua tep SVG nam o giua, nen chu giai cung neo o giua */
    popupAnchor: [0, -px / 2],
  });
}


/* --------------------------------------------------------------------------
   Ky hieu ve bang hinh don gian, mau lay tu kieu_ve()
   -------------------------------------------------------------------------- */
function duong_hinh(ten_hinh, nua) {
  var n = nua;
  switch (ten_hinh) {
    case 'tam_giac':
      /* Tam giac deu, dinh huong len */
      return '<polygon points="0,' + (-n) + ' ' + (n * 0.866) + ',' + (n * 0.5)
           + ' ' + (-n * 0.866) + ',' + (n * 0.5) + '"';
    case 'vuong':
      return '<rect x="' + (-n) + '" y="' + (-n) + '" width="' + (n * 2)
           + '" height="' + (n * 2) + '"';
    case 'thoi':
      return '<polygon points="0,' + (-n) + ' ' + n + ',0 0,' + n + ' '
           + (-n) + ',0"';
    case 'tron':
    default:
      return '<circle cx="0" cy="0" r="' + n + '"';
  }
}


/* Can lai trong luong thi giac giua cac hinh.
   kieu_ve() cua cac lop tra ve radius von tinh cho hinh tron. Mot hinh vuong
   canh 2r phu dien tich 4r2, lon hon hinh tron cung ban kinh khoang 27 phan
   tram, nen nhin nang hon han. Tam giac thi nguoc lai, nho hon. Cac he so duoi
   day keo chung ve cung muc dam nhat voi hinh tron cu. */
var HE_SO_HINH = {
  tron: 1.0,
  vuong: 0.7,
  thoi: 1.12,
  tam_giac: 1.18,
};


/* --------------------------------------------------------------------------
   Lop ve hinh don gian TRUC TIEP len canvas
   --------------------------------------------------------------------------
   Vi sao khong dung L.divIcon cho nhung hinh nay: ban do bat preferCanvas nen
   moi vector deu ve len canvas, chi ton mot the DOM cho ca lop. Rieng hai lop
   khai thac va xa thai da la 809 doi tuong; neu moi doi tuong mot the DOM thi
   keo ban do giat han, dung noi lo ma CLAUDE.md da ghi ve 666 nhan ten.

   L.CircleMarker lo san diem noi: bo ve canvas goi layer._updatePath(). Ke
   thua lai va ve da giac thay cho hinh tron la giu duoc toan bo phan con lai
   cua Leaflet: bat su kien, doi kieu ve, thu gom theo pane.
   -------------------------------------------------------------------------- */
var KyHieuHinh = L.CircleMarker.extend({

  options: { hinh: 'tron' },

  _updatePath: function () {
    var r = this._renderer;

    /* Bo ve SVG thi khong co _ctx. Khi do ve hinh tron nhu cu, van dung hon
       la khong ve gi. */
    if (!r || !r._ctx) {
      L.CircleMarker.prototype._updatePath.call(this);
      return;
    }

    var ctx = r._ctx;
    var p = this._point;
    var o = this.options;
    var n = this._radius * (HE_SO_HINH[o.hinh] || 1.0);

    ctx.beginPath();
    if (o.hinh === 'vuong') {
      ctx.rect(p.x - n, p.y - n, n * 2, n * 2);
    } else if (o.hinh === 'tam_giac') {
      ctx.moveTo(p.x, p.y - n);
      ctx.lineTo(p.x + n * 0.866, p.y + n * 0.5);
      ctx.lineTo(p.x - n * 0.866, p.y + n * 0.5);
      ctx.closePath();
    } else if (o.hinh === 'thoi') {
      ctx.moveTo(p.x, p.y - n);
      ctx.lineTo(p.x + n, p.y);
      ctx.lineTo(p.x, p.y + n);
      ctx.lineTo(p.x - n, p.y);
      ctx.closePath();
    } else {
      ctx.arc(p.x, p.y, n, 0, Math.PI * 2);
    }

    /* Dung dung ham to mau cua Leaflet de ton trong moi tuy chon kieu ve */
    r._fillStroke(ctx, this);
  },

});


function bieu_tuong_hinh(ten_hinh, kieu) {
  /* kieu la ket qua cua kieu_ve(): radius, fillColor, color, weight... */
  var bk = kieu.radius || 6;
  var day = kieu.weight === undefined ? 1.5 : kieu.weight;
  var dem = Math.ceil(day) + 2;          /* chua het net vien */
  var nua = bk * (HE_SO_HINH[ten_hinh] || 1.0);
  var canh = (nua + dem) * 2;

  var svg = '<svg xmlns="http://www.w3.org/2000/svg" viewBox="'
          + (-canh / 2) + ' ' + (-canh / 2) + ' ' + canh + ' ' + canh
          + '" width="' + canh + '" height="' + canh + '">'
          + duong_hinh(ten_hinh, nua)
          + ' fill="' + (kieu.fillColor || '#666') + '"'
          + ' fill-opacity="' + (kieu.fillOpacity === undefined
                                  ? 0.9 : kieu.fillOpacity) + '"'
          + ' stroke="' + (kieu.color || '#fff') + '"'
          + ' stroke-width="' + day + '"'
          + ' stroke-linejoin="round"/></svg>';

  return L.divIcon({
    html: svg,
    className: 'ky-hieu-hinh',
    iconSize: [canh, canh],
    iconAnchor: [canh / 2, canh / 2],
    popupAnchor: [0, -canh / 2],
  });
}


/* --------------------------------------------------------------------------
   Diem vao duy nhat cua mo-dun
   --------------------------------------------------------------------------
   Tra ve mot L.Marker neu lop co khai bao ky hieu, nguoc lai tra ve null de
   nguoi goi dung L.circleMarker nhu truoc.
   -------------------------------------------------------------------------- */
function tao_diem_co_ky_hieu(toa_do, dn, thuoc_tinh, rt, tuy_chon) {
  var kb = khai_bao_ky_hieu(dn, thuoc_tinh, rt);
  if (!kb) return null;

  /* Hinh don gian: ve len canvas cho nhe, xem lop KyHieuHinh o tren */
  if (kb.hinh) {
    var kieu = dn.kieu_ve ? dn.kieu_ve(thuoc_tinh, rt) : {};
    var tc_hinh = {};
    Object.keys(kieu).forEach(function (k) { tc_hinh[k] = kieu[k]; });
    if (tuy_chon) {
      Object.keys(tuy_chon).forEach(function (k) { tc_hinh[k] = tuy_chon[k]; });
    }
    tc_hinh.hinh = kb.hinh;
    return new KyHieuHinh(toa_do, tc_hinh);
  }

  /* Tep SVG sinh tu QGIS: phai dung the DOM vi canvas khong ve duoc SVG.
     Chi dung cho lop it doi tuong, vi du mang quan trac. */
  if (kb.tep) {
    var bieu_tuong = bieu_tuong_tu_tep(kb.tep, kb.co_px);
    if (!bieu_tuong) return null;

    var tc = {};
    if (tuy_chon) {
      Object.keys(tuy_chon).forEach(function (k) { tc[k] = tuy_chon[k]; });
    }
    tc.icon = bieu_tuong;
    tc.interactive = true;
    return L.marker(toa_do, tc);
  }

  return null;
}


/* Ky hieu dung cho chu giai, tra ve chuoi HTML */
function chu_giai_ky_hieu(kb, kieu, co_px) {
  if (!kb) return '';
  var px = co_px || 16;

  if (kb.tep && DANH_MUC_KY_HIEU && DANH_MUC_KY_HIEU[kb.tep]) {
    return '<img class="cg-ky-hieu" src="' + GOC_TRANG + 'assets/'
         + DANH_MUC_KY_HIEU[kb.tep].tep + '" width="' + px
         + '" height="' + px + '" alt="">';
  }

  if (kb.hinh) {
    var nua = px / 2 - 2;
    return '<svg class="cg-ky-hieu" width="' + px + '" height="' + px
         + '" viewBox="' + (-px / 2) + ' ' + (-px / 2) + ' ' + px + ' ' + px
         + '">' + duong_hinh(kb.hinh, nua)
         + ' fill="' + ((kieu && kieu.fillColor) || '#666') + '"'
         + ' stroke="' + ((kieu && kieu.color) || '#fff')
         + '" stroke-width="1.4" stroke-linejoin="round"/></svg>';
  }

  return '';
}
