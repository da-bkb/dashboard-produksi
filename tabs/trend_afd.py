import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import numpy as np

# Ambil data global dari session state app.py
df_raw = st.session_state["df_raw"].copy()
list_bulan = st.session_state["list_bulan"]

# --- 1. JUDUL UTAMA ---
st.markdown(f"# 📊 Trend Bulanan Per Afdeling")

# --- 2. DETEKSI KOLOM SECARA OTOMATIS ---
cols = list(df_raw.columns)

# Deteksi Kolom Aktual
COL_KG_AKT = next((c for c in cols if 'akt' in c.lower() and ('kg' in c.lower() or 'prod' in c.lower())), "Kg Akt.")
COL_JAN_AKT = next((c for c in cols if 'akt' in c.lower() and any(x in c.lower() for x in ['jg', 'jjg', 'jan', 'janjang'])), "Jjg Akt.")

# Deteksi Kolom Target (Dinamis mengikuti file Budget / Sensus)
COL_KG_BGT = next((c for c in cols if any(x in c.lower() for x in ['bgt', 'budget', 'sns', 'sensus']) and ('kg' in c.lower() or 'prod' in c.lower())), None)
COL_JAN_BGT = next((c for c in cols if any(x in c.lower() for x in ['bgt', 'budget', 'sns', 'sensus']) and any(x in c.lower() for x in ['jg', 'jjg', 'jan', 'janjang'])), None)
COL_HA = next((c for c in cols if 'ha' in c.lower() or 'luas' in c.lower()), None)

# Cek tipe target untuk label grafik
LABEL_TARGET = "Target Budget"
if COL_KG_BGT and 'sns' in COL_KG_BGT.lower():
    LABEL_TARGET = "Target Sensus"

# --- 3. FILTER DOUBLE DROP-DOWN (Kebun & Afdeling) ---
col_f1, col_f2 = st.columns(2)

with col_f1:
    if 'Kebun' in df_raw.columns:
        list_kebun = list(df_raw['Kebun'].unique())
        pilihan_kebun = st.selectbox("📍 Pilih Kebun:", list_kebun, key="trend_afd_kebun_picker")
        df_kebun_filtered = df_raw[df_raw['Kebun'] == pilihan_kebun].copy()
    else:
        df_kebun_filtered = df_raw.copy()

with col_f2:
    if 'Afdeling' in df_kebun_filtered.columns:
        list_afd = list(df_kebun_filtered['Afdeling'].unique())
        pilihan_afd = st.selectbox("🚪 Pilih Afdeling:", list_afd, key="trend_afd_picker")
        df_filtered = df_kebun_filtered[df_kebun_filtered['Afdeling'] == pilihan_afd].copy()
    else:
        df_filtered = df_kebun_filtered.copy()

# --- 4. AGREGASI DATA TREN BULANAN ---
URUTAN_BULAN_STD = ['JAN', 'FEB', 'MAR', 'APR', 'MEI', 'JUN', 'JUL', 'AGT', 'SEP', 'OKT', 'NOV', 'DES']
df_filtered['Bulan_Idx'] = df_filtered['Bulan'].apply(lambda x: URUTAN_BULAN_STD.index(x) if x in URUTAN_BULAN_STD else 99)
df_filtered = df_filtered[df_filtered['Bulan_Idx'] != 99]

df_trend = df_filtered.groupby(["Bulan_Idx", "Bulan"]).agg({
    COL_KG_AKT: 'sum',
    COL_JAN_AKT: 'sum',
    COL_KG_BGT: 'sum',
    COL_JAN_BGT: 'sum',
    COL_HA: 'sum' if COL_HA else 'max'
}).reset_index()

df_trend = df_trend.sort_values("Bulan_Idx").reset_index(drop=True)

# Hitung Indikator Utama (Yield, RJP, BJR)
df_trend["Yield Akt."] = np.where(df_trend[COL_HA] > 0, df_trend[COL_KG_AKT] / 1000 / df_trend[COL_HA], 0)
df_trend["Yield Bgt."] = np.where(df_trend[COL_HA] > 0, df_trend[COL_KG_BGT] / 1000 / df_trend[COL_HA], 0)

df_trend["RJP Akt."] = np.where(df_trend[COL_HA] > 0, df_trend[COL_JAN_AKT] / (df_trend[COL_HA] * 135), 0)
df_trend["RJP Bgt."] = np.where(df_trend[COL_HA] > 0, df_trend[COL_JAN_BGT] / (df_trend[COL_HA] * 135), 0)

df_trend["BJR Akt."] = np.where(df_trend[COL_JAN_AKT] > 0, df_trend[COL_KG_AKT] / df_trend[COL_JAN_AKT], 0)
df_trend["BJR Bgt."] = np.where(df_trend[COL_JAN_BGT] > 0, df_trend[COL_KG_BGT] / df_trend[COL_JAN_BGT], 0)

# Hitung Persentase Variansi
df_trend["Yield_Pct"] = np.where(df_trend["Yield Bgt."] > 0, (df_trend["Yield Akt."] / df_trend["Yield Bgt."] * 100) - 100, 0)
df_trend["RJP_Pct"] = np.where(df_trend["RJP Bgt."] > 0, (df_trend["RJP Akt."] / df_trend["RJP Bgt."] * 100) - 100, 0)
df_trend["BJR_Pct"] = np.where(df_trend["BJR Bgt."] > 0, (df_trend["BJR Akt."] / df_trend["BJR Bgt."] * 100) - 100, 0)


# =========================================================================
# FUNGSI UNTUK MEMBUAT GARIS HUBUNG PUTUS-PUTUS (DROP LINES KONDISIONAL)
# =========================================================================
def tambah_garis_hubung_afd(fig, df, col_akt, col_bgt):
    """
    Menambahkan garis hubung putus-putus tegak lurus antara Aktual dan Target.
    Merah jika Aktual < Target (Dibawah Target)
    Kuning jika Aktual >= Target (Diatas Target)
    """
    for idx, row in df.iterrows():
        if row[col_akt] == 0:  # Skip jika bulan tersebut belum ada data aktual
            continue
            
        # Tentukan warna berdasarkan kondisi pencapaian target
        warna_garis = "#C62828" if row[col_akt] < row[col_bgt] else "#FFD600"
        
        fig.add_trace(go.Scatter(
            x=[row["Bulan"], row["Bulan"]],
            y=[row[col_bgt], row[col_akt]],
            mode="lines",
            line=dict(color=warna_garis, width=2, dash="dot"),
            showlegend=False,
            hoverinfo="skip"
        ))

# =========================================================================
# 📉 GRAFIK 1: TREND YIELD (TON/HA)
# =========================================================================
st.markdown("---")
st.subheader("TREND YIELD (TON/HA)")

fig_yield = go.Figure()

# 1. Garis Aktual (Smooth Spline, Warna Batang Asli, Marker Merah)
fig_yield.add_trace(go.Scatter(
    x=df_trend["Bulan"], y=df_trend["Yield Akt."],
    mode='lines+markers', name="Aktual",
    line=dict(color='#28348A', width=3, shape='spline'),
    marker=dict(size=8, color='#C62828', symbol='circle')
))

# 2. Garis Target
fig_yield.add_trace(go.Scatter(
    x=df_trend["Bulan"], y=df_trend["Yield Bgt."],
    mode='lines+markers', name=LABEL_TARGET,
    line=dict(color='#00B050', width=3, shape='spline'),
    marker=dict(size=6, color='#FFFF00', line=dict(color='#00B050', width=1))
))

# 3. Suntik Garis Hubung Putus-Putus Kondisional
tambah_garis_hubung_afd(fig_yield, df_trend, "Yield Akt.", "Yield Bgt.")

# Menampilkan anotasi angka persentase (weight="bold")
for idx, row in df_trend.iterrows():
    if row["Yield Akt."] > 0:
        fig_yield.add_annotation(
            x=row["Bulan"], y=max(row["Yield Akt."], row["Yield Bgt."]),
            text=f"{row['Yield_Pct']:+.1f}%", showarrow=False, yshift=15,
            font=dict(color="#28348A", size=10, weight="bold")
        )

fig_yield.update_layout(margin=dict(l=20, r=20, t=20, b=20), hovermode="x unified", height=350)
st.plotly_chart(fig_yield, use_container_width=True)


# =========================================================================
# 🌱 GRAFIK 2: TREND RJP (JANJANG/POKOK)
# =========================================================================
st.markdown("---")
st.subheader("TREND RJP (JANJANG/POKOK)")

fig_rjp = go.Figure()

# Garis Aktual
fig_rjp.add_trace(go.Scatter(
    x=df_trend["Bulan"], y=df_trend["RJP Akt."],
    mode='lines+markers', name="Aktual",
    line=dict(color='#28348A', width=3, shape='spline'),
    marker=dict(size=8, color='#C62828', symbol='circle')
))

# Garis Target
fig_rjp.add_trace(go.Scatter(
    x=df_trend["Bulan"], y=df_trend["RJP Bgt."],
    mode='lines+markers', name=LABEL_TARGET,
    line=dict(color='#00B050', width=3, shape='spline'),
    marker=dict(size=6, color='#FFFF00', line=dict(color='#00B050', width=1))
))

# Suntik Garis Hubung Putus-Putus Kondisional
tambah_garis_hubung_afd(fig_rjp, df_trend, "RJP Akt.", "RJP Bgt.")

for idx, row in df_trend.iterrows():
    if row["RJP Akt."] > 0:
        fig_rjp.add_annotation(
            x=row["Bulan"], y=max(row["RJP Akt."], row["RJP Bgt."]),
            text=f"{row['RJP_Pct']:+.1f}%", showarrow=False, yshift=15,
            font=dict(color="#28348A", size=10, weight="bold")
        )

fig_rjp.update_layout(margin=dict(l=20, r=20, t=20, b=20), hovermode="x unified", height=350)
st.plotly_chart(fig_rjp, use_container_width=True)


# =========================================================================
# ⚖️ GRAFIK 3: TREND BJR (KG/JJG)
# =========================================================================
st.markdown("---")
st.subheader("TREND BJR (KG/JJG)")

fig_bjr = go.Figure()

# Garis Aktual
fig_bjr.add_trace(go.Scatter(
    x=df_trend["Bulan"], y=df_trend["BJR Akt."],
    mode='lines+markers', name="Aktual",
    line=dict(color='#28348A', width=3, shape='spline'),
    marker=dict(size=8, color='#C62828', symbol='circle')
))

# Garis Target
fig_bjr.add_trace(go.Scatter(
    x=df_trend["Bulan"], y=df_trend["BJR Bgt."],
    mode='lines+markers', name=LABEL_TARGET,
    line=dict(color='#00B050', width=3, shape='spline'),
    marker=dict(size=6, color='#FFFF00', line=dict(color='#00B050', width=1))
))

# Suntik Garis Hubung Putus-Putus Kondisional
tambah_garis_hubung_afd(fig_bjr, df_trend, "BJR Akt.", "BJR Bgt.")

for idx, row in df_trend.iterrows():
    if row["BJR Akt."] > 0:
        fig_bjr.add_annotation(
            x=row["Bulan"], y=max(row["BJR Akt."], row["BJR Bgt."]),
            text=f"{row['BJR_Pct']:+.1f}%", showarrow=False, yshift=15,
            font=dict(color="#28348A", size=10, weight="bold")
        )

fig_bjr.update_layout(margin=dict(l=20, r=20, t=20, b=20), hovermode="x unified", height=350)
st.plotly_chart(fig_bjr, use_container_width=True)