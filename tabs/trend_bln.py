import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import numpy as np

# Ambil data global dari session state
df_raw = st.session_state["df_raw"].copy()
list_bulan = st.session_state["list_bulan"]

st.markdown(f"# 📈 Trend Bulanan Performa Kebun")
st.markdown(f"**Analisis Pergerakan:** Kinerja Bulanan Januari s/d Desember")

# --- DETEKSI KOLOM OTOMATIS (Mencegah KeyError saat Sensus/Budget) ---
cols = list(df_raw.columns)
COL_JAN_AKT = next((c for c in cols if 'akt' in c.lower() and any(x in c.lower() for x in ['jg', 'jjg', 'jan', 'janjang'])), "Jjg Akt.")
COL_KG_AKT = next((c for c in cols if 'akt' in c.lower() and ('kg' in c.lower() or 'ton' in c.lower() or 'prod' in c.lower())), None)

# Otomatis mendeteksi target janjang & BJR (apakah Sensus atau Budget)
COL_JAN_BGT = next((c for c in cols if any(x in c.lower() for x in ['bgt', 'budget', 'sns', 'sensus']) and any(y in c.lower() for y in ['jg', 'jjg', 'jan', 'janjang'])), "Jjg Bgt.")
COL_BJR_BGT = next((c for c in cols if any(x in c.lower() for x in ['bgt', 'budget', 'sns', 'sensus']) and 'bjr' in c.lower()), None)

# Pastikan data berupa numeric murni
df_raw[COL_JAN_AKT] = pd.to_numeric(df_raw[COL_JAN_AKT], errors='coerce').fillna(0)
df_raw[COL_JAN_BGT] = pd.to_numeric(df_raw[COL_JAN_BGT], errors='coerce').fillna(0)
if COL_KG_AKT:
    df_raw[COL_KG_AKT] = pd.to_numeric(df_raw[COL_KG_AKT], errors='coerce').fillna(0)
if COL_BJR_BGT:
    df_raw[COL_BJR_BGT] = pd.to_numeric(df_raw[COL_BJR_BGT], errors='coerce').fillna(0)

# --- URUTAN BULAN STANDAR UNTUK SUMBU X ---
URUTAN_BULAN = ['JAN', 'FEB', 'MAR', 'APR', 'MEI', 'JUN', 'JUL', 'AGT', 'SEP', 'OKT', 'NOV', 'DES']

# --- DROP DOWN PILIHAN KEBUN ---
list_kebun = sorted(df_raw["Kebun"].unique())
pilihan_kebun = st.selectbox("Pilih Kebun untuk melihat Trend Bulanan:", list_kebun)

# --- PROSES AGREGASI DATA BULANAN BERDASARKAN KEBUN YANG DIPILIH ---
df_kebun = df_raw[df_raw["Kebun"] == pilihan_kebun].copy()

# Buat total luas dan pokok per bulan (first per afdeling lalu sum per kebun)
df_luas_pokok = df_kebun.groupby(['Bulan', 'Afdeling']).agg({'Luas': 'first', 'Pokok': 'first'}).reset_index()
df_luas_total = df_luas_pokok.groupby('Bulan').agg({'Luas': 'sum', 'Pokok': 'sum'}).reset_index()

# Agregasi kolom produksi utama
df_janjang = df_kebun.groupby('Bulan').agg({
    COL_JAN_AKT: 'sum',
    COL_JAN_BGT: 'sum'
}).reset_index()

# Gabungkan data
df_trend = pd.merge(df_janjang, df_luas_total, on='Bulan', how='left')

# Hitung BJR Aktual & Target secara dinamis
if COL_KG_AKT:
    df_kg_sum = df_kebun.groupby('Bulan')[COL_KG_AKT].sum().reset_index()
    df_trend = pd.merge(df_trend, df_kg_sum, on='Bulan', how='left')
    df_trend["BJR Akt."] = (df_trend[COL_KG_AKT] / df_trend[COL_JAN_AKT]).fillna(0)
else:
    df_trend["BJR Akt."] = 0

if COL_BJR_BGT:
    df_bjr_bgt_mean = df_kebun.groupby('Bulan')[COL_BJR_BGT].mean().reset_index()
    df_trend = pd.merge(df_trend, df_bjr_bgt_mean, on='Bulan', how='left')
    df_trend["BJR Bgt."] = df_trend[COL_BJR_BGT].fillna(0)
else:
    df_trend["BJR Bgt."] = 0

# Penyelarasan nama kolom internal agar grafik lama Bapak tidak rusak
df_trend["Jjg Akt."] = df_trend[COL_JAN_AKT]
df_trend["Jjg Bgt."] = df_trend[COL_JAN_BGT]
df_trend['Bulan'] = pd.Categorical(df_trend['Bulan'].str.upper(), categories=URUTAN_BULAN, ordered=True)
df_trend = df_trend.sort_values('Bulan').reset_index(drop=True)

# Hitung persentase performa janjang & BJR
df_trend["Jjg_Pct"] = np.where(df_trend["Jjg Bgt."] > 0, (df_trend["Jjg Akt."] / df_trend["Jjg Bgt."] * 100), 0)
df_trend["BJR_Pct"] = np.where(df_trend["BJR Bgt."] > 0, (df_trend["BJR Akt."] / df_trend["BJR Bgt."] * 100), 0)

# =========================================================================
# 📊 AREA GRAFIK PLOTLY BAWAAN BAPAK (TIDAK BERUBAH)
# =========================================================================
st.subheader("📦 Trend Janjang Keluar")
fig_jjg = go.Figure()
fig_jjg.add_trace(go.Bar(x=df_trend["Bulan"], y=df_trend["Jjg Akt."], name="Aktual", marker_color="#28348A", width=0.4))
fig_jjg.add_trace(go.Scatter(x=df_trend["Bulan"], y=df_trend["Jjg Bgt."], mode='lines+markers', name='Target/Budget', line=dict(color='#00B050', width=3, shape='spline'), marker=dict(size=6, symbol='circle')))
for idx, row in df_trend.iterrows():
    if pd.isna(row["Bulan"]): continue
    fig_jjg.add_annotation(x=idx, y=0, text=f"{row['Jjg_Pct']:.1f}%", showarrow=False, yshift=25, textangle=-90, font=dict(color="white", size=11, weight="bold"))
    if row["Jjg_Pct"] < 90:
        fig_jjg.add_annotation(x=idx, y=row["Jjg Bgt."], ax=idx, ay=row["Jjg Akt."], xref="x", yref="y", axref="x", ayref="y", showarrow=True, arrowhead=2, arrowsize=1, arrowwidth=2.5, arrowcolor='#FF0000', standoff=4, startstandoff=4)
fig_jjg.update_layout(height=340, margin=dict(l=20, r=20, t=20, b=20), legend=dict(orientation="h", y=1.15))
st.plotly_chart(fig_jjg, use_container_width=True)

st.markdown("---")
st.subheader("⚖️ Trend BJR (Kg/Janjang)")
fig_bjr = go.Figure()
fig_bjr.add_trace(go.Bar(x=df_trend["Bulan"], y=df_trend["BJR Akt."], name="Aktual", marker_color="#28348A", width=0.4))
fig_bjr.add_trace(go.Scatter(x=df_trend["Bulan"], y=df_trend["BJR Bgt."], mode='lines+markers', name='Target/Budget', line=dict(color='#00B050', width=3, shape='spline'), marker=dict(size=6, symbol='circle')))\

for idx, row in df_trend.iterrows():
    if pd.isna(row["Bulan"]): continue
    fig_bjr.add_annotation(x=idx, y=0, text=f"{row['BJR_Pct']:.1f}%", showarrow=False, yshift=25, textangle=-90, font=dict(color="white", size=11, weight="bold"))
    if row["BJR_Pct"] < 95:
        fig_bjr.add_annotation(x=idx, y=row["BJR Bgt."], ax=idx, ay=row["BJR Akt."], xref="x", yref="y", axref="x", ayref="y", showarrow=True, arrowhead=2, arrowsize=1, arrowwidth=2.5, arrowcolor='#FF0000', standoff=4, startstandoff=4)
fig_bjr.update_layout(height=340, margin=dict(l=20, r=20, t=20, b=20), legend=dict(orientation="h", y=1.15))
st.plotly_chart(fig_bjr, use_container_width=True)