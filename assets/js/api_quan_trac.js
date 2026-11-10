/* ==========================================================================
   api_quan_trac.js - May khach goi backend trung gian QTQG
   --------------------------------------------------------------------------
   Nap sau config.js va tinh.js, truoc quan_trac.js.

   Dia chi dich vu lay tu dia_chi_backend() trong tinh.js, khong viet cung o
   day: no uu tien CAU_HINH.api.goc, khong co thi suy tu TINH.cong.backend.

   Nguyen tac xu ly loi, giong nap_realtime() trong realtime.js: khong ham nao
   nem loi ra ngoai. Moi ham tra ve null khi that bai va ghi ly do vao
   API_QT.loi, de trang goi co the hien thong bao tu te thay vi vo man trang.

   Viet theo ES5: var, function, khong module. Trang chay truc tiep khong qua
   buoc bien dich.
   ========================================================================== */

var API_QT = {
  tram: null,       /* FeatureCollection cac tram */
  so_do: null,      /* goi so do, cung schema data/realtime.json */
  suc_khoe: null,   /* ket qua goi /api/suc-khoe */
  loi: null,        /* chuoi loi gan nhat, null neu khong co */
};


/* --------------------------------------------------------------------------
   Goi mot duong dan cua API, co gioi han thoi gian cho
   --------------------------------------------------------------------------
   AbortController khong co trong IE nhung co trong moi trinh duyet hien nay.
   Thieu no thi chi mat phan huy yeu cau khi het gio, phan con lai van chay.
   -------------------------------------------------------------------------- */
function _goi_api(duong_dan) {
  var goc = dia_chi_backend();
  var het_gio = (CAU_HINH.api && CAU_HINH.api.het_gio_ms) || 15000;
  var tuy_chon = { cache: 'no-store' };
  var dong_ho = null;

  if (typeof AbortController === 'function') {
    var dieu_khien = new AbortController();
    tuy_chon.signal = dieu_khien.signal;
    dong_ho = setTimeout(function () { dieu_khien.abort(); }, het_gio);
  }

  return fetch(goc + duong_dan, tuy_chon)
    .then(function (r) {
      if (dong_ho) clearTimeout(dong_ho);
      if (!r.ok) {
        /* Backend tra 503 kem than JSON mo ta ly do, doc ra de hien cho nguoi
           dung biet la loi nguon du lieu chu khong phai loi trang web. */
        return r.json().then(function (than) {
          var mo_ta = (than && than.detail && than.detail.chi_tiet)
                   || (than && than.detail && than.detail.loi)
                   || ('HTTP ' + r.status);
          throw new Error(mo_ta);
        }, function () {
          throw new Error('HTTP ' + r.status);
        });
      }
      return r.json();
    })
    .catch(function (e) {
      if (dong_ho) clearTimeout(dong_ho);
      var mo_ta;
      if (e && e.name === 'AbortError') {
        mo_ta = 'Dịch vụ không trả lời trong '
              + Math.round(het_gio / 1000) + ' giây';
      } else if (e && e.name === 'TypeError') {
        /* Trinh duyet bao "Failed to fetch" cho moi loi tang mang va khong
           noi gi them, vi ly do an toan. Ba nguyen nhan thuc te la: dich vu
           chua chay, sai dia chi, hoac CORS tu choi. Noi ro ra de nguoi dung
           khong phai mo bang Network cua cong cu lap trinh. */
        mo_ta = 'Không gọi được dịch vụ. Thường là do dịch vụ chưa chạy, '
              + 'sai địa chỉ, hoặc địa chỉ trang chưa nằm trong CORS_NGUON '
              + 'của backend.';
      } else {
        mo_ta = (e && e.message) || 'Lỗi không rõ';
      }
      API_QT.loi = mo_ta;
      console.warn('Lỗi gọi ' + duong_dan + ': ' + mo_ta);
      return null;
    });
}


/* --------------------------------------------------------------------------
   Kiem tra dich vu truoc khi nap du lieu
   -------------------------------------------------------------------------- */
function kiem_tra_suc_khoe() {
  return _goi_api('/api/suc-khoe').then(function (dl) {
    API_QT.suc_khoe = dl;
    return dl;
  });
}


/* --------------------------------------------------------------------------
   Vi tri cac tram, dang GeoJSON
   -------------------------------------------------------------------------- */
function nap_tram_qtqg() {
  return _goi_api('/api/quan-trac/tram.geojson').then(function (dl) {
    API_QT.tram = dl;
    return dl;
  });
}


/* --------------------------------------------------------------------------
   So do moi nhat
   -------------------------------------------------------------------------- */
function nap_so_do_qtqg() {
  return _goi_api('/api/quan-trac/so-do').then(function (dl) {
    API_QT.so_do = dl;
    return dl;
  });
}


/* --------------------------------------------------------------------------
   Chuoi thoi gian mot tram, mot thong so
   -------------------------------------------------------------------------- */
function nap_chuoi_qtqg(ma, thong_so, tu, den) {
  var dd = '/api/quan-trac/chuoi?ma=' + encodeURIComponent(ma)
         + '&thong_so=' + encodeURIComponent(thong_so);
  if (tu) dd += '&tu=' + encodeURIComponent(tu);
  if (den) dd += '&den=' + encodeURIComponent(den);
  return _goi_api(dd);
}


/* --------------------------------------------------------------------------
   Ban ghi so do cua mot tram
   --------------------------------------------------------------------------
   Cung chu ky nhu lay_realtime() trong realtime.js, nho vay cac ham ve ky
   hieu va bang chi tiet dung duoc cho ca hai nguon.
   -------------------------------------------------------------------------- */
function lay_so_do(ma) {
  if (!API_QT.so_do || !API_QT.so_do.doi_tuong || !ma) return null;
  return API_QT.so_do.doi_tuong[ma] || null;
}


/* Co phai so lieu that hay khong. Giao dien dung de gan nhan. */
function la_so_lieu_that() {
  return !!(API_QT.so_do && API_QT.so_do.che_do === 'that');
}
