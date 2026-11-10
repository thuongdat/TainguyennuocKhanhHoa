/* ==========================================================================
   xuat_tep.js - Tien ich tai tep ve may, dung chung cho moi trang
   --------------------------------------------------------------------------
   Tach rieng khoi table.js de trang thong ke dung lai duoc ma khong phai nap
   ca bo ma nguon cua ban do. Quy uoc CSV chi dinh nghia mot cho duy nhat o
   day, tranh hai trang xuat ra hai kieu khac nhau.
   ========================================================================== */

/* Tao va tai xuong mot tep CSV.
   Them BOM UTF-8 o dau tep de Excel doc dung tieng Viet co dau.
   Dung dau phay lam dau phan cach theo chuan RFC 4180, moi o deu duoc dat
   trong ngoac kep nen GeoPandas, pandas va QGIS deu doc duoc truc tiep. */
function tai_ve_csv(ten_tep, cac_cot, cac_hang) {
  var dong = [cac_cot.map(boc_o_csv).join(',')];
  cac_hang.forEach(function (h) {
    dong.push(h.map(boc_o_csv).join(','));
  });
  var noi_dung = '﻿' + dong.join('\r\n');
  tai_ve_tep(ten_tep, noi_dung, 'text/csv;charset=utf-8');
}

function boc_o_csv(gia_tri) {
  var s = (gia_tri === null || gia_tri === undefined) ? '' : String(gia_tri);
  return '"' + s.replace(/"/g, '""') + '"';
}

/* Moi duong tai tep (CSV, GeoJSON) cua ca ba trang deu di qua day, nen cong
   mat khau chi can dat o mot cho. Chua nhap dung mat khau thi khong tai. */
function tai_ve_tep(ten_tep, noi_dung, kieu_mime) {
  yeu_cau_mat_khau().then(
    function () { thuc_hien_tai_ve(ten_tep, noi_dung, kieu_mime); },
    function () { /* nguoi dung dong hop thoai, khong tai */ }
  );
}

function thuc_hien_tai_ve(ten_tep, noi_dung, kieu_mime) {
  var blob = new Blob([noi_dung], { type: kieu_mime });
  var url = URL.createObjectURL(blob);
  var a = document.createElement('a');
  a.href = url;
  a.download = ten_tep;
  document.body.appendChild(a);
  a.click();
  document.body.removeChild(a);
  /* Giai phong bo nho sau khi trinh duyet da bat dau tai */
  setTimeout(function () { URL.revokeObjectURL(url); }, 2000);

  /* Trang ban do co thanh mach bao rieng, trang thong ke thi khong */
  if (typeof hien_mach_bao === 'function') {
    hien_mach_bao('Đã xuất tệp ' + ten_tep, 3000);
  }
}


/* ==========================================================================
   Cong mat khau cho chuc nang xuat du lieu

   GIOI HAN CAN BIET: trang nay thuan tinh nen mat khau chi duoc kiem o phia
   trinh duyet. No ngan nguoi dung thong thuong bam nut tai, KHONG ngan duoc
   nguoi co y: cac tep data/*.geojson van tai thang duoc bang duong dan, va ai
   biet sua JavaScript thi bo qua duoc cong nay. Muon chan that su thi phai
   kiem o may chu (vi du backend/ cap token), khong lam duoc tren trang tinh.

   Mat khau KHONG nam trong ma nguon. tinh.json chi giu muoi va ma bam
   PBKDF2-SHA256 (tinh.xuat_du_lieu), tao bang scripts/11_dat_mat_khau_xuat.py.
   Chua cau hinh ma bam thi cong DONG (khong cho tai), khong bao gio mo.
   ========================================================================== */

var KHOA_PHIEN_XUAT = 'xuat_du_lieu_da_mo';
var SO_LAN_SAI_MAT_KHAU = 0;
var HOP_MAT_KHAU = null;          /* hop thoai dung mot lan roi giu lai */

function cau_hinh_xuat_du_lieu() {
  var c = (typeof TINH !== 'undefined' && TINH) ? TINH.xuat_du_lieu : null;
  return c || {};
}

function hex_sang_byte(hex) {
  var kq = new Uint8Array(hex.length / 2);
  for (var i = 0; i < kq.length; i++) kq[i] = parseInt(hex.substr(i * 2, 2), 16);
  return kq;
}

function byte_sang_hex(buf) {
  return Array.prototype.map.call(new Uint8Array(buf), function (b) {
    return ('0' + b.toString(16)).slice(-2);
  }).join('');
}

/* PBKDF2-SHA256 bang Web Crypto, cung tham so voi hashlib.pbkdf2_hmac cua script 11 */
function bam_mat_khau(mat_khau, muoi_hex, so_vong) {
  var ma_hoa = new TextEncoder();
  return crypto.subtle.importKey('raw', ma_hoa.encode(mat_khau), 'PBKDF2', false, ['deriveBits'])
    .then(function (khoa) {
      return crypto.subtle.deriveBits(
        { name: 'PBKDF2', salt: hex_sang_byte(muoi_hex), iterations: so_vong, hash: 'SHA-256' },
        khoa, 256);
    })
    .then(byte_sang_hex);
}

function da_mo_khoa_phien(ma_bam) {
  try { return sessionStorage.getItem(KHOA_PHIEN_XUAT) === ma_bam; } catch (e) { return false; }
}

function ghi_nho_phien(ma_bam) {
  /* Chi luu co "da mo" gan voi ma bam: doi mat khau la tu het hieu luc. */
  try { sessionStorage.setItem(KHOA_PHIEN_XUAT, ma_bam); } catch (e) { /* bo qua */ }
}

/* Tra ve Promise: thanh cong khi duoc phep tai, bi tu choi khi nguoi dung dong hop thoai */
function yeu_cau_mat_khau() {
  var c = cau_hinh_xuat_du_lieu();
  if (c.yeu_cau_mat_khau === false) return Promise.resolve();

  var chua_cau_hinh = !c.ma_bam || !c.muoi;
  if (!chua_cau_hinh && da_mo_khoa_phien(c.ma_bam)) return Promise.resolve();

  /* Trinh duyet khong co Web Crypto (trang khong phai https hay localhost) */
  if (!window.crypto || !crypto.subtle) chua_cau_hinh = true;

  return new Promise(function (xong, tu_choi) {
    mo_hop_mat_khau(c, chua_cau_hinh, xong, tu_choi);
  });
}

function dung_hop_mat_khau() {
  var lop = document.createElement('div');
  lop.className = 'lop-mo';
  lop.hidden = true;

  var hop = document.createElement('div');
  hop.className = 'hop-thoai';
  hop.hidden = true;
  hop.setAttribute('role', 'dialog');
  hop.setAttribute('aria-modal', 'true');
  hop.setAttribute('aria-labelledby', 'hop-mat-khau-ten');
  hop.style.width = 'min(420px, calc(100vw - 32px))';
  hop.innerHTML =
      '<div class="hop-thoai__dau">'
    + '<h2 id="hop-mat-khau-ten">Nhập mật khẩu để tải dữ liệu</h2>'
    + '<button type="button" class="nut-bieu-tuong" data-dong aria-label="Đóng">&times;</button>'
    + '</div>'
    + '<div class="hop-thoai__than">'
    + '<p class="ghi-chu-nho" data-mo-ta></p>'
    + '<form data-form autocomplete="off">'
    + '<input type="password" data-mat-khau autocomplete="off" aria-label="Mật khẩu" '
    + 'style="width:100%;padding:8px 10px;margin:10px 0;border:1px solid var(--vien);'
    + 'border-radius:6px;background:var(--nen-the);color:inherit;font:inherit">'
    + '<p data-loi role="alert" hidden style="color:#b91c1c;margin:0 0 10px"></p>'
    + '<button type="submit" class="nut nut--chinh" data-gui>Xác nhận</button>'
    + '</form></div>';

  document.body.appendChild(lop);
  document.body.appendChild(hop);
  return { lop: lop, hop: hop };
}

function mo_hop_mat_khau(c, chua_cau_hinh, xong, tu_choi) {
  if (!HOP_MAT_KHAU) HOP_MAT_KHAU = dung_hop_mat_khau();
  var lop = HOP_MAT_KHAU.lop, hop = HOP_MAT_KHAU.hop;

  /* Thay form bang ban sao de khong chong chat handler cua lan mo truoc */
  var form = hop.querySelector('[data-form]');
  var form_moi = form.cloneNode(true);
  form.parentNode.replaceChild(form_moi, form);
  form = form_moi;
  var o_nhap = form.querySelector('[data-mat-khau]');
  var o_loi = form.querySelector('[data-loi]');
  var nut_gui = form.querySelector('[data-gui]');

  hop.querySelector('[data-mo-ta]').textContent = chua_cau_hinh
    ? 'Chức năng tải dữ liệu chưa được cấu hình mật khẩu nên đang bị khóa. '
      + 'Liên hệ quản trị viên hệ thống.'
    : 'Việc xuất CSV và GeoJSON cần mật khẩu. Liên hệ đơn vị quản lý nếu chưa có.';
  o_nhap.value = '';
  o_nhap.hidden = chua_cau_hinh;
  nut_gui.hidden = chua_cau_hinh;
  o_loi.hidden = true;

  function dong() {
    lop.hidden = true;
    hop.hidden = true;
    document.removeEventListener('keydown', khi_nhan_phim);
  }
  function khi_nhan_phim(e) {
    if (e.key === 'Escape') { dong(); tu_choi(); }
  }
  document.addEventListener('keydown', khi_nhan_phim);
  hop.querySelector('[data-dong]').onclick = function () { dong(); tu_choi(); };
  lop.onclick = function () { dong(); tu_choi(); };

  form.addEventListener('submit', function (e) {
    e.preventDefault();
    var mat_khau = o_nhap.value;
    if (!mat_khau) return;
    nut_gui.disabled = true;
    o_loi.hidden = true;

    bam_mat_khau(mat_khau, c.muoi, c.so_vong || 200000).then(function (ma) {
      o_nhap.value = '';
      if (ma === c.ma_bam) {
        SO_LAN_SAI_MAT_KHAU = 0;
        ghi_nho_phien(c.ma_bam);
        dong();
        xong();
        return;
      }
      /* Sai: cang sai nhieu cang phai cho lau, toi da 30 giay */
      SO_LAN_SAI_MAT_KHAU++;
      var cho = Math.min(30, SO_LAN_SAI_MAT_KHAU * 2);
      o_loi.textContent = 'Mật khẩu không đúng. Chờ ' + cho + ' giây rồi thử lại.';
      o_loi.hidden = false;
      setTimeout(function () { nut_gui.disabled = false; o_nhap.focus(); }, cho * 1000);
    });
  });

  lop.hidden = false;
  hop.hidden = false;
  if (!chua_cau_hinh) o_nhap.focus();
}
