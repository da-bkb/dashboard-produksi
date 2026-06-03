import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import numpy as np

# Ambil data global dari session state app.py
df_raw = st.session_state["df_raw"].copy()
list_bulan = st.session_state["list_bulan"]

# --- 1. PERBAIKAN JUDUL UTAMA (SESUAI PERINTAH) ---
st.markdown(f"# 📈 Trend Bulanan Per Kebun")

# --- 2. DETEKSI DUSTA KOLOM SECARA OTOMATIS (Mencegah KeyError Sensus/Budget) ---
cols = list(df_raw.columns)

# Deteksi Kolom Aktual
COL_KG_AKT = next((c for c in cols if 'akt' in c.lower() and ('kg' in c.lower() or 'prod' in c.lower())), "Kg Akt.")
COL_JAN_AKT = next((c for c in cols if 'akt' in c.lower() and any(x in c.lower() for x in ['jg', 'jjg', 'jan', 'janjang'])), "Jjg Akt.")

# Deteksi Kolom Target (Dinamis: Bisa Budget / Sensus tergantung file yang dimuat)
COL_KG_BGT = next((c for c in cols if any(x in c.lower() for x in ['bgt', 'budget', 'sns', 'sensus']) and ('kg' in c.lower() or 'prod' in c.lower())), None)
COL_JAN_BGT = next((c for c in cols if any(x in c.lower() for x in ['bgt', 'budget', 'sns', 'sensus']) and any(y in c.lower() for y in ['jg', 'jjg', 'jan', 'janjang'])), None)
COL_BJR_BGT = next((c for c in cols if any(x in c.lower() for x in ['bgt', 'budget', 'sns', 'sensus']) and 'bjr' in c.lower()), None)

# Label Dinamis untuk Legend Garis Target
LABEL_TARGET = "Sensus" if any('sns' in c.lower() or 'sensus' in c.lower() for c in cols) else "Budget"

# Pastikan data berupa murni numeric
for col in [COL_KG_AKT, COL_JAN_AKT, COL_KG_BGT, COL_JAN_BGT, COL_BJR_BGT]:
    if col and col in df_raw.columns:
        df_raw[col] = pd.to_numeric(df_raw[col].astype(str).str.replace(',', '.'), errors='coerce').fillna(0)

# --- 3. URUTAN BULAN STANDAR UNTUK SUMBU X ---
URUTAN_BULAN = ['JAN', 'FEB', 'MAR', 'APR', 'MEI', 'JUN', 'JUL', 'AGT', 'SEP', 'OKT', 'NOV', 'DES']

# --- 4. DROP DOWN PILIHAN KEBUN ---
list_kebun = sorted(df_raw["Kebun"].unique())
pilihan_kebun = st.selectbox("Pilih Kebun untuk melihat Trend Bulanan:", list_kebun)

# --- 5. PROSES AGREGASI DATA BULANAN BERDASARKAN KEBUN ---
df_kebun = df_raw[df_raw["Kebun"] == pilihan_kebun].copy()

# Ambil total luas dan pokok per bulan (first per afdeling lalu sum per kebun)
df_luas_pokok = df_kebun.groupby(['Bulan', 'Afdeling']).agg({'Luas': 'first', 'Pokok': 'first'}).reset_index()
df_luas_total = df_luas_pokok.groupby('Bulan').agg({'Luas': 'sum', 'Pokok': 'sum'}).reset_index()

# Agregasi kolom utama yang tersedia di file
agg_dict = {COL_KG_AKT: 'sum', COL_JAN_AKT: 'sum'}
if COL_KG_BGT: agg_dict[COL_KG_BGT] = 'sum'
if COL_JAN_BGT: agg_dict[COL_JAN_BGT] = 'sum'

df_main = df_kebun.groupby('Bulan').agg(agg_dict).reset_index()

# Gabungkan data janjang/kg dengan luas/pokok
df_trend = pd.merge(df_main, df_luas_total, on='Bulan', how='left')

# Hitung komponen analisa Yield
df_trend["Yield Akt."] = (df_trend[COL_KG_AKT] / 1000 / df_trend["Luas"]).fillna(0)
if COL_KG_BGT:
    df_trend["Yield Bgt."] = (df_trend[COL_KG_BGT] / 1000 / df_trend["Luas"]).fillna(0)
else:
    df_trend["Yield Bgt."] = 0

# Hitung komponen analisa RJP
df_trend["RJP Akt."] = (df_trend[COL_JAN_AKT] / df_trend["Pokok"]).fillna(0)
if COL_JAN_BGT:
    df_trend["RJP Bgt."] = (df_trend[COL_JAN_BGT] / df_trend["Pokok"]).fillna(0)
else:
    df_trend["RJP Bgt."] = 0

# Hitung komponen analisa BJR
df_trend["BJR Akt."] = (df_trend[COL_KG_AKT] / df_trend[COL_JAN_AKT]).fillna(0)
if COL_BJR_BGT:
    # Jika di file sensus ada kolom BJR Sensus langsung, kita ambil rata-ratanya
    df_bjr_bgt_mean = df_kebun.groupby('Bulan')[COL_BJR_BGT].mean().reset_index()
    df_trend = pd.merge(df_trend, df_bjr_bgt_mean, on='Bulan', how='left')
    df_trend["BJR Bgt."] = df_trend[COL_BJR_BGT].fillna(0)
elif COL_KG_BGT and COL_JAN_BGT:
    df_trend["BJR Bgt."] = (df_trend[COL_KG_BGT] / df_trend[COL_JAN_BGT]).fillna(0)
else:
    df_trend["BJR Bgt."] = 0

# Sinkronisasi urutan bulan di sumbu X
df_trend['Bulan'] = pd.Categorical(df_trend['Bulan'].str.upper(), categories=URUTAN_BULAN, ordered=True)
df_trend = df_trend.sort_values('Bulan').reset_index(drop=True)

# Hitung % Capaian untuk masing-masing matriks
df_trend["Yield_Pct"] = np.where(df_trend["Yield Bgt."] > 0, (df_trend["Yield Akt."] / df_trend["Yield Bgt."] * 100), 0)
df_trend["RJP_Pct"] = np.where(df_trend["RJP Bgt."] > 0, (df_trend[COL_JAN_AKT] / df_trend[COL_JAN_BGT] * 100), 0)
df_trend["BJR_Pct"] = np.where(df_trend["BJR Bgt."] > 0, (df_trend["BJR Akt."] / df_trend["BJR Bgt."] * 100), 0)


# =========================================================================
# 📊 GRAFIK 1: TREND YIELD (TON/HA)
# =========================================================================
st.markdown("---")
st.subheader("TREND YIELD (TON/HA)")

fig_yield = go.Figure()
fig_yield.add_trace(go.Bar(x=df_trend["Bulan"], y=df_trend["Yield Akt."], name="Aktual", marker_color="#28348A", width=0.4))
fig_yield.add_trace(go.Scatter(
    x=df_trend["Bulan"], y=df_trend["Yield Bgt."], mode='lines+markers', name=LABEL_TARGET,
    line=dict(color='#00B050', width=3, shape='spline'),
    marker=dict(size=6, symbol='circle', color='#FFFF00', line=dict(color='#00B050', width=1)) # Marker kuning cerah
))

for idx, row in df_trend.iterrows():
    if pd.isna(row["Bulan"]): continue
    # Hanya munculkan persentase dan panah jika data aktual sudah terisi (> 0)
    if row["Yield Akt."] > 0:
        fig_yield.add_annotation(x=idx, y=0, text=f"{row['Yield_Pct']:.1f}%", showarrow=False, yshift=25, textangle=-90, font=dict(color="white", size=11, weight="bold"))
        if row["Yield_Pct"] < 90:
            fig_yield.add_annotation(x=idx, y=row["Yield Bgt."], ax=idx, ay=row["Yield Akt."], xref="x", yref="y", axref="x", ayref="y", showarrow=True, arrowhead=2, arrowsize=1, arrowwidth=2.5, arrowcolor='#FF0000', standoff=4, startstandoff=4)

fig_yield.update_layout(height=340, margin=dict(l=20, r=20, t=20, b=20), legend=dict(orientation="h", y=1.15))
st.plotly_chart(fig_yield, use_container_width=True)


# =========================================================================
# 📊 GRAFIK 2: TREND RJP (JJG/PKK)
# =========================================================================
st.markdown("---")
st.subheader("TREND RJP (JJG/PKK)")

fig_rjp = go.Figure()
fig_rjp.add_trace(go.Bar(x=df_trend["Bulan"], y=df_trend["RJP Akt."], name="Aktual", marker_color="#28348A", width=0.4))
fig_rjp.add_trace(go.Scatter(
    x=df_trend["Bulan"], y=df_trend["RJP Bgt."], mode='lines+markers', name=LABEL_TARGET,
    line=dict(color='#00B050', width=3, shape='spline'),
    marker=dict(size=6, symbol='circle', color='#FFFF00', line=dict(color='#00B050', width=1)) # Marker kuning cerah
))

for idx, row in df_trend.iterrows():
    if pd.isna(row["Bulan"]): continue
    # Hanya munculkan persentase dan panah jika data aktual sudah terisi (> 0)
    if row["RJP Akt."] > 0:
        fig_rjp.add_annotation(x=idx, y=0, text=f"{row['RJP_Pct']:.1f}%", showarrow=False, yshift=25, textangle=-90, font=dict(color="white", size=11, weight="bold"))
        if row["RJP_Pct"] < 90:
            fig_rjp.add_annotation(x=idx, y=row["RJP Bgt."], ax=idx, ay=row["RJP Akt."], xref="x", yref="y", axref="x", ayref="y", showarrow=True, arrowhead=2, arrowsize=1, arrowwidth=2.5, arrowcolor='#FF0000', standoff=4, startstandoff=4)

fig_rjp.update_layout(height=340, margin=dict(l=20, r=20, t=20, b=20), legend=dict(orientation="h", y=1.15))
st.plotly_chart(fig_rjp, use_container_width=True)


# =========================================================================
# 📊 GRAFIK 3: TREND BJR (KG/JJG)
# =========================================================================
st.markdown("---")
st.subheader("TREND BJR (KG/JJG)")

fig_bjr = go.Figure()
fig_bjr.add_trace(go.Bar(x=df_trend["Bulan"], y=df_trend["BJR Akt."], name="Aktual", marker_color="#28348A", width=0.4))
fig_bjr.add_trace(go.Scatter(
    x=df_trend["Bulan"], y=df_trend["BJR Bgt."], mode='lines+markers', name=LABEL_TARGET,
    line=dict(color='#00B050', width=3, shape='spline'),
    marker=dict(size=6, symbol='circle', color='#FFFF00', line=dict(color='#00B050', width=1)) # Marker kuning cerah
))

for idx, row in df_trend.iterrows():
    if pd.isna(row["Bulan"]): continue
    # Hanya munculkan persentase dan panah jika data aktual sudah terisi (> 0)
    if row["BJR Akt."] > 0:
        fig_bjr.add_annotation(x=idx, y=0, text=f"{row['BJR_Pct']:.1f}%", showarrow=False, yshift=25, textangle=-90, font=dict(color="white", size=11, weight="bold"))
        if row["BJR_Pct"] < 95:
            fig_bjr.add_annotation(x=idx, y=row["BJR Bgt."], ax=idx, ay=row["BJR Akt."], xref="x", yref="y", axref="x", ayref="y", showarrow=True, arrowhead=2, arrowsize=1, arrowwidth=2.5, arrowcolor='#FF0000', standoff=4, startstandoff=4)

fig_bjr.update_layout(height=340, margin=dict(l=20, r=20, t=20, b=20), legend=dict(orientation="h", y=1.15))
st.plotly_chart(fig_bjr, use_container_width=True)