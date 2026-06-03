import streamlit as st
import pandas as pd
import numpy as np
import os

# --- 1. KONFIGURASI HALAMAN UTAMA ---
st.set_page_config(
    page_title="Dashboard Yield Performa Kebun & Afdeling",
    page_icon="🌱",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- 2. FUNGSI LOAD DATA UTAMA + AUTO MAP KOLOM ---
@st.cache_data
def load_data():
    file_target = "data_yield.xlsx" # <-- Sesuaikan dengan nama file Excel Bapak
    df = None
    
    if os.path.exists(file_target):
        if file_target.endswith('.csv'):
            df = pd.read_csv(file_target)
        else:
            df = pd.read_excel(file_target)
    else:
        # Fallback dummy data jika file tidak ditemukan saat dideploy
        bulan_list = ['JAN', 'FEB', 'MAR', 'APR', 'MEI', 'JUN', 'JUL', 'AGS', 'SEP', 'OKT', 'NOV', 'DES']
        kebun_list = ['BKB Inti', 'REK Inti', 'SRE Inti']
        afdeling_list = ['A', 'B', 'C', 'D']
        rows = []
        for bln in bulan_list:
            for kbn in kebun_list:
                for afd in afdeling_list:
                    rows.append({
                        "Bulan": bln, "Kebun": kbn, "Afdeling": afd, "Luas": 500.0,
                        "Kg Aktual": np.random.randint(400000, 600000),
                        "Kg Budget": np.random.randint(420000, 580000),
                        "Kg Sensus": np.random.randint(410000, 590000)
                    })
        df = pd.DataFrame(rows)

    # Standarisasi kolom otomatis
    df.columns = df.columns.str.strip().str.upper()
    kolom_map = {}
    for col in df.columns:
        if col in ['KEBUN', 'ESTATE', 'SITE']: kolom_map[col] = 'Kebun'
        elif col in ['AFDELING', 'AFD']: kolom_map[col] = 'Afdeling'
        elif col in ['BULAN', 'MONTH']: kolom_map[col] = 'Bulan'
        elif col in ['LUAS', 'HA', 'LUAS HA']: kolom_map[col] = 'Luas'
        elif 'AKT' in col or 'REAL' in col: kolom_map[col] = 'Kg Akt.'
        elif 'BGT' in col or 'BUD' in col or 'ANGG' in col: kolom_map[col] = 'Kg Bgt.'
        elif 'SNS' in col or 'SEN' in col or 'PRED' in col: kolom_map[col] = 'Kg Sns.'
        
    df = df.rename(columns=kolom_map)
    
    if 'Bulan' in df.columns:
        df['Bulan'] = df['Bulan'].astype(str).str.strip().str.upper()
        df['Bulan'] = df['Bulan'].replace({"AGUSTUS": "AGS", "MEI": "MEI", "MARET": "MAR"})

    return df

# Eksekusi pemuatan data
df_cleaned = load_data()

# --- 3. INISIALISASI SESSION STATE GLOBAL ---
st.session_state["df_raw"] = df_cleaned

# --- 4. SIDEBAR GLOBAL (FILTER BULAN UTAMA) ---
st.sidebar.markdown("## 🎛️ Filter Utama")

list_bulan_data = sorted(list(st.session_state["df_raw"]["Bulan"].unique()))
idx_default = list_bulan_data.index("AGS") if "AGS" in list_bulan_data else 0

pilihan_bulan = st.sidebar.selectbox(
    "Pilih Operasional Bulan:", 
    options=list_bulan_data, 
    index=idx_default
)
st.session_state["pilihan_bulan"] = pilihan_bulan

st.sidebar.markdown("---")
st.sidebar.info("💡 Filter Bulan berlaku untuk Tab Yield vs Budget & Yield vs Sensus.")

# --- 5. STRUKTUR NAVIGASI TABS ---
st.write("# 📑 Dashboard Performa Produksi (Yield)")

tab_budget, tab_sensus, tab_periodik = st.tabs([
    "📈 Yield vs Budget", 
    "🎯 Yield vs Sensus", 
    "📅 Yield Periodik"
])

# --- 6. IMPORT MODUL DAN EKSEKUSI SECARA AMAN ---
try:
    import tabs
    
    with tab_budget:
        tabs.render_yield_perf()
        
    with tab_sensus:
        tabs.render_yield_sensus()
        
    with tab_periodik:
        tabs.render_yield_periodik()
        
except Exception as e:
    st.error(f"Gagal memuat komponen dashboard. Error: {e}")