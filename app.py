import streamlit as st
import pandas as pd
import os

# --- 1. KONFIGURASI HALAMAN ---
st.set_page_config(page_title="Dashboard Yield & Komponen 2026", layout="wide")

# --- 2. GLOBAL CSS TAMPILAN DATAFRAME ---
st.markdown("""
    <style>
    .stDataFrame div[data-testid="stTable"] td, 
    .stDataFrame div[data-testid="stTable"] th,
    .stDataFrame table {
        font-size: 11px !important;
    }
    div[data-testid="stDataFrame"] div {
        font-size: 11px !important;
    }
    </style>
""", unsafe_allow_html=True)

# --- 3. FUNGSI KEAMANAN (SISTEM LOGIN LOKAL / CLOUD) ---
def cek_login():
    """Mengembalikan True jika pengguna berhasil login."""
    if st.session_state.get("otentikasi", False):
        return True

    st.markdown("<h2 style='text-align: center;'>🔒 Akses Terbatas</h2>", unsafe_allow_html=True)
    st.markdown("<p style='text-align: center; color: gray;'>Silakan masukkan kredensial Anda untuk mengakses Dashboard Produksi</p>", unsafe_allow_html=True)
    
    col_a, col_b, col_c = st.columns([1, 1.5, 1])
    with col_b:
        with st.form("Form_Login"):
            username_input = st.text_input("Username:")
            password_input = st.text_input("Password:", type="password")
            tombol_login = st.form_submit_button("Masuk")
            
            if tombol_login:
                # Coba baca st.secrets (untuk Cloud), jika gagal pakai default lokal
                try:
                    username_valid = st.secrets["credentials"]["username"]
                    password_valid = st.secrets["credentials"]["password"]
                except Exception:
                    username_valid = "admin"
                    password_valid = "kebun2026"
                
                if username_input == username_valid and password_input == password_valid:
                    st.session_state["otentikasi"] = True
                    st.rerun()
                else:
                    st.error("❌ Kredensial Salah!")
    return False

# --- 4. FUNGSI LOAD DATA ---
def load_and_cache_data():
    """Membaca dan membersihkan data dari Rekap26.csv."""
    if "df_raw" in st.session_state:
        return st.session_state["df_raw"]
        
    file_path = "Rekap26.csv"
    if not os.path.exists(file_path):
        st.error(f"File '{file_path}' tidak ditemukan di folder aktif!")
        return None
        
    df = pd.read_csv(file_path, sep=';', encoding='utf-8-sig')
    df.columns = df.columns.str.strip()
    
    for col in ['Bulan', 'Kebun', 'Afdeling', 'Kode Afd']:
        if col in df.columns:
            df[col] = df[col].astype(str).str.strip()
            
    kolom_numerik = [
        'Kg Akt.', 'Kg Bgt.', 'Luas', 'Pokok', 'Jjg Akt.', 'Jjg Bgt.', 
        'BJR Akt.', 'BJR Bgt.', 'Ton/ha Akt.', 'Ton/ha Bgt.'
    ]
    for c in kolom_numerik:
        if c in df.columns:
            df[c] = df[c].astype(str).str.replace('.', '', regex=False).str.replace(',', '.', regex=False)
            df[c] = pd.to_numeric(df[c], errors='coerce').fillna(0.0)
            
    kebun_target = ["BKB Inti", "SC Inti", "Setarap", "SC Plasma", "BKB Plasma", "BKB Plasma 1", "FFD Inti", "FFD Plasma"]
    df = df[df['Kebun'].isin(kebun_target)].copy()
    
    st.session_state["df_raw"] = df
    return df

# --- 5. ALUR UTAMA NAVIGASI DASHBOARD ---
if cek_login():
    df_raw = load_and_cache_data()
    
    if df_raw is not None:
        # Konfigurasi Pilihan Bulan di Sidebar
        list_bulan = ["JAN", "FEB", "MAR", "APR", "MEI", "JUN", "JUL", "AGT", "SEP", "OKT", "NOV", "DES"]
        bulan_aktif = df_raw[df_raw['Kg Akt.'] > 0]['Bulan'].unique()
        default_idx = list_bulan.index(bulan_aktif[-1]) if len(bulan_aktif) > 0 else 0
        
        # Simpan variabel global ke session state agar dibaca oleh semua file di folder tabs
        st.session_state["pilihan_bulan"] = st.sidebar.selectbox("Pilih Bulan Analisis:", list_bulan, index=default_idx)
        st.session_state["list_bulan"] = list_bulan
        
        if st.sidebar.button("🚪 Keluar Sistem"):
            st.session_state["otentikasi"] = False
            st.rerun()

        st.sidebar.markdown("---")
        st.sidebar.markdown("**Menu Analisis:**")

        # Deteksi Jalur Absolut Folder 'tabs' agar aman di sistem lokal laptop
        BASE_DIR = os.path.dirname(os.path.abspath(__file__))
        
        path_yield   = os.path.join(BASE_DIR, "tabs", "yield_perf.py")
        path_jp      = os.path.join(BASE_DIR, "tabs", "janjang_pokok.py")
        path_bjr     = os.path.join(BASE_DIR, "tabs", "bjr_perf.py")
        path_trend_b = os.path.join(BASE_DIR, "tabs", "trend_bln.py")
        path_trend_a = os.path.join(BASE_DIR, "tabs", "trend_afd.py")

        # Inisialisasi Halaman Multi-page
        pg_yield   = st.Page(path_yield, title="🌱 Yield Performa (Ton/ha)", icon="🌱")
        pg_jp      = st.Page(path_jp, title="🌴 Janjang / Pokok (J/P)", icon="🌴")
        pg_bjr     = st.Page(path_bjr, title="⚖️ Berat Janjang Rata-rata (BJR)", icon="⚖️")
        pg_trend_b = st.Page(path_trend_b, title="📈 Trend Bulanan Kebun", icon="📊")
        pg_trend_a = st.Page(path_trend_a, title="📈 Trend Afdeling", icon="📊")

        # Jalankan Navigasi Multi-page Streamlit
        pg = st.navigation([pg_yield, pg_jp, pg_bjr, pg_trend_b, pg_trend_a])
        pg.run()