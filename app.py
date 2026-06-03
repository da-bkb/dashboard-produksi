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

# --- 2. FUNGSI LOAD & MERGE DATA ASLI (VERSI SUPER AMAN) ---
@st.cache_data
def load_data():
    file_bgt = "Rekap26.csv"
    file_sns = "Rekap26_Sns.csv"
    
    df_bgt = None
    df_sns = None
    
    # Fungsi pembantu standarisasi nama kolom
    def standarkan_kolom(df_target):
        kolom_map = {}
        for col in df_target.columns:
            c_upper = col.strip().upper()
            if c_upper in ['KEBUN', 'ESTATE', 'SITE']: kolom_map[col] = 'Kebun'
            elif c_upper in ['AFDELING', 'AFD']: kolom_map[col] = 'Afdeling'
            elif c_upper in ['BULAN', 'MONTH']: kolom_map[col] = 'Bulan'
            elif c_upper in ['LUAS', 'HA', 'LUAS HA']: kolom_map[col] = 'Luas'
            elif 'AKT' in c_upper or 'REAL' in c_upper: kolom_map[col] = 'Kg Akt.'
            elif 'BGT' in c_upper or 'BUD' in c_upper or 'ANGG' in c_upper: kolom_map[col] = 'Kg Bgt.'
            elif 'SNS' in c_upper or 'SEN' in c_upper or 'PRED' in c_upper: kolom_map[col] = 'Kg Sns.'
        return df_target.rename(columns=kolom_map)

    # 1. Baca File Budget/Aktual
    if os.path.exists(file_bgt):
        try:
            df_bgt_raw = pd.read_csv(file_bgt, sep=None, engine='python', encoding='utf-8')
            df_bgt = standarkan_kolom(df_bgt_raw)
        except Exception as e:
            st.error(f"Gagal membaca file {file_bgt}. Error: {e}")
            
    # 2. Baca File Sensus
    if os.path.exists(file_sns):
        try:
            df_sns_raw = pd.read_csv(file_sns, sep=None, engine='python', encoding='utf-8')
            df_sns = standarkan_kolom(df_sns_raw)
        except Exception as e:
            st.error(f"Gagal membaca file {file_sns}. Error: {e}")

    # PROSES GABUNG DATA SECARA AMAN (ANTI-DUPLIKASI)
    if df_bgt is not None and df_sns is not None:
        # Tentukan kunci merge yang ada di kedua dataframe
        kunci_merge = ['Kebun', 'Afdeling', 'Bulan']
        kunci_bgt = [c for c in kunci_merge if c in df_bgt.columns]
        kunci_sns = [c for c in kunci_merge if c in df_sns.columns]
        kunci_bersama = list(set(kunci_bgt).intersection(set(kunci_sns)))
        
        if len(kunci_bersama) >= 2:
            # 💡 PROTEKSI UTAMA: Dari file sensus, kita HANYA ambil kolom kunci + kolom 'Kg Sns.'
            # Ini mencegah kolom 'Luas', 'Kg Akt.', dll ikut masuk dan menduplikasi data budget.
            kolom_sensus_yg_diambil = kunci_bersama.copy()
            if 'Kg Sns.' in df_sns.columns:
                kolom_sensus_yg_diambil.append('Kg Sns.')
                
            df_sns_filtered = df_sns[kolom_sensus_yg_diambil].copy()
            
            # Gabungkan data
            df = pd.merge(df_bgt, df_sns_filtered, on=kunci_bersama, how='left')
        else:
            st.error("Kolom relasi (Kebun/Afdeling/Bulan) tidak cocok antara kedua file CSV.")
            df = df_bgt
    elif df_bgt is not None:
        df = df_bgt
    else:
        return pd.DataFrame(columns=['Bulan', 'Kebun', 'Afdeling', 'Luas', 'Kg Akt.', 'Kg Bgt.', 'Kg Sns.'])

    # Bersihkan data Bulan
    if 'Bulan' in df.columns:
        df['Bulan'] = df['Bulan'].astype(str).str.strip().str.upper()
        df['Bulan'] = df['Bulan'].replace({"AGUSTUS": "AGS", "MEI": "MEI", "MARET": "MAR"})

    # Konversi kolom numerik dengan proteksi tipe data Series tunggal
    numeric_cols = ['Luas', 'Kg Akt.', 'Kg Bgt.', 'Kg Sns.']
    for col in numeric_cols:
        if col in df.columns:
            # Squeeze DataFrame ke Series jika entah bagaimana masih terduplikasi
            series_data = df[col].iloc[:, 0] if isinstance(df[col], pd.DataFrame) else df[col]
            df[col] = pd.to_numeric(series_data, errors='coerce').fillna(0.0)
        else:
            df[col] = 0.0

    return df

# Eksekusi pemuatan data hasil patch aman
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