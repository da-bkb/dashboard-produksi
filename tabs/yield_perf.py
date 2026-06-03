import streamlit as st
import pandas as pd
import plotly.graph_objects as go

df_raw = st.session_state["df_raw"]
pilihan_bulan = st.session_state["pilihan_bulan"]

df_bln = df_raw[df_raw["Bulan"] == pilihan_bulan].copy()

list_kebun = sorted(df_bln["Kebun"].unique().tolist())
pilihan_kebun = st.selectbox("Pilih Kebun:", list_kebun, key="yield_kebun_picker")

df_filtered = df_bln[df_bln["Kebun"] == pilihan_kebun].copy()

# Perhitungan Metrik Utama atas
total_prod = df_filtered["Kg Akt."].sum()
total_luas = df_filtered["Luas"].sum()
yield_real = total_prod / total_luas if total_luas > 0 else 0

m1, m2, m3 = st.columns(3)
m1.metric("Total Produksi (Kg)", f"{total_prod:,.0f}".replace(",", "."))
m2.metric("Total Luas (Ha)", f"{total_luas:,.2f}".replace(",", "X").replace(".", ",").replace("X", "."))
m3.metric("Yield Realisasi (Kg/Ha)", f"{yield_real:,.2f}".replace(",", "X").replace(".", ",").replace("X", "."))

st.markdown("---")

# --- GRAFIK BATANG TUNGGAL ---
fig = go.Figure()
fig.add_trace(go.Bar(
    x=df_filtered["Afdeling"],
    y=df_filtered["Ton/ha Akt."],
    name="Realisasi Ton/Ha",
    marker_color="rgb(55, 83, 109)"
))

fig.update_layout(
    title=f"Grafik Yield per Afdeling - {pilihan_kebun} ({pilihan_bulan})",
    xaxis_title="Afdeling",
    yaxis_title="Ton / Ha",
    template="plotly_white"
)
st.plotly_chart(fig, use_container_width=True)

# --- TABEL DATA ---
df_table = df_filtered[["Afdeling", "Luas", "Kg Akt.", "Ton/ha Akt.", "% Cap."]].copy()
df_table["Luas"] = df_table["Luas"].map('{:,.2f}'.format)
df_table["Kg Akt."] = df_table["Kg Akt."].map('{:,.0f}'.format)
df_table["Ton/ha Akt."] = df_table["Ton/ha Akt Tuk"].map('{:,.2f}'.format) if "Ton/ha Akt Tuk" in df_table.columns else df_table["Ton/ha Akt."].map('{:,.2f}'.format)
df_table["% Cap."] = df_table["% Cap."].map('{:,.2f}%'.format)

st.dataframe(df_table, use_container_width=True)