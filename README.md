# Proyek Data Warehouse & Business Intelligence (DWBI)
## Studi Kasus: Nusantara Retail Group (NRG) - Konsolidasi Penjualan Omnichannel

Repositori ini memuat seluruh artefak teknis dan laporan resmi pengembangan Data Warehouse untuk **Nusantara Retail Group (NRG)** sesuai panduan penugasan Tugas Kelompok 1 DWBI.

---

### Struktur Repositori & Berkas Deliverable
- `Laporan_Desain_Dimensional_NRG.docx`: Dokumen laporan akademis resmi dalam format Microsoft Word lengkap dengan styling standar institusi.
- `Laporan_Desain_Dimensional_NRG.md`: Dokumen laporan teknis lengkap dalam format Markdown dengan diagram Mermaid dan tabel output kueri aktual.
- `dw_schema_ddl.sql`: Skrip DDL pembentukan skema basis data Data Warehouse MySQL (`nrg_dw`) mencakup 1 tabel fakta, 5 tabel dimensi, dan 1 tabel audit error.
- `kueri_pembuktian.sql`: Empat kueri SQL analitik untuk menjawab seluruh pertanyaan strategis Direktur Penjualan NRG.
- `main_etl_job.kjb`: Master orchestration Job Pentaho Data Integration (PDI).
- `dim_waktu_loader.ktr`: Transformation PDI untuk pemuatan `dim_waktu`.
- `dim_produk_loader.ktr`: Transformation PDI untuk pemuatan `dim_produk` (termasuk penanganan *late-arriving dimension*).
- `dim_toko_kanal_loader.ktr`: Transformation PDI untuk pemuatan `dim_toko_kanal` (termasuk standarisasi kota via `ref_kota.csv`).
- `dim_pelanggan_loader.ktr`: Transformation PDI untuk pemuatan `dim_pelanggan` (termasuk resolusi identitas omnichannel via normalisasi HP).
- `dim_promosi_loader.ktr`: Transformation PDI untuk pemuatan `dim_promosi` (termasuk pengaliran anomali data teks 'sepuluh' ke tabel audit error).
- `fact_penjualan_loader.ktr`: Transformation PDI untuk pemuatan tabel fakta `fact_penjualan` Stream S1 (E-Commerce Web).
- `fact_s2_pos_loader.ktr`: Transformation PDI untuk pemuatan tabel fakta `fact_penjualan` Stream S2 (42 Toko Fisik POS, filter transaksi VOID).
- `fact_s3_mpl_loader.ktr`: Transformation PDI untuk pemuatan tabel fakta `fact_penjualan` Stream S3 (Marketplace API, JSON array flattening & deduplikasi).
- `run_etl.py`: Skrip otomasi pipeline pemuatan berkinerja tinggi (selesai dalam 3,92 detik untuk 14.723 baris fakta).
- `generate_pdi_files.py`: Generator otomatis berkas XML Pentaho (.ktr dan .kjb).

---

### Panduan Eksekusi dari Kondisi Kosong (Zero-to-Hero Guide)

#### 1. Prasyarat Lingkungan
- MySQL Server aktif pada `localhost:3306` (User: `root`, Password: *(kosong)*).
- Pentaho Data Integration (PDI / Kettle v9.x / v10.x).
- Python 3.9+ dengan pustaka `pandas` dan `mysql-connector-python`.

#### 2. Setup Basis Data MySQL
Buka PowerShell / Command Prompt di folder ini, lalu jalankan:
```powershell
# 1. Buat dan inisialisasi Data Warehouse nrg_dw
c:\xampp1\mysql\bin\mysql.exe -u root -e "CREATE DATABASE IF NOT EXISTS nrg_dw;"
c:\xampp1\mysql\bin\mysql.exe -u root nrg_dw < dw_schema_ddl.sql

# 2. Buat dan muat basis data OLTP e-commerce nrg_ecom
c:\xampp1\mysql\bin\mysql.exe -u root -e "CREATE DATABASE IF NOT EXISTS nrg_ecom;"
c:\xampp1\mysql\bin\mysql.exe -u root nrg_ecom < Data\S1_ecom_db_schema_mysql.sql
cd Data
python load_all.py
cd ..
```

#### 3. Eksekusi Pipeline ETL
##### Pilihan A: Menggunakan Pentaho Kitchen (CLI)
```powershell
c:\Users\daffa\Downloads\pdi-ce-10.2.0.0-222\data-integration\kitchen.bat /file:"c:\Users\daffa\Downloads\Tugas 1 DWBI KELOMPOK\main_etl_job.kjb" /level:Basic
```

##### Pilihan B: Menggunakan Pentaho Spoon (GUI)
1. Buka `spoon.bat` di folder instalasi PDI.
2. Buka `main_etl_job.kjb`.
3. Klik tombol Run (Play).

##### Pilihan C: Menggunakan Python ETL Runner (Pemuatan Penuh Cepat)
```powershell
python run_etl.py
```

#### 4. Eksekusi Empat Kueri Pembuktian Bisnis
Untuk memverifikasi jawaban terhadap empat pertanyaan Direktur Penjualan:
```powershell
c:\xampp1\mysql\bin\mysql.exe -u root nrg_dw < kueri_pembuktian.sql
```

Seluruh 4 kueri akan menghasilkan tabel data konsolidasi yang menjawab secara komprehensif:
1. Pertumbuhan Margin YoY Q1 2023 vs Q1 2022.
2. Segmentasi Pelanggan Omnichannel vs Online Murni.
3. Evaluasi Efektivitas Kampanye Promosi terhadap Margin.
4. Analisis Pangsa Pasar Produk Marketplace untuk Realokasi Stok.