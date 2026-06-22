import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import plotly.express as px
import os
from scipy import stats

st.markdown("# 🔬 Analisa Korelasi Historis Curah Hujan vs RJP")
st.markdown("---")

# --- 1. LOAD DATA ---
def load_clean_csv(file):
    df = pd.read_csv(file, sep=";", decimal=",", engine="python")
    df.columns = df.columns.str.strip().str.upper()
    return df

if not os.path.exists("Trend_produksi_satui.csv") or not os.path.exists("Rkp_ch_hh.csv"):
    st.error("⚠️ File data tidak ditemukan!")
    st.stop()

df_prod = load_clean_csv("Trend_produksi_satui.csv")
df_ch = load_clean_csv("Rkp_ch_hh.csv")
URUTAN_BULAN_STD = ['JAN', 'FEB', 'MAR', 'APR', 'MEI', 'JUN', 'JUL', 'AGT', 'SEP', 'OKT', 'NOV', 'DES']
MAPPING_KAPITAL = {'JAN': 'Jan', 'FEB': 'Feb', 'MAR': 'Mar', 'APR': 'Apr', 'MEI': 'Mei', 'JUN': 'Jun', 'JUL': 'Jul', 'AGT': 'Agt', 'SEP': 'Sep', 'OKT': 'Okt', 'NOV': 'Nov', 'DES': 'Des'}

# --- 2. FILTER KEBUN & LAG ---
list_kebun = sorted(list(df_prod['KEBUN'].unique()))
col_f1, col_f2 = st.columns([1, 2])
with col_f1: pilihan_kebun = st.selectbox("📍 Pilih Kebun:", list_kebun)
with col_f2: pilihan_lag = st.slider("⏱️ Lag Bulan Sebelum Panen:", 0, 48, 12)

# --- 3. PROSES DATA ---
df_prod['BULAN_IDX'] = df_prod['BULAN'].apply(lambda x: URUTAN_BULAN_STD.index(str(x).strip().upper()) if str(x).strip().upper() in URUTAN_BULAN_STD else 99)
df_prod['RJP'] = df_prod['AKT_JJG'] / df_prod['POKOK']
df_prod_map = df_prod[(df_prod['KEBUN'] == pilihan_kebun) & (df_prod['RJP'] > 0)].copy()

df_ch['BULAN_IDX'] = df_ch['BULAN'].apply(lambda x: URUTAN_BULAN_STD.index(str(x).strip().upper()) if str(x).strip().upper() in URUTAN_BULAN_STD else 99)

list_hasil = []
for _, r in df_prod_map.iterrows():
    tot = (int(r['TAHUN']) * 12 + int(r['BULAN_IDX'])) - pilihan_lag
    match = df_ch[(df_ch['KEBUN'] == pilihan_kebun) & (df_ch['TAHUN'] == tot // 12) & (df_ch['BULAN_IDX'] == tot % 12)]
    val_ch = match['CURAH_HUJAN'].sum() if not match.empty else 0.0
    list_hasil.append({
        'TAHUN': int(r['TAHUN']), 'TAHUN_YY': str(int(r['TAHUN']))[2:], 'BULAN': r['BULAN'], 
        'RJP': r['RJP'], 'CH': val_ch, 'ABS': int(r['TAHUN'])*12 + int(r['BULAN_IDX']),
        'CH_BULAN': MAPPING_KAPITAL.get(URUTAN_BULAN_STD[tot % 12] if not match.empty else '-', '-')
    })
df_master = pd.DataFrame(list_hasil).sort_values('ABS').reset_index(drop=True)

# --- 4. RENTANG WAKTU ---
col_t1, col_t2, col_t3, col_t4 = st.columns(4)
y_list = sorted(df_master['TAHUN'].unique())
m_list = ['Jan', 'Feb', 'Mar', 'Apr', 'Mei', 'Jun', 'Jul', 'Agt', 'Sep', 'Okt', 'Nov', 'Des']
with col_t1: b_awal = st.selectbox("🗓️ Awal Bulan:", m_list, index=0)
with col_t2: t_awal = st.selectbox("🗓️ Tahun Awal:", y_list, index=0)
with col_t3: b_akhir = st.selectbox("🗓️ Akhir Bulan:", m_list, index=len(m_list)-1)
with col_t4: t_akhir = st.selectbox("🗓️ Akhir Tahun:", y_list, index=len(y_list)-1)
df_ana = df_master[(df_master['ABS'] >= t_awal*12+m_list.index(b_awal)) & (df_master['ABS'] <= t_akhir*12+m_list.index(b_akhir))].copy()

# --- 5. GRAFIK & ANALISA (Otomatisasi Spearman/Pearson) ---
skew_rjp = df_ana['RJP'].skew()
has_outlier = (np.abs(stats.zscore(df_ana['RJP'])) > 3).any()
is_spearman = abs(skew_rjp) > 1 or has_outlier
method_name = "Spearman" if is_spearman else "Pearson"

st.markdown(f"##### 📈 Pengaruh Curah Hujan (mm) (Lag {pilihan_lag} Bulan) vs RJP")
x_labels = [f"<span style='color:#28348A; font-weight:bold;'>{MAPPING_KAPITAL.get(str(r['BULAN']).strip().upper(), r['BULAN'])}-{r['TAHUN_YY']}</span><br><span style='color:#00B050; font-size:10px; font-weight:bold;'>{r['CH_BULAN']}-{str(int(r['TAHUN'])-1)[2:]}</span>" for _, r in df_ana.iterrows()]

fig = go.Figure()
fig.add_trace(go.Scatter(x=x_labels, y=df_ana['RJP'], name="RJP", line=dict(color='#28348A', width=3, shape='spline')))
fig.add_trace(go.Scatter(x=x_labels, y=df_ana['CH'], name="CH", yaxis="y2", line=dict(color='#00B050', width=2.5, shape='spline', dash='dash'), marker=dict(symbol='square')))
fig.update_layout(xaxis=dict(tickangle=0), yaxis=dict(title=dict(text="RJP (Jjg/Pkk)", font=dict(color="#28348A")), tickfont=dict(color="#28348A")), 
                  yaxis2=dict(title=dict(text="CH (mm)", font=dict(color="#00B050")), tickfont=dict(color="#00B050"), overlaying="y", side="right"),
                  hovermode="x unified", height=450, margin=dict(b=100))
st.plotly_chart(fig, use_container_width=True)

slope, intercept, r_val, _, _ = stats.linregress(df_ana['CH'], df_ana['RJP'])
col_scat, col_narasi = st.columns([1.5, 1])
with col_scat:
    fig_scat = go.Figure()
    fig_scat.add_trace(go.Scatter(x=df_ana['CH'], y=df_ana['RJP'], mode='markers', name='Data', marker=dict(size=10, color='#28348A')))
    fig_scat.add_trace(go.Scatter(x=df_ana['CH'], y=intercept + slope*df_ana['CH'], mode='lines', name='Trend', line=dict(color='#C62828', width=2)))
    fig_scat.update_layout(title=f"Scatter Plot (Lag {pilihan_lag} Bln)", xaxis_title="Curah Hujan (mm)", yaxis_title="RJP", height=350)
    st.plotly_chart(fig_scat, use_container_width=True)

with col_narasi:
    st.markdown("##### 📝 Interpretasi Korelasi")
    corr, _ = stats.spearmanr(df_ana['CH'], df_ana['RJP']) if is_spearman else stats.pearsonr(df_ana['CH'], df_ana['RJP'])
    fase_label = "Anthesis (6 bulan)" if pilihan_lag == 6 else (f"Aborsi Bunga ({pilihan_lag} bulan)" if 10 <= pilihan_lag <= 15 else (f"Diferensiasi ({pilihan_lag} bulan)" if 16 <= pilihan_lag <= 24 else f"Primordia ({pilihan_lag} bulan)"))
    st.markdown(f"* **Persamaan:** $y = {intercept:.4f} {'+' if slope > 0 else '-'} {abs(slope):.5f}x$")
    st.markdown(f"* **Koefisien Determinasi ($r^2$):** {r_val**2:.4f}")
    st.markdown(f"* **Koefisien Korelasi ({method_name}):** {round(corr, 3)}")
    st.markdown(f"* **Analisis:** Setiap penambahan 1 mm curah hujan pada {fase_label} menyebabkan **{'peningkatan' if slope > 0 else 'penurunan'}** RJP sebesar **{abs(slope):.5f}** janjang/pokok.")

# --- 6. DETEKSI OTOMATIS ---
st.markdown("##### 🔍 Deteksi Lag Korelasi Terbaik per Fase")
fases = {"Anthesis (6 bln)": range(6, 7), "Aborsi Bunga (10-15 bln)": range(10, 16), "Diferensiasi (16-24 bln)": range(16, 25), "Primordia (25-40 bln)": range(25, 41)}
res = []
for f, lag_rng in fases.items():
    bc, bl = 0, 0
    for lag in lag_rng:
        t = df_ana.copy()
        t['CH_LAG'] = [df_ch[(df_ch['KEBUN']==pilihan_kebun) & (df_ch['TAHUN'] == (r['ABS']-lag)//12) & (df_ch['BULAN_IDX'] == (r['ABS']-lag)%12)]['CURAH_HUJAN'].sum() for _, r in t.iterrows()]
        t = t[t['CH_LAG'] > 0]
        if len(t) > 5:
            c, _ = stats.spearmanr(t['CH_LAG'], t['RJP']) if is_spearman else stats.pearsonr(t['CH_LAG'], t['RJP'])
            if abs(c) > abs(bc): bc, bl = c, lag
    res.append({"Fase (Rentang Bulan)": f, "Best Lag (Bln)": bl, f"Korelasi ({method_name})": round(bc, 3)})
st.table(pd.DataFrame(res))

# --- 7. VALIDASI DISTRIBUSI DATA ---
st.markdown("### 📊 Validasi Distribusi Data")
c1, c2 = st.columns(2)
with c1: st.plotly_chart(px.histogram(df_ana, x="RJP", title=f"Distribusi RJP (Metode: {method_name})", marginal="box"), use_container_width=True)
with c2: st.plotly_chart(px.histogram(df_ana, x="CH", title="Distribusi Curah Hujan", marginal="box", color_discrete_sequence=['green']), use_container_width=True)
st.info(f"**Kesimpulan:** Data {'tidak normal (Skewed/Outlier)' if is_spearman else 'Normal'}. Metode yang digunakan: **{method_name}**.")