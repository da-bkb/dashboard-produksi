import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import os
from scipy import stats

# --- 1. SETTING DEFAULT & LOAD DATA ---
st.markdown("# 🔬 Analisa Korelasi Historis Curah Hujan vs RJP (Janjang/Pokok)")
st.markdown("---")

FILE_PRODUKSI = "Trend_produksi_satui.csv"
FILE_IKLIM = "Rkp_ch_hh.csv"

if not os.path.exists(FILE_PRODUKSI) or not os.path.exists(FILE_IKLIM):
    st.error("⚠️ File 'Trend_produksi_satui.csv' atau 'Rkp_ch_hh.csv' tidak ditemukan di direktori!")
    st.stop()

# Load Data Produksi Multi-Tahun
df_prod = pd.read_csv(FILE_PRODUKSI, sep=";", decimal=",", engine="python")
df_prod.columns = df_prod.columns.str.strip().str.upper()
df_prod['BULAN'] = df_prod['BULAN'].astype(str).str.strip().str.upper()
df_prod['KEBUN'] = df_prod['KEBUN'].astype(str).str.strip().str.upper()

# Load Data Iklim Historis
df_ch = pd.read_csv(FILE_IKLIM, sep=";", decimal=",", engine="python")
df_ch.columns = df_ch.columns.str.strip().str.upper()
df_ch['BULAN'] = df_ch['BULAN'].astype(str).str.strip().str.upper()
df_ch['KEBUN'] = df_ch['KEBUN'].astype(str).str.strip().str.upper()

# --- 2. FILTER UTAMA KEBUN & LAG BULAN ---
list_kebun = sorted(list(df_prod['KEBUN'].unique()))
URUTAN_BULAN_STD = ['JAN', 'FEB', 'MAR', 'APR', 'MEI', 'JUN', 'JUL', 'AGT', 'SEP', 'OKT', 'NOV', 'DES']
MAPPING_KAPITAL_BARU = {
    'JAN': 'Jan', 'FEB': 'Feb', 'MAR': 'Mar', 'APR': 'Apr', 'MEI': 'Mei', 'JUN': 'Jun',
    'JUL': 'Jul', 'AGT': 'Agt', 'SEP': 'Sep', 'OKT': 'Okt', 'NOV': 'Nov', 'DES': 'Des'
}

col_f1, col_f2 = st.columns([1.1, 1.9])
with col_f1:
    pilihan_kebun = st.selectbox("📍 Pilih Kebun:", list_kebun, key="exec_ch_kebun_picker")
with col_f2:
    pilihan_lag = st.slider("⏱️ Lag Bulan Sebelum Panen:", min_value=0, max_value=48, value=12, step=1)
    
    # Panduan Fase Fisiologis Kelapa Sawit (Warna Biru #28348A)
    st.markdown("""
    <div style='color: #28348A; font-size: 12.5px; font-weight: bold; line-height: 1.4; margin-top: -5px; margin-bottom: 10px;'>
    ℹ️ Panduan Fase Fisiologis Tandan Sawit:<br>
    • Fase Anthesis (6 bulan)<br>
    • Fase Aborsi Bunga (10-15 bulan)<br>
    • Fase Diferensiasi Jantan-Betina (16-24 bulan)<br>
    • Fase Primordia/ Pembentukan Bakal Bunga (25-40 bulan)
    </div>
    """, unsafe_allow_html=True)

# --- 3. PROSES KONSOLIDASI DATA BERBASIS KALENDER RIIL ---
df_prod_filtered = df_prod[df_prod['KEBUN'] == pilihan_kebun].copy()
df_prod_filtered['BULAN_IDX'] = df_prod_filtered['BULAN'].apply(lambda x: URUTAN_BULAN_STD.index(x) if x in URUTAN_BULAN_STD else 99)
df_prod_filtered = df_prod_filtered[df_prod_filtered['BULAN_IDX'] != 99]

# Hitung RJP bulanan aktual
df_prod_filtered['RJP_AKTUAL'] = df_prod_filtered['AKT_JJG'] / df_prod_filtered['POKOK']
df_prod_map = df_prod_filtered[df_prod_filtered['RJP_AKTUAL'] > 0].reset_index(drop=True)

df_ch_filtered = df_ch[df_ch['KEBUN'] == pilihan_kebun].copy()
df_ch_filtered['BULAN_IDX'] = df_ch_filtered['BULAN'].apply(lambda x: URUTAN_BULAN_STD.index(x) if x in URUTAN_BULAN_STD else 99)

list_hasil_rekonstruksi = []
for idx, r_prod in df_prod_map.iterrows():
    bln_idx_prod = int(r_prod['BULAN_IDX'])
    tahun_prod = int(r_prod['TAHUN'])
    
    total_bulan_target = (tahun_prod * 12 + bln_idx_prod) - pilihan_lag
    tahun_ch_target = total_bulan_target // 12
    bln_idx_ch_target = total_bulan_target % 12
    
    match_ch = df_ch_filtered[(df_ch_filtered['TAHUN'] == tahun_ch_target) & (df_ch_filtered['BULAN_IDX'] == bln_idx_ch_target)]
    val_curah_hujan = match_ch['CURAH_HUJAN'].sum() if not match_ch.empty else 0.0
    
    list_hasil_rekonstruksi.append({
        'TAHUN_PROD': tahun_prod,
        'TAHUN_PROD_YY': str(tahun_prod)[2:],
        'BULAN_IDX_PROD': bln_idx_prod,
        'BULAN_PROD': r_prod['BULAN'],
        'RJP_AKTUAL': r_prod['RJP_AKTUAL'],
        'NAMA_BULAN_CH': URUTAN_BULAN_STD[bln_idx_ch_target],
        'TAHUN_CH_YY': str(tahun_ch_target)[2:],
        'CURAH_HUJAN': val_curah_hujan,
        'URUTAN_ABS': tahun_prod * 12 + bln_idx_prod
    })

df_master = pd.DataFrame(list_hasil_rekonstruksi).sort_values('URUTAN_ABS').reset_index(drop=True)

if df_master.empty:
    st.warning("⚠️ Tidak ada data.")
    st.stop()

# --- 4. SELEKTOR RENTANG WAKTU TERPISAH MURNI ---
col_t1, col_t2, col_t3, col_t4 = st.columns(4)
list_tahun_tersedia = sorted(list(df_master['TAHUN_PROD'].unique()))
list_bulan_tampil = ['Jan', 'Feb', 'Mar', 'Apr', 'Mei', 'Jun', 'Jul', 'Agt', 'Sep', 'Okt', 'Nov', 'Des']

with col_t1:
    pilihan_bln_awal = st.selectbox("🗓️ Bulan Awal:", list_bulan_tampil, index=0, key="ch_start_month")
with col_t2:
    pilihan_thn_awal = st.selectbox("🗓️ Tahun Awal:", list_tahun_tersedia, index=0, key="ch_start_year")

with col_t3:
    pilihan_bln_akhir = st.selectbox("🗓️ Bulan Akhir:", list_bulan_tampil, index=len(list_bulan_tampil)-1, key="ch_end_month")
with col_t4:
    pilihan_thn_akhir = st.selectbox("🗓️ Tahun Akhir:", list_tahun_tersedia, index=len(list_tahun_tersedia)-1, key="ch_end_year")

val_abs_awal = pilihan_thn_awal * 12 + list_bulan_tampil.index(pilihan_bln_awal)
val_abs_akhir = pilihan_thn_akhir * 12 + list_bulan_tampil.index(pilihan_bln_akhir)

if val_abs_awal > val_abs_akhir:
    st.error("❌ Eror: Periode Awal tidak boleh lebih besar dari Periode Akhir!")
    st.stop()

df_analisa = df_master[(df_master['URUTAN_ABS'] >= val_abs_awal) & (df_master['URUTAN_ABS'] <= val_abs_akhir)].copy().reset_index(drop=True)

if df_analisa.empty:
    st.warning("⚠️ Tidak ada data pada rentang waktu terpilih.")
    st.stop()

# --- 5. GRAFIK OVERLAY TREN HISTORIS SEJAJAR ---
st.markdown(f"##### 📈 Pengaruh Curah Hujan (mm) (Lag {pilihan_lag} Bulan) vs RJP")

fig_overlay = go.Figure()

# REVISI WARNA: Menyelaraskan teks aktual panen menjadi Biru (#28348A) mengikuti warna tema sumbu
x_labels_multiline = [
    f"<span style='color:#28348A; font-weight:bold;'>{MAPPING_KAPITAL_BARU.get(r['BULAN_PROD'], r['BULAN_PROD'])}-{r['TAHUN_PROD_YY']}</span><br>"
    f"<span style='color:#00B050; font-size:11px; font-weight:bold;'>{MAPPING_KAPITAL_BARU.get(r['NAMA_BULAN_CH'], r['NAMA_BULAN_CH'])}-{r['TAHUN_CH_YY']}</span>" 
    for idx, r in df_analisa.iterrows()
]

# Sumbu Kiri: RJP (Biru #28348A)
fig_overlay.add_trace(go.Scatter(x=x_labels_multiline, y=df_analisa["RJP_AKTUAL"], mode='lines+markers', name="RJP (Jjg/Pkk)", line=dict(color='#28348A', width=3, shape='spline'), marker=dict(size=8, color='#28348A')))
# Sumbu Kanan: Curah Hujan (Hijau #00B050)
fig_overlay.add_trace(go.Scatter(x=x_labels_multiline, y=df_analisa["CURAH_HUJAN"], mode='lines+markers', name="Curah Hujan (mm)", line=dict(color='#00B050', width=2.5, shape='spline', dash='dash'), marker=dict(size=7, color='#00B050', symbol='square'), yaxis="y2"))

axis_title_html = "Hubungan <span style='color:#28348A; font-weight:bold;'>Bulan Panen</span> dan <span style='color:#00B050; font-weight:bold;'>Bulan Historis Hujan</span>"

fig_overlay.update_layout(
    xaxis=dict(title=dict(text=axis_title_html), type='category', categoryorder='array', categoryarray=x_labels_multiline),
    yaxis=dict(title=dict(text="RJP (Janjang/Pokok)", font=dict(color="#28348A")), tickfont=dict(color="#28348A")),
    yaxis2=dict(title=dict(text="Curah Hujan (mm)", font=dict(color="#00B050")), tickfont=dict(color="#00B050"), overlaying="y", side="right"),
    hovermode="x unified", legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1), margin=dict(l=40, r=40, t=30, b=50), height=420
)
st.plotly_chart(fig_overlay, use_container_width=True)

# --- 6. VISUALISASI SCATTER PLOT & REGRESI DINAMIS ---
st.markdown("---")
col_graph, col_narasi = st.columns([1.3, 1])
x_data = df_analisa['CURAH_HUJAN'].values
y_data = df_analisa['RJP_AKTUAL'].values

if len(x_data) > 1:
    b_slope, a_intercept, r_value, p_value, std_err = stats.linregress(x_data, y_data)
    r_squared = r_value ** 2
    x_line = np.linspace(x_data.min(), x_data.max(), 100)
    y_line = a_intercept + b_slope * x_line
else:
    b_slope, a_intercept, r_squared = 0.0, 0.0, 0.0
    x_line, y_line = np.array([0, 1]), np.array([0, 1])

with col_graph:
    # REVISI HURUF: Mengecilkan font judul komponen scatter plot menggunakan heading level 5 (#####)
    st.markdown(f"##### 📊 Scatter Plot & Trend RJP (Lag {pilihan_lag} Bulan)")
    fig_scatter = go.Figure()
    fig_scatter.add_trace(go.Scatter(x=x_data, y=y_data, mode='markers', marker=dict(size=12, color='#28348A', opacity=0.8, line=dict(width=1, color='White')), text=df_analisa['BULAN_PROD'], hovertemplate="<b>Siklus Panen: %{text}</b><br>Curah Hujan: %{x:.1f} mm<br>RJP: %{y:.4f} Jg/Pkk<extra></extra>"))
    if len(x_data) > 1:
        fig_scatter.add_trace(go.Scatter(x=x_line, y=y_line, mode='lines', line=dict(color='#C62828', width=2)))
    fig_scatter.update_layout(xaxis=dict(title=dict(text="Curah Hujan (mm) - Lag " + str(pilihan_lag) + " Bulan")), yaxis=dict(title=dict(text="RJP (Janjang/Pokok)")), margin=dict(l=20, r=20, t=20, b=20), height=350, showlegend=False)
    st.plotly_chart(fig_scatter, use_container_width=True)

with col_narasi:
    # REVISI HURUF: Mengecilkan font judul komponen uraian menggunakan heading level 5 (#####)
    st.markdown("##### 📝 Uraian & Analisa Korelasi Pearson")
    st.markdown(f"Hasil Pemodelan Statistik Aktual Kebun {pilihan_kebun} :")
    tanda_b = "+" if b_slope >= 0 else "-"
    st.info(f"**Persamaan Regresi RJP:**\n$$y = {a_intercept:.3f} {tanda_b} {abs(b_slope):.3f}x$$")
    
    if r_squared >= 0.70:
        kekuatan = "Kuat"
    elif r_squared >= 0.40:
        kekuatan = "Moderat"
    else:
        kekuatan = "Lemah"
        
    arah_hubungan = "Positif" if b_slope >= 0 else "Negatif"
    efek_aksi = "peningkatan" if b_slope >= 0 else "penurunan"

    if pilihan_lag == 6:
        nama_fase = "Fase Anthesis (6 bulan)"
        insight_utama = (
            "Pada Fase Anthesis (bunga mekar berjalan), air berfungsi vital menjaga kesuburan tepung sari. "
            f"Model regresi {arah_hubungan} {kekuatan} ini membuktikan tingkat keberhasilan penyerbukan buah kelapa sawit. "
            "Jika b bernilai positif, tambahan air hujan mendukung optimalnya proses fertilisasi kelapa sawit. "
            "Namun apabila koefisien b bernilai negatif, intensitas hujan ekstrem (*over-wetting*) justru merusak viabilitas "
            "serbuk sari dan menghambat mobilitas terbang kumbang penyerbuk Elaeidobius kamerunicus, memicu buah partenokarpi (kempes)."
        )
        opsi_perbaikan = (
            "Apabila korelasi berbalik negatif akibat curah hujan berlebih, lakukan manajemen sanitasi piringan secara ketat "
            "untuk mengurangi kelembaban mikro ekstrem, serta rencanakan aplikasi hatching-box kumbang penyerbuk tambahan di lapangan."
        )
    elif 10 <= pilihan_lag <= 15:
        nama_fase = f"Fase Aborsi Bunga ({pilihan_lag} bulan)"
        insight_utama = (
            "Rentang waktu ini mencerminkan tingkat kerentanan bakal buah sawit terhadap gugur premature akibat cekaman lingkungan. "
            f"Korelasi {arah_hubungan} {kekuatan} mencerminkan ketersediaan kadar air tanah makro. Jika koefisien b bernilai positif, "
            "tambahan hujan menekan pelepasan senyawa etilen pohon sehingga aborsi berkurang. Jika b bernilai negatif, akumulasi hujan "
            "ekstrem memicu kondisi jenuh air (*waterlogging*) pada perakaran sawit yang menghentikan respirasi akar napas."
        )
        opsi_perbaikan = (
            "Jika korelasi positif dominan (artinya blok kekurangan air), prioritaskan pembuatan rorak penampung air hujan dan "
            "aplikasi mulsa pelepah kelapa sawit. Jika korelasi negatif dominan (kelebihan air), lakukan cuci parit cacing blok sesegera mungkin."
        )
    elif 16 <= pilihan_lag <= 24:
        nama_fase = f"Fase Diferensiasi Jantan-Betina ({pilihan_lag} bulan)"
        insight_utama = (
            "Ini adalah jendela paling kritis yang menentukan rasio jenis kelamin tunas bunga (*Sex Ratio*). "
            f"Korelasi {arah_hubungan} {kekuatan} memotret stabilitas pasokan energi tanaman. Jika b bernilai positif, pasokan "
            "air yang memadai mendorong pembentukan hormon giberelin untuk melahirkan bunga betina penghasil janjang. Jika b bernilai "
            "negatif, kelebihan air atau defisit matahari akibat awan tebal mengganggu fotosintesis pelepah, memicu pohon sawit "
            "memproduksi mayoritas bunga jantan yang mandul."
        )
        opsi_perbaikan = (
            "Pertahankan tinggi muka air tanah (*water-table*) di level aman 50-60 cm pada area rendahan. Serta perkuat aplikasi "
            "pupuk unsur hara Kalium dan Boron dosis tepat sebelum memasuki rentang bulan diferensiasi kritis ini."
        )
    elif 25 <= pilihan_lag <= 40:
        nama_fase = f"Fase Primordia / Pembentukan Bakal Bunga ({pilihan_lag} bulan)"
        insight_utama = (
            "Tahap paling awal inisiasi sel atau pembentukan jaringan primordia bakal bunga di ketiak pelepah bagian dalam. "
            f"Korelasi {arah_hubungan} {kekuatan} mencerminkan kecukupan asupan energi vegetatif jangka panjang. Nilai koefisien b "
            "menunjukkan seberapa sensitif sel primordial merespon kelembaban tanah; hubungan positif menandakan kesiapan "
            "tanaman memulai siklus generatif awal, sedangkan hubungan negatif menunjukkan cekaman berkepanjangan pada titik tumbuh."
        )
        opsi_perbaikan = (
            "Lakukan pemetaan zonasi wilayah rawan cekaman air jangka panjang, dan integrasikan jadwal pemupukan makro (N, P, K) "
            "tepat di bulan-bulan basah agar penyerapan hara di fase primordia tumbuh optimal."
        )
    else:
        nama_fase = f"Luar Jendela Kritis ({pilihan_lag} bulan)"
        insight_utama = f"Rentang waktu {pilihan_lag} bulan berada di luar batas jendela kritis metabolisme generatif kelapa sawit."
        opsi_perbaikan = "Eksplorasi slider kontrol lag bulan ke angka rentang fase kritis (6, 10-15, 16-24, atau 25-40 bulan) untuk memunculkan analisa operasional agronomi yang valid."

    st.markdown(f"""
    * **Kekuatan Hubungan Kunci ($R^2$):** `{r_squared:.4f}` (**{r_squared*100:.1f}%** akurasi model iklim terhadap RJP).
    * **Analisa Arah:**
      1. Hubungan bersifat **{arah_hubungan} {kekuatan}**.
      2. Pada cakupan **{nama_fase}**, setiap penambahan 1 mm curah hujan mempengaruhi **{efek_aksi}** RJP sebesar `{abs(b_slope):.5f}` janjang/pokok pada bulan berjalan.
    """)
    
    st.markdown("##### 📌 Kesimpulan:")
    st.markdown(f"""
    * **Insight Utama:** {insight_utama}
    * **Opsi Peningkatan / Perbaikan:** {opsi_perbaikan}
    """)