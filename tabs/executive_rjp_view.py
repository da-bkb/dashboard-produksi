import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import os
from scipy import stats  # Library regresi linear & Korelasi Pearson

# --- 1. SETTING DEFAULT & LOAD DATA ---
st.markdown("# 🔬 Analisa Korelasi Historis Pemupukan NPK 13 vs RJP (Janjang/Pokok)")
st.markdown("---")

# Mengambil data produksi global dari session state app.py
df_prod_raw = st.session_state["df_raw"].copy()

# Membaca data realisasi pemupukan (Mendukung Multi-Tahun pasca-update)
FILE_PUPUK = "Rkp_Umr_Ppk.csv"

if not os.path.exists(FILE_PUPUK):
    st.error(f"⚠️ File data pemupukan '{FILE_PUPUK}' tidak ditemukan di direktori!")
    st.stop()

# Load data pupuk dengan pemisah titik koma
df_ppk = pd.read_csv(FILE_PUPUK, sep=";", decimal=",", engine="python")
df_ppk.columns = df_ppk.columns.str.strip()
df_ppk['Bulan'] = df_ppk['Bulan'].astype(str).str.strip().str.upper()
df_ppk['Kebun'] = df_ppk['Kebun'].astype(str).str.strip()
df_ppk['Afd'] = df_ppk['Afd'].astype(str).str.strip()

# Pastikan tipe data kolom Tahun pada pupuk adalah integer
if 'Tahun' in df_ppk.columns:
    df_ppk['Tahun'] = df_ppk['Tahun'].astype(int)

# --- 2. FILTER KEBUN & AFDELING ---
list_kebun_bersama = sorted(list(set(df_prod_raw['Kebun'].unique()).intersection(set(df_ppk['Kebun'].unique()))))

if not list_kebun_bersama:
    list_kebun_bersama = list(df_ppk['Kebun'].unique())

col_f1, col_f2, col_f3 = st.columns([1.1, 1.1, 1.8])
with col_f1:
    pilihan_kebun = st.selectbox("📍 Pilih Kebun:", list_kebun_bersama, key="exec_rjp_kebun_picker")
with col_f2:
    df_ppk_sub = df_ppk[df_ppk['Kebun'] == pilihan_kebun]
    list_afd = sorted(list(df_ppk_sub['Afd'].unique()))
    pilihan_afd = st.selectbox("🚪 Pilih Afdeling:", list_afd, key="exec_rjp_afd_picker")
with col_f3:
    # Slider Fleksibel Jeda Pemupukan (0 hingga 48 bulan)
    pilihan_lag = st.slider("⏱️ Lag Bulan Ke Belakang:", min_value=0, max_value=48, value=12, step=1)

# --- 3. PROSES KONSOLIDASI DATA DENGAN KALKULASI KALENDER RIIL ---
URUTAN_BULAN_STD = ['JAN', 'FEB', 'MAR', 'APR', 'MEI', 'JUN', 'JUL', 'AGT', 'SEP', 'OKT', 'NOV', 'DES']
MAPPING_KAPITAL_BARU = {
    'JAN': 'Jan', 'FEB': 'Feb', 'MAR': 'Mar', 'APR': 'Apr', 'MEI': 'Mei', 'JUN': 'Jun',
    'JUL': 'Jul', 'AGT': 'Agt', 'SEP': 'Sep', 'OKT': 'Okt', 'NOV': 'Nov', 'DES': 'Des'
}

# Standarisasi Tahun Produksi Berjalan Saat Ini
TAHUN_PRODUKSI_BERJALAN = 2026

# A. Pemrosesan Data RJP Produksi
df_prod_filtered = df_prod_raw[(df_prod_raw['Kebun'] == pilihan_kebun) & (df_prod_raw['Afdeling'] == pilihan_afd)].copy()
cols_prod = list(df_prod_filtered.columns)

# Deteksi otomatis kolom Janjang Aktual dan Luas HA
COL_JAN_AKT = next((c for c in cols_prod if 'akt' in c.lower() and any(x in c.lower() for x in ['jg', 'jjg', 'jan', 'janjang'])), None)
COL_HA = next((c for c in cols_prod if 'ha' in c.lower() or 'luas' in c.lower()), None)

if df_prod_filtered.empty or not COL_JAN_AKT or not COL_HA:
    st.warning("⚠️ Data janjang atau Luas HA tidak ditemukan untuk kombinasi Kebun dan Afdeling ini.")
    st.stop()

# Ambil informasi Tahun Produksi jika tersedia secara baris per baris pasca-update csv
if 'Tahun' in df_prod_filtered.columns:
    df_prod_map = df_prod_filtered.groupby(['Tahun', 'Bulan']).agg({COL_JAN_AKT: 'sum', COL_HA: 'max'}).reset_index()
else:
    df_prod_map = df_prod_filtered.groupby('Bulan').agg({COL_JAN_AKT: 'sum', COL_HA: 'max'}).reset_index()
    df_prod_map['Tahun'] = TAHUN_PRODUKSI_BERJALAN

df_prod_map['RJP_Aktual'] = df_prod_map[COL_JAN_AKT] / (df_prod_map[COL_HA] * 135)
df_prod_map['Bulan_Idx'] = df_prod_map['Bulan'].apply(lambda x: URUTAN_BULAN_STD.index(x) if x in URUTAN_BULAN_STD else 99)
df_prod_map = df_prod_map[df_prod_map['Bulan_Idx'] != 99]

# TRIMMING PENGAMAN: Potong data produksi HANYA pada bulan yang sudah berjalan (RJP > 0)
df_prod_map = df_prod_map[df_prod_map['RJP_Aktual'] > 0].reset_index(drop=True)

if df_prod_map.empty:
    st.warning("⚠️ Belum ada data aktual RJP (> 0) pada periode ini untuk kalkulasi.")
    st.stop()

# B. Pemrosesan Data Luas Pemupukan (Hsl_krj) Historis dari CSV
df_ppk_filtered = df_ppk[(df_ppk['Kebun'] == pilihan_kebun) & (df_ppk['Afd'] == pilihan_afd)].copy()
df_ppk_filtered['Bulan_Idx'] = df_ppk_filtered['Bulan'].apply(lambda x: URUTAN_BULAN_STD.index(x) if x in URUTAN_BULAN_STD else 99)
df_ppk_filtered = df_ppk_filtered[df_ppk_filtered['Bulan_Idx'] != 99]

# C. ALGORITMA SIKLUS WAKTU MUNDUR KALENDER (KOREKSI TAHUN DAN BULAN)
list_hasil_rekonstruksi = []

for idx, r_prod in df_prod_map.iterrows():
    bln_idx_prod = r_prod['Bulan_Idx']
    current_tahun_prod = int(r_prod['Tahun'])
    
    # Hitung total bulan absolut mundur dari titik waktu panen berjalan riil
    total_bulan_target = (current_tahun_prod * 12 + bln_idx_prod) - pilihan_lag
    
    tahun_pupuk_target = total_bulan_target // 12
    bln_idx_pupuk_target = total_bulan_target % 12
    nama_bulan_pupuk_target = URUTAN_BULAN_STD[bln_idx_pupuk_target]
    
    if 'Tahun' in df_ppk_filtered.columns:
        match_pupuk = df_ppk_filtered[
            (df_ppk_filtered['Tahun'] == tahun_pupuk_target) & 
            (df_ppk_filtered['Bulan_Idx'] == bln_idx_pupuk_target)
        ]
    else:
        # FALLBACK SAMPLING: Toleransi jika file pupuk belum di-update kolom tahunnya
        match_pupuk = df_ppk_filtered[df_ppk_filtered['Bulan_Idx'] == bln_idx_pupuk_target]
        tahun_pupuk_target = 2025
        
    if not match_pupuk.empty:
        val_hsl_krj = match_pupuk['Hsl_krj'].sum()
        val_luas = match_pupuk['Luas'].max()
    else:
        val_hsl_krj = 0.0
        val_luas = 0.0
        
    list_hasil_rekonstruksi.append({
        'Tahun_Prod_YY': str(current_tahun_prod)[2:],
        'Bulan_Idx_Prod': bln_idx_prod,
        'Bulan_Prod': r_prod['Bulan'],
        'RJP_Aktual': r_prod['RJP_Aktual'],
        'Bulan_Idx_Ppk': bln_idx_pupuk_target,
        'Nama_Bulan_Ppk': nama_bulan_pupuk_target,
        'Tahun_Ppk_YY': str(tahun_pupuk_target)[2:],
        'Hsl_krj': val_hsl_krj,
        'Luas': val_luas
    })

df_analisa = pd.DataFrame(list_hasil_rekonstruksi)

# KUNCI UTAMA SORTING: Urutkan DataFrame secara paksa berdasarkan indeks kronologis panen (Jan -> Des)
df_analisa = df_analisa.sort_values('Bulan_Idx_Prod').reset_index(drop=True)


# --- 4. GRAFIK OVERLAY TREN HISTORIS SEJAJAR KRONOLOGIS ---
st.subheader(f"📈 Pengaruh Realisasi Pemupukan (Ha) (Lag {pilihan_lag} Bulan) vs RJP")

fig_overlay = go.Figure()

# Sumbu X bertingkat format formal MM-YY untuk Produksi & Pemupukan (Contoh: Mei-26 di atas, Ppk: Mei-25 di bawah)
x_labels_multiline = []
for idx, r in df_analisa.iterrows():
    nama_bulan_prod = MAPPING_KAPITAL_BARU.get(r['Bulan_Prod'], r['Bulan_Prod'])
    tahun_prod_yy = r['Tahun_Prod_YY']
    
    nama_bulan_pupuk = MAPPING_KAPITAL_BARU.get(r['Nama_Bulan_Ppk'], r['Nama_Bulan_Ppk'])
    tahun_pupuk_yy = r['Tahun_Ppk_YY']
    
    label_gabung = f"{nama_bulan_prod}-{tahun_prod_yy}<br><span style='color:#00B050; font-size:11px; font-weight:bold;'>Ppk: {nama_bulan_pupuk}-{tahun_pupuk_yy}</span>"
    x_labels_multiline.append(label_gabung)

# Sumbu Kiri: RJP (Koreksi Kalimat Keterangan Legend)
fig_overlay.add_trace(go.Scatter(
    x=x_labels_multiline, y=df_analisa["RJP_Aktual"],
    mode='lines+markers', name="RJP (Jjg/Pkk)",
    line=dict(color='#28348A', width=3, shape='spline'),
    marker=dict(size=8, color='#28348A', symbol='circle')
))

# Sumbu Kanan: Hasil Kerja Pemupukan (Ha)
fig_overlay.add_trace(go.Scatter(
    x=x_labels_multiline, y=df_analisa["Hsl_krj"],
    mode='lines+markers', name=f"Luas Aplikasi Pupuk ({pilihan_lag} Bln Lalu)",
    line=dict(color='#00B050', width=2.5, shape='spline', dash='dash'),
    marker=dict(size=7, color='#00B050', symbol='square'),
    yaxis="y2"
))

# LOCK URUTAN CHRONOLOGICAL
fig_overlay.update_layout(
    xaxis=dict(
        title=dict(text="Garis Waktu Hubungan (Baris Atas: Panen Berjalan | Baris Bawah: Aplikasi Pupuk Historis)"),
        type='category',
        categoryorder='array',
        categoryarray=x_labels_multiline
    ),
    yaxis=dict(title=dict(text="RJP (Janjang/Pokok)", font=dict(color="#28348A")), tickfont=dict(color="#28348A")),
    yaxis2=dict(title=dict(text="Luas Aplikasi Pemupukan (Ha/Bulan)", font=dict(color="#00B050")), tickfont=dict(color="#00B050"), overlaying="y", side="right"),
    hovermode="x unified",
    legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
    margin=dict(l=40, r=40, t=30, b=50),
    height=420
)

st.plotly_chart(fig_overlay, use_container_width=True)


# --- 5. VISUALISASI SCATTER PLOT & HITUNG STATISTIK REGRESI DINAMIS ---
st.markdown("---")
col_graph, col_narasi = st.columns([1.3, 1])

x_data = df_analisa['Hsl_krj'].values
y_data = df_analisa['RJP_Aktual'].values

# Kalkulasi statistik linear regression murni antara Luas Pupuk vs RJP
b_slope, a_intercept, r_value, p_value, std_err = stats.linregress(x_data, y_data)
r_squared = r_value ** 2

x_line = np.linspace(x_data.min(), x_data.max(), 100) if len(x_data) > 0 else np.array([0, 1])
y_line = a_intercept + b_slope * x_line

with col_graph:
    # Koreksi Kalimat Judul Sub-tab Scatter Plot
    st.subheader(f"📊 Scatter Plot & Trend RJP (Lag {pilihan_lag} Bulan)")
    
    fig_scatter = go.Figure()
    
    fig_scatter.add_trace(go.Scatter(
        x=x_data, y=y_data,
        mode='markers', name="Bulan Aktif",
        marker=dict(size=12, color='#28348A', opacity=0.8, line=dict(width=1, color='White')),
        text=df_analisa['Bulan_Prod'],
        hovertemplate="<b>Siklus Produksi: %{text}</b><br>Luas Pupuk: %{x:.1f} Ha<br>RJP: %{y:.2f} Jg/Pkk<extra></extra>"
    ))
    
    fig_scatter.add_trace(go.Scatter(
        x=x_line, y=y_line,
        mode='lines', name="Garis Tren",
        line=dict(color='#C62828', width=2)
    ))
    
    # Koreksi Kalimat Axis & Penghapusan Kata 'Variabel X/Y'
    fig_scatter.update_layout(
        xaxis=dict(title=dict(text=f"Luas Aplikasi Pupuk (Ha) - Lag {pilihan_lag} Bulan")),
        yaxis=dict(title=dict(text="RJP (Janjang/Pokok)")),
        margin=dict(l=20, r=20, t=20, b=20),
        height=350,
        showlegend=False
    )
    st.plotly_chart(fig_scatter, use_container_width=True)

with col_narasi:
    # Koreksi Kalimat Sub-judul Narasi Utama & Pembacaan Lokasi Dinamis
    st.subheader("📝 Uraian & Analisa Korelasi Pearson")
    st.markdown(f"Hasil Pemodelan Statistik Aktual Kebun {pilihan_kebun} - Afdeling {pilihan_afd} :")
    
    tanda_b = "+" if b_slope >= 0 else "-"
    formula_text = f"$$y = {a_intercept:.3f} {tanda_b} {abs(b_slope):.3f}x$$"
    st.info(f"**Persamaan Regresi RJP:**\n{formula_text}")
    
    if b_slope >= 0:
        dampak_text = f"**Positif (Searah)**. Pola menunjukkan kesesuaian teori pembentukan buah, setiap penambahan luas aplikasi pupuk sebesar 1 Ha pada {pilihan_lag} bulan lalu berkontribusi meningkatkan jumlah janjang per pokok sebesar `{abs(b_slope):.4f}` Janjang pada bulan berjalan."
    else:
        dampak_text = f"**Negatif (Terbalik)**. Tren data menunjukkan deviasi korelasi terbalik sebesar `{abs(b_slope):.4f}` Janjang/Pokok pada model lag ini."

    st.markdown(f"""
    * **Kekuatan Hubungan Kunci ($R^2$):** `{r_squared:.4f}` (**{r_squared*100:.1f}%** akurasi model terhadap RJP).
    * **Analisa Arah:** Hubungan bersifat {dampak_text}
    """)
    
    # Koreksi Kalimat & Penghapusan Kata Rekomendasi Utama (To The Point)
    st.markdown("##### 📌 Kesimpulan:")
    
    if r_squared >= 0.70:
        st.write(f"🌟 Lag `{pilihan_lag} Bulan` terdeteksi sebagai periode kritis untuk mempertahankan tandan buah dengan nilai $R^2$ yang sangat kuat (`{r_squared:.2f}`). Pasokan NPK 13 pada waktu ini terbukti vital menjaga jumlah janjang sawit agar tidak gugur/aborsi karena kekurangan nutrisi.")
    elif r_squared >= 0.40:
        st.write(f"▼ **Korelasi Moderat:** Lag `{pilihan_lag} Bulan` memengaruhi kuantitas janjang cukup signifikan. Silakan geser slider ke angka bulan lain untuk melacak siklus diferensiasi seks bunga sawit sampai dengan siklus aborsi (biasanya berada pada rentang 9-24 bulan ke belakang) untuk mencari nilai $R^2$ tertinggi.")
    else:
        st.write(f"ℹ️ **Korelasi Lemah/Anomali:** Lag `{pilihan_lag} Bulan` kurang sensitif menjelaskan variasi jumlah janjang. Disarankan menguji angka lag makro yang lebih tinggi untuk melihat efek jangka panjang ketersediaan asupan hara tanaman.")