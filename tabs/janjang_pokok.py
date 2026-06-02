import streamlit as st
import pandas as pd
import plotly.graph_objects as go

# --- AMBIL DATA DARI CONTEXT GLOBAL ---
df_raw = st.session_state["df_raw"]
pilihan_bulan = st.session_state["pilihan_bulan"]
list_bulan = st.session_state["list_bulan"]
nama_target = st.session_state.get("nama_target", "BUDGET")

def format_capaian(val):
    try:
        num = float(val)
        if 95.0 <= num <= 105.0:
            return f"{num:.1f}%"
        elif num < 95.0:
            return f"🔻 {num:.1f}%"
        else:
            return f"🔺 {num:.1f}%"
    except:
        return str(val)

# JUDUL DINAMIS
st.subheader(f"📊 Analisis Rasio Janjang Per Pokok / RJP (vs {nama_target.title()})")

# Bulanan
df_bln = df_raw[df_raw["Bulan"] == pilihan_bulan].copy()
df_kebun_bln = df_bln.groupby("Kebun", as_index=False).agg({"Pokok": "sum", "Jjg Akt.": "sum", "Jjg Bgt.": "sum"})
df_kebun_bln["JP_Akt"] = df_kebun_bln["Jjg Akt."] / df_kebun_bln["Pokok"]
df_kebun_bln["JP_Bgt"] = df_kebun_bln["Jjg Bgt."] / df_kebun_bln["Pokok"]

# YTD
idx_bulan = list_bulan.index(pilihan_bulan)
df_ytd = df_raw[df_raw["Bulan"].isin(list_bulan[:idx_bulan + 1])].copy()
df_kebun_ytd = df_ytd.groupby("Kebun", as_index=False).agg({"Pokok": "sum", "Jjg Akt.": "sum", "Jjg Bgt.": "sum"})
df_kebun_ytd["JP_Akt"] = df_kebun_ytd["Jjg Akt."] / df_kebun_ytd["Pokok"]

# --- GRAFIK KOMBINASI ---
fig = go.Figure()
fig.add_trace(go.Bar(x=df_kebun_bln["Kebun"], y=df_kebun_bln["JP_Akt"], name="RJP Aktual Bulanan"))
fig.add_trace(go.Bar(x=df_kebun_ytd["Kebun"], y=df_kebun_ytd["JP_Akt"], name="YTD RJP Aktual"))
fig.add_trace(go.Scatter(x=df_kebun_bln["Kebun"], y=df_kebun_bln["JP_Bgt"], mode="lines+markers", name=f"Target {nama_target.title()}"))

fig.update_layout(
    title=f"RJP Performa Kebun to {nama_target.title()} - Periode {pilihan_bulan}", 
    xaxis_title="Kebun", 
    yaxis_title="Janjang / Pokok", 
    barmode="group", 
    template="plotly_white"
)
st.plotly_chart(fig, use_container_width=True)

# Tabel Data
df_kebun_bln["% Cap. JP"] = (df_kebun_bln["JP_Akt"] / df_kebun_bln["JP_Bgt"]) * 100
df_display = df_kebun_bln.copy()
df_display["% Cap. JP"] = df_display["% Cap. JP"].apply(format_capaian)
st.dataframe(df_display, use_container_width=True)