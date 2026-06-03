import streamlit as st
import pandas as pd
import plotly.graph_objects as go

# Ambil data global dari session state app.py
df_raw = st.session_state["df_raw"]
pilihan_bulan = st.session_state["pilihan_bulan"]

st.markdown(f"### 🎯 Yield Performance terhadap Sensus (Ton/Ha)")
st.markdown(f"**Periode Analisis:** s/d Bulan {pilihan_bulan} (Kumulatif YTD)")

# --- 1. ENGINE FILTER TIMEFRAME KUMULATIF YTD ---
URUTAN_BULAN_STD = ['JAN', 'FEB', 'MAR', 'APR', 'MEI', 'JUN', 'JUL', 'AGS', 'SEP', 'OKT', 'NOV', 'DES']
pilihan_bulan_std = "AGS" if pilihan_bulan in ["AGUSTUS", "AGS"] else pilihan_bulan

if pilihan_bulan_std in URUTAN_BULAN_STD:
    idx_bulan = URUTAN_BULAN_STD.index(pilihan_bulan_std)
    bulan_ytd = URUTAN_BULAN_STD[:idx_bulan + 1]
else:
    bulan_ytd = [pilihan_bulan_std]

df_ytd = df_raw[df_raw['Bulan'].isin(bulan_ytd)].copy()

# --- 2. GRAFIK LEVEL 1: COMPARISON ANTAR KEBUN ---
st.subheader("📊 1. Grafik Yield Kumulatif YTD - Level Kebun")

luas_kebun = df_ytd.groupby(['Kebun', 'Afdeling'])['Luas'].first().reset_index().groupby('Kebun')['Luas'].sum()

df_kebun = df_ytd.groupby('Kebun').agg({'Kg Akt.': 'sum', 'Kg Sns.': 'sum'}).reset_index()
df_kebun['Luas'] = df_kebun['Kebun'].map(luas_kebun)
df_kebun['Yield_Akt'] = df_kebun['Kg Akt.'] / df_kebun['Luas'] / 1000
df_kebun['Yield_Sns'] = df_kebun['Kg Sns.'] / df_kebun['Luas'] / 1000

fig_k = go.Figure()
fig_k.add_trace(go.Bar(
    x=df_kebun["Kebun"], y=df_kebun["Yield_Akt"],
    name="Yield Aktual", marker_color="#28348A", width=0.3
))
fig_k.add_trace(go.Scatter(
    x=[None], y=[None], mode='lines',
    line=dict(color='#00B050', width=4), name='Target Sensus'
))

for idx, row in df_kebun.iterrows():
    fig_k.add_shape(
        type="line", x0=idx-0.2, x1=idx+0.2,
        y0=row["Yield_Sns"], y1=row["Yield_Sns"],
        line=dict(color="#00B050", width=4)
    )
    if row["Yield_Akt"] < row["Yield_Sns"]:
        fig_k.add_annotation(
            x=idx, y=row["Yield_Sns"], ax=idx, ay=row["Yield_Akt"],
            xref="x", yref="y", axref="x", ayref="y",
            showarrow=True, arrowhead=2, arrowsize=1.2, arrowwidth=2.5, arrowcolor='#FF0000'
        )

fig_k.update_layout(template="plotly_white", yaxis_title="Ton/Ha", legend=dict(orientation="h", y=1.1))
st.plotly_chart(fig_k, use_container_width=True)

st.markdown("---")

# --- 3. GRAFIK LEVEL 2: AFDELING PER KEBUN (INTERAKTIF) ---
st.subheader("🎯 2. Grafik Yield Kumulatif YTD - Level Afdeling per Kebun")

list_kebun = list(df_ytd['Kebun'].unique())
pilihan_kebun_filter = st.selectbox("🔍 Pilih Kebun yang ingin dilihat Afdelingnya:", list_kebun, key="filter_kebun_yield_sns")

df_ytd_filtered = df_ytd[df_ytd['Kebun'] == pilihan_kebun_filter].copy()

luas_afd = df_ytd_filtered.groupby('Afdeling')['Luas'].first()

df_afd = df_ytd_filtered.groupby('Afdeling').agg({'Kg Akt.': 'sum', 'Kg Sns.': 'sum'}).reset_index()
df_afd['Luas'] = df_afd['Afdeling'].map(luas_afd)
df_afd['Yield_Akt'] = df_afd['Kg Akt.'] / df_afd['Luas'] / 1000
df_afd['Yield_Sns'] = df_afd['Kg Sns.'] / df_afd['Luas'] / 1000

fig_a = go.Figure()
fig_a.add_trace(go.Bar(
    x=df_afd["Afdeling"], y=df_afd["Yield_Akt"],
    name="Yield Aktual", marker_color="#28348A", width=0.35
))
fig_a.add_trace(go.Scatter(
    x=[None], y=[None], mode='lines',
    line=dict(color='#00B050', width=4), name='Target Sensus'
))

for idx, row in df_afd.iterrows():
    fig_a.add_shape(
        type="line", x0=idx-0.2, x1=idx+0.2,
        y0=row["Yield_Sns"], y1=row["Yield_Sns"],
        line=dict(color="#00B050", width=4)
    )
    if row["Yield_Akt"] < row["Yield_Sns"]:
        fig_a.add_annotation(
            x=idx, y=row["Yield_Sns"], ax=idx, ay=row["Yield_Akt"],
            xref="x", yref="y", axref="x", ayref="y",
            showarrow=True, arrowhead=2, arrowsize=1.2, arrowwidth=2.5, arrowcolor='#FF0000'
        )

fig_a.update_layout(title=f"Performa Afdeling di Kebun {pilihan_kebun_filter}", template="plotly_white", yaxis_title="Ton/Ha", legend=dict(orientation="h", y=1.1))
st.plotly_chart(fig_a, use_container_width=True)