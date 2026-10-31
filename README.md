# Dynamic CSV/Excel to MongoDB Ingestion Pipeline

[ 🇮🇩 **Bahasa Indonesia** ] | [ 🇬🇧 **English** ]

---

## 🇬🇧 English Version

An interactive web-based data pipeline built with Streamlit to parse, clean, and ingest any CSV or Excel file directly into MongoDB seamlessly.

### Problem Solved
Uploading raw data from `.csv` or `.xlsx` files into NoSQL databases like MongoDB can be tedious:
* Excel export character encoding issues (e.g., `utf-8` vs `latin1`/`cp1252`).
* Inconsistent column delimiters (comma, semicolon, or tab).
* Dirty raw data (whitespace, duplicate rows, missing values/`NaN`).

This project provides an **automated schema-agnostic ETL pipeline** that addresses these edge cases in a single workflow.

### Key Features
* **Schema-Agnostic & Dynamic**: Handles CSV/Excel files with any arbitrary row/column structure without manual schema definition.
* **Smart Delimiter & Encoding Detection**: Automatically detects column separators and resolves encoding conflicts (`utf-8`, `latin1`, `cp1252`).
* **Automated Data Cleaning**:
  * Removes duplicate records automatically.
  * Standardizes column names into `snake_case` format.
  * Strips leading/trailing whitespaces from text values.
  * Converts missing/`NaN` values to JSON-compliant `null`.
* **Dynamic Database Management**: Fetches existing MongoDB Databases & Collections directly in the UI dropdown, with an option to create new ones on the fly.
* **Danger Zone Operations**: Allows dropping collections or databases directly from the sidebar.
* **Environment Security**: Sensitive URI configuration managed safely via `.env`.

---

## 🇮🇩 Versi Bahasa Indonesia

Aplikasi web interaktif berbasis Streamlit untuk memproses, membersihkan (*data cleaning*), dan memasukkan data dari file CSV atau Excel jenis apa pun langsung ke MongoDB secara otomatis.

### Masalah yang Diselesaikan
Mengunggah data dari file `.csv` atau `.xlsx` ke database NoSQL seperti MongoDB sering kali merepotkan:
* Format enkoding file dari Excel suka bikin error dekoding (`utf-8` vs `latin1`/`cp1252`).
* Tipe pemisah (*delimiter*) tidak konsisten (koma, titik koma, atau tab).
* Data mentah masih kotor (banyak spasi liar, baris duplikat, atau nilai kosong `NaN`).

Proyek ini menyediakan **pipeline ETL otomatis** yang menangani semua masalah di atas dalam satu alur kerja yang cepat dan dinamis.

### Fitur Utama
* **Schema-Agnostic & Dynamic**: Bisa membaca file CSV/Excel dengan struktur baris dan kolom apa saja tanpa perlu membuat skema tabel manual.
* **Smart Delimiter & Encoding Detection**: Otomatis mendeteksi pemisah kolom dan mengatasi masalah enkoding karakter (`utf-8`, `latin1`, `cp1252`).
* **Automated Data Cleaning**:
  * Menghapus baris duplikat secara otomatis.
  * Menyeragamkan format nama kolom menjadi standar `snake_case`.
  * Membersihkan spasi liar (*whitespace*) di awal dan akhir teks.
  * Mengonversi nilai `NaN` / kosong menjadi format `null` yang standar untuk JSON.
* **Dynamic Database Management**: Tarik daftar Database & Collection yang ada di MongoDB secara otomatis melalui dropdown UI, atau buat baru sesuai kebutuhan.
* **Danger Zone Operations**: Fitur hapus Collection atau Database langsung dari sidebar aplikasi.
* **Environment Configuration**: Parameter sensitif seperti `MONGO_URI` disimpan aman menggunakan file `.env`.

---

## Project Structure / Struktur Proyek

```text
csv-to-mongodb-app/
├── app.py              # Streamlit Web UI Interface
├── etl_pipeline.py     # Core ETL Engine (Extract, Transform, Load)
├── .env                # Environment Variables (MongoDB URI)
├── .gitignore          # Git Ignored Files
├── requirements.txt    # Python Dependencies
└── README.md           # Documentation