# -*- coding: utf-8 -*-
"""
create_reports.py
Generator Lengkap:
1. Laporan_Desain_Dimensional_NRG.md
2. Laporan_Desain_Dimensional_NRG.docx
3. README.md
"""

import os
import sys
import docx
from docx.shared import Inches, Pt, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.table import WD_TABLE_ALIGNMENT
from docx.oxml import OxmlElement, parse_xml
from docx.oxml.ns import nsdecls, qn

OUTPUT_DIR = os.path.dirname(os.path.abspath(__file__))

# Data untuk tabel-tabel laporan
DATA_SUMBER = [
    ["S1", "ECOM_DB", "Kanal Web Resmi", "MySQL OLTP (Dump SQL & CSV)", "12 file (orders, order_items, customers, vouchers, dll.)"],
    ["S2", "POS_TOKO", "42 Toko Fisik", "CSV per Toko (delimiter ';')", "130 file (trx_header, trx_line, member, store_master, dll.)"],
    ["S3", "MPL_API", "Marketplace A & B", "JSON Berpaginasi (REST API)", "16 file JSON bersarang (invoices, items, fees)"],
    ["S4", "ERP_MASTER", "Master Data Pusat", "CSV Ekstrak Mingguan", "produk_master.csv (SCD Type 2), supplier_master.csv"],
    ["S5", "MKT_SHEET", "Kampanye Pemasaran", "CSV Manual Tim Marketing", "kampanye_marketing.csv (data kotor & anomali non-numerik)"],
    ["REF", "REF_KOTA", "Standarisasi Geografi", "CSV Tabel Referensi", "ref_kota.csv (pemetaan alias kota kasir ke kota baku)"]
]

DATA_SCHEMA = [
    ["dim_waktu", "Tabel Dimensi", "sk_waktu (INT, YYYYMMDD)", "1.096", "Kalender harian 2022-2024 (tahun, kuartal, bulan, hari, nama hari)"],
    ["dim_produk", "Tabel Dimensi", "sk_produk (INT AUTO_INC)", "61", "Master produk unifikasi S1-S4, brand, kategori, COGS terkini, late-arriving"],
    ["dim_toko_kanal", "Tabel Dimensi", "sk_toko_kanal (INT AUTO_INC)", "45", "42 Toko fisik + 3 Kanal Online (WEB, MARKETPLACE_A, MARKETPLACE_B)"],
    ["dim_pelanggan", "Tabel Dimensi", "sk_pelanggan (INT AUTO_INC)", "2.345", "Resolusi profil pelanggan online, member POS, & pembeli marketplace"],
    ["dim_promosi", "Tabel Dimensi", "sk_promosi (INT AUTO_INC)", "11", "Master promosi/voucher aktif bersih setelah pembersihan anomali"],
    ["fact_penjualan", "Tabel Fakta", "fact_id (BIGINT AUTO_INC)", "14.723", "Fakta penjualan terpadu lintas kanal pada grain item transaksi"],
    ["error_kampanye_marketing", "Tabel Audit Error", "error_id (INT AUTO_INC)", "1", "Pencatatan data kampanye gagal validasi ('sepuluh') untuk audit tim marketing"]
]

DATA_STTM = [
    ["dim_waktu", "sk_waktu", "INT (PK)", "S1, S2, S3", "order_ts, trx_date, paid_at", "Integer YYYYMMDD (WIB)"],
    ["dim_waktu", "tanggal", "DATE", "S1, S2, S3", "order_ts, trx_date, paid_at", "Ekstraksi tanggal YYYY-MM-DD (WIB)"],
    ["dim_waktu", "tahun", "INT", "S1, S2, S3", "-", "Tahun kalender (2022-2024)"],
    ["dim_waktu", "kuartal", "INT", "S1, S2, S3", "-", "Kuartal 1 s.d. 4"],
    ["dim_waktu", "kuartal_nama", "VARCHAR(10)", "S1, S2, S3", "-", "'Q1 2023', 'Q2 2023', dst."],
    ["dim_produk", "sk_produk", "INT (PK)", "S4, S1", "produk_master.csv", "Surrogate Key bertambah otomatis"],
    ["dim_produk", "material_no", "VARCHAR(50)", "S4, S1, S2, S3", "material_no, sku, barcode", "Unifikasi kode master; inferensi P-1061 untuk ORD-9999"],
    ["dim_produk", "nama_produk", "VARCHAR(150)", "S4", "nama_material", "Nama resmi produk ERP pusat"],
    ["dim_produk", "kategori", "VARCHAR(50)", "S4", "kategori", "Kategori utama (Elektronik, Furnitur, Pakaian)"],
    ["dim_produk", "sub_kategori", "VARCHAR(50)", "S4", "sub_kategori", "Sub-kategori produk"],
    ["dim_produk", "harga_pokok_terkini", "DECIMAL(15,2)", "S4", "harga_pokok", "Harga pokok terakhir dari produk_master.csv"],
    ["dim_toko_kanal", "sk_toko_kanal", "INT (PK)", "S2, Injected", "store_master.csv", "Surrogate Key (1..42 Toko, 43..45 Kanal Online)"],
    ["dim_toko_kanal", "kode_toko_kanal", "VARCHAR(50)", "S2, Injected", "store_code", "'TS01'..'TS42', 'WEB', 'MARKETPLACE_A', 'MARKETPLACE_B'"],
    ["dim_toko_kanal", "nama_toko_kanal", "VARCHAR(100)", "S2, Injected", "store_name", "Nama toko fisik atau nama kanal online"],
    ["dim_toko_kanal", "jenis_kanal", "VARCHAR(30)", "S2, Injected", "-", "'TOKO_FISIK', 'WEB', 'MARKETPLACE'"],
    ["dim_toko_kanal", "kota_baku", "VARCHAR(100)", "S2, ref_kota", "city + ref_kota.csv", "Standarisasi kota via pemetaan alias ke kota baku"],
    ["dim_pelanggan", "sk_pelanggan", "INT (PK)", "S1, S2, S3", "-", "Surrogate Key pelanggan terpadu"],
    ["dim_pelanggan", "no_identitas_asal", "VARCHAR(100)", "S1, S2, S3", "customer_id, member_no, hash", "CUST-X, M-XXXX, BUYER-hash, gabungan CUST-X|M-XXXX"],
    ["dim_pelanggan", "no_hp_normal", "VARCHAR(30)", "S1, S2", "phone, hp", "Normalisasi nomor telepon (hapus simbol & leading 0/62)"],
    ["dim_pelanggan", "status_member", "VARCHAR(50)", "S1, S2, S3", "-", "'MEMBER_DAN_WEB', 'NON_MEMBER_WEB', 'MEMBER_TOKO', dll."],
    ["dim_pelanggan", "is_omnichannel", "TINYINT(1)", "S1, S2", "phone vs hp matching", "1 jika nomor HP web cocok dengan member toko, else 0"],
    ["dim_promosi", "sk_promosi", "INT (PK)", "S5, Injected", "kampanye_marketing.csv", "Surrogate Key promosi"],
    ["dim_promosi", "kode_promo", "VARCHAR(50)", "S5", "kode_promo", "Uppercase, spasi ditrim; fallback 'NO_PROMO'"],
    ["dim_promosi", "target_diskon_persen", "DECIMAL(5,2)", "S5", "target_diskon_persen", "Nilai numerik; jika 'sepuluh' dialirkan ke error table"],
    ["fact_penjualan", "fact_id", "BIGINT (PK)", "S1, S2, S3", "-", "Surrogate Key baris transaksi fakta"],
    ["fact_penjualan", "sk_waktu", "INT (FK)", "S1, S2, S3", "order_ts, trx_date, paid_at", "Lookup ke dim_waktu (YYYYMMDD)"],
    ["fact_penjualan", "sk_produk", "INT (FK)", "S1, S2, S3, S4", "sku, barcode, seller_sku", "Lookup ke dim_produk via material_no unifikasi"],
    ["fact_penjualan", "sk_toko_kanal", "INT (FK)", "S1, S2, S3", "store_code, channel", "Lookup ke dim_toko_kanal"],
    ["fact_penjualan", "sk_pelanggan", "INT (FK)", "S1, S2, S3", "customer_id, member_no, hash", "Lookup ke dim_pelanggan"],
    ["fact_penjualan", "sk_promosi", "INT (FK)", "S1, S2, S3, S5", "promo_code, voucher_id", "Lookup ke dim_promosi (default 1: NO_PROMO)"],
    ["fact_penjualan", "no_transaksi", "VARCHAR(100)", "S1, S2, S3", "order_id, trx_no, invoice_no", "Nomor transaksi unik asal"],
    ["fact_penjualan", "line_no", "INT", "S1, S2, S3", "line_no, line_id, item_index", "Nomor urut item dalam transaksi"],
    ["fact_penjualan", "kanal", "VARCHAR(30)", "S1, S2, S3", "-", "'WEB', 'TOKO_FISIK', 'MARKETPLACE'"],
    ["fact_penjualan", "qty", "INT", "S1, S2, S3", "qty, quantity", "Jumlah kuantitas barang terjual"],
    ["fact_penjualan", "harga_satuan_excl", "DECIMAL(15,2)", "S1, S2, S3", "unit_price, price", "Harga per unit tanpa PPN (S1 & S3 dibagi 1,11)"],
    ["fact_penjualan", "nilai_kotor_excl", "DECIMAL(15,2)", "S1, S2, S3", "-", "qty * harga_satuan_excl"],
    ["fact_penjualan", "nilai_diskon_excl", "DECIMAL(15,2)", "S1, S2, S3", "disc_amount, disc_pct", "Potongan diskon tanpa PPN"],
    ["fact_penjualan", "nilai_bersih_excl", "DECIMAL(15,2)", "S1, S2, S3", "-", "nilai_kotor_excl - nilai_diskon_excl"],
    ["fact_penjualan", "harga_pokok_satuan", "DECIMAL(15,2)", "S4", "harga_pokok", "COGS efektif saat tanggal transaksi (SCD Type 2)"],
    ["fact_penjualan", "total_harga_pokok", "DECIMAL(15,2)", "S1, S2, S3, S4", "-", "qty * harga_pokok_satuan"],
    ["fact_penjualan", "fee_komisi", "DECIMAL(15,2)", "S3", "commission + service fees", "Fee marketplace dialokasikan proporsional per item (0 utk S1/S2)"],
    ["fact_penjualan", "margin_kotor", "DECIMAL(15,2)", "Kalkulasi", "-", "nilai_bersih_excl - total_harga_pokok - fee_komisi"]
]

DATA_Q1 = [
    ["Aksesoris Elektronik", "MARKETPLACE", "Q1 2023", "Rp 75.607.504,02", "Rp 64.985.672,80", "Rp 10.621.831,22", "+16,34%"],
    ["Aksesoris Elektronik", "TOKO_FISIK", "Q1 2023", "Rp 586.368.178,00", "Rp 506.540.308,00", "Rp 79.827.870,00", "+15,76%"],
    ["Aksesoris Elektronik", "WEB", "Q1 2023", "Rp 343.505.999,05", "Rp 314.075.069,60", "Rp 29.430.929,45", "+9,37%"],
    ["Atasan", "MARKETPLACE", "Q1 2023", "Rp 78.942.794,42", "Rp 67.269.833,20", "Rp 11.672.961,22", "+17,35%"],
    ["Atasan", "TOKO_FISIK", "Q1 2023", "Rp 339.430.244,00", "Rp 390.078.083,00", "-Rp 50.647.839,00", "-12,98%"],
    ["Atasan", "WEB", "Q1 2023", "Rp 235.150.646,40", "Rp 193.393.264,05", "Rp 41.757.382,35", "+21,59%"],
    ["Bawahan", "MARKETPLACE", "Q1 2023", "Rp 28.316.061,09", "Rp 32.935.700,14", "-Rp 4.619.639,05", "-14,03%"],
    ["Bawahan", "TOKO_FISIK", "Q1 2023", "Rp 152.547.870,00", "Rp 137.207.901,00", "Rp 15.339.969,00", "+11,18%"],
    ["Bawahan", "WEB", "Q1 2023", "Rp 76.728.353,00", "Rp 108.554.970,00", "-Rp 31.826.617,00", "-29,32%"],
    ["Kursi", "MARKETPLACE", "Q1 2023", "Rp 73.561.090,86", "Rp 58.526.733,79", "Rp 15.034.357,07", "+25,69%"],
    ["Kursi", "TOKO_FISIK", "Q1 2023", "Rp 487.127.195,00", "Rp 459.352.469,00", "Rp 27.774.726,00", "+6,05%"],
    ["Kursi", "WEB", "Q1 2023", "Rp 337.417.872,25", "Rp 246.233.445,70", "Rp 91.184.426,55", "+37,03%"],
    ["Laptop", "MARKETPLACE", "Q1 2023", "Rp 16.543.536,68", "Rp 20.753.704,75", "-Rp 4.210.168,07", "-20,29%"],
    ["Laptop", "TOKO_FISIK", "Q1 2023", "Rp 167.251.064,00", "Rp 223.208.361,00", "-Rp 55.957.297,00", "-25,07%"],
    ["Laptop", "WEB", "Q1 2023", "Rp 108.508.124,80", "Rp 97.334.774,70", "Rp 11.173.350,10", "+11,48%"],
    ["Lemari", "MARKETPLACE", "Q1 2023", "Rp 110.336.481,80", "Rp 141.446.912,30", "-Rp 31.110.430,50", "-21,99%"],
    ["Lemari", "TOKO_FISIK", "Q1 2023", "Rp 599.855.655,00", "Rp 431.014.716,00", "Rp 168.840.939,00", "+39,17%"],
    ["Lemari", "WEB", "Q1 2023", "Rp 303.308.722,80", "Rp 258.215.130,15", "Rp 45.093.592,65", "+17,46%"],
    ["Meja", "MARKETPLACE", "Q1 2023", "Rp 20.478.406,89", "Rp 45.273.936,41", "-Rp 24.795.529,52", "-54,77%"],
    ["Meja", "TOKO_FISIK", "Q1 2023", "Rp 213.584.924,00", "Rp 222.060.360,00", "-Rp 8.475.436,00", "-3,82%"],
    ["Meja", "WEB", "Q1 2023", "Rp 111.498.567,35", "Rp 129.094.219,35", "-Rp 17.595.652,00", "-13,63%"],
    ["Sepatu", "MARKETPLACE", "Q1 2023", "Rp 50.302.586,02", "Rp 59.815.961,94", "-Rp 9.513.375,92", "-15,90%"],
    ["Sepatu", "TOKO_FISIK", "Q1 2023", "Rp 470.862.347,00", "Rp 465.282.749,00", "Rp 5.579.598,00", "+1,20%"],
    ["Sepatu", "WEB", "Q1 2023", "Rp 302.964.903,40", "Rp 444.005.918,05", "-Rp 141.041.014,65", "-31,77%"],
    ["Smartphone", "MARKETPLACE", "Q1 2023", "Rp 24.702.737,97", "Rp 36.344.721,07", "-Rp 11.641.983,10", "-32,03%"],
    ["Smartphone", "TOKO_FISIK", "Q1 2023", "Rp 271.854.079,00", "Rp 275.828.236,00", "-Rp 3.974.157,00", "-1,44%"],
    ["Smartphone", "WEB", "Q1 2023", "Rp 180.847.687,52", "Rp 162.961.746,95", "Rp 17.885.940,57", "+10,98%"]
]

DATA_Q2_SEGMENT = [
    ["Pelanggan Online Murni (Bukan Member)", "396", "2.031", "4.301", "Rp 36.614.206.964,77", "Rp 18.027.674,53", "Rp 7.219.541.584,77"],
    ["Pelanggan Online Sekaligus Member Toko Fisik", "199", "970", "2.050", "Rp 16.594.151.790,05", "Rp 17.107.372,98", "Rp 3.261.832.431,05"]
]

DATA_Q2_SAMPLES = [
    ["2936", "Lurhur Widodo", "88443299253", "MEMBER_DAN_WEB", "9", "9", "Rp 261.727.150,45", "Rp 488.178.150,45"],
    ["3067", "dr. Hardi Permata, M.M.", "81007449628", "MEMBER_DAN_WEB", "9", "11", "Rp 218.496.400,00", "Rp 385.897.400,00"],
    ["2949", "R.A. Wirda Nasyidah", "89507305174", "MEMBER_DAN_WEB", "10", "7", "Rp 171.297.500,90", "Rp 350.203.900,90"],
    ["2910", "Dewi Kusmawati", "80723763964", "MEMBER_DAN_WEB", "8", "9", "Rp 243.394.500,00", "Rp 347.640.600,00"],
    ["3009", "Victoria Mangunsong", "80309688519", "MEMBER_DAN_WEB", "5", "13", "Rp 125.222.850,45", "Rp 346.720.550,45"],
    ["2938", "Saka Yulianti, S.E.", "83388440265", "MEMBER_DAN_WEB", "6", "10", "Rp 213.327.600,00", "Rp 342.804.550,00"],
    ["2979", "T. Waluyo Nuraini, S.Kom", "89474541857", "MEMBER_DAN_WEB", "7", "7", "Rp 158.653.300,00", "Rp 330.920.700,00"],
    ["2934", "Artawan Halim", "81361662487", "MEMBER_DAN_WEB", "5", "8", "Rp 151.577.200,00", "Rp 317.027.050,00"],
    ["2948", "Ir. Bakiono Natsir, M.Kom.", "88183208704", "MEMBER_DAN_WEB", "5", "7", "Rp 114.608.000,00", "Rp 304.741.200,00"],
    ["3088", "Bahuraksa Simbolon", "89648001579", "MEMBER_DAN_WEB", "9", "8", "Rp 218.050.951,35", "Rp 302.030.451,35"]
]

DATA_Q3 = [
    ["NO_PROMO", "Reguler Tanpa Diskon", "Reguler", "0%", "9.255", "16.677", "Rp 139.993.611.161,17", "Rp 3.372.223.757,75", "Rp 26.440.670.933,17", "18,89%", "Sangat Sehat (Baseline)"],
    ["FLASH50", "Flash Sale Akhir Bulan", "Voucher", "5%", "73", "164", "Rp 1.440.318.167,55", "Rp 48.481.832,45", "Rp 285.672.433,55", "19,83%", "Sangat Efektif (Margin Tertinggi)"],
    ["BACKSCHOOL", "Promo Back to School", "Voucher", "10%", "134", "278", "Rp 2.054.970.216,20", "Rp 96.002.783,80", "Rp 380.520.955,20", "18,52%", "Sangat Efektif (Volume & Margin Kuat)"],
    ["NEWYEAR10", "Diskon Tahun Baru", "Voucher", "5%", "61", "127", "Rp 974.332.664,85", "Rp 38.914.335,15", "Rp 172.349.911,85", "17,69%", "Moderat (Aman)"],
    ["GAJIAN25", "Promo Gajian", "Cashback", "5%", "123", "236", "Rp 2.193.672.310,80", "Rp 106.844.689,20", "Rp 383.446.849,80", "17,48%", "Moderat (Stabil)"],
    ["RAMADAN23", "Promo Ramadan 2023", "Voucher", "10%", "58", "138", "Rp 1.156.098.400,00", "Rp 68.188.600,00", "Rp 198.408.617,00", "17,16%", "Moderat"],
    ["MEMBER15", "Diskon Member Khusus", "Voucher", "10%", "79", "165", "Rp 1.394.579.900,00", "Rp 91.490.100,00", "Rp 235.122.302,00", "16,86%", "Moderat (Retensi Loyalitas)"],
    ["WEEKEND20", "Diskon Akhir Pekan", "Voucher", "5%", "139", "273", "Rp 2.528.998.129,70", "Rp 180.935.870,30", "Rp 393.435.463,70", "15,56%", "Cukup (Margin Tertekan Tipis)"],
    ["BUNDLE2", "Beli 2 Diskon Bundling", "Bundling", "20%", "137", "288", "Rp 2.527.068.515,30", "Rp 216.590.484,70", "Rp 390.030.279,30", "15,43%", "Cukup (Perlu Kontrol HPP)"],
    ["IMLEK24", "Promo Spesial Imlek", "Voucher", "15%", "147", "311", "Rp 2.075.445.318,90", "Rp 173.971.681,10", "Rp 318.891.361,90", "15,36%", "Cukup"],
    ["HARBOLNAS", "Hari Belanja Online", "Voucher", "20%", "120", "273", "Rp 2.240.683.212,60", "Rp 263.220.787,40", "Rp 305.664.104,60", "13,64%", "⚠️ Margin Tergerus Signifikan"]
]

DATA_Q4 = [
    ["P-1019", "Samsung Smartphone Atque 128GB", "Elektronik", "Smartphone", "70", "157", "97", "324", "21,60%", "0,28", "Rp 4.690.045,11"],
    ["P-1054", "Uniqlo Atasan Maxime", "Pakaian", "Atasan", "72", "181", "96", "349", "20,63%", "0,26", "Rp 50.835.931,01"],
    ["P-1024", "Uniqlo Bawahan Aperiam 256GB", "Pakaian", "Bawahan", "52", "141", "104", "297", "17,51%", "0,21", "Rp 52.120.780,91"],
    ["P-1031", "Apple Laptop Pariatur", "Elektronik", "Laptop", "58", "167", "107", "332", "17,47%", "0,21", "Rp 2.076.874,67"],
    ["P-1045", "Erigo Atasan Cumque", "Pakaian", "Atasan", "52", "159", "90", "301", "17,28%", "0,21", "Rp 4.769.928,15"],
    ["P-1023", "Informa Lemari Ea 256GB", "Furnitur", "Lemari", "60", "172", "116", "348", "17,24%", "0,21", "Rp 34.897.085,01"],
    ["P-1049", "Olympic Lemari Sed 128GB", "Furnitur", "Lemari", "52", "152", "105", "309", "16,83%", "0,20", "Rp 293.005.098,70"],
    ["P-1015", "Informa Kursi Quaerat Lite", "Furnitur", "Kursi", "48", "155", "85", "288", "16,67%", "0,20", "Rp 583.821,49"],
    ["P-1014", "Informa Meja Reiciendis", "Furnitur", "Meja", "51", "160", "100", "311", "16,40%", "0,20", "Rp 59.051.426,38"],
    ["P-1025", "Erigo Bawahan Numquam Pro", "Pakaian", "Bawahan", "57", "186", "106", "349", "16,33%", "0,20", "Rp 10.258.800,98"]
]

print("Building Markdown report...")
# (Lanjutan kode pembuat Markdown dan DOCX)
