import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import os
from scipy import stats  # Library regresi linear & Korelasi Pearson

# --- 1. SETTING DEFAULT & LOAD DATA ---
st.markdown("# 🔬 Analisa Korelasi Historis Pemupukan NPK 13 vs BJR (Kg/Jjg)")
st.markdown("---")

# Mengambil data produksi global dari session state app.py
df_prod_raw = st.session_state["df_raw"].copy()

# Membaca data realisasi pemupukan
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
    pilihan_kebun = st.selectbox("📍 Pilih Kebun:", list_kebun_bersama, key="exec_bjr_kebun_picker")
with col_f2:
    df_ppk_sub = df_ppk[df_ppk['Kebun'] == pilihan_kebun]
    list_afd = sorted(list(df_ppk_sub['Afd'].unique()))
    pilihan_afd = st.selectbox("🚪 Pilih Afdeling:", list_afd, key="exec_bjr_afd_picker")
with col_f3:
    # Mengunci slider dari 1 s.d. 6 bulan sesuai formula jendela pemupukan pendek Anda
    pilihan_lag = st.slider("⏱️ Lag Bulan Ke Belakang:", min_value=1, max_value=6, value=4, step=1)

# --- 3. PROSES KONSOLIDASI DATA DENGAN ALGORITMA JENDELA DINAMIS RUMUS USER ---
URUTAN_BULAN_STD = ['JAN', 'FEB', 'MAR', 'APR', 'MEI', 'JUN', 'JUL', 'AGT', 'SEP', 'OKT', 'NOV', 'DES']
MAPPING_KAPITAL_BARU = {
    'JAN': 'Jan', 'FEB': 'Feb', 'MAR': 'Mar', 'APR': 'Apr', 'MEI': 'Mei', 'JUN': 'Jun',
    'JUL': 'Jul', 'AGT': 'Agt', 'SEP': 'Sep', 'OKT': 'Okt', 'NOV': 'Nov', 'DES': 'Des'
}

TAHUN_PRODUKSI_BERJALAN = 2026

# A. Pemrosesan Data BJR Produksi
df_prod_filtered = df_prod_raw[(df_prod_raw['Kebun'] == pilihan_kebun) & (df_prod_raw['Afdeling'] == pilihan_afd)].copy()
cols_prod = list(df_prod_filtered.columns)

COL_KG_AKT = next((c for c in cols_prod if 'akt' in c.lower() and ('kg' in c.lower() or 'prod' in c.lower())), None)
COL_JAN_AKT = next((c for c in cols_prod if 'akt' in c.lower() and any(x in c.lower() for x in ['jg', 'jjg', 'jan', 'janjang'])), None)

if df_prod_filtered.empty or not COL_KG_AKT or not COL_JAN_AKT:
    st.warning("⚠️ Data produksi Kg atau Janjang tidak ditemukan untuk kombinasi Kebun dan Afdeling ini.")
    st.stop()

if 'Tahun' in df_prod_filtered.columns:
    df_prod_map = df_prod_filtered.groupby(['Tahun', 'Bulan']).agg({COL_KG_AKT: 'sum', COL_JAN_AKT: 'sum'}).reset_index()
else:
    df_prod_map = df_prod_filtered.groupby('Bulan').agg({COL_KG_AKT: 'sum', COL_JAN_AKT: 'sum'}).reset_index()
    df_prod_map['Tahun'] = TAHUN_PRODUKSI_BERJALAN

# Hitung BJR Bulanan Aktual (Kg/Janjang)
df_prod_map['BJR_Aktual'] = np.where(df_prod_map[COL_JAN_AKT] > 0, df_prod_map[COL_KG_AKT] / df_prod_map[COL_JAN_AKT], 0)
df_prod_map['Bulan_Idx'] = df_prod_map['Bulan'].apply(lambda x: URUTAN_BULAN_STD.index(x) if x in URUTAN_BULAN_STD else 99)
df_prod_map = df_prod_map[df_prod_map['Bulan_Idx'] != 99]

# TRIMMING PENGAMAN: Potong data produksi HANYA pada bulan yang sudah berjalan (BJR > 0)
df_prod_map = df_prod_map[df_prod_map['BJR_Aktual'] > 0].reset_index(drop=True)

if df_prod_map.empty:
    st.warning("⚠️ Belum ada data aktual BJR (> 0) pada periode ini untuk kalkulasi.")
    st.stop()

# B. Pemrosesan Data Luas Pemupukan Bersih dari CSV
df_ppk_filtered = df_ppk[(df_ppk['Kebun'] == pilihan_kebun) & (df_ppk['Afd'] == pilihan_afd)].copy()
df_ppk_filtered['Bulan_Idx'] = df_ppk_filtered['Bulan'].apply(lambda x: URUTAN_BULAN_STD.index(x) if x in URUTAN_BULAN_STD else 99)
df_ppk_filtered = df_ppk_filtered[df_ppk_filtered['Bulan_Idx'] != 99]


# C. IMPLEMENTASI RIGID ALGORITMA JENDELA DINAMIS ANDA
list_hasil_rekonstruksi = []

for idx, r_prod in df_prod_map.iterrows():
    bln_idx_prod = r_prod['Bulan_Idx']
    current_tahun_prod = int(r_prod['Tahun'])
    
    total_bulan_prod_absolut = current_tahun_prod * 12 + bln_idx_prod
    
    # 1. Tentukan titik awal (Bulan Tertua) berdasarkan Lag pilihan
    total_bulan_awal_absolut = total_bulan_prod_absolut - pilihan_lag
    
    # 2. Tentukan titik akhir (Bulan Terbaru) berdasarkan aturan pemotongan maksimum bulan panen berjalan
    if pilihan_lag >= 3:
        # Aturan 4 Bulan: Titik awal + 3 bulan ke depan
        total_bulan_akhir_absolut = total_bulan_awal_absolut + 3
    else:
        # Lag 2 dan Lag 1: Dipotong paksa berhenti tepat di bulan panen berjalan
        total_bulan_akhir_absolut = total_bulan_prod_absolut
        
    total_luas_akumulasi_ha = 0.0
    list_komponen_bulan_label = []
    
    # Lakukan loop penjumlahan dari bulan awal sampai bulan akhir secara riil
    for m_abs in range(total_bulan_awal_absolut, total_bulan_akhir_absolut + 1):
        tahun_pupuk_target = m_abs // 12
        bln_idx_pupuk_target = m_abs % 12
        
        if 'Tahun' in df_ppk_filtered.columns:
            match_row = df_ppk_filtered[
                (df_ppk_filtered['Tahun'] == tahun_pupuk_target) & 
                (df_ppk_filtered['Bulan_Idx'] == bln_idx_pupuk_target)
            ]
        else:
            match_row = df_ppk_filtered[df_ppk_filtered['Bulan_Idx'] == bln_idx_pupuk_target]
            tahun_pupuk_target = 2025
            
        if not match_row.empty:
            total_luas_akumulasi_ha += match_row['Hsl_krj'].sum()
            
        # Simpan label untuk penamaan batas rentang
        if m_abs == total_bulan_awal_absolut or m_abs == total_bulan_akhir_absolut:
            nama_bln_singkat = MAPPING_KAPITAL_BARU.get(URUTAN_BULAN_STD[bln_idx_pupuk_target], URUTAN_BULAN_STD[bln_idx_pupuk_target])
            list_komponen_bulan_label.append(f"{nama_bln_singkat}-{str(tahun_pupuk_target)[2:]}")
            
    # Membuat label dinamis teks rentang pupuk sumbu X
    if len(list_komponen_bulan_label) > 1 and list_komponen_bulan_label[0] != list_komponen_bulan_label[1]:
        label_rentang_pupuk = f"{list_komponen_bulan_label[0]} s/d {list_komponen_bulan_label[1]}"
    else:
        label_rentang_pupuk = f"{list_komponen_bulan_label[0]}"
        
    list_hasil_rekonstruksi.append({
        'Tahun_Prod_YY': str(current_tahun_prod)[2:],
        'Bulan_Idx_Prod': bln_idx_prod,
        'Bulan_Prod': r_prod['Bulan'],
        'BJR_Aktual': r_prod['BJR_Aktual'],
        'Label_Rentang_Pupuk': label_rentang_pupuk,
        'Hsl_krj': total_luas_akumulasi_ha
    })

df_analisa = pd.DataFrame(list_hasil_rekonstruksi).sort_values('Bulan_Idx_Prod').reset_index(drop=True)


# --- 4. GRAFIK OVERLAY TREN HISTORIS SEJAJAR KRONOLOGIS ---
st.subheader(f"📈 Pengaruh Realisasi Pemupukan (Ha) (Lag {pilihan_lag} Bulan) vs BJR")

fig_overlay = go.Figure()

x_labels_multiline = []
for idx, r in df_analisa.iterrows():
    nama_bulan_prod = MAPPING_KAPITAL_BARU.get(r['Bulan_Prod'], r['Bulan_Prod'])
    tahun_prod_yy = r['Tahun_Prod_YY']
    rentang_pupuk_text = r['Label_Rentang_Pupuk']
    
    label_gabung = f"{nama_bulan_prod}-{tahun_prod_yy}<br><span style='color:#00B050; font-size:11px; font-weight:bold;'>Ppk: {rentang_pupuk_text}</span>"
    x_labels_multiline.append(label_gabung)

# Sumbu Kiri: BJR (Kg/Jjg)
fig_overlay.add_trace(go.Scatter(
    x=x_labels_multiline, y=df_analisa["BJR_Aktual"],
    mode='lines+markers', name="BJR (Kg/Jjg)",
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

fig_overlay.update_layout(
    xaxis=dict(title=dict(text="Garis Waktu Hubungan (Baris Atas: Panen Berjalan | Baris Bawah: Jendela Akumulasi Aplikasi Pupuk)"), type='category', categoryorder='array', categoryarray=x_labels_multiline),
    yaxis=dict(title=dict(text="BJR (Kilogram/Janjang)", font=dict(color="#28348A")), tickfont=dict(color="#28348A")),
    yaxis2=dict(title=dict(text="Luas Aplikasi Pemupukan (Ha/Bulan)", font=dict(color="#00B050")), tickfont=dict(color="#00B050"), overlaying="y", side="right"),
    hovermode="x unified", legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
    margin=dict(l=40, r=40, t=30, b=50), height=420
)
st.plotly_chart(fig_overlay, use_container_width=True)


# --- 5. VISUALISASI SCATTER PLOT & REGRESI DINAMIS ---
st.markdown("---")
col_graph, col_narasi = st.columns([1.3, 1])

x_data = df_analisa['Hsl_krj'].values
y_data = df_analisa['BJR_Aktual'].values

b_slope, a_intercept, r_value, p_value, std_err = stats.linregress(x_data, y_data)
r_squared = r_value ** 2

x_line = np.linspace(x_data.min(), x_data.max(), 100) if len(x_data) > 0 else np.array([0, 1])
y_line = a_intercept + b_slope * x_line

with col_graph:
    st.subheader(f"📊 Scatter Plot & Trend BJR (Lag {pilihan_lag} Bulan)")
    
    fig_scatter = go.Figure()
    fig_scatter.add_trace(go.Scatter(x=x_data, y=y_data, mode='markers', marker=dict(size=12, color='#28348A', opacity=0.8, line=dict(width=1, color='White')), text=df_analisa['Bulan_Prod'], hovertemplate="<b>Siklus Panen: %{text}</b><br>Total Luas Pupuk: %{x:.1f} Ha<br>BJR: %{y:.2f} Kg/Jjg<extra></extra>"))
    fig_scatter.add_trace(go.Scatter(x=x_line, y=y_line, mode='lines', line=dict(color='#C62828', width=2)))
    
    fig_scatter.update_layout(xaxis=dict(title=dict(text=f"Luas Aplikasi Pupuk (Ha) - Lag {pilihan_lag} Bulan")), yaxis=dict(title=dict(text="BJR (Kg/Janjang)")), margin=dict(l=20, r=20, t=20, b=20), height=350, showlegend=False)
    st.plotly_chart(fig_scatter, use_container_width=True)

with col_narasi:
    st.subheader("📝 Uraian & Analisa Korelasi Pearson")
    st.markdown(f"Hasil Pemodelan Statistik Aktual Kebun {pilihan_kebun} - Afdeling {pilihan_afd} :")
    
    tanda_b = "+" if b_slope >= 0 else "-"
    formula_text = f"$$y = {a_intercept:.3f} {tanda_b} {abs(b_slope):.3f}x$$"
    st.info(f"**Persamaan Regresi BJR:**\n{formula_text}")
    
    st.markdown(f"""
    * **Kekuatan Hubungan Kunci ($R^2$):** `{r_squared:.4f}` (**{r_squared*100:.1f}%** akurasi model terhadap BJR).
    * **Analisa Arah:** Hubungan bersifat {"**Positif (Searah)**" if b_slope >= 0 else "**Negatif (Terbalik)**"}.
    """)
    
    st.markdown("##### 📌 Kesimpulan:")
    if r_squared >= 0.70:
        st.write(f"🌟 Lag `{pilihan_lag} Bulan` terdeteksi sebagai periode kritis *Nutrient Filling Stage* (asimilasi hara instan) dengan nilai $R^2$ yang sangat kuat (`{r_squared:.2f}`). Aplikasi pupuk dalam jendela waktu pendek ini terbukti vital mengonversi berat janjang sawit agar padat dan optimal saat dipanen.")
    elif r_squared >= 0.40:
        st.write(f"▼ **Korelasi Moderat:** Lag `{pilihan_lag} Bulan` memengaruhi fluktuasi berat janjang cukup signifikan. Silakan geser slider dari 1-6 bulan untuk menemukan puncak kecepatan translokasi hara dari pelepah ke tandan buah untuk mencari nilai $R^2$ tertinggi.")
    else:
        st.write(f"ℹ️ **Korelasi Lemah/Anomali:** Lag `{pilihan_lag} Bulan` kurang sensitif menjelaskan variasi berat janjang melalui data luas Ha. Direksi disarankan melihat korelasi ini setelah file CSV diperbarui dengan data **Dosis Tonase Aplikasi/Ha** agar fluktuasi hara jangka pendek terekam lebih linier.")