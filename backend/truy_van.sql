-- Cac cau SELECT gui len CSDL QTQG.
--
-- Tach khoi ma Python de de doi chieu voi schema that va de nguoi khac soat
-- duoc ma khong phai doc Python.
--
-- Dinh dang: moi cau bat dau bang mot dong  -- @ten: <ten_cau>
-- va keo dai den dong  -- @ten:  tiep theo.
-- Tham so truyen bang ten, dang %(ten)s.
--
-- Rang buoc: chi SELECT, luon co LIMIT.
--
-- Ba cau "chuoi_*" sap xep GIAM dan roi moi cat bang LIMIT, de lay N moc MOI
-- NHAT. Sap tang dan roi cat se lay nham N moc CU NHAT: co tram trong CSDL
-- co so do tu nam 2000, bieu do se dung lai o nam 2020 va khong bao gio thay
-- so lieu hien tai. Phia Python dao lai thu tu cho dung chieu thoi gian.
--
-- ===========================================================================
-- Ghi chep ve schema QTQG, rut ra tu backend/kiem_tra_ket_noi.py
-- ===========================================================================
-- PostgreSQL 9.6.8 + PostGIS. Cac bang lien quan den nuoc MAT:
--
--   surfacewater_station        131 tram, geom EPSG:3405, khoa la "matram"
--   surfacewater_chatluongnuoc  khoa "sohieutram", ngay "ngaylaymau"
--   surfacewater_level          khoa "station_code", ngay "date_measure"
--   surfacewater_flow           khoa "station_code", ngay "date_measure"
--   hydrology_station           385 tram thuy van, chi co vi tri
--
-- Cac bang water_level, water_temperature, water_chemistry la nuoc DUOI DAT
-- (khoa "well_code"), khong dung o day.
--
-- HAI DIEM BAT NGO CUA SCHEMA, da kiem chung:
--
-- 1. surfacewater_chatluongnuoc luu MOI DONG MOT VAI THONG SO, phan con lai
--    de NULL. Mot lan lay mau trai ra nhieu dong cung (sohieutram, ngaylaymau).
--    Vi vay phai GOP bang MAX(...) GROUP BY tram, ngay. Doc tung dong roi le
--    se thay gan het thong so bi khuyet.
--
-- 2. water_level va stake_high tinh bang CENTIMET, tren moc cao do rieng cua
--    tung tram. Hai vi du do thang tu CSDL toan quoc: tram YYH01 dao dong
--    20734 den 21189 cm, tuc 207,3 den 211,9 m; tram AT01 dao dong 210 den
--    972 cm. Do la CAO DO mat nuoc theo moc tram, khong phai do sau. Chia 100
--    de ra met.

-- @ten: danh_sach_tram
-- Tram nuoc mat va tram thuy van nam trong khung bao cua tinh.
-- Chi lay tram CO ma: tram khong co ma thi khong noi duoc voi bang so do.
-- Cot tinh_qtqg duoc tra ve de loc tiep o phia Python: khung bao la hinh chu
-- nhat nen trum ca mot phan Phu Yen, Kon Tum va Dak Lak.
WITH khung AS (
    SELECT ST_MakeEnvelope(%(kd_min)s, %(vd_min)s,
                           %(kd_max)s, %(vd_max)s, 4326) AS g
)
SELECT s.matram                              AS ma,
       s.tentram                             AS ten,
       'Tài nguyên nước mặt'                 AS loai_tram,
       s.tensong                             AS song_ho,
       s.luuvucsong                          AS ten_luu_vuc,
       s.capquanly                           AS don_vi_quan_ly,
       s.thongsoqt                           AS thong_so,
       s.tinh                                AS tinh_qtqg,
       ST_X(ST_Transform(s.geom, 4326))      AS kinh_do,
       ST_Y(ST_Transform(s.geom, 4326))      AS vi_do
FROM public.surfacewater_station s, khung k
WHERE s.matram IS NOT NULL
  AND s.geom IS NOT NULL
  AND ST_Intersects(ST_Transform(s.geom, 4326), k.g)
UNION ALL
SELECT h.matram,
       h.tentram,
       'Thủy văn',
       h.tensong,
       NULL,
       NULL,
       NULL,
       h.tinh,
       ST_X(ST_Transform(h.geom, 4326)),
       ST_Y(ST_Transform(h.geom, 4326))
FROM public.hydrology_station h, khung k
WHERE h.matram IS NOT NULL
  AND h.geom IS NOT NULL
  AND ST_Intersects(ST_Transform(h.geom, 4326), k.g)
ORDER BY ma
LIMIT %(gioi_han)s;

-- @ten: chat_luong_moi_nhat
-- Ky lay mau gan nhat cua moi tram trong danh sach, da gop cac dong roi le.
-- DISTINCT ON lay dong dau tien cua moi tram sau khi sap ngay giam dan.
SELECT DISTINCT ON (sohieutram)
       sohieutram                AS ma,
       ngaylaymau::text          AS thoi_diem,
       MAX(ph)                   AS ph,
       MAX(vdo)                  AS do_mg_l,
       MAX(nhietdo)              AS nhiet_do_c,
       MAX(ec)                   AS ec_us_cm,
       MAX(tss)                  AS tss_mg_l,
       MAX(ntu)                  AS do_duc_ntu,
       MAX(cod)                  AS cod_mg_l,
       MAX(bod)                  AS bod5_mg_l,
       MAX(nh4)                  AS amoni_mg_l,
       MAX(no3)                  AS nitrat_mg_l,
       MAX(no2)                  AS nitrit_mg_l,
       MAX(po4)                  AS photphat_mg_l,
       MAX(coliform)             AS coliform_mpn_100ml,
       MAX(ecoli)                AS ecoli_mpn_100ml,
       MAX(asen)                 AS as_mg_l,
       MAX(cd)                   AS cd_mg_l,
       MAX(pb)                   AS pb_mg_l,
       MAX(cu)                   AS cu_mg_l,
       MAX(zn)                   AS zn_mg_l,
       MAX(hg)                   AS hg_mg_l,
       MAX(aldrin)               AS aldrin_ug_l,
       MAX(bhc)                  AS bhc_ug_l,
       MAX(dieldrin)             AS dieldrin_ug_l,
       MAX(ddt)                  AS ddts_ug_l,
       MAX(heptachlor)           AS heptachlor_ug_l
FROM public.surfacewater_chatluongnuoc
WHERE sohieutram = ANY(%(cac_ma)s)
GROUP BY sohieutram, ngaylaymau
ORDER BY sohieutram, ngaylaymau DESC
LIMIT %(gioi_han)s;

-- @ten: muc_nuoc_moi_nhat
-- So do muc nuoc gan nhat cua moi tram. Doi tu centimet sang met.
SELECT DISTINCT ON (station_code)
       station_code                                   AS ma,
       (date_measure::text || ' ' ||
        LPAD(COALESCE(time_measure, 0)::int::text, 2, '0') || ':00')
                                                      AS thoi_diem,
       water_level / 100.0                            AS h_m
FROM public.surfacewater_level
WHERE station_code = ANY(%(cac_ma)s)
  AND water_level IS NOT NULL
ORDER BY station_code, date_measure DESC, time_measure DESC
LIMIT %(gioi_han)s;

-- @ten: luu_luong_moi_nhat
-- So do luu luong gan nhat cua moi tram.
SELECT DISTINCT ON (station_code)
       station_code             AS ma,
       date_measure::text       AS thoi_diem,
       q_value::double precision AS q_m3s
FROM public.surfacewater_flow
WHERE station_code = ANY(%(cac_ma)s)
  AND q_value IS NOT NULL
ORDER BY station_code, date_measure DESC
LIMIT %(gioi_han)s;

-- @ten: nhiet_do_trung_binh_thang
-- Nhiet do nuoc trung binh nhieu nam theo thang, tinh rieng cho tung tram.
-- Dung de uoc nhiet do cho nhung ky thieu so do, phuc vu quy DO ra phan tram
-- bao hoa. Day la so SUY DIEN, moi ban ghi dung no deu bi danh dau.
SELECT sohieutram                                  AS ma,
       EXTRACT(MONTH FROM ngaylaymau)::int         AS thang,
       AVG(nhietdo)                                AS nhiet_do_c,
       COUNT(nhietdo)                              AS so_lan_do
FROM public.surfacewater_chatluongnuoc
WHERE sohieutram = ANY(%(cac_ma)s)
  AND nhietdo IS NOT NULL
GROUP BY sohieutram, EXTRACT(MONTH FROM ngaylaymau)
LIMIT %(gioi_han)s;

-- @ten: chuoi_chat_luong
-- Chuoi cac ky lay mau cua mot tram, da gop cac dong roi le.
SELECT ngaylaymau::text   AS thoi_diem,
       MAX(ph)            AS ph,
       MAX(vdo)           AS do_mg_l,
       MAX(nhietdo)       AS nhiet_do_c,
       MAX(ec)            AS ec_us_cm,
       MAX(tss)           AS tss_mg_l,
       MAX(ntu)           AS do_duc_ntu,
       MAX(cod)           AS cod_mg_l,
       MAX(bod)           AS bod5_mg_l,
       MAX(nh4)           AS amoni_mg_l,
       MAX(no3)           AS nitrat_mg_l,
       MAX(no2)           AS nitrit_mg_l,
       MAX(po4)           AS photphat_mg_l,
       MAX(coliform)      AS coliform_mpn_100ml,
       MAX(ecoli)         AS ecoli_mpn_100ml,
       MAX(asen)          AS as_mg_l,
       MAX(cd)            AS cd_mg_l,
       MAX(pb)            AS pb_mg_l,
       MAX(cu)            AS cu_mg_l,
       MAX(zn)            AS zn_mg_l,
       MAX(hg)            AS hg_mg_l
FROM public.surfacewater_chatluongnuoc
WHERE sohieutram = %(ma)s
  AND (%(tu)s::date IS NULL OR ngaylaymau >= %(tu)s::date)
  AND (%(den)s::date IS NULL OR ngaylaymau <= %(den)s::date)
GROUP BY ngaylaymau
ORDER BY ngaylaymau DESC
LIMIT %(gioi_han)s;

-- @ten: chuoi_muc_nuoc
-- Chuoi muc nuoc cua mot tram. Lay gia tri trung binh ngay cho gon, vi tram
-- do nhieu lan moi ngay va bieu do khong can den tung gio.
SELECT date_measure::text        AS thoi_diem,
       AVG(water_level) / 100.0  AS h_m
FROM public.surfacewater_level
WHERE station_code = %(ma)s
  AND water_level IS NOT NULL
  AND (%(tu)s::date IS NULL OR date_measure >= %(tu)s::date)
  AND (%(den)s::date IS NULL OR date_measure <= %(den)s::date)
GROUP BY date_measure
ORDER BY date_measure DESC
LIMIT %(gioi_han)s;

-- @ten: chuoi_luu_luong
-- Chuoi luu luong cua mot tram.
SELECT date_measure::text              AS thoi_diem,
       AVG(q_value)::double precision  AS q_m3s
FROM public.surfacewater_flow
WHERE station_code = %(ma)s
  AND q_value IS NOT NULL
  AND (%(tu)s::date IS NULL OR date_measure >= %(tu)s::date)
  AND (%(den)s::date IS NULL OR date_measure <= %(den)s::date)
GROUP BY date_measure
ORDER BY date_measure DESC
LIMIT %(gioi_han)s;

-- ===========================================================================
-- NUOC DUOI DAT
-- ===========================================================================
-- Ghi chep ve schema, kiem chung ngay 26/10/2026:
--
--   monitoring_well     Lo khoan quan trac, loc theo cot "province". Cot
--                       hientrang nhan hai gia tri 'Đang hoạt động' va
--                       'Dừng quan trắc'; cau truy van duoi day CHI lay nhom
--                       dang hoat dong. Khoa la "well_code", geom EPSG:3405.
--                       Nhom dang hoat dong co network_type = 'Quốc gia' va
--                       objective = 'Nước dưới đất'.
--                       So luong cua tinh nay: chay kiem_tra_ket_noi.py.
--   water_level         muc nuoc theo gio, khoa "well_code"
--   water_temperature   nhiet do nuoc, khoa "well_code"
--   water_chemistry     93 cot thanh phan hoa hoc, khoa "well_code"
--
-- BON DIEM KHAC HAN BANG NUOC MAT, da kiem chung:
--
-- 1. water_level cua nuoc duoi dat tinh bang MET va la so AM: -14,45 nghia la
--    mat nuoc nam sau 14,45 m duoi mieng lo khoan. Khong chia 100 nhu
--    surfacewater_level. Vi vay phai dung truong rieng h_ngam_m, khong duoc
--    dung lai h_m cua nuoc mat: hai so cung ten se bi ve chung mot bieu do
--    va chung mot cot bang, trong khi y nghia nguoc nhau.
--
-- 2. elevation la cao do mieng lo khoan (m). Cao do mat nuoc = elevation +
--    water_level. Day la phep cong dung nghia, khong phai suy dien.
--
-- 3. hcp va h_chophep (muc nuoc ha thap cho phep) RONG o ca 65 lo khoan, nen
--    KHONG co nguong nao de dat trang thai canh bao. Khong tu dat nguong.
--
-- 4. Lay dong moi nhat cua tung lo khoan phai dung CROSS JOIN LATERAL. Cach
--    DISTINCT ON quet het bang (65 lo khoan nhan khoang 20 den 32 nghin dong
--    moi cai) mat 8,5 giay, sat nguong statement_timeout 15 giay; LATERAL
--    dung chi muc idx_waterlevel_wellcode nen chi mat 1,9 giay.
--
-- 5. time_measure la chuoi gio le: '0','1','3',...,'23'. Ep sang so de sap
--    xep, neu so sanh dang chuoi thi '9' lai lon hon '23'.
--
-- VN_WQI KHONG AP DUNG CHO NUOC DUOI DAT. Quyet dinh 1460/QD-TCMT chi danh
-- cho nuoc mat luc dia. Ban ghi nuoc duoi dat duoc gan loai = nuoc_duoi_dat
-- va wqi.gan_wqi() bo qua chung, xem chuan_hoa.chuan_hoa_ban_ghi(loai=...).

-- @ten: danh_sach_lo_khoan
-- Lo khoan quan trac quoc gia DANG HOAT DONG trong khung bao cua tinh.
-- Bang khong co cot ten, nen ten tram duoc dung tu ma: "Lỗ khoan <ma>".
-- Cot district rong o ca 65 ban ghi, vi tri hanh chinh lay tu commune.
WITH khung AS (
    SELECT ST_MakeEnvelope(%(kd_min)s, %(vd_min)s,
                           %(kd_max)s, %(vd_max)s, 4326) AS g
)
SELECT w.well_code                            AS ma,
       'Lỗ khoan ' || w.well_code             AS ten,
       'Nước dưới đất'                        AS loai_tram,
       w.water_layer                          AS tang_chua_nuoc,
       w.elevation                            AS cao_do_mieng_lk_m,
       w.luuvuc                               AS ten_luu_vuc,
       w.network_type                         AS mang_quan_trac,
       w.thietbiquantrac                      AS thiet_bi_do,
       w.start_date::text                     AS ngay_bat_dau,
       NULLIF(TRIM(COALESCE(w.commune, '') ||
              CASE WHEN COALESCE(w.district, '') <> ''
                   THEN ', ' || w.district ELSE '' END), '')
                                              AS vi_tri_hc,
       w.province                             AS tinh_qtqg,
       ST_X(ST_Transform(w.geom, 4326))       AS kinh_do,
       ST_Y(ST_Transform(w.geom, 4326))       AS vi_do
FROM public.monitoring_well w, khung k
WHERE w.well_code IS NOT NULL
  AND w.geom IS NOT NULL
  AND w.hientrang = %(hien_trang)s
  AND ST_Intersects(ST_Transform(w.geom, 4326), k.g)
ORDER BY ma
LIMIT %(gioi_han)s;

-- @ten: muc_nuoc_ngam_moi_nhat
-- So do muc nuoc gan nhat cua tung lo khoan. Xem ghi chep 1, 2, 4 va 5.
SELECT g.ma,
       (l.date_measure::text || ' ' ||
        LPAD(l.gio::text, 2, '0') || ':00')   AS thoi_diem,
       l.water_level                          AS h_ngam_m,
       l.cao_do_mn                            AS cao_do_mn_m
FROM unnest(%(cac_ma)s::text[]) AS g(ma)
CROSS JOIN LATERAL (
    SELECT x.date_measure,
           COALESCE(NULLIF(regexp_replace(
               COALESCE(x.time_measure, ''), '[^0-9]', '', 'g'), ''),
               '0')::int                      AS gio,
           x.water_level,
           w.elevation + x.water_level        AS cao_do_mn
    FROM public.water_level x
    JOIN public.monitoring_well w ON w.well_code = x.well_code
    WHERE x.well_code = g.ma
      AND x.water_level IS NOT NULL
    ORDER BY x.date_measure DESC, 2 DESC
    LIMIT 1
) l
LIMIT %(gioi_han)s;

-- @ten: nhiet_do_ngam_moi_nhat
-- Nhiet do nuoc gan nhat cua tung lo khoan. Day la so DO that, khong phai so
-- uoc nhu _bu_nhiet_do() cua nuoc mat.
--
-- water_temperature co 24,6 trieu dong va khong co chi muc ghep
-- (well_code, date_measure), nen o day KHONG dung CROSS JOIN LATERAL nhu bang
-- muc nuoc: cach do mat 7,9 giay. Loc truoc theo cua so ngay rong de
-- PostgreSQL dung idx_watertemperature_datemeasure thi chi mat 1,7 giay.
--
-- Cua so nay co the bo sot lo khoan lau khong do nhiet do, nen moi co cau
-- nhiet_do_ngam_bu ngay duoi: phia Python goi cau do cho dung nhung lo khoan
-- con thieu. Binh thuong khong lo khoan nao thieu nen cau do khong chay.
SELECT DISTINCT ON (well_code)
       well_code                              AS ma,
       date_measure::text                     AS thoi_diem,
       temperature                            AS nhiet_do_c
FROM public.water_temperature
WHERE well_code = ANY(%(cac_ma)s)
  AND temperature IS NOT NULL
  AND date_measure >= (CURRENT_DATE - %(so_ngay)s::int)
ORDER BY well_code, date_measure DESC
LIMIT %(gioi_han)s;

-- @ten: nhiet_do_ngam_bu
-- Nhiet do gan nhat, KHONG gioi han cua so ngay, danh cho so lo khoan it oi
-- ma cau tren khong tim thay. Chi goi voi danh sach ma ngan.
SELECT g.ma,
       t.date_measure::text                   AS thoi_diem,
       t.temperature                          AS nhiet_do_c
FROM unnest(%(cac_ma)s::text[]) AS g(ma)
CROSS JOIN LATERAL (
    SELECT x.date_measure, x.temperature
    FROM public.water_temperature x
    WHERE x.well_code = g.ma
      AND x.temperature IS NOT NULL
    ORDER BY x.date_measure DESC
    LIMIT 1
) t
LIMIT %(gioi_han)s;

-- @ten: chat_luong_ngam_moi_nhat
-- Ky lay mau gan nhat cua tung lo khoan.
--
-- Khac bang nuoc mat: mot ky lay mau o day la MOT dong, khong trai ra nhieu
-- dong, nen khong phai gop bang MAX().
--
-- tds_total chi co o 65 trong 6301 dong con tds105 co o 2654 dong: hai cot do
-- cung mot thong so (tong chat ran hoa tan, mg/L) nhung duoc nhap vao hai
-- thoi ky khac nhau, nen lay cai nao co.
--
-- Sat: cot fe_total gan nhu rong (65 dong), con fe2 va fe3 co o hon mot nua.
-- KHONG cong fe2 voi fe3 de ra sat tong: do la suy dien. Tra ve ca ba cot,
-- giao dien chi ve cot nao co so.
--
-- cr la crom TONG, khong phai Cr(VI), nen khong anh xa vao cr6_mg_l.
SELECT DISTINCT ON (well_code)
       well_code                   AS ma,
       date_sampling::text         AS thoi_diem,
       ph                          AS ph,
       permanganat                 AS permanganat_mg_l,
       COALESCE(tds_total, tds105) AS tds_mg_l,
       hardness_general            AS do_cung_mg_l,
       nh4                         AS amoni_mg_l,
       no3                         AS nitrat_mg_l,
       no2                         AS nitrit_mg_l,
       po4                         AS photphat_mg_l,
       cl                          AS clorua_mg_l,
       so4                         AS sunfat_mg_l,
       f                           AS florua_mg_l,
       cn                          AS xyanua_mg_l,
       fe_total                    AS fe_mg_l,
       fe2                         AS fe2_mg_l,
       fe3                         AS fe3_mg_l,
       mn                          AS mn_mg_l,
       as_                         AS as_mg_l,
       cd                          AS cd_mg_l,
       pb                          AS pb_mg_l,
       cr                          AS cr_mg_l,
       cu                          AS cu_mg_l,
       zn                          AS zn_mg_l,
       hg                          AS hg_mg_l,
       se                          AS se_mg_l,
       phenol                      AS phenol_mg_l,
       coliform                    AS coliform_mpn_100ml,
       ecoli                       AS ecoli_mpn_100ml,
       conductivity                AS ec_us_cm,
       oxygen_dissolve             AS do_mg_l,
       water_temperature           AS nhiet_do_c
FROM public.water_chemistry
WHERE well_code = ANY(%(cac_ma)s)
ORDER BY well_code, date_sampling DESC
LIMIT %(gioi_han)s;

-- @ten: chuoi_muc_nuoc_ngam
-- Chuoi muc nuoc cua mot lo khoan, trung binh theo ngay cho gon: lo khoan do
-- 12 lan moi ngay va bieu do khong can den tung gio.
-- Tra ve ca cao do mat nuoc, de bieu do ve duoc ca hai cach nhin: do sau so
-- voi mieng lo khoan va cao do tuyet doi so voi mat bien.
--
-- Cao do mieng lo khoan la hang so cua tung lo khoan nen duoc cong vao SAU
-- khi lay trung binh ngay: ket qua giong het nhu cong vao tung so do roi moi
-- trung binh, nhung khong phai JOIN sang monitoring_well cho tung dong.
SELECT date_measure::text        AS thoi_diem,
       AVG(water_level)          AS h_ngam_m,
       AVG(water_level) + (SELECT MIN(elevation)
                           FROM public.monitoring_well
                           WHERE well_code = %(ma)s)
                                 AS cao_do_mn_m
FROM public.water_level
WHERE well_code = %(ma)s
  AND water_level IS NOT NULL
  AND (%(tu)s::date IS NULL OR date_measure >= %(tu)s::date)
  AND (%(den)s::date IS NULL OR date_measure <= %(den)s::date)
GROUP BY date_measure
ORDER BY date_measure DESC
LIMIT %(gioi_han)s;

-- @ten: chuoi_nhiet_do_ngam
SELECT date_measure::text        AS thoi_diem,
       AVG(temperature)          AS nhiet_do_c
FROM public.water_temperature
WHERE well_code = %(ma)s
  AND temperature IS NOT NULL
  AND (%(tu)s::date IS NULL OR date_measure >= %(tu)s::date)
  AND (%(den)s::date IS NULL OR date_measure <= %(den)s::date)
GROUP BY date_measure
ORDER BY date_measure DESC
LIMIT %(gioi_han)s;

-- @ten: chuoi_chat_luong_ngam
-- Chuoi cac ky lay mau cua mot lo khoan. Cung bo cot voi
-- chat_luong_ngam_moi_nhat de phia Python doc duoc bang mot duong ma.
SELECT date_sampling::text         AS thoi_diem,
       ph                          AS ph,
       permanganat                 AS permanganat_mg_l,
       COALESCE(tds_total, tds105) AS tds_mg_l,
       hardness_general            AS do_cung_mg_l,
       nh4                         AS amoni_mg_l,
       no3                         AS nitrat_mg_l,
       no2                         AS nitrit_mg_l,
       po4                         AS photphat_mg_l,
       cl                          AS clorua_mg_l,
       so4                         AS sunfat_mg_l,
       f                           AS florua_mg_l,
       cn                          AS xyanua_mg_l,
       fe_total                    AS fe_mg_l,
       fe2                         AS fe2_mg_l,
       fe3                         AS fe3_mg_l,
       mn                          AS mn_mg_l,
       as_                         AS as_mg_l,
       cd                          AS cd_mg_l,
       pb                          AS pb_mg_l,
       cr                          AS cr_mg_l,
       cu                          AS cu_mg_l,
       zn                          AS zn_mg_l,
       hg                          AS hg_mg_l,
       se                          AS se_mg_l,
       phenol                      AS phenol_mg_l,
       coliform                    AS coliform_mpn_100ml,
       ecoli                       AS ecoli_mpn_100ml,
       conductivity                AS ec_us_cm,
       oxygen_dissolve             AS do_mg_l,
       water_temperature           AS nhiet_do_c
FROM public.water_chemistry
WHERE well_code = %(ma)s
  AND (%(tu)s::date IS NULL OR date_sampling >= %(tu)s::date)
  AND (%(den)s::date IS NULL OR date_sampling <= %(den)s::date)
ORDER BY date_sampling DESC
LIMIT %(gioi_han)s;
