import streamlit as st
import pandas as pd
import plotly.graph_objects as go

df_raw = st.session_state["df_raw"]
pilihan_bulan = st.session_state["pilihan_bulan"]

df_bln = df_raw[df_raw["Bulan"] == pilihan_bulan].copy()

list_kebun = sorted(df_bln["Kebun"].unique().tolist())
pilihan_kebun = st.selectbox("Pilih Kebun:", list_kebun, key="rjp_kebun_picker")

df_filtered = df_bln[df_bln["Kebun"] == pilihan_kebun].copy()

# Perhitungan Metrik Utama atas
total_jjg = df_filtered["Jjg Akt."].sum()
total_pokok = df_filtered["Pokok"].sum()
rjp_real = total_jjg / total_pokok if total_pokok > 0 else 0

m1, m2, m3 = st.columns(3)
m1.metric("Total Janjang (Jjg)", f"{total_jjg:,.0f}".replace(",", "."))
m2.metric("Total Pokok (Pkk)", f"{total_pokok:,.0f}".replace(",", "."))
m3.metric("Rasio Janjang Pokok (RJP)", f"{rjp_real:,.2f}".replace(",", "X").replace(".", ",").replace("X", "."))

st.markdown("---")

# --- GRAFIK BATANG TUNGGAL ---
df_filtered["RJP_Akt_Afd"] = df_filtered["Jjg Akt."] / df_filtered["Pokok"]

fig = go.Figure()
fig.add_trace(go.Bar(
    x=df_filtered["Afdeling"],
    y=df_filtered["RJP_Akt_Afd"],
    name="RJP Realisasi",
    marker_color="rgb(26, 118, 255)"
))

fig.update_layout(
    title=f"Grafik RJP per Afdeling - {pilihan_kebun} ({pilihan_bulan})",
    xaxis_title="Afdeling",
    yaxis_title="Janjang / Pokok",
    template="plotly_white"
)
st.plotly_chart(fig, use_container_width=True)

# --- TABEL DATA ---
df_table = df_filtered[["Afdeling", "Pokok", "Jjg Akt.", "% Cap."]].copy()
df_table["RJP"] = (df_filtered["Jjg Akt."] / df_filtered["Pokok"]).map('{:,.2f}'.format)
df_table["Pokok"] = df_table["Pokok"].map('{:,.0f}'.format)
df_table["Jjg Akt."] = df_table["Jjg Akt."].map('{:,.0f}'.format)
df_table["% Cap."] = df_table["% Cap."].map('{:,.2f}%'.format)

st.dataframe(df_table, use_container_width=True)