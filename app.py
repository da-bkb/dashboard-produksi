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

# --- 2. FUNGSI LOAD & MERGE DATA ASLI (Rekap26.csv & Rekap26_Sns.csv) ---
@st.cache_data
def load_data():
    file_bgt = "Rekap26.csv"
    file_sns = "Rekap26_Sns.csv"
    
    df_bgt = None
    df_sns = None
    
    # 1. Baca File Budget & Aktual (Rekap26.csv)
    if os.path.exists(file_bgt):
        try:
            df_bgt = pd.read_csv(file_bgt, sep=None, engine='python', encoding='utf-8')
            df_bgt.columns = df_bgt.columns.str.strip().str.upper()
        except Exception as e:
            st.error(f"Gagal membaca file {file_bgt}. Error: {e}")
            
    # 2. Baca File Sensus (Rekap26_Sns.csv)
    if os.path.exists(file_sns):
        try:
            df_sns = pd.read_csv(file_sns, sep=None, engine='python', encoding='utf-8')
            df_sns.columns = df_sns.columns.str.strip().str.upper()
        except Exception as e:
            st.error(f"Gagal membaca file {file_sns}. Error: {e}")

    # JIKA KEDUA FILE ASLI ADA, LAKUKAN MERGE & STANDARISASI
    if df_bgt is not None and df_sns is not None:
        def dapatkan_kolom_map(columns):
            kolom_map = {}
            for col in columns:
                if col in ['KEBUN', 'ESTATE', 'SITE']: kolom_map[col] = 'Kebun'
                elif col in ['AFDELING', 'AFD']: kolom_map[col] = 'Afdeling'
                elif col in ['BULAN', 'MONTH']: kolom_map[col] = 'Bulan'
                elif col in ['LUAS', 'HA', 'LUAS HA']: kolom_map[col] = 'Luas'
                elif 'AKT' in col or 'REAL' in col: kolom_map[col] = 'Kg Akt.'
                elif 'BGT' in col or 'BUD' in col or 'ANGG' in col: kolom_map[col] = 'Kg Bgt.'
                elif 'SNS' in col or 'SEN' in col or 'PRED' in col: kolom_map[col] = 'Kg Sns.'
            return kolom_map

        df_bgt = df_bgt.rename(columns=dapatkan_kolom_map(df_bgt.columns))
        df_sns = df_sns.rename(columns=dapatkan_kolom_map(df_sns.columns))
        
        kunci_merge = ['Kebun', 'Afdeling', 'Bulan']
        kunci_bgt = [col for col in kunci_merge if col in df_bgt.columns]
        kunci_sns = [col for col in kunci_merge if col in df_sns.columns]
        kunci_bersama = list(set(kunci_bgt).intersection(set(kunci_sns)))
        
        if len(kunci_bersama) >= 2:
            # Drop kolom Luas dari df_sns sebelum merge untuk menghindari kolom ganda Luas_x dan Luas_y
            if 'Luas' in df_sns.columns:
                df_sns_clean = df_sns.drop(columns=['Luas'])
            else:
                df_sns_clean = df_sns
                
            # Gabungkan secara aman
            df = pd.merge(df_bgt, df_sns_clean, on=kunci_bersama, how='outer')
        else:
            st.error("Kolom relasi (Kebun/Afdeling/Bulan) tidak sinkron.")
            df = df_bgt
            
    elif df_bgt is not None:
        df = df_bgt
    else:
        return pd.DataFrame(columns=['Bulan', 'Kebun', 'Afdeling', 'Luas', 'Kg Akt.', 'Kg Bgt.', 'Kg Sns.'])

    # Bersihkan spasi dan standardisasi nama bulan
    if 'Bulan' in df.columns:
        df['Bulan'] = df['Bulan'].astype(str).str.strip().str.upper()
        df['Bulan'] = df['Bulan'].replace({"AGUSTUS": "AGS", "MEI": "MEI", "MARET": "MAR"})

    # --- PERBAIKAN UTAMA: Konversi kolom numerik yang kebal terhadap TypeError ---
    numeric_cols = ['Luas', 'Kg Akt.', 'Kg Bgt.', 'Kg Sns.']
    for col in numeric_cols:
        if col in df.columns:
            # Jika kolom tidak sengaja terduplikasi menjadi DataFrame, paksa ambil kolom pertamanya saja
            if isinstance(df[col], pd.DataFrame):
                df[col] = df[col].iloc[:, 0]
            
            # Konversi nilai ke numeric secara paksa dengan aman
            df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0.0)
        else:
            df[col] = 0.0

    return df

# Eksekusi gabungkan data asli
df_cleaned = load_data()

# --- 3. INISIALISASI SESSION STATE GLOBAL ---
st.session_state["df_raw"] = df_cleaned

# --- 4. SIDEBAR GLOBAL (FILTER BULAN UTAMA) ---
st.sidebar.markdown("## 🎛️ Filter Utama")

list_bulan_data = sorted(list(st.session_state["df_raw"]["Bulan"].unique())) if not st.session_state["df_raw"].empty else ["AGS"]
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