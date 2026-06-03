import streamlit as st
import pandas as pd
import os
import numpy as np
from datetime import datetime

# --- KONFIGURASI HALAMAN UTAMA ---
st.set_page_config(
    page_title="Dashboard Produksi Kelapa Sawit",
    page_icon="🌴",
    layout="wide"
)

# =========================================================================
# 🔒 SISTEM LOGIN KEAMANAN DASHBOARD (FINAL)
# =========================================================================
def cek_login():
    """Fungsi untuk memeriksa status login pengguna"""
    if "authenticated" not in st.session_state:
        st.session_state["authenticated"] = False

    if not st.session_state["authenticated"]:
        # Tampilan Form Login dengan susunan kolom rapi
        kolom = st.columns([1, 2, 1])
        with kolom[1]:
            st.markdown("<h2 style='text-align: center;'>🔒 Ruang Log Masuk Sistem</h2>", unsafe_allow_html=True)
            st.markdown("<p style='text-align: center; color: gray;'>Silakan masukkan kredensial untuk mengakses data produksi Satui</p>", unsafe_allow_html=True)
            
            username = st.text_input("Username:")
            password = st.text_input("Password:", type="password")
            tombol_login = st.button("Masuk", use_container_width=True)
            
            if tombol_login:
                if username == "AGRO" and password == "Satui26.":
                    st.session_state["authenticated"] = True
                    st.success("🔑 Akses diterima! Memuat data...")
                    st.rerun()
                else:
                    st.error("⚠️ Username atau Password salah. Silakan coba lagi.")
        return False
    return True

# Jalankan proteksi login sebelum mengeksekusi dashboard utama
if cek_login():

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
                
        # Sinkronisasi alias kolom Sensus agar grafik & tabel YTD tetap normal
        if nama_target == "SENSUS":
            if 'Jjg Sns.' in df.columns: df['Jjg Bgt.'] = df['Jjg Sns.']
            if 'Kg Sns.' in df.columns:  df['Kg Bgt.'] = df['Kg Sns.']
            if 'BJR Sns.' in df.columns: df['BJR Bgt.'] = df['BJR Sns.']
            if 'Ton/ha Sns.' in df.columns: df['Ton/ha Bgt.'] = df['Ton/ha Sns.']
                
        return df, nama_target


    # =========================================================================
    # 🌴 AREA UTAMA DASHBOARD
    # =========================================================================

    # Sidebar Keluar Sesi
    st.sidebar.markdown("### 🔑 Sesi Aktif")
    if st.sidebar.button("Keluar / Log Out"):
        st.session_state["authenticated"] = False
        st.rerun()

    st.title("🌴 Dashboard Performa Produksi Satui")
    st.markdown("Silakan atur basis analisis, periode bulan, dan menu grafik pada panel di bawah ini:")
    st.markdown("---")

    col1, col2, col3 = st.columns([1, 1, 1])

    with col1:
        basis_analisa = st.selectbox(
            "🎯 1. Basis Target Analisis:",
            ["Capaian terhadap BUDGET", "Capaian terhadap SENSUS"],
            key="main_basis_analisa"
        )

    df_raw, nama_target = load_data(basis_analisa)

    if df_raw.empty:
        st.error(f"⚠️ Gagal memuat data. File database '{basis_analisa}' tidak ditemukan.")
    else:
        df_raw = df_raw.replace([np.inf, -np.inf], np.nan)

        list_bulan_raw = df_raw["Bulan"].unique().tolist()
        URUTAN_BULAN_STD = ['JAN', 'FEB', 'MAR', 'APR', 'MEI', 'JUN', 'JUL', 'AGT', 'AGS', 'SEP', 'OKT', 'NOV', 'DES']
        list_bulan = [b for b in URUTAN_BULAN_STD if b in list_bulan_raw]
        for b in list_bulan_raw:
            if b not in list_bulan:
                list_bulan.append(b)

        # Logika Otomatis Menampilkan Data Bulan Lalu (-1 Bulan Berjalan)
        MAP_ANGKA_BULAN = {1: 'JAN', 2: 'FEB', 3: 'MAR', 4: 'APR', 5: 'MEI', 6: 'JUN', 7: 'JUL', 8: 'AGT', 9: 'SEP', 10: 'OKT', 11: 'NOV', 12: 'DES'}
        bulan_sekarang_angka = datetime.now().month
        
        bulan_lalu_angka = 12 if bulan_sekarang_angka == 1 else bulan_sekarang_angka - 1
        nama_bulan_lalu = MAP_ANGKA_BULAN.get(bulan_lalu_angka, 'JAN')

        if nama_bulan_lalu in list_bulan:
            default_index_bulan = list_bulan.index(nama_bulan_lalu)
        else:
            default_index_bulan = 0 

        with col2:
            pilihan_bulan = st.selectbox(
                "📅 2. Bulan Analisis:", 
                list_bulan, 
                index=default_index_bulan,
                key="global_month_picker_main"
            )

        st.session_state["df_raw"] = df_raw
        st.session_state["pilihan_bulan"] = pilihan_bulan
        st.session_state["list_bulan"] = list_bulan

        with col3:
            # Urutan menu yang sudah fix sesuai instruksi Bapak
            menu_analisis = st.selectbox(
                "📊 3. Pilih Menu Analisis:",
                ["Yield", "RJP", "BJR", "Trend Kebun", "Trend Afdeling"],
                key="menu_dashboard_navigator_main"
            )
        
        st.markdown("---") 

        global_context = globals()

        # Eksekusi tab sesuai pilihan menu
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