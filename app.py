import streamlit as st
import pandas as pd
from etl_pipeline import DataIngestionPipeline

st.set_page_config(page_title="Data Parser to MongoDB Pipeline", layout="wide")

st.title("CSV/Excel Data Ingestion Pipeline")
st.markdown("Unggah file CSV/Excel untuk diparse, ditransformasi, dan disimpan ke MongoDB.")

init_pipeline = DataIngestionPipeline()

# Sidebar
st.sidebar.header("Database Configuration")

try:
    existing_dbs = init_pipeline.get_existing_databases()
except Exception as e:
    st.sidebar.warning(f"Gagal terhubung ke MongoDB: {str(e)}")
    existing_dbs = []

db_options = existing_dbs + ["+ Create New Database"]
selected_db_option = st.sidebar.selectbox("Pilih Database", db_options, key="select_db")

if selected_db_option == "+ Create New Database":
    target_db = st.sidebar.text_input("Nama Database Baru", value="my_new_db", key="input_new_db")
else:
    target_db = selected_db_option

existing_collections = []
if target_db and target_db != "+ Create New Database":
    try:
        existing_collections = init_pipeline.get_existing_collections(target_db)
    except Exception:
        existing_collections = []

coll_options = existing_collections + ["+ Create New Collection"]
selected_coll_option = st.sidebar.selectbox("Pilih Collection", coll_options, key="select_coll")

if selected_coll_option == "+ Create New Collection":
    target_collection = st.sidebar.text_input("Nama Collection Baru", value="raw_imports", key="input_new_coll")
else:
    target_collection = selected_coll_option

if target_db in existing_dbs:
    st.sidebar.markdown("---")
    st.sidebar.subheader("Danger Zone")
    
    if selected_coll_option in existing_collections:
        if st.sidebar.button(f"Hapus Collection '{target_collection}'", type="secondary"):
            if init_pipeline.drop_collection(target_db, target_collection):
                st.sidebar.success(f"Collection '{target_collection}' berhasil dihapus!")
                st.rerun()

    if st.sidebar.button(f"Hapus Database '{target_db}'", type="secondary"):
        if init_pipeline.drop_database(target_db):
            st.sidebar.success(f"Database '{target_db}' berhasil dihapus!")
            st.rerun()

# Main Interface
uploaded_file = st.file_uploader("Pilih file CSV atau XLSX", type=["csv", "xlsx"])

if uploaded_file is not None:
    try:
        pipeline = DataIngestionPipeline(db_name=target_db, collection_name=target_collection)
        
        df_raw = pipeline.extract(uploaded_file)
        st.success(f"File **{uploaded_file.name}** berhasil dibaca ({len(df_raw)} baris, {len(df_raw.columns)} kolom).")
        
        st.subheader("1. Preview Data Awal")
        col1, col2 = st.columns(2)
        with col1:
            st.write("Sampel Data Mentah:")
            st.dataframe(df_raw.head())
        
        with col2:
            st.write("Info Kolom & Tipe Data:")
            info_df = pd.DataFrame({
                'Column': df_raw.columns,
                'Data Type': df_raw.dtypes.astype(str),
                'Null Values': df_raw.isnull().sum().values
            })
            st.dataframe(info_df)

        st.subheader("2. Opsi Data Cleaning")
        col_c1, col_c2, col_c3 = st.columns(3)
        with col_c1:
            opt_drop_dup = st.checkbox("Hapus Baris Duplikat", value=True)
        with col_c2:
            opt_clean_headers = st.checkbox("Format Header (snake_case)", value=True)
        with col_c3:
            opt_fill_na = st.checkbox("Konversi NaN ke null", value=True)

        records, clean_rows_count = pipeline.transform(
            df_raw, 
            drop_duplicates=opt_drop_dup, 
            clean_headers=opt_clean_headers, 
            fill_na=opt_fill_na
        )

        st.subheader("3. Preview Data Bersih")
        st.info(f"Jumlah baris setelah cleaning: **{clean_rows_count}** baris.")
        
        with st.expander("Lihat Sampel Payload JSON (2 Record Pertama)"):
            st.json(records[:2])

        st.subheader("4. Simpan ke MongoDB")
        st.warning(f"Target Penyimpanan -> Database: **{target_db}** | Collection: **{target_collection}**")
        
        if st.button("Push Data ke MongoDB", type="primary"):
            with st.spinner("Mengirim data..."):
                inserted_count = pipeline.load(records)
                st.success(f"Berhasil menyimpan {inserted_count} dokumen ke database '{target_db}', collection '{target_collection}'!")
                st.rerun()
                
    except Exception as e:
        st.error(f"Terjadi kesalahan: {str(e)}")
else:
    st.info("Silakan unggah file CSV atau Excel terlebih dahulu.")