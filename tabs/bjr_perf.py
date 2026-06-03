import streamlit as st
import pandas as pd
import plotly.graph_objects as go

df_raw = st.session_state["df_raw"]
pilihan_bulan = st.session_state["pilihan_bulan"]

df_bln = df_raw[df_raw["Bulan"] == pilihan_bulan].copy()

list_kebun = ["All"] + sorted(df_bln["Kebun"].unique().tolist())
pilihan_kebun = st.selectbox("Filter Kebun:", list_kebun, key="bjr_kebun_picker")

if pilihan_kebun != "All":
    df_bln = df_bln[df_bln["Kebun"] == pilihan_kebun]

df_kebun = df_bln.groupby("Kebun", as_index=False).agg({
    "Kg Akt.": "sum",
    "Jjg Akt.": "sum",
    "BJR Bgt.": "mean"
})

df_kebun["BJR_Akt"] = df_kebun["Kg Akt."] / df_kebun["Jjg Akt."]
df_kebun["% Cap."] = (df_kebun["BJR_Akt"] / df_kebun["BJR_Bgt"]) * 100
df_kebun["Gap"] = df_kebun["BJR_Akt"] - df_kebun["BJR_Bgt"]

total_kg = df_kebun["Kg Akt."].sum()
total_jjg = df_kebun["Jjg Akt."].sum()
avg_bjr_akt = total_kg / total_jjg if total_jjg > 0 else 0

m1, m2, m3 = st.columns(3)
m1.metric("Total Produksi (Kg)", f"{total_kg:,.0f}".replace(",", "."))
m2.metric("Total Janjang", f"{total_jjg:,.0f}".replace(",", "."))
m3.metric("Rata-rata BJR Aktual", f"{avg_bjr_akt:.2f} Kg")

st.markdown("---")

fig = go.Figure()
fig.add_trace(go.Bar(x=df_kebun["Kebun"], y=df_kebun["BJR_Akt"], name="Actual BJR (Kg)"))
fig.add_trace(go.Scatter(x=df_kebun["Kebun"], y=df_kebun["BJR_Bgt"], mode="lines+markers", name="Target BJR", line=dict(color="orange", width=3)))

fig.update_layout(
    title=f"Performa Berat Janjang Rata-rata (BJR) - {pilihan_bulan}",
    xaxis_title="Kebun",
    yaxis_title="BJR (Kg)",
    template="plotly_white"
)
st.plotly_chart(fig, use_container_width=True)

df_table = df_kebun.copy()
df_table["Kg Akt."] = df_table["Kg Akt."].map('{:,.0f}'.format)
df_table["Jjg Akt."] = df_table["Jjg Akt."].map('{:,.0f}'.format)
df_table["BJR_Akt"] = df_table["BJR_Akt"].map('{:,.2f}'.format)
df_table["BJR_Bgt"] = df_table["BJR_Bgt"].map('{:,.2f}'.format)
df_table["% Cap."] = df_table["% Cap."].map('{:,.2f}%'.format)
df_table["Gap"] = df_table["Gap"].map('{:,.2f}'.format)

st.dataframe(df_table, use_container_width=True)