import streamlit as st
import pandas as pd
import plotly.graph_objects as go

df_raw = st.session_state["df_raw"]
pilihan_bulan = st.session_state["pilihan_bulan"]
list_bulan = st.session_state["list_bulan"]

st.markdown(f"# 🌴 RJP to Sensus (J/P)")
st.markdown(f"**Periode Analisis:** Bulan {pilihan_bulan} & s/d Bulan {pilihan_bulan}")

# --- MTD ---
df_mtd = df_raw[df_raw['Bulan'] == pilihan_bulan].copy()
df_afd_mtd_grp = df_mtd.groupby('Afdeling').agg({
    'Jjg Akt.': 'sum',
    'Jjg Sns.': 'sum',
    'Pokok': 'first'
}).reset_index()

df_afd_mtd_grp['JP_Akt'] = df_afd_mtd_grp['Jjg Akt.'] / df_afd_mtd_grp['Pokok']
df_afd_mtd_grp['JP_Sns'] = df_afd_mtd_grp['Jjg Sns.'] / df_afd_mtd_grp['Pokok']
df_afd_mtd_grp['JP_Pct'] = (df_afd_mtd_grp['JP_Akt'] / df_afd_mtd_grp['JP_Sns'] * 100).fillna(0)

# --- YTD ---
URUTAN_BULAN_STANDAR = ['JAN', 'FEB', 'MAR', 'APR', 'MEI', 'JUN', 'JUL', 'AGS', 'SEP', 'OKT', 'NOV', 'DES']
pilihan_bulan_std = "AGS" if pilihan_bulan in ["AGUSTUS", "AGS"] else pilihan_bulan

if pilihan_bulan_std in URUTAN_BULAN_STANDAR:
    idx_bulan = URUTAN_BULAN_STANDAR.index(pilihan_bulan_std)
    bulan_ytd = URUTAN_BULAN_STANDAR[:idx_bulan + 1]
else:
    list_bulan_raw = list(df_raw['Bulan'].unique())
    if pilihan_bulan_std in list_bulan_raw:
        idx_bulan = list_bulan_raw.index(pilihan_bulan_std)
        bulan_ytd = list_bulan_raw[:idx_bulan + 1]
    else:
        bulan_ytd = [pilihan_bulan_std]

df_ytd = df_raw[df_raw['Bulan'].isin(bulan_ytd)].copy()
df_afd_ytd_grp = df_ytd.groupby('Afdeling').agg({
    'Jjg Akt.': 'sum',
    'Jjg Sns.': 'sum',
    'Pokok': 'first'
}).reset_index()

df_afd_ytd_grp['JP_Akt'] = df_afd_ytd_grp['Jjg Akt.'] / df_afd_ytd_grp['Pokok']
df_afd_ytd_grp['JP_Sns'] = df_afd_ytd_grp['Jjg Sns.'] / df_afd_ytd_grp['Pokok']
df_afd_ytd_grp['JP_Pct'] = (df_afd_ytd_grp['JP_Akt'] / df_afd_ytd_grp['JP_Sns'] * 100).fillna(0)

# --- VISUALISASI MTD ---
st.subheader("📊 Analisis J/P vs Sensus Per Kebun")
fig_m = go.Figure()
fig_m.add_trace(go.Bar(x=df_afd_mtd_grp["Afdeling"], y=df_afd_mtd_grp["JP_Akt"], name="Aktual", marker_color="#28348A", width=0.4))
fig_m.add_trace(go.Scatter(x=[None], y=[None], mode='lines', line=dict(color='#00B050', width=4), name='Sensus'))

for idx, row in df_afd_mtd_grp.iterrows():
    fig_m.add_shape(type="line", x0=idx-0.2, x1=idx+0.2, y0=row["JP_Sns"], y1=row["JP_Sns"], line=dict(color="#00B050", width=4))
    fig_m.add_annotation(x=idx, y=0, text=f"{row['JP_Pct']:.1f}%", showarrow=False, yshift=25, textangle=-90, font=dict(color="white", size=11, weight='bold'))
    if row["JP_Pct"] > 0 and (row["JP_Pct"] < 90 or row["JP_Pct"] > 110):
        fig_m.add_annotation(x=idx, y=row["JP_Sns"], ax=idx, ay=row["JP_Akt"], xref="x", yref="y", axref="x", ayref="y", showarrow=True, arrowhead=2, arrowsize=1, arrowwidth=2.5, arrowcolor='#FF0000')

fig_m.update_layout(height=320, margin=dict(l=20, r=20, t=20, b=20), legend=dict(orientation="h", y=1.15))
st.plotly_chart(fig_m, use_container_width=True)

# --- VISUALISASI YTD ---
st.subheader("📊 Analisis J/P Kumulatif YTD vs Sensus")
fig_a_y = go.Figure()
fig_a_y.add_trace(go.Bar(x=df_afd_ytd_grp["Afdeling"], y=df_afd_ytd_grp["JP_Akt"], name="YTD Aktual", marker_color="#28348A", width=0.4))
fig_a_y.add_trace(go.Scatter(x=[None], y=[None], mode='lines', line=dict(color='#00B050', width=4), name='Sensus YTD'))

for idx, row in df_afd_ytd_grp.iterrows():
    fig_a_y.add_shape(type="line", x0=idx-0.2, x1=idx+0.2, y0=row["JP_Sns"], y1=row["JP_Sns"], line=dict(color="#00B050", width=4))
    fig_a_y.add_annotation(x=idx, y=0, text=f"{row['JP_Pct']:.1f}%", showarrow=False, yshift=25, textangle=-90, font=dict(color="white", size=11, weight='bold'))
    if row["JP_Pct"] > 0 and (row["JP_Pct"] < 90 or row["JP_Pct"] > 110):
        fig_a_y.add_annotation(x=idx, y=row["JP_Sns"], ax=idx, ay=row["JP_Akt"], xref="x", yref="y", axref="x", ayref="y", showarrow=True, arrowhead=2, arrowsize=1, arrowwidth=2.5, arrowcolor='#FF0000')

fig_a_y.update_layout(height=320, margin=dict(l=20, r=20, t=20, b=20), legend=dict(orientation="h", y=1.15))
st.plotly_chart(fig_a_y, use_container_width=True)