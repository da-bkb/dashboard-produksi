import streamlit as st
import pandas as pd
import os
import numpy as np

# --- KONFIGURASI HALAMAN UTAMA ---
st.set_page_config(
    page_title="Dashboard Produksi Kelapa Sawit",
    page_icon="🌴",
    layout="wide"
)

# --- PROSES LOADING DATA BERSIH (MAPPING OTOMATIS) ---
@st.cache_data
def load_data(tipe_target):
    if tipe_target == "Capaian terhadap BUDGET":
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
                df[col] = df[col].astype(str).str.replace(' ', '', regex=False)
                df[col] = df[col].str.replace(',', '.', regex=False)
            df[col] = pd.to_numeric(df[col], errors='coerce')
            
    # 💡 KUNCI PENGEMBALIAN DATA: SINKRONISASI ALIAS KOLOM SENSUS KE BUDGET
    # Ini membuat file .py budget asli Bapak bisa memproses data sensus tanpa merusak struktur grafik bulanan & YTD
    if nama_target == "SENSUS":
        if 'Jjg Sns.' in df.columns: df['Jjg Bgt.'] = df['Jjg Sns.']
        if 'Kg Sns.' in df.columns:  df['Kg Bgt.'] = df['Kg Sns.']
        if 'BJR Sns.' in df.columns: df['BJR Bgt.'] = df['BJR Sns.']
        if 'Ton/ha Sns.' in df.columns: df['Ton/ha Bgt.'] = df['Ton/ha Sns.']
            
    return df, nama_target


# =========================================================================
# 🌴 AREA UTAMA DASHBOARD (ATAS DAN FILTER SEJAJAR)
# =========================================================================

# 1. Judul Utama Dashboard
st.title("🌴 Dashboard Performa Produksi Satui")
st.markdown("Silakan atur basis analisis, periode bulan, dan menu grafik pada panel di bawah ini:")
st.markdown("---")

# 2. PEMBUATAN 3 KOLOM FILTER UTAMA (SEJAJAR HORIZONTAL)
col1, col2, col3 = st.columns([1, 1, 1])

with col1:
    basis_analisa = st.selectbox(
        "🎯 1. Basis Target Analisis:",
        ["Capaian terhadap BUDGET", "Capaian terhadap SENSUS"],
        key="main_basis_analisa"
    )

# Eksekusi loading database berdasarkan basis analisis terpilih
df_raw, nama_target = load_data(basis_analisa)

if df_raw.empty:
    st.error(f"⚠️ Gagal memuat data. File database '{basis_analisa}' tidak ditemukan.")
else:
    df_raw = df_raw.replace([np.inf, -np.inf], np.nan)

    # Urutkan urutan bulan standar operational
    list_bulan_raw = df_raw["Bulan"].unique().tolist()
    URUTAN_BULAN_STD = ['JAN', 'FEB', 'MAR', 'APR', 'MEI', 'JUN', 'JUL', 'AGT', 'AGS', 'SEP', 'OKT', 'NOV', 'DES']
    list_bulan = [b for b in URUTAN_BULAN_STD if b in list_bulan_raw]
    for b in list_bulan_raw:
        if b not in list_bulan:
            list_bulan.append(b)

    with col2:
        pilihan_bulan = st.selectbox(
            "📅 2. Bulan Analisis:", 
            list_bulan, 
            key="global_month_picker_main"
        )

    # Simpan data terpilih ke session state agar terbaca oleh file di folder tabs
    st.session_state["df_raw"] = df_raw
    st.session_state["pilihan_bulan"] = pilihan_bulan
    st.session_state["list_bulan"] = list_bulan

    with col3:
        # Urutan List Menu Sesuai Permintaan Bapak
        menu_analisis = st.selectbox(
            "📊 3. Pilih Menu Analisis:",
            ["Yield", "RJP", "BJR", "Trend Kebun", "Trend Afdeling"],
            key="menu_dashboard_navigator_main"
        )
    
    st.markdown("---") 

    # Ambil konteks memori global agar sub-file tabs mengenali variabel utama app.py
    global_context = globals()

    # --- ROUTING BALIK KE JALUR AMAN FILE UTAMA ---
    if menu_analisis == "Yield":
        exec(open("tabs/yield_perf.py").read(), global_context)
    elif menu_analisis == "RJP":
        exec(open("tabs/janjang_pokok.py").read(), global_context)
    elif menu_analisis == "BJR":
        exec(open("tabs/bjr_perf.py").read(), global_context)
    elif menu_analisis == "Trend Afdeling":
        exec(open("tabs/trend_afd.py").read(), global_context)
    elif menu_analisis == "Trend Kebun":
        exec(open("tabs/trend_bln.py").read(), global_context)