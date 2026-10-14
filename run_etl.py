"""
====================================================================
PIPELINE ETL LENGKAP & OTOMATIS: DATA WAREHOUSE NUSANTARA RETAIL GROUP (NRG)
Mata Kuliah: Data Warehouse / Business Intelligence - Tugas 1
Sumber: S1 (ECOM_DB), S2 (POS_TOKO), S3 (MPL_API), S4 (ERP_MASTER), S5 (MKT_SHEET)
Target: Basis Data MySQL 'nrg_dw' (Star Schema)
====================================================================
"""

import os
import glob
import json
import re
import datetime
import pandas as pd
import numpy as np
import mysql.connector

# ====================================================================
# 1. KONFIGURASI KONEKSI DATABASE & DIREKTORI
# ====================================================================
DB_CONFIG_ECOM = {
    "host": "localhost",
    "port": 3306,
    "user": "root",
    "password": "",
    "database": "nrg_ecom"
}

DB_CONFIG_DW = {
    "host": "localhost",
    "port": 3306,
    "user": "root",
    "password": "",
    "database": "nrg_dw"
}

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE_DIR, "Data")


def get_dw_connection():
    return mysql.connector.connect(**DB_CONFIG_DW)


def get_ecom_connection():
    return mysql.connector.connect(**DB_CONFIG_ECOM)


# ====================================================================
# 2. HELPER FUNCTIONS
# ====================================================================
def clean_phone(p):
    """Normalisasi nomor HP standar Indonesia: menghapus awalan +62, 62, 0."""
    if pd.isna(p):
        return ""
    s = str(p).split('.')[0].strip()
    digits = ''.join(c for c in s if c.isdigit())
    if digits.startswith('62'):
        digits = digits[2:]
    elif digits.startswith('0'):
        digits = digits[1:]
    return digits


# ====================================================================
# 3. ETL DIM_WAKTU
# ====================================================================
def load_dim_waktu():
    print("\n[1/6] Memuat DIM_WAKTU...")
    conn = get_dw_connection()
    cursor = conn.cursor()
    cursor.execute("SET FOREIGN_KEY_CHECKS = 0;")
    cursor.execute("TRUNCATE TABLE dim_waktu;")
    cursor.execute("SET FOREIGN_KEY_CHECKS = 1;")
    
    start_date = datetime.date(2022, 1, 1)
    end_date = datetime.date(2024, 12, 31)
    
    records = []
    curr = start_date
    nama_hari_id = ['Senin', 'Selasa', 'Rabu', 'Kamis', 'Jumat', 'Sabtu', 'Minggu']
    nama_bulan_id = ['', 'Januari', 'Februari', 'Maret', 'April', 'Mei', 'Juni',
                     'Juli', 'Agustus', 'September', 'Oktober', 'November', 'Desember']
    
    while curr <= end_date:
        sk_waktu = int(curr.strftime("%Y%m%d"))
        thn = curr.year
        bln = curr.month
        hari = curr.day
        kuartal = (bln - 1) // 3 + 1
        kuartal_nama = f"Q{kuartal} {thn}"
        n_bulan = nama_bulan_id[bln]
        n_hari = nama_hari_id[curr.weekday()]
        is_wk = 1 if curr.weekday() >= 5 else 0
        
        records.append((sk_waktu, curr, thn, kuartal, kuartal_nama, bln, n_bulan, hari, n_hari, is_wk))
        curr += datetime.timedelta(days=1)
        
    sql = """
        INSERT INTO dim_waktu 
        (sk_waktu, tanggal, tahun, kuartal, kuartal_nama, bulan, nama_bulan, hari, nama_hari, is_weekend)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        ON DUPLICATE KEY UPDATE tahun=VALUES(tahun)
    """
    cursor.executemany(sql, records)
    conn.commit()
    print(f"  -> Selesai: {len(records)} baris kalender dimuat ke dim_waktu.")
    cursor.close()
    conn.close()


# ====================================================================
# 4. ETL DIM_PRODUK
# ====================================================================
def load_dim_produk():
    print("\n[2/6] Memuat DIM_PRODUK...")
    conn = get_dw_connection()
    cursor = conn.cursor()
    cursor.execute("SET FOREIGN_KEY_CHECKS = 0;")
    cursor.execute("TRUNCATE TABLE dim_produk;")
    cursor.execute("SET FOREIGN_KEY_CHECKS = 1;")
    
    erp_path = os.path.join(DATA_DIR, "S4_ERP_MASTER", "produk_master.csv")
    df_s4 = pd.read_csv(erp_path)
    
    # Ambil riwayat terbaru per material_no untuk atribut dimensi produk
    df_sorted = df_s4.sort_values(by=['material_no', 'berlaku_sejak'])
    df_latest = df_sorted.drop_duplicates(subset=['material_no'], keep='last')
    
    records = []
    for _, row in df_latest.iterrows():
        records.append((
            str(row['material_no']).strip(),
            str(row['nama_produk']).strip(),
            str(row['brand']).strip(),
            str(row['kategori']).strip(),
            str(row['sub_kategori']).strip(),
            float(row['harga_pokok']),
            str(row['supplier']).strip(),
            str(row['status']).strip()
        ))
        
    # Kasus Late Arriving Dimension: ORD-9999 (product_id 61 di ECOM)
    # Ditambahkan sebagai Inferred Member
    records.append((
        'P-1061', # atau SKU-NEWARR-001
        'Smartphone Model Terbaru (Belum Terdaftar di ERP)',
        'Samsung',
        'Elektronik',
        'Smartphone',
        0.00,
        'Belum Ditentukan',
        'BELUM_TERDAFTAR_ERP'
    ))
    
    sql = """
        INSERT INTO dim_produk
        (material_no, nama_produk, brand, kategori, sub_kategori, harga_pokok_terkini, supplier, status_erp)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
        ON DUPLICATE KEY UPDATE 
            nama_produk=VALUES(nama_produk),
            brand=VALUES(brand),
            kategori=VALUES(kategori),
            sub_kategori=VALUES(sub_kategori),
            harga_pokok_terkini=VALUES(harga_pokok_terkini),
            supplier=VALUES(supplier),
            status_erp=VALUES(status_erp)
    """
    cursor.executemany(sql, records)
    conn.commit()
    print(f"  -> Selesai: {len(records)} produk dimuat ke dim_produk (termasuk kasus Late Arriving P-1061).")
    cursor.close()
    conn.close()


# ====================================================================
# 5. ETL DIM_TOKO_KANAL
# ====================================================================
def load_dim_toko_kanal():
    print("\n[3/6] Memuat DIM_TOKO_KANAL...")
    conn = get_dw_connection()
    cursor = conn.cursor()
    cursor.execute("SET FOREIGN_KEY_CHECKS = 0;")
    cursor.execute("TRUNCATE TABLE dim_toko_kanal;")
    cursor.execute("SET FOREIGN_KEY_CHECKS = 1;")
    
    # 1. Baca ref_kota
    ref_kota_df = pd.read_csv(os.path.join(DATA_DIR, "ref_kota.csv"))
    kota_map = dict(zip(ref_kota_df['alias'].str.upper().str.strip(), ref_kota_df['kota_baku'].str.strip()))
    
    # 2. Baca store_master (42 toko fisik)
    store_df = pd.read_csv(os.path.join(DATA_DIR, "S2_POS_TOKO", "store_master.csv"))
    if len(store_df.columns) == 1:
        store_df = pd.read_csv(os.path.join(DATA_DIR, "S2_POS_TOKO", "store_master.csv"), sep=';')
        
    records = []
    for _, row in store_df.iterrows():
        k_toko = str(row['store_code']).strip()
        n_toko = str(row['store_name']).strip()
        raw_city = str(row['city']).strip()
        norm_city = kota_map.get(raw_city.upper(), raw_city)
        prov = str(row['province']).strip()
        fmt = str(row['format_toko']).strip()
        records.append((k_toko, n_toko, 'TOKO_FISIK', norm_city, prov, fmt))
        
    # 3. Tambah Kanal WEB & MARKETPLACE
    records.append(('WEB', 'Website Resmi Nusantara Retail Group', 'WEB', 'Jakarta Pusat', 'DKI Jakarta', 'Online E-Commerce'))
    records.append(('MARKETPLACE_A', 'Marketplace Platform A', 'MARKETPLACE', 'Nasional', 'Nasional', 'Online Third-Party'))
    records.append(('MARKETPLACE_B', 'Marketplace Platform B', 'MARKETPLACE', 'Nasional', 'Nasional', 'Online Third-Party'))
    
    sql = """
        INSERT INTO dim_toko_kanal
        (kode_toko_kanal, nama_toko_kanal, jenis_kanal, kota, provinsi, format_toko)
        VALUES (%s, %s, %s, %s, %s, %s)
        ON DUPLICATE KEY UPDATE 
            nama_toko_kanal=VALUES(nama_toko_kanal),
            kota=VALUES(kota),
            provinsi=VALUES(provinsi)
    """
    cursor.executemany(sql, records)
    conn.commit()
    print(f"  -> Selesai: {len(records)} entitas kanal/toko dimuat ke dim_toko_kanal.")
    cursor.close()
    conn.close()


# ====================================================================
# 6. ETL DIM_PELANGGAN
# ====================================================================
def load_dim_pelanggan():
    print("\n[4/6] Memuat DIM_PELANGGAN (Resolusi Identitas Omnichannel)...")
    dw_conn = get_dw_connection()
    dw_cursor = dw_conn.cursor()
    dw_cursor.execute("SET FOREIGN_KEY_CHECKS = 0;")
    dw_cursor.execute("TRUNCATE TABLE dim_pelanggan;")
    dw_cursor.execute("SET FOREIGN_KEY_CHECKS = 1;")
    dw_cursor.close()
    dw_conn.close()
    
    conn_ecom = get_ecom_connection()
    cust_df = pd.read_sql("SELECT customer_id, full_name, phone, gender, birth_date FROM customers", conn_ecom)
    addr_df = pd.read_sql("SELECT customer_id, city FROM customer_addresses WHERE is_primary=1", conn_ecom)
    conn_ecom.close()
    
    # Merge alamat utama pelanggan ecom
    cust_df = cust_df.merge(addr_df, on='customer_id', how='left')
    cust_df['city'] = cust_df['city'].fillna('Tidak Diketahui')
    cust_df['norm_hp'] = cust_df['phone'].apply(clean_phone)
    
    # Baca member POS S2
    member_df = pd.read_csv(os.path.join(DATA_DIR, "S2_POS_TOKO", "member.csv"), sep=';')
    member_df['norm_hp'] = member_df['hp'].apply(clean_phone)
    
    # Standarisasi kota member
    ref_kota_df = pd.read_csv(os.path.join(DATA_DIR, "ref_kota.csv"))
    kota_map = dict(zip(ref_kota_df['alias'].str.upper().str.strip(), ref_kota_df['kota_baku'].str.strip()))
    member_df['kota_norm'] = member_df['kota'].astype(str).str.upper().str.strip().map(lambda x: kota_map.get(x, x.title()))
    
    # Deteksi Overlap Pelanggan Ecom vs Member Toko via Nomor HP
    member_by_hp = {}
    for _, row in member_df.iterrows():
        if row['norm_hp']:
            member_by_hp[row['norm_hp']] = row
            
    records = []
    matched_hps = set()
    
    # 1. Pelanggan E-Commerce (dan yang overlap)
    for _, c_row in cust_df.iterrows():
        nhp = c_row['norm_hp']
        cid = f"CUST-{c_row['customer_id']}"
        cname = c_row['full_name']
        gender = 'Laki-Laki' if c_row['gender'] == 'M' else ('Perempuan' if c_row['gender'] == 'F' else 'TIDAK_DIKETAHUI')
        city = c_row['city']
        
        if nhp in member_by_hp:
            # Overlap! Pelanggan E-Commerce = Member Toko Fisik
            matched_hps.add(nhp)
            m_info = member_by_hp[nhp]
            identitas = f"{cid}|{m_info['member_no']}"
            records.append((
                identitas,
                cname,
                nhp,
                'MEMBER_DAN_WEB',
                city if city != 'Tidak Diketahui' else m_info['kota_norm'],
                gender,
                1 # is_omnichannel = True
            ))
        else:
            records.append((
                cid,
                cname,
                nhp,
                'NON_MEMBER_WEB',
                city,
                gender,
                0 # is_omnichannel = False
            ))
            
    # 2. Member Toko Fisik yang belum pernah belanja di Web
    for _, m_row in member_df.iterrows():
        nhp = m_row['norm_hp']
        if nhp not in matched_hps:
            records.append((
                str(m_row['member_no']),
                str(m_row['member_name']),
                nhp,
                'MEMBER_TOKO',
                str(m_row['kota_norm']),
                'TIDAK_DIKETAHUI',
                0 # is_omnichannel = False
            ))
            
    # 3. Kumpulkan Buyer Hash Marketplace dari S3
    s3_files = glob.glob(os.path.join(DATA_DIR, "S3_MPL_API", "*.json"))
    buyer_hashes = set()
    for f in s3_files:
        with open(f, 'r') as jf:
            d = json.load(jf)
            for r in d['records']:
                b = r.get('buyer', {})
                b_hash = b.get('hash')
                b_city = b.get('city', 'Nasional')
                if b_hash:
                    buyer_hashes.add((b_hash, b_city))
                    
    for b_hash, b_city in buyer_hashes:
        records.append((
            f"BUYER-{b_hash}",
            f"Marketplace Buyer ({b_hash})",
            "-",
            'BUYER_MARKETPLACE',
            b_city,
            'TIDAK_DIKETAHUI',
            0
        ))
        
    # Default Pelanggan Anonim / Tamu Toko
    records.append((
        'CUST-ANONYMOUS',
        'Pelanggan Reguler Non-Member',
        "-",
        'NON_MEMBER_TOKO',
        'Nasional',
        'TIDAK_DIKETAHUI',
        0
    ))
    
    conn = get_dw_connection()
    cursor = conn.cursor()
    sql = """
        INSERT INTO dim_pelanggan
        (no_identitas_asal, nama_pelanggan, no_hp_normal, status_member, kota, jenis_kelamin, is_omnichannel)
        VALUES (%s, %s, %s, %s, %s, %s, %s)
    """
    cursor.executemany(sql, records)
    conn.commit()
    print(f"  -> Selesai: {len(records)} profil pelanggan dimuat ke dim_pelanggan ({len(matched_hps)} teridentifikasi Omnichannel).")
    cursor.close()
    conn.close()


# ====================================================================
# 7. ETL DIM_PROMOSI
# ====================================================================
def load_dim_promosi():
    print("\n[5/6] Memuat DIM_PROMOSI (Pembersihan S5 & Penanganan Error 'sepuluh')...")
    conn = get_dw_connection()
    cursor = conn.cursor()
    cursor.execute("SET FOREIGN_KEY_CHECKS = 0;")
    cursor.execute("TRUNCATE TABLE dim_promosi;")
    cursor.execute("TRUNCATE TABLE error_kampanye_marketing;")
    cursor.execute("SET FOREIGN_KEY_CHECKS = 1;")
    
    mkt_path = os.path.join(DATA_DIR, "S5_MKT_SHEET", "kampanye_marketing.csv")
    with open(mkt_path, 'r', encoding='utf-8') as f:
        lines = [line.strip() for line in f.readlines() if line.strip()]
        
    header = lines[0].split(',')
    
    clean_promos = {}
    error_records = []
    
    # Record Default: Tanpa Promosi
    clean_promos['NO_PROMO'] = ('NO_PROMO', 'Tanpa Promosi / Reguler', 'Reguler', 'Semua Kanal', 0.00, 'System')
    
    for line in lines[1:]:
        cols = [c.strip() for c in line.split(',')]
        if len(cols) < 8 or not cols[0]:
            # Baris kosong / tidak lengkap
            continue
            
        k_promo = cols[0].upper().strip()
        n_kampanye = cols[1].strip()
        j_promo = cols[2].strip()
        kanal = cols[3].strip()
        t_mulai = cols[4].strip()
        t_selesai = cols[5].strip()
        t_diskon_raw = cols[6].strip()
        pic = cols[7].strip()
        
        # Validasi target_diskon_persen harus berupa angka numerik
        try:
            t_diskon = float(t_diskon_raw)
            if k_promo not in clean_promos:
                clean_promos[k_promo] = (k_promo, n_kampanye, j_promo, kanal, t_diskon, pic)
        except ValueError:
            # Baris gagal validasi (kasus teks 'sepuluh') -> diarahkan ke error table
            error_records.append((
                k_promo, n_kampanye, j_promo, kanal, t_mulai, t_selesai, t_diskon_raw, pic,
                "Nilai target_diskon_persen bukan numerik ('sepuluh')"
            ))
            
    # Tambahkan juga voucher dari S1 jika ada yang belum tercover
    conn_ecom = get_ecom_connection()
    vouchers_df = pd.read_sql("SELECT promo_code, discount_value FROM vouchers", conn_ecom)
    conn_ecom.close()
    
    for _, v in vouchers_df.iterrows():
        pcode = str(v['promo_code']).upper().strip()
        if pcode not in clean_promos:
            clean_promos[pcode] = (pcode, f"Voucher {pcode}", 'Voucher', 'Situs Web', float(v['discount_value']), 'Ecom Team')
            
    # Simpan error records
    if error_records:
        sql_err = """
            INSERT INTO error_kampanye_marketing
            (kode_promo, nama_kampanye, jenis_promo, kanal, tgl_mulai, tgl_selesai, target_diskon_persen, pic, alasan_error)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
        """
        cursor.executemany(sql_err, error_records)
        print(f"  -> [DATA QUALITY] {len(error_records)} baris gagal validasi dialirkan ke error_kampanye_marketing.")
        
    # Simpan clean promo ke dim_promosi
    sql_promo = """
        INSERT INTO dim_promosi
        (kode_promo, nama_kampanye, jenis_promo, kanal_target, target_diskon_persen, pic)
        VALUES (%s, %s, %s, %s, %s, %s)
        ON DUPLICATE KEY UPDATE 
            nama_kampanye=VALUES(nama_kampanye),
            target_diskon_persen=VALUES(target_diskon_persen)
    """
    cursor.executemany(sql_promo, list(clean_promos.values()))
    conn.commit()
    print(f"  -> Selesai: {len(clean_promos)} promosi aktif dimuat ke dim_promosi.")
    cursor.close()
    conn.close()


# ====================================================================
# 8. ETL FACT_PENJUALAN
# ====================================================================
def load_fact_penjualan():
    print("\n[6/6] Memuat FACT_PENJUALAN (Integrasi S1, S2, S3)...")
    dw_conn = get_dw_connection()
    cursor = dw_conn.cursor()
    cursor.execute("TRUNCATE TABLE fact_penjualan;")
    cursor.close()
    
    # -------------------------------------------------------------
    # Cache Lookup Dictionaries untuk Performa Cepat
    # -------------------------------------------------------------
    # 1. Produk: material_no -> sk_produk
    prod_df = pd.read_sql("SELECT sk_produk, material_no FROM dim_produk", dw_conn)
    prod_map = dict(zip(prod_df['material_no'], prod_df['sk_produk']))
    
    # 2. Toko/Kanal: kode_toko_kanal -> sk_toko_kanal
    toko_df = pd.read_sql("SELECT sk_toko_kanal, kode_toko_kanal FROM dim_toko_kanal", dw_conn)
    toko_map = dict(zip(toko_df['kode_toko_kanal'], toko_df['sk_toko_kanal']))
    
    # 3. Promosi: kode_promo -> sk_promosi
    promo_df = pd.read_sql("SELECT sk_promosi, kode_promo FROM dim_promosi", dw_conn)
    promo_map = dict(zip(promo_df['kode_promo'], promo_df['sk_promosi']))
    sk_no_promo = promo_map.get('NO_PROMO', 1)
    
    # 4. Pelanggan Lookup
    # a. CUST-ID -> sk_pelanggan
    # b. MEM-ID -> sk_pelanggan
    # c. BUYER-HASH -> sk_pelanggan
    pelanggan_df = pd.read_sql("SELECT sk_pelanggan, no_identitas_asal, no_hp_normal FROM dim_pelanggan", dw_conn)
    cust_id_map = {}
    member_no_map = {}
    buyer_hash_map = {}
    sk_anonymous = None
    
    for _, row in pelanggan_df.iterrows():
        ident = row['no_identitas_asal']
        sk = row['sk_pelanggan']
        if ident == 'CUST-ANONYMOUS':
            sk_anonymous = sk
        elif ident.startswith('BUYER-'):
            buyer_hash_map[ident.replace('BUYER-', '')] = sk
        elif '|' in ident:
            # Overlap: CUST-X|M-Y
            parts = ident.split('|')
            cust_id_map[parts[0]] = sk
            member_no_map[parts[1]] = sk
        elif ident.startswith('CUST-'):
            cust_id_map[ident] = sk
        else:
            member_no_map[ident] = sk
            
    # 5. Riwayat HPP / COGS dari S4 (produk_master.csv)
    # material_no -> list of (berlaku_sejak, harga_pokok)
    s4_path = os.path.join(DATA_DIR, "S4_ERP_MASTER", "produk_master.csv")
    s4_cogs_df = pd.read_csv(s4_path)
    s4_cogs_df['berlaku_sejak'] = pd.to_datetime(s4_cogs_df['berlaku_sejak']).dt.date
    s4_cogs_dict = {}
    for mat, grp in s4_cogs_df.groupby('material_no'):
        sorted_grp = grp.sort_values('berlaku_sejak')
        s4_cogs_dict[mat] = list(zip(sorted_grp['berlaku_sejak'], sorted_grp['harga_pokok']))
        
    def get_cogs(material_no, trx_date):
        if material_no not in s4_cogs_dict:
            return 0.0
        hist = s4_cogs_dict[material_no]
        effective_cogs = hist[0][1]
        for dt, cogs in hist:
            if dt <= trx_date:
                effective_cogs = cogs
            else:
                break
        return float(effective_cogs)
        
    fact_records = []
    
    # =============================================================
    # STREAM 1: S1 — ECOM_DB (Situs Web Resmi)
    # =============================================================
    print("  -> Memproses Stream 1: S1 (ECOM_DB)...")
    ecom_conn = get_ecom_connection()
    sql_ecom = """
        SELECT 
            oi.order_id,
            oi.line_no,
            oi.sku,
            oi.qty,
            oi.unit_price,
            oi.disc_amount,
            o.order_ts,
            o.customer_id,
            v.promo_code
        FROM order_items oi
        JOIN orders o ON oi.order_id = o.order_id
        LEFT JOIN vouchers v ON o.voucher_id = v.voucher_id
    """
    ecom_df = pd.read_sql(sql_ecom, ecom_conn)
    ecom_conn.close()
    
    sk_toko_web = toko_map.get('WEB')
    
    for _, row in ecom_df.iterrows():
        order_dt = pd.to_datetime(row['order_ts'])
        trx_date = order_dt.date()
        sk_waktu = int(order_dt.strftime("%Y%m%d"))
        
        # Mapping SKU ke material_no
        sku_str = str(row['sku']).strip()
        if sku_str == 'SKU-NEWARR-001':
            mat_no = 'P-1061' # Late arriving dimension ORD-9999
        else:
            m_match = re.search(r'SKU-(\d+)-', sku_str)
            mat_no = f"P-{m_match.group(1)}" if m_match else sku_str
            
        sk_prod = prod_map.get(mat_no, prod_map.get('P-1061', 1))
        
        # Lookup Pelanggan
        cid_str = f"CUST-{row['customer_id']}"
        sk_cust = cust_id_map.get(cid_str, sk_anonymous)
        
        # Lookup Promosi
        p_code = str(row['promo_code']).upper().strip() if pd.notna(row['promo_code']) else 'NO_PROMO'
        sk_promo = promo_map.get(p_code, sk_no_promo)
        
        qty = int(row['qty'])
        # Penyeragaman Harga: Eksklusif PPN (dibagi 1.11)
        unit_price_excl = round(float(row['unit_price']) / 1.11, 2)
        disc_excl = round(float(row['disc_amount']) / 1.11, 2)
        gross_excl = round(qty * unit_price_excl, 2)
        net_excl = round(gross_excl - disc_excl, 2)
        
        # COGS & Margin
        cogs_unit = get_cogs(mat_no, trx_date)
        tot_cogs = round(qty * cogs_unit, 2)
        fee_komisi = 0.00
        gross_margin = round(net_excl - tot_cogs - fee_komisi, 2)
        
        fact_records.append((
            sk_waktu, sk_prod, sk_toko_web, sk_cust, sk_promo,
            str(row['order_id']), int(row['line_no']), 'WEB',
            qty, unit_price_excl, gross_excl, disc_excl, net_excl,
            cogs_unit, tot_cogs, fee_komisi, gross_margin
        ))
    print(f"     Selesai S1: {len(ecom_df)} item transaksi web diproses.")
    
    # =============================================================
    # STREAM 2: S2 — POS_TOKO (42 Toko Fisik)
    # =============================================================
    print("  -> Memproses Stream 2: S2 (POS_TOKO - 42 Toko Fisik)...")
    pos_dir = os.path.join(DATA_DIR, "S2_POS_TOKO")
    header_files = sorted(glob.glob(os.path.join(pos_dir, "trx_header_TS*.csv")))
    
    pos_lines_count = 0
    void_lines_count = 0
    
    for hf in header_files:
        store_code = re.search(r'trx_header_(TS\d+)\.csv', hf).group(1)
        lf = os.path.join(pos_dir, f"trx_line_{store_code}.csv")
        if not os.path.exists(lf):
            continue
            
        hdf = pd.read_csv(hf, sep=';')
        ldf = pd.read_csv(lf, sep=';')
        
        # Filter Status VOID
        valid_h = hdf[hdf['status'] == 'NORMAL']
        void_count = len(hdf[hdf['status'] == 'VOID'])
        void_lines_count += void_count
        
        merged_pos = ldf.merge(valid_h, on='trx_no', how='inner')
        sk_toko = toko_map.get(store_code, 1)
        
        for _, row in merged_pos.iterrows():
            pos_lines_count += 1
            # Format tanggal: DD/MM/YYYY
            trx_dt = datetime.datetime.strptime(str(row['trx_date']).strip(), "%d/%m/%Y")
            trx_date = trx_dt.date()
            sk_waktu = int(trx_dt.strftime("%Y%m%d"))
            
            mat_no = str(row['item_code']).strip()
            sk_prod = prod_map.get(mat_no, 1)
            
            # Lookup Member Pelanggan
            m_no = str(row['member_no']).strip() if pd.notna(row['member_no']) else None
            sk_cust = member_no_map.get(m_no, sk_anonymous) if m_no else sk_anonymous
            
            sk_promo = sk_no_promo
            
            qty = int(row['qty'])
            # Harga pada S2 sudah Eksklusif PPN
            unit_price_excl = round(float(row['unit_price_excl']), 2)
            disc_pct = float(row['disc_pct'])
            gross_excl = round(qty * unit_price_excl, 2)
            disc_excl = round((unit_price_excl * (disc_pct / 100.0)) * qty, 2)
            net_excl = round(gross_excl - disc_excl, 2)
            
            cogs_unit = get_cogs(mat_no, trx_date)
            tot_cogs = round(qty * cogs_unit, 2)
            fee_komisi = 0.00
            gross_margin = round(net_excl - tot_cogs - fee_komisi, 2)
            
            fact_records.append((
                sk_waktu, sk_prod, sk_toko, sk_cust, sk_promo,
                str(row['trx_no']), int(row['line_seq']), 'TOKO_FISIK',
                qty, unit_price_excl, gross_excl, disc_excl, net_excl,
                cogs_unit, tot_cogs, fee_komisi, gross_margin
            ))
            
    print(f"     Selesai S2: {pos_lines_count} item transaksi toko fisik diproses (diabaikan {void_lines_count} transaksi VOID).")
    
    # =============================================================
    # STREAM 3: S3 — MPL_API (Marketplace API Pihak Ketiga)
    # =============================================================
    print("  -> Memproses Stream 3: S3 (MPL_API - Deduplikasi & UTC->WIB)...")
    mpl_dir = os.path.join(DATA_DIR, "S3_MPL_API")
    mpl_files = sorted(glob.glob(os.path.join(mpl_dir, "*.json")))
    
    # Baca seluruh invoice dan deduplikasi berbasis (invoice, seller_sku) memilih diambil_pada paling akhir
    raw_invoices = []
    for f in mpl_files:
        with open(f, 'r') as jf:
            d = json.load(jf)
            for r in d['records']:
                raw_invoices.append(r)
                
    # Kelompokkan per invoice untuk alokasi fee komisi proporsional
    # Deduplikasi item
    dedup_items = {} # (invoice, seller_sku) -> dict info
    inv_metadata = {} # invoice -> {'channel', 'paid_at', 'buyer', 'fees', 'diambil_pada'}
    
    for inv in raw_invoices:
        inv_no = inv['invoice']
        diambil = inv.get('diambil_pada', '')
        
        if inv_no not in inv_metadata or diambil > inv_metadata[inv_no]['diambil_pada']:
            inv_metadata[inv_no] = {
                'channel': inv['channel'],
                'paid_at': inv['paid_at'],
                'buyer': inv.get('buyer', {}),
                'fees': inv.get('fees', {}),
                'diambil_pada': diambil
            }
            
        for it in inv['items']:
            key = (inv_no, it['seller_sku'])
            if key not in dedup_items or diambil > dedup_items[key]['diambil_pada']:
                dedup_items[key] = {
                    'invoice': inv_no,
                    'seller_sku': it['seller_sku'],
                    'qty': it['qty'],
                    'price': it['price'],
                    'voucher': it.get('voucher', 0),
                    'diambil_pada': diambil
                }
                
    # Hitung total nilai penjualan bersih per invoice untuk pembagi fee komisi proporsional
    inv_total_net = {}
    for (inv_no, _), it in dedup_items.items():
        qty = int(it['qty'])
        u_price_excl = round(float(it['price']) / 1.11, 2)
        disc_excl = round(float(it['voucher']) / 1.11, 2)
        net_item = round((qty * u_price_excl) - disc_excl, 2)
        inv_total_net[inv_no] = inv_total_net.get(inv_no, 0.0) + net_item
        
    s3_lines_count = 0
    for (inv_no, s_sku), it in dedup_items.items():
        s3_lines_count += 1
        meta = inv_metadata[inv_no]
        
        # Konversi Waktu: UTC ke WIB (+7 Jam)
        # Format: 2022-08-18T21:39:16Z
        paid_dt_utc = datetime.datetime.fromisoformat(meta['paid_at'].replace('Z', '+00:00'))
        paid_dt_wib = paid_dt_utc + datetime.timedelta(hours=7)
        trx_date = paid_dt_wib.date()
        sk_waktu = int(paid_dt_wib.strftime("%Y%m%d"))
        
        # Map seller_sku ke material_no (cth: SAMSUN1005 -> P-1005)
        num_match = re.search(r'(\d{4})', s_sku)
        mat_no = f"P-{num_match.group(1)}" if num_match else s_sku
        sk_prod = prod_map.get(mat_no, 1)
        
        # Map Kanal Toko
        chan_code = 'MARKETPLACE_A' if 'marketplace_a' in meta['channel'].lower() else 'MARKETPLACE_B'
        sk_toko = toko_map.get(chan_code, 1)
        
        # Map Buyer Hash
        b_hash = meta['buyer'].get('hash')
        sk_cust = buyer_hash_map.get(b_hash, sk_anonymous) if b_hash else sk_anonymous
        sk_promo = sk_no_promo
        
        qty = int(it['qty'])
        # Harga S3 termasuk PPN 11% -> konversi ke non-PPN
        unit_price_excl = round(float(it['price']) / 1.11, 2)
        disc_excl = round(float(it['voucher']) / 1.11, 2)
        gross_excl = round(qty * unit_price_excl, 2)
        net_excl = round(gross_excl - disc_excl, 2)
        
        # Alokasi Fee Komisi Proporsional
        tot_fees = float(meta['fees'].get('commission', 0)) + float(meta['fees'].get('service', 0))
        tot_net_inv = inv_total_net.get(inv_no, 1.0)
        if tot_net_inv > 0:
            prop = net_excl / tot_net_inv
            fee_komisi = round(prop * tot_fees, 2)
        else:
            fee_komisi = 0.00
            
        cogs_unit = get_cogs(mat_no, trx_date)
        tot_cogs = round(qty * cogs_unit, 2)
        gross_margin = round(net_excl - tot_cogs - fee_komisi, 2)
        
        fact_records.append((
            sk_waktu, sk_prod, sk_toko, sk_cust, sk_promo,
            str(inv_no), 1, 'MARKETPLACE',
            qty, unit_price_excl, gross_excl, disc_excl, net_excl,
            cogs_unit, tot_cogs, fee_komisi, gross_margin
        ))
        
    print(f"     Selesai S3: {s3_lines_count} item marketplace bersih dimuat setelah deduplikasi.")
    
    # -------------------------------------------------------------
    # Insert Massal ke Tabel fact_penjualan
    # -------------------------------------------------------------
    print(f"\n  -> Menyimpan total {len(fact_records)} baris ke fact_penjualan MySQL...")
    cursor = dw_conn.cursor()
    cursor.execute("TRUNCATE TABLE fact_penjualan;")
    
    sql_fact = """
        INSERT INTO fact_penjualan
        (sk_waktu, sk_produk, sk_toko_kanal, sk_pelanggan, sk_promosi,
         no_transaksi, line_no, kanal, qty, harga_satuan_excl, nilai_kotor_excl,
         nilai_diskon_excl, nilai_bersih_excl, harga_pokok_satuan, total_harga_pokok,
         fee_komisi, margin_kotor)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
    """
    
    # Batch insert 5000 baris per batch
    batch_size = 5000
    for i in range(0, len(fact_records), batch_size):
        batch = fact_records[i:i+batch_size]
        cursor.executemany(sql_fact, batch)
        dw_conn.commit()
        print(f"     Tersimpan baris {i+1} sampai {min(i+batch_size, len(fact_records))}...")
        
    print(f"  -> Selesai: Seluruh {len(fact_records)} baris sukses dimuat ke fact_penjualan!")
    cursor.close()
    dw_conn.close()


# ====================================================================
# MAIN ENTRYPOINT
# ====================================================================
def main():
    print("====================================================================")
    print("EKSEKUSI PIPELINE DATA WAREHOUSE NUSANTARA RETAIL GROUP (NRG)")
    print("====================================================================")
    start_t = datetime.datetime.now()
    
    load_dim_waktu()
    load_dim_produk()
    load_dim_toko_kanal()
    load_dim_pelanggan()
    load_dim_promosi()
    load_fact_penjualan()
    
    end_t = datetime.datetime.now()
    dur = (end_t - start_t).total_seconds()
    print("\n====================================================================")
    print(f"ETL SELESAI DALAM {dur:.2f} DETIK. DATA WAREHOUSE SIAP DIGUNAKAN!")
    print("====================================================================")


if __name__ == '__main__':
    main()
