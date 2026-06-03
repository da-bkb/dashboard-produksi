import streamlit as st
import pandas as pd
import os
import numpy as np

# --- 1. KONFIGURASI HALAMAN UTAMA ---
st.set_page_config(
    page_title="Dashboard Production Kelapa Sawit",
    page_icon="🌴",
    layout="wide"
)

# --- 2. SISTEM LOGIN MULTI-DEVICE ---
# Inisialisasi status login di session state agar tersimpan selama browser aktif
if "logged_in" not in st.session_state:
    st.session_state["logged_in"] = False

def aplikasi_utama():
    """Fungsi pembungkus seluruh dashboard utama Bapak jika login berhasil"""
    
    # --- 3. FUNGSI LOADING DATA BERDASARKAN PARAMETER FILTER ---
    @st.cache_data
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
            df = pd.read_csv(file_name, sep=";", decimal=",")
        except:
            df = pd.read_csv(file_name, sep=",", decimal=",")
            
        df.columns = df.columns.str.strip()
        
        if 'Bulan' in df.columns:
            df['Bulan'] = df['Bulan'].astype(str).str.strip().str.upper()
            
        return df, nama_target

    # --- 4. JUDUL DASHBOARD ---
    st.markdown("<h1 style='text-align: center; color: #28348A;'>🌴 DASHBOARD PRODUKSI PT BKB & PT FFD</h1>", unsafe_allow_html=True)
    
    # Tombol Logout diletakkan di pojok kanan atas sidebar/halaman agar rapi
    with st.sidebar:
        st.markdown("### 👤 Sesi Pengguna")
        if st.button("🚪 Keluar / Logout", use_container_width=True):
            st.session_state["logged_in"] = False
            st.rerun()
            
    st.markdown("---")

    # --- 5. SUSUNAN FILTER UTAMA ---
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
        menu_analisis = st.selectbox(
            "📊 Pilih Menu Analisis:",
            ["Yield", "RJP", "BJR", "Trend per Kebun", "Trend per Afdeling"],
            key="menu_dashboard_navigator_main"
        )

    st.markdown("---") 

    # --- 6. VARIABEL GLOBAL KE SESSION STATE ---
    st.session_state["df_raw"] = df_raw
    st.session_state["pilihan_bulan"] = pilihan_bulan
    st.session_state["list_bulan"] = list_bulan

    # --- 7. ROUTING EKSEKUSI FILE SUB-TAB ---
    global_context = globals()

    if menu_analisis == "Yield":
        file_tab = "tabs/yield_perf.py" if pilihan_target == "Budget" else "tabs/yield_sensus.py"
        if os.path.exists(file_tab):
            exec(open(file_tab).read(), global_context)
        else:
            st.warning(f"File '{file_tab}' tidak ditemukan di folder tabs.")

    elif menu_analisis == "RJP":
        file_tab = "tabs/janjang_pokok.py" if pilihan_target == "Budget" else "tabs/janjang_sensus.py"
        if os.path.exists(file_tab):
            exec(open(file_tab).read(), global_context)
        else:
            st.warning(f"File '{file_tab}' tidak ditemukan di folder tabs.")

    elif menu_analisis == "BJR":
        file_tab = "tabs/bjr_perf.py" if pilihan_target == "Budget" else "tabs/bjr_sensus.py"
        if os.path.exists(file_tab):
            exec(open(file_tab).read(), global_context)
        else:
            st.warning(f"File '{file_tab}' tidak ditemukan di folder tabs.")

    elif menu_analisis == "Trend per Kebun":
        file_tab = "tabs/trend_bln.py"
        if os.path.exists(file_tab):
            exec(open(file_tab).read(), global_context)
        else:
            st.info("ℹ️ File 'tabs/trend_bln.py' belum dimasukkan ke folder.")

    elif menu_analisis == "Trend per Afdeling":
        file_tab = "tabs/trend_afd.py"
        if os.path.exists(file_tab):
            exec(open(file_tab).read(), global_context)
        else:
            st.info("ℹ️ File 'tabs/trend_afd.py' belum dimasukkan ke folder.")


# --- 8. LOGIKA GERBANG HALAMAN LOGIN ---
if not st.session_state["logged_in"]:
    # Membuat tampilan box login di tengah layar
    _, col_login, _ = st.columns([1, 1.2, 1])
    with col_login:
        st.markdown("<br><br>", unsafe_allow_html=True)
        st.markdown("<h2 style='text-align: center; color: #28348A;'>🔐 KUNCI AKSES</h2>", unsafe_allow_html=True)
        st.write("Silakan masukkan kredensial internal untuk mengakses Dashboard Produksi Kelapa Sawit.")
        
        # Input form login
        username = st.text_input("Username :", placeholder="Masukkan username")
        password = st.text_input("Password :", type="password", placeholder="Masukkan password")
        
        if st.button("Masuk 🚀", use_container_width=True):
            # Kredensial baru yang sudah diperbarui sesuai instruksi Bapak
            if username == "AGRO" and password == "Satui26!":
                st.session_state["logged_in"] = True
                st.success("Login Berhasil!")
                st.rerun() # Refresh halaman untuk langsung masuk ke dashboard utama
            else:
                st.error("⚠️ Username atau Password salah! Hubungi Tim Analis.")
else:
    # Jika status user sudah True (pernah login di device tersebut), langsung tampilkan aplikasinya
    aplikasi_utama()