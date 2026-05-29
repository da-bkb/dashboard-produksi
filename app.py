import streamlit as st
import pandas as pd
import os
import importlib

# --- KONFIGURASI HALAMAN ---
st.set_page_config(
    page_title="Dashboard Produksi Kelapa Sawit",
    page_icon="🌴",
    layout="wide"
)

# --- SIDEBAR: PILIHAN SUMBER DATA TARGET ---
st.sidebar.image("https://via.placeholder.com/150", use_container_width=True) 
st.sidebar.markdown("## ⚙️ Pengaturan Dashboard")

# Radio button untuk memilih basis analisa
basis_analisa = st.sidebar.radio(
    "1. Pilih Basis Target Analisis:",
    ["Capaian terhadap BUDGET", "Capaian terhadap SENSUS"]
)

# --- PROSES LOADING DATA DENGAN ALIASING ---
@st.cache_data
def load_data(tipe_target):
    if tipe_target == "Capaian terhadap BUDGET":
        file_name = "Rekap26.csv"
        nama_target = "Budget"
    else:
        file_name = "Rekap26_Sns.csv"
        nama_target = "Sensus"
        
    if not os.path.exists(file_name):
        return pd.DataFrame(), nama_target

    try:
        df = pd.read_csv(file_name, sep=";")
    except:
        df = pd.read_csv(file_name, sep=",")
        
    df.columns = df.columns.str.strip()
    
    if 'Bulan' in df.columns:
        df['Bulan'] = df['Bulan'].astype(str).str.strip().str.upper()
        
    kolom_angka = [
        'Luas', 'Pokok', 'Jjg Akt.', 'Kg Akt.', 'BJR Akt.', 'Ton/ha Akt.', '% Cap.', 'Gap Ton/Ha', 'Gap %',
        'Jjg Bgt.', 'Kg Bgt.', 'BJR Bgt.', 'Ton/ha Bgt.',
        'Jjg Sns.', 'Kg Sns.', 'BJR Sns.', 'Ton/ha Sns.'
    ]
    
    for col in kolom_angka:
        if col in df.columns:
            if df[col].dtype == 'object':
                df[col] = df[col].astype(str).str.replace(',', '.', regex=False)
            df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)
            
    # Sinkronisasi kolom target Sensus agar dibaca mulus oleh sistem Budget
    if nama_target == "Sensus":
        if 'Jjg Sns.' in df.columns: df['Jjg Bgt.'] = df['Jjg Sns.']
        if 'Kg Sns.' in df.columns:  df['Kg Bgt.'] = df['Kg Sns.']
        if 'BJR Sns.' in df.columns: df['BJR Bgt.'] = df['BJR Sns.']
        if 'Ton/ha Sns.' in df.columns: df['Ton/ha Bgt.'] = df['Ton/ha Sns.']
            
    return df, nama_target

df_raw, nama_target = load_data(basis_analisa)

if df_raw.empty:
    st.error(f"⚠️ Gagal memuat data. File pendukung untuk pilihan '{basis_analisa}' tidak ditemukan di server.")
else:
    # Simpan ke session state global
    st.session_state["df_raw"] = df_raw

    # --- SIDEBAR: FILTER BULAN GLOBAL ---
    st.sidebar.markdown("---")
    st.sidebar.markdown("## 📅 Filter Periode")

    list_bulan_raw = df_raw["Bulan"].unique().tolist()
    URUTAN_BULAN_STD = ['JAN', 'FEB', 'MAR', 'APR', 'MEI', 'JUN', 'JUL', 'AGT', 'SEP', 'OKT', 'NOV', 'DES']
    list_bulan = [b for b in URUTAN_BULAN_STD if b in list_bulan_raw]

    for b in list_bulan_raw:
        if b not in list_bulan:
            list_bulan.append(b)

    pilihan_bulan = st.sidebar.selectbox("2. Pilih Bulan Analisis:", list_bulan)
    st.session_state["pilihan_bulan"] = pilihan_bulan
    st.session_state["list_bulan"] = list_bulan

    # --- TITLE UTAMA DASHBOARD ---
    st.title("🌴 Dashboard Performa Produksi Satui")
    st.markdown(f"Menampilkan data analisa berbasis **Aktual vs {nama_target}**")

    # --- NAVIGASI TAB UTAMA (URUTAN FIX SESUAI PERMINTAAN BAPAK) ---
    if nama_target == "Budget":
        tabs_menu = ["Yield / Tonase", "Janjang / Pokok (J/P)", "BJR", "Trend Per Kebun", "Trend Per Afdeling"]
        t1, t2, t3, t4, t5 = st.tabs(tabs_menu)
        
        # Menggunakan metode eksekusi langsung (mengatasi bug import cache Streamlit)
        with t1:
            exec(open("tabs/yield_perf.py").read(), globals())
        with t2:
            exec(open("tabs/janjang_pokok.py").read(), globals())
        with t3:
            exec(open("tabs/bjr_perf.py").read(), globals())
        with t4:
            exec(open("tabs/trend_bln.py").read(), globals())
        with t5:
            exec(open("tabs/trend_afd.py").read(), globals())

    else:
        # Susunan Tab Menu untuk Mode Sensus
        tabs_menu_sns = ["Yield / Tonase (Sns)", "Janjang / Pokok (Sns)", "BJR (Sns)", "Trend Sensus Kebun"]
        t1, t2, t3, t4 = st.tabs(tabs_menu_sns)
        
        with t1:
            exec(open("tabs/yield_sensus.py").read(), globals())
        with t2:
            exec(open("tabs/janjang_sensus.py").read(), globals())
        with t3:
            exec(open("tabs/bjr_sensus.py").read(), globals())
        with t4:
            exec(open("tabs/trend_bln_sensus.py").read(), globals())