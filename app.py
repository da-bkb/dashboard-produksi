import streamlit as st
import pandas as pd
import os
import numpy as np
from datetime import datetime
import importlib.util

# --- KONFIGURASI HALAMAN UTAMA ---
st.set_page_config(
    page_title="Dashboard Produksi Kelapa Sawit",
    page_icon="🌴",
    layout="wide"
)

# =========================================================================
# 🔒 SISTEM LOGIN KEAMANAN DASHBOARD
# =========================================================================
def cek_login():
    if "authenticated" not in st.session_state:
        st.session_state["authenticated"] = False

    if not st.session_state["authenticated"]:
        kolom = st.columns([1, 2, 1])
        with kolom[1]:
            st.markdown("<h2 style='text-align: center;'>🔒 Ruang Log Masuk Sistem</h2>", unsafe_allow_html=True)
            st.markdown("<p style='text-align: center; color: gray;'>Silakan masukkan kredensial untuk mengakses data produksi Satui</p>", unsafe_allow_html=True)
            
            username = st.text_input("Username:")
            password = st.text_input("Password:", type="password")
            tombol_login = st.button("Masuk", use_container_width=True)
            
            if tombol_login:
                if username == "AGRO" and password == "Satui26!":
                    st.session_state["authenticated"] = True
                    st.success("🔑 Akses diterima! Memuat data...")
                    st.rerun()
                else:
                    st.error("⚠️ Username atau Password salah. Silakan coba lagi.")
        return False
    return True

if cek_login():

    # --- PROSES LOADING DATA BERSIH ---
    @st.cache_data
    def load_data(tipe_target):
        if tipe_target == "Capaian terhadap BUDGET":
            file_name = "Rekap26.csv"
        else:
            file_name = "Rekap26_Sns.csv"
            
        if not os.path.exists(file_name):
            return pd.DataFrame()

        try:
            df = pd.read_csv(file_name, sep=";", decimal=",")
        except:
            df = pd.read_csv(file_name, sep=",", decimal=",")
            
        df.columns = df.columns.str.strip()
        
        if 'Bulan' in df.columns:
            df['Bulan'] = df['Bulan'].astype(str).str.strip().str.upper()
            
        for col in df.columns:
            if col not in ['Bulan', 'Kebun', 'Afdeling']:
                if df[col].dtype == 'object':
                    df[col] = df[col].astype(str).str.replace(' ', '', regex=False)
                    df[col] = df[col].str.replace(',', '.', regex=False)
                df[col] = pd.to_numeric(df[col], errors='coerce')
                
        return df

    # =========================================================================
    # 🌴 AREA UTAMA DASHBOARD
    # =========================================================================

    st.sidebar.markdown("### 🔑 Sesi Aktif")
    if st.sidebar.button("Keluar / Log Out"):
        st.session_state["authenticated"] = False
        st.rerun()

    st.title("🌴 Dashboard Performa Produksi Satui")
    st.markdown("---")

    col1, col2, col3 = st.columns([1, 1, 1])

    with col1:
        basis_analisa = st.selectbox(
            "🎯 Basis Target Analisis:",
            ["Capaian terhadap BUDGET", "Capaian terhadap SENSUS"],
            key="main_basis_analisa"
        )

    df_raw = load_data(basis_analisa)

    if df_raw.empty:
        st.error(f"⚠️ Gagal memuat data. File database untuk '{basis_analisa}' tidak ditemukan.")
    else:
        df_raw = df_raw.replace([np.inf, -np.inf], np.nan)

        list_bulan_raw = df_raw["Bulan"].unique().tolist()
        URUTAN_BULAN_STD = ['JAN', 'FEB', 'MAR', 'APR', 'MEI', 'JUN', 'JUL', 'AGT', 'AGS', 'SEP', 'OKT', 'NOV', 'DES']
        list_bulan = [b for b in URUTAN_BULAN_STD if b in list_bulan_raw]

        # Default bulan lalu
        MAP_ANGKA_BULAN = {1: 'JAN', 2: 'FEB', 3: 'MAR', 4: 'APR', 5: 'MEI', 6: 'JUN', 7: 'JUL', 8: 'AGT', 9: 'SEP', 10: 'OKT', 11: 'NOV', 12: 'DES'}
        bulan_sekarang_angka = datetime.now().month
        bulan_lalu_angka = 12 if bulan_sekarang_angka == 1 else bulan_sekarang_angka - 1
        nama_bulan_lalu = MAP_ANGKA_BULAN.get(bulan_lalu_angka, 'JAN')

        default_index_bulan = list_bulan.index(nama_bulan_lalu) if nama_bulan_lalu in list_bulan else 0

        with col2:
            pilihan_bulan = st.selectbox("📅 Bulan Analisis:", list_bulan, index=default_index_bulan, key="global_month_picker_main")

        with col3:
            menu_analisis = st.selectbox(
                "📊 Pilih Menu Analisis:",
                ["Yield", "RJP", "BJR", "Trend Kebun", "Trend Afdeling"],
                key="menu_dashboard_navigator_main"
            )
        
        st.markdown("---") 

        # Fungsi untuk menjalankan skrip tab sebagai modul terisolasi
        def jalan_tab(path_file):
            nama_modul = os.path.splitext(os.path.basename(path_file))[0]
            spec = importlib.util.spec_from_file_location(nama_modul, path_file)
            modul = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(modul)
            # Panggil fungsi inisialisasi yang HARUS ada di setiap file tab
            modul.init_tab(df_raw, pilihan_bulan)

        # Eksekusi tab sesuai pilihan menu
        if menu_analisis == "Yield":
            jalan_tab("tabs/yield_perf.py")
        elif menu_analisis == "RJP":
            jalan_tab("tabs/janjang_pokok.py")
        elif menu_analisis == "BJR":
            jalan_tab("tabs/bjr_perf.py")
        elif menu_analisis == "Trend Afdeling":
            jalan_tab("tabs/trend_afd.py")
        elif menu_analisis == "Trend Kebun":
            jalan_tab("tabs/trend_bln.py")