import streamlit as st
import pandas as pd
import plotly.graph_objects as go

# --- AMBIL DATA DARI CONTEXT GLOBAL ---
df_raw = st.session_state["df_raw"]
pilihan_bulan = st.session_state["pilihan_bulan"]
list_bulan = st.session_state["list_bulan"]
nama_target = st.session_state.get("nama_target", "BUDGET")

# Format tampilan angka capaian
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

# JUDUL DINAMIS: Otomatis berubah "vs BUDGET" atau "vs SENSUS"
st.subheader(f"📊 Analisis Kinerja Yield / Tonase (vs {nama_target.title()})")

# --- PROSES DATA BULANAN ---
df_bln_kebun = df_raw[df_raw["Bulan"] == pilihan_bulan].copy()
df_kebun_bln = df_bln_kebun.groupby("Kebun", as_index=False).agg({
    "Luas": "sum",
    "Kg Akt.": "sum",
    "Kg Bgt.": "sum"
})
df_kebun_bln["Yield_Akt"] = (df_kebun_bln["Kg Akt."] / 1000) / df_kebun_bln["Luas"]
df_kebun_bln["Yield_Bgt"] = (df_kebun_bln["Kg Bgt."] / 1000) / df_kebun_bln["Luas"]

# --- PROSES DATA YTD ---
idx_bulan = list_bulan.index(pilihan_bulan)
bulan_ytd = list_bulan[:idx_bulan + 1]
df_ytd_kebun = df_raw[df_raw["Bulan"].isin(bulan_ytd)].copy()
df_kebun_ytd = df_ytd_kebun.groupby("Kebun", as_index=False).agg({
    "Luas": "sum",
    "Kg Akt.": "sum",
    "Kg Bgt.": "sum"
})
df_kebun_ytd["Yield_Akt"] = (df_kebun_ytd["Kg Akt."] / 1000) / df_kebun_ytd["Luas"]
df_kebun_ytd["Yield_Bgt"] = (df_kebun_ytd["Kg Bgt."] / 1000) / df_kebun_ytd["Luas"]

# --- GRAFIK KOMBINASI ---
fig = go.Figure()
fig.add_trace(go.Bar(x=df_kebun_bln["Kebun"], y=df_kebun_bln["Yield_Akt"], name="Yield Aktual Bulanan"))
fig.add_trace(go.Bar(x=df_kebun_ytd["Kebun"], y=df_kebun_ytd["Yield_Akt"], name="YTD Aktual"))
fig.add_trace(go.Scatter(x=df_kebun_bln["Kebun"], y=df_kebun_bln["Yield_Bgt"], mode="lines+markers", name=f"Target {nama_target.title()}"))

fig.update_layout(
    title=f"Yield Performa Kebun to {nama_target.title()} - Periode {pilihan_bulan}",
    xaxis_title="Kebun",
    yaxis_title="Ton / Ha",
    barmode="group",
    template="plotly_white"
)
st.plotly_chart(fig, use_container_width=True)

# --- TABEL DATA ---
df_kebun_bln["% Cap."] = 0.0
mask = df_kebun_bln["Yield_Bgt"] > 0
df_kebun_bln.loc[mask, "% Cap."] = (df_kebun_bln.loc[mask, "Yield_Akt"] / df_kebun_bln.loc[mask, "Yield_Bgt"]) * 100
df_display = df_kebun_bln.copy()
df_display["% Cap."] = df_display["% Cap."].apply(format_capaian)
st.dataframe(df_display, use_container_width=True)