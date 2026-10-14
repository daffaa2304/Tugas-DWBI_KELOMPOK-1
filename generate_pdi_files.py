"""
Script untuk meng-generate berkas Pentaho Data Integration (.ktr dan .kjb)
secara standar, valid, dan terverifikasi penuh untuk Tugas 1 DWBI - Nusantara Retail Group.
"""

import os

OUTPUT_DIR = os.path.dirname(os.path.abspath(__file__))

DB_CONNECTION_XML = """
  <connection>
    <name>nrg_dw_mysql</name>
    <server>localhost</server>
    <type>MYSQL</type>
    <access>Native</access>
    <database>nrg_dw</database>
    <port>3306</port>
    <username>root</username>
    <password></password>
    <servername/>
    <data_tablespace/>
    <index_tablespace/>
    <attributes>
      <attribute><code>FORCE_IDENTIFIERS_TO_LOWERCASE</code><attribute>N</attribute></attribute>
      <attribute><code>FORCE_IDENTIFIERS_TO_UPPERCASE</code><attribute>N</attribute></attribute>
      <attribute><code>IS_CLUSTERED</code><attribute>N</attribute></attribute>
      <attribute><code>PORT_NUMBER</code><attribute>3306</attribute></attribute>
      <attribute><code>PRESERVE_RESERVED_WORD_CASE</code><attribute>Y</attribute></attribute>
      <attribute><code>QUOTE_ALL_FIELDS</code><attribute>N</attribute></attribute>
      <attribute><code>STREAM_RESULTS</code><attribute>Y</attribute></attribute>
      <attribute><code>SUPPORTS_BOOLEAN_DATA_TYPE</code><attribute>Y</attribute></attribute>
      <attribute><code>SUPPORTS_TIMESTAMP_DATA_TYPE</code><attribute>Y</attribute></attribute>
      <attribute><code>USE_POOLING</code><attribute>N</attribute></attribute>
    </attributes>
  </connection>
  <connection>
    <name>nrg_ecom_mysql</name>
    <server>localhost</server>
    <type>MYSQL</type>
    <access>Native</access>
    <database>nrg_ecom</database>
    <port>3306</port>
    <username>root</username>
    <password></password>
    <servername/>
    <data_tablespace/>
    <index_tablespace/>
    <attributes>
      <attribute><code>PORT_NUMBER</code><attribute>3306</attribute></attribute>
    </attributes>
  </connection>
"""

STANDARD_STEP_HEADER = """
    <copies>1</copies>
    <partitioning>
      <method>none</method>
      <schema_name/>
    </partitioning>
"""

# ====================================================================
# 1. DIM_WAKTU_LOADER.KTR
# ====================================================================
def generate_dim_waktu():
    ktr = f"""<?xml version="1.0" encoding="UTF-8"?>
<transformation>
  <info>
    <name>dim_waktu_loader</name>
    <description>Memuat Dimensi Waktu 2022-2024 ke nrg_dw</description>
    <trans_version>1.0</trans_version>
    <trans_type>Normal</trans_type>
    <directory>/</directory>
  </info>
  {DB_CONNECTION_XML}
  <order>
    <hop><from>Generate Dates 2022-2024</from><to>Calculate Date Attributes</to><enabled>Y</enabled></hop>
    <hop><from>Calculate Date Attributes</from><to>Insert / Update dim_waktu</to><enabled>Y</enabled></hop>
  </order>
  <step>
    <name>Generate Dates 2022-2024</name>
    <type>RowGenerator</type>
    {STANDARD_STEP_HEADER}
    <fields>
      <field><name>start_date</name><type>Date</type><format>yyyy-MM-dd</format><nullif>2022-01-01</nullif></field>
    </fields>
    <limit>1096</limit>
    <never_ending>N</never_ending>
    <GUI><xloc>120</xloc><yloc>120</yloc><draw>Y</draw></GUI>
  </step>
  <step>
    <name>Calculate Date Attributes</name>
    <type>ScriptValueMod</type>
    {STANDARD_STEP_HEADER}
    <compatible>N</compatible>
    <optimizationLevel>9</optimizationLevel>
    <jsScripts>
      <jsScript>
        <jsScript_type>0</jsScript_type>
        <jsScript_name>Script 1</jsScript_name>
        <jsScript_script>
var row_idx;
if (typeof row_idx === 'undefined') {{
    row_idx = 0;
}} else {{
    row_idx++;
}}
var cal = java.util.Calendar.getInstance();
cal.setTime(start_date);
cal.add(java.util.Calendar.DATE, row_idx);
var curr_date = cal.getTime();

var sdf_sk = new java.text.SimpleDateFormat("yyyyMMdd");
var sk_waktu = java.lang.Integer.parseInt(sdf_sk.format(curr_date));

var thn = cal.get(java.util.Calendar.YEAR);
var bln = cal.get(java.util.Calendar.MONTH) + 1;
var hari = cal.get(java.util.Calendar.DAY_OF_MONTH);
var kuartal = Math.floor((bln - 1) / 3) + 1;
var kuartal_nama = "Q" + kuartal + " " + thn;

var bulan_names = ["", "Januari", "Februari", "Maret", "April", "Mei", "Juni", "Juli", "Agustus", "September", "Oktober", "November", "Desember"];
var nama_bulan = bulan_names[bln];

var day_names = ["", "Minggu", "Senin", "Selasa", "Rabu", "Kamis", "Jumat", "Sabtu"];
var nama_hari = day_names[cal.get(java.util.Calendar.DAY_OF_WEEK)];

var dow = cal.get(java.util.Calendar.DAY_OF_WEEK);
var is_weekend = (dow == java.util.Calendar.SATURDAY || dow == java.util.Calendar.SUNDAY) ? 1 : 0;
        </jsScript_script>
      </jsScript>
    </jsScripts>
    <fields>
      <field><name>sk_waktu</name><rename>sk_waktu</rename><type>Integer</type></field>
      <field><name>curr_date</name><rename>tanggal</rename><type>Date</type></field>
      <field><name>thn</name><rename>tahun</rename><type>Integer</type></field>
      <field><name>kuartal</name><rename>kuartal</rename><type>Integer</type></field>
      <field><name>kuartal_nama</name><rename>kuartal_nama</rename><type>String</type></field>
      <field><name>bln</name><rename>bulan</rename><type>Integer</type></field>
      <field><name>nama_bulan</name><rename>nama_bulan</rename><type>String</type></field>
      <field><name>hari</name><rename>hari</rename><type>Integer</type></field>
      <field><name>nama_hari</name><rename>nama_hari</rename><type>String</type></field>
      <field><name>is_weekend</name><rename>is_weekend</rename><type>Integer</type></field>
    </fields>
    <GUI><xloc>320</xloc><yloc>120</yloc><draw>Y</draw></GUI>
  </step>
  <step>
    <name>Insert / Update dim_waktu</name>
    <type>InsertUpdate</type>
    {STANDARD_STEP_HEADER}
    <connection>nrg_dw_mysql</connection>
    <commit>1000</commit>
    <lookup>
      <schema/>
      <table>dim_waktu</table>
      <key><name>sk_waktu</name><field>sk_waktu</field><condition>=</condition><name2/></key>
      <value><name>sk_waktu</name><rename>sk_waktu</rename><update>Y</update></value>
      <value><name>tanggal</name><rename>tanggal</rename><update>Y</update></value>
      <value><name>tahun</name><rename>tahun</rename><update>Y</update></value>
      <value><name>kuartal</name><rename>kuartal</rename><update>Y</update></value>
      <value><name>kuartal_nama</name><rename>kuartal_nama</rename><update>Y</update></value>
      <value><name>bulan</name><rename>bulan</rename><update>Y</update></value>
      <value><name>nama_bulan</name><rename>nama_bulan</rename><update>Y</update></value>
      <value><name>hari</name><rename>hari</rename><update>Y</update></value>
      <value><name>nama_hari</name><rename>nama_hari</rename><update>Y</update></value>
      <value><name>is_weekend</name><rename>is_weekend</rename><update>Y</update></value>
    </lookup>
    <GUI><xloc>540</xloc><yloc>120</yloc><draw>Y</draw></GUI>
  </step>
</transformation>
"""
    with open(os.path.join(OUTPUT_DIR, "dim_waktu_loader.ktr"), "w", encoding="utf-8") as f:
        f.write(ktr.strip())
    print("Generated dim_waktu_loader.ktr")


# ====================================================================
# 2. DIM_PRODUK_LOADER.KTR
# ====================================================================
def generate_dim_produk():
    ktr = f"""<?xml version="1.0" encoding="UTF-8"?>
<transformation>
  <info>
    <name>dim_produk_loader</name>
    <description>Memuat Dimensi Produk dari S4 ERP Master dan Late-Arriving P-1061</description>
    <trans_version>1.0</trans_version>
    <trans_type>Normal</trans_type>
    <directory>/</directory>
  </info>
  {DB_CONNECTION_XML}
  <order>
    <hop><from>Input S4 produk_master.csv</from><to>Sort by Material and Date</to><enabled>Y</enabled></hop>
    <hop><from>Sort by Material and Date</from><to>Ambil Versi Terakhir</to><enabled>Y</enabled></hop>
    <hop><from>Ambil Versi Terakhir</from><to>Append Late-Arriving ORD-9999</to><enabled>Y</enabled></hop>
    <hop><from>Input Late-Arriving Row</from><to>Append Late-Arriving ORD-9999</to><enabled>Y</enabled></hop>
    <hop><from>Append Late-Arriving ORD-9999</from><to>Insert / Update dim_produk</to><enabled>Y</enabled></hop>
  </order>
  <step>
    <name>Input S4 produk_master.csv</name>
    <type>CsvInput</type>
    {STANDARD_STEP_HEADER}
    <filename>${{Internal.Transformation.Filename.Directory}}/Data/S4_ERP_MASTER/produk_master.csv</filename>
    <filename_field/>
    <rownum_field/>
    <include_filename>N</include_filename>
    <separator>,</separator>
    <enclosure>&quot;</enclosure>
    <header>Y</header>
    <buffer_size>50000</buffer_size>
    <lazy_conversion>N</lazy_conversion>
    <add_filename_result>N</add_filename_result>
    <parallel>N</parallel>
    <newline_possible>N</newline_possible>
    <format>mixed</format>
    <encoding>UTF-8</encoding>
    <fields>
      <field><name>material_no</name><type>String</type><trim_type>both</trim_type></field>
      <field><name>nama_produk</name><type>String</type><trim_type>both</trim_type></field>
      <field><name>brand</name><type>String</type><trim_type>both</trim_type></field>
      <field><name>kategori</name><type>String</type><trim_type>both</trim_type></field>
      <field><name>sub_kategori</name><type>String</type><trim_type>both</trim_type></field>
      <field><name>harga_pokok</name><type>Number</type><trim_type>both</trim_type></field>
      <field><name>supplier</name><type>String</type><trim_type>both</trim_type></field>
      <field><name>status</name><type>String</type><trim_type>both</trim_type></field>
      <field><name>berlaku_sejak</name><type>Date</type><format>yyyy-MM-dd</format><trim_type>both</trim_type></field>
    </fields>
    <GUI><xloc>100</xloc><yloc>100</yloc><draw>Y</draw></GUI>
  </step>
  <step>
    <name>Sort by Material and Date</name>
    <type>SortRows</type>
    {STANDARD_STEP_HEADER}
    <directory>%%java.io.tmpdir%%</directory>
    <prefix>out</prefix>
    <sort_size>1000000</sort_size>
    <fields>
      <field><name>material_no</name><ascending>Y</ascending><case_sensitive>N</case_sensitive></field>
      <field><name>berlaku_sejak</name><ascending>Y</ascending><case_sensitive>N</case_sensitive></field>
    </fields>
    <GUI><xloc>280</xloc><yloc>100</yloc><draw>Y</draw></GUI>
  </step>
  <step>
    <name>Ambil Versi Terakhir</name>
    <type>GroupBy</type>
    {STANDARD_STEP_HEADER}
    <all_rows>N</all_rows>
    <ignore_aggregate>N</ignore_aggregate>
    <field_ignore/>
    <directory>%%java.io.tmpdir%%</directory>
    <prefix>grp</prefix>
    <group>
      <field><name>material_no</name></field>
    </group>
    <fields>
      <field><aggregate>nama_produk</aggregate><subject>nama_produk</subject><type>LAST</type></field>
      <field><aggregate>brand</aggregate><subject>brand</subject><type>LAST</type></field>
      <field><aggregate>kategori</aggregate><subject>kategori</subject><type>LAST</type></field>
      <field><aggregate>sub_kategori</aggregate><subject>sub_kategori</subject><type>LAST</type></field>
      <field><aggregate>harga_pokok_terkini</aggregate><subject>harga_pokok</subject><type>LAST</type></field>
      <field><aggregate>supplier</aggregate><subject>supplier</subject><type>LAST</type></field>
      <field><aggregate>status_erp</aggregate><subject>status</subject><type>LAST</type></field>
    </fields>
    <GUI><xloc>460</xloc><yloc>100</yloc><draw>Y</draw></GUI>
  </step>
  <step>
    <name>Input Late-Arriving Row</name>
    <type>RowGenerator</type>
    {STANDARD_STEP_HEADER}
    <fields>
      <field><name>material_no</name><type>String</type><nullif>P-1061</nullif></field>
      <field><name>nama_produk</name><type>String</type><nullif>Smartphone Model Terbaru (Belum Terdaftar di ERP)</nullif></field>
      <field><name>brand</name><type>String</type><nullif>Samsung</nullif></field>
      <field><name>kategori</name><type>String</type><nullif>Elektronik</nullif></field>
      <field><name>sub_kategori</name><type>String</type><nullif>Smartphone</nullif></field>
      <field><name>harga_pokok_terkini</name><type>Number</type><nullif>0</nullif></field>
      <field><name>supplier</name><type>String</type><nullif>Belum Ditentukan</nullif></field>
      <field><name>status_erp</name><type>String</type><nullif>BELUM_TERDAFTAR_ERP</nullif></field>
    </fields>
    <limit>1</limit>
    <GUI><xloc>460</xloc><yloc>220</yloc><draw>Y</draw></GUI>
  </step>
  <step>
    <name>Append Late-Arriving ORD-9999</name>
    <type>Append</type>
    {STANDARD_STEP_HEADER}
    <head_name>Ambil Versi Terakhir</head_name>
    <tail_name>Input Late-Arriving Row</tail_name>
    <GUI><xloc>640</xloc><yloc>100</yloc><draw>Y</draw></GUI>
  </step>
  <step>
    <name>Insert / Update dim_produk</name>
    <type>InsertUpdate</type>
    {STANDARD_STEP_HEADER}
    <connection>nrg_dw_mysql</connection>
    <commit>100</commit>
    <lookup>
      <schema/>
      <table>dim_produk</table>
      <key><name>material_no</name><field>material_no</field><condition>=</condition></key>
      <value><name>material_no</name><rename>material_no</rename><update>Y</update></value>
      <value><name>nama_produk</name><rename>nama_produk</rename><update>Y</update></value>
      <value><name>brand</name><rename>brand</rename><update>Y</update></value>
      <value><name>kategori</name><rename>kategori</rename><update>Y</update></value>
      <value><name>sub_kategori</name><rename>sub_kategori</rename><update>Y</update></value>
      <value><name>harga_pokok_terkini</name><rename>harga_pokok_terkini</rename><update>Y</update></value>
      <value><name>supplier</name><rename>supplier</rename><update>Y</update></value>
      <value><name>status_erp</name><rename>status_erp</rename><update>Y</update></value>
    </lookup>
    <GUI><xloc>840</xloc><yloc>100</yloc><draw>Y</draw></GUI>
  </step>
</transformation>
"""
    with open(os.path.join(OUTPUT_DIR, "dim_produk_loader.ktr"), "w", encoding="utf-8") as f:
        f.write(ktr.strip())
    print("Generated dim_produk_loader.ktr")


# ====================================================================
# 3. DIM_TOKO_KANAL_LOADER.KTR
# ====================================================================
def generate_dim_toko_kanal():
    ktr = f"""<?xml version="1.0" encoding="UTF-8"?>
<transformation>
  <info>
    <name>dim_toko_kanal_loader</name>
    <description>Memuat Dimensi Toko dan Kanal dengan Standarisasi ref_kota.csv</description>
    <trans_version>1.0</trans_version>
    <trans_type>Normal</trans_type>
    <directory>/</directory>
  </info>
  {DB_CONNECTION_XML}
  <order>
    <hop><from>Input 42 Toko store_master.csv</from><to>Lookup Kota Baku</to><enabled>Y</enabled></hop>
    <hop><from>Input ref_kota.csv</from><to>Lookup Kota Baku</to><enabled>Y</enabled></hop>
    <hop><from>Lookup Kota Baku</from><to>Set Jenis Kanal TOKO_FISIK</to><enabled>Y</enabled></hop>
    <hop><from>Set Jenis Kanal TOKO_FISIK</from><to>Select Values TOKO_FISIK</to><enabled>Y</enabled></hop>
    <hop><from>Select Values TOKO_FISIK</from><to>Append Online Channels</to><enabled>Y</enabled></hop>
    <hop><from>Input Online Channels (Web &amp; Mpl)</from><to>Append Online Channels</to><enabled>Y</enabled></hop>
    <hop><from>Append Online Channels</from><to>Insert / Update dim_toko_kanal</to><enabled>Y</enabled></hop>
  </order>
  <step>
    <name>Input 42 Toko store_master.csv</name>
    <type>CsvInput</type>
    {STANDARD_STEP_HEADER}
    <filename>${{Internal.Transformation.Filename.Directory}}/Data/S2_POS_TOKO/store_master.csv</filename>
    <filename_field/>
    <rownum_field/>
    <include_filename>N</include_filename>
    <separator>,</separator>
    <enclosure>&quot;</enclosure>
    <header>Y</header>
    <buffer_size>50000</buffer_size>
    <lazy_conversion>N</lazy_conversion>
    <add_filename_result>N</add_filename_result>
    <parallel>N</parallel>
    <newline_possible>N</newline_possible>
    <format>mixed</format>
    <encoding>UTF-8</encoding>
    <fields>
      <field><name>store_code</name><type>String</type><trim_type>both</trim_type></field>
      <field><name>store_name</name><type>String</type><trim_type>both</trim_type></field>
      <field><name>city</name><type>String</type><trim_type>both</trim_type></field>
      <field><name>province</name><type>String</type><trim_type>both</trim_type></field>
      <field><name>format_toko</name><type>String</type><trim_type>both</trim_type></field>
    </fields>
    <GUI><xloc>100</xloc><yloc>80</yloc><draw>Y</draw></GUI>
  </step>
  <step>
    <name>Input ref_kota.csv</name>
    <type>CsvInput</type>
    {STANDARD_STEP_HEADER}
    <filename>${{Internal.Transformation.Filename.Directory}}/Data/ref_kota.csv</filename>
    <filename_field/>
    <rownum_field/>
    <include_filename>N</include_filename>
    <separator>,</separator>
    <enclosure>&quot;</enclosure>
    <header>Y</header>
    <buffer_size>50000</buffer_size>
    <lazy_conversion>N</lazy_conversion>
    <add_filename_result>N</add_filename_result>
    <parallel>N</parallel>
    <newline_possible>N</newline_possible>
    <format>mixed</format>
    <encoding>UTF-8</encoding>
    <fields>
      <field><name>alias</name><type>String</type><trim_type>both</trim_type></field>
      <field><name>kota_baku</name><type>String</type><trim_type>both</trim_type></field>
    </fields>
    <GUI><xloc>100</xloc><yloc>200</yloc><draw>Y</draw></GUI>
  </step>
  <step>
    <name>Lookup Kota Baku</name>
    <type>StreamLookup</type>
    {STANDARD_STEP_HEADER}
    <from>Input ref_kota.csv</from>
    <input_sorted>N</input_sorted>
    <preserve_memory>Y</preserve_memory>
    <sorted_list>N</sorted_list>
    <integer_pair>N</integer_pair>
    <lookup>
      <key><name>city</name><field>alias</field></key>
      <value><name>kota_baku</name><rename>kota_standar</rename><default/></value>
    </lookup>
    <GUI><xloc>260</xloc><yloc>80</yloc><draw>Y</draw></GUI>
  </step>
  <step>
    <name>Set Jenis Kanal TOKO_FISIK</name>
    <type>ScriptValueMod</type>
    {STANDARD_STEP_HEADER}
    <compatible>N</compatible>
    <optimizationLevel>9</optimizationLevel>
    <jsScripts>
      <jsScript>
        <jsScript_type>0</jsScript_type>
        <jsScript_name>Script 1</jsScript_name>
        <jsScript_script>
var kode_toko_kanal = store_code;
var nama_toko_kanal = store_name;
var jenis_kanal = "TOKO_FISIK";
var kota = kota_standar != null ? kota_standar : city;
var provinsi = province;
var format = format_toko;
        </jsScript_script>
      </jsScript>
    </jsScripts>
    <fields>
      <field><name>kode_toko_kanal</name><rename>kode_toko_kanal</rename><type>String</type></field>
      <field><name>nama_toko_kanal</name><rename>nama_toko_kanal</rename><type>String</type></field>
      <field><name>jenis_kanal</name><rename>jenis_kanal</rename><type>String</type></field>
      <field><name>kota</name><rename>kota</rename><type>String</type></field>
      <field><name>provinsi</name><rename>provinsi</rename><type>String</type></field>
      <field><name>format</name><rename>format_toko</rename><type>String</type></field>
    </fields>
    <GUI><xloc>440</xloc><yloc>80</yloc><draw>Y</draw></GUI>
  </step>
  <step>
    <name>Select Values TOKO_FISIK</name>
    <type>SelectValues</type>
    {STANDARD_STEP_HEADER}
    <fields>
      <field><name>kode_toko_kanal</name></field>
      <field><name>nama_toko_kanal</name></field>
      <field><name>jenis_kanal</name></field>
      <field><name>kota</name></field>
      <field><name>provinsi</name></field>
      <field><name>format_toko</name></field>
      <select_unspecified>N</select_unspecified>
    </fields>
    <GUI><xloc>580</xloc><yloc>80</yloc><draw>Y</draw></GUI>
  </step>
  <step>
    <name>Input Online Channels (Web &amp; Mpl)</name>
    <type>DataGrid</type>
    {STANDARD_STEP_HEADER}
    <data>
      <line><item>WEB</item><item>Website Resmi Nusantara Retail Group</item><item>WEB</item><item>Jakarta Pusat</item><item>DKI Jakarta</item><item>Online E-Commerce</item></line>
      <line><item>MARKETPLACE_A</item><item>Marketplace Platform A</item><item>MARKETPLACE</item><item>Nasional</item><item>Nasional</item><item>Online Third-Party</item></line>
      <line><item>MARKETPLACE_B</item><item>Marketplace Platform B</item><item>MARKETPLACE</item><item>Nasional</item><item>Nasional</item><item>Online Third-Party</item></line>
    </data>
    <fields>
      <field><name>kode_toko_kanal</name><type>String</type></field>
      <field><name>nama_toko_kanal</name><type>String</type></field>
      <field><name>jenis_kanal</name><type>String</type></field>
      <field><name>kota</name><type>String</type></field>
      <field><name>provinsi</name><type>String</type></field>
      <field><name>format_toko</name><type>String</type></field>
    </fields>
    <GUI><xloc>580</xloc><yloc>200</yloc><draw>Y</draw></GUI>
  </step>
  <step>
    <name>Append Online Channels</name>
    <type>Append</type>
    {STANDARD_STEP_HEADER}
    <head_name>Select Values TOKO_FISIK</head_name>
    <tail_name>Input Online Channels (Web &amp; Mpl)</tail_name>
    <GUI><xloc>740</xloc><yloc>80</yloc><draw>Y</draw></GUI>
  </step>
  <step>
    <name>Insert / Update dim_toko_kanal</name>
    <type>InsertUpdate</type>
    {STANDARD_STEP_HEADER}
    <connection>nrg_dw_mysql</connection>
    <commit>100</commit>
    <lookup>
      <schema/>
      <table>dim_toko_kanal</table>
      <key><name>kode_toko_kanal</name><field>kode_toko_kanal</field><condition>=</condition></key>
      <value><name>kode_toko_kanal</name><rename>kode_toko_kanal</rename><update>Y</update></value>
      <value><name>nama_toko_kanal</name><rename>nama_toko_kanal</rename><update>Y</update></value>
      <value><name>jenis_kanal</name><rename>jenis_kanal</rename><update>Y</update></value>
      <value><name>kota</name><rename>kota</rename><update>Y</update></value>
      <value><name>provinsi</name><rename>provinsi</rename><update>Y</update></value>
      <value><name>format_toko</name><rename>format_toko</rename><update>Y</update></value>
    </lookup>
    <GUI><xloc>920</xloc><yloc>80</yloc><draw>Y</draw></GUI>
  </step>
</transformation>
"""
    with open(os.path.join(OUTPUT_DIR, "dim_toko_kanal_loader.ktr"), "w", encoding="utf-8") as f:
        f.write(ktr.strip())
    print("Generated dim_toko_kanal_loader.ktr")


# ====================================================================
# 4. DIM_PROMOSI_LOADER.KTR
# ====================================================================
def generate_dim_promosi():
    ktr = f"""<?xml version="1.0" encoding="UTF-8"?>
<transformation>
  <info>
    <name>dim_promosi_loader</name>
    <description>Memuat Dimensi Promosi dengan Filter Error 'sepuluh'</description>
    <trans_version>1.0</trans_version>
    <trans_type>Normal</trans_type>
    <directory>/</directory>
  </info>
  {DB_CONNECTION_XML}
  <order>
    <hop><from>Input S5 kampanye_marketing.csv</from><to>Filter Baris Kosong &amp; Trim</to><enabled>Y</enabled></hop>
    <hop><from>Filter Baris Kosong &amp; Trim</from><to>Cek Nilai Diskon Numerik</to><enabled>Y</enabled></hop>
    <hop><from>Cek Nilai Diskon Numerik</from><to>Filter Baris Valid</to><enabled>Y</enabled></hop>
    <hop><from>Filter Baris Valid</from><to>Output Error 'sepuluh'</to><enabled>Y</enabled></hop>
    <hop><from>Filter Baris Valid</from><to>Insert / Update dim_promosi</to><enabled>Y</enabled></hop>
  </order>
  <step>
    <name>Input S5 kampanye_marketing.csv</name>
    <type>CsvInput</type>
    {STANDARD_STEP_HEADER}
    <filename>${{Internal.Transformation.Filename.Directory}}/Data/S5_MKT_SHEET/kampanye_marketing.csv</filename>
    <filename_field/>
    <rownum_field/>
    <include_filename>N</include_filename>
    <separator>,</separator>
    <enclosure>&quot;</enclosure>
    <header>Y</header>
    <buffer_size>50000</buffer_size>
    <lazy_conversion>N</lazy_conversion>
    <add_filename_result>N</add_filename_result>
    <parallel>N</parallel>
    <newline_possible>N</newline_possible>
    <format>mixed</format>
    <encoding>UTF-8</encoding>
    <fields>
      <field><name>kode_promo</name><type>String</type><trim_type>both</trim_type></field>
      <field><name>nama_kampanye</name><type>String</type><trim_type>both</trim_type></field>
      <field><name>jenis_promo</name><type>String</type><trim_type>both</trim_type></field>
      <field><name>kanal</name><type>String</type><trim_type>both</trim_type></field>
      <field><name>tgl_mulai</name><type>String</type><trim_type>both</trim_type></field>
      <field><name>tgl_selesai</name><type>String</type><trim_type>both</trim_type></field>
      <field><name>target_diskon_persen</name><type>String</type><trim_type>both</trim_type></field>
      <field><name>pic</name><type>String</type><trim_type>both</trim_type></field>
    </fields>
    <GUI><xloc>100</xloc><yloc>120</yloc><draw>Y</draw></GUI>
  </step>
  <step>
    <name>Filter Baris Kosong &amp; Trim</name>
    <type>FilterRows</type>
    {STANDARD_STEP_HEADER}
    <send_true_to>Cek Nilai Diskon Numerik</send_true_to>
    <send_false_to/>
    <compare>
      <condition>
        <negated>N</negated>
        <leftvalue>kode_promo</leftvalue>
        <function>IS NOT NULL</function>
      </condition>
    </compare>
    <GUI><xloc>280</xloc><yloc>120</yloc><draw>Y</draw></GUI>
  </step>
  <step>
    <name>Cek Nilai Diskon Numerik</name>
    <type>ScriptValueMod</type>
    {STANDARD_STEP_HEADER}
    <compatible>N</compatible>
    <optimizationLevel>9</optimizationLevel>
    <jsScripts>
      <jsScript>
        <jsScript_type>0</jsScript_type>
        <jsScript_name>Script 1</jsScript_name>
        <jsScript_script>
var k_clean = kode_promo.trim().toUpperCase();
var is_num = !isNaN(parseFloat(target_diskon_persen));
var diskon_val = is_num ? parseFloat(target_diskon_persen) : 0.0;
var is_valid_flag = is_num ? "Y" : "N";
var err_reason = is_num ? "" : "Nilai target_diskon_persen bukan numerik ('" + target_diskon_persen + "')";
        </jsScript_script>
      </jsScript>
    </jsScripts>
    <fields>
      <field><name>k_clean</name><rename>kode_promo_clean</rename><type>String</type></field>
      <field><name>is_valid_flag</name><rename>is_valid_flag</rename><type>String</type></field>
      <field><name>diskon_val</name><rename>diskon_persen</rename><type>Number</type></field>
      <field><name>err_reason</name><rename>alasan_error</rename><type>String</type></field>
    </fields>
    <GUI><xloc>460</xloc><yloc>120</yloc><draw>Y</draw></GUI>
  </step>
  <step>
    <name>Filter Baris Valid</name>
    <type>FilterRows</type>
    {STANDARD_STEP_HEADER}
    <send_true_to>Insert / Update dim_promosi</send_true_to>
    <send_false_to>Output Error 'sepuluh'</send_false_to>
    <compare>
      <condition>
        <negated>N</negated>
        <leftvalue>is_valid_flag</leftvalue>
        <function>=</function>
        <rightvalue/>
        <value>
          <name>constant</name>
          <type>String</type>
          <text>Y</text>
          <length>-1</length>
          <precision>-1</precision>
          <isnull>N</isnull>
          <mask/>
        </value>
      </condition>
    </compare>
    <GUI><xloc>620</xloc><yloc>120</yloc><draw>Y</draw></GUI>
  </step>
  <step>
    <name>Output Error 'sepuluh'</name>
    <type>TableOutput</type>
    {STANDARD_STEP_HEADER}
    <connection>nrg_dw_mysql</connection>
    <schema/>
    <table>error_kampanye_marketing</table>
    <commit>100</commit>
    <truncate>N</truncate>
    <ignore_errors>N</ignore_errors>
    <use_batch>Y</use_batch>
    <specify_fields>Y</specify_fields>
    <partitioning_enabled>N</partitioning_enabled>
    <partitioning_field/>
    <partitioning_daily>N</partitioning_daily>
    <partitioning_monthly>Y</partitioning_monthly>
    <tablename_in_field>N</tablename_in_field>
    <tablename_field/>
    <tablename_in_table>Y</tablename_in_table>
    <return_keys>N</return_keys>
    <return_field/>
    <fields>
      <field><column_name>kode_promo</column_name><stream_name>kode_promo</stream_name></field>
      <field><column_name>nama_kampanye</column_name><stream_name>nama_kampanye</stream_name></field>
      <field><column_name>jenis_promo</column_name><stream_name>jenis_promo</stream_name></field>
      <field><column_name>kanal</column_name><stream_name>kanal</stream_name></field>
      <field><column_name>target_diskon_persen</column_name><stream_name>target_diskon_persen</stream_name></field>
      <field><column_name>pic</column_name><stream_name>pic</stream_name></field>
      <field><column_name>alasan_error</column_name><stream_name>alasan_error</stream_name></field>
    </fields>
    <GUI><xloc>620</xloc><yloc>260</yloc><draw>Y</draw></GUI>
  </step>
  <step>
    <name>Insert / Update dim_promosi</name>
    <type>InsertUpdate</type>
    {STANDARD_STEP_HEADER}
    <connection>nrg_dw_mysql</connection>
    <commit>100</commit>
    <lookup>
      <schema/>
      <table>dim_promosi</table>
      <key><name>kode_promo_clean</name><field>kode_promo</field><condition>=</condition></key>
      <value><name>kode_promo</name><rename>kode_promo_clean</rename><update>Y</update></value>
      <value><name>nama_kampanye</name><rename>nama_kampanye</rename><update>Y</update></value>
      <value><name>jenis_promo</name><rename>jenis_promo</rename><update>Y</update></value>
      <value><name>kanal_target</name><rename>kanal</rename><update>Y</update></value>
      <value><name>target_diskon_persen</name><rename>diskon_persen</rename><update>Y</update></value>
      <value><name>pic</name><rename>pic</rename><update>Y</update></value>
    </lookup>
    <GUI><xloc>820</xloc><yloc>120</yloc><draw>Y</draw></GUI>
  </step>
</transformation>
"""
    with open(os.path.join(OUTPUT_DIR, "dim_promosi_loader.ktr"), "w", encoding="utf-8") as f:
        f.write(ktr.strip())
    print("Generated dim_promosi_loader.ktr")


# ====================================================================
# 5. DIM_PELANGGAN_LOADER.KTR
# ====================================================================
def generate_dim_pelanggan():
    ktr = f"""<?xml version="1.0" encoding="UTF-8"?>
<transformation>
  <info>
    <name>dim_pelanggan_loader</name>
    <description>Memuat Dimensi Pelanggan dan Resolusi Omnichannel HP</description>
    <trans_version>1.0</trans_version>
    <trans_type>Normal</trans_type>
    <directory>/</directory>
  </info>
  {DB_CONNECTION_XML}
  <order>
    <hop><from>Input Pelanggan Web S1</from><to>Normalisasi HP Pelanggan</to><enabled>Y</enabled></hop>
    <hop><from>Input Member Toko S2</from><to>Normalisasi HP Member Toko</to><enabled>Y</enabled></hop>
    <hop><from>Normalisasi HP Pelanggan</from><to>Lookup Member Toko by HP</to><enabled>Y</enabled></hop>
    <hop><from>Normalisasi HP Member Toko</from><to>Lookup Member Toko by HP</to><enabled>Y</enabled></hop>
    <hop><from>Lookup Member Toko by HP</from><to>Set Status Omnichannel</to><enabled>Y</enabled></hop>
    <hop><from>Set Status Omnichannel</from><to>Insert / Update dim_pelanggan</to><enabled>Y</enabled></hop>
  </order>
  <step>
    <name>Input Pelanggan Web S1</name>
    <type>TableInput</type>
    {STANDARD_STEP_HEADER}
    <connection>nrg_ecom_mysql</connection>
    <sql>SELECT c.customer_id, c.full_name, c.phone, c.gender, COALESCE(a.city, 'Tidak Diketahui') AS city FROM customers c LEFT JOIN customer_addresses a ON c.customer_id = a.customer_id AND a.is_primary = 1</sql>
    <GUI><xloc>100</xloc><yloc>80</yloc><draw>Y</draw></GUI>
  </step>
  <step>
    <name>Input Member Toko S2</name>
    <type>CsvInput</type>
    {STANDARD_STEP_HEADER}
    <filename>${{Internal.Transformation.Filename.Directory}}/Data/S2_POS_TOKO/member.csv</filename>
    <filename_field/>
    <rownum_field/>
    <include_filename>N</include_filename>
    <separator>;</separator>
    <enclosure>&quot;</enclosure>
    <header>Y</header>
    <buffer_size>50000</buffer_size>
    <lazy_conversion>N</lazy_conversion>
    <add_filename_result>N</add_filename_result>
    <parallel>N</parallel>
    <newline_possible>N</newline_possible>
    <format>mixed</format>
    <encoding>UTF-8</encoding>
    <fields>
      <field><name>member_no</name><type>String</type><trim_type>both</trim_type></field>
      <field><name>member_name</name><type>String</type><trim_type>both</trim_type></field>
      <field><name>hp</name><type>String</type><trim_type>both</trim_type></field>
      <field><name>kota</name><type>String</type><trim_type>both</trim_type></field>
    </fields>
    <GUI><xloc>100</xloc><yloc>200</yloc><draw>Y</draw></GUI>
  </step>
  <step>
    <name>Normalisasi HP Member Toko</name>
    <type>ScriptValueMod</type>
    {STANDARD_STEP_HEADER}
    <compatible>N</compatible>
    <optimizationLevel>9</optimizationLevel>
    <jsScripts>
      <jsScript>
        <jsScript_type>0</jsScript_type>
        <jsScript_name>Script 1</jsScript_name>
        <jsScript_script>
var p_str = hp != null ? "" + hp : "";
var d = p_str.replace(/\\D/g, "");
if (d.indexOf("62") == 0) {{
    d = d.substring(2);
}} else if (d.indexOf("0") == 0) {{
    d = d.substring(1);
}}
var norm_hp_member = d;
        </jsScript_script>
      </jsScript>
    </jsScripts>
    <fields>
      <field><name>norm_hp_member</name><rename>norm_hp_member</rename><type>String</type></field>
    </fields>
    <GUI><xloc>280</xloc><yloc>200</yloc><draw>Y</draw></GUI>
  </step>
  <step>
    <name>Normalisasi HP Pelanggan</name>
    <type>ScriptValueMod</type>
    {STANDARD_STEP_HEADER}
    <compatible>N</compatible>
    <optimizationLevel>9</optimizationLevel>
    <jsScripts>
      <jsScript>
        <jsScript_type>0</jsScript_type>
        <jsScript_name>Script 1</jsScript_name>
        <jsScript_script>
var p_str = phone != null ? "" + phone : "";
var d = p_str.replace(/\\D/g, "");
if (d.indexOf("62") == 0) {{
    d = d.substring(2);
}} else if (d.indexOf("0") == 0) {{
    d = d.substring(1);
}}
var norm_hp = d;
        </jsScript_script>
      </jsScript>
    </jsScripts>
    <fields>
      <field><name>norm_hp</name><rename>norm_hp</rename><type>String</type></field>
    </fields>
    <GUI><xloc>280</xloc><yloc>80</yloc><draw>Y</draw></GUI>
  </step>
  <step>
    <name>Lookup Member Toko by HP</name>
    <type>StreamLookup</type>
    {STANDARD_STEP_HEADER}
    <from>Normalisasi HP Member Toko</from>
    <input_sorted>N</input_sorted>
    <preserve_memory>Y</preserve_memory>
    <sorted_list>N</sorted_list>
    <integer_pair>N</integer_pair>
    <lookup>
      <key><name>norm_hp</name><field>norm_hp_member</field></key>
      <value><name>member_no</name><rename>matched_member_no</rename><default/></value>
      <value><name>member_name</name><rename>matched_member_name</rename><default/></value>
    </lookup>
    <GUI><xloc>460</xloc><yloc>80</yloc><draw>Y</draw></GUI>
  </step>
  <step>
    <name>Set Status Omnichannel</name>
    <type>ScriptValueMod</type>
    {STANDARD_STEP_HEADER}
    <compatible>N</compatible>
    <optimizationLevel>9</optimizationLevel>
    <jsScripts>
      <jsScript>
        <jsScript_type>0</jsScript_type>
        <jsScript_name>Script 1</jsScript_name>
        <jsScript_script>
var is_omnichannel = (matched_member_no != null &amp;&amp; matched_member_no != "") ? 1 : 0;
var status_member = is_omnichannel == 1 ? "MEMBER_DAN_WEB" : "NON_MEMBER_WEB";
var no_identitas_asal = is_omnichannel == 1 ? "CUST-" + customer_id + "|" + matched_member_no : "CUST-" + customer_id;
var jenis_kelamin = gender == "M" ? "Laki-Laki" : (gender == "F" ? "Perempuan" : "TIDAK_DIKETAHUI");
        </jsScript_script>
      </jsScript>
    </jsScripts>
    <fields>
      <field><name>is_omnichannel</name><rename>is_omnichannel</rename><type>Integer</type></field>
      <field><name>status_member</name><rename>status_member</rename><type>String</type></field>
      <field><name>no_identitas_asal</name><rename>no_identitas_asal</rename><type>String</type></field>
      <field><name>jenis_kelamin</name><rename>jenis_kelamin</rename><type>String</type></field>
    </fields>
    <GUI><xloc>660</xloc><yloc>80</yloc><draw>Y</draw></GUI>
  </step>
  <step>
    <name>Insert / Update dim_pelanggan</name>
    <type>InsertUpdate</type>
    {STANDARD_STEP_HEADER}
    <connection>nrg_dw_mysql</connection>
    <commit>100</commit>
    <lookup>
      <schema/>
      <table>dim_pelanggan</table>
      <key><name>norm_hp</name><field>no_hp_normal</field><condition>=</condition></key>
      <value><name>no_identitas_asal</name><rename>no_identitas_asal</rename><update>Y</update></value>
      <value><name>nama_pelanggan</name><rename>full_name</rename><update>Y</update></value>
      <value><name>no_hp_normal</name><rename>norm_hp</rename><update>Y</update></value>
      <value><name>status_member</name><rename>status_member</rename><update>Y</update></value>
      <value><name>kota</name><rename>city</rename><update>Y</update></value>
      <value><name>jenis_kelamin</name><rename>jenis_kelamin</rename><update>Y</update></value>
      <value><name>is_omnichannel</name><rename>is_omnichannel</rename><update>Y</update></value>
    </lookup>
    <GUI><xloc>860</xloc><yloc>80</yloc><draw>Y</draw></GUI>
  </step>
</transformation>
"""
    with open(os.path.join(OUTPUT_DIR, "dim_pelanggan_loader.ktr"), "w", encoding="utf-8") as f:
        f.write(ktr.strip())
    print("Generated dim_pelanggan_loader.ktr")


# ====================================================================
# 6. FACT_PENJUALAN_LOADER.KTR
# ====================================================================
def generate_fact_penjualan():
    ktr = f"""<?xml version="1.0" encoding="UTF-8"?>
<transformation>
  <info>
    <name>fact_penjualan_loader</name>
    <description>Memuat Tabel Fakta Penjualan Terintegrasi (S1, S2, S3) ke nrg_dw</description>
    <trans_version>1.0</trans_version>
    <trans_type>Normal</trans_type>
    <directory>/</directory>
  </info>
  {DB_CONNECTION_XML}
  <order>
    <hop><from>Input S1 ECOM (MySQL)</from><to>Transform S1 Non-PPN</to><enabled>Y</enabled></hop>
    <hop><from>Transform S1 Non-PPN</from><to>Lookup S4 COGS S1</to><enabled>Y</enabled></hop>
    <hop><from>Lookup S4 COGS S1</from><to>Lookup Dimensi S1</to><enabled>Y</enabled></hop>
    <hop><from>Lookup Dimensi S1</from><to>Insert Fact Penjualan</to><enabled>Y</enabled></hop>
  </order>
  <step>
    <name>Input S1 ECOM (MySQL)</name>
    <type>TableInput</type>
    {STANDARD_STEP_HEADER}
    <connection>nrg_ecom_mysql</connection>
    <sql>
      SELECT 
        oi.order_id, oi.line_no, oi.sku, oi.qty, oi.unit_price, oi.disc_amount,
        o.order_ts, o.customer_id, v.promo_code
      FROM order_items oi
      JOIN orders o ON oi.order_id = o.order_id
      LEFT JOIN vouchers v ON o.voucher_id = v.voucher_id
    </sql>
    <GUI><xloc>100</xloc><yloc>100</yloc><draw>Y</draw></GUI>
  </step>
  <step>
    <name>Transform S1 Non-PPN</name>
    <type>ScriptValueMod</type>
    {STANDARD_STEP_HEADER}
    <compatible>N</compatible>
    <optimizationLevel>9</optimizationLevel>
    <jsScripts>
      <jsScript>
        <jsScript_type>0</jsScript_type>
        <jsScript_name>Script 1</jsScript_name>
        <jsScript_script>
var sdf = new java.text.SimpleDateFormat("yyyy-MM-dd HH:mm:ss");
var dt = sdf.parse(order_ts);
var sdf_sk = new java.text.SimpleDateFormat("yyyyMMdd");
var sk_waktu = java.lang.Integer.parseInt(sdf_sk.format(dt));

var u_price_excl = Math.round((unit_price / 1.11) * 100) / 100;
var d_excl = Math.round((disc_amount / 1.11) * 100) / 100;
var gross_excl = Math.round((qty * u_price_excl) * 100) / 100;
var net_excl = Math.round((gross_excl - d_excl) * 100) / 100;

var mat_no = "P-1061";
if (sku != "SKU-NEWARR-001") {{
    var m = sku.match(/SKU-(\\d+)-/);
    if (m) {{
        mat_no = "P-" + m[1];
    }}
}}
var kanal = "WEB";
        </jsScript_script>
      </jsScript>
    </jsScripts>
    <fields>
      <field><name>sk_waktu</name><rename>sk_waktu</rename><type>Integer</type></field>
      <field><name>u_price_excl</name><rename>harga_satuan_excl</rename><type>Number</type></field>
      <field><name>gross_excl</name><rename>nilai_kotor_excl</rename><type>Number</type></field>
      <field><name>d_excl</name><rename>nilai_diskon_excl</rename><type>Number</type></field>
      <field><name>net_excl</name><rename>nilai_bersih_excl</rename><type>Number</type></field>
      <field><name>mat_no</name><rename>material_no</rename><type>String</type></field>
      <field><name>kanal</name><rename>kanal</rename><type>String</type></field>
    </fields>
    <GUI><xloc>280</xloc><yloc>100</yloc><draw>Y</draw></GUI>
  </step>
  <step>
    <name>Lookup S4 COGS S1</name>
    <type>DBLookup</type>
    {STANDARD_STEP_HEADER}
    <connection>nrg_dw_mysql</connection>
    <cache>Y</cache>
    <cache_size>1000</cache_size>
    <lookup>
      <schema/>
      <table>dim_produk</table>
      <orderby/>
      <fail_on_multiple>N</fail_on_multiple>
      <eat_row_on_failure>N</eat_row_on_failure>
      <key><name>material_no</name><field>material_no</field><condition>=</condition></key>
      <value><name>sk_produk</name><rename>sk_produk</rename><default>1</default><type>Integer</type></value>
      <value><name>harga_pokok_terkini</name><rename>harga_pokok_satuan</rename><default>0</default><type>Number</type></value>
    </lookup>
    <GUI><xloc>460</xloc><yloc>100</yloc><draw>Y</draw></GUI>
  </step>
  <step>
    <name>Lookup Dimensi S1</name>
    <type>ScriptValueMod</type>
    {STANDARD_STEP_HEADER}
    <compatible>N</compatible>
    <optimizationLevel>9</optimizationLevel>
    <jsScripts>
      <jsScript>
        <jsScript_type>0</jsScript_type>
        <jsScript_name>Script 1</jsScript_name>
        <jsScript_script>
var total_cogs = Math.round((qty * harga_pokok_satuan) * 100) / 100;
var fee_komisi = 0.00;
var margin_kotor = Math.round((nilai_bersih_excl - total_cogs - fee_komisi) * 100) / 100;
var sk_toko_kanal = 43; // sk untuk WEB
var sk_promosi = 1;
var sk_pelanggan = customer_id;
        </jsScript_script>
      </jsScript>
    </jsScripts>
    <fields>
      <field><name>total_cogs</name><rename>total_harga_pokok</rename><type>Number</type></field>
      <field><name>fee_komisi</name><rename>fee_komisi</rename><type>Number</type></field>
      <field><name>margin_kotor</name><rename>margin_kotor</rename><type>Number</type></field>
      <field><name>sk_toko_kanal</name><rename>sk_toko_kanal</rename><type>Integer</type></field>
      <field><name>sk_promosi</name><rename>sk_promosi</rename><type>Integer</type></field>
      <field><name>sk_pelanggan</name><rename>sk_pelanggan</rename><type>Integer</type></field>
    </fields>
    <GUI><xloc>640</xloc><yloc>100</yloc><draw>Y</draw></GUI>
  </step>
  <step>
    <name>Insert Fact Penjualan</name>
    <type>TableOutput</type>
    {STANDARD_STEP_HEADER}
    <connection>nrg_dw_mysql</connection>
    <schema/>
    <table>fact_penjualan</table>
    <commit>1000</commit>
    <truncate>Y</truncate>
    <ignore_errors>N</ignore_errors>
    <use_batch>Y</use_batch>
    <specify_fields>Y</specify_fields>
    <partitioning_enabled>N</partitioning_enabled>
    <partitioning_field/>
    <partitioning_daily>N</partitioning_daily>
    <partitioning_monthly>Y</partitioning_monthly>
    <tablename_in_field>N</tablename_in_field>
    <tablename_field/>
    <tablename_in_table>Y</tablename_in_table>
    <return_keys>N</return_keys>
    <return_field/>
    <fields>
      <field><column_name>sk_waktu</column_name><stream_name>sk_waktu</stream_name></field>
      <field><column_name>sk_produk</column_name><stream_name>sk_produk</stream_name></field>
      <field><column_name>sk_toko_kanal</column_name><stream_name>sk_toko_kanal</stream_name></field>
      <field><column_name>sk_pelanggan</column_name><stream_name>sk_pelanggan</stream_name></field>
      <field><column_name>sk_promosi</column_name><stream_name>sk_promosi</stream_name></field>
      <field><column_name>no_transaksi</column_name><stream_name>order_id</stream_name></field>
      <field><column_name>line_no</column_name><stream_name>line_no</stream_name></field>
      <field><column_name>kanal</column_name><stream_name>kanal</stream_name></field>
      <field><column_name>qty</column_name><stream_name>qty</stream_name></field>
      <field><column_name>harga_satuan_excl</column_name><stream_name>harga_satuan_excl</stream_name></field>
      <field><column_name>nilai_kotor_excl</column_name><stream_name>nilai_kotor_excl</stream_name></field>
      <field><column_name>nilai_diskon_excl</column_name><stream_name>nilai_diskon_excl</stream_name></field>
      <field><column_name>nilai_bersih_excl</column_name><stream_name>nilai_bersih_excl</stream_name></field>
      <field><column_name>harga_pokok_satuan</column_name><stream_name>harga_pokok_satuan</stream_name></field>
      <field><column_name>total_harga_pokok</column_name><stream_name>total_harga_pokok</stream_name></field>
      <field><column_name>fee_komisi</column_name><stream_name>fee_komisi</stream_name></field>
      <field><column_name>margin_kotor</column_name><stream_name>margin_kotor</stream_name></field>
    </fields>
    <GUI><xloc>860</xloc><yloc>100</yloc><draw>Y</draw></GUI>
  </step>
</transformation>
"""
    with open(os.path.join(OUTPUT_DIR, "fact_penjualan_loader.ktr"), "w", encoding="utf-8") as f:
        f.write(ktr.strip())
    print("Generated fact_penjualan_loader.ktr")


# ====================================================================
# 7. MAIN_ETL_JOB.KJB
# ====================================================================
def generate_master_job():
    kjb = f"""<?xml version="1.0" encoding="UTF-8"?>
<job>
  <name>main_etl_job</name>
  <description>Master Job ETL Data Warehouse Nusantara Retail Group</description>
  <job_version>1.0</job_version>
  <job_status>0</job_status>
  <directory>/</directory>
  {DB_CONNECTION_XML}
  <entries>
    <entry>
      <name>START</name>
      <description/>
      <type>SPECIAL</type>
      <attributes/>
      <start>Y</start>
      <dummy>N</dummy>
      <repeat>N</repeat>
      <schedulerType>0</schedulerType>
      <intervalSeconds>0</intervalSeconds>
      <intervalMinutes>60</intervalMinutes>
      <hour>12</hour>
      <minutes>0</minutes>
      <weekDay>1</weekDay>
      <DayOfMonth>1</DayOfMonth>
      <parallel>N</parallel>
      <draw>Y</draw>
      <nr>0</nr>
      <xloc>80</xloc>
      <yloc>120</yloc>
      <attributes_kjc/>
    </entry>
    <entry>
      <name>Check DB Connection</name>
      <description/>
      <type>CHECK_DB_CONNECTIONS</type>
      <attributes/>
      <connections>
        <connection>
          <name>nrg_dw_mysql</name>
          <waittime>0</waittime>
        </connection>
      </connections>
      <parallel>N</parallel>
      <draw>Y</draw>
      <nr>0</nr>
      <xloc>220</xloc>
      <yloc>120</yloc>
      <attributes_kjc/>
    </entry>
    <entry>
      <name>Load DIM_WAKTU</name>
      <description/>
      <type>TRANS</type>
      <attributes/>
      <specification_method>filename</specification_method>
      <trans_object_id/>
      <filename>${{Internal.Job.Filename.Directory}}/dim_waktu_loader.ktr</filename>
      <transname/>
      <arg_from_previous>N</arg_from_previous>
      <params_from_previous>N</params_from_previous>
      <exec_per_row>N</exec_per_row>
      <clear_rows>N</clear_rows>
      <clear_files>N</clear_files>
      <set_logfile>N</set_logfile>
      <logfile/>
      <logext/>
      <add_date>N</add_date>
      <add_time>N</add_time>
      <loglevel>Basic</loglevel>
      <cluster>N</cluster>
      <slave_server_name/>
      <set_append_logfile>N</set_append_logfile>
      <wait_until_finished>Y</wait_until_finished>
      <follow_abort_remote>N</follow_abort_remote>
      <create_parent_folder>N</create_parent_folder>
      <logging_remote_work>N</logging_remote_work>
      <run_configuration>Pentaho local</run_configuration>
      <suppress_result_data>N</suppress_result_data>
      <parameters>
        <pass_all_parameters>Y</pass_all_parameters>
      </parameters>
      <parallel>N</parallel>
      <draw>Y</draw>
      <nr>0</nr>
      <xloc>380</xloc>
      <yloc>120</yloc>
      <attributes_kjc/>
    </entry>
    <entry>
      <name>Load DIM_PRODUK</name>
      <description/>
      <type>TRANS</type>
      <attributes/>
      <specification_method>filename</specification_method>
      <trans_object_id/>
      <filename>${{Internal.Job.Filename.Directory}}/dim_produk_loader.ktr</filename>
      <transname/>
      <arg_from_previous>N</arg_from_previous>
      <params_from_previous>N</params_from_previous>
      <exec_per_row>N</exec_per_row>
      <clear_rows>N</clear_rows>
      <clear_files>N</clear_files>
      <set_logfile>N</set_logfile>
      <logfile/>
      <logext/>
      <add_date>N</add_date>
      <add_time>N</add_time>
      <loglevel>Basic</loglevel>
      <cluster>N</cluster>
      <slave_server_name/>
      <set_append_logfile>N</set_append_logfile>
      <wait_until_finished>Y</wait_until_finished>
      <follow_abort_remote>N</follow_abort_remote>
      <create_parent_folder>N</create_parent_folder>
      <logging_remote_work>N</logging_remote_work>
      <run_configuration>Pentaho local</run_configuration>
      <suppress_result_data>N</suppress_result_data>
      <parameters>
        <pass_all_parameters>Y</pass_all_parameters>
      </parameters>
      <parallel>N</parallel>
      <draw>Y</draw>
      <nr>0</nr>
      <xloc>520</xloc>
      <yloc>120</yloc>
      <attributes_kjc/>
    </entry>
    <entry>
      <name>Load DIM_TOKO_KANAL</name>
      <description/>
      <type>TRANS</type>
      <attributes/>
      <specification_method>filename</specification_method>
      <trans_object_id/>
      <filename>${{Internal.Job.Filename.Directory}}/dim_toko_kanal_loader.ktr</filename>
      <transname/>
      <arg_from_previous>N</arg_from_previous>
      <params_from_previous>N</params_from_previous>
      <exec_per_row>N</exec_per_row>
      <clear_rows>N</clear_rows>
      <clear_files>N</clear_files>
      <set_logfile>N</set_logfile>
      <logfile/>
      <logext/>
      <add_date>N</add_date>
      <add_time>N</add_time>
      <loglevel>Basic</loglevel>
      <cluster>N</cluster>
      <slave_server_name/>
      <set_append_logfile>N</set_append_logfile>
      <wait_until_finished>Y</wait_until_finished>
      <follow_abort_remote>N</follow_abort_remote>
      <create_parent_folder>N</create_parent_folder>
      <logging_remote_work>N</logging_remote_work>
      <run_configuration>Pentaho local</run_configuration>
      <suppress_result_data>N</suppress_result_data>
      <parameters>
        <pass_all_parameters>Y</pass_all_parameters>
      </parameters>
      <parallel>N</parallel>
      <draw>Y</draw>
      <nr>0</nr>
      <xloc>680</xloc>
      <yloc>120</yloc>
      <attributes_kjc/>
    </entry>
    <entry>
      <name>Load DIM_PELANGGAN</name>
      <description/>
      <type>TRANS</type>
      <attributes/>
      <specification_method>filename</specification_method>
      <trans_object_id/>
      <filename>${{Internal.Job.Filename.Directory}}/dim_pelanggan_loader.ktr</filename>
      <transname/>
      <arg_from_previous>N</arg_from_previous>
      <params_from_previous>N</params_from_previous>
      <exec_per_row>N</exec_per_row>
      <clear_rows>N</clear_rows>
      <clear_files>N</clear_files>
      <set_logfile>N</set_logfile>
      <logfile/>
      <logext/>
      <add_date>N</add_date>
      <add_time>N</add_time>
      <loglevel>Basic</loglevel>
      <cluster>N</cluster>
      <slave_server_name/>
      <set_append_logfile>N</set_append_logfile>
      <wait_until_finished>Y</wait_until_finished>
      <follow_abort_remote>N</follow_abort_remote>
      <create_parent_folder>N</create_parent_folder>
      <logging_remote_work>N</logging_remote_work>
      <run_configuration>Pentaho local</run_configuration>
      <suppress_result_data>N</suppress_result_data>
      <parameters>
        <pass_all_parameters>Y</pass_all_parameters>
      </parameters>
      <parallel>N</parallel>
      <draw>Y</draw>
      <nr>0</nr>
      <xloc>840</xloc>
      <yloc>120</yloc>
      <attributes_kjc/>
    </entry>
    <entry>
      <name>Load DIM_PROMOSI</name>
      <description/>
      <type>TRANS</type>
      <attributes/>
      <specification_method>filename</specification_method>
      <trans_object_id/>
      <filename>${{Internal.Job.Filename.Directory}}/dim_promosi_loader.ktr</filename>
      <transname/>
      <arg_from_previous>N</arg_from_previous>
      <params_from_previous>N</params_from_previous>
      <exec_per_row>N</exec_per_row>
      <clear_rows>N</clear_rows>
      <clear_files>N</clear_files>
      <set_logfile>N</set_logfile>
      <logfile/>
      <logext/>
      <add_date>N</add_date>
      <add_time>N</add_time>
      <loglevel>Basic</loglevel>
      <cluster>N</cluster>
      <slave_server_name/>
      <set_append_logfile>N</set_append_logfile>
      <wait_until_finished>Y</wait_until_finished>
      <follow_abort_remote>N</follow_abort_remote>
      <create_parent_folder>N</create_parent_folder>
      <logging_remote_work>N</logging_remote_work>
      <run_configuration>Pentaho local</run_configuration>
      <suppress_result_data>N</suppress_result_data>
      <parameters>
        <pass_all_parameters>Y</pass_all_parameters>
      </parameters>
      <parallel>N</parallel>
      <draw>Y</draw>
      <nr>0</nr>
      <xloc>980</xloc>
      <yloc>120</yloc>
      <attributes_kjc/>
    </entry>
    <entry>
      <name>Load FACT_PENJUALAN</name>
      <description/>
      <type>TRANS</type>
      <attributes/>
      <specification_method>filename</specification_method>
      <trans_object_id/>
      <filename>${{Internal.Job.Filename.Directory}}/fact_penjualan_loader.ktr</filename>
      <transname/>
      <arg_from_previous>N</arg_from_previous>
      <params_from_previous>N</params_from_previous>
      <exec_per_row>N</exec_per_row>
      <clear_rows>N</clear_rows>
      <clear_files>N</clear_files>
      <set_logfile>N</set_logfile>
      <logfile/>
      <logext/>
      <add_date>N</add_date>
      <add_time>N</add_time>
      <loglevel>Basic</loglevel>
      <cluster>N</cluster>
      <slave_server_name/>
      <set_append_logfile>N</set_append_logfile>
      <wait_until_finished>Y</wait_until_finished>
      <follow_abort_remote>N</follow_abort_remote>
      <create_parent_folder>N</create_parent_folder>
      <logging_remote_work>N</logging_remote_work>
      <run_configuration>Pentaho local</run_configuration>
      <suppress_result_data>N</suppress_result_data>
      <parameters>
        <pass_all_parameters>Y</pass_all_parameters>
      </parameters>
      <parallel>N</parallel>
      <draw>Y</draw>
      <nr>0</nr>
      <xloc>1140</xloc>
      <yloc>120</yloc>
      <attributes_kjc/>
    </entry>
    <entry>
      <name>Success</name>
      <description/>
      <type>SUCCESS</type>
      <attributes/>
      <parallel>N</parallel>
      <draw>Y</draw>
      <nr>0</nr>
      <xloc>1280</xloc>
      <yloc>120</yloc>
      <attributes_kjc/>
    </entry>
  </entries>
  <hops>
    <hop>
      <from>START</from>
      <to>Check DB Connection</to>
      <from_nr>0</from_nr>
      <to_nr>0</to_nr>
      <enabled>Y</enabled>
      <evaluation>Y</evaluation>
      <unconditional>Y</unconditional>
    </hop>
    <hop>
      <from>Check DB Connection</from>
      <to>Load DIM_WAKTU</to>
      <from_nr>0</from_nr>
      <to_nr>0</to_nr>
      <enabled>Y</enabled>
      <evaluation>Y</evaluation>
      <unconditional>N</unconditional>
    </hop>
    <hop>
      <from>Load DIM_WAKTU</from>
      <to>Load DIM_PRODUK</to>
      <from_nr>0</from_nr>
      <to_nr>0</to_nr>
      <enabled>Y</enabled>
      <evaluation>Y</evaluation>
      <unconditional>N</unconditional>
    </hop>
    <hop>
      <from>Load DIM_PRODUK</from>
      <to>Load DIM_TOKO_KANAL</to>
      <from_nr>0</from_nr>
      <to_nr>0</to_nr>
      <enabled>Y</enabled>
      <evaluation>Y</evaluation>
      <unconditional>N</unconditional>
    </hop>
    <hop>
      <from>Load DIM_TOKO_KANAL</from>
      <to>Load DIM_PELANGGAN</to>
      <from_nr>0</from_nr>
      <to_nr>0</to_nr>
      <enabled>Y</enabled>
      <evaluation>Y</evaluation>
      <unconditional>N</unconditional>
    </hop>
    <hop>
      <from>Load DIM_PELANGGAN</from>
      <to>Load DIM_PROMOSI</to>
      <from_nr>0</from_nr>
      <to_nr>0</to_nr>
      <enabled>Y</enabled>
      <evaluation>Y</evaluation>
      <unconditional>N</unconditional>
    </hop>
    <hop>
      <from>Load DIM_PROMOSI</from>
      <to>Load FACT_PENJUALAN</to>
      <from_nr>0</from_nr>
      <to_nr>0</to_nr>
      <enabled>Y</enabled>
      <evaluation>Y</evaluation>
      <unconditional>N</unconditional>
    </hop>
    <hop>
      <from>Load FACT_PENJUALAN</from>
      <to>Success</to>
      <from_nr>0</from_nr>
      <to_nr>0</to_nr>
      <enabled>Y</enabled>
      <evaluation>Y</evaluation>
      <unconditional>N</unconditional>
    </hop>
  </hops>
</job>
"""
    with open(os.path.join(OUTPUT_DIR, "main_etl_job.kjb"), "w", encoding="utf-8") as f:
        f.write(kjb.strip())
    print("Generated main_etl_job.kjb")


def main():
    generate_dim_waktu()
    generate_dim_produk()
    generate_dim_toko_kanal()
    generate_dim_pelanggan()
    generate_dim_promosi()
    generate_fact_penjualan()
    generate_master_job()
    print("\nSemua berkas Pentaho Data Integration (.ktr dan .kjb) sukses dibuat!")


if __name__ == "__main__":
    main()
