import streamlit as st
import pandas as pd
import os
import numpy as np
import socket

# --- 1. KONFIGURASI HALAMAN UTAMA ---
st.set_page_config(
    page_title="Dashboard Production Kelapa Sawit",
    page_icon="🌴",
    layout="wide"
)

# --- 2. DETEKSI ENVIRONMENT (Lokal vs Server Produksi) ---
def is_local_environment():
    hostname = socket.gethostname().upper()
    if "LAPTOP" in hostname or "DESKTOP" in hostname or "LOCAL" in hostname:
        return True
    return False

IS_LOCAL = is_local_environment()

# --- 3. SISTEM LOGIN MULTI-DEVICE ---
if "logged_in" not in st.session_state:
    st.session_state["logged_in"] = False

# --- 4. FUNGSI LOADING DATA (Global Scope & Dioptimalkan) ---
@st.cache_data(ttl=3600)
def load_data(tipe_target):
    if tipe_target == "Budget":
        file_name = "Rekap26.csv"
        nama_target = "BUDGET"
    else:
        file_name = "Rekap26_Sns.csv"
        nama_target = "SENSUS"
        
    if not os.path.exists(file_name):
        return pd.DataFrame(), nama_target

    try:
        df = pd.read_csv(file_name, sep=";", decimal=",", engine="python")
    except Exception:
        df = pd.read_csv(file_name, sep=",", decimal=",", engine="python")
        
    df.columns = df.columns.str.strip()
    
    if 'Bulan' in df.columns:
        df['Bulan'] = df['Bulan'].astype(str).str.strip().str.upper()
        
    return df, nama_target


def aplikasi_utama():
    """Fungsi pembungkus seluruh dashboard utama jika login berhasil"""
        
    # --- 5. JUDUL DASHBOARD ---
    st.markdown("<h1 style='text-align: center; color: #28348A;'>🌴 DASHBOARD PRODUKSI PT BKB & PT FFD</h1>", unsafe_allow_html=True)
    
    with st.sidebar:
        st.markdown("### 👤 Sesi Pengguna")
        if st.button("🚪 Keluar / Logout", use_container_width=True):
            st.session_state["logged_in"] = False
            st.rerun()
            
    st.markdown("---")

    # --- 6. SUSUNAN FILTER UTAMA ---
    col1, col2, col3 = st.columns([1.5, 1.2, 1.8])

    with col1:
        pilihan_target = st.radio(
            "🎯 Capaian terhadap :",
            ["Budget", "Sensus"],
            horizontal=True,
            key="global_target_type_picker"
        )

    df_raw, nama_target_label = load_data(pilihan_target)

    if df_raw.empty:
        st.error(f"⚠️ File data untuk Analisa {pilihan_target} tidak ditemukan di direktori!")
        st.stop()

    with col2:
        list_bulan_raw = list(df_raw['Bulan'].unique()) if 'Bulan' in df_raw.columns else ['MEI']
        opsi_tambahan = ["CAWU I", "CAWU II", "CAWU III", "SEMESTER I", "SEMESTER II"]
        list_bulan = list_bulan_raw + [opsi for opsi in opsi_tambahan if opsi not in list_bulan_raw]
        default_idx = list_bulan.index("MEI") if "MEI" in list_bulan else 0
        
        pilihan_bulan = st.selectbox(
            "📅 Bulan Analisis:", 
            list_bulan, 
            index=default_idx,
            key="global_month_picker_main"
        )

    with col3:
        # PENAMBAHAN MENU BARU: Korelasi Curah Hujan vs RJP sesuai instruksi resmi Anda
        menu_analisis = st.selectbox(
            "📊 Pilih Menu Analisis:",
            [
                "Yield", 
                "RJP", 
                "BJR", 
                "Trend per Kebun", 
                "Trend per Afdeling", 
                "Korelasi Pupuk vs RJP",
                "Korelasi Pupuk vs BJR",
                "Korelasi Curah Hujan vs RJP"
            ],
            key="menu_dashboard_navigator_main"
        )

    st.markdown("---") 

    # --- 7. VARIABEL GLOBAL KE SESSION STATE ---
    st.session_state["df_raw"] = df_raw
    st.session_state["pilihan_bulan"] = pilihan_bulan
    st.session_state["list_bulan"] = list_bulan

    # --- 8. ROUTING EKSEKUSI FILE SUB-TAB ---
    global_context = globals().copy()
    global_context.update(locals())

    if menu_analisis == "Yield":
        file_tab = "tabs/yield_perf.py" if pilihan_target == "Budget" else "tabs/yield_sensus.py"
    elif menu_analisis == "RJP":
        file_tab = "tabs/janjang_pokok.py" if pilihan_target == "Budget" else "tabs/janjang_sensus.py"
    elif menu_analisis == "BJR":
        file_tab = "tabs/bjr_perf.py" if pilihan_target == "Budget" else "tabs/bjr_sensus.py"
    elif menu_analisis == "Trend per Kebun":
        file_tab = "tabs/trend_bln.py"
    elif menu_analisis == "Trend per Afdeling":
        file_tab = "tabs/trend_afd.py"
    elif menu_analisis == "Korelasi Pupuk vs RJP":
        file_tab = "tabs/executive_rjp_view.py"
    elif menu_analisis == "Korelasi Pupuk vs BJR":
        file_tab = "tabs/executive_bjr_view.py"
    elif menu_analisis == "Korelasi Curah Hujan vs RJP":
        # Routing mengarah ke file baru eksekutif iklim agronomi
        file_tab = "tabs/executive_ch_rjp_view.py"

    if os.path.exists(file_tab):
        try:
            with open(file_tab, "r", encoding="utf-8") as f:
                code = f.read()
            exec(code, global_context)
        except Exception as e:
            st.error(f"💥 Gagal mengeksekusi sub-menu {menu_analisis}: {e}")
    else:
        st.warning(f"⚠️ File '{file_tab}' tidak ditemukan di folder tabs.")


# --- 9. LOGIKA GERBANG HALAMAN LOGIN ---
if not st.session_state["logged_in"]:
    _, col_login, _ = st.columns([1, 1.2, 1])
    with col_login:
        st.markdown("<br><br>", unsafe_allow_html=True)
        st.markdown("<h2 style='text-align: center; color: #28348A;'>🔐 KUNCI AKSES</h2>", unsafe_allow_html=True)
        st.write("Silakan masukkan kredensial internal untuk mengakses Dashboard Produksi Kelapa Sawit.")
        
        with st.form("login_form"):
            username = st.text_input("Username :", placeholder="Masukkan username")
            password = st.text_input("Password :", type="password", placeholder="Masukkan password")
            submit_button = st.form_submit_button("Masuk 🚀", use_container_width=True)
            
            if submit_button:
                if username == "AGRO" and password == "Satui26!":
                    st.session_state["logged_in"] = True
                    st.success("Login Berhasil!")
                    st.rerun()
                else:
                    st.error("⚠️ Username atau Password salah! Hubungi Tim Analis.")
else:
    aplikasi_utama()