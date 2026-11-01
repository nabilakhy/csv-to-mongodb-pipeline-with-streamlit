import pandas as pd
import streamlit as st
from etl_pipeline import DataIngestionPipeline

st.set_page_config(page_title="MongoDB Data Ingestion Pipeline", layout="wide")

st.title("📦 Data Ingestion Pipeline ke MongoDB")

try:
    pipeline_init = DataIngestionPipeline()
except Exception as e:
    st.error(f"Gagal terhubung ke MongoDB: {e}")
    st.stop()

st.sidebar.header("⚙️ Target MongoDB")

existing_dbs = pipeline_init.get_existing_databases()

db_options = ["-- Buat Database Baru --"] + existing_dbs
selected_db_option = st.sidebar.selectbox("Pilih Database:", db_options)

if selected_db_option == "-- Buat Database Baru --":
    target_db = st.sidebar.text_input("Nama Database Baru:")
else:
    target_db = selected_db_option

existing_cols = []
if target_db and target_db in existing_dbs:
    existing_cols = pipeline_init.get_existing_collections(target_db)

col_options = ["-- Buat Collection Baru --"] + existing_cols
selected_col_option = st.sidebar.selectbox("Pilih Collection:", col_options)

if selected_col_option == "-- Buat Collection Baru --":
    target_col = st.sidebar.text_input("Nama Collection Baru:")
else:
    target_col = selected_col_option

st.sidebar.markdown("---")

with st.sidebar.expander("🗑️ Hapus Database / Collection"):
    if existing_dbs:
        del_db = st.selectbox("Hapus Database:", ["-- Pilih --"] + existing_dbs)
        if st.button("Hapus Database Ini", type="secondary"):
            if del_db != "-- Pilih --":
                if pipeline_init.drop_database(del_db):
                    st.session_state["success_msg"] = f"Database '{del_db}' berhasil dihapus!"
                    st.rerun()
    
    if target_db and existing_cols:
        del_col = st.selectbox("Hapus Collection:", ["-- Pilih --"] + existing_cols)
        if st.button("Hapus Collection Ini", type="secondary"):
            if del_col != "-- Pilih --":
                if pipeline_init.drop_collection(target_db, del_col):
                    st.session_state["success_msg"] = f"Collection '{del_col}' berhasil dihapus!"
                    st.rerun()

st.subheader("1. Unggah Berkas Data")
uploaded_file = st.file_uploader("Pilih file CSV atau Excel", type=['csv', 'xlsx', 'xls'])

if uploaded_file is not None:
    try:
        df_raw = pipeline_init.extract(uploaded_file)
        
        with st.expander("Preview Data Asli (Sebelum Transformasi)", expanded=True):
            st.dataframe(df_raw.head(10))
            st.caption(f"Total baris: {len(df_raw)} | Total kolom: {len(df_raw.columns)}")

        st.subheader("2. Pengaturan Transformasi")
        col1, col2, col3 = st.columns(3)
        with col1:
            drop_dup = st.checkbox("Hapus Duplikat", value=True)
        with col2:
            clean_head = st.checkbox("Bersihkan Header Kolom", value=True)
        with col3:
            fill_null = st.checkbox("Ubah NaN menjadi Null (None)", value=True)

        records, cleaned_count = pipeline_init.transform(
            df_raw.copy(), 
            drop_duplicates=drop_dup, 
            clean_headers=clean_head, 
            fill_na=fill_null
        )

        df_transformed = pd.DataFrame(records)

        with st.expander("Preview Data Hasil Transformasi"):
            st.dataframe(df_transformed.head(10))
            st.caption(f"Total baris setelah difilter: {cleaned_count}")

        st.subheader("3. Tipe Data & Skema Kolom")
        dtypes_df = pd.DataFrame({
            "Nama Kolom": df_transformed.columns,
            "Tipe Data": [str(dtype) for dtype in df_transformed.dtypes],
            "Jumlah Non-Null": df_transformed.notnull().sum().values
        })
        st.dataframe(dtypes_df, use_container_width=True)

        st.subheader("4. Ingest ke MongoDB")
        
        if "success_msg" in st.session_state:
            st.markdown(
                f"""
                <div style="background-color: #d4edda; border-left: 6px solid #28a745; color: #155724; padding: 16px; border-radius: 8px; font-size: 18px; margin-bottom: 20px;">
                    ✅ <strong>Berhasil!</strong> {st.session_state['success_msg']}
                </div>
                """,
                unsafe_allow_html=True
            )
            del st.session_state["success_msg"]

        if not target_db or not target_col:
            st.warning("Silakan tentukan Nama Database dan Collection terlebih dahulu di sidebar.")
        else:
            if st.button("🚀 Push Data ke MongoDB", type="primary"):
                with st.spinner("Mengunggah data ke MongoDB..."):
                    pipeline_load = DataIngestionPipeline(db_name=target_db, collection_name=target_col)
                    inserted_count = pipeline_load.load(records)
                    
                    st.session_state["success_msg"] = f"Berhasil memasukkan {inserted_count} dokumen ke Database '{target_db}' -> Collection '{target_col}'!"
                    st.rerun()

    except Exception as e:
        st.error(f"Terjadi kesalahan saat memproses file: {e}")