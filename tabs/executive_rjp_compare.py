import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import os
from scipy import stats

# --- 1. SETTING DEFAULT & LOAD DATA ---
st.markdown("# 📊 Dashboard Komparasi Tren RJP")
st.markdown("---")

FILE_PRODUKSI = "Trend_produksi_satui.csv"

if not os.path.exists(FILE_PRODUKSI):
    st.error("⚠️ File 'Trend_produksi_satui.csv' tidak ditemukan di direktori!")
    st.stop()

# Load Data Produksi Multi-Tahun
df_prod = pd.read_csv(FILE_PRODUKSI, sep=";", decimal=",", engine="python")
df_prod.columns = df_prod.columns.str.strip().str.upper()
df_prod['BULAN'] = df_prod['BULAN'].astype(str).str.strip().str.upper()
df_prod['KEBUN'] = df_prod['KEBUN'].astype(str).str.strip().str.upper()

# Urutan bulan standar untuk konversi indeks kalender
URUTAN_BULAN_STD = ['JAN', 'FEB', 'MAR', 'APR', 'MEI', 'JUN', 'JUL', 'AGT', 'SEP', 'OKT', 'NOV', 'DES']
MAPPING_KAPITAL_BARU = {
    'JAN': 'Jan', 'FEB': 'Feb', 'MAR': 'Mar', 'APR': 'Apr', 'MEI': 'Mei', 'JUN': 'Jun',
    'JUL': 'Jul', 'AGT': 'Agt', 'SEP': 'Sep', 'OKT': 'Okt', 'NOV': 'Nov', 'DES': 'Des'
}

# --- 2. FILTER KEBUN ANALISIS ---
list_kebun = sorted(list(df_prod['KEBUN'].unique()))
pilihan_kebun = st.selectbox("📍 Pilih Kebun Analisis:", list_kebun, key="compare_rjp_kebun_picker")

# --- 3. PROSES KONSOLIDASI DATA KRONOLOGIS MASTER ---
df_filtered = df_prod[df_prod['KEBUN'] == pilihan_kebun].copy()
df_filtered['BULAN_IDX'] = df_filtered['BULAN'].apply(lambda x: URUTAN_BULAN_STD.index(x) if x in URUTAN_BULAN_STD else 99)
df_filtered = df_filtered[df_filtered['BULAN_IDX'] != 99]

# Hitung RJP bulanan aktual
df_filtered['RJP_AKTUAL'] = df_filtered['AKT_JJG'] / df_filtered['POKOK']
df_filtered = df_filtered[df_filtered['RJP_AKTUAL'] > 0].reset_index(drop=True)

# Urutan absolut kalender runtun waktu
df_filtered['URUTAN_ABS'] = df_filtered['TAHUN'] * 12 + df_filtered['BULAN_IDX']
df_master = df_filtered.sort_values('URUTAN_ABS').reset_index(drop=True)

if df_master.empty:
    st.warning("⚠️ Tidak ada data produksi aktual untuk kebun terpilih.")
    st.stop()

list_tahun_tersedia = sorted(list(df_master['TAHUN'].unique()))
list_bulan_tampil = ['Jan', 'Feb', 'Mar', 'Apr', 'Mei', 'Jun', 'Jul', 'Agt', 'Sep', 'Okt', 'Nov', 'Des']

# --- 4. SELEKTOR DUAL-TIMELINE SINKRON (PERIODE TREN A VS PERIODE TREN B) ---
st.markdown("##### 🟢 Atur Rentang Waktu - PERIODE TREN A (Garis Hijau)")
col_a1, col_a2, col_a3, col_a4 = st.columns(4)
with col_a1:
    p_bln_start_a = st.selectbox("Bulan Awal (A):", list_bulan_tampil, index=0, key="start_month_a")
with col_a2:
    p_thn_start_a = st.selectbox("Tahun Awal (A):", list_tahun_tersedia, index=0, key="start_year_a")
with col_a3:
    p_bln_end_a = st.selectbox("Bulan Akhir (A):", list_bulan_tampil, index=len(list_bulan_tampil)-1, key="end_month_a")
with col_a4:
    p_thn_end_a = st.selectbox("Tahun Akhir (A):", list_tahun_tersedia, index=0, key="end_year_a")

st.markdown("##### 🔵 Atur Rentang Waktu - PERIODE TREN B (Garis Biru)")
col_b1, col_b2, col_b3, col_b4 = st.columns(4)
with col_b1:
    p_bln_start_b = st.selectbox("Bulan Awal (B):", list_bulan_tampil, index=0, key="start_month_b")
with col_b2:
    p_thn_start_b = st.selectbox("Tahun Awal (B):", list_tahun_tersedia, index=len(list_tahun_tersedia)-1, key="start_year_b")
with col_b3:
    p_bln_end_b = st.selectbox("Bulan Akhir (B):", list_bulan_tampil, index=len(list_bulan_tampil)-1, key="end_month_b")
with col_b4:
    p_thn_end_b = st.selectbox("Tahun Akhir (B):", list_tahun_tersedia, index=len(list_tahun_tersedia)-1, key="end_year_b")

# Ekstraksi Nilai Absolut Kalender
abs_start_a = p_thn_start_a * 12 + list_bulan_tampil.index(p_bln_start_a)
abs_end_a = p_thn_end_a * 12 + list_bulan_tampil.index(p_bln_end_a)

abs_start_b = p_thn_start_b * 12 + list_bulan_tampil.index(p_bln_start_b)
abs_end_b = p_thn_end_b * 12 + list_bulan_tampil.index(p_bln_end_b)

if abs_start_a > abs_end_a or abs_start_b > abs_end_b:
    st.error("❌ Eror: Bulan-Tahun Awal tidak boleh melewati Bulan-Tahun Akhir pada masing-masing periode!")
    st.stop()

# Segmentasi Data Berdasarkan Filter Berpasangan
df_tren_a = df_master[(df_master['URUTAN_ABS'] >= abs_start_a) & (df_master['URUTAN_ABS'] <= abs_end_a)].copy().reset_index(drop=True)
df_tren_b = df_master[(df_master['URUTAN_ABS'] >= abs_start_b) & (df_master['URUTAN_ABS'] <= abs_end_b)].copy().reset_index(drop=True)

if df_tren_a.empty or df_tren_b.empty:
    st.warning("⚠️ Salah satu atau kedua rentang periode yang Anda pilih tidak memiliki rekaman data.")
    st.stop()

# --- 5. GRAFIK OVERLAY TREN BERSAMBUNG BERPASANGAN ---
st.markdown(f"##### 📈 Trend RJP: Periode A vs Periode B")

fig_overlay = go.Figure()

# Pembuatan Label X Riil Berformat MM-YY (Jan-22, Jan-26, dst.)
labels_raw_a = [f"{MAPPING_KAPITAL_BARU.get(r['BULAN'])}-{str(r['TAHUN'])[2:]}" for idx, r in df_tren_a.iterrows()]
labels_raw_b = [f"{MAPPING_KAPITAL_BARU.get(r['BULAN'])}-{str(r['TAHUN'])[2:]}" for idx, r in df_tren_b.iterrows()]

# Warnai label teks sumbu X menggunakan HTML Span mengikuti warna garis penandanya
labels_html_a = [f"<span style='color:#00B050; font-weight:bold;'>{lbl}</span>" for lbl in labels_raw_a]
labels_html_b = [f"<span style='color:#28348A; font-weight:bold;'>{lbl}</span>" for lbl in labels_raw_b]

# REVISI STRUKTUR AXIS: Menggabungkan memanjang horizontal dengan pemisah titik dua " : "
max_len = max(len(df_tren_a), len(df_tren_b))
x_axis_combined_labels = []

for i in range(max_len):
    label_komponen = []
    if i < len(labels_html_a):
        label_komponen.append(labels_html_a[i])
    if i < len(labels_html_b):
        label_komponen.append(labels_html_b[i])
    
    # Gabungkan sejajar horizontal menggunakan separator titik dua " : " sesuai instruksi Anda
    x_axis_combined_labels.append(" : ".join(label_komponen))

# Trace Garis Periode A (Garis Hijau #00B050)
fig_overlay.add_trace(go.Scatter(
    x=x_axis_combined_labels[:len(df_tren_a)], y=df_tren_a["RJP_AKTUAL"],
    mode='lines+markers',
    name="Periode Tren A",
    line=dict(color='#00B050', width=3, shape='spline'),
    marker=dict(size=8, color='#00B050'),
    text=labels_raw_a,
    hovertemplate="<b>Periode A (%{text}):</b><br>RJP: %{y:.4f} Janjang/Pokok<extra></extra>"
))

# Trace Garis Periode B (Garis Biru #28348A)
fig_overlay.add_trace(go.Scatter(
    x=x_axis_combined_labels[:len(df_tren_b)], y=df_tren_b["RJP_AKTUAL"],
    mode='lines+markers',
    name="Periode Tren B",
    line=dict(color='#28348A', width=3, shape='spline'),
    marker=dict(size=8, color='#28348A', symbol='square'),
    text=labels_raw_b,
    hovertemplate="<b>Periode B (%{text}):</b><br>RJP: %{y:.4f} Janjang/Pokok<extra></extra>"
))

fig_overlay.update_layout(
    xaxis=dict(
        type='category', 
        categoryorder='array', 
        categoryarray=x_axis_combined_labels,
        tickangle=-45  # REVISI KRITIKAL: Memutar label secara diagonal -45 derajat agar tidak tumpang tindih
    ),
    yaxis=dict(title=dict(text="RJP (Janjang/Pokok)", font=dict(color="#28348A")), tickfont=dict(color="#28348A")),
    hovermode="x unified",
    legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
    margin=dict(l=40, r=40, t=20, b=80), # Memberikan ruang bawah yang cukup untuk teks miring
    height=450
)
st.plotly_chart(fig_overlay, use_container_width=True)

# --- 6. URAIAN & ANALISA DIAGNOSTIK KORPORAT ---
st.markdown("---")
col_m1, col_m2 = st.columns([1.1, 1])

# Ekstraksi Parameter Statistik untuk Periode A
y_a = df_tren_a['RJP_AKTUAL'].values
avg_a = np.mean(y_a)
slope_a, _, _, _, _ = stats.linregress(np.arange(len(y_a)), y_a) if len(y_a) > 1 else (0.0, 0, 0, 0, 0)
status_a = "📈 Uptrend" if slope_a >= 0 else "📉 Downtrend"

# Ekstraksi Parameter Statistik untuk Periode B
y_b = df_tren_b['RJP_AKTUAL'].values
avg_b = np.mean(y_b)
slope_b, _, _, _, _ = stats.linregress(np.arange(len(y_b)), y_b) if len(y_b) > 1 else (0.0, 0, 0, 0, 0)
status_b = "📈 Uptrend" if slope_b >= 0 else "📉 Downtrend"

delta_avg = avg_b - avg_a
pct_change = (delta_avg / avg_a * 100) if avg_a > 0 else 0.0

with col_m1:
    st.markdown("##### 📝 Uraian Analisa Komparasi Lini Masa Berpasangan")
    st.markdown(f"Karakteristik komparatif runtun waktu Kebun **{pilihan_kebun}**:")
    
    st.markdown(f"""
    * **Rata-rata RJP Kualitatif Periode A:** `{avg_a:.4f}` janjang/pokok/bulan.
    * **Rata-rata RJP Kualitatif Periode B:** `{avg_b:.4f}` janjang/pokok/bulan.
    * **Penyimpangan Rata-rata Kumulatif:** `{delta_avg:+.4f}` janjang/pokok/bulan (**{pct_change:+.1f}%**).
    * **Laju Pertumbuhan Jangka Panjang A:** Berstatus **{status_a}** (`{slope_a:+.5f}`/bln).
    * **Laju Pertumbuhan Jangka Panjang B:** Berstatus **{status_b}** (`{slope_b:+.5f}`/bln).
    """)

with col_m2:
    st.markdown("##### 📌 Kesimpulan & Strategi Operasional")
    
    if delta_avg > 0:
        insight_text = (
            f"Strategi operasional membuktikan bahwa performa pembuahan pada Periode B jauh lebih unggul dan produktif "
            f"sebesar {abs(pct_change):.1f}% dibandingkan sejarah masa lalu (Periode A). Pola akselerasi ini mencerminkan "
            "adanya perbaikan kualitas manajemen hara, efektivitas sistem pemupukan jendela dinamis, maupun "
            "kondisi tanaman yang telah memasuki puncak kematangan umur komersial."
        )
        opsi_text = (
            "Pertahankan tata kelola panen bersih yang diterapkan pada Periode B. Catat parameter operasional terbaik "
            "pada periode ini sebagai standar acuan minimum baku (*baseline core target*) di seluruh kebun grup PT BKB & PT FFD."
        )
    else:
        insight_text = (
            f"Manajemen harus waspada karena produktivitas kumulatif pada Periode B mengalami defisit atau pelemahan sebesar "
            f"{abs(pct_change):.1f}% jika dihadapkan pada tolok ukur historis Periode A. Kondisi ini mengindikasikan adanya "
            "gejala penurunan energi vegetatif jangka panjang, hambatan serapan pupuk makro, atau dampak sisa dari pergeseran iklim kering."
        )
        opsi_text = (
            "Rencanakan audit agronomi total pada blok-blok rawan: cek ketepatan waktu aplikasi pupuk hara esensial, "
            "evaluasi kebersihan piringan dari gangguan gulma liar, dan periksa sebaran umur vegetatif untuk memetakan jadwal replanting."
        )

    st.markdown(f"""
    * **Insight Utama:** {insight_text}
    * **Opsi Peningkatan:** {opsi_text}
    """)