import streamlit as st
import pandas as pd
import plotly.graph_objects as go

# Ambil data global dari session state (pastikan di app.py me-load Rekap26_Sns.csv)
df_raw = st.session_state["df_raw"]
pilihan_bulan = st.session_state["pilihan_bulan"]
list_bulan = st.session_state["list_bulan"]

st.markdown(f"# 🌱 Yield to Sensus Performa (Ton/ha)")
st.markdown(f"**Periode Analisis:** Bulan {pilihan_bulan} & s/d {pilihan_bulan}")

# --- FUNGSI PEWARNAAN 4 WARNA STYLER TABEL ---
def style_gap(val):
    persen_capaian = val + 100
    if persen_capaian >= 90:
        bg = '#00B050'  # Hijau
        color = 'white'
    elif persen_capaian >= 80:
        bg = '#FFFF00'  # Kuning Cerah
        color = 'black'
    elif persen_capaian >= 70:
        bg = '#FF8C00'  # Oranye
        color = 'white'
    else:
        bg = '#FF0000'  # Merah
        color = 'white'
    return f'background-color: {bg}; color: {color}; font-weight: bold; font-size: 11px;'

# --- PROSES DATA BULANAN (MONTH TO DATE - MTD) ---
df_mtd = df_raw[df_raw['Bulan'] == pilihan_bulan].copy()

df_afd_mtd_grp = df_mtd.groupby('Afdeling').agg({
    'Kg Akt.': 'sum',
    'Kg Sns.': 'sum',
    'Luas': 'first'
}).reset_index()

df_afd_mtd_grp['Yield_Akt'] = df_afd_mtd_grp['Kg Akt.'] / df_afd_mtd_grp['Luas'] / 1000
df_afd_mtd_grp['Yield_Sns'] = df_afd_mtd_grp['Kg Sns.'] / df_afd_mtd_grp['Luas'] / 1000
df_afd_mtd_grp['Yield_Pct'] = (df_afd_mtd_grp['Yield_Akt'] / df_afd_mtd_grp['Yield_Sns'] * 100).fillna(0)

# --- PROSES DATA AKUMULASI (YEAR TO DATE - YTD) ---
URUTAN_BULAN_STANDAR = ['JAN', 'FEB', 'MAR', 'APR', 'MEI', 'JUN', 'JUL', 'AGS', 'SEP', 'OKT', 'NOV', 'DES']
pilihan_bulan_std = "AGS" if pilihan_bulan in ["AGUSTUS", "AGS"] else pilihan_bulan

if pilihan_bulan_std in URUTAN_BULAN_STANDAR:
    idx_bulan = URUTAN_BULAN_STANDAR.index(pilihan_bulan_std)
    bulan_ytd = URUTAN_BULAN_STANDAR[:idx_bulan + 1]
else:
    list_bulan_raw = list(df_raw['Bulan'].unique())
    if pilihan_bulan_std in list_bulan_raw:
        idx_bulan = list_bulan_raw.index(pilihan_bulan_std)
        bulan_ytd = list_bulan_raw[:idx_bulan + 1]
    else:
        bulan_ytd = [pilihan_bulan_std]

df_ytd = df_raw[df_raw['Bulan'].isin(bulan_ytd)].copy()

df_afd_ytd_grp = df_ytd.groupby('Afdeling').agg({
    'Kg Akt.': 'sum',
    'Kg Sns.': 'sum',
    'Luas': 'first'
}).reset_index()

df_afd_ytd_grp['Yield_Akt'] = df_afd_ytd_grp['Kg Akt.'] / df_afd_ytd_grp['Luas'] / 1000
df_afd_ytd_grp['Yield_Sns'] = df_afd_ytd_grp['Kg Sns.'] / df_afd_ytd_grp['Luas'] / 1000
df_afd_ytd_grp['Yield_Pct'] = (df_afd_ytd_grp['Yield_Akt'] / df_afd_ytd_grp['Yield_Sns'] * 100).fillna(0)

# --- VISUALISASI MTD ---
st.subheader("📊 Analisis Yield vs Sensus Per Kebun")
fig_m = go.Figure()
fig_m.add_trace(go.Bar(x=df_afd_mtd_grp["Afdeling"], y=df_afd_mtd_grp["Yield_Akt"], name="Aktual", marker_color="#28348A", width=0.4))
fig_m.add_trace(go.Scatter(x=[None], y=[None], mode='lines', line=dict(color='#00B050', width=4), name='Sensus'))

for idx, row in df_afd_mtd_grp.iterrows():
    fig_m.add_shape(type="line", x0=idx-0.2, x1=idx+0.2, y0=row["Yield_Sns"], y1=row["Yield_Sns"], line=dict(color="#00B050", width=4))
    fig_m.add_annotation(x=idx, y=0, text=f"{row['Yield_Pct']:.1f}%", showarrow=False, yshift=25, textangle=-90, font=dict(color="white", size=11, weight='bold'))
    
    pct = row["Yield_Pct"]
    if pct > 0 and (pct < 90 or pct > 110):
        fig_m.add_annotation(
            x=idx, y=row["Yield_Sns"], ax=idx, ay=row["Yield_Akt"],
            xref="x", yref="y", axref="x", ayref="y",
            showarrow=True, arrowhead=2, arrowsize=1, arrowwidth=2.5, arrowcolor='#FF0000', standoff=0, startstandoff=0
        )
fig_m.update_layout(height=320, margin=dict(l=20, r=20, t=20, b=20), legend=dict(orientation="h", y=1.15))
st.plotly_chart(fig_m, use_container_width=True)

# --- VISUALISASI YTD ---
st.subheader("📊 Analisis Yield Kumulatif YTD vs Sensus")
fig_a_y = go.Figure()
fig_a_y.add_trace(go.Bar(x=df_afd_ytd_grp["Afdeling"], y=df_afd_ytd_grp["Yield_Akt"], name="YTD Aktual", marker_color="#28348A", width=0.4))
fig_a_y.add_trace(go.Scatter(x=[None], y=[None], mode='lines', line=dict(color='#00B050', width=4), name='Sensus YTD'))

for idx, row in df_afd_ytd_grp.iterrows():
    fig_a_y.add_shape(type="line", x0=idx-0.2, x1=idx+0.2, y0=row["Yield_Sns"], y1=row["Yield_Sns"], line=dict(color="#00B050", width=4))
    fig_a_y.add_annotation(x=idx, y=0, text=f"{row['Yield_Pct']:.1f}%", showarrow=False, yshift=25, textangle=-90, font=dict(color="white", size=11, weight='bold'))
    
    pct = row["Yield_Pct"]
    if pct > 0 and (pct < 90 or pct > 110):
        fig_a_y.add_annotation(
            x=idx, y=row["Yield_Sns"], ax=idx, ay=row["Yield_Akt"],
            xref="x", yref="y", axref="x", ayref="y",
            showarrow=True, arrowhead=2, arrowsize=1, arrowwidth=2.5, arrowcolor='#FF0000', standoff=0, startstandoff=0
        )
fig_a_y.update_layout(height=320, margin=dict(l=20, r=20, t=20, b=20), legend=dict(orientation="h", y=1.15))
st.plotly_chart(fig_a_y, use_container_width=True)