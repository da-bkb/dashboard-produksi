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
st.subheader(f"📊 Analisis Kinerja Berat Janjang Rata-rata / BJR (vs {nama_target.title()})")

# Bulanan
df_bln = df_raw[df_raw["Bulan"] == pilihan_bulan].copy()
df_kebun_bln = df_bln.groupby("Kebun", as_index=False).agg({"Kg Akt.": "sum", "Jjg Akt.": "sum", "BJR Bgt.": "mean"})
df_kebun_bln["BJR_Akt"] = df_kebun_bln["Kg Akt."] / df_kebun_bln["Jjg Akt."]
df_kebun_bln["BJR_Bgt"] = df_kebun_bln["BJR Bgt."]

# YTD
idx_bulan = list_bulan.index(pilihan_bulan)
df_ytd = df_raw[df_raw["Bulan"].isin(list_bulan[:idx_bulan + 1])].copy()
df_kebun_ytd = df_ytd.groupby("Kebun", as_index=False).agg({"Kg Akt.": "sum", "Jjg Akt.": "sum", "BJR Bgt.": "mean"})
df_kebun_ytd["BJR_Akt"] = df_kebun_ytd["Kg Akt."] / df_kebun_ytd["Jjg Akt."]

# --- GRAFIK KOMBINASI ---
fig = go.Figure()
fig.add_trace(go.Bar(x=df_kebun_bln["Kebun"], y=df_kebun_bln["BJR_Akt"], name="BJR Aktual Bulanan"))
fig.add_trace(go.Bar(x=df_kebun_ytd["Kebun"], y=df_kebun_ytd["BJR_Akt"], name="YTD BJR Aktual"))
fig.add_trace(go.Scatter(x=df_kebun_bln["Kebun"], y=df_kebun_bln["BJR_Bgt"], mode="lines+markers", name=f"Target {nama_target.title()}"))

fig.update_layout(
    title=f"BJR Performa Kebun to {nama_target.title()} - Periode {pilihan_bulan}", 
    xaxis_title="Kebun", 
    yaxis_title="Kg", 
    barmode="group", 
    template="plotly_white"
)
st.plotly_chart(fig, use_container_width=True)

# Tabel Data
df_kebun_bln["% Cap. BJR"] = (df_kebun_bln["BJR_Akt"] / df_kebun_bln["BJR_Bgt"]) * 100
df_display = df_kebun_bln.copy()
df_display["% Cap. BJR"] = df_display["% Cap. BJR"].apply(format_capaian)
st.dataframe(df_display, use_container_width=True)