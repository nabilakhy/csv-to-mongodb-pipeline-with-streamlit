import streamlit as st
import pandas as pd
from etl_pipeline import DataIngestionPipeline

# Konfigurasi Tampilan
st.set_page_config(page_title="Data Parser to MongoDB Pipeline", layout="wide")

st.title("CSV/Excel Data Ingestion Pipeline")
st.markdown("Unggah file CSV/Excel apa saja untuk diparse, ditransformasi & dicleaning, lalu disimpan ke MongoDB.")

# Inisialisasi helper pipeline untuk koneksi DB
init_pipeline = DataIngestionPipeline()

# --- SIDEBAR: Database & Collection Management ---
st.sidebar.header("Database Configuration")

# 1. Database Selector
try:
    existing_dbs = init_pipeline.get_existing_databases()
except Exception as e:
    st.error(f"Gagal terhubung ke MongoDB via .env: {str(e)}")
    existing_dbs = []

db_options = existing_dbs + ["+ Create New Database"]
selected_db_option = st.sidebar.selectbox("Pilih Database", db_options)

if selected_db_option == "+ Create New Database":
    target_db = st.sidebar.text_input("Nama Database Baru", value="my_new_db")
else:
    target_db = selected_db_option

# 2. Collection Selector
existing_collections = []
if target_db and selected_db_option != "+ Create New Database":
    existing_collections = init_pipeline.get_existing_collections(target_db)

coll_options = existing_collections + ["+ Create New Collection"]
selected_coll_option = st.sidebar.selectbox("Pilih Collection", coll_options)

if selected_coll_option == "+ Create New Collection":
    target_collection = st.sidebar.text_input("Nama Collection Baru", value="raw_imports")
else:
    target_collection = selected_coll_option

# --- SIDEBAR: DANGER ZONE (HAPUS DATABASE / COLLECTION) ---
if selected_db_option != "+ Create New Database":
    st.sidebar.markdown("---")
    st.sidebar.subheader("Danger Zone")
    
    # Hapus Collection
    if selected_coll_option != "+ Create New Collection":
        if st.sidebar.button(f"Hapus Collection '{target_collection}'"):
            if init_pipeline.drop_collection(target_db, target_collection):
                st.sidebar.success(f"Collection '{target_collection}' dihapus!")
                st.rerun()

    # Hapus Database
    if st.sidebar.button(f"Hapus Database '{target_db}'"):
        if init_pipeline.drop_database(target_db):
            st.sidebar.success(f"Database '{target_db}' dihapus!")
            st.rerun()

# --- MAIN PAGE: Upload & Ingestion ---
uploaded_file = st.file_uploader("Pilih file CSV atau XLSX (Semua Format)", type=["csv", "xlsx"])

if uploaded_file is not None:
    try:
        pipeline = DataIngestionPipeline(db_name=target_db, collection_name=target_collection)
        
        # 1. EXTRACT
        df_raw = pipeline.extract(uploaded_file)
        st.success(f"File **{uploaded_file.name}** berhasil dibaca! Total data: **{len(df_raw)}** baris, **{len(df_raw.columns)}** kolom.")
        
        # PREVIEW DATA AWAL & INFO TIPE DATA
        st.subheader("1. Data Preview & Structure")
        col1, col2 = st.columns(2)
        with col1:
            st.write("Raw Data Sample:")
            st.dataframe(df_raw.head())
        
        with col2:
            st.write("Informasi Kolom & Tipe Data:")
            info_df = pd.DataFrame({
                'Column': df_raw.columns,
                'Data Type': df_raw.dtypes.astype(str),
                'Null Values': df_raw.isnull().sum().values
            })
            st.dataframe(info_df)

        # 2. DATA CLEANING
        st.subheader("2. Data Cleaning Options")
        col_c1, col_c2, col_c3 = st.columns(3)
        with col_c1:
            opt_drop_dup = st.checkbox("Hapus Baris Duplikat", value=True)
        with col_c2:
            opt_clean_headers = st.checkbox("Format Header (snake_case)", value=True)
        with col_c3:
            opt_fill_na = st.checkbox("Konversi NaN ke null", value=True)

        # TRANSFORM & CLEANING
        records, clean_rows_count = pipeline.transform(
            df_raw, 
            drop_duplicates=opt_drop_dup, 
            clean_headers=opt_clean_headers, 
            fill_na=opt_fill_na
        )

        # PREVIEW DATA BERSIH & JSON PAYLOAD
        st.subheader("3. Cleaned Data Preview & Structure")
        st.info(f"Jumlah baris setelah cleaning/deduplikasi: **{clean_rows_count}** baris.")
        
        with st.expander("Lihat Sampel Data JSON Payload (2 Record Pertama)"):
            st.json(records[:2])

        # 4. INGESTION
        st.subheader("4. Execute Ingestion")
        st.warning(f"Target Penyimpanan -> Database: **{target_db}** | Collection: **{target_collection}**")
        
        if st.button("Push Data ke MongoDB", type="primary"):
            with st.spinner("Mengirim data ke MongoDB..."):
                inserted_count = pipeline.load(records)
                st.success(f"Berhasil menyimpan {inserted_count} dokumen ke database '{target_db}', collection '{target_collection}'!")
                
    except Exception as e:
        st.error(f"Terjadi kesalahan saat memproses file: {str(e)}")
else:
    st.info("Silakan unggah file CSV atau Excel terlebih dahulu pada form di atas.")