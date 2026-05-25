import streamlit as st
import pandas as pd
import plotly.graph_objects as go

# Ambil data global dari session state
df_raw = st.session_state["df_raw"]
list_bulan = st.session_state["list_bulan"]

# Nama kolom janjang sesuai Rekap26.csv
COL_JAN_AKT = "Jjg Akt."  
COL_JAN_BGT = "Jjg Bgt."  

st.markdown(f"# 📈 Trend Bulanan Performa Kebun")
st.markdown(f"**Analisis Pergerakan:** Kinerja Bulanan Januari s/d Desember")

# --- URUTAN BULAN STANDAR UNTUK SUMBU X ---
URUTAN_BULAN = ['JAN', 'FEB', 'MAR', 'APR', 'MEI', 'JUN', 'JUL', 'AGS', 'SEP', 'OKT', 'NOV', 'DES']

# --- DROP DOWN PILIHAN KEBUN ---
list_kebun = sorted(df_raw["Kebun"].unique())
pilihan_kebun = st.selectbox("Pilih Kebun untuk melihat Trend Bulanan:", list_kebun)

# --- PROSES AGREGASI DATA BULANAN BERDASARKAN KEBUN YANG DIPILIH ---
df_kebun = df_raw[df_raw["Kebun"] == pilihan_kebun].copy()

# Buat total luas dan pokok per bulan (first per afdeling lalu sum per kebun)
df_luas_pokok = df_kebun.groupby(['Bulan', 'Afdeling']).agg({'Luas': 'first', 'Pokok': 'first'}).reset_index().groupby('Bulan').agg({'Luas': 'sum', 'Pokok': 'sum'}).reset_index()

# Buat total produksi bulanan
df_prod = df_kebun.groupby('Bulan').agg({'Kg Akt.': 'sum', 'Kg Bgt.': 'sum', COL_JAN_AKT: 'sum', COL_JAN_BGT: 'sum'}).reset_index()

# Gabungkan data
df_trend = pd.merge(df_prod, df_luas_pokok, on='Bulan')

# --- KALKULASI METRIK UTAMA ---
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
df_trend['BJR Bgt.'] = df_trend['Kg Bgt.'] / df_trend['Kg Bgt.'] # Penjaga logika jika pembagi kosong
df_trend['BJR Bgt.'] = df_trend['Kg Bgt.'] / df_trend[COL_JAN_BGT]
df_trend['BJR_Pct'] = (df_trend['BJR Akt.'] / df_trend['BJR Bgt.'] * 100).fillna(0)

# Mengurutkan index berdasarkan kalender bulan
df_trend['Bulan'] = pd.Categorical(df_trend['Bulan'], categories=URUTAN_BULAN, ordered=True)
df_trend = df_trend.sort_values('Bulan').reset_index(drop=True)


# =========================================================================
# 📊 GRAFIK 1: TREND YIELD PERFORMA
# =========================================================================
st.markdown("---")
st.subheader("🌱 Trend Yield (Ton/ha)")

fig_yield = go.Figure()
fig_yield.add_trace(go.Bar(x=df_trend["Bulan"], y=df_trend["Yield Akt."], name="Aktual", marker_color="#28348A", width=0.4))

# Budget menggunakan Smoothed Line + Marker Bulat Kecil
fig_yield.add_trace(go.Scatter(
    x=df_trend["Bulan"], y=df_trend["Yield Bgt."], 
    mode='lines+markers', 
    name='Budget',
    line=dict(color='#00B050', width=3, shape='spline'),
    marker=dict(size=6, symbol='circle')
))

for idx, row in df_trend.iterrows():
    if pd.isna(row["Bulan"]): continue
    # % Capaian di bawah batang
    fig_yield.add_annotation(x=idx, y=0, text=f"{row['Yield_Pct']:.1f}%", showarrow=False, yshift=25, textangle=-90, font=dict(color="white", size=11, weight="bold"))
    
    # Logika Panah Yield: <90% atau >110%
    pct = row["Yield_Pct"]
    if pct > 0 and (pct < 90 or pct > 110):
        fig_yield.add_annotation(
            x=idx, y=row["Yield Bgt."], ax=idx, ay=row["Yield Akt."],
            xref="x", yref="y", axref="x", ayref="y",
            showarrow=True, arrowhead=2, arrowsize=1, arrowwidth=2.5, arrowcolor='#FF0000',
            standoff=4, startstandoff=4
        )

fig_yield.update_layout(height=350, margin=dict(l=20, r=20, t=20, b=20), legend=dict(orientation="h", y=1.15))
st.plotly_chart(fig_yield, use_container_width=True)


# =========================================================================
# 📊 GRAFIK 2: TREND JANJANG PER POKOK (J/P)
# =========================================================================
st.markdown("---")
st.subheader("🌴 Trend RJP (J/P)")

fig_jp = go.Figure()
fig_jp.add_trace(go.Bar(x=df_trend["Bulan"], y=df_trend["J/P Akt."], name="Aktual", marker_color="#28348A", width=0.4))

# Budget menggunakan Smoothed Line + Marker Bulat Kecil
fig_jp.add_trace(go.Scatter(
    x=df_trend["Bulan"], y=df_trend["J/P Bgt."], 
    mode='lines+markers', 
    name='Budget',
    line=dict(color='#00B050', width=3, shape='spline'),
    marker=dict(size=6, symbol='circle')
))

for idx, row in df_trend.iterrows():
    if pd.isna(row["Bulan"]): continue
    # % Capaian di bawah batang
    fig_jp.add_annotation(x=idx, y=0, text=f"{row['J/P_Pct']:.1f}%", showarrow=False, yshift=25, textangle=-90, font=dict(color="white", size=11, weight="bold"))
    
    # Logika Panah J/P: <90% atau >110%
    pct = row["J/P_Pct"]
    if pct > 0 and (pct < 90 or pct > 110):
        fig_jp.add_annotation(
            x=idx, y=row["J/P Bgt."], ax=idx, ay=row["J/P Akt."],
            xref="x", yref="y", axref="x", ayref="y",
            showarrow=True, arrowhead=2, arrowsize=1, arrowwidth=2.5, arrowcolor='#FF0000',
            standoff=4, startstandoff=4
        )

fig_jp.update_layout(height=350, margin=dict(l=20, r=20, t=20, b=20), legend=dict(orientation="h", y=1.15))
st.plotly_chart(fig_jp, use_container_width=True)


# =========================================================================
# 📊 GRAFIK 3: TREND BJR PERFORMA
# =========================================================================
st.markdown("---")
st.subheader("⚖️ Trend BJR (Kg/Janjang)")

fig_bjr = go.Figure()
fig_bjr.add_trace(go.Bar(x=df_trend["Bulan"], y=df_trend["BJR Akt."], name="Aktual", marker_color="#28348A", width=0.4))

# Budget menggunakan Smoothed Line + Marker Bulat Kecil
fig_bjr.add_trace(go.Scatter(
    x=df_trend["Bulan"], y=df_trend["BJR Bgt."], 
    mode='lines+markers', 
    name='Budget',
    line=dict(color='#00B050', width=3, shape='spline'),
    marker=dict(size=6, symbol='circle')
))

for idx, row in df_trend.iterrows():
    if pd.isna(row["Bulan"]): continue
    # % Capaian di bawah batang
    fig_bjr.add_annotation(x=idx, y=0, text=f"{row['BJR_Pct']:.1f}%", showarrow=False, yshift=25, textangle=-90, font=dict(color="white", size=11, weight="bold"))
    
    # Logika Panah BJR: Hanya jika capaian < 90%
    pct = row["BJR_Pct"]
    if 0 < pct < 90:
        fig_bjr.add_annotation(
            x=idx, y=row["BJR Bgt."], ax=idx, ay=row["BJR Akt."],
            xref="x", yref="y", axref="x", ayref="y",
            showarrow=True, arrowhead=2, arrowsize=1, arrowwidth=2.5, arrowcolor='#FF0000',
            standoff=4, startstandoff=4
        )

fig_bjr.update_layout(height=350, margin=dict(l=20, r=20, t=20, b=20), legend=dict(orientation="h", y=1.15))
st.plotly_chart(fig_bjr, use_container_width=True)