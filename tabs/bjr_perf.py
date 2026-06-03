import streamlit as st
import pandas as pd
import plotly.graph_objects as go

df_raw = st.session_state["df_raw"]
pilihan_bulan = st.session_state["pilihan_bulan"]

df_bln = df_raw[df_raw["Bulan"] == pilihan_bulan].copy()

list_kebun = sorted(df_bln["Kebun"].unique().tolist())
pilihan_kebun = st.selectbox("Pilih Kebun:", list_kebun, key="bjr_kebun_picker")

df_filtered = df_bln[df_bln["Kebun"] == pilihan_kebun].copy()

# Perhitungan Metrik Utama atas
total_prod = df_filtered["Kg Akt."].sum()
total_jjg = df_filtered["Jjg Akt."].sum()
bjr_real = total_prod / total_jjg if total_jjg > 0 else 0

m1, m2, m3 = st.columns(3)
m1.metric("Total Produksi (Kg)", f"{total_prod:,.0f}".replace(",", "."))
m2.metric("Total Janjang (Jjg)", f"{total_jjg:,.0f}".replace(",", "."))
m3.metric("BJR Realisasi (Kg)", f"{bjr_real:,.2f}".replace(",", "X").replace(".", ",").replace("X", "."))

st.markdown("---")

# --- GRAFIK BATANG ---
fig = go.Figure()
fig.add_trace(go.Bar(
    x=df_filtered["Afdeling"],
    y=df_filtered["BJR Akt."],
    name="BJR Realisasi",
    marker_color="rgb(50, 171, 96)"
))

fig.update_layout(
    title=f"Grafik BJR per Afdeling - {pilihan_kebun} ({pilihan_bulan})",
    xaxis_title="Afdeling",
    yaxis_title="BJR (Kg)",
    template="plotly_white"
)
st.plotly_chart(fig, use_container_width=True)

# --- TABEL DATA ---
df_table = df_filtered[["Afdeling", "Kg Akt.", "Jjg Akt.", "BJR Akt.", "% Cap."]].copy()
df_table["Kg Akt."] = df_table["Kg Akt."].map('{:,.0f}'.format)
df_table["Jjg Akt."] = df_table["Jjg Akt."].map('{:,.0f}'.format)
df_table["BJR Akt."] = df_table["BJR Akt."].map('{:,.2f}'.format)
df_table["% Cap."] = df_table["% Cap."].map('{:,.2f}%'.format)

st.dataframe(df_table, use_container_width=True)