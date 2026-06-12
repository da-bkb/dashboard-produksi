import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects go
import os
from scipy import stats

# --- 1. SETTING DEFAULT & LOAD DATA ---
st.markdown("# 🔬 Analisa Korelasi Historis Pemupukan NPK 13 vs BJR (Kg/Jjg)")
st.markdown("---")

FILE_PRODUKSI = "Trend_produksi_satui.csv"
FILE_PUPUK = "Rkp_Umr_Ppk.csv"

if not os.path.exists(FILE_PRODUKSI) or not os.path.exists(FILE_PUPUK):
    st.error("⚠️ File data tidak lengkap!")
    st.stop()

# Load Data Produksi Multi-Tahun
df_prod = pd.read_csv(FILE_PRODUKSI, sep=";", decimal=",", engine="python")
df_prod.columns = df_prod.columns.str.strip().str.upper()
df_prod['BULAN'] = df_prod['BULAN'].astype(str).str.strip().str.upper()
df_prod['KEBUN'] = df_prod['KEBUN'].astype(str).str.strip().str.upper()

# Load Data Pupuk Historis
df_ppk = pd.read_csv(FILE_PUPUK, sep=";", decimal=",", engine="python")
df_ppk.columns = df_ppk.columns.str.strip().str.upper()
df_ppk['BULAN'] = df_ppk['BULAN'].astype(str).str.strip().str.upper()
df_ppk['KEBUN'] = df_ppk['KEBUN'].astype(str).str.strip().str.upper()

# --- 2. FILTER UTAMA KEBUN & LAG ---
list_kebun = sorted(list(df_prod['KEBUN'].unique()))
URUTAN_BULAN_STD = ['JAN', 'FEB', 'MAR', 'APR', 'MEI', 'JUN', 'JUL', 'AGT', 'SEP', 'OKT', 'NOV', 'DES']
MAPPING_KAPITAL_BARU = {
    'JAN': 'Jan', 'FEB': 'Feb', 'MAR': 'Mar', 'APR': 'Apr', 'MEI': 'Mei', 'JUN': 'Jun',
    'JUL': 'Jul', 'AGT': 'Agt', 'SEP': 'Sep', 'OKT': 'Okt', 'NOV': 'Nov', 'DES': 'Des'
}

col_f1, col_f2 = st.columns([1.1, 1.9])
with col_f1:
    pilihan_kebun = st.selectbox("📍 Pilih Kebun:", list_kebun, key="exec_bjr_kebun_picker")
with col_f2:
    pilihan_lag = st.slider("⏱️ Lag Bulan Ke Belakang:", min_value=1, max_value=6, value=4, step=1)

# --- 3. PROSES KONSOLIDASI JENDELA DINAMIS ---
df_prod_filtered = df_prod[df_prod['KEBUN'] == pilihan_kebun].copy()
df_prod_filtered['BULAN_IDX'] = df_prod_filtered['BULAN'].apply(lambda x: URUTAN_BULAN_STD.index(x) if x in URUTAN_BULAN_STD else 99)
df_prod_filtered = df_prod_filtered[df_prod_filtered['BULAN_IDX'] != 99]
df_prod_map = df_prod_filtered[df_prod_filtered['BJR_AKT'] > 0].reset_index(drop=True)

df_ppk_filtered = df_ppk[df_ppk['KEBUN'] == pilihan_kebun].copy()
df_ppk_filtered['BULAN_IDX'] = df_ppk_filtered['BULAN'].apply(lambda x: URUTAN_BULAN_STD.index(x) if x in URUTAN_BULAN_STD else 99)

list_hasil_rekonstruksi = []
for idx, r_prod in df_prod_map.iterrows():
    bln_idx_prod = int(r_prod['BULAN_IDX'])
    tahun_prod = int(r_prod['TAHUN'])
    
    total_bulan_prod_absolut = tahun_prod * 12 + bln_idx_prod
    total_bulan_awal_absolut = total_bulan_prod_absolut - pilihan_lag
    total_bulan_akhir_absolut = total_bulan_awal_absolut + 3 if pilihan_lag >= 3 else total_bulan_prod_absolut
    
    total_luas_akumulasi_ha = 0.0
    list_komponen_bulan_label = []
    
    for m_abs in range(total_bulan_awal_absolut, total_bulan_akhir_absolut + 1):
        tahun_pupuk_target = m_abs // 12
        bln_idx_pupuk_target = m_abs % 12
        
        match_row = df_ppk_filtered[(df_ppk_filtered['TAHUN'] == tahun_pupuk_target) & (df_ppk_filtered['BULAN_IDX'] == bln_idx_pupuk_target)]
        if not match_row.empty:
            total_luas_akumulasi_ha += match_row['HSL_KRJ'].sum()
            
        if m_abs == total_bulan_awal_absolut or m_abs == total_bulan_akhir_absolut:
            nama_bln_singkat = MAPPING_KAPITAL_BARU.get(URUTAN_BULAN_STD[bln_idx_pupuk_target], URUTAN_BULAN_STD[bln_idx_pupuk_target])
            list_komponen_bulan_label.append(f"{nama_bln_singkat}-{str(tahun_pupuk_target)[2:]}")
            
    label_rentang_pupuk = f"{list_komponen_bulan_label[0]} s/d {list_komponen_bulan_label[1]}" if len(list_komponen_bulan_label) > 1 and list_komponen_bulan_label[0] != list_komponen_bulan_label[1] else f"{list_komponen_bulan_label[0]}"
    
    list_hasil_rekonstruksi.append({
        'TAHUN_PROD': tahun_prod,
        'TAHUN_PROD_YY': str(tahun_prod)[2:],
        'BULAN_IDX_PROD': bln_idx_prod,
        'BULAN_PROD': r_prod['BULAN'],
        'BJR_AKTUAL': r_prod['BJR_AKT'],
        'LABEL_RENTANG_PUPUK': label_rentang_pupuk,
        'HSL_KRJ': total_luas_akumulasi_ha,
        'URUTAN_ABS': total_bulan_prod_absolut
    })

df_master = pd.DataFrame(list_hasil_rekonstruksi).sort_values('URUTAN_ABS').reset_index(drop=True)

if df_master.empty:
    st.warning("⚠️ Tidak ada data.")
    st.stop()

# --- 4. SELEKTOR RENTANG WAKTU (REVISI: TERPISAH BULAN & TAHUN, TANPA JUDUL) ---
col_t1, col_t2, col_t3, col_t4 = st.columns(4)
list_tahun_tersedia = sorted(list(df_master['TAHUN_PROD'].unique()))
list_bulan_tampil = ['Jan', 'Feb', 'Mar', 'Apr', 'Mei', 'Jun', 'Jul', 'Agt', 'Sep', 'Okt', 'Nov', 'Des']

with col_t1:
    pilihan_bln_awal = st.selectbox("🗓️ Bulan Awal:", list_bulan_tampil, index=0, key="bjr_start_month")
with col_t2:
    pilihan_thn_awal = st.selectbox("🗓️ Tahun Awal:", list_tahun_tersedia, index=0, key="bjr_start_year")

with col_t3:
    pilihan_bln_akhir = st.selectbox("🗓️ Bulan Akhir:", list_bulan_tampil, index=len(list_bulan_tampil)-1, key="bjr_end_month")
with col_t4:
    pilihan_thn_akhir = st.selectbox("🗓️ Tahun Akhir:", list_tahun_tersedia, index=len(list_tahun_tersedia)-1, key="bjr_end_year")

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
st.subheader(f"📈 Pengaruh Realisasi Pemupukan (Ha) (Lag {pilihan_lag} Bulan) vs BJR")
fig_overlay = go.Figure()
x_labels_multiline = [f"{MAPPING_KAPITAL_BARU.get(r['BULAN_PROD'], r['BULAN_PROD'])}-{r['TAHUN_PROD_YY']}<br><span style='color:#00B050; font-size:11px; font-weight:bold;'>Ppk: {r['LABEL_RENTANG_PUPUK']}</span>" for idx, r in df_analisa.iterrows()]

fig_overlay.add_trace(go.Scatter(x=x_labels_multiline, y=df_analisa["BJR_AKTUAL"], mode='lines+markers', name="BJR (Kg/Jjg)", line=dict(color='#28348A', width=3, shape='spline'), marker=dict(size=8, color='#28348A')))
fig_overlay.add_trace(go.Scatter(x=x_labels_multiline, y=df_analisa["HSL_KRJ"], mode='lines+markers', name="Luas Pupuk Accum", line=dict(color='#00B050', width=2.5, shape='spline', dash='dash'), marker=dict(size=7, color='#00B050', symbol='square'), yaxis="y2"))

fig_overlay.update_layout(
    xaxis=dict(title=dict(text="Garis Waktu Hubungan (Baris Atas: Panen Berjalan | Baris Bawah: Jendela Akumulasi Aplikasi Pupuk)"), type='category', categoryorder='array', categoryarray=x_labels_multiline),
    yaxis=dict(title=dict(text="BJR (Kg/Jjg)", font=dict(color="#28348A")), tickfont=dict(color="#28348A")),
    yaxis2=dict(title=dict(text="Luas Aplikasi Pemupukan (Ha/Bulan)", font=dict(color='#00B050')), tickfont=dict(color='#00B050'), overlaying="y", side="right"),
    hovermode="x unified", legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1), margin=dict(l=40, r=40, t=30, b=50), height=420
)
st.plotly_chart(fig_overlay, use_container_width=True)

# --- 6. SCATTER & TREND ---
st.markdown("---")
col_graph, col_narasi = st.columns([1.3, 1])
x_data = df_analisa['HSL_KRJ'].values
y_data = df_analisa['BJR_AKTUAL'].values

if len(x_data) > 1:
    b_slope, a_intercept, r_value, p_value, std_err = stats.linregress(x_data, y_data)
    r_squared = r_value ** 2
    x_line = np.linspace(x_data.min(), x_data.max(), 100)
    y_line = a_intercept + b_slope * x_line
else:
    b_slope, a_intercept, r_squared = 0.0, 0.0, 0.0
    x_line, y_line = np.array([0, 1]), np.array([0, 1])

with col_graph:
    st.subheader(f"📊 Scatter Plot & Trend BJR (Lag {pilihan_lag} Bulan)")
    fig_scatter = go.Figure()
    fig_scatter.add_trace(go.Scatter(x=x_data, y=y_data, mode='markers', marker=dict(size=12, color='#28348A', opacity=0.8, line=dict(width=1, color='White')), text=df_analisa['BULAN_PROD'], hovertemplate="<b>Siklus Panen: %{text}</b><br>Total Luas Pupuk: %{x:.1f} Ha<br>BJR: %{y:.2f} Kg/Jjg<extra></extra>"))
    if len(x_data) > 1:
        fig_scatter.add_trace(go.Scatter(x=x_line, y=y_line, mode='lines', line=dict(color='#C62828', width=2)))
    fig_scatter.update_layout(xaxis=dict(title=dict(text=f"Luas Aplikasi Pupuk (Ha) - Lag {pilihan_lag} Bulan")), yaxis=dict(title=dict(text="BJR (Kg/Janjang)")), margin=dict(l=20, r=20, t=20, b=20), height=350, showlegend=False)
    st.plotly_chart(fig_scatter, use_container_width=True)

with col_narasi:
    st.subheader("📝 Uraian & Analisa Korelasi Pearson")
    st.markdown(f"Hasil Pemodelan Statistik Aktual Kebun {pilihan_kebun} :")
    tanda_b = "+" if b_slope >= 0 else "-"
    st.info(f"**Persamaan Regresi BJR:**\n$$y = {a_intercept:.3f} {tanda_b} {abs(b_slope):.3f}x$$")
    st.markdown(f"* **Kekuatan Hubungan Kunci ($R^2$):** `{r_squared:.4f}` (**{r_squared*100:.1f}%** akurasi model).\n* **Analisa Arah:** Hubungan bersifat {'**Positif (Searah)**' if b_slope >= 0 else '**Negatif (Terbalik)**'}")
    st.markdown("##### 📌 Kesimpulan:")
    if r_squared >= 0.70:
        st.write(f"🌟 Lag `{pilihan_lag} Bulan` terdeteksi sebagai periode kritis *Nutrient Filling Stage* dengan nilai $R^2$ yang sangat kuat (`{r_squared:.2f}`). Aplikasi pupuk dalam jendela waktu pendek ini terbukti vital mengonversi berat janjang sawit agar padat.")
    elif r_squared >= 0.40:
        st.write(f"▼ **Korelasi Moderat:** Lag `{pilihan_lag} Bulan` memengaruhi fluktuasi berat janjang cukup signifikan. Silakan geser slider dari 1-6 bulan untuk menemukan rentang 4-18 bulan terkuat.")
    else:
        st.write(f"ℹ️ **Korelasi Lemah/Anomali:** Lag `{pilihan_lag} Bulan` kurang sensitif menjelaskan variasi berat janjang melalui data luas Ha. Disarankan melihat indikator tonase hara jika tersedia.")