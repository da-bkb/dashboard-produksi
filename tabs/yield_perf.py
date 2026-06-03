import streamlit as st
import pandas as pd
import plotly.graph_objects as go

# Ambil data dari session state
df_raw = st.session_state["df_raw"]
pilihan_bulan = st.session_state["pilihan_bulan"]

# Filter data berdasarkan bulan terpilih
df_bln = df_raw[df_raw["Bulan"] == pilihan_bulan].copy()

# Pilihan Kebun
list_kebun = ["All"] + sorted(df_bln["Kebun"].unique().tolist())
pilihan_kebun = st.selectbox("Filter Kebun:", list_kebun, key="yield_kebun_picker")

if pilihan_kebun != "All":
    df_bln = df_bln[df_bln["Kebun"] == pilihan_kebun]

# Grouping data untuk Grafik & Tabel
df_kebun = df_bln.groupby("Kebun", as_index=False).agg({
    "Luas": "mean",
    "Kg Akt.": "sum",
    "Kg Bgt.": "sum"
})

# Hitung Yield
df_kebun["Yield_Akt"] = (df_kebun["Kg Akt."] / 1000) / df_kebun["Luas"]
df_kebun["Yield_Bgt"] = (df_kebun["Kg Bgt."] / 1000) / df_kebun["Luas"]
df_kebun["% Cap."] = (df_kebun["Yield_Akt"] / df_kebun["Yield_Bgt"]) * 100
df_kebun["Gap"] = df_kebun["Yield_Akt"] - df_kebun["Yield_Bgt"]

# Tampilkan KIP / Kunci Metrik Utama di Atas
total_luas = df_kebun["Luas"].sum()
total_kg_akt = df_kebun["Kg Akt."].sum()
total_kg_bgt = df_kebun["Kg Bgt."].sum()
avg_cap = (total_kg_akt / total_kg_bgt) * 100 if total_kg_bgt > 0 else 0

m1, m2, m3, m4 = st.columns(4)
m1.metric("Total Luas (Ha)", f"{total_luas:,.2f}".replace(",", "X").replace(".", ",").replace("X", "."))
m2.metric("Prod. Aktual (Kg)", f"{total_kg_akt:,.0f}".replace(",", "."))
m3.metric("Target (Kg)", f"{total_kg_bgt:,.0f}".replace(",", "."))
m4.metric("% Capaian", f"{avg_cap:.2f}%")

st.markdown("---")

# --- GRAFIK ---
fig = go.Figure()
fig.add_trace(go.Bar(x=df_kebun["Kebun"], y=df_kebun["Yield_Akt"], name="Actual Yield (Ton/Ha)"))
fig.add_trace(go.Scatter(x=df_kebun["Kebun"], y=df_kebun["Yield_Bgt"], mode="lines+markers", name="Target Yield", line=dict(color="orange", width=3)))

fig.update_layout(
    title=f"Performa Yield per Kebun - {pilihan_bulan}",
    xaxis_title="Kebun",
    yaxis_title="Ton / Ha",
    barmode="group",
    template="plotly_white"
)
st.plotly_chart(fig, use_container_width=True)

# --- TABEL ---
df_table = df_kebun.copy()
# Format angka agar rapi di tabel
df_table["Luas"] = df_table["Luas"].map('{:,.2f}'.format)
df_table["Kg Akt."] = df_table["Kg Akt."].map('{:,.0f}'.format)
df_table["Kg Bgt."] = df_table["Kg Bgt."].map('{:,.0f}'.format)
df_table["Yield_Akt"] = df_table["Yield_Akt"].map('{:,.2f}'.format)
df_table["Yield_Bgt"] = df_table["Yield_Bgt"].map('{:,.2f}'.format)
df_table["% Cap."] = df_table["% Cap."].map('{:,.2f}%'.format)
df_table["Gap"] = df_table["Gap"].map('{:,.2f}'.format)

st.dataframe(df_table, use_container_width=True)