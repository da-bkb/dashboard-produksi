import streamlit as st
import pandas as pd
import plotly.graph_objects as go

df_raw = st.session_state["df_raw"]
list_bulan = st.session_state["list_bulan"]

st.markdown(f"# 📈 Trend Bulanan Performa Kebun vs Sensus")
st.markdown(f"**Analisis Pergerakan:** Kinerja Bulanan Aktual vs Sensus Januari s/d Desember")

URUTAN_BULAN = ['JAN', 'FEB', 'MAR', 'APR', 'MEI', 'JUN', 'JUL', 'AGS', 'SEP', 'OKT', 'NOV', 'DES']

list_kebun = sorted(df_raw["Kebun"].unique())
pilihan_kebun = st.selectbox("Pilih Kebun untuk melihat Trend Sensus:", list_kebun)

df_kebun = df_raw[df_raw["Kebun"] == pilihan_kebun].copy()

df_luas_pokok = df_kebun.groupby(['Bulan', 'Afdeling']).agg({'Luas': 'first', 'Pokok': 'first'}).reset_index().groupby('Bulan').agg({'Luas': 'sum', 'Pokok': 'sum'}).reset_index()
df_prod = df_kebun.groupby('Bulan').agg({'Kg Akt.': 'sum', 'Kg Sns.': 'sum', 'Jjg Akt.': 'sum', 'Jjg Sns.': 'sum'}).reset_index()
df_trend = pd.merge(df_prod, df_luas_pokok, on='Bulan')

df_trend['Yield Akt.'] = df_trend['Kg Akt.'] / df_trend['Luas'] / 1000
df_trend['Yield Sns.'] = df_trend['Kg Sns.'] / df_trend['Luas'] / 1000
df_trend['Yield_Pct'] = (df_trend['Yield Akt.'] / df_trend['Yield Sns.'] * 100).fillna(0)

df_trend['J/P Akt.'] = df_trend['Jjg Akt.'] / df_trend['Pokok']
df_trend['J/P Sns.'] = df_trend['Jjg Sns.'] / df_trend['Pokok']
df_trend['J/P_Pct'] = (df_trend['J/P Akt.'] / df_trend['J/P Sns.'] * 100).fillna(0)

df_trend['BJR Akt.'] = df_trend['Kg Akt.'] / df_trend['Jjg Akt.']
df_trend['BJR Sns.'] = df_trend['Kg Sns.'] / df_trend['Jjg Sns.']
df_trend['BJR_Pct'] = (df_trend['BJR Akt.'] / df_trend['BJR Sns.'] * 100).fillna(0)

df_trend['Bulan'] = pd.Categorical(df_trend['Bulan'], categories=URUTAN_BULAN, ordered=True)
df_trend = df_trend.sort_values('Bulan').reset_index(drop=True)

# --- GRAFIK 1: YIELD ---
st.markdown("---")
st.subheader("🌱 Trend Yield Performa (Ton/ha)")
fig_yield = go.Figure()
fig_yield.add_trace(go.Bar(x=df_trend["Bulan"], y=df_trend["Yield Akt."], name="Aktual", marker_color="#28348A", width=0.4))
fig_yield.add_trace(go.Scatter(x=df_trend["Bulan"], y=df_trend["Yield Sns."], mode='lines+markers', name='Sensus', line=dict(color='#00B050', width=3, shape='spline'), marker=dict(size=6)))
for idx, row in df_trend.iterrows():
    if pd.isna(row["Bulan"]): continue
    fig_yield.add_annotation(x=idx, y=0, text=f"{row['Yield_Pct']:.1f}%", showarrow=False, yshift=25, textangle=-90, font=dict(color="white", size=11, weight="bold"))
    if row["Yield_Pct"] > 0 and (row["Yield_Pct"] < 90 or row["Yield_Pct"] > 110):
        fig_yield.add_annotation(x=idx, y=row["Yield Sns."], ax=idx, ay=row["Yield Akt."], xref="x", yref="y", axref="x", ayref="y", showarrow=True, arrowhead=2, arrowcolor='#FF0000', standoff=4)
st.plotly_chart(fig_yield, use_container_width=True)

# --- GRAFIK 2: J/P ---
st.markdown("---")
st.subheader("🌴 Trend Janjang Per Pokok Performa (J/P)")
fig_jp = go.Figure()
fig_jp.add_trace(go.Bar(x=df_trend["Bulan"], y=df_trend["J/P Akt."], name="Aktual", marker_color="#28348A", width=0.4))
fig_jp.add_trace(go.Scatter(x=df_trend["Bulan"], y=df_trend["J/P Sns."], mode='lines+markers', name='Sensus', line=dict(color='#00B050', width=3, shape='spline'), marker=dict(size=6)))
for idx, row in df_trend.iterrows():
    if pd.isna(row["Bulan"]): continue
    fig_jp.add_annotation(x=idx, y=0, text=f"{row['J/P_Pct']:.1f}%", showarrow=False, yshift=25, textangle=-90, font=dict(color="white", size=11, weight="bold"))
    if row["J/P_Pct"] > 0 and (row["J/P_Pct"] < 90 or row["J/P_Pct"] > 110):
        fig_jp.add_annotation(x=idx, y=row["J/P Sns."], ax=idx, ay=row["J/P Akt."], xref="x", yref="y", axref="x", ayref="y", showarrow=True, arrowhead=2, arrowcolor='#FF0000', standoff=4)
st.plotly_chart(fig_jp, use_container_width=True)

# --- GRAFIK 3: BJR ---
st.markdown("---")
st.subheader("⚖️ Trend BJR (Kg/Janjang)")
fig_bjr = go.Figure()
fig_bjr.add_trace(go.Bar(x=df_trend["Bulan"], y=df_trend["BJR Akt."], name="Aktual", marker_color="#28348A", width=0.4))
fig_bjr.add_trace(go.Scatter(x=df_trend["Bulan"], y=df_trend["BJR Sns."], mode='lines+markers', name='Sensus', line=dict(color='#00B050', width=3, shape='spline'), marker=dict(size=6)))
for idx, row in df_trend.iterrows():
    if pd.isna(row["Bulan"]): continue
    fig_bjr.add_annotation(x=idx, y=0, text=f"{row['BJR_Pct']:.1f}%", showarrow=False, yshift=25, textangle=-90, font=dict(color="white", size=11, weight="bold"))
    if 0 < row["BJR_Pct"] < 90:
        fig_bjr.add_annotation(x=idx, y=row["BJR Sns."], ax=idx, ay=row["BJR Akt."], xref="x", yref="y", axref="x", ayref="y", showarrow=True, arrowhead=2, arrowcolor='#FF0000', standoff=4)
st.plotly_chart(fig_bjr, use_container_width=True)