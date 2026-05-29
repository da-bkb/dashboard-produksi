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
st.sidebar.image("https://via.placeholder.com/150", use_container_width=True) # Silakan ganti logo perusahaan jika ada
st.sidebar.markdown("## ⚙️ Pengaturan Dashboard")

# Radio button untuk memilih basis analisa
basis_analisa = st.sidebar.radio(
    "1. Pilih Basis Target Analisis:",
    ["Capaian terhadap BUDGET", "Capaian terhadap SENSUS"]
)

# --- PROSES LOADING DATA DENGAN ALIASING AMAN ---
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
        
    # Bersihkan nama kolom
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
            
    # Trik Pemetaan Kolom Sensus agar seragam dibaca oleh file visualisasi budget
    if nama_target == "Sensus":
        if 'Jjg Sns.' in df.columns: df['Jjg Bgt.'] = df['Jjg Sns.']
        if 'Kg Sns.' in df.columns:  df['Kg Bgt.'] = df['Kg Sns.']
        if 'BJR Sns.' in df.columns: df['BJR Bgt.'] = df['BJR Sns.']
        if 'Ton/ha Sns.' in df.columns: df['Ton/ha Bgt.'] = df['Ton/ha Sns.']
            
    return df, nama_target

# Eksekusi fungsi load data
df_raw, nama_target = load_data(basis_analisa)

if df_raw.empty:
    st.error(f"⚠️ Gagal memuat data. File database untuk pilihan '{basis_analisa}' tidak terdeteksi di folder proyek.")
else:
    # Simpan ke session state agar bisa diakses oleh sub-file di folder /tabs
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

    # --- 🛡️ MEKANISME PROTEKSI DUPLIKASI ID WIDGET ---
    if not hasattr(st, 'selectbox_original'):
        st.selectbox_original = st.selectbox

    def apply_widget_patch(tab_suffix):
        """Mencegat pemanggilan selectbox untuk menyuntikkan key unik otomatis berdasarkan tab"""
        def custom_selectbox(label, *args, **kwargs):
            if 'key' not in kwargs:
                # Ambil karakter alfanumerik dari label sebagai penanda aman
                cleaned_label = "".join([c for c in str(label) if c.isalnum() or c in "_-"])[:30]
                kwargs['key'] = f"sb_{tab_suffix}_{cleaned_label}"
            return st.selectbox_original(label, *args, **kwargs)
        st.selectbox = custom_selectbox


    # --- NAVIGASI TAB UTAMA (URUTAN FIX SESUAI PERMINTAAN BAPAK) ---
    # Urutan: Yield -> Janjang/Pokok -> BJR -> Trend Per Kebun -> Trend Per Afdeling
    if nama_target == "Budget":
        tabs_menu = ["Yield / Tonase", "Janjang / Pokok (J/P)", "BJR", "Trend Per Kebun", "Trend Per Afdeling"]
        t1, t2, t3, t4, t5 = st.tabs(tabs_menu)
        
        with t1:
            apply_widget_patch("yield")
            import tabs.yield_perf as yield_perf
            importlib.reload(yield_perf)
        with t2:
            apply_widget_patch("janjang")
            import tabs.janjang_pokok as janjang_pokok
            importlib.reload(janjang_pokok)
        with t3:
            apply_widget_patch("bjr")
            import tabs.bjr_perf as bjr_perf
            importlib.reload(bjr_perf)
        with t4:
            apply_widget_patch("trend_kebun")
            import tabs.trend_bln as trend_bln
            importlib.reload(trend_bln)
        with t5:
            apply_widget_patch("trend_afd")
            import tabs.trend_afd as trend_afd
            importlib.reload(trend_afd)

    else:
        # Susunan Menu Dinamis Khusus Pilihan Target SENSUS
        tabs_menu_sns = ["Yield / Tonase (Sns)", "Janjang / Pokok (Sns)", "BJR (Sns)", "Trend Sensus Kebun"]
        t1, t2, t3, t4 = st.tabs(tabs_menu_sns)
        
        with t1:
            apply_widget_patch("yield_sns")
            import tabs.yield_sensus as yield_sensus
            importlib.reload(yield_sensus)
        with t2:
            apply_widget_patch("janjang_sns")
            import tabs.janjang_sensus as janjang_sensus
            importlib.reload(janjang_sensus)
        with t3:
            apply_widget_patch("bjr_sns")
            import tabs.bjr_sensus as bjr_sensus
            importlib.reload(bjr_sensus)
        with t4:
            apply_widget_patch("trend_kebun_sns")
            import tabs.trend_bln_sensus as trend_bln_sensus
            importlib.reload(trend_bln_sensus)

    # Kembalikan fungsi asli setelah selesai rendering halaman
    st.selectbox = st.selectbox_original