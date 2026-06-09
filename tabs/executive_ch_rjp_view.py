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

# Membaca data rekap iklim curah hujan dan hari hujan
FILE_IKLIM = "Rkp_ch_hh.csv"

if not os.path.exists(FILE_IKLIM):
    st.error(f"⚠️ File data curah hujan '{FILE_IKLIM}' tidak ditemukan di direktori!")
    st.stop()

# Load data iklim dengan pemisah titik koma dan penanganan decimal koma
df_ch = pd.read_csv(FILE_IKLIM, sep=";", decimal=",", engine="python")
df_ch.columns = df_ch.columns.str.strip()
df_ch['Bulan'] = df_ch['Bulan'].astype(str).str.strip().str.upper()
df_ch['Kebun'] = df_ch['Kebun'].astype(str).str.strip()
df_ch['Afd'] = df_ch['Afd'].astype(str).str.strip()

# Pastikan tipe data kolom Tahun pada iklim adalah integer
if 'Tahun' in df_ch.columns:
    df_ch['Tahun'] = df_ch['Tahun'].astype(int)

# --- 2. FILTER KEBUN & AFDELING (Sesuai SOP Redaksi Singkat Direksi) ---
list_kebun_bersama = sorted(list(set(df_prod_raw['Kebun'].unique()).intersection(set(df_ch['Kebun'].unique()))))

if not list_kebun_bersama:
    list_kebun_bersama = list(df_ch['Kebun'].unique())

col_f1, col_f2, col_f3 = st.columns([1.1, 1.1, 1.8])
with col_f1:
    pilihan_kebun = st.selectbox("📍 Pilih Kebun:", list_kebun_bersama, key="exec_ch_kebun_picker")
with col_f2:
    df_ch_sub = df_ch[df_ch['Kebun'] == pilihan_kebun]
    list_afd = sorted(list(df_ch_sub['Afd'].unique()))
    pilihan_afd = st.selectbox("🚪 Pilih Afdeling:", list_afd, key="exec_ch_afd_picker")
with col_f3:
    # Slider Fleksibel Jeda Iklim Makro Jangka Panjang (0 s.d 48 bulan)
    pilihan_lag = st.slider("⏱️ Lag Bulan Ke Belakang:", min_value=0, max_value=48, value=12, step=1)

# --- 3. PROSES KONSOLIDASI DATA DENGAN KALKULASI KALENDER RIIL ---
URUTAN_BULAN_STD = ['JAN', 'FEB', 'MAR', 'APR', 'MEI', 'JUN', 'JUL', 'AGT', 'SEP', 'OKT', 'NOV', 'DES']
MAPPING_KAPITAL_BARU = {
    'JAN': 'Jan', 'FEB': 'Feb', 'MAR': 'Mar', 'APR': 'Apr', 'MEI': 'Mei', 'JUN': 'Jun',
    'JUL': 'Jul', 'AGT': 'Agt', 'SEP': 'Sep', 'OKT': 'Okt', 'NOV': 'Nov', 'DES': 'Des'
}

TAHUN_PRODUKSI_BERJALAN = 2026

# A. Pemrosesan Data RJP Produksi
df_prod_filtered = df_prod_raw[(df_prod_raw['Kebun'] == pilihan_kebun) & (df_prod_raw['Afdeling'] == pilihan_afd)].copy()
cols_prod = list(df_prod_filtered.columns)

COL_JAN_AKT = next((c for c in cols_prod if 'akt' in c.lower() and any(x in c.lower() for x in ['jg', 'jjg', 'jan', 'janjang'])), None)
COL_HA = next((c for c in cols_prod if 'ha' in c.lower() or 'luas' in c.lower()), None)

if df_prod_filtered.empty or not COL_JAN_AKT or not COL_HA:
    st.warning("⚠️ Data janjang atau Luas HA tidak ditemukan untuk kombinasi Kebun dan Afdeling ini.")
    st.stop()

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

# B. Pemrosesan Data Curah Hujan (Curah_Hujan) Historis
df_ch_filtered = df_ch[(df_ch['Kebun'] == pilihan_kebun) & (df_ch['Afd'] == pilihan_afd)].copy()
df_ch_filtered['Bulan_Idx'] = df_ch_filtered['Bulan'].apply(lambda x: URUTAN_BULAN_STD.index(x) if x in URUTAN_BULAN_STD else 99)
df_ch_filtered = df_ch_filtered[df_ch_filtered['Bulan_Idx'] != 99]

# C. ALGORITMA SIKLUS WAKTU MUNDUR KALENDER TAHUN RIIL
list_hasil_rekonstruksi = []

for idx, r_prod in df_prod_map.iterrows():
    bln_idx_prod = r_prod['Bulan_Idx']
    current_tahun_prod = int(r_prod['Tahun'])
    
    # Hitung mundur total bulan kalender absolut sesuai slider lag
    total_bulan_target = (current_tahun_prod * 12 + bln_idx_prod) - pilihan_lag
    
    tahun_ch_target = total_bulan_target // 12
    bln_idx_ch_target = total_bulan_target % 12
    nama_bulan_ch_target = URUTAN_BULAN_STD[bln_idx_ch_target]
    
    match_ch = df_ch_filtered[
        (df_ch_filtered['Tahun'] == tahun_ch_target) & 
        (df_ch_filtered['Bulan_Idx'] == bln_idx_ch_target)
    ]
        
    if not match_ch.empty:
        val_curah_hujan = match_ch['Curah_Hujan'].sum()
    else:
        val_curah_hujan = 0.0
        
    list_hasil_rekonstruksi.append({
        'Tahun_Prod_YY': str(current_tahun_prod)[2:],
        'Bulan_Idx_Prod': bln_idx_prod,
        'Bulan_Prod': r_prod['Bulan'],
        'RJP_Aktual': r_prod['RJP_Aktual'],
        'Bulan_Idx_CH': bln_idx_ch_target,
        'Nama_Bulan_CH': nama_bulan_ch_target,
        'Tahun_CH_YY': str(tahun_ch_target)[2:],
        'Curah_Hujan': val_curah_hujan
    })

df_analisa = pd.DataFrame(list_hasil_rekonstruksi).sort_values('Bulan_Idx_Prod').reset_index(drop=True)

# --- 4. GRAFIK OVERLAY TREN HISTORIS SEJAJAR KRONOLOGIS ---
st.subheader(f"📈 Pengaruh Curah Hujan (mm) (Lag {pilihan_lag} Bulan) vs RJP")

fig_overlay = go.Figure()

x_labels_multiline = []
for idx, r in df_analisa.iterrows():
    nama_bulan_prod = MAPPING_KAPITAL_BARU.get(r['Bulan_Prod'], r['Bulan_Prod'])
    tahun_prod_yy = r['Tahun_Prod_YY']
    nama_bulan_ch = MAPPING_KAPITAL_BARU.get(r['Nama_Bulan_CH'], r['Nama_Bulan_CH'])
    tahun_ch_yy = r['Tahun_CH_YY']
    
    label_gabung = f"{nama_bulan_prod}-{tahun_prod_yy}<br><span style='color:#00B050; font-size:11px; font-weight:bold;'>CH: {nama_bulan_ch}-{tahun_ch_yy}</span>"
    x_labels_multiline.append(label_gabung)

# Sumbu Kiri: RJP
fig_overlay.add_trace(go.Scatter(
    x=x_labels_multiline, y=df_analisa["RJP_Aktual"],
    mode='lines+markers', name="RJP (Jjg/Pkk)",
    line=dict(color='#28348A', width=3, shape='spline'),
    marker=dict(size=8, color='#28348A', symbol='circle')
))

# Sumbu Kanan: Curah Hujan (mm)
fig_overlay.add_trace(go.Scatter(
    x=x_labels_multiline, y=df_analisa["Curah_Hujan"],
    mode='lines+markers', name=f"Curah Hujan ({pilihan_lag} Bln Lalu)",
    line=dict(color='#00B050', width=2.5, shape='spline', dash='dash'),
    marker=dict(size=7, color='#00B050', symbol='square'),
    yaxis="y2"
))

fig_overlay.update_layout(
    xaxis=dict(title=dict(text="Garis Waktu Hubungan (Baris Atas: Panen Berjalan | Baris Bawah: Rekap Curah Hujan Historis)"), type='category', categoryorder='array', categoryarray=x_labels_multiline),
    yaxis=dict(title=dict(text="RJP (Janjang/Pokok)", font=dict(color="#28348A")), tickfont=dict(color="#28348A")),
    yaxis2=dict(title=dict(text="Curah Hujan (mm)", font=dict(color="#00B050")), tickfont=dict(color="#00B050"), overlaying="y", side="right"),
    hovermode="x unified", legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
    margin=dict(l=40, r=40, t=30, b=50), height=420
)
st.plotly_chart(fig_overlay, use_container_width=True)

# --- 5. VISUALISASI SCATTER PLOT & REGRESI DINAMIS ---
st.markdown("---")
col_graph, col_narasi = st.columns([1.3, 1])

x_data = df_analisa['Curah_Hujan'].values
y_data = df_analisa['RJP_Aktual'].values

# Hitung komponen regresi & Korelasi Pearson otomatis via scipy
b_slope, a_intercept, r_value, p_value, std_err = stats.linregress(x_data, y_data)
r_squared = r_value ** 2

x_line = np.linspace(x_data.min(), x_data.max(), 100) if len(x_data) > 0 else np.array([0, 1])
y_line = a_intercept + b_slope * x_line

with col_graph:
    st.subheader(f"📊 Scatter Plot & Trend RJP (Lag {pilihan_lag} Bulan)")
    
    fig_scatter = go.Figure()
    fig_scatter.add_trace(go.Scatter(x=x_data, y=y_data, mode='markers', marker=dict(size=12, color='#28348A', opacity=0.8, line=dict(width=1, color='White')), text=df_analisa['Bulan_Prod'], hovertemplate="<b>Siklus Panen: %{text}</b><br>Curah Hujan: %{x:.1f} mm<br>RJP: %{y:.2f} Jg/Pkk<extra></extra>"))
    fig_scatter.add_trace(go.Scatter(x=x_line, y=y_line, mode='lines', line=dict(color='#C62828', width=2)))
    
    fig_scatter.update_layout(
        xaxis=dict(title=dict(text=f"Curah Hujan (mm) - Lag {pilihan_lag} Bulan")),
        yaxis=dict(title=dict(text="RJP (Janjang/Pokok)")),
        margin=dict(l=20, r=20, t=20, b=20), height=350, showlegend=False
    )
    st.plotly_chart(fig_scatter, use_container_width=True)

with col_narasi:
    # Sub-judul Uraian & Analisa Korelasi Pearson
    st.subheader("📝 Uraian & Analisa Korelasi Pearson")
    st.markdown(f"Hasil Pemodelan Statistik Aktual Kebun {pilihan_kebun} - Afdeling {pilihan_afd} :")
    
    tanda_b = "+" if b_slope >= 0 else "-"
    formula_text = f"$$y = {a_intercept:.3f} {tanda_b} {abs(b_slope):.3f}x$$"
    st.info(f"**Persamaan Regresi RJP:**\n{formula_text}")
    
    if b_slope >= 0:
        dampak_text = f"**Positif (Searah)**. Pola menunjukkan kesesuaian teori iklim, setiap penambahan intensitas curah hujan pada {pilihan_lag} bulan lalu berkontribusi meningkatkan rasio bunga feminin kelapa sawit pada bulan berjalan."
    else:
        dampak_text = f"**Negatif (Terbalik)**. Tren data menunjukkan deviasi korelasi terbalik pada model lag ini."

    st.markdown(f"""
    * **Kekuatan Hubungan Kunci ($R^2$):** `{r_squared:.4f}` (**{r_squared*100:.1f}%** akurasi model iklim terhadap RJP).
    * **Analisa Arah:** Hubungan bersifat {dampak_text}
    """)
    
    # KORIDOR FIX: Posisi Kesimpulan diletakkan di bawah Uraian Analisa dengan interpretasi dinamis "per 1 mm"
    st.markdown("##### 📌 Kesimpulan:")
    
    if r_squared >= 0.70:
        if b_slope >= 0:
            st.write(f"🌟 Lag `{pilihan_lag} Bulan` terdeteksi sebagai periode kritis untuk mempertahankan tandan buah dengan nilai $R^2$ yang sangat kuat (`{r_squared:.2f}`). Setiap **kenaikan 1 mm curah hujan** pada periode tersebut berpengaruh terhadap **peningkatan jumlah janjang sawit (RJP)** sebesar `{abs(b_slope):.5f}` janjang/pokok pada bulan berjalan, karena terpenuhinya kebutuhan air optimal tanaman untuk menekan laju aborsi bakal buah.")
        else:
            st.write(f"🌟 Lag `{pilihan_lag} Bulan` terdeteksi sebagai periode kritis untuk mempertahankan tandan buah dengan nilai $R^2$ yang sangat kuat (`{r_squared:.2f}`). Namun, arah koefisien menunjukkan hubungan terbalik. Setiap **kenaikan 1 mm curah hujan** berpengaruh terhadap **penurunan RJP** sebesar `{abs(b_slope):.5f}` janjang/pokok, mengindikasikan adanya intensitas hujan berlebih (*over-wetting*) yang berisiko mengganggu efektivitas penyerapan hara.")

    elif r_squared >= 0.40:
        if b_slope >= 0:
            st.write(f"▼ **Korelasi Moderat:** Lag `{pilihan_lag} Bulan` memengaruhi kuantitas janjang cukup signifikan dengan nilai $R^2$ (`{r_squared:.2f}`). Setiap **kenaikan 1 mm curah hujan** berpengaruh terhadap **kenaikan RJP** sebesar `{abs(b_slope):.5f}` janjang/pokok. Silakan geser slider ke angka bulan lain untuk melacak siklus diferensiasi seks bunga sawit sampai dengan siklus aborsi (biasanya berada pada rentang 9-24 bulan ke belakang) untuk mencari nilai $R^2$ tertinggi.")
        else:
            st.write(f"▼ **Korelasi Moderat:** Lag `{pilihan_lag} Bulan` memengaruhi kuantitas janjang cukup signifikan dengan nilai $R^2$ (`{r_squared:.2f}`). Setiap **kenaikan 1 mm curah hujan** justru berpengaruh terhadap **penurunan RJP** sebesar `{abs(b_slope):.5f}` janjang/pokok. Silakan eksplorasi slider lag bulan lainnya untuk memetakan puncak cekaman air (*water stress*) tanaman secara lebih presisi.")

    else:
        st.write(f"ℹ️ **Korelasi Lemah/Anomali:** Lag `{pilihan_lag} Bulan` kurang sensitif menjelaskan variasi jumlah janjang. Secara matematis, setiap **kenaikan 1 mm curah hujan** hanya berpengaruh marginal sebesar `{b_slope:+.5f}` terhadap perubahan nilai RJP. Disarankan menguji angka lag makro yang lebih tinggi (seperti rentang 18-24 bulan ke belakang) untuk melihat efek jangka panjang kumulatif dari kecukupan air terhadap pergeseran rasio seks (*sex ratio*) bunga kelapa sawit.")