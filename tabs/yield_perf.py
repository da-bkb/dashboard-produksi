import streamlit as st
import pandas as pd
import plotly.graph_objects as go

# Ambil data global dari session state app.py
df_raw = st.session_state["df_raw"]
pilihan_bulan = st.session_state["pilihan_bulan"]

st.markdown(f"### 🌱 Yield Performance terhadap Budget (Ton/Ha)")
st.markdown(f"**Periode Analisis:** Bulan {pilihan_bulan} & Kumulatif YTD")

# --- PROSES DATA TIMEFRAME (MTD & YTD) ---
df_mtd = df_raw[df_raw['Bulan'] == pilihan_bulan].copy()

URUTAN_BULAN_STD = ['JAN', 'FEB', 'MAR', 'APR', 'MEI', 'JUN', 'JUL', 'AGS', 'SEP', 'OKT', 'NOV', 'DES']
pilihan_bulan_std = "AGS" if pilihan_bulan in ["AGUSTUS", "AGS"] else pilihan_bulan

if pilihan_bulan_std in URUTAN_BULAN_STD:
    idx_bulan = URUTAN_BULAN_STD.index(pilihan_bulan_std)
    bulan_ytd = URUTAN_BULAN_STD[:idx_bulan + 1]
else:
    bulan_ytd = [pilihan_bulan_std]

df_ytd = df_raw[df_raw['Bulan'].isin(bulan_ytd)].copy()

# --- AGREGASI DATA KEBUN/AFDELING ---
# Menghitung Luas secara adil (first) agar tidak ter-sum berulang akibat baris bulan
luas_afd = df_ytd.groupby(['Kebun', 'Afdeling'])['Luas'].first().reset_index().groupby('Afdeling')['Luas'].sum()

# Grup MTD
df_afd_mtd = df_mtd.groupby('Afdeling').agg({'Kg Akt.': 'sum', 'Kg Bgt.': 'sum'}).reset_index()
df_afd_mtd['Luas'] = df_afd_mtd['Afdeling'].map(luas_afd)
df_afd_mtd['Yield_Akt'] = df_afd_mtd['Kg Akt.'] / df_afd_mtd['Luas'] / 1000
df_afd_mtd['Yield_Bgt'] = df_afd_mtd['Kg Bgt.'] / df_afd_mtd['Luas'] / 1000

# Grup YTD
df_afd_ytd = df_ytd.groupby('Afdeling').agg({'Kg Akt.': 'sum', 'Kg Bgt.': 'sum'}).reset_index()
df_afd_ytd['Luas'] = df_afd_ytd['Afdeling'].map(luas_afd)
df_afd_ytd['Yield_Akt'] = df_afd_ytd['Kg Akt.'] / df_afd_ytd['Luas'] / 1000
df_afd_ytd['Yield_Bgt'] = df_afd_ytd['Kg Bgt.'] / df_afd_ytd['Luas'] / 1000

# --- VISUALISASI GRAFIK KUMULATIF YTD ---
fig_ytd = go.Figure()

# Batang Aktual (Biru Tua)
fig_ytd.add_trace(go.Bar(
    x=df_afd_ytd["Afdeling"], y=df_afd_ytd["Yield_Akt"],
    name="YTD Aktual", marker_color="#28348A", width=0.4
))

# Legenda Target (Hijau)
fig_ytd.add_trace(go.Scatter(
    x=[None], y=[None], mode='lines',
    line=dict(color='#00B050', width=4), name='Budget YTD'
))

# Gambar Garis Target & Panah Gap Merah
for idx, row in df_afd_ytd.iterrows():
    fig_ytd.add_shape(
        type="line", x0=idx-0.25, x1=idx+0.25,
        y0=row["Yield_Bgt"], y1=row["Yield_Bgt"],
        line=dict(color="#00B050", width=4)
    )
    if row["Yield_Akt"] < row["Yield_Bgt"]:
        fig_ytd.add_annotation(
            x=idx, y=row["Yield_Bgt"], ax=idx, ay=row["Yield_Akt"],
            xref="x", yref="y", axref="x", ayref="y",
            showarrow=True, arrowhead=2, arrowsize=1.2, arrowwidth=2.5, arrowcolor='#FF0000'
        )

fig_ytd.update_layout(template="plotly_white", yaxis_title="Ton/Ha", legend=dict(orientation="h", y=1.1))
st.plotly_chart(fig_ytd, use_container_width=True)