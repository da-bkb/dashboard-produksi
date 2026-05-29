import streamlit as st
import pandas as pd
import plotly.graph_objects as go

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

st.subheader("📊 Analisis Rasio Janjang Per Pokok / JP (vs SENSUS)")

df_bulan_ini = df_raw[df_raw["Bulan"] == pilihan_bulan].copy()

df_kebun = df_bulan_ini.groupby("Kebun", as_index=False).agg({
    "Pokok": "sum",
    "Jjg Akt.": "sum",
    "Jjg Sns.": "sum"
})

df_kebun["JP Akt"] = df_kebun["Jjg Akt."] / df_kebun["Pokok"]
df_kebun["JP Sns"] = df_kebun["Jjg Sns."] / df_kebun["Pokok"]

# Hitung % Capaian terhadap Sensus
df_kebun["% Cap. JP"] = 0.0
mask = df_kebun["JP Sns"] > 0
df_kebun.loc[mask, "% Cap. JP"] = (df_kebun.loc[mask, "JP Akt"] / df_kebun.loc[mask, "JP Sns"]) * 100

df_display_kebun = df_kebun.copy()
df_display_kebun["% Cap. JP"] = df_display_kebun["% Cap. JP"].apply(format_capaian_sensus)

# --- GRAFIK ---
fig = go.Figure()
fig.add_trace(go.Bar(
    x=df_kebun["Kebun"],
    y=df_kebun["JP Akt"],
    name="Janjang/Pokok Aktual",
    marker_color="indigo"
))
fig.add_trace(go.Scatter(
    x=df_kebun["Kebun"],
    y=df_kebun["JP Sns"],
    mode="lines+markers",
    name="Target JP Sensus",
    line=dict(color="crimson", width=3)
))

fig.update_layout(
    title=f"Perbandingan Janjang/Pokok vs Target Sensus - Bulan {pilihan_bulan}",
    xaxis_title="Kebun",
    yaxis_title="Janjang / Pokok",
    template="plotly_white"
)

st.plotly_chart(fig, use_container_width=True)
st.markdown("### 📋 Ringkasan Data Janjang Pokok Kebun (Sensus)")
st.dataframe(df_display_kebun, use_container_width=True)