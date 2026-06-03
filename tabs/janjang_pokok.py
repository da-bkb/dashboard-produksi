import streamlit as st
import pandas as pd
import plotly.graph_objects as go

df_raw = st.session_state["df_raw"]
pilihan_bulan = st.session_state["pilihan_bulan"]

df_bln = df_raw[df_raw["Bulan"] == pilihan_bulan].copy()

list_kebun = ["All"] + sorted(df_bln["Kebun"].unique().tolist())
pilihan_kebun = st.selectbox("Filter Kebun:", list_kebun, key="rjp_kebun_picker")

if pilihan_kebun != "All":
    df_bln = df_bln[df_bln["Kebun"] == pilihan_kebun]

df_kebun = df_bln.groupby("Kebun", as_index=False).agg({
    "Pokok": "sum",
    "Jjg Akt.": "sum",
    "Jjg Bgt.": "sum"
})

df_kebun["RJP_Akt"] = df_kebun["Jjg Akt."] / df_kebun["Pokok"]
df_kebun["RJP_Bgt"] = df_kebun["Jjg Bgt."] / df_kebun["Pokok"]
df_kebun["% Cap."] = (df_kebun["RJP_Akt"] / df_kebun["RJP_Bgt"]) * 100
df_kebun["Gap"] = df_kebun["RJP_Akt"] - df_kebun["RJP_Bgt"]

total_pokok = df_kebun["Pokok"].sum()
total_jjg_akt = df_kebun["Jjg Akt."].sum()
total_jjg_bgt = df_kebun["Jjg Bgt."].sum()
avg_cap = (total_jjg_akt / total_jjg_bgt) * 100 if total_jjg_bgt > 0 else 0

m1, m2, m3, m4 = st.columns(4)
m1.metric("Total Pokok", f"{total_pokok:,.0f}".replace(",", "."))
m2.metric("Janjang Aktual", f"{total_jjg_akt:,.0f}".replace(",", "."))
m3.metric("Janjang Target", f"{total_jjg_bgt:,.0f}".replace(",", "."))
m4.metric("% Capaian RJP", f"{avg_cap:.2f}%")

st.markdown("---")

fig = go.Figure()
fig.add_trace(go.Bar(x=df_kebun["Kebun"], y=df_kebun["RJP_Akt"], name="Actual RJP (Jjg/Pkk)"))
fig.add_trace(go.Scatter(x=df_kebun["Kebun"], y=df_kebun["RJP_Bgt"], mode="lines+markers", name="Target RJP", line=dict(color="orange", width=3)))

fig.update_layout(
    title=f"Performa Janjang Per Pokok (RJP) - {pilihan_bulan}",
    xaxis_title="Kebun",
    yaxis_title="Janjang / Pokok",
    template="plotly_white"
)
st.plotly_chart(fig, use_container_width=True)

df_table = df_kebun.copy()
df_table["Pokok"] = df_table["Pokok"].map('{:,.0f}'.format)
df_table["Jjg Akt."] = df_table["Jjg Akt."].map('{:,.0f}'.format)
df_table["Jjg Bgt."] = df_table["Jjg Bgt."].map('{:,.0f}'.format)
df_table["RJP_Akt"] = df_table["RJP_Akt"].map('{:,.2f}'.format)
df_table["RJP_Bgt"] = df_table["RJP_Bgt"].map('{:,.2f}'.format)
df_table["% Cap."] = df_table["% Cap."].map('{:,.2f}%'.format)
df_table["Gap"] = df_table["Gap"].map('{:,.2f}'.format)

st.dataframe(df_table, use_container_width=True)