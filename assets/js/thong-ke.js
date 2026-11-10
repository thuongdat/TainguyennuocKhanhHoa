/* ==========================================================================
   thong-ke.js - Trang thong ke tong hop
   --------------------------------------------------------------------------
   Doc thang cac tep trong data/ giong trang ban do, khong co ban sao du lieu
   rieng. Nho vay chay lai pipeline Python la trang nay tu co so moi.
   Dung lai CAU_HINH va DINH_DANG tu config.js, tai_ve_csv tu xuat_tep.js.
   ========================================================================== */

/* Kho du lieu da nap: ma_lop -> mang thuoc tinh cua tung doi tuong */
var DL = {};
var RT = null;                 /* noi dung realtime.json */
var MA_LUU_VUC_LOC = '';       /* '' nghia la toan tinh */
var BIEU_DO = {};              /* ma -> doi tuong Chart.js dang hien */

/* Bang mau cho bieu do phan loai, lay tong the tu bang mau du an */
var MAU_PHAN_LOAI = ['#0b5e72', '#16a6c9', '#0f766e', '#7c3aed',
                     '#ea580c', '#b45309', '#64748b', '#be185d'];

/* Cac lop can nap. Lop nao thieu thi bao loi ro rang thay vi hien so 0 */
var CAC_LOP_CAN = ['luu_vuc', 'song_suoi', 'khai_thac', 'ao_ho',
                   'xa_thai', 'doan_song', 'ranh_gioi_xa'];


/* --------------------------------------------------------------------------
   Khoi dong
   -------------------------------------------------------------------------- */
document.addEventListener('DOMContentLoaded', function () {
  khoi_phuc_giao_dien();

  if (location.protocol === 'file:') {
    bao_loi('Trang đang được mở trực tiếp từ ổ đĩa (<code>file://</code>). '
      + 'Trình duyệt chặn việc đọc tệp dữ liệu theo cách này. Mở terminal tại '
      + 'thư mục dự án, chạy <code>python -m http.server 8000</code> rồi vào '
      + '<strong>http://localhost:8000/pages/thong-ke.html</strong>.');
    return;
  }

  nap_tinh()
    .then(function () {
      gan_su_kien();
      return nap_tat_ca();
    })
    .then(function () {
      document.getElementById('man-cho').hidden = true;
      document.getElementById('noi-dung-tk').hidden = false;
      an_muc_thieu_du_lieu();
      cap_nhat_dai_thong_bao();
      dung_bo_loc_luu_vuc();
      ve_tat_ca();
      ve_phan_hanh_chinh();   /* du lieu that, khong chiu anh huong bo loc */
    })
    .catch(function (e) {
      bao_loi('Không nạp được dữ liệu: ' + e.message
        + '<br>Hãy chạy lại pipeline trong thư mục <code>scripts/</code> '
        + 'rồi tải lại trang.');
    });
});

function gan_su_kien() {
  document.getElementById('loc-luu-vuc').addEventListener('change', function () {
    MA_LUU_VUC_LOC = this.value;
    ve_tat_ca();
  });

  document.getElementById('xuat-bang').addEventListener('click', xuat_bang_khai_thac);
  document.getElementById('nut-giao-dien').addEventListener('click', doi_giao_dien);
}


/* --------------------------------------------------------------------------
   Nap du lieu
   -------------------------------------------------------------------------- */
function nap_tat_ca() {
  /* Tinh nao chua co lop nao thi bo qua lop do, cac muc tuong ung se an di */
  var viec = CAC_LOP_CAN.filter(lop_co_san).map(function (ma) {
    var dn = CAU_HINH.lop[ma];
    return fetch(duong_dan_du_lieu(dn.tep))
      .then(function (r) {
        if (!r.ok) throw new Error(dn.tep + ' trả về HTTP ' + r.status);
        return r.json();
      })
      .then(function (gj) {
        DL[ma] = (gj.features || []).map(function (f) { return f.properties || {}; });
      });
  });

  /* Thieu realtime thi van xem duoc phan tinh, chi mat bieu do ho chua va WQI */
  viec.push(
    fetch(duong_dan_du_lieu('realtime.json') + '&t=' + Date.now())
      .then(function (r) { return r.ok ? r.json() : null; })
      .then(function (dl) { RT = dl; })
      .catch(function () { RT = null; })
  );

  return Promise.all(viec);
}

/* Muc nao doi hoi lop ma tinh nay chua co thi an di, thay vi hien bieu do rong.
   Lop can thiet khai bao bang thuoc tinh data-can-lop trong HTML. */
function an_muc_thieu_du_lieu() {
  var cac_muc = document.querySelectorAll('[data-can-lop]');
  for (var i = 0; i < cac_muc.length; i++) {
    var can = cac_muc[i].getAttribute('data-can-lop').split(/\s+/);
    var du = can.every(function (ma) { return DL[ma] && DL[ma].length > 0; });
    cac_muc[i].hidden = !du;
  }

  /* Khong con muc nao ve nuoc thi noi ro de nguoi dung khong tuong trang bi loi */
  var con = document.querySelectorAll('[data-can-lop]:not([hidden])').length;
  if (con <= 1) {
    var o = document.getElementById('loi-nap');
    o.hidden = false;
    o.innerHTML = '<strong>' + TINH.ten_tinh + ' chưa có lớp dữ liệu chuyên đề '
      + 'về nước.</strong><br>Hiện mới có ranh giới hành chính và nền địa phương. '
      + 'Khi đưa dữ liệu kiểm kê vào <code>data_goc/</code> và chạy script chuẩn hóa, '
      + 'các mục thống kê tương ứng sẽ tự hiện.';
  }
}

/* Dai canh bao chi co nghia voi tinh dang dung du lieu mo phong */
function cap_nhat_dai_thong_bao() {
  var dai = document.getElementById('dai-thong-bao');
  if (dai && !TINH.co_du_lieu_mo_phong) dai.hidden = true;
}

function bao_loi(html) {
  document.getElementById('man-cho').hidden = true;
  var o = document.getElementById('loi-nap');
  o.hidden = false;
  o.innerHTML = html;
}


/* --------------------------------------------------------------------------
   Bo loc theo luu vuc
   -------------------------------------------------------------------------- */
function dung_bo_loc_luu_vuc() {
  var o = document.getElementById('loc-luu-vuc');
  (DL.luu_vuc || []).forEach(function (lv) {
    var opt = document.createElement('option');
    opt.value = lv.ma;
    opt.textContent = lv.ten;
    o.appendChild(opt);
  });
}

/* Loc mot mang thuoc tinh theo luu vuc dang chon */
function loc(ma_lop) {
  var ds = DL[ma_lop] || [];
  if (!MA_LUU_VUC_LOC) return ds;
  return ds.filter(function (p) { return p.ma_luu_vuc === MA_LUU_VUC_LOC; });
}

/* Ho la CONG TRINH KHAI THAC trong lop ao_ho: chi cac doi tuong mang luu luong.

   ao_ho.geojson co hai kieu. Kieu cu do scripts/05 tach tu bang khai thac,
   moi ho mang q_khai_thac_m3_ngay va phai cong vao khai thac. Kieu moi do
   scripts/12 nap tu ban ra soat kiem ke la danh muc NGUON NUOC, khong co luu
   luong; khi do cac ho khai thac da nam san trong khai_thac.geojson, cong
   them ao_ho la dem trung.

   Phan biet bang viec doi tuong CO KHOA q_khai_thac_m3_ngay hay khong, chu
   khong xet gia tri: tep kieu cu luon ghi khoa do (ke ca khi gia tri rong),
   tep kieu moi khong bao gio co. */
function ho_khai_thac_trong_ao_ho(ds) {
  return (ds || []).filter(function (p) {
    return Object.prototype.hasOwnProperty.call(p, 'q_khai_thac_m3_ngay');
  });
}

/* Cong trinh khai thac day du, khong phu thuoc ho dang nam o lop nao */
function gop_khai_thac(ds_khai_thac, ds_ao_ho) {
  return (ds_khai_thac || []).concat(ho_khai_thac_trong_ao_ho(ds_ao_ho));
}

function khai_thac_day_du() {
  return gop_khai_thac(loc('khai_thac'), loc('ao_ho'));
}

/* So ho chua trong danh muc khai thac: ho con nam o ao_ho kieu cu, cong voi
   cong trinh loai "Ho..." nam trong khai_thac */
function dem_ho_khai_thac() {
  var trong_khai_thac = loc('khai_thac').filter(function (p) {
    return String(p.loai_hinh || '').indexOf('Hồ') === 0;
  }).length;
  return ho_khai_thac_trong_ao_ho(loc('ao_ho')).length + trong_khai_thac;
}

function tong(ds, truong) {
  return ds.reduce(function (t, p) { return t + (Number(p[truong]) || 0); }, 0);
}

/* Gom nhom va cong don mot truong so theo mot truong phan loai */
function gom_nhom(ds, truong_nhom, truong_cong) {
  var bang = {};
  ds.forEach(function (p) {
    var khoa = p[truong_nhom] || '(không rõ)';
    bang[khoa] = (bang[khoa] || 0) + (truong_cong ? (Number(p[truong_cong]) || 0) : 1);
  });
  return bang;
}


/* --------------------------------------------------------------------------
   Ve lai moi thanh phan chiu anh huong cua bo loc
   -------------------------------------------------------------------------- */
function ve_tat_ca() {
  ve_kpi();
  ve_bd_luu_vuc();
  ve_bd_loai_hinh();
  ve_bd_suc_chiu_tai();
  ve_bang_khai_thac();
  ve_thoi_diem();
}


/* --------------------------------------------------------------------------
   The chi tieu
   -------------------------------------------------------------------------- */
function ve_kpi() {
  var kt = khai_thac_day_du();
  var xt = loc('xa_thai');
  var ds_song = loc('doan_song');

  var q_khai_thac = tong(kt, 'q_khai_thac_m3_ngay');
  var q_xa = tong(xt, 'q_xa_m3_ngay');
  var so_ho = dem_ho_khai_thac();

  var het_kha_nang = ds_song.filter(function (p) {
    return p.trang_thai === 'Không còn khả năng tiếp nhận';
  }).length;

  var html = ''
    + the_kpi('Khai thác nước mặt (quy đổi)',
              so(q_khai_thac), 'm³/ngày · ' + kt.length + ' công trình', '', 'that')
    + the_kpi('Xả thải vào nguồn nước',
              so(q_xa), 'm³/ngày · ' + xt.length + ' điểm xả', '', 'that')
    + the_kpi('Đoạn sông hết khả năng tiếp nhận',
              het_kha_nang, 'trên tổng ' + ds_song.length + ' đoạn đánh giá',
              het_kha_nang > 0 ? 'xau' : 'tot', 'mp')
    + the_kpi('Hồ chứa trong danh mục khai thác',
              so(so_ho), 'trên tổng ' + kt.length + ' công trình khai thác', '', 'that');

  document.getElementById('hang-kpi').innerHTML = html;
}

/* nhan_nguon: 'mp' cho du lieu mo phong, 'that' cho du lieu that, '' thi khong gan */
function the_kpi(nhan, gia_tri, phu, trang_thai, nhan_nguon) {
  var huy_hieu = '';
  if (nhan_nguon === 'mp') huy_hieu = '<span class="the-mp">mô phỏng</span>';
  else if (nhan_nguon === 'that') huy_hieu = '<span class="the-that">dữ liệu thật</span>';

  return '<div class="the-so__o' + (trang_thai ? ' the-so__o--' + trang_thai : '') + '">'
       + huy_hieu
       + '<div class="the-so__nhan">' + nhan + '</div>'
       + '<div class="the-so__gt">' + gia_tri + '</div>'
       + '<div class="the-so__phu">' + phu + '</div>'
       + '</div>';
}

function mau_theo_dung_tich_kpi(ty_le) {
  if (ty_le === null) return '';
  if (ty_le < 0.30) return 'xau';
  if (ty_le < 0.50) return 'theodoi';
  return 'tot';
}


/* --------------------------------------------------------------------------
   Bieu do: khai thac va xa thai theo luu vuc
   -------------------------------------------------------------------------- */
function ve_bd_luu_vuc() {
  /* Bieu do nay luon ve toan bo luu vuc de con so sanh duoc giua cac luu vuc,
     nhung luu vuc dang chon se duoc lam noi bat */
  var ds_lv = DL.luu_vuc || [];
  var nhan = ds_lv.map(function (lv) {
    return lv.ten.replace('Lưu vực sông ', '');
  });

  var kt = ds_lv.map(function (lv) {
    return tong(gop_khai_thac(DL.khai_thac, DL.ao_ho).filter(function (p) {
      return p.ma_luu_vuc === lv.ma;
    }), 'q_khai_thac_m3_ngay');
  });

  var xt = ds_lv.map(function (lv) {
    return tong((DL.xa_thai || []).filter(function (p) {
      return p.ma_luu_vuc === lv.ma;
    }), 'q_xa_m3_ngay');
  });

  /* Lam mo cac luu vuc khong duoc chon */
  function mau(co_ban, i) {
    if (!MA_LUU_VUC_LOC) return co_ban;
    return ds_lv[i].ma === MA_LUU_VUC_LOC ? co_ban : co_ban + '33';
  }

  ve_bieu_do('bd-luu-vuc', {
    type: 'bar',
    data: {
      labels: nhan,
      datasets: [
        { label: 'Khai thác (quy đổi)',
          data: kt,
          backgroundColor: kt.map(function (_, i) { return mau('#0b5e72', i); }),
          borderRadius: 3 },
        { label: 'Xả thải',
          data: xt,
          backgroundColor: xt.map(function (_, i) { return mau('#ea580c', i); }),
          borderRadius: 3 },
      ],
    },
    options: tuy_chon_chung({
      scales: {
        x: { grid: { display: false }, ticks: { font: { size: 10 } } },
        y: { beginAtZero: true, ticks: { callback: function (v) { return so(v); } } },
      },
      plugins: { tooltip: { callbacks: { label: function (c) {
        return c.dataset.label + ': ' + so(c.parsed.y) + ' m³/ngày';
      } } } },
    }),
  });
}


/* --------------------------------------------------------------------------
   Bieu do: co cau khai thac theo loai hinh
   -------------------------------------------------------------------------- */
function ve_bd_loai_hinh() {
  var bang = gom_nhom(khai_thac_day_du(), 'loai_hinh', 'q_khai_thac_m3_ngay');
  var nhan = Object.keys(bang).sort(function (a, b) { return bang[b] - bang[a]; });

  ve_bieu_do('bd-loai-hinh', {
    type: 'doughnut',
    data: {
      labels: nhan,
      datasets: [{
        data: nhan.map(function (k) { return bang[k]; }),
        backgroundColor: nhan.map(function (_, i) {
          return MAU_PHAN_LOAI[i % MAU_PHAN_LOAI.length];
        }),
        borderColor: lay_mau('--nen-the', '#fff'),
        borderWidth: 2,
      }],
    },
    options: tuy_chon_chung({
      cutout: '58%',
      scales: {},
      plugins: {
        legend: { display: true, position: 'right',
                  labels: { boxWidth: 10, font: { size: 11 },
                            color: lay_mau('--chu-mo', '#5c6b7a') } },
        tooltip: { callbacks: { label: function (c) {
          var tong_ds = c.dataset.data.reduce(function (a, b) { return a + b; }, 0);
          var pt = tong_ds ? (c.parsed / tong_ds * 100).toFixed(1) : '0';
          return c.label + ': ' + so(c.parsed) + ' m³/ngày (' + pt + '%)';
        } } },
      },
    }),
  });
}


/* --------------------------------------------------------------------------
   Bieu do: suc chiu tai doan song, cot chong theo luu vuc
   -------------------------------------------------------------------------- */
function ve_bd_suc_chiu_tai() {
  var ds_lv = DL.luu_vuc || [];
  var ds = DL.doan_song || [];
  var cac_trang_thai = ['Còn khả năng tiếp nhận', 'Gần ngưỡng',
                        'Không còn khả năng tiếp nhận'];
  var mau_tt = [MAU.tot, MAU.theo_doi, MAU.xau];

  /* Chi giu luu vuc thuc su co doan song duoc danh gia */
  var lv_co = ds_lv.filter(function (lv) {
    return ds.some(function (p) { return p.ma_luu_vuc === lv.ma; });
  });

  ve_bieu_do('bd-suc-chiu-tai', {
    type: 'bar',
    data: {
      labels: lv_co.map(function (lv) { return lv.ten.replace('Lưu vực sông ', ''); }),
      datasets: cac_trang_thai.map(function (tt, i) {
        return {
          label: tt,
          data: lv_co.map(function (lv) {
            return ds.filter(function (p) {
              return p.ma_luu_vuc === lv.ma && p.trang_thai === tt;
            }).length;
          }),
          backgroundColor: mau_tt[i],
          borderRadius: 2,
        };
      }),
    },
    options: tuy_chon_chung({
      indexAxis: 'y',
      scales: {
        x: { stacked: true, beginAtZero: true,
             ticks: { precision: 0 },
             title: { display: true, text: 'Số đoạn sông',
                      color: lay_mau('--chu-mo', '#5c6b7a'), font: { size: 11 } } },
        y: { stacked: true, grid: { display: false }, ticks: { font: { size: 10.5 } } },
      },
    }),
  });
}


/* --------------------------------------------------------------------------
   Bang danh sach cong trinh khai thac
   -------------------------------------------------------------------------- */
var COT_BANG = [
  { ma: 'ma', ten: 'Mã' },
  { ma: 'ten_cong_trinh', ten: 'Tên công trình' },
  { ma: 'loai_hinh', ten: 'Loại công trình' },
  { ma: 'muc_dich_su_dung', ten: 'Mục đích' },
  { ma: 'xa_phuong', ten: 'Xã, phường' },
  { ma: 'ten_luu_vuc', ten: 'Lưu vực' },
  { ma: 'dung_tich_ho_trieu_m3', ten: 'Dung tích hồ (triệu m³)', so: true },
  { ma: 'q_khai_thac_m3_ngay', ten: 'Q khai thác quy đổi (m³/ngày)', so: true },
];

function ve_bang_khai_thac() {
  var ds = khai_thac_day_du().slice().sort(function (a, b) {
    return (b.q_khai_thac_m3_ngay || 0) - (a.q_khai_thac_m3_ngay || 0);
  });

  var bang = document.getElementById('bang-khai-thac');
  var dau = bang.querySelector('thead');
  var than = bang.querySelector('tbody');

  dau.innerHTML = '<tr>' + COT_BANG.map(function (c) {
    return '<th>' + c.ten + '</th>';
  }).join('') + '</tr>';

  than.innerHTML = ds.map(function (p) {
    return '<tr>'
      + '<td>' + (p.ma || '--') + '</td>'
      + '<td>' + (p.ten_cong_trinh || '--') + '</td>'
      + '<td>' + (p.loai_hinh || '--') + '</td>'
      + '<td>' + (p.muc_dich_su_dung || '--') + '</td>'
      + '<td>' + (p.xa_phuong || '--') + '</td>'
      + '<td>' + (p.ten_luu_vuc || '--') + '</td>'
      + '<td>' + (p.dung_tich_ho_trieu_m3 ? so_le(p.dung_tich_ho_trieu_m3) : '--') + '</td>'
      + '<td>' + so(p.q_khai_thac_m3_ngay) + '</td>'
      + '</tr>';
  }).join('');

  document.getElementById('tom-tat-bang').textContent =
    ds.length + ' công trình' + (MA_LUU_VUC_LOC ? ' trong lưu vực đang chọn' : ' trên toàn tỉnh');
}

function xuat_bang_khai_thac() {
  var ds = khai_thac_day_du().slice().sort(function (a, b) {
    return (b.q_khai_thac_m3_ngay || 0) - (a.q_khai_thac_m3_ngay || 0);
  });

  var cot = COT_BANG.map(function (c) { return c.ten; });
  cot.push('Nguồn dữ liệu');

  var hang = ds.map(function (p) {
    return [p.ma, p.ten_cong_trinh, p.loai_hinh, p.muc_dich_su_dung, p.xa_phuong,
            p.ten_luu_vuc, p.dung_tich_ho_trieu_m3, p.q_khai_thac_m3_ngay,
            p.nguon_dl || ''];
  });

  var ten = 'thong_ke_khai_thac'
          + (MA_LUU_VUC_LOC ? '_' + MA_LUU_VUC_LOC : '') + '.csv';
  tai_ve_csv(ten, cot, hang);
}


/* --------------------------------------------------------------------------
   Phan du lieu hanh chinh, nguon that, khong chiu anh huong bo loc luu vuc
   -------------------------------------------------------------------------- */
function ve_phan_hanh_chinh() {
  var xa = DL.ranh_gioi_xa || [];
  if (xa.length === 0) return;

  var dien_tich = tong(xa, 'dien_tich_km2');
  var dan_so = tong(xa, 'dan_so');
  var mat_do = dien_tich > 0 ? dan_so / dien_tich : 0;

  /* Loai don vi suy tu tien to cua ten. Truong phan_loai trong du lieu goc la
     phan loai dia hinh (Hai dao, Mien nui), khong phai loai don vi hanh chinh. */
  var theo_loai = gom_nhom(xa.map(function (p) {
    return { loai: loai_don_vi(p.ten) };
  }), 'loai', null);

  var mo_ta_loai = Object.keys(theo_loai)
    .sort(function (a, b) { return theo_loai[b] - theo_loai[a]; })
    .map(function (k) { return theo_loai[k] + ' ' + k.toLowerCase(); })
    .join(', ');

  document.getElementById('hang-kpi-hc').innerHTML = ''
    + the_kpi('Đơn vị hành chính cấp xã', xa.length, mo_ta_loai, '', 'that')
    + the_kpi('Tổng diện tích', so_le(dien_tich), 'km²', '', 'that')
    + the_kpi('Tổng dân số', so(dan_so), 'người', '', 'that')
    + the_kpi('Mật độ dân số', so(Math.round(mat_do)), 'người/km²', '', 'that');

  ve_top_xa('bd-dan-so', xa, 'dan_so', '#0b5e72', 'người');
  ve_top_xa('bd-dien-tich', xa, 'dien_tich_km2', '#0f766e', 'km²');
}

/* Ten don vi luon bat dau bang loai: "Phuong Ba Ngoi", "Xa Dien Khanh",
   "Dac khu Truong Sa". Lay tien to do lam loai don vi. */
function loai_don_vi(ten) {
  var t = String(ten || '').trim();
  if (t.indexOf('Đặc khu ') === 0) return 'Đặc khu';
  if (t.indexOf('Phường ') === 0) return 'Phường';
  if (t.indexOf('Thị trấn ') === 0) return 'Thị trấn';
  if (t.indexOf('Xã ') === 0) return 'Xã';
  return 'Đơn vị khác';
}

function ve_top_xa(id_canvas, xa, truong, mau, don_vi) {
  var top = xa.slice().sort(function (a, b) {
    return (Number(b[truong]) || 0) - (Number(a[truong]) || 0);
  }).slice(0, 10).reverse();

  ve_bieu_do(id_canvas, {
    type: 'bar',
    data: {
      labels: top.map(function (p) { return p.ten; }),
      datasets: [{
        data: top.map(function (p) { return Number(p[truong]) || 0; }),
        backgroundColor: mau,
        borderRadius: 3,
      }],
    },
    options: tuy_chon_chung({
      indexAxis: 'y',
      scales: {
        x: { beginAtZero: true, ticks: { callback: function (v) { return so(v); } } },
        y: { grid: { display: false }, ticks: { font: { size: 10.5 } } },
      },
      plugins: {
        legend: { display: false },
        tooltip: { callbacks: { label: function (c) {
          return so_le(c.parsed.x) + ' ' + don_vi;
        } } },
      },
    }),
  });
}


/* --------------------------------------------------------------------------
   Tien ich ve bieu do
   -------------------------------------------------------------------------- */
function ve_bieu_do(id_canvas, cau_hinh) {
  if (BIEU_DO[id_canvas]) BIEU_DO[id_canvas].destroy();
  var canvas = document.getElementById(id_canvas);
  if (!canvas) return;
  BIEU_DO[id_canvas] = new Chart(canvas, cau_hinh);
}

/* Tuy chon dung chung, da gan mau chu va mau luoi theo nen sang hay toi */
function tuy_chon_chung(rieng) {
  var mau_chu = lay_mau('--chu-mo', '#5c6b7a');
  var mau_luoi = lay_mau('--vien-nhat', '#e7ebef');

  var chung = {
    responsive: true,
    maintainAspectRatio: false,
    animation: { duration: 300 },
    plugins: {
      legend: { labels: { boxWidth: 12, font: { size: 11 }, color: mau_chu } },
      tooltip: { intersect: false, mode: 'index' },
    },
    scales: {
      x: { ticks: { color: mau_chu, font: { size: 11 } }, grid: { color: mau_luoi } },
      y: { ticks: { color: mau_chu, font: { size: 11 } }, grid: { color: mau_luoi } },
    },
  };

  /* Gop nong, du cho muc dich o day */
  var kq = Object.assign({}, chung, rieng || {});
  kq.plugins = Object.assign({}, chung.plugins, (rieng || {}).plugins || {});

  if (rieng && rieng.scales !== undefined) {
    kq.scales = {};
    Object.keys(rieng.scales).forEach(function (truc) {
      kq.scales[truc] = Object.assign({}, chung.scales[truc] || {}, rieng.scales[truc]);
      kq.scales[truc].ticks = Object.assign(
        {}, (chung.scales[truc] || {}).ticks || {}, rieng.scales[truc].ticks || {});
      if (rieng.scales[truc].grid) {
        kq.scales[truc].grid = Object.assign(
          { color: mau_luoi }, rieng.scales[truc].grid);
      }
    });
  }

  return kq;
}

function lay_mau(bien, mac_dinh) {
  var v = getComputedStyle(document.body).getPropertyValue(bien).trim();
  return v || mac_dinh;
}


/* --------------------------------------------------------------------------
   Dinh dang va giao dien
   -------------------------------------------------------------------------- */
function so(v) { return DINH_DANG.so(v) || '0'; }
function so_le(v) { return DINH_DANG.so_le(v) || '0'; }
function phan_tram(v) { return DINH_DANG.phan_tram(v) || '--'; }

function ve_thoi_diem() {
  var o_qt = document.getElementById('thoi-diem-qt');
  var o_ct = document.getElementById('thoi-diem-cap-nhat');
  if (!RT || !RT.thoi_diem || !RT.so_doi_tuong) {
    o_qt.textContent = 'chưa có số liệu';
    o_ct.textContent = '--';
    return;
  }
  var d = new Date(RT.thoi_diem);
  var chu = isNaN(d.getTime()) ? RT.thoi_diem
    : d.toLocaleString('vi-VN', { day: '2-digit', month: '2-digit', year: 'numeric',
                                 hour: '2-digit', minute: '2-digit' });
  o_qt.textContent = chu;
  o_ct.textContent = chu + (RT.che_do !== 'that' ? ' (mô phỏng)' : '');
}

function doi_giao_dien() {
  var hien_tai = document.documentElement.getAttribute('data-giao-dien');
  var moi;
  if (hien_tai === 'toi') moi = 'sang';
  else if (hien_tai === 'sang') moi = 'toi';
  else moi = window.matchMedia('(prefers-color-scheme: dark)').matches ? 'sang' : 'toi';

  document.documentElement.setAttribute('data-giao-dien', moi);
  try { localStorage.setItem('giao_dien', moi); } catch (e) { /* bo qua */ }

  /* Ve lai toan bo bieu do de doi mau chu va mau luoi */
  ve_tat_ca();
  ve_phan_hanh_chinh();
}

function khoi_phuc_giao_dien() {
  try {
    var da_luu = localStorage.getItem('giao_dien');
    if (da_luu) document.documentElement.setAttribute('data-giao-dien', da_luu);
  } catch (e) { /* trinh duyet chan localStorage, bo qua */ }
}
