import os
import pandas as pd
from pymongo import MongoClient
from dotenv import load_dotenv
import streamlit as st
import certifi

load_dotenv()

class DataIngestionPipeline:
    def __init__(self, db_name=None, collection_name=None):
        mongo_uri = None

        # Prioritas 1: Ambil dari Streamlit Secrets (Cloud)
        try:
            if "MONGO_URI" in st.secrets:
                mongo_uri = st.secrets["MONGO_URI"]
            elif "mongo_uri" in st.secrets:
                mongo_uri = st.secrets["mongo_uri"]
        except Exception:
            pass

        # Prioritas 2: Ambil dari .env / Environment Variable (Lokal)
        if not mongo_uri:
            mongo_uri = os.getenv("MONGO_URI") or os.getenv("mongo_uri")

        if not mongo_uri:
            raise ValueError("MONGO_URI tidak ditemukan di Streamlit Secrets maupun file .env!")

        self.mongo_uri = mongo_uri
        
        # Inisialisasi koneksi dengan sertifikasi SSL/TLS dari certifi
        self.client = MongoClient(self.mongo_uri, tlsCAFile=certifi.where())
        
        self.db = self.client[db_name] if db_name else None
        self.collection = self.db[collection_name] if (db_name and collection_name) else None

    def get_existing_databases(self):
        system_dbs = ['admin', 'config', 'local']
        dbs = self.client.list_database_names()
        return [db for db in dbs if db not in system_dbs]

    def get_existing_collections(self, db_name):
        if db_name in self.client.list_database_names():
            return self.client[db_name].list_collection_names()
        return []

    def drop_database(self, db_name):
        if db_name in self.client.list_database_names():
            self.client.drop_database(db_name)
            return True
        return False

    def drop_collection(self, db_name, collection_name):
        if db_name in self.client.list_database_names():
            db = self.client[db_name]
            if collection_name in db.list_collection_names():
                db.drop_collection(collection_name)
                return True
        return False

    def extract(self, uploaded_file):
        if uploaded_file.name.endswith('.csv'):
            encodings = ['utf-8', 'latin1', 'cp1252', 'iso-8859-1']
            
            for enc in encodings:
                try:
                    uploaded_file.seek(0)
                    df = pd.read_csv(uploaded_file, sep=None, engine='python', encoding=enc)
                    return df
                except (UnicodeDecodeError, Exception):
                    continue
            
            uploaded_file.seek(0)
            df = pd.read_csv(
                uploaded_file, 
                sep=None, 
                engine='python', 
                encoding='utf-8', 
                encoding_errors='ignore', 
                on_bad_lines='skip'
            )
            return df
        else:
            df = pd.read_excel(uploaded_file)
            return df

    def transform(self, df, drop_duplicates=True, clean_headers=True, fill_na=True):
        if drop_duplicates:
            df = df.drop_duplicates()

        if clean_headers:
            df.columns = (
                df.columns.astype(str)
                .str.strip()
                .str.lower()
                .str.replace(' ', '_')
                .str.replace('[^a-zA-Z0-9_]', '', regex=True)
            )

        string_cols = df.select_dtypes(include=['object']).columns
        for col in string_cols:
            df[col] = df[col].apply(lambda x: str(x).strip() if pd.notnull(x) else x)

        if fill_na:
            df = df.where(pd.notnull(df), None)

        records = df.to_dict(orient='records')
        return records, len(df)

    def load(self, records):
        if self.collection is None:
            raise ValueError("Database atau collection belum dipilih.")
        result = self.collection.insert_many(records)
        return len(result.inserted_ids)