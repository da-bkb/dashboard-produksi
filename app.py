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
    """
    Membaca data asli dari file Excel/CSV. 
    Jika tidak ditemukan, akan otomatis fallback ke data simulasi yang aman.
    """
    file_target = "data_yield.xlsx" # <-- Silakan ubah nama file sesuai file Bapak
    df = None
    
    if os.path.exists(file_target):
        if file_target.endswith('.csv'):
            df = pd.read_csv(file_target)
        else:
            df = pd.read_excel(file_target)
    else:
        # Taktik cadangan (Dummy Data Generator) agar app tidak crash saat testing
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

    # --- STANDARISASI KOLOM OTOMATIS (Mencegah KeyError) ---
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
st.sidebar.image("https://via.placeholder.com/150x50?text=LOGO+PERUSAHAAN", use_container_width=True)
st.sidebar.markdown("## 🎛️ Filter Utama")

list_bulan_data = sorted(list(st.session_state["df_raw"]["Bulan"].unique()))
idx_default = list_bulan_data.index("AGS") if "AGS" in list_bulan_data else 0

pilihan_bulan = st.sidebar.selectbox(
    "Pilih Operasional Bulan:", 
    options=list_bulan_data, 
    index=idx_default
)

# Simpan filter bulan terpilih secara global
st.session_state["pilihan_bulan"] = pilihan_bulan

st.sidebar.markdown("---")
st.sidebar.info(
    "💡 **Petunjuk Penggunaan:**\n\n"
    "1. Filter Bulan di atas berlaku untuk Tab **Yield vs Budget** & **Yield vs Sensus**.\n"
    "2. Untuk melihat performa makro, silakan buka Tab **Yield Periodik**."
)

# --- 5. STRUKTUR NAVIGASI UTAMA (TABS) ---
st.write("# 📑 Dashboard Performa Produksi (Yield)")
st.write("Sistem Analisa Produktivitas Blok, Afdeling, hingga Tingkat Regional Estate.")

tab_budget, tab_sensus, tab_periodik = st.tabs([
    "📈 Yield vs Budget", 
    "🎯 Yield vs Sensus", 
    "📅 Yield Periodik"
])

# --- 6. EKSEKUSI FILE KODE TIAP TAB SECARA DIRECT ---
with tab_budget:
    if os.path.exists("tabs/yield_perf.py"):
        with open("tabs/yield_perf.py", "r", encoding="utf-8") as f:
            code = f.read()
        exec(code)
    else:
        st.error("File `tabs/yield_perf.py` tidak ditemukan.")

with tab_sensus:
    if os.path.exists("tabs/yield_sensus.py"):
        with open("tabs/yield_sensus.py", "r", encoding="utf-8") as f:
            code = f.read()
        exec(code)
    else:
        st.error("File `tabs/yield_sensus.py` tidak ditemukan.")

with tab_periodik:
    if os.path.exists("tabs/yield_periodik.py"):
        with open("tabs/yield_periodik.py", "r", encoding="utf-8") as f:
            code = f.read()
        exec(code)
    else:
        st.error("File `tabs/yield_periodik.py` tidak ditemukan. Pastikan Anda sudah membuat filenya di dalam folder tabs.")