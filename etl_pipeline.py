import os
import pandas as pd
from pymongo import MongoClient
from dotenv import load_dotenv

# Load variabel lingkungan dari file .env
load_dotenv()

class DataIngestionPipeline:
    def __init__(self, db_name=None, collection_name=None):
        self.mongo_uri = os.getenv("MONGO_URI", "mongodb://localhost:27017/")
        self.client = MongoClient(self.mongo_uri)
        
        self.db = self.client[db_name] if db_name else None
        self.collection = self.db[collection_name] if (db_name and collection_name) else None

    def get_existing_databases(self):
        """Mengambil daftar nama database dari MongoDB (abai database sistem)."""
        system_dbs = ['admin', 'config', 'local']
        dbs = self.client.list_database_names()
        return [db for db in dbs if db not in system_dbs]

    def get_existing_collections(self, db_name):
        """Mengambil daftar collection dari database tertentu."""
        if db_name in self.client.list_database_names():
            return self.client[db_name].list_collection_names()
        return []

    def drop_database(self, db_name):
        """Menghapus seluruh database dari MongoDB."""
        if db_name in self.client.list_database_names():
            self.client.drop_database(db_name)
            return True
        return False

    def drop_collection(self, db_name, collection_name):
        """Menghapus collection tertentu dari database."""
        if db_name in self.client.list_database_names():
            db = self.client[db_name]
            if collection_name in db.list_collection_names():
                db.drop_collection(collection_name)
                return True
        return False

    def extract(self, uploaded_file):
        """Extract data dari CSV/Excel secara dinamis dengan fallback encoding."""
        if uploaded_file.name.endswith('.csv'):
            encodings = ['utf-8', 'latin1', 'cp1252', 'iso-8859-1']
            
            for enc in encodings:
                try:
                    uploaded_file.seek(0)
                    df = pd.read_csv(uploaded_file, sep=None, engine='python', encoding=enc)
                    return df
                except (UnicodeDecodeError, Exception):
                    continue
            
            # Jika semua encoding gagal, abaikan karakter bermasalah
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
        """
        Transformasi & Cleaning Data:
        - Drop duplicate rows
        - Standardize headers (snake_case)
        - Clean string whitespaces
        - Handling missing/null values
        """
        # 1. Hapus Baris Duplikat
        if drop_duplicates:
            df = df.drop_duplicates()

        # 2. Standardisasi Nama Kolom (misal: 'Customer Name ' -> 'customer_name')
        if clean_headers:
            df.columns = (
                df.columns.astype(str)
                .str.strip()
                .str.lower()
                .str.replace(' ', '_')
                .str.replace('[^a-zA-Z0-9_]', '', regex=True)
            )

        # 3. Clean Spasi di Isi Teks (String Columns)
        string_cols = df.select_dtypes(include=['object']).columns
        for col in string_cols:
            df[col] = df[col].apply(lambda x: str(x).strip() if pd.notnull(x) else x)

        # 4. Handling Missing/Null Values untuk JSON Compliant
        if fill_na:
            df = df.where(pd.notnull(df), None)

        records = df.to_dict(orient='records')
        return records, len(df)

    def load(self, records):
        """Load data JSON ke MongoDB collection."""
        if self.collection is None:
            raise ValueError("Database atau Collection belum ditentukan.")
        result = self.collection.insert_many(records)
        return len(result.inserted_ids)