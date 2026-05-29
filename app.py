import streamlit as st
import pandas as pd
import os

# --- KONFIGURASI HALAMAN ---
st.set_page_config(
    page_title="Dashboard Produksi Kelapa Sawit",
    page_icon="🌴",
    layout="wide"
)

# --- SIDEBAR: PILIHAN SUMBER DATA TARGET ---
st.sidebar.image("https://via.placeholder.com/150", use_container_width=True) # Silakan ganti logo perusahaan jika ada
st.sidebar.markdown("## ⚙️ Pengaturan Dashboard")

# Radio button untuk memilih basis analisa
basis_analisa = st.sidebar.radio(
    "1. Pilih Basis Target Analisis:",
    ["Capaian terhadap BUDGET", "Capaian terhadap SENSUS"]
)

# --- PROSES LOADING DATA DENGAN ALIASING OTOMATIS ---
@st.cache_data
def load_data(tipe_target):
    if tipe_target == "Capaian terhadap BUDGET":
        file_name = "Rekap26.csv"
        nama_target = "Budget"
    else:
        file_name = "Rekap26_Sns.csv"
        nama_target = "Sensus"
        
    # Pastikan file ada sebelum dibaca
    if not os.path.exists(file_name):
        st.error(f"⚠️ File `{file_name}` tidak ditemukan! Silakan upload file ke GitHub.")
        return pd.DataFrame(), nama_target

    try:
        df = pd.read_csv(file_name, sep=";")
    except:
        df = pd.read_csv(file_name, sep=",")
        
    # Bersihkan spasi pada nama kolom
    df.columns = df.columns.str.strip()
    
    # Standarisasi kolom Bulan
    if 'Bulan' in df.columns:
        df['Bulan'] = df['Bulan'].astype(str).str.strip().str.upper()
        
    # KOREKSI KOMA DESIMAL MENJADI TITIK DESIMAL
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
            
    # 🔥 TRIK UTAMA: Petakan kolom Sensus agar memiliki nama alias Budget
    # Langkah ini mencegah terjadinya KeyError di file visualisasi tab
    if nama_target == "Sensus":
        if 'Jjg Sns.' in df.columns: df['Jjg Bgt.'] = df['Jjg Sns.']
        if 'Kg Sns.' in df.columns:  df['Kg Bgt.'] = df['Kg Sns.']
        if 'BJR Sns.' in df.columns: df['BJR Bgt.'] = df['BJR Sns.']
        if 'Ton/ha Sns.' in df.columns: df['Ton/ha Bgt.'] = df['Ton/ha Sns.']
            
    return df, nama_target

# Eksekusi pemanggilan fungsi data
df_raw, nama_target = load_data(basis_analisa)

# --- JALANKAN UTAMA DASHBOARD ---
if not df_raw.empty:
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

    # --- NAVIGASI TAB SESUAI URUTAN BARU PERMINTAAN BAPAK ---
    # Yield -> Janjang/Pokok -> BJR -> Trend Per Kebun -> Trend Per Afdeling
    if nama_target == "Budget":
        tabs_menu = ["Yield / Tonase", "Janjang / Pokok (J/P)", "BJR", "Trend Per Kebun", "Trend Per Afdeling"]
        t1, t2, t3, t4, t5 = st.tabs(tabs_menu)
        
        with t1:
            import tabs.yield_perf as yield_perf
        with t2:
            import tabs.janjang_pokok as janjang_pokok
        with t3:
            import tabs.bjr_perf as bjr_perf
        with t4:
            import tabs.trend_bln as trend_bln
        with t5:
            import tabs.trend_afd as trend_afd

    else:
        # Urutan Tab Sensus disamakan polanya agar rapi
        tabs_menu_sns = ["Yield / Tonase (Sns)", "Janjang / Pokok (Sns)", "BJR (Sns)", "Trend Sensus Kebun"]
        t1, t2, t3, t4 = st.tabs(tabs_menu_sns)
        
        with t1:
            import tabs.yield_sensus as yield_sensus
        with t2:
            import tabs.janjang_sensus as janjang_sensus
        with t3:
            import tabs.bjr_sensus as bjr_sensus
        with t4:
            import tabs.trend_bln_sensus as trend_bln_sensus
else:
    st.warning("Silakan periksa ketersediaan file data Anda di folder repository.")