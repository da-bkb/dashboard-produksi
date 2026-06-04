import streamlit as st
import pandas as pd
import plotly.graph_objects as go

# Pastikan data tersedia
df_raw = st.session_state["df_raw"]
pilihan_bulan = st.session_state["pilihan_bulan"]

st.markdown(f"### 🎯 Yield terhadap Sensus (Ton/Ha)")

# --- LOGIKA FILTER ---
URUTAN_BULAN_STD = ['JAN', 'FEB', 'MAR', 'APR', 'MEI', 'JUN', 'JUL', 'AGS', 'SEP', 'OKT', 'NOV', 'DES']
if pilihan_bulan == 'CAWU I': b_mtd, b_ytd = ['JAN', 'FEB', 'MAR', 'APR'], ['JAN', 'FEB', 'MAR', 'APR']
elif pilihan_bulan == 'CAWU II': b_mtd, b_ytd = ['MEI', 'JUN', 'JUL', 'AGS'], ['JAN', 'FEB', 'MAR', 'APR', 'MEI', 'JUN', 'JUL', 'AGS']
elif pilihan_bulan == 'CAWU III': b_mtd, b_ytd = ['SEP', 'OKT', 'NOV', 'DES'], URUTAN_BULAN_STD
else: b_mtd, b_ytd = [pilihan_bulan], [pilihan_bulan]

df_mtd = df_raw[df_raw['Bulan'].isin(b_mtd)].copy()
df_ytd = df_raw[df_raw['Bulan'].isin(b_ytd)].copy()

def calc_yield(df):
    df_g = df.groupby('Kebun').agg({'Kg Akt.': 'sum', 'Kg Sns.': 'sum', 'Luas': 'sum'}).reset_index()
    df_g['Aktual'] = df_g['Kg Akt.'] / df_g['Luas'] / 1000
    df_g['Target'] = df_g['Kg Sns.'] / df_g['Luas'] / 1000
    df_g['Var'] = df_g['Aktual'] - df_g['Target']
    df_g['Pct'] = (df_g['Aktual'] / df_g['Target'] * 100) - 100
    return df_g

# --- STYLING ---
def style_var(val):
    if val < -30: return 'background-color: #FF0000; color: white; font-weight: bold;'
    elif val < -20: return 'background-color: #FF9900; color: black; font-weight: bold;'
    elif val < -10: return 'background-color: #FFFF00; color: black; font-weight: bold;'
    else: return 'background-color: #A9D08E; color: black; font-weight: bold;'

# --- TABEL ---
col_t1, col_t2 = st.columns(2)
for col, df, title, k in [(col_t1, calc_yield(df_mtd), "Bulan Ini", "t_sns_mtd"), (col_t2, calc_yield(df_ytd), "s.d Bulan Ini", "t_sns_ytd")]:
    with col:
        st.markdown(f"##### 📋 {title}")
        df_f = df[['Kebun', 'Aktual', 'Target', 'Var', 'Pct']].copy()
        df_f.insert(0, 'No', range(1, len(df_f) + 1))
        df_f.columns = ['No', 'Kebun', 'Aktual (Ton/Ha)', 'Sensus (Ton/Ha)', 'Gap (Ton/Ha)', 'Var (%)']
        st.dataframe(df_f.style.format({'Aktual (Ton/Ha)': '{:,.2f}', 'Sensus (Ton/Ha)': '{:,.2f}', 'Gap (Ton/Ha)': '{:+,.2f}', 'Var (%)': '{:+,.1f}%'})
                     .applymap(style_var, subset=['Var (%)']), use_container_width=True, hide_index=True, key=k)