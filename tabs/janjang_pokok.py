import streamlit as st
import pandas as pd
import plotly.graph_objects as go

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

# Pilihan Kebun untuk filter internal tab
list_kebun = sorted(df_ytd["Kebun"].unique().tolist())
pilihan_kebun = st.selectbox("Pilih Kebun:", list_kebun, key="rjp_kebun_picker")
df_ytd_filtered = df_ytd[df_ytd["Kebun"] == pilihan_kebun].copy()

# Perbaikan pemanggilan kolom dari nama variabel ke bentuk string asli database
df_afd_ytd_grp = df_ytd_filtered.groupby('Afdeling').agg({
    'Jjg Akt.': 'sum',
    'Jjg Bgt.': 'sum',
    'Pokok': 'first'
}).reset_index()

df_afd_ytd_grp['JP_Akt'] = df_afd_ytd_grp['Jjg Akt.'] / df_afd_ytd_grp['Pokok']
df_afd_ytd_grp['JP_Bgt'] = df_afd_ytd_grp['Jjg Bgt.'] / df_afd_ytd_grp['Pokok']
df_afd_ytd_grp['JP_Pct'] = (df_afd_ytd_grp['JP_Akt'] / df_afd_ytd_grp['JP_Bgt'] * 100).fillna(0)

# --- 1. TAMPILAN KARTU METRIK UTAMA ---
total_jjg = df_afd_ytd_grp["Jjg Akt."].sum()
total_pokok = df_afd_ytd_grp["Pokok"].sum()
rjp_real = total_jjg / total_pokok if total_pokok > 0 else 0

m1, m2, m3 = st.columns(3)
m1.metric("Total Janjang YTD (Jjg)", f"{total_jjg:,.0f}".replace(",", "."))
m2.metric("Total Pokok (Pkk)", f"{total_pokok:,.0f}".replace(",", "."))
m3.metric("Rasio Janjang Pokok (RJP)", f"{rjp_real:,.2f}".replace(",", "X").replace(".", ",").replace("X", "."))

st.markdown("---")

# --- 2. GRAFIK BATANG TUNGGAL ---
fig = go.Figure()
fig.add_trace(go.Bar(
    x=df_afd_ytd_grp["Afdeling"],
    y=df_afd_ytd_grp["JP_Akt"],
    name="RJP Realisasi",
    marker_color="rgb(26, 118, 255)"
))

fig.update_layout(
    title=f"Grafik RJP per Afdeling - {pilihan_kebun} (YTD s/d {pilihan_bulan})",
    xaxis_title="Afdeling",
    yaxis_title="Janjang / Pokok",
    template="plotly_white"
)
st.plotly_chart(fig, use_container_width=True)

# --- 3. TABEL DATA ---
df_table = df_afd_ytd_grp[["Afdeling", "Pokok", "Jjg Akt.", "JP_Akt", "JP_Pct"]].copy()
df_table["Pokok"] = df_table["Pokok"].map('{:,.0f}'.format)
df_table["Jjg Akt."] = df_table["Jjg Akt."].map('{:,.0f}'.format)
df_table["JP_Akt"] = df_table["JP_Akt"].map('{:,.2f}'.format)
df_table["JP_Pct"] = df_table["JP_Pct"].map('{:,.2f}%'.format)

st.dataframe(df_table, use_container_width=True)