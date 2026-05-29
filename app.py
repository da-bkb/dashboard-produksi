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

# --- PROSES LOADING DATA DENGAN CLEANING OTOMATIS ---
@st.cache_data
def load_data(tipe_target):
    if tipe_target == "Capaian terhadap BUDGET":
        file_name = "Rekap26.csv"
        nama_target = "Budget"
    else:
        file_name = "Rekap26_Sns.csv"
        nama_target = "Sensus"
        
    # 1. Baca File CSV
    if os.path.exists(file_name):
        try:
            df = pd.read_csv(file_name, sep=";")
        except:
            df = pd.read_csv(file_name, sep=",")
    else:
        df = pd.DataFrame()
        
    if not df.empty:
        # 2. Bersihkan spasi pada nama kolom
        df.columns = df.columns.str.strip()
        
        # 3. KOREKSI TIPE DATA (Hanya mengubah yang bertipe teks/object)
        kolom_numerik = [
            'Luas', 'Pokok', 'Jjg Akt.', 'Kg Akt.', 'BJR Akt.', 'Ton/ha Akt.', '% Cap.', 'Gap Ton/Ha', 'Gap %',
            'Jjg Bgt.', 'Kg Bgt.', 'BJR Bgt.', 'Ton/ha Bgt.',
            'Jjg Sns.', 'Kg Sns.', 'BJR Sns.', 'Ton/ha Sns.'
        ]
        
        for col in kolom_numerik:
            if col in df.columns:
                if df[col].dtype == 'object':
                    # Ganti koma desimal menjadi titik desimal
                    df[col] = df[col].astype(str).str.replace(',', '.', regex=False)
                # Ubah paksa menjadi numerik desimal
                df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)
            
    return df, nama_target

# Eksekusi fungsi load data
df_raw, nama_target = load_data(basis_analisa)

# Simpan ke session state agar bisa diakses oleh file di folder /tabs
st.session_state["df_raw"] = df_raw

# --- SIDEBAR: FILTER BULAN GLOBAL ---
st.sidebar.markdown("---")
st.sidebar.markdown("## 📅 Filter Periode")

# Mengambil list bulan unik dari data yang aktif
list_bulan_raw = df_raw["Bulan"].unique() if not df_raw.empty else ['JAN']
URUTAN_BULAN_STD = ['JAN', 'FEB', 'MAR', 'APR', 'MEI', 'JUN', 'JUL', 'AGS', 'SEP', 'OKT', 'NOV', 'DES']
list_bulan = [b for b in URUTAN_BULAN_STD if b in list_bulan_raw]

# Jika tidak sengaja ada bulan di luar standar
for b in list_bulan_raw:
    if b not in list_bulan:
        list_bulan.append(b)

pilihan_bulan = st.sidebar.selectbox("2. Pilih Bulan Analisis:", list_bulan)

# Masukkan ke session state periode
st.session_state["pilihan_bulan"] = pilihan_bulan
st.session_state["list_bulan"] = list_bulan


# --- NAVIGASI TAB MENU UTAMA ---
st.title("🌴 Dashboard Performa Produksi Satui")
st.markdown(f"Menampilkan data analisa berbasis **Aktual vs {nama_target}**")

# Cek basis analisis untuk menampilkan menu tab yang relevan
if nama_target == "Budget":
    tabs_menu = ["Yield / Tonase", "BJR", "Janjang / Pokok (J/P)", "Trend Per Afdeling", "Trend Per Kebun"]
    t1, t2, t3, t4, t5 = st.tabs(tabs_menu)
    
    with t1:
        import tabs.yield_perf as yield_perf
    with t2:
        import tabs.bjr_perf as bjr_perf
    with t3:
        import tabs.janjang_pokok as janjang_pokok
    with t4:
        import tabs.trend_afd as trend_afd
    with t5:
        import tabs.trend_bln as trend_bln

else:
    # Menu tab khusus jika user memilih target SENSUS
    tabs_menu_sns = ["Yield / Tonase (Sns)", "BJR (Sns)", "Janjang / Pokok (Sns)", "Trend Sensus Kebun"]
    t1, t2, t3, t4 = st.tabs(tabs_menu_sns)
    
    with t1:
        import tabs.yield_sensus as yield_sensus
    with t2:
        import tabs.bjr_sensus as bjr_sensus
    with t3:
        import tabs.janjang_sensus as janjang_sensus
    with t4:
        import tabs.trend_bln_sensus as trend_bln_sensus