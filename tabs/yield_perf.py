import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go

# Ambil data global dari session state app.py
df_raw = st.session_state["df_raw"]
pilihan_bulan = st.session_state["pilihan_bulan"]

st.markdown(f"### 🌱 Yield Performance terhadap Budget (Ton/Ha)")

# --- 1. PROSES FILTER TIMEFRAME (MTD & YTD) ---
# Data Bulan Ini (MTD)
df_mtd = df_raw[df_raw['Bulan'] == pilihan_bulan].copy()

# Data s.d Bulan Ini (YTD)
URUTAN_BULAN_STD = ['JAN', 'FEB', 'MAR', 'APR', 'MEI', 'JUN', 'JUL', 'AGS', 'SEP', 'OKT', 'NOV', 'DES']
pilihan_bulan_std = "AGS" if pilihan_bulan in ["AGUSTUS", "AGS"] else pilihan_bulan

if pilihan_bulan_std in URUTAN_BULAN_STD:
    idx_bulan = URUTAN_BULAN_STD.index(pilihan_bulan_std)
    bulan_ytd = URUTAN_BULAN_STD[:idx_bulan + 1]
else:
    bulan_ytd = [pilihan_bulan_std]

df_ytd = df_raw[df_raw['Bulan'].isin(bulan_ytd)].copy()

# --- 2. PERHITUNGAN AGREGASI DATA KEBUN ---
# Luas dihitung .first() per kombinasi Kebun-Afdeling agar komulatif YTD tidak melipatgandakan luas lapangan
luas_kebun_mtd = df_mtd.groupby(['Kebun', 'Afdeling'])['Luas'].first().reset_index().groupby('Kebun')['Luas'].sum()
luas_kebun_ytd = df_ytd.groupby(['Kebun', 'Afdeling'])['Luas'].first().reset_index().groupby('Kebun')['Luas'].sum()

# Agregasi Level Kebun - Bulan Ini (MTD)
df_k_mtd = df_mtd.groupby('Kebun').agg({'Kg Akt.': 'sum', 'Kg Bgt.': 'sum'}).reset_index()
df_k_mtd['Luas'] = df_k_mtd['Kebun'].map(luas_kebun_mtd)
df_k_mtd['Aktual'] = df_k_mtd['Kg Akt.'] / df_k_mtd['Luas'] / 1000
df_k_mtd['Target'] = df_k_mtd['Kg Bgt.'] / df_k_mtd['Luas'] / 1000

# Agregasi Level Kebun - s.d Bulan Ini (YTD)
df_k_ytd = df_ytd.groupby('Kebun').agg({'Kg Akt.': 'sum', 'Kg Bgt.': 'sum'}).reset_index()
df_k_ytd['Luas'] = df_k_ytd['Kebun'].map(luas_kebun_ytd)
df_k_ytd['Aktual'] = df_k_ytd['Kg Akt.'] / df_k_ytd['Luas'] / 1000
df_k_ytd['Target'] = df_k_ytd['Kg Bgt.'] / df_k_ytd['Luas'] / 1000

# --- 3. VISUALISASI GRAFIK BERSEBELAHAN (COLUMNS) ---
col_g1, col_g2 = st.columns(2)

with col_g1:
    st.markdown(f"##### 📊 Grafik Yield - Bulan Ini ({pilihan_bulan})")
    fig_mtd = go.Figure()
    fig_mtd.add_trace(go.Bar(x=df_k_mtd["Kebun"], y=df_k_mtd["Aktual"], name="Aktual MTD", marker_color="#28348A", width=0.35))
    fig_mtd.add_trace(go.Scatter(x=[None], y=[None], mode='lines', line=dict(color='#00B050', width=4), name='Budget MTD'))
    
    for idx, row in df_k_mtd.iterrows():
        fig_mtd.add_shape(type="line", x0=idx-0.2, x1=idx+0.2, y0=row["Target"], y1=row["Target"], line=dict(color="#00B050", width=4))
        if row["Aktual"] < row["Target"]:
            fig_mtd.add_annotation(x=idx, y=row["Target"], ax=idx, ay=row["Aktual"], xref="x", yref="y", axref="x", ayref="y", showarrow=True, arrowhead=2, arrowsize=1.2, arrowwidth=2.5, arrowcolor='#FF0000')
    fig_mtd.update_layout(template="plotly_white", yaxis_title="Ton/Ha", margin=dict(l=20, r=20, t=20, b=20), legend=dict(orientation="h", y=1.15))
    st.plotly_chart(fig_mtd, use_container_width=True)

with col_g2:
    st.markdown(f"##### 📊 Grafik Yield - s.d Bulan Ini (YTD {pilihan_bulan})")
    fig_ytd = go.Figure()
    fig_ytd.add_trace(go.Bar(x=df_k_ytd["Kebun"], y=df_k_ytd["Aktual"], name="Aktual YTD", marker_color="#28348A", width=0.35))
    fig_ytd.add_trace(go.Scatter(x=[None], y=[None], mode='lines', line=dict(color='#00B050', width=4), name='Budget YTD'))
    
    for idx, row in df_k_ytd.iterrows():
        fig_ytd.add_shape(type="line", x0=idx-0.2, x1=idx+0.2, y0=row["Target"], y1=row["Target"], line=dict(color="#00B050", width=4))
        if row["Aktual"] < row["Target"]:
            fig_ytd.add_annotation(x=idx, y=row["Target"], ax=idx, ay=row["Aktual"], xref="x", yref="y", axref="x", ayref="y", showarrow=True, arrowhead=2, arrowsize=1.2, arrowwidth=2.5, arrowcolor='#FF0000')
    fig_ytd.update_layout(template="plotly_white", yaxis_title="Ton/Ha", margin=dict(l=20, r=20, t=20, b=20), legend=dict(orientation="h", y=1.15))
    st.plotly_chart(fig_ytd, use_container_width=True)

st.markdown("---")

# --- 4. TABEL DATA SUMMARY KEBUN (YTD) ---
st.markdown(f"##### 📋 Tabel Data Summary Yield s.d Bulan Ini (YTD)")

# Hitung kalkulasi Variance sesuai request Bapak
df_tabel = df_k_ytd[['Kebun', 'Aktual', 'Target']].copy()
df_tabel.columns = ['Kebun', 'Akt (Ton/Ha)', 'Bgt (Ton/Ha)']
df_tabel['Var (Ton/Ha)'] = df_tabel['Akt (Ton/Ha)'] - df_tabel['Bgt (Ton/Ha)']
df_tabel['Var (%)'] = (df_tabel['Var (Ton/Ha)'] / df_tabel['Bgt (Ton/Ha)']) * 100

# Tambahkan baris Total / Site rata-rata nasional
total_luas = luas_kebun_ytd.sum()
total_kg_akt = df_ytd['Kg Akt.'].sum()
total_kg_bgt = df_ytd['Kg Bgt.'].sum()

site_akt = total_kg_akt / total_luas / 1000
site_bgt = total_kg_bgt / total_luas / 1000
site_var_ton = site_akt - site_bgt
site_var_pct = (site_var_ton / site_bgt) * 100

row_total = pd.DataFrame([{
    'Kebun': 'TOTAL SITE',
    'Akt (Ton/Ha)': site_akt,
    'Bgt (Ton/Ha)': site_bgt,
    'Var (Ton/Ha)': site_var_ton,
    'Var (%)': site_var_pct
}])

df_tabel = pd.concat([df_tabel, row_total], ignore_index=True)
df_tabel.insert(0, 'No', range(1, len(df_tabel) + 1))

# Fungsi pewarnaan kolom Var
def style_variance(val):
    if isinstance(val, (int, float)):
        color = 'red' if val < 0 else 'green'
        return f'color: {color}; font-weight: bold;'
    return ''

st.dataframe(
    df_tabel.style.format({
        'Akt (Ton/Ha)': '{:,.2f}',
        'Bgt (Ton/Ha)': '{:,.2f}',
        'Var (Ton/Ha)': '{:+,.2f}',
        'Var (%)': '{:+,.2f}%'
    }).map(style_variance, subset=['Var (Ton/Ha)', 'Var (%)']),
    use_container_width=True,
    hide_index=True
)