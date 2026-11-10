/* ==========================================================================
   dung_chung.js - Ham tien ich dung chung cho moi trang
   --------------------------------------------------------------------------
   Nap NGAY SAU tinh.js, truoc moi tep khac.

   Vi sao co tep nay: ba trang cua he thong nap bo ma khac nhau.
     index.html            nap day du, co ban do
     pages/thong-ke.html   chi config, tinh, xuat_tep, thong-ke
     pages/quan-trac.html  chi config, tinh, xuat_tep, api_quan_trac, quan_trac
   Bon ham duoi day truoc kia nam trong realtime.js va app.js, la hai tep gan
   chat voi LOP, ban_do va cac id DOM cua trang ban do. Trang thong ke va trang
   quan trac khong nap duoc hai tep do nhung van can bon ham nay, nen chung
   duoc tach ra day. Chung khong phu thuoc bien toan cuc nao ngoai DOM.
   ========================================================================== */


/* --------------------------------------------------------------------------
   The so lieu, dung cho hang KPI va cho hop thoai
   -------------------------------------------------------------------------- */
function the_so(nhan, gia_tri, phu) {
  return '<div class="the-so__o">'
       + '<div class="the-so__nhan">' + nhan + '</div>'
       + '<div class="the-so__gt">' + Number(gia_tri).toLocaleString('vi-VN') + '</div>'
       + (phu ? '<div class="the-so__phu">' + phu + '</div>' : '')
       + '</div>';
}


/* --------------------------------------------------------------------------
   Dinh dang thoi diem cap nhat
   --------------------------------------------------------------------------
   Ky quan trac khong phai luc nao cung la mot moc thoi gian. Co nguon ghi
   "Nam 2025" hay "Quy IV/2023"; new Date() van nhan nhung chuoi nhu vay roi
   tra ve 00:00 ngay 01/01, nghia la bay ra mot do chinh xac khong co that.
   Vi vay chi dinh dang khi chuoi dung dang ISO.
   -------------------------------------------------------------------------- */
function dinh_dang_thoi_diem(gia_tri) {
  if (!gia_tri) return '--';

  var chu = String(gia_tri);
  if (!/^\d{4}-\d{2}-\d{2}/.test(chu)) return chu;

  /* Chuoi chi co ngay, khong co gio. Dung new Date() thi trinh duyet hieu la
     nua dem gio UTC roi doi sang gio dia phuong, bay ra "07:00" khong co that.
     Cat tay ba phan ngay thang nam la dung va khong phu thuoc mui gio. */
  var chi_co_ngay = !/\d{2}:\d{2}/.test(chu);
  if (chi_co_ngay) {
    var p = chu.slice(0, 10).split('-');
    return p[2] + '/' + p[1] + '/' + p[0];
  }

  var d = new Date(chu);
  if (isNaN(d.getTime())) return chu;
  return d.toLocaleString('vi-VN', { day: '2-digit', month: '2-digit',
                                     year: 'numeric', hour: '2-digit',
                                     minute: '2-digit' });
}


/* --------------------------------------------------------------------------
   Hop thoai dung chung
   --------------------------------------------------------------------------
   Ca he thong dung MOT the hop thoai duy nhat. Nguoi goi tu dung chuoi HTML
   roi gan su kien cho cac nut ben trong SAU khi goi mo_hop_thoai().
   Trang nao dung hai ham nay thi phai co san #lop-mo va #hop-thoai trong HTML.
   -------------------------------------------------------------------------- */
function mo_hop_thoai(tieu_de, noi_dung_html) {
  document.getElementById('hop-thoai-ten').textContent = tieu_de;
  document.getElementById('hop-thoai-than').innerHTML = noi_dung_html;
  document.getElementById('lop-mo').hidden = false;
  document.getElementById('hop-thoai').hidden = false;
}

function dong_hop_thoai() {
  document.getElementById('lop-mo').hidden = true;
  document.getElementById('hop-thoai').hidden = true;
}
