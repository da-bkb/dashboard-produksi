import streamlit as st
import pandas as pd
import os
import numpy as np

# --- 1. KONFIGURASI HALAMAN UTAMA ---
st.set_page_config(
    page_title="Dashboard Produksi Kelapa Sawit",
    page_icon="🌴",
    layout="wide"
)

# --- 2. FUNGSI LOADING DATA ---
@st.cache_data
def load_data(tipe_target):
    if tipe_target == "Budget":
        file_name = "Rekap26.csv"
        nama_target = "BUDGET"
    else:
        file_name = "Rekap26_Sns.csv"
        nama_target = "SENSUS"
        
    if not os.path.exists(file_name):
        return pd.DataFrame(), nama_target

    try:
        df = pd.read_csv(file_name, sep=\";\", decimal=\",\")
    except:
        df = pd.read_csv(file_name, sep=\",\", decimal=\",\")
        
    # Bersihkan spasi liar pada nama kolom
    df.columns = df.columns.str.strip()
    
    # Standarisasi kolom Bulan menjadi huruf kapital murni
    if 'Bulan' in df.columns:
        df['Bulan'] = df['Bulan'].astype(str).str.strip().str.upper()
        
    return df, nama_target

# --- 3. SIDEBAR UTAMA ---
st.sidebar.image("https://via.placeholder.com/150", caption="Dashboard Kelapa Sawit", use_container_width=True)
st.sidebar.title("📌 Menu Filter Analisis")

# Filter Utama 1: Capaian Terhadap (Budget / Sensus)
pilihan_target = st.sidebar.radio(
    "Capaian terhadap:",
    ["Budget", "Sensus"],
    index=0
)

# Filter Utama 2: Menu Komponen Analisis
menu_analisis = st.sidebar.selectbox(
    "Pilih Menu Analisis:",
    ["Yield", "RJP", "BJR", "Trend per Kebun"]
)

# Filter Utama 3: Bulan/Periode Analisis (BERSIH TANPA LIST 's.d')
list_bulan = [
    'JAN', 'FEB', 'MAR', 'APR', 'MEI', 'JUN', 
    'JUL', 'AGS', 'SEP', 'OKT', 'NOV', 'DES',
    'CAWU I', 'CAWU II', 'CAWU III', 
    'SEMESTER I', 'SEMESTER II'
]

pilihan_bulan = st.sidebar.selectbox(
    "Pilih Bulan/Periode Analisis:", 
    list_bulan,
    index=7  # Default ke AGS (Agustus) agar data langsung terisi
)

# --- 4. MANAJEMEN STATE GLOBAL ---
df_raw, target_aktif = load_data(pilihan_target)

# Simpan filter ke session state agar bisa dibaca dengan aman oleh sub-file tab di folder tabs/
st.session_state["df_raw"] = df_raw
st.session_state["pilihan_bulan"] = pilihan_bulan
st.session_state["target_aktif"] = target_aktif

# --- 5. VALIDASI KETERSEDIAAN DATA ---
if df_raw.empty:
    st.error(f"❌ File data untuk target **{pilihan_target}** tidak ditemukan atau kosong. Pastikan file tersedia di root folder.")
    st.stop()

# --- 6. ROUTING ROUTER TAB DAN EXECUTE SUB-FILE ---
# Konteks global agar variabel di dalam exec() terbaca sempurna di streamlit
global_context = {"st": st, "pd": pd, "np": np}

if menu_analisis == "Yield":
    # Menentukan file sub-tab yang akan dibuka berdasarkan filter "Capaian terhadap"
    file_tab = "tabs/yield_perf.py" if pilihan_target == "Budget" else "tabs/yield_sensus.py"
    if os.path.exists(file_tab):
        exec(open(file_tab).read(), global_context)
    else:
        st.warning(f"⚠️ File '{file_tab}' tidak ditemukan di folder tabs.")

elif menu_analisis == "RJP":
    file_tab = "tabs/janjang_pokok.py" if pilihan_target == "Budget" else "tabs/janjang_sensus.py"
    if os.path.exists(file_tab):
        exec(open(file_tab).read(), global_context)
    else:
        st.warning(f"⚠️ File '{file_tab}' tidak ditemukan di folder tabs.")

elif menu_analisis == "BJR":
    file_tab = "tabs/bjr_perf.py" if pilihan_target == "Budget" else "tabs/bjr_sensus.py"
    if os.path.exists(file_tab):
        exec(open(file_tab).read(), global_context)
    else:
        st.warning(f"⚠️ File '{file_tab}' tidak ditemukan di folder tabs.")

elif menu_analisis == "Trend per Kebun":
    file_tab = "tabs/trend_kebun.py"
    if os.path.exists(file_tab):
        exec(open(file_tab).read(), global_context)
    else:
        st.warning(f"⚠️ File '{file_tab}' tidak ditemukan di folder tabs.")