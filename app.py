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

# --- 2. FUNGSI LOADING DATA OTOMATIS & TOLERAN ---
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
        # Menggunakan sep=None dan engine='python' agar otomatis mengenali separator (seperti ; atau ,)
        df = pd.read_csv(file_name, sep=None, engine='python', encoding='utf-8')
    except Exception as e:
        try:
            df = pd.read_csv(file_name, sep=None, engine='python', encoding='latin-1')
        except:
            return pd.DataFrame(), nama_target
        
    # Bersihkan spasi liar pada nama kolom dan buat huruf besar semua untuk standardisasi internal
    df.columns = df.columns.str.strip()
    
    # Deteksi dan standarkan kolom kunci operasional
    kolom_map = {}
    for col in df.columns:
        c_upper = col.upper()
        if c_upper in ['BULAN', 'MONTH']: kolom_map[col] = 'Bulan'
        elif c_upper in ['KEBUN', 'ESTATE', 'SITE']: kolom_map[col] = 'Kebun'
        elif c_upper in ['AFDELING', 'AFD']: kolom_map[col] = 'Afdeling'
        elif c_upper in ['LUAS', 'HA', 'LUAS HA']: kolom_map[col] = 'Luas'
        elif 'AKT' in c_upper or 'REAL' in c_upper: kolom_map[col] = 'Kg Akt.'
        elif 'BGT' in c_upper or 'BUD' in c_upper or 'ANGG' in c_upper: kolom_map[col] = 'Kg Bgt.'
        elif 'SNS' in c_upper or 'SEN' in c_upper or 'PRED' in c_upper: kolom_map[col] = 'Kg Sns.'
    
    df = df.rename(columns=kolom_map)
    
    # Standarisasi isi kolom Bulan menjadi nama pendek huruf kapital
    if 'Bulan' in df.columns:
        df['Bulan'] = df['Bulan'].astype(str).str.strip().str.upper()
        df['Bulan'] = df['Bulan'].replace({
            "JANUARI": "JAN", "FEBRUARI": "FEB", "MARET": "MAR", 
            "APRIL": "APR", "MEI": "MEI", "JUNI": "JUN", 
            "JULI": "JUL", "AGUSTUS": "AGS", "SEPTEMBER": "SEP", 
            "OKTOBER": "OKT", "NOVEMBER": "NOV", "DESEMBER": "DES"
        })
        
    return df, nama_target

# --- 3. JUDUL DASHBOARD ---
st.markdown("<h1 style='text-align: center; color: #28348A;'>🌴 DASHBOARD PRODUKSI PT BKB & PT FFD</h1>", unsafe_allow_html=True)
st.markdown("---")

# --- 4. SUSUNAN FILTER UTAMA ---
col1, col2, col3 = st.columns([1.5, 1.2, 1.8])

with col1:
    pilihan_target = st.radio(
        "🎯 Capaian terhadap :",
        ["Budget", "Sensus"],
        horizontal=True,
        key="global_target_type_picker"
    )

# Memuat data
df_raw, nama_target_label = load_data(pilihan_target)

if df_raw.empty:
    st.error(f"⚠️ File data untuk Analisa {pilihan_target} kosong atau formatnya tidak sesuai!")
    st.stop()

with col2:
    # Mengambil list bulan yang tersedia di CSV secara dinamis
    if 'Bulan' in df_raw.columns and len(df_raw['Bulan'].unique()) > 0:
        list_bulan = list(df_raw['Bulan'].dropna().unique())
    else:
        list_bulan = ['MEI']
        
    default_idx = list_bulan.index("MEI") if "MEI" in list_bulan else 0
    
    pilihan_bulan = st.selectbox(
        "📅 Bulan Analisis:", 
        list_bulan, 
        index=default_idx,
        key="global_month_picker_main"
    )

with col3:
    menu_analisis = st.selectbox(
        "📊 Pilih Menu Analisis:",
        ["Yield", "RJP", "BJR", "Trend per Kebun", "Trend per Afdeling"],
        key="menu_dashboard_navigator_main"
    )

st.markdown("---")

# --- 5. MENYIMPAN VARIABEL GLOBAL KE SESSION STATE ---
st.session_state["df_raw"] = df_raw
st.session_state["pilihan_bulan"] = pilihan_bulan
st.session_state["list_bulan"] = list_bulan

# --- 6. ROUTING EKSEKUSI FILE SUB-TAB ---
global_context = globals()

if menu_analisis == "Yield":
    file_tab = "tabs/yield_perf.py" if pilihan_target == "Budget" else "tabs/yield_sensus.py"
    if os.path.exists(file_tab):
        try:
            exec(open(file_tab).read(), global_context)
        except Exception as e:
            st.error(f"Terjadi kesalahan saat memuat visualisasi Yield: {e}")
    else:
        st.warning(f"File '{file_tab}' tidak ditemukan di folder tabs.")

elif menu_analisis == "RJP":
    file_tab = "tabs/janjang_pokok.py" if pilihan_target == "Budget" else "tabs/janjang_sensus.py"
    if os.path.exists(file_tab):
        try:
            exec(open(file_tab).read(), global_context)
        except Exception as e:
            st.error(f"Terjadi kesalahan saat memuat visualisasi RJP: {e}")
    else:
        st.warning(f"File '{file_tab}' tidak ditemukan di folder tabs.")

elif menu_analisis == "BJR":
    file_tab = "tabs/bjr_perf.py" if pilihan_target == "Budget" else "tabs/bjr_sensus.py"
    if os.path.exists(file_tab):
        try:
            exec(open(file_tab).read(), global_context)
        except Exception as e:
            st.error(f"Terjadi kesalahan saat memuat visualisasi BJR: {e}")
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