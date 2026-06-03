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

# --- 2. FUNGSI LOADING DATA BERDASARKAN PARAMETER FILTER ---
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
        df = pd.read_csv(file_name, sep=";", decimal=",")
    except:
        df = pd.read_csv(file_name, sep=",", decimal=",")
        
    # Bersihkan spasi liar pada nama kolom
    df.columns = df.columns.str.strip()
    
    # Standarisasi kolom Bulan menjadi huruf kapital
    if 'Bulan' in df.columns:
        df['Bulan'] = df['Bulan'].astype(str).str.strip().str.upper()
        
    return df, nama_target

# --- 3. JUDUL DASHBOARD ---
st.markdown("<h1 style='text-align: center; color: #28348A;'>🌴 DASHBOARD PRODUKSI TBS SITE SATUI</h1>", unsafe_allow_html=True)
st.markdown("---")

# --- 4. SUSUNAN FILTER UTAMA (DI BAWAH JUDUL) ---
col1, col2, col3 = st.columns([1.5, 1.2, 1.8])

with col1:
    # Filter 1: Capaian terhadap pilihan Budget atau Sensus
    pilihan_target = st.radio(
        "🎯 Capaian terhadap :",
        ["Budget", "Sensus"],
        horizontal=True,
        key="global_target_type_picker"
    )

# Memuat data secara real-time dari file csv yang sesuai pilihan filter 1
df_raw, nama_target_label = load_data(pilihan_target)

if df_raw.empty:
    st.error(f"⚠️ File data untuk Analisa {pilihan_target} tidak ditemukan di direktori!")
    st.stop()

with col2:
    # Filter 2: Pilihan Bulan Produksi mengambil dari kolom 'Bulan' di CSV
    list_bulan = list(df_raw['Bulan'].unique()) if 'Bulan' in df_raw.columns else ['MEI']
    default_idx = list_bulan.index("MEI") if "MEI" in list_bulan else 0
    
    pilihan_bulan = st.selectbox(
        "📅 Bulan Produksi:", 
        list_bulan, 
        index=default_idx,
        key="global_month_picker_main"
    )

with col3:
    # Filter 3: Menu Tabs Analisis
    menu_analisis = st.selectbox(
        "📊 Pilih Parameter:",
        ["Yield", "RJP", "BJR", "Trend per Kebun", "Trend per Afdeling"],
        key="menu_dashboard_navigator_main"
    )

st.markdown("---") # Garis pembatas tebal penanda area visualisasi grafik di bawahnya

# --- 5. MENYIMPAN VARIABEL GLOBAL KE SESSION STATE ---
# Agar file-file sub-tab di folder 'tabs' bisa langsung membaca datanya tanpa error
st.session_state["df_raw"] = df_raw
st.session_state["pilihan_bulan"] = pilihan_bulan
st.session_state["list_bulan"] = list_bulan

# --- 6. ROUTING EKSEKUSI FILE SUB-TAB DI FOLDER TABS ---
global_context = globals()

if menu_analisis == "Yield":
    # Menentukan file sub-tab yang akan dibuka berdasarkan filter "Capaian terhadap"
    file_tab = "tabs/yield_perf.py" if pilihan_target == "Budget" else "tabs/yield_sensus.py"
    if os.path.exists(file_tab):
        exec(open(file_tab).read(), global_context)
    else:
        st.warning(f"File '{file_tab}' tidak ditemukan di folder tabs.")

elif menu_analisis == "RJP":
    file_tab = "tabs/janjang_pokok.py" if pilihan_target == "Budget" else "tabs/janjang_sensus.py"
    if os.path.exists(file_tab):
        exec(open(file_tab).read(), global_context)
    else:
        st.warning(f"File '{file_tab}' tidak ditemukan di folder tabs.")

elif menu_analisis == "BJR":
    file_tab = "tabs/bjr_perf.py" if pilihan_target == "Budget" else "tabs/bjr_sensus.py"
    if os.path.exists(file_tab):
        exec(open(file_tab).read(), global_context)
    else:
        st.warning(f"File '{file_tab}' tidak ditemukan di folder tabs.")

elif menu_analisis == "Trend per Kebun":
    file_tab = "tabs/trend_kebun.py"
    if os.path.exists(file_tab):
        exec(open(file_tab).read(), global_context)
    else:
        st.info("ℹ️ File 'tabs/trend_kebun.py' belum dimasukkan ke folder.")

elif menu_analisis == "Trend per Afdeling":
    file_tab = "tabs/trend_afdeling.py"
    if os.path.exists(file_tab):
        exec(open(file_tab).read(), global_context)
    else:
        st.info("ℹ️ File 'tabs/trend_afdeling.py' belum dimasukkan ke folder.")