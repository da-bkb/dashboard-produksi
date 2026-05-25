import streamlit as st
import pandas as pd
import plotly.graph_objects as go

# Ambil data global dari session state
df_raw = st.session_state["df_raw"]
list_bulan = st.session_state["list_bulan"]

# Nama kolom janjang sesuai Rekap26.csv
COL_JAN_AKT = "Jjg Akt."  
COL_JAN_BGT = "Jjg Bgt."  

st.markdown(f"# 📈 Trend Bulanan Performa Afdeling")
st.markdown(f"**Analisis Pergerakan:** Kinerja Bulanan Afdeling Januari s/d Desember")

# --- URUTAN BULAN STANDAR UNTUK SUMBU X ---
URUTAN_BULAN = ['JAN', 'FEB', 'MAR', 'APR', 'MEI', 'JUN', 'JUL', 'AGT', 'SEP', 'OKT', 'NOV', 'DES']

# --- DROP DOWN BERTINGKAT (KEBUN -> AFDELING) ---
c_sel_1, c_sel_2 = st.columns(2)

with c_sel_1:
    list_kebun = sorted(df_raw["Kebun"].unique())
    pilihan_kebun = st.selectbox("1. Pilih Kebun:", list_kebun)

# Filter afdeling berdasarkan kebun yang dipilih
df_filter_kebun = df_raw[df_raw["Kebun"] == pilihan_kebun].copy()

with c_sel_2:
    list_afdeling = sorted(df_filter_kebun["Afdeling"].unique())
    pilihan_afd = st.selectbox("2. Pilih Afdeling:", list_afdeling)

# --- FILTER DATA BERDASARKAN AFDELING YANG DIPILIH ---
df_afd = df_filter_kebun[df_filter_kebun["Afdeling"] == pilihan_afd].copy()

# Karena sudah level afdeling, kita bisa langsung grouping per Bulan
df_trend = df_afd.groupby('Bulan').agg({
    'Kg Akt.': 'sum', 
    'Kg Bgt.': 'sum', 
    COL_JAN_AKT: 'sum', 
    COL_JAN_BGT: 'sum',
    'Luas': 'first',   # Di level afdeling, luas dan pokok bernilai konstan/fixed
    'Pokok': 'first'
}).reset_index()

# --- KALKULASI METRIK UTAMA LEVEL AFDELING ---
# 1. Yield
df_trend['Yield Akt.'] = df_trend['Kg Akt.'] / df_trend['Luas'] / 1000
df_trend['Yield Bgt.'] = df_trend['Kg Bgt.'] / df_trend['Luas'] / 1000
df_trend['Yield_Pct'] = (df_trend['Yield Akt.'] / df_trend['Yield Bgt.'] * 100).fillna(0)

# 2. Janjang Per Pokok (J/P)
df_trend['J/P Akt.'] = df_trend[COL_JAN_AKT] / df_trend['Pokok']
df_trend['J/P Bgt.'] = df_trend[COL_JAN_BGT] / df_trend['Pokok']
df_trend['J/P_Pct'] = (df_trend['J/P Akt.'] / df_trend['J/P Bgt.'] * 100).fillna(0)

# 3. BJR
df_trend['BJR Akt.'] = df_trend['Kg Akt.'] / df_trend[COL_JAN_AKT]
df_trend['BJR Bgt.'] = df_trend['Kg Bgt.'] / df_trend[COL_JAN_BGT]
df_trend['BJR_Pct'] = (df_trend['BJR Akt.'] / df_trend['BJR Bgt.'] * 100).fillna(0)

# Urutkan berdasarkan kalender bulan JAN - DES
df_trend['Bulan'] = pd.Categorical(df_trend['Bulan'], categories=URUTAN_BULAN, ordered=True)
df_trend = df_trend.sort_values('Bulan').reset_index(drop=True)


# =========================================================================
# 📉 SECTION GRAFIK ANALISIS
# =========================================================================
st.markdown("---")
st.markdown(f"### 📈 Grafik Analisis Trend Bulanan Per Afdeling ({pilihan_afd})")

# 📊 GRAFIK 1: YIELD AFDELING
st.subheader("🌱 Trend Yield (Ton/ha)")
fig_yield = go.Figure()
fig_yield.add_trace(go.Bar(x=df_trend["Bulan"], y=df_trend["Yield Akt."], name="Aktual", marker_color="#28348A", width=0.4))
fig_yield.add_trace(go.Scatter(
    x=df_trend["Bulan"], y=df_trend["Yield Bgt."], mode='lines+markers', name='Budget',
    line=dict(color='#00B050', width=3, shape='spline'),
    marker=dict(size=6, symbol='circle')
))

for idx, row in df_trend.iterrows():
    if pd.isna(row["Bulan"]): continue
    fig_yield.add_annotation(x=idx, y=0, text=f"{row['Yield_Pct']:.1f}%", showarrow=False, yshift=25, textangle=-90, font=dict(color="white", size=11, weight="bold"))
    
    pct = row["Yield_Pct"]
    if pct > 0 and (pct < 90 or pct > 110):
        fig_yield.add_annotation(
            x=idx, y=row["Yield Bgt."], ax=idx, ay=row["Yield Akt."],
            xref="x", yref="y", axref="x", ayref="y",
            showarrow=True, arrowhead=2, arrowsize=1, arrowwidth=2.5, arrowcolor='#FF0000',
            standoff=4, startstandoff=4
        )
fig_yield.update_layout(height=340, margin=dict(l=20, r=20, t=20, b=20), legend=dict(orientation="h", y=1.15))
st.plotly_chart(fig_yield, use_container_width=True)


# 📊 GRAFIK 2: J/P AFDELING
st.markdown("---")
st.subheader("🌴 Trend RJP (J/P)")
fig_jp = go.Figure()
fig_jp.add_trace(go.Bar(x=df_trend["Bulan"], y=df_trend["J/P Akt."], name="Aktual", marker_color="#28348A", width=0.4))
fig_jp.add_trace(go.Scatter(
    x=df_trend["Bulan"], y=df_trend["J/P Bgt."], mode='lines+markers', name='Budget',
    line=dict(color='#00B050', width=3, shape='spline'),
    marker=dict(size=6, symbol='circle')
))

for idx, row in df_trend.iterrows():
    if pd.isna(row["Bulan"]): continue
    fig_jp.add_annotation(x=idx, y=0, text=f"{row['J/P_Pct']:.1f}%", showarrow=False, yshift=25, textangle=-90, font=dict(color="white", size=11, weight="bold"))
    
    pct = row["J/P_Pct"]
    if pct > 0 and (pct < 90 or pct > 110):
        fig_jp.add_annotation(
            x=idx, y=row["J/P Bgt."], ax=idx, ay=row["J/P Akt."],
            xref="x", yref="y", axref="x", ayref="y",
            showarrow=True, arrowhead=2, arrowsize=1, arrowwidth=2.5, arrowcolor='#FF0000',
            standoff=4, startstandoff=4
        )
fig_jp.update_layout(height=340, margin=dict(l=20, r=20, t=20, b=20), legend=dict(orientation="h", y=1.15))
st.plotly_chart(fig_jp, use_container_width=True)


# 📊 GRAFIK 3: BJR AFDELING
st.markdown("---")
st.subheader("⚖️ Trend BJR (Kg/Janjang)")
fig_bjr = go.Figure()
fig_bjr.add_trace(go.Bar(x=df_trend["Bulan"], y=df_trend["BJR Akt."], name="Aktual", marker_color="#28348A", width=0.4))
fig_bjr.add_trace(go.Scatter(
    x=df_trend["Bulan"], y=df_trend["BJR Bgt."], mode='lines+markers', name='Budget',
    line=dict(color='#00B050', width=3, shape='spline'),
    marker=dict(size=6, symbol='circle')
))

for idx, row in df_trend.iterrows():
    if pd.isna(row["Bulan"]): continue
    fig_bjr.add_annotation(x=idx, y=0, text=f"{row['BJR_Pct']:.1f}%", showarrow=False, yshift=25, textangle=-90, font=dict(color="white", size=11, weight="bold"))
    
    pct = row["BJR_Pct"]
    if 0 < pct < 90:
        fig_bjr.add_annotation(
            x=idx, y=row["BJR Bgt."], ax=idx, ay=row["BJR Akt."],
            xref="x", yref="y", axref="x", ayref="y",
            showarrow=True, arrowhead=2, arrowsize=1, arrowwidth=2.5, arrowcolor='#FF0000',
            standoff=4, startstandoff=4
        )
fig_bjr.update_layout(height=340, margin=dict(l=20, r=20, t=20, b=20), legend=dict(orientation="h", y=1.15))
st.plotly_chart(fig_bjr, use_container_width=True)