import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go

# Ambil data global dari session state app.py
df_raw = st.session_state["df_raw"]
pilihan_bulan = st.session_state["pilihan_bulan"]

st.markdown(f"### 🌱 Yield terhadap Budget (Ton/Ha)")

# --- 1. PROSES FILTER TIMEFRAME ---
URUTAN_BULAN_STD = ['JAN', 'FEB', 'MAR', 'APR', 'MEI', 'JUN', 'JUL', 'AGS', 'SEP', 'OKT', 'NOV', 'DES']

if pilihan_bulan == 'CAWU I':
    bulan_mtd, bulan_ytd = ['JAN', 'FEB', 'MAR', 'APR'], ['JAN', 'FEB', 'MAR', 'APR']
elif pilihan_bulan == 'CAWU II':
    bulan_mtd, bulan_ytd = ['MEI', 'JUN', 'JUL', 'AGS'], ['JAN', 'FEB', 'MAR', 'APR', 'MEI', 'JUN', 'JUL', 'AGS']
elif pilihan_bulan == 'CAWU III':
    bulan_mtd, bulan_ytd = ['SEP', 'OKT', 'NOV', 'DES'], URUTAN_BULAN_STD
else:
    bulan_mtd, bulan_ytd = [pilihan_bulan], [pilihan_bulan]

df_mtd = df_raw[df_raw['Bulan'].isin(bulan_mtd)].copy()
df_ytd = df_raw[df_raw['Bulan'].isin(bulan_ytd)].copy()

# --- 2. PERHITUNGAN YIELD ---
def calc_yield(df):
    df_g = df.groupby('Kebun').agg({'Kg Akt.': 'sum', 'Kg Bgt.': 'sum', 'Luas': 'sum'}).reset_index()
    df_g['Aktual'] = df_g['Kg Akt.'] / df_g['Luas'] / 1000
    df_g['Target'] = df_g['Kg Bgt.'] / df_g['Luas'] / 1000
    df_g['Var'] = df_g['Aktual'] - df_g['Target']
    df_g['Pct'] = (df_g['Aktual'] / df_g['Target'] * 100) - 100
    return df_g

df_k_mtd = calc_yield(df_mtd)
df_k_ytd = calc_yield(df_ytd)

# --- 3. STYLING ---
def style_gap_black(val): return 'color: black; font-weight: bold;'
def style_budget_var_fill(val):
    if isinstance(val, (int, float)):
        if val > 5: return 'background-color: #FFC000; color: black; font-weight: bold; text-align: right;'
        elif -5 <= 5: return 'background-color: #A9D08E; color: black; font-weight: bold; text-align: right;'
        else: return 'background-color: #FF8585; color: black; font-weight: bold; text-align: right;'
    return ''

# --- 4. GRAFIK ---
col1, col2 = st.columns(2)
for col, df, title, k in [(col1, df_k_mtd, "Bulan Ini", "bgt_chart_mtd"), (col2, df_k_ytd, "s.d Bulan Ini", "bgt_chart_ytd")]:
    with col:
        fig = go.Figure()
        fig.add_trace(go.Bar(x=df["Kebun"], y=df["Aktual"], name="Aktual", marker_color="#28348A"))
        fig.add_trace(go.Scatter(x=df["Kebun"], y=df["Target"], mode='lines', name='Budget', line=dict(color='#00B050', width=3)))
        st.plotly_chart(fig, use_container_width=True, key=k)

# --- 5. TABEL PER AFDELING ---
st.markdown("### 🔎 Detail per Afdeling")
kebun_terpilih = st.selectbox("Pilih Kebun:", sorted(df_raw['Kebun'].unique()), key="sb_bgt_afd")
df_a = df_mtd[df_mtd['Kebun'] == kebun_terpilih].groupby('Afdeling').agg({'Kg Akt.': 'sum', 'Kg Bgt.': 'sum', 'Luas': 'sum'}).reset_index()
df_a['Aktual'] = df_a['Kg Akt.'] / df_a['Luas'] / 1000
df_a['Target'] = df_a['Kg Bgt.'] / df_a['Luas'] / 1000
df_a['Var'] = df_a['Aktual'] - df_a['Target']
df_a['Pct'] = (df_a['Aktual'] / df_a['Target'] * 100) - 100

st.dataframe(df_a[['Afdeling', 'Aktual', 'Target', 'Var', 'Pct']].style
             .format({'Aktual': '{:,.2f}', 'Target': '{:,.2f}', 'Var': '{:+,.2f}', 'Pct': '{:+,.1f}%'})
             .map(style_budget_var_fill, subset=['Pct']), use_container_width=True, key="table_bgt_afd")
