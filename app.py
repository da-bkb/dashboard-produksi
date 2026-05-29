import streamlit as st
import pandas as pd
import os
import numpy as np

# --- KONFIGURASI HALAMAN ---
st.set_page_config(
    page_title="Dashboard Produksi Kelapa Sawit",
    page_icon="🌴",
    layout="wide"
)

# --- SIDEBAR: PILIHAN SUMBER DATA TARGET ---
st.sidebar.image("https://via.placeholder.com/150", use_container_width=True)
st.sidebar.markdown("## ⚙️ Pengaturan Dashboard")

basis_analisa = st.sidebar.radio(
    "1. Pilih Basis Target Analisis:",
    ["Capaian terhadap BUDGET", "Capaian terhadap SENSUS"]
)

# --- PROSES LOADING DATA YANG AMAN DARI INF/NAN ---
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

    # Baca file dengan deteksi desimal koma agar tidak terbaca string
    try:
        df = pd.read_csv(file_name, sep=";", decimal=",")
    except:
        df = pd.read_csv(file_name, sep=",", decimal=",")
        
    # Bersihkan nama kolom dari spasi gaib
    df.columns = df.columns.str.strip()
    
    # Standarisasi kolom Bulan
    if 'Bulan' in df.columns:
        df['Bulan'] = df['Bulan'].astype(str).str.strip().str.upper()
        
    # Daftar seluruh kolom angka potensial di kedua file CSV
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
            
            # Konversi ke numerik secara aman
            df[col] = pd.to_numeric(df[col], errors='coerce')
            
    # 💡 KUNCI AMAN SENSUS: SINKRONISASI ALIAS KOLOM
    # Jika user memilih Sensus, salin nilai kolom Sensus ke kolom berakhiran 'Bgt.' 
    # Ini berjaga-jaga jika file visualisasi Sensus Bapak masih memanggil nama variabel 'Bgt.' di dalamnya
    if nama_target == "Sensus":
        if 'Jjg Sns.' in df.columns: df['Jjg Bgt.'] = df['Jjg Sns.']
        if 'Kg Sns.' in df.columns:  df['Kg Bgt.'] = df['Kg Sns.']
        if 'BJR Sns.' in df.columns: df['BJR Bgt.'] = df['BJR Sns.']
        if 'Ton/ha Sns.' in df.columns: df['Ton/ha Bgt.'] = df['Ton/ha Sns.']
            
    return df, nama_target

# Eksekusi loading data
df_raw, nama_target = load_data(basis_analisa)

if df_raw.empty:
    st.error(f"⚠️ Gagal memuat data. File database '{basis_analisa}' tidak terdeteksi.")
else:
    # Hilangkan nilai infinity tak terhingga jika ada bawaan error dari file CSV asli
    df_raw = df_raw.replace([np.inf, -np.inf], np.nan)

    # Urutkan menu pilihan Bulan secara standar kelapa sawit
    list_bulan_raw = df_raw["Bulan"].unique().tolist()
    URUTAN_BULAN_STD = ['JAN', 'FEB', 'MAR', 'APR', 'MEI', 'JUN', 'JUL', 'AGT', 'AGS', 'SEP', 'OKT', 'NOV', 'DES']
    list_bulan = [b for b in URUTAN_BULAN_STD if b in list_bulan_raw]
    for b in list_bulan_raw:
        if b not in list_bulan:
            list_bulan.append(b)

    # --- SIDEBAR: FILTER BULAN GLOBAL ---
    st.sidebar.markdown("---")
    st.sidebar.markdown("## 📅 Filter Periode")
    pilihan_bulan = st.sidebar.selectbox("2. Pilih Bulan Analisis:", list_bulan, key="global_month_picker")

    # --- SIMPAN KE SESSION STATE ---
    st.session_state["df_raw"] = df_raw
    st.session_state["pilihan_bulan"] = pilihan_bulan
    st.session_state["list_bulan"] = list_bulan

    # --- SIDEBAR: NAVIGASI MENU UTAMA ---
    st.sidebar.markdown("---")
    st.sidebar.markdown("## 📊 Menu Analisis")
    
    if nama_target == "Budget":
        menu_analisis = st.sidebar.radio(
            "3. Pilih Menu Dashboard:",
            ["Yield / Tonase", "Janjang / Pokok (J/P)", "BJR", "Trend Per Kebun", "Trend Per Afdeling"],
            key="menu_budget_navigator"
        )
    else:
        menu_analisis = st.sidebar.radio(
            "3. Pilih Menu Dashboard:",
            ["Yield / Tonase (Sns)", "Janjang / Pokok (Sns)", "BJR (Sns)", "Trend Sensus Kebun"],
            key="menu_sensus_navigator"
        )

    # --- TITLE UTAMA DASHBOARD ---
    st.title("🌴 Dashboard Performa Produksi Satui")
    st.markdown(f"Menampilkan data analisa berbasis **Aktual vs {nama_target}**")
    st.markdown("---")

    # Ambil konteks memori global agar sub-file tabs mengenali variabel utama app.py
    global_context = globals()

    if nama_target == "Budget":
        if menu_analisis == "Yield / Tonase":
            exec(open("tabs/yield_perf.py").read(), global_context)
        elif menu_analisis == "Janjang / Pokok (J/P)":
            exec(open("tabs/janjang_pokok.py").read(), global_context)
        elif menu_analisis == "BJR":
            exec(open("tabs/bjr_perf.py").read(), global_context)
        elif menu_analisis == "Trend Per Kebun":
            exec(open("tabs/trend_bln.py").read(), global_context)
        elif menu_analisis == "Trend Per Afdeling":
            exec(open("tabs/trend_afd.py").read(), global_context)

    else:
        if menu_analisis == "Yield / Tonase (Sns)":
            exec(open("tabs/yield_sensus.py").read(), global_context)
        elif menu_analisis == "Janjang / Pokok (Sns)":
            exec(open("tabs/janjang_sensus.py").read(), global_context)
        elif menu_analisis == "BJR (Sns)":
            exec(open("tabs/bjr_sensus.py").read(), global_context)
        elif menu_analisis == "Trend Sensus Kebun":
            exec(open("tabs/trend_bln_sensus.py").read(), global_context)