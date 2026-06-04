import streamlit as st
import pandas as pd
import plotly.graph_objects as go

df_raw = st.session_state["df_raw"]
pilihan_bulan = st.session_state["pilihan_bulan"]

st.markdown(f"### 🌱 Yield terhadap Budget (Ton/Ha)")

# --- 1. FILTER ---
URUTAN_BULAN_STD = ['JAN', 'FEB', 'MAR', 'APR', 'MEI', 'JUN', 'JUL', 'AGS', 'SEP', 'OKT', 'NOV', 'DES']
if pilihan_bulan == 'CAWU I': b_mtd, b_ytd = ['JAN', 'FEB', 'MAR', 'APR'], ['JAN', 'FEB', 'MAR', 'APR']
elif pilihan_bulan == 'CAWU II': b_mtd, b_ytd = ['MEI', 'JUN', 'JUL', 'AGS'], ['JAN', 'FEB', 'MAR', 'APR', 'MEI', 'JUN', 'JUL', 'AGS']
elif pilihan_bulan == 'CAWU III': b_mtd, b_ytd = ['SEP', 'OKT', 'NOV', 'DES'], URUTAN_BULAN_STD
else: b_mtd, b_ytd = [pilihan_bulan], [pilihan_bulan]

df_mtd = df_raw[df_raw['Bulan'].isin(b_mtd)].copy()
df_ytd = df_raw[df_raw['Bulan'].isin(b_ytd)].copy()

def calc_yield(df):
    g = df.groupby('Kebun').agg({'Kg Akt.': 'sum', 'Kg Bgt.': 'sum', 'Luas': 'sum'}).reset_index()
    g['Aktual'] = g['Kg Akt.'] / g['Luas'] / 1000
    g['Target'] = g['Kg Bgt.'] / g['Luas'] / 1000
    g['Var'] = g['Aktual'] - g['Target']
    g['Pct'] = (g['Aktual'] / g['Target'] * 100) - 100
    return g

def style_var_koreksi(val):
    if val < -30: return 'background-color: #FF0000; color: white; font-weight: bold; text-align: right;'
    elif val < -20: return 'background-color: #FF9900; color: black; font-weight: bold; text-align: right;'
    elif val < -10: return 'background-color: #FFFF00; color: black; font-weight: bold; text-align: right;'
    else: return 'background-color: #A9D08E; color: black; font-weight: bold; text-align: right;'

# --- 2. TABEL ---
col_t1, col_t2 = st.columns(2)
for col, df, title, k in [(col_t1, calc_yield(df_mtd), "Bulan Ini", "t_bgt_mtd"), (col_t2, calc_yield(df_ytd), "s.d Bulan Ini", "t_bgt_ytd")]:
    with col:
        st.markdown(f"##### 📋 {title}")
        f = df[['Kebun', 'Aktual', 'Target', 'Var', 'Pct']].copy()
        f.insert(0, 'No', range(1, len(f) + 1))
        f.columns = ['No', 'Kebun', 'Aktual (Ton/Ha)', 'Budget (Ton/Ha)', 'Gap (Ton/Ha)', 'Var (%)']
        st.dataframe(f.style.format({'Aktual (Ton/Ha)': '{:,.2f}', 'Budget (Ton/Ha)': '{:,.2f}', 'Gap (Ton/Ha)': '{:+,.2f}', 'Var (%)': '{:+,.1f}%'})
                     .map(style_var_koreksi, subset=['Var (%)']), use_container_width=True, hide_index=True, key=k)

# --- 3. DETAIL AFDELING ---
st.markdown("---")
st.markdown("### 🔎 Detail per Afdeling")
kb = st.selectbox("Pilih Kebun:", sorted(df_raw['Kebun'].dropna().unique()), key="sb_bgt_afd")
df_a = df_mtd[df_mtd['Kebun'] == kb].groupby('Afdeling').agg({'Kg Akt.': 'sum', 'Kg Bgt.': 'sum', 'Luas': 'sum'}).reset_index()
df_a['Aktual'] = df_a['Kg Akt.'] / df_a['Luas'] / 1000
df_a['Target'] = df_a['Kg Bgt.'] / df_a['Luas'] / 1000
df_a['Var'] = df_a['Aktual'] - df_a['Target']
df_a['Pct'] = (df_a['Aktual'] / df_a['Target'] * 100) - 100
df_a.insert(0, 'No', range(1, len(df_a) + 1))
df_a.columns = ['No', 'Afdeling', 'Aktual (Ton/Ha)', 'Budget (Ton/Ha)', 'Gap (Ton/Ha)', 'Var (%)']
st.dataframe(df_a.style.format({'Aktual (Ton/Ha)': '{:,.2f}', 'Budget (Ton/Ha)': '{:,.2f}', 'Gap (Ton/Ha)': '{:+,.2f}', 'Var (%)': '{:+,.1f}%'})
             .map(style_var_koreksi, subset=['Var (%)']), use_container_width=True, hide_index=True, key="table_bgt_afd")