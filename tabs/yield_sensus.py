import streamlit as st
import pandas as pd
import plotly.graph_objects as go

# --- AMBIL DATA DARI CONTEXT GLOBAL ---
df_raw = st.session_state["df_raw"]
pilihan_bulan = st.session_state["pilihan_bulan"]

# 💡 LOGIKA RENTANG AMAN KHUSUS SENSUS (95% - 105%)
def format_capaian_sensus(val):
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

st.subheader("📊 Analisis Kinerja Yield / Tonase (vs SENSUS)")

# Filter data bulan berjalan
df_bulan_ini = df_raw[df_raw["Bulan"] == pilihan_bulan].copy()

# Agregasi tingkat kebun
df_kebun = df_bulan_ini.groupby("Kebun", as_index=False).agg({
    "Luas": "sum",
    "Kg Akt.": "sum",
    "Kg Sns.": "sum"
})

# Hitung rasio yield
df_kebun["Yield Akt"] = (df_kebun["Kg Akt."] / 1000) / df_kebun["Luas"]
df_kebun["Yield Sns"] = (df_kebun["Kg Sns."] / 1000) / df_kebun["Luas"]

# Hitung % Capaian terhadap Sensus
df_kebun["% Cap."] = 0.0
mask = df_kebun["Yield Sns"] > 0
df_kebun.loc[mask, "% Cap."] = (df_kebun.loc[mask, "Yield Akt"] / df_kebun.loc[mask, "Yield Sns"]) * 100

# Terapkan format panah khusus sensus ke tabel display
df_display_kebun = df_kebun.copy()
df_display_kebun["% Cap."] = df_display_kebun["% Cap."].apply(format_capaian_sensus)

# --- 📊 VISUALISASI GRAFIK ---
fig = go.Figure()
fig.add_trace(go.Bar(
    x=df_kebun["Kebun"],
    y=df_kebun["Yield Akt"],
    name="Yield Aktual (Ton/Ha)",
    marker_color="teal"
))
fig.add_trace(go.Scatter(
    x=df_kebun["Kebun"],
    y=df_kebun["Yield Sns"],
    mode="lines+markers",
    name="Target Sensus",
    line=dict(color="orange", width=3)
))

fig.update_layout(
    title=f"Perbandingan Yield Aktual vs Sensus - Bulan {pilihan_bulan}",
    xaxis_title="Kebun",
    yaxis_title="Ton / Ha",
    barmode="group",
    template="plotly_white"
)

st.plotly_chart(fig, use_container_width=True)

st.markdown("### 📋 Ringkasan Data Kebun (Sensus)")
st.dataframe(df_display_kebun, use_container_width=True)