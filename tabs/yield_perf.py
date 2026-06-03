import streamlit as st
import pandas as pd
import plotly.graph_objects as go

# --- PROSES DATA AKUMULASI (YEAR TO DATE - YTD) ---
URUTAN_BULAN_STANDAR = ['JAN', 'FEB', 'MAR', 'APR', 'MEI', 'JUN', 'JUL', 'AGS', 'SEP', 'OKT', 'NOV', 'DES']

# Standarisasi Input Agustus jika dari widget tertulis AGUSTUS
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

# Filter data YTD menggunakan list bulan standar yang sudah lolos verifikasi
df_ytd = df_raw[df_raw['Bulan'].isin(bulan_ytd)].copy()

# Pilihan Kebun untuk filter internal tab
list_kebun = sorted(df_ytd["Kebun"].unique().tolist())
pilihan_kebun = st.selectbox("Pilih Kebun:", list_kebun, key="yield_kebun_picker")
df_ytd_filtered = df_ytd[df_ytd["Kebun"] == pilihan_kebun].copy()

# Afdeling ytd group
df_afd_ytd_grp = df_ytd_filtered.groupby('Afdeling').agg({
    'Kg Akt.': 'sum',
    'Kg Bgt.': 'sum',
    'Luas': 'first'
}).reset_index()

df_afd_ytd_grp['Yield_Akt'] = df_afd_ytd_grp['Kg Akt.'] / df_afd_ytd_grp['Luas'] / 1000
df_afd_ytd_grp['Yield_Bgt'] = df_afd_ytd_grp['Kg Bgt.'] / df_afd_ytd_grp['Luas'] / 1000
df_afd_ytd_grp['Yield_Pct'] = (df_afd_ytd_grp['Yield_Akt'] / df_afd_ytd_grp['Yield_Bgt'] * 100).fillna(0)

# --- 1. TAMPILAN KARTU METRIK UTAMA ---
total_prod = df_afd_ytd_grp["Kg Akt."].sum()
total_luas = df_afd_ytd_grp["Luas"].sum()
yield_real = total_prod / total_luas if total_luas > 0 else 0

m1, m2, m3 = st.columns(3)
m1.metric("Total Produksi YTD (Kg)", f"{total_prod:,.0f}".replace(",", "."))
m2.metric("Total Luas (Ha)", f"{total_luas:,.2f}".replace(",", "X").replace(".", ",").replace("X", "."))
m3.metric("Yield Realisasi YTD (Kg/Ha)", f"{yield_real:,.2f}".replace(",", "X").replace(".", ",").replace("X", "."))

st.markdown("---")

# --- 2. GRAFIK BATANG TUNGGAL ---
fig = go.Figure()
fig.add_trace(go.Bar(
    x=df_afd_ytd_grp["Afdeling"],
    y=df_afd_ytd_grp["Yield_Akt"],
    name="Realisasi Ton/Ha",
    marker_color="rgb(55, 83, 109)"
))

fig.update_layout(
    title=f"Grafik Yield per Afdeling - {pilihan_kebun} (YTD s/d {pilihan_bulan})",
    xaxis_title="Afdeling",
    yaxis_title="Ton / Ha",
    template="plotly_white"
)
st.plotly_chart(fig, use_container_width=True)

# --- 3. TABEL DATA ---
df_table = df_afd_ytd_grp[["Afdeling", "Luas", "Kg Akt.", "Yield_Akt", "Yield_Pct"]].copy()
df_table["Luas"] = df_table["Luas"].map('{:,.2f}'.format)
df_table["Kg Akt."] = df_table["Kg Akt."].map('{:,.0f}'.format)
df_table["Yield_Akt"] = df_table["Yield_Akt"].map('{:,.2f}'.format)
df_table["Yield_Pct"] = df_table["Yield_Pct"].map('{:,.2f}%'.format)

st.dataframe(df_table, use_container_width=True)