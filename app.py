import streamlit as st
import pandas as pd
import os
import numpy as np

# --- 1. KONFIGURASI HALAMAN UTAMA DASHBOARD ---
st.set_page_config(
    page_title="Dashboard Produksi Kelapa Sawit",
    page_icon="🌴",
    layout="wide"
)

# --- 2. FUNGSI LOAD DATA BERDASARKAN PILIHAN ANALISA ---
@st.cache_data
def load_data_source(tipe_analisa):
    if tipe_analisa == "Analisa terhadap Budget":
        file_name = "Rekap26.csv"
        target_name = "BUDGET"
    else:
        file_name = "Rekap26_Sns.csv"
        target_name = "SENSUS"
        
    if not os.path.exists(file_name):
        return pd.DataFrame(), target_name

    try:
        df = pd.read_csv(file_name, sep=";", decimal=",")
    except:
        df = pd.read_csv(file_name, sep=",", decimal=",")
        
    # Bersihkan spasi pada nama kolom
    df.columns = df.columns.str.strip()
    
    # Standarisasi kolom Bulan menjadi huruf kapital
    if 'Bulan' in df.columns:
        df['Bulan'] = df['Bulan'].astype(str).str.strip().str.upper()
        
    # Memastikan kolom teks bersih dari spasi liar
    for col in ['Kebun', 'Afdeling']:
        if col in df.columns:
            df[col] = df[col].astype(str).str.strip()
            
    return df, target_name

# --- 3. TAMPILAN HEADER DASHBOARD ---
st.markdown("<h1 style='text-align: center; color: #28348A;'>🌴 DASHBOARD ANALISA PRODUKSI KELAPA SAWIT</h1>", unsafe_allow_html=True)
st.markdown("---")

# --- 4. AREA FILTER UTAMA (DI BAWAH JUDUL) ---
col1, col2 = st.columns(2)

with col1:
    # Filter 1: 2 Pilihan Analisa Utama sesuai instruksi
    pilihan_analisa = st.radio(
        "🎯 Pilih Tipe Analisa Utama:",
        ["Analisa terhadap Budget", "Analisa terhadap Sensus"],
        horizontal=True,
        key="global_tipe_analisa_main"
    )

# Memuat database secara real-time berdasarkan radio button di atas
df_raw, nama_target_aktif = load_data_source(pilihan_analisa)

if df_raw.empty:
    st.error(f"⚠️ File data untuk '{pilihan_analisa}' tidak ditemukan di root folder. Pastikan file csv tersedia!")
    st.stop()

with col2:
    # Filter 2: Pilihan Bulan dinamis mengambil dari kolom data csv
    list_bulan_raw = list(df_raw['Bulan'].unique()) if 'Bulan' in df_raw.columns else ['MEI']
    
    # Ambil index default ke MEI jika tersedia agar tampilan awal langsung ke bulan Mei
    default_idx = list_bulan_raw.index("MEI") if "MEI" in list_bulan_raw else 0
    
    pilihan_bulan = st.selectbox(
        "📅 Pilih Bulan Analisis:",
        list_bulan_raw,
        index=default_idx,
        key="global_month_picker_main"
    )

# Simpan variabel ke session state agar file di folder tabs bisa membaca parameter global secara adil
st.session_state["df_raw"] = df_raw
st.session_state["pilihan_bulan"] = pilihan_bulan
st.session_state["list_bulan"] = list_bulan_raw
st.session_state["tipe_target"] = pilihan_analisa
st.session_state["nama_target_label"] = nama_target_aktif

st.markdown("---")

# --- 5. NAVIGASI TABS ANALISA (URUTAN SESUAI PERMINTAAN) ---
# Urutan: Yield -> RJP -> BJR -> Trend per Kebun -> Trend per Afdeling
menu_analisis = st.selectbox(
    "📊 Pilih Menu Analisis:",
    ["Yield", "RJP", "BJR", "Trend per Kebun", "Trend per Afdeling"],
    key="menu_dashboard_navigator_main"
)

st.markdown("---") # Pembatas area visualisasi grafik

# Mengambil konteks memori global agar sub-file mengenali variabel utama app.py
global_context = globals()

# --- 6. ENGINE ROUTING ROUTER SUB-FILE TABS ---
if menu_analisis == "Yield":
    # Jika memilih analisa budget, panggil yield_perf.py. Jika sensus, panggil yield_sensus.py
    if pilihan_analisa == "Analisa terhadap Budget":
        file_target_tab = "tabs/yield_perf.py"
    else:
        file_target_tab = "tabs/yield_sensus.py"
        
    if os.path.exists(file_target_tab):
        exec(open(file_target_tab).read(), global_context)
    else:
        st.warning(f"Sub-file '{file_target_tab}' tidak ditemukan di folder tabs.")

elif menu_analisis == "RJP":
    if pilihan_analisa == "Analisa terhadap Budget":
        file_target_tab = "tabs/janjang_pokok.py"
    else:
        file_target_tab = "tabs/janjang_sensus.py"
        
    if os.path.exists(file_target_tab):
        exec(open(file_target_tab).read(), global_context)
    else:
        st.warning(f"Sub-file '{file_target_tab}' tidak ditemukan di folder tabs.")

elif menu_analisis == "BJR":
    if pilihan_analisa == "Analisa terhadap Budget":
        file_target_tab = "tabs/bjr_perf.py"
    else:
        file_target_tab = "tabs/bjr_sensus.py"
        
    if os.path.exists(file_target_tab):
        exec(open(file_target_tab).read(), global_context)
    else:
        st.warning(f"Sub-file '{file_target_tab}' tidak ditemukan di folder tabs.")

elif menu_analisis == "Trend per Kebun":
    file_target_tab = "tabs/trend_kebun.py"
    if os.path.exists(file_target_tab):
        exec(open(file_target_tab).read(), global_context)
    else:
        st.info("ℹ️ Sub-file 'tabs/trend_kebun.py' belum tersedia. Silakan letakkan file analisis trend kebun Anda di folder tersebut.")

elif menu_analisis == "Trend per Afdeling":
    file_target_tab = "tabs/trend_afdeling.py"
    if os.path.exists(file_target_tab):
        exec(open(file_target_tab).read(), global_context)
    else:
        st.info("ℹ️ Sub-file 'tabs/trend_afdeling.py' belum tersedia. Silakan letakkan file analisis trend afdeling Anda di folder tersebut.")