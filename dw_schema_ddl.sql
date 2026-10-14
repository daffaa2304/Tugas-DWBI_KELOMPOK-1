-- ====================================================================
-- DDL DATA WAREHOUSE NUSANTARA RETAIL GROUP (NRG)
-- Database: nrg_dw
-- Mata Kuliah: Data Warehouse / Business Intelligence - Tugas 1
-- Skema: Star Schema (1 Tabel Fakta Penjualan & 5 Tabel Dimensi)
-- ====================================================================

CREATE DATABASE IF NOT EXISTS nrg_dw;
USE nrg_dw;

-- Matikan foreign key checks sementara untuk reset skema jika diperlukan
SET FOREIGN_KEY_CHECKS = 0;

DROP TABLE IF EXISTS fact_penjualan;
DROP TABLE IF EXISTS dim_promosi;
DROP TABLE IF EXISTS dim_pelanggan;
DROP TABLE IF EXISTS dim_toko_kanal;
DROP TABLE IF EXISTS dim_produk;
DROP TABLE IF EXISTS dim_waktu;
DROP TABLE IF EXISTS error_kampanye_marketing;

SET FOREIGN_KEY_CHECKS = 1;

-- --------------------------------------------------------------------
-- 1. DIM_WAKTU
-- --------------------------------------------------------------------
CREATE TABLE dim_waktu (
    sk_waktu INT NOT NULL PRIMARY KEY COMMENT 'Format integer YYYYMMDD',
    tanggal DATE NOT NULL UNIQUE,
    tahun INT NOT NULL,
    kuartal INT NOT NULL,
    kuartal_nama VARCHAR(10) NOT NULL COMMENT 'Contoh: Q1 2022',
    bulan INT NOT NULL,
    nama_bulan VARCHAR(20) NOT NULL,
    hari INT NOT NULL,
    nama_hari VARCHAR(15) NOT NULL,
    is_weekend TINYINT(1) NOT NULL DEFAULT 0,
    INDEX idx_waktu_tahun_kuartal (tahun, kuartal)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- --------------------------------------------------------------------
-- 2. DIM_PRODUK
-- --------------------------------------------------------------------
CREATE TABLE dim_produk (
    sk_produk INT AUTO_INCREMENT PRIMARY KEY,
    material_no VARCHAR(50) NOT NULL UNIQUE COMMENT 'Rujukan tunggal master ERP (P-XXXX)',
    nama_produk VARCHAR(255) NOT NULL,
    brand VARCHAR(100) NOT NULL,
    kategori VARCHAR(100) NOT NULL,
    sub_kategori VARCHAR(100) NOT NULL,
    harga_pokok_terkini DECIMAL(15,2) NOT NULL DEFAULT 0.00,
    supplier VARCHAR(150) NOT NULL DEFAULT '-',
    status_erp VARCHAR(50) NOT NULL DEFAULT 'AKTIF',
    INDEX idx_prod_kategori (kategori, sub_kategori)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- --------------------------------------------------------------------
-- 3. DIM_TOKO_KANAL
-- --------------------------------------------------------------------
CREATE TABLE dim_toko_kanal (
    sk_toko_kanal INT AUTO_INCREMENT PRIMARY KEY,
    kode_toko_kanal VARCHAR(50) NOT NULL UNIQUE COMMENT 'Kode toko (TS01-TS42) atau kanal (WEB, MARKETPLACE_A, MARKETPLACE_B)',
    nama_toko_kanal VARCHAR(150) NOT NULL,
    jenis_kanal VARCHAR(50) NOT NULL COMMENT 'TOKO_FISIK, WEB, MARKETPLACE',
    kota VARCHAR(100) NOT NULL,
    provinsi VARCHAR(100) NOT NULL,
    format_toko VARCHAR(50) NOT NULL DEFAULT '-',
    INDEX idx_toko_kanal (jenis_kanal, kota)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- --------------------------------------------------------------------
-- 4. DIM_PELANGGAN
-- --------------------------------------------------------------------
CREATE TABLE dim_pelanggan (
    sk_pelanggan INT AUTO_INCREMENT PRIMARY KEY,
    no_identitas_asal VARCHAR(100) NOT NULL COMMENT 'ID pelanggan ecom / member / buyer hash',
    nama_pelanggan VARCHAR(150) NOT NULL,
    no_hp_normal VARCHAR(50) NOT NULL DEFAULT '-' COMMENT 'Nomor HP ternormalisasi tanpa awalan 0/62/+62',
    status_member VARCHAR(50) NOT NULL COMMENT 'MEMBER_TOKO, NON_MEMBER_WEB, MEMBER_DAN_WEB, BUYER_MARKETPLACE',
    kota VARCHAR(100) NOT NULL DEFAULT '-',
    jenis_kelamin VARCHAR(20) NOT NULL DEFAULT 'TIDAK_DIKETAHUI',
    is_omnichannel TINYINT(1) NOT NULL DEFAULT 0 COMMENT '1 jika teridentifikasi berbelanja di online sekaligus member toko',
    INDEX idx_pelanggan_hp (no_hp_normal),
    INDEX idx_pelanggan_omni (is_omnichannel)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- --------------------------------------------------------------------
-- 5. DIM_PROMOSI
-- --------------------------------------------------------------------
CREATE TABLE dim_promosi (
    sk_promosi INT AUTO_INCREMENT PRIMARY KEY,
    kode_promo VARCHAR(50) NOT NULL UNIQUE,
    nama_kampanye VARCHAR(150) NOT NULL,
    jenis_promo VARCHAR(50) NOT NULL,
    kanal_target VARCHAR(50) NOT NULL,
    target_diskon_persen DECIMAL(5,2) NOT NULL DEFAULT 0.00,
    pic VARCHAR(50) NOT NULL DEFAULT '-',
    INDEX idx_promo_kode (kode_promo)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- --------------------------------------------------------------------
-- 6. FACT_PENJUALAN (1 Tabel Fakta Penjualan Terintegrasi)
-- Grain: 1 baris per item transaksi (order line / trx line / invoice item)
-- --------------------------------------------------------------------
CREATE TABLE fact_penjualan (
    sk_penjualan BIGINT AUTO_INCREMENT PRIMARY KEY,
    sk_waktu INT NOT NULL,
    sk_produk INT NOT NULL,
    sk_toko_kanal INT NOT NULL,
    sk_pelanggan INT NOT NULL,
    sk_promosi INT NOT NULL,
    no_transaksi VARCHAR(100) NOT NULL COMMENT 'Degenerate dimension: order_id, trx_no, atau invoice',
    line_no INT NOT NULL,
    kanal VARCHAR(50) NOT NULL COMMENT 'WEB, TOKO_FISIK, MARKETPLACE',
    qty INT NOT NULL,
    harga_satuan_excl DECIMAL(15,2) NOT NULL COMMENT 'Harga satuan non-PPN',
    nilai_kotor_excl DECIMAL(15,2) NOT NULL COMMENT 'qty * harga_satuan_excl',
    nilai_diskon_excl DECIMAL(15,2) NOT NULL COMMENT 'Nilai potongan harga non-PPN',
    nilai_bersih_excl DECIMAL(15,2) NOT NULL COMMENT 'nilai_kotor_excl - nilai_diskon_excl',
    harga_pokok_satuan DECIMAL(15,2) NOT NULL COMMENT 'HPP dari S4 berlaku saat tanggal transaksi',
    total_harga_pokok DECIMAL(15,2) NOT NULL COMMENT 'qty * harga_pokok_satuan',
    fee_komisi DECIMAL(15,2) NOT NULL DEFAULT 0.00 COMMENT 'Fee marketplace teralokasi proporsional (0 untuk web & toko)',
    margin_kotor DECIMAL(15,2) NOT NULL COMMENT 'nilai_bersih_excl - total_harga_pokok - fee_komisi',
    
    CONSTRAINT fk_fact_waktu FOREIGN KEY (sk_waktu) REFERENCES dim_waktu(sk_waktu),
    CONSTRAINT fk_fact_produk FOREIGN KEY (sk_produk) REFERENCES dim_produk(sk_produk),
    CONSTRAINT fk_fact_toko FOREIGN KEY (sk_toko_kanal) REFERENCES dim_toko_kanal(sk_toko_kanal),
    CONSTRAINT fk_fact_pelanggan FOREIGN KEY (sk_pelanggan) REFERENCES dim_pelanggan(sk_pelanggan),
    CONSTRAINT fk_fact_promosi FOREIGN KEY (sk_promosi) REFERENCES dim_promosi(sk_promosi),
    
    INDEX idx_fact_waktu (sk_waktu),
    INDEX idx_fact_produk (sk_produk),
    INDEX idx_fact_toko (sk_toko_kanal),
    INDEX idx_fact_pelanggan (sk_pelanggan),
    INDEX idx_fact_promosi (sk_promosi),
    INDEX idx_fact_kanal (kanal),
    INDEX idx_fact_trx (no_transaksi)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- --------------------------------------------------------------------
-- 7. ERROR_KAMPANYE_MARKETING (Pencatatan Baris Gagal Validasi S5)
-- --------------------------------------------------------------------
CREATE TABLE error_kampanye_marketing (
    error_id INT AUTO_INCREMENT PRIMARY KEY,
    kode_promo VARCHAR(100),
    nama_kampanye VARCHAR(150),
    jenis_promo VARCHAR(50),
    kanal VARCHAR(50),
    tgl_mulai VARCHAR(50),
    tgl_selesai VARCHAR(50),
    target_diskon_persen VARCHAR(50),
    pic VARCHAR(50),
    alasan_error VARCHAR(255),
    logged_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
