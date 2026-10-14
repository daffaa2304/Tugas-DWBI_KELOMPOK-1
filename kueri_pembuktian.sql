-- ====================================================================
-- EMPAT KUERI PEMBUKTIAN (PROOF QUERIES) DATA WAREHOUSE NRG
-- Mata Kuliah: Data Warehouse / Business Intelligence - Tugas 1
-- Studi Kasus: Nusantara Retail Group (NRG)
-- Database Target: nrg_dw (MySQL)
-- ====================================================================

USE nrg_dw;

-- ====================================================================
-- KUERI 1: ANALISIS MARGIN KOTOR PER SUB-KATEGORI PRODUK PER KANAL (YoY)
-- Rumusan Masalah:
-- "Berapa margin kotor per sub-kategori produk per kanal, dibandingkan 
--  dengan kuartal yang sama pada tahun lalu?"
-- ====================================================================

WITH qtr_margin AS (
    SELECT 
        p.sub_kategori,
        f.kanal,
        w.tahun,
        w.kuartal,
        w.kuartal_nama,
        ROUND(SUM(f.margin_kotor), 2) AS margin_kotor
    FROM fact_penjualan f
    JOIN dim_produk p ON f.sk_produk = p.sk_produk
    JOIN dim_waktu w ON f.sk_waktu = w.sk_waktu
    GROUP BY p.sub_kategori, f.kanal, w.tahun, w.kuartal, w.kuartal_nama
),
yoy_comparison AS (
    SELECT 
        sub_kategori,
        kanal,
        tahun,
        kuartal,
        kuartal_nama,
        margin_kotor,
        LAG(margin_kotor, 1) OVER (
            PARTITION BY sub_kategori, kanal, kuartal 
            ORDER BY tahun
        ) AS margin_kotor_ly
    FROM qtr_margin
)
SELECT 
    sub_kategori,
    kanal,
    kuartal_nama,
    margin_kotor AS margin_kotor_current,
    margin_kotor_ly AS margin_kotor_same_quarter_last_year,
    ROUND(margin_kotor - margin_kotor_ly, 2) AS selisih_nominal,
    ROUND(((margin_kotor - margin_kotor_ly) / NULLIF(margin_kotor_ly, 0)) * 100, 2) AS pertumbuhan_yoy_pct
FROM yoy_comparison
WHERE margin_kotor_ly IS NOT NULL
ORDER BY sub_kategori, kanal, tahun, kuartal;


-- ====================================================================
-- KUERI 2: IDENTIFIKASI PELANGGAN ONLINE VS. PEMEGANG KARTU MEMBER TOKO
-- Rumusan Masalah:
-- "Apakah pelanggan yang berbelanja secara online adalah orang yang 
--  sama dengan pemegang kartu member di toko fisik?"
-- Penjelasan:
-- Dilakukan pemadanan nomor HP yang dinormalkan antara pelanggan E-Commerce (S1)
-- dan Member Toko Fisik (S2), ditandai dengan flag is_omnichannel = 1 pada dim_pelanggan.
-- ====================================================================

-- 2A. Ringkasan Perilaku Belanja: Pelanggan Online yang merupakan Member Toko vs Non-Member
SELECT 
    CASE 
        WHEN p.is_omnichannel = 1 THEN 'Pelanggan Online Sekaligus Member Toko Fisik'
        ELSE 'Pelanggan Online Murni (Bukan Member Toko)'
    END AS segmen_pelanggan_online,
    COUNT(DISTINCT p.sk_pelanggan) AS jumlah_pelanggan_unik,
    COUNT(DISTINCT f.no_transaksi) AS total_transaksi_web,
    SUM(f.qty) AS total_unit_terjual,
    ROUND(SUM(f.nilai_bersih_excl), 2) AS total_penjualan_bersih_idr,
    ROUND(SUM(f.nilai_bersih_excl) / COUNT(DISTINCT f.no_transaksi), 2) AS rata_rata_belanja_per_transaksi,
    ROUND(SUM(f.margin_kotor), 2) AS total_margin_kotor_idr
FROM fact_penjualan f
JOIN dim_pelanggan p ON f.sk_pelanggan = p.sk_pelanggan
WHERE f.kanal = 'WEB'
GROUP BY p.is_omnichannel;

-- 2B. Bukti Detail Sampel Profil Pelanggan yang Teridentifikasi Berbelanja Lintas Kanal
SELECT 
    p.sk_pelanggan,
    p.nama_pelanggan,
    p.no_hp_normal,
    p.status_member,
    COUNT(DISTINCT CASE WHEN f.kanal = 'WEB' THEN f.no_transaksi END) AS trx_di_web,
    COUNT(DISTINCT CASE WHEN f.kanal = 'TOKO_FISIK' THEN f.no_transaksi END) AS trx_di_toko_fisik,
    ROUND(SUM(CASE WHEN f.kanal = 'WEB' THEN f.nilai_bersih_excl ELSE 0 END), 2) AS total_belanja_web,
    ROUND(SUM(f.nilai_bersih_excl), 2) AS total_belanja_gabungan
FROM fact_penjualan f
JOIN dim_pelanggan p ON f.sk_pelanggan = p.sk_pelanggan
WHERE p.is_omnichannel = 1
GROUP BY p.sk_pelanggan, p.nama_pelanggan, p.no_hp_normal, p.status_member
ORDER BY total_belanja_gabungan DESC
LIMIT 10;


-- ====================================================================
-- KUERI 3: EFEKTIVITAS KAMPANYE DISKON (VOLUME VS MARGIN EROSION)
-- Rumusan Masalah:
-- "Kampanye diskon mana yang berhasil menaikkan volume penjualan tanpa 
--  menggerus margin?"
-- Penjelasan:
-- Membandingkan volume unit terjual dan persentase margin kotor terhadap
-- nilai penjualan bersih antar program promosi.
-- ====================================================================

SELECT 
    pr.kode_promo,
    pr.nama_kampanye,
    pr.jenis_promo,
    pr.target_diskon_persen,
    COUNT(DISTINCT f.no_transaksi) AS jumlah_transaksi,
    SUM(f.qty) AS total_unit_terjual,
    ROUND(SUM(f.nilai_bersih_excl), 2) AS total_penjualan_bersih,
    ROUND(SUM(f.nilai_diskon_excl), 2) AS total_potongan_diskon,
    ROUND(SUM(f.margin_kotor), 2) AS total_margin_kotor,
    ROUND((SUM(f.margin_kotor) / NULLIF(SUM(f.nilai_bersih_excl), 0)) * 100, 2) AS margin_persen,
    CASE 
        WHEN (SUM(f.margin_kotor) / NULLIF(SUM(f.nilai_bersih_excl), 0)) * 100 >= 18.00 
             AND SUM(f.qty) >= 150 
             THEN 'Sangat Efektif (Volume Tinggi & Margin Terjaga Sehat)'
        WHEN (SUM(f.margin_kotor) / NULLIF(SUM(f.nilai_bersih_excl), 0)) * 100 < 15.00 
             THEN 'Margin Tergerus Signifikan (Perlu Evaluasi Tingkat Diskon)'
        ELSE 'Moderat'
    END AS evaluasi_kinerja_promosi
FROM fact_penjualan f
JOIN dim_promosi pr ON f.sk_promosi = pr.sk_promosi
GROUP BY pr.kode_promo, pr.nama_kampanye, pr.jenis_promo, pr.target_diskon_persen
ORDER BY total_unit_terjual DESC;


-- ====================================================================
-- KUERI 4: PRODUK KANDIDAT PEMINDAHAN ALOKASI STOK KE MARKETPLACE
-- Rumusan Masalah:
-- "Produk apa saja yang volume penjualannya tinggi di marketplace tetapi 
--  rendah di toko fisik dan web, sehingga menjadi kandidat pemindahan 
--  alokasi stok ke marketplace?"
-- ====================================================================

WITH prod_sales AS (
    SELECT 
        p.material_no,
        p.nama_produk,
        p.kategori,
        p.sub_kategori,
        SUM(CASE WHEN f.kanal = 'MARKETPLACE' THEN f.qty ELSE 0 END) AS qty_marketplace,
        SUM(CASE WHEN f.kanal = 'TOKO_FISIK' THEN f.qty ELSE 0 END) AS qty_toko_fisik,
        SUM(CASE WHEN f.kanal = 'WEB' THEN f.qty ELSE 0 END) AS qty_web,
        SUM(f.qty) AS total_qty_semua_kanal,
        ROUND(SUM(CASE WHEN f.kanal = 'MARKETPLACE' THEN f.margin_kotor ELSE 0 END), 2) AS margin_marketplace
    FROM fact_penjualan f
    JOIN dim_produk p ON f.sk_produk = p.sk_produk
    GROUP BY p.material_no, p.nama_produk, p.kategori, p.sub_kategori
)
SELECT 
    material_no,
    nama_produk,
    kategori,
    sub_kategori,
    qty_marketplace,
    qty_toko_fisik,
    qty_web,
    total_qty_semua_kanal,
    ROUND((qty_marketplace / NULLIF(total_qty_semua_kanal, 0)) * 100, 2) AS pangsa_pasar_marketplace_pct,
    ROUND((qty_marketplace / NULLIF(qty_toko_fisik + qty_web, 0)), 2) AS rasio_mpl_vs_offline_web,
    margin_marketplace AS total_margin_di_marketplace
FROM prod_sales
ORDER BY pangsa_pasar_marketplace_pct DESC, qty_marketplace DESC
LIMIT 10;
