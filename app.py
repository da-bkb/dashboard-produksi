import streamlit as st
import pandas as pd
import os

# --- 1. KONFIGURASI HALAMAN UTAMA ---
st.set_page_config(
    page_title="Dashboard Yield Performa Kebun & Afdeling",
    page_icon="🌱",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- 2. FUNGSI SIMULASI / LOAD DATA MENTAH ---
@st.cache_data
def load_data():
    """
    Fungsi untuk membaca data. 
    Silakan sesuaikan path atau nama file dengan data aktual Bapak.
    Di bawah ini adalah struktur dummy jika file belum ditemukan.
    """
    # Contoh pembacaan jika menggunakan excel:
    # if os.path.exists("data_yield.xlsx"):
    #     return pd.read_excel("data_yield.xlsx")
    
    # Dummy data generator agar aplikasi langsung jalan tanpa error data hilang
    np_random = pd.Series(range(1, 100)) # Placeholder pemicu
    bulan_list = ['JAN', 'FEB', 'MAR', 'APR', 'MEI', 'JUN', 'JUL', 'AGS', 'SEP', 'OKT', 'NOV', 'DES']
    kebun_list = ['BKB Inti', 'REK Inti', 'SRE Inti']
    afdeling_list = ['A', 'B', 'C', 'D']
    
    rows = []
    for bln in bulan_list:
        for kbn in kebun_list:
            for afd in afdeling_list:
                rows.append({
                    "Bulan": bln,
                    "Kebun": kbn,
                    "Afdeling": afd,
                    "Luas": 500.0 if afd in ['A', 'B'] else 450.0,
                    "Kg Akt.": pd.Series(range(400000, 600000)).sample(1).values[0],
                    "Kg Bgt.": pd.Series(range(420000, 580000)).sample(1).values[0],
                    "Kg Sns.": pd.Series(range(410000, 590000)).sample(1).values[0]
                })
    return pd.DataFrame(rows)

# Load data ke dalam cache
df_input = load_data()

# --- 3. INISIALISASI SESSION STATE GLOBAL ---
if "df_raw" not in st.session_state:
    st.session_state["df_raw"] = df_input

# --- 4. SIDEBAR GLOBAL (FILTER BULAN UTAMA) ---
st.sidebar.image("https://via.placeholder.com/150x50?text=LOGO+PERUSAHAAN", use_container_width=True)
st.sidebar.markdown("## 🎛️ Filter Utama")

# Daftar pilihan bulan berdasarkan data yang ada
list_bulan_data = list(st.session_state["df_raw"]["Bulan"].unique())
if "AGS" in list_bulan_data and "AGUSTUS" not in list_bulan_data:
    # Antisipasi jika user mencari kata kunci panjang atau pendek
    idx_default = list_bulan_data.index("AGS") if "AGS" in list_bulan_data else 0
else:
    idx_default = 0

pilihan_bulan = st.sidebar.selectbox(
    "Pilih Operasional Bulan:", 
    options=list_bulan_data, 
    index=idx_default
)

# Simpan pilihan bulan ke session state agar bisa diakses file tab lain
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

# Inisialisasi 3 Tab Utama sesuai alur kerja
tab_budget, tab_sensus, tab_periodik = st.tabs([
    "📈 Yield vs Budget", 
    "🎯 Yield vs Sensus", 
    "📅 Yield Periodik"
])

# --- 6. PEMANGGILAN MODUL FILE TIAP TAB ---
with tab_budget:
    try:
        # Mengimpor modul secara dinamis dan menjalankannya jika dibungkus fungsi,
        # atau langsung menjalankan script jika ditulis secara top-level execution.
        from tabs import yield_perf
    except ImportError:
        st.error("Gagal memuat file `tabs/yield_perf.py`. Pastikan folder dan file tersebut ada.")

with tab_sensus:
    try:
        from tabs import yield_sensus
    except ImportError:
        st.error("Gagal memuat file `tabs/yield_sensus.py`. Pastikan folder dan file tersebut ada.")

with tab_periodik:
    try:
        from tabs import yield_periodik
    except ImportError:
        st.error("Gagal memuat file `tabs/yield_periodik.py`. Pastikan folder dan file tersebut ada.")